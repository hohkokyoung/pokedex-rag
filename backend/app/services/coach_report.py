"""The team report the coach reads first: both ratings and the matchup, as plain text.

Ported from the website's ``reportFacts`` (``TeamMatchupText.tsx``) and pinned to its
output by golden cases (``tests/fixtures/coach_report_*.json``), so the coach says what
the team page shows whichever client asks. Pure code, no LLM.
"""

from __future__ import annotations

from app.schemas.analysis import MatchupCell, TeamRating, VsMember, VsOpponent
from app.schemas.team import TeamOut
from app.services.stats import round_half_up


def matchup_headline(vs: VsOpponent, opponent_name: str) -> str:
    v = vs.verdict
    if v is None:
        return ""
    if v.edge == "ours":
        return "You're favoured" if v.score >= 62 else "You're slightly favoured"
    if v.edge == "theirs":
        return f"{opponent_name} is {'favoured' if v.score <= 38 else 'slightly favoured'}"
    return "Evenly matched"


Threat = tuple[VsMember, list[MatchupCell], list[MatchupCell], str | None, str | None]


def _threats(vs: VsOpponent) -> list[Threat]:
    """Their members, most of ours beaten first: (member, beats, answers, move, setup)."""
    out = []
    for x in vs.their_members:
        cs = [c for c in vs.cells if c.their_slot == x.slot]
        beats = [c for c in cs if c.outcome == "lose"]
        answers = sorted((c for c in cs if c.outcome == "win"), key=lambda c: c.their_pct)
        setup = next((c.their_setup for c in cs if c.their_setup), None)
        top = sorted(beats, key=lambda c: -c.their_pct)
        out.append((x, beats, answers, top[0].their_move if top else None, setup))
    return sorted(out, key=lambda t: -len(t[1]))


def _ours(vs: VsOpponent) -> list[tuple[VsMember, int, int]]:
    """Our members, most pairings won first: (member, wins, pairings)."""
    rows = []
    for o in vs.our_members:
        cs = [c for c in vs.cells if c.our_slot == o.slot]
        rows.append((o, sum(1 for c in cs if c.outcome == "win"), len(cs)))
    return sorted(rows, key=lambda r: -r[1])


def report_facts(
    team: TeamOut,
    rating: TeamRating | None,
    opponent: TeamOut | None = None,
    opponent_rating: TeamRating | None = None,
    vs: VsOpponent | None = None,
) -> str:
    """Both ratings with every area's verdict and fix, then (with an opponent) the
    matchup verdict, their top threats with your answers, the best lead and who wins
    nothing. An opponent with no pairings (e.g. an empty team) adds no matchup lines."""
    lines: list[str] = []

    def rated(name: str, r: TeamRating) -> None:
        scaled = f", scaled for a {round_half_up(r.ceiling * 6 / 100)}/6 roster" if r.capped else ""
        lines.append(f"{name}: overall {r.overall}/100 ({r.grade}){scaled}.")
        for a in r.areas:
            fix = f" Fix: {a.fix}" if a.fix else ""
            lines.append(f"- {name} {a.label} {a.grade} ({a.score}): {a.headline}.{fix}")

    if rating is not None:
        rated(f'Your team "{team.name}"', rating)
    if opponent is not None and opponent_rating is not None:
        rated(f'Opponent "{opponent.name}"', opponent_rating)
    if opponent is not None and vs is not None and vs.cells:
        you = sum(1 for c in vs.cells if c.outcome == "win")
        them = sum(1 for c in vs.cells if c.outcome == "lose")
        close = len(vs.cells) - you - them
        lines.append(
            f"Matchup verdict: {matchup_headline(vs, opponent.name)} — you win {you} of "
            f"{len(vs.cells)} one-on-ones, they win {them}{f', {close} close' if close else ''}."
        )
        name = {o.slot: o.name for o in vs.our_members}
        for x, beats, answers, move, setup in _threats(vs)[:4]:
            how = (f" with {move}" if move else "") + (f" after {setup}" if setup else "")
            if answers:
                a = answers[0]
                took = round_half_up(a.their_pct)
                answer = (f"your best answer is {name.get(a.our_slot, '?')} "
                          f"(takes {took}%, KOs in {a.our_hko} with {a.our_move}).")
            else:
                answer = "nothing on your team beats it one-on-one."
            mine = len(vs.our_members)
            lines.append(f"Threat: {x.name} beats {len(beats)} of your {mine}{how}; {answer}")
        ours = _ours(vs)
        if ours:
            lead, wins, n = ours[0]
            lines.append(f"Best lead: {lead.name}, wins {wins} of {n} pairings.")
        idle = [o.name for o, wins, _ in ours if wins == 0]
        if idle:
            lines.append(f"Wins no pairing here: {', '.join(idle)}.")
    return "\n".join(lines)
