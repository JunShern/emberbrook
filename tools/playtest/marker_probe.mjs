/* marker_probe — IS THE WAY ONWARD MARKED, FROM HERE?  (playtest round 5)
 *
 * The instrument behind FIXLOG round 5. The valley road to Dellhollow carried three
 * exit markers and every one a player could see was an anonymous red triangle into
 * Emberbrook; the one naming Dellhollow was drawn off the top of the screen.
 *
 * Boots ow-valley at the ch1.done arrival with Chapter One's flags set (so the Old
 * Gate edge is live, exactly as it is for a player who just finished Ch1), then, at
 * a series of positions along the road, asks the ENGINE:
 *   - which scenegraph edges are live, where they project on screen, and whether the
 *     marker layer would actually draw them (markersTick's own frustum test)
 *   - the prompt the player would get here
 *   - the objective banner text
 * and captures the frame.
 *
 *   node tools/playtest/marker_probe.mjs [--port 3000] [--scene ow-valley]
 *      [--stations '[["name",[x,y,z],"shot"]]'] [--yaw <rad>] [--out <dir>]
 *
 * At each station it teleports the body, faces the camera the way play3d's own
 * heading-follow would for a player walking to the NEXT station (or --yaw), and reads
 * THE MARKER LAYER'S OWN DOM (#exit-markers) plus each edge's NDC through the follow
 * camera itself (window._rtCam) — so the probe can never drift from markersTick.
 */
import { freePort, findPage, killOrphans } from '../cdp.mjs';
import { spawn } from 'child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import WebSocket from 'ws';
import { mkArg } from '../argv.mjs';

const argv = process.argv.slice(2);
// `--k v` AND `--k=v` (tools/argv.mjs): the bare indexOf form silently
// ignored the `=` spelling and used the DEFAULT instead.
const { arg } = mkArg(argv);
const PORT = parseInt(arg('port', '3000'), 10);
const SC = arg('scene','ow-valley');
const OUT = arg('out', 'docs/qa/playtest/markers');
mkdirSync(OUT, { recursive: true });
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const profile = mkdtempSync(join(tmpdir(), 'corridor-'));
const cdpPort = await freePort();
const child = spawn(CHROME, [
  `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1280,800', '--headless=new', 'about:blank',
], { stdio: 'ignore' });
let done = false;
const reap = () => { if (done) return; done = true; try { child.kill('SIGKILL'); } catch (e) {} killOrphans(profile); };
process.on('exit', reap);
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { reap(); process.exit(1); });
setTimeout(() => { console.error('SELF-EXPIRY at 420 s'); reap(); process.exit(2); }, 420000);

const wsUrl = await findPage(cdpPort, { tries: 240, label: 'corridor_probe', match: /^about:blank/ });
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
await send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?nomusic=1&scene=${SC}` });

for (let i = 0; i < 240; i++) {
  if (await ev(`(()=>{try{return !!(window.SIM&&SIM.gpu&&SIM.gpu().meshes>0&&SIM.pos)}catch(e){return false}})()`)) break;
  await new Promise(r => setTimeout(r, 1000));
}
// Chapter One's flags, so the Old Gate edge is live exactly as it is after ch1.done.
await ev(`(()=>{const f={};for(const k of ["story.ch1.started","story.ch1.done","story.ch1.gate-open","story.ch1.sendoff","lake-joined"])f[k]=true;GS.setFlags(f);return 1})()`);
await ev(`(()=>{try{Story&&Story.objective&&Story.objective("Follow the valley road down to Dellhollow")}catch(e){}return 1})()`);
await new Promise(r => setTimeout(r, 1500));

// The marker layer's OWN visibility test, lifted from play3d.html markersTick so the
// probe cannot drift from the thing being measured.
const EDGES_JS = `(()=>{
  const es=SIM.edges();
  // THE MARKER LAYER'S OWN OUTPUT, read out of the DOM it draws into, so the probe
  // cannot drift from markersTick.
  const mk={}; for(const d of document.querySelectorAll('#exit-markers > div')){
    mk[d.dataset.edge]={shown:d.style.display!=='none', tf:d.style.transform}; }
  const p=SIM.pos();
  // window._rtCam IS the overworld follow camera (play3d assigns cam=window._rtCam),
  // so this is the marker layer's own projection, not a reconstruction of it.
  const C=window._rtCam; const nd={};
  if(C){ for(const e of es){ const sgE=(window.SGE||[]).find? null : null; } }
  return JSON.stringify({pos:[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)],
    cam:(SIM.cine()&&SIM.cine().cam)?SIM.cine().cam.pos:null,
    obj:(document.getElementById('story-obj')||{}).textContent||null,
    camdef:window._rtCam?{fov:window._rtCam.fov,near:window._rtCam.near,far:window._rtCam.far,pos:window._rtCam.position.toArray().map(v=>+v.toFixed(1))}:null,
    orbit:window.ORBIT?{yaw:+window.ORBIT.yaw.toFixed(3),pitch:+window.ORBIT.pitch.toFixed(3),dist:window.ORBIT.dist}:null,
    prompt:SIM.prompt(),
    edges:es.map(e=>({id:e.id,label:e.label,kind:e.kind,dist:e.dist,open:e.open,
      denied:e.denied,live:e.live,inRange:e.inRange,
      marker:mk[e.id]||null,
      ndc:(function(){ if(!window._rtCam) return null;
        const E=(SIM.edges().find(q=>q.id===e.id)); if(!E||!E.at) return null;
        const v=new THREE.Vector3(E.at[0],E.at[1]+2.1,E.at[2]).project(window._rtCam);
        return [+v.x.toFixed(3),+v.y.toFixed(3),+v.z.toFixed(3)]; })()}))});
})()`;

// Stations along the corridor: the arrival, points up the road toward the Old Gate,
// the gate court, and points down the gorge toward Dellhollow.
const STATIONS = arg('stations',null) ? JSON.parse(arg('stations')) : [
  ['A-arrival',      [-57.85, 26.72, 60.58]],
  ['B-road-mid',     [-58.5,  26.2,  45.0]],
  ['C-gate-approach',[-53.5,  26.3,  30.0]],
  ['D-gate-court',   [-45.0,  26.3,  20.0]],
  ['E-east-bank',    [-36.2,  23.3,  17.2]],
  ['F-gorge',        [-10.0,  18.0,  -5.0]],
  ['G-near-dell',    [ 30.0,  13.5, -28.0]],
  ['H-dell-gate',    [ 41.3,  13.1, -33.8]],
];
const rows = [];
for (let si = 0; si < STATIONS.length; si++) {
  const [name, pos, useShot] = STATIONS[si];
  if (useShot) { await ev(`SIM.shot(${JSON.stringify(useShot)})`); await new Promise(r => setTimeout(r, 2500)); }
  const next = si + 1 < STATIONS.length ? STATIONS[si+1][1] : null;
  await ev(`SIM.tp(${pos[0]},${pos[2]},${pos[1]})`);
  /* Face the camera the way a player who is WALKING THE ROAD would have it: the
   * heading-follow formula in play3d (yaw = atan2(-dz,-dx) of the movement dir),
   * aimed at the next station down the road. Without this the probe measures a
   * stale yaw and would under-report what is on screen. */
  const YAW = arg('yaw', null);
  if (YAW != null) await ev(`(()=>{window.ORBIT.yaw=${YAW};return 1})()`);
  else if (next) { const dx = next[0]-pos[0], dz = next[2]-pos[2];
    await ev(`(()=>{window.ORBIT.yaw=Math.atan2(${-dz},${-dx});return 1})()`); }
  await new Promise(r => setTimeout(r, 900));
  let r;
  try { r = JSON.parse(await ev(EDGES_JS)); } catch (e) { r = { error: String(e) }; }
  r.station = name; r.want = pos;
  rows.push(r);
  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 });
  writeFileSync(join(OUT, name + '.jpg'), Buffer.from(shot.data, 'base64'));
  console.log('\n=== ' + name + '  want ' + JSON.stringify(pos) + '  got ' + JSON.stringify(r.pos));
  console.log('    objective: ' + JSON.stringify(r.obj) + '   prompt: ' + JSON.stringify(r.prompt));
  for (const e of (r.edges || [])) {
    const m = e.marker;
    console.log('    ' + (m && m.shown ? 'MARKER' : '  ----') + '  ' + String(e.dist).padStart(6) + ' m  ' +
      String((m && m.shown && m.tf) ? m.tf.replace(/translate\(|\)|px/g, '') : '').padEnd(22) +
      '  ' + (e.label || '?') + '  [' + e.id + ']' + (e.open ? '' : ' SEALED') + (e.denied ? ' DENIED' : '') +
      (e.inRange ? '  <-- PROMPT IN RANGE' : ''));
  }
}
writeFileSync(join(OUT, 'stations.json'), JSON.stringify(rows, null, 1));
console.log('\nwrote ' + OUT);
reap(); process.exit(0);
