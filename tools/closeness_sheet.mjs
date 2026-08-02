// closeness_sheet.mjs — THE MORNING BOARD for the camera-closeness round (user redline
// 2026-08-02: "the camera angle is often too high up and far away... characters end up
// looking like ants").
//
//   node tools/closeness_sheet.mjs --draft <afterDir> [--before <beforeDir>]
//                                  [--town emberbrook] [--out docs/qa/closeness]
//
// It pairs, per shot, the OLD framing with the RE-SOLVED one and prints the numbers that
// moved underneath both. Both sides carry 1.7 m matte stand-ins on the shot's own ground
// at its nearest / median / farthest spawn candidate, because the stand-ins ARE the point:
// charPxFar is a number, and "does the player read as an ant" is a thing you answer by
// looking at a figure standing on the ground the shot owns. A LIKE-FOR-LIKE A/B needs the
// figure on BOTH sides — so `--before` takes a second draft dir, rendered at the OLD
// solved cameras (stage them under a temp town id: copy the old
// <town>.cameras.solved.json to <townOLD>.cameras.solved.json and bake `--town <townOLD>`,
// which needs no other file and touches nothing live). Without `--before` the left pane
// falls back to the shipped plate, which is honest but not like-for-like: it is a
// 128-spp finished frame with no character in it.
//
// WHY IT COPIES THE DRAFTS. A draft render lives in a scratch directory that is gone by
// morning. The sheet has to survive the session that made it, and it has to keep showing
// the BEFORE after the full bakes have overwritten it — so both images are copied in and
// the page is self-contained. The shipped plate is downscaled by the browser only; the
// file copied is the real one, so a reader can open it at full size.
import fs from 'fs';
import path from 'path';

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const REPO = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const TOWN = opt('--town', 'emberbrook');
const DRAFT = path.resolve(opt('--draft', ''));
const BEFORE_DIR = opt('--before', null) ? path.resolve(opt('--before', '')) : null;
const OUT = path.resolve(REPO, opt('--out', 'docs/qa/closeness'));
if (!DRAFT || !fs.existsSync(DRAFT)) {
  console.error('need --draft <dir> (a tools/cine_bake.py --draft output)');
  process.exit(1);
}

const solved = JSON.parse(fs.readFileSync(
  path.join(REPO, `public/townmap/${TOWN}.cameras.solved.json`), 'utf8'));
const cams = JSON.parse(fs.readFileSync(
  path.join(REPO, `public/townmap/${TOWN}.cameras.json`), 'utf8'));
const cineP = path.join(REPO, `public/assets/scenes/${solved.sceneKey}/cine.json`);
const cine = fs.existsSync(cineP) ? JSON.parse(fs.readFileSync(cineP, 'utf8')) : {cameras: []};
const baked = Object.fromEntries((cine.cameras || []).map((c) => [c.id, c]));
const draftDoc = JSON.parse(fs.readFileSync(path.join(DRAFT, 'draft.json'), 'utf8'));

// THE BEFORE, frozen. Once the full bakes land, cine.json describes the AFTER — so the
// shipped numbers are read now and written into the page as literals, and the page keeps
// being a before/after instead of quietly becoming an after/after.
const BEFORE_P = path.join(OUT, 'before.json');
fs.mkdirSync(path.join(OUT, 'img'), {recursive: true});
let before;
if (fs.existsSync(BEFORE_P)) {
  before = JSON.parse(fs.readFileSync(BEFORE_P, 'utf8'));
} else {
  before = {};
  for (const c of cine.cameras || [])
    before[c.id] = {pos: c.pos, aim: c.aim, fov: c.fov, visibleFrac: c.visibleFrac,
                    charPxNear: null, charPxFar: null, baked: c.baked};
  fs.writeFileSync(BEFORE_P, JSON.stringify(before, null, 1) + '\n');
}
// charPx is not in cine.json (it is a solver number), so the shipped values are passed
// in by the caller once, here, as the record of what the user was looking at.
const SHIPPED_CHARPX = {
  woodroad: [95, 59], waystone: [132, 76], arch: [96, 44], orchard: [84, 50],
  therise: [163, 69], square: [63, 37], pondlane: [123, 66], homerow: [104, 58],
  northlane: [88, 58], gateroad: [93, 61], gatefield: [91, 54],
};

const cp = (src, dst) => { if (fs.existsSync(src)) { fs.copyFileSync(src, dst); return true; } return false; };
const rows = [];
for (const s of solved.cameras) {
  const id = s.id;
  const cam = cams.cameras.find((c) => c.id === id) || {};
  const b = before[id] || {};
  const d = (draftDoc.cameras || {})[id];
  const shipImg = path.join(REPO, `public/assets/scenes/${solved.sceneKey}/cameras/${id}/bg.png`);
  const beforeDraft = BEFORE_DIR ? path.join(BEFORE_DIR, 'cameras', id, 'bg.png') : null;
  const likeForLike = !!(beforeDraft && fs.existsSync(beforeDraft));
  const drfImg = path.join(DRAFT, 'cameras', id, 'bg.png');
  const okA = cp(likeForLike ? beforeDraft : shipImg, path.join(OUT, 'img', `${id}-before.png`));
  const okB = cp(drfImg, path.join(OUT, 'img', `${id}-after.png`));
  rows.push({id, name: s.name, shot: s.shot, cam, s, b, d, okA, okB, likeForLike,
             shipCharPx: SHIPPED_CHARPX[id] || [null, null]});
}

const esc = (t) => String(t ?? '').replace(/[&<>]/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]));
const num = (v, dp = 0) => (v === null || v === undefined ? '&mdash;' : Number(v).toFixed(dp));
const delta = (a, b) => {
  if (a == null || b == null) return '';
  const d = b - a;
  return `<span class="d ${d > 0 ? 'up' : d < 0 ? 'dn' : ''}">${d > 0 ? '+' : ''}${d}</span>`;
};
const BANDS = (cams.defaults || {})._closeness_bands || [];
const ESTABLISHING = new Set(['square']);

const html = `<!-- generated by tools/closeness_sheet.mjs -->
<meta charset="utf-8"><title>Emberbrook — camera closeness round</title>
<style>
 :root{--bg:#12141a;--fg:#e8e6e1;--dim:#9aa0aa;--line:#2a2e38;--up:#7fd18c;--dn:#e0806e;--acc:#d9a441}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
 header{padding:28px 32px 20px;border-bottom:1px solid var(--line);max-width:1400px;margin:0 auto}
 h1{margin:0 0 6px;font-size:26px;letter-spacing:-.01em}
 .sub{color:var(--dim);max-width:78ch}
 main{max-width:1400px;margin:0 auto;padding:0 32px 80px}
 .bands{margin:22px 0 0;padding:16px 18px;border:1px solid var(--line);border-radius:8px;background:#171a21}
 .bands pre{margin:0;white-space:pre-wrap;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#c9cdd6}
 table.sum{width:100%;border-collapse:collapse;margin:26px 0 10px;font:13px/1.4 ui-monospace,Menlo,monospace}
 table.sum th,table.sum td{padding:6px 9px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
 table.sum th:first-child,table.sum td:first-child{text-align:left}
 table.sum th{color:var(--dim);font-weight:600;text-align:right}
 .d{font-size:11px;margin-left:5px}
 .up{color:var(--up)} .dn{color:var(--dn)}
 .shot{margin:38px 0 0;padding-top:26px;border-top:1px solid var(--line)}
 .shot h2{margin:0 0 2px;font-size:19px}
 .shot h2 .tag{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--acc);border:1px solid var(--acc);border-radius:3px;padding:2px 6px;margin-left:10px;vertical-align:2px}
 .shot .desc{color:var(--dim);font-size:13.5px;max-width:90ch;margin:0 0 14px}
 .pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
 .pane{min-width:0}
 .pane figcaption{font:12px/1.4 ui-monospace,Menlo,monospace;color:var(--dim);padding:7px 2px}
 .pane img{width:100%;height:auto;display:block;border-radius:5px;background:#000}
 .miss{padding:60px 12px;text-align:center;color:var(--dn);border:1px dashed var(--line);border-radius:5px}
 .why{margin:14px 0 0;padding:12px 14px;background:#171a21;border-left:3px solid var(--line);border-radius:0 6px 6px 0;font-size:13px;color:#c4c9d2}
 @media (max-width:900px){.pair{grid-template-columns:1fr}}
 @media (prefers-color-scheme:light){:root{--bg:#faf9f7;--fg:#1a1d23;--dim:#5c626c;--line:#e0dfdb;--up:#1f7a37;--dn:#a8331b}
  .bands,.why{background:#f1efec}}
 :root[data-theme="light"]{--bg:#faf9f7;--fg:#1a1d23;--dim:#5c626c;--line:#e0dfdb;--up:#1f7a37;--dn:#a8331b}
 :root[data-theme="light"] .bands,:root[data-theme="light"] .why{background:#f1efec}
 :root[data-theme="dark"]{--bg:#12141a;--fg:#e8e6e1;--dim:#9aa0aa;--line:#2a2e38;--up:#7fd18c;--dn:#e0806e}
 :root[data-theme="dark"] .bands,:root[data-theme="dark"] .why{background:#171a21}
</style>
<header>
<h1>Emberbrook — the camera-closeness round</h1>
<p class="sub">Your redline: <em>&ldquo;the camera angle is often too high up and far away from the characters&hellip; they end up
looking pretty small, like ants.&rdquo;</em> Left is what ships today. Right is the re-solved frame, drafted at
1008&times;576 / 28 spp with <strong>1.7&nbsp;m matte stand-ins</strong> on the shot&rsquo;s own ground &mdash; nearest, middle and
farthest point a player can stand. Draft renders are noisy by design; judge the <em>framing</em>, not the grain.
The night grade is the shipped one, per shot, unchanged.</p>
<div class="bands"><pre>${esc(BANDS.join('\n'))}</pre></div>
</header>
<main>
<table class="sum">
<tr><th>shot</th><th>fov</th><th>yaw</th><th>pitch</th><th>standoff</th><th>charPx near</th><th>charPx far</th><th>band</th></tr>
${rows.map((r) => {
  const F = r.cam.framing || {};
  const est = ESTABLISHING.has(r.id);
  return `<tr><td>${esc(r.id)}</td><td>35 &rarr; ${num(F.fov)}</td><td>${num(F.yaw)}</td><td>${num(F.pitch)}</td>` +
    `<td>${num(r.s.dist, 1)} m</td>` +
    `<td>${num(r.shipCharPx[0])} &rarr; ${num(r.s.charPxNear)}${delta(r.shipCharPx[0], r.s.charPxNear)}</td>` +
    `<td>${num(r.shipCharPx[1])} &rarr; ${num(r.s.charPxFar)}${delta(r.shipCharPx[1], r.s.charPxFar)}</td>` +
    `<td>${est ? 'establishing &ge;40' : 'ordinary 62&ndash;145'}</td></tr>`;
}).join('\n')}
</table>
${rows.map((r) => {
  const F = r.cam.framing || {};
  const est = ESTABLISHING.has(r.id);
  const bv = r.b.visibleFrac, dv = r.d ? r.d.visibleFrac : null;
  return `<section class="shot">
<h2>${esc(r.name)} <span style="color:var(--dim);font-size:14px">${esc(r.id)}</span>${est ? '<span class="tag">establishing</span>' : ''}</h2>
<p class="desc">${esc(r.shot)}</p>
<div class="pair">
 <figure class="pane">${r.okA ? `<img src="img/${r.id}-before.png" alt="shipped">` : '<div class="miss">no shipped plate</div>'}
  <figcaption>BEFORE &mdash; ${r.likeForLike ? 'draft at the shipped camera' : 'shipped plate (no stand-in)'} &middot; fov 35 &middot; charPx ${num(r.shipCharPx[0])}..${num(r.shipCharPx[1])} &middot; bake-visible ${bv == null ? '&mdash;' : (bv * 100).toFixed(1) + '%'}</figcaption></figure>
 <figure class="pane">${r.okB ? `<img src="img/${r.id}-after.png" alt="draft">` : '<div class="miss">draft not rendered</div>'}
  <figcaption>AFTER &mdash; draft &middot; fov ${num(F.fov)} yaw ${num(F.yaw)} pitch ${num(F.pitch)} &middot; charPx ${num(r.s.charPxNear)}..${num(r.s.charPxFar)} &middot; bake-visible ${dv == null ? '&mdash;' : (dv * 100).toFixed(1) + '%'}</figcaption></figure>
</div>
<div class="why">${esc((r.cam._framing_note || '').split('The note this heads is kept below')[0])}</div>
</section>`;
}).join('\n')}
</main>
`;
fs.writeFileSync(path.join(OUT, 'index.html'), html);
console.log('wrote ' + path.relative(REPO, path.join(OUT, 'index.html')) +
            `  (${rows.filter((r) => r.okB).length}/${rows.length} drafts present)`);
