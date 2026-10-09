"""Pokédex read endpoints: list, detail, and filter metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Generation, Type
from app.schemas.encounter import PokemonEncountersOut
from app.schemas.pokemon import (
    GenerationOut,
    PokemonDetail,
    PokemonListResponse,
    TypeChartOut,
    TypeOut,
)
from app.services import encounters, matchups, pokemon_query

router = APIRouter(prefix="/api", tags=["pokedex"])

SORT_OPTIONS = {
    "dex", "name", "total", "hp", "attack", "defense", "sp_attack", "sp_defense", "speed"
}


@router.get("/pokemon", response_model=PokemonListResponse)
async def list_pokemon(
    q: str | None = Query(None, description="Search by name or dex number"),
    type: list[str] | None = Query(None, description="Filter by type id(s); all must match"),
    generation: list[int] | None = Query(
        None, description="Filter by generation(s) 1-9; any may match"
    ),
    legendary: bool | None = None,
    mythical: bool | None = None,
    sort: str = Query("dex"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(40, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PokemonListResponse:
    if sort not in SORT_OPTIONS:
        raise HTTPException(
            status_code=422, detail=f"Invalid sort; choose from {sorted(SORT_OPTIONS)}"
        )
    if generation and any(not 1 <= g <= 9 for g in generation):
        raise HTTPException(status_code=422, detail="generation must be between 1 and 9")
    items, total = await pokemon_query.list_pokemon(
        session,
        q=q,
        types=type,
        generation=generation,
        legendary=legendary,
        mythical=mythical,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return PokemonListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/pokemon/{id_or_name}", response_model=PokemonDetail)
async def get_pokemon(
    id_or_name: str,
    session: AsyncSession = Depends(get_session),
) -> PokemonDetail:
    detail = await pokemon_query.get_pokemon(session, id_or_name)
    if detail is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    return detail


@router.get("/pokemon/{pokemon_id}/encounters", response_model=PokemonEncountersOut)
async def pokemon_encounters(
    pokemon_id: int,
    version: int | None = Query(None, description="Game (version) id; omit for the newest"),
    session: AsyncSession = Depends(get_session),
) -> PokemonEncountersOut:
    """Where a species or form (id > 10000) is found in the wild, one game at a time."""
    return await encounters.encounters_by_game(session, pokemon_id, version)


@router.get("/types", response_model=list[TypeOut])
async def list_types(session: AsyncSession = Depends(get_session)) -> list[TypeOut]:
    rows = (await session.execute(select(Type).order_by(Type.id))).scalars().all()
    return [TypeOut.model_validate(t) for t in rows]


@router.get("/types/chart", response_model=TypeChartOut)
async def type_chart(session: AsyncSession = Depends(get_session)) -> TypeChartOut:
    """The type-effectiveness chart, from the ingested data. Static: clients fetch it once."""
    return TypeChartOut(order=matchups.ATTACK_ORDER, chart=await matchups.type_chart(session))


@router.get("/generations", response_model=list[GenerationOut])
async def list_generations(session: AsyncSession = Depends(get_session)) -> list[GenerationOut]:
    rows = (await session.execute(select(Generation).order_by(Generation.id))).scalars().all()
    return [GenerationOut.model_validate(g) for g in rows]
