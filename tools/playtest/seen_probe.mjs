/* seen_probe.mjs — CAN THE PLAYER SEE THEMSELVES HERE, AND WHAT IS THE AGENT HANDED?
 *
 *   node tools/playtest/seen_probe.mjs --port 3000 --scene del-cine \
 *        --stands '[["name",[x,y,z],"shot"]]'
 *
 * WHY IT EXISTS (round 23, PT-20260805-032..036). Five tickets came off one stand in
 * del-cine. `_court_probe --way` drove it 3/3 legs BOTH ways and `wayfind_probe` found
 * the routed arrow on screen, labelled and landing on a walk ribbon — so the world was
 * open and the sign was right, and the agent still spent 29 steps walking into the one
 * fenced side. The missing question was the one nobody had an instrument for: DOES THE
 * PLAYER KNOW WHICH FIGURE IS THEM. Measured here: the body drew 353 of 428 pixels
 * through the plate at charNdc [-0.623,0.238] — screen [241,274] of 1280x720, the LEFT
 * QUARTER — while the ticket said "stuck at the far right of the platform". Wrong about
 * its own position by ~700 px, with four same-sized villagers in frame.
 *
 * WHAT IT ASKS, all of them the engine's own answers, never a model of them:
 *   SIM.paint({})            is the body rasterised at all (magenta, depth test OFF)
 *   SIM.paint({tested:true}) does it SURVIVE the shot's depth plate — the two together
 *                            separate "not drawn" from "drawn and occluded", which look
 *                            identical in a screenshot
 *   SIM.occCheck()           the presence ring the game puts up when you are hidden
 *   PERCEPT_JS + flattenPercept
 *                            THE TEXT THE AGENT WOULD ACTUALLY BE HANDED at this stand,
 *                            imported from the adapter and never copied, so this cannot
 *                            drift from what a run sees.
 *
 * NOTE ON `nostory=1`: the page boots with an empty flag store, so the story's routed
 * pill (.story-way) is ABSENT here and every marker prints unlabelled. That is correct
 * for a geometry read and wrong for a wayfinding one — for the labels use wayfind_probe,
 * which seeds the chapter's flags first.
 */
import { spawn } from 'child_process';
import { rmSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '/Users/junshernchan/projects/multiplayer-rpg/tools/cdp.mjs';
import { PERCEPT_JS, flattenPercept } from './adapter_emberbrook.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const SC = arg('scene', 'del-cine');
const STANDS = JSON.parse(arg('stands', '[]'));
const CDP = await freePort();
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const profile = join(tmpdir(), 'seen-probe-profile');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  '--window-size=1280,800', '--headless=new', 'about:blank'], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL') } catch (e) {} try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }) } catch (e) {} };
process.on('exit', kill);
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { kill(); process.exit(1); });
setTimeout(() => { console.error('SELF-EXPIRY 300s'); kill(); process.exit(2); }, 300000);

const wsUrl = await findPage(CDP, { tries: 240, label: 'seen_probe', match: /^about:blank/ });
const ws = new WebSocket(wsUrl, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
await new Promise(r => ws.on('open', r));
let id = 0; const pend = new Map();
ws.on('message', m => { const o = JSON.parse(m); if (o.id && pend.has(o.id)) { pend.get(o.id)(o); pend.delete(o.id); } });
const send = (method, params = {}) => new Promise((res, rej) => {
  const i = ++id; pend.set(i, o => o.error ? rej(new Error(method + ': ' + o.error.message)) : res(o.result));
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (e) => (await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true })).result.value;
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?nomusic=1&nostory=1&scene=${SC}` });
for (let i = 0; i < 240; i++) {
  if (await ev(`(()=>{try{return !!(window.SIM&&SIM.gpu&&SIM.gpu().meshes>0&&SIM.pos)}catch(e){return false}})()`)) break;
  await new Promise(r => setTimeout(r, 1000));
}
await new Promise(r => setTimeout(r, 2000));
console.log('scene:', await ev('SIM.scene()'), ' meshes:', await ev('SIM.gpu().meshes'));
for (const [name, pos, shot] of STANDS) {
  if (shot) { await ev(`SIM.shot(${JSON.stringify(shot)})`); await new Promise(r => setTimeout(r, 1200)); }
  await ev(`SIM.tp(${pos[0]},${pos[2]},${pos[1]})`);
  if (shot) await ev(`SIM.shot(${JSON.stringify(shot)})`);
  await new Promise(r => setTimeout(r, 900));
  await ev('SIM.tick(3)');
  await new Promise(r => setTimeout(r, 500));
  const drawn = await ev('JSON.stringify(SIM.paint({}))');
  const tested = await ev('JSON.stringify(SIM.paint({tested:true}))');
  const occ = await ev('JSON.stringify(SIM.occCheck())');
  const at = await ev('JSON.stringify(SIM.pos())');
  console.log(`\n== ${name}  want ${JSON.stringify(pos)} shot=${shot}`);
  console.log(`   landed ${at}`);
  console.log(`   paint (no depth test, "is it rasterised at all") : ${drawn}`);
  console.log(`   paint (depth test ON,  "survives the plate")     : ${tested}`);
  console.log(`   occCheck (presence ring)                         : ${occ}`);
  const p = await ev(PERCEPT_JS);
  console.log('   --- THE PERCEPT THE AGENT WOULD BE HANDED ---');
  console.log(flattenPercept(p).split('\n').map(l => '   | ' + l).join('\n'));
}
kill();
process.exit(0);
