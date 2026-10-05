"use client";

// Home "Catch rate" tile: pick a wild Pokémon, its HP and status, and every ball is
// ranked by its odds for that situation. Maths lives in lib/catchRate (client-side).
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { DcPicker, HpPicker, type CalcMon } from "@/components/calc/fields";
import { getPokemon } from "@/lib/api";
import {
  BALLS, DEFAULT_CTX, catchChance, pct,
  type Ball, type CatchCtx, type CatchMon, type Status,
} from "@/lib/catchRate";

/** A Poké Ball drawn from its colours (no ball sprites in the dataset). */
function BallIcon({ b, size = 22 }: { b: Ball; size?: number }) {
  const clip = `cr-top-${b.id}`;
  return (
    <svg className="cr-ball" width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <defs><clipPath id={clip}><rect x="0" y="0" width="32" height="16" /></clipPath></defs>
      <circle cx="16" cy="16" r="14.5" fill="#fff" />
      <circle cx="16" cy="16" r="14.5" fill={b.top} clipPath={`url(#${clip})`} />
      {b.accent && <path d="M6 9.5 Q10 5 14 6 M18 6 Q22 5 26 9.5" stroke={b.accent} strokeWidth="3" fill="none" strokeLinecap="round" clipPath={`url(#${clip})`} />}
      {b.band && <rect x="1" y="14" width="30" height="4" fill={b.band} />}
      <rect x="1.5" y="14.6" width="29" height="2.8" fill="#22252b" />
      <circle cx="16" cy="16" r="4.6" fill="#fff" stroke="#22252b" strokeWidth="2.4" />
      <circle cx="16" cy="16" r="14.5" fill="none" stroke="#22252b" strokeWidth="2" />
    </svg>
  );
}

const STATUSES: { k: Exclude<Status, "none">; code: string; name: string; hint: string }[] = [
  { k: "sleep", code: "SLP", name: "Asleep", hint: "×2.5 (×2 before Gen 5)" },
  { k: "freeze", code: "FRZ", name: "Frozen", hint: "×2.5 (×2 before Gen 5)" },
  { k: "paralysis", code: "PAR", name: "Paralyzed", hint: "×1.5" },
  { k: "burn", code: "BRN", name: "Burned", hint: "×1.5" },
  { k: "poison", code: "PSN", name: "Poisoned", hint: "×1.5" },
];
const STATUS_WORD: Record<Status, string> = { none: "healthy", sleep: "asleep", freeze: "frozen", paralysis: "paralyzed", burn: "burned", poison: "poisoned" };
const hpCol = (v: number) => (v > 50 ? "var(--ok)" : v > 20 ? "#f0b429" : "var(--red)");
const x = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/0$/, ""));

type Mon = CatchMon & { calc: CalcMon };

export default function CatchRateTile() {
  const [mon, setMon] = useState<Mon | null>(null);
  const [ctx, setCtx] = useState<CatchCtx>({ ...DEFAULT_CTX, hpPct: 25, level: 55 });
  const [ballId, setBallId] = useState("ultra");
  const [field, setField] = useState(false);
  const [math, setMath] = useState(false);
  const set = <K extends keyof CatchCtx>(k: K, v: CatchCtx[K]) => setCtx((c) => ({ ...c, [k]: v }));

  const load = (dex: number) => getPokemon(dex).then((d) => setMon({
    name: d.name, dex: d.dex_number, types: d.types, captureRate: d.capture_rate ?? 45,
    baseHp: d.stats.hp, baseSpeed: d.stats.speed, weightKg: d.weight_kg ?? 0, genderRate: d.gender_rate ?? 0,
    calc: { id: d.id, name: d.name, dex: d.dex_number, types: d.types, stats: d.stats },
  })).catch(() => {});
  useEffect(() => { load(149); }, []);

  const rows = useMemo(
    () => (mon ? BALLS.map((b) => ({ b, r: catchChance(mon, b, ctx) })).sort((a, b) => b.r.p - a.r.p) : []),
    [mon, ctx],
  );
  const cur = rows.find((r) => r.b.id === ballId);
  const res = cur?.r;
  const v = ctx.hpPct;

  const num = (k: "level" | "myLevel" | "turn" | "dexCaught", l: string, max: number, min = 1) => (
    <span className="cr-num"><span>{l}</span>
      <input inputMode="numeric" value={ctx[k]} aria-label={l}
        onChange={(e) => { const n = parseInt(e.target.value, 10); set(k, Number.isNaN(n) ? min : Math.max(min, Math.min(max, n))); }} />
    </span>
  );
  const chip = (k: "night" | "water" | "caught" | "loveMatch" | "charm", l: string, hint: string) => (
    <label className={ctx[k] ? "on" : ""} title={hint}><input type="checkbox" checked={ctx[k]} onChange={(e) => set(k, e.target.checked)} />{l}</label>
  );
  const sit = [`Lv ${ctx.level}`, `turn ${ctx.turn}`, ctx.night && "night", ctx.water && "water", ctx.caught && "caught"].filter(Boolean).join(" · ");

  return (
    <section className="card dc cr">
      <div className="lbl">Catch rate<span className="mono">base rate {mon?.captureRate ?? "–"}</span></div>
      <div className="cr-k">
        <span className="dc-k">Wild Pokémon · Lv {ctx.level}</span>
        <span className="dc-seg" role="group" aria-label="Status">
          {STATUSES.map((q) => (
            <button key={q.k} title={`${q.name} ${q.hint}`} aria-pressed={ctx.status === q.k} className={ctx.status === q.k ? "on" : ""}
              onClick={() => set("status", ctx.status === q.k ? "none" : q.k)}>{q.code}</button>
          ))}
        </span>
      </div>
      <div className="dc-ph cr-ph">
        <DcPicker mon={mon?.calc ?? null} forms={false} ph="Pick a Pokémon…" onPick={(p) => load(p.dex_number)} />
        <span className="dc-start"><HpPicker value={v} onChange={(n) => set("hpPct", n)} /></span>
      </div>
      {/* HP is set from the dropdown above or by dragging / clicking this bar */}
      <div className="dc-hpnow cr-hpnow">
        <span className="dc-k">HP</span>
        <div className="cr-hpbar" style={{ "--v": `${v}%`, "--c": hpCol(v) } as CSSProperties}>
          <div className="dc-hpl"><i /></div>
          <input type="range" min={1} max={100} value={v} onChange={(e) => set("hpPct", Number(e.target.value))}
            aria-label="Wild Pokémon's HP" aria-valuetext={res ? `${res.hp} of ${res.maxHp} HP, ${v}%` : `${v}%`} />
        </div>
        <span className="cr-hpn">{res ? `${res.hp}/${res.maxHp}` : ""}</span>
      </div>

      <div className="cr-lh"><span className="dc-k">Best balls here</span><span className="dc-k">per throw</span></div>
      <div className="cr-list" data-lenis-prevent>
        {rows.map(({ b, r }) => (
          <button key={b.id} className={`cr-row${ballId === b.id ? " on" : ""}`} aria-pressed={ballId === b.id} onClick={() => setBallId(b.id)}>
            <BallIcon b={b} />
            <span className="nm">{b.name}</span>
            <span className="mt">{r.ballWhy}</span>
            <b style={{ color: hpCol(r.p * 100) }}>{pct(r.p)}%</b>
          </button>
        ))}
      </div>

      <div className="dc-subrow">
        <button className="dc-optbtn" onClick={() => setField((o) => !o)}>{field ? "hide situation ▴" : `situation — ${sit} ▾`}</button>
        <button className="dc-optbtn" onClick={() => setMath((o) => !o)}>{math ? "hide math ▴" : "math ▾"}</button>
      </div>
      {field && (
        <div className="dc-drawer">
          <div className="dc-field">
            {num("level", "Wild Lv", 100)}{num("myLevel", "Your Lv", 100)}{num("turn", "Turn", 99)}
            {chip("night", "Night / cave", "Dusk Ball ×3")}
            {chip("water", "Fishing / surfing", "Dive Ball ×3.5 · Lure Ball ×4")}
            {chip("caught", "Caught before", "Repeat Ball ×3.5")}
            {chip("loveMatch", "Lead: same species, other gender", "Love Ball ×8")}
            {num("dexCaught", "Species caught", 1025, 0)}
            {chip("charm", "Catching Charm", "Doubles the critical-capture chance")}
          </div>
        </div>
      )}
      {math && res && cur && (
        <div className="dc-formula dc-formula-top">
          a = (3·{res.maxHp} − 2·{res.hp}) / (3·{res.maxHp}) × {res.rate} rate × {x(res.ballMul)} {cur.b.name} × {x(res.statusMul)} {STATUS_WORD[ctx.status]}{res.lowLv > 1 ? ` × ${x(res.lowLv)} low Lv` : ""} = <b>{res.a.toFixed(1)}</b>
          {res.sure
            ? <> → <b>guaranteed</b></>
            : <> · shake = 65536 / (255/a)^(3/16) ÷ 65536 = {res.shake.toFixed(3)} → {res.crit > 0 ? `crit ${(res.crit * 100).toFixed(1)}% + ` : ""}{res.shake.toFixed(3)}⁴ = <b>{pct(res.p)}%</b></>}
          <br />Ball and status multipliers are Gen 5+ values · Sword/Shield formula.
        </div>
      )}
    </section>
  );
}
