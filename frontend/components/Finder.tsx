"use client";

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import Dropdown from "@/components/Dropdown";
import { listAllAbilities, listAllItems, listAllMoves, listMoveGames, type ItemResult, type MoveGame, type MoveResult } from "@/lib/api";
import type { Ability } from "@/lib/types";
import { TYPE_HEX, TYPE_ORDER, typeHex } from "@/lib/pokeTypes";

/**
 * The home lookup's advanced finder: every move, ability or item (a radio switch
 * picks which), each with its own filters — the catalog toolbar's controls in the
 * lookup's modal shell. Picking a row hands it back to the lookup, which opens the
 * same modal a lookup result would.
 */
export type FinderKind = "move" | "ability" | "item";
const KINDS: { key: FinderKind; label: string; noun: string }[] = [
  { key: "move", label: "Moves", noun: "moves" },
  { key: "ability", label: "Abilities", noun: "abilities" },
  { key: "item", label: "Items", noun: "items" },
];

type MoveSort = "power" | "pp" | "accuracy" | "name";
type ItemSort = "name" | "cost" | "fling_power";
const CATS = [
  { value: "physical", label: "Physical" },
  { value: "special", label: "Special" },
  { value: "status", label: "Status" },
];
const CAT_SHORT: Record<string, string> = { physical: "PHY", special: "SPE", status: "STA" };
type MoveKind = "regular" | "z" | "max";
const KINDS_OF_MOVE: { value: MoveKind; label: string }[] = [
  { value: "regular", label: "Regular" },
  { value: "z", label: "Z-Move" },
  { value: "max", label: "Max Move" },
];
// Z-Moves are the 1-PP moves, bar these three ordinary ones; Max Moves are named "(G-)Max …".
const ORDINARY_ONE_PP = new Set(["struggle", "sketch", "revival-blessing"]);
const kindOf = (m: MoveResult): MoveKind =>
  /^(G-)?Max /.test(m.name) ? "max" : m.pp === 1 && !ORDINARY_ONE_PP.has(m.identifier) ? "z" : "regular";

/** A finder row: the generic Z-Moves are stored twice (a physical and a special copy),
 *  so same-named moves fold into one row carrying every category. */
type FinderMove = MoveResult & { kind: MoveKind; classes: string[] };
function foldMoves(ms: MoveResult[]): FinderMove[] {
  const byName = new Map<string, FinderMove>();
  for (const m of ms) {
    const hit = byName.get(m.name);
    if (hit) {
      if (m.damage_class && !hit.classes.includes(m.damage_class)) hit.classes.push(m.damage_class);
    } else {
      byName.set(m.name, { ...m, kind: kindOf(m), classes: m.damage_class ? [m.damage_class] : [] });
    }
  }
  return [...byName.values()];
}
const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"];
// Nothing "learns" Z-Moves or Max Moves, so the learnset-based game lists miss them:
// they belong to the games that had the mechanic.
const KIND_GAMES: Partial<Record<MoveKind, string[]>> = {
  z: ["sun-moon", "ultra-sun-ultra-moon"],
  max: ["sword-shield"],
};
const ANY_GAME = 0;
const dash = (v: number | null | undefined) => (v == null ? "—" : String(v));

// Each catalog is fixed at runtime: fetch once per page load (a failure retries next open).
function once<T>(load: () => Promise<T>): () => Promise<T> {
  let p: Promise<T> | null = null;
  return () => (p ??= load().catch((e) => { p = null; throw e; }));
}
const loadMoves = once(() => listAllMoves().then(foldMoves));
const loadAbilities = once(listAllAbilities);
const loadItems = once(listAllItems);
const loadGames = once(listMoveGames);

function useCatalog<T>(load: () => Promise<T[]>) {
  const [rows, setRows] = useState<T[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let alive = true;
    load().then((r) => alive && setRows(r)).catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, [load]);
  return { rows, failed };
}

/** Sort by a numeric field; rows without it sink either way, ties by name. */
function byField<T extends { name: string }>(get: (r: T) => number | null | undefined, dir: number) {
  return (a: T, b: T) => {
    const av = get(a), bv = get(b);
    if (av == null || bv == null) return av == null && bv == null ? a.name.localeCompare(b.name) : av == null ? 1 : -1;
    return dir * (av - bv) || a.name.localeCompare(b.name);
  };
}

/** A sortable column header: clicking the active column flips it; another sorts by it. */
function SortHead<S extends string>({ s, label, cls = "n", sort, order, onSort }: {
  s: S; label: string; cls?: string; sort: S; order: "asc" | "desc"; onSort: (s: S) => void;
}) {
  return (
    <button type="button" className={`${cls}${sort === s ? " on" : ""}`} onClick={() => onSort(s)} aria-label={`Sort by ${label}`}>
      {label}{sort === s && <i aria-hidden>{order === "asc" ? "↑" : "↓"}</i>}
    </button>
  );
}

export default function Finder({
  hidden = false,
  initialQuery = "",
  initialKind = "move",
  onPickMove,
  onPickAbility,
  onPickItem,
  onClose,
}: {
  /** Stay mounted but out of sight (a picked row's modal is on top) so filters,
   *  search and scroll survive the trip back. */
  hidden?: boolean;
  initialQuery?: string;
  initialKind?: FinderKind;
  onPickMove: (m: MoveResult) => void;
  onPickAbility: (a: Ability) => void;
  onPickItem: (i: ItemResult) => void;
  onClose: () => void;
}) {
  const [kind, setKind] = useState<FinderKind>(initialKind);
  // One search box shared by all three, so switching keeps what you typed.
  const [q, setQ] = useState(initialQuery);
  const query = q.trim().toLowerCase();
  // Effect text matches at a word start, so "rain" finds Drizzle but not "terrain".
  const inEffect = useMemo(() => {
    const re = new RegExp(`\\b${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i");
    return (text: string | null | undefined) => !!text && re.test(text);
  }, [query]);

  const moves = useCatalog(loadMoves);
  const abilities = useCatalog(loadAbilities);
  const items = useCatalog(loadItems);
  const games = useCatalog(loadGames);

  // Moves: type chips + category + sort.
  const [types, setTypes] = useState<string[]>([]);
  const [cats, setCats] = useState<string[]>([]);
  const [moveKinds, setMoveKinds] = useState<MoveKind[]>([]);
  const [game, setGame] = useState<number>(ANY_GAME);
  const [moveSort, setMoveSort] = useState<MoveSort>("power");
  const [moveOrder, setMoveOrder] = useState<"asc" | "desc">("desc");
  // Abilities: A–Z / Z–A.
  const [abilityOrder, setAbilityOrder] = useState<"asc" | "desc">("asc");
  // Items: category + sort.
  const [itemCats, setItemCats] = useState<string[]>([]);
  const [itemSort, setItemSort] = useState<ItemSort>("name");
  const [itemOrder, setItemOrder] = useState<"asc" | "desc">("asc");

  // Close on Escape and lock the page (Lenis) scroll while open (as MoveLearnersModal).
  const closeRef = useRef(onClose);
  const hiddenRef = useRef(hidden);
  useEffect(() => { closeRef.current = onClose; hiddenRef.current = hidden; });
  useEffect(() => {
    // While hidden, Escape belongs to the modal on top (which returns here).
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && !hiddenRef.current) closeRef.current(); };
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

  const gameOptions = useMemo(
    () => [
      { value: ANY_GAME, label: "Any game", hint: "Every move in the database" },
      ...(games.rows ?? []).map((g) => ({
        value: g.id,
        label: g.name,
        hint: `Generation ${ROMAN[g.generation] ?? g.generation} · ${g.move_ids.length} moves`,
      })),
    ],
    [games.rows],
  );
  // The picked game's moves, or null for any game.
  const inGame = useMemo(() => {
    const g = games.rows?.find((x: MoveGame) => x.id === game);
    return g ? { ids: new Set(g.move_ids), identifier: g.identifier } : null;
  }, [games.rows, game]);

  const moveRows = useMemo(() => {
    const out = (moves.rows ?? []).filter(
      (m) =>
        (!query || m.name.toLowerCase().includes(query)) &&
        (!types.length || (m.type != null && types.includes(m.type))) &&
        (!cats.length || m.classes.some((c) => cats.includes(c))) &&
        (!moveKinds.length || moveKinds.includes(m.kind)) &&
        (!inGame || inGame.ids.has(m.id) || !!KIND_GAMES[m.kind]?.includes(inGame.identifier)),
    );
    const dir = moveOrder === "asc" ? 1 : -1;
    return out.sort(moveSort === "name" ? (a, b) => dir * a.name.localeCompare(b.name) : byField((m) => m[moveSort], dir));
  }, [moves.rows, query, types, cats, moveKinds, inGame, moveSort, moveOrder]);

  const abilityRows = useMemo(() => {
    // Matches the effect text too, so "rain" finds Swift Swim and Drizzle.
    const out = (abilities.rows ?? []).filter(
      (a) => !query || a.name.toLowerCase().includes(query) || inEffect(a.short_effect ?? a.effect),
    );
    const dir = abilityOrder === "asc" ? 1 : -1;
    return out.sort((a, b) => dir * a.name.localeCompare(b.name));
  }, [abilities.rows, query, inEffect, abilityOrder]);

  // Item categories, most-populated first.
  const itemCatOptions = useMemo(() => {
    const n = new Map<string, number>();
    for (const i of items.rows ?? []) if (i.category) n.set(i.category, (n.get(i.category) ?? 0) + 1);
    return [...n].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([c, k]) => ({ value: c, label: c, hint: `${k} items` }));
  }, [items.rows]);

  const itemRows = useMemo(() => {
    const out = (items.rows ?? []).filter(
      (i) =>
        (!query || i.name.toLowerCase().includes(query) || inEffect(i.short_effect)) &&
        (!itemCats.length || (i.category != null && itemCats.includes(i.category))),
    );
    const dir = itemOrder === "asc" ? 1 : -1;
    return out.sort(itemSort === "name" ? (a, b) => dir * a.name.localeCompare(b.name) : byField((i) => i[itemSort] || null, dir));
  }, [items.rows, query, inEffect, itemCats, itemSort, itemOrder]);

  // Header clicks: the active column flips; another starts in its natural order (names A→Z, numbers high→low).
  const sortMoves = (k: MoveSort) => {
    if (k === moveSort) setMoveOrder((o) => (o === "asc" ? "desc" : "asc"));
    else { setMoveSort(k); setMoveOrder(k === "name" ? "asc" : "desc"); }
  };
  const sortItems = (k: ItemSort) => {
    if (k === itemSort) setItemOrder((o) => (o === "asc" ? "desc" : "asc"));
    else { setItemSort(k); setItemOrder(k === "name" ? "asc" : "desc"); }
  };
  const toggleType = (t: string) => setTypes((s) => (s.includes(t) ? s.filter((x) => x !== t) : [...s, t]));
  const cur = kind === "move" ? { ...moves, shown: moveRows.length } : kind === "ability" ? { ...abilities, shown: abilityRows.length } : { ...items, shown: itemRows.length };
  const noun = KINDS.find((k) => k.key === kind)!.noun;
  const filtered = query !== "" || (kind === "move" ? types.length > 0 || cats.length > 0 || moveKinds.length > 0 || game !== ANY_GAME : kind === "item" && itemCats.length > 0);
  const clear = () => {
    setQ("");
    if (kind === "move") { setTypes([]); setCats([]); setMoveKinds([]); setGame(ANY_GAME); }
    if (kind === "item") setItemCats([]);
  };

  if (typeof document === "undefined") return null;
  return createPortal(
    <div className="lc-modal" onClick={onClose} role="dialog" aria-modal="true" aria-label="Finder" hidden={hidden} data-lenis-prevent>
      <div className="lc-modal-card mf-card" onClick={(e) => e.stopPropagation()}>
        <div className="lc-modal-top mf-top">
          <div className="lc-modal-head">
            <div className="mv-tabs" role="radiogroup" aria-label="Find">
              {KINDS.map((k) => {
                const n = (k.key === "move" ? moves : k.key === "ability" ? abilities : items).rows?.length;
                return (
                  <button key={k.key} role="radio" aria-checked={kind === k.key} className={`mv-tab${kind === k.key ? " on" : ""}`} onClick={() => setKind(k.key)}>
                    {k.label}{n != null && <span className="c">{n.toLocaleString()}</span>}
                  </button>
                );
              })}
            </div>
            <span className="sub">{cur.rows ? `${cur.shown.toLocaleString()} of ${cur.rows.length.toLocaleString()} ${noun}` : ""}</span>
            <button className="x" onClick={onClose} aria-label="Close">×</button>
          </div>
          <div className="mf-bar">
            <input
              autoFocus
              placeholder={kind === "move" ? "Search moves…" : kind === "ability" ? "Search abilities or effects…" : "Search items or effects…"}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label={`Search ${noun}`}
            />
            {kind === "move" && (
              <>
                <Dropdown label="Category" prefix="Category" options={CATS} value={cats} onChange={setCats} multiple allLabel="Any" />
                <Dropdown label="Kind" prefix="Kind" options={KINDS_OF_MOVE} value={moveKinds} onChange={setMoveKinds} multiple allLabel="All" />
                <Dropdown label="Game" prefix="Game" options={gameOptions} value={[game]} onChange={([g]) => setGame(g ?? ANY_GAME)} align="right" />
              </>
            )}
            {kind === "item" && (
              <>
                <Dropdown label="Category" prefix="Category" options={itemCatOptions} value={itemCats} onChange={setItemCats} multiple allLabel="Any" />
              </>
            )}
          </div>
          {kind === "move" && (
            <div className="pk-types mf-types">
              {TYPE_ORDER.map((t) => (
                <button
                  key={t}
                  onClick={() => toggleType(t)}
                  aria-pressed={types.includes(t)}
                  className={types.includes(t) ? "on" : ""}
                  style={{ "--tc": typeHex(t) } as CSSProperties}
                >
                  {t}
                </button>
              ))}
            </div>
          )}
        </div>
        {/* Keyed by kind so switching starts the list at the top. */}
        <div className="mf-list" key={kind} data-lenis-prevent>
          {kind === "move" && (
            <>
              <div className="mf-row mf-head">
                <span className="t">Type</span>
                <SortHead s="name" label="Move" cls="nm" sort={moveSort} order={moveOrder} onSort={sortMoves} />
                <span className="c">Cat</span>
                <SortHead s="power" label="Pow" sort={moveSort} order={moveOrder} onSort={sortMoves} />
                <SortHead s="accuracy" label="Acc" sort={moveSort} order={moveOrder} onSort={sortMoves} />
                <SortHead s="pp" label="PP" sort={moveSort} order={moveOrder} onSort={sortMoves} />
              </div>
              {moveRows.map((m) => (
                <button key={m.id} className="mf-row" onClick={() => onPickMove(m)}>
                  <span className="t">
                    {m.type && <span className="lc-tt" style={{ background: TYPE_HEX[m.type] }}>{m.type}</span>}
                  </span>
                  <span className="nm" title={m.name}>{m.name}</span>
                  <span className="c">{m.classes.length ? m.classes.map((c) => CAT_SHORT[c]).join("·") : "—"}</span>
                  <span className="n">{dash(m.power)}</span>
                  <span className="n">{m.accuracy == null ? "—" : `${m.accuracy}%`}</span>
                  <span className="n">{dash(m.pp)}</span>
                </button>
              ))}
            </>
          )}
          {kind === "ability" && (
            <>
              <div className="mf-row mf-row--ab mf-head">
                <SortHead s="name" label="Ability" cls="nm" sort="name" order={abilityOrder} onSort={() => setAbilityOrder((o) => (o === "asc" ? "desc" : "asc"))} />
                <span className="e">Effect</span>
              </div>
              {abilityRows.map((a) => (
                <button key={a.id} className="mf-row mf-row--ab" onClick={() => onPickAbility(a)}>
                  <span className="nm" title={a.name}>{a.name}</span>
                  <span className="e" title={a.short_effect ?? a.effect ?? undefined}>{a.short_effect ?? a.effect ?? "—"}</span>
                </button>
              ))}
            </>
          )}
          {kind === "item" && (
            <>
              <div className="mf-row mf-row--it mf-head">
                <SortHead s="name" label="Item" cls="nm" sort={itemSort} order={itemOrder} onSort={sortItems} />
                <span className="e">Category</span>
                <SortHead s="cost" label="Cost" sort={itemSort} order={itemOrder} onSort={sortItems} />
                <SortHead s="fling_power" label="Fling" sort={itemSort} order={itemOrder} onSort={sortItems} />
              </div>
              {itemRows.map((i) => (
                <button key={i.id} className="mf-row mf-row--it" onClick={() => onPickItem(i)}>
                  <span className="nm" title={i.short_effect ? `${i.name} — ${i.short_effect}` : i.name}>{i.name}</span>
                  <span className="e">{i.category ?? "—"}</span>
                  <span className="n">{i.cost ? `₽${i.cost.toLocaleString()}` : "—"}</span>
                  <span className="n">{dash(i.fling_power)}</span>
                </button>
              ))}
            </>
          )}
          {!cur.rows && !cur.failed && <p className="mf-empty">Loading {noun}…</p>}
          {cur.failed && <p className="mf-empty">Couldn’t load the {noun}. Close and try again.</p>}
          {cur.rows && cur.shown === 0 && (
            <p className="mf-empty">
              No {noun} match these filters.{" "}
              {filtered && <button className="mf-clear" onClick={clear}>Clear filters</button>}
            </p>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
