/* spawn_gate — IS A REGION'S OWN BUNDLE SPAWN A PLACE A PLAYER CAN START?
 *
 * PT-20260803-015. ow-valley's meta.json spawn sat 0.072 m from the centre of the
 * portal edge that returns to Emberbrook (pad r 3.2). Anything that enters the scene
 * WITHOUT taking an edge — a checkpoint drop-in, a resume with no saved position, a
 * ?scene= dev jump — began the game standing on the door back out, and the playtest
 * agent walked through it on its first action in 2 runs out of 2.
 *
 * The file-side check is arithmetic and lives with the fix (valley_map.region_spawn).
 * THIS is the engine-side half, and it is the half that matters: boot the real page
 * with NO position in the URL, so play3d uses the bundle spawn exactly as a drop-in
 * does, then ask the ENGINE where the body ended up, whether it has floor, whether it
 * is boxed in, and how far it is from every edge pad in the scene.
 *
 * The rule this encodes is CLAUDE.md's: a walk check that reads the file is measuring
 * the artist's intent, not the player's world.
 *
 *   node tools/playtest/spawn_gate.mjs --scene ow-valley [--port 3000]
 */
import { freePort, findPage, killOrphans } from '../cdp.mjs';
import { spawn } from 'child_process';
import { mkdtempSync, readFileSync } from 'fs';
import { tmpdir } from 'os';
import { join, dirname } from 'path';
import WebSocket from 'ws';

const ROOT = join(dirname(new URL(import.meta.url).pathname), '../..');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const SCENE = arg('scene', 'ow-valley');
const PORT = parseInt(arg('port', '3000'), 10);
/* --pos x,y,z pins the body instead of using the bundle spawn. That is how a CONTROL
 * is taken: the interesting question about "20/24 headings have floor" is never the
 * number on its own, it is the number against the place the fix came from. */
const POS = arg('pos', null);
const FLOOR_MIN = parseInt(arg('floor-min', '18'), 10);
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const profile = mkdtempSync(join(tmpdir(), 'spawngate-'));
const cdpPort = await freePort();
const url = `http://localhost:${PORT}/play3d.html?nomusic=1&scene=${SCENE}` +
  (POS ? `&sx=${POS.split(',')[0]}&sy=${POS.split(',')[1]}&sz=${POS.split(',')[2]}` : '');
const child = spawn(CHROME, [
  `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1280,800', '--headless=new', url,
], { stdio: 'ignore' });
let done = false;
const reap = () => { if (done) return; done = true; try { child.kill('SIGKILL'); } catch (e) {} killOrphans(profile); };
process.on('exit', reap);
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { reap(); process.exit(1); });
const bail = setTimeout(() => { console.error('SELF-EXPIRY at 240 s'); reap(); process.exit(2); }, 240000);

const wsUrl = await findPage(cdpPort, { tries: 240, label: 'spawn_gate' });
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

for (let i = 0; i < 180; i++) {
  if (await ev(`(()=>{try{return !!(window.SIM&&SIM.gpu&&SIM.gpu().meshes>0&&SIM.pos)}catch(e){return false}})()`)) break;
  await new Promise(r => setTimeout(r, 1000));
}

// SIM.pos() is {x,y,z}; SIM.scene() is the in-place-swap surface's own answer.
const w = JSON.parse(await ev(`(()=>{const p=SIM.pos();return JSON.stringify({pos:[p.x,p.y,p.z],scene:SIM.scene()})})()`));
// 24-heading census at the body radius: floor under each step, and the blocking mesh name
// 24 headings at the body radius. SIM.blocked(x, z, fromY) answers with the BLOCKING
// MESH NAME, which is what turned an earlier "the court is a raft" into "the prop is a
// quarter turn out" — a census that only counts is a census that cannot be acted on.
const census = JSON.parse(await ev(`(()=>{ const p=SIM.pos(), R=0.8, out={floor:0,blocked:0,names:{}};
  for(let k=0;k<24;k++){ const a=k*Math.PI/12, x=p.x+Math.cos(a)*R, z=p.z+Math.sin(a)*R;
    const f=SIM.walkFloors(x,z); if(f&&f.length) out.floor++;
    const b=SIM.blocked(x,z,p.y);
    if(b){ out.blocked++; out.names[b]=(out.names[b]||0)+1; } }
  return JSON.stringify(out); })()`));

const sg = JSON.parse(readFileSync(join(ROOT, 'public/world/scenegraph.json'), 'utf8'));
const pads = (sg.edges || []).filter(e => e.from === SCENE && e.at);
const H = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);

let fails = 0;
const ok = (cond, what, detail) => { if (!cond) fails++; console.log(`  ${cond ? 'ok  ' : 'FAIL'}  ${what}   ${detail}`); };

console.log(`\nspawn_gate — ${SCENE}, ` +
  (POS ? `body pinned at ${POS} (CONTROL)` : 'booted with no position in the URL (the bundle spawn)') + '\n');
console.log(`  the engine put the body at [${w.pos.map(v => v.toFixed(2)).join(', ')}] in scene ${w.scene}\n`);
ok(w.scene === SCENE, 'the body is in the scene that was asked for', `${w.scene}`);
/* NOT 24/24. A road ribbon is ~4 m wide and the census steps 0.8 m out in 24
 * directions, so the two headings straight off each verge legitimately find no floor:
 * the shipped spawn this fix replaced scores the same. The gate is that the body is on
 * a road, not on a ledge — a majority of headings, measured, with the control recorded. */
ok(census.floor >= FLOOR_MIN, `at least ${FLOOR_MIN}/24 headings at 0.8 m have floor`, `${census.floor}/24 with floor`);
ok(census.blocked === 0, 'no heading is blocked by a body-box collision',
  census.blocked ? `${census.blocked}/24 blocked by ${Object.keys(census.names).join(', ')}` : '0/24 blocked');
console.log('');
for (const e of pads) {
  const d = H(w.pos, e.at);
  ok(d >= e.r, `clear of the pad ${e.id}`, `${d.toFixed(2)} m from a pad of radius ${e.r}` +
    (d < e.r ? '  <-- THE ARRIVAL IS ITS OWN EXIT' : ` (${(d - e.r).toFixed(2)} m of margin)`));
}
console.log(`\n${fails ? 'FAILED' : 'PASS'}  ${fails} failure(s)\n`);
clearTimeout(bail); reap();
process.exit(fails ? 1 : 0);
