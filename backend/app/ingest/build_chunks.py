"""Build the knowledge-chunk layer and embed it into pgvector.

Chunks come in two flavours:
  * ``profile``   — one structured summary per Pokémon (types, stats, abilities,
                    physical traits, evolution) for "tell me about X" queries.
  * ``dex_entry`` — each distinct English Pokédex flavour text, individually
                    citable, for lore / habitat / behaviour queries.

Idempotent: clears ``knowledge_chunks`` and rebuilds. Run on the host against
the Compose DB:

    cd backend
    DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex \\
        uv run python -m app.ingest.build_chunks
"""

from __future__ import annotations

import re

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import (
    Ability,
    KnowledgeChunk,
    Pokemon,
    PokemonEvolution,
    PokemonType,
)
from app.rag.embeddings import embed_documents

BATCH = 256


def _sync_engine():
    return create_engine(get_settings().database_url.replace("+asyncpg", "+psycopg"))


def _titlecase(s: str) -> str:
    return s[:1].upper() + s[1:]


def _evolution_sentence(session: Session, pokemon: Pokemon, name_by_id: dict[int, str]) -> str:
    if not pokemon.evolution_chain_id:
        return ""
    edges = session.execute(
        select(PokemonEvolution).where(
            PokemonEvolution.evolution_chain_id == pokemon.evolution_chain_id
        )
    ).scalars().all()

    parts: list[str] = []
    for e in edges:
        if e.to_pokemon_id == pokemon.id and e.from_pokemon_id:
            how = _how(e)
            parts.append(f"evolves from {name_by_id.get(e.from_pokemon_id, '?')}{how}")
    for e in edges:
        if e.from_pokemon_id == pokemon.id:
            how = _how(e)
            parts.append(f"evolves into {name_by_id.get(e.to_pokemon_id, '?')}{how}")
    return (". " + "; ".join(_titlecase(p) for p in parts)) if parts else ""


def _how(e: PokemonEvolution) -> str:
    if e.min_level:
        return f" at level {e.min_level}"
    if e.item:
        return f" using {e.item}"
    if e.trigger == "trade":
        return " by trading"
    if e.trigger:
        return f" via {e.trigger.replace('-', ' ')}"
    return ""


def _profile_text(
    pokemon: Pokemon, type_names: list[str], ability_names: list[str], evo: str
) -> str:
    types = "/".join(_titlecase(t) for t in type_names) or "unknown"
    rarity = ""
    if pokemon.is_mythical:
        rarity = " It is a Mythical Pokémon."
    elif pokemon.is_legendary:
        rarity = " It is a Legendary Pokémon."
    genus = f" the {pokemon.genus}" if pokemon.genus else ""
    abilities = ", ".join(ability_names) if ability_names else "none recorded"
    phys = []
    if pokemon.height_m:
        phys.append(f"{pokemon.height_m:.1f} m tall")
    if pokemon.weight_kg:
        phys.append(f"weighs {pokemon.weight_kg:.1f} kg")
    phys_s = (" It is " + " and ".join(phys) + ".") if phys else ""
    habitat = f" Its habitat is {pokemon.habitat}." if pokemon.habitat else ""
    return (
        f"{pokemon.name} (National Pokédex #{pokemon.dex_number}) is a {types}-type "
        f"Pokémon,{genus}.{rarity} Base stats — HP {pokemon.hp}, Attack {pokemon.attack}, "
        f"Defense {pokemon.defense}, Special Attack {pokemon.sp_attack}, Special Defense "
        f"{pokemon.sp_defense}, Speed {pokemon.speed} (base stat total {pokemon.base_stat_total}). "
        f"Abilities: {abilities}.{phys_s}{habitat}{evo}"
    )


def build() -> dict[str, int]:
    engine = _sync_engine()
    counts = {"profile": 0, "dex_entry": 0}

    with Session(engine) as session:
        session.execute(delete(KnowledgeChunk))
        session.commit()

        pokemon = session.execute(
            select(Pokemon)
            .options(
                selectinload(Pokemon.types).selectinload(PokemonType.type),
                selectinload(Pokemon.abilities),
                selectinload(Pokemon.flavor_texts),
            )
            .order_by(Pokemon.dex_number)
        ).scalars().all()

        name_by_id = {p.id: p.name for p in pokemon}
        abilities_by_id = {
            a.id: a.name for a in session.execute(select(Ability)).scalars().all()
        }

        pending: list[KnowledgeChunk] = []
        texts: list[str] = []

        def flush() -> None:
            if not texts:
                return
            vectors = embed_documents(texts)
            for chunk, vec in zip(pending, vectors, strict=True):
                chunk.embedding = vec
            session.add_all(pending)
            session.commit()
            pending.clear()
            texts.clear()

        for p in pokemon:
            type_names = [pt.type.identifier for pt in p.types]
            ability_names = [
                abilities_by_id.get(pa.ability_id, "") for pa in p.abilities
            ]
            ability_names = [a for a in ability_names if a]
            evo = _evolution_sentence(session, p, name_by_id)

            profile = _profile_text(p, type_names, ability_names, evo)
            pending.append(
                KnowledgeChunk(
                    pokemon_id=p.id,
                    pokemon_name=p.name,
                    chunk_type="profile",
                    source_ref="profile",
                    content=profile,
                    embedding=[],
                )
            )
            texts.append(profile)
            counts["profile"] += 1

            # Entries are stored one per game; many games reuse a text, so embed each once.
            seen_entries: set[str] = set()
            for ft in sorted(p.flavor_texts, key=lambda r: r.id):
                key = re.sub(r"[^a-z0-9]", "", ft.flavor_text.lower())
                if key in seen_entries:
                    continue
                seen_entries.add(key)
                content = f"{p.name} — Pokédex entry: {ft.flavor_text}"
                pending.append(
                    KnowledgeChunk(
                        pokemon_id=p.id,
                        pokemon_name=p.name,
                        chunk_type="dex_entry",
                        source_ref=ft.version,
                        content=content,
                        embedding=[],
                    )
                )
                texts.append(content)
                counts["dex_entry"] += 1

            if len(texts) >= BATCH:
                flush()

        flush()

    return counts


if __name__ == "__main__":
    print("Building knowledge chunks + embeddings (first run downloads the model)…")
    result = build()
    total = sum(result.values())
    print(f"Done. {total} chunks: {result['profile']} profiles, {result['dex_entry']} dex entries.")
