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
