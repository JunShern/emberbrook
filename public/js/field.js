'use strict';
/* ============================================================
   FIELD — scene-based painted world runtime.
   Scene geometry/content is defined by the chapter; this file
   handles rendering, collision, camera, exits, transitions,
   lamp glows and ambient scene effects.
   ============================================================ */

const Field = {
  scenes: {},          // set by chapter: key -> scene def
  currentKey: null,
  images: {},          // src -> Image
  cam: { x: 0, y: 0, leadX: 0, leadY: 0 },
  transitioning: false,

  register(scenes) {
    this.scenes = scenes;
    for (const s of Object.values(scenes)) {
      for (const src of Object.values(s.states)) {
        if (!this.images[src]) {
          const im = new Image();
          im.src = src;
          this.images[src] = im;
        }
      }
    }
  },

  scene() { return this.scenes[this.currentKey]; },
  backdrop() {
    const s = this.scene();
    if (!s) return null;
    const im = this.images[s.states[s.state]];
    return im && im.complete && im.naturalWidth ? im : null;
  },
  tint() {
    const s = this.scene();
    return s ? (s.tints ? s.tints[s.state] : null) : null;
  },

  setSceneState(key, state) {
    const s = this.scenes[key];
    if (s && s.states[state]) s.state = state;
  },

  enter(key, focusEnts, spawn) {
    this.currentKey = key;
    const s = this.scene();
    if (spawn && focusEnts) {
      focusEnts.forEach((e, i) => {
        e.scene = key;
        e.x = spawn[0] + (i ? 34 : 0);
        e.y = spawn[1] + (i ? 10 : 0);
        if (spawn[2]) e.dir = spawn[2];
      });
    }
    const f = focusEnts && focusEnts[0];
    this.cam.x = f ? f.x : (s.size ? s.size[0] / 2 : 660);
    this.cam.y = f ? f.y : (s.size ? s.size[1] / 2 : 380);
    this.cam.leadX = 0; this.cam.leadY = 0;
  },

  // transition with fade; moves the given entities to the target scene
  transition(exit, ents, onDone) {
    if (this.transitioning) return;
    this.transitioning = true;
    FX.fadeTarget = 1;
    setTimeout(() => {
      this.enter(exit.to, ents, exit.spawn);
      FX.fadeTarget = 0;
      this.transitioning = false;
      if (onDone) onDone();
      if (exit.onArrive) exit.onArrive();
    }, 620);
  },

  /* ---------- collision ---------- */
  inPoly(pts, x, y) {
    let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, yi] = pts[i], [xj, yj] = pts[j];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  },
  walkable(x, y, sceneKey) {
    const s = this.scenes[sceneKey || this.currentKey];
    if (!s) return false;
    const walk = (s.walkByState && s.walkByState[s.state]) || s.walk;
    if (!this.inPoly(walk, x, y)) return false;
    for (const b of (s.blocked || [])) {
      if (b.state && b.state !== s.state) continue;
      if (b.kind === 'rect' && x > b.x && x < b.x + b.w && y > b.y && y < b.y + b.h) return false;
      if (b.kind === 'circle' && Math.hypot(x - b.x, y - b.y) < b.r) return false;
    }
    return true;
  },

  /* ---------- camera ---------- */
  updateCamera(dt, focuses) {
    const img = this.backdrop();
    if (!img) return { camX: this.cam.x, camY: this.cam.y, Z: 1, viewW: Screen.cw };
    const s = this.scene();
    let tx, ty, viewH = s.viewH;
    if (Camera.target) {
      tx = Camera.target.x; ty = Camera.target.y;
      if (Camera.target.viewH) viewH = Camera.target.viewH;
      const k = Math.min(1, dt * 2.4);
      this.cam.x += (tx - this.cam.x) * k;
      this.cam.y += (ty - this.cam.y) * k;
      this._viewH = (this._viewH || s.viewH) + (viewH - (this._viewH || s.viewH)) * k;
    } else {
      this._viewH = (this._viewH || s.viewH) + (s.viewH - (this._viewH || s.viewH)) * Math.min(1, dt * 2);
      if (focuses.length) {
        tx = focuses.reduce((a, p) => a + p.x, 0) / focuses.length;
        ty = focuses.reduce((a, p) => a + p.y, 0) / focuses.length;
        const mv = focuses[0];
        const lead = 42;
        const vx = mv.moving ? (mv.dir === 'right' ? 1 : mv.dir === 'left' ? -1 : 0) : 0;
        const vy = mv.moving ? (mv.dir === 'down' ? 1 : mv.dir === 'up' ? -1 : 0) : 0;
        this.cam.leadX += (vx * lead - this.cam.leadX) * Math.min(1, dt * 2);
        this.cam.leadY += (vy * lead - this.cam.leadY) * Math.min(1, dt * 2);
        const k = Math.min(1, dt * 3.2);
        this.cam.x += (tx + this.cam.leadX - this.cam.x) * k;
        this.cam.y += (ty + this.cam.leadY - this.cam.y) * k;
      }
    }
    const vh = this._viewH || s.viewH;
    const Z = Screen.ch / vh;
    const viewW = Screen.cw / Z;
    let camX = Math.max(viewW / 2, Math.min(img.naturalWidth - viewW / 2, this.cam.x));
    let camY = Math.max(vh / 2, Math.min(img.naturalHeight - vh / 2, this.cam.y));
    if (img.naturalWidth < viewW) camX = img.naturalWidth / 2;
    if (img.naturalHeight < vh) camY = img.naturalHeight / 2;
    return { camX, camY, Z, viewW, viewH: vh };
  },

  worldToScreen(wx, wy) {
    const v = this._lastView;
    if (!v) return [0, 0];
    return [(wx - v.camX) * v.Z + Screen.cw / 2, (wy - v.camY) * v.Z + Screen.ch / 2];
  },

  /* ---------- draw ---------- */
  draw(g, ents, dt, focuses) {
    const img = this.backdrop();
    const s = this.scene();
    g.fillStyle = '#0d0a08';
    g.fillRect(0, 0, Screen.cw, Screen.ch);
    if (!img || !s) return;
    const view = this.updateCamera(dt, focuses);
    this._lastView = view;
    const { camX, camY, Z } = view;

    g.save();
    g.translate(Screen.cw / 2, Screen.ch / 2);
    const sx = FX.shake ? Math.sin(time * 55) * FX.shake : 0;
    const sy = FX.shake ? Math.cos(time * 47) * FX.shake : 0;
    g.scale(Z, Z);
    g.translate(-camX + sx, -camY + sy);
    g.imageSmoothingEnabled = true;
    g.drawImage(img, 0, 0);

    // sigil plates glow (gate scene)
    if (s.plates) {
      for (const pl of s.plates) {
        const active = s.platesActive && s.state !== 'open';
        const glow = pl.hold || 0;
        if (active || glow > 0) {
          const a = 0.3 + 0.5 * (glow || (0.3 + 0.3 * Math.sin(time * 3)));
          const gr = g.createRadialGradient(pl.x, pl.y, 2, pl.x, pl.y, 34);
          gr.addColorStop(0, `rgba(240,168,60,${a})`);
          gr.addColorStop(1, 'rgba(240,168,60,0)');
          g.fillStyle = gr;
          g.fillRect(pl.x - 34, pl.y - 34, 68, 68);
          if (glow > 0 && glow < 1) {
            g.strokeStyle = '#f2d16b'; g.lineWidth = 3;
            g.beginPath(); g.arc(pl.x, pl.y, 26, -Math.PI / 2, -Math.PI / 2 + glow * Math.PI * 2); g.stroke();
          }
        }
      }
    }

    // entities in this scene, y-sorted
    const drawList = ents.filter(e => e.scene === this.currentKey && !e.hidden)
      .sort((a, b) => a.y - b.y);
    const tint = this.tint();
    for (const e of drawList) Sprites.draw(g, e, tint);

    // occluders: re-draw backdrop chunks over entities standing behind them
    for (const oc of (s.occluders || [])) {
      const anyBehind = drawList.some(e => e.y < oc.baseY && e.x > oc.x - 40 && e.x < oc.x + oc.w + 40);
      if (anyBehind) g.drawImage(img, oc.x, oc.y, oc.w, oc.h, oc.x, oc.y, oc.w, oc.h);
    }

    // lamp glows (engine-lit so gameplay can light them)
    for (const lamp of (s.lamps || [])) {
      if (!lamp.lit) continue;
      const flick = 1 + Math.sin(time * 9 + lamp.x) * 0.05;
      const gr = g.createRadialGradient(lamp.x, lamp.y, 3, lamp.x, lamp.y, 110 * flick);
      gr.addColorStop(0, 'rgba(255,205,120,.5)');
      gr.addColorStop(0.4, 'rgba(255,185,100,.18)');
      gr.addColorStop(1, 'rgba(255,185,100,0)');
      g.fillStyle = gr;
      g.fillRect(lamp.x - 120, lamp.y - 120, 240, 240);
      g.fillStyle = `rgba(255,235,190,${0.8 + Math.sin(time * 11 + lamp.x) * 0.15})`;
      g.beginPath(); g.arc(lamp.x, lamp.y, 6, 0, 7); g.fill();
    }

    // heartlight ambience (square, festival state)
    if (s.heartlight && s.state === 'festival') {
      const hl = s.heartlight;
      const pulse = 0.16 + 0.07 * Math.sin(time * 2.1);
      const gr = g.createRadialGradient(hl.x, hl.y, 8, hl.x, hl.y, 190);
      gr.addColorStop(0, `rgba(255,190,90,${pulse})`);
      gr.addColorStop(1, 'rgba(255,190,90,0)');
      g.fillStyle = gr;
      g.fillRect(hl.x - 190, hl.y - 190, 380, 380);
      if (Math.random() < dt * 5)
        Particles.spawn({ kind: 'mote', x: hl.x + (Math.random() - 0.5) * 40, y: hl.y - 10, vy: -14, life: 2, sway: 10 });
    }
    // drifting moths in drained scenes
    if (s.mothAmbience && s.state !== 'festival' && Math.random() < dt * 1.2) {
      Particles.spawn({ kind: 'moth', x: camX + (Math.random() - 0.5) * view.viewW, y: camY + (Math.random() - 0.5) * view.viewH, vx: 0, vy: -6, life: 6, seed: Math.random() * 9 });
    }
    // fireflies in the forest
    if (s.fireflies && Math.random() < dt * 2)
      Particles.spawn({ kind: 'mote', x: camX + (Math.random() - 0.5) * view.viewW, y: camY + (Math.random() - 0.5) * view.viewH, vy: -4, life: 3, sway: 16 });

    Particles.draw(g);
    g.restore();
  },
};
