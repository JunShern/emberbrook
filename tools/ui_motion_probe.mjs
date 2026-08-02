#!/usr/bin/env node
// ui_motion_probe.mjs — MEASURE THE CURVE, do not photograph it.
//
// A CDP screenshot costs 200-300 ms on a 1920x1080 page, which is longer than
// most of the transitions in this UI; a strip shot that way returns identical
// frames of an already-arrived panel and proves nothing (tried, 2026-08-02).
// So the motion gate is a SERIES, sampled inside the page on its own rAF: for
// each frame, the wall clock and the computed style of the thing that is moving.
// If the numbers walk a decelerating ramp from 0 to 1, there is an easing curve;
// if they jump, there is not. That is a fact about the shipped CSS, not a guess
// from two pictures.
//
//   node tools/ui_motion_probe.mjs
import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, join, extname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.mp3': 'audio/mpeg' };

const port = await freePort();
const srv = createServer(async (req, res) => {
  const p = normalize(decodeURIComponent(req.url.split('?')[0]));
  const f = join(ROOT, p);
  if (!f.startsWith(ROOT)) return res.writeHead(403).end();
  let buf = null;
  try { buf = await readFile(f); } catch (e) { return res.writeHead(404).end(); }
  res.writeHead(200, { 'Content-Type': MIME[extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
  res.end(buf);
});
await new Promise(r => srv.listen(port, '127.0.0.1', r));

const CDP = await freePort();
const profile = join(process.env.TMPDIR || '/tmp', 'ui-motion-' + process.pid);
const chrome = spawn(process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`, '--no-first-run',
   '--no-default-browser-check', '--window-size=1600,900',
   `http://127.0.0.1:${port}/tools/ui_mock.html?view=menu&screen=root&nomusic=1`], { stdio: 'ignore' });
const kill = () => { try { chrome.kill('SIGKILL'); } catch (e) { } srv.close(); };
process.on('exit', kill);
try { execFileSync('osascript', ['-e', 'tell application "Google Chrome" to activate']); } catch (e) { }

let ws = null, seen = null;
for (let i = 0; i < 120 && !ws; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${CDP}/json/list`)).json();
    seen = list;
    const p = list.find(t => t.type === 'page' && /ui_mock/.test(t.url));
    if (p) ws = p.webSocketDebuggerUrl;
  } catch (e) { }
  if (!ws) await sleep(250);
}
if (!ws) { console.error('no ui_mock page; CDP saw', JSON.stringify(seen)); kill(); process.exit(2); }
const sock = new WebSocket(ws, { maxPayload: 64 * 1024 * 1024 });
const pend = new Map(); let id = 0;
sock.on('message', (raw) => { const m = JSON.parse(raw); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
await new Promise(r => sock.on('open', r));
const send = (method, params) => new Promise(ok => { const i = ++id; pend.set(i, ok); sock.send(JSON.stringify({ id: i, method, params: params || {} })); });
await send('Runtime.enable'); await send('Page.enable');
for (let i = 0; i < 120; i++) {
  const r = await send('Runtime.evaluate', { expression: 'document.documentElement.getAttribute("data-mock-ready")==="1"', returnByValue: true });
  if (r.result?.result?.value) break;
  await sleep(200);
}

// ---- probe 1: the pause menu's entrance ------------------------------------
const menu = await send('Runtime.evaluate', {
  awaitPromise: true, returnByValue: true, expression: `(async()=>{
    window.Menu.close();
    await new Promise(r=>setTimeout(r,400));
    const t0=performance.now(); window.Menu.open();
    const el=()=>document.querySelector('.ebui-veil>.ebui-panel');
    const out=[];
    await new Promise(done=>{
      const step=()=>{
        const e=el();
        if(e){const cs=getComputedStyle(e);
          out.push({t:+(performance.now()-t0).toFixed(0),op:+cs.opacity,tr:cs.transform,
                    dur:cs.transitionDuration,ease:cs.transitionTimingFunction});}
        if(performance.now()-t0<520) requestAnimationFrame(step); else done();
      };requestAnimationFrame(step);
    });
    return JSON.stringify(out.filter((_,i)=>i%2===0));
  })()` });

// ---- probe 2: the HP gauge — bar, chase bar and the numeral ----------------
const hp = await send('Runtime.evaluate', {
  awaitPromise: true, returnByValue: true, expression: `(async()=>{
    // drive the real menu roster gauge instead of the battle (no arena needed):
    // the KIT's gauge is what both surfaces render, so this measures the shared thing
    const GS=window.GS, v=GS.state.party.find(p=>p.id==='vesper');
    window.Menu.close(); await new Promise(r=>setTimeout(r,300));
    window.Menu.open(); await new Promise(r=>setTimeout(r,600));
    const g=document.querySelector('.mn-mem .eb-gauge');
    const cs=g?getComputedStyle(g.querySelector('.tk>i:not(.gh)')):null;
    const cg=g?getComputedStyle(g.querySelector('.tk>i.gh')):null;
    return JSON.stringify({
      band:g?g.className:null,
      fillDur:cs?cs.transitionDuration:null, fillEase:cs?cs.transitionTimingFunction:null,
      ghostDur:cg?cg.transitionDuration:null, ghostDelay:cg?cg.transitionDelay:null,
      ghostBg:cg?cg.backgroundColor:null,
      hasGhost:!!(g&&g.querySelector('.tk>i.gh')),
    });
  })()` });

console.log('--- pause menu entrance (t ms, opacity, transform) ---');
const rows = JSON.parse(menu.result.result.value);
for (const r of rows) console.log(String(r.t).padStart(4), r.op.toFixed(3), r.tr, '|', r.dur, r.ease);
console.log('\n--- the shared gauge, as computed in the page ---');
console.log(hp.result.result.value);
kill(); process.exit(0);
