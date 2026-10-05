"use client";

import { useEffect, useState } from "react";
import type { MoveListView } from "@/lib/api";
import { titleCase, typeColor } from "@/lib/pokeTypes";
import { CiteBadge, type Linking } from "./shared";

/** Moves as rows with a power bar, grouped by type. */
export function MoveChart({ view, link }: { view: MoveListView; link: Linking }) {
  const max = Math.max(...view.moves.map((m) => m.power ?? 0), 1);
  const [grown, setGrown] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setGrown(true));
    return () => cancelAnimationFrame(id);
  }, []);
  return (
    <ol className="ax-moves">
      {view.moves.map((m, i) => {
        const n = link.n(m.ref);
        const groupStart = i > 0 && view.moves[i - 1].type !== m.type;
        return (
          <li
            key={`${m.name}-${i}`}
            data-src={n ?? undefined}
            className={groupStart ? "is-group" : ""}
            style={{ animationDelay: `${i * 45}ms`, "--tc": typeColor(m.type) } as React.CSSProperties}
          >
            <div className={`ax-mv ${n !== null && link.hot === n ? "is-hot" : ""}`} title={m.effect ?? undefined} {...link.hover(n)}>
              <span className="ax-mv__type">{titleCase(m.type)}</span>
              <span className="ax-mv__name">
                {m.name}
                <small>
                  {titleCase(m.damage_class ?? "status")} · {m.accuracy === null ? "never misses" : `${m.accuracy}% acc`}
                  {m.pp !== null && <> · {m.pp} PP</>}
                  {m.learners !== null && <> · {m.learners} learn it</>}
                </small>
                {m.effect && <em>{m.effect}</em>}
              </span>
              <span className="ax-rank__track">
                <span
                  className="ax-mv__fill"
                  style={{ transform: `scaleX(${grown ? (m.power ?? 0) / max : 0})`, transitionDelay: `${120 + i * 45}ms` }}
                />
              </span>
              <span className="ax-mv__val">{m.power ?? "—"}</span>
              <CiteBadge n={n} cited={link.cited} className="ax-rank__n" />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
