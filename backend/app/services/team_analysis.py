"""Deterministic team analysis: defensive profile, offensive coverage, role
balance, per-slot optimization, and a vs-opponent diff.

No LLM here — every number comes from the ingested type chart, stats, abilities,
the moves set on each slot and the species' learnset (open move slots are filled
with the best learnable moves; see ``battle``). The coach endpoint (RAG) and the
UI both consume this report, so the same facts back the prose and the visuals.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ability, PokemonAbility
from app.schemas.analysis import (
    DefensiveProfile,
    DuelEvent,
    DuelOut,
    MatchupCell,
    MemberDefense,
    MemberRole,
    OffensiveProfile,
    OpponentThreat,
    PressurePoint,
    RoleProfile,
    ScoreRow,
    SetMember,
    SetProfile,
    SharedWeakness,
    SlotSuggestion,
    SuggestedMove,
    TeamAnalysis,
    Verdict,
    VsMember,
    VsOpponent,
)
from app.schemas.team import TeamMemberOut, TeamOut
from app.services import battle, matchups, sets
from app.services.stats import as_built
from app.services.team_profile import profile_team
from app.services.team_rating import rate_team

SHARED_WEAKNESS_MIN = 3  # ≥ this many members weak to one type = a team-wide hole

# Light keyword scoring to pick a "best" ability from a species' set without a
# full effect engine. Grounded in the ability's own effect text.
_ABILITY_KEYWORDS: dict[str, int] = {
    "boost": 3, "increase": 3, "raise": 3, "double": 4, "higher": 2, "power": 2,
    "immun": 4, "cannot be": 3, "prevent": 3, "protect": 2, "negat": 3,
    "restore": 2, "heal": 2, "weather": 2, "speed": 2, "critical": 2,
}


async def analyze(
    session: AsyncSession,
    team: TeamOut,
    opponent: TeamOut | None = None,
) -> TeamAnalysis:
    members = team.members

    # Move-aware fighters: ability-aware defence, set moves, learnset pool. Open
    # move slots are filled with the learnset moves that do the most damage to the
    # opponent (or, without one, to a neutral dummy of every type).
    fighters = await battle.load_fighters(session, members)
    foes = await battle.load_fighters(session, opponent.members) if opponent else []
    targets = foes or await battle.generic_targets(session)
    for f in fighters:
        f.moves = battle.complete_moveset(f, targets)
    for f in foes:
        f.moves = battle.complete_moveset(f, fighters)
    member_mults = {f.slot: f.def_mults for f in fighters}

    defensive = _defensive(members, member_mults)
    offensive = await _offensive(session, fighters)
    roles = _roles(members)
    set_profile = _sets(members)
    suggestions = await _suggestions(session, members, fighters)
    vs = _vs_opponent(members, fighters, opponent, foes) if opponent else None
    summary = _summary(len(members), defensive, offensive, roles, vs)

    analysis = TeamAnalysis(
        team_id=team.id,
        name=team.name,
        size=len(members),
        defensive=defensive,
        offensive=offensive,
        roles=roles,
        suggestions=suggestions,
        vs_opponent=vs,
        sets=set_profile,
        summary=summary,
    )
    # The grade describes the team on its own: with an opponent, empty move slots are
    # filled against them, which would move it. Clients read it from the opponent-free
    # analysis.
    if opponent is None and members:
        analysis.rating = rate_team(len(members), analysis, await matchups.type_chart(session))
        analysis.profile = profile_team(team, analysis, analysis.rating)
    return analysis


def _defensive(
    members: list[TeamMemberOut], member_mults: dict[int, dict[str, float]]
) -> DefensiveProfile:
    matrix: list[MemberDefense] = []
    weak_members: dict[str, list[str]] = defaultdict(list)
    for m in members:
        mult = member_mults[m.slot]
        weak_to = sorted((t for t, f in mult.items() if f > 1), key=lambda t: -mult[t])
        for t in weak_to:
            weak_members[t].append(m.name)
        matrix.append(
            MemberDefense(
                slot=m.slot,
                name=m.name,
                types=m.types,
                multipliers={t: round(f, 2) for t, f in mult.items() if f != 1.0},
                weak_to=weak_to,
            )
        )
    shared = [
        SharedWeakness(type=t, count=len(names), members=names)
        for t, names in weak_members.items()
        if len(names) >= SHARED_WEAKNESS_MIN
    ]
    shared.sort(key=lambda s: -s.count)
    return DefensiveProfile(matrix=matrix, shared_weaknesses=shared)


async def _offensive(session: AsyncSession, fighters: list[battle.Fighter]) -> OffensiveProfile:
    coverage = sorted({mv.type for f in fighters for mv in f.moves})
    off = await matchups.offense_multipliers(session, coverage)
    uncovered = sorted(d for d, fac in off.items() if fac < 1)
    not_super = sorted(d for d, fac in off.items() if fac < 2)

    set_types = {mv.type for f in fighters for mv in f.moves if not mv.learned}
    # Tips: learnable moves that reach a type nothing on the team can hit
    # super-effectively with its set moves or STAB.
    baseline = await matchups.offense_multipliers(
        session, sorted(set_types | {t for f in fighters for t in f.types})
    )
    tips: list[str] = []
    for f in fighters:
        for mv in f.moves:
            if not mv.learned:
                continue
            gained = sorted(
                d for d, fac in (await matchups.offense_multipliers(session, [mv.type])).items()
                if fac >= 2 and baseline.get(d, 1.0) < 2
            )
            if gained:
                label = mv.name if mv.name.lower() == mv.type else f"{mv.name} ({mv.type.title()})"
                tips.append(
                    f"{f.name} can learn {label} to hit "
                    f"{', '.join(g.title() for g in gained)} super-effectively."
                )
    return OffensiveProfile(
        coverage_types=coverage,
        used_move_coverage=any(f.set_attacks for f in fighters),
        uncovered_types=uncovered,
        not_super_effective=not_super,
        from_learnset=sorted(set(coverage) - set_types),
        tips=tips,
    )


def _classify(speed: int, offense: int, bulk: int) -> str:
    if bulk >= 280 and offense < 100:
        return "Wall"
    if speed >= 100 and offense >= 100:
        return "Fast attacker"
    if offense >= 110 and speed < 80:
        return "Wallbreaker"
    if offense >= 95:
        return "Attacker"
    if bulk >= 260:
        return "Tank"
    return "Balanced"


def _roles(members: list[TeamMemberOut]) -> RoleProfile:
    rows: list[MemberRole] = []
    for m in members:
        # Stats as built: EVs, IVs and nature move a member across the role thresholds.
        bs = as_built(m.final_stats) if m.final_stats else m.base_stats
        speed = bs["speed"]
        offense = max(bs["attack"], bs["sp_attack"])
        bulk = bs["hp"] + bs["defense"] + bs["sp_defense"]
        eff, note = _effective_speed(m)
        rows.append(
            MemberRole(
                slot=m.slot,
                name=m.name,
                role=_classify(speed, offense, bulk),
                speed=speed,
                offense=offense,
                bulk=bulk,
                bst=sum(m.base_stats.values()),
                eff_speed=eff,
                speed_note=note,
            )
        )

    missing: list[str] = []
    notes: list[str] = []
    if rows:
        if not any(r.speed >= 100 for r in rows):
            missing.append("fast attacker / speed control")
        if not any(r.bulk >= 280 for r in rows):
            missing.append("defensive wall")
        if not any(r.offense >= 110 for r in rows):
            missing.append("high-power wallbreaker")
        fastest = max(rows, key=lambda r: r.speed)
        notes.append(f"Fastest member: {fastest.name} (base Speed {fastest.speed}).")
        if sum(1 for r in rows if r.role in ("Fast attacker", "Attacker", "Wallbreaker")) >= 5:
            notes.append("Team leans heavily offensive — little defensive backbone.")
    return RoleProfile(members=rows, missing_roles=missing, notes=notes)


def _effective_speed(m: TeamMemberOut) -> tuple[int, str | None]:
    """Base Speed as the set plays it: Choice Scarf ×1.5, Iron Ball ×0.5, and
    Speed Boost / speed-raising setup counted as one stage (×1.5) up."""
    spe = (as_built(m.final_stats) if m.final_stats else m.base_stats)["speed"]
    item = sets.key(m.item.name) if m.item else None
    ability = sets.key(m.ability.name) if m.ability else None
    mult, why = sets.ITEM_STAT.get(item or "", {}).get("speed", 1.0), []
    if mult != 1.0:
        why.append(m.item.name)  # type: ignore[union-attr]
    if ability == "speed-boost":
        mult *= 1.5
        why.append("Speed Boost")
    else:
        spe_boosts = [
            (sets.SETUP_BOOSTS.get(sets.key(mv.name) or "", {}).get("speed", 0), mv.name)
            for mv in m.moves
        ]
        boost, move = max(spe_boosts, default=(0, ""))
        if boost > 0:
            mult *= sets.stage_mult(boost)
            why.append(move)
    eff = round(spe * mult)
    return eff, (f"{spe} → {eff} with {' + '.join(why)}" if why else None)


def _sets(members: list[TeamMemberOut]) -> SetProfile:
    out: list[SetMember] = []
    for m in members:
        ability = sets.key(m.ability.name) if m.ability else None
        item = sets.key(m.item.name) if m.item else None
        keys = [(mv, sets.key(mv.name) or "") for mv in m.moves]
        setup = [mv.name for mv, k in keys if k in sets.SETUP_BOOSTS]
        prio = [mv.name for mv, k in keys if (mv.priority or 0) > 0 and mv.damage_class != "status"]
        rec = [mv.name for mv, k in keys if k in sets.RECOVERY_MOVES]
        sup = [mv.name for mv, k in keys if k in sets.SUPPORT_MOVES]
        a_note = sets.ABILITY_NOTES.get(ability or "")
        i_note = sets.item_note(item)
        # Build score: ability and item chosen (more if we model their effect),
        # moves filled, and at least one move that does more than hit.
        score = (
            (15 + (10 if a_note else 0) if ability else 0)
            + (15 + (10 if i_note else 0) if item else 0)
            + round(30 * min(4, len(m.moves)) / 4)
            + (20 if setup or prio or rec or sup else 0)
        )
        out.append(
            SetMember(
                slot=m.slot, name=m.name,
                ability=m.ability.name if m.ability else None, ability_note=a_note,
                item=m.item.name if m.item else None, item_note=i_note,
                moves_set=len(m.moves), setup=setup, priority=prio, recovery=rec, support=sup,
                score=min(100, score),
            )
        )
    return SetProfile(members=out)


async def _suggestions(
    session: AsyncSession, members: list[TeamMemberOut], fighters: list[battle.Fighter]
) -> list[SlotSuggestion]:
    learned = {f.slot: [mv for mv in f.moves if mv.learned] for f in fighters}
    pokemon_ids = {m.pokemon_id for m in members}
    ability_by_pokemon: dict[int, list[tuple[str, str | None]]] = defaultdict(list)
    if pokemon_ids:
        rows = (
            await session.execute(
                select(PokemonAbility.pokemon_id, Ability.name, Ability.effect)
                .join(Ability, Ability.id == PokemonAbility.ability_id)
                .where(PokemonAbility.pokemon_id.in_(pokemon_ids))
                .order_by(PokemonAbility.slot)
            )
        ).all()
        for pid, name, effect in rows:
            ability_by_pokemon[pid].append((name, effect))

    out: list[SlotSuggestion] = []
    for m in members:
        ability_name, ability_reason = _best_ability(ability_by_pokemon.get(m.pokemon_id, []))
        nature, evs, rationale = _best_spread(m.name, m.base_stats)
        out.append(
            SlotSuggestion(
                slot=m.slot,
                name=m.name,
                recommended_ability=ability_name,
                ability_reason=ability_reason,
                recommended_nature=nature,
                recommended_evs=evs,
                rationale=rationale,
                recommended_moves=[
                    SuggestedMove(
                        name=mv.name, type=mv.type, damage_class=mv.damage_class,
                        power=mv.power, is_set=True,
                    )
                    for mv in m.moves
                ]
                + [
                    SuggestedMove(
                        name=mv.name, type=mv.type, damage_class=mv.damage_class,
                        power=mv.power, is_set=False,
                    )
                    for mv in learned.get(m.slot, [])
                ],
            )
        )
    return out


def _best_ability(abilities: list[tuple[str, str | None]]) -> tuple[str | None, str | None]:
    if not abilities:
        return None, None
    best_name, best_effect, best_score = abilities[0][0], abilities[0][1], -1
    for name, effect in abilities:
        text = (effect or "").lower()
        score = sum(weight for kw, weight in _ABILITY_KEYWORDS.items() if kw in text)
        if score > best_score:
            best_name, best_effect, best_score = name, effect, score
    return best_name, best_effect


def _best_spread(name: str, bs: dict[str, int]) -> tuple[str, dict[str, int], str]:
    atk, spa, spe = bs["attack"], bs["sp_attack"], bs["speed"]
    physical = atk >= spa
    off_key = "attack" if physical else "sp_attack"
    off_label = "Attack" if physical else "Sp. Atk"
    off_val = atk if physical else spa

    if spe >= 80:
        nature = "Jolly" if physical else "Timid"
        evs = {off_key: 252, "speed": 252, "hp": 4}
        rationale = (
            f"{name} pairs strong Speed (base {spe}) with {off_label} (base {off_val}); "
            f"a max-Speed max-{off_label} spread and a {nature} nature make it a fast attacker."
        )
    elif off_val >= 100:
        nature = "Adamant" if physical else "Modest"
        evs = {"hp": 252, off_key: 252, "defense" if physical else "sp_defense": 4}
        rationale = (
            f"{name} hits hard (base {off_label} {off_val}) but is slow (base Speed {spe}); "
            f"invest in bulk + {off_label} with a {nature} nature as a wallbreaker."
        )
    else:
        # Defensive investment toward the better defensive stat.
        def_key = "defense" if bs["defense"] >= bs["sp_defense"] else "sp_defense"
        nature = "Bold" if def_key == "defense" else "Calm"
        evs = {"hp": 252, def_key: 252, off_key: 4}
        rationale = (
            f"{name} has modest offenses; lean into its bulk (HP {bs['hp']}, "
            f"{def_key.replace('_', ' ')} {bs[def_key]}) with a {nature} spread as a wall."
        )
    return nature, evs, rationale


def _vs_opponent(
    members: list[TeamMemberOut],
    fighters: list[battle.Fighter],
    opponent: TeamOut,
    foes: list[battle.Fighter],
) -> VsOpponent:
    member_mults = {f.slot: f.def_mults for f in fighters}
    threats: list[OpponentThreat] = []
    exploited_types: set[str] = set()
    for foe in foes:
        threatened: list[str] = []
        via: set[str] = set()
        for our in fighters:
            se = [mv.type for mv in foe.moves if battle.type_mult(mv, our) >= 2]
            if se:
                threatened.append(our.name)
                via.update(se)
        if threatened:
            exploited_types.update(via)
            threats.append(
                OpponentThreat(
                    opponent_name=foe.name,
                    opponent_types=foe.types,
                    threatens=threatened,
                    via=sorted(via),
                )
            )

    h2h = _head_to_head(fighters, foes)

    advice: list[str] = []
    if h2h.verdict:
        advice.append(h2h.verdict.reason)
    # Which of our shared weaknesses does this opponent actually punish?
    for t in sorted(exploited_types):
        hit = [th.opponent_name for th in threats if t in th.via]
        n_ours = sum(1 for our in fighters if member_mults[our.slot].get(t, 1.0) >= 2)
        if n_ours >= SHARED_WEAKNESS_MIN:
            advice.append(
                f"{n_ours} of your Pokémon are weak to {t}, and {', '.join(hit)} can exploit it — "
                f"add a {t}-resist or a check."
            )
    unanswered = h2h.unanswered
    if unanswered and fighters:
        advice.append(
            "Nothing on your team clearly beats "
            + ", ".join(unanswered)
            + " one-on-one — add a check for "
            + ("it." if len(unanswered) == 1 else "them.")
        )
    if not threats:
        advice.append(
            "No opponent Pokémon has a super-effective move on your team — solid matchup."
        )
    return VsOpponent(
        opponent_id=opponent.id,
        opponent_name=opponent.name,
        threats=threats,
        advice=advice,
        our_pressure=h2h.pressure,
        our_members=[_vs_member(m) for m in members],
        their_members=[_vs_member(o) for o in opponent.members],
        cells=h2h.cells,
        scorecard=h2h.scorecard,
        verdict=h2h.verdict,
    )


# ── head-to-head ─────────────────────────────────────────────────────────────
# Each pairing is read from both sides' best move (set, or learnable for an open
# slot): damage % → hits to KO, and who moves first. A deterministic estimate,
# not a full battle simulator — items, key abilities and one setup turn are
# played out (battle.duel); no switching, status, weather or prediction.

_WEIGHTS = {"h2h": 0.45, "reach": 0.2, "damage": 0.2, "speed": 0.15}


@dataclass
class _HeadToHead:
    cells: list[MatchupCell]
    scorecard: list[ScoreRow]
    verdict: Verdict | None
    pressure: list[PressurePoint]
    unanswered: list[str]  # opponents nothing on our side beats one-on-one


def _vs_member(m: TeamMemberOut) -> VsMember:
    bs = as_built(m.final_stats) if m.final_stats else m.base_stats
    return VsMember(
        slot=m.slot,
        pokemon_id=m.pokemon_id,
        name=m.name,
        types=m.types,
        sprite_url=m.sprite_url,
        speed=m.final_stats.get("speed", bs.get("speed", 0)),
        bst=sum(m.base_stats.values()),
        role=_classify(
            bs["speed"],
            max(bs["attack"], bs["sp_attack"]),
            bs["hp"] + bs["defense"] + bs["sp_defense"],
        ),
    )


def _first(o: battle.Fighter, oh: battle.Hit, t: battle.Fighter, th: battle.Hit) -> str:
    """Who acts first with their chosen move: priority bracket, then Speed."""
    po = oh.attack.priority if oh.attack else 0
    pt = th.attack.priority if th.attack else 0
    if po != pt:
        return "ours" if po > pt else "theirs"
    so, st = o.stats["speed"], t.stats["speed"]
    return "ours" if so > st else "theirs" if st > so else "tie"


def _exchange(our_hko: int, their_hko: int, first: str) -> str:
    """Trade hits until someone faints; slow, near-equal slugfests count as close."""
    if min(our_hko, their_hko) >= battle.NO_KO:
        return "even"
    if min(our_hko, their_hko) >= 4 and abs(our_hko - their_hko) <= 1:
        return "even"
    if first == "ours":
        return "win" if our_hko <= their_hko else "lose"
    if first == "theirs":
        return "lose" if their_hko <= our_hko else "win"
    return "win" if our_hko < their_hko else "lose" if our_hko > their_hko else "even"


def _share(ours: float, theirs: float) -> float:
    total = ours + theirs
    return 0.5 if total <= 0 else ours / total


def _edge(share: float) -> str:
    return "ours" if share > 0.55 else "theirs" if share < 0.45 else "even"


def _head_to_head(ours: list[battle.Fighter], theirs: list[battle.Fighter]) -> _HeadToHead:
    cells: list[MatchupCell] = []
    for o in ours:
        for t in theirs:
            d = battle.duel(o, t)
            oh, th = d.a_hit, d.b_hit
            score = max(-3, min(3, d.b_turns - d.a_turns)) + (
                0.5 if d.first == "ours" else -0.5 if d.first == "theirs" else 0
            )
            cells.append(
                MatchupCell(
                    our_slot=o.slot,
                    their_slot=t.slot,
                    our_hit=oh.mult,
                    our_hit_type=oh.attack.type if oh.attack else None,
                    our_move=oh.attack.name if oh.attack else None,
                    our_move_learned=bool(oh.attack and oh.attack.learned),
                    our_pct=round(oh.pct, 1),
                    our_hko=d.a_turns,
                    their_hit=th.mult,
                    their_hit_type=th.attack.type if th.attack else None,
                    their_move=th.attack.name if th.attack else None,
                    their_move_learned=bool(th.attack and th.attack.learned),
                    their_pct=round(th.pct, 1),
                    their_hko=d.b_turns,
                    faster=d.first,
                    score=score,
                    outcome=d.outcome,
                    our_setup=d.a_setup,
                    their_setup=d.b_setup,
                    notes=list(d.notes),
                )
            )

    # Our offensive pressure: who on our side hits which opponents super-effectively.
    pressure: list[PressurePoint] = []
    by_slot = {t.slot: t for t in theirs}
    for o in ours:
        se = [c for c in cells if c.our_slot == o.slot and c.our_hit >= 2]
        if se:
            pressure.append(
                PressurePoint(
                    attacker=o.name,
                    attacker_types=o.types,
                    targets=[by_slot[c.their_slot].name for c in se],
                    via=sorted({c.our_hit_type for c in se if c.our_hit_type}),
                )
            )

    beaten = {c.their_slot for c in cells if c.outcome == "win"}
    unanswered = [t.name for t in theirs if t.slot not in beaten]

    if not ours or not theirs:
        return _HeadToHead(cells, [], None, pressure, unanswered)

    wins = sum(1 for c in cells if c.outcome == "win")
    losses = sum(1 for c in cells if c.outcome == "lose")
    evens = len(cells) - wins - losses
    our_reach = len({c.their_slot for c in cells if c.our_hit >= 2})
    their_reach = len({c.our_slot for c in cells if c.their_hit >= 2})
    our_reach_f, their_reach_f = our_reach / len(theirs), their_reach / len(ours)
    our_dmg = sum(min(100.0, c.our_pct) for c in cells) / len(cells)
    their_dmg = sum(min(100.0, c.their_pct) for c in cells) / len(cells)
    # Speed as the sets play it (Choice Scarf, Iron Ball).
    our_spe = sum(battle.stat(f, "speed") for f in ours) / len(ours)
    their_spe = sum(battle.stat(f, "speed") for f in theirs) / len(theirs)

    def row(key: str, label: str, o: float, t: float, ol: str, tl: str, share: float) -> ScoreRow:
        return ScoreRow(
            key=key, label=label, ours=round(o, 2), theirs=round(t, 2),
            ours_label=ol, theirs_label=tl, share=round(share, 3),
            weight=_WEIGHTS[key], edge=_edge(share),
        )

    scorecard = [
        row(
            "h2h", "One-on-one matchups", wins, losses,
            f"{wins} won", f"{losses} won",
            # Even pairings count half to each side.
            _share(wins + evens / 2, losses + evens / 2),
        ),
        row(
            "reach", "Super-effective reach", our_reach_f, their_reach_f,
            f"{our_reach}/{len(theirs)} hit", f"{their_reach}/{len(ours)} hit",
            _share(our_reach_f, their_reach_f),
        ),
        row(
            "damage", "Average damage per hit", our_dmg, their_dmg,
            f"{our_dmg:.0f}%", f"{their_dmg:.0f}%", _share(our_dmg, their_dmg),
        ),
        row(
            "speed", "Average Speed", our_spe, their_spe,
            f"{our_spe:.0f}", f"{their_spe:.0f}", _share(our_spe, their_spe),
        ),
    ]
    return _HeadToHead(
        cells, scorecard, _verdict(scorecard, len(ours), len(theirs)), pressure, unanswered
    )


def _verdict(scorecard: list[ScoreRow], n_ours: int, n_theirs: int) -> Verdict:
    score = round(100 * sum(r.weight * r.share for r in scorecard))
    if score >= 62:
        label = "Favored"
    elif score >= 54:
        label = "Slight edge"
    elif score > 46:
        label = "Even"
    elif score > 38:
        label = "Slight underdog"
    else:
        label = "Underdog"
    edge = "ours" if score >= 54 else "theirs" if score <= 46 else "even"

    # Explain with the category that pulls hardest in the verdict's direction.
    if edge == "even":
        reason = "Evenly matched on paper — typing, Speed and stats roughly cancel out."
    else:
        sign = 1 if edge == "ours" else -1
        top = max(scorecard, key=lambda r: sign * (r.share - 0.5) * r.weight)
        who = "Your team" if edge == "ours" else "The opponent"
        reason = (
            f"{who} has the edge ({score}/100), driven by {top.label.lower()} "
            f"({top.ours_label} vs {top.theirs_label})."
        )
    if n_ours != n_theirs:
        reason += f" Note: {n_ours} vs {n_theirs} Pokémon — rosters aren't the same size."
    return Verdict(score=score, label=label, edge=edge, reason=reason)


def _summary(
    size: int,
    defensive: DefensiveProfile,
    offensive: OffensiveProfile,
    roles: RoleProfile,
    vs: VsOpponent | None,
) -> list[str]:
    out: list[str] = []
    if size < 6:
        out.append(f"Team has {size}/6 Pokémon — fill the empty slots for full coverage.")
    for sw in defensive.shared_weaknesses[:3]:
        out.append(
            f"Shared weakness: {sw.count} members are weak to {sw.type} "
            f"({', '.join(sw.members)})."
        )
    if offensive.uncovered_types:
        out.append(
            "Offensively you can't hit these types neutrally: "
            + ", ".join(offensive.uncovered_types)
            + "."
        )
    out.extend(offensive.tips[:3])
    for role in roles.missing_roles:
        out.append(f"Missing role: {role}.")
    if vs:
        out.extend(vs.advice[:3])
    if not out:
        out.append("No major structural weaknesses detected — good balance.")
    return out


async def duel_detail(
    session: AsyncSession, team: TeamOut, opponent: TeamOut, our_slot: int, their_slot: int
) -> DuelOut | None:
    """Play one pairing out turn by turn, with the same movesets the matchup uses."""
    fighters = await battle.load_fighters(session, team.members)
    foes = await battle.load_fighters(session, opponent.members)
    for f in fighters:
        f.moves = battle.complete_moveset(f, foes)
    for f in foes:
        f.moves = battle.complete_moveset(f, fighters)
    a = next((f for f in fighters if f.slot == our_slot), None)
    b = next((f for f in foes if f.slot == their_slot), None)
    if a is None or b is None:
        return None
    d = battle.duel(a, b)
    return DuelOut(
        our_slot=a.slot, their_slot=b.slot, our_name=a.name, their_name=b.name,
        outcome=d.outcome, first=d.first, our_setup=d.a_setup, their_setup=d.b_setup,
        our_moves=[m.name for m in a.moves], their_moves=[m.name for m in b.moves],
        our_moves_learned=[m.name for m in a.moves if m.learned],
        their_moves_learned=[m.name for m in b.moves if m.learned],
        notes=list(d.notes), log=[DuelEvent(**e) for e in d.log],
    )
