# Pokédex (`/pokedex`, `/pokedex/[dex]`)

## Catalog — `/pokedex`

All 1,025 species as cards, loading more as you scroll.

- **Search** by name or dex number.
- **Filter** by type (any number), generation (several at once) and **Legendary**.
- **Sort** by dex number, name, base stat total, HP, Attack, Defense or Speed,
  ascending or descending.

A summary line shows the active filters and the match count.

## Detail — `/pokedex/[dex]`

One Pokémon, e.g. `/pokedex/445` for Garchomp. Previous/next arrows move through the
dex; a form switcher (Base / Mega / regional…) appears when the species has forms.
The first type sets the page's accent colour.

| Section | Shows |
|---|---|
| Header | dex number, generation, name, category, types, artwork, a dex entry, and the ♡ **favourite** button (feeds "for you" picks in Ask) |
| Facts | height, weight, habitat, capture rate, base experience, colour |
| Abilities | regular and hidden abilities with effects; "Show all" lists every Pokémon with that ability |
| Base stats | the six stats as bars, plus the total |
| Type matchups | takes more from (×4/×2), resists, immune to, and what its types hit ×2 |
| Training & breeding | gender ratio, egg groups, egg cycles, growth rate, EV yield, base friendship |
| Moveset | level-up, TM/HM, tutor and other moves, filterable by category, game and type; any move opens who else learns it, per game |
| Evolution | the chain with levels/conditions |
| Dex entries | every game's entry, grouped by generation |
| Where to find | encounter locations per game: wild areas (method, level, rate, conditions) and raid dens. Data ends at Sword/Shield |

## Code

Files: [pokedex manifest](../components/pokedex.yaml). Catalog and detail page are
served by `services/pokemon_query.py`; movesets and learners by `services/builder.py`.

The catalog's filters are **not** the Ask filters: Ask's "Gen 4 Fire types" goes through
`rag/sql_retrieval.py` ([retrieval.md](../architecture/retrieval.md)). A bug on this page
lives in `services/pokemon_query.py`.
