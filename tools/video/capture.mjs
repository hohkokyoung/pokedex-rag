// Captures the promo's stills from the running app at 3× into build/assets/.
// Asks one question ("Fastest non-legendary Fire types"): uses at most one LLM
// call when a key is set, none when the answer is cached or keyless.
import { copyFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { APP, ASSETS, HERE, ROOT, HIDE_DEV_BADGE, api, ensureDir, launch, showcaseTeam } from './lib.mjs';

ensureDir(ASSETS);
const out = (n) => join(ASSETS, n);
const b = await launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 3 });
await ctx.addInitScript(HIDE_DEV_BADGE);
const p = await ctx.newPage();
const wait = (ms) => p.waitForTimeout(ms);

// Fixed chrome (site nav, scroll progress bar, the Pokédex floating bar) would
// overlap element shots, so each shot hides it first.
async function shot(selector, name) {
  await p.addStyleTag({ content: '.site-nav,.scroll-progress,.pk-float{visibility:hidden!important}' });
  const l = p.locator(selector).first();
  await l.evaluate((e) => e.scrollIntoView({ block: 'center' }));
  await wait(1500); // let reveal animations finish
  await l.screenshot({ path: out(name + '.png') });
  console.log('captured', name);
}

// Home dashboard cards.
await p.goto(APP + '/', { waitUntil: 'networkidle' }); await wait(2000);
await p.getByRole('button', { name: 'dragon', exact: true }).first().click();
await p.getByRole('button', { name: 'ground', exact: true }).first().click();
for (const [s, n] of [['.ga-tc section', 'typecalc'], ['.ga-dc section', 'damage'], ['.ga-cr section', 'catch'], ['.ga-nat section', 'nature']]) await shot(s, n);

// Pokédex cards (the first page of the catalog is loaded without scrolling far).
await p.goto(APP + '/pokedex', { waitUntil: 'networkidle' }); await wait(1500);
for (const d of [1, 4, 7, 25, 6, 9, 65, 59]) await shot(`a[href="/pokedex/${d}"]`, 'card' + d);

// Ask: the answer tile and the ranking tile.
await p.goto(APP + '/ask', { waitUntil: 'networkidle' }); await wait(1000);
await p.getByPlaceholder(/Ask anything/).fill('Fastest non-legendary Fire types');
await p.keyboard.press('Enter');
const tiles = p.locator('main section, main article');
await tiles.nth(1).waitFor({ timeout: 60_000 }); await wait(2500);
for (const i of [0, 1]) { await tiles.nth(i).screenshot({ path: out(`asktile${i}.png`) }); console.log('captured asktile' + i); }

// Team rating panel and the team's artwork.
const team = await showcaseTeam();
await p.goto(`${APP}/teams/${team.id}`, { waitUntil: 'networkidle' }); await wait(1500);
await shot('section.panel.tr', 'rating');
for (const [i, src] of team.sprites.slice(0, 6).entries()) writeFileSync(out(`team${i}.png`), Buffer.from(await (await api(src)).arrayBuffer()));
writeFileSync(out('team.json'), JSON.stringify({ name: team.name, count: Math.min(team.sprites.length, 6) }));

// Garchomp's artwork and the brand mark come from disk.
copyFileSync(join(ROOT, 'data/sprites/official-artwork/445.png'), out('art445.png'));
copyFileSync(join(ROOT, 'frontend/public/brand/pokedex-os-symbol.svg'), out('logo.svg'));
copyFileSync(join(HERE, 'node_modules/gsap/dist/gsap.min.js'), out('gsap.min.js'));
console.log(`team: ${team.name} (#${team.id})`);
await b.close();
