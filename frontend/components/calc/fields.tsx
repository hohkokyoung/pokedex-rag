"use client";

// Shared building blocks of the home damage calculator — Pokémon picker, move /
// nature / ability search fields and the EV/IV table — reused by the team slot
// editor so both tools look and behave the same.
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { useKeyNav } from "@/hooks/useKeyNav";
import { assetUrl, getFormMoves, getPokemon, getPokemonMoves, listPokemon, thumb } from "@/lib/api";
import { TYPE_HEX, typeChip } from "@/lib/pokeTypes";
import type { Ability, PokemonSummary } from "@/lib/types";
import { NAT, SABBR, natMul, statFull, type EVs, type SKey } from "@/lib/damageCalc";

// The pure stat maths lives in lib/damageCalc (shared with the backend's port); re-exported
// here so calculator UI imports stay in one place.
export { NAT, SABBR, natMul, statFull };
export type { EVs, SKey };

const TC = TYPE_HEX;

export const art = (dex: number) => assetUrl(`/sprites/official-artwork/${dex}.png`);

export function Tag({ t }: { t: string }) {
  return <span className="lc-tt" style={typeChip(t)}>{t}</span>;
}



export type Stats = import("@/lib/types").Stats;
/**
 * A Pokémon in the calculator. For an alternate form (Mega, regional…) `id` is the
 * form's id and `formId` is set; its types, stats, abilities and artwork are the form's.
 */
export type CalcMon = {
  id: number; name: string; dex: number; types: string[]; stats: Stats;
  formId?: number | null; sprite?: string; abilities?: Ability[];
};
export type CalcMove = { name: string; type: string; damage_class: string; power: number; target: string | null; priority: number; accuracy: number | null; effect: string | null };

export const ZERO_EV: EVs = { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 };



export const ALL_IV: EVs = { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 };
export const EV_COLOR: Record<SKey, string> = { hp: "#5DCAA5", atk: "#E24B4A", def: "#85B7EB", spa: "#EF9F27", spd: "#B25EC4", spe: "#F0619A" };
export type Spread = { nat: string; ev: EVs; iv: EVs };
export const offensiveSet = (mon: CalcMon | null): Spread => {
  const phys = !mon || mon.stats.attack >= mon.stats.sp_attack;
  return phys
    ? { nat: "Adamant", ev: { ...ZERO_EV, atk: 252, spe: 252, hp: 4 }, iv: { ...ALL_IV } }
    : { nat: "Modest", ev: { ...ZERO_EV, spa: 252, spe: 252, hp: 4 }, iv: { ...ALL_IV, atk: 0 } };
};
export const BULKY_SET: Spread = { nat: "Bold", ev: { ...ZERO_EV, hp: 252, def: 252, spd: 4 }, iv: { ...ALL_IV } };
/** Load a species, or one of its alternate forms when `formId` is given (a search result's `form_id`). */
export async function loadCalcMon(id: number, formId?: number | null): Promise<CalcMon> {
  if (formId == null) {
    const d = await getPokemon(id);
    return { id: d.id, name: d.name, dex: d.dex_number, types: d.types, stats: d.stats };
  }
  // A form search result carries the species' dex number; the form lives on its detail.
  const d = await getPokemon(id);
  const f = d.forms?.find((x) => x.id === formId);
  if (!f) throw new Error(`Form ${formId} not found`);
  return {
    id: f.id, formId: f.id, name: f.name, dex: d.dex_number, types: f.types, stats: f.stats, sprite: f.sprite_url,
    abilities: f.abilities.map((a) => ({ id: a.id ?? -1, identifier: a.identifier, name: a.name, effect: a.effect, short_effect: a.effect, is_hidden: a.is_hidden })),
  };
}
/** Artwork for a calculator Pokémon — the form's own sprite when it has one. */
export const monArt = (m: CalcMon) => (m.sprite ? assetUrl(m.sprite) : art(m.dex));
/** A calculator Pokémon's learnset. A form uses its own, falling back to the species'
 *  when the dataset has none for it (e.g. newer Megas, which share the species' moves). */
export const loadMonMoves = async (m: CalcMon) => {
  if (m.formId == null) return getPokemonMoves(m.id);
  const own = await getFormMoves(m.formId);
  return own.length ? own : getPokemonMoves(m.dex);
};
export function DcPicker({ mon, onPick, ph, forms = true }: {
  mon: CalcMon | null; onPick: (p: PokemonSummary) => void; ph: string;
  /** Include alternate forms (Mega, regional…) in the results. */
  forms?: boolean;
}) {
  const [q, setQ] = useState(""); const [res, setRes] = useState<PokemonSummary[]>([]); const [open, setOpen] = useState(false);
  useEffect(() => {
    const query = q.trim();
    const id = setTimeout(() => {
      if (query.length < 2) { setRes([]); return; }
      listPokemon({ q: query, limit: forms ? 6 : 12 }).then((r) => setRes((forms ? r.items : r.items.filter((p) => p.form_id == null)).slice(0, 6))).catch(() => setRes([]));
    }, 180);
    return () => clearTimeout(id);
  }, [q, forms]);
  const pick = (p: PokemonSummary) => { onPick(p); setQ(""); setRes([]); };
  const { listRef, onKeyDown, itemProps } = useKeyNav(res, pick);
  return (
    <div className={`dc-pill${mon ? " has" : ""}`}>
      {mon && <img loading="lazy" decoding="async" src={thumb(monArt(mon), 48)} alt={mon.name} />/* eslint-disable-line @next/next/no-img-element */}
      <input placeholder={mon ? mon.name : ph} aria-label={ph} value={q} onChange={(e) => setQ(e.target.value)} onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)} onKeyDown={onKeyDown} aria-autocomplete="list" />
      {open && res.length > 0 && (
        <div className="ac" role="listbox" ref={listRef} data-lenis-prevent>
          {res.map((p, idx) => (
            <button key={p.id} role="option" {...itemProps(idx)} onMouseDown={() => pick(p)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img loading="lazy" decoding="async" src={thumb(p.sprite_url, 48)} alt={p.name} />
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
export const EV_TOTAL = 510, EV_MAX = 252;
// Which base stat each EV key raises.
const BASE_KEY: Record<SKey, keyof Stats> = { hp: "hp", atk: "attack", def: "defense", spa: "sp_attack", spd: "sp_defense", spe: "speed" };
/** EV/IV table: one row per stat — drag the bar to set EVs, type the IV, and read the final stat at this level. */
export function EvEditor({ mon, level, nat, ev, iv, onEv, onIv }: { mon: CalcMon; level: number; nat: string; ev: EVs; iv: EVs; onEv: (e: EVs) => void; onIv: (i: EVs) => void }) {
  const total = EV_KEYS.reduce((s, k) => s + ev[k], 0);
  // A stat can take at most 252, and all six together at most 510; round down to a multiple of 4.
  const setEv = (k: SKey, v: number) => {
    const room = EV_TOTAL - (total - ev[k]);
    onEv({ ...ev, [k]: Math.max(0, Math.floor(Math.min(v, EV_MAX, room) / 4) * 4) });
  };
  return (
    <div className="dc-eved">
      <div className="dc-evline hd">
        <span /><span>EVs</span><span />
        <button className="ivall" disabled={EV_KEYS.every((k) => iv[k] === 31)} onClick={() => onIv({ ...ALL_IV })} title="Set every IV to 31">IV<i aria-hidden> ⤒</i></button>
        <span>Stat</span>
      </div>
      {EV_KEYS.map((k) => {
        const nm = natMul(nat, k), cls = nm > 1 ? "up" : nm < 1 ? "dn" : "";
        return (
          <div className="dc-evline" key={k}>
            <span className={`k ${cls}`}>{SABBR[k]}</span>
            <input type="range" min={0} max={EV_MAX} step={4} value={ev[k]} onChange={(e) => setEv(k, Number(e.target.value))}
              style={{ "--c": EV_COLOR[k], "--p": `${(ev[k] / EV_MAX) * 100}%` } as CSSProperties} aria-label={`${SABBR[k]} EVs`} />
            <span className="v">{ev[k]}</span>
            <span className="ivc">
              <input className={`iv${iv[k] === 31 ? "" : " set"}`} type="number" inputMode="numeric" min={0} max={31} value={iv[k]} aria-label={`${SABBR[k]} IV`} title="IV (0–31)"
                onFocus={(e) => e.currentTarget.select()}
                onChange={(e) => onIv({ ...iv, [k]: Math.max(0, Math.min(31, Number(e.target.value) || 0)) })} />
              {iv[k] !== 31 && <button className="ivmax" onClick={() => onIv({ ...iv, [k]: 31 })} title="Set to 31" aria-label={`Set ${SABBR[k]} IV to 31`}>⤒</button>}
            </span>
            <span className={`fin ${cls}`}>{statFull(mon.stats[BASE_KEY[k]], level, iv[k], ev[k], nm, k === "hp")}</span>
          </div>
        );
      })}
      <div className="dc-evfoot">
        <span className={total > EV_TOTAL ? "over" : ""}>EVs {total} / {EV_TOTAL}{EV_TOTAL - total >= 4 ? <em> · {EV_TOTAL - total} left</em> : <em> · full (the last {EV_TOTAL - total} can&apos;t add a stat point)</em>}</span>
      </div>
    </div>
  );
}

/** Close a popover when clicking outside `ref`. */
export function useOutside(open: boolean, ref: React.RefObject<HTMLElement | null>, close: () => void) {
  useEffect(() => {
    if (!open) return;
    const off = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) close(); };
    document.addEventListener("mousedown", off);
    return () => document.removeEventListener("mousedown", off);
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
}

/** Move field — the same search bar as the home search. Type to filter the learnset by name, type or effect. */
export function MoveSearch({ moves, value, onPick, onDone, autoFocus = false, owner, preview, placeholder }: {
  moves: CalcMove[]; value: string | null; onPick: (m: CalcMove) => void; owner: string;
  /** Called whenever the list closes — after a pick, Escape or a click outside. */
  onDone?: () => void;
  /** Focus the field and open the list on mount. */
  autoFocus?: boolean;
  /** Extra text after a row's "type · power", e.g. the damage it would deal. */
  preview?: (m: CalcMove) => string;
  /** Shown when nothing is picked (defaults to a search prompt). */
  placeholder?: string;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(autoFocus);
  const boxRef = useRef<HTMLDivElement>(null);
  useOutside(open, boxRef, () => { setOpen(false); setQ(""); onDone?.(); });
  const rows = useMemo(() => {
    if (!open) return [];
    const s = q.trim().toLowerCase();
    return s ? moves.filter((m) => m.name.toLowerCase().includes(s) || m.type.startsWith(s) || (m.effect ?? "").toLowerCase().includes(s)) : moves;
  }, [open, q, moves]);
  const choose = (m: CalcMove) => { onPick(m); setOpen(false); setQ(""); boxRef.current?.querySelector("input")?.blur(); onDone?.(); };
  const { listRef, onKeyDown, itemProps } = useKeyNav(rows, choose);
  const m = value ? moves.find((x) => x.name === value) ?? null : null;
  return (
    <div className={`lc-search dc-ms${m ? " has" : ""}`} ref={boxRef}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
      <input
        value={q}
        placeholder={m ? m.name : moves.length ? placeholder ?? `Search ${owner}'s moves…` : "Loading moves…"}
        disabled={!moves.length}
        onFocus={() => setOpen(true)}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onKeyDown={(e) => { if (e.key === "Escape") { setOpen(false); setQ(""); e.currentTarget.blur(); onDone?.(); } else onKeyDown(e); }}
        autoFocus={autoFocus}
        aria-label={`Search ${owner}'s moves`}
        aria-autocomplete="list"
        enterKeyHint="done"
      />
      {open && (
        <div className="ac" role="listbox" ref={listRef} data-lenis-prevent>
          {rows.length === 0 && <div className="none">No move matches “{q}” in {owner}&apos;s learnset.</div>}
          {rows.map((row, k) => (
            <button key={row.name} role="option" {...itemProps(k)} className={row.name === value ? "on" : ""} onMouseDown={(e) => { e.preventDefault(); choose(row); }}>
              <span className="nm"><i className="tdot" style={{ background: TC[row.type] ?? "#999" }} />{row.name}</span>
              <span className="mt">{row.type} · {row.power || "status"}{preview?.(row) ?? ""}</span>
              {row.effect && <span className="ds">{row.effect}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
export type PickOpt = { v: string; hint?: string; off?: boolean };
/** Nature / item / ability field: the same search bar as the move field — the current value is the placeholder, type to filter. */
export function PickSearch({ label, value, opts, onPick, search, right = false, bare = false, autoFocus = false, onDone }: {
  label: string; value: string; opts: PickOpt[]; onPick: (v: string) => void; right?: boolean;
  /** Extra matches fetched as you type (2+ letters), listed after the local ones. */
  search?: (q: string) => Promise<PickOpt[]>;
  /** Render just the field, without its label. */
  bare?: boolean;
  /** Focus the field and open the list on mount. */
  autoFocus?: boolean;
  /** Called whenever the list closes — after a pick, Escape or a click outside. */
  onDone?: () => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(autoFocus);
  // Server matches, tagged with the query they answer so stale results are ignored.
  const [remote, setRemote] = useState<{ q: string; list: PickOpt[] }>({ q: "", list: [] });
  const boxRef = useRef<HTMLDivElement>(null);
  useOutside(open, boxRef, () => { setOpen(false); setQ(""); onDone?.(); });
  useEffect(() => {
    const query = q.trim();
    if (!search || query.length < 2) return;
    let alive = true;
    const id = setTimeout(() => search(query).then((list) => { if (alive) setRemote({ q: query, list }); }).catch(() => {}), 180);
    return () => { alive = false; clearTimeout(id); };
  }, [q, search]);
  const rows = useMemo(() => {
    if (!open) return [];
    const s = q.trim().toLowerCase();
    const local = s ? opts.filter((o) => o.v.toLowerCase().includes(s) || (o.hint ?? "").toLowerCase().includes(s)) : opts;
    const extra = remote.q === q.trim() ? remote.list : [];
    return [...local, ...extra.filter((o) => !local.some((l) => l.v === o.v))];
  }, [open, q, opts, remote]);
  const choose = (o: PickOpt) => { onPick(o.v); setOpen(false); setQ(""); boxRef.current?.querySelector("input")?.blur(); onDone?.(); };
  const { listRef, onKeyDown, itemProps } = useKeyNav(rows, choose);
  return (
    <div className="dc-fld">
      {!bare && <span>{label}</span>}
      <div className={`lc-search dc-ms has${right ? " r" : ""}`} ref={boxRef}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
        <input
          value={q}
          placeholder={value}
          onFocus={() => setOpen(true)}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onKeyDown={(e) => { if (e.key === "Escape") { setOpen(false); setQ(""); e.currentTarget.blur(); onDone?.(); } else onKeyDown(e); }}
          autoFocus={autoFocus}
          aria-label={`${label}: ${value}. Type to search`}
          aria-autocomplete="list"
          enterKeyHint="done"
        />
        {open && (
          <div className="ac" role="listbox" ref={listRef} data-lenis-prevent>
            {rows.length === 0 && <div className="none">No {label.toLowerCase()} matches “{q}”</div>}
            {rows.map((o, k) => (
              <button key={o.v} role="option" {...itemProps(k)} className={o.v === value ? "on" : ""} onMouseDown={(e) => { e.preventDefault(); choose(o); }}>
                <span className="nm">{o.v}</span>{o.hint && <span className={`mt${o.off ? " off" : ""}`}>{o.hint}</span>}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
export const NAT_OPTS: PickOpt[] = NAT.map(([n, up, dn]) => ({ v: n, hint: up && dn ? `+${up} −${dn}` : "neutral" }));

const STAT_FULL: Record<string, string> = { Atk: "Attack", Def: "Defense", SpA: "Sp. Atk", SpD: "Sp. Def", Spe: "Speed" };
/** A nature's short tag, e.g. "+Atk −SpA" (or "neutral"). */
export const natTag = (name: string) => {
  const r = NAT.find((x) => x[0] === name);
  return r?.[1] && r[2] ? `+${r[1]} −${r[2]}` : "neutral";
};
/** A nature in words, for its hover card. */
export const natDesc = (name: string) => {
  const r = NAT.find((x) => x[0] === name);
  return r?.[1] && r[2] ? `Raises ${STAT_FULL[r[1]]} by 10% and lowers ${STAT_FULL[r[2]]} by 10%.` : "No effect on stats.";
};

/** A set detail (move, ability, nature, item) as a compact card — click to search over it,
 *  hover for the full text. Shared by the damage calculator and the team slot editor. */
export function InfoBox({
  label,
  name,
  meta,
  desc,
  editing,
  onOpen,
  children,
  className,
}: {
  label: React.ReactNode;
  name: string;
  meta?: string;
  desc?: string;
  editing: boolean;
  onOpen: () => void;
  children: React.ReactNode;
  /** Extra class on the wrapper (e.g. `se-mv` for a move card). */
  className?: string;
}) {
  return (
    <div className={`se-info${className ? ` ${className}` : ""}${editing ? " editing" : ""}`}>
      <button className="se-ibox" onClick={onOpen} aria-label={`${name}${desc ? `. ${desc}` : ""} — change`}>
        <span className="k">{label}</span>
        <span className="nm">{name}</span>
        {meta && <span className="mt">{meta}</span>}
      </button>
      {desc && (
        <div className="se-itip" aria-hidden>
          <span className="nm">
            {name}
            {meta && <em>{meta}</em>}
          </span>
          <span className="fx">{desc}</span>
        </div>
      )}
      {editing && <div className="se-msearch">{children}</div>}
    </div>
  );
}

/** Current HP (as % of max) — quick values plus a slider. */
export function HpPicker({ value, onChange }: { value: number; onChange: (hp: number) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  useOutside(open, ref, () => setOpen(false));
  return (
    <span className="dc-pop" ref={ref}>
      <button className={`dc-hpbtn${value < 100 ? " low" : ""}`} onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-label={`Starting HP: ${value}%`}>
        <span className="k">HP</span><b>{value}%</b>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden><path d="M6 9l6 6 6-6" /></svg>
      </button>
      {open && (
        <span className="dc-pop-box dc-hpbox">
          <span className="qk">{[100, 75, 50, 25, 1].map((v) => <button key={v} className={value === v ? "on" : ""} onClick={() => onChange(v)}>{v}%</button>)}</span>
          <input type="range" min={1} max={100} value={value} onChange={(e) => onChange(Number(e.target.value))} aria-label="Current HP" />
        </span>
      )}
    </span>
  );
}
