#!/usr/bin/env node
/* light_shot.mjs — PHOTOGRAPH A CHARACTER STANDING IN ANY SCENE, over CDP.
 *
 *   node tools/light_shot.mjs --scene emb-cine --shot square --out a.png
 *   node tools/light_shot.mjs --scene ow-valley --rt 1 --out b.png
 *   node tools/light_shot.mjs --scene del-cine --shot gate \
 *        --expr 'AMBIENT.intensity=0' --out c.png
 *
 * WHY THIS EXISTS. ow_shot.mjs and ow_diag.mjs both hardcode `rt=1`, so neither
 * can photograph a BAKED-PLATE town — which is exactly where the character
 * lighting has to be judged, because in a cine bundle the character is the ONLY
 * lit thing on screen (every town mesh renders with colorWrite:false). This is
 * the same CDP pattern, with the scene, the shot, the standing place and an
 * arbitrary setup expression all on the command line, so a lighting hypothesis
 * costs a command instead of a commit to coordinator-owned play3d.html.
 *
 * IT PROVES IT PHOTOGRAPHED A CHARACTER. `--paint` runs SIM.paint({tested:true})
 * before the capture and prints the magenta pixel count: a frame with zero
 * character pixels is a frame that cannot say anything about character lighting,
 * and this tool must not let that be mistaken for "the lighting looks flat".
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
const OUT = arg('out', 'docs/qa/charlight/shot.png');
const SCENE = arg('scene', 'emb-cine');
const SHOT = arg('shot', null);
const AT = arg('at', null);                 // "x,z" — otherwise the shot's own spawn
const NEAR = arg('near', null);             // metres from the camera along its own aim
const CROP = arg('crop', null);             // "W,H" — a zoom crop centred on the character
const SETTLE = parseInt(arg('settle', '1000'), 10);   // ms before the capture (story banners run 5 s)
const EXPR = arg('expr', null);
const RT = arg('rt', null);
const EXTRA = arg('q', '');                 // extra query string, e.g. 'owlight=0'
const PAINT = process.argv.includes('--paint');
const PORT = parseInt(arg('port', '3000'), 10);
const CDP = parseInt(arg('cdp', '0'), 10) || await freePort();
const WAIT = parseInt(arg('wait', '40'), 10);
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const URL = `http://localhost:${PORT}/play.html?scene=${SCENE}&nomusic=1` +
            (RT ? `&rt=${RT}` : '') + (EXTRA ? '&' + EXTRA : '') + `&v=${Date.now()}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'light-shot-profile-' + process.pid);
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820', '--headless=new', URL], { stdio: 'ignore' });

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
    ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); }),
      close: () => ws.close() }));
    ws.on('error', rej);
  });
}
const evalJS = async (cdp, expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  const d = r.result || {};
  if (d.exceptionDetails) return 'ERR ' + JSON.stringify(d.exceptionDetails.exception && d.exceptionDetails.exception.description || d.exceptionDetails.text);
  return d.result ? d.result.value : undefined;
};

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'light_shot' }));
  await cdp.send('Runtime.enable');
  let ready = false, saw = null;
  for (let i = 0; i < WAIT * 4; i++) {
    saw = await evalJS(cdp, `(()=>{ try{
      if(!window.SIM||typeof SIM.pos!=='function') return null;
      const p=SIM.pos(); if(!p||!isFinite(p.x)) return null;
      if(!SIM.char().model) return null;                      // the character IS the subject
      return JSON.stringify({scene:SIM.scene(), pos:[+p.x.toFixed(1),+p.y.toFixed(1),+p.z.toFixed(1)]});
    }catch(e){ return 'ERR '+e.message; } })()`);
    if (saw && saw.startsWith('{')) { ready = true; break; }
    await sleep(250);
  }
  if (!ready) { console.error('scene never populated; last state:', saw); kill(); process.exit(2); }

  if (SHOT) {
    const r = await evalJS(cdp, `SIM.shot(${JSON.stringify(SHOT)}).then(r=>JSON.stringify(r))`);
    if (!r || r.startsWith('ERR') || r.includes('error')) { console.error('shot failed:', r); kill(); process.exit(4); }
    await sleep(600);
    // stand where the shot's own spawn says, unless overridden
    const place = AT
      ? `SIM.tp(${AT.split(',').map(Number).join(',')})`
      : NEAR
      // WALK THE CHARACTER TOWARD THE LENS. A town shot frames a whole district, so
      // the spawn point can put the figure 40 m out at 12 px tall — a frame that
      // cannot answer a question about how a FACE is lit. This marches along the
      // camera's own aim ray and takes the first standing place the walk network
      // offers, so the closeness is the scene's, not a coordinate someone typed.
      ? `(()=>{const c=SIM.cine().baked, m2r=p=>[p[0],p[2],-p[1]];
           const P0=m2r(c.pos), A=m2r(c.aim);
           let d=[A[0]-P0[0],A[1]-P0[1],A[2]-P0[2]];
           const L=Math.hypot(d[0],d[1],d[2]); d=d.map(v=>v/L);
           for(let n=${Number(NEAR)}; n<=${Number(NEAR)}+26; n+=1.0){
             const x=P0[0]+d[0]*n, y=P0[1]+d[1]*n, z=P0[2]+d[2]*n;
             if(!SIM.walkFloors(x,z).length) continue;
             const p=SIM.tpY(x,z,y); const q=SIM.paint({tested:true});
             if(q.onScreen && q.magentaPixels>60) return {at:p, n:+n.toFixed(1), px:q.magentaPixels};
           }
           return {at:SIM.pos(), n:null, px:0};})()`
      : `(()=>{const s=SIM.cine()&&SIM.cine().baked&&SIM.cine().baked.spawn; return s?SIM.place(s):SIM.pos();})()`;
    console.log('  placed', await evalJS(cdp, `JSON.stringify(${place})`));
  } else if (AT) {
    console.log('  placed', await evalJS(cdp, `JSON.stringify(SIM.tp(${AT.split(',').map(Number).join(',')}))`));
  }
  // the expr may be async (SIM.shot() returns a promise); always await it
  if (EXPR) console.log('  expr ->', await evalJS(cdp,
    `Promise.resolve((()=>{ try{ return (${EXPR}); }catch(e){ return 'ERR '+e.message; } })())
       .then(v=>JSON.stringify(v===undefined?'ok':v)).catch(e=>'ERR '+e.message)`));
  await evalJS(cdp, `JSON.stringify(SIM.tick(1))`);
  await sleep(SETTLE);
  await evalJS(cdp, `JSON.stringify(SIM.tick(1))`);
  await sleep(400);
  // RE-ASSERT THE SHOT AND THE STANDING PLACE, LAST. SIM.tick() runs sgTick, and
  // sgTick's whole job is to CORRECT the camera to whichever region the player is
  // standing in — so a --shot chosen before the tick is a request, not a state.
  // Two runs of the same command landed on two different cameras until this
  // existed (measured: del-cine weave, 452 char px one run and 0 the next).
  // tpY re-syncs the depth quad and renders, so no tick is needed to make it real.
  if (SHOT) {
    const re = AT ? `.then(()=>{const a=[${AT.split(',').map(Number).join(',')}];
                       // tp, NOT tpY: tpY only moves the player if walkFloors finds a
                       // floor under the point, so it silently no-ops while another
                       // lane is mid-write on the bundle's scene.glb and the A/B pair
                       // ends up photographing two different places.
                       return SIM.tp(a[0],a[1],a.length>2?a[2]:null);})` : '';
    await evalJS(cdp, `SIM.shot(${JSON.stringify(SHOT)})${re}.then(()=>1)`);
    await sleep(700);
  }
  const geom = JSON.parse(await evalJS(cdp, `JSON.stringify((()=>{const q=SIM.paint({tested:true});
      const cv=document.querySelector('canvas');
      return {shot:window.__cine?window.__cine.cam:null, pos:SIM.pos(),
              px:q.magentaPixels, ndc:q.charNdc, onScreen:q.onScreen,
              cw:cv.clientWidth, chh:cv.clientHeight,
              ox:cv.getBoundingClientRect().left, oy:cv.getBoundingClientRect().top};})())`));
  console.log('  live', JSON.stringify({ shot: geom.shot, px: geom.px, ndc: geom.ndc,
    pos: [+geom.pos.x.toFixed(1), +geom.pos.y.toFixed(1), +geom.pos.z.toFixed(1)] }));
  if (PAINT && geom.px === 0)
    console.warn('  WARNING: zero character pixels — this frame cannot say anything about character lighting');

  let clip;
  if (CROP) {
    const [cw, chh] = CROP.split(',').map(Number);
    const sx = geom.ox + (geom.ndc[0] * 0.5 + 0.5) * geom.cw;
    const sy = geom.oy + (1 - (geom.ndc[1] * 0.5 + 0.5)) * geom.chh;
    clip = { x: Math.max(0, Math.round(sx - cw / 2)), y: Math.max(0, Math.round(sy - chh / 2)),
             width: cw, height: chh, scale: 2 };
  }
  const shot = await cdp.send('Page.captureScreenshot', clip ? { format: 'png', clip } : { format: 'png' });
  const b64 = shot.result && shot.result.data;
  if (!b64) { console.error('no screenshot data'); kill(); process.exit(3); }
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, Buffer.from(b64, 'base64'));
  console.log(`${OUT}  ${saw}`);
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
