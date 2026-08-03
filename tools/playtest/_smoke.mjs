/* _smoke.mjs — mechanics only, no model. Proves: boot, new game, real keys move the
 * body, pixel->world un-projection lands on the walk network, and the percept sees
 * what is drawn. Delete-safe; it is a bring-up check, not a gate. */
import { makeAdapter } from './adapter_emberbrook.mjs';
import { join, dirname } from 'path';
const ROOT = join(dirname(new URL(import.meta.url).pathname), '../..');
const port = 3000;
const a = makeAdapter({ port, framesDir: join(ROOT, 'docs/qa/playtest/runs/_smoke/frames') });
const url = a.url('emb-cine', 'woodroad');
console.log('boot', await a.open(url));
console.log('setup', await a.setup({ kind: 'newgame', scene: 'emb-cine', cam: 'woodroad' }));
console.log('settled', await a.settle());
let o = await a.observe();
console.log('percept 1:\n' + o.text);
console.log('truth', JSON.stringify(await a.truth()).slice(0, 260));
console.log('frame', o.framePath);
// read whatever is open
const lines = await a.readThrough();
console.log('read', lines.length, 'lines:', lines.slice(0,4));
await a.settle();
o = await a.observe();
console.log('percept 2:\n' + o.text);
for (const [x,y] of [[0.60,0.30],[0.55,0.22],[0.48,0.55]]) {
  const leg = await a.walkLeg(x,y);
  console.log('leg', x, y, JSON.stringify(leg));
}
o = await a.observe();
console.log('percept 3:\n' + o.text);
console.log('truth', JSON.stringify(await a.truth()).slice(0,260));
await a.close(); process.exit(0);
