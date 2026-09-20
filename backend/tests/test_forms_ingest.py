"""Per-form enrichment: learnset, evolution linkage, and (where the data has it)
form-specific flavor text."""

from __future__ import annotations

from app.models import PokemonForm


async def _form(session, form_pokemon_id: int) -> PokemonForm | None:
    return await session.get(PokemonForm, form_pokemon_id)


async def test_hisuian_growlithe_has_own_learnset(session) -> None:
    # Hisuian Growlithe form pokemon.id = 10229.
    f = await _form(session, 10229)
    assert f is not None
    assert f.learnset, "expected a per-form learnset"
    assert all({"move_id", "method"} <= set(m) for m in f.learnset)


async def test_galarian_darmanitan_form_evolution_linkage(session) -> None:
    # Galarian Darmanitan (10177) evolves from Galarian Darumaka (10176) via Ice Stone.
    f = await _form(session, 10177)
    assert f is not None
    assert f.evolves_from_form_id == 10176
    assert f.evo_item == "Ice Stone"


async def test_galarian_darumaka_has_no_form_flavor(session) -> None:
    # Gen-8 regionals have no pokemon_form_flavor_text -> empty, panel hides.
    f = await _form(session, 10176)
    assert f is not None
    assert f.flavor_texts == []
