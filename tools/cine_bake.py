# cine_bake.py — bake A TOWN'S CINEMATIC SHOTS out of its live master.
#
#   Blender -b tools/blends/<town>-master.blend -P tools/cine_bake.py \
#           --python-exit-code 1 -- [opts]
#     --town <id>        which town's solved camera file to bake (default dellhollow);
#                        picks public/townmap/<id>.cameras.solved.json, and the output
#                        bundle follows that file's own sceneKey
#     --glb              export the shared collision GLB + meta.json only, no rendering
#     --cams a,b,c       bake only these camera ids (default: all in the solved file)
#     --samples N        Cycles samples for the beauty render (default 128, denoised)
#     --res WxH          beauty resolution (default 2688x1536)
#     --skip-existing    leave a camera alone if its bg.png is already on disk
#     --draft <dir>      FRAMING CONTACT SHEET: beauty pass only, into <dir>, writing
#                        nothing under public/ (no depth, no GLB, no cine.json). Pair
#                        with --res 1008x576 --samples 28 to judge eleven framings for
#                        the price of one plate.
#     --standins         draft only: 1.7 m matte figures on the shot's own ground at its
#                        nearest / median / farthest spawn candidate, so the sheet shows
#                        the character scale the numbers claim
#
# WHAT THIS IS. tools/depth_bake.py is the canon bundle exporter for a scene with ONE
# camera: one Blender session on the ORIGINAL blend (read-only — never copy a blend,
# relative texture paths break, manifest 63) renders the background, bakes the
# view-space depth map from the SAME camera, and exports the collision GLB, so the
# image and the occlusion physically cannot disagree. This is that pipeline
# generalised to N cameras over ONE town:
#
#   * the depth contract is IDENTICAL, per camera: bg.png and depth.png come from the
#     same session, same transform, same camera. Nothing about exact-pixel occlusion
#     is weakened by there being sixteen of them.
#   * the collision GLB is exported ONCE and SHARED. A master-baked bundle carries the
#     whole town's collision (canon), so eighteen per-camera bundles would have meant
#     ~330 MB of byte-identical GLB in git and a multi-second bundle reload on every
#     camera cut — which is not a cut, it is a loading screen. One bundle, N art
#     pairs, and the runtime's scene-internal handoff swaps two textures.
#   * every camera NUMBER comes from townmap/<town>.cameras.solved.json, which the
#     runtime also reads (through cine.json). Nothing about a camera is typed here.
#
# ORDER IS LOAD-BEARING: all beauty renders first, THEN the volume deletion + depth
# override, THEN all depth renders, THEN the GLB. The depth pass destroys the scene
# for beauty work (fog cubes deleted, every surface overridden with an emission
# shader), so it cannot be interleaved.
#
# Output: public/assets/scenes/<sceneKey of the solved file>/   (Dellhollow: del-cine)
#   scene.glb                    shared collision + walk_ surfaces (whole town)
#   cine.json                    per camera: pos/aim/fov/clip, depth near/far, spawn
#   cameras/<id>/bg.png          THE DELIVERABLE ART (Cycles, AgX, the accepted grade)
#   cameras/<id>/depth.png       rgb24 view-space depth at runtime canvas resolution
#   meta.json                    export stamp (the HUD shows master@<time>)

import bpy, os, sys, json, struct, zlib, contextlib, io, math, time, shutil
# unbuffered: a 60-minute bake must report progress as it happens, not at exit
try: sys.stdout.reconfigure(line_buffering=True)
except Exception: pass
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def opt(name, default=None):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1] if (default is not None and i + 1 < len(argv)) else True
    return default

# THE TOWN. One id picks the solved camera file; everything else — the output bundle,
# the blend this must have been opened on — follows from it or from that file's own
# sceneKey, so a second town bakes with no edit here.
TOWN = opt("--town", "dellhollow")
SOLVED = os.path.join(REPO, "public/townmap/%s.cameras.solved.json" % TOWN)
MASTER = "tools/blends/%s-master.blend" % TOWN
assert os.path.exists(SOLVED), (
    "no solved camera file for town '%s' (%s) — run: node tools/cine_solve.mjs --town %s"
    % (TOWN, SOLVED, TOWN))

GLB_ONLY = "--glb" in argv
SKIP_EXISTING = "--skip-existing" in argv
SAMPLES = int(opt("--samples", "128"))
RES = opt("--res", "2688x1536")
BW, BH = [int(v) for v in RES.split("x")]
DW, DH = 1344, 768                      # depth = the runtime drawing buffer, exactly

S = json.load(open(SOLVED))
# --- DRAFT MODE: a framing contact sheet, never a deliverable ------------------
# `--draft <dir>` renders the BEAUTY PASS ONLY, into <dir>, and touches nothing under
# public/. It exists for one question — HOW BIG IS THE CHARACTER IN THIS FRAME — which
# is a question you answer by looking, not by reading charPxFar, and which the closeness
# round (user redline 2026-08-02) has to answer eleven times before it is worth spending
# eleven full plates. It pairs with `--standins`, which puts 1.7 m matte figures on the
# shot's own ground at its nearest / median / farthest spawn candidate, so the sheet
# shows the near and far read of the very numbers the solver reports. Depth and GLB are
# skipped deliberately: a draft that wrote a depth map would be a bundle, and a bundle
# baked at 28 spp is exactly the thing that must never reach the runtime.
DRAFT = opt("--draft", "")
STANDINS = "--standins" in argv
if DRAFT and DRAFT is not True:
    OUT = os.path.abspath(DRAFT)
else:
    DRAFT = ""
    OUT = os.path.join(REPO, "public/assets/scenes", S["sceneKey"])
ART = os.path.join(OUT, "cameras")
os.makedirs(ART, exist_ok=True)
CAMS = {c["id"]: c for c in S["cameras"]}
want = opt("--cams", "")
ids = [i for i in (want.split(",") if want and want is not True else list(CAMS))if i in CAMS]
if want and want is not True:
    missing = [i for i in want.split(",") if i not in CAMS]
    assert not missing, "unknown camera ids: %s" % missing

sc = bpy.context.scene
D = S["defaults"]
T0 = time.time()

# --- GPU ----------------------------------------------------------------------
prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    cp = prefs.preferences
    try:
        cp.compute_device_type = 'METAL'
        cp.get_devices()
        for d in cp.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, CPU fallback:", e)

# --- the grade: one place, from the data ---------------------------------------
sc.view_settings.view_transform = D.get("view_transform", "AgX")
sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
sc.view_settings.exposure = D.get("exposure", 0.0)

# --- THE MOONLIT EVENING: overrides, and why they are FLAGS and not a file edit ---
# Emberbrook's dusk was measured unreadable on the shots outside the lamp roll, and the
# fix that survived review is a cool directional MOON plus, where the frame carries no
# warm light of its own, a warm practical in it. That recipe FORKS PER SHOT — the
# lamp-bearing shots take a modest moon, the lampless ones take a strong moon and an
# anchor — and `defaults.lightRig` has no per-camera layer to express that.
#
# The honest thing to do with a grade that outgrew its schema is NOT to quietly widen the
# schema from a bake lane: <town>.cameras.json is a town map file and the coordinator owns
# it. So the recipe arrives here as EXPLICIT FLAGS, and every value actually applied is
# written into the shipped cine.json as `appliedGrade` — the bundle states its own hour,
# which is the invariant the lightRig note cares about ("the master blend and the shipped
# plate cannot disagree"). The per-camera lightRig schema is PROPOSED to the coordinator,
# not stamped here.
MOON = float(opt("--moon", "0") or 0)
MOONCOL = [float(v) for v in opt("--mooncol", "0.65,0.75,1.0").split(",")]
MOONRX, MOONRZ = float(opt("--moonrx", "50")), float(opt("--moonrz", "90"))
# NOT `opt("--sky", None)`. This file's opt() returns the literal True — not the value —
# when its default is None, because the value branch is guarded by `default is not None`.
# `float(True)` is 1.0, so `--sky 0.65` silently applied a sky of 1.0 and the first square
# plate baked at the wrong hour while the log cheerfully printed "sky strength -> 1.000".
# An empty-string default keeps the value branch live and stays falsy when absent.
SKY_OVR = opt("--sky", "")
EXPO_OVR = opt("--exposure", "")
GLOW = float(opt("--glow", "0") or 0)
ANCHORLIGHT = float(opt("--anchorlight", "0") or 0)
LAMPWATTS = float(opt("--lampwatts", "0") or 0)
if EXPO_OVR:
    sc.view_settings.exposure = float(EXPO_OVR)
    print("GRADE OVERRIDE  exposure -> %.3f" % sc.view_settings.exposure)

# ...AND THE LIGHT THE GRADE IS A GRADE OF. `exposure` alone is a knob on a fixed
# rig, and an hour is not a knob: Emberbrook's Chapter One is the EMBERWAKE EVENING,
# where the sun is nearly down, the sky has stopped being the light source, and the
# town's light comes OUT of the Heartlight and the fifteen lamps lit from it. That is
# a different rig, not a different exposure, and it belongs in the same one place the
# exposure does — defaults.lightRig in <town>.cameras.json — so the master blend and
# the shipped plate cannot disagree about what hour it is, and so the bake can be
# re-run in the other key without a rebuild.
#
# A town with no `lightRig` is untouched: Dellhollow bakes byte-identical, and the
# blend's own rig stays the truth for every town that does not state one.
RIG = D.get("lightRig") or {}
if RIG:
    print("LIGHT RIG from the camera file (this town states its own hour):")
    sun_spec = RIG.get("sun") or {}
    if sun_spec:
        so = bpy.data.objects.get(sun_spec.get("object", ""))
        assert so is not None and so.type == 'LIGHT', (
            "lightRig.sun.object '%s' is not a light in this blend" % sun_spec.get("object"))
        if "energy" in sun_spec: so.data.energy = sun_spec["energy"]
        if "color" in sun_spec: so.data.color = tuple(sun_spec["color"])
        if "rotationEulerDeg" in sun_spec:
            so.rotation_euler = tuple(math.radians(v) for v in sun_spec["rotationEulerDeg"])
        print("  sun    %-12s energy %.2f  color %s  rot %s"
              % (so.name, so.data.energy, tuple(round(c, 2) for c in so.data.color),
                 tuple(round(math.degrees(a)) for a in so.rotation_euler)))
    w_spec = RIG.get("world") or {}
    if w_spec:
        bg = sc.world.node_tree.nodes["Background"]
        # ONE AUTHORITY FOR THE HOUR, THROUGH A LINKED SOCKET.
        # A world whose sky is a NODE GRAPH rather than a constant cannot take the rig's
        # colour in `Background.Color` — the link would win and the rig would be silently
        # ignored, which is exactly the failure the `--sky` assert below exists to refuse.
        # So a graph that wants the rig's colour publishes an RGB node named
        # `RIG_SKY_COLOR` and the rig is written THERE. Emberbrook's `emberwake_sky`
        # (tools/emb_dress.py) does this: its flat rig colour is still what every
        # non-camera ray sees, and the sky is the camera half of an Is-Camera-Ray mix.
        # A blend that links the socket and forgets the node FAILS HERE rather than
        # baking the wrong evening.
        _rignode = sc.world.node_tree.nodes.get("RIG_SKY_COLOR")
        _tgt, _where = bg.inputs[0], "Background.Color"
        if bg.inputs[0].links:
            assert _rignode is not None and _rignode.type == 'RGB', (
                "the world's sky colour socket is LINKED and there is no RGB node named "
                "RIG_SKY_COLOR to write the rig's colour into — defaults.lightRig.world."
                "color would be silently ignored and the plate would bake at an hour "
                "nothing states. Rebuild the blend with a sky graph that publishes it.")
            _tgt, _where = _rignode.outputs[0], "RIG_SKY_COLOR (the sky socket is linked)"
        if "color" in w_spec:
            _tgt.default_value = tuple(w_spec["color"]) + (1.0,)
        if "strength" in w_spec: bg.inputs[1].default_value = w_spec["strength"]
        print("  sky    %-12s strength %.2f  color %s  <- %s"
              % (sc.world.name, bg.inputs[1].default_value,
                 tuple(round(c, 2) for c in _tgt.default_value[:3]), _where))
    # THE CENSUS, asserted rather than believed. This grade only works if the light is
    # where the story says it is, and "the lamps carry the town" is a claim about object
    # count and wattage that costs nothing to check and everything to get wrong. The roll
    # is printed IN NAME ORDER because the numbering IS the canon: emb_lamp_00..14 run in
    # the lamplighter's own rounds order, low ground first and closing the ring at the
    # Heartlight, so lighting them by name stages the round for free.
    cen = RIG.get("census") or {}
    if cen:
        pfx = cen.get("lampPrefix", "")
        lamps = sorted((o for o in bpy.data.objects
                        if o.type == 'LIGHT' and o.name.startswith(pfx)), key=lambda o: o.name)
        hearts = [o for o in bpy.data.objects if o.type == 'LIGHT'
                  and o.data.energy >= cen.get("heartlightMinWatts", 1e9)]
        print("  lamps  %d x '%s*'   %s" % (len(lamps), pfx,
              ", ".join("%s %.0fW" % (o.name[len(pfx):], o.data.energy) for o in lamps)))
        print("  heartlight(s) %s" % ", ".join("%s %.0fW" % (o.name, o.data.energy)
                                               for o in hearts))
        if "lamps" in cen:
            assert len(lamps) == cen["lamps"], (
                "lightRig.census: expected %d '%s*' lamps, found %d — the rounds order is "
                "the canon and a missing lamp is a dark door" % (cen["lamps"], pfx, len(lamps)))
        if "heartlights" in cen:
            assert len(hearts) == cen["heartlights"], (
                "lightRig.census: expected %d source(s) over %s W, found %d — Emberbrook is "
                "the rare survivor that still has ONE Heartlight"
                % (cen["heartlights"], cen.get("heartlightMinWatts"), len(hearts)))

# The sky override lands AFTER the rig block so it wins over defaults.lightRig.world.
if SKY_OVR:
    _bg = sc.world.node_tree.nodes["Background"]
    assert (not _bg.inputs[0].links
            or sc.world.node_tree.nodes.get("RIG_SKY_COLOR") is not None), (
        "sky colour socket is LINKED and the graph publishes no RIG_SKY_COLOR node — the "
        "rig's colour would be silently ignored. Build the plate blend with "
        "`emb_dress --key emberwake`.")
    # NOTE what this override does and does not reach when the socket IS linked: strength
    # scales the WHOLE Background, so both halves of an Is-Camera-Ray sky move together
    # and the per-camera `--sky` grade still means what it meant.
    _bg.inputs[1].default_value = float(SKY_OVR)
    print("GRADE OVERRIDE  sky strength -> %.3f" % _bg.inputs[1].default_value)

if LAMPWATTS > 0:
    # A LEVER THAT WAS BUILT ON A HYPOTHESIS AND THEN MEASURED INERT — kept, with its
    # refutation attached, because the flag without this note would re-argue for itself.
    # The hypothesis: square's pools measured poolWarm 0.2593 against a 0.30 bar once
    # emb_pixbox's projection was fixed, so "add the warm side" — raise the roll's wattage.
    # THE PROBE REFUTED IT (watt_probe.py, dressed blend, square, 680 vs 2000 W, pool
    # boxes projected from geometry): poolWarm +0.2628 -> +0.2625, pool median L
    # 47.27 -> 47.31. Tripling the roll moved the pooled ground by NOTHING — the lamps
    # light their posts, not the floor a camera frames, exactly what the gray blockout
    # measured (lightRig.world._why) and now paid for a second time on dressed ground.
    # The ratified remedy was ruling (a): the poolWarm bar moves to square's honest
    # 0.2593, and warmth-vs-cool is spent through per-shot moon ENERGY, never wattage.
    #
    # The 14-lamp roll only. The Heartlight is a STORY number (5200 W) and is not touched
    # here — moving it needs the user, not a bake flag.
    _lamps = [o for o in bpy.data.objects if o.type == 'LIGHT'
              and o.name.startswith((RIG.get("census") or {}).get("lampPrefix", "KEYEMB_lamp_"))]
    assert _lamps, "--lampwatts: no KEYEMB_lamp_* lights in this blend"
    _was = _lamps[0].data.energy
    for _o in _lamps:
        _o.data.energy = LAMPWATTS
    print("LAMP WATTAGE    %d lamps %.0f W -> %.0f W (the roll only; Heartlight untouched)"
          % (len(_lamps), _was, LAMPWATTS))

if MOON > 0:
    _md = bpy.data.lights.new("EMB_moon", 'SUN')
    _md.energy, _md.color, _md.angle = MOON, tuple(MOONCOL), math.radians(0.55)
    _mo = bpy.data.objects.new("EMB_moon", _md)
    sc.collection.objects.link(_mo)
    _mo.rotation_euler = (math.radians(MOONRX), 0.0, math.radians(MOONRZ))
    print("MOON            %.2f W  colour (%.2f,%.2f,%.2f)  zenith %.0f deg (%.0f above "
          "horizon)  az %.0f" % (MOON, *MOONCOL, MOONRX, 90 - MOONRX, MOONRZ))

if ANCHORLIGHT > 0:
    # FIND THE HOUSING, THEN ASSERT — one authority for the position, never two.
    #
    # The map stamps a lantern AT the waystone and emb_dress builds the physical prop; this
    # light must land INSIDE that prop's glass by construction, not beside it by arithmetic.
    # Recomputing the stamped offset here would be a SECOND authority for the same
    # coordinate, and two copies of an offset drift: a lamp whose photons come from 30 cm
    # outside its own glass is a worse defect than the authorless glow this replaces.
    #
    # AND A MISSING HOUSING IS A HARD FAILURE, deliberately. Baking a lampless recipe
    # against a blend that has no lantern in it means the prop and the light have come apart
    # — exactly the state that shipped two plates with an unexplained glow. It must die
    # loudly rather than quietly regress to the old offset. `--anchorlight-legacy` keeps the
    # computed-offset path for archaeology only.
    _house = [o for o in bpy.data.objects if o.type == 'MESH'
              and o.name.startswith("emb_dress_waystone_lanternglass")]
    if _house:
        _vs = [o.matrix_world @ v.co for o in _house for v in o.data.vertices]
        _lx = sum(v.x for v in _vs) / len(_vs)
        _ly = sum(v.y for v in _vs) / len(_vs)
        _lz = sum(v.z for v in _vs) / len(_vs)
        ANCHOR_AT = (round(_lx, 4), round(_ly, 4), round(_lz, 4))
        ANCHOR_ON = _house[0].name
        print("WAYSTONE LANTERN %.0f W placed AT ITS HOUSING '%s' (%.2f, %.2f, %.2f) — the "
              "prop is the authority; this bake did not recompute the stamped offset"
              % (ANCHORLIGHT, ANCHOR_ON, *ANCHOR_AT))
    elif "--anchorlight-legacy" in argv:
        _ways = [o for o in bpy.data.objects if o.type == 'MESH'
                 and o.name.lower().startswith('lm_waystone')]
        assert _ways, "--anchorlight-legacy: no lm_waystone* mesh either"
        _vs = [o.matrix_world @ v.co for o in _ways for v in o.data.vertices]
        ANCHOR_AT = (round(sum(v.x for v in _vs) / len(_vs) + 0.9, 4),
                     round(sum(v.y for v in _vs) / len(_vs) - 0.6, 4),
                     round(max(v.z for v in _vs) + 0.5, 4))
        ANCHOR_ON = "<legacy computed offset — NO PROP>"
        print("WAYSTONE LANTERN %.0f W at the LEGACY computed offset %s — there is no lantern "
              "prop in this blend and this light has no visible author. Archaeology only."
              % (ANCHORLIGHT, ANCHOR_AT))
    else:
        raise AssertionError(
            "--anchorlight %s was requested but NO lantern housing "
            "('emb_dress_waystone_lanternglass*') exists in %s.\n"
            "The prop and the light have come apart: this is the exact state that shipped "
            "two plates with an authorless glow. Rebuild the dressed blend so emb_dress "
            "places the lantern, or pass --anchorlight-legacy if you are deliberately "
            "reproducing an old bake."
            % (ANCHORLIGHT, os.path.basename(bpy.data.filepath or "<unsaved>")))
    _li = bpy.data.lights.new("EMB_waystone_lantern", 'POINT')
    _li.energy, _li.color, _li.shadow_soft_size = ANCHORLIGHT, (1.0, 0.62, 0.28), 0.35
    _lo = bpy.data.objects.new("EMB_waystone_lantern", _li)
    _lo.location = ANCHOR_AT
    sc.collection.objects.link(_lo)
else:
    ANCHOR_AT, ANCHOR_ON = None, None

if GLOW > 0:
    # THE WARM ANCHOR. A lampless frame does not read as night for want of light — it
    # reads GREY for want of warm/cool contrast. Measured: square (14 lamps in frame)
    # brightens beautifully, woodroad (none) marches to neutral as it brightens.
    _ways = [o for o in bpy.data.objects if o.type == 'MESH'
             and o.name.lower().startswith('lm_waystone')]
    for _o in _ways:
        for _slot in _o.material_slots:
            if not _slot.material:
                continue
            _m = _slot.material
            if not _m.name.endswith("_warmanchor"):
                _m = _m.copy(); _m.name = _slot.material.name + "_warmanchor"
                _slot.material = _m
            _b = next((n for n in _m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if _b is None:
                continue
            if "Emission Color" in _b.inputs:
                _b.inputs["Emission Color"].default_value = (1.0, 0.66, 0.30, 1.0)
            if "Emission Strength" in _b.inputs:
                _b.inputs["Emission Strength"].default_value = GLOW
    print("WARM ANCHOR     waystone emissive %.1f on %d mesh(es)" % (GLOW, len(_ways)))

# THE GRADE SNAPSHOT IS TAKEN HERE, WHILE IT IS STILL TRUE. Reading the scene at
# cine.json-write time reports the DEPTH pass — that pass deletes the world and overrides
# every material, so the first run recorded `exposure 0.0, sky 0.0` for a beauty render
# graded 1.00/0.65. A record of the wrong pass is worse than no record.
APPLIED_GRADE = {
    "exposure": sc.view_settings.exposure,
    "viewTransform": sc.view_settings.view_transform,
    "look": sc.view_settings.look,
    "sky": (sc.world.node_tree.nodes["Background"].inputs[1].default_value
            if sc.world and sc.world.use_nodes and "Background" in sc.world.node_tree.nodes
            else None),
    "sunEnergy": (bpy.data.objects.get((RIG.get("sun") or {}).get("object", "")).data.energy
                  if (RIG.get("sun") or {}).get("object")
                  and bpy.data.objects.get((RIG.get("sun") or {}).get("object", "")) else None),
    "moon": MOON or None,
    "moonColor": MOONCOL if MOON > 0 else None,
    "moonZenithDeg": MOONRX if MOON > 0 else None,
    "moonAzimuthDeg": MOONRZ if MOON > 0 else None,
    "warmAnchorGlow": GLOW or None,
    "lampWatts": LAMPWATTS or None,
    "waystoneLanternW": ANCHORLIGHT or None,
    "waystoneLanternAt": ANCHOR_AT,
    "waystoneLanternOn": ANCHOR_ON,
}
print("APPLIED GRADE   exposure %.3f  sky %s  moon %s  anchor %s"
      % (APPLIED_GRADE["exposure"],
         ("%.3f" % APPLIED_GRADE["sky"]) if APPLIED_GRADE["sky"] is not None else "-",
         ("%.2f" % MOON) if MOON else "-", ("%.2f" % GLOW) if GLOW else "-"))

def build_cam(c):
    """The ONLY place a Blender camera is created. Every number comes from the
    solved file, which play3d.html also reads — bake and runtime cannot disagree
    about where a camera stands (supervisor condition 1)."""
    name = "cine_" + c["id"]
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(c["fov"])
    cd.clip_start, cd.clip_end = c["clip"][0], c["clip"][1]
    ob = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(ob)
    ob.location = Vector(c["pos"])
    ob.rotation_euler = (Vector(c["aim"]) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob

_STANDIN_MAT = [None]
_STANDIN_RIG = []                    # [(body, head), ...] built ONCE, then MOVED


def standins(c, cam):
    """DRAFT ONLY. Put 1.7 m matte figures on this shot's own ground at the nearest,
    median and farthest of its solved spawn candidates (feet-level points spread over
    the owned region), so a contact sheet shows how big a character actually reads at
    each end of the frame. Returns the objects so the caller can delete them — a
    stand-in that survived into the next camera would be a prop in the shipped art,
    which is why this is opt-in, draft-only, and cleaned up by its own caller."""
    cands = c.get("spawnCandidates", [])
    if not cands:
        return []
    origin = cam.matrix_world.translation
    fwd = (cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))).normalized()
    ranked = sorted(cands, key=lambda o: (Vector(o["at"]) - origin).dot(fwd))
    ranked = [o for o in ranked if (Vector(o["at"]) - origin).dot(fwd) > 0.01]
    if not ranked:
        return []
    pick = [ranked[0], ranked[len(ranked) // 2], ranked[-1]]
    if _STANDIN_MAT[0] is None:
        m = bpy.data.materials.new("DRAFT_STANDIN")
        m.use_nodes = True
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b is not None:
            # A MATTE FIGURE, NOT A MARKER. Albedo 0.55 neutral-warm, roughness 0.7: it is
            # lit by the town's own night grade, so the sheet answers "is a character
            # READABLE here" and not merely "how many pixels tall is a magenta stick".
            b.inputs["Base Color"].default_value = (0.55, 0.50, 0.46, 1.0)
            if "Roughness" in b.inputs:
                b.inputs["Roughness"].default_value = 0.7
        _STANDIN_MAT[0] = m
    # BUILT ONCE AND MOVED, NEVER ADDED AND REMOVED. Creating and deleting three meshes
    # between cameras invalidates Cycles' scene BVH, and on a 27 M-triangle dressed master
    # that rebuild IS the frame: measured 133 s and 123 s for two 1008x576 / 28 spp draft
    # frames whose actual ray tracing is worth about 12 s. Moving an existing object is an
    # object-transform update instead, so the BVH is built on the first frame only.
    if not _STANDIN_RIG:
        for i in range(3):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.19, depth=1.42, location=(0, 0, -9000))
            body = bpy.context.object
            body.name = "DRAFT_standin_%d" % i
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(0, 0, -9000))
            head = bpy.context.object
            head.name = "DRAFT_standin_%d_head" % i
            for o in (body, head):
                o.data.materials.clear()
                o.data.materials.append(_STANDIN_MAT[0])
            _STANDIN_RIG.append((body, head))
    for i, (body, head) in enumerate(_STANDIN_RIG):
        if i < len(pick):
            p = pick[i]["at"]
            body.location = (p[0], p[1], p[2] + 0.71)
            head.location = (p[0], p[1], p[2] + 1.56)
        else:                                    # park it under the world, out of every frame
            body.location = head.location = (0, 0, -9000)
    return []


def visibility(c, cam):
    """Can this camera SEE the region it owns? Ray-cast the solved probe points
    (character-head height, spread over every owned walk mesh). The map's draft
    cameras were buried INSIDE the cliffs by a fixed standoff and no number in the
    file said so — this is the number that says so."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = cam.matrix_world.translation
    seen = 0
    probes = c.get("probes", [])
    for p in probes:
        tgt = Vector(p)
        vec = tgt - origin
        L = vec.length
        if L < 1e-4: continue
        hit, *_ = sc.ray_cast(dg, origin, vec.normalized(), distance=L - 0.35)
        if not hit: seen += 1
    return (seen / len(probes)) if probes else 0.0, len(probes)

def pick_spawn(c, cam):
    """Bundle-level fallback spawn for this shot: the candidate nearest the region
    centre that the camera can actually see. (The runtime's ?sx&sy&sz arrival from a
    graph edge OUTRANKS this — bundle spawns are the fallback, per the brief.)
    Returned in RUNTIME coords (x, h, -y)."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = cam.matrix_world.translation
    # Test the CHEST and the HEAD, and require both. Head-only testing picked a spawn
    # on the rim road that the runtime rendered fully hidden behind the road's palisade:
    # a 1.4 m fence is transparent to a 1.7 m probe and opaque to a walking character.
    for cand in c.get("spawnCandidates", []):
        p = cand["at"]
        clear = True
        for hgt in (0.85, 1.6):
            tgt = Vector((p[0], p[1], p[2] + hgt))
            vec = tgt - origin
            if vec.length < 1e-4: clear = False; break
            hit, *_ = sc.ray_cast(dg, origin, vec.normalized(), distance=vec.length - 0.4)
            if hit: clear = False; break
        if clear:
            return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)], cand["from"], True
    if c.get("spawnCandidates"):
        p = c["spawnCandidates"][0]["at"]
        return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)], c["spawnCandidates"][0]["from"], False
    return None, None, False

def png_rgb24(depth_floats, w, h, near, rng, path):
    """Pack linear view depth into a 24-bit RGB PNG, top-down, no PIL.
    v = (d-near)/(far-near); n = round(v*0xFFFFFF); R=n>>16, G=(n>>8)&255, B=n&255.
    Zero radiance (no surface hit) = the far plane. Identical encoding to
    depth_bake.py, which is what public/play3d.html's fragment shader decodes."""
    rows = []
    for y in range(h - 1, -1, -1):                       # EXR is bottom-up
        row = bytearray([0])                             # PNG filter type 0
        base = y * w
        for x in range(w):
            v = depth_floats[base + x]
            n = 0xFFFFFF if v <= 1e-6 else max(0, min(0xFFFFFF, round((v - near) / rng * 0xFFFFFF)))
            row += bytes(((n >> 16) & 255, (n >> 8) & 255, n & 255))
        rows.append(bytes(row))
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 6))
        + chunk(b"IEND", b""))

# =============================================================== 1) BEAUTY =====
# The render norm's beauty-set ban does not apply here: these frames ARE the
# shipped art of the scene, not agent self-verification.
result = {}
todo = []
if not GLB_ONLY:
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = SAMPLES
    # Denoising ON for the beauty pass: these frames are the shipped art, and the
    # denoiser buys back most of what halving the sample count costs on a stylized
    # backdrop. (It is explicitly OFF for the depth pass below — a denoised depth map
    # would smear distances across silhouette edges, which is the one thing exact-pixel
    # occlusion cannot tolerate.)
    sc.cycles.use_denoising = True
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    for cid in ids:
        c = CAMS[cid]
        d = os.path.join(ART, cid)
        os.makedirs(d, exist_ok=True)
        bg = os.path.join(d, "bg.png")
        # RESUMABLE: --skip-existing reuses a beauty frame already on disk but still
        # builds the camera, re-probes visibility and bakes the depth map. Skipping the
        # camera outright would ship a background with no occlusion — the one pairing
        # this pipeline exists to make impossible. (A 3.5-minute Cycles frame is worth
        # resuming; a 20-second depth pass is not worth the risk.)
        cam = build_cam(c)
        sc.camera = cam
        vis, nprobe = visibility(c, cam)
        spawn, spawn_from, spawn_vis = pick_spawn(c, cam)
        el = 0.0
        if SKIP_EXISTING and os.path.exists(bg):
            print("REUSE %-14s existing bg.png (depth still baked)" % cid)
        else:
            props = standins(c, cam) if (DRAFT and STANDINS) else []
            sc.render.resolution_x, sc.render.resolution_y = BW, BH
            sc.cycles.samples = SAMPLES
            sc.render.filter_size = 1.5
            sc.render.filepath = bg
            t = time.time()
            with contextlib.redirect_stdout(io.StringIO()):
                bpy.ops.render.render(write_still=True)
            el = time.time() - t
            for o in props:
                bpy.data.objects.remove(o, do_unlink=True)
        result[cid] = {"visibleFrac": round(vis, 4), "probes": nprobe,
                       "spawn": spawn, "spawnFrom": spawn_from, "spawnVisible": spawn_vis,
                       "bgSeconds": round(el, 1)}
        todo.append(cid)
        print("BG   %-14s %5.1fs  probes %d visible %.1f%%  spawn %s (%s)"
              % (cid, el, nprobe, vis * 100, spawn, spawn_from))

# ================================================================ 2) DEPTH =====
if todo and DRAFT:
    print("DRAFT MODE: %d beauty frame(s) in %s — depth, GLB and cine.json SKIPPED"
          % (len(todo), os.path.relpath(OUT, REPO) if OUT.startswith(REPO) else OUT))
    todo = []
if todo:
    # Delete render-only volumes FIRST: under an emission override a fog domain
    # becomes a solid emissive box, i.e. a slab of fake depth hanging in the air.
    VL = set(bpy.context.view_layer.objects.keys())
    for o in list(bpy.data.objects):
        if o.type != 'MESH': continue
        n = o.name.lower()
        if (('fog' in n) or ('haze' in n) or ('steam_vol' in n) or ('smoke' in n)
                or ('shadow_ceiling' in n) or (o.name not in VL)):
            bpy.data.objects.remove(o, do_unlink=True)

    dm = bpy.data.materials.new("DEPTH_OVERRIDE"); dm.use_nodes = True
    nt = dm.node_tree; nt.nodes.clear()
    n_geo = nt.nodes.new('ShaderNodeNewGeometry')
    n_xf = nt.nodes.new('ShaderNodeVectorTransform')
    n_xf.vector_type = 'POINT'; n_xf.convert_from = 'WORLD'; n_xf.convert_to = 'CAMERA'
    n_sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    # Cycles' shader-space camera transform has +Z pointing INTO the scene (opposite
    # of Blender's object-space convention): negate-and-clamp renders black,
    # ABSOLUTE is correct in both (manifest 64).
    n_abs = nt.nodes.new('ShaderNodeMath'); n_abs.operation = 'ABSOLUTE'
    n_em = nt.nodes.new('ShaderNodeEmission'); n_em.inputs['Color'].default_value = (1, 1, 1, 1)
    n_out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(n_geo.outputs['Position'], n_xf.inputs['Vector'])
    nt.links.new(n_xf.outputs['Vector'], n_sep.inputs['Vector'])
    nt.links.new(n_sep.outputs['Z'], n_abs.inputs[0])
    nt.links.new(n_abs.outputs['Value'], n_em.inputs['Strength'])
    nt.links.new(n_em.outputs['Emission'], n_out.inputs['Surface'])
    bpy.context.view_layer.material_override = dm

    w = bpy.data.worlds.new("DEPTH_WORLD"); w.use_nodes = True
    for nd in w.node_tree.nodes:
        if nd.type == 'BACKGROUND': nd.inputs['Strength'].default_value = 0.0
    sc.world = w
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.view_settings.view_transform = "Standard"       # depth is DATA, never graded
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.filter_size = 0.01                       # no AA: never blend depths across edges
    sc.render.resolution_x, sc.render.resolution_y = DW, DH
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'

    for cid in todo:
        c = CAMS[cid]
        sc.camera = bpy.data.objects["cine_" + cid]
        exr = os.path.join(ART, cid, "_depth_raw.exr")
        sc.render.filepath = exr
        t = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(exr)
        px = list(img.pixels)
        dd = [px[i] for i in range(0, len(px), 4)]
        hit = [v for v in dd if v > 1e-6]
        near, far = (min(hit), max(hit)) if hit else (0.1, 100.0)
        rng = max(far - near, 1e-6)
        png_rgb24(dd, DW, DH, near, rng, os.path.join(ART, cid, "depth.png"))
        bpy.data.images.remove(img)
        os.remove(exr)
        # RUNTIME CLIP, derived: the fragment shader turns view depth into clip depth
        # through the RUNTIME camera's projection, so its near/far only have to
        # bracket the baked range. Bracketing it TIGHTLY instead of using Blender's
        # 0.05..1400 buys back the depth precision the character is z-tested with.
        rt_near = max(0.05, near * 0.5)
        rt_far = far * 1.6
        result[cid].update({"depth": {"near": near, "far": far, "width": DW, "height": DH,
                                      "encoding": "rgb24-viewz"},
                            "rtClip": [round(rt_near, 4), round(rt_far, 3)],
                            "depthSeconds": round(time.time() - t, 1)})
        print("DPT  %-14s %5.1fs  range %.2f .. %.2f  rtClip %.2f..%.1f"
              % (cid, time.time() - t, near, far, rt_near, rt_far))

# ================================================================== 3) GLB =====
if GLB_ONLY:
    bpy.context.view_layer.material_override = None
    # A CAMERA-RAY-ONLY OBJECT IS A BACKDROP, AND A BACKDROP IS NOT COLLISION.
    # `visible_camera` alone used to mean "in the world", and it stopped meaning that the
    # moment a town shipped geometry that ONLY the camera may see: Emberbrook's
    # `far_horizon` ridge ring is 300-490 m out, is set visible to camera rays and to no
    # other ray precisely so it cannot enter the town's light transport — and this filter
    # would have written it into the SHARED COLLISION BUNDLE, where walkGround, the BVH
    # and every ray the runtime casts would have taken it for world. The rule the
    # ray-visibility mask already states is the right one: if nothing but the camera may
    # see it, it is a picture, not a place.
    nback = 0
    for o in list(bpy.data.objects):
        if o.type != 'MESH': continue
        if o.name.startswith('walk_'): continue        # collision pads: hide_render by design
        backdrop = (o.visible_camera and not o.visible_diffuse
                    and not o.visible_glossy and not o.visible_shadow)
        if backdrop:
            nback += 1
        if (not o.visible_camera) or o.hide_render or o.hide_viewport or backdrop:
            bpy.data.objects.remove(o, do_unlink=True)
    if nback:
        print("GLB     %d camera-ray-only backdrop mesh(es) dropped from the collision "
              "bundle (visible_camera with no diffuse/glossy/shadow visibility is a "
              "picture, not a place)" % nback)
    # ===== WHY THIS EXPORT USED TO NEVER FINISH, AND THE ONE LINE THAT FIXES IT =====
    # MEASURED, not guessed (2026-08-07): `--glb` against the DRESSED Emberbrook master was
    # run three times by an earlier lane and reaped at 26, 32 and 33 minutes without
    # completing. A 20-minute `sample(1)` of the fourth run says where every second went:
    # **5776 of 5776 main-thread samples were inside `gc_collect_main`** — CPython's CYCLIC
    # GARBAGE COLLECTOR — reached through `_Py_HandlePending` from inside the glTF
    # exporter's own operator, with `deduce_unreachable` / `subtype_traverse` /
    # `visit_decref` under it. Not glTF, not Blender, not the geometry: the GC.
    #
    # The mechanism is the exporter's shape meeting CPython's policy. The exporter builds
    # tens of millions of small Python objects (per-primitive dicts, per-attribute lists),
    # and a generational collection is triggered by ALLOCATION COUNT while its cost is
    # O(LIVE SET). So the more of the scene it has already built, the more expensive every
    # subsequent collection is, and it keeps re-walking the same live graph: the run does
    # not hang, it goes quadratic. A 27 M-triangle town is simply the first scene here big
    # enough for that to pass a work window.
    #
    # `gc.freeze()` moves everything already alive into a permanent generation that is
    # never traversed, and `gc.disable()` stops collections for the duration. Reference
    # counting still frees everything acyclic, which is nearly all of what the exporter
    # makes; the trade is peak memory for a run that terminates. Restored afterwards.
    import gc
    _gcwas = gc.isenabled()
    gc.collect()
    gc.freeze()
    gc.disable()
    _t_glb = time.time()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                                      export_yup=True, export_cameras=False,
                                      export_lights=False)
    finally:
        gc.unfreeze()
        if _gcwas:
            gc.enable()
    print("GLB     export_scene.gltf %.1fs with the cyclic GC frozen+disabled (see the "
          "note above: 5776/5776 sampled main-thread frames of the un-frozen run were in "
          "gc_collect_main)" % (time.time() - _t_glb))
    n_walk = sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('walk_'))
    json.dump({"exported": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "source": MASTER,
               "tool": "tools/cine_bake.py --glb",
               "walkMeshes": n_walk,
               "note": "SHARED collision for every cinematic camera of %s. "
                       "The art (background + depth per camera) lives in cameras/<id>/ "
                       "and is indexed by cine.json." % S["sceneKey"]},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    print("GLB OK  walk=%d  %.1fs" % (n_walk, time.time() - T0))

# ------------------------------------------------------- 4) cine.json (merge) --
# Merged, not overwritten, so a PARTIAL re-bake is a first-class operation: the
# quay-market tier is under another agent's custody tonight and its three shots get
# re-baked alone once it lands (staleness is the only risk — bakes are read-only).
if result and DRAFT:
    json.dump({"draft": True, "rendered": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "plateSource": os.path.relpath(bpy.data.filepath, REPO) if bpy.data.filepath else None,
               "res": [BW, BH], "samples": SAMPLES, "standins": bool(STANDINS),
               "appliedGrade": APPLIED_GRADE,
               "cameras": {cid: {"pos": CAMS[cid]["pos"], "aim": CAMS[cid]["aim"],
                                 "fov": CAMS[cid]["fov"], "dist": CAMS[cid].get("dist"),
                                 "charPxNear": CAMS[cid].get("charPxNear"),
                                 "charPxFar": CAMS[cid].get("charPxFar"),
                                 "visibleFrac": result[cid]["visibleFrac"],
                                 "bgSeconds": result[cid]["bgSeconds"]} for cid in result}},
              open(os.path.join(OUT, "draft.json"), "w"), indent=1)
    print("DRAFT %d frame(s) + draft.json -> %s" % (len(result), OUT))
if result and not DRAFT:
    p = os.path.join(OUT, "cine.json")
    doc = json.load(open(p)) if os.path.exists(p) else {}
    doc.setdefault("_doc", [
        "BAKED CINEMATIC CAMERAS for %s — what tools/cine_bake.py actually" % S["sceneKey"],
        "rendered, per camera. GENERATED; the authored intent is",
        "public/townmap/%s.cameras.json and the solved numbers are" % TOWN,
        "public/townmap/%s.cameras.solved.json (this file must agree with it —" % TOWN,
        "tools/cine_test.mjs asserts every link of that chain).",
        "public/play3d.html builds its THREE.PerspectiveCamera from pos/aim/fov/rtClip",
        "here, and its depth quad from depth.near/far + cameras/<id>/depth.png, so the",
        "shipped image and the shipped occlusion come from one bake of one camera.",
        "pos/aim are MAP/Blender coords [x, y, h]; spawn is RUNTIME [x, h, -y].",
    ])
    doc["sceneKey"] = S["sceneKey"]
    doc["generator"] = "tools/cine_bake.py"
    # WHICH BLEND THE PICTURE CAME OUT OF, recorded because it is no longer the same blend
    # the collision came out of. meta.json's `source` describes the --glb pass (the master,
    # whose walk_ meshes ARE the town's collision); Emberbrook's ART bakes from the DRESSED
    # plate-tier build, which is derived from that master and never committed. Two artifacts
    # with two provenances in one bundle is a fact a reader has to be able to check, so it
    # is written from `bpy.data.filepath` — the blend actually open — and not from a
    # constant that would keep saying "master" no matter what was rendered.
    doc["defaults"] = {"aspect": D["aspect"], "charH": D["charH"],
                       "exposure": D["exposure"], "view_transform": D["view_transform"],
                       "look": D["look"], "beautyRes": [BW, BH], "samples": SAMPLES,
                       "denoised": True,
                       "plateSource": os.path.relpath(bpy.data.filepath, REPO)
                                      if bpy.data.filepath else None}
    # THE HOUR ACTUALLY RENDERED, per bake. The recipe forks per shot (lamp-bearing shots
    # take a modest moon; lampless ones take a strong moon and a warm anchor), so a single
    # file-level grade can no longer describe the bundle. Written per CAMERA below as well,
    # because two shots in this bundle are now legitimately lit differently and a reader
    # must be able to tell which is which without re-deriving it.
    doc["defaults"]["appliedGrade"] = APPLIED_GRADE
    cams = {c["id"]: c for c in doc.get("cameras", [])}
    for cid in todo:
        c, r = CAMS[cid], result[cid]
        cams[cid] = {
            "id": cid, "name": c["name"], "entry": c.get("entry", False),
            "transit": c.get("transit", False),
            "pos": c["pos"], "aim": c["aim"], "fov": c["fov"], "clip": c["clip"],
            "rtClip": r.get("rtClip"), "depth": r.get("depth"),
            "art": {"bg": "cameras/%s/bg.png" % cid, "depth": "cameras/%s/depth.png" % cid},
            "spawn": r.get("spawn"), "spawnFrom": r.get("spawnFrom"),
            "visibleFrac": r.get("visibleFrac"), "probes": r.get("probes"),
            "baked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seconds": round((r.get("bgSeconds") or 0) + (r.get("depthSeconds") or 0), 1),
            # THE HOUR THIS PLATE WAS ACTUALLY RENDERED AT. The defaults-level appliedGrade
            # is last-writer-wins — one bare bake after a lantern bake and the shared record
            # described the wrong pass for every other camera. The per-shot floor pass makes
            # grades legitimately DIFFER per plate, so each camera carries its own.
            "appliedGrade": APPLIED_GRADE,
        }
    # stable order = the solved file's order (the player's route down the town)
    doc["cameras"] = [cams[c["id"]] for c in S["cameras"] if c["id"] in cams]
    json.dump(doc, open(p, "w"), indent=1)
    # The hub's card thumbnails read <bundle>/stylized.png, the same path every other
    # scene uses. A cinematic bundle has no single background, so the ENTRY shot stands
    # for the town — one copy, so nothing downstream has to learn about cameras/.
    entry = next((c for c in S["cameras"] if c.get("entry")), S["cameras"][0])
    src = os.path.join(ART, entry["id"], "bg.png")
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(OUT, "stylized.png"))
        print("stylized.png <- the entry shot (%s), for the hub thumbnail" % entry["id"])
    print("cine.json updated: %d of %d cameras baked (%s)"
          % (len(doc["cameras"]), len(S["cameras"]), ",".join(todo)))
print("CINE BAKE DONE %.1fs" % (time.time() - T0))
