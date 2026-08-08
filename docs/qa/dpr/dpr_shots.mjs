/**
 * dpr_shots.mjs — CAPTURE LANE (docs/qa/dpr). Photographs the SAME viewpoint at
 * three main-renderer pixel ratios inside ONE Chrome driven at deviceScaleFactor 2,
 * so the PNG contains what a retina screen actually shows.
 *
 * Nothing in public/ is edited: the pixel ratio is applied at runtime through the
 * page's own top-level bindings (R = the WebGLRenderer, PFXRIG = the post-fx rig),
 * which a global Runtime.evaluate can see because play3d.html is a classic script.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '../../../tools/cdp.mjs';

const PORT = 3000, CDP = await freePort();
const OUTDIR = process.argv[2] || '/Users/junshernchan/projects/multiplayer-rpg/docs/qa/dpr';
const CW = 1344, CH = 756;                       // css viewport; #s is 100vw x 56.25vw
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const FPS_ONLY = process.env.FPS_ONLY === '1';   // re-measure the cost without re-shooting

const VIEWS = [
  { key: 'ow-ridge', scene: 'ow-valley',
    expr: `window.ORBIT.dist=4.5;window.ORBIT.pitch=0.14;SIM.tick&&SIM.tick(0.1)`, settle: 1800, fps: true },
  { key: 'del-lockhead', scene: 'del-cine',
    expr: `const _j=await fetch('assets/scenes/del-cine/cine.json').then(r=>r.json());const _c=_j.cameras.find(y=>y.id==='lockhead');if(_c&&_c.spawn)SIM.tp(_c.spawn[0],_c.spawn[2],_c.spawn[1]);window.__S=await SIM.shot('lockhead')`,
    settle: 2400, fps: true },
  { key: 'del-quay', scene: 'del-cine',
    expr: `const _j=await fetch('assets/scenes/del-cine/cine.json').then(r=>r.json());const _c=_j.cameras.find(y=>y.id==='quay-west');if(_c&&_c.spawn)SIM.tp(_c.spawn[0],_c.spawn[2],_c.spawn[1]);window.__S=await SIM.shot('quay-west')`,
    settle: 2400, fps: false },
];
const RATIOS = [1, 1.5, 2];

const urlFor = s => `http://localhost:${PORT}/play3d.html?scene=${s}&nomusic=1&nostory=1&v=${Date.now()}`;
const profile = join(process.env.TMPDIR || '/tmp', 'dpr-shots-profile');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  // UNCAP=1: take the vsync quantiser off, so a frame time is the RENDERER's and not
  // the display's. Without it every measurement lands on 8.3/16.6/25 ms and "60 fps"
  // can mean anything from 61 to 119.
  ...(process.env.UNCAP === '1' ? ['--disable-gpu-vsync', '--disable-frame-rate-limit'] : []),
  `--window-size=${CW},${CH + 120}`, '--headless=new', urlFor(VIEWS[0].scene)], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL') } catch (e) { }; killOrphans(profile); try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }) } catch (e) { } };
process.on('exit', kill); for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130) });

const CONSOLE = [];
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => {
      const m = JSON.parse(d.toString());
      if (m.method === 'Runtime.consoleAPICalled' && /error|warning/.test(m.params.type || ''))
        CONSOLE.push(m.params.type + ': ' + (m.params.args || []).map(a => a.value || a.description || '').join(' ').slice(0, 200));
      if (m.method === 'Runtime.exceptionThrown')
        CONSOLE.push('EXCEPTION: ' + ((m.params.exceptionDetails || {}).exception || {}).description);
      if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id) }
    });
    ws.on('open', () => res({
      send: (m, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method: m, params: p })) }),
      close: () => ws.close()
    }));
    ws.on('error', rej);
  });
}
const ev = async (cdp, e) => {
  const r = await cdp.send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  const d = r.result || {};
  if (d.exceptionDetails) return 'EXC ' + (d.exceptionDetails.exception?.description || JSON.stringify(d.exceptionDetails));
  return d.result ? d.result.value : undefined;
};
async function waitLive(cdp) {
  for (let i = 0; i < 400; i++) {
    if (await ev(cdp, `(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`) === true) return true;
    await sleep(250);
  }
  return false;
}

// THE PATCH. Installed fresh after every navigate (a page load wipes it).
const INSTALL = `
window.__dpr = function(pr){
  R.setPixelRatio(pr);                       // three re-runs setSize(W,H,false) itself
  try{
    if (typeof PFXRIG!=='undefined' && PFXRIG && PFXRIG.composer){
      PFXRIG.composer.setPixelRatio(pr);      // the composer RT is built at 1344x768: resize it too
      if (PFXRIG.ao) PFXRIG.ao.setSize(Math.max(2,Math.round(1344*pr*0.5)),
                                       Math.max(2,Math.round(768*pr*0.5)));  // ao_res 0.5, kept
    }
  }catch(e){}
  try{ SIM.px(4,4,1,1); }catch(e){}           // force one render through the shipped path
  return JSON.stringify({pr:R.getPixelRatio(), buf:[R.domElement.width,R.domElement.height],
    css:[innerWidth,innerHeight], devicePixelRatio:window.devicePixelRatio,
    pfx:(typeof PFXRIG!=='undefined'&&PFXRIG)?[PFXRIG.composer.renderTarget1.width,PFXRIG.composer.renderTarget1.height]:null,
    gl:(function(){try{const g=R.getContext();const x=g.getExtension('WEBGL_debug_renderer_info');
      return x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER)}catch(e){return 'n/a'}})()});
};
window.__fps = function(ms){ return new Promise(res=>{ const t=[]; let last=performance.now(); const t0=last;
  function tick(now){ t.push(now-last); last=now; if(now-t0<ms) requestAnimationFrame(tick); else res(JSON.stringify(t)); }
  requestAnimationFrame(tick); }); };
'installed';`;

const stats = a => {
  const s = [...a].sort((x, y) => x - y), q = p => s[Math.min(s.length - 1, Math.max(0, Math.round((s.length - 1) * p)))];
  return { n: s.length, medMs: +q(0.5).toFixed(2), p95Ms: +q(0.95).toFixed(2), maxMs: +q(1).toFixed(2),
           medFps: +(1000 / q(0.5)).toFixed(1), p5Fps: +(1000 / q(0.95)).toFixed(1) };
};

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'dpr_shots' }));
  await cdp.send('Runtime.enable');
  // RETINA. Everything below is captured at 2 device pixels per css pixel.
  await cdp.send('Emulation.setDeviceMetricsOverride',
    { width: CW, height: CH, deviceScaleFactor: 2, mobile: false });
  if (!await waitLive(cdp)) { console.error('never populated'); kill(); process.exit(2); }
  let cur = VIEWS[0].scene;
  await ev(cdp, INSTALL); await sleep(2500);
  const fpsTable = [];
  for (const v of VIEWS) {
    if (v.scene !== cur) {
      await cdp.send('Page.navigate', { url: urlFor(v.scene) });
      await sleep(1500);
      if (!await waitLive(cdp)) { console.error('scene never populated: ' + v.scene); continue; }
      cur = v.scene; await ev(cdp, INSTALL); await sleep(2500);
    }
    const r = await ev(cdp, `(async()=>{try{${v.expr}; return 'ok'}catch(e){return 'EXC '+e.message}})()`);
    if (String(r).startsWith('EXC')) { console.error(v.key, r); continue; }
    await sleep(v.settle);
    for (const pr of RATIOS) {
      const info = await ev(cdp, `window.__dpr(${pr})`);
      await sleep(1200);
      if (!FPS_ONLY) {
        const out = join(OUTDIR, `${v.key}-dpr${String(pr).replace('.', '_')}.png`);
        const shot = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
        const b64 = shot.result && shot.result.data;
        if (!b64) { console.error('no data', v.key, pr); continue; }
        mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, Buffer.from(b64, 'base64'));
        console.log(`WROTE ${out}  ${info}`);
      } else console.log(`SET ${v.key} ${info}`);
      if (v.fps) {
        await sleep(600);
        const raw = await ev(cdp, `window.__fps(10000)`);
        let arr = []; try { arr = JSON.parse(raw); } catch (e) { }
        arr = arr.slice(5);                       // drop the settling frames
        const st = stats(arr);
        fpsTable.push({ view: v.key, pr, ...st });
        console.log(`FPS ${v.key} dpr=${pr} ` + JSON.stringify(st));
      }
    }
  }
  mkdirSync(OUTDIR,{recursive:true}); writeFileSync(join(OUTDIR, 'fps.json'), JSON.stringify(fpsTable, null, 1));
  const uniq = [...new Set(CONSOLE)];
  console.log(uniq.length ? ('CONSOLE (' + uniq.length + '):\n  ' + uniq.join('\n  ')) : 'CONSOLE CLEAN');
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
