#!/usr/bin/env node
// battle_camera.mjs — THE INSTRUMENT FOR THE SHOT LANGUAGE (BET B, world arena).
//
//   node tools/battle_camera.mjs --port=3000 --mode=sides       # stage.sides() partitions, both arenas
//   node tools/battle_camera.mjs --port=3000 --mode=shots       # the contact sheet, both arenas
//   node tools/battle_camera.mjs --port=3000 --mode=legibility  # the numbers, 4 sites, cam off vs on
//   node tools/battle_camera.mjs --port=3000 --mode=moves       # the KO push and the victory move
//   node tools/battle_camera.mjs --port=3000 --mode=assert      # the 180-degree rule, every shot
//   node tools/battle_camera.mjs --port=3000 --mode=fps         # the frame budget, after
//   node tools/battle_camera.mjs --port=3000 --mode=regress     # flag OFF = today's game
//
// WHY IT MEASURES LEGIBILITY THE WAY IT DOES. The BET A spike's honest verdict
// was that the world wins on picture and LOSES on legibility — "two clean
// silhouettes on a low-contrast painted field is a composition; the valley is
// rock, foliage, houses and cast shadows". That is an assertion about PIXELS, so
// it is measured in pixels, and the extraction is a subtraction rather than a
// guess: render the frame with a body, render it without, and the difference IS
// that body's silhouette — shadow, rim light, alpha and all. Render it again
// with the cast's depth test off and the difference is the silhouette it WOULD
// have had unoccluded, so occlusion is one division and never an opinion.
//
// Everything is read out of the running game through the stage's own `qa`
// accessors. Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir
// prefix; this tool never pattern-kills Chrome by name.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, findPage, killOrphans, sweepStaleProfiles } from './cdp.mjs';
// THE METER LIVES IN ONE FILE (2026-08-09). READY / PRELUDE / the legibility
// meter / SITES / sideReport moved to battle_meter.mjs unchanged so the
// separation lane's instrument measures with THIS one rather than a copy.
import { READY, PRELUDE, SITES, sideReport } from './battle_meter.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const MODE = arg('mode', 'shots');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-camera'));
const HEAD = argv.includes('--head');
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROFILE_PREFIX = 'battle-camera-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);

const flag = MODE === 'regress' ? '' : '&arena=world';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1${flag}`;

const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1',
  ...(MODE === 'fps' ? ['--disable-gpu-vsync', '--disable-frame-rate-limit'] : []),
  '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { killOrphans(profile); } catch (e) { }
};
process.on('exit', kill);
process.on('SIGINT', () => { kill(); process.exit(130); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 512 * 1024 * 1024 });
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
const png = (name, uri) => { if (uri) writeFileSync(join(OUT, name), Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64')); };

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 250, label: 'battle_camera' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  const consoleErrs = [];
  cdp.send('Log.enable').catch(() => { });
  const ready = await ev(cdp, READY, 120000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready  three r${ready.three}  scene=${ready.scene}  bw=${JSON.stringify(ready.bw)}  fov=${ready.fov}`);
  await ev(cdp, PRELUDE, 60000);

  // ------------------------------------------------------------------ shots
  // THE CONTACT SHEET. THREE COLUMNS, ONE BUILD, THE SAME BEATS, DRIVEN BY THE
  // STAGE'S OWN VERBS — never by the shot solver, so what is photographed is the
  // game rather than the instrument:
  //   dio = the shipped diorama (BattleWorld.enabled = false)
  //   off = the world arena on the spike's single solved pose (CAM.on = false)
  //   on  = the world arena with the shot language
  // ------------------------------------------------------------------ sides
  // THE ACCESSOR'S OWN RECEIPT, in BOTH arenas. `stage.sides()` is the value
  // newBody() was constructed with; the claim it has to support is that it
  // PARTITIONS the stage's roster — every body on exactly one side, none
  // missing, none invented. The build orders differ between the two stages
  // (the diorama stages foes first, battle_world the party first), which is
  // exactly what made the old id-pattern fallback safe by accident in one
  // column and wrong in the other, so both are printed with their orders.
  if (MODE === 'sides') {
    const S = SITES.find(s => s.name === arg('site', 'meadow')) || SITES[0];
    const out = { site: S.name, group: S.group, arenas: {} };
    let bad = 0;
    for (const [tag, opt] of [['diorama', 'false, world:false'], ['world', 'true, world:true']]) {
      const [c1, c2] = opt.split(', ');
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${c1}, ${c2}})`, 300000);
      if (!r.ok) { console.log(tag, 'FAILED', r.why); out.arenas[tag] = { ok: false, why: r.why }; bad++; continue; }
      const ids = Object.keys(r.tiers);
      console.log(`${tag}: build order ${JSON.stringify(ids)}`);
      let res = null;
      try { res = sideReport(tag, r); } catch (e) { console.error('  ' + e.message); bad++; }
      if (res) {
        // the id pattern, computed alongside, so the divergence is on the record
        const pat = ids.filter(i => /^m\d+$/.test(i));
        const same = pat.length === res.foes.length && pat.every(i => res.foes.indexOf(i) >= 0);
        console.log(`  /^m\\d+$/ would have said foes=[${pat}] — ${same ? 'same answer here' : 'DIFFERENT'}`);
        out.arenas[tag] = { ok: true, order: ids, via: res.via, party: res.party, foes: res.foes,
                            idPatternFoes: pat, idPatternAgrees: same };
      }
      await ev(cdp, `window.__BC.end()`, 60000);
    }
    console.log('\n' + JSON.stringify(out, null, 2));
    writeFileSync(join(OUT, 'sides.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(bad ? 3 : 0);
  }

  if (MODE === 'shots') {
    const site = arg('site', 'meadow');
    const S = SITES.find(s => s.name === site) || SITES[0];
    const meta = { site: S.name, at: S.at, group: S.group, fovBefore: ready.fov, runs: {} };
    const COLS = [['dio', 'false, world:false'], ['off', 'false, world:true'], ['on', 'true, world:true']];
    for (const [tag, opt] of COLS) {
      const [c1, c2] = opt.split(', ');
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${c1}, ${c2}})`, 300000);
      if (!r.ok) { console.log(tag, 'FAILED', r.why); meta.runs[tag] = r; continue; }
      const { foes, party } = sideReport(`${S.name}/${tag}`, r);
      // ONE CONTINUOUS BEAT SEQUENCE, photographed on the way past. Timings are
      // the shipped pacing's own (announce 300 / approach 260 / wind 300 /
      // damage 640 / ko 820 / winHold 900 / winCheer 620).
      const seq = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        const W = ms => new Promise(r => setTimeout(r, ms));
        const shots = {}, cams = {};
        const grab = (k) => { shots[k] = st.snapshot(); cams[k] = st.cam ? st.cam() : null; };
        grab('opening');
        st.setActor('${party[0]}'); st.setTarget('${foes[0]}');
        await W(900); grab('decide');
        st.act('${party[0]}', 'attack', '${foes[0]}', 560);
        await W(430); grab('strike');
        st.flinch('${foes[0]}');
        await W(130); grab('impact');
        await W(900);
        if (st.ko) st.ko('${foes[0]}'); else st.setDead('${foes[0]}', true);
        await W(1000); grab('ko');
        await W(1100); grab('koSettled');
        st.cheer();
        await W(820); grab('victory');
        return { shots, cams, world: !!st.world };
      })()`, 180000);
      for (const [k, uri] of Object.entries(seq.shots)) png(`shot-${tag}-${k}.png`, uri);
      const table = tag === 'on' || tag === 'off'
        ? await ev(cdp, `window.__BC.stage().shotTable ? window.__BC.stage().shotTable() : null`) : null;
      meta.runs[tag] = { start: r, world: seq.world, cams: seq.cams, table };
      console.log(`  ${tag}: world=${seq.world} shots=${Object.keys(seq.shots).length}`);
      await ev(cdp, `window.__BC.end()`, 60000);
      meta.runs[tag].fovAfterTeardown = await ev(cdp, `(typeof cam!=='undefined'&&cam)?cam.fov:null`);
    }
    writeFileSync(join(OUT, 'shots.json'), JSON.stringify(meta, null, 2));
    console.log('fov after teardown:', JSON.stringify(Object.entries(meta.runs).map(([k, v]) => [k, v.fovAfterTeardown])));
    cdp.close(); kill(); process.exit(0);
  }

  // ------------------------------------------------------------- legibility
  if (MODE === 'legibility') {
    const out = { sites: {}, when: new Date().toISOString() };
    for (const S of SITES) {
      out.sites[S.name] = {};
      for (const on of [false, true]) {
        const tag = on ? 'on' : 'off';
        process.stdout.write(`  ${S.name} cam=${tag} ... `);
        let r;
        try { r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${on}})`, 300000); }
        catch (e) { console.log('EXCEPTION', e.message); out.sites[S.name][tag] = { ok: false, why: e.message }; continue; }
        if (!r.ok) { console.log('refused:', r.why); out.sites[S.name][tag] = r; await ev(cdp, `window.__BC.end()`, 60000); continue; }
        const m = await ev(cdp, `(async () => {
          const st = window.__BC.stage();
          st.shotTo('round', {});
          await new Promise(r => setTimeout(r, 1500));
          const lg = window.__BC.legibility();
          return { lg: lg, shot: st.snapshot() };
        })()`, 180000);
        png(`leg-${S.name}-${tag}.png`, m.shot);
        const b = m.lg.bodies;
        const foes = b.filter(x => x.side === 'foe');
        const mean = (a, k) => a.length ? +(a.reduce((s, v) => s + (v[k] || 0), 0) / a.length).toFixed(2) : null;
        const summ = {
          edgeAll: mean(b, 'edgeRGB'), edgeFoe: mean(foes, 'edgeRGB'),
          edgeLumAll: mean(b, 'edge'),
          occlAll: mean(b, 'occl'), occlMax: b.length ? +Math.max(...b.map(x => x.occl || 0)).toFixed(3) : null,
          foeHPctMin: foes.length ? +Math.min(...foes.map(x => x.hPct)).toFixed(2) : null,
          foeHPctMean: mean(foes, 'hPct'),
          clutter: mean(b, 'clutter'),
          pose: m.lg.cam && m.lg.cam.pose, base: m.lg.cam && m.lg.cam.base,
          view: m.lg.cam && m.lg.cam.view, axis: m.lg.cam && m.lg.cam.axis,
        };
        out.sites[S.name][tag] = { ok: true, zone: r.zone, bodies: b, summary: summ, plan: r.plan && { yawDelta: r.plan.yawDelta, relief: r.plan.relief } };
        console.log(`edge=${summ.edgeAll} foeH=${summ.foeHPctMean}% occl=${summ.occlAll} clutter=${summ.clutter}`);
        await ev(cdp, `window.__BC.end()`, 60000);
      }
    }
    writeFileSync(join(OUT, 'legibility.json'), JSON.stringify(out, null, 2));
    // the roll-up, printed so a run is readable without opening the file
    console.log('\nsite      | edge off->on | foe h% off->on | occl off->on | clutter off->on');
    for (const [n, v] of Object.entries(out.sites)) {
      const a = v.off && v.off.summary, c = v.on && v.on.summary;
      if (!a || !c) { console.log(`${n.padEnd(9)} | INCOMPLETE`); continue; }
      console.log(`${n.padEnd(9)} | ${String(a.edgeAll).padStart(5)} -> ${String(c.edgeAll).padStart(5)} | ${String(a.foeHPctMean).padStart(5)} -> ${String(c.foeHPctMean).padStart(5)} | ${String(a.occlAll).padStart(5)} -> ${String(c.occlAll).padStart(5)} | ${String(a.clutter).padStart(5)} -> ${String(c.clutter).padStart(5)}`);
    }
    cdp.close(); kill(); process.exit(0);
  }

  // ------------------------------------------------------------------ moves
  if (MODE === 'moves') {
    const S = SITES.find(s => s.name === (arg('site', 'meadow'))) || SITES[0];
    const meta = { site: S.name, ko: {}, victory: {} };
    for (const on of [false, true]) {
      const tag = on ? 'on' : 'off';
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${on}})`, 300000);
      if (!r.ok) { meta.ko[tag] = { ok: false, why: r.why }; continue; }
      const { foes, party } = sideReport(`${S.name}/ko-${tag}`, r);
      // THE KO PUSH — sampled on the same clock the beat runs on
      const ko = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        st.setActor('${party[0]}'); st.setTarget('${foes[0]}');
        const samples = [], shots = {};
        const t0 = performance.now();
        st.ko('${foes[0]}');
        const marks = [80, 340, 700, 1000, 1500, 2100, 2800];
        let mi = 0;
        while (mi < marks.length) {
          await new Promise(r => setTimeout(r, 40));
          const t = performance.now() - t0;
          const c = st.cam();
          samples.push({ t: +t.toFixed(0), dist: c.pose ? c.pose.dist : null, fov: c.pose ? c.pose.fov : null, kind: c.kind });
          if (t >= marks[mi]) { shots['t' + marks[mi]] = st.snapshot(); mi++; }
        }
        return { samples, shots, cam: st.cam() };
      })()`, 180000);
      for (const [k, uri] of Object.entries(ko.shots || {})) png(`ko-${tag}-${k}.jpg`.replace('.jpg', '.png'), uri);
      delete ko.shots;
      const ds = ko.samples.map(s => s.dist).filter(v => v != null);
      ko.travel = ds.length ? +(Math.max(...ds) - Math.min(...ds)).toFixed(3) : null;
      meta.ko[tag] = ko;
      console.log(`  ko cam=${tag}: boom travel ${ko.travel} m over the hold`);
      // THE VICTORY MOVE
      const vic = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        const samples = [], shots = {};
        const t0 = performance.now();
        st.cheer();
        const marks = [60, 400, 800, 1200, 1600];
        let mi = 0;
        while (mi < marks.length) {
          await new Promise(r => setTimeout(r, 40));
          const t = performance.now() - t0;
          const c = st.cam();
          samples.push({ t: +t.toFixed(0), dist: c.pose ? c.pose.dist : null, yaw: c.pose ? c.pose.yaw : null, kind: c.kind });
          if (t >= marks[mi]) { shots['t' + marks[mi]] = st.snapshot(); mi++; }
        }
        return { samples, shots, cam: st.cam() };
      })()`, 180000);
      for (const [k, uri] of Object.entries(vic.shots || {})) png(`vic-${tag}-${k}.png`, uri);
      delete vic.shots;
      const ys = vic.samples.map(s => s.yaw).filter(v => v != null);
      const vd = vic.samples.map(s => s.dist).filter(v => v != null);
      vic.yawSwing = ys.length ? +(Math.max(...ys) - Math.min(...ys)).toFixed(3) : null;
      vic.travel = vd.length ? +(Math.max(...vd) - Math.min(...vd)).toFixed(3) : null;
      meta.victory[tag] = vic;
      console.log(`  victory cam=${tag}: yaw swing ${vic.yawSwing} rad, boom travel ${vic.travel} m`);
      await ev(cdp, `window.__BC.end()`, 60000);
    }
    writeFileSync(join(OUT, 'moves.json'), JSON.stringify(meta, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  // ----------------------------------------------------------------- assert
  // THE 180-DEGREE RULE, ON EVERY SHOT IN THE TABLE, AT EVERY SITE, AT EVERY
  // ENCOUNTER SHAPE THE STAGING SOLVE SUPPORTS. A rule that is only checked on
  // the shot you photographed is not a rule.
  if (MODE === 'assert') {
    const shapes = [['duskpad'], ['duskpad', 'duskpad'], ['duskpad', 'reed-nibbler', 'scree-shell']];
    const out = { rows: [], fail: 0, checked: 0 };
    for (const S of SITES) {
      for (const g of shapes) {
        const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(g)}, {cam:true})`, 300000);
        if (!r.ok) { out.rows.push({ site: S.name, n: g.length, ok: false, why: r.why }); continue; }
        const t = await ev(cdp, `(() => {
          const st = window.__BC.stage();
          const ids = st.qa.ids(), sides = st.sides();
          const party = ids.filter(i => sides[i] === 'party'), foes = ids.filter(i => sides[i] === 'foe');
          const rows = [];
          // every (actor, target) pairing the fight can produce, not just one
          for (const a of ids) for (const tg of ids) {
            if (sides[a] === sides[tg]) continue;
            st.setActor(a); st.setTarget(tg);
            for (const row of st.shotTable({ decide: { actor: a, target: tg }, strike: { actor: a, target: tg },
                                             impact: { actor: a, target: tg }, ko: { victim: tg } })) {
              rows.push({ actor: a, target: tg, kind: row.kind, ok: row.axis.ok, order: row.axis.order,
                          side: row.axis.side, gap: row.axis.gap, refused: row.refused, softened: row.softened });
            }
          }
          return { rows, cam: st.cam() };
        })()`, 180000);
        for (const row of t.rows) {
          out.checked++;
          if (!row.ok) out.fail++;
          out.rows.push(Object.assign({ site: S.name, n: g.length }, row));
        }
        console.log(`  ${S.name} ${g.length}v2: ${t.rows.length} shots, ${t.rows.filter(x => !x.ok).length} axis violations, ${t.rows.filter(x => x.refused).length} refused`);
        await ev(cdp, `window.__BC.end()`, 60000);
      }
    }
    out.softened = out.rows.filter(r => r.softened != null && r.softened < 1).length;
    out.refused = out.rows.filter(r => r.refused).length;
    writeFileSync(join(OUT, 'assert.json'), JSON.stringify(out, null, 2));
    console.log(`\n180-RULE: ${out.checked} shots solved, ${out.fail} violations, ${out.softened} softened, ${out.refused} refused`);
    cdp.close(); kill(); process.exit(out.fail ? 1 : 0);
  }

  // -------------------------------------------------------------------- fps
  if (MODE === 'fps') {
    const S = SITES[0];
    const out = {};
    for (const on of [false, true]) {
      const tag = on ? 'camOn' : 'camOff';
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${on}})`, 300000);
      if (!r.ok) { out[tag] = { ok: false, why: r.why }; continue; }
      out[tag] = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        // measure WHILE the camera is working, not while it is parked
        st.shotTo('strike', {});
        let n = 0, stop = false; const t0 = performance.now();
        const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
        requestAnimationFrame(tick);
        await new Promise(r => setTimeout(r, 4000));
        stop = true;
        const dt = (performance.now() - t0) / 1000;
        return { ok: true, fps: +(n / dt).toFixed(1), dt: +dt.toFixed(2),
                 canvases: document.querySelectorAll('canvas').length,
                 calls: R.info.render.calls, tris: R.info.render.triangles,
                 moves: st.cam().moves, refusals: st.cam().refusals };
      })()`, 180000);
      console.log(`  ${tag}: ${out[tag].fps} fps`);
      await ev(cdp, `window.__BC.end()`, 60000);
    }
    // and the field with no battle, for the same reason the spike measured it
    out.fieldIdle = await ev(cdp, `(async () => {
      let n = 0, stop = false; const t0 = performance.now();
      const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
      await new Promise(r => setTimeout(r, 4000)); stop = true;
      return { fps: +(n / ((performance.now() - t0) / 1000)).toFixed(1) };
    })()`, 60000);
    console.log('  fieldIdle:', out.fieldIdle.fps);
    writeFileSync(join(OUT, 'fps.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  // ---------------------------------------------------------------- regress
  // FLAG OFF MUST BE TODAY'S GAME. The page is opened with no ?arena=world, so
  // battle_world.js is the frozen inert object it ships as; the battle must come
  // up on the DIORAMA with two canvases and the field's own fov untouched.
  if (MODE === 'regress') {
    const bw = await ev(cdp, `JSON.parse(JSON.stringify(window.BattleWorld))`);
    const before = await ev(cdp, `({ fov: cam.fov, orbit: Object.assign({}, window.ORBIT), pos: SIM.pos(),
                                     canvases: document.querySelectorAll('canvas').length })`);
    const r = await ev(cdp, `(async () => {
      const GS = window.GS, RU = window.Rules;
      GS.setFlags({ 'maren-joined': true });
      const items = GS.data.items.items, growth = GS.data.growth;
      const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                     .map(c => RU.derive.partyMember(growth, items, c));
      const zone = SIM.zone() || 'meadow';
      const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
      const p = window.Battle.start({ zone, group: ['duskpad','duskpad'], seed: 4242, backdrop: zd && zd.battleBackdrop },
                                    party, { speed: 1 });
      p.then(()=>{},()=>{});
      const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
      for (let i = 0; i < 250 && !S(); i++) await new Promise(r => setTimeout(r, 100));
      const st = S(); if (!st) return { ok: false, why: 'no stage' };
      await new Promise(r => setTimeout(r, 2500));
      const out = { ok: true, world: !!st.world, hasCam: typeof st.cam === 'function',
                    canvases: document.querySelectorAll('canvas').length,
                    fov: cam.fov, orbit: Object.assign({}, window.ORBIT),
                    bodies: Object.keys(st.tiers()).length,
                    patched: !!(window.BattleStage3D && window.BattleStage3D.__bwPatched),
                    shot: st.snapshot ? st.snapshot() : null };
      try { st.destroy(); } catch (e) {}
      try { window.__EBB_SCREEN && window.__EBB_SCREEN.destroy(); } catch (e) {}
      document.querySelectorAll('.ebb-root').forEach(n => n.remove());
      window.__EBB_SCREEN = null; window.Battle.active = false;
      try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
      await new Promise(r => setTimeout(r, 500));
      out.after = { fov: cam.fov, orbit: Object.assign({}, window.ORBIT), pos: SIM.pos(),
                    canvases: document.querySelectorAll('canvas').length };
      return out;
    })()`, 300000);
    png('regress-diorama.png', r.shot); delete r.shot;
    const out = { battleWorld: bw, before, battle: r };
    console.log(JSON.stringify(out, null, 2));
    writeFileSync(join(OUT, 'regress.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})().catch((e) => { console.error('battle_camera error:', e); kill(); process.exit(2); });
