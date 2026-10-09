"""The backend team rating and profile reproduce what the website computed before they
moved server-side (pure, no DB).

Golden cases come from the old TypeScript (``frontend/lib/teamEval.ts`` rateTeam and
``frontend/lib/teamProfile.ts`` profileTeam), run over captured saved teams plus edge
cases. They are frozen: the TypeScript is gone, so these files are the record of the
old behaviour. The profile's keys were camelCase there and are snake_case here."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.schemas.analysis import TeamAnalysis
from app.schemas.team import TeamOut
from app.services.team_profile import profile_team
from app.services.team_rating import js_round, rate_team

FIX = Path(__file__).parent / "fixtures"
INPUTS = json.loads((FIX / "team_rating_inputs.json").read_text())
CASES = {c["label"]: c for c in json.loads((FIX / "team_rating_cases.json").read_text())["cases"]}
_prev = json.loads((FIX / "type_chart_previous.json").read_text())
CHART: dict[str, dict[str, float]] = _prev["chart"]


def _snake(obj):
    if isinstance(obj, dict):
        return {re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower(): _snake(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_snake(v) for v in obj]
    return obj


def _rate(inp: dict):
    team = TeamOut.model_validate(inp["team"])
    analysis = TeamAnalysis.model_validate(inp["analysis"])
    rating = rate_team(len(team.members), analysis, CHART)
    return team, analysis, rating


@pytest.mark.parametrize("inp", INPUTS, ids=[i["label"] for i in INPUTS])
def test_rating_matches_previous_client(inp: dict) -> None:
    _, _, rating = _rate(inp)
    got = rating.model_dump(exclude={"fast_speed"})
    assert got == CASES[inp["label"]]["rating"]


@pytest.mark.parametrize("inp", INPUTS, ids=[i["label"] for i in INPUTS])
def test_profile_matches_previous_client(inp: dict) -> None:
    team, analysis, rating = _rate(inp)
    profile = profile_team(team, analysis, rating)
    want = CASES[inp["label"]]["profile"]
    assert (profile.model_dump() if profile else None) == _snake(want)


def test_js_round_is_half_up() -> None:
    # Math.round, not Python's banker's rounding.
    assert [js_round(x) for x in (60.5, 61.5, 0.5, -0.5, 2.4999)] == [61, 62, 1, 0, 2]


def test_half_point_case_rounds_up() -> None:
    """The edge case's Sets score averages exactly 60.5; the old client showed 61."""
    inp = next(i for i in INPUTS if i["label"] == "edge:sets score on .5")
    _, _, rating = _rate(inp)
    sets = next(a for a in rating.areas if a.key == "sets")
    assert sets.score == 61


def test_partial_team_is_capped() -> None:
    inp = next(i for i in INPUTS if i["label"] == "edge:three members")
    _, _, rating = _rate(inp)
    assert rating.capped and rating.ceiling == 50
    assert len(rating.areas) == 6 and len(rating.cover) == 18 and len(rating.threats) == 18


def test_duplicate_species_counts_once() -> None:
    inp = next(i for i in INPUTS if i["label"] == "edge:duplicate species")
    _, _, rating = _rate(inp)
    roster = next(a for a in rating.areas if a.key == "roster")
    assert "Garchomp twice" in roster.headline
    assert roster.fix and roster.fix.startswith("Only one of each species")
