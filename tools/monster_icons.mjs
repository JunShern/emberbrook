#!/usr/bin/env node
/* monster_icons.mjs — WRITE THE TURN-QUEUE FOE ICONS OUT OF THE ACTUAL MODELS.
 *
 *   node tools/monster_icons.mjs --port 3000            # write the six
 *   node tools/monster_icons.mjs --check                # measure hue agreement only
 *
 * THE DEFECT (battle-presentation-inventory §7.3). The turn-order rail draws each
 * foe as a 16 px hand-drawn sprite and the sprites contradict the bodies: duskpad's
 * was salmon-pink over a grey wolf, bramble shade's mint green over a dark
 * root-ball, scree shell's green over a red crab. A player picks a target from a
 * rail whose colours lie.
 *
 * THE FIX IS THE PIPELINE, NOT THE PIXELS. This drives
 * docs/qa/battle-monsters/icons.html — the same GLBs, the same MON heights, the
 * same light rig the arena uses — and writes the result over
 * public/assets/monsters/placeholder/<id>.png. That path is deliberately unchanged:
 * `monsterUrl()` in battle_turnbased.js and the claim in tools/build-static.mjs
 * both name it, and an icon fix is not worth a rename across three files.
 *
 * IT PROVES AGREEMENT AND DOES NOT ASSERT IT. --check reports each icon's
 * area-weighted mean hue against the model's, which is the audit's own proposed
 * measure ("icon and model matched by measured mean hue"), and is the number that
 * would have caught the salmon wolf the day it shipped.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const SIZE = parseInt(arg('size', '256'), 10);
const OUTDIR = join(ROOT, arg('outdir', 'public/assets/monsters/placeholder'));
const CHECK = process.argv.includes('--check');
const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/docs/qa/battle-monsters/icons.html?size=${SIZE}&v=${Date.now()}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'monster-icons-profile');
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--headless=new',
  '--window-size=1200,700', URL,
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
      send: (m, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok);
        ws.send(JSON.stringify({ id: i, method: m, params: p })); }),
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
  const cdp = await connect(await findPage(CDP, { tries: 240, label: 'monster_icons', match: /icons\.html/ }));
  await cdp.send('Runtime.enable');
  let ready = null;
  for (let i = 0; i < 160; i++) {
    ready = await evalJS(cdp, `window.__icons && window.__icons.ready ? Object.keys(window.__icons.png).join(',') : null`);
    if (ready) break;
    await sleep(250);
  }
  if (!ready) { console.error('icons page never became ready'); kill(); process.exit(2); }
  const ids = ready.split(',');
  mkdirSync(OUTDIR, { recursive: true });
  for (const id of ids) {
    const url = await evalJS(cdp, `window.__icons.png[${JSON.stringify(id)}]`);
    const b = Buffer.from(String(url).replace(/^data:image\/png;base64,/, ''), 'base64');
    if (!CHECK) writeFileSync(join(OUTDIR, id + '.png'), b);
    console.log(`${CHECK ? 'would write' : 'wrote'}  ${id}.png  ${b.length} bytes`);
  }
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
