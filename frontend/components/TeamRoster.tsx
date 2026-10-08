"use client";

/* The team page's Pokémon section: six tiles, and the picked one explained —
   its set (ability / item / nature, with what each does), base stats with the
   best and worst highlighted, and its moves. Used for both your team and the
   opponent; clicking Edit (or an empty tile) opens the slot editor. */

import { useState } from "react";
import { type Team, type TeamAnalysis, thumb } from "@/lib/api";
import { typeHex } from "@/lib/pokeTypes";
import { Chip } from "@/components/TeamCardParts";

type Member = Team["members"][number];

const STATS = [["hp", "HP"], ["attack", "Atk"], ["defense", "Def"], ["sp_attack", "SpA"], ["sp_defense", "SpD"], ["speed", "Spe"]] as const;
const STAT_MAX = 160;
const NATURE_STAT: Record<string, string> = {
  attack: "Atk", defense: "Def", "special-attack": "SpA", "special-defense": "SpD", speed: "Spe", sp_attack: "SpA", sp_defense: "SpD",
};

const Sprite = ({ src, size }: { src: string; size: number }) => (
  // eslint-disable-next-line @next/next/no-img-element
  <img loading="lazy" decoding="async" src={thumb(src, size)} alt="" width={size} height={size} style={{ objectFit: "contain", flex: "none" }} />
);
const bst = (m: Member) => STATS.reduce((s, [k]) => s + (m.base_stats[k] ?? 0), 0);

function setRows(a: TeamAnalysis | null, m: Member) {
  const sm = a?.sets?.members.find((x) => x.slot === m.slot);
  const r = a?.roles.members.find((x) => x.slot === m.slot);
  const nat = m.nature;
  return [
    { k: "Ability", v: m.ability?.name ?? null, note: sm?.ability_note ?? null },
    { k: "Item", v: m.item?.name ?? null, note: sm?.item_note ?? null },
    {
      k: "Nature",
      v: nat?.name ?? null,
      note: nat?.increased_stat
        ? `+${NATURE_STAT[nat.increased_stat] ?? nat.increased_stat}  −${NATURE_STAT[nat.decreased_stat ?? ""] ?? nat.decreased_stat}`
        : nat ? "neutral" : null,
    },
    ...(r?.eff_speed && r.eff_speed !== r.speed
      ? [{ k: "Speed", v: `${r.speed} → ${r.eff_speed}`, note: r.speed_note?.replace(/^\d+ → \d+ /, "") ?? null }]
      : []),
  ];
}

function Stats({ m }: { m: Member }) {
  const vals = STATS.map(([k]) => m.base_stats[k] ?? 0);
  const hi = Math.max(...vals);
  const lo = Math.min(...vals);
  return (
    <span className="ro-stats">
      {STATS.map(([k, l]) => {
        const v = m.base_stats[k] ?? 0;
        const tone = hi !== lo && v === hi ? "best" : hi !== lo && v === lo ? "worst" : "";
        return (
          <span key={k} className={tone} title={tone === "best" ? "Highest stat" : tone === "worst" ? "Lowest stat" : undefined}>
            <small>{l}</small>
            <i><u style={{ width: `${Math.min(100, (v / STAT_MAX) * 100)}%` }} /></i>
            <b>{v}</b>
          </span>
        );
      })}
    </span>
  );
}

function Moves({ m, a }: { m: Member; a: TeamAnalysis | null }) {
  const set = m.moves.length > 0;
  const moves = set
    ? m.moves.map((x) => ({ name: x.name, type: x.type, power: x.power }))
    : (a?.suggestions.find((x) => x.slot === m.slot)?.recommended_moves ?? []).map((x) => ({ name: x.name, type: x.type, power: x.power }));
  return (
    <div className="ro-moves">
      {moves.map((x) => (
        <span key={x.name}>
          <i style={{ background: typeHex(x.type ?? undefined) }} />
          {x.name}
          <em>{x.power || "—"}</em>
        </span>
      ))}
      {!set && <small>Suggested: no moves set yet</small>}
    </div>
  );
}

export default function TeamRoster({
  team,
  analysis,
  onEdit,
  onRemove,
}: {
  team: Team;
  analysis: TeamAnalysis | null;
  onEdit: (slot: number) => void;
  onRemove?: (slot: number) => Promise<void>;
}) {
  const [sel, setSel] = useState<number | null>(null);
  // Remove asks once more on the same button before clearing the slot.
  const [confirmSlot, setConfirmSlot] = useState<number | null>(null);
  const [removing, setRemoving] = useState(false);
  const members = [...team.members].sort((x, y) => x.slot - y.slot);
  const m = members.find((x) => x.slot === sel) ?? members[0];
  const role = (x: Member) => analysis?.roles.members.find((r) => r.slot === x.slot)?.role;
  return (
    <>
      <div className="ro-tiles">
        {Array.from({ length: 6 }, (_, i) => members.find((x) => x.slot === i + 1)).map((x, i) =>
          x ? (
            <button key={i} className={`ro-tile${m?.slot === x.slot ? " on" : ""}`} onClick={() => setSel(x.slot)}>
              <Sprite src={x.sprite_url} size={44} />
              <b>{x.name}</b>
            </button>
          ) : (
            <button key={i} className="ro-tile empty" onClick={() => onEdit(i + 1)} aria-label={`Add a Pokémon to slot ${i + 1}`}>
              +
            </button>
          ),
        )}
      </div>
      {m ? (
        <div className="ro-insp">
          <div className="ro-hd">
            <Sprite src={m.sprite_url} size={72} />
            <div>
              <b>{m.name}</b>
              <span className="tp">{m.types.map((t) => <Chip key={t} t={t} />)}</span>
              <small>{[role(m), `BST ${bst(m)}`].filter(Boolean).join(" · ")}</small>
            </div>
            <span className="ro-acts">
              {onRemove && (
                <button
                  className={`ro-rm${confirmSlot === m.slot ? " sure" : ""}`}
                  disabled={removing}
                  onBlur={() => setConfirmSlot(null)}
                  onClick={async () => {
                    if (confirmSlot !== m.slot) return setConfirmSlot(m.slot);
                    setRemoving(true);
                    try {
                      await onRemove(m.slot);
                      setSel(null);
                    } finally {
                      setRemoving(false);
                      setConfirmSlot(null);
                    }
                  }}
                >
                  {removing ? "Removing…" : confirmSlot === m.slot ? `Remove ${m.name}?` : "Remove"}
                </button>
              )}
              <button className="ro-edit" onClick={() => onEdit(m.slot)}>Edit</button>
            </span>
          </div>
          <div className="ro-cols">
            <div>
              <h3>Set</h3>
              <dl className="ro-dl">
                {setRows(analysis, m).map((r) => (
                  <div key={r.k}>
                    <dt>{r.k}</dt>
                    <dd>{r.v ? <><b>{r.v}</b>{r.note && <small>{r.note}</small>}</> : <span className="dash">—</span>}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div><h3>Base stats</h3><Stats m={m} /></div>
            <div><h3>Moves</h3><Moves m={m} a={analysis} /></div>
          </div>
        </div>
      ) : (
        <p className="ro-empty">No Pokémon yet. Tap a slot to add one.</p>
      )}
    </>
  );
}
