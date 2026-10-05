"""Where to find a Pokémon in the wild, per game."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PokemonEncounter
from app.schemas.encounter import EncounterGameOut, EncounterOut, PokemonEncountersOut


async def encounters_by_game(
    session: AsyncSession, pokemon_id: int, version_id: int | None = None
) -> PokemonEncountersOut:
    """A species' or form's (id > 10000) encounters in one game (default: the newest).

    Forms are not folded into their base species: an Alolan Rattata lives in
    different places than a Kantonian one, and a Mega form is never wild.
    """
    E = PokemonEncounter
    games = [
        EncounterGameOut(version_id=v, version=name, generation=gen, places=n)
        for v, name, gen, n in (
            await session.execute(
                select(E.version_id, E.version, E.generation, func.count(func.distinct(E.location)))
                .where(E.pokemon_id == pokemon_id)
                .group_by(E.version_id, E.version, E.generation, E.sort_order)
                .order_by(E.sort_order)
            )
        ).all()
    ]
    if not games:
        return PokemonEncountersOut(version_id=None, games=[], encounters=[])
    if version_id not in {g.version_id for g in games}:
        version_id = games[-1].version_id
    rows = (
        await session.execute(
            select(E)
            .where(E.pokemon_id == pokemon_id, E.version_id == version_id)
            .order_by(E.location, E.area.nulls_first(), E.method_name, E.min_level)
        )
    ).scalars()
    return PokemonEncountersOut(
        version_id=version_id,
        games=games,
        encounters=[EncounterOut.model_validate(r) for r in rows],
    )
