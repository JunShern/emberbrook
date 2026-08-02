"""gate_lib.py — shared terrain / corridor model for the Gate Approach district.

Used by `gate_build.py`, `gate_light.py` and `gate_shots.py` so all three agree
on where the ground is.  Imported inside a Blender session that has the master
(or the gate BRANCH copy) open.

Jurisdiction (parcel `p-gate`):  x 1.5..31.8,  y 0..12.5,  z ~22.5..27.5.
Coordinate contract is the town's:  x = along-gorge (upstream is -x, and the
overworld road arrives from there), y = out from the town cliff (0) toward the
river, z = height.  The gate tier is the highest terrace in Dellhollow: the road
comes down the valley, crosses the Porters' Yard (x~6), pays at the Gatehouse
(x~11.3), passes the Valley Gate arch (x~16.7) and runs east along a corbelled
gallery to the Cargo Winch head (x~27.3), where everything the town eats is
lowered 23 m to the quay.

Two ground regimes, and the boundary between them is what the whole district
hangs on:

  * WEST of x~19 nothing at all is built under the shelf, so the ground is a
    solid rock promontory: a mass that plunges from the shelf lip to well below
    the river.  That is the "rim rock" the parcel camera note asks arrival to be
    framed on.
  * EAST of x~19 the town is already stacked underneath — the Inn and the Item
    Shop blockout shells sit at z 19..23.55 and the gate->inn stairs descend
    right through the same plan — so the ground there can only be a THIN PLATE
    whose underside clears those roofs (23.60), carried on corbels.  Its plan
    footprint is derived from the walk graph, never guessed: the plate may not
    overhang any walk surface that is within 2 m below it, or the master's
    headroom gate fails.
"""
import bpy, math
from mathutils import Vector

import sys
sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import Corridor, dist_poly2, point_in_poly, plane_z_fn, world_bbox

# ------------------------------------------------------------------ extents
GX0, GX1 = -3.22, 29.60         # ground sheet, x
GY0, GY1 = -0.30, 12.50         # ground sheet, y  (parcel lip)
# GX0 WENT 1.20 -> -3.22 on 2026-08-02 (USER REDLINE #4, "the path should extend
# past that bottom edge").  MEASURED, not chosen: un-projected through the solved
# `gate` camera, the frame's own bottom edge crosses the tier plane z=24 at
# x = 0.8 + 0.106*(y - 7.6) — i.e. essentially AT the old sheet edge.  A road that
# stopped at x=1.20 therefore stopped 0.2-5% of frame height above the bottom of
# the picture and showed the player its own rim: the "dead end" read the redline
# is about.  The extra 4.4 m puts the crossing INSIDE the sheet, so the road is cut
# by the frame instead of by the world.  Everything the extension adds below the
# road (the west-facing skirt down to BASEZ) projects BELOW the frame edge and is
# never in shot — checked with the same un-projection, and it is the reason this
# was cheap.
# THE EXACT VALUE IS LATTICE-ALIGNED, not round: -3.22 = 1.20 - 13 x ST (0.34), the
# ground sheet's own cell size.  At a round -3.20 the extended lattice lands 0.02 m
# off the old one everywhere and NOTHING east of the extension can be compared
# column-for-column with what shipped — gate_roadchop's "the edit stayed in its
# lane" gate shared zero columns and could prove nothing.
SHELF = 24.00                   # nominal tier height
PLATE_BOT = 23.60               # underside of the eastern gallery plate
BASEZ = -8.00                   # foot of the promontory (never in shot)
SOLID_X = 18.20                 # promontory / plate boundary
HIGH_Z = 23.85                  # a walk at or above this is "on the gate tier"
DECK_DROP = 0.050               # paving sits this far UNDER the walk top, so the
                                # walk QA's down-ray still lands on the walk mesh
CORRIDOR_H = 2.05               # headroom band the QA measures over a walk


# --------------------------------------------------------------- the corridors
# ------------------------------------------------- the western approach spine
# THE ROAD BEYOND THE LAST LANDMARK.  The map's walk graph stops at the
# `valley-road` pad (the mouth, where the overworld exit stands); the road itself
# has to keep going, out of the parcel and off the bottom of the gate frame, or
# the player is looking at a carriageway that ends in mid-air two metres short of
# the picture edge.  This polyline is that continuation, and it lives HERE rather
# than in `gate_build.py` for the same reason `Terrain.rim` does: three tools lay
# geometry on it (the ground clamp, the carriageway, the parapet search) and a
# spine edited in one of them and stale in the others is a silent defect.
#
# It is a STRAIGHT CONTINUATION of the map edge's own tangent at the mouth
# (`valley-gate__valley-road`, waypoint (6.3, 6.6) -> pad (1.6, 6.2): dy/dx
# 0.085), carried west to the sheet's new edge.  A curve here would be invention;
# the road's shape is the map's business and this is only its extrapolation.
SPINE = [(-3.60, 5.76), (-0.80, 5.99), (1.60, 6.20), (4.20, 6.42)]
SPINE_Z0 = 24.07          # the tier walk ribbons' own top, at the mouth (x=1.6)
SPINE_FALL = 0.040        # m of drop per m of westing: the road leaves the
                          # clifftop town for the valley, so it falls away — and
                          # a road that falls crosses the frame edge sooner,
                          # which is the redline's whole point.


def spine_d(x, y):
    """Plan distance to the approach spine's centreline."""
    best = 1e9
    for i in range(len(SPINE) - 1):
        (ax, ay), (bx, by) = SPINE[i], SPINE[i + 1]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / L2))
        best = min(best, math.hypot(x - (ax + t * vx), y - (ay + t * vy)))
    return best


def spine_top(x):
    """The walk-surface height the spine's carriageway is laid under."""
    return SPINE_Z0 - SPINE_FALL * max(0.0, SPINE[2][0] - x)


def corridors():
    walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
    return walks, Corridor(walks, margin=0.0), Corridor(walks, margin=0.30), \
        Corridor(walks, margin=0.55)


class Terrain:
    """Ground height + footprint mask for the gate tier."""

    def __init__(self):
        self.walks, self.cor0, self.cor, self.keep = corridors()
        # every upward walk face, split into "on the tier" and "below the tier"
        self.high = []      # (raw_poly, zfn, ztop)
        self.low = []
        for poly, fn, raw, nm in self.cor0.tops:
            zt = sum(p.z for p in raw) / len(raw)
            if not (GX0 - 3.0 <= sum(p.x for p in raw) / len(raw) <= GX1 + 6.0):
                continue
            if sum(p.y for p in raw) / len(raw) > GY1 + 3.0:
                continue
            (self.high if zt >= HIGH_Z else self.low).append((raw, fn, zt, nm))
        # the lower walks that matter for headroom: anything whose surface is
        # within the 2 m band under the plate (the gate->inn stairs).  A walk 4 m
        # below the plate can be built over; one 1 m below cannot.
        self.hot = [(raw, fn, zt, nm) for raw, fn, zt, nm in self.low
                    if zt > PLATE_BOT - CORRIDOR_H]
        self._ylo = {}
        self._rim = None

    # ---------------------------------------------------------------- the lip
    def rim(self, x):
        """Outer (gorge-side) lip of the shelf.

        A verge off the road's own edge the whole way, with a deliberate notch at
        the winch: the Waterfront's `cargo_winch_foot` already carries its hoist
        rope up to (28.70, 10.04, 25.03), so the shelf has to let go before
        y=10.6 or the rope would come out of the ground.

        THE ENTRY ROAD (user redline #4, 2026-08-02).  The first two control
        points went (1.2, 12.46), (9.5, 12.46), (10.6, 12.10) -> (1.2, 9.20),
        (10.6, 9.05): the numbers are REDLINE #3's own derived blue line, and #4
        is what unblocked them ("narrowing to a road is the chop, done for the
        right reason").  They were blocked before because 53.8% of the pixels the
        blue line cut stood on `walk_lm_porters-yard`'s 8 x 8 m pad and the yard
        was under a do-not-cut ruling; the yard is now deleted from the map, so
        the protected thing does not exist.  What is left over x 1.2..10.6 is a
        3.74 m carriageway centred on y ~= 6.3 with ~0.7 m of verge to this lip,
        which is where `gate_parapet` now stands — a guard rail at the road's
        shoulder instead of 4 m out on empty apron.

        THE APRON CHOP (user redline, left ellipse of
        docs/qa/refs/user_gate_tier_annotated.png: "Unused space, just chop off
        to keep the lane narrow, replace with the more-realistic cliff face?").
        East of the yard the tier ran 4.1-6.1 m past the northernmost walk
        record — measured per 1 m column off del-cine/scene.glb's 37 tier walk
        meshes, DAYLOG 2026-08-02.  The yard itself is NOT cut: over x 1.2..10
        `walk_lm_porters-yard` genuinely reaches y=12.00 against this 12.46 rim,
        0.46 m of slack, so the bay stays.  The new lip holds a ~1.5 m verge off
        the road ribbon's own edge from x=11.5 and rejoins the authored rim at
        the winch (x=26.8).  Deliberately NOT chased column-by-column: a rim
        scalloped onto every leg of the walk graph reads as a machined edge, and
        the shoulder is a minimum, not a target.  `gate_ground` skirts "wherever
        the sheet stops", so the cut face IS the more-realistic cliff face the
        redline asks for; `gate_parapet` is placed by walking outward from
        `T.rim`, so the guard follows the new lip; rim vegetation clones off the
        same function.
        """
        P = [(1.2, 9.20), (10.6, 9.05), (11.5, 9.60),
             (13.0, 8.40), (16.0, 7.10), (19.0, 8.60), (22.0, 9.50),
             (25.0, 10.05), (26.8, 10.25), (27.6, 9.95),
             (30.2, 9.95), (31.9, 10.40)]
        if x <= P[0][0]:
            return P[0][1]
        for i in range(len(P) - 1):
            (x0, y0), (x1, y1) = P[i], P[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0)
                return y0 + (y1 - y0) * (t * t * (3 - 2 * t))
        return P[-1][1]

    # ------------------------------------------------- the plate's south edge
    def ylo(self, x):
        """South (cliff-side) edge of the ground east of the promontory.

        Derived from the walk graph, not chosen: it is the gate road's own south
        edge, pushed north of anything the gate->inn stairs put within 2 m below
        the plate.  A plate that overhangs a tread by even 0.3 m eats that
        tread's headroom and the master gate fails.
        """
        k = round(x, 2)
        if k in self._ylo:
            return self._ylo[k]
        v = self._ylo_raw(x)
        # the road ribbons are discrete quads, so the raw edge saw-tooths by
        # ~0.4 m; smooth it, then re-apply the stair constraint as a hard floor
        # (smoothing may never move the plate back over a tread).
        s = sum(self._ylo_raw(x + dx) for dx in (-0.6, -0.3, 0.0, 0.3, 0.6)) / 5.0
        v = max(v, s) if self._stair(x) is not None else min(v, s)
        st = self._stair(x)
        if st is not None:
            v = max(v, st + 0.15)
        self._ylo[k] = v
        return v

    def _stair(self, x):
        stair = None
        for raw, fn, zt, nm in self.hot:
            xs = [p.x for p in raw]
            if min(xs) - 0.40 <= x <= max(xs) + 0.40:
                v = max(p.y for p in raw)
                stair = v if stair is None else max(stair, v)
        return stair

    def _ylo_raw(self, x):
        road = None
        for raw, fn, zt, nm in self.high:
            xs = [p.x for p in raw]
            if min(xs) - 0.01 <= x <= max(xs) + 0.01:
                v = min(p.y for p in raw)
                road = v if road is None else min(road, v)
        stair = self._stair(x)
        if road is None:
            road = 4.6
        if stair is None:
            return road - 1.8           # no tread below: a generous shoulder
        return max(road, stair + 0.15)

    def has_ground(self, x, y):
        if not (GX0 - 1e-6 <= x <= GX1 + 1e-6 and GY0 - 1e-6 <= y <= GY1 + 1e-6):
            return False
        # west of the boundary the promontory's face plunges past the lip and
        # needs the extra band to fall in; the eastern plate just stops at it.
        if y > self.rim(x) + (1.35 if x <= SOLID_X + 0.80 else 0.0):
            return False
        if x <= SOLID_X:
            return True
        # The eastern plate is a FLAT gallery at the tier's own level: it may not
        # descend, so it may not exist over any lower walk it would have to
        # terrace down to.  (The first pass let it follow the gate->inn stairs
        # down and it came to rest ON the shop road 5 m below — the down-ray QA
        # named all eight samples.)
        if y < self.ylo(x) - 1e-6:
            return False
        for raw, fn, zt, nm in self.low:
            if dist_poly2(x, y, raw) < 0.95:
                top = self.cor0.top_at(x, y)
                if top is None or top < zt + 0.05:
                    return False
        return True

    # -------------------------------------------------------------- the shape
    def natural(self, x, y):
        """The tier before the walk graph gets a vote: a shelf that leans very
        slightly out to the gorge with a rock swell against the cliff."""
        n = (math.sin(x * 0.51 + y * 0.77) * 0.42 +
             math.sin(x * 1.63 - y * 1.21) * 0.20 +
             math.sin(x * 3.11 + y * 2.53) * 0.07) * 0.30
        h = SHELF + 0.16 - 0.014 * max(0.0, y - 2.0)
        # a rock swell along the cliff foot (y<2.2) so the tier is not a table
        d = max(0.0, 2.6 - y)
        h += 0.55 * d * d / 6.76
        # the ground rises into a bluff at the west end: the road comes round it,
        # and it stops the eye from walking off the edge of the parcel.
        if x < 6.2:
            u = min(1.0, (6.2 - x) / 4.6)
            h += 5.4 * u * u * (1.0 - 0.30 * u) * (1.0 if y < 4.6 else
                                                   max(0.0, 1.0 - (y - 4.6) / 3.4))
        return h + n

    def clamp(self, x, y, h):
        """No ground may stand over a walk surface, and it may only climb away
        from one at ~49 deg (manifest 38/74)."""
        for raw, fn, zt, nm in self.high:
            d = dist_poly2(x, y, raw)
            if d < 4.2:
                h = min(h, self.plane_at(raw, fn, x, y, d) + d * 1.15 - DECK_DROP)
        # A walk BELOW the tier is a disjunction, not a ceiling: ground may lie
        # under it (terraced) or clear over it by the full 2 m corridor, but
        # never inside the band between.  Treating it as a ceiling is what
        # dragged the whole eastern gallery down onto the shop road at z=19.
        for raw, fn, zt, nm in self.low:
            if x > SOLID_X:
                break                            # the gallery plate never terraces
            d = dist_poly2(x, y, raw)
            if d >= 2.2:
                continue
            top = self.cor0.top_at(x, y)
            if top is not None and top > zt + 0.05:
                continue                         # buried under a higher walk
            lo = zt + d * 1.15 - DECK_DROP
            if lo < h < zt + CORRIDOR_H + d * 0.6:
                h = lo
        return h

    @staticmethod
    def plane_at(raw, fn, x, y, d):
        if d <= 0.0:
            return fn(x, y)
        # evaluate the walk's own plane at the nearest point on it, never
        # extrapolated metres away (a 20 deg ramp extrapolates to nonsense)
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

    def top(self, x, y):
        h = self.clamp(x, y, self.natural(x, y))
        # past the lip the promontory falls away; the plate simply stops
        over = y - self.rim(x)
        if over > 0.0 and x <= SOLID_X + 0.8:
            h -= 30.0 * (over ** 1.30)
        return max(h, BASEZ)

    # ------------------------------------------------------- what is below us
    def under_building(self, x, y):
        for ob in bpy.data.objects:
            if not ob.name.startswith("lm_"):
                continue
            if ob.name.startswith(("lm_gatehouse", "lm_valley-gate", "lm_winch-head")):
                continue        # these are mine to remove
            b = world_bbox(ob)
            if b[4] > SHELF - 0.30:
                continue
            if b[0] - 0.55 <= x <= b[1] + 0.55 and b[2] - 0.55 <= y <= b[3] + 0.55:
                return True
        return False

    def bottom(self, x, y, t):
        base = PLATE_BOT if (x > SOLID_X - 1.4 and self.under_building(x, y)) else BASEZ
        if x > SOLID_X:
            base = max(base, PLATE_BOT)
        elif x > SOLID_X - 2.6:
            u = (x - (SOLID_X - 2.6)) / 2.6
            base = base * (1 - u) + max(base, PLATE_BOT) * u
        return min(base, t - 0.35)


# ==========================================================================
# THE REVIEW CAMERAS — and the near-field rule that depends on them
# ==========================================================================
# The shot list lives HERE rather than in `gate_shots.py` because the BUILD
# needs it.  A 1.3 m autumn clump standing 3.8 m from the lens is 12% of a
# frame; the same clump at 20 m is scenery.  Density and size are therefore not
# properties of a zone, they are properties of a zone SEEN FROM SOMEWHERE, and
# a placer can only apply that rule if it knows where the eyes are.  One dict,
# imported by the build and by the shot script, so a camera can never be moved
# in one of them and left stale in the other.
SHOTS = {
    # ARRIVAL — the game's first-ever frame of Dellhollow.  It stands on the
    # Porters' Yard gorge shoulder looking back across the road at the gate, so
    # that (a) the Gatehouse falls to the RIGHT of the arch instead of squarely
    # in front of it, (b) the arch's north pier has open gorge and sky behind it
    # instead of 20 m of cliff, and (c) the road the player walked in on sweeps
    # through the bottom of the frame.  The eye-level version (v1-v6) put the
    # camera inside a 4 m slot between the toll house and the arch pier with
    # every roofline in the district crossing the top of the frame in one band,
    # which is exactly why it read as a murky corridor with no subject.
    "arrival":   dict(pos=(3.10, 13.80, 29.55), aim=(16.45, 4.40, 26.10), fov=46, fit='H'),
    # the parcel's own draft camera: from inside the town looking back upstream at
    # the arch, arrival framed on rim rock
    "gate":      dict(pos=(24.20, 12.30, 28.40), aim=(16.30, 4.30, 25.60), fov=40, fit='V'),
    # standing in the gateway, looking into Dellhollow: the gallery, the winch and
    # the drop.  This is what the town IS, from its front door.
    "throughgate": dict(pos=(17.95, 4.95, 25.80), aim=(28.00, 8.60, 23.90), fov=46, fit='H'),
    # the toll house three-quarter, from the yard
    "tollyard":  dict(pos=(8.20, 8.60, 26.90), aim=(13.20, 2.90, 25.30), fov=44, fit='V'),
    # the Cargo Winch head from the gallery, with the rope going over
    "winch":     dict(pos=(22.90, 4.30, 26.55), aim=(28.60, 8.10, 24.50), fov=44, fit='V'),
    # the Porters' Yard from its gorge shoulder, bluff behind
    "yard":      dict(pos=(14.60, 15.80, 28.60), aim=(5.00, 6.00, 24.60), fov=46, fit='H'),
    # the promontory from out over the gorge: the tier has to STAND on something
    "fromgorge": dict(pos=(20.00, 44.00, 24.00), aim=(11.00, 6.00, 21.00), fov=44, fit='H'),
    # from the Boatyard's water, looking up at the gate tier — the town's silhouette
    "fromquay":  dict(pos=(42.00, 27.00, 15.00), aim=(16.00, 6.50, 24.20), fov=46, fit='H'),
    # the v10 Boatyard hero camera, unchanged — value continuity against
    # boatyard_v10.png / waterfront_v7_continuity.png
    "continuity": dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
}

# the frames that stand INSIDE the district — the ones that have a near field at
# all.  `fromgorge`, `fromquay` and `continuity` are 25-60 m out and have none.
HERO = ("arrival", "gate", "throughgate", "tollyard", "winch", "yard")
HERO_EYES = [Vector(SHOTS[n]["pos"]) for n in HERO]

# THE NEAR FIELD is not a radius.  Two earlier cuts of this rule got it wrong in
# opposite directions: absolute radii around six eyes stripped the grass tufts
# along with the 1.4 m autumn clumps, and then a pure distance/size ratio
# deleted every tree in the district, because in a 30 m parcel a 4 m crown is
# always within nine of its own lengths of SOME camera.  What separates an
# obstruction from scenery is not how big it is or how close, it is WHERE IT
# STANDS RELATIVE TO THE SUBJECT: a crown behind the gate is the skyline, the
# same crown between the lens and the gate is a wall.  So the test is per
# camera — in frame, and in front of the subject — and only then about size.
NEAR_FRAC = 0.85        # props at 85% of the camera-to-subject distance are scenery
NEAR_K = 3.20           # ... and inside that, a prop may not stand closer than
                        # 3.2x its own extent (roughly 18 deg of a 46 deg frame)

_FRUSTA = []
for _n in HERO:
    _s = SHOTS[_n]
    _eye = Vector(_s["pos"])
    _fwd = (Vector(_s["aim"]) - _eye)
    _sub = _fwd.length
    _fwd = _fwd.normalized()
    # a cone around the aim, widened past the nominal fov so a prop half out of
    # frame still counts (it is the half that is IN frame that ruins the shot)
    _FRUSTA.append((_eye, _fwd, _sub, math.cos(math.radians(_s["fov"] * 0.62))))


def hero_dist(x, y, z):
    p = Vector((x, y, z))
    return min((p - e).length for e in HERO_EYES)


def near_field(x, y, z, extent=1.0):
    """The fraction of full size and full density a loose prop may have here.

    `extent` is the prop's largest dimension in metres.  1.0 means "nothing in
    this district's hero frames objects to it"; 0.0 means it stands between a
    lens and its subject at a size that frame cannot carry.  Used as BOTH a
    keep-probability and a size ceiling, which is the point: what survives near
    a camera survives SMALL, so thinning does not merely leave fewer objects of
    the wrong size.
    """
    p = Vector((x, y, z))
    worst = 1.0
    for eye, fwd, sub, coshw in _FRUSTA:
        v = p - eye
        d = v.length
        if d < 1e-4 or d >= sub * NEAR_FRAC:
            continue                                   # at/behind the subject: scenery
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
