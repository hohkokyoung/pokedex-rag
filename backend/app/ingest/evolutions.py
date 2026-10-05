"""Standalone, idempotent (re)build of the ``pokemon_evolutions`` table.

Split out of the destructive full ingest so it can be re-run on the host against
the Compose DB without touching chunks/embeddings:  ``make evolutions``.

Fixes the species-edge collapse: a species with a form-dependent method (e.g.
Darmanitan: Lv.35 Unovan vs Ice Stone Galarian) keeps its DEFAULT-form method as
the species edge. Rows carrying ``evolved_form_id`` (alternate-form paths) are
NOT species edges here — they feed the forms ingest instead.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ingest.csv_source import read_csv, to_int
from app.ingest.run import _english_names, _evolution_condition, _lookup, _sync_engine
from app.models import Pokemon, PokemonEvolution


def _species_evo_detail() -> dict[int, dict[str, str]]:
    """evolved_species_id -> the DEFAULT-form evolution row (empty evolved_form_id).

    Falls back to the first row seen if a species has no default-form row."""
    out: dict[int, dict[str, str]] = {}
    for row in read_csv("pokemon_evolution"):
        sid = to_int(row["evolved_species_id"])
        if sid is None:
            continue
        is_default_path = not (row.get("evolved_form_id") or "").strip()
        if sid not in out or (is_default_path and (out[sid].get("evolved_form_id") or "").strip()):
            out[sid] = row
    return out


def ingest_evolutions(session: Session, default_ids: set[int]) -> int:
    triggers = _lookup("evolution_triggers")
    item_names = _english_names("item_names", "item_id")
    species_names = _english_names("pokemon_species_names", "pokemon_species_id")
    move_names = _english_names("move_names", "move_id")
    type_names = _english_names("type_names", "type_id")
    location_names = _english_names("location_names", "location_id")
    species = {int(r["id"]): r for r in read_csv("pokemon_species")}
    evo_detail = _species_evo_detail()

    rows: list[PokemonEvolution] = []
    for pid in sorted(default_ids):
        sp = species.get(pid, {})
        parent = to_int(sp.get("evolves_from_species_id"))
        if not parent:
            continue
        detail = evo_detail.get(pid, {})
        rows.append(
            PokemonEvolution(
                evolution_chain_id=to_int(sp.get("evolution_chain_id")) or 0,
                from_pokemon_id=parent if parent in default_ids else None,
                to_pokemon_id=pid,
                trigger=triggers.get(to_int(detail.get("evolution_trigger_id")) or -1),
                min_level=to_int(detail.get("minimum_level")),
                item=item_names.get(to_int(detail.get("trigger_item_id")) or -1, {}).get("name"),
                condition=_evolution_condition(
                    detail,
                    item_names,
                    species_names=species_names,
                    move_names=move_names,
                    type_names=type_names,
                    location_names=location_names,
                ),
            )
        )
    session.execute(delete(PokemonEvolution))
    session.add_all(rows)
    return len(rows)


def main() -> None:
    engine = _sync_engine()
    with Session(engine) as session:
        default_ids = {pid for (pid,) in session.execute(select(Pokemon.id)).all()}
        n = ingest_evolutions(session, default_ids)
        session.commit()
    print(f"Ingested {n} evolution edges.")


if __name__ == "__main__":
    main()
