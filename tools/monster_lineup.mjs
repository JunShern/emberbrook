#!/usr/bin/env node
/* monster_lineup.mjs — PHOTOGRAPH EVERY MONSTER IN ONE FRAME.
 *
 *   node tools/monster_lineup.mjs --out docs/qa/battle-monsters/lineup-before.png
 *   node tools/monster_lineup.mjs --dir monsters/3d-graded/ --out .../lineup-after.png
 *
 * WHY. `docs/plans/battle-presentation-inventory.md` §8 says "six creatures, at
 * least four art directions" and nobody could SEE it: the game never puts more
 * than three of them on screen at once, never at the same distance, and never
 * under the same plate. An incoherence you cannot photograph is an assertion.
 * This drives docs/qa/battle-monsters/lineup.html — which reads its light rig,
 * its zone palette and its per-monster target height off the SHIPPING
 * `window.BattleStage3D` (CFG / ZONES / MON) rather than keeping a second copy —
 * and writes one PNG plus the measured bodies.
 *
 * IT WAITS FOR THE PAGE'S OWN READY FLAG (`window.__lineup.ready`), which is set
 * after the last GLB has parsed and been staged, so a slow parse cannot produce a
 * photograph of a half-empty row. Chrome goes through tools/cdp.mjs (free port,
 * own profile) and is reaped by its own --user-data-dir on every exit path.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const OUT = arg('out', 'docs/qa/battle-monsters/lineup.png');
const DIR = arg('dir', 'monsters/3d/');
const ZONE = arg('zone', 'meadow');
const IDS = arg('ids', '');
const CHARS = arg('chars', '');   // append party rigs — the ratified reference
const SPAN = arg('span', ''), DIST = arg('dist', '');
const W = parseInt(arg('w', '1800'), 10), H = parseInt(arg('h', '620'), 10);
const PORT = parseInt(arg('port', '3000'), 10);
const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/docs/qa/battle-monsters/lineup.html?dir=${encodeURIComponent(DIR)}` +
            `&zone=${ZONE}&w=${W}&h=${H}${IDS ? '&ids=' + encodeURIComponent(IDS) : ''}${CHARS ? '&chars=' + encodeURIComponent(CHARS) : ''}${SPAN ? '&span=' + SPAN : ''}${DIST ? '&dist=' + DIST : ''}&v=${Date.now()}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'monster-lineup-profile');
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  `--window-size=${W + 40},${H + 120}`, '--headless=new', URL,
], { stdio: 'ignore' });

let closing = false;
const kill = () => { if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { } };
process.on('exit', kill);
for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => { const m = JSON.parse(d.toString());
      if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok);
        ws.send(JSON.stringify({ id: i, method, params })); }),
      close: () => ws.close(),
    }));
    ws.on('error', rej);
  });
}
const evalJS = async (cdp, e) => {
  const r = await cdp.send('Runtime.evaluate', { expression: e, returnByValue: true });
  return r.result && r.result.result ? r.result.result.value : undefined;
};

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 240, label: 'monster_lineup', match: /lineup\.html/ }));
  await cdp.send('Runtime.enable');
  let meta = null;
  for (let i = 0; i < 160; i++) {
    meta = await evalJS(cdp, `window.__lineup && window.__lineup.ready ? JSON.stringify(window.__lineup.meta) : null`);
    if (meta) break;
    await sleep(250);
  }
  if (!meta) {
    const why = await evalJS(cdp, `String(document.body && document.body.innerHTML || '').slice(0,300)`);
    console.error('lineup never became ready. page said:', why); kill(); process.exit(2);
  }
  await sleep(400);
  // THE CANVAS IS THE PICTURE, not the viewport: toDataURL off the page's own
  // preserveDrawingBuffer render is byte-exact and independent of window chrome.
  const data = await evalJS(cdp, `window.__lineup.shot()`);
  const b64 = String(data).replace(/^data:image\/png;base64,/, '');
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, Buffer.from(b64, 'base64'));
  // THE SIDECAR. Each body's measured box AND its own projected x as a fraction of
  // frame width, so tools/monster_board.py can burn a caption UNDER THE BODY rather
  // than under the column it happens to share with perspective. A picture whose
  // labels are guessed is a picture that mislabels one row and gets believed.
  writeFileSync(OUT.replace(/\.png$/, '') + '.json', meta);
  console.log(OUT);
  console.log(JSON.stringify(JSON.parse(meta), null, 1));
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
