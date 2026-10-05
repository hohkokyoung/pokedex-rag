"""Run the evaluation and print a report.

    cd backend
    DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex \\
        uv run python -m eval.run [--keyless | --plans-only] [--tpm 8000]

Keyword-plan accuracy and retrieval run without an API key. With a key the full Ask
path runs per case — planner selection, tools, answer — and the report adds LLM plan
accuracy, fast-path accuracy, multi-part accuracy, fallbacks, LLM calls/tokens per
question, and answer / citation / abstention grading. ``--tpm`` paces LLM cases to the
provider's tokens-per-minute limit (Groq's free tier is ~8k for gpt-oss-120b), so the
eval measures plans rather than rate limiting; 0 disables pacing.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from eval.harness import evaluate, evaluate_coach, llm_available, summarize


def _mark(v: bool | None) -> str:
    return "·" if v is None else ("✓" if v else "✗")


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.0%}"


async def main(keyless: bool, tpm: int, plans_only: bool) -> None:
    use_llm = llm_available() and not keyless
    engine = create_async_engine(get_settings().database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        results = await evaluate(session, use_llm=use_llm, factory=factory, tpm=tpm,
                                 plans_only=plans_only)
        coach_results = await evaluate_coach(session, use_llm=use_llm and not plans_only)
    await engine.dispose()

    mode = "OFF — keyword planner only" if not use_llm else "plans only" if plans_only else "ON"
    print(f"\nPokédex RAG evaluation — {len(results)} cases (LLM: {mode})\n")
    if use_llm and plans_only:
        print("  plans-only: answer calls are counted (exactly), not made; "
              "tokens = planning only\n")
    print(f"{'id':<5}{'cat':<13}{'plan':<9}{'kw':<4}{'ok':<4}{'fast':<5}{'hit':<4}"
          f"{'calls':<6}{'ans':<4}{'cite':<5}{'abst':<5} question  → tools")
    print("-" * 110)
    for r in results:
        fast = "·" if r.case.fast_path is None else _mark(r.keyword_confident == r.case.fast_path)
        calls = str(r.usage.get("llm_calls", "")) + ("!" if r.fallback else "")
        print(
            f"{r.case.id:<5}{r.case.category:<13}{r.planner:<9}{_mark(r.keyword_plan_ok):<4}"
            f"{_mark(r.plan_ok):<4}{fast:<5}{_mark(r.retrieval_hit):<4}{calls:<6}"
            f"{_mark(r.answer_correct):<4}{_mark(r.citation_ok):<5}{_mark(r.abstained):<5} "
            f"{r.case.question}  → {', '.join(r.tools)}"
        )

    s = summarize(results)
    print("\nSummary")
    print("-" * 44)
    for key in ("keyword_plan_accuracy", "fast_path_agreement", "plan_accuracy_llm",
                "plan_accuracy_fast_path", "multi_part_accuracy", "retrieval_hit_rate",
                "answer_correctness", "citation_rate", "abstention_rate"):
        print(f"  {key:<24}: {_pct(s[key])}")
    print(f"  {'fallbacks (429/errors)':<24}: {s['fallbacks']}")
    for key in ("avg_llm_calls", "avg_input_tokens", "avg_output_tokens"):
        print(f"  {key:<24}: {'n/a' if s[key] is None else s[key]}")
    print()

    # ---- team coach ----
    print("Team Coach (grounded coaching path)")
    print("-" * 96)
    print(f"{'id':<4}{'grounded':<10}{'cite':<6}{'abst':<6} question")
    for r in coach_results:
        print(
            f"{r.case.id:<4}{_mark(r.grounded):<10}{_mark(r.citation_ok):<6}"
            f"{_mark(r.abstained):<6} {r.case.question}"
        )
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--keyless", action="store_true", help="keyword planner only, no LLM")
    ap.add_argument("--plans-only", action="store_true",
                    help="run planners + tools but not the answer call (cheaper on tokens)")
    ap.add_argument("--tpm", type=int, default=8000,
                    help="pace LLM cases to this tokens-per-minute limit (0 = no pacing)")
    args = ap.parse_args()
    asyncio.run(main(args.keyless, args.tpm, args.plans_only))
