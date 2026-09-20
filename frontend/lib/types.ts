/** Shared API types mirroring the FastAPI Pydantic schemas. */

export type PokemonSummary = {
  id: number;
  dex_number: number;
  name: string;
  genus: string | null;
  types: string[];
  sprite_url: string;
  base_stat_total: number;
  generation_id: number | null;
  is_legendary: boolean;
  is_mythical: boolean;
  /** Set when this result is an alternate form; link to /pokedex/{dex_number}?form={form_id}. */
  form_id?: number | null;
};

export type PokemonListResponse = {
  items: PokemonSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type Ability = {
  id: number;
  identifier: string;
  name: string;
  effect: string | null;
  is_hidden: boolean;
};

export type Stats = {
  hp: number;
  attack: number;
  defense: number;
  sp_attack: number;
  sp_defense: number;
  speed: number;
  total: number;
};

export type Generation = {
  id: number;
  identifier: string;
  name: string;
};

export type EvolutionStage = {
  from_id: number | null;
  from_name: string | null;
  to_id: number;
  to_name: string;
  trigger: string | null;
  min_level: number | null;
  item: string | null;
  condition: string | null;
};

export type EvolutionMember = {
  id: number;
  name: string;
  types: string[];
  sprite_url: string;
};

export type FormAbility = {
  name: string;
  identifier: string;
  is_hidden: boolean;
  effect: string | null;
};

export type PokemonForm = {
  id: number;
  name: string;
  form_identifier: string | null;
  category: "regional" | "mega" | "primal" | "gigantamax" | "battle" | "other";
  is_mega: boolean;
  is_gigantamax: boolean;
  is_battle_only: boolean;
  types: string[];
  abilities: FormAbility[];
  stats: Stats;
  height_m: number | null;
  weight_kg: number | null;
  sprite_url: string;
  matchups: Matchups;
  flavor_texts: string[];
  evolution_members: EvolutionMember[];
  evolution_stages: EvolutionStage[];
};

export type Matchups = {
  weak_4x: string[];
  weak_2x: string[];
  resist_half: string[];
  resist_quarter: string[];
  immune: string[];
};

export type PokemonDetail = {
  id: number;
  dex_number: number;
  name: string;
  genus: string | null;
  types: string[];
  sprite_url: string;
  height_m: number | null;
  weight_kg: number | null;
  base_experience: number | null;
  capture_rate: number | null;
  base_happiness: number | null;
  color: string | null;
  shape: string | null;
  habitat: string | null;
  gender_rate: number | null;
  hatch_counter: number | null;
  growth_rate: string | null;
  egg_groups: string[];
  ev_yield: Record<string, number>;
  is_legendary: boolean;
  is_mythical: boolean;
  is_baby: boolean;
  generation: Generation | null;
  stats: Stats;
  abilities: Ability[];
  flavor_text: string | null;
  flavor_texts: string[];
  evolution_chain_id: number | null;
  evolution_stages: EvolutionStage[];
  evolution_members: EvolutionMember[];
  forms: PokemonForm[];
  matchups: Matchups;
};

export type TypeInfo = {
  id: number;
  identifier: string;
  name: string;
};
