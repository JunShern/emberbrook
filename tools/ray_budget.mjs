#!/usr/bin/env node
// ray_budget.mjs — THE VISIBILITY-RAY BUDGET GATE.
//
//   node tools/ray_budget.mjs --port=3000                 (standalone, own Chrome)
//   node tools/ray_budget.mjs --port=3000 --induce=3.0    (RED proof: tall scatter)
//   ...and imported by tools/transition_test.mjs, which already stands in ow-valley
//   three times in its own itinerary and pays ~0.15 s to run this there.
//
// ============================ WHY THIS EXISTS ================================
// The world arena's staging solve was 32 SECONDS. `--mode=raycost` billed it per
// mesh and 99.4% of every visibility ray was SIX InstancedMesh ground scatters
// (137,356 instances of six-triangle grass). The cause is STRUCTURAL, not a bad
// asset: play3d gives every ordinary mesh a three-mesh-bvh tree and an accelerated
// raycast, and an InstancedMesh gets NEITHER — three's raycast loops the instance
// list, so cost tracks INSTANCE COUNT and a 37,280-triangle tree is three thousand
// times cheaper than six-triangle grass.
//
// The shipped fix (battle_world.js, `SCATTER_H = 1.5`) drops instanced pieces under
// 1.5 m from the occluder set as ground detail. **THAT IS A HEIGHT THRESHOLD, NOT A
// BUDGET.** ow_detail.js's blade height is a live tunable (`OWD.set({hMax})`), and
// any bundle or scatter module that ships an instanced set TALLER than 1.5 m walks
// straight back into the 32-second solve with every gate in this repo green —
// because nothing in this repo measures the cost of a visibility ray. Same shape as
// cutin_edge measuring luminance and being blind to a chroma fringe: A GATE THAT
// MEASURES THE WRONG AXIS CANNOT SEE THE DEFECT.
//
// ==================== WHAT IT ASSERTS, AND WHY THAT QUANTITY ==================
// NOT microseconds. The per-mesh numbers in raycost.json bottom out at 4.2 us,
// which is 0.1 ms / 24 rays — the timer's own quantum, not a measurement — and any
// wall-clock ceiling on a laptop that also runs Blender bakes and a deploy lane is
// a ceiling that trips on an idle-vs-busy machine. A threshold that flaps is worse
// than none.
//
// It asserts W = UNACCELERATED TRIANGLE TESTS PER VISIBILITY RAY:
//
//     W = SUM over the module's own occluder set of  instanceCount(o) x tris(o)
//         for every o whose raycast is NOT BVH-accelerated
//         (an InstancedMesh is counted unaccelerated whatever its geometry carries,
//          because three loops the instance list either way — conservative on
//          purpose: a safety gate should cry wolf before it sleeps through one).
//
// W is a COUNT. It is the exact size of the inner loop three's raycast runs, it is
// the causal variable behind the 32 seconds, and it is identical on every machine.
//
// ==================== THE OCCLUDER RULE IS READ, NOT COPIED ===================
// The filter, the regex and SCATTER_H are EXTRACTED FROM public/js/battle_world.js
// AT RUN TIME and evaluated in the page. The gate therefore runs the SHIPPED rule
// against the SHIPPED constant: move SCATTER_H and the gate moves with it, which is
// the whole point (the defect this exists for IS a bundle that defeats that number).
// A copy would drift, and a drifted copy is a gate measuring its own drawing —
// CLAUDE.md's `_court_probe` lesson. If extraction fails the gate ERRORS; it never
// silently falls back to a guess.
//
// ==================== AN INSTRUMENT THAT FINDS NOTHING ========================
// ...must prove it could have found something. The census also counts the instanced
// meshes in the DRAWN scene, dropped ones included, and refuses to return a PASS
// unless it saw a real scatter (>= DETECT_INSTANCES instances). A census run before
// ow_detail has placed anything would otherwise report W = 0 forever.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const SRC = join(ROOT, 'public/js/battle_world.js');

// ---- THE CEILING, DERIVED FROM MEASUREMENT ---------------------------------
// Two measured anchors, both receipted in docs/qa/battle-world:
//
//   (a) THE SLOPE. The same staging solve cost 32,000 ms with the six scatters in
//       the occluder set and 407 ms without them at its worst cell
//       (stageperf.json, solve_ms_all.max). Those scatters are
//         60590*6 + 56126*6 + 16017*12 + 2179*36 + 1505*16 + 939*48 = 1,040,096
//       unaccelerated triangle tests per ray (raycost.json `worst`, count x tris).
//       So one staging solve costs
//         K = (32000 - 407) / 1040096 = 0.030375 ms per unit of W.
//
//   (b) THE BUDGET. "A battle must not take seconds to start" is the standing line
//       in battle_world_probe's own stageperf header, and the shipped worst case is
//       staging 407 ms inside a trigger-to-first-frame worst case of 871 ms. Holding
//       the WORST staging solve at or under 1000 ms keeps the worst first frame at
//       or under ~1464 ms — still under a second and a half, still not "seconds".
//       Allowance A = 1000 - 407 = 593 ms.
//
//   W_raw = A / K = 593 / 0.030375 = 19,522 tests per ray.
//
//   (c) SAFETY FACTOR 2. K was timed on this laptop with the machine quiet. The
//       deploy target and a machine mid-bake are comfortably 2x slower, and a gate
//       whose ceiling sits exactly on the cliff edge is a gate that certifies the
//       cliff. Halve it.
//
//   CEILING = 19522 / 2 = 9761 unaccelerated triangle tests per visibility ray.
//
// NOT ROUNDED, ON PURPOSE: the digits are the arithmetic above and a reader can
// re-derive them. Sanity on both sides — the CHEAPEST of the six shipped scatters
// (veg_owd_flower, 1505 x 16 = 24,080) busts it 2.5x on its own, so the defect
// cannot squeak through; and a legitimate tall instanced set of 200 fence posts at
// 40 triangles (8,000) passes, which is the class of thing that should.
export const K_MS_PER_TEST = 0.030375;     // ms of staging solve per unit of W
export const BASE_STAGE_MS = 407;          // stageperf.json solve_ms_all.max, post-fix
export const CEILING = 9761;               // unaccelerated triangle tests per ray
export const DETECT_INSTANCES = 1000;      // proof-of-detection floor

// ---- extract the shipped rule ----------------------------------------------
function braceBody(src, from) {
  const open = src.indexOf('{', from);
  if (open < 0) throw new Error('no brace after offset ' + from);
  let d = 0;
  for (let i = open; i < src.length; i++) {
    const c = src[i];
    if (c === '{') d++;
    else if (c === '}') { d--; if (d === 0) return { body: src.slice(open + 1, i), end: i }; }
  }
  throw new Error('unbalanced braces from offset ' + from);
}
export function shippedRule() {
  const src = readFileSync(SRC, 'utf8');
  const mH = src.match(/const\s+SCATTER_H\s*=\s*([0-9.]+)\s*;/);
  const mR = src.match(/const\s+NOT_OCCLUDER\s*=\s*(\/[^\n]*?\/[a-z]*)\s*;/);
  const iP = src.indexOf('function pieceHeight(o)');
  const iT = src.indexOf('sc.traverse((o) => {');
  if (!mH) throw new Error('ray_budget: SCATTER_H not found in ' + SRC);
  if (!mR) throw new Error('ray_budget: NOT_OCCLUDER not found in ' + SRC);
  if (iP < 0) throw new Error('ray_budget: pieceHeight() not found in ' + SRC);
  if (iT < 0) throw new Error('ray_budget: the occluder traverse not found in ' + SRC);
  const piece = braceBody(src, iP);
  const trav = braceBody(src, iT + 'sc.traverse('.length);
  return {
    scatterH: parseFloat(mH[1]),
    notOccluder: mR[1],
    pieceHeightBody: piece.body,
    filterBody: trav.body,
  };
}

// ---- the page-side census ---------------------------------------------------
// Read-only apart from three.js's own lazy computeBoundingBox, which the shipped
// pieceHeight already does on the same geometries every time a battle stages.
export function censusExpr(opt) {
  const R = shippedRule();
  const timing = !!(opt && opt.timing);
  return `(() => { try {
  const TH = window.THREE;
  const SC = (typeof scene !== 'undefined') ? scene : (window.scene || null);
  if (!SC) return { err: 'no scene global' };
  const SCATTER_H = ${R.scatterH};
  const NOT_OCCLUDER = ${R.notOccluder};
  const _scatH = (typeof WeakMap === 'function') ? new WeakMap() : null;
  function pieceHeight(o) {${R.pieceHeightBody}}
  const out = [], dropped = [];
  SC.traverse((o) => {${R.filterBody}});
  const triOf = (o) => { const g = o.geometry; if (!g) return 0;
    return g.index ? g.index.count / 3
         : (g.attributes && g.attributes.position ? g.attributes.position.count / 3 : 0); };
  let W = 0; const kept = [];
  for (const o of out) {
    const n = o.isInstancedMesh ? (o.count || 1) : 1;
    const t = triOf(o);
    const bvh = !!(o.geometry && o.geometry.boundsTree);
    const w = (bvh && !o.isInstancedMesh) ? 0 : n * t;
    W += w;
    if (w > 0) kept.push({ name: o.name || '(anon)', n: n, tris: t, inst: !!o.isInstancedMesh, bvh: bvh, w: w });
  }
  kept.sort((a, b) => b.w - a.w);
  // PROOF OF DETECTION — the drawn scene's instanced population, dropped included.
  let instMeshes = 0, instTotal = 0, tallest = 0;
  SC.traverse((o) => { if (o.isInstancedMesh && o.visible) {
    instMeshes++; instTotal += (o.count || 0);
    const h = pieceHeight(o); if (isFinite(h) && h > tallest) tallest = h; } });
  // SOFTWARE WebGL IS A DIFFERENT WORLD, and this is the module's OWN answer for
  // it. ow_detail.js refuses to place the scatter at all under swiftshader
  // (softwareGL() -> clear()), which is exactly the environment every headless
  // gauntlet gate in this repo runs in on purpose. A census there can still see
  // instancing that came out of a BUNDLE, and cannot see the runtime scatter.
  let soft = null;
  try { soft = (window.OWD && OWD.state) ? !!OWD.state().software : null; } catch (e) { soft = null; }
  if (soft == null) { try {
    const gl = (typeof R !== 'undefined' && R.getContext) ? R.getContext() : null;
    const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
    const s = gl ? ((dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '') + ' ' + gl.getParameter(gl.RENDERER)) : '';
    soft = /swiftshader|softwar|llvmpipe|mesa offscreen/i.test(s);
  } catch (e) { soft = null; } }
  const r = { scene: (window.SIM && SIM.scene) ? SIM.scene() : null,
    softwareGL: soft, scatterH: SCATTER_H, occluders: out.length,
    dropped: dropped, W: W, kept: kept.slice(0, 12),
    instMeshes: instMeshes, instTotal: instTotal,
    tallestPieceH: +tallest.toFixed(3),
    owd: (window.OWD && OWD.state) ? (() => { const s = OWD.state();
      return { draws: s.draws, blades: s.blades, tris: s.tris,
               hMin: s.params ? s.params.hMin : null, hMax: s.params ? s.params.hMax : null }; })() : null };
  ${timing ? `
  // TIMING IS REPORTED, NEVER ASSERTED (see the header). It exists to convert W
  // into milliseconds on THIS machine so a red line is actionable.
  if (TH && window.SIM && SIM.pos) {
    const P = SIM.pos();
    const rc = new TH.Raycaster(); const dirs = [];
    for (let i = 0; i < 24; i++) dirs.push(new TH.Vector3(Math.cos(i), 0.35, Math.sin(i)).normalize());
    const eye = new TH.Vector3(P.x, P.y + 3.5, P.z);
    const t0 = performance.now();
    for (const d of dirs) { rc.set(eye, d); rc.far = 40; rc.intersectObjects(out, true); }
    r.usPerRay = +((performance.now() - t0) / dirs.length * 1000).toFixed(1);
  }` : ''}
  return r;
} catch (e) { return { err: String((e && e.message) || e) }; } })()`;
}

// ---- the verdict -------------------------------------------------------------
// FOUR STATES, AND THE FOURTH IS THE ONE THIS PROJECT KEEPS PAYING FOR.
//
//   RED           W over the ceiling. Always fatal, in ANY environment — instancing
//                 that came out of a bundle is visible under software WebGL too.
//   GREEN         under the ceiling AND the census proved it could see a real
//                 scatter population.
//   SKIPPED       under the ceiling, no scatter seen, and the page is on SOFTWARE
//                 WebGL — where ow_detail.js refuses to place the scatter BY DESIGN
//                 (softwareGL() -> clear()). Every headless gate in this repo runs
//                 swiftshader deliberately, so this is not a failure, it is a
//                 measurement that half the defect surface is out of reach here.
//                 NOT a pass: the caller must not print it as one.
//   INCONCLUSIVE  under the ceiling, no scatter seen, and the GPU is real. Then the
//                 scatter should have been there and the instrument is looking at
//                 the wrong world — an instrument that finds nothing must prove it
//                 could have found something. Fatal.
export function verdict(c) {
  if (!c || c.err) return { ok: false, state: 'ERROR', why: 'census failed: ' + (c && c.err) };
  const ms = +(BASE_STAGE_MS + c.W * K_MS_PER_TEST).toFixed(0);
  if (c.W > CEILING)
    return { ok: false, state: 'RED', W: c.W, impliedStageMs: ms,
      why: `W = ${c.W} unaccelerated triangle tests per visibility ray, ceiling ${CEILING} ` +
           `(x${(c.W / CEILING).toFixed(1)} over). Implied worst staging solve ~${ms} ms. ` +
           'Offenders: ' + c.kept.slice(0, 4).map(k =>
             `${k.name} ${k.n}x${k.tris}${k.inst ? ' INSTANCED' : ''}${k.bvh ? '' : ' no-BVH'}`).join(', ') };
  if (!(c.instTotal >= DETECT_INSTANCES)) {
    if (c.softwareGL)
      return { ok: true, skipped: true, state: 'SKIPPED', W: c.W, impliedStageMs: ms,
        why: `software WebGL — ow_detail.js places NO scatter here by design, so the runtime ` +
             `half of this budget cannot be measured in this environment. Bundle-borne ` +
             `instancing WAS measured: W = ${c.W} / ${CEILING}. Run tools/ray_budget.mjs ` +
             `standalone (real GPU) for the whole surface.` };
    return { ok: false, state: 'INCONCLUSIVE', W: c.W,
      why: `the census saw ${c.instTotal} instanced pieces in the drawn scene (< ${DETECT_INSTANCES}) ` +
           `on a NON-software GPU; it cannot prove it could have found the defect, so it must ` +
           `not report a pass` };
  }
  return { ok: true, state: 'GREEN', W: c.W, impliedStageMs: ms,
    why: `W = ${c.W} / ${CEILING} (${(100 * c.W / CEILING).toFixed(2)}% of budget, ` +
         `${CEILING - c.W} to spare); implied worst staging solve ~${ms} ms` };
}

// ---- selftest: the verdict state machine, before any browser ------------------
// The RED proof that costs nothing and runs every time. `--selftest` asserts the
// four states on hand-built censuses, including the exact defect this gate exists
// for: ONE instanced scatter that clears SCATTER_H and therefore survives the
// module's filter. A gate whose own logic is never exercised on a failure is a
// gate nobody has seen fail.
export function selftest() {
  const base = { instTotal: 137356, softwareGL: false, kept: [], W: 0 };
  const cases = [
    ['current tree (W=2)', { ...base, W: 2, kept: [{ name: '__contact_shadow', n: 1, tris: 2, inst: false, bvh: false, w: 2 }] }, 'GREEN'],
    ['ONE tall scatter survives the 1.5 m rule',
      { ...base, W: 60590 * 6, kept: [{ name: 'veg_owd_short', n: 60590, tris: 6, inst: true, bvh: false, w: 363540 }] }, 'RED'],
    ['the cheapest of the six shipped scatters alone',
      { ...base, W: 1505 * 16, kept: [{ name: 'veg_owd_flower', n: 1505, tris: 16, inst: true, bvh: false, w: 24080 }] }, 'RED'],
    ['a legitimate tall instanced set (200 posts x 40 tris)',
      { ...base, W: 8000, kept: [{ name: 'fenceposts', n: 200, tris: 40, inst: true, bvh: false, w: 8000 }] }, 'GREEN'],
    ['exactly at the ceiling', { ...base, W: CEILING }, 'GREEN'],
    ['one test over the ceiling', { ...base, W: CEILING + 1 }, 'RED'],
    ['no scatter, software WebGL', { ...base, W: 2, instTotal: 0, softwareGL: true }, 'SKIPPED'],
    ['no scatter, REAL GPU', { ...base, W: 2, instTotal: 0, softwareGL: false }, 'INCONCLUSIVE'],
    ['over the ceiling under software WebGL is still fatal',
      { ...base, W: 500000, instTotal: 0, softwareGL: true, kept: [{ name: 'bundle_scatter', n: 10000, tris: 50, inst: true, bvh: false, w: 500000 }] }, 'RED'],
    ['a broken census', { err: 'no scene global' }, 'ERROR'],
  ];
  let bad = 0;
  for (const [label, c, want] of cases) {
    const v = verdict(c);
    const good = v.state === want;
    if (!good) bad++;
    console.log(`  ${good ? 'ok  ' : 'FAIL'} ${label} -> ${v.state}${good ? '' : ` (wanted ${want})`}`);
  }
  return bad;
}

// ---- standalone runner --------------------------------------------------------
if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.includes('--selftest')) {
    console.log(`ray_budget selftest — ceiling ${CEILING} unaccelerated triangle tests per visibility ray`);
    const bad = selftest();
    console.log(bad ? `\nFAIL ${bad} case(s)` : '\nPASS');
    process.exit(bad ? 1 : 0);
  }
  const { spawn } = await import('node:child_process');
  const { createRequire } = await import('node:module');
  const { freePort, findPage, killOrphans, sweepStaleProfiles } = await import('./cdp.mjs');
  const require = createRequire(import.meta.url);
  const WebSocket = require('ws');

  const argv = process.argv.slice(2);
  const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
  const PORT = parseInt(arg('port', '3000'), 10);
  const HEAD = argv.includes('--head');
  // --induce=<hMax>: THE RED PROOF. ow_detail.js's blade height is a shipped
  // tunable, so the defect can be induced without editing one line of runtime
  // code — OWD.set({hMax}) rebuilds the scatter taller than SCATTER_H and the six
  // ground scatters walk back into the occluder set. Nothing is committed and the
  // page is thrown away with the Chrome that hosted it.
  const INDUCE = arg('induce', null);
  const OUT = join(ROOT, arg('out', 'docs/qa/battle-world'));
  const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const CDP_PORT = await freePort();
  const PROFILE_PREFIX = 'ray-budget-gate-';
  sweepStaleProfiles(PROFILE_PREFIX);
  const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);
  const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&nomusic=1`;

  const chrome = spawn(CHROME, [
    `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1600,900',
    ...(HEAD ? [] : ['--headless=new']), URL,
  ], { stdio: 'ignore' });
  let closing = false;
  const kill = () => { if (closing) return; closing = true;
    try { chrome.kill('SIGKILL'); } catch (e) { }
    try { killOrphans(profile); } catch (e) { } };   // by OUR prefix only, never by name
  process.on('exit', kill);
  process.on('SIGINT', () => { kill(); process.exit(130); });

  const cdpWs = await findPage(CDP_PORT, { tries: 250, label: 'ray_budget' });
  const cdp = await new Promise((res, rej) => {
    const ws = new WebSocket(cdpWs, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({
      send(m, p) { return new Promise((ok2, no) => { const mid = ++id; pend.set(mid, { ok2, no }); ws.send(JSON.stringify({ id: mid, method: m, params: p || {} })); }); },
      close() { try { ws.close(); } catch (e) { } } }));
    ws.on('error', rej);
    ws.on('message', (raw) => { let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok2, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(m.error.message)) : ok2(m.result); } });
  });
  const ev = async (expr, ms) => {
    const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, timeout: ms || 120000 });
    if (r.exceptionDetails) throw new Error('page exception: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result && r.result.value;
  };
  await cdp.send('Runtime.enable');
  const ready = await ev(`(async () => { for (let i = 0; i < 400; i++) {
      if (window.SIM && window.THREE && SIM.pos && SIM.floors(SIM.pos().x, SIM.pos().z).length
          && window.OWD && OWD.state().draws > 0) return { ready: true, scene: SIM.scene(), owd: OWD.state().draws };
      await new Promise(r => setTimeout(r, 200)); }
    return { ready: false, owd: window.OWD ? OWD.state().draws : null }; })()`, 180000);
  if (!ready.ready) { console.error('ow-valley never became ready with a live scatter:', JSON.stringify(ready)); kill(); process.exit(2); }
  console.log(`ready  scene=${ready.scene}  OWD meshes=${ready.owd}`);

  if (INDUCE != null) {
    const r = await ev(`(() => { const before = OWD.state();
      OWD.set({ hMin: ${parseFloat(INDUCE) * 0.6}, hMax: ${parseFloat(INDUCE)} });
      const after = OWD.state();
      return { before: { draws: before.draws, blades: before.blades, hMax: before.params.hMax },
               after: { draws: after.draws, blades: after.blades, hMax: after.params.hMax } }; })()`, 120000);
    console.log(`INDUCED a tall scatter: OWD.set({hMax:${INDUCE}})  ${JSON.stringify(r)}`);
  }

  const c = await ev(censusExpr({ timing: true }), 300000);
  const v = verdict(c);
  const rec = { at: new Date().toISOString(), induced: INDUCE ? parseFloat(INDUCE) : null,
                ceiling: CEILING, kMsPerTest: K_MS_PER_TEST, baseStageMs: BASE_STAGE_MS,
                census: c, verdict: v };
  mkdirSync(OUT, { recursive: true });
  const file = join(OUT, INDUCE ? 'raybudget-induced.json' : 'raybudget.json');
  writeFileSync(file, JSON.stringify(rec, null, 2));
  console.log(JSON.stringify(rec, null, 2));
  console.log(`\nwrote ${file}`);
  console.log(`\n${v.state}  ${v.why}`);
  cdp.close(); kill();
  // SKIPPED is a pass for a host gate that cannot see the whole surface; it is NOT
  // a pass here — this runner exists to be the one that can.
  process.exit(v.ok && !v.skipped ? 0 : 1);
}
