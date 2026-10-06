"""Typed result views: what a tool's result looks like, for the UI to draw directly.

A view is built from the tool's own data (never from the LLM answer). Every row or
card carries ``ref``, the step-local index of the evidence chunk it came from; the
client maps it to the global ``[n]`` citation via the sources' ``step``/``step_index``.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from app.rag.build_suggest import BuildSuggestion
from app.schemas.analysis import DuelOut
from app.schemas.recommend import Candidate


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
    level: int | None = None  # any game: the newest game's level
    level_note: str | None = None  # "Lv 1 in SwSh/BDSP; Lv 51–52 in other games" when it varies


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
    method: str | None = None  # only this learn method was asked for
    rows: list[PokemonCard]
    chunk_refs: list[int] = Field(default_factory=list)


class LearnCheckView(BaseModel):
    """Can this Pokémon learn this move? Yes (with how) or no."""

    kind: Literal["learn_check"] = "learn_check"
    pokemon: PokemonCard
    move: MoveRow
    ok: bool
    how: str | None = None  # "by level-up at Lv 1"
    method: str | None = None  # only this learn method was asked for
    game: str | None = None
    absent: bool = False  # the Pokémon isn't in that game at all
    chunk_refs: list[int] = Field(default_factory=list)


# ---- team coach views -------------------------------------------------------------


class SlotRef(BaseModel):
    slot: int
    name: str


class CandidatesView(BaseModel):
    """Pokémon the coach suggests adding; each card adds only when clicked."""

    kind: Literal["candidates"] = "candidates"
    team_id: int
    candidates: list[Candidate]
    team_full: bool = False
    members: list[SlotRef] = Field(default_factory=list)  # for the Replace picker
    chunk_refs: list[int] = Field(default_factory=list)


class BuildSet(BaseModel):
    moves: list[str] = Field(default_factory=list)
    ability: str | None = None
    nature: str | None = None
    item: str | None = None
    evs: dict[str, int] = Field(default_factory=dict)  # hp/atk/def/spa/spd/spe


class SetEditView(BaseModel):
    """A proposed set for one member, shown was → now; saved only on Apply."""

    kind: Literal["set_edit"] = "set_edit"
    side: Literal["ours", "theirs"]
    team_id: int
    slot: int
    name: str
    sprite_url: str = ""
    before: BuildSet
    after: BuildSet
    why: str = ""
    # Only the fields that change, in the slot editor's apply shape.
    fields: dict = Field(default_factory=dict)
    # The member as it was (ids included), so Revert can restore it exactly.
    member: dict = Field(default_factory=dict)
    chunk_refs: list[int] = Field(default_factory=list)


class MemberAddedView(BaseModel):
    """An explicit "add X": what was added where (Undo clears the slot), or why not."""

    kind: Literal["member_added"] = "member_added"
    team_id: int
    added: bool
    slot: int | None = None
    card: PokemonCard
    message: str
    chunk_refs: list[int] = Field(default_factory=list)


class DuelView(BaseModel):
    """One pairing played out turn by turn by the deterministic duel engine."""

    kind: Literal["duel"] = "duel"
    team_id: int
    opponent_id: int
    duel: DuelOut
    chunk_refs: list[int] = Field(default_factory=list)


# ---- calc coach views ---------------------------------------------------------------


class CalcRef(BaseModel):
    slot: int
    name: str
    side: int  # 0 = the user's, 1 = the opponent's
    dex_number: int | None = None


class HitRange(BaseModel):
    min_pct: float
    max_pct: float
    ko: int  # hits to KO from current HP (0 = no damage)
    te: float = 1
    ko_text: str = ""


class CalcApply(BaseModel):
    """Calculator fields to set on one slot when the user clicks Apply."""

    slot: int
    fields: dict  # item / ability / nature / evs (full spread)


class DamageView(BaseModel):
    kind: Literal["damage"] = "damage"
    attacker: CalcRef
    defender: CalcRef
    move: MoveRow
    current: HitRange
    whatif: HitRange | None = None
    changes: list[dict] = Field(default_factory=list)
    apply: list[CalcApply] = Field(default_factory=list)
    chunk_refs: list[int] = Field(default_factory=list)


class SurviveView(BaseModel):
    kind: Literal["survive"] = "survive"
    defender: CalcRef
    attacker: CalcRef
    move: MoveRow
    survives: bool
    stat: Literal["def", "spd"]
    hp_ev: int
    stat_ev: int
    nature: str
    nature_changed: bool
    range: HitRange
    current: HitRange
    apply: CalcApply | None = None
    already: bool = False  # the current set already survives: nothing to apply
    chunk_refs: list[int] = Field(default_factory=list)


class BuildProposalView(BaseModel):
    kind: Literal["build_proposal"] = "build_proposal"
    slot: int
    pokemon: str
    build: BuildSuggestion
    chunk_refs: list[int] = Field(default_factory=list)


View = Annotated[
    RankingView
    | PokemonListView
    | TypeChartView
    | MoveListView
    | LearnsetView
    | LearnersView
    | LearnCheckView
    | CandidatesView
    | SetEditView
    | MemberAddedView
    | DuelView
    | DamageView
    | SurviveView
    | BuildProposalView,
    Field(discriminator="kind"),
]

VIEW_ADAPTER: TypeAdapter[View] = TypeAdapter(View)

VIEW_KINDS = (
    "ranking", "pokemon_list", "type_chart", "move_list", "learnset", "learners", "learn_check",
    "candidates", "set_edit", "member_added", "duel", "damage", "survive", "build_proposal",
)
