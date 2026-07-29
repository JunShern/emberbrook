"""shelf_lib.py — shared terrain / corridor / ceiling model for the SHELF TIER.

Used by `shelf_build.py`, `shelf_light.py` and `shelf_shots.py` so all three agree
on where the ground is, where the ceiling is, and where the cameras stand.
Imported inside a Blender session that has the gate BRANCH copy of the master open.

Jurisdiction: parcels `p-shelf-w` (x 17.5..42.3) and `p-shelf-e` (x 39.8..55.3),
y 1.0..13.5, at the tier floor z = 19.0.  The parcels overlap in x 39.8..42.3;
that overlap is STREET, not building (the weapon shop ends at 39.9 and the armor
shop begins at 42.2), so the seam is owned by the WEST parcel for ground purposes
and nothing is built in it.

Coordinate contract is the town's:  x = along-gorge, y = out from the town cliff
(0) toward the river, z = height.  The shelf is Dellhollow's shop street: it hangs
between the GATE tier 5 m above (whose gallery plate is this district's ceiling)
and the MARKET tier 5 m below (whose volume this district's ground may not enter).

THE THREE NUMBERS THAT GOVERN THIS DISTRICT
-------------------------------------------
* FLOOR = 19.00.  All five landmark pads read z 18.92..19.04.  The parcel's z
  bounds of 17.5..22.5 are a VOLUME, not a floor: do not build ground at 17.5.
* RIDGE_CAP = 23.10.  `gate_ground`'s eastern gallery plate has its underside at
  23.33..23.66 over x 19..29.4, y 4.2..11.2.  The blockout roofs top out at 23.55,
  which is 0.22 m ABOVE that: 23.55 is a blockout number, not a permission.
  4.10 m of build height, so differentiation comes from ridge DIRECTION, dormers
  and awning depth, never from height.
* CORBEL_FLOOR = 21.22.  MEASURED, per strut, not assumed: `gate_corbels` is 15
  components on a 1.55 m x-grid at x 19.20/20.75/22.30/23.85/25.40/26.95, in two
  bands — a RIM band (y 8.17..11.25, raking down to 21.22 at its inboard tip) at
  every station, and a SOUTH band (y 4.48..7.39, raking down to 21.38) at the
  first three stations only.  Those two bands are why the Inn cannot stand on its
  own pad at full height: between them, at x 22.3, the clear slot is y 7.39..8.78.
  The buildings are placed in the pockets the corbels leave, and every ridge is
  capped by `ceiling()`, which RAY-CASTS the gate's own art rather than trusting
  any of the numbers in this docstring.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import Corridor, dist_poly2, point_in_poly, plane_z_fn, world_bbox

# ------------------------------------------------------------------ extents
SX0, SX1 = 19.10, 55.35         # ground sheet, x.  West of 19.1 the GATE's own
                                # rock promontory (gate_ground, solid to z=-8.35)
                                # already fills the space; the sheet dies into it.
SY0, SY1 = 1.05, 13.40          # ground sheet, y  (cliff veneer .. gorge lip)
FLOOR = 19.00                   # the tier's walking surface, measured off the pads
RIDGE_CAP = 23.10               # nothing of ours rises above this, anywhere
CLIMB_CAP = 20.90               # ... and the GROUND may not climb above this, so
                                # the terrace under the gate stair never reaches
                                # the corbel tips at 21.22
BASEZ = -5.00                   # foot of the shelf's own rock mass (never in shot)
MARKET_TOP = 17.55              # p-quay-mkt's ceiling: our plate's underside may
                                # not enter the market's volume
DECK_DROP = 0.050               # paving sits this far UNDER the walk top, so the
                                # walk QA's down-ray still lands on the walk mesh
GROUND_DROP = 0.30              # ... and the GROUND SHEET sits under the paving.
                                # A sheet held only DECK_DROP under the walk and
                                # allowed to climb at 1.15 from the ribbon's edge
                                # rises 0.25 m in the 0.32 m between two nodes and
                                # pokes through the paving at the street's kerb —
                                # 2 blocked samples, both at a ribbon edge.
PAVE_W = 1.30                   # half-width of the paving laid on a walk ribbon
CORRIDOR_H = 2.05               # headroom band the QA measures over a walk
TIER_Z = 18.00                  # a walk at or above this is "on the shelf or above"
MASS_X = 30.70                  # west of this nothing at all is built below the
                                # shelf, so the ground is a solid rock mass; east of
                                # it the MARKET tier is underneath and it is a plate

# the parcel seam: p-shelf-w and p-shelf-e overlap here.  Declared once, in one
# place, so no piece of art has to decide it twice.
SEAM_X = (39.80, 42.30)


def corridors():
    walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
    return walks, Corridor(walks, margin=0.0), Corridor(walks, margin=0.30), \
        Corridor(walks, margin=0.55)


class Terrain:
    """Ground height + footprint mask for the shelf tier."""

    def __init__(self):
        self.walks, self.cor0, self.cor, self.keep = corridors()
        self.high = []      # on the shelf, or the gate stair descending onto it
        self.low = []       # the market tier and the loop stair dropping to it
        for poly, fn, raw, nm in self.cor0.tops:
            zt = sum(p.z for p in raw) / len(raw)
            cx = sum(p.x for p in raw) / len(raw)
            cy = sum(p.y for p in raw) / len(raw)
            if not (SX0 - 4.0 <= cx <= SX1 + 6.0):
                continue
            if cy > SY1 + 4.5 or cy < SY0 - 3.0:
                continue
            if zt > 24.5:
                continue                     # the gate tier's own road: not ours
            (self.high if zt >= TIER_Z else self.low).append((raw, fn, zt, nm))
        self._keepout = None
        self._ylo = {}

    # ------------------------------------------------------------ the lip
    def rim(self, x):
        """Outer (gorge-side) lip of the shelf.

        Read off three things and not chosen by eye: the walk graph's own
        northern reach (the pads run out to y=10.3), the Waterfront's ground
        (`wf_ground` begins at y=12.50 and tops at 15.09, so the shelf must not
        oversail it by much), and the CARGO WINCH: `cargo_winch_foot` rises from
        the quay through x 28.25..31.90 and the gate's hoist rope drops through
        x 27..30 — the lip lets go there or the tower comes out of the ground.
        """
        P = [(19.0, 11.35), (23.0, 11.60), (26.0, 11.30), (27.4, 10.10),
             (28.2, 9.05), (31.6, 9.05), (32.6, 10.60), (35.0, 12.30),
             (40.0, 12.90), (46.0, 13.05), (49.5, 12.70), (51.5, 11.60),
             (53.0, 10.90), (55.4, 10.70)]
        if x <= P[0][0]:
            return P[0][1]
        for i in range(len(P) - 1):
            (x0, y0), (x1, y1) = P[i], P[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0)
                return y0 + (y1 - y0) * (t * t * (3 - 2 * t))
        return P[-1][1]

    def ylo(self, x):
        """Inner (cliff-side) edge of the shelf.

        The cliff veneer stands at y ~0.1..1.0 and the gate's own veneer bulges to
        y=2.58 at its foot west of x=31.44, so the shelf's inner edge has to clear
        it rather than be pushed into it.
        """
        return 1.55 if x < 31.60 else 1.05

    # ---------------------------------------------------- the winch keep-out
    def winch_keepout(self, x, y):
        """`cargo_winch_foot` is ACCEPTED WATERFRONT ART and it passes straight
        through this tier's plane.  Its BOUNDING BOX is not its footprint
        (finding 96 — it is one joined mesh holding a tower at x~30 and a rope
        head at x~28.7 twenty metres up), so the keep-out is built from the
        vertices that actually lie in the shelf's own height band."""
        if self._keepout is None:
            self._keepout = []
            for nm in ("cargo_winch_foot", "gate_winch_rope"):
                ob = bpy.data.objects.get(nm)
                if ob is None:
                    continue
                P = [ob.matrix_world @ v.co for v in ob.data.vertices
                     if 15.0 <= (ob.matrix_world @ v.co).z <= 23.5]
                if P:
                    self._keepout.append((min(p.x for p in P), max(p.x for p in P),
                                          min(p.y for p in P), max(p.y for p in P)))
        for x0, x1, y0, y1 in self._keepout:
            if x0 - 0.75 <= x <= x1 + 0.75 and y0 - 0.75 <= y <= y1 + 0.75:
                return True
        return False

    # ------------------------------------------------------------- the shape
    def natural(self, x, y):
        """The shelf before the walk graph gets a vote: a terrace that leans a
        few centimetres out to the gorge, with a rock swell against the cliff."""
        n = (math.sin(x * 0.47 + y * 0.81) * 0.40 +
             math.sin(x * 1.57 - y * 1.13) * 0.19 +
             math.sin(x * 3.07 + y * 2.61) * 0.06) * 0.26
        h = FLOOR + 0.13 - 0.012 * max(0.0, y - 3.0)
        d = max(0.0, 2.9 - y)
        h += 0.42 * d * d / 8.41
        return h + n

    def clamp(self, x, y, h):
        """No ground may stand over a walk surface, and it may only climb away
        from one at ~49 deg (manifest 38/74).  Capped at CLIMB_CAP so the terrace
        that rises under the gate stair never reaches the corbels."""
        for raw, fn, zt, nm in self.high:
            d = dist_poly2(x, y, raw)
            if d < 4.2:
                h = min(h, self.plane_at(raw, fn, x, y, d) - GROUND_DROP
                        + max(0.0, d - (PAVE_W + 0.45)) * 1.15)
        # A walk BELOW the district is a disjunction, not a ceiling (finding 91):
        # ground may lie under it, terraced, or clear it by the full corridor —
        # never inside the band between.  The loop stair down to the market is
        # terraced; the market floor 5 m below is cleared.
        for raw, fn, zt, nm in self.low:
            d = dist_poly2(x, y, raw)
            if d >= 2.2:
                continue
            top = self.cor0.top_at(x, y)
            if top is not None and top > zt + 0.05:
                continue                         # buried under a higher walk
            lo = zt + d * 1.15 - DECK_DROP
            if lo < h < zt + CORRIDOR_H + d * 0.6:
                h = lo
        return min(h, CLIMB_CAP)

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
            t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - a.x) * ab.x + (y - a.y) * ab.y) / L2))
            px, py = a.x + t * ab.x, a.y + t * ab.y
            dd = (px - x) ** 2 + (py - y) ** 2
            if dd < best:
                best, bp = dd, (px, py)
        return fn(*bp)

    def has_ground(self, x, y):
        if not (SX0 - 1e-6 <= x <= SX1 + 1e-6):
            return False
        if not (self.ylo(x) - 1e-6 <= y <= self.rim(x) + 1.30):
            return False
        if self.winch_keepout(x, y):
            return False
        return True

    def top(self, x, y):
        h = self.clamp(x, y, self.natural(x, y))
        over = y - self.rim(x)
        if over > 0.0:
            h -= 26.0 * (over ** 1.30)
        return max(h, BASEZ)

    # ------------------------------------------------------- what is below us
    def _shells(self):
        if getattr(self, "_shell_cache", None) is None:
            self._shell_cache = []
            for ob in bpy.data.objects:
                if not ob.name.startswith("lm_"):
                    continue
                if ob.name.startswith(("lm_inn", "lm_item-shop", "lm_weapon-shop",
                                       "lm_armor-shop", "lm_shelf-homes")):
                    continue                              # these are mine to remove
                b = world_bbox(ob)
                if b[5] > FLOOR - 0.10:
                    continue
                self._shell_cache.append(b)
        return self._shell_cache

    def under_ceiling(self, x, y):
        """The highest thing our ground's UNDERSIDE has to clear.

        Three sources, all measured: the market tier's walk surfaces (which need
        the full 2.05 m corridor), the market's own `lm_` blockout shells (whose
        roofs come up to 18.55 under the weapon shop — 0.45 m below our floor,
        which is why the plate there is thinner than anywhere else), and the
        market parcel's nominal ceiling at 17.55 east of x=30.7.
        """
        best = BASEZ
        for raw, fn, zt, nm in self.low:
            if dist_poly2(x, y, raw) < 1.60:
                best = max(best, zt + CORRIDOR_H)
        for b in self._shells():
            if b[0] - 0.50 <= x <= b[1] + 0.50 and b[2] - 0.50 <= y <= b[3] + 0.50:
                best = max(best, b[5] + 0.06)
        if x > MASS_X:
            best = max(best, MARKET_TOP)
        return best

    def node(self, x, y):
        """(top, bottom) for one ground node, sharing the one expensive lookup.

        The falling skirt at the gorge lip may not plunge into whatever is below:
        west of MASS_X there is nothing at all under this tier, so the skirt is a
        real 24 m rock face and the tier finally stands on something; east of it
        the MARKET's volume begins at 17.55 and the skirt becomes a 1.4 m lip.
        That one rule also keeps the sheet off `wf_ground` (top 15.09 from y=12.5)
        and `seam_bank` (top 15.85), which are ACCEPTED art from two districts.

        The floor applies ONLY to the falling skirt, never to the clamped
        surface.  A first cut raised the whole node to `under_ceiling + 0.14` and
        pushed 56 down-ray samples' worth of ground up through the loop stair
        descending to the market: those treads run from 19.0 down to 14.4, i.e.
        BELOW the market's own nominal ceiling, so a floor derived from that
        ceiling is exactly the wrong constraint there.  Terraced ground follows
        its stair; only the skirt is floored.
        """
        uc = self.under_ceiling(x, y)
        h = self.clamp(x, y, self.natural(x, y))
        # WHERE THIS DISTRICT'S GROUND STOPS.  The disjunction in `clamp` will
        # happily terrace all the way down a stair, and the loop stair off the
        # shelf-homes descends 4.8 m into the MARKET tier — so the first cut
        # followed it and came to rest ON `walk_lm_quay-deck`, 25 blocked
        # down-ray samples in one corner.  The stair below the shelf's own head
        # is the market's ground to build, not ours: a node whose terraced
        # surface wants to sit below FLOOR-1.10 is simply not made, and the
        # sheet ends in a clean edge at the head of the stair.
        if h < FLOOR - 1.10:
            return None, None
        over = y - self.rim(x)
        t = h - (26.0 * (over ** 1.30) if over > 0.0 else 0.0)
        t = max(t, min(h, uc + 0.14), BASEZ)
        return t, min(uc, t - 0.32)

    def bottom(self, x, y, t):
        return min(self.under_ceiling(x, y), t - 0.32)


# ==========================================================================
# THE CEILING — measured off the gate's own geometry, never assumed
# ==========================================================================
_CEIL_OBJ = ("gate_ground", "gate_corbels", "gate_road", "gate_winch",
             "gate_winch_rope", "gate_cliffface", "gate_arch", "gate_parapet",
             "cargo_winch_foot")
_CEIL_TRIS = None


def _ceiling_soup():
    """Every downward-ish face of the gate district that hangs over this tier,
    as (x0,x1,y0,y1,zmin) boxes.  A ray-cast grid missed the corbels entirely at
    1 m spacing — they are 0.24 m struts on a 1.55 m pitch — so the ceiling is
    built from the GEOMETRY, one bounding box per connected lump of it."""
    global _CEIL_TRIS
    if _CEIL_TRIS is not None:
        return _CEIL_TRIS
    _CEIL_TRIS = {}
    for nm in _CEIL_OBJ:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        M = ob.matrix_world
        me = ob.data
        for p in me.polygons:
            P = [M @ me.vertices[i].co for i in p.vertices]
            zl = min(q.z for q in P)
            if zl < FLOOR + 0.40 or zl > 30.0:
                continue
            x0, x1 = min(q.x for q in P), max(q.x for q in P)
            rec = (x0, x1, min(q.y for q in P), max(q.y for q in P), zl)
            for b in range(int(math.floor(x0)) - 1, int(math.floor(x1)) + 2):
                _CEIL_TRIS.setdefault(b, []).append(rec)
    return _CEIL_TRIS


def ceiling(x, y, pad=0.0):
    """The lowest gate-district surface standing over (x, y), or 99.0 for open sky."""
    best = 99.0
    for x0, x1, y0, y1, zl in _ceiling_soup().get(int(math.floor(x)), ()):
        if zl < best and x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad:
            best = zl
    return best


def ceiling_over(x0, x1, y0, y1, step=0.22, pad=0.18):
    """The lowest ceiling anywhere over a rectangle — what caps a roof ridge."""
    best = 99.0
    nx = max(2, int((x1 - x0) / step) + 1)
    ny = max(2, int((y1 - y0) / step) + 1)
    for i in range(nx):
        for j in range(ny):
            x = x0 + (x1 - x0) * i / (nx - 1)
            y = y0 + (y1 - y0) * j / (ny - 1)
            best = min(best, ceiling(x, y, pad))
    return best


# ==========================================================================
# THE REVIEW CAMERAS — and the near-field rule that depends on them
# ==========================================================================
# The shot list lives HERE and not in `shelf_shots.py` because the BUILD needs
# it: density and prop size are properties of a zone SEEN FROM SOMEWHERE
# (finding 124), so a camera edited in the shot script alone would silently
# invalidate the thinning the frame was thinned for.  Per the 2026-07-29 render
# norm these are disposable scaffolding — "subject visible" is the whole bar.
SHOTS = {
    # the parcel's own p-shelf-w camera: down the street eastward from the foot of
    # the gate stair.  This is the frame a player gets walking into town.
    "street":  dict(pos=(20.60, 2.30, 21.90), aim=(34.50, 8.20, 20.10), fov=48, fit='H'),
    # standing on the street outside the Inn, looking back west and up: the gate
    # gallery overhead, the stair coming down, the inn's gable.
    "inn":     dict(pos=(30.20, 6.60, 20.90), aim=(22.60, 4.20, 21.30), fov=46, fit='H'),
    # mid-street from the gorge rail, looking east over the weapon shop toward the
    # armor shop and the homes.
    "shops":   dict(pos=(31.80, 12.60, 22.30), aim=(45.00, 7.60, 20.20), fov=46, fit='H'),
    # the parcel's own p-shelf-e camera: looking back westward up the street, armor
    # shop cantilevered over the void on the right, homes closing the row behind.
    "armor":   dict(pos=(53.20, 4.40, 21.60), aim=(41.00, 9.60, 20.40), fov=46, fit='H'),
    # from out over the gorge: the tier has to STAND on something.
    "gorge":   dict(pos=(37.00, 36.00, 25.50), aim=(35.00, 8.00, 17.50), fov=44, fit='H'),
    # the v10 Boatyard hero camera, unchanged — value continuity against
    # boatyard_v10.png / gate_v7_continuity.png (manifest 53/67).
    "continuity": dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
}

# the frames that stand INSIDE the district and therefore have a near field at all
HERO = ("street", "inn", "shops", "armor")
HERO_EYES = [Vector(SHOTS[n]["pos"]) for n in HERO]

NEAR_FRAC = 0.85        # props at 85% of the camera-to-subject distance are scenery
NEAR_K = 3.20           # ... and inside that, a prop may not stand closer than
                        # 3.2x its own extent

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
    """The fraction of full size and full density a loose prop may have here.

    Copied unchanged from `gate_lib` (findings 122/123): two earlier formulations
    failed — absolute radii stripped the tufts with the clumps, a pure
    distance/size ratio deleted every tree in the parcel.  Do not re-derive it.
    """
    p = Vector((x, y, z))
    worst = 1.0
    for eye, fwd, sub, coshw in _FRUSTA:
        v = p - eye
        d = v.length
        if d < 1e-4 or d >= sub * NEAR_FRAC:
            continue                                   # at/behind the subject
        if v.dot(fwd) / d < coshw:
            continue                                   # out of this frame
        worst = min(worst, max(0.0, min(1.0, d / (NEAR_K * max(extent, 0.05)))))
    return worst


def over_walk(cor, x, y, z, pad=0.16, h=CORRIDOR_H):
    """True if a solid at (x,y,z) would stand in a walking line."""
    for dx, dy in ((0, 0), (pad, 0), (-pad, 0), (0, pad), (0, -pad),
                   (pad * .7, pad * .7), (-pad * .7, pad * .7),
                   (pad * .7, -pad * .7), (-pad * .7, -pad * .7)):
        t = cor.top_at(x + dx, y + dy)
        if t is not None and t - 0.12 <= z <= t + h:
            return True
    return False
