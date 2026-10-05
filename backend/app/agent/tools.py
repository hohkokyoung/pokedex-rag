"""Tool registry: each tool is a thin, read-only adapter over existing retrieval code.

A tool declares the scopes it serves ("ask" now; "team"/"calc" later), a one-line
description for the planner, a Pydantic args model (validated server-side, whatever
the planner sent), and whether its result is *closed-form* — complete enough to be
answered by code with no LLM.

Handlers get the validated args plus an ``AgentContext``; they never see the user's
question, so the LLM and keyword planners behave the same for the same arguments.
"""

from __future__ import annotations

import types
import typing
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, get_args, get_origin

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.results import ToolResult


@dataclass
class AgentContext:
    """Per-request context a handler may use (never the question text)."""

    scope: str = "ask"
    extra: dict[str, Any] = field(default_factory=dict)


Handler = Callable[[AsyncSession, Any, AgentContext], Awaitable[ToolResult]]


@dataclass(frozen=True)
class Tool:
    name: str
    scopes: frozenset[str]
    description: str  # one line, shown to the planner
    args: type[BaseModel]
    handler: Handler
    closed_form: bool = False


REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    REGISTRY[tool.name] = tool
    return tool


def tool(
    name: str,
    *,
    scopes: tuple[str, ...] = ("ask",),
    description: str,
    args: type[BaseModel],
    closed_form: bool = False,
) -> Callable[[Handler], Handler]:
    """Decorator form of ``register``."""

    def wrap(fn: Handler) -> Handler:
        register(Tool(name, frozenset(scopes), description, args, fn, closed_form))
        return fn

    return wrap


def tools_for(scope: str) -> list[Tool]:
    """Tools available in a scope, in registration order."""
    return [t for t in REGISTRY.values() if scope in t.scopes]


# ---- compact signatures for the planner prompt ---------------------------------------


def _type_str(ann: Any) -> str:
    origin = get_origin(ann)
    if origin is Literal:
        return "|".join(str(a) for a in get_args(ann))
    if origin in (typing.Union, types.UnionType):
        inner = [a for a in get_args(ann) if a is not type(None)]
        return "|".join(_type_str(a) for a in inner)
    if origin is list:
        (item,) = get_args(ann) or (Any,)
        return f"[{_type_str(item)}]"
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return "{" + ",".join(ann.model_fields) + "}"
    return getattr(ann, "__name__", str(ann))


def signature(t: Tool) -> str:
    """``name(arg: type, opt?: type)`` — one line per tool keeps the prompt small."""
    parts = []
    for fname, f in t.args.model_fields.items():
        opt = "" if f.is_required() else "?"
        parts.append(f"{fname}{opt}: {_type_str(f.annotation)}")
    return f"{t.name}({', '.join(parts)})"
