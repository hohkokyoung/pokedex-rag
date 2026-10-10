"""The catalog's type filter: several types list Pokémon with any of them."""

from __future__ import annotations

from app.services import pokemon_query


async def test_types_any_may_match(session) -> None:
    _, fire = await pokemon_query.list_pokemon(session, types=["fire"])
    _, water = await pokemon_query.list_pokemon(session, types=["water"])
    _, grass = await pokemon_query.list_pokemon(session, types=["grass"])
    items, any_of = await pokemon_query.list_pokemon(
        session, types=["fire", "water", "grass"], limit=200
    )
    # A Pokémon with two of them (e.g. Water/Grass Lotad) is counted once.
    assert max(fire, water, grass) < any_of <= fire + water + grass
    assert all({"fire", "water", "grass"} & set(i.types) for i in items)


async def test_dual_type_pokemon_appears_under_either(session) -> None:
    items, _ = await pokemon_query.list_pokemon(session, types=["poison", "dragon"], limit=200)
    assert "Bulbasaur" in {i.name for i in items}  # Grass/Poison: has one of them
