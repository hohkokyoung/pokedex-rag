"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { assetUrl, getProfile, updatePreferredTypes, type Profile } from "@/lib/api";
import { TYPE_ORDER, titleCase, typeColor } from "@/lib/pokeTypes";

/**
 * The composer's footer on /ask: a compact "personalised" chip (favourite
 * sprites + counts) that opens the profile editor in place. `meta` sits on the
 * right of the row (provider line).
 */
export default function ProfilePanel({ meta }: { meta?: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(() => setProfile({ preferred_types: [], favorites: [] }));
  }, []);

  async function toggleType(t: string) {
    if (!profile) return;
    const next = profile.preferred_types.includes(t)
      ? profile.preferred_types.filter((x) => x !== t)
      : [...profile.preferred_types, t];
    setProfile({ ...profile, preferred_types: next }); // optimistic
    try {
      setProfile(await updatePreferredTypes(next));
    } catch {
      /* keep optimistic state */
    }
  }

  const types = profile?.preferred_types.length ?? 0;
  const favs = profile?.favorites ?? [];
  const summary =
    types + favs.length === 0
      ? "Personalise answers"
      : [types && `${types} type${types > 1 ? "s" : ""}`, favs.length && `${favs.length} favourite${favs.length > 1 ? "s" : ""}`]
          .filter(Boolean)
          .join(" · ");

  return (
    <div className="ax-foot">
      <div className="ax-foot__row">
        {profile && (
          <button
            type="button"
            className={`ax-profile ${open ? "is-open" : ""}`}
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
          >
            {favs.length > 0 && (
              <span className="ax-profile__dots" aria-hidden>
                {favs.slice(0, 3).map((f) => (
                  <img key={f.id} src={assetUrl(f.sprite_url)} alt="" />
                ))}
              </span>
            )}
            <span>{summary}</span>
            <svg className="ax-profile__chev" width="10" height="10" viewBox="0 0 10 10" aria-hidden>
              <path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        )}
        {meta && <span className="ax-foot__meta">{meta}</span>}
      </div>

      {open && profile && (
        <div className="ax-drawer">
          <div className="ax-drawer__lbl">Preferred types</div>
          <div className="pk-types" style={{ marginTop: 0 }}>
            {TYPE_ORDER.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => toggleType(t)}
                className={profile.preferred_types.includes(t) ? "on" : ""}
                style={{ "--tc": typeColor(t) } as React.CSSProperties}
              >
                {titleCase(t)}
              </button>
            ))}
          </div>

          <div className="ax-drawer__lbl" style={{ marginTop: 18 }}>Favourites</div>
          {favs.length === 0 ? (
            <p className="ax-drawer__hint">
              Add favourites from any Pokémon’s page, then ask “which Pokémon would I like?”.
            </p>
          ) : (
            <div className="ax-drawer__favs">
              {favs.map((f) => (
                <Link key={f.id} href={`/pokedex/${f.dex_number}`} className="ax-fav">
                  <img src={assetUrl(f.sprite_url)} alt="" />
                  {titleCase(f.name)}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
