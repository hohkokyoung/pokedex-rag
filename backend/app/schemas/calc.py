"""The damage calculator's state, as the calc coach receives it with each question."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.rag.build_suggest import BuildSuggestion, CoachTurn

_EV0 = {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
_IV31 = {"hp": 31, "atk": 31, "def": 31, "spa": 31, "spd": 31, "spe": 31}


class CalcField(BaseModel):
    weather: str = "None"
    terrain: str = "None"
    reflect: bool = False
    lightscreen: bool = False
    crit: bool = False
    burn: bool = False
    friend_guard: bool = False


class CalcSlot(BaseModel):
    """One filled calculator slot: 0–1 are the user's side, 2–3 the opponent's."""

    slot: int = Field(ge=0, le=3)
    pokemon_id: int  # the species (for a form, its base species)
    form_id: int | None = None
    name: str = ""
    nature: str = "Hardy"
    evs: dict[str, int] = Field(default_factory=lambda: dict(_EV0))
    ivs: dict[str, int] = Field(default_factory=lambda: dict(_IV31))
    item: str = "None"
    ability: str = "None"
    hp: float = Field(100, ge=0, le=100)
    move: str | None = None
    aim: int | None = None


class CalcHitIn(BaseModel):
    """A hit the calculator currently shows (its own turn result, used as-is)."""

    attacker: int
    target: int
    move: str
    min_pct: float
    max_pct: float
    ko: int = 0
    te: float = 1


class CalcProposal(BaseModel):
    slot: int
    build: BuildSuggestion
    thread: list[CoachTurn] = Field(default_factory=list)


class CalcAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    level: int = Field(100, ge=1, le=100)
    doubles: bool = False
    field: CalcField = Field(default_factory=CalcField)
    slots: list[CalcSlot] = Field(default_factory=list, max_length=4)
    focus: int = 0
    hits: list[CalcHitIn] = Field(default_factory=list, max_length=16)
    proposal: CalcProposal | None = None
