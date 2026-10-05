"""Unit tests for coach drafting/add intent parsing (pure, no DB)."""

from __future__ import annotations

from app.rag.coach import is_add_command
from app.services.recommend import allow_legendary, is_draft_request, parse_role


def test_add_command_vs_deliberation() -> None:
    assert is_add_command("add Garchomp to my team") is True
    assert is_add_command("include Ferrothorn") is True
    # A question about whether to add is NOT a command.
    assert is_add_command("should I add Garchomp?") is False
    assert is_add_command("is it worth adding Blissey?") is False
    # A recommendation ask is not an add command.
    assert is_add_command("which type should I add for coverage?") is False


def test_draft_request_detection() -> None:
    assert is_draft_request("help me draft the other best 5") is True
    assert is_draft_request("recommend a fast sweeper") is True
    assert is_draft_request("who should I add?") is True
    assert is_draft_request("what is Pikachu's speed?") is False


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
