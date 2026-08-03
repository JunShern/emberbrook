#!/usr/bin/env node
/* look_probe.mjs — GO AND STAND WHERE THE PLAYTESTER FILED IT, AND LOOK.
 *
 *   node tools/playtest/look_probe.mjs --pos 69,0,-55 --yaws -1.5,0.4,1.4,2.4 \
 *        --out docs/qa/playtest/round7 --tag r7 --port 3000
 *
 * WHY THIS EXISTS. A playtest report is a PICTURE at a COORDINATE. Rounds 5–6 both
 * produced complaints ("out-of-bounds geometry", "camera clipped inside foliage")
 * that were wrong about the cause and right about the picture, and there was no way
 * to judge them except by opening a jpg from a run that had already gone stale — the
 * ow bundle is rebuilt by other lanes most nights, so LAST NIGHT'S FRAME IS NOT
 * EVIDENCE ABOUT TONIGHT'S GAME. This boots the real runtime, SIM.tp()s to the exact
 * coordinate from the report, and photographs a ring of yaws, so the report can be
 * re-judged against the build that is actually shipping.
 *
 * It answers WHERE as well as WHAT: the TP line prints the landed position, the
 * encounter zone and the ground height, which is what separates "the player was out
 * of bounds" from "the player was in bounds and the view is broken".
 *
 * Adapted from tools/ow_shot.mjs — same CDP pattern, OS-assigned port via freePort(),
 * own profile cleaned on every exit path, plus a hard self-expiry. Chrome boots at
 * about:blank and the game arrives by Page.navigate, which is round 4's key-storm
 * fix (a target Chrome opens FROM A URL repeats dispatched key events thousands of
 * times); the page matcher is set to about:blank to match, per cdp.mjs's rule that
 * an instrument which finds nothing must prove it could have found something.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '../cdp.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const POS = arg('pos', '69,0,-55').split(',').map(Number);
const YAWS = arg('yaws', '-1.5,-0.8,0,0.8,1.6,2.4,3.1,-2.3').split(',').map(Number);
const OUTDIR = arg('out', '/tmp/moorage');
const TAG = arg('tag', 'now');
const PORT = parseInt(arg('port', '3000'), 10);
const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1&v=${Date.now()}`;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'moorage-shot-profile');
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820', '--headless=new', 'about:blank',
], { stdio: 'ignore' });

let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
};
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { kill(); process.exit(130); });
setTimeout(() => { console.error('SELF-EXPIRY 420s'); kill(); process.exit(9); }, 420000).unref();

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', (d) => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise((ok) => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); }),
      close: () => ws.close(),
    }));
    ws.on('error', rej);
  });
}
const evalJS = async (cdp, expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  return r.result && r.result.result ? r.result.result.value : undefined;
};

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'look_probe', match: /about:blank/ }));
  await cdp.send('Runtime.enable'); await cdp.send('Page.enable');
  await cdp.send('Page.navigate', { url: URL });

  let ready = false, saw = null;
  for (let i = 0; i < 200; i++) {
    saw = await evalJS(cdp, `(()=>{try{ if(!window.SIM||typeof SIM.pos!=='function')return null;
      const p=SIM.pos(); if(!p||!isFinite(p.x))return null;
      return JSON.stringify({pos:[+p.x.toFixed(1),+p.y.toFixed(1),+p.z.toFixed(1)], zone:(SIM.zone&&SIM.zone())||null});
    }catch(e){return 'ERR '+e.message}})()`);
    if (saw && saw.startsWith('{')) { ready = true; break; }
    await sleep(300);
  }
  if (!ready) { console.error('scene never populated; last:', saw); kill(); process.exit(2); }
  await sleep(2000);

  mkdirSync(OUTDIR, { recursive: true });
  const land = await evalJS(cdp, `(()=>{const p=SIM.tp(${POS[0]},${POS[2]},${POS[1]});
    return JSON.stringify({landed:[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)],
      zone:SIM.zone(), ground:SIM.ground?SIM.ground(${POS[0]},${POS[2]},${POS[1]}):null})})()`);
  console.log('TP ->', land);

  for (const yaw of YAWS) {
    await evalJS(cdp, `(()=>{window.ORBIT.yaw=${yaw}; return 1})()`);
    await sleep(900);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
    const f = join(OUTDIR, `${TAG}-yaw${String(yaw).replace('.', 'p').replace('-', 'm')}.png`);
    writeFileSync(f, Buffer.from(shot.result.data, 'base64'));
    console.log('  ', f);
  }
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.stack); kill(); process.exit(1); });
