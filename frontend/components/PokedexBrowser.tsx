"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { failureKind, listPokemon, type FailureKind, type ListParams } from "@/lib/api";
import ServerNote from "@/components/ServerNote";
import type { PokemonSummary } from "@/lib/types";
import { TYPE_ORDER, titleCase, typeVars } from "@/lib/pokeTypes";
import PokemonCard from "@/components/PokemonCard";
import Dropdown, { type DropdownOption } from "@/components/Dropdown";
import { useStaggerReveal } from "@/hooks/useStaggerReveal";

const PAGE = 36;
const GENS: DropdownOption<number>[] = [
  ["I", "Kanto"], ["II", "Johto"], ["III", "Hoenn"], ["IV", "Sinnoh"], ["V", "Unova"],
  ["VI", "Kalos"], ["VII", "Alola"], ["VIII", "Galar"], ["IX", "Paldea"],
].map(([n, region], i) => ({ value: i + 1, label: `Gen ${n}`, short: n, hint: region }));
const SORTS: DropdownOption<string>[] = [
  { value: "dex", label: "Dex №", hint: "national order" },
  { value: "name", label: "Name", hint: "A – Z" },
  { value: "total", label: "Total", hint: "base stat total" },
  { value: "hp", label: "HP" },
  { value: "attack", label: "Attack" },
  { value: "defense", label: "Defense" },
  { value: "speed", label: "Speed" },
];

export default function PokedexBrowser() {
  const [q, setQ] = useState("");
  const [types, setTypes] = useState<string[]>([]);
  const [generations, setGenerations] = useState<number[]>([]);
  const [sort, setSort] = useState("dex");
  const [order, setOrder] = useState<"asc" | "desc">("asc");
  const [legendary, setLegendary] = useState(false);

  const [items, setItems] = useState<PokemonSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  /** Why the first page failed to load (null = it loaded); never shown as "no results". */
  const [failed, setFailed] = useState<Exclude<FailureKind, "not-found"> | null>(null);
  const [attempt, setAttempt] = useState(0);

  const grid = useStaggerReveal<HTMLDivElement>([items]);
  const reqId = useRef(0);
  // True while any page is in flight (or a filter change is pending), so the
  // scroll sentinel never fires a second request or pages with stale filters.
  const busy = useRef(false);
  const sentinel = useRef<HTMLDivElement>(null);
  // The filter panel scrolls away with the page; once it's fully under the nav a
  // floating summary pill takes over, and "Edit" reopens the panel as a popover.
  const panel = useRef<HTMLDivElement>(null);
  const pop = useRef<HTMLDivElement>(null);
  const [away, setAway] = useState(false);
  const [editing, setEditing] = useState(false);

  const params = useCallback(
    (off: number): ListParams => ({
      q: q || undefined,
      types: types.length ? types : undefined,
      generations,
      legendary: legendary || undefined,
      sort,
      order,
      limit: PAGE,
      offset: off,
    }),
    [q, types, generations, legendary, sort, order],
  );

  // (re)load from the top whenever filters change (debounced for search).
  useEffect(() => {
    const id = ++reqId.current;
    busy.current = true;
    const handle = setTimeout(() => {
      setLoading(true);
      listPokemon(params(0))
        .then((r) => {
          if (id !== reqId.current) return;
          setFailed(null);
          setItems(r.items);
          setTotal(r.total);
        })
        .catch((e) => {
          if (id === reqId.current) {
            setItems([]);
            setTotal(0);
            setFailed(failureKind(e) === "offline" ? "offline" : "server");
          }
        })
        .finally(() => {
          if (id !== reqId.current) return;
          busy.current = false;
          setLoading(false);
        });
    }, 220);
    return () => clearTimeout(handle);
  }, [params, attempt]);

  const hasMore = items.length < total;

  const loadMore = useCallback(() => {
    if (busy.current) return;
    busy.current = true;
    const id = reqId.current;
    setLoading(true);
    listPokemon(params(items.length))
      .then((r) => {
        if (id === reqId.current) setItems((prev) => [...prev, ...r.items]);
      })
      .catch(() => {})
      .finally(() => {
        if (id !== reqId.current) return;
        busy.current = false;
        setLoading(false);
      });
  }, [params, items.length]);

  // Infinite scroll: fetch the next page well before the sentinel reaches the
  // viewport. Re-observing after each page re-checks a sentinel that's still close.
  useEffect(() => {
    const el = sentinel.current;
    if (!el || !hasMore) return;
    const io = new IntersectionObserver(
      ([entry]) => entry.isIntersecting && loadMore(),
      { rootMargin: "0px 0px 1200px 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [hasMore, loadMore]);

  useEffect(() => {
    const el = panel.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        const gone = !entry.isIntersecting && entry.boundingClientRect.top < 0;
        setAway(gone);
        if (!gone) setEditing(false);
      },
      { rootMargin: "-65px 0px 0px 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  // Changing a filter from the popover swaps the whole list; jump back to its top
  // (just past the panel, so the pill stays) instead of stranding the user deep
  // in a shorter page.
  useEffect(() => {
    const bottom = panel.current?.getBoundingClientRect().bottom;
    if (bottom === undefined || bottom > 65) return;
    window.scrollTo({ top: bottom + window.scrollY - 64, behavior: "instant" });
  }, [q, types, generations, legendary, sort, order]);

  useEffect(() => {
    if (!editing) return;
    const off = (e: MouseEvent) => {
      const t = e.target as Element;
      if (!pop.current?.contains(t) && !t.closest(".pk-pill")) setEditing(false);
    };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") setEditing(false); };
    document.addEventListener("mousedown", off);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", off);
      document.removeEventListener("keydown", esc);
    };
  }, [editing]);

  function toggleType(t: string) {
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : prev.length < 2 ? [...prev, t] : [prev[1], t],
    );
  }

  const genLabel = generations.map((g) => GENS[g - 1].label).join(", ");
  const summary = [
    q && `“${q}”`,
    types.length ? types.map(titleCase).join(" + ") : "All types",
    generations.length === 0 ? "All gens"
      : generations.length <= 3 ? `Gen ${generations.map((g) => GENS[g - 1].short).join(" · ")}`
      : `${generations.length} gens`,
    legendary && "Legendary",
    `${SORTS.find((s) => s.value === sort)?.label} ${order === "asc" ? "↑" : "↓"}`,
  ].filter(Boolean);

  const filters = (
    <>
        <div className="pk-filters__row">
          <div className="pk-search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <circle cx="11" cy="11" r="7" />
              <path d="M21 21l-4-4" />
            </svg>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by name or dex number…"
              aria-label="Search Pokémon"
            />
            {q && (
              <button className="pk-search__clear" onClick={() => setQ("")} aria-label="Clear">
                ✕
              </button>
            )}
          </div>

          <div className="pk-controls">
            <Dropdown
              label="Generation"
              options={GENS}
              value={generations}
              onChange={setGenerations}
              multiple
              allLabel="All generations"
            />
            <Dropdown
              label="Sort"
              prefix="Sort by"
              options={SORTS}
              value={[sort]}
              onChange={([s]) => setSort(s)}
              align="right"
            />
            <button
              className="pk-order"
              onClick={() => setOrder((o) => (o === "asc" ? "desc" : "asc"))}
              aria-label={order === "asc" ? "Sorted ascending. Switch to descending" : "Sorted descending. Switch to ascending"}
              title={order === "asc" ? "Ascending" : "Descending"}
            >
              {order === "asc" ? "↑" : "↓"}
            </button>
            <button
              className={`pk-toggle ${legendary ? "is-on" : ""}`}
              aria-pressed={legendary}
              onClick={() => setLegendary((v) => !v)}
            >
              Legendary
            </button>
          </div>
        </div>

        <div className="pk-types">
          {TYPE_ORDER.map((t) => (
            <button
              key={t}
              onClick={() => toggleType(t)}
              aria-pressed={types.includes(t)}
              className={types.includes(t) ? "on" : ""}
              style={typeVars(t) as React.CSSProperties}
            >
              {t}
            </button>
          ))}
        </div>
    </>
  );

  return (
    <div>
      {/* ---- filter panel (scrolls away) ---- */}
      <div className="pk-filters" ref={panel}>{filters}</div>

      {/* ---- floating summary pill + popover once the panel is gone ---- */}
      <div className={`pk-float${away ? " is-shown" : ""}`} inert={!away}>
        <button
          type="button"
          className="pk-pill"
          aria-expanded={editing}
          aria-haspopup="dialog"
          aria-label={`Edit filters: ${summary.join(", ")}`}
          onClick={() => setEditing((v) => !v)}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0" />
            <circle cx="16" cy="6" r="2" /><circle cx="10" cy="12" r="2" /><circle cx="18" cy="18" r="2" />
          </svg>
          <span className="pk-pill__n">{total.toLocaleString()}</span>
          <span className="pk-pill__s">{summary.join(" · ")}</span>
          <svg className="pk-pill__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden>
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
        {editing && (
          <div className="pk-pop" ref={pop} role="dialog" aria-label="Filters">
            {filters}
          </div>
        )}
      </div>

      {/* ---- result meta ---- */}
      <div className="pk-meta font-mono" style={failed ? { visibility: "hidden" } : undefined}>
        <span>
          {total.toLocaleString()} {total === 1 ? "specimen" : "specimens"}
          {generations.length > 0 && ` · ${genLabel}`}
          {types.length > 0 && ` · ${types.map(titleCase).join(" + ")}`}
        </span>
        {loading && items.length === 0 && <span className="pk-meta__loading">loading…</span>}
      </div>

      {/* ---- grid ---- */}
      <h2 className="sr-only">Results</h2>
      <div className="poke-grid" ref={grid}>
        {items.map((p) => (
          <PokemonCard key={`${p.id}-${p.form_id ?? ""}`} p={p} />
        ))}
        {hasMore &&
          loading &&
          items.length > 0 &&
          Array.from({ length: 5 }, (_, i) => <div key={`sk${i}`} className="poke-card poke-card--skeleton" aria-hidden />)}
      </div>

      {failed && !loading && (
        <ServerNote kind={failed} what="the Pokédex" onRetry={() => setAttempt((n) => n + 1)} />
      )}
      {items.length === 0 && !loading && !failed && (
        <div className="pk-empty font-mono">No specimens match these filters.</div>
      )}

      <div ref={sentinel} aria-hidden />
      {!hasMore && items.length > PAGE && (
        <div className="pk-end font-mono">End of catalog · {total.toLocaleString()} specimens</div>
      )}
    </div>
  );
}
