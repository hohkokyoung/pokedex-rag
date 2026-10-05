"""Ingest items from the local PokéAPI CSVs into the ``items`` table.

Standalone and idempotent: items have no relationships, so this clears and
repopulates only the ``items`` table (safe to run without a full re-ingest).
Run on the host against the Compose DB:  ``uv run python -m app.ingest.items``.
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ingest.csv_source import read_csv, to_int
from app.ingest.run import _sync_engine
from app.models import Item

_EN = 9  # English local_language_id


def _english(table: str, id_field: str, value: str = "name") -> dict[int, str]:
    out: dict[int, str] = {}
    for row in read_csv(table):
        if to_int(row["local_language_id"]) != _EN:
            continue
        rid = to_int(row[id_field])
        if rid is not None and row.get(value):
            out[rid] = row[value]
    return out


def main() -> None:
    names = _english("item_names", "item_id")
    effects = _english("item_prose", "item_id", "short_effect")
    cat_ids = {to_int(r["id"]): r["identifier"] for r in read_csv("item_categories")}
    cat_names = _english("item_category_prose", "item_category_id")
    # Newest game's English bag text per item.
    flavor: dict[int, tuple[int, str]] = {}
    for row in read_csv("item_flavor_text"):
        if to_int(row["language_id"]) != _EN:
            continue
        iid, vg = to_int(row["item_id"]), to_int(row["version_group_id"]) or 0
        if iid is not None and (iid not in flavor or vg > flavor[iid][0]):
            text = " ".join(row["flavor_text"].replace("\u00ad", "").split())
            flavor[iid] = (vg, text)

    rows: list[dict] = []
    for row in read_csv("items"):
        iid = to_int(row["id"])
        if iid is None:
            continue
        cat_id = to_int(row["category_id"])
        fallback = (cat_ids.get(cat_id) or "").replace("-", " ").title()
        category = cat_names.get(cat_id) or fallback or None
        rows.append(
            {
                "id": iid,
                "identifier": row["identifier"],
                "name": names.get(iid, row["identifier"].replace("-", " ").title()),
                "category": category,
                "cost": to_int(row["cost"]),
                "short_effect": (effects.get(iid) or None),
                "flavor_text": flavor[iid][1] if iid in flavor else None,
                "fling_power": to_int(row["fling_power"]),
            }
        )

    engine = _sync_engine()
    with Session(engine) as session:
        session.execute(delete(Item))
        if rows:
            session.execute(Item.__table__.insert(), rows)
        session.commit()
    print(f"Ingested {len(rows)} items.")


if __name__ == "__main__":
    main()
