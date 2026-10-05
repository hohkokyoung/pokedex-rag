"""Backfill ``moves.target`` without a full re-ingest.

Only issues UPDATEs, so it is safe against a populated DB (never touches
Pokémon, learnsets, chunks or saved teams). Run on the host against the Compose
DB:  ``uv run python -m app.ingest.backfill_move_targets``  (or ``make move-targets``).
"""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.ingest.run import _sync_engine, load_move_targets
from app.models import Move


def main() -> None:
    targets = load_move_targets()
    engine = _sync_engine()
    updated = 0
    with Session(engine) as session:
        for move_id, target in targets.items():
            result = session.execute(update(Move).where(Move.id == move_id).values(target=target))
            updated += result.rowcount or 0
        session.commit()
    print(f"Backfilled target on {updated} moves ({len(targets)} in source).")


if __name__ == "__main__":
    main()
