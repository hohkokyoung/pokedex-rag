"""question_log: per-question plan trace (planner, fallbacks, steps, usage)

Revision ID: a7c3e9b1d5f2
Revises: d8f1b3c5e7a9
Create Date: 2026-10-06

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a7c3e9b1d5f2"
down_revision = "d8f1b3c5e7a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "question_log",
        sa.Column("trace", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("question_log", "trace")
