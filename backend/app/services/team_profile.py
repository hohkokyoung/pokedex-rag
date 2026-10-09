"""Team profile: "what kind of team is this?" at a glance.

Derived only from ingested data: each member's stats as built (EVs, IVs and nature
included), its typing and set moves, and the team rating. Thresholds match the analysis
engine's role rules (fast = Speed 100+, wall = HP+Def+SpD 280+, wallbreaker = 110+).

Ported from the website's ``lib/teamProfile.ts`` and pinned to its output by golden
cases (``tests/test_team_rating.py``), so it rounds half up like JavaScript.
"""

from __future__ import annotations

from collections import Counter

from app.schemas.analysis import SpeedEntry, TeamAnalysis, TeamProfile, TeamRating, TypeNet
from app.schemas.team import TeamOut
from app.services.stats import STAT_KEYS, as_built
from app.services.team_rating import FAST_SPEED, js_round


def _avg(xs: list[int]) -> int:
    return js_round(sum(xs) / len(xs)) if xs else 0


def _title(s: str) -> str:
    return s[:1].upper() + s[1:]


def _and_list(xs: list[str]) -> str:
    return "".join(xs) if len(xs) < 2 else f"{', '.join(xs[:-1])} and {xs[-1]}"


def _style(avg_speed: int, off: int, bulk: int) -> str:
    # From team averages, so the label is explainable by the numbers shown.
    if avg_speed >= 95 and off >= 100:
        return "Hyper offense"
    if avg_speed <= 65 and off >= 100:
        return "Slow powerhouse"
    if bulk >= 270 and off < 100:
        return "Defensive"
    if off >= 100 and bulk >= 240:
        return "Bulky offense"
    if off >= 100:
        return "Offense"
    return "Balance"


def profile_team(team: TeamOut, a: TeamAnalysis, rating: TeamRating) -> TeamProfile | None:
    species = team.members
    if not species:
        return None
    # Stats as built, so EVs, IVs and natures move the style, lean and speed reads.
    built = [
        as_built(m.final_stats, rnd=js_round) if m.final_stats else m.base_stats for m in species
    ]

    avg = {k: _avg([b.get(k, 0) for b in built]) for k in STAT_KEYS}
    avg_bst = _avg([sum(m.base_stats.get(k, 0) for k in STAT_KEYS) for m in species])
    off = _avg([max(b["attack"], b["sp_attack"]) for b in built])
    bulk = _avg([b["hp"] + b["defense"] + b["sp_defense"] for b in built])
    avg_speed = avg["speed"]
    style = _style(avg_speed, off, bulk)

    # A member leans physical/special when its better attacking stat is 10+ ahead.
    physical = sum(1 for b in built if b["attack"] >= b["sp_attack"] + 10)
    special = sum(1 for b in built if b["sp_attack"] >= b["attack"] + 10)
    lean = "Physical" if physical > special else "Special" if special > physical else "Mixed"

    speeds = sorted(
        (
            SpeedEntry(name=m.name, speed=b["speed"], sprite=m.sprite_url)
            for m, b in zip(species, built, strict=True)
        ),
        key=lambda s: -s.speed,
    )
    fast_count = sum(1 for s in speeds if s.speed >= FAST_SPEED)

    freq = Counter(t for m in species for t in m.types)  # insertion order breaks ties
    core_types = [t for t, _ in sorted(freq.items(), key=lambda kv: -kv[1])]

    # Net per attacking type, so a one-Pokémon team still shows its weaknesses
    # (the Defence grade separately only penalises types hitting 2+ members).
    weak_to = sorted(
        (TypeNet(type=t.type, net=t.weak - t.resist) for t in rating.threats if t.weak > t.resist),
        key=lambda w: -w.net,
    )
    strong_vs = [c.type for c in rating.cover if c.now]
    resists = sorted(
        (TypeNet(type=t.type, net=t.resist - t.weak) for t in rating.threats if t.resist > t.weak),
        key=lambda r: -r.net,
    )
    moves_set = sum(len(m.moves) for m in species)
    items = sum(1 for m in species if m.item)
    priority = sum(
        1
        for m in species
        for mv in m.moves
        if (mv.priority or 0) > 0 and mv.damage_class != "status"
    )

    speed_line = (
        f"{fast_count} fast member{'s' if fast_count > 1 else ''} (avg Speed {avg_speed})"
        if fast_count
        else f"nothing reaches Speed {FAST_SPEED} (avg {avg_speed})"
    )
    weak_line = (
        f"{_and_list([_title(w.type) for w in weak_to[:3]])}"
        f" {'hurt' if len(weak_to) > 1 else 'hurts'} it"
        if weak_to
        else "no type hits it unchecked"
    )
    lean_word = "Mixed-attacking" if lean == "Mixed" else lean
    core = "/".join(_title(t) for t in core_types[:2])
    gist = f"{lean_word} {style.lower()} on a {core} core — {speed_line}; {weak_line}."

    return TeamProfile(
        style=style,
        style_why=f"avg Speed {avg_speed} · attack {off} · bulk {bulk}",
        lean=lean,
        physical=physical,
        special=special,
        avg=avg,
        avg_bst=avg_bst,
        avg_speed=avg_speed,
        fast_count=fast_count,
        speeds=speeds,
        core_types=core_types,
        weak_to=weak_to,
        strong_vs=strong_vs,
        resists=resists,
        moves_set=moves_set,
        items=items,
        priority=priority,
        gist=gist,
    )
