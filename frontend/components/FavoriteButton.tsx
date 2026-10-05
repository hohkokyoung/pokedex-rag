"use client";

import { useEffect, useState } from "react";
import { addFavorite, getProfile, removeFavorite } from "@/lib/api";

export default function FavoriteButton({ pokemonId }: { pokemonId: number }) {
  const [fav, setFav] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [pop, setPop] = useState(false);

  useEffect(() => {
    let active = true;
    getProfile()
      .then((p) => active && setFav(p.favorites.some((f) => f.id === pokemonId)))
      .catch(() => active && setFav(false));
    return () => {
      active = false;
    };
  }, [pokemonId]);

  async function toggle() {
    if (fav === null || busy) return;
    setBusy(true);
    const next = !fav;
    setFav(next); // optimistic
    if (next) {
      setPop(true);
      setTimeout(() => setPop(false), 260);
    }
    try {
      if (next) await addFavorite(pokemonId);
      else await removeFavorite(pokemonId);
    } catch {
      setFav(!next); // revert
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={toggle}
      className={`fav-btn ${fav ? "is-fav" : ""} ${pop ? "is-pop" : ""}`}
      aria-pressed={!!fav}
      aria-label={fav ? "Remove from favourites" : "Add to favourites"}
      disabled={fav === null}
      title={fav ? "In your favourites" : "Add to favourites"}
    >
      <span aria-hidden>{fav ? "♥" : "♡"}</span>
    </button>
  );
}
