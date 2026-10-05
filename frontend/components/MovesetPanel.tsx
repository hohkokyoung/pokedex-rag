"use client";

import { useEffect, useState, type CSSProperties } from "react";
import Dropdown from "@/components/Dropdown";
import { getPokemonMoves, getFormMoves, getPokemonMovesByGame, type GameMove, type PokemonGame } from "@/lib/api";
import { TYPE_HEX, TYPE_ORDER, typeHex } from "@/lib/pokeTypes";
import { MoveLearnersModal } from "@/components/MoveLearners";

/**
 * A species' learnset in the home Finder's language: a game picker (newest game
 * first, or every game at once), method tabs, a search / category / sort bar,
 * type chips (only the types this learnset has) and a scrolling table. Clicking a
 * row opens the move's "who learns it" modal on the same game.
 */
type LearnsetMove = GameMove;
type Group = { key: string; label: string; methods: string[] };
const GROUPS: Group[] = [
  { key: "level", label: "Level-up", methods: ["level-up"] },
  { key: "egg", label: "Egg", methods: ["egg"] },
  { key: "tm", label: "TM / HM", methods: ["machine"] },
  { key: "tutor", label: "Tutor", methods: ["tutor"] },
  { key: "other", label: "Other", methods: [] },
];
const KNOWN = new Set(GROUPS.flatMap((g) => g.methods));
// "Other" catches every remaining method (form change, Light Ball egg, Zygarde Cube…).
const inGroup = (g: Group, method: string | null) => (g.key === "other" ? !KNOWN.has(method ?? "") : g.methods.includes(method ?? ""));
const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"];
const ANY = 0;
const CATS = [
  { value: "physical", label: "Physical" },
  { value: "special", label: "Special" },
  { value: "status", label: "Status" },
];
const CAT_SHORT: Record<string, string> = { physical: "PHY", special: "SPE", status: "STA" };
// "slot" is the tab's own number: the level on Level-up, the TM number on TM / HM.
type Sort = "slot" | "power" | "accuracy" | "pp" | "name";
// Names read A→Z and levels/TMs low→high; the numbers read highest first.
const defaultOrder = (s: Sort) => (s === "name" || s === "slot" ? "asc" : "desc");
// TM01… then HM01… then TR01…, so the machine list reads in bag order.
const machineKey = (label: string | null) => {
  const m = label?.match(/^(TM|HM|TR)(\d+)$/);
  return m ? ["TM", "HM", "TR"].indexOf(m[1]) * 1000 + Number(m[2]) : null;
};
const NONE: LearnsetMove[] = [];
const dash = (v: number | null | undefined) => (v == null ? "—" : String(v));
const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Sort by a numeric field; rows without it sink either way, ties by name. */
function byField(get: (m: LearnsetMove) => number | null | undefined, dir: number) {
  return (a: LearnsetMove, b: LearnsetMove) => {
    const av = get(a), bv = get(b);
    if (av == null || bv == null) return av == null && bv == null ? a.name.localeCompare(b.name) : av == null ? 1 : -1;
    return dir * (av - bv) || a.name.localeCompare(b.name);
  };
}

export default function MovesetPanel({
  pokemonId,
  formId = null,
}: { pokemonId: number; formId?: number | null }) {
  const mon = formId ?? pokemonId;
  // ANY = every game at once (the default); otherwise one game's id.
  const [game, setGame] = useState<number | null>(ANY);
  const [res, setRes] = useState<{ mon: number; game: number; moves: LearnsetMove[] } | null>(null);
  const [games, setGames] = useState<{ mon: number; list: PokemonGame[] } | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    if (game === ANY) {
      // Every game: the collapsed all-time learnset.
      (formId != null ? getFormMoves(formId) : getPokemonMoves(pokemonId))
        .then((m) => { if (alive) { setFailed(false); setRes({ mon, game: ANY, moves: m.map((x) => ({ ...x, machine: null })) }); } })
        .catch(() => alive && setFailed(true));
      // The game picker still needs this Pokémon's game list.
      if (games?.mon !== mon) {
        getPokemonMovesByGame(mon)
          .then((d) => { if (alive) setGames({ mon, list: d.games }); })
          .catch(() => {});
      }
    } else {
      getPokemonMovesByGame(mon, game)
        .then((d) => {
          if (!alive) return;
          setFailed(false);
          setGames({ mon, list: d.games });
          setRes({ mon, game: d.version_group_id ?? ANY, moves: d.moves });
          // No per-game data at all (rare forms): fall back to every game.
          if (!d.games.length) setGame(ANY);
        })
        .catch(() => alive && setFailed(true));
    }
    return () => { alive = false; };
  }, [mon, game]); // eslint-disable-line react-hooks/exhaustive-deps

  // A different Pokémon / form starts again on every game.
  const [seen, setSeen] = useState(mon);
  if (seen !== mon) { setSeen(mon); setGame(ANY); }

  // Keep this Pokémon's previous game on screen while the next one loads (no flash).
  const cur = res && res.mon === mon ? res : null;
  const moves = cur?.moves ?? null;
  const gameList = games?.mon === mon ? games.list : [];
  const shownGame = cur?.game ?? ANY;
  const loadingGame = cur != null && game != null && game !== cur.game;

  const grouped: Record<string, LearnsetMove[]> = {};
  for (const g of GROUPS) {
    const rows = (moves ?? []).filter((m) => inGroup(g, m.learn_method));
    if (rows.length) grouped[g.key] = rows;
  }

  const available = GROUPS.filter((g) => grouped[g.key]?.length);
  const [tab, setTab] = useState<string>("level");
  const activeKey = available.some((g) => g.key === tab) ? tab : available[0]?.key;
  const isLevel = activeKey === "level";
  // TM numbers differ per game, so the TM tab only has them for one game.
  const isTm = activeKey === "tm" && shownGame !== ANY;
  const slotLabel = isLevel ? "Level" : isTm ? "TM" : null;
  const all = (activeKey && grouped[activeKey]) || NONE;

  const [q, setQ] = useState("");
  const [types, setTypes] = useState<string[]>([]);
  const [cats, setCats] = useState<string[]>([]);
  const [sort, setSort] = useState<Sort>("slot");
  const [order, setOrder] = useState<"asc" | "desc">("asc");
  // A tab without its own number (Egg, Tutor…) falls back to power.
  const sortBy: Sort = !slotLabel && sort === "slot" ? "power" : sort;
  const dirOf = !slotLabel && sort === "slot" ? "desc" : order;
  const pickSort = (s: Sort) => { setSort(s); setOrder(defaultOrder(s)); };
  // Clicking the active column flips it; another column sorts by it.
  const headSort = (s: Sort) => (s === sortBy ? (setSort(s), setOrder(dirOf === "asc" ? "desc" : "asc")) : pickSort(s));

  // Switching method keeps the search, but resets chips/sort to that tab's natural order.
  const switchTab = (k: string) => {
    setTab(k);
    setTypes([]);
    pickSort(k === "level" || k === "tm" ? "slot" : "power");
  };

  // Only the types this tab actually has, in the canonical order.
  const haveTypes = new Set(all.map((m) => m.type));
  const tabTypes = TYPE_ORDER.filter((t) => haveTypes.has(t));

  const query = q.trim().toLowerCase();
  // Effect text matches at a word start, so "heal" finds Drain Punch but not "wheal".
  const re = query ? new RegExp(`\\b${escapeRe(query)}`, "i") : null;
  const dir = dirOf === "asc" ? 1 : -1;
  const rows = all
    .filter(
      (m) =>
        (!query || m.name.toLowerCase().includes(query) || (!!m.short_effect && re!.test(m.short_effect))) &&
        (!types.length || (m.type != null && types.includes(m.type))) &&
        (!cats.length || (m.damage_class != null && cats.includes(m.damage_class))),
    )
    .sort(
      sortBy === "name" ? (a, b) => dir * a.name.localeCompare(b.name)
      : sortBy === "slot" ? byField((m) => (isLevel ? m.level : machineKey(m.machine)), dir)
      : byField((m) => m[sortBy], dir),
    );

  // Clicking a move opens its "who learns it" modal.
  const [open, setOpen] = useState<LearnsetMove | null>(null);

  if (moves === null) {
    if (failed) return <p className="font-mono" style={{ color: "var(--faint)", fontSize: 12, letterSpacing: "0.08em" }}>Couldn’t load the learnset.</p>;
    return <p className="font-mono" style={{ color: "var(--faint)", fontSize: 12, letterSpacing: "0.08em" }}>Loading learnset…</p>;
  }
  if (moves.length === 0 && shownGame === ANY && !gameList.length) return null;

  const filtered = query !== "" || types.length > 0 || cats.length > 0;
  const clear = () => { setQ(""); setTypes([]); setCats([]); };
  const toggleType = (t: string) => setTypes((s) => (s.includes(t) ? s.filter((x) => x !== t) : [...s, t]));
  const rowCls = `mf-row ms-row${slotLabel ? " ms-row--lv" : ""}`;
  const gameOpts = [
    { value: ANY, label: "Any game", hint: "Every move it has learned in any game" },
    ...gameList.map((g) => ({ value: g.id, label: g.name, hint: `Generation ${ROMAN[g.generation] ?? g.generation} · ${g.moves} moves` })),
  ];
  const head = (s: Sort, label: string, cls = "n") => (
    <button type="button" className={`${cls}${sortBy === s ? " on" : ""}`} onClick={() => headSort(s)} aria-label={`Sort by ${label}`}>
      {label}{sortBy === s && <i aria-hidden>{dirOf === "asc" ? "↑" : "↓"}</i>}
    </button>
  );

  return (
    <div className={`ms${loadingGame ? " is-loading" : ""}`}>
      <div className="ms-top">
        <div className="mv-tabs" role="tablist" aria-label="Learn method">
          {available.map((g) => (
            <button
              key={g.key}
              role="tab"
              aria-selected={g.key === activeKey}
              className={`mv-tab${g.key === activeKey ? " on" : ""}`}
              onClick={() => switchTab(g.key)}
            >
              {g.label}<span className="c">{grouped[g.key].length}</span>
            </button>
          ))}
        </div>
        <div className="ms-game">
          <span className="ms-count">{rows.length === all.length ? `${all.length} moves` : `${rows.length} of ${all.length} moves`}</span>
        </div>
      </div>

      <div className="mf-bar">
        <input
          placeholder="Search moves or effects…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search moves"
        />
        <Dropdown label="Category" prefix="Category" options={CATS} value={cats} onChange={setCats} multiple allLabel="Any" />
        {gameList.length > 0 && (
          <Dropdown label="Game" prefix="Game" options={gameOpts} value={[shownGame]} onChange={([v]) => v != null && setGame(v)} align="right" />
        )}
      </div>
      {tabTypes.length > 1 && (
        <div className="pk-types mf-types">
          {tabTypes.map((t) => (
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

      {/* Keyed by tab so switching starts the list at the top. */}
      <div className="ms-list" key={activeKey} data-lenis-prevent>
        <div className={`${rowCls} mf-head`}>
          {slotLabel && head("slot", isLevel ? "Lv" : "TM", "lv")}
          <span className="t">Type</span>
          {head("name", "Move", "nm")}
          <span className="c">Cat</span>
          {head("power", "Pow")}
          {head("accuracy", "Acc")}
          {head("pp", "PP")}
          <span className="e">Effect</span>
        </div>
        {rows.map((m) => (
          <button
            type="button"
            className={rowCls}
            key={`${m.move_id}-${m.learn_method}-${m.level ?? ""}`}
            onClick={() => setOpen(m)}
            title={`Who else learns ${m.name}`}
          >
            {slotLabel && <span className="lv">{isLevel ? (m.level ? m.level : "Evo") : (m.machine ?? "—")}</span>}
            <span className="t">
              {m.type && <span className="lc-tt" style={{ background: TYPE_HEX[m.type] }}>{m.type}</span>}
            </span>
            <span className="nm">{m.name}</span>
            <span className="c">{m.damage_class ? CAT_SHORT[m.damage_class] : "—"}</span>
            <span className="n">{dash(m.power)}</span>
            <span className="n">{m.accuracy == null ? "—" : `${m.accuracy}%`}</span>
            <span className="n">{dash(m.pp)}</span>
            <span className="e">{m.short_effect ?? "—"}</span>
          </button>
        ))}
        {rows.length === 0 && all.length === 0 && (
          <p className="mf-empty">No moves recorded for this game.</p>
        )}
        {rows.length === 0 && all.length > 0 && (
          <p className="mf-empty">
            No moves match these filters.{" "}
            {filtered && <button className="mf-clear" onClick={clear}>Clear filters</button>}
          </p>
        )}
      </div>

      {open && (
        <MoveLearnersModal
          move={{
            id: open.move_id,
            name: open.name,
            type: open.type,
            category: open.damage_class ? open.damage_class[0].toUpperCase() + open.damage_class.slice(1) : null,
            power: open.power,
            accuracy: open.accuracy,
            pp: open.pp,
            effect: open.short_effect,
          }}
          initialGame={shownGame === ANY ? null : shownGame}
          onClose={() => setOpen(null)}
        />
      )}
    </div>
  );
}
