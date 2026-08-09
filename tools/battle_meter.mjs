#!/usr/bin/env node
// battle_meter.mjs — THE SHARED BATTLE METER. One prelude, one legibility meter,
// one site list, imported by every battle instrument so two tools can never
// disagree about what they measured.
//
// EXTRACTED VERBATIM from tools/battle_camera.mjs (2026-08-09, the tonal-
// separation lane) when a second instrument needed the same numbers. A meter
// that is copy-pasted is two meters that drift; the repo has paid for that shape
// before (walk_bodygate reading the file while the engine read something else).
// Nothing below was retuned in the move — the extraction's own proof is that
// battle_camera's `--mode=legibility` reproduces its previous run through it.
//
// It exports STRINGS, not behaviour: READY and PRELUDE are injected into the
// page by the caller's own CDP plumbing, so this module imports nothing and can
// never spawn a Chrome of its own.

// SAY WHICH PATH ANSWERED, AND PROVE IT PARTITIONS. A side map that silently
// came from an id pattern is the defect this convention exists to make visible,
// so every run prints the path — and asserts the map covers every body on the
// stage exactly once, with no id on both sides and none missing.
export function sideReport(tag, r) {
  const ids = Object.keys(r.tiers || {});
  const sides = r.sides || {};
  const party = ids.filter(i => sides[i] === 'party'), foes = ids.filter(i => sides[i] === 'foe');
  const missing = ids.filter(i => sides[i] !== 'party' && sides[i] !== 'foe');
  const overlap = party.filter(i => foes.indexOf(i) >= 0);
  const extra = Object.keys(sides).filter(i => ids.indexOf(i) < 0);
  const ok = !missing.length && !overlap.length && !extra.length && ids.length > 0;
  console.log(`  sides[${tag}] via ${r.sidesVia || 'stage.sides()'} · party=[${party}] foes=[${foes}]`
            + ` · partition ${ok ? 'OK' : 'BROKEN'}`
            + (ok ? '' : ` missing=[${missing}] overlap=[${overlap}] extra=[${extra}]`));
  if (!ok) throw new Error('side map does not partition the body set: ' + JSON.stringify({ ids, sides }));
  return { party, foes, via: r.sidesVia || 'stage.sides()' };
}

export const READY = `(async () => {
  for (let i = 0; i < 400; i++) {
    if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE
        && window.ORBIT && window.SIM.pos && SIM.floors(SIM.pos().x, SIM.pos().z).length) {
      return { ready: true, three: THREE.REVISION, scene: SIM.bounds().scene,
               bw: window.BattleWorld ? { on: window.BattleWorld.on, installed: window.BattleWorld.installed } : null,
               fov: (typeof cam !== 'undefined' && cam) ? cam.fov : null };
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return { ready: false };
})()`;

// ---------------------------------------------------------------------------
// THE SHARED PRELUDE, injected once: start a battle at a spot, wait for models.
// ---------------------------------------------------------------------------
export const PRELUDE = `
window.__BC = window.__BC || {};
window.__BC.startAt = async function (x, z, group, opts) {
  opts = opts || {};
  const GS = window.GS, B = window.Battle, RU = window.Rules;
  GS.setFlags({ 'maren-joined': true });
  const f = SIM.floors(x, z);
  SIM.tp(x, z, f.length ? f[0] : null);
  SIM.tick(3);
  if (window.BattleWorld && !Object.isFrozen(window.BattleWorld)) {
    window.BattleWorld.CAM.on = opts.cam !== false;
    window.BattleWorld.enabled = opts.world !== false;   // false => the DIORAMA answers
  }
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zone = SIM.zone() || 'meadow';
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const p = B.start({ zone: zone, group: group, seed: 4242, backdrop: zd && zd.battleBackdrop },
                    party, { speed: opts.speed == null ? 1 : opts.speed });
  p.then(()=>{},()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 250 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { ok: false, why: 'no stage', plan: window.__BW_LAST_PLAN || null };
  const f0 = st.frames;
  for (let i = 0; i < 260; i++) {
    if (Object.values(st.tiers()).every(v => v !== 'proxy') && st.frames > f0 + 100) break;
    await new Promise(r => setTimeout(r, 100));
  }
  await new Promise(r => setTimeout(r, opts.settle == null ? 1500 : opts.settle));
  // AN ID IS NOT A SIDE. BOTH arenas now carry sides() — the per-body value
  // newBody() was constructed with (battle_world.js :1427, battle_stage3d.js
  // :3259) — so this asks the stage and REPORTS WHICH PATH ANSWERED. The id
  // pattern is a labelled last resort: /^m/ matches **maren**, and even
  // /^m\\d+$/ is a guess about battle_rules' private id scheme that was safe
  // in the diorama column only by accident of build order.
  let sidesVia = 'stage.sides()';
  let sides = st.sides ? st.sides() : null;
  if (!sides) {
    sidesVia = 'stage.at().side';
    sides = Object.keys(st.tiers()).reduce((o, k) => { const a = st.at && st.at(k); if (a && a.side) o[k] = a.side; return o; }, {});
    if (!Object.keys(sides).length) {
      sidesVia = 'id-pattern-fallback';
      sides = Object.keys(st.tiers()).reduce((o, k) => (o[k] = /^m\\d+$/.test(k) ? 'foe' : 'party', o), {});
    }
  }
  return { ok: true, zone: zone, world: !!st.world, tiers: st.tiers(), sides: sides, sidesVia: sidesVia,
           cam: st.cam ? st.cam() : null, plan: st.plan || null };
};
window.__BC.end = async function () {
  const s = window.__EBB_SCREEN;
  if (s && s.stage) { try { s.stage.destroy(); } catch (e) {} }
  if (s && s.destroy) { try { s.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
  await new Promise(r => setTimeout(r, 400));
  return true;
};
window.__BC.stage = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
window.__BC.shot = () => window.__BC.stage().snapshot();

// ============================ THE LEGIBILITY METER =========================
// A silhouette is a SUBTRACTION, not a heuristic: frame-with-body minus
// frame-without-body. Everything else follows from that one mask.
window.__BC.legibility = function () {
  const st = window.__BC.stage(); if (!st || !st.qa) return null;
  const cv = st.canvas, W = cv.width, H = cv.height;
  const c2 = window.__BC._c2 || (window.__BC._c2 = document.createElement('canvas'));
  c2.width = W; c2.height = H;
  const g = c2.getContext('2d', { willReadFrequently: true });
  const grab = (x, y, w, h) => { g.drawImage(cv, 0, 0); return g.getImageData(x, y, w, h); };
  const L = (d, i) => 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
  const ids = st.qa.ids();
  const boxes = {};
  for (const id of ids) boxes[id] = st.qa.box(id);
  // the region each body could occupy, in device pixels, with a margin for the ring
  const dpr = W / cv.getBoundingClientRect().width;
  const regionOf = (id) => {
    const b = boxes[id]; if (!b) return null;
    const M = 26;
    const x0 = Math.max(0, Math.floor((b.x0 - M) * dpr)), y0 = Math.max(0, Math.floor((b.y0 - M) * dpr));
    const x1 = Math.min(W, Math.ceil((b.x1 + M) * dpr)), y1 = Math.min(H, Math.ceil((b.y1 + M) * dpr));
    if (x1 <= x0 + 2 || y1 <= y0 + 2) return null;
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  };
  // ---- pass 1: the world with no cast in it (the background every body sits on)
  st.qa.showAll(false); st.draw();
  const bgFull = grab(0, 0, W, H);
  const bgOf = (r) => {
    const out = new Uint8ClampedArray(r.w * r.h * 4);
    for (let y = 0; y < r.h; y++) {
      const src = ((y + r.y) * W + r.x) * 4;
      out.set(bgFull.data.subarray(src, src + r.w * 4), y * r.w * 4);
    }
    return out;
  };
  const maskOf = (id, r) => {
    st.qa.show(id, true); st.draw();
    const im = grab(r.x, r.y, r.w, r.h).data;
    st.qa.show(id, false);
    const bg = bgOf(r);
    const m = new Uint8Array(r.w * r.h);
    let n = 0;
    for (let i = 0, p = 0; p < m.length; p++, i += 4) {
      const d = Math.max(Math.abs(im[i] - bg[i]), Math.abs(im[i + 1] - bg[i + 1]), Math.abs(im[i + 2] - bg[i + 2]));
      if (d > 12) { m[p] = 1; n++; }
    }
    return { m, n, im, bg };
  };
  const out = [];
  for (const id of ids) {
    const r = regionOf(id); if (!r) continue;
    const A = maskOf(id, r);
    if (!A.n) { out.push({ id: id, side: boxes[id].side, silPx: 0, why: 'no silhouette' }); continue; }
    // ---- the mask's own bbox, its edge band, and the background ring ---------
    let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let p = 0; p < A.m.length; p++) if (A.m[p]) {
      const px = p % r.w, py = (p / r.w) | 0;
      if (px < x0) x0 = px; if (px > x1) x1 = px;
      if (py < y0) y0 = py; if (py > y1) y1 = py;
    }
    // dilate by K to get the ring OUTSIDE the body, and erode to get the edge band INSIDE it
    const K = 4, RING = 10;
    const dil = new Uint8Array(A.m.length), ero = new Uint8Array(A.m.length);
    const at = (x, y) => (x < 0 || y < 0 || x >= r.w || y >= r.h) ? 0 : A.m[y * r.w + x];
    for (let y = 0; y < r.h; y++) for (let x = 0; x < r.w; x++) {
      const p = y * r.w + x;
      let any = 0, all = 1;
      for (let dy = -K; dy <= K && (!any || all); dy++) for (let dx = -K; dx <= K; dx++) {
        const v = at(x + dx, y + dy);
        if (v) any = 1; else all = 0;
      }
      dil[p] = any; ero[p] = all;
    }
    let sumB = 0, nB = 0, sumBg = 0, sumEdge = 0, nEdge = 0, sumRing = 0, nRing = 0, sumRing2 = 0;
    const eRGB = [0, 0, 0], rRGB = [0, 0, 0];
    for (let p = 0, i = 0; p < A.m.length; p++, i += 4) {
      const lb = L(A.im, i), lg = L(A.bg, i);
      if (A.m[p]) {
        sumB += lb; sumBg += lg; nB++;
        if (!ero[p]) { sumEdge += lb; nEdge++; eRGB[0] += A.im[i]; eRGB[1] += A.im[i + 1]; eRGB[2] += A.im[i + 2]; }
      }
      else if (dil[p]) {
        // the ring is read off the BACKGROUND frame, so a body's own rim light
        // never inflates the contrast it is being scored against
        const px = p % r.w, py = (p / r.w) | 0;
        let near = 0;
        for (let dy = -RING; dy <= RING && !near; dy += 2) for (let dx = -RING; dx <= RING; dx += 2) if (at(px + dx, py + dy)) { near = 1; break; }
        if (near) { sumRing += lg; sumRing2 += lg * lg; nRing++; rRGB[0] += A.bg[i]; rRGB[1] += A.bg[i + 1]; rRGB[2] += A.bg[i + 2]; }
      }
    }
    // ---- pass 2: the same body with depth testing off = its FREE silhouette --
    st.qa.xray(true);
    const B2 = maskOf(id, r);
    st.qa.xray(false);
    // OCCLUSION IS AN INTERSECTION, NOT A RATIO OF AREAS. Both masks carry a
    // halo the body did not draw — GTAO darkens the ground around a body that
    // writes depth, bloom bleeds outward from a bright one — and the two passes
    // do not carry the SAME halo, which is how a fully visible Maren measured
    // "-136% occluded". Asking how much of the FREE silhouette survived in the
    // real frame is immune to both.
    let inter = 0;
    for (let p = 0; p < A.m.length; p++) if (A.m[p] && B2.m[p]) inter++;
    const mB = nB ? sumB / nB : 0, mBgUnder = nB ? sumBg / nB : 0;
    const mEdge = nEdge ? sumEdge / nEdge : mB;
    const mRing = nRing ? sumRing / nRing : 0;
    const vRing = nRing ? Math.max(0, sumRing2 / nRing - mRing * mRing) : 0;
    // AND THE EDGE CONTRAST IS RGB DISTANCE, NOT LUMINANCE. This repo has paid
    // for the luminance-only version once already (cutin_edge's halo term: a rim
    // of the wrong HUE at the right brightness was invisible to it on 79 of 112
    // shipped plates). A teal eel on tan rock is 6 units apart in luminance and
    // 39 apart in RGB, and it reads.
    const dr = nEdge && nRing ? eRGB[0] / nEdge - rRGB[0] / nRing : 0;
    const dg = nEdge && nRing ? eRGB[1] / nEdge - rRGB[1] / nRing : 0;
    const db = nEdge && nRing ? eRGB[2] / nEdge - rRGB[2] / nRing : 0;
    out.push({
      id: id, side: boxes[id].side, tier: boxes[id].tier,
      silPx: A.n, freePx: B2.n, interPx: inter,
      occl: B2.n ? +(1 - inter / B2.n).toFixed(4) : null,
      edgeRGB: +Math.sqrt((dr * dr + dg * dg + db * db) / 3).toFixed(2),
      hPx: +((y1 - y0 + 1) / dpr).toFixed(1),
      hPct: +(((y1 - y0 + 1) / H) * 100).toFixed(2),
      // SILHOUETTE CONTRAST: how far the body's own edge band sits from the
      // background immediately around it. This is the number the spike's verdict
      // is about — a body that reads has a big one.
      edge: +Math.abs(mEdge - mRing).toFixed(2),
      // and the same thing measured over the WHOLE body against exactly what it
      // covers, which is blind to a busy background but immune to mask slop
      dL: +Math.abs(mB - mBgUnder).toFixed(2),
      // HOW BUSY THE BACKGROUND IS. A high-contrast body on a noisy field still
      // does not read; this is the noise.
      clutter: +Math.sqrt(vRing).toFixed(2),
      ringN: nRing, bodyL: +mB.toFixed(1), ringL: +mRing.toFixed(1),
    });
  }
  st.qa.showAll(true); st.draw();
  return { bodies: out, canvas: [W, H], cam: st.cam ? st.cam() : null };
};
true;
`;

// ---------------------------------------------------------------------------
export const SITES = [
  { name: 'meadow', at: [38.12, -26.88], group: ['duskpad', 'duskpad'] },
  { name: 'forest', at: [15.6, -16.9], group: ['bramble-shade', 'duskpad'] },
  { name: 'water', at: [-45.8, 26.7], group: ['weir-eel', 'brook-sprite'] },
  { name: 'crag', at: [65.6, -40.6], group: ['scree-shell', 'duskpad'] },
];
