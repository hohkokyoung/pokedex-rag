"""Catch odds match what the website's ``lib/catchRate.ts`` computed (golden cases)."""

import json
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from app.services.catch_rate import CatchMon, Situation, rank

FIX = Path(__file__).parent / "fixtures"
MONS = {m["id"]: m for m in json.loads((FIX / "catch_inputs.json").read_text())}
CASES = json.loads((FIX / "catch_cases.json").read_text())
CTX_KEYS = {"hpPct": "hp_pct", "level": "level", "myLevel": "my_level", "turn": "turn",
            "status": "status", "night": "night", "water": "water", "caught": "caught",
            "loveMatch": "love_match", "dexCaught": "dex_caught", "charm": "charm"}
TERMS = {"max_hp", "hp", "rate", "hp_factor", "ball", "status", "low_level", "a", "shake", "crit"}


def mon(pid: int) -> CatchMon:
    m = MONS[pid]
    return CatchMon(dex=m["dex"], types=m["types"], capture_rate=m["captureRate"],
                    base_hp=m["baseHp"], base_speed=m["baseSpeed"], weight_kg=m["weightKg"],
                    gender_rate=m["genderRate"])


@pytest.mark.parametrize("case", CASES, ids=[c["label"] for c in CASES])
def test_matches_the_website(case):
    ctx = Situation(**{CTX_KEYS[k]: v for k, v in case["ctx"].items()})
    got = rank(mon(case["pokemon_id"]), ctx)
    assert [b.id for b in got] == [b["id"] for b in case["balls"]]
    for g, want in zip(got, case["balls"], strict=True):
        assert (g.name, g.why, g.throws, g.sure) == (
            want["name"], want["why"], want["throws"], want["sure"])
        assert g.p == pytest.approx(want["p"], rel=1e-12, abs=1e-15)
        for k in TERMS:
            assert getattr(g.terms, k) == pytest.approx(want["terms"][k], rel=1e-12, abs=1e-15), k


# ---------------------------------------------------------------- the endpoint

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


async def test_quick_ball_leads_on_turn_one(client):
    r = await client.get("/api/pokemon/445/catch")
    assert r.status_code == 200
    body = r.json()
    assert body["capture_rate"] == 45
    ids = [b["id"] for b in body["balls"]]
    assert ids[0] == "master" and ids.index("quick") < ids.index("ultra")
    quick = next(b for b in body["balls"] if b["id"] == "quick")
    assert quick["terms"]["ball"] == 5 and quick["why"] == "first turn ×5"


async def test_sleep_at_one_percent_beats_full_hp(client):
    full = (await client.get("/api/pokemon/445/catch")).json()["balls"]
    low = (await client.get("/api/pokemon/445/catch?status=sleep&hp_pct=1")).json()["balls"]
    p = {b["id"]: b["p"] for b in full}
    assert all(b["p"] > p[b["id"]] for b in low if not b["sure"])


async def test_unknown_pokemon_and_bad_input(client):
    assert (await client.get("/api/pokemon/999999/catch")).status_code == 404
    assert (await client.get("/api/pokemon/445/catch?level=0")).status_code == 422
    assert (await client.get("/api/pokemon/445/catch?hp_pct=101")).status_code == 422
    assert (await client.get("/api/pokemon/445/catch?status=confused")).status_code == 422


async def test_endpoint_matches_a_golden_case(client):
    case = next(c for c in CASES if c["label"] == "garchomp-tile-default")
    body = (await client.get("/api/pokemon/445/catch?hp_pct=25&level=55")).json()
    assert [b["id"] for b in body["balls"]] == [b["id"] for b in case["balls"]]
    assert body["balls"][1]["p"] == pytest.approx(case["balls"][1]["p"], rel=1e-12)
