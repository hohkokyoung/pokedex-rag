"""ability short_effect text

Revision ID: a7d2f4c9e1b3
Revises: 72f70233db46
Create Date: 2026-09-21

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7d2f4c9e1b3"
down_revision = "72f70233db46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("abilities", sa.Column("short_effect", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("abilities", "short_effect")
