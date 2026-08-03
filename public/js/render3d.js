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
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
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
      new THREE.TextureLoader().load(dir + 'stylized.png', t => { t.colorSpace = THREE.SRGBColorSpace; this.scene.background = t; });
      new THREE.GLTFLoader().load(dir + 'scene.glb', g => {
        this.scene.add(g.scene);
        this.camera = (g.cameras && g.cameras[0]) ||
          Object.assign(new THREE.OrthographicCamera(-20, 20, 11.25, -11.25, 0.1, 200), { position: new THREE.Vector3(22, 24, 22) });
        g.scene.updateMatrixWorld(true);
        // occlusion depth = ALL geometry; collision floors/walls = ONLY walk_ surfaces
        // (props/roofs/awnings must never register as false floors — the perch bug)
        g.scene.traverse(o => {
          if (o.isMesh) { o.material = new THREE.MeshBasicMaterial({ colorWrite: false }); o.renderOrder = -1; if (/^walk/i.test(o.name)) this.collide.push(o); }
        });
        this.ready = true; if (onReady) onReady();
      });
    },

    // --- register a character sheet layout (cols, rows, dir rows/frame-counts) ---
    registerChar(key, url, layout) {
      const sheet = new THREE.TextureLoader().load(url);
      sheet.wrapS = sheet.wrapT = THREE.RepeatWrapping; sheet.repeat.set(1 / layout.cols, 1 / layout.rows);
      sheet.colorSpace = THREE.SRGBColorSpace;
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

    // === COLLISION (3D raycast — the authority for movement) =================
    // NOTE (QA finding, 2026-07-28): the flat 2D walkmask CANNOT be the collision
    // authority. A staircase projects to top-down as one disconnected strip per tread
    // (verified: stairs3d masks as ~6 floating islands), so a mask-lookup engine would
    // make stairs unclimbable — fatal for the scaffold scenes (Dellhollow). This raycast
    // over the invisible depth geometry handles multi-level AND flat ground correctly
    // (verified climbable in play3d.html). It supersedes migration decision #2's mask
    // lookup: Field movement should call Render3D.resolveMove, not sample mask.png.
    RAD: 0.42, STEP_UP: 0.55, STEP_DN: 0.8,
    _wn(h) { return h.face.normal.clone().applyMatrix3(new THREE.Matrix3().getNormalMatrix(h.object.matrixWorld)).normalize(); },
    // highest floor directly below (x,z) within a step of fy; null if none (a drop/void)
    ground(x, z, fy) {
      this._ray.set(new THREE.Vector3(x, fy + this.STEP_UP + 0.1, z), this._down);
      this._ray.far = this.STEP_UP + this.STEP_DN + 0.2;
      for (const h of this._ray.intersectObjects(this.collide, true)) if (this._wn(h).y > 0.5) return h.point.y;
      return null;
    },
    // all floor heights under (x,z) — used for spawn scan / multi-level probing
    floors(x, z) {
      this._ray.set(new THREE.Vector3(x, 40, z), this._down); this._ray.far = 80;
      return this._ray.intersectObjects(this.collide, true).filter(h => this._wn(h).y > 0.5).map(h => h.point.y);
    },
    // is there a wall blocking a move of (dx,dz) from (x,z)? 3-ray width sweep at heights
    // ABOVE STEP_UP so stair risers are climbed (not treated as walls) — the fix that made
    // stairs walkable instead of jump-only.
    wall(x, z, dx, dz, fy) {
      const l = Math.hypot(dx, dz) || 1, d = new THREE.Vector3(dx / l, 0, dz / l), pp = new THREE.Vector3(-d.z, 0, d.x);
      for (const hy of [this.STEP_UP + 0.2, 0.95, 1.5]) for (const o of [0, this.RAD * 0.75, -this.RAD * 0.75]) {
        this._ray.set(new THREE.Vector3(x + pp.x * o, fy + hy, z + pp.z * o), d); this._ray.far = this.RAD + l + 0.02;
        for (const h of this._ray.intersectObjects(this.collide, true)) if (Math.abs(this._wn(h).y) < 0.6) return true;
      }
      return false;
    },
    // resolve an attempted move from pos by (dx,dz); returns the new {x,y,z} (slides on walls,
    // climbs steps ≤ STEP_UP, refuses drops > STEP_DN). Engine calls this instead of a mask test.
    resolveMove(pos, dx, dz) {
      const p = { x: pos.x, y: pos.y, z: pos.z };
      for (const [mx, mz] of [[dx, dz], [dx, 0], [0, dz]]) {
        if (!mx && !mz) continue;
        if (this.wall(p.x, p.z, mx, mz, p.y)) continue;
        const g = this.ground(p.x + mx, p.z + mz, p.y);
        if (g == null) continue;
        p.x += mx; p.z += mz; p.y = g; return p;
      }
      return p; // blocked on all axes — stay put
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
