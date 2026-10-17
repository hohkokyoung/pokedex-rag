// Scenes for index.html: clips, windows, cameras, timing (seconds). The clip-time maps are
// pinned to the actions' marks in build/clips/<clip>.json; re-check them after a re-capture.
window.TOTAL = 23.0;
window.CLIPS = { // recorded viewport width (CSS px) of each clip
  ask: { vw: 1280 }, dex: { vw: 1440 }, detail: { vw: 1440 }, calc: { vw: 1920 }, types: { vw: 1920 }, team: { vw: 1440 },
};
// cam keys: [t, x, y, zoom, dy]  (x, y = CSS px of the recorded page at the window centre)
window.LAYERS = [
  { el: '#w-ask img', clip: 'ask', from: 0, to: 5.5, map: [[0, 0.9], [5.5, 6.4]],
    win: [[0, 120, 490, 1680, 230], [2.95, 120, 490, 1680, 230], [3.6, 740, 90, 1080, 900]],
    cam: [[0, 640, 254, 1.56], [2.95, 640, 254, 1.56], [3.6, 640, 518, 1.0], [5.5, 640, 522, 1.04]] },
  { el: '#w-dex img.a', clip: 'dex', from: 8.0, to: 10.0, map: [[8.0, 0.75], [10.0, 2.75]],
    cam: [[8.0, 720, 450, 0.894, 0], [9.65, 720, 450, 0.92, 0], [10.0, 720, 450, 0.92, -850]] },
  { el: '#w-dex img.b', clip: 'detail', from: 9.65, to: 13.0, map: [[9.8, 0.93], [10.7, 1.83], [10.9, 3.01], [13.0, 5.11]],
    cam: [[9.65, 720, 500, 0.894, 850], [10.0, 720, 500, 0.894, 0], [13.0, 720, 492, 0.92, 0]] },
  { el: '#w-calc img', clip: 'calc', from: 13.0, to: 16.5, map: [[13.0, 0.48], [16.5, 3.98]],
    cam: [[13.0, 960, 420, 1.05], [16.5, 960, 420, 1.08]] },
  { el: '#w-types img', clip: 'types', from: 13.0, to: 16.5, map: [[13.0, 1.43], [16.5, 5.2]],
    cam: [[13.0, 238, 210, 1.29], [15.05, 238, 210, 1.29], [15.6, 238, 430, 1.29], [16.5, 238, 431, 1.29]] },
  { el: '#w-team img', clip: 'team', from: 16.5, to: 19.5, map: [[16.5, 0.0], [19.5, 3.0]],
    cam: [[16.5, 720, 437, 0.845], [19.5, 720, 440, 0.85]] },
];
window.SCENES = [['#s1', 0, 5.5], ['#s2', 5.5, 8.0], ['#s3', 8.0, 13.0], ['#s4', 13.0, 16.5], ['#s5', 16.5, 19.5], ['#s6', 19.5, 23.0]];
window.MOTION = (tl, { rise, fadeUp, winIn, out }) => {
  // S1 — hook: the Ask bar, typing; then the answer lands and the window opens up
  winIn('#w-ask', 0.0, { y: 40 });
  rise('#s1 .hook .mask>span', 0.12);
  tl.to('#s1 .hook', { y: -40, opacity: 0, duration: .35, ease: 'power2.in' }, 2.75);
  rise('#s1 .col .mask>span', 3.3);
  fadeUp('#s1 .sub', 3.55);
  out(['#s1 .col', '#w-ask'], 5.12);
  // S2 — brand
  tl.from('#s2 .logo', { scale: 0, rotation: -100, duration: .9, ease: 'back.out(1.7)' }, 5.5)
    .from('#s2 .word .mask>span', { yPercent: 110, duration: .8 }, 5.62);
  fadeUp('#s2 .sub', 5.9);
  tl.to('#s2 .wrap', { scale: .96, opacity: 0, duration: .3, ease: 'power2.in' }, 7.68);
  // S3 — Pokédex
  rise('#s3 .mask>span', 8.05);
  winIn('#w-dex', 8.0, { x: 120 });
  fadeUp('#s3 .sub', 8.45);
  out(['#s3 .col', '#w-dex'], 12.7);
  // S4 — the maths
  winIn('#w-calc', 13.0, { x: -120 });
  rise('#s4 .mask>span', 13.1);
  winIn('#w-types', 13.25, { y: 120 });
  fadeUp('#s4 .sub', 13.45);
  out(['#s4 .col', '#w-calc', '#w-types'], 16.2);
  // S5 — teams
  rise('#s5 .mask>span', 16.55);
  winIn('#w-team', 16.5, { y: 100 });
  fadeUp('#s5 .sub', 16.95);
  out(['#s5 .col', '#w-team'], 19.2);
  // S6 — outro
  tl.from('#s6 .logo', { scale: 0, rotation: -100, duration: .9, ease: 'back.out(1.7)' }, 19.55)
    .from('#s6 .word .mask>span', { yPercent: 110, duration: .8 }, 19.65);
  fadeUp('#s6 .line', 19.95);
  tl.from('#s6 .tags span', { y: 24, opacity: 0, duration: .6, stagger: .1 }, 20.2);
  fadeUp('#s6 .url', 20.6);
  tl.from('#s6 .phone', { y: 900, rotation: 6, duration: 1.3, ease: 'expo.out' }, 19.6)
    .to('#s6 .phone', { y: -16, duration: 2.0, ease: 'sine.inOut' }, 20.9);
};
