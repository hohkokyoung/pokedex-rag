// Shared setup for the video scripts: where the app runs, where files go, and
// how to launch Chromium. See docs/guides/media.md.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const HERE = dirname(fileURLToPath(import.meta.url));
export const ROOT = join(HERE, '..', '..');
export const BUILD = join(HERE, 'build');
export const ASSETS = join(BUILD, 'assets');
export const MEDIA = join(ROOT, 'docs', 'media');

// The running stack (make up). Ports follow .env; the Makefile passes them in.
export const APP = process.env.APP_URL ?? 'http://localhost:3000';
export const API = process.env.API_URL ?? 'http://localhost:8000';

export function ensureDir(d) { mkdirSync(d, { recursive: true }); return d; }

// Playwright's own Chromium (`npx playwright install chromium`), or any Chrome via CHROME.
export function launch() {
  return chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
}

// Hides the Next.js dev badge in every page, before the app's own styles load.
export const HIDE_DEV_BADGE = () => {
  addEventListener('DOMContentLoaded', () => {
    const s = document.createElement('style');
    s.textContent = 'nextjs-portal{display:none!important}';
    document.head.appendChild(s);
  });
};

export async function api(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(`${API}${path} → ${r.status}. Is the backend up (make up), and API_URL right?`);
  return r;
}

// The fullest saved team: the team the promo and the tour show.
export async function showcaseTeam() {
  const { teams } = await (await api('/api/teams')).json();
  const team = [...teams].sort((a, b) => b.size - a.size)[0];
  if (!team?.size) throw new Error('No saved team with members — build one on /teams first.');
  return team;
}
