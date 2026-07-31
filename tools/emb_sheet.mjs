// emb_sheet.mjs — the contact sheet for Emberbrook's BAKED cinematic set.
//
//   node tools/emb_sheet.mjs            write docs/qa/emberbrook/cameras.html
//
// Not a review render. This reads what was actually baked — public/assets/scenes/
// emb-cine/cine.json — beside what was authored (emberbrook.cameras.json) and what was
// solved (emberbrook.cameras.solved.json), and puts the three on one page with the plate.
// A contact sheet whose numbers come from anywhere but the bake is a sheet that can lie
// about the thing it is showing you.
import fs from 'fs';
import path from 'path';
import {PUB, rd} from './cine_regions.mjs';

const CAM = rd('townmap/emberbrook.cameras.json');
const SOL = rd('townmap/emberbrook.cameras.solved.json');
const CINE = rd(`assets/scenes/${CAM.sceneKey}/cine.json`);
const A = Object.fromEntries(CAM.cameras.map((c) => [c.id, c]));
const S = Object.fromEntries(SOL.cameras.map((c) => [c.id, c]));
const OUT = path.join(PUB, '../docs/qa/emberbrook/cameras.html');
const REL = path.relative(path.dirname(OUT), path.join(PUB, 'assets/scenes', CAM.sceneKey, 'cameras'));

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const rows = CINE.cameras.map((b) => {
  const a = A[b.id] || {}, s = S[b.id] || {};
  const f = a.framing || {};
  const vis = b.visibleFrac == null ? '—' : (b.visibleFrac * 100).toFixed(1) + '%';
  const badge = (t, cls) => `<span class="k ${cls || ''}">${esc(t)}</span>`;
  return `<figure id="${esc(b.id)}">
  <div class=pair>
    <img src="${REL}/${b.id}/bg.png" alt="${esc(b.id)} background">
    <img src="${REL}/${b.id}/depth.png" alt="${esc(b.id)} depth" class=depth>
  </div>
  <figcaption>
    <h2>${esc(b.name)} ${badge(b.id)}${b.entry ? badge('entry', 'e') : ''}${b.transit ? badge('transit', 't') : ''}</h2>
    <p class=shot>${esc(a.shot || '')}</p>
    <table>
      <tr><th>authored</th><td>yaw ${f.yaw ?? CAM.defaults.fov} &middot; pitch ${f.pitch} &middot; margin ${f.margin ?? CAM.defaults.margin} &middot; fov ${b.fov}</td></tr>
      <tr><th>solved</th><td>pos [${b.pos.map((v) => v.toFixed(1)).join(', ')}] &rarr; aim [${b.aim.map((v) => v.toFixed(1)).join(', ')}] &middot; standoff ${s.dist} m</td></tr>
      <tr><th>legibility</th><td>character ${s.charPxNear}&hellip;${s.charPxFar} px of 768 &middot; region in frame ${((s.inFrameFrac ?? 0) * 100).toFixed(1)}%</td></tr>
      <tr><th>visibility</th><td><b class="${(b.visibleFrac ?? 0) >= 0.45 ? 'ok' : 'no'}">${vis}</b> of ${b.probes} probes unoccluded (bar 45%) &middot; depth ${b.depth ? b.depth.near.toFixed(1) + '&hellip;' + b.depth.far.toFixed(0) + ' m' : '—'}</td></tr>
      <tr><th>owns</th><td>${(a.owns.landmarks || []).map((l) => `<code>${esc(l)}</code>`).join(' ') || '<i>no landmarks, by design</i>'}<br>${(a.owns.edges || []).map((e) => `<code>${esc(e)}</code>`).join(' ')}</td></tr>
      ${a._framing_note ? `<tr><th>why</th><td class=note>${esc(a._framing_note)}</td></tr>` : ''}
    </table>
  </figcaption>
</figure>`;
}).join('\n');

const D = CAM.defaults, RIG = D.lightRig || {};
fs.writeFileSync(OUT, `<!doctype html><meta charset=utf-8>
<title>Emberbrook &mdash; the cinematic set</title>
<style>
body{background:#12100e;color:#e8dfd0;font:15px/1.6 -apple-system,Segoe UI,sans-serif;margin:0;padding:30px 34px 80px;max-width:1500px}
h1{font-weight:600;letter-spacing:.02em;margin:0 0 6px;font-size:27px}
p.sub{color:#9b8f7d;margin:0 0 8px;max-width:78ch}
.grade{border:1px solid #3a2f22;border-radius:5px;padding:12px 16px;margin:22px 0 34px;background:#171410;max-width:78ch}
.grade b{color:#e8b563}
figure{margin:0 0 44px;border-top:1px solid #2a231b;padding-top:20px}
.pair{display:grid;grid-template-columns:2fr 1fr;gap:10px}
img{width:100%;display:block;border:1px solid #302a22;border-radius:3px}
img.depth{filter:contrast(1.15)}
h2{font-size:18px;font-weight:600;margin:14px 0 4px}
p.shot{color:#b3a693;margin:0 0 12px;max-width:88ch;font-style:italic}
table{border-collapse:collapse;font-size:13.5px}
th{text-align:right;color:#8d8574;font-weight:500;padding:2px 12px 2px 0;vertical-align:top;white-space:nowrap;width:1px}
td{padding:2px 0;color:#cfc4b1}
td.note{color:#9b8f7d;max-width:86ch;font-size:12.8px}
code{background:#1d1913;border:1px solid #2e281f;border-radius:3px;padding:0 4px;font-size:12px;color:#c9b48c}
b.ok{color:#8fc07a}b.no{color:#d98a6a}
.k{background:#221c14;border:1px solid #4a3a22;color:#c98a3c;text-transform:uppercase;font-size:10.5px;
   letter-spacing:.09em;padding:1px 7px;border-radius:9px;margin-left:8px;vertical-align:middle}
.k.e{color:#e8b563;border-color:#6a5024}.k.t{color:#8ab0c9;border-color:#2f4657}
</style>
<h1>Emberbrook &mdash; the cinematic set</h1>
<p class=sub>The ${CINE.cameras.length} baked shots of <code>${CAM.sceneKey}</code>, each with the background the
game draws and the depth map it occludes the character against &mdash; both out of one Cycles
session on one camera, so the image and the occlusion cannot disagree. Every number below is
read from the bake (<code>cine.json</code>) and the solve, never typed here.</p>
<div class=grade><b>THE EMBERWAKE EVENING.</b> exposure ${D.exposure} &middot; ${D.view_transform} / ${D.look}
&middot; sun ${RIG.sun ? RIG.sun.energy : '—'} raking, sky ${RIG.world ? RIG.world.strength : '—'} &middot;
the Heartlight at 5200 W and the ${RIG.census ? RIG.census.lamps : '—'} lamps lit from it, numbered in Lake's own rounds order.
Chapter One is this hour, and the two accepted Chapter One paintings &mdash;
<code>square/festival.png</code> and <code>entrance/main.png</code> &mdash; are already lit by it.
Golden hour is one re-run away: the grade is two fields of <code>defaults</code> and nothing else.</div>
${rows}
<p class=sub style="margin-top:40px">Generated by <code>tools/emb_sheet.mjs</code> from
<code>${CAM.sceneKey}/cine.json</code> + <code>emberbrook.cameras{,.solved}.json</code>.</p>
`);
console.log('wrote ' + path.relative(path.join(PUB, '..'), OUT) + `  (${CINE.cameras.length} cameras)`);

// ...and keep docs/qa/emberbrook/index.html pointing at it. index.html is REGENERATED by
// tools/emb_shots.py (the review renders), so a hand-added link cannot be trusted to
// survive — it is re-inserted here, idempotently, every time the sheet is rebuilt. The
// marker makes the block replaceable rather than duplicated.
const IDX = path.join(path.dirname(OUT), 'index.html');
if (fs.existsSync(IDX)) {
  const MARK = '<!--CAMSHEET-->';
  const banner = `${MARK}<p style="border:1px solid #4a3a22;border-radius:5px;padding:11px 15px;` +
    `margin:0 0 26px;background:#191510"><b style="color:#e8b563">THE BAKED SET &rarr;</b> ` +
    `<a href="cameras.html" style="color:#c98a3c">cameras.html</a> &mdash; the ` +
    `${CINE.cameras.length} shipped shots of <code>${CAM.sceneKey}</code>, background and depth, ` +
    `each with its authored intent, solved standoff, measured visibility and character ` +
    `legibility beside it. The frames below are REVIEW renders and predate them.</p>${MARK}`;
  let html = fs.readFileSync(IDX, 'utf8');
  html = html.includes(MARK)
    ? html.replace(new RegExp(MARK + '[\\s\\S]*?' + MARK), banner)
    : html.replace('</p>', '</p>\n' + banner);
  fs.writeFileSync(IDX, html);
  console.log('       index.html banner refreshed');
}
