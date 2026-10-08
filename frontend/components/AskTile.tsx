"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getAskStatus } from "@/lib/api";
import type { CiteRenderer } from "@/lib/answerFormat";
import { citedNumbers, followUps } from "@/lib/askEvidence";
import { ABSTAIN, Answer, FollowUps, SUGGESTIONS } from "@/components/AskConsole";
import { EvidencePanel, chartedNames, moveTypes } from "@/components/agent/Evidence";
import { PlanSteps } from "@/components/agent/PlanSteps";
import { useAsk } from "@/components/agent/useAsk";

/**
 * The home Ask tile: the /ask console in miniature (composer, starter chips, the
 * live plan, verdict-first answer, the first evidence view). Answers can be a paid
 * LLM call, so nothing runs until the user asks, and finished answers are cached per
 * question for the session.
 */
export default function AskTile() {
  const [provider, setProvider] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [hot, setHot] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(false);
  const { run, ask: start } = useAsk({ cacheRuns: true });

  useEffect(() => {
    getAskStatus()
      .then((s) => setProvider(s.enabled ? s.provider : "none"))
      .catch(() => setProvider("offline")); // unreachable ≠ "no key": don't claim data-only
  }, []);

  function ask(question: string) {
    const trimmed = question.trim();
    if (!trimmed || run.status === "streaming") return;
    setQ(trimmed);
    setHot(null);
    setShowAll(false);
    start(trimmed);
  }

  const { answer, sources, views, status } = run;
  const cited = useMemo(() => citedNumbers(answer), [answer]);
  const streaming = status === "streaming";
  const abstained = status === "done" && ABSTAIN.test(answer) && cited.size === 0;
  const charted = useMemo(() => chartedNames(views.slice(0, 1)), [views]);
  const moves = useMemo(() => moveTypes(views), [views]);

  const cite: CiteRenderer = (n, key) => (
    <button
      key={key}
      type="button"
      className={`ax-cite ${hot === n ? "is-hot" : ""}`}
      onMouseEnter={() => setHot(n)}
      onMouseLeave={() => setHot(null)}
      onFocus={() => setHot(n)}
      onBlur={() => setHot(null)}
      aria-label={`Source ${n}`}
    >
      {n}
    </button>
  );

  const by = provider === "anthropic" ? "Claude" : provider === "groq" ? "Groq" : provider === "none" ? "data-only" : provider;

  return (
    <section className="card lc-ask">
      <div className="lbl">
        <h2 className="lbl-t">Ask pokérag</h2>
        {provider === "offline" ? <span className="mono">server offline</span> : by && <span className="mono">answers by {by}</span>}
      </div>
      <form
        className="ax-composer"
        onSubmit={(e) => {
          e.preventDefault();
          ask(q);
        }}
      >
        <div className="ax-composer__row">
          <span className="ax-composer__prompt" aria-hidden>›</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ask anything about Pokémon…"
            aria-label="Ask a question"
          />
          <button type="submit" className="btn btn-primary ax-composer__go" disabled={streaming || !q.trim()}>
            {streaming ? "Asking…" : "Ask →"}
          </button>
        </div>
      </form>
      <div className="ax-sugg">
        {SUGGESTIONS.map(([kind, label, question]) => (
          <button key={kind} type="button" onClick={() => ask(question)} disabled={streaming} title={question}>
            <span className="ax-sugg__k">{kind}</span>
            {label}
          </button>
        ))}
      </div>

      {status !== "idle" && (
        <div className="lc-ask-out">
          <div className="ax-q">{run.question}</div>
          <PlanSteps
            key={run.question}
            steps={run.steps}
            planner={run.planner}
            cached={run.cached}
            status={status}
            elapsed={run.elapsed}
            usage={run.usage}
            answering={answer.length > 0}
          />
          {status === "error" ? (
            <p className="ax-error">{run.error}</p>
          ) : (
            <>
              <Answer
                text={answer}
                streaming={streaming}
                abstained={abstained}
                sources={sources}
                charted={charted}
                moveTypes={moves}
                cite={cite}
                hot={hot}
                setHot={setHot}
              />
              <EvidencePanel
                steps={run.steps}
                views={views}
                sources={sources}
                cited={cited}
                done={status === "done"}
                hot={hot}
                setHot={setHot}
                showAll={showAll}
                setShowAll={setShowAll}
                maxViews={1}
              />
              {status === "done" && !abstained && (
                <FollowUps items={followUps(sources.filter((s) => cited.has(s.n)))} onAsk={ask} />
              )}
            </>
          )}
        </div>
      )}
      <Link className="go" href={run.question ? `/ask?q=${encodeURIComponent(run.question)}` : "/ask"}>Open the assistant →</Link>
    </section>
  );
}
