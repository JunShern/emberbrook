#!/usr/bin/env node
// battle_foeline_stats.mjs — READ THE FOE-LINE ARMS, AND BUILD THEIR BOARD.
//
//   node tools/battle_foeline_stats.mjs docs/qa/battle-foeline/overlap-*.json
//   node tools/battle_foeline_stats.mjs --board
//
// The arms themselves come from the instrument, not from here:
//   node tools/battle_decide.mjs --port=3000 --mode=overlap --tag=<t> \
//        [--foe=<rake> --foedz=<depth>] [--beye2=1] [--group=a,b] \
//        --out=docs/qa/battle-foeline
// which measures with tools/battle_overlap_lib.mjs — occlusion is an
// INTERSECTION of the solo silhouette and the visible-pixels mask, never a ratio
// of areas. Everything below is arithmetic on that JSON: it invents no number
// and reads no pixel. Run it from the repo root (paths are repo-relative).
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const files = process.argv.slice(2).filter(a => a !== '--board');
const med = a => { const b = a.slice().sort((x, y) => x - y); return b.length ? +b[Math.floor(b.length / 2)].toFixed(3) : null; };

export function arm(f) {
  const d = JSON.parse(readFileSync(f, 'utf8'));
  const sites = {};
  for (const r of d.rows) {
    const rows = (r.ovl && r.ovl.rows) || [];
    const foes = rows.filter(x => x.side === 'foe');
    const party = rows.filter(x => x.side !== 'foe');
    const g = (r.ovl && r.ovl.geo) || {};
    const num = (a, k) => a.map(x => (x[k] == null ? 0 : x[k]));
    // foe lateral separation at the live decide pose, from the plan's own coords
    let flat = null, fang = null, fL = null;
    const o = r.ovl;
    if (o && o.placed && o.pose && o.base && foes.length >= 2 && o.placed[foes[0].id] && o.placed[foes[1].id]) {
      const by = o.base.yaw, th = o.pose.yaw - o.base.yaw;
      const rx = Math.sin(by), rz = -Math.cos(by), fx = -Math.cos(by), fz = -Math.sin(by);
      const uv = p => ({ u: p.x * rx + p.z * rz, v: p.x * fx + p.z * fz });
      const A = uv(o.placed[foes[0].id]), B = uv(o.placed[foes[1].id]);
      const du = B.u - A.u, dv = B.v - A.v, L = Math.hypot(du, dv);
      const cr = { u: Math.cos(th), v: -Math.sin(th) }, cf = { u: Math.sin(th), v: Math.cos(th) };
      flat = Math.abs(du * cr.u + dv * cr.v); fL = L;
      fang = Math.acos(Math.min(1, Math.abs((du * cf.u + dv * cf.v) / (L || 1)))) * 180 / Math.PI;
    }
    sites[r.id] = {
      id: r.id, zone: r.zone,
      foeTeam: Math.max(0, ...num(foes, 'occTeam')),
      foeWorld: Math.max(0, ...num(foes, 'occWorld')),
      foeTotal: Math.max(0, ...num(foes, 'occTotal')),
      partyTeam: Math.max(0, ...num(party, 'occTeam')),
      partyWorld: Math.max(0, ...num(party, 'occWorld')),
      partyTotal: Math.max(0, ...num(party, 'occTotal')),
      noSil: rows.filter(x => x.why === 'no silhouette').length,
      noReg: rows.filter(x => x.why === 'no region').length,
      dcx: (foes.length >= 2 && foes[0].cx != null && foes[1].cx != null)
        ? +Math.abs(foes[0].cx - foes[1].cx).toFixed(4) : null,
      hFrac: med(num(foes, 'hFrac')),
      foesIn: r.foesIn, foesAll: r.foesAll, axisOk: r.axisOk,
      camDist: r.camDist, R: r.site && r.site.R, stageMs: r.site && r.site.ms,
      lat: flat == null ? null : +flat.toFixed(3), ang: fang == null ? null : +fang.toFixed(1),
      L: fL == null ? null : +fL.toFixed(3),
    };
  }
  return { meta: d.meta, sites, name: f.split('/').pop().replace(/^overlap-|\.json$/g, '') };
}

export function dist(a, key) {
  const v = Object.values(a.sites);
  const c = t => v.filter(s => s[key] >= t).length;
  return `${c(0.10)}/${c(0.25)}/${c(0.50)}`;
}

if (files.length && !process.argv.includes('--board')) {
  const arms = files.filter(existsSync).map(arm);
  const hdr = ['arm', 'n', 'FOEteam', 'FOEworld', 'FOEtot', 'PTYteam', 'PTYworld', 'PTYtot',
               'noSil', 'foesIn', 'axisOk', 'dcx p50', 'lat p50', 'ang p50', 'hFrac p50', 'camD p50', 'R0', 'stageMs p50'];
  console.log(hdr.join('\t'));
  for (const a of arms) {
    const v = Object.values(a.sites);
    console.log([a.name, v.length, dist(a, 'foeTeam'), dist(a, 'foeWorld'), dist(a, 'foeTotal'),
      dist(a, 'partyTeam'), dist(a, 'partyWorld'), dist(a, 'partyTotal'),
      v.reduce((s, x) => s + x.noSil + x.noReg, 0),
      v.reduce((s, x) => s + (x.foesIn || 0), 0) + '/' + v.reduce((s, x) => s + (x.foesAll || 0), 0),
      v.filter(x => x.axisOk !== false).length + '/' + v.length,
      med(v.map(x => x.dcx || 0)), med(v.map(x => x.lat || 0)), med(v.map(x => x.ang || 0)),
      med(v.map(x => x.hFrac || 0)), med(v.map(x => x.camDist || 0)),
      v.filter(x => x.R === 0).length, med(v.map(x => x.stageMs || 0))].join('\t'));
  }
}


// ===================== THE BOARD ==========================================
if (process.argv.includes('--board')) {

const D = 'docs/qa/battle-foeline/';
const A = f => arm(D + 'overlap-' + f + '.json');
const med = a => { const b = a.filter(x => x != null).slice().sort((x, y) => x - y); return b.length ? +b[Math.floor(b.length / 2)].toFixed(3) : null; };
const cls = v => v == null ? '' : (v >= 0.5 ? 'bad' : v >= 0.25 ? 'warn' : v >= 0.10 ? 'warn' : 'ok');
const f2 = v => v == null ? '&mdash;' : (+v).toFixed(3);

const sweep = [
  ['sw-ctl', '(0, 1) &mdash; the shipped closed form', 0],
  ['sw-abs', '(0.25, 1) &mdash; drop the <code>Math.abs</code>, keep foeChevron 0.5', 0],
  ['sw-r05d1', '(0.5, 1)', 0],
  ['sw-r1d1', '(1, 1) &mdash; the diagonal: rake AND depth', 0],
  ['sw-r07d05', '(0.7, 0.5)', 0],
  ['sw-r07d0', '(0.7, 0)', 0],
  ['sw-r1d0', '(1, 0) &mdash; a flat rank abreast', 1],
  ['sw-r14d0', '(1.4, 0)', 0],
  ['sw-rm1d0', '(&minus;1, 0) &mdash; the flat rank, other sign', 0],
];

const armRow = (a, label) => {
  const v = Object.values(a.sites);
  return `<tr><td>${label}</td><td>${v.length}</td>
  <td>${dist(a, 'foeTeam')}</td><td>${dist(a, 'foeWorld')}</td><td>${dist(a, 'foeTotal')}</td>
  <td>${dist(a, 'partyTeam')}</td><td>${dist(a, 'partyWorld')}</td><td>${dist(a, 'partyTotal')}</td>
  <td>${v.reduce((s, x) => s + x.noSil + x.noReg, 0)}</td>
  <td>${v.reduce((s, x) => s + (x.foesIn || 0), 0)}/${v.reduce((s, x) => s + (x.foesAll || 0), 0)}</td>
  <td>${v.filter(x => x.axisOk !== false).length}/${v.length}</td>
  <td>${med(v.map(x => x.dcx))}</td><td>${med(v.map(x => x.lat))}</td><td>${med(v.map(x => x.ang))}&deg;</td>
  <td>${med(v.map(x => x.hFrac))}</td><td>${med(v.map(x => x.camDist))}</td>
  <td>${v.filter(x => x.R === 0).length}</td><td>${med(v.map(x => x.stageMs))}</td></tr>`;
};

const SW = sweep.map(([tag, label, win]) => {
  const a = A(tag); const v = Object.values(a.sites);
  return `<tr class="${win ? 'win' : ''}"><td>${label}</td><td>${dist(a, 'foeTeam')}</td><td>${dist(a, 'foeTotal')}</td>
    <td>${v.reduce((s, x) => s + x.noSil + x.noReg, 0)}</td>
    <td>${v.reduce((s, x) => s + (x.foesIn || 0), 0)}/${v.reduce((s, x) => s + (x.foesAll || 0), 0)}</td>
    <td>${med(v.map(x => x.dcx))}</td><td>${med(v.map(x => x.lat))}</td><td>${med(v.map(x => x.ang))}&deg;</td>
    <td>${med(v.map(x => x.hFrac))}</td><td>${med(v.map(x => x.camDist))}</td></tr>`;
}).join('\n');

const B = A('before'), Af = A('after'), E = A('eye2');
const PB = existsSync(D + 'overlap-pair-before.json') ? A('pair-before') : null;
const PA = existsSync(D + 'overlap-pair-after.json') ? A('pair-after') : null;

function regs(key) {
  const up = [], dn = [];
  for (const id of Object.keys(B.sites)) {
    const b = B.sites[id], a = Af.sites[id]; if (!a) continue;
    const d = a[key] - b[key];
    if (d > 0.05) up.push(`${id} (${b.zone}) ${b[key].toFixed(2)}&rarr;${a[key].toFixed(2)}`);
    else if (d < -0.05) dn.push(id);
  }
  return { up, dn };
}
const rFoeT = regs('foeTeam'), rFoeW = regs('foeWorld'), rFoeTot = regs('foeTotal'),
      rPT = regs('partyTeam'), rPTot = regs('partyTotal');

const per = Object.keys(B.sites).map(id => {
  const b = B.sites[id], a = Af.sites[id]; if (!a) return '';
  return `<tr><td>${id}</td><td class=dim>${b.zone}</td>
  <td class="${cls(b.foeTeam)}">${b.foeTeam.toFixed(3)}</td><td class="${cls(b.foeTotal)}">${b.foeTotal.toFixed(3)}</td>
  <td class="${cls(a.foeTeam)}">${a.foeTeam.toFixed(3)}</td><td class="${cls(a.foeWorld)}">${a.foeWorld.toFixed(3)}</td>
  <td class="${cls(a.foeTotal)}">${a.foeTotal.toFixed(3)}</td>
  <td>${b.dcx == null ? '&mdash;' : b.dcx}</td><td>${a.dcx == null ? '&mdash;' : a.dcx}</td>
  <td>${b.lat == null ? '&mdash;' : b.lat}</td><td>${a.lat == null ? '&mdash;' : a.lat}</td>
  <td>${b.hFrac}</td><td>${a.hFrac}</td></tr>`;
}).join('\n');

const LOOK = ['s012', 's024', 's006', 's038'].map(id => {
  const b = B.sites[id], a = Af.sites[id];
  return `<h3>${id} &middot; ${b.zone}</h3><div class="pair">
  <figure><img loading="lazy" src="frames/before/${id}.jpg"><figcaption>BEFORE &mdash; second foe occTeam <b>${b.foeTeam.toFixed(2)}</b>, &Delta;cx ${b.dcx}</figcaption></figure>
  <figure><img loading="lazy" src="frames/after/${id}.jpg"><figcaption>AFTER &mdash; occTeam <b>${a.foeTeam.toFixed(2)}</b>, occWorld ${a.foeWorld.toFixed(2)}, &Delta;cx ${a.dcx}</figcaption></figure></div>`;
}).join('\n');

const html = `<title>The foe line stood in single file</title>
<style>
:root{--bg:#12141a;--fg:#e8e6e1;--dim:#9aa0aa;--line:#2a2f3a;--ok:#6fbf73;--warn:#d8a657;--bad:#e06c75;--acc:#7aa2f7}
@media (prefers-color-scheme:light){:root{--bg:#fbfaf7;--fg:#1b1d22;--dim:#5c626c;--line:#dcd8d0}}
:root[data-theme="dark"]{--bg:#12141a;--fg:#e8e6e1;--dim:#9aa0aa;--line:#2a2f3a}
:root[data-theme="light"]{--bg:#fbfaf7;--fg:#1b1d22;--dim:#5c626c;--line:#dcd8d0}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:2rem clamp(1rem,4vw,4rem)}
h1{font-size:1.7rem;margin:0 0 .2rem} h2{font-size:1.15rem;margin:2.2rem 0 .5rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
h3{font-size:1rem;margin:1.4rem 0 .3rem;color:var(--acc)}
p,li{max-width:78ch} .dim{color:var(--dim)} code{background:#0003;padding:.1em .35em;border-radius:3px}
table{border-collapse:collapse;font-size:13px;margin:.6rem 0;display:block;overflow-x:auto;max-width:100%}
th,td{border:1px solid var(--line);padding:.25rem .5rem;text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td.ok{color:var(--ok)} td.warn{color:var(--warn)} td.bad{color:var(--bad)}
tr.win td{background:#6fbf7322;font-weight:600}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin:.5rem 0}
.pair figure{margin:0} .pair img{width:100%;border:1px solid var(--line);border-radius:4px}
figcaption{font-size:12px;color:var(--dim)}
.lead{font-size:1.05rem}
</style>
<h1>The foe line stood in single file</h1>
<p class="dim">2026-08-09 &middot; instrument <code>tools/battle_overlap_lib.mjs</code> + <code>battle_decide --mode=overlap</code> &middot;
62-site census, three arms, one build &middot; <code>?bfoe=&lt;rake&gt;&amp;bfoedz=&lt;depth&gt;</code> is the A/B</p>

<p class="lead">The party-overlap lane found this in its own residuals and left it on purpose. <code>slotsFor</code> gives a foe
<code>ax = foeX + |i &minus; (n&minus;1)/2| &middot; foeChevron</code>: <b>the absolute value makes the chevron a V at three
foes and inert at two</b> &mdash; both foes take the same across-axis coordinate and differ only in depth. Measured here, on the
shipped build: <b>the second foe is &ge;25% eaten by the first at 44 of 62 sites and &ge;50% at 28</b>, with the pair's
screen-x centres <b>0.009 frame widths apart</b>. Every &ldquo;2.00 of 2 foes in frame&rdquo; receipt in this arc was true and hollow.</p>

<h2>1. The mechanism, and it is the same arithmetic as the party's</h2>
<p>At two foes the closed form puts both slots at <code>ax = foeX + 0.5&middot;foeChevron</code> and separates them only in
depth (<code>&plusmn;0.62&middot;foeSpread</code>). <code>decide</code> swings the boom 0.30 rad, so the line ends
<b>17.2&deg;</b> off the view axis and lateral separation is <b>0.422 m of a 1.428 m line</b> &mdash; against a duskpad
that projects <b>0.32 frame widths wide</b>. Two bodies 0.42 m apart across, one of them two metres long, are one body.</p>

<h2>2. The sweep &mdash; nine (rake, depth) pairs, 13 stratified sites, one build</h2>
<p class="dim"><code>rake</code> = the SIGNED across-axis rank as a multiple of the spread the depth rank uses; <code>depth</code> =
a multiplier on that depth rank. (0, 1) is the shipped closed form character for character. Worst foe per site.</p>
<table><tr><th>(rake, depth)</th><th>occTeam &ge;10/25/50</th><th>occTotal</th><th>bodies with no silhouette</th>
<th>foes in frame</th><th>&Delta;cx p50</th><th>lateral m p50</th><th>line vs axis</th><th>foe hFrac p50</th><th>camDist p50</th></tr>
${SW}
</table>
<p><b>The smallest change the evidence names does not fix it.</b> Literally deleting the <code>Math.abs</code> and keeping
<code>foeChevron</code>'s own 0.5 is arm (0.25, 1): 12/9/6 against the control's 12/11/9. 0.36 m of across-axis offset is not a
separation when the near body projects a third of the frame wide.</p>
<p><b>A flat rank wins the same way it won for the party, and for the same reason.</b> It is perpendicular to
<code>baseYaw</code>, so the swing leaves the line <b>72.8&deg;</b> off the view axis instead of 17.2&deg;, and
<b>it does not lengthen the line</b> &mdash; the across span is the spread the depth rank was already using, so every body moves
1.0 m and staging (a SEARCH over exactly this geometry) is perturbed no harder than the party fix perturbed it. Wider is not
better: at 1.4 the occlusion is already zero and the extra metres only buy a smaller foe (hFrac 0.284 &rarr; 0.261). The
opposite sign is no better and costs 0.7 m of boom.</p>

<h2>3. The census, three arms &times; 62 sites</h2>
<table><tr><th>arm</th><th>n</th><th>foe occTeam<br>&ge;10/25/50</th><th>foe occWorld</th><th>foe occTotal</th>
<th>party occTeam</th><th>party occWorld</th><th>party occTotal</th><th>no silhouette</th><th>foes in frame</th><th>axisOk</th>
<th>&Delta;cx p50</th><th>lateral m</th><th>line vs axis</th><th>foe hFrac</th><th>camDist</th><th>ring&nbsp;0</th><th>stage ms p50</th></tr>
${armRow(B, 'BEFORE &mdash; the closed form (rake 0, depth 1)')}
${armRow(Af, 'SHIPPED &mdash; a flat rank (rake 1, depth 0)')}
${armRow(E, '+ the second staging eye (<code>?beye2=1</code>, NOT shipped)')}
</table>
<p><b>The foe line: occTeam 52/44/28 &rarr; 2/0/0, occTotal 52/44/29 &rarr; 11/2/2, foes in frame 122/124 &rarr; 124/124,
bodies with no silhouette at all 4 &rarr; 0 (all four were ONE site, s015, where the before arm rendered no cast silhouette whatever), axisOk 62/62 in every arm.</b> The pair's screen centres go 0.009 &rarr; 0.165 frame
widths apart. It is close to free: foe height in frame 0.277 &rarr; 0.273 (&minus;1.4%), camera distance 11.98 &rarr; 11.16 m
(the frame gets <i>tighter</i>, because a line abreast is shallower than a line in depth), ring-0 staging unchanged at 13 sites,
staging solve p50 100 &rarr; 99 ms.</p>

<h2>4. Every regression, named</h2>
<ul>
<li><b>foe occTeam</b>: improved ${rFoeT.dn.length}, regressed ${rFoeT.up.length} &mdash; ${rFoeT.up.join('; ') || 'none'}</li>
<li><b>foe occWorld</b> (the trade: a body moved out from behind its neighbour can move behind the world): improved ${rFoeW.dn.length}, regressed ${rFoeW.up.length} &mdash; ${rFoeW.up.join('; ')}</li>
<li><b>foe occTotal</b> (what the player is actually left with): improved ${rFoeTot.dn.length}, regressed ${rFoeTot.up.length} &mdash; ${rFoeTot.up.join('; ')}</li>
<li><b>party occTeam</b>: improved ${rPT.dn.length}, regressed ${rPT.up.length} &mdash; ${rPT.up.join('; ')}</li>
<li><b>party occTotal</b>: improved ${rPTot.dn.length}, regressed ${rPTot.up.length} &mdash; ${rPTot.up.join('; ')}</li>
</ul>
<p>Seven sites changed staging ring (s002 R8&rarr;5, s004 R8&rarr;5, s007 R5&rarr;0, s026 R0&rarr;5, s036 R0&rarr;5,
s046 R5&rarr;0, s053 R5&rarr;8) &mdash; staging is a search over the slot geometry and this lane moved the geometry, so every
regression above is a relocation or a new world occluder, never a teammate. <b>s022</b> is not a new defect: its foe was already
0.89 lost to the world before the change. <b>s038</b> is the real one and it is looked at below.</p>

<h2>5. Looked at</h2>
<p>Frames are the shipped <code>decide</code> shot at the command step, cast idle phase pinned with <code>stage.qa.pose()</code>,
<code>ORBIT.yaw</code> pinned, ambient motes sat out &mdash; nothing between the two arms but the two numbers.</p>
${LOOK}
<p><b>Before, at s012 and s024 and s006, there is one animal on screen with a green wedge stuck to it</b> &mdash; it reads as part
of the wolf, a saddle or a shadow, not as a creature. After, there is a wolf in profile and a green blob beside it, and nobody
would describe that frame as containing one enemy. <b>s038 is the honest cost</b>: the fight is staged under a wooden deck, and
the across-axis move slid the wolf behind one of the deck's posts (occWorld 0.04 &rarr; 0.47). Even there the frame is more
legible as <i>two</i> creatures than the before frame was &mdash; but half a wolf is behind a post, and that is a real loss.</p>

<h2>6. The worst case for an across-axis rank: two bodies of the same width</h2>
<p>The census pair is a duskpad and a reed-nibbler &mdash; a two-metre wolf and a small blob. <code>duskpad, duskpad</code> is a
real shipped encounter (<code>encounters.json</code>, forest weight 3) and is the hardest case for any across offset, because both
bodies project the same width. 21 stratified sites, both arms, same build.</p>
${PB && PA ? `<table><tr><th>arm</th><th>n</th><th>foe occTeam &ge;10/25/50</th><th>foe occWorld</th><th>foe occTotal</th><th>no silhouette</th><th>foes in frame</th><th>axisOk</th><th>&Delta;cx p50</th><th>foe hFrac p50</th></tr>
<tr><td>BEFORE</td><td>${Object.keys(PB.sites).length}</td><td>${dist(PB, 'foeTeam')}</td><td>${dist(PB, 'foeWorld')}</td><td>${dist(PB, 'foeTotal')}</td><td>${Object.values(PB.sites).reduce((s, x) => s + x.noSil + x.noReg, 0)}</td><td>${Object.values(PB.sites).reduce((s, x) => s + (x.foesIn || 0), 0)}/${Object.values(PB.sites).reduce((s, x) => s + (x.foesAll || 0), 0)}</td><td>${Object.values(PB.sites).filter(x => x.axisOk !== false).length}/${Object.keys(PB.sites).length}</td><td>${med(Object.values(PB.sites).map(x => x.dcx))}</td><td>${med(Object.values(PB.sites).map(x => x.hFrac))}</td></tr>
<tr><td>AFTER</td><td>${Object.keys(PA.sites).length}</td><td>${dist(PA, 'foeTeam')}</td><td>${dist(PA, 'foeWorld')}</td><td>${dist(PA, 'foeTotal')}</td><td>${Object.values(PA.sites).reduce((s, x) => s + x.noSil + x.noReg, 0)}</td><td>${Object.values(PA.sites).reduce((s, x) => s + (x.foesIn || 0), 0)}/${Object.values(PA.sites).reduce((s, x) => s + (x.foesAll || 0), 0)}</td><td>${Object.values(PA.sites).filter(x => x.axisOk !== false).length}/${Object.keys(PA.sites).length}</td><td>${med(Object.values(PA.sites).map(x => x.dcx))}</td><td>${med(Object.values(PA.sites).map(x => x.hFrac))}</td></tr>
</table>
<h3>s009 &middot; forest &mdash; two duskpads</h3><div class="pair">
<figure><img loading="lazy" src="frames/pair-before/s009.jpg"><figcaption>BEFORE &mdash; occTeam ${PB.sites.s009.foeTeam.toFixed(2)}</figcaption></figure>
<figure><img loading="lazy" src="frames/pair-after/s009.jpg"><figcaption>AFTER &mdash; occTeam ${PA.sites.s009.foeTeam.toFixed(2)}</figcaption></figure></div>
<p><b>occTeam &ge;25% goes 13 of 21 to ZERO</b> and no foe is ever half-eaten by its twin; 7 sites keep a &ge;10% clip, which is
what two two-metre bodies 1.43 m apart do to each other's edges. <b>This is where the fix costs something real</b>: two wide
bodies abreast have to be framed wider, so foe height in frame falls 0.297 &rarr; 0.257 (&minus;13%) at this group, against
&minus;1.4% at the census pair. Bodies with no silhouette 4 &rarr; 0, foes in frame 41/42 &rarr; 42/42, axisOk 21/21.</p>
<p>Before, the two wolves are one animal with a doubled outline and a second head; after, they are two wolves.</p>` : '<p class="dim">(pending)</p>'}

<h2>7. The validation gap: built, measured, and default OFF</h2>
<p>The party lane named the cause of its own residual: <code>stageArena</code> validates every slot from the <b>round</b> eye and
<code>decide</code> swings 0.30 rad off it and pushes in. <code>decideEye()</code> in <code>battle_world.js</code> now
reproduces the part a ray cares about &mdash; the swing (read off the shot row and <code>partySide()</code>), the pitch offset,
and an aim weighted <code>keepBias</code> from the party slots toward the foe slots &mdash; and walks the SAME per-slot jitter
ring, preferring a jitter that clears both eyes and falling back to the round eye's own answer. By construction it cannot lose a
slot, refuse a site or relocate a fight, which is deliberate: relocation is the mechanism that produced every regression this lane
and the party lane have named.</p>
<p><b>It measures null and it is not free.</b> Against the shipped arm over the full census: <b>61 of 62 sites identical</b>,
foe occWorld unchanged at 7/2/1, party occWorld 15/2/0 &rarr; 14/2/0, and <b>the one site it moves is a regression</b>
(s049, party occTeam 0.05 &rarr; 0.22). Cost: staging solve p50 99 &rarr; 108 ms, p95 +66 ms, 8.70 &rarr; 9.99 s over the
census &mdash; <b>+14.9%</b>.</p>
<p><b>Why it is null is the part worth keeping.</b> The shot solver already has this refusal and has far more room to act on it:
<code>decide</code> carries <code>keepVis</code> and <code>showParty</code>, so every foe and every party body is already in
<code>subjVis()</code> at the <i>real</i> decide pose, and <code>solveShotSafe</code> walks three swings &times; three boom lifts
looking for one that clears them. A staging-time copy is a second bite at the same apple with a &plusmn;1.6-slot jitter instead of
a whole boom ladder &mdash; and where the world is genuinely in the way (s038, a fight under a deck) no jitter escapes the post,
so the fallback holds. The form that would have somewhere to go is a REFUSAL that relocates the site, and that is the trade this
arc has already paid for twice. The proxy is honest about itself: it sits a median <b>1.87 m</b> from the real decide eye
(p95 5.22, max 6.38). Kept, off, as the A/B that proves the above: <code>?beye2=1</code> / <code>--beye2=1</code>.</p>

<h2>8. What it costs</h2>
<table><tr><th></th><th>BEFORE (rake 0, depth 1)</th><th>SHIPPED (rake 1, depth 0)</th></tr>
<tr><td>staging solve p50 (62 sites)</td><td>100 ms</td><td>99 ms</td></tr>
<tr><td>staging solve, census total</td><td>8.80 s</td><td>8.70 s</td></tr>
<tr><td><code>decide</code> re-solve p50 (4 sites &times; 60 reps)</td><td>0.5 ms</td><td>0.5 ms</td></tr>
<tr><td>trigger &rarr; first frame p50 / max</td><td>575.5 / 614.8 ms</td><td>554.4 / 630.1 ms</td></tr>
<tr><td>round resolution (fixed scripted part)</td><td>7833.4 ms</td><td>7829.9 ms</td></tr>
<tr><td>camera refusals</td><td>0</td><td>0</td></tr>
<tr><td>foe height in frame p50</td><td>0.277</td><td>0.273</td></tr>
<tr><td>camera distance p50</td><td>11.98 m</td><td>11.16 m</td></tr>
<tr><td>ring-0 staging (&ldquo;fight where you stand&rdquo;)</td><td>13 / 62</td><td>13 / 62</td></tr>
</table>
<p>Nothing on the turn path moved: the slot geometry is read once, at <code>create()</code>, and the shot solver does the same
arithmetic on the same number of bodies either way.</p>

<h2>9. Per site</h2>
<table><tr><th>site</th><th>zone</th><th colspan=2>BEFORE</th><th colspan=3>AFTER</th><th colspan=2>&Delta;cx</th><th colspan=2>lateral m</th><th colspan=2>foe hFrac</th></tr>
<tr><th></th><th></th><th>occTeam</th><th>occTotal</th><th>occTeam</th><th>occWorld</th><th>occTotal</th><th>before</th><th>after</th><th>before</th><th>after</th><th>before</th><th>after</th></tr>
${per}
</table>
<p class="dim">Data: <code>overlap-{before,after,eye2,pair-before,pair-after}.json</code> and the nine
<code>overlap-sw-*.json</code> sweep arms in this directory. Frames: <code>frames/{before,after}/</code>.
Occlusion is an INTERSECTION of the solo silhouette and the visible-pixels mask, never a ratio of areas; every grab is
display-space sRGB off the WebGL canvas after play3d's own post chain.</p>
`;
writeFileSync(D + 'index.html', html);
console.log('wrote ' + D + 'index.html', html.length, 'bytes');

}
