// music.js — window.Music: THE SOUNDTRACK (music agent).
//
//   Music.scene(key)          play whatever public/game/music.json maps that scene to
//   Music.play(id, opts)      play a track id directly
//   Music.stop(opts)          fade out and release
//   Music.battle(on)          manual battle hook (normally self-arming, see below)
//   Music.sting(id)           one-shot, non-looping, then resume what was playing
//   Music.setVolume(v) / Music.mute(b) / Music.current() / Music._debug()
//
// FOUR PROBLEMS THIS MODULE EXISTS TO SOLVE, in the order they bite:
//
// 1. AUTOPLAY. No browser will start audio before a user gesture. So nothing is
//    created at load — no AudioContext, no fetch, no decode. The scene's track is
//    remembered as `pending` and the whole engine boots on the first keydown or
//    pointerdown. Before that gesture this file is inert and silent, and it never
//    logs an error for being inert: that is the normal state of a page nobody has
//    touched yet.
//
// 2. SCENE TRANSITIONS. There are now TWO ways a scene can change, and this module
//    handles both — the difference between them is audible, and the better one is
//    the default.
//
//    (a) IN-PLACE SWAP (the default since the transitions refactor). play3d
//        disposes the old bundle, loads the new one and fires ONE window
//        CustomEvent, 'eb-scene' {scene, prev, spawn}. Nothing is torn down: this
//        module, its AudioContext, its GainNodes and the sounding
//        AudioBufferSourceNode all survive the doorway. The handler is one line —
//        Music.scene(key) — and when the new scene maps to the SAME track, start()
//        sees a live voice with that id and RETURNS WITHOUT TOUCHING IT. The music
//        is not resumed, not re-seeked, not crossfaded and not faded: it is the
//        same node, still playing, and the seam is not merely inaudible but
//        physically absent. A different track gets the normal 1.5 s crossfade.
//
//    (b) FULL PAGE LOAD — still what a refresh, a deep link and ?reload=1 do, and
//        the fallback if the swap ever throws. location.assign() tears down the
//        whole JS world, and a naive implementation would restart the town theme
//        from bar one at every doorway. So the playhead is written to
//        sessionStorage continuously and on pagehide, and on the next load, if the
//        new scene maps to the SAME track, playback resumes at position + the
//        wall-clock time the page load itself cost. It behaves as though it never
//        stopped. This machinery is UNCHANGED and must stay: it is what makes the
//        fallback survivable, and (a) does not use it at all.
//
// 3. LOOPING. Game music loops mid-track, not from zero — the intro plays once and
//    the body repeats forever. That is `loopStart`/`loopEnd` on an
//    AudioBufferSourceNode, which is sample-exact and genuinely gapless (no timer,
//    no re-trigger, no seam). It is also why this is Web Audio and not <audio>.
//
// 4. THE BATTLE SWAP. The field theme does not restart after a fight. It is paused
//    at its exact position, the battle theme plays, the victory fanfare plays ONCE,
//    and then the field theme picks up where it left off. That is the behaviour the
//    Final Fantasy games trained everyone to expect and its absence is felt
//    immediately even by players who could not name what was wrong.
//
// NO-OPS COMPLETELY, and says why in _debug(), when: there is no window, no
// AudioContext, no music.json, no file for a track, or no user gesture yet. Every
// failure path is a silent game, never a broken one. `?nomusic=1` forces it off.
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  const LS_KEY = 'emberbrook-music';        // {volume, muted} — survives the browser
  const SS_KEY = 'emberbrook-music-pos';    // {trackId, position, timestamp} — survives the page load
  const DATA_URL = 'game/music.json';

  const DEF = {
    crossfadeMs: 1500,      // equal-power, both directions
    battleFadeMs: 400,      // the swap into a fight is a cut, not a dissolve
    resumeFadeMs: 700,      // coming back out of a fight
    stingFadeMs: 700,       // tail fade on non-looping stingers
    volume: 0.7,
    maxCached: 4,           // decoded AudioBuffers held at once (see CACHE below)
  };

  // A decoded 150-second stereo track is ~53 MB of float32 in memory. Five of those
  // is a quarter of a gigabyte for a game whose whole point is running on a couch
  // machine, so decoded buffers are cached with a cap and the least-recently-used
  // one is dropped. Anything currently sounding or currently parked (the field theme
  // waiting out a battle) is pinned and never evicted.
  const CACHE = new Map();   // id -> {buffer, used}
  let cacheTick = 0;

  let cfg = null;            // music.json once fetched
  let ctx = null;            // AudioContext — created on the unlock gesture, never before
  let master = null;         // master GainNode
  let unlocked = false;
  let booting = false;
  let disabled = false;
  let pending = null;        // {id, opts} wanted before the gesture arrived
  let voice = null;          // the sounding field/battle voice
  let sting = null;          // the sounding one-shot, if any
  let parked = null;         // {id, position} the field theme waiting out a battle/sting
  let sceneKey = null;
  let lastError = null;
  let battleOn = false;
  let battleWatch = null;
  let battleSeen = null;
  let saveTimer = null;

  const now = () => (ctx ? ctx.currentTime : 0);
  const num = (v, d) => (typeof v === 'number' && isFinite(v)) ? v : d;
  const def = (k) => num(cfg && cfg.defaults && cfg.defaults[k], DEF[k]);

  function warn(e, where) { lastError = where + ': ' + (e && e.message ? e.message : e); }

  // ---- settings ------------------------------------------------------------
  // Volume lives in localStorage because the pause menu is another agent's file and
  // this module must not touch it. When menu integration happens it can call
  // Music.setVolume() and the value is already persisted the way the menu would
  // want it. M is play3d's dev-settings key, so there is deliberately no key bound
  // here — the API is the surface, not a hotkey.
  // MUTED BY DEFAULT (user ruling 2026-08-01): a fresh profile — which is every
  // agent's headless Chrome — launches silent, so automated testing never reaches
  // the user's speakers. Unmuting via the M menu persists for the user's browser.
  let settings = { volume: DEF.volume, muted: true };
  try {
    const raw = window.localStorage && localStorage.getItem(LS_KEY);
    if (raw) {
      const s = JSON.parse(raw);
      if (s && typeof s === 'object') {
        settings.volume = Math.max(0, Math.min(1, num(s.volume, DEF.volume)));
        settings.muted = !!s.muted;
      }
    }
  } catch (e) { /* private mode / disabled storage — defaults are fine */ }

  function saveSettings() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(settings)); } catch (e) { /* ignore */ }
  }

  // The muted-by-default state needs an on-screen affordance (user ruling): a small
  // corner chip, visible only while muted, that is itself the unmute control — a
  // click is also the autoplay gesture the AudioContext wants, so one tap does both.
  // DOM-guarded like the eb-scene listener: suites boot this module without a document.
  let _chip = null;
  function muteChip() {
    if (typeof document === 'undefined' || !document.body || !document.createElement) return;
    if (!settings.muted) { if (_chip) _chip.style.display = 'none'; return; }
    if (!_chip) {
      _chip = document.createElement('div');
      _chip.textContent = '🔇 music off — click to unmute (or press M)';
      _chip.style.cssText = 'position:fixed;right:10px;bottom:10px;z-index:2000;' +
        'background:rgba(10,16,48,.82);color:#dfe6ff;border:1px solid #4a5bd0;' +
        'border-radius:16px;padding:5px 12px;font:12px system-ui;cursor:pointer;' +
        'user-select:none';
      _chip.addEventListener('click', () => { if (window.Music) window.Music.mute(false); });
      document.body.appendChild(_chip);
    }
    _chip.style.display = '';
  }
  if (typeof document !== 'undefined' && document.addEventListener) {
    (document.readyState === 'loading')
      ? document.addEventListener('DOMContentLoaded', muteChip)
      : setTimeout(muteChip, 0);
  }
  function masterTarget() { return settings.muted ? 0 : settings.volume; }

  // ---- the scene -> track map ---------------------------------------------
  // Resolution is data-driven and ordered so precedence is a property of music.json,
  // not of this code: exact scene match, then the `rules` list in file order (first
  // match wins — which is how "-int" beats "del-"), then defaults.track.
  function trackForScene(key) {
    if (!cfg || !key) return null;
    const s = cfg.scenes || {};
    if (Object.prototype.hasOwnProperty.call(s, key)) return s[key];   // null = deliberate silence
    for (const r of (cfg.rules || [])) {
      if (r.suffix && key.slice(-r.suffix.length) === r.suffix) return r.track;
      if (r.prefix && key.slice(0, r.prefix.length) === r.prefix) return r.track;
      if (r.equals && key === r.equals) return r.track;
    }
    return (cfg.defaults && cfg.defaults.track) || null;
  }
  function slot(name) { return (cfg && cfg.slots && cfg.slots[name]) || null; }
  function track(id) { return (cfg && cfg.tracks && cfg.tracks[id]) || null; }

  // ---- loading -------------------------------------------------------------
  async function loadConfig() {
    if (cfg) return cfg;
    try {
      // no-cache = revalidate with the server every load (304 when unchanged).
      // force-cache here once pinned a stale map across refreshes — the scene
      // mapping is a live tuning surface and must never be served stale. The
      // TRACK fetches below keep force-cache: audio is big and rarely changes.
      const res = await fetch(DATA_URL, { cache: 'no-cache' });
      if (!res.ok) throw new Error('music.json ' + res.status);
      cfg = await res.json();
    } catch (e) { warn(e, 'config'); cfg = { tracks: {}, scenes: {}, rules: [] }; }
    return cfg;
  }

  function pinned() {
    const p = new Set();
    if (voice) p.add(voice.id);
    if (sting) p.add(sting.id);
    if (parked) p.add(parked.id);
    return p;
  }

  async function buffer(id) {
    const t = track(id);
    if (!t || !t.file) return null;
    const hit = CACHE.get(id);
    if (hit) { hit.used = ++cacheTick; return hit.buffer; }
    let buf;
    try {
      const res = await fetch(t.file, { cache: 'force-cache' });
      if (!res.ok) throw new Error(t.file + ' ' + res.status);
      const bytes = await res.arrayBuffer();
      buf = await new Promise((ok, no) => {
        // callback form: Safari still wants it, and it is a superset of the promise form
        const p = ctx.decodeAudioData(bytes, ok, no);
        if (p && p.then) p.then(ok, no);
      });
    } catch (e) { warn(e, 'decode ' + id); return null; }
    bakeLoopXfade(buf, t);
    CACHE.set(id, { buffer: buf, used: ++cacheTick });
    const keep = pinned();
    while (CACHE.size > def('maxCached')) {
      let worst = null;
      for (const [k, v] of CACHE) if (!keep.has(k) && (!worst || v.used < CACHE.get(worst).used)) worst = k;
      if (!worst) break;
      CACHE.delete(worst);
    }
    return buf;
  }

  // Blend the seam INTO the samples, so the loop can stay a native gapless
  // AudioBufferSourceNode loop and still not click.
  //
  // The jump is loopEnd -> loopStart, so the ear expects to keep hearing whatever
  // naturally followed loopEnd. Overwriting the first `loopXfade` seconds at
  // loopStart with an equal-power blend of (what follows loopEnd) fading out into
  // (what is really at loopStart) fading in gives exactly that: the join becomes a
  // short crossfade instead of a cut. The only cost is that the FIRST pass through
  // loopStart hears the blend too, which at a fifth of a second nobody notices.
  // Done in place — decodeAudioData hands us a buffer we own, and loopStart+xfade
  // is always far below loopEnd, so there is no aliasing.
  function bakeLoopXfade(buf, t) {
    try {
      const x = num(t && t.loopXfade, 0);
      const a = num(t && t.loopStart, 0), b = num(t && t.loopEnd, 0);
      if (!(x > 0) || !(b > a)) return buf;
      const sr = buf.sampleRate;
      const X = Math.floor(x * sr), A = Math.round(a * sr), B = Math.round(b * sr);
      if (X < 8 || B + X > buf.length || A + X >= B) return buf;
      for (let ch = 0; ch < buf.numberOfChannels; ch++) {
        const d = buf.getChannelData(ch);
        for (let i = 0; i < X; i++) {
          const w = (i / X) * Math.PI / 2;
          d[A + i] = d[B + i] * Math.cos(w) + d[A + i] * Math.sin(w);
        }
      }
    } catch (e) { warn(e, 'xfade'); }
    return buf;
  }

  // ---- gain shaping --------------------------------------------------------
  // Equal power, not linear: two linear ramps crossing at 0.5 produce an audible
  // dip in the middle of the crossfade because power goes as the square of
  // amplitude. sin/cos quarter-curves keep the sum constant, which is what makes a
  // 1.5 s dissolve read as one continuous piece of music rather than two.
  function ramp(param, to, ms, shape) {
    const t0 = now(), dur = Math.max(0.001, ms / 1000);
    let from = to;
    try { from = param.value; } catch (e) { /* ignore */ }
    try { param.cancelScheduledValues(t0); } catch (e) { /* ignore */ }
    if (shape === 'linear' || ms <= 0) {
      try { param.setValueAtTime(from, t0); param.linearRampToValueAtTime(to, t0 + dur); }
      catch (e) { try { param.value = to; } catch (e2) { /* ignore */ } }
      return dur;
    }
    const n = 48, curve = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const x = i / (n - 1);
      // rising uses sin, falling uses cos; both are the same equal-power quarter arc
      const k = (to >= from) ? Math.sin(x * Math.PI / 2) : Math.cos(x * Math.PI / 2);
      curve[i] = from + (to - from) * (to >= from ? k : (1 - k));
    }
    curve[n - 1] = to;
    try { param.setValueCurveAtTime(curve, t0, dur); }
    catch (e) {
      try { param.setValueAtTime(from, t0); param.linearRampToValueAtTime(to, t0 + dur); }
      catch (e2) { /* ignore */ }
    }
    return dur;
  }

  // ---- voices --------------------------------------------------------------
  // Wall-clock and media time are the same thing here (playbackRate is always 1), so
  // the playhead is arithmetic rather than something that has to be polled off the
  // node — which matters because it has to be correct at the instant of a pagehide.
  function position(v) {
    if (!v || !ctx) return 0;
    let p = v.offset + (now() - v.startedAt);
    const t = v.track;
    if (v.looping && t && num(t.loopEnd, 0) > num(t.loopStart, 0)) {
      const a = num(t.loopStart, 0), b = num(t.loopEnd, 0);
      if (p > b) p = a + ((p - a) % (b - a));
    } else if (v.buffer && p > v.buffer.duration) {
      p = v.buffer.duration;
    }
    return Math.max(0, p);
  }

  // Clamp a resume position into the loop body. A saved position can legitimately
  // land past loopEnd (the page load's own elapsed time is added to it), and a
  // start offset past the buffer is silence.
  function wrap(t, p, dur) {
    const a = num(t.loopStart, 0), b = num(t.loopEnd, 0);
    if (b > a && p > b) return a + ((p - a) % (b - a));
    if (p >= dur) return b > a ? a : 0;
    return Math.max(0, p);
  }

  function makeVoice(id, buf, opts) {
    const t = track(id) || {};
    const loopEnd = num(t.loopEnd, 0) > 0 ? Math.min(t.loopEnd, buf.duration) : 0;
    const looping = opts.loop !== false && t.loop !== false && loopEnd > num(t.loopStart, 0);
    const g = ctx.createGain();
    g.gain.value = opts.fadeMs > 0 ? 0 : (num(t.gain, 1) * 1);
    g.connect(master);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    if (looping) { src.loop = true; src.loopStart = num(t.loopStart, 0); src.loopEnd = loopEnd; }
    src.connect(g);
    const off = looping ? wrap(t, num(opts.offset, 0), buf.duration)
      : Math.min(Math.max(0, num(opts.offset, 0)), Math.max(0, buf.duration - 0.01));
    const full = num(t.gain, 1);
    try { src.start(0, off); } catch (e) { warn(e, 'start ' + id); return null; }
    const v = { id, src, gain: g, track: t, buffer: buf, looping, offset: off, startedAt: now(), full, dead: false };
    if (opts.fadeMs > 0) ramp(g.gain, full, opts.fadeMs);
    else { try { g.gain.value = full; } catch (e) { /* ignore */ } }
    return v;
  }

  function release(v, ms) {
    if (!v || v.dead) return;
    v.dead = true;
    const dur = ms > 0 ? ramp(v.gain.gain, 0, ms) : 0;
    const stop = () => { try { v.src.stop(); } catch (e) { /* ignore */ } try { v.gain.disconnect(); } catch (e) { /* ignore */ } };
    if (dur > 0) setTimeout(stop, ms + 60); else stop();
  }

  // ---- the engine ----------------------------------------------------------
  function ensureCtx() {
    if (ctx) return true;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) { lastError = 'no AudioContext'; return false; }
    try {
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = masterTarget();
      master.connect(ctx.destination);
    } catch (e) { warn(e, 'context'); ctx = null; return false; }
    return true;
  }

  async function start(id, opts) {
    opts = opts || {};
    if (disabled || !id) return false;
    if (!unlocked) { pending = { id, opts }; return false; }
    if (!ensureCtx()) return false;
    await loadConfig();
    if (ctx.state === 'suspended') { try { await ctx.resume(); } catch (e) { /* ignore */ } }
    if (voice && voice.id === id && !voice.dead && opts.restart !== true) return true;
    const buf = await buffer(id);
    if (!buf) return false;
    const old = voice;
    const fade = num(opts.fadeMs, def('crossfadeMs'));
    // The resume offset is resolved HERE, not at boot. Between the page load and the
    // gesture that unlocks audio there can be seconds of real time — a fresh page has
    // no user activation, so every scene transition has to wait for the player's next
    // keypress — and a position frozen at boot would resume that many seconds behind
    // where the music should be. Reading it at the moment sound actually starts is
    // what keeps the continuity honest.
    let offset = opts.offset;
    if (opts.fromSaved) {
      const s = savedPos();
      offset = (s && s.trackId === id) ? s.position : 0;
    }
    const v = makeVoice(id, buf, { offset, fadeMs: opts.seamless ? 0 : fade, loop: opts.loop });
    if (!v) return false;
    voice = v;
    if (old) release(old, opts.seamless ? 0 : fade);
    persist();
    if (id !== slot('battle')) prewarm();
    return true;
  }

  // Decode the fight cues while the field theme is playing and nothing is urgent.
  // Measured: a cold 3.5 MB battle track costs about a second between the encounter
  // firing and the battle theme arriving. Nothing goes silent in that gap (the field
  // voice is only released once the new buffer exists) but the swap lands late, on
  // the one transition in the game that most needs to feel immediate. The cues are
  // small in number and the cache cap fits exactly: field + battle + the two stings.
  let prewarmed = false;
  function prewarm() {
    if (prewarmed || !ctx || disabled) return;
    prewarmed = true;
    setTimeout(async () => {
      for (const n of ['battle', 'victory', 'defeat']) {
        const id = slot(n);
        if (id && !CACHE.has(id)) { try { await buffer(id); } catch (e) { /* ignore */ } }
      }
    }, 2500);
  }

  // ---- persistence across the full page load -------------------------------
  function persist() {
    try {
      if (!voice || voice.dead || battleOn) return;
      sessionStorage.setItem(SS_KEY, JSON.stringify({
        trackId: voice.id, position: +position(voice).toFixed(3), timestamp: Date.now(),
      }));
    } catch (e) { /* ignore */ }
  }
  function savedPos() {
    try {
      const raw = sessionStorage.getItem(SS_KEY);
      if (!raw) return null;
      const s = JSON.parse(raw);
      if (!s || !s.trackId) return null;
      // Add the wall time the page load itself consumed, so the theme comes back in
      // where it WOULD have been rather than where it was when the page died. This
      // is the whole trick behind a doorway not interrupting the music.
      const gap = Math.max(0, (Date.now() - num(s.timestamp, Date.now())) / 1000);
      return { trackId: s.trackId, position: num(s.position, 0) + Math.min(gap, 30) };
    } catch (e) { return null; }
  }

  // ---- battle flow ---------------------------------------------------------
  // Battle.start()'s promise does not settle until the outro panel has been read and
  // faded, which is far too late to begin a victory fanfare — the fanfare belongs
  // ON the word "Victory". Battle.last is assigned the moment the engine returns,
  // BEFORE screen.outro() runs, so a light poll on its identity catches the outcome
  // at exactly the right frame. The promise is still awaited, as the authority on
  // when the fight is really over and for the case where it resolves null (no
  // party, no kernel, already running) and the field theme must simply come back.
  function battleBegin() {
    if (battleOn) return;
    const id = slot('battle');
    battleOn = true;
    if (voice && !voice.dead) parked = { id: voice.id, position: position(voice) };
    if (sting) { release(sting, 200); sting = null; }
    if (!id) { if (voice) { release(voice, def('battleFadeMs')); voice = null; } return; }
    start(id, { fadeMs: def('battleFadeMs'), restart: true, offset: 0 });
    battleSeen = (window.Battle && window.Battle.last) || null;
    clearInterval(battleWatch);
    battleWatch = setInterval(() => {
      const B = window.Battle;
      if (!B) return;
      if (B.last && B.last !== battleSeen) {
        battleSeen = B.last;
        clearInterval(battleWatch); battleWatch = null;
        outcome(B.last.outcome);
      }
    }, 100);
  }

  function outcome(kind) {
    const id = slot(kind === 'defeat' ? 'defeat' : kind === 'victory' ? 'victory' : null);
    if (voice) { release(voice, 250); voice = null; }
    if (!id) return;
    playSting(id, { after: () => { /* the promise handler brings the field back */ } });
  }

  function battleEnd() {
    if (!battleOn) return;
    battleOn = false;
    clearInterval(battleWatch); battleWatch = null;
    const back = parked; parked = null;
    if (!back) { if (voice && voice.id === slot('battle')) { release(voice, def('resumeFadeMs')); voice = null; } return; }
    // If a fanfare is still ringing, the field theme waits for it — the resume is
    // chained off the stinger's end rather than crossfaded over it.
    const resume = () => start(back.id, { offset: back.position, fadeMs: def('resumeFadeMs'), restart: true });
    if (sting && !sting.dead) { sting.after = resume; }
    else { if (voice && voice.id === slot('battle')) { release(voice, def('resumeFadeMs')); voice = null; } resume(); }
  }

  async function playSting(id, opts) {
    opts = opts || {};
    if (disabled || !unlocked || !ensureCtx()) return false;
    await loadConfig();
    const t = track(id);
    const buf = await buffer(id);
    if (!buf) { if (opts.after) opts.after(); return false; }
    if (sting) release(sting, 150);
    const v = makeVoice(id, buf, { offset: 0, fadeMs: 0, loop: false });
    if (!v) { if (opts.after) opts.after(); return false; }
    v.after = opts.after || null;
    sting = v;
    // Trimmed stingers end on a frame boundary rather than a musical one, so the
    // tail is faded here instead of being baked into the file.
    const dur = num(t && t.duration, buf.duration);
    const fo = num(t && t.fadeOutMs, def('stingFadeMs')) / 1000;
    if (dur > fo) setTimeout(() => { if (sting === v && !v.dead) ramp(v.gain.gain, 0, fo * 1000); }, (dur - fo) * 1000);
    setTimeout(() => {
      if (sting !== v) return;
      const after = v.after;
      release(v, 0); sting = null;
      if (after) after();
    }, dur * 1000 + 80);
    return true;
  }

  // Self-arming. The coordinator only has to add the script tag; this finds
  // window.Battle whenever it shows up (load order between modules is not this
  // file's business) and wraps start() defensively — a throw inside the wrapper can
  // never stop a fight from happening.
  function armBattle() {
    const B = window.Battle;
    if (!B || B.__musicArmed || typeof B.start !== 'function') return false;
    const orig = B.start;
    B.start = function () {
      let p;
      try { battleBegin(); } catch (e) { warn(e, 'battleBegin'); }
      try { p = orig.apply(this, arguments); }
      catch (e) { try { battleEnd(); } catch (e2) { /* ignore */ } throw e; }
      return Promise.resolve(p).then(
        (r) => { try { battleEnd(); } catch (e) { warn(e, 'battleEnd'); } return r; },
        (e) => { try { battleEnd(); } catch (e2) { /* ignore */ } throw e; }
      );
    };
    B.__musicArmed = true;
    return true;
  }

  // ---- unlock --------------------------------------------------------------
  function unlock() {
    if (unlocked || disabled) return;
    unlocked = true;
    for (const ev of ['keydown', 'pointerdown', 'touchstart', 'mousedown']) {
      window.removeEventListener(ev, unlock, true);
    }
    if (!ensureCtx()) return;
    if (ctx.state === 'suspended') { try { ctx.resume(); } catch (e) { /* ignore */ } }
    const p = pending; pending = null;
    if (p) start(p.id, p.opts);
  }

  // ---- boot ----------------------------------------------------------------
  // Decides WHAT should be playing without starting anything. The scene key is read
  // from the URL by this module itself (play3d's own `?scene=` with the same
  // default), so integration is one script tag and no edit to play3d.html.
  async function boot() {
    if (booting || disabled) return;
    booting = true;
    let q = null;
    try { q = new URLSearchParams(location.search); } catch (e) { /* ignore */ }
    if (q && (q.get('nomusic') === '1' || q.get('music') === '0')) { disabled = true; lastError = 'disabled by url'; return; }
    if (window.__NOMUSIC) { disabled = true; lastError = 'disabled by flag'; return; }
    sceneKey = (q && q.get('scene')) || 'dellhollow3d';
    await loadConfig();
    const id = trackForScene(sceneKey);

    // THE CONTINUITY DECISION. Same track as the page we just came from -> resume at
    // the saved playhead with no fade at all (`seamless`), because a fade here would
    // announce the very transition we are trying to hide. Different track -> normal
    // crossfade-in from zero.
    const saved = savedPos();
    const opts = (saved && id && saved.trackId === id)
      ? { fromSaved: true, seamless: true }
      : { fadeMs: def('crossfadeMs') };
    if (id) start(id, opts);

    for (const ev of ['keydown', 'pointerdown', 'touchstart', 'mousedown']) {
      window.addEventListener(ev, unlock, true);
    }
    // EAGER RESUME (2026-07-31, user: doors "pause" the music). Scene changes are
    // full page loads, and a fresh page normally can't sound until a gesture — so
    // every door inserted load+first-keypress of silence. Chrome grants autoplay
    // to origins with media engagement (localhost earns it within minutes of
    // play), so: TRY to run the context now; if the browser leaves it suspended,
    // the gesture path above remains armed and nothing changed. When it works,
    // the only remaining gap is the page load itself.
    (function eager() {
      if (unlocked || disabled) return;
      try {
        if (!ensureCtx()) return;
        const check = () => { if (!unlocked && ctx && ctx.state === 'running') unlock(); };
        if (ctx.state === 'suspended') {
          const pr = ctx.resume(); if (pr && pr.then) pr.then(check, () => { /* blocked: gesture path stands */ });
          setTimeout(check, 250);
        } else check();
      } catch (e) { /* gesture path stands */ }
    })();
    // pagehide is the one that actually fires on a bfcache/navigation teardown;
    // beforeunload and visibilitychange are belt and braces, and the 1 s timer is
    // the net under all three for a tab that is killed outright.
    for (const ev of ['pagehide', 'beforeunload']) window.addEventListener(ev, persist);
    document.addEventListener('visibilitychange', persist);
    saveTimer = setInterval(persist, 1000);

    if (!armBattle()) {
      let tries = 0;
      const t = setInterval(() => { if (armBattle() || ++tries > 40) clearInterval(t); }, 250);
    }
  }

  // ---- the in-place scene swap ---------------------------------------------
  // play3d's ONE transition event. Registered unconditionally at load (not inside
  // boot) so it works even in the states where boot() bails, and it is a plain
  // delegation to the public API — the continuity is a property of start(), not of
  // anything special done here. Deliberately does NOT persist(): the saved playhead
  // is for the page-load path, and writing it on a door would only make the
  // fallback's guess worse if the tab were killed mid-swap.
  //
  // Guarded against a battle for defence in depth only: play3d holds a UILOCK for
  // the whole swap and phys() cannot reach sgTick under one, so a door mid-fight is
  // unreachable by construction. If it ever became reachable, swapping the battle
  // theme out from under a fight is the wrong answer — the parked field theme is a
  // promise to come back, and it is kept.
  window.addEventListener('eb-scene', (ev) => {
    try {
      const key = ev && ev.detail && ev.detail.scene;
      if (!key || disabled) return;
      sceneKey = key;
      if (battleOn) return;
      Music.scene(key);
    } catch (e) { warn(e, 'eb-scene'); }
  });

  // ---- public API ----------------------------------------------------------
  const Music = window.Music = {
    version: 1,

    scene(key) {
      sceneKey = key;
      return loadConfig().then(() => {
        const id = trackForScene(key);
        if (!id) { Music.stop(); return null; }
        return start(id, { fadeMs: def('crossfadeMs') }).then(() => id);
      });
    },

    // What WOULD this scene play? Pure lookup, starts nothing — the map is data and
    // anything (a test, the menu, a debug overlay) is allowed to ask it a question.
    trackFor(key) { return cfg ? trackForScene(key) : null; },
    ready() { return loadConfig().then(() => true); },

    play(id, opts) { return start(id, opts || {}); },
    sting(id, after) { return playSting(id || slot('menu-stinger'), { after }); },

    stop(opts) {
      opts = opts || {};
      const ms = num(opts.fadeMs, def('crossfadeMs'));
      if (voice) { release(voice, ms); voice = null; }
      if (sting) { release(sting, ms); sting = null; }
      try { sessionStorage.removeItem(SS_KEY); } catch (e) { /* ignore */ }
      return true;
    },

    // Manual battle hook, for the case where wrapping Battle.start is not wanted
    // or a caller drives battles some other way. Music.battle(true) ducks and swaps;
    // Music.battle(false) resumes the field theme at its parked position.
    battle(on) { if (on) battleBegin(); else battleEnd(); return battleOn; },
    // Fire an outcome sting by hand (Music.outcome('victory')).
    outcome(kind) { outcome(kind); return true; },

    setVolume(v) {
      settings.volume = Math.max(0, Math.min(1, num(v, DEF.volume)));
      settings.muted = false;
      saveSettings();
      if (master) ramp(master.gain, masterTarget(), 120, 'linear');
      muteChip();
      return settings.volume;
    },
    mute(b) {
      settings.muted = (b === undefined) ? !settings.muted : !!b;
      saveSettings();
      if (master) ramp(master.gain, masterTarget(), 120, 'linear');
      muteChip();
      return settings.muted;
    },
    volume() { return settings.volume; },
    muted() { return settings.muted; },

    current() {
      return voice && !voice.dead
        ? { id: voice.id, position: +position(voice).toFixed(2), looping: voice.looping,
            mood: (voice.track && voice.track.mood) || null }
        : null;
    },

    _debug() {
      return {
        version: 1, disabled, unlocked, scene: sceneKey,
        mapped: cfg ? trackForScene(sceneKey) : null,
        ctx: ctx ? ctx.state : null,
        current: Music.current(),
        sting: sting && !sting.dead ? sting.id : null,
        battle: battleOn, parked: parked ? { id: parked.id, position: +parked.position.toFixed(2) } : null,
        armed: !!(window.Battle && window.Battle.__musicArmed),
        cached: [...CACHE.keys()], tracks: cfg ? Object.keys(cfg.tracks || {}) : [],
        saved: savedPos(), volume: settings.volume, muted: settings.muted,
        error: lastError,
      };
    },
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
