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
