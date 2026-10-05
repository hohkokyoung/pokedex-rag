"""team_members.form_id (a slot can hold an alternate form: Mega, regional…)

Revision ID: a1c4e6f8b2d0
Revises: e2b7c9d1f3a5
Create Date: 2026-09-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1c4e6f8b2d0"
down_revision = "e2b7c9d1f3a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No FK to pokemon_forms: forms are re-ingested wholesale (see TeamMember.form_id).
    op.add_column("team_members", sa.Column("form_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("team_members", "form_id")
