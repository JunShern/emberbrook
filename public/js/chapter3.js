'use strict';
/* ============================================================
   CHAPTER THREE — "The Lanternstead"  (painted scene edition)

   Beat 1 — the grey road: the first lamp, lamp to lamp.
   Beat 2 — the Stranger glimpse: a pale-blue lantern, a bow.
   Beat 3 — dusk at the Lanternstead: Friar Tally, the well.
   Beat 4 — night: the first moth swarm, the great-lantern.
   Beat 5 — morning: the grey post-crow, Rowan's letter.
   Beat 6 — the wall-map, Tally joins, the road to Harrowdel.
   ============================================================ */

const Chapter3 = {
  built: false,
  phase: 'together',
  flags: {
    roadIntro: false, roadLamps: 0, strangerSeen: false,
    arrived: false, wellDone: false, supperDone: false,
    swarmActive: false, swarmDone: false, hooded: false,
    letterRead: false, mapSeen: false, tallyJoined: false,
    ended: false, endT: 0,
    tallyTalk: 0,
  },
  npcs: {}, entities: [],

  activeRoles() { return ['vesper', 'lake']; },
  setPhase(p) {
    this.phase = p;
    Net.send({ type: 'phase', act: p });
  },

  /* ================= SCENES ================= */
  buildScenes() {
    const F = this.flags;
    const S = {
      road: {
        states: { gray: 'assets/scenes/road/main.png' }, state: 'gray',
        maskSrc: 'assets/scenes/road/mask.png',
        viewH: 700, charH: 120, speed: 190, mothAmbience: true,
        tints: { gray: '#96a091' },                    // grey-green, colder than the gate scene
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        lamps: [                                       // three dead Order road-lamps, relightable (as painted)
          { x: 400, y: 390, lit: false, id: 'rlamp1', base: [400, 555] },   // south stretch
          { x: 982, y: 88, lit: false, id: 'rlamp2', base: [982, 248] },    // mid rise
          { x: 1232, y: 28, lit: false, id: 'rlamp3', base: [1230, 188] },  // near the north bend
        ],
        exits: [
          { zone: { x: 0, y: 700, w: 450, h: 68 }, to: null,               // south — back to the gate
            enabled: () => false,
            deniedLine: ['lake', 'Back through the Gate? Not with the spark this side of it. The rounds only go one way now.'] },
          // north mouth, nudged east so rlamp3's base stays outside the zone
          { zone: { x: 1254, y: 60, w: 90, h: 230 }, to: 'lanternstead', spawn: [265, 635, 'up'],
            enabled: () => Chapter3.flags.strangerSeen,
            deniedLine: ['lake', 'That stretch ahead is solid moths. Light the lamps first — nobody walks the dark part of a round.'] },
        ],
      },
      lanternstead: {
        // one painting; the states drive tint/FX/logic (night = desat + mood,
        // the lit great-lantern = engine lamp-glow at the lantern head)
        states: {
          dusk:    'assets/scenes/lanternstead/main.png',
          night:   'assets/scenes/lanternstead/main.png',
          lantern: 'assets/scenes/lanternstead/main.png',
          morning: 'assets/scenes/lanternstead/main.png',
        }, state: 'dusk',
        maskSrc: 'assets/scenes/lanternstead/mask.png',
        viewH: 720, charH: 122, speed: 190, mothAmbience: true,
        tints: { dusk: '#c9a184', night: '#5d6377', lantern: '#e0b071', morning: '#aebdc9' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        lamps: [{ x: 900, y: 120, lit: false }],       // the great-lantern head (no id: not hand-lightable)
        exits: [
          { zone: { x: 180, y: 700, w: 170, h: 68 }, to: 'road', spawn: [1180, 210, 'left'],
            enabled: () => Chapter3.flags.arrived && !Chapter3.flags.swarmActive,
            deniedLine: ['tally', 'After dark? Flamebearer, rule one! The road will keep till morning — it has kept three hundred years.'] },
          { zone: { x: 782, y: 532, w: 82, h: 64 }, to: 'lanternstead-int', spawn: [672, 655, 'up'] },  // tower door step
        ],
      },
      'lanternstead-int': {
        states: { evening: 'assets/scenes/lanternstead-int/main.png',
                  morning: 'assets/scenes/lanternstead-int/main.png' }, state: 'evening',
        maskSrc: 'assets/scenes/lanternstead-int/mask.png',
        viewH: 725, charH: 205, speed: 280,
        tints: { evening: '#e8b184', morning: '#c9c2ae' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        exits: [{ zone: { x: 612, y: 620, w: 128, h: 148 }, to: 'lanternstead', spawn: [822, 570, 'down'] }],
      },
    };
    // merge with whatever is already registered so Chapter One's scenes
    // (and its checkpoints) stay reachable after the handoff
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
    N('tally', 'tally', 'lanternstead', 1080, 560, 'down', 118).hidden = true;
    const crow = N('postcrow', 'postcrow', 'lanternstead', 585, 395, 'down', 55);
    crow.hidden = true;
    const stranger = N('stranger', 'stranger', 'road', 1150, 155, 'down', 120);
    stranger.hidden = true;
    const mochi = N('mochi', 'mochi', 'road', 215, 660, 'right', 48);
    mochi.follow = 'party';
    // Maren — aboard since Dellhollow; walks with the party (Ch2 seam, §h)
    const maren = N('maren', 'maren', 'road', 175, 690, 'right', 112);
    maren.follow = 'party';
  },

  // hard reset of story state — used by begin() and the checkpoints
  resetFlags() {
    Object.assign(this.flags, {
      roadIntro: false, roadLamps: 0, strangerSeen: false,
      arrived: false, wellDone: false, supperDone: false,
      swarmActive: false, swarmDone: false, hooded: false,
      letterRead: false, mapSeen: false, tallyJoined: false,
      ended: false, endT: 0, tallyTalk: 0,
    });
    this._letterT = 0;
    const sc = Field.scenes;
    if (sc.road) sc.road.lamps.forEach(l => { l.lit = false; });
    if (sc.lanternstead) sc.lanternstead.lamps.forEach(l => { l.lit = false; });
    Field.setSceneState('road', 'gray');
    Field.setSceneState('lanternstead', 'dusk');
    Field.setSceneState('lanternstead-int', 'evening');
    const N = this.npcs;
    N.tally.hidden = true; N.tally.follow = null;
    Object.assign(N.tally, { scene: 'lanternstead', x: 1080, y: 560, dir: 'down' });
    N.postcrow.hidden = true; N.postcrow.char = 'postcrow';
    Object.assign(N.postcrow, { scene: 'lanternstead', x: 585, y: 395, dir: 'down' });
    N.stranger.hidden = true;
    Object.assign(N.stranger, { scene: 'road', x: 1150, y: 155, dir: 'down' });
    N.mochi.hidden = false; N.mochi.follow = 'party';
    Object.assign(N.mochi, { scene: 'road', x: 215, y: 660, dir: 'right' });
    N.maren.hidden = false; N.maren.follow = 'party';
    Object.assign(N.maren, { scene: 'road', x: 175, y: 690, dir: 'right' });
  },

  // chapter start — the cold open. Both players onto the grey road.
  begin(players) {
    this.build();
    this.resetFlags();
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const place = (e, scene, x, y, dir) => { if (!e) return; e.scene = scene; e.x = x; e.y = y; e.dir = dir; e.hidden = false; e.parked = false; };
    place(vesper, 'road', 150, 640, 'right');
    place(lake, 'road', 235, 665, 'right');
    FX.desatTarget = 0;
    Field.enter('road');
    Field.cam.x = 220; Field.cam.y = 640;
    this.setPhase('together');
    AudioSys.setMood('forestB');
  },

  spawnFor(role) {
    if (!this.flags.arrived)
      return role === 'vesper'
        ? { scene: 'road', x: 150, y: 640, dir: 'right' }
        : { scene: 'road', x: 235, y: 665, dir: 'right' };
    return role === 'vesper'
      ? { scene: 'lanternstead', x: 620, y: 560, dir: 'down' }
      : { scene: 'lanternstead', x: 700, y: 570, dir: 'down' };
  },

  /* scene-keyed music (see §f of the chapter script) */
  moodFor(sceneKey) {
    const F = this.flags;
    switch (sceneKey) {
      case 'road':
        return 'forestB';                       // "old roots" — the uneasy forest
      case 'lanternstead':
        return F.swarmActive ? null : 'resolve';
      case 'lanternstead-int':
        return 'resolve';
      default:
        return null;
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

    // moth ambience dies inside the great-lantern's ring
    const ls = Field.scenes.lanternstead;
    if (ls) ls.mothAmbience = (ls.state === 'dusk' || ls.state === 'night');

    // Beat 1 — cold open on the road
    if (both && !F.roadIntro && !busy && vesper.scene === 'road' && lake.scene === 'road')
      this.playRoadOpen(vesper, lake);
    // Beat 2 — the Stranger glimpse
    if (both && F.roadIntro && F.roadLamps >= 3 && !F.strangerSeen && !busy &&
        players.some(p => p && p.scene === 'road' && p.x > 950))
      this.playStranger(players);
    // Beat 3 — arrival at the Lanternstead
    if (both && F.strangerSeen && !F.arrived && !busy &&
        players.some(p => p && p.scene === 'lanternstead'))
      this.playArrival(players);
    // Beat 3½ — supper transition (glue): going inside with the water drawn
    if (both && F.wellDone && !F.supperDone && !busy &&
        players.some(p => p && p.scene === 'lanternstead-int'))
      this.playSupper(players);
    // Beat 4 — night swarm fires as soon as supper is done
    // (!Cutscene.active re-checked live: playSupper latches supperDone in this same
    // tick, and the stale `busy` snapshot must not let the swarm clobber the supper)
    if (both && F.supperDone && !F.swarmDone && !F.swarmActive && !busy && !Cutscene.active &&
        players.some(p => p && p.scene === 'lanternstead'))
      this.playSwarm(players);
    // Beat 5 — morning: the letter, after a short free-roam breath
    if (both && F.swarmDone && !F.letterRead && !busy &&
        players.some(p => p && p.scene === 'lanternstead')) {
      this._letterT = (this._letterT || 0) + dt;
      if (this._letterT > 2.0) this.playLetter(players);
    }

    // followers — Mochi always; Tally once he joins the party
    if (!Cutscene.active) this.updateFollowers(dt, players);

    if (F.ended) F.endT += dt;
  },

  updateFollowers(dt, players) {
    const ps = players.filter(p => p && !p.hidden && !p.parked);
    if (!ps.length) return;
    const jobs = [
      { e: this.npcs.mochi, target: ps[0], offs: [[-40, 8], [40, 8], [0, -45], [0, 45]], near: 60, far: 85, snap: 240, spd: 200 },
      { e: this.npcs.tally, target: ps[ps.length - 1], offs: [[-62, 16], [62, 16], [0, -64], [0, 64]], near: 80, far: 112, snap: 280, spd: 190 },
      // Maren trails the lead player (Tally's job, mirrored offsets — §h seam)
      { e: this.npcs.maren, target: ps[0], offs: [[58, 20], [-58, 20], [0, -60], [0, 60]], near: 78, far: 108, snap: 280, spd: 195 },
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
    if (!F.roadIntro) return '';
    if (!F.arrived) {
      if (F.roadLamps < 3) {
        const hints = [];
        const rl = Field.scenes.road.lamps;
        if (rl[0] && !rl[0].lit) hints.push('one on the south stretch');
        if (rl[1] && !rl[1].lit) hints.push('one on the rise');
        if (rl[2] && !rl[2].lit) hints.push('one by the north bend');
        return `The grey road — light the road-lamps (${F.roadLamps}/3)${hints.length ? ' · ' + hints.join(' · ') : ''}`;
      }
      if (!F.strangerSeen) return 'Make the Lanternstead by dusk — north, lamp to lamp';
      return 'The Lanternstead — someone is singing';
    }
    if (!F.wellDone) return 'Help Tally draw water — the well takes two';
    if (!F.supperDone) return 'Supper at the Lanternstead — go inside';
    if (!F.swarmDone) return 'Moths! — the great-lantern: wick and winch, together';
    if (!F.letterRead) return 'Morning — see what the crow brought';
    return 'The round room — ask Tally about the road ahead';
  },

  /* markers — hooks read by main.js drawMarkers */
  lampHintActive() {
    return this.flags.roadIntro && this.flags.roadLamps < 3;
  },
  storyMarker() {
    const F = this.flags;
    if (F.letterRead && !F.tallyJoined && Field.currentKey === 'lanternstead-int') {
      const t = this.npcs.tally;
      if (!t.hidden && t.scene === 'lanternstead-int') return { x: t.x, y: t.y - t.h - 18 };
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
      if (n.key === 'postcrow' || n.key === 'stranger') continue;
      if (n.key === 'tally' && n.follow) continue;    // once he walks with you, the map said it all
      if (n.key === 'maren' && n.follow) continue;    // walking with the party; her chapter was the last one
      consider(n.x, n.y, { kind: 'npc', key: n.key, ent: n });
    }
    if (p.role === 'lake') {
      const s = Field.scenes[p.scene];
      for (const l of (s.lamps || [])) if (!l.lit && l.id) consider(l.base[0], l.base[1], { kind: 'lamp', lamp: l });
    }
    if (p.scene === 'road') {
      consider(245, 590, { kind: 'waymarkA', at: [140, 480] }, 80);
      consider(1150, 300, { kind: 'waymarkB', at: [1210, 200] }, 80);
      consider(620, 470, { kind: 'darkstretch', at: [620, 400] }, 75);
    }
    if (p.scene === 'lanternstead') {
      consider(348, 470, { kind: 'well', at: [348, 340] }, 80);
      consider(900, 570, { kind: 'greatlantern', at: [900, 330] }, 70);
      consider(340, 276, { kind: 'washing', at: [330, 120] }, 110);
      consider(640, 290, { kind: 'flags', at: [640, 200] }, 100);
      consider(300, 655, { kind: 'veg', at: [220, 590] }, 90);
    }
    if (p.scene === 'lanternstead-int') {
      consider(650, 330, { kind: 'books', at: [650, 200] }, 90);
      consider(470, 420, { kind: 'hearth2', at: [430, 250] }, 85);
      consider(930, 430, { kind: 'wallmap', at: [930, 250] }, 90);
      consider(510, 540, { kind: 'bed', at: [400, 460] }, 85);
      consider(990, 460, { kind: 'bed', at: [1040, 390] }, 85);
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
      if (t.kind === 'lamp') return 'A — light the lamp';
      if (t.kind === 'npc') return 'A — talk to ' + SPEAKERS[t.key].name;
      if (t.kind === 'well') return this.flags.arrived && !this.flags.wellDone ? 'A — the well' : 'A — look';
      if (t.kind === 'wallmap') return 'A — the wall-map';
      return 'A — look';
    }
    return '';
  },

  interact(p) {
    const F = this.flags;
    const t = this.nearestThing(p);
    if (!t) return;
    const sys = (text) => Dialog.start([{ who: 'system', text }]);
    if (t.kind === 'lamp') return this.lightLamp(t.lamp, p);
    if (t.kind === 'npc') return this.talkTo(t.key, t.ent, p);
    if (t.kind === 'waymarkA') return sys(p.role === 'vesper'
      ? 'A waymarker, swallowed to the shoulders. The carved hand points north; the mile-count is moss. Vesper records it as “one, presumed.”'
      : 'The stone hand points up the road. Someone cut a small sun above it — or a lamp. On this road, likely a lamp.');
    if (t.kind === 'waymarkB') return sys('This one leans like it stopped believing in the road. The carving reads “LANTERNSTEAD —” and then three centuries of weather.');
    if (t.kind === 'darkstretch') return sys('The moths here drift without hurry and without direction — the way lost things drift, waiting to be found.');
    if (t.kind === 'well') {
      if (F.arrived && !F.wellDone) return this.playWell(window.players);
      return sys('The well. Somewhere down there, Brother Frog continues his ministry.');
    }
    if (t.kind === 'greatlantern') {
      const s = Field.scenes.lanternstead;
      return sys(s.state === 'lantern' || s.state === 'morning'
        ? 'The great-lantern, burning. The courtyard has a heartbeat now. The moths keep to the far dark, like a tide around a rock.'
        : 'The great-lantern crowns the tower: glass the size of a room, brass polished bright — around a wick that has never in living memory been lit. It is the cleanest dead thing on the whole road.');
    }
    if (t.kind === 'washing') return sys('Three shirts patched with liturgical neatness, and one enormous nightcap. The washing line of a man keeping civilization alive by hand.');
    if (t.kind === 'flags') return sys('Small faded flags, each block-printed with a lamp. Order prayer flags — the wind says the rite for you when you are too busy walking. These have been praying nonstop for three hundred years.');
    if (t.kind === 'veg') return sys('Cabbages in rows straight enough to survey by. A stick label reads “TURNIPS (unconvinced)”.');
    if (t.kind === 'books') return sys('Thirty-nine volumes, hand-copied, shelved in liturgical order and re-shelved, by the wear on them, several thousand times. Volume One falls open to the creed: “Light does not die—”. The rest of the page is worn away by a thumb.');
    if (t.kind === 'hearth2') return sys('The hearth is laid, swept, ready — the fire in it small and careful, a cook’s fire. Above the mantel hangs an empty bracket, polished, exactly the size of a lamplighter’s lighter. Waiting.');
    if (t.kind === 'bed') return sys('One bed, made with hospital corners — the walkers’ bed, kept ready three hundred years. One hammock, strung by the window: Tally’s. The arithmetic of a man who never stopped expecting company.');
    if (t.kind === 'wallmap') {
      if (F.letterRead && !F.tallyJoined) return this.playWallMap(window.players);
      return sys('The Order’s wall-map of the circuit: a ring of valleys around the deep wood, one road joining them, a lamp sigil at every name — and under every name, years of tiny meticulous tally-marks. You don’t yet know what they count.');
    }
  },

  lightLamp(lamp, p) {
    const F = this.flags;
    lamp.lit = true;
    F.roadLamps++;
    AudioSys.lampOn();
    Net.send({ type: 'buzz', ms: 60 });
    Particles.burst(8, () => ({ kind: 'sparkle', x: lamp.x + (Math.random() - 0.5) * 16, y: lamp.y + (Math.random() - 0.5) * 12, vy: -8, life: 0.8 }));
    if (F.roadLamps === 1) Dialog.start([
      { who: 'lake', text: '(One. The door swings like it was oiled last week. Order brass doesn’t rust — grandmother said they built for a longer war than weather.)' },
      { who: 'vesper', text: 'The moths just… made room. Noted: they don’t cross the lamplight.' },
      { who: 'lake', text: 'A lit lamp is a shut door. Grandmother’s phrase. I never asked who it was shut against.' },
    ]);
    if (F.roadLamps === 2) Dialog.start([
      { who: 'lake', text: '(Two. A mile-lamp. The walkers measured the road in light — one lamp, one hour, one prayer. I only know the saying: count lamps, not miles. Miles don’t care about you.)' },
    ]);
    if (F.roadLamps === 3) Dialog.start([
      { who: 'lake', text: '(Three. Lit, the road looks kept. Somebody should tell the moths this street’s taken. …I suppose I just did.)' },
    ]);
  },

  /* ================= dialogue ================= */
  talkTo(key, ent, p) {
    const F = this.flags;
    const dx = p.x - ent.x, dy = p.y - ent.y;
    if (key !== 'mochi') ent.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    const D = (lines, onFinish) => Dialog.start(lines.map(l => ({ who: l[0], text: l[1] })), onFinish);

    if (key === 'mochi') {
      if (p.scene === 'lanternstead' || p.scene === 'lanternstead-int')
        return D([['system', '(Mochi has inspected the entire station and is now sitting on the rite-books. Tally appears to regard this as a liturgically significant endorsement.)']]);
      return D([['mochi', 'Mrrp.']]);
    }

    if (key === 'tally') {
      if (F.letterRead && !F.tallyJoined && p.scene === 'lanternstead-int')
        return this.playWallMap(window.players);
      if (F.letterRead && !F.tallyJoined)
        return D([['tally:earnest', 'Before you walk, you should see what road you’re on. The wall-map — in the round room. I’ll meet you at it.']]);
      // evening villager-style branches: 1, 2, then the last on loop
      const n = F.tallyTalk++;
      if (n === 0) return D([
        ['tally:happy', 'Ask me anything! I know everything and have seen none of it. I am the world’s leading authority on things I have never watched happen.'],
        ['lake', 'The great-lantern, then. What was it for?'],
        ['tally:earnest', 'The waystations ring the deep wood — one great-lantern each. Lit, they warded the road for the walkers, and each answered the next: light in sight of light, all the way around the circuit. The rite calls it the necklace.'],
        ['tally:happy', 'I also call it the necklace. It’s a good rite.'],
        ['vesper', 'And it’s been dark since—'],
        ['tally', 'Since a hundred and nine years before my order bought its last new kettle. We were never a hasty organization.'],
      ]);
      if (n === 1) return D([
        ['tally:earnest', 'Friars keep; lighters walk. I’m the fourteenth keeper of this station — and the first to keep it alone.'],
        ['tally', 'My teacher taught me the rounds the way his teacher taught him: for the day the walking twos came back. He died believing they would.'],
        ['tally:happy', 'I feed his crows. And look — he was right.'],
      ]);
      return D([
        ['tally:happy', 'Eat! Doctrine can wait an hour. Doctrine has waited three hundred years — it’s very good at it.'],
      ]);
    }
  },

  /* ================= cutscenes ================= */

  // BEAT 1 — cold open: the grey road
  playRoadOpen(vesper, lake) {
    const F = this.flags;
    F.roadIntro = true;
    const mochi = this.npcs.mochi;
    mochi.follow = null;
    Cutscene.play([
      { mood: 'forestB' },                                     // the deep wood, uneasy
      { banner: { title: '— CHAPTER THREE —', sub: 'The Lanternstead', dur: 5 } },
      { cam: { x: 340, y: 560, viewH: 520 } },
      { wait: 1.2 },
      { narrate: 'Two days the river ran them north, quick and law-abiding — and then it shoaled grey among the marshes and bent away east, from every road at once. They put the boat ashore at an old stone landing where mossed steps climbed to a mossed road, moored her the way Maren’s father would have wanted, and walked.' },
      { narrate: 'The road was Order stone under three hundred years of moss — built by people who measured in lamps, for a walk that stopped.' },
      { move: { ent: mochi, x: 300, y: 620, speed: 150 } },    // mochi trots ahead, tail up
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi walks exactly down the middle of the road, tail up — the only one of the three who has decided this is a procession.)'] },
      { move: { ent: vesper, x: 290, y: 600, speed: 120 } },
      { face: { ent: vesper, dir: 'right' } },
      { say: ['vesper', 'There. Dead lamp, ten o’clock, brass door and all. First lamp, partner — as promised.'] },
      { say: ['lake', 'It’s ours. I mean — it’s the same pattern as ours. Same door, same wick. This whole road belonged to the Order.'] },
      { say: ['vesper', 'Three of them between here and the rise, and the moths sit thickest exactly where the lamps aren’t. So we do this your way. Lamp to lamp.'] },
      { say: ['lake', '(A road of my own lamps. Grandmother walked me the village round a thousand times and never once said the round kept going.)'] },
      { say: ['vesper:thinking', '(New page. “The North Road. Surface: Order stone. Weather: grey, permanent. Company: one lamplighter, one cat, every moth in the world.”)'] },
      { camRelease: true },
      { run: () => { mochi.follow = 'party'; } },
    ]);
  },

  // BEAT 2 — the Stranger glimpse
  playStranger(players) {
    const F = this.flags;
    F.strangerSeen = true;                                     // (north exit opens; frozen till the scene ends)
    const stranger = this.npcs.stranger;
    Cutscene.play([
      { mood: 'silence' },
      { run: () => { stranger.hidden = false; stranger.scene = 'road'; stranger.x = 1150; stranger.y = 155; stranger.dir = 'down'; } },
      { cam: { x: 1040, y: 280, viewH: 560 } },
      { wait: 1.2 },
      { narrate: 'Far up the road, where their lamplight ran out, stood a light that was not theirs. A lantern, carried. Full to the glass. And pale, pale blue.' },
      { say: ['vesper', 'Lake.'] },
      { say: ['lake', 'I see him.'] },
      { say: ['mochi', 'Hhhhhhhh.'] },
      { say: ['system', '(A sound is coming out of Mochi that neither of them has ever heard a cat make. Low. Level. Aimed.)'] },
      { say: ['system', '(Maren — who has stared down the Tenant at arm’s length — takes one look at the far light and steps closer to the others without deciding to.)'] },
      { say: ['vesper:worried', '(Hooded. Tall. Not moving like a man who has been walking — moving like a man who has never been doing anything else.)'] },
      { say: ['lake', 'Sir! The road’s dark past the bend — you’re welcome to walk in our light—'] },
      { wait: 1.0 },
      { narrate: 'The stranger did not come closer. He looked at them — or at something they carried — for a long moment. And then he bowed: deep, and slow, and courteous, the way you bow to an altar. Not to them. To the small brass flame in Lake’s hand.' },
      { wait: 0.8 },
      { flash: 0.5 },
      { run: () => { stranger.hidden = true; Net.send({ type: 'buzz', ms: 120 }); } },
      { narrate: 'Between one blink and the next, the road was empty.' },
      { wait: 0.8 },
      { say: ['vesper', '…Gone. Gone HOW? That’s a quarter mile of open road and nothing to be behind.'] },
      { say: ['lake:worried', 'He bowed. To the lighter — I know where he was looking.'] },
      { say: ['vesper', 'People don’t bow to lighters.'] },
      { say: ['lake', 'Lamplighters do. On the high days. Grandmother bowed exactly that deep and exactly that slow, and I never saw another soul do it in my life.'] },
      { say: ['vesper:thinking', '(Entry: one walker, unmapped. Lantern: full, blue, wrong. Manner: courteous. Departure: unexplained. Filed under things I refuse to call impossible twice in one week.)'] },
      { say: ['lake', 'Mochi hissed again. Twice in his life now — both times at that silhouette. Grandmother used to say: when the cat votes, count it twice.'] },
      { say: ['vesper', 'And how does the cat vote?'] },
      { say: ['lake', 'Against.'] },
      { mood: 'forestB' },
      { camRelease: true },
    ]);
  },

  // BEAT 3 — dusk at the Lanternstead: meet Tally
  playArrival(players) {
    const F = this.flags;
    F.arrived = true;
    const tally = this.npcs.tally;
    const lake = players.find(p => p && p.role === 'lake') || players.find(Boolean);
    Cutscene.play([
      { mood: 'resolve' },
      { cam: { x: 620, y: 380, viewH: 620 } },
      { narrate: 'They smelled the Lanternstead before they saw it: woodsmoke, turned earth, and — impossibly, out here at the end of the world — laundry.' },
      { wait: 0.8 },
      { say: ['vesper', 'A tower. A well. A vegetable patch in ruler-straight rows. And… shirts.'] },
      { say: ['lake', 'Somebody LIVES here.'] },
      { say: ['tally', '…aaaand the ninth observance, the polishing of the glass, la-la-la, that the light find no dust upon arrival—'] },   // offstage, sung
      { run: () => { tally.hidden = false; tally.scene = 'lanternstead'; tally.x = 1080; tally.y = 560; } },  // rounds the tower with a basket
      { move: { ent: tally, x: 770, y: 575, speed: 120 } },
      { wait: 0.8 },                                            // Tally sees them. Basket stays, barely.
      { say: ['tally:earnest', 'Oh! Oh. Wait. Wait wait wait — I know this one.'] },
      { say: ['tally', '“WHO WALKS the dead road?” — no, sorry, it’s “who KEEPS the dead road,” and then YOU say—'] },
      { say: ['vesper', '…We walk it?'] },
      { say: ['tally', 'You’re not supposed to ANSWER! Nobody has EVER answered!'] },
      { move: { ent: tally, x: lake.x + 60, y: lake.y, speed: 150 } },
      { say: ['tally:awed', '…Flamebearer. Flamebearer, is that flame ALIVE?'] },
      { say: ['lake', 'It’s— yes? It’s my lighter. It’s warm, if you want to—'] },
      { say: ['tally:awed', 'Don’t— don’t let me touch it. There’s a correct distance. I know the correct distance. I have never once needed the correct distance.'] },
      { wait: 1.0 },
      { say: ['tally:earnest', 'Three hundred years this station has kept the Rite of the Open Door. Firewood dry. Beds aired. Great-lantern polished — I do the glass on Sundays.'] },
      { say: ['tally', 'You’re real. The office is real. I have the whole liturgy and nobody ever came.'] },
      { wait: 1.2 },
      { say: ['vesper:worried', '…How long have you been out here alone?'] },
      { say: ['tally:happy', 'Alone? Madam, I have nineteen crows, a well with opinions, and the entire Order of Lamplighters, bound in thirty-nine volumes.'] },
      { say: ['tally:earnest', 'And now — a Flamebearer and a Waykeeper. A walking two, at my door, at dusk, in the correct season. The road was never meant to be walked alone, you know. It says so on the door.'] },
      { say: ['vesper', 'Vesper. Mapmaker — not, that I’m aware, a Waykeeper.'] },
      { say: ['tally:earnest', 'You walked here off the map, madam, in front of a Flamebearer. I won’t argue doctrine with the doctrine standing in my yard.'] },
      { say: ['lake', 'Lake. Lamplighter. Emberbrook.'] },
      { say: ['tally:happy', 'Emberbrook! The Third Daughter! Founded from a carried ember, one wick, one walking— sorry. I will be doing this all evening. Tally. Friar Tally, if titles survive being the last one.'] },
      { say: ['tally', 'You’ll want supper. The rite is clear: the walkers eat first.'] },
      { say: ['vesper', 'Why does everyone on this road make feeding me a LAW?'] },
      { say: ['tally:happy', 'Because the Order wrote good laws, madam.'] },
      { camRelease: true },
    ]);
  },

  // small co-op — the well
  playWell(players) {
    const F = this.flags;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    if (!vesper || !lake) {
      Dialog.start([{ who: 'tally', text: 'The crank takes two, friend — that is not a metaphor, it is engineering.' }]);
      return;
    }
    const tally = this.npcs.tally;
    Cutscene.play([
      { move: { ent: tally, x: 455, y: 505, speed: 150 } },
      { say: ['tally:earnest', 'Supper wants water, and the well was cut by the Order — which is to say, the crank takes two. Everything here takes two. It was that kind of Order.'] },
      { run: () => {                                            // stage players at the two crank handles
          vesper.x = 305; vesper.y = 465; vesper.dir = 'up';
          lake.x = 400; lake.y = 465; lake.dir = 'up';
        } },
      { bothHold: { prompt: 'HOLD  A — haul the bucket, together', dur: 1.6 } },
      { run: () => { AudioSys.chime(); Net.send({ type: 'buzz', ms: 120 }); } },
      { say: ['system', '(The bucket arrives. It contains water, and one entirely unhurried frog.)'] },
      { say: ['vesper', 'Your well has a frog.'] },
      { say: ['tally:happy', 'That’s Brother Frog. He predates me. Back he goes.'] },
      { say: ['mochi', 'Mrrp.'] },
      { run: () => { F.wellDone = true; } },
    ]);
  },

  // BEAT 3½ — supper at the round table
  playSupper(players) {
    const F = this.flags;
    F.supperDone = true;                              // latched at cutscene start
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const tally = this.npcs.tally, mochi = this.npcs.mochi, maren = this.npcs.maren;
    Cutscene.play([
      { fadeTo: 1 },
      { wait: 0.9 },
      { run: () => {                                  // everyone to the table — including a player still in the yard
          Field.setSceneState('lanternstead-int', 'evening');
          if (vesper) { vesper.scene = 'lanternstead-int'; vesper.x = 600; vesper.y = 548; vesper.dir = 'right'; }
          if (lake) { lake.scene = 'lanternstead-int'; lake.x = 748; lake.y = 552; lake.dir = 'left'; }
          tally.scene = 'lanternstead-int'; tally.x = 676; tally.y = 508; tally.dir = 'down';
          maren.scene = 'lanternstead-int'; maren.x = 812; maren.y = 520; maren.dir = 'left';
          mochi.scene = 'lanternstead-int'; mochi.x = 618; mochi.y = 588; mochi.dir = 'right';
          Field.enter('lanternstead-int');
          Field.cam.x = 672; Field.cam.y = 520;
        } },
      { cam: { x: 672, y: 505, viewH: 580 } },
      { mood: 'resolve' },
      { fadeTo: 0 },
      { wait: 0.6 },
      { narrate: 'The round room at evening: candle-brass and cook-fire, thirty-nine books, and a big table laid — plates, spoons, and a jug of flowers that on inspection were mostly kale.' },
      { say: ['tally:happy', 'Sit! Sit. The rite is clear—'] },
      { say: ['vesper', '…the walkers eat first. Yes. I’m coming to terms with a road where every law is about dinner.'] },
      { say: ['tally:earnest', 'The good laws usually are, madam.'] },
      { say: ['system', '(Supper is bread, butter, and turnip-and-barley out of the big pot — which is called Sister Kettle; the walking kettle is her novice. The table is set for four, and has very plainly been set for four for a long time.)'] },
      { say: ['vesper', 'You lay four places. Every night?'] },
      { say: ['tally:happy', 'Every night, madam. One for the keeper, two for the walking two, and a fourth for whoever the road sends extra. The arithmetic has never once come out before. Forgive me if I keep counting you.'] },
      { say: ['maren', 'Four places. We’re five and a cat. …I’ll get the wobbly stool, I ALWAYS get the wobbly stool.'] },
      { say: ['tally', 'Alone it’s the same pot — turnips, barley, whatever the garden forgives me. The art is making Tuesday taste different from Wednesday. Wednesdays, onions. It is a whole liturgy.'] },
      { say: ['system', '(Tally ladles the top of the stew onto the fourth plate and sets it down for Mochi. The cat inspects the plate, then Tally — and settles in with the air of an official approving a shipment.)'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['tally:happy', 'High praise. The crows only ever shout.'] },
      { say: ['tally:earnest', 'Now — supper’s price. A walker pays in news; station law. Tell me one true thing about Emberbrook. Not the founding, I HAVE the founding. A small thing. The kind no book keeps.'] },
      { say: ['lake', 'Poppy — our baker. She burns her thumb on the first tray every morning, and swears every morning that tomorrow she won’t. She’s sworn it every morning of my life.'] },
      { say: ['tally:awed', '…A baker, swearing at the bread, daily, on schedule. Thirty-nine volumes on that shelf and not one of them thought that worth writing down. I shall begin the fortieth.'] },
      { wait: 0.8 },
      { say: ['vesper', '…When did either of us last sit at a table? I’m asking honestly. I can’t find the entry.'] },
      { say: ['lake', 'Two nights ago you were a stranger, and since then we’ve eaten standing up in the dark. There’s never been a table. This is the first one.'] },
      { say: ['vesper:thinking', '(Two days, one road, one cat. On paper we hardly know each other. Noted, for the file: the paper is wrong.)'] },
      { wait: 0.8 },
      { narrate: 'The candles burned down a knuckle. Outside the little window, the last of the grey went out of the sky.' },
      { say: ['system', '(Tally rises and unhooks the tiny brass bell from his belt. He rings it once — a sound the size of a teaspoon, into a hush three hundred years deep.)'] },
      { say: ['tally:earnest', 'The walker’s grace — forgive the ceremony; I have never once got past the first line with anyone but the crows. “Light on the road behind you; light on the road ahead. Eat and be kept. Walk and be expected.”'] },
      { fadeTo: 1 },
      { wait: 1.2 },
      { camRelease: true },
      { run: () => {                                  // …and out to the courtyard, after dark (the old glue, kept)
          Field.setSceneState('lanternstead', 'night');
          FX.desatTarget = 0.45;                      // one painting: night is desat + tint + mood
          if (vesper) { vesper.scene = 'lanternstead'; vesper.x = 620; vesper.y = 560; vesper.dir = 'down'; }
          if (lake) { lake.scene = 'lanternstead'; lake.x = 700; lake.y = 570; lake.dir = 'down'; }
          tally.scene = 'lanternstead'; tally.x = 770; tally.y = 575; tally.dir = 'left';
          maren.scene = 'lanternstead'; maren.x = 560; maren.y = 585; maren.dir = 'right';
          mochi.scene = 'lanternstead'; mochi.x = 650; mochi.y = 605;
          Field.enter('lanternstead');
          Field.cam.x = 660; Field.cam.y = 560;
        } },
      { fadeTo: 0 },
      { wait: 0.4 },
    ]);
  },

  // BEAT 4 — night: the first moth swarm, the great-lantern
  playSwarm(players) {
    const F = this.flags;
    F.swarmActive = true;                                       // locks the exits for the setpiece
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const tally = this.npcs.tally, maren = this.npcs.maren;
    Cutscene.play([
      { narrate: 'Supper was turnips, doctrine, and the best bread either of them had eaten since Emberbrook. Night came down on the Lanternstead like a lid.' },
      { run: () => { Field.setSceneState('lanternstead', 'night'); } },
      { mood: 'silence' },
      { wait: 1.5 },
      { say: ['system', '(Mochi’s ears go flat. He is facing the courtyard wall. He is very, very still.)'] },
      { say: ['mochi', 'Hhhhhhhh.'] },
      { say: ['tally:earnest', 'The cat. The books draw PICTURES of a cat doing that— oh. Oh no. The books SAY this. “In the dark season the strays seek the walking flame”— outside. Everyone outside, NOW.'] },
      { cam: { x: 672, y: 420, viewH: 640 } },
      { run: () => {                                            // moth storm: spiral in toward Lake
          const lx = lake ? lake.x : 672, ly = lake ? lake.y : 500;
          Particles.burst(60, () => {
            const a = Math.random() * Math.PI * 2, r = 260 + Math.random() * 260;
            const x = lx + Math.cos(a) * r, y = ly + Math.sin(a) * r * 0.6;
            return { kind: 'moth', x, y, vx: (lx - x) * 0.35, vy: (ly - y) * 0.35, life: 7, seed: Math.random() * 9 };
          });
          AudioSys.hushSting(); Net.send({ type: 'buzz', ms: 400 });
        } },
      { shake: 4 },
      { say: ['system', '(Maren has the stance of a woman with a barge-pole and no barge-pole. She puts herself between the swarm and the smallest party member, who is the cat.)'] },
      { say: ['vesper', 'Define “seek the walking flame,” Tally — QUICKLY.'] },
      { say: ['tally:earnest', 'Moths eat light, madam, and out here your partner is carrying the only lit thing in the world! It’s rule ONE — no bare flame outdoors after dark on the dead road — it’s the FIRST rule and I have never once needed to say it out loud!'] },
      { say: ['lake:worried', 'They’re coming through my coat— I can’t put it out, it doesn’t GO out—'] },
      { say: ['tally:earnest', 'Don’t put it out — OUTSHINE it! The great-lantern! A lit lamp is a shut door; a GREAT lamp is a shut GATE! Wick and winch — it takes two, it always takes two!'] },
      { say: ['tally', 'Waykeeper — the winch! Nine turns, then HOLD! Flamebearer — the wick-gate! Brass door, same as your lamps, only rather — rather LARGE—'] },
      { run: () => {                                            // stage: vesper → winch, lake → wick-gate
          if (vesper) { vesper.x = 1035; vesper.y = 575; vesper.dir = 'up'; }
          if (lake) { lake.x = 915; lake.y = 560; lake.dir = 'up'; }
          tally.x = 975; tally.y = 590; tally.dir = 'up';
          maren.x = 1090; maren.y = 615; maren.dir = 'up';
        } },
      { say: ['lake', '(Mean it. A lamp for the whole road — for every walker who never came, and the one keeper who stayed. …That one’s easy to mean.)'] },
      { bothHold: { prompt: 'HOLD  A — wick and winch, together', dur: 2.6 } },
      { flash: 0.9 }, { shake: 5 },
      { run: () => {
          Field.setSceneState('lanternstead', 'lantern');
          FX.desatTarget = 0;
          Field.scenes.lanternstead.lamps[0].lit = true;        // the great-lantern head glows
          AudioSys.rumble(); AudioSys.chime(); Net.send({ type: 'buzz', ms: 500 });
          Particles.burst(30, () => ({ kind: 'sparkle', x: 900 + (Math.random() - 0.5) * 120, y: 120 + (Math.random() - 0.5) * 70, vy: -10, life: 1.4 }));
        } },
      { narrate: 'The great-lantern of the Lanternstead took the flame like a held breath let go — three hundred years of polish and readiness, and then LIGHT: a roar of it, out across the grey road in every direction at once.' },
      { run: () => {                                            // the swarm turns: wheel once, scatter outward
          Particles.burst(40, () => {
            const a = Math.random() * Math.PI * 2;
            return { kind: 'moth', x: 900 + Math.cos(a) * 120, y: 300 + Math.sin(a) * 90,
              vx: Math.cos(a) * 90, vy: Math.sin(a) * 60 - 20, life: 4, seed: Math.random() * 9 };
          });
        } },
      { narrate: 'The swarm broke against it like water on a stone. The moths rose, wheeled once around the tower — and scattered back into the dark, thin and aimless again.' },
      { wait: 1.2 },
      { mood: 'resolve' },
      { cam: { x: 900, y: 300, viewH: 560 } },
      { say: ['tally:awed', '…Ha. Hahaha. It’s— I did the glass on Sundays. Every Sunday. And the books never once say that it’s YELLOW—'] },
      { say: ['system', '(Tally is laughing. Tally is also crying. He does not appear to have noticed either.)'] },
      { say: ['lake:tender', 'You lit it too, Tally. Whoever keeps the wick dry is lighting the lamp — grandmother’s rule. You’ve been lighting this one your whole life. It just caught tonight.'] },
      { say: ['tally:awed', '…I’m going to write that in the margin of Volume One.'] },
      { wait: 0.8 },
      { say: ['tally:earnest', 'Now. Rule one, said properly this time: no bare flame outdoors after dark. The stores keep a walking-hood — brass cowl, Order pattern. The flame breathes; the light stays home.'] },
      { toast: { text: '✦ The walking-hood — the lighter travels shielded at night', color: '#e0a94e' } },
      { say: ['vesper:thinking', '(Entry: lamps ward moths. Great lamps ward roads. And after dark my partner is the most interesting thing in the world to every hungry thing on it. Underlined twice.)'] },
      { fadeTo: 1 }, { wait: 1.0 },
      { run: () => {
          F.swarmDone = true; F.hooded = true; F.swarmActive = false;
          Field.setSceneState('lanternstead', 'morning');
          Field.setSceneState('lanternstead-int', 'morning');
          if (vesper) { vesper.x = 520; vesper.y = 530; vesper.dir = 'up'; }
          if (lake) { lake.x = 640; lake.y = 545; lake.dir = 'up'; }
          tally.x = 655; tally.y = 500; tally.dir = 'down';
          maren.x = 720; maren.y = 560; maren.dir = 'left';
          this.npcs.mochi.x = 600; this.npcs.mochi.y = 580;
        } },
      { fadeTo: 0 },
      { wait: 0.4 },
    ]);
  },

  // BEAT 5 — morning: the grey post-crow, Rowan's letter
  playLetter(players) {
    const F = this.flags;
    F.letterRead = true;                                        // latched now; scene is frozen till it ends
    const crow = this.npcs.postcrow, tally = this.npcs.tally;
    const vesper = players.find(p => p && p.role === 'vesper');
    Cutscene.play([
      { narrate: 'Morning came up almost blue. Inside the great-lantern’s ring the frost had kept off the vegetable rows — and the crows were shouting about a visitor.' },
      { run: () => {                                            // Twenty-Two comes in on the wing
          crow.hidden = false; crow.char = 'postcrow-fly';
          crow.scene = 'lanternstead'; crow.x = 380; crow.y = 250; crow.dir = 'right';
        } },
      { cam: { x: 585, y: 440, viewH: 520 } },
      { move: { ent: crow, x: 585, y: 395, speed: 190 } },
      { run: () => { crow.char = 'postcrow'; crow.dir = 'down'; crow.moving = false; } },
      { say: ['tally:happy', 'Twenty-Two! MANNERS!'] },
      { say: ['vesper', 'You number your crows?'] },
      { say: ['tally', 'They’re post-crows, madam — the Order’s message line. The route runs to every Heartlight; the birds still fly it, because I still feed it. The letters stopped long before me.'] },
      { say: ['tally:earnest', 'She’s carrying. She’s— that is the first letter on this route since my teacher died.'] },
      { wait: 0.8 },
      { say: ['lake', 'Somebody at our end remembered what the old perch by the gate was for.'] },
      { say: ['vesper', 'Rowan.'] },
      { mood: 'hush' },
      { run: () => { if (vesper) { vesper.x = 555; vesper.y = 490; vesper.dir = 'up'; } } },  // vesper takes the tube; unrolls
      { say: ['vesper', 'It’s his hand. Steady as ever. “To the mapmaker and the lamplighter, gone north.”'] },
      { cam: { x: 600, y: 500, viewH: 440 } },
      { say: ['rowan:hollow', '“Day two. The village is fed. The mill turns. The weather has been fair for the season.”'] },
      { say: ['rowan:hollow', '“Notices: the baker bakes daily; output normal. The child Pip continues his instruction of the woman Mara; progress is recorded. The fisherman reports that the pond has fish in it. This is all of the news.”'] },
      { say: ['rowan:hollow', '“The ledger is kept. I find I have nothing further to put in this letter, though I sat an hour with it. Provisions follow with the bird. — R. Elder.”'] },
      { wait: 1.6 },
      { say: ['vesper', '…It’s all true. Every line of it is true, and correct, and in order.'] },
      { say: ['lake', 'That’s what’s wrong with it.'] },
      { say: ['vesper:sad', '(Rowan makes jokes. Rowan makes jokes the way the mill turns. There is not one joke in this letter.)'] },
      { say: ['lake:worried', 'He wrote “the woman Mara.” He named her to the flame himself, the day she was born — he used to tell that story every Emberwake. Now she’s “the woman Mara.”'] },
      { wait: 1.2 },
      { say: ['vesper:determined', 'New page. “Day two: the village is fed, and fading. The facts are keeping. The people aren’t.” …We walk faster.'] },
      { say: ['lake', 'She used to say a street goes cold slower than it warms. It’s the only mercy we’ve got. Let’s spend it walking.'] },
      { mood: 'resolve' },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['system', '(Mochi leans, very briefly, against Lake’s boot. Then pretends he didn’t.)'] },
      { camRelease: true },
      { run: () => {                                            // Tally heads in to the wall-map
          tally.scene = 'lanternstead-int'; tally.x = 935; tally.y = 480; tally.dir = 'up';
        } },
    ]);
  },

  // BEAT 6 — the wall-map, Tally joins, end card
  playWallMap(players) {
    const F = this.flags;
    if (F.tallyJoined) return;
    F.mapSeen = true;
    const tally = this.npcs.tally;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    Cutscene.play([
      { run: () => { tally.scene = 'lanternstead-int'; tally.x = 935; tally.y = 480; tally.dir = 'up'; } },
      { cam: { x: 930, y: 380, viewH: 480 } },
      { say: ['tally:earnest', 'Before you walk, you should see what road you’re on.'] },
      { say: ['tally', 'The circuit. One road, thirteen stations, ringing the deep wood — a Heartlight in every valley, and every one of them a daughter of the mother-fire at the middle. Emberbrook, here. The Lanternstead — you are here. First station north.'] },
      { say: ['maren:awed', 'Dellhollow. We’re ON somebody’s map. Ma would say that’s no excuse for anything.'] },
      { say: ['tally:earnest', 'And ahead — Harrowdel. Three days up the circuit. A LIVING valley, Flamebearer: their lamps still answer. The last on this road that do.'] },
      { say: ['vesper', 'And the little marks? Under every name?'] },
      { say: ['tally', 'Sunrises the station has been kept. My teacher started the count; I kept the count. It’s also where I got my name — the crows had names, and I had marks, so.'] },
      { say: ['tally:earnest', 'It is a great many marks, madam. But the count held. That’s the whole of the friar’s rite: hold the count until the walkers come.'] },
      { say: ['tally:happy', 'You came.'] },
      { wait: 1.0 },
      { say: ['lake:worried', 'The walker we saw on the road. Pale lantern, full. If he’s out here—'] },
      { say: ['tally:earnest', 'One road is all there is, Flamebearer. Whatever he keeps, he keeps it somewhere ahead of you.'] },
      { say: ['system', '(Mochi is sitting in the doorway, facing north.)'] },
      { wait: 1.0 },
      { say: ['tally:earnest', 'Which brings me to a request I have practiced, so let me get it out. The station kept the road FOR the walkers. The walkers are back. Therefore the keeping goes WITH you — that’s doctrine. I checked. I checked twice.'] },
      { say: ['vesper', 'Tally. Are you asking to come with us?'] },
      { say: ['tally', 'Desperately, madam.'] },
      { say: ['lake:happy', 'The road was meant to be walked by two. …Nobody ever said ONLY two.'] },
      { say: ['tally:happy', 'I’ll fetch the kettle. Not the good kettle. The WALKING kettle. We have DOCTRINE about kettles—'] },
      { toast: { text: '✦  Friar Tally joined the party  ✦', color: '#d97b3f' } },
      { say: ['vesper:thinking', '(For the record: party of three, one cat, one crow flying the route behind us. The chart is getting crowded. I find I don’t mind.)'] },
      { say: ['tally', 'Twenty-Two flies the circuit — she’ll find us wherever the road puts us. The rest stay and keep the necklace. Somebody must.'] },
      { banner: { title: '✦ The road to Harrowdel ✦', sub: 'three days north — the last living valley on the circuit', dur: 6 } },
      { run: () => { F.tallyJoined = true; tally.follow = 'party'; } },
      { fadeTo: 1 }, { wait: 0.8 },
      { run: () => {                                            // exterior shot: morning, lantern burning; party at the south exit
          Field.setSceneState('lanternstead', 'morning');
          Field.scenes.lanternstead.lamps[0].lit = true;
          if (vesper) { vesper.scene = 'lanternstead'; vesper.x = 230; vesper.y = 700; vesper.dir = 'down'; }
          if (lake) { lake.scene = 'lanternstead'; lake.x = 295; lake.y = 710; lake.dir = 'down'; }
          tally.scene = 'lanternstead'; tally.x = 350; tally.y = 700; tally.dir = 'down';
          this.npcs.maren.scene = 'lanternstead'; this.npcs.maren.x = 170; this.npcs.maren.y = 705; this.npcs.maren.dir = 'down';
          this.npcs.mochi.scene = 'lanternstead'; this.npcs.mochi.x = 260; this.npcs.mochi.y = 735;
          Field.enter('lanternstead');
        } },
      { fadeTo: 0 },
      { cam: { x: 900, y: 240, viewH: 640 } },
      { narrate: 'They left the Lanternstead burning behind them — the first light of the necklace, lit again; a shut gate at their backs and three days of grey road ahead.' },
      { narrate: 'And behind them the great-lantern held its one note of yellow against the winter, saying to anyone on the road what the Order had always meant it to say: keep walking. You are expected.' },
      { mood: 'silence' },
      { run: () => { F.ended = true; AudioSys.finale(); Net.send({ type: 'end' }); } },
    ]);
  },

  /* ================= dev checkpoints (via the C checkpoint menu) ================= */
  CHECKPOINT_NAMES: ['', 'Ch3: the grey road', 'Ch3: the Lanternstead at night (swarm ready)',
    'Ch3: morning (the letter & the wall-map)'],
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
    j.parked = false; j.hidden = false; c.parked = false; c.hidden = false;

    if (n === 1) {
      // the grey road — lamps unlit, straight into the rounds
      F.roadIntro = true;
      place(j, 'road', 150, 640, 'right'); place(c, 'road', 235, 665, 'right');
      place(N.mochi, 'road', 300, 620, 'right');
      place(N.maren, 'road', 175, 690, 'right');
      AudioSys.setMood('forestB');
    }
    if (n >= 2) {
      F.roadIntro = true; F.roadLamps = 3; F.strangerSeen = true;
      F.arrived = true; F.wellDone = true;
      Field.scenes.road.lamps.forEach(l => { l.lit = true; });
      N.tally.hidden = false;
    }
    if (n === 2) {
      // the Lanternstead at night — supperDone set so playSwarm fires immediately
      F.supperDone = true;
      Field.setSceneState('lanternstead', 'night');
      FX.desatTarget = 0.45;
      place(j, 'lanternstead', 620, 560, 'down'); place(c, 'lanternstead', 700, 570, 'down');
      place(N.tally, 'lanternstead', 900, 570, 'up');
      place(N.maren, 'lanternstead', 560, 585, 'right');
      place(N.mochi, 'lanternstead', 650, 605, 'left');
      AudioSys.setMood('silence');
    }
    if (n === 3) {
      // morning — swarm done, hood taken, the letter one breath away
      F.supperDone = true; F.swarmDone = true; F.hooded = true;
      Field.setSceneState('lanternstead', 'morning');
      Field.setSceneState('lanternstead-int', 'morning');
      Field.scenes.lanternstead.lamps[0].lit = true;
      place(j, 'lanternstead', 520, 530, 'up'); place(c, 'lanternstead', 640, 545, 'up');
      place(N.tally, 'lanternstead', 655, 500, 'down');
      place(N.maren, 'lanternstead', 720, 560, 'left');
      place(N.mochi, 'lanternstead', 600, 580, 'left');
      AudioSys.setMood('resolve');
    }
    Field.enter(j.scene);
    Field.cam.x = j.x; Field.cam.y = j.y;
    this.setPhase('together');
    Toasts.add('⚑ checkpoint — ' + this.CHECKPOINT_NAMES[n], '#8fb0c9');
  },
};
