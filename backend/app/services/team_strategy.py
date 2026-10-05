"""Team strategy profile — *how* a team wants to win, not just its raw stats.

Six axes, each 0–100 and each traceable to concrete members and moves:

* **offense** — average best attacking base stat.
* **bulk** — average HP + Def + SpD.
* **speed** — average base Speed, plus credit for speed control (Tailwind,
  Trick Room, Thunder Wave, priority…).
* **setup** — members with a stat-boosting move (Swords Dance, Dragon Dance…)
  or a snowballing ability (Speed Boost, Moxie…).
* **stall** — reliable recovery + passive damage/status, weighted by bulk.
* **support** — hazards, screens, pivoting, status and other utility.

A move *on the slot* counts in full; a move the species can legally *learn*
counts half (it's an option, not a plan). Moves nearly everything learns by TM
(Protect, Toxic, Rest, Substitute) only count when actually set, so the
learnable credit can't inflate every team. Built only from ingested data.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.moves import Move, PokemonMove
from app.schemas.team import TeamMemberOut
from app.services.stats import as_built

SETUP = {
    "swords-dance",
    "dragon-dance",
    "nasty-plot",
    "calm-mind",
    "bulk-up",
    "quiver-dance",
    "shell-smash",
    "iron-defense",
    "agility",
    "rock-polish",
    "autotomize",
    "coil",
    "shift-gear",
    "belly-drum",
    "curse",
    "work-up",
    "growth",
    "tail-glow",
    "geomancy",
    "victory-dance",
    "tidy-up",
    "no-retreat",
    "clangorous-soul",
    "cosmic-power",
    "amnesia",
    "cotton-guard",
    "acid-armor",
    "hone-claws",
    "howl",
    "fillet-away",
    "trailblaze",
}
SETUP_ABILITIES = {
    "speed-boost",
    "moxie",
    "beast-boost",
    "chilling-neigh",
    "grim-neigh",
    "as-one",
    "simple",
}
RECOVERY = {
    "recover",
    "roost",
    "soft-boiled",
    "milk-drink",
    "slack-off",
    "moonlight",
    "morning-sun",
    "synthesis",
    "wish",
    "rest",
    "shore-up",
    "strength-sap",
    "heal-order",
    "jungle-healing",
    "lunar-blessing",
    "leech-seed",
    "aqua-ring",
    "ingrain",
    "pain-split",
}
STALL_ABILITIES = {"regenerator", "poison-heal", "magic-guard", "unaware", "natural-cure"}
CHIP = {
    "toxic",
    "will-o-wisp",
    "leech-seed",
    "stealth-rock",
    "spikes",
    "toxic-spikes",
    "protect",
    "substitute",
    "haze",
    "whirlwind",
    "roar",
    "dragon-tail",
    "circle-throw",
    "salt-cure",
    "infestation",
    "whirlpool",
    "fire-spin",
    "sand-tomb",
    "baneful-bunker",
    "spiky-shield",
    "kings-shield",
}
SPEED_CONTROL = {
    "tailwind",
    "trick-room",
    "thunder-wave",
    "icy-wind",
    "electroweb",
    "sticky-web",
    "glare",
    "scary-face",
    "string-shot",
    "bulldoze",
    "rock-tomb",
    "low-sweep",
}
SUPPORT = {
    "stealth-rock",
    "spikes",
    "toxic-spikes",
    "sticky-web",
    "rapid-spin",
    "defog",
    "mortal-spin",
    "court-change",
    "reflect",
    "light-screen",
    "aurora-veil",
    "tailwind",
    "trick-room",
    "thunder-wave",
    "will-o-wisp",
    "toxic",
    "taunt",
    "encore",
    "u-turn",
    "volt-switch",
    "flip-turn",
    "parting-shot",
    "teleport",
    "chilly-reception",
    "shed-tail",
    "knock-off",
    "heal-bell",
    "aromatherapy",
    "wish",
    "healing-wish",
    "helping-hand",
    "follow-me",
    "rage-powder",
    "fake-out",
    "yawn",
    "spore",
    "sleep-powder",
    "haze",
    "memento",
    "trick",
    "switcheroo",
}
# Learnable by nearly everything via TM — only meaningful when actually chosen.
SET_ONLY = {"protect", "substitute", "rest", "toxic", "facade"}

LEARNABLE_WEIGHT = 0.35  # how much an unset-but-learnable move counts in the blended score

# Display names for move identifiers, filled by ``load_learnsets`` (falls back to title case).
MOVE_NAMES: dict[str, str] = {}


def slug(name: str) -> str:
    """'Swords Dance' → 'swords-dance' (PokéAPI identifiers)."""
    return name.strip().lower().replace("'", "").replace(".", "").replace(" ", "-")


def _nice(ident: str) -> str:
    return MOVE_NAMES.get(ident) or ident.replace("-", " ").title()


@dataclass
class Contributor:
    name: str
    moves: list[str]  # display names
    set: bool  # True when on the slot (or a chosen ability), False when only learnable


@dataclass
class Axis:
    key: str
    label: str
    score: int  # blended: set moves in full + learnable at LEARNABLE_WEIGHT
    now: int  # only what's actually on the team (set moves / chosen abilities)
    potential: int  # if every learnable option were used
    detail: str
    contributors: list[Contributor] = field(default_factory=list)


@dataclass
class Strategy:
    style: str
    style_reason: str
    axes: list[Axis]


def _credit(
    member: TeamMemberOut,
    pool: set[str],
    learnable: set[str],
    ability_bonus: frozenset[str] | set[str] = frozenset(),
) -> tuple[bool, bool, Contributor | None]:
    """(has it set, could learn it, contributor) for one member against one move pool."""
    set_moves = [mv.name for mv in member.moves if slug(mv.name) in pool]
    if member.ability and slug(member.ability.name) in ability_bonus:
        set_moves.append(member.ability.name)
    if set_moves:
        return True, True, Contributor(member.name, set_moves, True)
    can = sorted(m for m in learnable & pool if m not in SET_ONLY)
    if can:
        return False, True, Contributor(member.name, [_nice(m) for m in can[:3]], False)
    return False, False, None


def _pct(x: float) -> int:
    return int(round(max(0.0, min(1.0, x)) * 100))


def score_strategy(members: list[TeamMemberOut], learnsets: dict[int, set[str]]) -> Strategy:
    """Pure scoring: members + each member's learnable move identifiers (by slot)."""
    n = max(len(members), 1)
    # Stats as built (EVs, IVs, nature), in base-stat terms.
    bs = [as_built(m.final_stats) if m.final_stats else m.base_stats for m in members]
    off = sum(max(b["attack"], b["sp_attack"]) for b in bs) / n
    bulk = sum(b["hp"] + b["defense"] + b["sp_defense"] for b in bs) / n
    spe = sum(b["speed"] for b in bs) / n

    def share(pool, ability_bonus=frozenset()):
        """(now, potential, blended) shares across members + contributors."""
        now = pot = blend = 0.0
        who: list[Contributor] = []
        for m in members:
            on, can, c = _credit(m, pool, learnsets.get(m.slot, set()), ability_bonus)
            now += on
            pot += can
            blend += 1.0 if on else LEARNABLE_WEIGHT if can else 0.0
            if c:
                who.append(c)
        return now / n, pot / n, blend / n, who

    setup = share(SETUP, SETUP_ABILITIES)
    support = share(SUPPORT)
    sc = share(SPEED_CONTROL)
    priority = [
        m
        for m in members
        if any((mv.priority or 0) > 0 and mv.damage_class != "status" for mv in m.moves)
    ]

    # Stall per member: recovery (60%) + chip/status (40%), scaled by that member's bulk.
    st_now = st_pot = st_blend = 0.0
    stall_who: list[Contributor] = []
    for m in members:
        learn = learnsets.get(m.slot, set())
        r_on, r_can, r_c = _credit(m, RECOVERY, learn, STALL_ABILITIES)
        c_on, c_can, c_c = _credit(m, CHIP, learn)
        b = as_built(m.final_stats) if m.final_stats else m.base_stats
        sturdy = min(1.0, (b["hp"] + b["defense"] + b["sp_defense"]) / 280)
        w = lambda on, can: 1.0 if on else LEARNABLE_WEIGHT if can else 0.0  # noqa: E731
        st_now += min(1.0, r_on * 0.6 + c_on * 0.4) * sturdy
        st_pot += min(1.0, r_can * 0.6 + c_can * 0.4) * sturdy
        st_blend += min(1.0, w(r_on, r_can) * 0.6 + w(c_on, c_can) * 0.4) * sturdy
        stall_who += [c for c in (r_c, c_c) if c]

    prio = 0.1 * len(priority) / n
    speed = (
        spe / 110 + 0.25 * sc[0] + prio,
        spe / 110 + 0.25 * sc[1] + prio,
        spe / 110 + 0.25 * sc[2] + prio,
    )
    prio_who = [
        Contributor(m.name, [mv.name for mv in m.moves if (mv.priority or 0) > 0], True)
        for m in priority
    ]

    def axis(key, label, now, pot, blend, detail, who=()):
        return Axis(key, label, _pct(blend), _pct(now), _pct(pot), detail, list(who))

    axes = [
        axis("offense", "Offense", off / 130, off / 130, off / 130, f"avg best attack {off:.0f}"),
        axis("bulk", "Bulk", bulk / 300, bulk / 300, bulk / 300, f"avg HP+Def+SpD {bulk:.0f}"),
        axis(
            "speed",
            "Speed",
            *speed,
            f"avg Speed {spe:.0f}" + (f" · {len(priority)} with priority" if priority else ""),
            sc[3] + prio_who,
        ),
        axis("setup", "Setup", *setup[:3], _detail(setup[3], "setup"), setup[3]),
        axis(
            "stall",
            "Stall",
            st_now / n,
            st_pot / n,
            st_blend / n,
            _detail(stall_who, "recovery or chip"),
            stall_who,
        ),
        axis("support", "Support", *support[:3], _detail(support[3], "utility"), support[3]),
    ]
    s = {a.key: a.score for a in axes}
    style = (
        "Stall"
        if s["stall"] >= 55 and s["offense"] < 60
        else "Setup offense"
        if s["setup"] >= 50 and s["offense"] >= 60
        else "Hyper offense"
        if s["speed"] >= 70 and s["offense"] >= 65
        else "Bulky offense"
        if s["bulk"] >= 65 and s["offense"] >= 60
        else "Utility balance"
        if s["support"] >= 55
        else "Offense"
        if s["offense"] >= 65
        else "Balance"
    )
    top = sorted(axes, key=lambda a: a.score, reverse=True)[:2]
    return Strategy(style, f"strongest in {top[0].label.lower()} and {top[1].label.lower()}", axes)


def _detail(who: list[Contributor], what: str) -> str:
    on = len({c.name for c in who if c.set})
    can = len({c.name for c in who if not c.set} - {c.name for c in who if c.set})
    if not who:
        return f"no {what} moves"
    parts = []
    if on:
        parts.append(f"{on} set")
    if can:
        parts.append(f"{can} could learn")
    return " · ".join(parts)


async def load_learnsets(
    session: AsyncSession, members: list[TeamMemberOut]
) -> dict[int, set[str]]:
    """Each member's learnable move identifiers that matter here, keyed by slot."""
    wanted = SETUP | RECOVERY | CHIP | SPEED_CONTROL | SUPPORT
    ids = {m.form_id or m.pokemon_id for m in members} | {m.pokemon_id for m in members}
    rows = (
        await session.execute(
            select(PokemonMove.pokemon_id, Move.identifier, Move.name)
            .join(Move, Move.id == PokemonMove.move_id)
            .where(PokemonMove.pokemon_id.in_(ids), Move.identifier.in_(wanted))
        )
    ).all()
    by_pokemon: dict[int, set[str]] = defaultdict(set)
    for pid, ident, name in rows:
        by_pokemon[pid].add(ident)
        MOVE_NAMES[ident] = name
    # A form uses its own learnset when it has one, else the species'.
    return {
        m.slot: by_pokemon.get(m.form_id or -1) or by_pokemon.get(m.pokemon_id, set())
        for m in members
    }


async def team_strategy(session: AsyncSession, members: list[TeamMemberOut]) -> Strategy:
    return score_strategy(members, await load_learnsets(session, members))
