"""Items — reference data for the item lookup.

Ingested from the local PokéAPI CSVs (``items.csv``, ``item_names.csv``,
``item_prose.csv``, ``item_categories.csv``, ``item_flavor_text.csv``) — never
fetched at runtime. Items have no relationships to other tables, so they can be
(re)populated on their own.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    short_effect: Mapped[str | None] = mapped_column(Text, nullable=True)
    # The in-game bag description (newest game's English text).
    flavor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Base power when the item is thrown with Fling (None = can't be flung).
    fling_power: Mapped[int | None] = mapped_column(Integer, nullable=True)
