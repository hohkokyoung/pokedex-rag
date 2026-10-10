"""Pokédex read endpoints: list, detail, and filter metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import Generation, Pokemon, PokemonType, Type
from app.schemas.catch import BallOddsOut, CatchOut, CatchStatus, CatchTermsOut
from app.schemas.encounter import PokemonEncountersOut
from app.schemas.pokemon import (
    GenerationOut,
    PokemonDetail,
    PokemonListResponse,
    TypeChartOut,
    TypeOut,
)
from app.services import catch_rate, encounters, matchups, pokemon_query

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


@router.get("/pokemon/{pokemon_id}/catch", response_model=CatchOut)
async def catch_odds(
    pokemon_id: int,
    level: int = Query(30, ge=1, le=100, description="Wild level"),
    my_level: int = Query(30, ge=1, le=100, description="Your lead's level (Level Ball)"),
    hp_pct: int = Query(100, ge=1, le=100, description="Wild HP left, %"),
    turn: int = Query(1, ge=1, le=99),
    status: CatchStatus = "none",
    night: bool = Query(False, description="Night or in a cave (Dusk Ball)"),
    water: bool = Query(False, description="Fishing, surfing or underwater (Dive, Lure)"),
    caught: bool = Query(False, description="Species caught before (Repeat Ball)"),
    love_match: bool = Query(False, description="Lead: same species, opposite gender"),
    dex_caught: int = Query(0, ge=0, le=1025, description="Species caught (critical capture)"),
    charm: bool = Query(False, description="Catching Charm"),
    session: AsyncSession = Depends(get_session),
) -> CatchOut:
    """Every ball ranked by catch chance for this situation (Gen 8+ formula)."""
    p = (
        await session.execute(
            select(Pokemon).where(Pokemon.id == pokemon_id)
            .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        )
    ).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    mon = catch_rate.CatchMon(
        dex=p.dex_number, types=[pt.type.identifier for pt in p.types],
        capture_rate=p.capture_rate if p.capture_rate is not None else 45,
        base_hp=p.hp, base_speed=p.speed, weight_kg=p.weight_kg or 0,
        gender_rate=p.gender_rate if p.gender_rate is not None else 0,
    )
    ctx = catch_rate.Situation(hp_pct=hp_pct, level=level, my_level=my_level, turn=turn,
                               status=status, night=night, water=water, caught=caught,
                               love_match=love_match, dex_caught=dex_caught, charm=charm)
    return CatchOut(
        pokemon_id=p.id, name=p.name, capture_rate=mon.capture_rate,
        balls=[BallOddsOut(id=b.id, name=b.name, why=b.why, p=b.p, throws=b.throws, sure=b.sure,
                           terms=CatchTermsOut(**vars(b.terms)))
               for b in catch_rate.rank(mon, ctx)],
    )


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
