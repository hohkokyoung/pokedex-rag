"""LLM planner with a stubbed provider: schema, validation, re-plan rules, prompt budget."""

from __future__ import annotations

import json

import pytest

from app.agent import llm_planner
from app.agent.plan import MAX_STEPS
from app.agent.tools import tools_for


def _stub(monkeypatch, *payloads):
    """quick_complete returns each payload in turn and records its kwargs."""
    calls: list[dict] = []
    queue = list(payloads)

    async def fake(system, user, **kw):
        calls.append({"system": system, "user": user, **kw})
        p = queue.pop(0)
        if isinstance(p, BaseException):
            raise p
        return json.dumps(p)

    monkeypatch.setattr(llm_planner.answer_service, "quick_complete", fake)
    return calls


def _s(sid, tool, args, after=None):
    return {"id": sid, "tool": tool, "why": "w", "after": after or [], "args": args}


async def test_valid_plan_and_request_shape(monkeypatch):
    calls = _stub(monkeypatch, {"needs_followup": False, "steps": [
        _s("a", "learnset", {"move": "Will-O-Wisp", "types": ["fire"], "pokemon": None}),
        _s("b", "type_matchup", {"types": ["fire"]}),
    ]})
    plan = await llm_planner.plan_llm("q")
    assert plan.planner == "llm" and [s.tool for s in plan.valid_steps] == [
        "learnset", "type_matchup"]
    assert plan.steps[0].parsed.types == ["fire"]
    kw = calls[0]
    assert kw["json_schema"] is kw["tool_schema"]  # same schema for both providers
    assert kw["reasoning_effort"] == "low" and kw["retry"] is False and kw["cache_system"]


async def test_partially_invalid_plan(monkeypatch):
    _stub(monkeypatch, {"needs_followup": False, "steps": [
        _s("a", "nope_tool", {}),
        _s("b", "query_pokemon", {"sort_by": "charm"}),
        _s("c", "move_info", {"name": "Surf"}, after=["zz"]),
        _s("d", "move_info", {"name": "Surf"}),
    ]})
    plan = await llm_planner.plan_llm("q")
    errors = [s.error for s in plan.steps]
    assert errors[0].startswith("unknown tool")
    assert errors[1].startswith("bad args (sort_by")
    assert errors[2].startswith("depends on unknown step")
    assert errors[3] is None and [s.id for s in plan.valid_steps] == ["d"]


async def test_fully_invalid_and_capped(monkeypatch):
    _stub(monkeypatch, {"needs_followup": False,
                        "steps": [_s(f"x{i}", "nope", {}) for i in range(10)]})
    plan = await llm_planner.plan_llm("q")
    assert len(plan.steps) == MAX_STEPS and not plan.valid_steps


async def test_nulls_fall_back_to_defaults(monkeypatch):
    _stub(monkeypatch, {"needs_followup": False, "steps": [
        _s("a", "query_pokemon", {"types_all": None, "order": None, "limit": None,
                                  "sort_by": "speed"}),
    ]})
    [step] = (await llm_planner.plan_llm("q")).steps
    assert step.error is None and step.parsed.order == "desc" and step.parsed.limit == 5


async def test_provider_error_propagates(monkeypatch):
    _stub(monkeypatch, RuntimeError("429"))
    with pytest.raises(RuntimeError):
        await llm_planner.plan_llm("q")


# ---- 4.4 re-plan ------------------------------------------------------------------------


async def test_should_replan_rules(monkeypatch):
    _stub(monkeypatch, {"needs_followup": False, "steps": [
        _s("a", "query_pokemon", {"sort_by": "speed"}),
        _s("b", "learnset", {"pokemon": "Zorbulax"}),
    ]})
    plan = await llm_planner.plan_llm("q")
    assert not llm_planner.should_replan(plan, {"a": "empty", "b": "done"})
    assert llm_planner.should_replan(plan, {"a": "done", "b": "error"})
    plan.planner = "keyword"
    assert not llm_planner.should_replan(plan, {"a": "done", "b": "error"})


async def test_replan_adds_fresh_steps_only(monkeypatch):
    _stub(
        monkeypatch,
        {"needs_followup": False, "steps": [
            _s("a", "move_info", {"name": "Surf"}),
            _s("b", "learnset", {"pokemon": "Zorbulax"}),
        ]},
        {"needs_followup": False, "steps": [
            _s("a", "move_info", {"name": "Surf"}),           # repeat of a success → dropped
            _s("x", "learnset", {"pokemon": "Zubat"}),
            _s("y", "type_matchup", {"types": ["fire"]}),
            _s("z", "type_matchup", {"types": ["water"]}),
            _s("w", "type_matchup", {"types": ["grass"]}),   # over the cap
        ]},
    )
    plan = await llm_planner.plan_llm("q")
    added = await llm_planner.replan(
        "q", plan, {"a": ("done", "Surf"), "b": ("error", 'unresolved Pokémon "Zorbulax"')}
    )
    assert [s.tool for s in added.steps] == ["learnset", "type_matchup", "type_matchup"]
    assert all(s.id not in {"a", "b"} for s in added.steps)


# ---- prompt budget (task 3.6) -----------------------------------------------------------


def test_ask_planning_prompt_within_budget():
    assert llm_planner.prompt_size("ask") <= 10_000


def test_schema_is_strict_and_covers_every_tool():
    schema = llm_planner.plan_schema("ask")
    options = schema["properties"]["steps"]["items"]["anyOf"]
    assert {o["properties"]["tool"]["enum"][0] for o in options} == {
        t.name for t in tools_for("ask")}

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and node.get("properties"):
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(schema)


async def test_non_legendary_also_excludes_mythicals(monkeypatch):
    _stub(monkeypatch, {"needs_followup": False, "steps": [
        _s("a", "learnset", {"move": "Earthquake", "legendary": False, "mythical": None}),
        _s("b", "learnset", {"move": "Earthquake", "legendary": None, "mythical": None}),
    ]})
    a, b = (await llm_planner.plan_llm("q")).steps
    assert (a.parsed.legendary, a.parsed.mythical) == (False, False)
    assert (b.parsed.legendary, b.parsed.mythical) == (None, None)


# ---- team scope ---------------------------------------------------------------------------


async def test_team_prompt_roster_schema_and_empty_plan(monkeypatch):
    from types import SimpleNamespace as NS

    calls = _stub(monkeypatch, {"needs_followup": False, "steps": []})
    team = NS(members=[NS(name="Garchomp"), NS(name="Gyarados")])
    opp = NS(members=[NS(name="Salamence")])
    roster = llm_planner.roster_line(team, opp)
    plan = await llm_planner.plan_llm("What's my weakness?", "team", roster=roster)
    assert plan.steps == []  # an empty plan is a valid team answer (context only)
    assert "Your team: Garchomp, Gyarados; Opponent: Salamence" in calls[0]["user"]
    assert "ALREADY" in calls[0]["system"] and "add_member ONLY" in calls[0]["system"]

    tools = {o["properties"]["tool"]["enum"][0]
             for o in llm_planner.plan_schema("team")["properties"]["steps"]["items"]["anyOf"]}
    assert {"recommend_additions", "propose_set_edit", "add_member", "duel", "learnset"} <= tools
    assert "team_context" not in tools and "semantic_search" not in tools
    assert "add_member" not in {
        o["properties"]["tool"]["enum"][0]
        for o in llm_planner.plan_schema("ask")["properties"]["steps"]["items"]["anyOf"]}
