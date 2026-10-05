"use client";

import { useEffect, useRef } from "react";

/**
 * Reveals `.reveal` descendants of the returned ref as they scroll into view,
 * with a light per-batch stagger. Uses IntersectionObserver (robust under React
 * Strict Mode and graceful if animation frames stall), re-observing newly
 * appended elements when `deps` change. Respects prefers-reduced-motion.
 */
export function useStaggerReveal<T extends HTMLElement>(deps: unknown[]) {
  const scope = useRef<T | null>(null);

  useEffect(() => {
    const root = scope.current;
    if (!root) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const targets = Array.from(
      root.querySelectorAll<HTMLElement>(".reveal:not(.is-visible)"),
    );
    if (targets.length === 0) return;

    if (reduced || !("IntersectionObserver" in window)) {
      targets.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries, obs) => {
        let i = 0;
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const el = entry.target as HTMLElement;
          el.style.transitionDelay = `${(i % 6) * 55}ms`;
          el.classList.add("is-visible");
          // Drop the stagger once revealed so later hover transitions aren't delayed.
          el.addEventListener("transitionend", () => { el.style.transitionDelay = ""; }, { once: true });
          obs.unobserve(el);
          i += 1;
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 },
    );

    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return scope;
}
