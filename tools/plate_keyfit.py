#!/usr/bin/env python3
"""plate_keyfit.py — WHERE IS THE LIGHT IN THIS BAKED PLATE, measured from the
plate itself.

    python3 tools/plate_keyfit.py --bundle del-cine --cam weave --claim 53.285,112.38
    python3 tools/plate_keyfit.py --bundle emb-cine --cam homerow --claim 50,90

WHY THIS EXISTS.  The runtime character rig takes each town's key direction from
DATA — Emberbrook's from public/townmap/emberbrook.cameras.json defaults.lightRig,
Dellhollow's recovered out of its master blend and recorded in
public/game/lightrigs.json.  Both are claims about a NUMBER.  The thing that
actually has to be true is a claim about a PICTURE: that a character lit from
that direction has her lit side on the same side as the plate's own lit sides.
This is the instrument that closes that gap, and it needs no Blender and no
browser — every input already ships in the bundle.

HOW.  A cinematic bundle ships depth.png beside bg.png, baked from the SAME
render, so the geometry of the frame is known per pixel:

    d      = near + (far-near) * rgb24 / 16777215            (cine_bake's encoding,
                                                              read back exactly as
                                                              play3d's depth shader
                                                              decodes it)
    P_view = (ndc.x*tan(fov/2)*aspect, ndc.y*tan(fov/2), -1) * d
    n      = normalize(cross(dP/dx, dP/dy))                   -> rotated to world

Then for a candidate light direction L the predictor is plain Lambert,
max(0, n.L).  ALBEDO IS THE NOISE, and it is beaten by binning: normals are
bucketed onto a coarse sphere and each bucket contributes the MEDIAN luminance of
its pixels, so a bucket full of red roof and grey stone reports the middle of a
crowd rather than a colour.  The score is the weighted correlation between
predictor and median across buckets.

WHAT IT IS AND IS NOT.  It is a SCREEN, calibrated by being run against a plate
whose answer is already known (--claim prints the claim's own rank among 648
candidates).  It is not an oracle: a frame carried by local lamps rather than by
the sky has no global key to find, and the tell is a low peak correlation, which
is printed rather than hidden.  Read the correlation before reading the angle.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sun_dir(rx_deg, rz_deg):
    """Blender sun (rotation_euler rx, 0, rz) -> unit vector TO the light in the
    runtime's Y-up frame. The same transform play3d.html's sunDirFromBlender uses;
    verified there against the overworld lane's hand-checked (56,0,212)."""
    rx, rz = math.radians(rx_deg), math.radians(rz_deg)
    return np.array([math.sin(rx) * math.sin(rz), math.cos(rx), math.sin(rx) * math.cos(rz)])


def m2r(p):
    return np.array([p[0], p[2], -p[1]], dtype=float)


def load(bundle, cam_id):
    base = os.path.join(ROOT, "public/assets/scenes", bundle)
    cine = json.load(open(os.path.join(base, "cine.json")))
    cam = next((c for c in cine["cameras"] if c["id"] == cam_id), None)
    if cam is None:
        sys.exit("no camera %r in %s (%s)" % (cam_id, bundle,
                 ",".join(c["id"] for c in cine["cameras"])))
    bg = Image.open(os.path.join(base, cam["art"]["bg"])).convert("RGB")
    dp = Image.open(os.path.join(base, cam["art"]["depth"])).convert("RGB")
    return cine, cam, bg, dp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--cam", required=True)
    ap.add_argument("--claim", default=None, help="rx,rz in Blender degrees — the rig's own claim")
    ap.add_argument("--step", type=int, default=10, help="degrees between candidates")
    ap.add_argument("--scale", type=int, default=4, help="downsample factor")
    a = ap.parse_args()

    cine, cam, bg, dp = load(a.bundle, a.cam)
    W, H = dp.size
    sw, sh = W // a.scale, H // a.scale
    bg = bg.resize((sw, sh), Image.BOX)
    dp = dp.resize((sw, sh), Image.NEAREST)          # NEAREST: depth must not be blended
    D = np.asarray(dp, dtype=np.float64)
    near, far = cam["depth"]["near"], cam["depth"]["far"]
    code = D[..., 0] * 65536.0 + D[..., 1] * 256.0 + D[..., 2]
    d = near + (far - near) * code / 16777215.0
    sky = code >= 16777215.0 - 0.5                    # the far plane: nothing there

    fov = float(cam["fov"])
    aspect = W / float(H)
    t = math.tan(math.radians(fov) / 2.0)
    ys, xs = np.mgrid[0:sh, 0:sw]
    ndx = 2.0 * (xs + 0.5) / sw - 1.0
    ndy = 1.0 - 2.0 * (ys + 0.5) / sh
    P = np.stack([ndx * t * aspect * d, ndy * t * d, -d], axis=-1)

    # normals from the reconstructed surface; central differences, interior only
    du = P[1:-1, 2:] - P[1:-1, :-2]
    dv = P[2:, 1:-1] - P[:-2, 1:-1]
    n = np.cross(du, dv)
    ln = np.linalg.norm(n, axis=-1)
    n = n / np.maximum(ln, 1e-9)[..., None]
    if n[..., 2].mean() < 0:                          # face the camera
        n = -n

    # camera basis, runtime frame
    Pc, Ac = m2r(cam["pos"]), m2r(cam["aim"])
    z = Pc - Ac; z /= np.linalg.norm(z)
    x = np.cross(np.array([0.0, 1.0, 0.0]), z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    Nw = n[..., 0:1] * x + n[..., 1:2] * y + n[..., 2:3] * z

    # luminance, linearised out of the display-referred plate
    C = np.asarray(bg, dtype=np.float64)[1:-1, 1:-1] / 255.0
    lin = np.where(C <= 0.04045, C / 12.92, ((C + 0.055) / 1.055) ** 2.4)
    L = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]

    ok = (~sky[1:-1, 1:-1]) & (ln > 1e-7) & np.isfinite(L)
    # discard the steepest reconstruction artefacts: a depth edge fakes a normal
    ok &= (np.abs(Nw[..., 1]) < 0.999)
    Nf, Lf = Nw[ok], L[ok]
    if Nf.shape[0] < 2000:
        sys.exit("only %d usable pixels — nothing to fit" % Nf.shape[0])

    # bucket the normals; the MEDIAN of each bucket is what beats albedo
    B = 12
    key = (np.clip(((Nf + 1.0) * 0.5 * B).astype(int), 0, B - 1))
    kid = key[:, 0] * B * B + key[:, 1] * B + key[:, 2]
    order = np.argsort(kid)
    kid, Ns, Ls = kid[order], Nf[order], Lf[order]
    bounds = np.flatnonzero(np.diff(kid)) + 1
    groups = np.split(np.arange(kid.shape[0]), bounds)
    bn, bl, bw = [], [], []
    for g in groups:
        if g.size < 40:                               # a bucket of ten pixels is one prop
            continue
        v = Ns[g].mean(axis=0)
        nv = np.linalg.norm(v)
        if nv < 1e-6:
            continue
        bn.append(v / nv); bl.append(np.median(Ls[g])); bw.append(g.size)
    bn, bl, bw = np.array(bn), np.array(bl), np.array(bw, dtype=float)
    if bn.shape[0] < 12:
        sys.exit("only %d normal buckets — the frame is too flat to fit" % bn.shape[0])
    bw /= bw.sum()

    def score(Lv):
        p = np.maximum(0.0, bn @ Lv)
        mp, ml = (bw * p).sum(), (bw * bl).sum()
        cp, cl = p - mp, bl - ml
        den = math.sqrt((bw * cp * cp).sum() * (bw * cl * cl).sum())
        return 0.0 if den < 1e-12 else float((bw * cp * cl).sum() / den)

    cands = []
    for rx in range(5, 90, a.step):
        for rz in range(0, 360, a.step):
            cands.append((rx, rz, score(sun_dir(rx, rz))))
    cands.sort(key=lambda c: -c[2])
    best = cands[0]

    print("%s / %s   %d px, %d normal buckets" % (a.bundle, a.cam, Nf.shape[0], bn.shape[0]))
    print("  BEST      rx %3d  rz %3d   elev %4.1f   r = %+.3f"
          % (best[0], best[1], 90 - best[0], best[2]))
    for c in cands[1:4]:
        print("  runner-up rx %3d  rz %3d   elev %4.1f   r = %+.3f" % (c[0], c[1], 90 - c[0], c[2]))
    if a.claim:
        rx, rz = [float(v) for v in a.claim.split(",")]
        s = score(sun_dir(rx, rz))
        rank = 1 + sum(1 for c in cands if c[2] > s)
        ang = math.degrees(math.acos(max(-1.0, min(1.0,
              float(sun_dir(rx, rz) @ sun_dir(best[0], best[1]))))))
        print("  CLAIM     rx %5.1f  rz %5.1f  elev %4.1f   r = %+.3f   rank %d/%d   %.0f deg off the peak"
              % (rx, rz, 90 - rx, s, rank, len(cands), ang))


if __name__ == "__main__":
    main()
