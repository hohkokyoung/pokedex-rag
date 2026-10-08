import Link from "next/link";
import { thumb } from "@/lib/api";
import { STAT_LABELS, dexLabel, titleCase, typeChip } from "@/lib/pokeTypes";
import type { PokemonSummary } from "@/lib/types";

/**
 * Catalog card in the home page's card language: a white panel with a mono
 * label row, the artwork on plain white, home type tags and a
 * mono BST readout.
 */
/** Highest and lowest stat (first in dex order on ties); null if all equal. */
function extremes(stats: PokemonSummary["stats"]) {
  if (!stats) return null;
  const rows = STAT_LABELS.map((s) => ({ short: s.short, label: s.label, val: stats[s.key] }));
  const best = rows.reduce((a, b) => (b.val > a.val ? b : a));
  const worst = rows.reduce((a, b) => (b.val < a.val ? b : a));
  return best.val === worst.val ? null : { best, worst };
}

export default function PokemonCard({ p }: { p: PokemonSummary }) {
  const ex = extremes(p.stats);
  return (
    <Link
      href={p.form_id ? `/pokedex/${p.dex_number}?form=${p.form_id}` : `/pokedex/${p.dex_number}`}
      className="poke-card reveal"
    >
      <div className="poke-card__top">
        <span>{dexLabel(p.dex_number)}</span>
        {(p.is_legendary || p.is_mythical) && (
          <span className="poke-card__tag">{p.is_mythical ? "Mythical" : "Legendary"}</span>
        )}
      </div>

      <div className="poke-card__art">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={thumb(p.sprite_url, 160)} alt={p.name} loading="lazy" width={220} height={220} />
      </div>

      <h3 className="poke-card__name">{titleCase(p.name)}</h3>
      {p.genus && <span className="poke-card__genus">{p.genus}</span>}
      <div className="poke-card__types">
        {p.types.map((t) => (
          <span key={t} className="lc-tt" style={typeChip(t)}>
            {t}
          </span>
        ))}
      </div>

      <div className="poke-card__foot">
        <span>BST</span>
        {ex && (
          <span className="poke-card__ext">
            <span className="poke-card__ext-hi" title={`Highest: ${ex.best.label} ${ex.best.val}`}>
              {ex.best.short} <em>{ex.best.val}</em>
            </span>
            <span className="poke-card__ext-lo" title={`Lowest: ${ex.worst.label} ${ex.worst.val}`}>
              {ex.worst.short} <em>{ex.worst.val}</em>
            </span>
          </span>
        )}
        <b>{p.base_stat_total}</b>
      </div>
    </Link>
  );
}
