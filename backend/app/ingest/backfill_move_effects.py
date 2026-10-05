"""Backfill ``moves.short_effect`` without a full re-ingest.

The base ingest deletes and rebuilds the reference tables; this standalone
script only issues UPDATEs, so it is safe to run against a populated DB (it
never touches Pokémon, learnsets, or saved teams). Run on the host against the
Compose DB:  ``uv run python -m app.ingest.backfill_move_effects``.
"""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.ingest.run import _sync_engine, load_move_short_effects
from app.models import Move


def main() -> None:
    effects = load_move_short_effects()
    engine = _sync_engine()
    updated = 0
    with Session(engine) as session:
        for move_id, text in effects.items():
            result = session.execute(
                update(Move).where(Move.id == move_id).values(short_effect=text)
            )
            updated += result.rowcount or 0
        session.commit()
    print(f"Backfilled short_effect on {updated} moves ({len(effects)} in source).")


if __name__ == "__main__":
    main()
