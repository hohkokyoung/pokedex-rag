"""The home damage calculator's coach: questions over the calculator's live state."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import trace as plan_trace
from app.agent.runner import run_question
from app.agent.sse import _sse
from app.agent.tools import AgentContext
from app.core.database import async_session_factory, get_session
from app.schemas.calc import (
    CalcAskRequest,
    CalcHitOut,
    CalcHpOut,
    CalcMoveOut,
    CalcOrderOut,
    CalcStepOut,
    CalcTurnOut,
    CalcTurnRequest,
)
from app.services import calc_turn
from app.services import damage_calc as dc
from app.services.calc_state import UnknownInSlot, resolve_slots, resolve_state

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calc", tags=["calc"])


@router.post("/turn", response_model=CalcTurnOut)
async def calc_turn_route(payload: CalcTurnRequest,
                          session: AsyncSession = Depends(get_session)) -> CalcTurnOut:
    """Play one calculator turn: order, targeting, HP carried over, Focus Sash, KO calls.

    The same turn the website shows (``lib/calcTurn``), with types, stats and moves re-read
    from the DB. Pure code, no LLM.
    """
    try:
        members = await resolve_slots(session, payload.slots, strict=True)
    except UnknownInSlot as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    by = {m.slot: m for m in members}
    slots = [
        calc_turn.TurnSlot(
            mon=by[i].mon, set=by[i].set,
            move=calc_turn.TurnMove(m.type, m.damage_class, m.power, m.target, m.priority)
            if (m := by[i].move) else None,
        ) if i in by else calc_turn.TurnSlot(mon=None)
        for i in range(4)
    ]
    # Unaimed slots aim straight across, as the website starts out.
    default_aim = [2, 3, 0, 1]
    aims = [by[i].aim if i in by and by[i].aim is not None else default_aim[i] for i in range(4)]
    f = payload.field
    t = calc_turn.play_turn(
        calc_turn.TurnField(level=payload.level, doubles=payload.doubles, weather=f.weather,
                            terrain=f.terrain, reflect=f.reflect, lightscreen=f.lightscreen,
                            crit=f.crit, burn=f.burn, friend_guard=f.friend_guard),
        slots, aims,
    )

    def hit(h: calc_turn.Hit) -> CalcHitOut:
        r: dc.Result = h.r
        return CalcHitOut(attacker=h.frm, target=h.to, move=by[h.frm].move.name,  # type: ignore[union-attr]
                          min_pct=r.min_pct, max_pct=r.max_pct, ko_hits=r.ko, te=r.te,
                          stab=r.stab, attack=r.A, defense=r.D, base=r.base, mod=r.mod,
                          ko=h.ko, sash=h.sash, friendly_fire=h.ff)

    return CalcTurnOut(
        order=[CalcOrderOut(slot=o.i, priority=o.pri, speed=o.spe) for o in t.order],
        steps=[CalcStepOut(slot=s.i, skipped=s.skipped, at_risk=s.at_risk,
                           hits=[hit(h) for h in s.hits]) for s in t.steps],
        hp=[CalcHpOut(slot=i, lo=x.lo, hi=x.hi, sash=x.sash) for i, x in t.hp.items()],
        aims={i: t.aim[i] for i in t.active},
        moves=[CalcMoveOut(slot=m.slot, name=m.move.name, type=m.move.type,
                           damage_class=m.move.damage_class, power=m.move.power,
                           target=m.move.target, priority=m.move.priority)
               for m in members if m.move],
    )


@router.post("/ask")
async def calc_ask(payload: CalcAskRequest) -> StreamingResponse:
    """SSE coaching over the calculator, planned like Ask (see ``app.agent``).

    The state (sets, moves, field, hits, proposal + thread) comes with the question; types,
    stats and move data are re-read from the DB. Nothing is saved: Apply happens client-side.
    Events: ``plan`` (the calc context step first), ``step``*, ``view``* (damage, survive,
    build proposal and dex views), ``sources``, ``delta``*, ``done``.
    """

    async def event_stream() -> AsyncIterator[str]:
        planner = None
        try:
            async with async_session_factory() as session:
                state = await resolve_state(session, payload)
            ctx = AgentContext(scope="calc", extra={"calc": state})
            async for name, data in run_question(payload.question, "calc", ctx=ctx):
                if name == "plan" and planner is None:
                    planner = data["planner"]
                if name == "done":
                    # Log before `done`: the client stops reading at `done`.
                    await _log(payload.question, planner, ctx.extra.get("trace"))
                yield _sse(name, data)
        except Exception as exc:  # noqa: BLE001 — surface as a stream error event
            log.exception("calc coaching failed")
            yield _sse("error", {"message": f"Coaching failed: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _log(question: str, planner: str | None, trace: dict | None = None) -> None:
    """Record the question and its plan trace ("calc-llm" / "calc-keyword")."""
    await plan_trace.record(question, f"calc-{planner or 'keyword'}", trace)
