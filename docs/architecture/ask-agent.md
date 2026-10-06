# The Ask agent

How a question becomes an answer. The same engine runs three surfaces: **Ask**
(`/ask` and the home Ask tile), the **team coach** (`/teams/{id}`) and the **calc
coach** (the home damage calculator). Code: `backend/app/agent/`. The rules it must
keep are in `openspec/specs/assistant/` (and `team-coach/`, `calc-coach/`).

```
question
  │
  ├─ answer cache hit? ─────────────────────────────► replay the stored events
  │
  ▼
choose a plan  (runner._choose_plan)
  plan cache → keyword planner (always) → LLM planner (only if needed)
  │
  ▼
run the steps  (executor)        concurrently, one DB session each, 8 s timeout
  │                               each tool returns chunks + views + summary
  ▼
re-plan?  only an LLM plan with an error step (or needs_followup), at most once
  │
  ▼
answer
  every step closed-form ─► code writes it      (render.py)
  otherwise               ─► LLM, from the chunks only, cites [n]
  no LLM / it fails       ─► extractive answer   (quotes the chunks)
```

Everything streams as events: `plan` → `step`* → `view`* → `sources` → `delta`* →
`done{usage, fallback}`. The API layer sends them as SSE, or collects them into one
JSON response for the non-streaming endpoint.

## 1. Plans, not routes

A plan is 1–6 **steps**; each step is one tool call with typed arguments:

```python
Step(id="s1", tool="learnset",
     args={"move": "Will-O-Wisp", "types": ["fire"], "legendary": False},
     why="who learns Will-O-Wisp", after=[])
```

Steps that don't list each other in `after` run at the same time. A failing or slow
step becomes an `error` result and never fails the others.

## 2. Tools

Tools live in a registry (`tools.py`). Each one declares:

| Field | Meaning |
|---|---|
| `scopes` | where it's offered: `ask`, `team`, `calc` |
| `description` | one line, shown to the LLM planner |
| `args` | a Pydantic model — the only input the tool gets |
| `closed_form` | code can fully answer from its result (no LLM needed) |
| `plannable` | `False` for built-in steps the runner adds itself |

**Tools never see the question text.** They get validated arguments plus an
`AgentContext` (scope, team, opponent, page report). So the keyword and LLM planners
behave identically for the same arguments, and every lookup is reproducible.

| Tool | Scopes | Closed-form | What it fetches |
|---|---|---|---|
| `query_pokemon` | ask, team, calc | yes | filter + rank Pokémon (types, gen, legendary, stat thresholds, sort, game) |
| `get_pokemon` | ask, team, calc | | one Pokémon's profile and a dex entry |
| `semantic_search` | ask | | lore / descriptions (hybrid vector + full-text) |
| `similar_to` | ask | | look-alikes by profile embedding, with the target's own profile |
| `user_profile` | ask | | picks from your favourites and preferred types |
| `type_matchup` | ask, team, calc | yes | type chart for 1–2 types |
| `coverage_vs_types` | ask, team, calc | | who / which moves hit types (or a Pokémon) super-effectively |
| `learnset` | ask, team, calc | per result | can X learn Y; who learns Y; X's moves — game-aware |
| `move_info` / `ability_info` / `item_info` | ask, team, calc | move only | what a move / ability / item does |
| `encounters` | ask | | where to catch a Pokémon, per game |
| `team_context` | team (built-in) | | the team, page report, analysis, opponent |
| `recommend_additions`, `propose_set_edit`, `add_member`, `duel` | team | some | see [team-coach.md](team-coach.md) |
| `calc_context` | calc (built-in) | | the calculator's state |
| `damage_calc`, `survive_threshold`, `propose_build` | calc | yes | see [damage-calc.md](damage-calc.md) |

Each tool returns a `ToolResult`:

```python
ToolResult(
    chunks=[RetrievedChunk, ...],  # citable evidence → [1], [2]… for the answer
    views=[View, ...],             # typed data the UI draws (ranking, type chart, cards…)
    summary="6 passages",          # one line for the live plan
    status="done",                 # or "empty" / "error"
    note=None,                     # guidance for the answer LLM about this evidence
    data={},                       # payload for code-rendered answers
    closed=None,                   # per-result override of closed_form
)
```

`RetrievedChunk` is described in [retrieval.md](retrieval.md). The frontend draws
`views` directly and never parses chunk text.

## 3. Choosing a planner

Cheapest first (`runner._choose_plan`):

1. **Plan cache** (Ask only) — same normalised question → same plan.
2. **Keyword planner** — always runs; free.
3. If there's no LLM key, `ASK_AGENT_ENABLED=false`, or the keyword plan is
   **confident** → use the keyword plan (the *fast path*: no planning call).
4. Otherwise the **LLM planner** makes one call. A 429, timeout (10 s), bad JSON or a
   plan with no valid steps → the keyword plan. Never a retry.

### Keyword planner (`keyword_planner.py`)

1. **Find names.** `names.find_in_text` scans the question against every Pokémon, form,
   move, type, ability and item name in the DB, longest first ("Mewtwo" before "Mew",
   "Fire Punch" before "Fire"). A span can match two kinds ("Psychic" = type and move).
2. **Pick a tool** from what was found and a few cue words (`_decide`):
   Pokémon + move → `learnset`; move alone → `move_info`; Pokémon + "like" →
   `similar_to`; type + "weak" → `type_matchup`; nothing named → `query_pokemon` if a
   ranking/filter is recognised, else `semantic_search`.
3. **Fill the other args** with small parsers: `nlfilters.restricted_filters`
   (legendary/mythical, with negation), physical/special, learn method, game
   (`learnset.find_game_in_text`), stat words and thresholds (`sql_retrieval.plan`).

**Confident** means: one valid step, every name has one meaning, no extra filters
(game, method, types, legendary), and the question — with names replaced by
placeholders — matches a fixed template:

```
"Can Pikachu learn Surf?"  →  "can P learn M"  →  confident
"Can Pikachu learn Surf in Scarlet?"            →  not confident (game filter) → LLM
```

The keyword planner matches names exactly (after lowercasing and stripping
punctuation). Misspelled names are fixed later, inside the tools (`names.resolve`,
`difflib` ≥ 0.85).

### LLM planner (`llm_planner.py`)

One strict-JSON call. The schema is built from the tools' Pydantic models: each step is
an `anyOf` of per-tool objects, so choosing `learnset` forces learnset's argument
shape. Groq uses `json_schema` mode, Anthropic a forced tool call; SDK retries are off.

The prompt lists tool names + one-line descriptions, rules ("set a filter only when
the question states it", "use names as written", "never supply a Pokémon's stats from
memory"), and four examples. It must stay under `PROMPT_BUDGET` (11k characters,
~2.75k tokens) for Groq's free-tier tokens-per-minute limit; a test fails any scope
that goes over. **The budget is nearly full** (Oct 2026: ask ~9.8k, team ~10.6k, calc
~10.4k) — a new tool in team or calc scope will likely need a shorter description or
another tool trimmed. Check with `llm_planner.prompt_size(scope)`.

The plan also has `unhandled`: constraints no argument can express ("cute"). The
answer opens by saying they weren't applied.

### Validation (`plan.py`)

Both planners' raw steps go through `make_step`: the tool must exist in this scope,
nulls are dropped for non-nullable fields, `model_validate` checks types and enums,
and `legendary=False` also sets `mythical=False` (colloquial "non-legendary"). A bad
step gets `error` instead of raising.

## 4. Answering (`runner._answer_body`)

All steps' chunks are numbered once, in step order, deduplicated, capped (12 for Ask,
16 for coaches). Then:

- **Code-rendered** — if every step is closed-form, `render.py` writes the answer from
  `views`/`data`. Names and numbers can't be hallucinated. 0 LLM calls.
- **LLM** — `answer.stream_answer` with the numbered chunks, each tool's `note`, and a
  system prompt: use only the context, cite `[n]`, say "I don't have that in the
  Pokédex data" when it can't answer, open with one direct sentence.
- **Extractive** — no key, or the answer call fails/429s: the top chunks quoted with
  their `[n]` (coaches: the page report, analysis brief or candidate list).

## 5. Budget and caching

| | Planning | Re-plan | Answer |
|---|---|---|---|
| Fast-path closed-form question | 0 | 0 | 0 |
| Typical | 0–1 | 0–1 | 0–1 |
| Max | 1 | 1 | 1 |

Usage is reported in `done` and logged. Ask plans and answers are cached in memory
(LRU, cleared on restart) by normalised question; answers aren't cached if a step
fell back or read your profile. Team and calc answers are never cached — the team and
calculator change.

## Adding a capability

Add a **tool**, not a route: a typed args model, a read-only handler returning
`RetrievedChunk`s (and a view if there's a visual), registered with its scopes. Mark it
`closed_form` only if you also add a renderer. Then add eval cases in
`backend/eval/dataset.py`.
