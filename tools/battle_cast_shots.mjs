#!/usr/bin/env node
// battle_cast_shots.mjs — PHOTOGRAPH THE BEATS THE CAST NEVER HAD.
//
//   node tools/battle_cast_shots.mjs --port=3000 --out=docs/qa/battle-cast
//   node tools/battle_cast_shots.mjs --only=cheer --head
//
// WHY THIS EXISTS AND battle_shots.mjs DOES NOT COVER IT. battle_shots photographs
// the four zones, the impact pair and the fallback tiers — the arena's LOOK. This
// lane's claims are about MOTION over time: a victory pose, a body drinking, a body
// running away and coming back, and a weapon that is in a hand while the arm swings.
// None of those is one frame, and three of them did not exist to photograph before
// 2026-08-08 (docs/plans/battle-presentation-inventory.md §6: cheer and item bound
// no clip on any body in the game, and flee was `return`).
//
// EVERY FRAME COMES FROM stage.snapshot() — a SYNCHRONOUS render through the
// shipping renderFrame(), so a 200 ms beat cannot be missed by screenshot timing and
// a photograph is never of a different pipeline from the one the player sees. The
// whole-frame Page.captureScreenshot is taken too, for the beats where the UI is
// part of the claim (the victory tally over the cheering party).
//
// AN INSTRUMENT THAT PHOTOGRAPHS MUST PROVE THE CANVAS WAS LIVE: `frames` is read
// off the live stage before and after every shot and reported; under 30 gained is
// flagged, not silently written out as a picture.
//
// Chrome goes through tools/cdp.mjs (freePort/findPage) and is reaped by its own
// --user-data-dir prefix on exit. Never pattern-kill Chrome by name.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, findPage } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const TAG = arg('tag', 'cast');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-cast'));
const ONLY = arg('only', null);
const HEAD = argv.includes('--head');
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- THE SHOT LIST --------------------------------------------------------
// `equip` runs before the battle so the socket has something to hold; `beat` is
// the page-side driver, and every entry in `shots` it returns is written out as
// <tag>-<name>-<key>.png.
const PARTY = ['vesper', 'maren'];
const SHOTS = [
  // 1. THE WEAPON SOCKET. The same swing, twice, with the only difference being
  //    what is in her hand — which is the whole claim of the socket.
  { name: 'armed', zone: 'meadow', group: ['duskpad', 'duskpad'], party: PARTY,
    equip: { vesper: 'river-cudgel', maren: 'walking-staff' }, beat: 'swing', full: true },
  { name: 'unarmed', zone: 'meadow', group: ['duskpad', 'duskpad'], party: PARTY, beat: 'swing' },
  { name: 'hook', zone: 'water', group: ['weir-eel'], party: PARTY,
    equip: { vesper: 'boat-hook' }, beat: 'swing' },
  // 2. AN ITEM IS DRUNK. Was: a body standing perfectly still while a green number
  //    appeared (audit §6).
  { name: 'item', zone: 'meadow', group: ['reed-nibbler'], party: PARTY,
    equip: { vesper: 'walking-staff' }, beat: 'item', full: true },
  // 3. FLEEING. Both answers, because they are two different pictures.
  { name: 'flee-away', zone: 'forest', group: ['duskpad', 'bramble-shade'], party: PARTY, beat: 'fleeAway' },
  { name: 'flee-cornered', zone: 'forest', group: ['duskpad', 'bramble-shade'], party: PARTY, beat: 'fleeBack' },
  // 4. THE VICTORY POSE. Was: the whole party standing in their idles.
  { name: 'cheer', zone: 'meadow', group: ['reed-nibbler', 'reed-nibbler'], party: PARTY,
    equip: { vesper: 'river-cudgel' }, beat: 'cheer', full: true },
  // 5. AND THE SAME BEAT ARRIVING THE WAY A PLAYER GETS IT: a whole battle, played
  //    out by the autoplay seat, photographed on the frame the victory tally lands.
  //    The shot above drives stage.cheer() directly, which proves the STAGE; this one
  //    proves the PATH — battle_turnbased calls it, once, on a win.
  { name: 'victory', zone: 'meadow', group: ['reed-nibbler'], party: PARTY,
    equip: { vesper: 'river-cudgel', maren: 'walking-staff' }, beat: 'win', full: true, autoplay: true },
];

const profile = join(process.env.TMPDIR || '/tmp', 'battle-cast-shots-' + process.pid);
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1',
  '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (!closing) { closing = true; try { chrome.kill('SIGKILL'); } catch (e) { } } };
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

async function evalPage(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true, userGesture: true,
    timeout: timeoutMs || 300000,
  });
  if (r.exceptionDetails) {
    const e = r.exceptionDetails;
    throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text));
  }
  return r.result && r.result.value;
}

// AN ID IS NOT A SIDE. `/^m/` matches `maren`; even the narrower `/^m\d+$/` used
// here is a guess about somebody else's id scheme, so ask the stage instead
// (stage.sides() on battle_world, stage.at().side on battle_stage3d) and keep the
// pattern only as a labelled last resort. The `cheer` beat KOs EVERY foe, so a
// side test that is wrong there kills the party. See tools/battle_shots.mjs.
const FOES_JS = `
    let _sideVia = 'id-pattern-fallback';
    const _sideOf = (id) => {
      if (typeof st.sides === 'function') { const s = st.sides(); if (s && s[id]) { _sideVia = 'stage.sides()'; return s[id]; } }
      if (typeof st.at === 'function') { const a = st.at(id); if (a && a.side) { _sideVia = 'stage.at().side'; return a.side; } }
      return /^m[0-9]+$/.test(id) ? 'foe' : 'party';
    };
    const _ids = Object.keys(st.tiers());
    const foes = _ids.filter(k => _sideOf(k) === 'foe');
    const _party = _ids.filter(k => _sideOf(k) === 'party');
    const sideResolution = { via: _sideVia, party: _party, foes: foes };
    if (!foes.length) throw new Error('no foe-side body on the stage');
    if (foes.indexOf('vesper') >= 0 || foes.some(f => _sideOf(f) !== 'foe')) throw new Error('side resolution returned a party member');
    if (_party.length + foes.length !== _ids.length) throw new Error('side map does not partition the body set: ' + JSON.stringify(sideResolution));
`;

// THE BEATS, page-side. Each one drives the stage's OWN public verbs — the same
// ones battle_turnbased calls — and snapshots on a timeline measured in ms from the
// call, so the same picture comes back on every run.
const BEATS = {
  swing: FOES_JS + `
    st.setTarget(foes[0]); st.setActor('vesper');
    shots.rest = st.snapshot();
    st.act('vesper', 'attack', foes[0], 560);
    await hold(300); shots.wind = st.snapshot();
    await hold(180); shots.swing = st.snapshot();
    await hold(140); st.flinch(foes[0]); await hold(90); shots.impact = st.snapshot();`,
  item: `
    st.setActor('vesper');
    st.act('vesper', 'item');
    await hold(220); shots.raise = st.snapshot();
    await hold(240); shots.drink = st.snapshot();
    await hold(320); shots.settle = st.snapshot();`,
  fleeAway: `
    st.setActor('vesper');
    st.act('vesper', 'flee');
    await hold(240); shots.turn = st.snapshot();
    await hold(300); shots.run = st.snapshot();
    st.flee('vesper', true);
    await hold(420); shots.gone = st.snapshot();`,
  fleeBack: `
    st.setActor('vesper');
    st.act('vesper', 'flee');
    await hold(420); shots.run = st.snapshot();
    st.flee('vesper', false);
    await hold(260); shots.turning = st.snapshot();
    await hold(340); shots.cornered = st.snapshot();`,
  win: `
    // the autoplay seat is already swinging; wait for the outro box, then shoot the
    // beat the tally arrives on
    for (let i = 0; i < 400; i++) {
      if (document.querySelector('.ebb-obox')) break;
      await hold(100);
    }
    await hold(320); shots.tally = st.snapshot();
    await hold(300); shots.tally2 = st.snapshot();`,
  cheer: FOES_JS + `
    for (const f of foes) st.ko(f);
    await hold(900);
    st.cheer();
    await hold(260); shots.hop = st.snapshot();
    await hold(240); shots.pose = st.snapshot();
    await hold(400); shots.late = st.snapshot();`,
};

const drive = (s) => `(async () => {
  const GS = window.GS, B = window.Battle, R = window.Rules;
  const D = window.BattleStage3D && window.BattleStage3D.disable;
  if (D) for (const k in D) D[k] = false;
  const flags = {}; ${JSON.stringify(s.party)}.forEach(id => { if (id === 'maren') flags['maren-joined'] = true; if (id === 'lake') flags['lake-joined'] = true; });
  if (Object.keys(flags).length) GS.setFlags(flags);
  // EQUIP FOR REAL, through GS's own verb (the item has to be in the bag first —
  // GS.equip refuses an item nobody owns, which is the world's rule, not ours).
  const want = ${JSON.stringify(s.equip || {})};
  const equipped = {};
  // UNEQUIP FIRST. GS persists across shots on one page, so the "unarmed" control
  // came back armed on round 1 — a control that is not a control.
  for (const ch of GS.activeParty()) if (ch.equip && ch.equip.weapon) GS.equip(ch.id, null, 'weapon');
  for (const who in want) { GS.addItem(want[who]); GS.equip(who, want[who]); }
  for (const ch of GS.activeParty()) equipped[ch.id] = (ch.equip && ch.equip.weapon) || null;
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty()
    .filter(ch => ${JSON.stringify(s.party)}.indexOf(ch.id) >= 0)
    .map(ch => R.derive.partyMember(growth, items, ch));
  const zd = GS.data.encounters.zones[${JSON.stringify(s.zone)}];
  const p = B.start({ zone: ${JSON.stringify(s.zone)}, group: ${JSON.stringify(s.group)}, seed: 4242,
                      backdrop: zd && zd.battleBackdrop }, party,
                    { speed: 1, autoplay: ${s.autoplay ? 'true' : 'false'} });
  p.then(()=>{}, ()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 200 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { ok: false, why: 'no stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const settled = Object.values(st.tiers()).every(v => v !== 'proxy');
    if (settled && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
  const hold = (ms) => new Promise(r => setTimeout(r, ms));
  const shots = {};
  const clips = {}; for (const id of Object.keys(st.tiers())) clips[id] = st.clipsOf(id);
  const held = {}; for (const id of Object.keys(st.tiers())) held[id] = st.weaponOf ? st.weaponOf(id) : 'no-accessor';
  ${BEATS[s.beat] || ''}
  const f1 = st.frames;
  return { ok: true, tiers: st.tiers(), clips, held, equipped,
           sideResolution: (typeof sideResolution !== 'undefined' ? sideResolution : null),
           frames: f1, framesGained: f1 - f0, shots };
})()`;

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 200, label: 'battle_cast_shots' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');

  const ready = await evalPage(cdp, `(async () => {
    for (let i = 0; i < 300; i++) {
      if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE) return { ready: true, three: THREE.REVISION };
      await new Promise(r => setTimeout(r, 200));
    }
    return { ready: false };
  })()`, 90000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready (three r${ready.three})`);

  const meta = {};
  let bad = 0;
  for (const s of SHOTS) {
    if (ONLY && ONLY !== s.name) continue;
    process.stdout.write(`  ${s.name} ... `);
    const r = await evalPage(cdp, drive(s), 300000);
    if (!r.ok) { console.log('FAILED:', r.why); meta[s.name] = r; bad++; continue; }
    if (r.framesGained < 30) console.log(`\n    WARNING: only ${r.framesGained} frames rendered — the canvas may be stalled`);
    const png = (uri, file) => { if (uri) writeFileSync(file, Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64')); };
    for (const [k, uri] of Object.entries(r.shots || {})) png(uri, join(OUT, `${TAG}-${s.name}-${k}.png`));
    if (s.full) {
      const full = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
      writeFileSync(join(OUT, `${TAG}-${s.name}-frame.png`), Buffer.from(full.data, 'base64'));
    }
    meta[s.name] = { tiers: r.tiers, clips: r.clips, held: r.held, equipped: r.equipped,
                     sideResolution: r.sideResolution || null,
                     framesGained: r.framesGained, shots: Object.keys(r.shots || {}) };
    console.log(`ok  frames+${r.framesGained}  held=${JSON.stringify(r.held)}  clips.vesper=${JSON.stringify((r.clips || {}).vesper)}`);
    if (r.sideResolution) {
      const sr = r.sideResolution, ids = Object.keys(r.tiers || {});
      const ok = sr.party.length + sr.foes.length === ids.length && !sr.party.some(i => sr.foes.indexOf(i) >= 0);
      console.log(`    sides via ${sr.via} · party=[${sr.party}] foes=[${sr.foes}] · partition ${ok ? 'OK' : 'BROKEN'}`);
    }
    await evalPage(cdp, `(async()=>{ const s=window.__EBB_SCREEN;
      if (window.Battle) { try { window.Battle._forceEnd && window.Battle._forceEnd(); } catch(e){} }
      if (s && s.stage) { try { s.stage.destroy(); } catch(e){} }
      if (s && s.destroy) { try { s.destroy(); } catch(e){} }
      window.__EBB_SCREEN = null; window.Battle.active = false;
      document.querySelectorAll('.ebb-root').forEach(n=>n.remove());
      return true; })()`);
    await sleep(400);
  }
  console.log('\nwrote to', OUT);
  console.log(JSON.stringify(meta, null, 2));
  cdp.close(); kill(); process.exit(bad ? 2 : 0);
})().catch((e) => { console.error('battle_cast_shots error:', e); kill(); process.exit(2); });
