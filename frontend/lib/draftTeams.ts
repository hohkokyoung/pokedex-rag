/* A team made by "New team" is a draft until its first Pokémon is added. If the
   user leaves before that, it's deleted — so an untouched "New team" never shows
   up as an empty row. Shared between the team page (which discards) and the list
   (which hides anything mid-discard so it doesn't flash back). */

import { createTeam, deleteTeam, listTeams } from "@/lib/api";

/** Draft ids being (or already) discarded this session — lists hide them. */
export const discarding = new Set<number>();
const timers = new Map<number, ReturnType<typeof setTimeout>>();

/** Schedule the delete one tick out, so a React Strict Mode remount can cancel it. */
export function discardDraft(id: number) {
  discarding.add(id);
  write(read().filter((x) => x !== id));
  timers.set(
    id,
    setTimeout(() => {
      timers.delete(id);
      // Stays in `discarding` for the session: a list fetched while this delete was
      // in flight may still contain it, and a deleted draft never comes back.
      deleteTeam(id, { keepalive: true }).catch(() => discarding.delete(id));
    }, 0),
  );
}

/** The page is still (or again) showing this draft — keep it. */
export function keepDraft(id: number) {
  const t = timers.get(id);
  if (t) clearTimeout(t);
  timers.delete(id);
  discarding.delete(id);
}

// Drafts are also remembered in localStorage, so one abandoned by closing the tab
// (no unmount runs) is swept the next time the list loads.
const KEY = "pokerag.draftTeams";
const read = (): number[] => {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
};
const write = (ids: number[]) => {
  try {
    localStorage.setItem(KEY, JSON.stringify(ids));
  } catch {
    /* storage unavailable — the unmount path still cleans up */
  }
};

export function markDraft(id: number) {
  write([...new Set([...read(), id])]);
}

/** The draft got its first Pokémon — it's a real team now. */
export function promoteDraft(id: number) {
  write(read().filter((x) => x !== id));
  keepDraft(id);
}

/** Delete remembered drafts that are still empty; returns the ids to hide. */
export function sweepDrafts(teams: { id: number; size: number }[]): Set<number> {
  const drafts = new Set(read());
  const gone = new Set<number>();
  for (const t of teams) {
    if (!drafts.has(t.id)) continue;
    if (t.size === 0) {
      gone.add(t.id);
      deleteTeam(t.id).catch(() => {});
    }
  }
  write([...drafts].filter((id) => teams.some((t) => t.id === id && t.size === 0 && !gone.has(id))));
  return gone;
}

/** Create a fresh draft named "New team" (numbered if taken) and remember it. */
export async function createDraft(): Promise<number> {
  const { teams } = await listTeams();
  const names = new Set(teams.map((t) => t.name));
  let name = "New team";
  for (let i = 2; names.has(name); i++) name = `New team ${i}`;
  const team = await createTeam(name, "player");
  markDraft(team.id);
  return team.id;
}

// A draft URL whose team was already discarded (e.g. back, then forward) gets a
// fresh draft instead of "Team not found". Shared per missing id so React Strict
// Mode's double effect can't create two.
const replacements = new Map<number, Promise<number>>();
export function replaceMissingDraft(missingId: number): Promise<number> {
  let p = replacements.get(missingId);
  if (!p) {
    p = createDraft();
    replacements.set(missingId, p);
    p.catch(() => replacements.delete(missingId));
  }
  return p;
}
