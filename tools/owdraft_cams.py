#!/usr/bin/env python3
"""owdraft_cams.py — sight-line and crossing probes for the draft.

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


def crossings(F):
    """Every place the road changes BANK. A road that hops the river is a design
    decision and must be a bridge; an earlier pass switched banks 6u short of the
    Old Gate purely as fallout from re-siting the gate's doorway, and nothing
    caught it until the user did. This does."""
    P = np.array([(p[0], p[1]) for p in DL.D["river"]["points"]], float)

    def side(x, y):
        i = int(np.argmin(np.hypot(P[:, 0] - x, P[:, 1] - y)))
        a = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        v = np.array([x, y]) - P[i]
        return -(a[0] * v[1] - a[1] * v[0])          # + = right of the flow

    bridges = [l for l in DL.D["landmarks"] if "bridge" in l["id"]]
    out, prev = [], None
    for p in F.roadpts:
        sd = side(p[0], p[1])
        if prev is not None and (sd > 0) != (prev > 0):
            out.append(p)
        prev = sd
    print("\nROAD/RIVER BANK CHANGES: %d   (declared bridges: %d)"
          % (len(out), len(bridges)))
    for p in out:
        near = min((float(np.hypot(p[0] - b["pos"][0], p[1] - b["pos"][1])), b["id"])
                   for b in bridges) if bridges else (9e9, "-")
        w = float(F.riverwidth(p[0], p[1]))
        # the deck is span = w + 4.6, so half of it is w/2 + 2.3; allow one road
        # sample (~1u) of slack, because the bank change is detected at whichever
        # sample happens to straddle the centreline, not at the exact crossing.
        half = w * 0.5 + 2.3 + 1.0
        ok = near[0] <= half
        print("   (%6.1f,%6.1f)  nearest bridge '%s' %.2fu (deck reach %.2fu) -> %s"
              % (p[0], p[1], near[1], near[0], half,
                 "ON THE DECK" if ok else "*** UNBRIDGED ***"))
    if len(out) != len(bridges):
        print("   *** MISMATCH: %d bank changes vs %d bridges ***"
              % (len(out), len(bridges)))


def main():
    F = DL.DraftField()
    for nm, c in DL.D["cameras"].items():
        if not nm.startswith("_"):
            report(F, nm, c)
    crossings(F)


if __name__ == "__main__":
    main()
