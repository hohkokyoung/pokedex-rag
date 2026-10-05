"""Shared pytest fixtures.

The ``session`` fixture yields an async DB session bound to a fresh per-test engine
(so the connection pool never leaks across the loop each async test runs on). It
skips when the Compose DB is unreachable or unpopulated, so the pure-unit suite
still runs on a machine without the stack up.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(get_settings().database_url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as s:
            try:
                n = (await s.execute(text("SELECT count(*) FROM pokemon"))).scalar()
            except OperationalError:
                pytest.skip("Database not reachable")
            if not n:
                pytest.skip("Database not populated; run the ingestion pipeline")
            yield s
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory():
    """A sessionmaker on a fresh per-test engine, for code that opens its own sessions
    (the agent opens one per plan step). Skips like ``session`` without the DB."""
    engine = create_async_engine(get_settings().database_url)
    try:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as s:
            try:
                n = (await s.execute(text("SELECT count(*) FROM pokemon"))).scalar()
            except OperationalError:
                pytest.skip("Database not reachable")
            if not n:
                pytest.skip("Database not populated; run the ingestion pipeline")
        yield factory
    finally:
        await engine.dispose()
