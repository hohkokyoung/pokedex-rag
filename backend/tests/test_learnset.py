"""Learnset retrieval for Ask: who learns a move, what a Pokémon learns, can X learn Y."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models import Move, Pokemon, PokemonMove
from app.rag import learnset


async def _id(session, model, name: str) -> int:
    return (await session.execute(select(model.id).where(model.name == name))).scalar_one()


async def test_plan_detects_each_direction(session) -> None:
    eq = await _id(session, Move, "Earthquake")
    blaziken = await _id(session, Pokemon, "Blaziken")

    p = await learnset.plan(session, "what pokemon learns earthquake")
    assert p and p.move_id == eq and p.pokemon_id is None

    for q in (
        "what moves can blaziken learn",
        "all the moves blaziken cna learn",
        "Blaziken's moveset",
    ):
        p = await learnset.plan(session, q)
        assert p and p.pokemon_id == blaziken and p.move_id is None, q

    p = await learnset.plan(session, "can Blaziken learn Earthquake?")
    assert p and (p.pokemon_id, p.move_id) == (blaziken, eq)

    p = await learnset.plan(session, "which fire pokemon learn solar beam")
    assert p and p.types == ["fire"]


async def test_plan_leaves_other_questions_alone(session) -> None:
    for q in (
        "what moves beat fire pokemon",  # matchup: moves vs a type
        "what beats fire type",
        "Tell me about Kartana",
        "What is similar to Blaziken?",
        "Which Pokémon has the highest Attack?",
        "is surf good",  # a move name alone isn't a learnset question
    ):
        assert await learnset.plan(session, q) is None, q


async def test_learners_counts_and_best_users(session) -> None:
    q = "what pokemon learns earthquake"
    chunks, note = await learnset.retrieve(session, q, await learnset.plan(session, q))
    move, summary, *users = chunks
    eq = await _id(session, Move, "Earthquake")
    total = await session.scalar(
        select(func.count()).select_from(PokemonMove).where(PokemonMove.move_id == eq)
    )
    assert move.chunk_type == "move" and f"Learned by {total} Pokémon" in move.content
    assert summary.chunk_type == "learners" and summary.content.startswith(f"{total} Pokémon")
    assert users and all("Learns Earthquake" in u.content for u in users)
    assert "ground" in users[0].content  # same-type users rank first
    assert "Earthquake" in note


async def test_pokemon_learnset_covers_every_move(session) -> None:
    q = "what moves can blaziken learn"
    chunks, _note = await learnset.retrieve(session, q, await learnset.plan(session, q))
    groups = [c for c in chunks if c.chunk_type == "learnset"]
    assert {g.source_ref for g in groups} >= {"level-up", "TM"}
    listed = sum(int(g.content.split(" learns ")[1].split(" moves")[0]) for g in groups)
    blaziken = await _id(session, Pokemon, "Blaziken")
    total = await session.scalar(
        select(func.count()).select_from(PokemonMove).where(PokemonMove.pokemon_id == blaziken)
    )
    assert listed == total


async def test_pair_check_yes_and_no(session) -> None:
    for q, expect in (
        ("can blaziken learn earthquake?", "Blaziken can learn Earthquake by TM."),
        ("can charizard learn surf", "Charizard cannot learn Surf"),
    ):
        chunks, _note = await learnset.retrieve(session, q, await learnset.plan(session, q))
        assert chunks[0].source_ref == "learnset check"
        assert chunks[0].content.startswith(expect), chunks[0].content


# ---- typed entry point (used by the agent's learnset tool) ----


async def test_plan_typed_kinds(session) -> None:
    pair = await learnset.retrieve_typed(
        session, await learnset.plan_typed(session, pokemon="garchomp", move="Earthquake")
    )
    assert pair.kind == "pair" and pair.data["ok"] is True
    assert "can learn Earthquake" in pair.chunks[0].content

    learners = await learnset.retrieve_typed(
        session, await learnset.plan_typed(session, move="earthquake")
    )
    assert learners.kind == "learners" and learners.data["total"] > 100

    own = await learnset.retrieve_typed(
        session, await learnset.plan_typed(session, pokemon="Blaziken")
    )
    assert own.kind == "learnset" and own.data["groups"]


async def test_plan_typed_legendary_false_learners(session) -> None:
    from sqlalchemy import select

    from app.models import Pokemon

    out = await learnset.retrieve_typed(
        session, await learnset.plan_typed(session, move="Earthquake", legendary=False), k=25
    )
    ids = [pk.id for pk, _m, _lv in out.data["users"]]
    legendary = (await session.execute(
        select(Pokemon.id).where(Pokemon.id.in_(ids), Pokemon.is_legendary.is_(True))
    )).scalars().all()
    assert ids and not legendary
    assert "non-legendary" in out.data["scope"]


async def test_plan_typed_game_filter(session) -> None:
    p = await learnset.plan_typed(session, pokemon="Pikachu", move="Surf", game="scarlet")
    assert p.game and "Scarlet" in p.game
    out = await learnset.retrieve_typed(session, p)
    assert out.kind == "pair"
    assert "Scarlet" in out.chunks[0].content


async def test_plan_typed_unresolved(session) -> None:
    import pytest

    with pytest.raises(learnset.UnresolvedName) as e:
        await learnset.plan_typed(session, move="Notamove")
    assert e.value.kind == "move"
