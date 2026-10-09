# Tasks

## 1. API

- [x] 1.1 Add the moveset, learners, encounters and profile paths to `PATHS`, then run `make mobile-api`. Verify: `flutter analyze` is clean, the drift test passes, and recorded fixtures (Garchomp moves, Earthquake learners, Garchomp encounters, profile) decode in a Dart test.
- [x] 1.2 Add repository methods: `moves(id, game)`, `learners(moveId, game)`, `encounters(id, version)`, `profile()`, `addFavourite`, `removeFavourite`. Verify with repository tests against the fake backend, including the query parameters.

## 2. Detail sections

- [x] 2.1 Facts and training & breeding. Verify with a widget test: Garchomp shows 1.9 m, 95.0 kg, ♂ 50% · ♀ 50%, Monster/Dragon, 40 cycles (~10,455 steps), Slow, 3 Attack; and a genderless fixture reads Genderless.
- [x] 2.2 The moveset: game picker, groups ("Evo" for level 0, TM labels), category and type filters. Verify with widget tests: Crunch shows Evo under Level-up, a TM row shows its label, picking a game refetches with that version group, and filters narrow the rows.
- [x] 2.3 The move sheet with details and learners for the selected game; each learner navigates. Verify with a widget test: tapping Earthquake shows its power and the learners (Torterra), and tapping a learner opens its page.
- [x] 2.4 Dex entries grouped by generation, and Where to find with a game picker and the empty state. Verify with widget tests: Garchomp's Crown Tundra Max Raid dens (Lv 45–60) and entries under Gen IV.

## 3. Favourites and navigation

- [x] 3.1 Favourites: the heart (optimistic add/remove with revert) and a `/favourites` screen. Verify with widget tests: add → POST and the item is listed; remove → DELETE; a failed POST reverts the heart.
- [x] 3.2 Previous / next by dex number with bounds from the list total. Verify with a widget test: Next on #445 opens #446; #1 has no Previous.

## 4. Check and docs

- [x] 4.1 In the Simulator, check Garchomp's moveset (both games), Earthquake learners, encounters, entries, facts, favourite on/off (and that it shows on the website's profile), and prev/next. Run `make test`, `make lint` and `make mobile-test`.
- [x] 4.2 Update `docs/product/mobile.md` and the interfaces in `docs/components/mobile.yaml`. Verify: `make test` (docs checks) passes.
