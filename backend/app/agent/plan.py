"""The plan format both planners produce: ordered tool steps, validated per tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.agent.tools import REGISTRY

Planner = Literal["llm", "keyword"]
MAX_STEPS = 6


@dataclass
class Step:
    id: str
    tool: str
    args: dict
    why: str = ""
    after: list[str] = field(default_factory=list)
    parsed: BaseModel | None = None  # validated args; None when invalid
    error: str | None = None  # why it can't run (unknown tool, bad args, …)

    def key(self) -> tuple[str, str]:
        """Identity for de-duplication: tool + canonical args."""
        dumped = self.parsed.model_dump_json() if self.parsed is not None else str(self.args)
        return self.tool, dumped

    def public(self) -> dict:
        return {"id": self.id, "tool": self.tool, "why": self.why, "args": self.args}


@dataclass
class Plan:
    steps: list[Step]
    planner: Planner
    needs_followup: bool = False
    cached: bool = False

    @property
    def valid_steps(self) -> list[Step]:
        return [s for s in self.steps if s.error is None]


def _clean(model: type[BaseModel], args: dict) -> dict:
    """Drop nulls for fields that don't accept None, so their defaults apply."""
    out = {}
    for k, v in (args or {}).items():
        f = model.model_fields.get(k)
        if f is None:
            continue
        if v is None and not _nullable(f.annotation):
            continue
        out[k] = v
    return out


def _colloquial(args: BaseModel) -> BaseModel:
    """"Non-legendary" colloquially excludes mythicals too (as ``nlfilters`` does)."""
    if getattr(args, "legendary", None) is False and getattr(args, "mythical", "-") is None:
        args.mythical = False
    return args


def _nullable(ann) -> bool:
    import types
    import typing

    origin = typing.get_origin(ann)
    return origin in (typing.Union, types.UnionType) and type(None) in typing.get_args(ann)


def make_step(
    sid: str, tool: str, args: dict, why: str = "", after: list[str] | None = None,
    *, scope: str = "ask", known: set[str] | None = None,
) -> Step:
    """Validate one step against the tool registry and its args model."""
    step = Step(id=sid, tool=tool, args=dict(args or {}), why=why, after=list(after or []))
    t = REGISTRY.get(tool)
    if t is None or scope not in t.scopes:
        step.error = f'unknown tool "{tool}"'
        return step
    dangling = [a for a in step.after if a not in (known or set())]
    if dangling:
        step.error = f"depends on unknown step {', '.join(dangling)}"
        return step
    try:
        step.parsed = _colloquial(t.args.model_validate(_clean(t.args, step.args)))
    except ValidationError as e:
        first = e.errors()[0]
        where = ".".join(str(p) for p in first.get("loc", ())) or "args"
        step.error = f"bad args ({where}: {first.get('msg', 'invalid')})"
    return step


def build_plan(
    raw_steps: list[dict], planner: Planner, *, scope: str = "ask",
    needs_followup: bool = False, id_prefix: str = "s", taken: set[str] | None = None,
    limit: int = MAX_STEPS,
) -> Plan:
    """Validate raw ``{id, tool, args, why, after}`` dicts into a Plan (at most ``limit``)."""
    steps: list[Step] = []
    known = set(taken or set())
    for raw in raw_steps[:limit]:
        sid = str(raw.get("id") or "").strip()
        if not sid or sid in known:
            sid = f"{id_prefix}{len(known) + 1}"
            while sid in known:
                sid += "'"
        step = make_step(
            sid, str(raw.get("tool", "")), raw.get("args") or {}, str(raw.get("why") or ""),
            raw.get("after") or [], scope=scope, known=known,
        )
        known.add(sid)
        steps.append(step)
    return Plan(steps=steps, planner=planner, needs_followup=needs_followup)
