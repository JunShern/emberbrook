"""foliage_atlas.py — the LEAF-CLUSTER card atlas, drawn leaf by leaf.

  python3 tools/foliage_atlas.py [--force] [--sheet]

Pure numpy + PIL: no Blender, so the atlas can be judged at 200% in a second
without a build.  It is a ONE-OFF asset (finding 148) — the per-tile build only
loads the files.

WHY THIS EXISTS.  Three earlier valley forests failed on ATLAS QUALITY, not on
geometry: every one of them stamped ROTATED ELLIPSES with a radial shade ramp
(`overworld3_lib._stamp_wrap_cell`), up to 2400 per cell, and the user called the
result flakes every time.  An ellipse with a radial ramp has

  * no leaf silhouette      — a leaf is pointed, asymmetric and serrated;
  * no shared light         — each blob is lit from its own centre outward, so
                              the cluster has no top and no underside;
  * no occlusion            — later stamps overwrite earlier ones with no depth,
                              so there are no layers and no interior;
  * no normal that means anything — the normal map came from a *height* field
                              built out of the same ellipses.

This module instead RENDERS a small 3-D scene per atlas cell in numpy: a dome of
leaf sprays, each spray a rachis of individually-shaped blades with a midrib
fold, every blade rasterised through a Z-BUFFER with a real per-pixel normal.
One key light, one sky term, a depth-driven AO term and a translucency term
shade all of them together, so a clump has a lit top, a dark interior and a
backlit rim — the three things that make the reference's bushes read as bushes.

Outputs (per findings 131/143 the alpha one MUST be PNG):

  leafclump_atlas.png     RGBA — albedo with the light baked in, + the cutout
  leafclump_nor.jpg       tangent-space normal (OpenGL, +Y up) of the same cells
  leafmass_tile.jpg  +
  leafmass_tile_nor.jpg   the TILEABLE version of the same blades, for the dark
                          dense core the cards are shelled over

Atlas layout is a GRID x GRID grid, cell 0 at the TOP-LEFT, row-major:
  cells  0 .. N_BIG-1   BIG CLUMPS — the mass: near-filled, opaque dark interior
  cells  N_BIG ..       EDGE FUZZ  — open, few sprays, much sky; silhouette
                                     breakers for the rim of a forest mass
"""
import argparse
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXO = os.path.join(ROOT, "tools/textures/overworld")
QA = os.path.join(ROOT, "docs/qa/overworld")

ATLAS = os.path.join(TEXO, "leafclump_atlas.png")
ATLAS_NOR = os.path.join(TEXO, "leafclump_nor.jpg")
TILE = os.path.join(TEXO, "leafmass_tile.jpg")
TILE_NOR = os.path.join(TEXO, "leafmass_tile_nor.jpg")

# ---------------------------------------------------------------- taste knobs
GRID = 4                       # 4 x 4 = 16 cards
CELL = 256                     # shipped pixels per cell (atlas = GRID * CELL)
SS = 3                         # supersample factor while drawing
N_BIG = 8                      # cells 0..7 are big clumps, 8..15 edge fuzz
AUTUMN_RATIO = 0.075           # fraction of SPRAYS that have turned
PALE_RATIO = 0.10              # fraction that are new pale growth
AO_FLOOR = 0.40                # darkest a buried blade may go (never black)
R_BIG = 0.355                  # clump radius / cell.  Sprays throw ~0.13 past
R_FUZZ = 0.330                 # it, so anything larger CLIPS at the cell border
KEY = np.array([-0.42, 0.50, 0.76])          # key light, image space, +y up
KEY /= np.linalg.norm(KEY)
UP = np.array([0.0, 0.0, 1.0])
HALF = (KEY + UP) / np.linalg.norm(KEY + UP)

# leaf greens, deep -> sunlit.  Cool and desaturated in shadow, warm-yellow in
# the light: one hue ramped in value only is what reads as plastic.
G_DEEP = np.array([0.040, 0.076, 0.050])
G_MID = np.array([0.115, 0.215, 0.082])
G_LIT = np.array([0.300, 0.430, 0.145])
G_SUN = np.array([0.455, 0.545, 0.190])
AUT = np.array([0.520, 0.255, 0.055])
AUT2 = np.array([0.600, 0.400, 0.095])
PALE = np.array([0.395, 0.500, 0.175])
STEM = np.array([0.105, 0.086, 0.055])
TRANS_TINT = np.array([0.30, 0.34, 0.13])
SPEC_TINT = np.array([0.85, 0.90, 0.72])


def _norm(v, axis=-1):
    return v / np.maximum(np.linalg.norm(v, axis=axis, keepdims=True), 1e-9)


class Cluster:
    """Supersampled RGB + alpha + normal + Z buffers for one atlas cell.

    `y` runs UP (array row 0 is the bottom of the image); the savers flip.
    Keeping the maths in a y-up frame is what lets the normal buffer be written
    straight out as OpenGL tangent space with no sign hunting.
    """

    def __init__(self, n, wrap=False):
        self.n = n
        self.wrap = wrap
        self.col = np.zeros((n, n, 3), np.float32)
        self.alp = np.zeros((n, n), np.float32)
        self.nrm = np.zeros((n, n, 3), np.float32)
        self.nrm[..., 2] = 1.0
        self.dep = np.full((n, n), -1e9, np.float32)

    # ------------------------------------------------------------------ core
    def _box(self, cx, cy, pad):
        n = self.n
        x0, x1 = int(cx) - pad, int(cx) + pad + 1
        y0, y1 = int(cy) - pad, int(cy) + pad + 1
        if not self.wrap:
            x0, x1 = max(0, x0), min(n, x1)
            y0, y1 = max(0, y0), min(n, y1)
            if x1 <= x0 or y1 <= y0:
                return None
        return np.mgrid[y0:y1, x0:x1]

    def _put(self, iy, ix, z, c, N):
        """Z-test, then write colour AND normal together — they have to be the
        same decision or the normal map describes a surface that is not there."""
        if self.wrap:
            iy, ix = iy % self.n, ix % self.n
        keep = z > self.dep[iy, ix]
        if not keep.any():
            return
        iy, ix = iy[keep], ix[keep]
        self.dep[iy, ix] = z[keep]
        self.col[iy, ix] = c[keep]
        self.alp[iy, ix] = 1.0
        self.nrm[iy, ix] = N[keep]

    # ------------------------------------------------------------- one blade
    def leaf(self, cx, cy, length, width, ang, z, rgb, plate, cross,
             fold=0.90, droop=0.45, serr=0.05, phase=0.0, gloss=0.10,
             trans=0.26):
        """One leaf blade with a real per-pixel normal, z-tested.

        `plate` is the blade's 3-D surface normal and `cross` its width
        direction (unit, mutually perpendicular, both perpendicular to the blade
        axis).  They come from the CLUMP's dome, which is how every blade in a
        cell ends up lit by the same sun instead of from its own centre.
        """
        g = self._box(cx, cy, int(length + width) + 3)
        if g is None:
            return
        yy, xx = g
        dx, dy = xx - cx, yy - cy
        ca, sa = math.cos(ang), math.sin(ang)
        u = dx * ca + dy * sa                        # along the blade, 0 = base
        v = -dx * sa + dy * ca                       # across it
        s = u / max(length, 1e-3)
        sc = np.clip(s, 0.0, 1.0)
        # LANCEOLATE blade: widest near 0.4 of the length, drawn to a point at
        # the tip, serrated margin.  This is the line that separates a leaf from
        # the ellipse the three failed rounds stamped.
        hw = width * np.sin(np.pi * sc ** 0.80) ** 0.58 * (1.0 - 0.26 * sc)
        hw *= 1.0 + serr * np.sin(9.0 * np.pi * sc + phase)
        m = (s >= 0.0) & (s <= 1.0) & (np.abs(v) <= np.maximum(hw, 0.32))
        if not m.any():
            return
        t = np.clip(np.abs(v) / np.maximum(hw, 1e-3), 0.0, 1.0)[m]
        sm = sc[m]
        sgn = np.sign(v[m])
        axis = np.cross(cross, plate)
        N = _norm(plate[None, :] - (fold * t * sgn)[:, None] * cross[None, :]
                  + (droop * (sm - 0.35))[:, None] * axis[None, :])
        zz = z + 0.020 * (1.0 - t) + 0.010 * sm      # midrib stands proud
        ndl = N @ KEY
        lam = np.clip(ndl, 0.0, 1.0)
        sky = 0.30 + 0.26 * np.clip(N[:, 1], 0.0, 1.0)
        spec = gloss * np.clip(N @ HALF, 0.0, 1.0) ** 22.0
        # AO from the clump's own depth: z is 0 (buried) .. 1 (front/top).  The
        # FLOOR matters as much as the range: the first pass took it to 0.20 x a
        # deep green and the buried blades came out at 0.01, which reads as a
        # HOLE punched in the card, not as shade.  Deep foliage shadow is dark
        # green, never black.
        ao = AO_FLOOR + (1.0 - AO_FLOOR) * float(np.clip(z, 0.0, 1.0)) ** 0.75
        # translucency: a blade turned away from the sun still glows, warm and
        # strongest near the thin margin.  The FF-remake tell.
        tr = trans * np.clip(-ndl, 0.0, 1.0) * (0.45 + 0.55 * t)
        c = (np.asarray(rgb)[None, :] * ((sky + 0.98 * lam) * ao)[:, None]
             + tr[:, None] * TRANS_TINT[None, :]
             + spec[:, None] * SPEC_TINT[None, :])
        c *= (1.0 + 0.16 * np.exp(-((t / 0.085) ** 2))
              - 0.13 * np.exp(-(((t - 0.20) / 0.13) ** 2)))[:, None]
        self._put(yy[m], xx[m], zz, np.clip(c, 0.0, 4.0), N)

    def dot(self, cx, cy, r, rgb, z):
        g = self._box(cx, cy, int(r) + 2)
        if g is None:
            return
        yy, xx = g
        m = ((xx - cx) ** 2 + (yy - cy) ** 2) <= max(r * r, 1e-3)
        if not m.any():
            return
        k = int(m.sum())
        self._put(yy[m], xx[m], np.full(k, z, np.float32),
                  np.tile(np.asarray(rgb, np.float32), (k, 1)),
                  np.tile(_norm(np.array([[0.0, 0.12, 0.99]])), (k, 1)))

    def stem(self, x0_, y0_, x1_, y1_, r, z, rgb=None):
        """A twig, as a chain of dots.  A spray with no visible rachis reads as
        confetti — the stems are what tie its blades into one thing."""
        rgb = STEM if rgb is None else np.asarray(rgb)
        ln = math.hypot(x1_ - x0_, y1_ - y0_)
        npt = max(2, int(ln / max(r * 0.7, 0.5)))
        shade = rgb * (0.45 + 0.55 * float(np.clip(z, 0, 1)))
        for k in range(npt + 1):
            f = k / npt
            self.dot(x0_ + (x1_ - x0_) * f, y0_ + (y1_ - y0_) * f,
                     r * (1.0 - 0.35 * f), shade, z - 0.006)


# ---------------------------------------------------------------------------
# THE SPRAY — a rachis carrying alternating blades.  Real foliage is organised
# into sprays; scattering single leaves is the other way to make confetti.
# ---------------------------------------------------------------------------
def spray(C, rng, bx, by, ang, ln, leaf_len, leaf_w, z, plate, cross, rgb,
          nleaf=7, stem_r=1.1, fold=0.90, gloss=0.10):
    ex, ey = bx + math.cos(ang) * ln, by + math.sin(ang) * ln
    if stem_r > 0:
        C.stem(bx, by, ex, ey, stem_r, z)
    for oi in np.argsort(rng.rand(nleaf)):           # random draw order within
        f = 0.14 + 0.86 * (oi / max(nleaf - 1, 1))
        px = bx + math.cos(ang) * ln * f
        py = by + math.sin(ang) * ln * f
        side = 1.0 if (oi % 2 == 0) else -1.0
        la = ang + side * rng.uniform(0.55, 1.15) - 0.10 * f
        # each blade rolls a little around the rachis: one plate normal over a
        # whole spray is how a cluster starts looking printed
        rl = rng.uniform(-0.42, 0.42)
        pl = _norm(plate + rl * cross
                   + rng.uniform(-0.16, 0.16) * np.cross(cross, plate))
        cr = _norm(cross - rl * plate)
        C.leaf(px, py, leaf_len * (1.02 - 0.34 * f) * rng.uniform(0.82, 1.18),
               leaf_w * rng.uniform(0.84, 1.16), la, z + 0.004 * oi,
               rgb * rng.uniform(0.84, 1.16), pl, cr, fold=fold, gloss=gloss,
               phase=float(rng.uniform(0, 6.283)))
    C.leaf(ex, ey, leaf_len * rng.uniform(0.72, 0.98), leaf_w * 0.92, ang,
           z + 0.03, rgb * rng.uniform(0.92, 1.20), plate, cross, fold=fold,
           gloss=gloss, phase=float(rng.uniform(0, 6.283)))


def spray_colour(rng, zn):
    """Colour for one spray from its DEPTH in the clump: front and top sprays
    catch the sun, buried ones stay in the deep green.  Plus the strays."""
    r = rng.rand()
    if r < AUTUMN_RATIO:
        return (AUT if rng.rand() < 0.6 else AUT2) * rng.uniform(0.80, 1.15)
    if r < AUTUMN_RATIO + PALE_RATIO:
        return PALE * rng.uniform(0.88, 1.12)
    k = float(np.clip(zn * rng.uniform(0.75, 1.25), 0.0, 1.0))
    for (lo, hi, a, b_) in ((0.00, 0.34, G_DEEP, G_MID),
                            (0.34, 0.72, G_MID, G_LIT),
                            (0.72, 1.01, G_LIT, G_SUN)):
        if k < hi:
            return (a + (b_ - a) * (k - lo) / (hi - lo)) * rng.uniform(0.90, 1.10)
    return G_SUN


# three (nspray, z_lo, z_hi, leaf_len, leaf_w, nleaf) passes per kind
PASSES = {
    "big": ((70, 0.30, 0.62, 0.056, 0.0150, 7),
            (86, 0.58, 1.00, 0.047, 0.0136, 6),
            (52, 0.80, 1.00, 0.036, 0.0114, 5)),
    "fuzz": ((17, 0.34, 0.72, 0.080, 0.0196, 6),
             (21, 0.62, 1.00, 0.064, 0.0168, 5),
             (14, 0.84, 1.00, 0.047, 0.0141, 5)),
}
INTERIOR = {"big": (620, 0.88, 0.034, 0.058), "fuzz": (110, 0.62, 0.030, 0.050)}
BACKDROP = {"big": 0.80, "fuzz": 0.0}       # opaque floor, as a fraction of rad()


def clump(n, seed, kind="big"):
    """One atlas cell: a DOME of sprays, drawn back to front in three layers.

    LAYER 0, the interior, is what every earlier atlas was missing.  A card
    whose gaps are TRANSPARENT is a flake however many leaves are on it: against
    the sky the holes read as damage, and against the mass behind it the card
    disappears.  So the interior is a dense mat of small very dark blades over a
    shrunken silhouette — opaque, but made of leaves, so it never reads as a
    painted disc either.
    """
    C = Cluster(n)
    rng = np.random.RandomState(seed)
    cx = cy = n / 2.0
    ph = rng.rand(6) * 6.283
    R = n * (R_BIG if kind == "big" else R_FUZZ)

    def rad(a):
        return R * (1.0 + 0.20 * np.sin(3 * a + ph[0])
                    + 0.12 * np.sin(5 * a + ph[1])
                    + 0.075 * np.sin(7 * a + ph[2]))

    def dome(rx, ry, k=1.0):
        """Depth 0..1 and the outward dome normal at an offset from the centre."""
        rr = math.hypot(rx, ry) / R
        zn = math.sqrt(max(0.0, 1.0 - min(rr, 1.0) ** 2))
        nv = _norm(np.array([rx / R, ry / R, max(zn * k, 0.06)]))
        return zn, nv

    # ---- layer -1: the OPAQUE BACKDROP -------------------------------------
    # Counting leaves is not a way to fill a disc.  The first pass put 430 small
    # blades over the interior and covered 28% of it, so the middle of every big
    # card was SKY — and a card you can see the sky through in its middle is a
    # flake by definition, whatever its rim looks like.  So the mass gets a
    # floor: a filled lobed disc, well inside the silhouette (0.80 of it, so the
    # rim stays leaf-made), in noise-broken deep green.  It is never seen as a
    # disc because the interior mat and the sprays are drawn on top of it.
    if BACKDROP[kind] > 0:
        yy, xx = np.mgrid[0:n, 0:n]
        dx, dy = xx - cx, yy - cy
        rr = np.hypot(dx, dy)
        aa = np.arctan2(dy, dx)
        m = rr <= rad(aa) * BACKDROP[kind]
        if m.any():
            v = (0.72 + 0.34 * np.sin(dx * (9.0 / n) + ph[3])
                 * np.sin(dy * (11.0 / n) + ph[4])
                 + 0.20 * np.sin((dx + dy) * (23.0 / n) + ph[5]))
            k = int(m.sum())
            C._put(yy[m], xx[m], np.full(k, -0.02, np.float32),
                   (G_DEEP * 1.15)[None, :] * np.clip(v[m], 0.35, 1.3)[:, None],
                   np.tile(_norm(np.array([[0.0, 0.15, 0.99]])), (k, 1)))

    # ---------------- layer 0: the dark interior mat ------------------------
    cnt, shrink, l0, l1 = INTERIOR[kind]
    for _ in range(cnt):
        a = rng.rand() * 6.283
        rr = rad(a) * shrink * rng.rand() ** 0.42
        px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        zn, nv = dome(px - cx, py - cy, 0.55)
        cr = _norm(np.cross(nv, UP) + 1e-7)
        # an OPEN card has no mass behind it, so its inner blades are seen
        # against the sky: they have to be shade greens, not interior greens, or
        # every fuzz card wears a handful of black leaf-shaped holes
        lo_, hi_ = (G_DEEP, G_MID) if BACKDROP[kind] > 0 else (G_MID, G_LIT)
        C.leaf(px, py, n * rng.uniform(l0, l1), n * 0.0135, rng.rand() * 6.283,
               0.02 + 0.20 * zn * rng.uniform(0.6, 1.0),
               (lo_ + (hi_ - lo_) * rng.rand() ** 1.6) * rng.uniform(0.9, 1.5),
               nv, cr, fold=0.50, gloss=0.02, trans=0.05,
               phase=float(rng.uniform(0, 6.283)))

    # ---------------- layers 1-2: the sprays, drawn back to front -----------
    jobs = []
    for (nspray, z0, z1, ll, lw, nleaf) in PASSES[kind]:
        for _ in range(nspray):
            a = rng.rand() * 6.283
            # the RIM is where a projected dome is densest (grazing angle) and
            # it is the only place a card's silhouette can come from
            rr = rad(a) * (0.10 + 0.94 * rng.rand() ** 0.42)
            px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            zn, nv = dome(px - cx, py - cy)
            z = z0 + (z1 - z0) * (0.35 + 0.65 * zn) * rng.uniform(0.82, 1.0)
            # the spray points OUTWARD along the dome, so rim sprays throw their
            # blades past the silhouette and the card's edge is made of leaves
            out = math.atan2(py - cy, px - cx) + rng.uniform(-0.85, 0.85)
            ln = n * ll * rng.uniform(0.75, 1.30) * (1.6 if rr > R * 0.72 else 1.25)
            nv2 = _norm(nv + rng.uniform(-0.30, 0.30, 3))
            jobs.append((z, px, py, out, ln, n * ll, n * lw, nv2,
                         _norm(np.cross(nv2, UP) + 1e-7), nleaf))
    jobs.sort(key=lambda j: j[0])
    for (z, px, py, out, ln, ll, lw, nv2, cr, nleaf) in jobs:
        spray(C, rng, px, py, out, ln, ll, lw, z, nv2, cr,
              spray_colour(rng, z), nleaf=nleaf, stem_r=max(0.9, n * 0.0022))
    return C


# ---------------------------------------------------------------------------
def _downsample(a, k):
    h, w = a.shape[:2]
    a = a[: h // k * k, : w // k * k]
    return a.reshape((h // k, k, w // k, k) + a.shape[2:]).mean(axis=(1, 3))


def _write(path, buf, fmt):
    """Save an (h, w, 4) float buffer, y-UP, as PNG or JPEG.

    PIL when run under python3, Blender's own image API when run inside Blender
    (which ships numpy but not PIL).  The atlas is a one-off asset, but a fresh
    checkout that only ever runs the Blender scripts still has to be able to
    generate it, so both paths exist.
    """
    buf = np.ascontiguousarray(np.clip(buf[::-1], 0, 1), dtype=np.float32)
    try:
        from PIL import Image
        mode = "RGBA" if fmt == "PNG" else "RGB"
        arr = (buf[..., :4 if fmt == "PNG" else 3] * 255.0 + 0.5).astype(np.uint8)
        Image.fromarray(arr, mode).save(path, **({"quality": 92} if fmt == "JPEG" else {}))
        return
    except ImportError:
        pass
    import bpy
    nm = os.path.basename(path)
    old = bpy.data.images.get(nm)
    if old is not None:
        bpy.data.images.remove(old)
    im = bpy.data.images.new(nm, buf.shape[1], buf.shape[0], alpha=(fmt == "PNG"))
    im.filepath_raw = path
    im.file_format = fmt
    # Blender's pixel buffer is y-up, so undo the flip we just applied
    im.pixels.foreach_set(buf[::-1].ravel())
    im.update()
    im.save()


def _save_rgba(path, rgb, alpha):
    _write(path, np.concatenate([rgb, np.clip(alpha, 0, 1)[..., None]], -1), "PNG")


def _save_rgb(path, rgb):
    _write(path, np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1), "JPEG")


def build_atlas(force=False, cell=CELL, grid=GRID, ss=SS, seed=7717):
    if not force and os.path.exists(ATLAS) and os.path.exists(ATLAS_NOR):
        return ATLAS, ATLAS_NOR
    os.makedirs(TEXO, exist_ok=True)
    A = cell * grid
    alb = np.zeros((A, A, 3), np.float32)
    alp = np.zeros((A, A), np.float32)
    nor = np.zeros((A, A, 3), np.float32)
    nor[..., 2] = 1.0
    n = cell * ss
    for ci in range(grid * grid):
        kind = "big" if ci < N_BIG else "fuzz"
        C = clump(n, seed + ci * 613, kind)
        a = _downsample(C.alp, ss)
        N = _norm(_downsample(C.nrm, ss))
        # PREMULTIPLIED resolve: a downsampled edge pixel must not drag the
        # transparent black behind it into the colour — that is where an alpha
        # atlas gets its dark fringe, and a dark fringe on every leaf edge is
        # exactly what reads as "flakes" at distance.
        rgb = _downsample(C.col, ss) / np.maximum(a, 1e-4)[..., None]
        gx, gy = ci % grid, ci // grid
        y0 = (grid - 1 - gy) * cell                  # cell 0 = TOP-left
        x0 = gx * cell
        alb[y0:y0 + cell, x0:x0 + cell] = np.clip(rgb, 0, 1)
        alp[y0:y0 + cell, x0:x0 + cell] = a
        nor[y0:y0 + cell, x0:x0 + cell] = N
        print("  cell %2d %-4s  cover %5.1f%%  mean %.3f"
              % (ci, kind, 100.0 * float((a > 0.5).mean()),
                 float(rgb[a > 0.5].mean()) if (a > 0.5).any() else 0.0))
    _save_rgba(ATLAS, alb, alp)
    _save_rgb(ATLAS_NOR, nor * 0.5 + 0.5)
    print("  atlas  -> %s (%.2f MB)   normal -> %s (%.2f MB)"
          % (os.path.basename(ATLAS), os.path.getsize(ATLAS) / 1e6,
             os.path.basename(ATLAS_NOR), os.path.getsize(ATLAS_NOR) / 1e6))
    return ATLAS, ATLAS_NOR


def build_tile(force=False, size=768, ss=2, seed=4211):
    """The TILEABLE leaf mass for the bush CORES.

    Same blades, same sun, but wrapped and with no dome: a mat of foliage seen
    from just outside a mass, dark in its gaps.  The cores are shelled with
    cards, so this texture's only jobs are to be dark, to be leafy and to carry
    a normal — it must never compete with the cards for silhouette.
    """
    if not force and os.path.exists(TILE) and os.path.exists(TILE_NOR):
        return TILE, TILE_NOR
    n = size * ss
    C = Cluster(n, wrap=True)
    rng = np.random.RandomState(seed)
    for (cnt, ll, lw, z0, z1, dark) in ((900, 0.048, 0.0140, 0.02, 0.30, 0.55),
                                        (1500, 0.036, 0.0115, 0.28, 0.66, 0.85),
                                        (1700, 0.026, 0.0092, 0.62, 1.00, 1.00)):
        jobs = sorted((rng.uniform(z0, z1), rng.rand() * n, rng.rand() * n)
                      for _ in range(cnt))
        for (z, px, py) in jobs:
            nv = _norm(np.array([rng.uniform(-0.55, 0.55), rng.uniform(-0.55, 0.55),
                                 rng.uniform(0.55, 1.0)]))
            C.leaf(px, py, n * ll * rng.uniform(0.8, 1.25), n * lw,
                   rng.rand() * 6.283, z, spray_colour(rng, z * dark) * 0.86,
                   nv, _norm(np.cross(nv, UP) + 1e-7), gloss=0.06,
                   phase=float(rng.uniform(0, 6.283)))
    rgb = _downsample(C.col, ss)
    a = _downsample(C.alp, ss)
    N = _norm(_downsample(C.nrm, ss))
    rgb = rgb / np.maximum(a, 1e-4)[..., None]
    # a hole in the CORE is canopy shadow, never sky: the core is opaque by
    # contract, and the cards are what let the sky through
    rgb[a < 0.5] = G_DEEP * 0.45
    _save_rgb(TILE, np.clip(rgb, 0, 1))
    _save_rgb(TILE_NOR, N * 0.5 + 0.5)
    print("  core tile -> %s (%.2f MB) + normal (%.2f MB)  cover %.1f%%"
          % (os.path.basename(TILE), os.path.getsize(TILE) / 1e6,
             os.path.getsize(TILE_NOR) / 1e6, 100.0 * float((a > 0.5).mean())))
    return TILE, TILE_NOR


def contact_sheet(path=None, zoom=2, picks=(0, 1, 2, 8, 9, 10)):
    """The honesty check: cells at 200% over sky, over dark mass, and the normal.
    If a card reads as flakes HERE it will read as flakes in the tile."""
    from PIL import Image
    path = path or os.path.join(QA, "valley_leafcard_atlas.png")
    im = Image.open(ATLAS).convert("RGBA")
    nm = Image.open(ATLAS_NOR).convert("RGB")
    c = im.size[0] // GRID
    cz = c * zoom
    cols, rows = 4, 2
    sheet = Image.new("RGB", (cols * cz, rows * cz), (26, 28, 32))
    sky = Image.new("RGBA", (cz, cz), (122, 152, 190, 255))
    dark = Image.new("RGBA", (cz, cz), (18, 28, 16, 255))
    for k, ci in enumerate(picks[:6]):
        gx, gy = ci % GRID, ci // GRID
        cell = im.crop((gx * c, gy * c, gx * c + c, gy * c + c)).resize(
            (cz, cz), Image.LANCZOS)
        bg = (sky if k % 2 == 0 else dark).copy()
        bg.alpha_composite(cell)
        sheet.paste(bg.convert("RGB"), ((k % 3) * cz, (k // 3) * cz))
    for k, ci in enumerate(picks[:2]):
        gx, gy = ci % GRID, ci // GRID
        sheet.paste(nm.crop((gx * c, gy * c, gx * c + c, gy * c + c)).resize(
            (cz, cz), Image.LANCZOS), (3 * cz, k * cz))
    sheet.save(path)
    print("  contact sheet -> %s" % path)
    return path


if __name__ == "__main__":
    import time
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--cell", type=int, default=CELL)
    ap.add_argument("--ss", type=int, default=SS)
    a = ap.parse_args()
    t0 = time.time()
    build_atlas(force=a.force, cell=a.cell, ss=a.ss)
    build_tile(force=a.force)
    print("  %.1fs" % (time.time() - t0))
    if a.sheet:
        contact_sheet()
