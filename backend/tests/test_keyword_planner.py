"""Keyword planner: names first, then cues; and the fast-path confidence check."""

from __future__ import annotations

import pytest

from app.agent.keyword_planner import plan_keywords


async def _plan(session, q):
    kp = await plan_keywords(session, q)
    assert all(s.error is None for s in kp.plan.steps), [s.error for s in kp.plan.steps]
    return kp


def _tools(kp):
    return [(s.tool, {k: v for k, v in s.args.items() if v not in (None, [], False)})
            for s in kp.plan.steps]


@pytest.mark.parametrize("q,expected", [
    ("What does Earthquake do?", [("move_info", {"name": "Earthquake"})]),
    ("Who learns Earthquake?", [("learnset", {"move": "Earthquake"})]),
    ("Can Garchomp learn Earthquake?",
     [("learnset", {"pokemon": "Garchomp", "move": "Earthquake"})]),
    ("Tell me about Psychic",
     [("move_info", {"name": "Psychic"}), ("type_matchup", {"types": ["psychic"]})]),
    ("Tell me about Snorlax", [("get_pokemon", {"name": "Snorlax"})]),
    ("Pokémon like Gengar", [("similar_to", {"name": "Gengar"})]),
    ("Recommend a Pokémon for me", [("user_profile", {})]),
    ("Moves that beat Garchomp",
     [("coverage_vs_types", {"against": "Garchomp", "want": "moves"})]),
    ("What counters Dragonite?", [("coverage_vs_types", {"against": "Dragonite"})]),
    ("Which non-legendary Pokémon learn Earthquake?",
     [("learnset", {"move": "Earthquake"})]),
])
async def test_plans(session, q, expected) -> None:
    kp = await _plan(session, q)
    got = _tools(kp)
    assert [t for t, _ in got] == [t for t, _ in expected]
    for (_, args), (_, want) in zip(got, expected, strict=True):
        for k, v in want.items():
            assert args.get(k) == v, (q, k, args)


async def test_ranking_cue(session) -> None:
    kp = await _plan(session, "Which Pokémon has the highest Attack?")
    [step] = kp.plan.steps
    assert step.tool == "query_pokemon"
    assert step.args["sort_by"] == "attack" and step.args["order"] == "desc"


async def test_lore_question_searches(session) -> None:
    kp = await _plan(session, "Which Pokémon live in volcanoes?")
    assert [s.tool for s in kp.plan.steps] == ["semantic_search"]


async def test_legendary_negation_is_an_arg(session) -> None:
    kp = await _plan(session, "Which non-legendary Pokémon learn Earthquake?")
    assert kp.plan.steps[0].args["legendary"] is False


async def test_hybrid_type_plus_lore(session) -> None:
    kp = await _plan(session, "Which Fire-type Pokémon live near volcanoes?")
    assert [s.tool for s in kp.plan.steps] == ["query_pokemon", "semantic_search"]


async def test_plans_are_keyword_and_capped(session) -> None:
    kp = await _plan(session, "Which Fire-type Pokémon live near volcanoes?")
    assert kp.plan.planner == "keyword" and len(kp.plan.steps) <= 3


# ---- 4.2 confidence -------------------------------------------------------------------


@pytest.mark.parametrize("q", [
    "Can Garchomp learn Earthquake?",
    "What does Earthquake do?",
    "Who learns Earthquake?",
    "Which Pokémon has the highest Attack?",
    "Highest Attack",
    "Fastest Pokémon",
    "Tell me about Snorlax",
    "Pokémon similar to Blaziken",
    "What is similar to Blaziken?",
    "Where can I catch Pikachu?",
    "What is Fire weak to?",
    "Fire weaknesses",
    "Recommend a Pokémon for me.",
    "Which Pokémon would I probably like?",
])
async def test_confident(session, q) -> None:
    assert (await _plan(session, q)).confident, q


@pytest.mark.parametrize("q", [
    "Tell me about Psychic",
    "Fastest non-legendary Fire type that learns Will-O-Wisp",
    "Moves that beat Garchomp",
    "Which Fire types learn Will-O-Wisp, and what is Fire weak to?",
    "What is Mewtwo's origin?",
    "Which Fire-type Pokémon has the highest Speed?",
    "Pokémon like Gengar but faster",
    "What is Psychic weak to?",
    "Where can I catch Pikachu and Eevee?",
    "Recommend me a Pokémon and tell me about Dragonite",
])
async def test_not_confident(session, q) -> None:
    assert not (await _plan(session, q)).confident, q


# ---- team scope (needs temporary teams) -------------------------------------------------


@pytest.fixture
async def team_ctx(session):
    from app.agent.tools import AgentContext
    from app.schemas.team import SlotUpdate, TeamCreate
    from app.services import teams as teams_service

    made = []

    async def make(name, kind, ids):
        t = await teams_service.create_team(session, TeamCreate(name=name, kind=kind))
        made.append(t.id)
        for i, pid in enumerate(ids, start=1):
            await teams_service.set_slot(session, t.id, i, SlotUpdate(pokemon_id=pid))
        return await teams_service.get_team(session, t.id)

    ctx = AgentContext(scope="team", team=await make("__kw_player__", "player", [445, 6, 130]),
                       opponent=await make("__kw_opp__", "opponent", [9, 373]))
    yield ctx
    for tid in made:
        await teams_service.delete_team(session, tid)


async def _team_plan(session, ctx, q):
    kp = await plan_keywords(session, q, "team", ctx)
    assert all(s.error is None for s in kp.plan.steps), [s.error for s in kp.plan.steps]
    return kp, [(s.tool, {k: v for k, v in s.args.items() if v not in (None, [], False)})
                for s in kp.plan.steps]


async def test_team_add_vs_deliberation(session, team_ctx) -> None:
    from app.agent.keyword_planner import is_imperative_add

    kp, steps = await _team_plan(session, team_ctx, "add Dragonite")
    assert steps == [("add_member", {"pokemon": "Dragonite"})] and kp.confident
    assert is_imperative_add("add Dragonite") and not is_imperative_add("Should I add Dragonite?")
    _kp, steps = await _team_plan(session, team_ctx, "Should I add Dragonite?")
    assert steps == [("add_member", {"pokemon": "Dragonite"})]  # the runner's gate → card


async def test_team_set_edits(session, team_ctx) -> None:
    kp, steps = await _team_plan(session, team_ctx, "Give Garchomp a faster set")
    assert steps[0][0] == "propose_set_edit" and steps[0][1]["member"] == "Garchomp"
    assert steps[0][1]["side"] == "ours" and kp.confident
    _kp, steps = await _team_plan(session, team_ctx, "Give their Salamence a bulkier set")
    assert steps[0][1] == {**steps[0][1], "member": "Salamence", "side": "theirs"}
    kp, steps = await _team_plan(session, team_ctx, "What item should Garchomp run?")
    assert steps[0][0] == "propose_set_edit"  # "run" isn't an add for a member
    kp, _ = await _team_plan(session, team_ctx, "Replace Charizard with something faster")
    assert not kp.confident


async def test_team_draft_duel_lookup_and_plain(session, team_ctx) -> None:
    kp, steps = await _team_plan(session, team_ctx,
                                 "Draft the rest of my team — non-legendary sweepers")
    assert steps == [("recommend_additions", {"role": "sweeper"})] or (
        steps[0][0] == "recommend_additions" and steps[0][1]["role"] == "sweeper")
    assert kp.plan.steps[0].parsed.legendary is False and not kp.confident

    _kp, steps = await _team_plan(session, team_ctx, "Garchomp vs Salamence — who wins?")
    assert steps == [("duel", {"ours": "Garchomp", "theirs": "Salamence"})]

    kp, steps = await _team_plan(session, team_ctx, "Can Garchomp learn Swords Dance?")
    assert steps == [("learnset", {"pokemon": "Garchomp", "move": "Swords Dance"})]

    kp, steps = await _team_plan(session, team_ctx, "What's my team's biggest weakness?")
    assert steps == [] and kp.confident


# ---- calc scope -------------------------------------------------------------------------


@pytest.fixture
async def calc_ctx(session):
    from app.agent.tools import AgentContext
    from app.schemas.calc import CalcAskRequest
    from app.services.calc_state import resolve_state

    st = await resolve_state(session, CalcAskRequest(question="q", slots=[
        {"slot": 0, "pokemon_id": 445, "move": "Earthquake", "aim": 2},
        {"slot": 2, "pokemon_id": 485, "move": "Flamethrower", "aim": 0},
    ]))
    return AgentContext(scope="calc", extra={"calc": st})


async def _calc_plan(session, ctx, q):
    kp = await plan_keywords(session, q, "calc", ctx)
    assert all(s.error is None for s in kp.plan.steps), [s.error for s in kp.plan.steps]
    return kp, [(s.tool, {k: v for k, v in s.args.items() if v not in (None, [], False)})
                for s in kp.plan.steps]


async def test_calc_damage_and_whatif(session, calc_ctx) -> None:
    kp, steps = await _calc_plan(session, calc_ctx, "Can Garchomp OHKO Heatran?")
    assert steps == [("damage_calc", {"attacker": "Garchomp", "defender": "Heatran"})]
    assert kp.confident
    kp, steps = await _calc_plan(session, calc_ctx, "Can Garchomp OHKO Heatran with Choice Band?")
    assert steps[0][1]["changes"] == [{"who": "attacker", "key": "item", "value": "Choice Band"}]
    assert kp.confident


async def test_calc_survive_build_dex_plain(session, calc_ctx) -> None:
    kp, steps = await _calc_plan(
        session, calc_ctx, "How much Def does Heatran need to survive Garchomp's Earthquake?")
    assert steps == [("survive_threshold", {"defender": "Heatran", "attacker": "Garchomp",
                                            "move": "Earthquake"})] and kp.confident
    for q in ("Best build", "Make it bulkier", "Bulky set", "Fast sweeper"):
        kp, steps = await _calc_plan(session, calc_ctx, q)
        assert steps[0][0] == "propose_build" and kp.confident, q
    kp, steps = await _calc_plan(session, calc_ctx, "Who learns Earthquake?")
    assert steps == [("learnset", {"move": "Earthquake"})]
    kp, steps = await _calc_plan(session, calc_ctx, "Who wins this?")
    assert steps == [] and kp.confident


async def test_calc_mixed_is_not_confident(session, calc_ctx) -> None:
    kp, steps = await _calc_plan(
        session, calc_ctx, "Can Garchomp OHKO Heatran with Choice Band, and a bulkier set?")
    assert [t for t, _ in steps] == ["damage_calc", "propose_build"] and not kp.confident


async def test_calc_revisions_need_a_proposal(session, calc_ctx) -> None:
    """A bare tweak ("no Choice item") revises the build on the table, else it's plain."""
    import dataclasses

    from app.schemas.calc import CalcProposal

    kp, steps = await _calc_plan(session, calc_ctx, "No Choice item")
    assert steps == [] and kp.confident
    st = calc_ctx.extra["calc"]
    calc_ctx.extra["calc"] = dataclasses.replace(st, proposal=CalcProposal(slot=0, build={
        "pokemon": "Garchomp", "moves": ["Earthquake"], "evs": {"atk": 252}, "why": "fast"}))
    for q in ("No Choice item", "Swap Fire Fang for Stone Edge", "Use Rocky Helmet instead"):
        kp, steps = await _calc_plan(session, calc_ctx, q)
        assert [t for t, _ in steps] == ["propose_build"] and kp.confident, q
    kp, steps = await _calc_plan(session, calc_ctx, "Explain the EVs")
    assert steps == [] and kp.confident


@pytest.mark.parametrize("q,method", [
    ("which pokemon learns earthquake by levelling only but is a water type", "level-up"),
    ("which water types get earthquake from a TM", "machine"),
    ("who learns earthquake as an egg move", "egg"),
    ("who learns earthquake", None),
])
async def test_learn_method_cue(session, q, method) -> None:
    kp = await plan_keywords(session, q)
    [step] = kp.plan.steps
    assert step.tool == "learnset" and step.args.get("method") == method
    assert kp.confident is (method is None)


@pytest.mark.parametrize("q,want", [
    ("What do Protect and Substitute do?", [("move_info", "Protect"), ("move_info", "Substitute")]),
    ("What do Intimidate and Leftovers do?",
     [("ability_info", "Intimidate"), ("item_info", "Leftovers")]),
    ("What do Protect and Leftovers do?", [("move_info", "Protect"), ("item_info", "Leftovers")]),
])
async def test_every_named_lookup_gets_a_step(session, q, want) -> None:
    """Seen live on a quota fallback: only Protect was looked up and Substitute dropped."""
    kp = await plan_keywords(session, q)
    assert [(s.tool, s.args["name"]) for s in kp.plan.steps] == want
    assert not kp.confident  # multi-part: the LLM planner still gets a say when available


@pytest.mark.parametrize("q,level", [
    ("does garchomp learn crunch below lvl 30", 29),
    ("can Garchomp learn Crunch before level 30?", 29),
    ("does Garchomp get Crunch by level 30", 30),
    ("can garchomp learn crunch at lv 30 or below", 30),
    ("who learns earthquake under level 20", 19),
    ("does garchomp learn crunch", None),
])
async def test_level_cap_cue(session, q, level) -> None:
    """ "below lvl 30" is a level cap on the learnset step, not a dropped constraint."""
    kp = await plan_keywords(session, q)
    [step] = kp.plan.steps
    assert step.tool == "learnset" and step.args.get("max_level") == level, step.args
    if level is not None:
        assert step.args["method"] == "level-up" and not kp.confident


async def test_unresolved_game_is_flagged_not_dropped(session) -> None:
    """A game the planner can't place is reported as unapplied, never silently ignored."""
    kp = await plan_keywords(session, "can garchomp learn crunch in the newest gizmo game")
    [step] = kp.plan.steps
    assert step.args.get("game") is None
    assert kp.plan.unhandled and "gizmo" in kp.plan.unhandled[0] and not kp.confident
    kp = await plan_keywords(session, "can garchomp learn crunch in new diamond and pearl game")
    assert kp.plan.steps[0].args["game"] == "Brilliant Diamond / Shining Pearl"
    assert not kp.plan.unhandled
