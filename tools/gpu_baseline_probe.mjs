// gpu_baseline_probe.mjs — IS transition_test's PER-(SCENE,SHOT) GPU BASELINE A
// FUNCTION OF (SCENE, SHOT)? It is not, and this is the instrument that says so.
//
// transition_test asserts renderer.info.memory.geometries is IDENTICAL on every
// repeat visit to a (scene, shot). It has read 168/0, 167/1 and 164/5 on the SAME
// tree. This probe drives transition_test's own 24-door itinerary and its own battle
// leg, records the count at every arrival, and then names the resident geometries the
// only honest way — DISPOSE EACH ONE AND WATCH renderer.info. A geometry whose
// disposal drops the counter was resident; one whose owner is not currently drawable
// is a page-scope passenger, which is what a drifting baseline is made of.
//
// MEASURED 2026-08-09 (docs/qa/transition-test/gpu-baseline-probe-20260809.log), one
// run, four del-cine states drifting by exactly two:
//   shelf-west {624, 622, 624, 624}   gate {2073, 2075, 2075}   cottage {367, 365}
// Doors 3 and 19 are the SAME edge, the SAME shot and the SAME position (27.6,-7.38)
// and read 622 and 624. Of 615 resident geometries at the end, exactly TWO belong to
// an object that is not currently drawable: a RingGeometry and an OctahedronGeometry
// under `ch` — occRing and occDia (play3d.html:1537-1538), the occlusion indicator.
// mkMat() gives them no map, so they are worth 2 geometries and 0 textures: the
// fingerprint of every one of those reds.
//
// WHY IT DRIFTS: sceneDispose() disposes them on every scene change (7545d2fd), and
// three.js re-registers a geometry only when it is next DRAWN — so they are in the
// count iff occCheck()'s camera->body ray hit at ANY point during that scene's life.
// Every reading above had ring=false AT THE SNAPSHOT and still carried the +2.
//
// usage: node gpu_baseline_probe.mjs --port=3000
import { spawn } from 'node:child_process';
import { rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage, chromeArgs, sweepStaleProfiles } from './cdp.mjs';

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=')[1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const OUT = arg('out', 'docs/qa/transition-test/gpu-baseline-probe.json');
const CDP_PORT = await freePort();
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=del-cine`;
const profile = join(process.env.TMPDIR || '/tmp', 'gpu-baseline-probe-' + process.pid);
sweepStaleProfiles('gpu-baseline-probe-');
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, chromeArgs({ port: CDP_PORT, profile, url: URL }), { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) {}
  try { rmSync(profile, { recursive: true, force: true }); } catch (e) {} };
process.on('exit', kill); process.on('SIGINT', () => { kill(); process.exit(1); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({ send(m, p) { return new Promise((okk, no) => { const mid = ++id;
      pend.set(mid, { ok: okk, no }); ws.send(JSON.stringify({ id: mid, method: m, params: p || {} })); }); },
      close() { try { ws.close(); } catch (e) {} } }));
    ws.on('error', rej);
    ws.on('message', (raw) => { let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok: okk, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(m.error.message)) : okk(m.result); } });
  });
}
async function ev(cdp, expr, t) {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true,
    returnByValue: true, userGesture: true, timeout: t || 180000 });
  if (r.exceptionDetails) throw new Error('page exception: ' +
    (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  return r.result && r.result.value;
}

const NPCSETTLED = `(!window.Npc || !Npc.ready ? Promise.resolve(true)
  : Promise.race([Npc.ready(), new Promise(r=>setTimeout(()=>r('t'),20000))]))`;
const FRAMES = `Promise.race([new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))),
  new Promise(r=>setTimeout(r,1500))])`;
const READY = `(async()=>{for(let i=0;i<900;i++){ const S=window.SIM;
  if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot){ await ${NPCSETTLED}; return true; } }
  await new Promise(r=>setTimeout(r,100));} return false;})()`;
const settle = (cdp) => ev(cdp, `(async()=>{ for(let i=0;i<300;i++){
    const c=SIM.cine&&SIM.cine();
    if(!SIM.transitions().busy && (!c || !c.pending.length)) { await new Promise(r=>setTimeout(r,120));
      const c2=SIM.cine&&SIM.cine();
      if(!c2||!c2.pending.length){ await ${NPCSETTLED}; await ${FRAMES};
        const n=window.Npc&&Npc.debug?Npc.debug():null;
        if(!n||!n.building) return true; } }
    await new Promise(r=>setTimeout(r,100)); } return false; })()`, 180000);

const STATE = `(()=>{ const c=SIM.cine&&SIM.cine();
  return {scene:SIM.scene(), shot:(c&&c.shot)||'-', gpu:SIM.gpu(),
          occ:SIM.occ?SIM.occ():null, pos:SIM.pos(),
          fol: window.Followers&&Followers.debug?Followers.debug():null}; })()`;

// THE RESIDENT SET, named. Dedup by geometry uuid, dispose one at a time, keep the
// ones that moved the counter, and record whether their owner was drawable. This is
// destructive only in the sense sceneDispose() already is: the next drawn frame
// re-uploads whatever is still on screen.
const RESIDENT = `(()=>{ const SC=(typeof scene!=='undefined')?scene:window.scene;
  const seen=new Map();
  SC.traverse(o=>{ const g=o.geometry; if(!g) return;
    if(seen.has(g.uuid)) { seen.get(g.uuid).owners.push(o.name||'(anon)'); return; }
    let vis=true, p=o; const chain=[]; while(p){ chain.push(p.name||p.type); if(p.visible===false) vis=false; p=p.parent; }
    seen.set(g.uuid, {g:g, gt:g.type, name:o.name||'(anon)', type:o.type,
      parent:(o.parent&&(o.parent.name||o.parent.type))||'-', drawable:vis,
      chain:chain.slice(0,4).join('<'), owners:[o.name||'(anon)']}); });
  const res=[];
  for(const [,r] of seen){ const b=SIM.gpu(); r.g.dispose(); const a=SIM.gpu();
    if(b.geometries-a.geometries>0)
      res.push({gt:r.gt,name:r.name,type:r.type,parent:r.parent,drawable:r.drawable,
                chain:r.chain,n:r.owners.length}); }
  return {scanned:seen.size, resident:res}; })()`;

const ITIN = [['del-inn-int','del-cine'],['del-item-int','del-cine'],['ow-valley','del-cine'],
  ['del-weapon-int','del-cine'],['del-armor-int','del-cine'],['del-cookhouse-int','del-cine'],
  ['del-cottage-int','del-cine'],['ow-valley','del-cine'],['del-inn-int','del-cine'],
  ['del-item-int','del-cine'],['ow-valley','del-cine'],['del-cottage-int','del-cine']];

(async function main() {
  const cdp = await connect(await findPage(CDP_PORT, { tries: 240, label: 'gpu_baseline_probe' }));
  await cdp.send('Runtime.enable');
  if (await ev(cdp, READY, 300000) !== true) { console.log('FATAL: not playable'); kill(); process.exit(2); }
  const door = (to) => ev(cdp, `SIM.door(${JSON.stringify(to)})`, 300000);
  await settle(cdp);
  const rows = [];
  const line = (tag, s) => { rows.push({ tag, scene: s.scene, shot: s.shot, geo: s.gpu.geometries,
      tex: s.gpu.textures, ring: s.occ && s.occ.ring, nHits: s.occ && s.occ.nHits,
      first: s.occ && s.occ.first ? s.occ.first.name : null,
      pos: [+s.pos.x.toFixed(2), +s.pos.z.toFixed(2)] });
    const r = rows[rows.length - 1];
    console.log(`  ${String(tag).padEnd(9)} ${r.scene.padEnd(12)} ${String(r.shot).padEnd(11)} ` +
      `geo=${String(r.geo).padStart(5)} tex=${String(r.tex).padStart(3)} ring=${String(r.ring).padEnd(5)} ` +
      `nHits=${String(r.nHits).padStart(3)} first=${String(r.first || '-').padEnd(22)} pos=${r.pos}`); };

  console.log('\n== GAUNTLET (transition_test\'s own itinerary, 24 doors)');
  for (let i = 0; i < 24; i++) {
    const [to, ret] = ITIN[Math.floor(i / 2) % ITIN.length];
    const target = (i % 2 === 0) ? to : ret;
    if (target === await ev(cdp, 'SIM.scene()')) continue;
    const d = await door(target);
    if (d && d.error) { console.log(`  door ${i} -> ${target} ERROR ${JSON.stringify(d)}`); continue; }
    await settle(cdp);
    line('door ' + i, await ev(cdp, STATE));
  }

  console.log('\n== BATTLE MID-TOWN, THEN A DOOR (transition_test\'s own leg)');
  const bat = await ev(cdp, `(async()=>{
    if(!window.Battle||!window.GS||!GS.ok) return {skip:'no kernel'};
    const zones=GS.data.encounters.zones||{};
    const zk=Object.keys(zones).find(k=>(zones[k].groups||[]).length);
    const grp=zones[zk].groups[0]; const group=(grp&&(grp.monsters||grp.ids||grp.group||grp))||[];
    const p=Battle.start({zone:zk,group:[].concat(group),seed:7,backdrop:zk},null,{speed:0,autoplay:true});
    SIM.tick(120);
    const res=await Promise.race([p,new Promise(r=>setTimeout(()=>r('timeout'),150000))]);
    for(let i=0;i<300;i++){ if(!UILOCK.active()&&!Battle.active) break;
      await new Promise(r=>setTimeout(r,100)); }
    return {zone:zk,group,result:res==='timeout'?'timeout':((res&&res.outcome)||String(res))}; })()`, 200000);
  console.log('  ' + JSON.stringify(bat));
  await settle(cdp); line('postfight', await ev(cdp, STATE));
  await door('del-inn-int'); await settle(cdp); line('->inn', await ev(cdp, STATE));
  await door('del-cine'); await settle(cdp);
  const sFail = await ev(cdp, STATE); line('AFTER', sFail);

  const base = rows.find(r => r.scene === 'del-cine' && r.shot === 'shelf-west');
  console.log(`\n  shelf-west baseline geo=${base && base.geo}, after-battle geo=${sFail.gpu.geometries} ` +
    `=> DELTA ${sFail.gpu.geometries - (base ? base.geo : NaN)}` +
    (sFail.gpu.geometries - (base ? base.geo : 0) === 2 ? '  << REPRODUCED' : '  << not reproduced'));

  console.log('\n== RESIDENT SET, named by dispose-and-watch');
  const res = await ev(cdp, RESIDENT, 300000);
  console.log(`  scanned ${res.scanned} distinct geometries in the live graph; ${res.resident.length} were RESIDENT.`);
  const off = res.resident.filter(r => !r.drawable);
  console.log(`  of those, ${off.length} belong to an object that is NOT currently drawable:`);
  for (const r of off) console.log(`    ${r.gt.padEnd(22)} ${String(r.name).padEnd(24)} parent=${r.parent} chain=${r.chain}`);
  const byType = new Map();
  for (const r of res.resident) byType.set(r.gt, (byType.get(r.gt) || 0) + 1);
  console.log('  resident geometry types: ' + [...byType].map(([k, v]) => `${k}:${v}`).join(' '));
  writeFileSync(OUT, JSON.stringify({ rows, after: sFail, resident: res }, null, 2));
  console.log(`\n  wrote ${OUT}`);
  cdp.close(); kill();
})().catch(e => { console.error(e); kill(); process.exit(1); });
