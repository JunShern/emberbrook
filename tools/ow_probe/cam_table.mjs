#!/usr/bin/env node
/* cam_table.mjs — read cam_sweep's rows and print the trade the sweep is about.
 *   node tools/ow_probe/cam_table.mjs <rows.json> [--by station|cand] [--sort key]
 *
 * The columns are the four things Bet 5 has to hold at once, and they pull against
 * each other: PLYR (where the body sits in the frame, 0.61-0.63 in the references,
 * 0.818 as shipped), AIR (sky + ridge, the reference's distance band), COVER/AREA
 * (the user's ONE hard constraint — a wide view of the ground around the player),
 * and CLR (metres of air under the boom; this rig has no camera collision, so a
 * small number here is the frame going into a hillside).
 */
import { readFileSync } from 'fs';
import { mkArg } from '../argv.mjs';
const { arg } = mkArg(process.argv);
const rows = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const key = r => `${r.pitch.toFixed(2)}/${r.tilt.toFixed(2)}${r.panY ? '/+' + r.panY : ''}`;

const by = arg('by', 'cand');
if (by === 'station') {
  for (const st of [...new Set(rows.map(r => r.station))]) {
    console.log(`\n== ${st}`);
    hdr(); for (const r of rows.filter(r => r.station === st)) line(r);
  }
} else {
  const cands = [...new Set(rows.map(key))];
  const agg = cands.map(c => {
    const rs = rows.filter(r => key(r) === c);
    const m = k => rs.reduce((a, r) => a + (r[k] || 0), 0) / rs.length;
    const worst = k => Math.min(...rs.map(r => r[k] == null ? Infinity : r[k]));
    return {
      cand: c, n: rs.length,
      playerFrameY: +m('playerFrameY').toFixed(3), airPct: +m('airPct').toFixed(1),
      skyPct: +m('skyPct').toFixed(1), ridgePct: +m('ridgePct').toFixed(1),
      groundPct: +m('groundPct').toFixed(1), vegPct: +m('vegPct').toFixed(1),
      coverMed: +m('coverMed').toFixed(1), coverMin: +m('coverMin').toFixed(1),
      areaM2: Math.round(m('areaM2')), ahead: +m('ahead').toFixed(1),
      clrMin: worst('camAboveGround') === Infinity ? null : +worst('camAboveGround').toFixed(1),
      vegMax: Math.max(...rs.map(r => r.vegPct)),
      inFrame: rs.every(r => r.playerInFrame),
    };
  });
  const s = arg('sort', '');
  if (s) agg.sort((a, b) => (b[s] || 0) - (a[s] || 0));
  console.log('cand        PLYR   AIR  sky ridge  grnd   veg  vegMax  covMed covMin  areaM2 ahead  clrMin  ok');
  for (const a of agg) console.log(
    a.cand.padEnd(11),
    String(a.playerFrameY).padStart(5), String(a.airPct).padStart(5),
    String(a.skyPct).padStart(4), String(a.ridgePct).padStart(5),
    String(a.groundPct).padStart(5), String(a.vegPct).padStart(5),
    String(a.vegMax).padStart(6),
    String(a.coverMed).padStart(7), String(a.coverMin).padStart(6),
    String(a.areaM2).padStart(7), String(a.ahead).padStart(5),
    String(a.clrMin).padStart(7), a.inFrame ? ' y' : ' NO');
}
function hdr() { console.log('cand        PLYR horiz   AIR  sky ridge  grnd   veg covMed  areaM2 ahead  clr'); }
function line(r) {
  console.log(key(r).padEnd(11),
    String(r.playerFrameY).padStart(5), String(r.horizonMissDeg).padStart(5),
    String(r.airPct).padStart(5), String(r.skyPct).padStart(4), String(r.ridgePct).padStart(5),
    String(r.groundPct).padStart(5), String(r.vegPct).padStart(5),
    String(r.coverMed).padStart(6), String(r.areaM2).padStart(7),
    String(r.ahead).padStart(5), String(r.camAboveGround).padStart(6));
}
