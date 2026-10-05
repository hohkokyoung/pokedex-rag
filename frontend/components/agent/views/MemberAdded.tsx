"use client";

import { useState } from "react";
import { clearSlot, type MemberAddedView, type Team } from "@/lib/api";
import { sprite } from "./shared";

/** "Added Garchomp to slot 4" with Undo (clears the slot), or why nothing was added. */
export function MemberAddedStrip({ view, onTeamUpdated }: { view: MemberAddedView; onTeamUpdated: (team: Team) => void }) {
  const [undone, setUndone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const undo = async () => {
    if (!view.slot) return;
    setBusy(true);
    setErr("");
    try {
      onTeamUpdated(await clearSlot(view.team_id, view.slot));
      setUndone(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't undo.");
    }
    setBusy(false);
  };
  const art = sprite(view.card.pokemon_id ?? view.card.dex_number);
  return (
    <div className={`co-added ${view.added ? "" : "is-noop"}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      {art && <img src={art} alt="" width={36} height={36} />}
      <span className="t">
        {undone ? <>Removed <b>{view.card.name}</b> again.</> : view.added ? <>Added <b>{view.card.name}</b> to slot {view.slot}</> : view.message.replace(/\*\*/g, "")}
      </span>
      {view.added && !undone && (
        <button className="rev" onClick={undo} disabled={busy}>{busy ? "…" : "Undo"}</button>
      )}
      {err && <span className="co-err">{err}</span>}
    </div>
  );
}
