/* _court_probe.mjs — ASK THE RUNNING GAME WHERE IT IS SHUT, AND WHAT SHUTS IT.
 *
 *   node tools/_court_probe.mjs --port 3000 --comp '{"seeds":[[x,y,z],..],"box":[x0,x1,z0,z1],"step":0.4}'
 *   node tools/_court_probe.mjs --port 3000 --who  '{"x0":..,"x1":..,"z0":..,"z1":..,"step":0.2,"ymin":..,"ymax":..}'
 *   node tools/_court_probe.mjs --port 3000 --at   '[[x,z],..]'
 *   node tools/_court_probe.mjs --port 3000 --way  '[[x,y,z],..]'
 *   node tools/_court_probe.mjs --port 3000 --pairs '[{"name":..,"a":[x,y,z],"b":[x,y,z]}]'
 *
 * WHY IT EXISTS (Old Gate, 2026-08-03). A flood fill tells you WHERE the world is shut
 * and never WHAT shuts it. docs/qa/oldgate/index.html measured a six-cell island on the
 * culvert court, correctly, and then spent a day reasoning about step heights, aprons and
 * a re-cut of the deck's SE corner — because nothing had asked the runtime to NAME the
 * obstruction. `SIM.blocked` returns the blocking mesh's name. It returned `oldgate_3`,
 * the gate's own "wall over the water" run, lying across the road for 7.7 m: the whole
 * prop had been built a quarter turn out. One --who run, forty seconds.
 *
 *   --comp   flood fill on reach_probe's OVERWORLD rules (SIM.ground, its fall path,
 *            SIM.blocked, the player's body box), CLIPPED to a box, and it prints the
 *            filled cells as an ASCII plan with one letter per seed. Two seeds that
 *            print different letters are two worlds; `*` is where they overlap. That
 *            picture is the finding — a cell count alone cannot show you the frontier.
 *   --who    every cell's top floor in a height band, SIM.blocked's mesh NAME tallied
 *            and sampled. This is the one that ends arguments.
 *   --at     every floor under a point and what blocks a body standing on each.
 *   --way    SIM.move() along a waypoint list, forwards then backwards, naming the leg
 *            and position of any stall. The drive, not a model of it.
 *   --pairs  reach_probe's own __ebReach A->B verdicts, for the record.
 *
 * SCENE. `--scene <name>` (default ow-valley, which is where the instrument was born).
 * `--comp` settles the foot BY THE SCENE'S OWN LAW, derived the way reach_probe derives
 * it and never read off the #wl checkbox: in a WALKLOCK scene (/^(del-|emb-|townwalk)/)
 * only walk_ meshes may catch the foot — walkFloors within [fy-STEP_DN-.1, fy+STEP_UP+.1],
 * highest first, with walkGround's four 0.18 m plank-crack retries — and elsewhere it is
 * SIM.ground plus play3d's 8 m fall. THIS DISTINCTION IS THE WHOLE POINT IN A TOWN: the
 * overworld settle stands the fill on scenery the player cannot stand on, so a town probed
 * with it reports FEWER holes than the town has. Its defaults are one region's; its
 * answers are not soft — every number it prints is the engine's.
 */
import { spawn } from 'child_process';
import { rmSync } from 'fs';
import { join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';
import { INSTALL } from './reach_probe.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const TRANSECT = JSON.parse(arg('transect', '[]'));   // [[x,z],...] plan points, probed top-down
const PAIRS = JSON.parse(arg('pairs', '[]'));         // [{name,a,b}]
const DRIVE = (way) => `(async()=>{
  const W=${JSON.stringify(way)};
  SIM.tp(W[0][0], W[0][2], W[0][1]);
  const log=[]; let stalled=null;
  for(let i=1;i<W.length;i++){
    const T=W[i]; let ticks=0, last=1e9, still=0;
    while(ticks<400){
      const p=SIM.pos(); const dx=T[0]-p.x, dz=T[2]-p.z; const d=Math.hypot(dx,dz);
      if(d<0.6) break;
      SIM.move(dx/d*1.0, dz/d*1.0, 1); ticks++;
      const q=SIM.pos(); const nd=Math.hypot(T[0]-q.x, T[2]-q.z);
      if(last-nd < 0.002){ still++; } else { still=0; }
      last=nd;
      if(still>40){ stalled={leg:i, target:T, at:[+q.x.toFixed(2),+q.y.toFixed(2),+q.z.toFixed(2)], dist:+nd.toFixed(2)}; break; }
      if(ticks%200===0) await new Promise(r=>setTimeout(r,0));
    }
    const p=SIM.pos();
    log.push({leg:i, at:[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)], ticks,
              d:+Math.hypot(T[0]-p.x,T[2]-p.z).toFixed(2)});
    if(stalled) break;
  }
  const p=SIM.pos();
  return JSON.stringify({stalled, legs:log.length, of:W.length-1,
    end:[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)], log});
})()`;

const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const SCENE = arg('scene', 'ow-valley');
// rt=1 is the overworld's realtime flag; a pre-rendered town scene must not carry it.
const URL = `http://localhost:${PORT}/play.html?scene=${encodeURIComponent(SCENE)}` +
  `${/^ow-/.test(SCENE) ? '&rt=1' : ''}&nomusic=1&v=${Date.now()}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = join(process.env.TMPDIR || '/tmp', 'ow-court-profile');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820', '--headless=new', URL], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL') } catch (e) { }; try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }) } catch (e) { } };
process.on('exit', kill); for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130) });
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id) } });
    ws.on('open', () => res({ send: (m, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method: m, params: p })) }), close: () => ws.close() }));
    ws.on('error', rej)
  })
}
const ev = async (cdp, e) => {
  const r = await cdp.send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  const d = r.result || {}; if (d.exceptionDetails) return 'EXC ' + (d.exceptionDetails.exception?.description || JSON.stringify(d.exceptionDetails));
  return d.result ? d.result.value : undefined;
};
(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'court' }));
  await cdp.send('Runtime.enable');
  let ok = false;
  for (let i = 0; i < 200; i++) { if (await ev(cdp, `(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`) === true) { ok = true; break } await sleep(250) }
  if (!ok) { console.error('never populated'); kill(); process.exit(2) }
  await sleep(800);
  // SIM.pos() is finite LONG BEFORE the bundle's GLB is in allMeshes, and every probe
  // here reads SIM.floors — so a probe that fired on that race printed a whole region
  // as `<no floor>`: an instrument reporting an empty world because it asked too early.
  // Wait for the mesh census to be non-zero AND to stop moving for two ticks.
  let mesh = 0, still = 0;
  for (let i = 0; i < 240; i++) {
    const n = await ev(cdp, `(()=>{try{return SIM.gpu().meshes|0}catch(e){return 0}})()`) | 0;
    if (n > 0 && n === mesh) { if (++still >= 2) break; } else still = 0;
    mesh = n; await sleep(250);
  }
  if (!mesh) { console.error('bundle never loaded (allMeshes 0) — every floor reading would be a lie'); kill(); process.exit(2) }
  console.log('meshes:', mesh);
  console.log('scene:', await ev(cdp, 'SIM.scene()'),
    ' walklock:', await ev(cdp, `(()=>{ if(!/^(del-|emb-|townwalk)/.test(String(SIM.scene()))) return false;
      try{ if(new URLSearchParams(location.search).get('walklock')==='0') return false; }catch(e){}
      try{ if(localStorage.getItem('eb-walklock')==='0') return false; }catch(e){} return true; })()`));

  if (TRANSECT.length) {
    const expr = `(()=>{const P=${JSON.stringify(TRANSECT)};const out=[];
      for(const p of P){const x=p[0],z=p[1];
        const fl=(SIM.floors(x,z)||[]).map(v=>+v.toFixed(2)).sort((a,b)=>b-a);
        const g=SIM.ground(x,z,p[2]===undefined?60:p[2]);
        const gg=(g===null||g===undefined)?null:+g.toFixed(2);
        out.push({x:+x.toFixed(2),z:+z.toFixed(2),g:gg,fl:fl.slice(0,5),
                  b:gg===null?null:!!SIM.blocked(x,z,gg)});}
      return JSON.stringify(out);})()`;
    const t = await ev(cdp, expr);
    console.log('\n== TRANSECT (SIM.floors top-5, SIM.ground from y=60, SIM.blocked at ground) ==');
    try {
      for (const r of JSON.parse(t))
        console.log(`  x ${String(r.x).padStart(7)} z ${String(r.z).padStart(7)}  ground ${r.g === null ? ' none ' : String(r.g).padStart(6)}  blocked ${r.b === null ? '-' : (r.b ? 'YES' : ' no')}   floors ${JSON.stringify(r.fl)}`);
    } catch (e) { console.log(t); }
  }

  const GRID = JSON.parse(arg('grid', 'null'));   // {x0,x1,z0,z1,step,ymin,ymax, walk?}
  // `"walk":true` PAINTS THE LEGIBILITY HOLE, and in a WALKLOCK town that is the map that
  // matters. WALKLOCK means only walk_ meshes catch the foot, so a cell can carry a solid,
  // rendered, plate-visible floor (SIM.floors) and still refuse the player (no
  // SIM.walkFloors under it). Those cells print `v` — ground you can SEE and cannot STAND
  // on, which is what a player reports as "a hole in the ground". `#` still means a body
  // is blocked where the foot would land; `.` means no floor of any kind.
  if (GRID) {
    const expr = `(()=>{const G=${JSON.stringify(GRID)};const rows=[];
      // THE SAME Y WINDOW FOR BOTH SIDES. An earlier cut banded walkFloors around the TOP
      // scenery floor, so a walk pad under an eave or a jetty read as absent and painted a
      // hole that was not there. The question is per-BAND: is there walk network in the
      // slice of world this map is drawn for?
      const wf=(x,z)=>{const f=SIM.walkFloors(x,z)||[];let b=null;
        for(let i=0;i<f.length;i++){const v=f[i]; if(v>=G.ymin&&v<=G.ymax&&(b===null||v>b))b=v;} return b;};
      const O4=[[.18,0],[-.18,0],[0,.18],[0,-.18]];
      for(let z=G.z1; z>=G.z0-1e-9; z-=G.step){ let s='';
        for(let x=G.x0; x<=G.x1+1e-9; x+=G.step){
          const fl=(SIM.floors(x,z)||[]).filter(v=>v>=G.ymin&&v<=G.ymax).sort((a,b)=>b-a);
          if(!fl.length){ s+='.'; continue; }
          const y=fl[0];
          if(G.walk){
            let w=wf(x,z);
            if(w===null) for(let k=0;k<4;k++){ w=wf(x+O4[k][0],z+O4[k][1]); if(w!==null)break; }
            if(w===null){ s+='v'; continue; }            // visible floor, NO walk network
            s += SIM.blocked(x,z,w) ? '#' : (w>=G.hi?'H':(w>=G.mid?'M':'l'));
            continue;
          }
          s += SIM.blocked(x,z,y) ? '#' : (y>=G.hi?'H':(y>=G.mid?'M':'l'));
        }
        rows.push(z.toFixed(1).padStart(6)+' '+s); }
      return JSON.stringify(rows);})()`;
    const g = await ev(cdp, expr);
    console.log(`\n== GRID  x ${GRID.x0}..${GRID.x1} step ${GRID.step}  (# blocked, H/M/l floor band, ` +
      `${GRID.walk ? "v = VISIBLE floor with no walk network under it, " : ''}. no floor in [${GRID.ymin},${GRID.ymax}]) ==`);
    const hdr = [];
    for (let x = GRID.x0; x <= GRID.x1 + 1e-9; x += GRID.step) hdr.push(x);
    console.log('       ' + hdr.map(v => (Math.abs(v % 2) < GRID.step / 2 ? '|' : ' ')).join(''));
    try { for (const r of JSON.parse(g)) console.log(r); } catch (e) { console.log(g); }
    console.log('       ' + hdr.map(v => (Math.abs(v % 2) < GRID.step / 2 ? '|' : ' ')).join(''));
    console.log('       x from ' + GRID.x0 + ' to ' + GRID.x1 + ', ticks every 2 m');
  }

  // ---- COMPONENT: reach_probe's own walk rules, but DUMP THE CELLS ---------------
  const COMP = JSON.parse(arg('comp', 'null'));  // {seeds:[[x,y,z],..], box:[x0,x1,z0,z1], step, budget}
  if (COMP) {
    const expr = `(async()=>{const C=${JSON.stringify(COMP)};
      const STEP=C.step||0.4, SU=0.63, SD=0.8, DROP_MAX=8, BUD=C.budget||60000;
      // WALKLOCK, re-derived from the three inputs play3d derives it from (reach_probe's
      // note): the #wl checkbox is written once at page load and sgSwap moves the real
      // flag underneath it.
      const wl=(()=>{ if(!/^(del-|emb-|townwalk)/.test(String(SIM.scene()))) return false;
        try{ if(new URLSearchParams(location.search).get('walklock')==='0') return false; }catch(e){}
        try{ if(localStorage.getItem('eb-walklock')==='0') return false; }catch(e){}
        return true; })();
      const pickWalk=(x,z,lo,hi)=>{const f=SIM.walkFloors(x,z); let b=null;
        for(let i=0;i<f.length;i++){const y=f[i]; if(y>=lo&&y<=hi&&(b===null||y>b))b=y;} return b;};
      const O4=[[.18,0],[-.18,0],[0,.18],[0,-.18]];
      const settle = wl
        ? (x,z,fy)=>{const lo=fy-SD-0.1, hi=fy+SU+0.1;
            let g=pickWalk(x,z,lo,hi); if(g!==null)return g;
            for(let k=0;k<4;k++){ g=pickWalk(x+O4[k][0],z+O4[k][1],lo,hi); if(g!==null)return g; }
            return null;}
        : (x,z,fy)=>{const g=SIM.ground(x,z,fy); if(g!==null&&g!==undefined)return g;
            let best=null; const f=SIM.floors(x,z);
            for(let i=0;i<f.length;i++){const y=f[i]; if(y<fy-SD&&y>fy-DROP_MAX&&(best===null||y>best))best=y;}
            return best;};
      const snap=v=>Math.round(v/STEP), key=(i,j)=>(i+100000)*200000+(j+100000);
      const out=[];
      for(const S of C.seeds){
        const seen=new Map(), qi=[], qj=[]; let head=0;
        let si=snap(S[0]), sj=snap(S[2]);
        let sy=settle(si*STEP, sj*STEP, S[1]);
        if(sy===null){ out.push({seed:S, cells:0, note:'seed unstandable'}); continue; }
        seen.set(key(si,sj),sy); qi.push(si); qj.push(sj);
        const D=[[1,0],[-1,0],[0,1],[0,-1]];
        while(head<qi.length && seen.size<BUD){
          if((head%20000)===0&&head) await new Promise(r=>setTimeout(r,0));
          const i=qi[head], j=qj[head], y=seen.get(key(i,j)); head++;
          for(let d=0;d<4;d++){ const ni=i+D[d][0], nj=j+D[d][1], kk=key(ni,nj);
            if(seen.has(kk))continue;
            const nx=ni*STEP, nz=nj*STEP;
            if(C.box&&(nx<C.box[0]||nx>C.box[1]||nz<C.box[2]||nz>C.box[3])){seen.set(kk,null);continue;}
            const g=settle(nx,nz,y); if(g===null)continue;
            if(SIM.blocked(nx,nz,g))continue;
            seen.set(kk,g); qi.push(ni); qj.push(nj); } }
        const cells=[]; for(const [k,v] of seen){ if(v===null)continue;
          cells.push([+((Math.floor(k/200000)-100000)*STEP).toFixed(2), +v.toFixed(2), +(((k%200000)-100000)*STEP).toFixed(2)]); }
        out.push({seed:S, cells:cells.length, capped:seen.size>=BUD, list:cells});
      }
      return JSON.stringify(out);})()`;
    const c = await ev(cdp, expr);
    console.log('\n== COMPONENTS (fill clipped to the box; reach_probe overworld rules) ==');
    try {
      const res = JSON.parse(c);
      const step = COMP.step || 0.4, bx = COMP.box;
      for (const r of res) {
        console.log(`  seed ${JSON.stringify(r.seed)} -> ${r.cells} cells${r.capped ? ' (CAPPED)' : ''}${r.note ? ' ' + r.note : ''}`);
      }
      // ascii overlay of every component in the box, one letter each
      if (bx) {
        // THE PLAN IS DRAWN ON THE FILL'S OWN LATTICE, NOT ON THE BOX. The fill snaps every
        // cell to a global multiple of `step`; a box edge that is not one (z=-33 at 0.4 m)
        // puts every printed row half a cell off every filled cell, and HALF THE ROWS COME
        // OUT EMPTY — a picture of nothing, over a world that is there. Snap outward.
        const q0 = Math.floor(bx[0] / step), q1 = Math.ceil(bx[1] / step);
        const r0 = Math.floor(bx[2] / step), r1 = Math.ceil(bx[3] / step);
        const ox = q0 * step, oz = r0 * step;
        const cols = q1 - q0 + 1, rows = r1 - r0 + 1;
        const grid = Array.from({ length: rows }, () => new Array(cols).fill('.'));
        const L = 'ABCDEFG';
        res.forEach((r, n) => (r.list || []).forEach(([x, y, z]) => {
          const ci = Math.round(x / step) - q0, ri = Math.round(z / step) - r0;
          if (ci >= 0 && ci < cols && ri >= 0 && ri < rows) grid[ri][ci] = grid[ri][ci] === '.' ? L[n] : '*';
        }));
        console.log(`\n  plan, x ${ox.toFixed(1)}..${(q1 * step).toFixed(1)} left->right, ` +
          `z ${(r1 * step).toFixed(1)} (top) .. ${oz.toFixed(1)} (bottom), cell ${step} m` +
          `\n  ('*' = a cell BOTH fills reached — the fill settles from the neighbour's height,` +
          ` so membership is not symmetric and two components may overlap without joining)`);
        for (let ri = rows - 1; ri >= 0; ri--)
          console.log('   ' + (oz + ri * step).toFixed(1).padStart(6) + ' ' + grid[ri].join(''));
        let hdr = '          ';
        for (let ci = 0; ci < cols; ci++) { const x = ox + ci * step; hdr += (Math.abs(x - Math.round(x / 2) * 2) < step / 2) ? '|' : ' '; }
        console.log(hdr + '   (| = even x)');
      }
    } catch (e) { console.log(String(c).slice(0, 4000)); }
  }

  // ---- WHO BLOCKS: SIM.blocked returns the mesh NAME -----------------------------
  const WHO = JSON.parse(arg('who', 'null'));   // {x0,x1,z0,z1,step,ymin,ymax}
  if (WHO) {
    const expr = `(()=>{const W=${JSON.stringify(WHO)};const tally={};const samp=[];
      for(let z=W.z0;z<=W.z1+1e-9;z+=W.step)for(let x=W.x0;x<=W.x1+1e-9;x+=W.step){
        const fl=(SIM.floors(x,z)||[]).filter(v=>v>=W.ymin&&v<=W.ymax).sort((a,b)=>b-a);
        if(!fl.length){tally['<no floor>']=(tally['<no floor>']||0)+1;continue;}
        const y=fl[0]; const n=SIM.blocked(x,z,y);
        const k=n||'<clear>'; tally[k]=(tally[k]||0)+1;
        if(n&&samp.length<400)samp.push([+x.toFixed(1),+z.toFixed(1),+y.toFixed(2),n]);
      }
      return JSON.stringify({tally,samp});})()`;
    const w = await ev(cdp, expr);
    console.log('\n== WHO BLOCKS (top floor in band; SIM.blocked names the mesh) ==');
    try {
      const o = JSON.parse(w);
      for (const [k, v] of Object.entries(o.tally).sort((a, b) => b[1] - a[1])) console.log(`   ${String(v).padStart(5)}  ${k}`);
      console.log('   samples:'); o.samp.slice(0, 60).forEach(s => console.log(`     x ${s[0]} z ${s[1]} y ${s[2]}  <- ${s[3]}`));
    } catch (e) { console.log(String(w).slice(0, 3000)); }
  }

  const MESH = arg('mesh', null);
  if (MESH) {
    const expr = `(()=>{const out=[];const S=SIM.scn?SIM.scn():null;
      const root=(window.SCENE_ROOT||window.__root||null);
      const seen=[];
      (window.THREE_SCENE||window.scene||root||{traverse:()=>{}}).traverse(o=>{
        if(o.isMesh&&new RegExp(${JSON.stringify(MESH)}).test(o.name)){
          o.geometry.computeBoundingBox();const b=o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
          seen.push({n:o.name,tris:(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3,
            min:[+b.min.x.toFixed(2),+b.min.y.toFixed(2),+b.min.z.toFixed(2)],
            max:[+b.max.x.toFixed(2),+b.max.y.toFixed(2),+b.max.z.toFixed(2)]});}});
      return JSON.stringify(seen);})()`;
    console.log('\n== MESHES ==');
    console.log(await ev(cdp, expr));
  }

  const AT = JSON.parse(arg('at', 'null'));  // [[x,z],..] — full floor list + blocked at each floor
  if (AT) {
    const expr = `(()=>{const P=${JSON.stringify(AT)};const out=[];
      for(const p of P){const fl=(SIM.floors(p[0],p[1])||[]).slice().sort((a,b)=>b-a);
        out.push({x:p[0],z:p[1],rows:fl.map(y=>[+y.toFixed(2),SIM.blocked(p[0],p[1],y)||'clear'])});}
      return JSON.stringify(out);})()`;
    const a = await ev(cdp, expr);
    console.log('\n== AT (every floor under the point, and what blocks a body standing on it) ==');
    try { for (const r of JSON.parse(a)) { console.log(`  x ${r.x} z ${r.z}`); r.rows.forEach(([y, n]) => console.log(`      y ${String(y).padStart(6)}  ${n}`)); } }
    catch (e) { console.log(a); }
  }

  // ---- WAY: drive the body along a waypoint list with play3d's own phys() -------
  const WAY = JSON.parse(arg('way', '[]'));
  if (WAY.length) {
    for (const [label, way] of [['WEST -> EAST', WAY], ['EAST -> WEST', [...WAY].reverse()]]) {
      const r = await ev(cdp, DRIVE(way));
      console.log('\n== DRIVE ' + label + ' ==');
      try {
        const o = JSON.parse(r);
        console.log(`  legs walked ${o.legs}/${o.of}   end ${JSON.stringify(o.end)}   stalled: ${o.stalled ? JSON.stringify(o.stalled) : 'no'}`);
      } catch (e) { console.log(r); }
    }
  }

  if (PAIRS.length) console.log('install:', await ev(cdp, INSTALL));
  for (const p of PAIRS) {
    const r = await ev(cdp, `window.__ebReach(${JSON.stringify(p.a)},${JSON.stringify(p.b)},{step:${p.step || 0.4},tol:${p.tol || 2.0},ms:120000}).then(o=>JSON.stringify(o))`);
    console.log('\n== ' + p.name + ' ==');
    try {
      const o = JSON.parse(r);
      console.log(`  ok=${o.ok} reason=${o.reason} cells=${o.cells} startOffset=${o.startOffset} walklock=${o.walklock}`);
      console.log(`  near=${JSON.stringify(o.near)}`);
      if (o.gap) console.log(`  GAP ${JSON.stringify(o.gap)}  (reverse component ${o.reverseCells} cells)`);
      if (o.route && o.route.length) console.log(`  via edges ${JSON.stringify(o.route)}`);
    } catch (e) { console.log(r); }
  }
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1) });
