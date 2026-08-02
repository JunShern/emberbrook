/* cdp.mjs — the shared Chrome/CDP plumbing every browser tool in this repo uses.
 *
 * WHY THIS EXISTS (2026-08-02). Five tools drove Chrome independently and each
 * re-made the same three mistakes. All three cost real debugging time in one day:
 *
 *  1. HARDCODED PORTS THAT COLLIDE. `playthrough_test` and `trigger_probe` both
 *     shipped `9351`; run them together and the second Chrome cannot bind, so it
 *     exits and the tool reports "chrome never exposed a page" — a lie about the
 *     world caused by a neighbour. The coordinator also poisoned a lane's run this
 *     way by driving the same gauntlet concurrently, and left an orphan holding a
 *     port afterwards. `freePort()` ends the whole class: ask the OS for a port
 *     nobody owns.
 *
 *  2. A MATCHER THAT KNEW ONE URL. Four tools searched targets for the literal
 *     'play3d.html'. The game is ALSO served at the friendly route '/play.html'
 *     (server.js maps it), so a tool aimed at the friendly route found nothing and
 *     said so confidently. The page was there every time.
 *
 *  3. FAILURE MESSAGES THAT REPORT ONLY THE ABSENCE. "no page found" is
 *     indistinguishable from "Chrome never started", "Chrome started and crashed",
 *     "the port was taken" and "my matcher is wrong" — and it was the last of
 *     those. A negative result must carry the evidence that produced it, or the
 *     next person debugs the wrong layer. findPage() dumps every target it saw.
 *
 * The general rule this encodes, which is the day's most expensive lesson:
 * AN INSTRUMENT THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING.
 */
import { createServer } from 'net';
import { execSync } from 'child_process';

/** A port the OS says is free right now. Beats any hardcoded number. */
export function freePort() {
  return new Promise((res, rej) => {
    const s = createServer();
    s.once('error', rej);
    s.listen(0, '127.0.0.1', () => {
      const p = s.address().port;
      s.close(() => res(p));
    });
  });
}

/** Kill any Chrome still holding this profile dir — the orphan class, pre-empted.
 *  Note the `zsh -c` exclusion: a `ps | grep` matches the SHELL carrying the
 *  pattern in its own command line, which is how a coordinator once "confirmed"
 *  a stale Chrome that did not exist. */
export function killOrphans(profileDir) {
  try {
    const out = execSync(
      `ps ax -o pid,command | grep "user-data-dir=${profileDir}" | grep -v "grep\\|zsh -c" || true`,
      { encoding: 'utf8' });
    const pids = out.trim().split('\n').filter(Boolean)
      .map(l => parseInt(l.trim().split(/\s+/)[0], 10)).filter(Boolean);
    for (const pid of pids) { try { process.kill(pid, 'SIGKILL'); } catch (e) { } }
    return pids.length;
  } catch (e) { return 0; }
}

/** The game page, however it was routed. Accepts /play.html (the friendly Express
 *  route) and /play3d.html (the engine file) — both are the same runtime. */
export const GAME_PAGE = /\/play(3d)?\.html/;

/**
 * Find the game page over CDP, with a failure that carries its own evidence.
 * @param {number} port
 * @param {object} [o]  { match:RegExp, tries:number, waitMs:number, label:string }
 */
export async function findPage(port, o = {}) {
  const match = o.match || GAME_PAGE;
  const tries = o.tries || 240;          // 60 s at the default 250 ms
  const waitMs = o.waitMs || 250;
  let lastTargets = null, everReached = false, lastErr = null;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/list`);
      const targets = await r.json();
      everReached = true;
      lastTargets = targets;
      const p = targets.find(t => t.type === 'page' && match.test(t.url));
      if (p && p.webSocketDebuggerUrl) return p.webSocketDebuggerUrl;
    } catch (e) { lastErr = e && e.message; }
    await new Promise(r => setTimeout(r, waitMs));
  }
  // THE DIAGNOSTIC FAILURE. Say which of the four possible worlds we are in.
  const lines = [`${o.label || 'cdp'}: no page matching ${match} on port ${port}`];
  if (!everReached) {
    lines.push(`  CDP was never reachable at 127.0.0.1:${port} (${lastErr || 'no response'}).`);
    lines.push('  => Chrome did not start, died on launch, or the port was already taken.');
    lines.push('     Check: another tool on the same port, or an orphan (killOrphans).');
  } else {
    lines.push(`  CDP WAS reachable, so Chrome is alive. It exposed ${lastTargets.length} target(s):`);
    for (const t of lastTargets) lines.push(`    [${t.type}] ${t.url}`);
    lines.push('  => Chrome is fine; the MATCHER is probably wrong. Compare the URLs above');
    lines.push('     with the pattern. (This is exactly how /play.html was missed by a');
    lines.push("     matcher hardcoded to 'play3d.html'.)");
  }
  throw new Error(lines.join('\n'));
}

/** Standard flags. `gpu:true` for anything that PHOTOGRAPHS the render — forcing
 *  swiftshader while a Blender bake owns the CPU made Chrome miss its window
 *  entirely (measured). State-only assertions can afford software rasterisation. */
export function chromeArgs({ port, profile, url, gpu = false, size = '1400,800', headed = false }) {
  return [
    `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    ...(gpu ? [] : ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu']),
    '--autoplay-policy=no-user-gesture-required',
    `--window-size=${size}`, ...(headed ? [] : ['--headless=new']), url,
  ];
}
