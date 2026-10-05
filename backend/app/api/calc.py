"""The home damage calculator's coach: questions over the calculator's live state."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.runner import run_question
from app.agent.sse import _sse
from app.agent.tools import AgentContext
from app.core.database import async_session_factory
from app.rag import personalize
from app.schemas.calc import CalcAskRequest
from app.services.calc_state import resolve_state

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calc", tags=["calc"])


@router.post("/ask")
async def calc_ask(payload: CalcAskRequest) -> StreamingResponse:
    """SSE coaching over the calculator, planned like Ask (see ``app.agent``).

    The state (sets, moves, field, hits, proposal + thread) comes with the question; types,
    stats and move data are re-read from the DB. Nothing is saved: Apply happens client-side.
    Events: ``plan`` (the calc context step first), ``step``*, ``view``* (damage, survive,
    build proposal and dex views), ``sources``, ``delta``*, ``done``.
    """

    async def event_stream() -> AsyncIterator[str]:
        planner = None
        try:
            async with async_session_factory() as session:
                state = await resolve_state(session, payload)
            ctx = AgentContext(scope="calc", extra={"calc": state})
            async for name, data in run_question(payload.question, "calc", ctx=ctx):
                if name == "plan" and planner is None:
                    planner = data["planner"]
                if name == "done":
                    # Log before `done`: the client stops reading at `done`.
                    await _log(payload.question, planner)
                yield _sse(name, data)
        except Exception as exc:  # noqa: BLE001 — surface as a stream error event
            log.exception("calc coaching failed")
            yield _sse("error", {"message": f"Coaching failed: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _log(question: str, planner: str | None) -> None:
    """Record the question for personalization ("calc-llm" / "calc-keyword")."""
    try:
        async with async_session_factory() as session:
            await personalize.log_question(session, question, f"calc-{planner or 'keyword'}")
    except Exception:  # noqa: BLE001 — history is a nicety; never fail the answer for it
        log.warning("couldn't log the calc question", exc_info=True)
