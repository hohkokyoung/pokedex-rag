"""Relational Pokémon schema.

Design notes
------------
* We ingest only *default-form* Pokémon (PokéAPI ``pokemon.is_default = 1``), so
  ``pokemon.id`` maps 1:1 to a species and to the national Pokédex number.
* The six base stats are stored as columns on ``pokemon`` (plus a precomputed
  ``base_stat_total``). This keeps structured/analytical queries in later phases
  simple and fast ("highest Attack", "Speed above 100", "sort by total").
* Types and abilities are modelled as proper many-to-many relationships.
* Multiple English flavour texts are retained per Pokémon; they become the seed
  corpus for knowledge chunks + embeddings in Phase 3, and are individually
  citable.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    pokemon: Mapped[list[Pokemon]] = relationship(back_populates="generation")


class Type(Base):
    __tablename__ = "types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)


class Ability(Base):
    __tablename__ = "abilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Fluffy in-game flavour text (from ability_flavor_text).
    effect: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Concise mechanical effect with the real numbers, e.g. "Increases moves'
    # accuracy to 1.3×" (from ability_prose.short_effect, English).
    short_effect: Mapped[str | None] = mapped_column(String(512), nullable=True)


class Pokemon(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    species_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    dex_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    genus: Mapped[str | None] = mapped_column(String(128), nullable=True)

    generation_id: Mapped[int | None] = mapped_column(
        ForeignKey("generations.id"), nullable=True, index=True
    )

    # Physical characteristics (converted to SI units on ingest).
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    base_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Species flags & descriptors.
    capture_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base_happiness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_legendary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_mythical: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_baby: Mapped[bool] = mapped_column(Boolean, default=False)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    shape: Mapped[str | None] = mapped_column(String(32), nullable=True)
    habitat: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    # Evolution linkage.
    evolution_chain_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    evolves_from_species_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Base stats (denormalised for fast structured queries).
    hp: Mapped[int] = mapped_column(Integer, default=0, index=True)
    attack: Mapped[int] = mapped_column(Integer, default=0, index=True)
    defense: Mapped[int] = mapped_column(Integer, default=0, index=True)
    sp_attack: Mapped[int] = mapped_column(Integer, default=0, index=True)
    sp_defense: Mapped[int] = mapped_column(Integer, default=0, index=True)
    speed: Mapped[int] = mapped_column(Integer, default=0, index=True)
    base_stat_total: Mapped[int] = mapped_column(Integer, default=0, index=True)

    # Training & breeding info (added in T-001).
    # -1 = genderless; otherwise female ratio in eighths (gender_rate / 8).
    gender_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hatch_counter: Mapped[int | None] = mapped_column(Integer, nullable=True)  # egg cycles
    growth_rate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    egg_groups: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    ev_yield: Mapped[dict[str, int] | None] = mapped_column(JSONB, nullable=True)

    # A representative English description + sprite.
    flavor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sprite_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Female artwork for species with visual gender differences (Pyroar, Unfezant…);
    # null when the female looks the same or is its own form (Meowstic, Indeedee).
    female_sprite_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Cosmetic (non-battle) variants sharing this pokemon record, in game order —
    # e.g. Alcremie's 63 cream × sweet combos, Vivillon's patterns. Empty unless >1.
    # Each entry is ``{"name": ..., "sprite_path": "variants/<id>-<form>.png"}``.
    cosmetic_variants: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    generation: Mapped[Generation | None] = relationship(back_populates="pokemon")
    types: Mapped[list[PokemonType]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan", order_by="PokemonType.slot"
    )
    abilities: Mapped[list[PokemonAbility]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan", order_by="PokemonAbility.slot"
    )
    flavor_texts: Mapped[list[PokemonFlavorText]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan"
    )


class PokemonType(Base):
    __tablename__ = "pokemon_types"

    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), primary_key=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("types.id"), primary_key=True)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)

    pokemon: Mapped[Pokemon] = relationship(back_populates="types")
    type: Mapped[Type] = relationship()


class PokemonAbility(Base):
    __tablename__ = "pokemon_abilities"

    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), primary_key=True)
    ability_id: Mapped[int] = mapped_column(ForeignKey("abilities.id"), primary_key=True)
    slot: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    pokemon: Mapped[Pokemon] = relationship(back_populates="abilities")
    ability: Mapped[Ability] = relationship()


class PokemonFlavorText(Base):
    __tablename__ = "pokemon_flavor_texts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), nullable=False, index=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    flavor_text: Mapped[str] = mapped_column(Text, nullable=False)

    pokemon: Mapped[Pokemon] = relationship(back_populates="flavor_texts")

    __table_args__ = (
        UniqueConstraint("pokemon_id", "version", name="uq_flavor_pokemon_version"),
    )


class TypeEffectiveness(Base):
    """Attacking-type × defending-type damage multiplier (the type chart)."""

    __tablename__ = "type_effectiveness"

    damage_type_id: Mapped[int] = mapped_column(ForeignKey("types.id"), primary_key=True)
    target_type_id: Mapped[int] = mapped_column(ForeignKey("types.id"), primary_key=True)
    factor: Mapped[float] = mapped_column(Float, nullable=False)  # 0, 0.5, 1, or 2


class PokemonForm(Base):
    """Alternate forms of a default-form species (regional, Mega, Primal, Gigantamax,
    and notable battle forms — the ``is_default = 0`` rows PokéAPI keeps as separate
    ``pokemon`` records).

    Forms are a *display-only* enrichment shown on the parent species' detail page.
    They are deliberately isolated from the default-form-only invariants that search,
    teams and RAG rely on, so types/abilities are denormalised into JSONB rather than
    modelled as new first-class entities.
    """

    __tablename__ = "pokemon_forms"

    # PokéAPI ``pokemon.id`` of the alternate form (> 10000).
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id"), nullable=False, index=True
    )
    # Short display label, e.g. "Alolan", "Mega X", "Gigantamax", "Speed Forme".
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    form_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # regional | mega | primal | gigantamax | battle | other
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="other")
    is_mega: Mapped[bool] = mapped_column(Boolean, default=False)
    is_gigantamax: Mapped[bool] = mapped_column(Boolean, default=False)
    is_battle_only: Mapped[bool] = mapped_column(Boolean, default=False)

    types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    # [{"name": str, "identifier": str, "is_hidden": bool}]
    abilities: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    hp: Mapped[int] = mapped_column(Integer, default=0)
    attack: Mapped[int] = mapped_column(Integer, default=0)
    defense: Mapped[int] = mapped_column(Integer, default=0)
    sp_attack: Mapped[int] = mapped_column(Integer, default=0)
    sp_defense: Mapped[int] = mapped_column(Integer, default=0)
    speed: Mapped[int] = mapped_column(Integer, default=0)
    base_stat_total: Mapped[int] = mapped_column(Integer, default=0)

    flavor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sprite_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Per-form enrichment (display-only; forms can't use the pokemon-id FKs).
    flavor_texts: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    learnset: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    # The pokemon id this form evolves from: another form (Galarian Darumaka ->
    # Galarian Darmanitan) or a default species (Koffing -> Galarian Weezing).
    evolves_from_form_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evo_trigger: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evo_min_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evo_item: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evo_condition: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Evolutions from this form into a *new species* (Hisuian Qwilfish -> Overqwil):
    # [{"to_pokemon_id", "trigger", "min_level", "item", "condition"}]
    evolves_to: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )


class PokemonEvolution(Base):
    __tablename__ = "pokemon_evolutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evolution_chain_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    from_pokemon_id: Mapped[int | None] = mapped_column(
        ForeignKey("pokemon.id"), nullable=True, index=True
    )
    to_pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), nullable=False, index=True)
    trigger: Mapped[str | None] = mapped_column(String(64), nullable=True)
    min_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item: Mapped[str | None] = mapped_column(String(64), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(256), nullable=True)

    __table_args__ = (
        Index("ix_evolution_from_to", "from_pokemon_id", "to_pokemon_id"),
    )
