"""master_river_widen.py — widen the Dellhollow gorge 3x IN THE MASTER.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_river_widen.py

The map (`public/townmap/dellhollow.map.json`) is the topology truth and it now
says: river width 16 -> 48, centreY 34 -> 50, gorge.farWallY 58 -> 84.  The NEAR
bank (town side, y~26) does not move — every built waterfront in the town sits on
it.  Everything on the FAR side moves or stretches north.

What this pass does, in order:

  1. blockout context (CONTEXT)   far cliff to the new wall line + taller, the
                                  three pool planes stretched to the new far bank,
                                  a new far-bank toe so the far side is not void,
                                  the Lock Five dam re-spanned and its three
                                  waterwheels redistributed across the full width.
  2. district river (DIST_boatyard) riverbed widened; the Lock Four dam — accepted
                                  district art — EXTENDED, not replaced: the town-side
                                  gate bays stay bit-identical, the black-stone weir /
                                  crest / cap / parapet / crest gallery run north to a
                                  far abutment set into the new cliff, the piers,
                                  string courses, crest posts and gallery posts carry
                                  on at their own pitches, and three more spill bays
                                  are DUPLICATED from the northernmost existing bay.
  3. fx_* atmosphere              haze slabs, upstream ridges and the far-town
                                  silhouette re-centred on the new gorge; the far-wall
                                  autumn crowns moved onto the new far rim.
  4. spar trim (finding 57)       the two `foreground_timber` spars that stand on the
                                  yard and drive their heads INTO the boatwright shed
                                  are removed; the trestles + board stack (genuinely
                                  supported) stay.
  5. grade                        view_settings.exposure -> +0.35 (user pick).

walk_/bar_ meshes are never touched.  Re-runnable is NOT claimed: this is a
one-shot migration from the 16-wide river to the 48-wide one (it asserts the
pre-state it expects and refuses to run twice).
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

ROOT = os.getcwd()
MAP = os.path.join(ROOT, "public/townmap/dellhollow.map.json")

D = json.load(open(MAP))
RV = D["river"]
CY = RV["centerY"]; RW = RV["width"]
NEAR = CY - RW / 2.0                    # 26.0  — unchanged, the town's waterfront
FAR = CY + RW / 2.0                     # 74.0  — the new far bank
FARWALL = RV["gorge"]["farWallY"]       # 84.0
OLD_FAR = 42.0                          # where the far bank used to be

LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-10s %-40s %s" % (kind, what, why))


def wbb(o):
    vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs),
            max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs))


def pull_north(o, split, target):
    """Move every vertex north of `split` to y=`target` (local-space safe)."""
    Mi = o.matrix_world.inverted()
    n = 0
    for v in o.data.vertices:
        p = o.matrix_world @ v.co
        if p.y > split:
            v.co = Mi @ Vector((p.x, target, p.z))
            n += 1
    o.data.update()
    return n


def shift(o, dy):
    o.location.y += dy


# ===========================================================================
# 0. sanity — this is a one-shot migration
# ===========================================================================
def preflight():
    cf = bpy.data.objects["cliff_far"]
    b = wbb(cf)
    assert b[2] < FARWALL - 1.0, "cliff_far is already at the new wall line — already run?"
    dam = bpy.data.objects["lock_four_dam"]
    assert wbb(dam)[3] < 46.0, "lock_four_dam already extended — already run?"
    print("preflight ok: near=%.1f far=%.1f farwall=%.1f (was far=%.1f)"
          % (NEAR, FAR, FARWALL, OLD_FAR))


# ===========================================================================
# 1. blockout context
# ===========================================================================
CLIFF_TOP = 58.0        # was 42 — the gorge is 58 wide now, it needs the height
CLIFF_DEPTH = 12.0      # was 8


def phase_context():
    print("\n--- 1. blockout context -------------------------------------------")
    cf = bpy.data.objects["cliff_far"]
    b = wbb(cf)
    Mi = cf.matrix_world.inverted()
    for v in cf.data.vertices:
        p = cf.matrix_world @ v.co
        y = FARWALL if p.y < (b[2] + b[3]) / 2 else FARWALL + CLIFF_DEPTH
        z = p.z if p.z < 0 else CLIFF_TOP
        v.co = Mi @ Vector((p.x, y, z))
    cf.data.update()
    log("MOVE", "cliff_far", "y %.0f..%.0f -> %.0f..%.0f, top z %.0f -> %.0f (enclosure at 3x width)"
        % (b[2], b[3], FARWALL, FARWALL + CLIFF_DEPTH, b[5], CLIFF_TOP))

    # --- the three pool planes: near edge KEPT, far edge to the new bank -----
    for pid in ("pool-upstream", "pool-mid", "pool-downstream"):
        o = bpy.data.objects["water_" + pid]
        b = wbb(o)
        n = pull_north(o, (b[2] + b[3]) / 2.0, FAR)
        log("STRETCH", "water_" + pid,
            "far edge y %.2f -> %.1f (near edge %.2f preserved, level z %.2f), %d verts"
            % (b[3], FAR, b[2], b[5], n))

    # --- a far bank so the far side is not void under the cliff -------------
    far_bank_toe()
    farwall_look()
    relight_gorge()

    # --- Lock Five: the blockout dam must span the full new width ------------
    span_dam_five()


def level_at(x):
    for p in RV["pools"]:
        if p["from"] - 0.001 <= x <= p["to"] + 0.001:
            return p["level"]
    return RV["pools"][0]["level"] if x < RV["pools"][0]["from"] else RV["pools"][-1]["level"]


def far_bank_toe():
    """Shelving rock between the new waterline and the foot of the far cliff.

    Without it the 10 m between water (y=74) and cliff face (y=84) renders as a
    hole to the world background from any camera that looks down the gorge.
    Its lip is cut to the LOCAL pool level so each of the three pools meets a
    shoreline instead of floating over a step.
    """
    old = bpy.data.objects.get("cliff_far_toe")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    XS = [-35.0, -20.0, 13.98, 14.02, 86.98, 87.02, 135.0]
    YS = [FAR - 1.0, FAR + 4.0, FARWALL + 1.0]
    ZOFF = [-0.35, 3.2, 15.0]
    BOT = -9.0
    V, F = [], []
    idx = {}
    for i, x in enumerate(XS):
        lv = level_at(x)
        for j, y in enumerate(YS):
            idx[(i, j)] = len(V)
            V.append((x, y, lv + ZOFF[j] if j < 2 else ZOFF[j]))
    bot = {}
    for i, x in enumerate(XS):
        for j in (0, 2):
            bot[(i, j)] = len(V)
            V.append((x, YS[j], BOT))
    for i in range(len(XS) - 1):
        for j in range(len(YS) - 1):
            F.append((idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))
        F.append((bot[(i, 0)], bot[(i + 1, 0)], idx[(i + 1, 0)], idx[(i, 0)]))       # river face
        F.append((idx[(i, 2)], idx[(i + 1, 2)], bot[(i + 1, 2)], bot[(i, 2)]))       # back face
        F.append((bot[(i, 2)], bot[(i + 1, 2)], bot[(i + 1, 0)], bot[(i, 0)]))       # underside
    for i, s in ((0, 1), (len(XS) - 1, -1)):
        F.append((bot[(i, 0)], idx[(i, 0)], idx[(i, 1)], idx[(i, 2)])[::s])
        F.append((bot[(i, 0)], idx[(i, 2)], bot[(i, 2)])[::s])
    me = bpy.data.meshes.new("cliff_far_toe")
    me.from_pydata(V, [], [f for f in F])
    me.validate()
    o = bpy.data.objects.new("cliff_far_toe", me)
    src = bpy.data.objects["cliff_far"]
    for m in src.data.materials:
        me.materials.append(m)
    bpy.data.collections["CONTEXT"].objects.link(o)
    log("NEW", "cliff_far_toe", "far shore y %.0f..%.0f, lip cut to each pool level" % (FAR - 1, FARWALL + 1))


def farwall_look():
    """Aerial perspective on the new far wall  (idempotent — safe to re-run).

    At 16 m the far wall was a sliver; at 48 m it is a third of every frame that
    looks north, and in `m_rock` under the lifted grade it rendered the same pale
    value as the sunlit water, so bank and water merged into one white field.
    The district already owns the material for this — `mat_rock_far`, the hazed
    far-rock the upstream ridges are drawn in (manifest finding 52/53: the value,
    not the geometry, is what reads as distance).
    """
    src = bpy.data.materials.get("mat_rock_far")
    assert src, "mat_rock_far (the district's hazed far-rock) is missing"
    far = bpy.data.materials.get("mat_rock_farwall")
    if far is None:
        far = src.copy()
        far.name = "mat_rock_farwall"
    # mat_rock_far is tuned for ridges 100 m up the valley: it crushes to 0.12 and
    # is 85% haze, which puts the far WALL at the same value as the black-stone
    # dam in front of it and kills the dam's silhouette.  The wall is 58 m away,
    # not 130 — half the haze, and a mid value that sits between the sunlit water
    # and the dam.
    nt = far.node_tree
    nt.nodes["Mix.002"].inputs[7].default_value = (0.30, 0.295, 0.30, 1.0)   # crush target
    nt.nodes["Mix.001"].inputs[0].default_value = 0.60                        # haze mix
    for nm in ("cliff_far", "cliff_far_toe"):
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        old = o.data.materials[0].name if o.data.materials else "-"
        o.data.materials.clear()
        o.data.materials.append(far)
        log("MATERIAL", nm, "%s -> mat_rock_farwall (aerial perspective across a 48 m gorge)" % old)


def relight_gorge():
    """The district's sky fill has to cover the gorge it is the sky of.

    `SKY_wash` is a 46 x 34 area lamp centred on y=30 — sized for a 16 m river.
    Everything the widening put north of y~53 (two thirds of the new Lock Four
    dam) fell outside it and rendered as an unlit black mass: the extension was
    modelled correctly and simply had no light on it.  Widened along the river
    axis and re-centred on the gorge, with the power scaled by the same factor so
    the ACCEPTED yard keeps its irradiance (manifest finding 53 — the value gap is
    what reads as two datasets).  Absolute values, so a re-run is idempotent.
    """
    o = bpy.data.objects.get("SKY_wash")
    if not o:
        return
    d = o.data
    old = (d.size, o.location.y, d.energy)
    want_size = 90.0                       # local X == world Y at this lamp's yaw
    if abs(d.size - want_size) > 0.01:
        d.energy = round(d.energy * want_size / d.size, 1)
        d.size = want_size
    o.location.y = CY - 2.0
    log("LIGHT", "SKY_wash", "size %.0f -> %.0f along the river, y %.0f -> %.0f, "
        "energy %.0f -> %.0f (same irradiance, covers the 48 m gorge)"
        % (old[0], d.size, old[1], o.location.y, old[2], d.energy))


def span_dam_five():
    """Blockout Lock Five: wall + crest + foam re-spanned, wheels redistributed."""
    for nm, half in (("dam_dam-five_wall", RW / 2 + 1), ("dam_dam-five_crest", RW / 2 + 1),
                     ("dam_dam-five_foam", RW / 2 - 1)):
        o = bpy.data.objects[nm]
        b = wbb(o)
        mid = (b[2] + b[3]) / 2.0
        Mi = o.matrix_world.inverted()
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            v.co = Mi @ Vector((p.x, CY - half if p.y < mid else CY + half, p.z))
        o.data.update()
        log("STRETCH", nm, "y %.0f..%.0f -> %.0f..%.0f" % (b[2], b[3], CY - half, CY + half))
    n = len([o for o in bpy.data.objects if o.name.startswith("dam_dam-five_wheel")])
    for i in range(n):
        o = bpy.data.objects["dam_dam-five_wheel%d" % i]
        b = wbb(o)
        want = NEAR + (i + 1) * RW / (n + 1.0)
        shift(o, want - (b[2] + b[3]) / 2.0)
        log("MOVE", o.name, "wheel centre y %.1f -> %.1f (3 wheels across the new span)"
            % ((b[2] + b[3]) / 2.0, want))


# ===========================================================================
# 2. district river — riverbed + the Lock Four dam extension
# ===========================================================================
DAMX0, DAMX1 = 12.35, 15.85
GATE_HW = 1.15
GAL_Z = 5.35
DAM_N = 76.0                          # north end of weir / crest / gallery
ABUT_N = 87.0                         # far abutment buried in the new cliff (face y=84)
SRC_GATE_Y = 39.4                     # northernmost existing bay = the duplication source
NEW_GATE_Y = (46.0, 56.0, 66.0)       # three more spill bays across the new span

# component signatures of the dam's REPEATING units, keyed (x0,x1,z0,z1) rounded.
# Everything else inside a bay window is bay art.
REPEAT = {
    "pier":     (15.85, 16.47, -1.20, 4.30),
    "crestpost": (12.17, 12.33, 4.62, 6.30),
    "galpierW": (12.53, 12.77, 4.35, 5.35),
    "galpierE": (15.43, 15.67, 4.35, 5.35),
    "galpost":  (15.99, 16.10, 5.51, 6.41),
}
REPEAT_PITCH = {"pier": 1.55, "crestpost": 2.90, "galpierW": 1.42, "galpierE": 1.42,
                "galpost": 0.72}


def comps(bm):
    seen, out = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        stack, grp = [v], []
        seen.add(v)
        while stack:
            u = stack.pop(); grp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w not in seen:
                    seen.add(w); stack.append(w)
        out.append(grp)
    return out


def cbb(grp):
    return (min(v.co.x for v in grp), max(v.co.x for v in grp),
            min(v.co.y for v in grp), max(v.co.y for v in grp),
            min(v.co.z for v in grp), max(v.co.z for v in grp))


def sig_is(b, s, tol=0.02):
    """Does this component's (x0,x1,z0,z1) match a repeating-unit signature?"""
    return all(abs(a - c) <= tol for a, c in zip((b[0], b[1], b[4], b[5]), s))


def which_repeat(b):
    for name, s in REPEAT.items():
        if sig_is(b, s):
            return name
    return None


def dup_group(bm, verts, dy):
    vs = set(verts)
    geom = list(vs)
    geom += [e for e in bm.edges if e.verts[0] in vs and e.verts[1] in vs]
    geom += [f for f in bm.faces if all(v in vs for v in f.verts)]
    r = bmesh.ops.duplicate(bm, geom=geom)
    for el in r["geom"]:
        if isinstance(el, bmesh.types.BMVert):
            el.co.y += dy
    return r


def bbox(bm, x0, x1, y0, y1, z0, z1, mi):
    vs = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f]).material_index = mi


def phase_lockfour():
    print("\n--- 2b. Lock Four dam extension ------------------------------------")
    o = bpy.data.objects["lock_four_dam"]
    assert all(abs(o.matrix_world[r][c] - (1.0 if r == c else 0.0)) < 1e-6
               for r in range(4) for c in range(4)), \
        "lock_four_dam matrix is not identity — local edits would land in the wrong place"
    STONE = [i for i, m in enumerate(o.data.materials) if m and m.name == "mat_blackstone"][0]

    bm = bmesh.new(); bm.from_mesh(o.data)
    groups = comps(bm)
    tally = {"stretch": 0, "repeat": 0, "bay": 0}

    # -- 2b.i  the long spanning elements run north to the far abutment -------
    #    (the three string courses also end at y=44 but must NOT run through the
    #     new bays, so they are rebuilt segment-by-segment below)
    COURSE = (15.85, 16.05)
    course_z = []
    for g in groups:
        b = cbb(g)
        is_course = (abs(b[0] - COURSE[0]) < 0.02 and abs(b[1] - COURSE[1]) < 0.02 and b[4] < 4.2)
        if b[3] < 43.95:
            continue
        if is_course:
            course_z.append(round(b[4], 2))
            continue
        for v in g:
            if v.co.y > 43.95:
                v.co.y = DAM_N
        tally["stretch"] += 1
    assert len(course_z) == 3, "expected 3 string courses ending at the old dam end, got %s" % course_z
    log("STRETCH", "lock_four_dam spanning", "%d elements (weir, crest, cap, parapet, gallery deck, "
        "4 rails) y 44.0 -> %.1f" % (tally["stretch"], DAM_N))

    # -- 2b.ii  the repeating masonry / gallery units carry on at their pitch --
    by_sig = {}
    for g in groups:
        w = which_repeat(cbb(g))
        if w:
            by_sig.setdefault(w, []).append(g)
    for name, s in REPEAT.items():
        cand = by_sig.get(name, [])
        assert cand, "repeat unit %s not found (%s)" % (name, s)
        src = min(cand, key=lambda g: cbb(g)[2])
        b = cbb(src)
        pitch = REPEAT_PITCH[name]
        k0 = int(round((max(cbb(g)[2] for g in cand) - b[2]) / pitch)) + 1
        n = 0
        k = k0
        while b[3] + k * pitch <= DAM_N:
            dup_group(bm, src, k * pitch)
            n += 1; k += 1
        tally["repeat"] += n
        log("REPEAT", name, "%d more at pitch %.2f, to y=%.2f" % (n, pitch, b[3] + (k - 1) * pitch))

    # -- 2b.iii  three more spill bays, DUPLICATED from the northernmost bay ---
    lo, hi = SRC_GATE_Y - 1.45, SRC_GATE_Y + 1.45
    bay, nparts = [], 0
    for g in groups:
        b = cbb(g)
        if b[2] < lo or b[3] > hi or which_repeat(b):
            continue
        bay += g
        nparts += 1
    assert nparts == 17, "bay source should be 17 parts (slots, lintel, leaf, bands, stiles, " \
                         "hinges, winding gear, fall, crest foam, plunge), got %d" % nparts
    for gy in NEW_GATE_Y:
        dup_group(bm, bay, gy - SRC_GATE_Y)
        tally["bay"] += 1
    log("DUPLICATE", "spill bays", "%d new bays (%s) x %d parts, cloned from the bay at y=%.1f"
        % (len(NEW_GATE_Y), ", ".join("%.0f" % g for g in NEW_GATE_Y), nparts, SRC_GATE_Y))

    # -- 2b.iv  string courses across the new span, broken around the new bays -
    segs, y = [], 44.0
    for gy in NEW_GATE_Y:
        if gy - GATE_HW > y:
            segs.append((y, gy - GATE_HW))
        y = gy + GATE_HW
    segs.append((y, DAM_N))
    for zc in sorted(course_z):
        for ya, yb in segs:
            bbox(bm, COURSE[0], COURSE[1], ya, yb, zc, zc + 0.26, STONE)
    log("BUILD", "string courses", "%d segments x 3 courses across y 44..%.0f, broken at each bay"
        % (len(segs), DAM_N))

    # -- 2b.v  the far abutment: the dam lands in the new cliff ---------------
    bbox(bm, DAMX0, DAMX1, DAM_N - 0.6, ABUT_N, -1.6, 6.20, STONE)          # abutment mass
    bbox(bm, DAMX0 - 0.36, DAMX1 + 0.36, DAM_N - 0.6, ABUT_N, 6.20, 6.55, STONE)   # its cap
    bbox(bm, DAMX0 - 0.50, DAMX1 + 0.50, DAM_N + 0.2, DAM_N + 4.6, 6.55, 12.40, STONE)  # turret
    bbox(bm, DAMX0 - 0.80, DAMX1 + 0.80, DAM_N - 0.1, DAM_N + 4.9, 12.40, 12.95, STONE)  # turret cap
    log("BUILD", "far abutment + turret", "y %.1f..%.1f, set into the new far cliff (face y=%.0f)"
        % (DAM_N - 0.6, ABUT_N, FARWALL))

    bm.to_mesh(o.data); bm.free(); o.data.update()
    b = (min(v.co.x for v in o.data.vertices), max(v.co.x for v in o.data.vertices),
         min(v.co.y for v in o.data.vertices), max(v.co.y for v in o.data.vertices),
         min(v.co.z for v in o.data.vertices), max(v.co.z for v in o.data.vertices))
    print("   lock_four_dam now x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]  %d verts"
          % (b[0], b[1], b[2], b[3], b[4], b[5], len(o.data.vertices)))
    return tally


def phase_district_river():
    print("\n--- 2a. district river ---------------------------------------------")
    rb = bpy.data.objects["riverbed"]
    b = wbb(rb)
    pull_north(rb, (b[2] + b[3]) / 2.0, FAR + 4.0)
    log("STRETCH", "riverbed", "far edge y %.0f -> %.0f (under the new water)" % (b[3], FAR + 4))
    for nm, tgt in (("dam4_lip", DAM_N), ("fx_dam4_foam", DAM_N), ("fx_dam4_spray", DAM_N + 1.5)):
        o = bpy.data.objects[nm]
        b = wbb(o)
        pull_north(o, (b[2] + b[3]) / 2.0, tgt)
        log("STRETCH", nm, "far edge y %.1f -> %.1f (spans the whole new weir)" % (b[3], tgt))


# ===========================================================================
# 3. fx_* atmosphere — the distance layering follows the new gorge
# ===========================================================================
def phase_fx():
    print("\n--- 3. fx atmosphere ------------------------------------------------")
    for nm in ("fx_haze_far", "fx_haze_mid", "fx_haze_rim",
               "fx_ridge_upstream", "fx_ridge_upstream_mid"):
        o = bpy.data.objects[nm]
        b = wbb(o)
        dy = CY - (b[2] + b[3]) / 2.0
        shift(o, dy)
        log("MOVE", nm, "recentred on the gorge, y %+.1f (centre %.1f -> %.1f)"
            % (dy, (b[2] + b[3]) / 2.0, CY))
    # the far-town silhouette reads across the gorge mouth: widen with the river
    # and sit it toward the far side so it belongs to the new far rim.
    o = bpy.data.objects["fx_far_town_silhouette"]
    o.scale.y *= 1.6                     # widen with the gorge, not 3x (it is a distant town)
    b = wbb(o)
    shift(o, (CY + 6.0) - (b[2] + b[3]) / 2.0)
    log("SCALE", "fx_far_town_silhouette", "y x1.60 and recentred to %.0f (far side of the gorge)"
        % (CY + 6.0))
    crowns = [c for c in bpy.data.objects if c.name.startswith("farwallcrown_")]
    dy = FARWALL - 58.0
    for c in crowns:
        shift(c, dy)
    log("MOVE", "farwallcrown_* (%d)" % len(crowns),
        "autumn crowns follow the far wall, y %+.0f (onto the new far rim)" % dy)


# ===========================================================================
# 4. trim the boatyard spars  (KITLIB finding 57)
# ===========================================================================
def phase_spars():
    print("\n--- 4. spar trim ----------------------------------------------------")
    o = bpy.data.objects["foreground_timber"]
    shed = wbb(bpy.data.objects["boatwright_shed"])
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = []
    for g in comps(bm):
        b = cbb(g)
        # a spar is timber whose HEAD is inside the shed volume: it stands on the
        # yard and drives its top through the shed wall.  From the hero camera it
        # framed the shot; from the other seven it is a beam stabbing the yard.
        top = max(g, key=lambda v: v.co.z).co
        if (shed[0] < top.x < shed[1] and shed[2] < top.y < shed[3] and top.z < shed[5]):
            kill += g
            log("DELETE", "fg spar", "head (%.1f, %.1f, %.1f) is inside boatwright_shed — "
                "unsupported beam from every non-hero angle" % (top.x, top.y, top.z))
    assert len(kill) == 16, "expected exactly the 2 spars (16 verts), got %d" % len(kill)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(o.data); bm.free(); o.data.update()
    b = wbb(o)
    print("   foreground_timber now x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f] %d verts "
          "(trestles + board stack kept: they stand on the hard and carry the boards)"
          % (b[0], b[1], b[2], b[3], b[4], b[5], len(o.data.vertices)))


# ===========================================================================
# 5. grade
# ===========================================================================
def phase_grade():
    print("\n--- 5. grade --------------------------------------------------------")
    sc = bpy.context.scene
    old = sc.view_settings.exposure
    sc.view_settings.exposure = 0.35
    log("GRADE", "exposure %.2f -> +0.35" % old, "user pick (docs/qa/districts/exposure_lifted.png)")


def already_run():
    return wbb(bpy.data.objects["cliff_far"])[2] > FARWALL - 1.0


def main():
    print("=" * 78)
    print("MASTER RIVER WIDEN — width %g, centreY %g, farWallY %g" % (RW, CY, FARWALL))
    print("=" * 78)
    if already_run():
        # the widening itself is one-shot; the look phases are not, so a re-run
        # is the way to iterate on grade / far-wall value without redoing geometry.
        print("river already widened — running the idempotent look phases only")
        farwall_look()
        relight_gorge()
        phase_grade()
        bpy.ops.wm.save_mainfile()
        print("SAVED %s (look only)" % bpy.data.filepath)
        return
    preflight()
    phase_context()
    phase_district_river()
    t = phase_lockfour()
    phase_fx()
    phase_spars()
    phase_grade()
    bpy.ops.wm.save_mainfile()
    print("\n" + "=" * 78)
    print("SAVED %s" % bpy.data.filepath)
    print("dam: %d spanning stretched, %d repeat units added, %d bays duplicated"
          % (t["stretch"], t["repeat"], t["bay"]))
    print("=" * 78)


main()
