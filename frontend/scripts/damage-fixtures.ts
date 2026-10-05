/* Reference cases for the damage maths: runs lib/damageCalc's calcHit over hand-picked
   and seeded-random inputs and writes the results for the backend's port to match.

     node --import ./scripts/ts-resolve.mjs scripts/damage-fixtures.ts
     (or: make damage-fixtures)

   Regenerate whenever lib/damageCalc.ts changes. Output is deterministic. */

import { writeFileSync } from "node:fs";
import { NAT, calcHit, type CalcMonLite, type CalcMoveIn, type CalcSide, type DcField, type EVs } from "../lib/damageCalc";

const VERSION = 1;
const OUT = new URL("../../backend/tests/fixtures/damage_cases.json", import.meta.url);

const MON: Record<string, CalcMonLite> = {
  Garchomp: { types: ["dragon", "ground"], stats: { hp: 108, attack: 130, defense: 95, sp_attack: 80, sp_defense: 85, speed: 102 } },
  Salamence: { types: ["dragon", "flying"], stats: { hp: 95, attack: 135, defense: 80, sp_attack: 110, sp_defense: 80, speed: 100 } },
  Corviknight: { types: ["flying", "steel"], stats: { hp: 98, attack: 87, defense: 105, sp_attack: 53, sp_defense: 85, speed: 67 } },
  Gengar: { types: ["ghost", "poison"], stats: { hp: 60, attack: 65, defense: 60, sp_attack: 130, sp_defense: 75, speed: 110 } },
  Blissey: { types: ["normal"], stats: { hp: 255, attack: 10, defense: 10, sp_attack: 75, sp_defense: 135, speed: 55 } },
  Ferrothorn: { types: ["grass", "steel"], stats: { hp: 74, attack: 94, defense: 131, sp_attack: 54, sp_defense: 116, speed: 20 } },
  Azumarill: { types: ["water", "fairy"], stats: { hp: 100, attack: 50, defense: 80, sp_attack: 60, sp_defense: 80, speed: 50 } },
  Scizor: { types: ["bug", "steel"], stats: { hp: 70, attack: 130, defense: 100, sp_attack: 55, sp_defense: 80, speed: 65 } },
  Dragonite: { types: ["dragon", "flying"], stats: { hp: 91, attack: 134, defense: 95, sp_attack: 100, sp_defense: 100, speed: 80 } },
  Toxapex: { types: ["poison", "water"], stats: { hp: 50, attack: 63, defense: 152, sp_attack: 53, sp_defense: 142, speed: 35 } },
  Heatran: { types: ["fire", "steel"], stats: { hp: 91, attack: 90, defense: 106, sp_attack: 130, sp_defense: 106, speed: 77 } },
  Tyranitar: { types: ["rock", "dark"], stats: { hp: 100, attack: 134, defense: 110, sp_attack: 95, sp_defense: 100, speed: 61 } },
  Clefable: { types: ["fairy"], stats: { hp: 95, attack: 70, defense: 73, sp_attack: 95, sp_defense: 90, speed: 60 } },
  Weavile: { types: ["dark", "ice"], stats: { hp: 70, attack: 120, defense: 65, sp_attack: 45, sp_defense: 85, speed: 125 } },
  Volcarona: { types: ["bug", "fire"], stats: { hp: 85, attack: 60, defense: 65, sp_attack: 135, sp_defense: 105, speed: 100 } },
  Chansey: { types: ["normal"], stats: { hp: 250, attack: 5, defense: 5, sp_attack: 35, sp_defense: 105, speed: 50 } },
  Breloom: { types: ["grass", "fighting"], stats: { hp: 60, attack: 130, defense: 80, sp_attack: 60, sp_defense: 60, speed: 70 } },
  Pikachu: { types: ["electric"], stats: { hp: 35, attack: 55, defense: 40, sp_attack: 50, sp_defense: 50, speed: 90 } },
  Marill: { types: ["water", "fairy"], stats: { hp: 70, attack: 20, defense: 50, sp_attack: 20, sp_defense: 50, speed: 40 } },
  Rotom: { types: ["electric", "water"], stats: { hp: 50, attack: 65, defense: 107, sp_attack: 105, sp_defense: 107, speed: 86 } },
};

const MOVE: Record<string, CalcMoveIn> = {
  Earthquake: { type: "ground", damage_class: "physical", power: 100 },
  "Close Combat": { type: "fighting", damage_class: "physical", power: 120 },
  Flamethrower: { type: "fire", damage_class: "special", power: 90 },
  "Hydro Pump": { type: "water", damage_class: "special", power: 110 },
  Thunderbolt: { type: "electric", damage_class: "special", power: 90 },
  "Ice Beam": { type: "ice", damage_class: "special", power: 90 },
  "Dragon Claw": { type: "dragon", damage_class: "physical", power: 80 },
  "Shadow Ball": { type: "ghost", damage_class: "special", power: 80 },
  "Bullet Punch": { type: "steel", damage_class: "physical", power: 40 },
  "Mach Punch": { type: "fighting", damage_class: "physical", power: 40 },
  Moonblast: { type: "fairy", damage_class: "special", power: 95 },
  "Knock Off": { type: "dark", damage_class: "physical", power: 65 },
  "Stone Edge": { type: "rock", damage_class: "physical", power: 100 },
  Psychic: { type: "psychic", damage_class: "special", power: 90 },
  "Leaf Blade": { type: "grass", damage_class: "physical", power: 90 },
  "Brave Bird": { type: "flying", damage_class: "physical", power: 120 },
  "Sludge Bomb": { type: "poison", damage_class: "special", power: 90 },
  "Bug Buzz": { type: "bug", damage_class: "special", power: 90 },
  "Body Slam": { type: "normal", damage_class: "physical", power: 85 },
  "Heat Wave": { type: "fire", damage_class: "special", power: 95 },
  "Rock Slide": { type: "rock", damage_class: "physical", power: 75 },
};

const ITEMS = [
  "None", "Choice Band", "Choice Specs", "Life Orb", "Expert Belt", "Muscle Band", "Wise Glasses",
  "Charcoal", "Mystic Water", "Dragon Fang", "Black Belt", "Soft Sand", "Spell Tag", "Assault Vest",
  "Eviolite", "Focus Sash", "Leftovers", "Occa Berry", "Passho Berry", "Yache Berry", "Chople Berry",
  "Shuca Berry", "Haban Berry", "Roseli Berry", "Colbur Berry",
];
const ATK_ABIL = ["None", "Adaptability", "Huge Power", "Technician", "Guts", "Tinted Lens"];
const DEF_ABIL = ["None", "Thick Fat", "Multiscale", "Solid Rock", "Filter"];
const WEATHER = ["None", "Rain", "Sun"];
const TERRAIN = ["None", "Electric", "Grassy", "Psychic"];

const ALL_IV: EVs = { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 };
const ZERO: EVs = { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 };
const FIELD: DcField = {
  level: 100, doubles: false, spread: false, weather: "None", terrain: "None", reflect: false,
  lightscreen: false, crit: false, burn: false, helpingHand: false, friendGuard: false,
};
const side = (p: Partial<CalcSide> = {}): CalcSide => ({ nat: "Hardy", ev: { ...ZERO }, iv: { ...ALL_IV }, item: "None", abil: "None", hp: 100, ...p });

type Case = { id: string; atk: string; a: CalcSide; def: string; d: CalcSide; move: string; f: DcField };
const cases: Case[] = [];
const add = (id: string, atk: string, move: string, def: string, a: Partial<CalcSide> = {}, d: Partial<CalcSide> = {}, f: Partial<DcField> = {}) =>
  cases.push({ id, atk, a: side(a), def, d: side(d), move, f: { ...FIELD, ...f } });

// ---- hand-picked: every modifier the calculator models ----
add("immune-ground-vs-flying", "Garchomp", "Earthquake", "Salamence");
add("4x-ice", "Weavile", "Ice Beam", "Garchomp");
add("stab", "Garchomp", "Earthquake", "Heatran");
add("adaptability", "Garchomp", "Earthquake", "Heatran", { abil: "Adaptability" });
add("huge-power", "Azumarill", "Close Combat", "Tyranitar", { abil: "Huge Power" });
add("technician-40", "Scizor", "Bullet Punch", "Clefable", { abil: "Technician" });
add("technician-not-90", "Scizor", "Leaf Blade", "Azumarill", { abil: "Technician" });
add("choice-band", "Garchomp", "Earthquake", "Heatran", { item: "Choice Band", nat: "Jolly", ev: { ...ZERO, atk: 252, spe: 252, hp: 4 } });
add("choice-specs", "Gengar", "Shadow Ball", "Gengar", { item: "Choice Specs", nat: "Timid" });
add("choice-band-special-noop", "Heatran", "Flamethrower", "Ferrothorn", { item: "Choice Band" });
add("life-orb", "Volcarona", "Bug Buzz", "Tyranitar", { item: "Life Orb", nat: "Modest" });
add("expert-belt-se", "Breloom", "Close Combat", "Tyranitar", { item: "Expert Belt" });
add("expert-belt-neutral", "Breloom", "Close Combat", "Garchomp", { item: "Expert Belt" });
add("muscle-band", "Garchomp", "Dragon Claw", "Salamence", { item: "Muscle Band" });
add("wise-glasses", "Gengar", "Sludge Bomb", "Clefable", { item: "Wise Glasses" });
add("type-boost", "Heatran", "Flamethrower", "Scizor", { item: "Charcoal" });
add("type-boost-other-type", "Heatran", "Flamethrower", "Scizor", { item: "Mystic Water" });
add("assault-vest", "Gengar", "Shadow Ball", "Gengar", {}, { item: "Assault Vest" });
add("assault-vest-physical-noop", "Garchomp", "Earthquake", "Heatran", {}, { item: "Assault Vest" });
add("eviolite", "Garchomp", "Earthquake", "Chansey", {}, { item: "Eviolite", ev: { ...ZERO, hp: 252, def: 252 }, nat: "Bold" });
add("resist-berry", "Heatran", "Flamethrower", "Ferrothorn", {}, { item: "Occa Berry" });
add("resist-berry-neutral", "Heatran", "Flamethrower", "Blissey", {}, { item: "Occa Berry" });
add("thick-fat", "Weavile", "Ice Beam", "Garchomp", {}, { abil: "Thick Fat" });
add("multiscale-full", "Weavile", "Ice Beam", "Dragonite", {}, { abil: "Multiscale" });
add("multiscale-hurt", "Weavile", "Ice Beam", "Dragonite", {}, { abil: "Multiscale", hp: 90 });
add("solid-rock", "Weavile", "Ice Beam", "Garchomp", {}, { abil: "Solid Rock" });
add("filter-neutral", "Weavile", "Knock Off", "Garchomp", {}, { abil: "Filter" });
add("tinted-lens", "Volcarona", "Bug Buzz", "Heatran", { abil: "Tinted Lens" });
add("rain", "Azumarill", "Hydro Pump", "Heatran", {}, {}, { weather: "Rain" });
add("rain-fire", "Heatran", "Flamethrower", "Ferrothorn", {}, {}, { weather: "Rain" });
add("sun", "Heatran", "Flamethrower", "Ferrothorn", {}, {}, { weather: "Sun" });
add("sun-water", "Azumarill", "Hydro Pump", "Heatran", {}, {}, { weather: "Sun" });
add("electric-terrain", "Pikachu", "Thunderbolt", "Azumarill", {}, {}, { terrain: "Electric" });
add("grassy-terrain", "Breloom", "Leaf Blade", "Azumarill", {}, {}, { terrain: "Grassy" });
add("psychic-terrain", "Gengar", "Psychic", "Breloom", {}, {}, { terrain: "Psychic" });
add("reflect-singles", "Garchomp", "Earthquake", "Heatran", {}, {}, { reflect: true });
add("reflect-doubles", "Garchomp", "Earthquake", "Heatran", {}, {}, { reflect: true, doubles: true });
add("lightscreen", "Gengar", "Shadow Ball", "Gengar", {}, {}, { lightscreen: true });
add("crit-ignores-reflect", "Garchomp", "Earthquake", "Heatran", {}, {}, { reflect: true, crit: true });
add("burn", "Garchomp", "Earthquake", "Heatran", {}, {}, { burn: true });
add("burn-guts", "Breloom", "Close Combat", "Tyranitar", { abil: "Guts" }, {}, { burn: true });
add("spread", "Heatran", "Heat Wave", "Ferrothorn", {}, {}, { doubles: true, spread: true });
add("helping-hand", "Garchomp", "Rock Slide", "Salamence", {}, {}, { doubles: true, spread: true, helpingHand: true });
add("friend-guard", "Garchomp", "Earthquake", "Heatran", {}, {}, { doubles: true, friendGuard: true });
add("lv50", "Garchomp", "Earthquake", "Heatran", {}, {}, { level: 50 });
add("low-hp-ko", "Garchomp", "Dragon Claw", "Salamence", {}, { hp: 30 });
add("ivs-zero", "Garchomp", "Dragon Claw", "Salamence", { iv: { ...ALL_IV, atk: 0 } }, { iv: { ...ALL_IV, def: 0, hp: 0 } });
add("weak-ev-nature", "Chansey", "Body Slam", "Toxapex", { nat: "Modest" });

// ---- seeded random combinations (deterministic LCG) ----
let seed = 20261006;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = <T,>(xs: T[]) => xs[Math.floor(rnd() * xs.length)];
const ev = (): EVs => {
  const out = { ...ZERO };
  for (const k of Object.keys(out) as (keyof EVs)[]) out[k] = rnd() < 0.5 ? 0 : Math.floor(rnd() * 64) * 4;
  return out;
};
const iv = (): EVs => (rnd() < 0.8 ? { ...ALL_IV } : { hp: Math.floor(rnd() * 32), atk: Math.floor(rnd() * 32), def: Math.floor(rnd() * 32), spa: Math.floor(rnd() * 32), spd: Math.floor(rnd() * 32), spe: Math.floor(rnd() * 32) });
const mons = Object.keys(MON), moves = Object.keys(MOVE), natures = NAT.map((n) => n[0]);
for (let i = 0; i < 210; i++) {
  const doubles = rnd() < 0.3;
  add(`random-${i}`, pick(mons), pick(moves), pick(mons),
    { nat: pick(natures), ev: ev(), iv: iv(), item: pick(ITEMS), abil: pick(ATK_ABIL), hp: 100 },
    { nat: pick(natures), ev: ev(), iv: iv(), item: pick(ITEMS), abil: pick(DEF_ABIL), hp: rnd() < 0.7 ? 100 : 1 + Math.floor(rnd() * 100) },
    {
      level: rnd() < 0.5 ? 100 : 50, doubles, spread: doubles && rnd() < 0.5, weather: pick(WEATHER), terrain: pick(TERRAIN),
      reflect: rnd() < 0.15, lightscreen: rnd() < 0.15, crit: rnd() < 0.15, burn: rnd() < 0.15,
      helpingHand: doubles && rnd() < 0.3, friendGuard: doubles && rnd() < 0.2,
    });
}

const out = cases.map((c) => ({
  ...c,
  atk_mon: MON[c.atk], def_mon: MON[c.def], move_in: MOVE[c.move],
  result: calcHit(MON[c.atk], c.a, MON[c.def], c.d, MOVE[c.move], c.f),
}));
writeFileSync(OUT, JSON.stringify({ version: VERSION, generator: "frontend/scripts/damage-fixtures.ts", cases: out }, null, 1) + "\n");
console.log(`wrote ${out.length} cases → ${OUT.pathname}`);
