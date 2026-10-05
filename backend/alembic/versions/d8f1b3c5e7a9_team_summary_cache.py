"""teams: persisted AI summary keyed by a roster fingerprint

Revision ID: d8f1b3c5e7a9
Revises: c4e8a2f6d0b3
Create Date: 2026-10-03

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d8f1b3c5e7a9"
down_revision = "c4e8a2f6d0b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("summary_text", sa.Text(), nullable=True))
    op.add_column("teams", sa.Column("summary_source", sa.String(length=8), nullable=True))
    op.add_column("teams", sa.Column("summary_key", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("teams", "summary_key")
    op.drop_column("teams", "summary_source")
    op.drop_column("teams", "summary_text")
