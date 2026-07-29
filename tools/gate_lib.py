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
GX0, GX1 = 1.20, 29.60          # ground sheet, x
GY0, GY1 = -0.30, 12.50         # ground sheet, y  (parcel lip)
SHELF = 24.00                   # nominal tier height
PLATE_BOT = 23.60               # underside of the eastern gallery plate
BASEZ = -8.00                   # foot of the promontory (never in shot)
SOLID_X = 18.20                 # promontory / plate boundary
HIGH_Z = 23.85                  # a walk at or above this is "on the gate tier"
DECK_DROP = 0.050               # paving sits this far UNDER the walk top, so the
                                # walk QA's down-ray still lands on the walk mesh
CORRIDOR_H = 2.05               # headroom band the QA measures over a walk


# --------------------------------------------------------------- the corridors
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

        Wide over the Porters' Yard — the yard's own landmark pad runs out to
        y=12.0 — then drawing in as the tier narrows east, with a deliberate
        notch at the winch: the Waterfront's `cargo_winch_foot` already carries
        its hoist rope up to (28.70, 10.04, 25.03), so the shelf has to let go
        before y=10.6 or the rope would come out of the ground.
        """
        P = [(1.2, 12.46), (9.5, 12.46), (12.5, 12.10), (16.0, 11.55),
             (20.0, 11.10), (24.5, 10.60), (26.8, 10.25), (27.6, 9.95),
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


def over_walk(cor, x, y, z, pad=0.16, h=CORRIDOR_H):
    """True if a solid at (x,y,z) would stand in a walking line."""
    for dx, dy in ((0, 0), (pad, 0), (-pad, 0), (0, pad), (0, -pad),
                   (pad * .7, pad * .7), (-pad * .7, pad * .7),
                   (pad * .7, -pad * .7), (-pad * .7, -pad * .7)):
        t = cor.top_at(x + dx, y + dy)
        if t is not None and t - 0.12 <= z <= t + h:
            return True
    return False
