"""The damage calculator's state, as the calc coach receives it with each question."""

from __future__ import annotations

from typing import Literal

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


class CalcTurnRequest(BaseModel):
    """The calculator's state, to play one turn (``POST /api/calc/turn``)."""

    level: int = Field(100, ge=1, le=100)
    doubles: bool = False
    field: CalcField = Field(default_factory=CalcField)
    slots: list[CalcSlot] = Field(default_factory=list, max_length=4)


class CalcHitOut(BaseModel):
    """One hit of the turn: the damage range and how it ended."""

    attacker: int
    target: int
    move: str
    min_pct: float  # % of max HP, lowest roll
    max_pct: float
    ko_hits: int  # hits to KO from the target's HP going in (0 = no damage)
    te: float  # type effectiveness
    stab: float
    attack: int  # the attacking and defending stats used
    defense: int
    base: int  # base damage before the random roll
    mod: float  # the other modifiers multiplied
    ko: Literal["yes", "maybe"] | None  # faints on every roll / on high rolls
    sash: bool  # Focus Sash left it at 1 HP
    friendly_fire: bool  # hits its own side


class CalcStepOut(BaseModel):
    slot: int
    skipped: bool  # fainted before it could move
    at_risk: bool  # moves only if it survived high rolls
    hits: list[CalcHitOut]


class CalcOrderOut(BaseModel):
    slot: int
    priority: int
    speed: int


class CalcHpOut(BaseModel):
    slot: int
    lo: float  # HP % left if every roll is high
    hi: float  # … if every roll is low
    sash: bool


class CalcMoveOut(BaseModel):
    slot: int
    name: str
    type: str
    damage_class: str
    power: int
    target: str | None
    priority: int


class CalcTurnOut(BaseModel):
    order: list[CalcOrderOut]  # who moves first
    steps: list[CalcStepOut]  # in that order
    hp: list[CalcHpOut]  # after the turn, per active slot
    aims: dict[int, int | None]  # the foe each active slot's single-target move aims at
    moves: list[CalcMoveOut]  # each slot's move as the server read it


class CalcOptionOut(BaseModel):
    name: str
    side: Literal["a", "d"]  # works when attacking / defending
    note: str


class CalcOptionsOut(BaseModel):
    """What the damage maths models, for the calculator's pickers."""

    items: list[CalcOptionOut]
    abilities: list[CalcOptionOut]
    weathers: list[str]
    terrains: list[str]
    natures: list[str]
