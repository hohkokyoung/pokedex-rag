"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  BULKY_SET,
  DcPicker,
  EvEditor,
  MoveSearch,
  NAT_OPTS,
  InfoBox,
  PickSearch,
  Tag,
  natDesc,
  natTag,
  loadCalcMon,
  loadMonMoves,
  offensiveSet,
  type CalcMon,
  type CalcMove,
  type EVs,
  type PickOpt,
  type SKey,
} from "@/components/calc/fields";
import {
  assetUrl,
  clearSlot,
  getPokemonAbilities,
  getHeldItems,
  setSlot,
  type SlotItem,
  type NatureInfo,
  type Team,
  type TeamMember,
} from "@/lib/api";
import type { Ability, PokemonSummary } from "@/lib/types";
import { TYPE_HEX } from "@/lib/pokeTypes";

type Ask = { title: string; body: string; action: string; sprite?: string; resolve: (ok: boolean) => void };

const LEVEL = 50; // matches backend services/stats.DEFAULT_LEVEL
const SLOTS = [1, 2, 3, 4, 5, 6];
const MOVE_SLOTS = [0, 1, 2, 3];
// Every Pokémon has an ability and a nature — there is no "none". An unset nature
// reads as Hardy (neutral); an unset ability as the species' first regular one.
const DEFAULT_NATURE = "Hardy";
const NO_ITEM = "No item";
// Every holdable item is loaded once and filtered as you type; these common competitive
// picks are listed first, the rest alphabetically.
const COMMON_ITEMS = [
  "leftovers", "life-orb", "choice-band", "choice-specs", "choice-scarf", "focus-sash",
  "assault-vest", "heavy-duty-boots", "rocky-helmet", "sitrus-berry", "lum-berry", "expert-belt",
  "eviolite", "black-sludge", "weakness-policy", "booster-energy", "light-clay", "air-balloon",
  "covert-cloak", "clear-amulet", "loaded-dice", "safety-goggles", "white-herb", "mirror-herb",
];
let heldItems: Promise<SlotItem[]> | null = null;
const loadHeldItems = () =>
  (heldItems ??= getHeldItems()
    .then((xs) => {
      const rank = (id: string) => {
        const i = COMMON_ITEMS.indexOf(id);
        return i < 0 ? COMMON_ITEMS.length : i;
      };
      // The dataset repeats a few names (e.g. two Roseli Berry rows); keep one per name,
      // preferring the entry that has a description.
      const byName = new Map<string, (typeof xs)[number]>();
      for (const x of xs) if (!byName.has(x.name) || (!byName.get(x.name)!.short_effect && x.short_effect)) byName.set(x.name, x);
      return [...byName.values()]
        .sort((a, b) => rank(a.identifier) - rank(b.identifier) || a.name.localeCompare(b.name))
        .map((x) => ({ id: x.id, name: x.name, category: x.category, short_effect: x.short_effect }));
    })
    .catch(() => {
      heldItems = null;
      return [];
    }));
// Calculator stat keys ↔ the team API's spread keys.
const TEAM_KEY: Record<SKey, string> = { hp: "hp", atk: "attack", def: "defense", spa: "sp_attack", spd: "sp_defense", spe: "speed" };
const KEYS = Object.keys(TEAM_KEY) as SKey[];

const fromTeam = (spread: Record<string, number> | null | undefined, fill: number): EVs =>
  Object.fromEntries(KEYS.map((k) => [k, spread?.[TEAM_KEY[k]] ?? fill])) as EVs;
const toTeam = (v: EVs): Record<string, number> => Object.fromEntries(KEYS.map((k) => [TEAM_KEY[k], v[k]]));

/**
 * Team editor, built from the damage calculator's parts. The roster on the left
 * edits the whole team in place — switch slots, add to empty ones, remove
 * members — and the panel on the right edits one slot. Saving keeps it open.
 */
export default function SlotEditor({
  team,
  initialSlot,
  natures,
  onTeamChange,
  onClose,
}: {
  team: Team;
  initialSlot: number;
  natures: NatureInfo[];
  onTeamChange: (team: Team) => void;
  onClose: () => void;
}) {
  const [slot, setSlotNo] = useState(initialSlot);
  const [removing, setRemoving] = useState<number | null>(null);
  const dirty = useRef(false);

  const memberAt = (n: number): TeamMember | null => team.members.find((m) => m.slot === n) ?? null;
  const member = memberAt(slot);

  // In-modal confirmation (replaces the browser's confirm()); resolves true on the action.
  const [ask, setAsk] = useState<Ask | null>(null);
  const askRef = useRef<Ask | null>(null);
  useEffect(() => {
    askRef.current = ask;
  }, [ask]);
  const confirm = useCallback(
    (a: Omit<Ask, "resolve">) => new Promise<boolean>((resolve) => setAsk({ ...a, resolve })),
    [],
  );
  const answer = (ok: boolean) => {
    ask?.resolve(ok);
    setAsk(null);
  };

  const guard = useCallback(
    async () =>
      !dirty.current ||
      confirm({ title: "Discard changes?", body: "Your edits to this slot haven't been saved.", action: "Discard" }),
    [confirm],
  );
  const close = useCallback(async () => {
    if (await guard()) onClose();
  }, [guard, onClose]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      // Escape backs out of an open confirmation first…
      if (askRef.current) {
        askRef.current.resolve(false);
        setAsk(null);
        return;
      }
      // …and inside a search field it only closes that list.
      if (!(e.target instanceof HTMLInputElement)) close();
    };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [close]);

  const go = async (n: number) => {
    if (n === slot || !(await guard())) return;
    dirty.current = false;
    setSlotNo(n);
  };

  const remove = async (n: number) => {
    const m = memberAt(n);
    if (!m || removing !== null) return;
    const ok = await confirm({
      title: `Remove ${m.name}?`,
      body: `Slot ${n} of ${team.name} will be emptied.`,
      action: "Remove",
      sprite: m.sprite_url,
    });
    if (!ok) return;
    setRemoving(n);
    try {
      const updated = await clearSlot(team.id, n);
      if (n === slot) dirty.current = false;
      onTeamChange(updated);
    } finally {
      setRemoving(null);
    }
  };

  if (typeof document === "undefined") return null;
  // Portaled to <body>: the page wrapper animates with a transform, which would
  // trap this overlay in its stacking context beneath the fixed nav.
  return createPortal(
    <div className="se-scrim" onClick={close}>
      <div className="se dc" role="dialog" aria-modal="true" aria-label={`Edit ${team.name}`} onClick={(e) => e.stopPropagation()}>
        <div className="se-top">
          <span className="dc-k">
            Team · <b>{team.name}</b> · {team.members.length}/6
          </span>
          <button className="se-x" onClick={close} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="se-main">
          <div className="se-ros" role="tablist" aria-label="Team slots">
            {SLOTS.map((n) => {
              const m = memberAt(n);
              return (
                <div key={n} className="se-rcw">
                  <button
                    role="tab"
                    aria-selected={n === slot}
                    className={`dc-rc${n === slot ? " on" : ""}${m ? "" : " empty"}`}
                    onClick={() => go(n)}
                  >
                    {m ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={assetUrl(m.sprite_url)} alt="" />
                    ) : (
                      <span className="add" aria-hidden>
                        +
                      </span>
                    )}
                    <b>{m?.name ?? `Slot ${n}`}</b>
                    {m ? (
                      <small className="tps">
                        {m.types.map((t) => (
                          <Tag key={t} t={t} />
                        ))}
                      </small>
                    ) : (
                      <small>Add Pokémon</small>
                    )}
                  </button>
                  {m && (
                    <button
                      className="se-rm"
                      onClick={() => remove(n)}
                      disabled={removing !== null}
                      aria-label={`Remove ${m.name}`}
                      title={`Remove ${m.name}`}
                    >
                      {removing === n ? (
                        "…"
                      ) : (
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
                          <path d="M6 6l12 12M18 6L6 18" />
                        </svg>
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <SlotForm
            key={`${slot}:${member?.pokemon_id ?? "new"}:${member?.form_id ?? ""}`}
            teamId={team.id}
            slot={slot}
            member={member}
            natures={natures}
            onDirty={(d) => (dirty.current = d)}
            onSaved={onTeamChange}
            onClose={close}
          />
        </div>

        {ask && (
          <div className="se-ask" onClick={() => answer(false)}>
            <div className="se-askc" role="alertdialog" aria-modal="true" aria-labelledby="se-ask-t" onClick={(e) => e.stopPropagation()}>
              {ask.sprite && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={assetUrl(ask.sprite)} alt="" />
              )}
              <b id="se-ask-t">{ask.title}</b>
              <p>{ask.body}</p>
              <div className="se-askb">
                <button className="se-btn ghost" onClick={() => answer(false)}>
                  Cancel
                </button>
                <button className="se-btn primary" onClick={() => answer(true)} autoFocus>
                  {ask.action}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}

function SlotForm({
  teamId,
  slot,
  member,
  natures,
  onDirty,
  onSaved,
  onClose,
}: {
  teamId: number;
  slot: number;
  member: TeamMember | null;
  natures: NatureInfo[];
  onDirty: (dirty: boolean) => void;
  onSaved: (team: Team) => void;
  onClose: () => void;
}) {
  const [mon, setMon] = useState<CalcMon | null>(
    member
      ? {
          // A form member is keyed by its form id, as in the calculator.
          id: member.form_id ?? member.pokemon_id,
          formId: member.form_id ?? null,
          name: member.name,
          dex: member.dex_number,
          types: member.types,
          stats: member.base_stats as CalcMon["stats"],
          sprite: member.form_id ? member.sprite_url : undefined,
        }
      : null,
  );
  const [abilities, setAbilities] = useState<Ability[]>([]);
  const [learnset, setLearnset] = useState<{ moves: CalcMove[]; ids: Map<string, number> } | null>(null);

  const [abil, setAbil] = useState<string | null>(member?.ability?.name ?? null);
  const [nat, setNat] = useState(member?.nature?.name ?? DEFAULT_NATURE);
  const [ev, setEv] = useState<EVs>(fromTeam(member?.ev_spread, 0));
  const [iv, setIv] = useState<EVs>(fromTeam(member?.iv_spread, 31));
  const [pre, setPre] = useState("Custom");
  const [picks, setPicks] = useState<(string | null)[]>(MOVE_SLOTS.map((i) => member?.moves[i]?.name ?? null));
  // Which move box is open as a search field.
  const [editing, setEditing] = useState<string | null>(null);
  const [item, setItem] = useState<SlotItem | null>(member?.item ?? null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [dirty, setDirtyState] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const touch = () => {
    setDirtyState(true);
    setSaved(false);
    onDirty(true);
  };

  // The species' legal abilities and whole learnset — damaging moves first
  // (STAB, then power), status moves after, as in the calculator.
  useEffect(() => {
    if (!mon) return;
    let alive = true;
    // A form brings its own abilities (from the species detail) and learnset.
    const abilitiesOf = (m: CalcMon) =>
      m.abilities
        ? Promise.resolve(m.abilities)
        : m.formId != null
          ? loadCalcMon(m.dex, m.formId).then((f) => f.abilities ?? [])
          : getPokemonAbilities(m.id);
    Promise.all([abilitiesOf(mon), loadMonMoves(mon)])
      .then(([ab, ms]) => {
        if (!alive) return;
        const ids = new Map<string, number>();
        const moves: CalcMove[] = ms
          .filter((m) => m.type)
          .map((m) => {
            ids.set(m.name, m.move_id);
            return {
              name: m.name,
              type: m.type as string,
              damage_class: m.damage_class ?? "status",
              power: m.power ?? 0,
              target: m.target ?? null,
              priority: m.priority ?? 0,
              accuracy: m.accuracy,
              effect: m.short_effect,
            };
          });
        moves.sort(
          (a, b) =>
            Number(a.power === 0) - Number(b.power === 0) ||
            Number(mon.types.includes(b.type)) - Number(mon.types.includes(a.type)) ||
            b.power - a.power ||
            a.name.localeCompare(b.name),
        );
        setAbilities(ab);
        // Keep a legal chosen ability, else default to the first regular one.
        setAbil((cur) => (cur && ab.some((a) => a.name === cur) ? cur : (ab.find((a) => !a.is_hidden) ?? ab[0])?.name ?? null));
        setLearnset({ moves, ids });
      })
      .catch(() => {
        if (alive) setLearnset({ moves: [], ids: new Map() });
      });
    return () => {
      alive = false;
    };
  }, [mon]);

  const pickMon = (p: PokemonSummary) =>
    loadCalcMon(p.dex_number, p.form_id).then((m) => {
      if (m.id === mon?.id) return;
      setMon(m);
      setAbilities([]);
      setLearnset(null);
      setAbil(null);
      setPicks(MOVE_SLOTS.map(() => null));
      touch();
    });

  const abilOpts: PickOpt[] = useMemo(
    () => [
      ...abilities.map((a) => ({ v: a.name, hint: `${a.is_hidden ? "Hidden · " : ""}${a.short_effect ?? ""}` })),
    ],
    [abilities],
  );
  const natOpts: PickOpt[] = NAT_OPTS;
  const [held, setHeld] = useState<SlotItem[]>([]);
  useEffect(() => {
    let alive = true;
    loadHeldItems().then((xs) => {
      if (!alive) return;
      setHeld(xs);
    });
    return () => {
      alive = false;
    };
  }, []);
  const itemOpts: PickOpt[] = useMemo(
    () => [
      { v: NO_ITEM, hint: "no held item" },
      ...[...(item ? [item] : []), ...held.filter((c) => c.id !== item?.id)].map((x) => ({
        v: x.name,
        hint: itemDesc(x) ?? x.category ?? "",
      })),
    ],
    [item, held],
  );

  const applyPre = (x: string) => {
    setPre(x);
    if (x === "Custom") return;
    const set = x === "Bulky" ? BULKY_SET : offensiveSet(mon);
    setNat(set.nat);
    setEv({ ...set.ev });
    setIv({ ...set.iv });
    touch();
  };

  const setMove = (i: number, name: string | null) => {
    setPicks((p) => p.map((x, j) => (j === i ? name : x)));
    touch();
  };
  const moveInfo = (name: string | null) => (name ? learnset?.moves.find((m) => m.name === name) ?? null : null);

  const save = async () => {
    if (!mon || saving) return;
    setSaving(true);
    setError(null);
    try {
      const known = new Map(member?.moves.map((m) => [m.name, m.move_id]));
      const moveIds = picks
        .filter((n): n is string => !!n)
        .map((n) => learnset?.ids.get(n) ?? known.get(n))
        .filter((id): id is number => id != null);
      const evTotal = KEYS.reduce((s, k) => s + ev[k], 0);
      const team = await setSlot(teamId, slot, {
        // A form is saved as its species + form id.
        pokemon_id: mon.formId != null ? mon.dex : mon.id,
        form_id: mon.formId ?? null,
        ability_id: abilityId(abilities.find((a) => a.name === abil)?.id) ?? (abil === member?.ability?.name ? member.ability.id : null),
        nature_id: natures.find((n) => n.name === nat)?.id ?? null,
        item_id: item?.id ?? null,
        ev_spread: evTotal > 0 ? toTeam(ev) : null,
        iv_spread: toTeam(iv),
        move_ids: moveIds.length ? moveIds : null,
      });
      setDirtyState(false);
      setSaved(true);
      onDirty(false);
      onSaved(team);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };


  const filled = picks.filter(Boolean).length;

  return (
    <div className="se-side">
      <div className="se-scroll">
        <div className="se-panel">
          <div className="dc-ph">
            <DcPicker mon={mon} onPick={pickMon} ph={mon ? "Change Pokémon…" : `Pick a Pokémon for slot ${slot}…`} />
          </div>

          {mon && (
            <div className="dc-c2">
              {/* left: what it does — moves, ability, nature */}
              <div className="l">
                <span className="dc-k">Moves · {filled}/4</span>
                <div className="se-moves">
                  {MOVE_SLOTS.map((i) => {
                    const m = moveInfo(picks[i]);
                    const taken = new Set(picks.filter((p, j) => p && j !== i));
                    const meta = m
                      ? `${m.damage_class === "status" ? "status" : `${m.damage_class} ${m.power}`}${m.accuracy ? ` · ${m.accuracy}%` : ""}${m.priority ? ` · ${m.priority > 0 ? "+" : ""}${m.priority}` : ""}`
                      : undefined;
                    return (
                      // Same compact card as ability/nature/item; the search opens *over* it.
                      <div key={i} className={`se-info se-mv${editing === `m${i}` ? " editing" : ""}${i % 2 ? " r" : ""}`}>
                        {picks[i] ? (
                          <>
                            <button
                              className="se-ibox"
                              onClick={() => setEditing(`m${i}`)}
                              aria-label={`Move ${i + 1}: ${picks[i]}${m?.effect ? `. ${m.effect}` : ""} — change`}
                            >
                              <span className="k">
                                <i style={{ background: TYPE_HEX[m?.type ?? ""] ?? "var(--line)" }} />
                                {m?.type ?? "move"}
                              </span>
                              <span className="nm">{picks[i]}</span>
                              {meta && <span className="mt">{meta}</span>}
                            </button>
                            {m && (
                              <div className="se-itip" aria-hidden>
                                <span className="nm">
                                  {m.name}
                                  <em>
                                    {m.type} · {meta}
                                  </em>
                                </span>
                                {m.effect && <span className="fx">{m.effect}</span>}
                              </div>
                            )}
                            <button className="se-mclr" onClick={() => setMove(i, null)} aria-label={`Remove ${picks[i]}`} title="Remove move">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
                                <path d="M6 6l12 12M18 6L6 18" />
                              </svg>
                            </button>
                          </>
                        ) : (
                          <button className="se-ibox empty" onClick={() => setEditing(`m${i}`)}>
                            <span className="k">Move {i + 1}</span>
                            <span className="nm">+ Add move</span>
                          </button>
                        )}
                        {editing === `m${i}` && (
                          <div className="se-msearch">
                            <MoveSearch
                              moves={learnset ? learnset.moves.filter((x) => !taken.has(x.name)) : []}
                              value={picks[i]}
                              onPick={(x) => setMove(i, x.name)}
                              onDone={() => setEditing(null)}
                              autoFocus
                              owner={mon.name}
                              placeholder={`Search ${mon.name}'s moves…`}
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="se-infos">
                  <InfoBox
                    label="Ability"
                    name={abil ?? "Loading…"}
                    meta={abilities.find((a) => a.name === abil)?.is_hidden ? "hidden" : undefined}
                    desc={abilityDesc(abilities.find((a) => a.name === abil))}
                    editing={editing === "ability"}
                    onOpen={() => setEditing("ability")}
                  >
                    <PickSearch
                      bare
                      autoFocus
                      label="Ability"
                      value={abil ?? ""}
                      opts={abilOpts}
                      onPick={(v) => {
                        setAbil(v);
                        touch();
                      }}
                      onDone={() => setEditing(null)}
                    />
                  </InfoBox>
                  <InfoBox
                    label="Nature"
                    name={nat}
                    meta={natTag(nat)}
                    desc={natDesc(nat)}
                    editing={editing === "nature"}
                    onOpen={() => setEditing("nature")}
                  >
                    <PickSearch
                      bare
                      autoFocus
                      label="Nature"
                      value={nat}
                      opts={natOpts}
                      onPick={(v) => {
                        setNat(v);
                        setPre("Custom");
                        touch();
                      }}
                      onDone={() => setEditing(null)}
                    />
                  </InfoBox>
                  <InfoBox
                    label="Item"
                    name={item?.name ?? NO_ITEM}
                    meta={itemMeta(item)}
                    desc={itemDesc(item)}
                    editing={editing === "item"}
                    onOpen={() => setEditing("item")}
                  >
                    <PickSearch
                      bare
                      autoFocus
                      label="Item"
                      value={item?.name ?? NO_ITEM}
                      opts={itemOpts}
                      onPick={(v) => {
                        setItem(v === NO_ITEM ? null : held.find((c) => c.name === v) ?? item);
                        touch();
                      }}
                      onDone={() => setEditing(null)}
                    />
                  </InfoBox>
                </div>
              </div>

              {/* right: the stats it has */}
              <div className="r">
                <div className="dc-sth">
                  <span className="dc-k">Stats · Lv{LEVEL}</span>
                  <span className="dc-seg">
                    {["Offensive", "Bulky", "Custom"].map((x) => (
                      <button key={x} className={pre === x ? "on" : ""} onClick={() => applyPre(x)}>
                        {x}
                      </button>
                    ))}
                  </span>
                </div>
                <EvEditor
                  mon={mon}
                  level={LEVEL}
                  nat={nat}
                  ev={ev}
                  iv={iv}
                  onEv={(e) => {
                    setEv(e);
                    setPre("Custom");
                    touch();
                  }}
                  onIv={(v) => {
                    setIv(v);
                    setPre("Custom");
                    touch();
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="se-foot">
        <span className="se-meta">
          {error ? <span className="err">{error}</span> : saved ? "Saved to team" : dirty ? "Unsaved changes" : ""}
        </span>
        <button className="se-btn ghost" onClick={onClose}>
          {dirty ? "Cancel" : "Done"}
        </button>
        <button className="se-btn primary" onClick={save} disabled={!mon || saving || (!dirty && !!member)}>
          {saving ? "Saving…" : member && !dirty ? "Saved" : member ? "Save changes" : "Add to team"}
        </button>
      </div>
    </div>
  );
}

// Item text from the dataset reads "Held: …" under a "Held items" category — both redundant here.
const itemDesc = (i: SlotItem | null) => i?.short_effect?.replace(/^Held:\s*/i, "") ?? undefined;
const itemMeta = (i: SlotItem | null) => (i?.category && !/^held items$/i.test(i.category) ? i.category.toLowerCase() : undefined);
const abilityDesc = (a: Ability | undefined) => a?.short_effect ?? a?.effect ?? undefined;


/** A usable ability id — forms can list abilities the dataset has no id for (-1). */
const abilityId = (id: number | undefined) => (id != null && id > 0 ? id : null);

