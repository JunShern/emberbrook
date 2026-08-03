/**
 * node tools/build_three_lib.mjs — rebuild public/lib/three.min.js from
 * tools/three_lib_entry.js (three + GLTFLoader + three-mesh-bvh, one IIFE,
 * `globalThis.THREE` / `globalThis.MeshBVHLib`, plus a CommonJS tail so
 * tools/walk_engine_gate.mjs can `require()` the very file the browser runs).
 *
 * Needs the dev deps: npm i --no-save three three-mesh-bvh esbuild
 * The ARTIFACT is committed — this repo has no build step at serve time, and a
 * runtime asset that is not in git is a bug that only reproduces off the author's
 * machine (see public/game/lightrigs.json in CLAUDE.md).
 */
import { build } from 'esbuild';
import { readFileSync, statSync } from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const OUT = new URL('../public/lib/three.min.js', import.meta.url).pathname;

const vThree = JSON.parse(readFileSync(new URL('../node_modules/three/package.json', import.meta.url),'utf8')).version;
const vBVH = JSON.parse(readFileSync(new URL('../node_modules/three-mesh-bvh/package.json', import.meta.url),'utf8')).version;

await build({
  entryPoints: [new URL('three_lib_entry.js', import.meta.url).pathname],
  bundle: true, format: 'iife', minify: true, target: 'es2020',
  // DRACOLoader resolves its DEFAULT decoder URLs at module scope with
  // `new URL('../libs/...', import.meta.url)`, and an IIFE has no import.meta —
  // esbuild leaves it empty and `new URL` throws on load, taking the whole bundle
  // with it. The defaults are overridden by setDecoderPath() in every caller here
  // (tools/build-static.mjs --draco), so all this has to be is a VALID base in
  // both a browser and Node's require().
  // (a define value must be a literal or an entity name, so the expression lives
  // in a banner-declared global rather than inline.)
  define: { 'import.meta.url': '__EB_BASE_URL' },
  outfile: OUT, legalComments: 'none',
  banner: { js: `var __EB_BASE_URL=(typeof document!=='undefined'&&document.baseURI)||'file:///';\n/* three ${vThree} + three-mesh-bvh ${vBVH} — built by tools/build_three_lib.mjs. DO NOT EDIT. */` },
  // `module` exists in Node's CommonJS scope and not in a browser's; the guard is
  // what lets walk_engine_gate require() the same bytes the page loads.
  footer: { js: `if(typeof module!=="undefined"&&module.exports){module.exports=globalThis.THREE;module.exports.MeshBVHLib=globalThis.MeshBVHLib;}` },
});

// THE PROOF IS THE ARTIFACT, never the report: read the file back and ask it its
// own revision through the same require() path the gates use.
delete require.cache[OUT];
const T = require(OUT);
const kb = (statSync(OUT).size / 1024).toFixed(0);
if (!T || !T.REVISION) { console.error('BUILT BUT DEAD: no REVISION on the require()d bundle'); process.exit(1); }
if (!T.MeshBVHLib || !T.MeshBVHLib.MeshBVH) { console.error('BUILT BUT DEAD: no MeshBVHLib.MeshBVH'); process.exit(1); }
if (!T.GLTFLoader) { console.error('BUILT BUT DEAD: no GLTFLoader'); process.exit(1); }
if (!T.DRACOLoader) { console.error('BUILT BUT DEAD: no DRACOLoader'); process.exit(1); }
console.log(`SAVED ${OUT}  r${T.REVISION} (three ${vThree}, three-mesh-bvh ${vBVH})  ${kb} KB`);
