import type { AskSource, AskView, DoneEvent, PlanEvent, Planner, PlanStep, StepEvent, StepState, Usage } from "@/lib/api";

export type Status = "idle" | "streaming" | "done" | "error";

export type StepRun = PlanStep & { state: StepState; summary: string; ms: number; replan: boolean };

/** Everything one asked question streamed back (Ask or the team coach). */
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

export const EMPTY_RUN: AskRun = {
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

export const startRun = (question: string): AskRun => ({ ...EMPTY_RUN, question, status: "streaming" });

/** Pure reducers for each stream event, shared by Ask and the coach. */
export const applyPlan = (r: AskRun, p: PlanEvent): AskRun => ({
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
});

export const applyStep = (r: AskRun, e: StepEvent): AskRun => ({
  ...r,
  steps: r.steps.map((s) => (s.id === e.id ? { ...s, state: e.state, summary: e.summary || s.summary, ms: e.ms } : s)),
});

export const applyView = (r: AskRun, v: AskView): AskRun => ({ ...r, views: [...r.views, v] });
export const applySources = (r: AskRun, sources: AskSource[]): AskRun => ({ ...r, sources });
export const applyDelta = (r: AskRun, text: string): AskRun => ({ ...r, answer: r.answer + text });
export const applyDone = (r: AskRun, d: DoneEvent | undefined, elapsed: number): AskRun => ({
  ...r,
  status: "done",
  usage: d?.usage ?? null,
  elapsed,
});
export const applyError = (r: AskRun, error: string): AskRun => ({ ...r, status: "error", error });

export function failureMessage(reason: string): string {
  return reason === "assistant-not-configured"
    ? "The assistant isn’t configured. Add ANTHROPIC_API_KEY or GROQ_API_KEY to .env and restart the backend."
    : "Couldn’t reach the assistant. Check the backend is running, then ask again.";
}
