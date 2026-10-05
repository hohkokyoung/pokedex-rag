"""Executor, code-rendered answers and caches (no LLM, no DB except where noted)."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from pydantic import BaseModel

from app.agent import cache, executor, render
from app.agent import tools as agent_tools
from app.agent.plan import build_plan
from app.agent.results import ToolResult
from app.agent.views import (
    LearnCheckView,
    MoveListView,
    MoveRow,
    PokemonCard,
    TypeChartView,
)

# ---- 5.1 executor ---------------------------------------------------------------------


class _A(BaseModel):
    n: float = 0.0


@asynccontextmanager
async def _fake_session():
    yield object()


def _install(monkeypatch):
    reg = {}

    async def sleeper(session, args, ctx):
        await asyncio.sleep(args.n)
        return ToolResult(summary=f"slept {args.n}")

    async def raiser(session, args, ctx):
        raise RuntimeError("boom")

    for name, fn in (("sleep", sleeper), ("boom", raiser)):
        reg[name] = agent_tools.Tool(name, frozenset({"ask"}), name, _A, fn)
    monkeypatch.setattr(agent_tools, "REGISTRY", reg)
    monkeypatch.setattr("app.agent.plan.REGISTRY", reg)
    monkeypatch.setattr(executor, "REGISTRY", reg)


async def _collect(plan, **kw):
    return [e async for e in executor.run(plan, _fake_session, **kw)]


async def test_independent_steps_overlap_and_failures_isolated(monkeypatch):
    _install(monkeypatch)
    plan = build_plan([
        {"id": "a", "tool": "sleep", "args": {"n": 0.2}},
        {"id": "b", "tool": "sleep", "args": {"n": 0.2}},
        {"id": "c", "tool": "boom", "args": {}},
        {"id": "d", "tool": "sleep", "args": {"n": 5}},
    ], "llm")
    t = time.monotonic()
    events = await _collect(plan, timeout=0.5)
    elapsed = time.monotonic() - t
    final = {e.step.id: e.state for e in events if e.state != "running"}
    assert final == {"a": "done", "b": "done", "c": "error", "d": "error"}
    assert elapsed < 1.0  # a and b ran together; d was cut off at the timeout
    d = next(e for e in events if e.step.id == "d" and e.state == "error")
    assert "timed out" in d.result.summary


async def test_after_orders_steps(monkeypatch):
    _install(monkeypatch)
    plan = build_plan([
        {"id": "a", "tool": "sleep", "args": {"n": 0.05}},
        {"id": "b", "tool": "sleep", "args": {"n": 0}, "after": ["a"]},
    ], "llm")
    order = [(e.step.id, e.state) for e in await _collect(plan)]
    assert order.index(("a", "done")) < order.index(("b", "running"))


async def test_invalid_steps_report_error_without_running(monkeypatch):
    _install(monkeypatch)
    plan = build_plan([{"id": "x", "tool": "missing", "args": {}}], "llm")
    [ev] = await _collect(plan)
    assert ev.state == "error" and ev.result.summary.startswith("unknown tool")


# ---- 5.2 code-rendered answers --------------------------------------------------------

CARD = PokemonCard(name="Garchomp", dex_number=445)
MOVE = MoveRow(ref=1, name="Earthquake", type="ground", damage_class="physical", power=100,
               accuracy=100, pp=10, learners=292, effect="Hits everything.")


def test_two_closed_steps_number_citations_in_order():
    check = ToolResult(views=[LearnCheckView(pokemon=CARD, move=MOVE, ok=True, how="by TM")])
    chart = ToolResult(views=[TypeChartView(types=["fire"], weak_2x=["water", "ground", "rock"],
                                            resist_half=["fire", "grass"])])
    text = render.render_all([("learnset", check, 0), ("type_matchup", chart, 3)])
    first, second = text.split("\n\n", 1)
    assert first == "Yes — **Garchomp** can learn **Earthquake** by TM [1]."
    assert second.startswith("A Fire-type Pokémon is weak to Water, Ground and Rock moves [4].")
    assert "- **Resists** — Fire and Grass [4]" in second


def test_move_template_opens_with_one_sentence():
    text = render.render_step("move_info", ToolResult(views=[MoveListView(moves=[MOVE])]))
    opening, rest = text.split("\n\n", 1)
    assert opening.count(".") == 1 and opening.endswith("[2].")
    assert "- **Learned by** — 292 Pokémon [2]" in rest


def test_negative_learn_check_and_unrenderable():
    no = ToolResult(views=[LearnCheckView(pokemon=CARD, move=MOVE, ok=False)])
    assert render.render_step("learnset", no).startswith("No — **Garchomp** can't learn")
    assert render.render_all([("semantic_search", ToolResult(), 0)]) is None


# ---- 5.3 caches ---------------------------------------------------------------------------


def test_normalize_and_lru():
    assert cache.normalize("Who learns Earthquake?") == cache.normalize("who  learns earthquake")
    lru = cache.LRU(2)
    lru.put("ask", "a", [1])
    lru.put("ask", "b", [2])
    assert lru.get("ask", "A?") == [1]  # touch a → b is now oldest
    lru.put("ask", "c", [3])
    assert lru.get("ask", "b") is None and lru.get("ask", "c") == [3]
    assert lru.get("team", "a") is None  # scoped


def test_cache_returns_copies():
    lru = cache.LRU(4)
    value = {"x": [1]}
    lru.put("ask", "q", value)
    got = lru.get("ask", "q")
    got["x"].append(2)
    assert lru.get("ask", "q") == {"x": [1]}
