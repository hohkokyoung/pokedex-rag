# Tasks

## 1. Agent core: team scope plumbing

- [x] 1.1 Give `AgentContext` the fields `team`, `opponent` and `report`. Give `Tool` the field `plannable: bool = True`, and make `tools_for(scope, plannable_only=False)` able to filter on it. Register every Ask tool with `scopes=("ask", "team")`. Verify with a pytest that `tools_for("team")` includes the Ask tools and that `tools_for("ask")` excludes team tools.
- [x] 1.2 Give `build_suggest.suggest_build` the parameters `attempts: int = 2` and `usage: Usage | None`, passing usage through to `quick_complete`. Verify with a stubbed-LLM pytest that `attempts=1` makes exactly one call and that usage is counted. `tests/test_build_suggest.py` must still pass.
- [x] 1.3 Add the view models `CandidatesView`, `SetEditView`, `MemberAddedView` and `DuelView` to `views.py`, and extend the union. Verify with `tests/test_agent_views.py`: every kind round-trips.

## 2. Team tools

- [x] 2.1 Implement the built-in `team_context` tool (`plannable=False`, team scope) using the `coach.py` chunk builders. Order: report first, then members, analysis, suggestions, and, when there's an opponent, opponent members and vs-opponent. Note: the trimmed `COACH_NOTE`. Verify with a DB pytest on a temporary team: the report chunk is first, and opponent chunks appear only when an opponent is set.
- [x] 2.2 Implement `recommend_additions(role?, legendary?, mythical?, types, limit?)` (team scope, `candidates` view, not closed-form) over `recommend.recommend_additions(question="", prefs=DraftPrefs(...))`. Verify with pytest that sweeper with legendaries excluded returns fast non-legendaries, excludes current members, and fills the view's `team_full`/`members` correctly.
- [x] 2.3 Implement `propose_set_edit(member, side, request)` (team scope, closed-form, `set_edit` view). It resolves the member in the chosen roster (close match), builds the current set, calls `suggest_build(attempts=1, usage=…)`, and computes the changed `fields`. Verify with a stubbed-LLM pytest:
  - the proposal has `before`/`after`/`fields`, and invented options are dropped
  - an unknown member is an error step saying it isn't on the team
  - with no key, the error says it needs an LLM key
  - `side="theirs"` targets the opponent
- [x] 2.4 Implement `add_member(pokemon)` (team scope, closed-form, `member_added` view) with normal and card modes. Normal mode saves the next empty slot and schedules the team summary; it refuses a full team or a duplicate. Card mode returns a one-card `candidates` view. Verify with DB pytests: an add with space saves the slot and returns the updated team; full and duplicate change nothing; card mode changes nothing. Clean up the temporary teams.
- [x] 2.5 Implement `duel(ours, theirs)` (team scope, `duel` view) over `team_analysis.duel_detail`. Check for an existing team-page duel visual and record the outcome in `design.md` Open Questions. Verify with a DB pytest on temporary teams: a named pairing returns a duel view, and the step errors without an opponent.
- [x] 2.6 Add registry tests. Verify with `make test`. They cover:
  - every team tool except `add_member` is read-only (session spy)
  - `team_context` is never in the planner schema
  - the team planning prompt is ≤ 10,500 characters

## 3. Planners and runner for team scope

- [x] 3.1 Move the imperative-add check (`_ADD_VERBS`/`_DELIBERATE` from `coach.py`), `_DRAFT_KEYWORDS`, and the set-change and opponent cues (ported from `TeamCoach.tsx` `EDIT`/`THEIRS`) into `keyword_planner.py`. Implement team-scope planning in the Decision 5 order, with the `ctx` roster. Verify with `tests/test_keyword_planner.py` team cases:
  - "add Garchomp" → `add_member`, confident
  - "should I add Garchomp?" → not an add
  - "give Garchomp a faster set" → `propose_set_edit`, confident
  - "give their Salamence a bulkier set" → side `theirs`
  - a draft with "non-legendary sweepers" → `recommend_additions` with the right args, not confident
  - "Garchomp vs Gyarados" → `duel`
  - "can Garchomp learn Swords Dance" → `learnset`
  - "what's my team's biggest weakness?" → no extra steps, confident
- [x] 3.2 Team scope in `llm_planner`. Verify with a stubbed-LLM pytest that the team prompt contains the roster and the schema has the team tools but not `team_context`, that an empty plan is accepted for team scope, and that it's still rejected (fallback) for Ask. The changes are:
  - the roster line in the user message
  - team rules and few-shots
  - `plan_schema("team")`
  - accept empty plans for team scope
- [x] 3.3 Runner for team scope. Verify with stubbed-LLM pytests using temporary teams. The runner work:
  - prepend the `ctx` step
  - the imperative gate for `add_member` (card mode when the check fails)
  - send `team_updated` after a real add
  - exclude the context step from the closed-form check and from per-step quotas
  - raise the answer chunk cap to 16 for team scope
  - renderers for `set_edit` and `member_added`
  - the coach keyless/failure fallback (draft list → report → analysis brief, plus closed-form renders)

  The tests:
  - a planner that wrongly adds on "should I add Garchomp?" saves nothing and shows a card
  - "add Garchomp" saves, sends `team_updated` and makes 0 LLM calls
  - a set change alone makes 1 LLM call, with `why` as the answer
  - a plain question makes 1 call and the report is source [1]
  - a draft makes ≤ 2 calls
  - keyless with a report sends the report text

## 4. Coach API and cleanup

- [x] 4.1 Rewrite `coach_ask` in `api/teams.py`: load the team, opponent and analysis into `AgentContext`, call `run_question(scope="team")`, frame the events as SSE, and log questions as `coach-llm`/`coach-keyword`. Remove `_handle_add`. Verify with an httpx streaming test: the event order, no `candidates`/`edits` events, and an add sends `team_updated`.
- [x] 4.2 Remove the old routing code: `rag/router.py`, `rag/draft_intent.py`, `rag/coach_edits.py`, `coach.build_coach_chunks`/`is_add_command`/`resolve_species`, and `recommend.is_draft_request`/`allow_legendary`. Delete or rewrite their tests (`test_router.py`, `test_draft_intent.py`, `test_coach_intents.py`, the coach_edits test in `test_team_coach.py`, and `resolve_species` in `test_recommend.py`). Keep `test_page_report_is_the_coach_first_source` by pointing it at the context step. Verify that `grep -rn "rag.router\|draft_intent\|coach_edits\|is_draft_request\|resolve_species" backend/` has no hits, and `make test` passes.
- [x] 4.3 Run `make test` and `make lint` and verify both pass.

## 5. Eval

- [x] 5.1 Give `CoachCase` the fields `expect_tools` and `fast_path`. Add the cases: imperative add, deliberation, set change, draft with sentiment, dex lookup from the team page, and duel. Move `evaluate_coach` onto `run_question(scope="team")`, with keyless and `--plans-only` modes. Verify with `tests/test_eval.py`: keyless coach keyword-plan accuracy is 100% on single-intent coach cases. Also run `python -m eval.run --keyless` and confirm the coach table shows the plan and tools per case.

## 6. Frontend

- [x] 6.1 Extract the run reducer from `useAsk` into `components/agent/runState.ts` (`applyEvent`) and use it from `useAsk`. In `lib/api.ts`, add the coach view types, wire `coachAskStream` to the shared handlers (`onPlan`, `onStep`, `onView`, `onTeamUpdated`), and remove `onCandidates`/`onEdits`/`CoachEdit`. Verify with `tsc --noEmit` and that the Ask page still works in the browser.
- [x] 6.2 Move the candidate cards (Add/Replace/Revert) and `ProposalCard` (Apply/Revert/Dismiss) into `components/agent/views/Candidates.tsx` and `SetEdit.tsx`, driven by the `candidates`/`set_edit` views. Add a `member_added` strip with Undo (`clearSlot`) and the `duel` view. Verify with `tsc --noEmit` and `npm run lint`.
- [x] 6.3 Rewire `TeamCoach.tsx`:
  - turns become runs, each with compact `PlanSteps` (the context step labelled "Read your team"), `Answer` and the coach views
  - remove `EDIT`, `THEIRS`, `findMember`, `fromEdit` and the direct `suggestBuild` call
  - keep the starter prompts

  Verify in the browser on a team: a plain question shows the steps and a cited answer; "give X a faster set" shows the proposal, and Apply then Revert restores the set; "add X" adds, and Undo clears it; a draft shows cards whose Add works.
- [x] 6.4 Run `npm run lint` and `npm run build` in `frontend/` and verify both succeed.

## 7. Integration and docs

- [x] 7.1 End-to-end against the Compose stack on Groq, keeping the token budget small: a plain question, a set change, an add + Undo, a draft, and a dex lookup from the team page. Also check keyless. Verify by recording the outcomes and LLM call counts in this file's notes, and removing the test questions from `question_log` and any temporary slots.
- [x] 7.2 Update `CLAUDE.md`:
  - the coach section: team scope, always-attached context, team tools, the add gate, set-edit proposals
  - remove the `rag/router.py` note
  - update the Drafting/add-action paragraph

  Verify by reading it against `design.md`.

## Notes

**6.3 / 7.1 end-to-end, live stack on Groq, 2026-10-05.** Run in the browser on a temporary
team (Garchomp, Charizard, Gyarados).
- "add Dragonite": fast path, 0 LLM calls. Saved to slot 4, page roster refreshed; Undo cleared it.
- "Can Garchomp learn Swords Dance?": fast path, 0 calls, learn-check view.
- "What's my team's biggest weakness?": fast path, 1 call (answer). Cites the page report as [1].
- "Give Garchomp a faster set": fast path, 1 call (build coach). Was → now card. Apply saved
  Jolly / Life Orb / 252 Atk 252 Spe; Revert restored the exact empty set.
- "Draft the rest of my team — non-legendary sweepers": LLM plan, 2 calls. Six candidate cards;
  Add put Dragapult in slot 4, and Revert cleared it.
- "Should I add Dragonite?": card mode, 1 call (answer). Only an Add card; the team was unchanged.
- Keyless paths are covered by tests and `eval.run --keyless`, where coach keyword-plan accuracy
  is 100%.
- **Bug found and fixed:** questions were logged *after* `done`, and the browser stops reading at
  `done`, so the log write was cancelled (lost history and noisy tracebacks). This was already
  true of Ask before this change. Both endpoints now log before sending `done`, with a regression
  test in `test_coach_api.py`.
- **Answer quality, not a pipeline issue:** the "should I add Dragonite" answer was grounded but
  shallow ("you have empty slots").
- The temporary team was deleted and the test questions removed from `question_log`.
