"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CiteRenderer } from "@/lib/answerFormat";
import { citedNumbers } from "@/lib/askEvidence";
import { ABSTAIN, Answer } from "@/components/AskConsole";
import { AskBento, SourcePeek } from "./AskBento";
import { chartedNames, moveTypes } from "./Evidence";
import type { AskRun } from "./runState";

/**
 * One Ask run drawn as the bento of answer tiles, with ``[n]`` citations that open a
 * popover of their records. Shared by the /ask page and the home Ask tile; key it by
 * the question so hover and popover state reset with each new ask.
 */
export function AskResults({ run, scrollIntoView = false }: { run: AskRun; scrollIntoView?: boolean }) {
  const [hot, setHot] = useState<number | null>(null);
  // The record a clicked citation points to, shown in a popover by the citation.
  // ``jump`` is where the record is drawn in the results, unless that's the citation's own tile.
  const [peek, setPeek] = useState<{
    ns: number[];
    from: HTMLElement;
    x: number;
    y: number;
    above: boolean;
    jumps: (Element | null)[];
  } | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollIntoView) cardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [scrollIntoView]);

  const { answer, sources, views, status } = run;
  const cited = useMemo(() => citedNumbers(answer), [answer]);
  const streaming = status === "streaming";
  const abstained = status === "done" && ABSTAIN.test(answer) && cited.size === 0;
  // A ranking (or a move list) draws its own chart, so answer bullets that just
  // restate a charted Pokémon / move are folded into it rather than listed twice.
  // Here learners and type charts get their own tiles too, so bullets that only restate
  // one ("Ho-Oh — by TM", "Resists — Bug, Steel…") are dropped as well. Pokémon lists
  // keep theirs: look-alike bullets say why each one matches.
  const charted = useMemo(() => {
    const out = chartedNames(views);
    for (const v of views) {
      if (v.kind === "learners") v.rows.forEach((r) => out.add(r.name.toLowerCase()));
      if (v.kind === "type_chart") ["weak to", "resists", "immune to", "super-effective against", "hits hard"].forEach((l) => out.add(l));
    }
    return out;
  }, [views]);
  const moves = useMemo(() => moveTypes(views), [views]);

  /** Open (or toggle) the popover for these records, by the citation that was clicked. */
  const openPeek = (ns: number[], from: HTMLElement) => {
    const r = from.getBoundingClientRect();
    // Where each record is drawn in the results, unless that's the citation's own tile.
    const jumps = ns.map(
      (n) => [...(cardRef.current?.querySelectorAll(`[data-src="${n}"]`) ?? [])].find((el) => !el.contains(from)) ?? null,
    );
    // Placed on the page once, here: below the citation, or above it when the screen has no room.
    const above = window.innerHeight - r.bottom < 440 && r.top > window.innerHeight - r.bottom;
    const at = { x: r.left, y: (above ? r.top : r.bottom) + window.scrollY, above };
    setPeek((p) => (p?.from === from ? null : { ns, from, ...at, jumps }));
  };

  const cite: CiteRenderer = (n, key) => (
    <button
      key={key}
      type="button"
      className={`ax-cite ${hot === n ? "is-hot" : ""}`}
      onMouseEnter={() => setHot(n)}
      onMouseLeave={() => setHot(null)}
      onFocus={() => setHot(n)}
      onBlur={() => setHot(null)}
      onClick={(e) => openPeek([n], e.currentTarget)}
      aria-label={`Source ${n}`}
    >
      {n}
    </button>
  );

  /** A run of records ("2–9") as one citation; its popover lists them. */
  const citeRange = (a: number, b: number) => (
    <button
      type="button"
      className="ax-cite ax-cite--range"
      onClick={(e) => openPeek(Array.from({ length: b - a + 1 }, (_, i) => a + i), e.currentTarget)}
      aria-label={`Sources ${a} to ${b}`}
    >
      {a}–{b}
    </button>
  );

  return (
    <>
      <div className="ax-results" ref={cardRef}>
        <AskBento
          run={run}
          cited={cited}
          hot={hot}
          setHot={setHot}
          cite={(n) => cite(n, `c${n}`)}
          citeRange={citeRange}
          answer={
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
              maxItems={4}
            />
          }
        />
      </div>
      {peek && (
        <SourcePeek
          key={`${peek.ns.join(",")}-${peek.x}-${peek.y}`}
          sources={peek.ns.map((n) => sources.find((s) => s.n === n))}
          from={peek.from}
          x={peek.x}
          y={peek.y}
          above={peek.above}
          jumps={peek.jumps}
          onClose={() => setPeek(null)}
        />
      )}
    </>
  );
}
