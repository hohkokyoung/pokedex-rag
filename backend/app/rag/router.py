"""Query routing: decide SQL vs. semantic vs. hybrid retrieval, then dispatch.

The router is heuristic (no LLM required): it consults the structured planner
and looks for lore/description markers. Structured signals (rankings, stat
thresholds) route to SQL; descriptive questions route to semantic hybrid
retrieval; questions with both are answered from a merge of the two.
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag import hybrid, sql_retrieval
from app.rag.retrieval import RetrievedChunk

Route = Literal["sql", "semantic", "hybrid"]

_LORE_MARKERS = (
    "tell me about", "lore", "origin", "story", "describe", "description",
    "where does", "where do", "lives", "live", "habitat", "personality",
    "look like", "based on", "myth", "legend of", "behaviour", "behavior",
    "how does", "evolve", "diet", "eat", "sleep", "night", "day",
)


def classify(question: str) -> tuple[Route, sql_retrieval.StructuredQuery | None]:
    text = question.lower()
    sq = sql_retrieval.plan(question)
    has_structured = sq is not None
    strong_structured = has_structured and (sq.sort_by is not None or bool(sq.stat_filters))
    has_lore = any(m in text for m in _LORE_MARKERS)

    if strong_structured and has_lore:
        return "hybrid", sq
    if strong_structured:
        return "sql", sq
    if has_structured and has_lore:
        return "hybrid", sq
    if has_structured:
        return "sql", sq
    return "semantic", None


async def retrieve_for_route(
    session: AsyncSession,
    question: str,
    route: Route,
    *,
    k: int = 6,
    sq: sql_retrieval.StructuredQuery | None = None,
) -> tuple[Route, list[RetrievedChunk]]:
    """Run retrieval for an explicitly chosen route (used by both routers).

    ``sq`` may be supplied; otherwise the heuristic planner derives it for the
    sql/hybrid routes. Returns the *effective* route (it may downgrade to
    semantic if a structured query matched nothing).
    """
    if route == "sql":
        sq = sq or sql_retrieval.plan(question)
        if sq is not None:
            chunks = await sql_retrieval.execute(session, sq)
            if chunks:
                return "sql", chunks
        return "semantic", await hybrid.hybrid_retrieve(session, question, k=k)

    if route == "hybrid":
        sq = sq or sql_retrieval.plan(question)
        sql_chunks = await sql_retrieval.execute(session, sq) if sq is not None else []
        sem_chunks = await hybrid.hybrid_retrieve(session, question, k=k)
        merged: list[RetrievedChunk] = []
        seen: set[int] = set()
        # Structured rows first (authoritative for the constraint), then semantic.
        for chunk in [*sql_chunks[: max(3, k // 2)], *sem_chunks]:
            if chunk.id in seen:
                continue
            seen.add(chunk.id)
            merged.append(chunk)
            if len(merged) >= k + 3:
                break
        return "hybrid", merged

    return "semantic", await hybrid.hybrid_retrieve(session, question, k=k)


async def route_and_retrieve(
    session: AsyncSession, question: str, *, k: int = 6
) -> tuple[Route, list[RetrievedChunk]]:
    route, sq = classify(question)
    return await retrieve_for_route(session, question, route, k=k, sq=sq)
