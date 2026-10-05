import type { EvolutionStage } from "./types";
import { titleCase } from "./pokeTypes";

/**
 * Turns an EvolutionStage's raw fields (trigger / min_level / item / condition)
 * into a small display model: a set of chips (one primary "solid" chip plus any
 * "soft" qualifier chips joined by "+") and an optional plain-English description
 * shown behind a "?". The rule: say each mechanic ONCE — the exact number
 * (happiness ≥ 160, affection ≥ 2, a set level) lives in the description, never
 * doubled on a chip. A pure level-up shows just the number.
 */

export type EvoChip = { label: string; tone: "solid" | "soft" };
export type EvoCondition = { chips: EvoChip[]; description: string | null };

type Parsed = {
  happiness: number | null;
  affection: number | null;
  beauty: number | null;
  time: string | null;
  held: string | null;
  location: string | null;
  move: string | null;
  party: string | null;
  gender: string | null;
  rain: boolean;
  other: string[];
};

function parseCondition(cond: string | null): Parsed {
  const p: Parsed = {
    happiness: null, affection: null, beauty: null, time: null, held: null,
    location: null, move: null, party: null, gender: null, rain: false, other: [],
  };
  for (const raw of (cond ?? "").split(",")) {
    const t = raw.trim();
    if (!t) continue;
    let m: RegExpMatchArray | null;
    if ((m = t.match(/happiness\s*≥\s*(\d+)/i))) p.happiness = Number(m[1]);
    else if ((m = t.match(/affection\s*≥\s*(\d+)/i))) p.affection = Number(m[1]);
    else if ((m = t.match(/beauty\s*≥\s*(\d+)/i))) p.beauty = Number(m[1]);
    else if ((m = t.match(/^(day|night|dusk)\s*time$/i))) p.time = m[1].toLowerCase();
    else if ((m = t.match(/^holding\s+(.+)$/i))) p.held = m[1];
    else if ((m = t.match(/^near\s+(.+)$/i))) p.location = m[1];
    else if ((m = t.match(/^knowing\s+(?:a\s+)?(.+?)(?:-type)?(?:\s+move)?$/i))) p.move = m[1];
    else if ((m = t.match(/^with\s+(.+?)\s+in party$/i))) p.party = m[1];
    else if ((m = t.match(/^\((male|female)\)$/i))) p.gender = m[1].toLowerCase();
    else if (/rain/i.test(t)) p.rain = true;
    else p.other.push(t);
  }
  return p;
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const aOrAn = (s: string) => (/^[aeiou]/i.test(s) ? "an" : "a");
const humanize = (s: string) => cap(s.replace(/-/g, " "));

export function buildCondition(stage: EvolutionStage): EvoCondition {
  const p = parseCondition(stage.condition);
  const trigger = (stage.trigger ?? "").toLowerCase();
  const chips: EvoChip[] = [];
  const desc: string[] = [];

  // ---- primary chip ----
  if (stage.item) {
    const item = titleCase(stage.item);
    chips.push({ label: item, tone: "solid" });
    desc.push(`Use ${aOrAn(item)} ${item}.`);
  } else if (trigger === "trade") {
    chips.push({ label: "Trade", tone: "solid" });
    desc.push("Trade this Pokémon — or, since Gen VIII (Pokémon Legends: Arceus), use a Linking Cord to evolve it without trading.");
  } else if (p.happiness != null) {
    chips.push({ label: "Friendship", tone: "solid" });
    desc.push(`Level up with high friendship (happiness ≥ ${p.happiness}) — a bond raised by travelling and battling together.`);
  } else if (p.affection != null) {
    chips.push({ label: "Affection", tone: "solid" });
    desc.push(`Level up with high affection (≥ ${p.affection} heart${p.affection > 1 ? "s" : ""}) from Pokémon Camp care.`);
  } else if (p.beauty != null) {
    chips.push({ label: "Beauty", tone: "solid" });
    desc.push(`Level up with high beauty (≥ ${p.beauty}).`);
  } else if (trigger === "level-up" && stage.min_level != null) {
    chips.push({ label: `Lv. ${stage.min_level}`, tone: "solid" });
    desc.push(`Reaches level ${stage.min_level}.`);
  } else if (trigger === "level-up" || !trigger) {
    chips.push({ label: "Level up", tone: "solid" });
    desc.push("Level up.");
  } else {
    const h = humanize(trigger);
    chips.push({ label: h, tone: "solid" });
    desc.push(`${h}.`);
  }

  // ---- qualifier chips (soft, joined by +) ----
  if (p.time) { chips.push({ label: cap(p.time), tone: "soft" }); desc.push(`During the ${p.time}.`); }
  if (p.held) { chips.push({ label: p.held, tone: "soft" }); desc.push(`While holding ${aOrAn(p.held)} ${p.held}.`); }
  if (p.move) { const mv = `${cap(p.move)} move`; chips.push({ label: mv, tone: "soft" }); desc.push(`While knowing a ${cap(p.move)}-type move.`); }
  if (p.location) { chips.push({ label: p.location, tone: "soft" }); desc.push(`Near ${p.location}.`); }
  if (p.party) { chips.push({ label: p.party, tone: "soft" }); desc.push(`While ${p.party} is in your party.`); }
  if (p.gender) { chips.push({ label: cap(p.gender), tone: "soft" }); }
  if (p.rain) { chips.push({ label: "Raining", tone: "soft" }); desc.push("While it's raining."); }
  // a set level on top of another condition (rare) — show as a soft chip
  if (stage.min_level != null && trigger === "level-up" && (p.happiness != null || p.affection != null || p.beauty != null)) {
    chips.push({ label: `Lv. ${stage.min_level}`, tone: "soft" });
  }
  for (const o of p.other) chips.push({ label: titleCase(o), tone: "soft" });

  const jargon = p.happiness != null || p.affection != null || p.beauty != null;
  const hasInfo = chips.length > 1 || jargon || trigger === "trade";
  return { chips, description: hasInfo ? desc.join(" ") : null };
}
