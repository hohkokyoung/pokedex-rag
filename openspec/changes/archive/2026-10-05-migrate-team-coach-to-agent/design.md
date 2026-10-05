# Design

## Context

### What exists
Phase 1 (archived `2026-10-05-add-agent-retrieval-planner`) built the agent core in
`app/agent/`: tool registry with scopes, keyword planner (names first, fast path), LLM
planner (strict per-tool `anyOf` schema, no SDK retries), concurrent executor, code
renderers, caches, a runner that emits `plan`/`step`/`view`/`sources`/`delta`/`done`
events, and the frontend `useAsk`, `PlanSteps` and `ViewBlock`.

### How the coach works today
`POST /api/teams/{id}/ask`, in `api/teams.py::coach_ask`:
1. `coach.is_add_command(question)` (verbs minus "should I…") plus
   `coach.resolve_species` (longest Pokémon name in the text) → `_handle_add` saves the
   slot and sends `team_updated`.
2. `team_analysis.analyze(team, opponent)` runs.
3. `is_add_command or recommend.is_draft_request` → `draft_intent.extract_draft_prefs`
   (an LLM call) → `recommend.recommend_additions` → `candidates` event plus candidate
   chunks.
4. `coach.build_coach_chunks`: page report, member chunks, analysis, suggestions, opponent
   members, vs-opponent, candidates, and dex retrieval via `rag/router.route_and_retrieve`.
5. `answer.stream_answer(question, chunks, COACH_NOTE)`, then
   `coach_edits.extract_edits` (an LLM call) → `edits` event.
6. With no key: an extractive draft list, the page report, or an analysis brief.

### How the frontend works today
`TeamCoach.tsx` sends set changes to `POST /api/builder/builds/suggest` directly. The
`EDIT` regex plus `findMember` decide this, and the coach endpoint is never called. The
proposal card (`ProposalCard`), candidate cards (`co-cand`, with Add/Replace/Revert) and
Undo-by-`clearSlot` already exist on the client.

### Constraints
- Groq free tier: a plan call is about 2.4k input tokens. The SDK retries are already off
  for planning.
- `build_suggest.suggest_build` retries itself once with a larger budget, so it can
  make 2 calls today.

Motivation: see `proposal.md`. Requirements: see `specs/team-coach/*` and the modified
`specs/assistant/*`.

## Goals / Non-Goals

**Goals:**
- One planner path for every assistant surface. The coach differs only by scope and
  context.
- Mutations happen only through gated tools, with a deterministic imperative check that
  the LLM can't bypass.
- Reuse every existing visual and service: the recommender, `build_suggest`, the duel
  engine and the coach chunk builders.
- Fewer LLM calls per coach question than today.

**Non-Goals:**
- Changing `team_analysis`, `team_strategy`, `team_summary` or the recommender's ranking.
- The calc coach (phase 3).
- Conversation memory across coach questions.

## Decisions

### 1. Team context travels in `AgentContext`
- **`AgentContext` gains three fields:**
  - `team: TeamOut | None`
  - `opponent: TeamOut | None`
  - `report: str | None`
- **Per-request extras go in `extra`:**
  - `analysis`: computed once per request
  - `usage`: the request's `Usage`, so tools that call an LLM can count it
- **Who fills it:** `coach_ask` loads the team, opponent and analysis, then calls
  `runner.run_question(question, scope="team", ctx=ctx)`.
- **Why not have tools re-load the team:** every tool would repeat the same queries and
  analysis. `team_analysis.analyze` runs the duel engine, so it isn't cheap.

### 2. Always-attached team context step
- **A built-in step, not a planned one.** A `team_context` tool (scope `team`,
  `plannable=False`, so it never appears in the planner schema) is prepended by the
  runner to every team-scope plan, from either planner, as step `ctx`.
- **What it returns, built with the existing `coach.py` builders:**
  - the report chunk first, when one is sent
  - member chunks
  - the analysis
  - the suggestions
  - when an opponent is selected: opponent member chunks and the vs-opponent chunk
- **Never closed-form.** It doesn't count when deciding whether the rest of the plan is
  closed-form. A plan of only the context step is answered by the LLM, or by the
  keyless fallback.
- **The coach note.** `coach.COACH_NOTE`, trimmed of the drafting/"Add to team"
  instructions that now live in tool notes, becomes this step's note.
- **Why not let the planner pick a `team_overview` tool:** you chose always-attached. It
  also makes plain questions cheap (Decision 5) and the planner can never forget the
  team.

### 3. Team tools (`app/agent/team_tools.py`)

| Tool | Args (filled by the planner) | Wraps | View | Closed-form |
|---|---|---|---|---|
| `team_context` (built-in) | — | `coach._member_chunk`, `_analysis_chunk`, `_suggestions_chunk`, `_vs_chunk`, report chunk | — | — |
| `recommend_additions` | `role?: sweeper\|wall\|wallbreaker\|support`, `legendary?`, `mythical?`, `types: [str]`, `limit?` | `recommend.recommend_additions(team, analysis, question="", prefs=DraftPrefs(...))` + `recommend.to_chunks` | `candidates` | no — the answer explains the picks |
| `propose_set_edit` | `member: str`, `side: ours\|theirs`, `request: str` | `build_suggest.suggest_build(..., current=…, request=…, attempts=1, usage=ctx usage)` | `set_edit` | yes — the build's `why` is the answer |
| `add_member` | `pokemon: str` | `teams_service.set_slot` into the next empty slot + `team_summary.schedule` | `member_added` | yes |
| `duel` | `ours: str`, `theirs: str` | `team_analysis.duel_detail` | `duel` | no |

- **Most Ask tools join the team scope.** Their `@tool` registrations get
  `scopes=("ask", "team")`. The exceptions are `semantic_search`, `similar_to`,
  `user_profile` and `encounters`. They aren't coaching tools (`recommend_additions`
  covers alternatives), and leaving them out keeps the team planning prompt within its
  10,500-character budget (it measured 11,629 with them, 10,499 without). Confirmed with
  the user during apply.
- **Names resolve within the roster first.** `propose_set_edit`, `duel` and `add_member`
  close-match against the team (or opponent) roster before the whole dex. A member
  that's on neither team is an error step whose summary says so, which satisfies the
  "unknown member" scenario.
- **`propose_set_edit` builds the current set** from the member (moves, ability, nature,
  item, EVs mapped to `hp/atk/def/spa/spd/spe`), exactly as `TeamCoach.tsx` did. The
  `set_edit` view carries `before`, `after` and only the changed `fields`, so Apply sends
  exactly what the card shows.
- **`add_member` refuses rather than half-acting.** If the team is full or already has
  that Pokémon, it returns `status="done"` with a summary saying so, `data.added = False`
  and no change.

### 4. The add gate: a deterministic imperative check
- **Two-part rule.** An `add_member` step only executes when the planner chose it **and**
  the runner's `is_imperative_add(question)` agrees. The check is the old
  `coach.is_add_command` logic (verb list minus deliberation phrases), moved into
  `keyword_planner.py`.
- **When the check fails:** the runner runs the step in *card mode*. Nothing is saved; the
  step returns a one-card `candidates` view for that Pokémon (role and reason from the
  recommender's classifier), so the user can click Add.
- **Why:** you chose add-now-with-Undo for explicit commands. A model mistake on "should
  I add Garchomp?" must not write to the database, and this rule makes the "nothing
  changes without an explicit command or a click" invariant hold in code, not just in a
  prompt.
- **After a real add:** the runner sends `team_updated` (the new `TeamOut`) right after
  the step's `view`, so the page refreshes as it does today.

### 5. Team-scope planning and the fast path
- **Keyword planner, team scope.** `plan_keywords(..., scope="team", ctx)`. The roster
  (both teams) is matched first. The order:
  1. **Imperative add** + a resolvable Pokémon → `add_member`. Confident.
  2. **Set-change cue** (the old frontend `EDIT` regex, ported) + a roster member →
     `propose_set_edit(member, side, request=question)`. The side comes from the old
     `THEIRS` regex. Confident.
  3. **Draft cue** (`recommend._DRAFT_KEYWORDS`) → `recommend_additions` with
     `parse_role` / `nlfilters` arguments. Not confident; the LLM reads sentiment better.
  4. **"X vs Y"** with members on both sides → `duel`. Not confident.
  5. **Names not on the roster, or dex cues** → the Ask rules (learnset, move info,
     type chart, coverage…), using the same rule table as Ask.
  6. **Nothing else → no extra steps.** Confident: the **plain team question** fast path.
- **Grounding the `request` arg.** Passing the question as `request` to the build coach
  is the one place a tool receives the user's words. It's an argument the planner (or
  keyword planner) chooses, the build coach needs the user's intent to revise a set, and
  the result is still validated against legal data.
- **LLM planner, team scope.**
  - `plan_schema("team")`: the Ask tools plus the team tools, minus `team_context`.
  - The system prompt adds a roster line ("Your team: Garchomp, Rotom-Wash…; Opponent:
    …"), about 60 tokens, and these rules:
    - the team context is already attached; plan only extra lookups
    - **an empty plan is valid**
    - use `add_member` only for an explicit command
    - set changes go to `propose_set_edit` with the member's exact name
    - drafting goes to `recommend_additions`
  - Two team few-shots replace two Ask ones, keeping the prompt size about the same.
- **Empty plans are valid in team scope** (`steps: []`). The Ask scope still requires at
  least one valid step before falling back.

### 6. Answer step for the coach
- **Closed-form:** if every non-context step is closed-form, the code renderer answers.
  - `set_edit`: the build's `why` plus "Proposed for Garchomp — press Apply to save."
  - `member_added`: "Added **Garchomp** to slot 4. Configure its set from the slot, or
    ask me for one."
- **Otherwise the LLM answers** with `answer.stream_answer` over all chunks and notes.
  The context step comes first, so the report stays the authoritative first source, as
  `test_page_report_is_the_coach_first_source` requires today.
- **Keyless or a failed answer call:**
  - with candidates → `coach.compose_extractive_draft`
  - otherwise, the page report if one was sent
  - otherwise → `coach.compose_extractive_coach(analysis)`
  - plus any closed-form renders
  - This keeps today's no-key behaviour.

### 7. Build coach inside the agent
- **New parameters on `build_suggest.suggest_build`:** `attempts: int = 2` and
  `usage: Usage | None`. The tool passes `attempts=1` (max budget 2400) and the request's
  `usage`, so the call is counted and bounded.
- **Unchanged default:** the calc endpoint keeps `attempts=2` until phase 3.
- **Errors:** a `SuggestError` becomes an error step with its message. Without a key, the
  message says set suggestions need an LLM key.

### 8. Views and SSE

New view models in `views.py`:
- `CandidatesView`: a list of `Candidate`, with `team_full` and `members` (slot, name)
  for the Replace picker.
- `SetEditView`: `side`, `team_id`, `slot`, `name`, `sprite_url`, `before{moves, ability,
  nature, item, evs}`, `after{…, why}`, `fields{…only changed}`.
- `MemberAddedView`: `team_id`, `slot`, `card: PokemonCard`, `added: bool`, `message`.
- `DuelView`: the `DuelOut` payload, already shaped for the team page's duel detail.

SSE order for the coach:
`plan` (the context step first) → `step`* → `view`* (`team_updated` right after a
`member_added` view that added) → `sources` → `delta`* → `done{usage}`.
The old `candidates` and `edits` events are gone.

### 9. Frontend
- **Shared state logic.** The run reducer is extracted from `useAsk` into
  `components/agent/runState.ts` (pure `applyEvent(run, event)`). `useAsk` and the coach
  both use it, and `coachAskStream` gets the same handlers.
- **`TeamCoach` turns become `AskRun`s,** each rendered with:
  - `PlanSteps` (compact; the context step labelled "Read your team")
  - `Answer`
  - a coach view block:
    - `candidates` → the existing `co-cand` cards (moved into
      `components/agent/views/Candidates.tsx`, keeping Add/Replace/Revert)
    - `set_edit` → the existing `ProposalCard` (moved into
      `components/agent/views/SetEdit.tsx`, keeping Apply/Revert/Dismiss)
    - `member_added` → a strip with Undo (`clearSlot`)
    - `duel` → the existing duel summary visual if one exists on the team page, else a
      compact turn list
    - other kinds → `ViewBlock`
- **Removed:** `EDIT`, `THEIRS`, `findMember`, `fromEdit` and the direct `suggestBuild`
  call.

### Existing modules: reused, slimmed, removed
- **Reused as-is:**
  - `recommend.recommend_additions`, `to_chunks`, `parse_role`
  - `nlfilters`
  - `build_suggest.suggest_build` / `validate` (two new parameters)
  - `team_analysis.analyze` / `duel_detail`
  - `teams_service.*`
  - `team_summary.schedule`
  - the Ask tools
  - the runner, executor, planners and renderers
- **Slimmed:** `rag/coach.py` keeps the chunk builders, `COACH_NOTE` (trimmed) and the
  extractive composers. `build_coach_chunks`, `is_add_command`, `resolve_species` and
  the `_ADD_VERBS`/`_DELIBERATE` lists move into or are deleted from the keyword planner.
- **Removed:**
  - `rag/router.py`, `rag/draft_intent.py`, `rag/coach_edits.py`
  - `recommend.is_draft_request`; `_DRAFT_KEYWORDS` moves to the keyword planner.
    `allow_legendary` stays, because it is `recommend_additions`' own fallback when no
    legendary preference is given.
  - `api/teams.py::_handle_add`
  - tests: `tests/test_router.py`, `tests/test_draft_intent.py`, the coach-intent tests,
    and the `coach_edits` test in `test_team_coach.py`. Their behaviours are covered by
    the new team-scope tests.

### Per-question LLM budget (coach)

| Question | Plan | Build coach | Answer | Total |
|---|---|---|---|---|
| Plain team question (fast path) | 0 | 0 | 1 | 1 |
| "Give Garchomp a faster set" (fast path) | 0 | 1 | 0 (why = answer) | 1 |
| "add Garchomp" (fast path) | 0 | 0 | 0 | 0 |
| Draft (LLM plan for sentiment) | 1 | 0 | 1 | 2 |
| Mixed (draft + set change) | 1 | 1 | 1 | 3 |
| Today: draft | — | — | — | 3 (prefs + answer + edit extraction) |

- **Prompt budget:** the planning prompt test is extended to the team scope (≤ 10,500
  characters, because of the roster line and the extra tools).

### Eval
- `CoachCase` gains `expect_tools` and `fast_path`.
- New cases: an imperative add on a team with space; a deliberation (no add);
  "give X a faster set"; a draft with sentiment; a dex lookup from the team page; a duel.
- `evaluate_coach` runs through `run_question(scope="team")` against the existing
  temporary teams. The keyless run checks keyword plans; `--plans-only` counts calls.

## Risks / Trade-offs

- **[The LLM planner picks `add_member` for a deliberation]** → The deterministic
  imperative gate (Decision 4) blocks the write, and a test covers "should I add X?"
  with a stubbed planner that wrongly plans an add.
- **[`request` is the one place user words reach a tool]** → It goes only to the build
  coach, whose output is validated against legal data, and it's capped at 300
  characters (`build_suggest` already does this).
- **[The team context adds tokens to every coach answer]** → It is the same evidence the
  coach uses today (`build_coach_chunks`). The answer chunk cap is raised to 16 for team
  scope, with the context step exempt from the per-step quota, since the report and
  analysis must survive.
- **[Removing the frontend shortcut adds a round trip for set changes]** → The fast path
  makes it 0 plan calls plus the same build call. Latency is about the same; the plan
  step simply shows.
- **[Opponent edits]** → `propose_set_edit` supports `side="theirs"`. Apply already uses
  the opponent team id on the client, as today.

## Migration Plan

- **No migrations.** Backend and frontend ship together, since the coach stream format
  changes.
- **Rollback:** a git revert. `ASK_AGENT_ENABLED=false` also turns off LLM planning for
  the coach, leaving keyword plans.
- **After this change:** `rag/router.py` is gone, and phase 3 (the calc coach) registers
  a `calc` scope the same way.

## Open Questions

- **Resolved (task 2.5):** the team page has no duel component. `getTeamDuel` / `TeamDuel`
  exist in `lib/api.ts` but nothing renders them, so the `duel` view gets the compact turn
  list (outcome, who moves first, the movesets, then the log).
