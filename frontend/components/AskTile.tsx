"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getAskStatus } from "@/lib/api";
import { citedNumbers, followUps } from "@/lib/askEvidence";
import { ABSTAIN, FollowUps, SUGGESTIONS } from "@/components/AskConsole";
import { AskResults } from "@/components/agent/AskResults";
import { useAsk } from "@/components/agent/useAsk";

/**
 * The home Ask tile: the /ask console in miniature — composer and starter chips, with
 * answers drawn as the same bento of tiles as /ask (``AskResults``). Answers can be a paid
 * LLM call, so nothing runs until the user asks, and finished answers are cached per
 * question for the session.
 */
export default function AskTile() {
  const [provider, setProvider] = useState<string | null>(null);
  const [q, setQ] = useState("");
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
    start(trimmed);
  }

  const { answer, sources, status } = run;
  const cited = useMemo(() => citedNumbers(answer), [answer]);
  const streaming = status === "streaming";
  const abstained = status === "done" && ABSTAIN.test(answer) && cited.size === 0;

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
          <AskResults key={run.question} run={run} />
          {status === "done" && !abstained && (
            <FollowUps items={followUps(sources.filter((s) => cited.has(s.n)))} onAsk={ask} />
          )}
        </div>
      )}
      <Link className="go" href={run.question ? `/ask?q=${encodeURIComponent(run.question)}` : "/ask"}>Open the assistant →</Link>
    </section>
  );
}
