"""Ingest the PokéAPI CSV dataset into PostgreSQL.

Idempotent: existing rows in the target tables are cleared first, then repopulated.
Only *default-form* Pokémon (national dex 1-1025) are ingested; for these,
``pokemon.id == species_id == national dex number``.

Run (against the Compose DB on host port 5433):

    cd backend
    DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex \\
        uv run python -m app.ingest.run
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingest.csv_source import (
    ENGLISH_LANGUAGE_ID,
    clean_flavor_text,
    read_csv,
    to_int,
)
from app.models import (
    Ability,
    Generation,
    Move,
    Nature,
    Pokemon,
    PokemonAbility,
    PokemonEvolution,
    PokemonFlavorText,
    PokemonForm,
    PokemonMove,
    PokemonType,
    Type,
)

STAT_COLUMN = {1: "hp", 2: "attack", 3: "defense", 4: "sp_attack", 5: "sp_defense", 6: "speed"}

# Preference order when collapsing a learnset across version groups to one row
# per (pokemon, move): lower rank wins.
_METHOD_RANK = {"level-up": 0, "machine": 1, "tutor": 2, "egg": 3, "form-change": 4}


def _sync_engine():
    url = get_settings().database_url.replace("+asyncpg", "+psycopg")
    return create_engine(url)


def _lookup(name: str, key: str = "id", value: str = "identifier") -> dict[int, str]:
    """Build an ``id -> identifier`` map from a reference CSV."""
    return {int(row[key]): row[value] for row in read_csv(name)}


def _english_names(name: str, id_field: str) -> dict[int, dict[str, str]]:
    """Map ``entity id -> {"name":..., ...}`` for English rows only."""
    out: dict[int, dict[str, str]] = {}
    for row in read_csv(name):
        if int(row["local_language_id"]) != ENGLISH_LANGUAGE_ID:
            continue
        out[int(row[id_field])] = row
    return out


def ingest() -> dict[str, int]:
    engine = _sync_engine()
    counts: dict[str, int] = {}

    with Session(engine) as session:
        # --- clear existing data (children first) ---
        for model in (
            PokemonMove,
            PokemonForm,
            PokemonEvolution,
            PokemonFlavorText,
            PokemonAbility,
            PokemonType,
            Pokemon,
            Move,
            Nature,
            Ability,
            Type,
            Generation,
        ):
            session.execute(delete(model))
        session.commit()

        # --- generations ---
        gen_names = _english_names("generation_names", "generation_id")
        generations = []
        for row in read_csv("generations"):
            gid = int(row["id"])
            generations.append(
                Generation(
                    id=gid,
                    identifier=row["identifier"],
                    name=gen_names.get(gid, {}).get("name", row["identifier"]),
                )
            )
        session.add_all(generations)
        counts["generations"] = len(generations)

        # --- types ---
        type_names = _english_names("type_names", "type_id")
        types = []
        for row in read_csv("types"):
            tid = int(row["id"])
            if tid >= 10000:  # skip shadow/unknown meta-types
                continue
            types.append(
                Type(
                    id=tid,
                    identifier=row["identifier"],
                    name=type_names.get(tid, {}).get("name", row["identifier"]),
                )
            )
        session.add_all(types)
        counts["types"] = len(types)
        valid_type_ids = {t.id for t in types}

        # --- abilities (+ English effect from latest flavour text) ---
        ability_names = _english_names("ability_names", "ability_id")
        ability_effect: dict[int, tuple[int, str]] = {}
        for row in read_csv("ability_flavor_text"):
            if int(row["language_id"]) != ENGLISH_LANGUAGE_ID:
                continue
            aid = int(row["ability_id"])
            vg = int(row["version_group_id"])
            if aid not in ability_effect or vg > ability_effect[aid][0]:
                ability_effect[aid] = (vg, clean_flavor_text(row["flavor_text"]))
        abilities = []
        for row in read_csv("abilities"):
            aid = int(row["id"])
            if aid >= 10000:
                continue
            abilities.append(
                Ability(
                    id=aid,
                    identifier=row["identifier"],
                    name=ability_names.get(aid, {}).get("name", row["identifier"]),
                    effect=ability_effect.get(aid, (0, None))[1],
                )
            )
        session.add_all(abilities)
        counts["abilities"] = len(abilities)
        valid_ability_ids = {a.id for a in abilities}
        session.commit()

        # --- reference lookups for species descriptors ---
        colors = _lookup("pokemon_colors")
        shapes = _lookup("pokemon_shapes")
        habitats = _lookup("pokemon_habitats")

        # species-level attributes
        species: dict[int, dict[str, str]] = {int(r["id"]): r for r in read_csv("pokemon_species")}
        species_names = _english_names("pokemon_species_names", "pokemon_species_id")

        # default-form pokemon (national dex 1-1025)
        default_ids: set[int] = set()
        pokemon_base: dict[int, dict[str, str]] = {}
        for row in read_csv("pokemon"):
            if row["is_default"] != "1" or int(row["id"]) > 10000:
                continue
            pid = int(row["id"])
            default_ids.add(pid)
            pokemon_base[pid] = row

        # stats per pokemon
        stats: dict[int, dict[str, int]] = defaultdict(dict)
        for row in read_csv("pokemon_stats"):
            pid = int(row["pokemon_id"])
            if pid not in default_ids:
                continue
            col = STAT_COLUMN.get(int(row["stat_id"]))
            if col:
                stats[pid][col] = int(row["base_stat"])

        # English flavour texts per pokemon (deduped by text; version label from latest)
        version_id_to_name: dict[int, str] = {}
        for row in read_csv("version_names"):
            if int(row["local_language_id"]) == ENGLISH_LANGUAGE_ID:
                version_id_to_name[int(row["version_id"])] = row["name"]

        flavor_by_pokemon: dict[int, dict[str, tuple[int, str]]] = defaultdict(dict)
        for row in read_csv("pokemon_species_flavor_text"):
            if int(row["language_id"]) != ENGLISH_LANGUAGE_ID:
                continue
            sid = int(row["species_id"])
            if sid not in default_ids:
                continue
            text = clean_flavor_text(row["flavor_text"])
            if not text:
                continue
            vid = int(row["version_id"])
            # keep one entry per distinct text, remembering the newest version id
            existing = flavor_by_pokemon[sid].get(text)
            if existing is None or vid > existing[0]:
                flavor_by_pokemon[sid][text] = (vid, text)

        # --- build pokemon rows ---
        pokemon_rows = []
        flavor_rows = []
        for pid in sorted(default_ids):
            base = pokemon_base[pid]
            sp = species.get(pid, {})
            st = stats.get(pid, {})
            bst = sum(st.get(c, 0) for c in STAT_COLUMN.values())
            name_row = species_names.get(pid, {})

            # representative flavour text = newest distinct entry
            texts = flavor_by_pokemon.get(pid, {})
            rep_text = None
            if texts:
                newest = max(texts.values(), key=lambda t: t[0])
                rep_text = newest[1]
                for vid, text in sorted(texts.values(), key=lambda t: t[0]):
                    flavor_rows.append(
                        PokemonFlavorText(
                            pokemon_id=pid,
                            version=version_id_to_name.get(vid),
                            flavor_text=text,
                        )
                    )

            pokemon_rows.append(
                Pokemon(
                    id=pid,
                    species_id=pid,
                    dex_number=pid,
                    name=(name_row.get("name") or base["identifier"]).strip(),
                    genus=name_row.get("genus") or None,
                    generation_id=to_int(sp.get("generation_id")),
                    height_m=(to_int(base.get("height")) or 0) / 10 or None,
                    weight_kg=(to_int(base.get("weight")) or 0) / 10 or None,
                    base_experience=to_int(base.get("base_experience")),
                    capture_rate=to_int(sp.get("capture_rate")),
                    base_happiness=to_int(sp.get("base_happiness")),
                    is_legendary=sp.get("is_legendary") == "1",
                    is_mythical=sp.get("is_mythical") == "1",
                    is_baby=sp.get("is_baby") == "1",
                    color=colors.get(to_int(sp.get("color_id")) or -1),
                    shape=shapes.get(to_int(sp.get("shape_id")) or -1),
                    habitat=habitats.get(to_int(sp.get("habitat_id")) or -1),
                    evolution_chain_id=to_int(sp.get("evolution_chain_id")),
                    evolves_from_species_id=to_int(sp.get("evolves_from_species_id")),
                    hp=st.get("hp", 0),
                    attack=st.get("attack", 0),
                    defense=st.get("defense", 0),
                    sp_attack=st.get("sp_attack", 0),
                    sp_defense=st.get("sp_defense", 0),
                    speed=st.get("speed", 0),
                    base_stat_total=bst,
                    flavor_text=rep_text,
                    sprite_path=f"official-artwork/{pid}.png",
                )
            )
        session.add_all(pokemon_rows)
        session.commit()
        counts["pokemon"] = len(pokemon_rows)
        counts["flavor_texts"] = len(flavor_rows)

        # --- pokemon types ---
        type_rows = []
        for row in read_csv("pokemon_types"):
            pid = int(row["pokemon_id"])
            tid = int(row["type_id"])
            if pid in default_ids and tid in valid_type_ids:
                type_rows.append(
                    PokemonType(pokemon_id=pid, type_id=tid, slot=int(row["slot"]))
                )
        session.add_all(type_rows)
        counts["pokemon_types"] = len(type_rows)

        # --- pokemon abilities ---
        ability_rows = []
        for row in read_csv("pokemon_abilities"):
            pid = int(row["pokemon_id"])
            aid = int(row["ability_id"])
            if pid in default_ids and aid in valid_ability_ids:
                ability_rows.append(
                    PokemonAbility(
                        pokemon_id=pid,
                        ability_id=aid,
                        slot=int(row["slot"]),
                        is_hidden=row["is_hidden"] == "1",
                    )
                )
        session.add_all(ability_rows)
        counts["pokemon_abilities"] = len(ability_rows)

        session.add_all(flavor_rows)
        session.commit()

        # --- evolutions (shared with the standalone `make evolutions`) ---
        from app.ingest.evolutions import ingest_evolutions

        counts["evolutions"] = ingest_evolutions(session, default_ids)
        session.commit()

        # --- alternate forms (regional, Mega, Primal, Gigantamax, battle) ---
        from app.ingest.forms import ingest_forms

        counts.update(ingest_forms(session, default_ids, valid_type_ids))
        session.commit()

        # --- natures, moves & learnsets (for the team builder) ---
        counts.update(_ingest_moves_natures(session, default_ids, valid_type_ids))
        session.commit()

    return counts


def load_move_short_effects() -> dict[int, str]:
    """Map move_id → concise English effect text (``$effect_chance`` resolved).

    Joins ``moves.effect_id`` to ``move_effect_prose.short_effect`` (language 9).
    Shared by the full ingest and the standalone backfill.
    """
    prose: dict[int, str] = {}
    for row in read_csv("move_effect_prose"):
        if to_int(row["local_language_id"]) != 9:
            continue
        eid = to_int(row["move_effect_id"])
        if eid is not None and row.get("short_effect"):
            prose[eid] = row["short_effect"]
    out: dict[int, str] = {}
    for row in read_csv("moves"):
        mid = to_int(row["id"])
        if mid is None or mid >= 10000:
            continue
        eff = to_int(row["effect_id"])
        text = prose.get(eff) if eff is not None else None
        if not text:
            continue
        text = text.replace("$effect_chance", (row.get("effect_chance") or "").strip())
        out[mid] = text[:512]
    return out


def _ingest_moves_natures(
    session: Session, default_ids: set[int], valid_type_ids: set[int]
) -> dict[str, int]:
    """Ingest natures, battle moves, and each species' legal learnset.

    The learnset (``pokemon_moves.csv``) spans every version group; we collapse it
    to one representative row per ``(pokemon, move)`` — "can this species ever learn
    this move" — keeping the most instructive learn method (level-up first).
    """
    counts: dict[str, int] = {}

    # --- natures ---
    nature_names = _english_names("nature_names", "nature_id")
    natures = []
    for row in read_csv("natures"):
        nid = int(row["id"])
        inc = STAT_COLUMN.get(to_int(row["increased_stat_id"]) or -1)
        dec = STAT_COLUMN.get(to_int(row["decreased_stat_id"]) or -1)
        neutral = row["increased_stat_id"] == row["decreased_stat_id"]
        natures.append(
            Nature(
                id=nid,
                identifier=row["identifier"],
                name=nature_names.get(nid, {}).get("name", row["identifier"]),
                increased_stat=None if neutral else inc,
                decreased_stat=None if neutral else dec,
            )
        )
    session.add_all(natures)
    counts["natures"] = len(natures)

    # --- moves ---
    move_names = _english_names("move_names", "move_id")
    damage_classes = _lookup("move_damage_classes")
    short_effects = load_move_short_effects()
    move_rows: list[dict] = []
    valid_move_ids: set[int] = set()
    for row in read_csv("moves"):
        mid = int(row["id"])
        if mid >= 10000:  # skip max/g-max/shadow meta moves
            continue
        tid = to_int(row["type_id"])
        valid_move_ids.add(mid)
        move_rows.append(
            {
                "id": mid,
                "identifier": row["identifier"],
                "name": move_names.get(mid, {}).get("name", row["identifier"]),
                "type_id": tid if tid in valid_type_ids else None,
                "damage_class": damage_classes.get(to_int(row["damage_class_id"]) or -1),
                "power": to_int(row["power"]),
                "pp": to_int(row["pp"]),
                "accuracy": to_int(row["accuracy"]),
                "priority": to_int(row["priority"]) or 0,
                "short_effect": short_effects.get(mid),
            }
        )
    if move_rows:
        session.execute(Move.__table__.insert(), move_rows)
    counts["moves"] = len(move_rows)

    # --- legal learnsets (collapsed across version groups) ---
    methods = _lookup("pokemon_move_methods")
    # key (pid, mid) -> (rank, method, level)
    best: dict[tuple[int, int], tuple[int, str | None, int | None]] = {}
    for row in read_csv("pokemon_moves"):
        pid = int(row["pokemon_id"])
        if pid not in default_ids:
            continue
        mid = int(row["move_id"])
        if mid not in valid_move_ids:
            continue
        method = methods.get(to_int(row["pokemon_move_method_id"]) or -1)
        level = to_int(row["level"])
        rank = _METHOD_RANK.get(method or "", 9)
        key = (pid, mid)
        cur = best.get(key)
        if cur is None or rank < cur[0] or (
            rank == cur[0]
            and method == "level-up"
            and level
            and (cur[2] is None or level < cur[2])
        ):
            best[key] = (rank, method, level)

    learn_rows = [
        {
            "pokemon_id": pid,
            "move_id": mid,
            "learn_method": method,
            "level": level if method == "level-up" else None,
        }
        for (pid, mid), (_rank, method, level) in best.items()
    ]
    if learn_rows:
        session.execute(PokemonMove.__table__.insert(), learn_rows)
    counts["pokemon_moves"] = len(learn_rows)

    return counts


def _evolution_condition(
    detail: dict[str, str], item_names: dict[int, dict[str, str]]
) -> str | None:
    """Summarise extra evolution conditions into a short human-readable string."""
    parts: list[str] = []
    if to_int(detail.get("minimum_happiness")):
        parts.append(f"happiness ≥ {detail['minimum_happiness']}")
    if detail.get("time_of_day"):
        parts.append(f"{detail['time_of_day']} time")
    held = item_names.get(to_int(detail.get("held_item_id")) or -1, {}).get("name")
    if held:
        parts.append(f"holding {held}")
    if detail.get("needs_overworld_rain") == "1":
        parts.append("while raining")
    if to_int(detail.get("minimum_affection")):
        parts.append(f"affection ≥ {detail['minimum_affection']}")
    if to_int(detail.get("minimum_beauty")):
        parts.append(f"beauty ≥ {detail['minimum_beauty']}")
    return ", ".join(parts) or None


if __name__ == "__main__":
    result = ingest()
    print("Ingestion complete:")
    for table, n in result.items():
        print(f"  {table:>18}: {n}")
