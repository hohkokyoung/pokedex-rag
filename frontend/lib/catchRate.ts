// Catch-rate display helpers. The odds are computed by the backend
// (GET /api/pokemon/{id}/catch, services/catch_rate.py); this file only holds the
// situation's shape, its defaults, the balls' colours and the % formatter.

export type Status = "none" | "sleep" | "freeze" | "paralysis" | "burn" | "poison";

export type CatchCtx = {
  hpPct: number;          // 1–100 of current HP
  level: number;          // wild level
  myLevel: number;        // your lead's level (Level Ball)
  turn: number;           // battle turn, 1 = first throw
  status: Status;
  night: boolean;         // night or cave (Dusk Ball)
  water: boolean;         // fishing / surfing / underwater (Dive, Lure)
  caught: boolean;        // species already registered as caught (Repeat Ball)
  loveMatch: boolean;     // your lead: same species, opposite gender (Love Ball)
  dexCaught: number;      // # species caught (critical capture)
  charm: boolean;         // Catching Charm
};

export const DEFAULT_CTX: CatchCtx = {
  hpPct: 100, level: 30, myLevel: 30, turn: 1, status: "none", night: false, water: false,
  caught: false, loveMatch: false, dexCaught: 0, charm: false,
};

/** How each ball is drawn (no ball sprites in the dataset), by the backend's ball id. */
export type BallLook = { top: string; band?: string; accent?: string };
export const BALL_LOOK: Record<string, BallLook> = {
  poke: { top: "#e3350d" },
  great: { top: "#2f6bff", accent: "#e3350d" },
  ultra: { top: "#22252b", accent: "#f5c400" },
  master: { top: "#7b3fc4", accent: "#e44fa3" },
  quick: { top: "#2f8fe0", accent: "#f5c400" },
  dusk: { top: "#1f5a3a", accent: "#e3350d" },
  timer: { top: "#f4f4f4", band: "#e3350d", accent: "#22252b" },
  net: { top: "#2fb7a8", accent: "#22252b" },
  nest: { top: "#7cbf3a", accent: "#e7b33a" },
  repeat: { top: "#e8a21a", accent: "#e3350d" },
  dive: { top: "#3a8fe0", accent: "#9fd6ff" },
  lure: { top: "#2fa8a0", accent: "#e3350d" },
  fast: { top: "#f08a1a", accent: "#f5d400" },
  level: { top: "#e8a21a", accent: "#e3350d" },
  heavy: { top: "#8a94a3", accent: "#2f6bff" },
  moon: { top: "#2b3a6b", accent: "#f5d400" },
  love: { top: "#f06aa8", accent: "#ffffff" },
  dream: { top: "#f29ac4", accent: "#8b5cf6" },
  beast: { top: "#2f6bff", accent: "#f5d400" },
  premier: { top: "#f4f4f4", band: "#e3350d" },
};

export const pct = (p: number) => (p >= 1 ? "100" : p >= 0.995 ? ">99" : p < 0.001 ? "<0.1" : (p * 100).toFixed(p < 0.1 ? 1 : 0));
