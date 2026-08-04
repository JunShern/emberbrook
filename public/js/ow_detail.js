// ow_detail.js — THE OVERWORLD'S NEAR-FIELD GROUND: a clumped tuft scatter that follows
// the camera, a fringe band along every seam, and the shared FOLIAGE MATERIAL.
//
// WHY IT IS RUNTIME AND NOT IN THE BUNDLE. Both halves are camera-relative. The refs
// (public/assets/refs/reimagine_ff9_overworld_{1,2,3}.jpg) carry blade geometry from the
// bottom of frame past the character; ours stopped a few metres in, so the meadow changed
// species mid-frame. Baking that density into ow-valley's GLB is not an option — the
// player walks the whole 280x200u region, so "dense wherever the player is" as static
// geometry is dense EVERYWHERE, which at the ~45/m2 this needs is millions of triangles in
// a 45 MB bundle. Placed against the live camera instead it costs no bytes at all, and the
// falloff can have the shape the refs have (thick at the near edge, thinning with depth)
// rather than the shape a static scatter can afford.
//
// ============================ FOLIAGE ROUND 1 (2026-08-04) ============================
// The blind foliage critic's thesis, and every change below is one clause of it:
//   "The references' vegetation is a POPULATION OF INDIVIDUAL CLUMPED PLANTS that breaks
//    every silhouette and every seam, and ours is a SURFACE TREATMENT APPLIED TO TERRAIN —
//    which is why nothing of ours reads as growing anywhere."
//
// WHAT THE PICTURE SHOWED WHEN THE OBJECTS WERE TURNED OFF ONE AT A TIME (id-*.png,
// scratchpad/f1). The near-field "grass" the critic was judging IS NOT THIS CARPET. It is
// `ow_f2_tuft`, 108 744 static triangles in the bundle, and with it hidden the frame loses
// every pale spiked clump in the meadow: they read as AGAVE, not turf. This carpet was
// underneath it the whole time at 173 423 blades of 0.085-0.235 m — ankle height on a 1.45u
// character — and contributed a fine grain you have to be told to look for. Two lessons in
// one A/B: (a) ASK WHICH OBJECT SUPPLIES THE PIXELS BEFORE TUNING ANYTHING (LOOP.md r14),
// (b) a carpet sized so it cannot break a silhouette is a texture with extra triangles.
//
// AND THE SHEEN WAS NOT THE ENVIRONMENT. Before sweeping the material the wire was checked:
// envMapIntensity = 0 on EVERY foliage material moves the bush box by 0.1/255 and the tuft
// field by 0.4/255. The "wet plastic" read is not specular at all — it is a PALE, NARROW-HUE
// albedo with a near-black interior, lit by a warm key. So the material work here is a
// translucency term, a highlight DESATURATION clamp, and an albedo value->hue remap; the
// specular knob was left alone because it was measured and it was not connected to the
// complaint. (Eighth disconnected knob avoided rather than swept — see LOOP.md r14.)
//
// THE SCATTER IS NOW TUFTS, NOT BLADES. A blade placed independently per triangle is an even
// lawn no matter what the density field does, because the eye reads the ROOT SPACING. Blades
// are drawn 3-5 to a root point inside a 5-16 cm radius, sharing that tuft's height scale,
// hue draw and species — which is what makes a clump occlude itself and carry one identity.
//
// THE FRINGE IS THE HIGHEST-PAYOFF HALF AND IT IS A DISTANCE FIELD. Every hard seam in the
// frame (road edge, water line, rock foot, building footing, bush base) is a cell where the
// grass primitive meets something else. Those are rasterised ONCE into a 0.6 m occupancy
// grid and chamfer-transformed, so `fringe(x,z)` is a metre distance any placement rule can
// read. Density multiplies up inside the band, a share of the tufts are pushed OUT along the
// field's own gradient so they stand IN the dirt, and the seam stops being a line.
//
// WHAT IT IS NOT. It is CONTENT — geometry and materials. No fog, no AO, no bloom, no
// grading, no tone curve: those belong to the post-processing lane and nothing here may
// touch them (scope seam ratified 2026-08-04, docs/qa/ow-refs/LOOP.md). The one edit that
// sits near that seam is the highlight desaturation, and it is deliberately PER-MATERIAL
// (foliage only) rather than a curve on the frame.
//
// THE TREE LANE OWNS THE CANOPY ALBEDO. tools/foliage_atlas.py and the canopy/leaf textures
// are not touched here. The SHARED terms (translucency, highlight clamp, roughness) are
// applied to the canopy too because they are one shader edit by design; the albedo value->hue
// REMAP is applied only to the materials this lane owns, so the two lanes cannot fight over
// the same pixels.
//
// COLLISION. Every mesh it adds is veg_-prefixed and is only ever scene.add()ed — never
// pushed into play3d's collide / walkRef / allMeshes, which are built once from the bundle.
// Both are needed: the name is what keeps it out if this is ever baked into a GLB. Verify
// in the ENGINE (tools/walk_engine_gate.mjs --scene ow-valley), never in the file.
//
// window.OWD — the instrument:
//   OWD.state()          counts, budget, last rebuild ms, current params
//   OWD.set({...})       any of the tunables below, then rebuilds
//   OWD.rebuild(force)   place the scatter at the player's current position
//   OWD.enable(false)    tear the scatter down (materials stay patched)
//   OWD.occ()            the fringe field's own census — cells, occupied, ms
(function () {
  'use strict';

  // play3d.html is a classic script: its top-level const/let live in the shared global
  // lexical scope and are readable from here, but a missing one is a ReferenceError.
  var TH = function () { try { return THREE; } catch (e) { return window.THREE; } };
  var SCN = function () { try { return scene; } catch (e) { return null; } };
  var SKEY = function () {
    var s = null; try { s = SCENE; } catch (e) {}
    return s || new URLSearchParams(location.search).get('scene') || '';
  };

  var GROUP = 'veg_owd';
  var ON = true, MESHES = [], SRCS = null, LASTMS = 0, LASTAT = null, LASTT = 0, NBLADE = 0;
  var PATCHED = {};

  // ---- tunables -----------------------------------------------------------------
  var P = {
    // ---- the disc ----------------------------------------------------------------
    r0: 15,          // full density radius
    r1: 74,          // zero at this radius — set by the FRAME, not by taste: at boom 40 /
                     // pitch 0.61 the meadow still fills the top of the plate at 60 m, and
                     // a fade that ends inside the picture is a fade the player can SEE
                     // end, which is the whole deficit ("the blade layer visibly stops").
    tail: 1.30,      // falloff exponent; >1 keeps tufts far out at low density
    budget: 230000,  // hard BLADE cap — a safety valve, see rebuild()
    step: 9.0,       // rebuild once the player has moved this far
    minMs: 700,      // ...and never more often than this (see rebuild)

    // ---- the tuft ----------------------------------------------------------------
    // ROOT POINTS PER SQUARE METRE, not blades. 9.5 inside r0 is a 0.32 m mean spacing,
    // the dense end of the reference's 0.3-0.6 m, and the bare gaps come from the clump
    // threshold rather than from thinning the whole field.
    tuftDens: 11.4,
    bptMin: 4, bptMax: 7,   // blades per root point
    tuftR: 0.070,           // how far a blade's root may sit from the tuft centre (m)
    // HEIGHT: r3's carpet read at the waist and was cut for it; R6's replacement read at
    // the ankle and could not break a silhouette. Knee on a 1.45u character is ~0.40 m,
    // and hMax x the height jitter's ceiling lands there. Power-distributed so the mass
    // sits short and a thin tail of tall blades breaks the top edge up.
    // hPow 1.85 put the MASS of the distribution on top of hMin: median height came out
    // 0.176 m against a 0.115-0.335 range, so most blades were the same short blade and the
    // tall ones were a thin garnish. At a grazing camera that mass is a flat even mat, which
    // is what "even ranks, identical heights" describes. 1.40 keeps the short bias (a lawn
    // is not a wheat field) while putting real spread in the middle of the range.
    hMin: 0.105, hMax: 0.360, hPow: 1.40,
    sizeJit: 0.35,   // +-35% on WIDTH (0.65..1.35), and half of that on height: a blade
                     // scaled 1.4x tall is a different plant, 1.4x wide is the same plant
                     // seen closer, and only one of those is what "size jitter" should buy.
    grow: 0.16,      // extra height per r1 of distance — far blades read at fewer pixels.
                     // CUT from 0.25: height was never the axis that was failing (a blade
                     // still measured 7.9 px tall at 30 m), and growing the far ones while
                     // the field around them thinned is what made the survivors read as
                     // "isolated sprigs, each too large for its distance".
    // ---- THE ANGULAR WIDTH FLOOR — the actual fix for the mid-distance collapse --------
    // MEASURED AT THE CLOSEUP CAMERA (scratchpad/f2/probe2.js, 1840 screen rays against the
    // running game, camera 7.25 m behind the player at pitch 0.18). Per 10 m band of camera
    // distance, mean live root density and mean blade size in PIXELS:
    //
    //     dCam      0-10   10-20  20-30  30-40  40-50  50-60
    //     roots/m2  3.49   8.12   4.38   4.52   4.52   5.87
    //     spacing   0.63   0.41   0.62   0.56   0.63   0.48   m
    //     blade H   28.1   19.6   11.2    7.9    6.6    5.5   px
    //     blade W   5.11   3.52   1.94   1.33   1.08   0.87   px
    //
    // THE DENSITY NEVER COLLAPSED. Roots hold at ~4.5/m2 and 0.6 m spacing all the way out;
    // `fall` is only down to 0.56 at 40 m. What collapses is the WIDTH OF ONE BLADE: 0.036 m
    // of grass is 5.1 px at the player's feet and 1.1 px at 40 m, and a blade thinner than a
    // pixel does not half-cover that pixel — it either wins the sample or vanishes. Past
    // ~30 m the whole population was rendering as an aliased stipple over the terrain
    // texture, which is why the frame reads as "bare terrain with roughly eight isolated
    // sprigs" while 10 600 blade roots stand inside that very region.
    //
    // So the mid band is bought with COVERAGE PER PLANT, not with more plants: widen a blade
    // with distance so its apparent width holds near two pixels, and pay for it out of blade
    // COUNT (farThin). This is ordinary grass LOD and it is self-limiting — a blade at 60 m
    // scaled 2.3x subtends the same two pixels a near blade does, so it cannot look like a
    // leaf on screen; it only looks wrong if you fly out and stand next to it, and the disc
    // ends at r1 before that. The near field is untouched by construction (gain is 1 inside
    // r0), so r3's "field of corn" cannot come back through this door.
    wgrow: 1.55,     // extra WIDTH at r1, on top of 1.0 — 1.08 px at 40 m becomes ~2.0 px
    wgrowP: 0.80,    // shaping exponent: <1 spends the gain early, where the collapse is
    lean: 0.38,      // radians of random lean about a random horizontal axis
    seedFrac: 0.12,  // share of blades drawn as the seed-head variant
    shortFrac: 0.52, // ...as the short broad variant; the rest are the medium blade
    farThin: 0.72,   // blades per tuft are cut by this fraction at r1 — a far tuft needs a
                     // ROOT (that is what serrates a silhouette) and not four cards. The
                     // first build at tuftDens 12 hit the 230k valve, and the valve loses
                     // one SIDE of the disc rather than thinning evenly, so the far field
                     // is thinned on purpose instead of being truncated by accident.
    wide: 0.0138,    // blade half-width at the base, before the per-variant multiplier.
                     // 0.030 x the short variant's 1.30 gave a 7.8 cm leaf: at the low
                     // camera the field read as CORN, which is the exact word the critic
                     // used for r3. A grass blade is a few millimetres wide and the thing
                     // that makes it read is the ASPECT RATIO, not the height.

    // ---- where it grows -----------------------------------------------------------
    slope: 0.62,     // reject triangles whose normal.y is below this (no grass on cliff)
    // THE FIELD MUST THIN TO BARE EARTH. Two octaves of world-space value noise, then a
    // THRESHOLD: below `bare` the density is zero, not small. A carpet that only thins
    // still covers everything, and "covers everything" is the surface-treatment read.
    clumpM: 5.5,     // metres per clump cell
    bare: 0.36,      // clump value below which the ground is left bare
    clumpP: 0.80,    // shaping exponent above the threshold
    clumpH: 0.40,    // how much of the same field the tuft HEIGHT follows
    // ---- THE SLOT BOUNDARY: a density step that lay exactly on a polygon edge ----------
    // The terrain is ONE mesh with PER-FACE material slots (overworld3_build.py:306 assigns
    // grass/dry/rock by `material_index`), so the grass/dry line is a chain of triangle
    // edges — dead straight, and running through open ground. r1 put a CONSTANT 0.48x
    // density on the dry slot, which laid a 2x density step precisely along that straight
    // line: "a visible grid... terminating in a straight-line rectangle boundary against
    // dirt with no density falloff". Hiding it under more dry vegetation was r1's plan and
    // the judge found it anyway, blind.
    // THE FIX IS TO STOP THE SLOT DECIDING THE DENSITY. Both slots now draw their weight
    // from the SAME range [dryDens, 1], and where in that range a given spot lands is
    // decided by `slotAt` — a rotated noise field that knows nothing about the polygon
    // edge. The slots only BIAS which end they tend toward, and the bias is small enough
    // that the two distributions overlap heavily. There is still a dry slope and a green
    // one, because the TINT still follows the slot (dryTint/dryBias); what no longer
    // follows the slot is the count, so the edge has nothing to draw itself with.
    slotM: 11.0,     // metres per cell of the slot-blend field — wider than clumpM, so it
                     // reads as ground changing character rather than as more clumping
    slotBias: 0.14,  // how far each slot is pushed toward its end of the range
    dryDens: 0.48,   // FLOOR of that shared range (was a flat multiplier on DRY). THE
                     // SLOT BOUNDARY BECAME VISIBLE the moment only one slot had plants on
                     // it: the grass/dry split is a polygon edge, and at 0.30 the gate plate
                     // showed straight-edged green patches where before both sides were
                     // equally bare. Vegetation on both slots is what hides a seam the
                     // terrain has always had. (worn slopes are
                     // not bare dirt in the references — they carry ochre grass.)
    crestK: 0.85,    // extra density where the ground is already sloping, which is where
                     // vegetation is seen against a backdrop rather than from above

    // ---- the fringe ----------------------------------------------------------------
    fringeD: 1.30,   // width of the dense band along every seam, metres
    fringeK: 2.6,    // density multiplier at the seam itself
    fringeH: 0.22,   // ...and how much taller the band's tufts are
    stray: 0.30,     // share of fringe tufts pushed OUT past the seam, into the dirt
    strayMax: 0.32,  // how far out (m). The reference has no hard seam anywhere — but the
                     // first build added `fd` to this and let a third of the band's tufts
                     // travel up to 1.3 m onto the road, which is not a fringe: the plate
                     // showed CONFETTI scattered across the whole path. A straggler is a
                     // plant that has crossed the edge, so it must stay near the edge, be
                     // rarer than the band it comes from, and be SHORT (it gets trodden).
    strayFr: 0.45,   // ...and only tufts already this deep in the band may stray
    strayH: 0.62,    // how tall a straggler is against its own tuft
    strayLift: 0.30, // the most a straggler may be lifted onto the surface it crossed
                     // onto (see occTop). A road ramp, a dock plank and a bedding ring
                     // are all proud of their terrain by 0.02-0.25 m; a roof is not a
                     // surface anything walked onto.
    occCell: 0.6,    // fringe field resolution, metres

    // ---- colour -----------------------------------------------------------------
    lift: 1.14,      // tuft tint vs the ground it stands in, AFTER the texture mean is
                     // folded in (see texMean). MEASURED and it is a finding: raising this
                     // barely moves frame luminance — the carpet darkens a frame by
                     // COVERAGE, not by albedo. Chase L back through density and exposure.
    jitV: 0.30,      // per-TUFT value jitter width
    jitH: 0.20,      // per-TUFT hue jitter width (green <-> amber)
    jitB: 0.10,      // per-BLADE jitter inside a tuft — small, or a clump stops being one
    dryFrac: 0.20,   // share of tufts drawn DRY (ochre). The references' vegetation is
                     // 15-25% NON-GREEN overall and ours was one green family.
    dryTint: [1.20, 0.95, 0.44],
    dryBias: 1.9,    // ...and dry tufts are this much likelier on worn/fringe ground
    // OCHRE ON SAND IS CAMOUFLAGE. r1 drew 55-90% of the tufts on the DRY slot in the dry
    // tint, and the dry slot's ground is itself sand-coloured — so on the one slope the
    // blind judge called "bare terrain texture", the plants that were standing there had
    // almost no hue or value contrast against the dirt behind them. Density was never going
    // to fix that: an invisible plant at twice the count is still invisible. Cutting the
    // floor to a third puts GREEN tussocks on the worn slope, which is also what the
    // references show — a dry hillside is green clumps in ochre ground, not ochre in ochre.
    dryOnDry: 0.42,  // floor on the dry share for tufts standing ON the dry slot
    // ...AND CUTTING THAT SHARE ALONE MADE IT WORSE, which is the finding. A tuft takes its
    // base colour from the COLOR_0 of the ground UNDER it (see texMean — deliberate, so the
    // scatter is never a different green from its own ground). On the dry slot that base is
    // sand, so a "not dry" tuft there is not green: it is PALE SAND, and dropping dryOnDry
    // to 0.34 simply traded ochre-on-sand for sand-on-sand and the slope got fainter, not
    // greener. Measured by eye at the closeup, and it is the same shape of error as r1's
    // disconnected-knob list: the term I reached for was not wired to the thing I wanted.
    // A worn slope needs plants that DISAGREE with it, so the non-dry share on dry ground is
    // tinted green explicitly rather than inheriting the sand.
    grassOnDry: [0.64, 1.04, 0.56],

    // ---- flowers -----------------------------------------------------------------
    // Three species, in PATCHES, biased to transitions. Never mid-lawn: a flower on open
    // ground is confetti, a flower at a path shoulder or a bush base is a plant.
    // AND THEY DID NOT READ. r1 shipped them and the blind judge saw none, in either frame;
    // MEASURED at the closeup camera, 793 heads existed in the disc and TWELVE were on
    // screen. Two causes, both wiring: (1) `flPer` is a per-tuft probability, and tuft count
    // grows with the ANNULUS AREA, so 62% of the heads landed 30-50 m out where a 6 cm head
    // is 2 px — the population was real and spent almost entirely where it could not be
    // seen; (2) the head is 4 triangles 6 cm across and `vs.set(1, fh, 1)` scaled only Y, so
    // unlike a blade it got no size compensation at all. Flowers are pulled INWARD, made
    // bigger, and given the same angular width floor the blades now get.
    flowers: 1.0,    // master scale, 0 = off
    flPatchM: 13.0,  // metres per flower-patch cell
    flPatchT: 0.52,  // patch threshold — above this the patch may flower
    flPer: 0.115,    // heads per tuft inside a patch at full density
    flNear: 2.4,     // ...multiplied by up to this at the player and 1.0 at r1. THE ONE
                     // TERM THAT MOVES THEM INTO THE PICTURE: without it the per-tuft
                     // probability spends the whole budget on the far annulus.
    flFringe: 2.2,   // ...multiplied by this inside the fringe band
    flH: 0.205,      // stem height — a head that does not clear the blades around it is a
                     // head nobody sees, and hMax went up this round too
    flW: 1.35,       // head width scale at r0, before the distance gain

    // ---- ROUND 3: the two new ground assets ----------------------------------------
    // They get their OWN density fields, not a share of the grass's. A second species
    // scattered on the first one's mask is the first species in a different shape: the
    // patches have to land somewhere the grass patches are not, or the hillside is still
    // one population. Each field has its own rotation angle and its own scale (see
    // weedAt/sedgeAt), so a weed patch, a sedge stand and a grass clump have no edges
    // in common.
    //
    // THE WEED IS A PLANT OF DISTURBED GROUND — path shoulders, house bedding, the foot
    // of a rock — which is exactly where `fringe` already knows how to point. So the
    // fringe boost is bigger than the grass's, and mid-lawn it is rare.
    weed: 1.0,       // master, 0 = off
    weedM: 17.0,     // metres per weed-patch cell
    weedT: 0.44,     // patch threshold
    weedPer: 0.105,  // per-tuft probability inside a patch at full density
    weedFringe: 2.3, // ...and this much likelier inside the fringe band
    weedNear: 2.0,   // ...at the player, falling to 1.0 at r1 (the flNear lesson: a
                     // per-tuft probability spends itself on the far annulus by
                     // arithmetic alone, because tuft count grows as the AREA)
    weedS: 0.225,    // leaf length (m); the rosette spans ~1.7x this and stands ~0.85x
    weedJ: 0.34,     // +-34% size jitter
    // THE SEDGE IS A PLANT OF HELD WATER. There is no moisture field here and inventing
    // one would be a system for one asset, so it rides two things that already exist and
    // correlate with it: the GREEN slot (the terrain builder put the dry slot on the worn
    // slopes, which is where water does not sit) and low `crest` (flat ground, not a
    // shoulder). It is the one asset that gets RARER toward the dry slope, which is what
    // makes the two slopes read as different GROUND rather than as one ground at two
    // tints — f2's own unfinished business.
    sedge: 1.0,
    sedgeM: 23.0,
    sedgeT: 0.52,
    sedgePer: 0.085,
    sedgeDry: 0.28,  // multiplier for a sedge standing on the DRY slot
    sedgeFlat: 1.7,  // ...and this much likelier on flat ground than on a shoulder
    sedgeNear: 1.7,
    sedgeS: 0.46,    // crown height (m)
    sedgeJ: 0.36,

    // ---- the bundle's own tufts ----------------------------------------------------
    // `ow_f2_tuft` is the pale spiked clump the critic was judging. It is a bundle asset
    // this lane cannot rebuild tonight, so it is DITHERED OUT of the band where this
    // scatter is dense and left standing beyond it, where it still serrates a far hillside
    // and its species is not readable. tuftFade = 0 restores it everywhere.
    tuftFade: 1.0, tuftFadeA: 20.0, tuftFadeB: 66.0,

    // ---- the shared foliage material ------------------------------------------------
    rough: 0.90,     // one number for every foliage material (was 0.92-0.95, and the
                     // spread was accidental rather than authored)
    trans: 0.42,     // LEAF TRANSLUCENCY: light through the back of a leaf, strongest
                     // when the viewer is looking down-sun. The references' single most
                     // recognisable foliage cue and we had none of it.
    transCol: [1.00, 0.86, 0.42],
    transPow: 2.2,
    hiA: 0.85, hiB: 1.70, hiAmt: 0.55,  // highlight DESATURATION, not a clip: above hiA
                     // the pixel is pulled toward its own luminance, so a lit tip stops
                     // going chartreuse without the value being crushed. Chartreuse is a
                     // CHROMA failure (warm key x green albedo blows G first) and clamping
                     // the value would only make it a paler chartreuse.
                     // THE THRESHOLD IS IN PRE-TONEMAP LINEAR AND THE FIRST GUESS WAS HALF
                     // A CROWN TOO LOW. At 0.45 the term fired over the WHOLE lit canopy,
                     // not its tips: measured on the meadow's crown box, saturation
                     // 0.326 (term off) -> 0.243 at 0.45/1.00 -> 0.296 at 0.80/1.60. A
                     // desaturator wide enough to catch every lit pixel is a chroma cut on
                     // the frame, which is the round-13 overshoot in miniature.
    remap: 0.72,     // strength of the albedo value->hue remap, this lane's materials only
    vComp: 0.75,     // value-range compression toward vMid. THE FIRST SETTING TOOK THE
                     // MODELLING OUT WITH THE BLACK: at 0.62/0.055 the bushes' whole value
                     // range collapsed and the frame read candy — the near-black CORES are
                     // the defect, not the shading. Compress less, floor lower.
    vMid: 0.30, vFloor: 0.035,
    hueSpread: 0.30, // how far the remap swings yellow-green <-> blue-green
    sat: 1.25,       // chroma gain after the remap

    grit: 0.42,      // ground material: amount of the pixel-scale octave
    gritFar: 30.0    // ...faded to nothing by this view depth, so it never stipples
  };

  // ---- the blade variants -------------------------------------------------------------
  // THREE SHAPES, MIXED PER CLUMP. One blade shape is one plant no matter how it is jittered
  // — the critic's words for r3 were "one blade shape... a field of corn". The seed-head is
  // the one that reads at distance, because its silhouette has a lump in it.
  //
  // The vertex colour is a BASE-TO-TIP HUE RAMP, not just a value ramp. Base is a deep cool
  // green (a clump is dark where it meets the ground — that contact is what makes it sit in
  // the terrain instead of on it); tip is warm and yellow. So a single clump carries hue
  // variation from root to tip before any per-instance jitter is applied.
  var BASE_C = [0.60, 0.72, 0.50];
  var TIP_C  = [1.14, 1.06, 0.72];

  function ramp(t, out) {
    for (var i = 0; i < 3; i++) out[i] = BASE_C[i] + (TIP_C[i] - BASE_C[i]) * t;
    return out;
  }

  function bladeGeo(kind) {
    var T = TH();
    // kind 0 SHORT/BROAD, 1 MEDIUM, 2 SEED-HEAD
    var seg = kind === 2 ? 4 : 3;
    var wmul = kind === 0 ? 1.35 : (kind === 1 ? 0.92 : 0.58);
    var bend = kind === 0 ? 0.42 : (kind === 1 ? 0.24 : 0.16);
    var hmul = kind === 0 ? 0.72 : (kind === 1 ? 1.00 : 1.22);
    var w = P.wide * wmul, h = hmul;
    var Pp = [], N = [], U = [], C = [], I = [], c3 = [0, 0, 0];
    for (var i = 0; i <= seg; i++) {
      var t = i / seg, tw = w * (1 - t * 0.85), y = h * t, z = bend * t * t * h;
      Pp.push(-tw, y, z, tw, y, z);
      // NORMALS POINT MOSTLY UP, not along the blade's own face. R6 MEASURED THE TILT AND
      // IT WAS SPECKLE: 0.34 of lateral normal against a key at elevation 34 deg swings a
      // blade's own N.L from 0.24 to 0.81 depending on which way it happens to be yawed,
      // and yaw is uniform over 2*pi. 0.14 keeps a trace of form and lands the mean on the
      // ground's own. The value variation comes from the baked ramp, which is ours, rather
      // than from the light, which is not.
      N.push(0, 0.990, 0.14, 0, 0.990, 0.14);
      U.push(0, t, 1, t);
      ramp(t, c3);
      C.push(c3[0], c3[1], c3[2], c3[0], c3[1], c3[2]);
    }
    for (var j = 0; j < seg; j++) { var a = j * 2; I.push(a, a + 1, a + 3, a, a + 3, a + 2); }
    if (kind === 2) {
      // THE SEED HEAD: two crossed cards on the top fifth of the stalk, paler and warmer.
      // It is 4 triangles and it is what stops the far band reading as a comb.
      var v0 = Pp.length / 3, hy0 = h * 0.70, hy1 = h * 1.08, hw = P.wide * 0.72;
      var hz0 = bend * 0.74 * 0.74 * h, hz1 = bend * 1.0 * 1.0 * h;
      var quads = [[hw, 0], [0, hw]];
      for (var q = 0; q < 2; q++) {
        var ax = quads[q][0], az = quads[q][1];
        Pp.push(-ax, hy0, hz0 - az, ax, hy0, hz0 + az, -ax * 0.35, hy1, hz1 - az * 0.35,
                ax * 0.35, hy1, hz1 + az * 0.35);
        for (var k = 0; k < 4; k++) {
          N.push(0, 0.94, 0.34); U.push(0, 0.85);
          C.push(1.08, 1.02, 0.66);
        }
        var b0 = v0 + q * 4;
        I.push(b0, b0 + 1, b0 + 3, b0, b0 + 3, b0 + 2);
      }
    }
    var g = new T.BufferGeometry();
    g.setAttribute('position', new T.Float32BufferAttribute(Pp, 3));
    g.setAttribute('normal', new T.Float32BufferAttribute(N, 3));
    g.setAttribute('uv', new T.Float32BufferAttribute(U, 2));
    g.setAttribute('color', new T.Float32BufferAttribute(C, 3));
    g.setIndex(I);
    return g;
  }

  // ===================================================================================
  // ROUND 3: THREE NEW GROUND ASSETS — the ceiling f2 measured from the inside
  // ===================================================================================
  // f2's own STILL OPEN list named this and the blind judge named it independently:
  // "the dry slope is one tint multiplier on the same three blade shapes." Every knob
  // this module owns moves COUNT, SIZE, TINT or PLACEMENT, and none of them can make a
  // second species — a hillside carried by one silhouette at two tints is a hillside
  // with one plant on it, and no amount of scatter tuning is going to be the answer.
  // So: two more ground plants and one real flower, in the same vertex-colour language
  // (a base->tip ramp baked into COLOR_0, no new material, no new texture, no new
  // draw call per plant — two more instanced meshes).
  //
  // THE POINT OF EACH IS ITS SILHOUETTE, not its detail. At 10-20 m these are 8-25 px
  // tall, so what survives is the OUTLINE:
  //   blade   a thin spike            (have)
  //   weed    a low rosette of BROAD lobed leaves — a round, horizontal mass
  //   sedge   a tight fountain of stiff arcs — tall, narrow, sharply bent
  //   flower  a NOTCHED DISC on a stem — the one round-with-holes shape out there
  // Three of the four disagree in aspect ratio, which is the axis a 12 px plant is
  // read on. Detail below ~2 px is triangles spent on nothing (f2's whole finding).

  // ---- the broadleaf weed: a plantain/dock rosette --------------------------------
  // 5 ovate leaves from one crown, pitched out and arcing DOWN at the tip so the mass
  // is wider than it is tall. 30 triangles. It is the only thing in the frame with a
  // horizontal silhouette, which is exactly why it reads next to a field of spikes.
  // THE MIDRIB IS AN ARC THAT TURNS OVER, AND THE FIRST VERSION DID NOT — CAUGHT BY
  // LOOKING, not by any number here. Written as `y = len*t*cos(pitch*0.55)` the height
  // grows monotonically with t, so every leaf's TIP was its highest point: six leaves
  // radiating UP and OUT, which in the frame read as loose leaves floating over the road
  // rather than as one plant on the ground. A rosette is defined by its tips being BELOW
  // its crown. So the midrib is integrated from a tangent ELEVATION that starts steep and
  // ends NEGATIVE, which is the one property the shape has to have.
  function weedGeo() {
    var T = TH(), Pp = [], N = [], U = [], C = [], I = [], c3 = [0, 0, 0];
    var NL = 6, SEG = 3;
    for (var l = 0; l < NL; l++) {
      // deterministic per-leaf variation: the six leaves of ONE geometry must differ, or
      // the rosette is a pinwheel and reads as a manufactured object.
      var a = l * (6.2831853 / NL) + (l % 2 ? 0.21 : -0.14);
      var ca = Math.cos(a), sa = Math.sin(a);
      var len = 0.84 + 0.16 * ((l * 7) % 5) / 4;          // 0.84..1.00
      // TWO ERECT INNER LEAVES AND FOUR FLAT OUTER ONES. A rosette of six flat leaves is
      // 0.07 m tall against grass that is 0.10-0.36 m: a correct plant that the field it
      // stands in completely hides. Dock and plantain both hold their young leaves up,
      // so the two silhouettes this asset needs — a horizontal MASS and something that
      // clears the blades — are the same plant's, not a compromise between them.
      var erect = l < 2;
      var A0 = erect ? 1.35 : 1.09 + 0.14 * ((l * 3) % 4) / 3;   // tangent elevation, base
      var A1 = erect ? 0.75 : -0.42 - 0.30 * ((l * 5) % 3) / 2;  // ...and at the tip
      var v0 = Pp.length / 3, rr = 0, yy = 0;
      for (var i = 0; i <= SEG; i++) {
        var t = i / SEG;
        if (i > 0) {                                       // midpoint integration of the arc
          var am = A0 + (A1 - A0) * (t - 0.5 / SEG);
          rr += len / SEG * Math.cos(am);
          yy += len / SEG * Math.sin(am);
        }
        // OVATE, not lanceolate: widest at ~40% of the length. sin(pi*t^0.75) puts the
        // shoulder there and still closes to a point, which is the whole difference
        // between "leaf" and "blade" at 12 px. WIDE ENOUGH TO OVERLAP ITS NEIGHBOURS:
        // six leaves that do not touch are six leaves, and the asset is a MASS.
        var hw = 0.30 * len * Math.sin(Math.PI * Math.pow(Math.max(1e-4, t), 0.75));
        if (i === 0) hw = 0.040 * len;
        var px = ca * rr, pz = sa * rr;
        var ox = -sa * hw, oz = ca * hw;
        Pp.push(px - ox, yy, pz - oz, px + ox, yy, pz + oz);
        // a broad leaf FACES UP; the lateral term is the elevation it is held at, so a
        // drooping tip turns its face outward exactly as far as it has turned over.
        var av = A0 + (A1 - A0) * t, nl = Math.sin(av) * 0.62;
        N.push(-ca * nl, 0.92, -sa * nl, -ca * nl, 0.92, -sa * nl);
        U.push(0, t, 1, t);
        ramp3(WEED_C0, WEED_C1, t, c3);
        C.push(c3[0], c3[1], c3[2], c3[0], c3[1], c3[2]);
      }
      for (var j = 0; j < SEG; j++) { var b = v0 + j * 2; I.push(b, b + 1, b + 3, b, b + 3, b + 2); }
    }
    return mkGeo(T, Pp, N, U, C, I);
  }

  // ---- the low sedge / rush tussock ------------------------------------------------
  // 7 stiff arcs off ONE knot, splayed in a fan, each much narrower and much more bent
  // than a grass blade, and the whole thing TALLER than the tuft it stands among. 42
  // triangles, and it replaces blades rather than adding to them (see `weedCost`).
  // Its hue family is the cool one on purpose — the f2 `grassOnDry` lesson generalised:
  // a second species that agrees with the first is a tint, not a species.
  function sedgeGeo() {
    var T = TH(), Pp = [], N = [], U = [], C = [], I = [], c3 = [0, 0, 0];
    var NA = 7, SEG = 3;
    for (var l = 0; l < NA; l++) {
      var a = l * (6.2831853 / NA) + (l % 2 ? 0.28 : -0.21);
      var ca = Math.cos(a), sa = Math.sin(a);
      var len = 0.70 + 0.30 * ((l * 11) % 7) / 6;         // 0.70..1.00 — ragged crown
      // A FOUNTAIN, NOT A STARFISH. The first pass ran flop to 1.10 and the tussock came
      // out wider than it was tall, which is the weed's silhouette — two assets with one
      // outline is the defect this round exists to fix, arriving by the back door.
      var flop = 0.18 + 0.30 * ((l * 5) % 4) / 3;         // how far the arc falls over
      var v0 = Pp.length / 3;
      for (var i = 0; i <= SEG; i++) {
        var t = i / SEG;
        var rr = len * flop * t * t;                      // out
        var yy = len * (t - 0.28 * t * t * flop);         // up, bending over
        var hw = 0.030 * len * (1 - t * 0.90);            // a rush is a needle
        var px = ca * rr, pz = sa * rr;
        var ox = -sa * hw, oz = ca * hw;
        Pp.push(px - ox, yy, pz - oz, px + ox, yy, pz + oz);
        N.push(-ca * 0.22, 0.96, -sa * 0.22, -ca * 0.22, 0.96, -sa * 0.22);
        U.push(0, t, 1, t);
        ramp3(SEDGE_C0, SEDGE_C1, t, c3);
        C.push(c3[0], c3[1], c3[2], c3[0], c3[1], c3[2]);
      }
      for (var j = 0; j < SEG; j++) { var b = v0 + j * 2; I.push(b, b + 1, b + 3, b, b + 3, b + 2); }
    }
    // THE DARK KNOT. A tussock's base is a dense mat of old growth, and without it the
    // seven arcs read as seven separate blades that happen to touch — the one thing
    // this asset exists NOT to be. Six triangles for the read that makes it one plant.
    var v1 = Pp.length / 3;
    for (var k = 0; k < 6; k++) {
      var ak = k * (6.2831853 / 6);
      Pp.push(Math.cos(ak) * 0.085, 0.035, Math.sin(ak) * 0.085);
      N.push(0, 1, 0); U.push(0.5, 0.05);
      C.push(SEDGE_C0[0] * 0.62, SEDGE_C0[1] * 0.62, SEDGE_C0[2] * 0.66);
    }
    var vc = Pp.length / 3;
    Pp.push(0, 0.075, 0); N.push(0, 1, 0); U.push(0.5, 0.1);
    C.push(SEDGE_C0[0] * 0.86, SEDGE_C0[1] * 0.86, SEDGE_C0[2] * 0.90);
    for (var k2 = 0; k2 < 6; k2++) I.push(vc, v1 + k2, v1 + (k2 + 1) % 6);
    return mkGeo(T, Pp, N, U, C, I);
  }

  // ---- A REAL FLOWER: a notched disc on a stem -------------------------------------
  // f2 made the billboard cross BIGGER and pulled it IN, and the judge still called the
  // result specks — correctly, because a cross of two cards has no outline of its own:
  // seen from anywhere but dead-on it is one bright rectangle, and a bright rectangle
  // 3 px across is a speck whatever colour it is. What reads at 10-20 m is a shape the
  // eye has a name for, and for a flower that is a RING OF PETALS: six petals around a
  // gold centre give a round silhouette with notches in it, and notches survive
  // downsampling as a texture the way a rectangle does not.
  // 6 petals x 2 + a 6-triangle centre fan + stem + two stem leaves = 24 triangles for
  // the one object in this scatter the player is meant to notice.
  function flowerGeo() {
    var T = TH(), Pp = [], N = [], U = [], C = [], I = [], v0;
    var sw = 0.007, hy = 0.92;                    // stem half-width, head height
    // stem
    Pp.push(-sw, 0, 0, sw, 0, 0, -sw * 0.7, hy, 0, sw * 0.7, hy, 0);
    for (var i = 0; i < 4; i++) { N.push(0, 0.97, 0.24); U.push(0, 0); C.push(0.30, 0.40, 0.22); }
    I.push(0, 1, 3, 0, 3, 2);
    // two small stem leaves, so the flower is a PLANT and not a lollipop — the same
    // note the tree lane paid for on its canopies, one scale down.
    for (var q = 0; q < 2; q++) {
      var a = q * 2.4 + 0.6, ca = Math.cos(a), sa = Math.sin(a);
      var y0 = 0.24 + q * 0.22, ln = 0.20;
      v0 = Pp.length / 3;
      Pp.push(0, y0, 0,
              ca * ln * 0.55, y0 + 0.055, sa * ln * 0.55,
              ca * ln, y0 - 0.02, sa * ln);
      for (var k = 0; k < 3; k++) { N.push(-ca * 0.3, 0.94, -sa * 0.3); U.push(0.5, 0.5); C.push(0.34, 0.46, 0.24); }
      I.push(v0, v0 + 1, v0 + 2);
    }
    // the head: a gold centre and six petals lifted into a shallow bowl. COLOR_0 is
    // WHITE on the petals so the per-instance colour carries the species (three of
    // them), and the centre is baked warm so every species keeps a gold eye.
    var NP = 6, R = 0.055, RC = 0.019, lift = 0.020;
    var cIdx = Pp.length / 3;
    Pp.push(0, hy + lift * 0.5, 0); N.push(0, 1, 0); U.push(0.5, 1); C.push(1.15, 0.86, 0.30);
    var ring0 = Pp.length / 3;
    for (var p2 = 0; p2 < NP; p2++) {
      var ap = p2 * (6.2831853 / NP);
      Pp.push(Math.cos(ap) * RC, hy + lift * 0.35, Math.sin(ap) * RC);
      N.push(0, 1, 0); U.push(0.5, 0.9); C.push(1.10, 0.80, 0.26);
    }
    for (var p3 = 0; p3 < NP; p3++) I.push(cIdx, ring0 + p3, ring0 + (p3 + 1) % NP);
    for (var p4 = 0; p4 < NP; p4++) {
      var a4 = (p4 + 0.5) * (6.2831853 / NP), c4 = Math.cos(a4), s4 = Math.sin(a4);
      var w4 = 0.40;                                   // petal half-angle spread
      v0 = Pp.length / 3;
      Pp.push(Math.cos(a4 - w4) * RC * 1.2, hy + lift * 0.30, Math.sin(a4 - w4) * RC * 1.2,
              Math.cos(a4 + w4) * RC * 1.2, hy + lift * 0.30, Math.sin(a4 + w4) * RC * 1.2,
              c4 * R, hy + lift, s4 * R);
      for (var k4 = 0; k4 < 3; k4++) { N.push(-c4 * 0.18, 0.98, -s4 * 0.18); U.push(0.5, 1); C.push(1, 1, 1); }
      I.push(v0, v0 + 1, v0 + 2);
    }
    return mkGeo(T, Pp, N, U, C, I);
  }

  function mkGeo(T, Pp, N, U, C, I) {
    var g = new T.BufferGeometry();
    g.setAttribute('position', new T.Float32BufferAttribute(Pp, 3));
    g.setAttribute('normal', new T.Float32BufferAttribute(N, 3));
    g.setAttribute('uv', new T.Float32BufferAttribute(U, 2));
    g.setAttribute('color', new T.Float32BufferAttribute(C, 3));
    g.setIndex(I);
    return g;
  }
  function ramp3(a, b, t, out) {
    for (var i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
    return out;
  }
  // Each asset gets its OWN base->tip ramp. The weed is broad, so it catches more key
  // and runs warmer at the tip; the sedge is the COOL member of the family, which is
  // what stops a mixed clump reading as one plant at two sizes.
  var WEED_C0  = [0.40, 0.56, 0.32], WEED_C1  = [0.90, 0.96, 0.54];
  var SEDGE_C0 = [0.40, 0.56, 0.48], SEDGE_C1 = [0.88, 1.00, 0.78];

  // WHITE / YELLOW / PINK-LAVENDER. Three species, because two reads as a mistake and four
  // reads as a garden. Values are close together on purpose — the references' flowers are a
  // HUE event at roughly the ground's own value, not a bright spot.
  var FLOWER = [[1.30, 1.26, 1.10], [1.34, 1.10, 0.34], [1.22, 0.72, 0.92]];

  // ---- the sources: the terrain's own GRASS and DRY primitives -------------------------
  // Placing against the ground MESH rather than a height probe buys three things at once:
  // the exact surface y, the terrain's own COLOR_0 under each tuft (so the scatter is never
  // a different green from the ground it stands in), and the slot choice for free.
  //
  // R-F1 ADDS THE DRY PRIMITIVE. The worn slopes were bare dirt with nothing growing on
  // them and the references' worn slopes are ochre GRASS; scattering there at 0.42x density
  // with the dry tint is most of the "15-25% non-green" item, and it costs no new asset.
  var SRC_DEF = [
    { name: 'ow_f2_ter_grass', mesh: 'ground_valley_1', dry: 0.0, w: 1.0 },
    { name: 'ow_f2_ter_dry', mesh: null, dry: 1.0, w: 0.42 }
  ];

  function sources() {
    var sc = SCN(); if (!sc) return null;
    var out = [];
    for (var i = 0; i < SRC_DEF.length; i++) {
      (function (def) {
        var hit = null;
        sc.traverse(function (m) {
          if (hit || !m.isMesh || !m.geometry) return;
          var mn = (m.material && m.material.name) || '';
          if (mn === def.name || (def.mesh && m.name === def.mesh)) hit = m;
        });
        if (hit) out.push({ def: def, mesh: hit, idx: null });
      })(SRC_DEF[i]);
    }
    return out.length ? out : null;
  }

  // THE GROUND IS TEXTURE x COLOR_0, AND THE TUFTS ONLY GET COLOR_0. Sampling the terrain's
  // vertex colour alone made the first carpet 1.5-2x brighter than the ground it stood in,
  // which at boom 40 is exactly white frost — the terrain material is baseColorTexture *
  // COLOR_0 (glTF can only multiply). So measure the map's mean, in the shader's own colour
  // space, and fold it into the tint. A texture that will not draw leaves it null and the
  // scatter falls back to a flat factor rather than to a wrong one.
  var TEXMEAN = {};
  function texMean(mat) {
    var key = (mat && mat.name) || '?';
    if (key in TEXMEAN) return TEXMEAN[key];
    var out = null;
    try {
      var img = mat && mat.map && mat.map.image;
      if (img && img.width) {
        var cv = document.createElement('canvas'); cv.width = cv.height = 24;
        var cxr = cv.getContext('2d', { willReadFrequently: true });
        cxr.drawImage(img, 0, 0, 24, 24);
        var d = cxr.getImageData(0, 0, 24, 24).data, s = [0, 0, 0];
        for (var i = 0; i < d.length; i += 4) { s[0] += d[i]; s[1] += d[i + 1]; s[2] += d[i + 2]; }
        var n = d.length / 4; out = [];
        for (var c = 0; c < 3; c++) {
          var u = s[c] / n / 255;
          out.push(u <= 0.04045 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4));
        }
      }
    } catch (e) { out = null; }
    TEXMEAN[key] = out;
    return out;
  }

  function index(mesh) {
    var g = mesh.geometry, pos = g.attributes.position, col = g.attributes.color;
    var ix = g.index; if (!ix) return null;
    mesh.updateWorldMatrix(true, false);
    var mw = mesh.matrixWorld.elements;
    var nv = pos.count, X = new Float32Array(nv), Y = new Float32Array(nv), Z = new Float32Array(nv);
    for (var v = 0; v < nv; v++) {
      var x = pos.getX(v), y = pos.getY(v), z = pos.getZ(v);
      X[v] = mw[0] * x + mw[4] * y + mw[8] * z + mw[12];
      Y[v] = mw[1] * x + mw[5] * y + mw[9] * z + mw[13];
      Z[v] = mw[2] * x + mw[6] * y + mw[10] * z + mw[14];
    }
    var nt = ix.count / 3, CELL = 8;
    var cells = new Map(), area = new Float32Array(nt), ny = new Float32Array(nt);
    for (var t = 0; t < nt; t++) {
      var a = ix.getX(t * 3), b = ix.getX(t * 3 + 1), c = ix.getX(t * 3 + 2);
      var ux = X[b] - X[a], uy = Y[b] - Y[a], uz = Z[b] - Z[a];
      var vx = X[c] - X[a], vy = Y[c] - Y[a], vz = Z[c] - Z[a];
      var cxn = uy * vz - uz * vy, cyn = uz * vx - ux * vz, czn = ux * vy - uy * vx;
      var len = Math.hypot(cxn, cyn, czn);
      area[t] = len * 0.5;
      ny[t] = len > 1e-9 ? Math.abs(cyn) / len : 0;
      var mx = (X[a] + X[b] + X[c]) / 3, mz = (Z[a] + Z[b] + Z[c]) / 3;
      var key = Math.floor(mx / CELL) + ',' + Math.floor(mz / CELL);
      var arr = cells.get(key); if (!arr) { arr = []; cells.set(key, arr); }
      arr.push(t);
    }
    return { X: X, Y: Y, Z: Z, ix: ix, col: col, nt: nt, CELL: CELL, cells: cells,
             area: area, ny: ny };
  }

  // ===================================================================================
  // THE FRINGE FIELD — a distance transform over everything that is not turf
  // ===================================================================================
  // A FLOOD FILL TELLS YOU WHERE THE WORLD IS SHUT AND NEVER WHAT SHUTS IT (CLAUDE.md), and
  // the same is true here in reverse: "the path edge is hard" is a fact about a SEAM, and a
  // seam is only findable if you know where both sides are. Rasterising every non-turf
  // surface into one grid and chamfer-transforming it turns "am I near a seam, and which way
  // is it" into two array reads, which is what lets the fringe rule be one line at the
  // placement site instead of five special cases.
  //
  // The occluder set is deliberately WIDE: road and dock path (the item the critic named),
  // water (a shoreline is a seam), terrain rock (a cliff foot is a seam), stone/planks/
  // plaster/tiles/tar (building footings), bark (tree feet) and bushcore (bush bases).
  // `ow_f2_matte` IS THE HOUSE PADS, and its absence here was r1's unfringed-seam defect.
  // MEASURED, not guessed: valley_build's `trodden_ring` lays its wear ring with class
  // DIRT (valley_build.py:1076), and overworld3_build's class->material `group` map has no
  // entry for DIRT, so it falls through `group.get(int(c), "matte")` to ow_f2_matte. The
  // ring is therefore a 2 cm-proud disc of bare earth that the chamfer field could not see:
  // every house pad was a hard polygon edge with no band on either side of it, which is
  // exactly the "stamped decals with hard, unfringed seams" the blind judge named on five
  // pads at once. A SEAM IS ONLY FINDABLE IF THE FIELD KNOWS BOTH SIDES OF IT.
  var OCC_MATS = ['ow_f2_road', 'ow_f2_dockpath', 'ow_f2_water', 'ow_f2_ter_rock',
                  'ow_f2_stone', 'ow_f2_planks', 'ow_f2_plaster', 'ow_f2_tiles',
                  'ow_f2_tar', 'ow_f2_bark', 'ow_valley_bushcore', 'ow_f2_matte'];
  // ...and the SUBSET a plant genuinely cannot grow through. THE TWO SETS ARE NOT THE SAME
  // AND CONFLATING THEM COST 68% OF THE FIELD: refusing a tuft in any occupied cell dropped
  // the closeup from 208 055 blades to 67 095, because `ow_f2_ter_rock` and the bush cores
  // are terrain SLOTS that interleave with turf across most of the meadow. A rock outcrop
  // is something grass grows AGAINST (so it must fringe) and also something grass grows
  // BETWEEN (so it must not refuse). A paved road is neither.
  // ...and it is HARD too, because a trodden ring is trodden: valley_build's own docstring
  // for it says "the grass stops a foot short of the wall and a few blades grow against the
  // stone", which is a refusal plus a fringe plus strays — precisely this pair of sets.
  var HARD_MATS = ['ow_f2_road', 'ow_f2_dockpath', 'ow_f2_water', 'ow_f2_tar',
                   'ow_f2_stone', 'ow_f2_planks', 'ow_f2_plaster', 'ow_f2_tiles',
                   'ow_f2_matte'];
  // ow_f2_ter_dry IS DELIBERATELY NOT AN OCCLUDER, and the first build proved why: the dry
  // primitive is also a SOURCE, so marking it occupied put every dry cell at distance 0 from
  // a seam and gave the whole worn slope the fringe multiplier — a bleached straw carpet
  // across the middle of the frame instead of a thin band at its edge. A cell cannot be both
  // the thing being fringed and the thing doing the fringing.
  var OCC = null;

  function buildOcc() {
    var sc = SCN(); if (!sc || !SRCS || !SRCS.length) return null;
    var t0 = (performance && performance.now) ? performance.now() : 0;
    var T = TH();
    // bounds from the TURF, padded — a fringe cell outside the turf is still needed
    // (a stray blade stands past the seam).
    var bb = new T.Box3();
    for (var i = 0; i < SRCS.length; i++) {
      SRCS[i].mesh.updateWorldMatrix(true, false);
      bb.expandByObject(SRCS[i].mesh);
    }
    if (!isFinite(bb.min.x)) return null;
    var cell = P.occCell, pad = 4;
    var x0 = bb.min.x - pad, z0 = bb.min.z - pad;
    var nx = Math.ceil((bb.max.x - bb.min.x + pad * 2) / cell);
    var nz = Math.ceil((bb.max.z - bb.min.z + pad * 2) / cell);
    if (nx <= 0 || nz <= 0 || nx * nz > 4e6) return null;
    var D = new Float32Array(nx * nz); D.fill(1e9);
    var HD = new Uint8Array(nx * nz);
    // ...AND HOW HIGH THE HARD SURFACE STANDS (round 3). EVERY paved or bedded surface
    // in this bundle is PROUD of the terrain it lies on — the road ribbon has its own
    // ramp, `bed_in`'s trodden ring is a 2 cm disc, a house floor is a step — and a
    // STRAY takes its y from the TERRAIN TRIANGLE it was born on, because that is the
    // surface it was pushed off. So a straggler that crosses the seam stands at the
    // height of the ground BESIDE the path, which puts its lower stem inside the path:
    // measured on the closeup, 130 of 20 844 sampled blades sit under a hard surface,
    // 56 of them by 3-25 cm (a stray at a bedding ring or a road shoulder), the rest by
    // more than that (inside a house, where nothing can see them anyway). It is a small
    // number and it lands on the ONE seam the player stands closest to, which is where
    // f2 already learned this field's errors get read. One more array on a grid that is
    // already being rasterised: the max surface height per hard cell.
    var HY = new Float32Array(nx * nz); HY.fill(-1e9);
    var nOcc = 0, nHard = 0, nTri = 0;
    var va = new T.Vector3(), vb = new T.Vector3(), vc = new T.Vector3();

    sc.traverse(function (m) {
      if (!m.isMesh || !m.geometry) return;
      var mn = (m.material && m.material.name) || '';
      if (OCC_MATS.indexOf(mn) < 0) return;
      var hard = HARD_MATS.indexOf(mn) >= 0;
      var g = m.geometry, pos = g.attributes.position, ix = g.index;
      if (!pos) return;
      m.updateWorldMatrix(true, false);
      var mw = m.matrixWorld;
      var cnt = ix ? ix.count : pos.count;
      for (var t = 0; t + 2 < cnt; t += 3) {
        var ia = ix ? ix.getX(t) : t, ib = ix ? ix.getX(t + 1) : t + 1, ic = ix ? ix.getX(t + 2) : t + 2;
        va.fromBufferAttribute(pos, ia).applyMatrix4(mw);
        vb.fromBufferAttribute(pos, ib).applyMatrix4(mw);
        vc.fromBufferAttribute(pos, ic).applyMatrix4(mw);
        nTri++;
        // plan-view area -> sample count. 16 samples/m2 puts ~4 in a 0.6 m cell, which is
        // enough that a thin road ribbon never develops holes in its own footprint.
        var ax = vb.x - va.x, ay = vb.y - va.y, az = vb.z - va.z;
        var bx = vc.x - va.x, by2 = vc.y - va.y, bz = vc.z - va.z;
        var ar = Math.abs(ax * bz - az * bx) * 0.5;
        var ns = Math.max(3, Math.min(400, Math.ceil(ar * 16)));
        for (var s = 0; s < ns; s++) {
          var u = ((s * 0.7548776662) % 1), w = ((s * 0.5698402909) % 1);
          if (u + w > 1) { u = 1 - u; w = 1 - w; }
          var px = va.x + u * ax + w * bx, pz = va.z + u * az + w * bz;
          var gi = ((px - x0) / cell) | 0, gk = ((pz - z0) / cell) | 0;
          if (gi < 0 || gk < 0 || gi >= nx || gk >= nz) continue;
          var o = gk * nx + gi;
          if (D[o] !== 0) { D[o] = 0; nOcc++; }
          if (hard) {
            if (!HD[o]) { HD[o] = 1; nHard++; }
            var py2 = va.y + u * ay + w * by2;
            if (py2 > HY[o]) HY[o] = py2;
          }
        }
      }
    });

    // two-pass chamfer (3,4)/3 — the standard cheap Euclidean approximation, in CELLS,
    // scaled to metres on read.
    var A = 1.0, B = Math.SQRT2;
    var k, o2;
    for (k = 0; k < nz; k++) for (var i2 = 0; i2 < nx; i2++) {
      o2 = k * nx + i2; if (D[o2] === 0) continue;
      var d = D[o2];
      if (i2 > 0) d = Math.min(d, D[o2 - 1] + A);
      if (k > 0) d = Math.min(d, D[o2 - nx] + A);
      if (k > 0 && i2 > 0) d = Math.min(d, D[o2 - nx - 1] + B);
      if (k > 0 && i2 < nx - 1) d = Math.min(d, D[o2 - nx + 1] + B);
      D[o2] = d;
    }
    for (k = nz - 1; k >= 0; k--) for (var i3 = nx - 1; i3 >= 0; i3--) {
      o2 = k * nx + i3; if (D[o2] === 0) continue;
      var e = D[o2];
      if (i3 < nx - 1) e = Math.min(e, D[o2 + 1] + A);
      if (k < nz - 1) e = Math.min(e, D[o2 + nx] + A);
      if (k < nz - 1 && i3 < nx - 1) e = Math.min(e, D[o2 + nx + 1] + B);
      if (k < nz - 1 && i3 > 0) e = Math.min(e, D[o2 + nx - 1] + B);
      D[o2] = e;
    }
    var ms = ((performance && performance.now) ? performance.now() : 0) - t0;
    return { x0: x0, z0: z0, nx: nx, nz: nz, cell: cell, D: D, HD: HD, HY: HY,
             cells: nx * nz, occ: nOcc, hard: nHard, tris: nTri, ms: +ms.toFixed(1) };
  }

  function occHard(x, z) {                    // is this cell paved / water / a building?
    if (!OCC) return false;
    var gi = ((x - OCC.x0) / OCC.cell) | 0, gk = ((z - OCC.z0) / OCC.cell) | 0;
    if (gi < 0 || gk < 0 || gi >= OCC.nx || gk >= OCC.nz) return false;
    return OCC.HD[gk * OCC.nx + gi] === 1;
  }
  // ...and how high it stands. null = no hard surface here, which is NOT the same as
  // "the surface is at zero": a caller that treats a miss as a height puts every plant
  // in open country at y=0.
  function occTop(x, z) {
    if (!OCC) return null;
    var gi = ((x - OCC.x0) / OCC.cell) | 0, gk = ((z - OCC.z0) / OCC.cell) | 0;
    if (gi < 0 || gk < 0 || gi >= OCC.nx || gk >= OCC.nz) return null;
    var o = gk * OCC.nx + gi;
    return OCC.HD[o] === 1 && OCC.HY[o] > -1e8 ? OCC.HY[o] : null;
  }
  function occD(x, z) {                       // metres to the nearest non-turf surface
    if (!OCC) return 99;
    var gi = ((x - OCC.x0) / OCC.cell) | 0, gk = ((z - OCC.z0) / OCC.cell) | 0;
    if (gi < 0 || gk < 0 || gi >= OCC.nx || gk >= OCC.nz) return 99;
    return OCC.D[gk * OCC.nx + gi] * OCC.cell;
  }
  // ...and which way it lies. Central differences on the same field: a stray tuft is pushed
  // DOWN the gradient, i.e. toward the thing it is fringing, so it ends up standing in the
  // dirt rather than beside it.
  function occGrad(x, z, out) {
    var h = OCC ? OCC.cell : 1;
    var dx = occD(x + h, z) - occD(x - h, z), dz = occD(x, z + h) - occD(x, z - h);
    var l = Math.hypot(dx, dz);
    if (l < 1e-6) { out[0] = 0; out[1] = 0; return false; }
    out[0] = -dx / l; out[1] = -dz / l; return true;
  }

  // WORLD-SPACE VALUE NOISE, for the clump and patch fields. Keyed on WORLD position, not on
  // draw order, which is what makes a patch stay where it is across a rebuild — a clump field
  // derived from the per-call PRNG would reshuffle the meadow every time the player walked
  // 9 m, and a meadow that reshuffles is worse than a meadow that is even.
  function vhash(a, b) {
    var s = (Math.imul(a | 0, 374761393) ^ Math.imul(b | 0, 668265263) ^ 0x9e3779b9) >>> 0;
    s = (s ^ (s >>> 13)) >>> 0; s = Math.imul(s, 1274126177) >>> 0;
    return ((s ^ (s >>> 16)) >>> 8) / 16777216;
  }
  function vnoise(x, z) {
    var xi = Math.floor(x), zi = Math.floor(z), xf = x - xi, zf = z - zi;
    var u = xf * xf * (3 - 2 * xf), v = zf * zf * (3 - 2 * zf);
    return (vhash(xi, zi) * (1 - u) + vhash(xi + 1, zi) * u) * (1 - v) +
           (vhash(xi, zi + 1) * (1 - u) + vhash(xi + 1, zi + 1) * u) * v;
  }
  // THE NOISE LATTICE IS AXIS-ALIGNED AND THE TERRAIN GRID IS TOO, so a threshold on it
  // produces blobs whose edges run along world x and z — and the blind judge read exactly
  // that back as "a visible grid, even ranks". Value noise is bilinear over integer cells;
  // nothing makes it isotropic. Rotating the SAMPLE DOMAIN by an angle that is no simple
  // fraction of a turn costs two multiplies and takes the lattice off both the world axes
  // and the road tangent, so a clump edge no longer agrees with anything else in the frame.
  // Each octave gets its OWN angle, or the octaves re-align with each other at depth.
  var RC1 = Math.cos(0.5473), RS1 = Math.sin(0.5473);     // ~31.4 deg
  var RC2 = Math.cos(1.2971), RS2 = Math.sin(1.2971);     // ~74.3 deg
  var RC3 = Math.cos(2.2419), RS3 = Math.sin(2.2419);     // ~128.4 deg
  function clumpAt(x, z) {
    var s = 1 / Math.max(0.5, P.clumpM);
    var xa = (x * RC1 - z * RS1) * s, za = (x * RS1 + z * RC1) * s;
    var xb = (x * RC2 - z * RS2) * s * 2.7, zb = (x * RS2 + z * RC2) * s * 2.7;
    // a THIRD octave, finer and weaker: two octaves threshold into blobs of one size and a
    // field of one blob size is its own kind of regularity at a grazing angle.
    var xc = (x * RC3 - z * RS3) * s * 6.1, zc = (x * RS3 + z * RC3) * s * 6.1;
    return vnoise(xa, za) * 0.60 + vnoise(xb + 11.3, zb - 4.1) * 0.28 +
           vnoise(xc + 5.9, zc + 27.7) * 0.12;
  }
  function patchAt(x, z) {
    var s = 1 / Math.max(0.5, P.flPatchM);
    return vnoise((x * RC2 - z * RS2) * s + 71.7, (x * RS2 + z * RC2) * s - 33.1);
  }
  // ...and the slot-blend field (see `wgt` in rebuild): its whole job is to disagree with
  // the terrain's polygon edges, so it gets its own angle and its own scale.
  function slotAt(x, z) {
    var s = 1 / Math.max(0.5, P.slotM);
    return vnoise((x * RC3 - z * RS3) * s + 43.1, (x * RS3 + z * RC3) * s + 19.7);
  }
  // ...and one field per NEW SPECIES, each on its own angle. If the weed and the sedge
  // shared the grass's clump field they would appear exactly where the grass is thickest
  // and vanish where it thins — three assets drawing one map. Their patches have to be
  // able to land in the grass's bare gaps, which is where a different plant grows.
  var RC4 = Math.cos(0.9126), RS4 = Math.sin(0.9126);     // ~52.3 deg
  var RC5 = Math.cos(1.8734), RS5 = Math.sin(1.8734);     // ~107.3 deg
  function weedAt(x, z) {
    var s = 1 / Math.max(0.5, P.weedM);
    return vnoise((x * RC4 - z * RS4) * s - 17.3, (x * RS4 + z * RC4) * s + 61.9);
  }
  function sedgeAt(x, z) {
    var s = 1 / Math.max(0.5, P.sedgeM);
    return vnoise((x * RC5 - z * RS5) * s + 8.7, (x * RS5 + z * RC5) * s - 52.3);
  }

  function rngAt(x, z) {
    var s = (Math.imul(Math.round(x * 4) | 0, 374761393) ^
             Math.imul(Math.round(z * 4) | 0, 668265263) ^ 20260804) >>> 0;
    return function () { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
  }

  function clear() {
    var sc = SCN(); if (!sc) return;
    var g = sc.getObjectByName(GROUP);
    if (g) {
      g.traverse(function (n) {
        if (n.isMesh) { try { n.geometry.dispose(); } catch (e) {} }
      });
      sc.remove(g);
    }
    MESHES = []; NBLADE = 0;
  }

  // the scatter's own material is built ONCE and shared by all four instanced meshes, so the
  // foliage shader patch below is applied to it exactly like a bundle material.
  var SMAT = null;
  function scatterMat() {
    if (SMAT) return SMAT;
    var T = TH();
    SMAT = new T.MeshStandardMaterial({ color: 0xffffff, roughness: P.rough, metalness: 0.0,
                                        vertexColors: true, side: T.DoubleSide });
    SMAT.name = 'veg_owd_blade';
    patchFoliage(SMAT, true);
    return SMAT;
  }

  function rebuild(force) {
    var T = TH(), sc = SCN(), SIM = window.SIM;
    if (!ON || !T || !sc || !SIM || !SIM.pos) return null;
    if (softwareGL()) { clear(); return 0; }
    var p = SIM.pos();
    var now = (performance && performance.now) ? performance.now() : Date.now();
    if (!force) {
      if (LASTAT && Math.hypot(p.x - LASTAT.x, p.z - LASTAT.z) < P.step) return null;
      // A FLOOR ON HOW OFTEN THIS CAN COST 80 ms. Movement alone is not enough of a guard:
      // a harness that teleports (playthrough_test, transition_test, reach_probe) clears the
      // step test on every jump and would pay for a full rebuild each time.
      if (LASTT && now - LASTT < P.minMs) return null;
    }
    LASTT = now;
    if (!SRCS || !SRCS.length || !sc.getObjectByName(SRCS[0].mesh.name)) { SRCS = sources(); OCC = null; }
    if (!SRCS) return null;
    for (var si = 0; si < SRCS.length; si++) if (!SRCS[si].idx) SRCS[si].idx = index(SRCS[si].mesh);
    if (!OCC) OCC = buildOcc();
    var t0 = (performance && performance.now) ? performance.now() : 0;

    var R = rngAt(p.x, p.z), cx = p.x, cz = p.z, r1 = P.r1, r0 = P.r0, span = r1 - r0;
    // `budget` is a SAFETY VALVE, not a target. Cells are walked in x,z order, so a run that
    // actually hits the cap loses one whole side of the disc rather than thinning evenly.
    // If a future tune gets close, lower tuftDens; do not raise the cap.
    var MB = [[], [], []], MC = [[], [], []];   // per-variant matrices / colours
    var FM = [], FC = [];                       // flowers
    var WM = [], WC = [], SM = [], SC = [];     // weeds, sedges
    var n = 0, nT = 0, nW = 0, nS = 0;
    var zone = SIM.zone ? SIM.zone : null;
    var m4 = new T.Matrix4(), q = new T.Quaternion(), up = new T.Vector3(0, 1, 0);
    var lean = new T.Quaternion(), axis = new T.Vector3();
    var vp = new T.Vector3(), vs = new T.Vector3();
    var gr = [0, 0];

    for (var srci = 0; srci < SRCS.length; srci++) {
      var S = SRCS[srci], IDX = S.idx;
      if (!IDX) continue;
      var dryW = S.def.dry, baseW = S.def.dry > 0 ? 1.0 : S.def.w;
      var COL = IDX.col, ix = IDX.ix, X = IDX.X, Y = IDX.Y, Z = IDX.Z;
      var TM = texMean(S.mesh.material) || [0.34, 0.34, 0.34];
      var c0 = IDX.CELL;
      var i0 = Math.floor((cx - r1) / c0), i1 = Math.floor((cx + r1) / c0);
      var k0 = Math.floor((cz - r1) / c0), k1 = Math.floor((cz + r1) / c0);

      for (var ci = i0; ci <= i1 && n < P.budget; ci++) {
        for (var ck = k0; ck <= k1 && n < P.budget; ck++) {
          var list = IDX.cells.get(ci + ',' + ck);
          if (!list) continue;
          for (var li = 0; li < list.length && n < P.budget; li++) {
            var t = list[li];
            if (IDX.ny[t] < P.slope) continue;            // no grass growing out of cliff
            var a = ix.getX(t * 3), b = ix.getX(t * 3 + 1), c = ix.getX(t * 3 + 2);
            var mx = (X[a] + X[b] + X[c]) / 3, mz = (Z[a] + Z[b] + Z[c]) / 3;
            var d = Math.hypot(mx - cx, mz - cz);
            if (d > r1) continue;
            var fall = d <= r0 ? 1 : Math.pow(1 - (d - r0) / span, P.tail);

            // the clump field is sampled at the TRIANGLE, not per tuft: a per-tuft sample
            // thins a patch uniformly instead of moving its edge, which is the even carpet
            // again by another route.
            var cl = clumpAt(mx, mz);
            // ...and then THRESHOLDED, which is what puts bare earth in the frame.
            var cm = (cl - P.bare) / Math.max(1e-3, 1 - P.bare);
            if (cm <= 0) continue;
            cm = Math.pow(cm, P.clumpP) * (1 + P.clumpP);

            // FRINGE: the density multiplier along every seam, and the whole reason the
            // horizon and the path edges stop being lines.
            var fd = occD(mx, mz);
            // A TUFT MAY NOT BE BORN INSIDE THE THING IT IS FRINGING. The turf primitive
            // runs UNDER the road ribbon, the bush cores and the rock feet, so without this
            // line every one of those cells is a grass cell that also scores the maximum
            // fringe multiplier — the first plate had grass growing out of the middle of
            // the path at 3.6x the meadow's density and it read as scattered straw. Only a
            // deliberate STRAY may cross, and it crosses by being pushed.
            //
            // ...BUT THIS TEST DECIDES THE COUNT ONLY, NOT WHERE THE EDGE IS. It is asked
            // at the triangle's CENTROID, and the terrain's triangles are metres across, so
            // as the sole test it resolved every road shoulder at TRIANGLE scale: a triangle
            // whose centroid fell on the road contributed nothing at all, and one whose
            // centroid fell beside it scattered blades right across the paving. That is a
            // ~2.5 m ragged quantisation of the one edge the player stands closest to, and
            // at the grazing camera it reads as the judge's "no geometry at its edges at
            // all, just a brushed texture ramp". The refusal is repeated PER BLADE below,
            // at 0.6 m, which is the grid's own resolution and the finest this can be.
            if (occHard(mx, mz)) continue;
            var fr = fd < P.fringeD ? (1 - fd / P.fringeD) : 0;
            var fk = 1 + P.fringeK * fr;
            // the slot blend — see `slotBias`. Both slots span [dryDens, 1]; the noise, not
            // the polygon, says where in that range this patch of ground sits.
            var sv = slotAt(mx, mz) + (dryW > 0 ? -P.slotBias : P.slotBias);
            var wgt = baseW * (P.dryDens + (1 - P.dryDens) * Math.max(0, Math.min(1, sv)));
            // ...and a slope term, because vegetation seen against a backdrop is what
            // serrates a silhouette, and slope is where that happens.
            var ck2 = 1 + P.crestK * Math.max(0, Math.min(1, (0.985 - IDX.ny[t]) / 0.30));

            var want = IDX.area[t] * P.tuftDens * wgt * fall * cm * fk * ck2;
            var kt = Math.floor(want); if (R() < want - kt) kt++;

            for (var j = 0; j < kt && n < P.budget; j++) {
              var u = R(), w = R();
              if (u + w > 1) { u = 1 - u; w = 1 - w; }
              var bx = X[a] + u * (X[b] - X[a]) + w * (X[c] - X[a]);
              var by = Y[a] + u * (Y[b] - Y[a]) + w * (Y[c] - Y[a]);
              var bz = Z[a] + u * (Z[b] - Z[a]) + w * (Z[c] - Z[a]);

              // A STRAY STANDS IN THE DIRT. Pushed down the distance field's own gradient,
              // with its y taken from this triangle's PLANE rather than held constant — a
              // stray held at the old y floats on a slope, and a floating blade at 0.4 m is
              // exactly the seam artefact this is here to remove.
              var isStray = false;
              if (fr > P.strayFr && R() < P.stray && occGrad(bx, bz, gr)) {
                isStray = true;
                var push = fd + (0.15 + 0.85 * R()) * P.strayMax;
                var nx2 = bx + gr[0] * push, nz2 = bz + gr[1] * push;
                var e1x = X[b] - X[a], e1z = Z[b] - Z[a], e1y = Y[b] - Y[a];
                var e2x = X[c] - X[a], e2z = Z[c] - Z[a], e2y = Y[c] - Y[a];
                var det = e1x * e2z - e1z * e2x;
                if (Math.abs(det) > 1e-6) {
                  var rx = nx2 - X[a], rz = nz2 - Z[a];
                  var uu = (rx * e2z - rz * e2x) / det, ww = (e1x * rz - e1z * rx) / det;
                  bx = nx2; bz = nz2; by = Y[a] + uu * e1y + ww * e2y;
                  // A STRAGGLER STANDS ON THE PATH, NOT IN IT. The plane it just took its
                  // height from is the TERRAIN, and the thing it was pushed onto is proud
                  // of that terrain by anything from 2 cm (a bedding ring) to a step (a
                  // house floor). Without this the plant is planted at the height of the
                  // ground BESIDE the paving and the paving draws over its lower stem —
                  // the "grass clipping through the path" read, and its actual mechanism.
                  // Only ever a LIFT: pulling a plant down to a surface it is standing
                  // above would bury the ones the field is wrong about.
                  // ...AND THE LIFT IS BOUNDED, WHICH THE FIRST BUILD LEARNED IN ONE
                  // FRAME. `occTop` is the max height of any HARD triangle in the cell,
                  // and `ow_f2_tiles` / `ow_f2_plaster` are in that set because a wall
                  // footing is a seam — so under a house the cell's top is THE ROOF, and
                  // an unbounded lift planted grass and flowers on the roofs of Emberbrook
                  // (r3-meadow, caught by eye against t2-meadow's clean roof). A surface a
                  // straggler could have stepped onto is proud of its terrain by
                  // centimetres; anything higher is a BUILDING OVER the plant, not the
                  // ground under it, and the plant stays where the terrain put it.
                  var top = occTop(bx, bz);
                  if (top !== null && top > by && top - by < P.strayLift) by = top + 0.004;
                }
              }
              if (zone) { var zn = zone(bx, bz); if (zn === 'water') continue; }
              // ---- THE SEAM, RESOLVED WHERE THE PLANT IS ------------------------------
              // Two array reads, and they are what turn a triangle-scale shoulder into a
              // 0.6 m one. A stray is exempt because a stray was PUT there on purpose —
              // refusing it here would delete the only plants that cross the seam at all,
              // which is the whole mechanism that stops a path edge being a line.
              if (!isStray && occHard(bx, bz)) continue;
              var frb = fr;
              if (!isStray) {
                var fdb = occD(bx, bz);
                frb = fdb < P.fringeD ? (1 - fdb / P.fringeD) : 0;
              }
              var dd = Math.hypot(bx - cx, bz - cz);

              // ---- the tuft's own identity, shared by its blades -----------------------
              var hBase = (P.hMin + Math.pow(R(), P.hPow) * (P.hMax - P.hMin)) *
                          (1 + P.grow * (dd / r1)) *
                          (1 - P.clumpH * 0.5 + P.clumpH * cl) *
                          (1 + P.fringeH * frb) * (isStray ? P.strayH : 1);
              // THE ANGULAR WIDTH FLOOR (see `wgrow`): the blade gets wider with distance so
              // its apparent width holds, and this is the term that puts cover back on the
              // 20-50 m hillside. It scales WIDTH ONLY — height already has `grow`, and
              // widening a blade without lengthening it is what keeps a far clump reading as
              // grass rather than as a shrub.
              var wg = 1 + P.wgrow * Math.pow(Math.min(1, dd / r1), P.wgrowP);
              var dryP = Math.min(0.95, P.dryFrac * (dryW > 0 ? P.dryBias : 1) *
                                        (1 + (P.dryBias - 1) * frb));
              var isDry = dryW > 0 ? (R() < P.dryOnDry + (1 - P.dryOnDry) * dryP) : (R() < dryP);
              var dw = (1 - 0.7 * (dd / r1));
              var jv = P.jitV * dw, jh = P.jitH * dw;
              var tv = (1 - jv * 0.5) + R() * jv;
              var th = (R() - 0.5) * jh;
              var cr = COL ? COL.getX(a) + u * (COL.getX(b) - COL.getX(a)) + w * (COL.getX(c) - COL.getX(a)) : 0.5;
              var cg = COL ? COL.getY(a) + u * (COL.getY(b) - COL.getY(a)) + w * (COL.getY(c) - COL.getY(a)) : 0.5;
              var cb = COL ? COL.getZ(a) + u * (COL.getZ(b) - COL.getZ(a)) + w * (COL.getZ(c) - COL.getZ(a)) : 0.5;
              var tr = cr * TM[0] * P.lift * tv * (1 + th);
              var tg = cg * TM[1] * P.lift * tv * (1 - th * 0.55);
              var tb = cb * TM[2] * P.lift * tv * 0.98 * (1 - th * 0.9);
              if (isDry) { tr *= P.dryTint[0]; tg *= P.dryTint[1]; tb *= P.dryTint[2]; }
              else if (dryW > 0) { tr *= P.grassOnDry[0]; tg *= P.grassOnDry[1]; tb *= P.grassOnDry[2]; }

              var nb = P.bptMin + ((R() * (P.bptMax - P.bptMin + 1)) | 0);
              nb = Math.max(2, Math.round(nb * (1 - P.farThin * (dd / r1))));
              if (isStray) nb = Math.max(2, nb - 3);

              // ---- ROUND 3: the weed and the sedge ------------------------------------
              // THEY ARE PAID FOR OUT OF THE BLADES, NOT ADDED TO THEM. A rosette is 36
              // triangles and a tussock 48 against a blade's 6, so a tuft that draws one
              // drops most of its blades: the plant STANDS WHERE THE GRASS WOULD HAVE
              // BEEN, which is the right picture — two species do not occupy the same
              // 8 cm. `n` is charged their real cost so the budget valve still means what
              // it says.
              // BUT THE SUBSTITUTION DOES NOT MAKE THEM FREE, AND THE MEASURED A/B SAYS SO.
              // An earlier draft of this comment claimed "two assets for roughly no
              // triangles"; the true A/B on one bundle (closeup, r2 vs f3) is 808 848 ->
              // 964 794 scatter triangles, +19.3%, and 4 -> 6 draws. The saving is real and
              // the round spent it: `tuftDens` 10.5 -> 11.4 put 2 586 blades back in the
              // same breath, so it never reaches the total. Substitution bounds the cost of
              // a species; it does not pay for one.
              var near = 1 - Math.min(1, dd / r1);
              // NEITHER OF THEM MAY BE A STRAGGLER. A stray is deliberately pushed PAST
              // the seam and now stands on top of the paving (see occTop), which is right
              // for a few short blades and wrong for a 0.37 m rosette: the first build put
              // pale dock leaves lying flat across the middle of the road and they read as
              // litter, not as plants. The module's own note for `strayH` already says what
              // a straggler is — a plant that has crossed the edge and GETS TRODDEN — and
              // neither of these two assets is that plant.
              var drewBig = isStray;
              if (P.weed > 0 && !drewBig && n + 5 < P.budget) {
                var wv2 = weedAt(bx, bz);
                if (wv2 > P.weedT) {
                  var pw = P.weedPer * P.weed * (wv2 - P.weedT) / (1 - P.weedT) *
                           (1 + (P.weedFringe - 1) * frb) * (1 + (P.weedNear - 1) * near);
                  if (R() < pw) {
                    var ws = P.weedS * (1 + (R() - 0.5) * 2 * P.weedJ) * (1 + P.grow * (dd / r1));
                    q.setFromAxisAngle(up, R() * Math.PI * 2);
                    axis.set(Math.cos(R() * 6.283), 0, Math.sin(R() * 6.283));
                    // a rosette sits ON the ground and takes its tilt from it, so the lean
                    // is a third of a blade's: a weed leaning 20 degrees is a weed that has
                    // been stepped on, which is a different story than the one being told.
                    lean.setFromAxisAngle(axis, (R() - 0.5) * P.lean * 0.34);
                    q.multiply(lean);
                    vp.set(bx, by - 0.010, bz);
                    // the horizontal gain goes on BOTH ground axes, unlike a blade: this is
                    // a 3D rosette, not a card, so scaling one axis would shear it.
                    vs.set(ws * wg, ws, ws * wg);
                    m4.compose(vp, q, vs);
                    for (var ew = 0; ew < 16; ew++) WM.push(m4.elements[ew]);
                    var wj = 0.92 + 0.16 * R();
                    WC.push(tr * wj, tg * wj * 1.02, tb * wj * 0.94);
                    n += 5; nW++; drewBig = true;
                    nb = Math.max(1, nb - 3);
                  }
                }
              }
              if (P.sedge > 0 && !drewBig && n + 8 < P.budget) {
                var sv3 = sedgeAt(bx, bz);
                if (sv3 > P.sedgeT) {
                  var flat = 1 + (P.sedgeFlat - 1) * Math.max(0, Math.min(1, (IDX.ny[t] - 0.86) / 0.14));
                  var ps = P.sedgePer * P.sedge * (sv3 - P.sedgeT) / (1 - P.sedgeT) *
                           (dryW > 0 ? P.sedgeDry : 1) * flat *
                           (1 + (P.sedgeNear - 1) * near);
                  if (R() < ps) {
                    var ss = P.sedgeS * (1 + (R() - 0.5) * 2 * P.sedgeJ) * (1 + P.grow * (dd / r1));
                    q.setFromAxisAngle(up, R() * Math.PI * 2);
                    axis.set(Math.cos(R() * 6.283), 0, Math.sin(R() * 6.283));
                    lean.setFromAxisAngle(axis, (R() - 0.5) * P.lean * 0.45);
                    q.multiply(lean);
                    vp.set(bx, by - 0.020, bz);
                    vs.set(ss * wg, ss, ss * wg);
                    m4.compose(vp, q, vs);
                    for (var es = 0; es < 16; es++) SM.push(m4.elements[es]);
                    var sjt = 0.90 + 0.20 * R();
                    // the COOL member of the family, and it is explicit rather than
                    // inherited: f2's `grassOnDry` finding is that a plant which takes its
                    // colour from its own ground cannot disagree with its own ground.
                    SC.push(tr * sjt * 0.88, tg * sjt, tb * sjt * 1.10);
                    n += 8; nS++; drewBig = true;
                    nb = Math.max(1, nb - 4);
                  }
                }
              }
              nT++;
              for (var bi = 0; bi < nb && n < P.budget; bi++) {
                // ROOTS INSIDE ONE TUFT, not one root: blades that share a point read as a
                // starburst. A small disc of roots is what makes a clump occlude itself.
                var ang = R() * 6.2831853, rad = P.tuftR * Math.sqrt(R());
                var ox = Math.cos(ang) * rad, oz = Math.sin(ang) * rad;
                var kind = R() < P.seedFrac ? 2 : (R() < P.shortFrac ? 0 : 1);
                var sj = 1 + (R() - 0.5) * 2 * P.sizeJit;
                var h = hBase * (1 + (sj - 1) * 0.5);
                var sw = sj * wg;                       // width carries the distance gain
                q.setFromAxisAngle(up, R() * Math.PI * 2);
                axis.set(Math.cos(R() * 6.283), 0, Math.sin(R() * 6.283));
                // blades in one tuft lean OUTWARD from its centre as well as randomly —
                // a clump is a fan, not a bundle
                lean.setFromAxisAngle(axis, (R() - 0.5) * P.lean + rad * 1.1);
                q.multiply(lean);
                vp.set(bx + ox, by - 0.015, bz + oz);
                // X IS THE BLADE'S WIDTH AXIS AND Z IS ITS BEND (bladeGeo pushes +-tw on x
                // and `bend*t*t` on z), so the gain goes on X ALONE. Putting it on Z as well
                // multiplies the forward curve by the same 2.5x and lays every far blade
                // flat on the ground — a wider blade, not a collapsed one.
                vs.set(sw, h, sj);
                m4.compose(vp, q, vs);
                var MM = MB[kind], CC = MC[kind];
                for (var e = 0; e < 16; e++) MM.push(m4.elements[e]);
                var bj = 1 + (R() - 0.5) * P.jitB;
                CC.push(tr * bj, tg * bj, tb * bj * (1 - (R() - 0.5) * 0.08));
                n++;
              }

              // ---- flowers -------------------------------------------------------------
              // In PATCHES and at TRANSITIONS. `flPer` is a per-tuft probability here, which
              // is what keeps flowers inside the same clumps the grass is in rather than
              // sprinkled over the bare gaps between them.
              if (P.flowers > 0) {
                var pv = patchAt(bx, bz);
                if (pv > P.flPatchT) {
                  // flNear: the per-tuft probability is spent where the flowers can be SEEN.
                  // Tuft count grows as the annulus area, so a flat probability puts most of
                  // the population past 30 m by arithmetic alone — which is what it did.
                  var pp = P.flPer * P.flowers * (pv - P.flPatchT) / (1 - P.flPatchT) *
                           (1 + (P.flFringe - 1) * frb) *
                           (1 + (P.flNear - 1) * (1 - Math.min(1, dd / r1)));
                  if (R() < pp) {
                    var sp = FLOWER[(vhash(Math.floor(bx / 7), Math.floor(bz / 7)) * 3) | 0];
                    var fh = P.flH * (0.75 + 0.5 * R());
                    q.setFromAxisAngle(up, R() * Math.PI * 2);
                    vp.set(bx + (R() - 0.5) * 0.2, by - 0.01, bz + (R() - 0.5) * 0.2);
                    // the head gets the blades' angular floor too — r1 scaled Y only, so a
                    // flower was the one thing in the frame with no size compensation at all.
                    var fw = P.flW * wg;
                    vs.set(fw, fh, fw);
                    m4.compose(vp, q, vs);
                    for (var e2 = 0; e2 < 16; e2++) FM.push(m4.elements[e2]);
                    var fj = 0.9 + 0.2 * R();
                    FC.push(sp[0] * fj, sp[1] * fj, sp[2] * fj);
                  }
                }
              }
            }
          }
        }
      }
    }

    clear();
    if (!n) { LASTAT = { x: p.x, z: p.z }; return 0; }
    var mat = scatterMat();
    var grp = new T.Group(); grp.name = GROUP;
    var made = [];
    function addIM(geo, marr, carr, nm) {
      var cnt = marr.length / 16; if (!cnt) { geo.dispose(); return; }
      var im = new T.InstancedMesh(geo, mat, cnt);
      im.instanceMatrix = new T.InstancedBufferAttribute(new Float32Array(marr), 16);
      im.instanceMatrix.needsUpdate = true;
      if (carr.length === cnt * 3) {
        im.instanceColor = new T.InstancedBufferAttribute(new Float32Array(carr), 3);
        im.instanceColor.needsUpdate = true;
      }
      im.frustumCulled = false;      // instanced bounds lie about a carpet this wide
      // RECEIVE, DO NOT CAST. A carpet that ignores the shadow map is BRIGHTER than the
      // ground inside every tree shadow and darker than it outside — speckle in both
      // directions, and it undoes the terminator the lighting lane bought. Casting would
      // cost 150k instances in the depth pass for shadows nothing resolves at 3-8 px.
      im.castShadow = false; im.receiveShadow = true;
      im.name = nm;                  // veg_ => play3d's noStand test can never adopt it
      grp.add(im); MESHES.push(im); made.push(nm + ':' + cnt);
    }
    addIM(bladeGeo(0), MB[0], MC[0], 'veg_owd_short');
    addIM(bladeGeo(1), MB[1], MC[1], 'veg_owd_med');
    addIM(bladeGeo(2), MB[2], MC[2], 'veg_owd_seed');
    addIM(weedGeo(), WM, WC, 'veg_owd_weed');
    addIM(sedgeGeo(), SM, SC, 'veg_owd_sedge');
    addIM(flowerGeo(), FM, FC, 'veg_owd_flower');
    sc.add(grp);                     // scene ONLY: collide/walkRef/allMeshes never touched
    NBLADE = n;
    LASTAT = { x: p.x, z: p.z, tufts: nT, weeds: nW, sedges: nS, made: made };
    LASTMS = ((performance && performance.now) ? performance.now() : 0) - t0;
    return n;
  }

  // ===================================================================================
  // THE SHARED FOLIAGE MATERIAL — one shader edit, every plant in the frame
  // ===================================================================================
  // AND IT MUST BE WRITTEN AS AN INCLUDE EDIT. three.js calls onBeforeCompile BEFORE
  // resolveIncludes, so what the hook is handed is the template with `#include <chunk>`
  // still in it, not the expanded chunk. R6 paid for this once with a patch that matched
  // nothing and would have shipped as a no-op; every replace below targets an include, and
  // the one place that needs the chunk's INSIDE pulls the chunk out of THREE.ShaderChunk and
  // inlines it, which is version-robust because it is the shipping text rather than a copy.
  //
  // WHICH MATERIALS GET WHAT. The shared terms (translucency, highlight desaturation,
  // roughness) go on everything green, canopy included — they are one edit by design and the
  // tree lane was told this lane owns the shader. The albedo value->hue REMAP goes only on
  // the materials this lane owns, so the tree lane's canopy albedo work cannot be fought
  // over the same pixels.
  // (bark is deliberately NOT here: a trunk is not translucent, and a highlight clamp
  // authored for leaf tips has no business on wood.)
  var FOL_SHARED = ['ow_f2_canopy', 'ow_f2_leaf'];
  var FOL_OWNED = ['ow_f2_tuft', 'ow_f2_flower', 'ow_f2_green',
                   'ow_valley_bushcore', 'ow_valley_bushcard'];

  function chunkOr(name, fallback) {
    try { var s = TH().ShaderChunk[name]; if (typeof s === 'string' && s.length) return s; }
    catch (e) {}
    return fallback;
  }

  var TRANS_FN =
    'uniform float owdTrans; uniform vec3 owdTransCol; uniform float owdTransPow;\n' +
    'uniform float owdTransMul;\n' +
    'uniform float owdHiA; uniform float owdHiB; uniform float owdHiAmt;\n' +
    'uniform float owdRemap; uniform float owdVComp; uniform float owdVMid;\n' +
    'uniform float owdVFloor; uniform float owdHueSp; uniform float owdSat;\n' +
    'uniform float owdTuftFade; uniform vec3 owdEye; uniform vec2 owdFadeAB;\n' +
    'varying vec3 vOwdW;\n' +
    // THE TRANSLUCENCY. A leaf lit from behind glows, and the glow is strongest when the
    // VIEWER is looking down-sun through it. `directLight.color` already has the shadow
    // factor applied at this point in lights_fragment_begin, which is exactly why the hook
    // goes there and not at lights_fragment_end: a leaf in shade must not glow.
    'void owdTransAdd(const in IncidentLight dl, const in vec3 nrm, const in vec3 vdir,\n' +
    '                 const in vec3 alb, inout ReflectedLight rl) {\n' +
    '  float bk = max(0.0, -dot(nrm, dl.direction));\n' +
    '  float fw = max(0.0, -dot(vdir, dl.direction));\n' +
    '  float tr = owdTrans * owdTransMul * bk * (0.30 + 0.70 * pow(fw, owdTransPow));\n' +
    '  rl.indirectDiffuse += dl.color * owdTransCol * alb * tr;\n' +
    '}\n';

  // THE TRANSLUCENCY LEVEL IS PER MATERIAL, AND IT IS MEASURED, NOT TASTE. At one global
  // 0.55 the canopy box on the meadow plate went L50 0.452 -> 0.690 with saturation
  // 0.312 -> 0.258: an additive term large enough to wash a dense crown pale, on the exact
  // asset the tree lane is about to re-author. A tree crown presents far more back-facing
  // card area per screen pixel than a grass blade does, so the same coefficient is a rim on
  // one and a flood on the other. The SHADER is still one edit; only the level differs.
  var TRANS_MUL = { ow_f2_canopy: 0.42, ow_f2_leaf: 0.60, ow_valley_bushcard: 0.85,
                    ow_valley_bushcore: 0.70 };

  function patchFoliage(mat, owned) {
    if (!mat || PATCHED['F' + mat.uuid]) return false;
    PATCHED['F' + mat.uuid] = true;
    mat.roughness = P.rough;
    var isTuft = mat.name === 'ow_f2_tuft';
    var tmul = TRANS_MUL[mat.name] !== undefined ? TRANS_MUL[mat.name] : 1.0;
    mat.onBeforeCompile = function (sh) {
      sh.uniforms.owdTransMul = { value: tmul };
      sh.uniforms.owdTrans = { value: P.trans };
      sh.uniforms.owdTransCol = { value: new (TH().Color)(P.transCol[0], P.transCol[1], P.transCol[2]) };
      sh.uniforms.owdTransPow = { value: P.transPow };
      sh.uniforms.owdHiA = { value: P.hiA };
      sh.uniforms.owdHiB = { value: P.hiB };
      sh.uniforms.owdHiAmt = { value: P.hiAmt };
      sh.uniforms.owdRemap = { value: owned ? P.remap : 0.0 };
      sh.uniforms.owdVComp = { value: P.vComp };
      sh.uniforms.owdVMid = { value: P.vMid };
      sh.uniforms.owdVFloor = { value: P.vFloor };
      sh.uniforms.owdHueSp = { value: P.hueSpread };
      sh.uniforms.owdSat = { value: P.sat };
      sh.uniforms.owdTuftFade = { value: isTuft ? P.tuftFade : 0.0 };
      sh.uniforms.owdEye = { value: new (TH().Vector3)() };
      sh.uniforms.owdFadeAB = { value: new (TH().Vector2)(P.tuftFadeA, P.tuftFadeB) };
      UNIS.push(sh.uniforms);

      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vOwdW;')
        .replace('#include <begin_vertex>',
          '#include <begin_vertex>\nvOwdW = (modelMatrix * vec4(transformed,1.0)).xyz;');

      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\n' + TRANS_FN);

      // ---- the bundle's own spiked tufts, dithered out of the near band ---------------
      // A hard radius pops; a HASHED dither over a 28 m band reads as thinning, and the
      // thing it thins toward is this module's own clumps. It is a stopgap for an asset
      // this lane cannot rebuild, and it is named as one.
      if (isTuft) {
        sh.fragmentShader = sh.fragmentShader.replace('#include <clipping_planes_fragment>',
          '#include <clipping_planes_fragment>\n' +
          '{ float dw = distance(vOwdW.xz, owdEye.xz);\n' +
          '  float keep = smoothstep(owdFadeAB.x, owdFadeAB.y, dw);\n' +
          '  float hsh = fract(sin(dot(floor(vOwdW.xz*3.0), vec2(127.1,311.7)))*43758.5453);\n' +
          '  if (owdTuftFade > 0.5 && hsh > keep) discard; }');
      }

      // ---- albedo: NARROW VALUE, WIDE HUE ---------------------------------------------
      // The near-black cores are baked into the art and a dark core is what makes a card
      // read as a painted texture rather than as a plant. Compress the value range toward
      // vMid with a floor, then spend the range that was there on HUE — dark goes blue-
      // green, light goes yellow-green — at roughly constant luminance, and add a little
      // chroma. This is the one term the tree lane's canopy does not get.
      sh.fragmentShader = sh.fragmentShader.replace('#include <color_fragment>',
        '#include <color_fragment>\n' +
        '#ifdef OWD_REMAP\n' +
        '{ vec3 c0 = diffuseColor.rgb;\n' +
        '  float l0 = max(1e-4, dot(c0, vec3(0.2126,0.7152,0.0722)));\n' +
        '  float l1 = max(owdVFloor, owdVMid + (l0 - owdVMid) * owdVComp);\n' +
        '  float tt = clamp((l0 - owdVMid) / 0.28, -1.0, 1.0);\n' +
        '  vec3 hs = vec3(1.0 + owdHueSp * tt * 0.55, 1.0, 1.0 - owdHueSp * tt);\n' +
        '  vec3 c1 = c0 * (l1 / l0) * hs;\n' +
        '  float lm = dot(c1, vec3(0.2126,0.7152,0.0722));\n' +
        '  c1 = mix(vec3(lm), c1, owdSat);\n' +
        '  diffuseColor.rgb = mix(c0, max(c1, vec3(0.0)), owdRemap); }\n' +
        '#endif\n');
      if (owned) sh.fragmentShader = '#define OWD_REMAP\n' + sh.fragmentShader;

      // ---- translucency, INSIDE the light loop where the shadow factor lives ----------
      var lb = chunkOr('lights_fragment_begin', null);
      if (lb && /RE_Direct\s*\(/.test(lb)) {
        var hooked = lb.replace(/(RE_Direct\s*\([^;]*\);)/g,
          '$1\n\t\towdTransAdd( directLight, normal, normalize( vViewPosition ), diffuseColor.rgb, reflectedLight );');
        sh.fragmentShader = sh.fragmentShader.replace('#include <lights_fragment_begin>', hooked);
      } else if (window.console) {
        console.warn('[owd] lights_fragment_begin unavailable — no translucency on ' + mat.name);
      }

      // ---- the highlight stops going chartreuse ---------------------------------------
      // outgoingLight is declared in the main body immediately before <opaque_fragment>,
      // so this is an include-boundary edit like every other one here.
      sh.fragmentShader = sh.fragmentShader.replace('#include <opaque_fragment>',
        '{ float owl = dot(outgoingLight, vec3(0.2126,0.7152,0.0722));\n' +
        '  float owk = smoothstep(owdHiA, owdHiB, owl) * owdHiAmt;\n' +
        '  outgoingLight = mix(outgoingLight, vec3(owl), owk); }\n' +
        '#include <opaque_fragment>');
    };
    mat.needsUpdate = true;
    return true;
  }

  // every patched material's uniform block, so a live sweep (OWD.set) reaches the shader
  // without a recompile — and so the tuft fade can track the player.
  var UNIS = [];
  function pushUnis() {
    var SIM = window.SIM, p = (SIM && SIM.pos) ? SIM.pos() : null;
    for (var i = 0; i < UNIS.length; i++) {
      var u = UNIS[i];
      if (u.owdTrans) u.owdTrans.value = P.trans;
      if (u.owdTransPow) u.owdTransPow.value = P.transPow;
      if (u.owdTransCol) u.owdTransCol.value.setRGB(P.transCol[0], P.transCol[1], P.transCol[2]);
      if (u.owdHiA) u.owdHiA.value = P.hiA;
      if (u.owdHiB) u.owdHiB.value = P.hiB;
      if (u.owdHiAmt) u.owdHiAmt.value = P.hiAmt;
      if (u.owdVComp) u.owdVComp.value = P.vComp;
      if (u.owdVMid) u.owdVMid.value = P.vMid;
      if (u.owdVFloor) u.owdVFloor.value = P.vFloor;
      if (u.owdHueSp) u.owdHueSp.value = P.hueSpread;
      if (u.owdSat) u.owdSat.value = P.sat;
      if (u.owdFadeAB) u.owdFadeAB.value.set(P.tuftFadeA, P.tuftFadeB);
      if (u.owdTuftFade && u.owdTuftFade.value > 0) u.owdTuftFade.value = P.tuftFade;
      if (u.owdEye && p) u.owdEye.value.set(p.x, p.y, p.z);
    }
  }

  function patchAllFoliage() {
    var sc = SCN(); if (!sc) return 0;
    var n = 0;
    sc.traverse(function (m) {
      if (!m.isMesh || !m.material) return;
      var mn = m.material.name || '';
      if (FOL_OWNED.indexOf(mn) >= 0) { if (patchFoliage(m.material, true)) n++; }
      else if (FOL_SHARED.indexOf(mn) >= 0) { if (patchFoliage(m.material, false)) n++; }
    });
    return n;
  }

  // ---- pixel-scale ground material --------------------------------------------------
  // Three octaves of world-space value noise multiplied into diffuse. The finest is the one
  // that matters (gravel speckle in the worn dirt is most of what separates the refs' path
  // from ours) and it is also the one that aliases, so it is faded out by view depth. Worn
  // ground gets more of it than turf: the terrain builder already split those into separate
  // primitives, so "more grit on the dirt" is a per-material amount, not a mask.
  function patchGround() {
    var sc = SCN(); if (!sc) return 0;
    var AMT = { ow_f2_ter_grass: 0.62, ow_f2_ter_dry: 1.0, ow_f2_road: 1.15,
                ow_f2_dockpath: 1.0 };
    var n = 0;
    sc.traverse(function (m) {
      if (!m.isMesh || !m.material) return;
      var mn = m.material.name || '';
      if (!(mn in AMT) || PATCHED[m.material.uuid]) return;
      PATCHED[m.material.uuid] = true;
      var k = AMT[mn], mat = m.material;
      mat.onBeforeCompile = function (sh) {
        sh.uniforms.owdAmt = { value: P.grit * k };
        sh.uniforms.owdFar = { value: P.gritFar };
        sh.vertexShader = sh.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec3 vOWDW;\nvarying float vOWDD;')
          .replace('#include <begin_vertex>',
            '#include <begin_vertex>\nvOWDW = (modelMatrix * vec4(transformed,1.0)).xyz;\n' +
            'vOWDD = -(modelViewMatrix * vec4(transformed,1.0)).z;');
        sh.fragmentShader = sh.fragmentShader
          .replace('#include <common>', '#include <common>\n' +
            'varying vec3 vOWDW; varying float vOWDD;\n' +
            'uniform float owdAmt; uniform float owdFar;\n' +
            'float owdH(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }\n' +
            'float owdN(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);\n' +
            '  return mix(mix(owdH(i),owdH(i+vec2(1,0)),f.x),mix(owdH(i+vec2(0,1)),owdH(i+vec2(1,1)),f.x),f.y); }')
          .replace('#include <color_fragment>', '#include <color_fragment>\n' +
            '{ vec2 wp = vOWDW.xz;\n' +
            // ~1.4 m patches, ~0.35 m mottle, ~0.09 m grit. The grit is the one the eye
            // reads as material and the one that stipples at distance, so it alone is
            // faded out by depth.
            '  float grit = smoothstep(owdFar, owdFar*0.35, vOWDD);\n' +
            '  float v = owdN(wp*0.70)*0.42 + owdN(wp*2.90)*0.30 + owdN(wp*11.0)*0.28*grit;\n' +
            '  float amt = owdAmt * (0.55 + 0.45*grit);\n' +
            '  diffuseColor.rgb *= (1.0 - amt*0.5 + amt*v); }');
      };
      mat.needsUpdate = true; n++;
    });
    return n;
  }

  // ---- arming -----------------------------------------------------------------------
  // A SOFTWARE RASTERISER CANNOT AFFORD A CARPET, AND HALF THIS REPO'S GATES USE ONE.
  // tools/cdp.mjs:149 and transition_test.mjs:180 launch Chrome with
  // `--use-angle=swiftshader --disable-gpu`. The scatter is ~1 M triangles of overdraw-heavy
  // instancing; on the GPU path it costs nothing measurable, on SwiftShader every one of
  // those triangles is rasterised by the CPU. So it is a GPU feature: on a software context
  // the module keeps the material patches (a few ALU ops per fragment) and places nothing.
  // WHAT IS MEASURED AND WHAT IS NOT: the DETECTION is measured — booted under the gates'
  // own flags, OWD.state() comes back {software:true, blades:0}. The saving is NOT isolated.
  // Do not quote a speedup from this comment.
  var SOFT = null;
  function softwareGL() {
    if (SOFT !== null) return SOFT;
    SOFT = false;
    try {
      var ren = null; try { ren = R; } catch (e) {}
      var gl = ren && ren.getContext && ren.getContext();
      if (!gl) return SOFT;                       // undecided: retried on the next poll
      SOFT = null;
      var s = '';
      var dbg = gl.getExtension('WEBGL_debug_renderer_info');
      if (dbg) s += ' ' + (gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || '');
      s += ' ' + (gl.getParameter(gl.RENDERER) || '') + ' ' + (gl.getParameter(gl.VENDOR) || '');
      SOFT = /swiftshader|softwar|llvmpipe|mesa offscreen/i.test(s);
      if (SOFT) console.warn('[owd] software WebGL (' + s.trim() + ') — scatter off');
    } catch (e) { SOFT = false; }
    return SOFT;
  }

  // `?owdetail=0` turns the whole module off — scatter AND material patches — so an A/B
  // capture never has to edit play3d.html to get a clean BEFORE. An art lane that has to
  // remove a script tag to photograph its own baseline will eventually photograph somebody
  // else's tree.
  function isOW() {
    try { if (new URLSearchParams(location.search).get('owdetail') === '0') return false; }
    catch (e) {}
    return /^ow-/.test(SKEY() || '');
  }

  var TICK = null, NPATCH = 0, NFOL = 0;
  function arm() {
    clear(); SRCS = null; OCC = null; LASTAT = null; NPATCH = 0; NFOL = 0;
    if (TICK) { clearInterval(TICK); TICK = null; }
    if (!isOW()) return;
    // THE BUNDLE IS NOT LOADED YET. This module arms at DOMContentLoaded and on 'eb-scene',
    // and BOTH can land before ow-valley's 45 MB GLB has finished parsing — at which point
    // sources() finds nothing and the patches patch nothing, silently and forever. So arming
    // only starts the poll; the poll does the work and keeps retrying. (A module that decides
    // at t=0 whether the world contains a thing is a module that ships off.)
    TICK = setInterval(function () {
      try {
        if (NPATCH < 2) NPATCH += patchGround();
        if (NFOL < 6) NFOL += patchAllFoliage();
        rebuild(false);
        pushUnis();
      } catch (e) {}
    }, 250);
  }

  window.OWD = {
    state: function () {
      var tris = 0;
      for (var i = 0; i < MESHES.length; i++) {
        var g = MESHES[i].geometry;
        tris += (g.index ? g.index.count / 3 : 0) * MESHES[i].count;
      }
      return { on: ON, scene: SKEY(), software: softwareGL(), blades: NBLADE,
               ms: +LASTMS.toFixed(1), at: LASTAT, params: JSON.parse(JSON.stringify(P)),
               sources: SRCS ? SRCS.map(function (s) { return s.mesh.name; }) : null,
               folPatched: NFOL, draws: MESHES.length, tris: tris };
    },
    occ: function () { return OCC ? { cells: OCC.cells, occ: OCC.occ, hard: OCC.hard, tris: OCC.tris,
                                      ms: OCC.ms, cell: OCC.cell, nx: OCC.nx, nz: OCC.nz } : null; },
    set: function (o) { for (var k in o) if (k in P) P[k] = o[k]; pushUnis(); return rebuild(true); },
    rebuild: rebuild,
    enable: function (v) { ON = v !== false; if (!ON) clear(); else rebuild(true); return ON; }
  };

  if (typeof window !== 'undefined') {
    // self-arm at load AND on every in-place scene swap, which is the module contract every
    // module in this runtime keeps (see play3d.html's sgAnnounce comment).
    window.addEventListener('eb-scene', function () {
      try { arm(); } catch (e) { console.error('[owd] eb-scene', e); }
    });
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(function () { try { arm(); } catch (e) { console.error('[owd] arm', e); } }, 0);
    } else {
      window.addEventListener('DOMContentLoaded', function () {
        try { arm(); } catch (e) { console.error('[owd] arm', e); }
      });
    }
  }
})();
