"""Encode the README preview: an animated WebP from the promo's frames.

GitHub won't play a repo MP4 inline, but it shows animated images. Settings, and why:
  - 24 fps, 960px: smooth and about 10 MB. 30 fps is about 14 MB; 15 fps stutters.
  - every frame a keyframe (kmax=1): libwebp's partial-frame updates left a stale smear
    of moving shadows (the Teams scene). Full frames cost size but are exact.
  - lossy q62, full colour: a GIF's 256-colour palette dithers soft UI shadows into blur.

Usage: uv run --with pillow python preview.py <frames dir> <out.webp>
"""

import glob
import os
import subprocess
import sys
import tempfile

from PIL import Image

frames, out = sys.argv[1], sys.argv[2]
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-framerate", "30", "-i", os.path.join(frames, "f%05d.jpg"),
         "-vf", "fps=24,scale=960:-1:flags=lanczos", os.path.join(tmp, "%04d.png")],
        check=True,
    )
    images = [Image.open(f).convert("RGB") for f in sorted(glob.glob(os.path.join(tmp, "*.png")))]
    # Hold the last frame (the outro) for 1.5 s before looping.
    durations = [42] * (len(images) - 1) + [1500]
    images[0].save(out, save_all=True, append_images=images[1:], duration=durations, loop=0,
                   quality=62, method=4, minimize_size=False, kmin=0, kmax=1)
print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB)")
