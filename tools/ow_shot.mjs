#!/usr/bin/env node
/* ow_shot.mjs — screenshot an overworld scene through the real runtime.
 *
 *   node tools/ow_shot.mjs --out docs/qa/ow/after.png --sky 1
 *   node tools/ow_shot.mjs --out docs/qa/ow/before.png --sky 0
 *
 * WHY THIS EXISTS. The overworld renders in REAL TIME from scene.glb (rt=1), so
 * there is no baked plate to look at — the only honest way to judge an overworld
 * art change is to photograph the thing the player actually sees. This borrows
 * transition_test.mjs's CDP pattern verbatim (own port, own profile, cleaned on
 * every exit path) rather than inventing a second browser harness.
 *
 * IT WAITS FOR THE FRAME, NOT FOR A TIMER. The bundle is a 30 MB glb; a fixed
 * sleep either wastes time or photographs an empty scene. This polls the page's
 * own readiness (a rendered frame with the scene graph populated) and only then
 * captures — the same "measure the artifact, never the report" rule the bake
 * pipeline runs on.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage, GAME_PAGE } from './cdp.mjs';

const arg = (k, d) => {
  const i = process.argv.indexOf('--' + k);
  return i >= 0 ? process.argv[i + 1] : d;
};
const OUT = arg('out', 'docs/qa/ow/shot.png');
const SKY = arg('sky', '1');
const LIGHT = arg('light', '1');   // ?owlight — the 2026-08-02 lighting probe
const SCENE = arg('scene', 'ow-valley');
const PORT = parseInt(arg('port', '3000'), 10);
// PORT: a free one unless --cdp says otherwise. Two tools shipped 9351 and
// would have collided; a fixed port also collides with an orphan of yourself.
const CDP = parseInt(arg('cdp', '0'), 10) || await freePort();   // was 9412   // NOT transition_test's 9347
const WAIT = parseInt(arg('wait', '25'), 10);
const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const URL = `http://localhost:${PORT}/play.html?scene=${SCENE}&rt=1&owsky=${SKY}` +
            `&owlight=${LIGHT}&nomusic=1&v=${Date.now()}`;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'ow-shot-profile');
killOrphans(profile);   // a live Chrome still holding this profile makes the rmSync a lie
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check',
  // NO swiftshader/--disable-gpu here, unlike transition_test: this tool exists to
  // PHOTOGRAPH the render, and forcing software rasterisation while a Blender bake
  // owns the CPU made Chrome miss its 40 s CDP window entirely (measured — the same
  // launch without these flags exposed the page in ~6 s). A test that asserts on
  // scene STATE can afford swiftshader; a screenshot cannot.
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820', '--headless=new', URL,
], { stdio: 'ignore' });

let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
};
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP'])
  process.on(sig, () => { kill(); process.exit(130); });

// 320 tries = 80 s: the bundle is 30 MB and the box may be busy. findPage's
// failure carries its evidence — see tools/cdp.mjs.
const targetWs = () => findPage(CDP, { tries: 320, label: 'ow_shot' });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', (d) => {
      const m = JSON.parse(d.toString());
      if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
    });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise((ok) => {
        const i = ++id; pend.set(i, ok);
        ws.send(JSON.stringify({ id: i, method, params }));
      }),
      close: () => ws.close(),
    }));
    ws.on('error', rej);
  });
}

const evalJS = async (cdp, expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true });
  return r.result && r.result.result ? r.result.result.value : undefined;
};

(async () => {
  const cdp = await connect(await targetWs());
  await cdp.send('Runtime.enable');

  // READINESS: use a signal the runtime ACTUALLY publishes. The first version of
  // this loop polled `window.scene`, which play3d does not expose — so it timed out
  // on a page that was fully loaded and rendering. Same failure family as the URL
  // matcher: the instrument asked for something that never existed and reported the
  // world broken. `window.SIM` is the runtime's own probe surface (CLAUDE.md's
  // browser-verify doctrine names it), and SIM.pos() answers once the world is
  // walkable — which is exactly "there is something to photograph".
  let ready = false, saw = null;
  for (let i = 0; i < WAIT * 4; i++) {
    saw = await evalJS(cdp, `(() => {
      try {
        if (!window.SIM || typeof SIM.pos !== 'function') return null;
        const p = SIM.pos();
        if (!p || !isFinite(p.x)) return null;
        return JSON.stringify({ pos: [+p.x.toFixed(1), +p.y.toFixed(1), +p.z.toFixed(1)],
          zone: (SIM.zone && SIM.zone()) || null,
          sky: !!document.querySelector('canvas') });
      } catch (e) { return 'ERR ' + e.message; }
    })()`);
    if (saw && saw.startsWith('{')) { ready = true; break; }
    await sleep(250);
  }
  if (!ready) { console.error('scene never populated; last state:', saw); kill(); process.exit(2); }
  await sleep(1200);                       // let a couple of frames settle

  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  const b64 = shot.result && shot.result.data;
  if (!b64) { console.error('no screenshot data'); kill(); process.exit(3); }
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, Buffer.from(b64, 'base64'));
  console.log(`${OUT}  ${saw}`);
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
