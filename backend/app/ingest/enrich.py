"""Enrich ingested Pokémon with training & breeding info (ticket T-001).

Adds gender ratio, egg groups, egg cycles, growth rate and EV yield — all from
the PokéAPI CSVs. UPDATE-only (keyed by id), so it never touches the FK-referenced
pokemon rows and can run independently of the main ingest:

    cd backend
    DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex \\
        uv run python -m app.ingest.enrich
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingest.csv_source import read_csv, to_int
from app.models import Pokemon

STAT_COLUMN = {1: "hp", 2: "attack", 3: "defense", 4: "sp_attack", 5: "sp_defense", 6: "speed"}

GROWTH_RATE = {
    "slow": "Slow",
    "medium": "Medium Fast",
    "fast": "Fast",
    "medium-slow": "Medium Slow",
    "slow-then-very-fast": "Erratic",
    "fast-then-very-slow": "Fluctuating",
}

EGG_GROUP = {
    "monster": "Monster", "water1": "Water 1", "water2": "Water 2", "water3": "Water 3",
    "bug": "Bug", "flying": "Flying", "ground": "Field", "fairy": "Fairy",
    "plant": "Grass", "humanshape": "Human-Like", "mineral": "Mineral",
    "indeterminate": "Amorphous", "ditto": "Ditto", "dragon": "Dragon",
    "no-eggs": "No Eggs Discovered",
}


def _sync_engine():
    return create_engine(get_settings().database_url.replace("+asyncpg", "+psycopg"))


def enrich() -> int:
    growth = {
        int(r["id"]): GROWTH_RATE.get(r["identifier"], r["identifier"])
        for r in read_csv("growth_rates")
    }
    egg = {
        int(r["id"]): EGG_GROUP.get(r["identifier"], r["identifier"].title())
        for r in read_csv("egg_groups")
    }

    egg_by_species: dict[int, list[str]] = defaultdict(list)
    for row in read_csv("pokemon_egg_groups"):
        name = egg.get(int(row["egg_group_id"]))
        if name:
            egg_by_species[int(row["species_id"])].append(name)

    ev_by_pokemon: dict[int, dict[str, int]] = defaultdict(dict)
    for row in read_csv("pokemon_stats"):
        effort = to_int(row["effort"]) or 0
        if effort <= 0:
            continue
        col = STAT_COLUMN.get(int(row["stat_id"]))
        if col:
            ev_by_pokemon[int(row["pokemon_id"])][col] = effort

    updates: list[dict] = []
    for row in read_csv("pokemon_species"):
        sid = int(row["id"])
        if sid > 10000:
            continue
        updates.append(
            {
                "id": sid,  # default-form pokemon.id == species id
                "gender_rate": to_int(row.get("gender_rate")),
                "hatch_counter": to_int(row.get("hatch_counter")),
                "growth_rate": growth.get(to_int(row.get("growth_rate_id")) or -1),
                "egg_groups": egg_by_species.get(sid) or None,
                "ev_yield": ev_by_pokemon.get(sid) or None,
            }
        )

    engine = _sync_engine()
    with Session(engine) as session:
        # bulk UPDATE keyed by primary key
        session.execute(update(Pokemon), updates)
        session.commit()
    return len(updates)


if __name__ == "__main__":
    n = enrich()
    print(f"Enriched {n} Pokémon with training & breeding info.")
