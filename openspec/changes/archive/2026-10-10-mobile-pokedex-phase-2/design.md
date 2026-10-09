# Design

## Context

Phase 1 built `mobile/` with a generated client (`tools/mobile/openapi_snapshot.py`
PATHS → `make mobile-api`), Riverpod providers, `DetailBody` sections, a fake backend
for tests, and an artwork provider. The endpoints this phase needs already serve the
website: `builder.moves_by_game`, `builder.move_learners_by_game`,
`encounters.encounters_by_game`, and the profile routes.

## Decisions

1. **Extend the slice, regenerate.** Add the moveset, learners, encounters and profile
   paths (incl. `POST/DELETE /api/profile/favorites/{pokemon_id}`) to `PATHS`. Then
   `make mobile-api`. The drift test covers them automatically.
2. **The detail page gets a second tier of sections** below Evolution: Moveset, Where to
   find, Dex entries, Facts / Training & breeding. Each data-heavy section is its own
   `FutureProvider.family` keyed by (pokemon id, game), so switching games refetches
   only that section and failures stay local. A section's can't-reach failure shows an
   inline Retry rather than replacing the page.
3. **Moves for a form** use the form id (> 10000), as the website does
   (`/pokemon/{form_id}/moves/by-game`).
4. **Move sheet:** a modal bottom sheet with the move's facts, from the moveset row, plus
   the learners for the selected game. Each learner opens `/pokemon/{dex}` (`?form=`
   for forms).
5. **Favourites:**
   - a `favouritesProvider` (Notifier over `GET /api/profile`) with optimistic
     add/remove that reverts on failure;
   - the heart in the detail header;
   - a `/favourites` route from the list's app bar.
6. **Previous / next** by dex number, 1..(list total from the backend). The bounds come
   from the list response's `total`, not a hard-coded 1025.
7. **Formatting only:** the gender ratio (rate/8 female, −1 genderless), steps
   ((cycles + 1) × 255) and EV yield text mirror `TrainingBreeding.tsx`. They are
   display, not rules (ADR-009/010).

LLM budget: none (0 calls).

## Risks / Trade-offs

- [Long movesets (100+ rows) in one ListView] → It's a lazy builder inside the page's
  scroll; group headers are sticky-free to keep it simple.
- [Optimistic favourite toggles diverging] → Revert on failure and refresh the profile
  after each change.

## Docs affected

`docs/product/mobile.md` (detail sections, favourites) and
`docs/components/mobile.yaml` (interfaces).
