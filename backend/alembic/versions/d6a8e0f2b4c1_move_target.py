"""move doubles target

Revision ID: d6a8e0f2b4c1
Revises: c9f5d3e7a2b4
Create Date: 2026-09-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d6a8e0f2b4c1"
down_revision = "c9f5d3e7a2b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("moves", sa.Column("target", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("moves", "target")
