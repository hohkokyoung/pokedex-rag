"""team_members.item_id (a slot's held item)

Revision ID: b3d5f7a9c1e2
Revises: a1c4e6f8b2d0
Create Date: 2026-09-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b3d5f7a9c1e2"
down_revision = "a1c4e6f8b2d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No FK to items: `make items` reloads that table wholesale (see TeamMember.item_id).
    op.add_column("team_members", sa.Column("item_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("team_members", "item_id")
