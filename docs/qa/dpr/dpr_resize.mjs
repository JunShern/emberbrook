/**
 * dpr_resize.mjs — THE RESIZE PROOF for the dpr lane. Not a shipped gate;
 * a one-off receipt. Loads ow-valley at the SHIPPED ratio and asks, after each
 * event, whether the drawing buffer, the composer target, the GTAO buffer and the
 * FXAA texel still agree — and whether the frame still has pixels in it.
 *   1. CSS resizes (the only kind this page can get: setSize's updateStyle is
 *      false and the canvas is laid out by the stylesheet, so a window resize must
 *      change NOTHING about the buffer).
 *   2. A composer.setPixelRatio round trip 2 -> 1 -> 2 (what a dpr change or an
 *      instrument does): every derived size must follow, both ways.
 */
import { spawn } from 'child_process';
import { rmSync } from 'fs';
import { join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '../../../tools/cdp.mjs';

const PORT = process.env.PORT || 3000, CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = join(process.env.TMPDIR || '/tmp', 'dpr-resize-profile');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const URL0 = `http://localhost:${PORT}/play3d.html?scene=ow-valley&nomusic=1&nostory=1&v=${Date.now()}`;
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--window-size=1344,876', '--headless=new', URL0], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL') } catch (e) { }; killOrphans(profile); try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }) } catch (e) { } };
process.on('exit', kill); for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130) });
const CONSOLE = [];
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => { const m = JSON.parse(d.toString());
      if (m.method === 'Runtime.consoleAPICalled' && /error|warning/.test(m.params.type || ''))
        CONSOLE.push(m.params.type + ': ' + (m.params.args || []).map(a => a.value || a.description || '').join(' ').slice(0, 160));
      if (m.method === 'Runtime.exceptionThrown') CONSOLE.push('EXCEPTION');
      if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id) } });
    ws.on('open', () => res({ send: (m, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method: m, params: p })) }), close: () => ws.close() }));
    ws.on('error', rej);
  });
}
const ev = async (cdp, e) => { const r = await cdp.send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  const d = r.result || {}; if (d.exceptionDetails) return 'EXC ' + (d.exceptionDetails.exception?.description || ''); return d.result ? d.result.value : undefined; };
const STATE = `JSON.stringify((()=>{const p=(typeof PFXRIG!=='undefined'&&PFXRIG)?PFXRIG:null;
  const px=SIM.px(672,384,8,8), pt=SIM.paint({});
  return {buf:[R.domElement.width,R.domElement.height], pr:R.getPixelRatio(),
    css:[innerWidth,innerHeight], cssBox:[R.domElement.clientWidth,R.domElement.clientHeight],
    rt:p?[p.composer.renderTarget1.width,p.composer.renderTarget1.height]:null,
    rt2:p?[p.composer.renderTarget2.width,p.composer.renderTarget2.height]:null,
    ao:(p&&p.ao)?[p.ao.width,p.ao.height]:null,
    texel:(p&&p.aa)?[Math.round(1/p.aa.material.uniforms.texel.value.x),Math.round(1/p.aa.material.uniforms.texel.value.y)]:null,
    rgb:px.rgb, magenta:pt.magentaPixels};})())`;
let pass = 0, fail = 0;
const ok = (c, m, x) => { c ? (pass++, console.log('  ok   ' + m)) : (fail++, console.log('  FAIL ' + m + '  ' + JSON.stringify(x || ''))); };
const lit = s => s.rgb[0] + s.rgb[1] + s.rgb[2] > 30;

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'dpr_resize' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1344, height: 756, deviceScaleFactor: 2, mobile: false });
  // RE-NAVIGATE. PR is read at load, so the override must be in place BEFORE the
  // page boots or devicePixelRatio is still 1 and the whole probe measures dpr 1.
  await cdp.send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?scene=ow-valley&nomusic=1&nostory=1&v=${Date.now()}` });
  await sleep(1500);
  for (let i = 0; i < 400; i++) { if (await ev(cdp, `(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`) === true) break; await sleep(250); }
  await ev(cdp, `window.ORBIT.dist=4.5;window.ORBIT.pitch=0.14;SIM.tick(2)`); await sleep(2500);
  const S = async () => JSON.parse(await ev(cdp, STATE));
  console.log('== 1  BOOT at the shipped default');
  const b = await S(); console.log('     ' + JSON.stringify(b));
  ok(b.pr === 2 && b.buf[0] === 2688 && b.buf[1] === 1536, 'drawing buffer is 2688x1536 at pr 2', b);
  ok(b.rt[0] === 2688 && b.rt[1] === 1536 && b.rt2[0] === 2688, 'composer rt1+rt2 follow the ratio', b);
  ok(b.ao[0] === 1344 && b.ao[1] === 768, 'GTAO is half of the EFFECTIVE size (ao_res 0.5)', b);
  ok(b.texel[0] === 2688 && b.texel[1] === 1536, 'the FXAA texel is one device pixel', b);
  ok(lit(b) && b.magenta > 0, 'the frame has pixels and the character is rasterised', b);

  console.log('== 2  CSS RESIZES (updateStyle:false — the buffer must not move)');
  for (const [w, h] of [[800, 450], [1920, 1080], [1344, 756]]) {
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await sleep(900); await ev(cdp, `SIM.tick(2)`); await sleep(300);
    const s = await S();
    ok(s.buf[0] === 2688 && s.buf[1] === 1536 && s.rt[0] === 2688 && s.ao[0] === 1344 && s.texel[0] === 2688,
      `css ${w}x${h}: buffer/rt/ao/texel unchanged (css box now ${s.cssBox})`, s);
    ok(lit(s) && s.magenta > 0, `css ${w}x${h}: still drawing (rgb ${s.rgb}, ${s.magenta} char px)`, s);
  }

  console.log('== 3  COMPOSER RATIO ROUND TRIP 2 -> 1 -> 2');
  for (const pr of [1, 2]) {
    await ev(cdp, `(()=>{R.setPixelRatio(${pr});R.setSize(1344,768,false);PFXRIG.composer.setPixelRatio(${pr});SIM.tick(2);return 1})()`);
    await sleep(700);
    const s = await S();
    const e = [1344 * pr, 768 * pr];
    ok(s.buf[0] === e[0] && s.rt[0] === e[0] && s.rt[1] === e[1] && s.rt2[0] === e[0]
      && s.ao[0] === e[0] / 2 && s.texel[0] === e[0] && s.texel[1] === e[1],
      `pr ${pr}: buf ${s.buf} rt ${s.rt} ao ${s.ao} texel ${s.texel} all consistent`, s);
    ok(lit(s) && s.magenta > 0, `pr ${pr}: still drawing (rgb ${s.rgb}, ${s.magenta} char px)`, s);
  }
  const u = [...new Set(CONSOLE)];
  ok(u.length === 0, 'console clean across the whole probe', u);
  console.log((fail ? 'FAIL' : 'PASS') + `  ${pass} ok, ${fail} failed`);
  cdp.close(); kill(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1) });
