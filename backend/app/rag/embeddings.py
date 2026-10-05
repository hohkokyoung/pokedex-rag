"""Local text embeddings via fastembed (ONNX, no external API).

A single model instance is lazily loaded and reused. bge-small-en-v1.5 uses
distinct query/passage encodings, so queries and documents call different
methods for best retrieval quality.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

from fastembed import TextEmbedding

from app.core.config import get_settings


@lru_cache
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=get_settings().embedding_model)


def embed_documents(texts: Iterable[str]) -> list[list[float]]:
    """Embed passages/documents for storage."""
    return [vec.tolist() for vec in _model().embed(list(texts))]


def embed_query(text: str) -> list[float]:
    """Embed a search query (applies the model's query-side encoding)."""
    return next(iter(_model().query_embed([text]))).tolist()


def warmup() -> None:
    """Force model download/load (call at startup to avoid first-request latency)."""
    embed_query("warmup")
