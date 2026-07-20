'use strict';
/* ============================================================
   CHAPTER TWO — "Dellhollow"  (painted scene edition)

   Beat 1  — the descent: map-is-wrong, the valley from above,
             the Stranger, the parapet vista.
   Beat 2  — arrival on the stair-street; Hobb and Pell on the quay.
   Beat 3  — the jam explained: Odessa's ruling.
   Beat 4  — Maren, entering wet; the tally beam.
   Beat 5  — down to Lock Five: the Tenant; the flume plan.
   Beat 5¼ — supper at the keepers' cottage; nightfall.
   Beat 5½ — the dock, at night: Vesper's biography.
   Beat 6  — the twin winches, and Odessa's station.
   Beat 7  — the flume run.
   Beat 8  — the landing: the bag, the chart, the boat.
   ============================================================ */

const Chapter2 = {
  built: false,
  phase: 'together',
  flags: {
    descentIntro: false, chartDone: false, strangerSeen: false,
    arrived: false, talked: {}, jamDone: false, marenDone: false,
    lockSeen: false, planMade: false, nightFallen: false, dockDone: false,
    boatDown: false, gateHalf: false, gatesOpen: false, flumeDone: false,
    marenJoined: false, ended: false, endT: 0,
    hobbTalk: 0, pellTalk: 0,
    supperCalled: false, supperDone: false,
    sorrelTalk: 0, creelTalk: 0, nibTalk: 0,
  },
  npcs: {}, entities: [],

  activeRoles() { return ['vesper', 'lake']; },
  setPhase(p) {
    this.phase = p;
    Net.send({ type: 'phase', act: p });
  },

  /* ================= SCENES ================= */
  buildScenes() {
    const S = {
      descent: {
        states: { gray: 'assets/scenes/descent/main.png' }, state: 'gray',
        maskSrc: 'assets/scenes/descent/mask.png',
        viewH: 700, charH: 120, speed: 190, mothAmbience: true,
        tints: { gray: '#9aa393' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        exits: [
          { zone: { x: 60, y: 0, w: 240, h: 80 }, to: null,               // back up to the Gate
            enabled: () => false,
            deniedLine: ['lake', 'Back up to the Gate? Not with the spark this side of it. The rounds only go one way now.'] },
          { zone: { x: 520, y: 704, w: 300, h: 64 }, to: 'stairs', spawn: [800, 150, 'down'],
            enabled: () => Chapter2.flags.strangerSeen,
            deniedLine: ['vesper', 'Not yet. The world and my sheet are having a disagreement, and I intend to referee it before we lose the light.'] },
        ],
      },
      vista: {
        // cutscene-only, landing-class but stricter: no mask, no exits, no walkability —
        // players are never present in it (they stay in 'descent'; only the camera travels)
        states: { morning: 'assets/scenes/vista/main.png' }, state: 'morning',
        viewH: 700, charH: 120, speed: 190,
        tints: { morning: '#adb3a6' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],
        blocked: [], exits: [],
      },
      stairs: {
        // the stair-street: one painting; night = tint + lantern-strings lit (engine glow)
        states: { day: 'assets/scenes/stairs/main.png',
                  night: 'assets/scenes/stairs/main.png' }, state: 'day',
        maskSrc: 'assets/scenes/stairs/mask.png',
        viewH: 720, charH: 118, speed: 190,
        tints: { day: '#c9a988', night: '#66708c' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        lamps: [   // painted lamp-posts + lantern-string glow points — no id, lit at night
          { x: 297, y: 185, lit: false }, { x: 858, y: 200, lit: false },
          { x: 500, y: 120, lit: false }, { x: 640, y: 105, lit: false },
          { x: 950, y: 80, lit: false },
        ],
        exits: [
          // top — back up the switchbacks (the night denial and Maren's line moved
          // here from the shipped dellhollow west exit)
          { zone: { x: 700, y: 0, w: 180, h: 80 }, to: 'descent', spawn: [640, 640, 'up'],
            enabled: () => !Chapter2.flags.nightFallen,
            deniedLine: ['maren', 'Up the switchbacks at THIS hour? Nothing up there but weather. Everything worth anything is down.'] },
          // bottom — the quay gate. Spawn (210, 110) is the PROVEN shipped west-entry
          // spawn — do not drift this value.
          { zone: { x: 620, y: 700, w: 190, h: 68 }, to: 'dellhollow', spawn: [210, 110, 'down'] },
          // the keepers' cottage door — mid-scene door exit (Ch1 lane→interior precedent)
          { zone: { x: 940, y: 490, w: 90, h: 80 }, to: 'cottage', spawn: [490, 600, 'right'],
            enabled: () => Chapter2.flags.supperCalled && !Chapter2.flags.supperDone,
            get deniedLine() {
              return Chapter2.flags.supperDone
                ? ['system', '(Pulled to. The lamp inside is banked low. Let the house keep its keeper tonight.)']
                : ['vesper', 'A door with lock-gates carved over it. Keepers live here. We haven’t been asked.'];
            } },
        ],
      },
      cottage: {
        // Maren and Odessa's house — Ch1 interior-class; night = tint only
        states: { dusk: 'assets/scenes/cottage/main.png',
                  night: 'assets/scenes/cottage/main.png' }, state: 'dusk',
        maskSrc: 'assets/scenes/cottage/mask.png',
        viewH: 725, charH: 205, speed: 280,
        tints: { dusk: '#e8b489', night: '#8d8298' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        exits: [{ zone: { x: 390, y: 560, w: 130, h: 150 }, to: 'stairs', spawn: [985, 610, 'down'] }],
      },
      dellhollow: {
        // one painting; night = tint + desat + lantern-strings lit (engine glow)
        states: { day: 'assets/scenes/dellhollow/main.png',
                  night: 'assets/scenes/dellhollow/main.png' }, state: 'day',
        maskSrc: 'assets/scenes/dellhollow/mask.png',
        viewH: 720, charH: 118, speed: 190,
        tints: { day: '#c9ab86', night: '#66708c' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        lamps: [   // lantern-strings: ordinary lamps, engine glow only; no id (never hand-lit); lit at night
          { x: 300, y: 250, lit: false }, { x: 470, y: 285, lit: false }, { x: 640, y: 255, lit: false },
          { x: 420, y: 470, lit: false }, { x: 600, y: 500, lit: false }, { x: 780, y: 470, lit: false },
          { x: 1010, y: 350, lit: false },
        ],
        exits: [
          // west edge — the quay gate up to the stair-street (the painted rope bridge
          // beside it is dressing now; the night denial moved to the stairs top exit)
          { zone: { x: 0, y: 90, w: 60, h: 70 }, to: 'stairs', spawn: [720, 680, 'up'],
            enabled: () => true },
          { zone: { x: 1180, y: 560, w: 164, h: 168 }, to: 'lockfive', spawn: [1230, 240, 'down'],
            enabled: () => Chapter2.flags.marenDone,
            deniedLine: ['odessa', 'The deep stairs are lock business. Nobody walks them without my say — or my daughter.'] },
        ],
      },
      lockfive: {
        states: { dim: 'assets/scenes/lockfive/main.png',
                  night: 'assets/scenes/lockfive/main.png' }, state: 'dim',
        maskSrc: 'assets/scenes/lockfive/mask.png',
        viewH: 700, charH: 120, speed: 180,
        tints: { dim: '#5f6b70', night: '#454e5e' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs (L-shaped apron)
        blocked: [],
        lamps: [{ x: 240, y: 545, lit: true }, { x: 900, y: 535, lit: true }],  // work-lanterns, always lit
        exits: [
          { zone: { x: 1180, y: 60, w: 164, h: 150 }, to: 'dellhollow', spawn: [1230, 640, 'up'] },
        ],
      },
      landing: {
        // cutscene-only: the ending owns it start to finish; no exits, no POIs
        states: { dawn: 'assets/scenes/landing/main.png' }, state: 'dawn',
        maskSrc: 'assets/scenes/landing/mask.png',
        viewH: 700, charH: 120, speed: 190,
        tints: { dawn: '#c9c2b3' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],
        blocked: [], exits: [],
      },
    };
    // merge with whatever is already registered so earlier chapters'
    // scenes (and their checkpoints) stay reachable after the handoff
    Field.register(Object.assign({}, Field.scenes, S));
  },

  build() {
    if (this.built) return;
    this.built = true;
    this.buildScenes();
    const N = (key, char, scene, x, y, dir, h) => {
      const e = { key, char, scene, x, y, dir: dir || 'down', moving: false, animT: 0, h: h || 90 };
      this.npcs[key] = e; this.entities.push(e);
      return e;
    };
    N('maren', 'maren', 'dellhollow', 1150, 600, 'down', 118).hidden = true;
    N('odessa', 'odessa', 'dellhollow', 1000, 285, 'down', 128);
    // sprite-first extras: existing villager sheets, distinct identity tints
    const hobb = N('hobb', 'finn', 'dellhollow', 330, 350, 'down', 122);
    hobb.tint = '#e8c093';                                  // wind-burned warm — the barge captain
    const pell = N('pell', 'rowan', 'dellhollow', 552, 468, 'down', 130);
    pell.tint = '#c9d1ad';                                  // oilskin grey-green — the night-watchman
    // stair-street flavor voices (expansion §b): nameplate-only, reuse-tinted sheets
    const sorrel = N('sorrel', 'poppy', 'stairs', 300, 555, 'down', 120);
    sorrel.tint = '#d9b08a';                                // flour-warm — the bread-window
    sorrel.interactR = 130;                                 // behind the counter (Poppy pattern)
    const creel = N('creel', 'rowan', 'stairs', 940, 610, 'down', 112);
    creel.tint = '#b0a98f';                                 // old rope — the splicer on his step
    const nib = N('nib', 'pip', 'stairs', 800, 660, 'down', 84);
    nib.tint = '#e0c07a';                                   // gull-officer yellow — the kid
    const stranger = N('stranger', 'stranger', 'descent', 1250, 80, 'down', 110);
    stranger.hidden = true;
    const mochi = N('mochi', 'mochi', 'descent', 250, 180, 'down', 48);
    mochi.follow = 'party';
    // props: the boat (side-on cutout, ~280px long) and the Tenant's head
    // (cutscene overlay for the flume-run glide — never doubled on the painted eel)
    N('boat', 'boat-side', 'lockfive', 560, 600, 'right', 280).hidden = true;
    N('tenant', 'tenant-head', 'lockfive', 350, 560, 'right', 300).hidden = true;
  },

  // hard reset of story state — used by begin() and the checkpoints
  resetFlags() {
    Object.assign(this.flags, {
      descentIntro: false, chartDone: false, strangerSeen: false,
      arrived: false, talked: {}, jamDone: false, marenDone: false,
      lockSeen: false, planMade: false, nightFallen: false, dockDone: false,
      boatDown: false, gateHalf: false, gatesOpen: false, flumeDone: false,
      marenJoined: false, ended: false, endT: 0,
      hobbTalk: 0, pellTalk: 0,
      supperCalled: false, supperDone: false,
      sorrelTalk: 0, creelTalk: 0, nibTalk: 0,
    });
    this._dockT = 0;
    this._supT = 0;
    const sc = Field.scenes;
    if (sc.dellhollow) sc.dellhollow.lamps.forEach(l => { l.lit = false; });
    if (sc.stairs) sc.stairs.lamps.forEach(l => { l.lit = false; });
    Field.setSceneState('descent', 'gray');
    Field.setSceneState('dellhollow', 'day');
    Field.setSceneState('stairs', 'day');
    Field.setSceneState('cottage', 'dusk');
    Field.setSceneState('lockfive', 'dim');
    Field.setSceneState('landing', 'dawn');
    const N = this.npcs;
    N.maren.hidden = true; N.maren.follow = null;
    Object.assign(N.maren, { scene: 'dellhollow', x: 1150, y: 600, dir: 'down' });
    N.odessa.hidden = false;
    Object.assign(N.odessa, { scene: 'dellhollow', x: 1000, y: 285, dir: 'down' });
    N.hobb.hidden = false;
    Object.assign(N.hobb, { scene: 'dellhollow', x: 330, y: 350, dir: 'down' });
    N.pell.hidden = false;
    Object.assign(N.pell, { scene: 'dellhollow', x: 552, y: 468, dir: 'down' });
    N.sorrel.hidden = false;
    Object.assign(N.sorrel, { scene: 'stairs', x: 300, y: 555, dir: 'down' });
    N.creel.hidden = false;
    Object.assign(N.creel, { scene: 'stairs', x: 940, y: 610, dir: 'down' });
    N.nib.hidden = false;
    Object.assign(N.nib, { scene: 'stairs', x: 800, y: 660, dir: 'down' });
    N.stranger.hidden = true;
    Object.assign(N.stranger, { scene: 'descent', x: 1250, y: 80, dir: 'down' });
    N.mochi.hidden = false; N.mochi.follow = 'party';
    Object.assign(N.mochi, { scene: 'descent', x: 250, y: 180, dir: 'down' });
    N.boat.hidden = true;
    Object.assign(N.boat, { scene: 'lockfive', x: 560, y: 600, dir: 'right' });
    N.tenant.hidden = true;
    Object.assign(N.tenant, { scene: 'lockfive', x: 350, y: 560, dir: 'right' });
  },

  // chapter start — the morning after the gate. Both players onto the descent.
  begin(players) {
    this.build();
    this.resetFlags();
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const place = (e, scene, x, y, dir) => { if (!e) return; e.scene = scene; e.x = x; e.y = y; e.dir = dir; e.hidden = false; e.parked = false; };
    place(vesper, 'descent', 140, 150, 'down');
    place(lake, 'descent', 200, 130, 'down');
    FX.desatTarget = 0;
    Field.enter('descent');
    Field.cam.x = 220; Field.cam.y = 180;
    this.setPhase('together');
    AudioSys.setMood('forestB');
  },

  spawnFor(role) {
    if (!this.flags.arrived)
      return role === 'vesper'
        ? { scene: 'descent', x: 140, y: 150, dir: 'down' }
        : { scene: 'descent', x: 200, y: 130, dir: 'down' };
    // supper window: rejoiners land at the cottage door on the stairs, so the
    // both-in-cottage trigger can't strand a late join on the quay
    if (this.flags.supperCalled && !this.flags.supperDone)
      return role === 'vesper'
        ? { scene: 'stairs', x: 940, y: 600, dir: 'up' }
        : { scene: 'stairs', x: 1020, y: 610, dir: 'up' };
    return role === 'vesper'
      ? { scene: 'dellhollow', x: 600, y: 520, dir: 'down' }
      : { scene: 'dellhollow', x: 660, y: 530, dir: 'down' };
  },

  /* scene-keyed music (§f of the chapter script) */
  moodFor(sceneKey) {
    const F = this.flags;
    switch (sceneKey) {
      case 'descent':
        return 'forestB';                       // the uneasy wood, continued from the gate
      case 'dellhollow':
        return F.nightFallen ? 'dellhollowNight' : 'dellhollow';
      case 'stairs':
        return F.nightFallen ? 'dellhollowNight' : 'dellhollow';
      case 'cottage':
        return 'dellhollowNight';               // the town theme at house scale (§f)
      case 'lockfive':
        return 'silence';                       // the chamber scores itself
      default:
        return null;                            // landing/vista: the cutscenes own them
    }
  },

  /* ================= per-frame ================= */
  update(dt, players) {
    const F = this.flags;
    if (Field.currentKey !== this._moodScene) {
      if (!Cutscene.active && !F.ended) {
        const m = this.moodFor(Field.currentKey);
        if (m && (AudioSys.ALIAS[m] || m) !== AudioSys.mood) AudioSys.setMood(m);
      }
      this._moodScene = Field.currentKey;
    }
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const both = vesper && lake;
    const busy = Cutscene.active || Dialog.active();

    // Beat 1 — chapter open on the descent
    if (both && !F.descentIntro && !busy && vesper.scene === 'descent' && lake.scene === 'descent')
      this.playDescent(vesper, lake);
    // Beat 1 — map-is-wrong at the chart halt (the slab on the second terrace)
    if (both && F.descentIntro && !F.chartDone && !busy &&
        players.some(p => p && p.scene === 'descent' && p.x > 250 && p.x < 560 && p.y > 200 && p.y < 380))
      this.playChart(players);
    // Beat 1 — the Stranger across the ravine (descending past the slab)
    if (both && F.chartDone && !F.strangerSeen && !busy &&
        players.some(p => p && p.scene === 'descent' && p.y > 380))
      this.playRavine(players);
    // Beat 1 — the vista, at the parapet
    if (both && F.strangerSeen && !this._vistaSeen && !busy &&
        players.some(p => p && p.scene === 'descent' && p.y > 640)) {
      this._vistaSeen = true;
      this.playVista(players);
    }
    // Beat 2 — arrival: first entry to the town, on the stair-street
    if (both && !F.arrived && F.strangerSeen && !busy &&
        players.some(p => p && p.scene === 'stairs'))
      this.playArrival(players);
    // Beat 3 — the jam: both quay voices heard, either player near Odessa
    if (both && F.arrived && !F.jamDone && F.talked.hobb && F.talked.pell && !busy) {
      const o = this.npcs.odessa;
      if (players.some(p => p && p.scene === 'dellhollow' && Math.hypot(p.x - o.x, p.y - o.y) < 110))
        this.playJam(players);
    }
    // Beat 5 — down to Lock Five, Maren walking point
    if (both && F.marenDone && !F.lockSeen && !busy &&
        players.some(p => p && p.scene === 'lockfive'))
      this.playLockFive(players);
    // Beat 5 → 5¼ glue — coming up with the plan made, dusk falls: the supper call
    if (both && F.planMade && !F.supperCalled && !busy &&
        players.some(p => p && p.scene === 'dellhollow'))
      this.playSupperCall(players);
    // Beat 5¼ — the supper, after a free-roam breath in the cottage (or at the hearth)
    if (both && F.supperCalled && !F.supperDone && !busy &&
        vesper.scene === 'cottage' && lake.scene === 'cottage') {
      this._supT = (this._supT || 0) + dt;
      if (this._supT > 8) this.playSupper2(players);
    }
    // Beat 5½ — the dock scene, after a short free-roam breath
    if (both && F.nightFallen && !F.dockDone && !busy &&
        vesper.scene === 'dellhollow' && lake.scene === 'dellhollow') {
      this._dockT = (this._dockT || 0) + dt;
      if (this._dockT > 2.0) this.playDockNight(players);
    }
    // Beat 6 — the winches: both players down in the dark
    if (both && F.dockDone && !F.boatDown && !busy &&
        vesper.scene === 'lockfive' && lake.scene === 'lockfive')
      this.playWinches(players);

    // followers — Mochi rides along all chapter
    if (!Cutscene.active) this.updateFollowers(dt, players);

    if (F.ended) F.endT += dt;
  },

  updateFollowers(dt, players) {
    const ps = players.filter(p => p && !p.hidden && !p.parked);
    if (!ps.length) return;
    const jobs = [
      { e: this.npcs.mochi, target: ps[0], offs: [[-40, 8], [40, 8], [0, -45], [0, 45]], near: 60, far: 85, snap: 240, spd: 200 },
    ];
    for (const { e, target, offs, near, far, snap, spd } of jobs) {
      if (!e || !e.follow || e.hidden) continue;
      e.scene = target.scene;
      let tx = target.x + offs[0][0], ty = target.y + offs[0][1], restOk = false;
      for (const [ox, oy] of offs) {
        if (fieldWalkable(target.scene, target.x + ox, target.y + oy)) { tx = target.x + ox; ty = target.y + oy; restOk = true; break; }
      }
      const dx = tx - e.x, dy = ty - e.y, d = Math.hypot(dx, dy);
      if (d > snap) { e.x = tx; e.y = ty; e.moving = false; }
      else if (d > near && (restOk || d > far)) {
        e.moving = true; e.animT += dt;
        const step = Math.min(spd, d * 2.4) * dt;
        const nx = e.x + dx / d * step, ny = e.y + dy / d * step;
        const curOk = fieldWalkable(e.scene, e.x, e.y);
        let moved = false;
        if (dx && (fieldWalkable(e.scene, nx, e.y) || !curOk)) { e.x = nx; moved = true; }
        if (dy && (fieldWalkable(e.scene, e.x, ny) || !curOk)) { e.y = ny; moved = true; }
        if (!moved) {
          const px2 = -dy / d, py2 = dx / d;
          for (const sgn of [1, -1]) {
            const sx2 = e.x + px2 * sgn * step * 0.9, sy2 = e.y + py2 * sgn * step * 0.9;
            if (fieldWalkable(e.scene, sx2, sy2)) { e.x = sx2; e.y = sy2; break; }
          }
        }
        e.dir = dx > 0 ? 'right' : 'left';
      } else e.moving = false;
    }
  },

  objective() {
    const F = this.flags;
    if (F.ended) return '';
    if (!F.descentIntro) return '';
    if (!F.arrived) {
      if (!F.chartDone) return 'Down the switchbacks — the road knows the way';
      return 'Down — Dellhollow is not on the map';
    }
    if (!F.jamDone) {
      const n = Object.keys(F.talked).length;
      if (n < 2) return `Dellhollow — meet the quay (${n}/2)`;
      return 'The lockhead — ask the harbormistress about passage north';
    }
    if (!F.lockSeen) return 'Down to Lock Five — the stairs, not the water';
    if (!F.nightFallen) return F.supperCalled
      ? 'Supper at the keepers’ cottage — the low door on the stair-street'
      : 'Evening — back up to the quay';
    if (!F.dockDone) return 'Night on the quay';
    if (!F.boatDown) return 'Meet Maren at the deep stairs — quietly';
    return '';
  },

  /* markers — hooks read by main.js drawMarkers */
  lampHintActive() { return false; },
  storyMarker() {
    const F = this.flags;
    if (Field.currentKey === 'dellhollow') {
      // ✦ over Odessa once both quay voices are heard
      if (F.arrived && !F.jamDone && F.talked.hobb && F.talked.pell) {
        const o = this.npcs.odessa;
        return { x: o.x, y: o.y - o.h - 18 };
      }
      // ✦ over the deep-stairs stairhead when the way down is the story
      if ((F.marenDone && !F.lockSeen) || (F.dockDone && !F.boatDown))
        return { x: 1240, y: 560 };
      // ✦ over the west stairs gate when supper is calling them up
      if (F.supperCalled && !F.supperDone) return { x: 30, y: 125 };
      return null;
    }
    if (Field.currentKey === 'stairs') {
      // ✦ over the keepers' door during the supper window
      if (F.supperCalled && !F.supperDone) return { x: 985, y: 470 };
      return null;
    }
    return null;
  },

  /* ================= interaction ================= */
  nearestThing(p) {
    const F = this.flags;
    let best = null, bd = Infinity;
    const consider = (x, y, thing, r) => {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d > (r || 85)) return;
      if (d < bd) { bd = d; best = thing; }
    };
    for (const n of Object.values(this.npcs)) {
      if (n.hidden || n.scene !== p.scene) continue;
      if (n.key === 'mochi' && n.follow) continue;    // considered last, below
      if (n.key === 'stranger' || n.key === 'boat' || n.key === 'tenant') continue;
      consider(n.x, n.y, { kind: 'npc', key: n.key, ent: n }, n.interactR);
    }
    if (p.scene === 'descent') {
      consider(660, 170, { kind: 'bracket', at: [660, 95] }, 80);
      if (F.chartDone) consider(420, 320, { kind: 'charthalt', at: [400, 245] }, 80);
      consider(672, 700, { kind: 'parapet', at: [672, 660] }, 90);
    }
    if (p.scene === 'dellhollow') {
      consider(170, 300, { kind: 'queue', at: [200, 240] }, 80);
      consider(300, 380, { kind: 'barge', at: [265, 300] }, 75);
      consider(430, 540, { kind: 'eelstall', at: [430, 480] }, 75);
      consider(1025, 270, { kind: 'notice', at: [985, 230] }, 70);
      consider(880, 400, { kind: 'tallybeam', at: [880, 340] }, 75);
      consider(660, 380, { kind: 'wheels', at: [660, 320] }, 70);
      consider(510, 500, { kind: 'lamppole', at: [528, 430] }, 60);
      consider(70, 150, { kind: 'ropebridge', at: [40, 110] }, 75);
      if (F.dockDone) consider(540, 640, { kind: 'dockedge', at: [540, 600] }, 80);
    }
    if (p.scene === 'stairs') {
      consider(520, 610, { kind: 'cistern', at: [455, 540] }, 70);
      consider(500, 330, { kind: 'laundry', at: [500, 160] }, 70);
      consider(860, 650, { kind: 'gullrail', at: [875, 690] }, 65);
      consider(1130, 310, { kind: 'hoist', at: [1130, 250] }, 70);
      consider(985, 585, { kind: 'cottagedoor', at: [985, 470] }, 75);
    }
    if (p.scene === 'cottage') {
      consider(310, 500, { kind: 'tallies', at: [300, 370] }, 75);
      consider(340, 480, { kind: 'coatpeg', at: [295, 375] }, 70);
      consider(830, 450, { kind: 'drawer', at: [825, 330] }, 75);
      consider(690, 380, { kind: 'toolwall', at: [700, 250] }, 75);
      consider(700, 610, { kind: 'tableseats', at: [595, 545] }, 80);
      consider(520, 450, { kind: 'hearthpot', at: [500, 330] }, 75);
    }
    if (p.scene === 'lockfive') {
      consider(600, 690, { kind: 'pool', at: [560, 560] }, 90);
      consider(330, 620, { kind: 'grate', at: [320, 430] }, 80);
      consider(940, 440, { kind: 'flume', at: [920, 250] }, 70);
      consider(950, 480, { kind: 'winch', at: [975, 400] }, 60);
      consider(1090, 480, { kind: 'winch', at: [1080, 415] }, 60);
      consider(700, 655, { kind: 'boatlook', at: [645, 300] }, 70);
    }
    // the following cat never outranks anything else
    const mochi = this.npcs.mochi;
    if (!best && mochi.follow && !mochi.hidden && mochi.scene === p.scene &&
        Math.hypot(p.x - mochi.x, p.y - mochi.y) < 85)
      best = { kind: 'npc', key: 'mochi', ent: mochi };
    return best;
  },

  promptFor(p) {
    if (this.flags.ended) return '';
    if (Cutscene.holdJob) return 'HOLD  A';
    if (Dialog.active()) return 'Next ▸';
    if (Cutscene.active) return '';
    const t = this.nearestThing(p);
    if (t) {
      if (t.kind === 'npc') return 'A — talk to ' + SPEAKERS[t.key].name;
      return 'A — look';
    }
    return '';
  },

  interact(p) {
    const F = this.flags;
    const t = this.nearestThing(p);
    if (!t) return;
    const sys = (text) => Dialog.start([{ who: 'system', text }]);
    if (t.kind === 'npc') return this.talkTo(t.key, t.ent, p);
    /* --- descent --- */
    if (t.kind === 'bracket') return sys('An iron bracket bolted to the rock, empty, at lamp height. Whoever took the lamp unbolted it cleanly and took the bolts too. Thrift, or reverence. On this road, possibly both.');
    if (t.kind === 'charthalt') return sys('The north sheet, corrected in the field: one gorge, one river, one town, inked over forty years of confident heath. The annotation reads "SURVEYED, this time. —V."');
    if (t.kind === 'parapet') return sys('The parapet is polished at the top, the way stone gets where four hundred years of people have leaned to look at home coming up at them.');
    /* --- dellhollow --- */
    if (t.kind === 'queue') return sys('Boats lashed hull to hull, three and four deep, gangplanked into a floating lane. Somebody has strung washing between two masts. Somebody else has planted herbs in a bailing bucket. The queue has become a neighborhood.');
    if (t.kind === 'barge') return sys('Forty tons of pumpkins in elegant rows. The nearest rank has begun, very quietly, to slump. Captain Hobb has arranged the worst of them facing away from the quay, like a man combing his hair over the thin patch.');
    if (t.kind === 'eelstall') return sys('Smoked eel by the yard. The eel-wife’s sign reads "FRESH — ASK HER YOURSELF." The quay finds this funnier than visitors do.');
    if (t.kind === 'notice') return sys('RULINGS OF THE HARBOR. One: the river is right. Two: in disputes, see Ruling One. Three: no boat works Lock Five while the Tenant is below. — O.');
    if (t.kind === 'tallybeam') return sys('The old balance beam. Low down, under wax: a fathom of grey chalk tallies, a big hand’s, ended mid-row one June. Above them, climbing year by year, charcoal: a smaller hand’s, renewed every morning. Nobody has ever cleaned this beam. Nobody ever will.');
    if (t.kind === 'wheels') return sys('The bypass races still turn the wheels — the town grinds, saws, and hoists on water that never asks the locks’ permission. The river is only shut to things that float.');
    if (t.kind === 'lamppole') return sys('A lamp-pole, a ladder, and a wick-knife on a string. In a flame village this corner would be a shrine. Here it is a chore, and the town sleeps just as sound.');
    if (t.kind === 'dockedge') return sys('The bench holds the warmth a while after you stand up. That is all it does, and tonight it was enough.');
    if (t.kind === 'ropebridge') return sys('The west rope bridge, slack-roped and patient, running out over the ravine toward the old rim. It goes to the switchback road eventually, for those with the knees and the nerve. The stair-street has handrails, and better gossip.');
    /* --- stairs --- */
    if (t.kind === 'cistern') return sys('The public cistern, fed off a bypass race somewhere above. A tin cup on a chain, worn bright. Four centuries of the same thirst, and the same answer.');
    if (t.kind === 'laundry') return sys('Laundry strung wall to wall, three stories up — shirts of every size, in every colour boat-paint comes in, snapping in the gorge wind. The town flies its ordinary flags, daily, and nobody salutes.');
    if (t.kind === 'gullrail') return sys('Gulls hold the stair-rail in strict order of seniority, everyone sliding down one place whenever a bigger gull lands at the top. The town underneath runs on roughly the same system, at roughly the same volume.');
    if (t.kind === 'hoist') return sys('A barrel-hoist rigged from a top-floor beam: freight goes up the outside of the house, because the inside is stairs, and the stairs are already full of everyone. Chalked on the wall: load-tallies, initials, and a rude but accurate drawing of a gull.');
    if (t.kind === 'cottagedoor') return sys(F.supperDone
      ? 'Pulled to. The lamp inside is banked low. Let the house keep its keeper tonight.'
      : 'A low door under a lintel carved in miniature: two lock-gates, shut fast, holding back a carved curl of water. On a street of painted doors it is the plainest one — and the only one with a job description over it.');
    /* --- cottage --- */
    if (t.kind === 'tallies') return sys('Small dated marks climb the doorframe: MAREN, and a height; MAREN, and a height — rising like a spring flood, then stopping a hand below the lintel, years ago. Above the last mark, nothing. Her records moved to her arm, and to the beam, and nobody in this house has ever said so out loud.');
    if (t.kind === 'coatpeg') return sys('A man’s oilskin coat on the peg nearest the door, square on its shoulders, oiled this winter the way the boat is tarred. Eleven years of weather have come and gone outside. The coat is ready anyway.');
    if (t.kind === 'drawer') return sys('A small drawer in the dresser, under the window. Every latch in this house is worn bright with use. This one keyhole is worn bright with something else. Locked — not stuck. Locked.');
    if (t.kind === 'toolwall') return sys('Eel-spears, wicked and elderly, racked beside winch-pinions, a gear-puller, and a coil of chain-links: the wall of a house where the river is the family trade. Everything is oiled. Nothing is for show.');
    if (t.kind === 'tableseats') return sys('Two chairs, arm-ends worn to shine by four generations of forearms — and a third seat: a stool, the newest wood in the room by eighty years, standing exactly where a chair would. Nobody says why. The table has learned not to ask.');
    if (t.kind === 'hearthpot') {
      // the hearth is also the supper trigger: fires the beat early, no dwell
      if (F.supperCalled && !F.supperDone) return this.playSupper2(window.players);
      return sys('The stew-pot on its hook, and a fire kept the way locks are kept: banked exact, nothing wasted, nothing out.');
    }
    /* --- lockfive --- */
    if (t.kind === 'pool') return sys('Still black water. She is watching. She was watching before you looked, and she will be watching after you stop — the pale eye neither blinks nor wanders. Being seen is the toll here, and it costs more than it should.');
    if (t.kind === 'grate') return sys(F.lockSeen
      ? 'The sealed gallery, dark weed packed through its bars, carried there strand by strand. The next generation of the river, behind a locked door, with the oldest thing in the water lying guard. …Move along quietly.'
      : 'A timber-and-iron grate, low over the water in the far wall, dark weed packed through its bars. Sealed workings — lock business, and older than anyone doing it.');
    if (t.kind === 'flume') return sys('A mile of black, dropping like a stair through the inside of a cliff. The timber ring is scarred where three centuries of log-drives went through. Boats were never the flume’s business. There is a first time for everything, ideally with a pilot.');
    if (t.kind === 'winch') return sys('A century of grease gone to amber. The left drum might turn, with conviction. The right one has become geology.');
    if (t.kind === 'boatlook') return sys(F.boatDown
      ? 'Clinker-built, tar-dark, rope fenders, a lantern hook at the prow. The tar is this winter’s. Somebody does this boat’s rounds, and has for eleven years, and has never once said so.'
      : 'High in the chains over the water hangs a shrouded shape, small and boat-sized, hoisted clear of the flood. The tarpaulin is neat. The knots are renewed. Somebody tends whatever sleeps up there.');
  },

  /* ================= dialogue ================= */
  talkTo(key, ent, p) {
    const F = this.flags;
    const dx = p.x - ent.x, dy = p.y - ent.y;
    if (key !== 'mochi') ent.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    const D = (lines, onFinish) => Dialog.start(lines.map(l => ({ who: l[0], text: l[1] })), onFinish);

    if (key === 'mochi') {
      if (p.scene === 'dellhollow')
        return D([['system', '(Mochi is sitting at the eel-stall with the composure of a paying customer. The eel-wife has already fed him twice. Neither of them has admitted it.)']]);
      return D([['mochi', 'Mrrp.']]);
    }

    if (key === 'hobb') {
      if (F.nightFallen) return D([['system', '(Captain Hobb has turned in. The pumpkins keep their own watch.)']]);
      const n = F.hobbTalk++;
      if (n === 0) { F.talked.hobb = true;
        return D([
          ['hobb', 'Don’t buy anything, don’t lean on anything, and if you’ve come to gawp at the eel you can gawp at forty ton of pumpkins instead. Going SOFT, the lot of them. In elegant rows.'],
          ['vesper', 'How long have you been in the queue?'],
          ['hobb', 'Nineteen days. “Cut them for pie,” my wife says. Nineteen days of my wife saying pie. It was a bulk contract, madam. Harvest-fair, downriver. There is no fair for a November pumpkin.'],
          ['lake', 'I’m sorry for your cargo.'],
          ['hobb', 'Don’t be sorry, be useful— no. No, forgive me. Nobody’s useful against the river. First thing you learn up here, last thing you believe.'],
        ]);
      }
      return D([['hobb', 'You want north, I hear. So do forty ton of pumpkins. Get in the queue — it’s a very patient queue. We’ve named the seagulls.']]);
    }

    if (key === 'pell') {
      if (F.nightFallen) return D([['pell', 'Night shift. The proper one. Every wick burning, and the river behaving. …Go on about your business, friends — quietly.']]);
      const n = F.pellTalk++;
      if (n === 0) { F.talked.pell = true;
        return D([
          ['pell', 'Watchman. Night shift. It is presently day, which is why I’m holding a wick-knife and a grudge.'],
          ['lake', 'You keep the lantern-strings?'],
          ['pell', 'Every wick, every noon, so they’ll burn every night. No ceremony to it, friend — oil goes in, light comes out, and I’d thank the town to remember who carries the ladder.'],
          ['pell', 'Odd stretch of nights, mind. Three nights back I’m on the rim walk, and there’s a light going north along the old high road. Steady. Didn’t bob, the way a carried lantern bobs. And pale — pale BLUE, like the heart of a hail-cloud.'],
          ['vesper', 'Did you hail it?'],
          ['pell', 'Put my own lamp up, which is the whole language I’ve got. It stopped. A long stop. Then it went on north, and I found I’d sat down on the wall without deciding to.'],
          ['pell', 'Marsh-gas, the harbormistress says. Aye. Well. Marsh-gas doesn’t stop to look back at you.'],
          ['vesper:thinking', '(Filed. Next to the bow.)'],
        ]);
      }
      return D([['pell', 'Sleep’s for the day shift. Which is now. Which is the grudge.']]);
    }

    if (key === 'sorrel') {
      const n = F.sorrelTalk++;
      if (n === 0) {
        return D([
          ['sorrel', 'Mind the drip-line, loves — wash overhead, bread underhand. Half-loaf’s a penny, whole loaf’s a penny and a look at your cat.'],
          ['mochi', 'Mrrp.'],
          ['sorrel', 'Paid in full. Here’s the heel for him, and don’t tell the gulls. Nineteen days of stuck boats is nineteen days of boat-folk buying bread — worst thing ever to happen to this town, and my ovens haven’t cooled since. Don’t tell the harbormistress which way I’m praying.'],
        ]);
      }
      return D([['sorrel', 'Half-loaf’s still a penny. The cat’s credit is good.']]);
    }

    if (key === 'creel') {
      const n = F.creelTalk++;
      if (n === 0) {
        return D([
          ['creel', 'Four hundred years of stairs, stranger. The town’s knees give out before the timber does. I’ve spliced rope on this step since I was the boy with the gulls — and there’s always a boy with the gulls.'],
          ['creel', 'The bridges? Sound as sermons. I splice what they hang from. Rope tells you before it goes — so do stairs, so do most things, if you’re the sort that listens.'],
        ]);
      }
      return D([['creel', 'Mind your feet going down. Coming up, mind everything else.']]);
    }

    if (key === 'nib') {
      const n = F.nibTalk++;
      if (n === 0) {
        return D([
          ['nib', 'That one’s Bailiff, that one’s Soup, and the big one’s called the Harbormistress — don’t TELL the harbormistress.'],
          ['lake', 'Your secret’s kept.'],
          ['nib', 'She knows anyway. She knows everything. Are you the flame people? You’re littler than the quay said.'],
        ]);
      }
      return D([['nib', 'Soup! SOUP! …He knows his name. He just doesn’t respect it.']]);
    }

    if (key === 'odessa') {
      if (ent.scene === 'cottage')
        return D([['odessa:grave', 'Sit or stir, guest. Standing in the middle of a kitchen is for weathervanes.']]);
      if (!F.jamDone) {
        if (F.talked.hobb && F.talked.pell) return this.playJam(window.players);
        return D([['odessa:grave', 'Walk the quay before you spend my time, strangers. The town will tell you most of what I would — and shorter.']]);
      }
      return D([['odessa:grave', 'My ruling stands as posted. And the deep stairs are open to you — my daughter has the showing of it. The stairs, mind. Not the water.']]);
    }

    if (key === 'maren') {
      if (ent.scene === 'cottage')
        return D([['maren:happy', 'Door’s open. Lintel’s low — for tall people and opinions.']]);
      if (F.dockDone) return D([['maren', '(low) Stairs. Quietly. The town sleeps light and my mother doesn’t sleep at all.']]);
      if (F.lockSeen) return D([['maren:determined', 'The flume goes DOWN. Past her, past the locks. It wants water, a boat, and a pilot. Tell my mother none of that, in any order.']]);
      return D([['maren:happy', 'Deep stairs, then. Ma said show you, so I’m showing you — try to look shown when we get down there.']]);
    }
  },

  /* ================= cutscenes ================= */

  // BEAT 1 — chapter open: the descent
  playDescent(vesper, lake) {
    const F = this.flags;
    F.descentIntro = true;
    const mochi = this.npcs.mochi;
    mochi.follow = null;
    Cutscene.play([
      { mood: 'forestB' },
      { banner: { title: '— CHAPTER TWO —', sub: 'Dellhollow', dur: 5 } },
      { cam: { x: 300, y: 260, viewH: 520 } },
      { wait: 1.2 },
      { narrate: 'They walked until the last light of Emberbrook was gone behind them, slept badly under a bramble, and the first morning of winter came up grey and stayed that way.' },
      { narrate: 'Half a morning north of the Gate, the road — old, dressed stone, built by serious people — did something no road on any of Vesper’s charts had ever done. It stepped off the edge of the world.' },
      { move: { ent: mochi, x: 330, y: 240, speed: 150 } },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi sits down at the first switchback and looks back at them, in the manner of a guide waiting for slow clients.)'] },
      { say: ['vesper', 'Switchbacks. Cut switchbacks, Lake — that’s a month of masons per turn. Somebody needed to get down there very badly, a very long time ago.'] },
      { say: ['lake', 'Down where? All I can see is gorge.'] },
      { say: ['vesper', 'Well. That’s the other thing.'] },
      ...this.playValley(vesper, lake),
      { camRelease: true },
      { run: () => { mochi.follow = 'party'; } },
    ]);
  },

  // BEAT 1v — the valley from above: the vista cut, spliced inside playDescent.
  // Returns the steps; the players stay in 'descent' (parked) — only the camera travels.
  playValley(vesper, lake) {
    const park = (on) => { if (vesper) vesper.parked = on; if (lake) lake.parked = on; };
    return [
      { fadeTo: 1 },
      { wait: 0.8 },
      { run: () => { park(true); Field.enter('vista'); Field.cam.x = 455; Field.cam.y = 265; } },
      { cam: { x: 455, y: 265, viewH: 520 } },
      { fadeTo: 0 },
      { wait: 1.2 },
      { narrate: 'They stepped out of the trees onto the rim of the world, and the other thing was this:' },
      { narrate: 'A gorge you could lose a cathedral district in — and it was FULL. The river came in high and silver from the south, stepped down five great timber stairs, and a town went with it: houses stacked down both cliffs and painted every colour a boat can be, one ribbon of loud, lived-in colour down all that grey stone, woodsmoke leaning all one way, strings of unlit lanterns crossing the air like beads on a wire.' },
      { mood: 'dellhollow' },                       // the town theme, early and far away (§f)
      { cam: { x: 672, y: 400, viewH: 520 } },
      { say: ['vesper', 'Not on the sheet. A whole town, Lake. Not on the sheet.'] },
      { say: ['vesper', 'Read it off the water — rivers abbreviate, they don’t lie. In high on the south. Five locks — that’s a STAIR, for boats. Town on both walls, where the work is. And out the far end, low and easy — north, into the haze. That hairline in the right-hand cliff will be a spillway. The rest is people.'] },
      { say: ['lake', 'The little lights, strung straight across the air. Bridges?'] },
      { say: ['vesper', 'Lantern-strings, on rope bridges. A town that ties its own two halves together every morning, and lights the knot at night. …I like them already.'] },
      { cam: { x: 854, y: 420, viewH: 560 } },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi regards the whole descending wonder of it with the enthusiasm of a cat regarding a very large wet staircase. There had better be fish.)'] },
      { narrate: 'Smoke went up. Gulls came down. And out past the last lock the river went on north without waiting for anyone, the way rivers do.' },
      { fadeTo: 1 },
      { wait: 0.8 },
      { run: () => { park(false); Field.enter('descent'); if (vesper) { Field.cam.x = vesper.x; Field.cam.y = vesper.y; } } },
      { fadeTo: 0 },
      { mood: 'forestB' },                          // back on the grey road
    ];
  },

  // BEAT 1 — map-is-wrong at the chart halt
  playChart(players) {
    const F = this.flags;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    Cutscene.play([
      { cam: { x: 420, y: 300, viewH: 460 } },
      { run: () => {                                            // stage: Vesper at the slab, sheet spread; Lake beside
          if (vesper) { vesper.x = 390; vesper.y = 330; vesper.dir = 'up'; }
          if (lake) { lake.x = 460; lake.y = 335; lake.dir = 'up'; }
        } },
      { say: ['vesper', 'Hold this corner. HOLD it, the wind is a critic.'] },
      { say: ['vesper:worried', 'This is my north sheet — forty years old, surveyed by a man with a theodolite and a reputation. It shows this road running on through open heath. Flat. Six more miles of confident little grass symbols.'] },
      { say: ['lake', 'The road disagrees.'] },
      { say: ['vesper', 'The road is going DOWNSTAIRS. There is a gorge here you could lose a cathedral district in, there is a river at the bottom of it — I can HEAR the river — and my best chart of this whole country says: heath.'] },
      { say: ['lake', 'Maybe the theodolite man never came this far.'] },
      { say: ['vesper', 'Oh, he came. He got tired, or the light went, and he guessed — and then he inked the guess like a survey. The oldest sin in cartography, and forty years of travelers have carried it since.'] },
      { say: ['vesper:determined', '(Pen. Rule of the trade: the map is corrected the day you catch it, or the lie outlives its maker.)'] },
      { say: ['lake', '(Eleven days of impossible things, and the one that finally offends her is bad surveying. Noted. It’s good to know what a person’s actually for.)'] },
      { say: ['mochi', 'Mrrp.'] },
      { run: () => { F.chartDone = true; } },
      { camRelease: true },
    ]);
  },

  // BEAT 1 — the Stranger across the ravine (Mochi hiss #1)
  playRavine(players) {
    const F = this.flags;
    const stranger = this.npcs.stranger;
    Cutscene.play([
      { mood: 'silence' },
      { run: () => { stranger.hidden = false; stranger.scene = 'descent'; stranger.x = 1250; stranger.y = 80; stranger.dir = 'down'; } },
      { cam: { x: 1090, y: 200, viewH: 520 } },
      { wait: 1.2 },
      { narrate: 'Across the ravine — a stone’s throw away, and an hour’s walk, and no way over — the old rim road ran on north. Somebody was standing on it.' },
      { say: ['vesper', 'Lake.'] },
      { say: ['lake', 'I see him.'] },
      { say: ['mochi', 'Hhhhhhhh.'] },
      { say: ['system', '(A sound is coming out of Mochi that neither of them has ever heard a cat make. Low. Level. Aimed across the gap.)'] },
      { run: () => {                                            // the ambiguous glint — a cutscene sparkle, not painted
          Particles.burst(6, () => ({ kind: 'sparkle', x: 1236 + (Math.random() - 0.5) * 10, y: 96 + (Math.random() - 0.5) * 14, vy: -3, life: 1.1 }));
        } },
      { say: ['vesper:worried', '(Tall. Hooded. Standing the way a post stands — like the road grew him. Something at his side keeps catching the light. Glass?)'] },
      { say: ['lake', 'Hello the road! Is there a crossing north?'] },
      { wait: 1.0 },
      { narrate: 'The figure did not answer, and did not wave. It turned to face them across the ravine — and bowed. Deep, and slow, and formal: a bow with rules in it, aimed low, at something carried and not at anyone carrying it.' },
      { wait: 0.8 },
      { flash: 0.4 },
      { run: () => { stranger.hidden = true; Net.send({ type: 'buzz', ms: 120 }); } },
      { narrate: 'Between one blink and the next, the rim road was empty.' },
      { wait: 0.8 },
      { say: ['vesper', 'Gone. There is no cover on that stretch. I am LOOKING at the absence of cover.'] },
      { say: ['lake:worried', 'He bowed. That was a real bow — a taught one. Grandmother had one like it and I never learned what it was for.'] },
      { say: ['lake', 'And he aimed it low. At my hands. At the—'] },
      { say: ['vesper', 'Don’t finish that sentence, I’m not ready to file it.'] },
      { say: ['vesper:thinking', '(Entry: one figure, far rim, hooded. Conduct: courteous. Departure: unexplained. Cat’s opinion: extensive, recorded in full.)'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['lake', 'First time in his life he’s made that sound. I’d have been happy never learning he could.'] },
      { mood: 'forestB' },
      { run: () => { F.strangerSeen = true; } },                 // vista exit opens
      { camRelease: true },
    ]);
  },

  // BEAT 1 — the vista (a cam move; the painting's lower band is the reveal)
  playVista(players) {
    Cutscene.play([
      { cam: { x: 672, y: 700, viewH: 768 } },
      { wait: 1.0 },
      { narrate: 'The last switchback turned them around a shoulder of rock, and the gorge opened below like a lit window.' },
      { narrate: 'Closer now, the town stopped being geography and started being NOISE. Hammers. Gulls. Somebody laughing. Somebody selling something. And under everything, patient as a held breath, the river working.' },
      { say: ['lake', 'Listen to it.'] },
      { say: ['vesper', 'I am listening to it. …I’d forgotten what a Tuesday sounds like.'] },
      { say: ['lake', '(Two days. Two days since the square went quiet, and my ears have been ringing with it the whole way. And down there it’s just… going on. All of it. Going on.)'] },
      { camRelease: true },
    ]);
  },

  // BEAT 2 — arrival: the town alive, on the stair-street
  playArrival(players) {
    const F = this.flags;
    F.arrived = true;
    Cutscene.play([
      { mood: 'dellhollow' },
      { cam: { x: 672, y: 300, viewH: 620 } },
      { narrate: 'Dellhollow, of the five locks. It smelled of tar, bread, wet rope and roasting chestnuts, and it sounded like everything Emberbrook had stopped being.' },
      { narrate: 'The road became a street and the street became a stair, and the town happened to them from every side at once: houses standing on each other’s shoulders, every door and shutter painted in somebody’s leftover hull-colours, washing overhead like signal-flags, bunting from some long-finished regatta that nobody had ever taken down — the whole loud, painted, vertical parish descending, arguing, to the water.' },
      { narrate: 'Nobody stared at them. A woman in a bread-window quoted them a price on principle. Two children ran down between the party without apology or slowing, taking the stairs three at a time. It was wonderful.' },
      { say: ['vesper:happy', 'A stair with SHOPS on it. A bread-window. A public cistern with a polished cup. Lake — people. Uninterrupted people, doing ordinary things, at VOLUME, on top of each other, on a cliff.'] },
      { say: ['lake', '(No pedestal. No keeping-flame. I’ve read every doorway on the way down — just oil lamps on strings, lit by whoever’s nearest, meaning nothing.)'] },
      { say: ['lake', '(And it holds. It’s loud, and it’s kind, and it holds together with no flame at all. …Grandmother, what else didn’t you tell me? Or didn’t know?)'] },
      { say: ['system', '(A rope bridge creaks overhead: a woman crosses it with a basket of eels on her hip, treating the air between the cliffs as a footpath — because here, it is one.)'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi has caught wind of the eel-stall. It is somewhere below. Everything worth anything, the cat has concluded, is down — and the party’s marching order has quietly changed.)'] },
      { say: ['vesper', 'Quay first. Towns are like rivers — you read them from the people at the edges. Then whoever’s in charge.'] },
      { camRelease: true },
    ]);
  },

  // BEAT 3 — the jam explained: Odessa's ruling
  playJam(players) {
    const F = this.flags;
    if (F.jamDone) return;
    const { odessa, hobb, pell } = this.npcs;
    Cutscene.play([
      { cam: { x: 960, y: 380, viewH: 540 } },
      { run: () => {                                            // Hobb and Pell drift in to the lockhead
          hobb.scene = 'dellhollow'; hobb.x = 930; hobb.y = 425; hobb.dir = 'up';
          pell.scene = 'dellhollow'; pell.x = 1080; pell.y = 440; pell.dir = 'up';
          odessa.dir = 'down';
        } },
      { say: ['odessa:grave', 'Harbormistress. You’ll be the pair off the rim road — the quay’s told me twice already, with improvements. Say your business plain; I’ve a town of idle boats to keep from stupidity.'] },
      { say: ['vesper', 'Vesper — mapmaker. Lake — lamplighter. We need to go north, faster than walking. Everyone we’ve met says the river is the road.'] },
      { say: ['odessa', 'The river IS the road. The road is shut.'] },
      { say: ['odessa:grave', 'Lamplighter, you said. Off the rim road. …Emberbrook, then. The flame-village on the high valley. You’re a long way below your lamps, boy.'] },
      { say: ['lake', 'Yes. And I’ll say it to you straight, because you’ll hear it crooked off a fish-cart eventually: two nights ago our flame was taken. All of it, in a breath. The village stands — fed, housed, safe. And every soul in it has gone flat. They know their own lives like a ledger and can’t feel one line of them. We’re going north to bring the flame home.'] },
      { wait: 1.2 },
      { say: ['odessa:grave', '…I’ve heard of your lamps the way you’ve maybe heard of our floods. Neighbors’ weather.'] },
      { say: ['hobb', 'Took the— the LIGHTS? All the lights at once? Who’s minding the ovens? A village can’t just— somebody has to mind the ovens.'] },
      { say: ['odessa', 'Hobb.'] },
      { say: ['hobb', 'I’m only saying. Terrible thing. Terrible. My cousins downriver won’t believe half of it.'] },
      { say: ['vesper:thinking', '(They’re sorry the way you’re sorry for an earthquake across the sea. It’s real sorrow. It just has nowhere in them to land — and why would it? You can’t miss a warmth you never sat in.)'] },
      { say: ['odessa:grave', 'Then you have my sympathy, and my sympathy moves no water. Come to the beam. I’ll show you what shut my road.'] },
      { run: () => {                                            // group to the lockhead rail; cam angles down the gorge
          const vesper = players.find(p => p && p.role === 'vesper');
          const lake = players.find(p => p && p.role === 'lake');
          if (vesper) { vesper.x = 1060; vesper.y = 430; vesper.dir = 'down'; }
          if (lake) { lake.x = 1115; lake.y = 460; lake.dir = 'down'; }
          odessa.x = 1085; odessa.y = 410; odessa.dir = 'down';
        } },
      { cam: { x: 1050, y: 520, viewH: 620 } },
      { say: ['odessa', 'Five locks step this water down to the low country. Nineteen days ago, something moved into Lock Five and shut it better than gates ever did. An eel — river-eel, the old kind. Long as a grain-barge, patient as winter, and lying on the only water out of this gorge.'] },
      { say: ['vesper', 'And you can’t… move her along? Drive her down?'] },
      { say: ['odessa:grave', 'Mind how you talk about her in my town.'] },
      { say: ['odessa', 'This town is not frightened of an eel — carry that upriver and down, with my compliments. This town is POLITE to this river. Politeness is why Dellhollow is four hundred years old, and why the rapids are full of towns that weren’t.'] },
      { say: ['hobb', 'What she said. It isn’t fear. It’s manners.'] },
      { say: ['pell', 'And nobody who’s seen her close is in a hurry to be impolite. Which is a different thing from the other word. Which nobody has said.'] },
      { say: ['odessa:grave', 'My ruling stands as posted. No boat works Lock Five while she’s below. She came up for her own reasons; she’ll go down for her own reasons. The river asks a season — the town waits a season. Towns that argue with rivers lose.'] },
      { say: ['vesper', 'We can’t spend a season. Truly. Every day we’re slow, home gets flatter.'] },
      { say: ['odessa', 'Then walk the high road, or wait with the pumpkins. Those are the choices I’ve got to sell.'] },
      { say: ['vesper', 'The high road crossed a ravine this morning without us — there’s a gap in it you could post letters down. How far north does it actually get?'] },
      { say: ['odessa:grave', 'To the Falls Span. Which went, sixty years before I was born — a yard of it left on each rim, like a sentence somebody stopped saying. Everything north of here goes by water. That is what Dellhollow is FOR, and just now Dellhollow isn’t going either.'] },
      { say: ['vesper:thinking', '(And there’s my heath explained. The sheet was drawn while the span still stood — the road ran on, so the pen ran on. The map remembers a bridge the world forgot.)'] },
      { say: ['odessa:grave', 'I’m sorry for your village, lamplighter. I am. But I won’t drown polite strangers to save it faster, and I won’t—'] },
      { say: ['pell', 'OI! HARBORMISTRESS!'] },
      { run: () => { F.jamDone = true; this.playMarenWet(window.players); } },
    ]);
  },

  // BEAT 4 — Maren, entering wet (chained from Beat 3)
  playMarenWet(players) {
    const F = this.flags;
    const { odessa, hobb, pell, maren } = this.npcs;
    Cutscene.play([
      { run: () => {                                            // pell marches maren up from the deep stairs, dripping
          maren.hidden = false; maren.scene = 'dellhollow';
          maren.x = 1180; maren.y = 560; maren.dir = 'left';
          pell.x = 1120; pell.y = 540; pell.dir = 'left';
        } },
      { cam: { x: 1000, y: 460, viewH: 560 } },
      { say: ['pell', 'Fished this out of Five. AGAIN. Swimming, if you please. In the dark. In November. Over THAT.'] },
      { wait: 0.4 },
      { move: { ent: maren, x: 920, y: 430, speed: 160 } },
      { say: ['maren:happy', 'Under. “Over” implies I stayed on top. Morning, Ma.'] },
      { say: ['odessa:grave', 'Maren.'] },
      { say: ['maren', 'Before you start — she watched me the whole way down and the whole way up and she did not care. Nine dives now, and she’s never so much as turned that eye—'] },
      { say: ['odessa', 'Ten.'] },
      { say: ['maren', '…Ten. The point stands!'] },
      { say: ['odessa:grave', 'The point does not stand. The point sinks, like everything else you put in that lock. Home. Dry clothes. Now.'] },
      { say: ['maren:happy', 'Can’t. Company. …Hello! You’re the flame people — whole quay says. Is the cat part of it? The cat looks official.'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['maren:determined', 'Then before my mother says what she’s going to say: take me on. I’m the best water-eye on this quay and every captain rafted out there knows it. I’ve crewed these locks since I was five. I can read this river the way your mapmaker reads a— a map. I know what’s in Five better than any soul living. And I’m seventeen, which is grown, ask anyone who isn’t my mother.'] },
      { say: ['odessa:grave', 'No.'] },
      { say: ['maren', 'You haven’t heard the—'] },
      { say: ['odessa', 'I’ve heard every word of it since you were six and rowing the wash-tub. The answer is the answer. No child of mine works the north river.'] },
      { wait: 0.8 },
      { say: ['maren:determined', 'Say why. Out loud. In front of strangers, say the why.'] },
      { wait: 1.2 },
      { say: ['odessa:grave', '…Mind the beam when you shout. You’ll smudge your father’s marks.'] },
      { cam: { x: 880, y: 380, viewH: 420 } },
      { say: ['system', '(On the old balance beam, low down: a fathom of chalk tallies gone grey under wax — a big hand’s work, ended mid-row. Above them, climbing higher every year, fresher marks in charcoal: a smaller hand’s. Nobody has ever cleaned this beam.)'] },
      { mood: 'silence' },
      { say: ['maren', 'That’s not an answer. It’s never been an answer.'] },
      { say: ['odessa', 'It’s the whole answer. He was the best eye this river ever grew — better than you, and you’re better than everyone else alive. And the north water took him anyway. Between one heartbeat and the next, on a fair morning, in June.'] },
      { say: ['odessa:grave', 'I hauled his boat back up the portage myself. I tar it every winter. I have never once let myself ask why. And I will not stand on my own quay and watch it go north again with you in it.'] },
      { wait: 1.0 },
      { say: ['maren', '…Ma.'] },
      { say: ['odessa', 'Dry clothes. Then — since you’re the standing authority on Lock Five — take our guests down and show them what’s shut my river. SHOW, Maren. The stairs. Not the water.'] },
      { run: () => {                                            // odessa withdraws to the guildhall; pell releases the collar with ceremony
          odessa.x = 1050; odessa.y = 290; odessa.dir = 'up';
          pell.x = 552; pell.y = 468; pell.dir = 'down';
          hobb.x = 330; hobb.y = 350; hobb.dir = 'down';
        } },
      { wait: 0.8 },
      { mood: 'dellhollow' },
      { say: ['maren:happy', '…She tars the boat. Every winter. She thinks I don’t know.'] },
      { say: ['vesper:thinking', '(New page. “Dellhollow. Population: alive, loud, and not saying the word afraid. The harbormistress’s daughter keeps her ledger in charcoal, on herself. The beam is a ledger too.”)'] },
      { run: () => {                                            // maren waits at the stairhead; deep stairs open
          F.marenDone = true;
          maren.x = 1150; maren.y = 600; maren.dir = 'down';
        } },
      { camRelease: true },
    ]);
  },

  // BEAT 5 — down to Lock Five: the Tenant
  playLockFive(players) {
    const F = this.flags;
    F.lockSeen = true;                                          // latched at cutscene start
    const maren = this.npcs.maren;
    Cutscene.play([
      { mood: 'silence' },
      { run: () => {                                            // Maren walked point — she's at the stair foot
          maren.scene = 'lockfive'; maren.x = 1180; maren.y = 330; maren.dir = 'down';
        } },
      { cam: { x: 1100, y: 300, viewH: 560 } },
      { narrate: 'The stairs went down past the third lock, and the fourth, into the cool black under the town — two hundred steps of wet timber, with the river talking to itself inside the walls.' },
      { say: ['maren:happy', 'Mind the forty-first step, it lies. So — Lake of Emberbrook. Vesper of— what’s yours? Everyone’s of somewhere. I’m of HERE, four generations; you can’t get rid of us with a flood, they tried.'] },
      { say: ['lake', 'Emberbrook. Born a lane off the square. I know every window.'] },
      { say: ['maren', 'And you?'] },
      { wait: 0.8 },
      { say: ['vesper', '…Around. Professionally around.'] },
      { say: ['maren', 'That’s not a somewhere.'] },
      { say: ['vesper', 'No. It isn’t. Mind your forty-first step.'] },
      { say: ['maren:happy', '(loud whisper, to Lake) Is she always—'] },
      { say: ['lake', 'Yes.'] },
      { say: ['vesper', 'The marks on your arm. You’re a ledger too.'] },
      { say: ['maren', 'Locks worked. Da chalked his on the beam; I wasn’t allowed the beam yet, so — arm. Charcoal washes off, so I redraw them every morning.'] },
      { say: ['maren:determined', 'It’s not sad. It’s bookkeeping.'] },
      { wait: 0.6 },
      { cam: { x: 620, y: 480, viewH: 700 } },
      { narrate: 'Lock Five was a cathedral that worked for a living: black timber going up out of lantern-reach, chains hanging like bell-ropes — and a flooded chamber of still, dark water, with the dark in it coiled.' },
      { say: ['system', '(She is there. She was always going to be there, and it still lands like a hand closing on the back of the neck: a body thicker than a barrel, mottled moss-and-bronze, old scars like map-lines, laid around the chamber in two easy coils. One pale eye, clouded like a lamp behind fog, is open.)'] },
      { say: ['vesper:worried', '…You swam in this.'] },
      { say: ['maren:awed', 'Ten times. Look at her. LOOK at her. She was in this river when the locks were still trees.'] },
      { say: ['lake', '(The eye moved. Not at the lantern — at us. I have never been read so thoroughly by anything, and I grew up under my grandmother.)'] },
      { say: ['maren', 'The Tenant, the quay calls her. Under Dellhollow longer than any family in it. Never once paid rent.'] },
      { say: ['maren:determined', 'Now the part nobody up top will hear me out on. She’s not hunting and she’s not lost. Eels her size hold the deep banks, the low country — they do not climb five locks for fun. And watch. Every hour, near enough, she does THAT.'] },
      { run: () => {                                            // ripple FX: the great body eases toward the grate and back
          Net.send({ type: 'buzz', ms: 100 });
          Particles.burst(14, () => {
            const t = Math.random();
            return { kind: 'sparkle', x: 555 - t * 235 + (Math.random() - 0.5) * 30, y: 495 - t * 110 + (Math.random() - 0.5) * 20, vy: -2, life: 1.6 };
          });
        } },
      { say: ['system', '(The coils unwind by a fathom. She crosses to the left wall — to a sealed grate, timber and iron, low over the water — and lies against it a long moment, whiskered chin to the bars. Then she comes back, and settles, and watches them again.)'] },
      { say: ['vesper', 'The grate. What’s behind the grate?'] },
      { say: ['maren', 'Sluice gallery. Old workings — draws the chamber down when they need her dry. Sealed since granddad crewed.'] },
      { say: ['vesper:thinking', 'She’s not resting against it. She’s TENDING it. Circuit, wall, back — that’s not an animal loafing. That’s a round.'] },
      { say: ['lake', '…Like a keeper.'] },
      { say: ['maren:awed', 'The weed. There’s weed packed through those bars — I saw it on dive six and called it flood-trash. She CARRIED it there. She’s nesting. Eggs in my sluice gallery — that’s why she won’t go down—'] },
      { say: ['vesper', 'She won’t go anywhere. Nothing that tends leaves the thing it tends.'] },
      { say: ['maren', '(quiet) Funny, though. The old pilots always said the deep banks were thick with her kind. It’s been dead quiet down there this year. Maybe that’s why she came all the way up.'] },
      { wait: 0.8 },
      { say: ['maren:determined', 'So it’s worse than the town thinks. Eel eggs, in cold water? She could be over that gallery till spring. Ma’s season just got five months longer, and nobody knows it but the four of us.'] },
      { say: ['vesper', 'Then nobody waits her out, and nobody in their right mind moves her off a nest. Which leaves— Maren. What is that?'] },
      { cam: { x: 1000, y: 320, viewH: 520 } },
      { say: ['system', '(High in the cliff wall, above the waterline: a round timber-ringed mouth, dry and dark, big enough to swallow a boat whole. Two winches crouch on the apron before it, under a hundred years of grease and rust.)'] },
      { say: ['maren', 'The flume. High-water spillway — the old boys cut it to shoot timber and spring floods past the bottom locks, straight down to the tailwater pool. Dry since before I was born. It’s a mile of black, it drops like a stair, and the head-gate winches seized when granddad was young.'] },
      { say: ['vesper', 'But it goes DOWN. Past the locks. Past her — without opening one gate over that nest.'] },
      { say: ['maren:awed', 'It goes down. …You’d need water in it — the head-gates draw off the top of this pool; she’d feel weather, nothing worse. You’d need a boat that can take a beating. And you’d need a pilot who holds the mile of black in her head.'] },
      { say: ['maren:determined', 'You’d need me.'] },
      { say: ['lake', 'Your mother—'] },
      { say: ['maren:determined', 'Said show you Five. I’m showing you Five.'] },
      { say: ['vesper:thinking', '(For the record: the plan is insane, the pilot is seventeen, and the chart of the flume exists in exactly one living head. …I’ve been that head. New page.)'] },
      { run: () => { F.planMade = true; } },
      { camRelease: true },
    ]);
  },

  // BEAT 5 → 5¼ glue — dusk falls on the way back up: the supper call
  playSupperCall(players) {
    const F = this.flags;
    F.supperCalled = true;                                      // latched at cutscene start
    const { maren, odessa } = this.npcs;
    Cutscene.play([
      { run: () => {                                            // Maren up from the stairhead to meet them
          maren.hidden = false; maren.scene = 'dellhollow';
          maren.x = 1150; maren.y = 600; maren.dir = 'left';
        } },
      { cam: { x: 900, y: 540, viewH: 520 } },
      { move: { ent: maren, x: 760, y: 560, speed: 170 } },
      { narrate: 'They came up out of the lock-dark into the last of the light: dusk sliding down both cliffs, and the first lantern going up the stair-street like the first bead on a wire.' },
      { say: ['maren:happy', 'There you are. Right — orders, and not mine, so don’t argue with ME: Ma says the flame people eat at ours tonight.'] },
      { say: ['vesper', 'She says, or she asks?'] },
      { say: ['maren', 'She SAYS. Asking is for the guild. It’s the low door on the stair-street — the one with the gates carved over. I’ll go ahead; somebody has to warn the stew.'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['maren:happy', 'Yes, the cat’s invited. The cat was invited FIRST, if you want the order of it.'] },
      { run: () => {                                            // the house fills: Odessa home cooking, Maren ahead
          odessa.scene = 'cottage'; odessa.x = 520; odessa.y = 445; odessa.dir = 'right';
          maren.scene = 'cottage'; maren.x = 750; maren.y = 600; maren.dir = 'left';
        } },
      { camRelease: true },
    ]);
  },

  // BEAT 5¼ — supper at the keepers' cottage (absorbs the shipped nightfall)
  playSupper2(players) {
    const F = this.flags;
    F.supperDone = true;                                        // latched at cutscene start
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const { maren, odessa, hobb, sorrel, creel, nib, mochi } = this.npcs;
    Cutscene.play([
      { fadeTo: 1 },
      { wait: 0.8 },
      { run: () => {                                            // everyone to the table
          if (vesper) { vesper.scene = 'cottage'; vesper.x = 545; vesper.y = 470; vesper.dir = 'right'; }
          if (lake) { lake.scene = 'cottage'; lake.x = 680; lake.y = 480; lake.dir = 'left'; }
          maren.scene = 'cottage'; maren.x = 560; maren.y = 600; maren.dir = 'up';      // THE STOOL
          odessa.scene = 'cottage'; odessa.x = 520; odessa.y = 445; odessa.dir = 'right';  // at the pot
          mochi.follow = null; mochi.scene = 'cottage'; mochi.x = 460; mochi.y = 640; mochi.dir = 'up';
          Field.enter('cottage');
          Field.cam.x = 640; Field.cam.y = 490;
        } },
      { cam: { x: 640, y: 490, viewH: 580 } },
      { mood: 'dellhollowNight' },                              // the town theme at house scale (§f)
      { fadeTo: 0 },
      { wait: 0.6 },
      { narrate: 'The keepers’ cottage held its heat the way the gorge held the town: close, and hard-won. Eel stew on the hook, bread in the window-iron, and the river talking quietly under the floorboards, off shift but never off duty.' },
      { say: ['odessa:grave', 'Wash. Basin’s by the door. The cat eats on the step, and knows it.'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi eats on the step. On the WARM half of the step. The negotiation takes four seconds, and Odessa loses exactly half of it, and does not appear to mind the arithmetic.)'] },
      { say: ['system', '(She serves the way she runs the locks: in order, without hurry, every bowl filled before her own is even down. She has not sat yet. It is not clear the chair expects her to.)'] },
      { say: ['maren:happy', 'So — this is the house. Four generations. That beam’s off a barge that sank in the ’02 flood, Da reclaimed it — well, GRAND-da — and that’s the good table. We’re eating at the good table. Ma got out the good table.'] },
      { say: ['odessa:grave', 'The table we eat at.'] },
      { say: ['maren', 'The good one.'] },
      { cam: { x: 420, y: 480, viewH: 460 } },
      { say: ['system', '(By the door, climbing the frame: small dated marks. MAREN, and a height. MAREN, and a height. They rise like water coming up a lock wall — and stop, a hand below the lintel, years ago.)'] },
      { say: ['lake', 'The doorframe. Emberbrook does the same — Grandmother kept mine on the pantry door.'] },
      { say: ['maren', 'Ma stopped measuring me at fourteen.'] },
      { say: ['odessa:grave', 'You stopped standing still.'] },
      { mood: 'silence' },                                      // music out for the middle of the table
      { wait: 0.8 },
      { say: ['maren', 'You never asked me to.'] },
      { say: ['system', '(Odessa says nothing. Odessa puts a second helping into Maren’s bowl before Maren has noticed the first is gone. That, apparently, is the sentence.)'] },
      { cam: { x: 640, y: 490, viewH: 580 } },
      { say: ['vesper', 'Harbormistress — your house has one lock in it. Forgive me; I survey rooms, it’s a disease. Every latch here is worn bright with use. One keyhole is worn bright with something else.'] },
      { say: ['odessa:grave', 'And it will stay one.'] },
      { say: ['maren', 'It’s the—'] },
      { say: ['odessa', 'Maren.'] },
      { say: ['maren', '…It’s nothing. Dresser drawer. Sticks.'] },
      { say: ['system', '(It is a small drawer, in the dresser, under the window. The wood around the keyhole is clean. The keyhole does not stick. Nobody at this table believes the drawer is nothing, including, just possibly, the drawer.)'] },
      { say: ['vesper:thinking', '(A mother, a daughter, one table, and one locked thing in the middle of it, politely orbited. So this is what other people’s kitchens are for. …Filed. And for once, the file can stay shut.)'] },
      { wait: 0.8 },
      { mood: 'dellhollowNight' },                              // music back with the kitchen rhythm
      { say: ['system', '(Lake, without asking, has found the cloth, the kettle-hook, and the rhythm of somebody else’s kitchen. He and Odessa work around each other like two halves of one watch.)'] },
      { say: ['odessa:grave', 'You’ve kept house.'] },
      { say: ['lake', 'Kept a lamp. It’s the same wrist.'] },
      { say: ['odessa', 'Mm.'] },
      { say: ['system', '(From the harbormistress, that is a commendation with a seal on it.)'] },
      { say: ['system', '(Going to hang the cloth, Lake finds one peg by the door already taken: a man’s oilskin, oiled this winter, hung square. He hangs the cloth on the peg below it, and asks nothing — and Odessa watches him not ask, and fills his bowl again.)'] },
      { say: ['maren:happy', 'Anyway — tomorrow we thought we’d see the town. More of the town. There’s… plenty of town.'] },
      { say: ['lake', '(She is the worst liar on this river. Her mother is letting her be.)'] },
      { say: ['odessa:grave', 'Mind the tide, then. Seeing your town.'] },
      { wait: 1.0 },
      { narrate: 'The stew went, and the bread went after it, and the lamp burned down the way house-lamps do — unwatched, and trusted.' },
      { say: ['odessa:grave', 'Night’s down. Take the stair slow, strangers. Mind the—'] },
      { say: ['maren', 'Forty-first step.'] },
      { mood: 'silence' },
      { wait: 1.2 },
      { say: ['maren', '(quiet) …You know the step joke.'] },
      { say: ['odessa:grave', 'I taught him the step joke.'] },
      { fadeTo: 1 },
      { wait: 1.2 },
      { run: () => {                                            // NIGHTFALL — the absorbed playNightfall body
          Field.setSceneState('dellhollow', 'night');
          Field.setSceneState('stairs', 'night');
          Field.setSceneState('lockfive', 'night');
          FX.desatTarget = 0.35;
          Field.scenes.dellhollow.lamps.forEach(l => { l.lit = true; });
          Field.scenes.stairs.lamps.forEach(l => { l.lit = true; });
          maren.hidden = true;                          // gone ahead — to rig chains
          hobb.hidden = true;                           // the town turns in; Pell keeps the night
          sorrel.hidden = true; creel.hidden = true; nib.hidden = true;
          // odessa stays in the cottage (the door is closed to re-entry now)
          if (vesper) { vesper.scene = 'stairs'; vesper.x = 940; vesper.y = 600; vesper.dir = 'down'; }
          if (lake) { lake.scene = 'stairs'; lake.x = 1020; lake.y = 610; lake.dir = 'down'; }
          mochi.follow = 'party'; mochi.scene = 'stairs'; mochi.x = 980; mochi.y = 645; mochi.dir = 'down';
          Field.enter('stairs');
          if (vesper) { Field.cam.x = vesper.x; Field.cam.y = vesper.y; }
          F.nightFallen = true;                         // ← the shipped flag, latched HERE now
        } },
      { mood: 'dellhollowNight' },
      { fadeTo: 0 },
      { narrate: 'They stepped out into a night already down, the lantern-strings burning above the stair-street like beads of held breath. Maren had gone past them somewhere between the bread and the door, two steps at a time, already rigging chains in her head.' },
    ]);
  },

  // BEAT 5½ — the dock, at night: Vesper's scene
  playDockNight(players) {
    const F = this.flags;
    F.dockDone = true;                                          // latched at cutscene start
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const maren = this.npcs.maren, mochi = this.npcs.mochi;
    Cutscene.play([
      { mood: 'dellhollowNight' },
      { cam: { x: 560, y: 590, viewH: 460 } },
      { run: () => {                                            // stage: seated at the dock edge; mochi between them
          if (vesper) { vesper.x = 505; vesper.y = 638; vesper.dir = 'down'; }
          if (lake) { lake.x = 578; lake.y = 642; lake.dir = 'down'; }
          mochi.follow = null; mochi.scene = 'dellhollow'; mochi.x = 540; mochi.y = 652; mochi.dir = 'down';
        } },
      { narrate: 'Night, on the quay. The lantern-strings burned in long swags over the water — ordinary oil, ordinary light — and under them the town went warmly about its evening as if that were nothing at all.' },
      { say: ['lake', 'Pell lit half of these and complained the whole time. A fish-wife did three while I watched — one-handed, still arguing about brill. Anyone. They just… light them.'] },
      { say: ['vesper', 'And it’s enough. That’s the thing rattling around in you tonight, isn’t it. It’s enough.'] },
      { say: ['lake', '…I’ll manage. It’s a good rattle. Ask me your real question.'] },
      { say: ['vesper', 'I don’t have a—'] },
      { say: ['lake', 'Maren asked where you’re from. You answer everything, Vesper. Usually with footnotes. You didn’t answer her.'] },
      { wait: 1.2 },
      { say: ['vesper', '…I don’t know where I’m from. That’s the whole answer. It isn’t tragic, so don’t make the face.'] },
      { say: ['lake', 'This is my listening face.'] },
      { say: ['vesper', 'We moved when I was six. The way families do — work, weather, roads. No story to it. My parents are warm people, Lake. Genuinely. Ask about last summer, you get stories — three hours of stories, my father does the voices.'] },
      { say: ['vesper', 'Ask about anything before I was born, you get weather.'] },
      { say: ['vesper', '“Where did you two meet?” — “Oh, it was a wet spring.” A wet SPRING. Twenty years of asking, and I hold a complete meteorological record of my own family and not one placename.'] },
      { say: ['lake', 'Every family has a fog somewhere. Half of Emberbrook can’t name a great-grandmother.'] },
      { say: ['vesper', 'That’s what I decided too. People move. The past gets left behind for practical reasons. Nobody owes their childhood an atlas.'] },
      { say: ['vesper', 'I remember three things from before. A well with a cracked cap. A fence with a gate that dragged. And a hill — round, bald on top, off east from a kitchen window.'] },
      { say: ['vesper', 'I remember the hill perfectly, Lake. I could draw you the hill — I HAVE drawn the hill; it’s numbered. And I feel nothing about it. People feel things about home. I’ve watched you do it all week — it costs you something every time you say “Emberbrook.” My hill is a landform.'] },
      { say: ['lake', '(She says it the way she’d report a survey error. Which, I am beginning to understand, is exactly what she thinks it is.)'] },
      { say: ['lake', '…And the routes.'] },
      { say: ['vesper', 'And the routes. Eleven years of them. Nobody commissions the routes I walk — surveyors follow the trade; I go along everything, in order. You know what you call walking every road out of every market town on a sheet, in sequence?'] },
      { say: ['lake', 'A grid.'] },
      { say: ['vesper', 'A grid. Thank you. A search would be emotional. A grid is just thorough. Somewhere there is a well, a fence, and a round bald hill that line up out a kitchen window — and the day I walk over the right rise, I’ll know it. And then I’ll finally have an answer for everyone’s favorite small question.'] },
      { say: ['vesper', 'It’s a filing problem. I file. Don’t make it a wound, or I’ll invoice you for the honeybun I know you’ve been saving.'] },
      { say: ['system', '(Lake hands over the honeybun. He had been saving it. He does not make it a wound.)'] },
      { say: ['lake', 'For the record — the day you walk over the right rise. I’d like to be there.'] },
      { say: ['vesper', '…Noted. For the record.'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi has been asleep against the woman with no somewhere for the better part of an hour. Cats file things too.)'] },
      { wait: 1.0 },
      { run: () => { maren.hidden = false; maren.scene = 'dellhollow'; maren.x = 1150; maren.y = 620; maren.dir = 'left'; } },
      { move: { ent: maren, x: 700, y: 630, speed: 170 } },
      { say: ['maren:determined', '(low) Oi. Flame people. Tide’s slack, town’s asleep, boat’s on the chains. …Well? It’s a very good hour for being impolite quietly.'] },
      { say: ['vesper', '(One day in, and the girl who can’t leave home is smuggling us out of it. I like her enormously. This is also going to be a problem.)'] },
      { run: () => { mochi.follow = 'party'; } },
      { camRelease: true },
    ]);
  },

  // BEAT 6 — the twin winches, and Odessa's station
  playWinches(players) {
    const F = this.flags;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const { maren, odessa, boat, mochi } = this.npcs;
    Cutscene.play([
      { mood: 'silence' },
      { run: () => {                                            // stage: Maren already below, at the chains
          maren.hidden = false; maren.scene = 'lockfive'; maren.x = 760; maren.y = 640; maren.dir = 'up';
          mochi.follow = null; mochi.scene = 'lockfive'; mochi.x = 700; mochi.y = 680; mochi.dir = 'up';
        } },
      { cam: { x: 620, y: 420, viewH: 680 } },
      { narrate: 'Lock Five at midnight was blacker than the flume it kept. The work-lanterns made two small rooms of light in a dark the size of a church. The Tenant’s eye was open. The Tenant’s eye, they were coming to understand, was always open.' },
      { say: ['maren', 'Chains first. She’s watched me rig them all week and offered no opinion — which, from her, is a permit.'] },
      { run: () => {                                            // the boat comes down out of the dark to the water's edge
          boat.hidden = false; boat.scene = 'lockfive'; boat.x = 620; boat.y = 620; boat.dir = 'right';
          AudioSys.rumble();
        } },
      { say: ['system', '(Down out of the dark comes a boat: clinker-built, tar-dark, rope fenders, a lantern hook at the prow. Small, old, and kept the way tools are loved by people who won’t say so out loud. The tar is fresh.)'] },
      { say: ['lake', '(He knows whose it is before anyone says. Somebody does this boat’s rounds.)'] },
      { say: ['maren', 'Da’s. Ma thinks it hangs down here because she hauled it here. It hangs here because I climb down and sit in it, some nights. …Don’t tell her that. She has enough weather.'] },
      { say: ['mochi', 'Mrrp?'] },
      { say: ['system', '(Mochi looks at the boat. Mochi looks at the water beneath the boat, and at the shape in the water beneath the boat. Mochi sits down to reconsider the terms of his employment.)'] },
      { say: ['maren:determined', 'Head-gates. Twin winches, twin bars. Order of operations: LEFT winch first, to half — or the flume takes her water sideways and we all learn a great deal very fast. Both of you on the bar. And don’t stop on the squeal. The squeal is it working.'] },
      { run: () => {                                            // stage: vesper + lake at winch L; maren spotting the gate
          if (vesper) { vesper.x = 930; vesper.y = 480; vesper.dir = 'up'; }
          if (lake) { lake.x = 985; lake.y = 495; lake.dir = 'up'; }
          maren.x = 1040; maren.y = 540; maren.dir = 'up';
        } },
      { cam: { x: 1000, y: 400, viewH: 560 } },
      { bothHold: { prompt: 'HOLD  A — the left winch, together', dur: 2.2 } },
      { shake: 3 },
      { run: () => { AudioSys.rumble(); Net.send({ type: 'buzz', ms: 250 }); F.gateHalf = true; } },
      { say: ['system', '(A hundred years of rust lets go a degree at a time. Somewhere inside the cliff, water finds a passage it had forgotten — and the flume mouth begins, hollowly, to breathe.)'] },
      { say: ['maren:happy', 'HA! Half-gate! Hear her? That’s the flume clearing its throat. Right winch now — and the right one’s the widow. Seized since granddad. She’ll fight.'] },
      { run: () => {                                            // stage: both players at winch R; they heave — nothing
          if (vesper) { vesper.x = 1055; vesper.y = 480; vesper.dir = 'up'; }
          if (lake) { lake.x = 1115; lake.y = 495; lake.dir = 'up'; }
          maren.x = 990; maren.y = 545; maren.dir = 'up';
        } },
      { wait: 1.0 },
      { say: ['system', '(The right-hand bar does not move. It has spent a lifetime becoming part of the cliff, and it declines — politely, completely — to stop being cliff.)'] },
      { say: ['lake', 'It’s not rust on this one. The drum’s crowned over. We’re two pairs of hands short of—'] },
      { run: () => {                                            // lantern-light on the stairs, descending, unhurried
          odessa.hidden = false; odessa.scene = 'lockfive';
          odessa.x = 1200; odessa.y = 310; odessa.dir = 'down';
        } },
      { say: ['system', '(There is a lantern coming down the stairs. It does not hurry. It has never needed to hurry. Everyone born in this town knows the harbormistress’s step.)'] },
      { wait: 1.2 },
      { move: { ent: odessa, x: 1140, y: 450, speed: 100 } },
      { say: ['maren', '…Ma.'] },
      { say: ['odessa:grave', 'Forty years I’ve kept this gorge. Did the pack of you imagine a gate-chain moves ANYWHERE in it at midnight without my pillow hearing it?'] },
      { wait: 1.0 },
      { say: ['odessa:grave', '…That bar is cut for six hands. Move over.'] },
      { say: ['system', '(She pulls the heavy gloves from her belt — worn to the shape of exactly this work — and sets herself at the bar like a woman coming home to an argument.)'] },
      { move: { ent: odessa, x: 1090, y: 470, speed: 90 } },
      { say: ['maren:awed', 'Ma—'] },
      { say: ['odessa', 'Turn.'] },
      { bothHold: { prompt: 'HOLD  A — the widow-winch, all together', dur: 2.6 } },
      { flash: 0.6 }, { shake: 5 },
      { run: () => {
          F.gatesOpen = true;
          AudioSys.rumble(); AudioSys.chime(); Net.send({ type: 'buzz', ms: 500 });
          Particles.burst(24, () => ({ kind: 'sparkle', x: 920 + (Math.random() - 0.5) * 140, y: 220 + (Math.random() - 0.5) * 80, vy: -8, life: 1.2 }));
        } },
      { narrate: 'The widow-winch came off her century all at once — and the river stood up and walked into the mountain. White water took the dry mile in one long swallowed roar, and the whole chamber rang like the inside of a drum.' },
      { say: ['maren:happy', 'FULL GATE! She’s running! Oh, she sounds like Da always said — like weather underground—'] },
      { say: ['odessa:grave', 'The head-gates draw off the top of the pool. Nothing below the waterline will feel more than weather — her gallery holds its level. I cut my teeth on those sums, girl; don’t look so surprised.'] },
      { wait: 1.0 },
      { say: ['odessa:grave', 'Maren.'] },
      { say: ['maren:determined', 'Say it, then. Say no.'] },
      { wait: 1.6 },
      { say: ['odessa:grave', '…Who else knows the mile of black.'] },
      { say: ['system', '(It is not permission. It is arithmetic, done out loud by the only person in Dellhollow honest enough to do it. Maren does not whoop. Somehow, she does not whoop.)'] },
      { say: ['odessa', 'Stern for you. Weight low past the eye — all of you, low, and hands inboard. I’ll take the portage stair; I’ll be at the tailwater before the sun is.'] },
      { say: ['odessa:grave', '…Don’t make me stand there long.'] },
      { say: ['system', '(Boarding order: Maren to the stern like gravity is optional. Lake amidships, the lighter warm inside his coat. Vesper to the bow, notebook triple-wrapped in oilcloth. Mochi—)'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi is not aboard. Mochi is delivering, from the apron, a position paper on boats. Lake holds open the satchel. A long negotiation occurs, at the speed of cat. Mochi boards the satchel facing backward, as if the whole arrangement were his own idea and everyone else were late.)'] },
      { run: () => { F.boatDown = true; this.playFlumeRun(window.players); } },
    ]);
  },

  // BEAT 7 — the flume run (chained from Beat 6)
  playFlumeRun(players) {
    const F = this.flags;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const { maren, odessa, boat, tenant, mochi } = this.npcs;
    Cutscene.play([
      { mood: 'silence' },
      { cam: { x: 560, y: 520, viewH: 520 } },
      { narrate: 'Maren pushed off with one long stroke of the sculling oar, and the pool took them: black water, dead quiet under the roar of the filling flume, the lantern-strings of Dellhollow a hundred feet up like somebody else’s stars.' },
      { wait: 1.0 },
      { run: () => {                                            // everyone aboard: the boat carries the blocking
          if (vesper) vesper.hidden = true;
          if (lake) lake.hidden = true;
          maren.hidden = true; mochi.hidden = true; odessa.hidden = true;
          boat.x = 540; boat.y = 590; boat.dir = 'right';
        } },
      { narrate: 'And then the water to starboard was not water.' },
      { run: () => {                                            // the Tenant rises alongside — the keyed head, one slow pass
          tenant.hidden = false; tenant.scene = 'lockfive';
          tenant.x = 380; tenant.y = 575; tenant.dir = 'right';
          Net.send({ type: 'buzz', ms: 150 });
        } },
      { move: { ent: tenant, x: 700, y: 585, speed: 42 } },
      { say: ['system', '(She has risen. Not at them — beside them: a wall of moss-and-bronze sliding past at arm’s reach, old scars like map-lines, and the one pale eye, huge and calm, level with the gunwale. Watching.)'] },
      { say: ['maren', '(whisper) Oars in. Weight low. Nobody row — we’re guests.'] },
      { say: ['lake', '(The lighter is warm through my coat, and the eye finds it — the one small kept fire in all this dark — and rests there. The way old women look at other people’s grandchildren.)'] },
      { say: ['vesper:thinking', '(The eye goes over each of us in turn, unhurried, like a harbormistress reading papers. …Approved. Apparently. Filed under: the river has opinions, and today we had one.)'] },
      { narrate: 'For the length of three boats, the oldest thing in the river looked at them, and they let themselves be looked at. Then — unhurried, immense, deciding — she sank away under the black, back toward her sealed door and everything she was keeping behind it.' },
      { run: () => { tenant.hidden = true; } },
      { say: ['maren', '(whisper) …Told you. Manners.'] },
      { wait: 1.0 },
      { narrate: 'Then the flume took them.' },
      { run: () => { boat.hidden = true; } },
      { cam: { x: 940, y: 260, viewH: 480 } },
      { shake: 5 },
      { run: () => { Net.send({ type: 'buzz', ms: 400 }); Particles.burst(30, () => ({ kind: 'sparkle', x: 920 + (Math.random() - 0.5) * 200, y: 260 + (Math.random() - 0.5) * 120, vy: 20, life: 0.6 })); } },
      { say: ['maren:determined', 'BOW LEFT! Left, left— GOOD. First drop in three— two— HANG ON—'] },
      { shake: 6 }, { flash: 0.3 },
      { say: ['system', '(The bottom falls out of the world. The prow lantern draws one gold line down a mile of roaring black.)'] },
      { say: ['maren:happy', 'Second drop’s a dog-leg — fend RIGHT— Da always called it three lengths, it’s TWO now, the wall’s slumped — FEND—'] },
      { shake: 5 },
      { say: ['system', '(A wave the temperature of January comes over the bow. Vesper shields the notebook with her entire body. Priorities.)'] },
      { say: ['lake', '(Light: held. Cat: yowling. Pilot: laughing. Grandmother, the round has gotten strange — and I am sorry to report I’m having the time of my life.)'] },
      { shake: 6 },
      { say: ['maren:happy', 'LAST GATE! It’s open— it was never even shut proper— she OILED it. Ma, you absolute— SHE OILED THE TAIL-GATE—'] },
      { flash: 0.5 },
      { narrate: 'And then: sky. Stars, actual stars, wheeling to a stop overhead. The flume spat them long and flat across the tailwater pool below the last lock, and the roar fell away behind them like a door closing kindly.' },
      { wait: 1.2 },
      { mood: 'resolve' },
      { say: ['system', '(Silence. Steam off the water. Far above, very faint, the lantern-strings of Dellhollow. Mochi emerges from the satchel and begins, immediately and furiously, to wash.)'] },
      { say: ['maren:awed', '…Under four minutes. Da’s best was six.'] },
      { say: ['maren', '(quiet) Beat your time, Da. You’d have hated that. …You’d have loved that.'] },
      { fadeTo: 1 }, { wait: 1.2 },
      { run: () => { F.flumeDone = true; this.playLanding(window.players); } },
    ]);
  },

  // BEAT 8 — the landing: the bag, the chart, the boat (chained from Beat 7)
  playLanding(players) {
    const F = this.flags;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const { maren, odessa, boat, mochi } = this.npcs;
    Cutscene.play([
      { mood: 'resolve' },
      { run: () => {                                            // place: boat moored; party ashore; odessa at the stair foot
          Field.setSceneState('landing', 'dawn');
          FX.desatTarget = 0;
          boat.hidden = false; boat.scene = 'landing'; boat.x = 560; boat.y = 560; boat.dir = 'left';
          if (vesper) { vesper.hidden = false; vesper.scene = 'landing'; vesper.x = 700; vesper.y = 520; vesper.dir = 'right'; }
          if (lake) { lake.hidden = false; lake.scene = 'landing'; lake.x = 760; lake.y = 545; lake.dir = 'right'; }
          maren.hidden = false; maren.scene = 'landing'; maren.x = 650; maren.y = 555; maren.dir = 'right';
          mochi.hidden = false; mochi.follow = null; mochi.scene = 'landing'; mochi.x = 620; mochi.y = 585; mochi.dir = 'right';
          odessa.hidden = false; odessa.scene = 'landing'; odessa.x = 1010; odessa.y = 430; odessa.dir = 'left';
          Field.enter('landing');
          Field.cam.x = 700; Field.cam.y = 480;
        } },
      { fadeTo: 0 },
      { cam: { x: 700, y: 480, viewH: 620 } },
      { narrate: 'They warped the boat in to the old stone landing under the cliffs, and bailed, and wrung, and were loudly alive at one another, until the sky went the color of pearl.' },
      { wait: 0.6 },
      { narrate: 'Odessa was on the landing before the sun was. Of course she was. She had her lantern, a rope’s-end coiled over one shoulder — and a bag.' },
      { say: ['maren', '…Ma. That’s my bag.'] },
      { say: ['odessa:grave', 'Packed a week ago. You were going north the moment that eel gave you an excuse — I’ve watched it coming the way I watch weather come. A harbormistress who can’t read her own harbor should hand in the whistle.'] },
      { say: ['maren', 'A WEEK? You packed it a week ago and you still said no! Nine times you said no!'] },
      { say: ['odessa', 'Ten. And I’d say all ten again. The no was what I owed my own heart. The bag is what I owed yours.'] },
      { wait: 1.2 },
      { say: ['odessa', 'The boat’s yours — it was always going to be yours. I only kept the tar on while it waited for you to be ready. Fenders are new-roped. Bread in the bow locker, and salt-fish enough to make you sick of salt-fish, which is a harbor blessing. Take it.'] },
      { toast: { text: '✦ The party gains the boat — tar-dark, clinker-built, river-worthy', color: '#3fa7c9' } },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi walks the gunwale from stem to stern, inspecting. The boat appears to have passed. Nobody points out to Mochi what he was doing in a satchel an hour ago.)'] },
      { wait: 0.8 },
      { say: ['odessa:grave', 'Mapmaker. A word.'] },
      { run: () => {                                            // aside: odessa + vesper apart, near the stair
          if (vesper) { vesper.x = 950; vesper.y = 450; vesper.dir = 'right'; }
          odessa.x = 1020; odessa.y = 440; odessa.dir = 'left';
        } },
      { cam: { x: 960, y: 440, viewH: 420 } },
      { say: ['system', '(From inside her coat she takes an oilskin tube, worn glossy at the cap from years of handling. She does not hand it over so much as set it in Vesper’s hands and keep her own on it a moment longer.)'] },
      { say: ['vesper:thinking', '(The drawer. The one bright keyhole in a worn house. She went home in the dark, then, before the portage stair — and stood in front of eleven years, and turned the key.)'] },
      { say: ['odessa', 'His chart. The north river — every reach and shoal of it, tailwater to the grey marshes. He drew it from memory, the night before. It’s wrong.'] },
      { say: ['odessa:warm', 'She’ll want to fix it. Don’t let her do that alone.'] },
      { wait: 1.0 },
      { say: ['vesper', '…I’ve been correcting a wrong map by myself for eleven years, harbormistress. I don’t recommend it to anyone.'] },
      { say: ['vesper:determined', 'She won’t be alone.'] },
      { say: ['odessa:grave', 'Then that’s the whole of my asking.'] },
      { camRelease: true },
      { cam: { x: 650, y: 500, viewH: 560 } },
      { say: ['maren:determined', 'Ma — I’ll send word. Every town with a fish-queue between here and wherever, I’ll send—'] },
      { say: ['odessa', 'You’ll send charts. Word is air. A chart is a daughter’s hand on paper. I’ll have the charts.'] },
      { say: ['system', '(There is an embrace. It is brief, and it is total, and the harbormistress of Dellhollow does not care who is watching — which is how everyone watching knows exactly what it costs.)'] },
      { say: ['maren:happy', '(aboard, scrubbing her face with her sleeve, absolutely not crying) Right! Stations! Flame people amidships. Cat on the— cat wherever the cat decides. I’m not fighting the cat.'] },
      { toast: { text: '✦  Maren joined the party  ✦', color: '#3fa7c9' } },
      { say: ['lake', '(North, then. By water. The lighter warm against my chest, the old road keeping pace somewhere up on the rim. Grandmother — the round’s gotten strange. But I swear it’s still the round.)'] },
      { say: ['vesper:thinking', '(New page. “Party of three, one boat, one cat. One wrong chart to put right — and a hole in my own sheet: filed, patient, waiting for its rise.” …North.)'] },
      { banner: { title: '✦ North on the river ✦', sub: 'the flume behind them, the grey marshes ahead', dur: 6 } },
      { run: () => { F.marenJoined = true; } },                 // maren.follow = 'party' from Ch3 onward; here the boat carries the blocking
      { narrate: 'The current took the little boat the moment it felt her — north, quick and cold, down the long water her father had drawn wrong, and her mother had let her go and fix.' },
      { narrate: 'On the landing, the harbormistress of Dellhollow stood with her lantern until the boat was a speck, and then stood a while longer. Then she took up her rope and began the long climb home — where a town, a river, and one enormous tenant were waiting, politely, for spring.' },
      { mood: 'silence' },
      { run: () => { F.ended = true; AudioSys.finale(); Net.send({ type: 'end' }); } },
    ]);
  },

  /* ================= dev checkpoints (via the C checkpoint menu) ================= */
  CHECKPOINT_NAMES: ['', 'Ch2: the descent', 'Ch2: the valley from above',
    'Ch2: Dellhollow — the stair-street',
    'Ch2: Lock Five — the Tenant', 'Ch2: supper at the keepers’ cottage',
    'Ch2: night — the flume winches', 'Ch2: the landing — Maren joins'],
  applyCheckpoint(n) {
    this.build();
    const F = this.flags;
    // clear any running story UI
    Dialog.lines = null;
    Cutscene.active = false; Cutscene.steps = null; Cutscene.holdJob = null; Cutscene.waitFn = null; Cutscene.moveJob = null;
    Camera.target = null; FX.letterboxTarget = 0; FX.fadeTarget = 0; FX.desatTarget = 0;
    // ensure both keepers exist (keyboard-claimed if needed)
    if (!window.players.find(p => p && p.role === 'vesper')) {
      const slot = window.players.findIndex(p => p === null);
      if (slot !== -1) window.players[slot] = makePlayer('vesper', 'kb1', true);
    }
    if (!window.players.find(p => p && p.role === 'lake')) {
      const slot = window.players.findIndex(p => p === null);
      if (slot !== -1) window.players[slot] = makePlayer('lake', 'kb2', true);
    }
    const j = window.players.find(p => p && p.role === 'vesper');
    const c = window.players.find(p => p && p.role === 'lake');
    const N = this.npcs;
    const place = (e, scene, x, y, dir) => { e.scene = scene; e.x = x; e.y = y; if (dir) e.dir = dir; };
    // base state
    this.resetFlags();
    this.phase = 'together';
    this._vistaSeen = false;
    j.parked = false; j.hidden = false; c.parked = false; c.hidden = false;

    if (n === 1) {
      // the descent top — playDescent fires
      place(j, 'descent', 140, 150, 'down'); place(c, 'descent', 200, 130, 'down');
      place(N.mochi, 'descent', 250, 180, 'down');
      AudioSys.setMood('forestB');
    }
    if (n === 2) {
      // the rim — replays the valley cut, then the descent continues from the trees
      F.descentIntro = true;
      place(j, 'descent', 650, 140, 'down'); place(c, 'descent', 700, 160, 'down');
      place(N.mochi, 'descent', 620, 190, 'down');
      AudioSys.setMood('forestB');
      Field.enter('descent'); Field.cam.x = j.x; Field.cam.y = j.y;
      this.setPhase('together');
      Toasts.add('⚑ checkpoint — ' + this.CHECKPOINT_NAMES[n], '#8fb0c9');
      Cutscene.play([...this.playValley(j, c), { camRelease: true },
        { run: () => { N.mochi.follow = 'party'; } }]);
      return;
    }
    if (n === 3) {
      // the stairs top, under the arch — playArrival fires on the stair-street
      F.descentIntro = true; F.chartDone = true; F.strangerSeen = true;
      this._vistaSeen = true;
      place(j, 'stairs', 800, 150, 'down'); place(c, 'stairs', 842, 160, 'down');
      place(N.mochi, 'stairs', 770, 190, 'down');
      AudioSys.setMood('dellhollow');
    }
    if (n >= 4) {
      F.descentIntro = true; F.chartDone = true; F.strangerSeen = true;
      this._vistaSeen = true;
      F.arrived = true; F.talked = { hobb: true, pell: true };
      F.hobbTalk = 1; F.pellTalk = 1;
      F.jamDone = true; F.marenDone = true;
      N.maren.hidden = false;
    }
    if (n === 4) {
      // the lockfive stair foot — playLockFive fires (Maren walks point)
      place(j, 'lockfive', 1230, 240, 'down'); place(c, 'lockfive', 1264, 255, 'down');
      place(N.maren, 'lockfive', 1180, 330, 'down');
      place(N.mochi, 'lockfive', 1230, 300, 'down');
      AudioSys.setMood('silence');
    }
    if (n === 5) {
      // dusk in the keepers' cottage — the free-roam breath, then playSupper2
      // fires via the 8s dwell (the props are explorable first — that is the point)
      F.lockSeen = true; F.planMade = true; F.supperCalled = true;
      place(N.odessa, 'cottage', 520, 445, 'right');
      place(N.maren, 'cottage', 750, 600, 'left');
      place(N.mochi, 'cottage', 460, 640, 'up');
      place(j, 'cottage', 750, 620, 'down'); place(c, 'cottage', 820, 580, 'down');
      AudioSys.setMood('dellhollowNight');
    }
    if (n >= 6) {
      F.lockSeen = true; F.planMade = true; F.supperCalled = true; F.supperDone = true;
      F.nightFallen = true; F.dockDone = true;
      Field.setSceneState('dellhollow', 'night');
      Field.setSceneState('stairs', 'night');
      Field.setSceneState('lockfive', 'night');
      Field.scenes.dellhollow.lamps.forEach(l => { l.lit = true; });
      Field.scenes.stairs.lamps.forEach(l => { l.lit = true; });
      FX.desatTarget = 0.35;
      N.odessa.hidden = true; N.hobb.hidden = true;
      N.sorrel.hidden = true; N.creel.hidden = true; N.nib.hidden = true;
    }
    if (n === 6) {
      // midnight in Lock Five — playWinches fires
      place(j, 'lockfive', 1230, 240, 'down'); place(c, 'lockfive', 1264, 255, 'down');
      place(N.maren, 'lockfive', 760, 640, 'up');
      place(N.mochi, 'lockfive', 700, 680, 'up');
      AudioSys.setMood('silence');
    }
    if (n === 7) {
      // the tailwater landing — playLanding plays the ending
      F.boatDown = true; F.gateHalf = true; F.gatesOpen = true; F.flumeDone = true;
      FX.desatTarget = 0;
      place(j, 'landing', 700, 520, 'right'); place(c, 'landing', 760, 545, 'right');
      Field.enter('landing');
      Field.cam.x = 700; Field.cam.y = 480;
      this.setPhase('together');
      AudioSys.setMood('resolve');
      Toasts.add('⚑ checkpoint — ' + this.CHECKPOINT_NAMES[n], '#8fb0c9');
      this.playLanding(window.players);
      return;
    }
    Field.enter(j.scene);
    Field.cam.x = j.x; Field.cam.y = j.y;
    this.setPhase('together');
    Toasts.add('⚑ checkpoint — ' + this.CHECKPOINT_NAMES[n], '#8fb0c9');
  },
};
