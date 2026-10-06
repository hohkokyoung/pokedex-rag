"""Personalization: local profile, favourites, question history, recommendations.

Preferences and a few recent questions are used as *hints* — the system prompt
treats them as personalization, never as authoritative Pokémon facts. We never
inject the whole history: only recent questions and the compact profile.
"""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    KnowledgeChunk,
    Pokemon,
    PokemonType,
    QuestionLog,
    Type,
    UserFavorite,
    UserProfile,
)
from app.models.user import SOLE_PROFILE_ID
from app.rag.retrieval import RetrievedChunk
from app.rag.sql_retrieval import _row_to_chunk

_RECOMMEND_MARKERS = (
    "would i like", "would i enjoy", "would i probably", "probably like",
    "recommend", "suggest", "for me", "should i", "which pokemon do i",
    "based on my", "my favou", "my type", "i would probably", "pick for me",
    "what pokemon should",
)


def is_recommendation(question: str) -> bool:
    text = question.lower()
    return any(m in text for m in _RECOMMEND_MARKERS)


async def load_profile(session: AsyncSession) -> tuple[list[str], list[Pokemon]]:
    profile = await session.get(UserProfile, SOLE_PROFILE_ID)
    preferred = list(profile.preferred_types) if profile and profile.preferred_types else []

    fav_ids = (
        await session.execute(select(UserFavorite.pokemon_id))
    ).scalars().all()
    favorites: list[Pokemon] = []
    if fav_ids:
        favorites = list(
            (
                await session.execute(
                    select(Pokemon)
                    .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
                    .where(Pokemon.id.in_(fav_ids))
                    .order_by(Pokemon.dex_number)
                )
            ).scalars().all()
        )
    return preferred, favorites


async def log_question(
    session: AsyncSession, question: str, route: str, trace: dict | None = None
) -> None:
    session.add(QuestionLog(question=question, route=route, trace=trace))
    await session.commit()


async def recent_questions(
    session: AsyncSession, *, limit: int = 5, exclude: str | None = None
) -> list[str]:
    rows = (
        await session.execute(
            select(QuestionLog.question).order_by(desc(QuestionLog.created_at)).limit(limit + 1)
        )
    ).scalars().all()
    out: list[str] = []
    for q in rows:
        if exclude and q.strip().lower() == exclude.strip().lower():
            continue
        if q not in out:
            out.append(q)
        if len(out) >= limit:
            break
    return out


async def recommend_chunks(
    session: AsyncSession,
    preferred_types: list[str],
    favorites: list[Pokemon],
    *,
    k: int = 8,
) -> list[RetrievedChunk]:
    """Candidate Pokémon for a recommendation, from preferred/favourite types."""
    types = list(preferred_types)
    if not types and favorites:
        for f in favorites:
            types.extend(pt.type.identifier for pt in f.types)
    types = list(dict.fromkeys(types))
    favorite_ids = {f.id for f in favorites}

    stmt = (
        select(Pokemon)
        .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        .order_by(Pokemon.base_stat_total.desc())
        .limit(k)
    )
    if types:
        has_type = (
            select(PokemonType.pokemon_id)
            .join(Type, Type.id == PokemonType.type_id)
            .where(PokemonType.pokemon_id == Pokemon.id, Type.identifier.in_(types))
            .exists()
        )
        stmt = stmt.where(has_type)
    else:
        # No signal at all — recommend from legendaries as a sensible default.
        stmt = stmt.where(Pokemon.is_legendary.is_(True))
    if favorite_ids:
        stmt = stmt.where(Pokemon.id.notin_(favorite_ids))

    rows = (await session.execute(stmt)).scalars().all()
    return [_row_to_chunk(p) for p in rows]


def preference_block(
    preferred_types: list[str], favorites: list[Pokemon], recent: list[str]
) -> str:
    parts: list[str] = []
    if preferred_types:
        parts.append("Preferred types: " + ", ".join(t.title() for t in preferred_types) + ".")
    if favorites:
        parts.append("Favourite Pokémon: " + ", ".join(f.name for f in favorites) + ".")
    if recent:
        parts.append("Recent questions: " + " | ".join(f'"{q}"' for q in recent) + ".")
    if not parts:
        return ""
    return (
        "USER PROFILE (personalization hints only — NOT authoritative Pokémon facts):\n"
        + "\n".join(parts)
    )


async def favorite_profile_chunks(
    session: AsyncSession, favorites: list[Pokemon]
) -> list[RetrievedChunk]:
    """Profile chunks for the user's favourites, to ground 'like my favourites'."""
    if not favorites:
        return []
    ids = [f.id for f in favorites]
    rows = (
        await session.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.pokemon_id.in_(ids), KnowledgeChunk.chunk_type == "profile")
        )
    ).scalars().all()
    dex_by_id = {f.id: f.dex_number for f in favorites}
    return [
        RetrievedChunk(
            id=c.id,
            pokemon_id=c.pokemon_id,
            pokemon_name=c.pokemon_name,
            dex_number=dex_by_id.get(c.pokemon_id) if c.pokemon_id else None,
            chunk_type="profile",
            source_ref="favourite",
            content=c.content,
            score=1.0,
        )
        for c in rows
    ]
