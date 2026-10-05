"""Tests for the query router and hybrid retrieval."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.rag import hybrid, router

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex",
)


# ---- classification (pure) ----

@pytest.mark.parametrize(
    "question,expected",
    [
        ("Which Pokémon has the highest Attack?", "sql"),
        ("Fire-type Pokémon with Speed over 100", "sql"),
        ("Tell me about Bulbasaur", "semantic"),
        ("What is Mewtwo's origin?", "semantic"),
        ("Which Fire-type Pokémon live near volcanoes?", "hybrid"),
        ("strongest water type and where does it live", "hybrid"),
    ],
)
def test_classify(question: str, expected: str) -> None:
    route, _ = router.classify(question)
    assert route == expected


# ---- retrieval (needs DB) ----

@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(DB_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as s:
            count = (await s.execute(text("SELECT count(*) FROM knowledge_chunks"))).scalar()
            if not count:
                pytest.skip("knowledge_chunks not populated")
            yield s
    except OperationalError:
        pytest.skip("Database not reachable")
    finally:
        await engine.dispose()


async def test_keyword_search(session: AsyncSession) -> None:
    hits = await hybrid.keyword_search(session, "volcano lava fire", k=5)
    assert hits
    assert all(h.score >= 0 for h in hits)


async def test_hybrid_retrieve_fuses(session: AsyncSession) -> None:
    hits = await hybrid.hybrid_retrieve(session, "a legendary bird of fire", k=6)
    assert 1 <= len(hits) <= 6


async def test_route_sql_returns_ranked(session: AsyncSession) -> None:
    route, chunks = await router.route_and_retrieve(
        session, "Which Pokémon has the highest Attack?", k=5
    )
    assert route == "sql"
    assert chunks and chunks[0].pokemon_name == "Kartana"


async def test_route_semantic(session: AsyncSession) -> None:
    route, chunks = await router.route_and_retrieve(session, "Tell me about Bulbasaur", k=6)
    assert route == "semantic"
    assert any(c.pokemon_name == "Bulbasaur" for c in chunks)
