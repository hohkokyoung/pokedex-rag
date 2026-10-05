"""Tests for legendary negation + movepool-based coverage in Ask retrieval."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Pokemon, PokemonType
from app.rag import matchup
from app.rag.sql_retrieval import plan
from app.services import nlfilters


async def _types(session, pokemon_id: int) -> set[str]:
    p = (
        await session.execute(
            select(Pokemon)
            .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            .where(Pokemon.id == pokemon_id)
        )
    ).scalars().first()
    return {pt.type.identifier for pt in p.types}


# ---- pure: negation parsing ----


def test_legendary_negation() -> None:
    assert nlfilters.legendary_constraint("legendary fire types") is True
    assert nlfilters.legendary_constraint("non legendary sweepers") is False
    assert nlfilters.legendary_constraint("non-legendary") is False
    assert nlfilters.legendary_constraint("no legendaries please") is False
    assert nlfilters.legendary_constraint("fast attackers") is None


def test_legendary_sentiment_negation() -> None:
    # Open-ended rejection (no LLM) → exclude.
    for q in ("fuck legendaries, give me a team", "skip the legendaries",
              "without legendaries", "i don't want legendaries", "hate legendaries"):
        assert nlfilters.legendary_constraint(q) is False, q
    # Positive / trailing-negation must STAY include.
    for q in ("legendary dragons", "give me a legendary sweeper",
              "which legendary is not a dragon", "strongest legendary"):
        assert nlfilters.legendary_constraint(q) is True, q


def test_restricted_coupling() -> None:
    # "non legendary" should also drop mythicals unless mythicals are asked for.
    assert nlfilters.restricted_filters("non legendary") == (False, False)
    assert nlfilters.restricted_filters("legendary") == (True, None)
    assert nlfilters.restricted_filters("no legendaries but mythicals ok") == (False, True)


def test_sql_planner_respects_negation() -> None:
    assert plan("non legendary fire types with highest attack").legendary is False
    assert plan("legendary dragons").legendary is True


# ---- integration: coverage retrieval ----


async def test_non_legendary_coverage_excludes_restricted(session) -> None:
    q = "non legendary pokemon with highest sp attack that has coverage against dark"
    chunks, _note = await matchup.coverage(session, q, matchup.target_types(q), k=10)
    attackers = [c for c in chunks if c.chunk_type != "type_chart"]
    assert attackers
    for c in attackers:
        p = await session.get(Pokemon, c.pokemon_id)
        assert not p.is_legendary and not p.is_mythical


async def test_movepool_coverage_beyond_stab(session) -> None:
    # Dark is countered by fighting/bug/fairy. Movepool coverage should surface
    # attackers whose OWN typing is none of those but that can learn such a move.
    q = "special attacker with coverage against dark, highest sp attack"
    chunks, _note = await matchup.coverage(session, q, ["dark"], k=12)
    counter_types = {"fighting", "bug", "fairy"}
    off_type = [
        c.pokemon_name
        for c in chunks
        if c.pokemon_id is not None
        and counter_types.isdisjoint(await _types(session, c.pokemon_id))
    ]
    assert off_type, "expected coverage credited by learnset, not just STAB typing"


async def test_type_chart_chunk_answers_what_beats(session) -> None:
    # "what beats fire type" must be answerable from a citable chunk, not just the note.
    chunks, _note = await matchup.coverage(session, "what beats fire type", ["fire"], k=6)
    chart = chunks[0]
    assert chart.chunk_type == "type_chart" and chart.pokemon_id is None
    assert "Fire-type" in chart.content
    for weak in ("Ground", "Rock", "Water"):
        assert weak in chart.content.split("super-effective")[1].split(";")[0]


async def test_plain_what_beats_prefers_counter_types(session) -> None:
    # No "coverage"/special-attacker wording → Pokémon that ARE a counter type rank first,
    # and each attacker names the super-effective move it learns.
    chunks, _note = await matchup.coverage(session, "what beats fire type", ["fire"], k=6)
    attackers = [c for c in chunks if c.pokemon_id is not None]
    assert attackers
    for c in attackers:
        assert (await _types(session, c.pokemon_id)) & {"ground", "rock", "water"}, c.pokemon_name
        assert "Coverage moves it can learn:" in c.content, c.pokemon_name


def test_wants_moves_intent() -> None:
    for q in (
        "what moves beat fire pokemon",
        "best moves against water",
        "which move beats dragon",
    ):
        assert matchup.wants_moves(q), q
    for q in ("what beats fire type", "which pokemon has moves that beat fire",
              "a special attacker with moves against dark", "strongest attacker vs fire"):
        assert not matchup.wants_moves(q), q


async def test_move_question_returns_moves_not_pokemon(session) -> None:
    q = "what moves beat fire pokemon"
    chunks, note = await matchup.coverage(session, q, ["fire"], k=6)
    assert chunks[0].chunk_type == "type_chart"
    moves = chunks[1:]
    assert moves and all(c.chunk_type == "move" and c.pokemon_id is None for c in moves)
    by_type: dict[str, int] = {}
    for c in moves:
        assert "Super-effective vs Fire" in c.content
        mtype = c.content.split(" is a ")[1].split("-type")[0]
        assert mtype in {"Ground", "Rock", "Water"}
        by_type[mtype] = by_type.get(mtype, 0) + 1
    assert set(by_type) == {"Ground", "Rock", "Water"} and max(by_type.values()) <= 4
    # widely learned staples, not signature moves
    names = {c.source_ref for c in moves}
    assert {"Earthquake", "Surf"} <= names and "Precipice Blades" not in names
    assert "MOVES" in note


async def test_coverage_typed_special_vs_dark(session) -> None:
    from app.rag import matchup

    chunks, note = await matchup.coverage_typed(
        session, ["dark"], attacker_class="special", k=6
    )
    attackers = [c for c in chunks if c.chunk_type == "sql_row"]
    assert attackers, "expected special attackers covering Dark"
    for c in attackers:
        # Every listed coverage move is special and super-effective vs Dark.
        assert "Coverage moves it can learn:" in c.content
        assert "physical" not in c.content.split("Coverage moves it can learn:")[1]
    assert "special" in note
    # Ranked by Special Attack, highest first.
    spa = [c.values["sp_attack"] for c in attackers]
    assert spa == sorted(spa, reverse=True)


async def test_coverage_typed_excludes_legendaries(session) -> None:
    from sqlalchemy import select

    from app.models import Pokemon
    from app.rag import matchup

    chunks, _ = await matchup.coverage_typed(session, ["dragon"], legendary=False, k=8)
    ids = [c.pokemon_id for c in chunks if c.chunk_type == "sql_row"]
    legendary = (await session.execute(
        select(Pokemon.id).where(Pokemon.id.in_(ids), Pokemon.is_legendary.is_(True))
    )).scalars().all()
    assert ids and not legendary
