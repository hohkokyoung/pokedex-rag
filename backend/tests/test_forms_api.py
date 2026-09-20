"""Detail API embeds per-form evolution/flavor; a display-only form-moves route
serves the form learnset without touching the team-builder path."""

from __future__ import annotations

from app.services import builder, pokemon_query


async def test_galarian_darumaka_form_has_ice_stone_chain(session) -> None:
    detail = await pokemon_query.get_pokemon(session, "554")  # Darumaka species
    galar = next((f for f in detail.forms if f.id == 10176), None)
    assert galar is not None
    ids = {m.id for m in galar.evolution_members}
    assert {10176, 10177} <= ids, "expected Galarian Darumaka + Darmanitan as members"
    stage = next((s for s in galar.evolution_stages if s.to_id == 10177), None)
    assert stage is not None and "Ice Stone" in (stage.item or "")
    assert galar.flavor_texts == []  # panel will hide


async def test_form_moves_endpoint_serves_form_learnset(session) -> None:
    rows = await builder.legal_moves_for_form(session, 10229, None)  # Hisuian Growlithe
    assert rows, "expected a Hisuian Growlithe learnset"
    assert all(r.move_id for r in rows)


async def test_species_legal_moves_unchanged(session) -> None:
    rows = await builder.legal_moves(session, 58, None)  # base Growlithe
    assert rows  # regression guard: builder path still works
