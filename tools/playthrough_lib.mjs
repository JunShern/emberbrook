// playthrough_lib.mjs — THE THREE DECISIONS playthrough_test.mjs USED TO MAKE INLINE,
// pulled out so they can be driven with a fake ledger and a fake clock in 0.1 s.
//
//   node tools/playthrough_lib.mjs --selftest
//
// WHY THIS FILE EXISTS. On the night of 2026-08-09 the same tree, the same build and
// the same server produced 84/1, 44/16 and 86/0 from three consecutive runs of
// playthrough_test. Nothing was wrong with the game: story_runtime writes the beat
// ledger at the END of a beat's `do` chain (deliberately — an interrupted beat should
// replay rather than be silently lost), and a beat carrying a `banner` or an `endCard`
// spends a FIXED, DECLARED number of seconds presenting itself before that write. Under
// machine load the harness's flat 60/75/90 s poll expired while the beat was still
// legitimately running. The proof was in the harness's own output moments later:
// `FAIL beat ch2.landing fired` followed by `beats completed: 28 — … ch2.landing`, with
// §6 fully green and zero console errors.
//
// A RACE IN A GATE IS ONLY DEBUGGABLE IF IT CAN BE REPRODUCED WITHOUT THE THING IT
// GATES. A 13-minute browser run that fails one time in three is not a test of the fix;
// it is a coin. Everything below is a pure function or takes its clock and its ledger as
// arguments, so the race, the cascade and the false UNREACHABLE line are demonstrated
// deterministically, offline, in the selftest at the bottom.

// ---------------------------------------------------------------- the window --
// A BEAT'S PRESENTATION COST IS DECLARED DATA, NOT AN UNKNOWN. `banner.ms`,
// `toast.ms`, `endCard.ms` and `wait` are in story.json; story_runtime's own defaults
// and fade-outs are the rest. So the poll window is split into two things that were
// previously conflated:
//
//   UI       — how long the game spends PRESENTING this beat. Exactly knowable.
//   SLACK    — how long the harness will wait for the beat to become ELIGIBLE and
//              start at all. Not knowable; a function of machine load.
//
// budget = SLACK + UI makes SLACK mean the same thing on every row. Under the old flat
// window a heavily-presented beat was implicitly given LESS trigger slack than a bare
// one — ch2.landing's 75 s window contained a 20 s end card, a 4.6 s banner, a 2.6 s
// toast and two dialogue nodes, so it was really a ~40 s window wearing a 75 s label,
// and it was the beat that failed. It is also self-maintaining: lengthening an end card
// in story.json now lengthens the window that waits for it, with no edit here.
//
// DECLARED durations are exact. The others are ESTIMATES and are marked as such — they
// exist so that a beat with four dialogue nodes is not scored against the same trigger
// slack as one with none, NOT to be a schedule.
export const STEP_MS = {
  banner:   (s) => (s.ms == null ? 3200 : s.ms) + 450,          // + story_runtime's fade
  toast:    (s) => (s.ms == null ? 2600 : s.ms),
  endCard:  (s) => 50 + (s.ms == null ? 16000 : s.ms) + 750,    // + fade-in + fade-out
  wait:     (s) => Math.max(0, (s || 0) * 1000),
  dialogue: () => 5000,   // ESTIMATE: the auto-reader's pace over a node of unknown length
  pov:      () => 8000,   // ESTIMATE: a pov step loads a scene
  shot:     () => 1500,   // ESTIMATE: a cut
};
export function beatUiMs(beat) {
  let ms = 0;
  for (const s of (beat && beat['do']) || []) {
    if (!s || typeof s !== 'object') continue;
    for (const k of Object.keys(STEP_MS)) if (s[k] !== undefined) ms += STEP_MS[k](s[k]);
  }
  return ms;
}
export function beatBudgetMs(beat, slackMs) {
  return (slackMs || 60000) + beatUiMs(beat);
}

// ----------------------------------------------------------------- the grace --
// WHEN THE WINDOW EXPIRES, ASK WHY BEFORE DECLARING A FAILURE. Two states look
// identical from the ledger alone and are opposite findings:
//
//   the director is BUSY  — a beat is running its `do` chain right now. The window was
//                           too short for this machine. That is a HARNESS defect, and a
//                           bounded grace turns it into a pass WITH A REPORT.
//   the director is IDLE  — nothing is running and the beat is not in the ledger. The
//                           beat did not fire. That is a GAME defect and it fails at
//                           once, with no grace at all.
//
// THIS IS WHAT KEEPS THE GATE FROM BEING WEAKENED. The grace is not "wait a bit longer
// and hope"; it is gated on a positive statement from the page that work is in flight,
// it is bounded, and it is reported with the number of milliseconds it needed. A beat
// that never fires never sees it — the director is idle, so the run fails at the window
// with `director idle`. A beat that hangs mid-chain sees it, exhausts it and fails with
// `grace expired while the director was still busy`, which is a different and equally
// true sentence.
//
// io: { poll(id, budgetMs) -> Promise<bool>   the page-side ledger poll (also pumps SIM)
//       probe(id)          -> Promise<{beat:bool, busy:bool}>   one atomic read
//       sleep(ms), now() }
export async function awaitBeat(io, id, opt) {
  const budgetMs = opt.budgetMs;
  const graceMs = opt.graceMs == null ? 30000 : opt.graceMs;
  const gracePollMs = opt.gracePollMs == null ? 250 : opt.gracePollMs;
  const t0 = io.now();
  if (await io.poll(id, budgetMs)) return { fired: true, graceMs: 0, ms: io.now() - t0, why: null };
  const g0 = io.now();
  let last = null;
  for (;;) {
    last = await io.probe(id);
    if (last && last.beat) return { fired: true, graceMs: io.now() - g0, ms: io.now() - t0, why: 'grace' };
    if (!last || !last.busy)
      return { fired: false, graceMs: io.now() - g0, ms: io.now() - t0,
               why: 'director idle — no beat was running when the window expired, so this beat is not late, it is absent' };
    if (io.now() - g0 >= graceMs)
      return { fired: false, graceMs: io.now() - g0, ms: io.now() - t0,
               why: `grace expired while the director was still busy (${graceMs} ms) — a beat is running and did not finish` };
    await io.sleep(gracePollMs);
  }
}

// --------------------------------------------------------------- the cascade --
// ONE FALSE RED USED TO INVENT FIFTEEN MORE. The CH1 loop `break`s on a beat that does
// not fire — correct, the spine is causally ordered and there is no point standing in
// the square asserting Chapter Two — but main() then carried straight on through §3,
// §3b, §4, §5, §6 and §7, every one of which asserts something that can only be true if
// the beats ran. Run 2 of 2026-08-09 turned a single 4.2 s banner race into 44/16 and
// printed `no edge to ow-valley from emb-cine`, `at.chapter is 1` and a walk verdict
// reading `No walk can ever trigger this beat` — sentences a future lane inherits as
// real defects. This repo has been burned four times by inheriting an attribution.
//
// THE RULE: after a spine break, a downstream check is NOT RUN. It is not a pass (we do
// not know) and it is not a failure (we did not look). It is counted and named in a
// third column, and the exit code is still non-zero because the run did not complete.
//
// WHY NOT "skip to the next chapter anchor and keep asserting". Considered and refused:
// the harness would have to fabricate the state the missed beats set — the flags, the
// party, `at.chapter`, the gate's own `story.ch1.gate-open` — which is Story.force() by
// another name, and §2's whole claim is that nothing here forces a beat. A gate that
// invents the preconditions of the thing it is measuring measures nothing.
export class Spine {
  constructor() { this.broken = null; this.notrun = 0; this.skipped = []; }
  break(id) { if (!this.broken) this.broken = id; }
  // Returns true if this check should run. If the spine is broken it books the label
  // as NOT RUN and returns false.
  guard(label) {
    if (!this.broken) return true;
    this.notrun++; this.skipped.push(label);
    return false;
  }
  guardAll(labels) { let any = false; for (const l of labels) any = this.guard(l) || any; return any; }
}

// ------------------------------------------------------- §W's own precondition --
// "No walk can ever trigger this beat" IS A CLAIM ABOUT THE WORLD, and §W was making it
// about a player who never got there. `anchor()` reads WHERE THE BODY IS and calls that
// the beat's anchor; when the beat never fired, the body is wherever the harness last
// teleported it, which in run 2 was the Emberbrook square labelled `ch1.done`, filled
// against a Dellhollow coordinate that is nowhere in emb-cine.
//
// THE PRECONDITION, MADE EXPLICIT: a walk pair may only be formed between two anchors
// that ARE THE PLACES TWO BEATS ACTUALLY FIRED. A beat that did not fire has no anchor,
// so it neither closes the pair behind it nor opens one in front of it — the chain is
// cut and said to be cut.
export function walkPair(prev, cur) {
  if (!cur || cur.fired !== true)
    return { action: 'no-anchor', reason:
      `${cur ? cur.id : '?'} did not fire, so the body is wherever the harness last stood it — ` +
      `that is not an anchor and nothing may be measured against it` };
  if (!prev) return { action: 'chain-start', reason: 'first anchor of the chain' };
  if (prev.fired !== true)
    return { action: 'chain-broken', reason:
      `${prev.id} did not fire, so there is no anchor behind ${cur.id} to walk from` };
  if (prev.scene !== cur.scene)
    return { action: 'scene-change', reason: `${prev.scene} -> ${cur.scene}` };
  return { action: 'fill', reason: null };
}

// ================================================================== selftest ==
// Everything above, driven with a fake ledger and a virtual clock. RED FIRST: each case
// runs the OLD logic (flat window, no grace; break-and-keep-asserting; anchor from a
// beat that never fired) and then the NEW one, so the difference is the evidence.
function fakeIo(script) {
  // script: { busyFrom, ledgerAt }  — ms on the virtual clock. ledgerAt null = never.
  let T = 0;
  const st = (t) => ({
    beat: script.ledgerAt != null && t >= script.ledgerAt,
    busy: t >= (script.busyFrom == null ? Infinity : script.busyFrom) &&
          (script.ledgerAt == null || t < script.ledgerAt),
  });
  return {
    now: () => T,
    sleep: (ms) => { T += ms; return Promise.resolve(); },
    async poll(id, budgetMs) {           // the page-side loop, 50 ms a tick
      const end = T + budgetMs;
      while (T < end) { if (st(T).beat) return true; T += 50; }
      T = end; return st(T).beat;
    },
    async probe() { return st(T); },
  };
}
async function selftest() {
  let pass = 0, fail = 0;
  const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
    else { fail++; console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
  const head = (s) => console.log('\n== ' + s);

  head('A. the window is derived from the beat\'s own declared UI, and the old flat one was short');
  // The two beats that actually failed on 2026-08-09, verbatim from story.json.
  const HUSH = { id: 'ch1.hush', do: [{ dialogue: 'x' }, { setFlags: {} },
    { banner: { title: 'The Hush has come to Emberbrook', ms: 4200 } }, { objective: 'y' }] };
  const LANDING = { id: 'ch2.landing', do: [{ dialogue: 'a' }, { dialogue: 'b' }, { setFlags: {} },
    { toast: { text: 't' } }, { banner: { ms: 4600 } },
    { endCard: { title: 'Chapter Two', ms: 20000, lines: [1, 2, 3, 4] } }, { objective: 'z' }, { save: 1 }] };
  const DONE = { id: 'ch1.done', do: [{ setFlags: {} }, { chapter: 2 },
    { endCard: { ms: 15000, lines: [1, 2] } }, { banner: { ms: 4200 } }, { objective: 'z' }, { save: 1 }] };
  ok(beatUiMs(HUSH) === 5000 + 4650, 'ch1.hush presents for 9.65 s of its window', beatUiMs(HUSH));
  ok(beatUiMs(LANDING) === 10000 + 2600 + 5050 + 20800, 'ch2.landing presents for 38.45 s of its window', beatUiMs(LANDING));
  ok(beatUiMs(DONE) === 15800 + 4650, 'ch1.done presents for 20.45 s of its window', beatUiMs(DONE));
  ok(beatUiMs({ id: 'ch1.reveal', do: [{ dialogue: 'x' }, { setFlags: {} }] }) === 5000,
     'a bare beat presents for 5 s, so it keeps essentially the whole old window');
  // The number that says the old flat window was mislabelled.
  ok(75000 - beatUiMs(LANDING) === 36550,
     'ch2.landing\'s OLD 75 s window was really 36.6 s of trigger slack wearing a 75 s label');
  ok(beatBudgetMs(LANDING, 75000) === 113450, 'the NEW window for ch2.landing is 113.4 s', beatBudgetMs(LANDING, 75000));
  ok(beatBudgetMs({ do: [] }, 60000) === 60000, 'a beat with no `do` chain is unchanged at 60 s');

  head('B. THE RACE — a beat still presenting when the window expires (this is the bug)');
  {
    // The measured shape: eligible late (68 s in, under load), then 9.65 s of `do`.
    const script = { busyFrom: 68000, ledgerAt: 68000 + 9650 };
    const oldIo = fakeIo(script);
    const oldRes = await oldIo.poll('ch1.hush', 60000);                     // the OLD logic, verbatim
    ok(oldRes === false, 'OLD: flat 60 s window -> FAIL beat ch1.hush fired  (the false red)');
    const newIo = fakeIo(script);
    const r = await awaitBeat(newIo, 'ch1.hush', { budgetMs: beatBudgetMs(HUSH, 60000), graceMs: 30000 });
    ok(r.fired === true, 'NEW: the derived 69.65 s window plus a bounded grace -> PASS', r);
    ok(r.graceMs === 8000, 'NEW: and it says it needed 8.0 s of grace', r.graceMs);
    ok(r.why === 'grace', 'NEW: the pass is labelled as a grace pass, never silent', r.why);
  }

  head('C. A DEAD BEAT STILL FAILS, AT THE WINDOW, WITH NO GRACE SPENT');
  {
    const io = fakeIo({ busyFrom: null, ledgerAt: null });   // never eligible, never busy
    const r = await awaitBeat(io, 'ch1.hush', { budgetMs: beatBudgetMs(HUSH, 60000), graceMs: 30000 });
    ok(r.fired === false, 'a beat that never fires FAILS', r);
    ok(r.graceMs === 0, 'and it spends ZERO grace — the director was idle, so it is absent, not late', r.graceMs);
    ok(/director idle/.test(r.why), 'the verdict names why the grace was refused', r.why);
  }
  head('C2. A BEAT THAT HANGS MID-CHAIN FAILS TOO, at the grace bound');
  {
    const io = fakeIo({ busyFrom: 10000, ledgerAt: null });  // busy forever, never writes
    const r = await awaitBeat(io, 'ch1.hush', { budgetMs: 69650, graceMs: 30000 });
    ok(r.fired === false, 'a beat stuck in its own `do` chain FAILS', r);
    ok(r.graceMs >= 30000 && r.graceMs < 30500, 'the grace is BOUNDED — it does not wait forever', r.graceMs);
    ok(/grace expired/.test(r.why), 'and the verdict is a different sentence from the idle one', r.why);
  }
  head('C3. the grace cannot rescue a beat that fires after the bound');
  {
    const io = fakeIo({ busyFrom: 68000, ledgerAt: 68000 + 70000 });
    const r = await awaitBeat(io, 'x', { budgetMs: 69650, graceMs: 30000 });
    ok(r.fired === false, 'a beat 70 s into a `do` chain is still a FAIL at a 30 s grace', r);
  }

  head('D. THE CASCADE — one false red used to invent fifteen more');
  {
    // Run 2's own downstream failures, in order, from playthrough_test2.log.
    const DOWNSTREAM = [
      'story.ch1.gate-open is set by the sigil beat',
      'open: the same edge is live once the flag is true',
      'the corridor was entered by the OLD GATE',
      'the player is in ow-valley, having taken an edge',
      'beat ch1.done fired on arrival in the corridor',
      'at.chapter is 2', 'at.scene tracks the corridor',
      'beat ch2.road fired on the approach to Dellhollow',
      'walk: ch1.done -> ch2.road: UNREACHABLE … No walk can ever trigger this beat',
      'the corridor was WALKED into Dellhollow', 'beat ch2.arrive fired',
      'story.ch2.done is set', 'maren-joined is set', 'GS.activeParty() now contains Maren',
      'within a stride of the same place',
    ];
    let oldFail = 1;                                   // the real one: ch1.hush
    for (const _ of DOWNSTREAM) oldFail++;             // ...and every downstream assert ran and failed
    ok(oldFail === 16, 'OLD: 1 race -> 16 failures (44/16 on the night)', oldFail);
    const sp = new Spine(); sp.break('ch1.hush');
    let newFail = 1;
    for (const l of DOWNSTREAM) if (sp.guard(l)) newFail++;
    ok(newFail === 1, 'NEW: 1 race -> 1 failure', newFail);
    ok(sp.notrun === 15, 'NEW: and 15 checks booked as NOT RUN, by name', sp.notrun);
    ok(sp.skipped[8].includes('No walk can ever'), 'NEW: including the scary walk line', sp.skipped[8]);
    const clean = new Spine();
    ok(clean.guard('anything') === true && clean.notrun === 0, 'an unbroken spine books nothing');
  }

  head('E. §W — the false UNREACHABLE line needs an anchor that a beat actually fired at');
  {
    // Run 2's exact shape: ch1.done never fired, the body is still in the square, and
    // the harness then teleports to a Dellhollow coordinate for ch2.road.
    const prev = { id: 'ch1.done', scene: 'emb-cine', at: [60.57, 1.09, -32.98], fired: false };
    const cur  = { id: 'ch2.road', scene: 'emb-cine', at: [44.5, 12.46, -36.31], fired: false };
    const oldWouldFill = prev.scene === cur.scene;     // the OLD precondition, in full
    ok(oldWouldFill === true, 'OLD: same-scene was the whole precondition -> it filled and printed UNREACHABLE');
    const p = walkPair(prev, cur);
    ok(p.action === 'no-anchor', 'NEW: no pair is formed at all', p);
    ok(/did not fire/.test(p.reason), 'NEW: and the reason names the precondition', p.reason);
    // The chain must also not re-open across a hole.
    ok(walkPair({ id: 'a', scene: 's', at: [0, 0, 0], fired: false },
                { id: 'b', scene: 's', at: [1, 0, 0], fired: true }).action === 'chain-broken',
       'NEW: a fired beat behind a hole does not close a pair either');
    ok(walkPair(null, { id: 'a', scene: 's', at: [0, 0, 0], fired: true }).action === 'chain-start',
       'the first anchor opens the chain');
    ok(walkPair({ id: 'a', scene: 's', at: [0, 0, 0], fired: true },
                { id: 'b', scene: 't', at: [0, 0, 0], fired: true }).action === 'scene-change',
       'a scene change is still an edge, not a walk');
    ok(walkPair({ id: 'a', scene: 's', at: [0, 0, 0], fired: true },
                { id: 'b', scene: 's', at: [9, 0, 0], fired: true }).action === 'fill',
       'two real anchors in one scene are still filled');
  }

  head('F. NO WINDOW SHRANK — the real story.json, against the flat 60/75/90 it replaces');
  {
    const { readFileSync } = await import('fs');
    const S = JSON.parse(readFileSync(new URL('../public/game/story.json', import.meta.url), 'utf8'));
    // The slack the harness passes per call site, and the flat window it used to pass.
    const SLACK = { 'ch1.open': [40, 40], 'ch1.done': [75, 90], 'ch2.road': [40, 40] };
    const CH2 = (b) => b.id.startsWith('ch2.');
    let worst = null, shrank = 0;
    for (const b of S.beats || []) {
      const [slack, old] = SLACK[b.id] || (CH2(b) ? [75, 75] : [60, 60]);
      const now = beatBudgetMs(b, slack * 1000);
      if (now < old * 1000) shrank++;
      const gain = now - old * 1000;
      if (!worst || gain > worst.gain) worst = { id: b.id, gain, now, old: old * 1000 };
    }
    ok(shrank === 0, 'every beat\'s window is >= the flat one it replaces (nothing got tighter)', shrank);
    ok(worst.id === 'ch2.landing' && worst.gain === 38450,
       'the biggest gain is ch2.landing: 75.0 s -> 113.5 s, and it is the beat that failed', worst);
  }

  head('G. --grace=0 is a real A/B — with the grace off, the race is red again');
  {
    const io = fakeIo({ busyFrom: 68000, ledgerAt: 77650 });
    const r = await awaitBeat(io, 'ch1.hush', { budgetMs: 69650, graceMs: 0 });
    ok(r.fired === false, 'graceMs 0 reproduces the false red on demand', r);
  }

  console.log('\n' + '='.repeat(64));
  console.log(`playthrough_lib --selftest: ${pass} passed, ${fail} failed`);
  console.log('='.repeat(64));
  process.exit(fail ? 1 : 0);
}
if (process.argv.includes('--selftest')) selftest();
