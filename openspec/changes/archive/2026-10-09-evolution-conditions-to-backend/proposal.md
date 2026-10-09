# Proposal

## Why

The evolution chain labels each step with chips and a plain-English description:
"Lv. 36", "Friendship + Day", "Use a Water Stone.". Today that wording is built in
the browser by `frontend/lib/evolution.ts`. The planned mobile app needs the same
labels. Under ADR-009, wording that two clients must agree on is computed by the
backend. This change does that before the app is built (`mobile-pokedex-phase-1`
depends on it).

## What Changes

- Every evolution stage in the Pokémon detail response gains a `display`: an ordered
  list of chips (each `solid` or `soft`) and an optional description. This covers the
  species chain and each form's chain.
- The backend computes it by porting `buildCondition`. For every evolution stage in
  the ingested data, it returns exactly what the website showed: same chips, order,
  tones and description. Frozen golden cases prove this.
- The website's evolution chain reads `display`. `frontend/lib/evolution.ts` is
  deleted.
- ADR-009's list of what stays client-side drops "the evolution condition text".

## Out of scope

- No wording changes; this is a move.
- The raw stage fields (`trigger`, `min_level`, `item`, `condition`) stay in the
  response, unchanged.
- The mobile app itself (`mobile-pokedex-phase-1`).

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `pokedex/reference-data`: adds a requirement that evolution stages carry their
  display labels from the backend.

## Impact

- **Backend:** new `services/evolution_display.py`, an `EvolutionDisplay` schema on
  `EvolutionStage` (`schemas/pokemon.py`), and filling it in `pokemon_query`.
- **Frontend:** `EvolutionChain.tsx` and `lib/types.ts`. `lib/evolution.ts` is
  deleted.
- **Tests:** golden fixtures over every ingested stage, made from the current
  TypeScript.
- **Docs:** ADR-009, `docs/components/pokedex.yaml`.
- **LLM:** none.
