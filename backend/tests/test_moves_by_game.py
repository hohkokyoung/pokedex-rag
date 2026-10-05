"""A Pokémon's learnset in one game (the Pokédex moveset's game picker)."""

from __future__ import annotations

from sqlalchemy import select

from app.models import PokemonForm, VersionGroup
from app.services.builder import moves_by_game


async def _vg(session, identifier: str) -> int:
    stmt = select(VersionGroup.id).where(VersionGroup.identifier == identifier)
    return (await session.execute(stmt)).scalar_one()


async def test_defaults_to_newest_game(session) -> None:
    out = await moves_by_game(session, 445)  # Garchomp
    assert out.version_group_id == out.games[0].id == await _vg(session, "scarlet-violet")
    gens = [g.generation for g in out.games]
    assert gens == sorted(gens, reverse=True)
    assert out.moves and all(m.learn_method for m in out.moves)


async def test_one_game_levels_and_tms(session) -> None:
    dp = await _vg(session, "diamond-pearl")
    out = await moves_by_game(session, 445, dp)
    assert out.version_group_id == dp
    by = {(m.name, m.learn_method): m for m in out.moves}
    assert by[("Dragon Claw", "level-up")].level == 33
    eq = by[("Earthquake", "machine")]
    assert eq.machine and eq.machine.startswith("TM")
    assert all(m.machine is None for m in out.moves if m.learn_method != "machine")


async def test_unknown_game_falls_back(session) -> None:
    out = await moves_by_game(session, 445, 99999)
    assert out.version_group_id == out.games[0].id


async def test_mega_uses_base_species(session) -> None:
    mega = (
        await session.execute(
            select(PokemonForm.id).where(PokemonForm.base_pokemon_id == 445).limit(1)
        )
    ).scalar_one_or_none()
    if mega is None:
        return
    out = await moves_by_game(session, mega)
    assert out.games and out.moves
