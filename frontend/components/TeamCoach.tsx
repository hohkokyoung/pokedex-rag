"use client";

/* The team coach. Questions stream a grounded answer (with sources and, when you ask
   it to draft, Pokémon you can add). Asking it to change a Pokémon — "give Garchomp
   a faster set", "what item should Salamence hold?" — gets a proposed set shown as a
   was → now diff; nothing is saved until Apply, and Revert puts the old set back,
   like the home calculator's coach. Works on either team on the page. */

import { useEffect, useRef, useState } from "react";
import {
  applySlotBuild,
  clearSlot,
  assetUrl,
  coachAskStream,
  setSlot,
  suggestBuild,
  type AskSource,
  type BuildSuggestion,
  type Candidate,
  type CoachEdit,
  type Team,
} from "@/lib/api";
import { Chip } from "@/components/TeamCardParts";
import { Answer } from "@/components/AskConsole";

type Member = Team["members"][number];
type Side = "ours" | "theirs";
type Proposal = {
  side: Side;
  slot: number;
  name: string;
  before: Member;
  build: BuildSuggestion;
  /** Only these fields are applied (the rest of the slot is left as is). */
  fields: { moves?: string[]; ability?: string | null; nature?: string | null; item?: string | null; evs?: Record<string, number> };
  applied: boolean;
  busy?: boolean;
  err?: string;
};
type Turn = {
  q: string;
  text: string;
  done: boolean;
  err?: string;
  sources: AskSource[];
  candidates: Candidate[];
  proposals: Proposal[];
};

const EV_SHORT: Record<string, string> = { hp: "HP", atk: "Atk", def: "Def", spa: "SpA", spd: "SpD", spe: "Spe" };
const EV_FROM_TEAM: Record<string, string> = { hp: "hp", attack: "atk", defense: "def", sp_attack: "spa", sp_defense: "spd", speed: "spe" };
const evText = (evs: Record<string, number> | undefined | null) =>
  Object.entries(evs ?? {}).filter(([, v]) => v).map(([k, v]) => `${v} ${EV_SHORT[k] ?? k}`).join(" / ") || "none";
const teamEvs = (m: Member) =>
  Object.fromEntries(Object.entries(m.ev_spread ?? {}).map(([k, v]) => [EV_FROM_TEAM[k] ?? k, v])) as BuildSuggestion["evs"];

// A request to change a set: an edit verb or a set field, about a named Pokémon.
const EDIT = /\b(change|make|give|set|swap|switch|replace|teach|equip|put|tweak|improve|optimi[sz]e|fix|rebuild|build|use|hold|run)\b|\b(best|better|new) (set|build|moveset)\b|\bmoveset\b|\bevs?\b|\bitem\b|\bnature\b|\bability\b/i;
const THEIRS = /\b(their|opponent'?s?|rival'?s?|enemy|foe'?s?)\b/i;

function findMember(text: string, team: Team, opponent: Team | null): { side: Side; m: Member } | null {
  const t = text.toLowerCase();
  const scan = (tm: Team | null) =>
    tm ? [...tm.members].sort((a, b) => b.name.length - a.name.length).find((m) => t.includes(m.name.toLowerCase())) : undefined;
  const preferTheirs = THEIRS.test(text);
  const ours = scan(team);
  const theirs = scan(opponent);
  if (preferTheirs && theirs) return { side: "theirs", m: theirs };
  if (ours) return { side: "ours", m: ours };
  if (theirs) return { side: "theirs", m: theirs };
  return null;
}

const NO_CHART = new Set<string>();

/** A proposal from a partial edit: the member's current set with the edited fields swapped in. */
function fromEdit(e: CoachEdit, before: Member): Proposal {
  const build: BuildSuggestion = {
    pokemon: before.name,
    moves: e.moves ?? before.moves.map((x) => x.name),
    ability: e.ability ?? before.ability?.name ?? null,
    nature: e.nature ?? before.nature?.name ?? null,
    item: e.item ?? before.item?.name ?? null,
    evs: (e.evs as BuildSuggestion["evs"]) ?? teamEvs(before),
    why: "",
  };
  const fields = Object.fromEntries(
    (["moves", "ability", "nature", "item", "evs"] as const).filter((k) => e[k] != null).map((k) => [k, e[k]]),
  ) as Proposal["fields"];
  return { side: e.side, slot: e.slot, name: e.name, before, build, fields, applied: false };
}

function ProposalCard({ p, onApply, onRevert, onDismiss }: { p: Proposal; onApply: () => void; onRevert: () => void; onDismiss: () => void }) {
  const b = p.before;
  const rows: [string, string, string][] = [
    ["Ability", b.ability?.name ?? "—", p.build.ability ?? b.ability?.name ?? "—"],
    ["Nature", b.nature?.name ?? "—", p.build.nature ?? b.nature?.name ?? "—"],
    ["Item", b.item?.name ?? "No item", p.build.item && p.build.item !== "None" ? p.build.item : "No item"],
    ["EVs", evText(teamEvs(b)), evText(p.build.evs)],
  ];
  const wasMoves = b.moves.map((m) => m.name);
  return (
    <div className={`co-prop${p.applied ? " applied" : ""}`}>
      <div className="co-prop-h">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={assetUrl(b.sprite_url)} alt="" width={36} height={36} />
        <span className="t">{p.applied ? "Applied to " : "Proposed set for "}<b>{p.name}</b>{p.side === "theirs" && <em> (opponent)</em>}</span>
        <span className="acts">
          {p.applied ? (
            <button className="rev" onClick={onRevert} disabled={p.busy}>{p.busy ? "…" : "Revert"}</button>
          ) : (
            <>
              <button className="ok" onClick={onApply} disabled={p.busy}>{p.busy ? "Saving…" : "Apply"}</button>
              <button className="x" onClick={onDismiss} aria-label="Dismiss">Dismiss</button>
            </>
          )}
        </span>
      </div>
      <div className="co-diff">
        {rows.map(([k, was, now]) => (
          <div key={k} className={was === now ? "same" : "chg"}>
            <span className="k">{k}</span>
            {was === now ? <span>{now}</span> : <span><s>{was}</s> → <b>{now}</b></span>}
          </div>
        ))}
        <div className="moves">
          <span className="k">Moves</span>
          <span className="mv">
            {p.build.moves.map((m) => <i key={m} className={wasMoves.includes(m) ? "" : "new"}>{m}</i>)}
            {wasMoves.filter((m) => !p.build.moves.includes(m)).map((m) => <i key={m} className="gone">{m}</i>)}
          </span>
        </div>
      </div>
      {p.err && <p className="co-err">{p.err}</p>}
    </div>
  );
}

export default function TeamCoach({
  team,
  opponent,
  disabled,
  onAddCandidate,
  onTeamUpdated,
  onOpponentUpdated,
  report,
}: {
  report?: string;
  team: Team;
  opponent: Team | null;
  disabled: boolean;
  onAddCandidate: (pokemonId: number) => Promise<{ ok: boolean; msg: string; slot?: number }>;
  onTeamUpdated: (team: Team) => void;
  onOpponentUpdated: (team: Team) => void;
}) {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  // Per candidate: what happened when added, and the slot it went into (for Revert).
  const [added, setAdded] = useState<Record<number, { msg: string; slot?: number; busy?: boolean }>>({});
  const [openSources, setOpenSources] = useState<number | null>(null);
  const [hot, setHot] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [turns.length]);

  const patchTurn = (i: number, patch: Partial<Turn> | ((t: Turn) => Partial<Turn>)) =>
    setTurns((ts) => ts.map((t, j) => (j === i ? { ...t, ...(typeof patch === "function" ? patch(t) : patch) } : t)));

  const first = [...team.members].sort((a, b) => a.slot - b.slot)[0];
  const quick = [
    "What's my team's biggest weakness?",
    opponent ? `How do I beat ${opponent.name}?` : "Which type should I add for coverage?",
    first ? `Give ${first.name} its best set` : "Draft the rest of my team — I like sweepers, non-legendary",
    "Draft the rest of my team — I like sweepers, non-legendary",
  ].filter((q, i, xs) => xs.indexOf(q) === i).slice(0, 4);

  const ask = async (raw: string) => {
    const q = raw.trim();
    if (!q || busy || disabled) return;
    setInput("");
    setBusy(true);
    const idx = turns.length;
    setTurns((ts) => [...ts, { q, text: "", done: false, sources: [], candidates: [], proposals: [] }]);

    const target = EDIT.test(q) ? findMember(q, team, opponent) : null;
    if (target) {
      // A set change: ask the build coach to revise this Pokémon's current set per the request.
      const m = target.m;
      const current: BuildSuggestion | undefined = m.moves.length
        ? { pokemon: m.name, moves: m.moves.map((x) => x.name), ability: m.ability?.name ?? null, nature: m.nature?.name ?? null, item: m.item?.name ?? null, evs: teamEvs(m), why: "" }
        : undefined;
      try {
        const build = await suggestBuild(m.pokemon_id, m.form_id ?? null, { current, request: q, history: [] });
        const fields = { moves: build.moves, ability: build.ability, nature: build.nature, item: build.item ?? "none", evs: build.evs };
        patchTurn(idx, { text: build.why, done: true, proposals: [{ side: target.side, slot: m.slot, name: m.name, before: m, build, fields, applied: false }] });
      } catch (e) {
        patchTurn(idx, { done: true, err: e instanceof Error ? e.message : "The coach couldn't suggest a set." });
      }
      setBusy(false);
      return;
    }

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    await coachAskStream(team.id, q, opponent?.id ?? null, {
      signal: ctrl.signal,
      onSources: (s) => patchTurn(idx, { sources: s }),
      onEdits: (edits) =>
        patchTurn(idx, {
          proposals: edits.flatMap((e) => {
            const before = (e.side === "ours" ? team : opponent)?.members.find((m) => m.slot === e.slot);
            return before ? [fromEdit(e, before)] : [];
          }),
        }),
      onCandidates: (c) => patchTurn(idx, { candidates: c }),
      onTeamUpdated: (t) => onTeamUpdated(t),
      onDelta: (d) => patchTurn(idx, (t) => ({ text: t.text + d })),
      onDone: () => {
        patchTurn(idx, { done: true });
        setBusy(false);
      },
      onError: (reason) => {
        patchTurn(idx, {
          done: true,
          err: reason === "assistant-not-configured" ? "The coach needs an LLM API key to answer." : "The coach couldn't answer — try again.",
        });
        setBusy(false);
      },
    }, report);
  };

  const patchProposal = (i: number, j: number, patch: Partial<Proposal>) =>
    patchTurn(i, (t) => ({ proposals: t.proposals.map((p, k) => (k === j ? { ...p, ...patch } : p)) }));

  const apply = async (i: number, j: number) => {
    const p = turns[i]?.proposals[j];
    if (!p) return;
    patchProposal(i, j, { busy: true, err: undefined });
    const teamId = p.side === "ours" ? team.id : opponent!.id;
    try {
      const t = await applySlotBuild(teamId, p.slot, p.fields);
      (p.side === "ours" ? onTeamUpdated : onOpponentUpdated)(t);
      patchProposal(i, j, { busy: false, applied: true });
    } catch (e) {
      patchProposal(i, j, { busy: false, err: e instanceof Error ? e.message : "Couldn't apply the set." });
    }
  };
  const revert = async (i: number, j: number) => {
    const p = turns[i]?.proposals[j];
    if (!p) return;
    patchProposal(i, j, { busy: true, err: undefined });
    const b = p.before;
    const teamId = p.side === "ours" ? team.id : opponent!.id;
    try {
      const t = await setSlot(teamId, p.slot, {
        pokemon_id: b.pokemon_id, form_id: b.form_id ?? null, ability_id: b.ability?.id ?? null,
        nature_id: b.nature?.id ?? null, item_id: b.item?.id ?? null, ev_spread: b.ev_spread ?? null,
        iv_spread: b.iv_spread ?? null, move_ids: b.moves.length ? b.moves.map((x) => x.move_id) : null,
      });
      (p.side === "ours" ? onTeamUpdated : onOpponentUpdated)(t);
      patchProposal(i, j, { busy: false, applied: false });
    } catch (e) {
      patchProposal(i, j, { busy: false, err: e instanceof Error ? e.message : "Couldn't revert." });
    }
  };

  // Team full: a candidate replaces a member you pick — confirm first, Revert after.
  const [replace, setReplace] = useState<Record<number, { slot?: number; busy?: boolean; done?: Member; err?: string }>>({});
  const patchReplace = (id: number, patch: { slot?: number; busy?: boolean; done?: Member; err?: string } | null) =>
    setReplace((r) => {
      const n = { ...r };
      if (patch === null) delete n[id];
      else n[id] = { ...r[id], ...patch };
      return n;
    });
  const confirmReplace = async (c: Candidate) => {
    const slot = replace[c.pokemon_id]?.slot;
    const before = team.members.find((m) => m.slot === slot);
    if (!slot || !before) return;
    patchReplace(c.pokemon_id, { busy: true, err: undefined });
    try {
      onTeamUpdated(await setSlot(team.id, slot, { pokemon_id: c.pokemon_id }));
      patchReplace(c.pokemon_id, { busy: false, done: before });
    } catch (e) {
      patchReplace(c.pokemon_id, { busy: false, err: e instanceof Error ? e.message : "Couldn't replace." });
    }
  };
  const revertReplace = async (c: Candidate) => {
    const b = replace[c.pokemon_id]?.done;
    if (!b) return;
    patchReplace(c.pokemon_id, { busy: true });
    try {
      onTeamUpdated(await setSlot(team.id, b.slot, {
        pokemon_id: b.pokemon_id, form_id: b.form_id ?? null, ability_id: b.ability?.id ?? null,
        nature_id: b.nature?.id ?? null, item_id: b.item?.id ?? null, ev_spread: b.ev_spread ?? null,
        iv_spread: b.iv_spread ?? null, move_ids: b.moves.length ? b.moves.map((x) => x.move_id) : null,
      }));
      patchReplace(c.pokemon_id, null);
    } catch {
      patchReplace(c.pokemon_id, { busy: false });
    }
  };
  const teamFull = team.members.length >= 6;

  const add = async (c: Candidate) => {
    if (added[c.pokemon_id]) return;
    const res = await onAddCandidate(c.pokemon_id);
    setAdded((prev) => ({ ...prev, [c.pokemon_id]: { msg: res.msg, slot: res.ok ? res.slot : undefined } }));
  };
  const undoAdd = async (c: Candidate) => {
    const a = added[c.pokemon_id];
    if (!a?.slot) return;
    setAdded((prev) => ({ ...prev, [c.pokemon_id]: { ...a, busy: true } }));
    try {
      onTeamUpdated(await clearSlot(team.id, a.slot));
      setAdded((prev) => {
        const n = { ...prev };
        delete n[c.pokemon_id];
        return n;
      });
    } catch {
      setAdded((prev) => ({ ...prev, [c.pokemon_id]: { ...a, busy: false } }));
    }
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
          {turns.map((t, i) => (
            <div key={i} className="co-turn">
              <p className="co-q">{t.q}</p>
              {t.text || !t.done ? (
                <div className="co-a">
                  <Answer
                    text={t.text}
                    streaming={!t.done}
                    abstained={false}
                    sources={t.sources}
                    charted={NO_CHART}
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
              {t.err && <p className="co-err">{t.err}</p>}
              {t.proposals.length > 0 && (
                <div className="co-props">
                  {t.proposals.length > 1 && <span className="co-props-h">Suggested changes — apply the ones you want</span>}
                  {t.proposals.map((p, j) => (
                    <ProposalCard
                      key={`${p.side}${p.slot}`}
                      p={p}
                      onApply={() => apply(i, j)}
                      onRevert={() => revert(i, j)}
                      onDismiss={() => patchTurn(i, (tt) => ({ proposals: tt.proposals.filter((_, k) => k !== j) }))}
                    />
                  ))}
                </div>
              )}
              {t.candidates.length > 0 && (
                <div className="co-cands">
                  {t.candidates.map((c) => (
                    <div key={c.pokemon_id} className="co-cand">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={assetUrl(c.sprite_url)} alt="" width={40} height={40} />
                      <div>
                        <b>{c.name}</b>
                        <span className="tp">{c.types.map((ty) => <Chip key={ty} t={ty} />)}<em>{c.role}</em></span>
                        <small>{c.reason}</small>
                      </div>
                      {(() => {
                        const r = replace[c.pokemon_id];
                        if (r?.done) {
                          return (
                            <span className="co-repl">
                              <span className="st">Replaced {r.done.name}</span>
                              <button onClick={() => revertReplace(c)} disabled={r.busy}>{r.busy ? "…" : "Revert"}</button>
                            </span>
                          );
                        }
                        const ad = added[c.pokemon_id];
                        if (ad) {
                          return ad.slot ? (
                            <span className="co-repl">
                              <span className="st">{ad.msg}</span>
                              <button onClick={() => undoAdd(c)} disabled={ad.busy}>{ad.busy ? "…" : "Revert"}</button>
                            </span>
                          ) : <span className="st">{ad.msg}</span>;
                        }
                        if (!teamFull) return <button onClick={() => add(c)}>Add</button>;
                        if (r?.slot) {
                          const out = team.members.find((m) => m.slot === r.slot);
                          return (
                            <span className="co-repl">
                              <span className="q">Replace <b>{out?.name}</b>?</span>
                              <button className="ok" onClick={() => confirmReplace(c)} disabled={r.busy}>{r.busy ? "Saving…" : "Confirm"}</button>
                              <button onClick={() => patchReplace(c.pokemon_id, null)}>Cancel</button>
                            </span>
                          );
                        }
                        return r ? (
                          <span className="co-repl pick" role="group" aria-label={`Pick who ${c.name} replaces`}>
                            <span className="q">Replace who?</span>
                            {[...team.members].sort((a, b) => a.slot - b.slot).map((m) => (
                              <button key={m.slot} className="mon" title={m.name} onClick={() => patchReplace(c.pokemon_id, { slot: m.slot })}>
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img src={assetUrl(m.sprite_url)} alt={m.name} width={28} height={28} />
                              </button>
                            ))}
                            <button onClick={() => patchReplace(c.pokemon_id, null)}>Cancel</button>
                          </span>
                        ) : (
                          <button onClick={() => patchReplace(c.pokemon_id, {})}>Replace…</button>
                        );
                      })()}
                      {replace[c.pokemon_id]?.err && <span className="co-err">{replace[c.pokemon_id]?.err}</span>}
                    </div>
                  ))}
                </div>
              )}
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
          ))}
          <div ref={endRef} />
        </div>
      )}

      <div className="co-quick">
        {quick.map((q) => <button key={q} onClick={() => ask(q)} disabled={disabled || busy}>{q}</button>)}
      </div>
      <form className="co-in" onSubmit={(e) => { e.preventDefault(); ask(input); }}>
        <input
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
