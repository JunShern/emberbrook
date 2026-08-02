// reach_probe.mjs — CAN THE BODY GET FROM HERE TO THERE? (the engine answers)
//
// Used by tools/playthrough_test.mjs --walk. Exports one page-side function,
// window.__ebReach(A, B, opt), and the JS that installs it. No CDP and no Chrome of
// its own: the caller owns the browser and evaluates INSTALL once per page load.
//
// WHY IT EXISTS. playthrough_test moves the body with SIM.tp(), which sets x/z and
// ray-casts for a floor. It never asks whether a PATH leads there — so the spine can
// be green (every beat fires, in order) while the player is stuck two houses from the
// NPC the objective names. On 2026-08-02 the user hit exactly that: Chapter One's
// first objective was uncompletable on a commit playthrough_test passed 51/0.
//
// AND THE FILE CANNOT ANSWER IT. walk_bodygate reads the GLB and reported 0.00%
// blocked over a square where the running game had lost 209.6 m2 to a collision-BVH
// defect (tools/walk_engine_gate.mjs's header is the whole story). So this runs INSIDE
// the page and uses the runtime's own primitives — SIM.walkFloors, SIM.ground,
// SIM.blocked, SIM.edges — the same rays and the same body box the player is subject to.
//
// WHAT IT DOES. A 4-neighbour flood fill on a globally-snapped lattice, from A, until
// it stands within `tol` of B. Each step reproduces play3d's walkStep():
//
//   settle   WALKLOCK scenes (/^(del-|emb-|townwalk)/): walkGround — ONLY walk_ meshes
//            may catch the foot, within [fy-STEP_DN-.1, fy+STEP_UP+.1], highest first,
//            with walkGround's four 0.18 m plank-crack retries. Elsewhere (the
//            overworld): SIM.ground(), the same settle over every collider.
//   body     SIM.blocked(x,z,g) — the real body box (BODY_R .30, BODY_H 1.30) against
//            the real triangles, above the step-up grace.
//
// AND IT TAKES THE IN-SCENE EDGES, because in these towns they are locomotion, not
// scenery. Dellhollow's levels are 10 m apart vertically and are joined by `cut` bands
// and `passage` edges (del-cine has 42 self-edges); a fill that only walks reports the
// gate arrival and the log-jam as unreachable, 0.4 m apart in plan and 10 m apart in
// height. So when a filled cell lands in an edge's own trigger — sgHit's rectangle for
// a band, its radius for a passage — that edge's `spawn` is seeded as a new fill root.
// Only edges INTO THE SAME SCENE, and only ones SIM.edges() reports `open` (its
// conditional-flag gate: a sealed gate stays shut).
//
// WHAT IT PROVES AND WHAT IT DOES NOT.
//  * It is a TOPOLOGY screen, not a drive: a connected chain of standable, body-clear
//    cells exists. It does not prove walkStep's 0.075 m stride negotiates every one of
//    them — walk_bodygate is the instrument for the stride.
//  * CAMERA GATING IS IGNORED. An edge is offered only in its `camFrom` shot; the fill
//    takes any open edge regardless of which shot is up. Optimistic on purpose: the
//    alternative is a camera-state search, and the failure it would catch (an edge you
//    can only reach in a shot you can never be in) is seam_test's.
//  * LATTICE PHASE. STEP defaults to 0.4 m. It cannot tunnel a thin wall — a step must
//    be under 2*BODY_R = .6 m or the two body boxes stop overlapping — but a gap barely
//    wider than the body can fall between two cell centres and read as shut. A red is a
//    claim worth walking by hand; --walk-step 0.3 is the cheap re-ask.
//  * DESCENT. walkStep's body box floors at max(g+STEP_UP+.02, y+.02); SIM.blocked only
//    takes the first form, so a step DOWN of more than STEP_UP (.63 m) is tested with a
//    box up to that much lower than the walker's. Pessimistic only.
//  * DIAGONALS are not neighbours on purpose: walkStep resolves a blocked diagonal into
//    its two axis slides, so 4-neighbour IS the walker's move set.

export const STEP_UP = 0.63, STEP_DN = 0.8, BODY_R = 0.30;

// Installed once per page load (and again after every navigation).
export const INSTALL = `(()=>{
window.__ebReach = async function(A, B, opt){
  opt = opt || {};
  const STEP   = opt.step   || 0.4;
  const TOL    = opt.tol    || 1.5;      // close enough to B that its trigger radius has you
  const DYTOL  = opt.dyTol  || 1.5;      // and on the right storey
  const BUDGET = opt.budget || 250000;   // cells — a runaway fill must not hang the gate
  const MS     = opt.ms     || 90000;
  const EDGES_ON = opt.edges !== false;
  const SU = ${STEP_UP}, SD = ${STEP_DN};
  const t0 = Date.now();
  let probes = 0, yields = 0;

  const wl = (()=>{ const el = document.getElementById('wl');   // the live flag, mirrored
    if (el) return !!el.checked;
    return /^(del-|emb-|townwalk)/.test(String(SIM.scene())); })();

  const pickWalk = (x,z,lo,hi)=>{ const f = SIM.walkFloors(x,z); let b = null;
    for (let i=0;i<f.length;i++){ const y=f[i]; if (y>=lo && y<=hi && (b===null || y>b)) b=y; }
    return b; };
  const O4 = [[.18,0],[-.18,0],[0,.18],[0,-.18]];
  // OFF THE WALK NETWORK THE WALKER MAY STEP OFF A LEDGE AND FALL — walkStep's second
  // half, reached only when WALKLOCK is off. Without it the overworld reads as a maze
  // of 3 m cliffs the player in fact just walks down. DROP_MAX is play3d's 8 m.
  const DROP_MAX = 8;
  const settle = wl
    ? (x,z,fy)=>{ probes++; const lo=fy-SD-0.1, hi=fy+SU+0.1;
        let g = pickWalk(x,z,lo,hi); if (g!==null) return g;
        for (let k=0;k<4;k++){ g = pickWalk(x+O4[k][0], z+O4[k][1], lo, hi); if (g!==null) return g; }
        return null; }
    : (x,z,fy)=>{ probes++; const g = SIM.ground(x,z,fy);
        if (g!==null && g!==undefined) return g;
        let best = null;                                   // the fall: highest floor below
        const f = SIM.floors(x,z);
        for (let i=0;i<f.length;i++){ const y=f[i];
          if (y < fy-SD && y > fy-DROP_MAX && (best===null || y>best)) best=y; }
        return best; };

  const snap = (v)=>Math.round(v/STEP);
  const key  = (i,j)=>(i+100000)*200000 + (j+100000);
  const KI   = (k)=>Math.floor(k/200000)-100000, KJ = (k)=>(k%200000)-100000;
  const XX   = (i)=>i*STEP, ZZ = (j)=>j*STEP;

  // ---- the in-scene edges, and sgHit's own trigger test -----------------------
  const scene = SIM.scene();
  const edges = EDGES_ON ? (SIM.edges()||[]).filter(e=>e.to===scene && e.open && e.spawn && e.at) : [];
  // vTol is not on SIM.edges()'s report; sgDef's default is 2 and the per-edge values
  // in the shipped graph are 1.6-2. Two is the permissive read, and it is named here
  // rather than guessed at the call site.
  const VTOL = 2;
  const fires = (e,x,z,y)=>{
    const dy = Math.abs(y - e.at[1]); if (dy > VTOL) return false;
    const px = x - e.at[0], pz = z - e.at[2];
    if (e.band){
      const along = px*e.band.n[0] + pz*e.band.n[1], across = -px*e.band.n[1] + pz*e.band.n[0];
      return Math.abs(along) <= e.band.t && Math.abs(across) <= e.band.w;
    }
    return Math.hypot(px,pz) <= (e.r||1.5);
  };

  // ---- one fill ---------------------------------------------------------------
  async function fill(from, target, tol){
    const seen = new Map(), par = new Map();   // key -> y ; key -> {p, e}
    const qi = [], qj = [];
    let head = 0, budgetHit = false, timeHit = false, near = null;
    const usedEdge = new Set();
    let hitKey = null;

    const test = (k,x,z,y)=>{
      const d = Math.hypot(x-target[0], z-target[2]), dy = Math.abs(y-target[1]);
      if (!near || d < near.d) near = {d:+d.toFixed(2), dy:+dy.toFixed(2),
                                       x:+x.toFixed(2), y:+y.toFixed(2), z:+z.toFixed(2)};
      if (d <= tol && dy <= DYTOL){ hitKey = k; return true; }
      return false;
    };
    const push = (i,j,y,pk,eid)=>{ const k = key(i,j);
      seen.set(k,y); par.set(k,{p:pk===undefined?null:pk, e:eid||null}); qi.push(i); qj.push(j); return k; };

    // START. The anchor may be off the walk network — SIM.tp settles on ANY collider,
    // walkGround only on walk_ meshes — which is a finding, not a crash. Say so, then
    // start from the nearest standable cell within 2 m so the pair still gets an answer.
    let si = snap(from[0]), sj = snap(from[2]);
    let sy = settle(XX(si), ZZ(sj), from[1]);
    let startOffset = 0;
    if (sy === null){
      outer:
      for (let r=1; r<=Math.ceil(2/STEP); r++)
        for (let di=-r; di<=r; di++) for (let dj=-r; dj<=r; dj++){
          if (Math.max(Math.abs(di),Math.abs(dj)) !== r) continue;
          const y = settle(XX(si+di), ZZ(sj+dj), from[1]);
          if (y !== null && !SIM.blocked(XX(si+di), ZZ(sj+dj), y)){
            si+=di; sj+=dj; sy=y; startOffset = +Math.hypot(di*STEP, dj*STEP).toFixed(2); break outer; }
        }
    }
    if (sy === null) return {ok:false, reason:'start-unstandable', cells:0, near:null,
                             startOffset:null, seen, route:[]};

    const k0 = push(si, sj, sy);
    if (test(k0, XX(si), ZZ(sj), sy))
      return {ok:true, reason:'start-is-target', cells:1, near, startOffset, seen, route:[]};

    const D = [[1,0],[-1,0],[0,1],[0,-1]];
    while (head < qi.length){
      if (seen.size > BUDGET){ budgetHit = true; break; }
      if (Date.now()-t0 > MS){ timeHit = true; break; }
      // Yield rarely: the game's own rAF loop is software-rendering 2500 meshes in
      // this tab, and every yield hands it the main thread for a whole frame. Measured:
      // yielding per 1024 cells cost ~14 ms/cell wall, versus 0.1 ms of actual work.
      if ((head % 20000) === 0 && head){ yields++; await new Promise(r=>setTimeout(r,0)); }
      const i = qi[head], j = qj[head], k = key(i,j), y = seen.get(k); head++;

      // an edge whose trigger contains this cell is a move the player can make
      for (let m=0; m<edges.length; m++){
        const e = edges[m];
        if (usedEdge.has(e.id) || !fires(e, XX(i), ZZ(j), y)) continue;
        usedEdge.add(e.id);
        const s = e.spawn, ei = snap(s[0]), ej = snap(s[2]);
        if (seen.has(key(ei,ej))) continue;
        const sy2 = settle(XX(ei), ZZ(ej), s[1]);
        if (sy2 === null) continue;
        const kk = push(ei, ej, sy2, k, e.id);
        if (test(kk, XX(ei), ZZ(ej), sy2)) { head = qi.length; break; }
      }
      if (hitKey !== null) break;

      for (let d=0; d<4; d++){
        const ni = i+D[d][0], nj = j+D[d][1], kk = key(ni,nj);
        if (seen.has(kk)) continue;
        const nx = XX(ni), nz = ZZ(nj);
        const g = settle(nx, nz, y);
        if (g === null) continue;
        if (SIM.blocked(nx, nz, g)) continue;
        push(ni, nj, g, k);
        if (test(kk, nx, nz, g)) { head = qi.length; break; }
      }
      if (hitKey !== null) break;
    }

    if (hitKey !== null){
      const route = []; let k = hitKey, guard = 0;
      while (k !== null && guard++ < 1e6){ const p = par.get(k); if (!p) break;
        if (p.e) route.push(p.e); k = p.p; }
      return {ok:true, reason:'reached', cells:seen.size, near, startOffset, seen, route:route.reverse()};
    }
    return {ok:false, reason: budgetHit ? 'budget' : timeHit ? 'timeout' : 'no-path',
            cells:seen.size, near, startOffset, seen, route:[]};
  }

  const fwd = await fill(A, B, TOL);
  const out = {ok:fwd.ok, reason:fwd.reason, cells:fwd.cells, near:fwd.near, route:fwd.route,
               startOffset:fwd.startOffset, walklock:wl, step:STEP, tol:TOL, edges:edges.length,
               probes, yields, ms:0, gap:null, reverseCells:0, targetStandable:null};

  // ---- ONLY ON A RED: fill from B as well, and MEASURE THE GAP ------------------
  // "unreachable" is not actionable. "the two reachable regions come within 0.9 m of
  // each other at (61.2,-44.0), 0.1 m apart in height" is. Same lattice both times, so
  // the minimum is a ring search in a hash rather than an N^2 scan. dy is carried
  // because a 0.4 m plan gap across a 10 m drop is a CLIFF, not a doorway.
  if (!fwd.ok && fwd.reason === 'no-path'){
    const rev = await fill(B, A, TOL);
    out.reverseCells = rev.cells;
    out.targetStandable = rev.reason !== 'start-unstandable';
    if (rev.seen && rev.seen.size && fwd.seen.size){
      let best = null;
      const maxR = Math.ceil(10/STEP);
      for (const [kb, yb] of rev.seen){
        const i = KI(kb), j = KJ(kb);
        for (let r=1; r<=maxR; r++){
          if (best && r*STEP >= best.d) break;
          let found = false;
          for (let di=-r; di<=r && !found; di++) for (let dj=-r; dj<=r; dj++){
            if (Math.max(Math.abs(di),Math.abs(dj)) !== r) continue;
            const ka = key(i+di,j+dj); if (!fwd.seen.has(ka)) continue;
            const d = Math.hypot(di*STEP, dj*STEP);
            if (!best || d < best.d) best = {d:+d.toFixed(2), dy:+Math.abs(fwd.seen.get(ka)-yb).toFixed(2),
              from:[+XX(i+di).toFixed(2), +fwd.seen.get(ka).toFixed(2), +ZZ(j+dj).toFixed(2)],
              to:[+XX(i).toFixed(2), +yb.toFixed(2), +ZZ(j).toFixed(2)]};
            found = true; break;
          }
          if (found) break;
        }
      }
      out.gap = best;
    }
  }
  out.probes = probes; out.yields = yields; out.ms = Date.now() - t0;
  return out;
};
return 'armed'; })()`;

// The call, as a page expression. A and B are [x, y, z] — story.json's own `at` order.
export const REACH = (A, B, opt) =>
  `window.__ebReach(${JSON.stringify(A)}, ${JSON.stringify(B)}, ${JSON.stringify(opt || {})})`;

// Install-if-needed AND call, in ONE Runtime.evaluate. Two evaluates would be two
// waits on the page's main thread, and in del-cine (2493 meshes, software GL in a
// headless tab) a single evaluate waits up to ~7 s for a frame to end — an order of
// magnitude more than the fill itself costs. So: one round trip per pair.
export const CALL = (A, B, opt) =>
  `(()=>{ if(!window.__ebReach){ ${INSTALL} } return ${REACH(A, B, opt)}; })()`;

// One actionable line out of one result. A FAILURE MUST NAME THE PAIR AND THE GAP.
export function verdict(fromId, toId, A, B, res) {
  const d = Math.hypot(B[0] - A[0], B[2] - A[2]);
  const head = `${fromId} -> ${toId}`;
  if (res.ok) {
    const via = res.route.length ? `, via ${res.route.length} in-scene edge${res.route.length > 1 ? 's' : ''}` : ' on foot';
    return `${head}: reachable (${d.toFixed(1)} m apart, ${res.cells} cells filled${via})`;
  }
  const n = res.near;
  if (res.reason === 'start-unstandable')
    return `${head}: UNREACHABLE — the START anchor [${A.map(v => +v.toFixed(2))}] is not standable in the ` +
           `running game (no walk floor within 2 m). A body teleported there cannot walk at all.`;
  if (res.reason === 'budget' || res.reason === 'timeout')
    return `${head}: INCONCLUSIVE — the fill hit its ${res.reason} after ${res.cells} cells; ` +
           `nearest approach ${n ? n.d + ' m' : '?'}. Re-run that pair alone with a bigger --walk-budget.`;
  if (res.targetStandable === false)
    return `${head}: UNREACHABLE — the TARGET anchor [${B.map(v => +v.toFixed(2))}] is not standable in the ` +
           `running game, and the nearest ground the player can reach is ${n ? n.d.toFixed(1) : '?'} m away ` +
           `(${res.cells} cells filled). No walk can ever trigger this beat.`;
  const g = res.gap;
  return `${head}: UNREACHABLE — ${res.cells} cells filled from the start, ${res.reverseCells} from the target, ` +
         `and they never meet. Nearest standable cell to the target is ${n ? n.d.toFixed(1) : '?'} m away` +
         (n ? ` (at ${n.x},${n.y},${n.z}, ${n.dy} m off in height)` : '') +
         (g ? `; the two regions come within ${g.d} m of each other between ${JSON.stringify(g.from)} and ` +
              `${JSON.stringify(g.to)} — a ${g.dy} m step` : '') + '.';
}
