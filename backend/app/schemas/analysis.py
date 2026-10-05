"""Structured team-analysis report — consumed by the coach endpoint and the UI."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class MemberDefense(BaseModel):
    slot: int
    name: str
    types: list[str]
    # attacking type -> damage multiplier against this member
    multipliers: dict[str, float]
    weak_to: list[str]  # multipliers > 1


class SharedWeakness(BaseModel):
    type: str
    count: int
    members: list[str]


class DefensiveProfile(BaseModel):
    matrix: list[MemberDefense]
    shared_weaknesses: list[SharedWeakness]


class OffensiveProfile(BaseModel):
    coverage_types: list[str]
    used_move_coverage: bool  # True = at least one damaging move is set on a slot
    uncovered_types: list[str]  # can't hit at least neutrally
    not_super_effective: list[str]  # nothing on the team hits these super-effectively
    # Coverage types that come only from learnset moves suggested for open slots.
    from_learnset: list[str] = []
    tips: list[str] = []  # "Blaziken can learn Thunder Punch to hit Water super-effectively"


class MemberRole(BaseModel):
    slot: int
    name: str
    role: str
    speed: int
    offense: int
    bulk: int
    bst: int
    # Base Speed after the held item / ability (Choice Scarf ×1.5, Speed Boost…).
    eff_speed: int | None = None
    speed_note: str | None = None


class RoleProfile(BaseModel):
    members: list[MemberRole]
    missing_roles: list[str]
    notes: list[str]


class SuggestedMove(BaseModel):
    name: str
    type: str | None = None
    damage_class: str | None = None
    power: int | None = None
    is_set: bool  # already on the slot (else suggested from the learnset)


class SlotSuggestion(BaseModel):
    slot: int
    name: str
    recommended_ability: str | None = None
    ability_reason: str | None = None
    recommended_nature: str | None = None
    recommended_evs: dict[str, int]
    rationale: str
    recommended_moves: list[SuggestedMove] = []


class OpponentThreat(BaseModel):
    opponent_name: str
    opponent_types: list[str]
    threatens: list[str]  # our members
    via: list[str]  # opponent STAB types that are super-effective


class PressurePoint(BaseModel):
    """One of *our* members and the opponents it hits super-effectively."""

    attacker: str
    attacker_types: list[str]
    targets: list[str]  # opponent members
    via: list[str]  # our attacking types that are super-effective


class VsMember(BaseModel):
    slot: int
    pokemon_id: int
    name: str
    types: list[str]
    sprite_url: str
    speed: int  # final (EV/IV/nature-adjusted) Speed
    bst: int
    role: str


class MatchupCell(BaseModel):
    """One-on-one read of our member vs an opponent member, from each side's best move."""

    our_slot: int
    their_slot: int
    our_hit: float  # type multiplier of our best move on them
    our_hit_type: str | None = None
    our_move: str | None = None
    our_move_learned: bool = False  # suggested from the learnset, not on the slot yet
    our_pct: float = 0  # % of their HP per hit (average roll)
    our_hko: int = 99  # hits to KO
    their_hit: float
    their_hit_type: str | None = None
    their_move: str | None = None
    their_move_learned: bool = False
    their_pct: float = 0
    their_hko: int = 99
    faster: Literal["ours", "theirs", "tie"]  # who moves first (priority, then Speed)
    score: float  # >0 favours us
    outcome: Literal["win", "lose", "even"]
    our_setup: str | None = None  # setup move used first when that's the better plan
    their_setup: str | None = None
    notes: list[str] = []  # items/abilities/setup that shaped this pairing


class ScoreRow(BaseModel):
    key: str
    label: str
    ours: float
    theirs: float
    ours_label: str
    theirs_label: str
    share: float  # our share of this category, 0..1
    weight: float
    edge: Literal["ours", "theirs", "even"]


class Verdict(BaseModel):
    score: int  # 0..100, our weighted share
    label: str
    edge: Literal["ours", "theirs", "even"]
    reason: str


class VsOpponent(BaseModel):
    opponent_id: int
    opponent_name: str
    threats: list[OpponentThreat]
    advice: list[str]
    our_pressure: list[PressurePoint] = []
    our_members: list[VsMember] = []
    their_members: list[VsMember] = []
    cells: list[MatchupCell] = []
    scorecard: list[ScoreRow] = []
    verdict: Verdict | None = None


class DuelEvent(BaseModel):
    """One step of a played-out one-on-one (side "a" = our member, "b" = theirs)."""

    turn: int
    side: Literal["a", "b"]
    kind: str  # intimidate | setup | attack | sash | recoil | heal | speed-boost | faint | nothing
    move: str | None = None
    type: str | None = None
    mult: float | None = None
    pct: float | None = None  # damage / heal / recoil, % of max HP
    hp: float | None = None  # HP % left on the affected Pokémon afterwards
    item: str | None = None
    ability: str | None = None
    boosts: dict[str, int] | None = None


class DuelOut(BaseModel):
    our_slot: int
    their_slot: int
    our_name: str
    their_name: str
    outcome: Literal["win", "lose", "even"]
    first: Literal["ours", "theirs", "tie"]
    our_setup: str | None = None
    their_setup: str | None = None
    our_moves: list[str] = []  # the moveset the engine used (set + learnset fill)
    their_moves: list[str] = []
    our_moves_learned: list[str] = []  # of those, the ones not set on the slot
    their_moves_learned: list[str] = []
    notes: list[str] = []
    log: list[DuelEvent] = []


class SetMember(BaseModel):
    """What a member's set adds beyond species + typing."""

    slot: int
    name: str
    ability: str | None = None
    ability_note: str | None = None  # modelled effect, when we model it
    item: str | None = None
    item_note: str | None = None
    moves_set: int = 0
    setup: list[str] = []
    priority: list[str] = []
    recovery: list[str] = []
    support: list[str] = []
    score: int = 0  # 0–100 build completeness/impact


class SetProfile(BaseModel):
    members: list[SetMember]


class TeamAnalysis(BaseModel):
    team_id: int
    name: str
    size: int
    defensive: DefensiveProfile
    offensive: OffensiveProfile
    roles: RoleProfile
    suggestions: list[SlotSuggestion]
    vs_opponent: VsOpponent | None = None
    sets: SetProfile | None = None
    summary: list[str]  # top-line "what to improve" bullets
