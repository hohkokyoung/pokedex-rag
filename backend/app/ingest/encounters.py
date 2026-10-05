"""Ingest where to find each Pokémon in the wild, per game, from the PokéAPI CSVs.

Fills ``pokemon_encounters``: one row per Pokémon (or alternate form) × game ×
place × method × conditions, with a level range and a summed encounter chance.
The raw CSV has one row per encounter *slot*; slots for the same place/method/
conditions are folded together here, and rows that differ only by a condition
that covers every value (morning + day + night) collapse to one unconditional row.

Coverage is PokéAPI's: the main games through Sword / Shield and its DLC.

Standalone and idempotent: needs only ``pokemon`` / ``pokemon_forms`` and clears
and reloads its own table. Run on the host against the Compose DB:
``uv run python -m app.ingest.encounters``.
"""

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ingest.csv_source import read_csv, to_int
from app.ingest.run import _sync_engine
from app.models import Pokemon, PokemonEncounter, PokemonForm

_EN = 9  # English local_language_id
# Colosseum / XD and the Japan-only Gen 1 releases.
_SKIP_VERSIONS = {"colosseum", "xd", "red-japan", "green-japan", "blue-japan"}
# The CSV's method prose is a sentence ("Walking in tall grass or a cave"); these
# read better as a table cell. Anything unlisted falls back to the prose.
_METHOD_NAMES = {
    "walk": "Grass / cave",
    "old-rod": "Old Rod",
    "good-rod": "Good Rod",
    "super-rod": "Super Rod",
    "surf": "Surfing",
    "rock-smash": "Rock Smash",
    "headbutt": "Headbutt",
    "headbutt-low": "Headbutt (rare tree)",
    "headbutt-normal": "Headbutt",
    "headbutt-high": "Headbutt (common tree)",
    "dark-grass": "Dark grass",
    "grass-spots": "Rustling grass",
    "cave-spots": "Dust cloud",
    "bridge-spots": "Bridge shadow",
    "super-rod-spots": "Fishing (rippling water)",
    "surf-spots": "Surfing (rippling water)",
    "yellow-flowers": "Yellow flowers",
    "purple-flowers": "Purple flowers",
    "red-flowers": "Red flowers",
    "rough-terrain": "Rough terrain",
    "gift": "Gift",
    "gift-egg": "Gift egg",
    "static": "Static encounter",
    "pokeflute": "Poké Flute",
    "squirt-bottle": "Squirt Bottle",
    "wailmer-pail": "Wailmer Pail",
    "seaweed": "Diving",
    "roaming-grass": "Roaming (grass)",
    "roaming-water": "Roaming (water)",
    "devon-scope": "Devon Scope",
    "feebas-tile-fishing": "Fishing (Feebas tile)",
    "island-scan": "Island Scan",
    "sos": "SOS battle",
    "bubbling-spots": "Fishing (bubbling spot)",
    "sos-from-bubbling-spot": "SOS (bubbling spot)",
    "berry-trees": "Berry tree",
    "npc-trade": "In-game trade",
    "overworld": "Overworld",
    "overworld-water": "Overworld (water)",
    "overworld-flying": "Overworld (sky)",
    "overworld-special": "Overworld (rare)",
    "overworld-flying-special": "Overworld (rare, sky)",
    "overworld-water-special": "Overworld (rare, water)",
    "overworld-dirt": "Overworld (ground)",
    "horde": "Horde",
    "hidden-grotto": "Hidden Grotto",
    "honey-tree": "Honey tree",
    "wanderer": "Wanderer",
    "wanderer-water": "Wanderer (water)",
    "chase-water": "Chases you (water)",
    "dynamax-adventure": "Dynamax Adventure",
    "max-raid": "Max Raid",
    "trash-can-ambush": "Trash can",
    "rustling-bush-ambush": "Rustling bush",
    "ceiling-ambush": "Ceiling ambush",
    "ground-ambush": "Ground ambush",
    "sky-ambush": "Sky ambush",
}
# Raid dens split every slot by beam colour × star rating; one row per den reads better.
_NO_ODDS = {"max-raid", "dynamax-adventure"}
_NEUTRAL = re.compile(r"-(no|off|none)$")
_PAREN = re.compile(r"\(([^)]+)\)\s*$")


def _en(name: str, key: str) -> dict[int, str]:
    """English ``name`` per id from a ``*_names`` / ``*_prose`` CSV."""
    return {
        int(r[key]): r["name"]
        for r in read_csv(name)
        if to_int(r["local_language_id"]) == _EN and r["name"]
    }


def _area_label(identifier: str, prose: str | None) -> str | None:
    """The part of a location area that tells it apart from the location itself.

    The English area prose repeats the location ("Route 204 (south, towards
    Jubilife City)"), so take its parenthetical; otherwise humanise the slug.
    """
    if prose and (m := _PAREN.search(prose)):
        return m.group(1)[:1].upper() + m.group(1)[1:]
    if not identifier or identifier == "area":
        return None
    words = identifier.replace("-", " ").split()
    label = " ".join(w.upper() if re.fullmatch(r"b?\d+f", w) else w for w in words)
    return label[:1].upper() + label[1:]


# The CSV's condition prose is long ("Before entering the Hall of Fame · During
# normal weather / During overcast weather / …"); these keep a table cell to a line.
_SHORT = {
    "story-progress-before-hall-of-fame": "Before Hall of Fame",
    "story-progress-hall-of-fame": "After Hall of Fame",
}
_WEATHER = {
    "weather-normal": "clear",
    "weather-overcast": "overcast",
    "weather-raining": "rain",
    "weather-thunderstorm": "thunderstorm",
    "weather-snowing": "snow",
    "weather-snowstorm": "snowstorm",
    "weather-sandstorm": "sandstorm",
    "weather-intense-sun": "intense sun",
    "weather-fog": "fog",
}


CondKey = tuple[int, str]


def _family(identifier: str) -> str:
    """Which set of mutually exclusive values a condition value belongs to."""
    for pattern, family in (
        (r"weather-", "weather"),
        (r"time-(morning|day|night)$", "time-of-day"),
        (r"time-minute-", "minute"),
        (r"time-\d", "clock"),
        (r"max-den-", identifier.rsplit("-", 2)[0]),
    ):
        if re.match(pattern, identifier):
            return family
    return ""


def _condition_text(
    vids: set[int],
    every: set[int],
    ident: dict[int, str],
    values: dict[int, tuple[int, str]],
) -> str:
    """One condition's values as short text; alternatives read "a, b or c".

    Weather lists flip to "Any weather but …" once most kinds qualify.
    """
    if all(ident[v] in _WEATHER for v in vids):
        missing = [_WEATHER[ident[v]] for v in sorted(every - vids)]
        if len(missing) <= 3 and len(vids) > len(missing):
            return f"Any weather but {_or(missing)}"
        text = _or([_WEATHER[ident[v]] for v in sorted(vids)])
        return text[:1].upper() + text[1:]
    return " / ".join(_SHORT.get(ident[v], values[v][1]) for v in sorted(vids))


def _or(words: list[str]) -> str:
    return words[0] if len(words) == 1 else f"{', '.join(words[:-1])} or {words[-1]}"


def main() -> None:
    engine = _sync_engine()
    with Session(engine) as session:
        wanted = set(session.execute(select(Pokemon.id)).scalars()) | set(
            session.execute(select(PokemonForm.id)).scalars()
        )

        vgs = {int(r["id"]): r for r in read_csv("version_groups")}
        version_names = _en("version_names", "version_id")
        # id -> (name, generation, release order: version group, then version)
        versions: dict[int, tuple[str, int, int]] = {}
        for r in read_csv("versions"):
            if r["identifier"] in _SKIP_VERSIONS:
                continue
            vid, vg = int(r["id"]), vgs[int(r["version_group_id"])]
            name = version_names.get(vid, r["identifier"].title())
            versions[vid] = (name, int(vg["generation_id"]), int(vg["order"]) * 100 + vid)

        region_names = _en("region_names", "region_id")
        location_names = _en("location_names", "location_id")
        locations = {
            int(r["id"]): (
                location_names.get(int(r["id"]), r["identifier"].replace("-", " ").title()),
                region_names.get(to_int(r["region_id"]) or -1),
            )
            for r in read_csv("locations")
        }
        area_prose = _en("location_area_prose", "location_area_id")
        areas = {
            int(r["id"]): (
                int(r["location_id"]),
                _area_label(r["identifier"], area_prose.get(int(r["id"]))),
            )
            for r in read_csv("location_areas")
        }

        method_ident = {int(r["id"]): r["identifier"] for r in read_csv("encounter_methods")}
        method_prose = _en("encounter_method_prose", "encounter_method_id")
        slots = {
            int(r["id"]): (int(r["encounter_method_id"]), to_int(r["rarity"]))
            for r in read_csv("encounter_slots")
        }

        # Condition values: drop the "nothing special" ones (not during a swarm,
        # radar off, empty slot 2). Other defaults are real states ("during the day").
        cond_prose = _en("encounter_condition_value_prose", "encounter_condition_value_id")
        # Conditions are keyed by (condition id, family): the CSV files unrelated
        # values under one id (weather sits with raid star ratings; time of day
        # with clock-minute ranges), and "every value present" must be per family.
        cond_values: dict[int, tuple[CondKey, str]] = {}  # value id -> (key, text)
        cond_all: dict[CondKey, set[int]] = defaultdict(set)  # key -> every value id
        cond_ident: dict[int, str] = {}
        for r in read_csv("encounter_condition_values"):
            vid, ident = int(r["id"]), r["identifier"]
            key = (int(r["encounter_condition_id"]), _family(ident))
            cond_ident[vid] = ident
            cond_all[key].add(vid)
            text = cond_prose.get(vid)
            if text and text != "None" and not _NEUTRAL.search(ident):
                cond_values[vid] = (key, text)
        enc_conds: dict[int, set[int]] = defaultdict(set)
        for r in read_csv("encounter_condition_value_map"):
            vid = int(r["encounter_condition_value_id"])
            if vid in cond_values:
                enc_conds[int(r["encounter_id"])].add(vid)

        # Fold slots: (pokemon, version, area, method, conditions) -> [min, max, chance].
        Key = tuple[int, int, int, int, frozenset[int]]
        folded: dict[Key, list[int | None]] = {}
        for r in read_csv("encounters"):
            pid, ver = int(r["pokemon_id"]), int(r["version_id"])
            if pid not in wanted or ver not in versions:
                continue
            method_id, rarity = slots[int(r["encounter_slot_id"])]
            conds = frozenset(enc_conds.get(int(r["id"]), ()))
            if method_ident[method_id] in _NO_ODDS:
                conds, rarity = frozenset(), None
            key = (pid, ver, int(r["location_area_id"]), method_id, conds)
            lo, hi = int(r["min_level"]), int(r["max_level"])
            cur = folded.get(key)
            if cur is None:
                folded[key] = [lo, hi, rarity]
            else:
                cur[0], cur[1] = min(cur[0], lo), max(cur[1], hi)
                cur[2] = None if cur[2] is None or rarity is None else cur[2] + rarity

        # Rows identical but for their conditions merge; a condition whose every
        # value is then present (all three times of day) stops being a condition.
        merged: dict[tuple, set[int]] = defaultdict(set)
        for (pid, ver, area, method_id, conds), (lo, hi, chance) in folded.items():
            merged[(pid, ver, area, method_id, lo, hi, chance)] |= conds or {0}
        rows = []
        for (pid, ver, area, method_id, lo, hi, chance), conds in merged.items():
            by_cond: dict[CondKey, set[int]] = defaultdict(set)
            for vid in conds - {0}:
                by_cond[cond_values[vid][0]].add(vid)
            if 0 in conds:  # an unconditional variant exists: conditions add nothing
                by_cond = {}
            # Every value of a condition present = it doesn't matter (any time of day).
            # Values of one condition are alternatives ("In the morning / At night").
            texts = [
                _condition_text(
                    vids, {v for v in cond_all[cid] if v in cond_values}, cond_ident, cond_values
                )
                for cid, vids in sorted(by_cond.items())
                if not {v for v in cond_all[cid] if v in cond_values} <= vids
            ]
            location_id, area_label = areas[area]
            location, region = locations[location_id]
            ident = method_ident[method_id]
            version, gen, order = versions[ver]
            rows.append(
                {
                    "pokemon_id": pid,
                    "version_id": ver,
                    "version": version,
                    "generation": gen,
                    "sort_order": order,
                    "region": region,
                    "location": location,
                    "area": area_label,
                    "method": ident,
                    "method_name": _METHOD_NAMES.get(ident) or method_prose.get(method_id, ident),
                    "min_level": lo,
                    "max_level": hi,
                    # Stacked gift/static slots can sum past 100.
                    "chance": min(chance, 100) if chance is not None else None,
                    "conditions": " · ".join(texts)[:255] or None,
                }
            )

        session.execute(delete(PokemonEncounter))
        for i in range(0, len(rows), 20_000):
            session.execute(PokemonEncounter.__table__.insert(), rows[i : i + 20_000])
        session.commit()
    species = len({r["pokemon_id"] for r in rows})
    print(f"Ingested {len(rows)} encounter rows for {species} Pokémon/forms.")


if __name__ == "__main__":
    main()
