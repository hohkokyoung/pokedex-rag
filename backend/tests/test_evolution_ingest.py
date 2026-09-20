"""The species-level evolution edge must use the DEFAULT-form method, not the
last CSV row (a form-split species like Darmanitan otherwise shows the Galarian
Ice Stone trigger on its default page)."""

from __future__ import annotations

from sqlalchemy import select

from app.models import PokemonEvolution


async def test_darmanitan_species_edge_is_level_up(session) -> None:
    # Darmanitan species id = 555; default (Unovan) path is level-up @ 35.
    rows = (
        await session.execute(
            select(PokemonEvolution).where(PokemonEvolution.to_pokemon_id == 555)
        )
    ).scalars().all()
    assert rows, "expected a species evolution edge for Darmanitan"
    # Exactly one species edge, and it is the Lv.35 level-up (not Ice Stone).
    assert len(rows) == 1
    edge = rows[0]
    assert edge.min_level == 35
    assert edge.item is None
