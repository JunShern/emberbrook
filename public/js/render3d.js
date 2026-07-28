/*
 * render3d.js — the FF-hybrid world renderer, as an engine module.
 *
 * Extracts the proven runtime (see public/play3d.html, verified across all Ch1/Ch2 scenes)
 * into an object the game engine can drive. It replaces the *body* of Field.draw for
 * 3D scenes while the existing 2D canvas keeps drawing the HUD via Field.worldToScreen.
 *
 * INTEGRATION (next step — see MIGRATION.md):
 *   - Field.register: for a scene with mode3d, note its bundle dir.
 *   - Field.draw(g, entities, dt, focuses): if Field.mode3d, call
 *       Render3D.setView(camX, camY, viewH); Render3D.setEntities(entities); Render3D.frame();
 *     and SKIP the 2D backdrop/y-sort (Render3D drew the world to its own WebGL canvas,
 *     layered under the 2D HUD canvas). Keep Field._lastView/worldToScreen for the HUD.
 *   - Collision stays Field.walkable over the geometry-baked mask.png (unchanged code path).
 *
 * This module is written to be dropped in once the WebGL canvas is layered under the game
 * canvas; it deliberately owns only the WORLD layer, never the HUD.
 *
 * Requires THREE (r128) + THREE.GLTFLoader loaded first (see public/lib/).
 */
(function (global) {
  'use strict';

  const Render3D = {
    ready: false,
    scene: null, camera: null, renderer: null,
    collide: [],                 // invisible depth-writing meshes (occlusion + raycast collision)
    chars: {},                   // per-entity visual (billboard/model) keyed by a stable id
    _sheets: {},                 // loaded character sprite sheets + layout
    _ray: null, _down: null,

    // --- one-time init: attach a WebGL canvas sized to the world layer ---
    init(container, W, H) {
      this.W = W; this.H = H;
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setSize(W, H, false);
      this.renderer.outputEncoding = THREE.sRGBEncoding;
      container.appendChild(this.renderer.domElement);
      this.scene = new THREE.Scene();
      this.scene.add(new THREE.AmbientLight(0xffffff, 0.95));
      const dl = new THREE.DirectionalLight(0xffd9a8, 1.3); dl.position.set(6, 10, 4); this.scene.add(dl);
      this._ray = new THREE.Raycaster(); this._down = new THREE.Vector3(0, -1, 0);
      return this;
    },

    // --- load a scene bundle (public/assets/scenes/<key>/{stylized.png, scene.glb}) ---
    loadScene(dir, onReady) {
      // clear previous scene geometry
      for (const m of this.collide) this.scene.remove(m);
      this.collide = []; this.ready = false;
      new THREE.TextureLoader().load(dir + 'stylized.png', t => { t.encoding = THREE.sRGBEncoding; this.scene.background = t; });
      new THREE.GLTFLoader().load(dir + 'scene.glb', g => {
        this.scene.add(g.scene);
        this.camera = (g.cameras && g.cameras[0]) ||
          Object.assign(new THREE.OrthographicCamera(-20, 20, 11.25, -11.25, 0.1, 200), { position: new THREE.Vector3(22, 24, 22) });
        g.scene.updateMatrixWorld(true);
        g.scene.traverse(o => {
          if (o.isMesh) { o.material = new THREE.MeshBasicMaterial({ colorWrite: false }); o.renderOrder = -1; this.collide.push(o); }
        });
        this.ready = true; if (onReady) onReady();
      });
    },

    // --- register a character sheet layout (cols, rows, dir rows/frame-counts) ---
    registerChar(key, url, layout) {
      const sheet = new THREE.TextureLoader().load(url);
      sheet.wrapS = sheet.wrapT = THREE.RepeatWrapping; sheet.repeat.set(1 / layout.cols, 1 / layout.rows);
      sheet.encoding = THREE.sRGBEncoding;
      this._sheets[key] = { sheet, layout };
    },

    // --- camera pan/zoom driven by the engine's Field.updateCamera (ortho window) ---
    // camX,camY in backdrop px; viewH = px of world shown vertically. Maps to the ortho
    // camera's frustum window. (The one refinement flagged in MIGRATION.md — validate vs a
    // scrolling scene; for one-frame scenes the GLB camera is already correct as-is.)
    setView(camX, camY, viewH) {
      // TODO(engine-wire): translate backdrop-px camX/camY/viewH into an offset+zoom on the
      // ortho camera so bg + geometry + HUD stay locked while panning to frame both players.
      this._view = { camX, camY, viewH };
    },

    // --- place entities: raycast each entity's ground position, drop its billboard there ---
    setEntities(entities) {
      const seen = {};
      for (const e of entities) {
        if (e.hidden) continue;
        const id = e._r3id || (e._r3id = 'e' + (Render3D._nid = (Render3D._nid || 0) + 1));
        seen[id] = true;
        let c = this.chars[id];
        if (!c) c = this.chars[id] = this._makeChar(e);
        this._placeChar(c, e);
      }
      for (const id in this.chars) if (!seen[id]) { this.scene.remove(this.chars[id].group); delete this.chars[id]; }
    },

    _makeChar(e) {
      const group = new THREE.Group(); this.scene.add(group);
      const s = this._sheets[e.char] || Object.values(this._sheets)[0];
      const mat = new THREE.MeshBasicMaterial({ map: s.sheet.clone(), alphaTest: 0.5, side: THREE.DoubleSide });
      mat.map.repeat.copy(s.sheet.repeat); mat.map.needsUpdate = true;
      const spr = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 2.6), mat); spr.position.y = 1.02; group.add(spr);
      return { group, spr, layout: s.layout, dir: 'down', tick: 0 };
    },

    _placeChar(c, e) {
      // world backdrop-px (e.x, e.y) -> 3D ground via raycast from the ortho camera through
      // that screen point; falls back to entity height. (For one-frame ortho scenes the GLB
      // ground under the entity's projected point is correct.)
      // ...engine-wire: use Field.worldToScreen(e.x,e.y) -> NDC -> Raycaster(camera).
      // Billboard yaw to camera; pick frame row from e.dir; advance walk frames when e.moving.
      const L = c.layout;
      const rows = { down: L.down, up: L.up, left: L.side, right: L.side };
      const d = e.dir || 'down'; const rowInfo = rows[d] || L.down;
      if (e.moving) c.tick = (c.tick + 1) % (rowInfo.n * 5);
      const f = e.moving ? Math.floor(c.tick / 5) : 0;
      c.spr.material.map.offset.set(f / L.cols, 1 - (rowInfo.row + 1) / L.rows);
      c.spr.scale.x = (d === 'right') ? -1 : 1;
      c.group.rotation.y = Math.atan2(this.camera.position.x - c.group.position.x, this.camera.position.z - c.group.position.z);
    },

    frame() { if (this.ready) this.renderer.render(this.scene, this.camera); },
  };

  global.Render3D = Render3D;
})(this);
