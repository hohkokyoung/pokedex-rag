"""Rebuild ``pokemon_flavor_texts`` (one dex entry per game) without a full re-ingest.

Replaces only that table (and refreshes ``pokemon.flavor_text``), so it is safe to
run against a populated DB — Pokémon, learnsets, chunks and saved teams are left
alone. Run on the host against the Compose DB:
``uv run python -m app.ingest.backfill_flavor_texts``.
"""

from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.ingest.run import _sync_engine, load_species_flavor
from app.models import Pokemon, PokemonFlavorText


def main() -> None:
    engine = _sync_engine()
    with Session(engine) as session:
        ids = set(session.execute(select(Pokemon.id)).scalars())
        flavor = load_species_flavor(ids)
        session.execute(delete(PokemonFlavorText))
        rows = [
            PokemonFlavorText(pokemon_id=pid, version=version, flavor_text=text)
            for pid, entries in flavor.items()
            for version, text in entries
        ]
        session.add_all(rows)
        for pid, entries in flavor.items():
            session.execute(
                update(Pokemon).where(Pokemon.id == pid).values(flavor_text=entries[-1][1])
            )
        session.commit()
    print(f"Rebuilt {len(rows)} dex entries for {len(flavor)} species.")


if __name__ == "__main__":
    main()
