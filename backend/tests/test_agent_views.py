"""Every view kind round-trips through JSON, discriminated on ``kind``."""

from __future__ import annotations

import pytest

from app.agent.views import (
    VIEW_ADAPTER,
    VIEW_KINDS,
    BuildProposalView,
    BuildSet,
    CalcApply,
    CalcRef,
    CandidatesView,
    DamageView,
    DuelView,
    HitRange,
    LearnCheckView,
    LearnersView,
    LearnGroup,
    LearnMove,
    LearnsetView,
    MemberAddedView,
    MoveListView,
    MoveRow,
    PokemonCard,
    PokemonListView,
    RankingRow,
    RankingView,
    SetEditView,
    SlotRef,
    SurviveView,
    TypeChartView,
)
from app.rag.build_suggest import BuildSuggestion
from app.schemas.analysis import DuelOut
from app.schemas.recommend import Candidate

CARD = PokemonCard(ref=0, pokemon_id=6, name="Charizard", dex_number=6, types=["fire", "flying"],
                   stats={"hp": 78, "speed": 100}, total=534)
MOVE = MoveRow(ref=0, move_id=89, name="Earthquake", type="ground", damage_class="physical",
               power=100, accuracy=100, pp=10, learners=400)
GAR = CalcRef(slot=0, name="Garchomp", side=0, dex_number=445)
HEA = CalcRef(slot=2, name="Heatran", side=1, dex_number=485)
RANGE = HitRange(min_pct=80.5, max_pct=95.2, ko=2, te=1, ko_text="a guaranteed 2HKO")

SAMPLES = [
    RankingView(stat="speed", total=12, rows=[RankingRow(**CARD.model_dump(), value=100)],
                chunk_refs=[0]),
    PokemonListView(cards=[CARD], chunk_refs=[0]),
    TypeChartView(types=["fire"], weak_2x=["water", "ground", "rock"], chunk_refs=[0]),
    MoveListView(moves=[MOVE], chunk_refs=[0]),
    LearnsetView(pokemon=CARD, groups=[LearnGroup(ref=1, method="machine", label="TM", moves=[
        LearnMove(name="Earthquake", type="ground", damage_class="physical", power=100)])]),
    LearnersView(move=MOVE, total=400, by_method={"machine": 380}, rows=[CARD]),
    LearnCheckView(pokemon=CARD, move=MOVE, ok=True, how="by TM"),
    CandidatesView(team_id=1, candidates=[Candidate(
        pokemon_id=445, dex_number=445, name="Garchomp", types=["dragon", "ground"],
        sprite_url="/s.png", role="sweeper", base_stats={"speed": 102}, reason="fast")],
        team_full=False, members=[SlotRef(slot=1, name="Charizard")]),
    SetEditView(side="ours", team_id=1, slot=1, name="Charizard",
                before=BuildSet(moves=["Ember"]), after=BuildSet(moves=["Flamethrower"]),
                why="stronger", fields={"moves": ["Flamethrower"]}, member={"slot": 1}),
    MemberAddedView(team_id=1, added=True, slot=4, card=CARD, message="Added"),
    DuelView(team_id=1, opponent_id=2, duel=DuelOut(
        our_slot=1, their_slot=1, our_name="A", their_name="B", outcome="win", first="ours")),
    DamageView(attacker=GAR, defender=HEA, move=MOVE, current=RANGE, whatif=RANGE,
               changes=[{"who": "attacker", "key": "item", "value": "Choice Band"}],
               apply=[CalcApply(slot=0, fields={"item": "Choice Band"})]),
    SurviveView(defender=HEA, attacker=GAR, move=MOVE, survives=True, stat="def", hp_ev=252,
                stat_ev=44, nature="Bold", nature_changed=True, range=RANGE, current=RANGE,
                apply=CalcApply(slot=2, fields={"evs": {"hp": 252, "def": 44}})),
    BuildProposalView(slot=0, pokemon="Garchomp", build=BuildSuggestion(
        pokemon="Garchomp", moves=["Earthquake"], evs={"atk": 252}, why="fast")),
]


def test_samples_cover_every_kind():
    assert sorted(v.kind for v in SAMPLES) == sorted(VIEW_KINDS)


@pytest.mark.parametrize("view", SAMPLES, ids=lambda v: v.kind)
def test_round_trip(view):
    dumped = view.model_dump(mode="json")
    back = VIEW_ADAPTER.validate_python(dumped)
    assert type(back) is type(view)
    assert back == view
