#!/usr/bin/env node
// ui_shots.mjs — PHOTOGRAPH THE UI CHROME. The battle HUD, the pause menu and
// the shop, off tools/ui_mock.html (the real modules, the real rules data, a
// posed party), at a TV-shaped 1920x1080, plus a downscaled copy of every plate
// so "is this readable across a living room" is a picture and not an opinion.
//
// WHY IT EXISTS: the UI lane's deliverable is before/after plates, and every
// previous pass shot them by hand. One command, a manifest, and the same frame
// every time is the difference between "it looks better" and a comparison.
//
//   node tools/ui_shots.mjs --out=docs/qa/ui/before        # every surface
//   node tools/ui_shots.mjs --out=/tmp/x --only=battle-cmd,menu-root
//   node tools/ui_shots.mjs --headless                     # no window (no GPU)
//
// THE WINDOW IS REAL BY DEFAULT. rAF is throttled to nothing in a background or
// headless tab and its canvas screenshots go stale (repo canon); the 3D arena
// under the battle chrome also needs a GPU to render inside a sane budget. So
// this launches a visible Chrome and activates it, and the DOM stage
// (?stage=dom) is used for the chrome shots — the windows are what this lane
// owns, and they are identical over either stage.
//
// SERVES THE REPO ROOT, not public/: ui_mock.html lives in tools/ and re-roots
// the game's relative paths with <base href="/public/">.
import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, extname, resolve, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const OUT = resolve(ROOT, arg('out', 'docs/qa/ui/shots'));
const ONLY = (arg('only', '') || '').split(',').filter(Boolean);
const HEADLESS = argv.includes('--headless');
const W = parseInt(arg('w', '1920'), 10), H = parseInt(arg('h', '1080'), 10);
// TV-DISTANCE PROXY. A 55" screen at 10 feet subtends about what a 13" laptop
// does at arm's length; downscaling the plate by ~3.4x and reading it is the
// cheap stand-in for walking across the room. Anything that dies here dies there.
const TVW = parseInt(arg('tvw', '560'), 10);

// ---- the surfaces ---------------------------------------------------------
// NO `stage=dom`. That flag is the no-WebGL FALLBACK (it sets Battle.stage3d =
// false), and UI chrome composited over a flat DOM stage is not the chrome the
// player sees — contrast, legibility and where the eye goes all move when the
// same windows sit over a lit 3D arena. The first pass of these plates was shot
// on the fallback and every judgement made on them had to be re-taken
// (coordinator correction, 2026-08-02). The shipped stage is the default; this
// tool ASSERTS which one booted (see the mockbar read below) rather than
// trusting the URL.
const SHOTS = [
  ['battle-cmd',    'view=battle&zone=forest&state=cmd'],
  ['battle-target', 'view=battle&zone=forest&state=target'],
  ['battle-items',  'view=battle&zone=forest&state=items'],
  ['battle-outro',  'view=battle&zone=meadow&group=reed-nibbler&state=outro'],
  ['battle-meadow', 'view=battle&zone=meadow&group=reed-nibbler,reed-nibbler&state=cmd'],
  ['menu-root',     'view=menu&screen=root'],
  ['menu-party',    'view=menu&screen=party'],
  ['menu-equip',    'view=menu&screen=equip'],
  ['menu-items',    'view=menu&screen=items'],
  ['shop',          'view=shop&shop=del-weapon'],
  ['shop-qty',      'view=shop&shop=del-weapon&qty=1'],
];

// ---- MOTION -----------------------------------------------------------------
// A STILL CANNOT SHOW AN EASING CURVE. Each entry parks a surface, runs a `fire`
// expression against the REAL module API (no re-implementation of anything), and
// photographs the next few hundred milliseconds as a strip — which is the only
// way to check that a thing arrives on a curve rather than appearing, and the
// only way to see the chase bar at all, since its whole life is 780 ms.
//
// SLOW MOTION, AND WHY IT IS HONEST. A CDP screenshot of a 1920x1080 page costs
// 200-300 ms round trip, so a strip shot at "55 ms" intervals photographs a
// 300 ms entrance exactly once — the first attempt returned seven identical
// frames of an already-arrived menu. Rather than lie about the interval, the
// capture stretches the CLOCK and leaves the CURVE alone: every duration in the
// kit is a custom property, so multiplying the four tokens plays the same
// easing at 1/8 speed. What the strip shows is the real curve; only the seconds
// are the instrument's.
// 20x. The ease is cubic-bezier(.16,1,.3,1) — deliberately front-loaded, so a
// third of the way through the clock it is already 93% arrived; at 8x that put
// only two frames inside the ramp. At 20x the strip walks the curve.
const SLOW = ':root{--eb-t-fast:2400ms;--eb-t-med:4400ms;--eb-t-slow:7600ms;' +
  '--eb-t-ghost:11200ms;--eb-t-ghost-wait:4400ms}' +
  '.ebui-panel.enter .eb-win{animation-duration:6000ms}' +
  '.ebui-panel.enter .eb-win:nth-child(2){animation-delay:900ms}' +
  '.ebui-panel.enter .eb-win:nth-child(3){animation-delay:1800ms}' +
  '.ebui-panel.enter .eb-win:nth-child(4){animation-delay:2600ms}';
const SLOWJS = '(()=>{const s=document.createElement("style");s.textContent=' +
  JSON.stringify(SLOW) + ';document.head.appendChild(s);return 1})()';

const MOTION = [
  { tag: 'motion-menu-open', url: 'view=menu&screen=root', n: 8, every: 30, slow: true,
    // close, then re-open: the entrance is what is being measured
    fire: 'window.Menu.close(), setTimeout(()=>window.Menu.open(),400), 1' },
  { tag: 'motion-hp-chase', url: 'view=battle&zone=forest&state=cmd', n: 8, every: 30, slow: true,
    // drive the SHIPPED syncHp with a real state mutation: bar, chase bar,
    // numeral tween and the danger band all come from the game's own code path
    fire: '(()=>{const s=window.__EBB_SCREEN,S=s._state();' +
          'const v=S.state.party.find(c=>!c.dead);v.hp=Math.max(1,Math.round(v.maxHp*0.12));' +
          's.syncHp(S.state);return 1})()' },
];

// ---- a static server over the repo root -----------------------------------
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.glb': 'model/gltf-binary', '.mp3': 'audio/mpeg', '.css': 'text/css', '.svg': 'image/svg+xml' };
async function serve() {
  const port = await freePort();
  const srv = createServer(async (req, res) => {
    const p = normalize(decodeURIComponent(req.url.split('?')[0]));
    const file = join(ROOT, p);
    if (!file.startsWith(ROOT)) { res.writeHead(403).end(); return; }
    try {
      const buf = await readFile(file);
      res.writeHead(200, { 'Content-Type': MIME[extname(file)] || 'application/octet-stream',
        'Cache-Control': 'no-store' });
      res.end(buf);
    } catch (e) { res.writeHead(404).end('no ' + p); }
  });
  await new Promise(r => srv.listen(port, '127.0.0.1', r));
  return { port, close: () => srv.close() };
}

// ---- CDP ------------------------------------------------------------------
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((ok, no) => { const mid = ++id; pend.set(mid, { ok, no });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} })); });
      },
      close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(JSON.stringify(m.error))) : ok(m.result); }
    });
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const srv = await serve();
const CDP = await freePort();
const profile = join(process.env.TMPDIR || '/tmp', 'ui-shots-' + process.pid);
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--hide-crash-restore-bubble', '--autoplay-policy=no-user-gesture-required',
  `--window-size=${W},${H}`, '--window-position=0,0',
  ...(HEADLESS ? ['--headless=new', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] : []),
  `http://127.0.0.1:${srv.port}/tools/ui_mock.html?view=menu`,
], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (!closing) { closing = true; try { chrome.kill('SIGKILL'); } catch (e) { } srv.close(); } };
process.on('exit', kill);
process.on('SIGINT', () => { kill(); process.exit(130); });
if (!HEADLESS) { try { execFileSync('osascript', ['-e', 'tell application "Google Chrome" to activate']); } catch (e) { } }

// find the page (our own mock URL, not GAME_PAGE)
let wsUrl = null, seen = null;
for (let i = 0; i < 120 && !wsUrl; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${CDP}/json/list`)).json();
    seen = list;
    const p = list.find(t => t.type === 'page' && /ui_mock\.html/.test(t.url));
    if (p) wsUrl = p.webSocketDebuggerUrl;
  } catch (e) { }
  if (!wsUrl) await sleep(250);
}
if (!wsUrl) { console.error('no ui_mock page; CDP saw:', JSON.stringify(seen, null, 1)); kill(); process.exit(2); }
const cdp = await connect(wsUrl);
await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
// EXACT PIXELS, whatever the OS scale factor is: a 2x Retina screenshot and a 1x
// one are not comparable plates, and the TV downscale would mean two things.
await cdp.send('Emulation.setDeviceMetricsOverride',
  { width: W, height: H, deviceScaleFactor: 1, mobile: false });

await mkdir(OUT, { recursive: true });
const done = [];
for (const [tag, qs] of SHOTS) {
  if (ONLY.length && !ONLY.includes(tag)) continue;
  const url = `http://127.0.0.1:${srv.port}/tools/ui_mock.html?${qs}&nomusic=1`;
  await cdp.send('Page.navigate', { url });
  let ready = false;
  for (let i = 0; i < 160 && !ready; i++) {
    await sleep(150);
    try {
      const r = await cdp.send('Runtime.evaluate', {
        expression: 'document.documentElement.getAttribute("data-mock-ready")===\"1\"',
        returnByValue: true });
      ready = !!(r.result && r.result.value);
    } catch (e) { }
  }
  await sleep(500);                       // let transitions land on their end state
  // WHICH STAGE ACTUALLY BOOTED. The mock prints it, and a battle plate is
  // worthless if it turns out to be the DOM fallback — so the plate carries the
  // evidence rather than the URL being trusted. An instrument that photographs
  // something must say what it photographed.
  let note = '';
  try {
    const r = await cdp.send('Runtime.evaluate', {
      expression: '(document.getElementById("mockbar")||{}).textContent||""', returnByValue: true });
    note = (r.result && r.result.value) || '';
  } catch (e) { }
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  const file = join(OUT, tag + '.png');
  await writeFile(file, Buffer.from(shot.data, 'base64'));
  // the TV-distance copy, side by side in the same directory
  try { execFileSync('sips', ['-Z', String(TVW), file, '--out', join(OUT, tag + '.tv.png')], { stdio: 'ignore' }); }
  catch (e) { }
  const bad = /battle/.test(tag) && !/3D ARENA/.test(note);
  done.push(tag + (ready ? '' : ' (NOT READY)') + (bad ? '  <-- NOT THE 3D ARENA' : ''));
  console.log('shot', tag, ready ? '' : 'NOT-READY', '·', note.replace(/^mock · /, ''));
  if (bad) console.log('  !! this battle plate did NOT boot the 3D arena — do not judge chrome on it');
}
// ---- motion strips ----------------------------------------------------------
for (const m of MOTION) {
  if (ONLY.length && !ONLY.includes(m.tag)) continue;
  await cdp.send('Page.navigate', { url: `http://127.0.0.1:${srv.port}/tools/ui_mock.html?${m.url}&nomusic=1` });
  let ready = false;
  for (let i = 0; i < 160 && !ready; i++) {
    await sleep(150);
    try {
      const r = await cdp.send('Runtime.evaluate', {
        expression: 'document.documentElement.getAttribute("data-mock-ready")===\"1\"', returnByValue: true });
      ready = !!(r.result && r.result.value);
    } catch (e) { }
  }
  await sleep(400);
  if (m.slow) await cdp.send('Runtime.evaluate', { expression: SLOWJS, returnByValue: true });
  const fired = await cdp.send('Runtime.evaluate', { expression: m.fire, returnByValue: true });
  if (!fired.result || fired.result.value !== 1) {
    console.log('  !! motion trigger did not run for', m.tag, JSON.stringify(fired.result));
    continue;
  }
  for (let i = 0; i < m.n; i++) {
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
    const f = join(OUT, m.tag + '-' + String(i).padStart(2, '0') + '.png');
    await writeFile(f, Buffer.from(shot.data, 'base64'));
    // strips are read as a sequence, so they are written small enough to read as one
    try { execFileSync('sips', ['-Z', '760', f, '--out', f], { stdio: 'ignore' }); } catch (e) { }
    await sleep(m.every);
  }
  console.log('strip', m.tag, m.n, 'frames @', m.every + 'ms');
}

console.log('\n' + done.length + ' plates ->', OUT);
cdp.close(); kill();
process.exit(0);
