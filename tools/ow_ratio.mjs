/**
 * owlight.mjs — the lit/shadow ratio probe for the real-time scenes.
 *
 * ONE Chrome, one scene load, N configs. For each config it captures the frame
 * TWICE — dl.castShadow on and off — so "shadowed" is the engine's own shadow
 * pass and not a guessed patch. Reports mean luma of the masked pixels vs the
 * untouched ones, the ratio, the frame's percentiles, and the MEAN RGB of each
 * side so the terminator hue shift is a number too.
 *
 * node owlight.mjs --scene ow-valley --view corridor --configs <json> [--save dir]
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { PNG } from 'pngjs';
import { freePort, killOrphans, findPage } from './cdp.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const SCENE = arg('scene', 'ow-valley');
const PORT = parseInt(arg('port', '3000'), 10);
const SAVE = arg('save', '');
const QEXTRA = arg('q', '');
const CONFIGS = JSON.parse(readFileSync(arg('configs'), 'utf8'));
// HOW MUCH OF ITS LIGHT A PIXEL MUST LOSE TO COUNT AS SHADOWED. 0.22 is a
// penumbra, not a shadow: at the mask rig (no fill) a pixel that keeps 78% of
// its key is a pixel the player reads as LIT, and averaging it into the shadow
// side is what makes a frame with real black shadows still report ~2:1.
const MASKREL = parseFloat(arg('maskrel', '0.75'));
const VIEWS = JSON.parse(readFileSync(arg('views'), 'utf8'));
const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const url = s => `http://localhost:${PORT}/play3d.html?scene=${s}&nomusic=1&nostory=1${QEXTRA ? '&' + QEXTRA : ''}&v=${Date.now()}`;

const profile = join(process.env.TMPDIR || '/tmp', 'owlight-profile-' + process.pid);
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820', '--headless=new', url(SCENE)], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL') } catch (e) { }; try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }) } catch (e) { } };
process.on('exit', kill); for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130) });

function connect(u) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(u, { perMessageDeflate: false, maxPayload: 512 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); }),
      close: () => ws.close(),
    }));
    ws.on('error', rej);
  });
}
const evalJS = async (cdp, expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: `(async()=>{${expr}})()`, awaitPromise: true, returnByValue: true });
  if (r.result && r.result.exceptionDetails) return 'ERR ' + JSON.stringify(r.result.exceptionDetails.exception && r.result.exceptionDetails.exception.description);
  return r.result && r.result.result ? r.result.result.value : undefined;
};
const shot = async cdp => {
  const s = await cdp.send('Page.captureScreenshot', { format: 'png' });
  return Buffer.from(s.result.data, 'base64');
};

// ---- measurement -----------------------------------------------------------
// THE MASK IS TAKEN ONCE PER VIEW AND REUSED FOR EVERY CONFIG, and that is the
// whole reason this instrument can be trusted across a key sweep. Which pixels
// the shadow pass covers is GEOMETRY — it does not change when the key gets
// brighter. An absolute "darkened by more than 12/255" threshold, re-derived per
// config, does: at key x3 it admits every half-lit terminator pixel, the masked
// set grows from 10% of the frame to 17%, and the mean of a set that just gained
// its brightest members goes UP while the picture got more contrasty. The first
// sweep run here reported exactly that and it was an artefact of the instrument.
const luma = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
function maskFrom(bufOn, bufOff) {
  const A = PNG.sync.read(bufOn), B = PNG.sync.read(bufOff);
  const m = new Uint8Array(A.width * A.height);
  for (let y = 0; y < A.height; y++) for (let x = 0; x < A.width; x++) {
    const i = (A.width * y + x) << 2;
    const la = luma(A.data[i], A.data[i + 1], A.data[i + 2]);
    const lb = luma(B.data[i], B.data[i + 1], B.data[i + 2]);
    const rel = (lb - la) / Math.max(lb, 1);
    m[A.width * y + x] = rel > MASKREL ? 1 : (rel < 0.02 ? 2 : 0);   // 1 shadow, 2 lit, 0 penumbra
  }
  return { m, w: A.width, h: A.height };
}
function measure(bufOn, MASK) {
  const A = PNG.sync.read(bufOn);
  const y0 = 26, y1 = A.height - 40;
  let sMask = { n: 0, l: 0, r: 0, g: 0, b: 0 }, sLit = { n: 0, l: 0, r: 0, g: 0, b: 0 };
  const all = [];
  let tot = 0, satSum = 0;
  for (let y = y0; y < y1; y++) for (let x = 0; x < A.width; x += 2) {
    const i = (A.width * y + x) << 2;
    const ar = A.data[i], ag = A.data[i + 1], ab = A.data[i + 2];
    const la = luma(ar, ag, ab);
    all.push(la / 255); tot++;
    satSum += (Math.max(ar, ag, ab) - Math.min(ar, ag, ab)) / 255;
    const k = MASK.m[A.width * y + x];
    const t = k === 1 ? sMask : (k === 2 ? sLit : null);
    if (t) { t.n++; t.l += la; t.r += ar; t.g += ag; t.b += ab; }
  }
  all.sort((a, b) => a - b);
  const q = t => all[Math.min(all.length - 1, Math.floor(all.length * t))];
  const mk = s => s.n ? { n: s.n, L: s.l / s.n, rgb: [s.r / s.n, s.g / s.n, s.b / s.n] } : null;
  const M = mk(sMask), L = mk(sLit);
  const hueOf = c => { // b-g and g-r deltas tell warm/cool without a colour lib
    return { bg: +(c[2] - c[1]).toFixed(1), gr: +(c[1] - c[0]).toFixed(1) };
  };
  return {
    shadowPct: +(100 * sMask.n / tot).toFixed(1),
    shadowL: M ? +M.L.toFixed(1) : null, litL: L ? +L.L.toFixed(1) : null,
    ratio: M && L ? +(L.L / Math.max(M.L, 1e-6)).toFixed(3) : null,
    L05: +q(0.05).toFixed(3), L50: +q(0.5).toFixed(3), L95: +q(0.95).toFixed(3), L99: +q(0.99).toFixed(3),
    Lmin: +q(0.002).toFixed(3), chroma: +(satSum / tot).toFixed(3),
    shadowRGB: M ? M.rgb.map(v => +v.toFixed(1)) : null, litRGB: L ? L.rgb.map(v => +v.toFixed(1)) : null,
    shadowHue: M ? hueOf(M.rgb) : null, litHue: L ? hueOf(L.rgb) : null,
  };
}

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 400, label: 'owlight' }));
  await cdp.send('Runtime.enable');
  for (let i = 0; i < 300; i++) {
    const ok = await evalJS(cdp, `try{ return !!(window.SIM && SIM.pos() && isFinite(SIM.pos().x)); }catch(e){ return false; }`);
    if (ok === true) break; await sleep(250);
  }
  await sleep(1500);
  const rows = [];
  const MASKCFG = arg('maskcfg', '');
  for (const view of VIEWS) {
    // the page's camera lerps back to its own default between captures, so the
    // view is re-armed before EVERY frame, not once per view. A plate taken 3 s
    // after the expr is not the framing the expr asked for.
    await evalJS(cdp, `window.__V=()=>{ ${view.expr} };  window.__V(); return 1;`);
    await sleep(900);
    // the mask config: a deliberately high-contrast rig (bright key, no fill) so
    // the shadow footprint is detected at full strength, then thrown away.
    if (MASKCFG) await evalJS(cdp, readFileSync(MASKCFG, 'utf8') + '; return 1;');
    await sleep(700);
    const mOn = await shot(cdp);
    await evalJS(cdp, 'dl.castShadow=false; return 1;'); await sleep(500);
    const mOff = await shot(cdp);
    await evalJS(cdp, 'dl.castShadow=true; return 1;');
    const MASK = maskFrom(mOn, mOff);
    for (const cfg of CONFIGS) {
      const r0 = await evalJS(cdp, cfg.expr + '; return 1;');
      if (typeof r0 === 'string' && r0.startsWith('ERR')) { console.error(cfg.name, r0); }
      await sleep(700);
      const on = await shot(cdp);
      const m = measure(on, MASK);
      rows.push({ view: view.name, cfg: cfg.name, ...m });
      console.log(`${view.name.padEnd(14)} ${cfg.name.padEnd(26)} ratio ${String(m.ratio).padEnd(6)} lit ${String(m.litL).padEnd(6)} sh ${String(m.shadowL).padEnd(6)} sh% ${String(m.shadowPct).padEnd(5)} L05 ${m.L05} L50 ${m.L50} L99 ${m.L99} chr ${m.chroma}  shHue b-g ${m.shadowHue && m.shadowHue.bg} g-r ${m.shadowHue && m.shadowHue.gr} | litHue b-g ${m.litHue && m.litHue.bg} g-r ${m.litHue && m.litHue.gr}`);
      if (SAVE) { mkdirSync(SAVE, { recursive: true }); writeFileSync(join(SAVE, `${view.name}-${cfg.name}.png`), on); }
    }
  }
  if (SAVE) writeFileSync(join(SAVE, 'rows.json'), JSON.stringify(rows, null, 1));
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.stack); kill(); process.exit(1); });
