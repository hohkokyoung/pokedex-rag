"use client";

import { useState } from "react";
import type { LearnCheckView, LearnersView, LearnsetView, TypeChartView } from "@/lib/api";
import { titleCase, typeColor } from "@/lib/pokeTypes";
import { PokemonGrid } from "./PokemonCards";
import { CiteBadge, METHOD_COLOR, METHOD_LABEL, type Linking } from "./shared";

function TypeChips({ types }: { types: string[] }) {
  return (
    <span className="ax-types">
      {types.map((t) => (
        <span key={t} className="ax-type" style={{ background: typeColor(t) }}>
          {titleCase(t)}
        </span>
      ))}
    </span>
  );
}

/** How a type (or dual typing) fares: weaknesses first, then resistances, immunities, offence. */
export function TypeChartStrip({ view, link }: { view: TypeChartView; link: Linking }) {
  const n = link.n(view.chunk_refs[0]);
  const rows: [string, string[], string][] = [
    ["Weak to", view.weak_4x, "4×"],
    ["Weak to", view.weak_2x, "2×"],
    ["Resists", view.resist_half, "½×"],
    ["Resists", view.resist_quarter, "¼×"],
    ["Immune to", view.immune, "0×"],
    ["Hits hard", view.strong_against, "2×"],
  ];
  const shown = rows.filter(([, types]) => types.length);
  return (
    <div
      className={`ax-tc ${n !== null && link.hot === n ? "is-hot" : ""} ${n !== null && !link.cited.has(n) ? "is-unused" : ""}`}
      data-src={n ?? undefined}
      {...link.hover(n)}
    >
      <div className="ax-tc__target">
        {view.types.map((t) => (
          <span key={t} className="ax-type" style={{ background: typeColor(t) }}>
            {titleCase(t)}
          </span>
        ))}
        <span className="ax-tc__lbl">type chart</span>
      </div>
      {shown.map(([label, types, mult], i) => (
        <div key={label + mult} className={`ax-tc__row ${i === 0 && label === "Weak to" ? "is-key" : ""}`}>
          <span className="ax-tc__lbl">
            {label} <b>{mult}</b>
          </span>
          <TypeChips types={types} />
        </div>
      ))}
      <CiteBadge n={n} cited={link.cited} />
    </div>
  );
}

/** "Can X learn Y?" — the yes/no from the learnset. */
export function LearnCheckStrip({ view, link }: { view: LearnCheckView; link: Linking }) {
  const n = link.n(view.chunk_refs[0]);
  const game = view.game ? ` in ${view.game}` : "";
  return (
    <div className={`ax-check ${view.ok ? "is-yes" : "is-no"} ${n !== null && link.hot === n ? "is-hot" : ""}`} data-src={n ?? undefined} {...link.hover(n)}>
      <span className="ax-check__mark" aria-hidden>
        {view.ok ? "✓" : "✕"}
      </span>
      <span className="ax-check__text">
        <b>{view.ok ? "Yes" : "No"}</b> — {view.pokemon.name}{" "}
        {view.ok ? `can learn ${view.move.name} ${view.how ?? ""}${game}` : `can’t learn ${view.move.name}${game}`}
      </span>
      <CiteBadge n={n} cited={link.cited} />
    </div>
  );
}

const ORDER = ["level-up", "machine", "tutor", "egg"];

/** "Who learns Y?" — how many, split by method, then the standout users. */
export function LearnersStrip({ view, link }: { view: LearnersView; link: Linking }) {
  const n = link.n(view.chunk_refs[1] ?? view.chunk_refs[0]);
  const methods = Object.entries(view.by_method).sort(
    ([a], [b]) => (ORDER.indexOf(a) + 1 || 9) - (ORDER.indexOf(b) + 1 || 9),
  );
  return (
    <>
      <div className={`ax-learners ${n !== null && link.hot === n ? "is-hot" : ""}`} data-src={n ?? undefined} {...link.hover(n)}>
        <div className="ax-learners__big">
          <b>{view.total}</b>
          <span>
            {view.scope.length ? `${view.scope.join(" ")} ` : ""}Pokémon learn {view.move.name}
            {view.game ? ` in ${view.game}` : ""}
          </span>
        </div>
        {methods.length > 0 && (
          <>
            <div className="ax-learners__bar" aria-hidden>
              {methods.map(([m, c]) => (
                <span key={m} style={{ flexGrow: c, background: METHOD_COLOR[m] ?? "var(--faint)" }} />
              ))}
            </div>
            <div className="ax-learners__legend">
              {methods.map(([m, c]) => (
                <span key={m}>
                  <i style={{ background: METHOD_COLOR[m] ?? "var(--faint)" }} />
                  {c} {m === "egg" ? "egg move" : `by ${METHOD_LABEL[m] ?? m}`}
                </span>
              ))}
            </div>
          </>
        )}
        <CiteBadge n={n} cited={link.cited} />
      </div>
      <PokemonGrid cards={view.rows} link={link} />
    </>
  );
}

const PREVIEW = 16;

function LearnGroup({ group, link }: { group: LearnsetView["groups"][number]; link: Linking }) {
  const [open, setOpen] = useState(false);
  const n = link.n(group.ref);
  const visible = open ? group.moves : group.moves.slice(0, PREVIEW);
  return (
    <div className={`ax-ls ${n !== null && link.hot === n ? "is-hot" : ""}`} data-src={n ?? undefined} {...link.hover(n)}>
      <header className="ax-ls__head">
        <span className="ax-ls__method" style={{ background: METHOD_COLOR[group.method] ?? "var(--faint)" }}>
          {METHOD_LABEL[group.method] ?? titleCase(group.label)}
        </span>
        <span className="ax-ls__count">{group.moves.length} moves</span>
        <CiteBadge n={n} cited={link.cited} />
      </header>
      <ul className="ax-ls__moves">
        {visible.map((m) => (
          <li
            key={m.name}
            className="ax-ls__move"
            style={{ "--tc": typeColor(m.type) } as React.CSSProperties}
            title={`${titleCase(m.type)} · ${titleCase(m.damage_class ?? "status")}${m.power ? ` · ${m.power} power` : ""}`}
          >
            {m.level !== null && <span className="ax-ls__lv">Lv {m.level}</span>}
            <span className="ax-ls__name">{m.name}</span>
            {m.power !== null && <span className="ax-ls__pow">{m.power}</span>}
          </li>
        ))}
      </ul>
      {group.moves.length > PREVIEW && (
        <button type="button" className="ax-ls__more" onClick={() => setOpen((o) => !o)}>
          {open ? "Show fewer" : `Show all ${group.moves.length}`}
        </button>
      )}
    </div>
  );
}

/** A Pokémon's moves, one group per learn method. */
export function LearnsetGroups({ view, link }: { view: LearnsetView; link: Linking }) {
  return (
    <>
      {view.game && <div className="ax-view__title">{view.pokemon.name} in {view.game}</div>}
      {view.groups.map((g) => (
        <LearnGroup key={g.method} group={g} link={link} />
      ))}
    </>
  );
}
