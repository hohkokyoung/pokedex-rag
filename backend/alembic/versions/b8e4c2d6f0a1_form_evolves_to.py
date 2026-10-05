"""pokemon_forms.evolves_to (form -> new species evolution edges)

Revision ID: b8e4c2d6f0a1
Revises: a7d2f4c9e1b3
Create Date: 2026-09-23

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b8e4c2d6f0a1"
down_revision = "a7d2f4c9e1b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pokemon_forms",
        sa.Column(
            "evolves_to",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("pokemon_forms", "evolves_to")
