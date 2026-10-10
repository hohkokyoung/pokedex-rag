# Design

## Context

- The server side (`/api/calc/ask`, `calc_state.resolve_state`, the calc tools and
  views) is unchanged.
- The app has: the stream reader `streamAsk` (Ask, team coach), the calculator state
  (`calcProvider`), the server turn (`calcTurnProvider`), and `ViewCard` for dex
  views.

## Goals / Non-Goals

**Goals:** the website's calc coach in the app, with the same requests and the same
click-only Apply / Revert; no new LLM spend in tests.

**Non-Goals:** server changes.

## Decisions

1. **State:**
   - A `calcCoachProvider` notifier holds `{slot, monKey, turns, build, pick, prev,
     applied}`, as on the website, plus a `cardPrev` map (card key → the slots as
     they were).
   - The thread is about the focused slot. Focusing another Pokémon starts fresh, and
     coming back while the proposal's Pokémon is unchanged resumes it.
2. **Request:** `CalcAskRequest` JSON is built from `CalcModel.request()` plus
   `question`, `focus`, `hits` and `proposal`.
   - `hits` come from the last server turn (`attacker`, `target`, `move`, `min_pct`,
     `max_pct`, `ko`, `te`), the same thing the website sends from its own turn.
   - `proposal` is `{slot, build, thread: [{ask, reply}]}` from finished turns.
3. **Stream:** `streamAsk` to `/api/calc/ask`. A `build_proposal` view becomes the
   coach's `build`:
   - the same build (ignoring `why`) keeps `applied`;
   - a different one resets `applied` and `pick`;
   - a build for another slot moves the coach there.
4. **Apply:**
   - **Damage/survive:** each `CalcApply` patches its slot. Fields map
     item→item, ability→ability, nature→nature, evs merged, hp→hp; the preset becomes
     Custom. The previous sets are saved under `turn:view`.
   - **Build:** saves `prev` (set + move) on the first Apply, then sets ability,
     nature, item, EVs (and preset Custom) and the move: the picked chip if it's in
     the learnset, else the build's first damaging move, else its first.
   - **Revert** restores `prev` and clears `applied`.
   - A card is "live" when the calculator's slot still holds the named Pokémon.
5. **Views:** `damage`, `survive` and `build_proposal` decode into the generated
   classes. The build card is drawn above the conversation, not in the turn (as on
   the website).
6. **Placement:** below the slot editor on the calculator page, inside the focused
   Pokémon's area.

## LLM budget

Unchanged server budget (calc coach: plan ≤ 1, build ≤ 1, answer ≤ 1; damage and
survive are closed-form, 0 calls). The app adds none. Fixtures are recorded keyless
with every settings reader patched. The build proposal fixture is hand-written from
the schema, so no LLM is called. The Simulator check uses only closed-form questions.

## Reused / removed

- Reused: `streamAsk`, `HowAnswered`, `AnswerText`, `ViewCard`, the calculator state
  and turn.
- Removed: nothing.

## Docs affected

`docs/product/mobile.md`, `docs/components/mobile.yaml`.

## Risks / Trade-offs

- **The proposal thread lives in memory:** leaving the calculator drops it, as
  reloading the website does.
