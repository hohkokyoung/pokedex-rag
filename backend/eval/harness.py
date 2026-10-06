"""Evaluation harness: retrieval-plan accuracy, retrieval recall, LLM usage, and (with
a key) answer correctness, citation presence and abstention behaviour."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import cache, executor, llm_planner
from app.agent import runner as agent_runner
from app.agent.keyword_planner import plan_keywords
from app.agent.plan import Plan
from app.agent.runner import run_question
from app.api.ask import collect
from app.core.config import get_settings
from app.models import UserFavorite, UserProfile
from app.models.user import SOLE_PROFILE_ID
from app.rag import answer as answer_service
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import team_analysis
from app.services import teams as teams_service
from eval.dataset import (
    CALC_CASES,
    CALC_STATE,
    CASES,
    COACH_CASES,
    COACH_OPPONENT_TEAM,
    COACH_PLAYER_TEAM,
    CalcCase,
    CoachCase,
    EvalCase,
    ToolExpect,
)

_ABSTAIN_PHRASES = (
    "don't have", "do not have", "don't know", "do not know", "can't answer",
    "cannot answer", "no information", "not have that information", "isn't in",
    "is not in", "outside", "can't help", "cannot help", "not able to",
    "no relevant", "doesn't contain", "does not contain",
)


def is_abstention(answer: str) -> bool:
    low = answer.lower()
    return any(p in low for p in _ABSTAIN_PHRASES)


# ---- plan matching --------------------------------------------------------------------


def _norm(v):
    if isinstance(v, str):
        return v.strip().lower()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _arg_matches(want, got) -> bool:
    if isinstance(want, list):
        if not isinstance(got, list):
            return False
        if all(isinstance(w, dict) for w in want):  # each wanted dict ⊆ some actual one
            return all(any(_arg_matches(w, g) for g in got) for w in want)
        return {_norm(w) for w in want} == {_norm(g) for g in got}
    if isinstance(want, dict):
        return isinstance(got, dict) and all(
            k in got and _arg_matches(v, got[k]) for k, v in want.items()
        )
    return _norm(want) == _norm(got)


def _step_matches(expect: ToolExpect, tool: str, args: dict) -> bool:
    return tool in expect.tool.split("|") and all(
        k in args and _arg_matches(v, args[k]) for k, v in expect.args.items()
    )


def plan_matches(expects: list[ToolExpect], steps: list[tuple[str, dict]]) -> bool:
    """Every expected tool appears (with its key args); extra steps are allowed."""
    return all(any(_step_matches(e, t, a) for t, a in steps) for e in expects)


def _steps(plan: Plan) -> list[tuple[str, dict]]:
    return [(s.tool, s.parsed.model_dump() if s.parsed else s.args) for s in plan.valid_steps]


# ---- results --------------------------------------------------------------------------


@dataclass
class CaseResult:
    case: EvalCase
    keyword_plan_ok: bool
    keyword_confident: bool
    planner: str  # who planned the graded run: "llm" | "keyword"
    plan_ok: bool
    retrieval_hit: bool | None
    fallback: bool = False
    usage: dict[str, int] = field(default_factory=dict)
    answer_correct: bool | None = None
    citation_ok: bool | None = None
    abstained: bool | None = None
    tools: list[str] = field(default_factory=list)


async def _set_demo_profile(session: AsyncSession) -> tuple[list[str], list[int]]:
    """Set a temporary profile for personalized cases; return prior state."""
    profile = await session.get(UserProfile, SOLE_PROFILE_ID)
    prior_types = list(profile.preferred_types) if profile else []
    prior_favs = (await session.execute(select(UserFavorite.pokemon_id))).scalars().all()

    if profile is None:
        profile = UserProfile(id=SOLE_PROFILE_ID, preferred_types=[])
        session.add(profile)
    profile.preferred_types = ["fire", "dragon"]
    await session.execute(delete(UserFavorite))
    session.add(UserFavorite(pokemon_id=6))  # Charizard
    await session.commit()
    return prior_types, list(prior_favs)


async def _restore_profile(session: AsyncSession, types: list[str], favs: list[int]) -> None:
    profile = await session.get(UserProfile, SOLE_PROFILE_ID)
    if profile:
        profile.preferred_types = types
    await session.execute(delete(UserFavorite))
    for pid in favs:
        session.add(UserFavorite(pokemon_id=pid))
    await session.commit()


def _hit(case: EvalCase, evidence: list[tuple[str | None, int | None]]) -> bool | None:
    """``evidence`` = (pokemon name, dex number) per chunk/source, in order."""
    if case.expected_top1:
        return bool(evidence) and evidence[0][0] == case.expected_top1
    if case.expected_dex_any:
        return any(d in {dex for _, dex in evidence} for d in case.expected_dex_any)
    return None


async def _keyword_case(case: EvalCase, factory: Callable) -> CaseResult:
    async with factory() as s:
        kp = await plan_keywords(s, case.question)
    chunks = []
    async for ev in executor.run(kp.plan, factory):
        if ev.result is not None:
            chunks.append((ev.step.id, ev.result.chunks))
    order = {st.id: i for i, st in enumerate(kp.plan.steps)}
    evidence = [(c.pokemon_name, c.dex_number)
                for _, cs in sorted(chunks, key=lambda x: order[x[0]]) for c in cs]
    ok = plan_matches(case.expect_tools, _steps(kp.plan))
    return CaseResult(
        case, ok, kp.confident, "keyword", ok, _hit(case, evidence),
        tools=[s.tool for s in kp.plan.valid_steps],
    )


async def _llm_case(case: EvalCase, factory: Callable) -> CaseResult:
    async with factory() as s:
        kp = await plan_keywords(s, case.question)
    events = [e async for e in run_question(case.question, session_factory=factory)]
    out = collect(events)
    done = next(d for n, d in events if n == "done")
    steps = [(st.tool, st.args) for st in out.steps if st.state != "error"]
    answer = out.answer
    result = CaseResult(
        case, plan_matches(case.expect_tools, _steps(kp.plan)), kp.confident, out.planner,
        plan_matches(case.expect_tools, steps),
        _hit(case, [(s.pokemon_name, s.dex_number) for s in out.sources]),
        fallback=bool(done.get("fallback")), usage=out.usage,
        tools=[st.tool for st in out.steps],
    )
    if case.abstain:
        result.abstained = is_abstention(answer)
    else:
        if case.expected_substrings:
            result.answer_correct = all(
                s.lower() in answer.lower() for s in case.expected_substrings
            )
        # Accept ASCII [n] and fullwidth 【n】 (some models emit the latter).
        result.citation_ok = bool(re.search(r"[\[【]\d+[\]】]", answer))
    return result


async def _plans_only_case(case: EvalCase, factory: Callable) -> CaseResult:
    """The real planner selection and tools, without the answer call.

    The answer call is counted, not made: it happens exactly when the plan isn't
    closed-form (the runner's own rule), so ``llm_calls`` is exact; tokens cover
    planning only. A re-plan the runner would make is counted the same way.
    """
    async with factory() as s:
        kp = await plan_keywords(s, case.question)
    usage = answer_service.Usage()
    plan, fell_back = await agent_runner._choose_plan(case.question, "ask", factory, usage)
    run = agent_runner._Run(case.question, "ask", plan, usage, fallback=fell_back)
    async for ev in executor.run(plan, factory):
        if ev.result is not None:
            run.results[ev.step.id] = ev.result
    states = {sid: r.status for sid, r in run.results.items()}
    calls = usage.calls
    calls += int(llm_planner.should_replan(plan, states))
    calls += int(not agent_runner._closed_form(run))
    chunks = [c for st in plan.steps if (r := run.results.get(st.id)) for c in r.chunks]
    return CaseResult(
        case, plan_matches(case.expect_tools, _steps(kp.plan)), kp.confident, plan.planner,
        plan_matches(case.expect_tools, _steps(plan)),
        _hit(case, [(c.pokemon_name, c.dex_number) for c in chunks]),
        fallback=fell_back,
        usage={**usage.as_dict(), "llm_calls": calls},
        tools=[st.tool for st in plan.valid_steps],
    )


async def evaluate(
    session: AsyncSession, *, use_llm: bool, factory: Callable | None = None,
    tpm: int = 0, plans_only: bool = False,
) -> list[CaseResult]:
    """Run every case. Keyless: keyword plans + retrieval. With an LLM: the full Ask
    path (planner selection, tools, answer). ``tpm`` paces LLM cases to a provider's
    tokens-per-minute limit so the eval measures plans, not rate limiting."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = factory or async_sessionmaker(session.bind, expire_on_commit=False)
    prior = await _set_demo_profile(session)
    cache.plans.clear()
    cache.answers.clear()
    results: list[CaseResult] = []
    try:
        for case in CASES:
            if use_llm:
                r = await (_plans_only_case if plans_only else _llm_case)(case, factory)
                spent = r.usage.get("input_tokens", 0) + r.usage.get("output_tokens", 0)
                if tpm and spent:
                    await asyncio.sleep(60 * spent / tpm)
            else:
                r = await _keyword_case(case, factory)
            results.append(r)
    finally:
        await _restore_profile(session, *prior)
    return results


async def _pace(usage: dict, tpm: int) -> None:
    """Wait out the tokens just spent, so the next case measures plans, not rate limits."""
    spent = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    if tpm and spent:
        await asyncio.sleep(60 * spent / tpm)


def summarize(results: list[CaseResult]) -> dict:
    def rate(vals: list[bool | None]) -> float | None:
        xs = [v for v in vals if v is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    def avg(key: str) -> float | None:
        xs = [r.usage.get(key, 0) for r in results if r.usage]
        return round(sum(xs) / len(xs), 2) if xs else None

    graded = [r for r in results if r.case.expect_tools]
    single = [r for r in graded if not r.case.multi_part]
    fast = [r for r in results if r.case.fast_path is not None]
    return {
        "n": len(results),
        # keyword planner (always measured): single-part questions are its job
        "keyword_plan_accuracy": rate([r.keyword_plan_ok for r in single]),
        "fast_path_agreement": rate(
            [r.keyword_confident == r.case.fast_path for r in fast]),
        # the graded run's plan (LLM or fast path), split by who planned it
        "plan_accuracy_llm": rate([r.plan_ok for r in graded if r.planner == "llm"]),
        "plan_accuracy_fast_path": rate(
            [r.plan_ok for r in graded if r.planner == "keyword" and r.keyword_confident]),
        "multi_part_accuracy": rate([r.plan_ok for r in graded if r.case.multi_part]),
        "retrieval_hit_rate": rate([r.retrieval_hit for r in results]),
        "fallbacks": sum(r.fallback for r in results),
        "avg_llm_calls": avg("llm_calls"),
        "avg_input_tokens": avg("input_tokens"),
        "avg_output_tokens": avg("output_tokens"),
        "answer_correctness": rate([r.answer_correct for r in results]),
        "citation_rate": rate([r.citation_ok for r in results]),
        "abstention_rate": rate([r.abstained for r in results]),
        "llm_graded": any(r.answer_correct is not None or r.abstained is not None
                          for r in results),
    }


def llm_available() -> bool:
    return get_settings().llm_enabled


@dataclass
class CoachCaseResult:
    case: CoachCase
    grounded: bool
    keyword_plan_ok: bool
    keyword_confident: bool
    planner: str
    plan_ok: bool
    citation_ok: bool | None = None
    abstained: bool | None = None
    usage: dict[str, int] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    fallback: bool = False  # an LLM call failed (e.g. a 429) and the keyword plan stood in


async def _coach_ctx(session: AsyncSession, player_id: int, opponent_id: int | None):
    from app.agent.tools import AgentContext

    team = await teams_service.get_team(session, player_id)
    opp = await teams_service.get_team(session, opponent_id) if opponent_id else None
    analysis = await team_analysis.analyze(session, team, opp)
    return AgentContext(scope="team", team=team, opponent=opp, extra={"analysis": analysis})


async def evaluate_coach(
    session: AsyncSession, *, use_llm: bool, factory: Callable | None = None,
    plans_only: bool = False, tpm: int = 0,
) -> list[CoachCaseResult]:
    """Team-coach cases on the agent (scope "team") against fixed temporary teams.

    Keyless: the keyword plan and the team context only (adds run in card mode, so
    nothing is written). With an LLM: the full coach path, or ``plans_only`` without the
    answer call. The temporary teams are always deleted.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = factory or async_sessionmaker(session.bind, expire_on_commit=False)
    player = await teams_service.create_team(
        session, TeamCreate(name="__eval_player__", kind="player")
    )
    opponent = await teams_service.create_team(
        session, TeamCreate(name="__eval_opponent__", kind="opponent")
    )
    results: list[CoachCaseResult] = []
    try:
        for i, pid in enumerate(COACH_PLAYER_TEAM, start=1):
            await teams_service.set_slot(session, player.id, i, SlotUpdate(pokemon_id=pid))
        for i, pid in enumerate(COACH_OPPONENT_TEAM, start=1):
            await teams_service.set_slot(session, opponent.id, i, SlotUpdate(pokemon_id=pid))

        for case in COACH_CASES:
            ctx = await _coach_ctx(session, player.id, opponent.id if case.with_opponent else None)
            kp = await plan_keywords(session, case.question, "team", ctx)
            kw_ok = plan_matches(case.expect_tools, _steps(kp.plan))
            r = CoachCaseResult(case, False, kw_ok, kp.confident, "keyword", kw_ok,
                                tools=[s.tool for s in kp.plan.valid_steps])
            if use_llm and not plans_only:
                events = [e async for e in run_question(
                    case.question, "team", session_factory=factory, ctx=ctx)]
                out = collect(events)
                r.planner, r.usage = out.planner, out.usage
                r.fallback = bool(next(d for n, d in events if n == "done").get("fallback"))
                steps = [(s.tool, s.args) for s in out.steps
                         if s.state != "error" and s.tool != "team_context"]
                r.plan_ok = plan_matches(case.expect_tools, steps)
                r.tools = [s.tool for s in out.steps if s.tool != "team_context"]
                r.grounded = any(s.step == "ctx" for s in out.sources)
                if case.abstain:
                    r.abstained = is_abstention(out.answer)
                else:
                    r.citation_ok = bool(re.search(r"[\[【]\d+[\]】]", out.answer))
            else:
                usage = answer_service.Usage()
                if use_llm:  # plans only: real planner selection, no answer call
                    ctx.extra["usage"] = usage
                    plan, r.fallback = await agent_runner._choose_plan(
                        case.question, "team", factory, usage, ctx)
                    r.planner = plan.planner
                    r.plan_ok = plan_matches(case.expect_tools, _steps(plan))
                    r.tools = [s.tool for s in plan.valid_steps]
                else:
                    plan = kp.plan
                plan = agent_runner._with_context(plan, "team")
                run = agent_runner._Run(case.question, "team", plan, usage, ctx=ctx)
                async for ev in executor.run(plan, factory, ctx):  # adds: card mode
                    if ev.result is not None:
                        run.results[ev.step.id] = ev.result
                r.grounded = bool(run.results.get("ctx") and run.results["ctx"].chunks)
                if use_llm:
                    calls = usage.calls + int(not agent_runner._closed_form(run))
                    r.usage = {**usage.as_dict(), "llm_calls": calls}
            await _pace(r.usage, tpm)
            results.append(r)
    finally:
        await teams_service.delete_team(session, player.id)
        await teams_service.delete_team(session, opponent.id)
    return results


# ---- calc coach -----------------------------------------------------------------------


@dataclass
class CalcCaseResult:
    case: CalcCase
    grounded: bool
    keyword_plan_ok: bool
    keyword_confident: bool
    planner: str
    plan_ok: bool
    citation_ok: bool | None = None
    abstained: bool | None = None
    usage: dict[str, int] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    fallback: bool = False  # an LLM call failed (e.g. a 429) and the keyword plan stood in


async def evaluate_calc(
    session: AsyncSession, *, use_llm: bool, factory: Callable | None = None,
    plans_only: bool = False, tpm: int = 0,
) -> list[CalcCaseResult]:
    """Calculator-coach cases on the agent (scope "calc") against ``CALC_STATE``.

    Keyless and plans-only runs never execute ``propose_build`` (it is an LLM call): each
    one is counted as a call instead, so the count stays exact without spending tokens.
    Nothing is written — the calc coach has no saved state.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.agent.tools import REGISTRY, AgentContext
    from app.schemas.calc import CalcAskRequest
    from app.services.calc_state import resolve_state

    factory = factory or async_sessionmaker(session.bind, expire_on_commit=False)
    state = await resolve_state(session, CalcAskRequest(question="eval", **CALC_STATE))
    results: list[CalcCaseResult] = []
    for case in CALC_CASES:
        ctx = AgentContext(scope="calc", extra={"calc": state})
        kp = await plan_keywords(session, case.question, "calc", ctx)
        kw_ok = plan_matches(case.expect_tools, _steps(kp.plan))
        r = CalcCaseResult(case, False, kw_ok, kp.confident, "keyword", kw_ok,
                           tools=[s.tool for s in kp.plan.valid_steps])
        if use_llm and not plans_only:
            events = [e async for e in run_question(
                case.question, "calc", session_factory=factory, ctx=ctx)]
            out = collect(events)
            r.planner, r.usage = out.planner, out.usage
            r.fallback = bool(next(d for n, d in events if n == "done").get("fallback"))
            steps = [(s.tool, s.args) for s in out.steps
                     if s.state != "error" and s.tool != "calc_context"]
            r.plan_ok = plan_matches(case.expect_tools, steps)
            r.tools = [s.tool for s in out.steps if s.tool != "calc_context"]
            r.grounded = any(s.step == "ctx" for s in out.sources)
            if case.abstain:
                r.abstained = is_abstention(out.answer)
            elif not (r.tools and all(REGISTRY[t].closed_form for t in r.tools)):
                r.citation_ok = bool(re.search(r"[\[【]\d+[\]】]", out.answer))
        else:
            usage = answer_service.Usage()
            if use_llm:  # plans only: real planner selection, no build/answer call
                ctx.extra["usage"] = usage
                plan, r.fallback = await agent_runner._choose_plan(
                    case.question, "calc", factory, usage, ctx)
                r.planner = plan.planner
                r.plan_ok = plan_matches(case.expect_tools, _steps(plan))
                r.tools = [s.tool for s in plan.valid_steps]
            else:
                plan = kp.plan
            builds = sum(s.tool == "propose_build" for s in plan.valid_steps)
            plan = agent_runner._with_context(
                replace(plan, steps=[s for s in plan.steps if s.tool != "propose_build"]),
                "calc")
            run = agent_runner._Run(case.question, "calc", plan, usage, ctx=ctx)
            async for ev in executor.run(plan, factory, ctx):
                if ev.result is not None:
                    run.results[ev.step.id] = ev.result
            r.grounded = bool(run.results.get("ctx") and run.results["ctx"].chunks)
            if use_llm:
                rest = [s for s in plan.steps if s.id != "ctx"]
                closed = (bool(rest) and agent_runner._closed_form(run)) or (
                    builds and not rest)
                calls = usage.calls + builds + int(not closed)
                r.usage = {**usage.as_dict(), "llm_calls": calls}
        await _pace(r.usage, tpm)
        results.append(r)
    return results
