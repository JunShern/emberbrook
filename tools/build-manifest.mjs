#!/usr/bin/env node
// Scans public/assets/{characters,scenes,refs} into public/assets/assets-manifest.json,
// which assets.html renders as the browsable asset explorer.
// Run after any asset generation: node tools/build-manifest.mjs

import fs from 'fs';
import path from 'path';

const root = path.join(import.meta.dirname, '..');
const A = path.join(root, 'public/assets');

const listPngs = (dir) => {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.png'))
    .sort()
    .map(f => ({ name: f, kb: Math.round(fs.statSync(path.join(dir, f)).size / 1024) }));
};

const scanGroup = (groupDir) => {
  const out = {};
  if (!fs.existsSync(groupDir)) return out;
  for (const name of fs.readdirSync(groupDir).sort()) {
    const dir = path.join(groupDir, name);
    if (!fs.statSync(dir).isDirectory()) continue;
    out[name] = {
      files: listPngs(dir),
      candidates: listPngs(path.join(dir, 'candidates')),
    };
  }
  return out;
};

// merge playbook prompts if the char-manifest exists
let prompts = {};
const cm = path.join(A, 'char-manifest.json');
if (fs.existsSync(cm)) {
  const m = JSON.parse(fs.readFileSync(cm, 'utf8'));
  for (const [name, data] of Object.entries(m))
    prompts[name] = Object.fromEntries(
      Object.entries(data.stages || {}).map(([id, s]) => [s.file.split('/').pop(), s.prompt]));
}

const manifest = {
  generated: new Date().toISOString(),
  characters: scanGroup(path.join(A, 'characters')),
  scenes: scanGroup(path.join(A, 'scenes')),
  refs: listPngs(path.join(A, 'refs')),
  prompts,
};

fs.writeFileSync(path.join(A, 'assets-manifest.json'), JSON.stringify(manifest, null, 2));
const counts = (g) => Object.entries(g).map(([k, v]) => `${k}:${v.files.length}+${v.candidates.length}c`).join(' ');
console.log('characters →', counts(manifest.characters));
console.log('scenes     →', counts(manifest.scenes));
console.log('refs       →', manifest.refs.length, 'files');
console.log('wrote public/assets/assets-manifest.json');
