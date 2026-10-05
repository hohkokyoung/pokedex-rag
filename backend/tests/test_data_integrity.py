"""Data-integrity checks for the ingested Pokémon dataset.

These require a populated database. They connect via ``DATABASE_URL`` (defaulting
to the Compose DB on host port 5433) and are skipped if it is unreachable or
empty, so the suite still runs on a machine without the stack up.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex",
).replace("+asyncpg", "+psycopg")


@pytest.fixture(scope="module")
def conn():
    engine = create_engine(DB_URL)
    try:
        connection = engine.connect()
    except OperationalError:
        pytest.skip("Database not reachable")
    try:
        count = connection.execute(text("SELECT count(*) FROM pokemon")).scalar()
    except Exception:
        pytest.skip("pokemon table not present")
    if not count:
        pytest.skip("Database not populated; run the ingestion pipeline")
    yield connection
    connection.close()


def test_pokemon_count(conn) -> None:
    assert conn.execute(text("SELECT count(*) FROM pokemon")).scalar() == 1025


def test_no_null_core_fields(conn) -> None:
    nulls = conn.execute(
        text("SELECT count(*) FROM pokemon WHERE name IS NULL OR base_stat_total = 0")
    ).scalar()
    assert nulls == 0


def test_reference_tables_populated(conn) -> None:
    assert conn.execute(text("SELECT count(*) FROM types")).scalar() == 19
    assert conn.execute(text("SELECT count(*) FROM generations")).scalar() == 9
    assert conn.execute(text("SELECT count(*) FROM abilities")).scalar() > 300


def test_bulbasaur_shape(conn) -> None:
    row = conn.execute(
        text(
            "SELECT name, hp, attack, base_stat_total FROM pokemon WHERE dex_number = 1"
        )
    ).one()
    assert row.name == "Bulbasaur"
    assert row.hp == 45
    assert row.attack == 49
    assert row.base_stat_total == 318


def test_bulbasaur_types(conn) -> None:
    types = conn.execute(
        text(
            """
            SELECT t.identifier FROM pokemon_types pt
            JOIN types t ON t.id = pt.type_id
            WHERE pt.pokemon_id = 1 ORDER BY pt.slot
            """
        )
    ).scalars().all()
    assert types == ["grass", "poison"]


def test_evolution_chain_bulbasaur(conn) -> None:
    edges = conn.execute(
        text(
            """
            SELECT from_pokemon_id, to_pokemon_id, min_level
            FROM pokemon_evolutions WHERE evolution_chain_id = 1
            ORDER BY to_pokemon_id
            """
        )
    ).all()
    assert (1, 2, 16) in [(e.from_pokemon_id, e.to_pokemon_id, e.min_level) for e in edges]
    assert (2, 3, 32) in [(e.from_pokemon_id, e.to_pokemon_id, e.min_level) for e in edges]


def test_highest_attack_is_kartana(conn) -> None:
    name = conn.execute(
        text("SELECT name FROM pokemon ORDER BY attack DESC, dex_number LIMIT 1")
    ).scalar()
    assert name == "Kartana"
