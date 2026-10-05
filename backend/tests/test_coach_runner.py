"""The team coach end to end on the runner: temporary teams, LLM stubbed."""

from __future__ import annotations

import json

import pytest
import pytest_asyncio

from app.agent import cache, runner
from app.agent.tools import AgentContext
from app.core.config import Settings
from app.rag import answer as answer_service
from app.rag import build_suggest
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import team_analysis
from app.services import teams as teams_service


@pytest_asyncio.fixture
async def teams(session_factory):
    made: list[int] = []
    async with session_factory() as s:
        async def make(name, kind, ids):
            t = await teams_service.create_team(s, TeamCreate(name=name, kind=kind))
            made.append(t.id)
            for i, pid in enumerate(ids, start=1):
                await teams_service.set_slot(s, t.id, i, SlotUpdate(pokemon_id=pid))
            return t.id

        player = await make("__coach_player__", "player", [445, 6, 130])
        opponent = await make("__coach_opp__", "opponent", [9, 373])
    yield player, opponent
    async with session_factory() as s:
        for tid in made:
            await teams_service.delete_team(s, tid)


async def _ctx(factory, player, opponent=None, report=None):
    async with factory() as s:
        team = await teams_service.get_team(s, player)
        opp = await teams_service.get_team(s, opponent) if opponent else None
        analysis = await team_analysis.analyze(s, team, opp)
    return AgentContext(scope="team", team=team, opponent=opp, report=report,
                        extra={"analysis": analysis})


def _settings(monkeypatch, key="g"):
    s = Settings(anthropic_api_key="", groq_api_key=key)
    monkeypatch.setattr(runner, "get_settings", lambda: s)
    monkeypatch.setattr(build_suggest, "get_settings", lambda: s)


class LLM:
    """Stubs planning + build-coach calls (quick_complete) and the answer stream."""

    def __init__(self, monkeypatch, plans=(), build=None):
        self.plans, self.build = list(plans), build
        self.plan_calls = self.build_calls = self.answer_calls = 0

        async def quick_complete(system, user, *, usage=None, **kw):
            if "competitive Pokémon coach" in system:  # build_suggest
                self.build_calls += 1
                payload = self.build
            else:
                self.plan_calls += 1
                payload = self.plans.pop(0)
            if usage is not None:
                usage.add(1000, 100)
            return json.dumps(payload)

        async def stream_answer(question, chunks, note=None, *, usage=None):
            self.answer_calls += 1
            self.chunks = chunks
            if usage is not None:
                usage.add(3000, 200)
            yield "Coach answer [1]."

        monkeypatch.setattr(answer_service, "quick_complete", quick_complete)
        monkeypatch.setattr(answer_service, "stream_answer", stream_answer)


async def _run(q, factory, ctx):
    events = [e async for e in runner.run_question(q, "team", session_factory=factory, ctx=ctx)]
    text = "".join(d["text"] for n, d in events if n == "delta")
    return events, text


def _first(events, name):
    return next(d for n, d in events if n == name)


def _plan(*steps):
    return {"needs_followup": False, "steps": [
        {"id": f"s{i}", "tool": t, "why": "w", "after": [], "args": a}
        for i, (t, a) in enumerate(steps, start=1)
    ]}


SET = {"moves": ["Earthquake", "Dragon Claw", "Swords Dance", "Fire Fang"],
       "ability": "Rough Skin", "nature": "Jolly", "item": "Choice Scarf",
       "evs": {"hp": 4, "atk": 252, "def": 0, "spa": 0, "spd": 0, "spe": 252},
       "why": "Scarf Jolly outspeeds more threats."}


async def test_plain_question_one_call_report_first(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    ctx = await _ctx(session_factory, teams[0], report="Grade B — weak to Ice.")
    events, text = await _run("What's my team's biggest weakness?", session_factory, ctx)
    plan = _first(events, "plan")
    assert [s["tool"] for s in plan["steps"]] == ["team_context"] and plan["planner"] == "keyword"
    assert (llm.plan_calls, llm.answer_calls) == (0, 1)
    assert _first(events, "sources")[0]["chunk_type"] == "team_report"  # report is [1]
    assert _first(events, "done")["usage"]["llm_calls"] == 1


async def test_explicit_add_writes_and_reports(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    ctx = await _ctx(session_factory, teams[0])
    events, text = await _run("add Dragonite", session_factory, ctx)
    names = [n for n, _ in events]
    assert "team_updated" in names and names.index("team_updated") > names.index("view")
    assert text.startswith("Added **Dragonite** to slot 4")
    assert (llm.plan_calls, llm.answer_calls) == (0, 0)
    async with session_factory() as s:
        assert len((await teams_service.get_team(s, teams[0])).members) == 4


async def test_wrongly_planned_add_never_writes(monkeypatch, session_factory, teams):
    """Even if the LLM plans an add for a deliberation, the gate turns it into a card."""
    _settings(monkeypatch)
    LLM(monkeypatch, plans=[_plan(("add_member", {"pokemon": "Dragonite"}))])
    ctx = await _ctx(session_factory, teams[0])
    monkeypatch.setattr(runner, "plan_keywords", _not_confident)
    events, _ = await _run("Is Dragonite a good fit for my team?", session_factory, ctx)
    view = next(d for n, d in events if n == "view")
    assert view["kind"] == "candidates" and view["candidates"][0]["name"] == "Dragonite"
    assert "team_updated" not in [n for n, _ in events]
    async with session_factory() as s:
        assert len((await teams_service.get_team(s, teams[0])).members) == 3


async def _not_confident(session, question, scope="ask", ctx=None):
    from app.agent.keyword_planner import KeywordPlan
    from app.agent.plan import Plan

    return KeywordPlan(Plan(steps=[], planner="keyword"), False)


async def test_should_i_add_shows_card(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    LLM(monkeypatch)
    ctx = await _ctx(session_factory, teams[0])
    events, _ = await _run("Should I add Dragonite?", session_factory, ctx)
    kinds = [d["kind"] for n, d in events if n == "view"]
    assert kinds == ["candidates"]
    async with session_factory() as s:
        assert len((await teams_service.get_team(s, teams[0])).members) == 3


async def test_set_change_alone_is_one_call(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, build=SET)
    ctx = await _ctx(session_factory, teams[0], teams[1])
    events, text = await _run("Give Garchomp a faster set", session_factory, ctx)
    view = next(d for n, d in events if n == "view")
    assert view["kind"] == "set_edit" and view["fields"]["nature"] == "Jolly"
    assert text.startswith("Scarf Jolly outspeeds more threats.")
    assert "press Apply" in text
    assert (llm.plan_calls, llm.build_calls, llm.answer_calls) == (0, 1, 0)
    assert _first(events, "done")["usage"]["llm_calls"] == 1


async def test_draft_is_at_most_two_calls(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan(("recommend_additions",
                                         {"role": "sweeper", "legendary": False}))])
    ctx = await _ctx(session_factory, teams[0])
    events, _ = await _run("Draft the rest of my team, fuck legendaries, I like sweepers",
                           session_factory, ctx)
    assert [d["kind"] for n, d in events if n == "view"] == ["candidates"]
    assert llm.plan_calls + llm.answer_calls <= 2
    assert _first(events, "done")["usage"]["llm_calls"] <= 2


async def test_empty_llm_plan_is_accepted_for_team(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan()])
    monkeypatch.setattr(runner, "plan_keywords", _not_confident)
    ctx = await _ctx(session_factory, teams[0])
    events, _ = await _run("How does my team look?", session_factory, ctx)
    plan = _first(events, "plan")
    assert plan["planner"] == "llm" and [s["tool"] for s in plan["steps"]] == ["team_context"]
    assert llm.answer_calls == 1


async def test_keyless_with_report_and_set_change(monkeypatch, session_factory, teams):
    _settings(monkeypatch, key="")
    LLM(monkeypatch)
    ctx = await _ctx(session_factory, teams[0], report="Grade B — weak to Ice.")
    _, text = await _run("What's my team's biggest weakness?", session_factory, ctx)
    assert text == "Grade B — weak to Ice."
    ctx = await _ctx(session_factory, teams[0])
    _, text = await _run("Give Garchomp a faster set", session_factory, ctx)
    assert "LLM key" in text


async def test_team_answers_are_never_cached(monkeypatch, session_factory, teams):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    cache.answers.clear()
    for _ in range(2):
        ctx = await _ctx(session_factory, teams[0])
        await _run("What's my team's biggest weakness?", session_factory, ctx)
    assert llm.answer_calls == 2


def test_ask_still_rejects_empty_plans():
    """Ask keeps falling back when the LLM returns no steps (see test_agent_runner)."""
    import inspect

    src = inspect.getsource(runner._choose_plan)
    assert 'empty_ok = scope == "team"' in src


@pytest.mark.parametrize("q", ["add Dragonite", "Should I add Dragonite?"])
def test_gate_is_deterministic(q):
    from app.agent.keyword_planner import is_imperative_add

    assert is_imperative_add(q) is (q == "add Dragonite")
