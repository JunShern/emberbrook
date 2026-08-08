// glb_census.mjs — WHAT IS ACTUALLY IN A SHIPPED BUNDLE, from the bytes.
//
//   node tools/glb_census.mjs <a.glb> [<b.glb> ...]
//
// Prints, per file: the binary-glTF magic and version straight out of the header,
// byte size, chunk sizes, and the JSON's own counts (nodes / meshes / primitives /
// accessors / bufferViews / materials), plus the triangle total summed from the
// primitives' index accessors and the walk_* mesh count the runtime's collision
// contract is stated in. Two or more files are printed side by side so an export
// change can be read as a DIFF rather than as two paragraphs.
//
// It exists because "the export finished" is not "the export produced the bundle":
// the only proof of a build is the artifact (CLAUDE.md working rules), and until
// this file the only reader in the tree (glb_read.mjs) answered geometric questions
// about named meshes, never the census a provenance claim needs.
import fs from 'fs';

function census(path) {
  const buf = fs.readFileSync(path);
  const magic = buf.toString('ascii', 0, 4);
  const version = buf.readUInt32LE(4);
  const declared = buf.readUInt32LE(8);
  const out = { path, bytes: buf.length, magic, version, declared,
                lengthMatches: declared === buf.length };
  let off = 12, json = null, binLen = 0;
  while (off + 8 <= buf.length) {
    const clen = buf.readUInt32LE(off), ctype = buf.toString('ascii', off + 4, off + 8);
    const body = buf.subarray(off + 8, off + 8 + clen);
    if (ctype === 'JSON') json = JSON.parse(body.toString('utf8'));
    else if (ctype.startsWith('BIN')) binLen = clen;
    off += 8 + clen;
  }
  out.jsonChunk = json ? Buffer.byteLength(JSON.stringify(json)) : 0;
  out.binChunk = binLen;
  if (!json) { out.error = 'no JSON chunk'; return out; }
  const g = json;
  out.nodes = (g.nodes || []).length;
  out.meshes = (g.meshes || []).length;
  out.accessors = (g.accessors || []).length;
  out.bufferViews = (g.bufferViews || []).length;
  out.materials = (g.materials || []).length;
  out.images = (g.images || []).length;
  out.cameras = (g.cameras || []).length;
  out.generator = (g.asset || {}).generator || '?';
  let prims = 0, tris = 0, verts = 0;
  for (const m of g.meshes || []) {
    for (const p of m.primitives || []) {
      prims++;
      if (p.indices != null) tris += Math.floor((g.accessors[p.indices].count || 0) / 3);
      else if (p.attributes && p.attributes.POSITION != null)
        tris += Math.floor((g.accessors[p.attributes.POSITION].count || 0) / 3);
      if (p.attributes && p.attributes.POSITION != null)
        verts += g.accessors[p.attributes.POSITION].count || 0;
    }
  }
  out.primitives = prims; out.triangles = tris; out.vertices = verts;
  // walk_* is the collision contract every town bundle is read through
  const meshName = new Map();
  (g.meshes || []).forEach((m, i) => meshName.set(i, m.name || ''));
  let walkNodes = 0;
  for (const n of g.nodes || []) if (/^walk/i.test(n.name || '')) walkNodes++;
  out.walkNodes = walkNodes;
  out.walkMeshes = (g.meshes || []).filter(m => /^walk/i.test(m.name || '')).length;
  return out;
}

const files = process.argv.slice(2);
if (!files.length) { console.error('usage: node tools/glb_census.mjs <a.glb> [b.glb ...]'); process.exit(2); }
const rows = files.map(census);
const keys = ['bytes', 'magic', 'version', 'lengthMatches', 'jsonChunk', 'binChunk', 'generator',
              'nodes', 'meshes', 'primitives', 'accessors', 'bufferViews', 'materials', 'images',
              'cameras', 'vertices', 'triangles', 'walkNodes', 'walkMeshes', 'error'];
const w = Math.max(...rows.map(r => String(r.path).length), 12);
console.log('field'.padEnd(14) + rows.map(r => String(r.path).padStart(w)).join('  '));
for (const k of keys) {
  if (rows.every(r => r[k] === undefined)) continue;
  console.log(k.padEnd(14) + rows.map(r => String(r[k]).padStart(w)).join('  '));
}
const bad = rows.filter(r => r.magic !== 'glTF' || r.version !== 2 || !r.lengthMatches || r.error);
if (bad.length) { console.log('\nNOT A VALID BINARY GLTF: ' + bad.map(b => b.path).join(', ')); process.exit(1); }
console.log('\nall files: binary-glTF magic OK, version 2, declared length == file length');
