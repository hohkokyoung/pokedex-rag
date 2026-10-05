"""Hybrid retrieval: full-text (BM25-style) + vector search fused with RRF."""

from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag import retrieval
from app.rag.retrieval import RetrievedChunk

# Reciprocal Rank Fusion constant (standard default).
RRF_K = 60


def _or_tsquery(query: str) -> str:
    """Build an OR tsquery string from user text (recall-friendly for RRF).

    Tokens are sanitised to word characters, so the value is safe to pass to
    ``to_tsquery`` — no raw user text reaches the query parser.
    """
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    return " | ".join(tokens)


async def keyword_search(session: AsyncSession, query: str, k: int = 12) -> list[RetrievedChunk]:
    """Postgres full-text ranking over chunk content, ordered by ts_rank_cd."""
    tsq = _or_tsquery(query)
    if not tsq:
        return []
    sql = text(
        """
        SELECT kc.id, kc.pokemon_id, kc.pokemon_name, kc.chunk_type, kc.source_ref,
               kc.content, p.dex_number,
               ts_rank_cd(kc.content_tsv, to_tsquery('english', :q)) AS rank
        FROM knowledge_chunks kc
        LEFT JOIN pokemon p ON p.id = kc.pokemon_id
        WHERE kc.content_tsv @@ to_tsquery('english', :q)
        ORDER BY rank DESC
        LIMIT :k
        """
    )
    rows = (await session.execute(sql, {"q": tsq, "k": k})).all()
    return [
        RetrievedChunk(
            id=r.id,
            pokemon_id=r.pokemon_id,
            pokemon_name=r.pokemon_name,
            dex_number=r.dex_number,
            chunk_type=r.chunk_type,
            source_ref=r.source_ref,
            content=r.content,
            score=round(float(r.rank), 4),
        )
        for r in rows
    ]


def rrf_fuse(
    result_lists: list[list[RetrievedChunk]], *, top: int, k: int = RRF_K
) -> list[RetrievedChunk]:
    """Reciprocal Rank Fusion over several ranked lists, keyed by chunk id."""
    scores: dict[int, float] = {}
    by_id: dict[int, RetrievedChunk] = {}
    for results in result_lists:
        for rank, chunk in enumerate(results):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)
            by_id.setdefault(chunk.id, chunk)
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    fused: list[RetrievedChunk] = []
    for chunk_id, score in ordered[:top]:
        chunk = by_id[chunk_id]
        chunk.score = round(score, 5)
        fused.append(chunk)
    return fused


async def hybrid_retrieve(
    session: AsyncSession, query: str, *, k: int = 6
) -> list[RetrievedChunk]:
    """Vector + full-text retrieval fused with RRF."""
    vector_hits = await retrieval.retrieve(session, query, k=k * 2)
    keyword_hits = await keyword_search(session, query, k=k * 2)
    if not keyword_hits:
        return vector_hits[:k]
    return rrf_fuse([vector_hits, keyword_hits], top=k)
