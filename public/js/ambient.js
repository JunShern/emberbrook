// ambient.js — window.Ambient: THE WORLD MOVES (director slate Bet 11, visual half).
//
// Every frame of this game used to be a still: pre-rendered plates with one moving
// character. AAA reads as alive because cheap ambient motion never stops. This module
// is that motion, as CONTENT layered on the shipped scenes — it rebuilds nothing:
//   smoke      one billboard-particle ribbon per lit chimney (meshes named *_chim
//              in the bundle — DERIVED, never authored; a scene with no named
//              chimneys gets no smoke, which is the honest answer for ow-valley's
//              merged town massing until its builder exports anchors)
//   glints     animated specular twinkle on every water_* surface (the AS BUILT
//              water of docs/plans/water-transparency.md is untouched — this
//              DECORATES it: points sampled area-weighted on the surface triangles)
//   fireflies  emb-cine only (Emberwake dusk). THEY RESPECT THE HUSH: warm sparks
//              are exactly the light the hush takes, so Hush.active() fades the
//              master alpha to zero (plus the canvas grade, which is free).
//   leaves+pollen  near-field drift in ow-valley, wrapped in a box that follows
//              the player (the ow_detail camera-relative lesson: density where
//              the player is costs no bytes anywhere else)
//   sky drift  the Bet 12 fbm cumulus get a slow two-rate advection — a RUNTIME
//              PATCH on the __owsky ShaderMaterial (the ow_detail material-patch
//              precedent), so play3d.html is not edited. Both fbm octaves move at
//              different rates: shape evolution, not wallpaper slide.
//
// ONE WIND. window.__wind {x,z,speed,t} is the shared vocabulary: smoke, leaves,
// pollen and the cloud advection all read the same vector, so the world disagrees
// with itself in no frame. Foliage may join later by reading the same global.
//
// WHY PARTICLES WORK OVER A PLATE. The towns are pre-rendered backgrounds, but
// occlusion is per-pixel REAL: play3d's DEPTHQ quad writes gl_FragDepth from
// depth.png (NoColorSpace packed metres) before anything else draws, so a smoke
// point behind a roofline loses the depth test pixel-for-pixel exactly as the
// character does. Nothing here needs to know what occludes it. depthWrite stays
// OFF (particles never occlude anyone), depthTest stays ON (the plate occludes us).
//
// THE FOLLOWERS RULE, inherited verbatim: every object is amb_-prefixed and only
// ever scene.add()ed — never pushed into collide/walkRef/allMeshes — so ambient
// art can never block a player, by construction. All motion is computed IN THE
// VERTEX SHADER from static attributes + a time uniform: per-frame CPU cost is a
// handful of uniform writes, whatever the particle count.
//
// PAUSE CONTRACT: ambient motion CONTINUES under dialogue (the point — the world
// breathes while you talk) and PAUSES under battle (battle_stage3d draws its own
// full-bleed canvas over ours; UILOCK._h.battle is the tell) by freezing the clock,
// so smoke does not teleport when the overlay drops.
//
// WHICH SPACE THE BYTES ARE IN (the r185 rule): these are ShaderMaterials, so
// three's tonemap/colorspace chunks do not enter on their own. In town scenes the
// renderer draws DIRECT to the sRGB canvas → the fragment ends with
// colorspace_fragment so our linear colours are encoded like everyone else's. In
// RT scenes the composer's OutputPass grades the whole linear buffer → the chunk
// must NOT run (it would encode twice). The material is built per scene, so the
// include is decided by the same RT flag play3d itself uses.
//
//   ?ambient=0            kills everything
//   ?amb_smoke=0 etc.     kills one effect (smoke, glint, fly, leaf, sky)
//   window.Ambient        state() / set({...}) / rebuild() / enable(false) / debug()
(function () {
  'use strict';

  var Qs; try { Qs = new URLSearchParams(location.search); } catch (e) { Qs = { get: function () { return null; } }; }
  if (Qs.get('ambient') === '0') { window.Ambient = { off: true, state: function () { return { off: true }; } }; return; }

  // play3d.html is a classic script: its top-level const/let live in the shared
  // global lexical scope (the ow_detail precedent). A missing one is a
  // ReferenceError, hence every read is fenced.
  var TH   = function () { try { return THREE; } catch (e) { return window.THREE; } };
  var SCN  = function () { try { return scene; } catch (e) { return null; } };
  var CAMR = function () { try { return cam; } catch (e) { return null; } };
  var GLB  = function () { try { return GLBROOT; } catch (e) { return null; } };
  var ISRT = function () { try { return !!RT; } catch (e) { return false; } };
  var PP   = function () { try { return P; } catch (e) { return null; } };
  var SKEY = function () {
    var s = null; try { s = SCENE; } catch (e) { }
    try { return s || new URLSearchParams(location.search).get('scene') || ''; } catch (e) { return s || ''; }
  };
  var battleUp = function () { try { return !!(window.UILOCK && UILOCK._h && UILOCK._h.battle); } catch (e) { return false; } };

  var ON = true;
  var FXON = { smoke: Qs.get('amb_smoke') !== '0', glint: Qs.get('amb_glint') !== '0',
               fly: Qs.get('amb_fly') !== '0', leaf: Qs.get('amb_leaf') !== '0',
               sky: Qs.get('amb_sky') !== '0' };

  // ---- tunables (Ambient.set({...}) then Ambient.rebuild()) ------------------------
  var Ptun = {
    windAz: 2.53,        // rad; ~145 deg — crosses the ratified key (az 238) obliquely
    windSpd: 0.55,       // m/s base; gusts modulate ±~50%
    smokeChimMax: 26,    // lit stacks cap (emb has 50 named chimneys; a town where
                         // every stack smokes reads as a fire, not as supper)
    smokeLit: 0.62,      // share of chimneys lit (deterministic per name hash)
    smokePer: 26,   // r1 judge: 'a chain of 2-3 airbrushed cotton balls' — overlap is bought with COUNT        // particles per ribbon
    smokeRise: 3.4,      // m the plume climbs over a life
    smokeLife: [7.0, 9.2],  // tight: divergent lives scatter the ribbon into balls
    smokeSize: [0.42, 1.95], // m radius, birth -> death — birth size covers the mouth gap
    smokeA: 0.30,        // peak alpha
    flyN: 120, flyA: 1.0,
    glintN: 16000,       // shared cap across all water meshes (one draw call; attrs are static)
    glintDens: 5.5,      // glints per m2 of water surface (each mesh floored at 60) — glitter is a POPULATION: 1/m2 reads as fireflies on the water, not sparkle
    glintA: 0.85, glintFade: [110, 180],  // m of VIEW depth: full -> gone (the del vista pool sits ~100 m from its lens)
    leafN: 40, pollenN: 110,
    leafBox: [26, 12, 26], // m, wrapped around a point ~11 m in front of the lens
  };

  var FX = [];            // built effects: {name, obj, mat, geo, n}
  var BUILT_FOR = null;   // scene key the current build belongs to
  var BUILD_MS = 0, SKYPATCHED = false, SKYMAT = null;
  var T = 0, lastMs = 0, RAFON = false, POLL = null;

  // ---- wind: one vector, shared ---------------------------------------------------
  function windNow() {
    var g = 1 + 0.35 * Math.sin(T * 0.13) + 0.20 * Math.sin(T * 0.047 + 1.7);
    var s = Ptun.windSpd * Math.max(0.15, g);
    var ax = Math.sin(Ptun.windAz), az = Math.cos(Ptun.windAz);
    return { x: ax * s, z: az * s, speed: s, t: T };
  }

  // ---- sprite textures (per build; disposed with the build) ------------------------
  function texSoft(TT) {   // radial gaussian-ish falloff — smoke, halos
    var c = document.createElement('canvas'); c.width = c.height = 64;
    var x = c.getContext('2d');
    var g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,0.85)'); g.addColorStop(0.35, 'rgba(255,255,255,0.42)');
    g.addColorStop(0.75, 'rgba(255,255,255,0.10)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.fillRect(0, 0, 64, 64);
    var t = new TT.CanvasTexture(c); t.colorSpace = TT.NoColorSpace; return t;
  }
  function texStar(TT) {   // 4-ray glint
    var c = document.createElement('canvas'); c.width = c.height = 64;
    var x = c.getContext('2d');
    var g = x.createRadialGradient(32, 32, 0, 32, 32, 30);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,0.35)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.fillRect(0, 0, 64, 64);
    x.globalCompositeOperation = 'lighter';
    x.strokeStyle = 'rgba(255,255,255,0.85)'; x.lineWidth = 2.2;
    x.beginPath(); x.moveTo(32, 2); x.lineTo(32, 62); x.moveTo(2, 32); x.lineTo(62, 32); x.stroke();
    var t = new TT.CanvasTexture(c); t.colorSpace = TT.NoColorSpace; return t;
  }
  function texLeaf(TT) {   // white alpha leaf, tinted per particle; 3px transparent
    var c = document.createElement('canvas'); c.width = c.height = 64;   // border + clamp = safe rotated sampling
    var x = c.getContext('2d');
    x.translate(32, 32); x.rotate(0.5);
    x.fillStyle = 'rgba(255,255,255,0.95)';
    x.beginPath(); x.ellipse(0, 0, 9, 20, 0, 0, Math.PI * 2); x.fill();
    x.strokeStyle = 'rgba(180,180,180,0.9)'; x.lineWidth = 1.4;
    x.beginPath(); x.moveTo(0, -20); x.lineTo(0, 24); x.stroke();
    var t = new TT.CanvasTexture(c); t.colorSpace = TT.NoColorSpace;
    t.wrapS = t.wrapT = TT.ClampToEdgeWrapping; return t;
  }

  // fragment tail: encode only when the town path draws direct to the sRGB canvas.
  // RT goes through the composer's OutputPass, which grades the linear buffer itself
  // (the battle_stage3d display-space lesson: say which space the bytes are in).
  // The %TAIL% marker sits INSIDE main(), after the final gl_FragColor write.
  function fragTail() { return ISRT() ? '' : '#include <colorspace_fragment>'; }
  function shader(fs) { return fs.replace('%TAIL%', fragTail()); }

  function pxScale() {
    var c = CAMR(); if (!c || !c.projectionMatrix) return 900;
    var hh; try { hh = H; } catch (e) { hh = 768; }
    return 0.5 * hh * c.projectionMatrix.elements[5];
  }

  var mulberry = function (seed) { return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    var z = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296; }; };
  function hashStr(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }

  // ---- mesh scans ------------------------------------------------------------------
  function chimAnchors() {
    var TT = TH(), root = GLB() || SCN(); if (!root) return [];
    var out = [], box = new TT.Box3();
    root.traverse(function (m) {
      if (!m.isMesh || !/(^|_)chim(ney)?(_|$|\d)/i.test(m.name || '')) return;
      box.setFromObject(m);
      if (!isFinite(box.min.x)) return;
      out.push({ name: m.name, x: (box.min.x + box.max.x) / 2, y: box.max.y + 0.06,
                 z: (box.min.z + box.max.z) / 2 });
    });
    return out;
  }
  // area-weighted random points on the up-facing triangles of matching meshes.
  // SAMPLED PER MESH, not over one combined CDF: ow's river is two orders of
  // magnitude bigger than a millpond, and a shared CDF spends the entire budget
  // on the river — the pond in the one shot that frames it gets nothing. Each
  // mesh draws area*density points, floored at minPer, under the shared cap K.
  function surfacePoints(nameRe, K, minNy, rnd, density, minPer) {
    var TT = TH(), root = GLB() || SCN(); if (!root) return [];
    var va = new TT.Vector3(), vb = new TT.Vector3(), vc = new TT.Vector3();
    var meshes = [];
    root.traverse(function (m) {
      if (!m.isMesh || !m.geometry || !nameRe.test(m.name || '')) return;
      var g = m.geometry, pos = g.attributes.position; if (!pos) return;
      m.updateWorldMatrix(true, false);
      var ix = g.index, nt = ix ? ix.count / 3 : pos.count / 3;
      var tris = [], total = 0;
      for (var t = 0; t < nt; t++) {
        var a = ix ? ix.getX(t * 3) : t * 3, b = ix ? ix.getX(t * 3 + 1) : t * 3 + 1, c = ix ? ix.getX(t * 3 + 2) : t * 3 + 2;
        va.fromBufferAttribute(pos, a).applyMatrix4(m.matrixWorld);
        vb.fromBufferAttribute(pos, b).applyMatrix4(m.matrixWorld);
        vc.fromBufferAttribute(pos, c).applyMatrix4(m.matrixWorld);
        var ux = vb.x - va.x, uy = vb.y - va.y, uz = vb.z - va.z;
        var wx = vc.x - va.x, wy = vc.y - va.y, wz = vc.z - va.z;
        var cx = uy * wz - uz * wy, cy = uz * wx - ux * wz, cz = ux * wy - uy * wx;
        var len = Math.hypot(cx, cy, cz); if (len < 1e-9) continue;
        if (Math.abs(cy) / len < minNy) continue;
        var ar = len * 0.5; total += ar;
        tris.push([va.x, va.y, va.z, ux, uy, uz, wx, wy, wz, total]);
      }
      if (tris.length) meshes.push({ tris: tris, total: total });
    });
    if (!meshes.length) return [];
    // desired counts first, then ONE proportional scale under the cap — a greedy
    // first-come budget gave del-cine's upstream pool all 16000 and its vista pool
    // ZERO (measured: 0 anchors in the vista frustum)
    var want = [], totalWant = 0;
    for (var wi = 0; wi < meshes.length; wi++) {
      var wn = density ? Math.max(minPer || 1, Math.round(meshes[wi].total * density)) : Math.round(K / meshes.length);
      want.push(wn); totalWant += wn;
    }
    var scale = totalWant > K ? K / totalWant : 1;
    var pts = [];
    for (var mi = 0; mi < meshes.length; mi++) {
      var M = meshes[mi];
      var n = Math.max(1, Math.round(want[mi] * scale));
      for (var k = 0; k < n; k++) {
        var r = rnd() * M.total, lo = 0, hi = M.tris.length - 1;
        while (lo < hi) { var mid = (lo + hi) >> 1; if (M.tris[mid][9] < r) lo = mid + 1; else hi = mid; }
        var tr = M.tris[lo], u = rnd(), v = rnd();
        if (u + v > 1) { u = 1 - u; v = 1 - v; }
        pts.push([tr[0] + tr[3] * u + tr[6] * v, tr[1] + tr[4] * u + tr[7] * v, tr[2] + tr[5] * u + tr[8] * v]);
      }
    }
    return pts;
  }

  // ---- effect builders -------------------------------------------------------------
  function addFx(name, obj, mat, geo, n, tex) {
    obj.name = 'amb_' + name; obj.frustumCulled = false; obj.renderOrder = 40;
    SCN().add(obj);
    FX.push({ name: name, obj: obj, mat: mat, geo: geo, n: n, tex: tex || null });
  }

  function buildSmoke() {
    var TT = TH(), anchors = chimAnchors();
    if (!anchors.length) return 'no chimneys named in bundle';
    // deterministic lit subset — a hash on the stack's own name, so the same houses
    // smoke on every visit (a town whose fires move between loads reads as a bug)
    var lit = anchors.filter(function (a) { return (hashStr(a.name) % 1000) / 1000 < Ptun.smokeLit; });
    if (!lit.length) lit = [anchors[0]];
    lit = lit.slice(0, Ptun.smokeChimMax);
    var n = lit.length * Ptun.smokePer, pos = new Float32Array(n * 3), aR = new Float32Array(n * 4);
    var rnd = mulberry(20260806), i = 0;
    for (var c = 0; c < lit.length; c++) for (var p = 0; p < Ptun.smokePer; p++, i++) {
      pos[i * 3] = lit[c].x; pos[i * 3 + 1] = lit[c].y; pos[i * 3 + 2] = lit[c].z;
      aR[i * 4] = rnd();                                                   // phase
      aR[i * 4 + 1] = Ptun.smokeLife[0] + rnd() * (Ptun.smokeLife[1] - Ptun.smokeLife[0]); // life s
      aR[i * 4 + 2] = rnd();                                               // seed
      aR[i * 4 + 3] = 0.75 + rnd() * 0.5;                                  // size mul
    }
    var geo = new TT.BufferGeometry();
    geo.setAttribute('position', new TT.BufferAttribute(pos, 3));
    geo.setAttribute('aR', new TT.BufferAttribute(aR, 4));
    var dusk = /^emb-/.test(SKEY());
    var tex = texSoft(TT);
    var mat = new TT.ShaderMaterial({
      uniforms: { uT: { value: 0 }, uWind: { value: new TT.Vector3() }, uPx: { value: 900 },
                  uTex: { value: tex }, uA: { value: Ptun.smokeA },
                  uCol: { value: new TT.Color(dusk ? 0x9fa2b8 : 0xd8ccba) },
                  uRise: { value: Ptun.smokeRise },
                  uSz: { value: new TT.Vector2(Ptun.smokeSize[0], Ptun.smokeSize[1]) } },
      vertexShader: [
        'attribute vec4 aR;',
        'uniform float uT,uPx,uRise; uniform vec3 uWind; uniform vec2 uSz;',
        'varying float vA;',
        'void main(){',
        '  float t=fract(uT/aR.y+aR.x);',
        '  vec3 p=position;',
        '  p.y+=uRise*(0.85+0.3*fract(aR.z*7.31))*pow(t,0.8);',
        '  p.xz+=uWind.xz*(0.78+0.22*fract(aR.z*3.7))*t*t*aR.y*0.5;',   // wind takes over with height
        '  p.x+=sin(uT*0.22+aR.z*37.0+t*2.6)*0.11*t;',
        '  p.z+=cos(uT*0.19+aR.z*57.0+t*2.2)*0.11*t;',
        '  vec4 mv=modelViewMatrix*vec4(p,1.0);',
        '  gl_PointSize=clamp(mix(uSz.x,uSz.y,t)*aR.w*uPx/max(1.0,-mv.z),1.0,220.0);',
        '  vA=smoothstep(0.0,0.06,t)*(1.0-smoothstep(0.45,1.0,t));',
        '  gl_Position=projectionMatrix*mv;',
        '}'].join('\n'),
      fragmentShader: shader([
        'uniform vec3 uCol; uniform sampler2D uTex; uniform float uA;',
        'varying float vA;',
        'void main(){',
        '  float a=texture2D(uTex,gl_PointCoord).a*vA*uA;',
        '  if(a<0.004) discard;',
        '  gl_FragColor=vec4(uCol,a);',
        '%TAIL%',
        '}'].join('\n')),
      transparent: true, depthWrite: false, depthTest: true });
    addFx('smoke', new TT.Points(geo, mat), mat, geo, n, tex);
    return lit.length + ' chimneys, ' + n + ' particles';
  }

  function buildGlints() {
    var TT = TH(), rnd = mulberry(20260807);
    var pts = surfacePoints(/(^|_)water(_|$)|^water_|whitewater/i, Ptun.glintN, 0.55, rnd, Ptun.glintDens, 60);
    if (!pts.length) return 'no water surfaces';
    var n = pts.length, pos = new Float32Array(n * 3), aR = new Float32Array(n * 4);
    for (var i = 0; i < n; i++) {
      pos[i * 3] = pts[i][0]; pos[i * 3 + 1] = pts[i][1] + 0.04; pos[i * 3 + 2] = pts[i][2];
      aR[i * 4] = rnd() * 6.2831853;            // phase
      aR[i * 4 + 1] = 1.4 + rnd() * 2.8;        // period s
      aR[i * 4 + 2] = rnd();                    // seed
      aR[i * 4 + 3] = 0.045 + rnd() * 0.075;    // size m
    }
    var geo = new TT.BufferGeometry();
    geo.setAttribute('position', new TT.BufferAttribute(pos, 3));
    geo.setAttribute('aR', new TT.BufferAttribute(aR, 4));
    var tex = texStar(TT);
    var mat = new TT.ShaderMaterial({
      uniforms: { uT: { value: 0 }, uPx: { value: 900 }, uTex: { value: tex },
                  uA: { value: Ptun.glintA }, uCtr: { value: new TT.Vector3() },
                  uFade: { value: new TT.Vector2(Ptun.glintFade[0], Ptun.glintFade[1]) },
                  uCol: { value: new TT.Color(0xfff0c8) } },
      vertexShader: [
        'attribute vec4 aR;',
        'uniform float uT,uPx; uniform vec2 uFade;',
        'varying float vA;',
        'void main(){',
        '  vec3 p=position;',
        '  float tw=pow(max(sin(uT*6.2831853/aR.y+aR.x),0.0),20.0);',   // sharp intermittent flash
        // a slow travelling shimmer field, so the twinkles cluster and MOVE as a
        // body down the river instead of firing as uncorrelated static
        '  float wave=0.5+0.5*sin(uT*0.35+p.x*0.33+p.z*0.27+aR.z*2.0);',
        '  vec4 mv=modelViewMatrix*vec4(p,1.0);',
        '  gl_PointSize=clamp(aR.w*(0.55+1.65*tw)*uPx/max(1.0,-mv.z),1.0,26.0);',
        // fade on LENS distance, not player distance: a cine plate frames water the
        // body never stands near (Dellhollow's vista pool), and the sparkle budget
        // must go where the CAMERA is looking
        '  float d=-mv.z;',
        '  vA=(0.10*wave*wave+tw*wave)*(1.0-smoothstep(uFade.x,uFade.y,d));',
        '  gl_Position=projectionMatrix*mv;',
        '}'].join('\n'),
      fragmentShader: shader([
        'uniform vec3 uCol; uniform sampler2D uTex; uniform float uA;',
        'varying float vA;',
        'void main(){',
        '  float a=texture2D(uTex,gl_PointCoord).a*vA*uA;',
        '  if(a<0.004) discard;',
        '  gl_FragColor=vec4(uCol,a);',
        '%TAIL%',
        '}'].join('\n')),
      transparent: true, depthWrite: false, depthTest: true, blending: TT.AdditiveBlending });
    addFx('glint', new TT.Points(geo, mat), mat, geo, n, tex);
    return n + ' glints';
  }

  function buildFireflies() {
    var TT = TH(), rnd = mulberry(20260808);
    // anchors hover over the WALK surfaces — the paths are where every cine camera
    // already looks, and the walk mesh y is the true ground (no probe needed)
    var pts = surfacePoints(/^walk_/, Ptun.flyN, 0.5, rnd);
    if (!pts.length) return 'no walk surfaces';
    // the per-mesh floor of 1 overshoots K when a town has hundreds of walk
    // meshes — shuffle (deterministic) and cut back to the roster
    for (var sh = pts.length - 1; sh > 0; sh--) { var sj = (rnd() * (sh + 1)) | 0; var tmp = pts[sh]; pts[sh] = pts[sj]; pts[sj] = tmp; }
    pts = pts.slice(0, Ptun.flyN);
    var n = pts.length, pos = new Float32Array(n * 3), aR = new Float32Array(n * 4);
    for (var i = 0; i < n; i++) {
      pos[i * 3] = pts[i][0] + (rnd() - 0.5) * 4.0;
      pos[i * 3 + 1] = pts[i][1] + 0.35 + rnd() * 1.5;
      pos[i * 3 + 2] = pts[i][2] + (rnd() - 0.5) * 4.0;
      aR[i * 4] = rnd() * 6.2831853;         // wander phase
      aR[i * 4 + 1] = 0.10 + rnd() * 0.16;   // wander rate rad/s
      aR[i * 4 + 2] = rnd();                 // seed
      aR[i * 4 + 3] = 0.25 + rnd() * 0.5;    // blink rate Hz-ish
    }
    var geo = new TT.BufferGeometry();
    geo.setAttribute('position', new TT.BufferAttribute(pos, 3));
    geo.setAttribute('aR', new TT.BufferAttribute(aR, 4));
    var tex = texSoft(TT);
    var mat = new TT.ShaderMaterial({
      uniforms: { uT: { value: 0 }, uPx: { value: 900 }, uTex: { value: tex },
                  uA: { value: Ptun.flyA }, uCol: { value: new TT.Color(0xffd98a) },
                  uCol2: { value: new TT.Color(0xd8f0a0) } },
      vertexShader: [
        'attribute vec4 aR;',
        'uniform float uT,uPx;',
        'varying float vA; varying float vMix;',
        'void main(){',
        '  vec3 p=position;',
        '  float w=uT*aR.y*6.2831853;',
        '  p.x+=sin(w+aR.x)*0.9; p.z+=cos(w*0.83+aR.x*1.7)*0.9;',
        '  p.y+=sin(w*1.31+aR.x*2.3)*0.45;',
        '  float s=sin(uT*aR.w*6.2831853+aR.x*3.0);',
        '  float glow=smoothstep(0.55,0.92,s);',                 // mostly dark, brief pulses
        '  vec4 mv=modelViewMatrix*vec4(p,1.0);',
        '  gl_PointSize=clamp(0.13*(0.55+glow)*uPx/max(1.0,-mv.z),1.5,26.0);',
        '  vA=0.05+0.95*glow; vMix=fract(aR.z*5.7);',
        '  gl_Position=projectionMatrix*mv;',
        '}'].join('\n'),
      fragmentShader: shader([
        'uniform vec3 uCol,uCol2; uniform sampler2D uTex; uniform float uA;',
        'varying float vA; varying float vMix;',
        'void main(){',
        '  float a=texture2D(uTex,gl_PointCoord).a*vA*uA;',
        '  if(a<0.004) discard;',
        '  gl_FragColor=vec4(mix(uCol,uCol2,step(0.8,vMix)),a);',
        '%TAIL%',
        '}'].join('\n')),
      transparent: true, depthWrite: false, depthTest: true, blending: TT.AdditiveBlending });
    addFx('fly', new TT.Points(geo, mat), mat, geo, n, tex);
    return n + ' fireflies';
  }

  function buildLeaves() {
    var TT = TH(), rnd = mulberry(20260809);
    var B = Ptun.leafBox, nL = Ptun.leafN, nP = Ptun.pollenN;
    // pollen — faint golden motes, additive
    var posP = new Float32Array(nP * 3), aRP = new Float32Array(nP * 4);
    for (var i = 0; i < nP; i++) {
      posP[i * 3] = rnd() * B[0]; posP[i * 3 + 1] = rnd() * B[1]; posP[i * 3 + 2] = rnd() * B[2];
      aRP[i * 4] = rnd() * 6.2831853; aRP[i * 4 + 1] = 0.4 + rnd() * 0.8;
      aRP[i * 4 + 2] = rnd(); aRP[i * 4 + 3] = 0.020 + rnd() * 0.026;   // size m
    }
    var geoP = new TT.BufferGeometry();
    geoP.setAttribute('position', new TT.BufferAttribute(posP, 3));
    geoP.setAttribute('aR', new TT.BufferAttribute(aRP, 4));
    var texP2 = texSoft(TT);
    // uWindI is the CPU-ACCUMULATED wind integral, not wind*t: a gust changing the
    // instantaneous vector must bend the drift from here on, not re-price every
    // second already travelled (wind*t folds the whole history through the new
    // gust — at t=600 s a 0.1 m/s gust step teleports every mote 60 m).
    var wrapVS = function (extra, size, rot) { return [
      'attribute vec4 aR;' + (rot ? ' attribute vec3 aC;' : ''),
      'uniform float uT,uPx,uTopY; uniform vec3 uCtr,uBox,uWindI;',
      'varying float vA;' + (rot ? ' varying float vRot; varying vec3 vC;' : ''),
      'void main(){',
      '  vec3 drift=vec3(uWindI.x,0.0,uWindI.z)*' + (rot ? '0.9' : '0.28') + ';',
      extra,
      '  vec3 raw=position+drift+bob;',
      '  vec3 rel=mod(raw,uBox)-0.5*uBox;',
      '  vec3 p=uCtr+rel;',   // uCtr is a point on the view axis — the box is centred on it
      // fade at the wrap faces so recycling never pops in frame
      '  vec3 e=1.0-smoothstep(0.5*uBox-vec3(2.0),0.5*uBox,abs(rel));',
      // never above the treetops: a mote crossing the SKY band reads as a bird-
      // sized artifact at the vista pitch, so fade everything out above the player
      '  float top=1.0-smoothstep(uTopY,uTopY+3.0,p.y);',
      '  vec4 mv=modelViewMatrix*vec4(p,1.0);',
      '  gl_PointSize=clamp(' + size + '*uPx/max(1.0,-mv.z),1.0,42.0);',
      '  vA=e.x*e.y*e.z*top;',
      (rot ? '  vRot=aR.x+uT*(aR.y*2.0-1.2); vC=aC;' : ''),
      '  gl_Position=projectionMatrix*mv;',
      '}'].join('\n'); };
    var matP = new TT.ShaderMaterial({
      uniforms: { uT: { value: 0 }, uPx: { value: 900 }, uTex: { value: texP2 },
                  uA: { value: 0.30 }, uCol: { value: new TT.Color(0xffe6b0) },
                  uCtr: { value: new TT.Vector3() }, uBox: { value: new TT.Vector3(B[0], B[1], B[2]) },
                  uWindI: { value: new TT.Vector3() }, uTopY: { value: 1e6 } },
      vertexShader: wrapVS(
        '  vec3 bob=vec3(sin(uT*0.5+aR.x)*0.6, sin(uT*0.7+aR.x*1.9)*0.5-0.03*uT, cos(uT*0.45+aR.x*2.7)*0.6);',
        'aR.w', false),
      fragmentShader: shader([
        'uniform vec3 uCol; uniform sampler2D uTex; uniform float uA;',
        'varying float vA;',
        'void main(){',
        '  float a=texture2D(uTex,gl_PointCoord).a*vA*uA;',
        '  if(a<0.004) discard;',
        '  gl_FragColor=vec4(uCol,a);',
        '%TAIL%',
        '}'].join('\n')),
      transparent: true, depthWrite: false, depthTest: true, blending: TT.AdditiveBlending });
    addFx('pollen', new TT.Points(geoP, matP), matP, geoP, nP, texP2);

    // leaves — tinted cards, tumbling; slow fall folded into the wrap
    var posL = new Float32Array(nL * 3), aRL = new Float32Array(nL * 4), aC = new Float32Array(nL * 3);
    var PAL = [[0.54, 0.35, 0.17], [0.66, 0.45, 0.18], [0.42, 0.42, 0.18], [0.61, 0.31, 0.16]];
    for (var j = 0; j < nL; j++) {
      posL[j * 3] = rnd() * B[0]; posL[j * 3 + 1] = rnd() * B[1]; posL[j * 3 + 2] = rnd() * B[2];
      aRL[j * 4] = rnd() * 6.2831853; aRL[j * 4 + 1] = rnd();
      aRL[j * 4 + 2] = rnd(); aRL[j * 4 + 3] = 0.085 + rnd() * 0.06;   // size m
      var cc = PAL[(rnd() * PAL.length) | 0];
      aC[j * 3] = cc[0]; aC[j * 3 + 1] = cc[1]; aC[j * 3 + 2] = cc[2];
    }
    var geoL = new TT.BufferGeometry();
    geoL.setAttribute('position', new TT.BufferAttribute(posL, 3));
    geoL.setAttribute('aR', new TT.BufferAttribute(aRL, 4));
    geoL.setAttribute('aC', new TT.BufferAttribute(aC, 3));
    var texL = texLeaf(TT);
    var matL = new TT.ShaderMaterial({
      uniforms: { uT: { value: 0 }, uPx: { value: 900 }, uTex: { value: texL },
                  uA: { value: 0.9 },
                  uCtr: { value: new TT.Vector3() }, uBox: { value: new TT.Vector3(B[0], B[1], B[2]) },
                  uWindI: { value: new TT.Vector3() }, uTopY: { value: 1e6 } },
      vertexShader: wrapVS(
        '  vec3 bob=vec3(sin(uT*1.7+aR.x)*0.45, -0.34*uT+sin(uT*2.1+aR.x*1.3)*0.30, cos(uT*1.5+aR.x*2.2)*0.45);',
        'aR.w', true),
      fragmentShader: shader([
        'uniform sampler2D uTex; uniform float uA;',
        'varying float vA; varying float vRot; varying vec3 vC;',
        'void main(){',
        '  vec2 pc=gl_PointCoord-0.5;',
        '  float c=cos(vRot),s=sin(vRot);',
        '  pc=vec2(c*pc.x-s*pc.y,s*pc.x+c*pc.y)+0.5;',
        '  vec4 t=texture2D(uTex,pc);',
        '  float a=t.a*vA*uA;',
        '  if(a<0.02) discard;',
        '  gl_FragColor=vec4(vC*t.r,a);',
        '%TAIL%',
        '}'].join('\n')),
      transparent: true, depthWrite: false, depthTest: true });
    addFx('leaf', new TT.Points(geoL, matL), matL, geoL, nL, texL);
    return nP + ' pollen + ' + nL + ' leaves';
  }

  // ---- cloud drift: runtime patch on the Bet 12 sky dome ---------------------------
  var CD_SRC = 'float cd(vec2 p){ return fbm(p*0.55+vec2(3.7,8.2))+0.35*fbm(p*1.7+vec2(11.0,4.0)); }';
  var CD_NEW = 'float cd(vec2 p){ vec2 w=uDrift*uT; return fbm(p*0.55+w*0.55+vec2(3.7,8.2))+0.35*fbm(p*1.7+w*1.15+vec2(11.0,4.0)); }';
  function patchSky() {
    SKYPATCHED = false; SKYMAT = null;
    var sc = SCN(); if (!sc) return 'no scene';
    var TT = TH(), sky = null;
    sc.traverse(function (o) { if (o.name === '__owsky' && o.material && o.material.isShaderMaterial) sky = o; });
    if (!sky) return 'no shader sky';
    var m = sky.material;
    if (m.fragmentShader.indexOf('uDrift') !== -1) { SKYPATCHED = true; SKYMAT = m; return 'already patched'; }
    if (m.fragmentShader.indexOf(CD_SRC) === -1) return 'cd() not found (sky changed?)';
    var w = windNow();
    var wl = Math.hypot(w.x, w.z) || 1;
    m.uniforms.uT = { value: 0 };
    // plane-units/s: full first-octave cell in ~2 min at base wind. The two octaves
    // advect at DIFFERENT rates so the bank changes shape as it travels.
    m.uniforms.uDrift = { value: new TT.Vector2(w.x / wl * 0.016, w.z / wl * 0.016) };
    m.fragmentShader = m.fragmentShader
      .replace('uniform vec3 uZen', 'uniform float uT; uniform vec2 uDrift;\nuniform vec3 uZen')
      .replace(CD_SRC, CD_NEW);
    m.needsUpdate = true;
    SKYPATCHED = true; SKYMAT = m;
    return 'patched';
  }

  // ---- build / teardown ------------------------------------------------------------
  var REPORT = {};
  function teardown() {
    var sc = SCN();
    for (var i = 0; i < FX.length; i++) {
      var f = FX[i];
      try { if (sc && f.obj.parent) f.obj.parent.remove(f.obj); } catch (e) { }
      try { f.geo.dispose(); } catch (e) { }
      try { f.mat.dispose(); } catch (e) { }
      try { if (f.tex) f.tex.dispose(); } catch (e) { }
    }
    FX = []; BUILT_FOR = null; SKYPATCHED = false; SKYMAT = null; REPORT = {};
  }

  function build() {
    if (!ON) return;
    var t0 = performance.now(), key = SKEY();
    REPORT = { scene: key };
    var interior = /-int$/.test(key);
    if (!interior) {
      if (FXON.smoke) { try { REPORT.smoke = buildSmoke(); } catch (e) { REPORT.smoke = 'ERR ' + e.message; console.warn('[Ambient] smoke', e); } }
      if (FXON.glint) { try { REPORT.glint = buildGlints(); } catch (e) { REPORT.glint = 'ERR ' + e.message; console.warn('[Ambient] glint', e); } }
      if (FXON.fly && /^emb-cine/.test(key)) { try { REPORT.fly = buildFireflies(); } catch (e) { REPORT.fly = 'ERR ' + e.message; console.warn('[Ambient] fly', e); } }
      if (FXON.leaf && /^ow-/.test(key)) { try { REPORT.leaf = buildLeaves(); } catch (e) { REPORT.leaf = 'ERR ' + e.message; console.warn('[Ambient] leaf', e); } }
      if (FXON.sky) { try { REPORT.sky = patchSky(); } catch (e) { REPORT.sky = 'ERR ' + e.message; console.warn('[Ambient] sky', e); } }
    }
    BUILD_MS = +(performance.now() - t0).toFixed(1);
    BUILT_FOR = key;
    console.log('[Ambient] built for ' + key + ' in ' + BUILD_MS + 'ms', REPORT);
  }

  // the bundle parses long after 'eb-scene' fires — poll until GLBROOT is up
  // (the ow_detail pattern), then build once per scene key
  function schedule() {
    if (POLL) { clearInterval(POLL); POLL = null; }
    var key = SKEY(), tries = 0;
    POLL = setInterval(function () {
      try {
        if (SKEY() !== key) { key = SKEY(); tries = 0; teardown(); }
        if (BUILT_FOR === key) { clearInterval(POLL); POLL = null; return; }
        if (++tries > 120) { clearInterval(POLL); POLL = null; return; }   // 60 s: give up quietly
        if (!GLB() || !SCN()) return;
        build();
      } catch (e) { console.warn('[Ambient] build poll', e); }
    }, 500);
  }

  // ---- the frame -------------------------------------------------------------------
  var _dir = null;                     // scratch vec3, allocated on first use
  var WINDI = { x: 0, z: 0 };          // integral of the wind — see wrapVS
  var skyRetryAt = 0;
  function frameTick() {
    var now = performance.now();
    var dt = lastMs ? Math.min(0.05, (now - lastMs) / 1000) : 0.016;
    lastMs = now;
    if (!ON || battleUp()) return;      // the clock freezes under the battle overlay
    T += dt;
    var w = windNow();
    WINDI.x += w.x * dt; WINDI.z += w.z * dt;
    window.__wind = { x: w.x, z: w.z, speed: w.speed, t: T };
    // the sky dome is built late in the spawn chain — retry the patch until it lands
    if (FXON.sky && !SKYPATCHED && BUILT_FOR && T > skyRetryAt) {
      skyRetryAt = T + 2.0;
      try { REPORT.sky = patchSky(); } catch (e) { }
    }
    var px = pxScale(), pp = PP();
    if (!_dir) { var TT0 = TH(); if (TT0) _dir = new TT0.Vector3(); }
    var hushOn = false; try { hushOn = !!(window.Hush && Hush.active()); } catch (e) { }
    for (var i = 0; i < FX.length; i++) {
      var u = FX[i].mat.uniforms;
      if (u.uT) u.uT.value = T;
      if (u.uPx) u.uPx.value = px;
      if (u.uWind) u.uWind.value.set(w.x, 0, w.z);
      if (u.uWindI) u.uWindI.value.set(WINDI.x, 0, WINDI.z);
      if (u.uCtr) {
        if (FX[i].name === 'pollen' || FX[i].name === 'leaf') {
          // NEAR-FIELD MEANS NEAR THE LENS. A 2 cm mote is sub-pixel at the 40 m
          // boom if the box follows the PLAYER; centred ~11 m down the view axis
          // it drifts through the frustum where it subtends pixels. (Measured:
          // player-centred pollen at the shipped boom was 0 visible pixels.)
          var cc = CAMR();
          if (cc) {
            cc.getWorldDirection(_dir);
            u.uCtr.value.set(cc.position.x + _dir.x * 11, cc.position.y + _dir.y * 11, cc.position.z + _dir.z * 11);
          } else if (pp) u.uCtr.value.set(pp.x, pp.y, pp.z);
        } else if (pp) u.uCtr.value.set(pp.x, pp.y, pp.z);
      }
      if (u.uTopY && pp) u.uTopY.value = pp.y + 7.0;
      if (FX[i].name === 'fly' && u.uA) {
        // THE HUSH TAKES THE WARM LIGHTS, fireflies included — ease them out over ~2 s
        var target = hushOn ? 0 : Ptun.flyA;
        u.uA.value += (target - u.uA.value) * Math.min(1, dt * 2.0);
      }
    }
    if (SKYPATCHED && SKYMAT && SKYMAT.uniforms.uT) SKYMAT.uniforms.uT.value = T;
  }
  function raf() { frameTick(); requestAnimationFrame(raf); }

  // ---- module contract -------------------------------------------------------------
  function arm() {
    if (!RAFON) { RAFON = true; requestAnimationFrame(raf); }
    schedule();
  }
  if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('eb-scene', function () {
      try { teardown(); } catch (e) { console.error('[Ambient] eb-scene teardown', e); }
      try { schedule(); } catch (e) { console.error('[Ambient] eb-scene schedule', e); }
    });
  }

  window.Ambient = {
    state: function () { return { on: ON, scene: BUILT_FOR, fx: FX.map(function (f) { return f.name + ':' + f.n; }), report: REPORT, buildMs: BUILD_MS, wind: window.__wind || null, sky: SKYPATCHED }; },
    set: function (o) { for (var k in o) if (k in Ptun) Ptun[k] = o[k]; return Ptun; },
    rebuild: function () { teardown(); build(); return REPORT; },
    enable: function (on) { ON = on !== false; if (!ON) teardown(); else schedule(); return ON; },
    debug: function () { return { report: REPORT, params: Ptun, fxon: FXON, t: T }; },
  };

  arm();
  setTimeout(arm, 1500);   // the first bundle may land after us
})();
