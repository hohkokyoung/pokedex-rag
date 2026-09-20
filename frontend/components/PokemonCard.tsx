"use client";

import Link from "next/link";
import { useRef } from "react";
import { assetUrl } from "@/lib/api";
import { dexLabel, primaryColor, titleCase, typeColor } from "@/lib/pokeTypes";
import type { PokemonSummary } from "@/lib/types";
import TypeBadge from "@/components/TypeBadge";

/**
 * A "specimen" card: big official artwork over a type-tinted aura, mono dex
 * readout, and a subtle pointer-tracked 3D tilt.
 */
export default function PokemonCard({ p }: { p: PokemonSummary }) {
  const ref = useRef<HTMLAnchorElement | null>(null);
  const color = primaryColor(p.types);
  const color2 = typeColor(p.types[1] ?? p.types[0]);

  function onMove(e: React.MouseEvent) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    // Drive the CSS tilt (transform lives in the stylesheet with translateZ layers).
    el.style.setProperty("--rx", `${(-py * 10).toFixed(2)}deg`);
    el.style.setProperty("--ry", `${(px * 13).toFixed(2)}deg`);
    el.style.setProperty("--gx", `${(px * 60 + 50).toFixed(1)}%`);
    el.style.setProperty("--gy", `${(py * 60 + 30).toFixed(1)}%`);
  }
  function onLeave() {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--rx", "0deg");
    el.style.setProperty("--ry", "0deg");
  }

  return (
    <Link
      ref={ref}
      href={p.form_id ? `/pokedex/${p.dex_number}?form=${p.form_id}` : `/pokedex/${p.dex_number}`}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className="poke-card reveal"
      style={
        {
          "--c": color,
          "--c2": color2,
        } as React.CSSProperties
      }
    >
      <div className="poke-card__glow" />
      <div className="poke-card__top">
        <span className="font-mono poke-card__dex">{dexLabel(p.dex_number)}</span>
        {(p.is_legendary || p.is_mythical) && (
          <span className="font-mono poke-card__tag">
            {p.is_mythical ? "MYTHICAL" : "LEGENDARY"}
          </span>
        )}
      </div>

      <div className="poke-card__art">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={assetUrl(p.sprite_url)}
          alt={p.name}
          loading="lazy"
          width={220}
          height={220}
        />
      </div>

      <div className="poke-card__body">
        <h3 className="font-display poke-card__name">{titleCase(p.name)}</h3>
        {p.genus && <span className="poke-card__genus">{p.genus}</span>}
        <div className="poke-card__types">
          {p.types.map((t) => (
            <TypeBadge key={t} type={t} size="sm" />
          ))}
        </div>
      </div>

      <div className="poke-card__foot font-mono">
        <span>BST</span>
        <span className="poke-card__bst">{p.base_stat_total}</span>
      </div>
    </Link>
  );
}
