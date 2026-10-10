"""Moves carry their kind, and the moves nothing learns are placed in their games."""

from __future__ import annotations

import httpx
import pytest_asyncio

from app.services.move_kind import move_kind


def test_kind_rules():
    assert move_kind("max-airstream", "Max Airstream", 10) == "max"
    assert move_kind("g-max-wildfire", "G-Max Wildfire", 10) == "max"
    assert move_kind("breakneck-blitz--physical", "Breakneck Blitz", 1) == "z"
    assert move_kind("sketch", "Sketch", 1) == "regular"  # an ordinary 1-PP move
    assert move_kind("struggle", "Struggle", 1) == "regular"
    assert move_kind("earthquake", "Earthquake", 10) == "regular"


@pytest_asyncio.fixture
async def client(session):
    from app.core.database import get_session
    from app.main import app

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_session, None)


async def test_moves_carry_their_kind(client):
    moves = (await client.get("/api/moves?limit=2000")).json()
    kind = {m["name"]: m["kind"] for m in moves}
    assert kind["Max Airstream"] == "max"
    assert kind["Breakneck Blitz"] == "z"
    assert kind["Sketch"] == "regular" and kind["Earthquake"] == "regular"


async def test_games_include_moves_nothing_learns(client):
    moves = (await client.get("/api/moves?limit=2000")).json()
    by_name = {m["name"]: m["id"] for m in moves}
    z_ids = {m["id"] for m in moves if m["kind"] == "z"}
    listed = (await client.get("/api/moves/games")).json()
    games = {g["identifier"]: set(g["move_ids"]) for g in listed}
    assert by_name["Max Airstream"] in games["sword-shield"]
    assert not (z_ids & games["sword-shield"])
    assert z_ids <= games["sun-moon"] and z_ids <= games["ultra-sun-ultra-moon"]
    assert by_name["Max Airstream"] not in games["scarlet-violet"]
