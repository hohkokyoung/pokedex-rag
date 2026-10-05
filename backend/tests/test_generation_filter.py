"""The catalog's generation filter accepts several generations (any may match)."""

from __future__ import annotations

from app.services import pokemon_query


async def test_multiple_generations_union(session) -> None:
    _, gen1 = await pokemon_query.list_pokemon(session, generation=[1])
    _, gen3 = await pokemon_query.list_pokemon(session, generation=[3])
    items, both = await pokemon_query.list_pokemon(session, generation=[1, 3], limit=200)
    assert both == gen1 + gen3
    assert {i.generation_id for i in items} == {1, 3}


async def test_empty_generation_list_means_all(session) -> None:
    _, everything = await pokemon_query.list_pokemon(session)
    _, empty = await pokemon_query.list_pokemon(session, generation=[])
    assert empty == everything
