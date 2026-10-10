"""One calculator turn played out: who moves first, who each move hits (doubles
targeting), HP carried from hit to hit as a worst/best range, Focus Sash, KO calls.

Ported from the website's ``frontend/lib/calcTurn.ts`` (``playTurn``) over the shared
per-hit formula (``damage_calc.calc_hit``), and pinned to it by
``tests/fixtures/turn_cases.json`` (``make damage-fixtures``). Change the TS first, port
it here, regenerate the fixtures, run the tests. Pure code, no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from app.services import damage_calc as dc

TgKind = Literal["sel", "rand", "foes", "all", "ally"]


def tg_kind(target: str | None) -> TgKind:
    """Doubles targeting from the move's PokéAPI ``move_targets`` identifier."""
    return {"all-opponents": "foes", "all-other-pokemon": "all", "ally": "ally",
            "random-opponent": "rand"}.get(target or "", "sel")  # type: ignore[return-value]


def is_spread(k: TgKind) -> bool:
    return k in ("foes", "all")


def side_of(i: int) -> int:
    return 0 if i < 2 else 1


@dataclass(frozen=True)
class TurnMove:
    type: str
    damage_class: str
    power: int
    target: str | None = None
    priority: int = 0

    @property
    def maths(self) -> dc.MoveIn:
        return dc.MoveIn(self.type, self.damage_class, self.power)


@dataclass(frozen=True)
class TurnSlot:
    """Slots 0–1 are your side, 2–3 the opponent's; ``mon`` is None for an empty slot."""

    mon: dc.Mon | None
    set: dc.Side = field(default_factory=dc.Side)
    move: TurnMove | None = None


@dataclass(frozen=True)
class TurnField:
    level: int = 100
    doubles: bool = False
    weather: str = "None"
    terrain: str = "None"
    reflect: bool = False
    lightscreen: bool = False
    crit: bool = False
    burn: bool = False
    friend_guard: bool = False


@dataclass
class Hit:
    frm: int
    to: int
    r: dc.Result
    ff: bool  # hits its own side (a spread move's partner)
    ko: Literal["yes", "maybe"] | None = None
    sash: bool = False


@dataclass
class Step:
    i: int
    skipped: bool
    at_risk: bool
    hits: list[Hit]


@dataclass(frozen=True)
class Order:
    i: int
    pri: int
    spe: int


@dataclass
class HpRange:
    lo: float  # if every roll is high
    hi: float  # if every roll is low
    sash: bool = False


@dataclass
class Turn:
    active: list[int]
    aim: dict[int, int | None]
    order: list[Order]
    steps: list[Step]
    hp: dict[int, HpRange]


def play_turn(f: TurnField, slots: list[TurnSlot], aims: list[int]) -> Turn:
    active = [0, 1, 2, 3] if f.doubles else [0, 2]

    def foes_of(i: int) -> list[int]:
        return [j for j in active if side_of(j) != side_of(i)]

    def mate_of(i: int) -> int | None:
        return next((j for j in active if j != i and side_of(j) == side_of(i)), None)

    def targets_of(i: int) -> list[int]:
        return [j for j in foes_of(i) if slots[j].mon]

    def aim_of(i: int) -> int | None:
        t = targets_of(i)
        if aims[i] in t:
            return aims[i]
        return t[0] if t else (foes_of(i)[0] if foes_of(i) else None)

    def kind_of(i: int) -> TgKind:
        m = slots[i].move
        return tg_kind(m.target if m else None)

    base = dc.Field(level=f.level, doubles=f.doubles, spread=False, weather=f.weather,
                    terrain=f.terrain, reflect=f.reflect, lightscreen=f.lightscreen, crit=f.crit,
                    burn=f.burn, helping_hand=False, friend_guard=f.friend_guard)

    def hits_for(u: int, move: TurnMove | None, aim: int | None, up, hp_of) -> list[Hit]:
        a, mate = slots[u], mate_of(u)
        if not a.mon or not move or move.power <= 0:
            return []
        k: TgKind = tg_kind(move.target) if f.doubles else "sel"
        if k == "ally":
            return []
        helped = (f.doubles and mate is not None and bool(slots[mate].mon) and up(mate)
                  and kind_of(mate) == "ally")
        standing = [t for t in foes_of(u) if slots[t].mon and up(t)]
        single = aim if aim is not None and slots[aim].mon and up(aim) else (
            standing[0] if standing else None)
        tos = (standing if is_spread(k) else ([single] if single is not None else []))
        if k == "all" and mate is not None and slots[mate].mon and up(mate):
            tos = [*tos, mate]
        out = []
        for t in tos:
            opp = side_of(t) == 1
            fld = replace(base, spread=is_spread(k), helping_hand=helped,
                          reflect=f.reflect and opp, lightscreen=f.lightscreen and opp,
                          friend_guard=f.friend_guard and opp, burn=f.burn and side_of(u) == 0)
            r = dc.calc_hit(a.mon, a.set, slots[t].mon, replace(slots[t].set, hp=hp_of(t)),  # type: ignore[arg-type]
                            move.maths, fld)
            out.append(Hit(u, t, r, side_of(t) == side_of(u)))
        return out

    def spe(s: TurnSlot) -> int:
        if not s.mon:
            return 0
        return dc.stat_full(s.mon.stats["speed"], f.level, s.set.iv["spe"], s.set.ev["spe"],
                            dc.nat_mul(s.set.nat, "spe"), False)

    # Turn order: move priority first, then Speed (stable, like JS sort).
    order = sorted(
        (Order(i, slots[i].move.priority if slots[i].move else 0, spe(slots[i]))
         for i in active if slots[i].mon),
        key=lambda o: (-o.pri, -o.spe),
    )

    hp = {i: HpRange(slots[i].set.hp, slots[i].set.hp) for i in active}

    def standing(t: int) -> bool:
        return hp[t].hi > 0

    steps: list[Step] = []
    for o in order:
        i = o.i
        if not standing(i):
            steps.append(Step(i, True, False, []))
            continue
        at_risk = hp[i].lo <= 0
        hs = hits_for(i, slots[i].move, aim_of(i), standing, lambda t: hp[t].hi)
        for h in hs:
            x, d = hp[h.to], slots[h.to].set
            if h.r.te == 0:
                continue
            sash = d.item == "Focus Sash" and not x.sash and x.lo >= 100 and h.r.max_pct >= 100
            if sash:
                x.sash, x.lo, x.hi = True, 1, max(1, 100 - h.r.min_pct)
            else:
                x.lo, x.hi = max(0, x.lo - h.r.max_pct), max(0, x.hi - h.r.min_pct)
            h.ko = "yes" if x.hi <= 0 else "maybe" if x.lo <= 0 else None
            h.sash = sash
        steps.append(Step(i, False, at_risk, hs))

    return Turn(active=active, aim={i: (aim_of(i) if i in active else None) for i in range(4)},
                order=order, steps=steps, hp=hp)
