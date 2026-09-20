"""Pydantic response schemas for the Pokédex API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    identifier: str
    name: str


class GenerationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    identifier: str
    name: str


class AbilityOut(BaseModel):
    id: int
    identifier: str
    name: str
    effect: str | None = None
    is_hidden: bool = False


class StatsOut(BaseModel):
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int
    total: int


class PokemonSummary(BaseModel):
    """Compact representation for grid/list views."""

    id: int
    dex_number: int
    name: str
    genus: str | None = None
    types: list[str]
    sprite_url: str
    base_stat_total: int
    generation_id: int | None = None
    is_legendary: bool = False
    is_mythical: bool = False
    # Set when this result is an alternate form; the UI links to
    # /pokedex/{dex_number}?form={form_id}. None for a default-species result.
    form_id: int | None = None


class EvolutionStage(BaseModel):
    from_id: int | None = None
    from_name: str | None = None
    to_id: int
    to_name: str
    trigger: str | None = None
    min_level: int | None = None
    item: str | None = None
    condition: str | None = None


class EvolutionMember(BaseModel):
    id: int
    name: str
    types: list[str]
    sprite_url: str


class FormAbilityOut(BaseModel):
    name: str
    identifier: str
    is_hidden: bool = False
    effect: str | None = None


class MatchupsOut(BaseModel):
    weak_4x: list[str] = []
    weak_2x: list[str] = []
    resist_half: list[str] = []
    resist_quarter: list[str] = []
    immune: list[str] = []


class FormOut(BaseModel):
    """An alternate form of a species. Carries everything the detail page's form
    switcher swaps in (sprite/name/types/stats/abilities/matchups); species-level
    moveset stays on the base species, but evolution and dex-entry flavor are now
    per-form (a form may have its own evolution chain and/or flavor text)."""

    id: int
    name: str
    form_identifier: str | None = None
    category: str  # regional | mega | primal | gigantamax | battle | other
    is_mega: bool = False
    is_gigantamax: bool = False
    is_battle_only: bool = False
    types: list[str] = []
    abilities: list[FormAbilityOut] = []
    stats: StatsOut
    height_m: float | None = None
    weight_kg: float | None = None
    sprite_url: str
    matchups: MatchupsOut = MatchupsOut()
    flavor_texts: list[str] = []
    evolution_members: list[EvolutionMember] = []
    evolution_stages: list[EvolutionStage] = []


class PokemonDetail(BaseModel):
    id: int
    dex_number: int
    name: str
    genus: str | None = None
    types: list[str]
    sprite_url: str

    height_m: float | None = None
    weight_kg: float | None = None
    base_experience: int | None = None
    capture_rate: int | None = None
    base_happiness: int | None = None

    color: str | None = None
    shape: str | None = None
    habitat: str | None = None

    # Training & breeding (T-001)
    gender_rate: int | None = None  # -1 genderless; else female eighths
    hatch_counter: int | None = None  # egg cycles
    growth_rate: str | None = None
    egg_groups: list[str] = []
    ev_yield: dict[str, int] = {}

    is_legendary: bool = False
    is_mythical: bool = False
    is_baby: bool = False

    generation: GenerationOut | None = None
    stats: StatsOut
    abilities: list[AbilityOut]
    flavor_text: str | None = None
    flavor_texts: list[str] = []

    evolution_chain_id: int | None = None
    evolution_stages: list[EvolutionStage] = []
    evolution_members: list[EvolutionMember] = []

    forms: list[FormOut] = []

    matchups: MatchupsOut = MatchupsOut()


class PokemonListResponse(BaseModel):
    items: list[PokemonSummary]
    total: int
    limit: int
    offset: int
