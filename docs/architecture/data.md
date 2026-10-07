# Data model

What lives in Postgres, who writes it, and the rules the rest of the code relies on.
Columns are in the ORM (`backend/app/models/`); this page is the map.

## Two kinds of data

| Kind | Written by | Tables |
|---|---|---|
| **Reference** — the Pokédex | the offline pipeline only ([data-pipeline.md](../guides/data-pipeline.md)); read-only at runtime | everything below except *User* |
| **User** — your stuff | the API at runtime | `teams`, `team_members`, `user_profile`, `user_favorites`, `question_log` |

Reference data is rebuilt from the PokéAPI CSVs; user data is not, so a re-ingest must
never truncate it.

## Reference data

```
generations ◄── pokemon ──► pokemon_types ──► types ◄── type_effectiveness (attacker × defender)
                   │  └───► pokemon_abilities ──► abilities
                   │
                   ├── pokemon_forms          (alternate forms, display-only)
                   ├── pokemon_evolutions     (from → to edges)
                   ├── pokemon_flavor_texts   (one dex entry per game)
                   ├── pokemon_moves ──► moves ◄── move_machines (TM per version group)
                   ├── pokemon_move_learns    (per game: version group × move × method)
                   ├── pokemon_encounters     (per game, pre-aggregated)
                   └── knowledge_chunks       (text + embedding for search)

items · natures · version_groups   (lookups)
```

| Group | Tables | Notes |
|---|---|---|
| Species | `pokemon`, `generations`, `types`, `pokemon_types`, `abilities`, `pokemon_abilities` | base stats are columns (plus `base_stat_total`) so ranking and threshold queries are plain SQL |
| Forms | `pokemon_forms` | regional, Mega, Primal, Gigantamax, battle forms; PokéAPI ids > 10000. Types, abilities, learnset and dex entries are denormalised JSONB |
| Lore | `pokemon_flavor_texts`, `pokemon_evolutions` | |
| Moves | `moves`, `pokemon_moves`, `pokemon_move_learns`, `move_machines`, `version_groups` | `pokemon_moves` is "can it ever learn it" (one row per pair); `pokemon_move_learns` is the game-aware answer |
| Matchups | `type_effectiveness` | the type chart, read through `services/matchups.py` |
| Battle items | `items`, `natures` | |
| Where to find | `pokemon_encounters` | encounter slots folded into one row per place × method × conditions; names denormalised. Data ends at Sword/Shield |
| Search | `knowledge_chunks` | profile and dex-entry chunks with a 384-d embedding and a DB-managed `content_tsv` — see [retrieval.md](retrieval.md#text-retrieval-lore-and-look-alikes) |

## User data

| Table | Holds |
|---|---|
| `teams` | a player team or a saved opponent (`kind`), plus the cached AI summary and its roster fingerprint (`summary_key`) — [team-coach.md](team-coach.md#the-ai-summary) |
| `team_members` | one row per slot (1–6, unique per team): species, optional form, ability, item, nature, EV/IV spreads, move ids |
| `user_profile`, `user_favorites` | preferred types and favourite Pokémon, used by personalised Ask picks |
| `question_log` | every asked question, plus a plan trace on the newest `TRACE_RETENTION` rows — [ask-agent-traces.md](ask-agent-traces.md) |

## Invariants

- **`pokemon.id` is the national dex number.** Only default forms are in `pokemon`
  (1–1025); everything keyed by `pokemon_id` means a species.
- **Forms are isolated.** They aren't rows in `pokemon`, so search, rankings and
  most FKs ignore them. Code that supports forms reads `pokemon_forms` explicitly;
  `pokemon_move_learns`, `pokemon_encounters` and `team_members.form_id` accept form
  ids, which is why those columns have no FK.
- **Rules live in code, not constraints.** Slot legality (EV caps, IV bounds, ≤ 4
  moves, moves in the learnset, ability belongs to the species) is enforced by
  `services/teams.py`; the DB stores spreads and moves loosely as JSONB.
- **`knowledge_chunks` depends on `pokemon`.** Its FK is why a full `make ingest`
  fails on a populated DB; change data with the standalone targets.
- **Never let Alembic drop `content_tsv`.** It's excluded via `include_object` in
  `alembic/env.py`.
