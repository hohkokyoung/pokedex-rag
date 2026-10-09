"""The served type chart: the 18 battle types in display order, every pair, and equal
to the chart the website hard-coded before it moved server-side (DB-backed)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.services import matchups

PREVIOUS = json.loads((Path(__file__).parent / "fixtures" / "type_chart_previous.json").read_text())


async def test_chart_matches_previous_client_chart(session) -> None:
    chart = await matchups.type_chart(session)
    assert list(chart) == PREVIOUS["order"]
    diffs = [
        (a, d, chart[a][d], PREVIOUS["chart"][a][d])
        for a in PREVIOUS["order"]
        for d in PREVIOUS["order"]
        if chart[a][d] != PREVIOUS["chart"][a][d]
    ]
    assert diffs == [], f"{len(diffs)} of 324 multipliers differ"


async def test_chart_endpoint(session) -> None:
    from app.core.database import get_session
    from app.main import app

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t"
        ) as c:
            resp = await c.get("/api/types/chart")
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert resp.status_code == 200
    body = resp.json()
    assert body["order"] == matchups.ATTACK_ORDER and len(body["order"]) == 18
    chart = body["chart"]
    assert all(len(row) == 18 for row in chart.values())
    assert chart["ground"]["flying"] == 0
    assert chart["water"]["fire"] == 2
    assert chart["fire"]["water"] == 0.5
    assert chart["normal"]["normal"] == 1
    assert {v for row in chart.values() for v in row.values()} <= {0, 0.5, 1, 2}
    # Non-battle types in the ingested data (e.g. "unknown", "shadow", "stellar") stay out.
    assert not set(chart) - set(matchups.ATTACK_ORDER)


def test_damage_calc_chart_matches_previous_client_chart() -> None:
    """The damage calc keeps its own copy (self-contained, like the TS formula); it must
    agree with the chart the pages read."""
    from app.services.damage_calc import type_eff

    order = PREVIOUS["order"]
    assert [
        (a, d) for a in order for d in order if type_eff(a, d) != PREVIOUS["chart"][a][d]
    ] == []
