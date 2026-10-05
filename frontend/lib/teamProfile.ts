/* Team profile — "what kind of team is this?" at a glance. Derived only from
   ingested data: each member's base stats and typing, its set moves, and the
   rating model (lib/teamEval). Thresholds match the analysis engine's role
   rules (fast = base Speed 100+, wall = HP+Def+SpD 280+, wallbreaker = 110+). */

import type { Team, TeamAnalysis } from "@/lib/api";
import { titleCase } from "@/lib/pokeTypes";
import { FAST_SPEED, rateTeam, type Rating } from "@/lib/teamEval";

export type Lean = "Physical" | "Special" | "Mixed";

export type Profile = {
  style: string; // "Bulky offense", "Hyper offense", …
  styleWhy: string; // the numbers behind the style label
  lean: Lean;
  physical: number; // members leaning physical
  special: number; // members leaning special
  avg: Record<"hp" | "attack" | "defense" | "sp_attack" | "sp_defense" | "speed", number>;
  avgBst: number;
  avgSpeed: number;
  fastCount: number;
  speeds: { name: string; speed: number; sprite: string }[];
  coreTypes: string[]; // most common member types, most frequent first
  weakTo: { type: string; net: number }[]; // types more members are weak to than resist (4× counts double)
  strongVs: string[]; // types the team hits super-effectively now
  resists: { type: string; net: number }[]; // types more members resist than are weak to
  movesSet: number; // moves actually on the slots
  items: number; // members holding an item
  priority: number; // set moves with priority > 0
  gist: string;
  rating: Rating;
};

const KEYS = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"] as const;
const avgOf = (xs: number[]) => (xs.length ? Math.round(xs.reduce((s, x) => s + x, 0) / xs.length) : 0);
const andList = (xs: string[]) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);

/** Base-stat equivalents of a member's real Lv50 stats (EVs, IVs and nature included):
 *  the inverse of the stat formula for an uninvested, neutral, 31-IV Pokémon. Mirrors
 *  `as_built` in backend/app/services/stats.py so the cards and the engine agree. */
export function asBuilt(final: Record<string, number> | undefined, base: Record<string, number>): Record<string, number> {
  if (!final || !Object.keys(final).length) return base;
  return Object.fromEntries(
    KEYS.map((k) => {
      const v = final[k] ?? 0;
      const raw = k === "hp" ? ((v - 60) * 100) / 50 : ((v - 5) * 100) / 50;
      return [k, Math.max(1, Math.round((raw - 31) / 2))];
    }),
  );
}

export function profileTeam(team: Team, a: TeamAnalysis): Profile | null {
  // Stats as built, so EVs, IVs and natures move the style, lean and speed reads.
  const ms = team.members.map((m) => ({ ...m, base_stats: asBuilt(m.final_stats, m.base_stats) }));
  const species = team.members;
  if (!ms.length) return null;
  const rating = rateTeam(ms.length, a);

  const avg = Object.fromEntries(KEYS.map((k) => [k, avgOf(ms.map((m) => m.base_stats[k] ?? 0))])) as Profile["avg"];
  const avgBst = avgOf(species.map((m) => KEYS.reduce((s, k) => s + (m.base_stats[k] ?? 0), 0)));
  const off = avgOf(ms.map((m) => Math.max(m.base_stats.attack, m.base_stats.sp_attack)));
  const bulk = avgOf(ms.map((m) => m.base_stats.hp + m.base_stats.defense + m.base_stats.sp_defense));
  const avgSpeed = avg.speed;

  // Style from team averages (base stats), so the label is explainable by the numbers shown.
  const style =
    avgSpeed >= 95 && off >= 100 ? "Hyper offense"
    : avgSpeed <= 65 && off >= 100 ? "Slow powerhouse"
    : bulk >= 270 && off < 100 ? "Defensive"
    : off >= 100 && bulk >= 240 ? "Bulky offense"
    : off >= 100 ? "Offense"
    : "Balance";
  const styleWhy = `avg Speed ${avgSpeed} · attack ${off} · bulk ${bulk}`;

  // A member leans physical/special when its better attacking stat is 10+ ahead.
  const physical = ms.filter((m) => m.base_stats.attack >= m.base_stats.sp_attack + 10).length;
  const special = ms.filter((m) => m.base_stats.sp_attack >= m.base_stats.attack + 10).length;
  const lean: Lean = physical > special ? "Physical" : special > physical ? "Special" : "Mixed";

  const speeds = [...ms]
    .map((m) => ({ name: m.name, speed: m.base_stats.speed, sprite: m.sprite_url }))
    .sort((x, y) => y.speed - x.speed);
  const fastCount = speeds.filter((s) => s.speed >= FAST_SPEED).length;

  const freq = new Map<string, number>();
  for (const m of ms) for (const t of m.types) freq.set(t, (freq.get(t) ?? 0) + 1);
  const coreTypes = [...freq.entries()].sort((x, y) => y[1] - x[1]).map(([t]) => t);

  // Net per attacking type, so a one-Pokémon team still shows its weaknesses
  // (the defence *grade* separately only penalises types hitting 2+ members).
  const weakTo = rating.threats
    .filter((t) => t.weak > t.resist)
    .map((t) => ({ type: t.type, net: t.weak - t.resist }))
    .sort((x, y) => y.net - x.net);
  const strongVs = rating.cover.filter((c) => c.now).map((c) => c.type);
  const resists = rating.threats
    .filter((t) => t.resist > t.weak)
    .map((t) => ({ type: t.type, net: t.resist - t.weak }))
    .sort((x, y) => y.net - x.net);
  const movesSet = ms.reduce((s, m) => s + m.moves.length, 0);
  const items = ms.filter((m) => m.item).length;
  const priority = ms.reduce((s, m) => s + m.moves.filter((mv) => (mv.priority ?? 0) > 0 && mv.damage_class !== "status").length, 0);

  const speedLine = fastCount
    ? `${fastCount} fast member${fastCount > 1 ? "s" : ""} (avg Speed ${avgSpeed})`
    : `nothing reaches Speed ${FAST_SPEED} (avg ${avgSpeed})`;
  const weakLine = weakTo.length
    ? `${andList(weakTo.slice(0, 3).map((w) => titleCase(w.type)))} ${weakTo.length > 1 ? "hurt" : "hurts"} it`
    : "no type hits it unchecked";
  const gist = `${lean === "Mixed" ? "Mixed-attacking" : lean} ${style.toLowerCase()} on a ${coreTypes
    .slice(0, 2)
    .map(titleCase)
    .join("/")} core — ${speedLine}; ${weakLine}.`;

  return { style, styleWhy, lean, physical, special, avg, avgBst, avgSpeed, fastCount, speeds, coreTypes, weakTo, strongVs, resists, movesSet, items, priority, gist, rating };
}
