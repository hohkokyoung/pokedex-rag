// Records the promo's live clips into build/clips/ (see slowclock.mjs), and copies the
// promo's other assets into build/assets/. The iOS app screen comes from capture-app.mjs.
// Asks one question ("Fastest non-legendary Fire types"): one LLM call at most when a key
// is set and the answer isn't cached, none keyless.
//   node capture.mjs            all clips
//   node capture.mjs ask team   just those
import { copyFileSync } from 'node:fs';
import { join } from 'node:path';
import { ASSETS, HERE, ROOT, ensureDir, showcaseTeam } from './lib.mjs';
import { open } from './slowclock.mjs';

const only = process.argv.slice(2);
const want = (n) => !only.length || only.includes(n);
const typeBtn = (c, t) => c.getByRole('button', { name: t, exact: true }).first();

// Ask: type the question, click Ask, let the answer and its ranking land.
if (want('ask')) {
  const s = await open(1280, 1000); await s.go('/ask'); await s.wait(300); const { p } = s;
  s.at = [1100, 760];
  s.start('ask'); await s.wait(250);
  await s.clickLoc(p.getByPlaceholder(/Ask anything/), 600, -330, 0); s.mark('focus');
  await s.moveTo(900, 470, 350);
  s.mark('type0'); await s.type('Fastest non-legendary Fire types', 40); s.mark('type1');
  await s.wait(180);
  await s.clickLoc(p.getByRole('button', { name: 'Ask', exact: true }).last(), 420); s.mark('askclick');
  await s.moveTo(1180, 960, 900);
  await s.wait(3200); await s.stop();
}

// Pokédex: the Dragon filter swaps the catalog.
if (want('dex')) {
  const s = await open(1440, 900); await s.go('/pokedex'); await s.wait(400); const { p } = s;
  s.at = [1250, 700];
  s.start('dex'); await s.wait(250);
  await s.clickLoc(typeBtn(p, 'dragon'), 650); s.mark('dragon');
  await s.wait(2000); await s.stop();
}

// Gabite → Garchomp (next), then the Mega form. The form morph is heavy to paint, so this
// page runs on a slower clock.
if (want('detail')) {
  const s = await open(1440, 1350, 0.02); await s.go('/pokedex/444'); await s.wait(500); const { p } = s;
  s.at = [1250, 300];
  s.start('detail'); await s.wait(250);
  await s.clickLoc(p.getByRole('link', { name: /#0445/ }).first(), 550); s.mark('next');
  await s.wait(1700);
  await s.clickLoc(p.getByRole('tab', { name: /^Mega/ }).first(), 750); s.mark('mega');
  await s.moveTo(900, 760, 600);
  await s.wait(1600); await s.stop();
}

// The fullest team's page, scrolled to its rating (eased, set before every shot).
if (want('team')) {
  const team = await showcaseTeam();
  const s = await open(1440, 900); await s.go(`/teams/${team.id}`); await s.wait(600); const { p } = s;
  s.at = [1300, 520];
  const [y0, y1, t0] = await p.evaluate(() => {
    document.documentElement.style.scrollBehavior = 'auto';
    const r = document.querySelector('section.panel.tr').getBoundingClientRect();
    return [scrollY, scrollY + r.top - 207, performance.now()];
  });
  s.start('team'); await s.wait(300); s.mark('scroll');
  const t1 = t0 + 300;
  s.beforeShot = () => p.evaluate(([y0, y1, t1]) => {
    const u = Math.min(1, Math.max(0, (performance.now() - t1) / 1400));
    window.scrollTo(0, y0 + (y1 - y0) * (1 - Math.pow(1 - u, 4)));
  }, [y0, y1, t1]);
  await s.wait(3600); await s.stop();
}

// Home: the type calculator and the damage calculator, at 1920 wide (narrower layouts
// truncate the calc's roster names). The nav is hidden so it can't cover the card.
for (const [name, sel, vh, act] of [
  ['types', '.ga-tc section', 900, async (s, c) => {
    await s.clickLoc(typeBtn(c, 'fire'), 600); s.mark('fire'); await s.wait(380);
    await s.clickLoc(typeBtn(c, 'dragon'), 550); s.mark('dragon'); await s.wait(520);
    await s.clickLoc(typeBtn(c, 'ground'), 450); s.mark('ground'); await s.wait(1600);
  }],
  ['calc', '.ga-dc section', 1100, async (s, c) => {
    await s.clickLoc(c.getByRole('button', { name: 'Bulky', exact: true }), 650); s.mark('bulky'); await s.wait(1300);
    await s.clickLoc(c.getByRole('button', { name: 'Offensive', exact: true }), 500); s.mark('offensive'); await s.wait(1300);
  }],
]) {
  if (!want(name)) continue;
  const s = await open(1920, vh); await s.go('/'); await s.wait(600); const { p } = s;
  await p.addStyleTag({ content: '.site-nav{visibility:hidden!important} body{padding-bottom:700px!important}' });
  const c = p.locator(sel).first();
  await c.evaluate((e, nm) => { const r = e.getBoundingClientRect(); window.scrollTo(0, scrollY + r.top - (nm === 'types' ? 60 : (innerHeight - r.height) / 2)); }, name);
  await s.wait(900);
  const r = await c.evaluate(e => { const r = e.getBoundingClientRect(); return [r.x + r.width * .85, r.y + r.height * .9]; });
  s.at = r;
  s.start(name); await s.wait(250);
  await act(s, c);
  await s.stop();
}

ensureDir(ASSETS);
copyFileSync(join(ROOT, 'frontend/public/brand/pokedex-os-symbol.svg'), join(ASSETS, 'logo.svg'));
copyFileSync(join(HERE, 'node_modules/gsap/dist/gsap.min.js'), join(ASSETS, 'gsap.min.js'));
