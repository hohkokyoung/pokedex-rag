# Proposal

## Why

Phase 1 brought over the Pokédex's core: list, stats, matchups and evolution. The
website's detail page has more that a player reaches for mid-game: what a Pokémon learns
in *this* game, where to catch it, its dex entries and breeding facts, and the
favourites that steer Ask's "for you" picks. Phase 2 brings the app's Pokédex up to the
website's.

## What Changes

- **Facts and training & breeding** on the detail page:
  - height, weight, habitat, capture rate, base experience, colour;
  - gender ratio, egg groups, egg cycles (about how many steps), growth rate, EV
    yield, base friendship.
- **Moveset per game:**
  - a game picker (newest by default) and groups: Level-up (an evolution move reads
    "Evo"), Egg, TM/HM (with the TM number), Tutor, Other;
  - filters by category and type;
  - tapping a move opens its details and **who else learns it in that game**, and each
    learner opens its own page.
- **Dex entries**, grouped by generation.
- **Where to find:** a game picker plus each encounter's location, area, method,
  levels, rate and conditions; raid dens included.
- **Favourites:** a heart on the detail header saves the Pokémon to the server profile
  (the same one the website and Ask use), plus a Favourites screen from the list.
- **Previous / next** buttons on the detail page move through the dex.

All data comes from existing endpoints. The app only formats it (percentages, step
counts).

## Out of scope

- Ask, Teams, calculators (later phases).
- Editing preferred types (a website profile setting).
- The website's gender artwork toggle and the 63-variant Alcremie gallery.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `mobile/pokedex-browsing`: adds the detail sections, the moveset and learners,
  encounters, favourites and dex navigation.

## Impact

- **Mobile:** new detail sections, a move sheet, a favourites screen, and new
  repository methods. The OpenAPI slice gains `/api/pokemon/{pokemon_id}/moves/by-game`,
  `/api/moves/{move_id}/learners/by-game`, `/api/pokemon/{pokemon_id}/encounters` and
  `/api/profile` (+ favourites POST/DELETE).
- **Backend:** none.
- **Docs:** `docs/product/mobile.md`, the mobile manifest's interfaces.
