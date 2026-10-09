"""The coach's team report matches what the website's ``reportFacts`` wrote, byte for byte."""

import json
from pathlib import Path

import pytest

from app.schemas.analysis import TeamRating, VsOpponent
from app.schemas.team import TeamOut
from app.services.coach_report import report_facts

FIX = Path(__file__).parent / "fixtures"
INPUTS = {c["label"]: c for c in json.loads((FIX / "coach_report_inputs.json").read_text())}
CASES = json.loads((FIX / "coach_report_cases.json").read_text())


def _maybe(model, data):
    return model.model_validate(data) if data is not None else None


@pytest.mark.parametrize("case", CASES, ids=[c["label"] for c in CASES])
def test_report_matches_the_website(case):
    i = INPUTS[case["label"]]
    team = TeamOut.model_validate(i["team"])
    opponent = _maybe(TeamOut, i["opponent"])
    got = report_facts(
        team,
        _maybe(TeamRating, i["rating"]) if team.members else None,
        opponent,
        _maybe(TeamRating, i["opponent_rating"]) if opponent and opponent.members else None,
        _maybe(VsOpponent, i["vs"]),
    )
    assert got == case["report"]


def test_an_empty_opponent_adds_no_matchup_lines():
    i = INPUTS["garchomp-vs-empty"]
    got = report_facts(TeamOut.model_validate(i["team"]), TeamRating.model_validate(i["rating"]),
                       TeamOut.model_validate(i["opponent"]), None,
                       VsOpponent.model_validate(i["vs"]))
    assert "Matchup" not in got and "Best lead" not in got and "Opponent" not in got
