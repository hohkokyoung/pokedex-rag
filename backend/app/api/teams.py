"""Team CRUD + per-slot editing (single local user, player & opponent teams)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ask import _sources, _sse
from app.core.config import get_settings
from app.core.database import async_session_factory, get_session
from app.models.team import MAX_SLOTS
from app.rag import answer as answer_service
from app.rag import coach, coach_edits, draft_intent, personalize, team_summary
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
from app.services import recommend, team_analysis, team_strategy
from app.services import teams as teams_service


def _next_empty_slot(team: TeamOut) -> int | None:
    used = {m.slot for m in team.members}
    return next((s for s in range(1, MAX_SLOTS + 1) if s not in used), None)


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
    """SSE coaching over a team: emits `sources`, `delta`* tokens, then `done`.

    Grounds the assistant in the team, its analysis, and (optionally) an opponent.
    With no LLM key, streams a single extractive brief built from the analysis.
    """
    settings = get_settings()

    async def event_stream() -> AsyncIterator[str]:
        async with async_session_factory() as session:
            try:
                team = await teams_service.get_team(session, team_id)
                if team is None:
                    yield _sse("error", {"message": "Team not found"})
                    return
                question = payload.question

                # --- conversational add: "add <name>" ---
                if coach.is_add_command(question):
                    poke = await coach.resolve_species(session, question)
                    if poke is not None:
                        async for evt in _handle_add(session, team, poke.id, poke.name):
                            yield evt
                        await personalize.log_question(session, question, "coach")
                        return

                opponent = None
                if payload.opponent_id is not None:
                    opponent = await teams_service.get_team(session, payload.opponent_id)
                analysis = await team_analysis.analyze(session, team, opponent)

                # --- drafting: surface candidate additions ---
                candidate_chunks = None
                candidates = []
                if coach.is_add_command(question) or recommend.is_draft_request(question):
                    prefs = await draft_intent.extract_draft_prefs(question)
                    candidates = await recommend.recommend_additions(
                        session, team, analysis, question, prefs=prefs
                    )
                    if candidates:
                        candidate_chunks = recommend.to_chunks(candidates)
                        yield _sse("candidates", [c.model_dump() for c in candidates])

                chunks = await coach.build_coach_chunks(
                    session, question, team, analysis, opponent, candidate_chunks,
                    report=payload.report,
                )
                yield _sse("sources", [s.model_dump() for s in _sources(chunks)])
                if settings.llm_enabled:
                    said: list[str] = []
                    async for delta in answer_service.stream_answer(
                        question, chunks, coach.COACH_NOTE
                    ):
                        said.append(delta)
                        yield _sse("delta", {"text": delta})
                    # Set advice in the answer → validated, appliable proposals.
                    edits = await coach_edits.extract_edits(session, "".join(said), team, opponent)
                    if edits:
                        yield _sse("edits", edits)
                elif candidates:
                    yield _sse("delta", {"text": coach.compose_extractive_draft(candidates)})
                elif payload.report:
                    # No LLM: answer with what the page shows rather than a different summary.
                    yield _sse("delta", {"text": payload.report})
                else:
                    yield _sse("delta", {"text": coach.compose_extractive_coach(analysis)})
                yield _sse("done", {})
                await personalize.log_question(session, question, "coach")
            except Exception as exc:  # noqa: BLE001 — surface as a stream error event
                yield _sse("error", {"message": f"Coaching failed: {exc}"})

    async def _handle_add(
        session: AsyncSession, team: TeamOut, pokemon_id: int, name: str
    ) -> AsyncIterator[str]:
        slot = _next_empty_slot(team)
        if slot is None:
            yield _sse(
                "delta",
                {"text": f"Your team is already full (6/6) — clear a slot before adding {name}."},
            )
            yield _sse("done", {})
            return
        if any(m.pokemon_id == pokemon_id for m in team.members):
            yield _sse("delta", {"text": f"{name} is already on this team."})
            yield _sse("done", {})
            return
        updated = await teams_service.set_slot(
            session, team.id, slot, SlotUpdate(pokemon_id=pokemon_id)
        )
        team_summary.schedule(team.id)
        yield _sse("team_updated", updated.model_dump())
        yield _sse(
            "delta",
            {
                "text": f"Added **{name}** to slot {slot}. Configure its ability, nature, "
                "EVs and moves from the slot, and ask me for the best spread."
            },
        )
        yield _sse("done", {})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
