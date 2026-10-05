"use client";

import { useEffect, useRef, useState } from "react";
import Dropdown from "@/components/Dropdown";
import { getPokemonEncounters, type Encounter, type PokemonEncounters } from "@/lib/api";

/**
 * Where to find a Pokémon, in the Moveset panel's language: a "Game" dropdown
 * over one table (place · how · level · rate), split into sentence-case groups
 * by how you catch it. A place's name shows once per run of rows, and Sword /
 * Shield raid dens fold into a single row.
 */
const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"];
const RAID = new Set(["max-raid", "dynamax-adventure"]);
// Busy games list 80+ rows; show a page-sized slice so the last section on the
// page doesn't swing the page length by thousands of pixels per game.
const PREVIEW = 12;

const GROUPS = ["In the wild", "On water", "Fishing", "Headbutt trees", "Gifts and one-offs", "Max Raid dens"];
function group(method: string) {
  if (RAID.has(method)) return "Max Raid dens";
  if (/rod|fishing|bubbling/.test(method)) return "Fishing";
  if (/surf|seaweed|water/.test(method)) return "On water";
  if (/headbutt/.test(method)) return "Headbutt trees";
  if (/gift|trade|static/.test(method)) return "Gifts and one-offs";
  return "In the wild";
}

const levels = (lo: number, hi: number) => (lo === hi ? `${lo}` : `${lo}–${hi}`);

const BEFORE = "Before Hall of Fame";
const AFTER = "After Hall of Fame";
type Shown = Encounter & { postgame?: string };

/** Sword / Shield list most spawns twice — before and after the Hall of Fame,
 *  at a higher level. Fold each pair into one row with a "Lv 60 after…" note. */
function foldPostgame(rows: Encounter[]): Shown[] {
  const tags = (e: Encounter) => (e.conditions ?? "").split(" · ");
  const rest = (e: Encounter) => tags(e).filter((t) => t !== BEFORE && t !== AFTER).join(" · ");
  const key = (e: Encounter) => [e.location, e.area, e.method, e.chance, rest(e)].join("|");
  const after = new Map(rows.filter((e) => tags(e).includes(AFTER)).map((e) => [key(e), e]));
  const paired = new Map<Encounter, Encounter>(); // before row -> its after row
  for (const e of rows) {
    const twin = tags(e).includes(BEFORE) ? after.get(key(e)) : undefined;
    if (twin) paired.set(e, twin);
  }
  const absorbed = new Set(paired.values());
  return rows
    .filter((e) => !absorbed.has(e))
    .map((e) => {
      const twin = paired.get(e);
      if (!twin) return e;
      return { ...e, conditions: rest(e) || null, postgame: `Lv ${levels(twin.min_level, twin.max_level)} after the Hall of Fame` };
    });
}

type Row =
  | { kind: "group"; label: string; count: number }
  | { kind: "row"; e: Shown; first: boolean }
  | { kind: "raid"; dens: string[]; lo: number; hi: number };

/** Flatten a game's encounters into group headers + rows, in GROUPS order. */
function buildRows(encounters: Encounter[]): Row[] {
  const out: Row[] = [];
  for (const label of GROUPS) {
    const rows = foldPostgame(encounters.filter((e) => group(e.method) === label));
    if (!rows.length) continue;
    if (label === "Max Raid dens") {
      const dens = [...new Set(rows.map((r) => (r.area ? `${r.location} (${r.area.replace(/^Max Den /, "")})` : r.location)))];
      out.push({ kind: "group", label, count: dens.length });
      out.push({ kind: "raid", dens, lo: Math.min(...rows.map((r) => r.min_level)), hi: Math.max(...rows.map((r) => r.max_level)) });
      continue;
    }
    out.push({ kind: "group", label, count: new Set(rows.map((r) => r.location)).size });
    rows.forEach((e, i) => out.push({ kind: "row", e, first: i === 0 || rows[i - 1].location !== e.location }));
  }
  return out;
}

export default function EncountersPanel({ pokemonId }: { pokemonId: number }) {
  const [data, setData] = useState<PokemonEncounters | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let alive = true;
    getPokemonEncounters(pokemonId, version)
      .then((d) => { if (alive) { setFailed(false); setData(d); } })
      .catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, [pokemonId, version]);

  const muted = { color: "var(--faint)", fontSize: 12, letterSpacing: "0.08em" };
  if (!data) {
    return <p className="font-mono" style={muted}>{failed ? "Couldn’t load encounter data." : "Loading…"}</p>;
  }
  if (data.games.length === 0) {
    return (
      <p className="enc-none">
        Not found in the wild in any game on record. It’s usually obtained by evolution, breeding, a trade or an event.
        <span> Encounter data covers the main series up to Sword &amp; Shield.</span>
      </p>
    );
  }

  // A picked game is in flight until the response for it lands.
  const loading = version != null && data.version_id !== version;
  // Newest game first, as in the Moveset picker.
  const options = [...data.games].reverse().map((g) => ({ value: g.version_id, label: g.version, hint: `Gen ${ROMAN[g.generation] ?? g.generation}` }));
  const all = buildRows(data.encounters);
  const dataRows = all.filter((r) => r.kind !== "group").length;
  // Cut after PREVIEW data rows, keeping their group headers.
  let seen = 0;
  const rows = expanded ? all : all.filter((r) => (r.kind === "group" ? seen < PREVIEW : ++seen <= PREVIEW));
  const places = new Set(data.encounters.map((e) => e.location)).size;

  const pick = (v: number) => { setExpanded(false); setVersion(v); };
  const collapse = () => {
    setExpanded(false);
    // Don't strand the reader below a list that just got shorter.
    rootRef.current?.scrollIntoView({ block: "start" });
  };

  return (
    <div ref={rootRef} className={`enc${loading ? " is-loading" : ""}`}>
      <div className="enc-top">
        <Dropdown label="Game" prefix="Game" options={options} value={[data.version_id!]} onChange={([v]) => v != null && pick(v)} />
        <span className="enc-count">{places} {places === 1 ? "place" : "places"}</span>
      </div>

      <div className="enc-table" role="table" aria-label="Where to find">
        <div className="enc-row enc-head" role="row">
          <span role="columnheader">Place</span>
          <span role="columnheader">How</span>
          <span role="columnheader" className="n">Level</span>
          <span role="columnheader" className="n">Rate</span>
        </div>
        {rows.map((r, i) => {
          if (r.kind === "group") {
            return (
              <div key={`g-${r.label}`} className="enc-group" role="row">
                <span role="cell">{r.label}<span className="c">{r.count}</span></span>
              </div>
            );
          }
          if (r.kind === "raid") {
            return (
              <div key="raid" className="enc-row" role="row">
                <span role="cell" className="enc-dens">{r.dens.join(" · ")}</span>
                <span role="cell">Max Raid</span>
                <span role="cell" className="n">{levels(r.lo, r.hi)}</span>
                <span role="cell" className="n" />
              </div>
            );
          }
          const { e, first } = r;
          return (
            <div key={i} className={`enc-row${first ? "" : " is-cont"}`} role="row">
              <span role="cell">
                {first && <b>{e.location}</b>}
                {e.area && <small>{e.area}</small>}
              </span>
              <span role="cell">
                {e.method_name}
                {(e.conditions || e.postgame) && <small>{[e.conditions, e.postgame].filter(Boolean).join(" · ")}</small>}
              </span>
              <span role="cell" className="n">{levels(e.min_level, e.max_level)}</span>
              <span role="cell" className="n">{e.chance != null ? `${e.chance}%` : ""}</span>
            </div>
          );
        })}
      </div>

      {dataRows > PREVIEW && (
        <button type="button" className="enc-more font-mono" onClick={expanded ? collapse : () => setExpanded(true)}>
          {expanded ? "Show fewer" : `Show all ${dataRows} rows`}
        </button>
      )}
    </div>
  );
}
