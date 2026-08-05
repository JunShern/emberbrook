#!/usr/bin/env node
/* save_probe.mjs — CAN A PLAYER STOP FOR THE NIGHT MID-CHAPTER AND COME BACK?
 *
 *   node tools/playtest/save_probe.mjs --from ch2.jam --port 3000
 *
 * WHY THIS EXISTS. It is item 4 on llm_playtester's own "covering Chapter Two" list
 * and the one nobody had built: *"A SAVE/RESUME PROBE. Ch2 is where a player stops
 * for the night. Driving the pause menu with the same keys and reloading would
 * exercise the v2 save from the OUTSIDE for the first time. --from= already proves
 * the load half."*
 *
 * Everything in this repo that touches the save writes it from the inside.
 * `playthrough_test` proves a cold reload built from `at` lands in the same place,
 * but IT WRITES THE SAVE ITSELF; `--from=` patches localStorage directly. Neither
 * has ever asked the question a player asks: **press Escape, choose SAVE, quit,
 * come back through the front door.** Every key here is a real
 * Input.dispatchKeyEvent and the resume URL is built by the SAME rule
 * public/index.html's CONTINUE card uses (scene + cam + sx/sy/sz out of `at`), so a
 * green run is a statement about the door the player actually walks through.
 *
 * IT MOVES THE BODY BEFORE IT SAVES, on purpose. A save taken on the drop-in
 * coordinate would round-trip even if `at.pos` were hard-coded from the URL, and
 * the probe would pass while proving nothing.
 *
 * Adapted from look_probe.mjs: same CDP pattern, OS-assigned port via freePort(),
 * own profile cleaned on every exit path, hard self-expiry. Chrome boots at
 * about:blank and the game arrives by Page.navigate — round 4's key-storm fix.
 */
import { spawn } from 'child_process';
import { rmSync } from 'fs';
import { join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '../cdp.mjs';
import { checkpointsFromStory } from './adapter_emberbrook.mjs';
import { mkArg } from '../argv.mjs';

// `--k v` AND `--k=v` (tools/argv.mjs): the bare indexOf form silently

// ignored the `=` spelling and used the DEFAULT instead.

const { arg } = mkArg(process.argv);
const FROM = arg('from', 'ch2.jam');
const PORT = parseInt(arg('port', '3000'), 10);
const WALK_MS = parseInt(arg('walk-ms', '1200'), 10);
const CDP = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const KEYS = {
  down: { key: 's', code: 'KeyS', vk: 83 }, up: { key: 'w', code: 'KeyW', vk: 87 },
  right: { key: 'd', code: 'KeyD', vk: 68 }, left: { key: 'a', code: 'KeyA', vk: 65 },
  enter: { key: 'Enter', code: 'Enter', vk: 13 }, escape: { key: 'Escape', code: 'Escape', vk: 27 },
  e: { key: 'e', code: 'KeyE', vk: 69 },
};

const profile = join(process.env.TMPDIR || '/tmp', 'save-probe-profile-' + process.pid);
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  /* THE FOUR THROTTLING FLAGS ARE NOT DECORATION — play3d's world, and with it
   * Story.tick, rides requestAnimationFrame, and a throttled rAF is a player who
   * cannot walk. Measured while writing this probe: without them the body moved
   * 0.07-0.22 m across four 1.2 s key holds and `at.cam` never followed the shot,
   * and both looked exactly like game defects. The adapter carries the same four
   * for the same reason. */
  '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows',
  '--disable-renderer-backgrounding', '--disable-features=CalculateNativeWinOcclusion',
  '--window-size=1400,820', '--headless=new', 'about:blank',
], { stdio: 'ignore' });

let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
};
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { kill(); process.exit(130); });
setTimeout(() => { console.error('SELF-EXPIRY 480s'); kill(); process.exit(9); }, 480000).unref();

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', (d) => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
    ws.on('open', () => res({
      send: (method, params = {}) => new Promise((ok) => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); }),
      close: () => ws.close(),
    }));
    ws.on('error', rej);
  });
}

let PASS = 0, FAIL = 0;
const ok = (name, cond, detail) => { if (cond) { PASS++; console.log(`  ok    ${name}${detail ? '  ' + detail : ''}`); } else { FAIL++; console.log(`  FAIL  ${name}${detail ? '  ' + detail : ''}`); } };

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'save_probe', match: /about:blank/ }));
  await cdp.send('Runtime.enable'); await cdp.send('Page.enable');
  const ev = async (expr) => {
    const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    return r.result && r.result.result ? r.result.result.value : undefined;
  };
  // `text` on a single-character keyDown is what the adapter sends and what the page
  // expects; without it a held 'w' moves the body a few centimetres in five seconds.
  const kd = (k) => ({ type: 'keyDown', key: k.key, code: k.code, windowsVirtualKeyCode: k.vk,
    nativeVirtualKeyCode: k.vk, ...(k.key.length === 1 ? { text: k.key } : {}) });
  const ku = (k) => ({ type: 'keyUp', key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk });
  const tap = async (name) => {
    const k = KEYS[name];
    await cdp.send('Input.dispatchKeyEvent', kd(k));
    await sleep(60);
    await cdp.send('Input.dispatchKeyEvent', ku(k));
    await sleep(320);
  };
  const hold = async (name, ms) => {
    const k = KEYS[name];
    await cdp.send('Input.dispatchKeyEvent', kd(k));
    await sleep(ms);
    await cdp.send('Input.dispatchKeyEvent', ku(k));
    await sleep(250);
  };
  const urlFor = (scene, cam, pos, extra) => {
    const q = new URLSearchParams({ nomusic: '1' });
    if (scene) q.set('scene', scene); if (cam) q.set('cam', cam);
    if (pos) { q.set('sx', pos[0]); q.set('sy', pos[1]); q.set('sz', pos[2]); }
    for (const [k, v] of Object.entries(extra || {})) q.set(k, v);
    return `http://localhost:${PORT}/play3d.html?` + q.toString();
  };
  /* "PLAYABLE" MEANS THE BODY IS PLACED AND THE SCENE HAS PICKED ITS SHOT — not
   * merely that SIM answers. On a cold boot SIM.pos() is finite and equal to the
   * engine's [0,2,0] placeholder for the first ~2 s, and a probe that starts
   * walking there measures the placement, not the walk. */
  const ready = async (budget = 90000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < budget) {
      const v = await ev(`(()=>{try{ if(!window.SIM||!window.GS) return 0;
        const p=SIM.pos(); if(!p||!isFinite(p.x)) return 0;
        const c=SIM.cine?SIM.cine():null; if(c && !c.shot) return 0;
        return 1 }catch(e){return 0}})()`);
      if (v === 1) { await sleep(1500); return true; }
      await sleep(400);
    }
    return false;
  };
  // The whole state a resume has to carry, read from the engine rather than the file.
  const STATE_JS = `(()=>{ const o={};
    try{ o.scene=SIM.scene() }catch(e){}
    try{ const p=SIM.pos(); o.pos=[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)] }catch(e){}
    try{ o.shot=(SIM.cine()||{}).shot||null }catch(e){}
    try{ const s=JSON.parse(GS.serialize());
      o.beats=Object.keys(s.beats||{}).length; o.flags=Object.keys(s.flags||{}).length;
      o.gold=s.gold; o.at=s.at||null; o.v=s.v||s.version||null }catch(e){}
    try{ o.party=(GS.activeParty()||[]).map(c=>c.id||c) }catch(e){}
    return JSON.stringify(o) })()`;
  const state = async () => JSON.parse(await ev(STATE_JS) || '{}');

  const c = checkpointsFromStory().checkpoints.find(x => x.id === FROM);
  if (!c) { console.error(`no beat "${FROM}" in story.json`); kill(); process.exit(2); }

  console.log(`save_probe — the pause menu, a real SAVE, and the front door's own CONTINUE`);
  console.log(`  checkpoint ${c.id}   scene ${c.scene}   pos [${(c.pos || []).join(', ')}]\n`);

  // ---- 1. boot and patch in the checkpoint, exactly as the playtester's setup() does
  await cdp.send('Page.navigate', { url: urlFor(c.scene, c.cam, c.pos, { v: String(Date.now()) }) });
  if (!await ready()) { console.error('the page never became playable'); kill(); process.exit(3); }
  await ev(`(()=>{ const p=${JSON.stringify({ flags: c.flags, beats: c.beats, at: { chapter: c.chapter, scene: c.scene, cam: c.cam, pos: c.pos, yaw: null } })};
    const st=JSON.parse(GS.serialize());
    Object.assign(st.flags,p.flags||{}); Object.assign(st.beats,p.beats||{});
    st.at=Object.assign({},st.at,p.at||{});
    localStorage.setItem('emberbrook-save',JSON.stringify(st)); return 1 })()`);
  await cdp.send('Page.navigate', { url: urlFor(c.scene, c.cam, c.pos, { v: String(Date.now()) }) });
  if (!await ready()) { console.error('the page never became playable after the patch'); kill(); process.exit(3); }

  /* READ THROUGH WHATEVER THE ARRIVAL OPENED. A `--from=` checkpoint drops in JUST
   * BEFORE its beat, so the beat fires on the first tick and holds UILOCK — and
   * while UILOCK is held the body cannot walk AND ui_kit suppresses the global Esc
   * that opens the pause menu. The first version of this probe measured both of
   * those as failures of the game. They were the probe standing inside a cutscene. */
  console.log('§0 THE ARRIVAL BEAT, READ THROUGH');
  let lines = 0;
  for (let i = 0; i < 40; i++) {
    const up = await ev(`(()=>{const v=[...document.querySelectorAll('.ebui-veil')].filter(e=>getComputedStyle(e).display!=='none');
      return (v.length || (window.UILOCK&&UILOCK.active&&UILOCK.active())) ? 1 : 0})()`);
    if (!up) break;
    await tap('e'); lines++;
  }
  ok('the arrival cutscene closed', !(await ev(`(()=>((window.UILOCK&&UILOCK.active&&UILOCK.active())?1:0))()`)),
    `${lines} box(es) read through`);

  console.log('\n§1 THE PLAYER WALKS SOMEWHERE, so the save has something of its own to carry');
  const before0 = await state();
  for (const dir of ['down', 'right', 'up', 'left']) {
    await hold(dir, WALK_MS);
    const p = await state();
    if (p.pos && before0.pos && Math.hypot(p.pos[0]-before0.pos[0], p.pos[2]-before0.pos[2]) > 0.5) break;
  }
  const before = await state();
  const moved = before0.pos && before.pos
    ? Math.hypot(before.pos[0] - before0.pos[0], before.pos[2] - before0.pos[2]) : 0;
  ok('the body moved off the drop-in coordinate', moved > 0.5, `${moved.toFixed(2)} m`);
  console.log(`        at ${before.scene} · ${before.shot} · [${(before.pos || []).join(', ')}] · ` +
    `${before.beats} beats · party ${(before.party || []).join('+')}`);

  console.log('\n§2 THE PAUSE MENU, ON THE KEY A PLAYER PRESSES');
  await tap('escape');
  // .mn-navrow IS THE PAUSE MENU'S ROW CLASS — menu.js's layout:'full' nav list.
  // The first version of this probe read .ebui-row, found nothing, and would have
  // filed "Escape opens no menu" against a menu that opens perfectly.
  const menu = await ev(`(()=>{const v=[...document.querySelectorAll('.ebui-veil')].filter(e=>getComputedStyle(e).display!=='none').pop();
    if(!v) return null; return JSON.stringify([...v.querySelectorAll('.mn-navrow, .ebui-row')].map(r=>r.textContent.replace(/\\s+/g,' ').trim()))})()`);
  const rows = menu ? JSON.parse(menu) : [];
  ok('Escape opens a menu', rows.length > 0, rows.length ? `${rows.length} rows` : 'nothing opened');
  const saveIdx = rows.findIndex(r => /^SAVE\b/i.test(r));
  ok('the menu offers SAVE', saveIdx >= 0, saveIdx >= 0 ? `row ${saveIdx}: "${rows[saveIdx]}"` : `rows: ${rows.join(' | ')}`);

  console.log('\n§3 SAVE, DRIVEN BY KEYS');
  if (saveIdx >= 0) {
    for (let i = 0; i < saveIdx; i++) await tap('down');   // the cursor opens on row 0
    await tap('enter');                       // open SAVE
    await sleep(400);
    await tap('enter');                       // the ask() confirm
    await sleep(900);
  }
  const raw = await ev(`(()=>{try{return localStorage.getItem('emberbrook-save')}catch(e){return null}})()`);
  let saved = null; try { saved = JSON.parse(raw); } catch (e) { }
  ok('a save was written', !!saved, saved ? `${raw.length} bytes` : 'localStorage is empty');
  if (saved) {
    const at = saved.at || {};
    ok('the save carries `at` with a scene', !!at.scene, `at.scene=${at.scene} cam=${at.cam}`);
    ok('`at.pos` is where the player was standing, not where they dropped in',
      Array.isArray(at.pos) && before.pos && Math.hypot(at.pos[0] - before.pos[0], at.pos[2] - before.pos[2]) < 1.5,
      at.pos ? `[${at.pos.map(n => (+n).toFixed(2)).join(', ')}] vs body [${before.pos.join(', ')}]` : 'no at.pos');
    ok('the beat ledger survived the save', Object.keys(saved.beats || {}).length >= before.beats,
      `${Object.keys(saved.beats || {}).length} beats`);
  }

  console.log('\n§4 QUIT AND COME BACK THROUGH THE FRONT DOOR');
  // index.html's continueUrl(), rule for rule: scene + cam + sx/sy/sz out of `at`.
  const at = (saved && saved.at) || {};
  const resume = urlFor(at.scene, at.cam, Array.isArray(at.pos) ? at.pos : null, { fade: '1', v: String(Date.now()) });
  await cdp.send('Page.navigate', { url: 'about:blank' });
  await sleep(600);
  await cdp.send('Page.navigate', { url: resume });
  const back = await ready();
  ok('the resumed page became playable', back);
  const after = back ? await state() : {};
  ok('same scene', after.scene === before.scene, `${before.scene} -> ${after.scene}`);
  ok('same shot', after.shot === before.shot, `${before.shot} -> ${after.shot}`);
  const d = (after.pos && before.pos) ? Math.hypot(after.pos[0] - before.pos[0], after.pos[2] - before.pos[2]) : Infinity;
  ok('same place (within 1.5 m)', d < 1.5, `${isFinite(d) ? d.toFixed(2) + ' m' : 'no position'}`);
  ok('the beats came back', (after.beats || 0) >= before.beats, `${before.beats} -> ${after.beats}`);
  ok('the flags came back', (after.flags || 0) >= before.flags, `${before.flags} -> ${after.flags}`);
  ok('the party came back', JSON.stringify(after.party || []) === JSON.stringify(before.party || []),
    `${(before.party || []).join('+')} -> ${(after.party || []).join('+')}`);

  console.log(`\n${FAIL ? 'FAIL' : 'PASS'}  ${PASS} passed / ${FAIL} failed`);
  cdp.close(); kill(); process.exit(FAIL ? 1 : 0);
})().catch(e => { console.error('FAILED:', e && e.stack); kill(); process.exit(1); });
