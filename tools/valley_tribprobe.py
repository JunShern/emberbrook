#!/usr/bin/env python3
"""valley_tribprobe.py — FIND the tributaries, do not type them.

  python3 tools/valley_tribprobe.py

The user's geography note: the gorge river grows from 4.5u at the falls to 28u at
the handoff and nothing visible feeds it.  The answer is not a drawn stream where a
stream would look nice; it is to ask the terrain that is already built where the
water already runs, and to put the visible waterlines THERE.

Method: D8 steepest-descent flow accumulation on the BUILT height field (the same
ValleyField the tile is carved from), with the main channel removed from the
candidate set.  A tributary is a flow path whose accumulation clears a threshold
and whose outlet touches the channel inside the corridor.  Writes nothing.
"""
import json, math, sys
import numpy as np

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
import valley_map as VM

F = VM.ValleyField()
H = F.H_natural.copy()                      # the LAND, before the works
NX, NY = H.shape
STEP = VM.STEP

# ---- D8 accumulation ---------------------------------------------------------
order = np.dstack(np.unravel_index(np.argsort(-H, axis=None), H.shape))[0]
acc = np.ones_like(H)
NB = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
for ix, iy in order:
    best, bs = None, 0.0
    for dx, dy in NB:
        jx, jy = ix + dx, iy + dy
        if 0 <= jx < NX and 0 <= jy < NY:
            s = (H[ix, iy] - H[jx, jy]) / (math.hypot(dx, dy) * STEP)
            if s > bs:
                best, bs = (jx, jy), s
    if best is not None:
        acc[best] += acc[ix, iy]

WX = F.X + VM.CX
WY = F.Y + VM.CY
dr = F.dr
hw = F.hw
chan = dr <= hw + 1.5                       # the main stem
arc = np.interp(F.tr, VM.RIV_T, VM.RIV_S)

print("accumulation: max %.0f, p99.9 %.0f, p99 %.0f"
      % (acc.max(), np.percentile(acc, 99.9), np.percentile(acc, 99)))

# ---- outlets: high-accumulation cells that touch the channel ------------------
GATE_ARC = VM.river_arc_at(*VM.PORTALS["old-gate"]["at"][:2])
band = (dr > hw + 1.5) & (dr < hw + 6.0) & (arc > GATE_ARC + 4) & (arc < VM.RIV_S[-1] - 12)
cand = band & (acc > np.percentile(acc[band], 97.5))
idx = np.argwhere(cand)
print("%d candidate outlet cells" % len(idx))

# cluster them by arc so one ravine is one candidate
rows = sorted(((float(arc[i, j]), float(acc[i, j]), float(WX[i, j]), float(WY[i, j]),
                int(i), int(j)) for i, j in idx), key=lambda r: -r[1])
picked = []
for r in rows:
    if all(abs(r[0] - q[0]) > 18.0 for q in picked):
        picked.append(r)
    if len(picked) >= 12:
        break
picked.sort(key=lambda r: r[0])
side = np.where(F.sideL > 0.5, "LEFT(far)", "RIGHT(bench)")
print("\n%-8s %-10s %-22s %-10s %s" % ("arc", "acc", "outlet world", "bank", "trace up"))
traces = {}
for a_, ac_, x_, y_, i, j in picked:
    # walk UPHILL along the strongest contributing neighbour — the ravine itself
    path = [(x_, y_)]
    ci, cj = i, j
    for _ in range(140):
        best, ba = None, acc[ci, cj]
        for dx, dy in NB:
            ki, kj = ci + dx, cj + dy
            if 0 <= ki < NX and 0 <= kj < NY and H[ki, kj] > H[ci, cj] and acc[ki, kj] > ba * 0.35:
                if acc[ki, kj] > (acc[best] if best else 0):
                    best, ba = (ki, kj), acc[ki, kj]
        if best is None:
            break
        ci, cj = best
        path.append((float(WX[ci, cj]), float(WY[ci, cj])))
    ln = sum(math.dist(path[k], path[k + 1]) for k in range(len(path) - 1))
    drop = float(H[i, j] - H[ci, cj])
    print("%-8.1f %-10.0f [%6.2f,%6.2f]  %-10s  %3d pts, %5.1fu long, rises %5.1fu, head [%6.1f,%6.1f]"
          % (a_, ac_, x_, y_, side[i, j], len(path), ln, -drop, path[-1][0], path[-1][1]))
    traces[round(a_, 1)] = path

json.dump({str(k): v for k, v in traces.items()},
          open("/Users/junshernchan/projects/multiplayer-rpg/scratchpad/trib_traces.json", "w"))

# ---- and where does the Hollowmere outlet have to come from? -----------------
hm = [e for e in VM.REG_META.get("exits", []) if e["id"] == "pass-hollowmere"][0]["at"]
d_hm = np.hypot(WX - hm[0], WY - hm[1])
m = band & (d_hm < 80.0) & (F.sideL > 0.5)
if m.any():
    k = np.argmax(np.where(m, acc, 0))
    i, j = np.unravel_index(k, acc.shape)
    print("\nHollowmere side: strongest far-bank outlet within 80u of the pass at "
          "[%.2f, %.2f], arc %.1f, acc %.0f" % (WX[i, j], WY[i, j], arc[i, j], acc[i, j]))
