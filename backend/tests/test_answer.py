"""Tests for the no-LLM extractive answer fallback (pure, no DB / no key)."""

from __future__ import annotations

from app.rag.answer import compose_extractive_answer
from app.rag.retrieval import RetrievedChunk


def _chunk(id_, name, dex, ctype, content, score=1.0):
    return RetrievedChunk(
        id=id_, pokemon_id=dex, pokemon_name=name, dex_number=dex,
        chunk_type=ctype, source_ref=None, content=content, score=score,
    )


def test_empty_abstains() -> None:
    assert "don't have" in compose_extractive_answer([]).lower()


def test_profile_lead_has_citation() -> None:
    chunks = [
        _chunk(1, "Bulbasaur", 1, "profile", "Bulbasaur is a Grass/Poison-type Pokémon."),
        _chunk(2, "Bulbasaur", 1, "dex_entry", "Bulbasaur — Pokédex entry: A strange seed."),
    ]
    out = compose_extractive_answer(chunks)
    assert "Bulbasaur" in out
    assert "[1]" in out  # citation aligned to the profile chunk


def test_ranking_list() -> None:
    chunks = [
        _chunk(-798, "Kartana", 798, "sql_row", "Kartana (#798): Attack 181."),
        _chunk(-409, "Rampardos", 409, "sql_row", "Rampardos (#409): Attack 165."),
    ]
    out = compose_extractive_answer(chunks)
    assert "[1]" in out and "[2]" in out
    assert "Kartana" in out and "Rampardos" in out
