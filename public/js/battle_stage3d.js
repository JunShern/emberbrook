// battle_stage3d.js — window.BattleStage3D: THE 3D BATTLE ARENA (battle-arena v3).
//
// THE RULING THIS FILE EXISTS TO SERVE: the v2 battle screen stood everyone in a
// single row of flat sprites — "more like a mobile game than a proper impressive
// desktop game". So the battle is now a 3D ARENA: a real THREE.Scene with a
// simple dished clearing, per-zone props, a curved backdrop carrying the
// pre-rendered plate, an FF-style staggered formation with depth, and 3D bodies
// for everyone who has a model. Anyone who does not gets a CAMERA-FACING
// BILLBOARD in the same scene — that is the ruled path, and it is also how every
// future character appears before their model is authored.
//
// ============================ THE SEAM ======================================
// This module owns PIXELS AND GEOMETRY ONLY. It never reads battle state, never
// touches GS, never sees an event stream, and never knows what a "round" is. Its
// entire surface to battle_turnbased.js is:
//
//   BattleStage3D.available()          -> bool  (DOM + THREE + a WebGL context)
//   BattleStage3D.create(cfg)          -> stage | null
//   stage.anchor(id)                   -> {x,y,h,vis} screen px of a body
//   stage.setTarget(id|null) / setActor(id|null)
//   stage.act(id, kind) / flinch(id) / ko(id) / revive(id) / setDead(id,bool)
//   stage.destroy()
//
// battle_turnbased.js keeps every UI window, the log, the command menus, the
// damage-number STYLING and the whole keyboard flow. What changed there is only
// WHERE a combatant's DOM furniture sits: in 3D mode the foe/hero elements become
// zero-width anchors that this stage positions each frame by projection. Kill
// this file and the DOM stage renders exactly as it did — that is the fallback.
//
// ============================ ARCHITECTURE: OWN RENDERER ====================
// This stage builds its OWN THREE.WebGLRenderer + Scene + Camera rather than
// sharing play3d's. Three reasons, in order of weight:
//   1. play3d.html is READ-ONLY custody and exposes no render hook. Sharing its
//      renderer would mean a second scene pass inside its loop() — an edit to a
//      file this agent may not touch.
//   2. The battle is EXCLUSIVE. UILOCK freezes phys() and the world renderer is
//      drawing a frozen frame nobody can see behind a full-bleed overlay; there
//      is no frame budget being wasted, only one being reclaimed.
//   3. Disposal is total. destroy() drops the context, so a battle cannot leak
//      geometry, textures or a rAF into the overworld — which a shared scene,
//      with its shared material cache, makes genuinely hard to guarantee.
// The cost is one extra WebGL context for the life of a battle. Accepted.
//
// This file is also NOT in play3d.html's script list (read-only): battle_turnbased
// injects it lazily, from its own sibling URL, the first time a battle starts on
// a page that has THREE. A page without THREE never fetches it.
//
// ============================ THE 2026 PASS (2026-08-02) ====================
// Two things changed and both are load-bearing enough to belong up here.
//
// 1. THE PARTY IS THE REAL CAST. `art.charModel` used to be a borrowed CC0
//    KayKit rogue and it was EVERY party member's body — three identical green
//    hooded chibis standing under three different painted busts. It is now null
//    and `art.models` names each character's own retargeted rig, the same files
//    play3d.html's MODELS registry hands the overworld. See the ASSET
//    CONVENTIONS block. A character with no rig falls to their OWN pose plate,
//    then to the mannequin — never to a wrong-identity body.
//    THE RIGS NOW CARRY COMBAT CLIPS — Attack / Hit_A / Death_A alongside the
//    three locomotion ones (character factory, 2026-08-02). The PROCEDURAL swing
//    that covered for their absence stood itself down on its own terms and stays
//    as the fallback for any body without them. See procSwing(), and CFG.act.fit
//    for why a donor's tempo is refitted to the turn's.
//
// 2. THE LOOK. Cast shadows, a near-horizontal rim matched to the plates' own
//    backlight, and one hand-rolled grade (bloom / split-tone / vignette /
//    grain) over the WHOLE frame, plate included — the diagnosis being that the
//    plate was a graded photograph and the 3D in front of it was raw
//    framebuffer. Plus a hit package: flash, shove, sparks, ground ring, camera
//    shake, and a lean-in on the swing. Every one of them has a kill switch in
//    CFG (`post.on`, `shadow.on`, `rim.on`, `fx.*`), and the before/after board
//    is docs/qa/battle3d/BEFORE-AFTER.md, shot by tools/battle_shots.mjs.
//
// ============================ HEADLESS SAFETY ===============================
// Nothing here runs at load beyond defining an object. available() is the only
// gate and it probes for document + THREE + a real GL context, so battle_sim and
// encounter_sim (node, no DOM) can neither reach nor break this module.
(function () {
  'use strict';

  const HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  const T = () => (typeof window !== 'undefined' ? window.THREE : null);
  const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());
  const D2R = Math.PI / 180;
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, u) => a + (b - a) * u;
  const easeOut = u => 1 - Math.pow(1 - u, 3);
  const easeInOut = u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);

  // ===== TUNABLES ===========================================================
  // Everything an art pass would want to move lives here and is mutable from the
  // console (BattleStage3D.CFG.cam.pitch = 12; then restart a battle), so tuning
  // the look never means editing geometry code.
  const CFG = {
    charH: 1.7,                    // the canonical character height, in metres
    snapshots: true,               // keep the drawing buffer readable (see the renderer)

    // THE FF BATTLE CAMERA. pitch/yaw are degrees. The yaw is toward +X (the
    // party's side) so the monsters — the things you aim at — read frontally and
    // the party reads three-quarter-rear, which is the classic legible framing.
    // THE MIRROR. `partySide` is the ONLY place the handedness of the whole
    // arena is written down: -1 puts the party on -X (screen LEFT) and the foes
    // on +X, +1 swaps them. Every x below is a MAGNITUDE, every facing and every
    // lunge is derived from this sign, and the camera yaws toward the party's
    // side so the foes — the things you aim at — keep reading frontally.
    // User ruling 2026-07-31: party left, enemies right.
    partySide: -1,
    cam: { fov: 34, dist: 11.6, pitch: 13, yawMag: 14, target: [0, 1.15, 0.15], near: 0.5, far: 260 },
    // The intro sweep: start wider/higher, ease into the rest pose. It plays
    // BEHIND battle_turnbased's own fade-in, so the first thing the player sees
    // is already settling.
    intro: { ms: 1050, dist: 1.34, pitch: 8, yawMag: 6 },
    // The idle drift. Amplitudes are metres; at this distance ~0.05 m is the
    // 2-3 screen pixels the brief asks for. Dies under reduced motion.
    drift: { ax: 0.075, ay: 0.05, az: 0.045, px: 0.061, py: 0.041, pz: 0.029, tgt: 0.5 },

    // THE ARENA GROUND: a dished clearing. `dish` is how far the rim rises above
    // the centre over `radius` metres, so combatants stand on near-flat ground
    // and the far edge lifts to meet the plate's horizon.
    ground: { radius: 20, rings: 30, segs: 72, dish: 1.35, bump: 0.22 },
    // THE BACKDROP BAND: a gently curved plane centred on the CAMERA AXIS (not
    // the world origin), so the visible arc is symmetric and the plate is mapped
    // at its natural aspect with ~1.2x upscale in the visible band rather than
    // the 2x horizontal stretch a world-centred cylinder forces.
    backdrop: { dist: 34, arcPad: 1.16, segs: 44, horizon: 0.58 },
    // FOG IS MEASURED FROM THE CAMERA, which stands 11.6 m out — so anything
    // under ~17 must stay clear or the fighters themselves come out hazed.
    fogNear: 18, fogFar: 33,

    // FORMATIONS. Distances in metres from the arena centre along the battle
    // axis (X). Party right (+X), foes left (-X).
    form: {
      // DEPTH IS THE SEPARATION, and it has to be generous. The camera's yaw
      // means a slot's screen-x is ~0.97x - 0.24z: pushing a body along +z drags
      // it LEFT almost as fast as pushing it along +x drags it right, so the two
      // very nearly cancel and no realistic sideways offset will pull two
      // combatants apart horizontally. What does separate them is the thing FF
      // actually used — distance, which shows up as size and as height in frame.
      // So the spreads are big (3.3 m between foes, 2.0 m between heroes) and the
      // sideways jog is only there to break the line, not to do the work.
      partyX: 3.2, partyDx: 1.05, partyZ: 0.35, partyDz: 2.0,   // partyX/foeX are MAGNITUDES
      // foeZ pushes the whole foe line AWAY from the camera: the nearest slot of
      // a three-wide chevron otherwise drops low enough to hide behind the
      // command window.
      foeX: 3.4, foeZ: -0.8, foeRank: 2.1, foeSpread: 3.2, foeJog: 0.78, foeChevron: 0.5,
    },
    // How far a body travels on a lunge, and for how long.
    act: { lungeM: 1.35, ms: 620, flinchM: 0.42, flinchMs: 330,
      // CLIP-TO-BEAT FIT (2026-08-02, when the cast got real combat clips). A donor
      // clip is authored at the DONOR's tempo and the turn is paced at the GAME's:
      // battle_turnbased announces, waits `wind` (300 ms), then lands the damage. The
      // retargeted attack is 1.200 s with its contact 37 % in, so played at its own
      // speed the number appears ~150 ms BEFORE the blow. Fitting the clip to the lunge
      // tween fixes it for free — the lunge's own contact is at 34 % — and the swing
      // and the step become one gesture instead of two overlapping ones.
      //   ms per kind, 0/absent = play at the clip's own tempo.
      fit: { attack: 620, hit: 330, die: 1000 },
      // and CLAMPED, because a clip 3x off the beat is the wrong clip, not a timing
      // problem: past this band, take the mismatch rather than ship a seizure.
      fitMin: 0.6, fitMax: 2.2 },

    // ===== THE 2026 PASS ======================================================
    // Everything below was added on 2026-08-02 against the shipped frame, which
    // the before/after board (docs/qa/battle3d/BEFORE-AFTER.md) photographs. The
    // diagnosis that produced this list, in one sentence: the painted plate was a
    // graded, backlit, golden-hour PHOTOGRAPH and the 3D layer in front of it was
    // an unlit, ungraded, shadowless clay model — two pictures in one frame.

    // CAST SHADOWS. The one thing a blob shadow cannot do is tell you a body is
    // standing where the light says it is. `size` is the orthographic half-width
    // in metres — it wraps the fight and nothing else, because a shadow camera
    // sized to the 20 m clearing spends its whole texel budget on empty grass.
    shadow: { on: true, map: 2048, size: 9, bias: -0.0016, normalBias: 0.02, radius: 2.6 },
    // THE RIM. The plates are backlit — the sun sits at or behind the horizon in
    // every one of the four — and the arena's key came from the front-left, so
    // every body read as a flat cutout laid on a lit photograph. A warm rim from
    // behind is what re-attaches them. Town lane's measured lesson, applied:
    // ADDING a source moves a frame; adjusting an existing one has never.
    //
    // IT IS ALMOST HORIZONTAL, AND THAT IS THE ENTIRE TRICK. three r128 tests a
    // light's layers against the CAMERA's, never against the object's (verified
    // in the shipped bundle), so there is no such thing here as a light that
    // touches bodies and not the floor. What there IS, is a sun at the horizon:
    // at y 1.05 over z -12 the direction is 8.7 degrees above level, so a floor
    // facing straight up takes cos(81) ~ 0.09 of it while a body's back takes
    // ~0.99. One-eleventh on the ground for full strength on the silhouette —
    // which is also, exactly, what the plates were painted under.
    rim: { on: true, intensity: 1.25, pos: [3.0, 1.05, -12] },

    // POST. One render target, a quarter-res bloom, and a grade — see makePost().
    // Kill switch: BattleStage3D.CFG.post.on = false restores the raw frame, and
    // that is how the pass is VERIFIED rather than asserted.
    // MEASURED IN TWO ROUNDS, and the numbers moved a long way between them.
    // Round one (bloom 0.62 / threshold 0.70) put a milky glow over the whole
    // lower half of every frame: the crag's dune went white and the meadow's
    // trodden centre disappeared under it. In display space — which is where
    // this grade runs, see above — a 0.70 threshold catches sunlit GRASS, not
    // just the sun. Round two: bloom down a third, threshold up to 0.80 so only
    // the sun, the river's specular and the hit flash qualify.
    post: {
      on: true,
      bloom: 0.40,        // how much of the blurred bright pass is added back
      threshold: 0.80,    // where a pixel starts to be "a highlight"
      knee: 0.17,         // softness of that threshold — a hard one strobes
      vignette: 0.38,     // corner falloff; the frame's own letterbox
      warmth: 0.042,      // highlights toward the plate's gold, shadows toward blue
      contrast: 1.085,    // a gentle S about mid grey
      sat: 1.08,
      grain: 0.016,       // a whisper of it. Kills the banding a smooth dish shows.
      scale: 0.25,        // bloom buffer resolution
    },

    // HIT FEEDBACK. Read this as a budget, not a wish list: a flash, a shove, a
    // shake and one puff of dirt. Anything more and a turn-based game starts
    // lying about how much happened.
    fx: {
      flashMs: 150,       // the struck body goes hot white and falls back
      flash: 0.62,        // 0.85 drove a pale creature to PURE white and it lost its own read
      shakeMs: 260, shake: 0.10, shakeKo: 0.19,   // metres of camera displacement
      // SPARK SIZE IS IN METRES AND THAT IS WHY THE FIRST NUMBER FAILED. 0.14 m
      // at 12 m from a 34-degree camera is under three pixels, and three
      // additive pixels over sunlit grass are nothing: the burst was in the
      // frame and invisible. 0.30 m is a spark you can see.
      sparks: 18,         // the impact burst
      sparkMs: 430,
      dust: true,         // a puff at the feet when a body lands its lunge
      pushIn: 0.055,      // the camera leans this fraction of its distance into a strike
      pushMs: 620,
    },
  };

  // ===== ZONE PALETTES ======================================================
  // The 3D arena is TINTED PER ZONE and its props are chosen per zone, so the
  // simple model reads as "the place the plate is a picture of". Everything is a
  // colour plus a prop recipe name — no zone needs code.
  // `horizon` is the fraction DOWN FROM THE TOP of that zone's plate that gets
  // pinned to the 3D ground's far silhouette. It is the whole of "the backdrop
  // was generated with awareness of the 3D model": the plates are painted with
  // their lower band deliberately empty and hazy, and this number says which
  // painted row the real ground takes over from. Re-shoot a plate, re-measure
  // this one value, and the seam is correct again.
  const ZONES = {
    // `dirt` is the TRODDEN CENTRE, and it is not always lighter than the field:
    // a meadow wears down to pale earth, a river shore wears down to DARK WET
    // silt. `grain` is how hard the fine-noise mottle is driven — a stony floor
    // wants far more of it than grass does, and that difference is most of why
    // crag and water were reading as pancakes next to meadow and forest.
    meadow: { ground: 0x6f8a3f, ground2: 0x93a856, dirt: 0x9c8a5c, rock: 0x9a9384,
              haze: 0xe6d3a8, sky: 0xd9c48e, key: 0xffe0b0, fill: 0x9fb6d8,
              props: 'meadow', horizon: 0.60, grain: 0.5 },
    forest: { ground: 0x5e4d31, ground2: 0x7d6540, dirt: 0x9a7f52, rock: 0x7c7364,
              haze: 0xd9b787, sky: 0xc9a473, key: 0xffcf96, fill: 0x8fa07e,
              props: 'forest', horizon: 0.63, grain: 0.7 },
    // grey scree over warm dust: the field is stone, the worn centre is the pale
    // grit that gets kicked loose, and the mottle is coarse
    crag:   { ground: 0x7c766c, ground2: 0xa9a396, dirt: 0xc0b49c, rock: 0x9d8f7f,
              haze: 0xdfcdbe, sky: 0xd3c3b6, key: 0xffd6a0, fill: 0xa9b7cc,
              props: 'crag', horizon: 0.56, grain: 1.0 },
    // dry pale gravel with damp DARKER patches where the water reaches
    water:  { ground: 0xa6a186, ground2: 0xc2bda1, dirt: 0x6f7566, rock: 0x8d9490,
              haze: 0xe4dcd0, sky: 0xd8c9bd, key: 0xffe0bb, fill: 0xa8c6d6,
              props: 'water', horizon: 0.60, grain: 0.85 },
    default:{ ground: 0x7f7663, ground2: 0x968c77, dirt: 0x8d8064, rock: 0x8d8577,
              haze: 0xdfd0b4, sky: 0xcdbfa8, key: 0xffd9a8, fill: 0x9fb6d8,
              props: 'meadow', horizon: 0.58, grain: 0.62 },
  };

  // ===== THE MONSTER SCALE TABLE ============================================
  // A target HEIGHT IN METRES per monster, measured against charH 1.7 — the
  // loader measures whatever bounding box the sourced GLB happens to have and
  // scales uniformly to hit this, so a CC0 pack's arbitrary units never leak
  // into the composition (the sourced set ranges from 1.4 to 3.2 in its own
  // units for creatures that must read as 0.7 m to 2.0 m tall). `y` lifts a
  // floater off the ground; `bob` is the idle breathe amplitude in metres;
  // `wide` fattens the blob shadow for a squat body; `yaw` corrects a pack whose
  // model faces a different axis from the rest (recorded per file in the
  // monsters/3d MANIFEST — reed-nibbler is the odd one out at +X).
  const MON = {
    'reed-nibbler': { h: 0.72, bob: 0.05, y: 0, yaw: -Math.PI / 2, wide: 1.2 },
    // A WISP IS LIGHT, AND LIGHT IS NOT A MESH YOU CAN BUY. The sourced CC0
    // ghost is a bare white blob with eyes: tinting it made it a blue blob with
    // eyes, which reads as a cute monster, not as a spirit on the water. So this
    // one slot is BUILT (`build:'wisp'`) — an emissive core inside two soft
    // additive shells — and the ghost GLB stays on disk as its documented
    // fallback. World canon: Heartlights are the rare magical ones; a brook
    // sprite is the small wild kind, so it glows cool and dim, not warm.
    'brook-sprite': { h: 1.0, bob: 0.16, y: 0.62, float: true, build: 'wisp' },
    'duskpad':      { h: 1.05, bob: 0.045, y: 0, wide: 1.25 },
    'bramble-shade':{ h: 1.95, bob: 0.06, y: 0 },
    'scree-shell':  { h: 1.0, bob: 0.035, y: 0, wide: 1.55 },
    'weir-eel':     { h: 1.5, bob: 0.08, y: 0 },
    default:        { h: 1.3, bob: 0.06, y: 0 },
  };
  // The PROXY SOLID palette — tier 4, the 3D translation of the DOM stage's CSS
  // silhouettes. Keyed by monsters.json `family` exactly like battle_turnbased's
  // `sprites` table, so a new monster of a known family needs no entry anywhere.
  const PROXY = {
    nibbler: { c: 0xc8b877, c2: 0x6c5f34, shape: 'blob' },
    sprite:  { c: 0xbfe9f2, c2: 0x3f8ea6, shape: 'orb', glow: true },
    duskpad: { c: 0x8b7f92, c2: 0x413a4c, shape: 'quad' },
    shade:   { c: 0x6a5a78, c2: 0x2c2436, shape: 'spike' },
    shell:   { c: 0xc3a173, c2: 0x6b4f31, shape: 'dome' },
    eel:     { c: 0x79c9ae, c2: 0x2f6a58, shape: 'coil' },
    default: { c: 0xa2957f, c2: 0x4b4237, shape: 'blob' },
  };

  // ===== ASSET CONVENTIONS ==================================================
  // Same idiom as battle_turnbased's `art`: a base + a directory + an extension,
  // with an override map for exceptions. Nothing enumerates monsters or zones.
  const art = {
    base: 'assets/',
    modelDir: 'monsters/3d/',            // tier 1 — CC0 GLBs
    plateDir: 'monsters/',               // tier 2 — hi-res billboard plates (future)
    spriteDir: 'monsters/placeholder/',  // tier 3 — the pixel sprites we ship today
    battleDir: 'battle/',                // the backdrop plates
    // THE REAL CAST (2026-08-02). Until today the WHOLE PARTY was one borrowed
    // CC0 KayKit rogue with a dye tint: three identical green hooded chibis
    // standing under three different painted busts in the status panel. The
    // shipped cast are retargeted, gated rigs under
    // assets/characters/<name>/<name>-vN.glb, and these are the SAME FILES
    // play3d.html's MODELS registry hands the overworld — the arena and the
    // world must never be two different people. That registry is coordinator
    // custody and is READ, not edited, from here; this table mirrors it.
    //
    // A VALUE MAY BE A LIST, newest first, and the first URL that PARSES wins.
    // That is not decoration: the character factory versions its deliveries
    // (`-v1`, `-v2`) and a lane can be mid-retarget while a battle runs, so a
    // rig that has not landed yet must cost a silent 404 rather than a hole.
    models: {
      vesper: ['assets/characters/vesper/vesper-v2.glb', 'assets/characters/vesper/vesper.glb'],
      maren:  ['assets/characters/maren/maren-v1.glb',   'assets/characters/maren/maren.glb'],
      lake:   ['assets/characters/lake/lake-v1.glb',     'assets/characters/lake/lake.glb'],
    },
    // NOBODY'S BODY IS A BORROWED ROGUE ANY MORE. This was
    // 'assets/characters3d/rogue.glb' and it was every party member's tier-1
    // model; a character with no rig of their own now falls to THEIR OWN
    // painted pose plate (the ruled 2D-in-3D billboard) and then to the
    // mannequin, because wrong-identity geometry is worse than correct art.
    // Set it back to a URL and the generic body returns, one word, no logic.
    charModel: null,
    // DYE IS FOR A BORROWED MODEL, and it retires the moment a character owns
    // their own textures — tinting Maren's real rig would just soil it. Kept as
    // the mechanism (a future palette-swap enemy ally, a status effect) with
    // nothing in it.
    tint: {},
    // Per-character height in metres, against CFG.charH for anyone absent. The
    // cast are not all one size and the arena is where that reads.
    height: {},
    // WHICH BODY THE PARTY PREFERS. 'model' = the character's own rig first, the
    // chroma-keyed pose plate as its fallback. 'billboard' = the painterly plate
    // first, the rig as ITS fallback. Both paths are the same two tiers in the
    // other order and both are shipped and photographed; this is the whole of
    // the switch, because the ruling on which one is the game's look is the
    // user's to make.
    partyBody: 'model',
  };
  // KILL SWITCHES — this is how the fallback chain is VERIFIED rather than
  // asserted. Set any of these and the tier below takes over on the next battle.
  const disable = { partyModel: false, foeModel: false, billboard: false, plate: false };

  const cleanId = s => String(s == null ? '' : s).replace(/[^a-z0-9_-]/gi, '');
  const modelUrl = id => (disable.foeModel ? null : art.base + art.modelDir + cleanId(id) + '.glb');
  const spriteUrls = (id) => {
    if (disable.billboard) return [];
    const k = cleanId(id);
    return [art.base + art.plateDir + k + '.png', art.base + art.spriteDir + k + '.png'];
  };

  // ===== CAPABILITY PROBE ===================================================
  let probed = null;
  function available() {
    if (probed !== null) return probed;
    probed = false;
    if (!HAS_DOM) return false;
    const TH = T();
    if (!TH || !TH.WebGLRenderer || !TH.GLTFLoader) return false;
    try {
      const c = document.createElement('canvas');
      const gl = c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) return false;
      const lose = gl.getExtension('WEBGL_lose_context');
      if (lose) { try { lose.loseContext(); } catch (e) { } }
      probed = true;
    } catch (e) { probed = false; }
    return probed;
  }
  function reducedMotion() {
    try { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); }
    catch (e) { return false; }
  }

  // ---- COLOUR SPACE --------------------------------------------------------
  // The renderer writes sRGB (outputEncoding), but three r128 has no colour
  // management: a hex handed to THREE.Color is taken as ALREADY LINEAR and then
  // gamma-encoded on the way out, so #5e4d31 — a dark forest brown — leaves the
  // pipe as a pale tan. Every palette hex in this file is authored as the colour
  // you want to SEE, so every one of them goes through here. Getting this wrong
  // is what turns a zone-tinted clearing into one flat orange pancake.
  const _cc = Object.create(null);
  function C(hex) {
    if (_cc[hex]) return _cc[hex].clone();
    const c = new (T().Color)(hex);
    if (c.convertSRGBToLinear) c.convertSRGBToLinear();
    _cc[hex] = c;
    return c.clone();
  }

  // ===== TINY PROCEDURAL TEXTURES ===========================================
  // Two canvases, generated once and shared: the blob shadow and the mist band.
  // No files, no fetches, no failure mode.
  let shadowTex = null, mistTex = null, dotTexture = null;
  // The one sprite every particle in the arena uses: a soft round dot. Shared
  // module-wide and deliberately NOT disposed with a battle (destroy() skips it
  // by identity), because the next battle wants exactly the same 64 px canvas.
  function dotTex() {
    const TH = T();
    if (dotTexture) return dotTexture;
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d');
    const rg = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    rg.addColorStop(0, 'rgba(255,255,255,1)');
    rg.addColorStop(0.35, 'rgba(255,255,255,0.72)');
    rg.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = rg; g.fillRect(0, 0, 64, 64);
    dotTexture = new TH.CanvasTexture(c);
    return dotTexture;
  }
  function blobShadow() {
    const TH = T();
    if (shadowTex) return shadowTex;
    const c = document.createElement('canvas'); c.width = c.height = 128;
    const g = c.getContext('2d');
    const rg = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    rg.addColorStop(0, 'rgba(0,0,0,0.62)');
    rg.addColorStop(0.45, 'rgba(0,0,0,0.36)');
    rg.addColorStop(0.78, 'rgba(0,0,0,0.10)');
    rg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = rg; g.fillRect(0, 0, 128, 128);
    shadowTex = new TH.CanvasTexture(c);
    return shadowTex;
  }
  function mistBand() {
    const TH = T();
    if (mistTex) return mistTex;
    const c = document.createElement('canvas'); c.width = 4; c.height = 128;
    const g = c.getContext('2d');
    const lg = g.createLinearGradient(0, 0, 0, 128);          // v=0 is the BOTTOM once flipY applies
    lg.addColorStop(0, 'rgba(255,255,255,0)');                // top of the band: clear
    lg.addColorStop(0.42, 'rgba(255,255,255,0.30)');
    lg.addColorStop(0.72, 'rgba(255,255,255,0.72)');
    lg.addColorStop(1, 'rgba(255,255,255,0.92)');             // bottom: dense, buried by the ground
    g.fillStyle = lg; g.fillRect(0, 0, 4, 128);
    mistTex = new TH.CanvasTexture(c);
    return mistTex;
  }

  // ---- value noise, for the ground's mottle and bumps ------------------------
  function mkNoise(seed) {
    let s = (seed >>> 0) || 1;
    const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
    const G = 64, tab = new Float32Array(G * G);
    for (let i = 0; i < tab.length; i++) tab[i] = rnd();
    const at = (x, y) => tab[((y & (G - 1)) * G) + (x & (G - 1))];
    return function (x, y) {                                   // bilinear value noise
      const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
      const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
      return lerp(lerp(at(xi, yi), at(xi + 1, yi), u), lerp(at(xi, yi + 1), at(xi + 1, yi + 1), u), v);
    };
  }

  // ===== GLB LOADING ========================================================
  // One fetch per URL, then a FRESH PARSE per instance. That is deliberate:
  // three r128 ships no SkeletonUtils here, and a naive Object3D.clone() of a
  // skinned mesh shares the skeleton, so two party members would share one pose.
  // Re-parsing a cached ArrayBuffer gives an independent rig for the price of a
  // parse — and the fetch, which is the expensive half, happens exactly once.
  const bufCache = Object.create(null);
  function glbBuffer(url) {
    if (bufCache[url]) return bufCache[url];
    return (bufCache[url] = (typeof fetch === 'function'
      ? fetch(url).then(r => (r.ok ? r.arrayBuffer() : null)).catch(() => null)
      : Promise.resolve(null)));
  }
  function loadGlb(url) {
    if (!url) return Promise.resolve(null);
    return glbBuffer(url).then(buf => {
      if (!buf) return null;
      return new Promise((res) => {
        try { new (T().GLTFLoader)().parse(buf.slice(0), '', g => res(g || null), () => res(null)); }
        catch (e) { res(null); }
      });
    }).catch(() => null);
  }
  // A GLB probe down a list of candidate URLs; resolves the first that PARSES.
  // A 404 and a corrupt file are the same answer here — "not this one, try the
  // next" — which is what lets a versioned delivery (`-v2` today, `-v3` next
  // week) be authored as a preference list instead of a deploy step.
  function loadFirstGlb(urls) {
    const list = (Array.isArray(urls) ? urls : [urls]).filter(Boolean);
    if (!list.length) return Promise.resolve(null);
    return list.reduce((p, u) => p.then(g => (g ? g : loadGlb(u))), Promise.resolve(null));
  }
  // An <img> probe down a list of candidate URLs; resolves the first that decodes.
  function probeImage(urls) {
    return new Promise((res) => {
      let i = 0;
      const next = () => {
        if (i >= urls.length || typeof Image !== 'function') return res(null);
        const im = new Image();
        im.onload = () => res(im);
        im.onerror = () => { i++; next(); };
        im.src = urls[i];
      };
      next();
    });
  }

  // ===== FORMATIONS =========================================================
  // THE SINGLE ROW IS THE THING BEING KILLED. Party: an offset column, each
  // member a step right and a step back — FF's staggered depth, so two bodies
  // never share a screen-space line. Foes: a zigzag when there are few, two
  // staggered ranks when there are many, the back rank pushed away from camera
  // AND jogged sideways so nobody is hidden behind anybody.
  const partySide = () => (CFG.partySide < 0 ? -1 : 1);
  const foeSide = () => -partySide();
  function partySlots(n) {
    const f = CFG.form, out = [], mid = (n - 1) / 2, S = partySide();
    // Each member one step FURTHER FROM THE ENEMY and one step nearer the camera
    // than the one in front of her, so no two party bodies share a screen column.
    // The x is a magnitude times the side, which is what makes the mirror one sign.
    for (let i = 0; i < n; i++) {
      out.push([S * (f.partyX + (i - mid) * f.partyDx), f.partyZ + (i - mid) * f.partyDz]);
    }
    return out;
  }
  function foeSlots(n) {
    const f = CFG.form, out = [], mid = (n - 1) / 2;
    // A CHEVRON, not a parity zigzag. Parity put slot 1 and slot 2 on nearly the
    // same screen ray from this camera and one monster stood inside another; a
    // chevron pushes the middle of the line at the party and the ends back, so
    // depth separation and screen separation grow together.
    const S = foeSide();
    if (n === 1) return [[S * f.foeX, f.foeZ]];
    if (n <= 3) {
      // Chevron (middle of the line pushed at the party) PLUS an alternating
      // sideways jog. The jog is what actually pulls neighbours apart: the depth
      // spread separates them vertically but leaves two identical slimes in the
      // same screen COLUMN, one behind the other.
      //
      // AT n=2 THE CHEVRON CONTRIBUTES NOTHING — |i - mid| is 0.5 for both slots,
      // so it shifts them by the same amount and the jog is working alone. It
      // therefore gets a boost there, which the two-monster case can afford
      // because there is no third body to make room for. Two foes is also the
      // commonest encounter shape in encounters.json, so this is the case that
      // has to read best, not the one that can be left to the tie-breakers.
      // THE JOG MUST ALTERNATE AGAINST THE DEPTH, AND THAT IS WHY IT CARRIES THE
      // SIDE. Screen-x is roughly `a*x + b*z`, and the sign of b is tied to the
      // sign of the camera yaw — so mirroring the arena flips whether the jog and
      // the depth spread ADD or CANCEL. Left unfixed, the mirror turned a 1.23 m
      // and 2.78 m pair of gaps into 1.81 m and 0.26 m: two monsters back inside
      // each other, the exact bug the jog was added to kill. Tying the jog to
      // partySide keeps every separation identical under the flip.
      const jog = f.foeJog * (n === 2 ? 1.7 : 1) * partySide();
      for (let i = 0; i < n; i++) {
        // the chevron PUSHES THE MIDDLE AT THE PARTY, so it shrinks the magnitude
        out.push([S * (f.foeX + Math.abs(i - mid) * f.foeChevron) + (i % 2 ? jog : -jog),
                  f.foeZ + (i - mid) * f.foeSpread]);
      }
      return out;
    }
    const front = Math.ceil(n / 2), back = n - front;
    const sp = f.foeSpread * 0.82;                  // two ranks can pack a little tighter
    for (let i = 0; i < front; i++) out.push([S * f.foeX, f.foeZ + (i - (front - 1) / 2) * sp]);
    for (let i = 0; i < back; i++) out.push([S * (f.foeX + f.foeRank), f.foeZ + (i - (back - 1) / 2) * sp + f.foeJog * partySide()]);
    return out;
  }

  // ===== THE STAGE ==========================================================
  // cfg = {
  //   mount        element to append the canvas to (the battle root)
  //   zone         zone key (palette + props)
  //   backdrop     plate key (assets/battle/<key>.png)
  //   party, foes  [{id, ref, name, dead}]  — ref is the charId / monsterId
  //   familyOf(monsterId) -> family    (for the proxy solid)
  //   onFrame(stage)                   (the screen re-projects its DOM anchors)
  // }
  function create(cfg) {
    if (!available()) return null;
    const TH = T();
    cfg = cfg || {};
    const RM = cfg.reducedMotion != null ? cfg.reducedMotion : reducedMotion();
    const zone = ZONES[cfg.zone] || ZONES[cfg.backdrop] || ZONES.default;
    const mount = cfg.mount || document.body;

    // ---- renderer -----------------------------------------------------------
    let renderer;
    try {
      // preserveDrawingBuffer is what makes stage.snapshot() — and every headless
      // screenshot in docs/qa/battle3d — possible; the cost is a buffer readback
      // per frame ("GPU stall due to ReadPixels" in a swiftshader log). In a
      // turn-based battle that trade is worth making, and CFG.snapshots = false
      // takes it back for anyone who disagrees.
      renderer = new TH.WebGLRenderer({ antialias: true, alpha: false,
                                        preserveDrawingBuffer: CFG.snapshots !== false });
    } catch (e) { return null; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    if (TH.sRGBEncoding !== undefined) renderer.outputEncoding = TH.sRGBEncoding;
    renderer.setClearColor(zone.sky, 1);
    // SHADOWS. Soft-PCF, and every failure mode here is a silent one — an old
    // driver that refuses a depth texture must cost the arena a shadow, never a
    // battle. The whole block is therefore guarded and the rest of the file
    // never asks whether it worked.
    try {
      if (CFG.shadow.on) {
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = TH.PCFSoftShadowMap;
      }
    } catch (e) { }
    const canvas = renderer.domElement;
    canvas.className = 'ebb-gl';
    canvas.setAttribute('aria-hidden', 'true');
    mount.appendChild(canvas);

    const scene = new TH.Scene();
    scene.fog = new TH.Fog(C(zone.haze), CFG.fogNear, CFG.fogFar);
    const camera = new TH.PerspectiveCamera(CFG.cam.fov, 16 / 9, CFG.cam.near, CFG.cam.far);

    // ---- the rest camera pose ----------------------------------------------
    const target = new TH.Vector3().fromArray(CFG.cam.target);
    function camPose(dist, pitch, yaw) {
      const hz = dist * Math.cos(pitch * D2R);
      return new TH.Vector3(
        target.x + hz * Math.sin(yaw * D2R),
        target.y + dist * Math.sin(pitch * D2R),
        target.z + hz * Math.cos(yaw * D2R));
    }
    // THE CAMERA YAWS TOWARD THE PARTY'S SIDE, whichever side that is. That is
    // what keeps the monsters — the things the player aims at — reading frontally
    // and the party three-quarter-rear, and it is why the yaw is a magnitude
    // times the side rather than a signed constant that a mirror would silently
    // point the wrong way. The intro sweep leans the same way for the same reason.
    const camYaw = CFG.cam.yawMag * partySide();
    const introYaw = camYaw + CFG.intro.yawMag * partySide();
    const restPos = camPose(CFG.cam.dist, CFG.cam.pitch, camYaw);
    const introPos = camPose(CFG.cam.dist * CFG.intro.dist,
                             CFG.cam.pitch + CFG.intro.pitch, introYaw);
    camera.position.copy(restPos);
    camera.lookAt(target);

    // ---- light: golden hour, matching the canon and play3d's own rig --------
    // Total intensity is kept UNDER ~1.0 on the lit side on purpose: a Lambert
    // surface driven past 1 clips its albedo to white, which is exactly what
    // turns a zone-tinted clearing into one flat tan pancake.
    // THE AMBIENT COMES DOWN BECAUSE A SOURCE WENT UP. The rim adds ~0.09 to a
    // level floor and the grade adds contrast on top of that; left at 0.50 the
    // hemisphere blew the ground out and the cast read as dark cut-outs against
    // it. 0.44 / 0.12 is the same total on the LIT side with the floor a stop
    // down, which is what lets a character hold the frame.
    const hemi = new TH.HemisphereLight(C(zone.sky), C(zone.ground), 0.44);
    scene.add(hemi);
    const key = new TH.DirectionalLight(C(zone.key), 0.86);
    key.position.set(-7, 9, -4.5);                    // raking from the upper LEFT-BACK
    scene.add(key);
    // THE SHADOW CAMERA WRAPS THE FIGHT, NOT THE CLEARING. The formations live
    // inside ~7 m of the origin; an ortho box sized to the 20 m ground would put
    // ~90 % of a 2048 map on grass nobody looks at and hand the bodies a soft
    // grey mush instead of a shadow. `target` must be IN THE SCENE or three
    // leaves its matrix un-updated and the whole map points at the world origin
    // from wherever the light last was.
    try {
      if (CFG.shadow.on) {
        const S = CFG.shadow;
        key.castShadow = true;
        key.shadow.mapSize.set(S.map, S.map);
        const c = key.shadow.camera;
        c.left = -S.size; c.right = S.size; c.top = S.size; c.bottom = -S.size;
        c.near = 0.5; c.far = 40;
        c.updateProjectionMatrix();
        key.shadow.bias = S.bias;
        if ('normalBias' in key.shadow) key.shadow.normalBias = S.normalBias;
        key.shadow.radius = S.radius;
        key.target.position.set(0, 0.6, 0);
        scene.add(key.target);
      }
    } catch (e) { console.warn('[stage3d] shadows unavailable', e); }
    const fill = new TH.DirectionalLight(C(zone.fill), 0.22);
    fill.position.set(6, 4, 7);
    scene.add(fill);
    // THE RIM, from behind the formations and almost level with them — see
    // CFG.rim for why the elevation is the whole design. Its colour is the
    // zone's own key pushed toward white so a backlit edge reads as SUN rather
    // than as a second coloured lamp.
    if (CFG.rim.on) {
      const rc = C(zone.key); rc.lerp(new TH.Color(1, 1, 1), 0.35);
      const rim = new TH.DirectionalLight(0xffffff, CFG.rim.intensity);
      rim.color.copy(rc);
      rim.position.set(CFG.rim.pos[0] * partySide(), CFG.rim.pos[1], CFG.rim.pos[2]);
      scene.add(rim);
    }
    scene.add(new TH.AmbientLight(0xffffff, 0.12));

    // ---- THE GROUND: a dished clearing --------------------------------------
    // A radial grid, not a square plane: the rim is a circle, so the silhouette
    // where it meets the backdrop is an even arc rather than four corners.
    const noise = mkNoise(0x9e37);
    // ONE closed form for the surface height, used BOTH to build the mesh and to
    // seat every combatant, prop and blob shadow on it. Two copies of this
    // formula drift the moment one is tuned, and the symptom is bodies hovering
    // a few centimetres over their own shadows.
    function groundY(x, z) {
      const g = CFG.ground, R = g.radius;
      const r = Math.min(Math.sqrt(x * x + z * z), R);
      // Three octaves, all at wavelengths this grid can actually resolve. The
      // rings crowd toward the centre (r = rr²R), so near the fight the spacing
      // is ~0.2 m and a 1 m feature reads; at the rim it is ~1.4 m and only the
      // slow swell survives — which is right, because the rim is what dissolves
      // into the plate.
      const n1 = noise(x * 0.17 + 40, z * 0.17 + 40);   // slow swells
      const n2 = noise(x * 0.55 + 7, z * 0.55 + 7);     // patchiness
      const n3 = noise(x * 1.15 + 91, z * 1.15 + 91);   // grain
      const dish = g.dish * (r / R) * (r / R);
      const bump = ((n1 - 0.5) * 1.3 + (n2 - 0.5) * 0.6 + (n3 - 0.5) * 0.32) * g.bump *
                   Math.min(1, r / 2.6 + 0.3);          // flattest where they stand
      return dish + bump;
    }
    function buildGround() {
      const g = CFG.ground, R = g.radius;
      const pos = [], col = [], idx = [];
      const cBase = C(zone.ground), cAlt = C(zone.ground2), cDirt = C(zone.dirt);
      const tmp = new TH.Color();
      for (let ri = 0; ri <= g.rings; ri++) {
        const rr = (ri / g.rings);
        const r = rr * rr * R;                        // denser rings near the centre, where the fight is
        for (let si = 0; si <= g.segs; si++) {
          const a = (si / g.segs) * Math.PI * 2;
          const x = Math.cos(a) * r, z = Math.sin(a) * r;
          const n1 = noise(x * 0.17 + 40, z * 0.17 + 40);   // slow swells
          const n2 = noise(x * 0.55 + 7, z * 0.55 + 7);     // patchiness
          const n3 = noise(x * 1.15 + 91, z * 1.15 + 91);   // grain
          pos.push(x, groundY(x, z), z);
          // THE CENTRE IS TRODDEN. A bare, paler dirt patch under the combatants
          // grading out to the zone's ground colour — the thing that makes a
          // clearing read as a place people fight in rather than a green disc.
          // Its edge is broken by the patch noise so it is never a drawn circle.
          const wear = clamp(1 - (r + (n2 - 0.5) * 3.6) / 6.6, 0, 1);
          tmp.copy(cBase).lerp(cAlt, clamp(n2 * 1.7 - 0.3, 0, 1));
          tmp.lerp(cDirt, clamp(wear * 1.3, 0, 0.9));
          const gr = zone.grain != null ? zone.grain : 0.62;
          const shade = (1 - gr * 0.62) + n3 * gr + n1 * 0.2;   // grain + the swells' shading
          col.push(tmp.r * shade, tmp.g * shade, tmp.b * shade);
        }
      }
      // WINDING MATTERS AND IT BIT ONCE. The ring runs +X toward +Z as si grows
      // and radius grows with ri, so (a, c, b) puts the normal at -Y: the whole
      // floor is back-face culled and you spend an hour tuning a plate you think
      // is the ground. (a, b, c) faces +Y. computeVertexNormals then agrees.
      const row = g.segs + 1;
      for (let ri = 0; ri < g.rings; ri++) {
        for (let si = 0; si < g.segs; si++) {
          const a = ri * row + si, b = a + 1, c = a + row, d = c + 1;
          idx.push(a, b, c, b, d, c);
        }
      }
      const geo = new TH.BufferGeometry();
      geo.setAttribute('position', new TH.Float32BufferAttribute(pos, 3));
      geo.setAttribute('color', new TH.Float32BufferAttribute(col, 3));
      geo.setIndex(idx);
      geo.computeVertexNormals();
      const m = new TH.Mesh(geo, new TH.MeshLambertMaterial({ vertexColors: true }));
      m.renderOrder = 1;
      m.receiveShadow = true;                       // THE floor the cast shadows land on
      return m;
    }
    const ground = buildGround();
    scene.add(ground);
    const rimY = CFG.ground.dish;

    // ---- THE BACKDROP BAND --------------------------------------------------
    // Curved around the CAMERA, not the world — see CFG.backdrop. The plate's
    // horizon row is pinned to where the ground's far rim projects at backdrop
    // distance, which is what "generated with awareness of the 3D model" buys:
    // the painted horizon lands exactly on the 3D silhouette.
    // THE REST POSE, CAPTURED ONCE. The band is rebuilt whenever the plate
    // decodes or the window aspect changes — both of which land at arbitrary
    // moments, typically MID INTRO-SWEEP, when the live camera is metres from
    // where it will settle. Reading the live camera there would pin the painted
    // horizon to a pose that no longer exists a beat later, non-deterministically.
    const restDir = new TH.Vector3(target.x - restPos.x, 0, target.z - restPos.z).normalize();
    const restRight = new TH.Vector3(-restDir.z, 0, restDir.x);
    function backdropGeo(dist, halfArc, plateAspect, horizonFrac) {
      const f = restDir, r = restRight, P = restPos;
      // where the ground's far rim projects onto the backdrop, along the view ray
      const distToRim = Math.sqrt(P.x * P.x + P.z * P.z) + CFG.ground.radius;
      const horizonY = P.y - dist * (P.y - rimY) / Math.max(1, distToRim);
      const W = 2 * dist * Math.sin(halfArc);
      const H = W / plateAspect;
      const yTop = horizonY + horizonFrac * H, yBot = yTop - H;
      const N = CFG.backdrop.segs, M = 6;
      const pos = [], uv = [], idx = [];
      for (let i = 0; i <= N; i++) {
        const s = (i / N) * 2 - 1, a = s * halfArc;
        const dx = f.x * Math.cos(a) + r.x * Math.sin(a);
        const dz = f.z * Math.cos(a) + r.z * Math.sin(a);
        const px = P.x + dist * dx, pz = P.z + dist * dz;
        for (let j = 0; j <= M; j++) {
          const v = j / M;
          pos.push(px, lerp(yBot, yTop, v), pz);
          uv.push(i / N, v);
        }
      }
      for (let i = 0; i < N; i++) for (let j = 0; j < M; j++) {
        const a = i * (M + 1) + j, b = a + 1, c = a + M + 1, d = c + 1;
        idx.push(a, c, b, b, c, d);
      }
      const geo = new TH.BufferGeometry();
      geo.setAttribute('position', new TH.Float32BufferAttribute(pos, 3));
      geo.setAttribute('uv', new TH.Float32BufferAttribute(uv, 2));
      geo.setIndex(idx);
      return { geo, horizonY, W, H };
    }
    const halfFovV = (CFG.cam.fov / 2) * D2R;
    let halfArc = Math.atan(Math.tan(halfFovV) * (16 / 9)) * CFG.backdrop.arcPad;
    let backdrop = null, backdropInfo = null, mistMesh = null;
    // Called again whenever the plate decodes or the window aspect changes, so
    // BOTH meshes have to be torn down or a resize storm plants a new haze band
    // every frame.
    function mountBackdrop(aspect, map) {
      if (backdrop) { scene.remove(backdrop); backdrop.geometry.dispose(); backdrop.material.dispose(); }
      if (mistMesh) { scene.remove(mistMesh); mistMesh.geometry.dispose(); mistMesh.material.dispose(); }
      const hz = cfg.horizon != null ? cfg.horizon
               : zone.horizon != null ? zone.horizon : CFG.backdrop.horizon;
      const b = backdropGeo(CFG.backdrop.dist, halfArc, aspect, hz);
      backdropInfo = b;
      const mat = map
        ? new TH.MeshBasicMaterial({ map: map, fog: false, side: TH.DoubleSide, depthWrite: false })
        : new TH.MeshBasicMaterial({ color: C(zone.sky), fog: false, side: TH.DoubleSide, depthWrite: false });
      backdrop = new TH.Mesh(b.geo, mat);
      backdrop.renderOrder = -10;                     // painted first; never occludes anything
      scene.add(backdrop);
      // THE SEAM: a soft haze band standing just in front of the plate at the
      // rim height. Fog already dissolves the ground's far edge into zone.haze;
      // this puts the same haze on the plate side of the join so the two grounds
      // meet in mist instead of in a line.
      const mb = backdropGeo(CFG.backdrop.dist - 1.4, halfArc * 0.995, aspect, 0);
      const mist = new TH.Mesh(mb.geo, new TH.MeshBasicMaterial({
        map: mistBand(), color: C(zone.haze), transparent: true, opacity: 0.62,
        fog: false, side: TH.DoubleSide, depthWrite: false,
      }));
      // squash the band down to a thin ribbon straddling the rim's projected line
      const p = mb.geo.attributes.position;
      for (let i = 0; i < p.count; i++) {
        const y = p.getY(i), u = (y - (mb.horizonY - mb.H)) / mb.H;   // 0..1 up the band
        p.setY(i, b.horizonY - 2.6 + u * 3.4);
      }
      p.needsUpdate = true;
      mist.renderOrder = -9;
      mistMesh = mist;
      scene.add(mist);
      return b;
    }
    mountBackdrop(16 / 9, null);                       // a flat sky until the plate decodes
    if (!disable.plate && cfg.backdrop) {
      const url = art.base + art.battleDir + cleanId(cfg.backdrop) + '.png';
      probeImage([url]).then((im) => {
        if (!im || dead) return;
        const tex = new TH.Texture(im);
        if (TH.sRGBEncoding !== undefined) tex.encoding = TH.sRGBEncoding;
        tex.minFilter = TH.LinearFilter; tex.generateMipmaps = false;
        tex.wrapS = tex.wrapT = TH.ClampToEdgeWrapping;
        tex.needsUpdate = true;
        mountBackdrop((im.naturalWidth || 16) / (im.naturalHeight || 9), tex);
      });
    }

    // ---- PROPS: 2-4 simple low-poly pieces per zone, built in code ----------
    // Deliberately SIMPLE — the ruling asks for "a very simple 3D model overlaid
    // on an arena background", and props that out-detail the plate would fight it.
    // Every prop is placed OUTSIDE the combat footprint (r > 6.5) or well behind
    // the formations, so nothing ever stands in front of a body.
    // FACETED, AND IT HAS TO BE PHONG TO BE FACETED. MeshLambertMaterial shades
    // per VERTEX in r128 and simply drops `flatShading` (with a console warning
    // per material), so every low-poly rock built with it came out smooth — the
    // one thing a low-poly rock must not be. Phong with shininess 0 is Lambert's
    // look, per fragment, and honours the flag.
    const flat = (c) => new TH.MeshPhongMaterial({ color: C(c), flatShading: true, shininess: 0 });
    function place(o, x, z, ry, s) {
      o.position.set(x, groundY(x, z), z);
      o.rotation.y = ry == null ? 0 : ry;
      if (s) o.scale.multiplyScalar(s);
      // A prop that neither casts nor receives is the give-away that the arena
      // is a diorama: rocks sat on the grass with no dark side and no shadow.
      o.traverse(n => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; } });
      scene.add(o);
      return o;
    }
    function rock(size, c) {
      const m = new TH.Mesh(new TH.DodecahedronGeometry(size, 0), flat(c));
      m.scale.set(1, 0.62 + Math.random() * 0.3, 0.86);
      m.rotation.set(Math.random() * 0.4, Math.random() * 6, Math.random() * 0.3);
      m.position.y = size * 0.28;
      const g = new TH.Group(); g.add(m); return g;
    }
    function log(len, rad, c) {
      const m = new TH.Mesh(new TH.CylinderGeometry(rad, rad * 0.86, len, 7, 1), flat(c));
      m.rotation.z = Math.PI / 2; m.rotation.x = 0.06; m.position.y = rad;
      const g = new TH.Group(); g.add(m); return g;
    }
    function tuft(h, c, n) {
      const g = new TH.Group();
      for (let i = 0; i < (n || 6); i++) {
        const b = new TH.Mesh(new TH.ConeGeometry(0.055, h * (0.6 + Math.random() * 0.7), 4), flat(c));
        b.position.set((Math.random() - 0.5) * 0.7, h * 0.35, (Math.random() - 0.5) * 0.7);
        b.rotation.z = (Math.random() - 0.5) * 0.5;
        g.add(b);
      }
      return g;
    }
    function stump(h, r, c) {
      const g = new TH.Group();
      const m = new TH.Mesh(new TH.CylinderGeometry(r, r * 1.2, h, 9, 1), flat(c));
      m.position.y = h / 2; g.add(m);
      const top = new TH.Mesh(new TH.CylinderGeometry(r * 0.98, r * 0.98, 0.06, 9), flat(0xc0a479));
      top.position.y = h; g.add(top);
      return g;
    }
    // SCATTER, WITH A NO-GO ZONE. The combat footprint — everything within 8 m of
    // the battle axis and anywhere nearer the camera than the party — stays clear,
    // so a prop can never stand in front of a body or in the lane a lunge travels.
    // Everything else is fair game, and the placement is random per battle: the
    // same meadow twice is the same arena wearing different weeds.
    function scatter(n, make) {
      let placed = 0, guard = 0;
      while (placed < n && guard++ < n * 30) {
        const a = Math.random() * 6.283, r = 7.5 + Math.random() * 11;
        const x = Math.cos(a) * r, z = Math.sin(a) * r;
        if (Math.abs(z) < 3.2 && Math.abs(x) < 9) continue;     // the fighting lane
        if (z > 5.5) continue;                                   // between camera and party
        place(make(), x, z, Math.random() * 6.283);
        placed++;
      }
    }
    const PROPS = {
      meadow(z) {
        place(rock(0.85, z.rock), -9.4, -5.2, 0.4);
        place(rock(0.55, z.rock), -8.0, -6.4, 1.9);
        place(log(3.4, 0.36, 0x8a7147), 9.2, -4.6, -0.5);
        scatter(22, () => tuft(0.85, z.ground2, 7));
      },
      forest(z) {
        place(stump(1.05, 0.72, 0x6b563a), -9.6, -5.0, 0.3);
        place(log(4.2, 0.42, 0x5f4c34), 9.0, -5.6, 0.35);
        place(rock(0.62, z.rock), 10.2, 3.4, 1.1);
        scatter(24, () => tuft(0.68, 0x4f6338, 5));
      },
      crag(z) {
        place(rock(1.6, z.rock), -10.4, -4.2, 0.7);
        place(rock(1.05, 0x8a8073), -9.0, -6.4, 2.3);
        place(rock(1.35, z.rock), 10.2, -4.4, 1.4);
        place(rock(0.7, 0x9a9080), 9.4, 4.2, 0.2);
        scatter(30, () => rock(0.13 + Math.random() * 0.18, 0x8f8677));   // scree
      },
      water(z) {
        place(log(2.8, 0.3, 0x8d8571), 9.6, -4.0, 0.9);        // driftwood
        place(rock(0.95, 0x7f8a86), -9.8, -4.6, 1.6);
        place(rock(0.5, 0x7f8a86), -8.4, -6.0, 0.4);
        scatter(26, () => tuft(1.55, 0x77894f, 8));            // reeds, tall and thin
      },
    };
    try { (PROPS[zone.props] || PROPS.meadow)(zone); } catch (e) { console.warn('[stage3d] props', e); }

    // ===== BODIES ============================================================
    const bodies = Object.create(null);
    const order = [];
    const mixers = [];
    const billboards = [];
    let dead = false;

    function newBody(id, side, x, z, facing) {
      const TH2 = T();
      const root = new TH2.Group();
      root.position.set(x, groundY(x, z), z);
      root.rotation.y = facing;
      const pivot = new TH2.Group();                  // lunge / knockback offsets live here
      root.add(pivot);
      const bob = new TH2.Group();                    // idle breathe lives here
      pivot.add(bob);
      scene.add(root);
      const sh = new TH2.Mesh(new TH2.PlaneGeometry(1, 1), new TH2.MeshBasicMaterial({
        map: blobShadow(), transparent: true, depthWrite: false, opacity: 0.85,
        color: 0x000000, fog: false,
      }));
      sh.rotation.x = -Math.PI / 2; sh.position.y = 0.035; sh.renderOrder = 2;
      root.add(sh);
      const b = {
        id, side, root, pivot, bob, shadow: sh, obj: null, mixer: null, actions: null,
        h: CFG.charH, w: 1, tier: 'proxy', home: root.position.clone(), facing,
        bobAmp: 0.05, bobPhase: Math.random() * 6.283, dead: false, ring: null,
        billboard: false, floatY: 0, mats: null, baseShadow: 0.85,
        flash: 0, emis: null, procT: 0, procKind: null,
      };
      bodies[id] = b; order.push(id);
      return b;
    }
    // swap in a visual, measure it, size the shadow, and remember where the head is
    function setVisual(b, obj, targetH, opt) {
      opt = opt || {};
      if (b.obj) { b.bob.remove(b.obj); disposeTree(b.obj); }
      // MEASURED BEFORE IT IS PARENTED. Box3.setFromObject walks world matrices,
      // so measuring after the add would fold the root's ground height and yaw
      // into min.y and seat every model a few centimetres into the dirt.
      const box = new (T().Box3)().setFromObject(obj);
      const sz = new (T().Vector3)(); box.getSize(sz);
      b.obj = obj; b.bob.add(obj);
      const h = sz.y || 1;
      if (targetH && h > 0.001 && !opt.noScale) {
        const k = targetH / h;
        obj.scale.multiplyScalar(k);
        obj.position.y -= box.min.y * k;               // seat its feet on the ground
        sz.multiplyScalar(k);
      } else if (!opt.noScale) { obj.position.y -= box.min.y; }
      b.h = targetH || h;
      b.w = Math.max(sz.x, sz.z) || b.h * 0.6;
      b.tier = opt.tier || b.tier;
      b.billboard = !!opt.billboard;
      // CAST. Set in the ONE place a body's geometry is ever swapped in, so no
      // tier can be half-lit: a proxy solid, a rig and a billboard all cast.
      // (A billboard's cast shadow is its plane's — a bottom-anchored cutout,
      // which is the right shadow for a cutout.)
      //
      // A LIGHT DOES NOT CAST A SHADOW. The `built` tier is reserved for
      // creatures that ARE light (the brook sprite), and giving the wisp a
      // shadow map put a hard dark ellipse on the shore a metre away from a
      // glowing spirit — measured in after-water, first pass. It keeps its soft
      // blob, which reads as the light it throws down, not as an occlusion.
      const casts = opt.tier !== 'built';
      obj.traverse((o) => {
        if (o.isMesh || o.isSkinnedMesh) { o.castShadow = casts; o.receiveShadow = true; }
      });
      // THE BLOB IS NOW CONTACT, NOT LIGHTING. With a real cast shadow on the
      // floor a full-strength blob under every body reads as two shadows from
      // two suns; dropped to ~0.34 it becomes the tight ambient-occlusion darkening
      // right at the feet that a shadow map at this texel density cannot resolve,
      // and it stays the ONLY grounding a body has if the driver refuses shadows.
      const sw = clamp(b.w * (opt.shadow || 1.5), 0.55, 3.4) * (CFG.shadow.on ? 0.72 : 1);
      b.shadow.scale.set(sw, sw * 0.62, 1);
      b.baseShadow = CFG.shadow.on ? (opt.float ? 0.30 : 0.44) : (opt.float ? 0.42 : 0.85);
      b.shadow.material.opacity = b.baseShadow;
      b.floatY = opt.floatY || 0;
      b.bob.position.y = b.floatY;
      collectMats(b);
    }
    // KHR_materials_unlit — half the sourced monster packs declare it, and three
    // r128 honours it by giving those meshes a MeshBasicMaterial. A fullbright
    // creature ignores the arena's key light AND its fog, so it floats on the
    // plate like a sticker while everything around it sits in golden hour. Every
    // basic material on a loaded creature is therefore re-homed onto Lambert,
    // keeping its map and colour. This is the one place a sourced asset's
    // authoring choice is overruled, and it is overruled for lighting alone.
    function relight(objRoot) {
      const TH2 = T();
      objRoot.traverse((o) => {
        if (!o.material) return;
        const ms = Array.isArray(o.material) ? o.material : [o.material];
        const out = ms.map((m) => {
          if (!m || !m.isMeshBasicMaterial) return m;
          const n = new TH2.MeshLambertMaterial({
            color: m.color ? m.color.clone() : 0xffffff, map: m.map || null,
            transparent: m.transparent, opacity: m.opacity, alphaTest: m.alphaTest,
            side: m.side, vertexColors: m.vertexColors, skinning: m.skinning,
          });
          return n;
        });
        o.material = Array.isArray(o.material) ? out : out[0];
      });
    }
    // DYE. Materials are cloned first, so tinting one instance of a model can
    // never bleed into another instance of the same file (they share materials
    // by construction after a parse). `glow` is emissive: the one lever that
    // makes a creature read as lit from inside rather than lit by the arena.
    function dye(objRoot, tint, glow) {
      objRoot.traverse((o) => {
        if (!o.material) return;
        const ms = Array.isArray(o.material) ? o.material : [o.material];
        const out = ms.map((m) => {
          const n = m.clone();
          if (tint != null && n.color) n.color.multiply(C(tint));
          if (glow != null && n.emissive) n.emissive.copy(C(glow));
          return n;
        });
        o.material = Array.isArray(o.material) ? out : out[0];
      });
    }
    function collectMats(b) {
      const list = [];
      if (b.obj) b.obj.traverse(o => { if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => list.push(m)); });
      b.mats = list;
      b.emis = null; b.flash = 0;   // the flash baseline belongs to THESE materials
    }
    function disposeTree(o) {
      o.traverse(n => {
        if (n.geometry) n.geometry.dispose();
        const ms = n.material ? (Array.isArray(n.material) ? n.material : [n.material]) : [];
        for (const m of ms) { if (m.map && m.map.__own) m.map.dispose(); m.dispose(); }
      });
    }
    function setOpacity(b, a) {
      if (!b.mats) return;
      for (const m of b.mats) { m.transparent = true; m.opacity = a; m.depthWrite = a > 0.9; }
      b.shadow.material.opacity = b.baseShadow * a;
    }
    // ---- THE HIT FLASH -------------------------------------------------------
    // A struck body goes hot for ~150 ms. It is done on `emissive` and not by
    // swapping in a white material, because emissive is additive on top of the
    // existing albedo: a dark monster and a pale hero both read as STRUCK rather
    // than both reading as white. MeshBasicMaterial has no emissive and is
    // skipped — the wisp is already light and cannot be made lighter.
    function flashOn(b, amount) {
      if (!b.mats) return;
      if (!b.emis) {
        b.emis = b.mats.map(m => (m && m.emissive ? m.emissive.clone() : null));
      }
      b.flash = amount;
      applyFlash(b);
    }
    function applyFlash(b) {
      if (!b.mats || !b.emis) return;
      for (let i = 0; i < b.mats.length; i++) {
        const m = b.mats[i], base = b.emis[i];
        if (!m || !m.emissive || !base) continue;
        m.emissive.setRGB(base.r + b.flash, base.g + b.flash * 0.94, base.b + b.flash * 0.82);
      }
    }

    // ---- BUILT BODIES: creatures no CC0 pack can supply ----------------------
    // A `build` entry in MON routes a slot here instead of down the asset chain.
    // Reserved for things that are LIGHT or FIELD rather than geometry, where
    // buying a mesh gets you the wrong idea of the creature no matter how well
    // it is textured. The GLB for the slot stays on disk as the documented
    // fallback and one deleted line puts it back in play.
    const BUILT = {
      wisp() {
        const TH2 = T();
        const g = new TH2.Group();
        // the core is the only thing with a hard edge, and it is small
        const core = new TH2.Mesh(new TH2.IcosahedronGeometry(0.17, 2),
          new TH2.MeshBasicMaterial({ color: C(0xf2fbff), fog: false }));
        core.position.y = 0.5;
        g.add(core);
        // two shells, additive and back-side so the far wall of each glows
        // through the near one — the cheap trick that reads as volume
        [[0.34, 0.4, 0x9fe6ff], [0.56, 0.16, 0x5fb9e0]].forEach(([r, o, c]) => {
          const sh = new TH2.Mesh(new TH2.IcosahedronGeometry(r, 2), new TH2.MeshBasicMaterial({
            color: C(c), transparent: true, opacity: o, blending: TH2.AdditiveBlending,
            depthWrite: false, side: TH2.BackSide, fog: false,
          }));
          sh.position.y = 0.5;
          g.add(sh);
        });
        // three motes orbiting the core, so it is never a static circle
        for (let i = 0; i < 3; i++) {
          const a = (i / 3) * 6.283;
          const m = new TH2.Mesh(new TH2.IcosahedronGeometry(0.045, 0),
            new TH2.MeshBasicMaterial({ color: C(0xcdf1ff), transparent: true, opacity: 0.8,
                                        blending: TH2.AdditiveBlending, depthWrite: false, fog: false }));
          m.position.set(Math.cos(a) * 0.42, 0.5 + Math.sin(a * 1.7) * 0.2, Math.sin(a) * 0.42);
          g.add(m);
        }
        return g;
      },
    };

    // ---- the party's proxy: a WOODEN FIGURE, not a ball -----------------------
    // The party's last tier is on screen for the ~200 ms before a 3.5 MB rig
    // parses, at the start of every single battle. A 1.7 m sphere in that slot
    // reads as a bug; a crude artist's mannequin reads as "she is arriving".
    function proxyFigure(tintC) {
      const TH2 = T();
      const g = new TH2.Group();
      const cloth = new TH2.MeshPhongMaterial({ color: C(tintC != null ? tintC : 0x6f8a63), flatShading: true, shininess: 0 });
      const skin = new TH2.MeshPhongMaterial({ color: C(0xd8b48c), flatShading: true, shininess: 0 });
      const add = (geo, m, x, y, z) => { const me = new TH2.Mesh(geo, m); me.position.set(x, y, z); g.add(me); return me; };
      add(new TH2.CylinderGeometry(0.2, 0.26, 0.62, 8), cloth, 0, 1.03, 0);   // torso
      add(new TH2.SphereGeometry(0.19, 10, 8), skin, 0, 1.47, 0);             // head
      for (const s of [-1, 1]) {
        add(new TH2.CylinderGeometry(0.075, 0.075, 0.5, 6), cloth, s * 0.26, 1.06, 0).rotation.z = s * 0.16;
        add(new TH2.CylinderGeometry(0.09, 0.08, 0.72, 6), cloth, s * 0.11, 0.36, 0);
      }
      return g;
    }

    // ---- tier 4: the proxy solid (the 3D translation of the CSS silhouette) --
    function proxySolid(family, tintC) {
      const TH2 = T();
      const d = PROXY[family] || PROXY.default;
      const g = new TH2.Group();
      const mA = new TH2.MeshPhongMaterial({ color: C(tintC != null ? tintC : d.c), flatShading: true, shininess: 0 });
      const mB = new TH2.MeshPhongMaterial({ color: C(d.c2), flatShading: true, shininess: 0 });
      const add = (geo, m, x, y, z, sx, sy, sz) => {
        const me = new TH2.Mesh(geo, m);
        me.position.set(x, y, z);
        if (sx) me.scale.set(sx, sy == null ? sx : sy, sz == null ? sx : sz);
        g.add(me); return me;
      };
      if (d.shape === 'orb') {
        add(new TH2.IcosahedronGeometry(0.5, 1), mA, 0, 0.5, 0);
        add(new TH2.IcosahedronGeometry(0.28, 0), mB, 0, 0.5, 0, 1.35, 1.35, 1.35);
      } else if (d.shape === 'quad') {                       // four legs, a body, a head
        add(new TH2.BoxGeometry(1.15, 0.5, 0.5), mA, 0, 0.62, 0);
        add(new TH2.BoxGeometry(0.36, 0.34, 0.36), mA, 0.68, 0.8, 0);
        for (const sx of [-0.42, 0.42]) for (const sz of [-0.18, 0.18])
          add(new TH2.BoxGeometry(0.14, 0.42, 0.14), mB, sx, 0.21, sz);
        add(new TH2.ConeGeometry(0.1, 0.5, 5), mB, -0.66, 0.78, 0).rotation.z = 1.1;
      } else if (d.shape === 'spike') {                      // a thicket: a trunk in a crown of spines
        add(new TH2.CylinderGeometry(0.22, 0.34, 0.9, 6), mB, 0, 0.45, 0);
        add(new TH2.IcosahedronGeometry(0.62, 0), mA, 0, 1.2, 0, 1, 1.15, 1);
        for (let i = 0; i < 7; i++) {
          const a = (i / 7) * 6.283;
          const s = add(new TH2.ConeGeometry(0.09, 0.7, 4), mA, Math.cos(a) * 0.42, 1.35, Math.sin(a) * 0.42);
          s.rotation.set(Math.sin(a) * 0.7, 0, -Math.cos(a) * 0.7);
        }
      } else if (d.shape === 'dome') {                       // a shell on stubby legs
        const s = add(new TH2.SphereGeometry(0.62, 12, 8, 0, 6.283, 0, Math.PI / 2), mA, 0, 0.3, 0, 1.15, 0.85, 1);
        s.material = mA;
        add(new TH2.BoxGeometry(1.28, 0.22, 0.9), mB, 0, 0.2, 0);
        add(new TH2.SphereGeometry(0.2, 8, 6), mB, 0.62, 0.26, 0);
      } else if (d.shape === 'coil') {                       // a serpent: a rising stack of rings
        for (let i = 0; i < 7; i++) {
          const t = i / 6;
          add(new TH2.TorusGeometry(0.44 - t * 0.24, 0.12, 6, 10), i % 2 ? mB : mA,
              Math.sin(t * 4) * 0.1, 0.14 + t * 0.72, 0).rotation.x = Math.PI / 2;
        }
        add(new TH2.ConeGeometry(0.17, 0.42, 6), mA, 0.14, 1.02, 0).rotation.z = -0.9;
      } else {                                               // 'blob'
        add(new TH2.SphereGeometry(0.5, 12, 9), mA, 0, 0.44, 0, 1.1, 0.86, 1);
        add(new TH2.SphereGeometry(0.2, 8, 6), mB, 0.3, 0.62, 0.16);
        add(new TH2.SphereGeometry(0.2, 8, 6), mB, 0.3, 0.62, -0.16);
      }
      if (d.glow) g.children[0].material = new TH2.MeshBasicMaterial({ color: C(d.c), fog: false });
      return g;
    }

    // ---- tier 2/3: a camera-facing billboard --------------------------------
    // THE RULED 2D-IN-3D PATH. A plane carrying the keyed plate, bottom-anchored,
    // yaw-only billboarded (it stays STANDING — a full billboard would lie down
    // as the camera pitches), with the same blob shadow as a model. Pixel art
    // gets NearestFilter so 16px sprites stay crisp instead of turning to soup.
    function billboardFrom(source, targetH, pixel) {
      const TH2 = T();
      const w = source.naturalWidth || source.width, h = source.naturalHeight || source.height;
      const tex = source instanceof HTMLCanvasElement ? new TH2.CanvasTexture(source) : new TH2.Texture(source);
      tex.__own = true;
      if (TH2.sRGBEncoding !== undefined) tex.encoding = TH2.sRGBEncoding;
      if (pixel || h <= 64) { tex.minFilter = tex.magFilter = TH2.NearestFilter; }
      else { tex.minFilter = TH2.LinearFilter; }
      tex.generateMipmaps = false;
      tex.needsUpdate = true;
      const pw = targetH * (w / h);
      const geo = new TH2.PlaneGeometry(pw, targetH);
      geo.translate(0, targetH / 2, 0);                     // bottom-anchored: feet at y=0
      const mat = new TH2.MeshBasicMaterial({
        map: tex, transparent: true, alphaTest: 0.28, side: TH2.DoubleSide,
      });
      const m = new TH2.Mesh(geo, mat);
      m.renderOrder = 4;
      const g = new TH2.Group(); g.add(m);
      return g;
    }

    // ---- clip picking (KayKit's library, by intent not by index) ------------
    const CLIP = {
      idle: ['Idle', 'Unarmed_Idle', '2H_Melee_Idle', 'Idle_A'],
      attack: ['1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Chop', 'Attack', 'Melee_Attack',
               'Unarmed_Melee_Attack_Punch_A', 'Attack_A', 'Bite_Front', 'Attack_Bite'],
      hit: ['Hit_A', 'Hit', 'Hit_B', 'HitRecieve', 'Take_Damage'],
      die: ['Death_A', 'Death', 'Die', 'Death_B'],
      item: ['Use_Item', 'PickUp', 'Interact'],
      cheer: ['Cheer', 'Victory'],
    };
    function pickClip(clips, kind) {
      if (!clips || !clips.length) return null;
      for (const want of CLIP[kind] || []) {
        const hit = clips.find(c => c.name === want);
        if (hit) return hit;
      }
      // a loose match, so a pack that names things its own way still lands
      const re = { idle: /idle/i, attack: /attack|bite|slash|swipe/i, hit: /hit|damage|flinch/i,
                   die: /death|die/i, item: /item|pick|interact/i, cheer: /cheer|victory|win/i }[kind];
      return (re && clips.find(c => re.test(c.name))) || null;
    }
    function rigUp(b, gltf) {
      const TH2 = T();
      const clips = gltf.animations || [];
      if (!clips.length) return;
      const mixer = new TH2.AnimationMixer(b.obj);
      mixers.push(mixer);
      b.mixer = mixer;
      b.actions = {};
      for (const kind of Object.keys(CLIP)) {
        const c = pickClip(clips, kind);
        if (!c) continue;
        const a = mixer.clipAction(c);
        if (kind !== 'idle') { a.setLoop(TH2.LoopOnce, 1); a.clampWhenFinished = kind === 'die'; }
        b.actions[kind] = a;
      }
      if (b.actions.idle) { b.actions.idle.play(); b.current = b.actions.idle; }
      if (b.actions.idle) b.actions.idle.time = Math.random() * 2;   // desync the party
    }
    // Play a one-shot and hand the body back to its idle. `hold` keeps the last
    // frame (death). The return is on a TIMER rather than the mixer's 'finished'
    // event because a hidden tab's rAF stops, the mixer never advances, and the
    // event would never fire — leaving a corpse mid-swing when the tab wakes.
    function oneShot(b, kind, hold) {
      if (!b.actions || !b.actions[kind]) return false;
      const a = b.actions[kind];
      const idle = b.actions.idle;
      // fit the donor's tempo to the turn's — see CFG.act.fit
      const raw = a.getClip().duration, want = CFG.act.fit[kind];
      const ts = (want && raw > 0)
        ? clamp(raw * 1000 / want, CFG.act.fitMin, CFG.act.fitMax) : 1;
      a.reset(); a.setEffectiveWeight(1); a.setEffectiveTimeScale(ts);
      a.fadeIn(0.08).play();
      if (idle && !hold) {
        idle.fadeOut(0.08);
        const dur = raw / ts;
        clearTimeout(b._backT);
        b._backT = setTimeout(() => {
          if (dead || b.dead) return;
          a.fadeOut(0.2);
          idle.reset().fadeIn(0.2).play();
        }, Math.max(140, dur * 1000 - 200));
      } else if (hold && idle) {
        idle.fadeOut(0.15);
      }
      return true;
    }

    // ---- BUILD THE CAST -----------------------------------------------------
    // THE RESOLUTION CHAIN, per combatant, best first. Every tier is built the
    // same way: the proxy solid goes up IMMEDIATELY (so the arena is never empty
    // and a slow network is never a hole), and a better tier replaces it the
    // moment it resolves. A tier that 404s is silent.
    //
    //   party  rogue.glb model -> pose-plate billboard -> proxy solid
    //   foe    monsters/3d GLB -> hi-res plate billboard -> pixel sprite billboard
    //          -> proxy solid
    //
    // The pixel-sprite tier is a BILLBOARD, not a DOM sprite: mixing a CSS shape
    // into a 3D scene would read as a bug. The DOM CSS-shape tier still exists —
    // it is what the whole DOM stage falls back to when this file cannot run.
    // STAGE BY HEIGHT. Slots are handed out tallest-creature-to-deepest-slot, so
    // a 1.95 m bramble-shade stands BEHIND the wolves rather than eclipsing one
    // — the oldest rule in stage blocking, and the cheapest legibility win here.
    // Group order is preserved everywhere else (names, targeting, turn order);
    // this only decides who stands where.
    const foeList = cfg.foes || [];
    const rawSlots = foeSlots(foeList.length);
    const farFirst = rawSlots.map((s, i) => i).sort((a, b) => rawSlots[a][1] - rawSlots[b][1]);
    const tallFirst = foeList.map((c, i) => i).sort((a, b) =>
      ((MON[foeList[b].ref] || MON.default).h) - ((MON[foeList[a].ref] || MON.default).h));
    const foeSlot = [];
    tallFirst.forEach((foeIdx, k) => { foeSlot[foeIdx] = rawSlots[farFirst[k]]; });
    foeList.forEach((c, i) => {
      const s = foeSlot[i] || [CFG.form.foeX, 0];
      // face ACROSS the arena at the party, turned a little toward the camera
      const b = newBody(c.id, 'foe', s[0], s[1], partySide() * (Math.PI / 2) + foeSide() * 0.22);
      const md = MON[c.ref] || MON.default;
      b.bobAmp = md.bob;
      const fam = cfg.familyOf ? cfg.familyOf(c.ref) : 'default';
      setVisual(b, proxySolid(fam), md.h, { tier: 'proxy', float: md.float, floatY: md.y,
                                           shadow: (md.wide || 1) * 1.5 });
      if (c.dead) markDead(b, true);
      // a BUILT body short-circuits the asset chain entirely — see BUILT
      if (md.build && BUILT[md.build]) {
        setVisual(b, BUILT[md.build](), md.h, { tier: 'built', float: true, floatY: md.y,
                                                shadow: (md.wide || 1) * 1.1, noScale: true });
        if (c.dead) markDead(b, true);
        return;
      }
      // tier 1
      loadGlb(modelUrl(c.ref)).then((g) => {
        if (dead || !g || b.tier !== 'proxy') return null;
        relight(g.scene);
        g.scene.traverse((o) => { o.frustumCulled = false; });   // skinned bounds go stale mid-clip
        if (md.tint != null || md.glow != null) dye(g.scene, md.tint, md.glow);
        if (md.yaw) g.scene.rotation.y += md.yaw;                // a pack that faces the wrong axis
        setVisual(b, g.scene, md.h, { tier: 'model', float: md.float, floatY: md.y,
                                      shadow: (md.wide || 1) * 1.5 });
        rigUp(b, g);
        if (b.dead) markDead(b, true);
        return 'done';
      }).then((r) => {
        if (r || dead || b.tier !== 'proxy') return;
        // tiers 2 and 3 share one probe: the first URL that decodes wins
        return probeImage(spriteUrls(c.ref)).then((im) => {
          if (!im || dead || b.tier !== 'proxy') return;
          setVisual(b, billboardFrom(im, md.h), md.h,
                    { tier: 'billboard', billboard: true, noScale: true, float: md.float,
                      floatY: md.y, shadow: (md.wide || 1) * 1.2 });
          billboards.push(b);
          if (b.dead) markDead(b, true);
        });
      }).catch(() => { });
    });

    const partySlot = partySlots((cfg.party || []).length);
    (cfg.party || []).forEach((c, i) => {
      const s = partySlot[i] || [CFG.form.partyX, 0];
      // face ACROSS the arena at the foes, turned further toward the camera so we
      // read three-quarter rather than pure back
      const b = newBody(c.id, 'party', s[0], s[1], foeSide() * (Math.PI / 2) + partySide() * 0.55);
      b.bobAmp = 0.035;
      const tint = art.tint[c.ref] || art.tint[c.id];
      const hM = art.height[c.ref] || art.height[c.id] || CFG.charH;
      setVisual(b, proxyFigure(tint), hM, { tier: 'proxy', shadow: 1.9 });
      if (c.dead) markDead(b, true);

      // THE RIG — the character's OWN, resolved from art.models by charId, with
      // art.charModel (null today) behind it for anyone the table does not name.
      // dye() still clones materials per instance, so nothing a tint does to one
      // body can bleed into another through a shared material.
      const asModel = () => {
        const urls = disable.partyModel ? null
          : (art.models[c.ref] || art.models[c.id] || art.charModel);
        return loadFirstGlb(urls).then((g) => {
          if (dead || !g || b.tier !== 'proxy') return null;
          relight(g.scene);
          g.scene.traverse((o) => { o.frustumCulled = false; });  // skinned bounds go stale mid-clip
          if (tint != null) dye(g.scene, tint, null);
          setVisual(b, g.scene, hM, { tier: 'model' });
          rigUp(b, g);
          if (b.dead) markDead(b, true);
          return 'done';
        });
      };
      // THE PLATE — ui_kit's chroma-keyed pose sprite on a camera-facing plane.
      // Keyed, despilled and cropped to its own opaque bounds by EBUI, so it is
      // bottom-anchored by construction and its feet land on the floor.
      const asBillboard = () => {
        const K = window.EBUI;
        if (dead || b.tier !== 'proxy' || disable.billboard || !K || !K.poseSprite) return null;
        return Promise.resolve(K.poseSprite(c.ref || c.id)).then((canvas) => {
          if (!canvas || dead || b.tier !== 'proxy') return null;
          setVisual(b, billboardFrom(canvas, hM), hM,
                    { tier: 'billboard', billboard: true, noScale: true, shadow: 1.15 });
          billboards.push(b);
          if (b.dead) markDead(b, true);
          return 'done';
        });
      };
      // ORDER IS art.partyBody, AND THAT IS THE WHOLE SWITCH. Both are shipped;
      // whichever loses is the other's fallback. Flipping one string flips the
      // game's look for the party without touching a line of this logic.
      const first = art.partyBody === 'billboard' ? asBillboard : asModel;
      const second = art.partyBody === 'billboard' ? asModel : asBillboard;
      Promise.resolve(first()).then(r => (r ? r : second())).catch(() => { });
    });

    // ---- target / actor rings ----------------------------------------------
    // WAS: one hard white annulus per marker, and it read as a debug gizmo — the
    // single most "unfinished" element in the before frames. Now each marker is a
    // GROUP of three coplanar pieces on the same additive material family: a soft
    // filled disc (presence), a bright thin ring (the edge the eye locks to) and
    // a set of ticks that turn (life). Additive rather than opaque, so the marker
    // GLOWS on the ground instead of being painted over it.
    function markerMesh(colHex, r, o) {
      const TH2 = T();
      o = o || {};
      const g = new TH2.Group();
      const mk = (geo, op) => {
        const m = new TH2.Mesh(geo, new TH2.MeshBasicMaterial({
          color: C(colHex), transparent: true, opacity: op, side: TH2.DoubleSide,
          depthWrite: false, depthTest: false, fog: false, blending: TH2.AdditiveBlending,
        }));
        g.add(m); return m;
      };
      const disc = mk(new TH2.CircleGeometry(r * 0.94, 36), (o.disc == null ? 0.16 : o.disc));
      const ring = mk(new TH2.RingGeometry(r * 0.88, r, 48), 0.9);
      const ticks = new TH2.Group();
      if (o.ticks !== false) {
        for (let i = 0; i < 4; i++) {
          const t = mk(new TH2.RingGeometry(r * 1.10, r * 1.26, 8, 1, i * (Math.PI / 2), 0.42), 0.8);
          g.remove(t); ticks.add(t);
        }
      }
      g.add(ticks);
      g.rotation.x = -Math.PI / 2; g.position.y = 0.06; g.renderOrder = 900;
      g.visible = false;
      g.userData = { disc, ring, ticks };
      scene.add(g);
      return g;
    }
    const targetRing = markerMesh(0xffb257, 0.60, { disc: 0.20 });
    const actorRing = markerMesh(0xbcd4ff, 0.50, { disc: 0.10, ticks: false });
    let targetId = null, actorId = null;
    // THE MARKER BELONGS TO THE BODY, NOT TO THE SLOT. Read off the PIVOT's
    // world position — the same source anchor() uses — so a lunging attacker and
    // a knocked-back target keep their marker under their feet. Reading
    // root.position instead left the marker standing in the empty grass the
    // fighter had just left, which was visible in the first swing frame.
    const _rp = new TH.Vector3();
    function placeRing(ring, id, k) {
      const b = id && bodies[id];
      if (!b || b.dead) { ring.visible = false; return; }
      b.pivot.getWorldPosition(_rp);
      ring.position.set(_rp.x, b.root.position.y + 0.06, _rp.z);
      const s = clamp(b.w * 0.78, 0.55, 2.3) * (k || 1);
      ring.scale.set(s, s, 1);
      ring.visible = true;
    }
    // one opacity write for a whole marker, so the pulse stays a single number
    function ringAlpha(ring, a) {
      const u = ring.userData;
      if (!u) return;
      u.disc.material.opacity = a * 0.22;
      u.ring.material.opacity = a;
      u.ticks.children.forEach(t => { t.material.opacity = a * 0.85; });
    }

    // ===== IMPACT VFX =========================================================
    // THE RESTRAINT RULE, and it is the whole brief for this section: a
    // turn-based game shows ONE event per beat, so a hit gets ONE burst, ONE
    // ring and ONE flash, all of them gone inside half a second. Anything that
    // lingers is still on screen when the next beat's number lands and the
    // player stops being able to tell which hit they are reading.
    //
    // Everything here is built, tweened and DISPOSED per event — no pool, no
    // residency. A battle fires a few dozen of these; a pool would be a cache
    // that outlives the scene it caches for, which is precisely the leak
    // destroy() exists to make impossible.
    function burst(pos, colHex, n, o) {
      const TH2 = T();
      o = o || {};
      const N = Math.max(1, n | 0);
      const p = new Float32Array(N * 3), v = [];
      const sp = o.spread || 0;
      const org = [];
      for (let i = 0; i < N; i++) {
        const a = Math.random() * 6.283, e = (o.up || 0.55) + Math.random() * 0.9;
        const s = (o.speed || 3.2) * (0.45 + Math.random() * 0.85);
        v.push([Math.cos(a) * s * 0.7, e * s, Math.sin(a) * s * 0.7]);
        // a spawn RADIUS, not a spawn point: a burst that starts as one dot is a
        // dot for the first two frames, which are the frames a 400 ms effect has
        const o3 = [pos.x + (Math.random() - 0.5) * 2 * sp,
                    pos.y + (Math.random() - 0.5) * 1.4 * sp,
                    pos.z + (Math.random() - 0.5) * 2 * sp];
        org.push(o3);
        p[i * 3] = o3[0]; p[i * 3 + 1] = o3[1]; p[i * 3 + 2] = o3[2];
      }
      const geo = new TH2.BufferGeometry();
      geo.setAttribute('position', new TH2.Float32BufferAttribute(p, 3));
      const mat = new TH2.PointsMaterial({
        size: o.size || 0.16, map: dotTex(), color: C(colHex), transparent: true,
        opacity: o.opacity == null ? 0.95 : o.opacity, depthWrite: false, fog: false,
        blending: o.additive === false ? TH2.NormalBlending : TH2.AdditiveBlending,
      });
      const pts = new TH2.Points(geo, mat);
      pts.renderOrder = 950;
      scene.add(pts);
      const ms = o.ms || CFG.fx.sparkMs, g = o.gravity == null ? 7.5 : o.gravity;
      const attr = geo.attributes.position;
      tween(ms, (u) => {
        const t = (u * ms) / 1000;
        for (let i = 0; i < N; i++) {
          attr.setXYZ(i, org[i][0] + v[i][0] * t,
                         org[i][1] + v[i][1] * t - 0.5 * g * t * t,
                         org[i][2] + v[i][2] * t);
        }
        attr.needsUpdate = true;
        mat.opacity = (o.opacity == null ? 0.95 : o.opacity) * (1 - u * u);
        mat.size = (o.size || 0.16) * (1 + u * (o.grow || 0));
      }, () => { scene.remove(pts); geo.dispose(); mat.dispose(); });
    }
    // The expanding ground ring. Reads as "the blow landed HERE" in one frame,
    // which a cloud of particles alone never does — the eye needs an edge.
    function shockRing(x, z, colHex, o) {
      const TH2 = T();
      o = o || {};
      const geo = new TH2.RingGeometry(0.26, 0.36, 32);
      const mat = new TH2.MeshBasicMaterial({ color: C(colHex), transparent: true, opacity: 0.8,
                                              side: TH2.DoubleSide, depthWrite: false, fog: false,
                                              blending: TH2.AdditiveBlending });
      const m = new TH2.Mesh(geo, mat);
      m.rotation.x = -Math.PI / 2;
      m.position.set(x, groundY(x, z) + 0.05, z);
      m.renderOrder = 940;
      scene.add(m);
      tween(o.ms || 380, (u) => {
        const e = easeOut(u), s = 1 + e * (o.to || 4.2);
        m.scale.set(s, s, 1);
        mat.opacity = 0.8 * (1 - e);
      }, () => { scene.remove(m); geo.dispose(); mat.dispose(); });
    }
    // A puff of the zone's own dirt where a body plants its foot. Uses the
    // ground palette, not a grey, so a crag kicks up pale grit and a river shore
    // kicks up dark silt — the same one-line-per-zone idea as everything else here.
    function dustAt(x, z, k) {
      if (!CFG.fx.dust || RM) return;
      burst(new (T().Vector3)(x, groundY(x, z) + 0.08, z), zone.dirt, 12,
            { speed: 1.5 * (k || 1), up: 0.35, size: 0.46, gravity: 2.6, ms: 560,
              opacity: 0.55, additive: false, grow: 1.6, spread: 0.16 });
    }

    // ===== CAMERA SHAKE + PUSH-IN =============================================
    // Absolute-timestamp driven like every tween here, so a hidden tab that
    // wakes up finds the shake OVER rather than resuming it half a second late
    // and jolting a settled frame.
    let shakeAmp = 0, shakeT0 = 0, shakeDur = 1, pushU = 0, pushDir = 0;
    function shake(amount, ms) {
      if (RM) return;
      shakeAmp = Math.max(shakeAmp, amount);
      shakeT0 = now(); shakeDur = ms || CFG.fx.shakeMs;
    }
    function pushIn(side) {
      if (RM) return;
      pushDir = side;
      tween(CFG.fx.pushMs, (u) => { pushU = u < 0.3 ? easeOut(u / 0.3) : 1 - easeInOut((u - 0.3) / 0.7); },
            () => { pushU = 0; });
    }

    // ===== TWEENS =============================================================
    // Absolute-timestamp tweens, NOT frame-delta ones: rAF is throttled to zero
    // in a hidden tab, so a delta-driven tween would freeze mid-lunge and a body
    // would be left standing in the wrong place when the tab came back. With
    // timestamps a resumed tab simply finds every tween finished and snaps to
    // the settled pose — which is the only correct answer.
    const tweens = [];
    function tween(dur, fn, done) {
      const t = { t0: now(), dur: Math.max(1, dur), fn, done };
      tweens.push(t); return t;
    }
    function runTweens() {
      const t = now();
      for (let i = tweens.length - 1; i >= 0; i--) {
        const w = tweens[i];
        const u = clamp((t - w.t0) / w.dur, 0, 1);
        try { w.fn(u); } catch (e) { }
        if (u >= 1) { tweens.splice(i, 1); if (w.done) { try { w.done(); } catch (e) { } } }
      }
    }

    // ===== THE PUBLIC VERBS ===================================================
    // Each one is "make this read on screen"; none of them means anything to the
    // battle, which has already decided the outcome before it calls.
    function act(id, kind) {
      const b = bodies[id];
      if (!b || b.dead) return;
      if (kind === 'item') { oneShot(b, 'item'); return; }
      if (kind === 'flee') return;
      const clipped = oneShot(b, 'attack');
      if (RM) return;                                  // reduced motion: the clip plays, the body stays put
      const dir = b.side === 'party' ? foeSide() : partySide();   // lunge AT the enemy
      // THE CAMERA LEANS INTO THE BLOW. 5.5 % of the camera's distance, out on
      // the same curve as the lunge — small enough that you feel it and never
      // notice it, which is the definition of camera language rather than a
      // camera trick. Every FF battle camera in the modern series does this and
      // no ruling of ours needs to change for it: the shot does not cut.
      pushIn(dir);
      tween(CFG.act.ms, (u) => {
        // out fast, hold a beat, back slow — a strike, not a slide
        const p = u < 0.34 ? easeOut(u / 0.34) : u < 0.5 ? 1 : 1 - easeInOut((u - 0.5) / 0.5);
        axisMove(b, dir * CFG.act.lungeM * p);
        // THE PROCEDURAL SWING — see procSwing(). Only when no clip took the job.
        if (!clipped) procSwing(b, u);
      }, () => { b.pivot.position.set(0, 0, 0); if (!clipped) procSwing(b, 1); });
      // dirt where the foot plants, at the end of the step out
      const home = b.home;
      tween(Math.round(CFG.act.ms * 0.34), () => { }, () => {
        dustAt(home.x + Math.cos(b.facing) * CFG.act.lungeM * 0.8,
               home.z + Math.sin(b.facing) * CFG.act.lungeM * 0.8, 1);
      });
    }
    // ---- THE PROCEDURAL SWING — NOW THE FALLBACK, NOT THE PATH ---------------
    // WRITTEN 2026-08-02 because the shipped cast had NO combat clips: the rigs
    // carried Idle, Walking_A and Jump_Full_Short and nothing else, so
    // `oneShot(b,'attack')` found nothing and the party's whole attack was a body
    // sliding forward on its idle. The arena supplied the motion itself: a
    // wind-up lean back, a hard rotate through, a settle. Crude, and a body's
    // WHOLE MASS moving, which is what makes it read at this camera distance.
    //
    // IT HAS SINCE STOOD ITSELF DOWN, exactly as designed — no flag, no edit, no
    // coordination. Later the same day the character factory shipped Attack /
    // Hit_A / Death_A on every retargeted rig (tools/vesper_retarget.py, COMBAT
    // CLIPS); the names are exact entries in CLIP above, `clipped` came back
    // true, and this function stopped running for the cast. That is the whole
    // mechanism: `clipped` is the MIXER's own answer, never a capability flag
    // somebody has to remember to flip.
    //
    // IT IS NOT DEAD CODE. It is what every body WITHOUT a combat clip still runs
    // on — a monster GLB from a pack that ships only an idle, the mannequin
    // proxy, a pose-plate billboard, and the next character whose rig lands
    // before their retarget does. A body with no clip must still be seen to
    // swing, so do not delete it when it looks unused.
    //
    // THE AXIS IS DERIVED, NOT GUESSED. A body's root is yawed by `facing` and
    // every model in the game faces a different way in its own file, so "lean
    // forward" is `up x fwd` — the horizontal axis perpendicular to the lunge —
    // and a positive angle tips the head toward the enemy for any facing at all.
    // Hard-coding rotation.x here would tip half the cast sideways.
    const _ax = new TH.Vector3();
    function leanAxis(b) { return _ax.set(Math.sin(b.facing), 0, -Math.cos(b.facing)); }
    function procSwing(b, u) {
      // wind up (back 0.26 rad) -> snap through (forward 0.40) -> settle
      const lean = u < 0.28 ? -0.26 * easeOut(u / 0.28)
                 : u < 0.46 ? lerp(-0.26, 0.40, easeOut((u - 0.28) / 0.18))
                 : 0.40 * (1 - easeInOut((u - 0.46) / 0.54));
      b.bob.setRotationFromAxisAngle(leanAxis(b), lean);
    }
    // The recoil twin: a struck body rotates AWAY from the blow rather than only
    // sliding, so a hit on a rig with no Hit clip still reads as a hit.
    //
    // THE HIT IS DELIBERATELY EXCLUDED FROM THE CLIP STAND-DOWN, AND IT IS THE ONE
    // EXCEPTION — do not "fix" it back to `if (!clipped)` (user ruling 2026-08-02).
    // The attack and the death hand over to their clips completely; the hit does
    // not, and it ALWAYS runs, on top of Hit_A rather than instead of it. Why:
    // Hit_A (UAL Hit_Chest, retargeted) is anatomically the better flinch — the
    // chin snaps back through about 41 degrees and the feet stay planted — but
    // MEASURED AT THE DISTANCE THE PLAYER ACTUALLY SEES IT, a body here is 40-60 px
    // tall, so a head is ~10 px and a 41 degree head rotation moves it 2-3 px. The
    // procedural lean rotates the WHOLE MASS 18 degrees and moves the head ~10 px.
    // The clip is more correct; the lean is more legible, and legibility at the
    // shipped camera distance wins — the same call that put Finn in the scarlet
    // vest rather than the ember one.
    //
    // THEY COMPOSE FOR FREE, which is why this costs no mechanism: the mixer poses
    // the SKELETON inside b.obj, and this rotates b.bob, which is a parent node. So
    // the struck body does both — the clip's head snap and the whole-body lean —
    // and neither one is fighting the other. The day a punchier hit donor lands,
    // drop the lean by restoring the `!clipped` guard.
    function procRecoil(b, u) {
      const back = u < 0.22 ? -0.32 * easeOut(u / 0.22) : -0.32 * (1 - easeInOut((u - 0.22) / 0.78));
      b.bob.setRotationFromAxisAngle(leanAxis(b), back);
    }
    // Move a body `m` metres along the WORLD battle axis (X) while its root is
    // yawed to face the enemy: the offset has to be expressed in the root's own
    // frame, or a yawed body would lunge sideways.
    function axisMove(b, m) {
      b.pivot.position.set(Math.cos(b.facing) * m, 0, Math.sin(b.facing) * m);
    }
    // THE HIT. Four things land on the same frame, which is the whole point:
    // the body goes hot, it is shoved, the ground says where, and the camera
    // registers the blow. Individually each is a gimmick; together they are the
    // difference between "a number appeared" and "that connected".
    function flinch(id) {
      const b = bodies[id];
      if (!b || b.dead) return;
      // The return value is deliberately NOT captured: unlike act() and markDead(),
      // the hit does not stand its procedural layer down. See procRecoil.
      oneShot(b, 'hit');
      // THE FLASH SURVIVES REDUCED MOTION. It is not motion — it is the single
      // piece of information "this body is the one that was hit", and a player
      // who has asked for less movement still needs to know who got struck.
      flashOn(b, CFG.fx.flash);
      tween(CFG.fx.flashMs, (u) => { b.flash = CFG.fx.flash * (1 - u) * (1 - u); applyFlash(b); },
            () => { b.flash = 0; applyFlash(b); });
      if (RM) return;
      b.pivot.getWorldPosition(_rp);
      const hx = _rp.x, hz = _rp.z;
      // AMBER, NOT WHITE. The struck body is already flashing white, and white
      // sparks over a white flash are sparks nobody sees — the first pass put
      // eighteen of them inside the one silhouette they could not be read
      // against. Amber over hot white reads; so does the wider spawn radius,
      // which puts half the burst outside the body on frame one.
      burst(new TH.Vector3(hx, b.root.position.y + b.floatY + b.h * 0.55, hz),
            0xffb851, CFG.fx.sparks,
            { speed: 3.4, size: 0.30, ms: CFG.fx.sparkMs, gravity: 8, spread: b.w * 0.45 });
      shockRing(hx, hz, 0xfff2d8);
      shake(CFG.fx.shake, CFG.fx.shakeMs);
      const dir = b.side === 'party' ? partySide() : foeSide();   // knocked AWAY from the enemy
      tween(CFG.act.flinchMs, (u) => {
        const p = u < 0.25 ? easeOut(u / 0.25) : 1 - easeInOut((u - 0.25) / 0.75);
        axisMove(b, dir * CFG.act.flinchM * p);
        // a little air on the shove: 6 cm, which at this distance is 3-4 px and
        // is the difference between "pushed" and "slid"
        b.pivot.position.y = Math.sin(p * Math.PI) * 0.06;
        procRecoil(b, u);      // ALWAYS, clip or no clip — see procRecoil's note
      }, () => { b.pivot.position.set(0, 0, 0); procRecoil(b, 1); });
    }
    function markDead(b, instant) {
      b.dead = true;
      // a procedural lean or a hit flash must never be what a corpse is wearing
      b.bob.rotation.set(0, 0, 0);
      b.flash = 0; applyFlash(b);
      if (b.id === targetId) { targetId = null; targetRing.visible = false; }
      if (instant) {
        b.pivot.rotation.z = b.side === 'foe' ? 0 : Math.PI * 0.42;
        b.root.position.y = b.home.y - (b.side === 'foe' ? 0.55 : 0);
        setOpacity(b, b.side === 'foe' ? 0 : 0.22);
        if (b.side === 'foe' && b.obj) b.obj.visible = false;
        return;
      }
      const fell = oneShot(b, 'die', true);
      // A DEATH IS THE LOUDEST BEAT IN A TURN AND GETS THE LOUDEST SHAKE. It
      // also gets its own burst in the zone's dirt rather than in sparks: the
      // body hits the ground, and what a body hitting the ground throws up is
      // the ground.
      if (!RM) {
        shake(CFG.fx.shakeKo, 420);
        dustAt(b.root.position.x, b.root.position.z, 1.9);
      }
      const y0 = b.root.position.y, r0 = b.pivot.rotation.z;
      const sink = b.side === 'foe' ? 0.55 : 0.0;
      const endA = b.side === 'foe' ? 0 : 0.22;
      tween(RM ? 260 : 720, (u) => {
        const e = easeInOut(u);
        if (!fell && !RM) b.pivot.rotation.z = lerp(r0, b.side === 'foe' ? Math.PI * 0.5 : Math.PI * 0.42, e);
        b.root.position.y = lerp(y0, y0 - sink, e);
        setOpacity(b, lerp(1, endA, u));               // the fade is INFORMATION; it survives reduced motion
      }, () => { if (b.side === 'foe' && b.obj) b.obj.visible = false; });
    }
    function revive(b) {
      b.dead = false;
      if (b.obj) b.obj.visible = true;
      b.pivot.rotation.z = 0;
      b.pivot.position.set(0, 0, 0);
      b.bob.rotation.set(0, 0, 0);          // a procedural lean must not outlive the body's death
      b.flash = 0; applyFlash(b);
      b.root.position.y = b.home.y;
      setOpacity(b, 1);
      if (b.actions && b.actions.idle) { b.actions.idle.reset().fadeIn(0.2).play(); }
    }

    // ===== PROJECTION =========================================================
    // What the DOM needs from the 3D scene: where is this body on screen, and how
    // tall is it in pixels. The screen positions its foe/hero anchor elements from
    // this, so every damage number, name tag, HP pip and caret in battle_turnbased
    // keeps its existing markup and styling and simply follows a 3D body.
    let _vb = null, _vt = null;
    let rect = { w: 1, h: 1 };
    function anchor(id) {
      const b = bodies[id];
      if (!b) return null;
      const TH2 = T();
      if (!_vb) { _vb = new TH2.Vector3(); _vt = new TH2.Vector3(); }
      // the pivot carries the lunge/knockback offset IN THE ROOT'S YAWED FRAME,
      // so the screen anchor has to come from the world matrix, not from adding
      // the two local vectors — a lunging body would otherwise leave its label
      // behind at an angle.
      b.pivot.getWorldPosition(_vb);
      // A FLOATER'S TAG FLOATS WITH IT. The anchor box is the BODY's screen
      // rectangle, not the patch of ground it is standing over — so for a wisp
      // hovering 0.6 m up, the name tag hanging under the box hangs under the
      // wisp instead of under empty grass. The blob shadow is a mesh on the root
      // and is untouched by this: it stays on the floor, which is the whole point
      // of a cast shadow.
      _vb.y += b.floatY;
      _vt.copy(_vb); _vt.y += b.h * (b.dead ? 0.35 : 1);
      _vb.project(camera); _vt.project(camera);
      const bx = (_vb.x * 0.5 + 0.5) * rect.w, by = (-_vb.y * 0.5 + 0.5) * rect.h;
      const ty = (-_vt.y * 0.5 + 0.5) * rect.h;
      return { x: bx, y: by, h: Math.max(12, by - ty), vis: _vb.z < 1 };
    }

    // ===== POST: THE GRADE ====================================================
    // THE DIAGNOSIS, from the before/after board: the painted plate is a graded
    // golden-hour photograph — warm highlights, cool shadows, a bloomed sun, a
    // dark frame — and the 3D layer in front of it was raw framebuffer. Two
    // pictures in one frame. This is four cheap draws that put the WHOLE frame,
    // plate included, through one grade so it becomes one picture.
    //
    // WHY IT IS HAND-ROLLED: play3d ships three.min.js, GLTFLoader and the BVH
    // and nothing else — there is no EffectComposer on this page and adding one
    // would mean editing play3d.html, which is coordinator custody. Four shader
    // passes is less code than the vendored one anyway.
    //
    // GAMMA, HONESTLY: the render target carries the renderer's sRGB output, so
    // the bloom threshold and the blur run in display space rather than in
    // linear. That is the cheap-bloom convention and it is why the threshold sits
    // as high as 0.70 with a knee — in display space a hard threshold on midtones
    // strobes as a body moves. Anyone re-tuning this should know which space the
    // numbers are in.
    const POST_V = [
      'varying vec2 vUv;',
      'void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    ].join('\n');
    const BRIGHT_F = [
      'varying vec2 vUv; uniform sampler2D tS; uniform float thr, knee;',
      'void main(){',
      '  vec3 c = texture2D(tS, vUv).rgb;',
      '  float l = max(c.r, max(c.g, c.b));',
      '  float w = smoothstep(thr - knee, thr + knee, l);',
      '  gl_FragColor = vec4(c * w, 1.0);',
      '}',
    ].join('\n');
    const BLUR_F = [
      'varying vec2 vUv; uniform sampler2D tS; uniform vec2 dir;',
      'void main(){',
      '  vec3 s = texture2D(tS, vUv).rgb * 0.2270270;',
      '  s += (texture2D(tS, vUv + dir * 1.3846153).rgb + texture2D(tS, vUv - dir * 1.3846153).rgb) * 0.3162162;',
      '  s += (texture2D(tS, vUv + dir * 3.2307692).rgb + texture2D(tS, vUv - dir * 3.2307692).rgb) * 0.0702702;',
      '  gl_FragColor = vec4(s, 1.0);',
      '}',
    ].join('\n');
    // THE GRADE. Order matters and this is the order a colourist works in:
    // bloom add -> contrast about mid grey -> split-tone (highlights warm,
    // shadows cool) -> saturation -> vignette -> grain. Vignette AFTER the tone
    // work or it darkens the thing the tone work just lifted.
    const COMP_F = [
      'varying vec2 vUv; uniform sampler2D tS, tB;',
      'uniform float bloom, vig, warm, con, sat, grain, seed;',
      'float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }',
      'void main(){',
      '  vec3 c = texture2D(tS, vUv).rgb;',
      '  c += texture2D(tB, vUv).rgb * bloom;',
      '  c = clamp((c - 0.5) * con + 0.5, 0.0, 2.0);',
      '  float l = dot(c, vec3(0.299, 0.587, 0.114));',
      '  c.r += warm * (l - 0.42);',
      '  c.b -= warm * (l - 0.42) * 0.85;',
      '  c = mix(vec3(l), c, sat);',
      '  vec2 d = vUv - 0.5;',
      '  c *= 1.0 - vig * dot(d, d) * 1.9;',
      '  c += (hash(vUv * 512.0 + seed) - 0.5) * grain;',
      '  gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);',
      '}',
    ].join('\n');

    let post = null;
    function makePost() {
      if (!CFG.post.on) return null;
      try {
        const P = CFG.post;
        const opt = { minFilter: TH.LinearFilter, magFilter: TH.LinearFilter,
                      format: TH.RGBAFormat, depthBuffer: true, stencilBuffer: false };
        const quad = new TH.Mesh(new TH.PlaneGeometry(2, 2), null);
        quad.frustumCulled = false;
        const qs = new TH.Scene(); qs.add(quad);
        const qc = new TH.OrthographicCamera(-1, 1, 1, -1, 0, 1);
        const mk = (frag, uni) => new TH.ShaderMaterial({ vertexShader: POST_V, fragmentShader: frag,
                                                          uniforms: uni, depthTest: false, depthWrite: false });
        const p = {
          rt: null, bA: null, bB: null, quad, qs, qc, w: 0, h: 0,
          bright: mk(BRIGHT_F, { tS: { value: null }, thr: { value: P.threshold }, knee: { value: P.knee } }),
          blur: mk(BLUR_F, { tS: { value: null }, dir: { value: new TH.Vector2() } }),
          comp: mk(COMP_F, { tS: { value: null }, tB: { value: null }, bloom: { value: P.bloom },
                             vig: { value: P.vignette }, warm: { value: P.warmth }, con: { value: P.contrast },
                             sat: { value: P.sat }, grain: { value: P.grain }, seed: { value: 0 } }),
          size(w, h) {
            if (w === p.w && h === p.h) return;
            p.w = w; p.h = h;
            const dpr = renderer.getPixelRatio();
            const W = Math.max(2, Math.floor(w * dpr)), H = Math.max(2, Math.floor(h * dpr));
            const bw = Math.max(2, Math.floor(W * P.scale)), bh = Math.max(2, Math.floor(H * P.scale));
            for (const k of ['rt', 'bA', 'bB']) if (p[k]) p[k].dispose();
            p.rt = new TH.WebGLRenderTarget(W, H, opt);
            p.bA = new TH.WebGLRenderTarget(bw, bh, opt);
            p.bB = new TH.WebGLRenderTarget(bw, bh, opt);
            // The scene pass must land in the target ALREADY sRGB-encoded, or the
            // composite reads linear values through a shader that assumes display
            // space and the whole frame comes out washed. Stating it on the
            // texture is how r128 is told.
            if (TH.sRGBEncoding !== undefined) p.rt.texture.encoding = TH.sRGBEncoding;
          },
          draw(to, mat) {
            quad.material = mat;
            renderer.setRenderTarget(to);
            renderer.render(qs, qc);
          },
          dispose() {
            for (const k of ['rt', 'bA', 'bB']) if (p[k]) p[k].dispose();
            quad.geometry.dispose();
            p.bright.dispose(); p.blur.dispose(); p.comp.dispose();
          },
        };
        return p;
      } catch (e) { console.warn('[stage3d] post unavailable', e); return null; }
    }
    post = makePost();
    // ONE render of the whole frame. Everything that draws — the loop, and
    // snapshot() — goes through here, so a QA photograph can never be of a
    // different pipeline from the one the player sees.
    function renderFrame() {
      if (!post || !CFG.post.on) {
        renderer.setRenderTarget(null);
        renderer.render(scene, camera);
        return;
      }
      const P = CFG.post;
      post.size(rect.w, rect.h);
      renderer.setRenderTarget(post.rt);
      renderer.clear();
      renderer.render(scene, camera);
      post.bright.uniforms.tS.value = post.rt.texture;
      post.bright.uniforms.thr.value = P.threshold;
      post.bright.uniforms.knee.value = P.knee;
      post.draw(post.bA, post.bright);
      const bw = post.bA.width, bh = post.bA.height;
      post.blur.uniforms.tS.value = post.bA.texture;
      post.blur.uniforms.dir.value.set(1 / bw, 0);
      post.draw(post.bB, post.blur);
      post.blur.uniforms.tS.value = post.bB.texture;
      post.blur.uniforms.dir.value.set(0, 1 / bh);
      post.draw(post.bA, post.blur);
      const cu = post.comp.uniforms;
      cu.tS.value = post.rt.texture; cu.tB.value = post.bA.texture;
      cu.bloom.value = P.bloom; cu.vig.value = P.vignette; cu.warm.value = P.warmth;
      cu.con.value = P.contrast; cu.sat.value = P.sat; cu.grain.value = P.grain;
      cu.seed.value = (frames % 97) * 0.37;
      post.draw(null, post.comp);
    }

    // ===== THE LOOP ===========================================================
    const clock = new (T().Clock)();
    const t0 = now();
    let raf = 0, introFrom = RM ? null : introPos.clone();
    let frames = 0;

    function resize() {
      const w = mount.clientWidth || window.innerWidth || 1280;
      const h = mount.clientHeight || window.innerHeight || 720;
      if (w === rect.w && h === rect.h) return;
      rect = { w, h };
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      // the backdrop arc is sized to the frustum, so a wider window needs a wider
      // band — rebuild it rather than let the sky run out at the edges
      const want = Math.atan(Math.tan(halfFovV) * camera.aspect) * CFG.backdrop.arcPad;
      if (Math.abs(want - halfArc) > 0.02 && backdrop) {
        halfArc = want;
        const m = backdrop.material;
        mountBackdrop(m.map ? (m.map.image.naturalWidth || 16) / (m.map.image.naturalHeight || 9) : 16 / 9, m.map);
      }
      camera.updateProjectionMatrix();
    }
    resize();

    function frame() {
      if (dead) return;
      raf = requestAnimationFrame(frame);
      resize();
      const dt = Math.min(clock.getDelta(), 0.1);
      const t = (now() - t0) / 1000;

      // camera: intro sweep, then the idle drift
      if (introFrom) {
        const u = clamp((now() - t0) / CFG.intro.ms, 0, 1);
        const e = easeOut(u);
        camera.position.set(lerp(introFrom.x, restPos.x, e), lerp(introFrom.y, restPos.y, e),
                            lerp(introFrom.z, restPos.z, e));
        if (u >= 1) introFrom = null;
      } else {
        camera.position.copy(restPos);
      }
      if (!RM) {
        const d = CFG.drift;
        camera.position.x += Math.sin(t * d.px) * d.ax;
        camera.position.y += Math.sin(t * d.py + 1.7) * d.ay;
        camera.position.z += Math.sin(t * d.pz + 3.1) * d.az;
        // THE PUSH-IN. The camera slides its own view ray toward the target and
        // drifts a touch toward the side the blow travels. It does NOT change fov
        // — a fov push is a zoom and reads as a cut in a game whose whole camera
        // doctrine is "one cut per passage".
        if (pushU > 0.001) {
          const k = CFG.fx.pushIn * pushU;
          camera.position.x += (target.x - camera.position.x) * k + pushDir * 0.22 * pushU;
          camera.position.y += (target.y - camera.position.y) * k * 0.7;
          camera.position.z += (target.z - camera.position.z) * k;
        }
        // THE SHAKE, decaying and pseudo-random per axis. Sines rather than a
        // random() so it is smooth at 60 Hz and identical at 30 — a per-frame
        // random shake is a per-frame-rate shake.
        if (shakeAmp > 0) {
          const su = clamp((now() - shakeT0) / shakeDur, 0, 1);
          if (su >= 1) shakeAmp = 0;
          else {
            const a = shakeAmp * (1 - su) * (1 - su), ph = (now() - shakeT0) / 1000;
            camera.position.x += Math.sin(ph * 61) * a;
            camera.position.y += Math.sin(ph * 47 + 1.1) * a * 0.85;
            camera.position.z += Math.sin(ph * 53 + 2.3) * a * 0.5;
          }
        }
        camera.lookAt(target.x + Math.sin(t * 0.037) * d.tgt * 0.12, target.y, target.z);
      } else {
        camera.lookAt(target);
      }

      runTweens();
      for (const m of mixers) m.update(dt);

      // idle breathe, on the bob group so the blob shadow never lifts off the floor
      if (!RM) {
        for (const id of order) {
          const b = bodies[id];
          if (b.dead) continue;
          // a rigged model has its OWN idle; only unrigged bodies get the bob
          const amp = b.mixer ? 0 : b.bobAmp;
          b.bob.position.y = b.floatY + Math.sin(t * 1.9 + b.bobPhase) * amp;
        }
      }
      // yaw-only billboarding: the plate turns to face the camera but stays upright
      for (const b of billboards) {
        if (!b.obj) continue;
        const dx = camera.position.x - b.root.position.x, dz = camera.position.z - b.root.position.z;
        b.obj.rotation.y = Math.atan2(dx, dz) - b.root.rotation.y;
      }
      placeRing(targetRing, targetId, 1.0 + (RM ? 0 : Math.sin(t * 4.2) * 0.06));
      placeRing(actorRing, actorId, 0.9);
      if (targetRing.visible) {
        ringAlpha(targetRing, RM ? 0.9 : 0.66 + Math.sin(t * 4.2) * 0.26);
        // the ticks TURN. A static marker is furniture; a turning one is a
        // cursor, and the player's eye finds a cursor without being told.
        if (!RM) targetRing.userData.ticks.rotation.z = t * 0.85;
      }
      // THE ACTOR MARKER IS TURN TELEGRAPHING and it has to be findable. At 0.42
      // it was a faint white smear on sunlit grass — a marker you have to hunt
      // for is not telling anyone whose turn it is.
      if (actorRing.visible) ringAlpha(actorRing, RM ? 0.85 : 0.72 + Math.sin(t * 2.1) * 0.14);

      renderFrame();
      frames++;
      if (cfg.onFrame) { try { cfg.onFrame(stage); } catch (e) { } }
    }
    raf = requestAnimationFrame(frame);

    // ===== THE STAGE OBJECT ===================================================
    const stage = {
      canvas, scene, camera, renderer,
      get frames() { return frames; },
      anchor,
      tierOf(id) { return bodies[id] ? bodies[id].tier : null; },
      tiers() { const o = {}; for (const id of order) o[id] = bodies[id].tier; return o; },
      // WHICH CLIPS A BODY ACTUALLY BOUND. `clipped` — the flag that stands the
      // procedural swing down — is the mixer's own answer and is therefore
      // invisible from outside; this makes it observable, so "the cast has real
      // combat clips" is something a harness can READ rather than infer from the
      // GLB on disk. Empty/absent = this body runs on procSwing, which is a
      // legitimate answer, not a failure.
      clipsOf(id) { const b = bodies[id]; return b && b.actions ? Object.keys(b.actions) : []; },
      setTarget(id) { targetId = id && bodies[id] && !bodies[id].dead ? id : null; },
      setActor(id) { actorId = id && bodies[id] && !bodies[id].dead ? id : null; },
      act, flinch,
      ko(id) { const b = bodies[id]; if (b && !b.dead) markDead(b, false); },
      setDead(id, on) {
        const b = bodies[id]; if (!b) return;
        if (on && !b.dead) markDead(b, false);
        else if (!on && b.dead) revive(b);
      },
      cheer() { for (const id of order) { const b = bodies[id]; if (b.side === 'party' && !b.dead) oneShot(b, 'cheer'); } },
      // ONE frame, rendered synchronously — the QA hook. preserveDrawingBuffer is
      // on, so a headless screenshot of a throttled tab still gets a live canvas.
      // THROUGH renderFrame(), NOT renderer.render(): a QA photograph of a
      // different pipeline from the one the player sees is worse than no
      // photograph, because it is believed.
      snapshot() { try { renderFrame(); return canvas.toDataURL('image/png'); } catch (e) { return null; } },
      // the polish knobs, live, so a tuning pass costs a console line
      fx: { shake, pushIn, burst, shockRing, dust: dustAt, flash: flashOn },
      destroy() {
        if (dead) return;
        dead = true;
        if (raf) cancelAnimationFrame(raf);
        tweens.length = 0;
        for (const m of mixers) { try { m.stopAllAction(); } catch (e) { } }
        // Every texture in this scene came out of THIS battle's own GLB parses
        // and canvases, so all of them go — except the two module-level canvases
        // (blob shadow, mist ribbon) which are shared with the next battle.
        scene.traverse((o) => {
          if (o.geometry) o.geometry.dispose();
          const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
          for (const m of ms) {
            for (const k of ['map', 'emissiveMap', 'alphaMap', 'normalMap', 'specularMap']) {
              const t = m[k];
              if (t && t !== shadowTex && t !== mistTex && t !== dotTexture) t.dispose();
            }
            m.dispose();
          }
        });
        // the post chain owns three render targets and three shader materials and
        // is NOT in the scene graph, so the traverse above never sees it
        if (post) { try { post.dispose(); } catch (e) { } post = null; }
        try { renderer.setRenderTarget(null); } catch (e) { }
        try { renderer.dispose(); } catch (e) { }
        try { renderer.forceContextLoss(); } catch (e) { }
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
        if (window.BattleStage3D && window.BattleStage3D._live === stage) {
          window.BattleStage3D._live = null;      // a dead stage must not be readable
        }
      },
    };
    // THE QA HANDLE. clipsOf() above exists so a harness can READ which clips a body
    // bound instead of inferring it from the GLB on disk — but every verb on this
    // object lives on the INSTANCE, and the instance is a closure variable inside
    // battle_turnbased (screenRef.stage). Nothing outside could reach it, so the
    // accessor was unreadable and the thing it was built to prove stayed unproven.
    // This is the handle, and it is READ-ONLY BY INTENT: null between battles,
    // nulled by destroy() above so a torn-down stage can never answer, and nothing
    // in the game reads it. Drive the arena through Battle, never through this.
    if (window.BattleStage3D) window.BattleStage3D._live = stage;
    return stage;
  }

  window.BattleStage3D = {
    version: 1,
    available, create,
    _live: null,        // the live stage instance, or null between battles — QA only

    CFG, ZONES, MON, PROXY, art, disable,
    reducedMotion,
    _debug() {
      return { available: available(), three: !!T() && (T().REVISION || '?'),
               disable: Object.assign({}, disable), charModel: art.charModel,
               models: Object.keys(art.models), post: CFG.post.on };
    },
  };
})();
