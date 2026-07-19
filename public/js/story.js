'use strict';
/* ============================================================
   STORY — dialogue with portraits, cutscene runner, banners,
   objectives, toasts. Content lives in chapter files.
   ============================================================ */

const SERIF = '"Iowan Old Style", Palatino, Georgia, serif';

function roundRectPath(g, x, y, w, h, r) {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

/* ---------- dialogue ---------- */
const Dialog = {
  lines: null, i: 0, chars: 0, onFinish: null, narration: false, cooldown: 0,
  active() { return this.lines !== null; },
  start(lines, onFinish, narration) {
    this.lines = lines; this.i = 0; this.chars = 0; this.cooldown = 0;
    this.onFinish = onFinish || null;
    this.narration = !!narration;
    AudioSys.blip(narration ? 380 : 520);
  },
  advance() {
    if (!this.lines) return;
    const line = this.lines[this.i];
    // fast-forward the typewriter, then briefly ignore presses so a
    // double-tap can't skip a line unread
    if (this.chars < line.text.length) { this.chars = line.text.length; this.cooldown = 0.25; return; }
    if (this.cooldown > 0) return;
    this.i++; this.chars = 0;
    if (this.i >= this.lines.length) {
      const fin = this.onFinish;
      this.lines = null;
      if (fin) fin();
    } else AudioSys.blip(this.narration ? 380 : 520);
  },
  update(dt) {
    this.cooldown = Math.max(0, this.cooldown - dt);
    if (!this.lines) return;
    const line = this.lines[this.i];
    const wasTyping = this.chars < line.text.length;
    this.chars = Math.min(line.text.length, this.chars + dt * 42);
    if (wasTyping && this.chars >= line.text.length) this.cooldown = 0.25;
  },
  draw(g) {
    if (!this.lines) return;
    const { cw, ch } = Screen;
    const line = this.lines[this.i];
    const shown = line.text.slice(0, Math.floor(this.chars));
    const done = Math.floor(this.chars) >= line.text.length;

    if (this.narration) {
      g.save();
      g.textAlign = 'center';
      g.font = `italic 21px ${SERIF}`;
      g.fillStyle = 'rgba(8,6,12,.55)';
      g.fillRect(0, ch * 0.68 - 40, cw, 86);
      g.fillStyle = '#e8d5b0';
      wrapText(g, shown, cw / 2, ch * 0.68, cw * 0.62, 28);
      if (done && Math.sin(time * 5) > 0) {
        g.font = `15px ${SERIF}`;
        g.fillStyle = 'rgba(232,178,92,.8)';
        g.fillText('▾  A', cw / 2, ch * 0.68 + 62);
      }
      g.restore();
      return;
    }

    // who may carry an expression tag: 'vesper:worried'
    const [whoBase] = line.who.split(':');
    const sp = SPEAKERS[whoBase] || { name: whoBase, color: '#e0a94e' };
    const portrait = PORTRAITS[whoBase];
    const thought = line.text.startsWith('(');
    const bw = Math.min(800, cw - 80), bh = 134;
    const bx = cw / 2 - bw / 2, by = ch - bh - 36;

    // box
    g.fillStyle = '#f2e4c4';
    roundRectPath(g, bx, by, bw, bh, 12); g.fill();
    g.strokeStyle = '#9c7a4c'; g.lineWidth = 3;
    roundRectPath(g, bx, by, bw, bh, 12); g.stroke();
    g.strokeStyle = 'rgba(156,122,76,.4)'; g.lineWidth = 1;
    roundRectPath(g, bx + 5, by + 5, bw - 10, bh - 10, 8); g.stroke();

    // portrait panel — large hand-drawn bust if we have one, else pixel faceset
    let textX = bx + 28;
    const hd = typeof PORTRAITS_HD !== 'undefined' && (PORTRAITS_HD[line.who] || PORTRAITS_HD[whoBase]);
    if (hd) {
      const ps = 176, ppx = bx + 16, ppy = by + bh - ps - 8;
      g.save();
      g.fillStyle = '#2b2027';
      roundRectPath(g, ppx - 5, ppy - 5, ps + 10, ps + 10, 12); g.fill();
      roundRectPath(g, ppx - 2, ppy - 2, ps + 4, ps + 4, 10); g.clip();
      g.imageSmoothingEnabled = true;
      // crop in on the face — trim the paper margins baked into the art
      const cw2 = hd.naturalWidth, ch2 = hd.naturalHeight;
      g.drawImage(hd, cw2 * 0.14, ch2 * 0.02, cw2 * 0.72, ch2 * 0.72, ppx - 2, ppy - 2, ps + 4, ps + 4);
      g.restore();
      g.strokeStyle = sp.color; g.lineWidth = 2.5;
      roundRectPath(g, ppx - 5, ppy - 5, ps + 10, ps + 10, 12); g.stroke();
      textX = ppx + ps + 26;
    } else if (portrait) {
      const ps = 84, ppx = bx + 18, ppy = by - 24;
      g.fillStyle = '#2b2027';
      roundRectPath(g, ppx - 5, ppy - 5, ps + 10, ps + 10, 10); g.fill();
      g.strokeStyle = sp.color; g.lineWidth = 2;
      roundRectPath(g, ppx - 5, ppy - 5, ps + 10, ps + 10, 10); g.stroke();
      g.save();
      g.imageSmoothingEnabled = false;
      g.drawImage(portrait, ppx, ppy, ps, ps);
      g.restore();
      textX = ppx + ps + 24;
    }

    // nameplate
    g.font = `700 16px ${SERIF}`;
    g.textAlign = 'left';
    const nw = g.measureText(sp.name).width;
    const npx = textX - 6;
    g.fillStyle = '#2b2027';
    roundRectPath(g, npx, by - 14, nw + 26, 28, 9); g.fill();
    g.fillStyle = sp.color;
    g.beginPath(); g.arc(npx + 13, by, 4.5, 0, 7); g.fill();
    g.fillStyle = '#f2e4c4';
    g.fillText(sp.name, npx + 22, by + 5.5);

    // text — inner thoughts render italic and softer
    g.font = thought ? `italic 18px ${SERIF}` : `18px ${SERIF}`;
    g.fillStyle = thought ? '#6d5a42' : '#42311f';
    wrapTextLeft(g, shown, textX, by + 42, bx + bw - textX - 28, 26);

    if (done && Math.sin(time * 5) > 0) {
      g.fillStyle = '#9c7a4c';
      g.font = `16px ${SERIF}`;
      g.textAlign = 'right';
      g.fillText('▾  A', bx + bw - 20, by + bh - 14);
      g.textAlign = 'left';
    }
  },
};

function wrapTextLeft(g, txt, x, y, maxW, lh) {
  const words = txt.split(' ');
  let line = '', yy = y;
  for (const w of words) {
    const test = line ? line + ' ' + w : w;
    if (g.measureText(test).width > maxW) { g.fillText(line, x, yy); line = w; yy += lh; }
    else line = test;
  }
  g.fillText(line, x, yy);
}
function wrapText(g, txt, cx, y, maxW, lh) {
  const words = txt.split(' ');
  let line = '', yy = y;
  for (const w of words) {
    const test = line ? line + ' ' + w : w;
    if (g.measureText(test).width > maxW) { g.fillText(line, cx, yy); line = w; yy += lh; }
    else line = test;
  }
  g.fillText(line, cx, yy);
}

/* ---------- banner / objective / toasts ---------- */
const Banner = {
  cur: null,
  show(title, sub, dur) { this.cur = { title, sub, t: 0, dur: dur || 6 }; },
  update(dt) { if (this.cur) { this.cur.t += dt; if (this.cur.t > this.cur.dur) this.cur = null; } },
  draw(g) {
    if (!this.cur) return;
    const { cw, ch } = Screen;
    const b = this.cur;
    const a = Math.min(Math.min(1, b.t / 0.6), Math.min(1, (b.dur - b.t) / 0.8));
    const y = ch * 0.2 - (1 - Math.min(1, b.t / 0.6)) * 18;
    g.save();
    g.globalAlpha = Math.max(0, a);
    g.textAlign = 'center';
    g.font = `600 44px ${SERIF}`;
    const w = Math.max(g.measureText(b.title).width, 300) + 90;
    g.fillStyle = 'rgba(20,14,8,.74)';
    roundRectPath(g, cw / 2 - w / 2, y - 44, w, b.sub ? 96 : 64, 12); g.fill();
    g.strokeStyle = 'rgba(201,151,63,.65)'; g.lineWidth = 2;
    roundRectPath(g, cw / 2 - w / 2, y - 44, w, b.sub ? 96 : 64, 12); g.stroke();
    g.fillStyle = '#f2d16b';
    g.fillText(b.title, cw / 2, y);
    if (b.sub) {
      g.font = `italic 19px ${SERIF}`;
      g.fillStyle = '#e8d5b0';
      g.fillText(b.sub, cw / 2, y + 32);
    }
    g.restore();
  },
};

const Objective = {
  text: '', ping: 0,
  set(t) { if (t !== this.text) { this.text = t; this.ping = 1.2; } },
  update(dt) { this.ping = Math.max(0, this.ping - dt); },
  draw(g) {
    if (!this.text || Cutscene.active) return;
    g.save();
    g.font = `italic 15px ${SERIF}`;
    g.textAlign = 'left';
    const w = g.measureText(this.text).width;
    const glow = this.ping > 0 ? Math.sin(this.ping * 10) * 0.3 + 0.3 : 0;
    g.fillStyle = 'rgba(24,16,8,.68)';
    roundRectPath(g, 16, 16, w + 44, 32, 9); g.fill();
    g.strokeStyle = `rgba(201,151,63,${0.5 + glow})`; g.lineWidth = 1.5;
    roundRectPath(g, 16, 16, w + 44, 32, 9); g.stroke();
    g.fillStyle = '#e0a94e'; g.fillText('✦', 30, 37);
    g.fillStyle = '#f2e4c4'; g.fillText(this.text, 48, 37);
    g.restore();
  },
};

const Toasts = {
  list: [],
  add(text, color) { this.list.push({ text, color: color || '#e0a94e', t: 0 }); AudioSys.sparkle(); },
  update(dt) {
    for (const t of this.list) t.t += dt;
    this.list = this.list.filter(t => t.t < 4.5);
  },
  draw(g) {
    const { cw } = Screen;
    g.save();
    g.textAlign = 'center';
    this.list.forEach((t, i) => {
      const a = Math.min(Math.min(1, t.t / 0.3), Math.min(1, (4.5 - t.t) / 0.8));
      const y = 78 + i * 42 - Math.max(0, 0.3 - t.t) * 40;
      g.globalAlpha = Math.max(0, a);
      g.font = `600 17px ${SERIF}`;
      const w = g.measureText(t.text).width + 56;
      g.fillStyle = 'rgba(24,16,8,.78)';
      roundRectPath(g, cw / 2 - w / 2, y - 21, w, 32, 9); g.fill();
      g.strokeStyle = t.color; g.lineWidth = 1.5;
      roundRectPath(g, cw / 2 - w / 2, y - 21, w, 32, 9); g.stroke();
      g.fillStyle = t.color;
      g.fillText(t.text, cw / 2, y + 1);
    });
    g.restore();
  },
};

/* ---------- cutscene runner ---------- */
const Cutscene = {
  steps: null, idx: 0, active: false, onDone: null,
  waitT: 0, waitFn: null, moveJob: null, holdJob: null,

  play(steps, onDone) {
    this.steps = steps; this.idx = 0; this.active = true; this.onDone = onDone || null;
    this.waitT = 0; this.waitFn = null; this.moveJob = null; this.holdJob = null;
    FX.letterboxTarget = 1;
    this.next();
  },
  finish() {
    this.active = false; this.steps = null;
    FX.letterboxTarget = 0;
    Camera.target = null;
    if (this.onDone) { const f = this.onDone; this.onDone = null; f(); }
  },
  next() {
    if (!this.active) return;
    while (this.idx < this.steps.length) {
      const s = this.steps[this.idx++];
      // instant steps run immediately and continue; blocking steps return
      if (s.say) { Dialog.start([{ who: s.say[0], text: s.say[1] }], () => this.next()); return; }
      if (s.dialog) { Dialog.start(s.dialog.map(l => ({ who: l[0], text: l[1] })), () => this.next()); return; }
      if (s.narrate) { Dialog.start([{ who: 'system', text: s.narrate }], () => this.next(), true); return; }
      if (s.wait) { this.waitT = s.wait; return; }
      if (s.waitFor) { this.waitFn = s.waitFor; return; }
      if (s.move) { this.moveJob = Object.assign({ speed: 55 }, s.move); this.moveJob.ent.moving = true; return; }
      if (s.bothHold) { this.holdJob = { prompt: s.bothHold.prompt || 'HOLD  A — together', dur: s.bothHold.dur || 2, p: 0 }; return; }
      if (s.cam) Camera.target = s.cam;
      if (s.camRelease) Camera.target = null;
      if (s.fadeTo !== undefined) FX.fadeTarget = s.fadeTo;
      if (s.mood) AudioSys.setMood(s.mood);
      if (s.light && typeof World !== 'undefined' && World.setLight) World.setLight(s.light);
      if (s.banner) Banner.show(s.banner.title, s.banner.sub, s.banner.dur);
      if (s.toast) Toasts.add(s.toast.text, s.toast.color);
      if (s.face) { s.face.ent.dir = s.face.dir; }
      if (s.shake) FX.shake = s.shake;
      if (s.flash) FX.flash = s.flash;
      if (s.run) s.run();
    }
    this.finish();
  },
  tick(dt, players) {
    if (!this.active) return;
    if (Dialog.active()) return;             // waiting on dialogue advance
    if (this.waitT > 0) { this.waitT -= dt; if (this.waitT <= 0) this.next(); return; }
    if (this.waitFn) { if (this.waitFn()) { this.waitFn = null; this.next(); } return; }
    if (this.moveJob) {
      const j = this.moveJob, e = j.ent;
      const dx = j.x - e.x, dy = j.y - e.y, d = Math.hypot(dx, dy);
      if (d < 2) { e.moving = false; this.moveJob = null; this.next(); return; }
      e.x += dx / d * j.speed * dt; e.y += dy / d * j.speed * dt;
      e.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
      e.animT = (e.animT || 0) + dt;
      return;
    }
    if (this.holdJob) {
      const j = this.holdJob;
      const ps = players.filter(Boolean);
      const holding = ps.length >= 2 && ps.every(p => p.a);
      j.p = holding ? Math.min(1, j.p + dt / j.dur) : Math.max(0, j.p - dt * 1.5);
      if (j.p >= 1) { this.holdJob = null; this.next(); }
      return;
    }
  },
  drawHold(g, players) {
    if (!this.holdJob) return;
    const { cw, ch } = Screen;
    const j = this.holdJob;
    g.save();
    g.textAlign = 'center';
    g.font = `600 22px ${SERIF}`;
    g.fillStyle = '#f2d16b';
    g.strokeStyle = 'rgba(20,12,4,.7)'; g.lineWidth = 4;
    g.strokeText(j.prompt, cw / 2, ch * 0.6);
    g.fillText(j.prompt, cw / 2, ch * 0.6);
    // twin rings
    const ps = players.filter(Boolean);
    [-46, 46].forEach((off, i) => {
      const px = cw / 2 + off, py = ch * 0.6 + 46;
      const holding = ps[i] && ps[i].a;
      g.strokeStyle = 'rgba(120,100,70,.5)'; g.lineWidth = 4;
      g.beginPath(); g.arc(px, py, 17, 0, 7); g.stroke();
      g.strokeStyle = holding ? '#f2d16b' : 'rgba(242,209,107,.25)';
      g.beginPath(); g.arc(px, py, 17, -Math.PI / 2, -Math.PI / 2 + j.p * Math.PI * 2); g.stroke();
      g.font = `13px ${SERIF}`;
      g.fillStyle = holding ? '#f2d16b' : '#a89a7a';
      g.fillText(ps[i] ? ps[i].charName : '—', px, py + 34);
      g.font = `600 22px ${SERIF}`;
    });
    g.restore();
  },
};
