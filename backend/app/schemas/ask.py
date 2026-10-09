"""Schemas for the Ask (RAG) endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agent.views import View


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    n: int
    pokemon_id: int | None = None
    pokemon_name: str | None = None
    dex_number: int | None = None
    chunk_type: str
    source_ref: str | None = None
    snippet: str
    score: float
    # Which plan step produced it, and its index within that step's evidence, so a
    # view's step-local refs can be linked to the global [n].
    step: str | None = None
    step_index: int | None = None


class PlanStepOut(BaseModel):
    """One executed plan step with its final state."""

    id: str
    tool: str
    why: str = ""
    args: dict = Field(default_factory=dict)
    state: str = "pending"  # done | empty | error
    summary: str = ""
    replan: bool = False


class AskResponse(BaseModel):
    answer: str
    planner: str  # "llm" | "keyword"
    cached: bool = False
    steps: list[PlanStepOut] = Field(default_factory=list)
    # Typed result views (a union discriminated by "kind"), so clients can generate them.
    views: list[View] = Field(default_factory=list)
    sources: list[Source]
    usage: dict[str, int] = Field(default_factory=dict)
