"""Ask-scope tools against the real data (skipped without the Compose DB)."""

from __future__ import annotations

import inspect

import pytest

from app.agent import ask_tools  # noqa: F401 — registers the tools
from app.agent.tools import REGISTRY, AgentContext, tools_for


async def run(session, _tool: str, **args):
    t = REGISTRY[_tool]
    return await t.handler(session, t.args.model_validate(args), AgentContext())


# ---- 3.1 query_pokemon --------------------------------------------------------------


async def test_query_ranking(session) -> None:
    r = await run(session, "query_pokemon", sort_by="attack", order="desc", limit=5)
    assert r.status == "done"
    [view] = r.views
    assert view.kind == "ranking" and view.stat == "attack"
    assert view.rows[0].name == "Kartana" and view.rows[0].value == 181
    assert view.total == r.data["total"]
    assert view.rows[0].types == ["grass", "steel"]
    assert [row.ref for row in view.rows] == [0, 1, 2, 3, 4]


async def test_query_types_are_normalised_and_impossible_is_empty(session) -> None:
    r = await run(session, "query_pokemon", types_all=["Fire"],
                  stat_filters=[{"stat": "speed", "op": "gt", "value": 250}])
    assert r.status == "empty" and r.data["total"] == 0
    assert r.data["query"].types_all == ["fire"]


# ---- 3.2 get_pokemon / similar_to / user_profile ------------------------------------


async def test_get_pokemon_profile_and_entry(session) -> None:
    r = await run(session, "get_pokemon", name="snorlax")
    assert r.status == "done" and r.chunks[0].chunk_type == "profile"
    card = r.views[0].cards[0]
    assert card.name == "Snorlax" and card.types == ["normal"] and card.entry


async def test_get_pokemon_close_match_and_form(session) -> None:
    r = await run(session, "get_pokemon", name="charizrd")
    assert "Charizard" in r.summary and "closest match" in r.summary
    r = await run(session, "get_pokemon", name="Mega Latios")
    assert r.views[0].cards[0].name == "Mega Latios"
    assert "alternate form of Latios" in r.chunks[0].content


async def test_similar_to_excludes_evolution_line(session) -> None:
    r = await run(session, "similar_to", name="Blaziken")
    names = {c.name for c in r.views[0].cards}
    assert names and not names & {"Torchic", "Combusken", "Blaziken"}
    assert all(c.match is not None for c in r.views[0].cards)
    assert "similar to it" in r.note


async def test_similar_to_leads_with_the_target(session) -> None:
    # The answer compares both sides, so the target's profile is evidence (not a card).
    r = await run(session, "similar_to", name="Jigglypuff")
    assert r.chunks[0].pokemon_name == "Jigglypuff" and r.chunks[0].source_ref == "target"
    assert "Jigglypuff" not in {c.name for c in r.views[0].cards}
    refs = r.views[0].chunk_refs
    assert refs == [c.ref for c in r.views[0].cards] and 0 not in refs
    assert "cite both sides" in r.note
    # The ranking is spelled out, so the answer can't call #2 "the closest".
    top = r.views[0].cards[0]
    assert f"The closest match is {top.name}" in r.note
    assert f"{top.name} ({round(top.match * 100)}%)" in r.note


async def test_user_profile_note(session) -> None:
    r = await run(session, "user_profile")
    assert r.data == {"profile": True}
    assert r.status in ("done", "empty")


# ---- 3.3 semantic_search / type_matchup / move_info --------------------------------


async def test_semantic_search(session) -> None:
    r = await run(session, "semantic_search", query="lives near volcanoes", k=4)
    assert r.status == "done" and len(r.chunks) <= 4 and not r.views


async def test_type_matchup_fire(session) -> None:
    r = await run(session, "type_matchup", types=["Fire"])
    [view] = r.views
    assert set(view.weak_2x) == {"water", "ground", "rock"}
    assert {"grass", "ice", "bug", "steel"} <= set(view.strong_against)
    assert "super-effective" in r.chunks[0].content


async def test_type_matchup_dual(session) -> None:
    r = await run(session, "type_matchup", types=["grass", "steel"])
    assert r.views[0].weak_4x == ["fire"]


async def test_move_info(session) -> None:
    r = await run(session, "move_info", name="will o wisp")
    [row] = r.views[0].moves
    assert row.name == "Will-O-Wisp" and row.type == "fire" and row.learners > 50


# ---- 3.4 coverage_vs_types / learnset ----------------------------------------------


async def test_coverage_special_vs_dark(session) -> None:
    r = await run(session, "coverage_vs_types", targets=["dark"], attacker_class="special")
    kinds = [v.kind for v in r.views]
    assert kinds == ["type_chart", "pokemon_list"]
    cards = r.views[1].cards
    assert cards and all(c.coverage for c in cards)
    assert all(c.chunk_type != "sql_row" or "physical" not in
               c.content.split("Coverage moves it can learn:")[1]
               for c in r.chunks if c.chunk_type == "sql_row")


async def test_learnset_check(session) -> None:
    r = await run(session, "learnset", pokemon="Pikachu", move="Surf")
    [view] = r.views
    assert view.kind == "learn_check" and isinstance(view.ok, bool)
    assert r.closed is True


async def test_learnset_learners_and_movepool(session) -> None:
    r = await run(session, "learnset", move="Earthquake", legendary=False)
    assert r.views[0].kind == "learners" and r.views[0].total > 100
    assert "non-legendary" in r.views[0].scope and r.closed is True
    r = await run(session, "learnset", pokemon="Blaziken")
    assert r.views[0].kind == "learnset" and r.closed is False


async def test_learnset_unresolved(session) -> None:
    r = await run(session, "learnset", pokemon="Zorbulax", move="Surf")
    assert r.status == "error" and r.summary.startswith("unresolved")


# ---- 3.5 ability_info / item_info / encounters -------------------------------------


@pytest.mark.parametrize("tool,name", [
    ("ability_info", "Intimidate"), ("item_info", "Leftovers"),
])
async def test_info_tools(session, tool, name) -> None:
    r = await run(session, tool, name=name)
    assert r.status == "done" and name in r.chunks[0].content
    miss = await run(session, tool, name="Qqqqqqqq Zzzz")
    assert miss.status == "empty"


async def test_encounters(session) -> None:
    r = await run(session, "encounters", pokemon="Pikachu")
    assert r.status == "done" and "Where to find Pikachu" in r.chunks[0].content
    miss = await run(session, "encounters", pokemon="Zorbulax")
    assert miss.status == "error"


# ---- 3.6 registry invariants -------------------------------------------------------


EXPECTED = {
    "query_pokemon", "get_pokemon", "semantic_search", "similar_to", "user_profile",
    "type_matchup", "coverage_vs_types", "learnset", "move_info", "ability_info",
    "item_info", "encounters",
}


def test_ask_scope_has_every_tool() -> None:
    assert {t.name for t in tools_for("ask")} == EXPECTED


def test_handlers_never_read_the_question() -> None:
    from dataclasses import fields

    assert "question" not in {f.name for f in fields(AgentContext)}
    for t in tools_for("ask"):
        params = inspect.signature(t.handler).parameters
        assert list(params) == ["session", "args", "ctx"], t.name
        assert "question" not in t.args.model_fields, t.name


class _SpySession:
    """Proxies a real session but fails on any write."""

    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        if name in ("add", "add_all", "flush", "commit", "delete", "merge"):
            raise AssertionError(f"tool wrote to the session via {name}")
        return getattr(self._inner, name)


@pytest.mark.parametrize("name,args", [
    ("query_pokemon", {"sort_by": "speed"}), ("get_pokemon", {"name": "Snorlax"}),
    ("semantic_search", {"query": "ghost"}), ("similar_to", {"name": "Gengar"}),
    ("user_profile", {}), ("type_matchup", {"types": ["fire"]}),
    ("coverage_vs_types", {"targets": ["water"]}), ("learnset", {"move": "Surf"}),
    ("move_info", {"name": "Surf"}), ("ability_info", {"name": "Levitate"}),
    ("item_info", {"name": "Choice Scarf"}), ("encounters", {"pokemon": "Zubat"}),
])
async def test_tools_are_read_only(session, name, args) -> None:
    t = REGISTRY[name]
    await t.handler(_SpySession(session), t.args.model_validate(args), AgentContext())


async def test_query_pokemon_game_filter(session) -> None:
    """ "in Scarlet/Violet" is a real filter (the game's learnset data), not Generation 9."""
    r = await run(session, "query_pokemon", sort_by="base_stat_total", limit=5,
                  game="Scarlet/Violet")
    assert r.data["query"].game == "Scarlet / Violet" and r.data["total"] > 500
    r = await run(session, "query_pokemon", sort_by="attack", game="Let's Go")
    assert r.data["total"] == 153  # the 151 + Meltan and Melmetal
    gen5_grass = {"types_all": ["grass"], "generation": 5, "limit": 25}
    every = {c.pokemon_name for c in (await run(session, "query_pokemon", **gen5_grass)).chunks}
    swsh = {c.pokemon_name for c in
            (await run(session, "query_pokemon", **gen5_grass, game="SwSh")).chunks}
    assert "Snivy" in every and "Snivy" not in swsh and swsh < every  # Snivy isn't in SwSh
    r = await run(session, "query_pokemon", game="Platinum Ultra")
    assert r.status == "error" and "unresolved game" in r.summary


async def test_learnset_level_cap_renders_no(session) -> None:
    from app.agent import render

    r = await run(session, "learnset", pokemon="Garchomp", move="Crunch", method="level-up",
                  max_level=29)
    assert r.views[0].ok is False and r.views[0].max_level == 29
    text = render.render_step("learnset", r)
    assert text.startswith("No — **Garchomp** doesn't learn **Crunch** by level-up by Lv 29"), text
    assert "Lv 48" in text
