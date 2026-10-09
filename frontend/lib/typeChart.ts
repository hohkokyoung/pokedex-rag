/* The attacking-type effectiveness chart, served by the backend from the ingested data
   (GET /api/types/chart) and fetched at most once per page load. Shared by the detail
   page's Type Matchups card and the home Type Calculator; the helpers below only look
   multipliers up in it. */

import { useEffect, useState } from "react";
import { getTypeChart } from "@/lib/api";
import type { Matchups, TypeChart } from "@/lib/types";

let cached: TypeChart | null = null;
let pending: Promise<TypeChart> | null = null;

/** The chart, fetched once; a failed fetch is retried by the next caller. */
export function loadTypeChart(): Promise<TypeChart> {
  if (cached) return Promise.resolve(cached);
  pending ??= getTypeChart().then(
    (c) => (cached = c),
    (e) => {
      pending = null;
      throw e;
    },
  );
  return pending;
}

/** The chart, or null while it loads (render a skeleton, never guessed multipliers). */
export function useTypeChart(): TypeChart | null {
  const [chart, setChart] = useState<TypeChart | null>(cached);
  useEffect(() => {
    if (chart) return;
    let alive = true;
    loadTypeChart()
      .then((c) => alive && setChart(c))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [chart]);
  return chart;
}

/** Multiplier of one attacking type against one defending type. */
export const typeEff = (c: TypeChart, atk: string, def: string) => c.chart[atk]?.[def] ?? 1;

/** Combined multiplier of an attacking type against a (dual) typing. */
export const typingEff = (c: TypeChart, atk: string, defs: string[]) => defs.reduce((m, d) => m * typeEff(c, atk, d), 1);

/** Defensive buckets for a typing, in the same shape the API returns. */
export function defensiveMatchups(c: TypeChart, defs: string[]): Matchups {
  const at = (m: number) => c.order.filter((a) => typingEff(c, a, defs) === m);
  return { weak_4x: at(4), weak_2x: at(2), resist_half: at(0.5), resist_quarter: at(0.25), immune: at(0) };
}

/** Types that at least one of `types` hits super-effectively (same-type attacks). */
export const superEffectiveHits = (c: TypeChart, types: string[]) =>
  c.order.filter((d) => types.some((t) => typeEff(c, t, d) >= 2));
