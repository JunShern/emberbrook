'use strict';
/* ============================================================
   CHAPTER ONE — "Emberwake"

   Act I   — JUNE: a mapmaker follows a road she has only seen
             in dreams, into a village that is not on her maps.
   Act II  — COLE: the last lamplighter of Emberbrook makes his
             rounds on festival night, carrying a flame that has
             never gone out.
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
  },
  npcs: {}, darkLamps: [], litLamps: [], buntings: [], entities: [],

  activeRoles() {
    return this.phase === 'june' ? ['june'] : this.phase === 'cole' ? ['cole'] : ['june', 'cole'];
  },
  setPhase(p) {
    this.phase = p;
    Net.send({ type: 'phase', act: p });
  },

  /* ---------------- map ---------------- */
  build() {
    World.init(48, 36);
    const W = World;

    W.fillT(23, 0, 25, 12, PATH);            // north road, through the gate
    W.fillT(12, 14, 20, 15, PATH);           // west lane
    W.fillT(23, 19, 24, 34, PATH);           // south road (June arrives this way)
    W.fillT(10, 27, 23, 28, PATH);           // cottage lane
    W.fillT(25, 27, 30, 28, PATH);           // pond lane
    for (let y = 0; y < 36; y++) for (let x = 0; x < 48; x++) {
      const dx = (x + 0.5 - 24.5) / 4.6, dy = (y + 0.5 - 15.5) / 4.6;
      if (dx * dx + dy * dy < 1) W.tiles[y][x] = PLAZA;
    }
    for (let y = 0; y < 36; y++) for (let x = 0; x < 48; x++) {
      const dx = (x + 0.5 - 37.5) / 7.8, dy = (y + 0.5 - 28.5) / 5.4;
      const dx2 = (x + 0.5 - 37.5) / 6.5, dy2 = (y + 0.5 - 28.5) / 4.2;
      if (dx2 * dx2 + dy2 * dy2 < 1) { W.tiles[y][x] = WATER; W.coll[y][x] = 1; }
      else if (dx * dx + dy * dy < 1 && W.tiles[y][x] === GRASS) W.tiles[y][x] = SAND;
    }
    for (let x = 31; x <= 35; x++) { W.tiles[28][x] = DOCK; W.coll[28][x] = 0; }

    W.addHouse({ tx: 11, ty: 9,  tw: 4, th: 3, style: 'bakery' });
    W.addHouse({ tx: 30, ty: 8,  tw: 4, th: 3, style: 'elder' });
    W.addHouse({ tx: 9,  ty: 23, tw: 4, th: 3, style: 'cottage' });  // Cole's
    W.addHouse({ tx: 16, ty: 20, tw: 4, th: 3, style: 'thatch' });
    W.addHouse({ tx: 33, ty: 20, tw: 3, th: 3, style: 'hut' });

    for (let y = 0; y < 36; y++) for (let x = 0; x < 48; x++) {
      if (x < 1 || x >= 47) W.coll[y][x] = 1;
      if (y >= 35 && !(x >= 23 && x <= 24)) W.coll[y][x] = 1;
      if (y < 1 && !(x >= 23 && x <= 25)) W.coll[y][x] = 1;
    }

    W.gate = { x0: 21, x1: 27, y0: 2, y1: 4, open: false, opening: 0, sigilsLit: false };
    W.gateCells = [];
    for (let y = 2; y <= 4; y++) for (let x = 21; x <= 27; x++) {
      W.coll[y][x] = 1;
      if (x >= 23 && x <= 25) W.gateCells.push([x, y]);
    }
    W.plates = [{ x: 22.5 * T, y: 6.5 * T, hold: 0 }, { x: 26.5 * T, y: 6.5 * T, hold: 0 }];

    W.heartlight = { x: 400, y: 254, state: 'alive' };
    W.coll[15][24] = 1; W.coll[15][25] = 1;

    let seed = 20260718;
    const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    for (let x = 1; x < 47; x += 2) {
      if (!(x >= 21 && x <= 27)) W.addTree(x, 1 + (x % 3 === 0 ? 1 : 0), rnd() > 0.5);
      if (!(x >= 22 && x <= 26)) W.addTree(x + (x % 4 === 0 ? 1 : 0), 34 - (x % 3), rnd() > 0.5);
    }
    for (let y = 3; y < 34; y += 2) { W.addTree(1 + (y % 3 === 0 ? 1 : 0), y, rnd() > 0.6); W.addTree(46 - (y % 3 === 0 ? 1 : 0), y, rnd() > 0.6); }
    for (let i = 0; i < 46; i++) W.addTree(2 + Math.floor(rnd() * 44), 2 + Math.floor(rnd() * 32), rnd() > 0.6);

    const FC = ['#e8788a', '#f2d16b', '#e8e2f2', '#e8a04c'];
    for (let i = 0; i < 90; i++) {
      const tx = 1 + Math.floor(rnd() * 46), ty = 1 + Math.floor(rnd() * 34);
      if (W.tiles[ty][tx] === GRASS && !W.coll[ty][tx])
        W.flowers.push({ x: tx * T + 3 + rnd() * 10, y: ty * T + 3 + rnd() * 10, c: FC[Math.floor(rnd() * 4)], ph: rnd() * 6 });
    }

    // festival dressing
    this.litLamps = [
      W.addLamp(20, 11, true), W.addLamp(29, 12, true),
      W.addLamp(21, 19, true), W.addLamp(22, 25, true), W.addLamp(31, 26, true),
    ];
    this.darkLamps = [W.addLamp(16, 13, false), W.addLamp(27, 20, false), W.addLamp(26, 8, false)];

    W.addProp('stall', 21, 12, { tw: 2, goods: 'buns', c1: '#c9584a', c2: '#f2e8d0' });
    W.addProp('stall', 27, 12, { tw: 2, goods: 'trinkets', c1: '#4f9f92', c2: '#f2e8d0' });
    W.addProp('crate', 20, 13); W.addProp('barrel', 23, 12); W.addProp('barrel', 29, 13);
    W.addProp('crate', 13, 13); W.addProp('noticeboard', 19, 17);
    W.addProp('sign', 26, 26);
    W.addProp('waystone', 22, 31, { solid: true });
    W.addProp('fence', 8, 27, { tw: 3 });

    this.buntings = [
      W.addBunting(20 * T + 8, 11 * T - 20, 29 * T + 8, 12 * T - 20, true),
      W.addBunting(21 * T + 8, 19 * T - 20, 29 * T + 8, 12 * T - 16, true),
      W.addBunting(16 * T + 8, 13 * T - 20, 21 * T + 8, 12 * T - 14, true),
    ];

    World.setLight('night');
    AudioSys.setMood('festival');

    const N = (key, x, y, dir) => {
      const e = { key, look: key, x, y, dir: dir || 'down', moving: false, animT: 0 };
      this.npcs[key] = e; this.entities.push(e);
      return e;
    };
    N('rowan', 26.5 * T, 14 * T, 'down');
    N('poppy', 22 * T + 8, 11.8 * T, 'down');
    N('finn', 35 * T + 12, 28 * T + 4, 'right');
    N('mara', 27 * T, 18 * T, 'left');
    N('pip', 27.8 * T, 18.6 * T, 'left');
    const mochi = { key: 'mochi', cat: true, x: 25 * T, y: 32.5 * T, dir: 'left', moving: false, animT: 0, follow: null, hidden: true };
    this.npcs.mochi = mochi; this.entities.push(mochi);
    const stranger = { key: 'stranger', look: 'stranger', x: 24.5 * T, y: -3 * T, dir: 'down', moving: false, animT: 0, hidden: true };
    this.npcs.stranger = stranger; this.entities.push(stranger);
  },

  spawnFor(role) {
    // June walks in from the south; Cole starts at his cottage door
    return role === 'june'
      ? { x: 384, y: 33.5 * T, dir: 'up' }
      : { x: 11.5 * T, y: 28.3 * T, dir: 'down' };
  },

  /* ---------------- per-frame ---------------- */
  update(dt, players) {
    const F = this.flags;
    World.update(dt);
    const june = players.find(p => p && p.role === 'june');
    const cole = players.find(p => p && p.role === 'cole');

    // hide the inactive keeper's character until their act
    if (cole) cole.hidden = this.phase === 'june';
    if (june) june.parked = this.phase === 'cole';

    // --- Act I: June's opening ---
    if (this.phase === 'june' && june && !F.juneIntro && !Cutscene.active) this.playJuneIntro(june);
    if (this.phase === 'june' && june && F.juneIntro && !F.waystone && june.y < 31.6 * T && !Cutscene.active)
      this.playWaystone(june);

    // --- Act II: Cole's opening ---
    if (this.phase === 'cole' && cole && !F.coleIntro && !Cutscene.active && !Dialog.active())
      this.playColeIntro(cole);

    // meet — when the third lamp is lit
    if (this.phase === 'cole' && !F.met && F.lampsLit >= 3 && june && cole && !Cutscene.active && !Dialog.active())
      this.playMeet(players);

    // Pip orbits his mother during the festival
    const pip = this.npcs.pip, mara = this.npcs.mara;
    if (!F.hushDone && !Cutscene.active) {
      pip.animT += dt; pip.moving = true;
      const a = time * 1.6;
      pip.x = mara.x + Math.cos(a) * 22;
      pip.y = mara.y + Math.sin(a) * 12 + 6;
      pip.dir = Math.cos(a) > 0 ? 'right' : 'left';
    }

    // Mochi the follower
    const mochi = this.npcs.mochi;
    if (!Cutscene.active && mochi.follow) {
      let tx, ty;
      if (mochi.follow === 'june' && june && !june.parked) { tx = june.x - 14; ty = june.y + 4; }
      else if (mochi.follow === 'party') {
        const ps = players.filter(p => p && !p.hidden);
        if (ps.length) {
          tx = ps.reduce((s, p) => s + p.x, 0) / ps.length - 14;
          ty = ps.reduce((s, p) => s + p.y, 0) / ps.length + 10;
        }
      }
      if (tx != null) {
        const dx = tx - mochi.x, dy = ty - mochi.y, d = Math.hypot(dx, dy);
        if (d > 26) {
          mochi.x += dx / d * Math.min(70, d * 2) * dt;
          mochi.y += dy / d * Math.min(70, d * 2) * dt;
          mochi.dir = dx > 0 ? 'right' : 'left';
        }
      }
    }

    // sigil plates
    const gate = World.gate;
    if (F.pactDone && !gate.open && !gate.openingStarted) {
      let all = true;
      for (const pl of World.plates) {
        const on = players.some(p => p && Math.hypot(p.x - pl.x, p.y - pl.y) < 15);
        pl.hold = on ? Math.min(1, pl.hold + dt / 1.2) : Math.max(0, pl.hold - dt * 2);
        if (pl.hold < 1) all = false;
      }
      if (all && june && cole) {
        gate.openingStarted = true;
        AudioSys.rumble();
        Net.send({ type: 'buzz', ms: 300 });
      }
    }
    if (gate.openingStarted && !gate.open) {
      gate.opening = Math.min(1, gate.opening + dt / 1.8);
      FX.shake = Math.max(FX.shake, 2.5 * (1 - gate.opening));
      if (gate.opening >= 1) {
        gate.open = true;
        for (const [x, y] of World.gateCells) World.coll[y][x] = 0;
        AudioSys.chime();
        F.gateOpen = true;
      }
    }

    if (F.gateOpen && !F.ended && !F.endingStarted && !Cutscene.active &&
        june && cole && june.y < 1.8 * T && cole.y < 1.8 * T) {
      this.playEnding(players);
    }
    if (F.ended) F.endT += dt;
  },

  objective() {
    const F = this.flags;
    if (F.ended) return '';
    if (this.phase === 'june') {
      if (!F.waystone) return 'Follow the south road into the valley';
      const n = Object.keys(F.juneTalked).length;
      if (n < 2) return `The festival of Emberwake — meet the villagers (${n}/2)`;
      return 'Find whoever is in charge — the elder, by the glowing crystal';
    }
    if (this.phase === 'cole') {
      if (!F.coleIntro) return '';
      return `Your rounds — light the dark lamps before the Kindling Hour (${F.lampsLit}/3)`;
    }
    if (!F.hushDone) return 'The Kindling Hour begins…';
    if (!F.pactDone) {
      const n = Object.keys(F.seen).length;
      return n < 4 ? `See to the villagers — (${n}/4)` : 'Find Elder Rowan by the Heartlight';
    }
    if (!F.gateOpen) return 'Stand on the twin sigils before the Old Gate — together';
    return 'Step through the Old Gate — together';
  },

  /* ---------------- interaction ---------------- */
  nearestThing(p) {
    let best = null, bd = 30;
    const consider = (x, y, thing) => {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d < bd) { bd = d; best = thing; }
    };
    for (const key of ['rowan', 'poppy', 'finn', 'mara', 'pip', 'mochi']) {
      const n = this.npcs[key];
      if (n.hidden) continue;
      consider(n.x, n.y, { kind: 'npc', key, ent: n });
    }
    if (p.role === 'cole') for (const l of this.darkLamps) if (!l.lit) consider(l.x, l.y - 8, { kind: 'lamp', lamp: l });
    const hl = World.heartlight;
    consider(hl.x, hl.y - 8, { kind: 'heartlight' });
    consider(19 * T + 8, 17 * T + 8, { kind: 'notice' });
    consider(26 * T + 8, 26 * T + 8, { kind: 'sign' });
    consider(22 * T + 8, 31 * T + 8, { kind: 'waystone' });
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
    if (this.flags.pactDone && !this.flags.gateOpen &&
        World.plates.some(pl => Math.hypot(p.x - pl.x, p.y - pl.y) < 26))
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
      const alive = World.heartlight.state === 'alive';
      Dialog.start([{ who: 'system', text: alive
        ? 'The Heartlight of Emberbrook. Three hundred years of the village live inside it — every wedding, every argument, every good loaf and bad winter. It hums, very faintly, like a kettle two rooms away.'
        : 'What is left of the Heartlight. It does not hum. It does not do anything. Holding a hand near it feels like reading a letter from someone who never existed.' }]);
    }
    if (t.kind === 'notice') {
      Dialog.start([{ who: 'system', text: this.flags.hushDone
        ? 'The notice board. The letters are still here, but they have stopped meaning anything to anyone but you two. One notice reads: "LOST — brown dog, answers to Biscuit."'
        : 'The notice board. "EMBERWAKE TONIGHT — bring a memory worth keeping. And a chair. We are short of chairs."' }]);
    }
    if (t.kind === 'sign') {
      Dialog.start([{ who: 'system', text: 'A road sign. North: THE OLD GATE (SHUT). South: EVERYWHERE ELSE.' }]);
    }
    if (t.kind === 'waystone') {
      Dialog.start([{ who: 'system', text: p.role === 'june'
        ? 'The waystone from drawing forty-one. She has stopped checking whether it matches. It matches.'
        : 'An old waystone. EMBERBROOK, it says, under forty years of moss. Somebody has recently brushed the moss off the E.' }]);
    }
  },

  lightLamp(lamp, p) {
    lamp.lit = true;
    this.flags.lampsLit++;
    AudioSys.lampOn();
    Net.send({ type: 'buzz', ms: 60 });
    Particles.burst(6, () => ({ kind: 'sparkle', x: lamp.x + (Math.random() - 0.5) * 8, y: lamp.y - 26, vy: -6, life: 0.8 }));
    if (this.flags.lampsLit === 1)
      Dialog.start([{ who: 'cole', text: '(One. The wick takes the flame like it remembers it. Grandmother swore they do.)' }]);
    if (this.flags.lampsLit === 2)
      Dialog.start([{ who: 'cole', text: '(Two. Light them like you mean it, she said, or they gutter by midnight. She never once explained what meaning it involved. I improvise.)' }]);
  },

  /* ---------------- NPC dialogue ---------------- */
  talkTo(key, ent, p) {
    const F = this.flags;
    if (!ent.cat) {
      const dx = p.x - ent.x, dy = p.y - ent.y;
      ent.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    }
    const isJune = p.role === 'june';
    const D = (lines, onFinish) => Dialog.start(lines.map(l => ({ who: l[0], text: l[1] })), onFinish);

    if (!F.hushDone) {
      /* ---------- festival night (Acts I & II) ---------- */
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
            ['rowan', '…Ha! Stay for the Kindling Hour, mapmaker. Then take it up with our lamplighter — the Gate was always his order’s business, not mine.'],
            ['rowan', 'The quiet boy with the flame that never goes out. You’ll find him apologizing to lamps somewhere across the square.'],
          ], () => { if (!F.juneDone) this.playJuneOutro(p); });
        }
        return D([
          ['rowan', 'Cole! The Kindling Hour will not wait for poetry. Lamps, boy, lamps!'],
        ]);
      }
      if (key === 'poppy') {
        if (isJune) { F.juneTalked.poppy = true;
          return D([
            ['poppy', 'A new face! Nobody passes through Emberbrook on Emberwake without eating something warm. That is not hospitality, that is law.'],
            ['june', 'I— alright. One. For the record, I’m here to chart the Whisperwood, not to eat pastry.'],
            ['poppy', 'Chart the— HA! Did you hear her? Eat two.'],
            ['june', '(I ate two. In my defense, they were extraordinary, and I have been walking for eleven days.)'],
          ]);
        }
        return D([
          ['poppy', 'There he is! The only soul in Emberbrook allowed to be late tonight — because nothing starts till his lamps are lit. Bun?'],
          ['cole', 'On duty, Poppy.'],
          ['poppy', 'Half a bun. I’ll hold the other half hostage until the Kindling Hour.'],
        ]);
      }
      if (key === 'finn') {
        if (isJune) F.juneTalked.finn = true;
        return D([
          ['finn', 'Festival’s up there. Fish are down here. I know which conversation I prefer.'],
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

    /* ---------- after the Hush (Act III) ---------- */
    if (key === 'rowan') {
      if (Object.keys(F.seen).length < 4) return D([
        ['rowan', 'See to them first. All of them. They deserve to hear their names from someone who still owns them.'],
        ['rowan', 'I will be here, reading my ledger… while it still says anything at all.'],
      ]);
      if (!F.pactDone) return this.playPact(p);
      return D([
        ['rowan', 'Twin sigils, before the Gate. Two keepers, one flame. Walk close, and walk kindly.'],
      ]);
    }
    if (key === 'poppy') {
      if (!F.seen.poppy) { F.seen.poppy = true;
        return D([
          ['poppy', '…Why am I holding bread? Whose stall is this? Whose HANDS are these— no, those are mine, I recognize the burn scars.'],
          ['cole', 'You’re Poppy. You bake. Every morning you burn your thumb on the first tray and swear you won’t tomorrow.'],
          ['poppy', '…Do I do it anyway?'],
          ['cole', 'Every morning.'],
          ['poppy', 'The word. The round warm things. Give me the word.'],
          ['june', 'Honeybuns.'],
          ['poppy', 'HONEYBUNS. Say more words. Both of you. Anything in this stall, it’s yours — I am reliably informed it is mine to give.'],
          ['june', '(I’m writing it all down. Everything they’ve lost. If this ever happens again — there will be a copy of everyone.)'],
        ]);
      }
      return D([['poppy', 'Honeybuns. Poppy. Thumb. I’m keeping the words in a row where I can see them.']]);
    }
    if (key === 'finn') {
      if (!F.seen.finn) { F.seen.finn = true;
        return D([
          ['finn', 'Can’t recall my own name, friend. Hands still know the knots, though. Funny what stays.'],
          ['cole', 'Finn. You’re Finn.'],
          ['finn', '…Finn. Huh. Short. I like it.'],
          ['finn', 'Tell you one thing for your book, mapmaker: the fish stopped circlin’. The very moment it happened. Like they’d been countin’ down to it.'],
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
          ['mara', 'I believe you. That is the worst of it — I believe every word, and it lands like a fact about a stranger.'],
          ['pip', '…You held my hand. TONIGHT. You said I’d remember tonight forever.'],
          ['june', 'Pip. Look at me. I saw her holding your hand — an hour ago, by the stall.'],
          ['june', 'I’m a mapmaker. I keep records of true things. And I am telling you: it is TRUE. It happened. I have it.'],
          ['pip', '…Is it in ink?'],
          ['june', 'It is now.'],
          ['mara', 'Whoever you two are — whatever you still carry — do not waste it. Please.'],
        ]);
      }
      return D([
        ['pip', 'I’m teaching her me again. We started with my name and the good stick I found in spring.'],
        ['mara', 'It is a very good stick. I have decided to believe in the stick.'],
      ]);
    }
    if (key === 'mochi') {
      if (!F.seen.mochi) { F.seen.mochi = true;
        return D([
          ['june', 'The cat. The cat is FINE?!'],
          ['mochi', '(Mochi is purring. Mochi has, if anything, improved.)'],
          ['cole', 'Cats don’t keep their memories where moths can reach. My grandmother used to say that.'],
          ['june', 'Your grandmother said that. Casually. As common knowledge.'],
          ['cole', 'She said a lot of things. She was a lamplighter too.'],
        ]);
      }
      return D([['mochi', 'Mrrrrp. (He is watching the north road. He does not usually watch anything.)']]);
    }
  },

  /* ---------------- Act I cutscenes — June ---------------- */
  playJuneIntro(june) {
    this.flags.juneIntro = true;
    Cutscene.play([
      { banner: { title: '— JUNE —', sub: 'a mapmaker with someone else’s dreams', dur: 5 } },
      { cam: { x: june.x, y: june.y - 20, zoom: 3.6 } },
      { wait: 1.2 },
      { narrate: 'On the last night of autumn, a mapmaker walked into a valley that was not on her maps — following a road she had only ever seen with her eyes closed.' },
      { camRelease: true },
    ]);
  },

  playWaystone(june) {
    this.flags.waystone = true;
    const mochi = this.npcs.mochi;
    Cutscene.play([
      { cam: { x: 22.5 * T + 12, y: 31 * T - 6, zoom: 4.2 } },
      { move: { ent: june, x: 23.2 * T, y: 31.4 * T, speed: 50 } },
      { face: { ent: june, dir: 'left' } },
      { say: ['june', '(A waystone. Grey cap. Moss on the north face. A crack running through the E of EMBERBROOK like a river.)'] },
      { say: ['june', '(It’s the one from drawing forty-one. Line for line. Which is impossible — I drew it eleven days ago, four hundred miles from here, asleep.)'] },
      { run: () => { mochi.hidden = false; mochi.x = june.x + 30; mochi.y = june.y + 8; mochi.dir = 'left'; } },
      { wait: 0.6 },
      { say: ['mochi', 'Mrrp.'] },
      { face: { ent: june, dir: 'right' } },
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
    const poppy = this.npcs.poppy;
    Cutscene.play([
      { narrate: 'The mapmaker bought a third honeybun she had no intention of admitting to, and waited for the lamps.' },
      { run: () => {
          june.x = poppy.x + 4; june.y = poppy.y + 30; june.dir = 'up';
          const mochi = this.npcs.mochi;
          mochi.x = june.x + 14; mochi.y = june.y + 6;
        } },
      { fadeTo: 1 },
      { wait: 1.0 },
      { banner: { title: '— COLE —', sub: 'the last lamplighter of Emberbrook', dur: 5 } },
      { run: () => { this.setPhase('cole'); } },
      { waitFor: () => window.players.some(p => p && p.role === 'cole') },
      { run: () => {
          const cole = window.players.find(p => p && p.role === 'cole');
          const sp = this.spawnFor('cole');
          cole.x = sp.x; cole.y = sp.y; cole.dir = 'down'; cole.hidden = false;
        } },
      { fadeTo: 0 },
      { wait: 0.6 },
    ]);
  },

  /* ---------------- Act II cutscenes — Cole ---------------- */
  playColeIntro(cole) {
    this.flags.coleIntro = true;
    Cutscene.play([
      { cam: { x: cole.x, y: cole.y - 10, zoom: 4 } },
      { narrate: 'The same evening, across the square: the last lamplighter of Emberbrook stepped out of his grandmother’s cottage, carrying his grandmother’s flame.' },
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
      { run: () => { Net.send({ type: 'buzz', ms: 80 }); june.parked = false; } },
      { move: { ent: june, x: cole.x + 22, y: cole.y, speed: 65 } },
      { face: { ent: cole, dir: 'right' } }, { face: { ent: june, dir: 'left' } },
      { cam: { x: cole.x + 11, y: cole.y - 10, zoom: 4 } },
      { say: ['june', 'Excuse me. You look official — you’re holding fire. Are you the lamplighter, or do I keep collecting cats until one talks?'] },
      { say: ['cole', 'Oh. Um. Yes? The first one. Cole. The cats don’t talk, to my knowledge.'] },
      { say: ['june', 'June. Mapmaker. Your elder says the Old Gate is your family’s business, and I need it open.'] },
      { say: ['cole', 'The— nobody crosses the Gate. It hasn’t opened in my lifetime. Why would anyone want—'] },
      { say: ['june', 'Because this valley is not on any chart I own. And I walked here anyway — on a road I only know from dreams.'] },
      { say: ['june', 'Something on the other side of that gate has been sending me MAIL, Cole. I intend to answer it in person.'] },
      { say: ['cole', '…what?'] },
      { say: ['rowan', 'THE HOUR! Gather, gather! Neighbors, to the square! Cole — the flame!'] },
      { camRelease: true },
      { run: () => this.playKindlingHour(players) },
    ]);
  },

  /* ---------------- Act III — the Hush ---------------- */
  playKindlingHour(players) {
    const { rowan, poppy, mara, pip } = this.npcs;
    const june = players.find(p => p && p.role === 'june');
    const cole = players.find(p => p && p.role === 'cole');
    const hl = World.heartlight;
    const F = this.flags;

    const allLampsOut = [];
    for (const l of [...this.litLamps, ...this.darkLamps]) {
      allLampsOut.push({ run: () => { l.lit = false; } }, { wait: 0.22 });
    }

    Cutscene.play([
      { move: { ent: rowan, x: hl.x - 26, y: hl.y + 14, speed: 50 } },
      { run: () => { poppy.x = hl.x - 10; poppy.y = hl.y + 34; poppy.dir = 'up'; } },
      { run: () => { mara.x = hl.x + 26; mara.y = hl.y + 30; mara.dir = 'up'; pip.x = hl.x + 38; pip.y = hl.y + 34; pip.dir = 'up'; } },
      { run: () => { june.x = hl.x - 34; june.y = hl.y + 44; june.dir = 'up'; cole.x = hl.x - 18; cole.y = hl.y + 46; cole.dir = 'up'; } },
      { cam: { x: hl.x, y: hl.y + 10, zoom: 3.4 } },
      { wait: 0.8 },
      { say: ['rowan', 'Neighbors! The year turns!'] },
      { say: ['rowan', 'Three hundred years, and every one of them alive — right here. Every wedding. Every argument. Every good loaf and bad winter.'] },
      { say: ['rowan', 'What we tell the flame, the flame keeps.'] },
      { say: ['rowan', 'So! Who brings the first memory of the year?'] },
      { say: ['poppy', 'The flood! The spring flood — the whole town in my bakery, bailing water with soup pots, and LAUGHING, gods help us—'] },
      { run: () => { World.tempLights.push({ x: hl.x, y: hl.y - 16, r: 150, warm: 1.5, id: 'surge' }); } },
      { wait: 1.0 },

      { mood: 'silence' },
      { wait: 1.6 },
      { say: ['pip', '…Why did the music stop?'] },
      { flash: 1.4 }, { shake: 4 },
      { run: () => {
          hl.state = 'hollow';
          World.tempLights = World.tempLights.filter(l => l.id !== 'surge');
          Particles.burst(46, () => ({ kind: 'shard', x: hl.x + (Math.random() - 0.5) * 14, y: hl.y - 18, vy: -30 - Math.random() * 50, life: 3.2, seed: Math.random() * 9 }));
          Particles.burst(30, () => ({ kind: 'moth', x: hl.x + (Math.random() - 0.5) * 20, y: hl.y - 14, vx: (Math.random() - 0.5) * 30, vy: -10, life: 6, seed: Math.random() * 9 }));
          AudioSys.hushSting();
          Net.send({ type: 'buzz', ms: 500 });
        } },
      { wait: 1.4 },
      { run: () => { for (const b of this.buntings) b.lit = false; } },
      ...allLampsOut,
      { run: () => { FX.desatTarget = 0.55; for (const h of World.houses) h.dark = true; } },
      { wait: 1.2 },
      { narrate: 'It did not happen slowly. Between one heartbeat and the next, the light of Emberbrook — three hundred years of it — stood up and left.' },
      { run: () => Particles.burst(14, () => ({ kind: 'moth', x: hl.x + (Math.random() - 0.5) * 120, y: hl.y + (Math.random() - 0.5) * 60, vx: 0, vy: -6, life: 7, seed: Math.random() * 9 })) },

      { say: ['poppy', '…Why am I holding bread? Whose stall is this?'] },
      { say: ['pip', 'Mama?'] },
      { say: ['mara', '…I’m sorry — whose child is this? Where is— I don’t— someone’s crying. Why is someone crying?'] },
      { say: ['pip', 'MAMA. It’s me. It’s Pip. You KNOW me!'] },
      { say: ['rowan', 'Everyone stay where you are. Names! Say your names, out loud — say them NOW.'] },
      { wait: 1.4 },
      { say: ['rowan', '…I’ll start. I am… '] },
      { wait: 1.8 },
      { say: ['rowan', '…I keep the ledger. I know that I keep the ledger.'] },
      { say: ['cole', 'Rowan. Your name is Rowan.'] },
      { say: ['june', '…You know them? All of them?'] },
      { say: ['cole', 'Every window in this village. Every name behind it. Why do I still— why do WE still—'] },
      { move: { ent: rowan, x: cole.x - 4, y: cole.y - 26, speed: 45 } },
      { say: ['rowan', 'You two. The stranger and the lamplighter. Everyone in this square is a stranger wearing a neighbor’s face — except you.'] },
      { say: ['rowan', 'Why do YOU still hold your names?'] },
      { say: ['june', 'I got here an HOUR ago.'] },
      { say: ['cole', '…My lighter’s still warm. Every other flame in Emberbrook just died. Not this one.'] },
      { say: ['rowan', 'Then we are not finished. Not yet.'] },
      { say: ['rowan', 'See to them — all of them. They deserve their names back, even borrowed. Then come find me… while my ledger still says anything at all.'] },
      { banner: { title: 'The Hush has come to Emberbrook', sub: 'the village forgets itself', dur: 5 } },
      { mood: 'hush' },
      { run: () => { F.hushDone = true; Net.send({ type: 'buzz', ms: 200 }); } },
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
    const hl = World.heartlight;
    Cutscene.play([
      { run: () => { june.x = hl.x - 30; june.y = hl.y + 34; june.dir = 'up'; cole.x = hl.x - 8; cole.y = hl.y + 38; cole.dir = 'up'; } },
      { move: { ent: rowan, x: hl.x + 18, y: hl.y + 26, speed: 45 } },
      { face: { ent: rowan, dir: 'left' } },
      { cam: { x: hl.x, y: hl.y + 16, zoom: 3.8 } },
      { say: ['rowan', 'Look at this. This morning, this page held the year four-twenty-nine. The flood. A wedding — someone’s wedding, the ink is going as I hold it.'] },
      { say: ['rowan', 'Ink outlasts minds. It will not outlast whatever THAT was. When this book goes blank, Emberbrook never happened.'] },
      { say: ['june', 'It won’t.'] },
      { say: ['june', '…I don’t know why I said that with such confidence. Ignore me.'] },
      { say: ['rowan', 'No. Hold on to that, girl; we will need it.'] },
      { say: ['rowan', 'Now — our flame was first drawn from a shrine deep in the Whisperwood. The Kindling. Every Heartlight in every valley is a child of that fire.'] },
      { say: ['cole', 'Nobody knows the way. The Gate’s been shut three hundred years. The road’s gone.'] },
      { say: ['june', '…I need to show you both something, and I need you to not be strange about it.'] },
      { say: ['june', 'Since I was six years old, I have drawn one clearing. Over and over. In dreams. Forty-one drawings of the same clearing.'] },
      { say: ['june', 'I came here because the forty-first had YOUR gate in the corner.'] },
      { say: ['rowan', 'Girl… that is the Kindling. That is the heart of the Whisperwood.'] },
      { say: ['june', 'I have never BEEN there.'] },
      { say: ['rowan', 'No. It has been CALLING you. Forty-one times it called.'] },
      { say: ['rowan', 'And tonight of all nights, it made sure a mapmaker with the road in her head stood in our square — beside the last living flame in the valley.'] },
      { say: ['rowan', 'The map does not know fire. The flame does not know the way. Alone, each of you is a curiosity. Together, you are a rescue.'] },
      { say: ['june', 'We met an hour ago.'] },
      { say: ['rowan', 'Then you have an hour’s head start on resenting each other. Marvelous. The sigils will want more than acquaintance, mind.'] },
      { run: () => {
          Particles.burst(10, () => ({ kind: 'mote', x: hl.x + (Math.random() - 0.5) * 10, y: hl.y - 12, vy: -14, life: 1.2 }));
        } },
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
          Particles.burst(18, () => ({ kind: 'sparkle', x: (june.x + cole.x) / 2 + (Math.random() - 0.5) * 30, y: (june.y + cole.y) / 2 - 10 - Math.random() * 14, vy: -8, life: 1.4 }));
        } },
      { wait: 0.8 },
      { move: { ent: mochi, x: hl.x - 20, y: hl.y + 40, speed: 70 } },
      { say: ['rowan', '…The cat is going with you.'] },
      { say: ['cole', 'He’s not my—'] },
      { say: ['rowan', 'It was not a question, boy. Some decisions are made over our heads. That one has been watching the north road all evening, and I suggest you take the hint.'] },
      { run: () => { mochi.follow = 'party'; } },
      { toast: { text: '✦  Mochi joined the party  ✦', color: '#d9a441' } },
      { banner: { title: '✦ Quest — The Long Rekindling ✦', sub: 'Carry the Last Spark to the Kindling, deep in the Whisperwood', dur: 6 } },
      { mood: 'resolve' },
      { run: () => { World.gate.sigilsLit = true; this.flags.pactDone = true; } },
      { say: ['rowan', 'Twin sigils, before the Gate. The Lamplighters cut them, in the old days — that road was always meant to be walked by two.'] },
    ]);
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
      { cam: { x: 24.5 * T, y: 1.2 * T, zoom: 3.6 } },
      { narrate: 'Beyond the Old Gate, the road ran grey — soft and wrong, like snow that refused to melt.' },
      { run: () => Particles.burst(60, () => ({
          kind: 'moth', seed: Math.random() * 9, life: 8,
          x: 23 * T + Math.random() * 3 * T, y: -2.5 * T + Math.random() * 3.4 * T,
          vx: (Math.random() - 0.5) * 20, vy: -14 - Math.random() * 20,
        })) },
      { shake: 1.5 },
      { say: ['june', '…Moths. The whole road is moths.'] },
      { say: ['cole', 'That’s where the light went. Some of it never made it to the sky.'] },
      { run: () => { stranger.hidden = false; stranger.x = 24.5 * T; stranger.y = -2.2 * T; stranger.dir = 'down'; } },
      { wait: 1.2 },
      { run: () => { mochi.x = (june.x + cole.x) / 2; mochi.y = Math.min(june.y, cole.y) - 6; } },
      { say: ['mochi', 'HHHHssss.'] },
      { say: ['june', 'He’s never done that.'] },
      { say: ['cole', 'He’s not my— …no. No, he’s never done that.'] },
      { run: () => { World.tempLights.push({ x: 24.5 * T, y: -2.6 * T, r: 34, warm: 0, id: 'lantern' }); AudioSys.blip(220); } },
      { say: ['june', 'Cole. His lantern. It isn’t dark — it’s FULL.'] },
      { wait: 1.4 },
      { narrate: 'The figure bowed — unhurried, and courteous, the way a debt collector is courteous — and was gone between one blink and the next.' },
      { run: () => { stranger.hidden = true; World.tempLights = World.tempLights.filter(l => l.id !== 'lantern'); } },
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
