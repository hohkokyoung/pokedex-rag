"""LLM planner: one structured call turns a question into a plan of tool steps.

Groq gets strict ``json_schema`` output and Anthropic a forced tool call, both with
the same schema: each step is an ``anyOf`` of per-tool step objects, so the tool name
and its arguments are constrained together. The prompt lists only each tool's name
and one-line description (the schema carries the argument shapes), with the fixed
text first so providers can cache it. Arguments are validated again server-side.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache

from pydantic import BaseModel

from app.agent import ask_tools  # noqa: F401 — registers the Ask tools
from app.agent.plan import MAX_STEPS, Plan, Step, build_plan
from app.agent.tools import Tool, tools_for
from app.rag import answer as answer_service

PLAN_MAX_TOKENS = 1200
REPLAN_MAX_TOKENS = 800
MAX_REPLAN_STEPS = 3

_RULES = """Rules:
- Use the fewest steps that fully answer the question: one step per distinct piece of \
information. Most questions need 1 step; multi-part questions need one per part.
- Put filters (types, legendary/mythical, physical/special, game, stat thresholds) in \
the tool's own args. Never chain steps to filter: steps cannot see each other's results, \
so leave "after" empty unless order matters.
- Use exact Pokémon, move, ability and item names as the user wrote them.
- Set a filter ONLY when the question states it; leave every other filter null or empty. \
legendary: false only for "non-legendary" / "no legendaries"; null means no constraint. \
Types are lowercase.
- Questions that aren't about Pokémon: one semantic_search step with the question.
- needs_followup is false unless the answer clearly needs another lookup you can't plan \
yet."""

_EXAMPLES = """Examples (only the args that matter shown):
Q: Which Pokémon has the highest Attack?
steps: query_pokemon(sort_by="attack", order="desc", limit=5)
Q: Which Fire types learn Will-O-Wisp?
steps: learnset(move="Will-O-Wisp", types=["fire"], legendary=null)
Q: Tell me about Psychic  ("Psychic" is a type AND a move: look up both)
steps: type_matchup(types=["psychic"]); move_info(name="Psychic")
Q: Which moves beat Garchomp, and what is Fire weak to?
steps: coverage_vs_types(against="Garchomp", want="moves"); type_matchup(types=["fire"])
Never supply a Pokémon's types or stats from memory: name it and let a tool look it up."""


# ---- schema ---------------------------------------------------------------------------


def _inline_refs(schema: dict) -> dict:
    """Inline ``$defs`` references (strict mode and small prompts both prefer it)."""
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(copy.deepcopy(defs[node["$ref"].split("/")[-1]]))
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


def _strict(node):
    """Strict-mode object rules: every property required, no extras, no titles/defaults."""
    if isinstance(node, list):
        return [_strict(v) for v in node]
    if not isinstance(node, dict):
        return node
    node = {k: _strict(v) for k, v in node.items() if k not in ("title", "default")}
    if node.get("type") == "object" or "properties" in node:
        node["type"] = "object"
        node.setdefault("properties", {})
        if node["properties"]:
            node["required"] = list(node["properties"])
        else:  # Groq rejects "required" next to an empty "properties"
            node.pop("required", None)
        node["additionalProperties"] = False
    return node


def args_schema(model: type[BaseModel]) -> dict:
    return _strict(_inline_refs(model.model_json_schema()))


def _step_schema(t: Tool) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "tool": {"type": "string", "enum": [t.name]},
            "why": {"type": "string"},
            "after": {"type": "array", "items": {"type": "string"}},
            "args": args_schema(t.args),
        },
        "required": ["id", "tool", "why", "after", "args"],
    }


@lru_cache
def plan_schema(scope: str) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "steps": {
                "type": "array",
                "items": {"anyOf": [_step_schema(t) for t in tools_for(scope)]},
            },
            "needs_followup": {"type": "boolean"},
        },
        "required": ["steps", "needs_followup"],
    }


@lru_cache
def system_prompt(scope: str) -> str:
    tools = "\n".join(f"- {t.name}: {t.description}" for t in tools_for(scope))
    return (
        "You plan data lookups for a Pokédex assistant. Reply with a plan: up to "
        f"{MAX_STEPS} steps, each one tool call with its args and a short why.\n\n"
        f"Tools:\n{tools}\n\n{_RULES}\n\n{_EXAMPLES}"
    )


def prompt_size(scope: str) -> int:
    """Characters sent per planning call: system text + schema (budget proxy)."""
    return len(system_prompt(scope)) + len(json.dumps(plan_schema(scope), separators=(",", ":")))


# ---- calls ----------------------------------------------------------------------------


async def _call(system: str, user: str, scope: str, max_tokens: int, usage) -> dict:
    schema = plan_schema(scope)
    raw = await answer_service.quick_complete(
        system, user, max_tokens=max_tokens, json_schema=schema, tool_schema=schema,
        reasoning_effort="low", cache_system=True, usage=usage, retry=False,
    )
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])


async def plan_llm(question: str, scope: str = "ask", *, usage=None) -> Plan:
    """The LLM's plan. Raises on provider errors (incl. 429) — the runner falls back."""
    data = await _call(system_prompt(scope), f"Question: {question}", scope,
                       PLAN_MAX_TOKENS, usage)
    return build_plan(
        list(data.get("steps") or []), "llm", scope=scope,
        needs_followup=bool(data.get("needs_followup")),
    )


def should_replan(plan: Plan, states: dict[str, str]) -> bool:
    """Only LLM plans re-plan: on an errored step or an explicit follow-up request."""
    if plan.planner != "llm":
        return False
    return plan.needs_followup or any(states.get(s.id) == "error" for s in plan.steps)


async def replan(
    question: str, plan: Plan, summaries: dict[str, tuple[str, str]], scope: str = "ask",
    *, usage=None,
) -> Plan:
    """Up to 3 added steps; never a repeat of a step that already succeeded."""
    lines = "\n".join(
        f"- {s.id} {s.tool}({json.dumps(s.args, ensure_ascii=False)}): "
        f"{summaries.get(s.id, ('error', s.error or ''))[0]} — "
        f"{summaries.get(s.id, ('', s.error or ''))[1]}"
        for s in plan.steps
    )
    user = (
        f"Question: {question}\n\nThis plan already ran:\n{lines}\n\n"
        f"Add at most {MAX_REPLAN_STEPS} NEW steps that fix the errors (e.g. a corrected name) "
        "or fetch what is still missing. Return no steps if nothing would help."
    )
    data = await _call(system_prompt(scope), user, scope, REPLAN_MAX_TOKENS, usage)
    taken = {s.id for s in plan.steps}
    done = {s.key() for s in plan.steps if summaries.get(s.id, ("",))[0] in ("done", "empty")}
    added = build_plan(
        list(data.get("steps") or []), "llm", scope=scope, id_prefix="r", taken=taken,
        limit=MAX_REPLAN_STEPS * 2,
    )
    fresh: list[Step] = [s for s in added.steps if s.key() not in done][:MAX_REPLAN_STEPS]
    for s in fresh:  # a re-plan step may only wait on steps that exist
        s.after = [a for a in s.after if a in taken or a in {f.id for f in fresh}]
    return Plan(steps=fresh, planner="llm")
