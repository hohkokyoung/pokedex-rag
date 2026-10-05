"""Eval-as-regression: keyword-plan accuracy and retrieval recall must stay high.

Answer/citation/abstention grading needs an API key, so it is exercised by
`python -m eval.run` rather than asserted here.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from eval.harness import evaluate, summarize

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex",
)


@pytest.fixture
async def engine():
    eng = create_async_engine(DB_URL)
    try:
        async with async_sessionmaker(eng)() as s:
            count = (await s.execute(text("SELECT count(*) FROM knowledge_chunks"))).scalar()
            if not count:
                pytest.skip("knowledge_chunks not populated")
    except OperationalError:
        pytest.skip("Database not reachable")
    yield eng
    await eng.dispose()


async def test_eval_routing_and_recall(engine) -> None:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        results = await evaluate(session, use_llm=False)
    s = summarize(results)
    misses = [(r.case.id, r.tools) for r in results
              if r.case.expect_tools and not r.case.multi_part and not r.keyword_plan_ok]
    assert s["keyword_plan_accuracy"] == 1.0, f"keyword planner regressed: {misses}"
    assert s["fast_path_agreement"] == 1.0, "fast-path confidence changed on the eval set"
    assert s["retrieval_hit_rate"] >= 0.85, "retrieval recall dropped below 85%"


def test_every_case_expects_tools_or_abstains() -> None:
    from eval.dataset import CASES

    for case in CASES:
        assert case.expect_tools or case.abstain, case.id
        assert not case.multi_part or len(case.expect_tools) >= 1, case.id
    assert sum(c.multi_part for c in CASES) >= 14


async def test_coach_keyword_plans(engine) -> None:
    from eval.harness import evaluate_coach

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        results = await evaluate_coach(session, use_llm=False)
    misses = [(r.case.id, r.tools) for r in results if not r.case.abstain and not r.keyword_plan_ok]
    assert not misses, f"coach keyword planner regressed: {misses}"
    assert all(r.grounded for r in results), "team context missing"
    fast = [r for r in results if r.case.fast_path is not None]
    assert all(r.keyword_confident == r.case.fast_path for r in fast)


async def test_calc_keyword_plans(engine) -> None:
    from eval.harness import evaluate_calc

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        results = await evaluate_calc(session, use_llm=False)
    misses = [(r.case.id, r.tools) for r in results if not r.case.abstain and not r.keyword_plan_ok]
    assert not misses, f"calc keyword planner regressed: {misses}"
    assert all(r.grounded for r in results), "calc context missing"
    fast = [r for r in results if r.case.fast_path is not None]
    assert all(r.keyword_confident == r.case.fast_path for r in fast)
