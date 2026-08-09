#!/usr/bin/env node
// battle_party.mjs — IS THE PARTY'S OWN ALBEDO RANGE WIDE ENOUGH TO SIT AGAINST
// THIS VALLEY.
//
//   node tools/battle_party.mjs --port=3000 --mode=census --tag=v1
//   node tools/battle_party.mjs --port=3000 --mode=census --party=vesper,maren,lake --tag=trio
//   node tools/battle_party.mjs --port=3000 --mode=noise --site=17 --reps=6
//   node tools/battle_party.mjs --mode=board
//
// THE QUESTION. Bet H (tools/monster_regrade.py) pulled the six creatures INTO the
// party's measured value/saturation band on the finding that the WOLF was in the
// game's register and the chibis were the outliers. That was a claim about CAST
// COHERENCE and it was right. Nobody had asked the other question: the party band
// was never compared against the terrain the party stands on. The rim spike then
// measured that the sites where a body fails to read are NOT fixed by any edge cue
// and that the failures concentrate on small clothed PARTY bodies — so the
// hypothesis under test here is that the party rigs share too much value and
// saturation with ow-valley itself.
//
// HOW IT MEASURES, and every clause is deliberate:
//  * ONE RULER. Everything pixel-side comes from tools/battle_meter.mjs's
//    `__BC.legibility`, the same object battle_camera / battle_sep / battle_rim
//    read, called with its additive `{hist:true}` option. Nothing is recomputed
//    here, so these numbers sit in the same column as every prior lane's.
//  * PER BODY, NEVER PER FRAME. The meter isolates each body by toggling ITS
//    visibility and re-rendering, so "the background behind vesper" is the ring
//    around HER mask and not a statistic of the whole picture.
//  * THE FRAME THE PLAYER LIVES IN. Staged exactly as battle_decide's census
//    stages it — same landing cells (docs/qa/battle-placement/sites{,-b}.json),
//    same party, same two foes, same seed, ORBIT.yaw pinned, same maturity ladder
//    — and photographed at the `decide` command step after its 620 ms move, with
//    nothing driving the camera.
//  * THE FRAME IS PINNED BEFORE IT IS PHOTOGRAPHED. `stage.qa.pose(true)` holds
//    the cast at its hashed idle phase and `Ambient.hide(true)` sits the motes
//    out, because the meter subtracts two renders and anything that moves between
//    them is measured as silhouette. Both are restored. KNOWN BOUND, inherited
//    from the rim spike: one battle staged once and metered six times moves
//    edgeRGB by 1.5 and ring luminance by 4.6, so --mode=noise exists and no
//    single-site claim here is made without it.
//
// SAY WHICH SPACE THE BYTES ARE IN. The meter reads the WebGL canvas after
// play3d's own post chain (RenderPass -> GTAO -> bloom -> OutputPass), so every
// histogram below is DISPLAY-SPACE sRGB. The albedo half of this study is
// tools/battle_party_albedo.py and it is in TEXTURE space; the two are related by
// the light, not by identity, and the board says so where it matters.
//
// This lane CHANGES NO SHIPPED ASSET. It stages, photographs and measures.
// Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir prefix.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, killOrphans, sweepStaleProfiles } from './cdp.mjs';
import { PRELUDE, READY } from './battle_meter.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const MODE = arg('mode', 'census');
const TAG = arg('tag', 'v1');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-party'));
const HEAD = argv.includes('--head');
const PARTY = arg('party', 'vesper,maren');
const REPS = parseInt(arg('reps', '6'), 10);
const SITE = arg('site', '17');
const YAW = arg('yaw', null);
const SHOTQ = parseFloat(arg('q', '0.8'));

mkdirSync(OUT, { recursive: true });

const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const PROFILE_PREFIX = 'battle-party-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1&arena=world`;

let chrome = null, closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { if (chrome) chrome.kill('SIGKILL'); } catch (e) { }
  try { killOrphans(profile); } catch (e) { }
};
process.on('exit', kill);
process.on('SIGINT', () => { kill(); process.exit(130); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((ok, no) => { const mid = ++id; pend.set(mid, { ok, no }); ws.send(JSON.stringify({ id: mid, method, params: params || {} })); });
      },
      close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); }
    });
  });
}
async function ev(cdp, expr, ms) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true, userGesture: true, timeout: ms || 300000 });
  if (r.exceptionDetails) {
    const e = r.exceptionDetails;
    throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text));
  }
  return r.result && r.result.value;
}

const INJECT = `(async () => {
  if (window.BattleWorld) return { already: true, on: window.BattleWorld.on };
  await new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = 'js/battle_world.js?v=' + Date.now();
    s.onload = res; s.onerror = () => rej(new Error('battle_world.js failed to load'));
    document.head.appendChild(s);
  });
  return { already: false, on: !!(window.BattleWorld && window.BattleWorld.on) };
})()`;

// ---------------------------------------------------------------------------
// ONE SITE. Staged the way battle_decide's census stages it, to the line, then
// PINNED and metered. The only additions are the pin and the histogram flag.
const driver = (site, yaw, party) => `(async () => {
  const S = ${JSON.stringify(site)};
  const WHO = ${JSON.stringify(party)};
  const GS = window.GS, B = window.Battle, RU = window.Rules;
  GS.setFlags({ 'maren-joined': true, 'lake-joined': true });
  const f = SIM.floors(S.at.x, S.at.z);
  if (!f.length) return { skip: 'no floor at the census cell' };
  SIM.tp(S.at.x, S.at.z, S.at.y); SIM.tick(3);
  const p0 = SIM.pos();
  const zone = SIM.zone(p0.x, p0.z) || S.zone;
  const yawWas = +window.ORBIT.yaw.toFixed(4);
  window.ORBIT.yaw = ${yaw};

  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => WHO.indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const t0 = performance.now();
  const pr = B.start({ zone: zone, group: ['duskpad','reed-nibbler'], seed: 4242,
                       backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  pr.then(()=>{}, ()=>{});
  let st = null;
  for (let i = 0; i < 300 && !(st = window.__BC.stage()); i++) await new Promise(r => setTimeout(r, 100));
  if (!st) return { skip: 'no stage' };
  if (!st.world) return { skip: 'not the world stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const t = st.tiers();
    if (Object.values(t).every(v => v !== 'proxy') && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
  for (let i = 0; i < 160; i++) { const tn = st.tone(); if (tn && (tn.ok || tn.why && !/waiting/.test(tn.why))) break; await new Promise(r => setTimeout(r, 100)); }
  await new Promise(r => setTimeout(r, 1100));
  const stageMs = performance.now() - t0;

  // the command step, waited for and never forced; then the decide move waited out
  const menuUp = () => { const c = document.querySelector('.ebb-cmds'); return !!c && !c.classList.contains('idle'); };
  const kindNow = () => { const c = st.cam ? st.cam() : null; return c ? c.kind : null; };
  for (let i = 0; i < 400 && !menuUp(); i++) await new Promise(r => setTimeout(r, 25));
  if (!menuUp()) return { skip: 'the command menu never opened' };
  for (let i = 0; i < 200 && kindNow() !== 'decide'; i++) await new Promise(r => setTimeout(r, 25));
  await new Promise(r => setTimeout(r, 900));

  // ---- PIN, PHOTOGRAPH, METER, UNPIN -------------------------------------
  // The meter subtracts two renders of the same frame. Anything that moves
  // between them lands in the mask, so the cast is held at its own hashed idle
  // phase and the motes are sat out — the two things the tone lane proved were
  // still moving. Both are restored below whatever happens.
  const posed = st.qa.pose ? st.qa.pose(true) : 0;
  const hadAmb = !!(window.Ambient && window.Ambient.hide);
  if (hadAmb) window.Ambient.hide(true);
  st.draw();
  const shot = (() => {
    st.snapshot();
    const src = st.canvas;
    const c = document.createElement('canvas');
    c.width = src.width; c.height = src.height;
    c.getContext('2d').drawImage(src, 0, 0);
    return c.toDataURL('image/jpeg', ${SHOTQ});
  })();
  let lg = null, err = null;
  try { lg = window.__BC.legibility({ hist: true }); } catch (e) { err = String(e && e.message || e); }
  if (hadAmb) window.Ambient.hide(false);
  if (st.qa.pose) st.qa.pose(false);

  const sides = st.sides ? st.sides() : {};
  const camr = st.cam ? st.cam() : null;
  const site = st.site || {};
  const plan = st.plan || {};
  const cast = st.castPhase ? st.castPhase() : null;

  try { st.destroy(); } catch (e) {}
  const sc = window.__EBB_SCREEN;
  if (sc && sc.destroy) { try { sc.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}

  return { ok: true, row: { id: S.id, zone: zone, at: p0, yawWas: yawWas,
      posed: posed, ambHidden: hadAmb, err: err,
      site: { R: site.R, d: site.d, ms: site.ms, quality: site.quality || null },
      relief: plan.relief, yawDelta: plan.yawDelta,
      kind: camr ? camr.kind : null, fov: camr ? camr.fov : null,
      pitch: camr && camr.base ? camr.base.pitch : null,
      sides: sides, tiers: st.tiers ? st.tiers() : null, cast: cast,
      stageMs: +stageMs.toFixed(0),
      bodies: lg ? lg.bodies : null, canvas: lg ? lg.canvas : null },
    shot: shot };
})()`;

// ---------------------------------------------------------------------------
// NODE-SIDE ARITHMETIC ON THE HISTOGRAMS. Quantiles and the OVERLAP COEFFICIENT
// (histogram intersection, sum of per-bin minima). Intersection is the right
// shape for the question: it is 1 when the body's paint and the terrain's paint
// occupy the same values entirely, and 0 when they share none.
function quant(h, p) {
  if (!h) return null;
  let a = 0;
  for (let i = 0; i < h.length; i++) { a += h[i]; if (a >= p) return +((i + 0.5) / h.length).toFixed(4); }
  return 1;
}
const inter = (a, b) => (!a || !b) ? null : +a.reduce((s, v, i) => s + Math.min(v, b[i]), 0).toFixed(4);

function bodyStats(b) {
  const H = b.hist; if (!H) return null;
  const q = (set, ch) => H[set] && H[set][ch] ? {
    p05: quant(H[set][ch], .05), p25: quant(H[set][ch], .25), p50: quant(H[set][ch], .5),
    p75: quant(H[set][ch], .75), p95: quant(H[set][ch], .95) } : null;
  const o = {
    id: b.id, side: b.side, silPx: b.silPx, hPct: b.hPct, occl: b.occl,
    edgeRGB: b.edgeRGB, edge: b.edge, clutter: b.clutter, bodyL: b.bodyL, ringL: b.ringL,
    bodyV: q('body', 'v'), bodyS: q('body', 's'),
    edgeV: q('edge', 'v'), edgeS: q('edge', 's'),
    ringV: q('ring', 'v'), ringS: q('ring', 's'),
    underV: q('under', 'v'), underS: q('under', 's'),
    rgb: { body: H.body && H.body.rgb, edge: H.edge && H.edge.rgb,
           ring: H.ring && H.ring.rgb, under: H.under && H.under.rgb },
  };
  o.ovl = {
    ringV: inter(H.body && H.body.v, H.ring && H.ring.v),
    ringS: inter(H.body && H.body.s, H.ring && H.ring.s),
    underV: inter(H.body && H.body.v, H.under && H.under.v),
    edgeRingV: inter(H.edge && H.edge.v, H.ring && H.ring.v),
    edgeRingS: inter(H.edge && H.edge.s, H.ring && H.ring.s),
  };
  // THE GAP, SIGNED. Where the body's own median value sits relative to the
  // terrain immediately around it. A body that reads has a big |dV50|; a body
  // painted at the terrain's own value has one near zero whatever its hue.
  o.dV50 = (o.bodyV && o.ringV) ? +(o.bodyV.p50 - o.ringV.p50).toFixed(4) : null;
  o.dS50 = (o.bodyS && o.ringS) ? +(o.bodyS.p50 - o.ringS.p50).toFixed(4) : null;
  // THE CANCELLATION TEST. `edgeRGB` is one signed difference of means over the
  // whole silhouette; `edgeRows` is the same difference taken in six horizontal
  // bands. Their ratio says how much of a body's contrast the global number
  // ANNIHILATES against itself — which is a property of the body's SHAPE, not of
  // its paint, and the two sides of this cast have opposite shapes.
  const rw = (H.rows || []).filter(Boolean);
  if (rw.length) {
    const mag = rw.map(x => x.rgb);
    o.rows = mag;
    o.rowsAbs = +(mag.reduce((s, v) => s + v, 0) / mag.length).toFixed(2);
    o.rowMin = +Math.min(...mag).toFixed(2);
    o.rowMax = +Math.max(...mag).toFixed(2);
    o.rowSignFlip = rw.some(x => x.dL > 2) && rw.some(x => x.dL < -2);
    o.cancel = b.edgeRGB > 0.01 ? +(o.rowsAbs / b.edgeRGB).toFixed(3) : null;
  }
  return o;
}

function slim(row) {
  const out = Object.assign({}, row);
  out.bodies = (row.bodies || []).map(bodyStats).filter(Boolean);
  // the raw histograms go to their own file; the summary stays readable
  out.hist = (row.bodies || []).reduce((o, b) => { if (b.hist) o[b.id] = b.hist; return o; }, {});
  delete out.cast;
  return out;
}

// ---------------------------------------------------------------------------
(async () => {
  if (MODE === 'board') { buildBoard(); process.exit(0); }

  chrome = spawn(CHROME, [
    `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--autoplay-policy=no-user-gesture-required',
    '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1600,900',
    ...(HEAD ? [] : ['--headless=new']), URL,
  ], { stdio: 'ignore' });

  let cdp = null;
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
      const list = await r.json();
      const pg = list.find(t => t.type === 'page' && /play3d\.html|play\.html/.test(t.url));
      if (pg && pg.webSocketDebuggerUrl) { cdp = await connect(pg.webSocketDebuggerUrl); break; }
    } catch (e) { }
    await sleep(500);
  }
  if (!cdp) { console.error('chrome never exposed the game page on CDP ' + CDP_PORT); kill(); process.exit(2); }
  await cdp.send('Runtime.enable');
  const ready = await ev(cdp, READY, 180000);
  if (!ready.ready) { console.error('page never became ready'); kill(); process.exit(2); }
  console.log(`ready three=r${ready.three} scene=${ready.scene}`);
  console.log('battle_world: ' + JSON.stringify(await ev(cdp, INJECT, 60000)));
  await ev(cdp, PRELUDE, 30000);
  const who = PARTY.split(',');
  const yaw = YAW != null ? parseFloat(YAW) : await ev(cdp, '(() => +window.ORBIT.yaw.toFixed(6))()', 10000);
  console.log(`ORBIT.yaw pinned at ${yaw}   party=[${who}]`);

  // THE CENSUS IS 60 + 2 — sites.json exhausted the 400 road cells and sites-b
  // added the two the rotated pass found. Reading only the first file turns a
  // census into a sample (battle_decide's own note).
  const census = JSON.parse(readFileSync(join(ROOT, 'docs/qa/battle-placement/sites.json'), 'utf8')).rows
    .concat(existsSync(join(ROOT, 'docs/qa/battle-placement/sites-b.json'))
      ? JSON.parse(readFileSync(join(ROOT, 'docs/qa/battle-placement/sites-b.json'), 'utf8')).rows : []);

  if (MODE === 'noise') {
    // THE METER'S OWN SPREAD, ON THIS PATH, WITH THE PIN ON. The rim spike
    // measured 1.5 edgeRGB and 4.6 ring luminance of run-to-run movement without
    // it; every per-site claim on this board is bounded by whatever this prints.
    const i = parseInt(SITE, 10);
    const s = { id: 's' + String(i).padStart(3, '0'), zone: census[i].zone, at: census[i].at };
    const dir = join(OUT, 'noise'); mkdirSync(dir, { recursive: true });
    const rows = [];
    for (let r = 0; r < REPS; r++) {
      process.stdout.write(`  rep${r} ${s.id} ... `);
      let out; try { out = await ev(cdp, driver(s, yaw, who), 300000); }
      catch (e) { console.log('THREW ' + e.message); continue; }
      if (!out || !out.ok) { console.log('skip: ' + (out && out.skip)); continue; }
      if (out.shot) writeFileSync(join(dir, `${s.id}-r${r}.jpg`), Buffer.from(out.shot.split(',')[1], 'base64'));
      const sl = slim(out.row); sl.rep = r; rows.push(sl);
      const p = sl.bodies.filter(b => b.side === 'party');
      console.log(p.map(b => `${b.id} edge=${b.edgeRGB} ringV50=${b.ringV && b.ringV.p50} ovlV=${b.ovl.ringV}`).join('  '));
      await sleep(300);
    }
    const f = join(OUT, `noise-${s.id}-${TAG}.json`);
    writeFileSync(f, JSON.stringify({ meta: { when: new Date().toISOString(), site: s, reps: REPS, yaw, party: who, three: ready.three }, rows }, null, 1));
    console.log('WROTE ' + f);
    // the spread, printed
    const ids = [...new Set(rows.flatMap(r => r.bodies.map(b => b.id)))];
    for (const id of ids) {
      const v = rows.map(r => r.bodies.find(b => b.id === id)).filter(Boolean);
      const stat = (k, f2) => { const a = v.map(f2).filter(x => x != null); if (!a.length) return `${k}=-`;
        return `${k}=${(a.reduce((s2, x) => s2 + x, 0) / a.length).toFixed(2)}±${(Math.max(...a) - Math.min(...a)).toFixed(2)}`; };
      console.log(`  ${id.padEnd(8)} ${stat('edgeRGB', b => b.edgeRGB)}  ${stat('ringL', b => b.ringL)}  ` +
                  `${stat('ringV50', b => b.ringV && b.ringV.p50)}  ${stat('ovlV', b => b.ovl.ringV)}  ${stat('dV50', b => b.dV50)}`);
    }
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'census') {
    const dir = join(OUT, 'census', TAG); mkdirSync(dir, { recursive: true });
    const from = parseInt(arg('start', '0'), 10);
    const lim = parseInt(arg('limit', String(census.length)), 10);
    const rows = [], t0 = Date.now();
    for (const c of census.slice(from, from + lim)) {
      const s = { id: c.id, zone: c.zone, at: c.at };
      process.stdout.write(`  ${s.id} (${s.zone}) ... `);
      let out; try { out = await ev(cdp, driver(s, yaw, who), 300000); }
      catch (e) { console.log('THREW ' + e.message); continue; }
      if (!out || !out.ok) { console.log('skip: ' + (out && out.skip)); continue; }
      if (out.shot) writeFileSync(join(dir, `${s.id}.jpg`), Buffer.from(out.shot.split(',')[1], 'base64'));
      const sl = slim(out.row); rows.push(sl);
      const p = sl.bodies.filter(b => b.side === 'party');
      console.log(p.map(b => `${b.id}: edge=${b.edgeRGB} dV=${b.dV50} ovl=${b.ovl.ringV}`).join(' | ') || 'NO PARTY BODIES');
      await sleep(200);
    }
    const meta = { when: new Date().toISOString(), tag: TAG, yaw, party: who, three: ready.three,
                   n: rows.length, secs: Math.round((Date.now() - t0) / 1000) };
    writeFileSync(join(OUT, `census-${TAG}.json`), JSON.stringify({ meta, rows: rows.map(r => { const x = Object.assign({}, r); delete x.hist; return x; }) }, null, 1));
    writeFileSync(join(OUT, `hist-${TAG}.json`), JSON.stringify({ meta, hist: rows.map(r => ({ id: r.id, zone: r.zone, hist: r.hist })) }));
    console.log(`WROTE census-${TAG}.json (${rows.length} sites, ${meta.secs}s)  frames -> ${dir}`);
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})().catch(e => { console.error(e); kill(); process.exit(1); });

function buildBoard() { console.log('board is written by tools/battle_party_board.mjs'); }
