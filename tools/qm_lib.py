"""qm_lib.py — terrain / ceiling / corridor model for the QUAY-MARKET TIER.

Shared by `qm_build.py`, `qm_light.py` and `qm_shots.py` so all three agree about
where the floor is, what is overhead, and where the cameras stand.  Imported
inside a Blender session with the LIVE master open
(`tools/blends/dellhollow-master.blend`).

Jurisdiction: parcel `p-quay-mkt` — x 30.70..63.60, y 6.50..21.50, z 12.50..17.50
(the map's own bounds; the brief's y/z are transposed and the map is authority).
Members: cookhouse, quay-deck, market-stalls, notice-board, deep-stairs-head.

Coordinate contract is the town's: x = along-gorge, y = out from the town cliff
(0) toward the river, z = height.

THE NUMBERS THAT GOVERN THIS DISTRICT — every one MEASURED, none assumed
------------------------------------------------------------------------
* FLOOR = 14.00.  Every market-level pad reads z 13.92..14.04 and the two
  landmark slabs (`walk_lm_quay-deck`, `walk_lm_market-stalls`) read 13.99..14.25.
  The parcel's z bounds of 12.5..17.5 are a VOLUME, not a floor.

* THIS IS THE TOWN'S FIRST DISTRICT WITH WALKABLE TOPOLOGY DIRECTLY OVERHEAD,
  and that broke the shared corridor model (finding 222).
  `boatyard_lib.Corridor.top_at` returns the MAXIMUM walk top over a point.  For
  a single-tier district that is right.  Here the shop street's walk graph lies
  over the market's at the same (x, y) five metres up, so a market-level solid
  tested with `top_at` is measured against the street ABOVE it and every corridor
  test passes: the first cut of the arcade put its wall 1.10 m inside
  `walk_lm_quay-deck` and the QA would have caught it as blocked samples.
  `WalkIndex` below replaces it — every face, binned in plan, tested per LEVEL.

* THE TIER HAS NO GROUND UNDER MOST OF ITSELF.  Vertical sections through the
  master: south of y = 12.5 there is nothing at all below `shelf_ground`'s
  underside (17.37..18.61) — the shop street above is a PLATE OVER VOID, which
  `shelf_lib` states outright ("east of MASS_X the MARKET tier is underneath and
  it is a plate").  North of y = 12.5 the Waterfront's `wf_ground` rises to
  13.6..14.9 (and pokes 0.86 m ABOVE this floor in a knoll at x ~ 45..46.6), so
  that half is bedded on accepted art.  Past y ~ 17 the quay deck oversails the
  Weave's huts by 6..8 m.  Three zones, and the build reads them off the world:
      MASS   no terrain, or terrain far below      -> masonry bench + the ARCADE
      LAP    terrain within ~0.7 m under the floor -> paving on the walk graph
      DECK   terrain further below but reachable   -> planking, joists, piles

* THE CEILING IS ANOTHER DISTRICT'S FLOOR.  `ceiling()` is a soup of every
  DOWNWARD-facing polygon of SHELF_DISTRICT standing over this tier, plus the
  shelf's hanging creepers whole (they reach z 16.88 and a soffit test cannot see
  a leaf).  Built from geometry, not a ray grid, because a grid a build can
  afford misses a 0.2 m member — the same reason `shelf_lib` did it that way.

* CROSS-PARCEL BUILD ORDER (finding 224).  The arcade BEARS on SHELF_DISTRICT's
  plate: bearing heights come from a run-time measurement of that plate's
  underside (`plate_min`), never from a constant.  Consequence, and it is the
  master's first inter-district structural dependency: on any joint rebuild the
  shelf must be rebuilt BEFORE the quay market.  Stated here, in `qm_build.py`'s
  docstring, in the deletions manifest and in the KITLIB manifest.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (Corridor, dist_poly2, point_in_poly, plane_z_fn,
                          world_bbox, offset_poly)

# ------------------------------------------------------------------ extents
QX0, QX1 = 30.70, 63.60         # the parcel, in x
QY0, QY1 = 2.40, 20.40          # the sheet's y span: south past the walk graph's
                                # own reach so the arcade has a floor and the
                                # space behind it closes into the cliff instead of
                                # ending in a visible edge
FLOOR = 14.00
DECK_DROP = 0.050               # paving/planking this far UNDER the walk top, so
                                # the master's down-ray still lands on canonical
                                # topology (finding 90)
GROUND_DROP = 0.30              # ... and the ground sheet under the paving
PAVE_W = 1.60                   # half-width of paving laid on a walk ribbon
CORRIDOR_H = 2.05               # the headroom band the master's QA measures
TIER_LO, TIER_HI = 12.00, 18.20 # a walk face in this band is ON this tier
LEVEL_BAND = 1.60               # ... and two walk faces within this of each other
                                # are on the same LEVEL for capping purposes
TALUS_Y = 6.90                  # the floor is flat north of here and climbs as a
                                # cut-and-spoil talus south of it, up to the plate
BASEZ = 8.20
MASS_DEPTH = 4.60               # how deep the masonry bench is; a bench whose
                                # underside chases the riverbed is an 18 m slab
CEIL_CLEAR = 0.30
PIER_SHY = 0.040                # THE ARCADE'S BEARING GAP: bearing to the eye, no
                                # interpenetration for the audit
DECK_MIN = 0.70
PILE_MAX = 7.40
BASE_FLOOR = 5.60               # the mass never plunges below this

PLAZA_QUAY = (47.90, 58.90, 8.50, 19.50)
PLAZA_MKT = (56.09, 62.09, 10.00, 16.00)
LH_X0, LH_X1 = 76.20, 85.20


# =========================================================================
# THE WALK INDEX — per-LEVEL corridor tests (finding 222)
# =========================================================================
class WalkIndex:
    """Every walk_/bar_ upward face, binned in plan, queried per level.

    `Corridor.top_at` answers "how high is the highest walk here", which is the
    wrong question in a town with two walkable tiers over each other.  Every
    query below tests EVERY face whose expanded footprint contains the point, so
    a market-level solid is measured against the market's walks and against the
    shop street's independently.
    """

    def __init__(self, objs, margin=0.30):
        self.faces = []
        self.bins = {}
        for ob in objs:
            Mx = ob.matrix_world
            N = Mx.to_3x3().inverted().transposed()
            for p in ob.data.polygons:
                if (N @ p.normal).normalized().z <= 0.5:
                    continue
                raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
                poly = offset_poly(raw, margin) if margin else raw
                fn = plane_z_fn(raw)
                idx = len(self.faces)
                self.faces.append((poly, fn, raw, ob.name))
                x0 = min(q.x for q in poly); x1 = max(q.x for q in poly)
                y0 = min(q.y for q in poly); y1 = max(q.y for q in poly)
                for bx in range(int(math.floor(x0)), int(math.floor(x1)) + 1):
                    for by in range(int(math.floor(y0)), int(math.floor(y1)) + 1):
                        self.bins.setdefault((bx, by), []).append(idx)

    def _at(self, x, y):
        return self.bins.get((int(math.floor(x)), int(math.floor(y))), ())

    def tops_at(self, x, y):
        """Every walk top over (x, y), one per containing face."""
        out = []
        for i in self._at(x, y):
            poly, fn, raw, nm = self.faces[i]
            if point_in_poly(x, y, poly):
                out.append((fn(x, y), nm))
        return out

    def blocked(self, x, y, z, pad=0.16, h=CORRIDOR_H):
        """True if a solid at (x, y, z) would stand in ANY walking line."""
        for dx, dy in ((0, 0), (pad, 0), (-pad, 0), (0, pad), (0, -pad),
                       (pad * .7, pad * .7), (-pad * .7, pad * .7),
                       (pad * .7, -pad * .7), (-pad * .7, -pad * .7)):
            for zt, nm in self.tops_at(x + dx, y + dy):
                if zt - 0.12 <= z <= zt + h:
                    return True
        return False

    def top_band(self, x, y, zlo, zhi):
        """The highest walk top over (x, y) INSIDE a height band, or None."""
        best = None
        for zt, nm in self.tops_at(x, y):
            if zlo <= zt <= zhi and (best is None or zt > best):
                best = zt
        return best


def corridors():
    """walk_ ONLY, and that distinction cost a rebuild.

    `bar_` railings are canonical topology and the master's QA accepts them as a
    first hit, but they are not WALKING SURFACES: their cap faces stand 0.9 m
    above the tread they guard, and including them made
    `bar_e_deep-stairs-head__*`'s cap the reference for the paving beside it —
    the deck came out at z 14.84 laid on a handrail.  Rails are keep-out for
    props (`RAILS` below), never a surface to build to.
    """
    walks = [o for o in bpy.data.objects if o.type == 'MESH'
             and o.name.startswith("walk_")]
    return walks, WalkIndex(walks, margin=0.0), WalkIndex(walks, margin=0.30), \
        WalkIndex(walks, margin=0.55)


def rails():
    """`bar_` railing bounding boxes — a keep-out list for props, nothing more."""
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith("bar_"):
            continue
        b = world_bbox(ob)
        if b[1] < QX0 - 2 or b[0] > QX1 + 2 or b[5] < TIER_LO - 2 or b[4] > TIER_HI + 2:
            continue
        out.append(b)
    return out


def over_walk(idx, x, y, z, pad=0.16, h=CORRIDOR_H):
    return idx.blocked(x, y, z, pad, h)


# =========================================================================
# WHAT IS ALREADY THERE — the existing-TERRAIN sampler
# =========================================================================
# The zone a node belongs to is a property of the WORLD, and the question is
# specifically "what real TERRAIN is under this point" — not "what is the first
# thing a ray hits".  A whitelist rather than a blacklist, because the wrong
# answers here are expensive and specific: the Weave's huts stand under the quay
# deck with their ridges 0.46 m below its surface, so a blacklist that let them
# through would have bedded the market's floor slab on a weaver's roof and driven
# its piles through three of them.  `clear_below` is the separate question a pile
# has to ask.
_TERRAIN = ("wf_ground", "seam_bank", "yard_ground", "lf_ground", "riverbed",
            "lf_riverbed_tail", "lf_farbank_tail", "water_pool", "water_mid",
            "water_upstream", "lf_lock_floor")
_RAY_Z0 = FLOOR + 2.40          # above the wf_ground knoll (15.09 max) and below
                                # the shop street's plate (17.37 min)
_EX = {}
_CB = {}


def existing(x, y, z0=None, depth=32.0):
    """(z, name) of the first real TERRAIN surface under the floor, or (None, None)."""
    k = (round(x, 2), round(y, 2))
    if k in _EX:
        return _EX[k]
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    z = _RAY_Z0 if z0 is None else z0
    stop = z - depth
    out = (None, None)
    for _ in range(64):
        hit, loc, nor, idx, ob, m = sc.ray_cast(dg, Vector((x, y, z)),
                                                Vector((0, 0, -1)), distance=z - stop)
        if not hit or ob is None:
            break
        if ob.name.startswith(_TERRAIN):
            out = (loc.z, ob.name)
            break
        z = loc.z - 0.008
        if z <= stop:
            break
    _EX[k] = out
    return out


def clear_below(x, y, zfrom):
    """True when the column under (x, y) reaches TERRAIN without passing through
    anything else — the question a pile has to ask before it is driven."""
    k = (round(x, 2), round(y, 2), round(zfrom, 1))
    if k in _CB:
        return _CB[k]
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    z = zfrom
    ok = False
    for _ in range(48):
        hit, loc, nor, idx, ob, m = sc.ray_cast(dg, Vector((x, y, z)),
                                                Vector((0, 0, -1)), distance=z + 12.0)
        if not hit or ob is None:
            break
        nm = ob.name
        if nm.startswith(_TERRAIN):
            ok = True
            break
        if nm.startswith(("walk_", "bar_", "lm_", "veg_", "fx_", "qm_", "KEYQ_")):
            z = loc.z - 0.008          # not an obstruction, keep going
            continue
        ok = False                     # a hut, a deck, a prop: no pile here
        break
    _CB[k] = ok
    return ok


def zone(x, y):
    """'lap' | 'deck' | 'mass' — which of the three the tier is here."""
    ez, en = existing(x, y)
    if ez is not None and FLOOR - ez < DECK_MIN:
        return "lap"
    if ez is not None and FLOOR - ez <= PILE_MAX:
        return "deck"
    return "mass"


# =========================================================================
# THE CEILING — SHELF_DISTRICT's plate, measured off its own geometry
# =========================================================================
# DOWNWARD faces only for the structural sheets.  The first cut took every
# polygon whose lowest vertex stood above the floor, which swept up `wf_ground`'s
# own terrain faces at z 14.4 and told the cookhouse its ceiling was 0.42 m over
# its head.  A ceiling is a SOFFIT: it faces down.  Vegetation is the exception —
# a hanging creeper has faces in every direction and all of them are in the way.
_PLATE = ("shelf_ground", "shelf_paving", "shelf_parapet", "shelf_stair_underworks")
_OVER = _PLATE + ("shelf_inn", "shelf_item_shop", "shelf_weapon_shop",
                  "shelf_armor_shop", "shelf_home_a", "shelf_home_b", "shelf_home_c",
                  "shelf_stalls", "shelf_awning", "shelf_bunting", "shelf_clutter",
                  "shelf_lantern", "shelf_cliffface",
                  "gate_", "cargo_winch_foot")
_SOFT_OVER = ("veg_shelf_",)
_CEIL = None


def _ceiling_soup():
    global _CEIL
    if _CEIL is not None:
        return _CEIL
    _CEIL = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        soft = ob.name.startswith(_SOFT_OVER)
        if not (soft or ob.name.startswith(_OVER)):
            continue
        b = world_bbox(ob)
        if b[5] < FLOOR + 1.30 or b[4] > 34.0:
            continue
        if b[1] < QX0 - 3.0 or b[0] > QX1 + 3.0:
            continue
        M = ob.matrix_world
        N = M.to_3x3().inverted().transposed()
        me = ob.data
        for p in me.polygons:
            if not soft and (N @ p.normal).normalized().z > -0.15:
                continue                       # not a soffit
            P = [M @ me.vertices[i].co for i in p.vertices]
            zl = min(q.z for q in P)
            if zl < FLOOR + 1.30 or zl > 30.0:
                continue
            x0, x1 = min(q.x for q in P), max(q.x for q in P)
            rec = (x0, x1, min(q.y for q in P), max(q.y for q in P), zl, ob.name)
            for bx in range(int(math.floor(x0)) - 1, int(math.floor(x1)) + 2):
                _CEIL.setdefault(bx, []).append(rec)
    return _CEIL


def ceiling_named(x, y, pad=0.0):
    best, who = 99.0, None
    for x0, x1, y0, y1, zl, nm in _ceiling_soup().get(int(math.floor(x)), ()):
        if zl < best and x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad:
            best, who = zl, nm
    return best, who


def ceiling(x, y, pad=0.0):
    return ceiling_named(x, y, pad)[0]


def ceiling_over(x0, x1, y0, y1, step=0.22, pad=0.18):
    """The lowest ceiling anywhere over a rectangle — what caps a ridge."""
    best, who = 99.0, None
    nx = max(2, int((x1 - x0) / step) + 1)
    ny = max(2, int((y1 - y0) / step) + 1)
    for i in range(nx):
        for j in range(ny):
            z, nm = ceiling_named(x0 + (x1 - x0) * i / (nx - 1),
                                  y0 + (y1 - y0) * j / (ny - 1), pad)
            if z < best:
                best, who = z, nm
    return best


def plate_under(x, y, pad=0.0):
    """(underside z, object) of the shop street's structural plate, or (None, None).

    This is what a pier may BEAR on — the plate itself, not a creeper and not the
    far cliff.  Condition 1 of the arcade's red-team verdict: measured here, at
    run time, never stored as a constant.
    """
    best, who = None, None
    for x0, x1, y0, y1, zl, nm in _ceiling_soup().get(int(math.floor(x)), ()):
        if not nm.startswith(_PLATE):
            continue
        if x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad:
            if best is None or zl < best:
                best, who = zl, nm
    return best, who


def plate_min(x0, x1, y0, y1, step=0.18):
    """The LOWEST plate underside over a footprint — what a pier is cut to."""
    best, who = None, None
    nx = max(2, int((x1 - x0) / step) + 1)
    ny = max(2, int((y1 - y0) / step) + 1)
    for i in range(nx):
        for j in range(ny):
            z, nm = plate_under(x0 + (x1 - x0) * i / (nx - 1),
                                y0 + (y1 - y0) * j / (ny - 1))
            if z is not None and (best is None or z < best):
                best, who = z, nm
    return best, who


# =========================================================================
# TERRAIN
# =========================================================================
class Terrain:
    """Floor height + zone mask for the quay-market tier."""

    def __init__(self):
        self.walks, self.cor0, self.cor, self.keep = corridors()
        self.high = []      # on this tier (and the stairs entering its band)
        self.low = []       # the deep stairs' lower flights, the Weave below
        self.up = []        # the SHOP STREET's own graph, 5 m over our heads
        for poly, fn, raw, nm in self.cor0.faces:
            zt = sum(p.z for p in raw) / len(raw)
            cx = sum(p.x for p in raw) / len(raw)
            cy = sum(p.y for p in raw) / len(raw)
            if not (QX0 - 6.0 <= cx <= QX1 + 8.0):
                continue
            if cy > QY1 + 5.0 or cy < QY0 - 2.0:
                continue
            if zt > TIER_HI:
                self.up.append((raw, fn, zt, nm))
            elif zt >= TIER_LO:
                self.high.append((raw, fn, zt, nm))
            else:
                self.low.append((raw, fn, zt, nm))

    # ---------------------------------------------------------- the shape
    def natural(self, x, y):
        """The tier before the walk graph gets a vote.

        A quay is flat and drains to the gorge; the only real relief is the
        TALUS at the back, where the bench was cut out of the rock and the spoil
        never fully cleared.  That talus is what closes the arcade's dark space
        into `shelf_cliffface` instead of leaving a floating edge, and its rate
        is set so it meets the plate's underside inside the sheet's own y span.
        """
        n = (math.sin(x * 0.51 + y * 0.77) * 0.36 +
             math.sin(x * 1.63 - y * 1.09) * 0.17 +
             math.sin(x * 3.11 + y * 2.53) * 0.06) * 0.17
        h = FLOOR + 0.10 - 0.010 * max(0.0, y - 9.0)
        d = max(0.0, TALUS_Y - y)
        h += 0.26 * d + 0.135 * d * d
        return h + n

    def clamp(self, x, y, h):
        """No ground may stand over a walk surface, and it may only climb away
        from one at ~49 deg (manifest 38/74)."""
        for raw, fn, zt, nm in self.high:
            d = dist_poly2(x, y, raw)
            if d < 4.6:
                h = min(h, self.plane_at(raw, fn, x, y, d) - GROUND_DROP
                        + max(0.0, d - (PAVE_W + 0.45)) * 1.15)
        # A walk BELOW the district is a disjunction, not a ceiling (finding 92):
        # the Deep Stairs drop 8.5 m off this tier's west corner and the pilot
        # stair 4 m off its east.  Ground may terrace down with them or clear
        # them entirely, never sit in the band between.
        for raw, fn, zt, nm in self.low:
            d = dist_poly2(x, y, raw)
            if d >= 2.2:
                continue
            top = self.cor0.top_band(x, y, zt + 0.05, TIER_HI)
            if top is not None:
                continue                       # buried under a higher walk
            lo = zt + d * 1.15 - DECK_DROP
            if lo < h < zt + CORRIDOR_H + d * 0.6:
                h = lo
        c = ceiling(x, y)
        if c < 90.0:
            h = min(h, c - CEIL_CLEAR)
        return h

    @staticmethod
    def plane_at(raw, fn, x, y, d):
        if d <= 0.0:
            return fn(x, y)
        best, bp = 1e9, None
        n = len(raw)
        for i in range(n):
            a, b = raw[i], raw[(i + 1) % n]
            ab = Vector((b.x - a.x, b.y - a.y))
            L2 = ab.length_squared
            t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0,
                ((x - a.x) * ab.x + (y - a.y) * ab.y) / L2))
            px, py = a.x + t * ab.x, a.y + t * ab.y
            dd = (px - x) ** 2 + (py - y) ** 2
            if dd < best:
                best, bp = dd, (px, py)
        return fn(*bp)

    # ------------------------------------------------------------- the lip
    def rim(self, x):
        """Outer (gorge-side) reach of anything this district builds.

        Read off the walk graph's own northern edge and the accepted art beyond
        it: `walk_lm_quay-deck` runs to y = 19.50 and the Weave's huts stand from
        y = 15.79 with ridges at z 13.7, so the deck stops where the huts begin
        to matter and the rail goes on that line.
        """
        P = [(30.70, 15.40), (34.00, 18.60), (36.60, 19.10), (40.00, 16.40),
             (44.00, 16.10), (47.40, 16.80), (49.30, 19.95), (56.20, 19.95),
             (58.90, 19.10), (60.40, 17.20), (63.60, 16.70)]
        if x <= P[0][0]:
            return P[0][1]
        for i in range(len(P) - 1):
            (x0, y0), (x1, y1) = P[i], P[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0)
                return y0 + (y1 - y0) * (t * t * (3 - 2 * t))
        return P[-1][1]

    def ylo(self, x):
        return QY0

    def has_ground(self, x, y):
        if not (QX0 - 1e-6 <= x <= QX1 + 1e-6):
            return False
        return self.ylo(x) - 1e-6 <= y <= self.rim(x) + 0.90

    # --------------------------------------------------------------- nodes
    def node(self, x, y):
        """(top, bottom) for one ground node, or (None, None) where this district
        builds nothing.

        Nothing is built where the world already provides the surface: `wf_ground`
        rises to within 0.45 m of the floor over the whole bedded half and pokes
        0.86 m ABOVE it in a knoll at x ~ 45..46.6, and `yard_ground` stands
        1.24 m above the deep-stairs-head pad at the west corner.  Both are
        accepted art of other districts; the sheet stops at them rather than
        arguing with them.
        """
        if not self.has_ground(x, y):
            return None, None
        t = self.clamp(x, y, self.natural(x, y))
        over = y - self.rim(x)
        if over > 0.0:
            t -= 18.0 * (over ** 1.30)
        ez, en = existing(x, y)
        if ez is not None and ez >= t - 0.12:
            return None, None                  # the world is already the floor
        if t < FLOOR - 3.4:
            return None, None                  # off the end of a stair; not ours
        # ZONE PRECEDENCE, and getting it wrong cost the deck entirely.  The first
        # cut built ground wherever terrain was more than 0.12 m below the floor,
        # which is TRUE of the whole gorge — so the masonry bench swallowed the
        # deck zone and grew an underside at z 7.58 out over the Weave's roofs.
        # The bench belongs only where there is nothing to build on or off:
        #   ez is None                  -> MASS, a real bench with a real depth
        #   FLOOR - ez < DECK_MIN       -> LAP, the Waterfront's ground shows
        #   otherwise                   -> DECK, planking on piles (section 5)
        if ez is not None and FLOOR - ez >= DECK_MIN:
            return None, None
        # THE UNDERSIDE.  Bedded onto terrain where there is terrain to bed onto,
        # otherwise a bench of a believable depth — never a slab that chases the
        # riverbed 18 m down, which is what the first cut built.
        if ez is not None:
            b = min(ez + 0.08, t - 0.34)
        else:
            b = t - MASS_DEPTH
        return t, max(min(b, t - 0.34), min(t - 0.34, BASE_FLOOR))

    def top(self, x, y):
        t, b = self.node(x, y)
        if t is not None:
            return t
        ez, en = existing(x, y)
        if ez is not None:
            return ez
        return self.clamp(x, y, self.natural(x, y))


# =========================================================================
# THE REVIEW CAMERAS — and the near-field rule that depends on them
# =========================================================================
# The shot list lives HERE because the BUILD needs it: density and prop size are
# properties of a zone SEEN FROM SOMEWHERE (finding 108).  Per the 2026-07-29
# render norm these are disposable scaffolding — "subject visible" is the bar and
# no angle gets polished past it.  EYE HEIGHT IS THE PROBLEM ON THIS TIER TOO:
# the floor is 14.00 and the arcade's soffit is 17.4..18.6, so a camera above
# ~16.6 standing inside the undercroft renders the shop street's underside and
# nothing else.  Every interior eye below is 1.5..1.9 m off the floor.
SHOTS = {
    # the parcel's own camera, from over the gorge at the deck: cookhouse glow
    # left, stalls centre, the shop street's lights rising behind.
    "quay":    dict(pos=(61.40, 25.80, 19.20), aim=(44.60, 12.80, 15.10), fov=46, fit='H'),
    # on the deck looking west down the tier — the player's own frame arriving
    # from the market.
    "deck":    dict(pos=(58.60, 16.90, 15.62), aim=(41.00, 13.60, 15.05), fov=52, fit='H'),
    # the arcade: eye level under the shop street's plate, along the colonnade.
    # This is the frame the whole undercroft exists for.
    "arcade":  dict(pos=(56.20, 10.90, 15.55), aim=(38.60, 9.60, 15.20), fov=54, fit='H'),
    # the cookhouse from the deck's north-east, its lit north front over the drop.
    "cook":    dict(pos=(46.60, 19.60, 16.05), aim=(39.60, 14.40, 15.60), fov=48, fit='H'),
    # the market stalls and the notice board, from the plaza.
    "stalls":  dict(pos=(52.20, 15.60, 15.75), aim=(60.60, 12.60, 15.05), fov=50, fit='H'),
    # THERE IS NO GORGE CAMERA FOR THIS TIER, and finding that out is worth the
    # frame it cost.  Every other district's "prove it stands on something" shot
    # comes from out over the gorge and below; here that sightline does not exist.
    # East of x=42 the bench is BEDDED on `wf_ground`, which rises to 13.6..14.9
    # and hides its own underside; west of that the void is filled by the Weave —
    # `wv_hut_weave-north_0/1/2` occupy x 41..54 / y 15.8..23.3 up to z 13.74, and
    # `wv_cloth_1..7` string dye lines across x 45..78 at z 7..11.6.  A camera at
    # (52, 31, 8.6) renders the Weave's washing, with the market a strip along the
    # top edge (`quaymkt_v2_gorge.png`, kept as the record).  So the support
    # question is answered by the AUDIT (0 strays over 170 meshes, every pile
    # column-tested twice) rather than by a frame.
    #
    # DO NOT RETRY THIS.  The second attempt (`piles`, below) moved in to deck
    # level and over the Weave's roofs at (57.6, 22.6, 12.1) — and landed INSIDE
    # the `wv_hut_pilot-cluster` cluster, so it renders a hut roof and its crates
    # with this district's joists in the top-left corner
    # (`quaymkt_v2_piles.png`, also kept).  Two frames were enough to establish
    # the general fact: between y = 15.8 and 23.3 the Weave owns the whole volume
    # from z 3.7 to 13.7, this deck's underside is at 13.6..14.0, and there is no
    # standoff between them.  Both frames are kept because what they DO show — a
    # market deck 0.5 m over a weaver's ridge — is the town's tightest vertical
    # stack and worth a custodian's attention.
    "piles":   dict(pos=(57.60, 22.60, 12.10), aim=(52.00, 17.40, 13.70), fov=46, fit='H'),
    "gorge":   dict(pos=(52.00, 31.00, 8.60), aim=(46.00, 14.20, 14.60), fov=44, fit='H'),
    # the v10 Boatyard hero camera, unchanged — value continuity against
    # boatyard_v10 / gate_v7_continuity / shelf continuity (manifest 53/67).
    "continuity": dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
}

HERO = ("quay", "deck", "arcade", "cook", "stalls")
HERO_EYES = [Vector(SHOTS[n]["pos"]) for n in HERO]

NEAR_FRAC = 0.85
NEAR_K = 3.20

_FRUSTA = []
for _n in HERO:
    _s = SHOTS[_n]
    _eye = Vector(_s["pos"])
    _fwd = (Vector(_s["aim"]) - _eye)
    _sub = _fwd.length
    _fwd = _fwd.normalized()
    _FRUSTA.append((_eye, _fwd, _sub, math.cos(math.radians(_s["fov"] * 0.62))))


def hero_dist(x, y, z):
    p = Vector((x, y, z))
    return min((p - e).length for e in HERO_EYES)


def near_field(x, y, z, extent=1.0):
    """The fraction of full size and density a loose prop may have here.

    Copied unchanged from `gate_lib`/`shelf_lib` (findings 106/107): two earlier
    formulations failed — absolute radii stripped the tufts with the clumps, a
    pure distance/size ratio deleted every tree in the parcel.  Not re-derived.
    """
    p = Vector((x, y, z))
    worst = 1.0
    for eye, fwd, sub, coshw in _FRUSTA:
        v = p - eye
        d = v.length
        if d < 1e-4 or d >= sub * NEAR_FRAC:
            continue
        if v.dot(fwd) / d < coshw:
            continue
        worst = min(worst, max(0.0, min(1.0, d / (NEAR_K * max(extent, 0.05)))))
    return worst
