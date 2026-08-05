#!/usr/bin/env node
/* hush_shot.mjs — photograph THE HUSH, with and without, through the real runtime.
 *
 *   node tools/hush_shot.mjs --port 3000 --cams square,pondlane,waystone
 *   node tools/hush_shot.mjs --cams square --grades "0.34,0.80,0.90,0.42,196,1.55|0.20,..."
 *
 * WHY THIS EXISTS. The hush is a taste decision on a pre-rendered plate. Numbers
 * can tell you the warm sources went out; only a pair of frames can tell you
 * whether it reads as held breath or as a bug. This captures the SAME camera twice
 * — clean and hushed — in one browser session, so the only thing that differs
 * between the two files is the effect. It also takes a cut-in up in the second
 * frame on request (--cutin), because "the portraits stay warm" is the whole
 * effect and a pair that does not show a portrait cannot show it.
 *
 * It borrows ow_shot.mjs's CDP pattern (own free port, own profile, cleaned on
 * every exit path) through tools/cdp.mjs rather than inventing a fifth harness.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';
import { mkArg } from './argv.mjs';

// `--k v` AND `--k=v` (tools/argv.mjs): the bare indexOf form silently

// ignored the `=` spelling and used the DEFAULT instead.

const { arg } = mkArg(process.argv);
const PORT = parseInt(arg('port', '3000'), 10);
const SCENE = arg('scene', 'emb-cine');
const CAMS = arg('cams', 'square').split(',').map(s => s.trim()).filter(Boolean);
const OUTDIR = arg('outdir', 'docs/qa/hush');
const CUTIN = arg('cutin', '') || '';         // a dialogue node id to play in the hushed frame
const GRADES = (arg('grades', '') || '').split('|').map(s => s.trim()).filter(Boolean);
const CDP = parseInt(arg('cdp', '0'), 10) || await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play.html?scene=${SCENE}&nomusic=1&nostory=1&v=${Date.now()}`;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'hush-shot-profile');
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check',
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
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { kill(); process.exit(130); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); }),
      close: () => ws.close(),
    }));
    ws.on('error', rej);
  });
}
const ev = async (cdp, e) => {
  const r = await cdp.send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  if (r.result && r.result.exceptionDetails)
    return 'EXC ' + (r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text);
  return r.result?.result?.value;
};
const shoot = async (cdp, path) => {
  const s = await cdp.send('Page.captureScreenshot', { format: 'png' });
  if (!s.result?.data) throw new Error('no screenshot data for ' + path);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, Buffer.from(s.result.data, 'base64'));
  console.log('  ' + path);
};

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'hush_shot' }));
  await cdp.send('Runtime.enable');

  // Readiness: the runtime's own probe surface, not a timer (ow_shot's lesson).
  let ready = false, saw = null;
  for (let i = 0; i < 160; i++) {
    saw = await ev(cdp, `(()=>{try{ if(!window.SIM||!SIM.pos)return null; const p=SIM.pos();
      return (isFinite(p.x)&&window.Hush)?JSON.stringify({pos:[+p.x.toFixed(1),+p.z.toFixed(1)],hush:Hush.debug()}):null;
    }catch(e){return 'ERR '+e.message}})()`);
    if (saw && saw.startsWith('{')) { ready = true; break; }
    await sleep(250);
  }
  if (!ready) { console.error('never ready; last state:', saw); kill(); process.exit(2); }
  console.log('boot ' + saw);
  // The FF7 exit arrows are DOM, so the canvas grade never touches them and they
  // sit over both frames as bright orange. They are identical in both, but they are
  // the loudest warm thing in a picture whose whole subject is warmth — off.
  if (arg('markers', '0') === '0')
    await ev(cdp, `(()=>{try{MARKERS_ON=false;var b=document.getElementById('exit-markers');
      if(b)b.style.display='none';}catch(e){} return 1;})()`);
  await sleep(1500);

  // THE PLAYER HAS TO BE IN THE SHOT. SIM.shot() cuts the camera, but sgTick's
  // bands cut it straight back to whichever shot owns the ground she is standing
  // on — the first run of this tool asked for `square` and photographed `woodroad`
  // with a cheerful success message. Each camera in cine.json carries its own
  // `spawn` (the walk landmark the solver aimed at); standing her there first is
  // what makes the requested shot the shot that stays up.
  const spawns = JSON.parse(await ev(cdp,
    `fetch('assets/scenes/${SCENE}/cine.json').then(r=>r.json())
      .then(j=>JSON.stringify(Object.fromEntries((j.cameras||[]).map(c=>[c.id,c.spawn||null]))))`) || '{}');

  for (const cam of CAMS) {
    const sp = spawns[cam];
    if (sp) await ev(cdp, `JSON.stringify(SIM.tp(${sp[0]},${sp[2]},${sp[1]}))`);
    const r = await ev(cdp, `SIM.shot(${JSON.stringify(cam)}).then(x=>JSON.stringify(x))`);
    await sleep(600);
    const live = await ev(cdp, `(SIM.cine()||{}).shot`);
    console.log('\n' + cam + ' -> ' + r + '  live=' + live);
    if (String(r).includes('error')) continue;
    if (live !== cam) console.log('  WARN the live shot is ' + live + ', not ' + cam + ' — the frame is not what was asked for');
    await sleep(1800);
    await ev(cdp, `Hush.off(0)`); await sleep(500);
    await shoot(cdp, join(OUTDIR, `${cam}-clear.png`));
    if (GRADES.length) {
      for (let i = 0; i < GRADES.length; i++) {
        const g = GRADES[i].split(',').map(Number);
        await ev(cdp, `(()=>{const c=document.querySelector('#s canvas');c.style.transition='none';
          c.style.filter='saturate(${g[0]}) brightness(${g[1]}) contrast(${g[2]}) sepia(${g[3]}) hue-rotate(${g[4]}deg) saturate(${g[5]})';
          window.__hush={on:true,key:[0.55,0.65,0.88],sky:[0.44,0.55,0.82],grd:[0.20,0.24,0.34],keyMul:0.55,fillMul:0.85,ambMul:1.10};
          SIM.relight&&SIM.relight(); return 1;})()`);
        await sleep(500);
        await shoot(cdp, join(OUTDIR, `${cam}-cand${i + 1}.png`));
      }
      await ev(cdp, `Hush.off(0)`);
    }
    await ev(cdp, `Hush.on(0)`); await sleep(1200);   // instant apply, but give the compositor a frame
    await shoot(cdp, join(OUTDIR, `${cam}-hush.png`));
    console.log('  charlight ' + await ev(cdp, `JSON.stringify({hush:__charlight.hush,key:__charlight.intens,gain:__charlight.gain})`));
    if (CUTIN) {
      // NOT awaited: Dialogue.play() resolves when the CONVERSATION ends, i.e. when
      // a player presses a key, so `awaitPromise:true` on it hangs the harness for
      // ever. Fire it and photograph the window that opens. (Cost of learning this
      // the other way: one 8-minute stuck run.)
      await ev(cdp, `(()=>{Dialogue.play(${JSON.stringify(CUTIN)});return 1})()`);
      await sleep(1600);
      await shoot(cdp, join(OUTDIR, `${cam}-hush-cutin.png`));
      await ev(cdp, `(()=>{try{Dialogue.close&&Dialogue.close()}catch(e){}return 1})()`);
      await sleep(400);
    }
    await ev(cdp, `Hush.off(0)`); await sleep(400);
  }
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
