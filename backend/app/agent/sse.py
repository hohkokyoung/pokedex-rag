"""Server-Sent Events framing and the sources list sent with every answer."""

from __future__ import annotations

import json

from app.rag.retrieval import RetrievedChunk
from app.schemas.ask import Source


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _sources(
    chunks: list[RetrievedChunk], refs: list[tuple[str, int]] | None = None
) -> list[Source]:
    """Number the evidence 1..n. ``refs`` gives each chunk's (step id, step-local index)."""
    return [
        Source(
            n=i,
            pokemon_id=c.pokemon_id,
            pokemon_name=c.pokemon_name,
            dex_number=c.dex_number,
            chunk_type=c.chunk_type,
            source_ref=c.source_ref,
            # A learnset chunk is shown in full (the UI lists every move); others are previews.
            snippet=(
                c.content
                if c.chunk_type == "learnset" or len(c.content) <= 420
                else c.content[:420] + "…"
            ),
            score=c.score,
            step=refs[i - 1][0] if refs else None,
            step_index=refs[i - 1][1] if refs else None,
        )
        for i, c in enumerate(chunks, start=1)
    ]
