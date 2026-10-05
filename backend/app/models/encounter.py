"""Where to find a Pokémon in the wild, per game (from the PokéAPI encounter CSVs)."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PokemonEncounter(Base):
    """One way to meet a Pokémon (or alternate form) at one place in one game.

    Pre-aggregated at ingest: the raw encounter-slot rows for the same place,
    method and conditions are folded into one level range and a summed chance.
    Names are denormalised so the detail page reads it with a single query.
    """

    __tablename__ = "pokemon_encounters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pokemon_id: Mapped[int] = mapped_column(Integer, nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)  # "HeartGold"
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)  # release order
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str] = mapped_column(String(128), nullable=False)  # "Route 29"
    area: Mapped[str | None] = mapped_column(String(128), nullable=True)  # "1F", "South"
    method: Mapped[str] = mapped_column(String(32), nullable=False)  # 'walk' | 'surf' | …
    method_name: Mapped[str] = mapped_column(String(160), nullable=False)
    min_level: Mapped[int] = mapped_column(Integer, nullable=False)
    max_level: Mapped[int] = mapped_column(Integer, nullable=False)
    # Summed slot rarity in percent, capped at 100.
    chance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # "At night · During a swarm"
    conditions: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (Index("ix_pokemon_encounters_pokemon", "pokemon_id", "version_id"),)
