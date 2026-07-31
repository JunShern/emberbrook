#!/usr/bin/env python3
"""owdraft_cams.py — sight-line probe for the draft's three renders.

  python3 tools/owdraft_cams.py

"In frame" is not "visible" (docs/qa/DAYLOG.md).  Each camera in the draft map is
marched against the field in 0.6u steps and the FIRST blocking ground is reported,
so a shot that stares into a gorge wall says so here instead of costing a render.
Cameras flagged snapToGround are placed at ground + eye height.

*** PROPOSAL DRAFT. NOT CANON. ***
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import owdraft_lib as DL

EYE = 1.5


def march(F, P, T, step=0.6, clearance=0.35):
    d = np.array(T, float) - np.array(P, float)
    L = float(np.linalg.norm(d[:2]))
    n = max(4, int(L / step))
    t = np.linspace(0.0, 1.0, n)
    x = P[0] + d[0] * t
    y = P[1] + d[1] * t
    z = P[2] + d[2] * t
    g = F.height(np.clip(x, 0, DL.TILE_W), np.clip(y, 0, DL.TILE_H))
    hit = np.where(g > z - clearance)[0]
    hit = hit[hit > 2]
    return (None if hit.size == 0
            else (float(t[hit[0]] * L), float(x[hit[0]]), float(y[hit[0]]), float(g[hit[0]])))


def report(F, nm, c):
    P = list(map(float, c["pos"]))
    T = list(map(float, c["target"]))
    gnd = float(F.height(P[0], P[1]))
    if c.get("snapToGround"):
        P[2] = gnd + EYE + float(c.get("lift", 0.0))
    m = march(F, P, T)
    L = float(np.linalg.norm(np.array(T[:2]) - np.array(P[:2])))
    print("%-10s eye(%.1f,%.1f,%.1f) ground=%.1f%s -> target(%.0f,%.0f,%.0f) %.0fu"
          % (nm, P[0], P[1], P[2], gnd,
             " [SNAP+%.0f]" % c.get("lift", 0.0) if c.get("snapToGround") else "",
             T[0], T[1], T[2], L))
    print("           " + ("clear to target" if m is None else
                           "BLOCKED at %.1fu (%.0f,%.0f) ground %.1f  [%.0f%%]"
                           % (m[0], m[1], m[2], m[3], 100 * m[0] / L)))
    return P


def main():
    F = DL.DraftField()
    for nm, c in DL.D["cameras"].items():
        if not nm.startswith("_"):
            report(F, nm, c)


if __name__ == "__main__":
    main()
