"""Plan traces: a per-question record of how the assistant planned and answered.

The runner builds one at ``done`` (planner choice, fallback reasons, the keyword and LLM
plans, step outcomes, answer tier, usage) and leaves it in ``ctx.extra["trace"]``; the API
routes store it with the question log. Nothing here calls an LLM or changes an answer.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from sqlalchemy import text

if TYPE_CHECKING:
    from app.agent.plan import Plan, Step
    from app.agent.runner import PlanChoice, _Run

log = logging.getLogger(__name__)

VERSION = 1
_WHY = 200  # characters kept of a step's reason or summary
_ARG = 300  # characters kept of one argument value
_STEPS = 12  # steps kept per plan


def _clip(s: str | None, n: int) -> str | None:
    if s is None:
        return None
    return s if len(s) <= n else s[: n - 1] + "…"


def _value(v: Any) -> Any:
    if isinstance(v, BaseModel):
        v = v.model_dump(mode="json")
    if isinstance(v, str):
        return _clip(v, _ARG)
    if isinstance(v, list):
        return [_value(x) for x in v[:20]]
    if isinstance(v, dict):
        return {k: _value(x) for k, x in v.items() if x is not None and x != []}
    return v


def _args(step: Step) -> dict:
    raw = step.parsed.model_dump(mode="json") if step.parsed is not None else (step.args or {})
    return _value(raw)


def _steps(steps: list[Step]) -> list[dict]:
    """A plan's own steps. The coach context step is added by the runner, not planned, so it
    only appears among the executed ``steps``."""
    from app.agent.runner import CONTEXT_STEP

    out = []
    for s in [x for x in steps if x.id != CONTEXT_STEP][:_STEPS]:
        d = {"tool": s.tool, "args": _args(s), "why": _clip(s.why, _WHY)}
        if s.error:
            d["error"] = _clip(s.error, _WHY)
        out.append(d)
    return out


def _plan(plan: Plan | None, *, llm: bool = False) -> dict | None:
    if plan is None:
        return None
    d: dict[str, Any] = {"steps": _steps(plan.steps)}
    if llm:
        d["unhandled"] = list(plan.unhandled)
        d["needs_followup"] = plan.needs_followup
    return d


def build(choice: PlanChoice, run: _Run, ms: float) -> dict:
    """The version-1 trace for a finished run."""
    timings: dict[str, int] = {}
    for name, data in run.events:
        if name == "step" and isinstance(data, dict) and data.get("state") not in (None,
                                                                                   "running"):
            timings[data["id"]] = int(data.get("ms") or 0)
    steps = []
    for s in run.plan.steps[: _STEPS * 2]:
        r = run.results.get(s.id)
        steps.append({
            "id": s.id, "tool": s.tool,
            "state": r.status if r is not None else ("error" if s.error else "skipped"),
            "summary": _clip(r.summary if r is not None else s.error, _WHY),
            "ms": timings.get(s.id, 0),
        })
    kp = choice.keyword
    return {
        "v": VERSION,
        "scope": run.scope,
        "ms": int(ms),
        "planner": "cached" if choice.plan.cached else choice.plan.planner,
        "skip_llm": choice.skip_llm,
        "fallback": choice.fallback_reason,
        "keyword": (
            {"confident": kp.confident, **(_plan(kp.plan) or {})} if kp is not None else None
        ),
        "llm": _plan(choice.llm_plan, llm=True),
        "corrected": choice.corrected or None,
        "replan": (
            {"steps": _steps(run.replan_steps), "error": run.replan_error}
            if run.replan_steps or run.replan_error else None
        ),
        "steps": steps,
        "answer": {"tier": run.answer_tier, "fallback": run.answer_fallback},
        "usage": run.usage.as_dict(),
    }


def cached(scope: str, ms: float) -> dict:
    """A repeated question answered from the answer cache: no planning, no LLM."""
    return {
        "v": VERSION, "scope": scope, "ms": int(ms), "planner": "cached", "skip_llm": None,
        "fallback": None, "keyword": None, "llm": None, "replan": None, "steps": [],
        "answer": {"tier": "cached", "fallback": None},
        "usage": {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0},
    }


# ---- storing ------------------------------------------------------------------------------

# Clear the trace on every row older than the newest ``n`` traced ones (questions stay).
_PRUNE = text("""
    UPDATE question_log SET trace = NULL
    WHERE trace IS NOT NULL AND id < (
        SELECT id FROM question_log WHERE trace IS NOT NULL
        ORDER BY id DESC OFFSET :skip LIMIT 1
    )
""")


async def record(
    question: str, route: str, trace: dict | None, *,
    session_factory: Callable | None = None, retention: int | None = None,
) -> None:
    """Log the question with its trace, then apply retention. Best-effort: never raises."""
    from app.core.config import get_settings
    from app.core.database import async_session_factory
    from app.rag import personalize

    try:
        async with (session_factory or async_session_factory)() as session:
            await personalize.log_question(session, question, route, trace)
            if trace is not None:
                keep = retention if retention is not None else get_settings().trace_retention
                await session.execute(_PRUNE, {"skip": max(keep, 1) - 1})
                await session.commit()
    except Exception:  # noqa: BLE001 — history is a nicety; never fail the answer for it
        log.warning("couldn't log the question and its trace", exc_info=True)
