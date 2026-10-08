"use client";

import type { FailureKind } from "@/lib/api";

const COPY: Record<Exclude<FailureKind, "not-found">, { title: string; body: string }> = {
  offline: {
    title: "Can't reach the pokérag server",
    body: "Nothing could load. Check the backend is running (make up), then try again.",
  },
  server: {
    title: "The server couldn't load this",
    body: "It answered with an error. Try again; if it keeps failing, check the backend logs.",
  },
};

/**
 * Shown in place of data when a request fails, so an outage never reads as
 * "no results", "no teams" or "not found". `compact` fits inside a home tile.
 */
export default function ServerNote({
  kind,
  onRetry,
  what,
  compact = false,
}: {
  kind: Exclude<FailureKind, "not-found">;
  onRetry?: () => void;
  /** What failed to load, e.g. "your teams"; replaces "this"/"Nothing". */
  what?: string;
  compact?: boolean;
}) {
  const c = COPY[kind];
  const body = what
    ? kind === "offline"
      ? `Couldn't load ${what}. Check the backend is running (make up), then try again.`
      : `Loading ${what} returned an error. Try again; if it keeps failing, check the backend logs.`
    : c.body;
  return (
    <div className={`srv-note${compact ? " srv-note--compact" : ""}`} role="status">
      <div className="srv-note__txt">
        <p className="srv-note__title">{c.title}</p>
        <p className="srv-note__body">{body}</p>
      </div>
      {onRetry && (
        <button type="button" className="srv-note__retry" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
