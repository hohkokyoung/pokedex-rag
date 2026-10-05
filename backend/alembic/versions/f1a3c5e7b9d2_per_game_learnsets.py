"""per-game learnsets: version_groups, move_machines, pokemon_move_learns

Revision ID: f1a3c5e7b9d2
Revises: b3d5f7a9c1e2
Create Date: 2026-09-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f1a3c5e7b9d2"
down_revision = "b3d5f7a9c1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "version_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identifier", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )
    op.create_table(
        "move_machines",
        sa.Column("version_group_id", sa.Integer(), primary_key=True),
        sa.Column("move_id", sa.Integer(), sa.ForeignKey("moves.id"), primary_key=True),
        sa.Column("label", sa.String(16), nullable=False),
    )
    op.create_table(
        "pokemon_move_learns",
        sa.Column("pokemon_id", sa.Integer(), primary_key=True),
        sa.Column("version_group_id", sa.Integer(), primary_key=True),
        sa.Column("move_id", sa.Integer(), sa.ForeignKey("moves.id"), primary_key=True),
        sa.Column("learn_method", sa.String(32), primary_key=True),
        sa.Column("level", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_pokemon_move_learns_move_vg", "pokemon_move_learns", ["move_id", "version_group_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_pokemon_move_learns_move_vg", table_name="pokemon_move_learns")
    op.drop_table("pokemon_move_learns")
    op.drop_table("move_machines")
    op.drop_table("version_groups")
