# Design

## Context

- `damage_calc.calc_hit` is the shared per-hit formula, pinned by
  `damage_cases.json` and `make damage-fixtures`.
- The turn engine is in `frontend/app/page.tsx` (`hitsFor`, `order`, `steps`,
  `takenBy`), in closures over React state.
- `calc_state.resolve_state` already rebuilds slots from a request (DB types, stats
  and moves) for the coach, but without move target or priority.

## Goals / Non-Goals

**Goals:** the turn defined once (TS) with a pinned Python port the app reads;
calculator parity in the app; no LLM.

**Non-Goals:** the calc coach in the app; new mechanics.

## Decisions

1. **`frontend/lib/calcTurn.ts`** is a pure module:
   - `playTurn(state)` takes level, doubles, field toggles, and four slots (mon,
     set, move with target and priority, aim; null when empty).
   - It returns `{order, steps, hp}` exactly as the page computes them today.
   - `hitsFor` is exported for the move dropdown's preview.
   - `page.tsx` builds the state from its React state and renders from the result.
     Behaviour is unchanged; the page's existing logic is moved, not rewritten.
2. **Reference cases:**
   - `scripts/damage-fixtures.ts` also writes `turn_cases.json`, with ~60 states.
   - Hand-picked states cover: singles; doubles with spread / random / ally / aim at
     a fainted target; priority; speed ties; Focus Sash; burn and screens on the
     right sides; Friend Guard; an empty slot; a status move; an immune target;
     current HP below 100.
   - The rest are seeded-random states over the existing `MON` / `MOVE` tables, with
     targets and priorities added.
3. **`services/calc_turn.py`:**
   - It mirrors `playTurn` over `dc.calc_hit`.
   - Float ops follow the same order. HP ranges are floats; the comparisons
     (`<= 0`, `>= 100`) are the same.
   - Speed uses `dc.stat_full`. Sort is stable by `(-priority, -speed)`, matching
     JS `sort` on the filtered active order.
4. **`POST /api/calc/turn`:**
   - Request: `CalcTurnRequest`, the `CalcAskRequest` fields minus question, hits
     and proposal.
   - `calc_state` gains `resolve_slots(...)`, shared with the coach, and `CalcMove`
     gains `target` and `priority`. An unknown species or move is a 422 naming the
     slot.
   - Response:
     - `speeds` (per slot) and `order`;
     - `steps`: `[{slot, skipped, at_risk, hits: [{from, to, min_pct, max_pct, ko_rolls, te, stab, a, d, base, mod, ko: "yes"|"maybe"|null, sash, friendly_fire}]}]`;
     - `hp`: per slot `{lo, hi, sash}`.
5. **App calculator (`/tools/calc`):**
   - A Riverpod notifier holds the four sets, field, level, doubles and focus.
   - Each change rebuilds the request; a `FutureProvider.family` keyed by the
     request's JSON fetches the turn, and the last result stays shown while the next
     loads.
   - Slot editing reuses the team set editor's pieces (legal moves, abilities, held
     items, natures, EV/IV limits), restricted to damaging moves.
   - Presets copy the website's `offensiveSet` / `BULKY_SET`. That's UI defaulting,
     not a game rule.

## LLM budget

None. The turn is pure code; the app never calls the LLM here.

## Reused / removed

- Reused: `calc_hit`, `stat_full`, `nat_mul`, `calc_state`; the app's builder
  lookups.
- Removed: the turn closures in `page.tsx` (moved to the lib).

## Docs affected

- `docs/architecture/damage-calc.md` (the turn joins the shared maths; how to change it)
- `docs/product/mobile.md`, `docs/components/damage-calc.yaml`, `docs/components/mobile.yaml`

## Risks / Trade-offs

- **Refactoring the page could change behaviour.** The lib is a move, not a rewrite,
  and the reference cases plus a browser check of the default and a doubles setup
  guard it.
- **The app needs a round trip per change:** a few ms on the home network, with the
  last turn kept on screen.
