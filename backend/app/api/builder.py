"""Team-builder lookup endpoints: a species' legal moves & abilities, and natures."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Pokemon
from app.rag.build_suggest import BuildSuggestion, CoachTurn, SuggestError, suggest_build
from app.schemas.builder import (
    AbilityHolderOut,
    ItemOut,
    LearnsetMoveOut,
    MoveGameLearnersOut,
    MoveGameOut,
    MoveLearnerOut,
    MoveOut,
    NatureOut,
    PokemonGameMovesOut,
)
from app.schemas.pokemon import AbilityOut
from app.services import builder

router = APIRouter(prefix="/api", tags=["builder"])


async def _require_pokemon(session: AsyncSession, pokemon_id: int) -> None:
    if await session.get(Pokemon, pokemon_id) is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")


@router.get("/pokemon/{pokemon_id}/moves", response_model=list[LearnsetMoveOut])
async def pokemon_moves(
    pokemon_id: int,
    q: str | None = Query(None, description="Filter moves by name substring"),
    session: AsyncSession = Depends(get_session),
) -> list[LearnsetMoveOut]:
    await _require_pokemon(session, pokemon_id)
    return await builder.legal_moves(session, pokemon_id, q)


@router.get("/pokemon/forms/{form_id}/moves", response_model=list[LearnsetMoveOut])
async def pokemon_form_moves(
    form_id: int,
    q: str | None = Query(None, description="Filter moves by name substring"),
    session: AsyncSession = Depends(get_session),
) -> list[LearnsetMoveOut]:
    return await builder.legal_moves_for_form(session, form_id, q)


@router.get("/pokemon/{pokemon_id}/moves/by-game", response_model=PokemonGameMovesOut)
async def pokemon_moves_by_game(
    pokemon_id: int,
    version_group: int | None = Query(None, description="Game id; omit for the newest game"),
    session: AsyncSession = Depends(get_session),
) -> PokemonGameMovesOut:
    """A species' or form's (id > 10000) learnset in one game, with TM labels."""
    return await builder.moves_by_game(session, pokemon_id, version_group)


@router.get("/pokemon/{pokemon_id}/abilities", response_model=list[AbilityOut])
async def pokemon_abilities(
    pokemon_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[AbilityOut]:
    await _require_pokemon(session, pokemon_id)
    return await builder.species_abilities(session, pokemon_id)


@router.get("/moves", response_model=list[MoveOut])
async def search_moves(
    q: str | None = Query(None, description="Filter moves by name substring"),
    # High enough for the home finder to load every move (~900) at once.
    limit: int = Query(8, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> list[MoveOut]:
    return await builder.search_moves(session, q, limit)


@router.get("/moves/games", response_model=list[MoveGameOut])
async def move_games(session: AsyncSession = Depends(get_session)) -> list[MoveGameOut]:
    return await builder.move_games(session)


@router.get("/moves/{move_id}/learners", response_model=list[MoveLearnerOut])
async def move_learners(
    move_id: int,
    limit: int = Query(120, ge=1, le=400),
    session: AsyncSession = Depends(get_session),
) -> list[MoveLearnerOut]:
    return await builder.move_learners(session, move_id, limit)


@router.get("/moves/{move_id}/learners/by-game", response_model=MoveGameLearnersOut)
async def move_learners_by_game(
    move_id: int,
    version_group: int | None = Query(None, description="Game id; omit for every game"),
    session: AsyncSession = Depends(get_session),
) -> MoveGameLearnersOut:
    return await builder.move_learners_by_game(session, move_id, version_group)


@router.get("/abilities", response_model=list[AbilityOut])
async def search_abilities(
    q: str | None = Query(None, description="Filter abilities by name substring"),
    # High enough for the home finder to load every ability at once.
    limit: int = Query(8, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> list[AbilityOut]:
    return await builder.search_abilities(session, q, limit)


@router.get("/abilities/{ability_id}/pokemon", response_model=list[AbilityHolderOut])
async def ability_holders(
    ability_id: int,
    limit: int = Query(250, ge=1, le=400),
    session: AsyncSession = Depends(get_session),
) -> list[AbilityHolderOut]:
    return await builder.ability_holders(session, ability_id, limit)


@router.get("/items", response_model=list[ItemOut])
async def search_items(
    q: str | None = Query(None, description="Filter items by name substring"),
    # High enough for the home finder to load every item at once.
    limit: int = Query(8, ge=1, le=5000),
    held: bool = Query(False, description="Only items a Pokémon can hold in battle"),
    session: AsyncSession = Depends(get_session),
) -> list[ItemOut]:
    return await builder.search_items(session, q, limit, held)


@router.get("/natures", response_model=list[NatureOut])
async def list_natures(session: AsyncSession = Depends(get_session)) -> list[NatureOut]:
    return await builder.all_natures(session)


class SuggestBuildIn(BaseModel):
    pokemon_id: int
    form_id: int | None = None
    # Follow-up: the set being discussed, the user's new request, and earlier turns.
    current: BuildSuggestion | None = None
    request: str | None = None
    history: list[CoachTurn] = []


@router.post("/builds/suggest", response_model=BuildSuggestion)
async def suggest_build_endpoint(
    payload: SuggestBuildIn,
    session: AsyncSession = Depends(get_session),
) -> BuildSuggestion:
    """A coach-picked set (moves, ability, nature, item, EVs), validated against real data."""
    try:
        return await suggest_build(
            session,
            payload.pokemon_id,
            payload.form_id,
            request=payload.request,
            current=payload.current,
            history=payload.history,
        )
    except SuggestError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
