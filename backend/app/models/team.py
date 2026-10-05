"""Saved teams and their configured slots (single local user).

Like the rest of the app there is no auth: every team belongs to the sole user.
A team is either the player's own (``kind='player'``) or a saved opponent
(``kind='opponent'``) to plan against.

Per-slot competitive config (ability, nature, EV/IV spreads, chosen moves) is
stored loosely as JSONB; the *validation* (EV caps, IV bounds, ≤4 moves, moves
legal for the species, ability belongs to the species) lives in the schema/service
layer, not in the database — mirroring how the profile models keep rules in code.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime as SADateTime
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

TEAM_KINDS = ("player", "opponent")
MAX_SLOTS = 6
MAX_MOVES = 4
MAX_EV_PER_STAT = 252
MAX_EV_TOTAL = 510
MAX_IV = 31


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="player", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Cached summary (app.rag.team_summary): only rewritten when ``summary_key`` —
    # a fingerprint of the members, abilities and moves — no longer matches.
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_source: Mapped[str | None] = mapped_column(String(8), nullable=True)
    summary_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list[TeamMember]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
        order_by="TeamMember.slot",
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slot: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..6
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), nullable=False)
    # Optional alternate form of ``pokemon_id`` (``pokemon_forms.id``, e.g. Mega Garchomp Z).
    # No FK: forms are re-ingested wholesale (``make forms``), which would trip a constraint;
    # the service validates it belongs to the species and hydration tolerates a stale id.
    form_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ability_id: Mapped[int | None] = mapped_column(ForeignKey("abilities.id"), nullable=True)
    # Held item (``items.id``). No FK for the same reason as ``form_id``: ``make items``
    # reloads the table wholesale. Validated on write; a stale id hydrates as no item.
    item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nature_id: Mapped[int | None] = mapped_column(ForeignKey("natures.id"), nullable=True)
    # {stat_column: value}; validated in the service layer.
    ev_spread: Mapped[dict[str, int] | None] = mapped_column(JSONB, nullable=True)
    iv_spread: Mapped[dict[str, int] | None] = mapped_column(JSONB, nullable=True)
    move_ids: Mapped[list[int] | None] = mapped_column(JSONB, nullable=True)

    team: Mapped[Team] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint("team_id", "slot", name="uq_team_member_slot"),
    )
