"""pokemon.cosmetic_variants (Alcremie creams/sweets, Vivillon patterns, …)

Revision ID: c9f5d3e7a2b4
Revises: b8e4c2d6f0a1
Create Date: 2026-09-23

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c9f5d3e7a2b4"
down_revision = "b8e4c2d6f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pokemon",
        sa.Column(
            "cosmetic_variants",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("pokemon", "cosmetic_variants")
