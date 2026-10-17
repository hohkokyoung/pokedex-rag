// Renders promo/index.html frame by frame (deterministic: the timeline is seeked, never
// played) at 3840×2160 and 60 fps, synthesises the soundtrack, then encodes
// docs/media/pokerag-promo.mp4 (1440p60) and the README preview pokerag-promo.webp.
// Needs ffmpeg and uv on PATH, and build/clips + build/assets from capture.mjs / capture-app.mjs.
//   node render.mjs              full render + encode
//   node render.mjs 3.5 11.9 21  stills at those seconds → build/stills/ (for checking)
import { execFileSync } from 'node:child_process';
import { copyFileSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { BUILD, HERE, MEDIA, ensureDir, launch } from './lib.mjs';
import { CLIPS, FPS } from './slowclock.mjs';

const POSTER = 4.9; // the frame baked in as frame 0: the platforms' thumbnail
const stills = process.argv.slice(2).map(Number);
const frames = Object.fromEntries(readdirSync(CLIPS).filter((f) => f.endsWith('.json'))
  .map((f) => [f.slice(0, -5), JSON.parse(readFileSync(join(CLIPS, f), 'utf8')).frames]));

const b = await launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
p.on('pageerror', (e) => console.log('page error:', e.message));
await p.addInitScript((f) => { window.CLIP_FRAMES = f; }, frames);
await p.goto(pathToFileURL(join(HERE, 'promo/index.html')).href);
await p.evaluate(() => window.ready);
const total = await p.evaluate(() => window.TOTAL);
const shot = async (t, path) => { await p.evaluate((t) => window.seek(t), t); await p.screenshot({ path, type: 'jpeg', quality: 95 }); };

if (stills.length) {
  const dir = ensureDir(join(BUILD, 'stills'));
  for (const t of stills) await shot(t, join(dir, `${t}.jpg`));
  console.log(`stills → ${dir}`); await b.close(); process.exit(0);
}

const out = join(BUILD, 'frames'); rmSync(out, { recursive: true, force: true }); ensureDir(out);
const n = Math.round(total * FPS), f = (i) => join(out, `f${String(i).padStart(5, '0')}.jpg`);
for (let i = 0; i < n; i++) {
  await shot(i / FPS, f(i));
  if (i % 120 === 0) console.log(`frame ${i}/${n}`);
}
await b.close();
copyFileSync(f(Math.round(POSTER * FPS)), f(0));

const wav = join(BUILD, 'audio.wav'), master = join(BUILD, 'audio-master.wav');
execFileSync('uv', ['run', '-q', '--with', 'numpy', 'python', join(HERE, 'promo/music.py'), join(HERE, 'promo/sfx.json'), wav], { stdio: 'inherit' });
execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', wav, '-af', 'highshelf=f=9000:g=-4,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000', master]);

const mp4 = join(MEDIA, 'pokerag-promo.mp4');
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', join(out, 'f%05d.jpg'), '-i', master,
  '-vf', 'scale=2560:1440:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
  '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
console.log('wrote', mp4);
execFileSync('uv', ['run', '--with', 'pillow', 'python', join(HERE, 'preview.py'), out, join(MEDIA, 'pokerag-promo.webp')],
  { stdio: 'inherit', env: { ...process.env, FPS: String(FPS) } });
