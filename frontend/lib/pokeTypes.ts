/** Type metadata: colors + helpers for the type-driven accent system. */

export const TYPE_ORDER = [
  "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
  "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
  "steel", "fairy",
] as const;

export type PokeType = (typeof TYPE_ORDER)[number];

/** oklch base color per type (kept in sync with the CSS variables). */
export const TYPE_COLOR: Record<string, string> = {
  normal: "oklch(0.72 0.03 100)",
  fire: "oklch(0.7 0.19 45)",
  water: "oklch(0.66 0.15 250)",
  electric: "oklch(0.85 0.16 100)",
  grass: "oklch(0.75 0.17 145)",
  ice: "oklch(0.83 0.09 200)",
  fighting: "oklch(0.58 0.18 20)",
  poison: "oklch(0.6 0.18 320)",
  ground: "oklch(0.7 0.11 70)",
  flying: "oklch(0.75 0.09 265)",
  psychic: "oklch(0.7 0.18 5)",
  bug: "oklch(0.77 0.17 130)",
  rock: "oklch(0.68 0.06 90)",
  ghost: "oklch(0.55 0.13 300)",
  dragon: "oklch(0.6 0.19 275)",
  dark: "oklch(0.5 0.04 300)",
  steel: "oklch(0.72 0.05 230)",
  fairy: "oklch(0.8 0.11 340)",
};

/** Solid hex per type — the home page's tag / type-picker palette. */
export const TYPE_HEX: Record<string, string> = {
  normal: "#a8a878", fire: "#f0803c", water: "#5aa0e6", electric: "#f4cf46", grass: "#6fc25a",
  ice: "#8fd4d4", fighting: "#d13b52", poison: "#b25ec4", ground: "#e0c068", flying: "#8aa0e6",
  psychic: "#f0619a", bug: "#9fc02f", rock: "#b8a038", ghost: "#7a5aa0", dragon: "#7a5cf0",
  dark: "#5a5366", steel: "#a8b0c0", fairy: "#f0a6d0",
};

export function typeHex(type: string | undefined): string {
  return (type && TYPE_HEX[type]) || "#a8b0c0";
}

export function typeColor(type: string | undefined): string {
  return (type && TYPE_COLOR[type]) || "oklch(0.7 0.02 265)";
}

/** Primary color for a Pokémon = its first type. */
export function primaryColor(types: string[]): string {
  return typeColor(types[0]);
}

export function titleCase(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Zero-padded dex number, e.g. 25 -> "025". */
export function dexLabel(n: number): string {
  return `#${String(n).padStart(4, "0")}`;
}

export const STAT_LABELS: { key: keyof PokeStats; label: string; short: string }[] = [
  { key: "hp", label: "HP", short: "HP" },
  { key: "attack", label: "Attack", short: "ATK" },
  { key: "defense", label: "Defense", short: "DEF" },
  { key: "sp_attack", label: "Sp. Atk", short: "SPA" },
  { key: "sp_defense", label: "Sp. Def", short: "SPD" },
  { key: "speed", label: "Speed", short: "SPE" },
];

type PokeStats = {
  hp: number;
  attack: number;
  defense: number;
  sp_attack: number;
  sp_defense: number;
  speed: number;
};

/** Max individual base stat in the dataset (for bar scaling): Blissey HP = 255. */
export const STAT_MAX = 255;
