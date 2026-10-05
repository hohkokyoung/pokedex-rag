"""Tests for structured (SQL) retrieval: the heuristic planner and the executor."""

from __future__ import annotations

import os

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.rag import sql_retrieval as sql
from app.rag.sql_retrieval import StructuredQuery

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex",
)


# ---- planner (pure, no DB) ----

def test_plan_highest_attack() -> None:
    q = sql.plan("Which Pokémon has the highest Attack?")
    assert q is not None
    assert q.sort_by == "attack"
    assert q.order == "desc"


def test_plan_lowest_speed() -> None:
    q = sql.plan("weakest speed pokemon")
    assert q is not None
    assert q.sort_by == "speed"
    assert q.order == "asc"


def test_plan_type_and_threshold() -> None:
    q = sql.plan("Which Fire-type Pokémon have Speed above 100?")
    assert q is not None
    assert "fire" in q.types_all
    assert any(f.stat == "speed" and f.op == "gt" and f.value == 100 for f in q.stat_filters)


def test_plan_generation_and_legendary() -> None:
    q = sql.plan("strongest legendary in generation 1")
    assert q is not None
    assert q.generation == 1
    assert q.legendary is True
    assert q.sort_by == "base_stat_total"


def test_plan_non_structured_returns_none() -> None:
    assert sql.plan("Tell me about Bulbasaur's personality") is None


# ---- executor (needs DB) ----

@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(DB_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as s:
            from sqlalchemy import text

            count = (await s.execute(text("SELECT count(*) FROM pokemon"))).scalar()
            if not count:
                pytest.skip("Database not populated")
            yield s
    except OperationalError:
        pytest.skip("Database not reachable")
    finally:
        await engine.dispose()


async def test_execute_highest_attack(session: AsyncSession) -> None:
    q = StructuredQuery(sort_by="attack", order="desc", limit=1)
    rows = await sql.execute(session, q)
    assert rows and rows[0].pokemon_name == "Kartana"


async def test_execute_fire_speed_threshold(session: AsyncSession) -> None:
    q = StructuredQuery(
        types_all=["fire"],
        stat_filters=[{"stat": "speed", "op": "gt", "value": 100}],
        sort_by="speed",
        limit=25,
    )
    rows = await sql.execute(session, q)
    assert rows
    # every returned Pokémon should be Fire-type (content encodes the type)
    assert all("fire" in r.content for r in rows)


async def test_execute_legendary_filter(session: AsyncSession) -> None:
    q = StructuredQuery(legendary=True, sort_by="base_stat_total", limit=3)
    rows = await sql.execute(session, q)
    assert len(rows) == 3
