"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { AskSource, AskView, LearnersView, PokemonCardData, TypeChartView } from "@/lib/api";
import { STAT_LABEL, STAT_ORDER, STAT_SHORT } from "@/lib/askEvidence";
import { dexLabel, titleCase } from "@/lib/pokeTypes";
import { Tag } from "@/components/calc/fields";
import TypeMatchups from "@/components/TypeMatchups";
import { TOOL_TITLE } from "./Evidence";
import { TOOL_LABEL } from "./PlanSteps";
import type { AskRun } from "./runState";
import { CHUNK_LABEL, SourceCard, ViewBlock, refIndex, viewCaption, viewRefs } from "./ViewBlock";
import { METHOD_COLOR, METHOD_LABEL, sprite, type Linking } from "./views/shared";
import { STAT_NAME } from "./views/RankChart";
import { thumb } from "@/lib/api";

/**
 * The /ask results as tiles: the answer (with one row per lookup when several drew
 * results) with the type chart's matchups as a panel beside it, one tile per other
 * view, and a Records tile for sources no view draws. Every tile ends with the
 * records it came from. Hover/click links ``[n]`` citations to rows via ``hot``.
 */
export function AskBento({
  run,
  answer,
  cited,
  hot,
  setHot,
  cite,
  citeRange,
}: {
  run: AskRun;
  /** The rendered verdict + bullets (``<Answer/>``). */
  answer: ReactNode;
  cited: Set<number>;
  hot: number | null;
  setHot: (n: number | null) => void;
  cite: (n: number) => ReactNode;
  /** A run of records ("2–9") as one citation. */
  citeRange: (a: number, b: number) => ReactNode;
}) {
  const [showAll, setShowAll] = useState(false);
  const { steps, views, sources, status } = run;
  const index = refIndex(sources);
  const order = new Map(steps.map((s, i) => [s.id, i]));
  const ordered = [...views].sort((a, b) => (order.get(a.step) ?? 99) - (order.get(b.step) ?? 99));
  const hover = (n: number | null) =>
    n === null ? {} : { onMouseEnter: () => setHot(n), onMouseLeave: () => setHot(null) };
  const linkFor = (step: string): Linking => ({
    n: (ref) => (ref == null ? null : index.get(`${step}:${ref}`) ?? null),
    hot,
    cited,
    hover,
  });
  const nsOf = (v: AskView) =>
    viewRefs(v)
      .map((r) => index.get(`${v.step}:${r}`))
      .filter((n): n is number => n !== undefined);
  const bySrc = new Map(sources.map((s) => [s.n, s]));
  const from = (ns: number[]) => (
    <From sources={ns.map((n) => bySrc.get(n)).filter((s): s is AskSource => !!s)} cite={cite} citeRange={citeRange} />
  );

  // The first type chart is its own card beside the answer (the answer caps its bullets
  // so the two stay about the same height); a one-sentence answer spans the row and the
  // matchups go under it as a strip (CSS, ``.ab-answer:not(:has(…)) + .ab-side``).
  const charts = ordered.filter((v): v is TypeChartView => v.kind === "type_chart");
  const side = charts[0];
  const wide = ordered.filter((v) => v !== side);
  // One "part" per lookup that drew something — several views from one step are one part.
  const parts = ordered.filter((v, i) => ordered.findIndex((w) => w.step === v.step) === i);
  const covered = new Set(ordered.flatMap(nsOf));
  const loose = sources.filter((s) => !covered.has(s.n));
  const looseShown = loose.filter((s) => cited.has(s.n) || showAll);
  const looseRest = loose.length - looseShown.length;
  const whyOf = new Map(steps.map((s) => [s.id, s.why]));
  const toolOf = new Map(steps.map((s) => [s.id, s.tool]));

  return (
    <div className={`ab-grid ${side ? "has-side" : ""}`}>
      <section className="ab-tile ab-answer">
        <div className="ab-q">{run.question}</div>
        {status === "error" ? <p className="ax-error">{run.error}</p> : answer}
        {parts.length > 1 && status !== "error" && (
          <ol className="ab-parts">
            {parts.map((v, i) => {
              const n = nsOf(v)[0] ?? null;
              return (
                <li key={`${v.step}-${i}`} className={n !== null && hot === n ? "is-hot" : ""} {...hover(n)}>
                  <span className="ab-parts__n">{i + 1}</span>
                  <span className="ab-parts__q">{capital(whyOf.get(v.step) || viewCaption(v))}</span>
                  <span className="ab-parts__a">
                    {partSummary(v)}
                    {n !== null && cite(n)}
                  </span>
                </li>
              );
            })}
          </ol>
        )}
        <RunMeta run={run} />
      </section>

      {side && (
        <section className="ab-tile ab-mu ab-side" data-src={nsOf(side)[0]} {...hover(nsOf(side)[0] ?? null)}>
          <h3 className="ab-h">{side.types.map(titleCase).join("/")}’s matchups</h3>
          <TypeMatchups m={side} hits={side.strong_against} renderType={(t) => <Tag key={t} t={t} />} />
          {from(nsOf(side))}
        </section>
      )}

      {wide.map((v, i) => (
        <section key={`${v.step}-${v.kind}-${i}`} className={`ab-tile ab-wide ${v.kind === "type_chart" ? "ab-mu" : ""}`}>
          {v.kind === "type_chart" ? (
            <>
              <h3 className="ab-h">{v.types.map(titleCase).join("/")}’s matchups</h3>
              <TypeMatchups m={v} hits={v.strong_against} renderType={(t) => <Tag key={t} t={t} />} />
            </>
          ) : v.kind === "learners" ? (
            <LearnersTile view={v} link={linkFor(v.step)} />
          ) : v.kind === "pokemon_list" ? (
            <>
              <h3 className="ab-h">{v.title ?? `${v.cards.length} Pokémon`}</h3>
              <DexCards cards={v.cards} link={linkFor(v.step)} coverLabel={coverLabel(v.title)} />
            </>
          ) : (
            <>
              <h3 className="ab-h">
                {v.kind === "ranking"
                  ? `Top ${v.rows.length} by ${STAT_NAME[v.stat] ?? v.stat}`
                  : TOOL_TITLE[toolOf.get(v.step) ?? ""] ?? "Evidence"}
                {v.kind !== "ranking" && <span>{viewCaption(v)}</span>}
                {v.kind === "ranking" && <span>of {v.total.toLocaleString()} Pokémon</span>}
              </h3>
              <ViewBlock view={v} link={linkFor(v.step)} />
            </>
          )}
          {from(nsOf(v))}
        </section>
      ))}

      {(looseShown.length > 0 || looseRest > 0) && (
        <section className="ab-tile ab-wide ab-records">
          <h3 className="ab-h">
            Records <span>{looseShown.length ? `${looseShown.length} cited` : "none cited"}</span>
          </h3>
          {looseShown.length > 0 && (
            <div className="ax-ev__grid" data-n={Math.min(looseShown.length, 5)}>
              {looseShown.map((s, i) => (
                <SourceCard key={s.n} s={s} link={{ n: (r) => r ?? null, hot, cited, hover }} delay={i * 50} />
              ))}
            </div>
          )}
          {looseRest > 0 && (
            <button type="button" className="ab-more" onClick={() => setShowAll(true)}>
              Show {looseRest} more retrieved but not used
            </button>
          )}
        </section>
      )}
    </div>
  );
}

/** "Covers Dark" → "Hits Dark with"; several targets → each move may hit only one, so stay general. */
const coverLabel = (title: string | null) => {
  const target = title?.match(/^Covers (.+)$/)?.[1];
  return target && !/,| and /.test(target) ? `Hits ${target} with` : undefined;
};

const capital = (s: string) => (s ? s[0].toUpperCase() + s.slice(1) : s);

/** One part of a multi-part answer, in a few words or tags. */
function partSummary(v: AskView): ReactNode {
  switch (v.kind) {
    case "type_chart": {
      const weak = [...v.weak_4x, ...v.weak_2x];
      return weak.length ? weak.map((t) => <Tag key={t} t={t} />) : "No weaknesses";
    }
    case "learners":
      return (
        <>
          <b>{v.total}</b>
          {methodSplit(v)
            .map(([m, c]) => `${c} ${m === "egg" ? "egg" : `by ${METHOD_LABEL[m] ?? m}`}`)
            .join(", ")}
        </>
      );
    case "ranking":
      return v.rows[0] ? (
        <>
          <b>{v.rows[0].name}</b> {v.rows[0].value}
        </>
      ) : "—";
    case "learn_check":
      return <b className={v.ok ? "is-yes" : "is-no"}>{v.ok ? `Yes${v.how ? `, ${v.how}` : ""}` : "No"}</b>;
    case "move_list":
      return v.moves.length === 1 ? <b>{v.moves[0].name}</b> : <><b>{v.moves.length}</b> moves</>;
    case "learnset":
      return <><b>{v.groups.reduce((a, g) => a + g.moves.length, 0)}</b> moves</>;
    case "pokemon_list":
      return <><b>{v.cards.length}</b> Pokémon</>;
    default:
      return null;
  }
}

const METHOD_ORDER = ["level-up", "machine", "tutor", "egg"];
const methodSplit = (v: LearnersView) =>
  Object.entries(v.by_method).sort(([a], [b]) => (METHOD_ORDER.indexOf(a) + 1 || 9) - (METHOD_ORDER.indexOf(b) + 1 || 9));

function LearnersTile({ view, link }: { view: LearnersView; link: Linking }) {
  return (
    <>
      <div className="ab-learn__head">
        <h3 className="ab-h">
          Who learns {view.move.name}
          <span>
            {view.total} {view.scope.length ? `${view.scope.join(" ")} ` : ""}Pokémon{view.game ? ` in ${view.game}` : ""}
            {view.rows.length < view.total ? ` · strongest ${view.rows.length} shown` : ""}
          </span>
        </h3>
        <span className="ab-learn__split">
          {methodSplit(view).map(([m, c]) => (
            <span key={m}>
              <i style={{ background: METHOD_COLOR[m] ?? "var(--faint)" }} />
              {m === "egg" ? "Egg" : METHOD_LABEL[m] ?? titleCase(m)} <b>{c}</b>
            </span>
          ))}
        </span>
      </div>
      <DexCards cards={view.rows} link={link} />
    </>
  );
}

/** "by TM" → "TM", "by level-up at Lv 55" → "Level 55". */
const viaLabel = (via: string) => {
  const lv = via.match(/Lv\s*(\d+)/i);
  if (lv) return { text: `Level ${lv[1]}`, tone: "is-lv" };
  const t = via.replace(/^by\s+/i, "");
  return { text: t.length <= 3 ? t.toUpperCase() : capital(t), tone: /tm|machine/i.test(t) ? "is-tm" : "is-other" };
};

/**
 * Pokémon as the Pokédex page's cards, with how they qualify in the corner. Coverage
 * moves (if any) list under the types as "[type] Move", headed by ``coverLabel``.
 */
export function DexCards({
  cards,
  link,
  coverLabel = "Super-effective with",
}: {
  cards: PokemonCardData[];
  link: Linking;
  coverLabel?: string;
}) {
  if (!cards.length) return null;
  return (
    <div className="ab-dex">
      {cards.map((c, i) => {
        const n = link.n(c.ref);
        const art = sprite(c.pokemon_id ?? c.dex_number);
        const vals = STAT_ORDER.map((k) => ({ k, v: c.stats[k] })).filter((x): x is { k: (typeof STAT_ORDER)[number]; v: number } => x.v !== undefined);
        const hi = vals.length === 6 ? vals.reduce((a, b) => (b.v > a.v ? b : a)) : null;
        const lo = vals.length === 6 ? vals.reduce((a, b) => (b.v < a.v ? b : a)) : null;
        const via = c.via ? viaLabel(c.via) : null;
        const inner = (
          <>
            <div className="poke-card__top">
              <span>{c.dex_number ? dexLabel(c.dex_number) : ""}</span>
              {via ? (
                <span className={`ab-via ${via.tone}`}>{via.text}</span>
              ) : c.match !== null ? (
                <span className="ab-via is-other">{Math.round(c.match * 100)}% match</span>
              ) : null}
            </div>
            <div className="poke-card__art">{art && <img src={thumb(art, 160)} alt="" loading="lazy" />}</div>
            <h3 className="poke-card__name">{c.name}</h3>
            <div className="poke-card__types">
              {c.types.map((t) => (
                <Tag key={t} t={t} />
              ))}
            </div>
            {c.coverage.length > 0 && (
              <div className="ab-dex__cov">
                <span className="ab-dex__cov-lbl">{coverLabel}</span>
                {c.coverage.map((m) => (
                  <span key={m.move} className="ab-dex__cov-mv">
                    <Tag t={m.type} />
                    {m.move}
                  </span>
                ))}
              </div>
            )}
            {c.entry && <q className="ab-dex__entry">{c.entry}</q>}
            {c.total !== null && (
              <div className="poke-card__foot">
                <span>BST</span>
                {hi && lo && hi.v !== lo.v && (
                  <span className="poke-card__ext">
                    <span className="poke-card__ext-hi" title={`Highest: ${STAT_LABEL[hi.k]} ${hi.v}`}>
                      {STAT_SHORT[hi.k]} <em>{hi.v}</em>
                    </span>
                    <span className="poke-card__ext-lo" title={`Lowest: ${STAT_LABEL[lo.k]} ${lo.v}`}>
                      {STAT_SHORT[lo.k]} <em>{lo.v}</em>
                    </span>
                  </span>
                )}
                <b>{c.total}</b>
              </div>
            )}
          </>
        );
        const props = {
          className: `poke-card ab-dex__card ${n !== null && link.hot === n ? "is-hot" : ""}`,
          "data-src": n ?? undefined,
          style: { animationDelay: `${i * 40}ms` },
          ...link.hover(n),
        };
        return c.dex_number ? (
          <Link key={`${c.name}-${i}`} href={`/pokedex/${c.dex_number}`} {...props}>
            {inner}
          </Link>
        ) : (
          <div key={`${c.name}-${i}`} {...props}>
            {inner}
          </div>
        );
      })}
    </div>
  );
}

const KIND_NAME: Record<string, [string, string]> = {
  profile: ["profile", "Pokémon profiles"],
  sql_row: ["stats", "Pokémon stat lines"],
  dex_entry: ["Pokédex entry", "Pokédex entries"],
  type_chart: ["type chart", "type charts"],
  move: ["move details", "move records"],
  ability: ["ability details", "ability records"],
  item: ["item details", "item records"],
  encounters: ["encounter list", "encounter lists"],
  learners: ["learner list", "learner lists"],
  learnset: ["learnset", "learnsets"],
};

/** A record's kind, as the citation popover labels it. */
const PEEK_KIND: Record<string, string> = {
  sql_row: "Stats record",
  profile: "Profile record",
  dex_entry: "Pokédex entry",
  type_chart: "Type chart",
  move: "Move record",
  ability: "Ability record",
  item: "Item record",
  encounters: "Encounter list",
  learners: "Learner list",
  learnset: "Learnset",
};

/** One record in words: "Ho-Oh’s stats", "the Will-O-Wisp learner list", "the type chart". */
function oneName(s: AskSource, one: string): string {
  if (s.chunk_type === "type_chart") return "the type chart";
  if (s.pokemon_name && ["profile", "sql_row", "dex_entry", "learnset", "encounters"].includes(s.chunk_type))
    return `${s.pokemon_name}’s ${one}`;
  return s.source_ref ? `the ${s.source_ref} ${one}` : `the ${one}`;
}

/**
 * What a clicked citation points to, by the citation: one record in full (name, kind,
 * text), or — for a range like "2–9" — the list of records. "Show in results" scrolls
 * to where a record is drawn, when that's elsewhere. It scrolls with the page and
 * closes on Escape, an outside click, or a resize.
 */
export function SourcePeek({
  sources,
  from,
  x,
  y,
  above,
  jumps,
  onClose,
}: {
  sources: (AskSource | undefined)[];
  /** The citation that opened it (clicking it again toggles, so it isn't "outside"). */
  from: HTMLElement;
  /** Where to pin it on the page: the citation's left edge (viewport x) and its bottom
   * edge — or top edge, when ``above`` — in page coordinates. */
  x: number;
  y: number;
  above: boolean;
  /** Per source: where it's drawn in the results (null if only in the citation's own tile). */
  jumps: (Element | null)[];
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const down = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!ref.current?.contains(t) && !from.contains(t)) onClose();
    };
    const key = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("mousedown", down);
    document.addEventListener("keydown", key);
    window.addEventListener("resize", onClose);
    return () => {
      document.removeEventListener("mousedown", down);
      document.removeEventListener("keydown", key);
      window.removeEventListener("resize", onClose);
    };
  }, [from, onClose]);
  const items = sources.map((s, i) => ({ s, jump: jumps[i] ?? null })).filter((x): x is { s: AskSource; jump: Element | null } => !!x.s);
  if (!items.length) return null;

  const show = (el: Element) => {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    onClose();
  };
  const kindOf = (s: AskSource) => PEEK_KIND[s.chunk_type] ?? capital(CHUNK_LABEL[s.chunk_type] ?? s.chunk_type.replace(/_/g, " "));
  const textOf = (s: AskSource) => (s.chunk_type === "dex_entry" ? s.snippet.split(/Pokédex entry:\s*/)[1] ?? s.snippet : s.snippet);
  const nameOf = (s: AskSource) => s.pokemon_name ?? capital(s.source_ref ?? "Pokédex");
  const meta = (s: AskSource) => `${s.dex_number ? `${dexLabel(s.dex_number)} · ` : ""}${kindOf(s)}`;
  const width = items.length > 1 ? 400 : 340;
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth;
  const left = Math.max(12, Math.min(x - 16, vw - width - 12));
  // Pinned to the page (not the screen), so it scrolls with its citation and stays open.
  const place = above ? { top: y - 8, translate: "0 -100%" } : { top: y + 8 };
  const [one] = items;

  return createPortal(
    <div ref={ref} className="ab-peek" role="dialog" aria-label="Sources" style={{ left, width, ...place }} data-lenis-prevent>
      {items.length === 1 ? (
        <>
          <div className="ab-peek__head">
            {sprite(one.s.pokemon_id ?? one.s.dex_number) && <img loading="lazy" decoding="async" src={thumb(sprite(one.s.pokemon_id ?? one.s.dex_number), 160)} alt="" />}
            <span className="ab-peek__id">
              <b>{nameOf(one.s)}</b>
              <small>{meta(one.s)}</small>
            </span>
            <span className="ab-peek__n">{one.s.n}</span>
          </div>
          <p className="ab-peek__text">{textOf(one.s)}</p>
          {one.jump && (
            <button type="button" onClick={() => show(one.jump!)}>
              Show in results
            </button>
          )}
        </>
      ) : (
        <>
          <div className="ab-peek__title">
            {items.length} source records <span>— the data this answer was built from</span>
          </div>
          <ul className="ab-peek__list">
            {items.map(({ s, jump }) => (
              <li key={s.n}>
                <div className="ab-peek__head">
                  <span className="ab-peek__n">{s.n}</span>
                  {sprite(s.pokemon_id ?? s.dex_number) && <img loading="lazy" decoding="async" src={thumb(sprite(s.pokemon_id ?? s.dex_number), 160)} alt="" />}
                  <span className="ab-peek__id">
                    <b>{nameOf(s)}</b>
                    <small>{meta(s)}</small>
                  </span>
                  {jump && (
                    <button type="button" className="ab-peek__go" onClick={() => show(jump)}>
                      Show
                    </button>
                  )}
                </div>
                <p className="ab-peek__text">{textOf(s)}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>,
    document.body,
  );
}

/** Consecutive runs: [3,4,5,9] → [[3,5],[9,9]]. */
function runs(ns: number[]): [number, number][] {
  const out: [number, number][] = [];
  for (const n of [...ns].sort((a, b) => a - b)) {
    const last = out[out.length - 1];
    if (last && n === last[1] + 1) last[1] = n;
    else out.push([n, n]);
  }
  return out;
}

/** "From the Fire type chart [11]" / "From 8 Pokémon profiles [3]–[10]" under a tile. */
function From({
  sources,
  cite,
  citeRange,
}: {
  sources: AskSource[];
  cite: (n: number) => ReactNode;
  citeRange: (a: number, b: number) => ReactNode;
}) {
  if (!sources.length) return null;
  const groups = new Map<string, AskSource[]>();
  for (const s of sources) groups.set(s.chunk_type, [...(groups.get(s.chunk_type) ?? []), s]);
  const parts = [...groups.entries()].map(([kind, ss]) => {
    const [one, many] = KIND_NAME[kind] ?? [CHUNK_LABEL[kind] ?? kind.replace(/_/g, " "), `${CHUNK_LABEL[kind] ?? kind.replace(/_/g, " ")} records`];
    const label = ss.length === 1 ? oneName(ss[0], one) : `${ss.length} ${many}`;
    return (
      <span key={kind} className="ab-from__part">
        {label}
        {runs(ss.map((s) => s.n)).map(([a, b]) => (
          <span key={a} className="ab-from__cites">
            {b > a ? citeRange(a, b) : cite(a)}
          </span>
        ))}
      </span>
    );
  });
  return (
    <div className="ab-from">
      From{" "}
      {parts.map((p, i) => (
        <span key={i}>
          {i > 0 && (i === parts.length - 1 ? " and " : ", ")}
          {p}
        </span>
      ))}
    </div>
  );
}

/** How the answer was worked out: live while streaming, then one quiet line that opens the steps. */
function RunMeta({ run }: { run: AskRun }) {
  const [open, setOpen] = useState(false);
  const { steps, status, planner, cached, elapsed, usage } = run;
  const settled = status === "done" || status === "error";
  if (!settled) {
    const now = steps.find((s) => s.state === "running" || s.state === "pending");
    const label = !steps.length
      ? "Planning the lookups…"
      : now
        ? `${TOOL_LABEL[now.tool] ?? now.tool}…`
        : run.answer
          ? "Writing the answer…"
          : "Reading the evidence…";
    return (
      <div className="ab-meta is-live" aria-live="polite">
        <span className="ab-meta__dot" /> {label}
      </div>
    );
  }
  const by = cached ? "Cached" : planner === "keyword" ? "Planned by keywords" : planner === "llm" ? "Planned by the LLM" : null;
  const bits = [by, elapsed !== null && `${elapsed.toFixed(1)}s`, usage && `${usage.llm_calls} LLM call${usage.llm_calls === 1 ? "" : "s"}`].filter(Boolean);
  return (
    <div className="ab-meta">
      <div className="ab-meta__row">
        {steps.length > 0 && (
          <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
            {steps.length} lookup{steps.length === 1 ? "" : "s"} {open ? "▴" : "▾"}
          </button>
        )}
        <span>{bits.join(" · ")}</span>
      </div>
      {open && (
        <ol className="ab-steps">
          {steps.map((s) => (
            <li key={s.id} className={`is-${s.state}`}>
              <span className="ab-steps__mark">{s.state === "done" ? "✓" : s.state === "error" ? "!" : "∅"}</span>
              <span>
                <b>
                  {TOOL_LABEL[s.tool] ?? s.tool}
                  {s.replan && <em> · follow-up</em>}
                </b>
                <small>
                  {capital(s.why)}
                  {s.summary ? ` — ${s.summary}` : ""}
                  {s.ms > 0 ? ` · ${s.ms} ms` : ""}
                </small>
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
