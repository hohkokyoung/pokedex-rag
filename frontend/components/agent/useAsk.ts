"use client";

import { useEffect, useRef, useState } from "react";
import {
  askQuestionStream,
  type AskSource,
  type AskView,
  type Planner,
  type PlanStep,
  type StepState,
  type Usage,
} from "@/lib/api";

export type Status = "idle" | "streaming" | "done" | "error";

export type StepRun = PlanStep & { state: StepState; summary: string; ms: number; replan: boolean };

/** Everything one asked question streamed back. */
export type AskRun = {
  question: string;
  status: Status;
  planner: Planner | null;
  cached: boolean;
  steps: StepRun[];
  views: AskView[];
  sources: AskSource[];
  answer: string;
  usage: Usage | null;
  elapsed: number | null;
  error: string;
};

const EMPTY: AskRun = {
  question: "",
  status: "idle",
  planner: null,
  cached: false,
  steps: [],
  views: [],
  sources: [],
  answer: "",
  usage: null,
  elapsed: null,
  error: "",
};

function failure(reason: string): string {
  return reason === "assistant-not-configured"
    ? "The assistant isn’t configured. Add ANTHROPIC_API_KEY or GROQ_API_KEY to .env and restart the backend."
    : "Couldn’t reach the assistant. Check the backend is running, then ask again.";
}

/**
 * Stream an Ask answer: the plan, each step's progress, typed views, sources and the
 * answer text. ``cacheRuns`` keeps finished answers per question for the session
 * (the home tile uses it so re-asking a starter question costs nothing).
 */
export function useAsk({ cacheRuns = false }: { cacheRuns?: boolean } = {}) {
  const [run, setRun] = useState<AskRun>(EMPTY);
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
    setRun({ ...EMPTY, question: q, status: "streaming" });

    askQuestionStream(q, {
      signal: controller.signal,
      onPlan: (p) =>
        patch((r) => ({
          ...r,
          planner: p.replan ? r.planner : p.planner,
          cached: p.replan ? r.cached : p.cached,
          steps: [
            ...r.steps,
            ...p.steps.map((s) => ({
              ...s,
              state: (s.error ? "error" : "pending") as StepState,
              summary: s.error ?? "",
              ms: 0,
              replan: p.replan,
            })),
          ],
        })),
      onStep: (e) =>
        patch((r) => ({
          ...r,
          steps: r.steps.map((s) => (s.id === e.id ? { ...s, state: e.state, summary: e.summary || s.summary, ms: e.ms } : s)),
        })),
      onView: (v) => patch((r) => ({ ...r, views: [...r.views, v] })),
      onSources: (sources) => patch((r) => ({ ...r, sources })),
      onDelta: (text) => patch((r) => ({ ...r, answer: r.answer + text })),
      onDone: (d) =>
        patch((r) => {
          const next = { ...r, status: "done" as Status, usage: d?.usage ?? null, elapsed: (performance.now() - t0) / 1000 };
          if (cacheRuns) done.current[q] = next;
          return next;
        }),
      onError: (reason) => patch((r) => ({ ...r, status: "error", error: failure(reason) })),
    });
  }

  return { run, ask };
}
