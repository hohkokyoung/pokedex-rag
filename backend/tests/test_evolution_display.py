"""The backend's evolution labels reproduce what the website showed before they moved
server-side, for every distinct evolution stage in the data (pure, no DB).

Golden cases come from the old TypeScript (``frontend/lib/evolution.ts`` buildCondition)
and are frozen: the TypeScript is gone, so these files are the record of the old
behaviour."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.pokemon import EvolutionStage
from app.services.evolution_display import evolution_display

CASES = json.loads(
    (Path(__file__).parent / "fixtures" / "evolution_cases.json").read_text()
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["example"] for c in CASES])
def test_labels_match_previous_website(case: dict) -> None:
    stage = EvolutionStage(
        to_id=0,
        to_name="",
        trigger=case["trigger"],
        min_level=case["min_level"],
        item=case["item"],
        condition=case["condition"],
    )
    assert evolution_display(stage).model_dump() == case["display"]


async def test_detail_response_carries_labels(session) -> None:
    from app.services import pokemon_query

    def by_to(detail, name):
        return next(s for s in detail.evolution_stages if s.to_name == name).display

    bulba = await pokemon_query.get_pokemon(session, "1")
    ivy = by_to(bulba, "Ivysaur")
    assert [(c.label, c.tone) for c in ivy.chips] == [("Lv. 16", "solid")]
    assert ivy.description is None

    eevee = await pokemon_query.get_pokemon(session, "133")
    espeon = by_to(eevee, "Espeon")
    assert [(c.label, c.tone) for c in espeon.chips] == [("Friendship", "solid"), ("Day", "soft")]
    assert espeon.description and espeon.description.count("160") == 1
    assert [c.label for c in by_to(eevee, "Vaporeon").chips] == ["Water Stone"]

    abra = await pokemon_query.get_pokemon(session, "63")
    trade = by_to(abra, "Alakazam")
    assert trade.chips[0].label == "Trade" and "Linking Cord" in trade.description
    # Form chains are labelled too.
    assert all(s.display for f in eevee.forms for s in f.evolution_stages)
