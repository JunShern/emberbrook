"""bushlang.py — BUSH CONSTRUCTION for miniature-scale forest masses.

The user's ruling, ratified: at this world's scale a whole FOREST occupies the
screen area that one BUSH occupies in a modern FF remake.  So a forest mass must
be built the way a good bush is built, not the way a tree is built:

  1. a CHUNKY MULTI-LOBED CORE, overlapping lobes merged into one mass, its
     interior dark and its crevices shaded (vertex colour);
  2. a DENSE SHELL of leaf-cluster ALPHA CARDS over the visible surface, angled
     outward along the surface normal, denser where the silhouette is;
  3. REAL MATERIAL RESPONSE — albedo + normal + alpha atlases, not flat colour.

The atlases come from tools/foliage_atlas.py.  This module is the geometry, and
it is deliberately map-agnostic: `Mass` knows about lobes and cards, callers know
about stands, corridors and clearings.

THE TWO TRAPS, both learned the hard way and both encoded here as clamps:

  * A CARD SEEN FLAT IS A FLAKE (finding: round-2 style H, and tree_c's fringe).
    The follow camera looks down at ~35 deg, so a card lying horizontally is seen
    face-on with nothing behind it and reads as a sticker.  "Along the surface
    normal" therefore CANNOT be taken literally at the top of a dome, where the
    normal is straight up.  `BETA_MAX` clamps how far a card may lie back from
    vertical, so the crown of a mass is shelled with steeply-pitched cards that
    still show their silhouette instead of their face.
  * AN INTERIOR FACE IS A SEAM.  Overlapping lobes that keep their buried faces
    read as a heap of separate balls the moment the light grazes them, because
    every intersection draws a crease.  `cull_interior()` deletes any face whose
    centre is inside another lobe, which is what turns the heap into one mass
    (and pays for the cards in triangles).
"""
import math
import os

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXO = os.path.join(ROOT, "tools/textures/overworld")

# ------------------------------------------------------------------ taste knobs
BETA_MAX = math.radians(56.0)     # max card lie-back from vertical (the H clamp)
BETA_JIT = math.radians(13.0)
SIL_BIAS = 0.42                   # 0 = cards only on silhouettes, 1 = uniform
CORE_UV = 3.6                     # world units per leafmass_tile repeat
CARD_SINK = 0.10                  # extra sink below the sample point
CARD_OUT = 0.16                   # card centre stands this far out along N
FUZZ_LOW = 0.34                   # below this n.z, prefer the small fuzz cards
CARD_LO = 0.55                    # darkest a shell card's COLOR_0 may go
GRID = 4                          # atlas grid (must match foliage_atlas.GRID)
N_BIG = 8                         # cells 0..7 big clumps, 8..15 edge fuzz


# ---------------------------------------------------------------- icosphere
_ICO = {}


def icosphere(subd):
    """Unit icosphere as (verts, faces) numpy arrays.  Cached per subdivision."""
    if subd in _ICO:
        return _ICO[subd]
    t = (1.0 + 5.0 ** 0.5) / 2.0
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
         (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9),
         (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2),
         (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    V = [tuple(np.array(v, float) / np.linalg.norm(v)) for v in V]
    for _ in range(subd):
        mid = {}
        nF = []

        def m(a, b):
            k = (min(a, b), max(a, b))
            if k not in mid:
                p = np.array(V[a]) + np.array(V[b])
                V.append(tuple(p / np.linalg.norm(p)))
                mid[k] = len(V) - 1
            return mid[k]

        for (a, b, c) in F:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            nF += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = nF
    out = (np.array(V, float), np.array(F, np.int64))
    _ICO[subd] = out
    return out


def _harm(n, ph, squash):
    """The lobe's radius as a function of direction.

    LOW-order terms only: a 162-vertex lobe cannot resolve a third harmonic, and
    smooth shading over sub-facet deformation is what made round 1's crowns read
    as cabbages.  The SILHOUETTE is what has to vary; leaf detail is the map's.
    """
    nx, ny, nz = n[..., 0], n[..., 1], n[..., 2]
    k = (1.0
         + 0.31 * np.sin(2.7 * nx + ph[0]) * np.sin(2.2 * ny + ph[1])
         + 0.17 * np.sin(3.9 * ny + ph[2]) * np.sin(3.3 * nz + ph[3])
         + 0.06 * np.sin(6.9 * nx + ph[4]) * np.sin(5.9 * nz + ph[5]))
    k = k - squash * np.maximum(nz, 0.0) ** 2      # a crown that met the sky
    k = k + 0.10 * np.maximum(-nz, 0.0)            # and hangs lower underneath
    return np.maximum(k, 0.55)


class Lobe:
    __slots__ = ("c", "s", "ph", "sq", "tone")

    def __init__(self, c, s, ph, sq, tone):
        self.c, self.s, self.ph, self.sq, self.tone = c, s, ph, sq, tone

    def inside(self, P, margin=0.97):
        d = (P - self.c[None, :]) / self.s[None, :]
        r = np.linalg.norm(d, axis=1)
        n = d / np.maximum(r, 1e-9)[:, None]
        return r < _harm(n, self.ph, self.sq) * margin


class Mass:
    """One vegetation mass: lobed core + card shell, both in numpy until finish."""

    def __init__(self, name):
        self.name = name
        self.lobes = []
        self.nv = 0            # accumulated CORE VERTEX count.  Not len(self.V):
        #                        that is the number of lobe blocks, and using it
        #                        as the face-index offset welds every lobe's
        #                        triangles onto the first few vertices — which
        #                        renders as a fan of huge plates and spikes and
        #                        looks like a sculpt bug, not an indexing one.
        self.V = []            # core verts, one array per lobe
        self.F = []            # core faces (triangles), indices into V
        self.VN = []           # core vertex normals (the sculpted sphere normal)
        self.VL = []           # which lobe each vert belongs to
        self.cV, self.cF, self.cUV, self.cC = [], [], [], []   # the cards
        self.ncv = 0           # accumulated CARD vertex count (same trap as nv)
        self.n_cards = 0

    # -------------------------------------------------------------- the core
    def lobe(self, cx, cy, cz, rx, ry, rz, subd=1, seed=0, squash=0.14, tone=1.0):
        U, Fc = icosphere(subd)
        rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
        ph = rng.rand(6) * 6.283
        k = _harm(U, ph, squash)
        s = np.array([rx, ry, rz], float)
        c = np.array([cx, cy, cz], float)
        P = U * k[:, None] * s[None, :] + c[None, :]
        base = self.nv
        self.nv += len(U)
        self.V.append(P)
        self.VN.append(U)                          # good enough: the sphere normal
        self.VL.append(np.full(len(U), len(self.lobes), np.int32))
        self.F.append(Fc + base)
        self.lobes.append(Lobe(c, s, ph, squash, tone))
        return len(self.lobes) - 1

    def cull_interior(self, margin=0.965):
        """Delete every face whose centre is buried in ANOTHER lobe.

        This is what merges the heap of lobes into one mass — and it is also the
        triangle budget for the card shell: on a well-overlapped stand it removes
        a third of the core.
        """
        V = np.concatenate(self.V)
        F = np.concatenate(self.F)
        VL = np.concatenate(self.VL)
        ctr = V[F].mean(axis=1)
        fl = VL[F[:, 0]]                           # the face's own lobe
        kill = np.zeros(len(F), bool)
        for j, lb in enumerate(self.lobes):
            cand = ~kill & (fl != j)
            if not cand.any():
                continue
            # cheap bbox reject before the harmonic test
            d = np.abs(ctr - lb.c[None, :]) - (lb.s * 1.35)[None, :]
            cand &= (d <= 0).all(axis=1)
            if not cand.any():
                continue
            idx = np.nonzero(cand)[0]
            kill[idx[lb.inside(ctr[idx], margin)]] = True
        self._V, self._F, self._VL = V, F[~kill], VL
        return int(kill.sum()), int(len(F))

    # ---------------------------------------------------------- the vcol pass
    def shade_core(self, deep=0.17, lift=0.33, crev=0.34, hue_jit=0.10, seed=3):
        """COLOR_0 for the core: dark interior, AO-ish depth, per-lobe hue.

        glTF multiplies baseColorTexture by COLOR_0, so this can only DARKEN —
        which is exactly right for a canopy, whose whole job is to be black
        underneath and lit on top.  Three terms:
          * up-facing lift    — the sky is the only big source at dusk;
          * crevice occlusion — how many other lobes are near this vertex;
          * per-lobe tone     — so the mass is not one flat green.
        """
        V, VL = self._V, self._VL
        N = np.concatenate(self.VN)
        rng = np.random.RandomState(seed)
        # crevice: distance to the nearest OTHER lobe's surface, in lobe radii
        occ = np.zeros(len(V))
        for j, lb in enumerate(self.lobes):
            d = (V - lb.c[None, :]) / lb.s[None, :]
            r = np.linalg.norm(d, axis=1)
            nn = d / np.maximum(r, 1e-9)[:, None]
            pen = _harm(nn, lb.ph, lb.sq) - r       # >0 inside, <0 outside
            m = VL != j
            occ[m] += np.clip(pen[m] + 0.30, 0.0, 0.65) / 0.65
        occ = np.clip(occ, 0.0, 2.2)
        up = np.clip(N[:, 2], -1.0, 1.0)
        shade = deep + lift * np.clip(up * 0.5 + 0.5, 0.0, 1.0) ** 1.6
        shade *= np.clip(1.0 - crev * occ, 0.22, 1.0)
        tone = np.array([lb.tone for lb in self.lobes])[VL]
        col = np.clip(shade * tone, 0.0, 1.0)[:, None] * np.ones((1, 3))
        # per-lobe hue: a shade of warmth either way, never a full hue swap
        jit = rng.uniform(-hue_jit, hue_jit, (len(self.lobes), 3))[VL]
        self._C = np.clip(col * (1.0 + jit * np.array([1.0, 0.35, -0.9])), 0.0, 1.0)
        self._shade = shade
        return self._C

    # ---------------------------------------------------------- the card shell
    def shell(self, rng, density=0.85, big=(1.55, 2.35), fuzz=(0.70, 1.15),
              fuzz_frac=0.30, beta_max=BETA_MAX, sil_bias=SIL_BIAS,
              hi_lift=1.10, cell_pick=None):
        """Scatter cards over the SURVIVING core faces, area-weighted.

        `density` is cards per square world unit of visible core surface, which
        is the one number the user is taste-gating: three of these are what the
        line-up compares.
        """
        V, F = self._V, self._F
        if not len(F):
            return 0
        A = V[F]
        e1, e2 = A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]
        cr = np.cross(e1, e2)
        area = 0.5 * np.linalg.norm(cr, axis=1)
        nrm = cr / np.maximum(np.linalg.norm(cr, axis=1), 1e-12)[:, None]
        # a face whose normal points down is under the mass: nothing to see
        keep = nrm[:, 2] > -0.45
        if not keep.any():
            return 0
        area, nrm, A = area[keep], nrm[keep], A[keep]
        fidx = np.nonzero(keep)[0]
        # DENSER ON SILHOUETTES: from a 35 deg camera the silhouette is where the
        # surface turns away, i.e. where the normal is nearly horizontal
        w = area * (sil_bias + (1.0 - sil_bias) * (1.0 - np.clip(nrm[:, 2], 0, 1)))
        n_want = int(density * float(area.sum()))
        if n_want <= 0:
            return 0
        p = w / w.sum()
        pick = rng.choice(len(area), size=n_want, p=p)
        b = rng.rand(n_want, 2)
        flip = b.sum(1) > 1.0
        b[flip] = 1.0 - b[flip]
        P = A[pick, 0] + b[:, :1] * (A[pick, 1] - A[pick, 0]) \
            + b[:, 1:] * (A[pick, 2] - A[pick, 0])
        N = nrm[pick]
        shade = self._shade[self._F[fidx[pick]]].mean(axis=1) if hasattr(self, "_shade") \
            else np.ones(n_want)
        nz = np.clip(N[:, 2], -1.0, 1.0)
        # --- the angle distribution, i.e. the whole H lesson ------------------
        beta = np.minimum(np.arcsin(np.clip(nz, 0.0, 1.0)), beta_max)
        beta = np.clip(beta + rng.uniform(-BETA_JIT, BETA_JIT, n_want),
                       math.radians(6.0), math.radians(74.0))
        az = np.arctan2(N[:, 1], N[:, 0])
        yaw = az + math.pi / 2.0 + rng.uniform(-0.30, 0.30, n_want)
        is_fuzz = (rng.rand(n_want) < fuzz_frac + 0.30 * (nz < FUZZ_LOW))
        sz = np.where(is_fuzz, rng.uniform(fuzz[0], fuzz[1], n_want),
                      rng.uniform(big[0], big[1], n_want))
        cell = np.where(is_fuzz, N_BIG + rng.randint(0, GRID * GRID - N_BIG, n_want),
                        rng.randint(0, N_BIG, n_want))
        if cell_pick is not None:
            cell = cell_pick(cell, is_fuzz, rng)
        # The shell's COLOR_0 is RELATIVE, normalised against the core's own
        # brightest vertex — and this line is the one the glTF round trip caught.
        # Reading the core's ABSOLUTE shade meant that darkening the core (which
        # region masses want, so their gaps read as canopy shadow) pushed every
        # single card onto the clamp floor: the export came back with COLOR_0
        # min == max == 0.521 on 28 000 cards, so the shell AO was doing nothing
        # AND was multiplying the whole atlas by a flat half.  That is where the
        # persistent murkiness came from, and no amount of re-lighting the atlas
        # would have fixed it.  Normalised, the shell spans CARD_LO..1.0 whatever
        # the core is set to.
        rel = shade / max(float(self._shade.max()), 1e-6)
        col = np.clip(CARD_LO + (1.0 - CARD_LO) * rel * hi_lift
                      * (0.86 + 0.28 * np.clip(nz, 0, 1)), CARD_LO, 1.0)
        # PUSH THE SHELL OUT past the core.  With the cards' bases sitting ON the
        # surface the core stayed the silhouette and the mass read as mossy
        # boulders with leaves along the top: half of every card was inside the
        # thing it was supposed to hide.  Standing each card's CENTRE a little
        # outside the surface makes the shell the volume and demotes the core to
        # what it should be — the dark interior nothing can see through.
        base = P + N * (sz * CARD_OUT)[:, None]
        self._emit_cards(base, yaw, beta, sz, cell, col, rng)
        self.n_cards += n_want
        return n_want

    def _emit_cards(self, P, yaw, beta, sz, cell, col, rng):
        n = len(P)
        cw, sw = np.cos(yaw), np.sin(yaw)
        cb, sb = np.cos(beta), np.sin(beta)
        # right = (cos yaw, sin yaw, 0); up leans back by beta, so the quad's own
        # plane normal is (cos az * sin beta ... ) with elevation sin(beta)
        R = np.stack([cw, sw, np.zeros(n)], -1)
        U = np.stack([-sw * sb, cw * sb, cb], -1)
        w = (sz * 0.5)[:, None]
        h = sz[:, None]
        # the card straddles its sample point instead of standing on it, so a
        # shell over a vertical flank covers the flank instead of only its upper
        # half (which is what left bare core showing between the clumps)
        o = P - U * (h * (0.5 + CARD_SINK))
        quad = np.stack([o - R * w, o + R * w, o + R * w + U * h, o - R * w + U * h], 1)
        b0 = self.ncv
        self.ncv += n * 4
        self.cV.append(quad.reshape(-1, 3))
        f = b0 + np.arange(n)[:, None] * 4 + np.array([0, 1, 2, 3])[None, :]
        self.cF.append(f)
        gx, gy = cell % GRID, cell // GRID
        u0 = gx / GRID
        v0 = 1.0 - (gy + 1) / GRID                 # cell 0 is the atlas TOP-left
        v1 = v0 + 1.0 / GRID
        # MIRROR half the cards in u: 16 cells shelled over a whole region would
        # otherwise repeat visibly, and a flip is free
        mir = rng.rand(n) < 0.5
        ua = np.where(mir, u0, u0 + 1.0 / GRID)
        ub = np.where(mir, u0 + 1.0 / GRID, u0)
        uv = np.stack([np.stack([ua, v0], -1), np.stack([ub, v0], -1),
                       np.stack([ub, v1], -1), np.stack([ua, v1], -1)], 1)
        self.cUV.append(uv)
        self.cC.append(np.repeat(col[:, None] * np.ones((1, 3)), 4, axis=0))

    # ------------------------------------------------------------------ output
    def finish(self, coll, core_mat, card_mat, uv_scale=CORE_UV):
        if not hasattr(self, "_C"):
            raise RuntimeError("call cull_interior() then shade_core() before finish()")
        out = {}
        if len(self._F):
            out["core"] = self._mesh_core(coll, core_mat, uv_scale)
        if self.cV:
            out["cards"] = self._mesh_cards(coll, card_mat)
        return out

    def _mesh_core(self, coll, mat, uv_scale):
        V, F, C = self._V, self._F, self._C
        used, inv = np.unique(F, return_inverse=True)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([tuple(v) for v in V[used]], [],
                       [tuple(t) for t in inv.reshape(F.shape)])
        # triplanar-ish planar UVs, axis chosen per face by its dominant normal
        uvl = me.uv_layers.new(name="UVMap")
        P = V[used]
        loops = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops)
        fn = np.zeros(len(me.polygons) * 3)
        me.polygons.foreach_get("normal", fn)
        fn = fn.reshape(-1, 3)
        ax = np.argmax(np.abs(fn), axis=1)
        pl = np.repeat(ax, 3)                       # tris: 3 loops per face
        pv = P[loops]
        u = np.where(pl == 0, pv[:, 1], pv[:, 0])
        v = np.where(pl == 2, pv[:, 1], pv[:, 2])
        uv = np.stack([u, v], -1) / uv_scale
        uvl.data.foreach_set("uv", uv.ravel())
        ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
        d = np.ones((len(used), 4))
        d[:, :3] = C[used]
        ca.data.foreach_set("color", d.ravel())
        me.materials.append(mat)
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        return ob

    def _mesh_cards(self, coll, mat):
        V = np.concatenate(self.cV)
        F = np.concatenate(self.cF)
        UV = np.concatenate(self.cUV)
        C = np.concatenate(self.cC)
        me = bpy.data.meshes.new(self.name + "_cards")
        me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", UV.reshape(-1, 2).ravel())
        ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
        d = np.ones((len(V), 4))
        d[:, :3] = C
        ca.data.foreach_set("color", d.ravel())
        me.materials.append(mat)
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(self.name + "_cards", me)
        coll.objects.link(ob)
        return ob


# ---------------------------------------------------------------------------
# ONE BUSH — the line-up's exhibit and the unit the forest masses are made of
# ---------------------------------------------------------------------------
def bush(M, rng, x, y, z, r, h, nlobe=5, tone=1.0, squash=0.16):
    """A chunky multi-lobed core: one dominant lobe plus satellites.

    The satellites sit at 0.40-0.70 r and are DELIBERATELY unequal — a ring of
    equal lobes is a flower, and a single lobe is round 1's rejected blob.
    """
    ids = [M.lobe(x, y, z + h * 0.50, r, r * rng.uniform(0.88, 1.06), h * 0.55,
                  subd=2, seed=rng.randint(1 << 28), squash=squash,
                  tone=tone * rng.uniform(0.94, 1.06))]
    a0 = rng.uniform(0, 6.283)
    for k in range(nlobe - 1):
        a = a0 + k * (6.283 / (nlobe - 1)) + rng.uniform(-0.45, 0.45)
        # PUSHED OUT far enough to break the silhouette.  The first pass put the
        # satellites at 0.40-0.72 r with radius 0.42-0.70 r, which buries them
        # entirely inside the dominant lobe: cull_interior then deleted 100% of
        # their faces and the "multi-lobed" core was one plain ellipsoid.
        d = r * rng.uniform(0.62, 0.98)
        rr = r * rng.uniform(0.46, 0.76)
        ids.append(M.lobe(x + math.cos(a) * d, y + math.sin(a) * d,
                          z + h * rng.uniform(0.30, 0.62),
                          rr, rr * rng.uniform(0.85, 1.12), h * rng.uniform(0.28, 0.48),
                          subd=2 if rr > r * 0.5 else 1, seed=rng.randint(1 << 28),
                          squash=squash * rng.uniform(0.6, 1.4),
                          tone=tone * rng.uniform(0.88, 1.10)))
    return ids


# ---------------------------------------------------------------------------
def materials(atlas_png, atlas_nor, tile_jpg, tile_nor, suffix="valley",
             pbr_mat=None):
    """The two exportable materials.  `gain_to=0.0` on purpose: the atlases carry
    their own baked light at a chosen level, so COLOR_0 must be a plain multiply
    (gain 1.0) and not the class-colour pre-division the prop materials need."""
    if pbr_mat is None:
        import overworld2_build as B2
        pbr_mat = B2.pbr_mat
    core = bpy.data.materials.get("ow_%s_bushcore" % suffix)
    card = bpy.data.materials.get("ow_%s_bushcard" % suffix)
    if core is None:
        core = pbr_mat("ow_%s_bushcore" % suffix, tile_jpg, tile_nor, None,
                       tile=1.0, vcol=True, gain_to=0.0, rough_default=0.93)
    if card is None:
        card = pbr_mat("ow_%s_bushcard" % suffix, atlas_png, atlas_nor, None,
                       tile=1.0, vcol=True, gain_to=0.0, alpha_clip=True,
                       twosided=True, rough_default=0.95)
    return core, card
