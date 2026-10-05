"""Typed result views: what a tool's result looks like, for the UI to draw directly.

A view is built from the tool's own data (never from the LLM answer). Every row or
card carries ``ref``, the step-local index of the evidence chunk it came from; the
client maps it to the global ``[n]`` citation via the sources' ``step``/``step_index``.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter


class PokemonCard(BaseModel):
    """One Pokémon as evidence: art, types, stats, and whatever the step adds."""

    ref: int | None = None
    pokemon_id: int | None = None
    name: str
    dex_number: int | None = None
    types: list[str] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)  # hp … speed
    total: int | None = None
    entry: str | None = None  # a dex quote
    match: float | None = None  # similarity in [0, 1]
    coverage: list[dict[str, str]] = Field(default_factory=list)  # [{move, type}]
    via: str | None = None  # how it fits, e.g. "Learns Earthquake by TM"


class RankingRow(PokemonCard):
    value: float | None = None  # the ranked stat


class RankingView(BaseModel):
    kind: Literal["ranking"] = "ranking"
    stat: str  # a StructuredQuery stat name, e.g. "speed"
    order: Literal["asc", "desc"] = "desc"
    total: int  # how many match, ignoring the limit
    rows: list[RankingRow]
    chunk_refs: list[int] = Field(default_factory=list)


class PokemonListView(BaseModel):
    kind: Literal["pokemon_list"] = "pokemon_list"
    title: str | None = None
    cards: list[PokemonCard]
    chunk_refs: list[int] = Field(default_factory=list)


class TypeChartView(BaseModel):
    """How one type (or a dual typing) fares defensively."""

    kind: Literal["type_chart"] = "type_chart"
    types: list[str]
    weak_4x: list[str] = Field(default_factory=list)
    weak_2x: list[str] = Field(default_factory=list)
    resist_half: list[str] = Field(default_factory=list)
    resist_quarter: list[str] = Field(default_factory=list)
    immune: list[str] = Field(default_factory=list)
    # Offence, for a single type: the types its moves hit super-effectively.
    strong_against: list[str] = Field(default_factory=list)
    chunk_refs: list[int] = Field(default_factory=list)


class MoveRow(BaseModel):
    ref: int | None = None
    move_id: int | None = None
    name: str
    type: str
    damage_class: str | None = None
    power: int | None = None
    accuracy: int | None = None
    pp: int | None = None
    learners: int | None = None
    effect: str | None = None


class MoveListView(BaseModel):
    kind: Literal["move_list"] = "move_list"
    moves: list[MoveRow]
    chunk_refs: list[int] = Field(default_factory=list)


class LearnMove(BaseModel):
    name: str
    type: str
    damage_class: str | None = None
    power: int | None = None
    level: int | None = None


class LearnGroup(BaseModel):
    ref: int | None = None
    method: str  # level-up | machine | tutor | egg | …
    label: str  # "level-up", "TM", …
    moves: list[LearnMove]


class LearnsetView(BaseModel):
    """A Pokémon's moves, grouped by how it learns them."""

    kind: Literal["learnset"] = "learnset"
    pokemon: PokemonCard
    game: str | None = None
    groups: list[LearnGroup]
    chunk_refs: list[int] = Field(default_factory=list)


class LearnersView(BaseModel):
    """Who learns a move: how many, by which method, and the standout users."""

    kind: Literal["learners"] = "learners"
    move: MoveRow
    total: int
    by_method: dict[str, int] = Field(default_factory=dict)
    scope: list[str] = Field(default_factory=list)  # e.g. ["Fire-type", "non-legendary"]
    game: str | None = None
    rows: list[PokemonCard]
    chunk_refs: list[int] = Field(default_factory=list)


class LearnCheckView(BaseModel):
    """Can this Pokémon learn this move? Yes (with how) or no."""

    kind: Literal["learn_check"] = "learn_check"
    pokemon: PokemonCard
    move: MoveRow
    ok: bool
    how: str | None = None  # "by level-up at Lv 1"
    game: str | None = None
    chunk_refs: list[int] = Field(default_factory=list)


View = Annotated[
    RankingView
    | PokemonListView
    | TypeChartView
    | MoveListView
    | LearnsetView
    | LearnersView
    | LearnCheckView,
    Field(discriminator="kind"),
]

VIEW_ADAPTER: TypeAdapter[View] = TypeAdapter(View)

VIEW_KINDS = (
    "ranking", "pokemon_list", "type_chart", "move_list", "learnset", "learners", "learn_check",
)
