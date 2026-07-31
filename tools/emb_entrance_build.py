"""emb_entrance_build.py — THE VILLAGE ENTRANCE, the parcel the game OPENS on.

    Blender -b tools/blends/emberbrook-entrance-wip.blend -P tools/emb_entrance_build.py \
        --python-exit-code 1 -- [save] [--digest]

WHAT THIS IS.  `tools/emb_blockout.py` raises the whole town from the map as gray
massing; `tools/emb_square_build.py` is the pattern this file follows exactly, one
parcel east and one district later.  This pass takes the `p-entrance` PARCEL
(`road-gate`, `waystone`, `orchard`) and builds it for real.  It is the second real
district of Emberbrook and it is built in PARALLEL with the square, on a copy of the
frozen blockout, which is why every line of the prefix contract below is absolute:
the two districts are re-assembled later by name, not by hand.

WHY THIS PARCEL MATTERS MORE THAN ITS SIZE.  `mapDiscovery.startRevealed` is
`["p-entrance"]` and `chapter1.js` spawns Act I on the south road: this is the FIRST
VIEW OF THE GAME WORLD.  Vesper walks in from the valley at dusk on Emberwake with the
river she has followed for weeks falling away east, the arch is the threshold she comes
through, and the waystone is where a cat hires himself to her.  The map's own camera
note asks for the reverse of that walk — "from inside the village looking back down the
road through the arch, orchard rows framing, valley haze beyond" — so this district has
to read from BOTH ends of the same road.  Everything below is composed for that pair.

THE REFERENCE IS SHIPPED ART.  `public/assets/scenes/entrance/main.png` is the accepted
Chapter One painting of this exact place: the mossy carved waystone on the WEST verge
with the dark wood behind it, the heavy low timber arch with its brace and its hanging
lantern, bunting and little lanterns strung off it toward the lit houses, a palisade
running off both posts, autumn trees with greens still in them, the road glowing warm
inside the village and cold outside it.  Every element here is transcribed from it onto
the map's own coordinates.

THE ONE THING IT DOES NOT TOUCH IS THE WALK NETWORK.  Coverage is proved BY MESH NAME
against the map (`walk_pad_road-gate`, `walk_lm_orchard`, `walk_e_<from>__<to>_*`); the
blockout already emits exactly those, already cut around every footprint, and every
camera solved against them is solved against the floor the player actually walks.  This
file owns the ART.  If a footprint must move it moves IN THE MAP and the blockout
re-runs — which is why finding 1 below is a REDLINE and not a re-cut floor.

PREFIX OWNERSHIP, and it is asserted rather than assumed: this pass clears `emb_en_`,
`bar_emb_en_`, `veg_emb_en_` and `KEYEN_` ONLY, plus the `lm_<member>_*` massing of its
own three members.  It never touches `emb_lamp_*` (the blockout's 15-lamp ring, which
stages Lake's rounds and is map canon), `emb_ground_*`, `water_*`, any blockout
`walk_`/`bar_`, or any `emb_sq_*` (the flagship's square, built in parallel).

FINDINGS THIS PASS PAID FOR, both of them measured before anything was built:

 1  THE MAP'S WAYSTONE COORDINATE STANDS IN THE ROAD.  `waystone` is authored at
    (27, 9); the blockout runs `walk_e_road-gate__waystone` doorstep-to-doorstep
    through (28.6, 6.5) and the ribbon's 2.4 m width covers that point.  Measured with
    the gate's own sampler, a stone of ANY radius at (27, 9) — even 0.30 m — is refused,
    and the blockout's own `lm_waystone` is therefore standing on walkable road (it is
    one of the three intersection offenders the region audits at HEAD).  This pass does
    not re-cut the ribbon and does not silently move a landmark: it SEARCHES outward
    from the map point for the nearest seat where the marker's real footprint is clear,
    prints the offset as a MAP REDLINE for the coordinator, and lands the stone there —
    on the west verge, which is where the painting puts it and where a waystone belongs.
    The search returns the map point unchanged the moment the map is corrected, so the
    fix is a one-line map edit and a blockout re-run, and this file follows it for free.

 2  THE ARCH AND THE LAMP ARE THE SAME 40 CM.  `emb_lamp_00_road-gate` was foot-searched
    by the blockout to (31.90, 4.00) and the blockout's own `lm_road-gate_postR` box is
    drawn at (31.70, 4.00) — the lamppost is INSIDE the gatepost.  The blockout offsets
    its arch posts on the world x axis while rotating only the boxes; the real arch is
    set out on the road's own normal, which moves the east post to (31.66, 4.93) and
    clears the lamp by 0.96 m.  The lamp is map canon and never moves; the arch is mine
    and does.

DETERMINISM IS A GATE: no `random`, no time, no `bpy.ops` primitives.  Variation comes
from `h01()`, an integer hash of the object's own index.  `-- --digest` prints a digest
of THIS DISTRICT'S OWN objects (not the whole scene, which the flagship is editing in
parallel in its own copy) so two runs can be diffed, plus the untouched walk network's
digest, which must equal the frozen blockout's.
"""
import bpy, json, math, os, sys, hashlib
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from district_lib import GateGrid, WalkGuard, bvh_of, ground_z as bvh_ground_z

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DIGEST = "--digest" in argv

D = json.load(open(os.path.join(REPO, "public/townmap/emberbrook.map.json")))
LM = {l["id"]: l for l in D["landmarks"]}
PARCEL = next(p for p in D["parcels"] if p["id"] == "p-entrance")
MEMBERS = [m for m in PARCEL["members"] if m in LM]
B = PARCEL["bounds"]

# THE REGION IS WIDER THAN THE PARCEL, DELIBERATELY, AND IT IS DECLARED HERE.
# The parcel is the WALKABLE ground (x 12..34, y 0..15).  Two composition bands hang off
# it and neither is walkable or claimed by any other parcel (asserted below):
#   * the SOUTH APPROACH, y -15..0 — the valley the player arrives out of, and the only
#     way "beyond the arch" can be anything but empty grass (impliedScale technique 1);
#   * the EAST FALL, x 34..44 — the ground dropping to the river Vesper followed, which
#     the map places at centre x 57 and which is the reason this frame has a horizon.
# A guard must cover every place its caller builds (district_lib's own lesson), so the
# gate grid is built over all of it.
REGION = (10.0, 44.0, -15.0, 17.0)

MINE = ("emb_en_", "bar_emb_en_", "veg_emb_en_", "KEYEN_")
COLL = "EMB_ENTRANCE"

print("=" * 78)
print("THE VILLAGE ENTRANCE — the parcel the game opens on")
print("=" * 78)
print("  parcel %s  members: %s" % (PARCEL["id"], ", ".join(MEMBERS)))
print("  parcel bounds x %.1f..%.1f  y %.1f..%.1f" % (B["min"][0], B["max"][0],
                                                     B["min"][1], B["max"][1]))
print("  build region  x %.1f..%.1f  y %.1f..%.1f  (+ south approach, + east fall)"
      % REGION)

# PREFIX SAFETY, asserted: none of my prefixes may swallow the lamp ring, the ground,
# the water, the walk network or the flagship's square.  This is the assertion that
# keeps it true if a prefix is ever shortened.
for p in MINE:
    assert not p.startswith(("emb_l", "emb_g", "emb_s", "water", "walk")), \
        "prefix %r would swallow blockout or flagship geometry" % p
    assert not ("emb_sq_".startswith(p) or p.startswith("emb_sq_")), \
        "prefix %r collides with the square" % p
FORBIDDEN = ("emb_lamp_", "emb_ground_", "emb_pondbed_", "emb_culvert_", "emb_lanestub_",
             "water_", "walk_", "emb_sq_", "KEYSQ_", "KEYEMB_")


def protected(name):
    """True for anything this pass must never delete or rename.  `bar_emb_en_` is mine;
    every other `bar_` in the town is the blockout's."""
    if name.startswith("bar_"):
        return not name.startswith("bar_emb_en_")
    return name.startswith(FORBIDDEN)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def M(name):
    m = bpy.data.materials.get(name)
    assert m is not None, "material %r missing — run tools/emb_blockout.py first" % name
    return m


MAT = {k: M("emb_mat_" + k) for k in
       ("grass", "earth", "road", "cobble", "stone", "timber", "plaster", "thatch",
        "slate", "tile", "leaf_autumn", "leaf_green", "iron", "window", "lamp_glass")}


def newmat(name, rgba, rough=0.85, emit=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = emit[0]
        b.inputs["Emission Strength"].default_value = emit[1]
    return m


# POPS OF COLOUR, 5-10% of frame (docs/plans/pops-of-color.md).  Out here the budget is
# spent on exactly three things and all three are the harvest festival: the apples on the
# trees and in the baskets, the bunting flags, and the wreaths' berries.  Everything else
# is timber, stone, straw and leaf.  Materials carry the district's own `_en_` infix so a
# merge can never confuse them with the square's awning palette.
MAT["apple"] = newmat("emb_mat_en_apple", (0.62, 0.13, 0.10, 1))
MAT["moss"] = newmat("emb_mat_en_moss", (0.20, 0.29, 0.14, 1), rough=0.95)
MAT["straw"] = newmat("emb_mat_en_straw", (0.58, 0.47, 0.24, 1))
MAT["cloth_red"] = newmat("emb_mat_en_cloth_red", (0.55, 0.15, 0.12, 1))
MAT["cloth_cream"] = newmat("emb_mat_en_cloth_cream", (0.82, 0.76, 0.62, 1))
MAT["cloth_green"] = newmat("emb_mat_en_cloth_green", (0.22, 0.34, 0.16, 1))
MAT["cloth_blue"] = newmat("emb_mat_en_cloth_blue", (0.12, 0.20, 0.40, 1))
MAT["beam"] = newmat("emb_mat_en_beam", (0.23, 0.15, 0.09, 1))
MAT["pumpkin"] = newmat("emb_mat_en_pumpkin", (0.70, 0.29, 0.07, 1))
MAT["waystone"] = newmat("emb_mat_en_waystone", (0.33, 0.32, 0.29, 1), rough=0.95)
# a three-hundred-year-old incision is a SHADOW, not a line: barely darker than the
# stone, because "the carved face is worn nearly smooth" is shipped dialogue
MAT["carve"] = newmat("emb_mat_en_carve", (0.31, 0.30, 0.28, 1), rough=0.98)
# the little hanging lanterns are PAPER, not the lamp ring's glass: a fifth of the
# emission, or the string of them blows out every frame they hang in
MAT["paper"] = newmat("emb_mat_en_paper", (1.0, 0.80, 0.52, 1), rough=0.4,
                      emit=((1.0, 0.70, 0.34, 1), 5.0))

# MEMBERSHIP IS BY PARCEL MEMBER, NEVER BY DISTRICT — the Home Row lane's near-miss,
# relayed by the coordinator while this pass was building.  `district: "homerow"` also
# names two implied-scale vista clusters and a closed lane; a build that retires "every
# lm_ in my district" deletes them, and NOTHING in any district builder puts them back.
# This parcel would lose exactly the depth its opening shot is made of: `river-vista` and
# `east-cottages` both carry `district: entrance`-adjacent roles in the map's east, and
# the entrance's own frames are 60% valley.  So the retirement list below is
# PARCEL["members"], which the map authors by hand, and the whole-scene snapshot at the
# end proves that nothing else in the town moved.
BEFORE = {o.name for o in bpy.data.objects}
DRESSING = [l["id"] for l in D["landmarks"] if l.get("class") == "dressing"
            or "closed" in (l.get("name") or "").lower()]
for mid in MEMBERS:
    assert LM[mid].get("class") != "dressing", \
        "parcel member %r is dressing — retiring its massing would delete implied scale" % mid
DRESS_BEFORE = {o.name for o in bpy.data.objects
                if any(o.name.startswith(("lm_%s_" % i, "bar_%s_" % i, "emb_lanestub_%s_" % i))
                       or o.name == "lm_" + i for i in DRESSING)}
print("  implied-scale objects in the town (vistas + closed lanes): %d, none of them "
      "mine to touch" % len(DRESS_BEFORE))

# ------------------------------------------------------------------- clearing --
removed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(MINE):
        assert not protected(o.name), "refusing to clear protected object %r" % o.name
        bpy.data.objects.remove(o, do_unlink=True)
        removed += 1
for d in list(bpy.data.lights):
    if d.name.startswith("KEYEN_") and d.users == 0:
        bpy.data.lights.remove(d)
# ... and the blockout massing this pass exists to replace.  `walk_lm_orchard` is the
# orchard's FLOOR and starts with `walk_`, so the protected() guard is what stands
# between "retire the massing" and "delete the district's walkable ground".
gone = 0
for o in list(bpy.data.objects):
    if protected(o.name):
        continue
    for mid in MEMBERS:
        if o.name == "lm_" + mid or o.name.startswith("lm_%s_" % mid):
            bpy.data.objects.remove(o, do_unlink=True)
            gone += 1
            break
for d in list(bpy.data.meshes):
    if d.users == 0:
        bpy.data.meshes.remove(d)
print("  cleared %d of my own objects, retired %d blockout massing objects"
      % (removed, gone))
coll(COLL)

# ------------------------------------------------------------------ primitives --
# Every solid here is an explicit vertex list (no bpy.ops: their vertex order has moved
# between Blender versions and this file has to be byte-stable).  Assemblies that are ONE
# THING — a gate frame, a tree, a swag of bunting — are built as one MESH with several
# material slots rather than as a bag of boxes: it halves the object count the merge has
# to carry and it stops `geometry_audit` from reporting a district's own joinery as
# interpenetration (finding 79, learned the expensive way by four Dellhollow districts).
NEW = []


class Part:
    """An accumulator for one multi-material mesh."""

    def __init__(self):
        self.v, self.f, self.fm, self.mats = [], [], [], []

    def _slot(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, verts, faces, m):
        base, s = len(self.v), self._slot(m)
        self.v.extend(tuple(x) for x in verts)
        for fc in faces:
            self.f.append(tuple(base + i for i in fc))
            self.fm.append(s)

    def box(self, cx, cy, cz, sx, sy, sz, m, rz=0.0):
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        c, s = math.cos(rz), math.sin(rz)
        v = []
        for dz in (-hz, hz):
            for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
                v.append((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz))
        self.add(v, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                     (2, 3, 7, 6), (3, 0, 4, 7)], m)

    def cyl(self, cx, cy, cz, r, h, m, seg=10, r2=None):
        r2 = r if r2 is None else r2
        v = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            v.append((cx + r * math.cos(a), cy + r * math.sin(a), cz - h / 2))
        for k in range(seg):
            a = 2 * math.pi * k / seg
            v.append((cx + r2 * math.cos(a), cy + r2 * math.sin(a), cz + h / 2))
        f = [tuple(range(seg - 1, -1, -1)), tuple(range(seg, 2 * seg))]
        for k in range(seg):
            n = (k + 1) % seg
            f.append((k, n, seg + n, seg + k))
        self.add(v, f, m)

    def beam(self, p, q, w, h, m, up=(0, 0, 1)):
        """A rectangular member between two POINTS IN SPACE — the thing a box cannot do,
        and what every brace, ladder rail, rail fence and bunting swag is made of."""
        p, q = Vector(p), Vector(q)
        d = (q - p)
        if d.length < 1e-6:
            return
        d = d.normalized()
        u = Vector(up)
        if abs(d.dot(u)) > 0.95:
            u = Vector((1, 0, 0))
        r = d.cross(u).normalized()
        u = r.cross(d).normalized()
        v = []
        for base in (p, q):
            for sr, su in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v.append(tuple(base + r * (sr * w / 2) + u * (su * h / 2)))
        self.add(v, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                     (2, 3, 7, 6), (3, 0, 4, 7)], m)

    def prism(self, base4, top4, m):
        """A tapered/leaning solid from two quads — the waystone itself."""
        self.add(list(base4) + list(top4),
                 [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                  (2, 3, 7, 6), (3, 0, 4, 7)], m)

    def quad(self, a, b, c, d, m):
        self.add([a, b, c, d], [(0, 1, 2, 3)], m)

    def ring(self, c, R, e1, e2, thick, m, seg=12):
        """A wreath: a closed chain of short members in the plane (e1, e2)."""
        e1, e2 = Vector(e1).normalized(), Vector(e2).normalized()
        pts = [Vector(c) + e1 * (R * math.cos(2 * math.pi * k / seg))
               + e2 * (R * math.sin(2 * math.pi * k / seg)) for k in range(seg)]
        for k in range(seg):
            self.beam(pts[k], pts[(k + 1) % seg], thick, thick, m)
        return pts

    def emit(self, name):
        assert self.v, "empty part %r" % name
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], [tuple(f) for f in self.f])
        me.validate()
        me.update()
        for m in self.mats:
            me.materials.append(m)
        for i, p in enumerate(me.polygons):
            if i < len(self.fm):
                p.material_index = self.fm[i]
        ob = bpy.data.objects.new(name, me)
        assert ob.name == name, "name collision on %r (Blender suffixed it)" % name
        coll(COLL).objects.link(ob)
        NEW.append(ob)
        return ob


def h32(*ints):
    h = 2166136261
    for i in ints:
        h = ((h ^ (int(i) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


def h01(*ints):
    return h32(*ints) / 4294967295.0


def appr_of(lid):
    """The direction a landmark is approached from — the blockout's own derivation, so
    the arch this pass sets out is square to the road the blockout actually drew."""
    px, py, _pz = LM[lid]["pos"]
    vx = vy = 0.0
    for e in D["edges"]:
        if e["from"] == lid:
            nb = (e.get("waypoints") or [LM[e["to"]]["pos"]])[0]
        elif e["to"] == lid:
            nb = (e.get("waypoints") or [LM[e["from"]]["pos"]])[-1]
        else:
            continue
        dx, dy = nb[0] - px, nb[1] - py
        d = math.hypot(dx, dy)
        if d > 1e-6:
            vx += dx / d
            vy += dy / d
    d = math.hypot(vx, vy)
    return (vx / d, vy / d) if d > 1e-6 else (0.0, -1.0)


# NOTHING IS EVER FOUNDED ON A GUESS (district_lib's rule, and the boatyard's scar):
# every solid this pass lands is put down on a ray-cast against the ground the blockout
# interpolated from the map's own z values.  A point with no ground under it is counted,
# not floated.
GBVH = bvh_of(lambda n: n.startswith("emb_ground_"))
NOGROUND = []


def gz(x, y, who="?"):
    z = bvh_ground_z(GBVH, x, y)
    if z is None:
        NOGROUND.append((who, round(x, 2), round(y, 2)))
        return 0.0
    return z


# The gate's OWN sampling contract, so "will this solid break the walk gate" is answered
# by the gate's instrument and not by a stricter one.  `free_box` is the corridor guard;
# it would refuse every palisade picket at the edge of the road it belongs to.
GUARD = WalkGuard(REGION)
GATE = GateGrid(REGION, GUARD)
print("  gate grid: %d walk samples inside the region (%d walk faces loaded)"
      % (len(GATE.pts), len(GUARD.faces)))
REFUSED = []


def place(what, x, y, r, z0, z1):
    """True when a solid of this footprint may stand here.  A refusal is COUNTED and
    printed, never silently skipped."""
    if GATE.clear_pt(x, y, r, z0, z1):
        return True
    REFUSED.append((what, round(x, 2), round(y, 2)))
    return False


def seat(what, x0, y0, r, z0, z1, step=0.25, rings=20):
    """The nearest place a footprint of radius `r` may stand, searched outward from the
    authored point in a deterministic square spiral.  Returns (x, y, dist).  When the
    authored point is already clear this returns it EXACTLY — so a map correction makes
    the search a no-op instead of a second, competing source of truth."""
    if GATE.clear_pt(x0, y0, r, z0, z1):
        return x0, y0, 0.0
    best = None
    for ring in range(1, rings + 1):
        cands = []
        for i in range(-ring, ring + 1):
            for j in (-ring, ring):
                cands.append((i, j))
                cands.append((j, i))
        for (i, j) in sorted(set(cands)):
            x, y = x0 + i * step, y0 + j * step
            if not GATE.clear_pt(x, y, r, z0, z1):
                continue
            d = math.hypot(x - x0, y - y0)
            if best is None or d < best[2] - 1e-9:
                best = (x, y, d)
        if best:
            return best
    REFUSED.append((what + " (no seat)", round(x0, 2), round(y0, 2)))
    return None


def in_other_parcel(x, y, pad=0.0):
    """The id of a NEIGHBOUR's parcel this point falls in, or None.  The region this pass
    gates is deliberately wider than its parcel (the two vista bands), and the square's
    own bounds reach down to y 15 at x 23..41 — so "is it in my region" is not the same
    question as "is it mine", and both have to be asked."""
    for p in D["parcels"]:
        if p["id"] == PARCEL["id"]:
            continue
        pb = p["bounds"]
        if pb["min"][0] - pad <= x <= pb["max"][0] + pad \
                and pb["min"][1] - pad <= y <= pb["max"][1] + pad:
            return p["id"]
    return None


def in_region(x, y, margin=0.0):
    return (REGION[0] + margin <= x <= REGION[1] - margin
            and REGION[2] + margin <= y <= REGION[3] - margin)


# A CROWN IS NOT A TRESPASS.  Containment is measured twice below and the two questions
# are different: an object's CENTRE must be inside the declared region and outside every
# neighbour's parcel, while its BOUNDING BOX may reach this much further — because a tree
# planted a metre inside the line still hangs three metres of leaf over it, and demanding
# otherwise plants the orchard in a smaller field than the map authored.
FOLIAGE = 3.4


def world_centre(o):
    """The centre of a mesh IN WORLD SPACE, from its vertices.  `matrix_world.translation`
    is NOT that here and the difference is silent: the blockout bakes world coordinates
    into every mesh and leaves the object at the origin, so asking a lamppost where it is
    via its transform answers (0, 0, 0) — which is 30 m outside this district and reads as
    "no lamps in the region" rather than as a bug."""
    P = [o.matrix_world @ v.co for v in o.data.vertices]
    return ((min(p.x for p in P) + max(p.x for p in P)) / 2,
            (min(p.y for p in P) + max(p.y for p in P)) / 2,
            (min(p.z for p in P) + max(p.z for p in P)) / 2)


# THE ANCHOR IS A REAL CAMERA AT A PLAYER'S EYE HEIGHT, standing ON the road beside the
# waystone: `tools/emb_entrance_shots`'s `riverlook`.  The map's words for this landmark
# are "glimpsed east of the road on arrival", so the sightline that has to stay open is
# the one a player has while walking up the road — not one a camera might be flown to.
# No frame that contains the arch can also contain the water (the arch is due south, the
# river 27 m east; at 28 mm they are 50 degrees apart at best), so the river gets its own
# look rather than a pretended one.
#
# AND THE STATIONS ARE GEOMETRY CONSTRAINTS, not documentation.  `emb_entrance_shots.py`
# stands at the four points below; a tree planted two metres in front of one fills the
# frame with leaf, and a planting grid has no idea a camera is there.  It happened twice
# — the second time to the archback frame, on a rebuild that moved the rows by 40 cm —
# so the stations are declared here and every tree this pass plants keeps clear of them.
STATIONS = [(34.90, -5.10), (31.80, 13.60), (30.60, 6.30), (27.00, 9.60)]
STATION_CLEAR = 4.2


def near_station(x, y, r=None):
    return any(math.hypot(x - sx, y - sy) < (STATION_CLEAR if r is None else r)
               for (sx, sy) in STATIONS)
CAM_ANCHOR = (27.00, 9.60, 2.20)
RIV = D.get("river") or {}
RIVER_PT = (RIV.get("centerX", 57.0), 6.2, RIV.get("level", -0.6))


def seg_d(px, py, ax_, ay_, bx_, by_):
    dx, dy = bx_ - ax_, by_ - ay_
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - ax_) * dx + (py - ay_) * dy) / L2))
    return math.hypot(px - ax_ - t * dx, py - ay_ - t * dy)


def sight_dist(x, y):
    ax_, ay_ = CAM_ANCHOR[0], CAM_ANCHOR[1]
    bx_, by_ = RIVER_PT[0], RIVER_PT[1]
    dx, dy = bx_ - ax_, by_ - ay_
    L2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((x - ax_) * dx + (y - ay_) * dy) / L2))
    return math.hypot(x - (ax_ + t * dx), y - (ay_ + t * dy))


RG = LM["road-gate"]
GX, GY, GZ0 = RG["pos"]
AX, AY = appr_of("road-gate")                       # points INTO the village (NNW)
UX, UY = -AY, AX                                    # along the arch's span
GRZ = math.atan2(AY, AX) + math.pi / 2

# =============================================================================
# 0. THE ROAD ITSELF — a skin under the walk network, because a road is continuous
# =============================================================================
# THE FINDING THAT PAID FOR THIS SECTION IS A RENDER.  The blockout's road is a chain of
# chaikin ribbons 2.4 m wide, each a separate box with a 0.14 m skirt; on the plan they
# are a road, and in a 32 mm frame at eye height they are a dozen pale slabs scattered
# across a green field with grass showing between them at every bend.  The first contact
# render of this parcel — the FIRST FRAME OF THE GAME — had no road in it.
#
# The walk network is not mine to rebuild, and it must not move: the fix is therefore a
# SKIN.  It is `emb_en_` (scenery, never walkable), it follows the map's own polyline, and
# it is 4.3 m wide against the ribbons' 2.4 so the road gets verges.  So the surface the
# player walks is still, exactly, the blockout's; the surface the camera sees is a road.
def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            out.append(tuple(p[k] * 0.75 + q[k] * 0.25 for k in range(3)))
            out.append(tuple(p[k] * 0.25 + q[k] * 0.75 for k in range(3)))
        out.append(pts[-1])
        pts = out
    return pts


def doorstep(lid):
    """Where the road actually ends up: READ OFF THE SCENE, not re-derived.

    The first version of this function reproduced `emb_blockout`'s doorstep arithmetic
    (|ax|*bw/2 + |ay|*bd/2 + 1.15 along the mean approach).  Between this district
    starting and freezing, the blockout changed BOTH halves of that — the approach is now
    the single preferred road edge rather than the mean of all edges, and the set-back is
    bd/2 + 1.15 — and `walk_pad_waystone` moved 0.94 m.  A copy of somebody else's
    formula is a copy that goes stale silently; the pad itself cannot.  So the skin's
    polyline is taken from the pad the blockout built, and this district follows the walk
    network wherever a later blockout run puts it."""
    o = bpy.data.objects.get("walk_pad_" + lid)
    if o is not None and o.data.vertices:
        c = world_centre(o)
        return (c[0], c[1], c[2])
    x, y, z = LM[lid]["pos"]                              # no pad: the doorstep is the point
    return (x, y, z)


SKIN_LONG = 0.45                                         # metres along the road
SKIN_LAT = 0.26                                          # ... and across it


def skin_z(x, y):
    """The skin's height: 20 mm over the grass out on the verge, and 40 mm UNDER the walk
    face wherever one is within a quarter of a metre.

    TWO DRAFTS DIED ON THIS ONE NUMBER and the survivor is the third.  Clamping against a
    0.9 m neighbourhood pulled the whole strip 60 mm down — under the ground mesh, which
    sits within centimetres of every walk top in this town — and the road rendered as
    nothing.  Cutting it into cells against the gate's samples rendered as a mosaic of
    280 mm tiles with a grass seam around every ribbon.  A quarter-metre probe is the
    tight version of the same idea: it reaches far enough to catch every gate sample
    (they start 175 mm inside a face, and the strip's own vertices are 260 mm apart, so
    the surface over any sample is interpolated from vertices that ALL probe into that
    face) and not so far that it drags the verges under the grass.

    THE RADIUS IS 0.40 AND NOT 0.25, and one sample bought the difference: at the
    waystone pad's north-west CORNER (25.41, 12.43) the pad's top is 0.37 while the
    interpolated ground beside it is 0.58 — a 210 mm step — so a strip vertex a quarter
    of a metre outside the corner found no face, stayed up at the grass, and the surface
    interpolated 130 mm over the sample.  Corners are where a probe ring is thinnest."""
    z = gz(x, y, "road skin") + 0.02
    w = GUARD.eff_top(x, y)
    if w is not None:
        z = min(z, w - 0.04)
    for r in (0.20, 0.40):
        for k in range(8):
            a = math.pi / 4 * k
            w = GUARD.eff_top(x + r * math.cos(a), y + r * math.sin(a))
            if w is not None:
                z = min(z, w - 0.04)
    return z


def road_skin(part, pts, width):
    """A continuous surface the width of the road AND ITS VERGES, laid over the blockout's
    ribbons and dipping under each one.  In the gaps between ribbons — which is every bend
    in the road — it is what the camera sees; over a ribbon it is 40 mm below the surface
    the player walks and 20 mm below the grass, i.e. invisible and unhittable.  Never
    walkable, never `walk_`, and re-measured by the acceptance block's own rays."""
    C = chaikin([tuple(p) for p in pts], 2)
    P = []
    for a, b in zip(C, C[1:]):
        n_ = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / SKIN_LONG)))
        for s in range(n_):
            P.append(tuple(a[k] + (b[k] - a[k]) * (s / float(n_)) for k in range(3)))
    P.append(C[-1])
    ndiv = int(math.ceil(width / SKIN_LAT))
    rows = []
    for i, p in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        row = []
        for k in range(ndiv + 1):
            t = (k / float(ndiv) - 0.5) * width
            rx, ry = p[0] + nx * t, p[1] + ny * t
            row.append((rx, ry, skin_z(rx, ry)))
        rows.append(row)
    n = 0
    for i in range(len(rows) - 1):
        for k in range(ndiv):
            part.add([rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]],
                     [(0, 1, 2, 3)], MAT["road"])
            n += 1
    return n


WSDOOR = doorstep("waystone")
SKIN = Part()
nq = road_skin(SKIN, [(GX, GY, GZ0)] + [tuple(w) for w in
                                        next(e for e in D["edges"]
                                             if e["from"] == "road-gate")["waypoints"]]
               + [WSDOOR] + [(28.5, 13.0, 0.7), (29.6, 14.4, 0.95)], 4.30)
nq += road_skin(SKIN, [WSDOOR, (23.5, 10.2, 0.45),
                       (LM["orchard"]["pos"][0] + 4.3, LM["orchard"]["pos"][1] - 0.4,
                        LM["orchard"]["pos"][2])], 3.10)
SKIN.emit("emb_en_roadskin")
print("  ROAD SKIN: %d quads, road plus verges, dipping under every ribbon it "
      "crosses (never walkable)" % nq)

# =============================================================================
# 1. THE VILLAGE ARCH — a threshold, not a gate: you walk through it
# =============================================================================
# The map calls it a PORTAL and the blockout gives portals a doorstep AT their centre:
# the arch is walked through, so its opening is a corridor and its posts are the only
# solid it may own.  Set out on the road's own normal (finding 2), 1.90 m each side of
# centre, which leaves a 3.36 m clear opening over a 2.4 m road.
ARCH_HALF = 1.90
POSTS = []
for sgn, tag in ((-1, "W"), (1, "E")):
    px, py = GX + UX * ARCH_HALF * sgn, GY + UY * ARCH_HALF * sgn
    if not place("arch_post_" + tag, px, py, 0.30, GZ0 - 0.5, GZ0 + 3.6):
        continue
    POSTS.append((tag, px, py, gz(px, py, "arch post " + tag)))
assert len(POSTS) == 2, "the arch needs both posts and the gate refused one: %s" % REFUSED

A = Part()
LIN_Z = None
for (tag, px, py, pz) in POSTS:
    # a stone footing pad, then the post: a timber gatepost with its foot out of the mud
    A.box(px, py, pz + 0.09, 0.86, 0.86, 0.40, MAT["stone"], GRZ)
    A.box(px, py, pz + 1.80, 0.38, 0.38, 3.14, MAT["timber"], GRZ)
    A.box(px, py, pz + 3.42, 0.50, 0.50, 0.10, MAT["beam"], GRZ)         # the cap
LZ = max(p[3] for p in POSTS) + 3.16                                     # lintel underside
WX, WY, _wz = POSTS[0][1], POSTS[0][2], 0
EX, EY = POSTS[1][1], POSTS[1][2]
# the lintel, its top rail and the two king posts between them: a heavy, LOW timber
# frame (the map's own word is "low"), its underside 3.16 m over the road — well clear of
# the 2.05 m corridor the walk gate keeps.
A.beam((WX - UX * 0.45, WY - UY * 0.45, LZ + 0.20),
       (EX + UX * 0.45, EY + UY * 0.45, LZ + 0.20), 0.46, 0.40, MAT["timber"])
A.beam((WX - UX * 0.30, WY - UY * 0.30, LZ + 0.72),
       (EX + UX * 0.30, EY + UY * 0.30, LZ + 0.72), 0.34, 0.22, MAT["beam"])
for k in range(3):
    t = 0.25 + 0.25 * k
    kx, ky = WX + (EX - WX) * t, WY + (EY - WY) * t
    A.box(kx, ky, LZ + 0.50, 0.16, 0.16, 0.36, MAT["beam"], GRZ)
# the knee braces the painting leans on — the detail that says "carpentry", not "arch"
for (tag, px, py, pz) in POSTS:
    sgn = -1 if tag == "W" else 1
    A.beam((px + UX * 0.10 * -sgn, py + UY * 0.10 * -sgn, LZ - 0.90),
           (px + UX * 1.05 * -sgn, py + UY * 1.05 * -sgn, LZ + 0.16),
           0.20, 0.20, MAT["timber"])
ARCH = A.emit("emb_en_arch_frame")

# HARVEST WREATHS — Emberwake, and the map's own note for this landmark ("low timber
# arch over the south road; harvest wreaths").  Three: one on each post facing the road
# out, one hung under the middle of the lintel.  The hung one clears the corridor by
# 0.5 m and is gate-checked anyway, because a wreath in a doorway is a bollard.
NW = 0
for wi, (cx, cy, cz, R) in enumerate([
        (WX + AX * 0.26, WY + AY * 0.26, POSTS[0][3] + 2.05, 0.46),
        (EX + AX * 0.26, EY + AY * 0.26, POSTS[1][3] + 2.05, 0.46),
        ((WX + EX) / 2, (WY + EY) / 2, LZ - 0.42, 0.54)]):
    if not GATE.clear_pt(cx, cy, R + 0.05, cz - R - 0.1, cz + R + 0.1):
        REFUSED.append(("arch_wreath%d" % wi, round(cx, 2), round(cy, 2)))
        continue
    W = Part()
    pts = W.ring((cx, cy, cz), R, (UX, UY, 0), (0, 0, 1), 0.13, MAT["leaf_green"], seg=14)
    for k, p in enumerate(pts):                       # berries and dried wheat, alternating
        if k % 2:
            W.box(p.x, p.y, p.z, 0.10, 0.10, 0.10, MAT["apple"], GRZ)
        else:
            W.box(p.x, p.y, p.z, 0.09, 0.09, 0.14, MAT["straw"], GRZ)
    W.beam((cx, cy, cz + R), (cx, cy, cz + R + 0.30), 0.05, 0.05, MAT["beam"])
    W.emit("emb_en_arch_wreath%d" % wi)
    NW += 1

# THE HANGING LANTERN, straight out of the painting: an ordinary flame in a small iron
# cage under the lintel.  680 W, the town standard seven districts old — Emberbrook has
# exactly ONE magical light and it is the Heartlight on the square, not this.
LNX, LNY = (WX + EX) / 2 + UX * 0.95, (WY + EY) / 2 + UY * 0.95
L = Part()
L.beam((LNX, LNY, LZ + 0.02), (LNX, LNY, LZ - 0.34), 0.05, 0.05, MAT["iron"])
L.box(LNX, LNY, LZ - 0.58, 0.28, 0.28, 0.34, MAT["lamp_glass"], GRZ)
L.box(LNX, LNY, LZ - 0.38, 0.34, 0.34, 0.07, MAT["iron"], GRZ)
L.box(LNX, LNY, LZ - 0.77, 0.30, 0.30, 0.06, MAT["iron"], GRZ)
L.emit("emb_en_arch_lantern")
li = bpy.data.lights.new("KEYEN_arch_lantern", 'POINT')
li.energy = 680.0
li.color = (1.0, 0.58, 0.24)
li.shadow_soft_size = 0.10
li.use_custom_distance = True
li.cutoff_distance = 14.0
lo = bpy.data.objects.new(li.name, li)
lo.location = (LNX, LNY, LZ - 0.58)
coll(COLL).objects.link(lo)
NEW.append(lo)

# THE PALISADE WINGS — the painting's own fence, and the cheapest legibility this town
# can buy: a run of pointed pales off each post tells the player instantly that the arch
# is the WAY IN and the rest of the line is not.  `bar_` — a collider that is never a
# floor, which is exactly what a fence is.
npale = 0
for (tag, px, py, pz) in POSTS:
    sgn = -1 if tag == "W" else 1
    P = Part()
    n = 0
    for k in range(11):
        d = 0.55 + k * 0.44
        fx, fy = px + UX * d * sgn, py + UY * d * sgn
        if not place("palisade_" + tag, fx, fy, 0.14, GZ0 - 0.6, GZ0 + 1.6):
            continue
        fz = gz(fx, fy, "palisade")
        ht = 1.28 + 0.10 * h01(k, ord(tag))
        P.box(fx, fy, fz + ht / 2 - 0.06, 0.17, 0.17, ht, MAT["timber"], GRZ)
        P.add([(fx - 0.085 * UX - 0.085 * AX, fy - 0.085 * UY - 0.085 * AY, fz + ht - 0.06),
               (fx + 0.085 * UX - 0.085 * AX, fy + 0.085 * UY - 0.085 * AY, fz + ht - 0.06),
               (fx + 0.085 * UX + 0.085 * AX, fy + 0.085 * UY + 0.085 * AY, fz + ht - 0.06),
               (fx - 0.085 * UX + 0.085 * AX, fy - 0.085 * UY + 0.085 * AY, fz + ht - 0.06),
               (fx, fy, fz + ht + 0.16)],
              [(0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], MAT["timber"])
        n += 1
    if n >= 2:
        far = 0.55 + (n - 1) * 0.44
        for rz_ in (0.52, 1.02):
            P.beam((px + UX * 0.5 * sgn, py + UY * 0.5 * sgn, gz(px, py, "rail") + rz_),
                   (px + UX * far * sgn, py + UY * far * sgn,
                    gz(px + UX * far * sgn, py + UY * far * sgn, "rail") + rz_),
                   0.09, 0.07, MAT["beam"])
        P.emit("bar_emb_en_palisade_%s" % tag)
        npale += n
print("  ARCH built: 2 posts on the road's normal, %d wreaths, 1 hanging lantern (680 W),"
      " %d palisade pales" % (NW, npale))

# =============================================================================
# 2. THE WAYSTONE — a mossy marker, a worn face, and a cat-sized shelf
# =============================================================================
WS = LM["waystone"]
WSX, WSY, WSZ = WS["pos"]
WAPX, WAPY = appr_of("waystone")
st = seat("waystone", WSX, WSY, 0.86, -1.0, 2.6)
assert st, "no seat for the waystone within 5 m of its map point"
SX_, SY_, SD = st
if SD > 0.01:
    print("  MAP REDLINE — waystone: authored (%.2f, %.2f) is inside the walk ribbon "
          "`walk_e_road-gate__waystone`; the marker is seated at (%.2f, %.2f), %.2f m "
          "west onto the verge.  Proposed map fix: waystone.pos -> [%.1f, %.1f, %.1f], "
          "then re-run the blockout and this search becomes a no-op."
          % (WSX, WSY, SX_, SY_, SD, round(SX_, 1), round(SY_, 1), WSZ))
WGZ = gz(SX_, SY_, "waystone")
# THE STONE FACES THE TRAVELLER, and that is authored here rather than inherited: a
# waystone is read by somebody walking UP the road, so its carved face looks back down it
# toward the arch.  Deriving the facing from `appr_of` would hand it to whichever rule
# the blockout currently uses to pick an approach — that rule changed once mid-build
# already (mean of all edges -> the preferred road edge) and would have spun this stone
# to face the square instead of the road it marks.
FX, FY = (GX - SX_), (GY - SY_)
_fl = math.hypot(FX, FY) or 1.0
FX, FY = FX / _fl, FY / _fl
RX, RY = -FY, FX
S = Part()
# two rough courses.  The upper one is 1.10 x 0.90 and its top is 0.56 m over the ground:
# that is the CAT PERCH, and it is deliberate — STORY.md and the map both put Mochi's
# hiring at this stone, and a cutscene needs somewhere a small cat can plausibly sit
# without floating or clipping.  Nothing else is allowed onto it.
S.box(SX_, SY_, WGZ + 0.14, 1.52, 1.24, 0.30, MAT["waystone"], math.atan2(FY, FX))
S.box(SX_, SY_, WGZ + 0.43, 1.10, 0.90, 0.28, MAT["waystone"], math.atan2(FY, FX))
PERCH_Z = WGZ + 0.57


def face_quad(cx, cy, cz, hw, hh, out):
    """A patch on the stone's front face, `out` metres proud of it."""
    return [(cx + RX * -hw + FX * out, cy + RY * -hw + FY * out, cz - hh),
            (cx + RX * hw + FX * out, cy + RY * hw + FY * out, cz - hh),
            (cx + RX * hw + FX * out, cy + RY * hw + FY * out, cz + hh),
            (cx + RX * -hw + FX * out, cy + RY * -hw + FY * out, cz + hh)]


# the marker itself: a tapered slab with a slight lean back off the road, because three
# hundred years of frost is what makes a stone a waystone rather than a bollard
LEAN = 0.10
base = [(SX_ + RX * -0.44 + FX * -0.22, SY_ + RY * -0.44 + FY * -0.22, PERCH_Z),
        (SX_ + RX * 0.44 + FX * -0.22, SY_ + RY * 0.44 + FY * -0.22, PERCH_Z),
        (SX_ + RX * 0.44 + FX * 0.22, SY_ + RY * 0.44 + FY * 0.22, PERCH_Z),
        (SX_ + RX * -0.44 + FX * 0.22, SY_ + RY * -0.44 + FY * 0.22, PERCH_Z)]
top = [(x - FX * LEAN + (RX * 0.06 if i in (0, 3) else -RX * 0.06),
        y - FY * LEAN + (RY * 0.06 if i in (0, 3) else -RY * 0.06),
        PERCH_Z + 1.74) for i, (x, y, _z) in enumerate(base)]
S.prism(base, top, MAT["waystone"])
S.quad(*face_quad(SX_ - FX * LEAN * 0.9, SY_ - FY * LEAN * 0.9, PERCH_Z + 1.66, 0.32, 0.06,
                  0.23), MAT["waystone"])                   # a weathered brow lip
# THE CARVED FACE, worn nearly smooth (`chapter1.js`: "the carved face is worn nearly
# smooth", and Vesper's own line — "it matches the sketch in her book, line for line,
# even the crack through the chin").  Relief is 20-30 mm: at this town's scale that is
# all a three-hundred-year-old carving has left, and it is what the painting shows.
FCZ = PERCH_Z + 1.16
FOF = 0.225 - LEAN * 0.55
S.quad(*face_quad(SX_, SY_, FCZ + 0.28, 0.26, 0.036, FOF + 0.024), MAT["carve"])   # brow
for sgn in (-1, 1):
    S.quad(*face_quad(SX_ + RX * sgn * 0.14, SY_ + RY * sgn * 0.14, FCZ + 0.15,
                      0.055, 0.046, FOF + 0.012), MAT["carve"])                    # eyes
S.quad(*face_quad(SX_, SY_, FCZ + 0.02, 0.034, 0.14, FOF + 0.028), MAT["carve"])   # nose
S.quad(*face_quad(SX_, SY_, FCZ - 0.21, 0.12, 0.026, FOF + 0.015), MAT["carve"])   # mouth
# the crack through the chin: three short offset incisions, because a crack is not a line
for k in range(3):
    S.quad(*face_quad(SX_ + RX * (0.02 * k - 0.02), SY_ + RY * (0.02 * k - 0.02),
                      FCZ - 0.38 - 0.11 * k, 0.020, 0.062, FOF + 0.008), MAT["carve"])
# EMBERBROOK, incised below the face: nine marks, which is what a carved name reads as at
# the distance every camera in this parcel stands.  No new proper noun is invented here —
# the town's own name is the map's.
for k in range(9):
    u = -0.26 + k * 0.065
    S.quad(*face_quad(SX_ + RX * u, SY_ + RY * u, PERCH_Z + 0.42,
                      0.020, 0.055, FOF + 0.010), MAT["carve"])
# the later, hand-scratched addition under it — a traveller's mark, scratched not carved
for k in range(3):
    u = -0.13 + k * 0.11
    S.quad(*face_quad(SX_ + RX * u, SY_ + RY * u, PERCH_Z + 0.24, 0.035, 0.022,
                      FOF + 0.006), MAT["carve"])
S.emit("emb_en_waystone")

# the moss: north and east faces and the plinth's shaded edges (the stone's own compass)
MO = Part()
for k in range(11):
    a = 1.2 + 0.44 * k
    mx = SX_ + 0.54 * math.cos(a)
    my = SY_ + 0.46 * math.sin(a)
    MO.box(mx, my, WGZ + 0.29 + 0.29 * (k % 2), 0.34 + 0.18 * h01(k, 7),
           0.30 + 0.16 * h01(k, 11), 0.05, MAT["moss"], a)
# and up the shaded back and flanks of the marker itself — the stone's own compass, and
# the map's first word for this landmark ("mossy marker stone")
for k in range(9):
    side = (-1.0 if k % 3 else 0.0)
    MO.quad(*face_quad(SX_ - FX * 0.44 + RX * (0.13 * k - 0.52) * (1 + side * 0.4),
                       SY_ - FY * 0.44 + RY * (0.13 * k - 0.52) * (1 + side * 0.4),
                       PERCH_Z + 0.22 + 1.24 * h01(k, 13), 0.13, 0.22, -0.012),
            MAT["moss"])
for k in range(4):
    sgn = 1 if k % 2 else -1
    MO.box(SX_ + RX * sgn * 0.41, SY_ + RY * sgn * 0.41,
           PERCH_Z + 0.35 + 1.05 * h01(k, 17), 0.10, 0.10, 0.34, MAT["moss"],
           math.atan2(FY, FX))
MO.emit("emb_en_waystone_moss")

# a small cairn at the foot: three stones, huddled and touching (docs/SCENE-LAYOUT.md —
# dressing huddles against an anchor, never scattered singletons)
CA = Part()
for k in range(3):
    a = 2.6 + 1.5 * k
    cx = SX_ + (0.86 + 0.10 * h01(k, 3)) * math.cos(a)
    cy = SY_ + (0.78 + 0.10 * h01(k, 5)) * math.sin(a)
    if not place("waystone_cairn", cx, cy, 0.30, WGZ, WGZ + 0.5):
        continue
    CA.box(cx, cy, gz(cx, cy, "cairn") + 0.14 + 0.05 * k, 0.44, 0.38,
           0.28 + 0.10 * h01(k, 7), MAT["stone"], h01(k, 9) * 1.4)
if CA.v:
    CA.emit("emb_en_waystone_cairn")
print("  WAYSTONE built at (%.2f, %.2f): carved face + crack, EMBERBROOK incised, "
      "cat perch at z %.2f (%.2f x %.2f m clear)" % (SX_, SY_, PERCH_Z, 1.10, 0.90))

# =============================================================================
# 3. THE ORCHARD — apple rows either side of the approach, ladders and baskets
# =============================================================================
OR_ = LM["orchard"]
OX, OY, OZ = OR_["pos"]
OEXT = OR_.get("extent", 5)
# ROWS ARE SET OUT ALONG THE ROAD, not along the field's own axis, and that is the whole
# composition: from either end of the south road the rows run AWAY from the camera and
# the perspective they draw is what makes 22 metres of village read as a valley.
# `walk_lm_orchard` is the field's walkable floor (extent 5, cells cut at 0.7 m with the
# 0.63 pad the square's build paid for) — every trunk is checked against the gate's own
# samples, so the rows part around the floor instead of standing on it.
ROWU = (AX, AY)
ROWV = (UX, UY)
TREES = []
ntree = 0
for j in range(-7, 8):                                   # rows, across the road
    for i in range(-8, 9):                               # trees along each row
        t = h32(i + 9, j + 9, 3)
        # TIGHT ALONG THE ROW, WIDE BETWEEN ROWS (2.8 x 3.9): that ratio is what makes an
        # orchard read as ROWS from a camera standing at the end of one, and it is the
        # only reason to set the grid out along the road in the first place.
        cx = OX + ROWU[0] * (i * 2.80) + ROWV[0] * (j * 3.90) + (h01(t, 1) - 0.5) * 0.4
        cy = OY + ROWU[1] * (i * 2.80) + ROWV[1] * (j * 3.90) + (h01(t, 2) - 0.5) * 0.4
        if not (B["min"][0] - 1.5 <= cx <= B["max"][0] + 1.0
                and B["min"][1] + 1.0 <= cy <= B["max"][1] + 1.0):
            continue                                     # the orchard stays in its parcel
        if not in_region(cx, cy, 0.8) or in_other_parcel(cx, cy, 1.0):
            continue
        # THE ARCH KEEPS ITS OWN AIR, and the shape of that air is not a circle: the
        # palisade runs 4.9 m off each post ALONG the span and nothing runs along the
        # road, so the exclusion is an ellipse.  A disc big enough to clear the fence
        # also deletes every tree that should be framing the road behind it.
        du = (cx - GX) * AX + (cy - GY) * AY
        dv = (cx - GX) * UX + (cy - GY) * UY
        if (du / 4.6) ** 2 + (dv / 7.8) ** 2 < 1.0:
            continue
        if math.hypot(cx - SX_, cy - SY_) < 3.4:
            continue                                     # ... and so does the waystone
        # AND THE RIVER'S WINDOW IS EVERY TREE'S PROBLEM, not the east screen's alone.
        # Measured: with the corridor applied only to the riverside wood, ONE apple tree
        # at (29.4, 10.8) — 5.5 m in front of the parcel's own camera — closed all 21
        # rays to the water by itself.  A screen composed 20 m out is worth nothing if
        # the foreground was planted by a different rule.
        if sight_dist(cx, cy) < 2.8:
            continue
        if near_station(cx, cy):
            continue
        tz = gz(cx, cy, "orchard tree")
        if not place("apple_tree", cx, cy, 0.55, tz, tz + 2.6):
            continue
        TREES.append((cx, cy, tz, t))
for ti, (cx, cy, tz, t) in enumerate(TREES):
    T = Part()
    ht = 3.9 + 1.15 * h01(t, 17)                          # apple trees are SMALL: the
    T.cyl(cx, cy, tz + ht * 0.30, 0.20, ht * 0.62, MAT["timber"], seg=8, r2=0.15)
    for bk in range(3):                                   # three lifted limbs
        a = 2 * math.pi * bk / 3 + h01(t, 19) * 2.0
        T.beam((cx, cy, tz + ht * 0.52),
               (cx + 0.85 * math.cos(a), cy + 0.85 * math.sin(a), tz + ht * 0.86),
               0.10, 0.10, MAT["timber"])
    leaf = MAT["leaf_green"] if (h32(t, 23) % 5) < 2 else MAT["leaf_autumn"]
    for c_ in range(3):
        rr = (1.55 + 0.42 * h01(t, 29 + c_)) * (1.0 - 0.19 * c_)
        T.cyl(cx + (h01(t, 31 + c_) - 0.5) * 0.5, cy + (h01(t, 37 + c_) - 0.5) * 0.5,
              tz + ht * 0.80 + c_ * 0.72, rr, 1.05, leaf, seg=8, r2=rr * 0.62)
    for ak in range(6):                                   # the apples: the pop of colour
        a = 2 * math.pi * ak / 6 + h01(t, 41) * 3.0
        rr = 1.15 + 0.35 * h01(t, 43 + ak)
        T.box(cx + rr * math.cos(a), cy + rr * math.sin(a),
              tz + ht * 0.80 + 1.15 * h01(t, 47 + ak), 0.15, 0.15, 0.15, MAT["apple"])
    T.emit("veg_emb_en_apple%02d" % ti)
    ntree += 1
print("  ORCHARD: %d apple trees in rows set out along the road (%d row candidates "
      "refused by the gate)" % (ntree, len([r for r in REFUSED if r[0] == "apple_tree"])))

# LADDERS AND BASKETS — the map's own note for this landmark, and the reason the orchard
# reads as WORKED rather than planted.  Each leans on a tree that actually exists.
nlad = nbask = 0
for k, ti in enumerate([max(0, int(len(TREES) * f)) for f in (0.17, 0.48, 0.79)]):
    if ti >= len(TREES):
        continue
    cx, cy, tz, t = TREES[ti]
    a = h01(t, 53) * 2 * math.pi
    fx, fy = cx + 2.05 * math.cos(a), cy + 2.05 * math.sin(a)
    if not place("ladder", fx, fy, 0.45, tz, tz + 2.6):
        continue
    fz = gz(fx, fy, "ladder")
    LA = Part()
    topx, topy, topz = cx + 0.42 * math.cos(a), cy + 0.42 * math.sin(a), tz + 3.05
    for sgn in (-1, 1):
        ox, oy = -math.sin(a) * sgn * 0.19, math.cos(a) * sgn * 0.19
        LA.beam((fx + ox, fy + oy, fz), (topx + ox, topy + oy, topz), 0.08, 0.08,
                MAT["timber"])
    for r_ in range(6):
        u = (r_ + 0.5) / 6.0
        LA.beam((fx + (topx - fx) * u - math.sin(a) * 0.19,
                 fy + (topy - fy) * u + math.cos(a) * 0.19, fz + (topz - fz) * u),
                (fx + (topx - fx) * u + math.sin(a) * 0.19,
                 fy + (topy - fy) * u - math.cos(a) * 0.19, fz + (topz - fz) * u),
                0.06, 0.05, MAT["timber"])
    LA.emit("emb_en_orchard_ladder%d" % k)
    nlad += 1
    # baskets HUDDLED at the ladder's foot, touching, with apples heaped over the rim
    BA = Part()
    n = 0
    for b in range(3):
        bx = fx + 0.62 * math.cos(a + 2.1 + b * 0.9)
        by = fy + 0.62 * math.sin(a + 2.1 + b * 0.9)
        if not place("basket", bx, by, 0.34, fz, fz + 0.7):
            continue
        bz = gz(bx, by, "basket")
        BA.cyl(bx, by, bz + 0.20, 0.30, 0.40, MAT["straw"], seg=10, r2=0.33)
        for ak in range(4):
            aa = 2 * math.pi * ak / 4 + h01(b, k, 7) * 2
            BA.box(bx + 0.15 * math.cos(aa), by + 0.15 * math.sin(aa), bz + 0.44,
                   0.14, 0.14, 0.14, MAT["apple"])
        n += 1
    if n:
        BA.emit("emb_en_orchard_baskets%d" % k)
        nbask += n

# THE ORCHARD HANDCART, parked at the field's road end with its load
CART = None
_c = seat("orchard_cart", OX + 4.6, OY + 2.2, 1.25, -1, 1.7, step=0.3, rings=14)
if _c:
    CART = (_c[0], _c[1], gz(_c[0], _c[1], "cart"))
if CART:
    ccx, ccy, ccz = CART
    crz = math.atan2(ROWU[1], ROWU[0])
    C = Part()
    C.box(ccx, ccy, ccz + 0.70, 2.10, 1.15, 0.22, MAT["timber"], crz)
    for sgn in (-1, 1):                                   # the sides and the tail
        C.box(ccx - math.sin(crz) * sgn * 0.56, ccy + math.cos(crz) * sgn * 0.56,
              ccz + 0.92, 2.10, 0.09, 0.34, MAT["timber"], crz)
    C.box(ccx + math.cos(crz) * 1.02, ccy + math.sin(crz) * 1.02, ccz + 0.92,
          0.09, 1.15, 0.34, MAT["timber"], crz)
    for sgn in (-1, 1):
        C.cyl(ccx - math.sin(crz) * sgn * 0.66, ccy + math.cos(crz) * sgn * 0.66,
              ccz + 0.46, 0.44, 0.11, MAT["timber"], seg=12)
    for sgn in (-1, 1):                                   # shafts, resting on the ground
        C.beam((ccx + math.cos(crz) * 1.0 - math.sin(crz) * sgn * 0.40,
                ccy + math.sin(crz) * 1.0 + math.cos(crz) * sgn * 0.40, ccz + 0.78),
               (ccx + math.cos(crz) * 2.3 - math.sin(crz) * sgn * 0.40,
                ccy + math.sin(crz) * 2.3 + math.cos(crz) * sgn * 0.40, ccz + 0.10),
               0.09, 0.09, MAT["timber"])
    for k in range(10):                                   # crates and loose apples
        u, v = (k % 5) * 0.38 - 0.76, (k // 5) * 0.42 - 0.21
        C.box(ccx + math.cos(crz) * u - math.sin(crz) * v,
              ccy + math.sin(crz) * u + math.cos(crz) * v,
              ccz + 0.90 + 0.05 * h01(k, 3), 0.34, 0.36, 0.20, MAT["apple"], crz)
    C.emit("emb_en_orchard_cart")
print("  orchard work: %d ladders, %d baskets, %d cart" % (nlad, nbask, 1 if CART else 0))

# =============================================================================
# 4. THE SOUTH APPROACH — the valley the player arrives out of
# =============================================================================
# IMPLIED SCALE, technique 1 (`impliedScale._doc`): non-walkable massing beyond every
# playable edge, composed into the frame.  South of the arch is the ONLY edge of this
# town a player has already travelled, so an empty lawn there is a lie about where they
# came from.  The road continues — `emb_en_` scenery, NOT walkable, exactly the way the
# blockout's own `emb_lanestub_*` closes a lane — narrowing as it recedes, between two
# harvested fields, and it disappears into the wooded rim the blockout already planted
# 11 m out.  Nothing here is `walk_`: the walk network stays exactly as tight as the
# parcel.
SOUTH = Part()
nseg = 0
for k in range(11):
    d0, d1 = 1.4 + k * 1.55, 1.4 + (k + 1) * 1.55
    m0x, m0y = GX - AX * d0, GY - AY * d0
    m1x, m1y = GX - AX * d1, GY - AY * d1
    if m0y < REGION[2] + 1:
        break
    w0, w1 = 2.45 - 0.10 * k, 2.45 - 0.10 * (k + 1)
    z0, z1 = gz(m0x, m0y, "south road") + 0.04, gz(m1x, m1y, "south road") + 0.04
    SOUTH.add([(m0x - UX * w0 / 2, m0y - UY * w0 / 2, z0),
               (m0x + UX * w0 / 2, m0y + UY * w0 / 2, z0),
               (m1x + UX * w1 / 2, m1y + UY * w1 / 2, z1),
               (m1x - UX * w1 / 2, m1y - UY * w1 / 2, z1)],
              [(0, 1, 2, 3)], MAT["road"])
    nseg += 1
SOUTH.emit("emb_en_southroad")

# the two field walls that flank it — dry-stone, the map's own motif ("dry-stone walls
# along lanes"), each one a run of stones in a single mesh
nwall = 0
for sgn, tag in ((-1, "E"), (1, "W")):
    # A DRY-STONE WALL IS A RUN, NOT A ROW OF BOULDERS.  The first draft set two courses
    # of 0.66 m blocks at each sample's own ground height and rendered, from the parcel's
    # own camera, as a flight of white steps climbing out of the field beside the arch —
    # the single ugliest thing in the frame.  It is built as a continuous member now, with
    # a capstone course broken into shorter lengths, and it is the darker stone: a field
    # wall is the thing you do not notice.
    WA = Part()
    pts = []
    for k in range(30):
        d = 3.0 + k * 0.62
        wx = GX - AX * d + UX * sgn * (3.9 + 0.055 * k)
        wy = GY - AY * d + UY * sgn * (3.9 + 0.055 * k)
        if wy < REGION[2] + 1:
            break
        pts.append((wx, wy, gz(wx, wy, "field wall")))
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        WA.beam((a[0], a[1], a[2] + 0.24), (b[0], b[1], b[2] + 0.24), 0.46, 0.48,
                MAT["waystone"])
        if k % 2 == 0 and k + 2 < len(pts):
            c = pts[k + 2]
            WA.beam((a[0], a[1], a[2] + 0.55), (c[0], c[1], c[2] + 0.55), 0.52, 0.14,
                    MAT["waystone"])
    if len(pts) > 1:
        WA.emit("bar_emb_en_fieldwall_%s" % tag)
        nwall += len(pts) - 1

# the harvest itself: stooks huddled in touching groups of four, two per field.  It is
# Emberwake — the harvest is IN, and the fields have to say so.
nstook = 0
for gi in range(4):
    d = 5.5 + 4.4 * (gi // 2)
    sgn = -1 if gi % 2 == 0 else 1
    bx = GX - AX * d + UX * sgn * (6.6 + 1.4 * h01(gi, 3))
    by = GY - AY * d + UY * sgn * (6.6 + 1.4 * h01(gi, 5))
    if by < REGION[2] + 1:
        continue
    ST = Part()
    for k in range(4):
        a = 2 * math.pi * k / 4 + h01(gi, 7)
        sx2, sy2 = bx + 0.62 * math.cos(a), by + 0.62 * math.sin(a)
        sz2 = gz(sx2, sy2, "stook")
        ht = 1.25 + 0.20 * h01(gi, k, 11)
        ST.cyl(sx2, sy2, sz2 + ht / 2, 0.42, ht, MAT["straw"], seg=8, r2=0.10)
    ST.emit("emb_en_stooks%d" % gi)
    nstook += 4
print("  SOUTH APPROACH: %d road segments running out of frame, %d m of field wall, "
      "%d stooks in %d huddles" % (nseg, nwall, nstook, nstook // 4))

# =============================================================================
# 5. THE EAST FALL — the river Vesper followed, glimpsed through the trees
# =============================================================================
# The map's `river` block is USER CANON: "Vesper has been following the river ... Build:
# visible vista east of town, NOT walkable."  The blockout puts the water at centre
# x 57 as one slab and carves its channel; the ground between falls away from +0.4 at
# the road to -1.3 by x 50.  So the river is ALREADY there and already reachable by eye
# — what was missing is a reason for the eye to travel, and a frame to travel through.
#
# This band plants a broken screen of riverside trees on the fall with a MEASURED GAP:
# every candidate within 4.2 m of the sightline from the parcel's own camera anchor to
# the water is dropped, so the glimpse is composed rather than hoped for.  It is checked
# by ray-cast in the acceptance block, not asserted here.
SR_END = (GX - AX * 18.5, GY - AY * 18.5)                 # the south road's far end
nriv = ngap = nfield = 0
for k in range(96):
    rx = 35.6 + 8.6 * h01(k, 5)
    ry = -7.5 + 21.5 * (k / 95.0) + (h01(k, 7) - 0.5) * 2.4
    if not in_region(rx, ry, 0.8) or in_other_parcel(rx, ry, 1.0):
        continue
    # THE FIELDS COME FIRST, THEN THE WOOD.  The south approach's own road, walls and
    # stooks occupy the same band this screen sweeps through; a riverside tree planted in
    # the middle of a harvested field is not a vista, it is a collision.
    if seg_d(rx, ry, GX, GY, SR_END[0], SR_END[1]) < 6.0:
        nfield += 1
        continue
    if sight_dist(rx, ry) < 3.6 or near_station(rx, ry):
        ngap += 1
        continue                                          # THE GAP: the river's window
    if any(math.hypot(rx - t[0], ry - t[1]) < 3.0 for t in TREES):
        continue
    rz_ = gz(rx, ry, "river tree")
    if not place("river_tree", rx, ry, 0.6, rz_, rz_ + 2.6):
        continue
    R_ = Part()
    ht = 5.2 + 2.9 * h01(k, 11)
    R_.cyl(rx, ry, rz_ + ht * 0.33, 0.26, ht * 0.68, MAT["timber"], seg=8, r2=0.18)
    leaf = MAT["leaf_green"] if (h32(k, 13) % 5) < 2 else MAT["leaf_autumn"]
    for c_ in range(2):
        rr = (1.9 + 0.9 * h01(k, 17 + c_)) * (1.0 - 0.20 * c_)
        R_.cyl(rx, ry, rz_ + ht * 0.66 + c_ * 1.30, rr, 1.7, leaf, seg=8, r2=rr * 0.55)
    R_.emit("veg_emb_en_riverwood%02d" % k)
    nriv += 1

# reeds and bank tufts down on the fall, where the ground drops under +0.1: the cue that
# says "water down there" from a camera that cannot yet see the water itself
nreed = 0
RE = Part()
for k in range(70):
    rx = 37.0 + 6.8 * h01(k, 23)
    ry = -12.0 + 26.0 * (k / 69.0)
    if not in_region(rx, ry, 1.0) or in_other_parcel(rx, ry, 1.0):
        continue
    rz_ = gz(rx, ry, "reed")
    if rz_ > 0.15:
        continue
    if not GATE.clear_pt(rx, ry, 0.4, rz_, rz_ + 1.2):
        continue
    for b in range(4):
        a = 2 * math.pi * b / 4 + h01(k, b, 3)
        RE.beam((rx + 0.10 * math.cos(a), ry + 0.10 * math.sin(a), rz_),
                (rx + 0.34 * math.cos(a), ry + 0.34 * math.sin(a),
                 rz_ + 0.75 + 0.35 * h01(k, b, 5)), 0.05, 0.05, MAT["leaf_green"])
    nreed += 1
if nreed:
    RE.emit("veg_emb_en_riverreeds")

# the milestone where the river road leaves the village — the exit `valley-road-south`
# made of one small stone, so the road out has a mark on it as well as a gate over it
MSX, MSY = GX - AX * 2.6 + UX * 2.1, GY - AY * 2.6 + UY * 2.1
if place("milestone", MSX, MSY, 0.30, -1, 1.4):
    MS = Part()
    msz = gz(MSX, MSY, "milestone")
    MS.box(MSX, MSY, msz + 0.10, 0.62, 0.52, 0.22, MAT["stone"], GRZ)
    MS.box(MSX, MSY, msz + 0.52, 0.40, 0.30, 0.66, MAT["stone"], GRZ)
    MS.quad(*[(MSX - AX * 0.16 + UX * u, MSY - AY * 0.16 + UY * u, msz + z_)
              for (u, z_) in ((-0.13, 0.44), (0.13, 0.44), (0.13, 0.62), (-0.13, 0.62))],
            MAT["carve"])
    MS.emit("emb_en_milestone")
print("  EAST FALL: %d riverside trees (%d dropped to keep the river's window open, "
      "%d to keep the harvested fields open), %d reed clumps on the fall"
      % (nriv, ngap, nfield, nreed))

# =============================================================================
# 6. FESTIVAL DRESSING — Emberwake, and the lamps already lit
# =============================================================================
# The bunting hangs from things that EXIST: the blockout's lamp ring, this pass's arch,
# and three festival poles planted along the road (a pole is a real object with a real
# foot on real ground — it is not a floating anchor).  A strung line overhead is the
# cheapest legibility in the town: it says "the way in is dressed for tonight".
POLES = []
for pi, (fx0, fy0) in enumerate([(28.6, 6.5), (28.5, 10.4), (25.6, 11.6)]):
    s2 = seat("festival_pole%d" % pi, fx0, fy0, 0.30, -1, 3.6, step=0.3, rings=10)
    if not s2:
        continue
    px, py, _d = s2
    pz = gz(px, py, "pole")
    P = Part()
    P.box(px, py, pz + 0.10, 0.46, 0.46, 0.28, MAT["stone"], GRZ)
    P.box(px, py, pz + 1.72, 0.18, 0.18, 3.06, MAT["timber"], GRZ)
    P.box(px, py, pz + 3.30, 0.28, 0.28, 0.10, MAT["beam"], GRZ)
    for k in range(3):                                     # a pennant, and it is cloth
        P.quad((px + 0.09, py, pz + 3.20 - k * 0.28), (px + 0.62, py, pz + 3.05 - k * 0.28),
               (px + 0.62, py, pz + 2.86 - k * 0.28), (px + 0.09, py, pz + 2.94 - k * 0.28),
               [MAT["cloth_red"], MAT["cloth_cream"], MAT["cloth_green"]][k])
    P.emit("emb_en_festpole%d" % pi)
    POLES.append((px, py, pz + 3.26))

ANCHORS = []
for (tag, px, py, pz) in POSTS:                            # the arch's own lintel ends
    ANCHORS.append(("arch_" + tag, px, py, LZ + 0.44))
for o in sorted(bpy.data.objects, key=lambda o: o.name):   # the blockout's lamps: canon
    if o.name.startswith("emb_lamp_") and o.name.endswith("_cap") and o.data.vertices:
        cx_, cy_, cz_ = world_centre(o)
        # a lamp in the SQUARE's parcel is the flagship's to dress; hanging my bunting on
        # it would put my geometry in their frame and their objects in my digest
        if in_region(cx_, cy_) and not in_other_parcel(cx_, cy_):
            ANCHORS.append((o.name, cx_, cy_, cz_ + 0.06))
for pi, (px, py, pz) in enumerate(POLES):
    ANCHORS.append(("pole%d" % pi, px, py, pz))
ANCHORS.sort(key=lambda a: (round(a[1], 3), round(a[2], 3), a[0]))

LINES = []
for i in range(len(ANCHORS)):
    for j in range(i + 1, len(ANCHORS)):
        a, b = ANCHORS[i], ANCHORS[j]
        Ld = math.hypot(b[1] - a[1], b[2] - a[2])
        if 3.2 <= Ld <= 13.0:
            LINES.append((Ld, i, j))
LINES.sort()
used = {}
nline = nflag = 0
FLAGM = [MAT["cloth_red"], MAT["cloth_cream"], MAT["cloth_green"], MAT["cloth_blue"]]
for (Ld, i, j) in LINES:
    if used.get(i, 0) >= 2 or used.get(j, 0) >= 2:
        continue                                           # two swags per anchor, no web
    a, b = ANCHORS[i], ANCHORS[j]
    BU, FL = Part(), Part()
    N = max(5, int(Ld / 1.15))
    prev = None
    lowest = 1e9
    seg = []
    for s in range(N + 1):
        t = s / float(N)
        sag = 0.30 + 0.55 * math.sin(math.pi * t)
        p = (a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t,
             a[3] + (b[3] - a[3]) * t - sag)
        if prev is not None:
            seg.append((prev, p))
            lowest = min(lowest, p[2], prev[2])
        prev = p
    # a swag over a walk sample is a tripwire: check the whole line before hanging it
    if not GATE.clear_seg(Vector((min(a[1], b[1]), min(a[2], b[2]), lowest)),
                          Vector((max(a[1], b[1]), max(a[2], b[2]), lowest + 0.25)), 0.10):
        REFUSED.append(("bunting %s-%s" % (a[0], b[0]), round(a[1], 2), round(a[2], 2)))
        continue
    for (p, q) in seg:
        BU.beam(p, q, 0.045, 0.045, MAT["beam"])
    for si, (p, q) in enumerate(seg):
        if si % 2:
            continue
        m = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2
        col = FLAGM[(i + si) % 4]
        FL.add([(m[0] - 0.17, m[1], m[2] - 0.02), (m[0] + 0.17, m[1], m[2] - 0.02),
                (m[0], m[1], m[2] - 0.36)], [(0, 1, 2)], col)
        nflag += 1
    # two little hanging lanterns per line, the painting's own detail
    for lk in (0.34, 0.68):
        s2 = int(lk * len(seg))
        if s2 < len(seg):
            p, q = seg[s2]
            m = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2
            FL.box(m[0], m[1], m[2] - 0.30, 0.15, 0.15, 0.21, MAT["paper"])
            FL.beam((m[0], m[1], m[2]), (m[0], m[1], m[2] - 0.19), 0.03, 0.03, MAT["iron"])
    BU.emit("emb_en_bunting%02d" % nline)
    FL.emit("emb_en_buntingflags%02d" % nline)
    used[i] = used.get(i, 0) + 1
    used[j] = used.get(j, 0) + 1
    nline += 1
print("  FESTIVAL: %d poles, %d bunting swags, %d flags, hung off %d real anchors: %s"
      % (len(POLES), nline, nflag, len(ANCHORS), ", ".join(a[0] for a in ANCHORS)))

# pumpkins and gourds huddled at the feet of things that already stand (never singletons)
npump = 0
for gi, (ax_, ay_) in enumerate([(POSTS[0][1] - UX * 0.9, POSTS[0][2] - UY * 0.9),
                                 (POSTS[1][1] + UX * 0.9, POSTS[1][2] + UY * 0.9),
                                 (SX_ - FX * 1.1, SY_ - FY * 1.1)]):
    PU = Part()
    n = 0
    for k in range(4):
        a = 2 * math.pi * k / 4 + h01(gi, 3)
        px, py = ax_ + 0.40 * math.cos(a), ay_ + 0.40 * math.sin(a)
        if not place("pumpkin", px, py, 0.30, -1, 1.0):
            continue
        pz = gz(px, py, "pumpkin")
        r = 0.24 + 0.07 * h01(gi, k, 5)
        # squat, not conical: the first draft's tapered cylinders rendered as traffic
        # cones in a harvest festival
        PU.cyl(px, py, pz + r * 0.34, r * 0.92, r * 0.68, MAT["pumpkin"], seg=10, r2=r)
        PU.cyl(px, py, pz + r * 0.92, r, r * 0.48, MAT["pumpkin"], seg=10, r2=r * 0.62)
        PU.box(px, py, pz + r * 1.24, 0.06, 0.06, 0.13, MAT["timber"])
        n += 1
    if n:
        PU.emit("emb_en_gourds%d" % gi)
        npump += n
print("  gourds huddled at posts and stone: %d" % npump)

# =============================================================================
# ACCEPTANCE — measured, printed, and non-zero on a real failure
# =============================================================================
print("-" * 78)
if REFUSED:
    print("  REFUSED (would have stood in the walk gate's own rays) — %d:" % len(REFUSED))
    seen = {}
    for nm, x, y in REFUSED:
        seen[nm] = seen.get(nm, 0) + 1
    for nm in sorted(seen):
        ex = next((r for r in REFUSED if r[0] == nm), None)
        print("      %-24s x%-3d  e.g. (%.2f, %.2f)" % (nm, seen[nm], ex[1], ex[2]))
else:
    print("  REFUSED: none")
if NOGROUND:
    print("  NO GROUND UNDER (nothing was floated; these were counted): %d" % len(NOGROUND))
    for w, x, y in NOGROUND[:8]:
        print("      %-20s (%.2f, %.2f)" % (w, x, y))

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# 1. THE GATE'S OWN TEST, RE-RUN AS RAYS — master_walk_qa's two rays per walk sample,
# not bounding boxes (the square's build paid for that distinction: 32 false positives).
NEWNAMES = {o.name for o in NEW if o.type == 'MESH'}
offenders = {}
for (sx, sy, sz) in GATE.pts:
    for org, dvec, dist in (((sx, sy, sz + 0.90), (0, 0, -1), 1.90),
                            ((sx, sy, sz + 0.06), (0, 0, 1), 1.94)):
        hit, _l, _n, _i, ob, _m = sc.ray_cast(dg, Vector(org), Vector(dvec), distance=dist)
        if hit and ob is not None and ob.name in NEWNAMES:
            floor = "?"
            fh, _fl, _fn, _fi, fo, _fm = sc.ray_cast(dg, Vector((sx, sy, sz + 0.05)),
                                                     Vector((0, 0, -1)), distance=0.60)
            if fh and fo is not None:
                floor = fo.name
            offenders.setdefault(ob.name, []).append((round(sx, 2), round(sy, 2), floor))
print("  GATE RE-CHECK (master_walk_qa's own two rays, %d walk samples): %d offenders"
      % (len(GATE.pts), len(offenders)))
for nm in sorted(offenders)[:20]:
    pts = offenders[nm]
    print("      %-32s %3d samples on %s"
          % (nm, len(pts), ", ".join(sorted({q[2] for q in pts}))[:70]))

# 2. THE WALK NETWORK, PROVED UNTOUCHED.  Not "I did not mean to": a digest over every
# blockout walk_/bar_ mesh in the town, which must equal the frozen base's.
wh = hashlib.sha256()
nwalk = 0
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type != 'MESH' or not o.name.startswith(("walk_", "bar_")):
        continue
    if o.name.startswith("bar_emb_en_"):
        continue                                           # mine, and new by design
    wh.update(o.name.encode())
    Mx = o.matrix_world
    for v in o.data.vertices:
        p = Mx @ v.co
        wh.update(("%.6f,%.6f,%.6f;" % (p.x, p.y, p.z)).encode())
    nwalk += 1
print("  WALK NETWORK DIGEST (%d blockout walk_/bar_ meshes): %s" % (nwalk, wh.hexdigest()))

# 2b. HOW MUCH OF THE ROAD IS EVEN VISIBLE — measured, because the answer surprised this
# pass and it is not a fault this district can fix from inside its own prefix.
# `emb_blockout` interpolates the ground from the map's anchors and lays each walk top at
# its landmark's authored z; the two disagree, and where the ground wins the walk surface
# is UNDER THE GRASS.  The skin can fill the gaps between ribbons but it may never rise
# above a walk face (that would fail master_walk_qa's coverage ray), so wherever the
# ground is over the road, the road is invisible and stays invisible until the blockout
# cuts its ground down to its own network — the same way it already carves the brook.
buried = shown = 0
worst = 0.0
for (sx, sy, sz) in GATE.pts:
    g = bvh_ground_z(GBVH, sx, sy)
    if g is None:
        continue
    if g > sz + 0.005:
        buried += 1
        worst = max(worst, g - sz)
    else:
        shown += 1
print("  WALK SURFACE vs GROUND in this region: %d of %d samples have the interpolated "
      "ground ABOVE the walk top (worst %.2f m) — a blockout-level finding, not a "
      "district one" % (buried, buried + shown, worst))

# 2c. THE WHOLE-SCENE SNAPSHOT.  Everything above proves things about MY objects; this
# proves the negative, which is the one the merge actually depends on: apart from the six
# `lm_` massing objects belonging to my three parcel members, not one object in the town
# was removed by this pass.  Lamps, ground, water, walk, bar, lanestubs, every vista
# cluster and both closed lanes are still exactly where the blockout left them.
AFTER = {o.name for o in bpy.data.objects}
lost = sorted(BEFORE - AFTER)
expected_lost = sorted(n for n in BEFORE - AFTER
                       if any(n == "lm_" + m or n.startswith("lm_%s_" % m) for m in MEMBERS)
                       or n.startswith(MINE))
assert lost == expected_lost, \
    "this pass removed objects it does not own: %s" % sorted(set(lost) - set(expected_lost))
dress_after = {o.name for o in bpy.data.objects
               if any(o.name.startswith(("lm_%s_" % i, "bar_%s_" % i, "emb_lanestub_%s_" % i))
                      or o.name == "lm_" + i for i in DRESSING)}
assert dress_after == DRESS_BEFORE, "implied-scale massing lost: %s" % (DRESS_BEFORE - dress_after)
print("  SCENE SNAPSHOT: %d objects retired, all of them my own or my members' massing "
      "(%s); %d implied-scale vista/closed-lane objects intact"
      % (len(lost), ", ".join(n for n in lost if not n.startswith(MINE))[:70],
         len(dress_after)))

# 3. CONTAINMENT: nothing of mine may stand inside another parcel's bounds, and nothing
# may stand outside the region this pass declared and gated.
def wbb(o):
    P = [o.matrix_world @ v.co for v in o.data.vertices]
    return ((min(p.x for p in P) + max(p.x for p in P)) / 2,
            (min(p.y for p in P) + max(p.y for p in P)) / 2,
            min(p.x for p in P), max(p.x for p in P),
            min(p.y for p in P), max(p.y for p in P))


bad = []
for o in NEW:
    if o.type != 'MESH':
        continue
    cx, cy, x0, x1, y0, y1 = wbb(o)
    if not in_region(cx, cy):
        bad.append((o.name, "centre outside the declared region"))
    if not (REGION[0] - FOLIAGE <= x0 and x1 <= REGION[1] + FOLIAGE
            and REGION[2] - FOLIAGE <= y0 and y1 <= REGION[3] + FOLIAGE):
        bad.append((o.name, "reaches more than %.1f m past the region" % FOLIAGE))
    who = in_other_parcel(cx, cy)
    if who:
        bad.append((o.name, "inside parcel %s" % who))
for nm, why in bad[:12]:
    print("      CONTAINMENT %-30s %s" % (nm, why))
assert not bad, "%d objects break containment" % len(bad)
print("  CONTAINMENT OK — %d meshes, all inside the declared region and outside every "
      "other parcel" % len([o for o in NEW if o.type == 'MESH']))

# 4. the walk surfaces this district hands to the cameras, counted and unchanged
walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")
         and o.data.vertices and REGION[0] <= wbb(o)[0] <= REGION[1]
         and REGION[2] <= wbb(o)[1] <= REGION[3]]
print("  walk surfaces in region: %d (untouched by this pass, by design)" % len(walks))

# 5. THE RIVER'S WINDOW, measured by ray-cast rather than hoped for: a fan of rays from
# the parcel's camera anchor toward the water, counting how many reach it.
hits = tot = 0
for k in range(21):
    t = k / 20.0
    tx = RIVER_PT[0] + (t - 0.5) * 16.0
    ty = RIVER_PT[1] + (t - 0.5) * 9.0
    d = Vector((tx - CAM_ANCHOR[0], ty - CAM_ANCHOR[1], RIVER_PT[2] - CAM_ANCHOR[2]))
    dist = d.length
    d.normalize()
    hit, _l, _n, _i, ob, _m = sc.ray_cast(dg, Vector(CAM_ANCHOR), d, distance=dist * 0.999)
    tot += 1
    if not hit or (ob is not None and ob.name.startswith("water_")):
        hits += 1
print("  RIVER WINDOW from the camera anchor (%.1f, %.1f, %.1f): %d of %d rays reach the "
      "water" % (CAM_ANCHOR + (hits, tot)))
assert hits, "the east screen closed the river's own window — widen the gap"

# 6. exactly one magical light in the whole town, and mine are ordinary
heart = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.energy > 2000]
mine_l = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name.startswith("KEYEN_")]
print("  magical light sources town-wide: %d (%s); this district adds %d ordinary "
      "practicals at 680 W" % (len(heart), ", ".join(o.name for o in heart), len(mine_l)))
assert len(heart) == 1, "Emberbrook has exactly one Heartlight — found %d" % len(heart)
assert all(o.data.energy <= 700 for o in mine_l), "an entrance light is not ordinary"

mine = [o for o in bpy.data.objects if o.name.startswith(MINE)]
nv = sum(len(o.data.vertices) for o in mine if o.type == 'MESH')
print("  BUILT: %d objects, %d vertices under %s" % (len(mine), nv, "/".join(MINE)))

if DIGEST:
    h = hashlib.sha256()
    for o in sorted([o for o in bpy.data.objects if o.name.startswith(MINE)],
                    key=lambda o: o.name):
        h.update(o.name.encode())
        if o.type == 'MESH':
            for v in o.data.vertices:
                h.update(("%.4f,%.4f,%.4f;" % (v.co.x, v.co.y, v.co.z)).encode())
        else:
            h.update(("%.4f,%.4f,%.4f;" % tuple(o.location)).encode())
    print("DIGEST %s" % h.hexdigest())

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the blend)")
