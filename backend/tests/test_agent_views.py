"""Every view kind round-trips through JSON, discriminated on ``kind``."""

from __future__ import annotations

import pytest

from app.agent.views import (
    VIEW_ADAPTER,
    VIEW_KINDS,
    LearnCheckView,
    LearnersView,
    LearnGroup,
    LearnMove,
    LearnsetView,
    MoveListView,
    MoveRow,
    PokemonCard,
    PokemonListView,
    RankingRow,
    RankingView,
    TypeChartView,
)

CARD = PokemonCard(ref=0, pokemon_id=6, name="Charizard", dex_number=6, types=["fire", "flying"],
                   stats={"hp": 78, "speed": 100}, total=534)
MOVE = MoveRow(ref=0, move_id=89, name="Earthquake", type="ground", damage_class="physical",
               power=100, accuracy=100, pp=10, learners=400)

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
]


def test_samples_cover_every_kind():
    assert sorted(v.kind for v in SAMPLES) == sorted(VIEW_KINDS)


@pytest.mark.parametrize("view", SAMPLES, ids=lambda v: v.kind)
def test_round_trip(view):
    dumped = view.model_dump(mode="json")
    back = VIEW_ADAPTER.validate_python(dumped)
    assert type(back) is type(view)
    assert back == view
