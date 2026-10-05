"""POST /api/calc/ask over HTTP on the agent runner (keyless; nothing is saved)."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import func, select

from app.agent import runner
from app.api import calc as calc_api
from app.core.config import Settings
from app.main import app
from app.models.team import Team, TeamMember
from tests.test_ask_api import _parse_sse
from tests.test_calc_runner import STATE


@pytest.fixture
def logged(monkeypatch, session_factory):
    monkeypatch.setattr(calc_api, "async_session_factory", session_factory)
    monkeypatch.setattr(
        calc_api, "run_question",
        lambda q, scope, ctx: runner.run_question(q, scope, session_factory=session_factory,
                                                  ctx=ctx),
    )
    monkeypatch.setattr(runner, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key=""))
    seen: list = []

    async def log(question, planner):
        seen.append(("log", question, planner))

    monkeypatch.setattr(calc_api, "_log", log)
    return seen


async def _ask(q: str, **extra) -> list[tuple[str, dict]]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/calc/ask", json={**STATE, "question": q, **extra})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    return _parse_sse(r.text)


async def _team_rows(factory) -> tuple[int, int]:
    async with factory() as s:
        return (await s.scalar(select(func.count()).select_from(Team)),
                await s.scalar(select(func.count()).select_from(TeamMember)))


async def test_ohko_stream(logged, session_factory) -> None:
    before = await _team_rows(session_factory)
    events = await _ask("Can Garchomp OHKO Heatran?")
    names = [n for n, _ in events]
    assert names[0] == "plan" and names[-1] == "done"
    assert names.index("view") < names.index("delta")
    plan = dict(events)["plan"]
    assert [s["tool"] for s in plan["steps"]] == ["calc_context", "damage_calc"]
    view = dict(events)["view"]
    assert view["kind"] == "damage" and view["current"]["ko"] == 1
    assert dict(events)["done"]["usage"]["llm_calls"] == 0
    assert logged == [("log", "Can Garchomp OHKO Heatran?", "keyword")]
    assert await _team_rows(session_factory) == before


async def test_survive_stream(logged) -> None:
    events = await _ask("How much Def does Heatran need to survive Dragon Claw?", focus=2)
    view = next(d for n, d in events if n == "view")
    assert view["kind"] == "survive" and view["defender"]["name"] == "Heatran"


async def test_bad_request_is_422(logged) -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/calc/ask", json={"question": "hi", "slots": [{"slot": 9,
                                                                             "pokemon_id": 1}]})
    assert r.status_code == 422
