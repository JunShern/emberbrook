'use strict';
/* ============================================================
   ENGINE — screen, camera, fx, particles, audio, networking
   ============================================================ */

const Screen = {
  canvas: null, ctx: null, cw: 0, ch: 0, dpr: 1,
  init() {
    this.canvas = document.getElementById('game');
    this.ctx = this.canvas.getContext('2d');
    window.addEventListener('resize', () => this.resize());
    this.resize();
  },
  resize() {
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.cw = window.innerWidth; this.ch = window.innerHeight;
    this.canvas.width = this.cw * this.dpr;
    this.canvas.height = this.ch * this.dpr;
    this.canvas.style.width = this.cw + 'px';
    this.canvas.style.height = this.ch + 'px';
  },
};

let time = 0;

const Camera = {
  x: 0, y: 0, zoom: 3,
  target: null,           // {x,y,zoom} — cutscene override
  update(dt, focuses, mapW, mapH) {
    const { cw, ch } = Screen;
    let tx, ty, tz;
    if (this.target) {
      tx = this.target.x; ty = this.target.y; tz = this.target.zoom || 3;
    } else if (focuses.length === 0) {
      tx = mapW / 2; ty = mapH / 2; tz = ch / 300;
    } else {
      const xs = focuses.map(p => p.x), ys = focuses.map(p => p.y);
      const minx = Math.min(...xs), maxx = Math.max(...xs);
      const miny = Math.min(...ys), maxy = Math.max(...ys);
      tx = (minx + maxx) / 2; ty = (miny + maxy) / 2 - 8;
      tz = Math.min(cw / ((maxx - minx) + 230), ch / ((maxy - miny) + 210));
      tz = Math.max(ch / 470, Math.min(ch / 240, tz));
    }
    const k = Math.min(1, dt * (this.target ? 2.4 : 4));
    this.zoom += (tz - this.zoom) * k;
    this.x += (tx - this.x) * k;
    this.y += (ty - this.y) * k;
    const vw = cw / this.zoom, vh = ch / this.zoom;
    this.x = Math.max(vw / 2, Math.min(mapW - vw / 2, this.x));
    this.y = Math.max(vh / 2, Math.min(mapH - vh / 2, this.y));
    if (vw >= mapW) this.x = mapW / 2;
    if (vh >= mapH) this.y = mapH / 2;
  },
  worldToScreen(wx, wy) {
    return [(wx - this.x) * this.zoom + Screen.cw / 2, (wy - this.y) * this.zoom + Screen.ch / 2];
  },
};

/* ---------- screen effects ---------- */
const FX = {
  shake: 0, flash: 0,
  letterbox: 0, letterboxTarget: 0,
  desat: 0, desatTarget: 0,
  fade: 0, fadeTarget: 0,       // black fade 0..1
  update(dt) {
    this.shake = Math.max(0, this.shake - dt * 4);
    this.flash = Math.max(0, this.flash - dt * 1.4);
    this.letterbox += (this.letterboxTarget - this.letterbox) * Math.min(1, dt * 3);
    this.desat += (this.desatTarget - this.desat) * Math.min(1, dt * 1.2);
    this.fade += (this.fadeTarget - this.fade) * Math.min(1, dt * 2);
  },
  // call after world render, before UI
  post(ctx) {
    const { cw, ch } = Screen;
    if (this.desat > 0.01) {
      ctx.save();
      ctx.globalCompositeOperation = 'saturation';
      ctx.fillStyle = `rgba(128,128,128,${this.desat})`;
      ctx.fillRect(0, 0, cw, ch);
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = `rgba(150,158,170,${this.desat * 0.16})`;
      ctx.fillRect(0, 0, cw, ch);
      ctx.restore();
    }
    if (this.flash > 0.01) {
      ctx.fillStyle = `rgba(255,248,235,${Math.min(1, this.flash)})`;
      ctx.fillRect(0, 0, cw, ch);
    }
  },
  bars(ctx) {
    if (this.letterbox < 0.01) return;
    const { cw, ch } = Screen;
    const h = ch * 0.11 * this.letterbox;
    ctx.fillStyle = '#0a0810';
    ctx.fillRect(0, 0, cw, h);
    ctx.fillRect(0, ch - h, cw, h);
  },
  black(ctx) {
    if (this.fade < 0.01) return;
    ctx.fillStyle = `rgba(8,6,12,${this.fade})`;
    ctx.fillRect(0, 0, Screen.cw, Screen.ch);
  },
};

/* ---------- particles ---------- */
const Particles = {
  list: [],
  spawn(p) { this.list.push(Object.assign({ age: 0 }, p)); },
  burst(n, maker) { for (let i = 0; i < n; i++) this.spawn(maker(i)); },
  update(dt) {
    for (let i = this.list.length - 1; i >= 0; i--) {
      const p = this.list[i];
      p.age += dt; p.life -= dt;
      switch (p.kind) {
        case 'moth':
          p.vx += Math.sin(p.age * 7 + p.seed) * 60 * dt;
          p.vy += (Math.cos(p.age * 5.3 + p.seed) * 40 - 12) * dt;
          p.vx *= 0.98; p.vy *= 0.98;
          p.x += p.vx * dt; p.y += p.vy * dt;
          break;
        case 'shard':
          p.vy -= 60 * dt;                    // light streams upward
          p.x += Math.sin(p.age * 3 + p.seed) * 14 * dt;
          p.y += p.vy * dt;
          break;
        default:
          p.x += (p.vx || 0) * dt + Math.sin(p.age * 2 + i) * (p.sway || 0) * dt;
          p.y += (p.vy || 0) * dt;
      }
      if (p.life <= 0) this.list.splice(i, 1);
    }
  },
  draw(ctx) {
    for (const p of this.list) {
      const a = Math.max(0, Math.min(1, p.life / (p.fadeOver || 1)));
      switch (p.kind) {
        case 'smoke':
          ctx.fillStyle = `rgba(210,205,200,${0.2 * a})`;
          ctx.beginPath(); ctx.arc(p.x, p.y, (p.r || 2) + p.age, 0, 7); ctx.fill();
          break;
        case 'mote':
          ctx.fillStyle = `rgba(240,190,110,${0.55 * a})`;
          ctx.fillRect(p.x, p.y, 1.6, 1.6);
          break;
        case 'sparkle': {
          ctx.fillStyle = `rgba(255,240,200,${a})`;
          const s = 1 + Math.sin(p.age * 10) * 0.6;
          ctx.fillRect(p.x - s / 2, p.y - s / 2, s, s);
          break;
        }
        case 'shard': {
          ctx.fillStyle = `rgba(250,220,160,${0.85 * a})`;
          ctx.fillRect(p.x, p.y, 1.6, 4.5);
          ctx.fillStyle = `rgba(255,255,240,${0.5 * a})`;
          ctx.fillRect(p.x, p.y + 1, 1.6, 1.6);
          break;
        }
        case 'moth': {
          const flap = Math.sin(p.age * 26 + p.seed) > 0 ? 1 : 2.2;
          ctx.fillStyle = `rgba(196,196,205,${0.8 * a})`;
          ctx.fillRect(p.x - flap, p.y, flap, 1.4);
          ctx.fillRect(p.x + 0.6, p.y, flap, 1.4);
          ctx.fillStyle = `rgba(140,140,152,${0.9 * a})`;
          ctx.fillRect(p.x, p.y - 0.4, 0.8, 2.2);
          break;
        }
        case 'leaf':
          ctx.fillStyle = p.c;
          ctx.globalAlpha = Math.min(1, p.life / 2) * 0.85;
          ctx.fillRect(p.x, p.y, 2, 2);
          ctx.globalAlpha = 1;
          break;
      }
    }
  },
};

/* ---------- audio: mood-based sequencer + sfx ---------- */
const AudioSys = {
  ctx: null, master: null, musicGain: null, started: false, musicOn: true,
  mood: 'festival', step: 0, nextT: 0,
  f(m) { return 440 * Math.pow(2, (m - 69) / 12); },
  init() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain(); this.master.gain.value = 0.9;
    const lp = this.ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 4200;
    this.master.connect(lp); lp.connect(this.ctx.destination);
    this.musicGain = this.ctx.createGain(); this.musicGain.gain.value = 0.9;
    this.musicGain.connect(this.master);
    this.nextT = this.ctx.currentTime + 0.1;
    setInterval(() => this.schedule(), 90);
    this.started = true;
    const hint = document.getElementById('musicHint');
    if (hint) hint.classList.add('gone');
  },
  setMood(m) { this.mood = m; this.step = 0; },
  note(m, t, dur, type, gain, detune) {
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = type; o.frequency.value = this.f(m);
    if (detune) o.detune.value = detune;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(this.musicGain);
    o.start(t); o.stop(t + dur + 0.05);
  },
  // Each mood is a song form: several 32-step sections (own chords + phrase
  // + texture flags), played in `form` order. Repeat passes vary (octave
  // lifts, added sparkle), so the loop point is minutes away, not seconds.
  MOODS: {
    // Emberwake festival — bright, quick, tambourine-ish tick
    festival: {
      stepDur: 0.26, tick: true,
      form: [0, 1, 2, 0, 3, 2, 1],
      sections: [
        { // A — the theme
          roots: [48, 45, 41, 43],
          chords: [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]],
          melody: [76, 0, 79, 76, 81, 0, 79, 0, 76, 74, 76, 0, 72, 0, 74, 76,
                   74, 0, 72, 74, 69, 0, 72, 0, 74, 76, 79, 0, 76, 0, 0, 0],
        },
        { // A' — theme with a lifted, questioning ending
          roots: [48, 45, 41, 43],
          chords: [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]],
          melody: [76, 0, 79, 76, 81, 0, 79, 0, 76, 74, 76, 0, 72, 0, 74, 76,
                   79, 0, 81, 79, 84, 0, 83, 0, 81, 79, 76, 0, 79, 0, 0, 0],
          arp: true,
        },
        { // B — bridge, rising through F and G
          roots: [41, 43, 40, 45],
          chords: [[53, 57, 60], [55, 59, 62], [52, 55, 59], [57, 60, 64]],
          melody: [69, 0, 72, 0, 74, 0, 76, 0, 74, 0, 71, 0, 74, 0, 72, 0,
                   71, 0, 67, 0, 71, 0, 74, 0, 76, 0, 74, 0, 72, 0, 69, 0],
          arp: true,
        },
        { // C — gentle answer, low and warm
          roots: [45, 41, 48, 43],
          chords: [[57, 60, 64], [53, 57, 60], [60, 64, 67], [55, 59, 62]],
          melody: [69, 0, 0, 67, 0, 0, 64, 0, 65, 0, 67, 0, 69, 0, 72, 0,
                   72, 0, 0, 71, 0, 0, 67, 0, 69, 0, 71, 0, 72, 0, 74, 0],
        },
      ],
    },
    // after the Hush — sparse, hollow, wrong
    hush: {
      stepDur: 0.62, drone: 33,
      form: [0, 1, 0, 2],
      sections: [
        {
          roots: [45, 45, 41, 44],
          chords: [[57, 60], [57, 60], [53, 56], [56, 59]],
          melody: [0, 0, 69, 0, 0, 0, 0, 68, 0, 0, 0, 0, 65, 0, 0, 0,
                   0, 0, 69, 0, 0, 70, 0, 0, 0, 0, 0, 0, 68, 0, 0, 0],
        },
        { // the fragment tries to remember the festival theme, and fails
          roots: [41, 41, 44, 45],
          chords: [[53, 56], [53, 56], [56, 59], [57, 60]],
          melody: [0, 0, 0, 0, 76, 0, 0, 74, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 65, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0],
        },
        { // lower, slower heartbeat of it
          roots: [38, 38, 41, 44],
          chords: [[50, 53], [50, 53], [53, 56], [56, 59]],
          melody: [0, 0, 0, 62, 0, 0, 0, 0, 0, 0, 61, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 62, 0, 0, 0, 0, 65, 0, 0, 0, 0, 0, 0],
        },
      ],
    },
    // the pact / setting out — the festival theme, slowed, resolute
    resolve: {
      stepDur: 0.42,
      form: [0, 1, 0, 2],
      sections: [
        {
          roots: [48, 45, 41, 43],
          chords: [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]],
          melody: [76, 0, 0, 79, 0, 0, 81, 0, 79, 0, 76, 0, 74, 0, 72, 0,
                   69, 0, 0, 72, 0, 0, 74, 0, 76, 0, 74, 0, 72, 0, 0, 0],
        },
        { // steadier, striding bridge
          roots: [41, 43, 45, 43],
          chords: [[53, 57, 60], [55, 59, 62], [57, 60, 64], [55, 59, 62]],
          melody: [72, 0, 0, 74, 0, 0, 76, 0, 74, 0, 72, 0, 71, 0, 72, 0,
                   74, 0, 0, 76, 0, 0, 79, 0, 76, 0, 74, 0, 72, 0, 74, 0],
          arp: true,
        },
        { // the vow — high, held, certain
          roots: [41, 43, 48, 48],
          chords: [[53, 57, 60], [55, 59, 62], [60, 64, 67], [60, 64, 67]],
          melody: [81, 0, 0, 0, 79, 0, 0, 0, 76, 0, 79, 0, 84, 0, 0, 0,
                   83, 0, 0, 0, 84, 0, 0, 0, 79, 0, 0, 0, 76, 0, 0, 0],
        },
      ],
    },
    silence: null,
  },
  schedule() {
    if (!this.ctx || !this.musicOn) return;
    const M = this.MOODS[this.mood];
    if (!M) { this.nextT = this.ctx.currentTime + 0.2; return; }
    while (this.nextT < this.ctx.currentTime + 0.5) {
      const formLen = M.form.length * 32;
      const s = this.step % 32, t = this.nextT;
      const sec = M.sections[M.form[Math.floor((this.step % formLen) / 32)]];
      const pass = Math.floor(this.step / formLen);       // which time through the whole form
      const chord = Math.floor(s / 8);
      let mel = sec.melody[s];
      // second pass onward: lift arp sections an octave now and then
      if (mel && sec.arp && pass % 2 === 1) mel += 12;
      if (mel) this.note(mel, t, M.stepDur * 1.9, 'triangle', this.mood === 'hush' ? 0.035 : 0.055, 3);
      if (s % 8 === 0) {
        this.note(sec.roots[chord], t, M.stepDur * 7, 'sine', 0.09);
        for (const c of sec.chords[chord]) this.note(c, t + 0.02, M.stepDur * 7, 'sine', 0.014);
      }
      // sparkle layer: quiet off-beat chord tones in arp-flagged sections
      if (sec.arp && s % 4 === 3) {
        const tones = sec.chords[chord];
        this.note(tones[(s >> 2) % tones.length] + 12, t, M.stepDur * 1.2, 'sine', 0.016, -4);
      }
      if (M.tick && s % 4 === 2) this.noise(t, 0.03, 3800, 0.012);
      if (M.drone && s % 16 === 0) this.note(M.drone, t, M.stepDur * 15, 'sine', 0.05);
      this.step++; this.nextT += M.stepDur;
    }
  },
  noise(t, dur, freq, gain) {
    const buf = this.ctx.createBuffer(1, this.ctx.sampleRate * dur, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const src = this.ctx.createBufferSource(); src.buffer = buf;
    const bp = this.ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = freq;
    const g = this.ctx.createGain(); g.gain.value = gain;
    src.connect(bp); bp.connect(g); g.connect(this.musicGain); src.start(t);
  },
  toggleMusic() {
    if (!this.ctx) { this.init(); return; }
    this.musicOn = !this.musicOn;
    this.musicGain.gain.value = this.musicOn ? 0.9 : 0;
  },
  sfxNote(m, delay, dur, type, gain) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime + delay;
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = type; o.frequency.value = this.f(m);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(this.master);
    o.start(t); o.stop(t + dur + 0.05);
  },
  blip(freq) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = 'square'; o.frequency.value = freq || 520;
    g.gain.setValueAtTime(0.028, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.06);
    o.connect(g); g.connect(this.master); o.start(t); o.stop(t + 0.08);
  },
  chime()   { [72, 76, 79, 84].forEach((m, i) => this.sfxNote(m, i * 0.1, 0.8, 'triangle', 0.09)); },
  sparkle() { [84, 88].forEach((m, i) => this.sfxNote(m, i * 0.07, 0.3, 'sine', 0.05)); },
  lampOn()  { [64, 71].forEach((m, i) => this.sfxNote(m, i * 0.05, 0.5, 'triangle', 0.07)); },
  pact()    { [60, 67, 72, 76, 79].forEach((m, i) => this.sfxNote(m, i * 0.13, 1.6, 'triangle', 0.08)); },
  finale()  { [60, 64, 67, 72, 76].forEach((m, i) => this.sfxNote(m, i * 0.16, 2.2, 'triangle', 0.08)); },
  hushSting() {
    [69, 68, 65, 63].forEach((m, i) => this.sfxNote(m, 0.5 + i * 0.7, 1.8, 'sine', 0.09));
  },
  rumble() {
    if (!this.ctx) return;
    this.noiseMaster(2, 130, 0.5);
  },
  noiseMaster(dur, freq, gain) {
    const t = this.ctx.currentTime;
    const buf = this.ctx.createBuffer(1, this.ctx.sampleRate * dur, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const src = this.ctx.createBufferSource(); src.buffer = buf;
    const lp = this.ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = freq;
    const g = this.ctx.createGain(); g.gain.value = gain;
    src.connect(lp); lp.connect(g); g.connect(this.master); src.start(t);
  },
};

/* ---------- networking (display side) ---------- */
const Net = {
  ws: null, onMessage: null,
  send(msg) { if (this.ws && this.ws.readyState === 1) this.ws.send(JSON.stringify(msg)); },
  to(id, msg) { msg.to = id; this.send(msg); },
  connect() {
    this.ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host);
    this.ws.onopen = () => this.send({ type: 'hello', role: 'display' });
    this.ws.onclose = () => setTimeout(() => this.connect(), 1500);
    this.ws.onmessage = (ev) => {
      let m; try { m = JSON.parse(ev.data); } catch { return; }
      if (this.onMessage) this.onMessage(m);
    };
  },
};
