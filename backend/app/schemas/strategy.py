"""Schemas for the team strategy profile and its one-paragraph summary."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class StrategyContributor(BaseModel):
    name: str
    moves: list[str]
    set: bool  # on the slot (or chosen ability) vs only learnable


class StrategyAxis(BaseModel):
    key: str
    label: str
    score: int  # 0–100, set moves in full + learnable partly
    now: int  # only what's on the team today
    potential: int  # if every learnable option were used
    detail: str
    contributors: list[StrategyContributor]


class TeamStrategy(BaseModel):
    team_id: int
    style: str
    style_reason: str
    axes: list[StrategyAxis]


class TeamSummaryOut(BaseModel):
    team_id: int
    text: str
    source: Literal["ai", "rules"]
    # True while a fresher (AI) summary is being written in the background.
    pending: bool = False
