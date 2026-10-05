/* The damage calculator's maths, as a pure module (no React, relative imports only).

   The home calculator imports it, and so does `scripts/damage-fixtures.ts`, which writes
   reference cases the backend's port (`app/services/damage_calc.py`) is tested against —
   regenerate them (`make damage-fixtures`) whenever this file changes. */

import { typingEff } from "./typeChart";

export type SKey = "hp" | "atk" | "def" | "spa" | "spd" | "spe";
export type EVs = Record<SKey, number>;
export const SABBR: Record<SKey, string> = { hp: "HP", atk: "Atk", def: "Def", spa: "SpA", spd: "SpD", spe: "Spe" };

export const NAT: [string, string | null, string | null][] = [
  ["Hardy",null,null],["Lonely","Atk","Def"],["Brave","Atk","Spe"],["Adamant","Atk","SpA"],["Naughty","Atk","SpD"],
  ["Bold","Def","Atk"],["Docile",null,null],["Relaxed","Def","Spe"],["Impish","Def","SpA"],["Lax","Def","SpD"],
  ["Timid","Spe","Atk"],["Hasty","Spe","Def"],["Serious",null,null],["Jolly","Spe","SpA"],["Naive","Spe","SpD"],
  ["Modest","SpA","Atk"],["Mild","SpA","Def"],["Quiet","SpA","Spe"],["Bashful",null,null],["Rash","SpA","SpD"],
  ["Calm","SpD","Atk"],["Gentle","SpD","Def"],["Sassy","SpD","Spe"],["Careful","SpD","SpA"],["Quirky",null,null],
];

export const natMul = (name: string, key: SKey): number => {
  const r = NAT.find((x) => x[0] === name); if (!r || key === "hp") return 1;
  return r[1] === SABBR[key] ? 1.1 : r[2] === SABBR[key] ? 0.9 : 1;
};
export const statFull = (base: number, level: number, iv: number, ev: number, nm: number, isHP: boolean) => {
  const core = Math.floor((2 * base + iv + Math.floor(ev / 4)) * level / 100);
  return isHP ? core + level + 10 : Math.floor((core + 5) * nm);
};

/** What the maths needs of a Pokémon: its typing and base stats. */
export type CalcStats = { hp: number; attack: number; defense: number; sp_attack: number; sp_defense: number; speed: number };
export type CalcMonLite = { types: string[]; stats: CalcStats };
/** One side's set: nature, EVs/IVs, item, ability, and current HP as % of max. */
export type CalcSide = { nat: string; ev: EVs; iv: EVs; item: string; abil: string; hp: number };
export type CalcMoveIn = { type: string; damage_class: string; power: number };

// Held items the calc models. Type boosters and resist berries are keyed by the move type they touch.
export const TYPE_BOOST: Record<string, string> = {
  "Silk Scarf": "normal", "Charcoal": "fire", "Mystic Water": "water", "Magnet": "electric", "Miracle Seed": "grass", "Never-Melt Ice": "ice",
  "Black Belt": "fighting", "Poison Barb": "poison", "Soft Sand": "ground", "Sharp Beak": "flying", "Twisted Spoon": "psychic", "Silver Powder": "bug",
  "Hard Stone": "rock", "Spell Tag": "ghost", "Dragon Fang": "dragon", "Black Glasses": "dark", "Metal Coat": "steel", "Fairy Feather": "fairy",
};
export const RESIST_BERRY: Record<string, string> = {
  "Occa Berry": "fire", "Passho Berry": "water", "Wacan Berry": "electric", "Rindo Berry": "grass", "Yache Berry": "ice", "Chople Berry": "fighting",
  "Kebia Berry": "poison", "Shuca Berry": "ground", "Coba Berry": "flying", "Payapa Berry": "psychic", "Tanga Berry": "bug", "Charti Berry": "rock",
  "Kasib Berry": "ghost", "Haban Berry": "dragon", "Colbur Berry": "dark", "Babiri Berry": "steel", "Roseli Berry": "fairy",
};

export type DcField = {
  level: number; doubles: boolean; spread: boolean; weather: string; terrain: string;
  reflect: boolean; lightscreen: boolean; crit: boolean; burn: boolean; helpingHand: boolean; friendGuard: boolean;
};
export type DcResult = { minPct: number; maxPct: number; ko: number; te: number; stab: number; A: number; D: number; base: number; mod: number };
// hp = current HP as % of max; damage % stays relative to max HP, KO calls use current.
export function calcHit(atk: CalcMonLite, a: CalcSide, def: CalcMonLite, d: CalcSide, move: CalcMoveIn, f: DcField): DcResult {
  const { level } = f;
  const phys = move.damage_class === "physical";
  const aK: SKey = phys ? "atk" : "spa"; const dK: SKey = phys ? "def" : "spd";
  let A = statFull(phys ? atk.stats.attack : atk.stats.sp_attack, level, a.iv[aK], a.ev[aK], natMul(a.nat, aK), false);
  let D = statFull(phys ? def.stats.defense : def.stats.sp_defense, level, d.iv[dK], d.ev[dK], natMul(d.nat, dK), false);
  const HP = statFull(def.stats.hp, level, d.iv.hp, d.ev.hp, 1, true);
  if (a.item === "Choice Band" && phys) A = Math.floor(A * 1.5);
  if (a.item === "Choice Specs" && !phys) A = Math.floor(A * 1.5);
  if (a.abil === "Huge Power" && phys) A = Math.floor(A * 2);
  if (a.abil === "Guts" && f.burn && phys) A = Math.floor(A * 1.5);
  if (d.item === "Assault Vest" && !phys) D = Math.floor(D * 1.5);
  if (d.item === "Eviolite") D = Math.floor(D * 1.5);
  // Helping Hand boosts the move's base power, so it enters before the base-damage floor.
  const power = f.doubles && f.helpingHand ? Math.floor(move.power * 1.5) : move.power;
  const base = Math.floor(Math.floor(Math.floor((2 * level) / 5 + 2) * power * A / D) / 50) + 2;
  const te = typingEff(move.type, def.types);
  const stab = atk.types.includes(move.type) ? (a.abil === "Adaptability" ? 2 : 1.5) : 1;
  let mod = 1;
  if (f.doubles && f.spread) mod *= 0.75;
  if (f.weather === "Rain") mod *= move.type === "water" ? 1.5 : move.type === "fire" ? 0.5 : 1;
  if (f.weather === "Sun") mod *= move.type === "fire" ? 1.5 : move.type === "water" ? 0.5 : 1;
  if (f.terrain === "Electric" && move.type === "electric") mod *= 1.3;
  if (f.terrain === "Grassy" && move.type === "grass") mod *= 1.3;
  if (f.terrain === "Psychic" && move.type === "psychic") mod *= 1.3;
  if (f.crit) mod *= 1.5;
  if (f.burn && phys && a.abil !== "Guts") mod *= 0.5;
  if (!f.crit) { if (phys && f.reflect) mod *= f.doubles ? 0.667 : 0.5; if (!phys && f.lightscreen) mod *= f.doubles ? 0.667 : 0.5; }
  if (f.doubles && f.friendGuard) mod *= 0.75;
  if (a.item === "Life Orb") mod *= 1.3;
  if (a.item === "Muscle Band" && phys) mod *= 1.1;
  if (a.item === "Wise Glasses" && !phys) mod *= 1.1;
  if (a.item === "Expert Belt" && te > 1) mod *= 1.2;
  if (TYPE_BOOST[a.item] === move.type) mod *= 1.2;
  if (RESIST_BERRY[d.item] === move.type && te > 1) mod *= 0.5;
  if (a.abil === "Technician" && move.power <= 60) mod *= 1.5;
  if (a.abil === "Tinted Lens" && te < 1) mod *= 2;
  if (d.abil === "Thick Fat" && (move.type === "fire" || move.type === "ice")) mod *= 0.5;
  if (d.abil === "Multiscale" && d.hp >= 100) mod *= 0.5;
  if ((d.abil === "Solid Rock" || d.abil === "Filter") && te > 1) mod *= 0.75;
  const total = base * stab * te * mod;
  const maxDmg = Math.floor(total), minDmg = Math.floor(total * 0.85);
  return { minPct: HP ? minDmg / HP * 100 : 0, maxPct: HP ? maxDmg / HP * 100 : 0, ko: te === 0 || minDmg <= 0 ? 0 : Math.ceil((HP * d.hp) / 100 / minDmg), te, stab, A, D, base, mod: stab * te * mod };
}
