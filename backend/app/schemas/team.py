"""Schemas for teams and their configured slots.

Structural validation (types, ranges, list lengths, EV caps) lives here; the
*relational* validation that needs the DB — ability/nature/move legality for the
chosen species — lives in ``app.services.teams``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.models.team import MAX_EV_PER_STAT, MAX_EV_TOTAL, MAX_IV, MAX_MOVES, MAX_SLOTS
from app.services.stats import STAT_KEYS


def _validate_spread(spread: dict[str, int] | None, *, cap: int, total_cap: int | None) -> None:
    if spread is None:
        return
    for key, value in spread.items():
        if key not in STAT_KEYS:
            raise ValueError(f"Unknown stat '{key}'; expected one of {list(STAT_KEYS)}")
        if not (0 <= value <= cap):
            raise ValueError(f"{key} must be between 0 and {cap}")
    if total_cap is not None and sum(spread.values()) > total_cap:
        raise ValueError(f"EV total must not exceed {total_cap}")


class SlotBuild(BaseModel):
    """A set by name (moves, ability, nature, item, EVs) to apply to an existing slot."""

    moves: list[str] | None = None
    ability: str | None = None
    nature: str | None = None
    item: str | None = None
    evs: dict[str, int] | None = None


class SlotUpdate(BaseModel):
    """Set (upsert) one slot's configuration."""

    pokemon_id: int
    # An alternate form of ``pokemon_id`` (Mega, regional…); its typing/stats/abilities apply.
    form_id: int | None = None
    ability_id: int | None = None
    nature_id: int | None = None
    item_id: int | None = None
    ev_spread: dict[str, int] | None = None
    iv_spread: dict[str, int] | None = None
    move_ids: list[int] | None = None

    @field_validator("ev_spread")
    @classmethod
    def _check_ev(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        _validate_spread(v, cap=MAX_EV_PER_STAT, total_cap=MAX_EV_TOTAL)
        return v

    @field_validator("iv_spread")
    @classmethod
    def _check_iv(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        _validate_spread(v, cap=MAX_IV, total_cap=None)
        return v

    @field_validator("move_ids")
    @classmethod
    def _check_moves(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        if len(v) > MAX_MOVES:
            raise ValueError(f"A slot can hold at most {MAX_MOVES} moves")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate moves are not allowed in a slot")
        return v


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    kind: str = Field(default="player")
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("kind")
    @classmethod
    def _check_kind(cls, v: str) -> str:
        if v not in ("player", "opponent"):
            raise ValueError("kind must be 'player' or 'opponent'")
        return v


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    kind: str | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("kind")
    @classmethod
    def _check_kind(cls, v: str | None) -> str | None:
        if v is not None and v not in ("player", "opponent"):
            raise ValueError("kind must be 'player' or 'opponent'")
        return v


# --- output shapes ---


class SlotAbility(BaseModel):
    id: int
    name: str
    is_hidden: bool = False


class SlotNature(BaseModel):
    id: int
    name: str
    increased_stat: str | None = None
    decreased_stat: str | None = None


class SlotMove(BaseModel):
    move_id: int
    name: str
    type: str | None = None
    damage_class: str | None = None
    power: int | None = None
    accuracy: int | None = None
    priority: int = 0


class SlotItem(BaseModel):
    id: int
    name: str
    category: str | None = None
    short_effect: str | None = None


class TeamMemberOut(BaseModel):
    slot: int
    pokemon_id: int
    form_id: int | None = None
    dex_number: int
    name: str
    types: list[str]
    sprite_url: str
    base_stats: dict[str, int]
    final_stats: dict[str, int]
    ability: SlotAbility | None = None
    nature: SlotNature | None = None
    item: SlotItem | None = None
    ev_spread: dict[str, int]
    iv_spread: dict[str, int]
    moves: list[SlotMove]


class TeamOut(BaseModel):
    id: int
    name: str
    kind: str
    notes: str | None = None
    members: list[TeamMemberOut]


class TeamSummary(BaseModel):
    id: int
    name: str
    kind: str
    size: int
    sprites: list[str]


class TeamListResponse(BaseModel):
    teams: list[TeamSummary]


class CoachAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    opponent_id: int | None = None
    # The team report is built by the server (services/coach_report.py); a ``report``
    # sent by an old page is ignored.


MAX_SLOT = MAX_SLOTS
