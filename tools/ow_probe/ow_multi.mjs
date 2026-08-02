#!/usr/bin/env node
/* ow_multi.mjs — multi-frame probe harness for the overworld art lane.
 *
 *   node ow_multi.mjs --spec shots.json
 *
 * ow_shot/ow_diag each launch their own Chrome. This lane needs the SAME camera
 * photographed under N different material treatments, and Chrome is the contended
 * resource on this box tonight (two playthrough gauntlets live). One launch, many
 * frames: each spec entry is {out, expr} and expr runs against the live scene graph
 * exactly the way ow_diag's --expr does (globals R/scene/dl/AMBIENT/cam/SIM/ORBIT
 * are reachable — play3d's main script is a classic script).
 *
 * Nothing here ships; it exists so a hypothesis costs a command line.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '../cdp.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const SPEC = JSON.parse(readFileSync(arg('spec'), 'utf8'));
const SCENE = arg('scene', 'ow-valley');
const PORT = parseInt(arg('port', '3000'), 10);
const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const W = arg('w', '1400'), H = arg('h', '820');
const URL = `http://localhost:${PORT}/play.html?scene=${SCENE}&rt=1&owsky=1&owlight=1&nomusic=1&v=${Date.now()}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = join(process.env.TMPDIR || '/tmp', 'ow-multi-profile');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  `--window-size=${W},${H}`, '--headless=new', URL], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) {}
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) {} };
process.on('exit', kill);
for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130); });

function connect(url) { return new Promise((res, rej) => {
  const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
  const pend = new Map(); let id = 0;
  ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  ws.on('open', () => res({ send: (m, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method: m, params: p })); }), close: () => ws.close() }));
  ws.on('error', rej); }); }

const evalJS = async (cdp, expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  const d = r.result || {};
  if (d.exceptionDetails) return 'EXC ' + (d.exceptionDetails.exception?.description || JSON.stringify(d.exceptionDetails));
  return d.result ? d.result.value : undefined;
};

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 400, label: 'ow_multi' }));
  await cdp.send('Runtime.enable');
  let ok = false;
  for (let i = 0; i < 240; i++) {
    if (await evalJS(cdp, `(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`) === true) { ok = true; break; }
    await sleep(250);
  }
  if (!ok) { console.error('scene never populated'); kill(); process.exit(2); }
  // hide the HUD + music nag so the plates are clean pictures
  await evalJS(cdp, `(()=>{const h=document.getElementById('h'); if(h)h.style.display='none';
    for(const el of document.querySelectorAll('body *')) { const t=(el.textContent||''); if(t.indexOf('music off')>=0 && el.children.length<3) el.style.display='none'; }
    // __tp: SIM.tp(x,z) raycasts from the CURRENT P.y, so teleporting across a
    // 20 m elevation change silently leaves the body at the old height (measured:
    // every corridor pose came back y=26.4). Take the highest floor under the cell.
    window.__tp=(x,z)=>{ const fs=SIM.floors(x,z); const y=(fs&&fs.length)?Math.max.apply(null,fs):null;
      return SIM.tp(x,z,y); };
    return 1})()`);
  for (const f of (arg('inject', '') ? arg('inject').split(',') : [])) {
    const r = await evalJS(cdp, readFileSync(f, 'utf8') + '\n;1');
    console.log(`INJECT ${f} -> ${r}`);
  }
  await sleep(1200);

  for (const s of SPEC) {
    if (s.expr) {
      const r = await evalJS(cdp, `(()=>{try{ ${s.expr}; return 'ok' }catch(e){ return 'EXC '+e.message }})()`);
      if (String(r).startsWith('EXC')) { console.error(`[${s.out}] expr failed: ${r}`); continue; }
    }
    await sleep(s.settle || 900);
    // the music nag mounts late; hide it immediately before every capture
    await evalJS(cdp, `(()=>{for(const el of document.querySelectorAll('body *')){const t=(el.textContent||'');if(t.indexOf('music off')>=0&&el.children.length<3)el.style.display='none';}const h=document.getElementById('h');if(h)h.style.display='none';return 1})()`);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
    const b64 = shot.result && shot.result.data;
    if (!b64) { console.error('no data for ' + s.out); continue; }
    mkdirSync(dirname(s.out), { recursive: true });
    writeFileSync(s.out, Buffer.from(b64, 'base64'));
    const info = await evalJS(cdp, `JSON.stringify({p:SIM.pos(),zone:SIM.zone(),yaw:+window.ORBIT.yaw.toFixed(2),dist:window.ORBIT.dist,pitch:+window.ORBIT.pitch.toFixed(2)})`);
    console.log(`WROTE ${s.out}  ${info}${s.report ? '  report=' + await evalJS(cdp, `JSON.stringify(window.__report)`) : ''}`);
  }
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
