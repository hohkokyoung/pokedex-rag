# Proposal

## Why

The website's lookup has an Advanced search (every move, ability and item with
filters and sorting). It's the last website feature the app lacks. Two of its rules
live only in the browser (`components/Finder.tsx`):
- **which moves are Z-Moves or Max Moves:** from the name and PP, with three
  ordinary 1-PP exceptions;
- **which games those belong to:** nothing learns them, so the learnset-based game
  lists miss them.

Per ADR-009 those move to the server instead of being copied into Dart.

## What Changes

- **Backend:**
  - `MoveOut` gains `kind` (`regular` | `z` | `max`), computed in
    `services/move_kind.py`;
  - `GET /api/moves/games` places Z-Moves in Sun/Moon and Ultra Sun/Ultra Moon, and
    Max Moves in Sword/Shield.
- **Website:** the finder reads `kind` and the server's game lists; its own
  `kindOf` and `KIND_GAMES` are removed.
- **App:** Lookup gains **Advanced search**, a page with Moves / Abilities / Items
  tabs and their counts, and one search box shared by all three.
  - **Moves:** type toggles, category, kind and game filters, and sorting by
    power, PP, accuracy or name. Same-named Z-Move copies fold into one row with
    both categories.
  - **Abilities:** search by name or effect (matching at a word start), A–Z or Z–A.
  - **Items:** search by name or effect, category filter (most-populated first),
    and sorting by name, cost or Fling power.
  - It shows "N of M" and a "Clear" control. Picking a row opens the same move,
    ability or item sheet as the lookup.

## Capabilities

### New Capabilities
- `mobile/finder`: the app's advanced search.
- `pokedex/move-kinds`: the server's move kind and the games of moves nothing learns.

### Modified Capabilities
(none)

## Out of scope

- New data.
- A server-side search or filter endpoint: catalogs stay small (≈900 moves, ≈300
  abilities, ≈2,000 items) and load once, as on the website.

## Impact

- Backend: `services/move_kind.py`, `services/builder.py` (search_moves,
  move_games), `schemas/builder.py`; tests.
- Website: `components/Finder.tsx`, `lib/api.ts` (`MoveResult.kind`).
- App: `lib/features/tools/finder_screen.dart`, the lookup screen, the route,
  OpenAPI slice (+ `/api/moves/games`).
- Docs: `docs/product/home.md`, `docs/product/mobile.md`,
  `docs/components/mobile.yaml`.
