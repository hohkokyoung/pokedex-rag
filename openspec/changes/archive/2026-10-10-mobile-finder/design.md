# Design

## Context

- `Finder.tsx` loads every move, ability and item plus the games once, then filters
  in memory.
- The rules that aren't UI are `kindOf` (Max by name, Z by 1 PP minus three
  exceptions) and `KIND_GAMES` (Z → Sun/Moon and Ultra Sun/Ultra Moon, Max →
  Sword/Shield).

## Goals / Non-Goals

**Goals:** website parity in the app; the two rules on the server; no LLM.

**Non-Goals:** server-side filtering.

## Decisions

1. **`services/move_kind.py`:**
   - `move_kind(identifier, name, pp)` exactly as `kindOf`;
   - `KIND_GAMES` maps a kind to version-group identifiers;
   - `search_moves` fills `kind`;
   - `move_games` adds the moves of each kind to the mapped games, using every move's
     kind from the moves table.
2. **Website:** `MoveResult.kind` replaces `kindOf`. The game filter uses
   `inGame.ids` only, since the server already includes Z and Max Moves. Folding
   stays: it's display.
3. **App:**
   - `FinderScreen` at `/tools/lookup/finder`, opened from an "Advanced search"
     button on Lookup.
   - The catalogs are `FutureProvider`s (all moves, `limit` 2000; all abilities,
     2000; all items, 5000; games), kept for the session.
   - Filtering, sorting and folding are pure Dart functions (unit-tested), mirroring
     the website's in-memory behaviour.
   - Filters use the app's controls: the type toggle strip, compact multi-select
     sheets for category, kind and game, and `Segmented` sort keys with a direction
     toggle.
   - Rows are dense (name, type chip / category, numbers in mono). Picking one opens
     `showMoveSheet` (game null) or the ability or item sheet.

## LLM budget

None.

## Reused / removed

- Reused: lookup sheets, `TypeToggle`, `Segmented`.
- Removed: `kindOf` and `KIND_GAMES` from the website.

## Docs affected

`docs/product/home.md` (kinds from the server), `docs/product/mobile.md`,
`docs/components/mobile.yaml`.

## Risks / Trade-offs

- **Payload:** about 2,000 items in one request (≈400 KB) when the Items tab first
  loads. It's loaded lazily per tab and fine on the home network.
