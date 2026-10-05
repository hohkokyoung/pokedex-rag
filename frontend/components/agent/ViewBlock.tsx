"use client";

import type { AskSource, AskView } from "@/lib/api";
import { dexLabel } from "@/lib/pokeTypes";
import { MoveChart } from "./views/MoveChart";
import { PokemonGrid } from "./views/PokemonCards";
import { RankChart, STAT_NAME } from "./views/RankChart";
import { LearnCheckStrip, LearnersStrip, LearnsetGroups, TypeChartStrip } from "./views/Strips";
import { CiteBadge, sprite, type Linking } from "./views/shared";

/** Draw one typed view with the visual for its kind. */
export function ViewBlock({ view, link }: { view: AskView; link: Linking }) {
  switch (view.kind) {
    case "ranking":
      return <RankChart view={view} link={link} />;
    case "pokemon_list":
      return <PokemonGrid cards={view.cards} link={link} title={view.title} />;
    case "type_chart":
      return <TypeChartStrip view={view} link={link} />;
    case "move_list":
      return <MoveChart view={view} link={link} />;
    case "learnset":
      return <LearnsetGroups view={view} link={link} />;
    case "learners":
      return <LearnersStrip view={view} link={link} />;
    case "learn_check":
      return <LearnCheckStrip view={view} link={link} />;
  }
}

/** What a view shows, in a few words ("who learns Will-O-Wisp", "Fire" …). */
export function viewCaption(view: AskView): string {
  switch (view.kind) {
    case "ranking":
      return `top ${view.rows.length} of ${view.total} by ${STAT_NAME[view.stat] ?? view.stat}`;
    case "pokemon_list":
      return view.title ?? `${view.cards.length} Pokémon`;
    case "type_chart":
      return view.types.map((t) => t[0].toUpperCase() + t.slice(1)).join("/");
    case "move_list":
      return view.moves.length === 1 ? view.moves[0].name : `${view.moves.length} moves by power`;
    case "learnset":
      return `${view.pokemon.name}’s moves`;
    case "learners":
      return `who learns ${view.move.name}`;
    case "learn_check":
      return `${view.pokemon.name} × ${view.move.name}`;
  }
}

/** Global ``[n]`` for each (step, step-local index), from the sources list. */
export function refIndex(sources: AskSource[]): Map<string, number> {
  const m = new Map<string, number>();
  for (const s of sources) if (s.step != null && s.step_index != null) m.set(`${s.step}:${s.step_index}`, s.n);
  return m;
}

/** Every step-local evidence index a view draws (so the panel doesn’t repeat it as a card). */
export function viewRefs(view: AskView): number[] {
  const refs = new Set(view.chunk_refs);
  const add = (r: number | null | undefined) => r != null && refs.add(r);
  if (view.kind === "ranking") view.rows.forEach((r) => add(r.ref));
  if (view.kind === "pokemon_list") view.cards.forEach((c) => add(c.ref));
  if (view.kind === "move_list") view.moves.forEach((m) => add(m.ref));
  if (view.kind === "learners") view.rows.forEach((c) => add(c.ref));
  if (view.kind === "learnset") view.groups.forEach((g) => add(g.ref));
  return [...refs];
}

const CHUNK_LABEL: Record<string, string> = {
  dex_entry: "Pokédex entry",
  profile: "profile",
  ability: "ability",
  item: "item",
  encounters: "where to find",
  type_chart: "type chart",
  move: "move",
};

/** A source no view covers (descriptions, dex entries, abilities, items, encounters). */
export function SourceCard({ s, link, delay = 0 }: { s: AskSource; link: Linking; delay?: number }) {
  const entry = s.chunk_type === "dex_entry" ? s.snippet.split(/Pokédex entry:\s*/)[1] ?? s.snippet : null;
  const art = sprite(s.pokemon_id ?? s.dex_number);
  return (
    <div
      className={`ax-evc ${link.hot === s.n ? "is-hot" : ""} ${link.cited.has(s.n) ? "" : "is-unused"}`}
      data-src={s.n}
      style={{ animationDelay: `${delay}ms` }}
      {...link.hover(s.n)}
    >
      <CiteBadge n={s.n} cited={link.cited} />
      <div className="ax-evc__top">
        {art && <img src={art} alt="" />}
        <div>
          <div className="ax-evc__name">{s.pokemon_name ?? s.source_ref ?? "Pokédex"}</div>
          <div className="ax-evc__meta">
            {s.dex_number ? dexLabel(s.dex_number) : CHUNK_LABEL[s.chunk_type] ?? s.chunk_type.replace("_", " ")}
          </div>
        </div>
      </div>
      {entry ? <q className="ax-evc__quote">{entry}</q> : <p className="ax-evc__text">{s.snippet}</p>}
    </div>
  );
}
