# Tasks

## 1. Agent core scaffolding and provider support

- [x] 1.1 Create `backend/app/agent/` with these modules, then verify with `tests/test_agent_views.py` that each view kind round-trips through `model_dump`/`model_validate`:
  - `results.py`: `ToolResult` (chunks, views, summary, status, note)
  - `views.py`: a union on `kind` for `ranking`, `pokemon_list`, `type_chart`, `move_list`, `learnset`, `learners` and `learn_check`, each with `chunk_refs`
- [x] 1.2 Add `tools.py` with the `Tool` dataclass (name, scopes, one-line description, args model, handler, `closed_form`), `REGISTRY`, `tools_for(scope)` and `signature(tool)`. Verify with a pytest that a registered dummy tool appears in `tools_for("ask")` and that its signature string is stable.
- [x] 1.3 Spike Groq strict `json_schema` with per-tool `anyOf` args against `openai/gpt-oss-120b`, using a throwaway script in the scratchpad. Record the outcome in `design.md` Decision 7: keep string args, or switch to `anyOf`. Verify by noting the outcome there.
- [x] 1.4 Extend `answer.quick_complete` and `stream_answer`. Verify with a unit test that mocks both clients and asserts the request shape and the reported usage for each provider. The changes are:
  - Anthropic forced-tool structured output (`tool_schema=`) next to the Groq `json_schema` path
  - `reasoning_effort: "low"` for gpt-oss planning
  - Anthropic `cache_control` on the fixed system/tools prefix
  - provider usage (input/output tokens) returned alongside the result
- [x] 1.5 Add `ask_agent_enabled: bool = True` to `Settings`. When it is false, LLM planning is off and every question uses the keyword planner. Verify with a settings test that it defaults to true and reads from env.
- [x] 1.6 Move `_sse` / `_sources` into `app/agent/sse.py`, re-export them from `api/ask.py`, and give `Source` the optional fields `step` and `step_index`. Verify that `teams.py` still imports them and that `tests/test_team_coach.py` passes.

## 2. Typed retrieval entry points and name lookup

- [x] 2.1 Add `matchup.coverage_typed(session, targets, *, attacker_class, want, legendary, mythical, k)`, and make `matchup.coverage(question, targets)` parse the text and delegate to it. Verify that `tests/test_coverage.py` passes unchanged, plus a new direct test for "special attacker vs Dark".
- [x] 2.2 Add `learnset.plan_typed(session, pokemon=, move=, game=, types=, damage_class=, legendary=, mythical=)`, applying legendary/mythical to learner lists, and keep `learnset.plan(question)` as the text wrapper. Verify that the existing learnset tests pass unchanged, plus new tests for pokemon-only, move-only, pair, and `legendary=False` learners (no legendaries returned).
- [x] 2.3 Add `agent/names.py`, reusing the existing name indexes. It resolves Pokémon (with forms), moves, abilities, items and types: exact, then case-insensitive, then close match, returning **every** kind a token matches. Verify with `tests/test_agent_names.py`:
  - "charizrd" → Charizard
  - "psychic" → type and move
  - an unknown name → nothing
  - a form name resolves

## 3. Ask-scope tools

- [x] 3.1 Implement `query_pokemon` (args = `StructuredQuery`, `closed_form`). It emits a `ranking` view when sorted, else `pokemon_list`, and status `empty` when there are no rows. Verify with a pytest that `sort_by=attack, limit=5` gives a ranking with Kartana first and a total equal to `count`, and that an impossible filter gives `empty`.
- [x] 3.2 Implement `get_pokemon`, `similar_to` and `user_profile`, wrapping `similarity.*` and `personalize.*`. They emit `pokemon_list` and carry the similar/personalized notes. Verify with pytest that Blaziken's similar list excludes its evolution line and that `user_profile` carries the preference note.
- [x] 3.3 Implement `semantic_search` (no view), `type_matchup` (`type_chart`, `closed_form`) and `move_info` (`move_list`, `closed_form`). Verify with pytest that Fire's weaknesses are water/ground/rock and that Will-O-Wisp's type and learner count are reported.
- [x] 3.4 Implement `coverage_vs_types` on top of 2.1, and `learnset` on top of 2.2. `learnset` emits `learnset` / `learners` / `learn_check`, with check and learners being `closed_form`. Verify with pytest:
  - special coverage vs Dark returns only special-move learners
  - Pikachu + Surf gives a `learn_check`
  - unresolvable names give `error: unresolved name`
- [x] 3.5 Implement `ability_info`, `item_info` and `encounters` as chunk-only tools. Verify with pytest that a known name returns at least one chunk and an unknown one returns `empty`.
- [x] 3.6 Add registry tests. Verify with `make test`. They cover:
  - every Ask tool is read-only (a session spy on `add`/`flush`/`commit`)
  - no tool reads the question text from context
  - the rendered Ask planning prompt is ≤ 10,000 chars

## 4. Planners

- [x] 4.1 Implement `keyword_planner.plan_keywords(question, scope)` using the name-first rule table in design Decision 5: at most 3 steps, one step per kind for ambiguous names, filters taken from the existing parsers and `nlfilters`, and lore markers copied from `router.py`. Verify with `tests/test_keyword_planner.py`, covering each scenario in the retrieval-planning spec:
  - Earthquake → `move_info`
  - "Who learns Earthquake" → learners
  - Garchomp + Earthquake → check
  - Psychic → type + move
  - highest Attack → ranking
  - Snorlax → profile
  - like Gengar → similar
  - lore → semantic
  - recommend → `user_profile`
  - "non-legendary … learns X" → `legendary=False`
- [x] 4.2 Implement the `confident` flag: one step, one single-kind name (or a lone ranking cue), and a fixed phrasing list. Verify with pytest that "Can Garchomp learn Earthquake?", "What does Earthquake do?" and "Highest Attack" are confident, and that "Tell me about Psychic", "Fastest non-legendary Fire type that learns Will-O-Wisp" and "Moves that beat Garchomp" are not.
- [x] 4.3 Implement `llm_planner.plan_llm(question, scope)`: a prompt from tool signatures plus 4 few-shot examples with the fixed part first, the provider-specific plan schema, and validation (unknown tool, bad args or a dangling `after` become error steps; max 6). Verify with pytest using a stubbed `quick_complete` that returns valid, partially invalid and fully invalid plans.
- [x] 4.4 Implement `llm_planner.replan(question, plan, summaries)`. It runs only for LLM plans with an error step or `needs_followup`, adds at most 3 steps, and never repeats a step that succeeded. Verify with a stubbed-LLM pytest that an `empty` query step does not trigger it and an unresolved-name error does.

## 5. Executor, answers, caches and runner

- [x] 5.1 Implement `executor.run(plan)`: one session per step, `after` ordering, an 8 s timeout per step, and failures turned into error steps. Verify with pytest using fake tools (a sleeper and a raiser) that independent steps overlap, the timeout reports `error`, and the others complete.
- [x] 5.2 Implement `render.py` with code answers for closed-form results:
  - rankings and counts via `structured_answer.render`
  - templates for `learn_check`, `move_info`, `type_matchup` and `learners`
  - "no Pokémon match …" for `empty`
  - joined across steps with offset citation numbering

  Verify with pytest: a two-step closed-form plan has correct `[n]` numbering, and each template opens with one direct sentence.
- [x] 5.3 Implement `cache.py`: a plan LRU (256) and an answer LRU (128) keyed by `(scope, normalized question)`, skipping profile-based answers and extractive answers from LLM failures. Verify with pytest that a repeat question hits, a profile plan never serves a cached answer, and normalization treats "Who learns Earthquake?" and "who learns earthquake" as the same.
- [x] 5.4 Implement `runner.run_question(question, scope)`. Verify with stubbed-LLM pytests: the event order, citation numbering across two steps, and LLM-call counts (fast-path closed-form = 0, fast-path descriptive = 1, LLM closed-form = 1, LLM multi-part = 2). It covers:
  - planner selection (cache → keyword → fast path → LLM → keyword fallback), as in Decision 6
  - the executor, plus at most one re-plan
  - the answer tiers: code-rendered, then LLM, then extractive
  - the 12-chunk deduplicated cap
  - usage totals
  - the events: `plan`, `step`, `view`, `sources` with step refs, `delta`, `done{usage}`
- [x] 5.5 Test the fallbacks with stubbed-LLM pytests:
  - no key → keyword plan, extractive answer for descriptive questions
  - flag off → keyword plan
  - planner 429/error/timeout/zero-valid → keyword plan with no retry
  - answer-call 429 (including mid-stream) → extractive answer over the same sources, ending in `done`

## 6. Ask API wiring and legacy removal

- [x] 6.1 Wire `POST /api/ask/stream` to `runner.run_question(scope="ask")`. Log questions as `agent-llm` / `agent-keyword`. Verify with an httpx streaming test that the event sequence is right, no `route` event is sent, and `sources`/`delta` keep their shapes.
- [x] 6.2 Change `AskResponse`: drop `route`, add `planner`, `steps`, `views` and `usage`, and wire `POST /api/ask` through the runner. Verify with an API test for both an LLM-planned (stubbed) and a keyless question.
- [x] 6.3 Delete the old routing code:
  - `rag/llm_router.py`
  - `ask._resolve` / `_apply_decision` / `_retrieve` / `_personalized` / `Resolved` / `_similar_note` / `_structured_answer`

  Then move `tests/test_structured_answer.py` onto keyword planner + executor + `render`, and keep `rag/router.py` and `tests/test_router.py` for the team coach. Verify with `grep -rn "llm_router\|_resolve\b" backend/` (no hits outside history) and `make test`.
- [x] 6.4 Run `make test` and `make lint` and verify both pass.

## 7. Eval

- [x] 7.1 Add `expect_tools`, `multi_part` and `fast_path` to `EvalCase`, and fill them in for every existing case. Verify with `tests/test_eval.py` that every case has `expect_tools` or is a refusal.
- [x] 7.2 Add cases. Verify by reviewing `eval/dataset.py` for the expected tools on each:
  - about 15 multi-part
  - the move-only cases: "What does Earthquake do?", "Who learns Earthquake?", "Tell me about Psychic" (`fast_path=False`)
  - legendary negation on learners
- [x] 7.3 Move `eval/harness.py` off `_resolve`. Verify by running `make eval`: the report shows every metric, with no regression in the existing retrieval hit rate and an average of ≤ 1.3 LLM calls per question on the eval set (≤ 1.0 is the everyday-use goal; the eval set is weighted toward descriptive and multi-part questions). The metrics are:
  - plan accuracy, split into LLM and fast path
  - multi-part accuracy
  - keyword-plan accuracy (keyless)
  - fallback count
  - average LLM calls and tokens per question

## 8. Frontend: stream client and views

- [x] 8.1 Update `lib/api.ts`. Verify with `npm run lint` and `tsc --noEmit`. The changes are:
  - the `PlanStep`, `View` (mirroring `views.py`) and `Usage` types
  - `Source.step` / `step_index`
  - `onPlan`, `onStep` and `onView`
  - `onDone(usage)`
  - `AskResponse` without `route`
  - removal of `onRoute` from `StreamHandlers`
- [x] 8.2 Move `RankChart`, `TypeChartStrip`, `CheckStrip`, `LearnersStrip`, `LearnsetGroup`, `MoveChart` and `EvidenceCard` into `components/agent/views/` with typed props. Then delete `parseEvidence`, `questionStat`, `rankedSources` and the regex helpers from `askEvidence.ts`. Verify that `grep -n "parseEvidence\|questionStat" frontend/` has no hits and that `tsc --noEmit` passes.
- [x] 8.3 Build `components/agent/ViewBlock.tsx`, which dispatches on `kind` and maps `chunk_refs` to global `n` via `Source.step`/`step_index`. Verify in the browser that a ranking + type chart answer renders both in step order.
- [x] 8.4 Build `components/agent/PlanSteps.tsx` with live states, a reason per step, "Keyword match · no LLM" and "Cached" labels, collapse to "N steps · Xs", expand on click, CSS-only transitions turned off under `prefers-reduced-motion`, and the light "Instrument" tokens. Verify in the browser with a multi-step question, and again with reduced motion emulated.
- [x] 8.5 Rewire the home `AskTile` to `plan`/`view`/`sources` events, rendering the answer and its first view via `ViewBlock` with its layout unchanged. Verify in the browser that "Fastest Pokémon" on the home tile shows the ranking.

## 9. Frontend: AskConsole integration

- [x] 9.1 Rewire `AskConsole`:
  - `PlanSteps` replaces `Trace`
  - `EvidencePanel` renders views in step order, plus evidence cards for leftover sources
  - remove `ROUTE_LABELS` and every `route ===` branch

  Verify in the browser that "Which Fire types learn Will-O-Wisp, and what is Fire weak to?" shows live steps, a learners view and a type chart.
- [x] 9.2 Hover linking: a citation `[n]` highlights its row or card in a view, and the reverse. Verify in the browser on a ranking answer.
- [x] 9.3 Run `npm run lint` and `npm run build` in `frontend/` and verify both succeed.

## 10. Integration and docs

- [x] 10.1 End-to-end check against the Compose stack with the Groq key. Verify by recording the outcomes and `done.usage` call counts in the change's task notes. Check:
  - eval samples s1, m1, h1 and p1, plus a refusal
  - three multi-part questions
  - "What does Earthquake do?" and "Can Garchomp learn Earthquake?" (expect 0 LLM calls)
  - a repeated question (expect a cache hit)
  - the home `AskTile`
  - repeat with `ask_agent_enabled=false` and with no keys: Earthquake → move info, "Tell me about Psychic" → type + move
- [x] 10.2 Update `CLAUDE.md`. Verify by reading it against `design.md`. It should cover:
  - replace the routing section with the plan → execute → answer agent (`app/agent/`)
  - LLM and keyword planners and the fast path, tool scopes, typed views and the SSE events
  - answer tiers, caches, and the per-question LLM budget
  - that `rag/router.py` remains only for the team coach
  - the "sql route skips the LLM" convention generalised to closed-form answers

## Notes

**7.3 eval: plans-only, 2026-10-05.** `eval.run --plans-only`: the real planners and tools
run; answer calls are counted, not made. Results:
- LLM plan accuracy 100%, fast-path plan accuracy 100%, fast-path agreement 100%.
- Multi-part accuracy 93%. The one miss was a Groq 429 that fell back to the keyword plan.
- Retrieval recall 100%.
- **Average LLM calls 1.38 per question, missing the ≤ 1.0 target.** Descriptive questions (2
  calls), refusals (2) and the 15 multi-part cases pull it up. Rankings and lookups average 0–1;
  learnset and move questions are mostly 0.
- Planning cost about 1.9k input and 130 output tokens per call.

**10.1 end-to-end, live stack on Groq, 2026-10-05.**
- s1, Earthquake and Garchomp + Earthquake: fast path, 0 LLM calls, under 0.1 s.
- m1: fast path plus an LLM answer, 1 call. h1, p1, r1: 2 calls each; r1 abstains.
- Multi-part: "Earthquake + can Garchomp learn it" took 1 call (both parts rendered by code);
  "Compare Gengar and Alakazam" and "Ghost weakness + look-alikes" took 2 each.
- A repeated question came from the cache with 0 calls.
- Every `[n]` was within the sources list.
- Home AskTile: OK in the browser ("Fastest Pokémon" ranking).
- Keyless and `ASK_AGENT_ENABLED=false`: Earthquake gives move info; Psychic gives the move and
  the type chart, both by keyword plan.
- One answer-quality issue: the LLM mis-compared Speed (110 vs 120) in the Gengar/Alakazam answer.
  The numbers were correctly cited; the wording was wrong.
- Test questions were removed from `question_log`.

**7.3 follow-up: wider fast path (option B), 2026-10-05.** Added four fast-path phrasings, with
the spec and design updated: Pokémon-like-X, where-to-catch-X, what-is-TYPE-weak-to, and
recommend-me. The keyword planner was 100% right on all four. Recomputed without new LLM spend:
fast-pathed cases are costed exactly from the code-answer rule, and the rest keep their
measured counts. The average is now **1.29 LLM calls per question** (was 1.38); u6 is counted as
a normal 2-call run rather than its 429 fallback. What remains is mostly inherent: descriptive,
off-topic and multi-part questions need a plan call and an answer call.
