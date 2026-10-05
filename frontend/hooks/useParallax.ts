"use client";

import { useEffect, useRef } from "react";

/**
 * Lightweight scroll parallax: translates the returned ref vertically based on
 * its position in the viewport. `factor` < 0 makes it drift up as you scroll
 * (content lags), > 0 drifts down. rAF-throttled, dependency-free, and
 * disabled under prefers-reduced-motion.
 */
export function useParallax<T extends HTMLElement>(factor = -0.12) {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let raf = 0;
    const update = () => {
      raf = 0;
      const rect = el.getBoundingClientRect();
      const fromCenter = rect.top + rect.height / 2 - window.innerHeight / 2;
      el.style.transform = `translate3d(0, ${(fromCenter * factor).toFixed(1)}px, 0)`;
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    update();
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [factor]);

  return ref;
}
