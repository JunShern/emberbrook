"""valley_build.py — build THE VALLEY region (chapters 1-2) in style F2.

  Blender -b --factory-startup -P tools/valley_build.py

The first real overworld region, replacing the 120 x 90u prototype tile.  It is
280 x 200u of terrain and it AUTHORS NOTHING about its own geography: every height,
every zone, the river, the road, the forests, the town anchors and the rim
treatments are read from

    public/world/world.json                  (spine, massifs, envelopes, graph)
    public/world/regions/valley.region.json  (the region's own refinement)

through tools/valley_map.py.  Edit the map, re-run this, get the same tile back.

REUSE.  The style is F2, unchanged: overworld3_lib's zone grid, zone-driven
tessellation and crag treatment, its four tree constructions and procedural
vegetation maps; overworld2_lib's tar boat, mooring basin and jetty;
overworld2_build's PBR material recipe; overworld_build's Prop accumulator, class
palette and dusk rig; overworld3_build's terrain material pass verbatim.  What is
new here is region CONTENT that the prototype had no equivalent of:

    * the two TOWN IMPRESSIONS (Emberbrook's plateau village, Dellhollow's
      gorge-straddling stepped clusters with its weir flight)
    * the two PORTAL markers
    * region PLANTING: the map's forest stamps, approach (a) in the stands and
      hybrid (c) breaking their edges, with the road held as a corridor
    * the VISTA RING, generated from the PARENT's coarse data
"""
import bpy
import bmesh
import json
import math
import os
import random
import sys
import time

import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valley_map as VM            # FIRST: re-points overworld_lib at the region
import overworld_lib as L
import overworld_build as B
import overworld2_lib as O2
import overworld2_build as B2
import overworld3_lib as O3
import overworld3_build as B3      # F2's material + vertex-colour passes
import valley_veg as VV            # this region's forest, rock and meadow
import valley_land as VL           # L2/L3: the landscape pass (docs/qa/ow-land)

# The canyon rebuild puts more crag beside the gorge-rim climb than F2's tile ever
# had, and the 0.16u road notch no longer clears the terrain/ribbon sawtooth
# (verify measured a 0.088u pierce).  Deepen the worn corridor: invisible at this
# scale, and a canyon road WOULD be cut deeper into its shelf.
_rn_o3 = O3.road_notch
O3.road_notch = lambda F, x, y, depth=0.28: _rn_o3(F, x, y, depth)

ROOT = VM.ROOT
STYLE = "f2"                       # the TREATMENT is F2's, byte for byte
SUF = "valley"
OUT_BLEND = os.path.join(ROOT, "tools/blends/overworld-valley.blend")
BUNDLE = os.path.join(ROOT, "public/assets/scenes/ow-valley")

srgb = B.srgb
(GRASS, GRASS_HI, AUTUMN, ROCK, PEAK, SAND, DIRT, WATER, WALL, ROOF, WOOD, STONE,
 FOL_A, FOL_B, FOL_C, TRUNK, EMIT, BASE, METAL, MIST) = range(20)
TAR, CANVAS, ROPE, LEAF, TUFT, LAMP = range(20, 26)
LEAFM, LEAFC, BARK, MARK = O3.LEAFM, O3.LEAFC, O3.BARK, O3.MARK

HOUSE_RIDGE = VM.HOUSE_RIDGE       # 3.7u — the scale contract beside a 1.45u character
HOUSE_EAVE = 1.80                  # wall-plate height before the per-house factor
STATS = {}


def gh(F, zg, fr, x, y):
    """The BUILT ground height at one point (crag treatment included)."""
    return float(O3.height(F, zg, np.array([float(x)]), np.array([float(y)]), fr)[0])


def ghv(F, zg, fr, x, y):
    return O3.height(F, zg, np.asarray(x, float), np.asarray(y, float), fr)


# =============================================================================
# WATER, ROAD, GREEN — the ribbons
# =============================================================================
# B1 GLASS RIVER (user pick, 2026-08-03, from docs/qa/ow-art/index.html section B).
# The probe's B1 is four numbers on ONE material — colour, opacity, roughness,
# metalness — and this is what it takes to make them survive the glTF export.
#
# THE RIVER SHIPPED FULLY OPAQUE AND NOBODY MEANT IT TO.  `new_mat(..., alpha=0.82,
# blend=True)` sets the BSDF Alpha default AND links COLOR_0's alpha into the same
# socket; the link wins, every water vertex carries alpha 1.0, and the exporter
# writes no baseColorFactor at all.  Measured in the shipped bundle before this
# change: ow_f2_water = {metallic 0, roughness 0.28}, no factor, and COLOR_0 alpha
# = 1.000 on all 672/2496/1212/108 water vertices.  The 0.82 was a Blender-only
# number for four weeks.  That is the mechanism behind the probe's "water is an
# opaque plate", and it is a bug, not a taste call.
#
# TWO EXPORTER FACTS, MEASURED (scratchpad probe, Blender 5.1.1, three planes):
#   * an UNLINKED Alpha socket exports as baseColorFactor[3].  So the alpha has to
#     come off the vertex link to reach the runtime — which costs nothing here,
#     because that link was only ever carrying 1.0.
#   * `ShaderNodeMix` (data_type RGBA, MULTIPLY) of COLOR_0 x a constant exports
#     the constant as baseColorFactor.rgb.  The LEGACY `ShaderNodeMixRGB` in the
#     same position exports [1,1,1] — the tint is dropped SILENTLY.  Use the new
#     node or the colour never leaves Blender.
# Nothing else is needed: three's GLTFLoader turns alphaMode BLEND into
# transparent=true + depthWrite=false, which is the rest of the probe's recipe.
GLASS = "#bfe6ee"        # probe B1's tint, sRGB
GLASS_OPACITY = 0.62
GLASS_ROUGH = 0.06


def _srgb_to_linear(hex_):
    out = []
    for i in (0, 2, 4):
        c = int(hex_.lstrip("#")[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def glass_water(m, tint=GLASS, opacity=GLASS_OPACITY, rough=GLASS_ROUGH):
    """Re-cut `ow_f2_water` as the probe's B1 glass river."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    vc = next((n for n in nt.nodes if n.type == "VERTEX_COLOR"), None)
    old = nt.nodes.get("glass_tint")
    if old is not None:                       # idempotent: a re-run re-cuts, never stacks
        nt.nodes.remove(old)
        if vc is not None:
            nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
    # `lk.to_socket is b.inputs["Alpha"]` is FALSE even for the right link: the RNA
    # accessor hands back a fresh proxy every lookup, so identity never matches and
    # the first pass left the vertex-alpha link in place with the default underneath
    # it (printed alpha=0.62, exported 1.0). Match by node + socket NAME.
    for lk in list(nt.links):
        if lk.to_node == b and lk.to_socket.name == "Alpha":
            nt.links.remove(lk)
    b.inputs["Alpha"].default_value = float(opacity)
    b.inputs["Roughness"].default_value = float(rough)
    b.inputs["Metallic"].default_value = 0.0
    lin = _srgb_to_linear(tint)
    if vc is not None:
        mx = nt.nodes.new("ShaderNodeMix")
        mx.name = mx.label = "glass_tint"
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.location = (-160, 120)
        mx.inputs["Factor"].default_value = 1.0
        nt.links.new(vc.outputs["Color"], mx.inputs[6])
        mx.inputs[7].default_value = (*lin, 1.0)
        nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = (*lin, 1.0)
    print("  water: B1 glass  tint %s -> linear %s, opacity %.2f, rough %.2f"
          % (tint, ", ".join("%.4f" % v for v in lin), opacity, rough))
    return m


def build_water(col, F):
    """The river surface, at the PARENT spine's width profile.

    The widening (3u at Ember Falls to 22u at the SE exit) is story-load-bearing:
    it is why a boat can leave from the Moorage and could not leave from anywhere
    upstream, so it is driven straight off world.json's own width column.
    """
    xy = VM.RIV_XY[::3]
    t = VM.RIV_T[::3]
    hw = VM.water_halfwidth(t) * 1.03
    wl = VM.water_level(t)
    tg = np.gradient(xy, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nx, ny = -tg[:, 1], tg[:, 0]
    bx, by = xy[:, 0] - VM.CX, xy[:, 1] - VM.CY
    p = B.Prop("water_river")
    p.strip(WATER, list(zip(bx + nx * hw, by + ny * hw, wl)),
            list(zip(bx - nx * hw, by - ny * hw, wl)))
    ob = p.finish(col)
    STATS["river_width"] = (float(VM.RIV_WIDTH[0]), float(VM.RIV_WIDTH[-1]))
    return ob


def build_tributaries(col, F, zg, fr):
    """The found ravines, given a waterline — the river's growth, made visible.

    The user's note was that the gorge grows 4.5u -> 28u with nothing feeding it.
    These two are not drawn: `region.tributaries` records the flow-accumulation probe
    that found them and the accumulation each mouth scored.  The build's only job is
    to lay a thin water strip in the groove valley_map already carved, ON THE GROUND
    that is actually there — the strip's z is the lower of the traced z and the built
    surface, so a ravine cannot end up running along the air above its own bed.
    """
    if not VM.TRIBS:
        return None
    p = B.Prop("water_tributaries")
    n = 0
    for t in VM.TRIBS:
        xy = t["xy"]
        bx, by = xy[:, 0] - VM.CX, xy[:, 1] - VM.CY
        gz = ghv(F, zg, fr, bx, by)
        z = np.minimum(t["z"], gz) + 0.05
        z = np.minimum.accumulate(z)
        tg = np.gradient(xy, axis=0)
        tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
        nx, ny = -tg[:, 1], tg[:, 0]
        hw = t["w"] * 0.5
        p.strip(WATER, list(zip(bx + nx * hw, by + ny * hw, z)),
                list(zip(bx - nx * hw, by - ny * hw, z)))
        # where it drops more than 1.2u between samples it is falling, not flowing:
        # a short curtain so the far wall reads wet rather than striped
        for k in range(1, len(z)):
            if z[k - 1] - z[k] > 1.2:
                p.cube(WATER, (float((bx[k] + bx[k - 1]) / 2), float((by[k] + by[k - 1]) / 2),
                               float((z[k] + z[k - 1]) / 2)),
                       (0.34, t["w"] * 0.92, float(max(0.4, abs(z[k - 1] - z[k])) * 1.05)),
                       rz=math.atan2(float(tg[k, 1]), float(tg[k, 0])))
                n += 1
    STATS["tributaries"] = [(t["id"], round(float(t["s"][-1]), 1), round(t["drop"], 1))
                            for t in VM.TRIBS]
    STATS["tributary_falls"] = n
    print("TRIBUTARIES: %s (%d falling segments)"
          % ("; ".join("%s %.1fu falling %.1fu" % (t["id"], t["s"][-1], t["drop"])
                       for t in VM.TRIBS), n))
    return p.finish(col)


def build_falls(col, F, zg, fr):
    """EMBER FALLS — the plunge, built as a plunge.

    The water surface is one strip following the river's authored z, so a 5.76u drop
    over 2u of arc came out as a very steep RAMP: measured it is a waterfall, rendered
    it was a chute, and this is a named landmark on the world map.  Three things make a
    fall read and this adds those and nothing else: a hard rock LIP the water visibly
    leaves, a near-vertical CURTAIN hung from it, and a PLUNGE POOL with churn at its
    foot.  The reach is FOUND, not typed — the lip is where the water's gradient first
    breaks 1.0u per unit of arc and the foot where it falls back under 0.4 — so a
    restamped river moves the fall with it, the same rule the mesa lip now follows.
    """
    S = VM.RIV_S
    wl_all = VM.water_level(VM.RIV_T)
    grad = np.zeros_like(wl_all)
    grad[1:] = -np.diff(wl_all) / np.maximum(np.diff(S), 1e-6)
    fi = int(np.argmin(np.hypot(VM.RIV_XY[:, 0] - VM.LAND_W["ember-falls"][0],
                                VM.RIV_XY[:, 1] - VM.LAND_W["ember-falls"][1])))
    lip = fi
    while lip > 1 and grad[lip] > 1.0:
        lip -= 1
    foot = fi
    while foot < len(S) - 2 and grad[foot + 1] > 0.4:
        foot += 1
    if S[foot] - S[lip] < 0.5 or wl_all[lip] - wl_all[foot] < 1.5:
        print("build_falls: no plunge at ember-falls (%.2fu over %.2fu) — nothing built, "
              "and that is a fact about the map, not a build failure"
              % (wl_all[lip] - wl_all[foot], S[foot] - S[lip]))
        return None
    p = B.Prop("water_falls")
    z_top, z_bot = float(wl_all[lip]), float(wl_all[foot])
    STATS["falls_drop_u"] = round(z_top - z_bot, 2)
    STATS["falls_run_u"] = round(float(S[foot] - S[lip]), 2)

    def frame(i):
        tg = VM.RIV_XY[min(i + 1, len(S) - 1)] - VM.RIV_XY[max(i - 1, 0)]
        tg = tg / max(float(np.hypot(*tg)), 1e-9)
        return (VM.RIV_XY[i] - np.array([VM.CX, VM.CY]), tg,
                np.array([-tg[1], tg[0]]),
                float(VM.water_halfwidth(np.array([VM.RIV_T[i]]))[0]))

    c0, t0, n0, hw0 = frame(lip)
    c1, t1, n1, hw1 = frame(foot)
    ang0 = math.atan2(float(t0[1]), float(t0[0]))
    # 1. THE LIP — a hard rock sill, so the water leaves the GROUND, not a slope
    for k in range(7):
        u = (k - 3) / 3.0
        p.cube(STONE, (float(c0[0] + n0[0] * u * hw0 * 1.12),
                       float(c0[1] + n0[1] * u * hw0 * 1.12), z_top - 0.20),
               (1.5, hw0 * 0.42, 0.9), rz=ang0)
    # 2. THE CURTAIN — sheets hung from the lip, bowed downstream at the centre so it
    #    catches light as a face instead of as a seam
    nseg, nrow = 9, 5
    for k in range(nseg):
        u = (k + 0.5) / nseg * 2.0 - 1.0
        bow = (1.0 - u * u) * 0.55
        for r in range(nrow):
            fmid = (r + 0.5) / nrow
            zz = z_top - (z_top - z_bot) * fmid
            ax = c0 + (c1 - c0) * fmid * 0.55 + t0 * bow
            p.cube(WATER, (float(ax[0] + n0[0] * u * hw0),
                           float(ax[1] + n0[1] * u * hw0), zz),
                   (0.55, hw0 * 2.0 / nseg * 1.06, (z_top - z_bot) / nrow * 1.04), rz=ang0)
    # 3. THE PLUNGE POOL and its churn — a fall with no foam is a pane of glass
    p.cone(WATER, (float(c1[0]), float(c1[1]), z_bot + 0.06),
           hw1 * 1.45, hw1 * 1.45, 0.12, seg=16)
    rng = random.Random(20260801)
    for k in range(22):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.15, 1.15) * hw1
        px = float(c1[0] + math.cos(a) * rr + (c0[0] - c1[0]) * rng.uniform(0.0, 0.35))
        py = float(c1[1] + math.sin(a) * rr + (c0[1] - c1[1]) * rng.uniform(0.0, 0.35))
        s_ = rng.uniform(0.30, 0.78)
        p.ico(WATER, (px, py, z_bot + rng.uniform(0.05, 1.25)), (s_, s_, s_ * 0.72), subd=1)
    print("EMBER FALLS: lip arc %.1fu z %.2f -> foot arc %.1fu z %.2f = %.2fu of free "
          "water over %.2fu of run (curtain %dx%d, 22 churn)"
          % (S[lip], z_top, S[foot], z_bot, z_top - z_bot, S[foot] - S[lip], nseg, nrow))
    return p.finish(col)


def _ribbon(p, cls, xy, z, hw):
    tg = np.gradient(xy, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nx, ny = -tg[:, 1], tg[:, 0]
    p.strip(cls, list(zip(xy[:, 0] + nx * hw, xy[:, 1] + ny * hw, z)),
            list(zip(xy[:, 0] - nx * hw, xy[:, 1] - ny * hw, z)))


def build_road(col, F):
    """walk_road — the visible road AND the walk network, on its authored z.

    The edge is deliberately SCRUFFY (user note: clean edges read as paving):
    the halfwidth wanders +-35% along the stations, independently per side."""
    xy = np.column_stack([F.road[:, 0], F.road[:, 1]])
    p = B.Prop("walk_road")
    s_ = F.road_s
    wob_l = 1.0 + 0.35 * np.sin(s_ * 0.61 + 0.9) * np.abs(np.sin(s_ * 0.173 + 2.2))
    wob_r = 1.0 + 0.35 * np.sin(s_ * 0.53 - 1.7) * np.abs(np.sin(s_ * 0.191 + 0.4))
    tg = np.gradient(xy, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nx, ny = -tg[:, 1], tg[:, 0]
    hw = VM.ROAD_WIDTH * 0.5
    z = F.road_h + 0.09
    p.strip(DIRT, list(zip(xy[:, 0] + nx * hw * wob_l, xy[:, 1] + ny * hw * wob_l, z)),
            list(zip(xy[:, 0] - nx * hw * wob_r, xy[:, 1] - ny * hw * wob_r, z)))
    return p.finish(col)


def build_causeway(col, F, zg, fr):
    """The span the map forces (see valley_map.CAUSEWAY).

    region.crossings.list is empty by ruling, but the region's road changes bank at
    the parent spine's second meander, so it must cross the water somewhere.  Rather
    than leave the ribbon hanging in mid-air over the channel, the build lays a low
    culverted causeway under it and flags it as the build's one unauthorised object.
    Delete-on-map-fix: valley_map.CAUSEWAY = False and this returns nothing.
    """
    if not VM.CAUSEWAY or not VM.ROAD_SPANS:
        return None
    p = B.Prop("walk_causeway")
    n = 0
    for (a, b) in VM.ROAD_SPANS:
        a, b = max(a - 3, 0), min(b + 3, len(F.road) - 1)
        xy = F.road[a:b + 1]
        z = F.road_h[a:b + 1]
        tg = np.gradient(xy, axis=0)
        tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
        nx, ny = -tg[:, 1], tg[:, 0]
        for side in (-1, 1):
            ex = xy[:, 0] + nx * side * 1.35
            ey = xy[:, 1] + ny * side * 1.35
            bed = ghv(F, zg, fr, ex, ey) - 0.3
            p.strip(STONE, list(zip(ex, ey, z + 0.06)), list(zip(ex, ey, bed)))
        # three culvert arches so the causeway is fill, not a dam
        for k in (0.30, 0.50, 0.70):
            i = int(k * (len(xy) - 1))
            cx_, cy_ = float(xy[i, 0]), float(xy[i, 1])
            dz = float(F._river_dist(np.array([cx_]), np.array([cy_]))[1][0])
            w = float(VM.water_level(np.array([dz]))[0])
            ang = math.atan2(float(tg[i, 1]), float(tg[i, 0]))
            p.cube(STONE, (cx_, cy_, w + 0.62), (0.9, 3.6, 0.34), rz=ang)
            n += 1
        # a CONTINUOUS kerb, not a row of posts.  With the road grade now embanking
        # the crossing, discrete posts read as cubes floating beside the ribbon.
        for side in (-1, 1):
            kx = xy[:, 0] + nx * side * 1.22
            ky = xy[:, 1] + ny * side * 1.22
            p.strip(STONE, list(zip(kx, ky, z + 0.34)), list(zip(kx, ky, z - 0.10)))
            kx2 = xy[:, 0] + nx * side * 1.02
            ky2 = xy[:, 1] + ny * side * 1.02
            p.strip(STONE, list(zip(kx, ky, z + 0.34)), list(zip(kx2, ky2, z + 0.30)))
    STATS["causeway_arches"] = n
    return p.finish(col)


# =============================================================================
# TOWN IMPRESSIONS — impressions, NOT the town models shrunk
# =============================================================================
# PER-HOUSE TINT FAMILIES.  B.write_prop_colors already jitters COLOR_0 per FACE,
# which is grain, not variety: every house still ends up the same colour because the
# jitter averages out over its dozen faces.  What reads as "several houses" is a
# whole BUILDING sharing one deviation from the palette while its neighbour shares
# another.  So the builder tags each house's faces with a family index on a bmesh
# float layer, and apply_house_tints() multiplies COLOR_0 by that family's wall and
# roof factors AFTER B3.apply_class_gains — the last write to COLOR_0 wins, and the
# gains pass would otherwise erase this.  Zero new materials, zero new triangles.
HTINT = "htint"
WALL_TINTS = [(1.00, 1.00, 1.00),        # the palette's own plaster
              (0.86, 0.82, 0.71),        # earth daub, darker and warmer
              (0.98, 1.00, 1.04)]        # limewash, a touch cooler
ROOF_TINTS = [(1.00, 1.00, 1.00),        # the palette's own tile
              (0.71, 0.78, 0.87),        # weathered slate
              (1.06, 0.85, 0.70)]        # a redder, older tile


def tint_layer(p):
    """The per-house family index layer on a B.Prop under construction."""
    return p.bm.faces.layers.float.get(HTINT) or p.bm.faces.layers.float.new(HTINT)


def apply_house_tints(ob, cls):
    """Multiply COLOR_0 by each house's family tint. Returns houses touched."""
    me = ob.data
    at = me.attributes.get(HTINT)
    if at is None:
        return 0
    fam = np.array([v.value for v in at.data])
    col = me.color_attributes.get("Col")
    if col is None:
        me.attributes.remove(at)
        return 0
    buf = np.zeros(len(me.loops) * 4, dtype=np.float64)
    col.data.foreach_get("color", buf)
    buf = buf.reshape(-1, 4)
    seen = set()
    for pi, poly in enumerate(me.polygons):
        k = int(round(float(fam[pi])))
        if k <= 0:
            continue
        c = int(cls[pi])
        m = (WALL_TINTS[(k - 1) % len(WALL_TINTS)] if c == WALL else
             ROOF_TINTS[(k - 1) % len(ROOF_TINTS)] if c == ROOF else None)
        seen.add(k)
        if m is None:
            continue
        for li in poly.loop_indices:
            buf[li, 0] *= m[0]
            buf[li, 1] *= m[1]
            buf[li, 2] *= m[2]
    col.data.foreach_set("color", buf.ravel())
    me.attributes.remove(me.attributes[HTINT])   # never reaches the GLB
    return len(seen)


# =============================================================================
# HOW TALL IS A HOUSE (2026-08-04) — one construction, both towns
# =============================================================================
# The impression houses were 1.6u to the ridge beside a 1.45u character: 1.1x her
# height, and WIDER THAN THEY WERE TALL.  Four independent observers converged on it
# by two unrelated routes — a shadow-geometry probe measured in the running page, and
# three blind art critics who saw neither the probe nor each other ("the character is
# roughly one house tall"; "the settlement reads as a tabletop model").  Two
# consequences, and the second is the one that cost a whole lighting lane:
#
#   * it reads as a MODEL.  A real cottage is 2.5-3x a person.
#   * at the 34-degree sun a shadow is 1.48x the caster's height, so a box wider than
#     it is tall throws a shadow that never clears its own footprint — and the meadow
#     camera sits 18 degrees off straight down-sun, which hides the last metre behind
#     the house.  The ONLY object in that frame with a visible shadow was the
#     character: the only thing in it taller than it is wide.  Key, frustum, texel
#     density and bias were each measured innocent (docs/qa/ow-refs/LOOP.md R8).
#     NO LIGHTING CHANGE CAN FIX A CASTER ASPECT RATIO.  This is the fix.
#
# So: ridge 3.7u (2.55x the character), eaves ~2.2u, footprint ~1.5 x 1.3u, giving
# height:width ~2.0 — and the silhouette is broken on purpose (a chimney that clears
# the ridge, an eave board, a lean-to on a third of them), because "a single flat
# colour per face plus a glowing window decal is a blockout, and it is the loudest
# tell in the frame."  A DOOR IS THE SCALE CUE: it is the one element a viewer reads
# as person-sized without being told, and it is what turns a big box into a building.
HOUSE_KINDS = 3


def house_dims(rng):
    """Per-house proportions: ONE apparent-size factor plus a KIND.

    Scale jitter alone makes fourteen copies of one house at fourteen sizes.  The
    kind changes the PROPORTION — a cottage, a cottage with a lean-to, and a tall
    narrow two-storey — so the row does not read as one asset.
    """
    s = 0.86 + rng.uniform(0.0, 0.30)
    kind = rng.randrange(HOUSE_KINDS)
    w = (1.94 + rng.uniform(0, 0.46)) * s        # across the ridge (the eave walls)
    d = (1.68 + rng.uniform(0, 0.42)) * s        # along the ridge (the gable ends)
    eh = (HOUSE_EAVE + rng.uniform(0, 0.30)) * s
    rh = HOUSE_RIDGE * s + rng.uniform(-0.14, 0.34)
    if kind == 2:                                # the two-storey: taller AND narrower
        w *= 0.82
        d *= 0.90
        eh *= 1.22
        rh *= 1.10
    return s, w, d, eh, rh, kind


def house_ground(F, zg, fr, px, py, w, d, yaw):
    """The four footprint corners' ground heights (plus a little margin)."""
    ca, sa = math.cos(yaw), math.sin(yaw)
    hw, hd = w * 0.62, d * 0.62
    return [gh(F, zg, fr, px + ca * u * hw - sa * v * hd,
               py + sa * u * hw + ca * v * hd)
            for u in (-1, 1) for v in (-1, 1)]


def impression_house(p, ht, fam, px, py, yaw, dims, ch, rng):
    """ONE overworld impression house.  Returns its ridge height above `min(ch)`.

    `ch` is house_ground()'s four corner heights.  The floor sits above the HIGHEST
    of them and the stone footing reaches below the LOWEST, so a house on a slope
    MEETS the ground instead of being cut by it on a straight line — which is the
    critics' "every house floats, no contact shading where wall meets ground", in
    geometry rather than in a shader.  The footing is also the dark band.
    """
    s, w, d, eh, rh, kind = dims
    before = set(p.bm.faces)
    ca, sa = math.cos(yaw), math.sin(yaw)

    def at(u, v, z):                    # local (across-ridge, along-ridge, up) -> world
        return (px + ca * u - sa * v, py + sa * u + ca * v, z)

    fl = max(ch) + 0.20                                     # the floor
    ft = max(0.48, fl - (min(ch) - 0.40))                   # ...down past the low corner
    p.cube(STONE, at(0, 0, fl - ft / 2), (w * 1.07, d * 1.07, ft), rz=yaw)
    p.cube(WALL, at(0, 0, fl + eh / 2), (w, d, eh), rz=yaw)
    # the eave board: the dark line every real building has where its roof meets its
    # wall, and the cheapest thing in this file that stops a wall reading as a decal.
    p.cube(WOOD, at(0, 0, fl + eh + 0.05), (w * 1.31, d * 1.18, 0.13), rz=yaw)
    p.prism(ROOF, at(0, 0, fl + eh + 0.11), w * 1.26, d * 1.14,
            max(0.9, rh - eh - 0.11), rz=yaw)
    # CHIMNEY — an EXTERNAL STACK ON A GABLE END, not a stub on the roof slope.  The
    # old one was 0.74u and would now be buried inside the prism; a stack pushed
    # through the slope reads DETACHED from a high camera, because the half of it
    # below the ridge is hidden by the near slope.  Against the gable wall it runs
    # from the ground to above the ridge in one unbroken line: unambiguously part of
    # the building from every angle this camera can take, and the tallest, narrowest
    # thing in the frame — which is exactly what a 34-degree sun draws best.
    gs = 1.0 if rng.random() < 0.5 else -1.0        # which gable end carries it
    cw, cz0 = 0.34 + 0.10 * s, fl - 0.30
    cz1 = fl + rh + 0.26 + rng.uniform(0, 0.24)
    p.cube(STONE, at(0, gs * d * 0.60, (cz0 + cz1) / 2), (cw, 0.34, cz1 - cz0), rz=yaw)
    p.cube(STONE, at(0, gs * d * 0.60, cz1 + 0.07), (cw * 1.32, 0.48, 0.14), rz=yaw)
    # DOOR + two windows on the face the yaw points at.  The door is the scale cue;
    # the gable window is what says "there is an upstairs", which is most of the
    # difference between a tall box and a house.
    p.cube(WOOD, at(w / 2 + 0.02, d * 0.17, fl + 0.54), (0.11, 0.42, 1.08), rz=yaw)
    p.cube(EMIT, at(w / 2 + 0.02, -d * 0.22, fl + eh * 0.54), (0.09, 0.36, 0.42), rz=yaw)
    p.cube(EMIT, at(0.0, -gs * d * 0.60, fl + eh + (rh - eh) * 0.30),
           (0.30, 0.09, 0.30), rz=yaw)             # the far gable from the stack
    if kind == 1:                       # the lean-to: a third of the town is not a box
        ww, wd, weh = w * 0.60, d * 0.74, eh * 0.50
        wu = -(w / 2 + ww / 2 - 0.07)
        p.cube(STONE, at(wu, d * 0.09, fl - ft / 2), (ww * 1.08, wd * 1.08, ft), rz=yaw)
        p.cube(WALL, at(wu, d * 0.09, fl + weh / 2), (ww, wd, weh), rz=yaw)
        p.prism(ROOF, at(wu, d * 0.09, fl + weh), ww * 1.26, wd * 1.16,
                weh * 0.62, rz=yaw)
    for f in p.bm.faces:
        if f not in before:
            f[ht] = float(fam)
    return cz1 - min(ch)


def build_emberbrook(col, F, zg, fr):
    """Emberbrook: a clustered warm-lit village in a forest clearing on the plateau.

    An IMPRESSION at overworld scale: 14 houses whose ridges land at 3.7u beside a
    1.45u character, the Heartlight on its plinth at the centre (world canon: a
    Heartlight is rare and magical, and Emberbrook is the Heartlight town — the
    other lights here are ordinary lanterns), and a green for the spawn scan.
    """
    rng = random.Random(20260730)
    p = B.Prop("emberbrook")
    ht = tint_layer(p)
    cx, cy = L.VILLAGE
    h0 = F.village_h
    ring = []
    road_clear = 1e9
    for i in range(14):
        # A SETTLEMENT, NOT FOURTEEN COPIES (2026-08-04).  A blind critic comparing
        # this frame against the FFIX-reimagined overworld refs called the dressing out
        # exactly: "one house asset, ~14 copies, one scale, one rotation family, one
        # material, roughly even spacing" — and said the same fourteen with jitter would
        # read as a settlement.  Four scatter parameters, no new art:
        #   spacing  angular jitter + double the radial spread (was a fixed 2π/14 step)
        #   scale    ONE per-house factor 0.86..1.16, so w/d/h/ridge move together —
        #            per-dimension jitter alone changes proportion, not apparent size
        #   rotation still mostly faces the green (the warm window is the town's read),
        #            but every fourth house stands gable-on or askew
        #   tint     a family index carried on the faces to apply_house_tints() below
        #   shape    a KIND (house_dims): plain, lean-to, tall two-storey — added
        #            2026-08-04, because scale jitter alone is fourteen copies at
        #            fourteen sizes and the critique was about the ASSET, not the size
        a = i * (2 * math.pi / 14) + 0.22 + rng.uniform(-0.13, 0.13)
        r = 5.3 + (i % 3) * 2.25 + rng.uniform(0.0, 2.15)
        hx, hy = cx + math.cos(a) * r, cy + math.sin(a) * r
        # the ROAD passes through the village ring — a house whose footprint touches
        # it blocks the region's one route (slice agent: emberbrook_5 stood on the
        # road 3u from spawn).  A PURELY RADIAL push cannot always clear it, and the
        # 2026-08-04 rescatter proved it in a frame: a house whose bearing points
        # ALONG the road walks straight down the road as r grows, and one landed on
        # the Emberbrook gate portal itself.  Search r AND the bearing together, and
        # take the first station that clears both the road and every neighbour.
        need = VM.ROAD_WIDTH * 0.5 + 2.45
        for dr in (0.0, 0.9, 1.8, 2.7, 3.6, 4.6):
            for da in (0.0, .13, -.13, .26, -.26, .40, -.40, .55, -.55, .72, -.72):
                tx = cx + math.cos(a + da) * (r + dr)
                ty = cy + math.sin(a + da) * (r + dr)
                if float(F.road_dist(np.array([tx]), np.array([ty]))[0]) < need:
                    continue
                if not all(math.hypot(tx - ox, ty - oy) >= 3.55 for ox, oy in ring):
                    continue
                hx, hy = tx, ty
                dr = None                                  # sentinel: placed
                break
            if dr is None:
                break
        road_clear = min(road_clear,
                         float(F.road_dist(np.array([hx]), np.array([hy]))[0]))
        fa = a + math.pi + rng.uniform(-0.30, 0.30)          # mostly face the green
        if i % 4 == 1:                                        # ...but not all of them
            fa += (1.0 if rng.random() < 0.5 else -1.0) * rng.uniform(0.75, 1.25)
        dims = house_dims(rng)
        fam = 1 + (i * 5 + i // 3) % 3                        # neighbours rarely match
        ch = house_ground(F, zg, fr, hx, hy, dims[1], dims[2], fa)
        impression_house(p, ht, fam, hx, hy, fa, dims, ch, rng)
        ring.append((hx, hy))
    # ---- the Heartlight: plinth + a standing light, the town's whole identity ----
    for i in range(8):
        a = i * (2 * math.pi / 8)
        p.cube(STONE, (cx + math.cos(a) * 0.62, cy + math.sin(a) * 0.62, h0 + 0.16),
               (0.34, 0.28, 0.32), rz=a)
    p.cone(STONE, (cx, cy, h0 + 0.62), 0.34, 0.24, 1.0, seg=8)
    p.ico(EMIT, (cx, cy, h0 + 1.34), (0.36, 0.36, 0.44), subd=2)
    # ---- ordinary lanterns on posts + a low boundary fence ----
    # A post standing INSIDE a house is the tell that a scatter was written against a
    # smaller building: the footprints grew on 2026-08-04 and the two rings did not,
    # so both now skip any station a house centre has taken.
    def clear_of_houses(fx, fy, gap):
        return all(math.hypot(fx - ox, fy - oy) >= gap for ox, oy in ring)
    for k in range(5):
        a = 0.5 + k * 1.15
        fx, fy = cx + math.cos(a) * 8.4, cy + math.sin(a) * 8.4
        if not clear_of_houses(fx, fy, 2.35):
            continue
        gz = gh(F, zg, fr, fx, fy)
        p.cube(WOOD, (fx, fy, gz + 0.52), (0.12, 0.12, 1.04), rz=a)
        p.cube(EMIT, (fx, fy, gz + 1.12), (0.17, 0.17, 0.20), rz=a)
    for a in np.linspace(2.6, 5.4, 11):
        fx, fy = cx + math.cos(a) * 9.6, cy + math.sin(a) * 9.6
        if not clear_of_houses(fx, fy, 2.05):
            continue
        gz = gh(F, zg, fr, fx, fy)
        p.cube(WOOD, (fx, fy, gz + 0.30), (0.11, 0.11, 0.60), rz=a)
    STATS["emberbrook_houses"] = 14
    # the number that must never silently regress: the CLOSEST house centre to
    # the road centreline.  A house on the road is invisible in every gate this
    # repo owns and obvious in one frame — so it gets a number in valley_build.json.
    STATS["emberbrook_road_clear_u"] = round(road_clear, 2)
    return p.finish(col)


def build_emberbrook_green(col, F, zg, fr):
    """The green — a walk_ surface, so the spawn scan has somewhere sensible to land."""
    cx, cy = L.VILLAGE
    h0 = F.village_h + 0.07
    a = np.linspace(0, 2 * math.pi, 33)
    ring = [(cx + 3.4 * math.cos(t), cy + 3.4 * math.sin(t)) for t in a]
    p = B.Prop("walk_emberbrook_green")
    p.strip(GRASS, [(x, y, h0) for x, y in ring],
            [(cx + (x - cx) * 0.05, cy + (y - cy) * 0.05, h0) for x, y in ring])
    return p.finish(col)


def gorge_frame(F, wx, wy):
    """Local gorge frame at a world point: tangent, cross-normal, water level, halfwidth."""
    i = int(np.argmin(np.hypot(VM.RIV_XY[:, 0] - wx, VM.RIV_XY[:, 1] - wy)))
    i = max(1, min(len(VM.RIV_XY) - 2, i))
    tg = VM.RIV_XY[i + 1] - VM.RIV_XY[i - 1]
    tg = tg / np.linalg.norm(tg)
    nr = np.array([-tg[1], tg[0]])
    t = float(VM.RIV_T[i])
    return (np.array([VM.RIV_XY[i, 0] - VM.CX, VM.RIV_XY[i, 1] - VM.CY]), tg, nr,
            float(VM.water_level(np.array([t]))[0]),
            float(VM.water_halfwidth(np.array([t]))[0]), t)


def build_dellhollow(col, F, zg, fr):
    """Dellhollow: stepped clusters down the BENCH-SIDE gorge wall, weirs, wheels, gate.

    ONE BANK.  This used to build two terraced strings facing each other across the
    notch, citing world.json for "the town straddles the river in its gorge" — and
    world.json has not said that since the 2026-08-01 restamp, which reads: "the
    town's mass is on the WEST bank — the LEFT bank looking downstream, the road's own
    side, unbroken from Emberbrook".  Half of this impression was standing on the FAR
    wall: the cliff the player provably cannot cross, which the same restamp made ch3
    territory.  The side is taken from valley_map's RESOLVED bench (from
    elevation.canyon.benchSide, cross-checked against the road) and never named here,
    so the town cannot be put on the wrong bank the way the canyon once was.
    """
    rng = random.Random(20260731)
    p = B.Prop("dellhollow")
    ht = tint_layer(p)
    aw = VM.DELLHOLLOW
    ctr, tg, nr, wl, hw, t = gorge_frame(F, aw[0], aw[1])
    rot = math.radians(float(VM.ANCHORS["dellhollow"]["rotationDeg"]))
    base_ang = math.atan2(float(tg[1]), float(tg[0]))
    n_house = 0
    # `nr` is the gorge frame's LEFT normal, so +1 is the left bank looking downstream.
    bench_side = 1 if VM.BENCH_LEFT else -1
    anchor_arc = VM.river_arc_at(aw[0], aw[1])
    # 4 tiers on one bank, not 3 on two: the town keeps its mass and its stepped read
    # without borrowing the cliff opposite. STATS carries the count so the change is
    # visible in valley_build.json rather than only in a render.
    for side in (bench_side,):
        for tier in range(4):
            lat = hw + 2.4 + tier * 4.4
            for stat in (-13.0, -7.0, -1.0, 5.0, 11.0):
                jx = rng.uniform(-1.1, 1.1)
                # STEP ALONG THE RIVER'S OWN CURVE, and take the normal there.
                # Restricting `side` to the bench was not enough: this cluster spans
                # 24u of a reach that turns from bearing 13 to 49 degrees, so lateral
                # offsets taken in the ANCHOR's frame walked across the water — 34% of
                # the impression's vertices were still on the far wall, measured by
                # vertex.  A per-station bank guard refused those, and correctly, but
                # it cost the town half its houses.  On the curve, nothing is refused.
                cpt, ctg, cnr, cwl, chw, _ = VM.river_frame_at_arc(anchor_arc + stat + jx)
                q = cpt + cnr * side * lat
                px, py = float(q[0] - VM.CX), float(q[1] - VM.CY)
                gz = gh(F, zg, fr, px, py)
                if gz < cwl + 0.35:                 # that station is in the water
                    continue
                off, hw_here = VM.bank_offset(float(q[0]), float(q[1]))
                if off * side < hw_here + 1.5:      # kept as a SCREEN, not the method
                    continue
                # The terrace ALIGNS to the bench — a stepped town does not scatter its
                # yaw — so the copy-read is broken here on size and tint, plus a small
                # yaw wobble a mason would allow. See the note above build_emberbrook.
                yaw = (math.atan2(float(ctg[1]), float(ctg[0])) + rot
                       + (0.0 if side > 0 else math.pi) + rng.uniform(-0.16, 0.16))
                dims = house_dims(rng)
                w, d = dims[1], dims[2]
                # A terrace pad + retaining wall is what makes a cluster read
                # STEPPED — but a pad placed at the CENTRE height cantilevers off a
                # gorge wall, which is what the first render showed.  The pad top is
                # the lowest of its own four corners, and the wall reaches from there
                # down to the ground beneath its outer edge.
                pw_, pd_ = w * 1.24, d * 1.24
                ca, sa = math.cos(yaw), math.sin(yaw)
                cor = [(px + ca * u * pw_ / 2 - sa * v * pd_ / 2,
                        py + sa * u * pw_ / 2 + ca * v * pd_ / 2)
                       for u in (-1, 1) for v in (-1, 1)]
                ch = [gh(F, zg, fr, a_, b_) for a_, b_ in cor]
                # the v2 canyon steepened both walls: where the pad's own corners
                # span more than ~2.8u of height, no terrace can read as bedded —
                # the house "stands proud" of the wall (foliage agent's gorge-shot
                # flag).  Skip that station; the cluster keeps its rhythm on the
                # stations that CAN bed.
                if max(ch) - min(ch) > 2.8:
                    continue
                pad = min(ch) + 0.10
                p.cube(STONE, (px, py, pad - 0.20), (pw_, pd_, 0.44), rz=yaw)
                foot = min(ch) - 0.4
                ox = px - nr[0] * side * pd_ * 0.52
                oy = py - nr[1] * side * pd_ * 0.52
                foot = min(foot, gh(F, zg, fr, ox - nr[0] * side * 1.6,
                                    oy - nr[1] * side * 1.6))
                drop = max(0.6, min(5.0, pad - foot))
                p.cube(STONE, (ox, oy, pad - 0.42 - drop / 2), (pw_, 0.38, drop), rz=yaw)
                fam = 1 + (n_house * 5 + n_house // 3) % 3
                # the pad IS this house's ground: four equal corners, so the footing
                # is the shallow contact band and not a second retaining wall.
                impression_house(p, ht, fam, px, py, yaw, dims, [pad] * 4, rng)
                n_house += 1
    # ---- THE WEIR FLIGHT: the reason the locks exist ------------------------
    n_weir = 0
    crest = None
    for k, stat in enumerate((-11.0, -1.0, 9.0)):
        cx_ = float(ctr[0] + tg[0] * stat)
        cy_ = float(ctr[1] + tg[1] * stat)
        _, wtg, wnr, wwl, whw, _ = gorge_frame(F, cx_ + VM.CX, cy_ + VM.CY)
        ang = math.atan2(float(wtg[1]), float(wtg[0])) + math.pi / 2
        span = whw * 2.0 + 1.4
        # SEGMENTED: one 2 x 15 x 3.4u block beside the houses reads as a monolith,
        # and the moorage camera stood right behind it.  Six courses with hashed
        # offsets read as built masonry at the same cost.
        nb = 6
        for bi in range(nb):
            u = (bi - (nb - 1) / 2.0) * (span / nb)
            hj = float(O3._hash01(bi, k * 17, 3))
            p.cube(STONE, (cx_ + float(wnr[0]) * u, cy_ + float(wnr[1]) * u,
                           wwl - 1.0 - 0.10 * hj),
                   (1.5 + 0.22 * hj, span / nb * 0.97, 2.9), rz=ang)
        p.cube(STONE, (cx_, cy_, wwl + 0.62), (2.1, span, 0.36), rz=ang)   # crest walk
        # a visible weir LINE downstream of the sill: white water reads as a drop
        p.cube(STONE, (cx_ - float(wtg[0]) * 1.6, cy_ - float(wtg[1]) * 1.6,
                       wwl - 0.28), (0.9, span * 0.88, 0.5), rz=ang)
        if crest is None:
            crest = (cx_, cy_, wwl + 0.90, ang, span)
        # ---- waterwheel HINTS on the abutment (2 of the 3 stations) ----------
        if k != 1:
            for side in (-1, 1):
                wx_ = cx_ + float(wnr[0]) * side * (whw + 1.4)
                wy_ = cy_ + float(wnr[1]) * side * (whw + 1.4)
                for j in range(9):
                    a = j * (2 * math.pi / 9)
                    p.cube(WOOD, (wx_ + math.cos(a) * 1.15 * float(wtg[0]),
                                  wy_ + math.cos(a) * 1.15 * float(wtg[1]),
                                  wwl + 0.15 + math.sin(a) * 1.15),
                           (0.40, 0.14, 0.40), rz=ang, rx=a)
                p.cone(WOOD, (wx_, wy_, wwl + 0.15), 1.22, 1.22, 0.20, seg=12, rz=ang)
                p.cone(METAL, (wx_, wy_, wwl + 0.15), 0.16, 0.16, 1.2, seg=8, rz=ang)
                # the mill it drives — BENCH SIDE ONLY.  A weir has two abutments and
                # both may carry a wheel; a MILL is a building, and a building on the
                # far wall is town mass on the cliff the player cannot reach.
                if side != bench_side:
                    n_weir += 1
                    continue
                mx = wx_ + float(wnr[0]) * side * 2.4
                my = wy_ + float(wnr[1]) * side * 2.4
                mz = gh(F, zg, fr, mx, my)
                # the mill grew with the cottages (2026-08-04): a working building that
                # is SHORTER than the houses around it stops reading as a mill.
                p.cube(WALL, (mx, my, max(mz, wwl) + 1.35), (2.0, 1.8, 2.70), rz=ang)
                p.cube(WOOD, (mx, my, max(mz, wwl) + 2.76), (2.6, 2.2, 0.14), rz=ang)
                p.prism(ROOF, (mx, my, max(mz, wwl) + 2.83), 2.5, 2.1, 1.35, rz=ang)
                n_weir += 1
    STATS["dellhollow_houses"] = n_house
    STATS["dellhollow_wheels"] = n_weir
    return p.finish(col), crest


def build_dam_crest(col, F, zg, fr, crest):
    """The dam crest — by the region's own ruling the ONLY span of this river."""
    if crest is None:
        return None
    cx_, cy_, z, ang, span = crest
    p = B.Prop("walk_dam_crest")
    dx, dy = math.cos(ang), math.sin(ang)
    n = 9
    ts = np.linspace(-span / 2, span / 2, n)
    xs = cx_ + dx * ts
    ys = cy_ + dy * ts
    _ribbon(p, STONE, np.column_stack([xs, ys]), np.full(n, z + 0.05), 1.05)
    return p.finish(col)


# The FOREST lives in tools/valley_veg.py now (VV.build_canopy).  Three iterations
# of it stood here — a billowed blanket, packed crown domes, and a painted canopy
# texture over a gentle swell — and the user called all three flakes, because all
# three were different GEOMETRY over the same ellipse-stamp texture.  The fourth is
# bush construction on a rendered leaf-cluster atlas; findings section E.  The stand
# masks, the wide road corridor and the clearing carves moved over verbatim.


def build_portals(col, F, zg, fr):
    """A visible marker at each portal: a town gate, and a gate-arch impression.

    The Valley Gate marker stands at the road's BUILT endpoint, not at the region's
    authored [215, 65] — the clearance pass shows that coordinate standing in the
    channel.  Reported as a map-change request.
    """
    p = B.Prop("portal_markers")
    # ---- emberbrook-gate: a timber town gate across the road ----------------
    # the station ~11u out from the town centre: the first render put the gate frame
    # straddling two houses because station 4 is only 4u from the green
    vx, vy = L.VILLAGE
    dv = np.hypot(F.road[:, 0] - vx, F.road[:, 1] - vy)
    i = int(np.argmin(np.abs(dv - 11.0)))
    i = max(2, min(len(F.road) - 3, i))
    rx, ry, rz = float(F.road[i, 0]), float(F.road[i, 1]), float(F.road_h[i])
    tgv = F.road[i + 1] - F.road[i - 1]
    tgv = tgv / np.linalg.norm(tgv)
    ang = math.atan2(float(tgv[1]), float(tgv[0]))
    for side in (-1, 1):
        gx = rx - float(tgv[1]) * side * 1.75
        gy = ry + float(tgv[0]) * side * 1.75
        gz = gh(F, zg, fr, gx, gy)
        p.cube(WOOD, (gx, gy, gz + 1.35), (0.30, 0.30, 2.70), rz=ang)
        p.cube(EMIT, (gx, gy, gz + 2.55), (0.18, 0.18, 0.22), rz=ang)
    p.cube(WOOD, (rx, ry, rz + 2.62), (0.26, 4.0, 0.34), rz=ang)
    p.prism(ROOF, (rx, ry, rz + 2.80), 0.9, 4.3, 0.42, rz=ang + math.pi / 2)
    # ---- dellhollow-valley-gate: a stone gate arch on the gorge rim ---------
    ex, ey = float(F.road[-1, 0]), float(F.road[-1, 1])
    ez = float(F.road_h[-1])
    tge = F.road[-1] - F.road[-4]
    tge = tge / np.linalg.norm(tge)
    ang2 = math.atan2(float(tge[1]), float(tge[0]))
    for side in (-1, 1):
        gx = ex - float(tge[1]) * side * 2.05
        gy = ey + float(tge[0]) * side * 2.05
        gz = gh(F, zg, fr, gx, gy)
        p.cube(STONE, (gx, gy, gz + 1.85), (1.05, 1.05, 3.70), rz=ang2)
        p.cube(STONE, (gx, gy, gz + 3.85), (1.25, 1.25, 0.42), rz=ang2)
        # the curtain either side: the NOTCH in the rim the gate sits in
        for k in (1, 2, 3):
            wx_ = gx - float(tge[1]) * side * k * 1.35
            wy_ = gy + float(tge[0]) * side * k * 1.35
            wz = gh(F, zg, fr, wx_, wy_)
            p.cube(STONE, (wx_, wy_, wz + 1.15 - 0.15 * k), (1.4, 1.0, 2.4 - 0.3 * k),
                   rz=ang2)
    p.cube(STONE, (ex, ey, ez + 3.55), (0.62, 4.6, 0.62), rz=ang2)
    for side in (-1, 1):
        p.cube(EMIT, (ex - float(tge[1]) * side * 1.5, ey + float(tge[0]) * side * 1.5,
                      ez + 3.05), (0.18, 0.18, 0.22), rz=ang2)
    return p.finish(col)


def build_old_gate(col, F, zg, fr):
    """THE OLD GATE — ONE WALL ACROSS THE PINCH, built from the ratios that seated it.

    Canon (docs/qa/emberbrook/concepts/gate-final.png, and stamp 188a329): a single
    structure spanning the whole notch — plain coursed masonry, the ROAD's doorway
    ARCHED because arches are for humans, and the water passage a LOW GRATE AT WATER
    LEVEL with no arch over it.  The tile used to build nothing here at all: the Old
    Gate has target null, so build_portals skipped it and the region's one bottleneck
    was two survey posts.

    Every dimension is the town's own, carried as a multiple of the CHANNEL's
    half-width — the pinch-ratio rule, which is also how the seat was derived:
        curtain 1.583 | doorway 1.410 | founded 1.022 | grate 2.000  (half-widths)
    and the wall takes a bite into the living rock at both ends, because "built
    wall-to-wall into living rock" is what makes it a seal rather than a fence, and
    because a flush joint is the knife edge that made 2b's rectangle test lie twice.
    """
    p = B.Prop("oldgate")
    gw = VM.PORTALS["old-gate"]["at"]
    i = int(np.argmin(np.hypot(VM.RIV_XY[:, 0] - gw[0], VM.RIV_XY[:, 1] - gw[1])))
    tg = VM.RIV_XY[min(i + 1, len(VM.RIV_XY) - 1)] - VM.RIV_XY[max(i - 1, 0)]
    tg = tg / np.linalg.norm(tg)
    nl = np.array([-tg[1], tg[0]])                       # +nl = LEFT bank = west
    t = float(VM.RIV_T[i])
    wl = float(VM.water_level(np.array([t]))[0])
    hw = float(VM.water_halfwidth(np.array([t]))[0])
    ctr = VM.RIV_XY[i]
    # THE PROP'S LOCAL FRAME, AND IT WAS 90 DEGREES OUT FOR THE WHOLE OF THIS GATE'S
    # LIFE (measured 2026-08-03, tools/glb_read.mjs on the shipped bundle).  Every
    # cube here is sized (ALONG THE RIVER, ACROSS THE NOTCH, height) — `wall()` passes
    # (thick, ow, ...), the grate bars (0.9, 0.13, ...), the deck ((b1-b0), span, ...).
    # Blender's Matrix.Rotation(rz, 'Z') sends local X to (cos rz, sin rz), so rz must
    # be the RIVER's angle for size[0] to lie along the river.  It was `nl`'s, which is
    # the angle ACROSS the notch, and every box came out rotated a quarter turn: the
    # four wall runs stood as piers ALONG the gorge instead of one wall across it (the
    # coping boxes measured 1.86-1.90 m of x against 2.2-7.7 m of z, on a notch that
    # runs along x), and the nine deck bays stacked into a single 0.42 m strip pointing
    # downstream — which is the SIX-CELL "raft" docs/qa/oldgate/index.html measured and
    # read as a height problem.  The comment on this line was right about the intent
    # ("the wall runs ACROSS the water") and the code did the opposite.
    #
    # THE BUILDER'S OWN SEAL COULD NOT SEE IT: the flood fill below blocks the wall's
    # INTENDED footprint analytically (`abs(bb) < 0.7 and ...`), so it scored the design,
    # not the build, and printed 0 leaks over a gate made of four detached piers.
    ang = math.atan2(float(tg[1]), float(tg[0]))         # the wall runs ACROSS the water

    def at(off, bx=0.0):
        """world point `off` half-widths west of the centreline, `bx` u downstream."""
        q = ctr + nl * off + tg * bx
        return float(q[0] - VM.CX), float(q[1] - VM.CY)

    CURT, DOOR, FOUND, GRATE = 1.583 * hw, 1.410 * hw, 1.022 * hw, 2.000 * hw
    e_rock = -hw                                          # the channel's east edge
    door_c = hw + FOUND + DOOR / 2.0                      # = 2.778 half-widths, proven
    w_rock = door_c + DOOR / 2.0 + CURT
    top = float(gw[2]) + 3.5                              # coursed masonry above
    ROCK = float(gw[2]) + 2.6            # above this a walker is climbing, not walking

    # ---- THE BITES ARE MEASURED, NOT TYPED ---------------------------------
    # "Built wall-to-wall into living rock" is a claim about where the rock IS, and
    # the rock moved: the chirality flip made the EAST side the traversable bench, so
    # the 2.4u bite that used to land in the far wall's own cliff left 2.25u of open
    # ground for a walker to slip round (131 leaked cells, measured).  Each end now
    # WALKS OUT until the ground is rock and then bites 0.9u into it, and the numbers
    # it found are printed with the seal.
    def _to_rock(o0, d, cap=16.0):
        s_, o = 0.0, o0
        while s_ < cap:
            x_, y_ = at(o)
            if gh(F, zg, fr, x_, y_) >= ROCK:
                return s_
            s_ += 0.05
            o += d * 0.05
        return cap

    BITE = _to_rock(w_rock, +1.0) + 0.9                   # west end, into the rock
    EBITE = _to_rock(-hw, -1.0) + 0.9                     # east end, into the rock
    STATS["oldgate_notch_u"] = round((w_rock + BITE) - (-hw - EBITE), 2)
    STATS["oldgate_pinch_u"] = round(w_rock - e_rock, 2)
    STATS["oldgate_door_halfwidths"] = round(door_c / hw, 3)
    STATS["oldgate_bite_w_u"] = round(BITE, 2)
    STATS["oldgate_bite_e_u"] = round(EBITE, 2)

    def wall(o0, o1, z0, z1, thick=1.5):
        """A run of masonry between two offsets, z0 (base) to z1 (top).

        ONE WALL, NOT A STACK (docs/qa/oldgate/index.html, 2026-08-03).  This used
        to lay one cube per 0.55u course with a +-0.06u jog, meant to read as
        coursing.  At the overworld boom (dist 40) it reads as a FLIGHT OF SHELVES,
        and the courses are individually standable — the arrival's own frame showed
        the player on top of the gatewall, and a wall you can stand on is not a
        seal.  Three boxes instead of six or seven: a plinth proud at the base, the
        shaft, and a coping proud at the top, which is what gives masonry its
        silhouette at distance.  It is also 276 triangles CHEAPER.
        """
        oc, ow = (o0 + o1) / 2.0, abs(o1 - o0)
        if ow < 0.05:
            return
        x_, y_ = at(oc)
        h = z1 - z0
        plin = min(0.55, h * 0.16)
        cope = min(0.45, h * 0.13)
        p.cube(STONE, (x_, y_, z0 + plin / 2.0), (thick + 0.30, ow, plin), rz=ang)
        p.cube(STONE, (x_, y_, (z0 + plin + z1 - cope) / 2.0),
               (thick, ow, max(0.05, h - plin - cope)), rz=ang)
        p.cube(STONE, (x_, y_, z1 - cope / 2.0), (thick + 0.34, ow + 0.10, cope), rz=ang)

    # 1. the WEST CURTAIN, from the doorway's jamb into the living rock
    wall(door_c + DOOR / 2.0, w_rock + BITE, wl, top)
    # 2. the ROAD'S DOORWAY — arched, and the only human-sized opening in the world
    jamb = float(gw[2]) + 1.9                              # springing line of the arch
    wall(door_c - DOOR / 2.0, door_c + DOOR / 2.0, jamb + 1.15, top)      # over the arch
    for k in range(9):                                     # the arch ring itself
        a = math.pi * (k + 0.5) / 9.0
        ox = door_c + math.cos(a) * DOOR / 2.0
        oz = jamb + math.sin(a) * (DOOR / 2.0) * 0.62
        x_, y_ = at(ox)
        p.cube(STONE, (x_, y_, oz), (1.62, DOOR / 9.0 * 1.25, 0.42), rz=ang, rx=a)
    # 3. the FOUNDED EAST WALL — the dry ground between the doorway and the water
    wall(hw, door_c - DOOR / 2.0, wl, top)
    # 4. the WATER PASSAGE: a LOW GRATE AT WATER LEVEL, no arch (stamp 188a329),
    #    with the wall carried on OVER it in one unbroken run of masonry.
    grate_top = wl + 1.15
    wall(-hw - EBITE, hw, grate_top, top)                  # the wall over the water
    nb = 11
    for k in range(nb):                                    # the bars, standing IN the water
        o = -hw + (k + 0.5) * (GRATE / nb)
        x_, y_ = at(o)
        p.cube(METAL, (x_, y_, (wl - 0.6 + grate_top) / 2.0),
               (0.9, 0.13, grate_top - wl + 0.6), rz=ang)
    x_, y_ = at(0.0)
    p.cube(STONE, (x_, y_, grate_top + 0.16), (1.75, GRATE + 0.4, 0.32), rz=ang)  # the sill lintel
    # 5. a lamp either side of the doorway — the Order keeps it lit
    for s_ in (-1, 1):
        x_, y_ = at(door_c + s_ * (DOOR / 2.0 + 0.35))
        p.cube(EMIT, (x_, y_, jamb + 0.15), (0.22, 0.22, 0.26), rz=ang)

    # ---- 6. THE CULVERT COURT (user's flavour 1, ratified 2026-08-01) -------
    # The river ALREADY passes under this wall through the low grate.  The court is
    # that grate extended: the water runs on under stone for road.culvert.lengthU and
    # comes back to daylight at the SILL, where it falls.  The ROAD crosses on the
    # paving — through the doorway, over the court, out on the east bank — so the
    # region's one bank change is made of masonry and water, not of a span.  There is
    # no bridge here and none anywhere; crossings.list is still empty.
    #
    # The court length is the PINCH RATIO of the town's own gate court (8.0 m against
    # a 6.95 m grate = 1.151 grate-widths), capped so the deck never overhangs the
    # falls' lip.  Both numbers are in road.culvert's note; the build re-derives the
    # cap from the map rather than trusting it.
    culv = VM.REGION["road"].get("culvert")
    court_from = court_to = None
    if culv is not None:
        clen = float(culv["lengthU"])
        face = VM.WALL_THICK_U / 2.0 if hasattr(VM, "WALL_THICK_U") else 0.75
        court_from, court_to = face, face + clen - 0.40   # 0.40 short of the lip
        deck_z = float(gw[2]) - 0.10                      # the court's nominal level
        w_lim, e_lim = w_rock + BITE, -hw - EBITE
        # ---- THE DECK FOLLOWS THE ROAD IT CARRIES ---------------------------
        # A COURT LAID AT ONE LEVEL IS A TABLE BESIDE THE ROAD, NOT A PIECE OF IT.
        # The road descends across this notch — measured off VM.ROAD_Z, 26.44 at the
        # doorway (off +6.7) to 25.62 where it leaves the court's downstream edge
        # (off -4.86) and 25.34 one station further — while a flat deck stands at
        # 26.40 the whole way.  walkStep's step-UP is 0.63 m, so a 0.78 m lip at the
        # east end is a wall the player can fall off and never climb back onto: the
        # Old Gate as a ONE-WAY DOOR, exactly as docs/qa/oldgate/index.html §5 read it.
        # So the paving takes its height from THE ROAD'S OWN Z at that offset, read
        # off the map's stations inside the court band.  No ramp object, no apron
        # (one was tried and made the island smaller): the deck and the road are the
        # same surface because they are derived from the same numbers.
        _r = VM.ROAD_XY - ctr
        _off = _r @ nl
        _bxr = _r @ tg
        _band = [k for k in range(len(_bxr)) if court_from - 2.5 <= _bxr[k] <= court_to + 2.5]
        _ro = np.array([_off[k] for k in _band], float)
        _rz = np.array([float(VM.ROAD_Z[k]) for k in _band], float)
        _sort = np.argsort(_ro)
        _ro, _rz = _ro[_sort], _rz[_sort]

        def deck_at(o):
            """The paving's top at offset `o` — the road's own z, 30 mm under it.

            np.interp CLAMPS outside the sampled band, so the court's buried west
            shoulder keeps the doorway's level instead of extrapolating off a cliff.
            """
            return float(np.interp(float(o), _ro, _rz)) - 0.03
        # THE DECK IS AS WIDE AS THE HOLLOW IT HAS TO COVER, AND THE HOLLOW IS
        # MEASURED.  A slab run rock-to-rock at one level is half buried and half
        # floating — which is exactly what the first render of this court showed,
        # a row of stone shelves jutting out of a cliff.  Walk out from the channel
        # each way along the court's own middle and stop where the ground comes up
        # to the paving; that is where a court would stop being built.
        def _deck_end(d, cap):
            o = 0.0
            while abs(o) < abs(cap):
                x_, y_ = at(o, (court_from + court_to) / 2.0)
                if gh(F, zg, fr, x_, y_) >= deck_at(o) - 0.12 and abs(o) > hw + 0.6:
                    break
                o += d * 0.1
            return o
        w_end = min(_deck_end(+1.0, w_lim), w_lim)
        e_end = max(_deck_end(-1.0, e_lim), e_lim)
        # the DECK: coursed paving over the hollow, laid on the culvert.
        # THE COURSES RUN ACROSS THE ROAD, one per step of offset, because that is
        # what lets each course sit at its own height: nine bays laid the other way
        # could only ever be one flat table.  Twelve courses over a 12 m notch put
        # ~0.075 m between neighbours against a 0.63 m step-up — a slope to walk, a
        # coursing line to look at.  They overlap 2% so the paving has no crack for
        # a floor ray to fall through.
        ncr = 12
        deck_lo = deck_hi = None
        for k in range(ncr):
            o0 = e_end + (w_end - e_end) * k / ncr
            o1 = e_end + (w_end - e_end) * (k + 1) / ncr
            zc = deck_at((o0 + o1) / 2.0)
            deck_lo = zc if deck_lo is None else min(deck_lo, zc)
            deck_hi = zc if deck_hi is None else max(deck_hi, zc)
            x_, y_ = at((o0 + o1) / 2.0, (court_from + court_to) / 2.0)
            p.cube(STONE, (x_, y_, zc - 0.22),
                   (court_to - court_from, (o1 - o0) * 1.02, 0.44), rz=ang)
        # the CULVERT BARREL under it: two side walls in the channel carrying the deck,
        # so the paving is held up by something and the water has a barrel to run in
        for s_ in (-1.0, 1.0):
            zb = deck_at(s_ * (hw + 0.45))
            x_, y_ = at(s_ * (hw + 0.45), (court_from + court_to) / 2.0)
            p.cube(STONE, (x_, y_, (wl - 1.6 + zb) / 2.0),
                   (court_to - court_from, 0.9, zb - wl + 1.6), rz=ang)
        # the DOWNSTREAM MOUTH: a plain arched head, and the water leaves it at the sill
        for k in range(7):
            a_ = math.pi * (k + 0.5) / 7.0
            ox = math.cos(a_) * (hw + 0.45)
            oz = wl + 0.55 + math.sin(a_) * 1.15
            x_, y_ = at(ox, court_to)
            p.cube(STONE, (x_, y_, oz), (0.55, (hw + 0.45) * 2 / 7 * 1.3, 0.42),
                   rz=ang, rx=a_ + math.pi / 2)
        # a low parapet along the court's downstream edge — the drop is right there.
        # IT IS GAPPED WHERE THE ROAD CROSSES THIS EDGE, MEASURED — not where the
        # doorway happens to be.  The gap used to be cut at `door_c`, the ARCHED
        # DOORWAY's offset, which is on the WEST bank.  The road comes through the
        # doorway, crosses the court and leaves on the EAST bank, so the parapet
        # stood across its own exit: measured in the running game, a 4.4u band of
        # body-blocked cells at world x -44.9 to -40.9.  The road's own offset at
        # this edge is read off VM.ROAD_XY, so it follows the road if the map moves
        # it.  (This alone did NOT open the court: the court was shut by the prop's
        # 90-degree frame error and by the flat deck, both fixed above.)
        _j = int(np.argmin(np.abs(_bxr - court_to)))
        road_o = float(_off[_j])
        GAPW = max(DOOR * 0.75, VM.ROAD_WIDTH * 0.5 + 1.2)
        for s_ in (0,):
            for k in range(11):
                o = e_end + (w_end - e_end) * (k + 0.5) / 11
                if abs(o - door_c) < DOOR * 0.75:          # the doorway's own opening
                    continue
                if abs(o - road_o) < GAPW:                 # and the road's
                    continue
                x_, y_ = at(o, court_to)
                p.cube(STONE, (x_, y_, deck_at(o) + 0.36),
                       (0.42, (w_end - e_end) / 11 * 0.96, 0.72), rz=ang)
        # ---- THE THREE MARKS THE CONCEPT IDENTIFIES THIS GATE BY ---------------
        # docs/qa/emberbrook/concepts/gate-final.png is RATIFIED art and the built
        # gate carried none of its identity: no leaf in the arch, no sigil over it,
        # no plates in the paving.  Chapter One's climax is TWO KEEPERS ON TWIN
        # SIGIL PLATES opening this gate, so the plates are the climax's SET — from
        # the valley side there was nothing here a player could recognise as the
        # thing they had just opened.  All three are FLAT — a leaf, a disc, two
        # plates — and together they cost less than the coursing above gave back.
        # 1. THE LEAF, SWUNG OPEN.  It opened in Chapter One and it stays open: two
        #    dark timber leaves laid back against the doorway's own reveals, which
        #    is also why they cannot be walked into.
        #    THE OPENING BETWEEN THEM IS NEVER NARROWER THAN THE ROAD.  Laid back
        #    at DOOR*0.44 wide and 0.22 inside the jamb (the first cut), the two
        #    leaves left 1.34u clear against a 2.0u road, and every mesh in
        #    ow-valley that is not water_/lm_/veg_ BLOCKS — so the door dressing
        #    would have been a second, smaller pinch inside the doorway.
        LEAF_W = DOOR * 0.30
        for s_ in (-1.0, 1.0):
            ox = door_c + s_ * (DOOR / 2.0 - 0.10)
            x_, y_ = at(ox, 0.62)
            p.cube(WOOD, (x_, y_, wl + (jamb + 1.15 - wl) / 2.0),
                   (0.34, LEAF_W, jamb + 1.15 - wl), rz=ang)
        STATS["oldgate_door_clear_u"] = round(DOOR - 2 * (0.10 + LEAF_W / 2.0), 2)
        # 2. THE SIGIL ROUNDEL, over the arch, on the court-side face.
        x_, y_ = at(door_c, 0.80)
        p.cone(EMIT, (x_, y_, jamb + 1.62), DOOR * 0.27, DOOR * 0.27, 0.16, seg=14, rz=ang)
        x_, y_ = at(door_c, 0.86)
        p.cone(STONE, (x_, y_, jamb + 1.62), DOOR * 0.34, DOOR * 0.34, 0.22, seg=14, rz=ang)
        # 3. THE TWIN PLATES, set in the court paving, one either side of the road —
        #    the two keepers stood on these.
        #    PERPENDICULAR TO THE ROAD'S OWN DIRECTION, AND CLAMPED TO THE DECK.
        #    "Either side of the road" was first written as road_o +- half a road
        #    width along `nl`, and rendered wrong for a measured reason: the road
        #    does not run along this court, it CROSSES it — off runs +6.5 to -4.9
        #    over 4u of bx — so an nl offset walks along the road, not across it,
        #    and the east plate landed 1.7u past e_end, hanging over the drop
        #    (seen in docs/qa/oldgate/ship-after-court.png, first cut).  Take the
        #    road's own local tangent at the middle station inside the court, step
        #    across THAT, and clamp both plates inside the paving.
        _in = [k for k in range(len(_bxr))
               if court_from <= _bxr[k] <= court_to and e_end <= _off[k] <= w_end]
        if _in:
            _m = _in[len(_in) // 2]
            _a, _b = _in[max(0, len(_in) // 2 - 1)], _in[min(len(_in) - 1, len(_in) // 2 + 1)]
            _d = np.array([_bxr[_b] - _bxr[_a], _off[_b] - _off[_a]])
            _n = float(np.linalg.norm(_d))
            _d = _d / _n if _n > 1e-6 else np.array([0.0, -1.0])
            _perp = np.array([-_d[1], _d[0]])
            for s_ in (-1.0, 1.0):
                q = np.array([_bxr[_m], _off[_m]]) + _perp * s_ * (VM.ROAD_WIDTH * 0.5 + 0.55)
                bxp = min(max(float(q[0]), court_from + 0.5), court_to - 0.5)
                ofp = min(max(float(q[1]), e_end + 0.7), w_end - 0.7)
                x_, y_ = at(ofp, bxp)
                # a STONE plate with an EMIT sigil inset, NOT an emissive disc: at
                # 0.62u across, plain EMIT reads as spilled yellow paint at every
                # boom this scene is ever seen from (measured by eye, same frame).
                # low segment counts on purpose: a 1.24u disc read from a 20u boom
                # cannot show the difference, and the whole redesign is held to
                # costing LESS than what it replaces.
                p.cone(STONE, (x_, y_, deck_at(ofp) + 0.02), 0.62, 0.62, 0.10, seg=10, rz=ang)
                p.cone(EMIT, (x_, y_, deck_at(ofp) + 0.07), 0.30, 0.30, 0.05, seg=8, rz=ang)
            STATS["oldgate_plates_at"] = [round(float(_bxr[_m]), 2), round(float(_off[_m]), 2)]
        STATS["oldgate_parapet_road_off"] = round(road_o, 2)
        STATS["oldgate_court_len_u"] = round(court_to - court_from, 2)
        STATS["oldgate_court_span_u"] = round(w_end - e_end, 2)
        STATS["oldgate_court_ends"] = [round(e_end, 2), round(w_end, 2)]
        STATS["oldgate_culvert_covered_u"] = round(court_to + 0.75, 2)
        # THE GRADE, RECORDED EVERY BUILD.  These three numbers are what make the
        # gate a two-way door: the paving's fall across the notch, the biggest
        # riser between neighbouring courses, and how far the deck's two ENDS sit
        # from the road they meet.  A riser over walkStep's 0.63 m step-up, or an
        # end more than 0.63 m above its road, is the one-way door coming back.
        STATS["oldgate_deck_fall_u"] = round(deck_hi - deck_lo, 3)
        STATS["oldgate_deck_riser_u"] = round((deck_hi - deck_lo) / max(1, ncr - 1), 3)
        STATS["oldgate_deck_ends_z"] = [round(deck_at(e_end), 2), round(deck_at(w_end), 2)]
        STATS["oldgate_deck_end_vs_road_u"] = [
            round(deck_at(e_end) - (float(np.interp(e_end - 0.9, _ro, _rz))), 2),
            round(deck_at(w_end) - (float(np.interp(w_end + 0.9, _ro, _rz))), 2)]

    # ---- THE SEAL, PRINTED EVERY BUILD -------------------------------------
    # ow-valley is FREE-ROAM terrain, not WALKLOCK: nothing stops a walker but the
    # ground itself, so the TERRAIN has to be the wall.  Mini-round 2b proved the
    # town's notch with exactly these numbers; this is the region-scale twin, and it
    # runs on every build instead of being measured once and believed forever.
    step = 0.05

    def strip(o0, d):
        s_, o = 0.0, o0
        while s_ < 14.0:
            x_, y_ = at(o)
            if gh(F, zg, fr, x_, y_) >= ROCK:
                break
            s_ += step
            o += d * step
        return s_

    strip_w = strip(w_rock + BITE, +1.0)          # masonry's west end -> living rock
    strip_e = strip(-hw - EBITE, -1.0)            # masonry's east end -> living rock
    # flood fill from the gate court: can any walkable cell reach PAST the pinch line?
    # WHAT COUNTS AS "PAST" IS THE WALL, NOT A LINE THROUGH IT.  The first version
    # counted any cell downstream of the pinch line in the RIVER's frame, and the
    # gatewall runs diagonally across that frame — so it scored cells that were still
    # on the highland side, riding the band's own inner edge, as escapes.  A probe that
    # over-reports is only marginally better than one that under-reports: both make you
    # chase the wrong geometry.  "Past" now means out beyond the gatewall's OUTER face,
    # which is the valley, which is the thing the gate exists to withhold.
    _gwb = [m for m in VM.WORLD["massifs"] if m["id"] == "gatewall"][0]["blob"]
    _a, _b = np.array(_gwb[3], float), np.array(_gwb[2], float)
    _d = _b - _a
    _dn = float(np.hypot(*_d))

    def beyond(px, py):
        return float((px - _a[0]) * _d[1] - (py - _a[1]) * _d[0]) / _dn * _sgn

    _ef = VM.LAND_W["ember-falls"]
    _sgn = 1.0
    _sgn = math.copysign(1.0, beyond(_ef[0], _ef[1]))   # calibrate on a known gorge point
    seen, frontier, past, cell, leak = set(), [(0.0, -6.0)], 0, 0.6, []
    while frontier:
        oo, bb = frontier.pop()
        key = (round(oo / cell), round(bb / cell))
        if key in seen or abs(oo) > 24.0 or abs(bb) > 24.0:
            continue
        seen.add(key)
        x_, y_ = at(door_c + oo, bb)
        h_ = gh(F, zg, fr, x_, y_)
        if h_ >= ROCK or h_ <= wl + 0.2:           # rock above it, water below it
            continue
        # THE WALL IS SOLID, AND SO IS ITS DOORWAY FOR THIS TEST.  The town's 2b probe
        # asked "is any gorge reachable" and wanted 0 because that gate is SEALED at
        # story start.  Here the road GOES THROUGH the doorway — it is the way to
        # Dellhollow — so a flood fill that walks through it measures nothing.  The
        # question worth asking at region scale is the other one: IS THERE A WAY ROUND?
        # So the wall's whole footprint blocks, doorway included, and anything that
        # still gets past did so over ground the gate does not cover.
        if abs(bb) < 0.7 and (-hw - EBITE) <= (door_c + oo) <= (w_rock + BITE):
            continue
        if beyond(x_ + VM.CX, y_ + VM.CY) > 1.0:   # OUT PAST THE GATEWALL'S OUTER FACE
            past += 1
            leak.append((door_c + oo, bb, h_))
        for d in ((cell, 0.0), (-cell, 0.0), (0.0, cell), (0.0, -cell)):
            frontier.append((oo + d[0], bb + d[1]))
    STATS["oldgate_strip_west_u"] = round(strip_w, 2)
    STATS["oldgate_strip_east_u"] = round(strip_e, 2)
    STATS["oldgate_floodfill_past_pinch"] = past
    print("OLD GATE SEAL:  notch %.2fu rock-to-rock (pinch %.2fu, bites W %.2f E %.2f) | "
          "doorway %.3f half-widths | founded %.2fu | strip masonry->rock  W %.2fu  E %.2fu "
          "| flood fill past the pinch %d cells"
          % ((w_rock + BITE) - (-hw - EBITE), w_rock - e_rock, BITE, EBITE,
             door_c / hw, FOUND, strip_w, strip_e, past))
    if court_from is not None:
        print("GATE COURT:  %.2fu of paving along the river x %.2fu across (offsets %+.2f to "
              "%+.2f of a %.2fu notch, MEASURED to where the ground comes up to the paving); "
              "the river is under stone from the grate to the sill, %.2fu; the road crosses on it"
              % (court_to - court_from, w_end - e_end, e_end, w_end,
                 w_rock + BITE + hw + EBITE, court_to + 0.75))
        print("   GRADED to the road: %d courses, %.2fu of fall, biggest riser %.3fu "
              "(step-up 0.63u); ends z %.2f east / %.2f west, %+.2fu / %+.2fu against "
              "the road just outside them"
              % (ncr, deck_hi - deck_lo, (deck_hi - deck_lo) / max(1, ncr - 1),
                 deck_at(e_end), deck_at(w_end),
                 STATS["oldgate_deck_end_vs_road_u"][0],
                 STATS["oldgate_deck_end_vs_road_u"][1]))
    if leak:
        offs = [l[0] for l in leak]
        bbs = [l[1] for l in leak]
        print("   LEAK: offsets %.2f..%.2f (wall spans %.2f..%.2f), bb %.2f..%.2f, "
              "ground %.2f..%.2f (rock threshold %.2f)"
              % (min(offs), max(offs), -hw - EBITE, w_rock + BITE, min(bbs), max(bbs),
                 min(l[2] for l in leak), max(l[2] for l in leak), ROCK))
    return p.finish(col)


def build_props(col, F, zg, fr):
    """The waystone at the treeline break, plus rock outcrops in the crag."""
    p = B.Prop("props_valley")
    # ---- the Whisperwood waystone (ch1 fiction) -----------------------------
    wx_, wy_ = VM.w2b(*VM.LAND_W["waystone"][:2])
    wx_, wy_ = float(wx_), float(wy_)
    # stand it just OFF the ribbon so the road stays clear
    d = F.road_frame_at(VM.LAND_W["waystone"][0], VM.LAND_W["waystone"][1])
    nx, ny = -d[3][1], d[3][0]
    wx_, wy_ = d[0] + nx * 2.2, d[1] + ny * 2.2
    gz = gh(F, zg, fr, wx_, wy_)
    ang = math.atan2(d[3][1], d[3][0])
    p.cube(STONE, (wx_, wy_, gz + 0.12), (1.5, 1.5, 0.30), rz=ang)
    p.cube(STONE, (wx_, wy_, gz + 1.02), (0.62, 0.34, 1.60), rz=ang + 0.12)
    p.cube(MARK, (wx_ + math.cos(ang + math.pi / 2) * 0.19,
                  wy_ + math.sin(ang + math.pi / 2) * 0.19, gz + 1.16),
           (0.34, 0.02, 0.46), rz=ang + 0.12)
    # ---- rock outcrops, biased into the crag zones -------------------------
    rng = random.Random(4242)
    n = 0
    tries = 0
    while n < 46 and tries < 40000:
        tries += 1
        bx = rng.uniform(-VM.TILE_W / 2 + 6, VM.TILE_W / 2 - 6)
        by = rng.uniform(-VM.TILE_H / 2 + 6, VM.TILE_H / 2 - 6)
        zt = zg.type_at_blender(bx, by)
        if zt != "crag":
            continue
        if float(F.road_dist(np.array([bx]), np.array([by]))[0]) < 3.0:
            continue
        # an outcrop on a near-vertical face hangs in the air (the first render had
        # boulders stuck to the plateau cliff like barnacles)
        if float(F.slope_at(np.array([bx]), np.array([by]))[0]) > 1.35:
            continue
        gz = gh(F, zg, fr, bx, by)
        s = rng.uniform(0.8, 2.4)
        before = set(p.bm.faces)
        # SUNK, and only where the ground is level enough to hold it: an outcrop set
        # on its own centre height hangs off a gorge wall like a barnacle
        ca = [gh(F, zg, fr, bx + dx_, by + dy_)
              for dx_, dy_ in ((-s, -s), (s, -s), (s, s), (-s, s))]
        if max(ca) - min(ca) > 1.7:
            continue
        p.ico(ROCK, (bx, by, min(ca) + s * 0.10), (s * 1.15, s * 0.86, s * 0.70),
              subd=1, rz=rng.uniform(0, 6.28))
        for f in p.bm.faces:
            if f not in before:
                for v in f.verts:
                    v.co += Vector((rng.uniform(-.13, .13), rng.uniform(-.13, .13),
                                    rng.uniform(-.10, .10))) * s
        n += 1
    STATS["outcrops"] = n
    return p.finish(col)


def build_moorage_spur(col, F, zg, fr, root):
    """A short bank path from the gorge floor out to the jetty root."""
    a = np.array([root[0], root[1]], float)
    ctr = fr["ctr"]
    tg = fr["tg"]
    b_ = a + tg * 9.0
    ts = np.linspace(0, 1, 14)
    pts = a[None, :] * (1 - ts[:, None]) + b_[None, :] * ts[:, None]
    # +0.16, not +0.09: the ribbon is linear between stations while the treated
    # ground varies, and the high-land rework steepened this descent — the same
    # sawtooth the road solves with its worn notch (verify caught 0.053u)
    z = ghv(F, zg, fr, pts[:, 0], pts[:, 1]) + 0.16
    p = B.Prop("walk_dockpath")
    _ribbon(p, DIRT, pts, z, 0.85)
    return p.finish(col)


# =============================================================================
# THE VISTA RING — generated from the PARENT's coarse data
# =============================================================================
def build_vista(col, F):
    """fx_ silhouette RANGES and the river continuing beyond the envelope.

    Read off world.json: each massif's crest sets the height of the range that
    carries on past the tile edge, and riverSpine's last point carries
    `continues: true`, so the water leaves the frame instead of stopping at it.

    Built as continuous ridge STRIPS, one per band per side.  The first pass used a
    cone per summit and every render came back with a picket fence of tents: a cone
    is a shape, and a mountain range is a CREST LINE.  A strip whose crest is hashed
    per station, with the bands overlapping in depth, is both cheaper and right.
    """
    p = B.Prop("fx_vista_ring")
    crest = {m["id"]: m.get("crest", 30.0) for m in VM.WORLD["massifs"]}
    HX, HY = VM.TILE_W / 2, VM.TILE_H / 2
    sides = (("northwall", 0, +1, HY, VM.TILE_W),
             ("southwall", 0, -1, HY, VM.TILE_W),
             ("westwall", 1, -1, HX, VM.TILE_H),
             ("northwall", 1, +1, HX, VM.TILE_H))          # east: over the escarpment
    # A LOW APRON first: without it the gap between the tile's cut edge and the
    # first range is a hole straight to the world background, and the vista shot
    # reads as a matte painting with the bottom torn off.
    for axis, sgn, edge, run in ((0, +1, HY, VM.TILE_W), (0, -1, HY, VM.TILE_H),
                                 (1, -1, HX, VM.TILE_H), (1, +1, HX, VM.TILE_H)):
        a0, a1 = edge - 2.0, edge + 640.0
        w = run / 2 + 660.0
        q = []
        for da in (a0, a1):
            for wu in (-w, w):
                q.append((wu, da * sgn) if axis == 0 else (da * sgn, wu))
        p.strip(ROCK, [(float(q[0][0]), float(q[0][1]), -11.0),
                       (float(q[1][0]), float(q[1][1]), -11.0)],
                [(float(q[2][0]), float(q[2][1]), -13.0),
                 (float(q[3][0]), float(q[3][1]), -13.0)])
    n = 0
    for si, (mid, axis, sgn, edge, run) in enumerate(sides):
        for band in range(3):
            dist = edge + 96.0 + band * 128.0
            top = crest[mid] * (1.15 + 0.55 * band)
            step = 26.0 + band * 14.0
            us = np.arange(-run / 2 - 260.0, run / 2 + 260.0 + step, step)
            crest_pts, near_pts, far_pts = [], [], []
            for k, u in enumerate(us):
                h1 = float(O3._hash01(int(k), band * 37 + si * 101, 5))
                h2 = float(O3._hash01(int(k) + 7, band * 53 + si * 211, 9))
                hgt = top * (0.55 + 0.50 * h1 * h1)
                # jitter the range's DEPTH as well as its height: overlapping crest
                # lines are what make three strips read as many ranges
                # depth jitter stays SMALL.  At +-2.2 steps the crest line zig-zagged
                # further in depth than it advanced along the range, and the "range"
                # became a self-overlapping mass that filled the whole vista frame.
                dd = dist + (h2 - 0.5) * step * 0.45
                foot = step * 0.85
                for lst, off, z in ((crest_pts, 0.0, -10.0 + hgt),
                                    (near_pts, -foot, -10.0), (far_pts, foot, -10.0)):
                    d2_ = (dd + off) * sgn
                    a = (u, d2_) if axis == 0 else (d2_, u)
                    lst.append((float(a[0]), float(a[1]), z))
                n += 1
            # a RIDGE WITH VOLUME: two faces meeting at the crest.  A single strip has
            # no thickness and from a high camera you look straight into its hollow
            # back — the overview render read it as torn cardboard.
            p.strip(ROCK, crest_pts, near_pts)
            p.strip(ROCK, far_pts, crest_pts)
    # ---- the spine continuing SE past the envelope -------------------------
    sp = VM.WORLD["riverSpine"]["points"]
    if sp[-1].get("continues"):
        ex, ey = sp[-1]["pos"][0], sp[-1]["pos"][1]
        pex, pey = sp[-2]["pos"][0], sp[-2]["pos"][1]
        d = np.array([ex - pex, ey - pey], float)
        d /= np.linalg.norm(d)
        m = 16
        ts = np.linspace(0.0, 150.0, m)
        xs = ex + d[0] * ts - VM.CX
        ys = ey + d[1] * ts - VM.CY
        w = np.linspace(float(sp[-1]["width"]), float(sp[-1]["width"]) * 1.7, m) * 0.5
        zs = np.linspace(float(sp[-1]["pos"][2]), float(sp[-1]["pos"][2]) - 7.0, m)
        nx, ny = -d[1], d[0]
        p.strip(WATER, list(zip(xs + nx * w, ys + ny * w, zs)),
                list(zip(xs - nx * w, ys - ny * w, zs)))
    STATS["vista_crest_stations"] = n
    return p.finish(col)


# =============================================================================
# PLANTING — the region's forest stamps, F2's trees
# =============================================================================
# The line-up answered the question (round 3): (a) chunky sculpted canopies are the
# field workhorse — real geometry that never breaks up or sorts wrong under the
# steep follow camera — and (c) the hybrid is what breaks a STAND EDGE, because its
# card fringe is only ever seen against the sky, which is the one thing a card is
# good at.  (b) and (d) stay in the prototype's line-up.
STAND_CFG = {
    # emberwood is the region's DENSE wood and the road's corridor runs through it,
    # so it is planted to its packing limit rather than to a round number
    "emberwood-core": dict(spacing=3.05, target=320, shrub=0.55),
    "valley-fringe": dict(spacing=4.4, target=60, shrub=0.40),
    "south-bank": dict(spacing=3.9, target=95, shrub=0.45),
    # rim.west = "forestwall": the wall itself is the stand
    "west-forestwall": dict(spacing=4.3, target=105, shrub=0.35),
}
MEADOW_CFG = dict(spacing=13.0, target=38, shrub=0.22)


def plant_region(col, F, zg, fr, suffix, seed=20260730):
    rng = np.random.RandomState(seed)
    V = O3.Veg("field")
    cell = 3.2
    grid = {}
    placed = []

    def free(x, y, sp):
        r = int(sp / cell) + 1
        c0, r0 = int(math.floor(x / cell)), int(math.floor(y / cell))
        for i in range(c0 - r, c0 + r + 1):
            for j in range(r0 - r, r0 + r + 1):
                for (ax, ay) in grid.get((i, j), ()):
                    if (x - ax) ** 2 + (y - ay) ** 2 < sp * sp:
                        return False
        return True

    def add(x, y, sp):
        grid.setdefault((int(math.floor(x / cell)), int(math.floor(y / cell))),
                        []).append((x, y))

    # keep-outs the map implies: settled ground, the moorage works, and the
    # TREELINE BREAK at the waystone (ch1 fiction: the road comes out of the wood
    # there, so the wood has to stop there)
    keepout = []
    for a in VM.REGION["townAnchors"]:
        bx, by = VM.w2b(a["pos"][0], a["pos"][1])
        keepout.append((float(bx), float(by), float(a["impressionRadius"]) * 0.92))
    mx, my = VM.w2b(*VM.LAND_W["dellhollow-moorage"][:2])
    keepout.append((float(mx), float(my), 13.0))
    wx_, wy_ = VM.w2b(*VM.LAND_W["waystone"][:2])
    keepout.append((float(wx_), float(wy_), 7.5))

    def candidates(mask):
        ii, jj = np.nonzero(mask)
        bx = zg.BX[ii, jj]
        by = zg.BY[ii, jj]
        o = rng.permutation(len(bx))
        return bx[o], by[o]

    def try_plant(bx, by, cfg, zone, edge_ok=True):
        n = 0
        sp = cfg["spacing"]
        for k in range(len(bx)):
            if n >= cfg["target"]:
                break
            x, y = float(bx[k]), float(by[k])
            x += float(rng.uniform(-0.5, 0.5))
            y += float(rng.uniform(-0.5, 0.5))
            if zg.type_at_blender(x, y) != zone:
                continue
            # THE ROAD MUST READ AS A CORRIDOR (H's lesson): in a stand the trees
            # come right up to the verge; in open meadow they stand well back, so
            # the corridor is a property of the wood and not of the whole tile.
            near = 2.45 if zone == "forest" else 5.5
            if float(F.road_dist(np.array([x]), np.array([y]))[0]) < near:
                continue
            dr, tr = F._river_dist(np.array([x]), np.array([y]))
            if float(dr[0]) - float(VM.water_halfwidth(tr)[0]) < 1.6:
                continue
            # 1.28, not the prototype's 0.85: the plateau skirt the emberwood grows
            # on runs 0.5-0.9, and a 0.85 cutoff left a bald band across the corridor
            if float(F.slope_at(np.array([x]), np.array([y]))[0]) > 1.28:
                continue
            if any((x - a) ** 2 + (y - b) ** 2 < r * r for a, b, r in keepout):
                continue
            # canopy interiors are the MASS's ground: specimen trees only at edges
            if getattr(zg, "canopy_int", None) is not None and \
                    bool(zg.wsample(zg.canopy_int.astype(float), x, y) > 0.5):
                continue
            if not free(x, y, sp):
                continue
            z = gh(F, zg, fr, x, y)
            fw = float(zg.wsample(zg.forest_w, x, y))
            interior = fw >= 0.72
            if zone == "meadow":
                key = "a"
            elif interior:
                key = "a" if rng.rand() < 0.80 else "c"
            else:
                key = "c" if rng.rand() < 0.74 else "a"
            s = float(rng.uniform(0.86, 1.26))
            O3.TREE_FN[key](V, x, y, z, s, float(rng.uniform(0, 6.283)), rng)
            if rng.rand() < cfg["shrub"]:
                a = rng.uniform(0, 6.283)
                dd = rng.uniform(1.3, 2.5)
                sx, sy = x + math.cos(a) * dd, y + math.sin(a) * dd
                # shrub (a) ALWAYS, whatever the tree is: the card-fringe shrubs
                # read as cabbages/agave in the foreground of the Emberbrook shot,
                # and understory is exactly where a card is seen flat from above
                O3.SHRUB_FN["a"](V, sx, sy, gh(F, zg, fr, sx, sy),
                                 float(rng.uniform(0.6, 1.0)),
                                 float(rng.uniform(0, 6.283)), rng)
            add(x, y, sp)
            placed.append((x, y, zone, key))
            n += 1
        return n

    byz = {}
    for sid, cfg in STAND_CFG.items():
        m = zg.stand.get(sid)
        if m is None or not m.any():
            continue
        bx, by = candidates(m)
        byz[sid] = try_plant(bx, by, cfg, "forest")
    mm = (zg.idx == O3.Z_MEADOW)
    bx, by = candidates(mm)
    byz["meadow-specimens"] = try_plant(bx, by, MEADOW_CFG, "meadow")

    n = V.n
    print("  planting: %d trees (a=%d c=%d), %d shrubs, %d cards, %d lobes"
          % (len(placed), n["a"], n["c"], n["shrub"], n["cards"], n["lobes"]))
    for k in sorted(byz):
        print("    %-18s %d" % (k, byz[k]))
    STATS["trees"] = len(placed)
    STATS["trees_by_stand"] = byz
    return V.finish(col, suffix), placed, byz


# =============================================================================
# CAMERAS
# =============================================================================
def add_cameras(sc, F, zg, fr, D, crest):
    cams = {}

    def cam(name, eye, aim, fov=42.0, fit="V"):
        nm = "cam_%s__%s" % (name, SUF)
        cd = bpy.data.cameras.new(nm)
        cd.sensor_fit = "VERTICAL" if fit == "V" else "HORIZONTAL"
        if fit == "V":
            cd.angle_y = math.radians(fov)
        else:
            cd.angle_x = math.radians(fov)
        cd.clip_start, cd.clip_end = 0.05, 2400.0
        ob = bpy.data.objects.new(nm, cd)
        sc.collection.objects.link(ob)
        # AN EYE UNDER THE GROUND SEES ROCK, and it renders a frame that looks like a
        # render.  The 'moorage' shot came back as an unbroken brown wall because its
        # eye was derived from the boat's water level while the boat had MOVED onto
        # the bank — the terrain closed over it and nothing in the pipeline objected.
        # Every audit eye is now floored at 2.2u of headroom over its own ground, and
        # says so when it had to move.  This is the region's cheapest instrument and
        # it should have existed before the first render, not after it.
        ex_, ey_, ez_ = float(eye[0]), float(eye[1]), float(eye[2])
        floor_ = gh(F, zg, fr, ex_, ey_) + 2.2
        if ez_ < floor_:
            print("camera %r: eye was %.2fu under its own ground — lifted %.2f -> %.2f"
                  % (name, floor_ - ez_, ez_, floor_))
            ez_ = floor_
        ob.location = Vector((ex_, ey_, ez_))
        ob.rotation_euler = (Vector(aim) - Vector((ex_, ey_, ez_))).to_track_quat("-Z", "Y").to_euler()
        cams[name] = ob
        return ob

    def clear_eye(name, eye, aim, step=1.0, cap=26.0):
        """Raise an audit eye until the first thing it sees is not foliage.

        BAKE RAY-CAST IS THE ONLY VISIBILITY ORACLE, and this is the region's version
        of it.  The first 'gate' frame was 60% canopy at the lens with the gate not in
        it, and the first attempt to fix that tested PROXIMITY TO OBJECT ORIGINS —
        useless, because every canopy in this tile is one joined mesh whose origin is
        somewhere else entirely.  Cast the ray the camera will actually look down.
        """
        dg = bpy.context.evaluated_depsgraph_get()
        ex_, ey_, ez_ = float(eye[0]), float(eye[1]), float(eye[2])
        aimv = Vector(tuple(aim))
        lift, why = 0.0, "clear"
        while lift < cap:
            e = Vector((ex_, ey_, ez_ + lift))
            d = aimv - e
            hit, loc, nor, idx, ob, mx = bpy.context.scene.ray_cast(
                dg, e, d.normalized(), distance=float(d.length))
            if not hit or not (ob.name.startswith("veg_") or "tree" in ob.name):
                why = "clear to the subject" if not hit else "first hit %s" % ob.name
                break
            why = "foliage %s at %.1fu" % (ob.name, (loc - e).length)
            lift += step
        print("camera %r: eye +%.1fu above its first guess, ray -> %s" % (name, lift, why))
        return (ex_, ey_, ez_ + lift)

    # 1) LAYOUT — the whole region from the south, high enough to read the descent
    cam("overview", (-4.0, -212.0, 236.0), (10.0, 6.0, 4.0), fov=64.0, fit="H")
    # 2) EMBERBROOK — coming up the road to the town gate, character height + boom
    ex, ey, ez, etg = F.road_point(0.10)
    vx, vy = L.VILLAGE
    cam("emberbrook", (ex + etg[0] * 4.0 - etg[1] * 3.0,
                       ey + etg[1] * 4.0 + etg[0] * 3.0, ez + 9.0),
        (vx, vy, F.village_h + 1.2), fov=42.0)
    # 3) MIDVALLEY — the chase rig's own geometry (42deg, dist 34, pitch 0.61) on the
    #    open reach, so the shot predicts what the runtime camera actually shows
    mx, my, mz, mtg = F.road_point(0.55)
    d, pit = 34.0, 0.61
    cam("midvalley", (mx - mtg[0] * d * math.cos(pit), my - mtg[1] * d * math.cos(pit),
                      mz + 1.0 + d * math.sin(pit)), (mx, my, mz + 1.0), fov=42.0)
    # 4) GORGE — from the lit (south) side, across the notch at Dellhollow
    ax, ay = VM.w2b(*VM.DELLHOLLOW[:2])
    ctr, tg, nr, wl, hw, _ = gorge_frame(F, VM.DELLHOLLOW[0], VM.DELLHOLLOW[1])
    sgn = -1.0 if nr[1] > 0 else 1.0
    gx = float(ctr[0] + nr[0] * sgn * 30.0 - tg[0] * 12.0)
    gy = float(ctr[1] + nr[1] * sgn * 30.0 - tg[1] * 12.0)
    _gaim = (float(ctr[0]), float(ctr[1]), wl + 5.0)
    cam("gorge", clear_eye("gorge", (gx, gy, gh(F, zg, fr, gx, gy) + 15.0), _gaim),
        _gaim, fov=46.0)
    # 5) SHELF — the mid-descent terrace and its pocket grove, at the CHASE RIG's
    #    own geometry, because this is the closest a player ever stands to a
    #    forest mass and it is therefore the honest test of the foliage
    #    AND THE SUBJECT IS READ FROM THE MAP.  This was `w2b(152.0, 54.0)` — a
    #    coordinate from an orientation the world has not had since the restamp: at
    #    world x=152 the road runs at y~145, so the shot had been pointing 90u off its
    #    own terrace and rendering a cliff and a meadow.  A camera aimed at a typed
    #    number goes stale silently; one aimed at a named map feature cannot.
    _pk = VM.CANYON["shelf"]["pockets"][0]["at"]
    _pi = int(np.argmin(np.hypot(F.road[:, 0] + VM.CX - _pk[0], F.road[:, 1] + VM.CY - _pk[1])))
    sx, sy = float(F.road[_pi, 0]), float(F.road[_pi, 1])
    sz_ = gh(F, zg, fr, sx, sy)
    d2, pit2 = 26.0, 0.61
    cam("shelf", (float(sx) - d2 * math.cos(pit2) * 0.62,
                  float(sy) - d2 * math.cos(pit2) * 0.78,
                  sz_ + 1.2 + d2 * math.sin(pit2)),
        (float(sx), float(sy), sz_ + 1.6), fov=42.0)
    # 6) MOORAGE — from the bank looking ALONG the water at the boat (finding 134)
    bx_, by_, bz_ = D["boat"]
    tx, ty = D["tg"]
    nx_, ny_ = D["nrm"]
    cx_, cy_ = D["ctr"]
    cam("moorage", (cx_ - tx * 15.0 + nx_ * 7.0, cy_ - ty * 15.0 + ny_ * 7.0,
                    D["wl"] + 7.5), (bx_ + tx * 1.0, by_ + ty * 1.0, bz_ + 0.5),
        fov=44.0)
    # 7) OLD GATE — a WALKER'S eye on the road at the gate seat, looking through the
    #    notch.  The seat is derived from emberbrook.map.json, so the shot is derived
    #    from the seat rather than typed.  This is the frame that audits the pinch:
    #    the previous re-seat put the gate IN its own river and only a render found it.
    ogw = VM.PORTALS["old-gate"]["at"]
    ogx, ogy = VM.w2b(ogw[0], ogw[1])
    _bs = int(np.argmin(np.hypot(F.road[:, 0] - ogx, F.road[:, 1] - ogy)))
    _bt = F.road[max(_bs - 3, 0)] - F.road[_bs]
    _bt = _bt / max(float(np.hypot(*_bt)), 1e-6)
    #    THE FIRST VERSION OF THIS EYE WAS INSIDE A TREE CROWN — 60% of the frame was
    #    canopy at the lens and the gate was not in it at all.  That is the
    #    camera-inside-tree-crown case CLAUDE.md names, and the answer is to probe the
    #    occluder rather than re-aim: the eye now rises until nothing veg_ is within
    #    2.2u of it, up to a 9u boom, and the height it settled at is printed.
    _gex, _gey = float(ogx + _bt[0] * 11.0), float(ogy + _bt[1] * 11.0)
    _gz0 = gh(F, zg, fr, _gex, _gey)
    _aim = Vector((float(ogx), float(ogy), float(ogw[2]) + 1.0))
    cam("gate", clear_eye("gate", (_gex, _gey, _gz0 + 2.9), _aim), tuple(_aim), fov=48.0)
    # 7b) THE COURT — the frame this lane exists to answer for, and it is aimed at the
    #    MAP's own culvert point, not at a typed coordinate.  Standing on the east
    #    bench below the gate, looking back UP at the crossing: the doorway on the west
    #    bank, the paving over the culverted water, the road arriving on this side.
    #    "Does it read as a crossing?" is a perceptual question and this is the frame it
    #    gets asked on.
    _cv = VM.REGION["road"].get("culvert")
    if _cv is not None:
        _cx, _cy = VM.w2b(_cv["at"][0], _cv["at"][1])
        _ci = int(np.argmin(np.hypot(F.road[:, 0] - _cx, F.road[:, 1] - _cy)))
        _cj = min(_ci + 16, len(F.road) - 1)          # 16u of ribbon downstream of it
        _ex2, _ey2 = float(F.road[_cj, 0]), float(F.road[_cj, 1])
        _caim = Vector((float(_cx), float(_cy),
                        float(VM.PORTALS["old-gate"]["at"][2]) + 0.4))
        cam("court", clear_eye("court", (_ex2, _ey2, gh(F, zg, fr, _ex2, _ey2) + 2.4),
                               _caim), tuple(_caim), fov=52.0)
    # 8) EMBER FALLS — from the bench below the sill, looking back UP at the plunge and
    #    the gatewall it comes off.  Also the frame that shows whether re-anchoring the
    #    mesa lip to the wall crossing actually put the plateau's edge at the sill.
    efw = VM.LAND_W["ember-falls"]
    efx, efy = VM.w2b(efw[0], efw[1])
    _fex, _fey = float(efx) + 7.0, float(efy) + 22.0
    cam("falls", (_fex, _fey, gh(F, zg, fr, _fex, _fey) + 6.0),
        (float(efx), float(efy), float(efw[2]) + 1.5), fov=46.0)
    # 9) VISTA-RING — from inside the region looking out over the east escarpment at
    #    the ranges the PARENT map put there
    # stand INSIDE the region on the east escarpment and look out over its edge:
    # what this shot has to answer for is whether the world continues past the rim
    vx_, vy_ = VM.w2b(222.0, 100.0)
    cam("vistaring", (float(vx_), float(vy_), gh(F, zg, fr, vx_, vy_) + 13.0),
        (560.0, float(vy_) + 26.0, -34.0), fov=64.0, fit="H")
    return cams


# =============================================================================
def main():
    t_all = time.time()
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    print(VM.describe())
    t0 = time.time()
    F = VM.ValleyField()
    t_field = time.time() - t0
    print("field %dx%d  h %.1f..%.1f  emberbrook=%.2f gate=%.2f  (%.2fs)"
          % (L.NX, L.NY, F.H.min(), F.H.max(), F.village_h, F.clifftown_h, t_field))

    t0 = time.time()
    can_d, can_n = O3.canopy_maps()
    bark_d, bark_n = O3.bark_maps()
    atlas = O3.leafmass_atlas()
    veg_maps = dict(can_d=can_d, can_n=can_n, bark_d=bark_d, bark_n=bark_n, atlas=atlas)
    veg_maps = VV.patch_veg_maps(veg_maps)   # specimen lobes get the new leaf mass
    VV.patch_terrain()                       # rock set, derived meadow, crag strata
    t_assets = time.time() - t0
    print("veg maps ready (%.1fs, one-off shared assets)" % t_assets)

    t_tile = time.time()
    sc = bpy.data.scenes[0]
    sc.name = "valley"
    col = sc.collection
    B.dusk_rig(sc, F, STYLE)
    # a second warm key in the gorge: Dellhollow's mills and windows are the only
    # light down there, and the dusk rig's single hearth is up on the plateau
    dl = bpy.data.lights.new("hearth_dellhollow", "POINT")
    dl.energy, dl.color, dl.shadow_soft_size = 420.0, (1.0, 0.66, 0.32), 1.2
    dob = bpy.data.objects.new("hearth_dellhollow", dl)
    dbx, dby = VM.w2b(*VM.DELLHOLLOW[:2])
    dob.location = (float(dbx), float(dby), 6.5)
    col.objects.link(dob)

    mats = {"matte": B.new_mat("ow_%s_matte" % STYLE, rough=0.9),
            "water": B.new_mat("ow_%s_water" % STYLE, rough=0.28, alpha=0.82, blend=True),
            "emit": B.new_mat("ow_%s_emit" % STYLE, rough=0.6, emit=srgb("ff9f38"),
                              emit_str=9.0),
            "mist": B.new_mat("ow_%s_mist" % STYLE, rough=1.0, alpha=0.2, blend=True)}
    for k in ("water", "mist"):
        mats[k].show_transparent_back = False
    glass_water(mats["water"])
    group = dict(B.GROUP)

    # ---- the zone grid -----------------------------------------------------
    fr = VM.moorage_frame(F)
    t0 = time.time()
    zg = VM.ValleyZoneGrid(F, fr)
    t_zone = time.time() - t0
    cov = zg.coverage()
    print("zone grid %dx%d cell=%.2fu (%.2fs)  %s"
          % (zg.cols, zg.rows, zg.cell, t_zone,
             " ".join("%s=%.1f%%" % (k, v) for k, v in cov.items())))
    print("  thresholds %s  override cells %d" % (zg.thresh, zg.n_override))

    made = {}

    # ---- the dock + boat_tar, solved BEFORE the terrain (F2's order) --------
    cls = dict(hull=TAR, wood=WOOD, dark=TAR, canvas=CANVAS, rope=ROPE, lamp=LAMP)
    deck = B.Prop("walk_dock")
    dprops = B.Prop("dock_props")
    D = O2.build_dock(F, deck, dprops, cls, fr, boat_rig="mast")
    # corridors the crag treatment must not touch
    O3.FLAT_PATHS[:] = [(D["root"][0], D["root"][1], D["ctr"][0], D["ctr"][1], 4.0, 9.0)]
    for (a, b) in VM.ROAD_SPANS:
        O3.FLAT_PATHS.append((float(F.road[a, 0]), float(F.road[a, 1]),
                              float(F.road[b, 0]), float(F.road[b, 1]), 4.0, 9.0))

    # ---- terrain -----------------------------------------------------------
    t0 = time.time()
    ground, skirt, fcrag = O3.build_terrain(col, F, zg, fr)
    t_ter = time.time() - t0
    for ob, key in ((ground, "ground"), (skirt, "skirt")):
        ob.name = "%s__%s" % (ob.name, SUF)
        ob.data.name = ob.name
        made[key] = ob
    print("  terrain built in %.1fs" % t_ter)

    # ---- ribbons, towns, props --------------------------------------------
    made["water"] = build_water(col, F)
    _fl = build_falls(col, F, zg, fr)
    if _fl is not None:
        made["falls"] = _fl
    _tb = build_tributaries(col, F, zg, fr)
    if _tb is not None:
        made["tributaries"] = _tb
    made["road"] = build_road(col, F)
    cw = build_causeway(col, F, zg, fr)
    if cw is not None:
        made["causeway"] = cw
    made["green"] = build_emberbrook_green(col, F, zg, fr)
    made["emberbrook"] = build_emberbrook(col, F, zg, fr)
    dh, crest = build_dellhollow(col, F, zg, fr)
    made["dellhollow"] = dh
    dc = build_dam_crest(col, F, zg, fr, crest)
    if dc is not None:
        made["damcrest"] = dc
    made["portals"] = build_portals(col, F, zg, fr)
    made["oldgate"] = build_old_gate(col, F, zg, fr)
    # FOURTH forest: BUSH LANGUAGE (tools/valley_veg.py + tools/bushlang.py).  The
    # stand masks, the WIDE road corridor, the clearings and the walkable-under
    # veg_ semantics are the third iteration's, unchanged — what changed is that a
    # stand is now a lobed core with a dense shell of leaf-cluster cards on a real
    # atlas instead of a painted swell.  One core + one cards mesh per stand, each
    # with its own vcol material, so they stay out of the class passes as before.
    for i_, ob_ in enumerate(VV.build_canopy(col, F, zg, fr, VM, STATS)):
        made["canopy_%d" % i_] = ob_
    made["props"] = build_props(col, F, zg, fr)
    made["fx"] = build_vista(col, F)

    # ---- the moorage: basin water, jetty, boat, spur -----------------------
    do = deck.finish(col)
    do.name = do.data.name = "walk_dock"
    po = dprops.finish(col)
    po.name = po.data.name = "boat_tar"
    made["dock"], made["boat"] = do, po
    wp = B.Prop("water_pool")
    O2.pool_water(wp, WATER, fr)
    made["pool"] = wp.finish(col)
    made["dockpath"] = build_moorage_spur(col, F, zg, fr, D["root"])

    # ---- 1.45u scale references (renders only; stripped at export) ---------
    rp = B.Prop("ref_char")
    px, py, pz, _ = F.road_point(0.55)
    qx, qy = L.VILLAGE
    qz = F.village_h
    ex, ey = float(F.road[-1, 0]), float(F.road[-1, 1])
    ez = float(F.road_h[-1])
    for (ox, oy, oz) in ((px, py, pz), (qx + 4.4, qy, qz), (ex, ey, ez),
                         (D["head"][0], D["head"][1], D["deck_z"])):
        rp.cone(PEAK, (ox, oy, oz + 0.72), 0.26, 0.26, 1.05, seg=10)
        rp.ico(PEAK, (ox, oy, oz + 1.24), (0.26, 0.26, 0.26), subd=1)
        rp.ico(PEAK, (ox, oy, oz + 0.21), (0.26, 0.26, 0.21), subd=1)
    made["ref"] = rp.finish(col)

    # ---- trees -------------------------------------------------------------
    t0 = time.time()
    field, placed, byzone = plant_region(col, F, zg, fr, SUF)
    t_veg = time.time() - t0
    veg_keys = []
    for k, o in field.items():
        made["veg_" + k] = o
        veg_keys.append("veg_" + k)
    print("  planting took %.1fs" % t_veg)

    # ---- clearance safety net ---------------------------------------------
    for key in ("road", "green", "dockpath", "dock", "damcrest"):
        if key not in made:
            continue
        n = O3.conform_ribbon(made[key], F, zg, fr)
        if n:
            print("  conform %-10s lifted %d verts clear of the treated ground"
                  % (key, n))
    # ---- MESH-TRUE conform (the verify lesson): the analytic conform above
    # measures a different ground than the verifier, which raycasts the ACTUAL
    # triangulated (and vertex-jittered) terrain mesh — they disagree by up to
    # the facet deviation.  Same class of bug as image-vs-geometry occlusion;
    # same cure: make both sides measure the SAME artifact.
    from mathutils.bvhtree import BVHTree
    gobj = next((o_ for o_ in bpy.data.objects
                 if o_.type == "MESH" and o_.name.startswith("ground_valley")), None)
    # (the build names it ground_valley__valley; export strips the suffix — a
    # bare .get() found nothing and this whole block silently skipped)
    if gobj is not None:
        dg_ = bpy.context.evaluated_depsgraph_get()
        bvh = BVHTree.FromObject(gobj, dg_)
        for key in ("road", "green", "dockpath", "dock", "damcrest"):
            if key not in made:
                continue
            ob_ = made[key]
            lifted = 0
            for v_ in ob_.data.vertices:
                wc = ob_.matrix_world @ v_.co
                hit = bvh.ray_cast(Vector((wc.x, wc.y, wc.z + 60.0)), Vector((0, 0, -1)))
                if hit[0] is not None and wc.z < hit[0].z + 0.035:
                    v_.co.z += (hit[0].z + 0.035) - wc.z
                    lifted += 1
            if lifted:
                print("  mesh-true conform %-10s lifted %d verts" % (key, lifted))

    # ---- colours, shading, materials --------------------------------------
    PROPKEYS = ([k for k in ("skirt", "water", "falls", "tributaries", "road", "causeway", "green",
                             "emberbrook", "dellhollow", "damcrest", "portals", "oldgate",
                             "props", "fx", "dock", "boat", "pool", "dockpath",
                             "ref") if k in made] + veg_keys)
    for i, key in enumerate(PROPKEYS):
        jit = 0.10 if key.startswith("veg_") else 0.055
        made[key + "_cls"] = B.write_prop_colors(made[key], STYLE, True, jit, seed=41 + i)
    SOFT = {"water", "pool", "props", "green", "fx"} | set(veg_keys)
    for key in PROPKEYS:
        ob = made[key]
        v = key in SOFT
        ob.data.polygons.foreach_set("use_smooth", [v] * len(ob.data.polygons))
        ob.data.update()

    pm = B3.props_materials_f2(made, mats, group, veg_maps)
    UVKEYS = [k for k in ("emberbrook", "dellhollow", "portals", "oldgate", "falls", "props", "damcrest",
                          "causeway", "boat", "dock", "skirt", "fx") if k in made]
    UVKEYS += [k for k in veg_keys if not k.endswith("_cards")]
    for key in UVKEYS:
        scale = 1.35 if key.startswith("veg_") and "trunks" not in key else 1.0
        B3.vec_planar_uv(made[key], 1.0 / scale)
    gains = {g: m["vcol_gain"] for g, m in pm.items()}
    for key in UVKEYS:
        B3.apply_class_gains(made[key], made[key + "_cls"], group, gains)
    # LAST write to COLOR_0 for the town impressions: the per-house tint families.
    # It runs after apply_class_gains on purpose — that pass rewrites every corner
    # from the class palette and would erase a tint applied before it.
    for key in ("emberbrook", "dellhollow"):
        if key in made:
            STATS[key + "_tint_families"] = apply_house_tints(made[key], made[key + "_cls"])
    for key in PROPKEYS:
        ob = made[key]
        if ob.data.materials:
            continue
        B2.assign_slots2(ob, mats, made[key + "_cls"], group)
    B3.terrain_pbr_f2(made, F, zg, fcrag)
    VV.patch_green(made)               # and drop leafy_grass from the bundle
    VV.stretch_rock_uv(made)           # a cliff wants a coarser run than a lawn

    # ---- THE LANDSCAPE PASS (L3 then L2 — tools/valley_land.py) -------------
    # Both read the ground's own SLOT CHOICE, so they run AFTER terrain_pbr_f2
    # writes it.  L3 first because it only rewrites COLOR_0 and L2 only reads
    # kinds; the order is the probe's own and keeps the two comparable to it.
    t0 = time.time()
    TS = VL.Terrain(made["ground"])
    STATS["land_surface"] = VL.surface(made["ground"], TS)
    land_objs, STATS["land_tufts"] = VL.tufts(col, made["ground"], zg, mats, T=TS)
    for ob_ in land_objs:
        made[ob_.name] = ob_
    print("  landscape pass took %.1fs" % (time.time() - t0))

    # ---- the QA-only zone overlay -----------------------------------------
    ovl = O3.build_zone_overlay(col, F, zg, fr)
    ovl.name = ovl.data.name = "qa_zone_overlay__" + SUF
    om = B.new_mat("ow_%s_zoneovl" % STYLE, rough=1.0, alpha=0.62, blend=True)
    nt = om.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Col"
    nt.links.new(ca.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    om.show_transparent_back = False
    ovl.data.materials.append(om)

    # ---- cameras + render conventions -------------------------------------
    cams = add_cameras(sc, F, zg, fr, D, crest)
    sc.camera = cams["overview"]
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
        sc.eevee.shadow_pool_size = 1024
    except Exception:
        pass

    t_tile = time.time() - t_tile

    # ---- zones.json + the build record ------------------------------------
    os.makedirs(BUNDLE, exist_ok=True)
    zp = os.path.join(BUNDLE, "zones.json")
    zg.write(zp)
    print("zones.json -> %s (%.1f kB)" % (zp, os.path.getsize(zp) / 1e3))

    tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
               for o in sc.objects if o.type == "MESH" and not o.name.startswith("qa_"))
    meshes = len([o for o in sc.objects if o.type == "MESH"])
    print("tile totals: %d meshes, %d tris (excl. QA overlay)" % (meshes, tris))

    qa = os.path.join(ROOT, "docs/qa/overworld")
    os.makedirs(qa, exist_ok=True)
    rec = dict(STATS)
    rec.update(dict(region=VM.REGION_ID, tile=[VM.TILE_W, VM.TILE_H], step=VM.STEP,
                    lattice=[L.NX, L.NY], build_s=round(t_tile, 2),
                    field_s=round(t_field, 2), zone_s=round(t_zone, 3),
                    terrain_s=round(t_ter, 2), veg_s=round(t_veg, 2),
                    veg_assets_oneoff_s=round(t_assets, 2), meshes=meshes, tris=tris,
                    zone_coverage_pct={k: round(v, 2) for k, v in cov.items()},
                    zone_cells=zg.cols * zg.rows,
                    road_pushed_stations=len(VM.ROAD_PUSH),
                    road_spans=[[int(a), int(b)] for a, b in VM.ROAD_SPANS],
                    h_range=[round(float(F.H.min()), 2), round(float(F.H.max()), 2)]))
    json.dump(rec, open(os.path.join(qa, "valley_build.json"), "w"), indent=1,
              sort_keys=True)

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED %s  (%.1fs total, %.1fs tile)" % (OUT_BLEND, time.time() - t_all, t_tile))


if __name__ == "__main__":
    main()
