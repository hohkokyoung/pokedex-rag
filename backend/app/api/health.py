"""Health endpoints: liveness and readiness (DB connectivity)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["up", "down"]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe — the process is running."""
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(session: AsyncSession = Depends(get_session)) -> ReadinessResponse:
    """Readiness probe — verifies the database is reachable."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        return ReadinessResponse(status="degraded", database="down")
    return ReadinessResponse(status="ok", database="up")
