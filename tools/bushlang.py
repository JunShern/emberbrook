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
BETA_MAX = math.radians(46.0)     # max card lie-back from vertical (the H clamp)
BETA_JIT = math.radians(13.0)
SIL_BIAS = 0.42                   # 0 = cards only on silhouettes, 1 = uniform
# CORE_UV — 3.6 -> 2.1.  `_mesh_core` projects PLANAR UVs with the axis chosen by
# each face's dominant normal, which does compress on faces near 45 degrees, and a
# shorter repeat makes that smear fine rather than coarse.
#
# THIS COMMENT USED TO BLAME THE PALE CROWN STREAKS ON THAT PROJECTION.  IT WAS
# WRONG, AND BEING WRITTEN DOWN IT COST ANOTHER LANE A DIAGNOSTIC HOUR — the
# documentation bar's own warning about interpretations carrying authority, paid in
# full.  MEASURED (round 2, ow_multi at the meadow camera, postfx off):
#   * hide the CORE and the streaks are unchanged; hide the CARDS and they are GONE.
#     The core is not drawing them.
#   * per-triangle UV anisotropy out of the shipped GLB (SVD of d(uv)/d(world)):
#     core median 1.14, max 1.70; cards exactly 1.000.  Dominant-axis planar
#     projection is bounded at sqrt(3) = 1.732 BY CONSTRUCTION, so "one texel
#     smeared across the face" cannot happen here at all.
#   * LinearFilter and anisotropy 16 (default 1) both leave the streaks unchanged,
#     which excludes filtering.
#   * culling cards with |N.view| < 0.45 removes 14 283 of 33 333 and most of the
#     streaks; a streak measures 85-130 px, which is one BIG card (1.55-2.35 u at
#     ~55 px/u).
# THE STREAKS ARE BIG SHELL CARDS SEEN NEAR EDGE-ON.  `beta` lays crown-top cards
# back to within BETA_MAX of horizontal; against a 35-degree-down camera half the
# azimuths at that pitch go edge-on, and NZ_HI makes those same up-facing cards the
# BRIGHTEST in the mass — so the slivers read pale over a darker crown.  The knobs
# that own it are BETA_MAX (line above), the beta clamp in `shell`, and NZ_HI.
CORE_UV = 2.1                     # world units per leafmass_tile repeat
CARD_SINK = 0.10                  # extra sink below the sample point
CARD_OUT = 0.16                   # card centre stands this far out along N
FUZZ_LOW = 0.34                   # below this n.z, prefer the small fuzz cards
CARD_LO = 0.34                    # darkest a shell card's COLOR_0 may go
GRID = 4                          # atlas grid (must match foliage_atlas.GRID)
N_BIG = 8                         # cells 0..7 big clumps, 8..15 edge fuzz
# ------------------------------------------------------- the RIM tier (charge 3)
# "The outline is made of QUADS, not of leaves — cards too large relative to the
# crown."  Measured on the shipped meadow frame: the hero crown is ~10 world units
# across at ~55 px/u, and a BIG card is 1.55-2.45 u, so one card is 85-135 px of a
# 550 px crown.  Nothing inside a card can rescue that; the notches in the
# silhouette ARE the quads.
#
# The answer is NOT to shrink every card — a card is also the only thing holding
# the mass opaque, and at a quarter of the area it takes four times as many to do
# it (12 000 cards to 48 000, and the tri budget says no).  It is a SECOND TIER:
# the mass keeps its big cards, and the silhouette — which is a thin band, a
# per-face property the shell already computes for its density weight — gets its
# own scatter of small ones, thrown OUT past the hull with a length jitter so the
# boundary is ragged at leaf-cluster scale.  Cost is proportional to the rim, not
# to the volume.
RIM_NZ = 0.42                     # a face silhouettes when its normal.z is under this
RIM_DENSITY = 5.6                 # rim cards per square unit of rim face
RIM_SIZE = (0.28, 0.58)           # ... and they are a QUARTER of a big card
RIM_OUT = (0.10, 0.85)            # how far past the surface, in card sizes
RIM_DIM = 0.88                    # the ragged edge is not the highlight
BASE_DARK = 0.36                  # COLOR_0 at the very bottom of a lobe
BASE_POW = 1.15
# HI_LIFT — the shell's CEILING, and it was cut 1.10 -> 0.80 the moment the card
# art stopped carrying its own 5x value range.  Measured on the hero crown:
# flattening the atlas alone took the frame from V50 0.464 / 13.7% of pixels over
# V 0.72 to V50 0.612 / 35.1% over, against references that run V50 0.43-0.54 and
# 1-3% over.  THE MASS DID NOT GET BRIGHTER, IT LOST ITS DARK HALF — the atlas's
# own mean is 0.262 against the old 0.263, and its p99 fell 0.702 -> 0.535.  A
# median rises when you delete the pixels below it.  So the value that used to
# live inside every card has to reappear at crown scale or not at all, and this
# and BASE_DARK are where it reappears.
HI_LIFT = 0.80
# NZ_HI 0.42 -> 0.22, BETA_MAX 56 -> 46 deg: THE PALE STREAKS.  These are the two
# knobs the streak diagnosis named (see the CORE_UV block).  A big card laid back
# near BETA_MAX goes edge-on for half its azimuths against the 35-degree-down
# camera, and NZ_HI made exactly those up-facing cards the BRIGHTEST thing in the
# mass — so every grazing sliver read pale over a darker crown.  That is also,
# word for word, the blind critic's "the canopy's brightest pixels are scattered":
# the streaks were half of charge 1, and no amount of crown-scale gradient can
# read through a field of bright slivers scattered across it.
NZ_LO, NZ_HI = 0.72, 0.22         # side-facing cards darker than up-facing ones
# ------------------------------------------------ THE TWIST (round 3, the streaks)
# ROUND 2 DIAGNOSED THE PALE STREAKS AND THEN TRIMMED TWO LEVELS AT THEM (BETA_MAX
# 56 -> 46, NZ_HI 0.42 -> 0.22).  That helped and it could not finish, because the
# diagnosis was STRUCTURAL and the answer was tonal: a streak is a BIG CARD SEEN
# NEAR EDGE-ON, and dimming an edge-on card leaves an edge-on card.  Round 2's own
# census: culling `|N.view| < 0.45` removed 14 283 of 33 333 cards on one frame, so
# this is not a rare azimuth — a shell aims its cards along the surface normal in
# every direction, so from ANY view about two fifths of a dome's cards are within
# 27 degrees of edge-on, and a 1.55-2.35 u quad seen that way is an 85-130 px
# SLIVER.  There is no scatter knob for that; there is no level for it either.
#
# A DOT-PRODUCT FADE IS THE STANDARD ANSWER AND IT IS NOT THIS LANE'S FILE — it is a
# draw-time term in the shared foliage shader (public/js/ow_detail.js, the grass
# lane's).  What IS in this file is the reason the sliver exists: THE CARD IS FLAT.
# So the corners are displaced along the card's own normal, +d on one diagonal and
# -d on the other — a propeller twist.  The quad's two triangles come out
# non-coplanar, tilted about +-atan(2 CARD_TWIST) from the card plane, so the
# projected area at the worst azimuth goes from ~0 to sin(that), and the card
# degrades into a small clump instead of a bright line.
#
# THE PROPERTY THAT MADE THIS THE CHOICE OVER A FOLD OR A CROSS: IT IS FREE.  A
# V-fold needs a centre seam (4 tris for 2) and a cross needs a second quad; both
# are +2 tris on every card in the region, which is +18% of the tile for a
# silhouette artefact.  A twist moves four vertices that already exist.
CARD_TWIST = 0.18                 # corner displacement along N, in card half-widths
# ------------------------------------------ THE SHELL NORMAL (round 3, the streaks)
# AND THE TWIST ALONE DID NOT PAY — measured, built, photographed: at 0.24 the thin
# bright slivers became BROAD SOFT SMEARS and the mass went hazier.  Widening a
# sliver is not removing it, because the sliver was never bright BECAUSE it was
# thin.  It was bright because A CARD CARRIES ITS OWN PLANE NORMAL: `_emit_cards`
# writes a flat quad and nothing ever replaced its normal, so a card laid back by
# `beta` over a lobe whose surface faces somewhere else takes a DIFFERENT lambert
# from every neighbour it sits between.  33 000 cards, each shading as its own
# little plane, is the mechanical statement of the blind critic's "the canopy's
# brightest pixels are scattered" — and no crown-scale gradient can read through it.
#
# So the card's normal is REPLACED by the core surface normal it was scattered from
# (the standard foliage normal transfer).  The shell then shades as the VOLUME it
# is a shell of, the mass gets its lit side and its shaded side back at lobe scale,
# and an edge-on card takes the same light as the crown behind it instead of
# announcing itself.  It costs nothing: the normals are already computed in `shell`
# and `_rim`, and custom split normals are what glTF's NORMAL accessor carries.
#
# NOT 1.0.  At a full transfer every card in a lobe is exactly one value and the
# crown flattens into a shaded ball; the residual plane term is what keeps leaf
# clusters reading as clusters.  With the normals transferred the TWIST is no
# longer a shading term at all — it only moves the silhouette — which is why the
# two ship together and why the twist could come down.
CARD_NRM = 0.82                   # share of the core surface normal in a card's own

# ------------------------------------------------------- THE SUN (round 2, charge 1)
# "Texture without form.  The house shadows say the sun is upper-right, yet the
# canopy's brightest pixels are scattered, so NO LOBE IS LIT AND NO LOBE IS SHADED."
#
# The blind critic is describing an absence, and it was an absence at the wire, not a
# level that wanted sweeping: EVERY crown-scale term in this module was a function of
# WORLD UP and nothing else.  `shade_core` read `up = N[:,2]`; `_colour` read
# `nz = N[:,2]` and `_lobe_height`, which is a Z gradient by construction.  A lobe on
# the sun side and a lobe on the shade side of the same mass therefore got IDENTICAL
# colour, at every scale.  That is not a gradient that is too weak to see — there was
# no lateral gradient to see.  (Same class as round 1's `hz = h*0.62`: check the wire
# before sweeping the knob.)
#
# SUN_TO is the direction TOWARD the sun, derived from the towns' own ratified rig —
# Blender euler (56, 0, 212) on a lamp that points down -Z (valley_build.py:791):
#     Rz(212) @ Rx(56) @ (0,0,-1) = (0.439, -0.703, -0.559)   [light travel]
#     toward the sun = -that = (-0.439, 0.703, 0.559),  elevation asin(0.559) = 34 deg,
# which is the 34-degree sun every shadow-length note in valley_build is written
# against.  DERIVED, NOT TYPED: change the rig and this must be re-derived with it.
#
# TWO SCALES, because the charge is about both and they are different mechanisms:
#   * SUN_N   — the LOCAL surface normal against the sun.  This is per-lobe form:
#               the side of a lobe that faces the sun lifts, the side away falls.
#   * SUN_AX  — position along the sun axis across the WHOLE MASS, normalised over
#               the mass's own extent.  This is the crown-scale gradient the critic
#               asked for in so many words ("as a gradient across the whole mass"),
#               and it is the one a distant crown can actually resolve, because at
#               60 m the per-lobe normals average out and only the mass-wide ramp
#               survives.
# THE SKY TERM STAYS.  Up-facing still lifts (the sky is a real source and the whole
# module's dark-underside logic hangs off it); the sun terms take a SHARE of the
# existing lift rather than stacking on it, so the mean is held and only the
# DISTRIBUTION changes.  SUN_SHARE is that split.
SUN_TO = np.array([-0.4393, 0.7030, 0.5592])
SUN_TO = SUN_TO / np.linalg.norm(SUN_TO)
SUN_SHARE = 0.55                  # of the lift, how much is sun vs sky (0 = old wire)
SUN_AX_MIX = 0.45                 # within the sun term, crown-scale vs local-normal
SUN_FLOOR = 0.30                  # the shade side never goes to zero: it is sky-lit


def _sun_term(N, P, centre=None, extent=None):
    """The sun's share of the lift, in 0..1, at two scales blended by SUN_AX_MIX.

    `N` is the surface normal per point; `P` the world position.  When `centre`/
    `extent` are given the crown-scale ramp is included — callers that have no mass
    extent (a single loose card) get the local term alone rather than a wrong ramp.
    """
    loc = np.clip(N @ SUN_TO, -1.0, 1.0) * 0.5 + 0.5          # 0 away .. 1 facing
    if centre is None or extent is None or extent <= 1e-6:
        t = loc
    else:
        ax = ((P - centre[None, :]) @ SUN_TO) / extent         # -0.5 .. +0.5
        ax = np.clip(ax + 0.5, 0.0, 1.0)
        t = (1.0 - SUN_AX_MIX) * loc + SUN_AX_MIX * ax
    return SUN_FLOOR + (1.0 - SUN_FLOOR) * t


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

    def __init__(self, name, sun_scope="mass"):
        self.name = name
        # SUN_SCOPE — "mass" or "local", and it is a correctness flag, not taste.
        # The crown-scale ramp normalises over THE MASS'S OWN EXTENT, which is
        # right for one forest mass and WRONG the moment a Mass is a container for
        # many separate plants: a tile-wide bush batch would get a tile-wide
        # gradient, i.e. bushes on the west of the map darker than bushes on the
        # east, which is not a form cue but a bug that looks like vignetting.
        # "local" drops the ramp and keeps the per-normal sun term, which is
        # scale-free and is what a 1 m bush reads by anyway.
        self.sun_scope = sun_scope
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
        self.cN = []           # ... and their TRANSFERRED normals (see CARD_NRM)
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

    def _sun_axis(self):
        """The mass's centre and its own extent ALONG THE SUN AXIS.

        Normalising the crown-scale ramp by the mass's extent (rather than by a
        world constant) is what makes one gradient work for a 2 m bush and a 40 m
        forest mass: both get the full ramp across themselves.
        """
        V = self._V if getattr(self, "_V", None) is not None else np.concatenate(self.V)
        if not len(V):
            return None, None
        t = V @ SUN_TO
        return V.mean(axis=0), float(t.max() - t.min())

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
        sky = np.clip(up * 0.5 + 0.5, 0.0, 1.0) ** 1.6
        # THE LIFT IS SPLIT, NOT STACKED (see the SUN_* block): the sky keeps
        # (1 - SUN_SHARE) of it and the sun takes the rest, so the mass's mean
        # COLOR_0 is held and what changes is WHICH SIDE of it is bright.
        self._sun_c, self._sun_e = self._sun_axis() \
            if self.sun_scope == "mass" else (None, None)
        sun = _sun_term(N, V, self._sun_c, self._sun_e)
        shade = deep + lift * ((1.0 - SUN_SHARE) * sky + SUN_SHARE * sun)
        shade *= np.clip(1.0 - crev * occ, 0.22, 1.0)
        tone = np.array([lb.tone for lb in self.lobes])[VL]
        col = np.clip(shade * tone, 0.0, 1.0)[:, None] * np.ones((1, 3))
        # per-lobe hue: a shade of warmth either way, never a full hue swap
        jit = rng.uniform(-hue_jit, hue_jit, (len(self.lobes), 3))[VL]
        self._C = np.clip(col * (1.0 + jit * np.array([1.0, 0.35, -0.9])), 0.0, 1.0)
        self._shade = shade
        return self._C

    # ---------------------------------------------------------- the card shell
    def _lobe_height(self, P):
        """Each point's height WITHIN ITS OWN LOBE, 0 at the lobe's floor and 1 at
        its crown.  Local on purpose: a stand lies on a hillside, so a height
        normalised over the whole mass measures the HILL and darkens the downhill
        end of a level crown.  The nearest lobe is taken in the lobe's own scaled
        space, which is the same metric `Lobe.inside` uses.
        """
        if not self.lobes:
            return np.full(len(P), 0.5)
        d2 = np.stack([np.linalg.norm((P - lb.c[None, :]) / lb.s[None, :], axis=1)
                       for lb in self.lobes], 1)
        j = d2.argmin(1)
        cz = np.array([lb.c[2] for lb in self.lobes])[j]
        sz = np.maximum(np.array([lb.s[2] for lb in self.lobes])[j], 1e-6)
        return np.clip((P[:, 2] - (cz - sz)) / (2.0 * sz), 0.0, 1.0)

    def _faces(self):
        """Surviving core faces as (area, normal, triangle) with the undersides
        dropped — shared by the mass scatter and the rim scatter."""
        V, F = self._V, self._F
        A = V[F]
        cr = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0])
        ln = np.linalg.norm(cr, axis=1)
        nrm = cr / np.maximum(ln, 1e-12)[:, None]
        keep = nrm[:, 2] > -0.45      # pointing down is under the mass: nothing to see
        return 0.5 * ln[keep], nrm[keep], A[keep], np.nonzero(keep)[0]

    def _sample(self, A, rng, n):
        b = rng.rand(n, 2)
        flip = b.sum(1) > 1.0
        b[flip] = 1.0 - b[flip]
        return A[:, 0] + b[:, :1] * (A[:, 1] - A[:, 0]) + b[:, 1:] * (A[:, 2] - A[:, 0])

    def _colour(self, shade, N, P, hi_lift):
        """COLOR_0 for a batch of cards.

        The shell's COLOR_0 is RELATIVE, normalised against the core's own
        brightest vertex — and this line is the one the glTF round trip caught.
        Reading the core's ABSOLUTE shade meant that darkening the core (which
        region masses want, so their gaps read as canopy shadow) pushed every
        single card onto the clamp floor: the export came back with COLOR_0
        min == max == 0.521 on 28 000 cards, so the shell AO was doing nothing
        AND was multiplying the whole atlas by a flat half.  That is where the
        persistent murkiness came from, and no amount of re-lighting the atlas
        would have fixed it.  Normalised, the shell spans CARD_LO..1.0 whatever
        the core is set to.

        THE BASE TERM IS THE VOLUME, and it moved here from the card art.  The
        references' masses are *"a lit crown on top, a hard falloff into an
        occluded dark underside, and the darkest value at the BASE where they
        meet ground"* — that is a CROWN-SCALE gradient.  Baking it into every
        card's own texture (which is what foliage_atlas's first light rig did,
        spanning 5.1x inside one card) gives every card a lit top and a dark
        bottom of its own, i.e. a field of little spheres — charge 1's
        cauliflower, from the other end.  One gradient, at the scale of the
        thing that actually has a top and a bottom.
        """
        rel = shade / max(float(self._shade.max()), 1e-6)
        base = BASE_DARK + (1.0 - BASE_DARK) * self._lobe_height(P) ** BASE_POW
        # THE CARDS CARRY THE SUN TOO, and they matter more than the core does:
        # the shell is 66.5% of the hero crop against the core's 26.8%, so a sun
        # gradient applied to the core alone would be a gradient nobody sees.
        # `nz` (world up) keeps its job of separating up-facing from side-facing
        # cards; the sun term is a SEPARATE multiplier, normalised to average 1.0
        # over a full sphere of normals so it redistributes rather than dims.
        nz = np.clip(N[:, 2], -1.0, 1.0)
        sun = _sun_term(N, P, getattr(self, "_sun_c", None),
                        getattr(self, "_sun_e", None))
        sunm = 1.0 + SUN_SHARE * (sun - (SUN_FLOOR + (1.0 - SUN_FLOOR) * 0.5)) * 2.0
        return np.clip(CARD_LO + (1.0 - CARD_LO) * rel * hi_lift * base
                       * (NZ_LO + NZ_HI * np.clip(nz, 0, 1)) * sunm, CARD_LO, 1.0)

    def shell(self, rng, density=0.85, big=(1.55, 2.35), fuzz=(0.70, 1.15),
              fuzz_frac=0.30, beta_max=BETA_MAX, sil_bias=SIL_BIAS,
              hi_lift=HI_LIFT, cell_pick=None, rim_density=RIM_DENSITY,
              rim_size=RIM_SIZE):
        """Scatter cards over the SURVIVING core faces, area-weighted.

        `density` is cards per square world unit of visible core surface, which
        is the one number the user is taste-gating: three of these are what the
        line-up compares.  `rim_density` is the same number for the SECOND tier,
        the small silhouette-breakers — see the RIM_* block at the top.
        """
        if not len(self._F):
            return 0
        area, nrm, A, fidx = self._faces()
        if not len(area):
            return 0
        # DENSER ON SILHOUETTES: from a 35 deg camera the silhouette is where the
        # surface turns away, i.e. where the normal is nearly horizontal
        w = area * (sil_bias + (1.0 - sil_bias) * (1.0 - np.clip(nrm[:, 2], 0, 1)))
        n_want = int(density * float(area.sum()))
        if n_want <= 0:
            return 0
        pick = rng.choice(len(area), size=n_want, p=w / w.sum())
        P = self._sample(A[pick], rng, n_want)
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
        col = self._colour(shade, N, P, hi_lift)
        # PUSH THE SHELL OUT past the core.  With the cards' bases sitting ON the
        # surface the core stayed the silhouette and the mass read as mossy
        # boulders with leaves along the top: half of every card was inside the
        # thing it was supposed to hide.  Standing each card's CENTRE a little
        # outside the surface makes the shell the volume and demotes the core to
        # what it should be — the dark interior nothing can see through.
        self._emit_cards(P + N * (sz * CARD_OUT)[:, None], yaw, beta, sz, cell,
                         col, rng, N)
        self.n_cards += n_want
        n_rim = self._rim(rng, area, nrm, A, fidx, rim_density, rim_size,
                          beta_max, hi_lift)
        self.n_cards += n_rim
        return n_want + n_rim

    def _rim(self, rng, area, nrm, A, fidx, density, size, beta_max, hi_lift):
        """The SECOND tier: small cards along the silhouette band, thrown out past
        the hull by a jittered distance so the boundary is ragged at leaf scale.

        `RIM_OUT` is the whole point and it is a RANGE, not a constant: cards all
        pushed out by the same amount give a smooth offset surface, which is
        another hull with another clean edge.  It is the SPREAD of the throw that
        makes leaf clusters stick out past the mass the way the references' do.
        Cells are drawn from the edge-fuzz half of the atlas only (open, few
        sprays, much sky) — a near-filled big clump used as a silhouette breaker
        just moves the same solid edge outwards.
        """
        sil = np.clip((RIM_NZ - nrm[:, 2]) / RIM_NZ, 0.0, 1.0)
        w = area * sil
        tot = float(w.sum())
        n = int(density * tot)
        if n <= 0 or tot <= 0:
            return 0
        pick = rng.choice(len(area), size=n, p=w / tot)
        P = self._sample(A[pick], rng, n)
        N = nrm[pick]
        nz = np.clip(N[:, 2], -1.0, 1.0)
        shade = self._shade[self._F[fidx[pick]]].mean(axis=1) if hasattr(self, "_shade") \
            else np.ones(n)
        sz = rng.uniform(size[0], size[1], n)
        # steeper than the mass tier: a rim card is seen against the sky, and a
        # card lying back at the silhouette shows its face (the H lesson again)
        beta = np.clip(np.minimum(np.arcsin(np.abs(nz)), beta_max) * 0.55
                       + rng.uniform(-BETA_JIT, BETA_JIT, n),
                       math.radians(4.0), math.radians(58.0))
        yaw = np.arctan2(N[:, 1], N[:, 0]) + math.pi / 2.0 + rng.uniform(-0.5, 0.5, n)
        out = rng.uniform(RIM_OUT[0], RIM_OUT[1], n) ** 1.5
        base = P + N * (sz * (CARD_OUT + out))[:, None]
        base[:, 2] += sz * rng.uniform(-0.30, 0.22, n)
        cell = N_BIG + rng.randint(0, GRID * GRID - N_BIG, n)
        # COLOUR FROM THE SURFACE POINT, NOT FROM THE THROWN POSITION.  `base` is
        # up to 0.85 card-sizes outside the hull, so feeding it to the height term
        # clipped every rim card to the top of its lobe and made the ragged edge
        # the BRIGHTEST thing in the crown — the opposite of a silhouette.  P is
        # where the card belongs to the mass; the throw is only where it reaches.
        self._emit_cards(base, yaw, beta, sz, cell,
                         self._colour(shade, N, P, hi_lift) * RIM_DIM, rng, N)
        return n

    def _emit_cards(self, P, yaw, beta, sz, cell, col, rng, SN=None):
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
        # THE TWIST (see CARD_TWIST).  N = R x U is the card's own plane normal;
        # corners 0 and 2 go out along it and 1 and 3 go in, which is a saddle, so
        # the quad's two triangles stop being coplanar and the card stops having an
        # orientation at which it disappears.  The sign flips per card so the shell
        # does not acquire one shared handedness at grazing angles.
        if CARD_TWIST > 0:
            Nc = np.cross(R, U)
            d = (Nc * (w * CARD_TWIST)) * np.where(rng.rand(n) < 0.5, -1.0, 1.0)[:, None]
            quad = quad + d[:, None, :] * np.array([1.0, -1.0, 1.0, -1.0])[None, :, None]
        b0 = self.ncv
        self.ncv += n * 4
        self.cV.append(quad.reshape(-1, 3))
        f = b0 + np.arange(n)[:, None] * 4 + np.array([0, 1, 2, 3])[None, :]
        self.cF.append(f)
        # THE SHELL NORMAL (see CARD_NRM).  The card's plane normal is mixed toward
        # the CORE surface normal it was scattered from, and the result is written
        # as a custom split normal in `_mesh_cards` — otherwise every quad shades as
        # its own plane and the crown has 33 000 independent lambert terms in it.
        Nq = np.cross(R, U)
        if SN is not None and CARD_NRM > 0:
            Nq = Nq * (1.0 - CARD_NRM) + SN * CARD_NRM
        Nq = Nq / np.maximum(np.linalg.norm(Nq, axis=1, keepdims=True), 1e-9)
        self.cN.append(np.repeat(Nq, 4, axis=0))
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
        # THE TRANSFERRED NORMALS.  A card is its own four verts, so the loop
        # normal is just the vertex's; glTF's NORMAL accessor is written from
        # the LOOP normals, which is why this has to be a custom split normal
        # and not a vertex attribute of our own.
        if self.cN:
            NR = np.concatenate(self.cN)
            try:
                me.shade_smooth()
            except Exception:
                pass
            try:
                me.use_auto_smooth = True          # <4.1 only; a no-op after
            except Exception:
                pass
            lv = np.zeros(len(me.loops), np.int32)
            me.loops.foreach_get("vertex_index", lv)
            me.normals_split_custom_set([tuple(v) for v in NR[lv]])
        ob = bpy.data.objects.new(self.name + "_cards", me)
        coll.objects.link(ob)
        return ob


# ---------------------------------------------------------------------------
# ONE BUSH — the line-up's exhibit and the unit the forest masses are made of
# ---------------------------------------------------------------------------
def bush(M, rng, x, y, z, r, h, nlobe=5, tone=1.0, squash=0.16, subd=2):
    """A chunky multi-lobed core: one dominant lobe plus satellites.

    The satellites sit at 0.40-0.70 r and are DELIBERATELY unequal — a ring of
    equal lobes is a flower, and a single lobe is round 1's rejected blob.
    """
    ids = [M.lobe(x, y, z + h * 0.50, r, r * rng.uniform(0.88, 1.06), h * 0.55,
                  subd=subd, seed=rng.randint(1 << 28), squash=squash,
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
                          subd=subd if rr > r * 0.5 else max(subd - 1, 0),
                          seed=rng.randint(1 << 28),
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
