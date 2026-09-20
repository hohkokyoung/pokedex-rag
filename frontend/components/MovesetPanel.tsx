"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getPokemonMoves, getFormMoves, type LearnsetMove } from "@/lib/api";
import { typeColor } from "@/lib/pokeTypes";

type Group = { key: string; label: string; methods: string[] };
const GROUPS: Group[] = [
  { key: "level", label: "Level-up", methods: ["level-up"] },
  { key: "egg", label: "Egg", methods: ["egg", "light-ball-egg"] },
  { key: "tm", label: "TM / HM", methods: ["machine"] },
  { key: "tutor", label: "Tutor", methods: ["tutor"] },
  { key: "other", label: "Other", methods: ["train", "form-change", "xd-purification"] },
];
const CAT: Record<string, string> = { physical: "PHY", special: "SPE", status: "STA" };
const meta = (m: LearnsetMove) =>
  `${m.damage_class ? CAT[m.damage_class] + " " : ""}${m.power ?? "—"} · ${m.pp ?? "—"}pp`;

export default function MovesetPanel({
  pokemonId,
  formId = null,
}: { pokemonId: number; formId?: number | null }) {
  const [moves, setMoves] = useState<LearnsetMove[] | null>(null);

  useEffect(() => {
    let alive = true;
    const load = formId != null ? getFormMoves(formId) : getPokemonMoves(pokemonId);
    load
      .then((m) => alive && setMoves(m))
      .catch(() => alive && setMoves([]));
    return () => {
      alive = false;
    };
  }, [pokemonId, formId]);

  const grouped = useMemo(() => {
    const out: Record<string, LearnsetMove[]> = {};
    for (const g of GROUPS) {
      const known = new Set(g.methods);
      const rows = (moves ?? []).filter((m) => known.has(m.learn_method ?? ""));
      if (g.key === "level") {
        rows.sort((a, b) => (a.level ?? 0) - (b.level ?? 0) || a.name.localeCompare(b.name));
      } else {
        rows.sort((a, b) => (b.power ?? 0) - (a.power ?? 0) || a.name.localeCompare(b.name));
      }
      if (rows.length) out[g.key] = rows;
    }
    return out;
  }, [moves]);

  const available = GROUPS.filter((g) => grouped[g.key]?.length);
  const [tab, setTab] = useState<string>("level");
  const [q, setQ] = useState("");
  const activeKey = available.some((g) => g.key === tab) ? tab : available[0]?.key;
  const all = activeKey ? grouped[activeKey] ?? [] : [];
  const query = q.trim().toLowerCase();
  const rows = query ? all.filter((m) => m.name.toLowerCase().includes(query)) : all;

  // Track how many grid columns are live so we can drop the divider under any
  // move that has nothing beneath it in its column (the visually-last row).
  const listRef = useRef<HTMLDivElement>(null);
  const [cols, setCols] = useState(1);
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const measure = () =>
      setCols(getComputedStyle(el).gridTemplateColumns.split(" ").filter(Boolean).length || 1);
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [rows.length]);

  if (moves === null) {
    return <p className="font-mono" style={{ color: "var(--faint)", fontSize: 12, letterSpacing: "0.08em" }}>Loading learnset…</p>;
  }
  if (moves.length === 0) return null;
  if (available.length === 0) {
    return <p className="font-mono" style={{ color: "var(--faint)", fontSize: 12, letterSpacing: "0.08em" }}>No recorded moves.</p>;
  }

  return (
    <div>
      <div className="mv-bar">
        <div className="mv-tabs">
          {available.map((g) => (
            <button
              key={g.key}
              className={`mv-tab${g.key === activeKey ? " on" : ""}`}
              onClick={() => setTab(g.key)}
            >
              {g.label}<span className="c">{grouped[g.key].length}</span>
            </button>
          ))}
        </div>
        <input
          className="mv-search font-mono"
          placeholder="Filter moves…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div className="mv-list" ref={listRef}>
        {rows.map((m, i) => (
          <div
            className={`mv-item${i + cols >= rows.length ? " last-col" : ""}`}
            key={`${m.move_id}-${m.learn_method}`}
          >
            {activeKey === "level" && <span className="mv-lv">{m.level ? `Lv.${m.level}` : "—"}</span>}
            <span className="mv-tag" style={{ background: m.type ? typeColor(m.type) : "var(--ink)" }}>{m.type ?? "—"}</span>
            <span className="nm" title={m.name}>{m.name}</span>
            <span className="pw">{meta(m)}</span>
          </div>
        ))}
      </div>
      {rows.length === 0 && (
        <p className="font-mono" style={{ color: "var(--faint)", fontSize: 12, marginTop: 14 }}>No moves match “{q}”.</p>
      )}
    </div>
  );
}
