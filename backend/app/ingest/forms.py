"""Ingest alternate Pokémon forms (regional, Mega, Primal, Gigantamax, battle).

These are the ``is_default = 0`` rows PokéAPI keeps as separate ``pokemon`` records
for a species. They are a *display-only* enrichment on the parent's detail page, so
types/abilities are denormalised into JSONB on ``pokemon_forms`` rather than reusing
the default-form relational tables.

Standalone and idempotent: clears and repopulates only the ``pokemon_forms`` table,
so it is safe to run without a full (destructive) re-ingest. Run on the host against
the Compose DB:  ``uv run python -m app.ingest.forms``.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ingest.csv_source import read_csv, to_int
from app.ingest.run import _evolution_condition, _sync_engine
from app.models import Pokemon, PokemonForm, Type

_EN = 9  # English local_language_id
_STAT_COLUMN = {1: "hp", 2: "attack", 3: "defense", 4: "sp_attack", 5: "sp_defense", 6: "speed"}
_REGIONAL_FORMS = ("alola", "galar", "hisui", "paldea")


def _english_names(table: str, id_field: str) -> dict[int, dict[str, str]]:
    out: dict[int, dict[str, str]] = {}
    for row in read_csv(table):
        if to_int(row["local_language_id"]) != _EN:
            continue
        rid = to_int(row[id_field])
        if rid is not None:
            out[rid] = row
    return out


def _lookup_local(table: str) -> dict[int, str]:
    return {int(r["id"]): r["identifier"] for r in read_csv(table)}


def _form_category(form_identifier: str, is_mega: bool, is_battle_only: bool) -> str:
    fid = (form_identifier or "").lower()
    if is_mega:
        return "mega"
    if "primal" in fid:
        return "primal"
    if "gmax" in fid or "gigantamax" in fid:
        return "gigantamax"
    if any(fid == r or fid.startswith(r) for r in _REGIONAL_FORMS):
        return "regional"
    if is_battle_only:
        return "battle"
    return "other"


def ingest_forms(
    session: Session, default_ids: set[int], valid_type_ids: set[int]
) -> dict[str, int]:
    """Populate ``pokemon_forms`` for the given default species. Clears the table first."""
    type_ident = {
        int(r["id"]): r["identifier"]
        for r in read_csv("types")
        if int(r["id"]) in valid_type_ids
    }
    ability_names = _english_names("ability_names", "ability_id")
    ability_ident = {
        int(r["id"]): r["identifier"] for r in read_csv("abilities") if int(r["id"]) < 10000
    }

    # form pokemon rows (is_default = 0) whose base species we carry
    form_pokemon: dict[int, dict[str, str]] = {}
    for row in read_csv("pokemon"):
        if row["is_default"] == "1":
            continue
        pid = int(row["id"])
        if pid <= 10000 or int(row["species_id"]) not in default_ids:
            continue
        form_pokemon[pid] = row

    # form metadata (name label + flags) keyed by the form's pokemon_id
    form_meta: dict[int, dict[str, str]] = {}
    form_id_by_pokemon: dict[int, int] = {}
    for row in read_csv("pokemon_forms"):
        pk = to_int(row["pokemon_id"])
        if pk in form_pokemon:
            form_meta[pk] = row
            form_id_by_pokemon[pk] = int(row["id"])

    # English display names keyed by pokemon_form id
    form_names = _english_names("pokemon_form_names", "pokemon_form_id")

    # stats / types / abilities for the form pokemon ids
    form_stats: dict[int, dict[str, int]] = defaultdict(dict)
    for row in read_csv("pokemon_stats"):
        pid = int(row["pokemon_id"])
        if pid in form_pokemon:
            col = _STAT_COLUMN.get(int(row["stat_id"]))
            if col:
                form_stats[pid][col] = int(row["base_stat"])

    form_types: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for row in read_csv("pokemon_types"):
        pid = int(row["pokemon_id"])
        tid = int(row["type_id"])
        if pid in form_pokemon and tid in type_ident:
            form_types[pid].append((int(row["slot"]), type_ident[tid]))

    form_abilities: dict[int, list[tuple[int, dict]]] = defaultdict(list)
    for row in read_csv("pokemon_abilities"):
        pid = int(row["pokemon_id"])
        aid = int(row["ability_id"])
        if pid in form_pokemon and aid in ability_ident:
            form_abilities[pid].append(
                (
                    int(row["slot"]),
                    {
                        "name": ability_names.get(aid, {}).get("name", ability_ident[aid]),
                        "identifier": ability_ident[aid],
                        "is_hidden": row["is_hidden"] == "1",
                    },
                )
            )

    # --- per-form flavor text (keyed by pokemon_forms.id via form_id_by_pokemon) ---
    form_flavor: dict[int, list[str]] = defaultdict(list)
    seen_flavor: dict[int, set[str]] = defaultdict(set)
    form_pk_by_formid = {fid: pk for pk, fid in form_id_by_pokemon.items()}
    for row in read_csv("pokemon_form_flavor_text"):
        if to_int(row["language_id"]) != _EN:
            continue
        fid = to_int(row["pokemon_form_id"])
        pk = form_pk_by_formid.get(fid)
        if pk is None:
            continue
        text = " ".join((row["flavor_text"] or "").split())
        if text and text not in seen_flavor[pk]:
            seen_flavor[pk].add(text)
            form_flavor[pk].append(text)

    # --- per-form learnset (collapsed across version groups) ---
    from app.ingest.run import _METHOD_RANK

    methods = _lookup_local("pokemon_move_methods")
    best: dict[tuple[int, int], tuple[int, str | None, int | None]] = {}
    for row in read_csv("pokemon_moves"):
        pid = int(row["pokemon_id"])
        if pid not in form_pokemon:
            continue
        mid = int(row["move_id"])
        method = methods.get(to_int(row["pokemon_move_method_id"]) or -1)
        level = to_int(row["level"])
        rank = _METHOD_RANK.get(method or "", 9)
        key = (pid, mid)
        cur = best.get(key)
        if cur is None or rank < cur[0] or (
            rank == cur[0] and method == "level-up" and level
            and (cur[2] is None or level < cur[2])
        ):
            best[key] = (rank, method, level)
    form_learnset: dict[int, list[dict]] = defaultdict(list)
    for (pid, mid), (_rank, method, level) in best.items():
        form_learnset[pid].append(
            {"move_id": mid, "method": method, "level": level if method == "level-up" else None}
        )

    # --- per-form evolution linkage (rows carrying evolved_form_id) ---
    triggers = _lookup_local("evolution_triggers")
    item_names = _english_names("item_names", "item_id")
    form_evo: dict[int, dict] = {}
    for row in read_csv("pokemon_evolution"):
        evolved_form = to_int(row.get("evolved_form_id"))
        base_form = to_int(row.get("base_form_id"))
        if evolved_form in form_pokemon and base_form is not None:
            form_evo[evolved_form] = {
                "from": base_form,
                "trigger": triggers.get(to_int(row.get("evolution_trigger_id")) or -1),
                "min_level": to_int(row.get("minimum_level")),
                "item": item_names.get(to_int(row.get("trigger_item_id")) or -1, {}).get("name"),
                "condition": _evolution_condition(row, item_names),
            }

    rows: list[PokemonForm] = []
    for pid, base in sorted(form_pokemon.items()):
        meta = form_meta.get(pid, {})
        fid = form_id_by_pokemon.get(pid)
        names = form_names.get(fid, {}) if fid is not None else {}
        form_identifier = meta.get("form_identifier") or ""
        is_mega = meta.get("is_mega") == "1"
        is_battle_only = meta.get("is_battle_only") == "1"
        category = _form_category(form_identifier, is_mega, is_battle_only)

        # Prefer the full form label ("Alolan Meowth", "Mega Charizard X"); fall back
        # to the partial form name, then a humanised identifier.
        fallback_label = (
            form_identifier.replace("-", " ").title() if form_identifier else base["identifier"]
        )
        label = (
            names.get("pokemon_name") or names.get("form_name") or fallback_label
        ).strip()

        st = form_stats.get(pid, {})
        bst = sum(st.get(c, 0) for c in _STAT_COLUMN.values())
        types = [ident for _slot, ident in sorted(form_types.get(pid, []))]
        abilities = [ab for _slot, ab in sorted(form_abilities.get(pid, []), key=lambda x: x[0])]

        rows.append(
            PokemonForm(
                id=pid,
                base_pokemon_id=int(base["species_id"]),
                name=label,
                form_identifier=form_identifier or None,
                category=category,
                is_mega=is_mega,
                is_gigantamax=category == "gigantamax",
                is_battle_only=is_battle_only,
                types=types,
                abilities=abilities,
                height_m=(to_int(base.get("height")) or 0) / 10 or None,
                weight_kg=(to_int(base.get("weight")) or 0) / 10 or None,
                hp=st.get("hp", 0),
                attack=st.get("attack", 0),
                defense=st.get("defense", 0),
                sp_attack=st.get("sp_attack", 0),
                sp_defense=st.get("sp_defense", 0),
                speed=st.get("speed", 0),
                base_stat_total=bst,
                sprite_path=f"official-artwork/{pid}.png",
                sort_order=to_int(meta.get("order")) or pid,
                flavor_texts=form_flavor.get(pid, []),
                learnset=form_learnset.get(pid, []),
                evolves_from_form_id=form_evo.get(pid, {}).get("from"),
                evo_trigger=form_evo.get(pid, {}).get("trigger"),
                evo_min_level=form_evo.get(pid, {}).get("min_level"),
                evo_item=form_evo.get(pid, {}).get("item"),
                evo_condition=form_evo.get(pid, {}).get("condition"),
            )
        )

    session.execute(delete(PokemonForm))
    session.add_all(rows)
    return {"pokemon_forms": len(rows)}


def main() -> None:
    engine = _sync_engine()
    with Session(engine) as session:
        default_ids = {pid for (pid,) in session.execute(select(Pokemon.id)).all()}
        valid_type_ids = {tid for (tid,) in session.execute(select(Type.id)).all()}
        counts = ingest_forms(session, default_ids, valid_type_ids)
        session.commit()
    print(f"Ingested {counts['pokemon_forms']} alternate forms.")


if __name__ == "__main__":
    main()
