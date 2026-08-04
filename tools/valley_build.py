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
# THE PER-HOUSE CHIMNEY GATE (R13).  One record per house built, in both towns:
# (footprint inside the pad, outer face behind the wall face, cap above the ridge,
# pad margin, wall recess, ridge clearance).  A house that fails any clause is built
# WITHOUT a chimney — the gate refuses, it does not merely report.
CHIM_GATE = []

# =============================================================================
# R13 — THE ROOFS WERE THE LOUDEST THING IN THE FRAME
# =============================================================================
# The twelfth blind critic: "the grass is a dull uniform olive ... while the roofs
# stay a strong terracotta and the river stays a strong cyan — two loud colours on
# a dead field", filed explicitly as the signature of a GLOBAL saturation walk-back
# where a PER-MATERIAL one was needed.  This is the per-material one, and it is a
# palette entry rather than a grade term precisely because a grade cannot separate
# a roof from the ground beside it.
#
# Measured (scratchpad/r13b/warmhue.py, warm band 8-32 deg at sat > 0.50): the r12
# meadow plate carries 27.8% of its pixels in that band at mean saturation 0.600;
# the three FFIX-reimagined overworld references carry 0.06-0.55% at 0.60-0.65.
# THE REFERENCES ARE NOT LESS SATURATED WHERE THEY ARE WARM — they are warm over
# half a percent of the frame instead of a quarter of it.  So the fix is chroma on
# the classes that cover area, not a hue move.
#
# `ow_f2_tiles` is a red-slate PHOTO albedo multiplied by this class colour, so the
# product's chroma is roughly (1 - s_tex)(1 - s_col): PAL f's a86b52 is s 0.512 and
# takes the pair to ~0.68.  917366 is s 0.297 at the SAME Rec.709 luminance (120.5
# against 118.1 — a chroma move must not smuggle in a value move, which is how the
# last two "desaturations" in this loop turned into brightness changes), landing the
# product near 0.54.  Still fired clay; no longer the loudest thing in the frame.
#
# =============================================================================
# R14 — AND THEN THE ROOF HAD NEITHER MORE CHROMA NOR LESS VALUE THAN THE WALL
# =============================================================================
# The fourteenth blind critic: "every house wall is the SAME tan, and the roofs are
# only a few percent different in value from the walls — so the whole village reads
# as ONE UNDIFFERENTIATED PUTTY-COLOURED MASS."  R13 desaturated the roof AT HELD
# LUMINANCE, deliberately.  That was right about chroma and is exactly why the value
# collapsed: holding luminance while removing chroma leaves a plane that differs
# from the wall under it in NOTHING.
#
# Measured on the shipped r13 bundle and the shipped r13 plate
# (tools/ow_probe/glb_albedo.py for the artifact, tools/ow_probe/matclass.py for the
# picture — the second is r13's classifier extended to walls and roofs, because
# HOUSES WERE NEVER A MEASURED CLASS and no grass statistic constrains a roof):
#
#   effective albedo  ow_f2_plaster L709 .0776   ow_f2_tiles L709 .0487  (0.63x)
#   the r13 meadow    wall L .445 hue 26.2       roof L .502 hue 24.9    (1.13x)
#   the reference     wall L .280 R-B -.082      roof L .231 R-B -.153   (0.83x)
#
# So in the PICTURE our roof is 13% BRIGHTER than the wall and 1.1 degrees away from
# it in hue; the reference's is 17% darker and decisively cooler.  A roof plane also
# collects about 2.1x the wall's irradiance here (measured as rendered/albedo per
# class, 4.55 against 2.21 — a 34-degree sun and a whole sky hemisphere), which is
# why an albedo ratio that already read as 0.63 arrived on screen above 1.
#
# TAKE THE VALUE.  Target eff albedo L709 0.0175 — 0.36x — with the class colour on
# the COOL side of neutral so the product lands blue-grey slate rather than a darker
# tan.  414c75 is that number solved backwards through the measured transfer (eff =
# tex_lin x k x pal_lin, k read off the shipped GLB per channel), NOT picked by eye:
# the product is [.0151 .0178 .0222] linear = a dark blue-grey at HSV sat 0.16.  The
# palette entry looks vividly blue in isolation and must — it is multiplying a red
# slate photo, and only the PRODUCT is ever seen.  R13's chroma finding stands: this
# does not go back toward saturated terracotta, it goes past neutral the other way.
#
# AND THEN A COOL NEUTRAL IS NOT THE COOL SECTOR.  With 414c75 in the bundle the
# roof measured HSV sat 0.042 in the frame against the reference slate's 0.446, and
# tools/ow_probe/framespread.py — which counts how much of a frame's chroma sits in
# each 30-degree hue sector — still found only THREE sectors at or above 8% where
# the references have four, the missing one being a cyan-blue holding a fifth of
# their frame.  The cause is measurable and is not the palette: the key is warm, so
# per-channel irradiance on a roof plane runs 7.36 / 5.65 / 4.34 and a 1.7x warm
# light cancels most of a cool albedo.  Pushed on the SAME held-luminance discipline
# r13 wrote down (eff L709 .0171 against .0176, inside a percent) so this is a
# chroma move and not a second value move.
#
# =============================================================================
# R14 SECOND PASS — THE SECTOR WAS BOUGHT WITH HUE DISTANCE, NOT WITH CHROMA
# =============================================================================
# 374c81 landed the value (roof/wall 0.82 against the reference's 0.83) and that
# stands.  What it did NOT land is the roof's own chroma: HSV sat 0.076 against the
# reference slate's 0.446, 5.9x under, while the roof-wall warm-cool ran to -0.26
# against the reference's -0.07, 3.7x over.  THOSE ARE ONE NUMBER, NOT TWO, and
# this is the arithmetic the last pass did not write down:
#
#   for a blue-grey (B is the max channel, R the min)   R-B  ==  -sat x max
#
# Checked on both frames to three places: reference roof sat .446 x max .344 =
# .154 against a measured R-B of -.153; our roof .076 x .372 = .0283 against
# -.0280.  It is an identity, not a fit.  So
#
#   roof-wall warm-cool  =  -(sat_roof x max_roof)  -  (R-B)_wall
#
# and with the wall held where it is (R-B +0.231, a warm tan), RAISING ROOF CHROMA
# CAN ONLY DRIVE THE WARM-COOL NUMBER FURTHER NEGATIVE.  They do not move
# together; they move apart, by construction.  The reference reaches -0.071 AT sat
# 0.446 because ITS wall is cool too (R-B -0.082, hue 223, sat 0.242 — a stone
# windmill, not plaster).  -0.07 is therefore not an axis this class can be steered
# along at all: it is a joint statement about wall AND roof, and closing it from
# the roof alone is impossible.  Solving it from the wall instead would need our
# wall at R-B -0.095, i.e. a COOL GREY VILLAGE.  That is an art-direction call and
# is left to the user; the gap is named below, not quietly closed.
#
# SO THIS PASS BUYS CHROMA AND SPENDS WARM-COOL, DELIBERATELY, and the previous
# pass's own diagnosis is why it is affordable: the key is warm, so the measured
# per-channel transfer on the roof box (display-linear / eff albedo out of the
# shipped GLB, tools/ow_probe/glb_albedo.py + tools/ow_probe/matclass.py) runs
#
#   9.06 / 5.58 / 3.73   —  R/B 2.43x
#
# NOT the 7.36/5.65/4.34 the last pass recorded (that number was read before its
# own second push; re-measured here on the shipped bundle it is 2.4x, not 1.7x).
# A cool albedo is cancelled harder than anyone thought, so the albedo has to go
# much further blue in LINEAR terms than the on-screen target looks.  Solved
# backwards through that transfer for the reference's own roof channel GEOMETRY at
# our own held frame value (L709 0.348, so the landed 0.82 value ratio does not
# move): target display 0.287 0.351 0.516, eff albedo .00738 .01815 .06137.
#
# PREDICTION, WRITTEN BEFORE THE BUILD (the brief's prediction was that chroma and
# warm-cool would move TOGETHER; the identity above says they cannot, and this is
# the falsifiable form):
#   * roof HSV sat 0.076 -> 0.30..0.44, SHORT of the 0.444 the proportional solve
#     says, because the transfer is not purely multiplicative — a two-point fit
#     across the r13 and r14 bundles puts ~25% of the roof box's luminance in an
#     albedo-independent floor (haze, lift, and non-tile pixels inside the box),
#     and a floor dilutes a chroma move;
#   * roof-wall warm-cool -0.26 -> WORSE, about -0.35..-0.46, never better;
#   * framespread stays at 4 sectors and circular R drops below 0.638.
# If the warm-cool number IMPROVES, the identity is wrong and everything above it
# is wrong with it.
#
# MEASURED, AFTER THE BUILD (meadow plate; and see docs/qa/ow-refs/LOOP.md).  The
# classifier itself had to be fixed first — its water exclusion was deleting 36% of
# the roof boxes' pixels, the bluest ones, the moment the slate became slate, so the
# 0.076 above was partly the instrument.  ON THE FIXED CLASSIFIER, before -> after,
# reference in brackets:
#
#   roof HSV saturation      0.114 -> 0.309   [0.457]
#   roof absolute chroma     0.044 -> 0.149   [0.154]   <- MATCHED
#   roof-wall warm-cool     -0.276 -> -0.375  [-0.076]  <- moved APART, as predicted
#   roof/wall value ratio    0.839 -> 0.852   [0.823]   <- the landed number held
#   frame circular R         0.638 -> 0.363   [0.493]
#   frame CB 210-240 share      9% -> 24%     [21%]
#
# THE SATURATION GAP IS OPEN AND IT IS A VALUE GAP, NOT A CHROMA GAP.  sat is
# chroma/max; our roof's max is 0.480 where the reference's is 0.344, because our
# whole built palette renders ~1.5x brighter than theirs (wall L 0.423 vs 0.280).
# The absolute chroma is already theirs.  Closing the rest means darkening the roof
# ~30%, which moves the value ratio this pass is forbidden to touch — an exposure
# question for the pipeline lane, not an albedo question for this one.  DO NOT
# spend another pass pushing this palette entry at it.
# R14 THIRD PASS — AND THE PICTURE REFUSED THE NUMBER, WHICH IS THE ROUND'S OWN RULE
# ARRIVING ON THE ROUND'S OWN WORK.  2d4db1 was solved backwards from the reference
# slate's absolute chroma and it HIT IT (0.149 against their 0.154, from 0.044).  The
# frame it produced has cobalt roofs: the village reads as a painted toy set, not as a
# hamlet, and `framespread` says the same thing from the other side — circular R 0.363
# against ref 1's 0.631 and ref 3's 0.493, i.e. PAST BOTH REFERENCES, with the cyan-blue
# sector at 24% against their 21% but carrying a hero colour rather than a material.
# THE REASON THE CHROMA TARGET IS NOT REACHABLE HERE IS MEASURED AND IS A VALUE FACT:
# sat = chroma / max, and our roof's max channel is 0.480 where the reference's is 0.344
# — our built palette renders about 1.5x brighter than the windmill it is being matched
# to (their wall L 0.280, ours 0.423).  At OUR brightness, the reference's SATURATION
# lands as cobalt; a slate is a dark saturated blue, and the dark half is not available
# without moving the roof/wall value ratio that this round already got onto their number
# (0.85 against 0.82).  So the chroma is set where the PICTURE puts it, between the two
# solved values, and the residual gap is recorded as a VALUE gap in LOOP.md rather than
# spent on another palette entry.  374c81 read as a grey with a cool cast; 2d4db1 as
# cobalt; this is 40% of the way from the first to the second in effective albedo (the
# blue channel's hex -> shipped-albedo transfer is linear at gain 0.1366, measured on
# both builds' own GLBs, so that fraction is arithmetic and not a guess).
ROOF_HEX = "32498f"
B.PAL[STYLE][ROOF] = ROOF_HEX
B.PAL_LIN[STYLE][ROOF] = srgb(ROOF_HEX)


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
#
# ============================ R13: A DEPTH-DRIVEN ALPHA, AND WHY IT IS ALLOWED HERE
# The thirteenth blind critic: the river is "OPAQUE FLAT CYAN: no reflection, no
# depth falloff, no shore transition, hitting the bank on a hard line ... the most
# saturated thing in the frame and the least believable material in either frame."
# docs/plans/water-transparency.md is this repo's ratified answer and its central
# ruling is that THE BATHYMETRY IS THE DELIVERABLE AND THE SHADER IS THE CHEAP
# PART — a depth-alpha ramp does nothing without a bed and a shallow zone.  So the
# first thing this round did was ask THIS river that question, with that document's
# own method (a down-ray stack; scratchpad/r13b/bathy.py against the built blend):
#
#   * A BED EXISTS UNDER EVERY STATION.  0 of 85 sampled stations have no ground
#     under the channel centre.  Centre depth: min 0.84, median 1.63, p90 3.57,
#     max 3.64u.  Dellhollow's pools were two flat slabs at a uniform 3.5-7.5 m;
#     this channel is a groove cut into the height field and it has a real profile.
#   * AND A REAL SHALLOW ZONE.  Across the channel the depth runs ~1.6u at the
#     centre, ~0.3-1.3u at half-width and crosses zero between 0.75 and 1.0 of the
#     half-width, i.e. the ramp lands inside the water's own footprint.
#   * FINDING 2 IS LARGELY ABSENT.  86% of the strip's own edge samples are BURIED
#     IN THE BANK (ground above the waterline); only 14% float, by a median 0.53u.
#     Dellhollow's sheets were 43-79% floating rectangle corner, which is why
#     making them transparent there would have been worse.
#
# So the ratified recipe applies as ratified, at x1.0 — no per-sheet rescale.  The
# two things this build has to add are the ones the measurement implies: the strip
# needed INTERIOR VERTICES to carry the ramp (it was two columns, so a per-vertex
# alpha could only ever describe its two edges), and the alpha has to come off
# COLOR_0.
#
# WHICH RE-INTRODUCES, DELIBERATELY, THE LINK THE COMMENT BELOW REMOVED.  Read that
# comment first: an alpha link from COLOR_0 WON over the BSDF default and shipped an
# opaque river for four weeks.  The difference is that the vertex alpha was flat 1.0
# then and carries the ramp now.  MEASURED IN THE EXPORTED GLB, not in Blender:
# COLOR_0 shipped as **VEC3** before this change — the exporter drops the alpha
# channel entirely unless the Alpha socket is fed from it, so `baseColorFactor[3]`
# was the only alpha that existed.  Linking it is what makes the attribute VEC4;
# three's GLTFLoader then sets USE_COLOR_ALPHA off `itemSize === 4` and the
# per-vertex alpha multiplies into the fragment.  The gate for this is a byte read
# of the accessor (scratchpad/r13b/glbwater.py), never the Blender-side print.
GLASS = "#f4f7f6"        # R13: NEAR-NEUTRAL.  This constant is a MULTIPLIER on the
# water's COLOR_0, and B1's #bfe6ee is itself a blue-green, so it was multiplying a
# saturated teal albedo by another blue and the product came out MORE chromatic than
# either (linear (0.019, 0.127, 0.170) — sRGB (37, 100, 115) at HSV sat 0.678).  The
# water's colour is authored in one place now, WATER_HEX below, and this stays out of
# its way.  Letting the transparency and the bed carry the colour is the ratified
# note's own recommendation.
WATER_HEX = "44757f"     # the river's albedo, written straight into COLOR_0.  With
# GLASS the product is sRGB (65, 113, 122) at sat 0.467 against r12's 0.678 — a 31%
# chroma cut in the albedo BEFORE the bed shows through it.
GLASS_OPACITY = 0.62     # the fallback for water with no bathymetry (falls, tribs)
GLASS_ROUGH = 0.06

# The ratified depth -> alpha ramp, docs/plans/water-transparency.md W3, verbatim.
ALPHA_RAMP = [(0.00, 0.06), (0.60, 0.30), (1.50, 0.62), (3.00, 0.88), (4.00, 0.97)]


def depth_alpha(depth):
    """Piecewise-linear ALPHA_RAMP, clamped at both ends."""
    d = np.asarray(depth, float)
    xs = np.array([p[0] for p in ALPHA_RAMP])
    ys = np.array([p[1] for p in ALPHA_RAMP])
    return np.interp(np.clip(d, xs[0], xs[-1]), xs, ys)


def _srgb_to_linear(hex_):
    out = []
    for i in (0, 2, 4):
        c = int(hex_.lstrip("#")[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def glass_water(m, tint=GLASS, opacity=GLASS_OPACITY, rough=GLASS_ROUGH,
                vertex_alpha=True):
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
    if vertex_alpha and vc is not None:
        # R13: the link goes BACK IN, on purpose (see the header above).  It is what
        # promotes COLOR_0 from VEC3 to VEC4 in the export, and the depth ramp rides
        # that alpha.  `opacity` above stays as the socket default and is what the
        # material falls back to if the link is ever cut again.
        nt.links.new(vc.outputs["Alpha"], b.inputs["Alpha"])
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
    print("  water: B1 glass  tint %s -> linear %s, opacity %.2f (%s), rough %.2f"
          % (tint, ", ".join("%.4f" % v for v in lin), opacity,
             "COLOR_0 alpha LINKED — the ramp drives it" if vertex_alpha and vc
             else "unlinked, exports as baseColorFactor[3]", rough))
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
    # R13 — THE STRIP NEEDS AN INSIDE.  It was two columns wide, one per bank, so a
    # per-vertex depth ramp could only ever describe its two EDGES: the whole
    # shallow-to-deep gradient the bathymetry actually has had nowhere to live, and
    # the surface interpolated straight from one shore alpha to the other.  Nine
    # columns across is all it takes; the ramp is written in water_bathymetry()
    # below, from the same height field the channel was cut out of.  (Adjacent
    # columns are laid as separate strips and therefore share duplicate vertices —
    # they take identical positions AND identical alpha, so no seam exists.)
    ncol = 9
    us = np.linspace(-1.0, 1.0, ncol)
    cols_ = [list(zip(bx + nx * hw * u, by + ny * hw * u, wl)) for u in us]
    for k in range(ncol - 1):
        p.strip(WATER, cols_[k], cols_[k + 1])
    ob = p.finish(col)
    STATS["river_width"] = (float(VM.RIV_WIDTH[0]), float(VM.RIV_WIDTH[-1]))
    return ob


def water_bathymetry(made, F, zg, fr):
    """THE WATER SHEETS' OWN COLOR_0: one albedo, and a DEPTH-DRIVEN ALPHA.

    Runs as the LAST write to COLOR_0 on these objects (see main): B.write_prop_colors
    rewrites every corner from the class palette and would erase anything applied
    before it — the same ordering rule apply_house_tints already lives under.

    Only WATER-class faces are touched.  `water_falls` carries a STONE lip in the
    same mesh, and a pass that recoloured the object rather than the class would
    have painted the rock the colour of the river — a mixed-class prop is why the
    per-polygon class array exists.

    Depth is measured against the SAME analytic height field the channel was cut
    from (O3.height, crag treatment included), so the ramp cannot disagree with the
    ground it is describing.  Sheets with no meaningful bathymetry take a flat
    alpha: the falls curtain is a vertical sheet whose "depth" is meaningless, and
    the tributaries are laid 0.05u above their own bed by construction, which the
    ramp would render at alpha 0.08 — i.e. it would DELETE them.  A ramp applied
    where its input is not a depth is a ramp applied to noise.
    """
    # `dhpools` is deliberately NOT flat: a lock pond has a real depth (shallow at
    # the head where it meets the river, deepest against its own dam), so the ramp
    # describes it correctly and darkens the ponded reach against the shallow river
    # — which is the "boat queue pooled above the jam" read, for free. `dhfalls` is
    # flat for the same reason `falls` is: a curtain is a vertical sheet and its
    # distance-to-ground is not a depth.
    flat = {"tributaries": 0.72, "falls": 0.86, "dhfalls": 0.86}
    lin = _srgb_to_linear(WATER_HEX)
    rep = {}
    for key in ("water", "pool", "tributaries", "falls", "dhpools", "dhfalls"):
        ob = made.get(key)
        cls = made.get(key + "_cls")
        if ob is None or cls is None:
            continue
        me = ob.data
        ca = me.color_attributes.get("Col")
        if ca is None:
            continue
        nv, nl = len(me.vertices), len(me.loops)
        co = np.zeros(nv * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        if key in flat:
            a_v = np.full(nv, float(flat[key]))
            depth = None
        else:
            depth = co[:, 2] - np.asarray(ghv(F, zg, fr, co[:, 0], co[:, 1]), float)
            a_v = depth_alpha(depth)
        # CORNER or POINT domain — measure the attribute, do not assume it
        per_loop = len(ca.data) == nl
        if per_loop:
            li = np.zeros(nl, dtype=np.int64)
            me.loops.foreach_get("vertex_index", li)
            sel = np.zeros(nl, bool)
            for pi, poly in enumerate(me.polygons):
                if int(cls[pi]) == WATER:
                    for lx in poly.loop_indices:
                        sel[lx] = True
            aa = a_v[li]
        else:
            sel = np.zeros(nv, bool)
            for pi, poly in enumerate(me.polygons):
                if int(cls[pi]) == WATER:
                    for vx in poly.vertices:
                        sel[vx] = True
            aa = a_v
        buf = np.zeros(len(ca.data) * 4)
        ca.data.foreach_get("color", buf)
        buf = buf.reshape(-1, 4)
        buf[sel, 0], buf[sel, 1], buf[sel, 2] = lin[0], lin[1], lin[2]
        buf[sel, 3] = aa[sel]
        ca.data.foreach_set("color", buf.ravel())
        me.update()
        rep[key] = dict(verts=nv, water_corners=int(sel.sum()),
                        alpha=[round(float(np.min(aa[sel])), 3),
                               round(float(np.median(aa[sel])), 3),
                               round(float(np.max(aa[sel])), 3)],
                        depth=None if depth is None else
                        [round(float(np.min(depth)), 2), round(float(np.median(depth)), 2),
                         round(float(np.max(depth)), 2)])
        print("  bathymetry %-13s %5d verts, %5d water corners, alpha %s%s"
              % (key, nv, int(sel.sum()), rep[key]["alpha"],
                 "" if depth is None else "  depth %s" % rep[key]["depth"]))
    return rep


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
    # 1. THE LIP — a hard rock sill, so the water leaves the GROUND, not a slope.
    #    R13: IT IS ITS OWN MESH NOW, and the reason is an exporter rule measured in
    #    the shipped GLB rather than guessed.  The depth ramp rides COLOR_0's ALPHA,
    #    and the glTF exporter only writes COLOR_0 as VEC4 when the mesh's materials
    #    feed their Alpha from it.  A mesh carrying BOTH the water material and the
    #    rock one exported VEC3 — alpha silently dropped for the whole object — so
    #    the curtain fell back to baseColorFactor[3] = 1.0 and went fully opaque,
    #    while the river beside it ramped correctly.  ONE MIXED-MATERIAL MESH
    #    DISABLES VERTEX ALPHA FOR EVERY PRIMITIVE IN IT.  Still `water_` prefixed,
    #    so it stays out of collision exactly as it was inside water_falls.
    lp = B.Prop("water_falls_lip")
    for k in range(7):
        u = (k - 3) / 3.0
        lp.cube(STONE, (float(c0[0] + n0[0] * u * hw0 * 1.12),
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
    return p.finish(col), lp.finish(col)


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
# R14 — THREE FAMILIES SPANNING 18% OF VALUE IS NOT A VILLAGE, IT IS ONE BUILDING
# PAINTED THREE TIMES.  Measured on the r13 meadow plate with the unsupervised
# split (tools/ow_probe/matclass.py): wall value across the five foreground
# buildings ran 0.234 to 0.336 and MOST of that was which way the house faced, not
# which family it drew.  The families themselves were 1.000 / 0.821 / 0.999 in
# Rec.709 factor — two of the three were the same house.  FIVE families now, spaced
# ~15% apart and spanning 1.87x, and the hue moves with the value the way real
# render does: limewash is pale AND cool, daub is dark AND warm, so a neighbour
# differs on two axes at once instead of being a dimmer copy.
#
# THE CEILING IS THE CLAMP, NOT TASTE.  COLOR_0 is written pal_lin x class gain x
# family x per-face jitter and vec_gain CLIPS it at 1.0; the shipped plaster base
# measures 0.81/0.69/0.49 with jitter to ~0.855 on red, so a family above ~1.17 on
# R would flatten its own brightest faces into a clipped patch and the family would
# stop being a colour.  1.12 is that headroom, not a preference.
WALL_TINTS = [(1.12, 1.14, 1.20),        # limewash — the brightest, and cool
              (1.00, 1.00, 1.00),        # the palette's own plaster
              (0.95, 0.85, 0.66),        # ochre daub, warm
              (0.70, 0.73, 0.79),        # grey render, cool
              (0.70, 0.60, 0.45)]        # earth daub, dark and warm
ROOF_TINTS = [(1.00, 1.00, 1.00),        # the palette's own slate
              (0.80, 0.83, 0.90),        # weathered, greyer and cooler still
              (1.12, 1.06, 0.94),        # an older tile that kept some fired clay
              (0.66, 0.70, 0.78),        # dark wet slate
              (0.98, 0.94, 0.86)]        # sun-bleached
assert len(WALL_TINTS) == len(ROOF_TINTS)   # one family index indexes BOTH lists
NFAM = len(WALL_TINTS)
# The five roof families are chosen so their PER-CHANNEL MEAN (0.912/0.906/0.896) is
# within a percent of the three they replace (0.913/0.900/0.897).  That is not
# tidiness: ROOF_HEX above was solved from the eff-albedo measured on the shipped
# bundle, and that measurement already had the old families averaged into it.  Move
# the family mean and the palette solve silently stops meaning what it says.
# TRODDEN EARTH IS DARKER THAN THE GRASS IT REPLACED, and the first version of the
# bedding ring was not: f2's DIRT is 9c8a70, a pale warm grey, and under a 2.4x
# golden key it arrived as CREAM — every house sat in a bright halo, which is the
# decal read the ring exists to prevent.  Worn ground is compacted and shaded; it
# has to be the darkest thing at the base or it draws a second silhouette line.
BED_TINT = (0.60, 0.46, 0.33)
TUFT_TINT = (0.86, 0.94, 0.72)           # the blades that overlap the plinth


def tint_layer(p):
    """The per-house family index layer on a B.Prop under construction."""
    return p.bm.faces.layers.float.get(HTINT) or p.bm.faces.layers.float.new(HTINT)


# WHICH WAY A ROOF POINTS (2026-08-04).  The blind critic: "every roof is the same
# value regardless of which way it points."  It is not a light bug — the key really
# does reach both slopes of a 34-degree-sun gable at similar cosines, and at a 40 m
# boom the two planes differ by a few percent of luminance, which is nothing beside
# their shared albedo.  The reference frames get their roof read from PAINT: the away
# plane is simply drawn darker.  So the SLOPE FACING AWAY FROM THE SUN takes 20% off
# its COLOR_0 and the facing one is left alone.  Baked into vertex colour on purpose:
# it is a stylisation, it survives every camera and every grade, and it costs nothing.
# The sun is the towns' own ratified rig, (56, 0, 212) in Blender euler — never a
# second copy of the number, and never a different sun than the one that shades it.
_SUNRX, _SUNRZ = math.radians(56.0), math.radians(212.0)
SUN_BL = (math.sin(_SUNRX) * math.sin(_SUNRZ),
          -math.sin(_SUNRX) * math.cos(_SUNRZ),
          math.cos(_SUNRX))
ROOF_AWAY = 0.80          # 20% off the away-facing plane


# =============================================================================
# R14 — THE FOLIAGE CLUMPS FLOATED
# =============================================================================
# The fourteenth blind critic: "the dark foliage clumps at upper right sit on the
# pale hill with zero contact shadow, floating."  They did.  The masses are lit by
# the same key as everything else and the runtime casts no shadow they can catch at
# region scale, so the only thing that ever said "this touches the ground" was the
# silhouette crossing it.
#
# TWO HALVES, AND THE SECOND IS THE ONE THAT DOES THE WORK.  A mass whose own base
# darkens still floats if the ground under it stays lit — that is the same lesson
# BED_TINT paid for on the houses (a house in a BRIGHT ring reads as a decal).  So:
#
#   1. the clump's own COLOR_0 ramps down toward its base, over a distance scaled
#      to the clump (a 12 m tree and a 4 m bush do not share a contact height);
#   2. the GROUND's COLOR_0 takes a soft ring wherever a mass stands over it,
#      derived from the masses' OWN vertices — no site list, no radius guess, and
#      it cannot drift out of step with the geometry because it IS the geometry.
#
# VERTEX COLOUR ONLY.  Nothing here adds a triangle, a material or an object, so
# ground detail cannot become collision: the runtime's veg_ rule and the collide /
# walkRef sets are untouched by construction, and walk_engine_gate proves it in the
# ENGINE rather than in the file.
#
# veg_land_* IS EXCLUDED ON PURPOSE.  L2's tuft and flower layers are 0.13-0.25 m
# blades whose ENTIRE height sits inside any plausible contact ramp — feeding them
# to this would not shade a contact, it would repaint the meadow two stops down.
# The gate is a real vertical extent (> 2.0 u above the ground beneath it).
CONTACT_BASE = 0.44       # COLOR_0 factor at the very bottom of a mass
CONTACT_GROUND = 0.46     # deepest ground darkening under full canopy cover
CONTACT_CELL = 0.7        # u, the footprint lattice
CONTACT_BLUR = 2          # cells; the ring's softness


def _loop_vert(me):
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    return lv


def _co(me):
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def _scale_color(me, per_vert):
    """Multiply COLOR_0 by a PER-VERTEX factor, on either colour domain.

    The prop accumulator writes CORNER colours and bushlang writes POINT ones, and
    a corner-shaped index into a point-domain buffer does not raise a wrong answer,
    it raises a broadcast error only because the counts happen to differ — on a mesh
    where they did NOT, this would have silently shaded the wrong vertices."""
    ca = me.color_attributes.get("Col")
    if ca is None:
        return False
    d = np.zeros(len(ca.data) * 4)
    ca.data.foreach_get("color", d)
    d = d.reshape(-1, 4)
    idx = (np.arange(len(me.vertices)) if ca.domain == "POINT" else _loop_vert(me))
    if len(idx) != len(d):
        return False
    d[:, :3] = np.clip(d[:, :3] * per_vert[idx][:, None], 0.0, 1.0)
    ca.data.foreach_set("color", d.ravel())
    return True


def canopy_contact(made, F, zg, fr):
    """Bed the vegetation masses into the ground in COLOR_0.  Returns stats."""
    masses, foot, seen = [], [], set()
    # THE DICT KEY IS NOT THE OBJECT NAME.  The bush masses live in `made` under
    # `canopy_0..n` while the OBJECT is `veg_canopy_<stand>` — the runtime's veg_
    # contract is on the object, so that is what this reads.  Keying on the dict
    # would have silently skipped every stand in the region and reported success.
    for ob in list(made.values()):
        if getattr(ob, "type", None) != "MESH" or ob.name in seen:
            continue
        seen.add(ob.name)
        if not ob.name.startswith("veg_"):
            continue
        # L2's BUSH CLUMPS ARE THE ONES THE CRITIC WAS LOOKING AT.  Measured on the
        # first r14 plate: the masses that read as floating on the pale hill are the
        # 0.4 m clump layer, not the stands, and the first cut of this pass excluded
        # every veg_land_* object by name.  Tufts and flowers stay out — their whole
        # height is inside any contact ramp, so a ramp would repaint the meadow —
        # but a clump has a base, and a per-object height test cannot find it: the
        # layer is ONE merged mesh spanning the region, so its 95th percentile
        # height is a bush, not a canopy.  The clumps get their own short ramp and
        # stay out of the ground footprint (a 0.4 m bush has no ring to cast).
        small = ob.name == "veg_land_clumps"
        if ob.name.startswith("veg_land_") and not small:
            continue
        me = ob.data
        if not len(me.vertices) or me.color_attributes.get("Col") is None:
            continue
        co = _co(me)
        h = co[:, 2] - ghv(F, zg, fr, co[:, 0], co[:, 1])
        top = float(np.percentile(h, 95))
        if not small and top <= 2.0:
            continue
        ramp = 0.42 if small else float(np.clip(0.30 * top, 0.6, 2.4))
        base = 0.52 if small else CONTACT_BASE
        f = base + (1.0 - base) * np.clip(h / ramp, 0.0, 1.0)
        if _scale_color(me, f):
            masses.append((ob.name, len(me.vertices), round(ramp, 2)))
            if not small:
                foot.append(co[:, :2])
    if not foot:
        return dict(masses=0)

    g = made.get("ground")
    ring = 0
    if g is not None and g.data.color_attributes.get("Col") is not None:
        P = np.concatenate(foot)
        gco = _co(g.data)
        x0, y0 = gco[:, 0].min(), gco[:, 1].min()
        nx = int((gco[:, 0].max() - x0) / CONTACT_CELL) + 3
        ny = int((gco[:, 1].max() - y0) / CONTACT_CELL) + 3
        occ = np.zeros((nx, ny), np.float32)
        ix = np.clip(((P[:, 0] - x0) / CONTACT_CELL).astype(int), 0, nx - 1)
        iy = np.clip(((P[:, 1] - y0) / CONTACT_CELL).astype(int), 0, ny - 1)
        occ[ix, iy] = 1.0
        k = CONTACT_BLUR
        sm = np.zeros_like(occ)
        for dx in range(-k, k + 1):
            for dy in range(-k, k + 1):
                sm += np.roll(np.roll(occ, dx, 0), dy, 1)
        sm /= (2 * k + 1) ** 2
        sm = np.clip(sm * 2.6, 0.0, 1.0)      # a ring, not a wash
        gx = np.clip(((gco[:, 0] - x0) / CONTACT_CELL).astype(int), 0, nx - 1)
        gy = np.clip(((gco[:, 1] - y0) / CONTACT_CELL).astype(int), 0, ny - 1)
        v = sm[gx, gy]
        _scale_color(g.data, 1.0 - CONTACT_GROUND * v)
        ring = int((v > 0.02).sum())
    print("  contact shadow: %d masses bedded, %d ground verts in a ring"
          % (len(masses), ring))
    return dict(masses=len(masses), ground_verts=ring,
                base=CONTACT_BASE, ground_dark=CONTACT_GROUND)


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
             ROOF_TINTS[(k - 1) % len(ROOF_TINTS)] if c == ROOF else
             BED_TINT if c == DIRT else
             TUFT_TINT if c == GRASS_HI else None)
        seen.add(k)
        if m is None:
            continue
        if c == ROOF:
            n = poly.normal
            dot = n[0] * SUN_BL[0] + n[1] * SUN_BL[1] + n[2] * SUN_BL[2]
            # a soft ramp, not a step: the ridge cap and the eave board sit near
            # dot 0 and a hard threshold would make a black line out of them.
            t = min(1.0, max(0.0, (dot + 0.05) / 0.35))
            m = tuple(mm * (ROOF_AWAY + (1.0 - ROOF_AWAY) * t) for mm in m)
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
# The corner-height spread a station may have and still carry a house (2026-08-04).
# The exposed stone under a house is 0.70 x this + 0.20u, so 0.85 caps it at 0.80u —
# a footing.  r9's worst station spanned ~1.3u and produced a 1.5u block of stone
# that a blind critic read as a detached slab.  It is a PREFERENCE, not a veto: the
# search falls back to the old road/neighbour-only test rather than lose a house.
HOUSE_SLOPE_CAP = 0.85


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


def bed_in(p, ht, fam, F, zg, fr, px, py, w, d, yaw, rng):
    """A RING OF TRODDEN EARTH round a house, plus tufts that overlap its plinth.

    The critic's phrase for this is "the cheapest conversion of 'model' into
    'building' available", and it is: a building placed on a surface has WORN the
    surface, so the grass stops a foot short of the wall and a few blades grow
    against the stone.  Without it every base is one hard silhouette line between
    two flat colours, which is what reads as "resting on the terrain" instead of
    "bedded into it" — a real building has no such line anywhere.

    Ground-hugging (+0.02) and follows `gh`, so it never becomes a step: it is a
    floor 2 cm above the floor, not an obstacle, and it inherits the emberbrook
    prop's own class gains and COLOR_0 rather than needing a material of its own.
    """
    before = set(p.bm.faces)
    r0 = max(w, d) * 0.56
    r1 = r0 + 0.42 + rng.uniform(0.0, 0.30)
    ph = rng.uniform(0, 6.283)
    inner, outer = [], []
    for i in range(25):
        a = 2 * math.pi * i / 24
        ca, sa = math.cos(a), math.sin(a)
        # the outer edge WANDERS: a perfect annulus reads as a decal, and a decal
        # under a building is the artefact this exists to avoid, not the fix.
        j = 1.0 + 0.17 * math.sin(3 * a + ph) + 0.09 * math.sin(5 * a + ph * 2)
        xi, yi = px + ca * r0, py + sa * r0
        xo, yo = px + ca * r1 * j, py + sa * r1 * j
        inner.append((xi, yi, gh(F, zg, fr, xi, yi) + 0.02))
        outer.append((xo, yo, gh(F, zg, fr, xo, yo) + 0.02))
    p.strip(DIRT, outer, inner)
    # ...and the tufts that break the base line. They straddle the plinth edge on
    # purpose — a tuft that stops at the stone draws the line again.
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        rr = r0 * rng.uniform(0.86, 1.02)
        tx, ty = px + math.cos(a) * rr, py + math.sin(a) * rr
        tz = gh(F, zg, fr, tx, ty)
        hgt = 0.16 + rng.uniform(0, 0.14)
        p.cone(GRASS_HI, (tx, ty, tz + hgt / 2), 0.075 + rng.uniform(0, 0.05),
               0.0, hgt, seg=4, rz=a)
    for f in p.bm.faces:                 # so apply_house_tints can grade the ring
        if f not in before:
            f[ht] = float(fam)


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

    # A PLINTH IS A PLINTH, NOT A PODIUM (2026-08-04).  This used to be ONE box
    # spanning `fl` down to `min(ch) - 0.40`, which is correct on flat ground and a
    # monolith on a slope: where the four corners spread 1.2u the stone grew to wall
    # height and stood proud as a slab as big as the house it carried.  A blind critic
    # read exactly that box as "a detached slab hanging in mid-air with a visible
    # underside face" — and it is NOT detached (measured: SIM.pick at the named pixels
    # puts the ground BEHIND the stone, its underside 0.4-0.6u below the terrain, and a
    # 4 px-step scan of all four landscape frames finds no downward-facing first hit on
    # any building at all).  The misread is the finding: an unbedded stone box that tall
    # stops reading as a footing.  So the PROUD course is a constant 0.42u whatever the
    # slope does, and the part that reaches down to the low corner is INSET, which
    # draws its own shadow line under the plinth instead of continuing the wall.
    # ...and the floor stops chasing the HIGH corner. `max(ch) + 0.20` puts the whole
    # slope into the exposed stone; 0.70 of the way up puts most of it there and beds
    # the uphill side INTO the ground, which is the ask ("bedded into it, not resting
    # on it") answered by the same line. It is 0.70 and not 0.50 because a door sits
    # at fl + 0.54: at 0.50 the uphill terrain would climb over the threshold on the
    # steepest station this town still allows.
    low = min(ch) - 0.40
    fl = min(ch) + 0.70 * (max(ch) - min(ch)) + 0.20
    plinth = 0.42
    p.cube(STONE, at(0, 0, fl - plinth / 2), (w * 1.07, d * 1.07, plinth), rz=yaw)
    sk = (fl - plinth) - low
    if sk > 0.03:
        p.cube(STONE, at(0, 0, low + sk / 2), (w * 0.92, d * 0.92, sk), rz=yaw)
    p.cube(WALL, at(0, 0, fl + eh / 2), (w, d, eh), rz=yaw)
    # the eave board: the dark line every real building has where its roof meets its
    # wall, and the cheapest thing in this file that stops a wall reading as a decal.
    p.cube(WOOD, at(0, 0, fl + eh + 0.05), (w * 1.31, d * 1.18, 0.13), rz=yaw)
    p.prism(ROOF, at(0, 0, fl + eh + 0.11), w * 1.26, d * 1.14,
            max(0.9, rh - eh - 0.11), rz=yaw)
    # ================================================================ CHIMNEY
    # R13 — THREE ROUNDS OF PATCHES, SO THE MASSING IS WHAT IS WRONG.  R11 attached
    # the stack to the wall face and collared it at the eave; R12 found the collar
    # was a metre low (u = 0 is the roof prism's RIDGE, not its eave) and narrowed
    # the shaft.  Both were real fixes and the thirteenth blind critic still read
    # the object as "SEPARATE OBJECTS LEANED AGAINST THE HOUSES ... background grass
    # visible in the gap at its base ... a flat cap in mid-air beside the roofline
    # ... the column's base sits on bare grass while the house sits on a pale gravel
    # pad".  Every clause of that is arithmetic, and here it is:
    #
    #   THE STACK OVERHUNG THE PAD ON EVERY HOUSE IN BOTH TOWNS.  It stood proud of
    #   the gable wall face by `cd - 0.14` = 0.20u.  The plinth it is supposed to
    #   stand on is `d * 1.07`, i.e. it reaches only `0.035 d` past that same wall
    #   face — 0.046u at d = 1.30 and 0.094u at d = 2.68.  So 0.11-0.15u of the
    #   stack's depth hung over open ground, and its base at `fl - 0.30` sat ABOVE
    #   that ground: a free-standing foot with daylight under and behind it.  "The
    #   column isn't on the pad" is literally, measurably true, on all fourteen.
    #   THE THIRD FRACTION-OF-A-JITTERED-DIMENSION CONTACT IN THIS FILE after R11's
    #   stack and R12's window pane — and this time it is retired by construction
    #   rather than by a better fraction: no dimension of the stack is a fraction
    #   of `d` any more, and the three clauses below are GATED per house, not
    #   asserted (see CHIM_GATE; a house that fails any of them LOSES ITS CHIMNEY,
    #   which is the authorised outcome — a missing chimney is invisible, a
    #   detached one is the first thing the eye finds).
    #
    #   (i)   FOOTPRINT INSIDE THE PAD.  |cv| + cd/2 = d*0.5 - CIN, inside both the
    #         plinth's d*0.535 and the trodden ring's max(w,d)*0.56.
    #   (ii)  OUTER FACE BEHIND THE WALL FACE by CIN.  Below the eave the stack is
    #         inside the wall solid, so THERE IS NO GAP TO SEE BACKGROUND THROUGH.
    #   (iii) THE CAP CLEARS THE RIDGE, always, by CUP at least.  A chimney that
    #         breaks the ridgeline reads as a chimney; one that stops beside the
    #         eave reads as a post, which is what "a flat cap in mid-air beside the
    #         roofline" is describing.
    #
    # WHAT THIS COSTS, deliberately: the stack is no longer a full-height column
    # with its own visible face below the roof.  What the near-top-down camera gets
    # is the stone standing ABOVE the roof at the gable end of the ridge, growing
    # out of the roof mass rather than leaning on the wall.  R11's argument for the
    # tall column (a 34-degree sun draws a tall narrow object best) produced three
    # rounds of "leaning menhir"; a short stack that is unambiguously part of the
    # building beats a tall one that is unambiguously not.
    gs = 1.0 if rng.random() < 0.5 else -1.0        # which gable end carries it
    CIN, CUP = 0.03, 0.55            # recess behind the wall face; clearance over the ridge
    cw = 0.30 + 0.09 * s                            # across the ridge
    cd = 0.38                                       # along the ridge (roughly square in plan)
    cv = gs * (d * 0.5 - CIN - cd * 0.5)
    zr = fl + max(rh, eh + 1.01)                    # the roof prism's apex, i.e. the ridge
    cz0 = fl - plinth                               # buried in the plinth: no free base exists
    cz1 = zr + CUP + rng.uniform(0.0, 0.28)
    pad_u, pad_v = w * 0.535, d * 0.535             # the plinth's own half-extents
    g_i = (cw * 0.5 <= pad_u + 1e-9) and (abs(cv) + cd * 0.5 <= pad_v + 1e-9)
    g_ii = (abs(cv) + cd * 0.5) <= d * 0.5 + 1e-9
    g_iii = cz1 >= zr + CUP - 1e-9
    CHIM_GATE.append((g_i, g_ii, g_iii,
                      round(pad_v - (abs(cv) + cd * 0.5), 3),      # pad margin
                      round(d * 0.5 - (abs(cv) + cd * 0.5), 3),    # recess behind the wall
                      round(cz1 - zr, 3)))                         # clearance over the ridge
    if g_i and g_ii and g_iii:
        p.cube(STONE, at(0, cv, (cz0 + cz1) / 2), (cw, cd, cz1 - cz0), rz=yaw)
        # A COLLAR IS A JOINT, NOT A SHELF (R12, paid for by looking): the first R12
        # pass put 1.44x plates on a narrow shaft high in the frame and the stack
        # became a totem of hovering slabs.  Two tight ones only — the flashing where
        # the shaft leaves the roof at the ridge, and the cap.  The eave collar is
        # GONE: at this massing that height is inside the wall solid, so it was a
        # slab hidden in a box.
        p.cube(STONE, at(0, cv, zr + 0.03), (cw * 1.14, cd * 1.14, 0.13), rz=yaw)
        p.cube(STONE, at(0, cv, cz1 + 0.055), (cw * 1.22, cd * 1.20, 0.13), rz=yaw)
    # DOOR + two windows on the face the yaw points at.  The door is the scale cue;
    # the gable window is what says "there is an upstairs", which is most of the
    # difference between a tall box and a house.
    p.cube(WOOD, at(w / 2 + 0.02, d * 0.17, fl + 0.54), (0.11, 0.42, 1.08), rz=yaw)
    # R12 — A WINDOW IS AN OPENING, NOT A DECAL.  "Flat unlit orange rectangles with
    # no frame, no glass, no recess — they read as stickers on a wall" (twelfth blind
    # critic, its own runner-up for this frame and named cheap).  Two things were
    # wrong and only one of them is art direction:
    #
    #   1. THE GABLE WINDOW WAS LITERALLY DETACHED, and it is the chimney's own
    #      arithmetic from R11 recurring in the line directly below it.  Its centre
    #      was `-gs * d * 0.60` with a 0.09 thickness, so its INNER face sat at
    #      0.555d against a gable wall face at 0.50d: floating 0.07-0.15 u off the
    #      house on every station where d > 1.7, and house_dims() draws d in
    #      1.30..2.68.  Measured from the wall face, like the stack.  AN OFFSET THAT
    #      IS A FRACTION OF A JITTERED DIMENSION IS A CONTACT THAT IS A COIN TOSS —
    #      the rule was written down in R11 and the neighbouring line still broke it.
    #   2. A pane flush with a wall cannot read as an opening at any distance,
    #      because nothing in it casts.  There is no boolean here to cut a reveal
    #      with, so the recess is built the way a joiner builds it: the pane sits AT
    #      the wall plane and a SILL, a LINTEL, two JAMBS and a glazing bar stand
    #      PROUD of it.  Under a 34 deg key the proud frame throws a real shadow
    #      across the glass, which is the recess — geometry, so it survives every
    #      camera and every grade.  Five cubes a window, no new material.
    def window(u, v, z, ww, wh, nrm):
        """A framed pane.  `nrm` is 'u' or 'v': which local axis the wall faces."""
        fp, th = 0.075, 0.05                 # frame proud of the wall, bar thickness
        if nrm == 'u':
            s = 1.0 if u > 0 else -1.0
            p.cube(EMIT, at(u + s * 0.015, v, z), (0.05, ww, wh), rz=yaw)
            p.cube(WOOD, at(u + s * fp * 0.62, v, z - wh / 2 - 0.05),
                   (fp * 1.7, ww + 0.20, 0.09), rz=yaw)          # sill
            p.cube(WOOD, at(u + s * fp * 0.50, v, z + wh / 2 + 0.045),
                   (fp * 1.4, ww + 0.15, 0.08), rz=yaw)          # lintel
            for sv in (-1.0, 1.0):
                p.cube(WOOD, at(u + s * fp * 0.45, v + sv * (ww / 2 + 0.04), z),
                       (fp * 1.3, 0.08, wh + 0.16), rz=yaw)      # jambs
            p.cube(WOOD, at(u + s * fp * 0.30, v, z), (fp, th, wh), rz=yaw)
        else:
            s = 1.0 if v > 0 else -1.0
            p.cube(EMIT, at(u, v + s * 0.015, z), (ww, 0.05, wh), rz=yaw)
            p.cube(WOOD, at(u, v + s * fp * 0.62, z - wh / 2 - 0.05),
                   (ww + 0.20, fp * 1.7, 0.09), rz=yaw)
            p.cube(WOOD, at(u, v + s * fp * 0.50, z + wh / 2 + 0.045),
                   (ww + 0.15, fp * 1.4, 0.08), rz=yaw)
            for su in (-1.0, 1.0):
                p.cube(WOOD, at(u + su * (ww / 2 + 0.04), v + s * fp * 0.45, z),
                       (0.08, fp * 1.3, wh + 0.16), rz=yaw)

            p.cube(WOOD, at(u, v + s * fp * 0.30, z), (th, fp, wh), rz=yaw)

    window(w / 2, -d * 0.22, fl + eh * 0.54, 0.36, 0.42, 'u')
    window(0.0, -gs * (d * 0.5 + 0.005), fl + eh + (rh - eh) * 0.30,
           0.30, 0.30, 'v')                        # the far gable from the stack
    if kind == 1:                       # the lean-to: a third of the town is not a box
        ww, wd, weh = w * 0.60, d * 0.74, eh * 0.50
        wu = -(w / 2 + ww / 2 - 0.07)
        p.cube(STONE, at(wu, d * 0.09, fl - plinth / 2), (ww * 1.08, wd * 1.08, plinth), rz=yaw)
        if sk > 0.03:
            p.cube(STONE, at(wu, d * 0.09, low + sk / 2), (ww * 0.93, wd * 0.93, sk), rz=yaw)
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
    house_slope = 0.0
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
        # A MASON DOES NOT BUILD ON A 40-DEGREE SLOPE, and the picture said so before
        # any gate did: the one station in r9 that a blind critic singled out ("its
        # stone plinth is a detached slab hanging in mid-air") was not detached at all
        # — measured, its underside sits 0.4-0.6u BELOW the terrain — it was a house
        # whose four footprint corners span ~1.3u, so the footing that has to reach the
        # low corner grew as tall as the wall above it and read as a separate block.
        # The station search now prefers ground the house can actually sit on, and only
        # falls back to the old road/neighbour-only test if nothing flat enough exists.
        placed = False
        for slope_cap in (HOUSE_SLOPE_CAP, 1e9):
            for dr in (0.0, 0.9, 1.8, 2.7, 3.6, 4.6):
                for da in (0.0, .13, -.13, .26, -.26, .40, -.40, .55, -.55, .72, -.72):
                    tx = cx + math.cos(a + da) * (r + dr)
                    ty = cy + math.sin(a + da) * (r + dr)
                    if float(F.road_dist(np.array([tx]), np.array([ty]))[0]) < need:
                        continue
                    if not all(math.hypot(tx - ox, ty - oy) >= 3.55 for ox, oy in ring):
                        continue
                    if slope_cap < 1e8:
                        # a NOMINAL footprint, not this house's own: house_dims()
                        # must keep its place in the rng stream or every later
                        # house's angle, size and yaw move and R9's ratified
                        # scatter is thrown away to answer a question about slope.
                        tc = house_ground(F, zg, fr, tx, ty, 2.35, 2.05, 0.0)
                        if max(tc) - min(tc) > slope_cap:
                            continue
                    hx, hy = tx, ty
                    placed = True
                    break
                if placed:
                    break
            if placed:
                break
        road_clear = min(road_clear,
                         float(F.road_dist(np.array([hx]), np.array([hy]))[0]))
        fa = a + math.pi + rng.uniform(-0.30, 0.30)          # mostly face the green
        if i % 4 == 1:                                        # ...but not all of them
            fa += (1.0 if rng.random() < 0.5 else -1.0) * rng.uniform(0.75, 1.25)
        dims = house_dims(rng)
        # NFAM families, walked by a stride coprime with it so neighbours in the
        # PLACEMENT order rarely draw the same one: 1,4,2,5,3,2,5,3,1,4,...
        fam = 1 + (i * 3 + i // NFAM) % NFAM
        ch = house_ground(F, zg, fr, hx, hy, dims[1], dims[2], fa)
        # ITS OWN STREAM, deliberately: drawing from `rng` here would re-scatter the
        # whole town (every later house's angle, radius and dims move), and R9's
        # placement is ratified art. Bedding must be able to land without moving it.
        bed_in(p, ht, fam, F, zg, fr, hx, hy, dims[1], dims[2], fa,
               random.Random(20260804 + i))
        impression_house(p, ht, fam, hx, hy, fa, dims, ch, rng)
        ring.append((hx, hy))
        house_slope = max(house_slope, max(ch) - min(ch))
    # ---- the Heartlight: plinth + a standing light, the town's whole identity ----
    for i in range(8):
        a = i * (2 * math.pi / 8)
        p.cube(STONE, (cx + math.cos(a) * 0.62, cy + math.sin(a) * 0.62, h0 + 0.16),
               (0.34, 0.28, 0.32), rz=a)
    p.cone(STONE, (cx, cy, h0 + 0.62), 0.34, 0.24, 1.0, seg=8)
    # R12 — SMALL AND DIM RATHER THAN LARGE AND SMOOTH (user ruling, given after the
    # twelfth blind critic filed this object under MISSING MATERIAL with no prompting
    # and no knowledge of its history: "untextured with a single specular hotspot;
    # whatever it's meant to be, it is currently a beach ball").  Two rounds of
    # sweeping what the sphere is made of have each made it worse, and the ruling is
    # that a restrained version beats a conspicuous wrong one.
    # A 0.44 u emissive ball 1.34 u up on a bare plinth has nothing in it that says
    # LAMP; what says lamp is a HOOD, RIBS and the light being smaller than the thing
    # holding it.  Radius 0.44 -> 0.26, three stone ribs standing just clear of the
    # glass, a flared hood over it and a finial: all four are existing materials and
    # existing primitives, and together they read at the ~40 px this object occupies
    # in the meadow frame where a smooth sphere read as a balloon at ~75 px.
    # THE CENTRE DOES NOT MOVE.  play3d.html hard-codes the Heartlight's PointLight
    # and its covering sphere at floor + 1.34; changing the height here would
    # silently separate the orb from its own light (LOOP.md R9 wrote that trap down).
    p.ico(EMIT, (cx, cy, h0 + 1.34), (0.22, 0.22, 0.26), subd=2)
    for i in range(3):
        a = 0.4 + i * (2 * math.pi / 3)
        p.cube(STONE, (cx + math.cos(a) * 0.235, cy + math.sin(a) * 0.235, h0 + 1.34),
               (0.042, 0.042, 0.60), rz=a)
    p.cone(STONE, (cx, cy, h0 + 1.735), 0.30, 0.06, 0.17, seg=8)
    p.cube(STONE, (cx, cy, h0 + 1.88), (0.07, 0.07, 0.12))
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
    # ...and its twin: the WORST corner-height spread any house ended up on. It is
    # what turns a footing into a podium (the exposed stone is 0.70 x this + 0.20u),
    # and like the road number it is invisible to every instrument in this repo and
    # obvious in one screenshot.
    STATS["emberbrook_house_slope_u"] = round(house_slope, 2)
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


def _strut(p, cls_, a, b, th):
    """ONE member between two world points, out of a cube that can only Z-then-X.

    Prop.cube applies Matrix.Rotation(rz,'Z') @ Matrix.Rotation(rx,'X'), so a box
    long in local Z points along (sin rz sin rx, -cos rz sin rx, cos rx).  Solving
    that for an arbitrary direction gives rz = bearing + pi/2 and rx = atan2(run,
    rise) — which is the whole reason this helper exists: without it every diagonal
    in the scaffold has to be hand-derived, and a diagonal derived by hand is the
    quarter-turn bug build_old_gate paid a day for.
    """
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    run = math.hypot(dx, dy)
    L = math.hypot(run, dz)
    if L < 1e-4:
        return
    p.cube(cls_, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2),
           (th, th, L), rz=math.atan2(dx, -dy), rx=math.atan2(run, dz))


# =============================================================================
# DELLHOLLOW'S OWN VOCABULARY — A STILT BAY, NOT A COTTAGE (2026-08-04)
# =============================================================================
# THE USER, ON THE SHIPPED VISTA: "the overworld vista of Dellhollow is a cluster of
# gabled cottages.  Dellhollow is not a cottage town" — and then, sharpening it:
# "dellhollow should have an entirely distinct look VS emberbrook."  They are right
# and the old code says why in one line: it called `impression_house()`, which is
# EMBERBROOK'S building, so the two towns were drawn from one asset set and differed
# only in where they stood.  t1-gorge.png and t1-closeup.png are the receipt — ochre
# plaster walls under blue slate gables in both frames.
#
# The canon (user memory "Dellhollow architecture", public/townmap/dellhollow.map.json,
# public/assets/refs/dellhollow-master-*.png): a STONE DAM/LOCKS SPINE with a village
# of RICKETY WOODEN SCAFFOLD LAYERS clinging to the gorge wall.  The map names its own
# shapes — "Stilt Cluster", "Weave huts / laundry lines, rickety balconies", "Drying
# decks", shops "cantilevered out over the gorge".  Master ref 6b is the picture: a
# cross-braced timber lattice, decks stacked with air between them, stair flights
# zig-zagging down, small sheds on top, dark wet masonry behind.
#
# SO THE BAY IS DIFFERENTIATED ON ALL THREE AXES A GLANCE READS, deliberately:
#   SILHOUETTE  Emberbrook is freestanding gabled masses on open ground; a bay is a
#               HORIZONTAL deck on VERTICAL stilts, nothing freestanding, and its
#               roofs are SINGLE-PITCH lean-tos.  No prism() is called in this town.
#   MATERIAL    Emberbrook is plaster (WALL) + tile (ROOF).  A bay uses none of
#               either: WOOD (weathered planks), TAR (dark planks), ROPE, STONE.
#               After this change the dellhollow object contains ZERO WALL and ZERO
#               ROOF faces — which is a countable claim, not a taste one, and
#               STATS carries it as dellhollow_plaster_faces / _tile_faces.
#   PALETTE     no terracotta and no slate anywhere in it; the timber is the f2
#               plank browns and the value contrast is carried by WOOD against TAR.
#
# IT IS AN IMPRESSION AT 40 m.  Big honest shapes only: the deck line, the leg
# lattice, the X-brace, the rail, the lean-to.  Treads, shingles and joinery are
# below a pixel at the gorge camera and would only alias.
DH_DECK_W = (4.4, 5.9)     # along the river — bays nearly touch at 6 u spacing
DH_DECK_D = (2.5, 3.4)     # out from the wall
DH_LIFT = (1.7, 3.5)       # deck top above the HIGHEST ground under its footprint

# =============================================================================
# ROUND 2 — THE TOWN HAS TO REACH THE WATER (2026-08-04)
# =============================================================================
# THE USER, on the round-1 vista: "this looks way better now but it seems entirely
# disconnected from the actual dellhollow town model that we use for the playable
# town.  e.g. the town stretches down into the river below and has locks; the
# screenshot shows me the town climbing up the slope but not the water."
#
# Round 1 passed DISTINCTNESS and failed IDENTITY, and the ladder is why. It offset
# each tier LATERALLY from the channel centreline (`lat = hw + 2.4 + tier * 3.5`),
# which says nothing about height — so where the gorge wall is steep the lowest deck
# is already high. MEASURED on the shipped ladder, tier 0's deck top stood 4.94 to
# 11.12 u ABOVE the local waterline; the town genuinely began above the river and
# climbed away from it. The cross-gorge profile says where it should have begun: the
# waterline band sits at lat 4-6, which is INSIDE the channel half-width (5.9-7.9).
#
# SO THE LADDER IS SOLVED IN HEIGHT, NOT IN LATERAL OFFSET. Each tier names a height
# ABOVE THE LOCAL WATER and the lateral offset is SEARCHED for — the first offset at
# which the built ground reaches it. Three things fall out of that and all three are
# the identity the user is asking for:
#   * the tiers become TRUE CONTOURS of the gorge wall, so where the wall is steep
#     they stack vertically (the master ref's lattice of decks with air between) and
#     where it eases they spread — instead of a constant offset doing whichever of
#     those the terrain happened to make it do;
#   * tier 0 is BELOW the waterline by construction, so its stilts foot on the
#     riverbed and the deck stands OVER the shallows. The `gz < cwl + 0.35` guard
#     that used to refuse those stations refuses DROWNED ones, not waterline ones —
#     a deck on tall stilts over water is the entire point of stilts;
#   * every height is relative to the LOCAL water, and the water falls 7.4 u across
#     the town's own reach, so the whole town steps down WITH the river rather than
#     sitting on one bench. That is the cascade, and it is derived, not drawn.
DH_TIER_H = (-0.55, 2.2, 5.2, 8.2, 11.2)   # tier GROUND target, REL. TO LOCAL WATER
# AND THE DECK TOPS ARE ANCHORED TO THE WATER TOO — every tier, not just the wet one.
# Measured on the first round-2 build: with tiers 1-3 still taking `max(cor) + lift`,
# their deck tops came out at water +13 to +19, which is 4 to 7 u ABOVE the rim road
# the player walks in on (h 12.3-14.5). The town therefore photographed as a thing
# standing ON the rim rather than descending into the gorge — the user's original
# complaint surviving in the upper tiers after the lower one had been fixed. The
# cause is that on a wall this steep `max(cor)` is the uphill corner, metres above
# the contour the tier was placed on, so the lift compounded the slope.
# Each entry is ALSO the next tier's ground target, which is what a terraced hillside
# actually is: every tier's deck is level with the ground the tier above stands on.
#
# FIVE TIERS, WATER TO RIM — and the fifth was earned by a photograph, not a taste.
# At four tiers the town spanned water +2.2 to +11.4, which is CORRECT placement and
# yet it read as almost nothing from the standing gorge camera: the rim road there is
# only 8-12 u above the river, so a town that stops at rim height sits entirely
# BEHIND the near lip from 36 u away, and the establishing frame went empty. Round 1
# was visible from there only because it stood too high to be a river town at all.
# The resolution is not to lift the town back up — it is that a cascade town SPANS.
# The lower tiers are what reach the water and the upper two are what break the rim
# line and carry the silhouette at distance; taking either end away loses one of the
# two things the frame has to say at once.
DH_TIER_TOP = (2.2, 5.2, 8.2, 11.2, 14.2)  # tier DECK TOP, relative to local water
# How far INBOARD of its own contour a wet bay sits, as a fraction of deck depth.
# A bay centred exactly on the waterline contour puts half its footprint up the
# cliff, and on this wall the ground climbs ~2 u per lateral unit — so its uphill
# corner came out 7 u above its downhill one and dragged the whole deck up with it
# (measured: tier-0 tops of +3.06 to +7.22 above water, when the intent was +2.2).
# Shifted inboard, the footprint straddles the waterline the way a stilt house on a
# shore actually does: back against the bank, front out over the water.
DH_WET_IN = 0.32
# THE LOCK FLIGHT. `rise` is how far each weir holds its pool ABOVE the natural
# surface at its own sill — i.e. exactly the height of the drop over it, which is
# the thing a distant glance reads. 1.9 u is not a taste: the natural fall between
# consecutive weirs is 2.57 u and 2.11 u, so a hold of 1.9 makes each pool reach
# back very nearly to the weir above it and the three steps tile the reach.
DH_LOCK_RISE = 1.9
DH_POOL_MAX = 13.0                   # longest reach one weir is allowed to pond


def contour_lat(F, zg, fr, cpt, cnr, side, target, lo=0.8, hi=26.0, step=0.22):
    """First lateral offset from the channel centreline where the GROUND reaches
    `target`, or (None, None) if the wall never gets there inside `hi`.

    This is the whole round-2 ladder in one function. It marches OUT from the
    channel, so for a target below the waterline it stops inside the water (which
    is what puts a stilt bay in the shallows) and for a target above it stops on
    the wall. The march is over the BUILT ground (O3.height, crag treatment
    included) rather than the analytic field, because the crag treatment is what
    the player actually sees and a contour taken from the smooth field would sit
    off the rock it is supposed to be following.
    """
    lat = lo
    while lat <= hi:
        q = cpt + cnr * side * lat
        g = gh(F, zg, fr, float(q[0] - VM.CX), float(q[1] - VM.CY))
        if g >= target:
            return lat, g
        lat += step
    return None, None


def scaffold_bay(p, F, zg, fr, px, py, yaw, sgn, dims, pad, rng, lamp, top_z=None):
    """ONE timber bay: deck, stilts, cross-bracing, rail, and sometimes a lean-to.

    `sgn` is which way local +Y points over the gorge — SOLVED by the caller against
    the river normal rather than assumed, because `yaw` carries the anchor's own
    rotation and a bank flip, and a lean-to that pitches INTO the cliff is the
    silent half of the same quarter-turn class of bug.

    `pad` is the stone terrace top under this bay, or None.  Legs foot on the HIGHER
    of the terrace and the ground so a leg never grows through its own masonry.

    `top_z` anchors the walking surface to an ABSOLUTE height instead of to this
    bay's own highest footing — which is what a bay standing in the river needs,
    because there the interesting datum is the WATER and the footings can be metres
    of riverbed and bank apart. The clearance floor it is held against is the
    LOWEST footing, deliberately: a bay on this wall has its back corner up the
    cliff, and holding an over-water deck above its HIGHEST footing is what threw
    round 2's first pass up to +7.22 above the waterline it was aiming at +2.2.
    Clearing the lowest footing is the condition for there being a bay at all;
    clearing the highest would mean there is no such thing as a bay against a bank.
    """
    dw, dd, lift = dims
    ca, sa = math.cos(yaw), math.sin(yaw)

    def at(u, v, z):                    # local (along river, out over gorge, up)
        return (px + ca * u - sa * v, py + sa * u + ca * v, z)

    def foot(u, v):
        x, y, _ = at(u, v, 0.0)
        g = gh(F, zg, fr, x, y)
        return g if pad is None else max(g, pad)

    cor = [foot(u * dw * 0.5, v * dd * 0.5) for u in (-1, 1) for v in (-1, 1)]
    top = (max(cor) + lift if top_z is None
           else max(float(top_z), min(cor) + 1.5))   # the walking surface

    # ---- THE STILTS. The outer row is the tall one: the ground falls away under
    # the cantilever, and that fall IS the read the map's "cantilevered out over the
    # gorge" is asking for.
    us = [-0.42 * dw, 0.0, 0.42 * dw]
    vs = [-sgn * 0.40 * dd, sgn * 0.40 * dd]
    legz = {}
    for u in us:
        for v in vs:
            g = foot(u, v)
            legz[(u, v)] = g
            h = max(0.5, top - 0.30 - g)
            p.cube(WOOD, at(u, v, g + h / 2 - 0.20), (0.26, 0.26, h + 0.40), rz=yaw)
    # ---- THE CROSS-BRACING, on the OUTER face only. This is the single element a
    # glance reads as "scaffold" rather than "building on posts", so it is worth its
    # triangles; the inner face is against the cliff and nobody ever sees it.
    ov = sgn * 0.40 * dd
    for k in range(len(us) - 1):
        u0, u1 = us[k], us[k + 1]
        z0, z1 = legz[(u0, ov)], legz[(u1, ov)]
        hi = top - 0.42
        if hi - max(z0, z1) < 1.0:      # too short to brace; a brace there is noise
            continue
        _strut(p, WOOD, at(u0, ov, z0 + 0.15), at(u1, ov, hi), 0.17)
        _strut(p, WOOD, at(u1, ov, z1 + 0.15), at(u0, ov, hi), 0.17)
        # the horizontal tie the braces cross at — it is what stops the X reading
        # as two unrelated sticks at distance
        zm = (max(z0, z1) + hi) / 2
        p.cube(WOOD, at((u0 + u1) / 2, ov, zm), (abs(u1 - u0) * 1.02, 0.15, 0.15), rz=yaw)
    # ---- THE DECK, and the DARK BAND under it. The fascia beam is the strong
    # horizontal line in the silhouette and it is TAR on purpose: a deck whose
    # underside is the same value as its top has no thickness at 40 m.
    p.cube(WOOD, at(0, 0, top - 0.11), (dw, dd, 0.22), rz=yaw)
    for u in (-0.34 * dw, 0.0, 0.34 * dw):
        p.cube(TAR, at(u, 0, top - 0.38), (0.24, dd * 1.04, 0.32), rz=yaw)
    p.cube(TAR, at(0, ov * 1.06, top - 0.36), (dw * 1.04, 0.26, 0.36), rz=yaw)
    # ---- THE RAIL. Rickety: a top rail, a slack rope below it, and posts that do
    # not quite line up.
    rv = sgn * dd * 0.46
    for k in range(5):
        u = (k / 4.0 - 0.5) * dw * 0.90 + rng.uniform(-0.10, 0.10)
        p.cube(WOOD, at(u, rv, top + 0.44), (0.11, 0.11, 0.88), rz=yaw)
    p.cube(WOOD, at(0, rv, top + 0.82), (dw * 0.94, 0.10, 0.11), rz=yaw)
    p.cube(ROPE, at(0, rv, top + 0.46), (dw * 0.94, 0.07, 0.07), rz=yaw)
    # ---- THE LEAN-TO. A SINGLE PITCH, high at the cliff and low over the water —
    # never prism(), which is the gable that started this.
    if rng.random() < 0.72:
        sw = dw * rng.uniform(0.42, 0.60)
        sd = dd * rng.uniform(0.54, 0.70)
        sh = rng.uniform(1.9, 2.7)
        su = rng.uniform(-0.18, 0.18) * dw
        sv = -sgn * dd * 0.10
        # THE SHED'S VALUE BREAK IS THE EAVE LINE, NOT A DARK MATERIAL (2026-08-04,
        # two builds photographed at the gorge camera). Walls WOOD under a TAR roof
        # made every shed a black LID; the swap made every shed a black BODY. Both
        # are the same mistake — this cliff faces away from the ratified sun, so
        # ANY tar-class plane here lands near black and a near-black mass is a hole
        # in the silhouette, not a shadow. So both are WOOD and the separation is
        # geometric: the roof is a TOP plane and catches what light there is, and a
        # TAR fascia under its overhang draws the dark line the eye reads as depth.
        # That line costs one box and cannot go black-on-black, because it is only
        # ever seen against the lit plane above it.
        p.cube(WOOD, at(su, sv, top + sh / 2), (sw, sd, sh), rz=yaw)
        p.cube(TAR, at(su, sv - sgn * sd * 0.62, top + sh + 0.06), (sw * 1.14, 0.14, 0.30),
               rz=yaw)
        p.cube(WOOD, at(su, sv, top + sh + 0.24), (sw * 1.18, sd * 1.34, 0.15),
               rz=yaw, rx=-0.30 * sgn)
        if lamp:                        # the hearth read, kept from the cottages
            p.cube(EMIT, at(su + sw * 0.52, sv, top + sh * 0.62),
                   (0.06, 0.34, 0.42), rz=yaw)
    if lamp:
        p.cube(EMIT, at(dw * rng.uniform(-0.34, 0.34), rv, top + 0.90),
               (0.15, 0.15, 0.18), rz=yaw)
    # ---- THE STAIR that says the tiers are joined. One flight raking down over the
    # gorge edge; the map's own "Deep Stairs" and the ref's zig-zags in one plank.
    if rng.random() < 0.55:
        su = rng.choice((-0.40, 0.40)) * dw
        run = dd * rng.uniform(0.7, 1.1)
        drop = rng.uniform(1.4, 2.4)
        a0 = at(su, sgn * dd * 0.48, top - 0.10)
        a1 = at(su, sgn * (dd * 0.48 + run), top - 0.10 - drop)
        p.cube(WOOD, ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2, (a0[2] + a1[2]) / 2),
               (0.62, 0.16, math.hypot(run, drop)), rz=yaw,
               rx=math.atan2(-sgn * run, -drop))
        _strut(p, WOOD, (a0[0], a0[1], a0[2] + 0.80), (a1[0], a1[1], a1[2] + 0.80), 0.10)
        _strut(p, WOOD, a1, (a1[0], a1[1], foot(su, sgn * (dd * 0.48 + run))), 0.18)
    return top, at(0, rv, top + 0.72)


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
    n_deck = 0
    n_terrace = 0
    prev_rail = {}                       # per tier: the last bay's rail anchor
    # `nr` is the gorge frame's LEFT normal, so +1 is the left bank looking downstream.
    bench_side = 1 if VM.BENCH_LEFT else -1
    anchor_arc = VM.river_arc_at(aw[0], aw[1])
    # Tiers on ONE bank, not on two: the town keeps its mass and its stepped read
    # without borrowing the cliff opposite. STATS carries the count so the change is
    # visible in valley_build.json rather than only in a render.
    n_water_deck = 0
    deck_dz = []                         # every deck top MINUS its local water level
    for side in (bench_side,):
        for tier in range(len(DH_TIER_TOP)):
            # THE TIER IS A HEIGHT ABOVE THE LOCAL WATER, and the lateral offset is
            # SEARCHED for — see DH_TIER_H. Round 1's constant `lat = hw + 2.4 +
            # tier * 3.5` is what put the lowest deck 4.9-11.1 u above the river.
            for stat in (-13.0, -7.0, -1.0, 5.0, 11.0):
                jx = rng.uniform(-1.1, 1.1)
                # THE BAY IS SIZED BEFORE IT IS PLACED, because a wet bay's position
                # depends on its own depth (DH_WET_IN).
                dw = rng.uniform(*DH_DECK_W)
                dd = rng.uniform(*DH_DECK_D)
                dims = (dw, dd, rng.uniform(*DH_LIFT))
                # STEP ALONG THE RIVER'S OWN CURVE, and take the normal there.
                # Restricting `side` to the bench was not enough: this cluster spans
                # 24u of a reach that turns from bearing 13 to 49 degrees, so lateral
                # offsets taken in the ANCHOR's frame walked across the water — 34% of
                # the impression's vertices were still on the far wall, measured by
                # vertex.  A per-station bank guard refused those, and correctly, but
                # it cost the town half its houses.  On the curve, nothing is refused.
                cpt, ctg, cnr, cwl, chw, _ = VM.river_frame_at_arc(anchor_arc + stat + jx)
                lat, gz = contour_lat(F, zg, fr, cpt, cnr, side,
                                      cwl + DH_TIER_H[tier])
                if lat is None:                     # wall never reaches this tier
                    continue
                wet = (tier == 0)
                if wet:
                    lat = max(1.2, lat - dd * DH_WET_IN)
                q = cpt + cnr * side * lat
                px, py = float(q[0] - VM.CX), float(q[1] - VM.CY)
                off, hw_here = VM.bank_offset(float(q[0]), float(q[1]))
                # ONE GUARD FOR EVERY TIER, and it is the CENTRELINE, not the bank.
                # Round 1's `off * side >= hw + 1.5` said "stand beyond the water's
                # edge", which is precisely the rule that makes a waterfront town
                # impossible — it refused four of five tier-1 stations here, because
                # once tiers are solved by HEIGHT a low tier legitimately sits at the
                # water. What must never happen is the town wading across to the far
                # wall (ch3 territory), and that is what this tests.
                if off * side < 0.30 * hw_here:
                    continue
                if wet and off * side > hw_here + 2.5:
                    continue
                # The terrace ALIGNS to the bench — a stepped town does not scatter its
                # yaw — so the copy-read is broken here on size and tint, plus a small
                # yaw wobble a mason would allow. See the note above build_emberbrook.
                yaw = (math.atan2(float(ctg[1]), float(ctg[0])) + rot
                       + (0.0 if side > 0 else math.pi) + rng.uniform(-0.16, 0.16))
                # WHICH WAY IS OUT OVER THE GORGE, SOLVED. `yaw` carries the anchor
                # rotation and the bank flip, so local +Y is not reliably the water
                # side — measure it against the river's own normal instead. Every
                # cantilever, lean-to pitch and stair rake in the bay hangs off this
                # sign; assuming it is how the deck ends up pitched into the cliff.
                sgn = 1.0 if (-math.sin(yaw) * float(-cnr[0] * side)
                              + math.cos(yaw) * float(-cnr[1] * side)) > 0 else -1.0
                # A terrace pad + retaining wall is what makes a cluster read
                # STEPPED — but a pad placed at the CENTRE height cantilevers off a
                # gorge wall, which is what the first render showed.  The pad top is
                # the lowest of its own four corners, and the wall reaches from there
                # down to the ground beneath its outer edge.
                pw_, pd_ = dw * 1.06, dd * 1.22
                ca, sa = math.cos(yaw), math.sin(yaw)
                cor = [(px + ca * u * pw_ / 2 - sa * v * pd_ / 2,
                        py + sa * u * pw_ / 2 + ca * v * pd_ / 2)
                       for u in (-1, 1) for v in (-1, 1)]
                ch = [gh(F, zg, fr, a_, b_) for a_, b_ in cor]
                # THE SPREAD TEST IS NOW A TERRACE TEST, NOT A STATION VETO (2026-08-04).
                # It used to `continue` — no house where the ground was steeper than
                # ~2.8u across the pad, which cost the cluster its stations on exactly
                # the steep wall the town is supposed to cling to. A cottage needs
                # bedding; A SCAFFOLD DOES NOT, that being the point of stilts. So the
                # steep stations keep their bay and simply lose the masonry under it.
                # A WET BAY GETS NO MASONRY. A stone terrace poured in the river is a
                # causeway, and a causeway is the one thing that must not appear here:
                # it would both fill the channel the boat leaves by and hand the
                # player a standable ramp toward the ch3 wall.
                pad = None
                if not wet and max(ch) - min(ch) <= 2.8:
                    pad = min(ch) + 0.10
                    p.cube(STONE, (px, py, pad - 0.20), (pw_, pd_, 0.44), rz=yaw)
                    foot = min(ch) - 0.4
                    ox = px - nr[0] * side * pd_ * 0.52
                    oy = py - nr[1] * side * pd_ * 0.52
                    foot = min(foot, gh(F, zg, fr, ox - nr[0] * side * 1.6,
                                        oy - nr[1] * side * 1.6))
                    drop = max(0.6, min(5.0, pad - foot))
                    p.cube(STONE, (ox, oy, pad - 0.42 - drop / 2), (pw_, 0.38, drop),
                           rz=yaw)
                    n_terrace += 1
                dtop, rail = scaffold_bay(p, F, zg, fr, px, py, yaw, sgn, dims, pad,
                                          rng, lamp=(n_deck % 3 != 1),
                                          top_z=cwl + DH_TIER_TOP[tier])
                deck_dz.append(dtop - cwl)
                if wet:
                    n_water_deck += 1
                # THE LAUNDRY LINE between neighbours in a tier. The townmap names it
                # twice ("laundry lines, rickety balconies"; "Drying decks — laundry
                # lines and fish racks strung between the clusters"), and at vista
                # distance it is the cheapest thing in the frame that says the decks
                # are ONE town rather than a row of separate huts. Sagged in two
                # segments; a straight line reads as a wire.
                pr = prev_rail.get(tier)
                if pr is not None:
                    span = math.hypot(rail[0] - pr[0], rail[1] - pr[1])
                    if span < 9.0:
                        mid = ((rail[0] + pr[0]) / 2, (rail[1] + pr[1]) / 2,
                               (rail[2] + pr[2]) / 2 - 0.16 - span * 0.045)
                        _strut(p, ROPE, pr, mid, 0.07)
                        _strut(p, ROPE, mid, rail, 0.07)
                prev_rail[tier] = rail
                n_deck += 1
    # ---- THE LOCK FLIGHT: the reason the locks exist, and the reason the river
    # ---- reads as a CASCADE (round 2, 2026-08-04) ---------------------------
    # Round 1 built these weirs and they were invisible in the frame, because A WEIR
    # WHOSE WATER DOES NOT STEP IS A WALL STANDING IN A RIVER: the surface ran past
    # them as one smooth ramp (VM.water_level interpolates the authored profile and
    # nothing in it knows a weir is there). The identity the user is asking for —
    # canon's "locks as the town's spine, waterfalls on every level" — is carried by
    # THE WATER, not by the masonry, and at 40 m a stepped surface is the whole read.
    #
    # So each weir now PONDS its own reach. The pool is held at the sill plus
    # DH_LOCK_RISE and its head is FOUND, not typed: march upstream until the natural
    # surface has itself risen to the crest, and stop there. That is what makes the
    # upstream seam invisible — at the head the natural ribbon is at or above the
    # pool, so it COVERS the pool's leading edge instead of z-fighting it, and the
    # pool appears to emerge from under the river. Every drop is then exactly
    # DH_LOCK_RISE tall and no seam has to be faired by hand.
    #
    # THE POOL WIDENS AS IT DEEPENS, because its edge is solved against the same
    # ground contour the decks are rather than taken from the channel's nominal
    # half-width. That is free, it is what ponded water actually does, and it draws
    # the townmap's "boat queue pooled above the jam" without authoring a vertex.
    #
    # THE WATER IS ITS OWN `water_` PROP, and BOTH halves of that matter. build_falls
    # paid for the first: ONE MIXED-MATERIAL MESH DISABLES VERTEX ALPHA FOR EVERY
    # PRIMITIVE IN IT, so water sharing a mesh with the STONE lock would export
    # COLOR_0 as VEC3 and the entire flight would go opaque. The second is
    # valley_export's own rule — every mesh that is NOT water_/lm_/veg_ is standable
    # AND BLOCKING — so a pool built into the town prop would be walkable water.
    # Pools and falls are split for the reason build_falls split them: a pool has a
    # real depth and wants the ramp, a curtain is a vertical sheet whose "depth" is
    # meaningless and wants a flat alpha.
    pwp = B.Prop("water_dellhollow_pools")
    pwf = B.Prop("water_dellhollow_falls")
    n_weir = 0
    n_pool = 0
    lock_steps = []
    crest = None
    for k, stat in enumerate((-11.0, -1.0, 9.0)):
        cx_ = float(ctr[0] + tg[0] * stat)
        cy_ = float(ctr[1] + tg[1] * stat)
        _, wtg, wnr, wwl, whw, _ = gorge_frame(F, cx_ + VM.CX, cy_ + VM.CY)
        ang = math.atan2(float(wtg[1]), float(wtg[0])) + math.pi / 2
        pool_z = wwl + DH_LOCK_RISE
        a_w = VM.river_arc_at(cx_ + VM.CX, cy_ + VM.CY)
        # THE HEAD OF THE POND, found by marching upstream to the crest level.
        head = a_w - DH_POOL_MAX
        s_ = a_w
        while s_ > a_w - DH_POOL_MAX:
            s_ -= 0.4
            if float(VM.river_frame_at_arc(s_)[3]) >= pool_z:
                head = s_
                break
        # THE PONDED SURFACE, its edges on the crest contour.
        #
        # NINE COLUMNS, AND THE FIRST BUILD PROVED WHY. This was two columns — one
        # per edge — and every vertex it had therefore sat exactly ON the contour
        # where the pool meets the ground, i.e. at depth ZERO. water_bathymetry
        # measured it and said so: `dhpools ... alpha [0.06, 0.06, 0.06] depth
        # [-0.49, -0.12, -0.01]`, an alpha of 0.06 being an INVISIBLE pool. The whole
        # cascade rendered as nothing. This is build_water's own R13 lesson — "THE
        # STRIP NEEDS AN INSIDE", a depth ramp on a two-column strip can only ever
        # describe its two edges — and it is written thirty lines above this one; a
        # note read and then not applied is a note that cost a build. The interior
        # columns are what sit over the deep bed and carry the ramp.
        ncol = 9
        ns = max(3, int((a_w - head) / 1.1))
        cols_ = [[] for _ in range(ncol)]
        wide = 0.0
        for i_ in range(ns + 1):
            s2 = head + (a_w - head) * i_ / ns
            cpt2, _, cnr2, _, hw2, _ = VM.river_frame_at_arc(s2)
            eL, _ = contour_lat(F, zg, fr, cpt2, cnr2, 1, pool_z,
                                lo=hw2 * 0.55, hi=hw2 + 8.0, step=0.18)
            eR, _ = contour_lat(F, zg, fr, cpt2, cnr2, -1, pool_z,
                                lo=hw2 * 0.55, hi=hw2 + 8.0, step=0.18)
            eL = hw2 if eL is None else eL
            eR = hw2 if eR is None else eR
            wide = max(wide, eL + eR)
            for ci in range(ncol):
                u = ci / (ncol - 1.0)                 # 0 at the right edge, 1 at left
                q2 = cpt2 + cnr2 * (-eR + (eL + eR) * u)
                cols_[ci].append((float(q2[0] - VM.CX), float(q2[1] - VM.CY), pool_z))
        for ci in range(ncol - 1):
            pwp.strip(WATER, cols_[ci], cols_[ci + 1])
        n_pool += 1
        # the masonry has to be as wide as the water it holds, or the pool runs
        # round the end of its own dam — measured off the pool, never guessed.
        span = max(whw * 2.0 + 1.4, wide + 1.6)
        # SEGMENTED: one 2 x 15 x 3.4u block beside the houses reads as a monolith,
        # and the moorage camera stood right behind it.  Six courses with hashed
        # offsets read as built masonry at the same cost.  The courses now run from
        # the BED to the crest, because the dam has to be as tall as its own head.
        bed = min(gh(F, zg, fr, cx_, cy_), wwl - 2.6)
        nb = 6
        for bi in range(nb):
            u = (bi - (nb - 1) / 2.0) * (span / nb)
            hj = float(O3._hash01(bi, k * 17, 3))
            top_ = pool_z + 0.34 - 0.10 * hj
            p.cube(STONE, (cx_ + float(wnr[0]) * u, cy_ + float(wnr[1]) * u,
                           (bed + top_) / 2),
                   (1.5 + 0.22 * hj, span / nb * 0.97, max(1.0, top_ - bed)), rz=ang)
        p.cube(STONE, (cx_, cy_, pool_z + 0.66), (2.1, span, 0.36), rz=ang)  # crest walk
        # THE FALL over the sill: a curtain from the crest down to the natural
        # surface just below it, plus churn at its foot. This is the element that
        # makes the step read at 40 m — the level change alone is a line, and a line
        # is what round 1 already had.
        _, _, _, wl_dn, _, _ = VM.river_frame_at_arc(min(a_w + 2.6, VM.RIV_S[-1]))
        drop = max(0.5, pool_z - wl_dn)
        nseg, nrow = 7, 4
        for ci in range(nseg):
            u = (ci + 0.5) / nseg * 2.0 - 1.0
            bow = (1.0 - u * u) * 0.42
            for r in range(nrow):
                fmid = (r + 0.5) / nrow
                zz = pool_z - drop * fmid
                pwf.cube(WATER, (cx_ + float(wnr[0]) * u * span * 0.46
                                 - float(wtg[0]) * (0.5 + bow),
                                 cy_ + float(wnr[1]) * u * span * 0.46
                                 - float(wtg[1]) * (0.5 + bow), zz),
                         (0.5, span * 0.92 / nseg, drop / nrow * 1.06), rz=ang)
        for ci in range(9):
            hj = float(O3._hash01(ci, k * 23, 5))
            u = (ci / 8.0 - 0.5) * span * 0.86
            pwf.ico(WATER, (cx_ + float(wnr[0]) * u - float(wtg[0]) * (1.5 + 0.9 * hj),
                            cy_ + float(wnr[1]) * u - float(wtg[1]) * (1.5 + 0.9 * hj),
                            wl_dn + 0.20 + 0.5 * hj),
                    (0.52 + 0.3 * hj, 0.52 + 0.3 * hj, 0.36), subd=1)
        lock_steps.append(round(float(drop), 2))
        if crest is None:
            crest = (cx_, cy_, pool_z + 0.94, ang, span)
        # ---- waterwheel HINTS on the abutment (2 of the 3 stations) ----------
        if k != 1:
            # A WHEEL IS DRIVEN BY THE TAILWATER, so its hub hangs just above the
            # level BELOW the sill and its rim dips into it — round 1 hung it at the
            # sill's own level, which now that the pool is 1.9u higher would have
            # buried the wheel in the pond it is supposed to be spilling out of.
            # The abutment moved out with the dam, so it is measured off `span`.
            hub = wl_dn + 1.25
            for side in (-1, 1):
                wx_ = cx_ + float(wnr[0]) * side * (span * 0.5 + 1.0)
                wy_ = cy_ + float(wnr[1]) * side * (span * 0.5 + 1.0)
                for j in range(9):
                    a = j * (2 * math.pi / 9)
                    p.cube(WOOD, (wx_ + math.cos(a) * 1.15 * float(wtg[0]),
                                  wy_ + math.cos(a) * 1.15 * float(wtg[1]),
                                  hub + math.sin(a) * 1.15),
                           (0.40, 0.14, 0.40), rz=ang, rx=a)
                p.cone(WOOD, (wx_, wy_, hub), 1.22, 1.22, 0.20, seg=12, rz=ang)
                p.cone(METAL, (wx_, wy_, hub), 0.16, 0.16, 1.2, seg=8, rz=ang)
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
                # AND THEN IT LOST THE COTTAGES' MATERIALS WITH THEM: this was the last
                # plaster wall and the last tile gable in Dellhollow, and one gabled
                # roof beside twenty lean-tos is precisely the element the user's
                # "entirely distinct look" rules out — swappable into Emberbrook
                # without looking wrong. A millhouse here is a stone footing, plank
                # cladding and one pitch.
                mb = max(mz, wl_dn)
                p.cube(STONE, (mx, my, mb + 0.55), (2.3, 2.1, 1.10), rz=ang)
                p.cube(WOOD, (mx, my, mb + 2.40), (2.0, 1.8, 2.60), rz=ang)
                p.cube(TAR, (mx, my, mb + 3.78), (2.6, 2.3, 0.16), rz=ang, rx=0.26)
                n_weir += 1
    # STATS IS THE HONEST RECORD OF THE SWAP. `dellhollow_houses` is GONE rather
    # than left reading zero: a stat that never moves off zero is a stat nobody
    # reads. The two face counts are the distinctness claim in a number a diff can
    # check — Emberbrook's vocabulary is plaster and tile, and Dellhollow must carry
    # NONE of either. If a later lane reintroduces a gable here, this goes nonzero.
    p.bm.faces.ensure_lookup_table()
    STATS["dellhollow_decks"] = n_deck
    STATS["dellhollow_terraces"] = n_terrace
    STATS["dellhollow_plaster_faces"] = sum(1 for f in p.bm.faces if f[p.cl] == WALL)
    STATS["dellhollow_tile_faces"] = sum(1 for f in p.bm.faces if f[p.cl] == ROOF)
    STATS["dellhollow_wheels"] = n_weir
    # ROUND 2'S OWN CLAIM, in numbers a diff can check: how many bays stand in the
    # river, and how far the water actually steps at each lock. `deck_over_water_u`
    # is the measurement the user's complaint was about — it is the whole town's
    # vertical extent ABOVE THE LOCAL WATERLINE, floor and ceiling. Round 1's LOWEST
    # deck alone stood +4.94 to +11.12, and the first round-2 build still carried its
    # top tier to +19. Both ends matter: the floor is "does the town reach the
    # water", the ceiling is "does it stay in the gorge instead of towering over the
    # rim road at 12.3-14.5". A regression in either is visible here without
    # re-rendering anything.
    STATS["dellhollow_water_decks"] = n_water_deck
    STATS["dellhollow_pools"] = n_pool
    STATS["dellhollow_lock_drops_u"] = lock_steps
    STATS["dellhollow_deck_over_water_u"] = [round(min(deck_dz), 2),
                                             round(max(deck_dz), 2)] if deck_dz else []
    return p.finish(col), crest, pwp.finish(col), pwf.finish(col)


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
# THE OPEN-COUNTRY SCATTER, and it is three numbers, not one.  The blind critic
# on the gorge plateau: "the plateau trees along the top edge are one lollipop at
# one size" — a treeline, not a picket fence.  All three causes were here:
#   * ONE SPECIES.  `key = "a"` unconditionally in the meadow zone.
#   * ONE SIZE.     `s = uniform(0.86, 1.26)`, a 1.5x span that a ridge silhouette
#                   at 60 m cannot resolve at all.
#   * ONE SPACING.  `free()` rejected inside a FIXED radius, so the survivors sit
#                   on the densest packing of one circle — a lattice, which is
#                   what reads as a fence.
# `jitter` multiplies each candidate's own keep-out radius, so trees cluster and
# gap; `scale` is the ramp; `mix` is the second species' share.
MEADOW_CFG = dict(spacing=11.0, target=44, shrub=0.22, spow=1.45,
                  scale=(0.68, 1.58), jitter=(0.62, 1.55), mix=0.42)


def plant_region(col, F, zg, fr, suffix, seed=20260730):
    rng = np.random.RandomState(seed)
    V = O3.Veg("field")
    cell = 3.2
    grid = {}
    placed = []
    bushes = []

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
            jit = cfg.get("jitter")
            spj = sp * (float(rng.uniform(*jit)) if jit else 1.0)
            if not free(x, y, spj):
                continue
            z = gh(F, zg, fr, x, y)
            fw = float(zg.wsample(zg.forest_w, x, y))
            interior = fw >= 0.72
            if zone == "meadow":
                key = "e" if rng.rand() < cfg.get("mix", 0.0) else "a"
            elif interior:
                key = "a" if rng.rand() < 0.80 else "c"
            else:
                key = "c" if rng.rand() < 0.74 else "a"
            slo, shi = cfg.get("scale", (0.86, 1.26))
            # weighted toward the SMALL end: a stand of young trees with a few
            # mature ones reads as a treeline, where a uniform draw gives a row of
            # medium ones with noise on it.  Power 1.0 for the forest stands, whose
            # scatter nobody has complained about — this is an open-country fix.
            s = float(slo + (shi - slo) * rng.rand() ** cfg.get("spow", 1.0))
            O3.TREE_FN[key](V, x, y, z, s, float(rng.uniform(0, 6.283)), rng)
            if rng.rand() < cfg["shrub"]:
                a = rng.uniform(0, 6.283)
                dd = rng.uniform(1.3, 2.5)
                sx, sy = x + math.cos(a) * dd, y + math.sin(a) * dd
                # THE BUSH IS NO LONGER A PAIR OF ELLIPSOIDS.  It used to be
                # `O3.SHRUB_FN["a"]` emitting two solid squashed lobes into this
                # same Veg accumulator, which is what read as a pancake disc
                # floating on its own ground.  Sites are COLLECTED here and built
                # as one bushlang mass afterwards (VV.build_bushes) — they cannot
                # be built inline because a Mass needs all its lobes before
                # cull_interior and shade_core can run.
                bushes.append((sx, sy, gh(F, zg, fr, sx, sy),
                               float(rng.uniform(0.6, 1.0))))
            add(x, y, spj)
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
    print("  planting: %d trees (a=%d c=%d e=%d), %d shrubs, %d cards, %d lobes"
          % (len(placed), n["a"], n["c"], n["e"], n["shrub"], n["cards"], n["lobes"]))
    for k in sorted(byz):
        print("    %-18s %d" % (k, byz[k]))
    STATS["trees"] = len(placed)
    STATS["trees_by_stand"] = byz
    out = V.finish(col, suffix)

    # ---- the bushes, as one bushlang mass (see VV.build_bushes) --------------
    # RETURNED SEPARATELY, and that is a contract and not tidiness: everything in
    # `out` goes through B.write_prop_colors, which writes the class-index colour
    # attribute a Prop mesh expects.  A bushlang mass already carries its own
    # COLOR_0 with a different layout, so putting bushes in `out` made that pass
    # die with "internal error setting the array".  The canopy masses are held out
    # of `veg_keys` for exactly this reason; bushes join them.
    bobs = []
    if bushes:
        atlas, atlas_nor = VV.FA.build_atlas()
        tile, tile_nor = VV.FA.build_tile()
        bcore, bcard = VV.BL.materials(atlas, atlas_nor, tile, tile_nor,
                                       suffix="valley", pbr_mat=B2.pbr_mat)
        bobs, bt, bc = VV.build_bushes(col, F, bushes,
                                       np.random.RandomState(seed + 4242),
                                       core_mat=bcore, card_mat=bcard)
        STATS["bushes"] = dict(n=len(bushes), core_tris=bt, cards=bc)
        print("  bushes: %d plants, core %d tris, %d cards" % (len(bushes), bt, bc))
    return out, placed, byz, bobs


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
            # A LIT WINDOW IS DARK GLASS WITH A LIGHT BEHIND IT, and this material
            # was PALE GLASS with a light behind it: `use_vcol` (the default) hands
            # Base Color to COLOR_0, which the class-gain pass lifts toward its own
            # target, so the pane had a near-white albedo and the 2.4x golden key
            # blew it out on its own.  MEASURED, because three rounds had assumed
            # the emissive was the culprit and swept it: at ?owemit=0.02, with the
            # emission effectively off AND ?bloom_s=0, the window core still read
            # (254, 215, 193).  Neither the emissive nor the bloom was making it
            # white — the albedo was.  A fixed dark base puts the pane's appearance
            # back where it belongs, in the light it is supposed to be emitting.
            "emit": B.new_mat("ow_%s_emit" % STYLE, base=(0.045, 0.030, 0.018),
                              use_vcol=False, rough=0.6, emit=srgb("ff9f38"),
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
        made["falls"], made["falls_lip"] = _fl
    _tb = build_tributaries(col, F, zg, fr)
    if _tb is not None:
        made["tributaries"] = _tb
    made["road"] = build_road(col, F)
    cw = build_causeway(col, F, zg, fr)
    if cw is not None:
        made["causeway"] = cw
    made["green"] = build_emberbrook_green(col, F, zg, fr)
    made["emberbrook"] = build_emberbrook(col, F, zg, fr)
    dh, crest, dhp, dhf = build_dellhollow(col, F, zg, fr)
    made["dellhollow"] = dh
    made["dhpools"], made["dhfalls"] = dhp, dhf
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
    field, placed, byzone, bushobs = plant_region(col, F, zg, fr, SUF)
    t_veg = time.time() - t0
    veg_keys = []
    for k, o in field.items():
        made["veg_" + k] = o
        veg_keys.append("veg_" + k)
    # bushes carry their own COLOR_0 — same handling as the canopy masses
    for i_, ob_ in enumerate(bushobs):
        made["bush_%d" % i_] = ob_
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
    PROPKEYS = ([k for k in ("skirt", "water", "falls", "falls_lip", "tributaries", "road", "causeway", "green",
                             "emberbrook", "dellhollow", "dhpools", "dhfalls",
                             "damcrest", "portals", "oldgate",
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
    UVKEYS = [k for k in ("emberbrook", "dellhollow", "portals", "oldgate", "falls", "falls_lip", "props", "damcrest",
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
    # ...and the LAST write to the water sheets', for the same reason.
    STATS["water_bathymetry"] = water_bathymetry(made, F, zg, fr)

    # ---- THE PER-HOUSE CHIMNEY GATE (R13) ----------------------------------
    # A GATE THAT MEASURES ITS OWN DRAWING CANNOT MEASURE ITS OWN BUILD (CLAUDE.md,
    # _court_probe): this proves the three clauses hold for the parameters that were
    # handed to p.cube, which is necessary and not sufficient.  The build is
    # confirmed by photographing it — see scratchpad/r13b.
    if CHIM_GATE:
        ok = sum(1 for r in CHIM_GATE if r[0] and r[1] and r[2])
        pm = [r[3] for r in CHIM_GATE]
        wr = [r[4] for r in CHIM_GATE]
        rc = [r[5] for r in CHIM_GATE]
        print("CHIMNEY GATE: %d/%d houses carry a stack "
              "(i footprint-in-pad %d, ii behind-wall-face %d, iii cap-above-ridge %d)"
              % (ok, len(CHIM_GATE), sum(1 for r in CHIM_GATE if r[0]),
                 sum(1 for r in CHIM_GATE if r[1]), sum(1 for r in CHIM_GATE if r[2])))
        print("  pad margin   min %+.3f  median %+.3f  max %+.3f u" %
              (min(pm), float(np.median(pm)), max(pm)))
        print("  wall recess  min %+.3f  median %+.3f  max %+.3f u  (+ve = behind the face)" %
              (min(wr), float(np.median(wr)), max(wr)))
        print("  ridge clear  min %+.3f  median %+.3f  max %+.3f u" %
              (min(rc), float(np.median(rc)), max(rc)))
        for i, r in enumerate(CHIM_GATE):
            print("    house %2d  %s%s%s  pad %+.3f  recess %+.3f  ridge %+.3f"
                  % (i, "i" if r[0] else "-", "i" if r[1] else "-", "i" if r[2] else "-",
                     r[3], r[4], r[5]))
        STATS["chimneys"] = dict(built=ok, houses=len(CHIM_GATE),
                                 pad_margin_min=round(min(pm), 3),
                                 wall_recess_min=round(min(wr), 3),
                                 ridge_clear_min=round(min(rc), 3))
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

    # ---- R14: THE CLUMPS WERE NOT TOUCHING THE GROUND ----------------------
    # It runs HERE and nowhere earlier because it is the LAST write to two
    # COLOR_0 buffers that four passes upstream each rewrite in full
    # (write_prop_colors -> apply_class_gains for the veg, terrain_pbr_f2 ->
    # VL.surface for the ground).  Same rule as the per-house tints.
    STATS["contact_shadow"] = canopy_contact(made, F, zg, fr)

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
