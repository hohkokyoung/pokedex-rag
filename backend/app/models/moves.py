"""Moves, per-species learnsets, and natures.

Reference data for the team builder / coach. Ingested from the local PokéAPI CSV
dataset (``moves.csv``, ``pokemon_moves.csv``, ``natures.csv`` …) — never fetched
from PokéAPI at runtime.

Design notes
------------
* ``Move`` keeps the battle-relevant columns only (type, damage class, power, PP,
  accuracy, priority). Effect text is out of scope for the first cut.
* ``PokemonMove`` is the *legal learnset*: one row per ``(pokemon_id, move_id)``,
  collapsed across version groups to "can this species ever learn this move".
  A representative learn method + level is retained for display (level-up wins,
  keeping the lowest level; otherwise machine → tutor → egg → form-change).
* ``PokemonMoveLearn`` is the *per-game* learnset: one row per
  ``(pokemon, version group, move, method)`` with the level, so the UI can answer
  "can X learn Y in this game, how, and at what level". ``pokemon_id`` is a default
  species or an alternate-form id (> 10000), hence no FK. ``VersionGroup`` names
  the games and ``MoveMachine`` gives each game's TM/HM/TR number for a move.
* ``Nature`` records the boosted/lowered stat (``None``/``None`` = neutral). Stat
  identifiers are stored as our denormalised stat column names
  (``attack``/``defense``/``sp_attack``/``sp_defense``/``speed``).
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.pokemon import Type


class Move(Base):
    __tablename__ = "moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type_id: Mapped[int | None] = mapped_column(ForeignKey("types.id"), nullable=True, index=True)
    # 'physical' | 'special' | 'status'
    damage_class: Mapped[str | None] = mapped_column(String(16), nullable=True)
    power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    # Concise mechanical effect (PokéAPI ``move_effect_prose.short_effect``, English),
    # with the ``$effect_chance`` placeholder resolved at ingest time.
    short_effect: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Who the move hits in a double battle — PokéAPI ``move_targets.identifier``
    # ('selected-pokemon' | 'all-opponents' | 'all-other-pokemon' | 'ally' | …).
    target: Mapped[str | None] = mapped_column(String(32), nullable=True)

    type: Mapped[Type | None] = relationship()


class PokemonMove(Base):
    """Legal learnset link — one representative row per (pokemon, move)."""

    __tablename__ = "pokemon_moves"

    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), primary_key=True)
    move_id: Mapped[int] = mapped_column(ForeignKey("moves.id"), primary_key=True)
    # 'level-up' | 'machine' | 'egg' | 'tutor' | 'form-change' …
    learn_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    move: Mapped[Move] = relationship()


class VersionGroup(Base):
    """A game (version group) that has learnset data, e.g. Scarlet / Violet."""

    __tablename__ = "version_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    # PokéAPI release order; newest has the highest value.
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class MoveMachine(Base):
    """The TM/HM/TR that teaches a move in a given game, e.g. ``TM64``."""

    __tablename__ = "move_machines"

    version_group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    move_id: Mapped[int] = mapped_column(ForeignKey("moves.id"), primary_key=True)
    label: Mapped[str] = mapped_column(String(16), nullable=False)


class PokemonMoveLearn(Base):
    """How a Pokémon (or alternate form) learns a move in one game."""

    __tablename__ = "pokemon_move_learns"

    pokemon_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    move_id: Mapped[int] = mapped_column(ForeignKey("moves.id"), primary_key=True)
    # 'level-up' | 'machine' | 'egg' | 'tutor' | …
    learn_method: Mapped[str] = mapped_column(String(32), primary_key=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (Index("ix_pokemon_move_learns_move_vg", "move_id", "version_group_id"),)


class Nature(Base):
    __tablename__ = "natures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # Denormalised stat column names, or NULL/NULL for a neutral nature.
    increased_stat: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decreased_stat: Mapped[str | None] = mapped_column(String(16), nullable=True)
