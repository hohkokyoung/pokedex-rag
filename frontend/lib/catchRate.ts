// Catch-rate maths — Gen 8+ (Sword/Shield onward) formula, client-side only.
//
//   a = (3M − 2H) / 3M × rate × ball × status × lowLevel        (a ≥ 255 → caught)
//   shake check b = 65536 / (255 / a)^(3/16), passed 4 times    → (b/65536)^4
//   critical capture: chance floor(a × dex × charm / 6) / 256, needs only 1 check
// Ball/status values follow Bulbapedia's Gen 8+ tables.

export type Status = "none" | "sleep" | "freeze" | "paralysis" | "burn" | "poison";
export const STATUS_MUL: Record<Status, number> = {
  none: 1, sleep: 2.5, freeze: 2.5, paralysis: 1.5, burn: 1.5, poison: 1.5,
};

export type CatchMon = {
  name: string; dex: number; types: string[]; captureRate: number;
  baseHp: number; baseSpeed: number; weightKg: number;
  genderRate: number; // -1 genderless
};

export type CatchCtx = {
  hpPct: number;          // 0–100 of current HP (≥1 HP)
  level: number;          // wild level
  myLevel: number;        // your lead's level (Level Ball)
  turn: number;           // battle turn, 1 = first throw
  status: Status;
  night: boolean;         // night or cave (Dusk Ball)
  water: boolean;         // fishing / surfing / underwater (Dive, Lure)
  caught: boolean;        // species already registered as caught (Repeat Ball)
  loveMatch: boolean;     // your lead: same species, opposite gender (Love Ball)
  dexCaught: number;      // # species caught (critical capture)
  charm: boolean;         // Catching Charm
};

export const DEFAULT_CTX: CatchCtx = {
  hpPct: 100, level: 30, myLevel: 30, turn: 1, status: "none", night: false, water: false,
  caught: false, loveMatch: false, dexCaught: 0, charm: false,
};

const MOON = new Set([30, 33, 35, 39, 300, 517]); // evolve with a Moon Stone
const ULTRA_BEAST = new Set([793, 794, 795, 796, 797, 798, 799, 803, 804, 805, 806]);

export type Ball = {
  id: string; name: string; top: string; band?: string; accent?: string;
  /** Multiplier, plus why. `rateAdd` is the Heavy Ball's flat catch-rate change. */
  rule: (m: CatchMon, c: CatchCtx) => { mul: number; why: string; rateAdd?: number; sure?: boolean };
};

const flat = (mul: number, why = "") => () => ({ mul, why });
export const BALLS: Ball[] = [
  { id: "poke", name: "Poké Ball", top: "#e3350d", rule: flat(1, "standard") },
  { id: "great", name: "Great Ball", top: "#2f6bff", accent: "#e3350d", rule: flat(1.5, "always ×1.5") },
  { id: "ultra", name: "Ultra Ball", top: "#22252b", accent: "#f5c400", rule: flat(2, "always ×2") },
  { id: "master", name: "Master Ball", top: "#7b3fc4", accent: "#e44fa3", rule: () => ({ mul: 255, why: "never fails", sure: true }) },
  { id: "quick", name: "Quick Ball", top: "#2f8fe0", accent: "#f5c400", rule: (_, c) => c.turn === 1 ? { mul: 5, why: "first turn ×5" } : { mul: 1, why: "only ×5 on turn 1" } },
  { id: "dusk", name: "Dusk Ball", top: "#1f5a3a", accent: "#e3350d", rule: (_, c) => c.night ? { mul: 3, why: "night / cave ×3" } : { mul: 1, why: "×3 only at night or in caves" } },
  { id: "timer", name: "Timer Ball", top: "#f4f4f4", band: "#e3350d", accent: "#22252b", rule: (_, c) => {
    const mul = Math.min(4, 1 + (c.turn - 1) * 1229 / 4096);
    return { mul, why: c.turn >= 11 ? "maxed at ×4 (turn 11+)" : `turn ${c.turn}: 1 + 0.3 per turn` };
  } },
  { id: "net", name: "Net Ball", top: "#2fb7a8", accent: "#22252b", rule: (m) => m.types.some((t) => t === "bug" || t === "water") ? { mul: 3.5, why: "Bug/Water ×3.5" } : { mul: 1, why: "×3.5 only vs Bug or Water" } },
  { id: "nest", name: "Nest Ball", top: "#7cbf3a", accent: "#e7b33a", rule: (_, c) => c.level < 30 ? { mul: Math.max(1, (41 - c.level) / 10), why: `(41 − Lv ${c.level}) / 10` } : { mul: 1, why: "no bonus at Lv 30+" } },
  { id: "repeat", name: "Repeat Ball", top: "#e8a21a", accent: "#e3350d", rule: (_, c) => c.caught ? { mul: 3.5, why: "already caught ×3.5" } : { mul: 1, why: "×3.5 only if caught before" } },
  { id: "dive", name: "Dive Ball", top: "#3a8fe0", accent: "#9fd6ff", rule: (_, c) => c.water ? { mul: 3.5, why: "on/under water ×3.5" } : { mul: 1, why: "×3.5 only on water / fishing" } },
  { id: "lure", name: "Lure Ball", top: "#2fa8a0", accent: "#e3350d", rule: (_, c) => c.water ? { mul: 4, why: "hooked by fishing ×4" } : { mul: 1, why: "×4 only when fishing" } },
  { id: "fast", name: "Fast Ball", top: "#f08a1a", accent: "#f5d400", rule: (m) => m.baseSpeed >= 100 ? { mul: 4, why: `base Speed ${m.baseSpeed} ≥ 100 ×4` } : { mul: 1, why: `base Speed ${m.baseSpeed} < 100` } },
  { id: "level", name: "Level Ball", top: "#e8a21a", accent: "#e3350d", rule: (_, c) => {
    const r = c.myLevel / c.level;
    if (r >= 4) return { mul: 8, why: "your level ≥ 4× theirs ×8" };
    if (r >= 2) return { mul: 4, why: "your level ≥ 2× theirs ×4" };
    if (r > 1) return { mul: 2, why: "your level higher ×2" };
    return { mul: 1, why: "your level isn't higher" };
  } },
  { id: "heavy", name: "Heavy Ball", top: "#8a94a3", accent: "#2f6bff", rule: (m) => {
    const w = m.weightKg;
    const add = w >= 300 ? 30 : w >= 200 ? 20 : w >= 100 ? 0 : -20;
    return { mul: 1, rateAdd: add, why: `${w} kg → catch rate ${add >= 0 ? "+" : "−"}${Math.abs(add)}` };
  } },
  { id: "moon", name: "Moon Ball", top: "#2b3a6b", accent: "#f5d400", rule: (m) => MOON.has(m.dex) ? { mul: 4, why: "Moon Stone evolver ×4" } : { mul: 1, why: "×4 only for Moon Stone evolvers" } },
  { id: "love", name: "Love Ball", top: "#f06aa8", accent: "#ffffff", rule: (m, c) => m.genderRate >= 0 && c.loveMatch ? { mul: 8, why: "same species, opposite gender ×8" } : { mul: 1, why: "×8 vs same species, opposite gender" } },
  { id: "dream", name: "Dream Ball", top: "#f29ac4", accent: "#8b5cf6", rule: (_, c) => c.status === "sleep" ? { mul: 4, why: "asleep ×4" } : { mul: 1, why: "×4 only if asleep" } },
  { id: "beast", name: "Beast Ball", top: "#2f6bff", accent: "#f5d400", rule: (m) => ULTRA_BEAST.has(m.dex) ? { mul: 5, why: "Ultra Beast ×5" } : { mul: 0.1, why: "not an Ultra Beast ×0.1" } },
  { id: "premier", name: "Premier Ball", top: "#f4f4f4", band: "#e3350d", rule: flat(1, "same as Poké Ball") },
];

export type CatchResult = {
  maxHp: number; hp: number;
  rate: number; hpFactor: number; ballMul: number; ballWhy: string; statusMul: number; lowLv: number;
  a: number; shake: number; crit: number; p: number; sure: boolean;
};

const hpStat = (base: number, lv: number) => Math.floor((2 * base + 15) * lv / 100) + lv + 10; // avg IV, 0 EV

export function catchChance(m: CatchMon, ball: Ball, c: CatchCtx): CatchResult {
  const maxHp = hpStat(m.baseHp, c.level);
  const hp = Math.max(1, Math.round(maxHp * c.hpPct / 100));
  const r = ball.rule(m, c);
  const rate = Math.max(1, m.captureRate + (r.rateAdd ?? 0));
  const hpFactor = (3 * maxHp - 2 * hp) / (3 * maxHp);
  const statusMul = STATUS_MUL[c.status];
  const lowLv = c.level < 20 ? (30 - c.level) / 10 : 1;
  const a = hpFactor * rate * r.mul * statusMul * lowLv;
  const base = { maxHp, hp, rate, hpFactor, ballMul: r.mul, ballWhy: r.why, statusMul, lowLv, a: Math.min(a, 255) };
  if (r.sure || a >= 255) return { ...base, shake: 1, crit: 0, p: 1, sure: true };
  const shake = Math.min(1, Math.floor(65536 / Math.pow(255 / a, 3 / 16)) / 65536);
  const dexMul = c.dexCaught > 600 ? 2.5 : c.dexCaught > 450 ? 2 : c.dexCaught > 300 ? 1.5 : c.dexCaught > 150 ? 1 : c.dexCaught > 30 ? 0.5 : 0;
  const crit = Math.min(255, Math.floor(a * dexMul * (c.charm ? 2 : 1) / 6)) / 256;
  const p = crit * shake + (1 - crit) * Math.pow(shake, 4);
  return { ...base, shake, crit, p, sure: false };
}

/** Throws needed to reach `target` odds of at least one catch. */
export const throwsFor = (p: number, target = 0.9) =>
  p >= 1 ? 1 : p <= 0 ? Infinity : Math.ceil(Math.log(1 - target) / Math.log(1 - p));
export const pct = (p: number) => (p >= 1 ? "100" : p >= 0.995 ? ">99" : p < 0.001 ? "<0.1" : (p * 100).toFixed(p < 0.1 ? 1 : 0));
