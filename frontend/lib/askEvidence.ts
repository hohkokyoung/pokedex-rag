import type { AskSource } from "@/lib/api";

/**
 * Small helpers for the Ask console. Evidence itself arrives as typed views from the
 * backend (see ``AskView`` in lib/api.ts), so nothing here parses source text.
 */
export type StatKey = "hp" | "attack" | "defense" | "sp_attack" | "sp_defense" | "speed";

export const STAT_ORDER: StatKey[] = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"];

export const STAT_LABEL: Record<StatKey, string> = {
  hp: "HP",
  attack: "Attack",
  defense: "Defense",
  sp_attack: "Sp. Atk",
  sp_defense: "Sp. Def",
  speed: "Speed",
};

export const STAT_SHORT: Record<StatKey, string> = {
  hp: "HP",
  attack: "Atk",
  defense: "Def",
  sp_attack: "SpA",
  sp_defense: "SpD",
  speed: "Spe",
};

/** Citation numbers referenced anywhere in the answer text. */
export function citedNumbers(answer: string): Set<number> {
  const out = new Set<number>();
  for (const m of answer.matchAll(/[[【](\d+)[\]】]/g)) out.add(Number(m[1]));
  return out;
}

/**
 * Deterministic follow-ups built from what was actually cited — no LLM. Only
 * question shapes the retriever handles reliably (profile lookup, similarity).
 */
export function followUps(cited: AskSource[]): string[] {
  const names = [...new Set(cited.map((s) => s.pokemon_name).filter(Boolean))] as string[];
  if (!names.length) return [];
  const [a, b] = names;
  return [`Tell me about ${a}`, `What is similar to ${a}?`, ...(b ? [`Tell me about ${b}`] : [])];
}
