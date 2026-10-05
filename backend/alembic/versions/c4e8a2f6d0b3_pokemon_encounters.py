"""pokemon_encounters: where to find each Pokémon, per game

Revision ID: c4e8a2f6d0b3
Revises: a9c2e4f6b8d1
Create Date: 2026-10-02

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c4e8a2f6d0b3"
down_revision = "a9c2e4f6b8d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pokemon_encounters",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pokemon_id", sa.Integer(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(32), nullable=True),
        sa.Column("location", sa.String(128), nullable=False),
        sa.Column("area", sa.String(128), nullable=True),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("method_name", sa.String(160), nullable=False),
        sa.Column("min_level", sa.Integer(), nullable=False),
        sa.Column("max_level", sa.Integer(), nullable=False),
        sa.Column("chance", sa.Integer(), nullable=True),
        sa.Column("conditions", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_pokemon_encounters_pokemon", "pokemon_encounters", ["pokemon_id", "version_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_pokemon_encounters_pokemon", table_name="pokemon_encounters")
    op.drop_table("pokemon_encounters")
