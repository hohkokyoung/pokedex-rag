"use client";

import type { AskSource, AskView } from "@/lib/api";
import type { StepRun } from "./useAsk";
import { SourceCard, ViewBlock, refIndex, viewCaption, viewRefs } from "./ViewBlock";
import { sprite, type Linking } from "./views/shared";
import { thumb } from "@/lib/api";

export const TOOL_TITLE: Record<string, string> = {
  query_pokemon: "Pokédex query",
  get_pokemon: "Profile",
  semantic_search: "Descriptions",
  similar_to: "Look-alikes",
  user_profile: "For you",
  type_matchup: "Type matchup",
  coverage_vs_types: "Coverage",
  learnset: "Learnset",
  move_info: "Move",
  ability_info: "Ability",
  item_info: "Item",
  encounters: "Where to find",
};

/**
 * Evidence, drawn from the plan's typed views in step order; any source no view
 * covers (descriptions, dex entries …) becomes a card — cited ones shown, the rest
 * folded behind "Show all".
 */
export function EvidencePanel({
  steps,
  views,
  sources,
  cited,
  done,
  hot,
  setHot,
  showAll,
  setShowAll,
  maxViews,
}: {
  steps: StepRun[];
  views: AskView[];
  sources: AskSource[];
  cited: Set<number>;
  done: boolean;
  hot: number | null;
  setHot: (n: number | null) => void;
  showAll: boolean;
  setShowAll: (v: boolean) => void;
  maxViews?: number;
}) {
  const index = refIndex(sources);
  const order = new Map(steps.map((s, i) => [s.id, i]));
  const ordered = [...views].sort((a, b) => (order.get(a.step) ?? 99) - (order.get(b.step) ?? 99));
  const shownViews = maxViews ? ordered.slice(0, maxViews) : ordered;
  const hover = (n: number | null) =>
    n === null ? {} : { onMouseEnter: () => setHot(n), onMouseLeave: () => setHot(null) };
  const linkFor = (step: string): Linking => ({
    n: (ref) => (ref == null ? null : index.get(`${step}:${ref}`) ?? null),
    hot,
    cited,
    hover,
  });

  const covered = new Set<number>();
  for (const v of ordered)
    for (const r of viewRefs(v)) {
      const n = index.get(`${v.step}:${r}`);
      if (n !== undefined) covered.add(n);
    }
  const loose = sources.filter((s) => !covered.has(s.n));
  const shownLoose = loose.filter((s) => cited.has(s.n) || showAll);
  const rest = loose.filter((s) => !cited.has(s.n));
  const plain: Linking = { n: (r) => r ?? null, hot, cited, hover };
  const toolOf = new Map(steps.map((s) => [s.id, s.tool]));

  if (!shownViews.length && !loose.length) return null;
  return (
    <section className="ax-ev" aria-label="Evidence">
      <header className="ax-ev__head">
        <span>Evidence</span>
        <span className="ax-ev__count">
          {cited.size} cited · {sources.length} retrieved
        </span>
      </header>

      {shownViews.map((v, i) => (
        <div key={`${v.step}-${v.kind}-${i}`} className="ax-view">
          {ordered.length > 1 && (
            <div className="ax-view__head">
              <span className="ax-view__tool">{TOOL_TITLE[toolOf.get(v.step) ?? ""] ?? toolOf.get(v.step)}</span>
              <span className="ax-view__cap">— {viewCaption(v)}</span>
            </div>
          )}
          <ViewBlock view={v} link={linkFor(v.step)} />
        </div>
      ))}

      {shownLoose.length > 0 && (
        <div className="ax-ev__grid" data-n={Math.min(shownLoose.length, 5)}>
          {shownLoose.map((s, i) => (
            <SourceCard key={s.n} s={s} link={plain} delay={i * 50} />
          ))}
        </div>
      )}

      {rest.length > 0 && !showAll && (
        <div className="ax-also">
          <span className="ax-also__avs" aria-hidden>
            {rest.slice(0, 6).map((s) => {
              const art = sprite(s.pokemon_id ?? s.dex_number);
              return art ? <img loading="lazy" decoding="async" key={s.n} src={thumb(art, 160)} alt="" /> : null;
            })}
          </span>
          <span className="ax-also__txt">
            {!done && !cited.size
              ? `Reading ${rest.length} retrieved records…`
              : cited.size
                ? `${rest.length} more retrieved but not used in the answer`
                : `${rest.length} retrieved, none used in the answer`}
          </span>
          {(done || cited.size > 0) && (
            <button type="button" onClick={() => setShowAll(true)}>
              Show all
            </button>
          )}
        </div>
      )}
    </section>
  );
}

/** Names a view already charts, so the answer doesn't repeat them as bullets. */
export function chartedNames(views: AskView[]): Set<string> {
  const out = new Set<string>();
  for (const v of views) {
    if (v.kind === "ranking") v.rows.forEach((r) => out.add(r.name.toLowerCase()));
    if (v.kind === "move_list" && v.moves.length > 1) v.moves.forEach((m) => out.add(m.name.toLowerCase()));
  }
  return out;
}

/** Move name → type, for the coloured dot on answer bullets that name a move. */
export function moveTypes(views: AskView[]): Map<string, string> {
  const out = new Map<string, string>();
  for (const v of views) {
    if (v.kind === "move_list") v.moves.forEach((m) => out.set(m.name.toLowerCase(), m.type));
    if (v.kind === "learners" || v.kind === "learn_check") out.set(v.move.name.toLowerCase(), v.move.type);
  }
  return out;
}
