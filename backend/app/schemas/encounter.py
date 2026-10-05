"""Where-to-find (wild encounter) response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EncounterGameOut(BaseModel):
    version_id: int
    version: str
    generation: int
    places: int  # distinct locations the Pokémon appears at in this game


class EncounterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location: str
    area: str | None
    region: str | None
    method: str
    method_name: str
    min_level: int
    max_level: int
    chance: int | None
    conditions: str | None


class PokemonEncountersOut(BaseModel):
    """Where a Pokémon is found in one game, plus every game it can be found in."""

    version_id: int | None
    games: list[EncounterGameOut]  # oldest first
    encounters: list[EncounterOut]
