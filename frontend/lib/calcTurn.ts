/* One calculator turn played out: who moves first, who each move hits (doubles
   targeting), HP carried from hit to hit as a worst/best range, Focus Sash, and KO
   calls. Moved out of the home page's calculator so the backend can mirror it
   (services/calc_turn.py, pinned by `make damage-fixtures`). Change it here, port the
   change, regenerate the fixtures, run the tests. */

import { calcHit, natMul, statFull, type CalcMonLite, type CalcSide, type DcField, type DcResult } from "./damageCalc";

/** A slot's chosen move, with the PokéAPI `move_targets` identifier and priority. */
export type TurnMove = { type: string; damage_class: string; power: number; target: string | null; priority: number };
/** Slots 0–1 are your side, 2–3 the opponent's; `mon` is null for an empty slot. */
export type TurnSlot = { mon: CalcMonLite | null; set: CalcSide; move: TurnMove | null | undefined };
export type TurnField = {
  level: number; doubles: boolean; weather: string; terrain: string;
  reflect: boolean; lightscreen: boolean; crit: boolean; burn: boolean; friendGuard: boolean;
};
export type TurnState = { field: TurnField; slots: TurnSlot[]; aims: number[] };

// Doubles targeting, from the move's PokéAPI `move_targets` identifier.
export type TgKind = "sel" | "rand" | "foes" | "all" | "ally";
export const tgKind = (t?: string | null): TgKind =>
  t === "all-opponents" ? "foes" : t === "all-other-pokemon" ? "all" : t === "ally" ? "ally" : t === "random-opponent" ? "rand" : "sel";
export const isSpread = (k: TgKind) => k === "foes" || k === "all";
export const isAimable = (k: TgKind) => k === "sel" || k === "rand";
export const sideOf = (i: number) => (i < 2 ? 0 : 1);

export type DcHit = { from: number; to: number; r: DcResult; ff: boolean };
export type TurnHit = DcHit & { ko: "yes" | "maybe" | null; sash: boolean };
export type TurnStep = { i: number; skipped: boolean; atRisk: boolean; hits: TurnHit[] };
export type TurnOrder = { i: number; pri: number; spe: number };
export type HpRange = { lo: number; hi: number; sash: boolean };

/** The turn's helpers (targeting, a move's hits) and its result (order, steps, HP). */
export function playTurn({ field, slots, aims }: TurnState) {
  const { level, doubles, weather, terrain, reflect, lightscreen, crit, burn, friendGuard } = field;
  const active = doubles ? [0, 1, 2, 3] : [0, 2];
  const foesOf = (i: number) => active.filter((j) => sideOf(j) !== sideOf(i));
  const mateOf = (i: number) => active.find((j) => j !== i && sideOf(j) === sideOf(i));
  // Aim at a filled opposing slot: the one picked, else the first with a Pokémon in it.
  const targetsOf = (i: number) => foesOf(i).filter((j) => slots[j].mon);
  const aimOf = (i: number) => (targetsOf(i).includes(aims[i]) ? aims[i] : targetsOf(i)[0] ?? foesOf(i)[0]);
  const kindOf = (i: number) => tgKind(slots[i].move?.target);
  const baseField: DcField = { level, doubles, spread: false, weather, terrain, reflect, lightscreen, crit, burn, helpingHand: false, friendGuard };

  // The hits `move` from slot `u` makes, following the move's real targeting. `up(t)` says whether slot t is
  // still standing and `hpOf(t)` its HP going into the hit, so the turn can be played out in order.
  const hitsFor = (u: number, move: TurnMove | null | undefined, aim: number, up: (t: number) => boolean = () => true, hpOf: (t: number) => number = (t) => slots[t].set.hp): DcHit[] => {
    const a = slots[u], mate = mateOf(u);
    if (!a.mon || !move || move.power <= 0) return [];
    // Singles has one foe and no partner: every move is a plain single-target hit.
    const k = doubles ? tgKind(move.target) : "sel";
    if (k === "ally") return [];
    const helped = doubles && mate !== undefined && !!slots[mate].mon && up(mate) && kindOf(mate) === "ally";
    const standing = foesOf(u).filter((t) => slots[t].mon && up(t));
    // A single-target move aimed at a fainted foe switches to its partner, as in the games.
    const single = slots[aim]?.mon && up(aim) ? aim : standing[0];
    const tos = [...(isSpread(k) ? standing : single !== undefined ? [single] : []), ...(k === "all" && mate !== undefined && slots[mate].mon && up(mate) ? [mate] : [])];
    return tos.map((t) => {
      // Screens and Friend Guard sit on the opponent's side; the burn toggle is on your attacker.
      const opp = sideOf(t) === 1;
      const fld = { ...baseField, spread: isSpread(k), helpingHand: helped, reflect: reflect && opp, lightscreen: lightscreen && opp, friendGuard: friendGuard && opp, burn: burn && sideOf(u) === 0 };
      return { from: u, to: t, r: calcHit(a.mon!, a.set, slots[t].mon!, { ...slots[t].set, hp: hpOf(t) }, move, fld), ff: sideOf(t) === sideOf(u) };
    });
  };

  const spe = (s: TurnSlot) => (s.mon ? statFull(s.mon.stats.speed, level, s.set.iv.spe, s.set.ev.spe, natMul(s.set.nat, "spe"), false) : 0);
  // Turn order: move priority first, then Speed.
  const order: TurnOrder[] = active.filter((i) => slots[i].mon)
    .map((i) => ({ i, pri: slots[i].move?.priority ?? 0, spe: spe(slots[i]) }))
    .sort((x, y) => y.pri - x.pri || y.spe - x.spe);

  // Play the turn out in order. HP carries over from hit to hit as a range — `lo` if every roll is high,
  // `hi` if every roll is low — starting from each Pokémon's current HP. A Pokémon that is KO'd even on
  // low rolls doesn't get to move, and Focus Sash saves its holder once, from full HP.
  const hp: Record<number, HpRange> = {};
  for (const i of active) hp[i] = { lo: slots[i].set.hp, hi: slots[i].set.hp, sash: false };
  const standing = (t: number) => hp[t].hi > 0;
  const steps: TurnStep[] = order.map(({ i }) => {
    if (!standing(i)) return { i, skipped: true, atRisk: false, hits: [] as TurnHit[] };
    const atRisk = hp[i].lo <= 0;
    const hs: TurnHit[] = hitsFor(i, slots[i].move, aimOf(i), standing, (t) => hp[t].hi).map((h) => {
      const x = hp[h.to], d = slots[h.to].set;
      if (h.r.te === 0) return { ...h, ko: null, sash: false };
      const sash = d.item === "Focus Sash" && !x.sash && x.lo >= 100 && h.r.maxPct >= 100;
      if (sash) { x.sash = true; x.lo = 1; x.hi = Math.max(1, 100 - h.r.minPct); }
      else { x.lo = Math.max(0, x.lo - h.r.maxPct); x.hi = Math.max(0, x.hi - h.r.minPct); }
      return { ...h, ko: x.hi <= 0 ? "yes" : x.lo <= 0 ? "maybe" : null, sash };
    });
    return { i, skipped: false, atRisk, hits: hs };
  });

  return { active, foesOf, mateOf, targetsOf, aimOf, kindOf, hitsFor, order, steps, hp };
}
