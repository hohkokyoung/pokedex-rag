"use client";

import { useState } from "react";
import type { Planner, Usage } from "@/lib/api";
import type { Status, StepRun } from "./useAsk";

const TOOL_LABEL: Record<string, string> = {
  query_pokemon: "Query the Pokédex",
  get_pokemon: "Read the profile",
  semantic_search: "Search descriptions",
  similar_to: "Find look-alikes",
  user_profile: "Read your profile",
  type_matchup: "Check the type chart",
  coverage_vs_types: "Find coverage",
  learnset: "Check the learnset",
  move_info: "Look up the move",
  ability_info: "Look up the ability",
  item_info: "Look up the item",
  encounters: "Find where it lives",
  team_context: "Read your team",
  recommend_additions: "Draft candidates",
  propose_set_edit: "Propose a set",
  add_member: "Add to the team",
  duel: "Play out the duel",
  calc_context: "Read the calculator",
  damage_calc: "Run the damage calc",
  survive_threshold: "Find the bulk to survive",
  propose_build: "Draft a build",
};

const MARK: Record<string, string> = { done: "✓", empty: "∅", error: "!" };

/**
 * The retrieval plan, live: each step with its reason and state while the answer is
 * being worked out, then folded into one line ("3 steps · 1.2s") that reopens on click.
 */
export function PlanSteps({
  steps,
  planner,
  cached,
  status,
  elapsed,
  usage,
  answering,
  compact = false,
}: {
  steps: StepRun[];
  planner: Planner | null;
  cached: boolean;
  status: Status;
  elapsed: number | null;
  usage: Usage | null;
  answering: boolean;
  /** Tighter spacing for the team coach's thread. */
  compact?: boolean;
}) {
  const settled = status === "done" || status === "error";
  // Open while working, folded once the answer is in. A click overrides that only for
  // the current status (parents remount this per question via ``key``).
  const [override, setOverride] = useState<{ status: Status; open: boolean } | null>(null);
  const open = override?.status === status ? override.open : !settled;
  const setOpen = (fn: (o: boolean) => boolean) => setOverride({ status, open: fn(open) });

  const by = cached ? "Cached" : planner === "keyword" ? "Planned by keywords" : planner === "llm" ? "Planned by the LLM" : null;
  const calls = usage ? `${usage.llm_calls} LLM call${usage.llm_calls === 1 ? "" : "s"}` : null;
  const working = !settled && steps.length > 0 && steps.every((s) => s.state !== "running" && s.state !== "pending");

  if (!steps.length) {
    return (
      <div className={`ax-plan is-planning ${compact ? "is-compact" : ""}`} aria-live="polite">
        <span className="ax-plan__dot" /> {status === "error" ? "Couldn’t plan" : "Planning the lookups…"}
      </div>
    );
  }

  return (
    <div className={`ax-plan ${open ? "is-open" : ""} ${settled ? "is-settled" : ""} ${compact ? "is-compact" : ""}`}>
      <button type="button" className="ax-plan__sum" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className="ax-plan__dot" />
        <b>
          {steps.length} step{steps.length === 1 ? "" : "s"}
        </b>
        {by && <span className="ax-plan__by">{by}</span>}
        {settled && elapsed !== null && <span>{elapsed.toFixed(1)}s</span>}
        {settled && calls && <span>{calls}</span>}
        {working && <span>{answering ? "Writing the answer" : "Reading the evidence"}</span>}
        <span className="ax-plan__chev" aria-hidden>
          ▾
        </span>
      </button>
      {open && (
        <ol className="ax-plan__steps" aria-live="polite">
          {steps.map((s) => (
            <li key={s.id} className={`ax-plan__step is-${s.state}`}>
              <span className="ax-plan__mark" aria-label={s.state}>
                {MARK[s.state] ?? ""}
              </span>
              <span className="ax-plan__body">
                <span className="ax-plan__tool">
                  {TOOL_LABEL[s.tool] ?? s.tool}
                  {s.replan && <em> follow-up</em>}
                </span>
                <span className="ax-plan__why">{s.why}</span>
              </span>
              <span className="ax-plan__res">
                {s.state === "running" || s.state === "pending" ? "…" : s.summary}
                {s.ms > 0 && <small>{s.ms} ms</small>}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
