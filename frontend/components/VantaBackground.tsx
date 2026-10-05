"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

type VantaEffect = { destroy: () => void };

/**
 * Atmospheric Vanta FOG background for the hero. FOG is a fullscreen-shader
 * effect (no legacy geometry), so it works with modern three. THREE is passed
 * explicitly rather than relying on a global.
 */
export default function VantaBackground() {
  const ref = useRef<HTMLDivElement | null>(null);
  const effectRef = useRef<VantaEffect | null>(null);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !ref.current) return;

    let cancelled = false;

    (async () => {
      const FOG = (await import("vanta/dist/vanta.fog.min")).default as (
        opts: Record<string, unknown>,
      ) => VantaEffect;
      if (cancelled || !ref.current) return;
      effectRef.current = FOG({
        el: ref.current,
        THREE,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.0,
        minWidth: 200.0,
        highlightColor: 0xe0a94a,
        midtoneColor: 0x3a2f18,
        lowlightColor: 0x1a1c2a,
        baseColor: 0x141519,
        blurFactor: 0.62,
        speed: 1.1,
        zoom: 0.75,
      });
    })();

    return () => {
      cancelled = true;
      effectRef.current?.destroy();
      effectRef.current = null;
    };
  }, []);

  return (
    <div
      ref={ref}
      aria-hidden
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 0,
        // fallback gradient before/without the effect
        background:
          "radial-gradient(1000px 600px at 70% 10%, oklch(0.3 0.06 85 / 0.35), transparent 60%), var(--bg)",
      }}
    />
  );
}
