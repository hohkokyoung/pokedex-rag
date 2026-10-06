"""Read-only plan traces: how each recent question was planned and answered."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import QuestionLog

router = APIRouter(prefix="/api/traces", tags=["traces"])


class TraceRow(BaseModel):
    id: int
    created_at: datetime
    question: str
    route: str | None
    scope: str | None
    planner: str | None
    fallback: str | None  # the planner's or the answer's fallback reason
    answer_tier: str | None
    llm_calls: int
    tools: list[str]


class TraceOut(BaseModel):
    id: int
    created_at: datetime
    question: str
    route: str | None
    trace: dict


def traced_rows(scope: str | None = None, planner: str | None = None,
                fallback: bool | None = None, limit: int = 50):
    """Newest traced questions first, with the trace filters applied (shared with the CLI)."""
    t = QuestionLog.trace
    stmt = select(QuestionLog).where(t.is_not(None))
    if scope:
        stmt = stmt.where(t["scope"].astext == scope)
    if planner:
        stmt = stmt.where(t["planner"].astext == planner)
    if fallback is not None:
        fell = or_(t["fallback"].astext.is_not(None), t["answer"]["fallback"].astext.is_not(None))
        stmt = stmt.where(fell if fallback else ~fell)
    return stmt.order_by(QuestionLog.id.desc()).limit(limit)


def summarize(row: QuestionLog) -> TraceRow:
    tr = row.trace or {}
    answer = tr.get("answer") or {}
    return TraceRow(
        id=row.id, created_at=row.created_at, question=row.question, route=row.route,
        scope=tr.get("scope"), planner=tr.get("planner"),
        fallback=tr.get("fallback") or answer.get("fallback"),
        answer_tier=answer.get("tier"),
        llm_calls=int((tr.get("usage") or {}).get("llm_calls") or 0),
        tools=[s.get("tool", "?") for s in tr.get("steps") or []],
    )


@router.get("", response_model=list[TraceRow])
async def list_traces(
    scope: Literal["ask", "team", "calc"] | None = None,
    planner: Literal["cached", "keyword", "llm"] | None = None,
    fallback: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[TraceRow]:
    rows = (await session.execute(traced_rows(scope, planner, fallback, limit))).scalars().all()
    return [summarize(r) for r in rows]


@router.get("/{trace_id}", response_model=TraceOut)
async def get_trace(trace_id: int, session: AsyncSession = Depends(get_session)) -> TraceOut:
    row = await session.get(QuestionLog, trace_id)
    if row is None or row.trace is None:
        raise HTTPException(status_code=404, detail="No trace for that id")
    return TraceOut(id=row.id, created_at=row.created_at, question=row.question,
                    route=row.route, trace=row.trace)
