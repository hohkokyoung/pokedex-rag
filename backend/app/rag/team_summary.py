"""A short plain-English summary of a team.

Grounded only in facts we compute (members, typings, strategy axes, analysis).
Uses the configured LLM when there is one; otherwise — or if the call fails or
is rate-limited — falls back to a deterministic sentence built from the same
facts.

The summary is persisted on the team row together with a *fingerprint* of the
roster (members, forms, abilities, moves). Opening the list page only reads it;
the LLM runs in the background, debounced, and only when the fingerprint
changes — so renaming a team or re-opening the page never calls it.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.models.team import Team
from app.rag import answer
from app.schemas.analysis import TeamAnalysis
from app.schemas.team import TeamOut
from app.services import team_analysis, team_strategy
from app.services import teams as teams_service
from app.services.stats import as_built
from app.services.team_strategy import Strategy

log = logging.getLogger(__name__)

# Bump when the prompt or facts change so stored summaries are rewritten once.
SUMMARY_VERSION = 3
DEBOUNCE_SECONDS = 2.5  # rapid slot edits collapse into one LLM call
FAILURE_BACKOFF = 60.0  # after a failed call, don't retry that team for a minute
_LLM_SLOTS = asyncio.Semaphore(2)  # at most two summaries in flight at once
_tokens: dict[int, int] = {}  # team_id → latest scheduled run (debounce)
_failed_at: dict[int, float] = {}
_tasks: set[asyncio.Task] = set()  # keep references so tasks aren't GC'd

SYSTEM = (
    "You describe a Pokémon team for its owner in at most two short sentences "
    "(under 40 words total). Use ONLY the facts provided. Say what kind of team it "
    "is and how it wants to win (how_it_wins), and what its key members do "
    "(member_jobs). Describe only — no risks, weaknesses, advice or suggestions. "
    "Never invent moves, items, abilities, tiers or usage stats that aren't in the "
    "facts. Plain text, no lists, no markdown, no quotes."
)


def _facts(team: TeamOut, strategy: Strategy, analysis: TeamAnalysis) -> dict:
    return {
        "members": [
            {
                "name": m.name,
                "types": m.types,
                "ability": m.ability.name if m.ability else None,
                "item": m.item.name if m.item else None,
                "moves": [mv.name for mv in m.moves],
            }
            for m in team.members
        ],
        "style": strategy.style,
        "how_it_wins": HOW[strategy.style],
        "member_jobs": member_jobs(team, strategy, analysis),
        "fastest": max(
            # Speed as built (EVs, IVs, nature), matching the roles and ratings.
            ((m.name, as_built(m.final_stats)["speed"]) for m in team.members),
            key=lambda x: x[1],
            default=None,
        ),
        "axes_now_vs_potential": {
            a.label: {"now": a.now, "potential": a.potential} for a in strategy.axes
        },
        # What's actually on the team vs options the species could learn but don't have.
        "on_team": {
            a.label: sorted({f"{c.name}: {mv}" for c in a.contributors if c.set for mv in c.moves})
            for a in strategy.axes
            if any(c.set for c in a.contributors)
        },
        "types_hit_super_effectively_of_18": 18
        - len([t for t in analysis.offensive.not_super_effective if t != "stellar"]),
        "team_size": len(team.members),
    }


HOW = {
    "Stall": "wears foes down with recovery and chip damage",
    "Setup offense": "boosts up and sweeps",
    "Hyper offense": "outspeeds and hits hard before the foe can act",
    "Bulky offense": "takes a hit and hits back hard",
    "Utility balance": "controls the game with hazards, status and pivots",
    "Offense": "relies on raw attacking power",
    "Balance": "mixes offence and defence without a clear win condition",
}


def member_jobs(team: TeamOut, strategy: Strategy, analysis: TeamAnalysis) -> list[str]:
    """What each member does, from its engine role plus the strategy moves actually set."""
    roles = {r.slot: r.role for r in analysis.roles.members}
    jobs: list[str] = []
    seen: set[str] = set()
    for m in team.members:
        if m.name in seen:  # a repeated species adds nothing new to the description
            continue
        seen.add(m.name)
        extras = sorted(
            {
                mv
                for a in strategy.axes
                for c in a.contributors
                if c.set and c.name == m.name
                for mv in c.moves
            }
        )
        role = roles.get(m.slot, "member").lower()
        jobs.append(f"{m.name}: {role}" + (f" with {', '.join(extras)}" if extras else ""))
    return jobs


def rules_summary(team: TeamOut, strategy: Strategy, analysis: TeamAnalysis) -> str:
    """Deterministic fallback from the same facts — a description, no advice."""
    types: list[str] = []
    for m in team.members:
        for t in m.types:
            if t not in types:
                types.append(t)
    core = "/".join(t.title() for t in types[:2])
    jobs = member_jobs(team, strategy, analysis)
    text = f"A {strategy.style.lower()} {core} team that {HOW[strategy.style]}."
    if jobs:
        text += " " + "; ".join(jobs[:3]).replace(": ", " is the ", len(jobs[:3])) + "."
    return text


async def summarize(team: TeamOut, strategy: Strategy, analysis: TeamAnalysis) -> tuple[str, str]:
    """(text, source) — source is 'ai' or 'rules'."""
    facts = _facts(team, strategy, analysis)
    if not team.members:
        return "No Pokémon yet.", "rules"
    if not get_settings().llm_enabled:
        return rules_summary(team, strategy, analysis), "rules"
    try:
        text = (await answer.quick_complete(SYSTEM, json.dumps(facts), max_tokens=900)).strip()
        if not text or len(text) > 400:
            raise ValueError("unusable summary")
        return text, "ai"
    except Exception as exc:  # rate limit, network, provider error → deterministic text
        log.warning("team summary fell back to rules: %s", exc)
        return rules_summary(team, strategy, analysis), "rules"


# ── persistence ──────────────────────────────────────────────────────────────


def fingerprint(team: TeamOut) -> str:
    """Hash of what the summary describes: species, forms and the whole set — ability,
    item, nature, EVs/IVs and moves — since roles and speed now follow the set (not the name)."""
    roster = sorted(
        (
            m.slot,
            m.pokemon_id,
            m.form_id,
            m.ability.id if m.ability else None,
            m.item.id if m.item else None,
            m.nature.id if m.nature else None,
            sorted((m.ev_spread or {}).items()),
            sorted((m.iv_spread or {}).items()),
            tuple(sorted(mv.move_id for mv in m.moves)),
        )
        for m in team.members
    )
    raw = json.dumps([SUMMARY_VERSION, roster], default=str)
    return hashlib.sha1(raw.encode()).hexdigest()


async def _generate(session: AsyncSession, team: TeamOut) -> tuple[str, str]:
    strategy = await team_strategy.team_strategy(session, team.members)
    analysis = await team_analysis.analyze(session, team)
    return await summarize(team, strategy, analysis)


async def _store(session: AsyncSession, team_id: int, text: str, source: str, key: str) -> None:
    row = await session.get(Team, team_id)
    if row is None:
        return
    row.summary_text, row.summary_source, row.summary_key = text, source, key
    await session.commit()


async def current(session: AsyncSession, team: TeamOut) -> tuple[str, str, bool]:
    """(text, source, pending) without ever waiting on the LLM.

    Fresh stored summary → return it. Otherwise return the rule-based text now
    and (if an LLM is configured) schedule an AI rewrite in the background.
    """
    if not team.members:
        return "No Pokémon yet.", "rules", False
    key = fingerprint(team)
    row = await session.get(Team, team.id)
    if row and row.summary_key == key and row.summary_text:
        return row.summary_text, row.summary_source or "rules", False
    strategy = await team_strategy.team_strategy(session, team.members)
    analysis = await team_analysis.analyze(session, team)
    text = rules_summary(team, strategy, analysis)
    if not get_settings().llm_enabled:
        await _store(session, team.id, text, "rules", key)  # nothing better is coming
        return text, "rules", False
    if row and row.summary_text and row.summary_source == "ai":
        text = row.summary_text  # show the last AI text while the new one is written
    scheduled = schedule(team.id)
    return text, "ai" if (row and row.summary_source == "ai") else "rules", scheduled


def schedule(team_id: int) -> bool:
    """Debounced background rewrite. Returns False when skipped (recent failure / no LLM)."""
    if not get_settings().llm_enabled:
        return False
    if time.monotonic() - _failed_at.get(team_id, -1e9) < FAILURE_BACKOFF:
        return False
    token = _tokens.get(team_id, 0) + 1
    _tokens[team_id] = token
    try:
        task = asyncio.get_running_loop().create_task(_run(team_id, token))
    except RuntimeError:  # no running loop (e.g. sync tests)
        return False
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return True


async def _run(team_id: int, token: int) -> None:
    await asyncio.sleep(DEBOUNCE_SECONDS)
    if _tokens.get(team_id) != token:
        return  # a newer edit superseded this one
    async with _LLM_SLOTS:
        try:
            await refresh(team_id)
        except Exception as exc:  # never let a background task crash the app
            log.warning("background summary for team %s failed: %s", team_id, exc)


async def refresh(team_id: int, *, force: bool = False) -> tuple[str, str] | None:
    """Rewrite and store the summary if the roster changed (or when forced)."""
    async with async_session_factory() as session:
        team = await teams_service.get_team(session, team_id)
        if team is None or not team.members:
            return None
        key = fingerprint(team)
        row = await session.get(Team, team_id)
        if not force and row and row.summary_key == key and row.summary_text:
            return row.summary_text, row.summary_source or "rules"
        text, source = await _generate(session, team)
        if source == "ai" or not get_settings().llm_enabled:
            await _store(session, team_id, text, source, key)
            _failed_at.pop(team_id, None)
        else:
            _failed_at[team_id] = time.monotonic()  # LLM failed — keep the old text, retry later
        return text, source
