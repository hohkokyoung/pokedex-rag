# Per-Form Detail View — Design

**Date:** 2026-09-20
**Status:** Approved for planning
**Area:** Pokédex detail page (frontend + backend forms subsystem)

## Problem

On a species detail page the form switcher (e.g. **Galarian Darumaka**, **Hisuian
Growlithe**) only swaps a *subset* of the view. Selecting a form updates
sprite / name / types / stats / abilities / matchups / physique, but the
**Moveset**, **Evolution**, and **Dex Entries** panels keep rendering the base
species' data, and the selection is lost on refresh. This produces visibly wrong
pages: Galarian Darumaka shows the red Unovan evolution sprites, and Hisuian
Growlithe shows the base Growlithe learnset and Growlithe → Arcanine chain.

There is also a latent data bug behind the Evolution panel: the evolution ingest
collapses multiple `pokemon_evolution` rows for one evolved species into the last
one seen, so a species with a form-dependent method (e.g. Darmanitan: Lv.35 Unovan
vs Ice Stone Galarian) loses its default method.

## Goals

- Selecting a form updates **Moveset**, **Evolution**, and **Dex Entries** to that
  form's data where the ingested data supports it.
- Form selection **persists across refresh** and is shareable via URL.
- Fix the species-level evolution collapse so base pages show the correct trigger.
- Stay within the existing "forms are display-only enrichment" architecture: **no
  changes to Team Builder, Teams, RAG, or search**, which depend on default-form
  invariants.

## Non-goals (YAGNI)

- No version-heuristic dex entries for forms the data doesn't cover. Forms without
  their own flavor text (e.g. Galarian Darumaka) **hide** the Dex Entries panel
  rather than showing misleading species text.
- No per-form data for Mega / Primal / Gigantamax / battle-only forms beyond what
  the data has; those forms hide the Evolution / Moveset / Dex Entries panels when
  they have nothing form-specific.
- No runtime PokéAPI calls (all data pre-ingested — project invariant).
- No changes to `builder.legal_moves` / the team-builder moves path.

## Data reality (verified against the ingested CSVs)

| Piece | Available? | Source / notes |
|---|---|---|
| Per-form sprites | ✅ | `official-artwork/{pokemon_id}.png` downloaded for form ids (10176/10177/10178, 10229/10230, …) |
| Per-form evolution linkage | ✅ | `pokemon_evolution` rows carry `base_form_id` / `evolved_form_id` (e.g. 10176 → 10177, Ice Stone). These equal the form's `pokemon.id`, which equals `PokemonForm.id`. |
| Per-form learnset | ✅ (not yet ingested) | `pokemon_moves` has rows keyed by the form's `pokemon.id` (83 rows for Hisuian Growlithe 10229). Current ingest drops them (`if pid not in default_ids: continue`). |
| Per-form dex entries | ⚠️ partial | `pokemon_form_flavor_text` (keyed by `pokemon_forms.id`) covers ~63 forms (Megas, Deoxys, **Alolan** Gen-7 regionals). **Galarian/Hisuian Gen-8 regionals have none.** |

### Key id relationships

- The `pokemon` table holds **only default-form species** (58 Growlithe, 59
  Arcanine). Alternate forms (10229 Hisuian Growlithe) live only in
  `pokemon_forms`, with `PokemonForm.id == the form's pokemon.id`.
- Therefore form ids **cannot** be stored in FK columns that reference
  `pokemon.id` (`PokemonEvolution.from/to_pokemon_id`, `PokemonMove.pokemon_id`).
  All per-form data is denormalised onto `PokemonForm`, consistent with how
  `types` / `abilities` already live there as JSONB.
- `forms.py` already computes `form_id_by_pokemon` (form `pokemon.id` →
  `pokemon_forms.id`), the join key needed for `pokemon_form_flavor_text`.

## Design

### Component 1 — URL-persisted form selection (frontend)

- `frontend/app/pokedex/[dex]/page.tsx` and `PokemonDetailView` read the selected
  form from the URL query `?form=<form_id>` instead of local-only state.
- On switch, `router.replace(\`/pokedex/{dex}?form={id}\`)` (or drop the param for
  base). Reading initial state from `searchParams` makes it survive refresh and be
  shareable; browser back/forward works.
- Guard: a `?form` id not present in `data.forms` falls back to the base species.

**Depends on:** nothing new. **Interface:** URL query param.

### Component 2 — `PokemonForm` model + migration (backend)

Add nullable columns to `PokemonForm`:

- `evolves_from_form_id: int | None` — the pre-evolution form's `PokemonForm.id`.
- `evo_trigger: str | None`, `evo_min_level: int | None`, `evo_item: str | None`,
  `evo_condition: str | None` — the method **into** this form.
- `flavor_texts: list[str]` (JSONB, default `[]`) — form-specific dex entries.
- `learnset: list[dict]` (JSONB, default `[]`) — `[{move_id, method, level}]`,
  collapsed across version groups.

One Alembic autogenerate migration. `content_tsv` exclusion in `alembic/env.py`
is unaffected.

### Component 3 — Evolution ingest fix, made standalone (backend)

- Extract the evolution block from `run.py` into `app/ingest/evolutions.py` with a
  `main()` (host entry), and add `make evolutions`. It clears + repopulates
  `pokemon_evolutions`, so it is re-runnable without the destructive full ingest
  (avoids the chunks-FK gotcha).
- Fix the collapse: when choosing the **species** edge for an evolved species,
  select the `pokemon_evolution` row whose `evolved_form_id` is empty (the
  default-form path) rather than last-wins. Rows with `base_form_id` /
  `evolved_form_id` set are **not** species edges; they feed Component 4.

### Component 4 — Form enrichment in `forms.py` (backend)

Extend `ingest_forms` to also populate, per form:

- **Evolution linkage** from `pokemon_evolution` rows whose `evolved_form_id`
  equals this form's `pokemon.id`: set `evolves_from_form_id = base_form_id` and
  the `evo_*` fields (reusing the existing trigger/item/condition lookups).
- **`flavor_texts`** from `pokemon_form_flavor_text` joined via
  `form_id_by_pokemon` (English, de-duplicated, capped like species entries).
- **`learnset`** from `pokemon_moves` for the form's `pokemon.id`, collapsed with
  the same `_METHOD_RANK` / level logic the species learnset uses.

Remains standalone and idempotent (`make forms`), clearing/repopulating only the
forms subsystem.

### Component 5 — API surface (backend)

- `FormOut` (schema) gains `flavor_texts: list[str]`,
  `evolution_members: list[EvolutionMember]`, `evolution_stages: list[EvolutionStage]`.
- `pokemon_query._forms` builds a **self-contained** evolution chain per form: for
  the current species' `evolution_chain_id`, gather every `PokemonForm` whose base
  species is in that chain, link them via `evolves_from_form_id`, and emit
  `EvolutionMember`s (with form sprites) + `EvolutionStage`s (trigger labels).
  Forms not part of a ≥2-node chain get empty lists.
- **New display-only route** `GET /pokemon/forms/{form_id}/moves` returning
  `list[LearnsetMoveOut]` (the existing shape), served from `PokemonForm.learnset`
  joined to move details. A new `builder.legal_moves_for_form` (or a small service
  fn) backs it; `builder.legal_moves` and all teams code are untouched.

### Component 6 — Frontend rendering (frontend)

- `PokemonDetailView.view` extends to `evolution_members` / `evolution_stages` /
  `flavor_texts`, sourced from the selected form when active, else base data.
  - **Evolution** panel uses `form ? form.evolution_* : data.evolution_*` and
    `currentId = form ? form.id : data.id`; hidden when a form is selected and its
    chain has ≤1 node.
  - **Dex Entries** uses `form ? form.flavor_texts : data.flavor_texts`; hidden
    when a form is selected and it is empty.
- `MovesetPanel` accepts an optional `formId`; when set, calls the form moves
  endpoint and labels the panel for that form; hidden/empty when the form has no
  learnset.
- `EvolutionChain` needs no structural change (renders whatever members/stages it
  is given). `frontend/lib/types.ts` Form type and `frontend/lib/api.ts` gain the
  new fields and the form-moves fetch.

## Data flow (Hisuian Growlithe example)

1. User opens `/pokedex/58?form=10229` → `PokemonDetailView` sees `formId=10229`.
2. Detail API returns base Growlithe plus `forms[]`; the Hisuian form carries its
   Fire/Rock types, stats, abilities, `flavor_texts`, and a 2-node evolution chain
   (Hisuian Growlithe → Hisuian Arcanine, Fire Stone, Hisuian sprites).
3. Evolution + Dex Entries panels render the form's data. Moveset panel calls
   `/pokemon/forms/10229/moves` for the Hisuian learnset.
4. Refresh preserves `?form=10229`.

## Error handling & edge cases

- `?form` id absent from `data.forms` → base species (no crash).
- Form with empty `flavor_texts` / ≤1-node chain / empty `learnset` → the
  respective panel is hidden while that form is selected.
- Terminal forms (Mega/Gmax/battle-only) naturally fall into the hide paths.
- Species-level Evolution/Dex/Moveset behaviour for the **base** view is unchanged
  except the corrected species evolution trigger.

## Testing

Backend:
- Regression: an evolved species with a form-split method keeps its **default**
  trigger (Darmanitan species edge = Lv.35, not Ice Stone).
- Galarian Darumaka form payload: 2-node Ice-Stone chain, Galarian sprites, empty
  `flavor_texts` (panel hidden).
- Hisuian Growlithe: form learnset present and distinct from base; evolution chain
  is Hisuian → Hisuian.
- An Alolan form with `pokemon_form_flavor_text` exposes `flavor_texts`.
- New `/pokemon/forms/{id}/moves` returns the form learnset; `builder.legal_moves`
  output for the base species is unchanged.

Frontend (light): form switch swaps evolution/moveset/entries; empty-data panels
hide; `?form` round-trips through refresh.

## Rollout

```
make migrate      # new PokemonForm columns
make evolutions   # rebuild pokemon_evolutions (standalone, correct species edges)
make forms        # repopulate forms incl. flavor_texts / learnset / evo linkage
```

No destructive full `make ingest` required.

## Files touched (indicative)

- `backend/app/models/pokemon.py` — `PokemonForm` columns
- `backend/alembic/versions/*` — migration
- `backend/app/ingest/evolutions.py` (new) + `Makefile` target; `run.py` (extract/fix)
- `backend/app/ingest/forms.py` — flavor_texts / learnset / evo linkage
- `backend/app/schemas/pokemon.py` — `FormOut` fields
- `backend/app/services/pokemon_query.py` — `_forms` builds form evolution/flavor
- `backend/app/services/builder.py` — `legal_moves_for_form` (display-only)
- `backend/app/api/builder.py` (or a pokemon route) — `/pokemon/forms/{id}/moves`
- `frontend/app/pokedex/[dex]/page.tsx`, `frontend/components/PokemonDetailView.tsx`,
  `frontend/components/MovesetPanel.tsx`, `frontend/lib/types.ts`, `frontend/lib/api.ts`
- Tests under `backend/tests/`
