"""Deterministic answers for the SQL route: every fact is rendered by code."""

from __future__ import annotations

import re

import pytest

from app.agent import executor
from app.agent import render as agent_render
from app.agent.keyword_planner import plan_keywords
from app.rag import sql_retrieval as sql
from app.rag.retrieval import RetrievedChunk
from app.rag.sql_retrieval import StatFilter, StructuredQuery
from app.rag.structured_answer import render


def _row(name: str, dex: int, **values: float) -> RetrievedChunk:
    return RetrievedChunk(
        id=-dex, pokemon_id=dex, pokemon_name=name, dex_number=dex,
        chunk_type="sql_row", source_ref="structured query", content=name,
        score=1.0, values=values,
    )


# ---- rendering (pure) ----

def test_ranking_names_top_with_value_and_lists_the_rest() -> None:
    q = StructuredQuery(sort_by="attack", order="desc", limit=3)
    rows = [_row("Kartana", 798, attack=181), _row("Rampardos", 409, attack=165),
            _row("Rayquaza", 384, attack=150)]
    out = render(q, rows, total=1025)
    first, *rest = out.split("\n\n")
    assert first == "**Kartana** has the highest Attack of any Pokémon at 181 [1]."
    assert "- **Rampardos** — 165 [2]\n- **Rayquaza** — 150 [3]" in out
    assert "Kartana" not in "".join(rest)  # opening item isn't repeated


def test_ranking_with_scope_and_ascending() -> None:
    q = StructuredQuery(types_all=["water"], generation=3, sort_by="speed", order="asc", limit=2)
    rows = [_row("Wailmer", 320, speed=60), _row("Corphish", 341, speed=35)]
    out = render(q, rows, total=28)
    assert out.startswith(
        "Among Water-type Pokémon from Generation 3, **Wailmer** has the lowest Speed at 60 [1]."
    )


def test_ranking_tie_names_every_leader() -> None:
    q = StructuredQuery(sort_by="speed", limit=3)
    rows = [_row("A", 1, speed=150), _row("B", 2, speed=150), _row("C", 3, speed=140)]
    out = render(q, rows, total=1025)
    assert out.startswith(
        "**A** [1] and **B** [2] are tied for the highest Speed of any Pokémon at 150."
    )
    assert "- **C** — 140 [3]" in out
    assert "- **A**" not in out and "- **B**" not in out


def test_height_uses_superlative_and_units() -> None:
    q = StructuredQuery(sort_by="height_m", limit=1)
    out = render(q, [_row("Eternatus", 890, height_m=20.0)], total=1025)
    assert out == "**Eternatus** is the tallest Pokémon at 20 m [1]."


def test_threshold_states_true_count_and_flags_truncation() -> None:
    q = StructuredQuery(
        types_all=["fire"],
        stat_filters=[StatFilter(stat="speed", op="gt", value=100)],
        sort_by="speed", limit=2,
    )
    rows = [_row("Blaziken", 257, speed=130), _row("Infernape", 392, speed=108)]
    out = render(q, rows, total=7)
    assert out.startswith(
        "7 Fire-type Pokémon have Speed above 100; **Blaziken** has the highest Speed "
        "among them at 130 [1]."
    )
    assert "- **Infernape** — Speed 108 [2]" in out
    assert out.endswith("Showing the top 2 of 7.")


def test_threshold_shows_sort_and_filter_values() -> None:
    q = StructuredQuery(stat_filters=[StatFilter(stat="speed", op="gte", value=100)],
                        sort_by="attack", limit=2)
    rows = [_row("A", 1, attack=150, speed=100), _row("B", 2, attack=140, speed=120)]
    out = render(q, rows, total=2)
    assert "Pokémon have Speed of at least 100" in out
    assert "- **B** — Attack 140, Speed 120 [2]" in out
    assert "Showing" not in out  # nothing hidden


def test_threshold_single_match() -> None:
    q = StructuredQuery(stat_filters=[StatFilter(stat="base_stat_total", op="gt", value=700)],
                        sort_by="base_stat_total")
    out = render(q, [_row("Arceus", 493, base_stat_total=720)], total=1)
    assert out == "Only 1 Pokémon has a base stat total above 700: **Arceus** at 720 [1]."


def test_plain_filter_counts_and_lists() -> None:
    q = StructuredQuery(types_all=["fire"], legendary=True)
    rows = [_row("Moltres", 146), _row("Entei", 244)]
    out = render(q, rows, total=9)
    assert out.startswith("There are 9 legendary Fire-type Pokémon.")
    assert "The first 2 by National Dex number:" in out
    assert "- **Moltres** — #146 [1]\n- **Entei** — #244 [2]" in out


def test_no_rows_is_an_honest_empty_answer() -> None:
    q = StructuredQuery(stat_filters=[StatFilter(stat="speed", op="gt", value=999)],
                        sort_by="speed")
    assert render(q, [], total=0) == "No Pokémon have Speed above 999."


def test_every_citation_points_at_a_row() -> None:
    q = StructuredQuery(sort_by="hp", limit=4)
    rows = [_row(n, i, hp=200 - i) for i, n in enumerate("ABCD", start=1)]
    out = render(q, rows, total=1025)
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", out)}
    assert cited == {1, 2, 3, 4}


# ---- end to end against the DB ----

async def test_count_matches_unlimited_rows(session) -> None:
    q = StructuredQuery(types_all=["fire"], legendary=True, limit=25)
    rows = await sql.execute(session, q)
    assert await sql.count(session, q) == len(rows)


async def test_rows_carry_values_and_height_in_content(session) -> None:
    rows = await sql.execute(session, StructuredQuery(sort_by="height_m", limit=1))
    assert rows[0].values is not None and rows[0].values["height_m"] > 10
    assert "Height" in rows[0].content


async def _keyword_answer(session_factory, question: str):
    """The keyword plan's code-rendered answer (None when it needs an LLM)."""
    async with session_factory() as s:
        kp = await plan_keywords(s, question)
    results = {e.step.id: e.result async for e in executor.run(kp.plan, session_factory)
               if e.result is not None}
    parts, offset = [], 0
    for step in kp.plan.steps:
        parts.append((step.tool, results[step.id], offset))
        offset += len(results[step.id].chunks)
    return kp, agent_render.render_all(parts)


@pytest.mark.parametrize(
    ("question", "expect"),
    [
        ("Which Pokémon has the highest Attack?", "**Kartana** has the highest Attack"),
        ("Which Pokémon have Speed above 130?", "Pokémon have Speed above 130"),
    ],
)
async def test_rankings_are_answered_without_llm(session_factory, question, expect) -> None:
    kp, answer = await _keyword_answer(session_factory, question)
    assert [s.tool for s in kp.plan.steps] == ["query_pokemon"]
    assert answer is not None and expect in answer


async def test_descriptions_are_left_to_the_llm(session_factory) -> None:
    _kp, answer = await _keyword_answer(session_factory, "Tell me about Bulbasaur")
    assert answer is None
