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

    // THE FF BATTLE CAMERA. pitch/yaw are degrees. The yaw is toward +X (the
    // party's side) so the monsters — the things you aim at — read frontally and
    // the party reads three-quarter-rear, which is the classic legible framing.
    cam: { fov: 34, dist: 11.6, pitch: 13, yaw: 14, target: [0, 1.15, 0.15], near: 0.5, far: 260 },
    // The intro sweep: start wider/higher, ease into the rest pose. It plays
    // BEHIND battle_turnbased's own fade-in, so the first thing the player sees
    // is already settling.
    intro: { ms: 1050, dist: 1.34, pitch: 8, yaw: 6 },
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
      partyX: 3.2, partyDx: 1.05, partyZ: 0.35, partyDz: 2.0,
      foeX: -3.4, foeRank: 2.1, foeSpread: 3.3, foeJog: 0.9, foeChevron: 0.6,
    },
    // How far a body travels on a lunge, and for how long.
    act: { lungeM: 1.35, ms: 620, flinchM: 0.42, flinchMs: 330 },
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
    meadow: { ground: 0x6f8a3f, ground2: 0x93a856, dirt: 0x9c8a5c, rock: 0x9a9384,
              haze: 0xe6d3a8, sky: 0xd9c48e, key: 0xffe0b0, fill: 0x9fb6d8,
              props: 'meadow', horizon: 0.60 },
    forest: { ground: 0x5e4d31, ground2: 0x7d6540, dirt: 0x9a7f52, rock: 0x7c7364,
              haze: 0xd9b787, sky: 0xc9a473, key: 0xffcf96, fill: 0x8fa07e,
              props: 'forest', horizon: 0.63 },
    crag:   { ground: 0x8d8073, ground2: 0xa79b8c, dirt: 0x9c8f7d, rock: 0x9d8f7f,
              haze: 0xdfcdbe, sky: 0xd3c3b6, key: 0xffd6a0, fill: 0xa9b7cc,
              props: 'crag', horizon: 0.56 },
    water:  { ground: 0x94907a, ground2: 0xafab90, dirt: 0xa39a7e, rock: 0x8d9490,
              haze: 0xe4dcd0, sky: 0xd8c9bd, key: 0xffe0bb, fill: 0xa8c6d6,
              props: 'water', horizon: 0.60 },
    default:{ ground: 0x7f7663, ground2: 0x968c77, dirt: 0x8d8064, rock: 0x8d8577,
              haze: 0xdfd0b4, sky: 0xcdbfa8, key: 0xffd9a8, fill: 0x9fb6d8,
              props: 'meadow', horizon: 0.58 },
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
    // the sourced ghost is bare white, which vanishes against a pale plate and
    // reads as nothing in particular; a cool tint plus a faint self-glow makes it
    // a water-wisp, which is what a brook-sprite is
    'brook-sprite': { h: 0.9, bob: 0.14, y: 0.5, float: true, tint: 0x92dcef, glow: 0x2a5f77 },
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
    charModel: 'assets/characters3d/rogue.glb',   // the party's 3D body today
    models: {},                          // charId -> glb url (overrides charModel)
    tint: { maren: 0x86c9c2 },           // same model, different dye lot
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
  let shadowTex = null, mistTex = null;
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
  function partySlots(n) {
    const f = CFG.form, out = [], mid = (n - 1) / 2;
    // each member a step further right AND a step nearer the camera than the one
    // in front of her: no two party bodies ever share a screen-space column
    for (let i = 0; i < n; i++) {
      out.push([f.partyX + (i - mid) * f.partyDx, f.partyZ + (i - mid) * f.partyDz]);
    }
    return out;
  }
  function foeSlots(n) {
    const f = CFG.form, out = [], mid = (n - 1) / 2;
    // A CHEVRON, not a parity zigzag. Parity put slot 1 and slot 2 on nearly the
    // same screen ray from this camera and one monster stood inside another; a
    // chevron pushes the middle of the line at the party and the ends back, so
    // depth separation and screen separation grow together.
    if (n <= 3) {
      for (let i = 0; i < n; i++) {
        out.push([f.foeX - Math.abs(i - mid) * f.foeChevron, (i - mid) * f.foeSpread]);
      }
      return out;
    }
    const front = Math.ceil(n / 2), back = n - front;
    for (let i = 0; i < front; i++) out.push([f.foeX, (i - (front - 1) / 2) * f.foeSpread]);
    for (let i = 0; i < back; i++) out.push([f.foeX - f.foeRank, (i - (back - 1) / 2) * f.foeSpread + f.foeJog]);
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
      renderer = new TH.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
    } catch (e) { return null; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    if (TH.sRGBEncoding !== undefined) renderer.outputEncoding = TH.sRGBEncoding;
    renderer.setClearColor(zone.sky, 1);
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
    const restPos = camPose(CFG.cam.dist, CFG.cam.pitch, CFG.cam.yaw);
    const introPos = camPose(CFG.cam.dist * CFG.intro.dist,
                             CFG.cam.pitch + CFG.intro.pitch, CFG.cam.yaw + CFG.intro.yaw);
    camera.position.copy(restPos);
    camera.lookAt(target);

    // ---- light: golden hour, matching the canon and play3d's own rig --------
    // Total intensity is kept UNDER ~1.0 on the lit side on purpose: a Lambert
    // surface driven past 1 clips its albedo to white, which is exactly what
    // turns a zone-tinted clearing into one flat tan pancake.
    const hemi = new TH.HemisphereLight(C(zone.sky), C(zone.ground), 0.5);
    scene.add(hemi);
    const key = new TH.DirectionalLight(C(zone.key), 0.86);
    key.position.set(-7, 9, -4.5);                    // raking from the upper LEFT-BACK
    scene.add(key);
    const fill = new TH.DirectionalLight(C(zone.fill), 0.22);
    fill.position.set(6, 4, 7);
    scene.add(fill);
    scene.add(new TH.AmbientLight(0xffffff, 0.15));

    // ---- THE GROUND: a dished clearing --------------------------------------
    // A radial grid, not a square plane: the rim is a circle, so the silhouette
    // where it meets the backdrop is an even arc rather than four corners.
    const noise = mkNoise(0x9e37);
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
          // Three octaves, all at wavelengths this grid can actually resolve.
          // The rings crowd toward the centre (r = rr²R), so near the fight the
          // spacing is ~0.2 m and a 1 m feature reads; at the rim it is ~1.4 m
          // and only the slow swell survives — which is exactly right, because
          // the rim is what dissolves into the plate.
          const n1 = noise(x * 0.17 + 40, z * 0.17 + 40);   // slow swells
          const n2 = noise(x * 0.55 + 7, z * 0.55 + 7);     // patchiness
          const n3 = noise(x * 1.15 + 91, z * 1.15 + 91);   // grain
          const dish = g.dish * (r / R) * (r / R);
          const bump = ((n1 - 0.5) * 1.3 + (n2 - 0.5) * 0.6 + (n3 - 0.5) * 0.32) * g.bump *
                       Math.min(1, r / 2.6 + 0.3);          // flattest where they stand
          pos.push(x, dish + bump, z);
          // THE CENTRE IS TRODDEN. A bare, paler dirt patch under the combatants
          // grading out to the zone's ground colour — the thing that makes a
          // clearing read as a place people fight in rather than a green disc.
          // Its edge is broken by the patch noise so it is never a drawn circle.
          const wear = clamp(1 - (r + (n2 - 0.5) * 3.6) / 6.6, 0, 1);
          tmp.copy(cBase).lerp(cAlt, clamp(n2 * 1.7 - 0.3, 0, 1));
          tmp.lerp(cDirt, clamp(wear * 1.3, 0, 0.9));
          const shade = 0.62 + n3 * 0.62 + n1 * 0.2;        // grain + the swells' own shading
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
      return m;
    }
    const ground = buildGround();
    scene.add(ground);
    // the ground height under a point, from the same closed form the mesh uses
    function groundY(x, z) {
      const g = CFG.ground, r = Math.min(Math.sqrt(x * x + z * z), g.radius);
      const n1 = noise(x * 0.19 + 40, z * 0.19 + 40), n2 = noise(x * 0.62 + 7, z * 0.62 + 7);
      return g.dish * (r / g.radius) * (r / g.radius) +
             ((n1 - 0.5) * 1.35 + (n2 - 0.5) * 0.55) * g.bump * Math.min(1, r / 2.6 + 0.3);
    }
    const rimY = CFG.ground.dish;

    // ---- THE BACKDROP BAND --------------------------------------------------
    // Curved around the CAMERA, not the world — see CFG.backdrop. The plate's
    // horizon row is pinned to where the ground's far rim projects at backdrop
    // distance, which is what "generated with awareness of the 3D model" buys:
    // the painted horizon lands exactly on the 3D silhouette.
    function backdropGeo(dist, halfArc, plateAspect, horizonFrac) {
      const f = new TH.Vector3(); camera.getWorldDirection(f); f.y = 0; f.normalize();
      const r = new TH.Vector3(-f.z, 0, f.x);          // screen-right, on the ground plane
      const P = camera.position;
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
    const flat = (c) => new TH.MeshLambertMaterial({ color: C(c), flatShading: true });
    function place(o, x, z, ry, s) {
      o.position.set(x, groundY(x, z), z);
      o.rotation.y = ry == null ? 0 : ry;
      if (s) o.scale.multiplyScalar(s);
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
        billboard: false, floatY: 0, mats: null,
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
      const sw = clamp(b.w * (opt.shadow || 1.5), 0.55, 3.4);
      b.shadow.scale.set(sw, sw * 0.62, 1);
      b.shadow.material.opacity = opt.float ? 0.42 : 0.85;
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
      b.shadow.material.opacity = 0.85 * a;
    }

    // ---- the party's proxy: a WOODEN FIGURE, not a ball -----------------------
    // The party's last tier is on screen for the ~200 ms before a 3.5 MB rig
    // parses, at the start of every single battle. A 1.7 m sphere in that slot
    // reads as a bug; a crude artist's mannequin reads as "she is arriving".
    function proxyFigure(tintC) {
      const TH2 = T();
      const g = new TH2.Group();
      const cloth = new TH2.MeshLambertMaterial({ color: C(tintC != null ? tintC : 0x6f8a63), flatShading: true });
      const skin = new TH2.MeshLambertMaterial({ color: C(0xd8b48c), flatShading: true });
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
      const mA = new TH2.MeshLambertMaterial({ color: C(tintC != null ? tintC : d.c), flatShading: true });
      const mB = new TH2.MeshLambertMaterial({ color: C(d.c2), flatShading: true });
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
      a.reset(); a.setEffectiveWeight(1); a.fadeIn(0.08).play();
      if (idle && !hold) {
        idle.fadeOut(0.08);
        const dur = a.getClip().duration;
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
    const foeSlot = foeSlots((cfg.foes || []).length);
    (cfg.foes || []).forEach((c, i) => {
      const s = foeSlot[i] || [CFG.form.foeX, 0];
      const b = newBody(c.id, 'foe', s[0], s[1], Math.PI / 2 - 0.22);   // face +X, angled to camera
      const md = MON[c.ref] || MON.default;
      b.bobAmp = md.bob;
      const fam = cfg.familyOf ? cfg.familyOf(c.ref) : 'default';
      setVisual(b, proxySolid(fam), md.h, { tier: 'proxy', float: md.float, floatY: md.y,
                                           shadow: (md.wide || 1) * 1.5 });
      if (c.dead) markDead(b, true);
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
      const b = newBody(c.id, 'party', s[0], s[1], -Math.PI / 2 + 0.55);  // face -X, turned to camera
      b.bobAmp = 0.035;
      const tint = art.tint[c.ref] || art.tint[c.id];
      setVisual(b, proxyFigure(tint), CFG.charH, { tier: 'proxy', shadow: 1.9 });
      if (c.dead) markDead(b, true);
      const url = disable.partyModel ? null : (art.models[c.ref] || art.models[c.id] || art.charModel);
      loadGlb(url).then((g) => {
        if (dead || !g || b.tier !== 'proxy') return null;
        // SAME MODEL, DIFFERENT DYE LOT. Vesper and Maren share one rig today
        // (ruled: do not build new models); dye() clones materials per instance,
        // so a tint on one can never bleed into the other.
        relight(g.scene);
        g.scene.traverse((o) => { o.frustumCulled = false; });   // skinned bounds go stale mid-clip
        if (tint != null) dye(g.scene, tint, null);
        setVisual(b, g.scene, CFG.charH, { tier: 'model' });
        rigUp(b, g);
        if (b.dead) markDead(b, true);
        return 'done';
      }).then((r) => {
        if (r || dead || b.tier !== 'proxy' || disable.billboard) return;
        // THE BILLBOARD FALLBACK — ui_kit's chroma-keyed pose plate on a plane.
        // This is the path every future character walks in on before their model
        // is authored, so it has to be as good as it can be: keyed, cropped to
        // its own opaque bounds by EBUI, hence bottom-anchored = feet on the floor.
        const K = window.EBUI;
        if (!K || !K.poseSprite) return;
        return Promise.resolve(K.poseSprite(c.ref || c.id)).then((canvas) => {
          if (!canvas || dead || b.tier !== 'proxy') return;
          setVisual(b, billboardFrom(canvas, CFG.charH), CFG.charH,
                    { tier: 'billboard', billboard: true, noScale: true, shadow: 1.15 });
          billboards.push(b);
          if (b.dead) markDead(b, true);
        });
      }).catch(() => { });
    });

    // ---- target / actor rings ----------------------------------------------
    function ringMesh(color, r) {
      const TH2 = T();
      const m = new TH2.Mesh(new TH2.RingGeometry(r * 0.76, r, 40), new TH2.MeshBasicMaterial({
        color: color, transparent: true, opacity: 0.9, side: TH2.DoubleSide,
        depthWrite: false, depthTest: false, fog: false,
      }));
      m.rotation.x = -Math.PI / 2; m.position.y = 0.06; m.renderOrder = 900;
      m.visible = false;
      scene.add(m);
      return m;
    }
    const targetRing = ringMesh(C(0xffc46a), 0.52);
    const actorRing = ringMesh(C(0xdfe8ff), 0.44);
    actorRing.material.opacity = 0.5;
    let targetId = null, actorId = null;
    function placeRing(ring, id, k) {
      const b = id && bodies[id];
      if (!b || b.dead) { ring.visible = false; return; }
      ring.position.set(b.root.position.x, b.root.position.y + 0.06, b.root.position.z);
      const s = clamp(b.w * 0.78, 0.55, 2.3) * (k || 1);
      ring.scale.set(s, s, 1);
      ring.visible = true;
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
      oneShot(b, 'attack');
      if (RM) return;                                  // reduced motion: the clip plays, the body stays put
      const dir = b.side === 'party' ? -1 : 1;         // lunge across the arena
      tween(CFG.act.ms, (u) => {
        // out fast, hold a beat, back slow — a strike, not a slide
        const p = u < 0.34 ? easeOut(u / 0.34) : u < 0.5 ? 1 : 1 - easeInOut((u - 0.5) / 0.5);
        axisMove(b, dir * CFG.act.lungeM * p);
      }, () => { b.pivot.position.set(0, 0, 0); });
    }
    // Move a body `m` metres along the WORLD battle axis (X) while its root is
    // yawed to face the enemy: the offset has to be expressed in the root's own
    // frame, or a yawed body would lunge sideways.
    function axisMove(b, m) {
      b.pivot.position.set(Math.cos(b.facing) * m, 0, Math.sin(b.facing) * m);
    }
    function flinch(id) {
      const b = bodies[id];
      if (!b || b.dead) return;
      oneShot(b, 'hit');
      if (RM) return;
      const dir = b.side === 'party' ? 1 : -1;         // knocked AWAY from the enemy
      tween(CFG.act.flinchMs, (u) => {
        const p = u < 0.25 ? easeOut(u / 0.25) : 1 - easeInOut((u - 0.25) / 0.75);
        axisMove(b, dir * CFG.act.flinchM * p);
      }, () => { b.pivot.position.set(0, 0, 0); });
    }
    function markDead(b, instant) {
      b.dead = true;
      if (b.id === targetId) { targetId = null; targetRing.visible = false; }
      if (instant) {
        b.pivot.rotation.z = b.side === 'foe' ? 0 : Math.PI * 0.42;
        b.root.position.y = b.home.y - (b.side === 'foe' ? 0.55 : 0);
        setOpacity(b, b.side === 'foe' ? 0 : 0.22);
        if (b.side === 'foe' && b.obj) b.obj.visible = false;
        return;
      }
      const fell = oneShot(b, 'die', true);
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
      _vt.copy(_vb); _vt.y += b.floatY + b.h * (b.dead ? 0.35 : 1);
      _vb.project(camera); _vt.project(camera);
      const bx = (_vb.x * 0.5 + 0.5) * rect.w, by = (-_vb.y * 0.5 + 0.5) * rect.h;
      const ty = (-_vt.y * 0.5 + 0.5) * rect.h;
      return { x: bx, y: by, h: Math.max(12, by - ty), vis: _vb.z < 1 };
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
      if (targetRing.visible) targetRing.material.opacity = RM ? 0.9 : 0.62 + Math.sin(t * 4.2) * 0.28;

      renderer.render(scene, camera);
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
      snapshot() { try { renderer.render(scene, camera); return canvas.toDataURL('image/png'); } catch (e) { return null; } },
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
              if (t && t !== shadowTex && t !== mistTex) t.dispose();
            }
            m.dispose();
          }
        });
        try { renderer.dispose(); } catch (e) { }
        try { renderer.forceContextLoss(); } catch (e) { }
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      },
    };
    return stage;
  }

  window.BattleStage3D = {
    version: 1,
    available, create,
    CFG, ZONES, MON, PROXY, art, disable,
    reducedMotion,
    _debug() {
      return { available: available(), three: !!T() && (T().REVISION || '?'),
               disable: Object.assign({}, disable), charModel: art.charModel };
    },
  };
})();
