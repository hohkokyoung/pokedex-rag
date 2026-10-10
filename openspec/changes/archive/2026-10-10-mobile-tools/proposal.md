# Proposal

## Why

Phase 6a of the mobile app. The website's home page has four reference tools the app
lacks: the type calculator, the nature helper, catch rate and the move / ability / item
lookup. Three of them only display server data. Catch rate is different: the website
computes it in the browser (`lib/catchRate.ts`: the ball table, the Gen 8+ formula,
critical captures). A Dart copy would be a third place for those rules to drift; per
ADR-009 they belong on the server.

## What Changes

- **Backend:** `GET /api/pokemon/{id}/catch` ranks every ball for a situation:
  - the inputs are wild level, your level, HP %, status, turn, night/cave, water,
    caught before, love match, species caught and Catching Charm;
  - each ball comes back with its chance per throw, throws for 90%, why it scores
    that way, and the formula terms;
  - the code is a port of `catchRate.ts`, pinned to its output by golden cases.
- **Website:** the catch-rate tile reads that endpoint; `lib/catchRate.ts` keeps only
  the ball colours and the input defaults.
- **App:** a fourth tab, **Tools**, with:
  - **Type calculator:** pick 1–2 types; shows what the typing takes ×4/×2, resists
    ×½/×¼, is immune to, and hits ×2, read from the served chart as the detail page
    does;
  - **Nature helper:** the 5×5 grid from `/api/natures`; tap one for its ±10%;
  - **Catch rate:** pick a Pokémon, set the situation, and see the server's ranked
    balls with the formula for the top one;
  - **Lookup:** one search over moves, abilities and items. A move opens the existing
    move sheet (details + learners per game); an ability shows its effect and holders
    (filterable); an item shows its effect, category, cost and Fling power.

## Capabilities

### New Capabilities
- `pokedex/catch-rate`: the server's catch-chance ranking and its parity with the old
  client formula.
- `mobile/tools`: the app's Tools tab.

### Modified Capabilities
(none)

## Out of scope

- The damage calculator and its coach (phase 6b).
- The website's advanced finder (filters/sorting over every move, ability and item).
- The home dashboard's team and Ask tiles (the app has those as tabs).
- Gen 1–7 catch formulas; the website only has Gen 8+.

## Impact

- Backend: `services/catch_rate.py`, `api/pokemon.py` (route), `schemas/catch.py`;
  tests and golden fixtures.
- Website: `components/CatchRateTile.tsx`, `lib/catchRate.ts`, `lib/api.ts`.
- App: `lib/features/tools/` (new), `app.dart` (a fourth branch), OpenAPI slice (+ catch,
  moves/abilities/items search, ability holders).
- Docs: `docs/product/home.md` (catch rate is server-side), `docs/product/mobile.md`,
  `docs/components/mobile.yaml`, `docs/components/pokedex.yaml`, and a line in
  `docs/architecture/data.md` or overview if the catch-rate rules are listed there.
