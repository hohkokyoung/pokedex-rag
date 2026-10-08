"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import Dropdown from "@/components/Dropdown";
import { getMoveLearnersByGame, type GameLearner, type LearnMethod, type MoveGameLearners, thumb } from "@/lib/api";
import { typeChip } from "@/lib/pokeTypes";
import { Tag } from "@/components/calc/fields";
import { useDialogFocus } from "@/hooks/useDialogFocus";

/**
 * Per-game "who learns this move" for the home lookup's show-all modal: method tabs
 * (the Moveset panel's), a game picker, an optional level cut-off that splits the
 * level-up grid into ready / later, and a search that answers "can X learn it?".
 */

type Group = { key: string; label: string; methods: string[] };
const GROUPS: Group[] = [
  { key: "level", label: "Level-up", methods: ["level-up"] },
  { key: "egg", label: "Egg", methods: ["egg", "light-ball-egg"] },
  { key: "tm", label: "TM / HM", methods: ["machine"] },
  { key: "tutor", label: "Tutor", methods: ["tutor"] },
];
const KNOWN = new Set(GROUPS.flatMap((g) => g.methods));
const ALL_GROUPS: Group[] = [...GROUPS, { key: "other", label: "Other", methods: [] }];
const inGroup = (g: Group, method: string) => (g.key === "other" ? !KNOWN.has(method) : g.methods.includes(method));
const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"];
const levelOf = (l: GameLearner) => l.methods.find((m) => m.method === "level-up")?.level ?? null;

/** Fetches the learners while `enabled`; `setGame(null)` = any game (the default). */
export function useGameLearners(moveId: number | null, enabled: boolean, initialGame: number | null = null) {
  // The chosen game belongs to one move; picking another move falls back to newest.
  const [pick, setPick] = useState<{ move: number | null; game: number | null }>({ move: initialGame != null ? moveId : null, game: initialGame });
  const game = pick.move === moveId ? pick.game : null;
  const [res, setRes] = useState<MoveGameLearners | null>(null);
  useEffect(() => {
    if (!enabled || moveId == null) return;
    let alive = true;
    getMoveLearnersByGame(moveId, game)
      .then((d) => alive && setRes(d))
      .catch(() => alive && setRes(null));
    return () => { alive = false; };
  }, [moveId, game, enabled]);
  // Keep showing this move's previous game while the next one loads (no flash).
  const data = res && res.move_id === moveId ? res : null;
  return { data, setGame: (id: number | null) => setPick({ move: moveId, game: id }) };
}

export default function MoveLearnersPanel({
  moveName,
  data,
  setGame,
  onPick,
}: {
  moveName: string;
  data: MoveGameLearners | null;
  setGame: (id: number | null) => void;
  onPick: () => void;
}) {
  const [tab, setTab] = useState("level");
  const [lvCap, setCap] = useState<number | null>(null);
  const [q, setQ] = useState("");

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const g of ALL_GROUPS) c[g.key] = (data?.learners ?? []).filter((l) => l.methods.some((m) => inGroup(g, m.method))).length;
    return c;
  }, [data]);

  if (!data) return <div className="lc-modal-grid"><div className="lc-modal-empty">Loading learners…</div></div>;

  const game = data.games.find((g) => g.id === data.version_group_id);
  const tabs = ALL_GROUPS.filter((g) => counts[g.key]);
  const active = tabs.find((g) => g.key === tab) ?? tabs[0];
  const f = q.trim().toLowerCase();

  const lv = (n: number | null) => (n === 0 ? "Evo" : `Lv.${n}`);
  const label = (l: GameLearner, m: LearnMethod) =>
    m.method === "level-up"
      ? m.level_max != null && m.level_max !== m.level ? `${lv(m.level)}–${m.level_max}` : lv(m.level)
    : m.method === "machine" ? data.machine ?? "TM"
    : m.method === "egg" || m.method === "light-ball-egg" ? "Egg"
    : m.method === "tutor" ? "Tutor"
    : m.method.replace(/-/g, " ");
  // Searching looks across every method; otherwise the active tab filters.
  const matchName = (l: GameLearner) => [l.name, ...l.also].find((n) => n.toLowerCase().includes(f));
  const list = f
    ? data.learners.filter((l) => matchName(l))
    : data.learners
        .filter((l) => active && l.methods.some((m) => inGroup(active, m.method)))
        // Level-up keeps the API's level order; other tabs read best in dex order.
        .sort((a, b) => (active?.key === "level" ? 0 : a.dex_number - b.dex_number || (a.form_id ?? 0) - (b.form_id ?? 0)));
  const split = !f && active?.key === "level" && lvCap != null;
  const ready = split ? list.filter((l) => (levelOf(l) ?? 0) <= lvCap!) : list;
  const later = split ? list.filter((l) => (levelOf(l) ?? 0) > lvCap!) : [];

  const tile = (l: GameLearner, late = false) => {
    const shown = f ? matchName(l) ?? l.name : l.name;
    const ms = f ? l.methods : l.methods.filter((m) => active && inGroup(active, m.method));
    const href = l.form_id ? `/pokedex/${l.dex_number}?form=${l.form_id}` : `/pokedex/${l.dex_number}`;
    return (
      <Link key={l.id} href={href} title={[l.name, ...l.also].join(" · ")} onClick={onPick} className={late ? "is-late" : undefined}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img loading="lazy" decoding="async" src={thumb(l.sprite_url, 160)} alt={shown} />
        <span>{shown}</span>
        <span className="tps-mini">{l.types.map((t) => <Tag key={t} t={t} />)}</span>
        <em className="lc-ml-how">{ms.map((m) => label(l, m)).join(" · ")}</em>
      </Link>
    );
  };

  return (
    <>
      <div className="lc-modal-sub lc-ml-sub">
        <div className="lc-ml-bar">
          {f ? (
            <div className="lc-ml-div">Every way it learns it<span>{list.length}</span></div>
          ) : (
            <div className="mv-tabs">
              {tabs.map((g) => (
                <button key={g.key} className={`mv-tab${g.key === active?.key ? " on" : ""}`} onClick={() => setTab(g.key)}>
                  {g.label}<span className="c">{counts[g.key]}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="lc-ml-row">
          <input autoFocus aria-label="Check whether a Pokémon can learn this move" placeholder="Can it learn it? Type a Pokémon…" value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="lc-ml-ctl">
            <Dropdown
              label="Game"
              prefix="Game"
              options={[
                { value: 0, label: "Any game", hint: `Every game · ${data.total} species` },
                ...data.games.map((g) => ({ value: g.id, label: g.name, hint: `Generation ${ROMAN[g.generation] ?? g.generation} · ${g.learners} species` })),
              ]}
              value={[data.version_group_id ?? 0]}
              onChange={([v]) => v != null && setGame(v === 0 ? null : v)}
              align="right"
            />
            {active?.key === "level" && !f && (
              <label className="pk-dd__btn lc-ml-lv">
                <span className="k">By level</span>
                <input type="text" inputMode="numeric" placeholder="Any" value={lvCap ?? ""} aria-label="Your level (empty = any level)"
                  onFocus={(e) => e.currentTarget.select()}
                  onChange={(e) => {
                    const v = e.target.value.replace(/\D/g, "");
                    setCap(v === "" ? null : Math.max(1, Math.min(100, +v)));
                  }} />
                <button type="button" className="lc-ml-clear" onClick={() => setCap(null)} aria-label="Show all levels"
                  tabIndex={lvCap == null ? -1 : 0} style={{ visibility: lvCap == null ? "hidden" : "visible" }}>✕</button>
              </label>
            )}
          </div>
        </div>
        {!data.machine && data.last_machine && game && (
          <div className="lc-ml-note">Not a TM in {game.name} · was {data.last_machine} up to {data.last_machine_game}</div>
        )}
      </div>
      <div className="lc-modal-grid" data-lenis-prevent>
        {split && ready.length > 0 && <div className="lc-ml-div">Ready by Lv.{lvCap}<span>{ready.length}</span></div>}
        {ready.map((l) => tile(l))}
        {later.length > 0 && <div className="lc-ml-div is-late">Learns after Lv.{lvCap}<span>{later.length}</span></div>}
        {later.map((l) => tile(l, true))}
        {list.length === 0 && (
          <div className="lc-modal-empty">
            {f ? <>No Pokémon matching “{q.trim()}” learns {moveName} in {game?.name ?? "any game"}.</> : <>No learners in {game?.name ?? "any game"}.</>}
          </div>
        )}
      </div>
    </>
  );
}

export type ModalMove = {
  id: number;
  name: string;
  type: string | null;
  /** Display category, e.g. "Physical". */
  category: string | null;
  power: number | null;
  accuracy: number | null;
  pp: number | null;
  effect: string | null;
  sub?: string | null;
};

const dash = (v: number | null | undefined) => (v == null ? "—" : String(v));

/** The move's "who learns it" modal — shared by the home lookup and the Moveset panel. */
export function MoveLearnersModal({
  move,
  onClose,
  onBack,
  emptyNote,
  initialGame = null,
}: {
  move: ModalMove;
  /** Open on this game (e.g. the one the Pokédex moveset is showing); default any game. */
  initialGame?: number | null;
  onClose: () => void;
  /** When set, a ‹ Back button (and Escape) returns to whatever opened this modal. */
  onBack?: () => void;
  /** Shown instead of the learner grid when no Pokémon learns the move (Z-Moves …). */
  emptyNote?: ReactNode;
}) {
  const dialogRef = useDialogFocus(true);
  const { data, setGame } = useGameLearners(move.id, true, initialGame);
  const game = data?.games.find((g) => g.id === data.version_group_id);

  // Close on Escape and lock the page (Lenis) scroll while open. The latest
  // onClose lives in a ref so callers needn't memoise it.
  const closeRef = useRef(onBack ?? onClose);
  useEffect(() => { closeRef.current = onBack ?? onClose; });
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") closeRef.current(); };
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
  }, []);

  if (typeof document === "undefined") return null;
  return createPortal(
    <div ref={dialogRef} className="lc-modal" onClick={onClose} role="dialog" aria-modal="true" aria-label={`Pokémon that learn ${move.name}`} data-lenis-prevent>
      <div className="lc-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="lc-modal-top">
          <div className="lc-modal-head">
            {onBack && <button className="lc-modal-back" onClick={onBack} aria-label="Back" title="Back"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M15 5l-7 7 7 7" /></svg></button>}
            {move.type && <span className="lc-tt" style={typeChip(move.type)}>{move.type}</span>}
            <b>{move.name}</b>
            <span className="sub">{data && data.games.length ? (game ? `${game.learners} species in ${game.name}` : `${data.total} species in any game`) : ""}</span>
            <button className="x" onClick={onClose} aria-label="Close">×</button>
          </div>
          <div className="lc-modal-meta">
            <span><b>{move.category ?? "—"}</b></span>
            <span>Power <b>{dash(move.power)}</b></span>
            <span>Acc <b>{dash(move.accuracy)}</b>{move.accuracy != null ? "%" : ""}</span>
            <span>PP <b>{dash(move.pp)}</b></span>
          </div>
          {move.effect && <p className="lc-modal-desc">{move.effect}</p>}
          {move.sub && <p className="lc-modal-desc lc-modal-desc--flavor">{move.sub}</p>}
        </div>
        {data && data.games.length === 0 ? (
          <div className="lc-modal-sub" style={{ paddingBottom: 18 }}>
            {emptyNote ?? <p className="lc-modal-desc" style={{ marginTop: 0 }}>No Pokémon learns {move.name}.</p>}
          </div>
        ) : (
          <MoveLearnersPanel moveName={move.name} data={data} setGame={setGame} onPick={onClose} />
        )}
      </div>
    </div>,
    document.body,
  );
}
