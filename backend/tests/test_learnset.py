"""Learnset retrieval for Ask: who learns a move, what a Pokémon learns, can X learn Y."""

from __future__ import annotations

import pytest
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


def test_how_by_game_names_the_newest_level() -> None:
    from app.rag.learnset import _how_by_game

    hist = [(52, "ruby-sapphire", 7), (51, "omega-ruby-alpha-sapphire", 18),
            (1, "sword-shield", 22), (1, "brilliant-diamond-shining-pearl", 25)]
    assert _how_by_game(hist) == "by level-up (Lv 1 in SwSh/BDSP; Lv 51–52 in other games)"
    assert _how_by_game([(52, "ruby-sapphire", 7), (52, "x-y", 17)]) is None  # one level
    assert _how_by_game(None) is None


async def test_any_game_level_is_game_aware(session) -> None:
    """The any-game table keeps the lowest level ("Lv 1"); answers say which games."""
    from app.rag.learnset import LearnsetPlan, retrieve_typed

    eq = await session.scalar(select(Move.id).where(Move.name == "Earthquake"))
    swampert = await session.scalar(select(Pokemon.id).where(Pokemon.name == "Swampert"))
    out = await retrieve_typed(session, LearnsetPlan(None, eq, ["water"], None), k=8)
    assert out.data["hows"][swampert].startswith("by level-up (Lv 1 in SwSh")
    out = await retrieve_typed(session, LearnsetPlan(swampert, eq, [], None))
    assert "in other games" in out.data["how"]


async def test_method_filter(session) -> None:
    """ "by levelling only" drops TM learners; a TM filter reads per game (a level-up
    learner that also takes the TM counts)."""
    from app.rag.learnset import LearnsetPlan, retrieve_typed

    eq = await session.scalar(select(Move.id).where(Move.name == "Earthquake"))
    lv = await retrieve_typed(session, LearnsetPlan(None, eq, ["water"], None, method="level-up"))
    assert set(lv.data["by_method"]) == {"level-up"}
    assert "Seismitoad" not in {pk.name for pk, _m, _l in lv.data["users"]}
    tm = await retrieve_typed(session, LearnsetPlan(None, eq, ["water"], None, method="machine"))
    allw = await retrieve_typed(session, LearnsetPlan(None, eq, ["water"], None))
    assert tm.data["total"] > allw.data["by_method"]["machine"]  # Swampert also takes the TM
    seismitoad = await session.scalar(select(Pokemon.id).where(Pokemon.name == "Seismitoad"))
    pair = await retrieve_typed(session, LearnsetPlan(seismitoad, eq, [], None, method="level-up"))
    assert not pair.data["ok"] and "doesn't learn Earthquake by level-up" in pair.chunks[0].content


async def test_pokemon_learnset_levels_name_their_games(session) -> None:
    from app.rag.learnset import LearnsetPlan, retrieve_typed

    swampert = await session.scalar(select(Pokemon.id).where(Pokemon.name == "Swampert"))
    eq = await session.scalar(select(Move.id).where(Move.name == "Earthquake"))
    out = await retrieve_typed(session, LearnsetPlan(swampert, None, [], None))
    assert out.data["varies"][eq] == "Lv 1 in SwSh/BDSP; Lv 51–52 in other games"
    text = next(c.content for c in out.chunks if "by level-up" in c.content)
    assert "Earthquake (Ground, physical, 100 power) at Lv 1 in SwSh/BDSP (Lv 51–52 in other " \
        "games)" in text


@pytest.mark.parametrize("text,want", [
    ("Scarlet/Violet", "Scarlet / Violet"), ("SwSh", "Sword / Shield"), ("sv", "Scarlet / Violet"),
    ("Sword & Shield", "Sword / Shield"), ("Let's Go", "Let’s Go, Pikachu / Eevee"),
    ("BDSP", "Brilliant Diamond / Shining Pearl"), ("Pokémon Emerald", "Emerald"),
])
async def test_resolve_game_spellings(session, text, want) -> None:
    vg = await learnset.resolve_game(session, text)
    assert vg is not None and vg.name == want


@pytest.mark.parametrize("q,want", [
    ("Top 5 by base stat total that are in Scarlet/Violet", "Scarlet / Violet"),
    ("strongest dragon in Pokémon Emerald", "Emerald"),
    ("Can Garchomp learn Earthquake in Emerald?", "Emerald"),
    ("best water types in sun and moon", "Sun / Moon"),
    ("which fire types are strong in the sun", None),  # everyday words need "Pokémon"
    ("top attack in red", None),
])
async def test_find_game_in_text(session, q, want) -> None:
    vg = await learnset.find_game_in_text(session, q)
    assert (vg.name if vg else None) == want


async def test_pair_says_when_the_pokemon_isnt_in_the_game(session) -> None:
    from app.rag.learnset import LearnsetPlan, retrieve_typed

    eq = await session.scalar(select(Move.id).where(Move.name == "Earthquake"))
    garchomp = await session.scalar(select(Pokemon.id).where(Pokemon.name == "Garchomp"))
    vg = await learnset.resolve_game(session, "Emerald")
    out = await retrieve_typed(session, LearnsetPlan(garchomp, eq, [], None,
                                                     version_group_id=vg.id, game=vg.name))
    assert out.data["absent"] and "isn't in Emerald at all" in out.chunks[0].content
