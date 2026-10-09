"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { gsap } from "gsap";
import { failureKind, getPokemon, listPokemon, getAbilityHolders, assetUrl, thumb } from "@/lib/api";
import type { AbilityHolder, FailureKind } from "@/lib/api";
import ServerNote from "@/components/ServerNote";
import { dexLabel, primaryColor, titleCase, typeColor, typeText, typeVars } from "@/lib/pokeTypes";
import type { FlavorEntry, PokemonDetail, PokemonSummary } from "@/lib/types";
import TypeBadge from "@/components/TypeBadge";
import StatBars from "@/components/StatBars";
import EvolutionChain from "@/components/EvolutionChain";
import TypeMatchups from "@/components/TypeMatchups";
import TrainingBreeding from "@/components/TrainingBreeding";
import MovesetPanel from "@/components/MovesetPanel";
import EncountersPanel from "@/components/EncountersPanel";
import FavoriteButton from "@/components/FavoriteButton";
import PointerFX from "@/components/PointerFX";
import { useStaggerReveal } from "@/hooks/useStaggerReveal";
import { useKeyNav } from "@/hooks/useKeyNav";
import { superEffectiveHits, useTypeChart } from "@/lib/typeChart";
import { useDialogFocus } from "@/hooks/useDialogFocus";

/** Search box to jump straight to any Pokémon (not just prev/next). */
function JumpSearch() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [res, setRes] = useState<PokemonSummary[]>([]);
  useEffect(() => {
    const query = q.trim();
    const id = setTimeout(() => {
      if (query.length < 2) { setRes([]); return; }
      listPokemon({ q: query, limit: 6 }).then((r) => setRes(r.items)).catch(() => setRes([]));
    }, 180);
    return () => clearTimeout(id);
  }, [q]);
  const go = (p: PokemonSummary) => {
    setQ("");
    setRes([]);
    router.push(p.form_id ? `/pokedex/${p.dex_number}?form=${p.form_id}` : `/pokedex/${p.dex_number}`);
  };
  const { listRef, onKeyDown, itemProps } = useKeyNav(res, go);
  return (
    <div className="d-jump">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
      <input
        aria-label="Jump to a Pokémon by name or dex number"
        placeholder="Jump to any Pokémon…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={onKeyDown}
        aria-autocomplete="list"
      />
      {res.length > 0 && (
        <div className="ac" role="listbox" ref={listRef}>
          {res.map((p, idx) => (
            <button key={p.id} role="option" {...itemProps(idx)} onClick={() => go(p)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img loading="lazy" decoding="async" src={thumb(p.sprite_url, 48)} alt="" />
              <span className="nm">{titleCase(p.name)}</span>
              <span className="tps">{p.types.map((t) => <TypeBadge key={t} type={t} size="sm" />)}</span>
              <span className="font-mono" style={{ fontSize: 12, color: "var(--faint)" }}>{dexLabel(p.dex_number)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function Chevron({ dir }: { dir: "left" | "right" }) {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d={dir === "left" ? "M15 6l-6 6 6 6" : "M9 6l6 6-6 6"} />
    </svg>
  );
}

/** Form name without the species name ("Pikachu Pop Star" → "Pop Star",
 *  "Mega Charizard X" → "Mega X"), since the page already says which species. */
function shortFormName(form: string, species: string) {
  const s = form.replace(new RegExp(`\\b${species}\\b`, "i"), "").replace(/\s+/g, " ").trim();
  return s || form;
}

const FORM_TAB_LIMIT = 6;

/** Form switcher in the Moveset panel's tab style. Long lists (Pikachu's caps)
 *  show the first few and expand in place; a selected form past the cut is
 *  always shown. */
function FormTabs({
  species,
  forms,
  value,
  onChange,
}: {
  species: string;
  forms: PokemonDetail["forms"];
  value: number | null;
  onChange: (id: number | null) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const all = [
    { id: null as number | null, label: "Base" },
    ...forms.map((f) => ({ id: f.id as number | null, label: shortFormName(f.name, species) })),
  ];
  const capped = all.length > FORM_TAB_LIMIT + 1 && !expanded;
  // Collapsed: the first few, plus the selected form if it sits past the cut.
  const shown = capped
    ? all.filter((f, i) => i < FORM_TAB_LIMIT || f.id === value)
    : all;
  return (
    <div className="mv-tabs d-formtabs reveal" role="tablist" aria-label="Form">
      {shown.map((f) => (
        <button
          key={f.id ?? "base"}
          type="button"
          role="tab"
          aria-selected={value === f.id}
          className={`mv-tab ${value === f.id ? "on" : ""}`}
          onClick={() => onChange(f.id)}
        >
          {f.label}
        </button>
      ))}
      {capped && (
        <button type="button" className="d-formtabs__more" onClick={() => setExpanded(true)}>
          +{all.length - shown.length} more
        </button>
      )}
      {expanded && (
        <button type="button" className="d-formtabs__more" onClick={() => setExpanded(false)}>
          Show less
        </button>
      )}
    </div>
  );
}

const GEN_ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"];

/** Dex entries: the newest game's entry featured as a quote, then one tab per
 *  generation (the Moveset tab style, newest selected) over boxes that list only
 *  that generation's games. Identical text across games is grouped by the API.
 *  Forms without per-game data get plain boxes. */
function DexEntries({ entries }: { entries: FlavorEntry[] }) {
  const gamesIn = (e: FlavorEntry, gen: number) =>
    (e.versions ?? []).filter((_, i) => e.version_generations?.[i] === gen);
  const gens = [...new Set(entries.flatMap((e) => e.version_generations ?? []))]
    .filter((g): g is number => g != null)
    .sort((a, b) => a - b);
  const newest = gens.at(-1);
  // Featured: the entry used by the newest game (the last one listed in that gen).
  const featured = newest != null ? entries.filter((e) => gamesIn(e, newest).length > 0).at(-1) : undefined;
  const [gen, setGen] = useState(newest);
  const shown = gen != null ? entries.filter((e) => gamesIn(e, gen).length > 0) : entries;
  return (
    <div className="panel d-panel">
      <h2 className="d-panel__title">Dex entries</h2>
      {featured && (
        <div className="d-dex__feat">
          <p className="font-display">“{featured.text}”</p>
          <div className="tb__chips">
            {(featured.versions ?? []).map((v) => <span key={v} className="tb__chip font-mono">{v}</span>)}
          </div>
        </div>
      )}
      {gens.length > 1 && (
        <div className="mv-tabs d-dex__tabs" role="tablist" aria-label="Generation">
          {gens.map((g) => (
            <button
              key={g}
              type="button"
              role="tab"
              aria-selected={g === gen}
              className={`mv-tab${g === gen ? " on" : ""}`}
              onClick={() => setGen(g)}
            >
              Gen {GEN_ROMAN[g] ?? g}<span className="c">{entries.filter((e) => gamesIn(e, g).length > 0).length}</span>
            </button>
          ))}
        </div>
      )}
      <div className="d-dex">
        {shown.map((e) => {
          const games = gen != null ? gamesIn(e, gen) : [];
          return (
            <div key={e.text} className="d-dex__card">
              <p>{e.text}</p>
              {games.length > 0 && (
                <div className="tb__chips">
                  {games.map((v) => <span key={v} className="tb__chip font-mono">{v}</span>)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <div style={{ fontSize: 12.5, fontWeight: 500, color: "var(--muted)" }}>
        {label}
      </div>
      <div style={{ fontSize: 15, marginTop: 4 }}>{value ?? "—"}</div>
    </div>
  );
}

/** Rarity marker folded into the dex eyebrow line — a gold (legendary) or violet
 *  (mythical) sparkled tag that reads as metadata beside the dex number, keeping
 *  the type-badge row clean. */
function RarityBadge({ kind }: { kind: "legendary" | "mythical" }) {
  return (
    <span className={`d-rarity d-rarity--${kind}`}>
      <span aria-hidden className="d-rarity__sep">·</span>
      <svg aria-hidden viewBox="0 0 24 24" width="11" height="11">
        <path
          d="M12 1.5l2.1 6.3a2 2 0 001.3 1.3l6.3 2.1-6.3 2.1a2 2 0 00-1.3 1.3L12 22.5l-2.1-6.3a2 2 0 00-1.3-1.3L2.3 12.8l6.3-2.1a2 2 0 001.3-1.3L12 1.5z"
          fill="currentColor"
        />
      </svg>
      {kind === "legendary" ? "Legendary" : "Mythical"}
    </span>
  );
}

/** "Show all" button + modal listing every other species that has an ability. */
function AbilityHolders({
  abilityId,
  name,
  effect,
  selfId,
}: {
  abilityId: number;
  name: string;
  effect: string | null;
  selfId: number;
}) {
  const [holders, setHolders] = useState<AbilityHolder[] | null>(null);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const dialogRef = useDialogFocus(open);

  // Fetch once so the button can show the count up front.
  useEffect(() => {
    let alive = true;
    getAbilityHolders(abilityId, 250)
      .then((hs) => { if (alive) setHolders(hs); })
      .catch(() => { if (alive) setHolders([]); });
    return () => { alive = false; };
  }, [abilityId]);

  // Lock scroll + close on Escape while the modal is open.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = prev; };
  }, [open]);

  const others = (holders ?? []).filter((h) => h.id !== selfId);
  if (holders !== null && others.length === 0) return null;

  const f = filter.trim().toLowerCase();
  const shown = f ? others.filter((h) => h.name.toLowerCase().includes(f)) : others;

  return (
    <div className="d-ability__holders">
      <button
        type="button"
        className="d-ability__toggle font-mono"
        disabled={holders === null}
        onClick={() => { setFilter(""); setOpen(true); }}
      >
        {holders === null
          ? "…"
          : `Show all ${others.length}${others.length >= 249 ? "+" : ""}`}
      </button>

      {open && typeof document !== "undefined" && createPortal(
        <div ref={dialogRef} className="d-hmodal" onClick={() => setOpen(false)} role="dialog" aria-modal="true" aria-label={`Pokémon with ${name}`} data-lenis-prevent>
          <div className="d-hmodal__card" onClick={(e) => e.stopPropagation()}>
            <div className="d-hmodal__top">
              <div className="d-hmodal__head">
                <span className="d-hmodal__badge font-mono">ABILITY</span>
                <b>{name}</b>
                <span className="d-hmodal__count font-mono">{others.length}{others.length >= 249 ? "+" : ""} species have it</span>
                <button className="d-hmodal__x" onClick={() => setOpen(false)} aria-label="Close">×</button>
              </div>
              {effect && <p className="d-hmodal__desc">{effect}</p>}
            </div>
            <div className="d-hmodal__filter">
              <input autoFocus aria-label="Filter species with this ability" placeholder="Filter these species…" value={filter} onChange={(e) => setFilter(e.target.value)} />
            </div>
            <div className="d-hmodal__grid" data-lenis-prevent>
              {shown.map((h) => (
                <Link
                  key={h.id}
                  href={`/pokedex/${h.dex_number}`}
                  title={h.is_hidden ? "hidden ability" : undefined}
                  className={h.is_hidden ? "is-hidden" : undefined}
                  onClick={() => setOpen(false)}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img loading="lazy" decoding="async" src={thumb(h.sprite_url, 160)} alt={h.name} />
                  <span>{titleCase(h.name)}</span>
                  <span className="tps-mini">{h.types.map((t) => <TypeBadge key={t} type={t} size="sm" />)}</span>
                </Link>
              ))}
              {shown.length === 0 && <div className="d-hmodal__empty">No species match “{filter.trim()}”.</div>}
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}

/** Male/female artwork for species with visual gender differences: the shown
 *  gender stands in front, the other waits smaller behind it (top-right) and
 *  swaps forward on click. Both images stay mounted so the swap can transition. */
function GenderStack({
  name, male, female, showFemale, onSwap,
}: { name: string; male: string; female: string; showFemale: boolean; onSwap: (female: boolean) => void }) {
  const looks = [
    { key: "male", isFemale: false, url: male, glyph: "♂", label: "Male" },
    { key: "female", isFemale: true, url: female, glyph: "♀", label: "Female" },
  ];
  const front = looks.find((l) => l.isFemale === showFemale)!;
  const back = looks.find((l) => l.isFemale !== showFemale)!;
  return (
    <div className="d-gstack">
      {looks.map((l) => {
        const isFront = l.isFemale === showFemale;
        return (
          <button
            key={l.key}
            type="button"
            className={`d-gstack__look ${isFront ? "is-front" : "is-back"}`}
            onClick={isFront ? undefined : () => onSwap(l.isFemale)}
            tabIndex={isFront ? -1 : 0}
            aria-disabled={isFront || undefined}
            aria-label={isFront ? undefined : `Show ${l.label.toLowerCase()} appearance`}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={assetUrl(l.url)} alt={isFront ? `${name} (${l.label.toLowerCase()})` : ""} width={460} height={460} />
          </button>
        );
      })}
      <span key={`now-${front.key}`} className="d-gstack__tag d-gstack__tag--front font-mono">
        <span aria-hidden>{front.glyph}</span> {front.label}
      </span>
      <button key={`alt-${back.key}`} type="button" className="d-gstack__tag d-gstack__tag--back font-mono" onClick={() => onSwap(back.isFemale)} tabIndex={-1} aria-hidden>
        <span>{back.glyph}</span> {back.label}
      </button>
    </div>
  );
}

export default function PokemonDetailView({ dex }: { dex: string }) {
  const [data, setData] = useState<PokemonDetail | null>(null);
  /** "not-found" → the 404 page; "offline"/"server" → a retryable notice. */
  const [error, setError] = useState<FailureKind | null>(null);
  const [attempt, setAttempt] = useState(0);
  // For the "Hits ×2" row; the defensive rows come with the detail payload.
  const typeChart = useTypeChart();
  const router = useRouter();
  const searchParams = useSearchParams();
  // Selected alternate form (null = the base species), persisted in the URL
  // as `?form=<id>` so it survives refresh/share.
  const formParam = searchParams.get("form");
  const formId = formParam ? Number(formParam) : null;

  const selectForm = (id: number | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (id == null) params.delete("form");
    else params.set("form", String(id));
    const qs = params.toString();
    router.replace(`/pokedex/${dex}${qs ? `?${qs}` : ""}`, { scroll: false });
  };
  const artRef = useRef<HTMLDivElement | null>(null);
  // Male/female artwork toggle for species with visual gender differences.
  const [female, setFemale] = useState(false);
  const scope = useStaggerReveal<HTMLElement>([data]);

  // The page remounts this component on `dex` change (via `key`), so initial
  // state is already null here — no synchronous reset needed.
  useEffect(() => {
    let active = true;
    getPokemon(dex)
      .then((d) => {
        if (!active) return;
        setError(null);
        setData(d);
      })
      .catch((e) => active && setError(failureKind(e)));
    return () => {
      active = false;
    };
  }, [dex, attempt]);

  // High-impact single tween: artwork scales/fades in once data arrives.
  useEffect(() => {
    const el = artRef.current;
    if (!data || !el) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;
    const tween = gsap.fromTo(
      el,
      { scale: 0.86, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.9, ease: "power4.out" },
    );
    return () => {
      tween.kill();
    };
  }, [data, formId]);

  if (error === "offline" || error === "server") {
    return (
      <main className="shell" style={{ paddingTop: 140, paddingBottom: 120 }}>
        <ServerNote kind={error} what={`Pokémon #${dex}`} onRetry={() => { setError(null); setAttempt((n) => n + 1); }} />
      </main>
    );
  }

  if (error) {
    return (
      <main className="shell" style={{ paddingTop: 160, paddingBottom: 120, textAlign: "center" }}>
        <p className="eyebrow">404</p>
        <h1 className="font-display" style={{ fontSize: "2.4rem", marginTop: 12 }}>Specimen not found</h1>
        <Link href="/pokedex" className="btn btn-ghost" style={{ marginTop: 24 }}>← Back to Pokédex</Link>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="shell" style={{ paddingTop: 200, paddingBottom: 200, textAlign: "center" }}>
        <span className="font-mono" style={{ color: "var(--muted)", letterSpacing: "0.2em" }}>SCANNING…</span>
      </main>
    );
  }

  // The form switcher swaps a subset of the view (sprite/name/types/stats/
  // abilities/matchups/physique); species-level info stays on the base data.
  const form = formId != null ? data.forms.find((f) => f.id === formId) ?? null : null;
  const view = {
    name: form ? form.name : titleCase(data.name),
    types: form ? form.types : data.types,
    sprite_url: form ? form.sprite_url : data.sprite_url,
    stats: form ? form.stats : data.stats,
    matchups: form ? form.matchups : data.matchups,
    height_m: form ? form.height_m : data.height_m,
    weight_kg: form ? form.weight_kg : data.weight_kg,
    abilities: form
      ? form.abilities.map((a) => ({ key: a.identifier, id: a.id, name: a.name, is_hidden: a.is_hidden, effect: a.effect }))
      : data.abilities.map((a) => ({ key: `${a.id}-${a.is_hidden}`, id: a.id, name: a.name, is_hidden: a.is_hidden, effect: a.effect })),
    evolution_members: form ? form.evolution_members : data.evolution_members,
    evolution_stages: form ? form.evolution_stages : data.evolution_stages,
    flavor_texts: form ? form.flavor_texts : data.flavor_texts,
    flavor_entries: form ? form.flavor_entries : data.flavor_entries,
    currentId: form ? form.id : data.id,
  };

  // Gender differences are cosmetic and only recorded for the base species.
  const femaleArt = form ? null : data.female_sprite_url ?? null;

  const color = primaryColor(view.types);
  const color2 = typeColor(view.types[1] ?? view.types[0]);
  const prev = data.dex_number > 1 ? data.dex_number - 1 : null;
  const next = data.dex_number < 1025 ? data.dex_number + 1 : null;

  // Evolution: a form with its own multi-member chain (e.g. a regional form
  // that evolves differently) shows that chain. Mega and other cosmetic forms
  // have no chain of their own, so fall back to the base species' family tree
  // (highlighting the base species, since the form isn't a chain member).
  const evo = form && view.evolution_members.length > 1
    ? { members: view.evolution_members, stages: view.evolution_stages, currentId: view.currentId, spinGuide: form.spin_guide }
    : { members: data.evolution_members, stages: data.evolution_stages, currentId: data.id, spinGuide: data.spin_guide };

  return (
    <main ref={scope} style={{ paddingTop: 84, paddingBottom: 100 }}>
      <title>{`pokérag — ${view.name}`}</title>
      {/* pointer parallax feeds only the hero art here (--px / --py) */}
      <PointerFX />
      {/* ---- nav row ---- */}
      <div className="shell d-navrow">
        <Link href="/pokedex" className="d-back">
          <Chevron dir="left" /> Pokédex
        </Link>
        <div className="d-navrow__right">
          <JumpSearch />
          <div className="d-step">
            {prev && <Link href={`/pokedex/${prev}`} aria-label={`Previous: ${dexLabel(prev)}`}><Chevron dir="left" /> {dexLabel(prev)}</Link>}
            {next && <Link href={`/pokedex/${next}`} aria-label={`Next: ${dexLabel(next)}`}>{dexLabel(next)} <Chevron dir="right" /></Link>}
          </div>
        </div>
      </div>

      {/* ---- form switcher (only when the species has alternate forms) ---- */}
      {data.forms.length > 0 && (
        <div className="shell d-formrow">
          <FormTabs species={data.name} forms={data.forms} value={formId} onChange={selectForm} />
        </div>
      )}

      {/* ---- hero ---- */}
      <section
        className="shell d-hero"
        style={{ ...typeVars(view.types[0], "--c"), "--c2": color2 } as React.CSSProperties}
      >
        <div className="d-hero__art">
          <span aria-hidden className="d-hero__dexbg font-display">{dexLabel(data.dex_number)}</span>
          <div className="d-hero__aura" />
          <div ref={artRef} className="d-art">
            {femaleArt ? (
              <GenderStack name={view.name} male={view.sprite_url} female={femaleArt} showFemale={female} onSwap={setFemale} />
            ) : (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img key={view.sprite_url} src={assetUrl(view.sprite_url)} alt={view.name} width={460} height={460} />
            )}
          </div>
        </div>

        <div className="d-hero__info">
          <p className="eyebrow reveal">
            {dexLabel(data.dex_number)}{data.generation ? ` · ${data.generation.name}` : ""}
            {data.is_legendary && <RarityBadge kind="legendary" />}
            {data.is_mythical && <RarityBadge kind="mythical" />}
          </p>
          <h1 className="font-display reveal" style={{ fontSize: "clamp(2.6rem, 7vw, 5rem)", marginTop: 8 }}>
            {view.name}
          </h1>
          {data.genus && <p className="reveal" style={{ color: "var(--ink-dim)", fontStyle: "italic", fontSize: "1.1rem", marginTop: 2 }}>{data.genus}</p>}

          <div className="reveal" style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap", alignItems: "center" }}>
            {view.types.map((t) => <TypeBadge key={t} type={t} />)}
            <FavoriteButton pokemonId={data.id} />
          </div>

          {data.flavor_text && (
            <p className="font-display reveal d-flavor">“{data.flavor_text}”</p>
          )}

          <div className="d-facts">
            <div className="reveal"><Fact label="Height" value={view.height_m ? `${view.height_m.toFixed(1)} m` : null} /></div>
            <div className="reveal"><Fact label="Weight" value={view.weight_kg ? `${view.weight_kg.toFixed(1)} kg` : null} /></div>
            <div className="reveal"><Fact label="Habitat" value={data.habitat ? titleCase(data.habitat) : null} /></div>
            <div className="reveal"><Fact label="Capture rate" value={data.capture_rate} /></div>
            <div className="reveal"><Fact label="Base exp" value={data.base_experience} /></div>
            <div className="reveal"><Fact label="Colour" value={data.color ? titleCase(data.color) : null} /></div>
          </div>
        </div>
      </section>

      {/* ---- abilities: full-width strip, one column per ability ---- */}
      <section className="shell">
        <div className="panel d-panel">
          <h2 className="d-panel__title">Abilities</h2>
          {view.abilities.length === 0 && (
            <p className="d-hmodal__empty">Ability data for this form isn’t in the PokéAPI dataset yet.</p>
          )}
          <div className="d-abilities" style={{ "--n": view.abilities.length } as React.CSSProperties}>
            {view.abilities.map((a) => (
              <div key={a.key} className={`d-ability${a.is_hidden ? " is-hidden" : ""}`}>
                <div className="d-ability__top">
                  {/* The home lookup's kind tag: ink "Ability", red "Hidden". */}
                  <span className="lc-tt d-ability__tag">{a.is_hidden ? "Hidden" : "Ability"}</span>
                  {a.id != null && <AbilityHolders abilityId={a.id} name={a.name} effect={a.effect} selfId={data.id} />}
                </div>
                <h3 className="d-ability__name">{a.name}</h3>
                {a.effect && <p className="d-ability__effect">{a.effect}</p>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- stats + type matchups: both have a fixed row count, so they pair evenly ---- */}
      <section className="shell d-grid" style={{ marginTop: 20 }}>
        <div className="panel d-panel d-panel--fill">
          <h2 className="d-panel__title">Base stats</h2>
          <StatBars key={view.name} stats={view.stats} color={color} textColor={typeText(view.types[0])} />
        </div>
        <div className="panel d-panel d-panel--fill">
          <h2 className="d-panel__title">Type matchups</h2>
          <TypeMatchups m={view.matchups} hits={typeChart ? superEffectiveHits(typeChart, view.types) : undefined} />
        </div>
      </section>

      {/* ---- training & breeding ---- */}
      <section className="shell" style={{ marginTop: 20 }}>
        <div className="panel d-panel">
          <h2 className="d-panel__title">Training &amp; breeding</h2>
          <TrainingBreeding d={data} />
        </div>
      </section>

      {/* ---- moveset ---- */}
      <section className="shell" style={{ marginTop: 20 }}>
        <div className="panel d-panel">
          <h2 className="d-panel__title">Moveset</h2>
          <MovesetPanel pokemonId={data.id} formId={formId} />
        </div>
      </section>

      {/* ---- evolution ---- */}
      {evo.members.length > 1 && (
        <section className="shell" style={{ marginTop: 20 }}>
          <div className="panel d-panel">
            <h2 className="d-panel__title">Evolution</h2>
            <EvolutionChain
              members={evo.members}
              stages={evo.stages}
              currentId={evo.currentId}
              spinGuide={evo.spinGuide}
            />
          </div>
        </section>
      )}

      {/* ---- dex entries ---- */}
      {view.flavor_entries.length > 0 && (
        <section className="shell" style={{ marginTop: 20 }}>
          <DexEntries key={view.currentId} entries={view.flavor_entries} />
        </section>
      )}

      {/* ---- where to find ---- */}
      <section className="shell" style={{ marginTop: 20 }}>
        <div className="panel d-panel">
          <h2 className="d-panel__title">Where to find</h2>
          <EncountersPanel key={view.currentId} pokemonId={view.currentId} />
        </div>
      </section>
    </main>
  );
}
