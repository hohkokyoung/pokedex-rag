"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { RankingView } from "@/lib/api";
import { CiteBadge, Types, sprite, type Linking } from "./shared";

export const STAT_NAME: Record<string, string> = {
  hp: "HP",
  attack: "Attack",
  defense: "Defense",
  sp_attack: "Sp. Atk",
  sp_defense: "Sp. Def",
  speed: "Speed",
  base_stat_total: "stat total",
  height_m: "height (m)",
  weight_kg: "weight (kg)",
  capture_rate: "capture rate",
};

/** A ranked stat chart: one bar per Pokémon, scaled to the leader. */
export function RankChart({ view, link }: { view: RankingView; link: Linking }) {
  const values = view.rows.map((r) => r.value ?? 0);
  const max = Math.max(...values, 1);
  const [grown, setGrown] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setGrown(true));
    return () => cancelAnimationFrame(id);
  }, []);
  return (
    <ol className="ax-rank">
      {view.rows.map((r, i) => {
        const n = link.n(r.ref);
        const v = r.value ?? 0;
        return (
          <li key={`${r.name}-${i}`} data-src={n ?? undefined} style={{ animationDelay: `${i * 60}ms` }}>
            <Link
              href={r.dex_number ? `/pokedex/${r.dex_number}` : "#"}
              className={`ax-rank__row ${n !== null && link.hot === n ? "is-hot" : ""} ${i === 0 ? "is-top" : ""}`}
              {...link.hover(n)}
            >
              <span className="ax-rank__pos">{i + 1}</span>
              <img src={sprite(r.pokemon_id ?? r.dex_number)} alt="" className="ax-rank__art" />
              <span className="ax-rank__name">
                {r.name}
                <Types types={r.types} />
              </span>
              <span className="ax-rank__track">
                <span
                  className="ax-rank__fill"
                  style={{ transform: `scaleX(${grown ? v / max : 0})`, transitionDelay: `${150 + i * 70}ms` }}
                />
              </span>
              <span className="ax-rank__val">{Number.isInteger(v) ? v : v.toFixed(1)}</span>
              <CiteBadge n={n} cited={link.cited} className="ax-rank__n" />
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
