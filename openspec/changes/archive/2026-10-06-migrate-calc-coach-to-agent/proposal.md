# Proposal

## Why

The home damage calculator has a coach. Unlike Ask and the team coach, which now run on the
planning agent (`assistant/retrieval-planning`, `team-coach/*`), it is a single fixed call:
`page.tsx` calls `POST /api/builder/builds/suggest` directly. It can only suggest or revise
one build. It never sees the calculator's numbers, the opposing Pokémon or the field, so it
can't answer the questions the calculator exists for: "can my Garchomp OHKO their
Salamence?", "what if I hold Life Orb?", "how much Defense do I need to survive Close
Combat?".

The damage maths also lives only in the browser (`calcHit` in `page.tsx`). The server has a
different, simpler engine (`battle.py`: average roll, no weather/terrain/screens/crits), so
nothing server-side can reproduce what the calculator shows.

This change moves the calc coach onto the agent as the third scope. It gives the backend a
faithful port of the calculator's maths, tied to the browser version by shared test cases.

## What Changes

- **Damage maths shared by both sides.**
  - `calcHit` and its pure helpers (stat formula, nature multipliers, type
    effectiveness, item/ability/field modifiers) move from `page.tsx` into
    `frontend/lib/damageCalc.ts`.
  - The backend gets `app/services/damage_calc.py`, a line-for-line port.
  - A Node script runs the TypeScript version over a set of reference cases and writes
    the expected results; pytest checks the port against them, so the two can't drift.
  - `battle.py` (team duels) is unchanged.
- **A `calc` scope for the agent.**
  - A new endpoint, `POST /api/calc/ask` (SSE), takes the question plus the calculator's
    state: the up to 4 slots with Pokémon, sets, HP and chosen moves, the field, singles
    or doubles, the level, and the current build proposal with its chat thread.
  - A built-in `calc_context` step turns that state into citable evidence (each slot's
    set and stats, and the hits the calculator currently shows).
- **Calc tools.** All calc tools are read-only and never touch saved teams.
  - `damage_calc(attacker, defender, move?, changes?)`: one hit (or every move) as a
    min–max % with hits-to-KO, with optional what-ifs (item, ability, nature, EVs, field).
  - `survive_threshold(defender, attacker, move, stat?)`: the smallest HP/defensive
    investment (EVs, then nature) that survives the hit, or "can't survive it".
  - `propose_build(slot, request)`: wraps `build_suggest` (`attempts=1`) with the current
    proposal and thread, so "make it bulkier" revises it.
  - The Ask dex tools (learnset, move info, type charts, coverage, rankings…).
- **Answers:** damage and threshold answers are rendered by code, with 0 answer calls.
  Build proposals answer with the build coach's explanation, as today.
- **Keyword planner:** learns calc phrasings (OHKO / 2HKO / survive / "best build" / "make
  it …") for the fast path and the no-key path.
- **New view kinds:** `damage` (hit rows with min–max %, KO calls and what-if diffs),
  `survive` (the needed spread vs. the current one), and `build_proposal` (the existing
  calc coach card, with Apply/Revert into the calculator only).
- **Calc coach UI** (`page.tsx`):
  - the coach box streams from the new endpoint and shows compact plan steps
  - damage and survive views render inline
  - the build card, Apply/Revert, quick chips and the thread keep working
  - Apply can now also take a what-if or threshold result into the calculator
  - the direct `suggestBuild` calls are removed

## Out of scope

- **Unifying `battle.py`** (team analysis duels: average roll, Lv 50) with the
  calculator's maths. That would change team grades and verdicts and is a separate change.
- **Porting the calculator's turn simulation** (move order, Focus Sash carry-over,
  multi-hit turn log) to the backend. The coach reasons about single hits from current HP,
  which is what the damage rows show.
- **Saving calculator builds to teams** from the calc coach.
- **The standalone `/api/builder/builds/suggest` endpoint stays** for compatibility. The
  calculator just stops calling it directly.

## Capabilities

### New Capabilities

- `calc-coach/coach-planning`: how a calculator question is answered. Covers the `calc`
  scope, the always-attached calc context, calc tools and their arguments, the fast path
  for damage/threshold/build phrasings, the keyword fallback, the per-question LLM budget,
  and showing plan steps in the coach box.
- `calc-coach/damage-maths`: what the backend's damage maths must guarantee. It matches
  the calculator's own numbers for the same inputs, supports what-if changes, and computes
  survival thresholds with a clear "can't survive" outcome.
- `calc-coach/coach-actions`: what the calc coach may change. Build proposals and what-if
  or threshold results apply only to the calculator, only on a click, and Revert restores
  the previous calculator set.

### Modified Capabilities

- `assistant/result-views`: "Results are streamed as typed views" gains the `damage`,
  `survive` and `build_proposal` kinds.

## Impact

- **Frontend:**
  - new `lib/damageCalc.ts` (pure maths, imported by `page.tsx` and
    `components/calc/fields.tsx`)
  - `app/page.tsx`: the coach rewired to `calcAskStream` with plan steps and the new views
  - `lib/api.ts`: `calcAskStream` and the view types
  - new `scripts/damage-fixtures.ts`, run by Node to regenerate the reference cases
- **Backend:**
  - new `app/services/damage_calc.py`, `app/agent/calc_tools.py` and `app/api/calc.py`
  - calc scope in the keyword and LLM planners
  - the runner's context step generalised to team and calc
  - view models
- **Tests and eval:**
  - `tests/fixtures/damage_cases.json` (generated) with `tests/test_damage_calc.py`
  - calc tool, planner, runner and API tests
  - calc cases in `eval/` (keyless and `--plans-only`)
- **LLM usage per calc question:** at most 1 plan, 1 build coach and 1 answer call.
  - Damage, threshold and dex questions on the fast path cost 0.
  - "Best build" or "make it bulkier" costs 1, as today.
  - Mixed questions cost up to 2.
- **No new dependencies. No migrations.**
