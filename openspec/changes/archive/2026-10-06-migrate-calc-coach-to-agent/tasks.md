# Tasks

## 1. Shared damage maths

- [x] 1.1 Extract `calcHit`, `natMul`, `statFull`, `NAT`, `TYPE_BOOST`, `RESIST_BERRY` and their types into `frontend/lib/damageCalc.ts` (relative imports only). Re-export them from `components/calc/fields.tsx` and use them in `app/page.tsx`. Verify with `tsc --noEmit` and in the browser: the calculator shows the same damage for Garchomp vs Salamence before and after.
- [x] 1.2 Add `frontend/scripts/ts-resolve.mjs` and `frontend/scripts/damage-fixtures.ts` (hand-picked and seeded random cases, ~250), plus a `make damage-fixtures` target that writes `backend/tests/fixtures/damage_cases.json`. Verify that running it twice produces identical JSON.
- [x] 1.3 Port the maths to `backend/app/services/damage_calc.py` (`nat_mul`, `stat_full`, `calc_hit`, the static type chart, `apply_changes`). Verify that `tests/test_damage_calc.py` matches every reference case (percentages ±0.01; `ko`, `te`, `stab`, `A`, `D`, `base` exact) and that the static chart equals the DB chart.
- [x] 1.4 Implement `survive()` (EV grid, then nature fallback, "can't survive" with the best spread). Verify with pytest:
  - a survivable case returns the minimal spread, and that spread really survives
  - an unsurvivable case returns `survives=False`
  - the search runs in under 100 ms

## 2. Calc scope: context and tools

- [x] 2.1 Add the calc state request schema (`schemas/calc.py`). Add server-side resolution of types, base stats and move data (forms included) into calc sides. Verify with a DB pytest: a state with Garchomp (and a Mega form) resolves stats and the move's type and power from the DB, ignoring client stats.
- [x] 2.2 Implement the built-in `calc_context` tool (scope `calc`, `plannable=False`): slot chunks with Lv-N stats, the field, the calculator's hits, the proposal and the last 3 thread turns, and the calc note. Verify with pytest: chunk order and unique ids, and no proposal chunk when none is sent.
- [x] 2.3 Implement `damage_calc` (`damage` view, closed-form) with slot name resolution, a default move, legal-move checking and `changes` parsing. Verify with pytest:
  - with no changes, it equals `calc_hit` on the same state
  - a Choice Band what-if raises the range
  - an unknown key, or an illegal move, is an error step
- [x] 2.4 Implement `survive_threshold` (`survive` view, closed-form, with `apply` fields). Verify with pytest on a known matchup: the needed spread and range, and the `apply` fields match the spread.
- [x] 2.5 Implement `propose_build` (`build_proposal` view, closed-form): `suggest_build(attempts=1, current, history, usage)`. Verify with a stubbed-LLM pytest: the current proposal and thread are passed when the slot matches, and invented options are dropped.
- [x] 2.6 Add the calc scope to the Ask dex tools (the same set as team). Add registry tests. Verify with `make test`:
  - calc tools are read-only (session spy)
  - `calc_context` is not plannable
  - the calc planning prompt is ≤ 10,500 characters

## 3. Planners, runner, renderers

- [x] 3.1 Calc scope in the keyword planner (the Decision 7 order, with `with <item/nature/EVs>` parsed into `changes`). Verify with pytest on a fixed state:
  - "Can Garchomp OHKO Salamence?" → `damage_calc`, confident
  - "…with Choice Band" → `changes` set
  - "How much Def does Salamence need to survive Earthquake?" → `survive_threshold`, confident
  - "best build" / "make it bulkier" → `propose_build`, confident
  - "Who learns Earthquake?" → `learnset`
  - "Who wins this?" → no extra steps, confident
- [x] 3.2 Calc scope in the LLM planner: the calc roster line, rules, few-shots and `plan_schema("calc")`. Verify with a stubbed-LLM pytest: the roster appears in the prompt, the schema has the calc tools but not `calc_context`, and an empty plan is accepted.
- [x] 3.3 Generalise the runner's context step to `calc` (no caching for calc). Add renderers for `damage`, `survive` and `build_proposal` (KO wording per Decision 8), and the keyless build message. Verify with stubbed-LLM runner pytests:
  - OHKO: 0 LLM calls, answer from code
  - survive: 0 calls
  - best build: 1 call, `why` is the answer
  - a plain question: 1 call, calc context is source [1]
  - keyless build: says it needs a key
  - a mixed question: ≤ 2 calls

## 4. Calc coach API

- [x] 4.1 Add `POST /api/calc/ask` (SSE): build the `AgentContext` from the state, call `run_question(scope="calc")`, and log the question (`calc-llm`/`calc-keyword`) before `done`. Verify with an httpx streaming test: the event order, the views, and that no saved team changes.
- [x] 4.2 Run `make test` and `make lint` and verify both pass.

## 5. Eval

- [x] 5.1 Add `CalcCase` and calc cases (OHKO, item what-if, survive, best build, make-it-faster, dex lookup, plain), plus `evaluate_calc` (keyless, `--plans-only`, full) and the report section. Verify with `tests/test_eval.py` that calc keyword-plan accuracy is 100% and fast-path agreement is 100%, and that `python -m eval.run --keyless` shows the calc table.

## 6. Frontend calc coach

- [x] 6.1 In `lib/api.ts`, add `calcAskStream` and the `DamageView`/`SurviveView`/`BuildProposalView` types. Verify with `tsc --noEmit`.
- [x] 6.2 Rewire the `page.tsx` coach box. Verify with `npm run lint` and `tsc --noEmit`. The changes:
  - `sendCoach` builds the calc state and streams
  - compact `PlanSteps` per turn, with the thread kept
  - a `build_proposal` view feeds the existing card (Apply/Revert/moveset chips unchanged)
  - inline `damage`/`survive` cards with Apply/Revert into the calc
  - remove the direct `suggestBuild` calls
- [x] 6.3 Browser check on the home calculator, token-free paths first:
  - "Can Garchomp OHKO Salamence?" shows the damage card, 0 LLM calls, and its numbers match the calculator's row
  - an item what-if, and Apply → the calc updates, Revert restores it
  - survive, and Apply → the EVs update

  Then, with the user's OK, the LLM paths: "Best build" → the card, Apply/Revert; "Make it bulkier" → revised. Record the results in this file's notes.
- [x] 6.4 Run `npm run lint` and `npm run build` in `frontend/` and verify both succeed.

## 7. Docs

- [x] 7.1 Update `CLAUDE.md`. Verify by reading it against `design.md`. It should cover:
  - the calc scope (calc context, tools, damage maths shared with the browser via reference cases)
  - when and how to regenerate the fixtures (`make damage-fixtures`)
  - `battle.py` stays separate

## Notes — 6.3 browser check (2026-10-06)

- Token-free (home calc, Garchomp vs Corviknight): "Can Garchomp OHKO Corviknight?" → damage card,
  0 LLM calls, 18.8–22.2% = the calc row's 19–22%. "…with Choice Band?" → what-if 28–33%; Apply
  moved the row to 28–33%, Revert restored it. Survive: at full HP "already survives" (no Apply);
  at 40% HP → Impish, Apply → takes 32–38% (survives), Revert restored Adamant.
- Fixed during the check: survive offered a 0/0 "spread" that stripped EVs when the set already
  survived (now `already`, no Apply); KO wording on survive ranges; "can't survive with any legal
  spread" now says when only the free EVs rule it out; "Bulky set"/"Fast sweeper" and tweaks like
  "No Choice item" (with a proposal) now plan `propose_build`.
- LLM (Groq): "Best build" → build card, 1 LLM call (Choice Scarf Jolly); Apply → calc shows
  Earthquake + Choice Scarf + Jolly, Revert restores Outrage/Adamant. "Make it bulkier" → revised
  the same build (252 HP, Rocky Helmet), 1 call. Quirk: kept Jolly with 0 Spe EVs (model choice).
- The plan badge "Keyword match · no LLM" contradicted "1 LLM call" on build turns → now
  "Planned by keywords" (the call count stays alongside).
