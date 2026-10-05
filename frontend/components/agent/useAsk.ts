"use client";

import { useEffect, useRef, useState } from "react";
import { askQuestionStream } from "@/lib/api";
import {
  EMPTY_RUN,
  applyDelta,
  applyDone,
  applyError,
  applyPlan,
  applySources,
  applyStep,
  applyView,
  failureMessage,
  startRun,
  type AskRun,
} from "./runState";

export type { AskRun, Status, StepRun } from "./runState";

/**
 * Stream an Ask answer: the plan, each step's progress, typed views, sources and the
 * answer text. ``cacheRuns`` keeps finished answers per question for the session
 * (the home tile uses it so re-asking a starter question costs nothing).
 */
export function useAsk({ cacheRuns = false }: { cacheRuns?: boolean } = {}) {
  const [run, setRun] = useState<AskRun>(EMPTY_RUN);
  const abortRef = useRef<AbortController | null>(null);
  const done = useRef<Record<string, AskRun>>({});

  useEffect(() => () => abortRef.current?.abort(), []);

  function ask(question: string) {
    const q = question.trim();
    if (!q || run.status === "streaming") return;
    const hit = cacheRuns ? done.current[q] : undefined;
    if (hit) {
      setRun(hit);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const t0 = performance.now();
    const patch = (fn: (r: AskRun) => AskRun) => setRun((r) => (r.question === q ? fn(r) : r));
    setRun(startRun(q));

    askQuestionStream(q, {
      signal: controller.signal,
      onPlan: (p) => patch((r) => applyPlan(r, p)),
      onStep: (e) => patch((r) => applyStep(r, e)),
      onView: (v) => patch((r) => applyView(r, v)),
      onSources: (sources) => patch((r) => applySources(r, sources)),
      onDelta: (text) => patch((r) => applyDelta(r, text)),
      onDone: (d) =>
        patch((r) => {
          const next = applyDone(r, d, (performance.now() - t0) / 1000);
          if (cacheRuns) done.current[q] = next;
          return next;
        }),
      onError: (reason) => patch((r) => applyError(r, failureMessage(reason))),
    });
  }

  return { run, ask };
}
