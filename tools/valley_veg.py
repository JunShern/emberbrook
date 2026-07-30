"""valley_veg.py — the valley's FOURTH forest, its rock and its meadow.

Everything this pass adds to the region lives here so that the diff in
`tools/valley_build.py` is three lines:

    import valley_veg as VV
    VV.patch_terrain()                       # once, before build_terrain
    ... VV.build_canopy(col, F, zg, fr, VM, STATS)   # replaces build_canopy

which matters because valley_build.py is shared with the geography session.

WHY A FOURTH FOREST.  The first three all answered "what shape is a forest?"
and the answer was never the problem:

  1. BLANKET      one billowed surface over the stand.  Read as a green duvet.
  2. CROWN DOMES  packed per-crown domes, hue per crown.  Read as a bag of peas.
  3. PAINTED TEX  a gentle swell + ~600 painted crowns in an albedo/normal pair.
                  Read as patterned ground — the geometry had no silhouette at
                  all, so from the follow camera it was a green hillside.

Each was a different geometry over the SAME class of texture: procedural blobs
with a radial ramp.  The user's ruling reframes it — at this scale a whole forest
is the size of one of the reference's BUSHES, so build it like a bush: a lobed
core with a DENSE SHELL of leaf-cluster cards over it, on a real atlas.  The
atlas is `tools/foliage_atlas.py`, the construction is `tools/bushlang.py`, and
this file is where the region's stands, corridors and clearings meet them.
"""
import math
import os

import bpy
import numpy as np

import overworld_lib as L
import overworld_build as B
import overworld2_build as B2
import overworld3_lib as O3
import overworld3_build as B3
import bushlang as BL
import foliage_atlas as FA

ROOT = B3.ROOT
TEX = os.path.join(ROOT, "tools/textures")
TEXO = os.path.join(TEX, "overworld")

# ------------------------------------------------------------------ taste knobs
LOBE_SP = 3.8               # lobe spacing over a stand, world units
LOBE_R = (2.9, 4.3)         # interior lobe radius (min, max)
LOBE_R_EDGE = (1.9, 2.7)    # ... at the stand edge, where the mass tapers
LOBE_H = (2.3, 4.0)         # lobe half-height range, scaled by the billow
DENSITY = 1.0             # CARDS PER SQUARE UNIT of visible core — the knob
BIG = (1.95, 3.05)          # big-clump card size at region scale: one treetop
FUZZ = (0.95, 1.55)
FUZZ_FRAC = 0.34
EDGE_DENSITY = 1.9          # the rim gets more cards: it is all silhouette

# rock
ROCK_SET = "dark_rock_02"   # stratified/striated — the gorge walls' hero material
CRAG_STRATA = 0.62          # bedding-terrace amplitude, world units
CRAG_BED = 2.9              # bed thickness
# The re-weighting is meant to be SPECTRAL, not louder.  Measured over the
# region's 20.1% crag cells, moving the octaves down and adding the bedding took
# the displacement's sd from 0.426 to 0.608 and its peak from 1.85 to 2.57u — and
# a taller crag is a new clearance risk for every walk ribbon that runs beside
# one, which is not what this pass is for.  0.70 puts the amplitude back where it
# was and leaves only the change that was wanted: the share of relief surviving a
# 7.5u blur (i.e. the share that reads as landform) goes 0.68 -> 0.83.
AMP_TRIM = 0.70
MEADOW_FLOWERS = 0.00085    # flower SEEDS per pixel (each throws 1-6 heads)


# ===========================================================================
# 1. THE FOREST
# ===========================================================================
def _stand_mask(F, zg, VM, st, rd, rs):
    """The stand's plantable cells, minus the road corridor and the clearings.

    Lifted verbatim from the third iteration so the CARVES do not change: the
    user's road note (nothing may overhang the road) and the map's clearings are
    settled behaviour and this pass is about texture, not about layout.
    """
    mask = zg.stand[st["id"]].copy()
    cor = st.get("corridor")
    if cor:
        w = float(cor.get("width", 6.0)) * 0.5 + 2.4
        s0, s1 = cor.get("alongRoad", [0, len(VM.ROAD_CTRL_W) - 1])
        sa = VM._arclen(VM.ROAD_CTRL_W[:, :2])
        lo, hi = float(sa[int(s0)]), float(sa[int(min(s1, len(sa) - 1))])
        mask &= ~((rd < w) & (rs >= lo - 4.0) & (rs <= hi + 8.0))
    else:
        mask &= ~(rd < 5.6)
    for c in st.get("clearings", []):
        cx_, cy_ = VM.w2b(c["at"][0], c["at"][1])
        mask &= (np.hypot(zg.BX - cx_, zg.BY - cy_) > float(c["r"]))
    return mask


def _lobe_sites(zg, mask, edge, rng, spacing=LOBE_SP):
    """Jittered-hex lobe centres over a stand mask, in BLENDER coords.

    A hex lattice rather than rejection sampling: a stand is a BLANKET, and the
    one thing it must not have is a hole, so the sites want to be even and the
    jitter only wants to stop the lattice reading as a lattice.
    """
    ii, jj = np.nonzero(mask)
    if not len(ii):
        return np.zeros((0, 3))
    x0, x1 = float(zg.BX[ii, jj].min()), float(zg.BX[ii, jj].max())
    y0, y1 = float(zg.BY[ii, jj].min()), float(zg.BY[ii, jj].max())
    dy = spacing * 0.866
    out = []
    row = 0
    y = y0 - dy
    while y <= y1 + dy:
        off = (row % 2) * spacing * 0.5
        xs = np.arange(x0 - spacing, x1 + spacing, spacing) + off
        for x in xs:
            px = float(x + rng.uniform(-0.34, 0.34) * spacing)
            py = float(y + rng.uniform(-0.34, 0.34) * spacing)
            e = float(zg.wsample(edge, px, py))
            if e <= 0.12:
                continue
            out.append((px, py, e))
        row += 1
        y += dy
    return np.array(out) if out else np.zeros((0, 3))


def stand_mass(name, F, sites, rng, density=None):
    """Grow ONE stand's mass from its lobe sites: core, cull, shade, shell.

    Separate from build_canopy so `tools/foliage_stand.py` can exercise the
    expensive half on a synthetic stand without the map, the zone grid or the
    valley blend — which is how this recipe was tuned while the geography session
    held the pipeline.
    """
    M = BL.Mass(name)
    # the billow is the same field the third iteration's swell used, so the mass
    # keeps the LANDFORM that was already right; it only grows a surface now
    bx, by = sites[:, 0], sites[:, 1]
    billow = (np.abs(O3.fbm(bx, by, 0.11, seed=61, oct_=3))
              + 0.5 * np.abs(O3.fbm(bx, by, 0.31, seed=62, oct_=2)))
    tone_n = O3.fbm(bx, by, 0.045, seed=77, oct_=2)
    gz = F.sample(bx, by)
    for k in range(len(sites)):
        e = float(sites[k, 2])
        lo, hi = (LOBE_R_EDGE if e < 0.55 else LOBE_R)
        r = float(rng.uniform(lo, hi))
        h = float(LOBE_H[0] + (LOBE_H[1] - LOBE_H[0]) * min(float(billow[k]), 1.0)) \
            * (0.62 + 0.38 * e)
        M.lobe(float(bx[k]), float(by[k]), float(gz[k]) + h * 0.42,
               r, r * rng.uniform(0.84, 1.14), h * 0.62,
               subd=1, seed=rng.randint(1 << 28),
               squash=float(rng.uniform(0.10, 0.24)),
               tone=float(0.86 + 0.30 * float(tone_n[k])))
    killed, total = M.cull_interior()
    # Darker than a lit surface but NOT black: at region scale the core is only
    # seen through gaps in the shell and a gap must read as canopy SHADOW, but
    # the first attempt at 0.115/0.245 (with the shell AO fixed) split the mass
    # into bright clumps sitting on black rock.  Core and shell have to stay
    # within about a stop of each other or the mass stops being one thing.
    M.shade_core(deep=0.20, lift=0.42)
    n = M.shell(rng, density=DENSITY if density is None else density,
                big=BIG, fuzz=FUZZ, fuzz_frac=FUZZ_FRAC)
    return M, killed, total, n


def build_canopy(col, F, zg, fr, VM, STATS=None):
    """The stands as BUSH MASSES: lobed cores plus a dense leaf-card shell.

    Runtime contract unchanged from the previous three iterations: everything is
    `veg_`, so the runtime removes it from collision entirely (no standing AND no
    blocking — forests are walkable encounter terrain, MIGRATION's height-only
    gating ruling), the cards are their own mesh because they are the tile's only
    alpha-MASK material, and `zg.canopy_int` still holds the interior so
    `plant_region` keeps its specimen trees to the edges.
    """
    STATS = STATS if STATS is not None else {}
    atlas, atlas_nor = FA.build_atlas()
    tile, tile_nor = FA.build_tile()
    core_mat, card_mat = BL.materials(atlas, atlas_nor, tile, tile_nor,
                                     suffix="valley", pbr_mat=B2.pbr_mat)
    made = []
    zg.canopy_int = np.zeros_like(zg.BX, dtype=bool)
    RD = np.hypot(zg.BX[..., None] - F.road[::4, 0], zg.BY[..., None] - F.road[::4, 1])
    ri = RD.argmin(-1) * 4
    rd = RD.min(-1)
    rs = F.road_s[np.clip(ri, 0, len(F.road_s) - 1)]

    for si, st in enumerate(VM.FORESTS):
        if st.get("representation") != "canopy":
            continue
        mask = _stand_mask(F, zg, VM, st, rd, rs)
        if not mask.any():
            continue
        soft = O3._box(mask.astype(float), 3)
        edge = np.clip(soft * 1.45, 0.0, 1.0)          # 1 inside, tapering out
        zg.canopy_int |= soft > 0.55
        rng = np.random.RandomState(90210 + si * 733)
        sites = _lobe_sites(zg, soft > 0.10, edge, rng)
        if not len(sites):
            continue
        M, killed, total, n = stand_mass("veg_canopy_" + st["id"], F, sites, rng)
        objs = M.finish(col, core_mat, card_mat)
        for key, ob in objs.items():
            nm = "veg_canopy_%s%s" % (st["id"], "_cards" if key == "cards" else "")
            ob.name = ob.data.name = nm
            made.append(ob)
        ct = int(len(M._F))
        STATS["canopy_" + st["id"]] = dict(lobes=len(sites), core_tris=ct,
                                           culled=killed, cards=n)
        print("  canopy %-18s %4d lobes, core %5d/%5d tris, %6d cards"
              % (st["id"], len(sites), ct, total, n))
    return made


# ===========================================================================
# 2. THE ROCK
# ===========================================================================
def _crag_strata(F, zg, x, y):
    """BEDDING TERRACES, as a function of the underlying height.

    The crag treatment's three octaves of ridged noise sit at wavelengths of 6.5,
    2.4 and 1.0 world units, and at region scale that reads as GRAVEL heaped on a
    cliff however tall the cliff is: there is no form bigger than 6.5u anywhere
    in it.  Rock does not work like that — a rock face is a few large coherent
    surfaces, bedding planes stacked and cut by joints.  This adds the bedding:
    a sawtooth in the underlying height that pulls ground toward the top of its
    own bed, with a slow DIP so the beds are not spirit-level flat (level beds
    read as contour lines, which is a map, not a landform).
    """
    h = F.sample(x, y)
    dip = 0.052 * x + 0.031 * y
    q = (h + dip) / CRAG_BED
    saw = np.floor(q) - q + 0.5                       # -0.5 .. +0.5
    # only where the ground is actually steep: terracing a meadow is a rice field
    return CRAG_STRATA * saw * np.clip(F.slope_at(x, y) / 0.9, 0.0, 1.0)


_ORIG_CRAG = None


def patch_crag():
    """Re-weight crag_disp toward LARGE coherent forms, and add the bedding.

    Kept as a wrapper for the same reason valley_build wraps `road_notch`: the
    prototype's F2 tile must keep rendering byte-for-byte, and the treatment is
    module state that the mesh, the tree feet, the markers and the QA overlay all
    read through one function (finding 141).
    """
    global _ORIG_CRAG
    if _ORIG_CRAG is not None:
        return
    _ORIG_CRAG = O3.crag_disp

    def crag_disp(F, zg, x, y, fr=None):
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        w = zg.wsample(zg.crag_w, x, y)
        g = _guard(F, zg, x, y, fr)
        # 19u / 7u / 2.3u instead of 6.5 / 2.4 / 1.0, same total amplitude:
        # the mass moves down into wavelengths the camera can read as landform
        d = ((O3.ridged(x, y, 0.052, 11) - 0.42) * 2.15
             + (O3.ridged(x, y, 0.145, 23) - 0.42) * 1.05
             + (O3.ridged(x, y, 0.440, 37) - 0.42) * 0.34)
        d = (d + _crag_strata(F, zg, x, y)) * AMP_TRIM
        return d * O3.CRAG_AMP * np.clip(w, 0.0, 1.0) ** 1.35 * g

    O3.crag_disp = crag_disp


def _guard(F, zg, x, y, fr):
    """The blockout-preserving guard, verbatim from O3.crag_disp.

    Duplicated rather than refactored ON PURPOSE: overworld3_lib is the F2
    prototype's shipped library and the geography session is editing the valley
    around this pass, so the guard's behaviour is pinned here where it cannot
    drift under either of us.  If it ever needs to change it changes in O3 and
    this copy is deleted with it.
    """
    g = L.sstep(3.2, 6.8, F.road_dist(x.ravel(), y.ravel()).reshape(x.shape))
    dr, tr = F._river_dist(x.ravel(), y.ravel())
    dr = dr.reshape(x.shape)
    hw = F.water_halfwidth(tr).reshape(x.shape)
    g = g * L.sstep(0.8, 4.2, dr - hw)
    vx, vy = L.VILLAGE
    g = g * L.sstep(7.0, 13.5, np.hypot(x - vx, y - vy))
    cx, cy = L.CLIFFTOWN
    g = g * L.sstep(6.5, 12.5, np.hypot(x - cx, y - cy))
    rt, rx, ry = L.river_pts(601)
    di = int(np.argmin(np.abs(rt - L.DAM_T)))
    g = g * L.sstep(6.0, 11.0, np.hypot(x - rx[di], y - ry[di]))
    if fr is not None:
        g = g * (1.0 - O3._pool_w_np(x, y, fr, 1.9))
    for (x0, y0, x1, y1, inner, outer) in O3.FLAT_PATHS:
        g = g * L.sstep(inner, outer, O3._seg_dist(x, y, x0, y0, x1, y1))
    return g


# ===========================================================================
# 3. THE MEADOW
# ===========================================================================
MEADOW_D = os.path.join(TEXO, "valley_meadow_diff_1k.jpg")
MEADOW_N = os.path.join(TEXO, "valley_meadow_nor_gl_1k.jpg")


def meadow_maps(force=False, size=1024, seed=515):
    """A derived meadow albedo: two grass photos, hue patches, and wildflowers.

    Poly Haven has no meadow-with-flowers texture (their whole grass shelf is
    `leafy_grass`, `sparse_grass`, `withered_grass`), so the upgrade is a
    DERIVATION rather than a download, and three things go into it:

      * TWO SOURCES blended on a low-frequency mask.  One photo tiled over a
        56 000 square-unit region repeats ~1500 times; two photos crossfading
        break the repeat far more cheaply than a bigger texture would.
      * PATCH-SCALE HUE.  A slow warm/cool, dry/lush mottle at about a third of
        the tile, so there is variation INSIDE one repeat and not only between
        vertices (COLOR_0 already carries the between-vertices part).
      * WILDFLOWERS, sparse, in the albedo.  At miniature scale a flower is one
        to three pixels; what the eye picks up is the sprinkle, and a sprinkle is
        exactly what a photograph of a lawn does not have.
    """
    if not force and os.path.exists(MEADOW_D) and os.path.exists(MEADOW_N):
        return MEADOW_D, MEADOW_N
    a = _load(os.path.join(TEXO, "leafy_grass_diff_1k.jpg"), size)
    b_ = _load(os.path.join(TEXO, "sparse_grass_diff_1k.jpg"), size)
    na = _load(os.path.join(TEXO, "leafy_grass_nor_gl_1k.jpg"), size)
    nb = _load(os.path.join(TEXO, "sparse_grass_nor_gl_1k.jpg"), size)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    rng = np.random.RandomState(seed)
    ph = rng.rand(8) * 6.283

    # A SUM OF SINUSOIDS IS A LATTICE.  Two passes went here.  The first used
    # separable sin(x)sin(y) at 1-3 cycles and came back as diagonal CORDUROY
    # marching across the whole meadow; the second used four diagonal waves at
    # coprime-ish frequencies and came back as a quilted CROSS-HATCH, because a
    # handful of pure tones summed is still periodic — it just has a bigger cell,
    # and the eye finds it instantly because it is the only straight thing in a
    # landscape.  A tiling texture needs tiling NOISE, and the cheap exact way to
    # get it is an inverse FFT of a random-phase spectrum: every coefficient is a
    # whole number of cycles across the image, so it wraps by construction, and
    # random phases mean there is no cell at all.
    def fnoise(k0, k1, seed_):
        r = np.random.RandomState(seed_)
        ky, kx = np.mgrid[0:size, 0:size]
        ky = np.minimum(ky, size - ky)
        kx = np.minimum(kx, size - kx)
        kk = np.hypot(kx, ky)
        amp = np.where((kk >= k0) & (kk <= k1),
                       1.0 / np.maximum(kk, 1.0) ** 0.8, 0.0)
        f = np.real(np.fft.ifft2(amp * np.exp(2j * np.pi * r.rand(size, size))))
        f = f - f.mean()
        return (f / (f.std() + 1e-9)).astype(np.float32)

    # weighted toward the GREEN source: sparse_grass is mostly soil, and an even
    # crossfade made the meadow read as dry ground with grass in it
    m = np.clip(0.36 + 0.17 * fnoise(2, 9, seed + 1), 0.14, 0.58)[..., None]
    dif = a * (1.0 - m) + b_ * m
    nor = na * (1.0 - m) + nb * m
    # patch-scale hue: warm/dry one way, cool/lush the other
    hue = np.clip(0.5 + 0.21 * fnoise(2, 7, seed + 2), 0.20, 0.80)
    warm = np.array([1.06, 1.04, 0.88], np.float32)
    cool = np.array([0.90, 1.03, 0.93], np.float32)
    dif = dif * (cool[None, None, :] + (warm - cool)[None, None, :] * hue[..., None])
    # ---- the wildflowers -------------------------------------------------
    PET = (np.array([0.95, 0.93, 0.80]), np.array([0.93, 0.85, 0.28]),
           np.array([0.72, 0.66, 0.90]), np.array([0.90, 0.72, 0.78]))
    n = int(MEADOW_FLOWERS * size * size)
    for _ in range(n):
        cx_, cy_ = rng.randint(0, size), rng.randint(0, size)
        c = PET[rng.randint(len(PET))] * rng.uniform(0.58, 0.92)
        r = rng.uniform(0.9, 2.0)
        # flowers come in PATCHES, never evenly: one seed throws 1-6 heads
        for _k in range(rng.randint(1, 7)):
            fx = int(cx_ + rng.randn() * 7.0) % size
            fy = int(cy_ + rng.randn() * 7.0) % size
            rr = int(r) + 1
            g = np.mgrid[fy - rr:fy + rr + 1, fx - rr:fx + rr + 1]
            d2 = (g[0] - fy) ** 2 + (g[1] - fx) ** 2
            sel = d2 <= r * r
            if not sel.any():
                continue
            iy_, ix_ = g[0][sel] % size, g[1][sel] % size
            # BLEND, do not replace: a petal painted at full opacity over a photo
            # is a sticker, and a meadow of stickers is worse than no flowers
            dif[iy_, ix_] = dif[iy_, ix_] * 0.22 + c[None, :] * 0.78
    _save(MEADOW_D, np.clip(dif, 0, 1))
    _save(MEADOW_N, np.clip(nor, 0, 1))
    print("  meadow maps -> %s (%.2f MB)" % (os.path.basename(MEADOW_D),
                                             os.path.getsize(MEADOW_D) / 1e6))
    return MEADOW_D, MEADOW_N


def _load(path, size):
    im = bpy.data.images.load(path, check_existing=True)
    w, h = im.size
    a = np.zeros(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[..., :3]
    if (h, w) != (size, size):
        yi = (np.arange(size) * (h / size)).astype(int)
        xi = (np.arange(size) * (w / size)).astype(int)
        a = a[np.ix_(yi, xi)]
    return a


def _save(path, rgb):
    FA._write(path, np.concatenate([rgb, np.ones(rgb.shape[:2] + (1,))], -1), "JPEG")


# ===========================================================================
_PATCHED = False


def patch_terrain():
    """Swap the terrain's ROCK and GRASS slots, and re-weight the crag.

    `B3.layer_paths` is a function precisely so it can be re-pointed: the F2
    prototype build never calls this, so its tile is untouched.
    """
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    md, mn = meadow_maps()
    orig = B3.layer_paths

    def layer_paths():
        out = []
        for (nm, d, n, r) in orig():
            if nm == "rock":
                out.append((nm, os.path.join(TEXO, ROCK_SET + "_diff_1k.jpg"),
                            os.path.join(TEXO, ROCK_SET + "_nor_gl_1k.jpg"),
                            os.path.join(TEXO, ROCK_SET + "_rough_1k.jpg")))
            elif nm == "grass":
                out.append((nm, md, mn, os.path.join(TEXO, "leafy_grass_rough_1k.jpg")))
            else:
                out.append((nm, d, n, r))
        return out

    B3.layer_paths = layer_paths
    patch_crag()
    print("  terrain patched: rock=%s, meadow=derived, crag=strata" % ROCK_SET)
