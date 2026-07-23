'use strict';
/* ============================================================
   CHAPTER ONE — "Emberwake"  (painted scene edition)

   Act I   — VESPER: a forest road with no name, a waystone from
             a dream, and a village that isn't on any map.
   Act II  — LAKE: a cottage with one warm flame, and the last
             lamplighter's rounds on festival night.
   Act III — the Kindling Hour, the Hush, and what two strangers
             still hold when a village forgets itself.
   ============================================================ */

const Chapter1 = {
  phase: 'vesper',                    // 'vesper' | 'lake' | 'together'
  flags: {
    vesperIntro: false, waystone: false, vesperTalked: {}, vesperDone: false,
    lakeIntro: false, lampsLit: 0,
    met: false, hushDone: false, seen: {},
    pactDone: false, gateOpen: false, ended: false, endT: 0,
    endingStarted: false,
  },
  npcs: {}, entities: [],

  activeRoles() {
    return this.phase === 'vesper' ? ['vesper'] : this.phase === 'lake' ? ['lake'] : ['vesper', 'lake'];
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
        maskSrc: 'assets/scenes/forest/mask.png',
        viewH: 700, charH: 120, speed: 190, fireflies: true,
        tints: { festival: '#9fa8c9' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        exits: [{ zone: { x: 1170, y: 30, w: 174, h: 320 }, to: 'entrance', spawn: [280, 660, 'right'] }],
      },
      entrance: {
        states: { festival: 'assets/scenes/entrance/main.png' }, state: 'festival',
        maskSrc: 'assets/scenes/entrance/mask.png',
        viewH: 700, charH: 125, speed: 190,
        tints: { festival: '#d9b18c' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        exits: [
          { zone: { x: 1150, y: 300, w: 194, h: 400 }, to: 'square', spawn: [672, 675, 'up'] },
          { zone: { x: 100, y: 620, w: 120, h: 148 }, to: 'forest', spawn: [1080, 120, 'left'] },
        ],
      },
      interior: {
        states: { festival: 'assets/scenes/interior/main.png' }, state: 'festival',
        maskSrc: 'assets/scenes/interior/mask.png',
        viewH: 725, charH: 215, speed: 290,   // capped: backdrop is 1344x768; higher letterboxes (width binds at wide aspects)
        tints: { festival: '#f2c091' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        exits: [{ zone: { x: 380, y: 560, w: 90, h: 150 }, to: 'lane', spawn: [400, 505, 'down'] }],
      },
      lane: {
        states: { festival: 'assets/scenes/lane/main.png' }, state: 'festival',
        maskSrc: 'assets/scenes/lane/mask.png',
        viewH: 730, charH: 130, speed: 200,
        tints: { festival: '#b8b4c9' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        blocked: [],
        lamps: [{ x: 908, y: 255, lit: false, id: 'lamp1', base: [905, 430] }],
        exits: [
          { zone: { x: 300, y: 385, w: 80, h: 55 }, to: 'interior', spawn: [500, 630, 'up'] },
          { zone: { x: 1200, y: 90, w: 144, h: 380 }, to: 'square', spawn: [120, 390, 'right'] },
        ],
      },
      square: {
        // pipeline scene: candidate C + north road, baked bitmap mask, keyed cutout occluders
        states: { festival: 'assets/scenes/square/festival.png', gray: 'assets/scenes/square/gray.png' }, state: 'festival',
        maskSrc: 'assets/scenes/square/mask.png',
        viewH: 730, charH: 125, speed: 190, mothAmbience: true,
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
            deniedLine: ['vesper', 'The south road can wait. Something is happening HERE.'] },
          { zone: { x: 0, y: 590, w: 70, h: 178 }, to: 'lane', spawn: [1250, 380, 'left'],
            enabled: () => Chapter1.phase !== 'vesper' && !Chapter1.flags.hushDone,
            deniedLine: ['lake', 'Lane’s dark and empty. Everyone’s in the square tonight.'] },
          { zone: { x: 630, y: 0, w: 190, h: 110 }, to: 'gate', spawn: [672, 660, 'up'],
            enabled: () => Chapter1.flags.pactDone,
            deniedLine: ['lake', 'The Old Gate. Nobody goes that way… it’s been shut my whole life.'] },
        ],
      },
      gate: {
        states: { gray: 'assets/scenes/gate/gray.png', open: 'assets/scenes/gate/open.png' }, state: 'gray',
        maskSrc: 'assets/scenes/gate/mask.png',
        viewH: 730, charH: 125, speed: 190, mothAmbience: true,
        tints: { gray: '#9aa3b5', open: '#9aa3b5' },
        walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
        archBlock: { x: 570, y: 250, w: 200, h: 190 },      // walkable only once state==='open'
        blocked: [],
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
    N('rowan', 'square', 790, 565, 'left', 130);
    N('poppy', 'square', 438, 598, 'left', 115);
    N('mara', 'square', 985, 655, 'left', 120);
    N('pip', 'square', 945, 672, 'left', 70);
    N('finn', 'lane', 890, 500, 'down', 130);
    const mochi = N('mochi', 'entrance', 640, 560, 'left', 48);
    mochi.hidden = true; mochi.follow = null;
    const stranger = N('stranger', 'gate', 672, 310, 'down', 145);
    stranger.hidden = true;

    AudioSys.setMood('forest');   // Vesper's act opens in the old forest
  },

  spawnFor(role) {
    return role === 'vesper'
      ? { scene: 'forest', x: 120, y: 690, dir: 'right' }
      : { scene: 'interior', x: 880, y: 590, dir: 'down' };
  },

  /* music keys off the current scene, filtered by story state.
     Returns null for scenes with no opinion (keep whatever is playing). */
  moodFor(sceneKey) {
    const F = this.flags;
    switch (sceneKey) {
      case 'forest': case 'entrance':
        return 'forest';                 // forest holds until actually inside the village
      case 'square': case 'lane': case 'interior':
        return F.hushDone ? (F.pactDone ? 'resolve' : 'hush') : 'festival';
      case 'gate':
        return F.pactDone ? 'resolve' : 'hush';
      default:
        return null;
    }
  },

  /* ================= per-frame ================= */
  update(dt, players) {
    const F = this.flags;
    // scene-keyed music: re-evaluate the mood only when the viewed scene changes,
    // so cutscene/checkpoint setMood calls stay authoritative while in-scene
    if (Field.currentKey !== this._moodScene) {
      if (!Cutscene.active && !F.ended) {
        const m = this.moodFor(Field.currentKey);
        // compare resolved keys so we never restart the same tune (setMood resets step)
        if (m && (AudioSys.ALIAS[m] || m) !== AudioSys.mood) AudioSys.setMood(m);
      }
      this._moodScene = Field.currentKey;
    }
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');

    if (lake) lake.hidden = this.phase === 'vesper';
    if (vesper) vesper.parked = this.phase === 'lake';

    // Act I triggers
    if (this.phase === 'vesper' && vesper && !F.vesperIntro && !Cutscene.active) this.playVesperIntro(vesper);
    if (this.phase === 'vesper' && vesper && F.vesperIntro && !F.waystone &&
        vesper.scene === 'entrance' && vesper.x > 400 && !Cutscene.active)
      this.playWaystone(vesper);

    // Act II triggers
    if (this.phase === 'lake' && lake && !F.lakeIntro && !Cutscene.active && !Dialog.active())
      this.playLakeIntro(lake);
    if (this.phase === 'lake' && !F.met && F.lampsLit >= 3 && vesper && lake &&
        lake.scene === 'square' && !Cutscene.active && !Dialog.active())
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
      if (mochi.follow === 'vesper' && vesper && !vesper.parked) target = vesper;
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
        if (d > 240) { mochi.x = tx; mochi.y = ty; mochi.moving = false; } // wedged/far: snap to rest
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
      if (all && vesper && lake) {
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
        vesper && lake && vesper.scene === 'gate' && lake.scene === 'gate' &&
        vesper.y < 430 && lake.y < 430 && vesper.x > 560 && vesper.x < 790 && lake.x > 560 && lake.x < 790) {
      this.playEnding(players);
    }
    if (F.ended) F.endT += dt;
  },

  objective() {
    const F = this.flags;
    if (F.ended) return '';
    if (this.phase === 'vesper') {
      if (!F.waystone) return 'Follow the road';
      const n = Object.keys(F.vesperTalked).length;
      if (!F.vesperDone) {
        if (n < 2) return `Emberwake — meet the villagers (${n}/2)`;
        return 'Find whoever is in charge — the elder, by the glowing crystal';
      }
      return '';
    }
    if (this.phase === 'lake') {
      if (!F.lakeIntro) return '';
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

  /* markers — hooks read by main.js drawMarkers */
  lampHintActive() {
    const F = this.flags;
    return !F.hushDone && F.lakeIntro && F.lampsLit < 3;
  },
  storyMarker() {
    const F = this.flags;
    const rowanBeat =
      (this.phase === 'vesper' && Object.keys(F.vesperTalked).length >= 2 && !F.vesperDone) ||
      (F.hushDone && !F.pactDone && Object.keys(F.seen).length >= 4);
    if (rowanBeat && Field.currentKey === 'square') {
      const r = this.npcs.rowan;
      return { x: r.x, y: r.y - r.h - 18 };
    }
    return null;
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
    if (p.role === 'lake') {
      const s = Field.scenes[p.scene];
      for (const l of (s.lamps || [])) if (!l.lit && l.id) consider(l.base[0], l.base[1], { kind: 'lamp', lamp: l });
    }
    if (p.scene === 'entrance') consider(570, 560, { kind: 'waystone' }, 85);
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
      Dialog.start(alive ? [
        { who: 'system', text: 'The Heartlight of Emberbrook. Every street lamp in the village is lit from this one flame.' },
        { who: 'system', text: 'Three hundred years of the village’s heart, warm inside it — given over and shone back. It hums, very faintly, like a kettle two rooms away.' },
      ] : [
        { who: 'system', text: 'What is left of the Heartlight. It does not hum. It does not do anything.' },
        { who: 'system', text: 'Holding a hand near it feels like reading a love letter meant for somebody else.' },
      ]);
    }
    if (t.kind === 'notice') {
      Dialog.start(this.flags.hushDone ? [
        { who: 'system', text: 'The notice board. Everyone can still read every word. The words have just stopped mattering to anyone but you two.' },
        { who: 'system', text: 'One notice reads: "LOST — brown dog, answers to Biscuit."' },
      ] : [
        { who: 'system', text: 'The notice board. "EMBERWAKE TONIGHT — bring a memory worth keeping. And a chair. We are short of chairs."' },
      ]);
    }
    if (t.kind === 'waystone') {
      Dialog.start([{ who: 'system', text: p.role === 'vesper'
        ? 'The waystone from drawing forty-one. She has stopped checking whether it matches. It matches.'
        : 'The old waystone, watching the road since before the village had a name. Somebody has recently brushed the moss from its eyes.' }]);
    }
    if (t.kind === 'hearth') {
      Dialog.start([
        { who: 'system', text: 'The hearth. Grandmother’s portrait watches from above the mantel — dusted daily, and the eyes still miss nothing.' },
        { who: 'system', text: 'Beneath it, an empty brass hook, worn bright. The lighter’s place, between rounds.' },
      ]);
    }
  },

  lightLamp(lamp, p) {
    lamp.lit = true;
    this.flags.lampsLit++;
    AudioSys.lampOn();
    Net.send({ type: 'buzz', ms: 60 });
    Particles.burst(8, () => ({ kind: 'sparkle', x: lamp.x + (Math.random() - 0.5) * 16, y: lamp.y + (Math.random() - 0.5) * 12, vy: -8, life: 0.8 }));
    if (this.flags.lampsLit === 1)
      Dialog.start([
        { who: 'lake', text: '(One. The wick takes the flame like it remembers it — Grandmother swore they do.)' },
        { who: 'lake', text: '(While this lamp burns, every house on the lane sits inside the village’s heart. Dark lamp, dull street.)' },
      ]);
    if (this.flags.lampsLit === 2)
      Dialog.start([
        { who: 'lake', text: '(Two. “Light them like you mean it,” she said, “or they gutter by midnight.”)' },
        { who: 'lake', text: '(She never once explained what the meaning involved. I improvise.)' },
      ]);
    if (this.flags.lampsLit === 3)
      Dialog.start([
        { who: 'lake', text: '(Three. The ring is closed before full dark, same as every night of my life.)' },
        { who: 'lake', text: '(A lit lamp near every door. Wherever you sleep in Emberbrook tonight, you sleep inside the warmth.)' },
      ]);
  },

  /* ================= dialogue ================= */
  talkTo(key, ent, p) {
    const F = this.flags;
    const dx = p.x - ent.x, dy = p.y - ent.y;
    if (key !== 'mochi') ent.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    const isVesper = p.role === 'vesper';
    const D = (lines, onFinish) => Dialog.start(lines.map(l => ({ who: l[0], text: l[1] })), onFinish);

    if (!F.hushDone) {
      if (key === 'rowan') {
        if (isVesper) {
          if (Object.keys(F.vesperTalked).length < 2) return D([
            ['rowan', 'A guest! Guests eat first, my dear — that is LAW on Emberwake, ask the baker. Come back fed and greeted.'],
          ]);
          return D([
            ['rowan', 'Now then. A guest, on Emberwake of all nights! Nobody finds Emberbrook by accident, my dear.'],
            ['vesper', 'Vesper. Mapmaker. I need to get through your gate, and I’m told you’re in charge.'],
            ['rowan', 'In charge! Ha! I keep the ledger; the village keeps itself.'],
            ['rowan', 'And nobody opens the Old Gate, child. It hasn’t a key. It has RULES.'],
            ['vesper', 'Rules can be charted. Charting things is my whole profession.'],
            ['rowan', '…Ha! I like you. Stay for the Kindling Hour, mapmaker — one hour, the whole village, the year’s best told to the flame.'],
            ['rowan', 'Nobody should walk into the Whisperwood on an empty heart.'],
            ['rowan', 'Three hundred years that flame has burned. In all of them, nobody in this valley has carried a grief alone.'],
            ['rowan', 'That is not boasting, my dear. It is bookkeeping. I checked.'],
            ['rowan', 'As for the Gate — lamplighter business. His order built it, his order shut it. Ask HIM.'],
            ['rowan', 'The quiet one with the flame that never goes out. You’ll find him apologizing to lamps somewhere across the village.'],
          ], () => { if (!F.vesperDone) this.playVesperOutro(p); });
        }
        return D([['rowan', 'Lake! The Kindling Hour will not wait for poetry. Lamps, boy, lamps!']]);
      }
      if (key === 'poppy') {
        if (isVesper) { F.vesperTalked.poppy = true;
          return D([
            ['poppy', 'A new face! Here, take a bun, love. Nobody goes hungry in Emberbrook on Emberwake — that’s not kindness, that’s LAW.'],
            ['vesper', 'I— fine. One. For the record: I’m here to chart the Whisperwood, not to eat pastry.'],
            ['poppy:laughing', 'Chart the— HA! Did you hear her? Eat two.'],
            ['poppy', 'And where’s home for you, love? Everybody’s road starts somewhere.'],
            ['vesper', 'Nowhere, yet. It’s under survey. Ask me again when the survey’s done.'],
            ['vesper', 'My turn for a question. Everyone keeps saying “the Kindling Hour” like I was born knowing what it is.'],
            ['poppy', 'Simplest thing in the world, love. Once a year you bring your best memory and TELL it to the flame.'],
            ['poppy', 'You keep the memory. The flame keeps the warmth of it — and shines it back on every soul in the lamplight, forever.'],
            ['vesper', 'You give your memories. To a fire. On purpose.'],
            ['poppy:happy', 'Give? TELL, love. You lose nothing — you keep every minute. The flame only takes what it meant to you.'],
            ['poppy:happy', 'And it pays that back to all of us, all year. Why do you think nobody here stays angry past sundown?'],
            ['vesper:thinking', '(That warm feeling, ever since the waystone. It isn’t the weather. It’s coming out of the LAMPS.)'],
            ['vesper', '(I ate two. In my defense: eleven days of walking, and they were extraordinary.)'],
          ]);
        }
        return D([
          ['poppy:happy', 'There he is! The one soul allowed to be late tonight — nothing starts till his lamps are lit. Bun?'],
          ['lake', 'On duty, Poppy.'],
          ['poppy', 'Half a bun. I’ll hold the other half hostage until the Kindling Hour.'],
          ['poppy', 'No use asking if YOU’LL make a telling this year. Keeper keeps his own — I know, I know. Strangest rule your family ever kept. Saddest one, too.'],
          ['lake', '(Everyone else gives their year to the flame, and the flame carries it for them. Keepers carry their own.)'],
          ['lake', '(“Someone has to stand outside the kept,” she said. I never asked why.)'],
        ]);
      }
      if (key === 'finn') {
        if (isVesper) F.vesperTalked.finn = true;
        return D([
          ['finn', 'Festival’s up in the square. Fish are down here. I know which conversation I prefer.'],
          ['finn', 'Somethin’s got the pond spooked tonight, though. They’re swimmin’ in a circle. One big circle. All of ’em. Slow.'],
          [isVesper ? 'vesper' : 'lake', isVesper ? 'Fish don’t… do that. Do they?' : 'They ever done that before, Finn?'],
          ['finn', 'Didn’t think so either, this morning.'],
        ]);
      }
      if (key === 'mara' || key === 'pip') {
        if (isVesper) { F.vesperTalked.mara = true;
          return D([
            ['mara', 'Pip, love, stop orbiting the nice stranger.'],
            ['pip', 'Are you a REAL mapmaker? Have you been everywhere?'],
            ['pip', 'Have you been to the MOON?'],
            ['vesper', '…Not yet.'],
            ['pip', 'She’s been to the moon.'],
            ['mara', 'He’ll remember tonight his whole life. Some grown-up Emberwake, he’ll tell it to the flame.'],
            ['mara', 'He’ll keep every minute of it — and the whole village will sleep warmer for his good night. Nights like this are what winters are for.'],
          ]);
        }
        return D([
          ['mara', 'He’s been up since dawn, Lake. He’ll sleep where he falls, and I’ll carry him home like every year.'],
          ['pip', 'I will NOT fall asleep.'],
          ['pip', 'Renn says you can SEE the memories go in. I’m staying awake to check.'],
          ['mara', 'Remember this night, both of you. That’s what it’s for.'],
        ]);
      }
      if (key === 'mochi') return D(isVesper ? [
        ['mochi', 'Mrrp.'],
        ['vesper', 'You’re still here. I don’t feed you. I have never fed you.'],
        ['mochi', 'Mrrp.'],
      ] : [
        ['mochi', '(Mochi is escorting the stranger with the interesting satchel. He acknowledges you, lamplighter, as staff.)'],
      ]);
    }

    /* ---- after the Hush ---- */
    if (key === 'rowan') {
      if (Object.keys(F.seen).length < 4) return D([
        ['rowan', 'See to them first. All of them. They deserve to hear their names from someone who still owns them.'],
        ['rowan', 'I will be here, reading my ledger. The ink is all still there — it is the caring that’s going. Be quick as kindness allows.'],
      ]);
      if (!F.pactDone) return this.playPact(p);
      return D([['rowan', 'Twin sigils, before the Gate. Two keepers, one flame. Walk close, and walk kindly.']]);
    }
    if (key === 'poppy') {
      if (!F.seen.poppy) { F.seen.poppy = true;
        return D([
          ['poppy:hollow', '…My stall. My bread. My hands — I know every burn scar on them. Why does none of it feel like MINE?'],
          ['lake', 'You’re Poppy. You bake. Every morning you burn your thumb on the first tray and swear you won’t tomorrow.'],
          ['poppy', '…Do I do it anyway?'],
          ['lake', 'Every morning.'],
          ['poppy', 'The round warm things. I know the word — it just sounds like nobody’s when I say it. Say it to me, love.'],
          ['vesper', 'Honeybuns.'],
          ['poppy:happy', 'HONEYBUNS. Say more words. Both of you.'],
          ['poppy:happy', 'Anything in this stall, it’s yours — I’m reliably informed it’s mine to give.'],
          ['vesper:thinking', '(Writing it all down. Who they are. Who they are to each other.)'],
          ['vesper:thinking', '(If this ever happens again — there will be a copy of everyone.)'],
        ]);
      }
      return D([['poppy', 'Honeybuns. Poppy. Thumb. I’m keeping the words in a row where I can see them.']]);
    }
    if (key === 'finn') {
      if (!F.seen.finn) { F.seen.finn = true;
        return D([
          ['finn:hollow', 'My name… I can say the word, friend. It just isn’t MINE anymore. Hands still know the knots, though. Funny what stays.'],
          ['lake', 'Finn. You’re Finn.'],
          ['finn', '…Finn. Huh. Short. I like it.'],
          ['finn:puzzled', 'Tell you one thing for your book, mapmaker: the fish stopped circlin’. The very moment it happened. Like they’d been countin’ down to it.'],
          ['vesper', 'Fish don’t count.'],
          ['finn', 'Didn’t think so either. This morning I was wrong about a lot of things.'],
        ]);
      }
      return D([['finn', 'Finn. Still short. Still like it.']]);
    }
    if (key === 'mara' || key === 'pip') {
      if (!F.seen.mara) { F.seen.mara = true;
        return D([
          ['pip', 'Tell her. TELL her!'],
          ['lake', 'Mara. This is Pip. Your son. Seven years old. You waited out a snowstorm at the pass for him to be born.'],
          ['mara:distressed', 'I believe you. That is the worst of it — I believe every word, and it lands like a fact about a stranger.'],
          ['pip:scared', '…You held my hand. TONIGHT. You said I’d remember tonight forever.'],
          ['vesper', 'Pip. Look at me. I saw her holding your hand — an hour ago, by the stall.'],
          ['vesper:determined', 'I’m a mapmaker. I keep records of true things. And I am telling you: it is TRUE. It happened. I have it.'],
          ['pip', '…Is it in ink?'],
          ['vesper', 'It is now.'],
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
          ['vesper:surprised', 'The cat. The cat is FINE?!'],
          ['mochi', '(Mochi is purring. Mochi has, if anything, improved.)'],
          ['lake', 'Cats don’t keep their hearts where moths can reach. My grandmother used to say that.'],
          ['vesper', 'Your grandmother said that. Casually. As common knowledge.'],
          ['lake', 'She said a lot of things. She was a lamplighter too.'],
        ]);
      }
      return D([['mochi', 'Mrrrrp. (He is watching the north road. He does not usually watch anything.)']]);
    }
  },

  /* ================= cutscenes ================= */
  playVesperIntro(vesper) {
    this.flags.vesperIntro = true;
    Cutscene.play([
      { banner: { title: '— VESPER —', sub: 'a mapmaker with someone else’s dreams', dur: 5 } },
      { cam: { x: 300, y: 620, viewH: 460 } },
      { wait: 1.2 },
      { narrate: 'On the last night of autumn, a mapmaker walked into a valley that was not on her maps — following a road she had only ever seen with her eyes closed.' },
      { camRelease: true },
    ]);
  },

  playWaystone(vesper) {
    this.flags.waystone = true;
    const mochi = this.npcs.mochi;
    Cutscene.play([
      { cam: { x: 620, y: 470, viewH: 440 } },
      { move: { ent: vesper, x: 470, y: 540, speed: 120 } },
      { face: { ent: vesper, dir: 'right' } },
      { say: ['vesper', '(A waystone. A worn face carved into the stone — patient, half-swallowed by moss, watching the road.)'] },
      { say: ['vesper:worried', '(It’s the one from drawing forty-one. Line for line, crack for crack.)'] },
      { say: ['vesper:worried', '(Which is impossible. I drew it eleven days ago, four hundred miles from here — asleep.)'] },
      { run: () => { mochi.hidden = false; mochi.x = 660; mochi.y = 580; mochi.dir = 'left'; } },
      { wait: 0.6 },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['vesper', 'GAH— …a cat. Hello. You’re not in my records.'] },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['vesper', '(The cat has decided something about me. I am choosing to find that flattering.)'] },
      { say: ['vesper', '(Also noted: lamplight, up the road. Eleven days of cold camps, and this valley feels like walking into somebody’s kitchen.)'] },
      { say: ['vesper', '(There will be an explanation. There is always an explanation.)'] },
      { run: () => { mochi.follow = 'vesper'; } },
      { toast: { text: '✦ A cat is following Vesper', color: '#d9a441' } },
      { camRelease: true },
    ]);
  },

  playVesperOutro(vesper) {
    this.flags.vesperDone = true;
    Cutscene.play([
      { narrate: 'The mapmaker bought a third honeybun she had no intention of admitting to, and waited for the lamps.' },
      { run: () => {
          vesper.x = 445; vesper.y = 590; vesper.dir = 'up';
          const mochi = this.npcs.mochi;
          mochi.scene = 'square'; mochi.x = 408; mochi.y = 605;
        } },
      { fadeTo: 1 },
      { wait: 1.0 },
      { banner: { title: '— LAKE —', sub: 'the last lamplighter of Emberbrook', dur: 5 } },
      { run: () => { this.setPhase('lake'); } },
      { waitFor: () => window.players.some(p => p && p.role === 'lake') },
      { run: () => {
          const lake = window.players.find(p => p && p.role === 'lake');
          const sp = this.spawnFor('lake');
          lake.scene = sp.scene; lake.x = sp.x; lake.y = sp.y; lake.dir = sp.dir; lake.hidden = false;
        } },
      { fadeTo: 0 },
      { wait: 0.6 },
    ]);
  },

  playLakeIntro(lake) {
    this.flags.lakeIntro = true;
    Cutscene.play([
      { cam: { x: 700, y: 480, viewH: 600 } },
      { narrate: 'The same evening, on the other side of the village: the last lamplighter of Emberbrook rose from his grandmother’s table, and took down his grandmother’s flame.' },
      { move: { ent: lake, x: 620, y: 640, speed: 160 } },
      { face: { ent: lake, dir: 'up' } },
      { say: ['lake', '(A year tonight since she set the lighter down and didn’t pick it up again.)'] },
      { say: ['lake', '(Forty years she carried it. It has never once gone out.)'] },
      { say: ['lake', '(She used to say it wasn’t hers to put out. I used to think that was a saying.)'] },
      { say: ['lake', '(The job, the way she gave it to me: carry the flame from the village’s heart to a lamppost near every home.)'] },
      { say: ['lake', '(So nobody sleeps outside the warmth. She said it the way you’d say “fetch the water.”)'] },
      { say: ['lake', '(Three lamps left before the Kindling Hour. Best go and mean it.)'] },
      { camRelease: true },
    ]);
  },

  playMeet(players) {
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const rowan = this.npcs.rowan;
    this.flags.met = true;
    this.setPhase('together');
    Cutscene.play([
      { run: () => { Net.send({ type: 'buzz', ms: 80 }); vesper.parked = false; vesper.scene = 'square'; } },
      { move: { ent: vesper, x: lake.x + 55, y: lake.y, speed: 150 } },
      { face: { ent: lake, dir: 'right' } }, { face: { ent: vesper, dir: 'left' } },
      { cam: { x: lake.x + 28, y: lake.y - 30, viewH: 400 } },
      { say: ['vesper:happy', 'Excuse me. You look official — you’re holding fire. Are you the lamplighter, or do I keep collecting cats until one talks?'] },
      { say: ['lake:worried', 'Oh. Um. Yes? The first one. Lake. The cats don’t talk, to my knowledge.'] },
      { say: ['vesper', 'Vesper. Mapmaker. Your elder says the Old Gate is your family’s business, and I need it open.'] },
      { say: ['lake', 'The— nobody crosses the Gate. It hasn’t opened in my lifetime. Why would anyone want—'] },
      { say: ['vesper', 'Because this valley isn’t on any chart I own. And I walked here anyway — on a road I only know from dreams.'] },
      { say: ['vesper:determined', 'Something on the other side of that gate has been sending me MAIL, Lake. I intend to answer it in person.'] },
      { say: ['lake:worried', '…what?'] },
      { say: ['rowan', 'The HOUR! Gather, gather! Neighbors, to the square! Lake — the flame!'] },
      { camRelease: true },
      { run: () => this.playKindlingHour(players) },
    ]);
  },

  playKindlingHour(players) {
    const { rowan, poppy, mara, pip } = this.npcs;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const F = this.flags;
    const hl = { x: 672, y: 470 };
    const sq = Field.scenes.square;

    const lampsOut = [];
    for (const l of sq.lamps) lampsOut.push({ run: () => { l.lit = false; } }, { wait: 0.3 });

    Cutscene.play([
      { move: { ent: rowan, x: 595, y: 555, speed: 110 } },
      { run: () => { poppy.x = 585; poppy.y = 605; poppy.dir = 'up'; } },
      { run: () => { mara.x = 748; mara.y = 612; mara.dir = 'up'; pip.x = 782; pip.y = 600; pip.dir = 'up'; pip.moving = false; } },
      { run: () => { vesper.x = 612; vesper.y = 645; vesper.dir = 'up'; lake.x = 700; lake.y = 648; lake.dir = 'up'; } },
      { cam: { x: 672, y: 520, viewH: 500 } },
      { wait: 0.8 },
      { say: ['rowan:happy', 'Neighbors! The year turns!'] },
      { say: ['rowan', 'Three hundred years, and the warmth of every one of them — right here. Every wedding. Every quarrel mended. Every good loaf and bad winter.'] },
      { say: ['rowan', 'You know the trade, and I never tire of saying it: bring the year’s best and tell it to the flame.'] },
      { say: ['rowan', 'You keep the memory — every minute, yours till you die. The flame keeps the WARMTH, and shines it on all of us, for good.'] },
      { say: ['rowan', 'What we tell the flame, the flame keeps.'] },
      { say: ['rowan', 'So bring your year, neighbors — the good and the bad of it. Let the flame hold it safe.'] },
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

      { say: ['poppy:hollow', '…My stall. My bread. Why doesn’t any of it feel like MINE?'] },
      { say: ['pip', 'Mama?'] },
      { say: ['mara:distressed', '…I’m sorry — whose child— no. I know whose. Mine.'] },
      { say: ['mara:distressed', 'I can say it, and it weighs NOTHING— someone’s crying. Why is someone crying?'] },
      { say: ['pip:scared', 'Mama. It’s me. It’s Pip. You KNOW me!'] },
      { say: ['rowan:grave', 'Everyone stay where you are. Names! Say your names, out loud — say them NOW.'] },
      { wait: 1.4 },
      { say: ['rowan:hollow', '…I’ll start. I am… '] },
      { wait: 1.8 },
      { say: ['rowan', '…I know my name. It just doesn’t feel like mine to say.'] },
      { say: ['rowan', 'I keep the ledger. I know that I keep the ledger.'] },
      { say: ['lake:worried', 'Rowan. Your name is Rowan.'] },
      { say: ['vesper:worried', '…You know them? All of them?'] },
      { say: ['lake', 'Every window in this village. Every name behind it. Why do I still— why do WE still—'] },
      { move: { ent: rowan, x: 652, y: 608, speed: 90 } },
      { say: ['rowan:grave', 'You two. The stranger and the lamplighter. Everyone in this square is a stranger wearing a neighbor’s face — except you.'] },
      { say: ['rowan', 'Why do YOU still hold your names?'] },
      { say: ['vesper', 'I got here an HOUR ago.'] },
      { say: ['lake', 'And keepers don\u2019t make tellings. We keep our own \u2014 Grandmother\u2019s one hard rule.'] },
      { say: ['lake', 'Whatever took the village\u2019s heart\u2026 nothing of mine was ever in it.'] },
      { say: ['lake:determined', '…My lighter’s still warm. Every other flame in Emberbrook just died. Not this one.'] },
      { say: ['rowan:grave', 'Then we are not finished. Not yet.'] },
      { say: ['rowan', 'See to them — all of them. They deserve their names back, even borrowed.'] },
      { say: ['rowan', 'Then come find me. I will be with my ledger — every word of it true, and not one of them mine.'] },
      { banner: { title: 'The Hush has come to Emberbrook', sub: 'the village loses its heart', dur: 5 } },
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
    const vesper = players.find(q => q && q.role === 'vesper');
    const lake = players.find(q => q && q.role === 'lake');
    if (!vesper || !lake) {
      Dialog.start([{ who: 'rowan', text: 'Both of you. This concerns the mapmaker AND the lamplighter — I’ll not say it twice.' }]);
      return;
    }
    Cutscene.play([
      { run: () => { vesper.x = 600; vesper.y = 600; vesper.dir = 'right'; lake.x = 692; lake.y = 605; lake.dir = 'left'; } },
      { move: { ent: rowan, x: 760, y: 585, speed: 90 } },
      { face: { ent: rowan, dir: 'left' } },
      { cam: { x: 672, y: 545, viewH: 440 } },
      { say: ['rowan:grave', 'Look at this. The year four-twenty-nine. The flood. A wedding.'] },
      { say: ['rowan:grave', 'I wrote every line of this page — and tonight I read it like the minutes of somebody else’s village.'] },
      { say: ['rowan', 'Ink keeps facts. It cannot keep what they WEIGHED.'] },
      { say: ['rowan', 'If our flame is truly gone, this village will stand here fed, housed, correct — and never be Emberbrook again.'] },
      { say: ['vesper', 'It won’t.'] },
      { say: ['vesper:worried', '…I don’t know why I said that with such confidence. Ignore me.'] },
      { say: ['rowan', 'No. Hold on to that, girl; we will need it.'] },
      { say: ['rowan', 'Now — our flame was first drawn from a shrine deep in the Whisperwood. The Kindling.'] },
      { say: ['rowan', 'Every Heartlight in every valley is a child of that fire.'] },
      { say: ['rowan', 'And the old Order kept one creed above all: light does not die — it is only ever carried.'] },
      { say: ['rowan', 'Whatever THAT was tonight, it did not put our flame out, children. It carried it off. Whole.'] },
      { say: ['rowan', 'Three hundred years of us, burning somewhere it should not be.'] },
      { say: ['lake', 'Nobody knows the way. The Gate’s been shut three hundred years. The road’s gone.'] },
      { say: ['vesper:worried', '…I need to show you both something, and I need you to not be strange about it.'] },
      { say: ['vesper', 'Since I was six years old, I have drawn one clearing. Over and over. In dreams. Forty-one drawings of the same clearing.'] },
      { say: ['vesper', 'I came here because the forty-first had YOUR gate in the corner.'] },
      { say: ['rowan:grave', 'Girl… that is the Kindling. That is the heart of the Whisperwood.'] },
      { say: ['vesper', 'I have never BEEN there.'] },
      { say: ['rowan', 'No. It has been CALLING you. Forty-one times it called.'] },
      { say: ['rowan', 'And tonight of all nights, a mapmaker with the road in her head stands in our square — beside the last living flame in the valley.'] },
      { say: ['rowan', 'The map does not know fire. The flame does not know the way. So it must be both of you, together.'] },
      { say: ['vesper', 'We met an hour ago.'] },
      { say: ['rowan:happy', 'Then you have an hour’s head start on resenting each other. Marvelous. The sigils will want more than acquaintance, mind.'] },
      { toast: { text: '✦ Vesper carries the Dream Charts', color: '#4f9f92' } },
      { wait: 0.6 },
      { toast: { text: '✦ Lake carries the Last Spark', color: '#e0a94e' } },
      { say: ['rowan:grave', 'Understand what you carry, boy. That little flame is the last live fire in the valley.'] },
      { say: ['rowan:grave', 'While it burns, Emberbrook is not dead — only dark. Our whole heart went somewhere tonight. Someone must go after it.'] },
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
      { say: ['lake', 'He’s not my—'] },
      { say: ['rowan', 'It was not a question, boy. Some decisions are made over our heads.'] },
      { say: ['rowan', 'That cat has been watching the north road all evening. I suggest you take the hint.'] },
      { run: () => { mochi.follow = 'party'; } },
      { toast: { text: '✦  Mochi joined the party  ✦', color: '#d9a441' } },
      { banner: { title: '✦ Quest — The Long Rekindling ✦', sub: 'Carry the Last Spark to the Kindling, deep in the Whisperwood', dur: 6 } },
      { mood: 'resolve' },
      { run: () => { this.flags.pactDone = true; Field.scenes.gate.platesActive = true; } },
      { say: ['rowan', 'Twin sigils, before the Gate. The Lamplighters cut them, in the old days — that road was always meant to be walked by two.'] },
    ]);
  },

  /* ================= dev checkpoints (keys 1–7) ================= */
  CHECKPOINT_NAMES: ['', 'Vesper: forest start', 'Vesper: village square', 'Lake: cottage start',
    'the meet (lamps done)', 'aftermath (post-Hush)', 'the sigils (pact done)', 'gate: finale ready'],
  applyCheckpoint(n) {
    if (n === 1) { location.reload(); return; }
    const F = this.flags;
    // clear any running story UI
    Dialog.lines = null;
    Cutscene.active = false; Cutscene.steps = null; Cutscene.holdJob = null; Cutscene.waitFn = null; Cutscene.moveJob = null;
    Camera.target = null; FX.letterboxTarget = 0; FX.fadeTarget = 0;
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
    Object.assign(F, { vesperIntro: true, waystone: true, vesperTalked: {}, vesperDone: false, lakeIntro: false,
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
    N.mochi.hidden = false; N.mochi.follow = 'vesper';
    N.stranger.hidden = true;
    j.parked = false; c.hidden = false;

    if (n === 2) {
      this.phase = 'vesper';
      place(j, 'square', 600, 630, 'up'); place(N.mochi, 'square', 560, 645);
      c.hidden = true; place(c, 'interior', 880, 590, 'down');
      AudioSys.setMood('festival');
    }
    if (n === 3) {
      F.vesperTalked = { poppy: true, mara: true }; F.vesperDone = true;
      this.phase = 'lake';
      j.parked = true; place(j, 'square', 445, 590, 'up'); place(N.mochi, 'square', 408, 605);
      place(c, 'interior', 880, 590, 'down');   // lakeIntro will auto-play
      AudioSys.setMood('festival');
    }
    if (n === 4) {
      F.vesperTalked = { poppy: true, mara: true }; F.vesperDone = true; F.lakeIntro = true;
      F.lampsLit = 3; setLamps(true);
      this.phase = 'lake';
      j.parked = true; place(j, 'square', 445, 590, 'up'); place(N.mochi, 'square', 408, 605);
      place(c, 'square', 900, 520, 'left');     // the meet auto-triggers
      AudioSys.setMood('festival');
    }
    if (n >= 5) {
      F.vesperTalked = { poppy: true, mara: true }; F.vesperDone = true; F.lakeIntro = true;
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
    const scene = this.activeRoles().includes('vesper') && !j.parked ? j.scene : c.scene;
    Field.enter(scene);
    Field.cam.x = (this.phase === 'lake' ? c : j).x;
    Field.cam.y = (this.phase === 'lake' ? c : j).y;
    this.setPhase(this.phase);
    Toasts.add('⚑ checkpoint — ' + this.CHECKPOINT_NAMES[n], '#8fb0c9');
  },

  playEnding(players) {
    const F = this.flags;
    const vesper = players.find(p => p && p.role === 'vesper');
    const lake = players.find(p => p && p.role === 'lake');
    const mochi = this.npcs.mochi;
    F.endingStarted = true;
    Cutscene.play([
      { run: () => { vesper.dir = 'up'; lake.dir = 'up'; } },
      { cam: { x: 672, y: 330, viewH: 480 } },
      { narrate: 'Beyond the Old Gate, the road ran grey — soft and wrong, like snow that refused to melt.' },
      { run: () => Particles.burst(26, () => ({
          kind: 'moth', seed: Math.random() * 9, life: 10,
          x: 540 + Math.random() * 270, y: 150 + Math.random() * 210,
          vx: (Math.random() - 0.5) * 10, vy: -4 - Math.random() * 8,
        })) },
      { say: ['vesper', '…Moths. The whole road is moths.'] },
      { say: ['lake', 'That’s where the light went. Some of it never made it to the sky.'] },
      { wait: 0.8 },
      { narrate: 'The moths drifted without hurry and without direction, the way lost things drift.' },
      { run: () => { mochi.scene = 'gate'; mochi.x = (vesper.x + lake.x) / 2; mochi.y = Math.min(vesper.y, lake.y) - 26; mochi.dir = 'up'; } },
      { say: ['mochi', 'Mrrp.'] },
      { say: ['vesper', 'New page. “North of Emberbrook: one road, unmapped, grey. Full of lost light.”'] },
      { say: ['vesper:thinking', '(I have wanted an unmapped road my whole life. I imagined it differently.)'] },
      { say: ['lake', 'My grandmother had a saying for the rounds. The first lamp is the whole job — the rest is only more of it.'] },
      { say: ['vesper', 'Is that supposed to help?'] },
      { say: ['lake', '…It always did. A little.'] },
      { say: ['vesper', 'Then it goes in the book. Come on, partner — first lamp.'] },
      { narrate: 'The Order of Lamplighters kept one creed: light does not die — it is only ever carried. And on the grey road north, theirs was the last light walking.' },
      { mood: 'silence' },
      { run: () => {
          F.ended = true;
          AudioSys.finale();
          Net.send({ type: 'end' });
        } },
    ]);
  },
};
