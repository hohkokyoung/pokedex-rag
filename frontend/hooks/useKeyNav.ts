"use client";

import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from "react";

/* Arrow-key navigation for suggestion dropdowns: ↑/↓ move the highlight,
   Enter chooses it, Escape clears it. The first row is highlighted by default.
   Attach onKeyDown to the input, listRef to the results container, and itemProps(idx) to each row. */
export function useKeyNav<T>(items: T[], onChoose: (item: T) => void) {
  const [active, setActive] = useState(0);
  const [seen, setSeen] = useState(items);
  const listRef = useRef<HTMLDivElement>(null);
  // Re-highlight the first row whenever the result set changes (render-time reset).
  if (items !== seen) { setSeen(items); setActive(0); }
  // Keep the highlighted row in view when navigating a long list.
  useEffect(() => {
    listRef.current?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: "nearest" });
  }, [active]);
  const onKeyDown = (e: ReactKeyboardEvent) => {
    if (!items.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((i) => (i + 1) % items.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((i) => (i <= 0 ? items.length - 1 : i - 1)); }
    // Enter picks the highlighted row, or the top result when nothing is highlighted.
    else if (e.key === "Enter") { e.preventDefault(); onChoose(items[active >= 0 && active < items.length ? active : 0]); }
    else if (e.key === "Escape") { setActive(-1); }
  };
  const itemProps = (idx: number) => ({
    "aria-selected": idx === active,
    onMouseMove: () => setActive(idx),
  });
  return { active, setActive, listRef, onKeyDown, itemProps };
}
