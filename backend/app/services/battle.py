"""Move-aware one-on-one maths for the team analysis.

Everything the head-to-head needs beyond raw typing: damage % from the level-50
damage formula (average roll) with STAB, the type chart, damage-relevant
abilities and held items (see `sets`); hits-to-KO; completing a partial moveset
from the species' ingested learnset; and `duel`, a short turn-by-turn one-on-one
where a set setup move (Swords Dance, Dragon Dance…) can be used before attacking,
Speed Boost / Choice Scarf change who moves first, and Focus Sash, Sturdy,
Leftovers, Life Orb recoil and Intimidate apply. Not modelled: weather/terrain,
crits, status, multi-hit/charge quirks, switching or prediction.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Move, PokemonMove
from app.schemas.team import TeamMemberOut
from app.services import matchups, sets
from app.services.stats import DEFAULT_LEVEL, STAT_KEYS, final_stats

MAX_MOVES = 4
AVG_ROLL = 0.925  # mean of the 0.85–1.00 damage roll
NO_KO = 99  # hits-to-KO when a move does no damage

# Learnset moves never suggested: self-KO, recharge/charge turns, delayed or
# conditional hits whose listed power overstates real damage.
EXCLUDED_MOVES = {
    "explosion", "self-destruct", "misty-explosion", "memento", "final-gambit",
    "hyper-beam", "giga-impact", "blast-burn", "hydro-cannon", "frenzy-plant",
    "rock-wrecker", "roar-of-time", "eternabeam", "prismatic-laser", "meteor-assault",
    "solar-beam", "solar-blade", "sky-attack", "skull-bash", "razor-wind", "freeze-shock",
    "ice-burn", "geomancy", "meteor-beam", "focus-punch", "future-sight", "doom-desire",
    "dream-eater", "last-resort", "belch", "synchronoise", "mind-blown", "steel-beam",
    "shell-trap", "beak-blast", "burn-up", "double-shock", "steel-roller",
    "hyperspace-fury", "hyperspace-hole", "dig", "dive", "fly", "bounce", "phantom-force",
    "shadow-force", "outrage", "thrash", "petal-dance", "uproar", "rollout", "ice-ball",
}

# Defender abilities: attacking type -> multiplier applied on top of the type chart.
ABILITY_DEFENSE: dict[str, dict[str, float]] = {
    "levitate": {"ground": 0.0},
    "earth-eater": {"ground": 0.0},
    "flash-fire": {"fire": 0.0},
    "well-baked-body": {"fire": 0.0},
    "water-absorb": {"water": 0.0},
    "storm-drain": {"water": 0.0},
    "dry-skin": {"water": 0.0, "fire": 1.25},
    "volt-absorb": {"electric": 0.0},
    "lightning-rod": {"electric": 0.0},
    "motor-drive": {"electric": 0.0},
    "sap-sipper": {"grass": 0.0},
    "thick-fat": {"fire": 0.5, "ice": 0.5},
    "heatproof": {"fire": 0.5},
    "water-bubble": {"fire": 0.5},
    "purifying-salt": {"ghost": 0.5},
    "fluffy": {"fire": 2.0},
}
SUPER_EFFECTIVE_FILTERS = {"filter": 0.75, "solid-rock": 0.75, "prism-armor": 0.75}


def ability_key(name: str | None) -> str | None:
    return sets.key(name)


@dataclass(frozen=True)
class Attack:
    move_id: int
    name: str
    type: str
    damage_class: str  # physical | special
    power: int
    accuracy: int | None = None
    priority: int = 0
    learned: bool = False  # True = picked from the learnset, not set on the slot


@dataclass
class Fighter:
    slot: int
    name: str
    types: list[str]
    stats: dict[str, int]
    ability: str | None
    def_mults: dict[str, float]  # attacking type -> multiplier (chart + ability)
    set_attacks: list[Attack] = field(default_factory=list)
    open_slots: int = MAX_MOVES
    pool: list[Attack] = field(default_factory=list)  # learnable damaging moves
    moves: list[Attack] = field(default_factory=list)  # effective set after completion
    item: str | None = None  # held item key (sets.key)
    setup: sets.Setup | None = None  # best setup move on the slot, if any


@dataclass(frozen=True)
class Hit:
    attack: Attack | None
    mult: float
    pct: float  # % of the defender's HP per hit (average roll, accuracy-weighted)
    hko: int  # hits to KO


def type_mult(att: Attack, dfn: Fighter) -> float:
    m = dfn.def_mults.get(att.type, 1.0)
    if dfn.ability == "wonder-guard" and m < 2:
        return 0.0
    if m >= 2 and dfn.ability in SUPER_EFFECTIVE_FILTERS:
        m *= SUPER_EFFECTIVE_FILTERS[dfn.ability]
    return m


Stages = dict[str, int]
NO_STAGES: Stages = {}


def stat(f: Fighter, k: str, stages: Stages | None = None) -> float:
    """Final stat with the held item and stat stages applied."""
    v = f.stats[k] * sets.ITEM_STAT.get(f.item or "", {}).get(k, 1.0)
    return v * sets.stage_mult((stages or NO_STAGES).get(k, 0))


def damage_pct(
    att_f: Fighter, att: Attack, dfn: Fighter,
    a_st: Stages | None = None, d_st: Stages | None = None, d_full: bool = False,
) -> float:
    physical = att.damage_class == "physical"
    a = stat(att_f, "attack" if physical else "sp_attack", a_st)
    if att.name == "Foul Play":  # uses the target's Attack
        a = stat(dfn, "attack", d_st)
    elif att.name == "Body Press":  # uses the user's Defense
        a = stat(att_f, "defense", a_st)
    if physical and att_f.ability in ("huge-power", "pure-power"):
        a *= 2
    # Assault Vest only boosts Sp. Def against attacks, which is all we model.
    d = max(1.0, stat(dfn, "defense" if physical else "sp_defense", d_st))
    power = att.power * (1.5 if att_f.ability == "technician" and att.power <= 60 else 1)
    base = ((2 * DEFAULT_LEVEL / 5 + 2) * power * a / d) / 50 + 2
    stab = (2.0 if att_f.ability == "adaptability" else 1.5) if att.type in att_f.types else 1.0
    acc = (att.accuracy or 100) / 100
    tm = type_mult(att, dfn)
    item = att_f.item or ""
    mod = sets.ITEM_DAMAGE.get(item, 1.0)
    if sets.TYPE_BOOST_ITEMS.get(item) == att.type:
        mod *= 1.2
    cls = sets.ITEM_CLASS_DAMAGE.get(item)
    if cls and cls[0] == att.damage_class:
        mod *= cls[1]
    if item == "expert-belt" and tm >= 2:
        mod *= sets.EXPERT_BELT
    if d_full and dfn.ability in ("multiscale", "shadow-shield"):
        mod *= 0.5
    dmg = base * stab * tm * AVG_ROLL * acc * mod
    return 100 * dmg / max(1, dfn.stats["hp"])


def hits_to_ko(pct: float) -> int:
    return NO_KO if pct <= 0 else max(1, math.ceil(100 / pct))


def best_hit(
    att_f: Fighter, dfn: Fighter, moves: list[Attack] | None = None,
    a_st: Stages | None = None, d_st: Stages | None = None,
) -> Hit:
    best: Hit = Hit(None, 1.0, 0.0, NO_KO)
    for mv in att_f.moves if moves is None else moves:
        pct = damage_pct(att_f, mv, dfn, a_st, d_st)
        if pct > best.pct:
            best = Hit(mv, type_mult(mv, dfn), pct, hits_to_ko(pct))
    return best


def complete_moveset(f: Fighter, targets: list[Fighter]) -> list[Attack]:
    """Fill open move slots greedily from the learnset, maximising damage vs targets.

    Each target's value is the best capped damage % the set lands on it, so a new
    move only scores where it beats what the set already does (coverage, not
    redundant STAB).
    """
    chosen = list(f.set_attacks)
    if not targets:
        return chosen

    def value(ms: list[Attack]) -> float:
        return sum(min(100.0, best_hit(f, t, ms).pct) for t in targets)

    current = value(chosen)
    for _ in range(f.open_slots):
        taken = {m.move_id for m in chosen}
        best_mv, best_val = None, current
        for cand in f.pool:
            if cand.move_id in taken:
                continue
            v = value([*chosen, cand])
            if v > best_val + 0.5:
                best_mv, best_val = cand, v
        if best_mv is None:
            break
        chosen.append(best_mv)
        current = best_val
    return chosen


def _prune(pool: list[Attack]) -> list[Attack]:
    """Keep the strongest 2 moves per (type, damage class) to bound the search."""
    groups: dict[tuple[str, str], list[Attack]] = defaultdict(list)
    for a in pool:
        groups[(a.type, a.damage_class)].append(a)
    out: list[Attack] = []
    for moves in groups.values():
        moves.sort(key=lambda a: -(a.power * (a.accuracy or 100)))
        out.extend(moves[:2])
    return out


def _attack_from_slot(mv) -> Attack | None:
    if mv.damage_class not in ("physical", "special") or not mv.type or not mv.power:
        return None
    return Attack(
        move_id=mv.move_id, name=mv.name, type=mv.type, damage_class=mv.damage_class,
        power=mv.power, accuracy=mv.accuracy, priority=mv.priority,
    )


async def load_fighters(session: AsyncSession, members: list[TeamMemberOut]) -> list[Fighter]:
    """Build fighters (stats, ability-aware defence, set moves, learnable pool)."""
    ids = {m.pokemon_id for m in members}
    pools: dict[int, list[Attack]] = defaultdict(list)
    if ids:
        rows = (
            await session.execute(
                select(PokemonMove)
                .options(selectinload(PokemonMove.move).selectinload(Move.type))
                .where(PokemonMove.pokemon_id.in_(ids))
            )
        ).scalars().all()
        seen: set[tuple[int, int]] = set()
        for pm in rows:
            mv = pm.move
            if (
                (pm.pokemon_id, mv.id) in seen
                or mv.damage_class not in ("physical", "special")
                or not mv.power
                or mv.type is None
                or mv.identifier in EXCLUDED_MOVES
            ):
                continue
            seen.add((pm.pokemon_id, mv.id))
            pools[pm.pokemon_id].append(
                Attack(
                    move_id=mv.id, name=mv.name, type=mv.type.identifier,
                    damage_class=mv.damage_class, power=mv.power, accuracy=mv.accuracy,
                    priority=mv.priority or 0, learned=True,
                )
            )

    out: list[Fighter] = []
    for m in members:
        ability = ability_key(m.ability.name) if m.ability else None
        type_ids = await matchups.ids_for(session, m.types)
        mults = await matchups.defense_multipliers(session, type_ids)
        for t, f in ABILITY_DEFENSE.get(ability or "", {}).items():
            mults[t] = mults.get(t, 1.0) * f
        set_attacks = [a for a in (_attack_from_slot(mv) for mv in m.moves) if a]
        physical = m.final_stats["attack"] >= m.final_stats["sp_attack"]
        out.append(
            Fighter(
                slot=m.slot, name=m.name, types=m.types, stats=m.final_stats, ability=ability,
                def_mults=mults, set_attacks=set_attacks,
                open_slots=max(0, MAX_MOVES - len(m.moves)),
                pool=_prune(pools.get(m.pokemon_id, [])),
                item=sets.key(m.item.name) if m.item else None,
                setup=sets.best_setup(
                    [(mv.name, sets.key(mv.name) or "") for mv in m.moves], physical
                ),
            )
        )
    return out


async def generic_targets(session: AsyncSession) -> list[Fighter]:
    """One neutral-stat dummy per type, for coverage when there's no opponent."""
    stats = final_stats({k: 90 for k in STAT_KEYS})
    out: list[Fighter] = []
    for i, t in enumerate(sorted(await matchups.all_type_idents(session))):
        mults = await matchups.defense_multipliers(session, await matchups.ids_for(session, [t]))
        out.append(
            Fighter(slot=100 + i, name=t, types=[t], stats=stats, ability=None, def_mults=mults)
        )
    return out


# ── one-on-one duel ──────────────────────────────────────────────────────────
MAX_TURNS = 12


@dataclass(frozen=True)
class Duel:
    outcome: str  # "win" | "lose" | "even", from `a`'s side
    a_hit: Hit  # the attack `a` lands with (after any setup)
    b_hit: Hit
    a_turns: int  # turns `a` needs to KO `b` with its plan (setup turn included)
    b_turns: int
    first: str  # who acts first on the opening turn: "ours" (a) | "theirs" (b) | "tie"
    a_setup: str | None  # setup move `a` uses first, if that's its better plan
    b_setup: str | None
    notes: tuple[str, ...] = ()  # set effects that changed this pairing
    log: tuple[dict, ...] = ()  # turn-by-turn events of the chosen plans


def _speed(f: Fighter, st: Stages) -> float:
    return stat(f, "speed", st)


def _turns_to_ko(att: Fighter, dfn: Fighter, plan: str, a_st: Stages, d_st: Stages) -> int:
    """Turns `att` needs on its own (ignoring being KO'd), incl. a setup turn."""
    st = dict(a_st)
    extra = 0
    if plan == "setup" and att.setup:
        for k, v in att.setup.boosts.items():
            st[k] = st.get(k, 0) + v
        extra = 1
    first = best_hit(att, dfn, None, st, d_st).pct
    if first <= 0:
        return NO_KO
    hp, n = 100.0, 0
    full = True
    heal = sets.LEFTOVERS_HEAL if dfn.item == "leftovers" or (
        dfn.item == "black-sludge" and "poison" in dfn.types
    ) else 0.0
    sash = dfn.item == "focus-sash" or dfn.ability == "sturdy"
    while hp > 0 and n < MAX_TURNS:
        mv = best_hit(att, dfn, None, st, d_st).attack
        pct = damage_pct(att, mv, dfn, st, d_st, d_full=full) if mv else 0.0
        if sash and full and pct >= 100:
            hp = 1.0
        else:
            hp -= pct
        full = False
        n += 1
        if hp > 0:
            hp = min(100.0, hp + heal)
    return extra + (n if hp <= 0 else NO_KO)


def _simulate(
    a: Fighter, pa: str, b: Fighter, pb: str, log: list[dict] | None = None
) -> tuple[str, int, float, float]:
    """Play the pairing out. Returns (result for a, turn, a hp left, b hp left).
    With `log`, every action is appended as an event dict for the battle text."""

    def ev(turn: int, side: str, kind: str, **kw: object) -> None:
        if log is not None:
            log.append({"turn": turn, "side": side, "kind": kind, **kw})

    hp = {"a": 100.0, "b": 100.0}
    st: dict[str, Stages] = {"a": {}, "b": {}}
    # Intimidate lands on entry.
    if a.ability == "intimidate":
        st["b"]["attack"] = -1
        ev(0, "a", "intimidate")
    if b.ability == "intimidate":
        st["a"]["attack"] = -1
        ev(0, "b", "intimidate")
    f = {"a": a, "b": b}
    plan = {"a": pa, "b": pb}
    used = {"a": False, "b": False}
    sash = {k: f[k].item == "focus-sash" or f[k].ability == "sturdy" for k in f}
    berry = {k: f[k].item == "sitrus-berry" for k in f}
    dealt: dict[str, float] = {}  # each side's latest hit, for the "close fight" read
    for turn in range(1, MAX_TURNS + 1):
        acts: dict[str, tuple[str, Attack | None]] = {}
        for k, o in (("a", "b"), ("b", "a")):
            if plan[k] == "setup" and f[k].setup and not used[k]:
                acts[k] = ("setup", None)
            else:
                acts[k] = ("attack", best_hit(f[k], f[o], None, st[k], st[o]).attack)

        prio = {
            k: (mv.priority if mv else 0, _speed(f[k], st[k])) for k, (_, mv) in acts.items()
        }
        order = ["a", "b"] if prio["a"] >= prio["b"] else ["b", "a"]
        simultaneous = prio["a"] == prio["b"]
        for k in order:
            o = "b" if k == "a" else "a"
            if hp[k] <= 0 and not simultaneous:
                continue
            kind, mv = acts[k]
            if kind == "setup":
                for s_k, v in f[k].setup.boosts.items():  # type: ignore[union-attr]
                    st[k][s_k] = max(-6, min(6, st[k].get(s_k, 0) + v))
                used[k] = True
                ev(turn, k, "setup", move=f[k].setup.name, boosts=f[k].setup.boosts)  # type: ignore[union-attr]
                continue
            if not mv:
                ev(turn, k, "nothing")
                continue
            pct = damage_pct(f[k], mv, f[o], st[k], st[o], d_full=hp[o] >= 100)
            if sash[o] and hp[o] >= 100 and pct >= 100:
                hp[o] = 1.0
                sash[o] = False
                ev(turn, k, "attack", move=mv.name, type=mv.type, mult=type_mult(mv, f[o]),
                   pct=round(min(pct, 99.0), 1), hp=1.0)
                ev(turn, o, "sash", item=f[o].item, ability=f[o].ability)
            else:
                hp[o] -= pct
                ev(turn, k, "attack", move=mv.name, type=mv.type, mult=type_mult(mv, f[o]),
                   pct=round(pct, 1), hp=round(max(0.0, hp[o]), 1))
            dealt[k] = pct
            if f[k].item == "life-orb" and pct > 0:
                hp[k] -= sets.LIFE_ORB_RECOIL
                ev(turn, k, "recoil", pct=sets.LIFE_ORB_RECOIL, hp=round(max(0.0, hp[k]), 1))
            if hp[o] <= 0:
                ev(turn, o, "faint")
            if hp[k] <= 0:
                ev(turn, k, "faint")
        a_down, b_down = hp["a"] <= 0, hp["b"] <= 0
        if a_down or b_down:
            if a_down and b_down:
                return "even", turn, hp["a"], hp["b"]
            res = "lose" if a_down else "win"
            # A long slugfest decided by one hit is close, not a clear win.
            loser = "a" if a_down else "b"
            winner = "b" if a_down else "a"
            if turn >= 4 and hp[winner] <= dealt.get(loser, 0):
                return "even", turn, hp["a"], hp["b"]
            return res, turn, hp["a"], hp["b"]
        for k in ("a", "b"):
            heals = f[k].item == "leftovers" or (
                f[k].item == "black-sludge" and "poison" in f[k].types
            )
            if heals and hp[k] < 100:
                hp[k] = min(100.0, hp[k] + sets.LEFTOVERS_HEAL)
                ev(turn, k, "heal", item=f[k].item, pct=sets.LEFTOVERS_HEAL, hp=round(hp[k], 1))
            if hp[k] <= 50 and berry[k]:
                hp[k] = min(100.0, hp[k] + sets.SITRUS_HEAL)
                berry[k] = False
                ev(turn, k, "heal", item="sitrus-berry", pct=sets.SITRUS_HEAL, hp=round(hp[k], 1))
            if f[k].ability == "speed-boost":
                st[k]["speed"] = min(6, st[k].get("speed", 0) + 1)
                ev(turn, k, "speed-boost")
    return "even", MAX_TURNS, hp["a"], hp["b"]


_RANK = {"win": 1, "even": 0, "lose": -1}


def duel(a: Fighter, b: Fighter) -> Duel:
    """Best plan for each side (attack straight away, or set up once first),
    each assuming the other answers with its own best plan."""
    pa_opts = ["attack"] + (["setup"] if a.setup else [])
    pb_opts = ["attack"] + (["setup"] if b.setup else [])
    res = {(pa, pb): _simulate(a, pa, b, pb) for pa in pa_opts for pb in pb_opts}

    def val_a(pa: str, pb: str) -> tuple[int, float]:
        r, _, ha, hb = res[(pa, pb)]
        return (_RANK[r], ha - hb)

    # Each side picks the plan whose worst case is best for it.
    pa = max(pa_opts, key=lambda p: min(val_a(p, q) for q in pb_opts))
    pb = max(pb_opts, key=lambda q: min((-val_a(p, q)[0], -val_a(p, q)[1]) for p in pa_opts))
    outcome = res[(pa, pb)][0]
    log: list[dict] = []
    _simulate(a, pa, b, pb, log)

    a_st: Stages = {"attack": -1} if b.ability == "intimidate" else {}
    b_st: Stages = {"attack": -1} if a.ability == "intimidate" else {}
    a_boost = dict(a_st)
    if pa == "setup" and a.setup:
        for k, v in a.setup.boosts.items():
            a_boost[k] = a_boost.get(k, 0) + v
    b_boost = dict(b_st)
    if pb == "setup" and b.setup:
        for k, v in b.setup.boosts.items():
            b_boost[k] = b_boost.get(k, 0) + v
    a_hit = best_hit(a, b, None, a_boost, b_boost)
    b_hit = best_hit(b, a, None, b_boost, a_boost)

    pa_mv, pb_mv = a_hit.attack, b_hit.attack
    first_a = (0 if pa == "setup" else (pa_mv.priority if pa_mv else 0), _speed(a, a_st))
    first_b = (0 if pb == "setup" else (pb_mv.priority if pb_mv else 0), _speed(b, b_st))
    first = "ours" if first_a > first_b else "theirs" if first_b > first_a else "tie"

    notes: list[str] = []
    for f, plan in ((a, pa), (b, pb)):
        if plan == "setup" and f.setup:
            notes.append(f"{f.name} sets up {f.setup.name} first")
        if f.item and (n := sets.item_note(f.item)):
            notes.append(f"{f.name}: {f.item.replace('-', ' ').title()} — {n}")
        if f.ability in ("speed-boost", "intimidate", "sturdy", "multiscale", "shadow-shield"):
            label = f.ability.replace("-", " ").title()
            notes.append(f"{f.name}: {label} — {sets.ABILITY_NOTES[f.ability]}")
    return Duel(
        outcome=outcome,
        a_hit=a_hit,
        b_hit=b_hit,
        a_turns=_turns_to_ko(a, b, pa, a_st, b_boost),
        b_turns=_turns_to_ko(b, a, pb, b_st, a_boost),
        first=first,
        a_setup=a.setup.name if pa == "setup" and a.setup else None,
        b_setup=b.setup.name if pb == "setup" and b.setup else None,
        notes=tuple(notes),
        log=tuple(log),
    )
