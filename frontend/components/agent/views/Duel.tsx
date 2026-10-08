"use client";

import type { DuelView } from "@/lib/api";
import { titleCase, typeVars } from "@/lib/pokeTypes";

const OUTCOME: Record<string, string> = { win: "wins", lose: "loses", even: "is even" };

/** One pairing played out: who wins, who moves first, each side's moves, then the log. */
export function DuelCard({ view }: { view: DuelView }) {
  const d = view.duel;
  const name = (side: "a" | "b") => (side === "a" ? d.our_name : d.their_name);
  const first = d.first === "ours" ? d.our_name : d.first === "theirs" ? d.their_name : "Speed tie";
  return (
    <div className={`co-duel is-${d.outcome}`}>
      <div className="co-duel-h">
        <b>{d.our_name}</b> vs <b>{d.their_name}</b>
        <span className="st">{d.our_name} {OUTCOME[d.outcome]}</span>
        <small>{first === "Speed tie" ? first : `${first} moves first`}</small>
      </div>
      <div className="co-duel-mv">
        <span><em>{d.our_name}</em> {d.our_moves.join(" · ") || "—"}</span>
        <span><em>{d.their_name}</em> {d.their_moves.join(" · ") || "—"}</span>
      </div>
      <ol className="co-duel-log">
        {d.log.filter((e) => e.kind !== "nothing").slice(0, 12).map((e, i) => (
          <li key={i} className={`s-${e.side}`}>
            <span className="tn">T{e.turn}</span>
            <span>
              <b>{name(e.side)}</b>{" "}
              {e.kind === "attack" && e.move ? (
                <>
                  uses <i style={typeVars(e.type ?? "normal") as React.CSSProperties}>{e.move}</i>
                  {e.pct != null && <> — {Math.round(e.pct)}%</>}
                  {e.mult != null && e.mult !== 1 && <> ({e.mult}×)</>}
                </>
              ) : e.kind === "faint" ? "faints" : titleCase(e.kind.replace("-", " "))}
              {e.hp != null && e.kind !== "faint" && <small> · {Math.round(e.hp)}% left</small>}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
