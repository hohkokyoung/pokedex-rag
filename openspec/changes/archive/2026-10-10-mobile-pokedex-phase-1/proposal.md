# Proposal

## Why

The owner uses pokérag "on a phone beside a console" (PRODUCT.md), but the only client
is a website. A native app makes the Pokédex one tap away mid-game. The backend now
owns the rules every client must agree on (ADR-009): grades, the type chart, the spin
guide and, after `evolution-conditions-to-backend`, the evolution labels. So the app
can display server values instead of re-implementing them. Phase 1 proves the whole
setup (project layout, generated API client, design tokens, network access, simulator
checks) on the simplest surface: a read-only Pokédex.

## What Changes

- **A new Flutter app in `mobile/`** for iOS and Android, run on the home network. It
  talks to the existing FastAPI backend over plain HTTP, with no hosting and no auth.
- **Pokédex list:** search by name or dex number, type and generation filters, sort,
  paged infinite scroll, and artwork thumbnails from the backend's `/sprites`.
- **Pokémon detail:**
  - artwork, types and base stats;
  - type matchups, plus "Hits ×2" from `GET /api/types/chart`, fetched once;
  - abilities;
  - the evolution chain with the backend's labels, forms and the Alcremie spin guide.
- **Server address setting.**
  - The default comes from the build: `localhost` on the iOS Simulator, the
    emulator's host alias on Android.
  - It can be edited and is remembered, and it's checked against `/health`.
  - A clear "can't reach the server" state offers a retry and the setting.
- **Platform network access:** iOS allows local-network HTTP and asks the local-network
  permission with a reason. Android allows cleartext HTTP.
- **Generated API types:** Dart models and the client are generated from a committed
  snapshot of the backend's OpenAPI schema. A backend test fails when the schema
  changes and the snapshot wasn't regenerated.
- **Generated design tokens:** Dart colour, type, radius and spacing tokens are
  generated from DESIGN.md's front matter, the same source the website's tokens
  document. Fonts (Chakra Petch, Space Grotesk, JetBrains Mono) are bundled.
- **New commands:** Make targets for the app: regenerate the API, regenerate the
  tokens, test, run.

**Depends on:** `evolution-conditions-to-backend` (the app shows the backend's
evolution labels).

## Out of scope

- Ask, Teams, the damage calc, the catch-rate and nature helpers.
- Moveset, encounter and learner panels; flavour text beyond the latest entry;
  favourites/profile.
- Offline use beyond image caching; hosting, auth, TLS; store builds and signing.
- Android verification on a device (the emulator is enough; the iOS Simulator is the
  primary check).

## Capabilities

### New Capabilities
- `mobile/pokedex-browsing`: browsing the Pokédex in the app (list, search, filter,
  sort, detail) using only backend data and backend-computed labels.
- `mobile/server-connection`: how the app finds and checks the home-network backend,
  and what it shows when it can't.

### Modified Capabilities
<!-- None: the backend API is unchanged (the OpenAPI snapshot test is tooling). -->

## Impact

- **New:** `mobile/` (Flutter project), `mobile/openapi.json` (snapshot),
  `tools/mobile/gen_tokens.py`.
- **Backend:** `tests/test_mobile_openapi.py`, a snapshot drift check. No runtime
  change.
- **Repo:** Makefile targets; `.gitignore` for Flutter build output.
- **Docs:** `docs/product/mobile.md`, `docs/guides/mobile.md`,
  `docs/components/mobile.yaml`, `docs/architecture/overview.md`, README feature list,
  CLAUDE.md commands, and an ADR for "the app displays, never computes".
- **LLM:** none.
