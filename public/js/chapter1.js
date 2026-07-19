'use strict';
/* ============================================================
   CHAPTER ONE — "Emberwake"  (painted scene edition)

   Act I   — JUNE: a forest road with no name, a waystone from
             a dream, and a village that isn't on any map.
   Act II  — COLE: a cottage with one warm flame, and the last
             lamplighter's rounds on festival night.
   Act III — the Kindling Hour, the Hush, and what two strangers
             still hold when a village forgets itself.
   ============================================================ */

const Chapter1 = {
  phase: 'june',                    // 'june' | 'cole' | 'together'
  flags: {
    juneIntro: false, waystone: false, juneTalked: {}, juneDone: false,
    coleIntro: false, lampsLit: 0,
    met: false, hushDone: false, seen: {},
    pactDone: false, gateOpen: false, ended: false, endT: 0,
    endingStarted: false,
  },
  npcs: {}, entities: [],

  activeRoles() {
    return this.phase === 'june' ? ['june'] : this.phase === 'cole' ? ['cole'] : ['june', 'cole'];
  },
  setPhase(p) {
    this.phase = p;
    Net.send({ type: 'phase', act: p });
  },

  /* ================= SCENES ================= */
  buildScenes() {
    const S = {
      forest: {
        states: { festival: 'assets/scenes/forest/main.png' }, state: 'festival',
        viewH: 540, charH: 120, speed: 190, fireflies: true,
        tints: { festival: '#9fa8c9' },
        walk: [[0, 768], [200, 768], [1344, 210], [1344, 70], [1180, 60], [0, 610]],
        blocked: [],
        exits: [{ zone: { x: 1170, y: 30, w: 174, h: 320 }, to: 'entrance', spawn: [280, 660, 'right'] }],
      },
      entrance: {
        states: { festival: 'assets/scenes/entrance/main.png' }, state: 'festival',
        viewH: 540, charH: 125, speed: 190,
        tints: { festival: '#d9b18c' },
        walk: [[150, 768], [980, 768], [1344, 600], [1344, 300], [1020, 250], [720, 300], [430, 500], [220, 640]],
        blocked: [
          { kind: 'circle', x: 565, y: 500, r: 70 },     // waystone
          { kind: 'rect', x: 620, y: 180, w: 200, h: 180 },  // trees by gate
          { kind: 'rect', x: 780, y: 200, w: 130, h: 200 },  // palisade left of arch
          { kind: 'circle', x: 950, y: 648, r: 62 },     // trees lower right
          { kind: 'rect', x: 1200, y: 250, w: 144, h: 150 }, // cottage right
        ],
        occluders: [{ x: 470, y: 250, w: 190, h: 300, baseY: 520 }],  // waystone top
        exits: [
          { zone: { x: 1150, y: 300, w: 194, h: 400 }, to: 'square', spawn: [672, 675, 'up'] },
          { zone: { x: 100, y: 620, w: 120, h: 148 }, to: 'forest', spawn: [1080, 120, 'left'] },
        ],
      },
      interior: {
        states: { festival: 'assets/scenes/interior/main.png' }, state: 'festival',
        viewH: 700, charH: 215, speed: 290,
        tints: { festival: '#f2c091' },
        walk: [[430, 470], [620, 380], [900, 430], [1080, 500], [1050, 620], [780, 740], [520, 720], [400, 610]],
        blocked: [
          { kind: 'rect', x: 600, y: 240, w: 310, h: 210 },
          { kind: 'rect', x: 505, y: 470, w: 185, h: 145 },
          { kind: 'rect', x: 920, y: 250, w: 150, h: 240 },
          { kind: 'rect', x: 390, y: 230, w: 210, h: 230 },
        ],
        exits: [{ zone: { x: 380, y: 560, w: 90, h: 150 }, to: 'lane', spawn: [400, 505, 'down'] }],
      },
      lane: {
        states: { festival: 'assets/scenes/lane/main.png' }, state: 'festival',
        viewH: 560, charH: 130, speed: 200,
        tints: { festival: '#b8b4c9' },
        walk: [[0, 768], [520, 768], [590, 690], [720, 610], [860, 545], [1010, 480], [1180, 445], [1344, 430], [1344, 300], [1010, 315], [660, 445], [340, 600], [0, 660]],
        walkExtra: [{ x: 806, y: 462, w: 180, h: 108 }],   // the dock
        blocked: [
          { kind: 'rect', x: 40, y: 100, w: 450, h: 320 },   // cottage
          { kind: 'rect', x: 0, y: 420, w: 210, h: 150 },    // left fence run
          { kind: 'rect', x: 425, y: 280, w: 135, h: 130 },  // right fence run
          { kind: 'circle', x: 903, y: 400, r: 16 },         // lamp post
        ],
        lamps: [{ x: 903, y: 268, lit: false, id: 'lamp1', base: [903, 420] }],
        exits: [
          { zone: { x: 300, y: 385, w: 80, h: 55 }, to: 'interior', spawn: [500, 630, 'up'] },
          { zone: { x: 1220, y: 280, w: 124, h: 190 }, to: 'square', spawn: [120, 390, 'right'] },
        ],
      },
      square: {
        // pipeline scene: candidate C + north road, baked bitmap mask, keyed cutout occluders
        states: { festival: 'assets/scenes/square/festival.png', gray: 'assets/scenes/square/gray.png' }, state: 'festival',
        maskSrc: 'assets/scenes/square/mask.png',
        viewH: 560, charH: 125, speed: 190, mothAmbience: true,
        tints: { festival: '#e2a97e', gray: '#9aa3b5' },
        heartlight: { x: 672, y: 415 },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback only; the mask governs
        blocked: [],
        // no walk-behind occluders by design: objects block wholesale
        // (simple and predictable beats fragile walk-behind strips)
        lamps: [
          { x: 764, y: 222, lit: false, id: 'lamp2', base: [765, 312] },
          { x: 1093, y: 428, lit: false, id: 'lamp3', base: [1094, 536] },
          { x: 250, y: 396, lit: true, base: [251, 486] },
        ],
        exits: [
          { zone: { x: 70, y: 700, w: 270, h: 68 }, to: 'entrance', spawn: [1230, 470, 'left'],
            enabled: () => !Chapter1.flags.hushDone,
            deniedLine: ['june', 'The south road can wait. Something is happening HERE.'] },
          { zone: { x: 0, y: 590, w: 70, h: 178 }, to: 'lane', spawn: [1250, 380, 'left'],
            enabled: () => Chapter1.phase !== 'june' && !Chapter1.flags.hushDone,
            deniedLine: ['cole', 'The lane’s dark and empty. Everyone who matters is in the square tonight.'] },
          { zone: { x: 630, y: 0, w: 190, h: 110 }, to: 'gate', spawn: [672, 660, 'up'],
            enabled: () => Chapter1.flags.pactDone,
            deniedLine: ['cole', 'The Old Gate. Nobody goes that way… it’s been shut my whole life.'] },
        ],
      },
      gate: {
        states: { gray: 'assets/scenes/gate/gray.png', open: 'assets/scenes/gate/open.png' }, state: 'gray',
        viewH: 560, charH: 125, speed: 190, mothAmbience: true,
        tints: { gray: '#9aa3b5', open: '#9aa3b5' },
        walk: [[170, 768], [1180, 768], [1180, 520], [960, 445], [780, 425], [560, 425], [360, 455], [170, 545]],
        walkExtra: [{ x: 585, y: 295, w: 165, h: 140, state: 'open' }],
        blocked: [{ kind: 'circle', x: 292, y: 620, r: 15 }],
        plates: [{ x: 420, y: 580, hold: 0 }, { x: 930, y: 578, hold: 0 }],
        platesActive: false,
        exits: [{ zone: { x: 580, y: 660, w: 180, h: 108 }, to: 'square', spawn: [672, 160, 'down'],
          enabled: () => !Chapter1.flags.endingStarted }],
      },
    };
    Field.register(S);
  },

  build() {
    this.buildScenes();
    const N = (key, scene, x, y, dir, h) => {
      const e = { key, char: key, scene, x, y, dir: dir || 'down', moving: false, animT: 0, h: h || 90 };
      this.npcs[key] = e; this.entities.push(e);
      return e;
    };
    N('rowan', 'square', 790, 565, 'left', 138);
    N('poppy', 'square', 438, 598, 'left', 112);
    N('mara', 'square', 985, 655, 'left', 122);
    N('pip', 'square', 945, 672, 'left', 70);
    N('finn', 'lane', 890, 500, 'down', 130);
    const mochi = N('mochi', 'entrance', 640, 560, 'left', 48);
    mochi.hidden = true; mochi.follow = null;
    const stranger = N('stranger', 'gate', 672, 310, 'down', 145);
    stranger.hidden = true;

    AudioSys.setMood('forest');   // June's act opens in the old forest
  },

  spawnFor(role) {
    return role === 'june'
      ? { scene: 'forest', x: 120, y: 690, dir: 'right' }
      : { scene: 'interior', x: 880, y: 590, dir: 'down' };
  },

  /* ================= per-frame ================= */
  update(dt, players) {
    const F = this.flags;
    // forest music holds until June steps out of the trees
    if (!F.leftForest && this.phase === 'june') {
      const j = players.find(p => p && p.role === 'june');
      if (j && j.scene && j.scene !== 'forest') { F.leftForest = true; AudioSys.setMood('festival'); }
    }
    const june = players.find(p => p && p.role === 'june');
    const cole = players.find(p => p && p.role === 'cole');

    if (cole) cole.hidden = this.phase === 'june';
    if (june) june.parked = this.phase === 'cole';

    // Act I triggers
    if (this.phase === 'june' && june && !F.juneIntro && !Cutscene.active) this.playJuneIntro(june);
    if (this.phase === 'june' && june && F.juneIntro && !F.waystone &&
        june.scene === 'entrance' && june.x > 400 && !Cutscene.active)
      this.playWaystone(june);

    // Act II triggers
    if (this.phase === 'cole' && cole && !F.coleIntro && !Cutscene.active && !Dialog.active())
      this.playColeIntro(cole);
    if (this.phase === 'cole' && !F.met && F.lampsLit >= 3 && june && cole &&
        cole.scene === 'square' && !Cutscene.active && !Dialog.active())
      this.playMeet(players);

    // Pip orbits his mother during the festival
    const pip = this.npcs.pip, mara = this.npcs.mara;
    if (!F.hushDone && !Cutscene.active) {
      pip.animT += dt; pip.moving = true;
      const a = time * 1.6;
      pip.x = mara.x + Math.cos(a) * 34;
      pip.y = mara.y + Math.sin(a) * 16 + 8;
      pip.dir = Math.cos(a) > 0 ? 'right' : 'left';
    } else { pip.moving = false; }

    // Mochi the follower
    const mochi = this.npcs.mochi;
    if (!Cutscene.active && mochi.follow) {
      let target = null;
      if (mochi.follow === 'june' && june && !june.parked) target = june;
      else if (mochi.follow === 'party') {
        const ps = players.filter(p => p && !p.hidden);
        if (ps.length) target = ps[0];
      }
      if (target) {
        mochi.scene = target.scene;
        // rest beside the player, skipping spots that fall inside an obstacle
        let tx = target.x - 40, ty = target.y + 8, restOk = false;
        for (const [ox, oy] of [[-40, 8], [40, 8], [0, -45], [0, 45]]) {
          if (fieldWalkable(target.scene, target.x + ox, target.y + oy)) { tx = target.x + ox; ty = target.y + oy; restOk = true; break; }
        }
        const dx = tx - mochi.x, dy = ty - mochi.y, d = Math.hypot(dx, dy);
        if (d > 500) { mochi.x = tx; mochi.y = ty; mochi.moving = false; } // wedged: snap to rest
        else if (d > 60 && (restOk || d > 85)) {
          mochi.moving = true; mochi.animT += dt;
          const step = Math.min(200, d * 2.4) * dt;
          const nx = mochi.x + dx / d * step, ny = mochi.y + dy / d * step;
          const curOk = fieldWalkable(mochi.scene, mochi.x, mochi.y);
          let moved = false;
          if (dx && (fieldWalkable(mochi.scene, nx, mochi.y) || !curOk)) { mochi.x = nx; moved = true; }
          if (dy && (fieldWalkable(mochi.scene, mochi.x, ny) || !curOk)) { mochi.y = ny; moved = true; }
          if (!moved) {
            const px2 = -dy / d, py2 = dx / d;
            for (const sgn of [1, -1]) {
              const sx2 = mochi.x + px2 * sgn * step * 0.9, sy2 = mochi.y + py2 * sgn * step * 0.9;
              if (fieldWalkable(mochi.scene, sx2, sy2)) { mochi.x = sx2; mochi.y = sy2; break; }
            }
          }
          mochi.dir = dx > 0 ? 'right' : 'left';
        } else mochi.moving = false;
      }
    }

    // sigil plates (gate scene)
    const gateScene = Field.scenes.gate;
    if (F.pactDone && !F.gateOpen && gateScene.platesActive) {
      let all = true;
      for (const pl of gateScene.plates) {
        const on = players.some(p => p && p.scene === 'gate' && Math.hypot(p.x - pl.x, p.y - pl.y) < 75);
        pl.hold = on ? Math.min(1, pl.hold + dt / 1.2) : Math.max(0, pl.hold - dt * 2);
        if (pl.hold < 1) all = false;
      }
      if (all && june && cole) {
        F.gateOpen = true;
        gateScene.platesActive = false;
        AudioSys.rumble();
        FX.shake = 5; FX.flash = 0.8;
        Net.send({ type: 'buzz', ms: 300 });
        setTimeout(() => { Field.setSceneState('gate', 'open'); AudioSys.chime(); }, 900);
      }
    }

    // chapter end — both step into the open arch
    if (F.gateOpen && !F.ended && !F.endingStarted && !Cutscene.active &&
        june && cole && june.scene === 'gate' && cole.scene === 'gate' &&
        june.y < 430 && cole.y < 430 && june.x > 560 && june.x < 790 && cole.x > 560 && cole.x < 790) {
      this.playEnding(players);
    }
    if (F.ended) F.endT += dt;
  },

  objective() {
    const F = this.flags;
    if (F.ended) return '';
    if (this.phase === 'june') {
      if (!F.waystone) return 'Follow the road';
      const n = Object.keys(F.juneTalked).length;
      if (!F.juneDone) {
        if (n < 2) return `Emberwake — meet the villagers (${n}/2)`;
        return 'Find whoever is in charge — the elder, by the glowing crystal';
      }
      return '';
    }
    if (this.phase === 'cole') {
      if (!F.coleIntro) return '';
      const hints = [];
      const laneLamp = Field.scenes.lane.lamps.find(l => l.id === 'lamp1');
      if (laneLamp && !laneLamp.lit) hints.push('one on the pond lane');
      const sqLeft = Field.scenes.square.lamps.filter(l => l.id && !l.lit).length;
      if (sqLeft) hints.push(sqLeft === 2 ? 'two in the square' : 'one in the square');
      return `Your rounds — light the dark lamps (${F.lampsLit}/3)${hints.length ? ' · ' + hints.join(' · ') : ''}`;
    }
    if (!F.hushDone) return 'The Kindling Hour begins…';
    if (!F.pactDone) {
      const n = Object.keys(F.seen).length;
      return n < 4 ? `See to the villagers — (${n}/4)` : 'Find Elder Rowan by the Heartlight';
    }
    if (!F.gateOpen) return 'Stand on the twin sigils before the Old Gate — together';
    return 'Step through the Old Gate — together';
  },

  /* ================= interaction ================= */
  nearestThing(p) {
    let best = null, bd = Infinity;
    const consider = (x, y, thing, r) => {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d > (r || 85)) return;
      if (d < bd) { bd = d; best = thing; }
    };
    for (const n of Object.values(this.npcs)) {
      if (n.hidden || n.scene !== p.scene) continue;
      if (n.key === 'mochi' && n.follow) continue;   // considered last, below
      consider(n.x, n.y, { kind: 'npc', key: n.key, ent: n });
    }
    if (p.role === 'cole') {
      const s = Field.scenes[p.scene];
      for (const l of (s.lamps || [])) if (!l.lit && l.id) consider(l.base[0], l.base[1], { kind: 'lamp', lamp: l });
    }
    if (p.scene === 'entrance') consider(565, 520, { kind: 'waystone' }, 80);
    if (p.scene === 'square') {
      consider(672, 560, { kind: 'heartlight' }, 72);
      consider(206, 535, { kind: 'notice' }, 58);
    }
    if (p.scene === 'interior') consider(500, 400, { kind: 'hearth' }, 70);
    // the following cat never outranks anything else
    const mochi = this.npcs.mochi;
    if (!best && mochi.follow && !mochi.hidden && mochi.scene === p.scene &&
        Math.hypot(p.x - mochi.x, p.y - mochi.y) < 85)
      best = { kind: 'npc', key: 'mochi', ent: mochi };
    return best;
  },

  promptFor(p) {
    if (this.flags.ended) return '';
    if (!this.activeRoles().includes(p.role)) return '';
    if (Cutscene.holdJob) return 'HOLD  A';
    if (Dialog.active()) return 'Next ▸';
    if (Cutscene.active) return '';
    const t = this.nearestThing(p);
    if (t) {
      if (t.kind === 'lamp') return 'A — light the lamp';
      if (t.kind === 'npc') return 'A — talk to ' + SPEAKERS[t.key].name;
      if (t.kind === 'heartlight') return 'A — the Heartlight';
      return 'A — look';
    }
    if (this.flags.pactDone && !this.flags.gateOpen && p.scene === 'gate')
      return 'Stand on the sigil — together';
    return '';
  },

  interact(p) {
    if (!this.activeRoles().includes(p.role)) return;
    const t = this.nearestThing(p);
    if (!t) return;
    if (t.kind === 'lamp') return this.lightLamp(t.lamp, p);
    if (t.kind === 'npc') return this.talkTo(t.key, t.ent, p);
    if (t.kind === 'heartlight') {
      const alive = Field.scenes.square.state === 'festival';
      Dialog.start([{ who: 'system', text: alive
        ? 'The Heartlight of Emberbrook. Three hundred years of the village live inside it — every wedding, every argument, every good loaf and bad winter. It hums, very faintly, like a kettle two rooms away.'
        : 'What is left of the Heartlight. It does not hum. It does not do anything. Holding a hand near it feels like reading a letter from someone who never existed.' }]);
    }
    if (t.kind === 'notice') {
      Dialog.start([{ who: 'system', text: this.flags.hushDone
        ? 'The notice board. The letters are still here, but they have stopped meaning anything to anyone but you two. One notice reads: "LOST — brown dog, answers to Biscuit."'
        : 'The notice board. "EMBERWAKE TONIGHT — bring a memory worth keeping. And a chair. We are short of chairs."' }]);
    }
    if (t.kind === 'waystone') {
      Dialog.start([{ who: 'system', text: p.role === 'june'
        ? 'The waystone from drawing forty-one. She has stopped checking whether it matches. It matches.'
        : 'An old waystone. EMBERBROOK, it says, under forty years of moss. Somebody has recently brushed the moss off the E.' }]);
    }
    if (t.kind === 'hearth') {
      Dialog.start([{ who: 'system', text: 'The hearth. Grandmother’s portrait watches from above the mantel — the frame is dusted daily; the eyes still miss nothing.' }]);
    }
  },

  lightLamp(lamp, p) {
    lamp.lit = true;
    this.flags.lampsLit++;
    AudioSys.lampOn();
    Net.send({ type: 'buzz', ms: 60 });
    Particles.burst(8, () => ({ kind: 'sparkle', x: lamp.x + (Math.random() - 0.5) * 16, y: lamp.y + (Math.random() - 0.5) * 12, vy: -8, life: 0.8 }));
    if (this.flags.lampsLit === 1)
      Dialog.start([{ who: 'cole', text: '(One. The wick takes the flame like it remembers it. Grandmother swore they do.)' }]);
    if (this.flags.lampsLit === 2)
      Dialog.start([{ who: 'cole', text: '(Two. Light them like you mean it, she said, or they gutter by midnight. She never once explained what meaning it involved. I improvise.)' }]);
  },

  /* ================= dialogue ================= */
  talkTo(key, ent, p) {
    const F = this.flags;
    const dx = p.x - ent.x, dy = p.y - ent.y;
    if (key !== 'mochi') ent.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    const isJune = p.role === 'june';
    const D = (lines, onFinish) => Dialog.start(lines.map(l => ({ who: l[0], text: l[1] })), onFinish);

    if (!F.hushDone) {
      if (key === 'rowan') {
        if (isJune) {
          if (Object.keys(F.juneTalked).length < 2) return D([
            ['rowan', 'A guest! Welcome, welcome. But guests eat first — that is LAW on Emberwake, ask the baker. Come back to me fed and greeted.'],
          ]);
          return D([
            ['rowan', 'Now then. A guest, on Emberwake of all nights! Nobody finds Emberbrook by accident, my dear — so you were either invited, or meant.'],
            ['june', 'June. Mapmaker. Neither, I hope — I need to get through your gate, and I’m told you’re in charge.'],
            ['rowan', 'In charge! Ha! I keep the ledger; the village keeps itself. And nobody opens the Old Gate, child. It hasn’t a key. It has RULES.'],
            ['june', 'Rules can be charted. Charting things is my whole profession.'],
            ['rowan', '…Ha! I like you. Stay for the Kindling Hour, mapmaker — one hour, the whole village, the year’s best memories going into the flame for safekeeping. Nobody should walk into the Whisperwood on an empty heart.'],
            ['rowan', 'As for the Gate — lamplighter business. His order built it, his order shut it, and I have never heard the boy so much as knock. Ask HIM.'],
            ['rowan', 'The quiet one with the flame that never goes out. You’ll find him apologizing to lamps somewhere across the village.'],
          ], () => { if (!F.juneDone) this.playJuneOutro(p); });
        }
        return D([['rowan', 'Cole! The Kindling Hour will not wait for poetry. Lamps, boy, lamps!']]);
      }
      if (key === 'poppy') {
        if (isJune) { F.juneTalked.poppy = true;
          return D([
            ['poppy', 'A new face! Nobody passes through Emberbrook on Emberwake without eating something warm. That is not hospitality, that is law.'],
            ['june', 'I— alright. One. For the record, I’m here to chart the Whisperwood, not to eat pastry.'],
            ['poppy:laughing', 'Chart the— HA! Did you hear her? Eat two.'],
            ['june', 'Fine. Question, though — everyone keeps saying “the Kindling Hour” like I was born knowing what it is.'],
            ['poppy', 'Simplest thing in the world, love. Once a year you bring your best memory and TELL it to the flame. The flame keeps it — safe, perfect, forever. You keep it warm, long as you live in the lamplight.'],
            ['june', 'You give your memories. To a fire. On purpose.'],
            ['poppy:happy', 'GIVE? Tell! Would you keep your life savings under a mattress? That flame has kept my whole life safer than my own head ever could. Three hundred years, never lost so much as a Tuesday.'],
            ['june', '(I ate two. In my defense, they were extraordinary, and I have been walking for eleven days.)'],
          ]);
        }
        return D([
          ['poppy:happy', 'There he is! The only soul in Emberbrook allowed to be late tonight — because nothing starts till his lamps are lit. Bun?'],
          ['cole', 'On duty, Poppy.'],
          ['poppy', 'Half a bun. I’ll hold the other half hostage until the Kindling Hour.'],
          ['poppy', 'And no use asking if YOU’LL finally make a telling this year. Keeper keeps his own — I know, I know. Queerest rule your family ever kept. Saddest one, too.'],
          ['cole', '(Everyone else banks their year in the flame. We keep ours the hard way. “Someone has to stand outside the kept,” she said. I never asked why.)'],
        ]);
      }
      if (key === 'finn') {
        if (isJune) F.juneTalked.finn = true;
        return D([
          ['finn', 'Festival’s up in the square. Fish are down here. I know which conversation I prefer.'],
          ['finn', 'Somethin’s got the pond spooked tonight, though. They’re swimmin’ in a circle. One big circle. All of ’em. Slow.'],
          [isJune ? 'june' : 'cole', isJune ? 'Fish don’t… do that. Do they?' : 'They ever done that before, Finn?'],
          ['finn', 'Didn’t think so either, this morning.'],
        ]);
      }
      if (key === 'mara' || key === 'pip') {
        if (isJune) { F.juneTalked.mara = true;
          return D([
            ['mara', 'Pip, love, stop orbiting the nice stranger.'],
            ['pip', 'Are you a REAL mapmaker? Have you been EVERYWHERE? Have you been to the MOON?'],
            ['june', '…Not yet.'],
            ['pip', 'She’s been to the moon.'],
            ['mara', 'He will remember tonight his whole life. Nights like this are what winters are for.'],
          ]);
        }
        return D([
          ['mara', 'He’s been up since dawn, Cole. He’ll sleep where he falls, and I’ll carry him home like every year.'],
          ['pip', 'I will NOT fall asleep. I am going to see the flame take the memories. Renn says you can SEE them go in.'],
          ['mara', 'Remember this night, both of you. That’s what it’s for.'],
        ]);
      }
      if (key === 'mochi') return D(isJune ? [
        ['mochi', 'Mrrp.'],
        ['june', 'You’re still here. I don’t feed you. I have never fed you.'],
        ['mochi', 'Mrrp.'],
      ] : [
        ['mochi', '(Mochi is escorting the stranger with the interesting satchel. He acknowledges you, lamplighter, as staff.)'],
      ]);
    }

    /* ---- after the Hush ---- */
    if (key === 'rowan') {
      if (Object.keys(F.seen).length < 4) return D([
        ['rowan', 'See to them first. All of them. They deserve to hear their names from someone who still owns them.'],
        ['rowan', 'I will be here, reading my ledger… while it still says anything at all.'],
      ]);
      if (!F.pactDone) return this.playPact(p);
      return D([['rowan', 'Twin sigils, before the Gate. Two keepers, one flame. Walk close, and walk kindly.']]);
    }
    if (key === 'poppy') {
      if (!F.seen.poppy) { F.seen.poppy = true;
        return D([
          ['poppy:hollow', '…Why am I holding bread? Whose stall is this? Whose HANDS are these— no, those are mine, I recognize the burn scars.'],
          ['cole', 'You’re Poppy. You bake. Every morning you burn your thumb on the first tray and swear you won’t tomorrow.'],
          ['poppy', '…Do I do it anyway?'],
          ['cole', 'Every morning.'],
          ['poppy', 'The word. The round warm things. Give me the word.'],
          ['june', 'Honeybuns.'],
          ['poppy:happy', 'HONEYBUNS. Say more words. Both of you. Anything in this stall, it’s yours — I am reliably informed it is mine to give.'],
          ['june:thinking', '(I’m writing it all down. Everything they’ve lost. If this ever happens again — there will be a copy of everyone.)'],
        ]);
      }
      return D([['poppy', 'Honeybuns. Poppy. Thumb. I’m keeping the words in a row where I can see them.']]);
    }
    if (key === 'finn') {
      if (!F.seen.finn) { F.seen.finn = true;
        return D([
          ['finn:hollow', 'Can’t recall my own name, friend. Hands still know the knots, though. Funny what stays.'],
          ['cole', 'Finn. You’re Finn.'],
          ['finn', '…Finn. Huh. Short. I like it.'],
          ['finn:puzzled', 'Tell you one thing for your book, mapmaker: the fish stopped circlin’. The very moment it happened. Like they’d been countin’ down to it.'],
          ['june', 'Fish don’t count.'],
          ['finn', 'Didn’t think so either. This morning I was wrong about a lot of things.'],
        ]);
      }
      return D([['finn', 'Finn. Still short. Still like it.']]);
    }
    if (key === 'mara' || key === 'pip') {
      if (!F.seen.mara) { F.seen.mara = true;
        return D([
          ['pip', 'Tell her. TELL her!'],
          ['cole', 'Mara. This is Pip. Your son. Seven years old. You waited out a snowstorm at the pass for him to be born.'],
          ['mara:distressed', 'I believe you. That is the worst of it — I believe every word, and it lands like a fact about a stranger.'],
          ['pip:scared', '…You held my hand. TONIGHT. You said I’d remember tonight forever.'],
          ['june', 'Pip. Look at me. I saw her holding your hand — an hour ago, by the stall.'],
          ['june:determined', 'I’m a mapmaker. I keep records of true things. And I am telling you: it is TRUE. It happened. I have it.'],
          ['pip', '…Is it in ink?'],
          ['june', 'It is now.'],
          ['mara:distressed', 'Whoever you two are — whatever you still carry — do not waste it. Please.'],
        ]);
      }
      return D([
        ['pip:happy', 'I’m teaching her me again. We started with my name and the good stick I found in spring.'],
        ['mara', 'It is a very good stick. I have decided to believe in the stick.'],
      ]);
    }
    if (key === 'mochi') {
      if (!F.seen.mochi) { F.seen.mochi = true;
        return D([
          ['june:surprised', 'The cat. The cat is FINE?!'],
          ['mochi', '(Mochi is purring. Mochi has, if anything, improved.)'],
          ['cole', 'Cats don’t keep their memories where moths can reach. My grandmother used to say that.'],
          ['june', 'Your grandmother said that. Casually. As common knowledge.'],
          ['cole', 'She said a lot of things. She was a lamplighter too.'],
        ]);
      }
      return D([['mochi', 'Mrrrrp. (He is watching the north road. He does not usually watch anything.)']]);
    }
  },

  /* ================= cutscenes ================= */
  playJuneIntro(june) {
    this.flags.juneIntro = true;
    Cutscene.play([
      { banner: { title: '— JUNE —', sub: 'a mapmaker with someone else’s dreams', dur: 5 } },
      { cam: { x: 300, y: 620, viewH: 460 } },
      { wait: 1.2 },
      { narrate: 'On the last night of autumn, a mapmaker walked into a valley that was not on her maps — following a road she had only ever seen with her eyes closed.' },
      { camRelease: true },
    ]);
  },

  playWaystone(june) {
    this.flags.waystone = true;
    const mochi = this.npcs.mochi;
    Cutscene.play([
      { cam: { x: 620, y: 470, viewH: 440 } },
      { move: { ent: june, x: 470, y: 540, speed: 120 } },
      { face: { ent: june, dir: 'right' } },
      { say: ['june', '(A waystone. Grey cap. Moss on the north face. A crack running through the E of EMBERBROOK like a river.)'] },
      { say: ['june:worried', '(It’s the one from drawing forty-one. Line for line. Which is impossible — I drew it eleven days ago, four hundred miles from here, asleep.)'] },
      { run: () => { mochi.hidden = false; mochi.x = 660; mochi.y = 580; mochi.dir = 'left'; } },
      { wait: 0.6 },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['june', 'GAH— …a cat. Hello. You are not in my records.'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['june', '(The cat has decided something about me. I am choosing to find that flattering.)'] },
      { run: () => { mochi.follow = 'june'; } },
      { toast: { text: '✦ A cat is following June', color: '#d9a441' } },
      { camRelease: true },
    ]);
  },

  playJuneOutro(june) {
    this.flags.juneDone = true;
    Cutscene.play([
      { narrate: 'The mapmaker bought a third honeybun she had no intention of admitting to, and waited for the lamps.' },
      { run: () => {
          june.x = 445; june.y = 590; june.dir = 'up';
          const mochi = this.npcs.mochi;
          mochi.scene = 'square'; mochi.x = 408; mochi.y = 605;
        } },
      { fadeTo: 1 },
      { wait: 1.0 },
      { banner: { title: '— COLE —', sub: 'the last lamplighter of Emberbrook', dur: 5 } },
      { run: () => { this.setPhase('cole'); } },
      { waitFor: () => window.players.some(p => p && p.role === 'cole') },
      { run: () => {
          const cole = window.players.find(p => p && p.role === 'cole');
          const sp = this.spawnFor('cole');
          cole.scene = sp.scene; cole.x = sp.x; cole.y = sp.y; cole.dir = sp.dir; cole.hidden = false;
        } },
      { fadeTo: 0 },
      { wait: 0.6 },
    ]);
  },

  playColeIntro(cole) {
    this.flags.coleIntro = true;
    Cutscene.play([
      { cam: { x: 700, y: 480, viewH: 600 } },
      { narrate: 'The same evening, on the other side of the village: the last lamplighter of Emberbrook rose from his grandmother’s table, and took down his grandmother’s flame.' },
      { move: { ent: cole, x: 620, y: 640, speed: 160 } },
      { face: { ent: cole, dir: 'up' } },
      { say: ['cole', '(A year tonight since she set the lighter down and didn’t pick it up again. Forty years she carried it. It has never once gone out.)'] },
      { say: ['cole', '(She used to say it wasn’t hers to put out. I used to think that was a saying.)'] },
      { say: ['cole', '(Three lamps left before the Kindling Hour. Best go and mean it.)'] },
      { camRelease: true },
    ]);
  },

  playMeet(players) {
    const june = players.find(p => p && p.role === 'june');
    const cole = players.find(p => p && p.role === 'cole');
    const rowan = this.npcs.rowan;
    this.flags.met = true;
    this.setPhase('together');
    Cutscene.play([
      { run: () => { Net.send({ type: 'buzz', ms: 80 }); june.parked = false; june.scene = 'square'; } },
      { move: { ent: june, x: cole.x + 55, y: cole.y, speed: 150 } },
      { face: { ent: cole, dir: 'right' } }, { face: { ent: june, dir: 'left' } },
      { cam: { x: cole.x + 28, y: cole.y - 30, viewH: 400 } },
      { say: ['june:happy', 'Excuse me. You look official — you’re holding fire. Are you the lamplighter, or do I keep collecting cats until one talks?'] },
      { say: ['cole:worried', 'Oh. Um. Yes? The first one. Cole. The cats don’t talk, to my knowledge.'] },
      { say: ['june', 'June. Mapmaker. Your elder says the Old Gate is your family’s business, and I need it open.'] },
      { say: ['cole', 'The— nobody crosses the Gate. It hasn’t opened in my lifetime. Why would anyone want—'] },
      { say: ['june', 'Because this valley is not on any chart I own. And I walked here anyway — on a road I only know from dreams.'] },
      { say: ['june:determined', 'Something on the other side of that gate has been sending me MAIL, Cole. I intend to answer it in person.'] },
      { say: ['cole:worried', '…what?'] },
      { say: ['rowan', 'THE HOUR! Gather, gather! Neighbors, to the square! Cole — the flame!'] },
      { camRelease: true },
      { run: () => this.playKindlingHour(players) },
    ]);
  },

  playKindlingHour(players) {
    const { rowan, poppy, mara, pip } = this.npcs;
    const june = players.find(p => p && p.role === 'june');
    const cole = players.find(p => p && p.role === 'cole');
    const F = this.flags;
    const hl = { x: 672, y: 470 };
    const sq = Field.scenes.square;

    const lampsOut = [];
    for (const l of sq.lamps) lampsOut.push({ run: () => { l.lit = false; } }, { wait: 0.3 });

    Cutscene.play([
      { move: { ent: rowan, x: 595, y: 555, speed: 110 } },
      { run: () => { poppy.x = 585; poppy.y = 605; poppy.dir = 'up'; } },
      { run: () => { mara.x = 748; mara.y = 612; mara.dir = 'up'; pip.x = 782; pip.y = 600; pip.dir = 'up'; pip.moving = false; } },
      { run: () => { june.x = 612; june.y = 645; june.dir = 'up'; cole.x = 700; cole.y = 648; cole.dir = 'up'; } },
      { cam: { x: 672, y: 520, viewH: 500 } },
      { wait: 0.8 },
      { say: ['rowan:happy', 'Neighbors! The year turns!'] },
      { say: ['rowan', 'Three hundred years, and every one of them alive — right here. Every wedding. Every argument. Every good loaf and bad winter.'] },
      { say: ['rowan', 'What we tell the flame, the flame keeps.'] },
      { say: ['rowan', 'So bring your year, neighbors — the good and the bad of it. Let the flame hold it safe, where no winter can wear it thin.'] },
      { say: ['rowan', 'Who brings the first memory?'] },
      { say: ['poppy:laughing', 'The flood! The spring flood — the whole town in my bakery, bailing water with soup pots, and LAUGHING, gods help us—'] },
      { wait: 1.0 },

      { mood: 'silence' },
      { wait: 1.6 },
      { say: ['pip:scared', '…Why did the music stop?'] },
      { flash: 1.4 }, { shake: 4 },
      { run: () => {
          Field.setSceneState('square', 'gray');
          Particles.burst(46, () => ({ kind: 'shard', x: hl.x + (Math.random() - 0.5) * 20, y: hl.y - 60, vy: -40 - Math.random() * 60, life: 3.2, seed: Math.random() * 9 }));
          Particles.burst(30, () => ({ kind: 'moth', x: hl.x + (Math.random() - 0.5) * 30, y: hl.y - 50, vx: (Math.random() - 0.5) * 40, vy: -14, life: 6, seed: Math.random() * 9 }));
          AudioSys.hushSting();
          Net.send({ type: 'buzz', ms: 500 });
        } },
      { wait: 1.4 },
      ...lampsOut,
      { run: () => { FX.desatTarget = 0.2; } },
      { wait: 1.0 },
      { narrate: 'It did not happen slowly. Between one heartbeat and the next, the light of Emberbrook — three hundred years of it — stood up and left.' },
      { run: () => Particles.burst(16, () => ({ kind: 'moth', x: 672 + (Math.random() - 0.5) * 300, y: 480 + (Math.random() - 0.5) * 160, vx: 0, vy: -8, life: 7, seed: Math.random() * 9 })) },

      { say: ['poppy:hollow', '…Why am I holding bread? Whose stall is this?'] },
      { say: ['pip', 'Mama?'] },
      { say: ['mara:distressed', '…I’m sorry — whose child is this? Where is— I don’t— someone’s crying. Why is someone crying?'] },
      { say: ['pip:scared', 'MAMA. It’s me. It’s Pip. You KNOW me!'] },
      { say: ['rowan:grave', 'Everyone stay where you are. Names! Say your names, out loud — say them NOW.'] },
      { wait: 1.4 },
      { say: ['rowan:hollow', '…I’ll start. I am… '] },
      { wait: 1.8 },
      { say: ['rowan', '…I keep the ledger. I know that I keep the ledger.'] },
      { say: ['cole:worried', 'Rowan. Your name is Rowan.'] },
      { say: ['june:worried', '…You know them? All of them?'] },
      { say: ['cole', 'Every window in this village. Every name behind it. Why do I still— why do WE still—'] },
      { move: { ent: rowan, x: 652, y: 608, speed: 90 } },
      { say: ['rowan:grave', 'You two. The stranger and the lamplighter. Everyone in this square is a stranger wearing a neighbor’s face — except you.'] },
      { say: ['rowan', 'Why do YOU still hold your names?'] },
      { say: ['june', 'I got here an HOUR ago.'] },
      { say: ['cole:determined', '…My lighter’s still warm. Every other flame in Emberbrook just died. Not this one.'] },
      { say: ['rowan:grave', 'Then we are not finished. Not yet.'] },
      { say: ['rowan', 'See to them — all of them. They deserve their names back, even borrowed. Then come find me… while my ledger still says anything at all.'] },
      { banner: { title: 'The Hush has come to Emberbrook', sub: 'the village forgets itself', dur: 5 } },
      { mood: 'hush' },
      { run: () => {
          F.hushDone = true;
          const finn = this.npcs.finn;
          finn.scene = 'square'; finn.x = 450; finn.y = 615; finn.dir = 'right';
          // everyone drifts back to their posts, hollowed
          rowan.x = 790; rowan.y = 565; rowan.dir = 'left';
          poppy.x = 438; poppy.y = 598; poppy.dir = 'left';
          mara.x = 985; mara.y = 655; mara.dir = 'left';
          pip.x = 945; pip.y = 672; pip.dir = 'left';
          Net.send({ type: 'buzz', ms: 200 });
        } },
    ]);
  },

  playPact(p) {
    const { rowan, mochi } = this.npcs;
    const players = window.players;
    const june = players.find(q => q && q.role === 'june');
    const cole = players.find(q => q && q.role === 'cole');
    if (!june || !cole) {
      Dialog.start([{ who: 'rowan', text: 'Both of you. This concerns the mapmaker AND the lamplighter — I’ll not say it twice.' }]);
      return;
    }
    Cutscene.play([
      { run: () => { june.x = 600; june.y = 600; june.dir = 'right'; cole.x = 692; cole.y = 605; cole.dir = 'left'; } },
      { move: { ent: rowan, x: 760, y: 585, speed: 90 } },
      { face: { ent: rowan, dir: 'left' } },
      { cam: { x: 672, y: 545, viewH: 440 } },
      { say: ['rowan:grave', 'Look at this. This morning, this page held the year four-twenty-nine. The flood. A wedding — someone’s wedding, the ink is going as I hold it.'] },
      { say: ['rowan', 'Ink outlasts minds. It will not outlast whatever THAT was. When this book goes blank, Emberbrook never happened.'] },
      { say: ['june', 'It won’t.'] },
      { say: ['june:worried', '…I don’t know why I said that with such confidence. Ignore me.'] },
      { say: ['rowan', 'No. Hold on to that, girl; we will need it.'] },
      { say: ['rowan', 'Now — our flame was first drawn from a shrine deep in the Whisperwood. The Kindling. Every Heartlight in every valley is a child of that fire.'] },
      { say: ['cole', 'Nobody knows the way. The Gate’s been shut three hundred years. The road’s gone.'] },
      { say: ['june:worried', '…I need to show you both something, and I need you to not be strange about it.'] },
      { say: ['june', 'Since I was six years old, I have drawn one clearing. Over and over. In dreams. Forty-one drawings of the same clearing.'] },
      { say: ['june', 'I came here because the forty-first had YOUR gate in the corner.'] },
      { say: ['rowan:grave', 'Girl… that is the Kindling. That is the heart of the Whisperwood.'] },
      { say: ['june', 'I have never BEEN there.'] },
      { say: ['rowan', 'No. It has been CALLING you. Forty-one times it called.'] },
      { say: ['rowan', 'And tonight of all nights, it made sure a mapmaker with the road in her head stood in our square — beside the last living flame in the valley.'] },
      { say: ['rowan', 'The map does not know fire. The flame does not know the way. Alone, each of you is a curiosity. Together, you are a rescue.'] },
      { say: ['june', 'We met an hour ago.'] },
      { say: ['rowan:happy', 'Then you have an hour’s head start on resenting each other. Marvelous. The sigils will want more than acquaintance, mind.'] },
      { toast: { text: '✦ June carries the Dream Charts', color: '#4f9f92' } },
      { wait: 0.6 },
      { toast: { text: '✦ Cole carries the Last Spark', color: '#e0a94e' } },
      { say: ['rowan', 'The old rite, then. Two keepers, one flame. Say it and mean it, or the Gate will know the difference:'] },
      { say: ['rowan', '“What they forgot, we keep. What we keep, we return.”'] },
      { bothHold: { prompt: 'HOLD  A — swear it together', dur: 2.2 } },
      { flash: 0.7 },
      { run: () => {
          AudioSys.pact();
          Net.send({ type: 'buzz', ms: 400 });
          Particles.burst(20, () => ({ kind: 'sparkle', x: 646 + (Math.random() - 0.5) * 80, y: 585 - Math.random() * 40, vy: -12, life: 1.4 }));
        } },
      { wait: 0.8 },
      { move: { ent: mochi, x: 640, y: 640, speed: 170 } },
      { say: ['rowan:happy', '…The cat is going with you.'] },
      { say: ['cole', 'He’s not my—'] },
      { say: ['rowan', 'It was not a question, boy. Some decisions are made over our heads. That one has been watching the north road all evening, and I suggest you take the hint.'] },
      { run: () => { mochi.follow = 'party'; } },
      { toast: { text: '✦  Mochi joined the party  ✦', color: '#d9a441' } },
      { banner: { title: '✦ Quest — The Long Rekindling ✦', sub: 'Carry the Last Spark to the Kindling, deep in the Whisperwood', dur: 6 } },
      { mood: 'resolve' },
      { run: () => { this.flags.pactDone = true; Field.scenes.gate.platesActive = true; } },
      { say: ['rowan', 'Twin sigils, before the Gate. The Lamplighters cut them, in the old days — that road was always meant to be walked by two.'] },
    ]);
  },

  /* ================= dev checkpoints (keys 1–7) ================= */
  CHECKPOINT_NAMES: ['', 'June: forest start', 'June: village square', 'Cole: cottage start',
    'the meet (lamps done)', 'aftermath (post-Hush)', 'the sigils (pact done)', 'gate: finale ready'],
  applyCheckpoint(n) {
    if (n === 1) { location.reload(); return; }
    const F = this.flags;
    // clear any running story UI
    Dialog.lines = null;
    Cutscene.active = false; Cutscene.steps = null; Cutscene.holdJob = null; Cutscene.waitFn = null; Cutscene.moveJob = null;
    Camera.target = null; FX.letterboxTarget = 0; FX.fadeTarget = 0;
    // ensure both keepers exist (keyboard-claimed if needed)
    if (!window.players.find(p => p && p.role === 'june')) {
      const slot = window.players.findIndex(p => p === null);
      if (slot !== -1) window.players[slot] = makePlayer('june', 'kb1', true);
    }
    if (!window.players.find(p => p && p.role === 'cole')) {
      const slot = window.players.findIndex(p => p === null);
      if (slot !== -1) window.players[slot] = makePlayer('cole', 'kb2', true);
    }
    const j = window.players.find(p => p && p.role === 'june');
    const c = window.players.find(p => p && p.role === 'cole');
    const N = this.npcs;
    const place = (e, scene, x, y, dir) => { e.scene = scene; e.x = x; e.y = y; if (dir) e.dir = dir; };
    const setLamps = (lit) => {
      Field.scenes.lane.lamps.forEach(l => { if (l.id) l.lit = lit; });
      Field.scenes.square.lamps.forEach(l => { l.lit = lit || !l.id; });
    };
    const npcPosts = (postHush) => {
      place(N.rowan, 'square', 790, 565, 'left');
      place(N.poppy, 'square', 438, 598, 'left');
      place(N.mara, 'square', 985, 655, 'left');
      place(N.pip, 'square', 945, 672, 'left');
      place(N.finn, postHush ? 'square' : 'lane', postHush ? 450 : 890, postHush ? 655 : 500, postHush ? 'right' : 'down');
    };
    // base state
    Object.assign(F, { juneIntro: true, waystone: true, leftForest: true, juneTalked: {}, juneDone: false, coleIntro: false,
      lampsLit: 0, met: false, hushDone: false, seen: {}, pactDone: false, gateOpen: false,
      ended: false, endT: 0, endingStarted: false });
    Field.setSceneState('square', 'festival');
    Field.setSceneState('gate', 'gray');
    Field.scenes.gate.platesActive = false;
    Field.scenes.gate.plates.forEach(pl => pl.hold = 0);
    const gt = Field.scenes.gate;
    gt.open = false;
    FX.desatTarget = 0;
    npcPosts(false);
    N.mochi.hidden = false; N.mochi.follow = 'june';
    N.stranger.hidden = true;
    j.parked = false; c.hidden = false;

    if (n === 2) {
      this.phase = 'june';
      place(j, 'square', 600, 630, 'up'); place(N.mochi, 'square', 560, 645);
      c.hidden = true; place(c, 'interior', 880, 590, 'down');
      AudioSys.setMood('festival');
    }
    if (n === 3) {
      F.juneTalked = { poppy: true, mara: true }; F.juneDone = true;
      this.phase = 'cole';
      j.parked = true; place(j, 'square', 445, 590, 'up'); place(N.mochi, 'square', 408, 605);
      place(c, 'interior', 880, 590, 'down');   // coleIntro will auto-play
      AudioSys.setMood('festival');
    }
    if (n === 4) {
      F.juneTalked = { poppy: true, mara: true }; F.juneDone = true; F.coleIntro = true;
      F.lampsLit = 3; setLamps(true);
      this.phase = 'cole';
      j.parked = true; place(j, 'square', 445, 590, 'up'); place(N.mochi, 'square', 408, 605);
      place(c, 'square', 900, 520, 'left');     // the meet auto-triggers
      AudioSys.setMood('festival');
    }
    if (n >= 5) {
      F.juneTalked = { poppy: true, mara: true }; F.juneDone = true; F.coleIntro = true;
      F.lampsLit = 3; setLamps(false);
      F.met = true; F.hushDone = true;
      this.phase = 'together';
      Field.setSceneState('square', 'gray');
      FX.desatTarget = 0.2;
      npcPosts(true);
      place(j, 'square', 612, 645, 'up'); place(c, 'square', 700, 648, 'up');
      place(N.mochi, 'square', 560, 660);
      AudioSys.setMood('hush');
    }
    if (n >= 6) {
      F.seen = { poppy: true, finn: true, mara: true, mochi: true };
      F.pactDone = true;
      Field.scenes.gate.platesActive = true;
      N.mochi.follow = 'party';
      AudioSys.setMood('resolve');
    }
    if (n === 7) {
      place(j, 'gate', 600, 660, 'up'); place(c, 'gate', 744, 660, 'up');
      place(N.mochi, 'gate', 672, 700);
    }
    const scene = this.activeRoles().includes('june') && !j.parked ? j.scene : c.scene;
    Field.enter(scene);
    Field.cam.x = (this.phase === 'cole' ? c : j).x;
    Field.cam.y = (this.phase === 'cole' ? c : j).y;
    this.setPhase(this.phase);
    Toasts.add('⚑ checkpoint — ' + this.CHECKPOINT_NAMES[n], '#8fb0c9');
  },

  playEnding(players) {
    const F = this.flags;
    const june = players.find(p => p && p.role === 'june');
    const cole = players.find(p => p && p.role === 'cole');
    const stranger = this.npcs.stranger;
    const mochi = this.npcs.mochi;
    F.endingStarted = true;
    Cutscene.play([
      { run: () => { june.dir = 'up'; cole.dir = 'up'; } },
      { cam: { x: 672, y: 330, viewH: 480 } },
      { narrate: 'Beyond the Old Gate, the road ran grey — soft and wrong, like snow that refused to melt.' },
      { run: () => Particles.burst(60, () => ({
          kind: 'moth', seed: Math.random() * 9, life: 8,
          x: 600 + Math.random() * 160, y: 180 + Math.random() * 160,
          vx: (Math.random() - 0.5) * 24, vy: -16 - Math.random() * 22,
        })) },
      { shake: 1.5 },
      { say: ['june', '…Moths. The whole road is moths.'] },
      { say: ['cole', 'That’s where the light went. Some of it never made it to the sky.'] },
      { run: () => { stranger.hidden = false; stranger.x = 672; stranger.y = 300; stranger.dir = 'down'; } },
      { wait: 1.2 },
      { run: () => { mochi.scene = 'gate'; mochi.x = (june.x + cole.x) / 2; mochi.y = Math.min(june.y, cole.y) + 20; mochi.dir = 'left'; } },
      { say: ['mochi', 'HHHHssss.'] },
      { say: ['june', 'He’s never done that.'] },
      { say: ['cole', 'He’s not my— …no. No, he’s never done that.'] },
      { say: ['june', 'Cole. His lantern. It isn’t dark — it’s FULL.'] },
      { wait: 1.4 },
      { narrate: 'The figure bowed — unhurried, and courteous, the way a debt collector is courteous — and was gone between one blink and the next.' },
      { run: () => { stranger.hidden = true; } },
      { say: ['cole', '…It bowed to me.'] },
      { say: ['june', 'It bowed to your LIGHTER, I think. New rule, partner: neither of us sleeps until we’re back inside a wall.'] },
      { narrate: 'The Order of Lamplighters kept one creed: light does not die — it is only ever carried. Someone is carrying Emberbrook away.' },
      { mood: 'silence' },
      { run: () => {
          F.ended = true;
          AudioSys.finale();
          Net.send({ type: 'end' });
        } },
    ]);
  },
};
