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

from app.agent import ask_tools, calc_tools, team_tools  # noqa: F401 — registers the Ask tools
from app.agent.plan import MAX_STEPS, Plan, Step, build_plan
from app.agent.tools import Tool, tools_for
from app.rag import answer as answer_service

PLAN_MAX_TOKENS = 1200
REPLAN_MAX_TOKENS = 800
MAX_REPLAN_STEPS = 3

_RULES = """Rules:
- Use the fewest steps: one per distinct piece of information. Most questions need 1 \
step; multi-part ones need one per part.
- Put filters (types, legendary/mythical, physical/special, game, learn method, stat \
thresholds) in \
the tool's own args. Never chain steps to filter: steps cannot see each other's results, \
so leave "after" empty unless order matters.
- Use Pokémon, move, ability and item names as written.
- Set a filter ONLY when the question states it; leave every other filter null or empty. \
legendary: false only for "non-legendary" / "no legendaries"; null means no constraint. \
Types are lowercase.
- needs_followup is false unless the answer clearly needs another lookup you can't plan \
yet.
- unhandled: stated constraints no tool arg can express, else []."""

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

_LORE_RULE = "\n- Questions that aren't about Pokémon: one semantic_search step with the question."

_TEAM_RULES = """Coach rules:
- The team, its analysis and any opponent matchup are ALREADY attached: plan only \
EXTRA lookups or actions; an empty plan is valid and common.
- add_member ONLY for an explicit command ("add Garchomp"); for "should I add …?" or \
"who should I add?" use recommend_additions.
- Set changes for a member ("give X a faster set", "what item should X hold?") -> \
propose_set_edit with the member's exact name and side ("theirs" for the opponent).
- Drafting additions -> recommend_additions with role and filters set."""

_TEAM_EXAMPLES = """Examples (only the args that matter shown):
Q: What's my team's biggest weakness?
steps: (none — the team analysis already answers it)
Q: Draft the rest of my team, no legendaries, I like sweepers
steps: recommend_additions(role="sweeper", legendary=false)
Q: Give Garchomp a faster set and tell me what beats Fairy types
steps: propose_set_edit(member="Garchomp", side="ours", request="a faster set"); \
coverage_vs_types(targets=["fairy"])"""


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


_CALC_RULES = """Calculator rules:
- The calculator's state (sets, field, the hits it shows) is ALREADY attached. Plan only \
extra calculations or lookups; an empty plan is valid.
- Damage / KO questions -> damage_calc; "with X" -> changes [{who, key, value}] \
(attacker unless the defender's item/EVs are meant). Survival -> survive_threshold. \
Builds and "make it …" -> propose_build with the user's words as request.
- Name calculator Pokémon exactly as listed; omit names to use the focused Pokémon."""

_CALC_EXAMPLES = """Examples (only the args that matter shown):
Q: Can Garchomp OHKO Salamence with Choice Band?
steps: damage_calc(attacker="Garchomp", defender="Salamence", \
changes=[{who:"attacker", key:"item", value:"Choice Band"}])
Q: How much Def does Salamence need to survive Earthquake?
steps: survive_threshold(defender="Salamence", move="Earthquake")
Q: Make it bulkier and tell me what Garchomp's Earthquake does now
steps: propose_build(request="make it bulkier"); damage_calc(attacker="Garchomp")"""


def calc_roster_line(st) -> str:
    """The calculator's Pokémon, sides and moves, so the planner names them exactly."""
    def one(m) -> str:
        return f"{m.name} [{m.move.name if m.move else 'no move'}]"
    yours = ", ".join(one(m) for m in st.members if m.side == 0) or "none"
    foes = ", ".join(one(m) for m in st.members if m.side == 1) or "none"
    focus = st.by_slot(st.focus)
    return (f"Calculator (Lv {st.level}, {'doubles' if st.doubles else 'singles'}): yours "
            f"{yours}; foe {foes}" + (f"; focused {focus.name}" if focus else ""))


def _scope_tools(scope: str) -> list[Tool]:
    return tools_for(scope, plannable_only=True)


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
                "items": {"anyOf": [_step_schema(t) for t in _scope_tools(scope)]},
            },
            "needs_followup": {"type": "boolean"},
            "unhandled": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["steps", "needs_followup", "unhandled"],
    }


@lru_cache
def system_prompt(scope: str) -> str:
    tools = "\n".join(f"- {t.name}: {t.description}" for t in _scope_tools(scope))
    if scope == "team":
        who = "a Pokémon team coach"
        rules, examples = f"{_RULES}\n\n{_TEAM_RULES}", _TEAM_EXAMPLES
    elif scope == "calc":
        who = "a damage calculator's coach"
        rules, examples = f"{_RULES}\n\n{_CALC_RULES}", _CALC_EXAMPLES
    else:
        who = "a Pokédex assistant"
        # Only Ask has lore search; the coach scopes answer off-topic questions from context.
        rules, examples = _RULES + _LORE_RULE, _EXAMPLES
    return (
        f"You plan data lookups for {who}. Reply with a plan: up to "
        f"{MAX_STEPS} steps, each one tool call with its args and a short why.\n\n"
        f"Tools:\n{tools}\n\n{rules}\n\n{examples}"
    )


def roster_line(team, opponent=None) -> str:
    """Who's on the teams, so the planner names members exactly (~60 tokens)."""
    line = "Your team: " + (", ".join(m.name for m in team.members) or "empty")
    if opponent is not None:
        line += "; Opponent: " + (", ".join(m.name for m in opponent.members) or "empty")
    return line


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


async def plan_llm(question: str, scope: str = "ask", *, usage=None, roster: str = "") -> Plan:
    """The LLM's plan. Raises on provider errors (incl. 429) — the runner falls back."""
    user = f"{roster}\nQuestion: {question}" if roster else f"Question: {question}"
    data = await _call(system_prompt(scope), user, scope, PLAN_MAX_TOKENS, usage)
    return build_plan(
        list(data.get("steps") or []), "llm", scope=scope,
        needs_followup=bool(data.get("needs_followup")),
        unhandled=list(data.get("unhandled") or []),
    )


def should_replan(plan: Plan, states: dict[str, str]) -> bool:
    """Only LLM plans re-plan: on an errored step or an explicit follow-up request."""
    if plan.planner != "llm":
        return False
    return plan.needs_followup or any(states.get(s.id) == "error" for s in plan.steps)


async def replan(
    question: str, plan: Plan, summaries: dict[str, tuple[str, str]], scope: str = "ask",
    *, usage=None, roster: str = "",
) -> Plan:
    """Up to 3 added steps; never a repeat of a step that already succeeded."""
    lines = "\n".join(
        f"- {s.id} {s.tool}({json.dumps(s.args, ensure_ascii=False)}): "
        f"{summaries.get(s.id, ('error', s.error or ''))[0]} — "
        f"{summaries.get(s.id, ('', s.error or ''))[1]}"
        for s in plan.steps
    )
    user = (
        (f"{roster}\n" if roster else "")
        + f"Question: {question}\n\nThis plan already ran:\n{lines}\n\n"
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
