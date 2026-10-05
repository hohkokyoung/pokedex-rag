"use client";

import { useCallback, useRef } from "react";

type TiltOptions = {
  max?: number; // max rotation in degrees
  scale?: number; // hover scale
  glare?: boolean;
};

/**
 * Pointer-driven 3D tilt. Returns a ref plus handlers to spread on an element;
 * the element rotates in X/Y toward the cursor (perspective set in CSS) so
 * inner layers with translateZ read as real depth. Smoothly resets on leave.
 */
export function useTilt<T extends HTMLElement>({ max = 12, scale = 1.02 }: TiltOptions = {}) {
  const ref = useRef<T | null>(null);

  const onMove = useCallback(
    (e: React.PointerEvent) => {
      const el = ref.current;
      if (!el) return;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      el.style.setProperty("--rx", `${(-py * max).toFixed(2)}deg`);
      el.style.setProperty("--ry", `${(px * max).toFixed(2)}deg`);
      el.style.setProperty("--gx", `${(px * 100 + 50).toFixed(1)}%`);
      el.style.setProperty("--gy", `${(py * 100 + 50).toFixed(1)}%`);
      el.style.setProperty("--tscale", String(scale));
    },
    [max, scale],
  );

  const onLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--rx", "0deg");
    el.style.setProperty("--ry", "0deg");
    el.style.setProperty("--tscale", "1");
  }, []);

  return { ref, onPointerMove: onMove, onPointerLeave: onLeave };
}
