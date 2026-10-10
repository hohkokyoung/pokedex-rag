/* Reference cases for the damage maths: runs lib/damageCalc's calcHit and lib/calcTurn's
   playTurn over hand-picked and seeded-random inputs and writes the results for the
   backend's ports to match.

     node --import ./scripts/ts-resolve.mjs scripts/damage-fixtures.ts
     (or: make damage-fixtures)

   Regenerate whenever lib/damageCalc.ts or lib/calcTurn.ts changes. Output is deterministic. */

import { writeFileSync } from "node:fs";
import { NAT, calcHit, type CalcMonLite, type CalcMoveIn, type CalcSide, type DcField, type EVs } from "../lib/damageCalc";
import { playTurn, type TurnField, type TurnMove } from "../lib/calcTurn";

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

// ---- whole turns (lib/calcTurn): order, targeting, HP carried over, Focus Sash ----
// A move's PokéAPI target and priority, on top of MOVE's maths.
const TMOVE: Record<string, TurnMove> = {
  ...Object.fromEntries(Object.entries(MOVE).map(([n, m]) => [n, { ...m, target: "selected-pokemon", priority: 0 }])),
  Earthquake: { ...MOVE.Earthquake, target: "all-other-pokemon", priority: 0 },
  "Rock Slide": { ...MOVE["Rock Slide"], target: "all-opponents", priority: 0 },
  "Heat Wave": { ...MOVE["Heat Wave"], target: "all-opponents", priority: 0 },
  "Bullet Punch": { ...MOVE["Bullet Punch"], target: "selected-pokemon", priority: 1 },
  "Mach Punch": { ...MOVE["Mach Punch"], target: "selected-pokemon", priority: 1 },
  Outrage: { type: "dragon", damage_class: "physical", power: 120, target: "random-opponent", priority: 0 },
  "Helping Hand": { type: "normal", damage_class: "status", power: 0, target: "ally", priority: 5 },
  Protect: { type: "normal", damage_class: "status", power: 0, target: "user", priority: 4 },
};
const TF: TurnField = { level: 100, doubles: false, weather: "None", terrain: "None", reflect: false, lightscreen: false, crit: false, burn: false, friendGuard: false };
type TS = { mon: string; move?: string; set?: Partial<CalcSide> } | null;
type TurnCase = { id: string; field: TurnField; slots: TS[]; aims: number[] };
const turns: TurnCase[] = [];
const turn = (id: string, slots: TS[], f: Partial<TurnField> = {}, aims = [2, 3, 0, 1]) =>
  turns.push({ id, field: { ...TF, ...f }, slots, aims });
const S = (mon: string, move?: string, set: Partial<CalcSide> = {}): TS => ({ mon, move, set });

turn("singles-faster-first", [S("Weavile", "Ice Beam"), null, S("Garchomp", "Earthquake"), null]);
turn("singles-ko-skips", [S("Weavile", "Ice Beam", { nat: "Modest", ev: { ...ZERO, spa: 252 } }), null, S("Garchomp", "Earthquake", { hp: 20 }), null]);
turn("singles-priority", [S("Scizor", "Bullet Punch"), null, S("Weavile", "Knock Off"), null]);
turn("singles-speed-tie", [S("Garchomp", "Dragon Claw"), null, S("Garchomp", "Dragon Claw"), null]);
turn("singles-sash", [S("Garchomp", "Dragon Claw", { item: "Choice Band", nat: "Adamant", ev: { ...ZERO, atk: 252 } }), null, S("Salamence", "Dragon Claw", { item: "Focus Sash" }), null]);
turn("singles-sash-not-full", [S("Garchomp", "Dragon Claw", { item: "Choice Band" }), null, S("Salamence", "Dragon Claw", { item: "Focus Sash", hp: 90 }), null]);
turn("singles-immune", [S("Garchomp", "Earthquake"), null, S("Salamence", "Brave Bird"), null]);
turn("singles-status-move", [S("Garchomp", "Protect"), null, S("Heatran", "Flamethrower"), null]);
turn("singles-no-move", [S("Garchomp"), null, S("Heatran", "Flamethrower"), null]);
turn("singles-empty-foe", [S("Garchomp", "Earthquake"), null, null, null]);
turn("singles-spread-is-single", [S("Garchomp", "Earthquake"), null, S("Heatran", "Flamethrower"), null]);
turn("singles-screens-burn", [S("Garchomp", "Earthquake"), null, S("Heatran", "Flamethrower"), null], { reflect: true, lightscreen: true, burn: true });
turn("singles-lv50-weather", [S("Azumarill", "Hydro Pump"), null, S("Heatran", "Flamethrower"), null], { level: 50, weather: "Rain" });
turn("doubles-spread-hits-partner", [S("Garchomp", "Earthquake"), S("Heatran", "Flamethrower"), S("Toxapex", "Sludge Bomb"), S("Rotom", "Thunderbolt")], { doubles: true });
turn("doubles-all-opponents", [S("Tyranitar", "Rock Slide"), S("Clefable", "Moonblast"), S("Volcarona", "Bug Buzz"), S("Dragonite", "Dragon Claw")], { doubles: true });
turn("doubles-helping-hand", [S("Garchomp", "Dragon Claw"), S("Clefable", "Helping Hand"), S("Salamence", "Dragon Claw"), S("Ferrothorn", "Leaf Blade")], { doubles: true });
turn("doubles-helping-hand-spread", [S("Heatran", "Heat Wave"), S("Clefable", "Helping Hand"), S("Ferrothorn", "Leaf Blade"), S("Scizor", "Bullet Punch")], { doubles: true });
turn("doubles-aim-second", [S("Weavile", "Ice Beam"), S("Pikachu", "Thunderbolt"), S("Garchomp", "Earthquake"), S("Salamence", "Dragon Claw")], { doubles: true }, [3, 2, 0, 1]);
turn("doubles-aim-empty", [S("Weavile", "Ice Beam"), null, S("Garchomp", "Dragon Claw"), null], { doubles: true }, [3, 3, 0, 0]);
turn("doubles-retarget-fainted", [S("Weavile", "Ice Beam", { nat: "Modest", ev: { ...ZERO, spa: 252 } }), S("Breloom", "Close Combat"), S("Garchomp", "Earthquake", { hp: 15 }), S("Tyranitar", "Stone Edge")], { doubles: true }, [2, 2, 0, 1]);
turn("doubles-random-foe", [S("Garchomp", "Outrage"), S("Gengar", "Shadow Ball"), S("Clefable", "Moonblast"), S("Heatran", "Flamethrower")], { doubles: true });
turn("doubles-friend-guard-screens", [S("Garchomp", "Earthquake"), S("Heatran", "Heat Wave"), S("Scizor", "Bullet Punch"), S("Clefable", "Moonblast")], { doubles: true, friendGuard: true, reflect: true, lightscreen: true });
turn("doubles-sash-spread", [S("Garchomp", "Earthquake", { item: "Choice Band" }), S("Salamence", "Rock Slide"), S("Pikachu", "Thunderbolt", { item: "Focus Sash" }), S("Heatran", "Flamethrower", { item: "Focus Sash" })], { doubles: true });
turn("doubles-priority-ko", [S("Scizor", "Bullet Punch", { item: "Choice Band", nat: "Adamant", ev: { ...ZERO, atk: 252 } }), S("Breloom", "Mach Punch"), S("Clefable", "Moonblast", { hp: 10 }), S("Weavile", "Ice Beam", { hp: 5 })], { doubles: true });
turn("doubles-their-side-empty-mate", [S("Garchomp", "Earthquake"), S("Pikachu", "Thunderbolt"), S("Heatran", "Flamethrower"), null], { doubles: true });

let tseed = 20261010;
const trnd = () => ((tseed = (tseed * 1103515245 + 12345) % 2147483648) / 2147483648);
const tpick = <T,>(xs: T[]) => xs[Math.floor(trnd() * xs.length)];
const tev = (): EVs => {
  const out = { ...ZERO };
  for (const k of Object.keys(out) as (keyof EVs)[]) out[k] = trnd() < 0.5 ? 0 : Math.floor(trnd() * 64) * 4;
  return out;
};
const tmoves = Object.keys(TMOVE);
for (let i = 0; i < 40; i++) {
  const doubles = trnd() < 0.5;
  const slot = (attacker: boolean): TS => (trnd() < 0.12 ? null : S(tpick(mons), trnd() < 0.08 ? undefined : tpick(tmoves), {
    nat: tpick(natures), ev: tev(), item: tpick(ITEMS), abil: tpick(attacker ? ATK_ABIL : DEF_ABIL),
    hp: trnd() < 0.7 ? 100 : 1 + Math.floor(trnd() * 100),
  }));
  turn(`random-turn-${i}`, [slot(true), slot(true), slot(false), slot(false)], {
    level: trnd() < 0.5 ? 100 : 50, doubles, weather: tpick(WEATHER), terrain: tpick(TERRAIN),
    reflect: trnd() < 0.15, lightscreen: trnd() < 0.15, crit: trnd() < 0.1, burn: trnd() < 0.15, friendGuard: doubles && trnd() < 0.2,
  }, [2 + Math.floor(trnd() * 2), 2 + Math.floor(trnd() * 2), Math.floor(trnd() * 2), Math.floor(trnd() * 2)]);
}

const turnOut = turns.map((c) => {
  const slots = c.slots.map((s) => (s ? { mon: MON[s.mon], set: side(s.set), move: s.move ? TMOVE[s.move] : null } : { mon: null, set: side(), move: null }));
  const t = playTurn({ field: c.field, slots, aims: c.aims });
  return {
    id: c.id, field: c.field, aims: c.aims,
    slots: c.slots.map((s, i) => (s ? { name: s.mon, mon: MON[s.mon], set: slots[i].set, move_name: s.move ?? null, move: slots[i].move } : null)),
    result: { order: t.order, steps: t.steps, hp: t.hp, aim: [0, 1, 2, 3].map((i) => (t.active.includes(i) ? t.aimOf(i) : null)) },
  };
});
const TURNS = new URL("../../backend/tests/fixtures/turn_cases.json", import.meta.url);
writeFileSync(TURNS, JSON.stringify({ version: VERSION, generator: "frontend/scripts/damage-fixtures.ts", cases: turnOut }, null, 1) + "\n");
console.log(`wrote ${turnOut.length} turns → ${TURNS.pathname}`);
