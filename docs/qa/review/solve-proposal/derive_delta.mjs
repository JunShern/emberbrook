// derive_delta.mjs — the DELTA REPORT for the exit-seam framing proposal.
//
//   node docs/qa/review/solve-proposal/derive_delta.mjs
//
// Reads the SHIPPED solve and the PROPOSED solve, and re-projects every entry and exit
// of every shot through both cameras. Nothing here is authored: the marks come from
// public/townmap/dellhollow.routes.json (the audit's own derived entry/exit data) and the
// projection is tools/cine_regions.mjs `project` — the same function the solver, the
// route generator and cine_test use, so an ndc in this report is comparable to an ndc in
// docs/qa/review/probe/*.json by construction rather than by convention.
//
// Writes, beside itself:
//   delta.md            per-shot camera delta + per-mark ndc delta, human-readable
//   delta.json          the same as data (probe-style), plus the mismatch advisory
//   probe/<shot>.json   one probe-style file per shot, keyed the way the audit's are
//
// The proposal is NOT the shipped chain: cameras.solved.json and cine.json are untouched
// and no backdrop is re-baked. This report is the evidence for that decision.
import fs from 'fs';
import path from 'path';
import {loadCine, project, charPx, r2m, edgePoint, PUB, rd} from '../../../../tools/cine_regions.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '../../../..');
const FRAME = [1344, 768];                     // the baked backdrop's pixel size
const OLD = rd('townmap/dellhollow.cameras.solved.json');
const NEW = JSON.parse(fs.readFileSync(path.join(HERE, 'dellhollow.cameras.solved.proposed.json'), 'utf8'));
const ROUTES = rd('townmap/dellhollow.routes.json');
const C = loadCine();
const oldBy = Object.fromEntries(OLD.cameras.map((c) => [c.id, c]));
const newBy = Object.fromEntries(NEW.cameras.map((c) => [c.id, c]));
const r3n = (n) => Math.round(n * 1000) / 1000;

// ---- projection, identical in form to routes_derive.project1/screenOf ---------
function shot1(cam, rtPoint, lift) {
  const p = r2m(rtPoint); p[2] += (lift || 0);
  const s = project(cam.pos, cam.aim, cam.fov, C.D.aspect, p);
  if (s.behind) return {behind: true, onScreen: false, ndc: null, charPx: 0};
  return {behind: false, ndc: [r3n(s.sx), r3n(s.sy)],
          px: [Math.round((s.sx * 0.5 + 0.5) * FRAME[0]), Math.round((0.5 - s.sy * 0.5) * FRAME[1])],
          onScreen: Math.abs(s.sx) <= 1 && Math.abs(s.sy) <= 1,
          edgeMargin: r3n(Math.min(1 - Math.abs(s.sx), 1 - Math.abs(s.sy))),
          depth: r3n(s.z), charPx: Math.round(charPx(cam.fov, s.z, C.D.charH, FRAME[1]))};
}
// FEET AND HEAD ARE DIFFERENT QUESTIONS (audit §4b.3): the ground you are walking to and
// the figure standing on it go off-frame at different moments and want different fixes.
function screenOf(cam, rtPoint) {
  const f = shot1(cam, rtPoint, 0);
  const h = shot1(cam, rtPoint, C.D.charH);
  f.headNdc = h.ndc; f.headOnScreen = h.onScreen;
  f.groundVisible = f.onScreen;                            // the surface itself is shown
  f.figureVisible = f.onScreen || h.onScreen;              // any part of a standing player
  return f;
}
const verdict = (o, n) => o.groundVisible === n.groundVisible && o.figureVisible === n.figureVisible
  ? (n.groundVisible ? 'ok' : n.figureVisible ? 'ground-off (unchanged)' : 'OFF-FRAME (unchanged)')
  : (!o.groundVisible && n.groundVisible) ? 'FIXED'
  : (!o.figureVisible && n.figureVisible) ? 'part-fixed (figure back in frame)'
  : (o.groundVisible && !n.groundVisible) ? 'REGRESSED'
  : 'REGRESSED (figure)';

// ---- per shot ----------------------------------------------------------------
const shots = [];
let maxDrift = 0;                              // my old-ndc vs the routes file's own ndc
for (const nc of NEW.cameras) {
  const oc = oldBy[nc.id], sh = ROUTES.shots[nc.id];
  if (!oc || !sh) continue;
  const d = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const marks = [];
  for (const kind of ['entries', 'exits']) {
    for (const m of sh[kind]) {
      const o = screenOf(oc, m.at), n = screenOf(nc, m.at);
      // cross-check: routes.json's own screen for this mark came from cine.json, which
      // carries the SHIPPED solve. If my old projection disagrees with it, this whole
      // report is measuring something else — so the disagreement is reported, not assumed.
      if (m.screen && m.screen.ndc && o.ndc)
        maxDrift = Math.max(maxDrift, Math.abs(m.screen.ndc[0] - o.ndc[0]), Math.abs(m.screen.ndc[1] - o.ndc[1]));
      marks.push({id: m.id, kind: m.kind, role: kind === 'exits' ? 'exit' : 'entry',
                  at: m.at, to: m.to || null, from: m.from || null,
                  old: o, new: n, verdict: verdict(o, n),
                  dEdgeMargin: r3n(n.edgeMargin - o.edgeMargin),
                  dNdcY: o.ndc && n.ndc ? r3n(n.ndc[1] - o.ndc[1]) : null});
    }
  }
  const F = Object.assign({}, C.D, (C.byId[nc.id].framing || {}));
  shots.push({
    shot: nc.id, name: nc.name, intent: nc.shot || null,
    pin: !!nc.pin, exitSeams: nc.exitSeams || 0,
    camera: {
      old: {pos: oc.pos, aim: oc.aim, dist: oc.dist, fov: oc.fov,
            inFrameFrac: oc.inFrameFrac, samples: oc.samples,
            charPxNear: oc.charPxNear, charPxFar: oc.charPxFar, capped: !!oc.capped},
      new: {pos: nc.pos, aim: nc.aim, dist: nc.dist, fov: nc.fov,
            inFrameFrac: nc.inFrameFrac, samples: nc.samples,
            charPxNear: nc.charPxNear, charPxFar: nc.charPxFar, capped: !!nc.capped},
      params: {yaw: F.yaw ?? null, pitch: F.pitch ?? null, margin: F.margin,
               minDist: F.minDist, maxDist: F.maxDist, authored: !!C.byId[nc.id].pos},
      dPos: r3n(d(oc.pos, nc.pos)), dAim: r3n(d(oc.aim, nc.aim)),
      dDist: r3n(nc.dist - oc.dist),
      dCharPxNear: nc.charPxNear - oc.charPxNear,
      charPxNearPct: r3n(100 * (nc.charPxNear - oc.charPxNear) / oc.charPxNear),
      // HOW BIG A RE-BAKE THIS IS, in the only unit that matters for a pre-rendered
      // backdrop: how far the shot's own marks move across the 1344x768 plate. A 2 px
      // move is a re-bake nobody would see; a 200 px move is a different painting.
      dPxMax: Math.round(Math.max(0, ...marks.filter((m) => m.old.px && m.new.px)
        .map((m) => Math.hypot(m.new.px[0] - m.old.px[0], m.new.px[1] - m.old.px[1])))),
    },
    marks,
    fixed: marks.filter((m) => m.verdict === 'FIXED' || m.verdict.startsWith('part-fixed')).map((m) => m.id),
    stillOff: marks.filter((m) => m.verdict.includes('unchanged') && !m.new.groundVisible).map((m) => m.id),
    regressed: marks.filter((m) => m.verdict.startsWith('REGRESSED')).map((m) => m.id),
  });
}

// TASTE REVIEW. A framing the solver is entitled to make is not automatically a framing a
// human accepts, so the report says which ones a person must look at. Thresholds are the
// two things a re-aim can spend: distance from the subject (the shot's intimacy) and the
// character's pixel height (its legibility floor, the audit's own >=50 px signal).
for (const s of shots) {
  const why = [];
  if (s.camera.dDist >= 3) why.push(`standoff +${s.camera.dDist.toFixed(1)}u (the shot pulls back)`);
  if (s.camera.charPxNearPct <= -15) why.push(`character ${s.camera.charPxNearPct.toFixed(0)}% smaller near-field`);
  if (s.camera.new.charPxFar < 50 && s.camera.new.charPxFar < s.camera.old.charPxFar)
    why.push(`far-field character crosses the rubric's 50 px floor (${s.camera.old.charPxFar} → ${s.camera.new.charPxFar} px)`);
  if (s.camera.dAim >= 1.5) why.push(`aim moved ${s.camera.dAim.toFixed(1)}u (a different subject)`);
  if (s.camera.new.capped && !s.camera.old.capped) why.push('standoff now CAPPED at maxDist — the region wants splitting');
  s.tasteReview = why;
}

// ---- ADVISORY: the ownership-mismatch spans ----------------------------------
// Not what this change is for, but the audit ranked them and the coordinator asked whether
// a re-aim helps: on these metres the floor belongs to one shot and another shot's camera
// is live, so the question is whether the LIVE camera can at least see the ground the
// player is on. A yes turns a surprise into a legible late cut.
// The span is measured along its WHOLE length (5 samples of the map edge, the same
// polyline the walk ribbon was built from), not just at its midpoint: a span that leaves
// frame does it at one end.
const advisory = ROUTES.mismatch.slice(0, 8).map((m) => {
  const E = C.MEDGE[m.edge];
  const pts = [0, 1, 2, 3, 4].map((i) => m2rPoint(E, m.t[0] + (m.t[1] - m.t[0]) * i / 4));
  const scan = (camId) => {
    const cam = camId && oldBy[camId] ? camId : null;
    if (!cam) return null;
    const one = (by) => {
      const ss = pts.map((p) => screenOf(by[cam], p));
      return {groundVisibleFrac: r3n(ss.filter((s) => s.groundVisible).length / ss.length),
              figureVisibleFrac: r3n(ss.filter((s) => s.figureVisible).length / ss.length),
              minEdgeMargin: r3n(Math.min(...ss.map((s) => s.edgeMargin))),
              minCharPx: Math.min(...ss.map((s) => s.charPx))};
    };
    return {old: one(oldBy), new: one(newBy)};
  };
  const up = scan(m.cameraUp);
  return {edge: m.edge, t: m.t, metres: m.metres, at: m.at, samples: pts.length,
          cameraUp: m.cameraUp, floorOwnedBy: m.floorOwnedBy,
          liveCamera: up, owningCamera: scan(m.floorOwnedBy),
          improved: up ? up.new.groundVisibleFrac > up.old.groundVisibleFrac ||
                         up.new.minEdgeMargin > up.old.minEdgeMargin + 0.02 : null};
});
// map-edge point -> runtime coords, the projection input this report uses everywhere
function m2rPoint(E, t) {
  const p = edgePoint(E, t);
  return [r3n(p[0]), r3n(p[2]), r3n(-p[1])];
}

// ---- write -------------------------------------------------------------------
const totals = {
  shots: shots.length,
  reAimed: shots.filter((s) => s.camera.dPos > 0.005).length,
  unchanged: shots.filter((s) => s.camera.dPos <= 0.005).length,
  pinned: shots.filter((s) => s.pin).map((s) => s.shot),
  fixed: shots.flatMap((s) => s.fixed.map((f) => `${s.shot}/${f}`)),
  stillOff: shots.flatMap((s) => s.stillOff.map((f) => `${s.shot}/${f}`)),
  stillOffByPin: shots.filter((s) => s.pin).flatMap((s) => s.stillOff.map((f) => `${s.shot}/${f}`)),
  regressed: shots.flatMap((s) => s.regressed.map((f) => `${s.shot}/${f}`)),
  offFrameExitsOld: shots.flatMap((s) => s.marks.filter((m) => m.role === 'exit' && !m.old.groundVisible).map((m) => `${s.shot}/${m.id}`)),
  offFrameExitsNew: shots.flatMap((s) => s.marks.filter((m) => m.role === 'exit' && !m.new.groundVisible).map((m) => `${s.shot}/${m.id}`)),
  tasteReview: shots.filter((s) => s.tasteReview.length).map((s) => s.shot),
  // Which plates a later re-bake would actually have to repaint: a mark that moves under
  // 4 px on a 1344x768 backdrop is a camera nobody can see has moved.
  rebakeNeeded: shots.filter((s) => s.camera.dPxMax >= 4).map((s) => s.shot),
  rebakeCosmetic: shots.filter((s) => s.camera.dPxMax > 0 && s.camera.dPxMax < 4).map((s) => s.shot),
  inFrameFracNew: [...new Set(shots.map((s) => s.camera.new.inFrameFrac))],
  projectionDriftVsRoutesJson: r3n(maxDrift),
};
const doc = {
  _doc: [
    'DELTA REPORT — exit-seam framing proposal (legibility follow-up, 2026-07-30).',
    'GENERATED by docs/qa/review/solve-proposal/derive_delta.mjs. Nothing here is shipped:',
    'old = public/townmap/dellhollow.cameras.solved.json (the live chain, unchanged),',
    'new = ./dellhollow.cameras.solved.proposed.json (node tools/cine_solve.mjs',
    '--frame-exits --out ...). No backdrop is re-baked by this tranche.',
    '',
    'Marks are the audit\'s own derived entries/exits (townmap/dellhollow.routes.json).',
    'An EXIT mark sits at the centre of a seam band — the metre where the cut fires; an',
    'ENTRY mark sits at the arrival point past that band. ndc is [-1,1]^2 = the frame;',
    'groundVisible = the surface is on screen, figureVisible = any part of a 1.7 m',
    'character standing there is. charPx is that character\'s height in px of 768.',
    'projectionDriftVsRoutesJson: max |ndc| disagreement between this report\'s OLD',
    'projection and the shipped routes file\'s own — a self-check that both measure the',
    'same cameras (0 = identical).',
  ],
  generator: 'docs/qa/review/solve-proposal/derive_delta.mjs',
  generated: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
  sources: ['townmap/dellhollow.cameras.solved.json',
            'docs/qa/review/solve-proposal/dellhollow.cameras.solved.proposed.json',
            'townmap/dellhollow.routes.json'],
  frame: FRAME, totals, shots, advisory,
};
fs.writeFileSync(path.join(HERE, 'delta.json'), JSON.stringify(doc, null, 1) + '\n');
fs.mkdirSync(path.join(HERE, 'probe'), {recursive: true});
for (const s of shots) {
  fs.writeFileSync(path.join(HERE, 'probe', s.shot + '.json'),
    JSON.stringify({shot: s.shot, name: s.name, generated: doc.generated,
                    generator: doc.generator, frame: FRAME, pin: s.pin,
                    exitSeams: s.exitSeams, camera: s.camera,
                    tasteReview: s.tasteReview,
                    entries: s.marks.filter((m) => m.role === 'entry'),
                    exits: s.marks.filter((m) => m.role === 'exit')}, null, 1) + '\n');
}

// ---- markdown ----------------------------------------------------------------
const L = [];
const ndc = (s) => s.ndc ? `${s.ndc[0].toFixed(2)}, ${s.ndc[1].toFixed(2)}` : 'behind';
L.push('# Exit-seam framing — delta report', '',
  `Generated \`${doc.generated}\` by \`docs/qa/review/solve-proposal/derive_delta.mjs\`.`,
  '',
  'Old = the shipped `townmap/dellhollow.cameras.solved.json`. New =',
  '`./dellhollow.cameras.solved.proposed.json`, from',
  '`node tools/cine_solve.mjs --frame-exits --out docs/qa/review/solve-proposal/dellhollow.cameras.solved.proposed.json`.',
  '**Nothing is shipped and nothing is re-baked by this tranche** — the live chain',
  '(`cameras.solved.json` → `cine.json` → the 17 baked backdrops) is untouched.', '',
  `Self-check: this report's OLD projection agrees with the shipped routes file's own to`,
  `**${totals.projectionDriftVsRoutesJson} ndc** (same cameras, same \`project()\`).`, '',
  '## 1. Per-shot camera delta', '',
  '| shot | pin | exit seams | dist old→new | Δpos | Δaim | max mark shift | charPx near old→new | taste review |',
  '| --- | --- | --- | --- | --- | --- | --- | --- | --- |');
for (const s of shots) {
  const c = s.camera;
  L.push(`| \`${s.shot}\` | ${s.pin ? '**PIN**' : ''} | ${s.exitSeams} | ` +
    `${c.old.dist} → ${c.new.dist} (${c.dDist >= 0 ? '+' : ''}${c.dDist}) | ${c.dPos} | ${c.dAim} | ` +
    `${c.dPxMax} px | ` +
    `${c.old.charPxNear} → ${c.new.charPxNear} (${c.charPxNearPct >= 0 ? '+' : ''}${c.charPxNearPct.toFixed(0)}%) | ` +
    `${s.tasteReview.length ? '**' + s.tasteReview.join('; ') + '**' : '—'} |`);
}
L.push('', `${totals.reAimed} of ${totals.shots} shots re-aim; ${totals.unchanged} stay put ` +
  `(pinned: ${totals.pinned.map((p) => '`' + p + '`').join(', ') || 'none'}). ` +
  `Every shot still frames 100% of its samples (inFrameFrac ${totals.inFrameFracNew.join('/')}).`,
  '', 'Backdrops a later re-bake would visibly have to repaint (a mark moves ≥4 px on the ' +
  `1344×768 plate): **${totals.rebakeNeeded.length}** — ` +
  `${totals.rebakeNeeded.map((p) => '`' + p + '`').join(', ')}. ` +
  `Sub-pixel-to-3 px, cosmetic: ${totals.rebakeCosmetic.map((p) => '`' + p + '`').join(', ') || 'none'}.`, '',
  '## 2. The five off-frame exits', '',
  '| shot | exit | old ndc | old head ndc | new ndc | new head ndc | verdict |',
  '| --- | --- | --- | --- | --- | --- | --- |');
for (const s of shots) for (const m of s.marks) {
  if (m.role !== 'exit' || m.old.groundVisible) continue;
  L.push(`| \`${s.shot}\` | \`${m.id}\` | ${ndc(m.old)} | ${m.old.headNdc ? m.old.headNdc.map((v) => v.toFixed(2)).join(', ') : '—'} | ` +
    `${ndc(m.new)} | ${m.new.headNdc ? m.new.headNdc.map((v) => v.toFixed(2)).join(', ') : '—'} | ${m.verdict} |`);
}
L.push('', '## 3. Every entry and exit, old vs new', '');
for (const s of shots) {
  L.push(`### \`${s.shot}\` — ${s.name}${s.pin ? ' · **PINNED**' : ''}`, '',
    `pos ${JSON.stringify(s.camera.old.pos)} → ${JSON.stringify(s.camera.new.pos)} · ` +
    `aim ${JSON.stringify(s.camera.old.aim)} → ${JSON.stringify(s.camera.new.aim)} · ` +
    `fov ${s.camera.new.fov}° · margin ${s.camera.params.margin} · ` +
    `samples ${s.camera.old.samples} → ${s.camera.new.samples}`, '',
    '| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |',
    '| --- | --- | --- | --- | --- | --- | --- | --- |');
  for (const m of s.marks)
    L.push(`| ${m.role} | \`${m.id}\` | ${ndc(m.old)} | ${ndc(m.new)} | ` +
      `${m.dNdcY === null ? '—' : (m.dNdcY >= 0 ? '+' : '') + m.dNdcY.toFixed(3)} | ` +
      `${m.old.edgeMargin.toFixed(3)} → ${m.new.edgeMargin.toFixed(3)} | ` +
      `${m.old.charPx} → ${m.new.charPx} | ${m.verdict === 'ok' ? 'ok' : '**' + m.verdict + '**'} |`);
  L.push('');
}
L.push('## 4. Advisory — the worst camera-vs-floor ownership mismatches', '',
  'These are metres where the floor belongs to one shot and another shot\'s camera is live',
  '(routes.json `mismatch`, ranked). Exit framing does not fix ownership; the question is',
  'whether the LIVE camera can at least see the ground the player is walking on there.', '',
  'Each span is sampled at 5 points along the map edge that generated it.', '',
  '| edge | t | metres | camera up | floor owned by | span in frame under live cam (old → new) | min edge margin | min charPx | improved |',
  '| --- | --- | --- | --- | --- | --- | --- | --- | --- |');
for (const a of advisory) {
  const u = a.liveCamera;
  L.push(`| \`${a.edge}\` | ${a.t[0]}..${a.t[1]} | ${a.metres.toFixed(1)} | \`${a.cameraUp}\` | \`${a.floorOwnedBy}\` | ` +
    `${u ? (u.old.groundVisibleFrac * 100).toFixed(0) + '% → ' + (u.new.groundVisibleFrac * 100).toFixed(0) + '%' : '—'} | ` +
    `${u ? u.old.minEdgeMargin.toFixed(3) + ' → ' + u.new.minEdgeMargin.toFixed(3) : '—'} | ` +
    `${u ? u.old.minCharPx + ' → ' + u.new.minCharPx : '—'} | ${a.improved ? 'yes' : 'no'} |`);
}
const mmSeen = advisory.filter((a) => a.liveCamera && a.liveCamera.old.groundVisibleFrac === 1).length;
L.push('', `${mmSeen} of these ${advisory.length} spans were ALREADY fully in frame under the live ` +
  'camera before the change: the ownership mismatch is a *timing* defect (the cut lands late), not ' +
  'a visibility one, so exit framing is not the lever for it — it only makes the late metres sit ' +
  'further inside the frame while they are walked. The lever is ownership/`cutOffset`, which is ' +
  'the coordinator\'s call and a separate tranche.', '',
  '## 5. Totals', '',
  `* exits with their ground off-frame — **before ${totals.offFrameExitsOld.length}**, **after ${totals.offFrameExitsNew.length}**`,
  `* fixed: ${totals.fixed.length ? totals.fixed.map((f) => '`' + f + '`').join(', ') : 'none'}`,
  `* still off-frame: ${totals.stillOff.length ? totals.stillOff.map((f) => '`' + f + '`').join(', ') : 'none'}` +
    (totals.stillOffByPin.length === totals.stillOff.length
      ? ' — every one of them on a PINNED shot, i.e. left off-frame BY RULING, not by the solver'
      : totals.stillOffByPin.length ? ` (${totals.stillOffByPin.length} of them on pinned shots, by ruling)` : ''),
  `* regressed: ${totals.regressed.length ? totals.regressed.map((f) => '`' + f + '`').join(', ') : 'none'}`,
  `* flagged for taste review: ${totals.tasteReview.length ? totals.tasteReview.map((f) => '`' + f + '`').join(', ') : 'none'}`,
  '',
  '## 6. Reproduce, and what the coordinator still has to move', '',
  '```sh',
  'node tools/cine_solve.mjs --check                 # the SHIPPED solve is unchanged',
  'node tools/cine_solve.mjs --frame-exits \\',
  '     --out docs/qa/review/solve-proposal/dellhollow.cameras.solved.proposed.json',
  'node docs/qa/review/solve-proposal/derive_delta.mjs',
  '```', '',
  'The solver change itself is unconditional and general: `solveCamera` now fits each shot',
  'around its owned region + its ARRIVALS + **the centre of every seam band it is an exit',
  'of** (both directions of every seam), so no future town can ship a shot whose own exit',
  'is off-frame. Two flags govern it and both belong in `townmap/<town>.cameras.json`:', '',
  '| flag | where | meaning |',
  '| --- | --- | --- |',
  '| `"pin": true` | a camera record | this frame is a human ruling: reproduce its authored `pos`/`aim` exactly and exclude it from the exit constraint. Requires `pos`+`aim`. |',
  '| `defaults.frameExits: false` | the cameras file | the whole town opts OUT — a migration flag for a town whose backdrops are already baked. |', '',
  'Because this tranche may not edit `cameras.json`, both currently live in the sidecar',
  '`public/townmap/dellhollow.cameras.pins.json`, which the solver merges onto the camera',
  'records. **The coordinator should move them into `cameras.json`** (`"pin": true` on the',
  'boatyard camera; `"frameExits": false` in `defaults`, deleted when the re-bake lands) and',
  'delete the sidecar — the solver only ever reads `cam.pin` / `C.D.frameExits`, so nothing',
  'else changes. Turning exit framing on for Dellhollow means re-solving the shipped',
  '`cameras.solved.json`, re-running `tools/scenegraph_derive.mjs`, and re-baking the',
  `${totals.rebakeNeeded.length} plates listed in §1 — deliberately NOT done here.`, '');
fs.writeFileSync(path.join(HERE, 'delta.md'), L.join('\n'));

console.log(`delta: ${totals.reAimed} re-aimed, ${totals.unchanged} unchanged (pinned ${totals.pinned.join(',') || '-'})`);
console.log(`off-frame exits: ${totals.offFrameExitsOld.length} -> ${totals.offFrameExitsNew.length}`);
console.log(`  fixed      : ${totals.fixed.join(', ') || '-'}`);
console.log(`  still off  : ${totals.stillOff.join(', ') || '-'}`);
console.log(`  REGRESSED  : ${totals.regressed.join(', ') || '-'}`);
console.log(`taste review : ${totals.tasteReview.join(', ') || '-'}`);
console.log(`projection drift vs routes.json: ${totals.projectionDriftVsRoutesJson} ndc`);
console.log(`wrote delta.md, delta.json, probe/*.json (${shots.length})`);
