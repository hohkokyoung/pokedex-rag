# Tasks

## 1. Turn engine: website → shared maths

- [x] 1.1 Move the turn engine from `page.tsx` into `frontend/lib/calcTurn.ts` (pure); the page renders from it. Verify: tsc, eslint, and the calculator in the browser (singles default, doubles with Earthquake) unchanged.
- [x] 1.2 Extend `scripts/damage-fixtures.ts` to write `turn_cases.json` (hand-picked + seeded). Verify: `make damage-fixtures`, cases cover every targeting kind, sash, priority, ties.
- [x] 1.3 Port to `services/calc_turn.py`; golden test. Verify: pytest.
- [x] 1.4 `POST /api/calc/turn` (+ `resolve_slots`, move target/priority); API tests (order, spread, sash, 422). Verify: pytest and a live request.

## 2. App: calculator

- [x] 2.1 OpenAPI slice + `make mobile-api`. Verify: drift test, analyze.
- [x] 2.2 Calc state + turn fetch; setup UI (mode, level, slots with presets/set/move/aim, field). Verify widget tests: default request (Garchomp vs Corviknight), Offensive preset on a special attacker, EV cap.
- [x] 2.3 This-turn log, HP bars, Math. Verify widget tests over recorded turns (singles, doubles spread, sash), can't-reach.

## 3. Check and docs

- [x] 3.1 Simulator against the real server. `make test`, `make lint`, `make mobile-test`.
- [x] 3.2 Docs. Verify: `make test`.
