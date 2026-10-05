"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useKeyNav } from "@/hooks/useKeyNav";

export type DropdownOption<V> = { value: V; label: string; hint?: string; short?: string };
type Row<V> = { all: true } | { all: false; opt: DropdownOption<V> };

/**
 * Home-style dropdown: a white field button (mono key + value + chevron) opening
 * a popover list with a red keyboard/hover bar and a ✓ on chosen rows — the same
 * language as the home calculator's pickers. `multiple` keeps it open and toggles
 * rows; `allLabel` adds a first row that clears the selection.
 */
export default function Dropdown<V extends string | number>({
  label,
  prefix,
  options,
  value,
  onChange,
  multiple = false,
  allLabel,
  align = "left",
}: {
  /** Accessible name. */
  label: string;
  /** Optional visible lead-in before the value, e.g. "Sort by". */
  prefix?: string;
  options: DropdownOption<V>[];
  value: V[];
  onChange: (next: V[]) => void;
  multiple?: boolean;
  allLabel?: string;
  align?: "left" | "right";
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const off = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", off);
    return () => document.removeEventListener("mousedown", off);
  }, [open]);

  // Stable array: useKeyNav resets its highlight whenever it gets a new one.
  const rows = useMemo<Row<V>[]>(
    () => (open ? [...(allLabel ? [{ all: true } as const] : []), ...options.map((opt) => ({ all: false as const, opt }))] : []),
    [open, allLabel, options],
  );

  const choose = (r: Row<V>) => {
    if (r.all) onChange([]);
    else if (!multiple) onChange([r.opt.value]);
    else onChange(
      value.includes(r.opt.value)
        ? value.filter((v) => v !== r.opt.value)
        : options.map((o) => o.value).filter((v) => v === r.opt.value || value.includes(v)),
    );
    if (!multiple || r.all) setOpen(false);
  };
  const { active, listRef, onKeyDown, itemProps } = useKeyNav(rows, choose);

  const picked = options.filter((o) => value.includes(o.value));
  const shown =
    picked.length === 0 ? allLabel ?? "Any"
    : picked.length === 1 ? picked[0].label
    : picked.length <= 3 ? picked.map((o) => o.short ?? o.label).join(" · ")
    : `${picked.length} selected`;
  // Every label the button can show, stacked invisibly under the real one so the
  // button keeps its widest width — otherwise it resizes per pick and the popover
  // anchored to it jitters.
  const ghosts = useMemo(() => {
    const shorts = options.map((o) => o.short ?? o.label).sort((a, b) => b.length - a.length);
    return [
      allLabel ?? "Any",
      ...options.map((o) => o.label),
      ...(multiple ? [shorts.slice(0, 3).join(" · "), `${options.length} selected`] : []),
    ];
  }, [options, allLabel, multiple]);

  return (
    <div className="pk-dd" ref={ref}>
      <button
        type="button"
        className="pk-dd__btn"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`${label}: ${shown}`}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === "Escape") { setOpen(false); return; }
          if (!open) {
            if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true); }
            return;
          }
          if (e.key === " ") { e.preventDefault(); if (rows[active]) choose(rows[active]); return; }
          onKeyDown(e);
        }}
      >
        {prefix && <span className="k">{prefix}</span>}
        <b>
          <span className="v">{shown}</span>
          {ghosts.map((g, i) => <span key={i} className="g" aria-hidden>{g}</span>)}
        </b>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden><path d="M6 9l6 6 6-6" /></svg>
      </button>
      {open && (
        <div
          className={`pk-dd__box${align === "right" ? " r" : ""}`}
          role="listbox"
          aria-multiselectable={multiple || undefined}
          ref={listRef}
          data-lenis-prevent
        >
          {rows.map((r, k) => {
            const on = r.all ? value.length === 0 : value.includes(r.opt.value);
            return (
              <button
                key={r.all ? "__all" : String(r.opt.value)}
                type="button"
                role="option"
                aria-checked={on}
                className={on ? "on" : ""}
                aria-selected={k === active}
                onMouseMove={itemProps(k).onMouseMove}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(r)}
              >
                <span className="nm">{r.all ? allLabel : r.opt.label}</span>
                {!r.all && r.opt.hint && <span className="mt">{r.opt.hint}</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
