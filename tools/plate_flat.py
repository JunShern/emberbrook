#!/usr/bin/env python3
"""plate_flat.py — find UNSHADED FLAT FILLS in baked backdrops.

    python3 tools/plate_flat.py [scene-key]        default del-cine

WHAT IT CATCHES. A backdrop card, a haze plane rendered without its volume, a material
with no shading, an emissive slab standing in for atmosphere: all of them land in the
plate as a region of literally constant colour. Real painted geometry never does -- even
a flat wall carries a light gradient, a shadow, or texture noise. So "a large connected
region whose colour variance is ~0" is a reliable, art-direction-agnostic signature of
something that is not really there.

WHY IT EXISTS. The 2026-07-30 water-facing pass turned five cameras OUTWARD along the
gorge for the first time in the town's life. The probe render of the Crossing's new
yaw-195 frame showed a hard-edged salmon rectangle (RGB 155,91,61, per-pixel std 0.41,
4.3% of frame, ndc x -0.72..-0.33 y 0.52..1.00) sitting over the water. Scanning all 17
SHIPPED plates for the same fill returned 0.00% on every one -- so the object was always
there and had simply never been in frame while every camera looked INTO the cliff.

That is the general hazard of a re-aim pass and the reason this is a tool and not a note:
a town's far field is built for the angles it has been shot from, and the first camera to
look somewhere new is the first to find what was never finished there.

WHAT IT MUST NOT CATCH: THE SKY. The 2026-08-01 gate re-aim put sky in a Dellhollow frame
for the first time in the town's life and the screen flagged it at 1.75%, RGB 155,91,61 --
byte-for-byte the same colour the Crossing's real backdrop card reported. That is not a
tuning failure, it is the signature colliding: the world background and a card standing in
for the far field are BOTH a constant colour at the far plane, and the two plates alone
cannot tell them apart. Only a ray can, so the screen now casts one -- see sky_census.
"""
import sys, os, glob, json, subprocess, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE = sys.argv[1] if len(sys.argv) > 1 else 'del-cine'
# CALIBRATED, not chosen. At 0.2% this screen flagged 1 of 17 shipped plates: loop-stairs
# at 0.72%, which on inspection is a real pale panel with a cast shadow on it -- evenly
# lit geometry, not a card. The Crossing's actual card was 4.29%. 1% sits between them and
# keeps the screen worth a human's attention. This is a SCREEN: it produces candidates for
# eyes, never a verdict. Lower it when hunting, and expect large flat lit surfaces back.
MIN_FRAC = 0.01
BLOCK = 8                 # variance is measured over 8x8 blocks

# SKY EXCLUSION, calibrated on the two cases that collide. Instrument: sky_census below
# (800 rays, sc.ray_cast on the evaluated depsgraph of tools/blends/dellhollow-master.blend,
# 2026-08-01) -- the SAME function the screen calls, not a separate probe:
#
#   SKY   del-cine gate, the flagged band     773/800 rays hit NOTHING = 96.6% miss
#         (over the region's own pixel mask, which is what the screen casts. Over its
#          bounding box instead: 722/800 = 90.25%, the extra hits being fx_haze_south and
#          cliff_east_closure at the band's edges; the seam lane's independent bbox census
#          the same night sampled 706/800 = 88.25%.)
#   CARD  del-cine crossing, the documented     0/800 rays miss = 0.00% miss
#         backdrop card                        (800/800 hit `fx_haze_east`, the 8-vertex
#          slab named in tools/fx_haze_east_fix.py -- the one card this screen has ever
#          caught, restored to render-visible for the measurement)
#
# The gap is 88 points wide and the threshold only has to land inside it. 0.75 does, with
# room on both sides. It is deliberately NOT 0.90: the sky's own number moves between
# 88.25% and 96.6% on nothing but how the region is sampled, so a 0.90 gate would make the
# classification an artefact of the sampler. A card is hit by EVERY ray -- that is why a
# threshold this loose still cannot excuse one.
SKY_MISS_FRAC = 0.75
CENSUS_RAYS = 800         # matches the census the calibration above was measured with
BLENDER = os.environ.get('BLENDER', '/Applications/Blender.app/Contents/MacOS/Blender')

# Runs INSIDE Blender. Rebuilds the baked camera by cine_bake.build_cam's exact recipe
# (sensor_fit VERTICAL, angle_y = fov, aim via to_track_quat) -- bake and screen may not
# disagree about where the camera stands -- and rays the region's real pixels.
_CENSUS_SRC = r'''
import bpy, sys, json, math
from mathutils import Vector
job = json.load(open(sys.argv[sys.argv.index('--') + 1:][0]))
c = job['cam']
sc = bpy.context.scene
cd = bpy.data.cameras.new('plate_flat_census')
cd.sensor_fit = 'VERTICAL'
cd.angle_y = math.radians(c['fov'])
cd.clip_start, cd.clip_end = c['clip'][0], c['clip'][1]
ob = bpy.data.objects.new('plate_flat_census', cd)
sc.collection.objects.link(ob)
ob.location = Vector(c['pos'])
ob.rotation_euler = (Vector(c['aim']) - ob.location).to_track_quat('-Z', 'Y').to_euler()
# The screen audits a RENDERED plate, so the census must see the RENDER's object set.
# sc.ray_cast reads viewport visibility, which is a different flag -- without this a
# hide_render object standing in front of sky (fx_haze_east is exactly that, hidden by
# tools/fx_haze_east_fix.py) would be raycast into a card that contributed no pixel.
if job.get('restore'):                       # regression harness only: put a hidden card
    for o in bpy.data.objects:               # back on screen to prove it still flags
        if o.name in job['restore']: o.hide_render = False
for coll in bpy.data.collections:
    if coll.hide_render: coll.hide_viewport = True
for o in bpy.data.objects:
    if o.hide_render: o.hide_viewport = True
bpy.context.view_layer.update()
tanY = math.tan(cd.angle_y / 2.0)
M = ob.matrix_world; R = M.to_3x3(); origin = M.translation
dg = bpy.context.evaluated_depsgraph_get()
miss = 0; tally = {}
for ndx, ndy in job['ndc']:
    d = (R @ Vector((ndx * tanY * job['aspect'], ndy * tanY, -1.0))).normalized()
    hit, loc, nor, idx, obj, mw = sc.ray_cast(dg, origin, d, distance=cd.clip_end)
    if hit: tally[obj.name] = tally.get(obj.name, 0) + 1
    else:   miss += 1
json.dump({'miss': miss, 'rays': len(job['ndc']), 'tally': tally}, open(job['out'], 'w'))
'''


def sky_census(scene, cam, mask, restore=()):
    """Is this flagged region the WORLD BACKGROUND rather than a card?

    Both read as one constant colour at the far plane, because cine_bake.py deletes the
    volume objects before the depth pass -- so the depth plate reports 'no surface' for a
    card and for sky alike and CANNOT separate them. A ray can: the card is real geometry
    that is merely absent from the depth pass, so rays hit it; sky is the absence of
    geometry, so they hit nothing. That is the whole discriminator, and it is the
    mechanism, not a heuristic about tone or position (the sky is not always up, and a
    card standing in for the far field is usually up).

    Returns {'miss': n, 'rays': n, 'frac': f, 'tally': {...}}, or None if the census could
    not be run. None FAILS CLOSED -- the caller keeps flagging. A screen that quietly
    stops screening because a tool path moved is worse than the defect it was built for.

    `restore` names objects to un-hide (in memory, never saved) before casting. It exists
    for ONE reason: the only card this screen ever caught is now hide_render, so the
    regression proof that the card class is still caught has to put it back. See the
    SKY EXCLUSION note above for both measurements.
    """
    if mask is None or not mask.any():
        return None
    d = os.path.join(ROOT, 'public/assets/scenes', scene)
    try:
        # meta.json's `source` is the bake's own record of which blend it came from --
        # the screen must ray the geometry that was RENDERED, not a same-named blend.
        blend = os.path.join(ROOT, json.load(open(os.path.join(d, 'meta.json')))['source'])
        c = [x for x in json.load(open(os.path.join(d, 'cine.json')))['cameras']
             if x['id'] == cam][0]
        if not (os.path.exists(blend) and os.path.exists(BLENDER)):
            return None
    except Exception:
        return None                      # interiors (depth.json carries no camera) and
                                         # any bundle without a blend: flag, never excuse
    H, W = mask.shape
    ys, xs = np.nonzero(mask)
    step = max(1, len(ys) // CENSUS_RAYS)          # deterministic stride, not a sample
    ys, xs = ys[::step][:CENSUS_RAYS], xs[::step][:CENSUS_RAYS]
    ndc = [[float((x + 0.5) / W * 2 - 1), float(1 - (y + 0.5) / H * 2)]
           for y, x in zip(ys, xs)]
    tmp = tempfile.mkdtemp(prefix='plate_flat_')
    try:
        job, out, src = (os.path.join(tmp, n) for n in ('job.json', 'out.json', 'c.py'))
        json.dump({'cam': c, 'aspect': W / H, 'ndc': ndc, 'out': out,
                   'restore': list(restore)}, open(job, 'w'))
        open(src, 'w').write(_CENSUS_SRC)
        subprocess.run([BLENDER, '-b', blend, '--python-exit-code', '1', '-P', src,
                        '--', job], capture_output=True, timeout=900)
        r = json.load(open(out))          # read the FILE, not stdout: addons print there
        r['frac'] = r['miss'] / r['rays'] if r['rays'] else 0.0
        return r
    except Exception:
        return None
    finally:
        for f in glob.glob(os.path.join(tmp, '*')):
            os.unlink(f)
        os.rmdir(tmp)

def far_plane_fill(bg_path, depth_path, far):
    """The EXACT signature of a render-only volume that rendered as a card.

    cine_bake.py deletes fog/haze/steam_vol/smoke objects before the DEPTH pass, and
    encodes 'no surface hit' as the far plane. So a region that is a constant colour in
    the beauty plate AND reads exactly the far plane in the depth plate is, provably,
    something that shaded like a solid and has no geometry: a volume rendered without
    its volumetrics. No heuristics about tone or shape -- this is the mechanism itself.

    It is also, unavoidably, the exact signature of open sky, which has no geometry
    either. Returns the region's own pixel MASK so sky_census can ray the region as it
    actually falls, not as its bounding box.
    """
    bg = np.asarray(Image.open(bg_path).convert('RGB'), dtype=np.int16)
    dp = np.asarray(Image.open(depth_path).convert('RGB'), dtype=np.float64)
    dep = dp[:, :, 0]*65536 + dp[:, :, 1]*256 + dp[:, :, 2]
    nohit = dep >= 16777215*0.999
    H, W = nohit.shape
    small = np.asarray(Image.fromarray(bg.astype(np.uint8)).resize((W, H), Image.NEAREST),
                       dtype=np.int16)
    if not nohit.any():
        return 0.0, None, None, None
    # among no-hit pixels, the dominant colour and how flat it is
    px = small[nohit]
    c = np.median(px, axis=0)
    same = nohit & (np.abs(small - c).max(2) <= 3)
    frac = same.sum() / (H*W)
    if frac < 1e-6:
        return 0.0, None, None, None
    ys, xs = np.nonzero(same)
    ndc = (xs.min()/W*2-1, xs.max()/W*2-1, 1-ys.max()/H*2, 1-ys.min()/H*2)
    return frac, np.round(c, 0), ndc, same

def flat_regions(path):
    im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)
    H, W, _ = im.shape
    h, w = H // BLOCK, W // BLOCK
    b = im[:h*BLOCK, :w*BLOCK].reshape(h, BLOCK, w, BLOCK, 3)
    var = b.std(axis=(1, 3)).max(axis=2)          # per-block colour spread
    mean = b.mean(axis=(1, 3))
    flat = var < 0.75                              # essentially constant
    if not flat.any():
        return 0.0, None, None, 0.0
    # largest connected run of flat blocks sharing one colour
    seen = np.zeros_like(flat); best = []
    for y in range(h):
        for x in range(w):
            if not flat[y, x] or seen[y, x]:
                continue
            c0 = mean[y, x]; stack = [(y, x)]; seen[y, x] = True; blob = []
            while stack:
                cy, cx = stack.pop(); blob.append((cy, cx))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < h and 0 <= nx < w and flat[ny, nx] and not seen[ny, nx] \
                       and np.abs(mean[ny, nx] - c0).max() <= 3:
                        seen[ny, nx] = True; stack.append((ny, nx))
            if len(blob) > len(best):
                best = blob; bc = c0
    if not best:
        return 0.0, None, None, 0.0
    P = np.array(best)
    frac = len(best) / (h * w)
    ys, xs = P[:, 0] * BLOCK, P[:, 1] * BLOCK
    ndc = (xs.min()/W*2-1, xs.max()/W*2-1, 1-ys.max()/H*2, 1-ys.min()/H*2)
    # RECTANGULARITY: what fraction of the blob's own bounding box it fills. A card is a
    # quad, so it fills its box; crushed shadow and blown highlight are organic and do not.
    bw = (P[:,1].max()-P[:,1].min()+1) * (P[:,0].max()-P[:,0].min()+1)
    rect = len(best) / bw if bw else 0.0
    return frac, np.round(bc, 0), ndc, rect

def verdict(scene, cam, frac, mask):
    """(trailing note, is_a_defect) for one plate's far-plane region.

    THREE outcomes, and the middle one is the point: below MIN_FRAC nothing is said; a
    flagged region that rays through to nothing is REPORTED AS SKY and is not a defect;
    everything else is a card. Sky is still printed, with its census, so a reader can see
    the region was considered and classified rather than silently dropped -- an exclusion
    nobody can see is indistinguishable from a screen that stopped working.
    """
    if frac < MIN_FRAC:
        return '', 0
    r = sky_census(scene, cam, mask)
    if r is None:
        return '   <== VOLUME RENDERED AS A CARD (no ray census — flagged unexamined)', 1
    if r['frac'] >= SKY_MISS_FRAC:
        return ('   ==  SKY, not a card: %d/%d rays hit nothing (%.1f%% miss)'
                % (r['miss'], r['rays'], 100 * r['frac'])), 0
    top = sorted(r['tally'].items(), key=lambda kv: -kv[1])[:2]
    return ('   <== VOLUME RENDERED AS A CARD: only %.1f%% of rays miss, they hit %s'
            % (100 * r['frac'], ', '.join('%s x%d' % kv for kv in top) or 'geometry')), 1


def _single_camera_bundle(scene):
    """An INTERIOR (or any tools/depth_bake.py bundle) is one camera and lays its
    files out flat -- background.png / depth.png / depth.json -- instead of
    cameras/<id>/{bg,depth}.png + cine.json.  The audit is identical; only the
    file layout differs, so it is resolved here rather than duplicated in a
    second script."""
    d = os.path.join(ROOT, 'public/assets/scenes', scene)
    bg = os.path.join(d, 'background.png')
    dp = os.path.join(d, 'depth.png')
    mj = os.path.join(d, 'depth.json')
    if not (os.path.exists(bg) and os.path.exists(dp) and os.path.exists(mj)):
        return None
    import json
    return [(scene, bg, dp, json.load(open(mj))['far'])]


if __name__ == '__main__':
    single = _single_camera_bundle(SCENE)
    if single:
        print('%-15s %7s  %-16s %s' % ('plate', 'card%', 'colour', 'ndc bbox'))
        bad = 0
        for cid, bgp, dpp, far in single:
            frac, c, ndc, mask = far_plane_fill(bgp, dpp, far)
            note, isbad = verdict(SCENE, cid, frac, mask)
            bad += isbad
            print('%-15s %6.2f%%  %-16s %s%s' % (
                cid, 100 * frac,
                '' if c is None else 'RGB %d,%d,%d' % tuple(c),
                '' if ndc is None else 'x %.2f..%.2f y %.2f..%.2f' % ndc, note))
            f2, c2, n2, rect = flat_regions(bgp)
            print('%-15s %6.2f%%  %-16s %s   (largest flat region, rect %.2f)' % (
                '  flat-fill', 100 * f2,
                '' if c2 is None else 'RGB %d,%d,%d' % tuple(c2),
                '' if n2 is None else 'x %.2f..%.2f y %.2f..%.2f' % n2, rect))
        print('\n%s — %d of %d plates carry a volume rendered as a card >= %.1f%%'
              % ('FLAG' if bad else 'clean', bad, len(single), 100 * MIN_FRAC))
        sys.exit(1 if bad else 0)

    pat = os.path.join(ROOT, 'public/assets/scenes', SCENE, 'cameras/*/bg.png')
    plates = sorted(glob.glob(pat))
    if not plates:
        sys.exit('no plates under ' + pat)
    import json
    cine = json.load(open(os.path.join(ROOT, 'public/assets/scenes', SCENE, 'cine.json')))
    FAR = {x['id']: x['depth']['far'] for x in cine['cameras'] if x.get('depth')}
    bad = 0
    sky = 0
    print('%-15s %7s  %-16s %s' % ('plate', 'card%', 'colour', 'ndc bbox'))
    for p in plates:
        cid = os.path.basename(os.path.dirname(p))
        dpath = os.path.join(os.path.dirname(p), 'depth.png')
        if not os.path.exists(dpath) or cid not in FAR:
            print('%-15s   (no depth plate — skipped)' % cid); continue
        frac, c, ndc, mask = far_plane_fill(p, dpath, FAR[cid])
        # A flagged region is a DEFECT only if rays find something there. The census runs
        # on flagged plates only, so a clean sweep still costs nothing but numpy.
        note, isbad = verdict(SCENE, cid, frac, mask)
        bad += isbad
        sky += (frac >= MIN_FRAC and not isbad)
        print('%-15s %6.2f%%  %-16s %s%s' % (
            cid, 100*frac,
            '' if c is None else 'RGB %d,%d,%d' % tuple(c),
            '' if ndc is None else 'x %.2f..%.2f y %.2f..%.2f' % ndc, note))
    print('\n%s — %d of %d plates carry a volume rendered as a card >= %.1f%% of frame%s'
          % ('FLAG' if bad else 'clean', bad, len(plates), 100*MIN_FRAC,
             '' if not sky else
             ' (%d further region(s) >= that size are SKY by ray census, not defects)' % sky))
    sys.exit(1 if bad else 0)
