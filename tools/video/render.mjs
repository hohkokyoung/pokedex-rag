// Renders promo/index.html frame by frame (deterministic: the timeline is seeked,
// never played), then encodes docs/media/pokerag-promo.mp4 (1440p) and the README
// preview pokerag-promo.webp. Needs ffmpeg and uv on PATH.
//   node render.mjs              full render + encode
//   node render.mjs 6.5 19 28.5  stills at those seconds → build/stills/ (for checking)
import { execFileSync } from 'node:child_process';
import { rmSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { BUILD, HERE, MEDIA, ensureDir, launch } from './lib.mjs';

const FPS = 30;
const stills = process.argv.slice(2).map(Number);
const b = await launch();
// Rendered at 2× (3840×2160) and scaled down: supersampling keeps UI text crisp.
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await p.goto(pathToFileURL(join(HERE, 'promo/index.html')).href);
await p.evaluate(() => window.ready);
const total = await p.evaluate(() => window.TOTAL);

if (stills.length) {
  const dir = ensureDir(join(BUILD, 'stills'));
  for (const t of stills) { await p.evaluate((t) => window.seek(t), t); await p.screenshot({ path: join(dir, `${t}.png`) }); }
  console.log(`stills → ${dir}`); await b.close(); process.exit(0);
}

const frames = join(BUILD, 'frames'); rmSync(frames, { recursive: true, force: true }); ensureDir(frames);
const n = Math.round(total * FPS);
for (let i = 0; i < n; i++) {
  await p.evaluate((t) => window.seek(t), i / FPS);
  await p.screenshot({ path: join(frames, `f${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 94 });
  if (i % 150 === 0) console.log(`frame ${i}/${n}`);
}
await b.close();

const mp4 = join(MEDIA, 'pokerag-promo.mp4');
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', join(frames, 'f%05d.jpg'),
  '-vf', 'scale=2560:1440:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
  '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
console.log('wrote', mp4);
execFileSync('uv', ['run', '--with', 'pillow', 'python', join(HERE, 'preview.py'), frames, join(MEDIA, 'pokerag-promo.webp')], { stdio: 'inherit' });
