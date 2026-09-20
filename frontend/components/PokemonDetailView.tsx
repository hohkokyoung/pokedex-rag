"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { getPokemon, listPokemon, assetUrl } from "@/lib/api";
import { dexLabel, primaryColor, titleCase, typeColor } from "@/lib/pokeTypes";
import type { PokemonDetail, PokemonSummary } from "@/lib/types";
import TypeBadge from "@/components/TypeBadge";
import StatBars from "@/components/StatBars";
import EvolutionChain from "@/components/EvolutionChain";
import TypeMatchups from "@/components/TypeMatchups";
import TrainingBreeding from "@/components/TrainingBreeding";
import MovesetPanel from "@/components/MovesetPanel";
import FavoriteButton from "@/components/FavoriteButton";
import { useStaggerReveal } from "@/hooks/useStaggerReveal";

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
  const go = (dex: number) => { setQ(""); setRes([]); router.push(`/pokedex/${dex}`); };
  return (
    <div className="d-jump">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
      <input
        placeholder="Jump to any Pokémon…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && res[0]) go(res[0].dex_number); }}
      />
      {res.length > 0 && (
        <div className="ac">
          {res.map((p) => (
            <button key={p.id} onClick={() => go(p.dex_number)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={assetUrl(`/sprites/official-artwork/${p.dex_number}.png`)} alt="" />
              <span style={{ flex: 1, fontWeight: 600 }}>{titleCase(p.name)}</span>
              <span className="font-mono" style={{ fontSize: 11, color: "var(--faint)" }}>{dexLabel(p.dex_number)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <div className="font-mono" style={{ fontSize: 9.5, letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--faint)" }}>
        {label}
      </div>
      <div style={{ fontSize: 15, marginTop: 4 }}>{value ?? "—"}</div>
    </div>
  );
}

export default function PokemonDetailView({ dex }: { dex: string }) {
  const [data, setData] = useState<PokemonDetail | null>(null);
  const [error, setError] = useState(false);
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
  const scope = useStaggerReveal<HTMLElement>([data]);

  // The page remounts this component on `dex` change (via `key`), so initial
  // state is already null here — no synchronous reset needed.
  useEffect(() => {
    let active = true;
    getPokemon(dex)
      .then((d) => active && setData(d))
      .catch(() => active && setError(true));
    return () => {
      active = false;
    };
  }, [dex]);

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
      ? form.abilities.map((a) => ({ key: a.identifier, name: a.name, is_hidden: a.is_hidden, effect: a.effect }))
      : data.abilities.map((a) => ({ key: `${a.id}-${a.is_hidden}`, name: a.name, is_hidden: a.is_hidden, effect: a.effect })),
    evolution_members: form ? form.evolution_members : data.evolution_members,
    evolution_stages: form ? form.evolution_stages : data.evolution_stages,
    flavor_texts: form ? form.flavor_texts : data.flavor_texts,
    currentId: form ? form.id : data.id,
  };

  const color = primaryColor(view.types);
  const color2 = typeColor(view.types[1] ?? view.types[0]);
  const prev = data.dex_number > 1 ? data.dex_number - 1 : null;
  const next = data.dex_number < 1025 ? data.dex_number + 1 : null;

  return (
    <main ref={scope} style={{ paddingTop: 84 }}>
      {/* ---- nav row ---- */}
      <div className="shell" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, position: "relative", zIndex: 20 }}>
        <Link href="/pokedex" className="font-mono" style={{ fontSize: 12, color: "var(--muted)", letterSpacing: "0.1em", flex: "none" }}>
          ← CATALOG
        </Link>
        <JumpSearch />
        <div style={{ display: "flex", gap: 8, flex: "none" }}>
          {prev && <Link href={`/pokedex/${prev}`} className="btn btn-ghost" style={{ padding: "6px 14px", fontSize: 12 }}>← {dexLabel(prev)}</Link>}
          {next && <Link href={`/pokedex/${next}`} className="btn btn-ghost" style={{ padding: "6px 14px", fontSize: 12 }}>{dexLabel(next)} →</Link>}
        </div>
      </div>

      {/* ---- form switcher (only when the species has alternate forms) ---- */}
      {data.forms.length > 0 && (
        <div className="shell">
          <div className="d-formswitch reveal" role="tablist" aria-label="Form">
            <button
              type="button"
              role="tab"
              aria-selected={formId === null}
              className={`d-formpill ${formId === null ? "is-active" : ""}`}
              onClick={() => selectForm(null)}
            >
              {titleCase(data.name)}
            </button>
            {data.forms.map((f) => (
              <button
                key={f.id}
                type="button"
                role="tab"
                aria-selected={formId === f.id}
                className={`d-formpill ${formId === f.id ? "is-active" : ""}`}
                onClick={() => selectForm(f.id)}
              >
                {titleCase(f.name)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ---- hero ---- */}
      <section
        className="shell d-hero"
        style={{ "--c": color, "--c2": color2 } as React.CSSProperties}
      >
        <div className="d-hero__art">
          <span aria-hidden className="d-hero__dexbg font-display">{dexLabel(data.dex_number)}</span>
          <div className="d-hero__aura" />
          <div ref={artRef} className="d-art">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img key={view.sprite_url} src={assetUrl(view.sprite_url)} alt={view.name} width={460} height={460} />
          </div>
        </div>

        <div className="d-hero__info">
          <p className="eyebrow reveal">{dexLabel(data.dex_number)}{data.generation ? ` · ${data.generation.name}` : ""}</p>
          <h1 className="font-display reveal" style={{ fontSize: "clamp(2.6rem, 7vw, 5rem)", marginTop: 8 }}>
            {view.name}
          </h1>
          {data.genus && <p className="reveal" style={{ color: "var(--ink-dim)", fontStyle: "italic", fontSize: "1.1rem", marginTop: 2 }}>{data.genus}</p>}

          <div className="reveal" style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap", alignItems: "center" }}>
            {view.types.map((t) => <TypeBadge key={t} type={t} />)}
            {data.is_legendary && <span className="d-flag">Legendary</span>}
            {data.is_mythical && <span className="d-flag">Mythical</span>}
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

      {/* ---- stats + abilities ---- */}
      <section className="shell d-grid">
        <div className="panel d-panel">
          <h2 className="d-panel__title font-mono">BASE STATS</h2>
          <StatBars key={view.name} stats={view.stats} color={color} />
        </div>

        <div className="panel d-panel">
          <h2 className="d-panel__title font-mono">ABILITIES</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {view.abilities.map((a) => (
              <div key={a.key} className="d-ability">
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 15, fontWeight: 600 }}>{a.name}</span>
                  {a.is_hidden && <span className="d-ability__hidden font-mono">HIDDEN</span>}
                </div>
                {a.effect && <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 4 }}>{a.effect}</p>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- training & breeding ---- */}
      <section className="shell" style={{ marginTop: 20 }}>
        <div className="panel d-panel">
          <h2 className="d-panel__title font-mono">TRAINING &amp; BREEDING</h2>
          <TrainingBreeding d={data} />
        </div>
      </section>

      {/* ---- type matchups ---- */}
      <section className="shell" style={{ marginTop: 20 }}>
        <div className="panel d-panel">
          <h2 className="d-panel__title font-mono">TYPE MATCHUPS</h2>
          <TypeMatchups m={view.matchups} />
        </div>
      </section>

      {/* ---- moveset ---- */}
      <section className="shell" style={{ marginTop: 20 }}>
        <div className="panel d-panel">
          <h2 className="d-panel__title font-mono">MOVESET</h2>
          <MovesetPanel pokemonId={data.id} formId={formId} />
        </div>
      </section>

      {/* ---- evolution ---- */}
      {(!form || view.evolution_members.length > 1) && (
        <section className="shell" style={{ marginTop: 20 }}>
          <div className="panel d-panel">
            <h2 className="d-panel__title font-mono">EVOLUTION</h2>
            <EvolutionChain
              members={view.evolution_members}
              stages={view.evolution_stages}
              currentId={view.currentId}
            />
          </div>
        </section>
      )}

      {/* ---- dex entries ---- */}
      {view.flavor_texts.length > 0 && (
        <section className="shell" style={{ marginTop: 20, marginBottom: 100 }}>
          <div className="panel d-panel">
            <h2 className="d-panel__title font-mono">DEX ENTRIES · {view.flavor_texts.length}</h2>
            <div className="d-entries">
              {view.flavor_texts.slice(0, 6).map((t, i) => (
                <p key={i} className="d-entry">{t}</p>
              ))}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
