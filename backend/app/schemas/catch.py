"""Catch odds per ball for a wild Pokémon (``GET /api/pokemon/{id}/catch``)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

CatchStatus = Literal["none", "sleep", "freeze", "paralysis", "burn", "poison"]


class CatchTermsOut(BaseModel):
    """The formula's terms for one ball (what the "math" line shows)."""

    max_hp: int
    hp: int
    rate: int  # catch rate after the Heavy Ball's change
    hp_factor: float  # (3M − 2H) / 3M
    ball: float
    status: float
    low_level: float
    a: float  # the modified rate, capped at 255
    shake: float  # one shake check's pass chance
    crit: float  # critical-capture chance


class BallOddsOut(BaseModel):
    id: str
    name: str
    why: str
    p: float  # chance to catch with one throw
    throws: int | None  # throws for a 90% chance; null when it can't catch
    sure: bool
    terms: CatchTermsOut


class CatchOut(BaseModel):
    pokemon_id: int
    name: str
    capture_rate: int
    balls: list[BallOddsOut]  # best first
