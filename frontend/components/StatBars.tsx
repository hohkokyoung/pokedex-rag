"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { STAT_LABELS, STAT_MAX } from "@/lib/pokeTypes";
import type { Stats } from "@/lib/types";

/** `color` fills the bars; `textColor` (the type's text-safe shade) colours numbers. */
export default function StatBars({ stats, color, textColor = color }: { stats: Stats; color: string; textColor?: string }) {
  const root = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const bars = el.querySelectorAll<HTMLElement>(".stat-fill");
    const nums = el.querySelectorAll<HTMLElement>(".stat-num");
    // Resting state (CSS scaleX(--pct) + real numbers in JSX) is already correct;
    // under reduced motion we leave it untouched.
    if (reduced) return;

    // Animate from 0 up to the resting value. immediateRender:false means the
    // bars only jump to 0 once the tween actually ticks, so they never get
    // stuck empty if frames are paused.
    const tweens: gsap.core.Tween[] = [];
    tweens.push(
      gsap.fromTo(
        bars,
        { scaleX: 0 },
        {
          scaleX: (i) => Number((bars[i] as HTMLElement).dataset.pct),
          duration: 0.9,
          ease: "power3.out",
          stagger: 0.06,
          immediateRender: false,
        },
      ),
    );
    nums.forEach((n) => {
      const target = Number(n.dataset.val);
      const obj = { v: 0 };
      tweens.push(
        gsap.to(obj, {
          v: target,
          duration: 0.9,
          ease: "power3.out",
          onUpdate: () => (n.textContent = String(Math.round(obj.v))),
        }),
      );
    });
    return () => {
      tweens.forEach((t) => t.kill());
    };
  }, [stats]);

  // Flag the highest and lowest stat (ties all flagged); skip when every stat is equal.
  const vals = STAT_LABELS.map((s) => stats[s.key]);
  const hi = Math.max(...vals);
  const lo = Math.min(...vals);
  const flat = hi === lo;

  return (
    <div ref={root} className="stat-bars" style={{ display: "flex", flexDirection: "column", gap: 13 }}>
      {STAT_LABELS.map((s) => {
        const val = stats[s.key];
        const pct = Math.min(1, val / STAT_MAX);
        const best = !flat && val === hi;
        const worst = !flat && val === lo;
        const fill = worst
          ? "linear-gradient(90deg, color-mix(in oklch, var(--muted) 35%, transparent), color-mix(in oklch, var(--muted) 70%, transparent))"
          : best
            ? color
            : `linear-gradient(90deg, color-mix(in oklch, ${color} 55%, transparent), ${color})`;
        return (
          <div
            key={s.key}
            className={best ? "stat-row stat-row--best" : worst ? "stat-row stat-row--worst" : "stat-row"}
            title={best ? "Highest stat" : worst ? "Lowest stat" : undefined}
            style={{ display: "grid", gridTemplateColumns: "44px 1fr 40px", gap: 12, alignItems: "center" }}
          >
            <span
              className="font-mono"
              style={{
                fontSize: 11.5,
                letterSpacing: "0.04em",
                color: best ? textColor : "var(--muted)",
                fontWeight: best ? 600 : undefined,
              }}
            >
              {s.short}
            </span>
            <div className="stat-track">
              <div
                className="stat-fill"
                data-pct={pct}
                style={
                  {
                    "--pct": pct,
                    background: fill,
                    boxShadow: best ? `0 0 10px color-mix(in oklch, ${color} 45%, transparent)` : undefined,
                  } as React.CSSProperties
                }
              />
            </div>
            <span
              className="font-mono stat-num"
              data-val={val}
              style={{
                fontSize: 13,
                textAlign: "right",
                color: best ? textColor : worst ? "var(--muted)" : undefined,
                fontWeight: best ? 600 : undefined,
              }}
            >
              {val}
            </span>
          </div>
        );
      })}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: 6,
          paddingTop: 12,
          borderTop: "1px solid var(--line-soft)",
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--muted)" }}>
          Base stat total
        </span>
        <span className="font-display" style={{ fontSize: 20, color: textColor }}>
          {stats.total}
        </span>
      </div>
    </div>
  );
}
