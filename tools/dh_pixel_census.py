"""dh_pixel_census.py — WHAT IS THIS PIXEL ACTUALLY SHOWING?  Two stages, one tool.

  # stage 1 (no Blender): pick the pixels, in world space, off the SHIPPED plate
  python3 tools/dh_pixel_census.py sample --shot lockfive --mask crushed --region 0 \
      --n 400 --out /tmp/s.json

  # stage 2 (Blender): ask the master what those rays hit
  /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend \
      --python-exit-code 1 -P tools/dh_pixel_census.py -- rays --in /tmp/s.json

  # coverage: how much of each frame does a named volume card own, and at what tau
  Blender -b … -P tools/dh_pixel_census.py -- cover --shots lockfive,weave,gate --grid 192

WHY IT EXISTS.  `plate_probe` names a REGION and never an object; the second step has
always been an ad-hoc ray census, and this repo has now written down TWO ways that
step lies about the frame:

  * "A first-hit tally that does not drop `hide_render` objects is a lie about the
    frame" (DAYLOG 2026-08-02, the gate's top-left quadrant: a naive tally called
    `fx_haze_east` 57% of it while that card was `hide_render = True`).
  * "VOLUME CARDS ARE MESHES TO A RAY-CASTER" (DAYLOG 2026-08-01, tranche-2 custodian:
    a clearance cast hit `fx_haze_south`'s back face and dragged 3,746 vertices of
    cliff out through it).

Both are the same mistake — the ray-caster's object set is not the renderer's — and
both produce a CONFIDENT WRONG OBJECT NAME, which is the most expensive kind of
measurement here.  So this tool models the BEAUTY pass:

  * objects with `hide_render` are not in the render and are not in the cast;
  * a RENDER-ONLY VOLUME CARD (a material whose output has a Volume link and NO
    Surface link) is not a surface.  The ray MARCHES THROUGH it, accumulating optical
    depth tau = density x path length, and keeps going until it lands on something
    that actually shades.  The card is reported as an ATTENUATOR with its tau, never
    as a hit.

That distinction is the whole point.  A uniform-density volume box contributes
`1 - exp(-tau)` of a constant scattering term and multiplies everything behind it by
`exp(-tau)`; at tau 0.06 that is a 6% wash, not a surface.  Calling it "the object at
this pixel" attributes a black cliff to the sheet of air in front of it.

Note that the bake's DEPTH pass already deletes every haze/fog/smoke object by name
(cine_bake.py, "Delete render-only volumes FIRST"), so `depth.png` — and therefore
every world position stage 1 reconstructs — is ALREADY past the cards.  Stage 1 and
stage 2 are two independent instruments that must agree, and when they disagree the
disagreement is the finding.

Densities are read off the Volume Scatter / Principled Volume `Density` socket.  A
node-DRIVEN density cannot be read statically and is reported as `density=driven`
with tau omitted rather than silently taken as its default (mat_smoke's default is
0.0 and its real density is a noise texture).
"""
import os, sys, json, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
MODE = argv[0] if argv else ""


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


# ------------------------------------------------------------------ stage 1 ---
def stage_sample():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import numpy as np
    import plate_probe as pp

    shot = arg("--shot")
    mask = arg("--mask", "crushed")
    n = int(arg("--n", "400"))
    region = int(arg("--region", "-1"))
    seed = int(arg("--seed", "1"))
    out = arg("--out", "/tmp/dh_pixel_census.json")

    c, bg, d, void, P = pp.load(shot)
    N, bad = pp.normals(P, void)
    L = pp.lum(bg)
    H, W = L.shape

    if mask == "crushed":
        m = (L <= pp.DARK) & (pp.local_sd(L) <= pp.FLAT) & (~void)
    elif mask == "all":
        m = ~void
    elif mask == "box":
        b = [float(x) for x in arg("--box").split(",")]
        m = ((~void) & (P[..., 0] >= b[0]) & (P[..., 0] <= b[1])
             & (P[..., 1] >= b[2]) & (P[..., 1] <= b[3])
             & (P[..., 2] >= b[4]) & (P[..., 2] <= b[5]))
    else:
        raise SystemExit("unknown --mask %s" % mask)

    if region >= 0:                      # the nth-largest connected crushed component
        from collections import deque
        ms = m[::2, ::2]
        seen = np.zeros(ms.shape, bool)
        regs = []
        for y0, x0 in np.argwhere(ms):
            if seen[y0, x0]:
                continue
            q = deque([(y0, x0)]); seen[y0, x0] = True; cells = []
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < ms.shape[0] and 0 <= xx < ms.shape[1] \
                       and ms[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; q.append((yy, xx))
            regs.append(cells)
        regs.sort(key=len, reverse=True)
        if region >= len(regs):
            raise SystemExit("only %d components" % len(regs))
        m2 = np.zeros(m.shape, bool)
        for y, x in regs[region]:
            m2[y * 2, x * 2] = True
        m = m2

    ys, xs = np.nonzero(m)
    rng = np.random.default_rng(seed)
    take = rng.choice(len(ys), size=min(n, len(ys)), replace=False)
    ty = math.tan(math.radians(c["fov"]) / 2.0)
    samples = []
    for i in take:
        py, px = int(ys[i]), int(xs[i])
        samples.append({"px": px, "py": py,
                        "X": float((2.0 * ((px + 0.5) / W) - 1.0) * ty * (W / H)),
                        "Y": float((1.0 - 2.0 * ((py + 0.5) / H)) * ty),
                        "L": round(float(L[py, px]), 2),
                        "d": round(float(d[py, px]), 3),
                        "world": [round(float(v), 3) for v in P[py, px]]})
    js = {"shot": shot, "mask": mask, "region": region,
          "pos": c["pos"], "aim": c["aim"], "fov": c["fov"],
          "W": W, "H": H, "maskPx": int(m.sum()), "maskFrac": float(m.mean()),
          "samples": samples}
    json.dump(js, open(out, "w"))
    print("SAMPLED %s mask=%s region=%s: %d px (%.2f%% of frame) -> %d samples -> %s"
          % (shot, mask, region, int(m.sum()), 100 * m.mean(), len(samples), out))


# ------------------------------------------------- stage 2 helpers (Blender) ---
def _volume_only(mat):
    """(is_render_only_volume, density_or_None, colour) — a material that shades a
    volume and NOT a surface.  Density None => node-driven, unreadable statically."""
    if mat is None or not mat.use_nodes:
        return False, None, None
    for n in mat.node_tree.nodes:
        if n.type != 'OUTPUT_MATERIAL':
            continue
        surf, vol = n.inputs.get('Surface'), n.inputs.get('Volume')
        if vol is not None and vol.is_linked and not (surf is not None and surf.is_linked):
            src = vol.links[0].from_node
            di = src.inputs.get('Density')
            dens = None if (di is None or di.is_linked) else float(di.default_value)
            ci = src.inputs.get('Color')
            col = None if ci is None else [round(float(v), 4) for v in ci.default_value[:3]]
            return True, dens, col
    return False, None, None


def _classify():
    """-> (volset {name: (density, colour)}, skipset {names not in the render})"""
    import bpy
    vol, skip = {}, set()
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if ob.hide_render or ob.name not in bpy.context.scene.objects:
            skip.add(ob.name); continue
        mats = [s.material for s in ob.material_slots]
        if mats and all(_volume_only(m)[0] for m in mats if m is not None) \
                and any(m is not None for m in mats):
            _, dens, col = _volume_only(mats[0])
            vol[ob.name] = (dens, col)
    return vol, skip


def _march(sc, dg, origin, direction, vol, skip, maxdist=2000.0, maxsteps=64):
    """Cast, marching THROUGH render-only volume cards.  -> (hit_obj, hit_mat, dist,
    {card: tau}, [passed cards])."""
    from mathutils import Vector
    o = Vector(origin); dv = Vector(direction).normalized()
    taus = {}; inside = {}; travelled = 0.0
    for _ in range(maxsteps):
        ok, loc, nrm, idx, ob, mw = sc.ray_cast(dg, o, dv, distance=maxdist - travelled)
        if not ok:
            break
        step = (loc - o).length
        travelled += step
        name = ob.name.split('.')[0] if ob.name not in vol and ob.name not in skip else ob.name
        nm = ob.name
        if nm in skip:
            o = loc + dv * 1e-3
            continue
        if nm in vol:
            if nm in inside:                       # exit face -> close the segment
                path = travelled - inside.pop(nm)
                dens = vol[nm][0]
                if dens is not None:
                    taus[nm] = taus.get(nm, 0.0) + dens * path
                else:
                    taus[nm] = None
            else:
                inside[nm] = travelled
            o = loc + dv * 1e-3
            continue
        mat = None
        try:
            me = ob.evaluated_get(dg).data
            if me.polygons and idx < len(me.polygons):
                si = me.polygons[idx].material_index
                if si < len(ob.material_slots) and ob.material_slots[si].material:
                    mat = ob.material_slots[si].material.name
        except Exception:
            pass
        return nm, mat, travelled, taus, list(taus.keys())
    return None, None, None, taus, list(taus.keys())


# ------------------------------------------------------------------ stage 2 ---
def stage_rays():
    import bpy
    from mathutils import Vector
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    vol, skip = _classify()
    print("RENDER-ONLY VOLUME CARDS (marched through, never counted as a hit):")
    for k, (d, c) in sorted(vol.items()):
        print("   %-28s density=%s colour=%s" % (k, "driven" if d is None else "%.6f" % d, c))
    print("NOT IN THE RENDER (hide_render / out of scene), %d objects%s"
          % (len(skip), (": " + ", ".join(sorted(skip)[:12])) if skip else ""))
    for path in arg("--in", "/tmp/dh_pixel_census.json").split(","):
        _rays_one(json.load(open(path)), sc, dg, vol, skip)


def _rays_one(js, sc, dg, vol, skip):
    from mathutils import Vector
    p = Vector(js["pos"]); a = Vector(js["aim"])
    f = (a - p).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)

    from collections import Counter
    hits = Counter(); mats = Counter(); dists = {}
    taustat = {}; miss = 0; err = 0.0; nerr = 0
    for s in js["samples"]:
        dv = (f + s["X"] * r + s["Y"] * u).normalized()
        nm, mat, dist, taus, _ = _march(sc, dg, p, dv, vol, skip)
        for k, t in taus.items():
            taustat.setdefault(k, []).append(t)
        if nm is None:
            miss += 1; continue
        hits[nm] += 1
        mats["%s | %s" % (nm, mat)] += 1
        dists.setdefault(nm, []).append(dist)
        # stage-1/stage-2 agreement: reconstructed world point vs cast hit point
        hp = p + dv * dist
        err += (hp - Vector(s["world"])).length; nerr += 1

    n = len(js["samples"])
    print("\n== %s  mask=%s region=%s  %d samples of %d mask px (%.2f%% of frame)"
          % (js["shot"], js["mask"], js["region"], n, js["maskPx"], 100 * js["maskFrac"]))
    print("FIRST OPAQUE HIT (volume cards marched through):")
    for nm, c in hits.most_common(14):
        dd = dists[nm]
        print("   %-30s %4d (%5.1f%%)  dist %6.1f..%6.1f m"
              % (nm, c, 100.0 * c / n, min(dd), max(dd)))
    print("   %-30s %4d (%5.1f%%)" % ("<no hit / world background>", miss, 100.0 * miss / n))
    print("BY MATERIAL:")
    for k, c in mats.most_common(10):
        print("   %-50s %4d (%5.1f%%)" % (k, c, 100.0 * c / n))
    print("VOLUME CARDS CROSSED BY THESE RAYS (tau = density x path):")
    for k, v in sorted(taustat.items()):
        vv = [x for x in v if x is not None]
        if not vv:
            print("   %-28s %4d rays  tau=driven" % (k, len(v))); continue
        vv.sort()
        print("   %-28s %4d rays (%5.1f%%)  tau min %.4f med %.4f max %.4f"
              "   -> transmit %.3f..%.3f, wash %.1f%%..%.1f%%"
              % (k, len(v), 100.0 * len(v) / n, vv[0], vv[len(vv) // 2], vv[-1],
                 math.exp(-vv[-1]), math.exp(-vv[0]),
                 100 * (1 - math.exp(-vv[0])), 100 * (1 - math.exp(-vv[-1]))))
    if nerr:
        print("AGREEMENT stage1(depth.png reconstruction) vs stage2(cast): mean |dP| = %.3f m"
              % (err / nerr))


# -------------------------------------------------------------------- cover ---
def stage_cover():
    import bpy
    from mathutils import Vector
    bundle = os.path.join(ROOT, "public/assets/scenes/del-cine/cine.json")
    cams = {c["id"]: c for c in json.load(open(bundle))["cameras"]}
    shots = arg("--shots") or ",".join(cams)
    grid = int(arg("--grid", "192"))
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    vol, skip = _classify()
    only = arg("--cards")
    want = set(only.split(",")) if only else set(vol)

    print("%-14s %-22s %7s %9s %9s %9s" % ("shot", "card", "frame%", "tau med", "tau max", "wash% max"))
    for sid in shots.split(","):
        c = cams[sid]
        p = Vector(c["pos"]); f = (Vector(c["aim"]) - p).normalized()
        r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
        ty = math.tan(math.radians(c["fov"]) / 2.0)
        W = grid; H = int(grid * 9 / 16)
        stat = {}
        total = 0
        for iy in range(H):
            Y = (1.0 - 2.0 * ((iy + 0.5) / H)) * ty
            for ix in range(W):
                X = (2.0 * ((ix + 0.5) / W) - 1.0) * ty * (W / H)
                dv = (f + X * r + Y * u).normalized()
                _, _, _, taus, _ = _march(sc, dg, p, dv, vol, skip)
                total += 1
                for k, t in taus.items():
                    if k in want and t:
                        stat.setdefault(k, []).append(t)
        for k in sorted(want):
            v = sorted(stat.get(k, []))
            if not v:
                print("%-14s %-22s %7.2f %9s %9s %9s" % (sid, k, 0.0, "-", "-", "-"))
                continue
            print("%-14s %-22s %7.2f %9.4f %9.4f %9.2f"
                  % (sid, k, 100.0 * len(v) / total, v[len(v) // 2], v[-1],
                     100 * (1 - math.exp(-v[-1]))))


# -------------------------------------------------------------- frustum map ---
def stage_frustum():
    """Per camera, a coarse first-opaque-hit tally PLUS the card-vs-subject overlap.

    This is the census that decides a rebake list and, for a volume card, decides
    whether raising its density is safe: `behind` counts the rays that cross the card
    AND land on the named far-field subjects (where more wash is the intended effect),
    `spill` counts the rays that cross the card and land on ANYTHING ELSE (where more
    wash would print the card's own silhouette over a near object — the "salmon card"
    failure this repo has already paid for once)."""
    import bpy
    from mathutils import Vector
    cams = {c["id"]: c for c in json.load(open(os.path.join(
        ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]}
    shots = (arg("--shots") or ",".join(cams)).split(",")
    grid = int(arg("--grid", "160"))
    card = arg("--card", "fx_haze_east")
    subj = set((arg("--subject") or "cliff_east_closure,water_pool-downstream,"
                "cliff_far,cliff_far_toe,lf_farbank_tail").split(","))
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    vol, skip = _classify()
    print("card=%s  subjects=%s  grid=%dx%d" % (card, ",".join(sorted(subj)), grid, int(grid * 9 / 16)))
    print("%-14s %8s %8s | %8s %8s %8s | %s"
          % ("shot", "subj%", "card%", "behind%", "spill%", "tau med", "spill objects (top 3)"))
    from collections import Counter
    for sid in shots:
        c = cams[sid]
        p = Vector(c["pos"]); f = (Vector(c["aim"]) - p).normalized()
        r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
        ty = math.tan(math.radians(c["fov"]) / 2.0)
        W = grid; H = int(grid * 9 / 16)
        n = W * H
        nsubj = ncard = nbeh = nspill = 0
        taus = []; spillc = Counter(); subjc = Counter()
        for iy in range(H):
            Y = (1.0 - 2.0 * ((iy + 0.5) / H)) * ty
            for ix in range(W):
                X = (2.0 * ((ix + 0.5) / W) - 1.0) * ty * (W / H)
                dv = (f + X * r + Y * u).normalized()
                nm, _, _, tt, _ = _march(sc, dg, p, dv, vol, skip)
                base = (nm or "<bg>").split('.')[0]
                if base in subj or (nm or "") in subj:
                    nsubj += 1; subjc[base] += 1
                if card in tt:
                    ncard += 1
                    if tt[card]:
                        taus.append(tt[card])
                    if base in subj or (nm or "") in subj:
                        nbeh += 1
                    else:
                        nspill += 1; spillc[base] += 1
        taus.sort()
        print("%-14s %8.2f %8.2f | %8.2f %8.2f %8.4f | %s"
              % (sid, 100.0 * nsubj / n, 100.0 * ncard / n, 100.0 * nbeh / n,
                 100.0 * nspill / n, taus[len(taus) // 2] if taus else 0.0,
                 ", ".join("%s %d" % (k, v) for k, v in spillc.most_common(3))))
        if subjc:
            print("%-14s   subjects: %s" % ("", ", ".join(
                "%s %.2f%%" % (k, 100.0 * v / n) for k, v in subjc.most_common(6))))


if MODE == "frustum":
    stage_frustum()
elif MODE == "sample":
    stage_sample()
elif MODE == "rays":
    stage_rays()
elif MODE == "cover":
    stage_cover()
else:
    raise SystemExit(__doc__)
