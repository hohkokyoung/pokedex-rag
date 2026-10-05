"""Integration tests for the team analysis + coach grounding path.

Require a populated database (Compose DB on host 5433 by default). Skipped when
it is unreachable or empty, so the rest of the suite still runs without the stack.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.rag import coach
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import team_analysis
from app.services import teams as teams_service


async def test_moves_and_natures_ingested(session) -> None:
    natures = (await session.execute(text("SELECT count(*) FROM natures"))).scalar()
    moves = (await session.execute(text("SELECT count(*) FROM moves"))).scalar()
    learn = (await session.execute(text("SELECT count(*) FROM pokemon_moves"))).scalar()
    assert natures == 25
    assert moves > 500
    assert learn > 10_000


async def test_fire_team_shared_weakness_and_coach_grounding(session) -> None:
    team = await teams_service.create_team(
        session, TeamCreate(name="__test_fire__", kind="player")
    )
    try:
        for slot, pid in ((1, 6), (2, 59), (3, 38)):  # Charizard, Arcanine, Ninetales
            await teams_service.set_slot(session, team.id, slot, SlotUpdate(pokemon_id=pid))

        full = await teams_service.get_team(session, team.id)
        assert full is not None
        analysis = await team_analysis.analyze(session, full)

        shared = {w.type for w in analysis.defensive.shared_weaknesses}
        assert "rock" in shared  # Fire/Flying etc. share a rock weakness
        assert "water" in shared

        chunks = await coach.build_coach_chunks(session, "How do I improve?", full, analysis)
        chunk_types = {c.chunk_type for c in chunks}
        assert "team_member" in chunk_types
        assert "team_analysis" in chunk_types

        brief = coach.compose_extractive_coach(analysis)
        assert "rock" in brief.lower() or "water" in brief.lower()
    finally:
        await teams_service.delete_team(session, team.id)


async def test_illegal_move_rejected(session) -> None:
    team = await teams_service.create_team(
        session, TeamCreate(name="__test_illegal__", kind="player")
    )
    try:
        with pytest.raises(HTTPException):
            await teams_service.set_slot(
                session, team.id, 1, SlotUpdate(pokemon_id=25, move_ids=[999_999])
            )
    finally:
        await teams_service.delete_team(session, team.id)


async def test_apply_build_by_name_and_reject_illegal(session) -> None:
    team = await teams_service.create_team(
        session, TeamCreate(name="__test_apply_build__", kind="player")
    )
    try:
        await teams_service.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=445))  # Garchomp
        out = await teams_service.apply_build(
            session, team.id, 1,
            moves=["Earthquake", "Dragon Claw"], ability="Rough Skin", nature="Jolly",
            item="Choice Scarf", evs={"atk": 252, "spe": 252, "hp": 4},
        )
        assert out is not None
        m = out.members[0]
        assert [mv.name for mv in m.moves] == ["Earthquake", "Dragon Claw"]
        assert m.ability and m.ability.name == "Rough Skin"
        assert m.nature and m.nature.name == "Jolly"
        assert m.item and m.item.name == "Choice Scarf"
        assert {k: v for k, v in m.ev_spread.items() if v} == {"attack": 252, "speed": 252, "hp": 4}
        # Fields left out keep what's set; an unlearnable move is refused.
        out = await teams_service.apply_build(session, team.id, 1, item="Leftovers")
        assert out is not None and out.members[0].ability.name == "Rough Skin"  # type: ignore[union-attr]
        with pytest.raises(HTTPException):
            await teams_service.apply_build(session, team.id, 1, moves=["Thunderbolt"])
    finally:
        await teams_service.delete_team(session, team.id)


async def test_page_report_is_the_coach_first_source(session) -> None:
    team = await teams_service.create_team(
        session, TeamCreate(name="__test_report__", kind="player")
    )
    try:
        await teams_service.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=445))
        full = await teams_service.get_team(session, team.id)
        assert full is not None
        analysis = await team_analysis.analyze(session, full)
        chunks = await coach.build_coach_chunks(
            session, "What's my biggest weakness?", full, analysis,
            report="Defence F: weak spots Ice, Dragon.",
        )
        assert chunks[0].chunk_type == "team_report"
        assert "Ice, Dragon" in chunks[0].content
        without = await coach.build_coach_chunks(session, "hi", full, analysis)
        assert all(c.chunk_type != "team_report" for c in without)
    finally:
        await teams_service.delete_team(session, team.id)


async def test_coach_edits_only_considered_for_set_advice_about_members(session) -> None:
    from app.rag import coach_edits

    team = await teams_service.create_team(
        session, TeamCreate(name="__test_edits__", kind="player")
    )
    try:
        await teams_service.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=445))
        full = await teams_service.get_team(session, team.id)
        assert full is not None
        assert coach_edits.worth_extracting("Give Garchomp a Jolly nature.", full, None)
        assert not coach_edits.worth_extracting("Your team is weak to Ice.", full, None)
        assert not coach_edits.worth_extracting("Run a Jolly nature on Pikachu.", full, None)
    finally:
        await teams_service.delete_team(session, team.id)
