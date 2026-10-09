# Tasks

## 1. Golden cases from today's TypeScript

- [x] 1.1 Write `backend/tests/fixtures/evolution_inputs.json`: every distinct `(trigger, min_level, item, condition)` stage in the database, gathered from the detail API or SQL. Verify: the count matches the distinct stages in the DB, and Espeon's, Kadabra→Alakazam's and Sylveon's stages are present.
- [x] 1.2 Add `frontend/scripts/evolution-fixtures.ts`, which runs `buildCondition` on each input and writes `evolution_cases.json`. Verify: two runs give byte-identical output.
- [x] 1.3 Write `backend/tests/test_evolution_display.py`, a pure test that compares every case. Verify: it fails because the module is missing.

## 2. Backend

- [x] 2.1 Implement `services/evolution_display.py` (`evolution_display(stage) -> EvolutionDisplay`) as a literal port. Verify: every golden case passes.
- [x] 2.2 Add `EvolutionDisplay` and `display` to `EvolutionStage`, and fill it in `pokemon_query`'s species and form stage builders. Verify with pytest (DB): Bulbasaur→Ivysaur is "Lv. 16" with no description; Eevee→Espeon is Friendship + Day with a description; Kadabra→Alakazam is Trade. Also check `/api/pokemon/133` on :8001.
- [x] 2.3 Update `docs/components/pokedex.yaml` and ADR-009 (with a dated note). Verify: `make test` and `make lint` pass.

## 3. Website switch-over

- [x] 3.1 Add `display` to `EvolutionStage` in `lib/types.ts`. Have `EvolutionChain.tsx` read `stage.display`, then delete `lib/evolution.ts` and `scripts/evolution-fixtures.ts`. Verify: `tsc --noEmit` and eslint pass, and `grep -rn "buildCondition\|lib/evolution" frontend/` finds nothing.
- [x] 3.2 Check in the browser: Eevee's, Abra's and Alcremie's detail pages show the same chips and "?" descriptions as before (capture text before 3.1), with no console errors.

## 4. Docs check

- [x] 4.1 Confirm every page in design.md "Docs affected" matches the code (`docs/product/pokedex.md` only if it names the old file). Verify: `grep -rn "lib/evolution" docs/ CLAUDE.md` finds only historical mentions, and `make test` passes.
