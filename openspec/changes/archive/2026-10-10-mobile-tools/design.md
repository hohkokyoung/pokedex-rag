# Design

## Context

- `/api/natures`, `/api/types/chart`, `/api/moves?q=`, `/api/abilities?q=`,
  `/api/items?q=` and `/api/abilities/{id}/pokemon` already exist.
- The app's move sheet (phase 2, `detail_more.dart`) shows move details and learners
  per game.
- Catch rate lives only in `frontend/lib/catchRate.ts` and `CatchRateTile.tsx`.

## Goals / Non-Goals

**Goals:**
- catch-rate rules in one place (the server);
- the app's tools match the website's;
- no LLM anywhere.

**Non-Goals:** the advanced finder; the damage calculator (6b).

## Decisions

1. **Catch rate on the server: `services/catch_rate.py`.**
   - It ports `BALLS` (multiplier rules and "why" strings), `catchChance`, `throwsFor`
     and the dex-count critical multiplier exactly.
   - Rounding: `Math.round` → `round_half_up` for HP; `Math.floor` → `math.floor`.
   - `throws` is `null` when the chance is 0 (JS returns `Infinity`).
   - Route: `GET /api/pokemon/{pokemon_id}/catch` with query parameters.
   - The Pokémon's capture rate, base HP and Speed, weight and gender rate are read
     from the DB (forms by their own row).
   - Response: `{pokemon, balls: [{id, name, p, throws, why, sure, terms}]}`, sorted
     by `p` desc with the table order as the tiebreak (JS `sort` is stable).
   - *Alternative:* keep the formula client-side, as the type calculator is. Rejected:
     the ball table is rules, not served data.
2. **Golden cases:**
   - ~40 cases: species × situations covering every ball's branch (turn 1/2/11, night,
     water, caught, love, level ratios, weights, Moon/Ultra Beast species, statuses,
     HP 1/50/100, low level, dex tiers, charm).
   - They're recorded once from the TS module under Node type stripping, then frozen as
     `tests/fixtures/catch_cases.json`.
   - The TS formula is then removed from the website.
3. **Website tile:**
   - It keeps its controls; changes are debounced (150 ms) into one request, and the
     last response is kept while the next loads (no flash).
   - Ball colours stay in `lib/catchRate.ts` (display).
4. **Type calculator in the app** reads the served chart through the cached
   `typeChartProvider`, with the same filters as `defensiveMatchups` /
   `superEffectiveHits`, ordered by the chart's order. This matches the spec "Clients
   read type matchups from the served chart".
5. **Tools tab:**
   - It's a fourth `StatefulShellRoute` branch at `/tools`, with sub-routes
     `/tools/types`, `/tools/natures`, `/tools/catch` and `/tools/lookup`.
   - The list is plain rows, one per tool; each sub-route pushes a page.
6. **Lookup:**
   - Results come from three parallel searches (moves 3, abilities 1, items 2, as on
     the website, but up to 20 each in the app since it's a full page), grouped by
     kind.
   - A move reuses `MoveSheet`.
   - Ability and item each get a detail sheet. Holders come from
     `/api/abilities/{id}/pokemon`, filtered client-side by name.

## LLM budget

None. These tools never call the LLM; tests are keyless.

## Reused / removed

- Reused: the natures, chart, search and holders endpoints; `MoveSheet`; `TypeToggle`;
  the Pokémon picker (catch rate).
- Removed: `catchChance`, `BALLS` rules and `throwsFor` from the website.

## Docs affected

- `docs/product/home.md` (catch rate is computed by the server)
- `docs/product/mobile.md` (Tools)
- `docs/components/mobile.yaml`, `docs/components/pokedex.yaml`

## Risks / Trade-offs

- **Latency on the website tile:** a request per change (debounced) instead of
  instant. On the home network it's a few ms, and the last result stays visible.
- **Float drift between JS and Python:** both use IEEE doubles with the same
  operation order, and the golden test compares with a tolerance of 1e-12 for
  probabilities and exactly for integers.
