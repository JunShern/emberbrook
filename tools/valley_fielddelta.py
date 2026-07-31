#!/usr/bin/env python3
"""valley_fielddelta.py — does a bench-side change reach a given frame?

  python3 tools/valley_fielddelta.py

The committed valley_vistaring.png came from the FIRST post-flip build, before
benchSideAboveCulvert existed.  Every other frame in the set was re-rendered after.
Rather than assert "that shot looks east, the handover is at the gate, so it cannot
matter", MEASURE it: build the field twice — once as shipped, once with the upstream
bench forced to the downstream side (the pre-handover state) — and ask how big the
difference is inside the frame's own footprint.
"""
import sys
import numpy as np
sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
import valley_map as VM

F_now = VM.ValleyField()                       # as shipped (handover in place)
VM.BENCH_LEFT_ABOVE = VM.BENCH_LEFT            # the pre-handover state
F_old = VM.ValleyField()
d = np.abs(F_now.H - F_old.H)

WX, WY = F_now.X + VM.CX, F_now.Y + VM.CY
CAM = (222.0, 100.0)                           # the vistaring eye, from valley_build
# the frame looks EAST (aim x=560): its footprint is the eastward half-plane from
# the eye.  Take everything east of it, plus a generous 40u of lateral spill.
east = (WX >= CAM[0] - 5.0) & (np.abs(WY - CAM[1]) <= 90.0)
print("field delta from the handover, WHOLE TILE:  max %.3fu, mean %.4fu, cells>0.05u %d"
      % (d.max(), d.mean(), int((d > 0.05).sum())))
print("...inside the vistaring footprint (east of the eye): max %.3fu, cells>0.05u %d"
      % (d[east].max(), int((d[east] > 0.05).sum())))
i, j = np.unravel_index(np.argmax(d), d.shape)
print("worst cell anywhere: world [%.1f, %.1f], %.2fu — %.1fu from the eye"
      % (WX[i, j], WY[i, j], d[i, j],
         float(np.hypot(WX[i, j] - CAM[0], WY[i, j] - CAM[1]))))

# ---- WHY does a change at the gate reach the far corner? --------------------
print()
print("floor profile a_prof (the calibrated bank-above-water controls):")
print("  shipped     ", np.round(F_now.floor_a, 3).tolist())
print("  pre-handover", np.round(F_old.floor_a, 3).tolist())
print("  max |delta| %.3fu" % np.abs(F_now.floor_a - F_old.floor_a).max())
for nm, p in (("emberbrook", (82.0, 48.0)), ("moorage", (200.96, 152.87)),
              ("vistaring eye", (222.0, 100.0)), ("long-reach corner", (226.0, 186.0))):
    bx, by = VM.w2b(p[0], p[1])
    a = float(F_now.sample(np.array([bx]), np.array([by]))[0])
    b = float(F_old.sample(np.array([bx]), np.array([by]))[0])
    print("  %-18s shipped %7.2f   pre-handover %7.2f   delta %+6.2f" % (nm, a, b, a - b))
