"""Semantic retrieval over knowledge chunks using pgvector cosine distance."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models import KnowledgeChunk, Pokemon
from app.rag.embeddings import embed_query


@dataclass
class RetrievedChunk:
    id: int
    pokemon_id: int | None
    pokemon_name: str | None
    dex_number: int | None
    chunk_type: str
    source_ref: str | None
    content: str
    score: float  # cosine similarity in [0, 1]
    # Raw numeric columns for structured rows, so answers can be rendered from
    # data rather than re-parsed from ``content``. None for text chunks.
    values: dict[str, float | None] | None = None
    # Structured extras for typed views (types, coverage moves, move facts), so the
    # UI never has to re-parse ``content``. Not shown to the LLM.
    meta: dict | None = None


async def retrieve(
    session: AsyncSession,
    query: str,
    *,
    k: int = 6,
    chunk_types: list[str] | None = None,
) -> list[RetrievedChunk]:
    # fastembed is synchronous/CPU-bound — keep it off the event loop.
    qvec = await run_in_threadpool(embed_query, query)

    distance = KnowledgeChunk.embedding.cosine_distance(qvec).label("distance")
    stmt = (
        select(KnowledgeChunk, distance, Pokemon.dex_number)
        .join(Pokemon, Pokemon.id == KnowledgeChunk.pokemon_id, isouter=True)
        .order_by(distance)
        .limit(k)
    )
    if chunk_types:
        stmt = stmt.where(KnowledgeChunk.chunk_type.in_(chunk_types))

    rows = (await session.execute(stmt)).all()
    return [
        RetrievedChunk(
            id=chunk.id,
            pokemon_id=chunk.pokemon_id,
            pokemon_name=chunk.pokemon_name,
            dex_number=dex,
            chunk_type=chunk.chunk_type,
            source_ref=chunk.source_ref,
            content=chunk.content,
            score=round(1.0 - float(dist), 4),
        )
        for chunk, dist, dex in rows
    ]
