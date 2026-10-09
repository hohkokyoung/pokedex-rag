# Tasks

## 1. Golden fixtures from today's TypeScript (before anything moves)

- [x] 1.1 Capture `{team, analysis}` pairs for every saved non-empty team from the running app (`GET /api/teams/{id}` and the opponent-free `/analysis`), add hand-built edge cases, and write them to `backend/tests/fixtures/team_rating_inputs.json`. The edge cases: 1 member, a duplicate species, empty move slots, no items, a 4× weakness, a slow team with priority users, and an area score exactly on .5. Verify: the file parses and the edge-case inputs are present.
- [x] 1.2 Add `frontend/scripts/team-rating-fixtures.ts` (same runner as `damage-fixtures`). It runs the current `rateTeam` + `profileTeam` on each input and writes `backend/tests/fixtures/team_rating_cases.json`. It also writes `type_chart_previous.json` (the current `ATTACK_ORDER` + `CHART` expanded to all 324 pairs). Verify: running it twice gives byte-identical output.
- [x] 1.3 Write `backend/tests/test_team_rating.py`, a pure test (no DB). It loads each input into the Pydantic models, rates and profiles it with the frozen chart, and compares to the case field by field. Add `backend/tests/test_type_chart.py` (DB, skips when it's down), comparing the served chart with `type_chart_previous.json`. Verify: both fail on the missing modules or endpoint, for the right reason.

## 2. Backend: type chart and rating engines

- [x] 2.1 In `services/matchups.py`, add `ATTACK_ORDER` and `type_chart(session)` (the 18 battle types only, every pair including 1×). Add `GET /api/types/chart` in `api/pokemon.py` with a response schema. Verify: `test_type_chart.py` passes, plus a pytest asserting ground→flying 0, water→fire 2, fire→water 0.5, normal→normal 1, and that non-battle types are excluded. Hit the endpoint on :8001.
- [x] 2.2 Add `TeamRating`, `RatingArea`, `TypeCover`, `TypeThreat` and `TeamProfile` schemas to `schemas/analysis.py`, and optional `rating` / `profile` fields on `TeamAnalysis`. Include `fast_speed`. Verify: existing analysis tests still pass.
- [x] 2.3 Implement `services/team_rating.py` (`rate_team`) as a literal port of `rateTeam`, with `js_round`, a grade from the unrounded clamped score, stable sorts and the string helpers (see design §3). Verify: the rating half of `test_team_rating.py` passes for every case, including the .5 rounding case.
- [x] 2.4 Implement `services/team_profile.py` (`profile_team`) as a literal port of `profileTeam`, reusing `stats.as_built`. Verify: the profile half of `test_team_rating.py` passes for every case.
- [x] 2.5 In `team_analysis.analyze()`, attach `rating` and `profile` only when there is no opponent and the team has members. Verify with pytest:
  - an empty team gets neither;
  - a with-opponent analysis gets neither;
  - an opponent-free analysis gets both;
  - with no LLM key, and with the LLM client patched to raise 429, the analysis still returns both and no LLM call is made.
- [x] 2.6 Update `docs/architecture/team-coach.md` (engines table: replace the `teamEval.ts` row with `team_rating.py` / `team_profile.py`). Amend `docs/decisions/ADR-007.md`: grades are computed in `services/team_rating.py`, with a dated note. Add the new services and `GET /api/types/chart` to `docs/components/team-coach.yaml` and `pokedex.yaml`. Verify: `make test` (incl. `test_docs.py`) and `make lint` pass.

## 3. Backend: Alcremie spin guide

- [x] 3.1 Add `services/alcremie.py`: steps, Sweet→topping, and the cream rules as an ordered list, copied verbatim from `frontend/lib/alcremie.ts`. Add a `SpinGuide` schema and an optional `spin_guide` on the detail responses that carry evolution fields. Set it in `pokemon_query` when a stage's trigger is `spin`. Verify with pytest (DB): Milcery and Alcremie get 3 steps, 7 toppings and 9 creams, Vanilla Cream first and Rainbow Swirl last; Bulbasaur gets no guide.
- [x] 3.2 Update `docs/components/pokedex.yaml` (and `docs/architecture/data.md` if it describes where game-knowledge constants live). Verify: `make test` passes.

## 4. Frontend switch-over

- [x] 4.1 Add the API types (`TeamRating`, `TeamProfile`, `rating?` / `profile?` on `TeamAnalysis`, `SpinGuide`, `TypeChart`) to `lib/api.ts` / `lib/types.ts`, plus `getTypeChart()`. Verify: `tsc --noEmit` passes.
- [x] 4.2 Rewrite `lib/typeChart.ts` as helpers that take a `TypeChart`, plus a cached `loadTypeChart()` / `useTypeChart()`. Switch `app/page.tsx` (Type Calculator) and `PokemonDetailView.tsx` over, with a skeleton until the chart loads. Verify in the browser: Dragon/Flying shows Ice 4× and Ground immune, and the network panel shows a single `/api/types/chart` request across home → detail → detail.
- [x] 4.3 Switch `TeamCardParts.tsx`, `TeamWorkbench.tsx`, `TeamReport.tsx` and `TeamMatchupText.tsx` to the analysis's `rating` / `profile`. Read `fast_speed` from the rating. Combine profile + rating where the components expect the old `Profile` shape. Verify in the browser: `/teams` cards and each team's detail page show the same grades, scores, style and gist as a pre-change screenshot taken at task 1.1. Selecting an opponent leaves the grade unchanged.
- [x] 4.4 Pass `spin_guide` into `EvolutionChain.tsx`, keeping the cream ordering (guide order, then unknown creams). Verify in the browser: Alcremie's "How it works", toppings and cream rules read the same as the pre-change screenshot.
- [x] 4.5 Delete `lib/teamProfile.ts`, `lib/alcremie.ts`, and `rateTeam` / `WEIGHTS` / `gradeOf` / `FAST_SPEED` from `lib/teamEval.ts` (keep `gradeTone`, `matchupFactors`, `isProvisional`). Delete `scripts/team-rating-fixtures.ts`, keeping its JSON output. Update the `globals.css` comment that names `lib/teamEval`. Verify: `grep -r "teamProfile\|alcremie\|rateTeam" frontend/` finds nothing, and `tsc --noEmit` and eslint pass.
- [x] 4.6 Update `docs/architecture/overview.md` (the `lib/teamEval.ts` row) and the `docs/components/*.yaml` code lists for the deleted files. Verify: `make test` (docs tests) passes.

## 5. Integration and docs check

- [x] 5.1 Rebuild and restart the stack (`make up`), then run `make test` and `make lint`. Verify end to end on :3000:
  - `/teams`, a team detail page with and without an opponent, the home Type Calculator, Garchomp's detail page and Alcremie's detail page all render with no console errors;
  - the grades match the pre-change screenshots.
- [x] 5.2 Docs pass. Check that every page named in design.md "Docs affected" matches the code, including ADR-007 and `docs/architecture/team-coach.md`. `docs/product/teams.md` and the README need no change unless they name a moved file. CLAUDE.md's "Team grades stay deterministic (`frontend/lib/teamEval.ts`)" line is updated to name `services/team_rating.py`. Verify: `grep -rn "teamEval.ts\|teamProfile.ts\|alcremie.ts" docs/ CLAUDE.md README.md` finds only historical mentions.
