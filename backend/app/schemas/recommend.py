"""Schemas for coach-drafted candidate additions."""

from __future__ import annotations

from pydantic import BaseModel


class Candidate(BaseModel):
    pokemon_id: int
    dex_number: int
    name: str
    types: list[str]
    sprite_url: str
    role: str
    base_stats: dict[str, int]
    reason: str
