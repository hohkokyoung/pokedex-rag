# README videos

The README shows two videos, both generated from the running app by `tools/video/`:

| File | What | Made by |
|---|---|---|
| `docs/media/pokerag-promo.mp4` | 23 s promo of the live app, 1440p60, original soundtrack | `make video-promo` |
| `docs/media/pokerag-promo.webp` | the README's inline preview of it (animated, 24 fps, 960px) | `make video-promo` |
| `docs/media/pokerag-tour.mp4` | about 1:45 screen tour of every page, 1080p | `make video-tour` |

Re-render after a visible UI change, so the README doesn't show an old screen.

## Running it

Needs the stack up with data (`make up`, `make data`), plus `ffmpeg` and `uv` on the
host. The promo also needs Xcode, fvm and a booted iPhone simulator (`open -a
Simulator`) for its app scene. Once:

```bash
make video-setup
```

Then either or both:

```bash
make video-promo
```

```bash
make video-tour
```

The targets read the frontend and backend ports from Docker Compose. Run the scripts
directly with `APP_URL` / `API_URL` set if the app runs elsewhere, or `CHROME=<path>` to
use a Chrome you already have instead of Playwright's.

**LLM calls.** Both ask real questions: the promo asks one, and the tour asks three (two on
`/ask`, one on the home tile). With a key set that's a few planning/answer calls unless
the answers are cached; keyless costs nothing.

**What it reads.** The "fullest saved team" (most members) is the team shown in both
videos, so build one first. The promo also opens Gabite → Garchomp → Mega Garchomp and
the home page's type and damage calculators.

**Rendering is slow.** The promo's capture takes about 15 minutes and its render about 20
(1,380 frames at 3840×2160); `node render.mjs 3.5 11.9` checks single stills in seconds.

## How the promo is made

Every UI frame in the promo is the running app in use, recorded live, not a mock-up or a
still. Six scenes: the Ask bar typing a question and its cited answer, the brand, the
Pokédex (a filter, then Gabite → Garchomp → Mega), the damage and type calculators, a
team's grade, and an outro with the iOS app.

1. `capture.mjs` records six clips into `tools/video/build/clips/` with `slowclock.mjs`:
   a pointer moves, clicks and types in the real pages. Each clip is 60 fps at 2×, and
   its `.json` holds the page time of each action (the "marks").
2. `capture-app.mjs` builds the Flutter app for the simulator, installs it, and
   screenshots three pages (the Pokédex, Garchomp, the fullest team) with Apple's 9:41
   status bar; the outro uses Garchomp. Each is a fresh launch: it writes a one-shot
   `start_route` preference that the app reads at startup and clears
   (`mobile/lib/main.dart`). It writes through the simulator's settings daemon
   (`simctl spawn … defaults write <container path>`). Writing the plist directly loses
   to the daemon's cache, and `defaults write <bundle id>` lands where the app doesn't
   read. `SKIP_BUILD=1` reuses the last build.
3. `promo/index.html` is the composition and `promo/scenes.js` its timing: each clip
   plays in a "window" with a camera (pan and zoom) and a map from video time to clip
   time, pinned to the marks. After a re-capture, check the marks still line up.
4. `render.mjs` seeks the timeline frame by frame (never plays it, so every run is
   identical) at 3840×2160 and 60 fps, synthesises the soundtrack (`promo/music.py`, with
   the clicks and cues in `promo/sfx.json`), and encodes 1440p. Frame 0 is replaced by
   a settled frame of the Ask answer, so players' thumbnails show it.
5. `preview.py` encodes the README preview. Its docstring has the settings and why:
   every frame is a full keyframe, because partial-frame updates left smears behind
   moving shadows.

**Why the slow clock** (`slowclock.mjs` has the detail). CDP's screencast only delivers
1× frames, which go soft when the camera zooms. 2× screenshots take ~80 ms each, so the
page's clock (JS time, timers, rAF, CSS animations) is slowed to 1/20 (1/50 for the
detail page's heavy form morph) and shots are taken back to back, then resampled to 60 fps
by nearest page time. Two traps made clips stutter: ffmpeg's concat demuxer rounds image
timestamps to 40 ms (25 fps), and back-to-back screenshots starve the page's rAF, so the
team page's scroll is set before every shot instead.

**Framing rules.** The app's nav is either wholly in a window or out of it, never a
sliced logo. Home's calculators are recorded at 1920 wide; narrower, the damage calc's
roster truncates names to "G…".

## How the tour is made

`tour.mjs` drives the app like a visitor (with a red ring as a visible cursor) and
records the browser's own screencast frames as high-quality JPEGs, each held for its
real duration, then encodes 30 fps 1080p. Playwright's built-in video recorder is not
used: its low bitrate blurs UI text. A step whose selector no longer matches is logged
(`step failed: …`) and skipped, so check the output after UI changes.

## Why the README shows an image, not a player

GitHub doesn't play a video stored in the repo inline; it only shows a player for videos
uploaded to an issue or PR (`github.com/user-attachments/...` links). The README embeds
the animated preview and links to the MP4s, which play in GitHub's file viewer.
