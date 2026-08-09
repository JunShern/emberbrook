// ===================== TEAMMATE OVERLAP, AS A MEASUREMENT ==================
// WHY THIS EXISTS AND WHY NO EXISTING RULER COULD ANSWER IT.
// tools/battle_meter.mjs's `legibility` isolates each body by hiding EVERY body
// and showing one — so the background it scores a silhouette against is
// CAST-FREE BY CONSTRUCTION and a teammate standing in front of another body is
// invisible to it. The ruler audit (docs/qa/battle-party/ruler-audit) found that
// 8 of its 57 eye-sorted bodies were compromised by exactly that, and that
// EXCLUDING them is what takes the 6-band ruler from chance to AUC 0.820. So the
// largest single cause of a party body not reading was a shot problem that every
// tonal instrument in the arc was blind to.
//
// WHAT IT MEASURES. Three renders per question, and the arithmetic is the one
// this repo has already paid for twice (docs/qa/battle-party: occlusion is an
// INTERSECTION of two silhouettes, never a ratio of areas — GTAO and bloom leave
// a halo the two passes do not share, which is how a fully visible body once
// measured "-136% occluded"):
//   SOLO_i  = diff( only body i visible , no cast at all )
//             the silhouette body i has against the WORLD — what the meter sees.
//   VIS_i   = diff( the whole cast visible , the cast minus body i )
//             the pixels body i is the FRONTMOST thing at, in the real frame.
//   occTeam = 1 - |SOLO_i AND VIS_i| / |SOLO_i|
// Bodies are opaque, so a pixel of SOLO_i that does not move when body i is
// removed from the full frame is a pixel some OTHER body is standing in front
// of. The lost pixels are then attributed by asking which other body's own SOLO
// mask covers them, so "who eclipses whom" is measured and not inferred.
//
// SAY WHICH SPACE THE BYTES ARE IN: every grab here is `drawImage` off the
// WebGL canvas AFTER play3d's own post chain (RenderPass -> GTAO -> bloom ->
// OutputPass), i.e. DISPLAY-SPACE sRGB. Nothing offscreen is read, so the r185
// linear-target trap is not on this path and no encode is applied.
//
// THE FRAME IS PINNED BEFORE IT IS PHOTOGRAPHED, for the same reason the tone
// probe pins it: the measurement subtracts two renders and anything that moves
// between them is counted as silhouette. `stage.qa.pose(true)` holds the cast at
// its hashed idle phase and `Ambient.hide(true)` sits the motes out; both are
// restored. Geometry (boxes, poses, the formation angle) is reproducible to four
// figures — which is exactly why this lane reports occlusion counts and not
// tonal deltas.
export const LIB = `(() => {
  const W = {};
  window.__OVL = W;

  // --- one canvas-sized scratch buffer, reused ------------------------------
  let c2 = null, g2 = null;
  function grab(cv) {
    if (!c2) { c2 = document.createElement('canvas'); g2 = c2.getContext('2d', { willReadFrequently: true }); }
    if (c2.width !== cv.width || c2.height !== cv.height) { c2.width = cv.width; c2.height = cv.height; }
    g2.drawImage(cv, 0, 0);
    return g2.getImageData(0, 0, cv.width, cv.height).data;
  }

  // The body's own projected Box3, in DEVICE pixels, padded and clipped. Every
  // mask below is filled only inside it: a body cannot be occluded outside the
  // box it projects into, and the box is what keeps 10 full-canvas diffs cheap.
  function regionOf(box, dpr, W2, H2) {
    if (!box) return null;
    const M = 8;
    const x0 = Math.max(0, Math.floor((box.x0 - M) * dpr)), y0 = Math.max(0, Math.floor((box.y0 - M) * dpr));
    const x1 = Math.min(W2, Math.ceil((box.x1 + M) * dpr)), y1 = Math.min(H2, Math.ceil((box.y1 + M) * dpr));
    if (x1 <= x0 + 2 || y1 <= y0 + 2) return null;
    return { x0: x0, y0: y0, x1: x1, y1: y1 };
  }
  function maskDiff(a, b, r, W2) {
    const rw = r.x1 - r.x0;
    const m = new Uint8Array(rw * (r.y1 - r.y0));
    let n = 0;
    for (let y = r.y0; y < r.y1; y++) {
      for (let x = r.x0; x < r.x1; x++) {
        const i = (y * W2 + x) * 4;
        const d = Math.max(Math.abs(a[i] - b[i]), Math.abs(a[i + 1] - b[i + 1]), Math.abs(a[i + 2] - b[i + 2]));
        if (d > 12) { m[(y - r.y0) * rw + (x - r.x0)] = 1; n++; }
      }
    }
    return { m: m, n: n, r: r, rw: rw };
  }
  const inMask = (M, x, y) => {
    if (!M) return 0;
    if (x < M.r.x0 || y < M.r.y0 || x >= M.r.x1 || y >= M.r.y1) return 0;
    return M.m[(y - M.r.y0) * M.rw + (x - M.r.x0)];
  };

  // =========================================================================
  W.measure = function () {
    const sc = window.__EBB_SCREEN, st = sc && sc.stage;
    if (!st || !st.qa) return { ok: false, why: 'no stage' };
    const cv = st.canvas, W2 = cv.width, H2 = cv.height;
    const dpr = W2 / cv.getBoundingClientRect().width;

    // PIN EVERYTHING THAT MOVES BETWEEN TWO RENDERS.
    const posed = st.qa.pose ? st.qa.pose(true) : 0;
    let ambWas = false;
    try { if (window.Ambient && Ambient.hide) { Ambient.hide(true); ambWas = true; } } catch (e) {}

    const ids = st.qa.ids();
    const boxes = {}, regions = {};
    for (const id of ids) boxes[id] = st.qa.box(id);
    const live = ids.filter(id => boxes[id] && !boxes[id].dead);
    for (const id of live) regions[id] = regionOf(boxes[id], dpr, W2, H2);

    // ---- pass A: the frame as the player sees it ---------------------------
    st.qa.showAll(true); st.draw();
    const imgAll = grab(cv);
    // ---- pass B: the same frame with ONE body removed, per body ------------
    const VIS = {};
    for (const id of live) {
      const r = regions[id]; if (!r) continue;
      st.qa.show(id, false); st.draw();
      const minus = grab(cv);
      st.qa.show(id, true);
      VIS[id] = maskDiff(imgAll, minus, r, W2);
    }
    // ---- pass C: no cast at all -------------------------------------------
    st.qa.showAll(false); st.draw();
    const bg = grab(cv);
    // ---- pass D: one body at a time, against that ------------------------
    const SOLO = {};
    for (const id of live) {
      const r = regions[id]; if (!r) continue;
      st.qa.show(id, true); st.draw();
      const solo = grab(cv);
      st.qa.show(id, false);
      SOLO[id] = maskDiff(solo, bg, r, W2);
    }
    // ---- pass E: the same body with DEPTH TESTING OFF ----------------------
    // A FIX THAT MOVES A BODY OUT FROM BEHIND A TEAMMATE AND PUTS IT BEHIND A
    // LAMP POST HAS NOT FIXED ANYTHING, and an occlusion count that only knows
    // about teammates would report that trade as a clean win. Measured at s002
    // on the first arm of this lane's own A/B, which is why this pass exists.
    // FREE_i is the silhouette body i would have with nothing in front of it at
    // all; occWorld is what the WORLD takes, occTotal what the player is left
    // with. Note that placement's own visibility test is run from the ROUND
    // eye, and 'decide' swings 0.3 rad off it — so these two are not the same
    // question and this is the one the player is looking at.
    st.qa.xray(true);
    const FREE = {};
    for (const id of live) {
      const r = regions[id]; if (!r) continue;
      st.qa.show(id, true); st.draw();
      const free = grab(cv);
      st.qa.show(id, false);
      FREE[id] = maskDiff(free, bg, r, W2);
    }
    st.qa.xray(false);
    st.qa.showAll(true); st.draw();

    // ---- the numbers -------------------------------------------------------
    const rows = [];
    for (const id of live) {
      const S = SOLO[id], V = VIS[id];
      if (!S || !V) { rows.push({ id: id, side: boxes[id].side, why: 'no region' }); continue; }
      if (!S.n) { rows.push({ id: id, side: boxes[id].side, soloPx: 0, why: 'no silhouette' }); continue; }
      let inter = 0, lost = 0;
      const by = {};
      for (const o of live) if (o !== id) by[o] = 0;
      let byNone = 0;
      for (let y = S.r.y0; y < S.r.y1; y++) for (let x = S.r.x0; x < S.r.x1; x++) {
        if (!S.m[(y - S.r.y0) * S.rw + (x - S.r.x0)]) continue;
        if (inMask(V, x, y)) { inter++; continue; }
        lost++;
        // WHO TOOK IT. The lost pixel belongs to whichever other body's own
        // solo silhouette covers it; a pixel no other body claims is halo slop
        // (GTAO/bloom around a neighbour) and is counted separately rather
        // than silently attributed.
        let hit = null;
        for (const o of live) if (o !== id && inMask(SOLO[o], x, y)) { hit = o; break; }
        if (hit) by[hit]++; else byNone++;
      }
      const b = boxes[id];
      // occlusion is an INTERSECTION of two silhouettes, never a ratio of areas
      const F = FREE[id];
      let fS = 0, fV = 0;
      if (F && F.n) {
        for (let y = F.r.y0; y < F.r.y1; y++) for (let x = F.r.x0; x < F.r.x1; x++) {
          if (!F.m[(y - F.r.y0) * F.rw + (x - F.r.x0)]) continue;
          if (inMask(S, x, y)) fS++;
          if (inMask(V, x, y)) fV++;
        }
      }
      rows.push({
        id: id, side: b.side, tier: b.tier,
        soloPx: S.n, visPx: V.n, interPx: inter, lostPx: lost, freePx: F ? F.n : null,
        // THE NUMBER: how much of what the world left of this body a TEAMMATE ate.
        occTeam: +(1 - inter / S.n).toFixed(4),
        // and the two that keep it honest: what the WORLD takes, and what the
        // player is left with once both have taken their share.
        occWorld: F && F.n ? +(1 - fS / F.n).toFixed(4) : null,
        occTotal: F && F.n ? +(1 - fV / F.n).toFixed(4) : null,
        occUnclaimed: +(byNone / S.n).toFixed(4),
        by: by,
        box: { x0: +b.x0.toFixed(1), y0: +b.y0.toFixed(1), x1: +b.x1.toFixed(1), y1: +b.y1.toFixed(1) },
        // AND THE OTHER WAY A BODY STOPS READING. A teammate can stop eclipsing
        // one by standing beside it and start LOSING it off the frame edge
        // instead, which is the same defect with a different cause and would be
        // invisible to an occlusion count alone. Same arithmetic battle_decide's
        // own 'foesIn' uses: the projected box clipped against the canvas.
        // (Plain quotes on purpose -- this comment lives inside a template
        // literal and a backtick in one ends the literal. Paid three times now.)
        inFrame: +(Math.max(0, Math.min(b.x1, b.w) - Math.max(b.x0, 0)) *
                   Math.max(0, Math.min(b.y1, b.h) - Math.max(b.y0, 0)) /
                   Math.max(1e-6, (b.x1 - b.x0) * (b.y1 - b.y0))).toFixed(4),
        cx: +(((b.x0 + b.x1) / 2) / b.w).toFixed(4),
        wFrac: +((b.x1 - b.x0) / b.w).toFixed(4),
        hFrac: +((b.y1 - b.y0) / b.h).toFixed(4),
      });
    }

    // ---- WHY: the formation line against the camera's own azimuth ----------
    // Everything here is derived from the stage's OWN plan and pose, never
    // retyped from the shot table.
    const camr = st.cam ? st.cam() : null;
    const plan = st.plan || {};
    const placed = {};
    for (const p of (plan.placed || [])) placed[p.id] = { x: +p.x.toFixed(3), y: +p.y.toFixed(3), z: +p.z.toFixed(3), slot: p.slot };
    let geo = null;
    if (camr && camr.pose && camr.base) {
      const th = camr.pose.yaw - camr.base.yaw;           // the decide swing, in radians
      const by = camr.base.yaw;
      // arena basis: u = screen-right at baseYaw, v = into the screen at baseYaw
      const rx = Math.sin(by), rz = -Math.cos(by), fx = -Math.cos(by), fz = -Math.sin(by);
      const uv = (p) => ({ u: p.x * rx + p.z * rz, v: p.x * fx + p.z * fz });
      const pl = live.filter(id => boxes[id].side !== 'foe' && placed[id]);
      if (pl.length >= 2) {
        const a = uv(placed[pl[0]]), b2 = uv(placed[pl[1]]);
        const du = b2.u - a.u, dv = b2.v - a.v;
        // the camera's own right and forward at the SWUNG yaw, in that basis
        const cr = { u: Math.cos(th), v: -Math.sin(th) };
        const cf = { u: Math.sin(th), v: Math.cos(th) };
        const sep = du * cr.u + dv * cr.v;                 // lateral separation, metres
        const dep = du * cf.u + dv * cf.v;                 // depth separation, metres
        const L = Math.hypot(du, dv);
        // the angle between the party line and the camera's view axis. 0 deg =
        // the line points straight into the lens and the two bodies eclipse.
        const cosA = L ? Math.abs((du * cf.u + dv * cf.v) / L) : 0;
        geo = { pair: [pl[0], pl[1]], swingRad: +th.toFixed(4),
                lineLen: +L.toFixed(3), lateralM: +sep.toFixed(3), depthM: +dep.toFixed(3),
                lineVsAxisDeg: +(Math.acos(Math.min(1, cosA)) * 180 / Math.PI).toFixed(2),
                nearer: dep > 0 ? pl[0] : pl[1], farther: dep > 0 ? pl[1] : pl[0] };
      }
    }
    // screen separation of the two party boxes, in frame widths, and how much
    // their boxes overlap in x as a fraction of the narrower one
    let pair = null;
    const pb = rows.filter(r => r.side !== 'foe' && r.box);
    if (pb.length >= 2) {
      const A = pb[0], B = pb[1];
      const wA = A.box.x1 - A.box.x0, wB = B.box.x1 - B.box.x0;
      const ov = Math.max(0, Math.min(A.box.x1, B.box.x1) - Math.max(A.box.x0, B.box.x0));
      pair = { a: A.id, b: B.id, dCx: +Math.abs(A.cx - B.cx).toFixed(4),
               xOverlapFrac: +(ov / Math.max(1e-6, Math.min(wA, wB))).toFixed(4) };
    }

    // restore
    try { if (ambWas) Ambient.hide(false); } catch (e) {}
    if (st.qa.pose) st.qa.pose(false);
    st.draw();
    return { ok: true, canvas: [W2, H2], dpr: +dpr.toFixed(3), posed: posed,
             rows: rows, geo: geo, pair: pair, placed: placed,
             pose: camr ? camr.pose : null, base: camr ? camr.base : null,
             kind: camr ? camr.kind : null, actor: camr ? camr.actor : null,
             axis: camr ? camr.axis : null };
  };
  return true;
})()`;
