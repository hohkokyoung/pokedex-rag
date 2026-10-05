"""A team slot can hold an alternate form (Mega, regional…): its typing, stats and
artwork apply, and it's validated against the form (or, lacking a learnset, the species)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.schemas.team import SlotUpdate, TeamCreate
from app.services import teams

GARCHOMP, MEGA_Z = 445, 10309  # Mega Garchomp Z: pure Dragon, no learnset of its own
EARTHQUAKE = 89


@pytest.fixture
async def team(session):
    t = await teams.create_team(session, TeamCreate(name="pytest-forms", kind="player"))
    yield t
    await teams.delete_team(session, t.id)


async def test_form_slot_hydrates_with_form_data(session, team) -> None:
    payload = SlotUpdate(pokemon_id=GARCHOMP, form_id=MEGA_Z, move_ids=[EARTHQUAKE])
    out = await teams.set_slot(session, team.id, 1, payload)
    m = out.members[0]
    assert m.form_id == MEGA_Z and m.pokemon_id == GARCHOMP
    assert m.name == "Mega Garchomp Z"
    assert m.types == ["dragon"]  # the form's typing, not Dragon/Ground
    assert m.base_stats["speed"] > 102  # form stats, not base Garchomp's
    assert "10309" in m.sprite_url
    # No form learnset in the dataset → the species' moves are legal.
    assert [mv.move_id for mv in m.moves] == [EARTHQUAKE]


async def test_form_must_belong_to_species(session, team) -> None:
    with pytest.raises(HTTPException) as e:
        await teams.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=6, form_id=MEGA_Z))
    assert e.value.status_code == 422


async def test_species_slot_has_no_form(session, team) -> None:
    out = await teams.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=GARCHOMP))
    m = out.members[0]
    assert m.form_id is None
    assert set(m.types) == {"dragon", "ground"}


async def test_held_item_round_trips(session, team) -> None:
    from sqlalchemy import select

    from app.models import Item

    stmt = select(Item).where(Item.identifier == "leftovers")
    leftovers = (await session.execute(stmt)).scalar_one()
    payload = SlotUpdate(pokemon_id=GARCHOMP, item_id=leftovers.id)
    out = await teams.set_slot(session, team.id, 1, payload)
    assert out.members[0].item is not None
    assert out.members[0].item.name == "Leftovers"
    with pytest.raises(HTTPException):
        await teams.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=GARCHOMP, item_id=999999))
