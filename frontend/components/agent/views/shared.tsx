"use client";

import { assetUrl } from "@/lib/api";
import { titleCase, typeChip } from "@/lib/pokeTypes";

/**
 * What every view needs to link its rows to the answer's citations: ``n`` maps a
 * step-local evidence index (a view's ``ref``) to the global ``[n]``, ``hot`` is the
 * citation being hovered, and ``hover(n)`` wires a row up to set it.
 */
export type Linking = {
  n: (ref: number | null | undefined) => number | null;
  hot: number | null;
  cited: Set<number>;
  hover: (n: number | null) => { onMouseEnter?: () => void; onMouseLeave?: () => void };
};

export const sprite = (id: number | null | undefined) =>
  id ? assetUrl(`/sprites/official-artwork/${id}.png`) : "";

/** Learn-method colours, keyed by method (level-up, machine, tutor, egg). */
export const METHOD_COLOR: Record<string, string> = {
  "level-up": "var(--accent)",
  machine: "#3f7fd8",
  tutor: "#8a5cd6",
  egg: "#e0a526",
};

export const METHOD_LABEL: Record<string, string> = {
  "level-up": "Level-up",
  machine: "TM",
  tutor: "Tutor",
  egg: "Egg",
};

export function Types({ types }: { types: string[] }) {
  if (!types.length) return null;
  return (
    <span className="ax-types">
      {types.map((t) => (
        <span key={t} className="ax-type" style={typeChip(t)}>
          {titleCase(t)}
        </span>
      ))}
    </span>
  );
}

/** The small citation badge on a row/card ("is-off" when the answer didn't cite it). */
export function CiteBadge({ n, cited, className = "ax-evc__n" }: { n: number | null; cited: Set<number>; className?: string }) {
  if (n === null) return null;
  return <span className={`${className} ${cited.has(n) ? "" : "is-off"}`}>{n}</span>;
}
