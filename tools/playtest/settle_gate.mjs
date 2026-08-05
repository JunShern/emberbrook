/* settle_gate.mjs — DOES A TRANSITION KEEP THE PLAYER WHERE THE WALKER PUT HIM?
 *
 *   node tools/playtest/settle_gate.mjs --port 3000 [--scene del-cine] [--cam lockfive]
 *        [--region 68,-29,80,-22] [--step 0.2] [--ab]
 *
 * THE QUESTION. Every authored cut and every sgCorrect routes the body through
 * play3d's `sgPlace`, which RE-SETTLES the height it is handed. `walkGround` — the
 * function that let the body stand where it is standing — probes (x, z) AND four
 * neighbours at +/-0.18 m, the plank-crack tolerance. Round 26 measured three falls
 * in one playtest run from one square metre of the Dellhollow crossing because
 * sgPlace had no such tolerance, found the exact column empty, and fell through to
 * the COLLISION set — which over those decks contains the river, 7 m down.
 *
 * SO THE GATE IS A DISAGREEMENT CENSUS, not a fill: over every column of a region,
 * at EVERY height a body may legitimately hold there, does the placer land within one
 * step (STEP_UP+STEP_DN = 1.43 m) of the walker's own answer? A cell where the walker
 * stands at 7.9 and the placer returns 1.6 is a TRAPDOOR: any cut taken there, or any
 * camera correction firing there, drops the player six metres with no cause on screen.
 *
 * WHY IT IS NOT `fall_probe --spray` §4, WHICH ROUND 26 NOMINATED FOR THIS JOB.
 * That section asks `SIM.tpY`, and `SIM.tpY` (play3d.html) carries ITS OWN INLINED
 * COPY of the settle — no range filter, no neighbour probe, the collide fallback
 * still first-class. It does not call sgPlace and never did. So it reports the
 * PRE-FIX behaviour on a fixed build, for ever, and a lane reading it concludes the
 * fix did nothing. A duplicated implementation in the test surface is a gate
 * measuring a function the game does not run — the same shape as walk_engine_gate's
 * file-vs-engine finding and _court_probe's builder-gate finding.
 *
 * Both functions are therefore replicated HERE from the shipped source, verbatim,
 * out of the primitives the page does expose (SIM.walkFloors / SIM.floors), and
 * `--ab` reports the pre-fix settle beside the shipped one so the census can prove
 * it could have found something. Measured on 162bade, del-cine, x 68..80 / z -29..-22
 * at 0.2 m: 4984 legitimate stands, 236 trapdoors BEFORE, 0 AFTER.
 */
import { freePort, findPage, killOrphans, sweepStaleProfiles, chromeArgs } from '../cdp.mjs';
import { spawn } from 'child_process';
import { tmpdir } from 'os';
import { join, dirname } from 'path';
import { mkdirSync, writeFileSync } from 'fs';
import WebSocket from 'ws';
import { mkArg } from '../argv.mjs';

const argv = process.argv.slice(2);
const { arg, checkArgs } = mkArg(argv, ['port', 'scene', 'cam', 'spawn', 'region', 'step', 'ab', 'out']);
checkArgs('settle_gate');
const PORT = parseInt(arg('port', '3000'), 10);
const SCENE = arg('scene', 'del-cine');
const CAM = arg('cam', 'lockfive');
const SPAWN = arg('spawn', '79.7,0.83,-27.13').split(',').map(Number);
const REGION = arg('region', '68,-29,80,-22').split(',').map(Number);   // x0,z0,x1,z1
const STEP = parseFloat(arg('step', '0.2'));
const AB = arg('ab', '1') !== '0';
const OUT = arg('out', 'docs/qa/playtest/settle-gate.json');
mkdirSync(dirname(OUT), { recursive: true });

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PREFIX = 'settlegate-';
sweepStaleProfiles(PREFIX);
const profile = join(tmpdir(), PREFIX + process.pid);
mkdirSync(profile, { recursive: true });
const cdpPort = await freePort();
const child = spawn(CHROME, chromeArgs({ port: cdpPort, profile, url: 'about:blank' }), { stdio: 'ignore' });
let done = false;
const reap = () => { if (done) return; done = true; try { child.kill('SIGKILL'); } catch (e) {} killOrphans(profile); };
process.on('exit', reap);
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { reap(); process.exit(1); });
setTimeout(() => { console.error('SELF-EXPIRY at 420 s'); reap(); process.exit(2); }, 420000);

const wsUrl = await findPage(cdpPort, { tries: 240, label: 'settle_gate', match: /^about:blank/ });
const ws = new WebSocket(wsUrl, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
await new Promise(r => ws.on('open', r));
let id = 0; const pend = new Map();
ws.on('message', m => { const o = JSON.parse(m); if (o.id && pend.has(o.id)) { pend.get(o.id)(o); pend.delete(o.id); } });
const send = (m, p = {}) => new Promise((res, rej) => {
  const i = ++id; pend.set(i, o => o.error ? rej(new Error(m + ': ' + o.error.message)) : res(o.result));
  ws.send(JSON.stringify({ id: i, method: m, params: p }));
});
const ev = async e => {
  const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text);
  return r.result.value;
};
const sleep = ms => new Promise(r => setTimeout(r, ms));
await send('Runtime.enable'); await send('Page.enable');
const url = `http://localhost:${PORT}/play3d.html?nomusic=1&nofollow=1&scene=${SCENE}&cam=${CAM}` +
            `&sx=${SPAWN[0]}&sy=${SPAWN[1]}&sz=${SPAWN[2]}`;
await send('Page.navigate', { url });
// READY MEANS THE WALK NETWORK IS BUILT (fall_probe's first failure: it accepted a
// truthy SIM and censused a world that had not loaded).
let ready = false;
for (let i = 0; i < 300; i++) {
  try { if (await ev(`(()=>{try{const c=SIM.cine(),g=SIM.gpu();return !!(c&&c.shot&&g.walk>0&&!SIM.busy())}catch(e){return false}})()`)) { ready = true; break; } } catch (e) {}
  await sleep(250);
}
if (!ready) { console.error('FAIL: the page never built a walk network'); reap(); process.exit(3); }

const res = await ev(`(()=>{
  const SU=0.63, SD=0.8, R=SU+SD, NB=[[.18,0],[-.18,0],[0,.18],[0,-.18]];
  // walkGround (play3d.html), in shape: topmost walk floor within one step of fy,
  // then the four plank-crack neighbours.
  const wcol=(x,z,fy)=>{ const lo=fy-SD-0.1, hi=fy+SU+0.1;
    const t=SIM.walkFloors(x,z).filter(y=>y>=lo&&y<=hi); return t.length?Math.max.apply(null,t):null; };
  const walkGround=(x,z,fy)=>{ let g=wcol(x,z,fy); if(g!=null) return g;
    for(const[ox,oz]of NB){ g=wcol(x+ox,z+oz,fy); if(g!=null) return g; } return null; };
  // sgPlace AS SHIPPED (162bade).
  const sgPlace=(x,y,z)=>{ let ys=SIM.walkFloors(x,z);
    let near=ys.filter(v=>Math.abs(v-y)<=R);
    if(!near.length) for(const[ox,oz]of NB){ const t=SIM.walkFloors(x+ox,z+oz).filter(v=>Math.abs(v-y)<=R); if(t.length){near=t;break;} }
    if(near.length) ys=near; else if(!ys.length) ys=SIM.floors(x,z);
    return ys.length?ys.reduce((a,b)=>Math.abs(a-y)<Math.abs(b-y)?a:b):y; };
  // sgPlace BEFORE the fix — the A/B that proves the census could find something.
  const sgPlaceOld=(x,y,z)=>{ let ys=SIM.walkFloors(x,z); if(!ys.length) ys=SIM.floors(x,z);
    return ys.length?ys.reduce((a,b)=>Math.abs(a-y)<Math.abs(b-y)?a:b):y; };
  const [x0,z0,x1,z1]=${JSON.stringify(REGION)}, S=${STEP};
  const bad=[], badOld=[]; let stands=0, cols=0;
  for(let x=x0;x<=x1+1e-6;x+=S) for(let z=z0;z<=z1+1e-6;z+=S){
    cols++;
    const cands=[...new Set(SIM.walkFloors(x,z).concat(
      NB.map(([ox,oz])=>SIM.walkFloors(x+ox,z+oz)).flat()).map(v=>+v.toFixed(2)))];
    for(const fy of cands){
      const wg=walkGround(x,z,fy);
      if(wg==null||Math.abs(wg-fy)>0.35) continue;     // not a height a body may hold here
      stands++;
      const n=sgPlace(x,fy,z);
      if(Math.abs(n-fy)>R) bad.push([+x.toFixed(2),+z.toFixed(2),+fy.toFixed(2),+n.toFixed(2)]);
      if(${AB}){ const o=sgPlaceOld(x,fy,z);
        if(Math.abs(o-fy)>R) badOld.push([+x.toFixed(2),+z.toFixed(2),+fy.toFixed(2),+o.toFixed(2)]); }
    }
  }
  return {cols, stands, bad, badOld};
})()`);

console.log(`settle_gate — ${SCENE} x ${REGION[0]}..${REGION[2]} / z ${REGION[1]}..${REGION[3]} at ${STEP} m`);
console.log(`  ${res.cols} columns, ${res.stands} legitimate stands (walkGround agrees within 0.35 m)`);
if (AB) console.log(`  pre-fix settle would misplace ${res.badOld.length} of them by more than 1.43 m` +
                    (res.badOld.length ? ` — e.g. ${res.badOld.slice(0,3).map(b=>`[${b[0]}, ${b[1]}] ${b[2]} -> ${b[3]}`).join('; ')}` : ''));
if (!res.bad.length) console.log(`  PASS — every stand survives its own transition.`);
else {
  console.log(`  FAIL — ${res.bad.length} TRAPDOOR(S):`);
  for (const b of res.bad.slice(0, 30)) console.log(`    [${b[0]}, ${b[1]}] standing ${b[2]} -> settled ${b[3]}`);
}
// A NEGATIVE RESULT MUST PROVE IT COULD HAVE FOUND SOMETHING (cdp.mjs's rule): with
// --ab off, or a region with no stands in it, this gate is green about nothing.
if (!res.stands) console.log('  !! ZERO STANDS — this region has no walk network in it; the PASS above is empty.');
writeFileSync(OUT, JSON.stringify({ scene: SCENE, region: REGION, step: STEP, ...res }, null, 1));
console.log('  wrote ' + OUT);
reap();
process.exit(res.bad.length || !res.stands ? 1 : 0);
