"""A by-name search surfaces alternate forms (linking back to the base species'
page via form_id); the default browse grid stays default-species only."""

from __future__ import annotations

from app.services import pokemon_query


async def test_name_search_includes_forms(session) -> None:
    items, total = await pokemon_query.list_pokemon(session, q="hisuian growlithe")
    hg = next((i for i in items if i.form_id == 10229), None)
    assert hg is not None, "Hisuian Growlithe form should be searchable by name"
    assert hg.dex_number == 58  # links to the base species page
    assert "rock" in hg.types
    assert total >= 1


async def test_browse_has_no_forms(session) -> None:
    items, _ = await pokemon_query.list_pokemon(session, limit=60)
    assert all(i.form_id is None for i in items), "default browse must be species-only"


async def test_dex_number_search_stays_species_only(session) -> None:
    items, _ = await pokemon_query.list_pokemon(session, q="58")
    assert all(i.form_id is None for i in items)
    assert any(i.dex_number == 58 and i.form_id is None for i in items)
