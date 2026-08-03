/**
 * The source of public/lib/three.min.js — see tools/build_three_lib.mjs.
 *
 * WHY A BUNDLE AND NOT AN IMPORT MAP. Modern three ships ESM only, and this page
 * is ~140 `THREE.` call sites across one inline <script> and fourteen classic
 * <script src> modules that self-arm at load AND on 'eb-scene'. Turning them into
 * modules changes their SCOPE (a module's top-level `const` is not a global) and
 * their TIMING (modules are deferred), which is a second, unrelated migration
 * riding on a renderer upgrade. An IIFE that publishes `globalThis.THREE` keeps
 * the load order and the scope rules exactly as r128's UMD build had them, so the
 * only thing that changes in this upgrade is three.js.
 *
 * ONE BUNDLE, ONE COPY OF THREE. three-mesh-bvh imports `three`; bundled here it
 * shares this file's classes. Two copies would break every `instanceof` between
 * them, and the BVH's own index-permutation trap (see play3d.html) is hard enough
 * to see without that on top.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
// DRACOLoader rides along because tools/build-static.mjs --draco needs one that
// MATCHES this three; the r128 era loaded a separate classic examples/js file,
// which modern three does not publish. Only the decoder binaries stay external
// (they are wasm, and they are what the build vendors into dist/lib/draco).
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
// POST-PROCESSING (2026-08-03). The r185 upgrade bought the capability; these six
// modules are it. They ride in THIS bundle rather than as <script src> tags for
// the same reason GLTFLoader does: they `import` three, and a second copy of three
// would give every pass its own WebGLRenderTarget/Vector2/ShaderMaterial classes,
// so `instanceof` between a pass and the renderer's own state would be false and
// the failure would look like a driver bug rather than a packaging one.
// EffectComposer + RenderPass + OutputPass are the frame; GTAOPass is the effect
// that actually changes the picture (see THE POST STACK in play3d.html for which
// scene families get it and why the baked-plate towns do not).
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import * as MeshBVHLib from 'three-mesh-bvh';

// the ESM namespace object is frozen, so the additive names go on a copy. Every
// mutable table inside it (ShaderChunk, ShaderLib, ...) is still the SAME object,
// which is what play3d.html's shader surgery relies on.
const NS = Object.assign({}, THREE, { GLTFLoader, DRACOLoader,
  EffectComposer, RenderPass, OutputPass, ShaderPass, GTAOPass, UnrealBloomPass });

globalThis.THREE = NS;
globalThis.MeshBVHLib = MeshBVHLib;
