"""/api/ask and /api/ask/stream over HTTP, on the agent runner."""

from __future__ import annotations

import json

import httpx
import pytest

from app.agent import cache, runner
from app.api import ask as ask_api
from app.core.config import Settings
from app.main import app


@pytest.fixture(autouse=True)
def _wire(monkeypatch, session_factory):
    """Run the endpoints on the per-test engine, keyless unless a test stubs an LLM."""
    cache.plans.clear()
    cache.answers.clear()

    async def no_log(question, planner, trace=None):  # keep test questions out of the history
        logged.append((question, planner))

    logged: list = []
    monkeypatch.setattr(ask_api, "_log", no_log)
    monkeypatch.setattr(
        ask_api, "run_question",
        lambda q, ctx=None: runner.run_question(q, session_factory=session_factory, ctx=ctx),
    )
    monkeypatch.setattr(runner, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key=""))
    yield
    cache.plans.clear()
    cache.answers.clear()


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        name = data = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:])
        events.append((name, data))
    return events


async def test_stream_event_sequence_and_shapes() -> None:
    async with _client() as c:
        r = await c.post("/api/ask/stream", json={"question": "Can Garchomp learn Earthquake?"})
    assert r.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(r.text)
    names = [n for n, _ in events]
    assert "route" not in names
    assert names[0] == "plan" and names[-1] == "done"
    assert names.index("view") < names.index("sources") < names.index("delta")

    plan = events[0][1]
    assert plan["planner"] == "keyword" and plan["steps"][0]["tool"] == "learnset"
    sources = dict(events)["sources"]
    # The old Source shape, plus the step reference.
    assert {"n", "pokemon_name", "chunk_type", "snippet", "score", "step", "step_index"} <= set(
        sources[0])
    delta = dict(events)["delta"]
    assert set(delta) == {"text"} and delta["text"].startswith("Yes")
    assert dict(events)["done"]["usage"]["llm_calls"] == 0


async def test_non_streaming_keyless() -> None:
    async with _client() as c:
        r = await c.post("/api/ask", json={"question": "Describe Snorlax"})
    body = r.json()
    assert "route" not in body
    assert body["planner"] == "keyword"
    assert body["steps"][0]["tool"] == "get_pokemon" and body["steps"][0]["state"] == "done"
    assert body["views"][0]["kind"] == "pokemon_list"
    assert "straight from the Pokédex" in body["answer"]
    assert body["usage"]["llm_calls"] == 0


async def test_non_streaming_llm_planned(monkeypatch) -> None:
    from app.rag import answer as answer_service

    monkeypatch.setattr(runner, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key="g"))
    plan = {"needs_followup": False, "steps": [
        {"id": "a", "tool": "type_matchup", "why": "w", "after": [], "args": {"types": ["fire"]}},
        {"id": "b", "tool": "move_info", "why": "w", "after": [], "args": {"name": "Ember"}},
    ]}

    async def quick_complete(system, user, *, usage=None, **kw):
        usage.add(2400, 150)
        return json.dumps(plan)

    monkeypatch.setattr(answer_service, "quick_complete", quick_complete)
    async with _client() as c:
        r = await c.post("/api/ask", json={"question": "Fire weaknesses and what Ember does"})
    body = r.json()
    assert body["planner"] == "llm"
    assert [s["state"] for s in body["steps"]] == ["done", "done"]
    assert [v["kind"] for v in body["views"]] == ["type_chart", "move_list"]
    assert [s["step"] for s in body["sources"]] == ["a", "b"]
    assert body["usage"]["llm_calls"] == 1  # closed-form: rendered by code


@pytest.mark.parametrize("path", ["/api/ask/stream", "/api/ask"])
async def test_route_logs_its_trace(monkeypatch, path) -> None:
    got: list = []

    async def log(question, planner, trace=None):
        got.append((question, planner, trace))

    monkeypatch.setattr(ask_api, "_log", log)
    async with _client() as c:
        r = await c.post(path, json={"question": "Can Garchomp learn Earthquake?"})
    assert r.status_code == 200
    [(q, planner, trace)] = got
    assert (q, planner, trace["scope"], trace["planner"]) == (
        "Can Garchomp learn Earthquake?", "keyword", "ask", "keyword")
    assert trace["steps"][0]["tool"] == "learnset"
