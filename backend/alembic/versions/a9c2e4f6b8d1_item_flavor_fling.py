"""items.flavor_text and items.fling_power

Revision ID: a9c2e4f6b8d1
Revises: f1a3c5e7b9d2
Create Date: 2026-09-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a9c2e4f6b8d1"
down_revision = "f1a3c5e7b9d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("items", sa.Column("flavor_text", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("fling_power", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("items", "fling_power")
    op.drop_column("items", "flavor_text")
