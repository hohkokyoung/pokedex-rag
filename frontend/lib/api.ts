/**
 * API client for the FastAPI backend.
 * Base URL is provided at build/run time via NEXT_PUBLIC_API_BASE_URL.
 */

import type {
  Ability,
  Generation,
  PokemonDetail,
  PokemonListResponse,
  TypeInfo,
} from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Resolve a backend-relative asset path (e.g. sprite_url) to a full URL. */
export function assetUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_BASE_URL}${path}`;
}

async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    throw new Error(`Request failed (${res.status}): ${path}`);
  }
  return (await res.json()) as T;
}

export type ListParams = {
  q?: string;
  types?: string[];
  /** Any of these generations (1–9) may match. */
  generations?: number[];
  legendary?: boolean;
  mythical?: boolean;
  sort?: string;
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

export function buildListQuery(params: ListParams): string {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  (params.types ?? []).forEach((t) => sp.append("type", t));
  (params.generations ?? []).forEach((g) => sp.append("generation", String(g)));
  if (params.legendary) sp.set("legendary", "true");
  if (params.mythical) sp.set("mythical", "true");
  if (params.sort) sp.set("sort", params.sort);
  if (params.order) sp.set("order", params.order);
  sp.set("limit", String(params.limit ?? 40));
  sp.set("offset", String(params.offset ?? 0));
  return sp.toString();
}

export function listPokemon(
  params: ListParams,
  init?: RequestInit,
): Promise<PokemonListResponse> {
  return getJSON<PokemonListResponse>(`/api/pokemon?${buildListQuery(params)}`, init);
}

export function getPokemon(idOrName: string | number): Promise<PokemonDetail> {
  return getJSON<PokemonDetail>(`/api/pokemon/${idOrName}`);
}

export function listTypes(): Promise<TypeInfo[]> {
  return getJSON<TypeInfo[]>("/api/types");
}

export function listGenerations(): Promise<Generation[]> {
  return getJSON<Generation[]>("/api/generations");
}

export type AskSource = {
  n: number;
  pokemon_id: number | null;
  pokemon_name: string | null;
  dex_number: number | null;
  chunk_type: string;
  source_ref: string | null;
  snippet: string;
  score: number;
  /** The plan step that retrieved it, and its index in that step's evidence. */
  step?: string | null;
  step_index?: number | null;
};

/* ── Retrieval plan + typed result views (mirror backend app/agent/views.py) ── */

export type Planner = "llm" | "keyword";
export type StepState = "pending" | "running" | "done" | "empty" | "error";

export type PlanStep = {
  id: string;
  tool: string;
  why: string;
  args: Record<string, unknown>;
  error?: string;
};

export type PlanEvent = {
  planner: Planner; cached: boolean; replan: boolean; steps: PlanStep[];
  /** Constraints the question stated that no tool could apply (the answer opens with a note). */
  unhandled?: string[];
};
export type StepEvent = { id: string; state: StepState; summary: string; ms: number };
export type Usage = { llm_calls: number; input_tokens: number; output_tokens: number };
export type DoneEvent = { usage?: Usage; fallback?: boolean };

export type PokemonCardData = {
  ref: number | null;
  pokemon_id: number | null;
  name: string;
  dex_number: number | null;
  types: string[];
  stats: Partial<Record<"hp" | "attack" | "defense" | "sp_attack" | "sp_defense" | "speed", number>>;
  total: number | null;
  entry: string | null;
  match: number | null;
  coverage: { move: string; type: string }[];
  via: string | null;
};
export type RankingRow = PokemonCardData & { value: number | null };
export type MoveRowData = {
  ref: number | null;
  move_id: number | null;
  name: string;
  type: string;
  damage_class: string | null;
  power: number | null;
  accuracy: number | null;
  pp: number | null;
  learners: number | null;
  effect: string | null;
};
export type LearnMoveData = { name: string; type: string; damage_class: string | null; power: number | null; level: number | null };

type ViewBase = { step: string; chunk_refs: number[] };
export type RankingView = ViewBase & { kind: "ranking"; stat: string; order: "asc" | "desc"; total: number; rows: RankingRow[] };
export type PokemonListView = ViewBase & { kind: "pokemon_list"; title: string | null; cards: PokemonCardData[] };
export type TypeChartView = ViewBase & {
  kind: "type_chart";
  types: string[];
  weak_4x: string[];
  weak_2x: string[];
  resist_half: string[];
  resist_quarter: string[];
  immune: string[];
  strong_against: string[];
};
export type MoveListView = ViewBase & { kind: "move_list"; moves: MoveRowData[] };
export type LearnsetView = ViewBase & {
  kind: "learnset";
  pokemon: PokemonCardData;
  game: string | null;
  groups: { ref: number | null; method: string; label: string; moves: LearnMoveData[] }[];
};
export type LearnersView = ViewBase & {
  kind: "learners";
  move: MoveRowData;
  total: number;
  by_method: Record<string, number>;
  scope: string[];
  game: string | null;
  rows: PokemonCardData[];
};
export type LearnCheckView = ViewBase & {
  kind: "learn_check";
  pokemon: PokemonCardData;
  move: MoveRowData;
  ok: boolean;
  how: string | null;
  game: string | null;
};
/* Team-coach views. */
export type BuildSet = {
  moves: string[];
  ability: string | null;
  nature: string | null;
  item: string | null;
  evs: Record<string, number>;
};
export type CandidatesView = ViewBase & {
  kind: "candidates";
  team_id: number;
  candidates: Candidate[];
  team_full: boolean;
  members: { slot: number; name: string }[];
};
export type SetEditView = ViewBase & {
  kind: "set_edit";
  side: "ours" | "theirs";
  team_id: number;
  slot: number;
  name: string;
  sprite_url: string;
  before: BuildSet;
  after: BuildSet;
  why: string;
  /** Only the changed fields, in the slot editor's apply shape. */
  fields: { moves?: string[]; ability?: string | null; nature?: string | null; item?: string | null; evs?: Record<string, number> };
  /** The member as it was (ids included), for Revert. */
  member: Team["members"][number];
};
export type MemberAddedView = ViewBase & {
  kind: "member_added";
  team_id: number;
  added: boolean;
  slot: number | null;
  card: PokemonCardData;
  message: string;
};
export type DuelView = ViewBase & { kind: "duel"; team_id: number; opponent_id: number; duel: TeamDuel };

/** A calculator slot: 0–1 are yours, 2–3 the opponent's. */
export type CalcRef = { slot: number; name: string; side: 0 | 1; dex_number: number | null };
export type HitRange = { min_pct: number; max_pct: number; ko: number; te: number; ko_text: string };
/** Fields to write into one calculator slot (Apply); never a saved team. */
export type CalcApply = {
  slot: number;
  fields: { item?: string; ability?: string; nature?: string; evs?: Record<string, number>; hp?: number };
};
export type DamageView = ViewBase & {
  kind: "damage";
  attacker: CalcRef;
  defender: CalcRef;
  move: MoveRowData;
  current: HitRange;
  whatif: HitRange | null;
  changes: { who: string; key: string; value: string }[];
  apply: CalcApply[];
};
export type SurviveView = ViewBase & {
  kind: "survive";
  defender: CalcRef;
  attacker: CalcRef;
  move: MoveRowData;
  survives: boolean;
  stat: "def" | "spd";
  hp_ev: number;
  stat_ev: number;
  nature: string;
  nature_changed: boolean;
  range: HitRange;
  current: HitRange;
  apply: CalcApply | null;
  /** The current set already survives: nothing to apply. */
  already: boolean;
};
export type BuildProposalView = ViewBase & { kind: "build_proposal"; slot: number; pokemon: string; build: BuildSuggestion };

export type AskView =
  | RankingView
  | PokemonListView
  | TypeChartView
  | MoveListView
  | LearnsetView
  | LearnersView
  | LearnCheckView
  | CandidatesView
  | SetEditView
  | MemberAddedView
  | DuelView
  | DamageView
  | SurviveView
  | BuildProposalView;

export type AskResponse = {
  answer: string;
  planner: Planner;
  cached: boolean;
  steps: (PlanStep & { state: StepState; summary: string; replan: boolean })[];
  views: AskView[];
  sources: AskSource[];
  usage: Usage;
};

export function getAskStatus(): Promise<{ enabled: boolean; provider: string }> {
  return getJSON<{ enabled: boolean; provider: string }>("/api/ask/status");
}

export type ProfileFavorite = {
  id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
};

export type Profile = {
  preferred_types: string[];
  favorites: ProfileFavorite[];
};

export function getProfile(): Promise<Profile> {
  return getJSON<Profile>("/api/profile");
}

export function updatePreferredTypes(preferred_types: string[]): Promise<Profile> {
  return getJSON<Profile>("/api/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferred_types }),
  });
}

export function addFavorite(pokemonId: number): Promise<Profile> {
  return getJSON<Profile>(`/api/profile/favorites/${pokemonId}`, { method: "POST" });
}

export function removeFavorite(pokemonId: number): Promise<Profile> {
  return getJSON<Profile>(`/api/profile/favorites/${pokemonId}`, { method: "DELETE" });
}

export type BuildSuggestion = {
  pokemon: string;
  moves: string[];
  ability: string | null;
  nature: string | null;
  item: string | null;
  evs: Record<"hp" | "atk" | "def" | "spa" | "spd" | "spe", number>;
  why: string;
};

export type CoachTurn = { ask: string; reply: string };

/** A coach-picked set for one Pokémon, every field checked against its real options.
 *  With `followUp`, the coach revises `current` per `request` (or just answers it);
 *  without `current`, `request` shapes a fresh build. */
export async function suggestBuild(
  pokemonId: number,
  formId?: number | null,
  followUp?: { current?: BuildSuggestion; request: string; history: CoachTurn[] },
): Promise<BuildSuggestion> {
  const res = await fetch(`${API_BASE_URL}/api/builds/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pokemon_id: pokemonId, form_id: formId ?? null, ...followUp }),
  });
  if (!res.ok) {
    const detail = await res.json().then((j) => j?.detail).catch(() => null);
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return (await res.json()) as BuildSuggestion;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch(`${API_BASE_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (res.status === 503) {
    throw new Error("assistant-not-configured");
  }
  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`);
  }
  return (await res.json()) as AskResponse;
}

// ---------------------------------------------------------------------------
// Team builder + coach
// ---------------------------------------------------------------------------

export type NatureInfo = {
  id: number;
  identifier: string;
  name: string;
  increased_stat: string | null;
  decreased_stat: string | null;
};

export type LearnsetMove = {
  move_id: number;
  identifier: string;
  name: string;
  type: string | null;
  damage_class: string | null;
  power: number | null;
  pp: number | null;
  accuracy: number | null;
  short_effect: string | null;
  /** Doubles targeting (PokéAPI move_targets identifier), e.g. "all-other-pokemon". */
  target?: string | null;
  /** Turn-order bracket: +1 Quick Attack, +3 Fake Out, 0 for most moves. */
  priority?: number;
  learn_method: string | null;
  level: number | null;
};

export type SlotAbility = { id: number; name: string; is_hidden: boolean };
export type SlotNature = {
  id: number;
  name: string;
  increased_stat: string | null;
  decreased_stat: string | null;
};
export type SlotItem = { id: number; name: string; category: string | null; short_effect: string | null };
export type SlotMove = {
  move_id: number;
  name: string;
  type: string | null;
  damage_class: string | null;
  power: number | null;
  accuracy?: number | null;
  priority?: number;
};

export type TeamMember = {
  slot: number;
  pokemon_id: number;
  form_id?: number | null;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  base_stats: Record<string, number>;
  final_stats: Record<string, number>;
  ability: SlotAbility | null;
  nature: SlotNature | null;
  item?: SlotItem | null;
  ev_spread: Record<string, number>;
  iv_spread: Record<string, number>;
  moves: SlotMove[];
};

export type Team = {
  id: number;
  name: string;
  kind: string;
  notes: string | null;
  members: TeamMember[];
};

export type TeamSummary = {
  id: number;
  name: string;
  kind: string;
  size: number;
  sprites: string[];
};

export type SlotPayload = {
  pokemon_id: number;
  /** Alternate form of the species (Mega, regional…); its typing/stats/abilities apply. */
  form_id?: number | null;
  ability_id?: number | null;
  item_id?: number | null;
  nature_id?: number | null;
  ev_spread?: Record<string, number> | null;
  iv_spread?: Record<string, number> | null;
  move_ids?: number[] | null;
};

export type Candidate = {
  pokemon_id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  role: string;
  base_stats: Record<string, number>;
  reason: string;
};

export type MemberDefense = {
  slot: number;
  name: string;
  types: string[];
  multipliers: Record<string, number>;
  weak_to: string[];
};
export type SharedWeakness = { type: string; count: number; members: string[] };
export type MemberRole = {
  slot: number;
  name: string;
  role: string;
  speed: number;
  offense: number;
  bulk: number;
  bst: number;
  /** Base Speed as the set plays it (Choice Scarf, Speed Boost, Dragon Dance…). */
  eff_speed?: number | null;
  speed_note?: string | null;
};
export type SlotSuggestion = {
  slot: number;
  name: string;
  recommended_ability: string | null;
  ability_reason: string | null;
  recommended_nature: string | null;
  recommended_evs: Record<string, number>;
  rationale: string;
  recommended_moves: SuggestedMove[];
};
export type SuggestedMove = {
  name: string;
  type: string | null;
  damage_class: string | null;
  power: number | null;
  is_set: boolean;
};
export type OpponentThreat = {
  opponent_name: string;
  opponent_types: string[];
  threatens: string[];
  via: string[];
};
export type PressurePoint = {
  attacker: string;
  attacker_types: string[];
  targets: string[];
  via: string[];
};
export type VsMember = {
  slot: number;
  pokemon_id: number;
  name: string;
  types: string[];
  sprite_url: string;
  speed: number;
  bst: number;
  role: string;
};
export type MatchupCell = {
  our_slot: number;
  their_slot: number;
  our_hit: number;
  our_hit_type: string | null;
  our_move: string | null;
  our_move_learned: boolean;
  our_pct: number;
  our_hko: number;
  their_hit: number;
  their_hit_type: string | null;
  their_move: string | null;
  their_move_learned: boolean;
  their_pct: number;
  their_hko: number;
  faster: "ours" | "theirs" | "tie";
  score: number;
  outcome: "win" | "lose" | "even";
  our_setup?: string | null;
  their_setup?: string | null;
  notes?: string[];
};
export type Edge = "ours" | "theirs" | "even";
export type ScoreRow = {
  key: string;
  label: string;
  ours: number;
  theirs: number;
  ours_label: string;
  theirs_label: string;
  share: number;
  weight: number;
  edge: Edge;
};
export type Verdict = { score: number; label: string; edge: Edge; reason: string };
export type VsOpponent = {
  opponent_id: number;
  opponent_name: string;
  threats: OpponentThreat[];
  advice: string[];
  our_pressure: PressurePoint[];
  our_members: VsMember[];
  their_members: VsMember[];
  cells: MatchupCell[];
  scorecard: ScoreRow[];
  verdict: Verdict | null;
};
export type TeamAnalysis = {
  team_id: number;
  name: string;
  size: number;
  defensive: { matrix: MemberDefense[]; shared_weaknesses: SharedWeakness[] };
  offensive: {
    coverage_types: string[];
    used_move_coverage: boolean;
    uncovered_types: string[];
    not_super_effective: string[];
    from_learnset: string[];
    tips: string[];
  };
  roles: { members: MemberRole[]; missing_roles: string[]; notes: string[] };
  suggestions: SlotSuggestion[];
  vs_opponent: VsOpponent | null;
  sets?: SetProfile | null;
  summary: string[];
};
/** What each member's set adds beyond species + typing (item, ability, set moves). */
export type SetMember = {
  slot: number;
  name: string;
  ability: string | null;
  ability_note: string | null;
  item: string | null;
  item_note: string | null;
  moves_set: number;
  setup: string[];
  priority: string[];
  recovery: string[];
  support: string[];
  score: number;
};
export type SetProfile = { members: SetMember[] };

const jsonInit = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
});

export function listTeams(kind?: "player" | "opponent"): Promise<{ teams: TeamSummary[] }> {
  const q = kind ? `?kind=${kind}` : "";
  return getJSON<{ teams: TeamSummary[] }>(`/api/teams${q}`);
}

export function getTeam(id: number): Promise<Team> {
  return getJSON<Team>(`/api/teams/${id}`);
}

export function createTeam(name: string, kind: "player" | "opponent"): Promise<Team> {
  return getJSON<Team>("/api/teams", jsonInit("POST", { name, kind }));
}

export function updateTeam(
  id: number,
  patch: { name?: string; kind?: string; notes?: string },
): Promise<Team> {
  return getJSON<Team>(`/api/teams/${id}`, jsonInit("PUT", patch));
}

export async function deleteTeam(id: number, opts: { keepalive?: boolean } = {}): Promise<void> {
  // keepalive lets the request finish even while the page is unloading.
  const res = await fetch(`${API_BASE_URL}/api/teams/${id}`, { method: "DELETE", keepalive: opts.keepalive });
  if (!res.ok) throw new Error(`Delete failed (${res.status})`);
}

export async function setSlot(
  id: number,
  slot: number,
  payload: SlotPayload,
): Promise<Team> {
  const res = await fetch(`${API_BASE_URL}/api/teams/${id}/slots/${slot}`, jsonInit("PUT", payload));
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as Team;
}

export function clearSlot(id: number, slot: number): Promise<Team> {
  return getJSON<Team>(`/api/teams/${id}/slots/${slot}`, { method: "DELETE" });
}

export function listNatures(): Promise<NatureInfo[]> {
  return getJSON<NatureInfo[]>("/api/natures");
}

export function getPokemonMoves(pokemonId: number, q?: string): Promise<LearnsetMove[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return getJSON<LearnsetMove[]>(`/api/pokemon/${pokemonId}/moves${query}`);
}

export function getFormMoves(formId: number, q?: string): Promise<LearnsetMove[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return getJSON<LearnsetMove[]>(`/api/pokemon/forms/${formId}/moves${query}`);
}

export type PokemonGame = { id: number; identifier: string; name: string; generation: number; moves: number };
export type GameMove = LearnsetMove & { machine: string | null };
export type PokemonGameMoves = { version_group_id: number | null; games: PokemonGame[]; moves: GameMove[] };

/** A species' or form's (id > 10000) learnset in one game; omit the game for the newest. */
export function getPokemonMovesByGame(pokemonId: number, versionGroup?: number | null): Promise<PokemonGameMoves> {
  const q = versionGroup != null ? `?version_group=${versionGroup}` : "";
  return getJSON<PokemonGameMoves>(`/api/pokemon/${pokemonId}/moves/by-game${q}`);
}

export function getPokemonAbilities(pokemonId: number): Promise<Ability[]> {
  return getJSON<Ability[]>(`/api/pokemon/${pokemonId}/abilities`);
}

export type MoveResult = {
  id: number;
  identifier: string;
  name: string;
  type: string | null;
  damage_class: string | null;
  power: number | null;
  pp: number | null;
  accuracy: number | null;
  priority: number;
  short_effect: string | null;
  /** Signature Z-Move: who can use it, holding which crystal, from which move. */
  signature_z?: SignatureZ | null;
};
export type SignatureZ = {
  crystal: string;
  base_move: string;
  users: { id: number; dex_number: number; name: string; sprite_url: string; form_id: number | null }[];
};

export function searchMoves(q: string, limit = 6): Promise<MoveResult[]> {
  return getJSON<MoveResult[]>(`/api/moves?q=${encodeURIComponent(q)}&limit=${limit}`);
}

/** Every move (~900), for the home finder's client-side filters. */
export function listAllMoves(): Promise<MoveResult[]> {
  return getJSON<MoveResult[]>(`/api/moves?limit=2000`);
}

/** A game and the ids of every move learnable in it (the finder's game filter). */
export type MoveGame = { id: number; identifier: string; name: string; generation: number; move_ids: number[] };

export function listMoveGames(): Promise<MoveGame[]> {
  return getJSON<MoveGame[]>(`/api/moves/games`);
}

export type MoveLearner = {
  id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  learn_method: string | null;
  level: number | null;
  /** Set when only an alternate form learns it (Black Kyurem's Freeze Shock). */
  form_id?: number | null;
};

export function getMoveLearners(moveId: number, limit = 120): Promise<MoveLearner[]> {
  return getJSON<MoveLearner[]>(`/api/moves/${moveId}/learners?limit=${limit}`);
}

/** `level` is the lowest level-up level; `level_max` the highest across games (any-game view). */
export type LearnMethod = { method: string; level: number | null; level_max?: number | null };
export type GameLearner = {
  id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  form_id: number | null;
  /** Forms folded into this row because they learn it the same way. */
  also: string[];
  methods: LearnMethod[];
};
export type LearnGame = { id: number; identifier: string; name: string; generation: number; learners: number };
export type MoveGameLearners = {
  move_id: number;
  /** null = every game at once (the default). */
  version_group_id: number | null;
  games: LearnGame[];
  /** Distinct species that learn it in any game. */
  total: number;
  machine: string | null;
  last_machine: string | null;
  last_machine_game: string | null;
  learners: GameLearner[];
};

/** Who learns a move in one game, or across every game when `versionGroup` is omitted, and how. */
export function getMoveLearnersByGame(moveId: number, versionGroup?: number | null): Promise<MoveGameLearners> {
  const q = versionGroup != null ? `?version_group=${versionGroup}` : "";
  return getJSON<MoveGameLearners>(`/api/moves/${moveId}/learners/by-game${q}`);
}

export function searchAbilities(q: string, limit = 6): Promise<Ability[]> {
  return getJSON<Ability[]>(`/api/abilities?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export type AbilityHolder = {
  id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  is_hidden: boolean;
};

export function getAbilityHolders(abilityId: number, limit = 250): Promise<AbilityHolder[]> {
  return getJSON<AbilityHolder[]>(`/api/abilities/${abilityId}/pokemon?limit=${limit}`);
}

export type ItemResult = {
  id: number;
  identifier: string;
  name: string;
  category: string | null;
  cost: number | null;
  short_effect: string | null;
  /** The in-game bag description. */
  flavor_text?: string | null;
  /** Fling base power (null = can't be flung). */
  fling_power?: number | null;
};

export function searchItems(q: string, limit = 8): Promise<ItemResult[]> {
  return getJSON<ItemResult[]>(`/api/items?q=${encodeURIComponent(q)}&limit=${limit}`);
}

/** Every ability / item, for the home finder's client-side filters. */
export function listAllAbilities(): Promise<Ability[]> {
  return getJSON<Ability[]>(`/api/abilities?limit=2000`);
}
export function listAllItems(): Promise<ItemResult[]> {
  return getJSON<ItemResult[]>(`/api/items?limit=5000`);
}

/** Every item a Pokémon can hold in battle (≈350), alphabetical. */
export function getHeldItems(): Promise<ItemResult[]> {
  return getJSON<ItemResult[]>(`/api/items?held=true&limit=500`);
}

export type StrategyAxis = {
  key: "offense" | "bulk" | "speed" | "setup" | "stall" | "support";
  label: string;
  score: number;
  now: number;
  potential: number;
  detail: string;
  contributors: { name: string; moves: string[]; set: boolean }[];
};
export type TeamStrategy = { team_id: number; style: string; style_reason: string; axes: StrategyAxis[] };
/** `pending` = the backend is writing a fresher (AI) summary in the background. */
export type TeamSummaryText = { team_id: number; text: string; source: "ai" | "rules"; pending?: boolean };

/** How the team wants to win — offense/bulk/speed/setup/stall/support (deterministic). */
export function getTeamStrategy(id: number): Promise<TeamStrategy> {
  return getJSON<TeamStrategy>(`/api/teams/${id}/strategy`);
}

/** Two-sentence summary: AI-written when the backend has an LLM key, else rule-based. */
export function getTeamSummary(id: number): Promise<TeamSummaryText> {
  return getJSON<TeamSummaryText>(`/api/teams/${id}/summary`);
}

/** Force a fresh summary now (stored for next time). */
export function refreshTeamSummary(id: number): Promise<TeamSummaryText> {
  return getJSON<TeamSummaryText>(`/api/teams/${id}/summary/refresh`, { method: "POST" });
}

export function getTeamAnalysis(id: number, opponentId?: number | null): Promise<TeamAnalysis> {
  const q = opponentId ? `?opponent_id=${opponentId}` : "";
  return getJSON<TeamAnalysis>(`/api/teams/${id}/analysis${q}`);
}

/** Stream a grounded coaching answer over SSE. */
export function coachAskStream(
  teamId: number,
  question: string,
  opponentId: number | null,
  handlers: StreamHandlers,
  report?: string,
): Promise<void> {
  return streamSSE(`/api/teams/${teamId}/ask`, { question, opponent_id: opponentId, report: report || null }, handlers);
}

/** The calculator as the coach sees it; stats, types and move data are re-read server-side. */
export type CalcSlotState = {
  slot: number;
  pokemon_id: number;
  form_id?: number | null;
  name?: string;
  nature: string;
  evs: Record<string, number>;
  ivs: Record<string, number>;
  item: string;
  ability: string;
  /** Current HP, % of max. */
  hp: number;
  move: string | null;
  aim: number | null;
};
export type CalcAskState = {
  level: number;
  doubles: boolean;
  field: {
    weather: string; terrain: string; reflect: boolean; lightscreen: boolean;
    crit: boolean; burn: boolean; friend_guard: boolean;
  };
  slots: CalcSlotState[];
  focus: number;
  hits: { attacker: number; target: number; move: string; min_pct: number; max_pct: number; ko: number; te: number }[];
  proposal: { slot: number; build: BuildSuggestion; thread: CoachTurn[] } | null;
};

/** Stream the calculator coach (damage, survival, builds, dex) over SSE. Nothing is saved. */
export function calcAskStream(question: string, state: CalcAskState, handlers: StreamHandlers): Promise<void> {
  return streamSSE("/api/calc/ask", { question, ...state }, handlers);
}

export type StreamHandlers = {
  /** The retrieval plan (again with ``replan: true`` for steps a re-plan adds). */
  onPlan?: (plan: PlanEvent) => void;
  /** A plan step changed state: running → done | empty | error. */
  onStep?: (step: StepEvent) => void;
  /** A typed result view from a finished step. */
  onView?: (view: AskView) => void;
  onSources?: (sources: AskSource[]) => void;
  onTeamUpdated?: (team: Team) => void;
  onDelta?: (text: string) => void;
  onDone?: (done?: DoneEvent) => void;
  onError?: (reason: string) => void;
  signal?: AbortSignal;
};

/** Stream a grounded answer over SSE. */
export function askQuestionStream(question: string, handlers: StreamHandlers): Promise<void> {
  return streamSSE("/api/ask/stream", { question }, handlers);
}

/**
 * Why a stream failed, as passed to `onError`: a transport-level reason below,
 * or the backend's own message from an `event: error`.
 *  - assistant-not-configured  503: no LLM key on the backend
 *  - request-failed            couldn't connect, non-2xx, or the reply wasn't SSE
 *  - stream-interrupted        the connection dropped or a message was malformed
 *  - stream-incomplete         the body ended without a `done` or `error` event
 */
export type StreamFailure =
  | "assistant-not-configured"
  | "request-failed"
  | "stream-interrupted"
  | "stream-incomplete";

/**
 * POST `body` to `path` and read the reply as Server-Sent Events (EventSource
 * can't POST, so the body is read by hand). Guarantees exactly one terminal
 * callback, `onDone` or `onError`, so the UI can never be left "streaming" —
 * except when the caller aborts via `signal`: a deliberate cancel is silent.
 */
async function streamSSE(path: string, body: unknown, handlers: StreamHandlers): Promise<void> {
  let settled = false;
  const finish = (fn?: () => void) => {
    if (settled) return;
    settled = true;
    fn?.();
  };
  const fail = (reason: string) => {
    if (!handlers.signal?.aborted) finish(() => handlers.onError?.(reason));
  };

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(body),
      signal: handlers.signal,
    });
  } catch {
    return fail("request-failed");
  }
  if (res.status === 503) return fail("assistant-not-configured");
  // A 200 that isn't SSE (wrong base URL, a proxy's HTML page) would otherwise
  // be read to the end without a single event.
  if (!res.ok || !res.body || !res.headers.get("content-type")?.includes("text/event-stream")) {
    res.body?.cancel().catch(() => {});
    return fail("request-failed");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (!settled) {
      const { done, value } = await reader.read();
      if (done) break; // the HTTP body ended (the final zero-length chunk)
      buffer += decoder.decode(value, { stream: true });

      let sep: number;
      while (!settled && (sep = buffer.indexOf("\n\n")) !== -1) {
        const raw = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);

        let event = "message";
        const data: string[] = [];
        for (const line of raw.split("\n")) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
        }
        if (!data.length) continue;

        const parsed = JSON.parse(data.join("\n"));
        if (event === "done") finish(() => handlers.onDone?.(parsed as DoneEvent));
        else if (event === "error") fail((parsed as { message: string }).message);
        else if (event === "plan") handlers.onPlan?.(parsed as PlanEvent);
        else if (event === "step") handlers.onStep?.(parsed as StepEvent);
        else if (event === "view") handlers.onView?.(parsed as AskView);
        else if (event === "sources") handlers.onSources?.(parsed as AskSource[]);
        else if (event === "team_updated") handlers.onTeamUpdated?.(parsed as Team);
        else if (event === "delta") handlers.onDelta?.((parsed as { text: string }).text);
      }
    }
  } catch {
    // read() rejected (network drop, or our own abort) or a message was malformed.
    return fail("stream-interrupted");
  } finally {
    reader.cancel().catch(() => {});
  }
  // The body ended but the backend never said `done` or `error` (e.g. it crashed).
  fail("stream-incomplete");
}

export type EncounterGame = { version_id: number; version: string; generation: number; places: number };
export type Encounter = {
  location: string;
  area: string | null;
  region: string | null;
  method: string;
  method_name: string;
  min_level: number;
  max_level: number;
  /** Encounter rate in percent; null where the game has no odds (raids, gifts by story). */
  chance: number | null;
  conditions: string | null;
};
export type PokemonEncounters = { version_id: number | null; games: EncounterGame[]; encounters: Encounter[] };

/** Where a species or form (id > 10000) is found in one game; omit the game for the newest. */
export function getPokemonEncounters(pokemonId: number, version?: number | null): Promise<PokemonEncounters> {
  const q = version != null ? `?version=${version}` : "";
  return getJSON<PokemonEncounters>(`/api/pokemon/${pokemonId}/encounters${q}`);
}

/** One step of a played-out one-on-one; side "a" = our member, "b" = theirs. */
export type DuelEvent = {
  turn: number;
  side: "a" | "b";
  kind: "intimidate" | "setup" | "attack" | "sash" | "recoil" | "heal" | "speed-boost" | "faint" | "nothing";
  move?: string | null;
  type?: string | null;
  mult?: number | null;
  pct?: number | null;
  hp?: number | null;
  item?: string | null;
  ability?: string | null;
  boosts?: Record<string, number> | null;
};
export type TeamDuel = {
  our_slot: number;
  their_slot: number;
  our_name: string;
  their_name: string;
  outcome: "win" | "lose" | "even";
  first: "ours" | "theirs" | "tie";
  our_setup: string | null;
  their_setup: string | null;
  our_moves: string[];
  their_moves: string[];
  our_moves_learned: string[];
  their_moves_learned: string[];
  notes: string[];
  log: DuelEvent[];
};

/** One pairing played out turn by turn with each side's set (moves, item, ability, setup). */
export function getTeamDuel(id: number, opponentId: number, ourSlot: number, theirSlot: number): Promise<TeamDuel> {
  return getJSON<TeamDuel>(`/api/teams/${id}/duel?opponent_id=${opponentId}&our_slot=${ourSlot}&their_slot=${theirSlot}`);
}

/** Apply a set given by name (the coach's or the engine's suggestion) to an existing slot. */
export function applySlotBuild(
  teamId: number,
  slot: number,
  build: { moves?: string[]; ability?: string | null; nature?: string | null; item?: string | null; evs?: Record<string, number> },
): Promise<Team> {
  return getJSON<Team>(`/api/teams/${teamId}/slots/${slot}/build`, jsonInit("POST", build));
}

/** One set change the coach recommended, already checked against the slot's legal options. */
