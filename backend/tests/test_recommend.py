"""Integration tests for the candidate recommender + species resolution.

Require a populated database; skipped otherwise (see conftest.session)."""

from __future__ import annotations

from app.models import Pokemon
from app.rag import coach
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import recommend, team_analysis
from app.services import teams as teams_service


async def _fresh_team(session, name: str, members: list[tuple[int, int]]):
    team = await teams_service.create_team(session, TeamCreate(name=name, kind="player"))
    for slot, pid in members:
        await teams_service.set_slot(session, team.id, slot, SlotUpdate(pokemon_id=pid))
    return await teams_service.get_team(session, team.id)


async def test_sweeper_recommendations_are_fast_and_non_legendary(session) -> None:
    team = await _fresh_team(session, "__test_rec_a__", [(1, 6)])  # Charizard
    try:
        analysis = await team_analysis.analyze(session, team)
        cands = await recommend.recommend_additions(
            session, team, analysis, "draft me sweepers, non legendary", limit=6
        )
        assert cands, "expected candidates"
        for c in cands:
            p = await session.get(Pokemon, c.pokemon_id)
            assert not p.is_legendary and not p.is_mythical  # non-legendary honoured
            assert c.base_stats["speed"] >= 90  # sweeper prefilter
    finally:
        await teams_service.delete_team(session, team.id)


async def test_recommendations_exclude_team_members(session) -> None:
    # Dragapult (887) is a fast sweeper that would otherwise be recommended.
    team = await _fresh_team(session, "__test_rec_b__", [(1, 887)])
    try:
        analysis = await team_analysis.analyze(session, team)
        cands = await recommend.recommend_additions(
            session, team, analysis, "draft me a sweeper", limit=10
        )
        assert all(c.pokemon_id != 887 for c in cands)
    finally:
        await teams_service.delete_team(session, team.id)


async def test_resolve_species_finds_multiword_name(session) -> None:
    poke = await coach.resolve_species(session, "please add Iron Hands to my squad")
    assert poke is not None and poke.name == "Iron Hands"
    single = await coach.resolve_species(session, "add garchomp now")
    assert single is not None and single.name == "Garchomp"
    assert await coach.resolve_species(session, "add xyzzy qwerty") is None
