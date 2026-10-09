/* Team rating — display helpers only. The rating and profile themselves are computed by
   the backend (services/team_rating.py, services/team_profile.py) and arrive on the
   opponent-free team analysis, so the /teams cards, the full report on /teams/{id} and
   any other client always show the same grades. */

import type { Grade, RatingArea, TeamAnalysis, TeamProfile, TeamRating, VsOpponent } from "@/lib/api";

export type { Grade };
export type Area = RatingArea;
export type Rating = TeamRating;
/** The backend's profile with its rating alongside, as the team UI reads it. */
export type Profile = TeamProfile & { rating: TeamRating };

/** The team's profile + rating from an opponent-free analysis; null for an empty team
 *  (or an analysis taken against an opponent, which carries no rating). */
export const profileOf = (a: TeamAnalysis | null | undefined): Profile | null =>
  a?.profile && a.rating ? { ...a.profile, rating: a.rating } : null;

export const gradeTone = (g: Grade) => (g === "A" || g === "B" ? "good" : g === "C" ? "fair" : "poor");

/** Each matchup scorecard factor in plain words, from your side. */
export function matchupFactors(vs: VsOpponent) {
  const wins = vs.cells.filter((c) => c.outcome === "win").length;
  const losses = vs.cells.filter((c) => c.outcome === "lose").length;
  const text: Record<string, [string, string, string]> = {
    h2h: [`Wins ${wins} of ${vs.cells.length} one-on-ones`, `Loses ${losses} of ${vs.cells.length} one-on-ones`, `One-on-ones split ${wins}–${losses}`],
    reach: ["Hits more of their team hard", "They hit more of yours hard", "Similar type reach"],
    damage: ["Deals more damage", "They deal more damage", "Similar damage"],
    speed: ["Faster", "They're faster", "Similar speed"],
  };
  return vs.scorecard.map((r) => ({
    key: r.key,
    edge: r.edge,
    weight: r.weight,
    label: text[r.key]?.[r.edge === "ours" ? 0 : r.edge === "theirs" ? 1 : 2] ?? r.label,
  }));
}

/** A matchup is only provisional while either side is short of six or they differ in size. */
export const isProvisional = (vs: VsOpponent) =>
  vs.our_members.length !== vs.their_members.length || vs.our_members.length < 6;
