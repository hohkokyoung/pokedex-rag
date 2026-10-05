"""Knowledge-chunk layer for semantic retrieval (pgvector)."""

from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.core.database import Base

_EMBED_DIM = get_settings().embedding_dim


class KnowledgeChunk(Base):
    """A retrievable unit of Pokémon knowledge with its embedding.

    ``chunk_type`` distinguishes profile summaries from individual dex entries
    and evolution notes, so retrieval and citations stay traceable to a source.
    """

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pokemon_id: Mapped[int | None] = mapped_column(
        ForeignKey("pokemon.id"), nullable=True, index=True
    )
    pokemon_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chunk_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(_EMBED_DIM), nullable=False)

    __table_args__ = (
        # Approximate-nearest-neighbour index over cosine distance.
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
