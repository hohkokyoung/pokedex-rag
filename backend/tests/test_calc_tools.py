"""Calc-coach tools on a fixed calculator state (needs the Compose DB for species/moves)."""

from __future__ import annotations

import json

import pytest

from app.agent import calc_tools  # noqa: F401 — registers the calc tools
from app.agent.tools import REGISTRY, AgentContext, tools_for
from app.core.config import Settings
from app.schemas.calc import CalcAskRequest
from app.services import damage_calc as dc
from app.services.calc_state import resolve_state

STATE = {
    "question": "q",
    "level": 100,
    "focus": 0,
    "slots": [
        {"slot": 0, "pokemon_id": 445, "nature": "Jolly", "evs": {"atk": 252, "spe": 252, "hp": 4},
         "item": "Life Orb", "ability": "Rough Skin", "move": "Earthquake", "aim": 2},
        {"slot": 2, "pokemon_id": 485, "nature": "Modest", "evs": {"hp": 252, "spa": 252},
         "item": "Leftovers", "move": "Flamethrower", "aim": 0},
    ],
    "hits": [{"attacker": 0, "target": 2, "move": "Earthquake", "min_pct": 200, "max_pct": 236,
              "ko": 1, "te": 4}],
}


async def _ctx(session, **kw):
    st = await resolve_state(session, CalcAskRequest(**{**STATE, **kw}))
    return AgentContext(scope="calc", extra={"calc": st})


async def run(session, name, ctx, **args):
    t = REGISTRY[name]
    return await t.handler(session, t.args.model_validate(args), ctx)


# ---- 2.2 calc_context -----------------------------------------------------------------


async def test_context_order_and_ids(session) -> None:
    r = await run(session, "calc_context", await _ctx(session))
    kinds = [c.chunk_type for c in r.chunks]
    assert kinds == ["calc_slot", "calc_slot", "calc_field", "calc_hits"]
    assert len({c.id for c in r.chunks}) == len(r.chunks)
    assert "your Garchomp" in r.chunks[0].content and "the opposing Heatran" in r.chunks[1].content
    assert "calc_proposal" not in kinds and "never invent damage" in r.note

    proposal = {"slot": 0, "build": {"pokemon": "Garchomp", "moves": ["Earthquake"],
                                     "ability": "Rough Skin", "nature": "Jolly", "item": "Life Orb",
                                     "evs": {"atk": 252, "spe": 252}, "why": "fast"},
                "thread": [{"ask": "best build", "reply": "fast"}]}
    r = await run(session, "calc_context", await _ctx(session, proposal=proposal))
    assert r.chunks[-1].chunk_type == "calc_proposal"


# ---- 2.3 damage_calc ------------------------------------------------------------------


async def test_damage_equals_port(session) -> None:
    ctx = await _ctx(session)
    r = await run(session, "damage_calc", ctx)
    st = ctx.extra["calc"]
    g, h = st.by_slot(0), st.by_slot(2)
    want = dc.calc_hit(g.mon, g.set, h.mon, h.set, g.move.maths, st.field)
    [v] = r.views
    assert v.current.min_pct == round(want.min_pct, 1) and v.current.ko == want.ko
    assert v.attacker.name == "Garchomp" and v.defender.name == "Heatran" and not v.whatif
    assert v.current.ko_text == "a guaranteed OHKO"


async def test_whatif_and_apply(session) -> None:
    ctx = await _ctx(session)
    plain = await run(session, "damage_calc", ctx, move="Dragon Claw")
    band = await run(session, "damage_calc", ctx, move="Dragon Claw",
                     changes=[{"who": "attacker", "key": "item", "value": "Choice Band"}])
    [v] = band.views
    assert v.whatif.max_pct > v.current.max_pct == plain.views[0].current.max_pct
    assert v.apply[0].slot == 0 and v.apply[0].fields == {"item": "Choice Band"}


async def test_damage_errors(session) -> None:
    ctx = await _ctx(session)
    r = await run(session, "damage_calc", ctx, changes=[{"who": "attacker", "key": "speed",
                                                          "value": "1"}])
    assert r.status == "error"
    r = await run(session, "damage_calc", ctx, move="Hydro Pump")  # Garchomp can't learn it
    assert r.status == "error" and "can't learn" in r.summary
    r = await run(session, "damage_calc", ctx, attacker="Pikachu")
    assert r.status == "error" and "isn't in the calculator" in r.summary


# ---- 2.4 survive_threshold ------------------------------------------------------------


async def test_survive_view_and_apply(session) -> None:
    # Garchomp at 30% HP with only Atk invested: needs HP/SpD to live through Flamethrower.
    slots = [{**STATE["slots"][0], "evs": {"atk": 252}, "hp": 30}, STATE["slots"][1]]
    ctx = await _ctx(session, slots=slots)
    r = await run(session, "survive_threshold", ctx, defender="Garchomp", attacker="Heatran",
                  move="Flamethrower")
    [v] = r.views
    assert v.survives and not v.already and v.stat == "spd"
    assert v.apply.slot == 0 and v.apply.fields["evs"]["hp"] == v.hp_ev
    assert v.apply.fields["evs"]["atk"] == 252  # the rest of the spread is kept
    st = ctx.extra["calc"]
    g, h = st.by_slot(0), st.by_slot(2)
    side = type(g.set)(**{**g.set.__dict__, "ev": v.apply.fields["evs"],
                          "nat": v.apply.fields.get("nature", g.set.nat)})
    assert dc.calc_hit(h.mon, h.set, g.mon, side, h.move.maths, st.field).max_pct < 30
    assert v.range.max_pct <= 30 <= v.current.max_pct  # (range is rounded to 0.1)

    ctx = await _ctx(session, focus=2)
    r = await run(session, "survive_threshold", ctx, defender="Heatran", attacker="Garchomp")
    assert r.views[0].survives is False and r.views[0].apply is None  # 4x Earthquake


async def test_survive_already(session) -> None:
    """Already surviving: no Apply (the minimal spread could strip bulk), real KO wording."""
    r = await run(session, "survive_threshold", await _ctx(session), defender="Garchomp",
                  attacker="Heatran", move="Flamethrower")
    [v] = r.views
    assert v.already and v.apply is None and "already survives" in r.summary
    assert v.current.ko >= 2 and v.current.ko_text == f"a {v.current.ko}HKO"


# ---- 2.5 propose_build ----------------------------------------------------------------


async def test_propose_build_passes_proposal_and_thread(session, monkeypatch) -> None:
    from app.rag import answer as answer_service
    from app.rag import build_suggest

    monkeypatch.setattr(build_suggest, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key="g"))
    seen: list[str] = []

    async def fake(system, user, *, usage=None, **kw):
        seen.append(user)
        return json.dumps({"moves": ["Earthquake", "Dragon Claw", "Swords Dance", "Not A Move"],
                           "ability": "Rough Skin", "nature": "Impish", "item": "Leftovers",
                           "evs": {"hp": 252, "atk": 4, "def": 252, "spa": 0, "spd": 0, "spe": 0},
                           "why": "Bulkier."})

    monkeypatch.setattr(answer_service, "quick_complete", fake)
    proposal = {"slot": 0, "build": {"pokemon": "Garchomp", "moves": ["Earthquake"],
                                     "ability": "Rough Skin", "nature": "Jolly", "item": "Life Orb",
                                     "evs": {"atk": 252, "spe": 252}, "why": "fast"},
                "thread": [{"ask": "best build", "reply": "fast"}]}
    r = await run(session, "propose_build", await _ctx(session, proposal=proposal),
                  request="make it bulkier")
    [v] = r.views
    assert v.slot == 0 and "Not A Move" not in v.build.moves and v.build.nature == "Impish"
    assert "Current set:" in seen[0] and "best build" in seen[0]  # proposal + thread passed


# ---- 2.6 registry ----------------------------------------------------------------------


def test_calc_scope_and_budget() -> None:
    from app.agent import llm_planner

    calc = {t.name for t in tools_for("calc")}
    assert {"calc_context", "damage_calc", "survive_threshold", "propose_build",
            "learnset"} <= calc
    assert "calc_context" not in {t.name for t in tools_for("calc", plannable_only=True)}
    assert not {"damage_calc", "propose_build"} & {t.name for t in tools_for("ask")}
    assert llm_planner.prompt_size("calc") <= llm_planner.PROMPT_BUDGET


class _SpySession:
    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        if name in ("add", "add_all", "flush", "commit", "delete", "merge"):
            raise AssertionError(f"tool wrote via {name}")
        return getattr(self._inner, name)


@pytest.mark.parametrize("name,args", [
    ("calc_context", {}), ("damage_calc", {}),
    ("survive_threshold", {"defender": "Heatran", "attacker": "Garchomp", "move": "Dragon Claw"}),
])
async def test_calc_tools_read_only(session, name, args) -> None:
    ctx = await _ctx(session)
    t = REGISTRY[name]
    await t.handler(_SpySession(session), t.args.model_validate(args), ctx)
