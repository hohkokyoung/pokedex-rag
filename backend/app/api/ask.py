"""Ask pokérag: every question is answered from a retrieval plan (see ``app.agent``)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.runner import run_question
from app.agent.sse import _sources, _sse  # noqa: F401 — re-exported for teams.py
from app.core.database import async_session_factory
from app.rag import personalize
from app.schemas.ask import AskRequest, AskResponse, PlanStepOut, Source

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ask"])


async def _log(question: str, planner: str | None) -> None:
    """Record the question for personalization ("agent-llm" / "agent-keyword")."""
    try:
        async with async_session_factory() as session:
            await personalize.log_question(session, question, f"agent-{planner or 'keyword'}")
    except Exception:  # noqa: BLE001 — history is a nicety; never fail the answer for it
        log.warning("couldn't log the question", exc_info=True)


def collect(events: list[tuple[str, object]]) -> AskResponse:
    """Fold a run's events into one non-streaming response."""
    steps: dict[str, PlanStepOut] = {}
    planner, cached = "keyword", False
    views: list[dict] = []
    sources: list[Source] = []
    answer: list[str] = []
    usage: dict[str, int] = {}
    for name, data in events:
        if name == "plan":
            if not data.get("replan"):
                planner, cached = data["planner"], bool(data.get("cached"))
            for s in data["steps"]:
                steps[s["id"]] = PlanStepOut(
                    **{k: s[k] for k in ("id", "tool", "why", "args")},
                    replan=bool(data.get("replan")),
                    state="error" if s.get("error") else "pending",
                    summary=s.get("error") or "",
                )
        elif name == "step" and data["id"] in steps and data["state"] != "running":
            steps[data["id"]].state = data["state"]
            steps[data["id"]].summary = data["summary"]
        elif name == "view":
            views.append(data)
        elif name == "sources":
            sources = [Source(**s) for s in data]
        elif name == "delta":
            answer.append(data["text"])
        elif name == "done":
            usage = data["usage"]
    return AskResponse(
        answer="".join(answer), planner=planner, cached=cached, steps=list(steps.values()),
        views=views, sources=sources, usage=usage,
    )


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> AskResponse:
    events = [e async for e in run_question(payload.question)]
    out = collect(events)
    await _log(payload.question, out.planner)
    return out


@router.post("/ask/stream")
async def ask_stream(payload: AskRequest) -> StreamingResponse:
    """Server-Sent Events: ``plan``, ``step``*, ``view``*, ``sources``, ``delta``*, ``done``."""

    async def event_stream() -> AsyncIterator[str]:
        planner = None
        try:
            async for name, data in run_question(payload.question):
                if name == "plan" and planner is None:
                    planner = data["planner"]
                yield _sse(name, data)
        except Exception as exc:  # noqa: BLE001 — surface as a stream error event
            log.exception("ask failed")
            yield _sse("error", {"message": f"Generation failed: {exc}"})
            return
        await _log(payload.question, planner)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
