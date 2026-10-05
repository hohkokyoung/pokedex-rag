"use client";

/* The matchup vs another team, written out: the verdict, their biggest threats
   (what they beat, how fast they are, your best answer) and a short plan. Every
   sentence is built from the engine's one-on-one results, which play out each
   side's set — moves, items, abilities and a setup turn. */

import { Fragment, type ReactNode } from "react";
import { assetUrl, type Team, type VsOpponent } from "@/lib/api";
import type { Rating } from "@/lib/teamEval";

type Cell = VsOpponent["cells"][number];

const ITEM_SPEED: Record<string, number> = { "Choice Scarf": 1.5, "Iron Ball": 0.5 };
const SPEED_SETUP: Record<string, number> = {
  "Dragon Dance": 1, "Quiver Dance": 1, "Shift Gear": 2, Agility: 2, "Rock Polish": 2, "Shell Smash": 2,
  "Tidy Up": 1, "Victory Dance": 1, Autotomize: 2,
};
const stage = (n: number) => (2 + n) / 2;
const list = (xs: string[]) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);
const N = ({ children }: { children: ReactNode }) => <b className="mx-n">{children}</b>;

function speedOf(team: Team, slot: number) {
  const m = team.members.find((x) => x.slot === slot);
  return m ? Math.round((m.final_stats.speed ?? 0) * (ITEM_SPEED[m.item?.name ?? ""] ?? 1)) : 0;
}
function boostedSpeed(team: Team, slot: number) {
  const m = team.members.find((x) => x.slot === slot);
  if (!m) return null;
  const base = speedOf(team, slot);
  const setup = m.moves.map((x) => x.name).find((n) => SPEED_SETUP[n]);
  if (setup) return { spe: Math.round(base * stage(SPEED_SETUP[setup])), how: setup };
  if (m.ability?.name === "Speed Boost") return { spe: Math.round(base * 1.5), how: "Speed Boost" };
  return null;
}

export function matchupHeadline(vs: VsOpponent, opponentName: string) {
  const v = vs.verdict;
  if (!v) return "";
  if (v.edge === "ours") return v.score >= 62 ? "You're favoured" : "You're slightly favoured";
  if (v.edge === "theirs") return `${opponentName} is ${v.score <= 38 ? "favoured" : "slightly favoured"}`;
  return "Evenly matched";
}
export function tally(vs: VsOpponent) {
  const you = vs.cells.filter((c) => c.outcome === "win").length;
  const them = vs.cells.filter((c) => c.outcome === "lose").length;
  return { you, them, close: vs.cells.length - you - them, n: vs.cells.length };
}

const Mini = ({ src, size = 30 }: { src: string; size?: number }) => (
  // eslint-disable-next-line @next/next/no-img-element
  <img src={assetUrl(src)} alt="" width={size} height={size} style={{ objectFit: "contain" }} />
);

/** The one-on-one results behind the Matchup card, per Pokémon: shared by the card
 *  and by the facts sent to the coach, so both say the same thing. */
export function computeMatchup(team: Team, opponent: Team, vs: VsOpponent) {
  const ours = vs.our_members;
  const theirs = vs.their_members;
  const oName = (slot: number) => ours.find((x) => x.slot === slot)?.name ?? "?";
  const tName = (slot: number) => theirs.find((x) => x.slot === slot)?.name ?? "?";

  const threats = theirs
    .map((x) => {
      const cs = vs.cells.filter((c) => c.their_slot === x.slot);
      const beats = cs.filter((c) => c.outcome === "lose");
      const answers = cs.filter((c) => c.outcome === "win").sort((a, b) => a.their_pct - b.their_pct);
      const setup = cs.find((c) => c.their_setup)?.their_setup ?? null;
      const move = [...beats].sort((a, b) => b.their_pct - a.their_pct)[0]?.their_move ?? null;
      const spe = speedOf(opponent, x.slot);
      const boost = boostedSpeed(opponent, x.slot);
      const outspeeds = ours.filter((o) => speedOf(team, o.slot) < spe).length;
      const outspeedsBoosted = boost ? ours.filter((o) => speedOf(team, o.slot) < boost.spe).length : 0;
      return { x, beats, answers, setup, move, spe, boost, outspeeds, outspeedsBoosted };
    })
    .sort((a, b) => b.beats.length - a.beats.length);

  const mine = ours
    .map((o) => {
      const cs = vs.cells.filter((c) => c.our_slot === o.slot);
      const wins = cs.filter((c) => c.outcome === "win");
      const best: Cell | undefined = [...wins].sort((a, b) => b.score - a.score)[0];
      return { o, wins: wins.length, n: cs.length, best };
    })
    .sort((a, b) => b.wins - a.wins);

  return { ours, theirs, oName, tName, threats, mine };
}

/** The page's report as plain text for the coach: both ratings with every area's
 *  verdict and fix, the matchup verdict, their top threats with your answers, and
 *  the plan — the same numbers the page shows. */
export function reportFacts(
  team: Team,
  rating: Rating | null,
  opponent?: { team: Team; rating: Rating | null } | null,
  vs?: VsOpponent | null,
): string {
  const lines: string[] = [];
  const rated = (name: string, r: Rating) => {
    lines.push(`${name}: overall ${r.overall}/100 (${r.grade})${r.capped ? `, scaled for a ${Math.round((r.ceiling * 6) / 100)}/6 roster` : ""}.`);
    for (const x of r.areas) lines.push(`- ${name} ${x.label} ${x.grade} (${x.score}): ${x.headline}.${x.fix ? ` Fix: ${x.fix}` : ""}`);
  };
  if (rating) rated(`Your team "${team.name}"`, rating);
  if (opponent?.rating) rated(`Opponent "${opponent.team.name}"`, opponent.rating);
  if (opponent && vs) {
    const t = tally(vs);
    lines.push(`Matchup verdict: ${matchupHeadline(vs, opponent.team.name)} — you win ${t.you} of ${t.n} one-on-ones, they win ${t.them}${t.close ? `, ${t.close} close` : ""}.`);
    const m = computeMatchup(team, opponent.team, vs);
    for (const th of m.threats.slice(0, 4)) {
      const a = th.answers[0];
      lines.push(
        `Threat: ${th.x.name} beats ${th.beats.length} of your ${m.ours.length}${th.move ? ` with ${th.move}` : ""}${th.setup ? ` after ${th.setup}` : ""}; ` +
          (a ? `your best answer is ${m.oName(a.our_slot)} (takes ${Math.round(a.their_pct)}%, KOs in ${a.our_hko} with ${a.our_move}).` : "nothing on your team beats it one-on-one."),
      );
    }
    const lead = m.mine[0];
    if (lead) lines.push(`Best lead: ${lead.o.name}, wins ${lead.wins} of ${lead.n} pairings.`);
    const idle = m.mine.filter((x) => x.wins === 0).map((x) => x.o.name);
    if (idle.length) lines.push(`Wins no pairing here: ${idle.join(", ")}.`);
  }
  return lines.join("\n");
}

export default function TeamMatchupText({ team, opponent, vs }: { team: Team; opponent: Team; vs: VsOpponent }) {
  const { ours, theirs, oName, tName, threats, mine } = computeMatchup(team, opponent, vs);
  const outrun = (n: number) => (n === 0 ? "is slower than all of yours" : n >= ours.length ? "outruns your whole team" : `outruns ${n} of your ${ours.length}`);
  const threatLine = (th: (typeof threats)[number]) => {
    const parts: ReactNode[] = [
      <><N>{th.x.name}</N> beats {th.beats.length} of your {ours.length}{th.move ? <> with {th.move}</> : null}{th.setup ? <> after a {th.setup}</> : null}.</>,
      th.boost && th.outspeeds < ours.length
        ? <> At {th.spe} Speed it {outrun(th.outspeeds)}; after {th.boost.how} it reaches {th.boost.spe} and {outrun(th.outspeedsBoosted)}.</>
        : <> At {th.spe} Speed it {outrun(th.outspeeds)}.</>,
    ];
    if (th.answers.length) {
      const a = th.answers[0];
      const more = th.answers.slice(1, 3).map((c) => oName(c.our_slot));
      parts.push(<> Your best answer is <N>{oName(a.our_slot)}</N> — it takes {Math.round(a.their_pct)}% and KOs in {a.our_hko} with {a.our_move}{more.length ? <>; {list(more)} {more.length > 1 ? "also win" : "also wins"}</> : null}.</>);
    } else {
      parts.push(<> <span className="mx-bad">Nothing on your team beats it one-on-one.</span></>);
    }
    return parts.map((p, i) => <Fragment key={i}>{p}</Fragment>);
  };

  const plan: ReactNode[] = [];
  const lead = mine[0];
  if (lead) plan.push(<>Lead with <N>{lead.o.name}</N>: it wins {lead.wins} of {lead.n} pairings{lead.best ? <>, best of all against {tName(lead.best.their_slot)} ({lead.best.our_move}, {lead.best.our_pct >= 100 ? "one hit" : `${Math.round(lead.best.our_pct)}% a hit`})</> : null}.</>);
  const top = threats[0];
  if (top?.beats.length) {
    plan.push(top.answers.length
      ? <>Save <N>{oName(top.answers[0].our_slot)}</N> for <N>{top.x.name}</N> — don&apos;t trade it away early.</>
      : <>You have no answer to <N>{top.x.name}</N>. Add a Pokémon that resists {top.move ?? "its main attack"} and hits it hard, or something faster.</>);
  }
  for (const sw of threats.filter((x) => x.setup && x !== top).slice(0, 1)) {
    plan.push(<>Pressure <N>{sw.x.name}</N> before it can {sw.setup} — {sw.answers.length ? <>{list(sw.answers.slice(0, 2).map((c) => oName(c.our_slot)))} can do it</> : <>nothing you have stops it once it&apos;s boosted</>}.</>);
  }
  const idle = mine.filter((m) => m.wins === 0);
  if (idle.length) plan.push(<><N>{list(idle.map((d) => d.o.name))}</N> {idle.length > 1 ? "don't" : "doesn't"} win any pairing here — {idle.length > 1 ? "they're" : "it's"} the first to swap for this matchup.</>);

  const cellOf = (o: number, t: number) => vs.cells.find((c) => c.our_slot === o && c.their_slot === t);

  const ourFast = [...ours].sort((a, b) => speedOf(team, b.slot) - speedOf(team, a.slot))[0];
  const theirFast = [...theirs].sort((a, b) => speedOf(opponent, b.slot) - speedOf(opponent, a.slot))[0];

  return (
    <div className="mx">
      <div className="mx-body">
        <h5>Their biggest threats <span className="mx-leg">your six underneath — <i className="w" /> beats it <i className="l" /> loses to it</span></h5>
        {threats.slice(0, 3).map((th) => (
          <div key={th.x.slot} className="mx-threat">
            <div className="mx-th-head">
              <Mini src={th.x.sprite_url} size={44} />
              <p>{threatLine(th)}</p>
            </div>
            <div className="mx-vs" role="group" aria-label={`Your Pokémon against ${th.x.name}`}>
              {ours.map((o) => {
                const c = cellOf(o.slot, th.x.slot);
                const res = c?.outcome === "win" ? "win" : c?.outcome === "lose" ? "lose" : "even";
                const how = c ? (res === "win" ? `${o.name} wins — ${c.our_move} ${Math.round(c.our_pct)}% a hit` : res === "lose" ? `${th.x.name} wins — ${c.their_move} ${Math.round(c.their_pct)}% a hit` : "too close to call") : "";
                return (
                  <span key={o.slot} className={res} title={`${o.name} vs ${th.x.name}: ${how}`}>
                    <Mini src={o.sprite_url} size={30} />
                  </span>
                );
              })}
            </div>
          </div>
        ))}
        {ourFast && theirFast && (
          <>
            <h5>Speed</h5>
            <p>
              Your fastest is <N>{ourFast.name}</N> at {speedOf(team, ourFast.slot)}; theirs is <N>{theirFast.name}</N> at {speedOf(opponent, theirFast.slot)}.
              {threats.filter((x) => x.boost).map((x) => <Fragment key={x.x.slot}> {x.x.name} reaches {x.boost!.spe} after {x.boost!.how}.</Fragment>)}
            </p>
          </>
        )}
        <h5>Your plan</h5>
        <ol>{plan.map((l, i) => <li key={i}>{l}</li>)}</ol>
      </div>
    </div>
  );
}
