"""The runner end to end against the real data, with the LLM stubbed.

Covers planner selection (fast path, LLM, fallbacks), answer tiers, event order,
citation numbering, LLM call counts, and the answer cache.
"""

from __future__ import annotations

import asyncio
import json

import groq
import httpx
import pytest

from app.agent import cache, runner
from app.core.config import Settings
from app.rag import answer as answer_service


@pytest.fixture(autouse=True)
def _fresh_caches():
    cache.plans.clear()
    cache.answers.clear()
    yield
    cache.plans.clear()
    cache.answers.clear()


def _settings(monkeypatch, **kw):
    s = Settings(**{"anthropic_api_key": "", "groq_api_key": "g", **kw})
    monkeypatch.setattr(runner, "get_settings", lambda: s)
    return s


def _rate_limit() -> groq.RateLimitError:
    resp = httpx.Response(429, request=httpx.Request("POST", "https://x"))
    return groq.RateLimitError("slow down", response=resp, body=None)


class LLM:
    """Stub for the planner call (quick_complete) and the answer stream."""

    def __init__(self, monkeypatch, plans=(), answer="Grounded answer [1].", answer_exc=None):
        self.plans = list(plans)
        self.plan_calls = 0
        self.answer_calls = 0
        self.answer_exc = answer_exc
        self.answer = answer

        async def quick_complete(system, user, *, usage=None, **kw):
            self.plan_calls += 1
            p = self.plans.pop(0)
            if isinstance(p, BaseException):
                raise p
            if callable(p):
                return await p()
            if usage is not None:
                usage.add(2400, 150)
            return json.dumps(p)

        async def stream_answer(question, chunks, note=None, *, usage=None):
            self.answer_calls += 1
            yield self.answer
            if self.answer_exc is not None:
                raise self.answer_exc
            if usage is not None:
                usage.add(3000, 200)

        monkeypatch.setattr(answer_service, "quick_complete", quick_complete)
        monkeypatch.setattr(answer_service, "stream_answer", stream_answer)


def _plan(*steps, followup=False):
    return {"needs_followup": followup, "steps": [
        {"id": f"s{i}", "tool": t, "why": "w", "after": [], "args": a}
        for i, (t, a) in enumerate(steps, start=1)
    ]}


async def _run(q, factory):
    events = [e async for e in runner.run_question(q, session_factory=factory)]
    text = "".join(d["text"] for n, d in events if n == "delta")
    return events, text


def _first(events, name):
    return next(d for n, d in events if n == name)


# ---- 5.4 planner selection, tiers, order, numbering, call counts -------------------------


async def test_fast_path_closed_form_uses_no_llm(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    events, text = await _run("Can Garchomp learn Earthquake?", session_factory)
    assert _first(events, "plan")["planner"] == "keyword"
    assert text.startswith("Yes — **Garchomp** can learn **Earthquake**")
    assert _first(events, "done")["usage"]["llm_calls"] == 0
    assert llm.plan_calls == llm.answer_calls == 0


async def test_fast_path_descriptive_uses_one_call(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    events, text = await _run("Tell me about Snorlax", session_factory)
    assert _first(events, "plan")["planner"] == "keyword"
    assert text == "Grounded answer [1]."
    assert (llm.plan_calls, llm.answer_calls) == (0, 1)
    assert _first(events, "done")["usage"]["llm_calls"] == 1


async def test_llm_closed_form_uses_one_call(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan(("query_pokemon", {"sort_by": "base_stat_total",
                                                             "limit": 5}))])
    events, text = await _run("Top 5 Pokémon by base stat total", session_factory)
    assert _first(events, "plan")["planner"] == "llm"
    assert text.startswith("**Arceus** has the highest base stat total")
    assert (llm.plan_calls, llm.answer_calls) == (1, 0)
    assert _first(events, "done")["usage"] == {
        "llm_calls": 1, "input_tokens": 2400, "output_tokens": 150}


async def test_multi_part_order_numbering_and_two_calls(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan(
        ("type_matchup", {"types": ["fire"]}),
        ("semantic_search", {"query": "volcano", "k": 3}),
    )])
    events, _ = await _run("What is Fire weak to, and which Pokémon live in volcanoes?",
                           session_factory)
    names = [n for n, _ in events]
    assert "route" not in names
    assert names[0] == "plan" and names[-1] == "done"
    assert names.index("sources") > max(i for i, n in enumerate(names) if n in ("step", "view"))
    assert names.index("delta") > names.index("sources")

    sources = _first(events, "sources")
    assert [s["n"] for s in sources] == list(range(1, len(sources) + 1))
    assert sources[0]["step"] == "s1" and sources[0]["step_index"] == 0
    assert sources[1]["step"] == "s2" and sources[1]["step_index"] == 0  # 2nd step follows
    view = _first(events, "view")
    assert view["kind"] == "type_chart" and view["step"] == "s1"
    assert (llm.plan_calls, llm.answer_calls) == (1, 1)
    assert _first(events, "done")["usage"]["llm_calls"] == 2


# ---- re-plan --------------------------------------------------------------------------------


async def test_unresolved_name_replans_once(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[
        _plan(("get_pokemon", {"name": "Zorbulax"})),
        _plan(("get_pokemon", {"name": "Zubat"})),
    ])
    events, _ = await _run("Tell me about Zorbulax and its moves", session_factory)
    plans = [d for n, d in events if n == "plan"]
    assert len(plans) == 2 and plans[1]["replan"] is True
    assert llm.plan_calls == 2


async def test_empty_query_is_an_answer_not_a_replan(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan(("query_pokemon", {
        "types_all": ["fire"], "stat_filters": [{"stat": "speed", "op": "gt", "value": 250}]}))])
    events, text = await _run("Fire types with Speed above 250?", session_factory)
    assert llm.plan_calls == 1 and llm.answer_calls == 0
    assert text.startswith("No Fire-type Pokémon have Speed above 250")


# ---- 5.5 fallbacks ------------------------------------------------------------------------


async def test_no_key_keyword_plan_and_extractive(monkeypatch, session_factory):
    _settings(monkeypatch, groq_api_key="")
    llm = LLM(monkeypatch)
    events, text = await _run("Describe Snorlax", session_factory)
    assert _first(events, "plan")["planner"] == "keyword"
    assert "straight from the Pokédex" in text and "Snorlax" in text
    assert llm.plan_calls == llm.answer_calls == 0


async def test_flag_off_skips_llm_planning(monkeypatch, session_factory):
    _settings(monkeypatch, ask_agent_enabled=False)
    llm = LLM(monkeypatch)
    events, _ = await _run("Which Fire-type Pokémon live near volcanoes?", session_factory)
    assert _first(events, "plan")["planner"] == "keyword"
    assert llm.plan_calls == 0 and llm.answer_calls == 1


@pytest.mark.parametrize("failure", ["429", "invalid", "timeout"])
async def test_planner_failure_falls_back_without_retry(monkeypatch, session_factory, failure):
    _settings(monkeypatch)
    if failure == "429":
        plan = _rate_limit()
    elif failure == "invalid":
        plan = _plan(("no_such_tool", {}))
    else:
        monkeypatch.setattr(runner, "PLAN_TIMEOUT", 0.05)

        async def slow():
            await asyncio.sleep(1)
        plan = slow
    llm = LLM(monkeypatch, plans=[plan])
    events, _ = await _run("Which Fire-type Pokémon live near volcanoes?", session_factory)
    assert _first(events, "plan")["planner"] == "keyword"
    assert llm.plan_calls == 1  # no retry
    assert ("done" in [n for n, _ in events])
    assert cache.answers.get("ask", "Which Fire-type Pokémon live near volcanoes?") is None


async def test_answer_429_mid_stream_is_extractive(monkeypatch, session_factory):
    _settings(monkeypatch)
    LLM(monkeypatch, answer="Partial", answer_exc=_rate_limit())
    events, text = await _run("Tell me about Snorlax", session_factory)
    assert text.startswith("Partial\n\n---\n\n")
    assert "straight from the Pokédex" in text
    assert [n for n, _ in events][-1] == "done"
    assert cache.answers.get("ask", "Tell me about Snorlax") is None


# ---- caching ------------------------------------------------------------------------------


async def test_repeat_question_served_from_cache(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch, plans=[_plan(("type_matchup", {"types": ["fire"]}),
                                        ("semantic_search", {"query": "volcano"}))])
    q = "What is Fire weak to, and which Pokémon live in volcanoes?"
    first, text1 = await _run(q, session_factory)
    second, text2 = await _run(q.lower() + "  ", session_factory)
    assert text1 == text2
    assert _first(second, "plan")["cached"] is True
    assert _first(second, "done")["usage"]["llm_calls"] == 0
    assert (llm.plan_calls, llm.answer_calls) == (1, 1)
    assert [d for n, d in first if n == "view"] == [d for n, d in second if n == "view"]


async def test_profile_answers_are_not_cached(monkeypatch, session_factory):
    _settings(monkeypatch)
    llm = LLM(monkeypatch)
    await _run("Recommend a Pokémon for me", session_factory)
    await _run("Recommend a Pokémon for me", session_factory)
    assert llm.answer_calls == 2
