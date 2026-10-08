# README videos

The README shows two videos, both generated from the running app by `tools/video/`:

| File | What | Made by |
|---|---|---|
| `docs/media/pokerag-promo.mp4` | 34 s motion video, 1440p | `make video-promo` |
| `docs/media/pokerag-promo.webp` | the README's inline preview of it (animated, 24 fps, 960px) | `make video-promo` |
| `docs/media/pokerag-tour.mp4` | about 1:45 screen tour of every page, 1080p | `make video-tour` |

Re-render after a visible UI change, so the README doesn't show an old screen.

## Running it

Needs the stack up with data (`make up`, `make data`), plus `ffmpeg` and `uv` on the
host. Once:

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
videos, so build one first. Garchomp is the promo's hero; its stats are written into
the composition.

## How the promo is made

1. `capture.mjs` screenshots parts of the live app at 3× into `tools/video/build/assets/`:
   home dashboard cards, Pokédex cards, the Ask answer for "Fastest non-legendary Fire
   types", and the team rating panel. Fixed site chrome (nav, scroll progress bar,
   floating bars) is hidden for each shot so it can't overlap.
2. `promo/index.html` is the composition: seven scenes on one GSAP timeline over those
   stills. Open it in a browser after a capture to preview it.
3. `render.mjs` seeks the timeline frame by frame (never plays it, so every run is
   identical) at 3840×2160, then ffmpeg scales to 1440p. Supersampling is what keeps
   small UI text sharp. `node render.mjs 6.5 19 28.5` renders single stills instead,
   for checking a change without a full render.
4. `preview.py` encodes the README preview. Its docstring has the settings and why:
   every frame is a full keyframe, because partial-frame updates left smears behind
   moving shadows.

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
