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
  generation?: number;
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
  if (params.generation) sp.set("generation", String(params.generation));
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
};

export type AskResponse = {
  answer: string;
  route?: string;
  sources: AskSource[];
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
export type SlotMove = {
  move_id: number;
  name: string;
  type: string | null;
  damage_class: string | null;
  power: number | null;
};

export type TeamMember = {
  slot: number;
  pokemon_id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  base_stats: Record<string, number>;
  final_stats: Record<string, number>;
  ability: SlotAbility | null;
  nature: SlotNature | null;
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
  ability_id?: number | null;
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
};
export type SlotSuggestion = {
  slot: number;
  name: string;
  recommended_ability: string | null;
  ability_reason: string | null;
  recommended_nature: string | null;
  recommended_evs: Record<string, number>;
  rationale: string;
};
export type OpponentThreat = {
  opponent_name: string;
  opponent_types: string[];
  threatens: string[];
  via: string[];
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
  };
  roles: { members: MemberRole[]; missing_roles: string[]; notes: string[] };
  suggestions: SlotSuggestion[];
  vs_opponent:
    | { opponent_id: number; opponent_name: string; threats: OpponentThreat[]; advice: string[] }
    | null;
  summary: string[];
};

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

export async function deleteTeam(id: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/teams/${id}`, { method: "DELETE" });
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
};

export function searchMoves(q: string, limit = 6): Promise<MoveResult[]> {
  return getJSON<MoveResult[]>(`/api/moves?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export type MoveLearner = {
  id: number;
  dex_number: number;
  name: string;
  types: string[];
  sprite_url: string;
  learn_method: string | null;
  level: number | null;
};

export function getMoveLearners(moveId: number, limit = 120): Promise<MoveLearner[]> {
  return getJSON<MoveLearner[]>(`/api/moves/${moveId}/learners?limit=${limit}`);
}

export function searchAbilities(q: string, limit = 6): Promise<Ability[]> {
  return getJSON<Ability[]>(`/api/abilities?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export type ItemResult = {
  id: number;
  identifier: string;
  name: string;
  category: string | null;
  cost: number | null;
  short_effect: string | null;
};

export function searchItems(q: string, limit = 8): Promise<ItemResult[]> {
  return getJSON<ItemResult[]>(`/api/items?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export function getTeamAnalysis(id: number, opponentId?: number | null): Promise<TeamAnalysis> {
  const q = opponentId ? `?opponent_id=${opponentId}` : "";
  return getJSON<TeamAnalysis>(`/api/teams/${id}/analysis${q}`);
}

/** Stream a grounded coaching answer over SSE (POST + ReadableStream). */
export async function coachAskStream(
  teamId: number,
  question: string,
  opponentId: number | null,
  handlers: StreamHandlers,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/teams/${teamId}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, opponent_id: opponentId }),
      signal: handlers.signal,
    });
  } catch {
    handlers.onError?.("request-failed");
    return;
  }
  if (!res.ok || !res.body) return handlers.onError?.("request-failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      let event = "message";
      let data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      const parsed = JSON.parse(data);
      if (event === "sources") handlers.onSources?.(parsed as AskSource[]);
      else if (event === "candidates") handlers.onCandidates?.(parsed as Candidate[]);
      else if (event === "team_updated") handlers.onTeamUpdated?.(parsed as Team);
      else if (event === "delta") handlers.onDelta?.((parsed as { text: string }).text);
      else if (event === "done") handlers.onDone?.();
      else if (event === "error") handlers.onError?.((parsed as { message: string }).message);
    }
  }
}

export type StreamHandlers = {
  onRoute?: (route: string) => void;
  onSources?: (sources: AskSource[]) => void;
  onCandidates?: (candidates: Candidate[]) => void;
  onTeamUpdated?: (team: Team) => void;
  onDelta?: (text: string) => void;
  onDone?: () => void;
  onError?: (reason: string) => void;
  signal?: AbortSignal;
};

/** Stream a grounded answer over SSE (POST + ReadableStream). */
export async function askQuestionStream(
  question: string,
  handlers: StreamHandlers,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal: handlers.signal,
    });
  } catch {
    handlers.onError?.("request-failed");
    return;
  }

  if (res.status === 503) return handlers.onError?.("assistant-not-configured");
  if (!res.ok || !res.body) return handlers.onError?.("request-failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);

      let event = "message";
      let data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;

      const parsed = JSON.parse(data);
      if (event === "route") handlers.onRoute?.((parsed as { route: string }).route);
      else if (event === "sources") handlers.onSources?.(parsed as AskSource[]);
      else if (event === "delta") handlers.onDelta?.((parsed as { text: string }).text);
      else if (event === "done") handlers.onDone?.();
      else if (event === "error")
        handlers.onError?.((parsed as { message: string }).message);
    }
  }
}
