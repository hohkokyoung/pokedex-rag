"""Similarity retrieval: "which Pokémon are similar to X?".

Naive semantic search fails here — the chunks closest to a query mentioning X
are X's *own* entries. Instead we resolve the target Pokémon, then find the
nearest *other* species by comparing profile embeddings (which encode type,
stats, abilities and role), excluding the target's own evolution line.
"""

from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeChunk, Pokemon
from app.rag.retrieval import RetrievedChunk

_MARKERS = (
    "similar to", "similar", "resembl", "comparable", "reminiscent", "closest to",
    "pokemon like", "pokémon like", "mon like", "alternatives to", "compare to",
    "others like", "something like", "same as",
)


def is_similarity(question: str) -> bool:
    t = question.lower()
    return any(m in t for m in _MARKERS)


async def find_target(session: AsyncSession, question: str) -> Pokemon | None:
    """Resolve a Pokémon named in the question (longest name match wins)."""
    tokens = {w for w in re.findall(r"[a-z0-9'.-]{3,}", question.lower())}
    if not tokens:
        return None
    rows = (
        await session.execute(
            select(Pokemon).where(func.lower(Pokemon.name).in_(tokens))
        )
    ).scalars().all()
    return max(rows, key=lambda p: len(p.name)) if rows else None


async def resolve_by_name(session: AsyncSession, name: str | None) -> Pokemon | None:
    """Look up a Pokémon by (case-insensitive) name — used with an LLM-extracted target."""
    if not name:
        return None
    return (
        await session.execute(
            select(Pokemon).where(func.lower(Pokemon.name) == name.strip().lower()).limit(1)
        )
    ).scalars().first()


async def target_profile_chunk(
    session: AsyncSession, target: Pokemon
) -> RetrievedChunk | None:
    """The target's own profile as a chunk (to include it alongside look-alikes)."""
    chunk = (
        await session.execute(
            select(KnowledgeChunk).where(
                KnowledgeChunk.pokemon_id == target.id,
                KnowledgeChunk.chunk_type == "profile",
            ).limit(1)
        )
    ).scalars().first()
    if chunk is None:
        return None
    return RetrievedChunk(
        id=chunk.id,
        pokemon_id=target.id,
        pokemon_name=target.name,
        dex_number=target.dex_number,
        chunk_type="profile",
        source_ref="target",
        content=chunk.content,
        score=1.0,
    )


async def similar_to(
    session: AsyncSession, target: Pokemon, *, k: int = 6
) -> list[RetrievedChunk]:
    emb = (
        await session.execute(
            select(KnowledgeChunk.embedding).where(
                KnowledgeChunk.pokemon_id == target.id,
                KnowledgeChunk.chunk_type == "profile",
            ).limit(1)
        )
    ).scalars().first()
    if emb is None:
        return []

    distance = KnowledgeChunk.embedding.cosine_distance(emb).label("distance")
    stmt = (
        select(KnowledgeChunk, distance, Pokemon.dex_number)
        .join(Pokemon, Pokemon.id == KnowledgeChunk.pokemon_id)
        .where(
            KnowledgeChunk.chunk_type == "profile",
            KnowledgeChunk.pokemon_id != target.id,
        )
        .order_by(distance)
        .limit(k)
    )
    # Exclude the target's own evolution line so we surface other species.
    if target.evolution_chain_id is not None:
        stmt = stmt.where(Pokemon.evolution_chain_id != target.evolution_chain_id)

    rows = (await session.execute(stmt)).all()
    return [
        RetrievedChunk(
            id=chunk.id,
            pokemon_id=chunk.pokemon_id,
            pokemon_name=chunk.pokemon_name,
            dex_number=dex,
            chunk_type="profile",
            source_ref="similar",
            content=chunk.content,
            score=round(1.0 - float(dist), 4),
        )
        for chunk, dist, dex in rows
    ]
