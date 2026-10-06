"""List recent plan traces, or show one in full.

    cd backend
    DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex \\
        uv run python -m app.agent.trace_cli [--scope ask|team|calc] [--planner …] \\
        [--fallback] [--limit 20] [--id N]

(or ``make traces ARGS="--fallback"``). Read-only; never calls an LLM.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Callable

from app.api.traces import summarize, traced_rows
from app.models import QuestionLog


def _line(r) -> str:
    when = r.created_at.strftime("%m-%d %H:%M")
    fb = f" !{r.fallback}" if r.fallback else ""
    tools = ",".join(r.tools) or "-"
    q = r.question if len(r.question) <= 60 else r.question[:59] + "…"
    return (f"{r.id:>6}  {when}  {r.scope or '?':<5} {r.planner or '?':<8}{fb:<16} "
            f"{r.llm_calls} call{'' if r.llm_calls == 1 else 's'}  {tools}  — {q}")


async def run(args: argparse.Namespace, session_factory: Callable) -> int:
    async with session_factory() as session:
        if args.id is not None:
            row = await session.get(QuestionLog, args.id)
            if row is None or row.trace is None:
                print(f"No trace for id {args.id}.")
                return 1
            print(f"#{row.id}  {row.created_at:%Y-%m-%d %H:%M:%S}  {row.route}\nQ: {row.question}")
            print(json.dumps(row.trace, indent=2, ensure_ascii=False))
            return 0
        fallback = True if args.fallback else None
        rows = (await session.execute(
            traced_rows(args.scope, args.planner, fallback, args.limit))).scalars().all()
        if not rows:
            print("No traces match.")
            return 0
        print(f"{'id':>6}  {'when':<11}  {'scope':<5} {'planner':<8}{'fallback':<16} calls  tools"
              "  — question")
        for row in rows:
            print(_line(summarize(row)))
        return 0


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="List recent plan traces, or show one in full.")
    ap.add_argument("--scope", choices=["ask", "team", "calc"])
    ap.add_argument("--planner", choices=["cached", "keyword", "llm"])
    ap.add_argument("--fallback", action="store_true", help="only questions that fell back")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--id", type=int, help="show this trace in full")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None, session_factory: Callable | None = None) -> int:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.config import get_settings

    args = parse(argv)
    if session_factory is not None:
        return asyncio.run(run(args, session_factory))

    async def go() -> int:
        engine = create_async_engine(get_settings().database_url)
        try:
            return await run(args, async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    return asyncio.run(go())


if __name__ == "__main__":
    raise SystemExit(main())
