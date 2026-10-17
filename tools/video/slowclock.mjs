// Records live-app clips that are both sharp (2×) and smooth (60 fps). See docs/guides/media.md.
//
// CDP's screencast is always 1×, so frames are 2× screenshots instead. Those take ~80 ms each,
// too slow for real time, so the page runs on a slowed clock: JS time, timers, rAF and CSS/Web
// animations all run at K× speed. Screenshots are taken back to back and stamped with page
// time, then resampled to 60 fps by picking the nearest shot (not ffmpeg's concat demuxer,
// which rounds each image's timestamp to 40 ms and quietly makes clips 25 fps).
//
// Input and screenshots share one lane, or the capture loop starves input. Back-to-back
// screenshots also starve the page's rAF, so JS-driven motion (a scroll) is set before each
// shot with `beforeShot` instead.
import { linkSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { APP, BUILD, launch } from './lib.mjs';

export const K = Number(process.env.K ?? 0.05);
export const FPS = 60;
export const CLIPS = join(BUILD, 'clips');

const INIT = (k) => {
  const rn = performance.now.bind(performance), t0 = rn(), dn = Date.now, d0 = dn();
  performance.now = () => t0 + (rn() - t0) * k;
  const OD = Date;
  // eslint-disable-next-line no-global-assign
  Date = class extends OD { constructor(...a) { a.length ? super(...a) : super(Date.now()); } static now() { return d0 + (dn() - d0) * k; } };
  const st = setTimeout, si = setInterval, raf = requestAnimationFrame;
  window.setTimeout = (f, ms = 0, ...a) => st(f, ms / k, ...a);
  window.setInterval = (f, ms = 0, ...a) => si(f, ms / k, ...a);
  window.requestAnimationFrame = (cb) => raf(() => cb(performance.now()));
  addEventListener('DOMContentLoaded', () => {
    const s = document.createElement('style');
    s.textContent = 'nextjs-portal{display:none!important} .scroll-progress{display:none!important}';
    document.head.appendChild(s);
    // A visible pointer, drawn into the page.
    const c = document.createElement('div');
    c.innerHTML = '<svg width="26" height="32" viewBox="0 0 26 32"><path d="M2 2 L2 25 L8 19.5 L12.5 29.5 L16.5 27.8 L12.2 18 L20.5 18 Z" fill="#14171d" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>';
    c.style.cssText = 'position:fixed;left:-80px;top:-80px;z-index:2147483647;pointer-events:none;transform-origin:2px 2px;filter:drop-shadow(0 3px 5px rgba(0,0,0,.25))';
    document.body.appendChild(c);
    addEventListener('mousemove', e => { c.style.left = e.clientX - 2 + 'px'; c.style.top = e.clientY - 2 + 'px'; }, true);
    addEventListener('mousedown', () => { c.style.transform = 'scale(.85)'; }, true);
    addEventListener('mouseup', () => { c.style.transform = ''; }, true);
  });
};
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

// A browser page on a clock slowed to k× (heavier pages need a smaller k). Waits are page ms.
export async function open(vw, vh, k = K) {
  const b = await launch();
  const ctx = await b.newContext({ viewport: { width: vw, height: vh } });
  await ctx.addInitScript(INIT, k);
  const p = await ctx.newPage();
  const cdp = await ctx.newCDPSession(p);
  // Playwright's own DPR doesn't reach raw CDP screenshots; this does.
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: vw, height: vh, deviceScaleFactor: 2, mobile: false });
  await cdp.send('Animation.enable');
  const s = { b, p, cdp, at: [vw * .8, vh * .8], beforeShot: null };
  let lane = Promise.resolve();
  s.excl = (fn) => { const r = lane.then(fn); lane = r.catch(() => {}); return r; };
  const input = (m, a) => s.excl(async () => { await cdp.send(m, a); await p.evaluate(() => 0); });
  s.go = async (url) => { await p.goto(APP + url, { waitUntil: 'networkidle' }); await cdp.send('Animation.setPlaybackRate', { playbackRate: k }); };
  s.wait = (ms) => new Promise(r => setTimeout(r, ms / k));
  s.mouse = (type, extra = {}) => input('Input.dispatchMouseEvent', { type, x: s.at[0], y: s.at[1], button: type === 'mouseMoved' ? 'none' : 'left', clickCount: type === 'mouseMoved' ? 0 : 1, ...extra });
  s.moveTo = async (x, y, ms = 500) => {
    const [x0, y0] = s.at, n = Math.max(2, Math.round(ms / 16));
    for (let i = 1; i <= n; i++) { const t = ease(i / n); s.at = [x0 + (x - x0) * t, y0 + (y - y0) * t]; await s.mouse('mouseMoved'); await s.wait(ms / n); }
  };
  s.click = async () => { await s.mouse('mousePressed'); await s.wait(90); await s.mouse('mouseReleased'); };
  s.clickLoc = async (loc, ms = 550, dx = 0, dy = 0) => { const bb = await loc.boundingBox(); await s.moveTo(bb.x + bb.width / 2 + dx, bb.y + bb.height / 2 + dy, ms); await s.wait(120); await s.click(); };
  s.type = async (text, every = 45) => { for (const ch of text) { await input('Input.insertText', { text: ch }); await s.wait(every); } };

  // Capture runs in the background from start() to stop(); mark() stamps an action's page time.
  s.start = (name) => {
    s.name = name; s.raw = join(CLIPS, `${name}-raw`); rmSync(s.raw, { recursive: true, force: true }); mkdirSync(s.raw, { recursive: true });
    s.shots = []; s.marks = {}; s.rec = true; s.t0 = Date.now();
    s.loop = (async () => {
      while (s.rec) {
        const a = Date.now();
        const { data } = await s.excl(async () => { if (s.beforeShot) await s.beforeShot(); return cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 92 }); });
        const f = join(s.raw, `${String(s.shots.length).padStart(6, '0')}.jpg`);
        writeFileSync(f, Buffer.from(data, 'base64'));
        s.shots.push([f, ((a + Date.now()) / 2 - s.t0) * k / 1000]);
      }
    })();
  };
  s.mark = (name) => { s.marks[name] = +(((Date.now() - s.t0) * k) / 1000).toFixed(3); };
  s.stop = async () => {
    s.rec = false; await s.loop; await b.close();
    const out = join(CLIPS, s.name); rmSync(out, { recursive: true, force: true }); mkdirSync(out);
    const end = s.shots.at(-1)[1], n = Math.floor(end * FPS);
    for (let k = 0, i = 0; k < n; k++) { // nearest shot to each output time
      const t = k / FPS;
      while (i + 1 < s.shots.length && Math.abs(s.shots[i + 1][1] - t) <= Math.abs(s.shots[i][1] - t)) i++;
      linkSync(s.shots[i][0], join(out, `${String(k + 1).padStart(4, '0')}.jpg`));
    }
    writeFileSync(`${out}.json`, JSON.stringify({ frames: n, marks: s.marks }));
    console.log(`${s.name}: ${s.shots.length} shots over ${end.toFixed(2)} s → ${n} frames`, s.marks);
  };
  return s;
}
