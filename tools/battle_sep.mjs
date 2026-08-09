#!/usr/bin/env node
// battle_sep.mjs — TONAL SEPARATION: DOES THE CAST READ AGAINST REAL TERRAIN.
//
//   node tools/battle_sep.mjs --port=3000 --mode=pitch   # what the BOOM axis is worth, per site
//   node tools/battle_sep.mjs --port=3000 --mode=ab      # control vs treatment, 4 sites
//   node tools/battle_sep.mjs --port=3000 --mode=sweep   # the treatment's own strength ladder
//   node tools/battle_sep.mjs --port=3000 --mode=shots   # the beats, for the EYE
//   node tools/battle_sep.mjs --port=3000 --mode=fps     # the frame budget, after
//
// WHY IT EXISTS. The camera lane's own verdict: the shot language owns SIZE and
// OCCLUSION and DOES NOT OWN TONAL SEPARATION — worst-case foe height improved at
// every site while RGB silhouette contrast FELL where a tighter frame happened to
// back the cast with mid-value terrain. That is a claim about pixels, so it is
// measured in pixels, with the SAME meter battle_camera uses (battle_meter.mjs —
// imported, never copied: a meter that is pasted is two meters that drift).
//
// THE THREE METER RULES THIS REPO HAS ALREADY PAID FOR, inherited whole:
//   * a silhouette is a SUBTRACTION (frame with the body minus frame without it),
//   * occlusion is an INTERSECTION with the depth-test-off silhouette, never a
//     ratio of areas (a fully visible body once measured "-136% occluded"),
//   * contrast is RGB, never luminance (cutin_edge: a rim of the wrong HUE at the
//     right brightness is invisible to a luminance metric — and it shipped on 79
//     of 112 plates that way).
//
// Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir prefix; this
// tool never pattern-kills Chrome by name.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, findPage, killOrphans, sweepStaleProfiles } from './cdp.mjs';
import { READY, PRELUDE, SITES, sideReport } from './battle_meter.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const MODE = arg('mode', 'ab');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-separation'));
const HEAD = argv.includes('--head');
const ONLY = arg('sites', '');
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const PROFILE_PREFIX = 'battle-sep-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1&arena=world`;

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
const sites = () => ONLY ? SITES.filter(s => ONLY.split(',').indexOf(s.name) >= 0) : SITES;

// THE ROLL-UP every mode prints. One row per arm, so a regression is visible in
// the terminal and not only in the json.
const mean = (a, k) => a.length ? +(a.reduce((s, v) => s + (v[k] || 0), 0) / a.length).toFixed(2) : null;
function summarise(lg) {
  const b = lg.bodies, foes = b.filter(x => x.side === 'foe'), party = b.filter(x => x.side === 'party');
  return {
    edgeAll: mean(b, 'edgeRGB'), edgeFoe: mean(foes, 'edgeRGB'), edgeParty: mean(party, 'edgeRGB'),
    // THE WORST BODY IS THE ONE THAT FAILS TO READ. A mean that hides one
    // invisible body is the same defect BET G's staging solve was fixed for.
    edgeMin: b.length ? +Math.min(...b.map(x => x.edgeRGB || 0)).toFixed(2) : null,
    edgeLumAll: mean(b, 'edge'),
    occlAll: mean(b, 'occl'), occlMax: b.length ? +Math.max(...b.map(x => x.occl || 0)).toFixed(3) : null,
    foeHPctMin: foes.length ? +Math.min(...foes.map(x => x.hPct)).toFixed(2) : null,
    foeHPctMean: mean(foes, 'hPct'),
    clutter: mean(b, 'clutter'),
    // THE SEPARATION RATIO. Contrast alone is not legibility: a body 20 units
    // from its background on a field whose own variance is 46 does not read.
    // This is the number the spike's verdict is actually about.
    snr: (() => { const c = mean(b, 'clutter'), e = mean(b, 'edgeRGB'); return c ? +(e / c).toFixed(3) : null; })(),
    bodyL: mean(b, 'bodyL'), ringL: mean(b, 'ringL'),
    pose: lg.cam && lg.cam.pose, view: lg.cam && lg.cam.view,
  };
}
const ROWH = 'site     arm            edgeRGB  edgeFoe  edgeMin  clutter    snr   foeH%   occl  pitch';
function row(site, arm, s) {
  const p = s.pose ? s.pose.pitch : null;
  return [site.padEnd(8), String(arm).padEnd(13),
    String(s.edgeAll).padStart(8), String(s.edgeFoe).padStart(8), String(s.edgeMin).padStart(8),
    String(s.clutter).padStart(8), String(s.snr).padStart(6), String(s.foeHPctMean).padStart(7),
    String(s.occlAll).padStart(6), String(p == null ? '-' : p).padStart(6)].join(' ');
}

// ONE ARM: set the page up however the arm says, stage the fight, hold the round
// shot, MEASURE, tear down. `pre` is arbitrary page script so an arm can be a
// config change with no new plumbing; it is echoed into the json so a row can
// never be mystery-provenance.
async function arm(cdp, S, tag, pre, opts) {
  opts = opts || {};
  process.stdout.write(`  ${S.name}/${tag} ... `);
  if (pre) await ev(cdp, pre, 30000);
  let r;
  try { r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${opts.cam === false ? 'false' : 'true'}})`, 300000); }
  catch (e) { console.log('EXCEPTION', e.message); return { ok: false, why: e.message, pre }; }
  if (!r.ok) { console.log('refused:', r.why); await ev(cdp, 'window.__BC.end()', 60000); return { ok: false, why: r.why, pre }; }
  const m = await ev(cdp, `(async () => {
    const st = window.__BC.stage();
    st.shotTo('round', {});
    await new Promise(r => setTimeout(r, 1500));
    const lg = window.__BC.legibility();
    const tone = (window.BattleWorld && window.BattleWorld.tone) ? window.BattleWorld.tone() : null;
    return { lg: lg, shot: st.snapshot(), tone: tone,
             pfx: window.__postfx ? { grade: !!window.__postfx.grade, ao: !!window.__postfx.ao } : null };
  })()`, 180000);
  const s = summarise(m.lg);
  console.log(`edge=${s.edgeAll} min=${s.edgeMin} clutter=${s.clutter} snr=${s.snr}`);
  if (opts.shot !== false) png(`${opts.prefix || 'arm'}-${S.name}-${tag}.png`, m.shot);
  await ev(cdp, 'window.__BC.end()', 60000);
  return { ok: true, pre, summary: s, bodies: m.lg.bodies, tone: m.tone, pfx: m.pfx,
           plan: r.plan && { yawDelta: r.plan.yawDelta, relief: r.plan.relief } };
}

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 250, label: 'battle_sep' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  const ready = await ev(cdp, READY, 120000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready  three r${ready.three}  scene=${ready.scene}  bw=${JSON.stringify(ready.bw)}`);
  await ev(cdp, PRELUDE, 60000);
  // THE TREATMENT ONLY EXISTS WHERE THE PASS DOES, and that is STATED rather than
  // hidden: the aerial ramp is built only when GTAO is on and the camera is the
  // overworld's (play3d, pfxBuild). A run whose page has no grade pass measures
  // the control twice and must say so.
  const pfx = await ev(cdp, `window.__postfx ? {grade: !!window.__postfx.grade, ao: !!window.__postfx.ao, family: window.__postfx.family} : null`);
  console.log('postfx:', JSON.stringify(pfx));

  const out = { mode: MODE, when: new Date().toISOString(), pfx, sites: {} };

  // ------------------------------------------------------------------- pitch
  // WHAT THE BOOM AXIS IS WORTH, TONALLY. The shot solver ranks the four
  // candidate elevations on VISIBILITY plus clear BACK-DEPTH — a geometric proxy
  // for "the body has sky behind it". This mode prices that proxy against the
  // thing it is a proxy FOR, by pinning the candidate list to one rung at a time.
  if (MODE === 'pitch') {
    const PITCHES = [0.16, 0.22, 0.27, 0.28, 0.34];
    console.log('\n' + ROWH);
    for (const S of sites()) {
      out.sites[S.name] = {};
      for (const p of PITCHES) {
        const r = await arm(cdp, S, 'p' + p, `window.BattleWorld.CAM.solve.pitches = [${p}]; true`, { prefix: 'pitch' });
        out.sites[S.name]['p' + p] = r;
        if (r.ok) console.log(row(S.name, 'pitch ' + p, r.summary));
      }
    }
    writeFileSync(join(OUT, 'pitch.json'), JSON.stringify(out, null, 2));
    console.log('\n' + ROWH);
    for (const [n, v] of Object.entries(out.sites)) for (const [k, r] of Object.entries(v)) if (r.ok) console.log(row(n, k, r.summary));
    cdp.close(); kill(); process.exit(0);
  }

  // ---------------------------------------------------------------------- ab
  // CONTROL VS TREATMENT, on ONE build and one page, so the only thing that
  // differs between the two rows is the flag.
  if (MODE === 'ab') {
    const ARMS = [
      ['off', 'window.BattleWorld.TONE.on = false; true'],
      ['on', 'window.BattleWorld.TONE.on = true; true'],
    ];
    console.log('\n' + ROWH);
    for (const S of sites()) {
      out.sites[S.name] = {};
      for (const [tag, pre] of ARMS) {
        const r = await arm(cdp, S, tag, pre, { prefix: 'ab' });
        out.sites[S.name][tag] = r;
        if (r.ok) console.log(row(S.name, tag, r.summary));
      }
    }
    writeFileSync(join(OUT, 'ab.json'), JSON.stringify(out, null, 2));
    console.log('\nsite     | edgeRGB off->on | edgeMin off->on | clutter off->on |  snr off->on');
    for (const [n, v] of Object.entries(out.sites)) {
      const a = v.off && v.off.summary, c = v.on && v.on.summary;
      if (!a || !c) { console.log(`${n.padEnd(8)} | INCOMPLETE`); continue; }
      const d = (x, y) => `${String(x).padStart(6)} ->${String(y).padStart(6)}`;
      console.log(`${n.padEnd(8)} | ${d(a.edgeAll, c.edgeAll)}  | ${d(a.edgeMin, c.edgeMin)}  | ${d(a.clutter, c.clutter)}  | ${d(a.snr, c.snr)}`);
    }
    cdp.close(); kill(); process.exit(0);
  }

  // ------------------------------------------------------------------- sweep
  // THE STRENGTH LADDER. The treatment has ONE tuned number and it is swept here
  // rather than asserted, with the shipped overworld value as rung zero.
  if (MODE === 'sweep') {
    const RUNGS = (arg('rungs', 'off,0,0.35,0.7')).split(',');
    console.log('\n' + ROWH);
    for (const S of sites()) {
      out.sites[S.name] = {};
      for (const g of RUNGS) {
        const pre = g === 'off' ? 'window.BattleWorld.TONE.on = false; true'
          : `window.BattleWorld.TONE.on = true; window.BattleWorld.TONE.wClutter = ${g}; true`;
        const r = await arm(cdp, S, 'w' + g, pre, { prefix: 'sweep' });
        out.sites[S.name]['w' + g] = r;
        if (r.ok) console.log(row(S.name, 'wClutter ' + g, r.summary));
      }
    }
    writeFileSync(join(OUT, 'sweep.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  // ------------------------------------------------------------------- shots
  // THE EYE'S OWN EVIDENCE. Same beats, same sites, treatment off and on, driven
  // by the STAGE'S OWN VERBS so what is photographed is the game.
  if (MODE === 'shots') {
    const meta = { when: out.when, pfx, runs: {} };
    for (const S of sites()) {
      meta.runs[S.name] = {};
      for (const tag of ['off', 'on']) {
        await ev(cdp, `window.BattleWorld.TONE.on = ${tag === 'on'}; true`, 30000);
        const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:true})`, 300000);
        if (!r.ok) { console.log(S.name, tag, 'FAILED', r.why); meta.runs[S.name][tag] = { ok: false, why: r.why }; continue; }
        const { foes, party } = sideReport(`${S.name}/${tag}`, r);
        const seq = await ev(cdp, `(async () => {
          const st = window.__BC.stage();
          const W = ms => new Promise(r => setTimeout(r, ms));
          const shots = {};
          const grab = (k) => { shots[k] = st.snapshot(); };
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
          st.cheer();
          await W(820); grab('victory');
          return { shots, tone: window.BattleWorld.tone ? window.BattleWorld.tone() : null };
        })()`, 180000);
        for (const [k, uri] of Object.entries(seq.shots)) png(`shot-${S.name}-${tag}-${k}.png`, uri);
        meta.runs[S.name][tag] = { ok: true, tone: seq.tone, site: r.plan && { yawDelta: r.plan.yawDelta } };
        console.log(`  ${S.name}/${tag}: ${Object.keys(seq.shots).length} beats`);
        await ev(cdp, 'window.__BC.end()', 60000);
      }
    }
    writeFileSync(join(OUT, 'shots.json'), JSON.stringify(meta, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  // --------------------------------------------------------------------- fps
  // THE WORLD ARENA MEASURED FASTER THAN THE DIORAMA (243.5 vs 184.7) and that
  // lead is not to be spent carelessly. Both arms on one page, the same site.
  if (MODE === 'fps') {
    const S = sites()[0];
    const res = {};
    for (const tag of ['off', 'on']) {
      await ev(cdp, `window.BattleWorld.TONE.on = ${tag === 'on'}; true`, 30000);
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:true})`, 300000);
      if (!r.ok) { res[tag] = { ok: false, why: r.why }; continue; }
      // COUNTED THE WAY battle_camera COUNTS IT — rAF ticks, not
      // renderer.info.render.frame, which the composer increments once PER PASS
      // and which therefore reads about eight times too fast. Two instruments
      // quoting different definitions of "fps" at the same board is how a lead
      // gets spent without anyone noticing.
      const f = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        st.shotTo('strike', {});
        await new Promise(r => setTimeout(r, 1200));
        let n = 0, stop = false; const t0 = performance.now();
        const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
        requestAnimationFrame(tick);
        await new Promise(r => setTimeout(r, 5000));
        stop = true;
        const dt = (performance.now() - t0) / 1000;
        return { frames: n, ms: +(dt * 1000).toFixed(0), fps: +(n / dt).toFixed(1),
                 calls: R.info.render.calls, tris: R.info.render.triangles,
                 tone: window.BattleWorld.tone ? window.BattleWorld.tone() : null };
      })()`, 60000);
      res[tag] = f;
      console.log(`  ${tag}: ${f.fps} fps over ${f.frames} frames`);
      await ev(cdp, 'window.__BC.end()', 60000);
    }
    writeFileSync(join(OUT, 'fps.json'), JSON.stringify({ site: S.name, when: out.when, pfx, arms: res }, null, 2));
    const d = res.off && res.on && res.off.fps && res.on.fps ? +(100 * (res.on.fps - res.off.fps) / res.off.fps).toFixed(2) : null;
    console.log(`delta: ${d}%`);
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})().catch(e => { console.error(e); kill(); process.exit(1); });
