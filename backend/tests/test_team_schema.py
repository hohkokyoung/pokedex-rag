"""Unit tests for slot payload validation (pure Pydantic, no DB)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.team import SlotUpdate, TeamCreate


def test_valid_slot() -> None:
    s = SlotUpdate(
        pokemon_id=6,
        ev_spread={"speed": 252, "sp_attack": 252, "hp": 4},
        iv_spread={"attack": 0},
        move_ids=[85, 86, 53, 76],
    )
    assert s.pokemon_id == 6


def test_ev_per_stat_cap() -> None:
    with pytest.raises(ValidationError):
        SlotUpdate(pokemon_id=6, ev_spread={"speed": 253})


def test_ev_total_cap() -> None:
    with pytest.raises(ValidationError):
        SlotUpdate(pokemon_id=6, ev_spread={"hp": 252, "attack": 252, "defense": 252})


def test_iv_bounds() -> None:
    with pytest.raises(ValidationError):
        SlotUpdate(pokemon_id=6, iv_spread={"speed": 32})


def test_unknown_stat_rejected() -> None:
    with pytest.raises(ValidationError):
        SlotUpdate(pokemon_id=6, ev_spread={"luck": 4})


def test_too_many_moves() -> None:
    with pytest.raises(ValidationError):
        SlotUpdate(pokemon_id=6, move_ids=[1, 2, 3, 4, 5])


def test_duplicate_moves_rejected() -> None:
    with pytest.raises(ValidationError):
        SlotUpdate(pokemon_id=6, move_ids=[1, 1])


def test_team_kind_validation() -> None:
    TeamCreate(name="Squad", kind="opponent")
    with pytest.raises(ValidationError):
        TeamCreate(name="Squad", kind="enemy")
