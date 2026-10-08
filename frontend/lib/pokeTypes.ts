/** Type metadata: colors + helpers for the type-driven accent system. */

export const TYPE_ORDER = [
  "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
  "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
  "steel", "fairy",
] as const;

export type PokeType = (typeof TYPE_ORDER)[number];

/**
 * Type colours: ONE palette, three roles. Contrast-checked (WCAG AA, 4.5:1):
 *  - TYPE_HEX   fill: chips, tags, dots, bars, accents (the bright game-style palette).
 *  - TYPE_ON    text drawn ON a TYPE_HEX fill: plain white. Deliberate exception to
 *               the AA text floor on the light types (see PRODUCT.md, Accessibility);
 *               the type name always shows.
 *  - TYPE_TEXT  the type used AS text on white/light panels.
 * The CSS --type-* variables in globals.css mirror TYPE_HEX.
 */
export const TYPE_HEX: Record<string, string> = {
  normal: "#a8a878", fire: "#f0803c", water: "#5aa0e6", electric: "#f4cf46", grass: "#6fc25a",
  ice: "#8fd4d4", fighting: "#d13b52", poison: "#b25ec4", ground: "#e0c068", flying: "#8aa0e6",
  psychic: "#f0619a", bug: "#9fc02f", rock: "#b8a038", ghost: "#7a5aa0", dragon: "#7a5cf0",
  dark: "#5a5366", steel: "#a8b0c0", fairy: "#f0a6d0",
};

export const TYPE_ON: Record<string, string> = {
  normal: "#ffffff", fire: "#ffffff", water: "#ffffff", electric: "#ffffff", grass: "#ffffff",
  ice: "#ffffff", fighting: "#ffffff", poison: "#ffffff", ground: "#ffffff", flying: "#ffffff",
  psychic: "#ffffff", bug: "#ffffff", rock: "#ffffff", ghost: "#ffffff", dragon: "#ffffff",
  dark: "#ffffff", steel: "#ffffff", fairy: "#ffffff",
};

export const TYPE_TEXT: Record<string, string> = {
  normal: "#787749", fire: "#bc570c", water: "#3178bb", electric: "#8a7102", grass: "#338618",
  ice: "#397e7e", fighting: "#d13b52", poison: "#a552b7", ground: "#8f7105", flying: "#5e72b5",
  psychic: "#cb3e7a", bug: "#667d08", rock: "#887306", ghost: "#7a5aa0", dragon: "#795aee",
  dark: "#5a5366", steel: "#6d7584", fairy: "#a25f87",
};

/** Same palette as TYPE_HEX (kept as a name for existing callers). */
export const TYPE_COLOR = TYPE_HEX;

const FALLBACK = { fill: "#a8b0c0", on: "#ffffff", text: "#6d7584" };

export function typeHex(type: string | undefined): string {
  return (type && TYPE_HEX[type]) || FALLBACK.fill;
}

/** Text colour for a label sitting on the type's fill. */
export function typeOn(type: string | undefined): string {
  return (type && TYPE_ON[type]) || FALLBACK.on;
}

/** The type's colour when used for words on a light panel. */
export function typeText(type: string | undefined): string {
  return (type && TYPE_TEXT[type]) || FALLBACK.text;
}

/** Inline style for a filled type chip/tag: fill + white label. */
export function typeChip(type: string | undefined): { background: string; color: string } {
  return { background: typeHex(type), color: typeOn(type) };
}

/**
 * CSS custom properties for a type-driven element: the fill under `name`
 * (default --tc), plus --on (label on the fill) and --tx (type as text).
 */
export function typeVars(type: string | undefined, name = "--tc"): Record<string, string> {
  return { [name]: typeHex(type), "--on": typeOn(type), "--tx": typeText(type) };
}

export function typeColor(type: string | undefined): string {
  return typeHex(type);
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
