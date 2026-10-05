"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { assetUrl, getAskStatus, type AskSource } from "@/lib/api";
import { parseBlocks, renderInline, type CiteRenderer } from "@/lib/answerFormat";
import { citedNumbers, followUps } from "@/lib/askEvidence";
import { typeColor } from "@/lib/pokeTypes";
import ProfilePanel from "@/components/ProfilePanel";
import { EvidencePanel, chartedNames, moveTypes } from "@/components/agent/Evidence";
import { PlanSteps } from "@/components/agent/PlanSteps";
import { useAsk } from "@/components/agent/useAsk";

/** Starter questions, labelled by what they exercise. */
export const SUGGESTIONS: [kind: string, label: string, question: string][] = [
  ["Rank", "Highest Attack", "Which Pokémon has the highest Attack?"],
  ["Lore", "Fire-types near volcanoes", "Which Fire-types live near volcanoes?"],
  ["Multi", "Will-O-Wisp + Fire", "Which Fire types learn Will-O-Wisp, and what is Fire weak to?"],
  ["Matchup", "Special attacker vs Dark", "Which special attacker has coverage against Dark?"],
  ["For you", "Pokémon I'd like", "Which Pokémon would I probably like?"],
];

export const ABSTAIN = /don.t have (that|anything)/i;

const sprite = (s: AskSource) => {
  const id = s.pokemon_id ?? s.dex_number;
  return id ? assetUrl(`/sprites/official-artwork/${id}.png`) : "";
};

export default function AskConsole() {
  const params = useSearchParams();
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [provider, setProvider] = useState("none");
  const initialQ = params.get("q");
  const [q, setQ] = useState(initialQ ?? "");
  const [hot, setHot] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(false);
  const cardRef = useRef<HTMLDivElement | null>(null);
  const { run, ask: start } = useAsk();

  useEffect(() => {
    getAskStatus()
      .then((s) => {
        setEnabled(s.enabled);
        setProvider(s.provider);
      })
      .catch(() => setEnabled(false));
  }, []);

  // /ask?q=… (e.g. from the home Ask tile) runs that question straight away.
  useEffect(() => {
    if (initialQ) submit(initialQ);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQ]);

  function submit(question: string) {
    if (!question.trim() || run.status === "streaming") return;
    setHot(null);
    setShowAll(false);
    start(question);
    requestAnimationFrame(() => cardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }

  function ask(question: string) {
    setQ(question);
    submit(question);
  }

  const { answer, sources, views, status } = run;
  const cited = useMemo(() => citedNumbers(answer), [answer]);
  const streaming = status === "streaming";
  const abstained = status === "done" && ABSTAIN.test(answer) && cited.size === 0;
  // A ranking (or a move list) draws its own chart, so answer bullets that just
  // restate a charted Pokémon / move are folded into it rather than listed twice.
  const charted = useMemo(() => chartedNames(views), [views]);
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
      onClick={() =>
        cardRef.current
          ?.querySelector(`[data-src="${n}"]`)
          ?.scrollIntoView({ behavior: "smooth", block: "nearest" })
      }
      aria-label={`Source ${n}`}
    >
      {n}
    </button>
  );

  return (
    <div>
      <form
        className="ax-composer"
        onSubmit={(e) => {
          e.preventDefault();
          submit(q);
        }}
      >
        <div className="ax-composer__row">
          <span className="ax-composer__prompt" aria-hidden>›</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ask anything about Pokémon…"
            aria-label="Ask a question"
            autoFocus
          />
          <button type="submit" className="btn btn-primary ax-composer__go" disabled={streaming || !q.trim()}>
            {streaming ? "Asking…" : "Ask →"}
          </button>
        </div>
        <ProfilePanel
          meta={
            enabled === null ? null : enabled ? (
              <>Answers by {provider === "anthropic" ? "Claude" : provider === "groq" ? "Groq" : provider}</>
            ) : (
              <>Data-only mode</>
            )
          }
        />
      </form>

      {enabled === false && (
        <p className="ax-note">
          No AI key set, so lookups are planned by keyword and descriptive answers show the matching
          Pokédex records verbatim. Add <code>ANTHROPIC_API_KEY</code> or a free <code>GROQ_API_KEY</code>{" "}
          to <code>.env</code> and restart the backend for planned lookups and written answers.
        </p>
      )}

      <div className="ax-sugg">
        {SUGGESTIONS.map(([kind, label, question]) => (
          <button key={kind} type="button" onClick={() => ask(question)} disabled={streaming} title={question}>
            <span className="ax-sugg__k">{kind}</span>
            {label}
          </button>
        ))}
      </div>

      {status !== "idle" && (
        <div className="ax-card" ref={cardRef}>
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
              />
              {status === "done" && !abstained && (
                <FollowUps items={followUps(sources.filter((s) => cited.has(s.n)))} onAsk={ask} />
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Answer: first paragraph is the verdict; bullets get the cited Pokémon's sprite ── */
export function Answer({
  text,
  streaming,
  abstained,
  sources,
  charted,
  moveTypes,
  cite,
  hot,
  setHot,
}: {
  text: string;
  streaming: boolean;
  abstained: boolean;
  sources: AskSource[];
  /** Names a view already charts; bullets that only restate them are dropped. */
  charted: Set<string>;
  /** Move name → type, for the coloured dot on bullets that name a move. */
  moveTypes?: Map<string, string>;
  cite: CiteRenderer;
  hot: number | null;
  setHot: (n: number | null) => void;
}) {
  if (!text) {
    return (
      <div className="ax-answer" aria-busy>
        <div className="ax-skel" style={{ width: "86%" }} />
        <div className="ax-skel" style={{ width: "58%" }} />
      </div>
    );
  }

  // "**Palkia (#484):**" / "**Mewtwo #150**" → "palkia" / "mewtwo"
  const labelOf = (li: string) =>
    li
      .match(/^\*\*([^*]+)\*\*/)?.[1]
      .replace(/[:\s]+$/, "")
      .replace(/\s*\(?#\d+\)?$/, "")
      .toLowerCase();
  const blocks = parseBlocks(text)
    .map((b) =>
      b.kind === "ul" && charted.size
        ? { ...b, items: b.items.filter((li) => !charted.has(labelOf(li) ?? "") && !(streaming && li.startsWith("**") && !labelOf(li))) }
        : b,
    )
    .filter((b) => b.kind === "p" || b.items.length > 0);
  const byName = new Map(sources.filter((s) => s.pokemon_name).map((s) => [s.pokemon_name!.toLowerCase(), s]));
  const cursor = streaming ? <span className="ax-cursor" aria-hidden /> : null;
  const last = blocks.length - 1;

  return (
    <div className={`ax-answer ${abstained ? "is-abstain" : ""}`} aria-live="polite">
      {blocks.map((b, i) => {
        if (b.kind === "p") {
          return (
            <p key={i} className={i === 0 ? "ax-verdict" : "ax-p"}>
              {renderInline(b.text, cite, `p${i}-`)}
              {i === last && cursor}
            </p>
          );
        }
        return (
          <ul key={i} className="ax-list">
            {b.items.map((li, j) => {
              const label = labelOf(li);
              const src = label ? byName.get(label) : undefined;
              const n = Number(li.match(/[[【](\d+)[\]】]/)?.[1] ?? 0);
              const mv = label ? moveTypes?.get(label) : undefined;
              return (
                <li
                  key={j}
                  className={`ax-li ${src ? "has-art" : ""} ${n && hot === n ? "is-hot" : ""}`}
                  style={{ animationDelay: `${j * 60}ms` }}
                  onMouseEnter={() => n && setHot(n)}
                  onMouseLeave={() => setHot(null)}
                >
                  {src && sprite(src) ? (
                    <img src={sprite(src)} alt="" className="ax-li__art" />
                  ) : mv ? (
                    <span className="ax-li__mv" style={{ "--tc": typeColor(mv) } as React.CSSProperties} />
                  ) : (
                    <span className="ax-li__dot" />
                  )}
                  <span>
                    {renderInline(li, cite, `u${i}-${j}-`)}
                    {i === last && j === b.items.length - 1 && cursor}
                  </span>
                </li>
              );
            })}
          </ul>
        );
      })}
      {abstained && (
        <p className="ax-abstain">
          Nothing in the retrieved records answers this, so there’s no answer rather than a guess.
          Try naming a Pokémon, type or stat.
        </p>
      )}
    </div>
  );
}

export function FollowUps({ items, onAsk }: { items: string[]; onAsk: (q: string) => void }) {
  if (!items.length) return null;
  return (
    <div className="ax-follow">
      <span className="ax-follow__lbl">Ask next</span>
      {items.map((f) => (
        <button key={f} type="button" onClick={() => onAsk(f)}>
          {f}
        </button>
      ))}
    </div>
  );
}
