---
name: web-to-flutter
description: Convert a pokérag website page or component (frontend/, Next.js) into the Flutter app (mobile/), keeping the website's design language with phone-first UX; or audit an existing app screen against its web page and fix the drift. Use when the user says "bring X to the app", "port this page to mobile", "make the app match the website", "audit the app screen", or names a web component to convert.
---

# Web → Flutter (pokérag)

Two modes. Pick from the request; ask if it's unclear.

- **Convert:** a website page or component becomes an app screen (or part of one).
- **Audit:** compare an existing app screen with its web counterpart, list the
  differences, then fix the ones the user picks.

The goal in both: **the website's language, cleaner, with phone UX.** Not a copy of the
web layout, and not stock Material. Read these before writing code:

- [references/translation.md](references/translation.md): how each web pattern becomes
  a phone pattern. This is the core of the skill.
- [references/components.md](references/components.md): the app's shared widgets. Reuse
  them; never rebuild one inline.
- [references/audit.md](references/audit.md): the checklist for Audit mode, also the
  final check in Convert mode.

Also read `PRODUCT.md`, `DESIGN.md`, `docs/product/mobile.md` and the web page's own
doc in `docs/product/` (the CLAUDE.md table says which).

## 0. Before anything: current docs

Ask the user once per session: *"Check the current Flutter / Riverpod / go_router docs
before building? (recommended)"* Default to yes.

- If yes, look up the APIs you are about to use with the context7 tools
  (`resolve-library-id`, then `query-docs`): Flutter widgets, flutter_riverpod 3,
  go_router, dio/retrofit.
- Pin to the repo's versions (`mobile/pubspec.lock`, fvm `3.44.1` in `.fvmrc`).
- If the docs show a better pattern than the repo uses, or a newer version, **flag it to
  the user; don't change it** as part of the conversion.

## 1. Read the web side

1. Read the component, its CSS (`frontend/app/globals.css`, search its class prefix),
   and the data it loads (`frontend/lib/api.ts`).
2. Look at it running at phone width. Use the built-in browser on
   `http://localhost:3000`, resize to the mobile preset, and screenshot. If the frontend
   isn't up, say so and work from the code.
3. Write down, briefly:
   - what the user does there (the jobs, not the widgets);
   - what data each part needs;
   - which rules live in the web client only.

**Client-only rules move to the backend (ADR-009).** Examples: a sort, a classification,
"which games had this". Don't port them to Dart. Add the rule to the backend with a
test, expose it, and have both the website and the app read it. Then add the path to
`tools/mobile/openapi_snapshot.py` and run `make mobile-api`. `backend/tests/test_mobile_openapi.py`
fails if the snapshot is stale.

## 2. Map it (show the user before building)

For each web part, pick its phone form from `references/translation.md` and its widget
from `references/components.md`. Give the user a short map:

| Web part | App part | Why (only when the UX changes) |
|---|---|---|

Ask about anything that changes behaviour, not just look. Examples: dropping a column,
moving a control into a sheet, hiding rows behind "Show all".

## 3. Build

Stack, as the repo uses it:

- **State:** Riverpod 3 (`Provider` / `FutureProvider` / `NotifierProvider`, `.family`,
  `autoDispose` for per-screen data).
- **Navigation:** routes in `lib/app.dart` through `_go(...)`, which always builds a
  `MaterialPage`. A page with no transition flashes and can't be swiped back. Tabs are
  the `StatefulShellRoute` branches.
- **API:** only through the generated client (`lib/api/`). Never hand-write JSON models.
- **Styling:**
  - tokens from `lib/theme/tokens.g.dart` (`Palette`, `Radii`, `Space`, `TypeColors`);
  - type from `AppText`, which is the phone scale (body 14);
  - no hex literals except where an existing widget already defines the colour.
- **Interaction:**
  - feedback through `Pressable` (dims), never `InkWell` ripples on new UI;
  - `HapticFeedback.selectionClick()` on selections;
  - respect `MediaQuery.disableAnimations`, and use the ease-out curve
    `Cubic(0.16, 1, 0.3, 1)`.
- **Keys:** give every interactive widget a stable `Key('...')`. The tests drive the UI
  by key.

## 4. Test

- **Widget tests** go in `mobile/test/`:
  - drive the app through `pumpApp` (`test/support/app_harness.dart`), against a
    `FakeBackend` serving recorded fixtures (`test/fixtures/*.json`);
  - record fixtures from the running backend with `curl`, never by hand;
  - large JSON already decodes synchronously in tests (`dioTransformerProvider`). If a
    test hangs in `pumpAndSettle`, check for a request that never resolves, or call
    `flush(tester)`.
- **Bug fixes:** write the failing test first, see it fail, then fix.
- **Feature work:** each spec scenario becomes a test.
- **Run:** `make mobile-test` (and `make test` if the backend changed), unless the user
  said to skip tests. Say so if you skipped them.

## 5. Check on the Simulator (always)

1. Build: `cd mobile && fvm flutter build ios --simulator --debug`.
2. Install and launch with `xcrun simctl install/launch` and bundle id
   `dev.pokerag.pokerag`. Use the booted device (`xcrun simctl list devices booted`).
3. Screenshot with the iOS Simulator tool and look at it next to the web screenshot
   from step 1.
4. Check:
   - the default state;
   - a long list scrolled;
   - an empty state;
   - an open sheet;
   - the narrowest case (375pt; long names).

Show the user the screenshots before calling it done. Fix what looks off, the same way
`references/audit.md` describes.

## 6. Record it

- **Docs:** update `docs/product/mobile.md` (what the screen does) in the same commit,
  and `docs/components/mobile.yaml` if the app uses a new endpoint.
- **OpenSpec:** only if the repo has it (`openspec list --json` returns a root). Then
  run propose → apply → archive for the change, one change per shippable piece:
  - `mobile/<capability>` specs for app behaviour;
  - `pokedex/...` or the relevant area for any backend rule you moved.

  Without OpenSpec, skip this step and say nothing about it.
- **Commit** on the current branch, with a message that says what the user sees. Push
  only when asked.

## Audit mode

1. Open the web page (phone width) and the app screen (Simulator), and screenshot both.
2. Walk `references/audit.md` item by item. Write a short list:
   - what differs;
   - which side is right;
   - the fix.
3. Show the list and let the user pick. Then fix, using steps 3–6.

## What the user has already decided (don't relitigate)

- The app is the **website's light Instrument language, cleaner**, not a new identity.
- **iOS feel on both platforms:**
  - no ripples;
  - Cupertino page slides with swipe-back, spinner, alerts and switches;
  - check-row sheets instead of dropdowns.
- **One corner scale:** 6 chips, 8 insets, 10 controls (and pills, buttons, inputs),
  14 panels. Never stadiums or circles for controls.
- **Red only for actions and the current selection;** Ask is the red tab.
- **Show less by default:** the top items plus "Show all"; fold detail (formulas, IVs,
  field settings) into panels.
- **Text:** the phone scale, with roomy type chips. Cramped chips and oversized text
  both came up as complaints.
- **Answers (Ask and both coaches) share one layout:**
  - the verdict first;
  - artwork rows;
  - small red citation chips;
  - suggestions as rows in one panel.
- The user reviews visually and fast. Prefer one well-built screen they can see over
  options to choose from. When they say something looks off, change it. Don't defend it.
