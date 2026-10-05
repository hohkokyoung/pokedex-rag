"use client";

import { useState } from "react";
import { assetUrl, clearSlot, setSlot, type Candidate, type CandidatesView, type Team } from "@/lib/api";
import { Chip } from "@/components/TeamCardParts";

type Member = Team["members"][number];
type Replace = { slot?: number; busy?: boolean; done?: Member; err?: string };

/** Restore a member exactly as it was (Revert / Undo for replaces). */
export async function restoreMember(teamId: number, b: Member): Promise<Team> {
  return setSlot(teamId, b.slot, {
    pokemon_id: b.pokemon_id, form_id: b.form_id ?? null, ability_id: b.ability?.id ?? null,
    nature_id: b.nature?.id ?? null, item_id: b.item?.id ?? null, ev_spread: b.ev_spread ?? null,
    iv_spread: b.iv_spread ?? null, move_ids: b.moves.length ? b.moves.map((x) => x.move_id) : null,
  });
}

/**
 * Pokémon the coach suggests adding. Nothing changes until a button is pressed: Add fills
 * the next empty slot (Revert clears it); on a full team, Replace… picks a member to swap
 * out (Confirm, then Revert restores them).
 */
export function CandidateCards({
  view,
  team,
  onAdd,
  onTeamUpdated,
}: {
  view: CandidatesView;
  team: Team;
  onAdd: (pokemonId: number) => Promise<{ ok: boolean; msg: string; slot?: number }>;
  onTeamUpdated: (team: Team) => void;
}) {
  const [added, setAdded] = useState<Record<number, { msg: string; slot?: number; busy?: boolean }>>({});
  const [replace, setReplace] = useState<Record<number, Replace>>({});
  const teamFull = team.members.length >= 6;
  const patchReplace = (id: number, patch: Replace | null) =>
    setReplace((r) => {
      const n = { ...r };
      if (patch === null) delete n[id];
      else n[id] = { ...r[id], ...patch };
      return n;
    });

  const add = async (c: Candidate) => {
    if (added[c.pokemon_id]) return;
    const res = await onAdd(c.pokemon_id);
    setAdded((prev) => ({ ...prev, [c.pokemon_id]: { msg: res.msg, slot: res.ok ? res.slot : undefined } }));
  };
  const undoAdd = async (c: Candidate) => {
    const a = added[c.pokemon_id];
    if (!a?.slot) return;
    setAdded((prev) => ({ ...prev, [c.pokemon_id]: { ...a, busy: true } }));
    try {
      onTeamUpdated(await clearSlot(team.id, a.slot));
      setAdded((prev) => {
        const n = { ...prev };
        delete n[c.pokemon_id];
        return n;
      });
    } catch {
      setAdded((prev) => ({ ...prev, [c.pokemon_id]: { ...a, busy: false } }));
    }
  };
  const confirmReplace = async (c: Candidate) => {
    const slot = replace[c.pokemon_id]?.slot;
    const before = team.members.find((m) => m.slot === slot);
    if (!slot || !before) return;
    patchReplace(c.pokemon_id, { busy: true, err: undefined });
    try {
      onTeamUpdated(await setSlot(team.id, slot, { pokemon_id: c.pokemon_id }));
      patchReplace(c.pokemon_id, { busy: false, done: before });
    } catch (e) {
      patchReplace(c.pokemon_id, { busy: false, err: e instanceof Error ? e.message : "Couldn't replace." });
    }
  };
  const revertReplace = async (c: Candidate) => {
    const b = replace[c.pokemon_id]?.done;
    if (!b) return;
    patchReplace(c.pokemon_id, { busy: true });
    try {
      onTeamUpdated(await restoreMember(team.id, b));
      patchReplace(c.pokemon_id, null);
    } catch {
      patchReplace(c.pokemon_id, { busy: false });
    }
  };

  return (
    <div className="co-cands">
      {view.candidates.map((c) => {
        const r = replace[c.pokemon_id];
        const ad = added[c.pokemon_id];
        let action: React.ReactNode;
        if (r?.done) {
          action = (
            <span className="co-repl">
              <span className="st">Replaced {r.done.name}</span>
              <button onClick={() => revertReplace(c)} disabled={r.busy}>{r.busy ? "…" : "Revert"}</button>
            </span>
          );
        } else if (ad) {
          action = ad.slot ? (
            <span className="co-repl">
              <span className="st">{ad.msg}</span>
              <button onClick={() => undoAdd(c)} disabled={ad.busy}>{ad.busy ? "…" : "Revert"}</button>
            </span>
          ) : <span className="st">{ad.msg}</span>;
        } else if (!teamFull) {
          action = <button onClick={() => add(c)}>Add</button>;
        } else if (r?.slot) {
          const out = team.members.find((m) => m.slot === r.slot);
          action = (
            <span className="co-repl">
              <span className="q">Replace <b>{out?.name}</b>?</span>
              <button className="ok" onClick={() => confirmReplace(c)} disabled={r.busy}>{r.busy ? "Saving…" : "Confirm"}</button>
              <button onClick={() => patchReplace(c.pokemon_id, null)}>Cancel</button>
            </span>
          );
        } else if (r) {
          action = (
            <span className="co-repl pick" role="group" aria-label={`Pick who ${c.name} replaces`}>
              <span className="q">Replace who?</span>
              {[...team.members].sort((a, b) => a.slot - b.slot).map((m) => (
                <button key={m.slot} className="mon" title={m.name} onClick={() => patchReplace(c.pokemon_id, { slot: m.slot })}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={assetUrl(m.sprite_url)} alt={m.name} width={28} height={28} />
                </button>
              ))}
              <button onClick={() => patchReplace(c.pokemon_id, null)}>Cancel</button>
            </span>
          );
        } else {
          action = <button onClick={() => patchReplace(c.pokemon_id, {})}>Replace…</button>;
        }
        return (
          <div key={c.pokemon_id} className="co-cand">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetUrl(c.sprite_url)} alt="" width={40} height={40} />
            <div>
              <b>{c.name}</b>
              <span className="tp">{c.types.map((ty) => <Chip key={ty} t={ty} />)}<em>{c.role}</em></span>
              <small>{c.reason}</small>
            </div>
            {action}
            {r?.err && <span className="co-err">{r.err}</span>}
          </div>
        );
      })}
    </div>
  );
}
