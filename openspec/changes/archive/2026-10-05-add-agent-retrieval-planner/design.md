# Design

## Context

### How Ask works today
`app/api/ask.py::_resolve` decides what to retrieve in this order:
1. A deterministic learnset check (`learnset.plan`).
2. `llm_router.classify`, which picks one of six routes.
3. Keyword heuristics: `matchup.is_matchup`, `similarity.is_similarity`,
   `personalize.is_recommendation`, then `router.classify`.

Exactly one retriever runs. The `sql` route renders with `structured_answer.render`;
every other route streams `answer.stream_answer`.

A move name alone falls through to semantic search. `learnset.plan` returns `None` for
a bare move on purpose ("a move name alone isn't a learnset question"), and no other
route covers moves.

### Frontend
- `AskConsole` lays out evidence by `route` and regex-parses snippets
  (`askEvidence.parseEvidence`, `questionStat`).
- `AskTile` also passes `route` to `rankedSources`.

### Who else uses the routing code
- `coach.build_coach_chunks` calls `router.route_and_retrieve`. The team coach is out of
  scope, so `rag/router.py` must survive this change.
- `teams.py` imports `_sources` and `_sse` from `api/ask.py`.
- `eval/harness.py` and `tests/test_structured_answer.py` import `_resolve`.

### Provider constraints
- **Active provider:** Groq `openai/gpt-oss-120b`, free tier. Reasoning tokens count
  against `max_tokens`, and there is a tokens-per-minute (TPM) limit.
- **Anthropic** is preferred when its key is set.
- `answer.quick_complete(json_schema=…)` already does Groq strict structured output.

### Retrievers that only take free text
- `matchup.coverage(question, targets)` reads physical/special, moves-vs-Pokémon and
  legendary negation from the question.
- `learnset.plan(question)` does name matching and filters together.

Motivation and scope: see `proposal.md`. Requirements: see `specs/assistant/*`.

## Goals / Non-Goals

**Goals:**
- One path for every question (plan → execute → answer) and one way to render it.
- A surface-agnostic core that the team and calc coaches can later extend with scoped
  tools.
- Tools are thin adapters over existing modules, with filters passed as typed arguments.
- About 1 LLM call per question in everyday use (≤ 1.3 on the eval set, which is weighted
  toward descriptive and multi-part questions), without losing plan quality.

**Non-Goals:**
- A native model ↔ tool loop.
- Streaming partial plans.
- Caches that persist across restarts or are shared between processes.
- Changing the team coach's or calc coach's behaviour.

## Decisions

### 1. Plan, run, answer instead of a native tool-calling loop
The plan is decided once up front. Steps run concurrently. One answer step follows,
and it may be skipped entirely.
- **Why:** a bounded, predictable number of calls on Groq's TPM limit, and a plan that
  can be shown and evaluated.
- **Rejected — a native tool loop:** an unknown number of round trips, each re-sending
  the growing context.
- **Rejected — a hybrid with several rounds:** the single, rare re-plan covers the gap.

### 2. Package layout
```
app/agent/
  tools.py            Tool(name, scopes, one-line description, args model, handler,
                      closed_form: bool); REGISTRY; tools_for(scope); signature(tool)
  results.py          ToolResult(chunks, views, summary, status: done|empty|error, note)
  views.py            Pydantic discriminated union on `kind`
  names.py            name resolution for Pokémon (incl. forms), moves, abilities,
                      items, types: exact → case-insensitive → close match; returns
                      every kind a token matches (Psychic → type + move)
  keyword_planner.py  plan_keywords(question, scope) -> KeywordPlan(steps, confident: bool)
  llm_planner.py      plan_llm(question, scope) / replan(question, plan, summaries)
  executor.py         runs steps concurrently, one session per step
  render.py           code renderers for closed-form results (wraps structured_answer)
  cache.py            in-memory LRU for plans and answers
  runner.py           run_question(question, scope) -> async iterator of events
  sse.py              _sse / _sources (moved from api/ask.py; re-exported there for teams.py)
  ask_tools.py        Ask-scope tool handlers
```

### 3. Ask-scope tools and what each one wraps

| Tool | Wraps | Views | Closed-form |
|---|---|---|---|
| `query_pokemon(StructuredQuery)` | `sql_retrieval.execute` + `count` | `ranking` (sorted) / `pokemon_list` | yes (ranking/count) |
| `get_pokemon(name)` | `similarity.target_profile_chunk` + dex-entry chunks | `pokemon_list` | no (narrative) |
| `semantic_search(query, k)` | `hybrid.hybrid_retrieve` | — | no |
| `similar_to(name, include_target)` | `similarity.similar_to` / `target_profile_chunk` | `pokemon_list` | no |
| `coverage_vs_types(targets, attacker_class?, want, legendary?, mythical?)` | `matchup.coverage_typed` (new) | `ranking`/`pokemon_list` + `type_chart` + `move_list` | no |
| `learnset(pokemon?, move?, game?, types?, damage_class?, legendary?, mythical?)` | `learnset.plan_typed` (new) + `retrieve` | `learnset` / `learners` / `learn_check` | yes (check, learners) |
| `type_matchup(types)` | `matchup.type_chart_chunk` | `type_chart` | yes |
| `move_info(name)` | `learnset.move_chunk` (+ learner count) | `move_list` | yes |
| `ability_info` / `item_info(name)` | `builder.search_abilities` / `search_items` | — | no |
| `encounters(pokemon, game?)` | `encounters.encounters_by_game` | — | no |
| `user_profile()` | `personalize.*` (incl. `preference_block` as note) | `pokemon_list` | no |

Route notes (`_similar_note`, the matchup and learnset notes) become each result's
`note`. The runner joins them into the answer's note block.

### 4. Typed retriever entry points
- **`matchup.coverage_typed` and `learnset.plan_typed`** take explicit filters,
  including `legendary`/`mythical` for learners. The existing text functions
  (`coverage(question, …)`, `plan(question)`) become wrappers that parse the text and
  delegate. Existing tests keep passing, and the keyword planner reuses the parsers.
- **`nlfilters` reads text only inside the keyword planner,** which turns sentiment
  ("no legendaries") into the `legendary=false` argument. Tools never read
  `ctx.question`, so the LLM and keyword plans behave the same for the same arguments.

### 5. Keyword planner: names first
`plan_keywords` never calls an LLM. It works in this order:
1. **Resolve names** with `names.py`. It reuses the name index that `learnset._find` and
   `similarity.resolve_by_name` already build.
2. **Pick tools** from what resolved plus cues. The first matching rule wins, except
   that a name matching several kinds produces one step per kind:

| Found | Cue | Steps |
|---|---|---|
| Pokémon + move | — | `learnset(pokemon, move)` (check) |
| move | learn/learners/who | `learnset(move, filters…)` |
| move | none | `move_info(move)` |
| Pokémon | learn/moves (no matchup words) | `learnset(pokemon)` |
| Pokémon | similar/like | `similar_to(pokemon)` |
| Pokémon | — | `get_pokemon(pokemon)` |
| type(s) | against/beats/coverage/counter | `coverage_vs_types(types, …)` (via `matchup.is_matchup`/`target_types`) |
| type | weak/resist/effective | `type_matchup(type)` |
| ability / item | — | `ability_info` / `item_info` |
| — | recommend/for me | `user_profile()` |
| — | `sql_retrieval.plan` matches | `query_pokemon(sq)` (+ `semantic_search` if lore markers, i.e. today's hybrid) |
| — | otherwise | `semantic_search(question)` |

3. **Cap and filters:** at most 3 steps. `legendary`/`mythical` come from `nlfilters`.
   Type and damage-class filters come from the existing parsers.
4. **`confident` is true only if all of these hold** (Decision 6):
   - exactly one step
   - exactly one resolved name that matches only one kind, or no name and a single
     ranking cue with no other conditions
   - the question matches a fixed phrasing list: profile ("tell me about X",
     "describe X", "who is X"), "what does X do", "can X learn Y", "who learns Y",
     "highest/lowest/fastest/slowest STAT", "Pokémon like/similar to X",
     "where can I catch/find X", "what is TYPE weak to" / "TYPE weaknesses", and
     recommendation asks ("recommend a Pokémon for me", "which Pokémon would I like").
     The last four were added after the eval: the keyword planner was 100% right on
     them, and fast-pathing them cut the average LLM calls per question.

The lore markers move from `router.py` into the keyword planner. `router.py` keeps its
own copy until the team coach change deletes it.

### 6. Planner selection and the fast path
```
cached plan? ─────────────────────────────── yes → use it
keyword plan (always computed, free)
  ├─ LLM unavailable (no key / flag off) ─────→ keyword plan
  ├─ confident ───────────────────────────────→ keyword plan        (fast path, 0 planning calls)
  └─ otherwise → LLM planner
        ├─ ok with ≥1 valid step ─────────────→ LLM plan
        └─ error / 429 / timeout / 0 valid ───→ keyword plan        (no retry)
```
- **Why the fast path is safe:** names are resolved before any decision, so
  "Earthquake" is a move rather than a lore keyword. Confidence also excludes
  ambiguity, multiple conditions and comparisons. The eval scores fast-path accuracy
  separately (Decision 13). A phrasing whose accuracy drops below the LLM planner's on
  the same cases is removed from the list.
- **Rejected — always calling the LLM planner when a key exists:** about 1 extra call on
  the most common, simplest questions, with no observed quality gain on them.

### 7. LLM plan schema that works on both providers
A step is `{id, tool, why, after: [ids], args}`, and the plan adds `needs_followup: bool`.
- **Groq:** strict `json_schema` mode, with each step an **`anyOf` of per-tool step
  objects**. Each object pins `tool` to one name and has that tool's `args` object, with
  every property `required`, optionals as `[type, "null"]`, and
  `additionalProperties: false`. Arguments are still validated server-side with the
  tool's Pydantic model.
- **Anthropic:** a single forced tool call (`tool_choice` → `submit_plan`) with the same
  schema as `input_schema`. `quick_complete` gains a `tool_schema` path.
- **Prompt cost:** the schema already carries the argument shapes, so the prompt text
  lists only each tool's name and its one-line description.
- **Spike result (task 1.3), on gpt-oss-120b:** strict `anyOf` works (≈1 s, valid plans).
  The string-`args` alternative is rejected: there the model invented step-to-step
  template references (`"{{1.results[0].name}}"`), which `anyOf` prevents. Each tool's
  schema adds about 90 prompt tokens, so tools keep their argument lists short.
- **Invalid steps** (unknown tool, bad args, dangling `after`) become error steps. If no
  valid step remains, the runner falls back to the keyword plan.

### 8. Execution
- **Session per step:** each ready step runs as an `asyncio` task with its **own**
  `AsyncSession`, because async sessions can't be shared across concurrent tasks.
- **Ordering and limits:**
  - `after` gives the order.
  - 8 s timeout per step.
  - At most 6 steps per plan, plus 3 added by a re-plan.
- **No piping:** `after` orders steps but doesn't pass data between them. "Use what
  step 1 found" is handled by the re-plan, whose summaries include resolved names.
- **Evidence cap:** chunks are concatenated in step order, deduplicated by chunk id,
  and capped at 12 for the answer prompt. Views keep their full data.

### 9. Empty results and re-plan
- **Status per step:** a tool returns `empty` when a valid query matched nothing, and
  `error` for an exception, a timeout or invalid arguments.
- **Name retry in code:** `names.py` already close-matches. The tool reports
  `error: unresolved name "<x>"` only when that also fails.
- **When to re-plan:** only on `error` steps, or when the LLM plan set
  `needs_followup`. Only LLM-planned questions re-plan. A keyword plan never triggers an
  LLM re-plan; its error steps are simply reported.
- **What the re-plan sees:** the question, the plan, and one-line summaries. It can
  only add steps.

### 10. Answer step
Answers are produced in the first of these tiers that applies:
1. **Code-rendered:** every step is `closed_form` with status `done` or `empty`.
   `render.py` produces the opening sentence plus bullets, with citations, per step
   kind, and joins them across steps with offset numbering:
   - rankings and counts reuse `structured_answer.render`
   - templates for `learn_check`, `move_info`, `type_matchup` and `learners`
   - "no Pokémon match …" for empty results
2. **LLM:** `answer.stream_answer(question, chunks, note)` with the unchanged
   `SYSTEM_PROMPT`. The note includes a one-line plan summary.
3. **Extractive:** used when there's no key, or the answer call raises or returns a
   429. `compose_extractive_answer` runs over the same chunks. If the LLM stream fails
   partway, a separator is sent and then the extractive text, so the stream still ends
   with `done`.

### 11. Caches (`cache.py`)
- **Plan cache:** an LRU of 256 entries keyed by `(scope, normalize(question))`, where
  normalize lowercases, collapses whitespace and strips trailing punctuation. Stores the
  validated plan and its planner.
- **Answer cache:** an LRU of 128 entries keyed by `(scope, normalize(question))`.
  Stores sources, views, steps and answer text.
  - Skipped when any step used `user_profile`.
  - Skipped for extractive answers produced because the LLM call failed, so the next
    ask can get a real answer.
- **Replay:** a hit replays the events with `plan.cached = true` and usage of 0 calls.
- **Safe to cache:** the data is static at runtime (ingest runs offline). Restarting the
  backend clears both caches.

### 12. Per-question LLM budget and usage reporting

| Call | When | Input budget | `max_tokens` |
|---|---|---|---|
| Plan | not cached, not confident, LLM available | ≤ 2,500 tokens: fixed text first (system, tool signatures, 4 few-shots), then the question | 1,200 (`reasoning_effort: "low"` on gpt-oss) |
| Re-plan | LLM plan with an error step or `needs_followup`; at most once | ≤ 1,500 tokens (question, plan, one-line summaries) | 800 |
| Answer | not all closed-form, LLM available | as today, ≤ 12 deduplicated chunks (~3–5k tokens) | 2,048 |

Expected calls per question:

| Question | Calls |
|---|---|
| Cached | 0 |
| Fast-path closed-form ("Can Garchomp learn Earthquake?") | 0 |
| Fast-path descriptive ("Tell me about Snorlax") | 1 |
| LLM-planned closed-form | 1 |
| LLM-planned descriptive or multi-part | 2 |
| With a re-plan | 3 |

- **Target:** an average of ≤ 1.3 calls per question on the eval set (measured 1.29), and
  about 1.0 in everyday use, where rankings and lookups dominate. Worst case is about
  9k tokens across 3 calls.
- **Prompt caching:** the fixed prompt text comes first so it can be cached. Anthropic
  `cache_control` goes on the system and tools block. Groq caches matching prompt
  prefixes automatically on models that support it, with no code needed.
- **Usage reporting:**
  - `quick_complete` and `stream_answer` report provider usage (input/output tokens).
  - The runner adds them up and sends the totals in `done.usage` and
    `AskResponse.usage`.
  - Usage is logged at INFO per question.
- **Budget test:** the rendered planning prompt for the Ask scope must stay ≤ 10,000
  characters (a proxy for the token budget).

### 13. SSE contract
Event order:
`plan{planner, cached, steps}` → `step{id, state, summary}`* → `view{step, kind, data, chunk_refs}`* → (`plan{replan: true, steps}` → `step`* → `view`*)? → `sources[…]` → `delta`* → `done{usage}`

- **No `route` event.**
- **`sources` stays a bare array of `Source`, as today.** Each entry gains two fields,
  `step` and `step_index`, so the client can map a view's step-local `chunk_refs` to
  global `n` once `sources` arrives.
- **The team coach is unaffected:** it shares `streamSSE`, but its endpoint just leaves
  the new fields out.
- **Logging:** `personalize.log_question` records `agent-llm` or `agent-keyword` in its
  route column. The column stays, and only its values change.

### 14. Frontend
- **`lib/api.ts`:**
  - `StreamHandlers` gains `onPlan`, `onStep` and `onView`, and `onDone` receives usage.
  - The `View` union mirrors `views.py`.
  - `AskResponse` drops `route` and gains `planner`, `steps`, `views` and `usage`.
- **`components/agent/views/`:** `RankChart`, `TypeChartStrip`, `CheckStrip`,
  `LearnersStrip`, `LearnsetGroup`, `MoveChart` and `EvidenceCard` move out of
  `AskConsole.tsx` with typed props.
- **`ViewBlock`:** dispatches on `kind`.
- **`PlanSteps`:**
  - Shows live states.
  - Labels keyword plans "Keyword match · no LLM" and cached plans "Cached".
  - Collapses to "N steps · Xs".
  - Transitions are CSS-only and turned off under `prefers-reduced-motion`.
- **Removed:**
  - `Trace`, `ROUTE_LABELS`, and every `route ===` branch in `EvidencePanel`
  - `askEvidence.parseEvidence` / `questionStat` / `rankedSources` and the regex helpers
  - `askEvidence.ts` keeps only `STAT_*` constants, `citedNumbers` and `followUps`
- **`AskTile`:** renders the answer and the first view (ranking or cards) via
  `ViewBlock`. Its layout is unchanged.

### Existing modules: reused, fallback-only, removed
- **Reused:**
  - `sql_retrieval` (`plan`, `execute`, `count`, `StructuredQuery`)
  - `structured_answer.render`
  - `hybrid.hybrid_retrieve`
  - `similarity.*`
  - `matchup.*` (with a typed entry)
  - `learnset.*` (with a typed entry)
  - `personalize.*`
  - `nlfilters`
  - `encounters.encounters_by_game`
  - `builder.search_abilities` / `search_items`
  - `answer.quick_complete` / `stream_answer` / `compose_extractive_answer`
- **Keyword-planner-only, no longer deciding answers directly:**
  - `matchup.is_matchup` / `target_types`
  - `similarity.is_similarity` / `find_target`
  - `personalize.is_recommendation`
  - the text wrappers `learnset.plan` and `matchup.coverage`
- **Removed:**
  - `rag/llm_router.py`
  - `ask._resolve` / `_apply_decision` / `_retrieve` / `_personalized` / `Resolved` /
    `_similar_note` (moved into tool handlers)
  - `ask._structured_answer` (moved into `render.py`)
  - the frontend items listed in Decision 14
- **Kept only for the team coach** (deleted in that change): `rag/router.py`
  (`classify`, `retrieve_for_route`, `route_and_retrieve`) and `tests/test_router.py`.

### Eval
- **`EvalCase` gains fields:**
  - `expect_tools: list[ToolExpect]`: a tool name plus key args that must match.
  - `multi_part: bool`.
  - `fast_path: bool | None`: whether the question should take the fast path.
- **Harness, with an LLM:**
  - Runs the planner selection.
  - Reports:
    - plan accuracy, split into LLM plans and fast-path plans
    - multi-part accuracy
    - fallback count (429s)
    - average LLM calls per question
    - average input/output tokens per question
  - Checks retrieval hits over the union of step chunks.
- **Harness, keyless:** keyword-plan accuracy against `expect_tools`. This replaces
  route accuracy.
- **New cases:**
  - about 15 multi-part
  - move-only: "What does Earthquake do?", "Who learns Earthquake?",
    "Tell me about Psychic" (should not take the fast path)
  - legendary negation on learners
- **Moves off `_resolve`:** `eval/harness.py` and `tests/test_structured_answer.py`
  switch to `keyword_planner` + executor + `render`.

## Risks / Trade-offs

- **[The fast path mis-plans a simple question]** → Names resolve first. Confidence is
  strict (one unambiguous name and a fixed phrasing list). The eval measures fast-path
  accuracy separately, and a phrasing that underperforms is removed.
- **[gpt-oss mis-plans: wrong tool or over-planning]** → 4 few-shot examples (one
  multi-part), a cap of 6 steps, and plan accuracy per category in the eval.
- **[Planning adds latency on non-fast-path questions]** → Low reasoning effort, a small
  prompt with the fixed part first, and immediate `plan`/`step` events. Closed-form
  plans skip the answer call.
- **[Groq TPM 429s]** → No retries. Planning falls back to the keyword plan and the
  answer falls back to extractive, within the same request. The eval counts fallbacks.
- **[Caching a wrong answer repeats it]** → The cache is in memory and cleared on
  restart. Extractive answers from LLM failures and profile-based answers are never
  cached.
- **[Two planners can drift apart]** → Both emit the same plan format into the same
  tools. The eval checks `expect_tools` against both.
- **[`Source` gains fields that the shared `streamSSE` passes to the team coach too]** →
  The fields are optional, and the coach endpoint leaves them out.
- **[Concurrent sessions per step]** → At most 6 per request, and the app is
  single-user. The default pool (5 + 10 overflow) is enough.
- **[The per-tool `anyOf` schema grows the prompt with every tool]** → Short argument
  lists, scope-filtered tools, and the prompt-size test. Server-side Pydantic validation
  still runs on every step.
- **[gpt-oss chains steps through `after` instead of filtering directly]** → Seen in
  the spike: "fast Fire types" was queried first, then learners. Tools take filters
  directly (e.g. `learnset(types=…)`), and a few-shot example shows one filtered step
  instead of a chain.

## Migration Plan

- **No DB migration and no new dependencies.** Backend and frontend ship together,
  since the stream format changes.
- **`ask_agent_enabled=false`** disables LLM planning, so every question uses the
  keyword planner. That is the quick switch if LLM planning misbehaves. Going back to
  route-based Ask needs a git revert.
- **Later changes:** the team coach and calc coach changes register `team` / `calc`
  tools, call `runner.run_question(scope=…)`, and delete `rag/router.py`.

## Open Questions

- The exact few-shot set and fast-path phrasing list, both tuned against the eval during
  this change.
