# Proposal

## Why

Ask now answers from a retrieval plan (`assistant/retrieval-planning`). The team coach still
decides what to do with hardcoded intent checks, spread across both layers:

- **`is_add_command` and `resolve_species`.** Keyword verbs plus "longest Pokémon name in
  the text" decide an add.
- **`is_draft_request` and `draft_intent`.** Keyword detection, then an LLM call just to
  pull out drafting preferences.
- **`build_coach_chunks`.** Every question gets the whole team, analysis and suggestions,
  plus dex retrieval through the old `rag/router.py` routes.
- **`coach_edits`.** A second LLM call re-reads the finished answer to recover set changes.
- **The frontend `EDIT` regex in `TeamCoach.tsx`.** Set-change requests go straight to the
  build coach and skip the coach entirely, so they can't be combined with anything else.

A draft question costs 3 LLM calls (preferences, answer, edit extraction). `rag/router.py`
only survives because of this path. This change moves the coach onto the agent core so one
system plans every assistant question.

## What Changes

- **A `team` scope for the agent.**
  - The coach endpoint (`POST /api/teams/{id}/ask`) runs `runner.run_question(scope="team")`.
  - The team and the optional opponent travel in the agent context.
  - The Ask dex tools (rankings, learnsets, moves, abilities, items, type charts,
    coverage) are also registered for `team` scope, so dex questions on the team page use
    the same tools. Lore search, look-alikes, profile picks and encounters stay Ask-only.
- **Team context is always attached.**
  - A *team context* step runs on every coach question, before planning results arrive:
    members, analysis, per-slot suggestions, the page's report, and the opponent matchup
    when an opponent is selected.
  - The planner only plans *extra* lookups.
  - Plain team questions ("what's my team's biggest weakness?") take the fast path, with
    no planning call.
- **New team tools.** The planner fills in their arguments.
  - `recommend_additions(role, legendary, mythical, types)` wraps the existing
    deterministic recommender. It replaces `is_draft_request` and `draft_intent`.
  - `propose_set_edit(member, side, request)` wraps `build_suggest`, so every field is
    validated against legal data. It returns a was → now proposal, and nothing is saved.
    It replaces the frontend `EDIT` shortcut and `coach_edits`.
  - `add_member(pokemon)` is used only for an explicit imperative ("add Garchomp"). It
    fills the next empty slot right away, and the reply offers **Undo**. A deliberation
    ("should I add Garchomp?") only ever shows Add cards.
  - `duel(our, theirs)` plays one pairing out with the existing deterministic duel engine.
- **New view kinds.**
  - `candidates`: the existing recommendation cards, with Add / Replace / Revert.
  - `set_edit`: the existing was → now card, with Apply / Revert.
  - `member_added`: what was added and where, with Undo.
  - `duel`.
  - The existing `candidates`, `edits` and `team_updated` SSE events are replaced by
    views. `team_updated` stays, but only for adds that actually happened.
- **The keyword planner learns team phrasings** for the no-key / 429 path: add, draft,
  set change and matchup. Without an LLM, set changes explain that they need a key, as
  today.
- **Coach UI.** `TeamCoach` uses the shared stream hook and shows the compact live plan
  steps. Candidates, set edits, adds and duels render from views. The client-side intent
  routing (`EDIT`, `findMember`, direct `suggestBuild`) is removed.
- **BREAKING (internal API):** the coach stream drops its `candidates` and `edits` events
  and gains `plan`, `step` and `view`. Its only consumer is `TeamCoach`, which is updated
  here.
- **Removed:**
  - `rag/router.py`, `rag/draft_intent.py`, `rag/coach_edits.py`
  - `coach.is_add_command`, `coach.resolve_species`, `recommend.is_draft_request`, and
    the routing part of `coach.build_coach_chunks`
  - their tests, replaced by agent-level tests
- **Eval:**
  - Coach cases gain `expect_tools`.
  - Add cases for draft, set change, add vs. deliberation, and a dex lookup asked from
    the team page.
  - LLM calls per coach question are reported.

## Out of scope

- **The calc coach** on the home damage calculator (`/api/builder/builds/suggest` from
  `page.tsx`) is phase 3. `build_suggest` itself stays and is reused here.
- **Team summary and strategy** (`team_summary.py`, `team_strategy.py`) are background
  description, not question answering, and are unchanged.
- **Multi-turn memory** for the coach. Each question is planned on its own, as today.
- **Server-side Undo history.** Undo uses the existing slot endpoints from the client, as
  Replace / Revert do now.

## Capabilities

### New Capabilities

- `team-coach/coach-planning`: how a coaching question is answered. Covers the team scope,
  the always-attached team context, team tools and their arguments, the fast path for
  plain team questions, the keyword fallback, and the per-question LLM budget.
- `team-coach/coach-actions`: what the coach may change and how. Covers explicit adds with
  Undo, Add cards for deliberation, validated set-edit proposals with Apply/Revert,
  recommendations as cards, and nothing saved without a click or an explicit command.

### Modified Capabilities

- `assistant/result-views`: "Results are streamed as typed views" gains the `candidates`,
  `set_edit`, `member_added` and `duel` kinds.
- `assistant/retrieval-planning`: "Tools are limited to read-only Pokédex data" now
  applies per scope. Ask tools stay read-only, while the team scope may change the user's
  team, only through the actions in `team-coach/coach-actions`.

## Impact

- **Backend:**
  - `app/agent/` gains `team_tools.py`, team scope in `keyword_planner` and `llm_planner`,
    a team context step in `runner`, and new view models.
  - `app/api/teams.py`: `coach_ask` becomes a thin wrapper over the runner.
  - `app/rag/coach.py` shrinks to the team-context chunk builders (member, analysis,
    suggestions, vs-opponent, report).
  - `app/rag/build_suggest.py` gains a single-attempt option for use inside the agent.
  - Deleted: `rag/router.py`, `rag/draft_intent.py`, `rag/coach_edits.py`.
- **Frontend:**
  - `TeamCoach.tsx` is rewired onto `useAsk`-style streaming with `PlanSteps`.
  - The views render with the existing `co-cand` and `ProposalCard` visuals, moved into
    `components/agent/views/`.
  - `lib/api.ts` gains the new view types and drops the `onCandidates` / `onEdits`
    handlers.
- **Tests and eval:**
  - New team-scope tests: tools, planner, add with Undo, set-edit validation, SSE.
  - `test_coach_intents.py`, `test_draft_intent.py` and the `coach_edits` tests are
    removed or rewritten.
  - `eval/` coach cases get `expect_tools`.
- **LLM usage per coach question:**
  - At most 1 plan call, at most 1 build-coach call (single attempt), at most 1 answer
    call.
  - A draft drops from 3 calls to 1–2. A plain team question costs 1 (answer only).
  - A set change alone costs 1 (the build coach's explanation is the answer).
- **No new dependencies. No migrations.**
