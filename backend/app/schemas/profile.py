"""Schemas for the local user profile."""

from __future__ import annotations

from pydantic import BaseModel


class FavoriteOut(BaseModel):
    id: int
    dex_number: int
    name: str
    types: list[str]
    sprite_url: str


class ProfileOut(BaseModel):
    preferred_types: list[str]
    favorites: list[FavoriteOut]


class ProfileUpdate(BaseModel):
    preferred_types: list[str]
