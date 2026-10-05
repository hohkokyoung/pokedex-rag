"""One question, end to end: plan → run the tools → answer, as a stream of events.

Planner selection (cheapest first):
  answer cache → plan cache → keyword plan (always computed, free)
    no LLM / LLM planning off → keyword plan
    keyword plan is confident  → keyword plan            (fast path)
    otherwise                  → LLM plan, or the keyword plan if that call fails/429s

Answer tiers: code-rendered (every step closed-form) → LLM → extractive (no LLM, or
the answer call failed). Events: ``plan``, ``step``, ``view``, ``sources``, ``delta``,
``done``; the API layer frames them as SSE or collects them into one response.
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field

from app.agent import cache, executor, llm_planner, render
from app.agent.keyword_planner import is_imperative_add, plan_keywords
from app.agent.plan import Plan, Step, make_step
from app.agent.results import ToolResult
from app.agent.sse import _sources
from app.agent.tools import REGISTRY, AgentContext
from app.core.config import get_settings
from app.core.database import async_session_factory
from app.rag import answer as answer_service
from app.rag.retrieval import RetrievedChunk

log = logging.getLogger(__name__)

PLAN_TIMEOUT = 10.0
MAX_ANSWER_CHUNKS = 12
MAX_TEAM_ANSWER_CHUNKS = 16
CONTEXT_STEP = "ctx"  # the team coach's always-attached team context

Event = tuple[str, object]


@dataclass
class _Run:
    """What a run accumulated, for the answer step and the answer cache."""

    question: str
    scope: str
    plan: Plan
    usage: answer_service.Usage
    results: dict[str, ToolResult] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    fallback: bool = False  # an LLM call failed and something cheaper stood in
    profile: bool = False  # a step read the user's profile (never cache the answer)
    ctx: AgentContext | None = None


def _plan_event(steps: list[Step], plan: Plan, *, replan: bool = False) -> dict:
    return {
        "planner": plan.planner,
        "cached": plan.cached,
        "replan": replan,
        "steps": [{**s.public(), **({"error": s.error} if s.error else {})} for s in steps],
    }


def _cacheable(scope: str) -> bool:
    """Ask answers depend only on static data; coach answers depend on the (mutable) team."""
    return scope == "ask"


def _roster(ctx: AgentContext | None) -> str:
    if ctx is None or ctx.team is None:
        return ""
    return llm_planner.roster_line(ctx.team, ctx.opponent)


async def _choose_plan(
    question: str, scope: str, session_factory: Callable, usage: answer_service.Usage,
    ctx: AgentContext | None = None,
) -> tuple[Plan, bool]:
    """(plan, fell_back): the cheapest plan that will do."""
    settings = get_settings()
    cached = cache.plans.get(scope, question) if _cacheable(scope) else None
    if cached is not None:
        cached.cached = True
        return cached, False

    async with session_factory() as session:
        kp = await plan_keywords(session, question, scope, ctx)
    if not (settings.llm_enabled and settings.ask_agent_enabled) or kp.confident:
        return kp.plan, False

    try:
        plan = await asyncio.wait_for(
            llm_planner.plan_llm(question, scope, usage=usage, roster=_roster(ctx)),
            PLAN_TIMEOUT,
        )
    except Exception as exc:  # noqa: BLE001 — incl. 429 and timeouts: fall back, no retry
        kind = "rate-limited" if answer_service.is_rate_limited(exc) else type(exc).__name__
        log.info("LLM planning failed (%s); using the keyword plan", kind)
        return kp.plan, True
    # Team scope: an empty plan is a real answer (the team context covers it). Otherwise a
    # plan with no valid steps falls back to the keyword plan.
    empty_ok = scope == "team" and not plan.steps
    if not plan.valid_steps and not empty_ok:
        log.info("LLM plan had no valid steps; using the keyword plan")
        return kp.plan, True
    if _cacheable(scope):
        cache.plans.put(scope, question, plan)
    return plan, False


def _with_context(plan: Plan, scope: str) -> Plan:
    """Prepend the team context step (built in, never planned) for the coach."""
    if scope != "team" or any(s.tool == "team_context" for s in plan.steps):
        return plan
    ctx_step = make_step(CONTEXT_STEP, "team_context", {}, "read your team", scope="team")
    plan.steps.insert(0, ctx_step)
    return plan


async def _execute(
    run: _Run, plan: Plan, session_factory: Callable, ctx: AgentContext
) -> AsyncIterator[Event]:
    async for ev in executor.run(plan, session_factory, ctx):
        r = ev.result
        if r is not None:
            run.results[ev.step.id] = r
            run.profile = run.profile or bool(r.data.get("profile"))
        yield "step", {
            "id": ev.step.id,
            "state": ev.state,
            "summary": r.summary if r else "",
            "ms": round(ev.elapsed * 1000),
        }
        for view in (r.views if r else []):
            yield "view", {"step": ev.step.id, **view.model_dump(mode="json")}
        if r is not None and r.data.get("team_updated"):
            yield "team_updated", r.data["team_updated"]


def _evidence(run: _Run, *, cap: int | None) -> tuple[
    list[RetrievedChunk], list[tuple[str, int]], list[tuple[str, ToolResult, int]]
]:
    """Chunks in step order (deduplicated, optionally capped per step), their (step, index)
    refs, and each step's citation offset for code rendering."""
    with_chunks = [s for s in run.plan.steps if run.results.get(s.id) and run.results[s.id].chunks
                   and s.id != CONTEXT_STEP]
    quota = None
    if cap is not None and with_chunks:
        quota = max(3, math.ceil(cap / len(with_chunks)))
    chunks: list[RetrievedChunk] = []
    refs: list[tuple[str, int]] = []
    offsets: list[tuple[str, ToolResult, int]] = []
    seen: set[int] = set()
    for step in run.plan.steps:
        r = run.results.get(step.id)
        if r is None:
            continue
        offsets.append((step.tool, r, len(chunks)))
        taken = 0
        for i, c in enumerate(r.chunks):
            if quota is not None and taken >= quota and step.id != CONTEXT_STEP:
                break
            if c.id in seen:
                continue
            seen.add(c.id)
            chunks.append(c)
            refs.append((step.id, i))
            taken += 1
    if cap is not None:  # the team context never counts against the cap
        keep = cap + sum(1 for sid, _ in refs if sid == CONTEXT_STEP)
        chunks, refs = chunks[:keep], refs[:keep]
    return chunks, refs, offsets


def _closed_form(run: _Run) -> bool:
    steps = [s for s in run.plan.steps if s.id != CONTEXT_STEP]
    if not steps:
        return False
    for step in steps:
        r = run.results.get(step.id)
        if r is None or r.status == "error":
            return False
        closed = r.closed if r.closed is not None else REGISTRY[step.tool].closed_form
        if not closed:
            return False
    return True


def _note(run: _Run) -> str | None:
    parts = [r.note for s in run.plan.steps if (r := run.results.get(s.id)) and r.note]
    done = [
        f"{s.tool} ({run.results[s.id].summary})"
        for s in run.plan.steps if s.id in run.results and run.results[s.id].status != "error"
    ]
    if len(done) > 1:
        parts.append("NOTE: The evidence comes from these lookups, in order: "
                     + "; ".join(done) + ".")
    return "\n\n".join(parts) or None


def _no_llm_answer(run: _Run, chunks: list[RetrievedChunk], offsets) -> str:
    """The answer from data alone (no key, or the answer call failed)."""
    if run.scope != "team":
        return answer_service.compose_extractive_answer(chunks)
    from app.rag import coach

    parts = [t for tool, r, off in offsets
             if tool != "team_context" and r.status != "error"
             and (t := render.render_step(tool, r)) is not None]
    for s in run.plan.steps:  # say why an action didn't happen (e.g. needs an LLM key)
        r = run.results.get(s.id)
        if r is not None and r.status == "error" and s.tool in ("propose_set_edit", "duel"):
            what = "suggest a set" if s.tool == "propose_set_edit" else "play the duel"
            parts.append(f"Couldn't {what}: {r.summary}.")
    candidates = [c for r in run.results.values() for v in r.views
                  if getattr(v, "kind", "") == "candidates" for c in v.candidates]
    if candidates:
        parts.append(coach.compose_extractive_draft(candidates))
    elif not parts:
        if run.ctx is not None and run.ctx.report:
            parts.append(run.ctx.report)
        elif run.ctx is not None and run.ctx.extra.get("analysis") is not None:
            parts.append(coach.compose_extractive_coach(run.ctx.extra["analysis"]))
    return "\n\n".join(parts) or answer_service.compose_extractive_answer(chunks)


async def _answer(run: _Run) -> AsyncIterator[Event]:
    settings = get_settings()
    if _closed_form(run):
        chunks, refs, offsets = _evidence(run, cap=None)
        text = render.render_all([o for o in offsets if o[0] != "team_context"])
        if text is not None:
            yield "sources", [s.model_dump() for s in _sources(chunks, refs)]
            yield "delta", {"text": text}
            return

    cap = MAX_TEAM_ANSWER_CHUNKS if run.scope == "team" else MAX_ANSWER_CHUNKS
    chunks, refs, offsets = _evidence(run, cap=cap)
    yield "sources", [s.model_dump() for s in _sources(chunks, refs)]
    if not settings.llm_enabled:
        yield "delta", {"text": _no_llm_answer(run, chunks, offsets)}
        return

    streamed = False
    try:
        async for delta in answer_service.stream_answer(
            run.question, chunks, _note(run), usage=run.usage
        ):
            streamed = True
            yield "delta", {"text": delta}
    except Exception as exc:  # noqa: BLE001 — incl. 429: answer from the data instead
        kind = "rate-limited" if answer_service.is_rate_limited(exc) else type(exc).__name__
        log.info("LLM answer failed (%s); answering from the data", kind)
        run.fallback = True
        sep = "\n\n---\n\n" if streamed else ""
        yield "delta", {"text": sep + _no_llm_answer(run, chunks, offsets)}


async def run_question(
    question: str,
    scope: str = "ask",
    *,
    session_factory: Callable = async_session_factory,
    ctx: AgentContext | None = None,
) -> AsyncIterator[Event]:
    """Yield ``(event, data)`` pairs for one question."""
    ctx = ctx or AgentContext(scope=scope)
    usage = answer_service.Usage()
    ctx.extra["usage"] = usage  # tools that call an LLM (the build coach) count here
    # The add gate: only an explicit command may write; anything else gets an Add card.
    ctx.extra["allow_add"] = is_imperative_add(question)

    hit = cache.answers.get(scope, question) if _cacheable(scope) else None
    if hit is not None:
        for name, data in hit:
            if name == "plan" and not data.get("replan"):
                data = {**data, "cached": True}
            yield name, data
        yield "done", {"usage": answer_service.Usage().as_dict(), "fallback": False}
        return

    plan, fell_back = await _choose_plan(question, scope, session_factory, usage, ctx)
    plan = _with_context(plan, scope)
    run = _Run(question, scope, plan, usage, fallback=fell_back, ctx=ctx)

    async def emit(name: str, data: object) -> Event:
        run.events.append((name, data))
        return name, data

    yield await emit("plan", _plan_event(plan.steps, plan))
    async for name, data in _execute(run, plan, session_factory, ctx):
        yield await emit(name, data)

    settings = get_settings()
    states = {sid: r.status for sid, r in run.results.items()}
    if settings.llm_enabled and llm_planner.should_replan(plan, states):
        summaries = {sid: (r.status, r.summary) for sid, r in run.results.items()}
        try:
            added = await asyncio.wait_for(
                llm_planner.replan(question, plan, summaries, scope, usage=usage,
                                   roster=_roster(ctx)),
                PLAN_TIMEOUT,
            )
        except Exception:  # noqa: BLE001 — the first plan's evidence still answers
            log.info("re-plan failed; answering with what the first plan found", exc_info=True)
            run.fallback = True
            added = Plan(steps=[], planner="llm")
        if added.steps:
            plan.steps.extend(added.steps)
            yield await emit("plan", _plan_event(added.steps, plan, replan=True))
            async for name, data in _execute(run, added, session_factory, ctx):
                yield await emit(name, data)

    async for name, data in _answer(run):
        yield await emit(name, data)

    if _cacheable(scope) and not (run.fallback or run.profile):
        cache.answers.put(scope, question, run.events)
    log.info("ask %r planner=%s usage=%s", question, plan.planner, usage.as_dict())
    yield "done", {"usage": usage.as_dict(), "fallback": run.fallback}
