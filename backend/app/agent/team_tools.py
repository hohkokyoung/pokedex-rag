"""Team-coach tools: the always-attached team context, recommendations, set-edit
proposals, explicit adds, and duels.

The team (and the selected opponent) arrive in ``AgentContext``; the computed analysis
and the request's ``Usage`` arrive in ``ctx.extra``. Only ``add_member`` writes, and
only when the runner's imperative-add gate (``ctx.extra["allow_add"]``) is set —
otherwise it answers with an Add card instead.
"""

from __future__ import annotations

import difflib
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent import names
from app.agent.ask_tools import _card_from_pokemon, _types
from app.agent.results import ToolResult
from app.agent.tools import AgentContext, tool
from app.agent.views import (
    BuildSet,
    CandidatesView,
    DuelView,
    MemberAddedView,
    SetEditView,
    SlotRef,
)
from app.models import Pokemon, PokemonType
from app.models.team import MAX_SLOTS
from app.rag import build_suggest, coach, team_summary
from app.rag.retrieval import RetrievedChunk
from app.schemas.team import SlotUpdate, TeamMemberOut, TeamOut
from app.services import recommend, team_analysis
from app.services import teams as teams_service

TEAM = ("team",)

# Team-scope chunk ids live in their own ranges so evidence de-duplication (by id)
# never collapses them: the coach builders all used id -1.
_CTX_BASE = 10_000_000
_CAND_BASE = 11_000_000

_EV_KEYS = {"hp": "hp", "attack": "atk", "defense": "def", "sp_attack": "spa",
            "sp_defense": "spd", "speed": "spe"}


async def analysis_for(session: AsyncSession, ctx: AgentContext):
    """The request's team analysis, computed once and shared by every step."""
    if ctx.extra.get("analysis") is None:
        ctx.extra["analysis"] = await team_analysis.analyze(session, ctx.team, ctx.opponent)
    return ctx.extra["analysis"]


def _numbered(chunks: list[RetrievedChunk], base: int) -> list[RetrievedChunk]:
    for i, c in enumerate(chunks):
        c.id = -(base + i)
    return chunks


# ---- team_context (built-in, never planned) -------------------------------------------


class NoArgs(BaseModel):
    pass


@tool(
    "team_context",
    scopes=TEAM,
    description="The user's team, its analysis and suggestions (always attached).",
    args=NoArgs,
    plannable=False,
)
async def team_context(session: AsyncSession, args: NoArgs, ctx: AgentContext) -> ToolResult:
    team: TeamOut = ctx.team
    analysis = await analysis_for(session, ctx)
    chunks: list[RetrievedChunk] = []
    if ctx.report and ctx.report.strip():
        chunks.append(RetrievedChunk(
            id=0, pokemon_id=None, pokemon_name=None, dex_number=None,
            chunk_type="team_report", source_ref="team page",
            content="Team report shown on the page (authoritative):\n" + ctx.report.strip(),
            score=1.0,
        ))
    chunks += [coach._member_chunk(m) for m in team.members]
    chunks.append(coach._analysis_chunk(analysis))
    chunks.append(coach._suggestions_chunk(analysis))
    if ctx.opponent is not None:
        chunks += [coach._member_chunk(m, opponent=True) for m in ctx.opponent.members]
        vs = coach._vs_chunk(analysis)
        if vs is not None:
            chunks.append(vs)
    opp = f" vs {ctx.opponent.name}" if ctx.opponent is not None else ""
    return ToolResult(
        chunks=_numbered(chunks, _CTX_BASE),
        summary=f"{team.name}: {len(team.members)}/6{opp}",
        note=coach.COACH_NOTE,
        data={"context": True},
    )


# ---- roster lookup ------------------------------------------------------------------


def find_member(team: TeamOut | None, name: str) -> TeamMemberOut | None:
    """A member by name: exact (case-insensitive), then the closest spelling."""
    if team is None or not name:
        return None
    by_name = {m.name.lower(): m for m in team.members}
    key = name.strip().lower()
    if key in by_name:
        return by_name[key]
    close = difflib.get_close_matches(key, list(by_name), n=1, cutoff=0.8)
    return by_name[close[0]] if close else None


def _set_of(m: TeamMemberOut) -> BuildSet:
    return BuildSet(
        moves=[mv.name for mv in m.moves],
        ability=m.ability.name if m.ability else None,
        nature=m.nature.name if m.nature else None,
        item=m.item.name if m.item else None,
        evs={_EV_KEYS.get(k, k): v for k, v in (m.ev_spread or {}).items()},
    )


# ---- recommend_additions ------------------------------------------------------------


class RecommendArgs(BaseModel):
    role: Literal["sweeper", "wall", "wallbreaker", "support"] | None = None
    legendary: bool | None = Field(None, description="true include, false exclude")
    mythical: bool | None = None
    types: list[str] = Field(default_factory=list, description="types the picks should be")
    limit: int | None = None

    @field_validator("types")
    @classmethod
    def _norm(cls, v: list[str]) -> list[str]:
        return _types(v)


@tool(
    "recommend_additions",
    scopes=TEAM,
    description="Draft Pokémon to add to the team (role, legendary/mythical, types).",
    args=RecommendArgs,
)
async def recommend_additions(
    session: AsyncSession, args: RecommendArgs, ctx: AgentContext
) -> ToolResult:
    team: TeamOut = ctx.team
    analysis = await analysis_for(session, ctx)
    mythical = args.mythical if args.mythical is not None else (
        False if args.legendary is False else None)
    prefs = recommend.DraftPrefs(
        role=args.role, include_legendary=args.legendary, include_mythical=mythical,
        want_types=args.types,
    )
    limit = max(1, min(args.limit or 6, 8))
    candidates = await recommend.recommend_additions(
        session, team, analysis, "", prefs=prefs, limit=limit
    )
    if not candidates:
        return ToolResult.empty("no candidates fit")
    chunks = _numbered(recommend.to_chunks(candidates), _CAND_BASE)
    view = CandidatesView(
        team_id=team.id, candidates=candidates, team_full=len(team.members) >= MAX_SLOTS,
        members=[SlotRef(slot=m.slot, name=m.name) for m in team.members],
        chunk_refs=list(range(len(chunks))),
    )
    note = (
        "NOTE: 'Candidate addition' passages are real Pokémon ranked for this team. "
        "Recommend ONLY from them, name each and say briefly why it fits; the user can add "
        "one with its Add button or by saying e.g. 'add <name>'."
    )
    return ToolResult(chunks=chunks, views=[view], note=note,
                      summary=f"{len(candidates)} candidates", data={"candidates": True})


# ---- propose_set_edit ---------------------------------------------------------------


class SetEditArgs(BaseModel):
    member: str = Field(description="the team member's name")
    side: Literal["ours", "theirs"] = "ours"
    request: str = Field(description="what to change, in the user's words")


def _changed(before: BuildSet, after: BuildSet) -> dict:
    """The fields that differ, in the slot editor's apply shape."""
    fields: dict = {}
    if after.moves and after.moves != before.moves:
        fields["moves"] = after.moves
    for k in ("ability", "nature"):
        if getattr(after, k) and (getattr(after, k) or "").lower() != (
                getattr(before, k) or "").lower():
            fields[k] = getattr(after, k)
    if (after.item or "").lower() != (before.item or "").lower():
        fields["item"] = after.item or "none"
    if {k: v for k, v in after.evs.items() if v} != {k: v for k, v in before.evs.items() if v}:
        fields["evs"] = after.evs
    return fields


@tool(
    "propose_set_edit",
    scopes=TEAM,
    description="A new set for one member (saved only on Apply).",
    args=SetEditArgs,
    closed_form=True,
)
async def propose_set_edit(
    session: AsyncSession, args: SetEditArgs, ctx: AgentContext
) -> ToolResult:
    roster: TeamOut | None = ctx.opponent if args.side == "theirs" else ctx.team
    m = find_member(roster, args.member)
    if m is None:  # the other side, before giving up
        other = ctx.team if args.side == "theirs" else ctx.opponent
        m = find_member(other, args.member)
        if m is not None:
            roster = other
    if m is None:
        return ToolResult.error(f"{args.member} isn't on the team")
    side = "theirs" if ctx.opponent is not None and roster is ctx.opponent else "ours"
    before = _set_of(m)
    current = (
        build_suggest.BuildSuggestion(pokemon=m.name, moves=before.moves, ability=before.ability,
                                      nature=before.nature, item=before.item,
                                      evs=before.evs or {k: 0 for k in build_suggest.STATS})
        if before.moves else None
    )
    try:
        build = await build_suggest.suggest_build(
            session, m.pokemon_id, m.form_id, request=args.request[:300], current=current,
            attempts=1, usage=ctx.extra.get("usage"),
        )
    except build_suggest.SuggestError as e:
        msg = str(e)
        if "LLM key" in msg:
            msg = "set suggestions need an LLM key"
        return ToolResult.error(msg)
    after = BuildSet(moves=build.moves, ability=build.ability, nature=build.nature,
                     item=build.item, evs=build.evs)
    fields = _changed(before, after)
    content = (
        f"Proposed set for {m.name} ({'opponent' if side == 'theirs' else 'your team'}, "
        f"slot {m.slot}): moves {', '.join(build.moves)}; ability {build.ability or '-'}; "
        f"nature {build.nature or '-'}; item {build.item or 'none'}; EVs "
        + (", ".join(f"{v} {k}" for k, v in build.evs.items() if v) or "none")
        + f". {build.why}"
    )
    chunk = RetrievedChunk(
        id=-(_CAND_BASE + 900_000 + m.pokemon_id), pokemon_id=m.pokemon_id,
        pokemon_name=m.name, dex_number=m.dex_number, chunk_type="set_proposal",
        source_ref="coach set", content=content, score=1.0,
    )
    view = SetEditView(
        side=side, team_id=roster.id, slot=m.slot, name=m.name, sprite_url=m.sprite_url,
        before=before, after=after, why=build.why, fields=fields,
        member=m.model_dump(mode="json"), chunk_refs=[0],
    )
    changed = ", ".join(fields) or "no changes"
    return ToolResult(chunks=[chunk], views=[view], summary=f"{m.name}: {changed}",
                      data={"why": build.why, "name": m.name})


# ---- add_member ---------------------------------------------------------------------


class AddArgs(BaseModel):
    pokemon: str


async def _species(session: AsyncSession, name: str) -> Pokemon | None:
    m = await names.resolve_one(session, name, "pokemon")
    if m is None:
        return None
    return (
        await session.execute(
            select(Pokemon).options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            .where(Pokemon.id == m.id)
        )
    ).scalars().first()


@tool(
    "add_member",
    scopes=TEAM,
    description="Add a Pokémon to the next empty slot; only for an explicit 'add X'.",
    args=AddArgs,
    closed_form=True,
)
async def add_member(session: AsyncSession, args: AddArgs, ctx: AgentContext) -> ToolResult:
    team: TeamOut = ctx.team
    p = await _species(session, args.pokemon)
    if p is None:
        return ToolResult.error(f'unresolved Pokémon "{args.pokemon}"')
    card = _card_from_pokemon(p, 0)

    if not ctx.extra.get("allow_add"):
        # Card mode: deliberation (or a planner mistake) never writes — offer an Add card.
        analysis = await analysis_for(session, ctx)
        cand = await recommend.candidate_for(session, p, analysis)
        chunks = _numbered(recommend.to_chunks([cand]), _CAND_BASE)
        view = CandidatesView(
            team_id=team.id, candidates=[cand], team_full=len(team.members) >= MAX_SLOTS,
            members=[SlotRef(slot=m.slot, name=m.name) for m in team.members], chunk_refs=[0],
        )
        return ToolResult(chunks=chunks, views=[view], closed=False,
                          summary=f"{p.name}: Add card (no change)", data={"card_mode": True})

    used = {m.slot for m in team.members}
    slot = next((s for s in range(1, MAX_SLOTS + 1) if s not in used), None)
    if any(m.pokemon_id == p.id for m in team.members):
        message = f"{p.name} is already on this team."
        slot = None
    elif slot is None:
        message = f"Your team is already full (6/6) — clear a slot before adding {p.name}."
    else:
        message = ""
    if not message:
        updated = await teams_service.set_slot(session, team.id, slot, SlotUpdate(pokemon_id=p.id))
        team_summary.schedule(team.id)
        ctx.team = updated
        message = (f"Added **{p.name}** to slot {slot}. Configure its ability, nature, EVs and "
                   "moves from the slot, or ask me for its best set.")
        added = True
    else:
        updated = None
        added = False
    chunk = RetrievedChunk(
        id=-(_CAND_BASE + 800_000 + p.id), pokemon_id=p.id, pokemon_name=p.name,
        dex_number=p.dex_number, chunk_type="team_change", source_ref="add",
        content=message.replace("**", ""), score=1.0,
    )
    view = MemberAddedView(team_id=team.id, added=added, slot=slot if added else None,
                           card=card, message=message, chunk_refs=[0])
    data = {"message": message, "added": added}
    if updated is not None:
        data["team_updated"] = updated.model_dump(mode="json")
    return ToolResult(chunks=[chunk], views=[view], data=data,
                      summary=f"added {p.name} to slot {slot}" if added else message)


# ---- duel ---------------------------------------------------------------------------


class DuelArgs(BaseModel):
    ours: str = Field(description="our member's name")
    theirs: str = Field(description="the opponent member's name")


@tool(
    "duel",
    scopes=TEAM,
    description="Play our member vs an opponent member, turn by turn.",
    args=DuelArgs,
)
async def duel(session: AsyncSession, args: DuelArgs, ctx: AgentContext) -> ToolResult:
    if ctx.opponent is None:
        return ToolResult.error("select an opponent team to play a duel")
    a = find_member(ctx.team, args.ours)
    b = find_member(ctx.opponent, args.theirs)
    if a is None or b is None:
        missing = args.ours if a is None else args.theirs
        return ToolResult.error(f"{missing} isn't on the team")
    out = await team_analysis.duel_detail(session, ctx.team, ctx.opponent, a.slot, b.slot)
    if out is None:
        return ToolResult.empty("no duel for that pairing")
    who = {"win": f"{a.name} wins", "lose": f"{b.name} wins", "even": "it's even"}[out.outcome]
    first = {"ours": a.name, "theirs": b.name, "tie": "neither (speed tie)"}[out.first]
    content = (
        f"Duel {a.name} (your team) vs {b.name} (opponent), played out by the damage engine: "
        f"{who}; {first} moves first. {a.name} uses {', '.join(out.our_moves) or '-'}; "
        f"{b.name} uses {', '.join(out.their_moves) or '-'}. " + " ".join(out.notes)
    )
    chunk = RetrievedChunk(
        id=-(_CAND_BASE + 700_000 + a.slot * 10 + b.slot), pokemon_id=a.pokemon_id,
        pokemon_name=a.name, dex_number=a.dex_number, chunk_type="duel",
        source_ref=f"{a.name} vs {b.name}", content=content, score=1.0,
    )
    view = DuelView(team_id=ctx.team.id, opponent_id=ctx.opponent.id, duel=out, chunk_refs=[0])
    return ToolResult(chunks=[chunk], views=[view], summary=f"{a.name} vs {b.name}: {who}")
