"""move short_effect text

Revision ID: c3e9f1a20b7d
Revises: b2d8e3a5c9f1
Create Date: 2026-09-18

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c3e9f1a20b7d"
down_revision = "b2d8e3a5c9f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("moves", sa.Column("short_effect", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("moves", "short_effect")
