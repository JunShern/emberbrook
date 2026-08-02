#!/usr/bin/env node
// ui_console_probe.mjs — THE CONSOLE GATE, ON ITS OWN.
//
// transition_test's console gate is the thing that catches a UI module which
// PARSES BUT DOES NOT EXECUTE (or worse, one that does not parse at all: this
// repo's modules self-arm at load, so a syntax error makes a module silently
// ABSENT). That gate is bundled inside a 24-door gauntlet that takes 20 minutes
// on a contended machine, which is a bad feedback loop for a UI lane that edits
// CSS-in-template-literals all day.
//
// So this is the same question asked in thirty seconds: load the real page, let
// the world become ready, dispatch the real 'eb-scene' CustomEvent (the in-place
// scene-swap contract every module re-arms on), and report EVERY console error
// and page exception, plus whether each module is actually present on window.
//
// It is NOT a replacement for transition_test — it proves nothing about
// transitions, GPU baselines, music drift or spawn placement. It proves the one
// thing a UI edit most often breaks.
//
//   node tools/ui_console_probe.mjs --port=3000
import { spawn } from 'node:child_process';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { freePort, findPage, GAME_PAGE } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=')[1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const SCENE = arg('scene', 'del-cine');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// THE OPTIONAL-ASSET CLASSIFIER IS transition_test's OWN, COPIED VERBATIM (see
// its "console watch" block). A bundle that ships no zones.json / depth.json /
// cine.json is the DOCUMENTED "absent is fine" path — every interior takes it —
// and the browser logs a network 404 for each. Two instruments answering the
// same question must not disagree about what an error is, so this probe does not
// get to invent a stricter rule than the gate it stands in for.
const OPTIONAL = /zones\.json|cine\.json|depth\.json|meta\.json|routes\.json|stylized\.png|favicon/;

const CDP = await freePort();
const profile = join(process.env.TMPDIR || '/tmp', 'ui-console-' + process.pid);
// nomusic=1: an agent is never audible (standing order).
const URL = `http://localhost:${PORT}/play3d.html?scene=${SCENE}&nomusic=1`;
const chrome = spawn(process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`, '--no-first-run',
   '--no-default-browser-check', '--disable-extensions', '--headless=new',
   '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu',
   '--autoplay-policy=no-user-gesture-required', '--window-size=1400,800', URL],
  { stdio: 'ignore' });
const kill = () => { try { chrome.kill('SIGKILL'); } catch (e) { } };
process.on('exit', kill);

const wsUrl = await findPage(CDP, { tries: 160, label: 'ui_console_probe' });
const sock = new WebSocket(wsUrl, { maxPayload: 64 * 1024 * 1024 });
const pend = new Map(); let id = 0;
const errors = [], warns = [];
sock.on('message', (raw) => {
  const m = JSON.parse(raw);
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); return; }
  if (m.method === 'Runtime.exceptionThrown') {
    const d = m.params.exceptionDetails;
    errors.push('EXCEPTION ' + (d.exception && d.exception.description || d.text) +
                ' @' + (d.url || '?') + ':' + (d.lineNumber + 1));
  }
  if (m.method === 'Log.entryAdded') {
    const e = m.params.entry;
    const line = `${e.source}: ${e.text}` + (e.url ? ` @${e.url}:${e.lineNumber || 0}` : '');
    if (e.level === 'error') errors.push(line);
    else if (e.level === 'warning') warns.push(line);
  }
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
    errors.push('console.error: ' + m.params.args.map(a => a.value || a.description || '?').join(' '));
  }
});
await new Promise(r => sock.on('open', r));
const send = (method, params) => new Promise(ok => { const i = ++id; pend.set(i, ok); sock.send(JSON.stringify({ id: i, method, params: params || {} })); });
await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');

const ev = async (expr) => {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  return r.result && r.result.result ? r.result.result.value : undefined;
};

// world ready
let ready = false;
for (let i = 0; i < 240 && !ready; i++) {
  ready = !!(await ev('!!(window.SIM && SIM.scene && SIM.scene())'));
  if (!ready) await sleep(500);
}
if (!ready) { console.error('FAIL: the world never became ready'); kill(); process.exit(2); }
await sleep(1500);

// THE MODULES. A module that failed to parse is simply not on window — which is
// exactly the failure mode this probe exists for, and it is invisible in a
// screenshot.
const mods = await ev(`JSON.stringify({
  EBUI: !!window.EBUI, Menu: !!window.Menu, Shop: !!window.Shop,
  Battle: !!window.Battle, Rules: !!window.Rules, GS: !!(window.GS && window.GS.ok),
  Encounters: !!window.Encounters, Story: !!window.Story, Dialogue: !!window.Dialogue,
  ramp: getComputedStyle(document.documentElement).getPropertyValue('--eb-fs-md').trim(),
  ease: getComputedStyle(document.documentElement).getPropertyValue('--eb-ease-out').trim()
})`);

// THE RE-ARM CONTRACT: every module self-arms at load AND on 'eb-scene'. Firing
// it by hand is the cheapest proof that none of them throws on the way through.
await ev(`window.dispatchEvent(new CustomEvent('eb-scene',{detail:{scene:SIM.scene()}})), 1`);
await sleep(1200);

// and the two panels really open and close through UILOCK
const panels = await ev(`(async()=>{
  const out={};
  out.menuOpen = !!window.Menu.open();
  await new Promise(r=>setTimeout(r,300));
  out.lockedWhileOpen = !!(window.UILOCK && window.UILOCK.active());
  out.menuClose = !!window.Menu.close();
  await new Promise(r=>setTimeout(r,400));
  out.lockedAfter = !!(window.UILOCK && window.UILOCK.active());
  return JSON.stringify(out);
})()`);
await sleep(500);

console.log('modules/tokens :', mods);
console.log('panel + UILOCK :', panels);
console.log('warnings       :', warns.length);
for (const w of warns.slice(0, 8)) console.log('   warn:', w);
const real = errors.filter(e => !OPTIONAL.test(e));
console.log('console errors :', errors.length, 'total,', errors.length - real.length,
            'optional-asset 404s (the gate\'s own classifier),', real.length, 'REAL');
for (const e of real) console.log('   ERR :', e);
for (const e of errors.filter(e => OPTIONAL.test(e))) console.log('   (optional):', e);
const m = JSON.parse(mods), p = JSON.parse(panels);
const missing = ['EBUI', 'Menu', 'Shop', 'Battle', 'Rules', 'GS'].filter(k => !m[k]);
const bad = real.length > 0 || missing.length > 0 || !m.ramp || !m.ease ||
            !p.menuOpen || !p.lockedWhileOpen || p.lockedAfter;
console.log('\n' + (bad ? 'CONSOLE GATE RED' + (missing.length ? ' — missing: ' + missing.join(',') : '')
                        : 'CONSOLE GATE GREEN — no errors, every module armed, UILOCK taken and released'));
kill();
process.exit(bad ? 1 : 0);
