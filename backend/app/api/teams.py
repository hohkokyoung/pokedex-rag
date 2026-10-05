"""Team CRUD + per-slot editing (single local user, player & opponent teams)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import run_question
from app.agent.sse import _sse
from app.agent.tools import AgentContext
from app.core.database import async_session_factory, get_session
from app.models.team import MAX_SLOTS
from app.rag import personalize, team_summary
from app.schemas.analysis import DuelOut, TeamAnalysis
from app.schemas.strategy import TeamStrategy, TeamSummaryOut
from app.schemas.team import (
    CoachAskRequest,
    SlotBuild,
    SlotUpdate,
    TeamCreate,
    TeamListResponse,
    TeamOut,
    TeamUpdate,
)
from app.services import team_analysis, team_strategy
from app.services import teams as teams_service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=TeamListResponse)
async def list_teams(
    kind: str | None = Query(None, pattern="^(player|opponent)$"),
    session: AsyncSession = Depends(get_session),
) -> TeamListResponse:
    return TeamListResponse(teams=await teams_service.list_teams(session, kind))


@router.post("", response_model=TeamOut, status_code=201)
async def create_team(
    payload: TeamCreate,
    session: AsyncSession = Depends(get_session),
) -> TeamOut:
    return await teams_service.create_team(session, payload)


@router.get("/{team_id}", response_model=TeamOut)
async def get_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
) -> TeamOut:
    team = await teams_service.get_team(session, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/{team_id}/strategy", response_model=TeamStrategy)
async def team_strategy_profile(
    team_id: int, session: AsyncSession = Depends(get_session)
) -> TeamStrategy:
    """How the team wants to win: offense/bulk/speed/setup/stall/support, each traceable."""
    team = await teams_service.get_team(session, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    s = await team_strategy.team_strategy(session, team.members)
    return TeamStrategy.model_validate({"team_id": team.id, **asdict(s)})


@router.get("/{team_id}/summary", response_model=TeamSummaryOut)
async def team_summary_text(
    team_id: int, session: AsyncSession = Depends(get_session)
) -> TeamSummaryOut:
    """Stored summary; never waits on the LLM. ``pending`` = a rewrite is underway."""
    team = await teams_service.get_team(session, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    text, source, pending = await team_summary.current(session, team)
    return TeamSummaryOut(team_id=team.id, text=text, source=source, pending=pending)


@router.post("/{team_id}/summary/refresh", response_model=TeamSummaryOut)
async def team_summary_refresh(
    team_id: int, session: AsyncSession = Depends(get_session)
) -> TeamSummaryOut:
    """Force a fresh summary now (the detail page's Regenerate button)."""
    team = await teams_service.get_team(session, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    result = await team_summary.refresh(team_id, force=True)
    text, source = result or ("No Pokémon yet.", "rules")
    return TeamSummaryOut(team_id=team.id, text=text, source=source)


@router.get("/{team_id}/analysis", response_model=TeamAnalysis)
async def analyze_team(
    team_id: int,
    opponent_id: int | None = Query(None, description="Compare against a saved opponent team"),
    session: AsyncSession = Depends(get_session),
) -> TeamAnalysis:
    team = await teams_service.get_team(session, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    opponent = None
    if opponent_id is not None:
        opponent = await teams_service.get_team(session, opponent_id)
        if opponent is None:
            raise HTTPException(status_code=404, detail="Opponent team not found")
    return await team_analysis.analyze(session, team, opponent)


@router.get("/{team_id}/duel", response_model=DuelOut)
async def duel_detail(
    team_id: int,
    opponent_id: int = Query(..., description="The other team"),
    our_slot: int = Query(..., ge=1, le=MAX_SLOTS),
    their_slot: int = Query(..., ge=1, le=MAX_SLOTS),
    session: AsyncSession = Depends(get_session),
) -> DuelOut:
    """One pairing played out turn by turn (set moves, items, abilities, setup)."""
    team = await teams_service.get_team(session, team_id)
    opponent = await teams_service.get_team(session, opponent_id)
    if team is None or opponent is None:
        raise HTTPException(status_code=404, detail="Team not found")
    out = await team_analysis.duel_detail(session, team, opponent, our_slot, their_slot)
    if out is None:
        raise HTTPException(status_code=404, detail="No Pokémon in that slot")
    return out


@router.post("/{team_id}/ask")
async def coach_ask(team_id: int, payload: CoachAskRequest) -> StreamingResponse:
    """SSE coaching over a team, planned like Ask (see ``app.agent``).

    Events: ``plan`` (the team context step first), ``step``*, ``view``* (candidates,
    set-edit proposals, adds, duels and dex views), ``team_updated`` after an explicit
    add, ``sources``, ``delta``*, ``done``.
    """

    async def event_stream() -> AsyncIterator[str]:
        planner = None
        try:
            async with async_session_factory() as session:
                team = await teams_service.get_team(session, team_id)
                if team is None:
                    yield _sse("error", {"message": "Team not found"})
                    return
                opponent = None
                if payload.opponent_id is not None:
                    opponent = await teams_service.get_team(session, payload.opponent_id)
                analysis = await team_analysis.analyze(session, team, opponent)
            ctx = AgentContext(scope="team", team=team, opponent=opponent,
                               report=payload.report, extra={"analysis": analysis})
            async for name, data in run_question(payload.question, "team", ctx=ctx):
                if name == "plan" and planner is None:
                    planner = data["planner"]
                if name == "done":
                    # Log before `done`: the client stops reading at `done`, which would
                    # cancel anything still running after it.
                    await _log(payload.question, planner)
                yield _sse(name, data)
        except Exception as exc:  # noqa: BLE001 — surface as a stream error event
            log.exception("coaching failed")
            yield _sse("error", {"message": f"Coaching failed: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _log(question: str, planner: str | None) -> None:
    """Record the question for personalization ("coach-llm" / "coach-keyword")."""
    try:
        async with async_session_factory() as session:
            await personalize.log_question(session, question, f"coach-{planner or 'keyword'}")
    except Exception:  # noqa: BLE001 — history is a nicety; never fail the answer for it
        log.warning("couldn't log the coach question", exc_info=True)


@router.put("/{team_id}", response_model=TeamOut)
async def update_team(
    team_id: int,
    payload: TeamUpdate,
    session: AsyncSession = Depends(get_session),
) -> TeamOut:
    team = await teams_service.update_team(session, team_id, payload)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    if not await teams_service.delete_team(session, team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    return Response(status_code=204)


@router.put("/{team_id}/slots/{slot}", response_model=TeamOut)
async def set_slot(
    team_id: int,
    slot: int,
    payload: SlotUpdate,
    session: AsyncSession = Depends(get_session),
) -> TeamOut:
    team = await teams_service.set_slot(session, team_id, slot, payload)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team_summary.schedule(team_id)  # roster changed → rewrite the summary in the background
    return team


@router.post("/{team_id}/slots/{slot}/build", response_model=TeamOut)
async def apply_slot_build(
    team_id: int,
    slot: int,
    payload: SlotBuild,
    session: AsyncSession = Depends(get_session),
) -> TeamOut:
    """Apply a set given by name (the coach's or the engine's suggestion) to a slot."""
    team = await teams_service.apply_build(session, team_id, slot, **payload.model_dump())
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team_summary.schedule(team_id)
    return team


@router.delete("/{team_id}/slots/{slot}", response_model=TeamOut)
async def clear_slot(
    team_id: int,
    slot: int,
    session: AsyncSession = Depends(get_session),
) -> TeamOut:
    team = await teams_service.clear_slot(session, team_id, slot)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team_summary.schedule(team_id)
    return team
