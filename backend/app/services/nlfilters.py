"""Tiny natural-language filter parsing shared by Ask retrieval and the recommender.

Leaf module (no app deps) so both the rag layer and the services layer can import
it without creating a cycle.

Negation is sentiment-aware and *proximity-based*: a rejecting word in the few
words just before "legendary"/"mythical" means exclude. This deliberately catches
open-ended phrasings ("fuck legendaries", "skip the legendaries", "no legendaries")
without an LLM, while a bare positive mention ("legendary dragons", "give me a
legendary") still means include, and something mentioned nowhere stays unconstrained.
"""

from __future__ import annotations

import re

# Rejecting tokens (whole-word) that flip a mention to "exclude".
_NEG_WORDS = (
    "no", "not", "non", "nope", "without", "exclude", "excluding", "skip", "skipping",
    "avoid", "avoiding", "ban", "banned", "drop", "dropping", "hate", "hates", "hating",
    "fuck", "fucking", "screw", "screwing", "damn", "forget", "remove", "removing",
    "ditch", "anti", "minus",
)
_NEG_RE = re.compile(r"\b(?:" + "|".join(_NEG_WORDS) + r")\b")

# Multiword rejections that a single-token check misses (checked over the whole text).
_NEG_PHRASES = (
    "don't want", "dont want", "do not want", "sick of", "tired of", "get rid of",
    "no thanks", "not into", "rather not",
)


def _mention_constraint(text: str, root: str) -> bool | None:
    """True = only these, False = exclude these, None = not mentioned."""
    low = text.lower()
    if root not in low:
        return None
    # The up-to-2 words immediately preceding the first mention. Kept short so a
    # rejection meant for a different noun ("no legendaries but mythicals ok") and a
    # trailing negation ("which legendary is not a dragon") don't leak in.
    m = re.search(r"((?:[a-z']+[^a-z']+){0,2})" + root, low)
    before = m.group(1) if m else ""
    if _NEG_RE.search(before) or any(p in low for p in _NEG_PHRASES):
        return False
    return True


def legendary_constraint(text: str) -> bool | None:
    return _mention_constraint(text, "legendar")


def mythical_constraint(text: str) -> bool | None:
    return _mention_constraint(text, "mythical")


def restricted_filters(text: str) -> tuple[bool | None, bool | None]:
    """(legendary, mythical) filters for retrieval, with casual coupling.

    "non-legendary" colloquially means "no restricted/uber Pokémon", so excluding
    legendaries also excludes mythicals unless the user positively asks for them.
    """
    legendary = legendary_constraint(text)
    mythical = mythical_constraint(text)
    if legendary is False and mythical is None:
        mythical = False
    return legendary, mythical
