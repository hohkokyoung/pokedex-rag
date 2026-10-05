"""Local user profile: preferred types and favourite Pokémon (single user)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import Pokemon, PokemonType, Type, UserFavorite, UserProfile
from app.models.user import SOLE_PROFILE_ID
from app.schemas.profile import FavoriteOut, ProfileOut, ProfileUpdate
from app.services.pokemon_query import sprite_url

router = APIRouter(prefix="/api/profile", tags=["profile"])


async def _get_or_create_profile(session: AsyncSession) -> UserProfile:
    profile = await session.get(UserProfile, SOLE_PROFILE_ID)
    if profile is None:
        profile = UserProfile(id=SOLE_PROFILE_ID, preferred_types=[])
        session.add(profile)
        await session.commit()
    return profile


async def _favorites(session: AsyncSession) -> list[FavoriteOut]:
    ids = (await session.execute(select(UserFavorite.pokemon_id))).scalars().all()
    if not ids:
        return []
    rows = (
        await session.execute(
            select(Pokemon)
            .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            .where(Pokemon.id.in_(ids))
            .order_by(Pokemon.dex_number)
        )
    ).scalars().all()
    return [
        FavoriteOut(
            id=p.id,
            dex_number=p.dex_number,
            name=p.name,
            types=[pt.type.identifier for pt in p.types],
            sprite_url=sprite_url(p),
        )
        for p in rows
    ]


@router.get("", response_model=ProfileOut)
async def get_profile(session: AsyncSession = Depends(get_session)) -> ProfileOut:
    profile = await _get_or_create_profile(session)
    return ProfileOut(
        preferred_types=list(profile.preferred_types or []),
        favorites=await _favorites(session),
    )


@router.put("", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    valid = {t for t in (await session.execute(select(Type.identifier))).scalars().all()}
    cleaned = [t for t in dict.fromkeys(payload.preferred_types) if t in valid]
    profile = await _get_or_create_profile(session)
    profile.preferred_types = cleaned
    await session.commit()
    return ProfileOut(preferred_types=cleaned, favorites=await _favorites(session))


@router.post("/favorites/{pokemon_id}", response_model=ProfileOut)
async def add_favorite(
    pokemon_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    if await session.get(Pokemon, pokemon_id) is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    if await session.get(UserFavorite, pokemon_id) is None:
        session.add(UserFavorite(pokemon_id=pokemon_id))
        await session.commit()
    await _get_or_create_profile(session)
    profile = await session.get(UserProfile, SOLE_PROFILE_ID)
    return ProfileOut(
        preferred_types=list(profile.preferred_types or []),
        favorites=await _favorites(session),
    )


@router.delete("/favorites/{pokemon_id}", response_model=ProfileOut)
async def remove_favorite(
    pokemon_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    fav = await session.get(UserFavorite, pokemon_id)
    if fav is not None:
        await session.delete(fav)
        await session.commit()
    profile = await _get_or_create_profile(session)
    return ProfileOut(
        preferred_types=list(profile.preferred_types or []),
        favorites=await _favorites(session),
    )
