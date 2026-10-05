/* Team rating — one deterministic model shared by the /teams summary cards and
   the full report on /teams/{id}, so both always show the same grades.

   Built only from the analysis engine's output (`TeamAnalysis`). Thresholds
   mirror the engine's role rules in backend/app/services/team_analysis.py:
   fast attacker = base Speed 100+, wall = HP+Def+SpD 280+, wallbreaker =
   best attacking stat 110+. */

import type { TeamAnalysis, VsOpponent } from "@/lib/api";
import { ATTACK_ORDER, typingEff } from "@/lib/typeChart";

export const FAST_SPEED = 100;

export type Grade = "A" | "B" | "C" | "D" | "F";
export type AreaKey = "coverage" | "defence" | "speed" | "roles" | "sets" | "roster";

export type Area = {
  key: AreaKey;
  label: string;
  score: number; // 0–100
  grade: Grade;
  headline: string; // the one-line verdict, e.g. "Hits 12 of 18 types"
  fix: string | null; // what to do about it; null when there's nothing to fix
};

export type TypeCover = { type: string; now: boolean; learnable: boolean };
/** Per attacking type: `weak` is weighted (a 4× weakness counts 2); `members`/`quad` are plain counts. */
export type TypeThreat = { type: string; weak: number; resist: number; members: number; quad: number; problem: boolean };

export type Rating = {
  overall: number;
  grade: Grade;
  /** True while the overall is held down because the roster isn't full. */
  capped: boolean;
  /** The highest overall this roster can reach: 100 × distinct species / 6. */
  ceiling: number;
  areas: Area[];
  /** Per-type detail behind the coverage and defence areas. */
  cover: TypeCover[];
  threats: TypeThreat[];
};

/** How much each area counts towards the overall rating. */
export const WEIGHTS: Record<AreaKey, number> = {
  coverage: 0.22,
  defence: 0.22,
  roles: 0.15,
  speed: 0.14,
  sets: 0.15,
  roster: 0.12,
};

export const gradeOf = (score: number): Grade =>
  score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : score >= 40 ? "D" : "F";

export const gradeTone = (g: Grade) => (g === "A" || g === "B" ? "good" : g === "C" ? "fair" : "poor");

const clamp = (x: number, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, x));
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const orList = (xs: string[]) =>
  xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} or ${xs[xs.length - 1]}`;

/** Defending types that resist `atk`, strongest resist first. */
const resistersOf = (atk: string) =>
  ATTACK_ORDER.filter((d) => typingEff(atk, [d]) < 1).sort((x, y) => typingEff(atk, [x]) - typingEff(atk, [y]));

export function rateTeam(size: number, a: TeamAnalysis): Rating {
  const members = a.defensive.matrix;
  const stab = members.flatMap((m) => m.types);

  // Coverage — STAB plus moves actually on the slots; learnable-only moves are reported separately.
  const setTypes = a.offensive.coverage_types.filter((t) => !a.offensive.from_learnset.includes(t));
  const hits = (atk: string[], d: string) => atk.some((t) => typingEff(t, [d]) >= 2);
  const cover: TypeCover[] = ATTACK_ORDER.map((d) => ({
    type: d,
    now: hits([...stab, ...setTypes], d),
    learnable: hits([...stab, ...a.offensive.coverage_types], d),
  }));
  const now = cover.filter((c) => c.now).length;
  const could = cover.filter((c) => c.learnable).length;
  const missing = cover.filter((c) => !c.now).map((c) => cap(c.type));

  // Defence — per attacking type, 4× weaknesses count double, resists and immunities offset them.
  const threats: TypeThreat[] = ATTACK_ORDER.map((t) => {
    const mult = members.map((m) => m.multipliers[t] ?? 1);
    const weak = mult.reduce((s, x) => s + (x >= 4 ? 2 : x >= 2 ? 1 : 0), 0);
    const resist = mult.filter((x) => x < 1).length;
    const membersWeak = mult.filter((x) => x >= 2).length;
    const quad = mult.filter((x) => x >= 4).length;
    return { type: t, weak, resist, members: membersWeak, quad, problem: weak >= 2 && weak > resist };
  });
  const problems = threats.filter((t) => t.problem).sort((x, y) => y.weak - y.resist - (x.weak - x.resist));

  // Speed and roles — straight from the engine's per-member base stats.
  // Speed counts the set: Choice Scarf, Speed Boost and speed-raising setup lift a member.
  const roles = a.roles.members;
  const spe = (r: (typeof roles)[number]) => r.eff_speed ?? r.speed;
  const fastest = [...roles].sort((x, y) => spe(y) - spe(x))[0];
  const fastCount = roles.filter((r) => spe(r) >= FAST_SPEED).length;
  const setMembers = a.sets?.members ?? [];
  const priorityUsers = setMembers.filter((m) => m.priority.length).map((m) => m.name);
  const missingRoles = a.roles.missing_roles.map((r) => r.split(" / ")[0]);

  const areas: Area[] = [];
  const push = (key: AreaKey, label: string, score: number, headline: string, fix: string | null) =>
    areas.push({ key, label, score: Math.round(clamp(score)), grade: gradeOf(clamp(score)), headline, fix });

  push(
    "coverage",
    "Coverage",
    (now / 15) * 100, // 15+ of 18 is excellent; full 18 is rarely reachable
    `Hits ${now} of 18 types super-effectively`,
    now >= 15
      ? null
      : could > now
        ? `Learnable moves would reach ${could} of 18 — add them to the empty move slots.`
        : `Nothing hits ${orList(missing.slice(0, 3))} hard — add a move or member that does.`,
  );

  const worst = problems[0];
  push(
    "defence",
    "Defence",
    100 - problems.reduce((s, p) => s + 18 + 8 * (p.weak - p.resist - 1), 0),
    problems.length === 0
      ? "No type hits several members unchecked"
      : `${problems.length} weak spot${problems.length > 1 ? "s" : ""}: ${problems.slice(0, 3).map((p) => cap(p.type)).join(", ")}`,
    worst
      ? `${cap(worst.type)} hits ${worst.members} member${worst.members > 1 ? "s" : ""} super-effectively${worst.quad ? ` (${worst.quad === worst.members ? "" : `${worst.quad} `}for 4×)` : ""} and ${worst.resist ? `only ${worst.resist} resist${worst.resist > 1 ? "" : "s"}` : "nothing resists it"} — add a ${orList(resistersOf(worst.type).slice(0, 2).map(cap))} type.`
      : null,
  );

  push(
    "speed",
    "Speed",
    // Priority attacks partly make up for a slow team.
    fastest ? ((spe(fastest) - 50) / (FAST_SPEED + 10 - 50)) * 100 + (fastCount ? 0 : 12 * Math.min(2, priorityUsers.length)) : 0,
    fastest
      ? fastCount
        ? `${fastCount} fast member${fastCount > 1 ? "s" : ""} (Speed ${FAST_SPEED}+ with their sets)`
        : `Fastest is ${fastest.name} at Speed ${spe(fastest)}${priorityUsers.length ? ` · priority on ${priorityUsers.join(", ")}` : ""}`
      : "No members yet",
    fastCount ? null : `Nothing reaches Speed ${FAST_SPEED} — add a fast attacker, a Choice Scarf or a speed-boosting move.`,
  );

  push(
    "roles",
    "Roles",
    ((3 - missingRoles.length) / 3) * 100,
    missingRoles.length ? `Missing ${orList(missingRoles)}` : "Has a fast attacker, a wall and a wallbreaker",
    missingRoles.length ? `Add a ${missingRoles[0]}.` : null,
  );

  // Sets — held items, abilities and set moves (setup, priority, recovery, support).
  if (setMembers.length) {
    const avg = setMembers.reduce((s, m) => s + m.score, 0) / setMembers.length;
    const noItem = setMembers.filter((m) => !m.item);
    const noAbility = setMembers.filter((m) => !m.ability);
    const thin = setMembers.filter((m) => m.moves_set < 4);
    const setup = setMembers.filter((m) => m.setup.length);
    const bits = [
      `${setMembers.length - noItem.length}/${setMembers.length} hold an item`,
      setup.length ? `${setup.length} can set up` : null,
      `${setMembers.reduce((s, m) => s + m.moves_set, 0)}/${setMembers.length * 4} moves set`,
    ].filter(Boolean);
    const names = (xs: { name: string }[]) => orList(xs.slice(0, 3).map((x) => x.name)).replace(/ or /, " and ");
    push(
      "sets",
      "Sets",
      avg,
      bits.join(" · "),
      thin.length > setMembers.length / 2
        ? `${thin.length} members have empty move slots — set their moves so the matchups use what they'll really click.`
        : noItem.length
          ? `${names(noItem)} ${noItem.length > 1 ? "hold" : "holds"} no item — Life Orb, a Choice item or Leftovers change damage and bulk.`
          : noAbility.length
            ? `Pick an ability for ${names(noAbility)}.`
            : !setup.length && !priorityUsers.length
              ? "No setup or priority moves — a Swords Dance or Dragon Dance user can snowball a game."
              : null,
    );
  }

  // Standard rules allow one of each species, so a repeat only counts once.
  const names = members.map((m) => m.name);
  const dupes = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
  const unique = size - (names.length - new Set(names).size);
  push(
    "roster",
    "Roster",
    (unique / 6) * 100,
    `${size} of 6 slots filled${dupes.length ? ` · ${dupes.join(", ")} twice` : ""}`,
    dupes.length
      ? `Only one of each species is allowed — swap the second ${dupes[0]} for something new.`
      : size < 6
        ? `Fill ${6 - size} more slot${6 - size > 1 ? "s" : ""} — every other grade firms up with a full team.`
        : null,
  );

  // Small rosters look artificially safe (fewer members, fewer shared weaknesses), so the
  // overall is scaled by how full the team is: a missing slot is a missing sixth of the
  // team. 5 distinct → ×5/6, 3 → ×½; only six different species can reach 100.
  const raw = Math.round(areas.reduce((s, x) => s + x.score * WEIGHTS[x.key], 0));
  const ceiling = Math.round((100 * unique) / 6);
  const overall = unique >= 6 ? raw : Math.round((raw * unique) / 6);
  return { overall, grade: gradeOf(overall), capped: unique < 6, ceiling, areas, cover, threats };
}

/** Each matchup scorecard factor in plain words, from your side. */
export function matchupFactors(vs: VsOpponent) {
  const wins = vs.cells.filter((c) => c.outcome === "win").length;
  const losses = vs.cells.filter((c) => c.outcome === "lose").length;
  const text: Record<string, [string, string, string]> = {
    h2h: [`Wins ${wins} of ${vs.cells.length} one-on-ones`, `Loses ${losses} of ${vs.cells.length} one-on-ones`, `One-on-ones split ${wins}–${losses}`],
    reach: ["Hits more of their team hard", "They hit more of yours hard", "Similar type reach"],
    damage: ["Deals more damage", "They deal more damage", "Similar damage"],
    speed: ["Faster", "They're faster", "Similar speed"],
  };
  return vs.scorecard.map((r) => ({
    key: r.key,
    edge: r.edge,
    weight: r.weight,
    label: text[r.key]?.[r.edge === "ours" ? 0 : r.edge === "theirs" ? 1 : 2] ?? r.label,
  }));
}

/** A matchup is only provisional while either side is short of six or they differ in size. */
export const isProvisional = (vs: VsOpponent) =>
  vs.our_members.length !== vs.their_members.length || vs.our_members.length < 6;
