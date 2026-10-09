# Tasks

> Starts after `evolution-conditions-to-backend` is applied (the app shows its `display` labels).

## 1. Scaffold

- [x] 1.1 Create the Flutter project in `mobile/` (org `dev.pokerag`, iOS + Android) pinned to Flutter 3.44.1 via `.fvmrc`. Add riverpod, go_router, dio, retrofit, json_annotation, shared_preferences and cached_network_image, plus the swagger_parser, build_runner, retrofit_generator and json_serializable dev deps. Add Flutter build output to `.gitignore`. Verify: `flutter analyze` is clean and the template runs in the iOS Simulator.
- [x] 1.2 Add Make targets `mobile-api`, `mobile-tokens`, `mobile-test`, `mobile-ios` and `mobile-android` (the last passes `API_BASE_URL=http://10.0.2.2:8001`). Verify: `make -n` shows each command.

## 2. Generated API client

- [x] 2.1 Write `swagger_parser.yaml` (json_serializable, retrofit, `include_paths` for `/api/pokemon`, `/api/pokemon/{id_or_name}`, `/api/types`, `/api/types/chart`, `/api/generations` and `/health`). Have `make mobile-api` dump the backend schema to `mobile/openapi.json` and generate into `mobile/lib/api/`. Verify: generation succeeds, `flutter analyze` is clean, and a Dart test decodes recorded JSON for Garchomp's detail and a list page into the generated models.
- [x] 2.2 Add `backend/tests/test_mobile_openapi.py`, which compares the snapshot's included paths and referenced schemas with `app.openapi()`. Verify: it passes now, and fails after a temporary field rename on `PokemonDetail` (then revert).
- [x] 2.3 Add the repositories in `mobile/lib/data/`: a paged list with query reset and end-of-results, detail by id, and a keep-alive type chart. Map dio connection errors and timeouts to `Unreachable`. Verify with unit tests against a mock dio adapter: paging, no duplicates, end detection, the chart requested once, and the error mapping.

## 3. Theme

- [x] 3.1 Write `tools/mobile/gen_tokens.py` and `make mobile-tokens`, generating `mobile/lib/theme/tokens.g.dart` from DESIGN.md's front matter. Verify: running it twice is byte-identical, and a Dart test asserts all 18 types have fill, on-fill and text colours.
- [x] 3.2 Bundle Chakra Petch, Space Grotesk and JetBrains Mono, with their OFL licence files, and build `theme.dart` (light Instrument theme, text styles from the tokens). Ask before downloading the font files, and name the source and size. Verify: a golden or widget test renders a type chip and a heading with the bundled families.

## 4. Server connection

- [x] 4.1 Add the server address: a dart-define default, a saved override, a health check before saving (3 s timeout), and a settings screen. Verify with widget tests: a wrong address isn't saved and shows the reason, a right address is saved and reloads the list, and the value survives a restart (fake prefs).
- [x] 4.2 Add the can't-reach state (address, Retry, Change address) used by list and detail. Verify: a widget test with an unreachable fake shows it instead of an empty list, and Retry recovers.
- [x] 4.3 Add iOS `NSAllowsLocalNetworking` + `NSLocalNetworkUsageDescription`, and Android `network_security_config.xml` + `INTERNET`. Verify: the Simulator reaches `localhost:8001`, the Android emulator reaches `10.0.2.2:8001`, and Info.plist has no other ATS exceptions.

## 5. Pokédex list

- [x] 5.1 Build the list screen: rows (dex number, name, type chips, 96px thumb), infinite scroll, and an empty "no Pokémon match" state with Clear filters. Verify with widget tests: the first page renders Bulbasaur, the next page appends near the end, and nothing loads past the end.
- [x] 5.2 Add search (debounced), type (up to 2) and generation filters, and sort + order, all of which reload from page 1. Verify: a widget test confirms each control resets paging, and in the Simulator "garch", "445", Dragon + Gen 4 and Speed descending behave as the spec says.

## 6. Pokémon detail

- [x] 6.1 Build the detail header and stats: artwork, name, dex number, genus, type chips, base stats with total and draw-in bars, and abilities with hidden marked. Add a form switcher that swaps types, stats, abilities, matchups and artwork. Verify: in the Simulator, Garchomp shows 600, Rough Skin as hidden, and Mega Garchomp switches. Also add a widget test for the form switch.
- [x] 6.2 Add the matchups: buckets from the response, plus "Hits ×2" from the cached chart, with a placeholder until it loads. Verify: Garchomp's Hits list is Fire, Electric, Poison, Rock, Dragon, Steel, and the chart is requested once across three detail opens (Simulator, plus a repository test).
- [x] 6.3 Add the evolution chain with backend `display` chips (tap for the description), forms and the spin guide. Verify in the Simulator: Eevee shows "Water Stone" and "Friendship" + "Day", and Alcremie shows 3 steps, 7 toppings and 9 creams. Add a widget test that chips render verbatim.
- [x] 6.4 Respect reduced motion, and lay out for 375pt. Verify: a widget test with `disableAnimations` shows the final state immediately, and an iPhone SE-size simulator shows no overflow or clipping on list and detail.

## 7. End-to-end and docs

- [x] 7.1 Do a full Simulator pass of every spec scenario, including stopping the backend (`docker compose stop backend`) to see the can't-reach state, then starting it and tapping Retry. Run `make test`, `make lint` and `make mobile-test`. Verify by noting each scenario's result.
- [x] 7.2 Docs:
  - new `docs/product/mobile.md`, `docs/guides/mobile.md` (Simulator, emulator, phone address, DHCP tip, regenerating the API and tokens) and `docs/components/mobile.yaml`;
  - ADR-010 plus a row in the ADR index;
  - the app added to `docs/architecture/overview.md` and `docs/index.md`;
  - the README feature list;
  - the CLAUDE.md layout block and commands.

  Verify: `make test` (docs link and manifest checks) passes.

> **Note (2026-10-10):** the 375pt checks in 6.4 and 7.1 were done by the widget tests in
> `mobile/test/narrow_test.dart` (list, Garchomp, Alcremie and the can't-reach screen at
> 375×667, failing on any overflow), not on an SE simulator: access to that simulator
> wasn't granted, and the owner chose to archive on the test evidence. Every other
> scenario in 7.1 was run in the iPhone 17 Simulator (list, search "garch"/"445",
> Dragon + Gen IV, Speed ↓, Garchomp + Mega form, Hits ×2, Eevee chips + description,
> Alcremie spin guide, backend stopped → can't-reach → Retry) and on the Android emulator.

