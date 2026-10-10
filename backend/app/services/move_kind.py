"""What kind of move a move is, and the games of the moves nothing learns.

Moved from the website's finder (``kindOf``, ``KIND_GAMES``) so every client filters
Z-Moves and Max Moves the same way.
"""

from __future__ import annotations

import re
from typing import Literal

MoveKind = Literal["regular", "z", "max"]

# Z-Moves are the 1-PP moves, bar these three ordinary ones; Max Moves are "(G-)Max …".
_ORDINARY_ONE_PP = {"struggle", "sketch", "revival-blessing"}
_MAX = re.compile(r"^(G-)?Max ")

# Nothing "learns" Z-Moves or Max Moves, so learnset-based game lists miss them: they
# belong to the games that had the mechanic.
KIND_GAMES: dict[MoveKind, tuple[str, ...]] = {
    "z": ("sun-moon", "ultra-sun-ultra-moon"),
    "max": ("sword-shield",),
}


def move_kind(identifier: str, name: str, pp: int | None) -> MoveKind:
    if _MAX.match(name):
        return "max"
    if pp == 1 and identifier not in _ORDINARY_ONE_PP:
        return "z"
    return "regular"
