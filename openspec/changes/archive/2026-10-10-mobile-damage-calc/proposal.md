# Proposal

## Why

Phase 6b of the mobile app: the damage calculator. Only part of it has a server
version today:
- `services/damage_calc.py` (the per-hit formula) is the Python twin of
  `frontend/lib/damageCalc.ts`.
- The **turn** lives only inside the website's `page.tsx`: who moves first, doubles
  targeting (spread, random, ally, a fainted target's partner), Helping Hand, HP
  carried from hit to hit as a worst/best range, Focus Sash, KO calls and who gets to
  move. `calc_state.py` even says "the turn simulation, which isn't ported".

The app must show the same turn, and a third copy in Dart would drift.

## What Changes

- **Website:** the turn engine moves out of `page.tsx` into a pure
  `frontend/lib/calcTurn.ts`. The page keeps using it (instant updates) with no change
  in behaviour.
- **Backend:**
  - `services/calc_turn.py` ports it, pinned to the TS by reference cases that
    `make damage-fixtures` now also writes (`turn_cases.json`): "one formula, two
    languages" grows to cover the turn.
  - `POST /api/calc/turn` takes the calculator state (level, singles/doubles, field,
    up to four slots with species/form, set, HP, move and aim) and returns the turn:
    - each slot's Speed and turn order;
    - each step's hits (range, KO call, Focus Sash, friendly fire, formula terms);
    - the HP each slot ends on.
  - Types, stats and moves are re-read from the DB.
- **App:** the damage calculator joins Tools (**Damage calc**):
  - singles or doubles, level 50 or 100;
  - your side and the opponent's, each slot with a Pokémon, preset (Offensive /
    Bulky / Custom), nature, EVs, IVs, item, ability, current HP, move and, in
    doubles, its target;
  - the field (weather, terrain, Reflect, Light Screen, crit, burn, Friend Guard);
  - **This turn**: the battle log in move order with ranges, HP bars, KO calls and
    who faints, from the server;
  - the formula for the focused hit.
- `docs/architecture/damage-calc.md`: the turn becomes part of the shared maths.

## Capabilities

### New Capabilities
- `calc-coach/turn`: the turn simulation and its parity with the website.
- `mobile/damage-calc`: the app's calculator.

### Modified Capabilities
(none)

## Out of scope

- The calc coach in the app (next phase).
- Using the server turn in the calc coach's evidence. The client's `hits` stay as
  they are; switching them over is a follow-up.
- Abilities and items beyond what the formula already models.

## Impact

- Website: `frontend/lib/calcTurn.ts` (new), `app/page.tsx`,
  `scripts/damage-fixtures.ts`.
- Backend:
  - `services/calc_turn.py` (new), `services/calc_state.py` (move target and
    priority, a resolver without a question);
  - `schemas/calc.py` (turn request/response), `api/calc.py`;
  - tests and fixtures.
- App: `lib/features/tools/calc*.dart`, OpenAPI slice (+ calc turn, legal moves,
  abilities and items already in).
- Docs: `docs/architecture/damage-calc.md`, `docs/product/mobile.md`,
  `docs/components/damage-calc.yaml`, `docs/components/mobile.yaml`.
