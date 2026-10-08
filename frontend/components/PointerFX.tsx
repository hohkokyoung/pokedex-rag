"use client";

import { useEffect } from "react";

/**
 * Publishes a smoothed, normalized pointer position (-1..1) as CSS custom
 * properties --px / --py on the root element, plus a scroll-linked --sy.
 * Layered elements read these to drift at different depths (parallax) and to
 * subtly tilt, which is what sells the 3D feel. rAF-lerped for smoothness;
 * disabled under reduced-motion (vars stay 0, so the UI is flat but correct).
 */
export default function PointerFX() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const root = document.documentElement;
    let tx = 0, ty = 0, px = 0, py = 0;
    let raf = 0;

    const onMove = (e: PointerEvent) => {
      tx = (e.clientX / window.innerWidth - 0.5) * 2;
      ty = (e.clientY / window.innerHeight - 0.5) * 2;
      if (!raf) raf = requestAnimationFrame(loop);
    };
    const loop = () => {
      px += (tx - px) * 0.09;
      py += (ty - py) * 0.09;
      root.style.setProperty("--px", px.toFixed(4));
      root.style.setProperty("--py", py.toFixed(4));
      if (Math.abs(tx - px) > 0.001 || Math.abs(ty - py) > 0.001) {
        raf = requestAnimationFrame(loop);
      } else {
        raf = 0;
      }
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      if (raf) cancelAnimationFrame(raf);
      root.style.removeProperty("--px");
      root.style.removeProperty("--py");
    };
  }, []);

  return null;
}
