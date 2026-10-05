"""In-memory caches for plans and finished answers.

The Pokédex data never changes at runtime (ingest runs offline), so a repeated
question can reuse its plan — or its whole answer — without new LLM calls. Both
caches live for the backend process and are cleared on restart.
"""

from __future__ import annotations

import copy
import re
from collections import OrderedDict

PLAN_CACHE_SIZE = 256
ANSWER_CACHE_SIZE = 128


def normalize(question: str) -> str:
    """Case, spacing and trailing punctuation don't make a different question."""
    text = " ".join(question.lower().split())
    return re.sub(r"[\s?.!]+$", "", text)


class LRU[T]:
    def __init__(self, size: int):
        self.size = size
        self._items: OrderedDict[tuple[str, str], T] = OrderedDict()

    def get(self, scope: str, question: str) -> T | None:
        key = (scope, normalize(question))
        if key not in self._items:
            return None
        self._items.move_to_end(key)
        return copy.deepcopy(self._items[key])

    def put(self, scope: str, question: str, value: T) -> None:
        key = (scope, normalize(question))
        self._items[key] = copy.deepcopy(value)
        self._items.move_to_end(key)
        while len(self._items) > self.size:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()


plans: LRU = LRU(PLAN_CACHE_SIZE)
answers: LRU = LRU(ANSWER_CACHE_SIZE)
