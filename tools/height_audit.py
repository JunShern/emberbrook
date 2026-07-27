#!/usr/bin/env python3
"""Run the height gate over every existing painted asset and print the audit
table (measured vs target, verdict). Reads the four metrics JSONs + the size
table in specs.json; standalone, mutates nothing. Usage: python3 tools/height_audit.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from height_gate import measure_height

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO = os.path.join(ROOT, 'public/assets/iso')

def load(p):
    with open(p) as f: return json.load(f)

SPECS = load(os.path.join(ISO, 'specs.json'))
TARGET = {a['id']: a for a in SPECS['assets']}

def target_cells(aid):
    a = TARGET.get(aid)
    return a['targetHeightCells'] if a else None

rows = []
def audit(catalog, aid, px_above, cell_px, S=1.0, fit=1.0, mb=None, decl=None):
    t = target_cells(aid)
    if t is None:
        rows.append((catalog, aid, None, None, None, 'NO-SPEC', ''))
        return
    r = measure_height(px_above, cell_px, t, S=S, fit_scale=fit,
                       measured_base=mb, declared=decl)
    note = ''
    if r.get('heightFitScale'): note = 'hFit x%.3f' % r['heightFitScale']
    rows.append((catalog, aid, r['measuredHeightCells'], t, r['ratio'],
                 r['verdict'], note))

# ---- blocks9 + festival native props ----
for cat, fn in [('blocks9', 'blocks9/blocks9-metrics.json'),
                ('festival', 'festival/festival-metrics.json')]:
    m = load(os.path.join(ISO, fn))
    for name, rec in m.items():
        if not rec.get('anchorSprite'): continue
        bc = rec.get('baseContainment') or {}
        audit(cat, name, rec['anchorSprite'][1], rec['cellPx'],
              fit=rec.get('renderFitScale', 1.0),
              mb=bc.get('measuredBase'), decl=rec['declared'])

# ---- buildings (render at cellScale.renderScale; measure total ridge) ----
bm = load(os.path.join(ISO, 'bldg/bldg-metrics.json'))
for name in ('bakery', 'cottage', 'guildhall'):
    rec = bm.get(name)
    if not rec or not rec.get('cellScale'): continue
    cs = rec['cellScale']
    # measuredHeightCells = pxAbove * renderScale / 32 ; renderScale already S*TW/cellPx
    px = rec['anchorSprite'][1]
    r = measure_height(px, rec['cellPx'], target_cells(name),
                       S=cs['S'], fit_scale=1.0)
    rows.append(('bldg', name, r['measuredHeightCells'], r['targetHeightCells'],
                 r['ratio'], r['verdict'], 'renderScale=%.3f' % cs['renderScale']))

# ---- interior shell walls + props ----
im = load(os.path.join(ISO, 'interior/interior-metrics.json'))
room = im['room']
S_int = 1.5
nw = room['nearWall']
r = measure_height(nw['heightPx'], room['cellPx'], target_cells('int-room'),
                   S=S_int, fit_scale=1.0)
rows.append(('interior', 'int-walls(S1.5)', r['measuredHeightCells'],
             r['targetHeightCells'], r['ratio'], r['verdict'], 'wall heightPx'))
# also at S=1.0 for comparison
r1 = measure_height(nw['heightPx'], room['cellPx'], target_cells('int-room'),
                    S=1.0, fit_scale=1.0)
rows.append(('interior', 'int-walls(S1.0)', r1['measuredHeightCells'],
             r1['targetHeightCells'], r1['ratio'], r1['verdict'], 'if shell S=1.0'))
for name, rec in room.get('props', {}) .items() if False else im.get('props', {}).items():
    if not rec.get('anchorSprite'): continue
    bc = rec.get('baseContainment') or {}
    audit('interior', 'i-' + name, rec['anchorSprite'][1], rec['cellPx'],
          fit=rec.get('renderFitScale', 1.0),
          mb=bc.get('measuredBase'), decl=rec['declared'])

# ---- character (engine CHAR_H, now PINNED to the size table in engine.js) ----
CHAR_H = 109          # = round(3.4 * TW/2); was 130 (4.06 cells = 2.03 m, the giant)
char_cells = CHAR_H / 32.0
rows.append(('char', 'vesper(CHAR_H=109)', round(char_cells, 2), 3.4,
             round(char_cells / 3.4, 3), 'REROLL' if abs(char_cells/3.4-1) > 0.15 else 'PASS',
             'pinned 3.4 cells=1.70m (was 130px=2.03m)'))

# ---- print ----
print('%-9s %-20s %8s %8s %7s  %-10s %s' %
      ('catalog', 'asset', 'measured', 'target', 'ratio', 'verdict', 'note'))
print('-' * 88)
for cat, aid, meas, t, ratio, verdict, note in rows:
    print('%-9s %-20s %8s %8s %7s  %-10s %s' %
          (cat, aid, meas if meas is not None else '-',
           t if t is not None else '-',
           ('%.2f' % ratio) if ratio is not None else '-', verdict, note))
