"use client";

/* Pieces of a team's summary card, shared by the /teams list and the home tile:
   grade badge, summary line, strategy bars, type facts and the "why" of the rating. */

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { getTeam, getTeamAnalysis, getTeamStrategy, getTeamSummary, type TeamStrategy, type TeamSummary, type TeamSummaryText, thumb } from "@/lib/api";
import { typeChip } from "@/lib/pokeTypes";
import { gradeTone } from "@/lib/teamEval";
import { profileTeam, type Profile } from "@/lib/teamProfile";

export type Info = { p?: Profile | null; st?: TeamStrategy; sum?: TeamSummaryText };

/** Everything a card shows: rating + type facts, strategy axes, and the summary.
 *  Fetches only teams it hasn't loaded yet (per roster size), so callers can pass a
 *  sliding window — e.g. the home tile's current/prev/next — without refetching. */
// Last-known card data, kept across page visits so coming back to /teams (or home)
// redraws instantly instead of rebuilding from skeletons; every mount still
// refetches in the background (stale-while-revalidate).
const infoCache: Record<number, Info> = {};

export function useInfo(teams: TeamSummary[]) {
  const [info, setInfo] = useState<Record<number, Info>>(() => ({ ...infoCache }));
  const requested = useRef(new Set<string>());
  const live = useRef(true);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  useEffect(() => {
    live.current = true;
    const pending = timers.current;
    return () => {
      live.current = false;
      pending.forEach(clearTimeout);
    };
  }, []);
  const key = teams.map((t) => `${t.id}.${t.size}`).join(",");
  useEffect(() => {
    const patch = (id: number, x: Info) => {
      infoCache[id] = { ...infoCache[id], ...x };
      if (live.current) setInfo((m) => ({ ...m, [id]: { ...m[id], ...x } }));
    };
    for (const t of teams.filter((x) => x.size > 0)) {
      const k = `${t.id}.${t.size}`;
      if (requested.current.has(k)) continue; // already loaded or in flight
      requested.current.add(k);
      Promise.all([getTeam(t.id), getTeamAnalysis(t.id)])
        .then(([team, a]) => patch(t.id, { p: profileTeam(team, a) }))
        .catch(() => {
          requested.current.delete(k); // let a later render retry
          if (!infoCache[t.id]?.p) patch(t.id, { p: null }); // keep stale data over a blank card
        });
      getTeamStrategy(t.id).then((st) => patch(t.id, { st })).catch(() => {});
      // The summary is stored server-side; if a rewrite is pending, look again a
      // couple of times so the AI text swaps in without a reload (never polls forever).
      const loadSummary = (tries: number) =>
        getTeamSummary(t.id)
          .then((sum) => {
            patch(t.id, { sum });
            if (sum.pending && tries > 0) timers.current.push(setTimeout(() => loadSummary(tries - 1), 4000));
          })
          .catch(() => {});
      loadSummary(2);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return info;
}

export const Chip = ({ t, n }: { t: string; n?: string }) => (
  <span className="tl-chip" style={typeChip(t)}>
    {t}
    {n && <em>{n}</em>}
  </span>
);

export function Mini({ team }: { team: TeamSummary }) {
  return (
    <span className="tl-mini">
      {Array.from({ length: 6 }, (_, i) => team.sprites[i]).map((s, i) =>
        s ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img loading="lazy" decoding="async" key={i} src={thumb(s, 48)} alt="" />
        ) : (
          <i key={i} />
        ),
      )}
    </span>
  );
}

/** Six strategy bars: solid = on the team now, striped = with learnable moves. */
export function StrategyBars({ st }: { st: TeamStrategy }) {
  return (
    <div className="tl-bars">
      <span className="tl-legend">
        <i className="n" />
        now <i className="p" />
        with learnable moves
      </span>
      {st.axes.map((a) => (
        <span key={a.key} className="tl-bar" title={a.detail}>
          <span className="k">{a.label}</span>
          <span className="t">
            <i className="pot" style={{ width: `${a.potential}%` }} />
            <i className="now" style={{ width: `${a.now}%` }} />
          </span>
          <span className="v">
            {a.now}
            {a.potential > a.now && <em> / {a.potential}</em>}
          </span>
        </span>
      ))}
    </div>
  );
}

export function Facts({ p }: { p: Profile }) {
  const list = (xs: Profile["weakTo"]) => (
    <>
      {xs.slice(0, 5).map((w) => <Chip key={w.type} t={w.type} n={w.net > 1 ? `×${w.net}` : undefined} />)}
      {xs.length > 5 && <span className="more">+{xs.length - 5}</span>}
    </>
  );
  return (
    <dl className="tl-dl">
      <div>
        <dt>Weak to</dt>
        <dd>{p.weakTo.length ? list(p.weakTo) : <span className="ok">No weaknesses</span>}</dd>
      </div>
      <div>
        <dt>Resists</dt>
        <dd>{p.resists.length ? list(p.resists) : <span className="dim">Nothing</span>}</dd>
      </div>
      <div>
        <dt>Hits hard</dt>
        <dd>
          <b>{p.strongVs.length}</b>/18 types · core {p.coreTypes.slice(0, 2).map((t) => <Chip key={t} t={t} />)}
        </dd>
      </div>
    </dl>
  );
}

/** Why the grade is what it is: every area's grade, then the weakest areas with their fix. */
export function RatingWhy({ p }: { p: Profile }) {
  const r = p.rating;
  const gaps = r.areas.filter((x) => x.fix).sort((x, y) => x.score - y.score).slice(0, 3);
  return (
    <div className="tl-why">
      <span className="tl-grades">
        {r.areas.map((x) => (
          <span key={x.key} title={x.headline}>
            {x.label}
            <span className={`ev-grade ${gradeTone(x.grade)}`}>{x.grade}</span>
          </span>
        ))}
      </span>
      {gaps.length > 0 ? (
        <ul className="tl-gaps">
          {gaps.map((x) => (
            <li key={x.key}>
              <span className={`ev-grade ${gradeTone(x.grade)}`}>{x.grade}</span>
              <span>
                <b>{x.label}:</b> {x.headline}. <span className="fix">{x.fix}</span>
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="tl-meta">Nothing major to fix: every area is in good shape.</p>
      )}
      {r.capped && <p className="tl-cap">Overall scaled to {Math.round(r.ceiling * 6 / 100)}/6 until the team has six different Pokémon.</p>}
    </div>
  );
}

/** Compact grade: a coloured letter square plus the score; links to the full rating. */
export function GradeBadge({ p, href }: { p: Profile; href: string }) {
  return (
    <Link href={href} className={`tl-badge ${gradeTone(p.rating.grade)}`} title="Full rating">
      <b>{p.rating.grade}</b>
      <span>
        {p.rating.overall}
        <small>/100</small>
      </span>
    </Link>
  );
}

/** The stored summary (AI or rule-based), tagged with where it came from. */
export function SummaryText({ sum, fallback }: { sum?: TeamSummaryText; fallback: string }) {
  return (
    <p className="tl-sum">
      <span className={`tl-src ${sum?.source ?? "rules"}`}>{sum?.source === "ai" ? "AI" : "Auto"}</span>
      {sum?.text ?? fallback}
    </p>
  );
}
