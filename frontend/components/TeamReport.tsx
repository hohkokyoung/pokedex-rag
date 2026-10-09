"use client";

import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { applySlotBuild, getTeamStrategy, setSlot, getTeamSummary, refreshTeamSummary, type VsOpponent, type Team, type TeamAnalysis, type TeamStrategy, type TeamSummaryText, thumb } from "@/lib/api";
import { Chip, StrategyBars } from "@/components/TeamCardParts";
import TeamMatchupText, { matchupHeadline, tally } from "@/components/TeamMatchupText";
import { titleCase, typeVars } from "@/lib/pokeTypes";
import { gradeTone, profileOf, type Area, type Profile, type Rating } from "@/lib/teamEval";

/** Overall grade as a drawn ring around the letter. */
export function GradeRing({ score, grade, size = 76 }: { score: number; grade: string; size?: number }) {
  const r = 30;
  const L = 2 * Math.PI * r;
  return (
    <span className={`ev-ring ${gradeTone(grade as Area["grade"])}`} style={{ width: size, height: size }}>
      <svg viewBox="0 0 76 76" aria-hidden>
        <circle cx="38" cy="38" r={r} className="trk" />
        <circle
          key={score}
          cx="38"
          cy="38"
          r={r}
          className="val"
          style={{ "--L": L, "--off": L * (1 - score / 100) } as CSSProperties}
        />
      </svg>
      <b>{grade}</b>
    </span>
  );
}

export function GradeTag({ grade }: { grade: Area["grade"] }) {
  return <span className={`ev-grade ${gradeTone(grade)}`}>{grade}</span>;
}

function TypeCells({ cells }: { cells: { type: string; tone: "on" | "half" | "off" | "bad"; tip: string }[] }) {
  return (
    <span className="ev-cells">
      {cells.map((c) => (
        <i
          key={c.type}
          className={c.tone}
          title={c.tip}
          style={typeVars(c.type, "--c") as CSSProperties}
        >
          {c.type.slice(0, 3)}
        </i>
      ))}
    </span>
  );
}

function Detail({ area, rating, a }: { area: Area; rating: Rating; a: TeamAnalysis }) {
  switch (area.key) {
    case "coverage":
      return (
        <>
          <TypeCells
            cells={rating.cover.map((c) => ({
              type: c.type,
              tone: c.now ? "on" : c.learnable ? "half" : "off",
              tip: `${titleCase(c.type)}: ${c.now ? "hit super-effectively" : c.learnable ? "only with learnable moves" : "not hit super-effectively"}`,
            }))}
          />
          <p className="ev-legend">
            <span><i className="on" />covered now</span>
            <span><i className="half" />with learnable moves</span>
          </p>
        </>
      );
    case "defence":
      return <DefenceTug a={a} />;
    case "speed": {
      const spe = (r: (typeof a.roles.members)[number]) => r.eff_speed ?? r.speed;
      const rows = [...a.roles.members].sort((x, y) => spe(y) - spe(x));
      const max = Math.max(150, ...rows.map(spe));
      return (
        <ul className="ev-bars">
          {rows.map((r) => (
            <li key={r.slot} title={r.speed_note ?? undefined}>
              <span>{r.name}</span>
              <i>
                <b style={{ width: `${(spe(r) / max) * 100}%` }} className={spe(r) >= rating.fast_speed ? "ok" : ""} />
                <em style={{ left: `${(rating.fast_speed / max) * 100}%` }} />
              </i>
              <span className="n">{spe(r) !== r.speed ? <>{r.speed}→<b>{spe(r)}</b></> : r.speed}</span>
            </li>
          ))}
        </ul>
      );
    }
    case "roles": {
      const m = a.roles.members;
      const role = (label: string, rule: string, who: string[]) => (
        <li key={label} className={who.length ? "ok" : ""}>
          <span className="ic">{who.length ? "✓" : "!"}</span>
          <span><b>{label}</b> <small>{rule}</small></span>
          <span className="who">{who.length ? who.join(", ") : "none"}</span>
        </li>
      );
      return (
        <ul className="ev-roles">
          {role("Fast attacker", `base Speed ${rating.fast_speed}+`, m.filter((r) => r.speed >= rating.fast_speed).map((r) => r.name))}
          {role("Wall", "HP + Def + SpD 280+", m.filter((r) => r.bulk >= 280).map((r) => r.name))}
          {role("Wallbreaker", "best attack 110+", m.filter((r) => r.offense >= 110).map((r) => r.name))}
        </ul>
      );
    }
    case "sets":
      return (
        <ul className="tr-sets">
          {(a.sets?.members ?? []).map((m) => (
            <li key={m.slot}>
              <b>{m.name}</b>
              <span className={m.item ? "" : "un"} title={m.item_note ?? undefined}>{m.item ?? "no item"}</span>
              <span className={m.ability ? "" : "un"} title={m.ability_note ?? undefined}>{m.ability ?? "no ability"}</span>
              <span className="mv">
                {[...m.setup, ...m.priority, ...m.recovery].slice(0, 2).join(", ") || `${m.moves_set}/4 moves`}
              </span>
            </li>
          ))}
        </ul>
      );
    case "roster":
      return (
        <span className="ev-roster">
          {Array.from({ length: 6 }, (_, i) => <i key={i} className={i < a.size ? "on" : ""} />)}
        </span>
      );
  }
}

/** The stored team summary, with a manual Regenerate (the only way to force an AI call). */
function SummaryLine({ teamId, version }: { teamId: number; version: unknown }) {
  const [sum, setSum] = useState<TeamSummaryText | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let alive = true;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const load = (tries: number) =>
      getTeamSummary(teamId)
        .then((s) => {
          if (!alive) return;
          setSum(s);
          if (s.pending && tries > 0) timers.push(setTimeout(() => load(tries - 1), 4000));
        })
        .catch(() => {});
    load(2);
    return () => {
      alive = false;
      timers.forEach(clearTimeout);
    };
  }, [teamId, version]);
  const regen = async () => {
    setBusy(true);
    try {
      setSum(await refreshTeamSummary(teamId));
    } finally {
      setBusy(false);
    }
  };
  if (!sum) return null;
  return (
    <p className="tl-sum tr-sum">
      <span className={`tl-src ${sum.source}`}>{sum.source === "ai" ? "AI" : "Auto"}</span>
      {sum.text}
      <button onClick={regen} disabled={busy} title="Write a fresh summary">
        {busy ? "Writing…" : "↻ Regenerate"}
      </button>
    </p>
  );
}

const mult = (f: number) => (f === 0 ? "0" : f === 0.25 ? "¼" : f === 0.5 ? "½" : `${f}×`);
type Hit = { name: string; f: number };
/** Hover card for a defence row: who is weak (red, ×4 called out) and who resists or is immune. */
function TugTip({ type, weak, cover, by }: { type: string; weak: Hit[]; cover: Hit[]; by?: string[] }) {
  const list = (xs: Hit[], cls: string) =>
    xs.length ? xs.map((x) => <span key={x.name} className={cls}>{x.name}{x.f !== 2 && x.f !== 0.5 && <em>{mult(x.f)}</em>}</span>) : <span className="none">nobody</span>;
  return (
    <span className="tr-tip" role="tooltip">
      <b className="h">{titleCase(type)} attacks</b>
      {by && by.length > 0 && <span className="row"><small>Used by</small><span className="who">{by.map((n) => <span key={n}>{n}</span>)}</span></span>}
      <span className="row"><small>Weak</small><span className="who">{list(weak, "w")}</span></span>
      <span className="row"><small>Resists</small><span className="who">{list(cover, "c")}</span></span>
    </span>
  );
}

/** Defence as tug bars: per attacking type, members it hits super-effectively pull
 *  left (red, solid for 4×), members that resist or are immune pull right (green). */
function DefenceTug({ a }: { a: TeamAnalysis }) {
  const rows = ATTACK_TYPES.map((type) => {
    const weak: { name: string; f: number }[] = [];
    const cover: { name: string; f: number }[] = [];
    for (const m of a.defensive.matrix) {
      const f = m.multipliers[type] ?? 1;
      if (f >= 2) weak.push({ name: m.name, f });
      else if (f < 1) cover.push({ name: m.name, f });
    }
    return { type, weak: weak.sort((x, y) => y.f - x.f), cover };
  })
    .filter((r) => r.weak.length)
    .sort((x, y) => y.weak.length - y.cover.length - (x.weak.length - x.cover.length) || y.weak.length - x.weak.length);
  const max = Math.max(3, ...rows.map((r) => Math.max(r.weak.length, r.cover.length)));
  return (
    <div className="tr-tug">
      {rows.map((r) => {
        const net = r.weak.length - r.cover.length;
        return (
          <div key={r.type} className="tr-tug-r" tabIndex={0}>
            <TugTip type={r.type} weak={r.weak} cover={r.cover} />
            <Chip t={r.type} />
            <span className="l">
              {Array.from({ length: max }, (_, i) => {
                const w = r.weak[max - 1 - i];
                return <i key={i} className={w ? (w.f >= 4 ? "on x4" : "on") : ""} />;
              })}
            </span>
            <span className="mid" />
            <span className="r">{Array.from({ length: max }, (_, i) => <i key={i} className={i < r.cover.length ? "on" : ""} />)}</span>
            <b className={net > 0 ? "bad" : net < 0 ? "good" : ""}>{net > 0 ? `+${net} weak` : net < 0 ? "covered" : "even"}</b>
          </div>
        );
      })}
    </div>
  );
}
const ATTACK_TYPES = [
  "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground",
  "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy",
];

function Card({ icon, title, sub, right, wide, children }: {
  icon: ReactNode; title: ReactNode; sub?: ReactNode; right?: ReactNode; wide?: boolean; children?: ReactNode;
}) {
  return (
    <article className={`tr-card${wide ? " wide" : ""}`}>
      <header>
        {icon}
        <div className="t"><b>{title}</b>{sub && <span>{sub}</span>}</div>
        {right}
      </header>
      {children}
    </article>
  );
}
const GradeIcon = ({ g }: { g: Area["grade"] }) => <span className={`tr-gicon ${gradeTone(g)}`}>{g}</span>;
const Note = ({ fix, children }: { fix?: boolean; children: ReactNode }) => (
  <p className="tr-note">{fix && <b>Fix </b>}{children}</p>
);

function TypeFacts({ p, compact = false }: { p: Profile; compact?: boolean }) {
  const net = (xs: Profile["weak_to"]) => xs.map((w) => <Chip key={w.type} t={w.type} n={w.net > 1 ? `×${w.net}` : undefined} />);
  return (
    <dl className="tl-dl tr-dl">
      <div><dt>Weak to</dt><dd>{p.weak_to.length ? net(p.weak_to) : <span className="ok">No weaknesses</span>}</dd></div>
      <div><dt>Resists</dt><dd>{p.resists.length ? net(p.resists) : <span className="dim">Nothing</span>}</dd></div>
      <div><dt>Hits hard</dt><dd><b>{p.strong_vs.length}</b>/18{!compact && <> · {p.strong_vs.map((t) => <Chip key={t} t={t} />)}</>}</dd></div>
      <div><dt>Core</dt><dd>{p.core_types.slice(0, 3).map((t) => <Chip key={t} t={t} />)}</dd></div>
    </dl>
  );
}

type Member = Team["members"][number];

/** A held item to start from when the slot has none, by the member's role. */
/** Each member's set, with the engine's suggestion shown wherever nothing is set yet,
 *  and a button to use it (Undo puts the old set back). */
function SetsDetail({ team, a, onChanged }: { team: Team; a: TeamAnalysis; onChanged?: (t: Team) => void }) {
  const [busy, setBusy] = useState<number | null>(null);
  const [undo, setUndo] = useState<Record<number, Member>>({});
  const [err, setErr] = useState<string | null>(null);
  const rows = [...team.members].sort((x, y) => x.slot - y.slot).map((m) => {
    const sug = a.suggestions.find((x) => x.slot === m.slot);
    return { m, sug, item: m.item?.name ?? null, sugItem: sug?.recommended_item ?? null };
  });
  const use = async (r: (typeof rows)[number]) => {
    if (!onChanged || !r.sug) return;
    setBusy(r.m.slot);
    setErr(null);
    try {
      const t = await applySlotBuild(team.id, r.m.slot, {
        moves: r.m.moves.length ? undefined : r.sug.recommended_moves.map((x) => x.name),
        ability: r.m.ability ? undefined : r.sug.recommended_ability,
        nature: r.m.nature ? undefined : r.sug.recommended_nature,
        item: r.m.item ? undefined : r.sugItem,
        evs: Object.keys(r.m.ev_spread ?? {}).length ? undefined : r.sug.recommended_evs,
      });
      setUndo((u) => ({ ...u, [r.m.slot]: r.m }));
      onChanged(t);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't apply the suggestion.");
    } finally {
      setBusy(null);
    }
  };
  const revert = async (slot: number) => {
    const b = undo[slot];
    if (!b || !onChanged) return;
    setBusy(slot);
    try {
      const t = await setSlot(team.id, slot, {
        pokemon_id: b.pokemon_id, form_id: b.form_id ?? null, ability_id: b.ability?.id ?? null,
        nature_id: b.nature?.id ?? null, item_id: b.item?.id ?? null, ev_spread: b.ev_spread ?? null,
        iv_spread: b.iv_spread ?? null, move_ids: b.moves.length ? b.moves.map((x) => x.move_id) : null,
      });
      setUndo((u) => { const n = { ...u }; delete n[slot]; return n; });
      onChanged(t);
    } finally {
      setBusy(null);
    }
  };
  return (
    <div className="tr-sets2">
      {rows.map((r) => {
        const empty = !r.m.item || !r.m.ability || !r.m.moves.length;
        return (
          <div key={r.m.slot} className="row">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img loading="lazy" decoding="async" src={thumb(r.m.sprite_url, 48)} alt="" width={30} height={30} />
            <div className="who">
              <b>{r.m.name}</b>
              <span>
                {r.m.item ? <>{r.m.item.name}</> : <em className="sug">{r.sugItem}</em>}
                {" · "}
                {r.m.ability ? <>{r.m.ability.name}</> : r.sug?.recommended_ability ? <em className="sug">{r.sug.recommended_ability}</em> : "—"}
                {" · "}
                {r.m.moves.length ? `${r.m.moves.length}/4 moves` : r.sug?.recommended_moves.length ? <em className="sug">{r.sug.recommended_moves.map((x) => x.name).join(", ")}</em> : "no moves"}
              </span>
            </div>
            {onChanged && (undo[r.m.slot]
              ? <button className="undo" onClick={() => revert(r.m.slot)} disabled={busy === r.m.slot}>{busy === r.m.slot ? "…" : "Undo"}</button>
              : empty && r.sug
                ? <button onClick={() => use(r)} disabled={busy === r.m.slot}>{busy === r.m.slot ? "Saving…" : "Use suggested"}</button>
                : null)}
          </div>
        );
      })}
      <p className="legend"><em className="sug">Grey italics</em> = suggested, not set yet. “Use suggested” fills only the empty parts.</p>
      {err && <p className="err">{err}</p>}
    </div>
  );
}

/** Your defence against the types the opponent actually attacks with (STAB and its
 *  moves — set, or the learnable ones the engine fills in). */
function DefenceVs({ a, opp, oppA }: { a: TeamAnalysis; opp: Team; oppA: TeamAnalysis | null }) {
  const carriers = new Map<string, Member[]>();
  for (const m of opp.members) {
    const moves = m.moves.length
      ? m.moves.filter((x) => x.damage_class !== "status").map((x) => x.type)
      : (oppA?.suggestions.find((x) => x.slot === m.slot)?.recommended_moves ?? []).filter((x) => x.damage_class !== "status").map((x) => x.type);
    for (const t of new Set([...m.types, ...moves].filter(Boolean) as string[])) carriers.set(t, [...(carriers.get(t) ?? []), m]);
  }
  const rows = [...carriers.keys()].map((type) => {
    const weak: Hit[] = [], cover: Hit[] = [];
    for (const m of a.defensive.matrix) {
      const f = m.multipliers[type] ?? 1;
      if (f >= 2) weak.push({ name: m.name, f });
      else if (f < 1) cover.push({ name: m.name, f });
    }
    return { type, weak: weak.sort((x, y) => y.f - x.f), cover, who: carriers.get(type)! };
  }).filter((r) => r.weak.length).sort((x, y) => y.weak.length - y.cover.length - (x.weak.length - x.cover.length) || y.weak.length - x.weak.length);
  const max = Math.max(3, ...rows.map((r) => Math.max(r.weak.length, r.cover.length)));
  if (!rows.length) return <p className="tr-note">None of their attacking types hits your team super-effectively.</p>;
  return (
    <div className="tr-tug vs">
      {rows.map((r) => {
        const net = r.weak.length - r.cover.length;
        return (
          <div key={r.type} className="tr-tug-r vs" tabIndex={0}>
            <TugTip type={r.type} weak={r.weak} cover={r.cover} by={r.who.map((m) => m.name)} />
            <Chip t={r.type} />
            <span className="l">{Array.from({ length: max }, (_, i) => { const w = r.weak[max - 1 - i]; return <i key={i} className={w ? (w.f >= 4 ? "on x4" : "on") : ""} />; })}</span>
            <span className="mid" />
            <span className="r">{Array.from({ length: max }, (_, i) => <i key={i} className={i < r.cover.length ? "on" : ""} />)}</span>
            <b className={net > 0 ? "bad" : net < 0 ? "good" : ""}>{net > 0 ? `+${net} weak` : net < 0 ? "covered" : "even"}</b>
            <span className="by">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {r.who.slice(0, 4).map((m) => <img loading="lazy" decoding="async" key={m.slot} src={thumb(m.sprite_url, 48)} alt={m.name} width={24} height={24} />)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** Strategy axes for two teams: yours over theirs on each axis. */
function PairedBars({ ours, theirs }: { ours: TeamStrategy; theirs: TeamStrategy }) {
  return (
    <div className="tr-pair">
      <span className="tl-legend"><i className="n" />you <i className="t" />them</span>
      {ours.axes.map((x) => {
        const o = theirs.axes.find((y) => y.key === x.key);
        const t = o?.now ?? 0;
        return (
          <div key={x.key} className="tr-pbar" title={x.detail}>
            <span className="k">{x.label}</span>
            <span className="bars"><i className="y" style={{ width: `${x.now}%` }} /><i className="t" style={{ width: `${t}%` }} /></span>
            <span className="v"><b className={x.now > t ? "y" : ""}>{x.now}</b> · <b className={t > x.now ? "t" : ""}>{t}</b></span>
          </div>
        );
      })}
    </div>
  );
}

/** The team page's report: rating + summary, how it plays, type profile and the
 *  areas that need work. Same numbers as the /teams card (the backend rating). With an
 *  opponent picked, every part shows both teams and a written matchup is added. */
export default function TeamReport({
  analysis,
  team,
  opponent = null,
  vs = null,
  onTeamChanged,
}: {
  analysis: TeamAnalysis | null;
  team: Team;
  opponent?: { team: Team; analysis: TeamAnalysis | null } | null;
  vs?: VsOpponent | null;
  /** Called after the report itself changes the team (e.g. "Use suggested" on Sets). */
  onTeamChanged?: (t: Team) => void;
}) {
  const [st, setSt] = useState<TeamStrategy | null>(null);
  const [opStrat, setOpStrat] = useState<{ id: number; st: TeamStrategy } | null>(null);
  useEffect(() => {
    let alive = true;
    getTeamStrategy(team.id).then((x) => alive && setSt(x)).catch(() => {});
    return () => {
      alive = false;
    };
  }, [team.id, analysis]);
  const opId = opponent?.team.id;
  // Only the strategy fetched for the current opponent counts (a stale one is ignored).
  const opSt = opStrat && opStrat.id === opId ? opStrat.st : null;
  useEffect(() => {
    let alive = true;
    if (opId != null) getTeamStrategy(opId).then((x) => alive && setOpStrat({ id: opId, st: x })).catch(() => {});
    return () => {
      alive = false;
    };
  }, [opId, opponent?.analysis]);

  if (team.members.length === 0)
    return (
      <section className="panel tr">
        <h2 className="ev-title">Team rating</h2>
        <p className="ev-empty">Add your first Pokémon to rate the team.</p>
      </section>
    );
  if (!analysis) return <section className="panel tr"><span className="lab-skel" style={{ height: 120 }} /></section>;
  // The backend's rating; a stale analysis from before the first add has none yet.
  const p = profileOf(analysis);
  if (!p) return <section className="panel tr"><span className="lab-skel" style={{ height: 120 }} /></section>;
  const r = p.rating;
  const gaps = r.areas.filter((x) => x.fix).sort((x, y) => x.score - y.score);
  const op = opponent?.team.members.length ? profileOf(opponent.analysis) : null;
  const or = op?.rating ?? null;
  const t = vs ? tally(vs) : null;
  // One style label everywhere: the strategy engine's (it counts setup, support and
  // stall moves), as on the /teams cards; the stat-only read is the fallback.
  const style = st?.style ?? p.style;
  const opStyle = opSt?.style ?? op?.style ?? "";
  // With an opponent, Defence gets its own "vs them" card instead.
  // Roster has no card (the roster section shows it); with an opponent, Defence gets a "vs them" card.
  const gapsShown = gaps.filter((x) => x.key !== "roster" && !(op && x.key === "defence"));
  return (
    <section className="panel tr" id="rating">
      {op && or && opponent ? (
        <div className="tr-top tr-vs">
          <div className="side">
            <GradeRing score={r.overall} grade={r.grade} size={72} />
            <div><h2 className="ev-title">{team.name}</h2><p className="ev-sub"><b>{r.overall}</b>/100 · <span className="tr-style you">{style}</span></p>{r.capped && <span className="tr-scaled">Scaled for a {Math.round(r.ceiling * 6 / 100)}/6 roster</span>}</div>
          </div>
          <div className="mid">
            {vs && t ? (
              <>
                <b>{matchupHeadline(vs, opponent.team.name)}</b>
                <span>You win {t.you} of {t.n} one-on-ones, they win {t.them}{t.close ? `, ${t.close} close` : ""}</span>
                <span className="tr-tri"><i className="y" style={{ flex: t.you }} /><i className="e" style={{ flex: t.close }} /><i className="t" style={{ flex: t.them }} /></span>
              </>
            ) : <span className="lab-skel" style={{ height: 40, width: 220 }} />}
          </div>
          <div className="side r">
            <div><h2 className="ev-title">{opponent.team.name}</h2><p className="ev-sub"><b>{or.overall}</b>/100 · <span className="tr-style them">{opStyle}</span></p>{or.capped && <span className="tr-scaled">Scaled for a {Math.round(or.ceiling * 6 / 100)}/6 roster</span>}</div>
            <GradeRing score={or.overall} grade={or.grade} size={72} />
          </div>
          <div className="sums">
            <SummaryLine teamId={team.id} version={analysis} />
            <SummaryLine teamId={opponent.team.id} version={opponent.analysis} />
          </div>
        </div>
      ) : (
        <div className="tr-top">
          <GradeRing score={r.overall} grade={r.grade} size={84} />
          <div style={{ minWidth: 0 }}>
            <h2 className="ev-title">Team rating</h2>
            <p className="ev-sub">
              <b>{r.overall}</b>/100 · <span className="tr-style">{style}</span> · {p.lean.toLowerCase()} lean
              {gaps[0] && <> · biggest gap <b>{gaps[0].label.toLowerCase()}</b></>}
              {r.capped && <span className="ev-cap">Scaled to {Math.round(r.ceiling * 6 / 100)}/6 — fill every slot for the full rating</span>}
            </p>
            <SummaryLine teamId={team.id} version={analysis} />
          </div>
        </div>
      )}

      {or ? (
        <div className="tr-cmp" aria-label="Area grades, you vs them">
          {r.areas.map((x) => {
            const o = or.areas.find((y) => y.key === x.key)!;
            const diff = x.score - o.score;
            const lead = Math.abs(diff) < 5 ? "even" : diff > 0 ? "you" : "them";
            const share = x.score + o.score ? (x.score / (x.score + o.score)) * 100 : 50;
            return (
              <div key={x.key} className={`tr-cmp-t ${lead}`} title={`You: ${x.headline}\nThem: ${o.headline}`}>
                <span className="lbl">{x.label}</span>
                <div className="g">
                  <span className="side"><span className="n"><GradeIcon g={x.grade} /><b>{x.score}</b></span><small>You</small></span>
                  <span className="side r"><span className="n"><b>{o.score}</b><GradeIcon g={o.grade} /></span><small>Them</small></span>
                </div>
                <span className="bar"><i className="y" style={{ width: `${share}%` }} /><i className="t" /></span>
                <span className="v">{lead === "even" ? "Even" : lead === "you" ? `You lead by ${diff}` : `They lead by ${-diff}`}</span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="tr-strip">
          {r.areas.map((x) => (
            <span key={x.key} className="tr-pill" title={x.headline}>
              <GradeIcon g={x.grade} />
              {x.label}
              <small>{x.score}</small>
            </span>
          ))}
        </div>
      )}

      <div className="tr-grid">
        {vs && opponent && (
          <Card wide icon={<span className="tr-gicon ink vs">vs</span>} title={`Matchup vs ${opponent.team.name}`} sub="One-on-ones played out with each side's moves, items, abilities and setup">
            <TeamMatchupText team={team} opponent={opponent.team} vs={vs} />
          </Card>
        )}
        <Card icon={<span className="tr-gicon ink">◆</span>} title="How it plays" sub={op ? `${style} vs ${opStyle}` : `${style} · ${p.lean.toLowerCase()} lean`}>
          {st && op ? (opSt ? <PairedBars ours={st} theirs={opSt} /> : <span className="lab-skel" style={{ height: 110 }} />)
            : st ? <StrategyBars st={st} /> : <span className="lab-skel" style={{ height: 110 }} />}
          <Note>{st?.style_reason ? `Reads as ${st.style.toLowerCase()}: ${st.style_reason}.` : p.style_why}</Note>
        </Card>
        <Card icon={<span className="tr-gicon ink">◇</span>} title="Type profile" sub={op ? `You hit ${p.strong_vs.length}/18 hard, they hit ${op.strong_vs.length}/18` : `Hits ${p.strong_vs.length} of 18 hard · ${p.weak_to.length} weak spot${p.weak_to.length === 1 ? "" : "s"}`}>
          {op ? (
            <div className="tr-types2">
              <div><h6>You</h6><TypeFacts p={p} compact /></div>
              <div><h6 className="t">Them</h6><TypeFacts p={op} compact /></div>
            </div>
          ) : <TypeFacts p={p} />}
        </Card>
        {op && opponent && (() => {
          const d = r.areas.find((x) => x.key === "defence")!;
          return (
            <Card wide icon={<GradeIcon g={d.grade} />} title={`Defence vs ${opponent.team.name}`} sub="Their attacking types against your six. Sprites show who on their side uses each." right={<span className="tr-score">{d.score}</span>}>
              <DefenceVs a={analysis} opp={opponent.team} oppA={opponent.analysis} />
            </Card>
          );
        })()}
        {gapsShown.map((area, i) => (
          <Card
            key={area.key}
            wide={gapsShown.length % 2 === 1 && i === gapsShown.length - 1}
            icon={<GradeIcon g={area.grade} />}
            title={area.label}
            sub={area.headline}
            right={<span className="tr-score">{area.score}</span>}
          >
            {area.key === "sets" ? <SetsDetail team={team} a={analysis} onChanged={onTeamChanged} /> : <Detail area={area} rating={r} a={analysis} />}
            <Note fix>{area.fix}</Note>
          </Card>
        ))}
      </div>
    </section>
  );
}
