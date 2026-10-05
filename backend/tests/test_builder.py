"""Tests for the global move/ability lookup service.

Uses the ``session`` fixture, which skips when the Compose DB is unreachable or
unpopulated (so the pure-unit suite still runs without the stack up).
"""

from __future__ import annotations

import pytest

from app.services import builder


async def test_search_moves_by_name(session) -> None:
    rows = await builder.search_moves(session, "ice beam", limit=8)
    assert rows, "expected at least one match for 'ice beam'"
    assert any(m.name.lower() == "ice beam" for m in rows)
    top = rows[0]
    assert top.type == "ice"
    assert top.damage_class in {"physical", "special", "status"}


async def test_search_moves_orders_damaging_first(session) -> None:
    rows = await builder.search_moves(session, "beam", limit=20)
    assert rows
    # Status moves (no power) must not precede damaging ones.
    seen_status = False
    for m in rows:
        if m.damage_class == "status":
            seen_status = True
        elif seen_status:
            raise AssertionError("a damaging move followed a status move in the ordering")


async def test_search_moves_respects_limit(session) -> None:
    rows = await builder.search_moves(session, None, limit=5)
    assert len(rows) == 5


async def test_search_abilities_by_name(session) -> None:
    rows = await builder.search_abilities(session, "intimidate", limit=8)
    assert rows
    assert any(a.name.lower() == "intimidate" for a in rows)


async def test_ability_holders_lists_species(session) -> None:
    abilities = await builder.search_abilities(session, "intimidate", limit=8)
    ability = next(a for a in abilities if a.name.lower() == "intimidate")
    holders = await builder.ability_holders(session, ability.id, limit=250)
    assert holders, "expected species that have Intimidate"
    # Gyarados (#130) is a classic Intimidate holder.
    assert any(h.dex_number == 130 for h in holders)
    top = holders[0]
    assert top.types, "each holder carries its types"
    assert isinstance(top.is_hidden, bool)
    # Ordered by dex number ascending.
    dexes = [h.dex_number for h in holders]
    assert dexes == sorted(dexes)


async def test_ability_holders_respects_limit(session) -> None:
    abilities = await builder.search_abilities(session, "levitate", limit=8)
    ability = next(a for a in abilities if a.name.lower() == "levitate")
    holders = await builder.ability_holders(session, ability.id, limit=3)
    assert len(holders) <= 3


def test_load_move_targets_maps_doubles_targeting() -> None:
    """Pure CSV read: each move's PokéAPI target identifier (no DB needed)."""
    from app.ingest.run import load_move_targets

    targets = load_move_targets()
    assert targets[89] == "all-other-pokemon"  # Earthquake hits the ally too
    assert targets[157] == "all-opponents"  # Rock Slide
    assert targets[200] == "random-opponent"  # Outrage
    assert targets[270] == "ally"  # Helping Hand
    assert targets[444] == "selected-pokemon"  # Stone Edge


async def test_legal_moves_carry_target(session) -> None:
    rows = {m.identifier: m for m in await builder.legal_moves(session, 445, None)}  # Garchomp
    assert rows["earthquake"].target == "all-other-pokemon"
    assert rows["rock-slide"].target == "all-opponents"
    assert rows["outrage"].target == "random-opponent"


async def test_legal_moves_carry_priority(session) -> None:
    rows = {m.identifier: m for m in await builder.legal_moves(session, 25, None)}  # Pikachu
    assert rows["quick-attack"].priority == 1
    assert rows["fake-out"].priority == 3
    assert rows["thunderbolt"].priority == 0


@pytest.mark.parametrize(
    ("path", "model_name", "limit"),
    [
        ("/api/moves", "Move", 2000),
        ("/api/abilities", "Ability", 2000),
        ("/api/items", "Item", 5000),
    ],
)
async def test_finder_endpoints_can_list_everything(session, path, model_name, limit) -> None:
    """The home finder loads each whole catalog (moves / abilities / items) in one call."""
    import httpx
    from sqlalchemy import func, select

    from app import models
    from app.core.database import get_session
    from app.main import app

    model = getattr(models, model_name)
    total = (await session.execute(select(func.count(model.id)))).scalar_one()

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(path, params={"limit": limit})
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert resp.status_code == 200
    assert len(resp.json()) == total
