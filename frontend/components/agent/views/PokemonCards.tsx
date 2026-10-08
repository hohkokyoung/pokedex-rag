"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import type { PokemonCardData } from "@/lib/api";
import { STAT_LABEL, STAT_ORDER, STAT_SHORT } from "@/lib/askEvidence";
import { dexLabel, typeVars } from "@/lib/pokeTypes";
import { CiteBadge, Types, sprite, type Linking } from "./shared";
import { thumb } from "@/lib/api";

/** One Pokémon as evidence: art, types, stats or a dex quote, coverage moves. */
export function PokemonCard({ c, link, delay = 0 }: { c: PokemonCardData; link: Linking; delay?: number }) {
  const n = link.n(c.ref);
  const hasStats = STAT_ORDER.every((k) => c.stats[k] !== undefined);
  const body: ReactNode = c.entry ? (
    <q className="ax-evc__quote">{c.entry}</q>
  ) : hasStats ? (
    <div className="ax-evc__stats">
      {STAT_ORDER.map((k) => (
        <span key={k} className="ax-evc__stat" title={`${STAT_LABEL[k]} ${c.stats[k]}`}>
          <span className="ax-evc__bar">
            <span style={{ height: `${Math.min(100, ((c.stats[k] ?? 0) / 180) * 100)}%` }} />
          </span>
          <span className="ax-evc__k">{STAT_SHORT[k]}</span>
          <span className="ax-evc__v">{c.stats[k]}</span>
        </span>
      ))}
      {c.total !== null && (
        <span className="ax-evc__total">
          <b>{c.total}</b>BST
        </span>
      )}
    </div>
  ) : null;

  const inner = (
    <>
      <CiteBadge n={n} cited={link.cited} />
      <div className="ax-evc__top">
        {sprite(c.pokemon_id ?? c.dex_number) && <img loading="lazy" decoding="async" src={thumb(sprite(c.pokemon_id ?? c.dex_number), 160)} alt="" />}
        <div>
          <div className="ax-evc__name">{c.name}</div>
          <div className="ax-evc__meta">
            {c.dex_number ? dexLabel(c.dex_number) : ""}
            {c.match !== null && <> · {Math.round(c.match * 100)}% match</>}
            {c.via && <span className="ax-evc__via">{c.via}</span>}
          </div>
        </div>
      </div>
      <Types types={c.types} />
      {c.coverage.length > 0 && (
        <span className="ax-evc__moves">
          {c.coverage.map((m) => (
            <span key={m.move} className="ax-evc__move" style={typeVars(m.type) as React.CSSProperties}>
              {m.move}
            </span>
          ))}
        </span>
      )}
      {body}
    </>
  );
  const cls = `ax-evc ${n !== null && link.hot === n ? "is-hot" : ""} ${n !== null && !link.cited.has(n) ? "is-unused" : ""}`;
  const props = { className: cls, "data-src": n ?? undefined, style: { animationDelay: `${delay}ms` }, ...link.hover(n) };
  return c.dex_number ? (
    <Link href={`/pokedex/${c.dex_number}`} {...props}>
      {inner}
    </Link>
  ) : (
    <div {...props}>{inner}</div>
  );
}

export function PokemonGrid({ cards, link, title }: { cards: PokemonCardData[]; link: Linking; title?: string | null }) {
  if (!cards.length) return null;
  return (
    <>
      {title && <div className="ax-view__title">{title}</div>}
      <div className="ax-ev__grid" data-n={Math.min(cards.length, 5)}>
        {cards.map((c, i) => (
          <PokemonCard key={`${c.name}-${i}`} c={c} link={link} delay={i * 50} />
        ))}
      </div>
    </>
  );
}
