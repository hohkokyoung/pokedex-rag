# Tasks

## 1. Backend: catch rate

- [x] 1.1 Record golden cases from `frontend/lib/catchRate.ts` (≥ 40 species × situations covering every ball branch) into `backend/tests/fixtures/catch_cases.json`. Verify: every ball id appears with a non-default multiplier in some case.
- [x] 1.2 Port to `services/catch_rate.py` + `GET /api/pokemon/{id}/catch`; golden test and API tests (Quick Ball turn 1, sleep at 1% beats full HP, 404, 422). Verify: pytest.
- [x] 1.3 Website: the catch-rate tile reads the endpoint; remove the formula from `lib/catchRate.ts`. Verify: tsc, eslint, and the tile in the browser (change status → ranking updates).

## 2. App: Tools tab

- [x] 2.1 OpenAPI slice: catch, moves/abilities/items search, ability holders; `make mobile-api`. Verify: drift test, analyze.
- [x] 2.2 Tools tab + list; type calculator; nature helper. Verify widget tests: Fire+Flying → Rock ×4, Ground immune; a third pick replaces the oldest; Adamant → +Atk / −SpA.
- [x] 2.3 Catch rate: picker, situation controls, ranked balls, top ball's formula. Verify widget tests: status Sleep sends `status=sleep` and shows the new order; can't-reach state.
- [x] 2.4 Lookup: grouped search, move → move sheet, ability → effect + filterable holders → Pokémon page, item → details. Verify widget tests (leftovers; Intimidate filter gyara → Gyarados page).

## 3. Check and docs

- [x] 3.1 Simulator: each tool against the real server. Run `make test`, `make lint`, `make mobile-test`.
- [x] 3.2 Docs: `docs/product/home.md`, `docs/product/mobile.md`, `docs/components/mobile.yaml`, `docs/components/pokedex.yaml`. Verify: `make test`.
