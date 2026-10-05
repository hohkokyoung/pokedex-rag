"""The calc coach end to end on the runner, LLM stubbed (needs the Compose DB)."""

from __future__ import annotations

import json

from app.agent import llm_planner, runner
from app.agent.tools import AgentContext
from app.core.config import Settings
from app.rag import answer as answer_service
from app.rag import build_suggest
from app.schemas.calc import CalcAskRequest
from app.services.calc_state import resolve_state

STATE = {
    "question": "q",
    "focus": 0,
    "slots": [
        {"slot": 0, "pokemon_id": 445, "nature": "Jolly", "evs": {"atk": 252, "spe": 252},
         "item": "Life Orb", "move": "Earthquake", "aim": 2},
        {"slot": 2, "pokemon_id": 485, "evs": {"hp": 252}, "move": "Flamethrower", "aim": 0},
    ],
    "hits": [{"attacker": 0, "target": 2, "move": "Earthquake", "min_pct": 200, "max_pct": 236,
              "ko": 1, "te": 4}],
}
BUILD = {"moves": ["Earthquake", "Dragon Claw", "Swords Dance", "Fire Fang"],
         "ability": "Rough Skin", "nature": "Impish", "item": "Leftovers",
         "evs": {"hp": 252, "atk": 4, "def": 252, "spa": 0, "spd": 0, "spe": 0},
         "why": "Impish Leftovers soaks physical hits."}


async def _ctx(factory, **kw):
    async with factory() as s:
        st = await resolve_state(s, CalcAskRequest(**{**STATE, **kw}))
    return AgentContext(scope="calc", extra={"calc": st})


def _settings(monkeypatch, key="g"):
    s = Settings(anthropic_api_key="", groq_api_key=key)
    monkeypatch.setattr(runner, "get_settings", lambda: s)
    monkeypatch.setattr(build_suggest, "get_settings", lambda: s)


class LLM:
    def __init__(self, monkeypatch, plans=()):
        self.plans = list(plans)
        self.plan_calls = self.build_calls = self.answer_calls = 0
        self.last_plan_prompt = None

        async def quick_complete(system, user, *, usage=None, **kw):
            if "competitive Pokémon coach" in system:
                self.build_calls += 1
                payload = BUILD
            else:
                self.plan_calls += 1
                self.last_plan_prompt = (system, user, kw.get("json_schema"))
                payload = self.plans.pop(0)
            if usage is not None:
                usage.add(1000, 100)
            return json.dumps(payload)

        async def stream_answer(question, chunks, note=None, *, usage=None):
            self.answer_calls += 1
            if usage is not None:
                usage.add(3000, 200)
            yield "Coach answer [1]."

        monkeypatch.setattr(answer_service, "quick_complete", quick_complete)
        monkeypatch.setattr(answer_service, "stream_answer", stream_answer)


async def _run(q, factory, ctx):
    events = [e async for e in runner.run_question(q, "calc", session_factory=factory, ctx=ctx)]
    return events, "".join(d["text"] for n, d in events if n == "delta")


def _first(events, name):
    return next(d for n, d in events if n == name)


def _plan(*steps):
    return {"needs_followup": False, "steps": [
        {"id": f"s{i}", "tool": t, "why": "w", "after": [], "args": a}
        for i, (t, a) in enumerate(steps, start=1)
    ]}


async def test_ohko_is_code_only(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    events, text = await _run("Can Garchomp OHKO Heatran?", session_factory,
                              await _ctx(session_factory))
    assert [s["tool"] for s in _first(events, "plan")["steps"]] == ["calc_context", "damage_calc"]
    assert text.startswith("Your **Garchomp**'s **Earthquake** does") and "guaranteed OHKO" in text
    assert (llm.plan_calls, llm.build_calls, llm.answer_calls) == (0, 0, 0)
    assert _first(events, "done")["usage"]["llm_calls"] == 0
    assert next(d for n, d in events if n == "view")["kind"] == "damage"


async def test_survive_is_code_only(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    _, text = await _run("How much Def does Heatran need to survive Garchomp's Dragon Claw?",
                         session_factory, await _ctx(session_factory))
    assert "Heatran" in text and ("survives" in text or "can't survive" in text)
    assert (llm.plan_calls, llm.answer_calls) == (0, 0)


async def test_best_build_is_one_call(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    events, text = await _run("Best build", session_factory, await _ctx(session_factory))
    assert text.startswith("Impish Leftovers soaks physical hits.")
    assert next(d for n, d in events if n == "view")["kind"] == "build_proposal"
    assert (llm.plan_calls, llm.build_calls, llm.answer_calls) == (0, 1, 0)


async def test_plain_question_context_first(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    events, _ = await _run("Who wins this?", session_factory, await _ctx(session_factory))
    assert _first(events, "sources")[0]["chunk_type"] == "calc_slot"
    assert (llm.plan_calls, llm.answer_calls) == (0, 1)


async def test_keyless_build_and_damage(monkeypatch, session_factory):
    _settings(monkeypatch, key="")
    LLM(monkeypatch)
    _, text = await _run("Best build", session_factory, await _ctx(session_factory))
    assert "LLM key" in text
    _, text = await _run("Can Garchomp OHKO Heatran?", session_factory,
                         await _ctx(session_factory))
    assert "guaranteed OHKO" in text


async def test_mixed_question_at_most_two_calls(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan(
        ("damage_calc", {"attacker": "Garchomp", "changes": [
            {"who": "attacker", "key": "item", "value": "Choice Band"}]}),
        ("propose_build", {"request": "a bulkier set"}),
    )])
    events, text = await _run("Can Garchomp OHKO Heatran with Choice Band, and a bulkier set?",
                              session_factory, await _ctx(session_factory))
    assert llm.plan_calls + llm.build_calls + llm.answer_calls <= 2
    _, user, schema = llm.last_plan_prompt
    assert "Calculator" in user and "Garchomp [Earthquake]" in user
    tools = {o["properties"]["tool"]["enum"][0]
             for o in schema["properties"]["steps"]["items"]["anyOf"]}
    assert {"damage_calc", "survive_threshold", "propose_build"} <= tools
    assert "calc_context" not in tools
    assert "With Choice Band" in text


async def test_empty_llm_plan_accepted(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan()])

    async def not_confident(session, question, scope="ask", ctx=None):
        from app.agent.keyword_planner import KeywordPlan
        from app.agent.plan import Plan

        return KeywordPlan(Plan(steps=[], planner="keyword"), False)

    monkeypatch.setattr(runner, "plan_keywords", not_confident)
    events, _ = await _run("Thoughts on this matchup?", session_factory,
                           await _ctx(session_factory))
    assert _first(events, "plan")["planner"] == "llm" and llm.answer_calls == 1


def test_calc_prompt_has_calc_rules():
    assert "damage calculator's coach" in llm_planner.system_prompt("calc")
