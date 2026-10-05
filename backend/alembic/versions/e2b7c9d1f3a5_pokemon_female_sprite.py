"""pokemon.female_sprite_path (visual gender differences: Pyroar's mane, Unfezant…)

Revision ID: e2b7c9d1f3a5
Revises: d6a8e0f2b4c1
Create Date: 2026-09-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e2b7c9d1f3a5"
down_revision = "d6a8e0f2b4c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pokemon", sa.Column("female_sprite_path", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("pokemon", "female_sprite_path")
