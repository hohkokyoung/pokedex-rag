// Records the two-minute screen tour → docs/media/pokerag-tour.mp4 (1080p, 30 fps).
// Frames come from the browser's own screencast (JPEG q92 at native resolution),
// not Playwright's recordVideo, whose low bitrate blurs UI text. Needs ffmpeg.
// Asks two questions on /ask and one on the home tile: up to ~3 LLM calls when a
// key is set and the answers aren't cached; none keyless.
import { execFileSync } from 'node:child_process';
import { rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { APP, BUILD, MEDIA, HIDE_DEV_BADGE, ensureDir, launch, showcaseTeam } from './lib.mjs';

const team = await showcaseTeam();
const dir = join(BUILD, 'tour'); rmSync(dir, { recursive: true, force: true }); ensureDir(dir);
const b = await launch();
const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 } });
await ctx.addInitScript(HIDE_DEV_BADGE);
// A visible cursor: a red ring that follows the mouse and shrinks on click.
await ctx.addInitScript(() => {
  const css = document.createElement('style');
  css.textContent = `#tourcur{position:fixed;z-index:2147483647;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;
  background:rgba(220,40,30,.35);border:2px solid rgba(220,40,30,.85);pointer-events:none;transition:transform .12s}
  #tourcur.down{transform:scale(.7)}`;
  const c = document.createElement('div'); c.id = 'tourcur';
  const add = () => { document.head.appendChild(css); document.body.appendChild(c); };
  document.readyState === 'loading' ? addEventListener('DOMContentLoaded', add) : add();
  addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => c.classList.add('down'), true);
  addEventListener('mouseup', () => c.classList.remove('down'), true);
});
const p = await ctx.newPage();

// Screencast frames arrive only when the screen changes; each one's timestamp sets
// how long it's shown, so pauses keep their real length.
const cdp = await ctx.newCDPSession(p);
const frames = [];
cdp.on('Page.screencastFrame', async (f) => {
  const file = join(dir, `${String(frames.length).padStart(6, '0')}.jpg`);
  writeFileSync(file, Buffer.from(f.data, 'base64'));
  frames.push([file, f.metadata.timestamp]);
  try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch { /* page navigating */ }
});

const wait = (ms) => p.waitForTimeout(ms);
async function click(loc) {
  await loc.scrollIntoViewIfNeeded();
  const bb = await loc.boundingBox();
  await p.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2, { steps: 25 }); await wait(200);
  await loc.click();
}
async function scroll(px, step = 120, pause = 60) {
  for (let s = 0; s < Math.abs(px); s += step) { await p.mouse.wheel(0, Math.sign(px) * step); await wait(pause); }
}
async function type(loc, text) { await click(loc); await loc.pressSequentially(text, { delay: 70 }); }
// A step that fails (UI changed) is logged and skipped, so one broken selector
// doesn't lose the whole recording. Check the log after a run.
async function step(name, fn) { try { await fn(); } catch (e) { console.log('step failed:', name, e.message.split('\n')[0]); } }
const typeBtn = (t) => p.getByRole('button', { name: t, exact: true }).first();

// 1. Home
await p.goto(APP + '/', { waitUntil: 'networkidle' });
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, everyNthFrame: 1 });
await wait(2500);
await step('search', async () => {
  await type(p.getByPlaceholder(/Search any of/), 'gar'); await wait(1500);
  await p.keyboard.press('Escape'); await p.getByPlaceholder(/Search any of/).fill(''); await wait(400);
});
await step('team arrows', async () => {
  await click(p.getByRole('button', { name: 'Next team' })); await wait(1500);
  await click(p.getByRole('button', { name: 'Previous team' })); await wait(1000);
});
await step('type calc', async () => {
  await click(typeBtn('fire')); await wait(600);
  await click(typeBtn('dragon')); await wait(900);
  await click(typeBtn('ground')); await wait(1500);
});
await step('ask tile', async () => {
  await scroll(-2000, 300, 20); await wait(500);
  await click(p.getByRole('button', { name: /Matchup/ }).first()); await wait(6000);
});
await step('lookup', async () => { await type(p.getByPlaceholder(/e\.g\. Earthquake/), 'Leftovers'); await wait(1800); });
await step('scroll home', async () => { await scroll(900); await wait(1500); await scroll(-900); await wait(800); });

// 2. Pokédex: catalog, a type filter, search, then Garchomp's page
await step('pokedex', async () => {
  await click(p.locator('a[href="/pokedex"]').first()); await wait(2500);
  await scroll(1400, 100, 70); await wait(800); await scroll(-1400, 300, 20); await wait(500);
  await click(typeBtn('dragon')); await wait(2000);
  await scroll(500); await wait(800); await scroll(-500, 250, 20);
  await click(typeBtn('dragon')); await wait(600);
  await type(p.getByPlaceholder(/Search by name/), 'garchomp'); await wait(2000);
  await click(p.locator('a[href*="/pokedex/445"]').first()); await wait(3500);
});
await step('detail scroll', async () => { await scroll(3000, 100, 90); await wait(1200); });

// 3. Ask: a ranking, then a learnset check
await step('ask', async () => {
  await p.mouse.wheel(0, -5000); await wait(600);
  await click(p.locator('a[href="/ask"]').first()); await wait(2000);
  await type(p.getByPlaceholder(/Ask anything/), 'Fastest non-legendary Fire types');
  await p.keyboard.press('Enter'); await wait(9000);
  await scroll(700); await wait(2000); await scroll(-700, 200, 30);
  const box = p.getByPlaceholder(/Ask anything/); await box.fill('');
  await type(box, 'Can Pikachu learn Surf in Scarlet?'); await p.keyboard.press('Enter'); await wait(8000);
});

// 4. Teams: the list, then the fullest team's page
await step('teams', async () => {
  await click(p.locator('a[href="/teams"]').first()); await wait(2500);
  await scroll(600); await wait(1200); await scroll(-600, 200, 30);
  await p.goto(`${APP}/teams/${team.id}`, { waitUntil: 'networkidle' }); await wait(2500);
  await scroll(1800, 100, 90); await wait(1500);
});
await step('home again', async () => {
  await p.mouse.wheel(0, -5000); await wait(600);
  await click(p.locator('a[href="/"]').nth(1)); await wait(2500);
});
await wait(500);
await cdp.send('Page.stopScreencast');
const end = Date.now() / 1000;
await ctx.close(); await b.close();

// ffmpeg concat list: each frame held until the next one arrived.
const list = join(dir, 'list.txt');
writeFileSync(list, frames.map(([f, t], i) => `file '${f}'\nduration ${((frames[i + 1]?.[1] ?? end) - t).toFixed(4)}`).join('\n')
  + `\nfile '${frames.at(-1)[0]}'\n`);
const out = join(MEDIA, 'pokerag-tour.mp4');
execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list,
  '-vf', 'fps=30,scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '23',
  '-movflags', '+faststart', out], { stdio: 'inherit' });
console.log(`wrote ${out} from ${frames.length} frames (team: ${team.name})`);
