"""Ingest the type-effectiveness chart (PokéAPI type_efficacy.csv).

Standalone (does not touch the FK-referenced `pokemon` table) so it can be run
independently of the main ingest:

    cd backend
    DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex \\
        uv run python -m app.ingest.type_chart
"""

from __future__ import annotations

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingest.csv_source import read_csv
from app.models import TypeEffectiveness


def _sync_engine():
    return create_engine(get_settings().database_url.replace("+asyncpg", "+psycopg"))


def ingest() -> int:
    engine = _sync_engine()
    with Session(engine) as session:
        session.execute(delete(TypeEffectiveness))
        rows = []
        for row in read_csv("type_efficacy"):
            dmg = int(row["damage_type_id"])
            tgt = int(row["target_type_id"])
            if dmg >= 10000 or tgt >= 10000:
                continue
            rows.append(
                TypeEffectiveness(
                    damage_type_id=dmg,
                    target_type_id=tgt,
                    factor=int(row["damage_factor"]) / 100.0,
                )
            )
        session.add_all(rows)
        session.commit()
        return len(rows)


if __name__ == "__main__":
    n = ingest()
    print(f"Ingested {n} type-effectiveness rows.")
