# Tasks

## 1. Backend and website

- [x] 1.1 `move_kind` + `MoveOut.kind` + games include Z/Max moves; tests (kinds of Max Airstream, Breakneck Blitz, Sketch, Earthquake; Sword/Shield has Max Airstream, no Z). Verify: pytest.
- [x] 1.2 Website finder uses `kind` and the server's games; remove `kindOf`/`KIND_GAMES`. Verify: tsc, eslint, browser (kind and game filters).

## 2. App

- [x] 2.1 OpenAPI slice (`/api/moves/games`), `make mobile-api`; catalog providers; pure filter/sort/fold functions with unit tests (fold, category on folded, sink nulls, effect word-start match).
- [x] 2.2 Finder screen (tabs, shared search, counts, filters, sort, clear) + Lookup entry + route; widget tests (rain across tabs, fire special by power, Max in Sword/Shield, items by Fling).

## 3. Check and docs

- [x] 3.1 Simulator check; `make test`, `make lint`, `make mobile-test`.
- [x] 3.2 Docs.
