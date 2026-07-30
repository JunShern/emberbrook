#!/usr/bin/env node
// arena_playtest.mjs — DRIVE THE REAL PAGE, HEADLESS, AND REPORT NUMBERS.
//
// The mock proved the 3D battle arena in isolation. This proves the INTEGRATION:
// play3d.html itself, the real encounter director firing organically as the player
// walks, the real fade, the real UILOCK, the real music wrap, and — the part no
// screenshot can show — that the arena is GONE afterwards and has not leaked a
// WebGL context.
//
//   node tools/arena_playtest.mjs                  # all four suites, asserts
//   node tools/arena_playtest.mjs --only=serial    # one suite
//   node tools/arena_playtest.mjs --json           # machine-readable
//   node tools/arena_playtest.mjs --head           # watch it in a real window
//   node tools/arena_playtest.mjs --port=3000      # where the game is served
//
// HOW: launches Chrome with --remote-debugging-port, talks CDP over the `ws`
// dependency the server already uses (no puppeteer, no new dependency), injects
// tools/arena_walk.js into the live page and awaits its promises. Everything it
// asserts is a number read out of the running game.
//
// WHY NOT SCREENSHOTS: rAF is throttled to nothing in a headless/background tab and
// a screenshot of one is stale — the lesson of slice finding 7, and the reason
// cine_walk reads pixels rather than pictures. In-page counters are the ground truth.
//
// WHY speed:0 EVERYWHERE: battle event pacing is setTimeout-based (deliberately —
// rAF does not run in a hidden tab at all), but Chrome applies intensive timer
// throttling after ~5 minutes hidden, so any speed > 0 turns a 4-second battle into
// tens of minutes. Battle's own harness canon, and this harness obeys it.
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const ONLY = arg('only', null);
const AS_JSON = argv.includes('--json');
const HEAD = argv.includes('--head');
const SCENE = arg('scene', 'ow-valley');
const CDP_PORT = parseInt(arg('cdp', '9339'), 10);

const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=${SCENE}&rt=1`;

const log = (...a) => { if (!AS_JSON) console.log(...a); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- launch ---------------------------------------------------------------
const profile = join(process.env.TMPDIR || '/tmp', 'arena-playtest-' + process.pid);
const flags = [
  `--remote-debugging-port=${CDP_PORT}`,
  `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  // WebGL in headless comes from swiftshader; without these the arena cannot exist
  // and the whole run would silently measure the DOM fallback instead. SWIFTSHADER
  // RENDERS THE ARENA AT WELL UNDER ONE FRAME PER SECOND — that is the harness, not
  // the game, and --gpu (with --head) is how you get a real frame rate to compare.
  ...(argv.includes('--gpu') ? [] : ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu']),
  // music.js will not build an AudioContext without a user gesture, and a headless
  // run has none — so the gesture requirement is waived rather than the music being
  // declared untestable.
  '--autoplay-policy=no-user-gesture-required',
  // heapMB() calls gc() when it can; without this it reports a noisier number
  '--js-flags=--expose-gc',
  '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
];
log('launching chrome ->', URL);
const chrome = spawn(CHROME, flags, { stdio: 'ignore', detached: false });
let closing = false;
const kill = () => { if (!closing) { closing = true; try { chrome.kill('SIGKILL'); } catch (e) { } } };
process.on('exit', kill);
process.on('SIGINT', () => { kill(); process.exit(130); });

// ---- CDP ------------------------------------------------------------------
async function targetWs() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
      const list = await r.json();
      const page = list.find(t => t.type === 'page' && t.url.includes('play3d.html'));
      if (page && page.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch (e) { /* not up yet */ }
    await sleep(250);
  }
  throw new Error('chrome never exposed a play3d page over CDP');
}

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map();
    let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((ok, no) => {
          const mid = ++id;
          pend.set(mid, { ok, no });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
        });
      },
      close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) {
        const { ok, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(m.error.message)) : ok(m.result);
      }
    });
  });
}

// evaluate an expression in the page and return its (awaited) value
async function evalPage(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true,
    userGesture: true, timeout: timeoutMs || 600000,
  });
  if (r.exceptionDetails) {
    const e = r.exceptionDetails;
    throw new Error('page exception: ' + (e.exception && e.exception.description || e.text));
  }
  return r.result && r.result.value;
}

// ---- the suites -----------------------------------------------------------
const SUITES = {
  // (1) the organic path: the director fires while the player walks, and every
  // stage of the handover is measured on the way through.
  organic: 'ARENAWALK.organic({})',
  // (2) the music wrap composed with the stage delegation rather than fighting it
  music: 'ARENAWALK.music()',
  // (3) the no-WebGL fallback, on the real page
  nogl: 'ARENAWALK.nogl()',
  // (4) three battles back to back: teardown, contexts, heap
  serial: `ARENAWALK.serial(${parseInt(arg('battles', '6'), 10)})`,
};

function verdictLines(kind, run) {
  const out = [];
  const mark = v => (v === true ? 'ok  ' : v === false ? 'FAIL' : '--  ');
  out.push('');
  out.push(`--- ${kind} ${run.ok ? 'PASS' : 'FAIL'} ---`);
  if (run.error) out.push('    error: ' + run.error);
  for (const [k, v] of Object.entries(run.checks || {})) {
    out.push(`  ${mark(typeof v === 'boolean' ? v : null)} ${k}` +
             (typeof v === 'boolean' ? '' : '  ' + JSON.stringify(v)));
  }
  return out;
}

(async function main() {
  const wsUrl = await targetWs();
  const cdp = await connect(wsUrl);
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  await cdp.send('Log.enable');

  // Wait for the game to be genuinely ready, not merely loaded: the scene GLB, the
  // rules data, the battle kernel and the director all arrive async.
  log('waiting for the world...');
  const ready = await evalPage(cdp, `(async () => {
    for (let i = 0; i < 240; i++) {
      const ok = window.SIM && window.SIM.zone && window.GS && window.GS.ok &&
                 window.Battle && window.Rules && window.Encounters &&
                 window.Encounters._debug().attached;
      if (ok) return { ready: true, i,
        scene: location.search, zone: window.SIM.zone(), pos: window.SIM.pos(),
        director: window.Encounters._debug(),
        music: !!window.Music, three: !!window.THREE && THREE.REVISION };
      await new Promise(r => setTimeout(r, 250));
    }
    return { ready: false,
      have: { SIM: !!window.SIM, GS: !!(window.GS && window.GS.ok), Battle: !!window.Battle,
              Rules: !!window.Rules, Encounters: !!window.Encounters,
              attached: !!(window.Encounters && window.Encounters._debug().attached) } };
  })()`, 90000);
  if (!ready.ready) { console.error('world never became ready:', JSON.stringify(ready)); kill(); process.exit(2); }
  log(`world ready (zone=${ready.zone}, three=r${ready.three}, music=${ready.music})`);

  // Inject the driver.
  await evalPage(cdp, readFileSync(join(HERE, 'arena_walk.js'), 'utf8') + '\n;true');
  const probe0 = await evalPage(cdp, 'ARENAWALK.glProbe()');
  log(`webgl contexts obtainable before any battle: ${probe0.obtained}/${probe0.of}`);

  // Confirm the arena is even possible here — otherwise every "pass" below would
  // be the DOM fallback quietly passing in its place.
  const cap = await evalPage(cdp, 'JSON.parse(JSON.stringify({avail: !!(window.BattleStage3D && BattleStage3D.available()), mod: !!window.BattleStage3D, dbg: Battle._debug().stage3d}))');
  log('stage capability:', JSON.stringify(cap.dbg));

  // --eval=<file>: run one throwaway probe against the live page and print what
  // it returns. The suites are the contract; this is the workbench for a change
  // that is being tuned by feel and needs one number out of a real battle.
  const EVAL = arg('eval', null);
  if (EVAL) {
    const out = await evalPage(cdp, readFileSync(EVAL, 'utf8'), 600000);
    console.log(JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  const results = {};
  let failed = 0;
  for (const [kind, expr] of Object.entries(SUITES)) {
    if (ONLY && ONLY !== kind) continue;
    log(`\n>>> ${kind} ...`);
    let run;
    try { run = await evalPage(cdp, `(async()=>{const r = await ${expr}; return JSON.parse(JSON.stringify(r));})()`); }
    catch (e) { run = { kind, ok: false, error: String(e.message || e) }; }
    results[kind] = run;
    if (!run.ok) failed++;
    if (!AS_JSON) verdictLines(kind, run).forEach(l => console.log(l));
  }

  const summary = await evalPage(cdp, 'JSON.parse(JSON.stringify(ARENAWALK.summary()))');
  const full = await evalPage(cdp, 'JSON.parse(JSON.stringify(ARENAWALK.report))');

  if (AS_JSON) console.log(JSON.stringify({ ready, cap: cap.dbg, results, summary, full }, null, 2));
  else {
    console.log('\n============================================================');
    console.log(failed ? `ARENA PLAYTEST: ${failed} SUITE(S) FAILED` : 'ARENA PLAYTEST GREEN — all suites passed');
    console.log('============================================================');
  }
  cdp.close();
  kill();
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error('playtest harness error:', e); kill(); process.exit(2); });
