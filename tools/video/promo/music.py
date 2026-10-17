"""The promo's soundtrack and SFX, synthesised from scratch (no samples, nothing licensed).

120 BPM, Am-F-C-G with a lift to C at the outro. SFX are tuned to the same key and
go through the same reverb bus so they sit inside the music.
usage: uv run --with numpy python music.py sfx.json out.wav
"""
import json
import sys

import numpy as np

SR = 48000
BPM = 120
BEAT = 60 / BPM
DUR = 23.0
N = int(SR * DUR)
rng = np.random.default_rng(7)


def t_arr(sec):
    return np.arange(int(sec * SR)) / SR


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def env(n, a, d, s=0.0, r=0.0, total=None):
    """ADSR in seconds; total = note length (sustain until release)."""
    total = total if total is not None else (a + d + r)
    L = int(total * SR) + int(r * SR)
    e = np.zeros(L)
    ia, idd = int(a * SR), int(d * SR)
    hold = max(int(total * SR) - ia - idd, 0)
    e[:ia] = np.linspace(0, 1, ia, endpoint=False) if ia else e[:0]
    e[ia:ia + idd] = np.linspace(1, s, idd, endpoint=False) if idd else e[ia:ia]
    e[ia + idd:ia + idd + hold] = s
    rel_start = ia + idd + hold
    ir = L - rel_start
    if ir > 0:
        e[rel_start:] = np.linspace(e[rel_start - 1] if rel_start else s, 0, ir)
    if n and n > len(e):
        e = np.concatenate([e, np.zeros(n - len(e))])
    return e[:n] if n else e


def onepole_lp(x, fc):
    """Simple one-pole lowpass; fc may be an array (time-varying)."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    z = 0.0
    for i in range(len(x)):
        z = (1 - a[i]) * x[i] + a[i] * z
        y[i] = z
    return y


def lp_fast(x, fc, passes=2):
    for _ in range(passes):
        a = np.exp(-2 * np.pi * fc / SR)
        y = np.empty_like(x)
        z = 0.0
        b = 1 - a
        for i in range(len(x)):
            z = b * x[i] + a * z
            y[i] = z
        x = y
    return x


def hp(x, fc):
    return x - lp_fast(x, fc, 1)


def saw(f, t, detune=0.0):
    ph = (f * (1 + detune)) * t
    return 2 * (ph - np.floor(ph + 0.5))


def add(buf, sig, start, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += gain * sig[: j - i]


# ---------------- arrangement ----------------
A3, C4, D4, E4, F3, G3 = 57, 60, 62, 64, 53, 55
CHORDS = [  # (start, end, root midi, chord tones) — bars start at 1.5 s so cuts land on downbeats
    (1.5, 3.5, 45, [57, 60, 64, 67]),   # Am7
    (3.5, 5.5, 41, [57, 60, 64, 65]),   # Fmaj7
    (5.5, 7.5, 48, [55, 60, 64, 67]),   # C
    (7.5, 9.5, 43, [55, 59, 62, 67]),   # G
    (9.5, 11.5, 45, [57, 60, 64, 67]),
    (11.5, 13.5, 41, [57, 60, 64, 65]),
    (13.5, 15.5, 48, [55, 60, 64, 67]),
    (15.5, 17.5, 43, [55, 59, 62, 67]),
    (17.5, 18.5, 38, [57, 60, 62, 65]),  # Dm7
    (18.5, 19.5, 43, [55, 59, 62, 65]),  # G7
    (19.5, 23.0, 48, [55, 59, 62, 64, 67]),  # Cmaj9 — the outro lift
]

pad = np.zeros(N)
bass = np.zeros(N)
pluck = np.zeros(N)
drums = np.zeros(N)
bells = np.zeros(N)

# Intro pad before the first chord: a soft A drone
t0 = t_arr(1.7)
pad[: len(t0)] += 0.18 * np.sin(2 * np.pi * hz(57) * t0) * np.minimum(np.linspace(0, 1.4, len(t0)), 1) * np.minimum(1, (1.7 - t0) / 0.4)

for (s, e, root, tones) in CHORDS:
    L = e - s + (1.6 if e >= 22 else 0.25)
    t = t_arr(L)
    # pad: detuned saws, soft
    sig = np.zeros(len(t))
    for m in tones:
        f = hz(m)
        sig += 0.5 * saw(f, t, -0.004) + 0.5 * saw(f, t, 0.004) + 0.3 * np.sin(2 * np.pi * f * t)
    sig /= len(tones)
    a = 0.35 if s > 1.5 else 0.6
    sig *= env(len(t), a, 0.4, 0.8, 0.25, total=e - s)[: len(t)]
    add(pad, sig, s, 0.32 if s < 19.5 else 0.42)
    # bass on 8ths after 5.0, whole notes before
    if s >= 5.5 and s < 19.5:
        step = BEAT / 2
        k = 0
        x = s
        while x < e - 1e-6:
            n = t_arr(step * 0.9)
            f = hz(root - 12 if root > 44 else root)
            b = np.sin(2 * np.pi * f * n) + 0.35 * np.sin(2 * np.pi * 2 * f * n) + 0.15 * saw(f, n)
            b *= env(len(n), 0.004, 0.18, 0.35, 0.03, total=step * 0.85)[: len(n)]
            add(bass, b, x, 0.55 if k % 2 == 0 else 0.38)
            x += step
            k += 1
    elif s < 5.5:
        n = t_arr(e - s)
        f = hz(root - 12 if root > 44 else root)
        b = np.sin(2 * np.pi * f * n) * env(len(n), 0.5, 0.3, 0.7, 0.2, total=e - s)[: len(n)]
        add(bass, b, s, 0.25 if s >= 3.5 else 0.12)
    else:  # outro: long sub
        n = t_arr(3.4)
        f = hz(36)
        b = (np.sin(2 * np.pi * f * n) + 0.3 * np.sin(2 * np.pi * 2 * f * n)) * np.exp(-n * 0.9)
        add(bass, b, s, 0.7)

    # pluck arpeggio: 16ths, pattern over chord tones up an octave
    if s >= 1.5 and s < 19.5:
        step = BEAT / 4
        pat = [0, 1, 2, 3, 2, 1, 3, 2]
        x, k = s, 0
        lvl = 0.10 if s < 5.5 else 0.17
        while x < e - 1e-6:
            if not (s < 5.5 and k % 2 == 1):  # sparser in the intro
                m = tones[pat[k % len(pat)] % len(tones)] + 12
                n = t_arr(0.35)
                f = hz(m)
                p = (saw(f, n) * 0.6 + np.sin(2 * np.pi * f * n)) * np.exp(-n * 16)
                add(pluck, p, x, lvl * (1.0 if k % 4 == 0 else 0.7))
            x += step
            k += 1

# Smooth the bright layers
pad = lp_fast(pad, 1800)
pluck = lp_fast(pluck, 3800, 1)


def kick(g=1.0):
    n = t_arr(0.45)
    f = 48 + 90 * np.exp(-n * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return g * np.sin(ph) * np.exp(-n * 7.5)


def snap(g=1.0):
    n = t_arr(0.22)
    noise = rng.standard_normal(len(n))
    body = np.sin(2 * np.pi * 190 * n) * np.exp(-n * 30)
    return g * (hp(noise, 1200) * np.exp(-n * 22) * 0.6 + body * 0.4)


def hat(g=1.0, dec=60):
    n = t_arr(0.08)
    return g * hp(rng.standard_normal(len(n)), 6500) * np.exp(-n * dec)


kick_times = []
for b in range(int(DUR / BEAT)):
    x = b * BEAT
    if 5.5 <= x < 19.0:
        drums_g = 1.0
        add(drums, kick(0.9), x)
        kick_times.append(x)
        if b % 2 == 1:
            add(drums, snap(0.32), x)
        add(drums, hat(0.13), x + BEAT / 2)
        add(drums, hat(0.06, 90), x + BEAT / 4)
        add(drums, hat(0.06, 90), x + 3 * BEAT / 4)
    elif 1.5 <= x < 5.5:
        add(drums, hat(0.07), x + BEAT / 2)
        if x >= 3.5:
            add(drums, kick(0.5), x)
            kick_times.append(x)
add(drums, kick(1.0), 19.5)
kick_times.append(19.5)

# Sidechain duck for pad / pluck / bass
duck = np.ones(N)
for x in kick_times:
    i = int(x * SR)
    L = int(0.32 * SR)
    j = min(N, i + L)
    curve = 1 - 0.45 * np.exp(-np.arange(j - i) / SR * 12)
    duck[i:j] = np.minimum(duck[i:j], curve)

# Riser into the brand reveal (4.0–5.0) and into the outro (17.5–19.0)
fx = np.zeros(N)


def riser(start, length, g):
    n = t_arr(length)
    noise = rng.standard_normal(len(n))
    fc = 400 + 5000 * (n / length) ** 2
    sig = onepole_lp(noise, fc) - onepole_lp(noise, fc * 0.35)
    sig *= (n / length) ** 1.6
    add(fx, sig, start, g)


riser(4.5, 1.0, 0.5)
riser(17.9, 1.6, 0.55)


# ---------------- SFX ----------------
def bell(m, g=1.0, dec=3.0):
    n = t_arr(2.5)
    f = hz(m)
    s = (np.sin(2 * np.pi * f * n) + 0.45 * np.sin(2 * np.pi * 2.0 * f * n) * np.exp(-n * 3)
         + 0.25 * np.sin(2 * np.pi * 3.01 * f * n) * np.exp(-n * 5))
    return g * s * np.exp(-n * dec) * np.minimum(1, n / 0.004)


def click(g=1.0):
    n = t_arr(0.05)
    tick = hp(rng.standard_normal(len(n)), 2500) * np.exp(-n * 160)
    tone = np.sin(2 * np.pi * hz(96) * n) * np.exp(-n * 90)
    return g * (0.7 * tick + 0.3 * tone)


def key(g=1.0):
    n = t_arr(0.03)
    return g * hp(rng.standard_normal(len(n)), 3500) * np.exp(-n * 260)


def whoosh(length=0.5, g=1.0):
    n = t_arr(length)
    noise = rng.standard_normal(len(n))
    x = n / length
    fc = 300 + 2600 * np.sin(np.pi * x) ** 2
    sig = onepole_lp(noise, fc) - onepole_lp(noise, fc * 0.3)
    return g * sig * np.sin(np.pi * x) ** 1.5


sfx = np.zeros(N)
events = json.load(open(sys.argv[1]))
for ev in events:
    kind, at = ev["kind"], ev["t"]
    g = ev.get("g", 1.0)
    if kind == "click":
        add(sfx, click(0.22 * g), at)
    elif kind == "key":
        add(sfx, key(0.05 * g * (0.7 + 0.6 * rng.random())), at)
    elif kind == "whoosh":
        add(sfx, whoosh(ev.get("len", 0.5), 0.16 * g), at - ev.get("len", 0.5) * 0.5)
    elif kind == "bell":
        for k, m in enumerate(ev["notes"]):
            add(sfx, bell(m, 0.11 * g), at + k * ev.get("spread", 0.07))

# ---------------- mix ----------------
music = 0.9 * pad * duck + 0.8 * bass * duck + 0.75 * pluck * duck + 0.7 * drums + 0.35 * fx


def reverb(x, secs=1.8, mix=0.22, pre=0.02):
    L = int(secs * SR)
    n = np.arange(L) / SR
    out = []
    for seed in (1, 2):
        r = np.random.default_rng(seed).standard_normal(L) * np.exp(-n * 6.9 / secs)
        r[: int(pre * SR)] = 0
        r = lp_fast(r, 5000, 1)
        r /= np.sqrt(np.sum(r ** 2))
        size = 1 << int(np.ceil(np.log2(len(x) + L)))
        y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(r, size), size)[: len(x)]
        out.append(y * mix)
    return out


wet_in = 0.6 * pad + 0.5 * pluck + 0.15 * drums + 0.9 * sfx + 0.3 * fx
wl, wr = reverb(wet_in)
L = music + 0.85 * sfx + wl
R = music + 0.85 * sfx + wr
# slight stereo: pluck pans left/right alternation via small delay
d = int(0.011 * SR)
R[d:] += 0.12 * pluck[:-d]
L += 0.0

# fades
fade_in = int(0.08 * SR)
for ch in (L, R):
    ch[:fade_in] *= np.linspace(0, 1, fade_in)
    tail = int(1.2 * SR)
    ch[-tail:] *= np.linspace(1, 0, tail) ** 1.5

st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) + 1e-9
st = np.tanh(st * 1.4) / np.tanh(1.4)
st *= 0.89

import wave  # noqa: E402

pcm = (st * 32767).astype("<i2")
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", sys.argv[2])
