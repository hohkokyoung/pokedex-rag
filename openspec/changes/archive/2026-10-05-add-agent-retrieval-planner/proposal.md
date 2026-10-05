# Proposal

## Why

Ask pokérag decides what to do with hardcoded intent routing: a learnset regex, then an
LLM classifier that picks exactly one of six fixed routes, then keyword heuristics. This
causes three problems:

- **One retriever per question.** A question can only ever use one retriever, so
  multi-part questions ("fastest Fire type that learns Will-O-Wisp, and how does it do
  vs Garchomp?") get half an answer.
- **No route for some intents.** "What does Earthquake do?" has no matching route: a
  move name alone isn't treated as a learnset question, so it falls through to semantic
  search over Pokémon lore.
- **The UI parses text.** Evidence comes back as text snippets, so the UI regex-parses
  them back into charts (`lib/askEvidence.ts`) and lays them out by route name.

This change replaces routes with a **retrieval plan** of tool calls:
- With a key, the LLM decides the plan.
- With no key, or when Groq is rate-limited, a names-first keyword planner produces the
  same kind of plan.

Every answer goes through one path. LLM calls are kept to what actually adds value. This
is the foundation the team coach and calc coach will reuse.

## What Changes

- **New agent core** (`backend/app/agent/`):
  - A tool registry whose tools wrap existing retrieval and services. Each tool returns
    citable `RetrievedChunk`s plus typed **views**.
  - Two planners that output the same plan format:
    - the **LLM planner**: strict JSON, Groq and Anthropic, tuned for Groq
    - the **keyword planner**: finds Pokémon, move, ability, item and type names first,
      then picks tools; no LLM
  - A concurrent executor, and the answer step.
- **LLM efficiency**, aiming for about 1 LLM call per question on average (≤ 1.3 on the eval set) while keeping
  quality:
  - **Fast path:** a confident keyword plan for a simple, unambiguous question skips the
    LLM planner.
  - **Code-rendered answers:** closed-form results (rankings, counts, learn checks, move
    info, type matchups, learner lists) are rendered by code with no LLM answer call.
  - **Rare re-plans:** empty query results count as answers. Re-planning happens at
    most once, only for names that still don't resolve after a close-match retry, or
    for errors.
  - **Small prompts:** scoped tools, compact signatures, fixed text first so providers
    can cache it.
  - **In-memory caches** for plans and answers. The data is static at runtime.
  - **Metrics:** LLM calls and tokens are reported per question and in the eval.
- **Fallback is a planner, not a route:** no key, the `ask_agent_enabled` flag off, or
  the LLM planner failing or rate-limited (429) → keyword planner. The same tools,
  views and UI apply. If the answer call fails or is rate-limited → an extractive answer
  with the same citations.
- **BREAKING (internal API):** the Ask stream's `route` event and `AskResponse.route`
  are removed. Every question now streams `plan` (carrying `planner: "llm" | "keyword"`)
  and `step`/`view` events. `sources`, `delta` and `error` keep their shapes (each source
  gains an optional step reference), and `done` gains usage.
  The only consumers are this app's Ask page and home Ask tile, both updated here.
- **Removed:**
  - `rag/llm_router.py`
  - `ask._resolve` / `_apply_decision` / `Resolved` (folded into the keyword planner)
  - the route-based `EvidencePanel` layout, `Trace` / `ROUTE_LABELS`, and the regex
    parsing in `lib/askEvidence.ts`
- **Typed retriever arguments:** `matchup.coverage` and `learnset` gain typed entry
  points, including `legendary`/`mythical` on learnset. Planners set filters explicitly
  instead of retrievers re-reading the question text.
- **Ask UI:**
  - A live plan step list.
  - Evidence drawn only from typed views, reusing the existing visuals.
  - The home `AskTile` reads the new events.
- **Eval:**
  - `expect_tools` per case.
  - Plan accuracy for LLM and keyword plans, plus fast-path accuracy.
  - About 15 multi-part cases, plus move-only cases (Earthquake, Psychic ambiguity).
  - Average LLM calls and tokens per question.

## Out of scope

- **Team coach** (`/api/teams/{id}/ask`) and **calc coach** (`build_suggest`).
  `rag/router.py` (`classify` / `route_and_retrieve`) stays only because
  `coach.build_coach_chunks` uses it.
- **Tools that change anything** (`propose_add`, `propose_set_edit`), and
  `damage_calc` / the `damage` view.
- **New view types** for encounters, matchup/duel and ability/item. Those tools return
  evidence chunks only for now.
- **Redesigning `AskTile`.** Only its stream handling changes.
- **Native multi-turn tool calling,** and caches that persist across restarts.

## Later phases (for context; separate changes)

- **Team coach.** Replaces these with team-scoped tools on this core:
  - `is_add_command` (keyword verbs) → `propose_add`
  - `recommend.is_draft_request` + `draft_intent` → `recommend_additions` with planner
    args
  - `resolve_species` (longest name in text) → tool name lookup
  - `coach_edits` (a second LLM call that reads the answer) → `propose_set_edit` chosen
    up front
  - `router.route_and_retrieve` → the shared tools, after which `rag/router.py` is
    deleted
- **Calc coach.** Replaces `build_suggest`'s single call with `suggest_build` +
  `damage_calc`, after reconciling `battle.py` with the client-side calc.

## Capabilities

### New Capabilities

- `assistant/retrieval-planning`: how a question becomes a plan of tool calls. Covers
  the LLM and keyword planners, the fast path, tool scopes, read-only tools, name
  lookup, concurrent execution, empty results and the single re-plan, caching,
  provider support, the fallback ladder, and per-question LLM budgets and metrics.
- `assistant/grounded-answers`: how a plan's results become an answer. Covers
  evidence-only answers, numbered citations in step order, code-rendered closed-form
  answers, honest empty results, and extractive answers when no LLM is available.
- `assistant/result-views`: the streamed contract and its presentation. Covers the
  `plan`/`step`/`view` events with `planner`, the removal of `route`, typed view kinds
  tied to citations, the live step list, view-driven evidence, and the home Ask tile.

### Modified Capabilities

<!-- None: openspec/specs/ is empty; there is no existing spec for Ask routing. -->

## Impact

- **Backend:**
  - New `app/agent/` package.
  - `app/api/ask.py` becomes a thin wrapper over the runner. `_sources`/`_sse` move to
    `app/agent/` and stay importable for `teams.py`.
  - `app/rag/answer.py`: Anthropic forced-tool structured output, and usage reporting.
  - `app/rag/matchup.py` and `app/rag/learnset.py` gain typed entry points.
  - `app/rag/llm_router.py` is deleted.
  - `app/schemas/ask.py` gains plan, step, view and usage models, and drops `route`.
- **Frontend:**
  - `lib/api.ts`: the new event handlers and types.
  - New `components/agent/` with `PlanSteps`, `ViewBlock` and the view components.
  - `AskConsole.tsx` and `AskTile.tsx` are rewired.
  - `lib/askEvidence.ts` is reduced to stat constants and citation helpers.
- **Tests and eval:**
  - New pytest modules for views, planners, executor, runner, caches and SSE.
  - `test_structured_answer.py` and the eval harness move off `_resolve`.
  - `test_router.py` is kept, because the team coach still uses the router.
  - `eval/` gains `expect_tools`, plan/fast-path accuracy and call/token metrics.
- **LLM usage:** target about 1 call per question on average (measured 1.29 on the eval set; today about 1–2), worst case
  3.
- **No new dependencies. No migrations.**
