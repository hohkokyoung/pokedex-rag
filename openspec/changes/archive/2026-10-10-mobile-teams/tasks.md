# Tasks

## 1. API and data

- [x] 1.1 Add the teams, slots, build, analysis, strategy, summary (+refresh) and builder (moves, form moves, abilities, items, natures) paths to `PATHS`, then run `make mobile-api`. Verify: the drift test and `flutter analyze` pass, and recorded team/analysis/strategy/summary fixtures decode.
- [x] 1.2 Add repository methods and providers with invalidation after every write. Verify with repository tests: payloads for create/rename/delete/set/clear/build, and the analysis `opponent_id` parameter.

- [x] 1.3 Move the website's suggested-item rule (`suggestItem` in `TeamReport.tsx`) to the backend as `SlotSuggestion.recommended_item` (`team_analysis._suggest_item`, a literal port), and have the website read it. ADR-009: both clients must agree. Verify: `test_suggested_item_follows_the_role` (written first, failed on import) passes, `tsc` passes, and the live analysis suggests Life Orb for Garchomp team's Slaking as before.

## 2. Navigation and list

- [x] 2.1 Add the shell route with a NavigationBar (Pokédex, Teams), with tab stacks preserved. Verify with a widget test: switching tabs keeps each tab's place, and detail routes open over either tab.
- [x] 2.2 Build the team list cards (grade, score, style, summary, type facts, six grades, fixes; empty card), plus New team (name dialog) and Delete (confirm). Verify with widget tests: the Garchomp team card shows A, 88/100 and Hyper offense; create POSTs and opens the team; cancelled delete sends nothing; confirmed delete DELETEs.

## 3. Team page

- [x] 3.1 Build the six slots (sprite, types, role, BST), rename, and the Pokémon picker that fills an empty slot. Verify with widget tests: picking Garchomp PUTs `pokemon_id` 445 to that slot; a form pick includes `form_id`.
- [x] 3.2 Build the set editor: ability (hidden marked), item search, nature (+/−), EVs (≤252, ≤510 total), IVs (0–31), up to 4 moves; Save and Remove; rejected saves reported. Verify with widget tests: EV total stops at 510, a fifth move is refused, Save PUTs ids, Remove DELETEs, and a 422 shows the server's message.
- [x] 3.3 Build the report: rating + summary (↻ Regenerate, pending re-check), grades with fixes, strategy axes, type profile, sets with Use suggested, defence per type. Verify with widget tests on the Garchomp team fixtures: 88/100 · A, Defence B 74, Sets C 61, and Use suggested POSTs that slot's suggestion to `/build`.
- [x] 3.4 Compare with…: an opponent picker and a matchup panel (verdict, scorecard, threats, pressure, advice); the rating stays opponent-free. Verify with a widget test: vs Rival shows "Even", 17 won / 18 won and Tyranitar, and the grade stays A 88.

## 4. Check and docs

- [x] 4.1 In the Simulator, on a scratch team created for the check and deleted after: create, add Garchomp, edit the set (Jolly, Scarf, 252/252, 4 moves), compare with Rival, Use suggested, then delete. Confirm the owner's teams are unchanged (before/after list). Run `make test`, `make lint` and `make mobile-test`.
- [x] 4.2 Update `docs/product/mobile.md` (Teams) and `docs/components/mobile.yaml`. Verify: `make test` passes.
