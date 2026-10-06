"""Team-coach tools against temporary teams (needs the Compose DB)."""

from __future__ import annotations

import json

import pytest
import pytest_asyncio

from app.agent import team_tools  # noqa: F401 — registers the team tools
from app.agent.tools import REGISTRY, AgentContext, tools_for
from app.core.config import Settings
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import teams as teams_service

PLAYER = [445, 6, 130]  # Garchomp, Charizard, Gyarados
OPPONENT = [9, 373]  # Blastoise, Salamence


@pytest_asyncio.fixture
async def teams(session):
    made = []

    async def make(name, kind, ids):
        t = await teams_service.create_team(session, TeamCreate(name=name, kind=kind))
        made.append(t.id)
        for i, pid in enumerate(ids, start=1):
            await teams_service.set_slot(session, t.id, i, SlotUpdate(pokemon_id=pid))
        return await teams_service.get_team(session, t.id)

    player = await make("__test_player__", "player", PLAYER)
    opponent = await make("__test_opponent__", "opponent", OPPONENT)
    yield player, opponent
    for tid in made:
        await teams_service.delete_team(session, tid)


def _ctx(team, opponent=None, report=None, **extra):
    return AgentContext(scope="team", team=team, opponent=opponent, report=report, extra=extra)


async def run(session, name, ctx, **args):
    t = REGISTRY[name]
    return await t.handler(session, t.args.model_validate(args), ctx)


# ---- 2.1 team_context -----------------------------------------------------------------


async def test_context_report_first_and_opponent_only_when_set(session, teams) -> None:
    player, opponent = teams
    r = await run(session, "team_context", _ctx(player, report="Grade B. Weak to Ice."))
    assert r.chunks[0].chunk_type == "team_report"
    assert not any(c.chunk_type == "opponent_member" for c in r.chunks)
    assert len({c.id for c in r.chunks}) == len(r.chunks)  # unique ids survive de-duplication

    r = await run(session, "team_context", _ctx(player, opponent))
    kinds = [c.chunk_type for c in r.chunks]
    assert kinds[0] == "team_member" and "opponent_member" in kinds and "vs_opponent" in kinds


# ---- 2.2 recommend_additions ------------------------------------------------------------


async def test_recommend_sweepers_non_legendary(session, teams) -> None:
    from sqlalchemy import select

    from app.models import Pokemon

    player, _ = teams
    r = await run(session, "recommend_additions", _ctx(player), role="sweeper", legendary=False)
    [view] = r.views
    ids = [c.pokemon_id for c in view.candidates]
    assert ids and not set(ids) & set(PLAYER)
    flagged = (await session.execute(select(Pokemon.id).where(
        Pokemon.id.in_(ids), Pokemon.is_legendary | Pokemon.is_mythical))).scalars().all()
    assert not flagged
    assert all(c.base_stats["speed"] >= 90 for c in view.candidates)
    assert view.team_full is False and [m.name for m in view.members][:1] == ["Garchomp"]


# ---- 2.3 propose_set_edit ---------------------------------------------------------------


def _llm(monkeypatch, key="g", payload=None):
    from app.rag import answer as answer_service
    from app.rag import build_suggest

    monkeypatch.setattr(build_suggest, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key=key))

    async def fake(system, user, *, usage=None, **kw):
        if usage is not None:
            usage.add(1000, 100)
        return json.dumps(payload)

    monkeypatch.setattr(answer_service, "quick_complete", fake)


SET = {"moves": ["Earthquake", "Dragon Claw", "Swords Dance", "Made Up Move"],
       "ability": "Rough Skin", "nature": "Jolly", "item": "Choice Scarf",
       "evs": {"hp": 4, "atk": 252, "def": 0, "spa": 0, "spd": 0, "spe": 252},
       "why": "Scarf Jolly outspeeds more threats."}


async def test_set_edit_proposal(session, teams, monkeypatch) -> None:
    from app.rag.answer import Usage

    player, opponent = teams
    _llm(monkeypatch, payload=SET)
    usage = Usage()
    r = await run(session, "propose_set_edit", _ctx(player, opponent, usage=usage),
                  member="garchomp", side="ours", request="faster set")
    [v] = r.views
    assert v.side == "ours" and v.team_id == player.id and v.slot == 1
    assert "Made Up Move" not in v.after.moves  # invented options dropped
    assert v.fields["nature"] == "Jolly" and "evs" in v.fields
    assert v.member["pokemon_id"] == 445 and usage.calls == 1
    stored = await teams_service.get_team(session, player.id)
    assert stored.members[0].nature is None  # nothing saved


async def test_set_edit_opponent_unknown_and_keyless(session, teams, monkeypatch) -> None:
    player, opponent = teams
    _llm(monkeypatch, payload={**SET, "moves": ["Dragon Claw", "Fly"], "ability": "Intimidate"})
    r = await run(session, "propose_set_edit", _ctx(player, opponent),
                  member="Salamence", side="theirs", request="bulkier")
    assert r.views[0].side == "theirs" and r.views[0].team_id == opponent.id

    r = await run(session, "propose_set_edit", _ctx(player, opponent),
                  member="Pikachu", side="ours", request="x")
    assert r.status == "error" and "isn't on the team" in r.summary

    _llm(monkeypatch, key="", payload=SET)
    r = await run(session, "propose_set_edit", _ctx(player), member="Garchomp", side="ours",
                  request="x")
    assert r.status == "error" and "LLM key" in r.summary


# ---- 2.4 add_member -----------------------------------------------------------------------


async def test_add_saves_and_refuses(session, teams) -> None:
    player, _ = teams
    r = await run(session, "add_member", _ctx(player, allow_add=True), pokemon="Dragonite")
    [v] = r.views
    assert v.added and v.slot == 4 and r.data["team_updated"]["members"][3]["name"] == "Dragonite"

    again = await teams_service.get_team(session, player.id)
    r = await run(session, "add_member", _ctx(again, allow_add=True), pokemon="Dragonite")
    assert not r.views[0].added and "already on this team" in r.views[0].message

    for slot, pid in ((5, 25), (6, 143)):
        await teams_service.set_slot(session, player.id, slot, SlotUpdate(pokemon_id=pid))
    full = await teams_service.get_team(session, player.id)
    r = await run(session, "add_member", _ctx(full, allow_add=True), pokemon="Gengar")
    assert not r.views[0].added and "full" in r.views[0].message
    assert len((await teams_service.get_team(session, player.id)).members) == 6


async def test_add_card_mode_never_writes(session, teams) -> None:
    player, _ = teams
    r = await run(session, "add_member", _ctx(player), pokemon="Dragonite")
    [v] = r.views
    assert v.kind == "candidates" and v.candidates[0].name == "Dragonite"
    assert len((await teams_service.get_team(session, player.id)).members) == 3


# ---- 2.5 duel -----------------------------------------------------------------------------


async def test_duel(session, teams) -> None:
    player, opponent = teams
    r = await run(session, "duel", _ctx(player, opponent), ours="Garchomp", theirs="Salamence")
    [v] = r.views
    assert v.kind == "duel" and v.duel.our_name == "Garchomp" and v.duel.log
    r = await run(session, "duel", _ctx(player), ours="Garchomp", theirs="Salamence")
    assert r.status == "error" and "opponent" in r.summary


# ---- 2.6 registry invariants -------------------------------------------------------------


def test_scopes_and_planner_visibility() -> None:
    from app.agent import llm_planner

    team_only = {"team_context", "recommend_additions", "propose_set_edit", "add_member", "duel"}
    assert not team_only & {t.name for t in tools_for("ask")}
    assert team_only <= {t.name for t in tools_for("team")}
    assert "team_context" not in {t.name for t in tools_for("team", plannable_only=True)}
    assert llm_planner.prompt_size("team") <= llm_planner.PROMPT_BUDGET


class _SpySession:
    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        if name in ("add", "add_all", "flush", "commit", "delete", "merge"):
            raise AssertionError(f"tool wrote via {name}")
        return getattr(self._inner, name)


@pytest.mark.parametrize("name,args", [
    ("team_context", {}), ("recommend_additions", {"role": "wall"}),
    ("duel", {"ours": "Garchomp", "theirs": "Blastoise"}),
    ("add_member", {"pokemon": "Dragonite"}),  # card mode: no allow_add
])
async def test_read_only_tools(session, teams, name, args) -> None:
    player, opponent = teams
    t = REGISTRY[name]
    await t.handler(_SpySession(session), t.args.model_validate(args), _ctx(player, opponent))
