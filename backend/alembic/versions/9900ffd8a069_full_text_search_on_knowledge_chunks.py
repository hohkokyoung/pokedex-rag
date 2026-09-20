"""full-text search on knowledge_chunks

Revision ID: 9900ffd8a069
Revises: e47ffb287097
Create Date: 2026-09-08 16:16:31.812901
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '9900ffd8a069'
down_revision: str | None = 'e47ffb287097'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Generated tsvector column over the chunk text + a GIN index for full-text
    # (BM25-style) keyword retrieval alongside the existing pgvector index.
    op.execute(
        "ALTER TABLE knowledge_chunks "
        "ADD COLUMN content_tsv tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_tsv "
        "ON knowledge_chunks USING GIN (content_tsv)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_tsv")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS content_tsv")
