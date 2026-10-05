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
    calc_tools,  # noqa: F401
    names,
    team_tools,  # noqa: F401
)
from app.agent.plan import Plan, build_plan
from app.rag import learnset, matchup, personalize, similarity, sql_retrieval
from app.services import nlfilters

MAX_KEYWORD_STEPS = 3

# Description / lore wording (the old heuristic router's markers).
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
# "by levelling only", "via TM", "egg moves", "move tutor" → the learnset's method filter.
_METHOD_CUES = (
    ("level-up", re.compile(r"\b(level(?:l?ing)?[- ]?up|by level(?:l?ing)?|level(?:l?ing|s)?|"
                            r"lvl)\b")),
    ("machine", re.compile(r"\b(tms?|technical machines?|trs?)\b")),
    ("egg", re.compile(r"\b(egg moves?|breed(?:ing)?|eggs?)\b")),
    ("tutor", re.compile(r"\b(tutors?|move tutor)\b")),
)


def _learn_method(text: str) -> str | None:
    """The one learn method the question restricts to, if it names exactly one."""
    hits = [m for m, rx in _METHOD_CUES if rx.search(text)]
    return hits[0] if len(hits) == 1 else None


_CLASS = re.compile(r"\b(physical|special)\b")
_COUNTER = re.compile(r"\b(beats?|counters?|against|super[- ]effective|weak to|deal with|"
                      r"check(s)?|wall(s)?)\b")


@dataclass
class KeywordPlan:
    plan: Plan
    confident: bool


def _step(tool: str, why: str, **args) -> dict:
    return {"tool": tool, "args": args, "why": why}


async def plan_keywords(
    session: AsyncSession, question: str, scope: str = "ask", ctx=None
) -> KeywordPlan:
    if scope == "team" and ctx is not None and ctx.team is not None:
        raw, confident = await _decide_team(session, question, ctx)
        plan = build_plan(raw[:MAX_KEYWORD_STEPS], "keyword", scope=scope)
        # A plain team question has no extra steps: the attached team context answers it.
        ok = len(plan.valid_steps) == len(plan.steps) <= 1
        return KeywordPlan(plan, confident and ok)
    if scope == "calc" and ctx is not None and ctx.extra.get("calc") is not None:
        raw, confident = await _decide_calc(session, question, ctx.extra["calc"])
        plan = build_plan(raw[:MAX_KEYWORD_STEPS], "keyword", scope=scope)
        ok = len(plan.valid_steps) == len(plan.steps) <= 1
        return KeywordPlan(plan, confident and ok)
    raw, confident = await _decide(session, question)
    plan = build_plan(raw[:MAX_KEYWORD_STEPS], "keyword", scope=scope)
    return KeywordPlan(plan, confident and len(plan.valid_steps) == 1)


# ---- damage-calculator phrasings ------------------------------------------------------

_KO = re.compile(r"\b(o\s*hko|[2-6]\s*hko|ko|one[- ]?shot|two[- ]?shot|kill|how much damage|"
                 r"how much does|does .+ do to|damage (does|from|to))\b")
_SURVIVE = re.compile(r"\b(survive|live through|tank|withstand)\b")
_BUILD = re.compile(r"\b(best build|build|best set|moveset|spread)\b|^\s*make it\b|"
                    r"\b(bulkier|faster|stronger|sweeper|special attacker|physical attacker)\b|"
                    r"\b(bulky|fast|offensive|defensive|special|physical|mixed|support) set\b")
# With a proposal on the table, an imperative tweak revises it ("no Choice item", "swap X for Y").
_REVISE = re.compile(r"^\s*(no|without|swap|replace|use|drop|give|try|change|switch|more|less|"
                     r"keep|go|max)\b|\binstead\b")
_WITH = re.compile(r"\bwith (an? |the )?(.+?)(?:\?|$|,| and | instead)")


def _calc_members(question: str, st) -> list:
    """Calculator Pokémon named in the question, in order of appearance."""
    low = question.lower()
    found = [(low.find(m.name.lower()), m) for m in st.members if m.name.lower() in low]
    return [m for _, m in sorted(found, key=lambda x: x[0])]


async def _changes(session: AsyncSession, question: str) -> list[dict]:
    """What-if changes from 'with <item | nature | EVs>' (attacker side)."""
    from app.services import damage_calc

    m = _WITH.search(question)
    if not m:
        return []
    phrase = m.group(2).strip()
    out: list[dict] = []
    items = await names.find_in_text(session, phrase, ("item",))
    if items:
        out.append({"who": "attacker", "key": "item", "value": items[0].name})
    nat = next((n for n in damage_calc.NATURES if re.search(rf"\b{n.lower()}\b", phrase.lower())),
               None)
    if nat:
        out.append({"who": "attacker", "key": "nature", "value": nat})
    if re.search(r"\d+\s*(hp|atk|attack|def|defen[cs]e|spa|spd|spe|speed)\b", phrase.lower()):
        try:
            damage_calc.parse_evs(phrase)
            out.append({"who": "attacker", "key": "evs", "value": phrase})
        except damage_calc.ChangeError:
            pass
    return out


async def _decide_calc(session: AsyncSession, question: str, st) -> tuple[list[dict], bool]:
    text = question.lower()
    named = _calc_members(question, st)
    moves = [m for m in await names.find_in_text(session, question, ("move",))
             if m.name.lower() not in {x.name.lower() for x in st.members}]
    move = moves[0].name if moves else None
    cues = sum(bool(r.search(text)) for r in (_KO, _SURVIVE, _BUILD))
    single = cues == 1 and len(named) <= 2 and len(moves) <= 1

    def before(cue: re.Pattern, m) -> bool:
        hit = cue.search(text)
        return hit is not None and text.find(m.name.lower()) < hit.start()

    if _SURVIVE.search(text):
        dfn = next((m for m in named if before(_SURVIVE, m)), None)
        atk = next((m for m in named if m is not dfn), None)
        return [_step("survive_threshold", "the bulk needed to survive the hit",
                      defender=dfn.name if dfn else None, attacker=atk.name if atk else None,
                      move=move)], single

    if _KO.search(text):
        atk = next((m for m in named if before(_KO, m)), None)
        dfn = next((m for m in named if m is not atk), None)
        if atk is None and dfn is not None and dfn.side == 0:
            atk, dfn = dfn, None  # "how much does Garchomp do" names the attacker
        changes = await _changes(session, question)
        steps = [_step("damage_calc", "the hit's damage and KO chance",
                       attacker=atk.name if atk else None, defender=dfn.name if dfn else None,
                       move=move, changes=changes)]
        if _BUILD.search(text):
            steps.append(_step("propose_build", "a new build", request=question[:300]))
        return steps, single

    if _BUILD.search(text):
        who = named[0].name if named else None
        return [_step("propose_build", "a build for the Pokémon", pokemon=who,
                      request=question[:300])], single

    if st.proposal is not None and _REVISE.search(text):
        return [_step("propose_build", "revise the proposed build", request=question[:300])], True

    raw, confident = await _decide(session, question)
    from app.agent.tools import REGISTRY

    roster = {m.name.lower() for m in st.members}
    useful = [
        r for r in raw
        if "calc" in REGISTRY[r["tool"]].scopes
        and not (r["tool"] == "get_pokemon" and r["args"].get("name", "").lower() in roster)
        and not (r["tool"] == "query_pokemon" and _vague_query(r["args"]))
    ]
    if not useful:
        return [], True  # plain: the attached calculator state answers it
    return useful, confident and len(useful) == len(raw)


# ---- team coach phrasings -------------------------------------------------------------

# Imperative "put this on my team" verbs vs. deliberation ("should I add …?").
_ADD_VERBS = ("add ", "include ", "put ", "bring in ", "slot in ", "recruit ", "run ")
_DELIBERATE = ("should i", "is it worth", "worth adding", "worth it", "do you think", "would you",
               "could i", "can i", "what if")
# A set change: an edit verb or a set field (ported from the old TeamCoach.tsx regex).
_SET_EDIT = re.compile(
    r"\b(change|make|give|set|swap|switch|replace|teach|equip|put|tweak|improve|optimi[sz]e|"
    r"fix|rebuild|build|use|hold|run)\b|\b(best|better|new) (set|build|moveset)\b|"
    r"\bmoveset\b|\bevs?\b|\bitem\b|\bnature\b|\bability\b", re.I)
_THEIRS = re.compile(r"\b(their|opponent'?s?|rival'?s?|enemy|foe'?s?)\b", re.I)
_SWAP = re.compile(r"\b(replace|swap|switch)\b", re.I)
_DRAFT_KEYWORDS = (
    "draft", "recommend", "suggest", "who should", "what should i add", "which pokemon",
    "fill", "complete", "round out", "additions", "rest of", "best 5", "best five", "team of",
    "picks", "options",
)
_VS = re.compile(r"\b(vs\.?|versus|against)\b", re.I)


def is_imperative_add(question: str) -> bool:
    """True for an imperative 'add <name>' — never for a 'should I add …?' deliberation."""
    low = question.lower()
    if any(d in low for d in _DELIBERATE):
        return False
    return any((" " + low).find(" " + v) != -1 for v in _ADD_VERBS)


def _deliberating_add(question: str) -> bool:
    low = question.lower()
    return any(d in low for d in _DELIBERATE) and any(v in low for v in _ADD_VERBS)


def _members(question: str, team) -> list:
    low = question.lower()
    return sorted(
        (m for m in (team.members if team else []) if m.name.lower() in low),
        key=lambda m: -len(m.name),
    )


async def _decide_team(session: AsyncSession, question: str, ctx) -> tuple[list[dict], bool]:
    text = question.lower()
    ours, theirs = _members(question, ctx.team), _members(question, ctx.opponent)
    roster = {m.name.lower() for m in ctx.team.members} | {
        m.name.lower() for m in (ctx.opponent.members if ctx.opponent else [])}

    # ---- a set change for a member (checked first: "what should Garchomp run?") ----
    if _SET_EDIT.search(text) and (ours or theirs):
        side = "theirs" if (theirs and (_THEIRS.search(text) or not ours)) else "ours"
        m = (theirs if side == "theirs" else ours)[0]
        step = _step("propose_set_edit", f"a new set for {m.name}", member=m.name, side=side,
                     request=question[:300])
        return [step], not _SWAP.search(text) and not any(k in text for k in _DRAFT_KEYWORDS)

    # ---- an add, or a deliberation about one (the runner's gate decides which) ----
    mons = [m for m in await names.find_in_text(session, question, ("pokemon",))
            if m.name.lower() not in roster]
    if mons and (is_imperative_add(question) or _deliberating_add(question)):
        return [_step("add_member", f"add {mons[0].name}", pokemon=mons[0].name)], True

    # ---- drafting ----
    if any(k in text for k in _DRAFT_KEYWORDS):
        from app.services import recommend

        known = set(names.STANDARD_TYPES)
        return [_step(
            "recommend_additions", "draft additions for the team",
            role=recommend.parse_role(question),
            legendary=nlfilters.legendary_constraint(question),
            mythical=nlfilters.mythical_constraint(question),
            types=recommend.requested_types(question, known),
        )], False

    # ---- one of ours against one of theirs ----
    if ours and theirs and _VS.search(text):
        return [_step("duel", f"{ours[0].name} vs {theirs[0].name}",
                      ours=ours[0].name, theirs=theirs[0].name)], False

    # ---- dex lookups (Ask rules), unless they only restate the team ----
    raw, confident = await _decide(session, question)
    from app.agent.tools import REGISTRY

    useful = [
        r for r in raw
        if "team" in REGISTRY[r["tool"]].scopes
        and not (r["tool"] == "get_pokemon" and r["args"].get("name", "").lower() in roster)
        and not (r["tool"] == "query_pokemon" and _vague_query(r["args"]))
    ]
    if not useful:
        return [], True  # plain: the attached team context answers it
    return useful, confident and len(useful) == len(raw)


def _vague_query(args: dict) -> bool:
    """A Pokédex query the keyword parser built from incidental words ("my team's best …")."""
    return not (args.get("types_all") or args.get("stat_filters") or args.get("generation")
                or args.get("legendary") is not None or args.get("mythical") is not None
                or args.get("sort_by") not in (None, "base_stat_total"))


async def _other_info(session: AsyncSession, question: str, *, limit: int,
                      found: list | None = None) -> list[dict]:
    """One ability_info / item_info step per ability or item named in the question."""
    if found is None:
        found = await names.find_in_text(session, question, ("ability", "item"))
    return [
        _step("ability_info" if o.kind == "ability" else "item_info", f"what {o.name} does",
              name=o.name)
        for o in found[:max(limit, 0)]
    ]


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
            how = _learn_method(text)
            return [_step("learnset", f"check {p.name} × {m.name}",
                          pokemon=p.name, move=m.name, method=how)], (
                _simple(question, found, "pair") and how is None)

    # ---- a move ----
    if moves and not mons:
        m = moves[0]
        if learn_cue or _LEARNERS.search(text):
            cls = _CLASS.search(text)
            how = _learn_method(text)
            steps = [_step(
                "learnset", f"who learns {m.name}", move=m.name, types=plain_types,
                legendary=legendary, mythical=mythical,
                damage_class=cls.group(1) if cls else None, method=how,
            )]
            return steps, _simple(question, found, "learners") and not (
                plain_types or legendary is not None or mythical is not None or how)
        # Every named move (and ability/item: "Protect and Leftovers"), one lookup each.
        steps = [_step("move_info", f"what {x.name} does", name=x.name) for x in moves[:4]]
        steps += await _other_info(session, question, limit=4 - len(steps))
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
                          damage_class=cls.group(1) if cls else None,
                          method=_learn_method(text))], False
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
            steps = await _other_info(session, question, limit=4, found=other)
            return steps, len(steps) == 1 and _simple(question, other, "move")

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
