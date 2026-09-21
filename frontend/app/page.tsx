"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Fragment, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent } from "react";
import {
  listPokemon,
  getPokemon,
  listTeams,
  getTeam,
  getPokemonMoves,
  searchMoves,
  searchAbilities,
  searchItems,
  getMoveLearners,
  listNatures,
  askQuestion,
  assetUrl,
  type MoveResult,
  type MoveLearner,
  type ItemResult,
  type NatureInfo,
} from "@/lib/api";
import type { PokemonSummary, Ability } from "@/lib/types";
import { renderAnswer } from "@/lib/answerFormat";

/* ---------------- shared data ---------------- */
const TC: Record<string, string> = {
  normal: "#a8a878", fire: "#f0803c", water: "#5aa0e6", electric: "#f4cf46", grass: "#6fc25a",
  ice: "#8fd4d4", fighting: "#d13b52", poison: "#b25ec4", ground: "#e0c068", flying: "#8aa0e6",
  psychic: "#f0619a", bug: "#9fc02f", rock: "#b8a038", ghost: "#7a5aa0", dragon: "#7a5cf0",
  dark: "#5a5366", steel: "#a8b0c0", fairy: "#f0a6d0",
};
const ORDER = ["normal","fire","water","electric","grass","ice","fighting","poison","ground","flying","psychic","bug","rock","ghost","dragon","dark","steel","fairy"];
const CH: Record<string, Record<string, number>> = {
  normal:{rock:.5,ghost:0,steel:.5}, fire:{fire:.5,water:.5,grass:2,ice:2,bug:2,rock:.5,dragon:.5,steel:2},
  water:{fire:2,water:.5,grass:.5,ground:2,rock:2,dragon:.5}, electric:{water:2,electric:.5,grass:.5,ground:0,flying:2,dragon:.5},
  grass:{fire:.5,water:2,grass:.5,poison:.5,ground:2,flying:.5,bug:.5,rock:2,dragon:.5,steel:.5},
  ice:{fire:.5,water:.5,grass:2,ice:.5,ground:2,flying:2,dragon:2,steel:.5},
  fighting:{normal:2,ice:2,poison:.5,flying:.5,psychic:.5,bug:.5,rock:2,ghost:0,dark:2,steel:2,fairy:.5},
  poison:{grass:2,poison:.5,ground:.5,rock:.5,ghost:.5,steel:0,fairy:2}, ground:{fire:2,electric:2,grass:.5,poison:2,flying:0,bug:.5,rock:2,steel:2},
  flying:{electric:.5,grass:2,fighting:2,bug:2,rock:.5,steel:.5}, psychic:{fighting:2,poison:2,psychic:.5,dark:0,steel:.5},
  bug:{fire:.5,grass:2,fighting:.5,poison:.5,flying:.5,psychic:2,ghost:.5,dark:2,steel:.5,fairy:.5}, rock:{fire:2,ice:2,fighting:.5,ground:.5,flying:2,bug:2,steel:.5},
  ghost:{normal:0,psychic:2,ghost:2,dark:.5}, dragon:{dragon:2,steel:.5,fairy:0}, dark:{fighting:.5,psychic:2,ghost:2,dark:.5,fairy:.5},
  steel:{fire:.5,water:.5,electric:.5,ice:2,rock:2,steel:.5,fairy:2}, fairy:{fire:.5,fighting:2,poison:.5,dragon:2,dark:2,steel:.5},
};
const one = (a: string, d: string) => (CH[a] && CH[a][d] !== undefined ? CH[a][d] : 1);
const eff = (a: string, ds: string[]) => ds.reduce((m, d) => m * one(a, d), 1);
const art = (dex: number) => assetUrl(`/sprites/official-artwork/${dex}.png`);
/** Detail link that preserves an alternate form (search results may be forms). */
const pokeHref = (p: PokemonSummary) =>
  p.form_id ? `/pokedex/${p.dex_number}?form=${p.form_id}` : `/pokedex/${p.dex_number}`;
const fmt = (x: number) => (x === 0 ? "0" : x === 0.25 ? "¼" : x === 0.5 ? "½" : String(x));
const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function Tag({ t }: { t: string }) {
  return <span className="lc-tt" style={{ background: TC[t] }}>{t}</span>;
}

/* ---------------- global search ---------------- */
/* Arrow-key navigation for suggestion dropdowns: ↑/↓ move the highlight,
   Enter chooses it, Escape clears it. Attach onKeyDown to the input,
   listRef to the results container, and itemProps(idx) to each row. */
function useKeyNav<T>(items: T[], onChoose: (item: T) => void) {
  const [active, setActive] = useState(-1);
  const [seen, setSeen] = useState(items);
  const listRef = useRef<HTMLDivElement>(null);
  // Reset the highlight whenever the result set changes (render-time reset).
  if (items !== seen) { setSeen(items); setActive(-1); }
  // Keep the highlighted row in view when navigating a long list.
  useEffect(() => {
    listRef.current?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: "nearest" });
  }, [active]);
  const onKeyDown = (e: ReactKeyboardEvent) => {
    if (!items.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((i) => (i + 1) % items.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((i) => (i <= 0 ? items.length - 1 : i - 1)); }
    else if (e.key === "Enter" && active >= 0 && active < items.length) { e.preventDefault(); onChoose(items[active]); }
    else if (e.key === "Escape") { setActive(-1); }
  };
  const itemProps = (idx: number) => ({
    "aria-selected": idx === active,
    onMouseMove: () => setActive(idx),
  });
  return { active, listRef, onKeyDown, itemProps };
}

function Search() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [res, setRes] = useState<PokemonSummary[]>([]);
  useEffect(() => {
    const query = q.trim();
    const id = setTimeout(() => {
      if (query.length < 2) { setRes([]); return; }
      listPokemon({ q: query, limit: 6 }).then((r) => setRes(r.items)).catch(() => setRes([]));
    }, 180);
    return () => clearTimeout(id);
  }, [q]);
  const choose = (p: PokemonSummary) => { setRes([]); router.push(pokeHref(p)); };
  const { listRef, onKeyDown, itemProps } = useKeyNav(res, choose);
  return (
    <div className="lc-search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
      <input
        placeholder="Search any of 1,025 species…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={onKeyDown}
        aria-autocomplete="list"
      />
      {res.length > 0 && (
        <div className="ac" role="listbox" ref={listRef}>
          {res.map((p, idx) => (
            <Link key={p.id} href={pokeHref(p)} onClick={() => setRes([])} role="option" {...itemProps(idx)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={assetUrl(p.sprite_url)} alt={p.name} />
              <span style={{ flex: 1, fontWeight: 600 }}>{p.name}</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--dim)" }}>Nº{String(p.dex_number).padStart(4, "0")}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------------- Ask ---------------- */
const ASK_QS = [
  "Which non-legendary has the highest Attack?",
  "Fastest Fire-type?",
  "Tell me about Mewtwo.",
];
const ROUTE_COLOR: Record<string, string> = {
  sql: "var(--blue)", semantic: "var(--violet)", hybrid: "var(--violet)",
  matchup: "var(--red)", personalized: "var(--ok)",
};
type AskState = { route: string; answer: string; srcs: { n: number; ref: string }[] } | { error: true };
function AskTile() {
  // Cost note: the assistant is a paid LLM call, so we NEVER auto-fetch or
  // rotate. A question only hits the API when the user explicitly clicks it,
  // and answers are cached per session.
  const [i, setI] = useState<number | null>(null);
  const [state, setState] = useState<AskState | null>(null);
  const [loading, setLoading] = useState(false);
  const cache = useRef<Record<string, AskState>>({});

  useEffect(() => {
    if (i === null) return;
    const q = ASK_QS[i];
    let alive = true;
    (async () => {
      if (cache.current[q]) { if (alive) setState(cache.current[q]); return; }
      if (alive) { setState(null); setLoading(true); }
      try {
        const r = await askQuestion(q);
        const st: AskState = {
          route: (r.route ?? "rag").toLowerCase(),
          answer: r.answer,
          srcs: r.sources.slice(0, 3).map((s) => ({
            n: s.n, ref: s.pokemon_name ?? s.source_ref ?? s.chunk_type,
          })),
        };
        cache.current[q] = st;
        if (alive) setState(st);
      } catch {
        if (alive) setState({ error: true });
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [i]);

  const ok = state && !("error" in state);
  const routeLabel = ok ? state.route.toUpperCase() : "RAG";
  const routeColor = ok ? (ROUTE_COLOR[state.route] ?? "var(--dim)") : "var(--dim)";
  // Preview: first few complete bullets/lines (cut at content boundaries, never
  // mid-line), plus deduped source names — the full answer lives in /ask.
  let preview = "", more = false;
  let srcs: { n: number; ref: string }[] = [];
  if (ok) {
    const lines = state.answer.split("\n").map((l) => l.trim()).filter(Boolean);
    preview = lines.slice(0, 3).join("\n");
    more = lines.length > 3;
    const seen = new Set<string>();
    srcs = state.srcs.filter((s) => (seen.has(s.ref) ? false : seen.add(s.ref))).slice(0, 3);
  }
  return (
    <section className="card">
      <div className="lbl">Ask the Pokédex · RAG<span className="lc-route" style={{ background: routeColor, opacity: ok ? 1 : 0.3 }}>{routeLabel}</span></div>
      <div className="lc-qchips">
        {ASK_QS.map((q, k) => <button key={k} className={k === i ? "on" : ""} onClick={() => setI(k)}>{q}</button>)}
      </div>
      <div className="lc-qbox">{i === null ? "Tap a question to ask the live assistant…" : ASK_QS[i]}</div>
      <div className="lc-ansbox">
        {i === null && <div className="lc-ans" style={{ color: "var(--dim)" }}>Answers use the live model, so they run only when you ask. Pick a question above, or open the full assistant.</div>}
        {loading && <div className="lc-ans" style={{ color: "var(--dim)" }}>Retrieving &amp; answering…</div>}
        {!loading && state && "error" in state && (
          <div className="lc-ans" style={{ color: "var(--dim)" }}>Assistant unavailable right now — open it to try live.</div>
        )}
        {!loading && ok && <>
          <div className="lc-ans">{renderAnswer(preview)}{more && <span className="lc-ansmore">…more in the assistant →</span>}</div>
          <div className="lc-srcs">{srcs.map((s) => <div className="lc-src" key={s.n}><span className="n">{s.n}</span> {s.ref}</div>)}</div>
        </>}
      </div>
      <Link className="go" href="/ask">Open the assistant →</Link>
    </section>
  );
}

/* ---------------- Team builder & coach ---------------- */
type Mon = { name: string; dex: number; types: string[] };
const EXAMPLE_TEAM: Mon[] = [
  { name: "Charizard", dex: 6, types: ["fire", "flying"] }, { name: "Garchomp", dex: 445, types: ["dragon", "ground"] },
  { name: "Tyranitar", dex: 248, types: ["rock", "dark"] }, { name: "Metagross", dex: 376, types: ["steel", "psychic"] },
  { name: "Greninja", dex: 658, types: ["water", "dark"] }, { name: "Gardevoir", dex: 282, types: ["fairy", "psychic"] },
];
const RADAR_TYPES: [string, string][] = [
  ["Fire", "fire"], ["Water", "water"], ["Grass", "grass"], ["Elec", "electric"],
  ["Ice", "ice"], ["Ground", "ground"], ["Fairy", "fairy"], ["Fight", "fighting"],
];
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const FIX: Record<string, [string, string]> = {
  fairy: ["a Steel or Poison-type", "Heatran"], ground: ["a Flying / Levitate pick", "Rotom-Wash"],
  ice: ["a Steel or Fire-type", "Heatran"], fighting: ["a Ghost-type", "Aegislash"],
  water: ["a Grass or Water resist", "Ferrothorn"], electric: ["a Ground-type", "Excadrill"],
  psychic: ["a Dark-type", "Tyranitar"], dragon: ["a Fairy-type", "Clefable"],
};
function TeamCoachTile() {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [team, setTeam] = useState<Mon[]>(EXAMPLE_TEAM);
  const [teamName, setTeamName] = useState("example team");
  const [q, setQ] = useState("");
  const [res, setRes] = useState<PokemonSummary[]>([]);
  const [addOpen, setAddOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { teams } = await listTeams("player");
        if (!teams.length) return;
        const full = await getTeam(teams[0].id);
        const mons = full.members
          .filter((m) => m.pokemon_id)
          .map((m) => ({ name: m.name, dex: m.dex_number, types: m.types }));
        if (alive && mons.length) { setTeam(mons); setTeamName(full.name); }
      } catch { /* keep example fallback */ }
    })();
    return () => { alive = false; };
  }, []);

  // add-a-member search suggestions
  useEffect(() => {
    const query = q.trim();
    const id = setTimeout(() => {
      if (query.length < 2) { setRes([]); return; }
      listPokemon({ q: query, limit: 20 }).then((r) => setRes(r.items)).catch(() => setRes([]));
    }, 180);
    return () => clearTimeout(id);
  }, [q]);

  const addMon = (p: PokemonSummary) => {
    setTeam((t) => (t.length >= 6 || t.some((m) => m.dex === p.dex_number)
      ? t : [...t, { name: p.name, dex: p.dex_number, types: p.types }]));
    setTeamName("your draft"); setQ(""); setRes([]); setAddOpen(false);
  };
  const removeMon = (dex: number) => { setTeam((t) => t.filter((m) => m.dex !== dex)); setTeamName("your draft"); };
  const { listRef: addListRef, onKeyDown: addKeyDown, itemProps: addItemProps } = useKeyNav(res, addMon);

  // Add-Pokémon modal: Escape to close, lock page (Lenis) scroll while open.
  useEffect(() => {
    if (!addOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setAddOpen(false); };
    window.addEventListener("keydown", onKey);
    const root = document.documentElement;
    const pb = document.body.style.overflow, pr = root.style.overflow;
    document.body.style.overflow = "hidden"; root.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = pb; root.style.overflow = pr; };
  }, [addOpen]);

  const size = team.length;
  // shared weaknesses (computed from real member types)
  const tally: Record<string, number> = {};
  ORDER.forEach((a) => { let c = 0; team.forEach((m) => { if (eff(a, m.types) > 1) c++; }); if (c) tally[a] = c; });
  const top = Object.entries(tally).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const fx = FIX[top[0]?.[0]] || ["a defensive pivot", "a bulky resist"];
  // radar: per-type average defensive exposure across the team (2× avg = full)
  const radVals = RADAR_TYPES.map(([, t]) =>
    size ? clamp(team.reduce((s, m) => s + eff(t, m.types), 0) / size / 2, 0.08, 1) : 0.1);
  const radKey = radVals.join(",");

  useEffect(() => {
    const svg = svgRef.current, wrap = wrapRef.current;
    if (!svg || !wrap) return;
    const cx = 75, cy = 75, R = 54;
    const pt = (i: number, v: number) => { const a = (-90 + i * (360 / RADAR_TYPES.length)) * Math.PI / 180; return [cx + Math.cos(a) * R * v, cy + Math.sin(a) * R * v]; };
    let h = "";
    [.25, .5, .75, 1].forEach((g) => { h += `<polygon class="g2" points="${RADAR_TYPES.map((_, i) => pt(i, g).join(",")).join(" ")}"/>`; });
    RADAR_TYPES.forEach((_, i) => { const [ex, ey] = pt(i, 1); h += `<line class="ax" x1="${cx}" y1="${cy}" x2="${ex}" y2="${ey}"/>`; });
    RADAR_TYPES.forEach((a, i) => { const [lx, ly] = pt(i, 1.16); h += `<text class="lab" x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle">${a[0]}</text>`; });
    h += `<polygon class="sh" id="sh" points="${radVals.map((v, i) => pt(i, v).join(",")).join(" ")}"/>`;
    radVals.forEach((v, i) => { const [dx, dy] = pt(i, v); h += `<circle class="dot" cx="${dx}" cy="${dy}" r="2.6"/>`; });
    svg.innerHTML = h;
    const sh = svg.querySelector("#sh") as SVGPolygonElement | null;
    if (!sh) return;
    const len = sh.getTotalLength ? sh.getTotalLength() : 300;
    sh.style.strokeDasharray = String(len); sh.style.strokeDashoffset = String(len);
    const draw = () => { sh.style.strokeDashoffset = "0"; svg.querySelectorAll(".dot").forEach((d, i) => setTimeout(() => d.classList.add("show"), reduced() ? 0 : 600 + i * 60)); };
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { if (reduced()) draw(); else setTimeout(draw, 200); io.disconnect(); } }), { threshold: 0.3 });
    io.observe(wrap);
    // weakness bars
    wrap.querySelectorAll<HTMLElement>(".wb i").forEach((el) => requestAnimationFrame(() => (el.style.width = el.dataset.w + "%")));
    return () => io.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [radKey]);

  return (
    <section className="card" ref={wrapRef as React.RefObject<HTMLDivElement>}>
      <div className="lbl">Team builder &amp; coach<span className="mono">{teamName}</span></div>
      <div className="lc-team">
        {team.map((m) => (
          <div className="s" key={m.dex} title={m.name}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={art(m.dex)} alt={m.name} />
            <button className="rm" onClick={() => removeMon(m.dex)} aria-label={`Remove ${m.name}`}>×</button>
          </div>
        ))}
        {Array.from({ length: Math.max(0, 6 - size) }).map((_, k) => (
          <button className="s e" key={"e" + k} onClick={() => { setQ(""); setRes([]); setAddOpen(true); }} aria-label="Add a Pokémon">+</button>
        ))}
      </div>
      <div className="lc-coachbody">
        <svg className="lc-radar" viewBox="0 0 150 150" ref={svgRef} />
        <div className="lc-wk">
          {top.length ? top.map(([t, c]) => (
            <div className="lc-wkrow" key={t}>
              <span className="wt" style={{ background: TC[t] }}>{t}</span>
              <span className="wb"><i data-w={String((c / size) * 100)} /></span>
              <span className="c">{c}/{size}</span>
            </div>
          )) : <div className="lc-wkrow" style={{ color: "var(--ok)", fontWeight: 600 }}>No shared weaknesses ✓</div>}
        </div>
      </div>
      <div className="lc-fix">
        {top.length
          ? <>Most exposed to <b>{top[0][0]}</b> ({top[0][1]}/{size}). Fix: draft <b>{fx[0]}</b> — e.g. <b>{fx[1]}</b>.</>
          : <>Balanced defensively across {size} {size === 1 ? "member" : "members"} — coverage looks solid.</>}
      </div>
      <Link className="go" href="/teams">Open team builder →</Link>
      {addOpen && (
        <div className="lc-modal lc-modal-add" onClick={() => setAddOpen(false)} role="dialog" aria-modal="true" data-lenis-prevent>
          <div className="lc-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="lc-modal-head">
              <b>Add a Pokémon</b>
              <span className="sub">slot {size + 1} of 6</span>
              <button className="x" onClick={() => setAddOpen(false)} aria-label="Close">×</button>
            </div>
            <div className="lc-addbody" data-lenis-prevent>
              {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
              <input autoFocus className="lc-addsearch" placeholder="Search any species — e.g. Ferrothorn…" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={addKeyDown} aria-autocomplete="list" />
              <div className="lc-addresults" role="listbox" ref={addListRef}>
                {res.map((p, idx) => {
                  const inTeam = team.some((m) => m.dex === p.dex_number);
                  return (
                    <button key={p.id} className="row" role="option" {...addItemProps(idx)} disabled={inTeam} onClick={() => addMon(p)}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={art(p.dex_number)} alt={p.name} />
                      <span className="nm">{p.name}</span>
                      <span className="tps">{p.types.map((t) => <Tag key={t} t={t} />)}</span>
                      {inTeam && <span className="added">on team</span>}
                    </button>
                  );
                })}
                {q.trim().length >= 2 && res.length === 0 && <div className="hint">No species match “{q.trim()}”.</div>}
                {q.trim().length < 2 && <div className="hint">Type at least 2 letters to search.</div>}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

/* ---------------- Type calculator (defends as 1 or 2 types) ---------------- */
function TypeCalcTile() {
  const [sel, setSel] = useState<string[]>(["fire"]);
  const toggle = (o: string) =>
    setSel((s) => (s.includes(o) ? s.filter((x) => x !== o) : s.length < 2 ? [...s, o] : [s[1], o]));
  // Defensive: combined multiplier of an attacking type vs the selected typing.
  const weak = ORDER.map((a) => ({ t: a, m: eff(a, sel) })).filter((x) => x.m > 1).sort((a, b) => b.m - a.m);
  const res = ORDER.map((a) => ({ t: a, m: eff(a, sel) })).filter((x) => x.m < 1).sort((a, b) => a.m - b.m);
  // Offensive: types the selected type(s) hit super-effectively (best STAB).
  const hits = ORDER.filter((d) => sel.length > 0 && Math.max(...sel.map((s) => one(s, d))) >= 2);
  const dash = <span style={{ color: "var(--dim)", fontSize: 12 }}>—</span>;
  // Group {t,m}[] into sub-rows by multiplier, in the given multiplier order.
  const grouped = (items: { t: string; m: number }[], order: number[]) => {
    const by: Record<number, string[]> = {};
    items.forEach((x) => (by[x.m] = by[x.m] ? [...by[x.m], x.t] : [x.t]));
    return order.filter((m) => by[m]?.length).map((m) => ({ m, types: by[m] }));
  };
  const mxClass = (m: number) => (m === 0 ? "im" : m > 1 ? "wk" : "rs");
  const groupRow = (label: string, groups: { m: number; types: string[] }[]) => (
    <div className="lc-tcline g">
      <span className="h">{label}</span>
      {groups.length ? (
        <div className="lc-tcgroups">
          {groups.map((g) => (
            <div className="lc-tcgrp" key={g.m}>
              <span className={`lc-tcmx ${mxClass(g.m)}`}>×{fmt(g.m)}</span>
              <span className="lc-tcset">{g.types.map((t) => <Tag key={t} t={t} />)}</span>
            </div>
          ))}
        </div>
      ) : dash}
    </div>
  );
  return (
    <section className="card">
      <div className="lbl">Type calculator<span className="mono">defends as 1–2 types</span></div>
      <div className="lc-tg">
        {ORDER.map((o) => <button key={o} onClick={() => toggle(o)} className={sel.includes(o) ? "on" : ""} style={{ "--c": TC[o] } as CSSProperties}>{o}</button>)}
      </div>
      {groupRow("Weak to", grouped(weak, [4, 2]))}
      {groupRow("Resists", grouped(res, [0, 0.25, 0.5]))}
      <div className="lc-tcline"><span className="h">Hits ×2</span><span className="lc-tcset">{hits.length ? hits.map((t) => <Tag key={t} t={t} />) : dash}</span></div>
    </section>
  );
}

/* ---------------- Combined lookup: moves + abilities + items ---------------- */
type Entry = {
  key: string; name: string; kind: "Move" | "Ability" | "Item"; type?: string | null;
  cat?: string | null; power?: number | null; acc?: number | null; pp?: number | null;
  cost?: number | null; effect?: string | null;
};
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const moveToEntry = (m: MoveResult): Entry => ({
  key: "m" + m.id, name: m.name, kind: "Move", type: m.type,
  cat: m.damage_class ? cap(m.damage_class) : null, power: m.power, acc: m.accuracy, pp: m.pp,
  effect: m.short_effect,
});
const abilityToEntry = (a: Ability): Entry => ({ key: "a" + a.id, name: a.name, kind: "Ability", effect: a.effect });
const itemToEntry = (i: ItemResult): Entry => ({
  key: "i" + i.id, name: i.name, kind: "Item", cat: i.category, cost: i.cost, effect: i.short_effect,
});
const KIND_BG: Record<string, string> = { Ability: "var(--ink)", Item: "#4a4a55" };
function LookupTile() {
  const [q, setQ] = useState("");
  const [list, setList] = useState<Entry[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [learners, setLearners] = useState<MoveLearner[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [learnerQ, setLearnerQ] = useState("");

  useEffect(() => {
    const query = q.trim();
    let alive = true;
    const id = setTimeout(async () => {
      setLoading(true);
      try {
        const [moves, abilities, items] = await Promise.all([
          searchMoves(query, 3),
          searchAbilities(query, 1),
          searchItems(query, 2),
        ]);
        if (!alive) return;
        const merged = [
          ...moves.map(moveToEntry),
          ...abilities.map(abilityToEntry),
          ...items.map(itemToEntry),
        ].slice(0, 5);
        setList(merged);
        setSel((cur) => (cur && merged.some((e) => e.key === cur) ? cur : merged[0]?.key ?? null));
      } catch {
        if (alive) setList([]);
      } finally {
        if (alive) setLoading(false);
      }
    }, 200);
    return () => { alive = false; clearTimeout(id); };
  }, [q]);

  const detail = list.find((e) => e.key === sel) || list[0];
  const { listRef: moveListRef, onKeyDown: moveKeyDown, itemProps: moveItemProps } = useKeyNav(list, (e: Entry) => setSel(e.key));

  // When a move is selected, pull the species that can learn it (reverse learnset).
  useEffect(() => {
    let alive = true;
    setModalOpen(false);
    if (detail && detail.kind === "Move") {
      const moveId = Number(detail.key.slice(1));
      getMoveLearners(moveId, 250).then((ls) => { if (alive) setLearners(ls); }).catch(() => { if (alive) setLearners([]); });
    } else setLearners([]);
    return () => { alive = false; };
  }, [detail?.key, detail?.kind]);

  // While the modal is open: close on Escape and lock the page (Lenis) scroll.
  useEffect(() => {
    if (!modalOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setModalOpen(false); };
    window.addEventListener("keydown", onKey);
    const root = document.documentElement;
    const prevBody = document.body.style.overflow;
    const prevRoot = root.style.overflow;
    document.body.style.overflow = "hidden";
    root.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevBody;
      root.style.overflow = prevRoot;
    };
  }, [modalOpen]);

  const dash = (v: number | null | undefined) => (v == null ? "—" : String(v));
  const badge = (e: Entry) =>
    e.type ? <Tag t={e.type} /> : <span className="lc-tt" style={{ background: KIND_BG[e.kind] }}>{e.kind}</span>;
  return (
    <section className="card lc-look">
      <div className="lbl">Move · ability · item lookup<span className="mono">3,000+ entries</span></div>
      <input placeholder="e.g. Earthquake, Levitate, Leftovers…" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={moveKeyDown} aria-autocomplete="list" />
      <div className="lc-moveres" role="listbox" ref={moveListRef}>
        {list.map((e, idx) => (
          <div className={`lc-moverow${e.key === detail?.key ? " on" : ""}`} key={e.key} role="option" {...moveItemProps(idx)} onClick={() => setSel(e.key)}>
            {badge(e)}
            <span className="nm">{e.name}</span>
            <span className="pw">{e.kind === "Move" ? `${e.cat ?? "—"} · ${dash(e.power)}` : e.kind === "Item" ? (e.cat ?? "Item") : "Ability"}</span>
          </div>
        ))}
        {!loading && list.length === 0 && <div className="sub">No match — try “Ice Beam”, “Intimidate”, “Leftovers”.</div>}
        {loading && list.length === 0 && <div className="sub">Searching…</div>}
      </div>
      {detail && (
        <div className="lc-movedet">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            {badge(detail)}
            <b>{detail.name}</b>
          </div>
          {detail.kind === "Move" && <>
            <div className="lc-kv"><span className="k">Category</span><span>{detail.cat ?? "—"}</span></div>
            <div className="lc-kv"><span className="k">Power / Acc / PP</span><span>{dash(detail.power)} / {dash(detail.acc)} / {dash(detail.pp)}</span></div>
          </>}
          {detail.kind === "Item" && <>
            <div className="lc-kv"><span className="k">Category</span><span>{detail.cat ?? "—"}</span></div>
            <div className="lc-kv"><span className="k">Cost</span><span>{detail.cost ? `₽${detail.cost.toLocaleString()}` : "—"}</span></div>
          </>}
          <div style={{ color: "var(--dim)", marginTop: 8, fontSize: 12.5, lineHeight: 1.5 }}>{detail.effect || "No description on file."}</div>
          {detail.kind === "Move" && learners.length > 0 && (
            <div className="lc-lklearn">
              <div className="h">
                Learned by <b>{learners.length}{learners.length >= 250 ? "+" : ""}</b> species
                {learners.length > 18 && <button className="tog" onClick={() => { setLearnerQ(""); setModalOpen(true); }}>show all</button>}
              </div>
              <div className="row">
                {learners.slice(0, 18).map((p) => (
                  <Link key={p.id} href={`/pokedex/${p.dex_number}`} title={p.name} className="s">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={art(p.dex_number)} alt={p.name} />
                  </Link>
                ))}
                {learners.length > 18 && <button className="more" onClick={() => { setLearnerQ(""); setModalOpen(true); }}>+{learners.length - 18}</button>}
              </div>
            </div>
          )}
        </div>
      )}
      {modalOpen && detail && (
        <div className="lc-modal" onClick={() => setModalOpen(false)} role="dialog" aria-modal="true" data-lenis-prevent>
          <div className="lc-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="lc-modal-head">
              {badge(detail)}
              <b>{detail.name}</b>
              <span className="sub">{learners.length}{learners.length >= 250 ? "+" : ""} species can learn it</span>
              <button className="x" onClick={() => setModalOpen(false)} aria-label="Close">×</button>
            </div>
            <div className="lc-modal-sub">
              {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
              <input autoFocus placeholder="Filter these species…" value={learnerQ} onChange={(e) => setLearnerQ(e.target.value)} />
            </div>
            {(() => {
              const f = learnerQ.trim().toLowerCase();
              const shown = f ? learners.filter((p) => p.name.toLowerCase().includes(f)) : learners;
              return (
                <div className="lc-modal-grid" data-lenis-prevent>
                  {shown.map((p) => (
                    <Link key={p.id} href={`/pokedex/${p.dex_number}`} title={p.name} onClick={() => setModalOpen(false)}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={art(p.dex_number)} alt={p.name} />
                      <span>{p.name}</span>
                    </Link>
                  ))}
                  {shown.length === 0 && <div className="lc-modal-empty">No species match “{learnerQ.trim()}”.</div>}
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </section>
  );
}

/* ---------------- Nature helper ---------------- */
const NAT: [string, string | null, string | null][] = [
  ["Hardy",null,null],["Lonely","Atk","Def"],["Brave","Atk","Spe"],["Adamant","Atk","SpA"],["Naughty","Atk","SpD"],
  ["Bold","Def","Atk"],["Docile",null,null],["Relaxed","Def","Spe"],["Impish","Def","SpA"],["Lax","Def","SpD"],
  ["Timid","Spe","Atk"],["Hasty","Spe","Def"],["Serious",null,null],["Jolly","Spe","SpA"],["Naive","Spe","SpD"],
  ["Modest","SpA","Atk"],["Mild","SpA","Def"],["Quiet","SpA","Spe"],["Bashful",null,null],["Rash","SpA","SpD"],
  ["Calm","SpD","Atk"],["Gentle","SpD","Def"],["Sassy","SpD","Spe"],["Careful","SpD","SpA"],["Quirky",null,null],
];
const STATS = ["Atk", "Def", "SpA", "SpD", "Spe"];
const DIAG = ["Hardy", "Docile", "Bashful", "Quirky", "Serious"]; // neutral on the diagonal, by stat index
const STAT_LABEL: Record<string, string> = { attack: "Atk", defense: "Def", sp_attack: "SpA", sp_defense: "SpD", speed: "Spe" };
// Fallback PAIR/UPDN from the built-in table (used until /api/natures resolves).
const FALLBACK_PAIR: Record<string, string> = {};
const FALLBACK_UPDN: Record<string, [string | null, string | null]> = {};
NAT.forEach(([n, up, dn]) => { FALLBACK_UPDN[n] = [up, dn]; if (up && dn) FALLBACK_PAIR[up + "|" + dn] = n; });
function NatureTile() {
  const [sel, setSel] = useState("Adamant");
  const [pair, setPair] = useState<Record<string, string>>(FALLBACK_PAIR);
  const [updn, setUpdn] = useState<Record<string, [string | null, string | null]>>(FALLBACK_UPDN);

  useEffect(() => {
    let alive = true;
    listNatures().then((rows: NatureInfo[]) => {
      const p: Record<string, string> = {};
      const u: Record<string, [string | null, string | null]> = {};
      rows.forEach((n) => {
        const up = n.increased_stat ? STAT_LABEL[n.increased_stat] ?? null : null;
        const dn = n.decreased_stat ? STAT_LABEL[n.decreased_stat] ?? null : null;
        u[n.name] = [up, dn];
        if (up && dn) p[up + "|" + dn] = n.name;
      });
      if (alive && Object.keys(p).length) { setPair(p); setUpdn(u); }
    }).catch(() => { /* keep fallback */ });
    return () => { alive = false; };
  }, []);

  const cur = updn[sel] ?? [null, null];
  return (
    <section className="card">
      <div className="lbl">Nature helper<span className="mono">tap to inspect</span></div>
      <div className="lc-natmx">
        <div className="corner">+/−</div>
        {STATS.map((s) => <div key={"h" + s} className="hc dn">−{s}</div>)}
        {STATS.map((up, r) => (
          <Fragment key={"r" + up}>
            <div className="hc up">+{up}</div>
            {STATS.map((dn, c) => {
              const name = r === c ? DIAG[r] : pair[up + "|" + dn];
              return <div key={dn} className={`cell${r === c ? " diag" : ""}${name === sel ? " on" : ""}`} onClick={() => name && setSel(name)} title={name}>{name}</div>;
            })}
          </Fragment>
        ))}
      </div>
      <div className="lc-natnote">
        {cur[0] ? <><b>{sel}</b> — <span style={{ color: "var(--ok)" }}>+{cur[0]}</span> / <span style={{ color: "var(--red)" }}>−{cur[1]}</span> (±10%)</> : <><b>{sel}</b> — neutral, no stat changes</>}
      </div>
    </section>
  );
}

/* ---------------- Damage calculator ---------------- */
type Stats = import("@/lib/types").Stats;
type CalcMon = { id: number; name: string; dex: number; types: string[]; stats: Stats };
type CalcMove = { name: string; type: string; damage_class: string; power: number };
type SKey = "hp" | "atk" | "def" | "spa" | "spd" | "spe";
type EVs = Record<SKey, number>;
const ZERO_EV: EVs = { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 };
const SABBR: Record<SKey, string> = { hp: "HP", atk: "Atk", def: "Def", spa: "SpA", spd: "SpD", spe: "Spe" };
const natMul = (name: string, key: SKey): number => {
  const r = NAT.find((x) => x[0] === name); if (!r || key === "hp") return 1;
  return r[1] === SABBR[key] ? 1.1 : r[2] === SABBR[key] ? 0.9 : 1;
};
const statFull = (base: number, level: number, iv: number, ev: number, nm: number, isHP: boolean) => {
  const core = Math.floor((2 * base + iv + Math.floor(ev / 4)) * level / 100);
  return isHP ? core + level + 10 : Math.floor((core + 5) * nm);
};
// Curated damage-relevant items & abilities (name → effect flags).
const DC_ITEMS = ["None", "Choice Band", "Choice Specs", "Life Orb", "Expert Belt", "Muscle Band", "Wise Glasses"];
const DC_ITEMS_D = ["None", "Assault Vest", "Eviolite"];
const DC_ABIL = ["None", "Adaptability", "Huge Power", "Technician", "Guts", "Tinted Lens"];
const DC_ABIL_D = ["None", "Thick Fat", "Multiscale", "Solid Rock", "Filter"];
const WEATHER = ["None", "Rain", "Sun"];
const TERRAIN = ["None", "Electric", "Grassy", "Psychic"];
const ALL_IV: EVs = { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 };
const EV_COLOR: Record<SKey, string> = { hp: "#5DCAA5", atk: "#E24B4A", def: "#85B7EB", spa: "#EF9F27", spd: "#B25EC4", spe: "#F0619A" };
type Spread = { nat: string; ev: EVs; iv: EVs };
const offensiveSet = (mon: CalcMon | null): Spread => {
  const phys = !mon || mon.stats.attack >= mon.stats.sp_attack;
  return phys
    ? { nat: "Adamant", ev: { ...ZERO_EV, atk: 252, spe: 252, hp: 4 }, iv: { ...ALL_IV } }
    : { nat: "Modest", ev: { ...ZERO_EV, spa: 252, spe: 252, hp: 4 }, iv: { ...ALL_IV, atk: 0 } };
};
const BULKY_SET: Spread = { nat: "Bold", ev: { ...ZERO_EV, hp: 252, def: 252, spd: 4 }, iv: { ...ALL_IV } };
async function loadCalcMon(id: number): Promise<CalcMon> {
  const d = await getPokemon(id);
  return { id: d.id, name: d.name, dex: d.dex_number, types: d.types, stats: d.stats };
}
function DcPicker({ mon, onPick, ph }: { mon: CalcMon | null; onPick: (id: number) => void; ph: string }) {
  const [q, setQ] = useState(""); const [res, setRes] = useState<PokemonSummary[]>([]); const [open, setOpen] = useState(false);
  useEffect(() => {
    const query = q.trim();
    const id = setTimeout(() => {
      if (query.length < 2) { setRes([]); return; }
      listPokemon({ q: query, limit: 6 }).then((r) => setRes(r.items)).catch(() => setRes([]));
    }, 180);
    return () => clearTimeout(id);
  }, [q]);
  return (
    <div className="dc-pill">
      {mon && <img src={art(mon.dex)} alt={mon.name} />/* eslint-disable-line @next/next/no-img-element */}
      <input placeholder={ph} value={q} onChange={(e) => setQ(e.target.value)} onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)} />
      {open && res.length > 0 && (
        <div className="ac">
          {res.map((p) => (
            <button key={p.id} onMouseDown={() => { onPick(p.id); setQ(""); setRes([]); }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={art(p.dex_number)} alt={p.name} />
              <span style={{ flex: 1, fontWeight: 600 }}>{p.name}</span>
              <span className="tps">{p.types.map((t) => <Tag key={t} t={t} />)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
const EV_KEYS: SKey[] = ["hp", "atk", "def", "spa", "spd", "spe"];
function EvBar({ ev }: { ev: EVs }) {
  const total = EV_KEYS.reduce((s, k) => s + ev[k], 0) || 1;
  return (
    <div className="dc-evbar">
      {EV_KEYS.map((k) => ev[k] > 0 && <i key={k} style={{ width: `${ev[k] / total * 100}%`, background: EV_COLOR[k] }} title={`${SABBR[k]} ${ev[k]}`} />)}
    </div>
  );
}
function EvEditor({ ev, iv, onEv, onIv }: { ev: EVs; iv: EVs; onEv: (e: EVs) => void; onIv: (i: EVs) => void }) {
  const total = EV_KEYS.reduce((s, k) => s + ev[k], 0);
  return (
    <div className="dc-eved">
      {EV_KEYS.map((k) => (
        <div className="dc-evline" key={k}>
          <span className="k">{SABBR[k]}</span>
          <input type="range" min={0} max={252} step={4} value={ev[k]} onChange={(e) => onEv({ ...ev, [k]: Number(e.target.value) })} style={{ accentColor: EV_COLOR[k] }} />
          <span className="v">{ev[k]}</span>
          <input className="iv" type="number" min={0} max={31} value={iv[k]} onChange={(e) => onIv({ ...iv, [k]: Math.max(0, Math.min(31, Number(e.target.value) || 0)) })} />
        </div>
      ))}
      <div className="dc-evfoot">
        <span className={total > 510 ? "over" : ""}>EVs {total} / 510</span>
        <span className="ivq">IV:
          <button onClick={() => onIv({ ...ALL_IV })}>31</button>
          <button onClick={() => onIv({ ...iv, atk: 0 })}>0 Atk</button>
          <button onClick={() => onIv({ ...iv, spe: 0 })}>0 Spe</button>
        </span>
      </div>
    </div>
  );
}
function DamageCalcTile() {
  const [level, setLevel] = useState(100);
  const [doubles, setDoubles] = useState(false);
  const [open, setOpen] = useState(false);
  const [showMath, setShowMath] = useState(false);
  const [atk, setAtk] = useState<CalcMon | null>(null);
  const [def, setDef] = useState<CalcMon | null>(null);
  const [moves, setMoves] = useState<CalcMove[]>([]);
  const [moveIdx, setMoveIdx] = useState(0);
  const [aNat, setANat] = useState("Adamant"); const [aEv, setAEv] = useState<EVs>({ ...ZERO_EV, atk: 252, spe: 252, hp: 4 }); const [aIv, setAIv] = useState<EVs>({ ...ALL_IV });
  const [dNat, setDNat] = useState("Bold"); const [dEv, setDEv] = useState<EVs>({ ...ZERO_EV, hp: 252, def: 252, spd: 4 }); const [dIv, setDIv] = useState<EVs>({ ...ALL_IV });
  const [aPre, setAPre] = useState("Offensive"); const [dPre, setDPre] = useState("Bulky");
  const [aItem, setAItem] = useState("None"); const [aAbil, setAAbil] = useState("None");
  const [dItem, setDItem] = useState("None"); const [dAbil, setDAbil] = useState("None");
  const [weather, setWeather] = useState("None"); const [terrain, setTerrain] = useState("None");
  const [reflect, setReflect] = useState(false); const [lightscreen, setLightscreen] = useState(false);
  const [crit, setCrit] = useState(false); const [burn, setBurn] = useState(false); const [spread, setSpread] = useState(false);
  const [ask, setAsk] = useState<{ loading: boolean; text?: string; err?: boolean } | null>(null);

  useEffect(() => { (async () => {
    try { setAtk(await loadCalcMon(445)); } catch { /* */ }
    try { setDef(await loadCalcMon(823)); } catch { /* */ }
  })(); }, []);

  useEffect(() => {
    if (!atk) return; let alive = true;
    // keep an Offensive preset aligned to the (possibly new) attacker's category
    if (aPre === "Offensive") { const s = offensiveSet(atk); setANat(s.nat); setAEv(s.ev); setAIv(s.iv); }
    getPokemonMoves(atk.id).then((ms) => {
      const dmg = ms.filter((m) => m.type && m.damage_class !== "status" && (m.power ?? 0) > 0)
        .map((m) => ({ name: m.name, type: m.type as string, damage_class: m.damage_class as string, power: m.power as number }));
      dmg.sort((a, b) => (Number(atk.types.includes(b.type)) - Number(atk.types.includes(a.type))) || b.power - a.power);
      const want = atk.stats.attack >= atk.stats.sp_attack ? "physical" : "special";
      if (alive) { setMoves(dmg); setMoveIdx(Math.max(0, dmg.findIndex((m) => m.damage_class === want))); }
    }).catch(() => { if (alive) { setMoves([]); setMoveIdx(0); } });
    return () => { alive = false; };
  }, [atk?.id, atk?.types]); // eslint-disable-line react-hooks/exhaustive-deps

  const applyA = (p: string) => { setAPre(p); const s = p === "Bulky" ? BULKY_SET : offensiveSet(atk); setANat(s.nat); setAEv(s.ev); setAIv(s.iv); };
  const applyD = (p: string) => { setDPre(p); const s = p === "Bulky" ? BULKY_SET : offensiveSet(def); setDNat(s.nat); setDEv(s.ev); setDIv(s.iv); };
  const aEvSet = (e: EVs) => { setAEv(e); setAPre("Custom"); }; const aIvSet = (i: EVs) => { setAIv(i); setAPre("Custom"); };
  const dEvSet = (e: EVs) => { setDEv(e); setDPre("Custom"); }; const dIvSet = (i: EVs) => { setDIv(i); setDPre("Custom"); };

  const move = moves[moveIdx];
  let r: null | { minPct: number; maxPct: number; ko: number; te: number; stab: number; A: number; D: number; base: number; mod: number } = null;
  if (atk && def && move) {
    const phys = move.damage_class === "physical";
    const aK: SKey = phys ? "atk" : "spa"; const dK: SKey = phys ? "def" : "spd";
    let A = statFull(phys ? atk.stats.attack : atk.stats.sp_attack, level, aIv[aK], aEv[aK], natMul(aNat, aK), false);
    let D = statFull(phys ? def.stats.defense : def.stats.sp_defense, level, dIv[dK], dEv[dK], natMul(dNat, dK), false);
    const HP = statFull(def.stats.hp, level, dIv.hp, dEv.hp, 1, true);
    if (aItem === "Choice Band" && phys) A = Math.floor(A * 1.5);
    if (aItem === "Choice Specs" && !phys) A = Math.floor(A * 1.5);
    if (aAbil === "Huge Power" && phys) A = Math.floor(A * 2);
    if (aAbil === "Guts" && burn && phys) A = Math.floor(A * 1.5);
    if (dItem === "Assault Vest" && !phys) D = Math.floor(D * 1.5);
    if (dItem === "Eviolite") D = Math.floor(D * 1.5);
    const base = Math.floor(Math.floor(Math.floor((2 * level) / 5 + 2) * move.power * A / D) / 50) + 2;
    const te = eff(move.type, def.types);
    const stab = atk.types.includes(move.type) ? (aAbil === "Adaptability" ? 2 : 1.5) : 1;
    let mod = 1;
    if (spread) mod *= 0.75;
    if (weather === "Rain") mod *= move.type === "water" ? 1.5 : move.type === "fire" ? 0.5 : 1;
    if (weather === "Sun") mod *= move.type === "fire" ? 1.5 : move.type === "water" ? 0.5 : 1;
    if (terrain === "Electric" && move.type === "electric") mod *= 1.3;
    if (terrain === "Grassy" && move.type === "grass") mod *= 1.3;
    if (terrain === "Psychic" && move.type === "psychic") mod *= 1.3;
    if (crit) mod *= 1.5;
    if (burn && phys && aAbil !== "Guts") mod *= 0.5;
    if (!crit) { if (phys && reflect) mod *= doubles ? 0.667 : 0.5; if (!phys && lightscreen) mod *= doubles ? 0.667 : 0.5; }
    if (aItem === "Life Orb") mod *= 1.3;
    if (aItem === "Muscle Band" && phys) mod *= 1.1;
    if (aItem === "Wise Glasses" && !phys) mod *= 1.1;
    if (aItem === "Expert Belt" && te > 1) mod *= 1.2;
    if (aAbil === "Technician" && move.power <= 60) mod *= 1.5;
    if (aAbil === "Tinted Lens" && te < 1) mod *= 2;
    if (dAbil === "Thick Fat" && (move.type === "fire" || move.type === "ice")) mod *= 0.5;
    if (dAbil === "Multiscale") mod *= 0.5;
    if ((dAbil === "Solid Rock" || dAbil === "Filter") && te > 1) mod *= 0.75;
    const total = base * stab * te * mod;
    const maxDmg = Math.floor(total), minDmg = Math.floor(total * 0.85);
    r = { minPct: HP ? minDmg / HP * 100 : 0, maxPct: HP ? maxDmg / HP * 100 : 0, ko: te === 0 || minDmg <= 0 ? 0 : Math.ceil(HP / minDmg), te, stab, A, D, base, mod: stab * te * mod };
  }
  const koLabel = !r ? "" : r.te === 0 ? "immune" : r.ko === 1 ? "OHKO" : `${r.ko}HKO`;
  const faster = atk && def
    ? (statFull(atk.stats.speed, level, aIv.spe, aEv.spe, natMul(aNat, "spe"), false) === statFull(def.stats.speed, level, dIv.spe, dEv.spe, natMul(dNat, "spe"), false)
      ? "speed tie" : `${(statFull(atk.stats.speed, level, aIv.spe, aEv.spe, natMul(aNat, "spe"), false) > statFull(def.stats.speed, level, dIv.spe, dEv.spe, natMul(dNat, "spe"), false) ? atk : def).name} outspeeds`)
    : "";
  const runAsk = () => { if (!atk) return; setAsk({ loading: true });
    askQuestion(`Give a competitive build and moveset suggestion for ${atk.name}.`).then((res) => setAsk({ loading: false, text: res.answer })).catch(() => setAsk({ loading: false, err: true })); };

  const side = (which: "a" | "d") => {
    const isA = which === "a";
    const pre = isA ? aPre : dPre, apply = isA ? applyA : applyD;
    const nat = isA ? aNat : dNat, setNat = isA ? (n: string) => { setANat(n); setAPre("Custom"); } : (n: string) => { setDNat(n); setDPre("Custom"); };
    const item = isA ? aItem : dItem, setItem = isA ? setAItem : setDItem, items = isA ? DC_ITEMS : DC_ITEMS_D;
    const abil = isA ? aAbil : dAbil, setAbil = isA ? setAAbil : setDAbil, abils = isA ? DC_ABIL : DC_ABIL_D;
    const ev = isA ? aEv : dEv, iv = isA ? aIv : dIv, onEv = isA ? aEvSet : dEvSet, onIv = isA ? aIvSet : dIvSet;
    return (
      <div className="dc-side">
        <div className="sh">{isA ? "Attacker set" : "Defender set"}</div>
        <div className="dc-preset">{["Offensive", "Bulky", "Custom"].map((p) => (
          <button key={p} className={pre === p ? "on" : ""} onClick={() => p === "Custom" ? (isA ? setAPre : setDPre)("Custom") : apply(p)}>{p}</button>
        ))}</div>
        <div className="dc-ctrls">
          <label>Nature<select value={nat} onChange={(e) => setNat(e.target.value)}>{NAT.map((n) => <option key={n[0]}>{n[0]}</option>)}</select></label>
          <label>Item<select value={item} onChange={(e) => setItem(e.target.value)}>{items.map((x) => <option key={x}>{x}</option>)}</select></label>
          <label>Ability<select value={abil} onChange={(e) => setAbil(e.target.value)}>{abils.map((x) => <option key={x}>{x}</option>)}</select></label>
        </div>
        {pre === "Custom" ? <EvEditor ev={ev} iv={iv} onEv={onEv} onIv={onIv} /> : <EvBar ev={ev} />}
      </div>
    );
  };

  return (
    <section className="card dc">
      <div className="lbl">Damage calculator
        <span className="dc-top">
          <span className="dc-seg">{["Singles", "Doubles"].map((m, k) => <button key={m} className={doubles === (k === 1) ? "on" : ""} onClick={() => setDoubles(k === 1)}>{m}</button>)}</span>
          <span className="dc-seg">{[50, 100].map((L) => <button key={L} className={level === L ? "on" : ""} onClick={() => setLevel(L)}>Lv{L}</button>)}</span>
        </span>
      </div>
      <div className="dc-oneline">
        <DcPicker mon={atk} onPick={(id) => { setAPre("Offensive"); loadCalcMon(id).then(setAtk); }} ph="Attacker…" />
        <select className="dc-mv" value={moveIdx} onChange={(e) => setMoveIdx(Number(e.target.value))}>
          {moves.length === 0 && <option>move…</option>}
          {moves.slice(0, 60).map((m, i) => <option key={m.name} value={i}>{m.name} · {m.type} · {m.power}</option>)}
        </select>
        <span className="vs">vs</span>
        <DcPicker mon={def} onPick={(id) => loadCalcMon(id).then(setDef)} ph="Defender…" />
        <span className="eq">=</span>
        <div className="dc-out">{r ? <><b>{r.minPct.toFixed(0)}–{r.maxPct.toFixed(0)}%</b><span className={`dc-ko${r.ko === 1 ? " o" : ""}${r.te === 0 ? " im" : ""}`}>{koLabel}</span></> : <span className="dim">—</span>}</div>
      </div>
      <div className="dc-subrow">
        {r && <span className="fast">{faster} · ×{fmt(r.te)}{r.stab > 1 ? " STAB" : ""}</span>}
        <button className="dc-optbtn" onClick={() => setOpen((v) => !v)}>{open ? "hide options ▴" : "options — spread · item · ability · field ▾"}</button>
      </div>
      {open && (
        <div className="dc-drawer">
          <div className="dc-two">{side("a")}{side("d")}</div>
          <div className="dc-field">
            <select value={weather} onChange={(e) => setWeather(e.target.value)}>{WEATHER.map((x) => <option key={x}>{x === "None" ? "Weather" : x}</option>)}</select>
            <select value={terrain} onChange={(e) => setTerrain(e.target.value)}>{TERRAIN.map((x) => <option key={x}>{x === "None" ? "Terrain" : x}</option>)}</select>
            <label className={reflect ? "on" : ""}><input type="checkbox" checked={reflect} onChange={(e) => setReflect(e.target.checked)} />Reflect</label>
            <label className={lightscreen ? "on" : ""}><input type="checkbox" checked={lightscreen} onChange={(e) => setLightscreen(e.target.checked)} />Light Screen</label>
            <label className={crit ? "on" : ""}><input type="checkbox" checked={crit} onChange={(e) => setCrit(e.target.checked)} />Crit</label>
            <label className={burn ? "on" : ""}><input type="checkbox" checked={burn} onChange={(e) => setBurn(e.target.checked)} />Burn</label>
            {doubles && <label className={spread ? "on" : ""}><input type="checkbox" checked={spread} onChange={(e) => setSpread(e.target.checked)} />Spread</label>}
          </div>
          <button className="dc-mathtog" onClick={() => setShowMath((v) => !v)}>{showMath ? "hide math ▴" : "show math ▾"}</button>
          {showMath && r && move && (
            <div className="dc-formula">dmg = ⌊(⌊(2·{level}/5+2)·{move.power}·{r.A}/{r.D}⌋/50)+2⌋ × {r.stab} STAB × {fmt(r.te)} type × [0.85–1.0] = <b>{r.base}</b> base → <b>{r.minPct.toFixed(1)}–{r.maxPct.toFixed(1)}%</b></div>
          )}
          <div className="dc-ask">
            <button className="dc-askbtn" onClick={runAsk} disabled={ask?.loading}>{ask?.loading ? "Asking…" : "Ask the coach: best build & moveset"}</button>
            {ask && !ask.loading && ask.err && <div className="dc-answ err">Assistant unavailable — open it to try live.</div>}
            {ask && !ask.loading && ask.text && <div className="dc-answ">{renderAnswer(ask.text.split("\n").slice(0, 4).join("\n"))}<Link className="go" href="/ask">Open the assistant →</Link></div>}
          </div>
        </div>
      )}
    </section>
  );
}

/* ---------------- page ---------------- */
export default function Home() {
  const rootRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const el = document.documentElement;
    el.setAttribute("data-home", "");
    return () => el.removeAttribute("data-home");
  }, []);
  // staggered reveal
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const cards = Array.from(root.querySelectorAll<HTMLElement>(".card"));
    if (reduced()) { cards.forEach((c) => c.classList.add("in")); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) {
        const idx = cards.indexOf(e.target as HTMLElement);
        (e.target as HTMLElement).style.transitionDelay = `${Math.max(0, idx) * 70}ms`;
        e.target.classList.add("in");
        io.unobserve(e.target);
      }
    }), { threshold: 0.12 });
    cards.forEach((c) => io.observe(c));
    return () => io.disconnect();
  }, []);

  return (
    <main ref={rootRef} className="lc">
      <div className="lc-app">
        <header className="lc-head">
          <p className="eyebrow">Pokédex OS · your competitive toolkit</p>
          <Search />
        </header>

        <div className="lc-bento">
          <div className="band b1">
            <div className="ga ga-coach"><TeamCoachTile /></div>
            <div className="ga ga-ask"><AskTile /></div>
          </div>
          <div className="band b2">
            <div className="ga ga-dc"><DamageCalcTile /></div>
          </div>
          <div className="band b3">
            <div className="ga ga-look"><LookupTile /></div>
            <div className="ga ga-tc"><TypeCalcTile /></div>
            <div className="ga ga-nat"><NatureTile /></div>
          </div>
        </div>
      </div>
    </main>
  );
}
