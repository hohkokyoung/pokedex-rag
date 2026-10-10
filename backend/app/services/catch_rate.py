"""Catch odds per Poké Ball — the Gen 8+ (Sword/Shield onward) formula.

    a = (3M − 2H) / 3M × rate × ball × status × lowLevel        (a ≥ 255 → caught)
    shake check b = 65536 / (255 / a)^(3/16), passed 4 times    → (b/65536)^4
    critical capture: chance floor(a × dex × charm / 6) / 256, needs only 1 check

Ball and status values follow Bulbapedia's Gen 8+ tables. Ported from the website's
``lib/catchRate.ts`` and pinned to its output by golden cases
(``tests/fixtures/catch_cases.json``). Pure code, no LLM.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from app.services.stats import round_half_up

STATUS_MUL = {"none": 1, "sleep": 2.5, "freeze": 2.5, "paralysis": 1.5, "burn": 1.5, "poison": 1.5}
MOON = {30, 33, 35, 39, 300, 517}  # evolve with a Moon Stone
ULTRA_BEAST = {793, 794, 795, 796, 797, 798, 799, 803, 804, 805, 806}


@dataclass(frozen=True)
class CatchMon:
    dex: int
    types: list[str]
    capture_rate: int
    base_hp: int
    base_speed: int
    weight_kg: float
    gender_rate: int  # -1 genderless


@dataclass(frozen=True)
class Situation:
    hp_pct: int = 100  # 1–100 of current HP
    level: int = 30  # wild level
    my_level: int = 30  # your lead's level (Level Ball)
    turn: int = 1  # 1 = first throw
    status: str = "none"
    night: bool = False  # night or cave (Dusk Ball)
    water: bool = False  # fishing / surfing / underwater (Dive, Lure)
    caught: bool = False  # species already caught (Repeat Ball)
    love_match: bool = False  # your lead: same species, opposite gender (Love Ball)
    dex_caught: int = 0  # species caught (critical capture)
    charm: bool = False  # Catching Charm


@dataclass(frozen=True)
class Rule:
    mul: float
    why: str
    rate_add: int = 0
    sure: bool = False


def _num(x: float) -> str:
    """A number as JavaScript prints it (460.0 → "460")."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def _flat(mul: float, why: str) -> Callable[[CatchMon, Situation], Rule]:
    return lambda m, c: Rule(mul, why)


def _timer(m: CatchMon, c: Situation) -> Rule:
    mul = min(4, 1 + (c.turn - 1) * 1229 / 4096)
    why = "maxed at ×4 (turn 11+)" if c.turn >= 11 else f"turn {c.turn}: 1 + 0.3 per turn"
    return Rule(mul, why)


def _level(m: CatchMon, c: Situation) -> Rule:
    r = c.my_level / c.level
    if r >= 4:
        return Rule(8, "your level ≥ 4× theirs ×8")
    if r >= 2:
        return Rule(4, "your level ≥ 2× theirs ×4")
    if r > 1:
        return Rule(2, "your level higher ×2")
    return Rule(1, "your level isn't higher")


def _heavy(m: CatchMon, c: Situation) -> Rule:
    w = m.weight_kg
    add = 30 if w >= 300 else 20 if w >= 200 else 0 if w >= 100 else -20
    return Rule(1, f"{_num(w)} kg → catch rate {'+' if add >= 0 else '−'}{abs(add)}", rate_add=add)


def _nest(m: CatchMon, c: Situation) -> Rule:
    if c.level < 30:
        return Rule(max(1, (41 - c.level) / 10), f"(41 − Lv {c.level}) / 10")
    return Rule(1, "no bonus at Lv 30+")


def _if(test: Callable[[CatchMon, Situation], bool], mul: float, yes: str, no: str,
        otherwise: float = 1) -> Callable[[CatchMon, Situation], Rule]:
    return lambda m, c: Rule(mul, yes) if test(m, c) else Rule(otherwise, no)


# (id, name, rule) in the website's table order (ties in the ranking keep it).
BALLS: list[tuple[str, str, Callable[[CatchMon, Situation], Rule]]] = [
    ("poke", "Poké Ball", _flat(1, "standard")),
    ("great", "Great Ball", _flat(1.5, "always ×1.5")),
    ("ultra", "Ultra Ball", _flat(2, "always ×2")),
    ("master", "Master Ball", lambda m, c: Rule(255, "never fails", sure=True)),
    ("quick", "Quick Ball", _if(lambda m, c: c.turn == 1, 5, "first turn ×5", "only ×5 on turn 1")),
    ("dusk", "Dusk Ball", _if(lambda m, c: c.night, 3, "night / cave ×3",
                              "×3 only at night or in caves")),
    ("timer", "Timer Ball", _timer),
    ("net", "Net Ball", _if(lambda m, c: any(t in ("bug", "water") for t in m.types), 3.5,
                            "Bug/Water ×3.5", "×3.5 only vs Bug or Water")),
    ("nest", "Nest Ball", _nest),
    ("repeat", "Repeat Ball", _if(lambda m, c: c.caught, 3.5, "already caught ×3.5",
                                  "×3.5 only if caught before")),
    ("dive", "Dive Ball", _if(lambda m, c: c.water, 3.5, "on/under water ×3.5",
                              "×3.5 only on water / fishing")),
    ("lure", "Lure Ball", _if(lambda m, c: c.water, 4, "hooked by fishing ×4",
                              "×4 only when fishing")),
    ("fast", "Fast Ball", lambda m, c: Rule(4, f"base Speed {m.base_speed} ≥ 100 ×4")
        if m.base_speed >= 100 else Rule(1, f"base Speed {m.base_speed} < 100")),
    ("level", "Level Ball", _level),
    ("heavy", "Heavy Ball", _heavy),
    ("moon", "Moon Ball", _if(lambda m, c: m.dex in MOON, 4, "Moon Stone evolver ×4",
                              "×4 only for Moon Stone evolvers")),
    ("love", "Love Ball", _if(lambda m, c: m.gender_rate >= 0 and c.love_match, 8,
                              "same species, opposite gender ×8",
                              "×8 vs same species, opposite gender")),
    ("dream", "Dream Ball", _if(lambda m, c: c.status == "sleep", 4, "asleep ×4",
                                "×4 only if asleep")),
    ("beast", "Beast Ball", _if(lambda m, c: m.dex in ULTRA_BEAST, 5, "Ultra Beast ×5",
                                "not an Ultra Beast ×0.1", otherwise=0.1)),
    ("premier", "Premier Ball", _flat(1, "same as Poké Ball")),
]


@dataclass(frozen=True)
class Terms:
    max_hp: int
    hp: int
    rate: int
    hp_factor: float
    ball: float
    status: float
    low_level: float
    a: float
    shake: float
    crit: float


@dataclass(frozen=True)
class BallOdds:
    id: str
    name: str
    why: str
    p: float
    throws: int | None  # throws for a 90% chance of at least one catch; None if impossible
    sure: bool
    terms: Terms


def _hp_stat(base: int, level: int) -> int:
    return math.floor((2 * base + 15) * level / 100) + level + 10  # average IV, 0 EV


def _dex_mul(n: int) -> float:
    if n > 600:
        return 2.5
    if n > 450:
        return 2
    if n > 300:
        return 1.5
    if n > 150:
        return 1
    return 0.5 if n > 30 else 0


def throws_for(p: float, target: float = 0.9) -> int | None:
    if p >= 1:
        return 1
    if p <= 0:
        return None
    return math.ceil(math.log(1 - target) / math.log(1 - p))


def odds(m: CatchMon, ball: tuple[str, str, Callable[[CatchMon, Situation], Rule]],
         c: Situation) -> BallOdds:
    bid, name, rule = ball
    max_hp = _hp_stat(m.base_hp, c.level)
    hp = max(1, round_half_up(max_hp * c.hp_pct / 100))
    r = rule(m, c)
    rate = max(1, m.capture_rate + r.rate_add)
    hp_factor = (3 * max_hp - 2 * hp) / (3 * max_hp)
    status = STATUS_MUL[c.status]
    low = (30 - c.level) / 10 if c.level < 20 else 1
    a = hp_factor * rate * r.mul * status * low

    def done(p: float, shake: float, crit: float, sure: bool) -> BallOdds:
        terms = Terms(max_hp, hp, rate, hp_factor, r.mul, status, low, min(a, 255), shake, crit)
        return BallOdds(bid, name, r.why, p, throws_for(p), sure, terms)

    if r.sure or a >= 255:
        return done(1, 1, 0, True)
    shake = min(1, math.floor(65536 / math.pow(255 / a, 3 / 16)) / 65536)
    crit = min(255, math.floor(a * _dex_mul(c.dex_caught) * (2 if c.charm else 1) / 6)) / 256
    p = crit * shake + (1 - crit) * math.pow(shake, 4)
    return done(p, shake, crit, False)


def rank(m: CatchMon, c: Situation) -> list[BallOdds]:
    """Every ball, best chance first; ties keep the table's order."""
    return sorted((odds(m, b, c) for b in BALLS), key=lambda o: -o.p)
