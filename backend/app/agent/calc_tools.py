"""Calc-coach tools: the always-attached calculator context, damage what-ifs, survival
thresholds and build proposals — all over the backend port of the calculator's maths
(``services/damage_calc``), so answers match what the calculator shows.

The resolved calculator state (``services/calc_state.CalcState``) arrives in
``ctx.extra["calc"]``. Nothing here writes: what-ifs, thresholds and builds are offered
to the calculator with an Apply button the user clicks.
"""

from __future__ import annotations

import difflib
from dataclasses import replace
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.results import ToolResult
from app.agent.tools import AgentContext, tool
from app.agent.views import (
    BuildProposalView,
    CalcApply,
    CalcRef,
    DamageView,
    HitRange,
    MoveRow,
    SurviveView,
)
from app.rag import build_suggest
from app.rag.retrieval import RetrievedChunk
from app.services import builder
from app.services import damage_calc as dc
from app.services.calc_state import CalcMember, CalcMove, CalcState, move_by_name

CALC = ("calc",)
_CTX_BASE = 12_000_000
_TOOL_BASE = 13_000_000

CALC_NOTE = (
    "NOTE: You are the damage calculator's coach. The CONTEXT starts with the calculator's "
    "current state — each Pokémon's set and stats, the field, and the hits the calculator "
    "shows — then any lookups planned for this question. Answer from those numbers and cite "
    "[n]; never invent damage percentages: if a number you need isn't in the CONTEXT, say "
    "which calculation would answer it."
)


def state_of(ctx: AgentContext) -> CalcState:
    return ctx.extra["calc"]


def _ref(m: CalcMember) -> CalcRef:
    return CalcRef(slot=m.slot, name=m.name, side=m.side, dex_number=m.dex_number)


def _who(m: CalcMember) -> str:
    return f"your {m.name}" if m.side == 0 else f"the opposing {m.name}"


def _stats(m: CalcMember, level: int) -> dict[str, int]:
    keys = {"hp": "hp", "atk": "attack", "def": "defense", "spa": "sp_attack",
            "spd": "sp_defense", "spe": "speed"}
    return {
        k: dc.stat_full(m.mon.stats[base], level, m.set.iv[k], m.set.ev[k],
                        dc.nat_mul(m.set.nat, k), k == "hp")
        for k, base in keys.items()
    }


def ev_text(ev: dict[str, int]) -> str:
    order = sorted((k for k in dc.SKEYS if ev.get(k)), key=lambda k: -ev[k])
    return " / ".join(f"{ev[k]} {dc.SABBR[k]}" for k in order) or "no EVs"


def ko_text(r: dc.Result | HitRange, hp: float = 100) -> str:
    """The calculator's KO wording: min damage vs current HP decides a guaranteed KO."""
    if r.te == 0:
        return "no effect"
    if r.ko == 1:
        return "a guaranteed OHKO"
    if r.max_pct >= hp:
        return "a possible OHKO (high rolls)"
    return f"a {r.ko}HKO" if r.ko else "no damage"


def _range(r: dc.Result, hp: float) -> HitRange:
    return HitRange(min_pct=round(r.min_pct, 1), max_pct=round(r.max_pct, 1), ko=r.ko, te=r.te,
                    ko_text=ko_text(r, hp))


def _pct(h: HitRange) -> str:
    return "0% (immune)" if h.te == 0 else f"{h.min_pct:g}–{h.max_pct:g}%"


# ---- calc_context (built-in, never planned) -------------------------------------------


class NoArgs(BaseModel):
    pass


@tool(
    "calc_context",
    scopes=CALC,
    description="The damage calculator's current state (always attached).",
    args=NoArgs,
    plannable=False,
)
async def calc_context(session: AsyncSession, args: NoArgs, ctx: AgentContext) -> ToolResult:
    st = state_of(ctx)
    chunks: list[RetrievedChunk] = []

    def add(content: str, ctype: str, ref: str, m: CalcMember | None = None) -> None:
        chunks.append(RetrievedChunk(
            id=-(_CTX_BASE + len(chunks)), pokemon_id=m.pokemon_id if m else None,
            pokemon_name=m.name if m else None, dex_number=m.dex_number if m else None,
            chunk_type=ctype, source_ref=ref, content=content, score=1.0,
        ))

    for m in st.members:
        s = _stats(m, st.level)
        mv = (f"{m.move.name} ({m.move.type.title()}, {m.move.damage_class}"
              f"{f', {m.move.power} power' if m.move.power else ''})") if m.move else "none"
        add(
            f"Calculator: {_who(m)} ({'/'.join(t.title() for t in m.mon.types)}), Lv {st.level}, "
            f"{m.set.nat} nature, {ev_text(m.set.ev)}, item {m.set.item}, ability {m.set.abil}, "
            f"{m.set.hp:g}% HP. Stats: HP {s['hp']} / Atk {s['atk']} / Def {s['def']} / "
            f"SpA {s['spa']} / SpD {s['spd']} / Spe {s['spe']}. Chosen move: {mv}.",
            "calc_slot", f"slot {m.slot}", m,
        )
    f = st.field
    on = [x for x in ("reflect", "lightscreen", "crit", "burn", "friend_guard") if getattr(f, x)]
    add(
        f"Calculator field: {'doubles' if st.doubles else 'singles'}, Lv {st.level}, weather "
        f"{f.weather}, terrain {f.terrain}" + (f"; on: {', '.join(on)}" if on else "") + ".",
        "calc_field", "field",
    )
    if st.hits:
        names = {m.slot: _who(m) for m in st.members}
        lines = [
            f"{names.get(h.attacker, f'slot {h.attacker}')}'s {h.move} → "
            f"{names.get(h.target, f'slot {h.target}')}: "
            + ("no effect" if h.te == 0 else f"{h.min_pct:.0f}–{h.max_pct:.0f}%")
            + (f", {h.ko}HKO" if h.ko else "")
            for h in st.hits
        ]
        add("What the calculator shows this turn: " + "; ".join(lines) + ".", "calc_hits", "turn")
    if st.proposal is not None:
        p, b = st.proposal, st.proposal.build
        thread = " | ".join(f"User: {t.ask} / Coach: {t.reply}" for t in p.thread[-3:])
        add(
            f"Current build proposal for slot {p.slot} ({b.pokemon}): moves {', '.join(b.moves)}; "
            f"ability {b.ability}; nature {b.nature}; item {b.item}; EVs {ev_text(b.evs)}."
            + (f" Earlier: {thread}" if thread else ""),
            "calc_proposal", "proposal",
        )
    names = ", ".join(m.name for m in st.members) or "empty"
    return ToolResult(chunks=chunks, summary=f"calculator: {names}", note=CALC_NOTE,
                      data={"context": True})


# ---- slot / move resolution -----------------------------------------------------------


def find_member(st: CalcState, name: str | None) -> CalcMember | None:
    if not name:
        return None
    key = name.strip().lower().removeprefix("the opposing ").removeprefix("my ")
    by = {m.name.lower(): m for m in st.members}
    if key in by:
        return by[key]
    close = difflib.get_close_matches(key, list(by), n=1, cutoff=0.75)
    return by[close[0]] if close else None


def pair(st: CalcState, attacker: str | None, defender: str | None
         ) -> tuple[CalcMember | None, CalcMember | None, str | None]:
    """(attacker, defender, error). Defaults: the focused slot attacks what it aims at."""
    a = find_member(st, attacker) if attacker else st.by_slot(st.focus) or (
        st.members[0] if st.members else None)
    if attacker and a is None:
        return None, None, f"{attacker} isn't in the calculator"
    if a is None:
        return None, None, "the calculator is empty"
    d = find_member(st, defender) if defender else None
    if defender and d is None:
        return None, None, f"{defender} isn't in the calculator"
    if d is None:
        foes = st.foes_of(a)
        d = next((x for x in foes if x.slot == a.aim), foes[0] if foes else None)
    if d is None:
        return None, None, f"there's nothing for {a.name} to hit"
    return a, d, None


async def move_for(session: AsyncSession, m: CalcMember, name: str | None
                   ) -> tuple[CalcMove | None, str | None]:
    if not name:
        if m.move is None or m.move.power <= 0:
            return None, f"{m.name} has no damaging move chosen"
        return m.move, None
    mv = await move_by_name(session, name)
    if mv is None:
        return None, f'unresolved move "{name}"'
    legal = (await builder.legal_moves_for_form(session, m.form_id) if m.form_id else []) or (
        await builder.legal_moves(session, m.pokemon_id))
    if mv.name.lower() not in {x.name.lower() for x in legal}:
        return None, f"{m.name} can't learn {mv.name}"
    if mv.power <= 0:
        return None, f"{mv.name} doesn't deal direct damage"
    return mv, None


def _move_row(mv: CalcMove, ref: int | None = 0) -> MoveRow:
    return MoveRow(ref=ref, move_id=mv.move_id, name=mv.name, type=mv.type,
                   damage_class=mv.damage_class, power=mv.power)


# ---- damage_calc ----------------------------------------------------------------------


class Change(BaseModel):
    who: Literal["attacker", "defender", "field"]
    key: str = Field(description="item|ability|nature|evs|hp|weather|terrain|crit|reflect|"
                     "lightscreen|burn")
    value: str


class DamageArgs(BaseModel):
    attacker: str | None = None
    defender: str | None = None
    move: str | None = None
    changes: list[Change] = Field(default_factory=list, description="what-if changes")


_APPLY_KEYS = {"item": "item", "ability": "ability", "nature": "nature", "evs": "evs"}


@tool(
    "damage_calc",
    scopes=CALC,
    description="One hit's damage % and KO (the calculator's maths), optionally with what-if "
    "changes.",
    args=DamageArgs,
    closed_form=True,
)
async def damage_calc(session: AsyncSession, args: DamageArgs, ctx: AgentContext) -> ToolResult:
    st = state_of(ctx)
    a, d, err = pair(st, args.attacker, args.defender)
    if err:
        return ToolResult.error(err)
    mv, err = await move_for(session, a, args.move)
    if err:
        return ToolResult.error(err)
    now = dc.calc_hit(a.mon, a.set, d.mon, d.set, mv.maths, st.field)
    current = _range(now, d.set.hp)
    whatif = None
    applies: list[CalcApply] = []
    changes = [c.model_dump() for c in args.changes]
    if changes:
        try:
            a2, d2, f2 = dc.apply_changes(a.set, d.set, st.field, changes)
        except (dc.ChangeError, ValueError) as e:
            return ToolResult.error(str(e))
        wi = dc.calc_hit(a.mon, a2, d.mon, d2, mv.maths, f2)
        whatif = _range(wi, d2.hp)
        for who, m, new in (("attacker", a, a2), ("defender", d, d2)):
            fields = {}
            for c in changes:
                if c["who"] == who and c["key"] in _APPLY_KEYS:
                    k = _APPLY_KEYS[c["key"]]
                    fields[k] = {"item": new.item, "ability": new.abil, "nature": new.nat,
                                 "evs": new.ev}[k]
            if fields:
                applies.append(CalcApply(slot=m.slot, fields=fields))

    text = (f"Damage by the calculator's maths: {_who(a)}'s {mv.name} vs {_who(d)} "
            f"({d.set.hp:g}% HP): {_pct(current)}, {current.ko_text}.")
    if whatif is not None:
        desc = ", ".join(f"{c['who']} {c['key']} {c['value']}" for c in changes)
        text += f" What-if ({desc}): {_pct(whatif)}, {whatif.ko_text}."
    chunk = RetrievedChunk(
        id=-(_TOOL_BASE + a.slot * 1000 + d.slot * 100 + mv.move_id % 100), pokemon_id=a.pokemon_id,
        pokemon_name=a.name, dex_number=a.dex_number, chunk_type="calc_damage",
        source_ref=f"{a.name} → {d.name}", content=text, score=1.0,
    )
    view = DamageView(attacker=_ref(a), defender=_ref(d), move=_move_row(mv), current=current,
                      whatif=whatif, changes=changes, apply=applies, chunk_refs=[0])
    data = {"attacker": a.name, "defender": d.name, "move": mv.name, "hp": d.set.hp,
            "current": current, "whatif": whatif, "changes": changes,
            "attacker_side": a.side, "defender_side": d.side}
    summary = f"{mv.name}: {_pct(current)}" + (f" → {_pct(whatif)}" if whatif else "")
    return ToolResult(chunks=[chunk], views=[view], summary=summary, data=data)


# ---- survive_threshold ----------------------------------------------------------------


class SurviveArgs(BaseModel):
    defender: str | None = None
    attacker: str | None = None
    move: str | None = None


@tool(
    "survive_threshold",
    scopes=CALC,
    description="The least HP/Def or SpD EVs (then nature) the defender needs to survive a hit.",
    args=SurviveArgs,
    closed_form=True,
)
async def survive_threshold(
    session: AsyncSession, args: SurviveArgs, ctx: AgentContext
) -> ToolResult:
    st = state_of(ctx)
    d = find_member(st, args.defender) if args.defender else st.by_slot(st.focus)
    if d is None:
        return ToolResult.error(f"{args.defender or 'the defender'} isn't in the calculator")
    if args.attacker:
        a = find_member(st, args.attacker)
        if a is None:
            return ToolResult.error(f"{args.attacker} isn't in the calculator")
    else:
        foes = st.foes_of(d)
        a = next((x for x in foes if x.aim == d.slot), foes[0] if foes else None)
        if a is None:
            return ToolResult.error(f"there's nothing attacking {d.name}")
    mv, err = await move_for(session, a, args.move)
    if err:
        return ToolResult.error(err)
    s = dc.survive(a.mon, a.set, d.mon, d.set, mv.maths, st.field)
    new_ev = {**d.set.ev, "hp": s.hp_ev, s.stat: s.stat_ev}
    now = dc.calc_hit(a.mon, a.set, d.mon, d.set, mv.maths, st.field)
    at = dc.calc_hit(a.mon, a.set, d.mon, replace(d.set, nat=s.nature, ev=new_ev), mv.maths,
                     st.field)
    cur, rng = _range(now, d.set.hp), _range(at, d.set.hp)
    # Already lives through it: nothing to apply (the minimal spread could even be less bulk).
    already = now.max_pct < d.set.hp
    apply = CalcApply(slot=d.slot, fields={"evs": new_ev, **(
        {"nature": s.nature} if s.nature_changed else {})}) if s.survives and not already else None
    evs = " / ".join(f"{v} {k}" for k, v in (("HP", s.hp_ev), (dc.SABBR[s.stat], s.stat_ev)) if v)
    spread = (f"{evs or 'no extra EVs'}, {s.nature} nature" if s.nature_changed
              else evs or "no extra EVs")
    # The search keeps the rest of the spread; say so when that is what rules it out.
    kept = {k: v for k, v in d.set.ev.items() if k not in ("hp", s.stat) and v}
    limit = (f"with the EVs it has free (the rest are in {ev_text(kept)})" if kept
             else "with any legal spread")
    lead = (f"Survival by the calculator's maths: {_who(d)} vs {_who(a)}'s {mv.name} from "
            f"{d.set.hp:g}% HP — currently takes {cur.min_pct:g}–{cur.max_pct:g}%. ")
    text = lead + (
        "It already survives as set." if already else
        f"Survives with {spread}: {rng.min_pct:g}–{rng.max_pct:g}%." if s.survives else
        f"Can't survive it {limit}; the best ({spread}) still takes "
        f"{rng.min_pct:g}–{rng.max_pct:g}%.")
    chunk = RetrievedChunk(
        id=-(_TOOL_BASE + 500_000 + d.slot * 1000 + a.slot * 100 + mv.move_id % 100),
        pokemon_id=d.pokemon_id, pokemon_name=d.name, dex_number=d.dex_number,
        chunk_type="calc_survive", source_ref=f"{d.name} vs {mv.name}", content=text, score=1.0,
    )
    view = SurviveView(defender=_ref(d), attacker=_ref(a), move=_move_row(mv), survives=s.survives,
                       stat=s.stat, hp_ev=s.hp_ev, stat_ev=s.stat_ev, nature=s.nature,
                       nature_changed=s.nature_changed, range=rng, current=cur, apply=apply,
                       already=already, chunk_refs=[0])
    data = {"defender": d.name, "attacker": a.name, "move": mv.name, "survives": s.survives,
            "already": already, "spread": spread, "limit": limit, "range": rng, "current": cur,
            "defender_side": d.side, "attacker_side": a.side}
    summary = (f"{d.name}: already survives" if already else
               f"{d.name}: {'survives with ' + spread if s.survives else 'can’t survive'}")
    return ToolResult(chunks=[chunk], views=[view], summary=summary, data=data)


# ---- propose_build --------------------------------------------------------------------


class BuildArgs(BaseModel):
    pokemon: str | None = Field(None, description="calculator Pokémon; default: the focused one")
    request: str = Field(description="what the user wants, in their words")


@tool(
    "propose_build",
    scopes=CALC,
    description="Suggest or revise a build for a calculator Pokémon (Apply puts it in the calc).",
    args=BuildArgs,
    closed_form=True,
)
async def propose_build(session: AsyncSession, args: BuildArgs, ctx: AgentContext) -> ToolResult:
    st = state_of(ctx)
    m = find_member(st, args.pokemon) if args.pokemon else st.by_slot(st.focus)
    if m is None:
        return ToolResult.error(f"{args.pokemon or 'that Pokémon'} isn't in the calculator")
    p = st.proposal if st.proposal is not None and st.proposal.slot == m.slot else None
    try:
        build = await build_suggest.suggest_build(
            session, m.pokemon_id, m.form_id, request=args.request[:300],
            current=p.build if p else None, history=p.thread if p else [],
            attempts=1, usage=ctx.extra.get("usage"),
        )
    except build_suggest.SuggestError as e:
        msg = str(e)
        return ToolResult.error("build suggestions need an LLM key" if "LLM key" in msg else msg)
    text = (f"Proposed build for {_who(m)}: moves {', '.join(build.moves)}; ability "
            f"{build.ability}; nature {build.nature}; item {build.item}; EVs {ev_text(build.evs)}. "
            f"{build.why}")
    chunk = RetrievedChunk(
        id=-(_TOOL_BASE + 900_000 + m.slot), pokemon_id=m.pokemon_id, pokemon_name=m.name,
        dex_number=m.dex_number, chunk_type="calc_build", source_ref="coach build",
        content=text, score=1.0,
    )
    view = BuildProposalView(slot=m.slot, pokemon=m.name, build=build, chunk_refs=[0])
    return ToolResult(chunks=[chunk], views=[view], summary=f"{m.name}: {build.nature} "
                      f"{build.item or ''}".strip(), data={"why": build.why, "name": m.name})

