"""The backend's turn equals the browser calculator's (``lib/calcTurn``) on its reference
cases (``make damage-fixtures``)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from app.services import calc_turn as ct
from app.services import damage_calc as dc

CASES = json.loads((Path(__file__).parent / "fixtures" / "turn_cases.json").read_text())
TOL = 0.01  # the per-hit maths' own tolerance (test_damage_calc)


def _slot(s: dict | None) -> ct.TurnSlot:
    if s is None:
        return ct.TurnSlot(mon=None)
    st = s["set"]
    m = s["move"]
    return ct.TurnSlot(
        mon=dc.Mon(**s["mon"]),
        set=dc.Side(nat=st["nat"], ev=st["ev"], iv=st["iv"], item=st["item"], abil=st["abil"],
                    hp=st["hp"]),
        move=ct.TurnMove(**m) if m else None,
    )


def _field(f: dict) -> ct.TurnField:
    return ct.TurnField(level=f["level"], doubles=f["doubles"], weather=f["weather"],
                        terrain=f["terrain"], reflect=f["reflect"], lightscreen=f["lightscreen"],
                        crit=f["crit"], burn=f["burn"], friend_guard=f["friendGuard"])


def test_fixture_is_substantial():
    assert CASES["version"] == 1 and len(CASES["cases"]) >= 60


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda c: c["id"])
def test_matches_the_calculator(case):
    t = ct.play_turn(_field(case["field"]), [_slot(s) for s in case["slots"]], case["aims"])
    want = case["result"]
    assert [(o.i, o.pri, o.spe) for o in t.order] == [
        (o["i"], o["pri"], o["spe"]) for o in want["order"]]
    assert [t.aim[i] for i in range(4)] == want["aim"]
    assert len(t.steps) == len(want["steps"])
    for got, w in zip(t.steps, want["steps"], strict=True):
        assert (got.i, got.skipped, got.at_risk) == (w["i"], w["skipped"], w["atRisk"])
        assert [(h.frm, h.to, h.ff, h.ko, h.sash) for h in got.hits] == [
            (h["from"], h["to"], h["ff"], h["ko"], h["sash"]) for h in w["hits"]]
        for h, wh in zip(got.hits, w["hits"], strict=True):
            assert h.r.min_pct == pytest.approx(wh["r"]["minPct"], abs=TOL)
            assert h.r.max_pct == pytest.approx(wh["r"]["maxPct"], abs=TOL)
            assert (h.r.te, h.r.ko) == (wh["r"]["te"], wh["r"]["ko"])
    for i, w in want["hp"].items():
        x = t.hp[int(i)]
        assert x.lo == pytest.approx(w["lo"], abs=TOL)
        assert x.hi == pytest.approx(w["hi"], abs=TOL)
        assert x.sash == w["sash"]


# ---------------------------------------------------------------- POST /api/calc/turn

@pytest_asyncio.fixture
async def client(session):
    from app.core.database import get_session
    from app.main import app

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_session, None)


FAST = {"nature": "Jolly", "evs": {"atk": 252, "spe": 252, "hp": 4}}


async def test_faster_pokemon_moves_first(client):
    r = await client.post("/api/calc/turn", json={"slots": [
        {"slot": 0, "pokemon_id": 445, "move": "Dragon Claw", **FAST},
        {"slot": 2, "pokemon_id": 823, "move": "Brave Bird"},
    ]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [o["slot"] for o in body["order"]] == [0, 2]
    assert body["steps"][0]["hits"][0]["target"] == 2
    assert body["steps"][0]["hits"][0]["min_pct"] > 0


async def test_spread_move_in_doubles_hits_both_foes_and_partner(client):
    r = await client.post("/api/calc/turn", json={"doubles": True, "slots": [
        {"slot": 0, "pokemon_id": 445, "move": "Earthquake"},
        {"slot": 1, "pokemon_id": 485, "move": "Flamethrower"},
        {"slot": 2, "pokemon_id": 748, "move": "Sludge Bomb"},
        {"slot": 3, "pokemon_id": 479, "move": "Thunderbolt"},
    ]})
    step = next(s for s in r.json()["steps"] if s["slot"] == 0)
    assert sorted((h["target"], h["friendly_fire"]) for h in step["hits"]) == [
        (1, True), (2, False), (3, False)]


async def test_focus_sash_saves_from_full_hp(client):
    r = await client.post("/api/calc/turn", json={"slots": [
        {"slot": 0, "pokemon_id": 445, "move": "Dragon Claw", "item": "Choice Band",
         "nature": "Adamant", "evs": {"atk": 252}},
        {"slot": 2, "pokemon_id": 373, "move": "Dragon Claw", "item": "Focus Sash"},
    ]})
    hits = [h for s in r.json()["steps"] for h in s["hits"] if h["target"] == 2]
    assert hits and hits[0]["sash"] and hits[0]["max_pct"] >= 100
    hp = next(x for x in r.json()["hp"] if x["slot"] == 2)
    assert hp["lo"] >= 1


async def test_unknown_move_or_pokemon_is_422(client):
    r = await client.post("/api/calc/turn", json={"slots": [
        {"slot": 0, "pokemon_id": 445, "move": "Not A Move"}]})
    assert r.status_code == 422 and "Slot 0" in r.json()["detail"]
    r = await client.post("/api/calc/turn", json={"slots": [{"slot": 2, "pokemon_id": 999999}]})
    assert r.status_code == 422 and "Slot 2" in r.json()["detail"]
