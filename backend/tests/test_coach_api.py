"""POST /api/teams/{id}/ask over HTTP on the agent runner (keyless, temporary teams)."""

from __future__ import annotations

import httpx
import pytest_asyncio

from app.agent import runner
from app.api import teams as teams_api
from app.core.config import Settings
from app.main import app
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import teams as teams_service
from tests.test_ask_api import _parse_sse


@pytest_asyncio.fixture
async def team_id(monkeypatch, session_factory):
    async with session_factory() as s:
        t = await teams_service.create_team(s, TeamCreate(name="__api_coach__", kind="player"))
        for i, pid in enumerate([445, 6], start=1):
            await teams_service.set_slot(s, t.id, i, SlotUpdate(pokemon_id=pid))
    monkeypatch.setattr(teams_api, "async_session_factory", session_factory)
    monkeypatch.setattr(
        teams_api, "run_question",
        lambda q, scope, ctx: runner.run_question(q, scope, session_factory=session_factory,
                                                  ctx=ctx),
    )
    monkeypatch.setattr(runner, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key=""))
    logged: list = []

    async def no_log(question, planner):
        logged.append((question, planner))

    monkeypatch.setattr(teams_api, "_log", no_log)
    yield t.id
    async with session_factory() as s:
        await teams_service.delete_team(s, t.id)


async def _ask(team_id: int, q: str, **extra) -> list[tuple[str, dict]]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post(f"/api/teams/{team_id}/ask", json={"question": q, **extra})
    assert r.headers["content-type"].startswith("text/event-stream")
    return _parse_sse(r.text)


async def test_add_streams_team_updated(team_id) -> None:
    events = await _ask(team_id, "add Dragonite")
    names = [n for n, _ in events]
    assert names[0] == "plan" and names[-1] == "done"
    assert "candidates" not in names and "edits" not in names
    assert names.index("view") < names.index("team_updated") < names.index("delta")
    updated = dict(events)["team_updated"]
    assert [m["name"] for m in updated["members"]] == ["Garchomp", "Charizard", "Dragonite"]


async def test_plain_question_keyless_uses_report(team_id) -> None:
    events = await _ask(team_id, "What's my team's biggest weakness?", report="Grade C.")
    plan = dict(events)["plan"]
    assert [s["tool"] for s in plan["steps"]] == ["team_context"]
    assert "".join(d["text"] for n, d in events if n == "delta") == "Grade C."


async def test_unknown_team(team_id) -> None:
    events = await _ask(999_999, "hi")
    assert events == [("error", {"message": "Team not found"})]


async def test_question_is_logged_before_done(team_id, monkeypatch) -> None:
    """The client stops reading at `done`; logging must already have happened by then."""
    order: list[str] = []

    async def log(question, planner):
        order.append("log")

    monkeypatch.setattr(teams_api, "_log", log)
    original = teams_api._sse

    def sse(name, data):
        order.append(name)
        return original(name, data)

    monkeypatch.setattr(teams_api, "_sse", sse)
    await _ask(team_id, "Can Garchomp learn Swords Dance?")
    assert order.index("log") < order.index("done")
