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
| `learnset` | ask, team, calc | per result | can X learn Y; who learns Y; X's moves — game-aware, optional level cap |
| `move_info` / `ability_info` / `item_info` | ask, team, calc | move only | what a move / ability / item does |
| `encounters` | ask | | where to catch a Pokémon, per game |
| `team_context` | team (built-in) | | the team, page report, analysis, opponent |
| `recommend_additions`, `propose_set_edit`, `add_member`, `duel` | team | some | see [team-coach.md](team-coach.md) |
| `calc_context` | calc (built-in) | | the calculator's state |
| `damage_calc`, `survive_threshold`, `propose_build` | calc | yes | see [damage-calc.md](damage-calc.md) |

Each tool returns a `ToolResult` (`results.py`): citable **chunks** (numbered `[n]` for
the answer), typed **views** the UI draws, a one-line **summary** for the live plan, a
**status** (`done` / `empty` / `error`), and optional **data** for code-rendered answers
and a **note** that guides the answer LLM.

`RetrievedChunk` is described in [retrieval.md](retrieval.md). The website and the
mobile app draw `views` directly and never parse chunk text.

Views are typed in the API: `AskResponse.views` is the `View` union (`agent/views.py`),
discriminated by `kind`, so the OpenAPI schema lists every view and generated clients
decode them. Each view carries the `step` that produced it (the runner sets it), and its
`chunk_refs` are indexes into that step's chunks; a source's `step` + `step_index` map
them to the answer's global `[n]`.

## 3. Choosing a planner

Cheapest first (`runner._choose_plan`):

1. **Plan cache** (Ask only) — same normalised question → same plan.
2. **Keyword planner** — always runs; free.
3. If there's no LLM key, `ASK_AGENT_ENABLED=false`, or the keyword plan is
   **confident** → use the keyword plan (the *fast path*: no planning call).
4. Otherwise the **LLM planner** makes one call. A 429, timeout (10 s), bad JSON or a
   plan with no valid steps → the keyword plan. Never a retry.

Details of each planner — name finding, the confidence test, the LLM schema and
prompt budget, step validation — are in [ask-agent-planners.md](ask-agent-planners.md).

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

## 6. Plan traces

Every answered question stores how it was planned and answered, at no LLM cost — see
[ask-agent-traces.md](ask-agent-traces.md). When the runner gains a decision (a new
fallback or answer path), record it in the trace.

## Adding a capability

Add a **tool**, not a route: a typed args model, a read-only handler returning
`RetrievedChunk`s (and a view if there's a visual), registered with its scopes. Mark it
`closed_form` only if you also add a renderer. Then add eval cases in
`backend/eval/dataset.py`.
