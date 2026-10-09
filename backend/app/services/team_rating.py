"""Team rating: one deterministic model behind every grade a client shows.

Built only from the analysis engine's output (``TeamAnalysis``) and the type chart. Six
area grades (Coverage, Defence, Speed, Roles, Sets, Roster), each with a one-line
verdict and a fix, roll up into an overall /100 that is scaled down until the roster
has six different species. Thresholds mirror the engine's role rules in
``team_analysis``: fast attacker = Speed 100+, wall = HP+Def+SpD 280+, wallbreaker =
best attacking stat 110+.

Ported from the website's ``lib/teamEval.ts`` and pinned to its output by golden cases
(``tests/test_team_rating.py``). It keeps JavaScript's numerics: ``Math.round`` rounds
half up (``js_round``), and a grade is read from the unrounded score.
"""

from __future__ import annotations

import math

from app.schemas.analysis import (
    AreaKey,
    Grade,
    MemberRole,
    RatingArea,
    TeamAnalysis,
    TeamRating,
    TypeCover,
    TypeThreat,
)
from app.services.matchups import ATTACK_ORDER

FAST_SPEED = 100

# How much each area counts towards the overall rating.
WEIGHTS: dict[str, float] = {
    "coverage": 0.22,
    "defence": 0.22,
    "roles": 0.15,
    "speed": 0.14,
    "sets": 0.15,
    "roster": 0.12,
}

Chart = dict[str, dict[str, float]]


def js_round(x: float) -> int:
    """JavaScript's ``Math.round``: half rounds up (Python's ``round`` rounds to even)."""
    return math.floor(x + 0.5)


def grade_of(score: float) -> Grade:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _clamp(x: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, x))


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _or_list(xs: list[str]) -> str:
    return "".join(xs) if len(xs) < 2 else f"{', '.join(xs[:-1])} or {xs[-1]}"


def _s(n: int) -> str:
    return "s" if n > 1 else ""


def rate_team(size: int, a: TeamAnalysis, chart: Chart) -> TeamRating:
    def eff(atk: str, d: str) -> float:
        return chart.get(atk, {}).get(d, 1)

    members = a.defensive.matrix
    stab = [t for m in members for t in m.types]

    # Coverage — STAB plus moves actually on the slots; learnable-only moves are reported
    # separately.
    set_types = [t for t in a.offensive.coverage_types if t not in a.offensive.from_learnset]

    def hits(atk: list[str], d: str) -> bool:
        return any(eff(t, d) >= 2 for t in atk)

    cover = [
        TypeCover(
            type=d,
            now=hits(stab + set_types, d),
            learnable=hits(stab + a.offensive.coverage_types, d),
        )
        for d in ATTACK_ORDER
    ]
    now = sum(c.now for c in cover)
    could = sum(c.learnable for c in cover)
    missing = [_cap(c.type) for c in cover if not c.now]

    # Defence — per attacking type, 4× weaknesses count double, resists and immunities offset them.
    threats: list[TypeThreat] = []
    for t in ATTACK_ORDER:
        mult = [m.multipliers.get(t, 1) for m in members]
        weak = sum(2 if x >= 4 else 1 if x >= 2 else 0 for x in mult)
        resist = sum(1 for x in mult if x < 1)
        threats.append(
            TypeThreat(
                type=t,
                weak=weak,
                resist=resist,
                members=sum(1 for x in mult if x >= 2),
                quad=sum(1 for x in mult if x >= 4),
                problem=weak >= 2 and weak > resist,
            )
        )
    problems = sorted((t for t in threats if t.problem), key=lambda p: -(p.weak - p.resist))

    # Speed and roles — straight from the engine's per-member stats.
    # Speed counts the set: Choice Scarf, Speed Boost and speed-raising setup lift a member.
    roles = a.roles.members

    def spe(r: MemberRole) -> int:
        return r.eff_speed if r.eff_speed is not None else r.speed

    fastest = sorted(roles, key=lambda r: -spe(r))[0] if roles else None
    fast_count = sum(1 for r in roles if spe(r) >= FAST_SPEED)
    set_members = a.sets.members if a.sets else []
    priority_users = [m.name for m in set_members if m.priority]
    missing_roles = [r.split(" / ")[0] for r in a.roles.missing_roles]

    areas: list[RatingArea] = []

    def push(key: AreaKey, label: str, score: float, headline: str, fix: str | None) -> None:
        areas.append(
            RatingArea(
                key=key,
                label=label,
                score=js_round(_clamp(score)),
                grade=grade_of(_clamp(score)),
                headline=headline,
                fix=fix,
            )
        )

    push(
        "coverage",
        "Coverage",
        (now / 15) * 100,  # 15+ of 18 is excellent; full 18 is rarely reachable
        f"Hits {now} of 18 types super-effectively",
        None
        if now >= 15
        else f"Learnable moves would reach {could} of 18; add them to the empty move slots."
        if could > now
        else f"Nothing hits {_or_list(missing[:3])} hard. Add a move or member that does.",
    )

    worst = problems[0] if problems else None
    if worst:
        resisters = sorted(
            (d for d in ATTACK_ORDER if eff(worst.type, d) < 1), key=lambda d: eff(worst.type, d)
        )
        quad = (
            f" ({'' if worst.quad == worst.members else f'{worst.quad} '}for 4×)"
            if worst.quad
            else ""
        )
        resists = (
            f"only {worst.resist} resist{'' if worst.resist > 1 else 's'}"
            if worst.resist
            else "nothing resists it"
        )
        defence_fix: str | None = (
            f"{_cap(worst.type)} hits {worst.members} member{_s(worst.members)}"
            f" super-effectively{quad}"
            f" and {resists} — add a {_or_list([_cap(d) for d in resisters[:2]])} type."
        )
    else:
        defence_fix = None
    push(
        "defence",
        "Defence",
        100 - sum(18 + 8 * (p.weak - p.resist - 1) for p in problems),
        "No type hits several members unchecked"
        if not problems
        else f"{len(problems)} weak spot{_s(len(problems))}: "
        f"{', '.join(_cap(p.type) for p in problems[:3])}",
        defence_fix,
    )

    if fastest:
        # Priority attacks partly make up for a slow team.
        speed_score = ((spe(fastest) - 50) / (FAST_SPEED + 10 - 50)) * 100 + (
            0 if fast_count else 12 * min(2, len(priority_users))
        )
        if fast_count:
            speed_head = (
                f"{fast_count} fast member{_s(fast_count)} (Speed {FAST_SPEED}+ with their sets)"
            )
        else:
            prio = f" · priority on {', '.join(priority_users)}" if priority_users else ""
            speed_head = f"Fastest is {fastest.name} at Speed {spe(fastest)}{prio}"
    else:
        speed_score, speed_head = 0, "No members yet"
    push(
        "speed",
        "Speed",
        speed_score,
        speed_head,
        None
        if fast_count
        else f"Nothing reaches Speed {FAST_SPEED} — add a fast attacker, a Choice Scarf"
        " or a speed-boosting move.",
    )

    push(
        "roles",
        "Roles",
        ((3 - len(missing_roles)) / 3) * 100,
        f"Missing {_or_list(missing_roles)}"
        if missing_roles
        else "Has a fast attacker, a wall and a wallbreaker",
        f"Add a {missing_roles[0]}." if missing_roles else None,
    )

    # Sets — held items, abilities and set moves (setup, priority, recovery, support).
    if set_members:
        n = len(set_members)
        avg = sum(m.score for m in set_members) / n
        no_item = [m for m in set_members if not m.item]
        no_ability = [m for m in set_members if not m.ability]
        thin = [m for m in set_members if m.moves_set < 4]
        setup = [m for m in set_members if m.setup]
        bits = [
            f"{n - len(no_item)}/{n} hold an item",
            f"{len(setup)} can set up" if setup else None,
            f"{sum(m.moves_set for m in set_members)}/{n * 4} moves set",
        ]

        def names(xs: list) -> str:
            return _or_list([x.name for x in xs[:3]]).replace(" or ", " and ", 1)

        if len(thin) > n / 2:
            sets_fix: str | None = (
                f"{len(thin)} members have empty move slots. "
                "Set their moves so the matchups use what they'll really click."
            )
        elif no_item:
            sets_fix = (
                f"{names(no_item)} {'hold' if len(no_item) > 1 else 'holds'} no item; "
                "Life Orb, a Choice item or Leftovers change damage and bulk."
            )
        elif no_ability:
            sets_fix = f"Pick an ability for {names(no_ability)}."
        elif not setup and not priority_users:
            sets_fix = (
                "No setup or priority moves. "
                "A Swords Dance or Dragon Dance user can snowball a game."
            )
        else:
            sets_fix = None
        push("sets", "Sets", avg, " · ".join(b for b in bits if b), sets_fix)

    # Standard rules allow one of each species, so a repeat only counts once.
    member_names = [m.name for m in members]
    dupes = list(
        dict.fromkeys(nm for i, nm in enumerate(member_names) if member_names.index(nm) != i)
    )
    unique = size - (len(member_names) - len(set(member_names)))
    if dupes:
        roster_fix: str | None = (
            f"Only one of each species is allowed. Swap the second {dupes[0]} for something new."
        )
    elif size < 6:
        roster_fix = (
            f"Fill {6 - size} more slot{_s(6 - size)}"
            " — every other grade firms up with a full team."
        )
    else:
        roster_fix = None
    push(
        "roster",
        "Roster",
        (unique / 6) * 100,
        f"{size} of 6 slots filled{f' · {", ".join(dupes)} twice' if dupes else ''}",
        roster_fix,
    )

    # Small rosters look artificially safe (fewer members, fewer shared weaknesses), so the
    # overall is scaled by how full the team is: a missing slot is a missing sixth of the
    # team. 5 distinct → ×5/6, 3 → ×½; only six different species can reach 100.
    raw = js_round(sum(x.score * WEIGHTS[x.key] for x in areas))
    ceiling = js_round((100 * unique) / 6)
    overall = raw if unique >= 6 else js_round((raw * unique) / 6)
    return TeamRating(
        overall=overall,
        grade=grade_of(overall),
        capped=unique < 6,
        ceiling=ceiling,
        areas=areas,
        cover=cover,
        threats=threats,
        fast_speed=FAST_SPEED,
    )
