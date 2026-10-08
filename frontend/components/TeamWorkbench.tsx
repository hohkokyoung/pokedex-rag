"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  failureKind,
  type FailureKind,
  getTeam,
  getTeamAnalysis,
  listNatures,
  listTeams,
  clearSlot,
  setSlot,
  updateTeam,
  type NatureInfo,
  type Team,
  type TeamAnalysis,
  type TeamSummary,
} from "@/lib/api";
import SlotEditor from "@/components/SlotEditor";
import ServerNote from "@/components/ServerNote";
import TeamCoach from "@/components/TeamCoach";
import TeamReport from "@/components/TeamReport";
import TeamRoster from "@/components/TeamRoster";
import Dropdown from "@/components/Dropdown";
import { reportFacts } from "@/components/TeamMatchupText";
import { rateTeam } from "@/lib/teamEval";
import { discardDraft, keepDraft, promoteDraft, replaceMissingDraft } from "@/lib/draftTeams";

const SLOTS = [1, 2, 3, 4, 5, 6];

export default function TeamWorkbench({
  teamId,
  initialOpponentId = null,
  isDraft = false,
}: {
  teamId: number;
  initialOpponentId?: number | null;
  /** Just made by "New team": discarded if left before any Pokémon is added. */
  isDraft?: boolean;
}) {
  const router = useRouter();
  const [team, setTeam] = useState<Team | null>(null);
  const filled = useRef(false);
  const [natures, setNatures] = useState<NatureInfo[]>([]);
  const [opponents, setOpponents] = useState<TeamSummary[]>([]);
  const [opponentId, setOpponentId] = useState<number | null>(initialOpponentId);
  // Which slot editor is open: on this team, or on the opponent picked to compare.
  const [editing, setEditing] = useState<{ side: "ours" | "theirs"; slot: number } | null>(null);
  const [oppTeam, setOppTeam] = useState<Team | null>(null);
  const [oppRated, setOppRated] = useState<TeamAnalysis | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loadFailed, setLoadFailed] = useState<Exclude<FailureKind, "not-found"> | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [renaming, setRenaming] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
  const [analysis, setAnalysis] = useState<TeamAnalysis | null>(null);
  // The rating always uses the opponent-free analysis (the engine fills empty move
  // slots differently per opponent), so it matches the grade on the /teams list.
  const [rated, setRated] = useState<TeamAnalysis | null>(null);


  // A draft becomes a real team once it has a Pokémon; leaving before that discards it.
  useEffect(() => {
    if (team && team.members.length > 0 && !filled.current) {
      filled.current = true;
      if (isDraft) promoteDraft(teamId);
    }
  }, [team, isDraft, teamId]);
  useEffect(() => {
    if (!isDraft) return;
    keepDraft(teamId); // cancels a Strict Mode double-mount discard
    return () => {
      if (!filled.current) discardDraft(teamId);
    };
  }, [isDraft, teamId]);

  // Any other saved team can be the other side.
  const reloadOpponents = useCallback(async () => {
    const { teams } = await listTeams();
    setOpponents(teams.filter((t) => t.id !== teamId));
  }, [teamId]);

  useEffect(() => {
    (async () => {
      try {
        const [t, n] = await Promise.all([getTeam(teamId), listNatures()]);
        setTeam(t);
        setNameDraft(t.name);
        setNatures(n);
        void reloadOpponents();
      } catch (e) {
        const kind = failureKind(e);
        if (kind !== "not-found") {
          // Server down or erroring: say so (and retry), never treat it as a missing team.
          setLoadFailed(kind);
          return;
        }
        if (isDraft) {
          // This draft was discarded (left without adding anything) — start a new one.
          replaceMissingDraft(teamId)
            .then((id) => router.replace(`/teams/${id}?new=1`))
            .catch(() => setNotFound(true));
          return;
        }
        setNotFound(true);
      }
    })();
  }, [teamId, reloadOpponents, isDraft, router, attempt]);

  // One analysis fetch feeds both the versus board and the analysis panel;
  // re-run whenever the team changes (slot edits, adds) or the opponent does.
  useEffect(() => {
    if (!team) return;
    let alive = true;
    const vsId = opponentId;
    getTeamAnalysis(team.id, vsId)
      .then((a) => {
        if (!alive) return;
        setAnalysis(a);
        if (!vsId) setRated(a);
      })
      .catch(() => alive && setAnalysis(null));
    if (vsId)
      getTeamAnalysis(team.id)
        .then((a) => alive && setRated(a))
        .catch(() => alive && setRated(null));
    return () => {
      alive = false;
    };
  }, [team, opponentId, oppTeam]);

  // Keep ?vs= in step with the picked opponent so a reload shows the same comparison.
  useEffect(() => {
    const url = new URL(window.location.href);
    if (opponentId) url.searchParams.set("vs", String(opponentId));
    else url.searchParams.delete("vs");
    window.history.replaceState(window.history.state, "", url);
  }, [opponentId]);

  // The opponent's own team + opponent-free analysis, for its roster and rating.
  useEffect(() => {
    if (!opponentId) return;
    let alive = true;
    getTeam(opponentId)
      .then((t) => alive && setOppTeam(t))
      .catch(() => alive && setOppTeam(null));
    return () => {
      alive = false;
    };
  }, [opponentId]);
  useEffect(() => {
    if (!oppTeam) return;
    let alive = true;
    getTeamAnalysis(oppTeam.id)
      .then((a) => alive && setOppRated(a))
      .catch(() => alive && setOppRated(null));
    return () => {
      alive = false;
    };
  }, [oppTeam]);

  // The editor stays open across saves/removals; just refresh the team.
  const onTeamEdited = (updated: Team) => {
    setTeam(updated);
    void reloadOpponents();
  };

  // Add a recommended candidate to the next empty slot (owns slot bookkeeping).
  const addPokemon = async (pokemonId: number): Promise<{ ok: boolean; msg: string; slot?: number }> => {
    if (!team) return { ok: false, msg: "no team" };
    if (team.members.some((m) => m.pokemon_id === pokemonId)) {
      return { ok: false, msg: "already on team" };
    }
    const used = new Set(team.members.map((m) => m.slot));
    const slot = SLOTS.find((s) => !used.has(s));
    if (!slot) return { ok: false, msg: "team full" };
    const updated = await setSlot(team.id, slot, { pokemon_id: pokemonId });
    setTeam(updated);
    return { ok: true, msg: `Added to slot ${slot}`, slot };
  };

  const saveName = async () => {
    if (!team) return;
    const trimmed = nameDraft.trim();
    setRenaming(false);
    if (!trimmed || trimmed === team.name) return;
    const updated = await updateTeam(team.id, { name: trimmed });
    setTeam((prev) => (prev ? { ...prev, name: updated.name } : prev));
  };

  if (loadFailed && !team) {
    return (
      <main className="shell" style={{ paddingTop: 140 }}>
        <ServerNote kind={loadFailed} what="this team" onRetry={() => { setLoadFailed(null); setAttempt((n) => n + 1); }} />
      </main>
    );
  }

  if (notFound) {
    return (
      <main className="shell" style={{ paddingTop: 140 }}>
        <p style={{ color: "var(--muted)" }}>
          Team not found. <Link href="/teams" style={{ color: "var(--accent-text)" }}>Back to Team Lab →</Link>
        </p>
      </main>
    );
  }

  if (!team) {
    return (
      <main className="shell" style={{ paddingTop: 140 }}>
        <p className="font-mono" style={{ color: "var(--muted)", fontSize: 12 }}>
          Loading team…
        </p>
      </main>
    );
  }

  const pickable = opponents.filter((o) => o.size > 0).map((o) => ({ value: o.id, label: o.name, hint: `${o.size}/6` }));
  // Any saved team can face any other: this team is always "your side".
  const versus = analysis?.vs_opponent?.opponent_id === opponentId ? analysis.vs_opponent : null;

  return (
    <main className="shell" style={{ paddingTop: 104, paddingBottom: 120 }}>
      <title>{`pokérag — ${team.name}`}</title>
      <Link href="/teams" className="tw-back" style={{ fontSize: 14, fontWeight: 500, color: "var(--muted)" }}>
        ← Team Lab
      </Link>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
        {renaming ? (
          <input
            autoFocus
            aria-label="Team name"
            value={nameDraft}
            onChange={(e) => setNameDraft(e.target.value)}
            onBlur={saveName}
            onKeyDown={(e) => e.key === "Enter" && saveName()}
            className="font-display"
            style={{
              fontSize: "clamp(1.8rem,4vw,2.8rem)",
              background: "transparent",
              border: "none",
              borderBottom: "1px solid var(--line)",
              color: "var(--ink)",
              outline: "none",
            }}
          />
        ) : (
          <h1
            className="font-display"
            style={{ fontSize: "clamp(1.8rem,4vw,2.8rem)", cursor: "text" }}
            onClick={() => setRenaming(true)}
            title="Click to rename"
          >
            {team.name}
          </h1>
        )}
      </div>

      {/* Pokémon: this team, and the team it's tested against */}
      {/* Pokémon: this team full width; once an opponent is picked, both side by side */}
      <div className={`ro-benches${opponentId ? "" : " solo"}`}>
        <section className="ro-col">
          <div className="ro-colh">
            <h2 className="ro-colt">Your team</h2>
            <span>{team.members.length}/6</span>
            {!opponentId && (
              <span className="ro-pick-r">
                {pickable.length ? (
                  <Dropdown<number>
                    label="Compare with another team"
                    allLabel="Compare with…"
                    align="right"
                    options={pickable}
                    value={[]}
                    onChange={(next) => setOpponentId(next[0] ?? null)}
                  />
                ) : (
                  <Link href="/teams" className="ro-start">Start another team to compare</Link>
                )}
              </span>
            )}
          </div>
          <TeamRoster
            team={team}
            analysis={rated}
            onEdit={(slot) => setEditing({ side: "ours", slot })}
            onRemove={async (slot) => setTeam(await clearSlot(team.id, slot))}
          />
        </section>
        {opponentId && (
          <section className="ro-col">
            <div className="ro-colh">
              <h2 className="ro-colt">Opponent</h2>
              <Dropdown<number>
                label="Team to compare against"
                options={pickable}
                value={[opponentId]}
                // Only the id changes here; the loaders below fetch the new team, and a
                // stale team/analysis is ignored by the id checks until it arrives.
                onChange={(next) => setOpponentId(next[0] && next[0] !== opponentId ? next[0] : null)}
              />
              <button className="ro-clear" onClick={() => setOpponentId(null)} title="Stop comparing">
                Clear
              </button>
            </div>
            {oppTeam?.id === opponentId ? (
              <TeamRoster
                team={oppTeam}
                analysis={oppRated?.team_id === oppTeam.id ? oppRated : null}
                onEdit={(slot) => setEditing({ side: "theirs", slot })}
                onRemove={async (slot) => setOppTeam(await clearSlot(oppTeam.id, slot))}
              />
            ) : (
              <span className="lab-skel" style={{ display: "block", height: 260 }} />
            )}
          </section>
        )}
      </div>

      <div style={{ marginTop: 14 }}>
        <TeamCoach
          team={team}
          opponent={opponentId && oppTeam?.id === opponentId ? oppTeam : null}
          disabled={team.members.length === 0}
          onAddCandidate={addPokemon}
          onTeamUpdated={(t) => setTeam(t)}
          onOpponentUpdated={(t) => setOppTeam(t)}
          report={reportFacts(
            team,
            rated && team.members.length ? rateTeam(team.members.length, rated) : null,
            opponentId && oppTeam?.id === opponentId
              ? { team: oppTeam, rating: oppRated?.team_id === oppTeam.id && oppTeam.members.length ? rateTeam(oppTeam.members.length, oppRated) : null }
              : null,
            versus,
          )}
        />
      </div>

      <div style={{ marginTop: 14 }}>
        <TeamReport
          analysis={rated}
          team={team}
          opponent={opponentId && oppTeam?.id === opponentId ? { team: oppTeam, analysis: oppRated?.team_id === oppTeam.id ? oppRated : null } : null}
          vs={versus}
          onTeamChanged={(t) => setTeam(t)}
        />
      </div>

      {editing && (editing.side === "ours" || oppTeam) && (
        <SlotEditor
          team={editing.side === "ours" ? team : oppTeam!}
          initialSlot={editing.slot}
          natures={natures}
          onTeamChange={(t) => {
            if (editing.side === "ours") onTeamEdited(t);
            else setOppTeam(t);
          }}
          onClose={() => setEditing(null)}
        />
      )}
    </main>
  );
}
