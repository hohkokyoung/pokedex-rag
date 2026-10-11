// Captures the promo's app screens from the iOS Simulator into build/assets/
// (app-pokedex.png, app-garchomp.png, app-team.png). Needs a booted iPhone simulator,
// fvm and Xcode; no LLM calls.
//   SKIP_BUILD=1 node capture-app.mjs   reuse the last simulator build
//
// Each screen is a fresh launch onto one page: the app reads a one-shot `start_route`
// preference at startup (mobile/lib/main.dart) and clears it.
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { ASSETS, ROOT, ensureDir, showcaseTeam } from './lib.mjs';

const BUNDLE = 'dev.pokerag.pokerag';
const MOBILE = join(ROOT, 'mobile');
const sh = (cmd, args, opts = {}) => execFileSync(cmd, args, { encoding: 'utf8', ...opts });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const booted = JSON.parse(sh('xcrun', ['simctl', 'list', 'devices', 'booted', '-j'])).devices;
const device = Object.values(booted).flat().find((d) => d.name.startsWith('iPhone'));
if (!device) throw new Error('Boot an iPhone simulator first (open -a Simulator).');
const udid = device.udid;
console.log(`simulator: ${device.name} (${udid})`);

if (!process.env.SKIP_BUILD) {
  sh('fvm', ['flutter', 'build', 'ios', '--simulator', '--debug'], { cwd: MOBILE, stdio: 'inherit' });
}
sh('xcrun', ['simctl', 'install', udid, join(MOBILE, 'build/ios/iphonesimulator/Runner.app')]);
// Apple's marketing status bar: 9:41, full signal and battery.
sh('xcrun', ['simctl', 'status_bar', udid, 'override', '--time', '9:41', '--batteryState', 'charged',
  '--batteryLevel', '100', '--cellularBars', '4', '--wifiBars', '3', '--dataNetwork', 'wifi']);

// The app's own preferences (its data container), written through the simulator's
// settings daemon. Writing the file directly loses to the daemon's cached copy, and
// `defaults write <bundle id>` lands in a domain the app's preferences plugin doesn't read.
const prefs = join(sh('xcrun', ['simctl', 'get_app_container', udid, BUNDLE, 'data']).trim(),
  'Library/Preferences', BUNDLE);
const setStart = (route) =>
  sh('xcrun', ['simctl', 'spawn', udid, 'defaults', 'write', prefs, 'flutter.start_route', '-string', route]);

const team = await showcaseTeam();
const shots = [
  ['/', 'app-pokedex', 6000],
  ['/pokemon/445', 'app-garchomp', 7000],
  [`/teams/${team.id}`, 'app-team', 9000], // the report loads analysis, strategy and summary
];
ensureDir(ASSETS);
for (const [route, name, wait] of shots) {
  try { sh('xcrun', ['simctl', 'terminate', udid, BUNDLE], { stdio: 'ignore' }); } catch { /* not running */ }
  await sleep(1500);
  setStart(route);
  sh('xcrun', ['simctl', 'launch', udid, BUNDLE]);
  await sleep(wait);
  sh('xcrun', ['simctl', 'io', udid, 'screenshot', join(ASSETS, `${name}.png`)], { stdio: 'ignore' });
  console.log('captured', name, route);
}
sh('xcrun', ['simctl', 'status_bar', udid, 'clear']);
