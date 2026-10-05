"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type MouseEvent } from "react";
import { deleteTeam, listTeams, type TeamSummary } from "@/lib/api";
import { Facts, GradeBadge, Mini, RatingWhy, StrategyBars, SummaryText, useInfo, type Info } from "@/components/TeamCardParts";
import { createDraft, discarding, sweepDrafts } from "@/lib/draftTeams";

// The last list we showed — returning to the page draws it immediately, then refreshes.
let lastTeams: TeamSummary[] | null = null;

function TeamCard({ team, info, onDelete }: { team: TeamSummary; info?: Info; onDelete: (id: number) => void }) {
  const router = useRouter();
  const href = `/teams/${team.id}`;
  const { p, st, sum } = info ?? {};
  // The whole card opens the team; inner controls stop the click from bubbling.
  const open = (e: MouseEvent) => {
    if ((e.target as HTMLElement).closest("button, a")) return;
    router.push(href);
  };
  return (
    <article className="tl-card" onClick={open}>
      <header className="tl-head">
        <div className="tl-id">
          <Link href={href} className="tl-name">{team.name}</Link>
          <Mini team={team} />
        </div>
        {p && (
          <GradeBadge p={p} href={`${href}#rating`} />
        )}
      </header>

      {!p || !st ? (
        <span className="lab-skel" style={{ height: 150 }} />
      ) : (
        <>
          <SummaryText sum={sum} fallback={p.gist} />
          <div className="tl-body">
            <div>
              <span className="tl-style" title={st.style_reason}>{st.style}</span>
              <StrategyBars st={st} />
            </div>
            <div>
              <Facts p={p} />
            </div>
          </div>
          <RatingWhy p={p} />
        </>
      )}

      <footer className="tl-foot">
        <button className="tl-del" onClick={() => onDelete(team.id)}>Delete</button>
        <Link href={href} className="tl-go">Open →</Link>
      </footer>
    </article>
  );
}

export default function TeamsBrowser() {
  const router = useRouter();
  const [teams, setTeams] = useState<TeamSummary[]>(() => (lastTeams ?? []).filter((t) => !discarding.has(t.id)));
  const [loading, setLoading] = useState(lastTeams === null);
  // Cards animate in on the first visit only; coming back should look exactly as you left it.
  const [animate] = useState(lastTeams === null);
  const [creating, setCreating] = useState(false);
  const info = useInfo(teams);

  useEffect(() => {
    let alive = true;
    listTeams()
      .then(({ teams }) => {
        if (!alive) return;
        const swept = sweepDrafts(teams); // untouched "New team"s left by a closed tab
        const shown = teams.filter((t) => !discarding.has(t.id) && !swept.has(t.id));
        lastTeams = shown;
        setTeams(shown);
      })
      .catch(() => {})
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  /** One click: create an empty team and open it, where Pokémon are added. Rename it there. */
  const newTeam = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const id = await createDraft();
      router.push(`/teams/${id}?new=1`); // a draft until its first Pokémon is added
    } catch {
      setCreating(false);
    }
  };

  const remove = async (id: number) => {
    const before = teams;
    setTeams((t) => t.filter((x) => x.id !== id));
    lastTeams = (lastTeams ?? []).filter((x) => x.id !== id);
    try {
      await deleteTeam(id);
    } catch {
      setTeams(before);
    }
  };

  // Empty teams go last as slim rows, so they never leave a hole in the grid.
  const filled = teams.filter((t) => t.size > 0);
  const empty = teams.filter((t) => t.size === 0);

  return (
    <>
      <div className="tl-top">
        <div>
          <h2>Your teams</h2>
          {!loading && (
            <span>
              {teams.length} saved · rated by coverage, defence, speed, roles, sets and roster
            </span>
          )}
        </div>
        <button className="tl-new" onClick={newTeam} disabled={creating}>
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden>
            <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          {creating ? "Creating…" : "New team"}
        </button>
      </div>

      {loading ? (
        <div className="tl-card"><span className="lab-skel" /></div>
      ) : teams.length === 0 ? (
        <button className="tl-first" onClick={newTeam}>
          <b>Build your first team</b>
          <span>Add up to six Pokémon and see how it rates.</span>
        </button>
      ) : (
        <div className={`tl-masonry${animate ? " anim" : ""}`}>
          {filled.map((t) => (
            <TeamCard key={t.id} team={t} info={info[t.id]} onDelete={remove} />
          ))}
          {empty.map((t) => (
            <div key={t.id} className="tl-empty">
              <Link href={`/teams/${t.id}`}>
                <b>{t.name}</b>
                <Mini team={t} />
                <span>Empty — tap to add Pokémon</span>
              </Link>
              <button className="tl-del" onClick={() => remove(t.id)}>Delete</button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
