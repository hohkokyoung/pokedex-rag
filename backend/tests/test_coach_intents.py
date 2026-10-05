"""Coach phrasing rules that stay deterministic: the add gate, role and legendary parsing."""

from __future__ import annotations

from app.agent.keyword_planner import is_imperative_add
from app.services.recommend import allow_legendary, parse_role


def test_add_command_vs_deliberation() -> None:
    assert is_imperative_add("add Garchomp to my team") is True
    assert is_imperative_add("include Ferrothorn") is True
    assert is_imperative_add("should I add Garchomp?") is False
    assert is_imperative_add("is it worth adding Blissey?") is False
    assert is_imperative_add("which type should I add for coverage?") is False


def test_parse_role() -> None:
    assert parse_role("I like a sweeper build") == "sweeper"
    assert parse_role("recommend a bulky wall") == "wall"
    assert parse_role("need a hard-hitting wallbreaker") == "wallbreaker"
    assert parse_role("just give me good options") is None


def test_allow_legendary_negation() -> None:
    assert allow_legendary("non legendary please") is False
    assert allow_legendary("non-legendary only") is False
    assert allow_legendary("no legendaries") is False
    assert allow_legendary("without legendaries") is False
    assert allow_legendary("legendaries are fine") is True
    assert allow_legendary("recommend a sweeper") is False  # no mention → excluded
