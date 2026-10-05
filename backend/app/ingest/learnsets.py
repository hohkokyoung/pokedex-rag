"""Ingest per-game learnsets from the local PokéAPI CSVs.

Fills ``version_groups``, ``move_machines`` and ``pokemon_move_learns`` — the
uncollapsed learnset (one row per Pokémon × game × move × method, with level) that
backs "who learns this move, how, in which game". The collapsed ``pokemon_moves``
table used by the team builder and RAG is left untouched.

Standalone and idempotent: it only needs ``pokemon``, ``pokemon_forms`` and
``moves`` to exist, and clears/reloads just its own three tables.
Run on the host against the Compose DB:  ``uv run python -m app.ingest.learnsets``.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ingest.csv_source import read_csv, to_int
from app.ingest.run import _sync_engine
from app.models import Move, MoveMachine, Pokemon, PokemonForm, PokemonMoveLearn, VersionGroup

_EN = 9  # English local_language_id

# Spin-offs, Japan-only duplicates of Red/Blue, and games without normal learnsets.
_SKIP_VERSION_GROUPS = {"colosseum", "xd", "red-green-japan", "blue-japan", "champions"}
# Battle-only transformations share their base species' learnset; listing them
# separately would only duplicate the base row.
_SKIP_FORM_CATEGORIES = {"mega", "primal", "gigantamax"}
# Names too long for a picker row.
_NAME_OVERRIDES = {"lets-go-pikachu-lets-go-eevee": "Let’s Go, Pikachu / Eevee"}


def version_group_names() -> dict[int, str]:
    """English display name per version group, e.g. ``"Scarlet / Violet"``."""
    version_vg = {int(r["id"]): int(r["version_group_id"]) for r in read_csv("versions")}
    names: dict[int, list[str]] = {}
    for r in read_csv("version_names"):
        if to_int(r["local_language_id"]) != _EN:
            continue
        vg = version_vg.get(int(r["version_id"]))
        if vg is not None:
            names.setdefault(vg, []).append(r["name"])
    return {vg: " / ".join(ns) for vg, ns in names.items()}


def main() -> None:
    engine = _sync_engine()
    with Session(engine) as session:
        default_ids = set(session.execute(select(Pokemon.id)).scalars())
        form_ids = set(
            session.execute(
                select(PokemonForm.id).where(PokemonForm.category.notin_(_SKIP_FORM_CATEGORIES))
            ).scalars()
        )
        move_ids = set(session.execute(select(Move.id)).scalars())
        wanted = default_ids | form_ids

        vg_names = version_group_names()
        vgs = {
            int(r["id"]): r
            for r in read_csv("version_groups")
            if r["identifier"] not in _SKIP_VERSION_GROUPS
        }
        methods = {int(r["id"]): r["identifier"] for r in read_csv("pokemon_move_methods")}

        # (pokemon, vg, move, method) -> lowest level seen (duplicates exist per level).
        learns: dict[tuple[int, int, int, str], int | None] = {}
        for r in read_csv("pokemon_moves"):
            pid, vg, mid = int(r["pokemon_id"]), int(r["version_group_id"]), int(r["move_id"])
            if pid not in wanted or vg not in vgs or mid not in move_ids:
                continue
            method = methods.get(to_int(r["pokemon_move_method_id"]) or -1)
            if not method:
                continue
            level = to_int(r["level"]) if method == "level-up" else None
            key = (pid, vg, mid, method)
            cur = learns.get(key, -1)
            if cur == -1 or (level is not None and (cur is None or level < cur)):
                learns[key] = level
        used_vgs = {vg for _pid, vg, _mid, _m in learns}

        item_ident = {int(r["id"]): r["identifier"] for r in read_csv("items")}
        machines = {
            (int(r["version_group_id"]), int(r["move_id"])): item_ident.get(
                int(r["item_id"]), ""
            ).upper()
            for r in read_csv("machines")
            if int(r["version_group_id"]) in used_vgs and int(r["move_id"]) in move_ids
        }

        vg_rows = [
            {
                "id": vg,
                "identifier": r["identifier"],
                "name": _NAME_OVERRIDES.get(r["identifier"])
                or vg_names.get(vg, r["identifier"].replace("-", " ").title()),
                "generation": int(r["generation_id"]),
                "sort_order": int(r["order"]),
            }
            for vg, r in vgs.items()
            if vg in used_vgs
        ]
        machine_rows = [
            {"version_group_id": vg, "move_id": mid, "label": label}
            for (vg, mid), label in machines.items()
            if label
        ]
        learn_rows = [
            {
                "pokemon_id": pid,
                "version_group_id": vg,
                "move_id": mid,
                "learn_method": m,
                "level": lv,
            }
            for (pid, vg, mid, m), lv in learns.items()
        ]

        session.execute(delete(PokemonMoveLearn))
        session.execute(delete(MoveMachine))
        session.execute(delete(VersionGroup))
        session.execute(VersionGroup.__table__.insert(), vg_rows)
        if machine_rows:
            session.execute(MoveMachine.__table__.insert(), machine_rows)
        for i in range(0, len(learn_rows), 50_000):
            session.execute(PokemonMoveLearn.__table__.insert(), learn_rows[i : i + 50_000])
        session.commit()
    print(
        f"Ingested {len(vg_rows)} games, {len(machine_rows)} machines, "
        f"{len(learn_rows)} per-game learnset rows."
    )


if __name__ == "__main__":
    main()
