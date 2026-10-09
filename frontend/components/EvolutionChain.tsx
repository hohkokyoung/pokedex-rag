"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { thumb } from "@/lib/api";
import { titleCase, typeVars } from "@/lib/pokeTypes";
import type { CosmeticVariant, EvolutionDisplay, EvolutionMember, EvolutionStage, SpinGuide } from "@/lib/types";
import { useDialogFocus } from "@/hooks/useDialogFocus";

type Edge = { to: number; stage: EvolutionStage };

/** The chain's spin guide (Milcery → Alcremie), served with the evolution data. */
const SpinGuideContext = createContext<SpinGuide | null>(null);

function ConditionRow({
  cond,
  open,
  onToggle,
}: {
  cond: EvolutionDisplay;
  open: boolean;
  onToggle: () => void;
}) {
  // Every requirement is one "recipe" block: the trigger on top, each extra
  // condition as its own "+" row inside the same frame — all equally required.
  const [primary, ...quals] = cond.chips;
  if (!primary) return null;
  return (
    <div className="evo2-cond">
      <span className={`evo2-req ${quals.length ? "evo2-req--multi" : ""}`}>
        <span className="evo2-req__main">
          {primary.label}
          {cond.description && (
            <button
              type="button"
              className={`evo2-q ${open ? "is-open" : ""}`}
              aria-expanded={open}
              aria-label="Explain this requirement"
              onClick={onToggle}
            >
              ?
              <span className="evo2-tip" role="tooltip">{cond.description}</span>
            </button>
          )}
        </span>
        {quals.map((q) => (
          <span key={q.label} className="evo2-req__and">
            <span className="evo2-req__plus" aria-hidden="true">+</span>
            {q.label}
          </span>
        ))}
      </span>
    </div>
  );
}

// Alcremie-style names: "<cream> <sweet>", e.g. "Ruby Swirl Strawberry Sweet".
const CREAM_SWEET = /^(.+ (?:Cream|Swirl)) (.+ Sweet)$/;
const uniq = (xs: string[]) => [...new Set(xs)];

/** One look's artwork; lazy-loaded since Alcremie alone has 63. */
function VariantArt({ v, size }: { v: CosmeticVariant; size: number }) {
  if (!v.sprite_url) return <span className="evo2-vart evo2-vart--none" style={{ width: size, height: size }} aria-hidden="true" />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img className="evo2-vart" src={thumb(v.sprite_url, 160)} alt={v.name} loading="lazy" width={size} height={size} />;
}

const PEEK = 232; // hover preview card size (px)

/** Enlarged look of the hovered grid cell, floated beside it (fixed, so the grid's
    scroll container can't clip it). Flips to the left near the viewport edge. */
function VariantPeek({ v, rect }: { v: CosmeticVariant; rect: DOMRect }) {
  const gap = 10;
  const left = rect.right + gap + PEEK <= window.innerWidth ? rect.right + gap : rect.left - gap - PEEK;
  const top = Math.min(Math.max(8, rect.top + rect.height / 2 - PEEK / 2), window.innerHeight - PEEK - 44);
  return (
    <div className="evo2-peek" style={{ left, top, width: PEEK }} aria-hidden="true">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img loading="lazy" decoding="async" src={thumb(v.sprite_url, 160)} alt="" width={PEEK - 24} height={PEEK - 24} />
      <b>{v.name}</b>
    </div>
  );
}

/** "63 variants" pill + a modal listing a member's cosmetic variants. Cream × sweet
    names (Alcremie) are split into the two independent choices that make them. */
function VariantsButton({ member }: { member: EvolutionMember }) {
  const [open, setOpen] = useState(false);
  const dialogRef = useDialogFocus(open);
  const [peek, setPeek] = useState<{ v: CosmeticVariant; rect: DOMRect } | null>(null);
  const variants = member.variants ?? [];
  const guide = useContext(SpinGuideContext);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = prev; };
  }, [open]);
  if (variants.length < 2) return null;
  const parts = variants.map((v) => v.name.match(CREAM_SWEET));
  const combo = parts.every(Boolean);
  const creams = combo ? uniq(parts.map((m) => m![1])) : [];
  const sweets = combo ? uniq(parts.map((m) => m![2])) : [];
  const name = titleCase(member.name);
  const byName = new Map(variants.map((v) => [v.name, v]));
  const toppingOf = new Map(guide?.toppings.map((t) => [t.sweet, t.topping]));
  const ruleOf = new Map(guide?.creams.map((c) => [c.cream, c]));
  return (
    <>
      <button type="button" className="evo2-variants font-mono" onClick={() => setOpen(true)}>
        {variants.length} variants
      </button>
      {open && typeof document !== "undefined" && createPortal(
        <div ref={dialogRef} className="d-hmodal" onClick={() => setOpen(false)} role="dialog" aria-modal="true" aria-label={`${name} variants`} data-lenis-prevent>
          <div className="d-hmodal__card" onClick={(e) => e.stopPropagation()}>
            <div className="d-hmodal__top">
              <div className="d-hmodal__head">
                <span className="d-hmodal__badge font-mono">VARIANTS</span>
                <b>{name}</b>
                <span className="d-hmodal__count font-mono">
                  {combo ? `${creams.length} creams × ${sweets.length} sweets = ${variants.length}` : `${variants.length} looks`}
                </span>
                <button className="d-hmodal__x" onClick={() => setOpen(false)} aria-label="Close">×</button>
              </div>
              <p className="d-hmodal__desc">
                {combo
                  ? "Every cream pairs with every sweet. Cosmetic only: all variants share the same stats, types and abilities."
                  : "Cosmetic only: all variants share the same stats, types and abilities."}
              </p>
            </div>
            <div className="evo2-vbody" data-lenis-prevent onScroll={() => setPeek(null)}>
              {combo ? (
                <>
                  <section className="evo2-vgroup">
                    <h4 className="font-mono">All {variants.length} looks · cream × sweet</h4>
                    <div className="evo2-tablewrap">
                      <table className="evo2-matrix" onMouseLeave={() => setPeek(null)}>
                        <thead>
                          <tr>
                            <th scope="col"><span className="sr-only">Cream</span></th>
                            {sweets.map((sw) => <th key={sw} scope="col">{sw.replace(/ Sweet$/, "")}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {creams.map((c) => (
                            <tr key={c}>
                              <th scope="row">{c}</th>
                              {sweets.map((sw) => {
                                const v = byName.get(`${c} ${sw}`);
                                if (!v) return <td key={sw} />;
                                const show = (e: React.SyntheticEvent<HTMLElement>) =>
                                  v.sprite_url && setPeek({ v, rect: e.currentTarget.getBoundingClientRect() });
                                return (
                                  <td
                                    key={sw}
                                    tabIndex={0}
                                    aria-label={v.name}
                                    className={peek?.v === v ? "is-peek" : undefined}
                                    onMouseEnter={show}
                                    onFocus={show}
                                    onBlur={() => setPeek(null)}
                                  >
                                    <VariantArt v={v} size={64} />
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                  {guide && (
                    <section className="evo2-vgroup">
                      <h4 className="font-mono">How it works</h4>
                      <ol className="evo2-steps">
                        {guide.steps.map((step, i) => (
                          <li key={i}><span className="font-mono">{i + 1}</span>{step}</li>
                        ))}
                      </ol>
                      <p>The Sweet it holds picks the topping; how you spin picks the cream. Any Sweet works with any cream.</p>
                    </section>
                  )}
                  <section className="evo2-vgroup">
                    <h4 className="font-mono">Sweet · the topping ({sweets.length})</h4>
                    <div className="evo2-sweets">
                      {sweets.map((sw) => (
                        <div key={sw} className="evo2-sweet">
                          <b>{sw}</b>
                          <span>{toppingOf.has(sw) ? `${toppingOf.get(sw)} topping` : "—"}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                  <section className="evo2-vgroup">
                    <h4 className="font-mono">Cream · how to spin ({creams.length})</h4>
                    <div className="evo2-tablewrap">
                      <table className="evo2-table">
                        <thead>
                          <tr><th>Cream</th><th>Spin</th><th>For</th><th>When</th></tr>
                        </thead>
                        <tbody>
                          {[...[...ruleOf.keys()].filter((c) => creams.includes(c)), ...creams.filter((c) => !ruleOf.has(c))].map((c) => {
                            const rule = ruleOf.get(c);
                            return (
                              <tr key={c}>
                                <td><b>{c}</b></td>
                                <td>{rule ? <><span className="evo2-dir" aria-hidden="true">{rule.direction === "Clockwise" ? "↻" : "↺"}</span>{rule.direction}</> : "—"}</td>
                                <td>{rule?.duration ?? "—"}</td>
                                <td>
                                  {rule?.time ?? "—"}
                                  {rule?.time.includes("PM") && <span className="evo2-tag font-mono">1-hour window</span>}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                    <p className="evo2-vnote">Rules from Pokémon Sword &amp; Shield. Day and night follow the in-game clock.</p>
                  </section>
                </>
              ) : (
                <div className="evo2-vgrid">
                  {variants.map((v) => (
                    <figure
                      key={v.name}
                      className={`evo2-vcard ${peek?.v === v ? "is-peek" : ""}`}
                      tabIndex={0}
                      onMouseEnter={(e) => v.sprite_url && setPeek({ v, rect: e.currentTarget.getBoundingClientRect() })}
                      onMouseLeave={() => setPeek(null)}
                      onFocus={(e) => v.sprite_url && setPeek({ v, rect: e.currentTarget.getBoundingClientRect() })}
                      onBlur={() => setPeek(null)}
                    >
                      <VariantArt v={v} size={112} />
                      <figcaption>{v.name}</figcaption>
                    </figure>
                  ))}
                </div>
              )}
            </div>
            {peek && <VariantPeek v={peek.v} rect={peek.rect} />}
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}

/**
 * A member's card: its artwork, name, and — for anything other than the chain
 * root — the requirement chips to reach it. The root shows a neutral "Base form"
 * marker so it reads the same as the others.
 */
function EvoCard({
  member,
  stage,
  currentId,
  open,
  onToggle,
  fork = 0,
}: {
  member: EvolutionMember;
  stage: EvolutionStage | null;
  currentId: number;
  open: boolean;
  onToggle: () => void;
  fork?: number;
}) {
  const cond = stage?.display ?? null;
  const isCurrent = member.id === currentId;
  return (
    <div className="evo2-card" style={typeVars(member.types[0], "--c") as React.CSSProperties}>
      <Link
        href={member.form_id ? `/pokedex/${member.dex_number}?form=${member.form_id}` : `/pokedex/${member.dex_number}`}
        className={`evo2-mon ${isCurrent ? "is-current" : ""}`}
        onClick={
          isCurrent
            ? (e) => {
                // Already viewing this Pokémon — don't re-navigate, just glide back up.
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: "smooth" });
              }
            : undefined
        }
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={thumb(member.sprite_url, 160)} alt={member.name} loading="lazy" width={80} height={80} />
        <span className="evo2-nm font-mono">{titleCase(member.name)}</span>
      </Link>
      {stage === null ? (
        fork > 1 ? null : <span className="evo2-base font-mono">Base form</span>
      ) : (
        cond && <ConditionRow cond={cond} open={open} onToggle={onToggle} />
      )}
      {fork > 1 && <span className="evo2-fork font-mono">Evolves into 1 of {fork}</span>}
      <VariantsButton member={member} />
    </div>
  );
}

/** Plain grey line joining two stages of a straight line. */
function EvoLink() {
  return <span className="evo2-link" aria-hidden="true" />;
}

function Subtree({
  id,
  edgeStage,
  byId,
  edges,
  currentId,
  openSet,
  toggle,
}: {
  id: number;
  edgeStage: EvolutionStage | null;
  byId: Map<number, EvolutionMember>;
  edges: Map<number, Edge[]>;
  currentId: number;
  openSet: Set<number>;
  toggle: (to: number) => void;
}) {
  const member = byId.get(id);
  if (!member) return null;
  const children = edges.get(id) ?? [];
  const cardKey = edgeStage ? edgeStage.to_id : -1;
  const card = (
    <EvoCard
      member={member}
      stage={edgeStage}
      currentId={currentId}
      open={openSet.has(cardKey)}
      onToggle={() => toggle(cardKey)}
      fork={children.length}
    />
  );
  const sub = (edge: Edge) => (
    <Subtree
      key={edge.to}
      id={edge.to}
      edgeStage={edge.stage}
      byId={byId}
      edges={edges}
      currentId={currentId}
      openSet={openSet}
      toggle={toggle}
    />
  );

  if (children.length > 1) {
    // Many one-step outcomes (Eevee) sit in a grid of up to 4 per row; fewer or
    // longer branches (Tyrogue, Wurmple) stack one line per row. A grey bracket
    // joins the base to the first card of each row.
    const leaves = children.every((c) => !edges.get(c.to)?.length);
    const cols = leaves && children.length >= 4 ? Math.min(4, Math.ceil(children.length / 2)) : 1;
    const rows: Edge[][] = [];
    for (let i = 0; i < children.length; i += cols) rows.push(children.slice(i, i + cols));
    return (
      <div className="evo2-sub evo2-split">
        {card}
        <span className="evo2-stub" aria-hidden="true" />
        <div className={`evo2-rows ${cols > 1 ? "evo2-rows--grid" : ""}`} style={{ "--cols": cols } as React.CSSProperties}>
          {rows.map((row, i) => (
            <div key={i} className="evo2-row">{row.map(sub)}</div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="evo2-sub">
      {card}
      {children.length === 1 && (
        <>
          <EvoLink />
          {sub(children[0])}
        </>
      )}
    </div>
  );
}

export default function EvolutionChain({
  members,
  stages,
  currentId,
  spinGuide = null,
}: {
  members: EvolutionMember[];
  stages: EvolutionStage[];
  currentId: number;
  spinGuide?: SpinGuide | null;
}) {
  const [openSet, setOpenSet] = useState<Set<number>>(new Set());
  const toggle = (to: number) =>
    setOpenSet((prev) => {
      const next = new Set(prev);
      if (next.has(to)) next.delete(to);
      else next.add(to);
      return next;
    });

  if (members.length <= 1) {
    return (
      <p className="font-mono" style={{ color: "var(--faint)", fontSize: 12, letterSpacing: "0.08em" }}>
        This Pokémon does not evolve.
      </p>
    );
  }

  const byId = new Map(members.map((m) => [m.id, m]));
  const edges = new Map<number, Edge[]>();
  const toIds = new Set<number>();
  for (const s of stages) {
    if (s.from_id == null || s.to_id == null) continue;
    if (!byId.has(s.from_id) || !byId.has(s.to_id)) continue;
    toIds.add(s.to_id);
    edges.set(s.from_id, [...(edges.get(s.from_id) ?? []), { to: s.to_id, stage: s }]);
  }

  const roots = members.filter((m) => !toIds.has(m.id));
  const rootIds = roots.length > 0 ? roots.map((m) => m.id) : [members[0].id];

  return (
    <SpinGuideContext.Provider value={spinGuide}>
    <div className="evo2-tree">
      {rootIds.map((rid) => (
        <Subtree
          key={rid}
          id={rid}
          edgeStage={null}
          byId={byId}
          edges={edges}
          currentId={currentId}
          openSet={openSet}
          toggle={toggle}
        />
      ))}
    </div>
    </SpinGuideContext.Provider>
  );
}
