"""moves, learnsets and natures

Revision ID: a1c7f2b9e4d0
Revises: 3b865352aed5
Create Date: 2026-09-09 12:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a1c7f2b9e4d0"
down_revision: str | None = "3b865352aed5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "natures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("increased_stat", sa.String(length=16), nullable=True),
        sa.Column("decreased_stat", sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_natures_identifier", "natures", ["identifier"])

    op.create_table(
        "moves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=True),
        sa.Column("damage_class", sa.String(length=16), nullable=True),
        sa.Column("power", sa.Integer(), nullable=True),
        sa.Column("pp", sa.Integer(), nullable=True),
        sa.Column("accuracy", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["type_id"], ["types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_moves_identifier", "moves", ["identifier"])
    op.create_index("ix_moves_type_id", "moves", ["type_id"])

    op.create_table(
        "pokemon_moves",
        sa.Column("pokemon_id", sa.Integer(), nullable=False),
        sa.Column("move_id", sa.Integer(), nullable=False),
        sa.Column("learn_method", sa.String(length=32), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["pokemon_id"], ["pokemon.id"]),
        sa.ForeignKeyConstraint(["move_id"], ["moves.id"]),
        sa.PrimaryKeyConstraint("pokemon_id", "move_id"),
    )


def downgrade() -> None:
    op.drop_table("pokemon_moves")
    op.drop_index("ix_moves_type_id", table_name="moves")
    op.drop_index("ix_moves_identifier", table_name="moves")
    op.drop_table("moves")
    op.drop_index("ix_natures_identifier", table_name="natures")
    op.drop_table("natures")
