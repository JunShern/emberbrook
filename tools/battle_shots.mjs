#!/usr/bin/env node
// battle_shots.mjs — PHOTOGRAPH THE BATTLE SCREEN OF THE REAL GAME.
//
// The battle-arena lane's eye gate. arena_playtest.mjs proves the integration in
// NUMBERS; this proves it in PIXELS, and it is the instrument the "open every
// image you produce" ruling is satisfied with for battle work.
//
//   node tools/battle_shots.mjs --port=3000 --tag=after
//   node tools/battle_shots.mjs --tag=before --only=meadow --head
//
// WHAT IT CAPTURES, and why there are two kinds of picture:
//   *.png            Page.captureScreenshot — THE WHOLE FRAME: arena + every
//                    battle window. This is "what the game looks like".
//   *-arena.png      stage.snapshot() — the WebGL canvas alone, rendered
//                    SYNCHRONOUSLY. Loose screenshot timing cannot catch a 120 ms
//                    impact flash; a synchronous render can, so VFX frames come
//                    from here. (Same path docs/qa/battle3d/arena-*.png used.)
//
// AN ID IS NOT A SIDE. The foe this tool attacks is resolved by ASKING THE STAGE
// (stage.sides() / stage.at().side) and asserted not to be a party member before a
// single frame is shot — see SIDE_JS below for the bug that earned the rule.
// For the `impact` shot the frames are: -swing (210 ms), -hit (post-flinch),
// -ko (+340 ms after stage.ko), and the trailing -arena.png, which for THIS shot
// alone is the settled post-KO frame rather than the impact frame.
//
// --arena=world drives the ?arena=world spike stage instead of the diorama; it is
// the A/B that proves the side resolution rather than the id pattern is doing the
// work, because that stage builds the PARTY FIRST.
//
// A REAL GPU, ON PURPOSE. swiftshader renders this arena at ~0.4 fps, which is
// not a picture of the game, it is a picture of the harness. So no --use-angle
// override: headless=new gets the machine's real GL. `frames` is read out of the
// live stage before every capture and asserted to be CLIMBING — an instrument
// that photographs a stalled canvas must prove the canvas was not stalled.
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
const TAG = arg('tag', 'shot');
const OUT = join(ROOT, arg('out', 'docs/qa/battle3d'));
const ONLY = arg('only', null);
const HEAD = argv.includes('--head');
const ARENA = arg('arena', null);          // 'world' drives the ?arena=world stage
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1`
          + (ARENA ? `&arena=${encodeURIComponent(ARENA)}` : '');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- THE SHOT LIST --------------------------------------------------------
// Fixed party, fixed groups, fixed seeds: the whole point is that a BEFORE and
// an AFTER differ only by the code between them.
const SHOTS = [
  { name: 'meadow',  zone: 'meadow', group: ['reed-nibbler', 'reed-nibbler'], party: ['vesper', 'maren'] },
  { name: 'forest',  zone: 'forest', group: ['duskpad', 'bramble-shade'],     party: ['vesper', 'maren'] },
  { name: 'crag',    zone: 'crag',   group: ['scree-shell', 'duskpad'],       party: ['vesper', 'maren', 'lake'] },
  { name: 'water',   zone: 'water',  group: ['weir-eel', 'brook-sprite'],     party: ['vesper', 'lake'] },
  // the impact frame: the party lands a hit and we render the flash synchronously
  { name: 'impact',  zone: 'meadow', group: ['duskpad', 'duskpad'],           party: ['vesper', 'maren'], impact: true },
  // THE FALLBACK CHAIN, VERIFIED RATHER THAN ASSERTED. Each of these kills a
  // tier at runtime so the tier BELOW it is what gets photographed — the same
  // switches BattleStage3D.disable ships for exactly this purpose.
  { name: 'fb-plate', zone: 'meadow', group: ['reed-nibbler', 'duskpad'], party: ['vesper', 'maren'],
    kill: ['partyModel'] },
  { name: 'fb-proxy', zone: 'meadow', group: ['reed-nibbler', 'duskpad'], party: ['vesper', 'maren'],
    kill: ['partyModel', 'foeModel', 'billboard'] },
];

// ---- launch ---------------------------------------------------------------
const profile = join(process.env.TMPDIR || '/tmp', 'battle-shots-' + process.pid);
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

// ---- AN ID IS NOT A SIDE --------------------------------------------------
// This tool used to pick its foe with `/^m/`, WHICH ALSO MATCHES `maren`. It
// survived here only by accident of build order — battle_stage3d builds foes
// BEFORE the party, so `Object.keys(tiers())[0]` was still `m0` — and the same
// line against battle_world (which builds the PARTY first, battle_world.js:268)
// selects a party member and lunges at, flinches and KOs her. An instrument that
// is correct by accident of somebody else's array order is not correct.
//
// So ASK THE STAGE. Preference order, most authoritative first:
//   1. st.sides()          — battle_world's own per-body side map (:735)
//   2. st.at(id).side      — battle_stage3d's per-body accessor (:3060), the
//                            value newBody() was constructed with ('foe'/'party')
//   3. /^m\d+$/            — LAST RESORT: battle_rules.derive.foesFromGroup's own
//                            id scheme. A pattern, and labelled as one.
// The resolution is REPORTED and ASSERTED, never assumed: a run whose target is
// not on the foe side throws instead of quietly photographing the wrong body.
const SIDE_JS = `
  const sideOf = (id) => {
    if (typeof st.sides === 'function') { const s = st.sides(); if (s && s[id]) return { side: s[id], via: 'stage.sides()' }; }
    if (typeof st.at === 'function') { const a = st.at(id); if (a && a.side) return { side: a.side, via: 'stage.at().side' }; }
    return { side: /^m\\d+$/.test(id) ? 'foe' : 'party', via: 'id-pattern-fallback' };
  };
  const roster = Object.keys(st.tiers()).map(id => Object.assign({ id }, sideOf(id)));
  const foes = roster.filter(r => r.side === 'foe').map(r => r.id);
  const allies = roster.filter(r => r.side !== 'foe').map(r => r.id);
  if (!foes.length) throw new Error('no foe-side body on the stage: ' + JSON.stringify(roster));
  const TARGET = foes[0], ACTOR = 'vesper';
  // THE ASSERTION THIS FILE EXISTS FOR.
  if (allies.indexOf(TARGET) >= 0) throw new Error('target ' + TARGET + ' is a PARTY MEMBER — an id is not a side');
  extra_meta.sideResolution = { via: roster.length ? roster[0].via : 'none', roster: roster,
                                actor: ACTOR, actorSide: (roster.find(r => r.id === ACTOR) || {}).side || '?',
                                target: TARGET, targetSide: 'foe',
                                order: Object.keys(st.tiers()), party: allies, foes: foes };
`;

// The page-side driver, as one expression per shot. It never touches the kernel:
// it starts a normal battle through Battle.start and parks it at the command
// menu (autoplay off, no key is ever sent), which is the state a player reads.
const drive = (s) => `(async () => {
  const GS = window.GS, B = window.Battle, R = window.Rules;
  const D = window.BattleStage3D && window.BattleStage3D.disable;
  if (D) { for (const k in D) D[k] = false; ${JSON.stringify(s.kill || [])}.forEach(k => { D[k] = true; }); }
  const flags = {}; ${JSON.stringify(s.party)}.forEach(id => { if (id === 'maren') flags['maren-joined'] = true; if (id === 'lake') flags['lake-joined'] = true; });
  if (Object.keys(flags).length) GS.setFlags(flags);
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty()
    .filter(ch => ${JSON.stringify(s.party)}.indexOf(ch.id) >= 0)
    .map(ch => R.derive.partyMember(growth, items, ch));
  const zd = GS.data.encounters.zones[${JSON.stringify(s.zone)}];
  // fire and DO NOT await: the battle parks on the human seat's menu
  const p = B.start({ zone: ${JSON.stringify(s.zone)}, group: ${JSON.stringify(s.group)}, seed: 4242,
                      backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  p.then(()=>{}, ()=>{});
  // wait for the stage, then for every body to leave the proxy tier, then for the
  // intro sweep to settle — measured in RENDERED FRAMES, the only honest clock.
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 200 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { ok: false, why: 'no stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const t = st.tiers();
    const settled = Object.values(t).every(v => v !== 'proxy');
    if (settled && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
  const extra = {};
  const extra_meta = {};
  ${s.impact ? `
  // THE IMPACT FRAMES. Drive the stage's own public verbs — the same ones
  // battle_turnbased calls on an action and a damage event — and render
  // SYNCHRONOUSLY, because a screenshot's timing cannot catch a 150 ms flash.
  // Three moments, because they are three different claims: the swing at full
  // extension, the frame the blow lands, and the KO.
  ${SIDE_JS}
  st.setTarget(TARGET); st.setActor(ACTOR);
  st.act(ACTOR, 'attack');
  await new Promise(r => setTimeout(r, 210));
  extra.swing = st.snapshot();
  await new Promise(r => setTimeout(r, 60));
  st.flinch(TARGET);
  await new Promise(r => setTimeout(r, 70));
  extra.hit = st.snapshot();
  await new Promise(r => setTimeout(r, 520));
  st.ko(TARGET);
  await new Promise(r => setTimeout(r, 340));
  extra.ko = st.snapshot();
  ` : ''}
  const frames1 = st.frames;
  const D2 = window.BattleStage3D && window.BattleStage3D.disable;
  return { ok: true, tiers: st.tiers(), frames: frames1, framesGained: frames1 - f0,
           killed: D2 ? Object.keys(D2).filter(k => D2[k]) : 'module-not-loaded-yet',
           arena: st.snapshot(), extra, sideResolution: extra_meta.sideResolution || null };
})()`;

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 200, label: 'battle_shots' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');

  const ready = await evalPage(cdp, `(async () => {
    for (let i = 0; i < 300; i++) {
      if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE) {
        return { ready: true, three: THREE.REVISION };
      }
      await new Promise(r => setTimeout(r, 200));
    }
    return { ready: false };
  })()`, 90000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready (three r${ready.three})`);

  const meta = {};
  for (const s of SHOTS) {
    if (ONLY && ONLY !== s.name) continue;
    process.stdout.write(`  ${s.name} ... `);
    const r = await evalPage(cdp, drive(s), 300000);
    if (!r.ok) { console.log('FAILED:', r.why); meta[s.name] = r; continue; }
    // AN INSTRUMENT THAT PHOTOGRAPHS MUST PROVE THE CANVAS WAS LIVE.
    if (r.framesGained < 30) console.log(`\n    WARNING: only ${r.framesGained} frames rendered — the canvas may be stalled`);
    const png = (uri, file) => { if (uri) writeFileSync(file, Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64')); };
    png(r.arena, join(OUT, `${TAG}-${s.name}-arena.png`));
    for (const [k, uri] of Object.entries(r.extra || {})) png(uri, join(OUT, `${TAG}-${s.name}-${k}.png`));
    const full = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    const fullFile = join(OUT, `${TAG}-${s.name}.png`);
    writeFileSync(fullFile, Buffer.from(full.data, 'base64'));
    meta[s.name] = { tiers: r.tiers, frames: r.frames, framesGained: r.framesGained, killed: r.killed,
                     sideResolution: r.sideResolution || undefined };
    console.log(`ok  frames+${r.framesGained}  killed=${JSON.stringify(r.killed)}  tiers=${JSON.stringify(r.tiers)}`);
    // THE SIDE RECEIPT, printed where a reader of the run log cannot miss it.
    if (r.sideResolution) {
      const sr = r.sideResolution;
      console.log(`    sides via ${sr.via}  |  build order ${JSON.stringify(sr.order)}`);
      console.log(`    actor ${sr.actor} (${sr.actorSide})  ->  target ${sr.target} (${sr.targetSide})` +
                  `  |  party=${JSON.stringify(sr.party)}  foes=${JSON.stringify(sr.foes)}`);
      if (sr.party.indexOf(sr.target) >= 0) { console.error('    FAIL: target is a party member'); process.exitCode = 3; }
      else console.log('    OK: target is NOT in the party');
    }
    // tear the battle down before the next one
    await evalPage(cdp, `(async()=>{ const s=window.__EBB_SCREEN; if (window.Battle) { try { window.Battle._forceEnd && window.Battle._forceEnd(); } catch(e){} }
      if (s && s.stage) { try { s.stage.destroy(); } catch(e){} }
      if (s && s.destroy) { try { s.destroy(); } catch(e){} }
      window.__EBB_SCREEN = null; window.Battle.active = false;
      document.querySelectorAll('.ebb-root').forEach(n=>n.remove());
      return true; })()`);
    await sleep(400);
  }
  console.log('\nwrote to', OUT);
  console.log(JSON.stringify(meta, null, 2));
  cdp.close(); kill(); process.exit(0);
})().catch((e) => { console.error('battle_shots error:', e); kill(); process.exit(2); });
