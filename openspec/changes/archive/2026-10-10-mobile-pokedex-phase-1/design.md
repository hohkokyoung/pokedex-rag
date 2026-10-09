# Design

## Context

- **Backend:** FastAPI on host port 8001, bound to `0.0.0.0`. From the LAN address
  (`192.168.0.244:8001` today), `/api/*` and `/sprites/*` both answer.
  - `GET /health` returns `{"status":"ok"}`.
  - OpenAPI 3.1 is published at `/openapi.json` (39 paths, 101 schemas).
  - The list response carries `sprite_url` paths. 96/320px WebP thumbs live under
    `/sprites/thumbs/{size}/…`, with a PNG fallback (see `thumb()` in
    `frontend/lib/api.ts`).
- **Data the app reads:**
  - `GET /api/pokemon` with `q`, `type[]`, `generation[]`, `sort`, `order`, `limit`
    and `offset`;
  - `GET /api/pokemon/{id}`, which includes forms, matchups, evolution stages and
    members, and `spin_guide` (plus `display` once `evolution-conditions-to-backend`
    lands);
  - `GET /api/types/chart`, `GET /api/types` and `GET /api/generations`.
- **Design source:** DESIGN.md's YAML front matter holds every token: colours
  (including type fill, on-fill and text shades), typography, radii and spacing.
  The fonts are Chakra Petch (display), Space Grotesk (body) and JetBrains Mono
  (readouts).
- **Toolchain:** Flutter 3.44.1 / Dart 3.12.1 through fvm, and Xcode with iOS 26.5
  simulators.

## Goals / Non-Goals

**Goals:**
- The app computes no game rules. It renders server values.
- The API types and design tokens are generated, never hand-copied.
- Everything is checked in the iOS Simulator.

**Non-Goals:**
- State persistence beyond the server address.
- Offline data.
- Release signing.
- Tablet-specific layouts.

## Decisions

### 1. Project layout: `mobile/`, feature-first

```
mobile/
  lib/
    app.dart, main.dart
    api/        generated (swagger_parser): models + retrofit clients; never edited
    data/       repositories wrapping the generated client (paging, chart cache)
    features/pokedex/   list/, detail/, widgets/
    features/settings/
    theme/      tokens.g.dart (generated), theme.dart, type_colors.dart
  openapi.json  committed snapshot (filtered to phase-1 paths)
  swagger_parser.yaml, analysis_options.yaml, .fvmrc
```

- The org is `dev.pokerag` and the app name is `pokérag`; the bundle ID is
  `dev.pokerag.app`.
- `.fvmrc` pins Flutter 3.44.1.

### 2. Generated API client: swagger_parser → retrofit + dio + json_serializable

- **Snapshot:** `make mobile-api` dumps `app.openapi()` from the backend into
  `mobile/openapi.json`, then runs `dart run swagger_parser` and `build_runner`.
  `include_paths` keeps only the endpoints phase 1 uses, so the generated code stays
  small.
- **Committed code:** the generated files are committed. A fresh clone builds without
  generation, and diffs show API changes.
- **Drift guard:** `backend/tests/test_mobile_openapi.py` compares the snapshot with
  the live schema for the included paths and the schemas they reference. A backend
  change that touches them fails `make test` until `make mobile-api` is re-run.
- *Alternative:* openapi-generator's `dart-dio`. Rejected: it needs a JVM toolchain
  and generates far more code.
- *Alternative:* hand-written models. Rejected: that's the drift this phase exists to
  prevent.

### 3. State and navigation: Riverpod + go_router

- **Riverpod:** `AsyncNotifier`s for the paged list (query → pages) and family
  providers for detail by id. The type chart is a `keepAlive` provider, which gives
  the fetch-once rule for free.
- **go_router:** routes are `/`, `/pokemon/:id` (`?form=`) and `/settings`.
- *Alternative:* Bloc. Rejected: more boilerplate for a read-only app.

### 4. Server address and connectivity

- **Default from the build:** `--dart-define=API_BASE_URL=...`. The default is
  `http://localhost:8001`, which the iOS Simulator reaches directly. The Android
  emulator run target passes `http://10.0.2.2:8001`.
- **Saving:** the override is stored with `shared_preferences`. It is saved only after
  `GET {addr}/health` answers `status: ok` within 3 s.
- **Failures:**
  - A dio interceptor maps connection errors and timeouts to an `Unreachable` error.
    Screens render it as the can't-reach state (address + Retry + Change address),
    never as an empty list.
  - Only 404 means "not found".
- **iOS:**
  - `NSAppTransportSecurity` → `NSAllowsLocalNetworking = true`, the narrowest ATS
    exception, covering local IPs and `.local`.
  - `NSLocalNetworkUsageDescription` gives the reason.
- **Android:**
  - `res/xml/network_security_config.xml` with a base config that permits
    cleartext. Domain configs can't match IP ranges, and this is a home-network app;
    revisit if it's ever hosted.
  - Plus the `INTERNET` permission in the main manifest.

### 5. Design tokens generated from DESIGN.md

- `tools/mobile/gen_tokens.py` reads DESIGN.md's front matter and writes
  `mobile/lib/theme/tokens.g.dart`: colours (as `Color`), type fill, on-fill and text
  maps, radii, spacing, and type scale (sizes in logical px; rem × 16). The command is
  `make mobile-tokens`.
- A Dart test checks that every type has fill, on-fill and text entries, so a missing
  token fails.
- The fonts are bundled as assets under the OFL; their licence files are committed
  next to them. `google_fonts` runtime fetching isn't used, so the app needs no
  internet beyond the home network.
- **Motion:**
  - The signature moments are stat bars that draw in and an artwork fade/scale.
  - `MediaQuery.disableAnimations` (iOS Reduce Motion, Android "remove animations")
    swaps them for instant changes.
  - There is no ambient motion.

### 6. What the app computes

- Only the "Hits ×2" list. It is the same lookup the website does (`superEffectiveHits`
  over the served chart): a filter over the fetched chart, not a rule.
- Everything else is rendered as served: matchup buckets, evolution `display`, the
  spin guide, stats and totals.
- Thumbs use the same URL rewrite as `thumb()` (96px for rows, 320px for larger). The
  backend's PNG fallback makes it safe.
- Images are cached with `cached_network_image`.

### 7. Testing

- **Widget tests** with a fake repository: list paging, search reload, the
  can't-reach state, a failed address check, form switch, evolution chips rendered
  verbatim, and reduced motion. Run with `make mobile-test` (`flutter test`).
- **Backend:** the OpenAPI drift test.
- **iOS Simulator checks** per the specs' scenarios: launch, scroll, search, filter,
  Garchomp, Eevee, Alcremie, backend stopped/started, and a 375pt device.

### LLM budget

None. Phase 1 makes 0 LLM calls.

## Risks / Trade-offs

- [The LAN IP changes (DHCP)] → The address is editable, and the can't-reach state
  points to the setting. Suggest a DHCP reservation in the guide.
- [Android cleartext is app-wide] → Accepted for a home-network app, noted in the
  guide. Revisit with hosting/TLS.
- [swagger_parser output for some 3.1 constructs, e.g. `anyOf` with null] → Phase 1
  includes only the paths it needs. If a schema generates badly, patch it with
  `replacement_rules` or a small hand-written model for that schema only, and record
  why in the guide.
- [Generated files bloat diffs] → They are confined to `mobile/lib/api/` and marked
  generated; reviewers skip them.
- [Font files add about 1 MB] → Accepted for offline-safe typography.

## Migration Plan

Purely additive: a new directory, a backend test and Make targets. `mobile/` can be
deleted without touching anything else. The order is:
1. Land `evolution-conditions-to-backend` first.
2. Scaffold and generate.
3. Build features.
4. Simulator pass.

## Docs affected

- New `docs/product/mobile.md` (what the app does) and `docs/guides/mobile.md` (run on
  the Simulator, emulator and phone; set the address; regenerate the API and tokens;
  DHCP tip).
- New `docs/components/mobile.yaml`.
- New ADR-010: the mobile app displays server-computed values; its API types and
  tokens are generated.
- `docs/architecture/overview.md`: the system map gains the app.
- `docs/index.md`; README feature list; CLAUDE.md layout block and commands.
