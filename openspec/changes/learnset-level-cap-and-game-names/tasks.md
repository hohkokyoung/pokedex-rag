# Tasks

## 1. Level cap and evolution moves

- [x] 1.1 Add `max_level` to the learnset lookup and the `learnset` tool arguments (cap implies level-up; level 0 counts at the evolution level) and verify `test_level_cap_on_a_pair` and `test_level_cap_on_learners` pass
- [x] 1.2 Describe evolution moves as "on evolving (Lv N)" and verify `test_evolution_move_says_when` passes
- [x] 1.3 Render a capped "no" with when the move is learned (renderer, `LearnCheckView`/`LearnersView` `max_level`) and verify `test_learnset_level_cap_renders_no` passes
- [x] 1.4 Parse level caps in the keyword planner ("below/before/under N" → N − 1, "by/until/up to N", "N or below" → N) and verify `test_level_cap_cue` passes
- [x] 1.5 Show the cap on the frontend learn-check strip and verify `tsc --noEmit` and eslint pass
- [x] 1.6 Add eval case `v5b` ("Does Garchomp learn Crunch below lvl 30?") and verify `tests/test_eval.py` passes
- [x] 1.7 Check the planning prompt stays under `PROMPT_BUDGET` in every scope and verify `tests/test_llm_planner.py` passes
- [x] 1.8 Update `docs/architecture/retrieval.md`, `ask-agent-planners.md` and `ask-agent.md` for the cap and evolution moves

## 2. Game names

- [x] 2.1 Resolve bare game names to the original and "new"/"remake" to the remake, skipping leading filler, and verify the new `test_resolve_game_spellings` and `test_find_game_in_text` cases pass
- [x] 2.2 Report a clearly named but unmatched game as `unhandled` in the keyword plan and verify `test_unresolved_game_is_flagged_not_dropped` passes
- [x] 2.3 Update `docs/architecture/retrieval.md` and `ask-agent-planners.md` for game names and unmatched games

## 3. Integration

- [x] 3.1 Run `make test` and `make lint` and verify both pass
- [x] 3.2 Replay trace #868's plan (`game: "diamond"`, `max_level: 49`) through the learnset tool and verify the answer names Diamond / Pearl
- [ ] 3.3 Add a level-cap example question to `docs/product/ask.md` and verify it renders in the Ask page's examples table
- [ ] 3.4 Run `make eval` (spends Groq tokens — ask first) and verify `v5b` plans a learnset step with a cap of 29
