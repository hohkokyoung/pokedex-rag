"use client";

/* The team coach. Each question is planned like Ask (see components/agent): the team is
   always in context, and the plan adds what the question needs — dex lookups, drafted
   candidates (Add / Replace), a proposed set for a member ("give Garchomp a faster set",
   shown was → now; nothing is saved until Apply, and Revert puts the old set back), a
   duel, or — only for an explicit "add X" — an add with Undo. Works on either team. */

import { useEffect, useRef, useState } from "react";
import { coachAskStream, type Team } from "@/lib/api";
import { Answer } from "@/components/AskConsole";
import { chartedNames, moveTypes } from "@/components/agent/Evidence";
import { PlanSteps } from "@/components/agent/PlanSteps";
import { ViewBlock, refIndex } from "@/components/agent/ViewBlock";
import {
  applyDelta,
  applyDone,
  applyError,
  applyPlan,
  applySources,
  applyStep,
  applyView,
  startRun,
  type AskRun,
} from "@/components/agent/runState";
import { CandidateCards } from "@/components/agent/views/Candidates";
import { DuelCard } from "@/components/agent/views/Duel";
import { MemberAddedStrip } from "@/components/agent/views/MemberAdded";
import { SetEditCard } from "@/components/agent/views/SetEdit";
import type { Linking } from "@/components/agent/views/shared";

/** Stream one coach question into its turn (outside the component: it reads the clock). */
function streamCoach(
  teamId: number,
  question: string,
  opponentId: number | null,
  patch: (fn: (t: AskRun) => AskRun) => void,
  onTeamUpdated: (team: Team) => void,
): AbortController {
  const ctrl = new AbortController();
  const t0 = performance.now();
  coachAskStream(teamId, question, opponentId, {
    signal: ctrl.signal,
    onPlan: (p) => patch((t) => applyPlan(t, p)),
    onStep: (e) => patch((t) => applyStep(t, e)),
    onView: (v) => patch((t) => applyView(t, v)),
    onTeamUpdated,
    onSources: (s) => patch((t) => applySources(t, s)),
    onDelta: (d) => patch((t) => applyDelta(t, d)),
    onDone: (d) => patch((t) => applyDone(t, d, (performance.now() - t0) / 1000)),
    onError: (reason) =>
      patch((t) =>
        applyError(t, reason === "assistant-not-configured" ? "The coach needs an LLM API key to answer." : "The coach couldn't answer. Try again."),
      ),
  });
  return ctrl;
}

export default function TeamCoach({
  team,
  opponent,
  disabled,
  onAddCandidate,
  onTeamUpdated,
  onOpponentUpdated,
}: {
  team: Team;
  opponent: Team | null;
  disabled: boolean;
  onAddCandidate: (pokemonId: number) => Promise<{ ok: boolean; msg: string; slot?: number }>;
  onTeamUpdated: (team: Team) => void;
  onOpponentUpdated: (team: Team) => void;
}) {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<AskRun[]>([]);
  const [openSources, setOpenSources] = useState<number | null>(null);
  const [hot, setHot] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const busy = turns.some((t) => t.status === "streaming");

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [turns.length]);
  useEffect(() => () => abortRef.current?.abort(), []);

  const patchTurn = (i: number, fn: (t: AskRun) => AskRun) =>
    setTurns((ts) => ts.map((t, j) => (j === i ? fn(t) : t)));

  const first = [...team.members].sort((a, b) => a.slot - b.slot)[0];
  const quick = [
    "What's my team's biggest weakness?",
    opponent ? `How do I beat ${opponent.name}?` : "Which type should I add for coverage?",
    first ? `Give ${first.name} its best set` : "Draft the rest of my team: I like sweepers, non-legendary",
    "Draft the rest of my team: I like sweepers, non-legendary",
  ].filter((q, i, xs) => xs.indexOf(q) === i).slice(0, 4);

  const ask = (raw: string) => {
    const q = raw.trim();
    if (!q || busy || disabled) return;
    setInput("");
    const idx = turns.length;
    setTurns((ts) => [...ts, startRun(q)]);
    abortRef.current?.abort();
    abortRef.current = streamCoach(team.id, q, opponent?.id ?? null, (fn) => patchTurn(idx, fn), onTeamUpdated);
  };

  return (
    <section className="panel co">
      <div className="co-h">
        <h3>Coach</h3>
        <p>
          Ask anything about {team.name}{opponent ? ` or ${opponent.name}` : ""}. It can also change a Pokémon&apos;s set —
          say “give Garchomp a faster set” — and nothing is saved until you press Apply.
        </p>
      </div>

      {turns.length > 0 && (
        <div className="co-thread" data-lenis-prevent>
          {turns.map((t, i) => {
            const index = refIndex(t.sources);
            const linkFor = (step: string): Linking => ({
              n: (ref) => (ref == null ? null : index.get(`${step}:${ref}`) ?? null),
              hot,
              cited: new Set<number>(),
              hover: (n) => (n === null ? {} : { onMouseEnter: () => setHot(n), onMouseLeave: () => setHot(null) }),
            });
            const edits = t.views.filter((v) => v.kind === "set_edit");
            return (
              <div key={i} className="co-turn">
                <p className="co-q">{t.question}</p>
                <PlanSteps
                  key={`${i}-${t.question}`}
                  compact
                  steps={t.steps}
                  planner={t.planner}
                  cached={t.cached}
                  status={t.status}
                  elapsed={t.elapsed}
                  usage={t.usage}
                  answering={t.answer.length > 0}
                />
                {t.answer || t.status === "streaming" ? (
                  <div className="co-a">
                    <Answer
                      text={t.answer}
                      streaming={t.status === "streaming"}
                      abstained={false}
                      sources={t.sources}
                      charted={chartedNames(t.views)}
                      moveTypes={moveTypes(t.views)}
                      hot={hot}
                      setHot={setHot}
                      cite={(n, key) => (
                        <button
                          key={key}
                          type="button"
                          className={`ax-cite ${hot === n ? "is-hot" : ""}`}
                          onMouseEnter={() => setHot(n)}
                          onMouseLeave={() => setHot(null)}
                          onClick={() => setOpenSources(i)}
                          title={t.sources.find((x) => x.n === n)?.snippet}
                        >
                          {n}
                        </button>
                      )}
                    />
                  </div>
                ) : null}
                {t.status === "error" && <p className="co-err">{t.error}</p>}

                {edits.length > 1 && <span className="co-props-h">Suggested changes: apply the ones you want</span>}
                {t.views.map((v, j) => {
                  switch (v.kind) {
                    case "set_edit":
                      return (
                        <div key={j} className="co-props">
                          <SetEditCard view={v} onUpdated={v.side === "ours" ? onTeamUpdated : onOpponentUpdated} />
                        </div>
                      );
                    case "candidates":
                      return <CandidateCards key={j} view={v} team={team} onAdd={onAddCandidate} onTeamUpdated={onTeamUpdated} />;
                    case "member_added":
                      return <MemberAddedStrip key={j} view={v} onTeamUpdated={onTeamUpdated} />;
                    case "duel":
                      return <DuelCard key={j} view={v} />;
                    default:
                      return (
                        <div key={j} className="co-view">
                          <ViewBlock view={v} link={linkFor(v.step)} />
                        </div>
                      );
                  }
                })}

                {t.sources.length > 0 && (
                  <div className="co-src">
                    <button onClick={() => setOpenSources(openSources === i ? null : i)}>
                      {openSources === i ? "Hide" : "Show"} {t.sources.length} sources
                    </button>
                    {openSources === i && (
                      <ol>
                        {t.sources.map((s) => <li key={s.n}><b>{s.pokemon_name ?? s.chunk_type}</b> — {s.snippet}</li>)}
                      </ol>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          <div ref={endRef} />
        </div>
      )}

      <div className="co-quick">
        {quick.map((q) => <button key={q} onClick={() => ask(q)} disabled={disabled || busy}>{q}</button>)}
      </div>
      <form className="co-in" onSubmit={(e) => { e.preventDefault(); ask(input); }}>
        <input
          aria-label="Message the team coach"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
          placeholder={disabled ? "Add a Pokémon first…" : "Ask the coach, or tell it what to change…"}
        />
        <button type="submit" disabled={disabled || busy || !input.trim()}>{busy ? "…" : "Ask"}</button>
      </form>
    </section>
  );
}
