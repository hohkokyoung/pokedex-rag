"""teams and team members

Revision ID: b2d8e3a5c9f1
Revises: a1c7f2b9e4d0
Create Date: 2026-09-09 12:35:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2d8e3a5c9f1"
down_revision: str | None = "a1c7f2b9e4d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_kind", "teams", ["kind"])

    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("pokemon_id", sa.Integer(), nullable=False),
        sa.Column("ability_id", sa.Integer(), nullable=True),
        sa.Column("nature_id", sa.Integer(), nullable=True),
        sa.Column("ev_spread", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("iv_spread", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("move_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pokemon_id"], ["pokemon.id"]),
        sa.ForeignKeyConstraint(["ability_id"], ["abilities.id"]),
        sa.ForeignKeyConstraint(["nature_id"], ["natures.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "slot", name="uq_team_member_slot"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_team_members_team_id", table_name="team_members")
    op.drop_table("team_members")
    op.drop_index("ix_teams_kind", table_name="teams")
    op.drop_table("teams")
