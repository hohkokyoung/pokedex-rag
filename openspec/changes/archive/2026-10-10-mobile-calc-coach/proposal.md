# Proposal

## Why

Phase 6c, the last one: the damage calculator's coach. The website lets you ask about
the focused Pokémon:
- damage questions ("Can Garchomp OHKO Corviknight?");
- bulk thresholds ("How much bulk does it need to survive…?");
- builds ("a bulky set for doubles") with follow-ups.

Its cards apply into the calculator with Revert. The coach already runs on the server
(`POST /api/calc/ask`); the app only needs the client side.

## What Changes

- **App, the calculator gains a Coach section for the focused Pokémon:**
  - quick questions: the website's starters ("Best build", "Bulky set", "Fast
    sweeper") or follow-ups once a build is proposed, plus the damage and bulk
    questions for the focused matchup;
  - a question box and the conversation, each turn with the answer, How line and
    error state.
- **Cards:**
  - **Damage:** the current hit, and with a what-if its result, with **Apply**
    (into the calculator) and **Revert**.
  - **Survive:** the current hit and the least bulk that survives (or "already
    survives" / "can't survive"), with **Apply EVs** and **Revert**.
  - **Build proposal:**
    - the proposal against the current set (ability, nature, item, EVs) and its
      full moveset, with **Apply** (set plus a chosen move) and **Revert**;
    - a follow-up that changes the build replaces the card and needs a new Apply;
    - one that leaves it alone keeps it applied.
  - Cards are disabled once the calculator no longer holds the Pokémon they're about.
- Each question sends the calculator state: sets, moves, aims, field, focus, the
  server's turn as the hits shown, and the proposal with its thread.
- The coach's view kinds (`damage`, `survive`, `build_proposal`) join the app's view
  decoding. `/api/calc/ask` joins the OpenAPI slice.

## Capabilities

### New Capabilities
- `mobile/calc-coach`: the calculator's coach in the app.

### Modified Capabilities
(none — the server's coach and its rules are unchanged)

## Out of scope

- Any change to the coach's planning, tools or budget.
- Saving anything: as on the website, Apply only changes the calculator.

## Impact

- App: `lib/features/tools/calc_coach*.dart` (new), `calc_state.dart`,
  `calc_screen.dart`, `features/ask/views.dart`, OpenAPI slice.
- Docs: `docs/product/mobile.md`, `docs/components/mobile.yaml`.
