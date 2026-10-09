# Design

## Context

The website's Teams pages read:
- `GET/POST /api/teams`, `GET/PUT/DELETE /api/teams/{id}`;
- `PUT/DELETE /api/teams/{id}/slots/{slot}` and `POST …/slots/{slot}/build`;
- `GET …/analysis[?opponent_id]` (rating and profile on the opponent-free read),
  `GET …/strategy` and `GET …/summary` (+ `POST …/summary/refresh`);
- the builder lookups: `/pokemon/{id}/moves`, `/pokemon/forms/{form_id}/moves`,
  `/pokemon/{id}/abilities`, `/items?held=true`, `/natures`.

The app's phase 1–2 patterns apply: the OpenAPI slice → generated client, repository +
Riverpod, fake-backend widget tests, Section cards.

## Decisions

1. **Shell navigation:** a go_router `StatefulShellRoute.indexedStack` with a
   `NavigationBar` (Pokédex, Teams). Each tab keeps its own stack. Detail routes
   (`/pokemon/:id`) stay top-level, so they open over either tab.
2. **Providers:**
   - `teamsProvider` (list);
   - `teamProvider(id)`;
   - `teamAnalysisProvider((id, opponentId?))`, plus the opponent-free one for the
     rating;
   - `strategyProvider(id)` and `summaryProvider(id)`.

   Every write (slot set, clear, build, rename, create, delete) invalidates the team, its
   analyses, its strategy, its summary and the list. The summary is re-fetched a couple
   of times while `pending` is true, as on the website's cards. It never polls
   indefinitely.
3. **Set editor:**
   - A full-screen route `/teams/:id/slot/:slot`. Its state starts from the
     member's set.
   - Abilities: `/pokemon/{id}/abilities` for species, or the form's own abilities
     from the detail response for forms. Moves: `/pokemon/{id}/moves` or
     `/pokemon/forms/{form_id}/moves`.
   - Items are searched as you type (`/items?q=&held=true`); natures are loaded once.
   - EV steppers clamp to 252 per stat and 510 in total, the same limits the server
     validates (`SlotUpdate._ev_spread`). IVs go 0–31.
   - Save sends a single `PUT …/slots/{slot}` with ids.
4. **Pokémon picker:** a search sheet over `/api/pokemon` (the list endpoint already
   includes forms with `form_id`). Picking sends `PUT …/slots/{slot}` with
   `pokemon_id` (+ `form_id`).
5. **Report:** the sections mirror `TeamReport.tsx`, reading only server fields
   (`rating`, `profile`, strategy, summary, `sets`, `suggestions`, `vs_opponent`).
   **Use suggested** posts `…/slots/{slot}/build` with the slot's suggestion (moves,
   ability, nature, EVs), and the server fills only empty parts (`apply_build`).
6. **Compare:** an opponent picker (other saved teams) sets a page-local `opponentId`.
   The matchup panel reads `vs_opponent` (verdict, scorecard, threats, our_pressure,
   advice). The rating always comes from the opponent-free analysis.
7. **Suggested item moves to the backend** (found during apply). The website's
   `suggestItem` (role → Leftovers / Choice Band or Specs / Life Orb / Focus Sash) was a
   rule only the browser knew. It becomes `SlotSuggestion.recommended_item`, so the app
   doesn't copy it (ADR-009).
8. **Testing writes on the real server:** Simulator checks create a scratch team and
   delete it at the end. The owner's teams are never edited.

LLM budget: 0 per screen. ↻ Regenerate = the existing single summary call
(keyless/429 → rules summary, unchanged backend behaviour).

## Risks / Trade-offs

- [The set editor is a large screen] → It's split into widgets per field; widget
  tests cover limits and saving.
- [Many invalidations after a write cause several requests] → Acceptable on a LAN. The
  list re-fetches lazily when its tab is shown.

## Docs affected

`docs/product/mobile.md` (Teams) and `docs/components/mobile.yaml` (interfaces,
depends_on team-coach).
