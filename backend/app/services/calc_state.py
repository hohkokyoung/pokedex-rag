"""Resolve the calculator state the client sends into damage-maths inputs.

Types, base stats and move data come from the database, never from the client; the
client's ``hits`` are kept verbatim as "what the calculator shows" (they include the
turn simulation, which isn't ported).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Move, Pokemon, PokemonForm, PokemonType, Type
from app.schemas.calc import CalcAskRequest, CalcHitIn, CalcProposal
from app.services import damage_calc as dc

STAT_KEYS = ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")


@dataclass(frozen=True)
class CalcMove:
    move_id: int
    name: str
    type: str
    damage_class: str
    power: int

    @property
    def maths(self) -> dc.MoveIn:
        return dc.MoveIn(self.type, self.damage_class, self.power)


@dataclass
class CalcMember:
    slot: int
    side: int  # 0 = the user's, 1 = the opponent's
    name: str
    pokemon_id: int
    form_id: int | None
    dex_number: int
    mon: dc.Mon
    set: dc.Side
    move: CalcMove | None
    aim: int | None


@dataclass
class CalcState:
    level: int
    doubles: bool
    field: dc.Field
    members: list[CalcMember]
    focus: int
    hits: list[CalcHitIn] = field(default_factory=list)
    proposal: CalcProposal | None = None

    def by_slot(self, slot: int) -> CalcMember | None:
        return next((m for m in self.members if m.slot == slot), None)

    def foes_of(self, m: CalcMember) -> list[CalcMember]:
        return [x for x in self.members if x.side != m.side]


async def move_by_name(session: AsyncSession, name: str) -> CalcMove | None:
    row = (
        await session.execute(
            select(Move, Type.identifier).join(Type, Type.id == Move.type_id)
            .where(func.lower(Move.name) == name.strip().lower()).limit(1)
        )
    ).first()
    if row is None:
        return None
    mv, mtype = row
    return CalcMove(mv.id, mv.name, mtype, mv.damage_class or "status", mv.power or 0)


async def resolve_state(session: AsyncSession, req: CalcAskRequest) -> CalcState:
    ids = {s.pokemon_id for s in req.slots}
    species = {
        p.id: p for p in (
            await session.execute(
                select(Pokemon).options(selectinload(Pokemon.types).selectinload(PokemonType.type))
                .where(Pokemon.id.in_(ids))
            )
        ).scalars().all()
    } if ids else {}
    form_ids = {s.form_id for s in req.slots if s.form_id}
    forms = {
        f.id: f for f in (
            await session.execute(select(PokemonForm).where(PokemonForm.id.in_(form_ids)))
        ).scalars().all()
    } if form_ids else {}

    members: list[CalcMember] = []
    for s in sorted(req.slots, key=lambda x: x.slot):
        base = species.get(s.pokemon_id)
        if base is None:
            continue
        form = forms.get(s.form_id) if s.form_id else None
        src = form or base
        types = list(form.types) if form else [pt.type.identifier for pt in base.types]
        mon = dc.Mon(types=types, stats={k: getattr(src, k) for k in STAT_KEYS})
        mv = await move_by_name(session, s.move) if s.move else None
        members.append(CalcMember(
            slot=s.slot, side=0 if s.slot < 2 else 1, name=form.name if form else base.name,
            pokemon_id=base.id, form_id=form.id if form else None, dex_number=base.dex_number,
            mon=mon,
            set=dc.Side(nat=s.nature, ev={**dict.fromkeys(dc.SKEYS, 0), **s.evs},
                        iv={**dict.fromkeys(dc.SKEYS, 31), **s.ivs}, item=s.item or "None",
                        abil=s.ability or "None", hp=s.hp or 1),
            move=mv, aim=s.aim,
        ))
    f = req.field
    fld = dc.Field(level=req.level, doubles=req.doubles, weather=f.weather, terrain=f.terrain,
                   reflect=f.reflect, lightscreen=f.lightscreen, crit=f.crit, burn=f.burn,
                   friend_guard=f.friend_guard)
    return CalcState(level=req.level, doubles=req.doubles, field=fld, members=members,
                     focus=req.focus, hits=req.hits, proposal=req.proposal)
