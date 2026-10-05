"""Answers rendered by code for closed-form results — no LLM writes them.

Rankings and counts reuse ``structured_answer.render``; learn checks, learner lists,
move facts and type charts have their own templates. Every answer follows the usual
shape (one direct opening sentence, then ``- **Label** — value [n]`` bullets), and
every ``[n]`` is offset to the step's position in the combined sources list.
"""

from __future__ import annotations

import re

from app.agent.results import ToolResult
from app.agent.views import LearnCheckView, LearnersView, MoveListView, TypeChartView
from app.rag import learnset as learnset_rag
from app.rag import structured_answer


def _shift(text: str, offset: int) -> str:
    return re.sub(r"\[(\d+)\]", lambda m: f"[{int(m.group(1)) + offset}]", text) if offset else text


def _join(words: list[str]) -> str:
    words = [w.title() for w in words]
    if not words:
        return ""
    return words[0] if len(words) == 1 else f"{', '.join(words[:-1])} and {words[-1]}"


def _view(result: ToolResult, kind):
    return next((v for v in result.views if isinstance(v, kind)), None)


def _query(result: ToolResult) -> str:
    q, total = result.data["query"], result.data["total"]
    return structured_answer.render(q, result.chunks, total)


def _learn_check(v: LearnCheckView) -> str:
    game = f" in {v.game}" if v.game else ""
    if v.ok:
        return f"Yes — **{v.pokemon.name}** can learn **{v.move.name}** {v.how}{game} [1]."
    return (f"No — **{v.pokemon.name}** can't learn **{v.move.name}**{game}: it isn't in "
            f"{v.pokemon.name}'s learnset [1].")


def _learners(v: LearnersView) -> str:
    game = f" in {v.game}" if v.game else ""
    who = " ".join([*v.scope, "Pokémon"])
    if not v.total:
        return f"No {who} learn **{v.move.name}**{game} [1]."
    methods = ", ".join(
        f"{n} {'as an egg move' if m == 'egg' else 'by ' + learnset_rag.METHOD_LABEL.get(m, m)}"
        for m, n in sorted(v.by_method.items(),
                           key=lambda kv: learnset_rag._METHOD_ORDER.index(kv[0])
                           if kv[0] in learnset_rag._METHOD_ORDER else 9)
    )
    lines = [f"{v.total} {who} can learn **{v.move.name}**{game} ({methods}) [2]."]
    if v.rows:
        lines.append("")
        lines.extend(
            f"- **{r.name}** — {r.via or 'learns it'} [{(r.ref or 0) + 1}]" for r in v.rows
        )
    return "\n".join(lines)


def _move(v: MoveListView) -> str:
    out = []
    for m in v.moves:
        n = (m.ref or 0) + 1
        power = f"{m.power} power" if m.power else "no base power"
        acc = f"{m.accuracy}% accuracy" if m.accuracy else "never misses"
        cls = m.damage_class or "status"
        lines = [f"**{m.name}** is a {m.type.title()}-type {cls} move with {power}, {acc} and "
                 f"{m.pp} PP [{n}]."]
        bullets = []
        if m.effect:
            bullets.append(f"- **Effect** — {m.effect} [{n}]")
        if m.learners is not None:
            bullets.append(f"- **Learned by** — {m.learners} Pokémon [{n}]")
        out.append("\n".join(lines + ([""] + bullets if bullets else [])))
    return "\n\n".join(out)


def _type_chart(v: TypeChartView) -> str:
    label = "/".join(t.title() for t in v.types)
    weak = v.weak_4x + v.weak_2x
    if weak:
        opening = f"A {label}-type Pokémon is weak to {_join(weak)} moves [1]."
    else:
        opening = f"A {label}-type Pokémon has no weaknesses [1]."
    bullets = []
    if v.weak_4x:
        bullets.append(f"- **4× weak to** — {_join(v.weak_4x)} [1]")
    resist = v.resist_quarter + v.resist_half
    if resist:
        bullets.append(f"- **Resists** — {_join(resist)} [1]")
    if v.immune:
        bullets.append(f"- **Immune to** — {_join(v.immune)} [1]")
    if v.strong_against:
        bullets.append(f"- **Super-effective against** — {_join(v.strong_against)} [1]")
    return opening + ("\n\n" + "\n".join(bullets) if bullets else "")


def render_step(tool: str, result: ToolResult) -> str | None:
    """This step's answer with step-local citations, or None if it can't be rendered."""
    if tool == "query_pokemon" and "query" in result.data:
        return _query(result)
    if tool == "learnset":
        if (v := _view(result, LearnCheckView)) is not None:
            return _learn_check(v)
        if (v := _view(result, LearnersView)) is not None:
            return _learners(v)
        return None
    if tool == "move_info" and (v := _view(result, MoveListView)) is not None:
        return _move(v)
    if tool == "type_matchup" and (v := _view(result, TypeChartView)) is not None:
        return _type_chart(v)
    return None


def render_all(parts: list[tuple[str, ToolResult, int]]) -> str | None:
    """Join per-step answers; ``parts`` = (tool, result, citation offset). None if any can't."""
    out = []
    for tool, result, offset in parts:
        text = render_step(tool, result)
        if text is None:
            return None
        out.append(_shift(text, offset))
    return "\n\n".join(out) if out else None
