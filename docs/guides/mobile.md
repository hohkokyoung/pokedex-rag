# Mobile app

The Flutter app in `mobile/` reads from the same backend as the website, over plain
HTTP on your home network. Flutter is pinned to 3.44.1 with fvm (`mobile/.fvmrc`).

## Run it

The stack must be up (`make up`). Then:

```bash
make mobile-ios
```

That runs on a booted iOS Simulator, which reaches the Mac at `http://localhost:8001`.

```bash
make mobile-android
```

That runs on the Android emulator, which reaches the host at `http://10.0.2.2:8001`.

## On a phone

1. Put the phone on the same Wi-Fi as the Mac.
2. Find the Mac's address: `ipconfig getifaddr en0` (e.g. `192.168.0.244`).
3. In the app, tap the **server** button and enter `http://<that address>:8001`. It's
   saved only if the server answers there.

You can also build with that address as the default:

```bash
make mobile-ios MOBILE_API=http://192.168.0.244:8001
```

**Keep the address stable:** give the Mac a DHCP reservation in your router, or the app
will need a new address whenever the Mac's changes.

**Platform permissions:**
- **iOS:** asks for local-network permission the first time; allow it. Plain HTTP is
  allowed only for local addresses (`NSAllowsLocalNetworking`).
- **Android:** allows cleartext HTTP app-wide (`res/xml/network_security_config.xml`),
  because its rules can't match IP ranges. That's fine for a home-network app;
  revisit if the server is ever hosted behind TLS.

## What's generated (don't edit by hand)

| Files | From | Regenerate |
|---|---|---|
| `mobile/openapi.json`, `mobile/lib/api/` | the backend's OpenAPI schema, limited to the endpoints the app calls (`tools/mobile/openapi_snapshot.py`) | `make mobile-api` |
| `mobile/lib/theme/tokens.g.dart` | DESIGN.md's front matter (colours, type scale, radii, spacing) | `make mobile-tokens` |

`backend/tests/test_mobile_openapi.py` fails when a backend change touches an endpoint
or schema the app uses. Run `make mobile-api`, then fix the app where the generated
types changed. To call a new endpoint, add it to `PATHS` in
`tools/mobile/openapi_snapshot.py` and regenerate.

The fonts (Chakra Petch, Space Grotesk, JetBrains Mono) are bundled in
`mobile/assets/fonts/` with their OFL licences.

## Test

```bash
make mobile-test
```

That runs `flutter test`: widget and unit tests against a fake backend
(`test/support/`), using recorded responses in `test/fixtures/`. Layout tests run at
375pt (iPhone SE) and fail on any overflow.
