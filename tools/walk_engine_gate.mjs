// walk_engine_gate.mjs — DOES THE ENGINE FIND THE FLOOR THAT IS IN THE FILE?
//
//   node tools/walk_engine_gate.mjs --port 3000                      del-cine (default)
//   node tools/walk_engine_gate.mjs --scene emb-townwalk --port 3000
//   node tools/walk_engine_gate.mjs --region x0,x1,z0,z1             one district
//   node tools/walk_engine_gate.mjs --step 0.45                      lattice (default 0.45 m)
//   node tools/walk_engine_gate.mjs --max-lost N                     gate mode (default 0)
//   node tools/walk_engine_gate.mjs --json out.json                  every disagreeing cell
//   node tools/walk_engine_gate.mjs --reduced                        THE MECHANISM, no browser
//
// WHY THIS EXISTS, and it is the hole a whole class of defect lived in. On 2026-08-02
// Festival Square was measured twice on the same bytes and answered twice:
//
//     the shipped GLB says          2220 standable cells   449.6 m2   75.4%
//     the shipped RUNTIME says      1213 standable cells   245.6 m2   41.2%
//
// 204 m2 — a third of the square — was floor that existed in the file and that the
// player could not stand on. A straight 4.5 m walk across open plaza driven by the
// runtime's own phys() travelled 0.00 m. Every gate in this repo was green through
// all of it, because every one of them reads THE FILE:
//
//   walk_bodygate  enumerates samples from the walk meshes' own AABBs and scores the
//                  step between two points that both have floor. It reported 0.00%
//                  blocked over this exact square.
//   glb_read       is the file, by construction.
//   cine_solve /   solve and derive from <town>.map.json and the bundle's geometry.
//   routes_derive
//
// A WALK-NETWORK GATE THAT NEVER ASKS THE ENGINE IS MEASURING THE ARTIST'S INTENT,
// NOT THE PLAYER'S WORLD. This file asks the engine. It samples the same lattice two
// ways — triangles out of the shipped GLB here, SIM.walkFloors() inside real Chrome
// there — and fails when they disagree.
//
// THE DEFECT IT WAS BUILT FROM (fixed at public/play3d.html's BVH build site, and
// reproduced by --reduced): three-mesh-bvh builds its tree by PERMUTING
// geometry.index.array IN PLACE, and GLTFLoader hands every primitive that references
// the same glTF index accessor the SAME BufferAttribute instance. Blender's exporter
// dedupes identical index buffers, so 41 of the square's walk blocks arrived sharing
// one array: each build scrambled the index its predecessors' trees were built
// against, and those meshes went silently non-collidable. Bounds correct, rays into
// nothing. It cost Emberbrook 64 of 218 walk meshes and Dellhollow 4 of 312.
//
// WHAT AGREEMENT MEANS HERE. The file side reproduces play3d's colTops() contract
// exactly and deliberately: a down-ray, and only faces whose WORLD normal has y > 0.5
// (signed — the engine's materials are FrontSide, so a down-ray never sees a
// down-facing face, and the `wn(h).y>.5` filter keeps the rest). It compares
// STANDABILITY, not height: a cell box whose top ring is wound inside-out gives the
// walker its bottom face, 0.14 m low, on both sides of this comparison — a real
// finding, but a different one, and heights are reported for information only.
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import vm from 'vm';
import { loadGlb, WALK_RE } from './glb_read.mjs';
import { PUB } from './cine_regions.mjs';
import { freePort, killOrphans, findPage, chromeArgs, sweepStaleProfiles } from './cdp.mjs';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const has = (n) => ARGS.includes(n);
const SCENE = opt('--scene', 'del-cine');
const STEP = +opt('--step', '0.45');
const PORT = +opt('--port', '3000');
const MAXLOST = +opt('--max-lost', '0');
const OUTJSON = opt('--json', null);
const REGION = opt('--region', null) ? opt('--region', null).split(',').map(Number) : null;
const GLB = opt('--glb', null) || path.join(PUB, 'assets/scenes', SCENE, 'scene.glb');
if (!fs.existsSync(GLB)) { console.error(`no bundle at ${GLB}`); process.exit(1); }

// ---------------------------------------------------------------------------
// THE FILE SIDE: standable cells straight out of the GLB's triangles.
// ---------------------------------------------------------------------------
function fileCensus() {
  const G = loadGlb(GLB);
  const T = G.trisFlat(WALK_RE);
  // keep only up-facing triangles — play3d's own filter, and the only ones a
  // FrontSide down-ray can return
  const keep = [];
  for (let t = 0; t < T.count; t++) {
    const o = t * 9;
    const ax = T.pos[o], ay = T.pos[o + 1], az = T.pos[o + 2];
    const bx = T.pos[o + 3], by = T.pos[o + 4], bz = T.pos[o + 5];
    const cx = T.pos[o + 6], cy = T.pos[o + 7], cz = T.pos[o + 8];
    const ux = bx - ax, uy = by - ay, uz = bz - az;
    const vx = cx - ax, vy = cy - ay, vz = cz - az;
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const nl = Math.hypot(nx, ny, nz) || 1e-12;
    if (ny / nl <= 0.5) continue;
    keep.push(t);
  }
  // uniform xz bucket grid over the kept triangles: 8000 cells x 40k triangles is a
  // 320 M-pair brute force and a gate nobody runs
  const BS = Math.max(STEP * 4, 1.0);
  const buckets = new Map();
  const key = (i, j) => i * 100000 + j;
  const triBox = new Float64Array(keep.length * 4);
  keep.forEach((t, k) => {
    const o = t * 9;
    const x0 = Math.min(T.pos[o], T.pos[o + 3], T.pos[o + 6]);
    const x1 = Math.max(T.pos[o], T.pos[o + 3], T.pos[o + 6]);
    const z0 = Math.min(T.pos[o + 2], T.pos[o + 5], T.pos[o + 8]);
    const z1 = Math.max(T.pos[o + 2], T.pos[o + 5], T.pos[o + 8]);
    triBox[k * 4] = x0; triBox[k * 4 + 1] = x1; triBox[k * 4 + 2] = z0; triBox[k * 4 + 3] = z1;
    for (let i = Math.floor(x0 / BS); i <= Math.floor(x1 / BS); i++)
      for (let j = Math.floor(z0 / BS); j <= Math.floor(z1 / BS); j++) {
        const kk = key(i, j); let a = buckets.get(kk); if (!a) buckets.set(kk, a = []); a.push(k);
      }
  });

  // THE LATTICE: every cell any walk mesh's own xz footprint claims, snapped to one
  // global grid so the two sides sample identical points. Sampling a whole town's
  // bounding square instead would spend 98% of the run on empty meadow.
  const cells = new Map();
  const snap = (v) => Math.round(v / STEP);
  for (const { i } of G.nodesNamed(WALK_RE)) {
    const b = G.nodeBox(i); if (!b) continue;
    if (REGION && (b.max[0] < REGION[0] || b.min[0] > REGION[1] || b.max[2] < REGION[2] || b.min[2] > REGION[3])) continue;
    for (let gi = snap(b.min[0]); gi <= snap(b.max[0]); gi++)
      for (let gj = snap(b.min[2]); gj <= snap(b.max[2]); gj++) {
        const x = gi * STEP, z = gj * STEP;
        if (REGION && (x < REGION[0] || x > REGION[1] || z < REGION[2] || z > REGION[3])) continue;
        cells.set(key(gi, gj), [x, z]);
      }
  }

  const pts = [...cells.values()];
  const stand = new Uint8Array(pts.length);
  const topY = new Float64Array(pts.length);
  for (let c = 0; c < pts.length; c++) {
    const [x, z] = pts[c];
    const a = buckets.get(key(Math.floor(x / BS), Math.floor(z / BS)));
    if (!a) continue;
    let best = -Infinity;
    for (const k of a) {
      if (x < triBox[k * 4] || x > triBox[k * 4 + 1] || z < triBox[k * 4 + 2] || z > triBox[k * 4 + 3]) continue;
      const o = keep[k] * 9;
      const ax = T.pos[o], ay = T.pos[o + 1], az = T.pos[o + 2];
      const bx = T.pos[o + 3], by = T.pos[o + 4], bz = T.pos[o + 5];
      const cx2 = T.pos[o + 6], cy = T.pos[o + 7], cz = T.pos[o + 8];
      const den = (bz - cz) * (ax - cx2) + (cx2 - bx) * (az - cz);
      if (Math.abs(den) < 1e-12) continue;
      const l1 = ((bz - cz) * (x - cx2) + (cx2 - bx) * (z - cz)) / den;
      const l2 = ((cz - az) * (x - cx2) + (ax - cx2) * (z - cz)) / den;
      const l3 = 1 - l1 - l2;
      if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) continue;
      const y = l1 * ay + l2 * by + l3 * cy;
      if (y > best) best = y;
    }
    if (best > -Infinity) { stand[c] = 1; topY[c] = best; }
  }
  return { pts, stand, topY, tris: keep.length };
}

// ---------------------------------------------------------------------------
// THE ENGINE SIDE: SIM.walkFloors() in real Chrome, on the same points.
// ---------------------------------------------------------------------------
const WebSocket = require('ws');
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); const evs = []; let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((ok, no) => { const mid = ++id; pend.set(mid, { ok, no }); ws.send(JSON.stringify({ id: mid, method, params: params || {} })); });
      }, events: evs, close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); return; }
      if (m.method) evs.push(m);
    });
  });
}
async function ev(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, timeout: timeoutMs || 180000 });
  if (r.exceptionDetails) throw new Error('page exception: ' + ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text));
  return r.result && r.result.value;
}

async function engineCensus(pts) {
  const CDP_PORT = await freePort();
  const profile = join(process.env.TMPDIR || '/tmp', `walk-engine-gate-profile-${process.pid}`);
  sweepStaleProfiles('walk-engine-gate-profile-');
  killOrphans(profile);
  const url = `http://127.0.0.1:${PORT}/play.html?scene=${SCENE}&nomusic=1`;
  const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    chromeArgs({ port: CDP_PORT, profile, url }), { stdio: 'ignore' });
  const kill = () => { try { chrome.kill('SIGKILL'); } catch (e) { } try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) { } };
  process.on('exit', kill);
  for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { kill(); process.exit(130); });

  const cdp = await connect(await findPage(CDP_PORT, { tries: 240, label: 'walk_engine_gate' }));
  await cdp.send('Runtime.enable');
  // READINESS: SIM.pos() answers long before a 91 MB GLB is parsed, and a half-loaded
  // world confidently reports no floor anywhere. gpu().walk is the walk mesh count —
  // it is zero until the bundle's traverse has actually run.
  const ready = await ev(cdp, `(async()=>{for(let i=0;i<600;i++){
    const S=window.SIM; if(S&&S.gpu&&S.gpu().walk>0) return S.gpu().walk;
    await new Promise(r=>setTimeout(r,100));} return 0;})()`, 90000);
  if (!ready) { kill(); throw new Error(`the runtime never loaded a walk mesh for scene=${SCENE} (SIM.gpu().walk stayed 0)`); }
  const bvh = await ev(cdp, `window.SIM.bvh?JSON.stringify(SIM.bvh()):'null'`);

  const stand = new Uint8Array(pts.length);
  const topY = new Float64Array(pts.length);
  const CH = 4000;
  for (let i = 0; i < pts.length; i += CH) {
    const chunk = pts.slice(i, i + CH);
    const flat = JSON.stringify(chunk.flat());
    const out = await ev(cdp, `(()=>{const P=${flat},n=P.length/2,s=new Array(n),y=new Array(n);
      for(let k=0;k<n;k++){const f=SIM.walkFloors(P[k*2],P[k*2+1]); s[k]=f.length?1:0; y[k]=f.length?Math.max.apply(null,f):0;}
      return {s:s.join(''),y};})()`, 300000);
    for (let k = 0; k < chunk.length; k++) { stand[i + k] = out.s[k] === '1' ? 1 : 0; topY[i + k] = out.y[k]; }
  }
  const gpu = await ev(cdp, `JSON.stringify(SIM.gpu())`);
  cdp.close(); kill();
  return { stand, topY, bvh: JSON.parse(bvh), gpu: JSON.parse(gpu), walkMeshes: ready };
}

// ---------------------------------------------------------------------------
// --reduced: THE MECHANISM, in one process, no browser, no server.
// Loads this repo's OWN three.js and three-mesh-bvh (public/lib) and builds the
// walk primitives three ways over the shipped bundle's largest shared-index group.
// ---------------------------------------------------------------------------
function reduced() {
  const THREE = require(join(HERE, '../public/lib/three.min.js'));
  globalThis.THREE = THREE;
  vm.runInThisContext(fs.readFileSync(join(HERE, '../public/lib/three-mesh-bvh.js'), 'utf8'), { filename: 'three-mesh-bvh.js' });
  const BVH = globalThis.MeshBVHLib;
  const G = loadGlb(GLB), J = G.json;
  // the walk primitives, grouped by the glTF index accessor they name
  const groups = new Map();
  for (const { i, name } of G.nodesNamed(WALK_RE)) {
    const nd = J.nodes[i]; if (nd.mesh === undefined) continue;
    for (const p of J.meshes[nd.mesh].primitives) {
      if (p.indices === undefined || p.attributes.POSITION === undefined) continue;
      if (!groups.has(p.indices)) groups.set(p.indices, []);
      groups.get(p.indices).push({ name, prim: p });
    }
  }
  const shared = [...groups.entries()].filter(([, m]) => m.length > 1)
    .sort((a, b) => b[1].length - a[1].length);
  console.log(`three.js r${THREE.REVISION} + public/lib/three-mesh-bvh.js, bundle ${path.basename(path.dirname(GLB))}`);
  console.log(`${G.nodesNamed(WALK_RE).length} walk primitives resolve to ${groups.size} glTF index accessors;`);
  console.log(`${shared.length} of those accessors are shared by more than one geometry, and GLTFLoader caches`);
  console.log(`accessors — so every sharer receives the SAME BufferAttribute, i.e. ONE index array.\n`);

  // A down-ray per 0.25 m of each mesh's own footprint. Sampling only the centre is
  // not enough: these walk blocks are concave (a plaza with solids cut out of it) and
  // a corrupted tree can still answer at one point.
  const probe = (mode, members, idxAcc) => {
    const sharedAttr = new THREE.BufferAttribute(G.accessor(idxAcc), 1);
    const items = members.map(({ name, prim }) => {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(G.accessor(prim.attributes.POSITION), 3));
      geo.setIndex(mode === 'shared' ? sharedAttr : new THREE.BufferAttribute(G.accessor(idxAcc), 1));
      geo.computeBoundingBox();
      const bb = geo.boundingBox.clone();                       // BEFORE a BVH can touch it
      const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ colorWrite: false }));  // = play3d's hideMat
      m.name = name; m.updateMatrixWorld(true); return { m, bb };
    });
    if (mode !== 'none') for (const { m } of items) {
      m.geometry.boundsTree = new BVH.MeshBVH(m.geometry, { setBoundingBox: false });
      m.raycast = BVH.acceleratedRaycast;
    }
    let hit = 0;
    for (const { m, bb } of items)
      for (let x = bb.min.x + .125; x < bb.max.x; x += .25)
        for (let z = bb.min.z + .125; z < bb.max.z; z += .25) {
          const rc = new THREE.Raycaster(new THREE.Vector3(x, 80, z), new THREE.Vector3(0, -1, 0), 0, 160);
          const its = []; m.raycast(rc, its); if (its.length) hit++;
        }
    return hit;
  };

  let tNone = 0, tShared = 0, tPriv = 0, worst = null;
  for (const [idxAcc, members] of shared) {
    const none = probe('none', members, idxAcc);
    const shr = probe('shared', members, idxAcc);
    const priv = probe('private', members, idxAcc);
    tNone += none; tShared += shr; tPriv += priv;
    if (!worst || none - shr > worst.loss) worst = { idxAcc, members, none, shr, priv, loss: none - shr };
  }
  console.log(`  over every shared-index group, samples that find floor:`);
  console.log(`    no BVH at all (three.js Mesh.raycast)         ${String(tNone).padStart(6)}`);
  console.log(`    BVH, ONE shared index array  = the defect     ${String(tShared).padStart(6)}   ${tNone ? (100 * (tNone - tShared) / tNone).toFixed(1) : '0.0'}% of the floor gone`);
  console.log(`    BVH, a private index per geometry = the fix   ${String(tPriv).padStart(6)}`);
  if (worst && worst.loss > 0)
    console.log(`\n  worst group: accessor ${worst.idxAcc}, ${worst.members.length} meshes (${worst.members[0].name}, ...)` +
      `\n    ${worst.none} samples with no BVH -> ${worst.shr} with the shared index -> ${worst.priv} with a private one`);
  const ok = tNone === tPriv && tShared < tNone;
  console.log(ok
    ? `\nMECHANISM CONFIRMED. three-mesh-bvh permutes geometry.index.array IN PLACE while it\nbuilds; two geometries on one array scramble each other's trees. A private copy per\ngeometry restores every sample (${tPriv} = ${tNone}), which is the fix in play3d.html.`
    : `\nNOT REPRODUCED on this bundle: ${tShared === tNone ? 'no shared group loses anything (every member partitions identically, so the permutation is idempotent)' : 'the private-index build does not restore the file — look further'}.`);
  return 0;   // informational: --reduced explains, it never gates
}

// ---------------------------------------------------------------------------
(async function main() {
  if (has('--reduced')) { process.exit(reduced()); }

  const t0 = Date.now();
  const F = fileCensus();
  const fileN = F.stand.reduce((a, b) => a + b, 0);
  console.log(`file   ${path.relative(process.cwd(), GLB)}`);
  console.log(`       ${F.tris} up-facing walk triangles, lattice ${STEP} m, ${F.pts.length} cells over the walk footprint`);

  const E = await engineCensus(F.pts);
  const engN = E.stand.reduce((a, b) => a + b, 0);
  const A = STEP * STEP;

  const lost = [], invented = [], dh = [];
  for (let i = 0; i < F.pts.length; i++) {
    if (F.stand[i] && !E.stand[i]) lost.push(i);
    else if (!F.stand[i] && E.stand[i]) invented.push(i);
    else if (F.stand[i] && E.stand[i]) dh.push(Math.abs(F.topY[i] - E.topY[i]));
  }
  dh.sort((a, b) => a - b);

  console.log(`engine scene=${SCENE}  ${E.walkMeshes} walk meshes  BVH built ${E.bvh ? E.bvh.built : '?'} copies ${E.bvh ? E.bvh.copies : '?'} FAIL ${E.bvh ? E.bvh.fail : '?'}`);
  console.log('');
  console.log(`  standable in the FILE    ${String(fileN).padStart(6)} cells  ${(fileN * A).toFixed(1).padStart(8)} m2`);
  console.log(`  standable in the ENGINE  ${String(engN).padStart(6)} cells  ${(engN * A).toFixed(1).padStart(8)} m2`);
  console.log(`  LOST  (file yes, engine no)   ${String(lost.length).padStart(6)} cells  ${(lost.length * A).toFixed(1).padStart(8)} m2   ${fileN ? (100 * lost.length / fileN).toFixed(2) : '0.00'}% of the walk network`);
  console.log(`  extra (engine yes, file no)   ${String(invented.length).padStart(6)} cells  ${(invented.length * A).toFixed(1).padStart(8)} m2`);
  if (dh.length) console.log(`  height agreement on shared cells: median ${dh[dh.length >> 1].toFixed(3)} m, p95 ${dh[Math.floor(dh.length * .95)].toFixed(3)} m  (INFORMATION ONLY — see the header)`);

  if (OUTJSON) {
    fs.writeFileSync(OUTJSON, JSON.stringify({
      scene: SCENE, glb: GLB, step: STEP, region: REGION, bvh: E.bvh,
      cells: F.pts.length, fileStandable: fileN, engineStandable: engN,
      lost: lost.map(i => ({ x: F.pts[i][0], z: F.pts[i][1], y: F.topY[i] })),
      invented: invented.map(i => ({ x: F.pts[i][0], z: F.pts[i][1] })),
    }, null, 1));
    console.log(`  wrote ${OUTJSON}`);
  }

  const fails = [];
  if (E.bvh && E.bvh.fail > 0) fails.push(`${E.bvh.fail} collision BVH(s) failed to build (SIM.bvh().fail)`);
  if (lost.length > MAXLOST) fails.push(`${lost.length} cells (${(lost.length * A).toFixed(1)} m2) are floor in the file that the engine will not stand on (--max-lost ${MAXLOST})`);
  console.log('');
  if (fails.length) { for (const f of fails) console.log(`  RED  ${f}`); console.log(`\n${((Date.now() - t0) / 1000).toFixed(1)}s`); process.exit(1); }
  console.log(`  GREEN  the engine finds every standable cell the file has.`);
  console.log(`\n${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e && e.stack || e); process.exit(2); });
