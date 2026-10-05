"""Run a plan's steps: concurrently where independent, each with its own DB session.

Async SQLAlchemy sessions can't be shared between concurrent tasks, so every step
opens its own. A step waits only for the steps named in its ``after``; a failing or
slow step becomes an ``error`` result and never fails the others.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from app.agent.plan import Plan, Step
from app.agent.results import ToolResult
from app.agent.tools import REGISTRY, AgentContext

log = logging.getLogger(__name__)

STEP_TIMEOUT = 8.0


@dataclass
class StepEvent:
    step: Step
    state: str  # running | done | empty | error
    result: ToolResult | None = None
    elapsed: float = 0.0


async def _run_step(step: Step, session_factory: Callable, ctx: AgentContext,
                    timeout: float) -> ToolResult:
    tool = REGISTRY[step.tool]
    try:
        async with session_factory() as session:
            return await asyncio.wait_for(tool.handler(session, step.parsed, ctx), timeout)
    except TimeoutError:
        return ToolResult.error(f"timed out after {timeout:g}s")
    except Exception as exc:  # noqa: BLE001 — one tool failing must not fail the plan
        log.warning("tool %s failed", step.tool, exc_info=True)
        return ToolResult.error(f"failed: {type(exc).__name__}")


async def run(
    plan: Plan,
    session_factory: Callable,
    ctx: AgentContext | None = None,
    *,
    timeout: float = STEP_TIMEOUT,
) -> AsyncIterator[StepEvent]:
    """Yield each step's ``running`` and terminal events as they happen."""
    ctx = ctx or AgentContext()
    finished: set[str] = set()
    pending: list[Step] = []
    for step in plan.steps:
        if step.error is not None:
            finished.add(step.id)
            yield StepEvent(step, "error", ToolResult.error(step.error))
        else:
            pending.append(step)

    running: dict[asyncio.Task, tuple[Step, float]] = {}
    try:
        while pending or running:
            ready = [s for s in pending if all(a in finished for a in s.after)]
            for step in ready:
                pending.remove(step)
                task = asyncio.create_task(_run_step(step, session_factory, ctx, timeout))
                running[task] = (step, time.monotonic())
                yield StepEvent(step, "running")
            if not running:  # remaining steps wait on each other: a cycle
                for step in pending:
                    finished.add(step.id)
                    yield StepEvent(step, "error", ToolResult.error("circular dependency"))
                break
            done, _ = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                step, started = running.pop(task)
                result = task.result()
                finished.add(step.id)
                yield StepEvent(step, result.status, result, time.monotonic() - started)
    finally:
        for task in running:
            task.cancel()
