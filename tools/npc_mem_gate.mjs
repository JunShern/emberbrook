#!/usr/bin/env node
/* npc_mem_gate.mjs — WHAT DOES ONE SCENE COST IN MEMORY, AND WHO IS HOLDING IT.
 *
 * Boots play3d in real Chrome on the REAL GPU, then reports the peak PHYSICAL
 * FOOTPRINT of the renderer and gpu-process. `--block` drops any set of URLs on
 * the way in (CDP Network.setBlockedURLs), so "who is holding it" is answered by
 * subtraction against instruments and not by reading the source.
 *
 * WHY PHYSICAL FOOTPRINT AND NOT `ps rss` (2026-08-03, the lesson that cost an
 * hour): on macOS `ps -o rss` counts shared and IOSurface-mapped pages, so it
 * reported ~2.7 GB for a page whose bundle had been BLOCKED — a figure that made
 * every A/B look flat and nearly buried the real cause. vmmap's "Physical
 * footprint" is what Activity Monitor shows and what the machine actually pays.
 * Calibration: an about:blank renderer is 27 MB by this metric and 103 MB by rss.
 *
 * WHAT IT FOUND. emb-cine booted at renderer 2867 MB + gpu-process 3379 MB =
 * 6.2 GB. Blocking js/npc.js dropped the renderer to 302 MB; blocking scene.glb,
 * the camera plates or three-mesh-bvh.js each moved it far less. npc.js was
 * calling GLTFLoader.load() once per PERSON on bodies carrying three 4096x4096
 * maps — 257 MB of decoded texture per instance, ten instances in Emberbrook,
 * four distinct files. See the fix at npc.js `modelMaster`.
 *
 *   node tools/npc_mem_gate.mjs --port=3000 --scene=emb-cine
 *   node tools/npc_mem_gate.mjs --port=3000 --scene=emb-cine --block=js/npc.js
 *   node tools/npc_mem_gate.mjs --port=3000 --scene=emb-cine --sw     (swiftshader)
 *
 * A NOTE ON THE HARNESS DEFAULT. cdp.mjs's chromeArgs({gpu:false}) forces
 * `--use-angle=swiftshader --disable-gpu`, which rasterises in the renderer on
 * the CPU: emb-cine idles at ~4 fps there and at ~120 fps on the real GPU. A
 * stall measured under `--sw` is the RASTERISER, not the game. This tool defaults
 * to the real GPU for exactly that reason.
 *
 * SELF-EXPIRY: the watchdog kills Chrome and exits non-zero on every path,
 * including SIGINT and an uncaught throw. Nothing here may be left running.
 */
import { spawn, execSync } from 'child_process';
import WebSocket from 'ws';
import { rmSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { freePort, findPage, killOrphans, chromeArgs, sweepStaleProfiles } from './cdp.mjs';

const A = Object.fromEntries(process.argv.slice(2).map(s => {
  const m = s.match(/^--([^=]+)(?:=(.*))?$/); return m ? [m[1], m[2] ?? '1'] : ['_', s];
}));
const PORT = +(A.port || 3000), SCENE = A.scene || 'emb-cine';
const GPU = A.sw !== '1', SECS = +(A.secs || 12);
const BLOCK = (A.block || '').split(',').filter(Boolean);
const BUDGET = A.budget ? +A.budget : null;      // MB; non-zero exit if exceeded
const PROFILE = join(tmpdir(), 'npcmem-profile-' + process.pid);

let chrome = null, ws = null, dead = false;
function reap(code) {
  if (dead) return; dead = true;
  try { if (ws) ws.close(); } catch (e) { }
  try { if (chrome && chrome.pid) process.kill(-chrome.pid, 'SIGKILL'); } catch (e) { }
  try { killOrphans(PROFILE); } catch (e) { }
  try { rmSync(PROFILE, { recursive: true, force: true, maxRetries: 2 }); } catch (e) { }
  if (code != null) process.exit(code);
}
const wd = setTimeout(() => { console.error('npc_mem_gate: EXPIRY watchdog fired'); reap(9); }, (SECS + 120) * 1000);
wd.unref?.();
for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => reap(9));
process.on('uncaughtException', e => { console.error(e); reap(9); });
process.on('unhandledRejection', e => { console.error(e); reap(9); });
process.on('exit', () => reap(null));

let idc = 0; const pend = new Map();
const send = (m, p = {}) => new Promise((res, rej) => {
  const id = ++idc; pend.set(id, { res, rej });
  ws.send(JSON.stringify({ id, method: m, params: p }));
  setTimeout(() => { if (pend.has(id)) { pend.delete(id); rej(new Error('cdp timeout ' + m)); } }, 60000);
});
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, timeout: 55000 }).catch(() => null);
  if (!r || r.exceptionDetails) return null;
  return r.result?.value;
}

/** Peak physical footprint, in MB, of this profile's renderer and gpu-process. */
function footprints() {
  let rend = 0, gpu = 0;
  try {
    const out = execSync(
      `ps ax -o pid,command | grep "user-data-dir=${PROFILE}" | grep -v "grep\\|zsh -c" || true`,
      { encoding: 'utf8' });
    for (const line of out.trim().split('\n').filter(Boolean)) {
      const pid = +line.trim().split(/\s+/)[0];
      const type = (line.match(/--type=(\S+)/) || [, 'browser'])[1];
      if (type !== 'renderer' && type !== 'gpu-process') continue;
      let mb = 0;
      try {
        const v = execSync(`vmmap --summary ${pid} 2>/dev/null | grep -i "Physical footprint:" | head -1`,
          { encoding: 'utf8' });
        const m = v.match(/([\d.]+)([KMG])/);
        if (m) mb = +m[1] * (m[2] === 'G' ? 1024 : m[2] === 'K' ? 1 / 1024 : 1);
      } catch (e) { /* the process exited between ps and vmmap */ }
      if (type === 'renderer') rend = Math.max(rend, mb); else gpu = Math.max(gpu, mb);
    }
  } catch (e) { }
  return { rend: Math.round(rend), gpu: Math.round(gpu) };
}

(async () => {
  sweepStaleProfiles('npcmem-profile-');
  const cport = await freePort();
  // about:blank first, so the block list is installed BEFORE the game page loads
  chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    chromeArgs({ port: cport, profile: PROFILE, url: 'about:blank', gpu: GPU, size: '1400,900', headed: false }),
    { detached: true, stdio: 'ignore' });
  ws = new WebSocket(await findPage(cport, { match: /about:blank/, label: 'npc_mem_gate' }),
    { maxPayload: 256 * 1024 * 1024 });
  await new Promise((r, j) => { ws.on('open', r); ws.on('error', j); });
  ws.on('message', d => {
    const m = JSON.parse(d);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result); }
  });
  await send('Runtime.enable'); await send('Page.enable'); await send('Network.enable');
  if (BLOCK.length) await send('Network.setBlockedURLs', { urls: BLOCK.map(b => '*' + b + '*') });
  await send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?scene=${SCENE}&nomusic=1` });

  let pr = 0, pg = 0;
  for (let i = 0; i < SECS; i++) {
    const f = footprints(); pr = Math.max(pr, f.rend); pg = Math.max(pg, f.gpu);
    await new Promise(r => setTimeout(r, 1000));
  }
  const st = await ev(`(()=>{try{
      const c = SIM.cine && SIM.cine();
      const people = (window.Npc && Npc.list) ? Npc.list() : [];
      return { shot: c && c.shot, plates: c ? c.cached.length : 0,
               figures: people.length, bodies: people.filter(p=>p.body==='model').length,
               bvh: SIM.bvh ? SIM.bvh().built : null };
    }catch(e){ return {e:String(e)} }})()`);

  console.log(`${SCENE}  gpu=${GPU ? 'REAL' : 'swiftshader'}  block=[${BLOCK.join(',') || '-'}]`);
  console.log(`  renderer ${pr} MB + gpu-process ${pg} MB = ${pr + pg} MB physical footprint`);
  console.log(`  page: ${JSON.stringify(st)}`);
  let code = 0;
  if (BUDGET) {
    const ok = pr + pg <= BUDGET;
    console.log(`  budget ${BUDGET} MB: ${ok ? 'PASS' : 'FAIL'}`);
    code = ok ? 0 : 1;
  }
  clearTimeout(wd); reap(code);
})().catch(e => { console.error('npc_mem_gate FAILED\n', e && e.stack || e); reap(1); });
