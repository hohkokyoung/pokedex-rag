"""Plan traces: what the runner records per question, and how it's stored and read."""

from __future__ import annotations

import contextlib
import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agent import runner, trace_cli
from app.agent import trace as plan_trace
from app.agent.tools import AgentContext
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.main import app
from app.models import QuestionLog
from tests.test_agent_runner import (  # noqa: F401 — _fresh_caches is an autouse fixture
    LLM,
    _fresh_caches,
    _plan,
    _rate_limit,
    _settings,
)


def test_trace_retention_setting(monkeypatch) -> None:
    assert Settings(_env_file=None).trace_retention == 2000
    monkeypatch.setenv("TRACE_RETENTION", "50")
    assert Settings(_env_file=None).trace_retention == 50


# ---- 2.2 / 2.3 the trace each runner path records -----------------------------------------



async def _trace(q, factory):
    ctx = AgentContext(scope="ask")
    events = [e async for e in runner.run_question(q, session_factory=factory, ctx=ctx)]
    return ctx.extra["trace"], events


async def test_fast_path(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch)
    t, _ = await _trace("Can Garchomp learn Earthquake?", session_factory)
    assert (t["v"], t["scope"], t["planner"], t["skip_llm"], t["fallback"]) == (
        1, "ask", "keyword", "fast-path", None)
    assert t["keyword"]["confident"] and [s["tool"] for s in t["keyword"]["steps"]] == ["learnset"]
    assert t["llm"] is None and t["answer"]["tier"] == "code"
    assert t["usage"]["llm_calls"] == 0 and t["steps"][0]["state"] == "done"


async def test_llm_plan(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch, plans=[_plan(("learnset", {"move": "Will-O-Wisp", "types": ["fire"]}),
                                  ("type_matchup", {"types": ["fire"]}))])
    t, _ = await _trace("Which Fire types learn Will-O-Wisp, and what is Fire weak to?",
                        session_factory)
    assert t["planner"] == "llm" and t["skip_llm"] is None and not t["keyword"]["confident"]
    assert [(s["tool"], s["why"]) for s in t["llm"]["steps"]] == [
        ("learnset", "w"), ("type_matchup", "w")]
    assert t["llm"]["steps"][0]["args"]["move"] == "Will-O-Wisp"
    assert {s["tool"] for s in t["steps"]} == {"learnset", "type_matchup"}
    assert all(s["state"] == "done" for s in t["steps"]) and t["usage"]["llm_calls"] >= 1


async def test_planner_429(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch, plans=[_rate_limit()])
    t, _ = await _trace("Which Fire types learn Will-O-Wisp, and what is Fire weak to?",
                        session_factory)
    assert (t["planner"], t["fallback"]) == ("keyword", "rate-limited")
    assert t["llm"] is None and t["keyword"]["steps"]


async def test_no_valid_steps(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch, plans=[_plan(("no_such_tool", {}))])
    t, _ = await _trace("Which Fire types learn Will-O-Wisp, and what is Fire weak to?",
                        session_factory)
    assert (t["planner"], t["fallback"]) == ("keyword", "no-valid-steps")
    assert t["llm"]["steps"][0]["tool"] == "no_such_tool" and "error" in t["llm"]["steps"][0]


async def test_no_key(monkeypatch, session_factory):
    _settings(monkeypatch, groq_api_key="")
    LLM(monkeypatch)
    t, _ = await _trace("Tell me about Snorlax", session_factory)
    assert (t["planner"], t["skip_llm"], t["fallback"]) == ("keyword", "no-llm", None)
    assert t["answer"]["tier"] == "no-llm" and t["usage"]["llm_calls"] == 0


async def test_unhandled_abstain(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch, plans=[{"needs_followup": False, "steps": [],
                             "unhandled": ["evolution method (trade)"]}])
    t, _ = await _trace("Which Pokémon that evolve by trading have the highest Attack?",
                        session_factory)
    assert t["answer"]["tier"] == "abstain"
    assert t["llm"]["unhandled"] == ["evolution method (trade)"]


async def test_answer_429(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch, answer="Partial", answer_exc=_rate_limit())
    t, _ = await _trace("Tell me about Snorlax", session_factory)
    assert t["answer"] == {"tier": "no-llm", "fallback": "rate-limited"}


async def test_cached(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch)
    await _trace("Can Garchomp learn Earthquake?", session_factory)
    t, _ = await _trace("Can Garchomp learn Earthquake?", session_factory)
    assert t["planner"] == "cached" and t["usage"]["llm_calls"] == 0


async def test_six_step_trace_is_small(monkeypatch, session_factory):
    _settings(monkeypatch)
    long = "x" * 2000
    LLM(monkeypatch, plans=[_plan(*[("semantic_search", {"query": f"{long}{i}"})
                                    for i in range(6)])])
    t, _ = await _trace("Six lore questions at once, please", session_factory)
    assert len(json.dumps(t)) < 8000


async def test_events_unchanged_by_tracing(monkeypatch, session_factory):
    """Tracing is invisible to the client: same events whether or not the trace builds."""
    _settings(monkeypatch)
    LLM(monkeypatch)

    def strip(events):
        return [(n, {k: v for k, v in d.items() if k != "ms"} if isinstance(d, dict) else d)
                for n, d in events]

    _, normal = await _trace("Can Garchomp learn Earthquake?", session_factory)
    runner.cache.answers.clear()
    runner.cache.plans.clear()

    def broken(*a, **k):
        raise RuntimeError("trace bug")

    monkeypatch.setattr(plan_trace, "build", broken)
    ctx = AgentContext(scope="ask")
    events = [e async for e in runner.run_question("Can Garchomp learn Earthquake?",
                                                   session_factory=session_factory, ctx=ctx)]
    assert strip(events) == strip(normal) and "trace" not in ctx.extra


# ---- 3.1 storing (inside one rolled-back transaction: the prune is global) -----------------



@contextlib.asynccontextmanager
async def _rolled_back():
    """A session factory whose commits are savepoints in one transaction rolled back after."""
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            try:
                yield async_sessionmaker(bind=conn, expire_on_commit=False,
                                         join_transaction_mode="create_savepoint")
            finally:
                await tx.rollback()
    finally:
        await engine.dispose()


async def test_record_writes_the_trace_and_prunes(session) -> None:
    async with _rolled_back() as factory:
        for i in range(4):
            await plan_trace.record(f"__trace_test_{i}__", "agent-keyword", {"v": 1, "n": i},
                                    session_factory=factory, retention=3)
        async with factory() as s:
            rows = (await s.execute(
                select(QuestionLog.question, QuestionLog.trace)
                .where(QuestionLog.question.like("__trace_test_%")).order_by(QuestionLog.id)
            )).all()
    assert [q for q, _ in rows] == [f"__trace_test_{i}__" for i in range(4)]  # questions stay
    assert rows[0].trace is None and [t["n"] for _, t in rows[1:]] == [1, 2, 3]


async def test_record_never_raises(caplog) -> None:
    def broken():
        raise RuntimeError("db down")

    with caplog.at_level(logging.WARNING, logger="app.agent.trace"):
        await plan_trace.record("q", "agent-keyword", {"v": 1}, session_factory=broken)
    assert "couldn't log the question" in caplog.text


# ---- 4.1 the read API (seeded inside a rolled-back transaction) ----------------------------


_SEED = [  # question, route, trace
    ("__tr_a__", "agent-keyword", {"v": 1, "scope": "ask", "planner": "keyword", "fallback": None,
                                   "steps": [{"tool": "learnset"}], "answer": {"tier": "code"},
                                   "usage": {"llm_calls": 0}}),
    ("__tr_b__", "coach-llm", {"v": 1, "scope": "team", "planner": "llm", "fallback": None,
                               "steps": [{"tool": "team_context"}, {"tool": "duel"}],
                               "answer": {"tier": "llm"}, "usage": {"llm_calls": 2}}),
    ("__tr_c__", "agent-keyword", {"v": 1, "scope": "ask", "planner": "keyword",
                                   "fallback": "rate-limited", "steps": [],
                                   "answer": {"tier": "no-llm", "fallback": None},
                                   "usage": {"llm_calls": 1}}),
    ("__tr_d__", "agent-keyword", None),  # untraced
]


@contextlib.asynccontextmanager
async def _seeded():
    async with _rolled_back() as factory:
        ids = {}
        async with factory() as s:
            for q, route, tr in _SEED:
                row = QuestionLog(question=q, route=route, trace=tr)
                s.add(row)
                await s.flush()
                ids[q] = row.id
            await s.commit()

        async def override():
            async with factory() as s:
                yield s

        app.dependency_overrides[get_session] = override
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="http://t") as c:
                yield c, ids
        finally:
            app.dependency_overrides.pop(get_session, None)


def _ours(rows):
    return [r["question"] for r in rows if r["question"].startswith("__tr_")]


async def test_list_filters_and_order(session) -> None:
    async with _seeded() as (c, ids):
        rows = (await c.get("/api/traces", params={"limit": 200})).json()
        assert _ours(rows) == ["__tr_c__", "__tr_b__", "__tr_a__"]  # newest first, untraced out
        b = next(r for r in rows if r["question"] == "__tr_b__")
        assert (b["scope"], b["planner"], b["llm_calls"], b["tools"]) == (
            "team", "llm", 2, ["team_context", "duel"])
        assert _ours((await c.get("/api/traces", params={"scope": "team", "limit": 200})).json()) \
            == ["__tr_b__"]
        assert _ours((await c.get("/api/traces", params={"planner": "keyword",
                                                         "limit": 200})).json()) \
            == ["__tr_c__", "__tr_a__"]
        fell = (await c.get("/api/traces", params={"fallback": "true", "limit": 200})).json()
        assert _ours(fell) == ["__tr_c__"] and fell[0]["fallback"] == "rate-limited"
        assert (await c.get("/api/traces", params={"limit": 500})).status_code == 422


async def test_get_one_and_404(session) -> None:
    async with _seeded() as (c, ids):
        one = (await c.get(f"/api/traces/{ids['__tr_b__']}")).json()
        assert one["trace"]["planner"] == "llm" and one["route"] == "coach-llm"
        assert (await c.get(f"/api/traces/{ids['__tr_d__']}")).status_code == 404  # no trace
        assert (await c.get("/api/traces/999999999")).status_code == 404


# ---- 4.2 the CLI -----------------------------------------------------------------------------



async def test_cli_list_filter_and_one(session, capsys) -> None:
    async with _rolled_back() as factory:
        ids = {}
        async with factory() as s:
            for q, route, tr in _SEED:
                row = QuestionLog(question=q, route=route, trace=tr)
                s.add(row)
                await s.flush()
                ids[q] = row.id
            await s.commit()

        assert await trace_cli.run(trace_cli.parse(["--limit", "200"]), factory) == 0
        lines = [ln for ln in capsys.readouterr().out.splitlines() if "__tr_" in ln]
        assert [ln.rsplit("— ", 1)[1] for ln in lines] == ["__tr_c__", "__tr_b__", "__tr_a__"]
        assert "team  llm" in lines[1] and "2 calls  team_context,duel" in lines[1]

        await trace_cli.run(trace_cli.parse(["--fallback", "--limit", "200"]), factory)
        out = [ln for ln in capsys.readouterr().out.splitlines() if "__tr_" in ln]
        assert len(out) == 1 and "!rate-limited" in out[0]

        assert await trace_cli.run(trace_cli.parse(["--id", str(ids["__tr_b__"])]), factory) == 0
        assert '"planner": "llm"' in capsys.readouterr().out
        assert await trace_cli.run(trace_cli.parse(["--id", str(ids["__tr_d__"])]), factory) == 1
        assert "No trace for id" in capsys.readouterr().out
