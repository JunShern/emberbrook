"""plate_ab.py — THE WHOLE-TOWN DRAFT A/B, AS A RULER.  No Blender, no browser.

    python3 tools/plate_ab.py --a <dirA> --b <dirB> [--floor 0.01] [--json out.json]
    python3 tools/plate_ab.py --a <dirA> --b <dirA2>          # the noise-floor control

Each <dir> is a `cine_bake --draft` output (`<dir>/cameras/<shot>/bg.png`), or any
directory of `<shot>/bg.png`.  For every shot present in both it reports the fraction of
the frame whose luminance moved by more than 4/255 and by more than 12/255, plus the
signed median shift, and RANKS them.

WHY THIS IS THE RULER AND A FRUSTUM IS NOT (CLAUDE.md, 2026-08-08).  `cine_bake --draft
--res 1008x576 --samples 28` is ~15 s a frame on a gray master, so a whole town costs
minutes — and **two independent draft renders of the SAME master differ by 0.01% of frame
above 4/255 and 0.00% above 12/255**, because denoised Cycles is effectively
deterministic.  That is a real noise floor, so a rebake list can be derived from RENDERED
FRAMES instead of from a frustum, and it is strictly better: on Dellhollow the frustum
said a wall was 24% of `lockhead` and the picture said the change there was zero.

TWO THINGS IT WILL NOT DO.
  * It will not tell you the two arms were rendered at the same GRADE.  They must be —
    the A/B is a ruler for GEOMETRY, so hold exposure/sky/moon fixed (the default draft
    grade is fine for both arms; the SHIPPED grade is `emb_bake_shipped`'s job) and this
    file only reports what it is given.
  * `--floor` is a REFUSAL, not a filter: a shot under it is printed WITH ITS NUMBER and
    marked REFUSED, because "we did not rebake it" is a claim that needs its measurement
    attached.
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--a", required=True)
ap.add_argument("--b", required=True)
ap.add_argument("--floor", type=float, default=0.01)     # % of frame above 4/255
ap.add_argument("--json", default=None)
args = ap.parse_args()


def shots(d):
    c = os.path.join(d, "cameras")
    base = c if os.path.isdir(c) else d
    return {s: os.path.join(base, s, "bg.png") for s in sorted(os.listdir(base))
            if os.path.isfile(os.path.join(base, s, "bg.png"))}


A, B = shots(args.a), shots(args.b)
both = sorted(set(A) & set(B))
only = sorted(set(A) ^ set(B))
assert both, ("no shot appears in both directories — an instrument that finds nothing "
              "must prove it could have found something (A: %d, B: %d)" % (len(A), len(B)))
if only:
    print("NOT IN BOTH ARMS, so not measured: %s" % ", ".join(only))

rows = []
for s in both:
    a = np.asarray(Image.open(A[s]).convert("RGB"), dtype=np.float32)
    b = np.asarray(Image.open(B[s]).convert("RGB"), dtype=np.float32)
    if a.shape != b.shape:
        print("  %-12s SHAPE MISMATCH %s vs %s — not measured" % (s, a.shape, b.shape))
        continue
    la = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    lb = 0.2126 * b[..., 0] + 0.7152 * b[..., 1] + 0.0722 * b[..., 2]
    d = lb - la
    ad = np.abs(d)
    n = float(ad.size)
    rows.append(dict(shot=s,
                     p4=100.0 * float((ad > 4).sum()) / n,
                     p12=100.0 * float((ad > 12).sum()) / n,
                     dmed=float(np.median(d[ad > 4])) if (ad > 4).any() else 0.0,
                     la=float(np.median(la)), lb=float(np.median(lb))))
    del a, b, la, lb, d, ad

rows.sort(key=lambda r: -r["p4"])
print("\n%-12s %10s %10s %10s %10s %10s   %s"
      % ("shot", "chg>4/255", "chg>12/255", "medshift", "L50 A", "L50 B", "verdict"))
keep = []
for r in rows:
    v = "REBAKE" if r["p4"] >= args.floor else "REFUSED (under the %.2f%% floor)" % args.floor
    if r["p4"] >= args.floor:
        keep.append(r["shot"])
    print("%-12s %9.3f%% %9.3f%% %+10.2f %10.1f %10.1f   %s"
          % (r["shot"], r["p4"], r["p12"], r["dmed"], r["la"], r["lb"], v))
print("\nREBAKE LIST (%d of %d): %s" % (len(keep), len(rows), ",".join(keep) or "-"))
if args.json:
    json.dump(dict(a=args.a, b=args.b, floor=args.floor, rebake=keep, rows=rows),
              open(args.json, "w"), indent=1)
    print("wrote " + args.json)
