"""items table

Revision ID: d4f0a2c81e6b
Revises: c3e9f1a20b7d
Create Date: 2026-09-19

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d4f0a2c81e6b"
down_revision = "c3e9f1a20b7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("cost", sa.Integer(), nullable=True),
        sa.Column("short_effect", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_items_identifier", "items", ["identifier"])
    op.create_index("ix_items_name", "items", ["name"])


def downgrade() -> None:
    op.drop_index("ix_items_name", table_name="items")
    op.drop_index("ix_items_identifier", table_name="items")
    op.drop_table("items")
