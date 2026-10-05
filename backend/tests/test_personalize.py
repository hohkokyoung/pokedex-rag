"""Tests for personalization: intent detection and preference-driven recommendations."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Pokemon
from app.rag import personalize

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex",
)


@pytest.mark.parametrize(
    "q,expected",
    [
        ("Which Pokémon would I probably like?", True),
        ("recommend a pokemon for me", True),
        ("what should I pick for me", True),
        ("Tell me about Bulbasaur", False),
        ("highest attack pokemon", False),
    ],
)
def test_is_recommendation(q: str, expected: bool) -> None:
    assert personalize.is_recommendation(q) is expected


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(DB_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as s:
            count = (await s.execute(text("SELECT count(*) FROM pokemon"))).scalar()
            if not count:
                pytest.skip("Database not populated")
            yield s
    except OperationalError:
        pytest.skip("Database not reachable")
    finally:
        await engine.dispose()


async def test_recommend_respects_preferred_types(session: AsyncSession) -> None:
    charizard = await session.get(Pokemon, 6)  # for favourite-exclusion
    recs = await personalize.recommend_chunks(session, ["dragon"], [charizard], k=6)
    assert recs
    assert all("dragon" in r.content for r in recs)
    assert all(r.pokemon_id != 6 for r in recs)


async def test_recommend_fallback_legendary(session: AsyncSession) -> None:
    recs = await personalize.recommend_chunks(session, [], [], k=5)
    assert len(recs) == 5  # falls back to legendaries when no signal
