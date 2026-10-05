"""Schemas for the team-builder lookup endpoints (legal moves, abilities, natures)."""

from __future__ import annotations

from pydantic import BaseModel


class LearnsetMoveOut(BaseModel):
    move_id: int
    identifier: str
    name: str
    type: str | None = None
    damage_class: str | None = None  # physical | special | status
    power: int | None = None
    pp: int | None = None
    accuracy: int | None = None
    short_effect: str | None = None
    # Doubles targeting (PokéAPI move_targets identifier), e.g. 'all-other-pokemon'.
    target: str | None = None
    # Turn-order bracket: +1 Quick Attack, +3 Fake Out, 0 normal, −6 Roar …
    priority: int = 0
    learn_method: str | None = None
    level: int | None = None


class ZUserOut(BaseModel):
    id: int
    dex_number: int
    name: str
    sprite_url: str
    form_id: int | None = None


class SignatureZOut(BaseModel):
    """Who can use a signature Z-Move: holding ``crystal``, ``base_move`` becomes it."""

    crystal: str
    base_move: str
    users: list[ZUserOut]


class MoveOut(BaseModel):
    """A move independent of any species (global lookup)."""

    id: int
    identifier: str
    name: str
    type: str | None = None
    damage_class: str | None = None  # physical | special | status
    power: int | None = None
    pp: int | None = None
    accuracy: int | None = None
    priority: int = 0
    short_effect: str | None = None
    signature_z: SignatureZOut | None = None


class MoveLearnerOut(BaseModel):
    """A species that can legally learn a given move (reverse learnset)."""

    id: int
    dex_number: int
    name: str
    types: list[str]
    sprite_url: str
    learn_method: str | None = None
    level: int | None = None
    # Set when only an alternate form learns it (Black Kyurem's Freeze Shock).
    form_id: int | None = None


class LearnMethodOut(BaseModel):
    method: str  # level-up | machine | egg | tutor | …
    level: int | None = None  # level-up only; 0 = learned on evolution
    # Any-game view: the highest level across games (``level`` is the lowest).
    level_max: int | None = None


class GameLearnerOut(BaseModel):
    """A Pokémon (or alternate form) that learns a move in one game, and how."""

    id: int
    dex_number: int
    name: str
    types: list[str]
    sprite_url: str
    form_id: int | None = None
    # Forms folded into this row because they learn it the same way ("Alolan Geodude").
    also: list[str] = []
    methods: list[LearnMethodOut]


class GameOut(BaseModel):
    id: int
    identifier: str
    name: str
    generation: int
    learners: int  # distinct species that learn the move in this game


class MoveGameOut(BaseModel):
    """A game and every move some Pokémon can learn in it (the finder's game filter)."""

    id: int
    identifier: str
    name: str
    generation: int
    move_ids: list[int]


class MoveGameLearnersOut(BaseModel):
    """Who learns a move in one game, or in any game (``version_group_id`` None,
    the default), plus every game it's in."""

    move_id: int
    version_group_id: int | None
    games: list[GameOut]  # newest first
    total: int  # distinct species that learn it in any game
    machine: str | None = None  # e.g. "TM64" in the selected game
    # When it isn't a machine here: the most recent game where it was.
    last_machine: str | None = None
    last_machine_game: str | None = None
    learners: list[GameLearnerOut]


class AbilityHolderOut(BaseModel):
    """A species that has a given ability (reverse ability lookup)."""

    id: int
    dex_number: int
    name: str
    types: list[str]
    sprite_url: str
    is_hidden: bool = False


class NatureOut(BaseModel):
    id: int
    identifier: str
    name: str
    increased_stat: str | None = None
    decreased_stat: str | None = None


class ItemOut(BaseModel):
    id: int
    identifier: str
    name: str
    category: str | None = None
    cost: int | None = None
    short_effect: str | None = None
    flavor_text: str | None = None
    fling_power: int | None = None


class GameMoveOut(LearnsetMoveOut):
    machine: str | None = None  # e.g. "TM64" — the TM/HM/TR that teaches it in this game


class PokemonGameOut(BaseModel):
    id: int
    identifier: str
    name: str
    generation: int
    moves: int  # distinct moves the Pokémon learns in this game


class PokemonGameMovesOut(BaseModel):
    """A Pokémon's learnset in one game, plus every game it has a learnset in."""

    version_group_id: int | None
    games: list[PokemonGameOut]  # newest first
    moves: list[GameMoveOut]
