"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { assetUrl, failureKind, getAskStatus, type AskSource, type FailureKind, thumb } from "@/lib/api";
import ServerNote from "@/components/ServerNote";
import { parseBlocks, renderInline, type CiteRenderer } from "@/lib/answerFormat";
import { citedNumbers, followUps } from "@/lib/askEvidence";
import { typeVars } from "@/lib/pokeTypes";
import ProfilePanel from "@/components/ProfilePanel";
import { AskResults } from "@/components/agent/AskResults";
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
  /** The status check itself failed: the server is unreachable, not "keyless". */
  const [statusFailed, setStatusFailed] = useState<Exclude<FailureKind, "not-found"> | null>(null);
  const [statusAttempt, setStatusAttempt] = useState(0);
  const [provider, setProvider] = useState("none");
  const initialQ = params.get("q");
  const [q, setQ] = useState(initialQ ?? "");
  const { run, ask: start } = useAsk();

  useEffect(() => {
    getAskStatus()
      .then((s) => {
        setStatusFailed(null);
        setEnabled(s.enabled);
        setProvider(s.provider);
      })
      .catch((e) => {
        setEnabled(null);
        setStatusFailed(failureKind(e) === "offline" ? "offline" : "server");
      });
  }, [statusAttempt]);

  // /ask?q=… (e.g. from the home Ask tile) runs that question straight away.
  useEffect(() => {
    if (initialQ) submit(initialQ);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQ]);

  function submit(question: string) {
    if (!question.trim() || run.status === "streaming") return;
    start(question);
  }

  function ask(question: string) {
    setQ(question);
    submit(question);
  }

  const { answer, sources, status } = run;
  const cited = useMemo(() => citedNumbers(answer), [answer]);
  const streaming = status === "streaming";
  const abstained = status === "done" && ABSTAIN.test(answer) && cited.size === 0;
  // Once answered, the search card's strip offers follow-ups instead of the examples.
  const next = status === "done" && !abstained ? followUps(sources.filter((s) => cited.has(s.n))) : [];

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
          <svg className="ax-composer__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ask anything about Pokémon…"
            aria-label="Ask a question"
            autoFocus
          />
          <button type="submit" className="btn btn-primary ax-composer__go" disabled={streaming || !q.trim()}>
            {streaming ? "Asking…" : "Ask"}
          </button>
        </div>
        <ProfilePanel
          lead={
            next.length > 0 ? (
              <>
                <span className="ax-foot__lbl">Ask next</span>
                {next.map((f) => (
                  <button key={f} type="button" onClick={() => ask(f)}>
                    {f}
                  </button>
                ))}
              </>
            ) : (
              SUGGESTIONS.map(([kind, label, question]) => (
                <button
                  key={kind}
                  type="button"
                  onClick={() => ask(question)}
                  disabled={streaming}
                  title={question}
                  className={run.question === question ? "on" : ""}
                >
                  {label}
                </button>
              ))
            )
          }
          meta={
            statusFailed ? <>Server offline</> : enabled === null ? null : enabled ? (
              <>Answers by {provider === "anthropic" ? "Claude" : provider === "groq" ? "Groq" : provider}</>
            ) : (
              <>Data-only mode</>
            )
          }
        />
      </form>

      {statusFailed && (
        <ServerNote compact kind={statusFailed} what="the assistant" onRetry={() => setStatusAttempt((n) => n + 1)} />
      )}

      {enabled === false && (
        <p className="ax-note">
          No AI key set, so lookups are planned by keyword and descriptive answers show the matching
          Pokédex records verbatim. Add <code>ANTHROPIC_API_KEY</code> or a free <code>GROQ_API_KEY</code>{" "}
          to <code>.env</code> and restart the backend for planned lookups and written answers.
        </p>
      )}

      {status !== "idle" && <AskResults key={run.question} run={run} scrollIntoView />}
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
  maxItems,
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
  /** Show this many bullets per list, the rest behind "Show N more" (once streamed). */
  maxItems?: number;
}) {
  const [allItems, setAllItems] = useState(false);
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
  // A leading "*Note: I couldn't filter by …*" (constraints the tools can't apply) is a notice,
  // not the verdict — the verdict is the paragraph after it.
  const gap = blocks[0]?.kind === "p" && /^\*Note: [\s\S]+\*$/.test(blocks[0].text.trim()) ? 0 : -1;
  const verdictAt = gap === 0 ? 1 : 0;

  return (
    <div className={`ax-answer ${abstained ? "is-abstain" : ""}`} aria-live="polite">
      {blocks.map((b, i) => {
        if (b.kind === "p") {
          return (
            <p key={i} className={i === gap ? "ax-gap" : i === verdictAt ? "ax-verdict" : "ax-p"} role={i === gap ? "note" : undefined}>
              {i === gap ? b.text.trim().replace(/^\*|\*$/g, "") : renderInline(b.text, cite, `p${i}-`)}
              {i === last && cursor}
            </p>
          );
        }
        const capped = !streaming && !allItems && maxItems !== undefined && b.items.length > maxItems + 1;
        return (
          <ul key={i} className="ax-list">
            {(capped ? b.items.slice(0, maxItems) : b.items).map((li, j) => {
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
                    <img loading="lazy" decoding="async" src={thumb(sprite(src), 160)} alt="" className="ax-li__art" />
                  ) : mv ? (
                    <span className="ax-li__mv" style={typeVars(mv) as React.CSSProperties} />
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
            {capped && (
              <li className="ax-li ax-li--more">
                <button type="button" onClick={() => setAllItems(true)}>
                  Show {b.items.length - maxItems} more
                </button>
              </li>
            )}
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
