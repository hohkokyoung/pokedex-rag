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
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field, replace

from app.agent import cache, executor, llm_planner, render
from app.agent import trace as plan_trace
from app.agent.keyword_planner import KeywordPlan, is_imperative_add, plan_keywords
from app.agent.plan import Plan, Step, make_step
from app.agent.results import ToolResult
from app.agent.sse import _sources
from app.agent.tools import REGISTRY, AgentContext
from app.core.config import get_settings
from app.core.database import async_session_factory
from app.rag import answer as answer_service
from app.rag import matchup
from app.rag.retrieval import RetrievedChunk

log = logging.getLogger(__name__)

PLAN_TIMEOUT = 10.0
MAX_ANSWER_CHUNKS = 12
MAX_TEAM_ANSWER_CHUNKS = 16
CONTEXT_STEP = "ctx"  # a coach's always-attached context step
CONTEXT_TOOLS = {"team": "team_context", "calc": "calc_context"}

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
    # For the trace: how the answer was produced, and what a re-plan added or why it failed.
    answer_tier: str | None = None  # code | llm | no-llm | abstain
    answer_fallback: str | None = None  # why the LLM answer was replaced (rate-limited | <Type>)
    replan_steps: list[Step] = field(default_factory=list)
    replan_error: str | None = None


def _plan_event(steps: list[Step], plan: Plan, *, replan: bool = False) -> dict:
    return {
        "planner": plan.planner,
        "cached": plan.cached,
        "replan": replan,
        "steps": [{**s.public(), **({"error": s.error} if s.error else {})} for s in steps],
        **({"unhandled": plan.unhandled} if plan.unhandled and not replan else {}),
    }


def _gap_note(plan: Plan) -> str | None:
    """Say what the plan couldn't filter by, so a broader answer isn't read as the asked one."""
    if not plan.unhandled:
        return None
    return (f"*Note: this part couldn't be applied — {'; '.join(plan.unhandled)}. The "
            "results below answer a broader question.*\n\n")


def _cacheable(scope: str) -> bool:
    """Ask answers depend only on static data; coach answers depend on mutable state."""
    return scope == "ask"


def _roster(ctx: AgentContext | None) -> str:
    if ctx is not None and ctx.extra.get("calc") is not None:
        return llm_planner.calc_roster_line(ctx.extra["calc"])
    if ctx is None or ctx.team is None:
        return ""
    return llm_planner.roster_line(ctx.team, ctx.opponent)


@dataclass
class PlanChoice:
    """The plan to run, and how it was chosen (recorded in the question's trace)."""

    plan: Plan
    fell_back: bool = False  # the LLM was asked but the keyword plan stood in
    keyword: KeywordPlan | None = None  # None only for a cached plan
    llm_plan: Plan | None = None  # the LLM's plan, also when it was rejected
    skip_llm: str | None = None  # "fast-path" | "no-llm" — why the LLM wasn't asked
    # rate-limited | timeout | provider-error:<Type> | no-valid-steps
    fallback_reason: str | None = None
    corrected: list[str] = field(default_factory=list)  # LLM args code overrode


def _failure(exc: BaseException) -> str:
    if answer_service.is_rate_limited(exc):
        return "rate-limited"
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return "timeout"
    return f"provider-error:{type(exc).__name__}"


async def _choose_plan(
    question: str, scope: str, session_factory: Callable, usage: answer_service.Usage,
    ctx: AgentContext | None = None,
) -> PlanChoice:
    """The cheapest plan that will do, and why it was picked."""
    settings = get_settings()
    cached = cache.plans.get(scope, question) if _cacheable(scope) else None
    if cached is not None:
        cached.cached = True
        return PlanChoice(cached)

    async with session_factory() as session:
        kp = await plan_keywords(session, question, scope, ctx)
    if not (settings.llm_enabled and settings.ask_agent_enabled):
        return PlanChoice(kp.plan, keyword=kp, skip_llm="no-llm")
    if kp.confident:
        return PlanChoice(kp.plan, keyword=kp, skip_llm="fast-path")

    try:
        plan = await asyncio.wait_for(
            llm_planner.plan_llm(question, scope, usage=usage, roster=_roster(ctx)),
            PLAN_TIMEOUT,
        )
    except Exception as exc:  # noqa: BLE001 — incl. 429 and timeouts: fall back, no retry
        reason = _failure(exc)
        log.info("LLM planning failed (%s); using the keyword plan", reason)
        return PlanChoice(kp.plan, fell_back=True, keyword=kp, fallback_reason=reason)
    # Coach scopes: an empty plan is a real answer (the context covers it). So is one that
    # says nothing can express the question (``unhandled``): falling back would answer a
    # broader question as if it were this one. Otherwise no valid steps → the keyword plan.
    empty_ok = (scope in CONTEXT_TOOLS or bool(plan.unhandled)) and not plan.steps
    if not plan.valid_steps and not empty_ok:
        log.info("LLM plan had no valid steps; using the keyword plan")
        return PlanChoice(kp.plan, fell_back=True, keyword=kp, llm_plan=plan,
                          fallback_reason="no-valid-steps")
    run_plan, corrected = _pin_coverage_want(plan, question, scope)
    if _cacheable(scope):
        cache.plans.put(scope, question, run_plan)
    return PlanChoice(run_plan, keyword=kp, llm_plan=plan, corrected=corrected)


def _pin_coverage_want(plan: Plan, question: str, plan_scope: str) -> tuple[Plan, list[str]]:
    """Whether coverage lists Pokémon or moves is the question's call, not the LLM's.

    The planner LLM drifts on it ("which special attacker has coverage…" came back as
    moves once, and the plan cache then kept it), so the keyword rule decides. Returns
    a corrected copy, leaving ``plan`` (the LLM's own, kept for the trace) untouched.
    """
    want = "moves" if matchup.wants_moves(question) else "pokemon"
    steps, notes = [], []
    for s in plan.steps:
        if s.tool == "coverage_vs_types" and s.parsed is not None and s.parsed.want != want:
            notes.append(f"{s.id}.want {s.parsed.want}->{want}")
            s = make_step(s.id, s.tool, {**s.args, "want": want}, s.why, s.after,
                          scope=plan_scope, known=set(s.after))
        steps.append(s)
    if not notes:
        return plan, []
    return replace(plan, steps=steps), notes


def _with_context(plan: Plan, scope: str) -> Plan:
    """Prepend the coach's context step (built in, never planned): the team or calculator."""
    tool = CONTEXT_TOOLS.get(scope)
    if tool is None or any(s.tool == tool for s in plan.steps):
        return plan
    why = "read your team" if scope == "team" else "read the calculator"
    ctx_step = make_step(CONTEXT_STEP, tool, {}, why, scope=scope)
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
    if run.plan.unhandled:
        parts.append("NOTE: The lookups could NOT apply: " + "; ".join(run.plan.unhandled)
                     + ". The answer already opens with a line saying so; don't claim the "
                     "results satisfy it.")
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
    if run.scope not in CONTEXT_TOOLS:
        return answer_service.compose_extractive_answer(chunks)
    from app.rag import coach

    parts = [t for tool, r, off in offsets
             if tool not in CONTEXT_TOOLS.values() and r.status != "error"
             and (t := render.render_step(tool, r)) is not None]
    actions = {"propose_set_edit": "suggest a set", "duel": "play the duel",
               "propose_build": "suggest a build", "damage_calc": "calculate that",
               "survive_threshold": "work out the bulk needed"}
    for s in run.plan.steps:  # say why an action didn't happen (e.g. needs an LLM key)
        r = run.results.get(s.id)
        if r is not None and r.status == "error" and s.tool in actions:
            parts.append(f"Couldn't {actions[s.tool]}: {r.summary}.")
    if run.scope == "calc":
        if not parts:  # plain question, no LLM: the calculator's own numbers
            parts = [c.content for c in chunks if c.chunk_type == "calc_hits"][:1]
        return "\n\n".join(parts) or answer_service.compose_extractive_answer(chunks)
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
    """The answer events, opening with the plan's gap note (if any) on the first delta."""
    if run.plan.unhandled and not run.plan.steps and run.scope not in CONTEXT_TOOLS:
        # Nothing could be looked up: say what's missing instead of guessing (no LLM call).
        run.answer_tier = "abstain"
        yield "sources", []
        yield "delta", {"text": "I can't answer that from the Pokédex data — no lookup can "
                        f"apply: {'; '.join(run.plan.unhandled)}."}
        return
    note = _gap_note(run.plan)
    async for name, data in _answer_body(run):
        if name == "delta" and note:
            data, note = {"text": note + data["text"]}, None
        yield name, data


async def _answer_body(run: _Run) -> AsyncIterator[Event]:
    settings = get_settings()
    if _closed_form(run):
        chunks, refs, offsets = _evidence(run, cap=None)
        text = render.render_all([o for o in offsets if o[0] not in CONTEXT_TOOLS.values()])
        if text is not None:
            run.answer_tier = "code"
            yield "sources", [s.model_dump() for s in _sources(chunks, refs)]
            yield "delta", {"text": text}
            return

    cap = MAX_TEAM_ANSWER_CHUNKS if run.scope in CONTEXT_TOOLS else MAX_ANSWER_CHUNKS
    chunks, refs, offsets = _evidence(run, cap=cap)
    yield "sources", [s.model_dump() for s in _sources(chunks, refs)]
    if not settings.llm_enabled:
        run.answer_tier = "no-llm"
        yield "delta", {"text": _no_llm_answer(run, chunks, offsets)}
        return

    streamed = False
    run.answer_tier = "llm"
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
        run.answer_tier, run.answer_fallback = "no-llm", kind
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
    t0 = time.perf_counter()
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
        ctx.extra["trace"] = plan_trace.cached(scope, (time.perf_counter() - t0) * 1000)
        yield "done", {"usage": answer_service.Usage().as_dict(), "fallback": False}
        return

    choice = await _choose_plan(question, scope, session_factory, usage, ctx)
    plan = _with_context(choice.plan, scope)
    run = _Run(question, scope, plan, usage, fallback=choice.fell_back, ctx=ctx)

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
        except Exception as exc:  # noqa: BLE001 — the first plan's evidence still answers
            log.info("re-plan failed; answering with what the first plan found", exc_info=True)
            run.fallback = True
            run.replan_error = _failure(exc)
            added = Plan(steps=[], planner="llm")
        run.replan_steps = list(added.steps)
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
    try:  # the trace is a record of the run; building it must never cost the answer
        ctx.extra["trace"] = plan_trace.build(choice, run, (time.perf_counter() - t0) * 1000)
    except Exception:  # noqa: BLE001
        log.warning("couldn't build the plan trace", exc_info=True)
    yield "done", {"usage": usage.as_dict(), "fallback": run.fallback}
