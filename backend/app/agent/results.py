"""What a tool returns: citable evidence, views for the UI, and a one-line summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.agent.views import View
from app.rag.retrieval import RetrievedChunk

StepStatus = Literal["done", "empty", "error"]


@dataclass
class ToolResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    views: list[View] = field(default_factory=list)
    summary: str = ""
    status: StepStatus = "done"
    # Guidance for the answer model about how this evidence is laid out (was Resolved.note).
    note: str | None = None
    # Structured payload a code renderer needs (e.g. the StructuredQuery + match count).
    data: dict = field(default_factory=dict)
    # Overrides the tool's ``closed_form`` for this result (e.g. a learnset tool is
    # closed-form for a yes/no check but not for a full movepool).
    closed: bool | None = None

    @classmethod
    def empty(cls, summary: str) -> ToolResult:
        return cls(summary=summary, status="empty")

    @classmethod
    def error(cls, summary: str) -> ToolResult:
        return cls(summary=summary, status="error")
