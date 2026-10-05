"""Grounded answer generation over retrieved context.

Provider-agnostic: prefers Anthropic Claude, falls back to Groq (OpenAI-compatible,
free tier) when only a Groq key is present. Both support non-streaming and SSE
streaming with the same call signatures.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from functools import lru_cache

import anthropic
import groq
from anthropic import AsyncAnthropic
from groq import AsyncGroq

from app.core.config import get_settings
from app.rag.retrieval import RetrievedChunk

SYSTEM_PROMPT = """You are the Pokédex research assistant. You answer ONLY questions \
about Pokémon, and ONLY using the numbered CONTEXT passages provided by the user.

Rules:
- Use ONLY the CONTEXT. Never use outside/world knowledge, even if you know the answer.
- If the question is not about Pokémon, or the CONTEXT does not contain the answer, \
reply briefly with something like: "I don't have that in the Pokédex data." Do NOT \
answer it anyway, do not guess, and do not add outside facts. This applies even to \
famous general-knowledge questions (capitals, sports, prices, current events).
- Cite the passages you use with ASCII square-bracket numbers like [1] or [2][3] \
(never fullwidth 【】 or other bracket styles), inline right after the claim they support.
- Past user questions (if any appear) are personalization hints only, never facts.
- Be concise, accurate, and friendly. Prefer specific numbers and names from the context.
- Shape every answer the same way:
  1. Open with ONE plain sentence (never a bullet, no heading) that directly answers \
the question, naming the key Pokémon and number, with its citation. E.g. \
"Kartana has the highest base Attack at 181 [1], 16 points ahead of Rampardos [2]."
  2. Then, only if there are further comparable items (a ranking, several matching \
Pokémon, a list of stats or abilities), add short Markdown bullets ("- "), one per \
line, each "**Name or label** — the value or a short detail [n]". For a ranking, \
continue down the list in order with each value. Don't repeat the opening item.
  Never answer with a single bullet. Keep it tight: no closing summary or filler.
- Keep [n] citations inline, right after the fact they support."""


# Room for a full answer. Groq's gpt-oss models reason before answering and those
# hidden reasoning tokens count against max_tokens, so 1024 cut longer answers off
# mid-bullet; low reasoning effort also keeps latency down for grounded answers.
ANSWER_MAX_TOKENS = 2048


def _groq_answer_kwargs() -> dict:
    model = get_settings().groq_model
    return {"reasoning_effort": "low"} if "gpt-oss" in model else {}


@dataclass
class Usage:
    """LLM calls and tokens spent on one question, summed across calls."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, input_tokens: int | None, output_tokens: int | None) -> None:
        self.calls += 1
        self.input_tokens += input_tokens or 0
        self.output_tokens += output_tokens or 0

    def as_dict(self) -> dict[str, int]:
        return {
            "llm_calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


def is_rate_limited(exc: BaseException) -> bool:
    """A provider 429 — callers fall back instead of retrying."""
    return isinstance(exc, groq.RateLimitError | anthropic.RateLimitError)


def _record_anthropic(usage: Usage | None, msg_usage) -> None:
    if usage is not None and msg_usage is not None:
        usage.add(msg_usage.input_tokens, msg_usage.output_tokens)


def _record_groq(usage: Usage | None, u) -> None:
    if usage is not None and u is not None:
        usage.add(u.prompt_tokens, u.completion_tokens)


@lru_cache
def _anthropic() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=get_settings().anthropic_api_key)


@lru_cache
def _groq() -> AsyncGroq:
    return AsyncGroq(api_key=get_settings().groq_api_key)


async def quick_complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 250,
    want_json: bool = False,
    json_schema: dict | None = None,
    tool_schema: dict | None = None,
    reasoning_effort: str | None = None,
    cache_system: bool = False,
    usage: Usage | None = None,
    retry: bool = True,
) -> str:
    """Small provider-aware completion (routers, planners, extractors).

    ``json_schema`` (Groq) requests strict schema-constrained structured output —
    the model's JSON is guaranteed to match the schema. ``tool_schema`` does the same
    on Anthropic: one forced tool call whose input is the schema, returned as JSON
    text. Pass both to get structured output whichever provider is active.
    ``reasoning_effort`` applies to Groq's gpt-oss models; ``cache_system`` marks
    Anthropic's system prompt cacheable (Groq caches shared prefixes on its own).
    ``usage`` collects the call's token counts. ``retry=False`` turns off the SDK's
    automatic retries, so a 429 surfaces at once and the caller can fall back.
    """
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        system_param: str | list[dict] = system
        if cache_system:
            system_param = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]
        kwargs: dict = {}
        if tool_schema is not None:
            kwargs["tools"] = [
                {
                    "name": "submit",
                    "description": "Submit the structured result.",
                    "input_schema": tool_schema,
                }
            ]
            kwargs["tool_choice"] = {"type": "tool", "name": "submit"}
        client = _anthropic() if retry else _anthropic().with_options(max_retries=0)
        msg = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system_param,
            messages=[{"role": "user", "content": user}],
            **kwargs,
        )
        _record_anthropic(usage, msg.usage)
        if tool_schema is not None:
            block = next((b for b in msg.content if b.type == "tool_use"), None)
            if block is not None:
                return json.dumps(block.input)
        return "".join(b.text for b in msg.content if b.type == "text")

    kwargs = {}
    schema = json_schema if json_schema is not None else tool_schema
    if schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "response", "strict": True, "schema": schema},
        }
    elif want_json:
        kwargs["response_format"] = {"type": "json_object"}
    if reasoning_effort and "gpt-oss" in settings.groq_model:
        kwargs["reasoning_effort"] = reasoning_effort
    client = _groq() if retry else _groq().with_options(max_retries=0)
    resp = await client.chat.completions.create(
        model=settings.groq_model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **kwargs,
    )
    _record_groq(usage, resp.usage)
    return resp.choices[0].message.content or ""


def build_context(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        # Non-Pokémon chunks (move, learner count, type chart) are tagged by what they
        # are, so the model doesn't cite them as vague "general data".
        tag = c.pokemon_name or {
            "move": f"move: {c.source_ref}",
            "learners": f"learners of {c.source_ref}",
            "type_chart": "type chart",
        }.get(c.chunk_type, "General")
        lines.append(f"[{i}] ({tag}) {c.content}")
    return "\n\n".join(lines)


def build_user_message(
    question: str, chunks: list[RetrievedChunk], personalization: str | None = None
) -> str:
    context = build_context(chunks) or "(no relevant passages found)"
    prefix = f"{personalization}\n\n" if personalization else ""
    return (
        f"{prefix}CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the context above, with inline [n] citations."
    )


def compose_extractive_answer(chunks: list[RetrievedChunk]) -> str:
    """Build an answer straight from retrieved data — no LLM.

    Used when no provider key is set, so basic Pokédex info is always available.
    Honest framing: it presents the most relevant records rather than claiming a
    narrated answer. Citations [n] line up with the source list.
    """
    if not chunks:
        return "I don't have anything in the Pokédex that matches that."

    top = chunks[:5]
    # Ranking-style structured results → a numbered list.
    if len(top) > 1 and all(c.chunk_type == "sql_row" for c in top):
        lines = [f"[{i}] {c.content}" for i, c in enumerate(top, start=1)]
        return "Straight from the Pokédex data:\n\n" + "\n".join(lines)

    # Otherwise lead with a profile if we have one, then add a dex entry or two.
    lead_idx, lead = next(
        ((i, c) for i, c in enumerate(chunks) if c.chunk_type == "profile"),
        (0, chunks[0]),
    )
    parts = [f"{lead.content} [{lead_idx + 1}]"]
    extras = [
        (i, c) for i, c in enumerate(chunks) if c is not lead and c.chunk_type == "dex_entry"
    ][:2]
    for i, c in extras:
        entry = c.content.split("Pokédex entry: ", 1)[-1]
        parts.append(f'Pokédex entry: "{entry}" [{i + 1}]')
    prefix = "(Showing facts straight from the Pokédex — add an LLM key for narrated answers.)\n\n"
    return prefix + " ".join(parts)


async def generate_answer(
    question: str, chunks: list[RetrievedChunk], personalization: str | None = None
) -> str:
    """Non-streaming grounded answer (Phase 3)."""
    settings = get_settings()
    user_msg = build_user_message(question, chunks, personalization)

    if settings.llm_provider == "anthropic":
        message = await _anthropic().messages.create(
            model=settings.anthropic_model,
            max_tokens=ANSWER_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        return "".join(block.text for block in message.content if block.type == "text")

    resp = await _groq().chat.completions.create(
        model=settings.groq_model,
        max_tokens=ANSWER_MAX_TOKENS,
        **_groq_answer_kwargs(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    return resp.choices[0].message.content or ""


async def stream_answer(
    question: str,
    chunks: list[RetrievedChunk],
    personalization: str | None = None,
    *,
    usage: Usage | None = None,
) -> AsyncIterator[str]:
    """Yield the grounded answer as text deltas (Phase 4, SSE); ``usage`` collects tokens."""
    settings = get_settings()
    user_msg = build_user_message(question, chunks, personalization)

    if settings.llm_provider == "anthropic":
        async with _anthropic().messages.stream(
            model=settings.anthropic_model,
            max_tokens=ANSWER_MAX_TOKENS,
            system=[
                {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
            final = await stream.get_final_message()
            _record_anthropic(usage, final.usage)
        return

    stream = await _groq().chat.completions.create(
        model=settings.groq_model,
        max_tokens=ANSWER_MAX_TOKENS,
        stream=True,
        **_groq_answer_kwargs(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    async for chunk in stream:
        # Groq reports usage on the final chunk (top level or under ``x_groq``).
        u = chunk.usage or getattr(getattr(chunk, "x_groq", None), "usage", None)
        if u is not None:
            _record_groq(usage, u)
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
