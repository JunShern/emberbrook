#!/usr/bin/env python3
"""CELLSCALE derivation — per-building cellScale injected into bldg-metrics.json.

The dollhouse finding: at one painted building-cell = one 0.5 m engine cell,
a 3x3 building is 1.5 m wide and the bakery door is knee-height on the 130 px
character. The fix proved this round: a per-building cellScale S — one painted
cell maps to an SxS block of engine cells (S=2 for all three buildings).

THE MAPPING (S = engine cells per painted cell; TW = 64 px engine cell):

  engineFoot      = declared x S                  painted [fw,fh] -> [fw*S, fh*S]
  renderScale     = S * TW / cellPx               cellPx is the MEASURED painted
                                                  cell size for this sprite, so
                                                  one painted cell spans exactly
                                                  S engine cells on screen
  engine anchor   = anchorSprite (SAME pixel)     the mark centre; placed at the
                                                  centre of engineFoot, exactly
                                                  like the 1x case
  engineDoorCells = {(di*S+u, dj*S+v) : 0<=u,v<S} painted door cell (di,dj)
                                                  becomes an SxS engine block
  engineDoorstep  = door on front edge j (dj==fh-1): {(di*S+t, fh*S) : 0<=t<S}
                    door on front edge i (di==fw-1): {(fw*S, dj*S+t) : 0<=t<S}
                    the row of S walkable trigger cells just OUTSIDE the door's
                    engine cells (2-cell-wide doorstep for a 2x-wide door) —
                    the same one-step-out rule slice_bldg.py uses, applied on
                    the engine grid
  engineSolid     = {(a*S+u, b*S+v) : (a,b) in solid, 0<=u,v<S}
  sortKey         = i + j + (engineFoot[0]+engineFoot[1])/2   (engine formula
                    unchanged — just fed the engine footprint)
  texelHeadroom   = cellPx / (S*TW)   source px per screen px at native zoom;
                    < 1 would mean the sprite is UPSCALED on screen

RESOLUTION FLOOR (standing pipeline rule): the painted cell must carry at
least one source pixel per engine screen pixel — cellPx / S >= 64. Below the
floor the sprite upscales by 64 / (cellPx/S) at native zoom. Therefore at
GENERATION time target measured painted cellPx >= S*64 (>= 128 for S=2). At
1024x1024 output the fitted mark spans ~595 px across (fw * cellPx), i.e.
cellPx ~= 595/fw for square footprints: 3x3 -> ~198 px, 4x4 -> ~149 px, so
1024 output supports S=2 up to 4x4; a 5x5 (or anything measuring under
128 px/cell) must be generated at 1536+ before it can take cellScale 2.

NOTE: tools/slice_bldg.py rewrites bldg-metrics.json wholesale; re-run this
script after any re-slice to restore the cellScale blocks.

Usage: python3 tools/bldg_cellscale.py [METRICS_DIR]
"""
import json, os, sys

TW = 64
S = 2
BUILDINGS = ['bakery', 'cottage', 'guildhall']

FORMULA = [
    "cellScale mapping (S engine cells per painted cell; TW=64px engine cell):",
    "engineFoot = declared*S; renderScale = S*TW/cellPx (one painted cell -> S engine cells on screen);",
    "engine anchor = anchorSprite, the SAME sprite pixel, placed at the centre of engineFoot;",
    "engineDoorCells = SxS block {(di*S+u, dj*S+v)}; engineDoorstep = the row of S walkable cells",
    "one step outside the door's front edge on the engine grid: j-edge -> {(di*S+t, fh*S)},",
    "i-edge -> {(fw*S, dj*S+t)}; engineSolid = each painted solid cell expanded to SxS;",
    "sortKey = i + j + (engineFoot w+h)/2 (engine formula unchanged);",
    "texelHeadroom = cellPx/(S*TW), <1 means upscaling. See tools/bldg_cellscale.py.",
    "RESOLUTION FLOOR rule: painted cellPx/S must be >= 64 (one source px per engine screen px);",
    "target measured cellPx >= S*64 (128 for S=2) at generation time. 1024px output yields",
    "~595px of mark span (cellPx ~= 595/fw), OK for S=2 up to 4x4; generate 5x5+ at 1536+.",
]


def derive(m, s=S):
    fw, fh = m['declared']
    cs = {
        'S': s,
        'engineFoot': [fw * s, fh * s],
        'renderScale': round(s * TW / m['cellPx'], 4),
        'paintedCellScreenPx': s * TW,
        'texelHeadroom': round(m['cellPx'] / (s * TW), 3),
        # RESOLUTION FLOOR: source px per engine cell must be >= TW (64)
        'resolutionFloor': {
            'cellPxPerEngineCell': round(m['cellPx'] / s, 2),
            'floorPx': TW,
            'pass': m['cellPx'] / s >= TW,
            'upscaleFactor': round(max(1.0, TW / (m['cellPx'] / s)), 3),
        },
        'engineAnchorSprite': m['anchorSprite'],
    }
    d = m.get('door') or {}
    if d.get('cell'):
        di, dj = d['cell']
        cs['engineDoorCells'] = [[di * s + u, dj * s + v]
                                 for v in range(s) for u in range(s)]
        if d.get('doorstep'):
            si, sj = d['doorstep']
            if sj == fh:                       # door in the j front edge
                cs['engineDoorstep'] = [[di * s + t, fh * s] for t in range(s)]
            else:                              # door in the i front edge
                cs['engineDoorstep'] = [[fw * s, dj * s + t] for t in range(s)]
    if m.get('solid'):
        cs['engineSolid'] = [[a * s + u, b * s + v] for a, b in m['solid']
                             for v in range(s) for u in range(s)]
    return cs


def main(outdir):
    path = os.path.join(outdir, 'bldg-metrics.json')
    with open(path) as f:
        M = json.load(f)
    M['_cellScaleFormula'] = FORMULA
    for name in BUILDINGS:
        m = M[name]
        m['cellScale'] = derive(m)
        cs = m['cellScale']
        rf = cs['resolutionFloor']
        print('%-10s painted %dx%d @ %.1fpx -> engine %dx%d, renderScale %.4f, '
              'headroom %.3f, floor %.2fpx/cell vs 64 %s, doorCells %s, doorstep %s' % (
                  name, m['declared'][0], m['declared'][1], m['cellPx'],
                  cs['engineFoot'][0], cs['engineFoot'][1], cs['renderScale'],
                  cs['texelHeadroom'], rf['cellPxPerEngineCell'],
                  'PASS' if rf['pass'] else 'UPSCALE x%.3f' % rf['upscaleFactor'],
                  cs.get('engineDoorCells'), cs.get('engineDoorstep')))
    with open(path, 'w') as f:
        json.dump(M, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'public/assets/iso/bldg')
