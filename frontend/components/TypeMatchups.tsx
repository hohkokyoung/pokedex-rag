import type { ReactNode } from "react";
import TypeBadge from "@/components/TypeBadge";
import type { Matchups } from "@/lib/types";

type Tone = "bad" | "good" | "immune" | "hit";

/* Rows are grouped by verdict; a group's label shows once, on its first row. */
const GROUPS: { tone: Tone; label: string; rows: { key: keyof Matchups; mult: string }[] }[] = [
  { tone: "bad", label: "Takes more from", rows: [{ key: "weak_4x", mult: "×4" }, { key: "weak_2x", mult: "×2" }] },
  { tone: "good", label: "Resists", rows: [{ key: "resist_half", mult: "×½" }, { key: "resist_quarter", mult: "×¼" }] },
  { tone: "immune", label: "Immune to", rows: [{ key: "immune", mult: "×0" }] },
];

/**
 * Type matchups as grouped rows: Takes more from (×4/×2), Resists (×½/×¼),
 * Immune to (×0) and, when `hits` is given, what the typing hits ×2. Only rows
 * with types are shown. Shared by the detail page and the home Type Calculator;
 * each passes its own chip via `renderType`.
 */
export default function TypeMatchups({
  m,
  hits,
  renderType = (t) => <TypeBadge key={t} type={t} size="sm" />,
}: {
  m: Matchups;
  hits?: string[];
  renderType?: (t: string) => ReactNode;
}) {
  const groups = [
    ...GROUPS.map((g) => ({ ...g, rows: g.rows.map((r) => ({ mult: r.mult, types: m[r.key] ?? [] })) })),
    ...(hits ? [{ tone: "hit" as Tone, label: "Hits", rows: [{ mult: "×2", types: hits }] }] : []),
  ]
    .map((g) => ({ ...g, rows: g.rows.filter((r) => r.types.length) }))
    .filter((g) => g.rows.length);

  if (groups.length === 0) {
    return <p className="mu__none font-mono">Perfectly neutral: no notable weaknesses or resistances.</p>;
  }
  return (
    <div className="mu">
      {groups.map((g) => (
        <div className={`mu__grp mu__grp--${g.tone}`} key={g.tone}>
          {g.rows.map((r, i) => (
            <div className="mu__row" key={r.mult}>
              <span className="mu__label font-mono">{i === 0 ? g.label : ""}</span>
              <span className="mu__mult font-mono">{r.mult}</span>
              <div className="mu__types">{r.types.map((t) => renderType(t))}</div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
