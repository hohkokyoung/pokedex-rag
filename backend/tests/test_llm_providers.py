"""Provider request shapes for structured output, and usage reporting (mocked clients)."""

from __future__ import annotations

import json
from types import SimpleNamespace as NS

import pytest

from app.core.config import Settings
from app.rag import answer

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"x": {"type": "integer"}}, "required": ["x"],
}


class _Recorder:
    def __init__(self, result):
        self.kwargs: dict = {}
        self.result = result
        self.options: dict = {}

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self.result


def _settings(monkeypatch, **kw):
    s = Settings(**{"anthropic_api_key": "", "groq_api_key": "", **kw})
    monkeypatch.setattr(answer, "get_settings", lambda: s)
    return s


async def test_groq_strict_schema_and_usage(monkeypatch):
    _settings(monkeypatch, groq_api_key="g", groq_model="openai/gpt-oss-120b")
    rec = _Recorder(NS(
        choices=[NS(message=NS(content='{"x": 1}'))],
        usage=NS(prompt_tokens=100, completion_tokens=20),
    ))
    client = NS(chat=NS(completions=rec))
    client.with_options = lambda **o: (rec.options.update(o), client)[1]
    monkeypatch.setattr(answer, "_groq", lambda: client)
    usage = answer.Usage()

    out = await answer.quick_complete(
        "sys", "q", json_schema=SCHEMA, tool_schema=SCHEMA, reasoning_effort="low", usage=usage,
        retry=False,
    )
    assert rec.options == {"max_retries": 0}

    assert json.loads(out) == {"x": 1}
    rf = rec.kwargs["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
    assert rf["json_schema"]["schema"] == SCHEMA
    assert rec.kwargs["reasoning_effort"] == "low"
    assert usage.as_dict() == {"llm_calls": 1, "input_tokens": 100, "output_tokens": 20}


async def test_groq_skips_reasoning_effort_on_other_models(monkeypatch):
    _settings(monkeypatch, groq_api_key="g", groq_model="llama-3.3-70b-versatile")
    rec = _Recorder(NS(choices=[NS(message=NS(content="{}"))], usage=None))
    monkeypatch.setattr(answer, "_groq", lambda: NS(chat=NS(completions=rec)))
    await answer.quick_complete("sys", "q", reasoning_effort="low")
    assert "reasoning_effort" not in rec.kwargs


async def test_anthropic_forced_tool_cached_system_and_usage(monkeypatch):
    _settings(monkeypatch, anthropic_api_key="a", anthropic_model="claude-x")
    rec = _Recorder(NS(
        content=[NS(type="tool_use", input={"x": 2})],
        usage=NS(input_tokens=300, output_tokens=40),
    ))
    monkeypatch.setattr(answer, "_anthropic", lambda: NS(messages=rec))
    usage = answer.Usage()

    out = await answer.quick_complete(
        "sys", "q", json_schema=SCHEMA, tool_schema=SCHEMA, cache_system=True, usage=usage
    )

    assert json.loads(out) == {"x": 2}
    assert rec.kwargs["tools"][0]["input_schema"] == SCHEMA
    assert rec.kwargs["tool_choice"] == {"type": "tool", "name": "submit"}
    assert rec.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "response_format" not in rec.kwargs
    assert usage.as_dict() == {"llm_calls": 1, "input_tokens": 300, "output_tokens": 40}


async def test_groq_stream_reports_usage_from_final_chunk(monkeypatch):
    _settings(monkeypatch, groq_api_key="g", groq_model="openai/gpt-oss-120b")

    async def chunks():
        yield NS(choices=[NS(delta=NS(content="Hi"))], usage=None, x_groq=None)
        yield NS(choices=[], usage=None,
                 x_groq=NS(usage=NS(prompt_tokens=50, completion_tokens=5)))

    class _Stream(_Recorder):
        async def create(self, **kwargs):
            self.kwargs = kwargs
            return chunks()

    monkeypatch.setattr(answer, "_groq", lambda: NS(chat=NS(completions=_Stream(None))))
    usage = answer.Usage()
    text = "".join([d async for d in answer.stream_answer("q", [], usage=usage)])
    assert text == "Hi"
    assert usage.as_dict() == {"llm_calls": 1, "input_tokens": 50, "output_tokens": 5}


@pytest.mark.parametrize("provider_err", ["groq", "anthropic"])
def test_is_rate_limited(provider_err):
    import anthropic
    import groq
    import httpx

    resp = httpx.Response(429, request=httpx.Request("POST", "https://x"))
    exc = (groq.RateLimitError if provider_err == "groq" else anthropic.RateLimitError)(
        "slow down", response=resp, body=None
    )
    assert answer.is_rate_limited(exc)
    assert not answer.is_rate_limited(RuntimeError("nope"))
