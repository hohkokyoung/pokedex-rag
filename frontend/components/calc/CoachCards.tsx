"use client";

import type { DamageView, HitRange, SurviveView } from "@/lib/api";

const pct = (r: HitRange) => `${r.min_pct.toFixed(1)}–${r.max_pct.toFixed(1)}%`;
const KoTag = ({ r }: { r: HitRange }) => (
  <em className={r.ko === 1 ? "ko" : r.ko === 0 ? "imm" : ""}>
    {r.ko_text || (r.ko === 0 ? "no damage" : `${r.ko}HKO`)}
  </em>
);

type Acts = {
  /** The calculator still holds the Pokémon the card is about. */
  live: boolean;
  applied: boolean;
  onApply: () => void;
  onRevert: () => void;
};

function Actions({
  live,
  applied,
  onApply,
  onRevert,
  label,
}: Acts & { label: string }) {
  return (
    <span className="acts">
      {applied ? (
        <button className="rev" onClick={onRevert}>
          Revert
        </button>
      ) : (
        <button
          className="ok"
          onClick={onApply}
          disabled={!live}
          title={live ? undefined : "The calculator has changed since"}
        >
          {label}
        </button>
      )}
    </span>
  );
}

/** "Can X OHKO Y?": the calculator's hit, plus the what-if when the question changed something. */
export function DamageCard({ view, ...acts }: { view: DamageView } & Acts) {
  const changed = view.changes.map((c) => c.value).join(", ");
  return (
    <div className="dc-cc">
      <div className="dc-cc-h">
        <span className="t">
          <b>{view.attacker.name}</b>’s {view.move.name} →{" "}
          <b>{view.defender.name}</b>
        </span>
        {view.whatif && view.apply.length > 0 && (
          <Actions {...acts} label="Apply" />
        )}
      </div>
      <div className={`dc-cc-row${view.whatif ? " was" : ""}`}>
        <span className="dc-k">{view.whatif ? "Now" : "Damage"}</span>
        <b>{pct(view.current)}</b>
        <KoTag r={view.current} />
      </div>
      {view.whatif && (
        <div className="dc-cc-row">
          <span className="dc-k">With {changed}</span>
          <b>{pct(view.whatif)}</b>
          <KoTag r={view.whatif} />
        </div>
      )}
    </div>
  );
}

/** "How much bulk to survive?": the smallest spread that lives, and what the hit then does. */
export function SurviveCard({ view, ...acts }: { view: SurviveView } & Acts) {
  const stat = view.stat === "def" ? "Def" : "SpD";
  const spread =
    [
      view.hp_ev && `${view.hp_ev} HP`,
      view.stat_ev && `${view.stat_ev} ${stat}`,
    ]
      .filter(Boolean)
      .join(" / ") || "no EVs";
  return (
    <div className="dc-cc">
      <div className="dc-cc-h">
        <span className="t">
          <b>{view.defender.name}</b> vs {view.attacker.name}’s {view.move.name}
        </span>
        {view.apply && <Actions {...acts} label="Apply EVs" />}
      </div>
      <div className="dc-cc-row was">
        <span className="dc-k">Now</span>
        <b>{pct(view.current)}</b>
        <KoTag r={view.current} />
      </div>
      {view.already ? (
        <div className="dc-cc-row">
          <span className="dc-k">Verdict</span>
          <span className="ok">Already survives as set</span>
        </div>
      ) : (
        <div className="dc-cc-row">
          <span className="dc-k">
            {view.survives ? "Survives with" : "Best try"}
          </span>
          <b>
            {spread}
            {view.nature_changed && ` · ${view.nature}`}
          </b>
          <span className={view.survives ? "ok" : "ko"}>
            takes {pct(view.range)}
            {view.survives ? "" : " — can’t survive"}
          </span>
        </div>
      )}
    </div>
  );
}
