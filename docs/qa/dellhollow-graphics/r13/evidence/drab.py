"""drab.py — whole-town draft A/B: what fraction of each frame actually moved.

  python3 drab.py <dirA> <dirB>

Two numbers per camera: % of pixels whose max RGB channel difference exceeds
4/255 and 12/255.  A REBAKE LIST IS DERIVED FROM RENDERED FRAMES, and the floor
is re-measured per camera by rendering one arm twice — never inherited.
"""
import sys, os
import numpy as np
from PIL import Image

A, B = sys.argv[1], sys.argv[2]
ca, cb = os.path.join(A, "cameras"), os.path.join(B, "cameras")
rows = []
for sid in sorted(set(os.listdir(ca)) & set(os.listdir(cb))):
    pa = os.path.join(ca, sid, "bg.png"); pb = os.path.join(cb, sid, "bg.png")
    if not (os.path.exists(pa) and os.path.exists(pb)):
        continue
    a = np.asarray(Image.open(pa).convert("RGB"), np.int16)
    b = np.asarray(Image.open(pb).convert("RGB"), np.int16)
    if a.shape != b.shape:
        print("%-16s SHAPE MISMATCH %s vs %s" % (sid, a.shape, b.shape)); continue
    d = np.abs(a - b).max(2)
    rows.append((float((d > 4).mean() * 100), float((d > 12).mean() * 100), sid,
                 float(d.mean())))
rows.sort(reverse=True)
print("%-16s %9s %9s %8s" % ("camera", ">4/255 %", ">12/255 %", "mean|d|"))
for p4, p12, sid, m in rows:
    print("%-16s %9.3f %9.3f %8.3f" % (sid, p4, p12, m))
print("\nONE LINE: " + " · ".join("%s %.3f/%.3f" % (s, p4, p12) for p4, p12, s, _ in rows))
