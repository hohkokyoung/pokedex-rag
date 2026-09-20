"""pokemon alternate forms

Revision ID: f5a1c3d7b204
Revises: d4f0a2c81e6b
Create Date: 2026-09-20

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f5a1c3d7b204"
down_revision = "d4f0a2c81e6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pokemon_forms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("base_pokemon_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("form_identifier", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=16), nullable=False, server_default="other"),
        sa.Column("is_mega", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_gigantamax", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_battle_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("abilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("height_m", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("hp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attack", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("defense", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sp_attack", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sp_defense", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("speed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("base_stat_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flavor_text", sa.Text(), nullable=True),
        sa.Column("sprite_path", sa.String(length=256), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["base_pokemon_id"], ["pokemon.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pokemon_forms_base_pokemon_id", "pokemon_forms", ["base_pokemon_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_pokemon_forms_base_pokemon_id", table_name="pokemon_forms")
    op.drop_table("pokemon_forms")
