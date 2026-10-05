"""Keyword planner: a retrieval plan without an LLM.

Names first — every Pokémon, form, move and type mentioned is resolved against the
data — then cues pick the tools. That is what keeps "What does Earthquake do?" on
the move instead of falling through to a lore search, and lets "Psychic" (a type
*and* a move) plan both lookups.

It runs for every question: it's the whole plan when no LLM is available, and the
fast path when its plan is ``confident`` (one unambiguous name in a simple, fixed
phrasing), which skips the LLM planner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import (
    ask_tools,  # noqa: F401 — registers the tools validated below
    names,
)
from app.agent.plan import Plan, build_plan
from app.rag import learnset, matchup, personalize, similarity, sql_retrieval
from app.services import nlfilters

MAX_KEYWORD_STEPS = 3

# Description / lore wording (moved from rag/router.py, which keeps its own copy for
# the team coach until that path moves to the agent).
_LORE_MARKERS = (
    "tell me about", "lore", "origin", "story", "describe", "description",
    "where does", "where do", "lives", "live", "habitat", "personality",
    "look like", "based on", "myth", "legend of", "behaviour", "behavior",
    "how does", "evolve", "diet", "eat", "sleep", "night", "day",
)
# Lore beyond what a profile + dex entry covers: also search descriptions.
_DEEP_LORE = (
    "origin", "based on", "myth", "legend of", "habitat", "live", "lives", "look like",
    "diet", "eat", "behaviour", "behavior", "personality", "story", "lore", "known for",
)
_ENCOUNTER = re.compile(r"\b(where (can|do|to) i (find|catch|get)|catch|encounter|location|"
                        r"where is .* found|found in the wild|wild)\b")
_WEAK = re.compile(r"\b(weak(ness|nesses)?|resist(s|ance|ances)?|immune|immunit(y|ies)|"
                   r"effective|strong against|good against|type chart|matchups?)\b")
_LEARNERS = re.compile(r"\b(who|which|what)\b.*\b(learns?|gets?|can use|knows?)\b")
_CLASS = re.compile(r"\b(physical|special)\b")
_COUNTER = re.compile(r"\b(beats?|counters?|against|super[- ]effective|weak to|deal with|"
                      r"check(s)?|wall(s)?)\b")


@dataclass
class KeywordPlan:
    plan: Plan
    confident: bool


def _step(tool: str, why: str, **args) -> dict:
    return {"tool": tool, "args": args, "why": why}


async def plan_keywords(session: AsyncSession, question: str, scope: str = "ask") -> KeywordPlan:
    raw, confident = await _decide(session, question)
    plan = build_plan(raw[:MAX_KEYWORD_STEPS], "keyword", scope=scope)
    return KeywordPlan(plan, confident and len(plan.valid_steps) == 1)


async def _decide(session: AsyncSession, question: str) -> tuple[list[dict], bool]:
    text = question.lower()
    found = await names.find_in_text(session, question, ("pokemon", "form", "move", "type"))
    mons = [m for m in found if m.kind in ("pokemon", "form")]
    moves = [m for m in found if m.kind == "move"]
    types_ = [m for m in found if m.kind == "type"]
    # A span that is both a move and a type ("Psychic") is ambiguous: plan both.
    both = {m.name for m in moves} & {t.name for t in types_}
    plain_types = [t.name.lower() for t in types_ if t.name not in both]
    legendary, mythical = nlfilters.restricted_filters(question)
    learn_cue = bool(learnset._LEARN.search(text))
    lore = any(m in text for m in _DEEP_LORE)

    # ---- recommendations from the user's profile ----
    if personalize.is_recommendation(question) and not mons and not moves:
        return [_step("user_profile", "recommend from your favourites and types")], bool(
            _RECOMMEND.match(" ".join(names.norm(question).split())))

    # ---- a Pokémon and a move: can it learn it? ----
    if mons and moves:
        p, m = mons[0], moves[0]
        if p.kind == "pokemon":
            return [_step("learnset", f"check {p.name} × {m.name}",
                          pokemon=p.name, move=m.name)], _simple(question, found, "pair")

    # ---- a move ----
    if moves and not mons:
        m = moves[0]
        if learn_cue or _LEARNERS.search(text):
            cls = _CLASS.search(text)
            steps = [_step(
                "learnset", f"who learns {m.name}", move=m.name, types=plain_types,
                legendary=legendary, mythical=mythical,
                damage_class=cls.group(1) if cls else None,
            )]
            return steps, _simple(question, found, "learners") and not (
                plain_types or legendary is not None or mythical is not None)
        steps = [_step("move_info", f"what {m.name} does", name=m.name)]
        if m.name in both:
            steps.append(_step("type_matchup", f"the {m.name} type chart", types=[m.name.lower()]))
        return steps, len(steps) == 1 and _simple(question, found, "move")

    # ---- a Pokémon ----
    if mons:
        p = mons[0]
        if similarity.is_similarity(question):
            return [_step("similar_to", f"Pokémon like {p.name}", name=p.name)], _simple(
                question, found, "similar")
        if _ENCOUNTER.search(text):
            return [_step("encounters", f"where to find {p.name}", pokemon=p.name)], _simple(
                question, found, "where")
        if p.kind == "pokemon" and _COUNTER.search(text):
            cls = _CLASS.search(text)
            return [_step(
                "coverage_vs_types", f"what hits {p.name} super-effectively", against=p.name,
                want="moves" if matchup.wants_moves(question) else "pokemon",
                attacker_class=cls.group(1) if cls else None,
                legendary=legendary, mythical=mythical,
            )], False
        moves_cue = learn_cue or (
            learnset._MOVES.search(text) and not learnset._MATCHUP.search(text))
        if moves_cue and p.kind == "pokemon":
            cls = _CLASS.search(text)
            return [_step("learnset", f"{p.name}'s moves", pokemon=p.name, types=plain_types,
                          damage_class=cls.group(1) if cls else None)], False
        steps = [_step("get_pokemon", f"{p.name}'s profile", name=p.name)]
        if lore:
            steps.append(_step("semantic_search", "descriptions and lore", query=question))
        return steps, len(steps) == 1 and _simple(question, found, "profile")

    # ---- types: matchups and type charts ----
    if types_:
        targets = [t.name.lower() for t in types_]
        if matchup.is_matchup(question):
            cls = _CLASS.search(text)
            return [_step(
                "coverage_vs_types", f"what hits {'/'.join(targets)} super-effectively",
                targets=targets, want="moves" if matchup.wants_moves(question) else "pokemon",
                attacker_class=cls.group(1) if cls else None,
                legendary=legendary, mythical=mythical, off_type="coverage" in text,
            )], False
        if _WEAK.search(text) or (both and len(found) == len(types_) + len(moves)):
            steps = [_step("type_matchup", f"the {'/'.join(targets)} type chart",
                           types=targets[:2])]
            steps += [_step("move_info", f"the move {n}", name=n) for n in sorted(both)]
            return steps, len(steps) == 1 and _simple(question, found, "weak")

    # ---- an ability or item ----
    if not found:
        other = await names.find_in_text(session, question, ("ability", "item"))
        if other:
            o = other[0]
            tool = "ability_info" if o.kind == "ability" else "item_info"
            return [_step(tool, f"what {o.name} does", name=o.name)], _simple(
                question, other, "move")

    # ---- rankings, thresholds, filters (+ lore = today's hybrid) ----
    sq = sql_retrieval.plan(question)
    if sq is not None:
        steps = [_step("query_pokemon", "filter and rank Pokémon", **sq.model_dump())]
        if any(m in text for m in _LORE_MARKERS):
            steps.append(_step("semantic_search", "descriptions and lore", query=question))
        return steps, len(steps) == 1 and _simple_ranking(question, sq)

    return [_step("semantic_search", "search descriptions", query=question)], False


# ---- confidence: a fixed list of simple phrasings ------------------------------------

_TEMPLATES = {
    "profile": re.compile(r"^(tell me about|describe|who is|what is|show me|info on) P$"),
    # "what does X do" for a move, ability or item
    "move": re.compile(r"^(what does M do|what is M|what is the move M|tell me about M|"
                       r"describe M|explain M)$"),
    "pair": re.compile(r"^(can|does|will) P (learn|get|use) M$"),
    "learners": re.compile(r"^(who|which pokemon|what pokemon|which pokemons) "
                           r"(can )?(learns?|gets?|can use) M$"),
    "similar": re.compile(r"^((which|what) )?(pokemon|pokemons|anything|something) "
                          r"(is |are )?(like|similar to) P$|^(what is|what s) similar to P$"),
    "where": re.compile(r"^where (can|do|to) (i )?(catch|find|get) (a |an )?P"
                        r"( in the wild)?$|^where is P found( in the wild)?$"),
    "weak": re.compile(r"^(what is|what are|what s) (a |the )?T( type| types)? weak "
                       r"(to|against)$|^(what are )?(the )?T( type)? weaknesses$"),
}
# Recommendation asks with nothing else in them.
_RECOMMEND = re.compile(
    r"^((can you |please )?recommend (me )?(a |some )?pokemon( for me)?|"
    r"(which|what) pokemon (would|will|might) i (probably )?(like|enjoy)|"
    r"(pick|suggest) (me )?(a )?pokemon( for me)?)$"
)
_RANK = re.compile(
    r"^((which|what) (pokemon )?(has|have|is) )?(the )?"
    r"(highest|lowest|fastest|slowest|tallest|shortest|heaviest|lightest|strongest|weakest)"
    r"( [a-z]+){0,3}( pokemon)?$"
)


def _simple(question: str, found: list[names.Match], shape: str) -> bool:
    """True when the question is exactly a known simple phrasing around its names."""
    kinds = {m.name: m.kind for m in found}
    if len(kinds) != len(found):  # one name resolved to several kinds
        return False
    text = names.norm(question)
    for m in found:
        slot = (" P " if m.kind in ("pokemon", "form")
                else " M " if m.kind in ("move", "ability", "item")
                else " T " if m.kind == "type" else None)
        if slot is None:
            return False
        text = text.replace(names.norm(m.name), slot, 1)
    text = " ".join(text.split()).replace(" pokemon s ", " ")
    return bool(_TEMPLATES[shape].match(text))


def _simple_ranking(question: str, sq: sql_retrieval.StructuredQuery) -> bool:
    only_sort = sq.sort_by is not None and not (
        sq.types_all or sq.generation or sq.legendary is not None
        or sq.mythical is not None or sq.stat_filters
    )
    return only_sort and bool(_RANK.match(" ".join(names.norm(question).split())))
