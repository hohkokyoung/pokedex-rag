"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Fragment, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { useKeyNav } from "@/hooks/useKeyNav";
import { Facts, GradeBadge, StrategyBars, SummaryText, useInfo } from "@/components/TeamCardParts";
import { defensiveMatchups, superEffectiveHits } from "@/lib/typeChart";
import TypeMatchups from "@/components/TypeMatchups";
import { MoveLearnersModal } from "@/components/MoveLearners";
import Finder from "@/components/Finder";
import AskTile from "@/components/AskTile";
import CatchRateTile from "@/components/CatchRateTile";
import {
  BULKY_SET, DcPicker, EvEditor, HpPicker, InfoBox, MoveSearch, NAT, NAT_OPTS, PickSearch, Tag, natDesc, natTag,
  SABBR, art, loadCalcMon, loadMonMoves, monArt, natMul, offensiveSet, statFull,
  type CalcMon, type CalcMove, type EVs, type PickOpt, type SKey,
} from "@/components/calc/fields";
import { renderAnswer } from "@/lib/answerFormat";
import { RESIST_BERRY, TYPE_BOOST, calcHit, type DcField, type DcResult } from "@/lib/damageCalc";
import { DamageCard, SurviveCard } from "@/components/calc/CoachCards";
import { PlanSteps } from "@/components/agent/PlanSteps";
import { ViewBlock } from "@/components/agent/ViewBlock";
import type { Linking } from "@/components/agent/views/shared";
import {
  applyDelta, applyDone, applyError, applyPlan, applySources, applyStep, applyView, startRun, type AskRun,
} from "@/components/agent/runState";
import {
  listPokemon,
  listTeams,
  getPokemonAbilities,
  searchMoves,
  searchAbilities,
  searchItems,
  getHeldItems,
  getMoveLearners,
  getAbilityHolders,
  listNatures,
  calcAskStream,
  type BuildSuggestion,
  type BuildProposalView,
  type CalcApply,
  type CalcAskState,
  type CalcRef,
  assetUrl,
  type MoveResult,
  type MoveLearner,
  type SignatureZ,
  type AbilityHolder,
  type ItemResult,
  type NatureInfo,
  type TeamSummary,
} from "@/lib/api";
import type { PokemonSummary, Ability } from "@/lib/types";
import { TYPE_HEX } from "@/lib/pokeTypes";

/* ---------------- shared data ---------------- */
const TC = TYPE_HEX;
const ORDER = ["normal","fire","water","electric","grass","ice","fighting","poison","ground","flying","psychic","bug","rock","ghost","dragon","dark","steel","fairy"];
/** Detail link that preserves an alternate form (search results may be forms). */
const pokeHref = (p: PokemonSummary) =>
  p.form_id ? `/pokedex/${p.dex_number}?form=${p.form_id}` : `/pokedex/${p.dex_number}`;
const fmt = (x: number) => (x === 0 ? "0" : x === 0.25 ? "¼" : x === 0.5 ? "½" : String(x));
const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------------- global search ---------------- */
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
        <div className="ac" role="listbox" ref={listRef} data-lenis-prevent>
          {res.map((p, idx) => (
            <Link key={p.id} href={pokeHref(p)} onClick={() => setRes([])} role="option" {...itemProps(idx)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={assetUrl(p.sprite_url)} alt={p.name} />
              <span className="nm">{p.name}</span>
              <span className="tps">{p.types.map((t) => <Tag key={t} t={t} />)}</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--dim)" }}>Nº{String(p.dex_number).padStart(4, "0")}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------------- Ask ---------------- */

/* ---------------- Team builder & coach ---------------- */
/** Mini version of a /teams card: the user's teams, one at a time — grade, what
 *  the team does, its strategy and type facts, and the one thing to fix first. */
function TeamCoachTile() {
  const [teams, setTeams] = useState<TeamSummary[] | null>(null);
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    let alive = true;
    listTeams()
      .then(({ teams }) => {
        // Most complete teams first; empty drafts aren't worth showing here.
        const filled = teams.filter((t) => t.size > 0).sort((a, b) => b.size - a.size || a.id - b.id);
        if (alive) setTeams(filled);
      })
      .catch(() => alive && setTeams([]));
    return () => { alive = false; };
  }, []);

  // Load only a sliding window — the shown team plus its neighbours — so a
  // switch never waits, yet the cost stays at ~3 teams however many exist.
  const n = teams?.length ?? 0;
  const window3 = n ? [...new Set([idx - 1, idx, idx + 1].map((i) => (i + n) % n))].map((i) => teams![i]) : [];
  const info = useInfo(window3);
  const neighbourKey = window3.map((t) => t.id).join(",");
  useEffect(() => {
    for (const t of window3) for (const src of t.sprites) new Image().src = assetUrl(src); // warm sprites
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [neighbourKey]);
  const ready = (t?: TeamSummary) => !!t && !!info[t.id]?.p && !!info[t.id]?.st;
  const want = teams?.[idx % Math.max(1, teams.length)];
  // Stay on the team being shown until the requested one is fully loaded
  // (state adjusted during render — React's pattern for derived state).
  const [shownId, setShownId] = useState<number | null>(null);
  if (want && ready(want) && shownId !== want.id) setShownId(want.id);
  const cur = teams?.find((t) => t.id === shownId) ?? want;
  const { p, st, sum } = (cur && info[cur.id]) || {};
  const gap = p?.rating.areas.filter((x) => x.fix).sort((x, y) => x.score - y.score)[0];
  const step = (d: number) => teams && setIdx((i) => (i + d + teams.length) % teams.length);

  return (
    <section className="card lc-tc">
      <div className="lbl">
        Team builder &amp; coach
        {cur && (
          <span className="lc-tc-sw">
            {teams && teams.length > 1 && <button onClick={() => step(-1)} aria-label="Previous team">‹</button>}
            <span className="mono">{cur.name}</span>
            {teams && teams.length > 1 && <button onClick={() => step(1)} aria-label="Next team">›</button>}
          </span>
        )}
      </div>

      {teams === null ? (
        <span className="lab-skel" style={{ height: 220 }} />
      ) : !cur ? (
        <div className="lc-tc-empty">
          <b>Build your first team</b>
          <span>Add up to six Pokémon and get a grade, a strategy read and what to fix.</span>
          <Link className="go" href="/teams">Start a team →</Link>
        </div>
      ) : (
        <>
          <div className="lc-team">
            {Array.from({ length: 6 }, (_, i) => cur.sprites[i]).map((s, i) =>
              s ? (
                <Link className="s" key={i} href={`/teams/${cur.id}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={assetUrl(s)} alt="" />
                </Link>
              ) : (
                <Link className="s e" key={i} href={`/teams/${cur.id}`} aria-label="Add a Pokémon">+</Link>
              ),
            )}
          </div>
          {!p || !st ? (
            <span className="lab-skel" style={{ height: 160 }} />
          ) : (
            <>
              <div className="lc-tc-head">
                <GradeBadge p={p} href={`/teams/${cur.id}#rating`} />
                <span className="tl-style" title={st.style_reason}>{st.style}</span>
              </div>
              <SummaryText sum={sum} fallback={p.gist} />
              <div className="lc-tc-body">
                <StrategyBars st={st} />
                <Facts p={p} />
              </div>
              {gap && (
                <div className="lc-fix">
                  Weakest: <b>{gap.label.toLowerCase()} ({gap.grade})</b> — {gap.headline}. {gap.fix}
                </div>
              )}
            </>
          )}
          <div className="lc-tc-links">
            <Link className="go" href={`/teams/${cur.id}`}>Open team →</Link>
            <Link className="go dim" href="/teams">All teams</Link>
          </div>
        </>
      )}
    </section>
  );
}

/* ---------------- Type calculator (defends as 1 or 2 types) ---------------- */
function TypeCalcTile() {
  const [sel, setSel] = useState<string[]>(["fire"]);
  const toggle = (o: string) =>
    setSel((s) => (s.includes(o) ? s.filter((x) => x !== o) : s.length < 2 ? [...s, o] : [s[1], o]));
  // Same rows as the detail page's Type Matchups card, plus what the picked types hit ×2.
  const matchups = defensiveMatchups(sel);
  const hits = superEffectiveHits(sel);
  return (
    <section className="card">
      <div className="lbl">Type calculator<span className="mono">defends as 1–2 types</span></div>
      <div className="lc-tg">
        {ORDER.map((o) => <button key={o} onClick={() => toggle(o)} className={sel.includes(o) ? "on" : ""} style={{ "--c": TC[o] } as CSSProperties}>{o}</button>)}
      </div>
      {sel.length > 0 && <TypeMatchups m={matchups} hits={hits} renderType={(t) => <Tag key={t} t={t} />} />}
    </section>
  );
}

/* ---------------- Combined lookup: moves + abilities + items ---------------- */
type Entry = {
  key: string; name: string; kind: "Move" | "Ability" | "Item"; type?: string | null;
  cat?: string | null; power?: number | null; acc?: number | null; pp?: number | null;
  cost?: number | null; effect?: string | null; sub?: string | null;
  zSig?: SignatureZ | null;
  fling?: number | null;
};
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const moveToEntry = (m: MoveResult): Entry => ({
  key: "m" + m.id, name: m.name, kind: "Move", type: m.type,
  cat: m.damage_class ? cap(m.damage_class) : null, power: m.power, acc: m.accuracy, pp: m.pp,
  effect: m.short_effect, zSig: m.signature_z ?? null,
});
const abilityToEntry = (a: Ability): Entry => ({
  key: "a" + a.id, name: a.name, kind: "Ability",
  // Lead with the concrete mechanic ("Increases moves' accuracy to 1.3×");
  // keep the in-game flavour text as a subtitle when it adds something.
  effect: a.short_effect ?? a.effect,
  sub: a.short_effect ? a.effect : null,
});
const itemToEntry = (i: ItemResult): Entry => ({
  key: "i" + i.id, name: i.name, kind: "Item", cat: i.category, cost: i.cost, effect: i.short_effect,
  sub: i.flavor_text ?? null, fling: i.fling_power ?? null,
});
/** Why no Pokémon learns a move, for the lookup card. */
const unlearnable = (e: Entry) =>
  e.name === "Struggle" ? "No Pokémon learns Struggle — it's used automatically once every move is out of PP."
  : e.pp === 1 ? "Z-Move — no Pokémon learns it. A Z-Crystal turns a damaging move into it for one turn."
  : /^(G-)?Max /.test(e.name) ? "Max Move — no Pokémon learns it. A Dynamaxed Pokémon's moves become it."
  : "No Pokémon learns this move in any game's regular learnset.";
const KIND_BG: Record<string, string> = { Ability: "var(--ink)", Item: "#4a4a55" };
function LookupTile() {
  const [q, setQ] = useState("");
  const [list, setList] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  // The entry whose modal is open (any kind: move, ability or item).
  const [modal, setModal] = useState<Entry | null>(null);
  const [holders, setHolders] = useState<AbilityHolder[]>([]);
  // Which ability `holders` was loaded for, so a stale list never shows.
  const [holdersFor, setHoldersFor] = useState<string | null>(null);
  const [holderQ, setHolderQ] = useState("");
  // The advanced finder: every move / ability / item with filters and sorting.
  const [finder, setFinder] = useState(false);

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
        setList([...moves.map(moveToEntry), ...abilities.map(abilityToEntry), ...items.map(itemToEntry)].slice(0, 5));
      } catch {
        if (alive) setList([]);
      } finally {
        if (alive) setLoading(false);
      }
    }, 200);
    return () => { alive = false; clearTimeout(id); };
  }, [q]);

  // Click or Enter opens the entry's modal; the card itself never grows.
  const open = (e: Entry) => { setHolderQ(""); setModal(e); };
  // The card previews whichever row is highlighted (hover or arrow keys); click or
  // Enter opens its modal. The preview follows the highlight only once it rests
  // (~90ms), so sweeping the mouse across rows doesn't resize the card per row.
  const { active, listRef, onKeyDown, itemProps } = useKeyNav(list, open);

  // Learners/holders for every listed move and ability, fetched as soon as the list
  // appears and cached, so a preview never shows (and then drops) a loading state.
  const [learnerCache, setLearnerCache] = useState<Record<string, (MoveLearner | AbilityHolder)[]>>({});
  const ready = (e: Entry | undefined) => !!e && (e.kind === "Item" || e.key in learnerCache);
  // The preview switches only to an entry whose data is ready, so it goes straight
  // from one complete state to the next (no half-loaded box that then grows).
  const [previewKey, setPreviewKey] = useState<string | null>(null);
  const target = list[active];
  const targetReady = ready(target);
  useEffect(() => {
    if (!target || !targetReady) return;
    const t = setTimeout(() => setPreviewKey(target.key), 90);
    return () => clearTimeout(t);
  }, [target, targetReady]);
  const previewed = list.find((e) => e.key === previewKey);
  // Until something has been previewed, show the top result once it's ready.
  const detail = previewed ?? (ready(list[0]) ? list[0] : undefined);
  useEffect(() => {
    let alive = true;
    for (const e of list) {
      if (e.kind === "Item" || e.key in learnerCache) continue;
      const id = Number(e.key.slice(1));
      (e.kind === "Move" ? getMoveLearners(id, 250) : getAbilityHolders(id, 250))
        .catch(() => [])
        .then((ls) => { if (alive) setLearnerCache((c) => ({ ...c, [e.key]: ls })); });
    }
    return () => { alive = false; };
  }, [list]); // eslint-disable-line react-hooks/exhaustive-deps
  const shownLearners = detail ? learnerCache[detail.key] ?? null : null;

  // An ability's modal lists every species that has it.
  useEffect(() => {
    if (modal?.kind !== "Ability") return;
    let alive = true;
    const key = modal.key;
    const done = (ls: AbilityHolder[]) => { if (alive) { setHolders(ls); setHoldersFor(key); } };
    getAbilityHolders(Number(key.slice(1)), 250).then(done).catch(() => done([]));
    return () => { alive = false; };
  }, [modal]);

  // Ability/item modals: close on Escape and lock the page (Lenis) scroll.
  // (The move modal handles its own.)
  const plainModal = modal != null && modal.kind !== "Move";
  useEffect(() => {
    if (!plainModal) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setModal(null); };
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
  }, [plainModal]);

  const dash = (v: number | null | undefined) => (v == null ? "—" : String(v));
  const badge = (e: Entry) =>
    e.type ? <Tag t={e.type} /> : <span className="lc-tt" style={{ background: KIND_BG[e.kind] }}>{e.kind}</span>;
  // Opened from the finder, the finder stays mounted (hidden) underneath: Back / Escape /
  // the backdrop return to it with its filters intact, while × closes both.
  const back = () => setModal(null);
  const close = () => { setModal(null); setFinder(false); };
  const shownHolders = modal && holdersFor === modal.key ? holders : null;

  return (
    <section className="card lc-look">
      <div className="lbl">Move · ability · item lookup<span className="mono">3,000+ entries</span></div>
      <div className="lc-look-q">
        <input placeholder="e.g. Earthquake, Levitate, Leftovers…" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={onKeyDown} aria-autocomplete="list" />
        <button className="lc-look-adv" onClick={() => setFinder(true)} aria-label="Advanced search" title="Advanced search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
            <path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1" />
            <circle cx="15" cy="6" r="2" /><circle cx="9" cy="12" r="2" /><circle cx="17" cy="18" r="2" />
          </svg>
        </button>
      </div>
      <div className="lc-moveres" role="listbox" ref={listRef}>
        {list.map((e, idx) => (
          <div className="lc-moverow" key={e.key} role="option" {...itemProps(idx)} onClick={() => open(e)}
            // Flag rows whose name is cut off, so hovering shows the full name.
            onMouseEnter={(ev) => {
              const nm = ev.currentTarget.querySelector<HTMLElement>(".nm");
              ev.currentTarget.toggleAttribute("data-cut", !!nm && nm.scrollWidth > nm.clientWidth);
            }}>
            {badge(e)}
            <span className="lc-nmwrap">
              <span className="nm">{e.name}</span>
              <span className="lc-nmtip" aria-hidden>{e.name}</span>
            </span>
            <span className="pw">{e.kind === "Move" ? `${e.cat ?? "—"} · ${dash(e.power)}` : e.kind === "Item" ? (e.cat ?? "Item") : "Ability"}</span>
          </div>
        ))}
        {!loading && list.length === 0 && <div className="sub">No match — try “Ice Beam”, “Intimidate”, “Leftovers”.</div>}
        {loading && list.length === 0 && <div className="sub">Searching…</div>}
      </div>
      {!detail && <div className="lc-movedet lc-movedet--fixed lc-movedet--empty" aria-hidden />}
      {detail && (
        <div className="lc-movedet lc-movedet--fixed">
          {/* Keyed so each newly previewed entry fades in (see .lc-det-in). */}
          <div key={detail.key} className="lc-det-in">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            {badge(detail)}
            <b className="lc-detname">{detail.name}</b>
          </div>
          {detail.kind === "Move" && (
            <div className="lc-modal-meta lc-detmeta">
              <span><b>{detail.cat ?? "—"}</b></span>
              <span>Power <b>{dash(detail.power)}</b></span>
              <span>Acc <b>{dash(detail.acc)}</b>{detail.acc != null ? "%" : ""}</span>
              <span>PP <b>{dash(detail.pp)}</b></span>
            </div>
          )}
          {detail.kind === "Item" && (
            <div className="lc-modal-meta lc-detmeta">
              <span><b>{detail.cat ?? "Item"}</b></span>
              <span>Cost <b>{detail.cost ? `₽${detail.cost.toLocaleString()}` : "—"}</b></span>
              <span>Fling <b>{dash(detail.fling)}</b></span>
            </div>
          )}
          <div className="lc-deteff">{detail.effect || "No description on file."}</div>
          </div>
          {detail.kind === "Item" && detail.sub && (
            <div key={detail.key + ":flavor"} className="lc-lklearn lc-det-in">
              <div className="h"><span className="lc-dethead">In-game description</span>
                <button className="tog" onClick={() => open(detail)}>details</button>
              </div>
              <p className="lc-detflavor">“{detail.sub}”</p>
            </div>
          )}
          {detail.kind !== "Item" && shownLearners && (
            <div key={detail.key + ":learners"} className="lc-lklearn lc-det-in">
              <div className="h">
                <span className="lc-dethead">
                  {shownLearners.length === 0 && detail.zSig ? <>Z-Move · holding <b style={{ fontWeight: 600, color: "var(--ink)" }}>{detail.zSig.crystal}</b></>
                    : shownLearners.length === 0 ? unlearnable(detail).split(" — ")[0]
                    : <>{detail.kind === "Move" ? "Learned by " : "Found on "}<b>{shownLearners.length}{shownLearners.length >= 250 ? "+" : ""}</b> species</>}
                </span>
                <button className="tog" onClick={() => open(detail)}>{shownLearners.length === 0 ? "details" : "show all"}</button>
              </div>
              <div className="row lc-detrow">
                {(shownLearners.length ? shownLearners : detail.zSig ? detail.zSig.users : []).slice(0, 6).map((p) => {
                  const formId = "form_id" in p ? p.form_id : null;
                  return (
                    <Link key={p.id} href={formId ? `/pokedex/${p.dex_number}?form=${formId}` : `/pokedex/${p.dex_number}`} title={p.name} className="s">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={formId ? assetUrl(p.sprite_url) : art(p.dex_number)} alt={p.name} />
                    </Link>
                  );
                })}
                {shownLearners.length > 6 && <button className="more" onClick={() => open(detail)}>+{shownLearners.length - 6}</button>}
              </div>
            </div>
          )}
        </div>
      )}
      {modal?.kind === "Move" && (
        <MoveLearnersModal
          move={{ id: Number(modal.key.slice(1)), name: modal.name, type: modal.type ?? null, category: modal.cat ?? null, power: modal.power ?? null, accuracy: modal.acc ?? null, pp: modal.pp ?? null, effect: modal.effect ?? null, sub: modal.sub ?? null }}
          emptyNote={modal.zSig ? (
            <>
              <p className="lc-modal-desc" style={{ marginTop: 0 }}>
                Signature Z-Move: holding <b style={{ color: "var(--ink)" }}>{modal.zSig.crystal}</b>, {modal.zSig.users.length > 1 ? "their" : "its"} <b style={{ color: "var(--ink)" }}>{modal.zSig.base_move}</b> becomes {modal.name}.
              </p>
              <div className="lc-modal-grid lc-modal-grid--flat">
                {modal.zSig.users.map((u) => (
                  <Link key={u.id} href={u.form_id ? `/pokedex/${u.dex_number}?form=${u.form_id}` : `/pokedex/${u.dex_number}`} title={u.name} onClick={close}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={assetUrl(u.sprite_url)} alt={u.name} />
                    <span>{u.name}</span>
                  </Link>
                ))}
              </div>
            </>
          ) : <p className="lc-modal-desc" style={{ marginTop: 0 }}>{unlearnable(modal)}</p>}
          onClose={close}
          onBack={finder ? back : undefined}
        />
      )}
      {plainModal && modal && typeof document !== "undefined" && createPortal(
        <div className="lc-modal" onClick={back} role="dialog" aria-modal="true" data-lenis-prevent>
          <div className={`lc-modal-card${modal.kind === "Item" ? " lc-modal-card--short" : ""}`} onClick={(e) => e.stopPropagation()}>
            <div className="lc-modal-top" style={modal.kind === "Item" ? { borderBottom: "none" } : undefined}>
              <div className="lc-modal-head">
                {finder && <button className="lc-modal-back" onClick={back} aria-label="Back" title="Back"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M15 5l-7 7 7 7" /></svg></button>}
                {badge(modal)}
                <b>{modal.name}</b>
                <span className="sub">
                  {modal.kind === "Ability" && shownHolders ? `${shownHolders.length}${shownHolders.length >= 250 ? "+" : ""} species have it` : ""}
                </span>
                <button className="x" onClick={close} aria-label="Close">×</button>
              </div>
              {modal.kind === "Item" && (
                <div className="lc-modal-meta">
                  <span><b>{modal.cat ?? "Item"}</b></span>
                  <span>Cost <b>{modal.cost ? `₽${modal.cost.toLocaleString()}` : "—"}</b></span>
                  <span>Fling <b>{dash(modal.fling)}</b></span>
                </div>
              )}
              <p className="lc-modal-desc">{modal.effect || "No description on file."}</p>
              {modal.sub && <p className="lc-modal-desc lc-modal-desc--flavor">{modal.sub}</p>}
            </div>
            {modal.kind === "Ability" && (
              <>
                <div className="lc-modal-sub">
                  <input autoFocus placeholder="Filter these species…" value={holderQ} onChange={(e) => setHolderQ(e.target.value)} />
                </div>
                {(() => {
                  const f = holderQ.trim().toLowerCase();
                  const all = shownHolders ?? [];
                  const shown = f ? all.filter((p) => p.name.toLowerCase().includes(f)) : all;
                  return (
                    <div className="lc-modal-grid" data-lenis-prevent>
                      {shown.map((p) => (
                        <Link key={p.id} href={`/pokedex/${p.dex_number}`} title={p.name} onClick={close} className={p.is_hidden ? "is-hidden" : undefined}>
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={art(p.dex_number)} alt={p.name} />
                          <span>{p.name}</span>
                          <span className="tps-mini">{p.types.map((t) => <Tag key={t} t={t} />)}</span>
                        </Link>
                      ))}
                      {!shownHolders && <div className="lc-modal-empty">Loading…</div>}
                      {shownHolders && shown.length === 0 && <div className="lc-modal-empty">No species match “{holderQ.trim()}”.</div>}
                    </div>
                  );
                })()}
              </>
            )}
          </div>
        </div>,
        document.body,
      )}
      {/* After the modals so, closing both at once, its scroll-lock cleanup runs last. */}
      {finder && (
        <Finder
          hidden={modal != null}
          initialQuery={q.trim()}
          // Start on whatever kind the lookup is previewing (a move, ability or item).
          initialKind={detail?.kind === "Ability" ? "ability" : detail?.kind === "Item" ? "item" : "move"}
          onPickMove={(m) => open(moveToEntry(m))}
          onPickAbility={(a) => open(abilityToEntry(a))}
          onPickItem={(i) => open(itemToEntry(i))}
          onClose={() => setFinder(false)}
        />
      )}
    </section>
  );
}

/* ---------------- Nature helper ---------------- */
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
// Curated damage-relevant items & abilities (name → effect flags).
// Held items the calc models. Type boosters and resist berries are keyed by the move type they touch.
type DcItem = { name: string; side: "a" | "d"; note: string };
const DC_ITEM_INFO: DcItem[] = [
  { name: "Choice Band", side: "a", note: "Atk ×1.5" }, { name: "Choice Specs", side: "a", note: "SpA ×1.5" },
  { name: "Life Orb", side: "a", note: "×1.3" }, { name: "Expert Belt", side: "a", note: "super-effective ×1.2" },
  { name: "Muscle Band", side: "a", note: "physical ×1.1" }, { name: "Wise Glasses", side: "a", note: "special ×1.1" },
  ...Object.entries(TYPE_BOOST).map(([name, t]): DcItem => ({ name, side: "a", note: `${t} moves ×1.2` })),
  { name: "Assault Vest", side: "d", note: "SpD ×1.5" }, { name: "Eviolite", side: "d", note: "Def & SpD ×1.5 (unevolved)" },
  { name: "Focus Sash", side: "d", note: "survives one hit from full HP" },
  ...Object.entries(RESIST_BERRY).map(([name, t]): DcItem => ({ name, side: "d", note: `halves super-effective ${t}` })),
];
const DC_ABIL = ["None", "Adaptability", "Huge Power", "Technician", "Guts", "Tinted Lens"];
const DC_ABIL_D = ["None", "Thick Fat", "Multiscale", "Solid Rock", "Filter"];
const WEATHER = ["None", "Rain", "Sun"];
const TERRAIN = ["None", "Electric", "Grassy", "Psychic"];
type DcSet = { mon: CalcMon | null; pre: string; nat: string; ev: EVs; iv: EVs; item: string; abil: string; hp: number };
// One-tap follow-ups for the calc's coach.
const COACH_START = ["Best build", "Bulky set", "Fast sweeper"];
const COACH_QUICK = ["Make it bulkier", "Make it faster", "No Choice item", "Try a special set", "Explain the EVs"];
const sameBuild = (a: BuildSuggestion, b?: BuildSuggestion) => !!b && JSON.stringify({ ...a, why: "" }) === JSON.stringify({ ...b, why: "" });
// An EV spread in words, biggest spends first: "252 Atk / 252 Spe / 4 HP".
const evText = (ev: EVs) => (Object.keys(ev) as SKey[]).filter((k) => ev[k] > 0).sort((x, y) => ev[y] - ev[x]).map((k) => `${ev[k]} ${SABBR[k]}`).join(" / ") || "none";
// hp = current HP as % of max; damage % stays relative to max HP, KO calls use current.
const newDef = (): DcSet => ({ mon: null, pre: "Bulky", ...BULKY_SET, item: "None", abil: "None", hp: 100 });
// Doubles targeting, from the move's PokéAPI `move_targets` identifier.
type TgKind = "sel" | "rand" | "foes" | "all" | "ally";
const tgKind = (t?: string | null): TgKind =>
  t === "all-opponents" ? "foes" : t === "all-other-pokemon" ? "all" : t === "ally" ? "ally" : t === "random-opponent" ? "rand" : "sel";
const TG_LABEL: Record<TgKind, string> = { sel: "one target", rand: "random foe", foes: "both foes", all: "everyone else", ally: "ally" };
const isSpread = (k: TgKind) => k === "foes" || k === "all";
const isAimable = (k: TgKind) => k === "sel" || k === "rand";
const pctText = (r: DcResult) => (r.te === 0 ? "immune" : `${r.minPct.toFixed(0)}–${r.maxPct.toFixed(0)}%`);

/** HP left after the hit: solid = worst roll, faded = best roll. */
function HpLeft({ min, max, hp = 100 }: { min: number; max: number; hp?: number }) {
  const worst = Math.max(0, hp - max), best = Math.max(0, hp - min);
  const col = (l: number) => (l > 50 ? "var(--ok)" : l > 20 ? "#f0b429" : "var(--red)");
  return (
    <div className="dc-hpl" aria-hidden>
      {hp < 100 && <i className="lost" style={{ left: `${hp}%`, width: `${100 - hp}%` }} />}
      <i className="ghost" style={{ width: `${best}%`, background: col(best) }} />
      <i style={{ width: `${worst}%`, background: col(worst) }} />
    </div>
  );
}


function useCalcMoves(mon: CalcMon | null) {
  const [moves, setMoves] = useState<CalcMove[]>([]);
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (!mon) return; let alive = true;
    loadMonMoves(mon).then((ms) => {
      // The whole learnset: damaging moves first (STAB, then power), status moves after.
      const keep = ms.filter((m) => m.type).map((m) => ({
        name: m.name, type: m.type as string, damage_class: m.damage_class ?? "status", power: m.power ?? 0,
        target: m.target ?? null, priority: m.priority ?? 0, accuracy: m.accuracy, effect: m.short_effect,
      }));
      keep.sort((a, b) => (Number(a.power === 0) - Number(b.power === 0))
        || (Number(mon.types.includes(b.type)) - Number(mon.types.includes(a.type))) || b.power - a.power || a.name.localeCompare(b.name));
      const want = mon.stats.attack >= mon.stats.sp_attack ? "physical" : "special";
      if (alive) { setMoves(keep); setIdx(Math.max(0, keep.findIndex((m) => m.damage_class === want))); }
    }).catch(() => { if (alive) { setMoves([]); setIdx(0); } });
    return () => { alive = false; };
  }, [mon?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  return { moves, idx, setIdx, move: mon ? moves[idx] : undefined };
}
// Held items' real descriptions (for the item card's hover), loaded once.
let heldItemInfo: Promise<Map<string, string>> | null = null;
function useItemInfo(): Map<string, string> {
  const [info, setInfo] = useState<Map<string, string>>(new Map());
  useEffect(() => {
    let alive = true;
    (heldItemInfo ??= getHeldItems()
      .then((xs) => new Map(xs.filter((x) => x.short_effect).map((x) => [x.name, x.short_effect!.replace(/^Held:\s*/i, "")])))
      .catch(() => {
        heldItemInfo = null;
        return new Map<string, string>();
      })).then((m) => alive && setInfo(m));
    return () => {
      alive = false;
    };
  }, []);
  return info;
}
const ITEM_OPTS: PickOpt[] = [{ v: "None", hint: "no item" }, ...DC_ITEM_INFO.map((i) => ({ v: i.name, hint: i.note }))];
// Typing searches every item in the database; ones the calc doesn't model are marked as not changing damage.
const searchAllItems = (q: string): Promise<PickOpt[]> => searchItems(q, 30).then((xs) => xs
  .filter((x) => !DC_ITEM_INFO.some((i) => i.name === x.name))
  .map((x) => ({ v: x.name, hint: `${x.short_effect ?? x.category ?? "item"} · no effect on damage`, off: true })));
const ABIL_HINT: Record<string, string> = {
  None: "no damage effect", Adaptability: "STAB ×2", "Huge Power": "Atk ×2", Technician: "moves ≤60 power ×1.5", Guts: "Atk ×1.5 while burned",
  "Tinted Lens": "resisted hits ×2", "Thick Fat": "takes ½ from Fire & Ice", Multiscale: "takes ½ at full HP", "Solid Rock": "super-effective hits ×0.75", Filter: "super-effective hits ×0.75",
};
const newAtk = (): DcSet => ({ mon: null, pre: "Offensive", ...offensiveSet(null), item: "None", abil: "None", hp: 100 });
// Slots 0–1 are your side (lead, partner) and 2–3 the opponent's (left, right). Singles uses slots 0 and 2.
const sideOf = (i: number) => (i < 2 ? 0 : 1);
const SLOT_ROLE = ["Lead", "Partner", "Left", "Right"];
const ORD = ["1st", "2nd", "3rd", "4th"];
const CALC_ABILS = new Set([...DC_ABIL.slice(1), ...DC_ABIL_D.slice(1)]);
// A species' real abilities (cached), for the ability field.
const abilityCache = new Map<number, Promise<Ability[]>>();
const loadAbilities = (id: number) => {
  if (!abilityCache.has(id)) abilityCache.set(id, getPokemonAbilities(id).catch(() => { abilityCache.delete(id); return []; }));
  return abilityCache.get(id)!;
};
// A form carries its own abilities; a species' come from the API.
const monAbilities = (m: CalcMon) => (m.abilities ? Promise.resolve(m.abilities) : loadAbilities(m.id));
// Default ability for a newly picked Pokémon: one the calc models if it has one, else its first regular ability.
const defaultAbility = (ab: Ability[]) => (ab.find((a) => CALC_ABILS.has(a.name)) ?? ab.find((a) => !a.is_hidden) ?? ab[0])?.name ?? "None";
function useAbilityOpts(mon: CalcMon | null): PickOpt[] {
  const [ab, setAb] = useState<{ id: number; list: Ability[] } | null>(null);
  useEffect(() => {
    if (!mon) return; let alive = true;
    monAbilities(mon).then((list) => { if (alive) setAb({ id: mon.id, list }); });
    return () => { alive = false; };
  }, [mon?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  return useMemo(() => {
    const list = ab && mon && ab.id === mon.id ? ab.list : [];
    return list.map((a) => ({
      v: a.name,
      hint: `${a.is_hidden ? "Hidden · " : ""}${ABIL_HINT[a.name] ?? `${a.short_effect ?? ""}${a.short_effect ? " · " : ""}no effect on damage`}`,
      off: !CALC_ABILS.has(a.name),
    }));
  }, [ab, mon]);
}
type DcHit = { from: number; to: number; r: DcResult; ff: boolean };
type TurnHit = DcHit & { ko: "yes" | "maybe" | null; sash: boolean };

// Damage / survive cards in the coach thread have no citations to link to.
const NO_LINK: Linking = { n: () => null, hot: null, cited: new Set<number>(), hover: () => ({}) };

/** Stream one calc-coach question into its turn (outside the component: it reads the clock). */
function streamCalcCoach(
  question: string,
  state: CalcAskState,
  patch: (fn: (t: AskRun) => AskRun) => void,
  onBuild: (v: BuildProposalView) => void,
): AbortController {
  const ctrl = new AbortController();
  const t0 = performance.now();
  calcAskStream(question, state, {
    signal: ctrl.signal,
    onPlan: (p) => patch((t) => applyPlan(t, p)),
    onStep: (e) => patch((t) => applyStep(t, e)),
    onView: (v) => {
      patch((t) => applyView(t, v));
      if (v.kind === "build_proposal") onBuild(v);
    },
    onSources: (s) => patch((t) => applySources(t, s)),
    onDelta: (d) => patch((t) => applyDelta(t, d)),
    onDone: (d) => patch((t) => applyDone(t, d, (performance.now() - t0) / 1000)),
    onError: (reason) =>
      patch((t) =>
        applyError(t, reason === "assistant-not-configured" ? "The coach needs an LLM API key for that."
          : reason.startsWith("Coaching failed") ? reason : "The coach couldn't answer — try again."),
      ),
  });
  return ctrl;
}

function DamageCalcTile() {
  const [level, setLevel] = useState(100);
  const [doubles, setDoubles] = useState(false);
  const [open, setOpen] = useState(false);
  const [showMath, setShowMath] = useState(false);
  // Which card of the focused Pokémon is open as a search ("<slot>:move", "<slot>:item"…).
  const [editing, setEditing] = useState<string | null>(null);
  const itemInfo = useItemInfo();
  const [sets, setSets] = useState<DcSet[]>([newAtk(), newAtk(), newDef(), newDef()]);
  // The opposing slot each Pokémon aims a single-target move at.
  const [aims, setAims] = useState<number[]>([2, 3, 0, 1]);
  // The Pokémon whose details are open.
  const [focus, setFocus] = useState(0);
  const [weather, setWeather] = useState("None"); const [terrain, setTerrain] = useState("None");
  const [reflect, setReflect] = useState(false); const [lightscreen, setLightscreen] = useState(false);
  const [crit, setCrit] = useState(false); const [burn, setBurn] = useState(false);
  const [friendGuard, setFriendGuard] = useState(false);
  // The coach's conversation about one slot, and the build it proposed there (from a `build_proposal`
  // view). `prev` is the set before the coach's first Apply (what Revert restores); `applied` says the
  // current proposal is in. Each turn is one streamed agent run (plan steps, views, answer).
  const [coach, setCoach] = useState<{
    id: number; slot: number; monId: number; turns: AskRun[]; build?: BuildSuggestion; pick?: string;
    prev?: { set: DcSet; idx: number }; applied?: boolean;
  } | null>(null);
  // Damage / survive cards applied into the calc: "<turn>:<view>" → the slots as they were, for Revert.
  const [cardPrev, setCardPrev] = useState<Record<string, Record<number, DcSet>>>({});
  const [coachInput, setCoachInput] = useState("");
  const coachChatRef = useRef<HTMLDivElement | null>(null);
  const coachAbort = useRef<AbortController | null>(null);
  const coachSeq = useRef(0);
  useEffect(() => () => coachAbort.current?.abort(), []);
  const lastTurn = coach?.turns.at(-1);
  // Keep the newest message in view as the conversation grows.
  useEffect(() => {
    const el = coachChatRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: reduced() ? "auto" : "smooth" });
  }, [coach?.turns.length, lastTurn?.answer.length, lastTurn?.views.length, lastTurn?.status]);
  const mv0 = useCalcMoves(sets[0].mon), mv1 = useCalcMoves(sets[1].mon), mv2 = useCalcMoves(sets[2].mon), mv3 = useCalcMoves(sets[3].mon);
  const mvs = [mv0, mv1, mv2, mv3];
  const ab0 = useAbilityOpts(sets[0].mon), ab1 = useAbilityOpts(sets[1].mon), ab2 = useAbilityOpts(sets[2].mon), ab3 = useAbilityOpts(sets[3].mon);
  const abilityOptsBySlot = [ab0, ab1, ab2, ab3];

  const patchSet = (i: number, p: Partial<DcSet>) => setSets((ds) => ds.map((d, k) => (k === i ? { ...d, ...p } : d)));
  // A newly picked Pokémon on the Offensive preset gets the spread matching its category.
  const pickMon = (i: number, m: CalcMon) => {
    setSets((ds) => ds.map((d, k) => (k !== i ? d : d.pre === "Offensive" ? { ...d, mon: m, ...offensiveSet(m), abil: "None" } : { ...d, mon: m, abil: "None" })));
    monAbilities(m).then((ab) => setSets((ds) => ds.map((d, k) => (k === i && d.mon?.id === m.id ? { ...d, abil: defaultAbility(ab) } : d))));
  };

  useEffect(() => { (async () => {
    try { pickMon(0, await loadCalcMon(445)); } catch { /* */ }
    try { pickMon(2, await loadCalcMon(823)); } catch { /* */ }
  })(); }, []);

  const applyPre = (i: number, p: string) => {
    const sp = p === "Bulky" ? BULKY_SET : offensiveSet(sets[i].mon);
    patchSet(i, { pre: p, nat: sp.nat, ev: sp.ev, iv: sp.iv });
  };

  const active = doubles ? [0, 1, 2, 3] : [0, 2];
  const f = active.includes(focus) ? focus : sideOf(focus) === 0 ? 0 : 2;
  const foesOf = (i: number) => active.filter((j) => sideOf(j) !== sideOf(i));
  const mateOf = (i: number) => active.find((j) => j !== i && sideOf(j) === sideOf(i));
  // Aim at a filled opposing slot: the one picked, else the first with a Pokémon in it.
  const targetsOf = (i: number) => foesOf(i).filter((j) => sets[j].mon);
  const aimOf = (i: number) => (targetsOf(i).includes(aims[i]) ? aims[i] : targetsOf(i)[0] ?? foesOf(i)[0]);
  const kindOf = (i: number) => tgKind(mvs[i].move?.target);
  const baseField: DcField = { level, doubles, spread: false, weather, terrain, reflect, lightscreen, crit, burn, helpingHand: false, friendGuard };

  // The hits `move` from slot `u` makes, following the move's real targeting. `up(t)` says whether slot t is
  // still standing and `hpOf(t)` its HP going into the hit, so the turn can be played out in order.
  const hitsFor = (u: number, move: CalcMove | undefined, aim: number, up: (t: number) => boolean = () => true, hpOf: (t: number) => number = (t) => sets[t].hp): DcHit[] => {
    const a = sets[u], mate = mateOf(u);
    if (!a.mon || !move || move.power <= 0) return [];
    // Singles has one foe and no partner: every move is a plain single-target hit.
    const k = doubles ? tgKind(move.target) : "sel";
    if (k === "ally") return [];
    const helped = doubles && mate !== undefined && !!sets[mate].mon && up(mate) && kindOf(mate) === "ally";
    const standing = foesOf(u).filter((t) => sets[t].mon && up(t));
    // A single-target move aimed at a fainted foe switches to its partner, as in the games.
    const single = sets[aim]?.mon && up(aim) ? aim : standing[0];
    const tos = [...(isSpread(k) ? standing : single !== undefined ? [single] : []), ...(k === "all" && mate !== undefined && sets[mate].mon && up(mate) ? [mate] : [])];
    return tos.map((t) => {
      // Screens and Friend Guard sit on the opponent's side; the burn toggle is on your attacker.
      const opp = sideOf(t) === 1;
      const fld = { ...baseField, spread: isSpread(k), helpingHand: helped, reflect: reflect && opp, lightscreen: lightscreen && opp, friendGuard: friendGuard && opp, burn: burn && sideOf(u) === 0 };
      return { from: u, to: t, r: calcHit(a.mon!, a, sets[t].mon!, { ...sets[t], hp: hpOf(t) }, move, fld), ff: sideOf(t) === sideOf(u) };
    });
  };

  const spe = (s: DcSet) => (s.mon ? statFull(s.mon.stats.speed, level, s.iv.spe, s.ev.spe, natMul(s.nat, "spe"), false) : 0);
  // Turn order: move priority first, then Speed.
  const order = active.filter((i) => sets[i].mon)
    .map((i) => ({ i, pri: mvs[i].move?.priority ?? 0, spe: spe(sets[i]) }))
    .sort((x, y) => y.pri - x.pri || y.spe - x.spe);
  const stepOf = (i: number) => order.findIndex((o) => o.i === i) + 1;

  // Play the turn out in order. HP carries over from hit to hit as a range — `lo` if every roll is high,
  // `hi` if every roll is low — starting from each Pokémon's current HP. A Pokémon that is KO'd even on
  // low rolls doesn't get to move, and Focus Sash saves its holder once, from full HP.
  const hp: Record<number, { lo: number; hi: number; sash: boolean }> = {};
  for (const i of active) hp[i] = { lo: sets[i].hp, hi: sets[i].hp, sash: false };
  const standing = (t: number) => hp[t].hi > 0;
  const steps = order.map(({ i }) => {
    if (!standing(i)) return { i, skipped: true, atRisk: false, hits: [] as TurnHit[] };
    const atRisk = hp[i].lo <= 0;
    const hs: TurnHit[] = hitsFor(i, mvs[i].move, aimOf(i), standing, (t) => hp[t].hi).map((h) => {
      const x = hp[h.to], d = sets[h.to];
      if (h.r.te === 0) return { ...h, ko: null, sash: false };
      const sash = d.item === "Focus Sash" && !x.sash && x.lo >= 100 && h.r.maxPct >= 100;
      if (sash) { x.sash = true; x.lo = 1; x.hi = Math.max(1, 100 - h.r.minPct); }
      else { x.lo = Math.max(0, x.lo - h.r.maxPct); x.hi = Math.max(0, x.hi - h.r.minPct); }
      return { ...h, ko: x.hi <= 0 ? "yes" : x.lo <= 0 ? "maybe" : null, sash };
    });
    return { i, skipped: false, atRisk, hits: hs };
  });
  const hits = steps.flatMap((st) => st.hits);
  // Damage taken over the turn, from the HP it started with.
  const takenBy = (i: number) => {
    const all = hits.filter((h) => h.to === i), hs = all.filter((h) => h.r.te !== 0), x = hp[i] ?? { lo: sets[i].hp, hi: sets[i].hp, sash: false };
    return { all, hs, min: sets[i].hp - x.hi, max: sets[i].hp - x.lo, fainted: x.hi <= 0, maybe: x.lo <= 0 && x.hi > 0, sash: x.sash };
  };
  // Dropdown hint: the hardest hit on the other side, plus a warning when it also hits the partner.
  const preview = (u: number) => (m: CalcMove) => {
    const hs = hitsFor(u, m, aimOf(u)), foe = hs.filter((h) => !h.ff).sort((x, y) => y.r.maxPct - x.r.maxPct);
    if (!hs.length) return "";
    return `${foe.length ? ` · ${pctText(foe[0].r)}` : ""}${hs.some((h) => h.ff) ? " · hits partner" : ""}`;
  };
  const involves = (i: number) => i === f || hits.some((h) => (h.from === i && h.to === f) || (h.from === f && h.to === i));

  // Battle-log wording: your Pokémon by name, the opponent's as "the opposing …", like the games.
  const who = (i: number, cap = false) => sideOf(i) === 0
    ? <b>{sets[i].mon?.name}</b>
    : <><span className="opp">{cap ? "The" : "the"} opposing</span> <b>{sets[i].mon?.name}</b></>;
  const logLines = (st: (typeof steps)[number]): ReactNode[] => {
    const i = st.i, m = mvs[i].move; if (!m) return [];
    const out: ReactNode[] = [], mate = mateOf(i);
    if (m.power <= 0) {
      out.push(doubles && kindOf(i) === "ally" && mate !== undefined && sets[mate].mon
        ? <>{who(mate, true)}&apos;s move gets a ×1.5 boost.</>
        : <span className="fx">Status move: no damage.</span>);
    } else if (!st.hits.length) out.push(<span className="fx">But there was no target…</span>);
    for (const h of st.hits) {
      const r = h.r;
      if (r.te === 0) { out.push(<><span className="fx">It doesn&apos;t affect</span> {who(h.to)}…</>); continue; }
      const fx = r.te > 1 ? "It's super effective! " : r.te < 1 ? "It's not very effective… " : "";
      out.push(<>
        {fx && <span className="fx">{fx}</span>}{who(h.to, true)} lost <b className="pct">{pctText(r)}</b> of its HP
        {h.ff && <span className="ffc"> ({sideOf(h.to) === 0 ? "your" : "its"} partner)</span>}.
        {h.sash ? " It hung on using its Focus Sash!" : h.ko === "maybe" ? " It could faint." : ""}
      </>);
      if (h.ko === "yes") out.push(<span className="ko">{who(h.to, true)} fainted!</span>);
    }
    return out;
  };

  const mathHit = hits.find((h) => h.from === f && h.r.te !== 0) ?? hits.find((h) => h.r.te !== 0);
  const mathMove = mathHit ? mvs[mathHit.from].move : undefined;
  // A proposal only stands while its slot still holds the same Pokémon.
  const cb = coach && sets[coach.slot]?.mon?.id === coach.monId ? coach : null;
  const cSet = cb ? sets[cb.slot] : null, cMoves = cb ? mvs[cb.slot] : null;
  // The move Apply will use: the one picked from the moveset chips, else the coach's first damaging move.
  const cMoveIdx = cb?.build && cMoves ? (() => {
    const at = (n: string) => cMoves.moves.findIndex((m) => m.name === n);
    if (cb.pick && at(cb.pick) >= 0) return at(cb.pick);
    const hit = cb.build.moves.map(at).find((i) => i >= 0 && cMoves.moves[i].power > 0);
    return hit ?? cb.build.moves.map(at).find((i) => i >= 0) ?? -1;
  })() : -1;
  const proposed = cb?.build && cSet ? {
    ...cSet,
    abil: cb.build.ability ?? cSet.abil, nat: cb.build.nature ?? cSet.nat, item: cb.build.item ?? cSet.item,
    ev: { ...cb.build.evs }, pre: "Custom",
  } : null;
  const applyCoach = () => {
    if (!cb || !cSet || !cMoves || !proposed) return;
    setCoach({ ...cb, prev: cb.prev ?? { set: cSet, idx: cMoves.idx }, applied: true });
    patchSet(cb.slot, proposed);
    if (cMoveIdx >= 0) cMoves.setIdx(cMoveIdx);
  };
  const revertCoach = () => {
    if (!cb?.prev || !cMoves) return;
    patchSet(cb.slot, cb.prev.set);
    cMoves.setIdx(cb.prev.idx);
    setCoach({ ...cb, prev: undefined, applied: false });
  };
  // The coach box talks about the focused Pokémon; its conversation carries on while that holds.
  const cv = cb && cb.slot === f ? cb : null;
  const coachBusy = !!cv?.turns.some((t) => t.status === "streaming");
  // Damage questions about the focused matchup, answered by the calc itself (no LLM).
  const foe = sets[f].mon ? aimOf(f) : undefined, foeMon = foe !== undefined ? sets[foe].mon : null;
  const calcChips = sets[f].mon && foeMon && foe !== undefined ? [
    ...(mvs[f].move && mvs[f].move.power > 0 ? [`Can ${sets[f].mon.name} OHKO ${foeMon.name}?`] : []),
    ...(mvs[foe].move && mvs[foe].move.power > 0 ? [`How much bulk does ${sets[f].mon.name} need to survive ${foeMon.name}'s ${mvs[foe].move.name}?`] : []),
  ] : [];
  // The calculator as the coach sees it; types, stats and move data are re-read server-side.
  const calcState = (c: typeof cv): CalcAskState => ({
    level, doubles,
    field: { weather, terrain, reflect, lightscreen, crit, burn, friend_guard: friendGuard },
    slots: active.filter((i) => sets[i].mon).map((i) => {
      const s = sets[i], m = s.mon!;
      return {
        slot: i, pokemon_id: m.formId ? m.dex : m.id, form_id: m.formId ?? null, name: m.name, nature: s.nat, evs: s.ev, ivs: s.iv,
        item: s.item, ability: s.abil, hp: s.hp, move: mvs[i].move?.name ?? null, aim: aimOf(i),
      };
    }),
    focus: f,
    hits: hits.flatMap((h) => {
      const m = mvs[h.from].move;
      return m ? [{ attacker: h.from, target: h.to, move: m.name, min_pct: h.r.minPct, max_pct: h.r.maxPct, ko: h.r.ko, te: h.r.te }] : [];
    }),
    proposal: c?.build ? { slot: c.slot, build: c.build, thread: c.turns.filter((t) => t.status === "done").map((t) => ({ ask: t.question, reply: t.answer })) } : null,
  });
  // One question → one streamed turn. A build proposal (for any slot) becomes the card above the chat;
  // a new set goes back to pending, while a reply that leaves the set alone keeps it applied.
  const sendCoach = (text: string) => {
    const q = text.trim(), a = sets[f].mon;
    if (!q || !a || coachBusy) return;
    const id = cv?.id ?? ++coachSeq.current, idx = cv ? cv.turns.length : 0, state = calcState(cv);
    setCoach(cv ? { ...cv, turns: [...cv.turns, startRun(q)] } : { id, slot: f, monId: a.id, turns: [startRun(q)] });
    setCoachInput("");
    const patch = (fn: (t: AskRun) => AskRun) =>
      setCoach((c) => (c?.id === id && c.turns[idx] ? { ...c, turns: c.turns.map((t, j) => (j === idx ? fn(t) : t)) } : c));
    const takeBuild = (v: BuildProposalView) => {
      const mon = sets[v.slot]?.mon; if (!mon) return;
      setCoach((c) => {
        if (c?.id !== id) return c;
        if (v.slot !== c.slot || mon.id !== c.monId) return { ...c, slot: v.slot, monId: mon.id, build: v.build, pick: undefined, applied: false, prev: undefined };
        return sameBuild(v.build, c.build) ? c : { ...c, build: v.build, pick: undefined, applied: false };
      });
      if (v.slot !== f) setFocus(v.slot);
    };
    coachAbort.current?.abort();
    coachAbort.current = streamCalcCoach(q, state, patch, takeBuild);
  };
  // Apply a damage / survive card's fields into the calc (never a saved team); Revert puts the slots back.
  const liveRef = (r: CalcRef) => sets[r.slot]?.mon?.name === r.name;
  const applyCard = (key: string, aps: CalcApply[]) => {
    const before: Record<number, DcSet> = {};
    for (const { slot, fields: p } of aps) {
      const cur = sets[slot]; if (!cur.mon) continue;
      before[slot] = cur;
      patchSet(slot, {
        ...(p.item !== undefined && { item: p.item }), ...(p.ability !== undefined && { abil: p.ability }),
        ...(p.nature !== undefined && { nat: p.nature }), ...(p.evs && { ev: { ...cur.ev, ...p.evs } }),
        ...(p.hp !== undefined && { hp: p.hp }), pre: "Custom",
      });
    }
    setCardPrev((m) => ({ ...m, [key]: before }));
  };
  const revertCard = (key: string) => {
    const before = cardPrev[key]; if (!before) return;
    for (const [slot, set] of Object.entries(before)) patchSet(Number(slot), set);
    setCardPrev((m) => Object.fromEntries(Object.entries(m).filter(([k]) => k !== key)));
  };
  const chip = (on: boolean, set: (v: boolean) => void, label: string, hint: string) => (
    <label className={on ? "on" : ""} title={hint}><input type="checkbox" checked={on} onChange={(e) => set(e.target.checked)} />{label}</label>
  );

  const rosterCard = (i: number) => {
    const s = sets[i], m = mvs[i].move, t = takenBy(i), n = stepOf(i);
    const placeholder = sideOf(i) === 0 ? (i === 0 ? "Your Pokémon" : "Partner") : doubles ? `Foe ${i - 1}` : "Opponent";
    // Removing resets the slot to a fresh set for its side (and keeps focus where it was).
    const remove = () => setSets((ds) => ds.map((d, k) => (k !== i ? d : sideOf(i) === 0 ? newAtk() : newDef())));
    return (
      <div key={i} className="dc-rcw">
      <button className={`dc-rc${i === f ? " on" : ""}${s.mon ? "" : " empty"}${involves(i) ? "" : " faded"}${s.mon && t.fainted ? " ko" : ""}`} onClick={() => setFocus(i)} aria-pressed={i === f}>
        {s.mon ? <img src={monArt(s.mon)} alt="" />/* eslint-disable-line @next/next/no-img-element */ : <span className="add" aria-hidden>+</span>}
        <b>{s.mon?.name ?? placeholder}</b>
        <small>{s.mon ? <>{n > 0 && `#${n} · `}{m?.name ?? "—"}{s.item !== "None" && <span className="itm"> · {s.item}</span>}</> : "tap to pick"}</small>
        {s.mon && (
          <span className="d">
            <em className={t.fainted ? "ko" : !t.hs.length && t.all.length ? "imm" : ""}>{t.fainted ? "KO" : t.hs.length ? `${t.min.toFixed(0)}–${t.max.toFixed(0)}%` : t.all.length ? "immune" : ""}</em>
            <HpLeft min={t.min} max={t.max} hp={s.hp} />
          </span>
        )}
      </button>
      {s.mon && (
        <button className="rm-x" onClick={remove} aria-label={`Remove ${s.mon.name}`} title="Remove">
          <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden><path d="M6 6l12 12M18 6L6 18" /></svg>
        </button>
      )}
      </div>
    );
  };

  // The focused Pokémon's details.
  const s = sets[f], m = mvs[f].move, t = takenBy(f), n = stepOf(f);
  const abilOpts = abilityOptsBySlot[f];
  const k: TgKind = m && doubles ? tgKind(m.target) : "sel";

  return (
    <section className="card dc">
      <div className="lbl">Damage calculator
        <span className="dc-top">
          <span className="dc-seg">{["Singles", "Doubles"].map((x, i) => <button key={x} className={doubles === (i === 1) ? "on" : ""} onClick={() => setDoubles(i === 1)}>{x}</button>)}</span>
          <span className="dc-seg">{[50, 100].map((L) => <button key={L} className={level === L ? "on" : ""} onClick={() => setLevel(L)}>Lv{L}</button>)}</span>
        </span>
      </div>
      <div className="dc-v2">
        <div className="dc-main">
          <div className="dc-ros">
            <div className="col"><span className="dc-k">Your team</span>{active.filter((i) => sideOf(i) === 0).map(rosterCard)}</div>
            <div className="col them"><span className="dc-k">Opponent</span>{active.filter((i) => sideOf(i) === 1).map(rosterCard)}</div>
          </div>
          {order.length > 0 && (
            <div className="dc-log">
              <span className="dc-k">This turn · priority › speed</span>
              {order.map((o, idx) => {
                const mv = mvs[o.i].move, st = steps[idx];
                const tie = order.some((x) => x.i !== o.i && x.pri === o.pri && x.spe === o.spe);
                return (
                  <button key={o.i} className={`dc-ls${o.i === f ? " on" : ""}${involves(o.i) ? "" : " faded"}`} onClick={() => setFocus(o.i)}>
                    <span className="n">{idx + 1}</span>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={monArt(sets[o.i].mon!)} alt="" />
                    <span className="tx">
                      {st.skipped
                        ? <span className="u gone">{who(o.i, true)} fainted before it could move.</span>
                        : <span className="u">{who(o.i, true)} used <b>{mv?.name ?? "…"}</b>!
                            {o.pri !== 0 && <em>{o.pri > 0 ? "+" : ""}{o.pri}</em>}{tie && <em>speed tie</em>}{st.atRisk && <em>if it&apos;s still standing</em>}
                          </span>}
                      {!st.skipped && logLines(st).map((l, j) => <span key={j} className="l">{l}</span>)}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="dc-panel" key={f}>
          <span className="dc-k">{sideOf(f) === 0 ? "Your team" : "Opponent"}{doubles ? ` · ${SLOT_ROLE[f]}` : ""}{n > 0 && ` · moves ${ORD[n - 1]}`}</span>
          <div className="dc-ph">
            <DcPicker mon={s.mon} onPick={(p) => loadCalcMon(p.dex_number, p.form_id).then((mm) => pickMon(f, mm)).catch(() => {})} ph="Pick a Pokémon…" />
            {s.mon && <span className="dc-start"><HpPicker value={s.hp} onChange={(hp) => patchSet(f, { hp })} /></span>}
          </div>
          {s.mon && (
            <>
              <div className="dc-hpnow">
                <span className="dc-k">After turn{t.sash ? <em className="warn"> · Sash holds</em> : t.fainted ? <em> · KO</em> : t.maybe ? <em> · maybe KO</em> : null}</span>
                <HpLeft min={t.min} max={t.max} hp={s.hp} />
              </div>
              <div className="dc-c2">
                {/* left: what it does — move, target, nature, item, ability */}
                <div className="l">
                  <InfoBox
                    className="se-mv"
                    label={m ? <><i style={{ background: TC[m.type] ?? "#999" }} />{m.type}</> : "Move"}
                    name={m?.name ?? (mvs[f].moves.length ? "Pick a move" : "Loading moves…")}
                    meta={m ? `${m.damage_class === "status" ? "status" : `${m.damage_class} ${m.power}`}${m.accuracy ? ` · ${m.accuracy}%` : ""}${m.priority ? ` · ${m.priority > 0 ? "+" : ""}${m.priority}` : ""}${doubles ? ` · ${TG_LABEL[k]}${isSpread(k) ? " ×0.75" : ""}` : ""}` : undefined}
                    desc={m?.effect ?? undefined}
                    editing={editing === `${f}:move`}
                    onOpen={() => setEditing(`${f}:move`)}
                  >
                    <MoveSearch moves={mvs[f].moves} value={m?.name ?? null} onPick={(mm) => mvs[f].setIdx(mvs[f].moves.indexOf(mm))} onDone={() => setEditing(null)} autoFocus owner={s.mon.name} preview={preview(f)} />
                  </InfoBox>
                  {doubles && m && m.power > 0 && isAimable(k) && targetsOf(f).length > 1 && (
                    <div className="dc-aim">
                      <span className="dc-k">Target</span>
                      <span className="dc-aimseg" role="radiogroup" aria-label="Target">
                        {targetsOf(f).map((d) => (
                          <button key={d} role="radio" aria-checked={aimOf(f) === d} className={aimOf(f) === d ? "on" : ""} onClick={() => setAims((xs) => xs.map((x, j) => (j === f ? d : x)))}>
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={monArt(sets[d].mon!)} alt="" />{sets[d].mon!.name}
                          </button>
                        ))}
                      </span>
                      {k === "rand" && <span className="fx">random target · previewing</span>}
                    </div>
                  )}
                  <div className="se-infos">
                    <InfoBox
                      label="Ability"
                      name={s.abil}
                      meta={ABIL_HINT[s.abil] ?? (abilOpts.find((o) => o.v === s.abil)?.off ? "no damage effect" : undefined)}
                      desc={abilOpts.find((o) => o.v === s.abil)?.hint}
                      editing={editing === `${f}:abil`}
                      onOpen={() => setEditing(`${f}:abil`)}
                    >
                      <PickSearch bare autoFocus label="Ability" value={s.abil} opts={abilOpts} onPick={(v) => patchSet(f, { abil: v })} onDone={() => setEditing(null)} />
                    </InfoBox>
                    <InfoBox
                      label="Nature"
                      name={s.nat}
                      meta={natTag(s.nat)}
                      desc={natDesc(s.nat)}
                      editing={editing === `${f}:nat`}
                      onOpen={() => setEditing(`${f}:nat`)}
                    >
                      <PickSearch bare autoFocus label="Nature" value={s.nat} opts={NAT_OPTS} onPick={(v) => patchSet(f, { nat: v, pre: "Custom" })} onDone={() => setEditing(null)} />
                    </InfoBox>
                    <InfoBox
                      label="Item"
                      name={s.item === "None" ? "No item" : s.item}
                      meta={s.item === "None" ? undefined : DC_ITEM_INFO.find((i) => i.name === s.item)?.note ?? "no damage effect"}
                      desc={s.item === "None" ? undefined : itemInfo.get(s.item)}
                      editing={editing === `${f}:item`}
                      onOpen={() => setEditing(`${f}:item`)}
                    >
                      <PickSearch bare autoFocus label="Item" value={s.item} opts={ITEM_OPTS} search={searchAllItems} onPick={(v) => patchSet(f, { item: v })} onDone={() => setEditing(null)} />
                    </InfoBox>
                  </div>
                </div>
                {/* right: the stats it has */}
                <div className="r">
                  <div className="dc-sth">
                    <span className="dc-k">Stats · Lv{level}</span>
                    <span className="dc-seg">{["Offensive", "Bulky", "Custom"].map((x) => (
                      <button key={x} className={s.pre === x ? "on" : ""} onClick={() => (x === "Custom" ? patchSet(f, { pre: "Custom" }) : applyPre(f, x))}>{x}</button>
                    ))}</span>
                  </div>
                  <EvEditor mon={s.mon} level={level} nat={s.nat} ev={s.ev} iv={s.iv} onEv={(e) => patchSet(f, { ev: e, pre: "Custom" })} onIv={(v) => patchSet(f, { iv: v, pre: "Custom" })} />
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="dc-subrow">
        <button className="dc-optbtn" onClick={() => setOpen((v) => !v)}>{open ? "hide field ▴" : "field — weather · screens · crit ▾"}</button>
        <button className="dc-optbtn" onClick={() => setShowMath((v) => !v)}>{showMath ? "hide math ▴" : "math ▾"}</button>
      </div>
      {open && (
        <div className="dc-drawer">
          <div className="dc-field">
            <select value={weather} onChange={(e) => setWeather(e.target.value)}>{WEATHER.map((x) => <option key={x}>{x === "None" ? "Weather" : x}</option>)}</select>
            <select value={terrain} onChange={(e) => setTerrain(e.target.value)}>{TERRAIN.map((x) => <option key={x}>{x === "None" ? "Terrain" : x}</option>)}</select>
            {chip(reflect, setReflect, "Foe Reflect", doubles ? "On the opponent's side · ×0.667 in doubles" : "On the opponent's side · ×0.5 in singles")}
            {chip(lightscreen, setLightscreen, "Foe Light Screen", doubles ? "On the opponent's side · ×0.667 in doubles" : "On the opponent's side · ×0.5 in singles")}
            {chip(crit, setCrit, "Crit", "Every hit crits: ×1.5, ignores screens")}
            {chip(burn, setBurn, "Your side burned", "Halves your physical damage unless Guts")}
            {doubles && chip(friendGuard, setFriendGuard, "Foe Friend Guard ×0.75", "The opponent's partner has Friend Guard")}
          </div>
        </div>
      )}
      {showMath && mathHit && mathMove && (
        <div className="dc-formula dc-formula-top">dmg = ⌊(⌊(2·{level}/5+2)·{mathMove.power}·{mathHit.r.A}/{mathHit.r.D}⌋/50)+2⌋ × {mathHit.r.stab} STAB × {fmt(mathHit.r.te)} type × [0.85–1.0] = <b>{mathHit.r.base}</b> base → <b>{mathHit.r.minPct.toFixed(1)}–{mathHit.r.maxPct.toFixed(1)}%</b> ({sets[mathHit.from].mon?.name} → {sets[mathHit.to].mon?.name})</div>
      )}
      {s.mon && (
        <div className="dc-coach" role="region" aria-label="Coach">
          {cv?.build && cSet && proposed ? ((cb, cSet) => {
            // "Was" is what the calc has now — or, once applied, what the coach replaced.
            const base = cb.applied && cb.prev ? cb.prev.set : cSet;
            const wasMove = cb.applied && cb.prev ? mvs[cb.slot].moves[cb.prev.idx]?.name : cMoves?.move?.name;
            const rows: [string, string | undefined, string | undefined][] = [
              ["Move", wasMove, cMoveIdx >= 0 ? cMoves?.moves[cMoveIdx]?.name : undefined],
              ["Ability", base.abil, proposed.abil],
              ["Nature", base.nat, proposed.nat],
              ["Item", base.item, proposed.item],
            ];
            const evSame = evText(base.ev) === evText(proposed.ev);
            return (
              <>
                <div className="dc-coach-h">
                  <span className="t">{cb.applied ? "Applied: " : "Coach's build for "}<b>{cSet.mon?.name}</b></span>
                  <span className="acts">
                    {cb.prev && <button className="rev" onClick={revertCoach}>Revert</button>}
                    {!cb.applied && <button className="ok" onClick={applyCoach}>Apply build</button>}
                    <button className="x" onClick={() => setCoach(null)} aria-label="Dismiss">×</button>
                  </span>
                </div>
                <div className="dc-coach-diff">
                  {rows.map(([k, was, now]) => (
                    <div key={k} className={was === now || !now ? "same" : "chg"}>
                      <span className="dc-k">{k}</span>
                      {!now || was === now ? <span className="v">{was === "None" ? "No item" : was ?? "—"}</span> : <span className="v"><s>{was === "None" ? "No item" : was ?? "—"}</s> → <b>{now}</b></span>}
                    </div>
                  ))}
                  <div className={`wide ${evSame ? "same" : "chg"}`}>
                    <span className="dc-k">EVs</span>
                    <span className="dc-evdiff">
                      {(Object.keys(proposed.ev) as SKey[]).filter((k) => base.ev[k] || proposed.ev[k]).map((k) => (
                        <span key={k} className={base.ev[k] === proposed.ev[k] ? "ev same" : "ev"}>
                          <em>{SABBR[k]}</em>
                          {base.ev[k] === proposed.ev[k] ? proposed.ev[k] : <><s>{base.ev[k]}</s> → <b>{proposed.ev[k]}</b></>}
                        </span>
                      ))}
                    </span>
                  </div>
                </div>
                <div className="dc-coach-set">
                  <span className="dc-k">Full moveset</span>
                  {cb.build!.moves.map((n) => {
                    const i = cMoves?.moves.findIndex((m) => m.name === n) ?? -1, mv = i >= 0 ? cMoves!.moves[i] : undefined;
                    return (
                      <button
                        key={n}
                        className={(cb.applied ? cMoves?.move?.name === n : cMoveIdx === i) ? "on" : ""}
                        disabled={i < 0}
                        // Before Apply a chip picks the move to apply; after, it swaps the calc's move directly.
                        onClick={() => (cb.applied ? cMoves?.setIdx(i) : setCoach({ ...cb, pick: n }))}
                        title={mv ? (cb.applied ? `Use ${n} in the calc` : `Apply with ${n}`) : n}
                      >
                        {mv && <i style={{ background: TC[mv.type] ?? "#999" }} />}{n}
                      </button>
                    );
                  })}
                </div>
              </>
            );
          })(cv, cSet) : (
            <div className="dc-coach-h"><span className="t">Ask the coach about <b>{s.mon.name}</b></span></div>
          )}
          {cv && cv.turns.length > 0 && (
            <div className="dc-coach-chat" ref={coachChatRef} data-lenis-prevent>
              {cv.turns.map((t, j) => (
                <div key={j} className={j < cv.turns.length - 1 ? "turn old" : "turn"}>
                  <p className="you">{t.question}</p>
                  <PlanSteps
                    key={`${cv.id}-${j}`}
                    compact
                    steps={t.steps}
                    planner={t.planner}
                    cached={t.cached}
                    status={t.status}
                    elapsed={t.elapsed}
                    usage={t.usage}
                    answering={t.answer.length > 0}
                  />
                  {/* Same light Markdown as the Ask answers and the team coach. */}
                  {/* No sources list in this box, so the [n] markers would point nowhere. */}
                  {t.answer ? <div className="coach">{renderAnswer(t.answer.replace(/ ?\[\d+(?:,\s*\d+)*\]/g, ""))}</div>
                    : t.status === "streaming" ? <p className="coach wait">Coach is thinking…</p> : null}
                  {t.status === "error" && <p className="coach err">{t.error}</p>}
                  {t.views.map((v, k) => {
                    const key = `${cv.id}:${j}:${k}`, acts = { applied: key in cardPrev, onRevert: () => revertCard(key) };
                    switch (v.kind) {
                      case "damage":
                        return <DamageCard key={k} view={v} {...acts} live={liveRef(v.attacker) && liveRef(v.defender)} onApply={() => applyCard(key, v.apply)} />;
                      case "survive":
                        return <SurviveCard key={k} view={v} {...acts} live={liveRef(v.defender)} onApply={() => v.apply && applyCard(key, [v.apply])} />;
                      case "build_proposal":
                        return null; // shown as the build card above
                      default:
                        return <div key={k} className="dc-cv"><ViewBlock view={v} link={NO_LINK} /></div>;
                    }
                  })}
                </div>
              ))}
            </div>
          )}
          <div className="dc-coach-quick">
            {[...(cv?.build ? COACH_QUICK : COACH_START), ...calcChips].map((q) => (
              <button key={q} onClick={() => sendCoach(q)} disabled={coachBusy}>{q}</button>
            ))}
          </div>
          <form className="dc-coach-in" onSubmit={(e) => { e.preventDefault(); sendCoach(coachInput); }}>
            <input
              value={coachInput}
              onChange={(e) => setCoachInput(e.target.value)}
              placeholder={cv?.build ? `Ask a follow-up, e.g. "swap ${cv.build.moves.at(-1) ?? "a move"} for a priority move"` : `What should ${s.mon.name} do? e.g. "a bulky set for doubles"`}
              aria-label="Message the coach"
              disabled={coachBusy}
            />
            <button type="submit" disabled={coachBusy || !coachInput.trim()}>Send</button>
          </form>
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
          <Search />
        </header>

        {/* three column stacks; below 1440px the columns flatten (display:contents)
            and the tiles are placed on a 12-col grid instead */}
        <div className="lc-bento">
          <div className="col c1">
            <div className="ga ga-coach"><TeamCoachTile /></div>
            <div className="ga ga-tc"><TypeCalcTile /></div>
          </div>
          <div className="col c2">
            <div className="ga ga-ask"><AskTile /></div>
            <div className="ga ga-dc"><DamageCalcTile /></div>
          </div>
          <div className="col c3">
            <div className="ga ga-look"><LookupTile /></div>
            <div className="ga ga-nat"><NatureTile /></div>
            <div className="ga ga-cr"><CatchRateTile /></div>
          </div>
        </div>
      </div>
    </main>
  );
}
