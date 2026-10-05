"""Tool registry and planner signatures."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.agent import tools as agent_tools
from app.agent.results import ToolResult


class _Args(BaseModel):
    name: str
    stat: Literal["hp", "speed"] = "hp"
    types: list[str] = []
    limit: int | None = None


async def _handler(session, args, ctx):
    return ToolResult(summary=f"hi {args.name}")


def test_register_and_scope(monkeypatch):
    monkeypatch.setattr(agent_tools, "REGISTRY", {})
    agent_tools.register(agent_tools.Tool(
        "dummy", frozenset({"ask"}), "a dummy tool", _Args, _handler))
    agent_tools.register(agent_tools.Tool(
        "team_only", frozenset({"team"}), "team tool", _Args, _handler))
    assert [t.name for t in agent_tools.tools_for("ask")] == ["dummy"]
    assert [t.name for t in agent_tools.tools_for("team")] == ["team_only"]


def test_signature_is_compact_and_stable():
    t = agent_tools.Tool("dummy", frozenset({"ask"}), "d", _Args, _handler)
    assert agent_tools.signature(t) == (
        "dummy(name: str, stat?: hp|speed, types?: [str], limit?: int)"
    )


def test_ask_tools_serve_the_team_scope_but_not_the_reverse():
    from app.agent import ask_tools  # noqa: F401 — registers the real tools

    ask = {t.name for t in agent_tools.tools_for("ask")}
    team = {t.name for t in agent_tools.tools_for("team")}
    # Lore search, look-alikes, profile picks and encounters stay Ask-only (not coaching).
    ask_only = {"semantic_search", "similar_to", "user_profile", "encounters"}
    assert ask_only <= ask and not ask_only & team
    assert ask - ask_only <= team


def test_plannable_filter(monkeypatch):
    monkeypatch.setattr(agent_tools, "REGISTRY", {})
    agent_tools.register(agent_tools.Tool("a", frozenset({"team"}), "a", _Args, _handler))
    agent_tools.register(agent_tools.Tool(
        "ctx", frozenset({"team"}), "c", _Args, _handler, plannable=False))
    assert [t.name for t in agent_tools.tools_for("team")] == ["a", "ctx"]
    assert [t.name for t in agent_tools.tools_for("team", plannable_only=True)] == ["a"]
