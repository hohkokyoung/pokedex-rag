"""The home damage calculator's maths, ported line for line from
``frontend/lib/damageCalc.ts`` so the calc coach computes exactly what the calculator
shows.

Kept in lockstep by ``tests/test_damage_calc.py``, which runs this port over reference
cases the TypeScript generates (``make damage-fixtures`` — regenerate whenever the TS
changes). Operation order and ``floor`` semantics follow the TS so floating-point
rounding matches. ``app/services/battle.py`` (team duels) is a separate, simpler engine.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, replace

SKEYS = ("hp", "atk", "def", "spa", "spd", "spe")
SABBR = {"hp": "HP", "atk": "Atk", "def": "Def", "spa": "SpA", "spd": "SpD", "spe": "Spe"}

# name, raised stat, lowered stat (display abbreviations, as in the TS)
NAT: list[tuple[str, str | None, str | None]] = [
    ("Hardy", None, None), ("Lonely", "Atk", "Def"), ("Brave", "Atk", "Spe"),
    ("Adamant", "Atk", "SpA"), ("Naughty", "Atk", "SpD"), ("Bold", "Def", "Atk"),
    ("Docile", None, None), ("Relaxed", "Def", "Spe"), ("Impish", "Def", "SpA"),
    ("Lax", "Def", "SpD"), ("Timid", "Spe", "Atk"), ("Hasty", "Spe", "Def"),
    ("Serious", None, None), ("Jolly", "Spe", "SpA"), ("Naive", "Spe", "SpD"),
    ("Modest", "SpA", "Atk"), ("Mild", "SpA", "Def"), ("Quiet", "SpA", "Spe"),
    ("Bashful", None, None), ("Rash", "SpA", "SpD"), ("Calm", "SpD", "Atk"),
    ("Gentle", "SpD", "Def"), ("Sassy", "SpD", "Spe"), ("Careful", "SpD", "SpA"),
    ("Quirky", None, None),
]
NATURES = {n for n, _, _ in NAT}

TYPE_BOOST = {
    "Silk Scarf": "normal", "Charcoal": "fire", "Mystic Water": "water", "Magnet": "electric",
    "Miracle Seed": "grass", "Never-Melt Ice": "ice", "Black Belt": "fighting",
    "Poison Barb": "poison", "Soft Sand": "ground", "Sharp Beak": "flying",
    "Twisted Spoon": "psychic", "Silver Powder": "bug", "Hard Stone": "rock",
    "Spell Tag": "ghost", "Dragon Fang": "dragon", "Black Glasses": "dark",
    "Metal Coat": "steel", "Fairy Feather": "fairy",
}
RESIST_BERRY = {
    "Occa Berry": "fire", "Passho Berry": "water", "Wacan Berry": "electric",
    "Rindo Berry": "grass", "Yache Berry": "ice", "Chople Berry": "fighting",
    "Kebia Berry": "poison", "Shuca Berry": "ground", "Coba Berry": "flying",
    "Payapa Berry": "psychic", "Tanga Berry": "bug", "Charti Berry": "rock",
    "Kasib Berry": "ghost", "Haban Berry": "dragon", "Colbur Berry": "dark",
    "Babiri Berry": "steel", "Roseli Berry": "fairy",
}

# The frontend's static chart (lib/typeChart.ts); a test checks it equals the DB chart.
# What the maths models, for a client's pickers (GET /api/calc/options): each item with
# the side it works on and what it does; abilities likewise. Keep in step with calc_hit
# (test_calc_options checks every name here changes some result).
CALC_ITEMS: list[tuple[str, str, str]] = [
    ("Choice Band", "a", "Atk ×1.5"), ("Choice Specs", "a", "SpA ×1.5"),
    ("Life Orb", "a", "×1.3"), ("Expert Belt", "a", "super-effective ×1.2"),
    ("Muscle Band", "a", "physical ×1.1"), ("Wise Glasses", "a", "special ×1.1"),
    *[(name, "a", f"{t} moves ×1.2") for name, t in TYPE_BOOST.items()],
    ("Assault Vest", "d", "SpD ×1.5"), ("Eviolite", "d", "Def & SpD ×1.5 (unevolved)"),
    ("Focus Sash", "d", "survives one hit from full HP"),
    *[(name, "d", f"halves super-effective {t}") for name, t in RESIST_BERRY.items()],
]
CALC_ABILITIES: list[tuple[str, str, str]] = [
    ("Adaptability", "a", "STAB ×2"), ("Huge Power", "a", "Atk ×2"),
    ("Technician", "a", "moves ≤60 power ×1.5"), ("Guts", "a", "Atk ×1.5 while burned"),
    ("Tinted Lens", "a", "resisted hits ×2"), ("Thick Fat", "d", "takes ½ from Fire & Ice"),
    ("Multiscale", "d", "takes ½ at full HP"), ("Solid Rock", "d", "super-effective hits ×0.75"),
    ("Filter", "d", "super-effective hits ×0.75"),
]
WEATHERS = ["None", "Rain", "Sun"]
TERRAINS = ["None", "Electric", "Grassy", "Psychic"]

CHART: dict[str, dict[str, float]] = {
    "normal": {"rock": .5, "ghost": 0, "steel": .5},
    "fire": {"fire": .5, "water": .5, "grass": 2, "ice": 2, "bug": 2, "rock": .5, "dragon": .5,
             "steel": 2},
    "water": {"fire": 2, "water": .5, "grass": .5, "ground": 2, "rock": 2, "dragon": .5},
    "electric": {"water": 2, "electric": .5, "grass": .5, "ground": 0, "flying": 2,
                 "dragon": .5},
    "grass": {"fire": .5, "water": 2, "grass": .5, "poison": .5, "ground": 2, "flying": .5,
              "bug": .5, "rock": 2, "dragon": .5, "steel": .5},
    "ice": {"fire": .5, "water": .5, "grass": 2, "ice": .5, "ground": 2, "flying": 2,
            "dragon": 2, "steel": .5},
    "fighting": {"normal": 2, "ice": 2, "poison": .5, "flying": .5, "psychic": .5, "bug": .5,
                 "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": .5},
    "poison": {"grass": 2, "poison": .5, "ground": .5, "rock": .5, "ghost": .5, "steel": 0,
               "fairy": 2},
    "ground": {"fire": 2, "electric": 2, "grass": .5, "poison": 2, "flying": 0, "bug": .5,
               "rock": 2, "steel": 2},
    "flying": {"electric": .5, "grass": 2, "fighting": 2, "bug": 2, "rock": .5, "steel": .5},
    "psychic": {"fighting": 2, "poison": 2, "psychic": .5, "dark": 0, "steel": .5},
    "bug": {"fire": .5, "grass": 2, "fighting": .5, "poison": .5, "flying": .5, "psychic": 2,
            "ghost": .5, "dark": 2, "steel": .5, "fairy": .5},
    "rock": {"fire": 2, "ice": 2, "fighting": .5, "ground": .5, "flying": 2, "bug": 2,
             "steel": .5},
    "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": .5},
    "dragon": {"dragon": 2, "steel": .5, "fairy": 0},
    "dark": {"fighting": .5, "psychic": 2, "ghost": 2, "dark": .5, "fairy": .5},
    "steel": {"fire": .5, "water": .5, "electric": .5, "ice": 2, "rock": 2, "steel": .5,
              "fairy": 2},
    "fairy": {"fire": .5, "fighting": 2, "poison": .5, "dragon": 2, "dark": 2, "steel": .5},
}


def type_eff(atk: str, dfn: str) -> float:
    return CHART.get(atk, {}).get(dfn, 1)


def typing_eff(atk: str, defs: list[str]) -> float:
    m: float = 1
    for d in defs:
        m = m * type_eff(atk, d)
    return m


def nat_mul(name: str, key: str) -> float:
    r = next((x for x in NAT if x[0] == name), None)
    if r is None or key == "hp":
        return 1
    return 1.1 if r[1] == SABBR[key] else 0.9 if r[2] == SABBR[key] else 1


def stat_full(base: int, level: int, iv: int, ev: int, nm: float, is_hp: bool) -> int:
    core = math.floor((2 * base + iv + math.floor(ev / 4)) * level / 100)
    return core + level + 10 if is_hp else math.floor((core + 5) * nm)


# ---- inputs and result --------------------------------------------------------------


@dataclass(frozen=True)
class Mon:
    types: list[str]
    stats: dict[str, int]  # hp, attack, defense, sp_attack, sp_defense, speed (base)


@dataclass(frozen=True)
class Side:
    nat: str = "Hardy"
    ev: dict[str, int] = field(default_factory=lambda: dict.fromkeys(SKEYS, 0))
    iv: dict[str, int] = field(default_factory=lambda: dict.fromkeys(SKEYS, 31))
    item: str = "None"
    abil: str = "None"
    hp: float = 100  # current HP as % of max


@dataclass(frozen=True)
class MoveIn:
    type: str
    damage_class: str
    power: int


@dataclass(frozen=True)
class Field:
    level: int = 100
    doubles: bool = False
    spread: bool = False
    weather: str = "None"
    terrain: str = "None"
    reflect: bool = False
    lightscreen: bool = False
    crit: bool = False
    burn: bool = False
    helping_hand: bool = False
    friend_guard: bool = False


@dataclass(frozen=True)
class Result:
    min_pct: float
    max_pct: float
    ko: int  # hits to KO from current HP (0 = no damage)
    te: float
    stab: float
    A: int
    D: int
    base: int
    mod: float


def calc_hit(atk: Mon, a: Side, dfn: Mon, d: Side, move: MoveIn, f: Field) -> Result:
    level = f.level
    phys = move.damage_class == "physical"
    a_k, d_k = ("atk", "def") if phys else ("spa", "spd")
    A = stat_full(atk.stats["attack"] if phys else atk.stats["sp_attack"], level, a.iv[a_k],
                  a.ev[a_k], nat_mul(a.nat, a_k), False)
    D = stat_full(dfn.stats["defense"] if phys else dfn.stats["sp_defense"], level, d.iv[d_k],
                  d.ev[d_k], nat_mul(d.nat, d_k), False)
    HP = stat_full(dfn.stats["hp"], level, d.iv["hp"], d.ev["hp"], 1, True)
    if a.item == "Choice Band" and phys:
        A = math.floor(A * 1.5)
    if a.item == "Choice Specs" and not phys:
        A = math.floor(A * 1.5)
    if a.abil == "Huge Power" and phys:
        A = math.floor(A * 2)
    if a.abil == "Guts" and f.burn and phys:
        A = math.floor(A * 1.5)
    if d.item == "Assault Vest" and not phys:
        D = math.floor(D * 1.5)
    if d.item == "Eviolite":
        D = math.floor(D * 1.5)
    # Helping Hand boosts the move's base power, so it enters before the base-damage floor.
    power = math.floor(move.power * 1.5) if f.doubles and f.helping_hand else move.power
    base = math.floor(math.floor(math.floor((2 * level) / 5 + 2) * power * A / D) / 50) + 2
    te = typing_eff(move.type, dfn.types)
    stab = (2 if a.abil == "Adaptability" else 1.5) if move.type in atk.types else 1
    mod: float = 1
    if f.doubles and f.spread:
        mod *= 0.75
    if f.weather == "Rain":
        mod *= 1.5 if move.type == "water" else 0.5 if move.type == "fire" else 1
    if f.weather == "Sun":
        mod *= 1.5 if move.type == "fire" else 0.5 if move.type == "water" else 1
    if f.terrain == "Electric" and move.type == "electric":
        mod *= 1.3
    if f.terrain == "Grassy" and move.type == "grass":
        mod *= 1.3
    if f.terrain == "Psychic" and move.type == "psychic":
        mod *= 1.3
    if f.crit:
        mod *= 1.5
    if f.burn and phys and a.abil != "Guts":
        mod *= 0.5
    if not f.crit:
        if phys and f.reflect:
            mod *= 0.667 if f.doubles else 0.5
        if not phys and f.lightscreen:
            mod *= 0.667 if f.doubles else 0.5
    if f.doubles and f.friend_guard:
        mod *= 0.75
    if a.item == "Life Orb":
        mod *= 1.3
    if a.item == "Muscle Band" and phys:
        mod *= 1.1
    if a.item == "Wise Glasses" and not phys:
        mod *= 1.1
    if a.item == "Expert Belt" and te > 1:
        mod *= 1.2
    if TYPE_BOOST.get(a.item) == move.type:
        mod *= 1.2
    if RESIST_BERRY.get(d.item) == move.type and te > 1:
        mod *= 0.5
    if a.abil == "Technician" and move.power <= 60:
        mod *= 1.5
    if a.abil == "Tinted Lens" and te < 1:
        mod *= 2
    if d.abil == "Thick Fat" and move.type in ("fire", "ice"):
        mod *= 0.5
    if d.abil == "Multiscale" and d.hp >= 100:
        mod *= 0.5
    if d.abil in ("Solid Rock", "Filter") and te > 1:
        mod *= 0.75
    total = base * stab * te * mod
    max_dmg, min_dmg = math.floor(total), math.floor(total * 0.85)
    return Result(
        min_pct=min_dmg / HP * 100 if HP else 0,
        max_pct=max_dmg / HP * 100 if HP else 0,
        ko=0 if te == 0 or min_dmg <= 0 else math.ceil((HP * d.hp) / 100 / min_dmg),
        te=te, stab=stab, A=A, D=D, base=base, mod=stab * te * mod,
    )


# ---- what-ifs -----------------------------------------------------------------------

_EV_WORDS = {"hp": "hp", "atk": "atk", "attack": "atk", "def": "def", "defense": "def",
             "defence": "def", "spa": "spa", "spatk": "spa", "spd": "spd", "spdef": "spd",
             "spe": "spe", "speed": "spe"}
SIDE_KEYS = ("item", "ability", "nature", "evs", "hp")
FIELD_KEYS = ("weather", "terrain", "crit", "reflect", "lightscreen", "burn")


class ChangeError(ValueError):
    pass


def parse_evs(text: str, base: dict[str, int] | None = None) -> dict[str, int]:
    """'252 Atk / 4 HP' → EV dict (unnamed stats keep ``base``, else 0)."""
    out = dict(base or dict.fromkeys(SKEYS, 0))
    parts = [p for p in re.split(r"[/,]", text) if p.strip()]
    if not parts:
        raise ChangeError(f"no EVs in {text!r}")
    for part in parts:
        m = re.match(r"\s*(\d{1,3})\s*([a-z. ]+?)\s*$", part.lower())
        key = _EV_WORDS.get(re.sub(r"[ .]", "", m.group(2))) if m else None
        if not m or key is None:
            raise ChangeError(f"can't read EVs {part.strip()!r}")
        out[key] = int(m.group(1))
    if any(v < 0 or v > 252 for v in out.values()) or sum(out.values()) > 510:
        raise ChangeError("EVs must be 0–252 each and 510 in total")
    return out


def _bool(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def apply_changes(
    a: Side, d: Side, f: Field, changes: list[dict]
) -> tuple[Side, Side, Field]:
    """What-if copies: ``changes`` = [{who: attacker|defender|field, key, value}]."""
    for ch in changes:
        who, key, value = ch.get("who"), str(ch.get("key", "")).lower(), str(ch.get("value", ""))
        if who in ("attacker", "defender"):
            s = a if who == "attacker" else d
            if key == "item":
                s = replace(s, item=value.strip() or "None")
            elif key == "ability":
                s = replace(s, abil=value.strip() or "None")
            elif key == "nature":
                nat = value.strip().title()
                if nat not in NATURES:
                    raise ChangeError(f"unknown nature {value!r}")
                s = replace(s, nat=nat)
            elif key == "evs":
                s = replace(s, ev=parse_evs(value, s.ev))
            elif key == "hp":
                s = replace(s, hp=max(1.0, min(100.0, float(value.rstrip("%")))))
            else:
                raise ChangeError(f"unknown {who} change {key!r}")
            a, d = (s, d) if who == "attacker" else (a, s)
        elif who == "field" and key in FIELD_KEYS:
            if key in ("weather", "terrain"):
                f = replace(f, **{key: value.strip().title() or "None"})
            else:
                f = replace(f, **{key: _bool(value)})
        else:
            raise ChangeError(f"unknown change {who}/{key}")
    return a, d, f


# ---- survival threshold -------------------------------------------------------------

MAX_TOTAL = 508  # 510 in steps of 4


@dataclass(frozen=True)
class Survival:
    survives: bool
    stat: str  # "def" (physical hit) or "spd" (special hit)
    hp_ev: int
    stat_ev: int
    nature: str
    nature_changed: bool
    min_pct: float  # damage range at that spread (or the best spread when not survivable)
    max_pct: float
    current_min_pct: float
    current_max_pct: float


def _bulk_nature(dfn: Mon, stat: str) -> str:
    """+Def/+SpD, lowering whichever attacking stat the defender uses less."""
    lower_atk = dfn.stats["attack"] <= dfn.stats["sp_attack"]
    if stat == "def":
        return "Bold" if lower_atk else "Impish"
    return "Calm" if lower_atk else "Careful"


def survive(atk: Mon, a: Side, dfn: Mon, d: Side, move: MoveIn, f: Field) -> Survival:
    """The smallest HP + Def/SpD EV investment that survives the hit's max damage from the
    defender's current HP — then with a defensive nature if EVs alone don't do it."""
    stat = "def" if move.damage_class == "physical" else "spd"
    now = calc_hit(atk, a, dfn, d, move, f)
    others = sum(v for k, v in d.ev.items() if k not in ("hp", stat))
    room = MAX_TOTAL - others
    natures = [d.nat]
    bulk = _bulk_nature(dfn, stat)
    if bulk != d.nat:
        natures.append(bulk)

    best_fail: tuple[float, Side, Result] | None = None
    for nat in natures:
        found: tuple[int, int, Side, Result] | None = None  # (total, -hp, side, result)
        for hp_ev in range(0, min(252, room) + 1, 4):
            for st_ev in range(0, min(252, room - hp_ev) + 1, 4):
                if found and hp_ev + st_ev > found[0]:
                    break
                side = replace(d, nat=nat, ev={**d.ev, "hp": hp_ev, stat: st_ev})
                r = calc_hit(atk, a, dfn, side, move, f)
                if r.max_pct < side.hp:
                    key = (hp_ev + st_ev, -hp_ev)
                    if found is None or key < (found[0], found[1]):
                        found = (hp_ev + st_ev, -hp_ev, side, r)
                    break  # more of this stat only costs more
                if best_fail is None or r.max_pct < best_fail[0]:
                    best_fail = (r.max_pct, side, r)
        if found is not None:
            _total, _neg_hp, side, r = found
            return Survival(True, stat, side.ev["hp"], side.ev[stat], nat, nat != d.nat,
                            r.min_pct, r.max_pct, now.min_pct, now.max_pct)
    assert best_fail is not None
    _m, side, r = best_fail
    return Survival(False, stat, side.ev["hp"], side.ev[stat], side.nat, side.nat != d.nat,
                    r.min_pct, r.max_pct, now.min_pct, now.max_pct)
