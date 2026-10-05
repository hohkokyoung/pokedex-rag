"""Team-aware coaching context for the assistant.

Builders that represent the user's team, the deterministic analysis, and (optionally) a
saved opponent as ``RetrievedChunk`` passages. The agent's built-in ``team_context`` step
(``app/agent/team_tools.py``) attaches them to every coach question, so everything the
coach says is grounded in — and cites — the same evidence path as the rest of the
assistant. Also the keyless composers used when no LLM is available.
"""

from __future__ import annotations

from app.rag.retrieval import RetrievedChunk
from app.schemas.analysis import TeamAnalysis
from app.schemas.recommend import Candidate
from app.schemas.team import TeamMemberOut

COACH_NOTE = (
    "NOTE: You are coaching the user's Pokémon team. The CONTEXT contains the team's "
    "current slots, a deterministic analysis (type weaknesses, offensive coverage, roles, "
    "and per-slot suggestions), when provided a saved opponent team, and any extra lookups "
    "planned for this question. Give "
    "concrete, actionable advice — which Pokémon, abilities, natures, EVs or moves to change "
    "and why — grounded in these facts and cited with [n]. If the "
    "user asks for data that isn't present (exact competitive tiers, full real-world movesets), "
    "say you don't have it rather than guessing. When a 'Team report' passage is present it "
    "is exactly what the user sees on the page — its grades, weak spots, threats, answers and "
    "plan are authoritative: base your answer on it, cite it, and never contradict it."
)


def _stat_line(stats: dict[str, int]) -> str:
    return "/".join(
        f"{k.replace('sp_', 'Sp')}{stats[k]}"
        for k in ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")
    )


def _member_chunk(m: TeamMemberOut, *, opponent: bool = False) -> RetrievedChunk:
    ability = m.ability.name if m.ability else "unset"
    nature = m.nature.name if m.nature else "unset"
    item = (
        f"{m.item.name} ({m.item.short_effect})" if m.item and m.item.short_effect
        else m.item.name if m.item else "none"
    )
    evs = ", ".join(f"{v} {k}" for k, v in m.ev_spread.items() if v) or "none"
    moves = ", ".join(mv.name for mv in m.moves) or "no moves set"
    who = "Opponent" if opponent else "Team"
    content = (
        f"{who} slot {m.slot}: {m.name} ({'/'.join(m.types)}). "
        f"Ability: {ability}. Nature: {nature}. Item: {item}. EVs: {evs}. Moves: {moves}. "
        f"Base stats {_stat_line(m.base_stats)}; battle stats at Lv50 {_stat_line(m.final_stats)}."
    )
    return RetrievedChunk(
        id=-1,
        pokemon_id=m.pokemon_id,
        pokemon_name=m.name,
        dex_number=m.dex_number,
        chunk_type="opponent_member" if opponent else "team_member",
        source_ref=f"{'opponent' if opponent else 'team'}-slot-{m.slot}",
        content=content,
        score=1.0,
    )


def _analysis_chunk(a: TeamAnalysis) -> RetrievedChunk:
    parts = [f"Analysis of team '{a.name}' ({a.size}/6 Pokémon):"]
    if a.defensive.shared_weaknesses:
        parts.append(
            "Shared defensive weaknesses — "
            + "; ".join(
                f"{w.type} ({w.count} members: {', '.join(w.members)})"
                for w in a.defensive.shared_weaknesses
            )
            + "."
        )
    else:
        parts.append("No type is super-effective against 3+ members.")
    cover = ", ".join(a.offensive.coverage_types) or "none"
    parts.append(
        "Offensive coverage (moves set on each slot, with open move slots filled by the best "
        f"moves each species can learn): {cover}."
    )
    if a.offensive.from_learnset:
        parts.append(
            "Of those, only reachable via learnable (not yet set) moves: "
            + ", ".join(a.offensive.from_learnset)
            + "."
        )
    parts.extend(a.offensive.tips)
    if a.offensive.uncovered_types:
        parts.append(
            "Cannot hit these types even neutrally: "
            + ", ".join(a.offensive.uncovered_types)
            + "."
        )
    roles = "; ".join(f"{r.name}: {r.role} (Spe {r.speed}, BST {r.bst})" for r in a.roles.members)
    parts.append("Roles — " + roles + ".")
    if a.roles.missing_roles:
        parts.append("Missing roles: " + ", ".join(a.roles.missing_roles) + ".")
    return RetrievedChunk(
        id=-1,
        pokemon_id=None,
        pokemon_name=None,
        dex_number=None,
        chunk_type="team_analysis",
        source_ref="analysis",
        content="\n".join(parts),
        score=1.0,
    )


def _suggestions_chunk(a: TeamAnalysis) -> RetrievedChunk:
    lines = ["Per-slot optimization suggestions:"]
    for s in a.suggestions:
        ev = ", ".join(f"{v} {k}" for k, v in s.recommended_evs.items() if v)
        moves = ", ".join(
            f"{m.name}{'' if m.is_set else ' (suggested, learnable)'}" for m in s.recommended_moves
        )
        lines.append(
            f"- {s.name}: ability {s.recommended_ability or 'n/a'}, nature {s.recommended_nature}, "
            f"EVs {ev}. Moves: {moves or 'none'}. {s.rationale}"
        )
    return RetrievedChunk(
        id=-1,
        pokemon_id=None,
        pokemon_name=None,
        dex_number=None,
        chunk_type="team_suggestions",
        source_ref="suggestions",
        content="\n".join(lines),
        score=1.0,
    )


def _vs_chunk(a: TeamAnalysis) -> RetrievedChunk | None:
    if a.vs_opponent is None:
        return None
    v = a.vs_opponent
    lines = [f"Matchup vs opponent team '{v.opponent_name}':"]
    if v.verdict:
        lines.append(
            f"- Overall verdict (damage calc from set + learnable moves, Speed; not a battle sim): "
            f"{v.verdict.label}, {v.verdict.score}/100 for the user's team."
        )
        for r in v.scorecard:
            lines.append(f"- {r.label}: user {r.ours_label} vs opponent {r.theirs_label}.")
    ours = {m.slot: m.name for m in v.our_members}
    for m in v.their_members:
        col = sorted((c for c in v.cells if c.their_slot == m.slot), key=lambda c: -c.score)
        if col:
            c = col[0]
            learned = " (learnable, not yet set)" if c.our_move_learned else ""
            lines.append(
                f"- Best answer to {m.name}: {ours.get(c.our_slot)} with {c.our_move}{learned}, "
                f"~{c.our_pct:.0f}% per hit ({c.our_hko}HKO) vs {m.name}'s {c.their_move} "
                f"~{c.their_pct:.0f}% ({c.their_hko}HKO); outcome {c.outcome}."
            )
    for p in v.our_pressure:
        lines.append(
            f"- User's {p.attacker} hits {', '.join(p.targets)} super-effectively "
            f"via {', '.join(p.via)}."
        )
    for t in v.threats:
        lines.append(
            f"- {t.opponent_name} ({'/'.join(t.opponent_types)}) threatens "
            f"{', '.join(t.threatens)} via super-effective {', '.join(t.via)}."
        )
    for a_line in v.advice:
        lines.append(f"- Advice: {a_line}")
    return RetrievedChunk(
        id=-1,
        pokemon_id=None,
        pokemon_name=None,
        dex_number=None,
        chunk_type="vs_opponent",
        source_ref="vs-opponent",
        content="\n".join(lines),
        score=1.0,
    )


def compose_extractive_draft(candidates: list[Candidate]) -> str:
    """Keyless fallback: a plain list of the recommended additions."""
    if not candidates:
        return "I couldn't find candidates that fit — try loosening the constraints."
    lines = ["Recommended additions (add an LLM key for tailored reasoning):", ""]
    lines.extend(f"- **{c.name}** ({'/'.join(c.types)}) — {c.reason}" for c in candidates)
    return "\n".join(lines)


def compose_extractive_coach(analysis: TeamAnalysis) -> str:
    """Keyless fallback: a plain-language coaching brief straight from the analysis."""
    lines = [f"Here's what the analysis says about **{analysis.name}** "
             "(add an LLM key for conversational coaching):", ""]
    lines.extend(f"- {s}" for s in analysis.summary)
    if analysis.suggestions:
        lines.append("")
        lines.append("Per-slot suggestions:")
        for s in analysis.suggestions:
            lines.append(
                f"- {s.name}: {s.recommended_nature} nature, "
                f"ability {s.recommended_ability or 'n/a'}."
            )
    return "\n".join(lines)
