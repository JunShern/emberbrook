// worldmap_validate.mjs — validate the world geography hierarchy.
// Usage: node tools/worldmap_validate.mjs [regionId]
// Checks (all hierarchical-refinement rules, consistency-by-construction):
//   world level : river spine monotonically descends; navigable widths hold;
//                 every region's exits sit on its envelope edge (±margin)
//   region level: all content inside the envelope; refined river within
//                 tolerance of the parent spine and covers the region's share
//                 of it; road slopes within spec; portals at road endpoints
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "public");
const world = JSON.parse(readFileSync(join(ROOT, "world/world.json")));
let errs = 0, warns = 0;
const err = (m) => { console.log("ERROR", m); errs++; };
const warn = (m) => { console.log("WARN ", m); warns++; };
const ok = (m) => console.log("ok   ", m);

const d2 = (a, b) => (a[0]-b[0])**2 + (a[1]-b[1])**2;
function ptSegDist(p, a, b) {
  const l2 = d2(a, b); if (!l2) return Math.sqrt(d2(p, a));
  let t = ((p[0]-a[0])*(b[0]-a[0]) + (p[1]-a[1])*(b[1]-a[1])) / l2;
  t = Math.max(0, Math.min(1, t));
  return Math.sqrt(d2(p, [a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])]));
}
const distToPolyline = (p, pts) => Math.min(...pts.slice(1).map((b, i) => ptSegDist(p, pts[i], b)));
function inPoly(p, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj-xi)*(p[1]-yi))/(yj-yi) + xi) inside = !inside;
  }
  return inside;
}

// ---- world level -------------------------------------------------------------
const spine = world.riverSpine.points;
for (let i = 1; i < spine.length; i++)
  if (spine[i].pos[2] > spine[i-1].pos[2] + 1e-9)
    err(`river spine ascends at point ${i} (${spine[i-1].pos[2]} -> ${spine[i].pos[2]})`);
ok(`river spine descends monotonically over ${spine.length} points`);
const navFromIdx = spine.findIndex(p => (p.note || "").includes("below the locks"));
const navStart = navFromIdx >= 0 ? navFromIdx : spine.length - 2;
for (let i = navStart; i < spine.length; i++)
  if (spine[i].width < world.riverSpine.minNavigableWidth)
    err(`spine point ${i} width ${spine[i].width} < minNavigableWidth ${world.riverSpine.minNavigableWidth}`);
ok(`navigable widths hold from point ${navStart} downstream`);

// ---- each region -------------------------------------------------------------
for (const reg of world.regions) {
  const R = JSON.parse(readFileSync(join(ROOT, reg.file)));
  const env = reg.envelope;
  const inside = (p, what) => { if (!inPoly(p, env)) err(`${reg.id}: ${what} [${p[0]},${p[1]}] outside envelope`); };

  for (const p of R.river.points) inside(p, "river point");
  for (const p of R.road.points) inside(p, "road point");
  for (const l of R.landmarks || []) inside(l.pos, `landmark ${l.id}`);
  for (const a of R.townAnchors || []) inside(a.pos, `townAnchor ${a.town}`);
  ok(`${reg.id}: containment (${R.river.points.length} river + ${R.road.points.length} road pts, ${(R.landmarks||[]).length} landmarks)`);

  // river fidelity: every refined point near the parent spine, and every
  // in-envelope spine point near the refined course (coverage)
  const spineXY = spine.map(p => p.pos);
  const tol = world.tolerance.riverRefine;
  let worst = 0;
  for (const p of R.river.points) worst = Math.max(worst, distToPolyline(p, spineXY));
  if (worst > tol) err(`${reg.id}: refined river drifts ${worst.toFixed(1)}u from spine (tol ${tol})`);
  else ok(`${reg.id}: river refines spine (worst drift ${worst.toFixed(1)}u <= ${tol})`);
  let worstCov = 0;
  for (const sp of spineXY) if (inPoly(sp, env)) worstCov = Math.max(worstCov, distToPolyline(sp, R.river.points));
  if (worstCov > tol) err(`${reg.id}: spine coverage gap ${worstCov.toFixed(1)}u (tol ${tol})`);
  else ok(`${reg.id}: spine fully covered (worst ${worstCov.toFixed(1)}u)`);

  for (let i = 1; i < R.river.points.length; i++)
    if (R.river.points[i][2] > R.river.points[i-1][2] + 1e-9)
      err(`${reg.id}: refined river ascends at point ${i}`);

  // road slopes (walkable spec: <= 45deg, warn > 35deg)
  for (let i = 1; i < R.road.points.length; i++) {
    const a = R.road.points[i-1], b = R.road.points[i];
    const run = Math.sqrt(d2(a, b)), rise = Math.abs(b[2] - a[2]);
    const deg = Math.atan2(rise, run) * 180 / Math.PI;
    if (deg > 45) err(`${reg.id}: road segment ${i} slope ${deg.toFixed(1)}deg > 45`);
    else if (deg > 35) warn(`${reg.id}: road segment ${i} slope ${deg.toFixed(1)}deg`);
  }
  ok(`${reg.id}: road slopes checked (${R.road.points.length - 1} segments)`);

  for (const po of R.road.portals || []) {
    const dEnds = Math.min(Math.sqrt(d2(po.at, R.road.points[0])), Math.sqrt(d2(po.at, R.road.points.at(-1))));
    if (dEnds > 2) err(`${reg.id}: portal ${po.id} is ${dEnds.toFixed(1)}u from a road endpoint`);
  }
  ok(`${reg.id}: portals sit on road endpoints`);

  for (const ex of reg.exits || []) {
    const dEdge = Math.min(...env.map((v, i) => ptSegDist(ex.at, v, env[(i+1) % env.length])));
    if (dEdge > 6) warn(`${reg.id}: exit ${ex.id} is ${dEdge.toFixed(1)}u from the envelope edge`);
  }
}

console.log(errs ? `\nFAILED: ${errs} error(s), ${warns} warning(s)` : `\nPASSED (${warns} warning(s))`);
process.exit(errs ? 1 : 0);
