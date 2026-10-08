"use client";

import { useState } from "react";
import { applySlotBuild, type SetEditView, type Team, thumb } from "@/lib/api";
import { restoreMember } from "./Candidates";

const EV_SHORT: Record<string, string> = { hp: "HP", atk: "Atk", def: "Def", spa: "SpA", spd: "SpD", spe: "Spe" };
const evText = (evs: Record<string, number> | undefined | null) =>
  Object.entries(evs ?? {}).filter(([, v]) => v).map(([k, v]) => `${v} ${EV_SHORT[k] ?? k}`).join(" / ") || "none";

/**
 * A proposed set for one member, was → now. Nothing is saved until Apply; Revert puts the
 * member back exactly as it was; Dismiss hides the card.
 */
export function SetEditCard({
  view,
  onUpdated,
}: {
  view: SetEditView;
  /** Called with the saved team (ours or the opponent's, per ``view.side``). */
  onUpdated: (team: Team) => void;
}) {
  const [applied, setApplied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [gone, setGone] = useState(false);
  if (gone) return null;

  const { before: b, after: a } = view;
  const rows: [string, string, string][] = [
    ["Ability", b.ability ?? "—", a.ability ?? b.ability ?? "—"],
    ["Nature", b.nature ?? "—", a.nature ?? b.nature ?? "—"],
    ["Item", b.item ?? "No item", a.item && a.item !== "None" ? a.item : "No item"],
    ["EVs", evText(b.evs), evText(a.evs)],
  ];

  const apply = async () => {
    setBusy(true);
    setErr("");
    try {
      onUpdated(await applySlotBuild(view.team_id, view.slot, view.fields));
      setApplied(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't apply the set.");
    }
    setBusy(false);
  };
  const revert = async () => {
    setBusy(true);
    setErr("");
    try {
      onUpdated(await restoreMember(view.team_id, view.member));
      setApplied(false);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't revert.");
    }
    setBusy(false);
  };

  return (
    <div className={`co-prop${applied ? " applied" : ""}`}>
      <div className="co-prop-h">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img loading="lazy" decoding="async" src={thumb(view.sprite_url, 48)} alt="" width={36} height={36} />
        <span className="t">
          {applied ? "Applied to " : "Proposed set for "}
          <b>{view.name}</b>
          {view.side === "theirs" && <em> (opponent)</em>}
        </span>
        <span className="acts">
          {applied ? (
            <button className="rev" onClick={revert} disabled={busy}>{busy ? "…" : "Revert"}</button>
          ) : (
            <>
              <button className="ok" onClick={apply} disabled={busy}>{busy ? "Saving…" : "Apply"}</button>
              <button className="x" onClick={() => setGone(true)} aria-label="Dismiss">Dismiss</button>
            </>
          )}
        </span>
      </div>
      <div className="co-diff">
        {rows.map(([k, was, now]) => (
          <div key={k} className={was === now ? "same" : "chg"}>
            <span className="k">{k}</span>
            {was === now ? <span>{now}</span> : <span><s>{was}</s> → <b>{now}</b></span>}
          </div>
        ))}
        <div className="moves">
          <span className="k">Moves</span>
          <span className="mv">
            {a.moves.map((m) => <i key={m} className={b.moves.includes(m) ? "" : "new"}>{m}</i>)}
            {b.moves.filter((m) => !a.moves.includes(m)).map((m) => <i key={m} className="gone">{m}</i>)}
          </span>
        </div>
      </div>
      {err && <p className="co-err">{err}</p>}
    </div>
  );
}
