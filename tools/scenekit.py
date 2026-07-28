"""
scenekit.py — reusable Blender toolkit for authoring FF-hybrid scene bundles.

The migration's scene-authoring template. A scene script is short and declarative:

    import sys; sys.path.insert(0, '/Users/junshernchan/projects/multiplayer-rpg/tools')
    import importlib, scenekit; importlib.reload(scenekit); from scenekit import SceneKit
    K = SceneKit('square3d')                       # collection + materials + ortho cam + light
    K.walkpath_disc(r=13)                           # WALK-FIRST: author walkable area first
    K.heartlight(0, 0)
    K.cottage_ring(radius=11.5, n=8)
    K.stall(6, -9, 20)
    K.fill_town(r0=13, r1=28, count=86)             # WORLD-FILL: dense surroundings, non-playable
    K.trees(r0=15, r1=34, count=46)
    K.set_ortho(scale=42)
    K.export()                                      # background.png + scene.glb + mask.png (atomic)

Design rules baked in:
- WALK-FIRST: walkable ground is authored ('walk_*' objects) before scenery; mask derives from it.
- WORLD-FILL: fill_town/trees are 'fill' (excluded from the collision GLB, kept in the render).
- Blockout materials are simple procedural colors; the nano-banana stylization adds the detail,
  so the kit has no external-texture dependency (scales cleanly to any fresh .blend).
- export() is ONE atomic step (render + glb + mask through the same ortho camera).

If a scene needs something the kit lacks, ADD IT TO THE KIT — never per-scene ad hoc.
"""
import bpy, math, random, io, contextlib, os

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
FILL_PREFIXES = ('fill_', 'tree_', 'trunk_', 'fol_', 'ground_base')   # excluded from collision GLB
WALK_PREFIX = 'walk_'                                                  # authored walkable surfaces

def _c(rgb, rough=0.85, emit=0.0):
    return (rgb, rough, emit)

# blockout palette (name -> (base_color, roughness, emission_strength))
PALETTE = {
    'wood':   ((0.20, 0.12, 0.06), 0.85, 0),
    'roof':   ((0.34, 0.13, 0.08), 0.8, 0),
    'stone':  ((0.36, 0.34, 0.30), 0.9, 0),
    'plaza':  ((0.34, 0.30, 0.26), 0.92, 0),
    'red':    ((0.42, 0.10, 0.08), 0.8, 0),
    'blue':   ((0.11, 0.22, 0.36), 0.8, 0),
    'green':  ((0.13, 0.28, 0.14), 0.8, 0),
    'ground': ((0.22, 0.20, 0.14), 0.95, 0),
    'trunk':  ((0.16, 0.11, 0.07), 0.9, 0),
    'fol_a':  ((0.55, 0.28, 0.08), 0.9, 0),
    'fol_b':  ((0.50, 0.40, 0.12), 0.9, 0),
    'fol_c':  ((0.30, 0.34, 0.16), 0.9, 0),
    'awning': ((0.70, 0.25, 0.18), 0.8, 0),
    'pumpkin':((0.75, 0.30, 0.06), 0.8, 0),
    'glow':   ((1.00, 0.62, 0.28), 0.5, 6.0),
    'flame':  ((1.00, 0.50, 0.15), 0.5, 18.0),
}


class SceneKit:
    def __init__(self, scene_key, clear=True):
        self.key = scene_key
        self.dir = f"{REPO}/public/assets/scenes/{scene_key}/"
        os.makedirs(self.dir, exist_ok=True)
        self.scene = bpy.context.scene
        # own collection
        col = bpy.data.collections.get(scene_key)
        if col and clear:
            for o in list(col.objects): bpy.data.objects.remove(o, do_unlink=True)
        if not col:
            col = bpy.data.collections.new(scene_key); self.scene.collection.children.link(col)
        elif col.name not in [c.name for c in self.scene.collection.children]:
            self.scene.collection.children.link(col)
        self.col = col
        self.paints = None
        self._materials()
        self._light()
        self.set_ortho()
        random.seed(hash(scene_key) & 0xffff)

    # ---------- materials ----------
    def _materials(self):
        M = bpy.data.materials
        self.M = {}
        for name, (rgb, rough, emit) in PALETTE.items():
            key = f"K_{name}"
            m = M.get(key) or M.new(key); m.use_nodes = True; nt = m.node_tree
            for n in list(nt.nodes): nt.nodes.remove(n)
            out = nt.nodes.new('ShaderNodeOutputMaterial')
            if emit > 0:
                e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*rgb, 1); e.inputs['Strength'].default_value = emit
                nt.links.new(e.outputs['Emission'], out.inputs['Surface'])
            else:
                b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
                nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
            self.M[name] = m
        self.paints = [self.M['red'], self.M['blue'], self.M['green']]
        self.fol = [self.M['fol_a'], self.M['fol_b'], self.M['fol_c']]

    def _light(self):
        s = self.scene
        w = s.world.node_tree.nodes.get('Background')
        w.inputs['Color'].default_value = (0.35, 0.26, 0.24, 1); w.inputs['Strength'].default_value = 0.7
        sun = bpy.data.objects.get('Sun')
        if not sun:
            d = bpy.data.lights.new('Sun', 'SUN'); sun = bpy.data.objects.new('Sun', d); s.collection.objects.link(sun)
        sun.data.energy = 2.0; sun.data.color = (1.0, 0.72, 0.48); sun.data.angle = math.radians(2)
        sun.rotation_euler = (math.radians(55), math.radians(8), math.radians(40))

    # ---------- primitives ----------
    def _link(self, ob):
        for c in ob.users_collection: c.objects.unlink(ob)
        self.col.objects.link(ob); return ob

    def box(self, n, loc, size, mat, rz=0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); ob = bpy.context.active_object; ob.name = n
        ob.scale = (size[0], size[1], size[2]); ob.rotation_euler = (0, 0, math.radians(rz)); ob.data.materials.append(self._m(mat))
        return self._link(ob)

    def cyl(self, n, loc, r, h, mat, v=16):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=v); ob = bpy.context.active_object; ob.name = n
        ob.data.materials.append(self._m(mat)); return self._link(ob)

    def sph(self, n, loc, r, mat, sz=1.0):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=2, location=loc); ob = bpy.context.active_object; ob.name = n
        ob.scale.z = sz; ob.data.materials.append(self._m(mat)); return self._link(ob)

    def gable(self, n, center, size, mat, rz=0):
        sx, sy, sz = size[0]/2, size[1]/2, size[2]; me = bpy.data.meshes.new(n); ob = bpy.data.objects.new(n, me)
        me.from_pydata([(-sx,-sy,0),(sx,-sy,0),(sx,sy,0),(-sx,sy,0),(0,-sy,sz),(0,sy,sz)], [],
                       [(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4)]); me.update(); me.uv_layers.new()
        ob.location = center; ob.rotation_euler = (0,0,math.radians(rz)); ob.data.materials.append(self._m(mat)); return self._link(ob)

    def point_light(self, loc, energy=45, color=(1.0, 0.6, 0.3)):
        d = bpy.data.lights.new('kl', 'POINT'); d.energy = energy; d.color = color
        o = bpy.data.objects.new('kl', d); o.location = loc; self.col.objects.link(o); return o

    def _m(self, mat):
        return mat if isinstance(mat, bpy.types.Material) else self.M[mat]

    # ---------- WALK-FIRST: authored walkable ground ----------
    def walkpath_disc(self, r=12, z=0.0, mat='plaza'):
        self.box(WALK_PREFIX + 'disc', (0, 0, z-0.1), (r*2, r*2, 0.2), mat)
        self._base_ground()
        return self

    def walkpath_rect(self, w, d, cx=0, cy=0, z=0.0, mat='plaza'):
        self.box(WALK_PREFIX + 'rect', (cx, cy, z-0.1), (w, d, 0.2), mat)
        self._base_ground()
        return self

    def _base_ground(self, size=90):
        # big non-playable ground so there is never void under the fill
        self.box('ground_base', (0, 0, -0.3), (size, size, 0.3), 'ground')

    # ---------- playable scenery builders ----------
    def cottage(self, x, y, rz, w=4.4, d=4.0, h=3.4, paint=None, lit=True, name='cot'):
        pt = paint or random.choice(self.paints)
        self.box(f'{name}_body', (x, y, h/2), (w, d, h), pt, rz=rz)
        for zz in (0.15, h-0.15): self.box(f'{name}_band', (x, y, zz), (w+0.1, d+0.1, 0.22), 'wood', rz=rz)
        self.gable(f'{name}_roof', (x, y, h), (w+1.0, d+1.1, 1.5), 'roof', rz=rz)
        th = math.radians(rz - 90)                      # front faces this way (local -y)
        fx, fy = math.cos(th), math.sin(th); px, py = -math.sin(th), math.cos(th)
        for s in (-1.1, 1.1):
            self.box(f'{name}_win', (x+fx*(d/2+0.02)+px*s, y+fy*(d/2+0.02)+py*s, h*0.55), (0.9, 0.9, 1.0),
                     'glow' if lit else 'wood', rz=rz)
        self.box(f'{name}_door', (x+fx*(d/2+0.03), y+fy*(d/2+0.03), 1.0), (1.1, 0.9, 2.0), 'wood', rz=rz)

    def cottage_ring(self, radius=11.5, n=8, jitter=0.0):
        for i in range(n):
            a = math.radians(360/n*i + 22)
            cx, cy = radius*math.cos(a), radius*math.sin(a)
            facing = math.degrees(a) + 90                # front faces centre
            self.cottage(cx, cy, facing, paint=self.paints[i % 3])

    def heartlight(self, x=0, y=0):
        self.cyl('ped_base', (x, y, 0.25), 2.2, 0.5, 'stone', v=20)
        self.cyl('ped_top', (x, y, 0.62), 1.6, 0.4, 'stone', v=20)
        self.cyl('bowl', (x, y, 0.9), 1.2, 0.35, 'wood', v=20)
        bpy.ops.mesh.primitive_cone_add(radius1=0.85, radius2=0.05, depth=1.7, location=(x, y, 1.75), vertices=16)
        fl = bpy.context.active_object; fl.name = 'flame'; fl.data.materials.append(self.M['flame']); self._link(fl)
        self.point_light((x, y, 1.6), energy=3600, color=(1.0, 0.6, 0.28))

    def stall(self, x, y, rz):
        self.box('stall_counter', (x, y, 0.6), (3.0, 1.2, 1.2), 'wood', rz=rz)
        for ox in (-1.3, 1.3):
            self.box('stall_post', (x+ox*math.cos(math.radians(rz)), y+ox*math.sin(math.radians(rz)), 1.4), (0.15, 0.15, 2.6), 'wood', rz=rz)
        self.box('stall_awning', (x, y-0.2, 2.7), (3.4, 1.8, 0.12), 'awning', rz=rz)
        for bx in (-1.0, 0.2, 1.1): self.cyl('barrel', (x+bx, y+1.0, 0.5), 0.35, 0.9, 'wood', v=10)
        self.sph('pumpkin', (x-0.6, y+1.4, 0.35), 0.4, 'pumpkin', sz=0.8)

    def lantern_ring(self, radius=6.5, n=10, z=4.2):
        for i in range(n):
            a = math.radians(360/n*i); lx, ly = radius*math.cos(a), radius*math.sin(a)
            self.cyl('lantern', (lx, ly, z), 0.28, 0.5, 'glow', v=10); self.point_light((lx, ly, z), 55)

    # ---------- WORLD-FILL (non-playable set dressing) ----------
    def fill_town(self, r0=13, r1=28, count=80, hmin=3.0, hmax=7.5):
        for i in range(count):
            a = random.uniform(0, 2*math.pi); rr = random.uniform(r0, r1)
            x, y = rr*math.cos(a), rr*math.sin(a)
            w = random.uniform(3.2, 5.0); d = random.uniform(3.2, 5.0); h = random.uniform(hmin, hmax)
            rz = random.uniform(0, 360)
            self.box('fill_body', (x, y, h/2), (w, d, h), random.choice(self.paints), rz=rz)
            self.gable('fill_roof', (x, y, h), (w+0.8, d+0.9, h*0.5), 'roof', rz=rz)

    def trees(self, r0=15, r1=34, count=44):
        for i in range(count):
            a = random.uniform(0, 2*math.pi); rr = random.uniform(r0, r1); s = random.uniform(0.8, 1.6)
            x, y = rr*math.cos(a), rr*math.sin(a)
            self.cyl('trunk_', (x, y, 1.2*s), 0.25*s, 2.4*s, 'trunk', v=8)
            self.sph('fol_', (x, y, 3.0*s), 1.6*s, random.choice(self.fol), sz=1.15)
            self.sph('fol_', (x, y+0.4*s, 2.4*s), 1.2*s, random.choice(self.fol))

    def landmark(self, x, y, kind='tower'):
        self.box('fill_landmark', (x, y, 6), (3.6, 3.6, 12), 'wood')
        self.gable('fill_landmark_roof', (x, y, 12), (4.2, 4.2, 3), 'roof')

    # ---------- builders: waystation / courtyard type (added for lanternstead) ----------
    def tower(self, x=0, y=0, r=2.6, h=9.0, lantern=True):
        # stacked round stone tower body + door + windows
        self.cyl('tower_body', (x, y, h/2), r, h, 'stone', v=24)
        self.cyl('tower_ring', (x, y, h), r+0.25, 0.5, 'stone', v=24)
        self.box('tower_door', (x, y-r-0.02, 1.4), (1.2, 0.3, 2.6), 'wood')
        for zz in (h*0.45, h*0.7):
            self.box('tower_win', (x, y-r-0.02, zz), (0.7, 0.3, 1.0), 'glow')
        if lantern:
            # great-lantern room: brass base ring, glass cage (open cylinder), flame + strong warm light
            self.cyl('lantern_base', (x, y, h+0.4), r+0.4, 0.6, 'wood', v=24)
            self.cyl('lantern_cage', (x, y, h+1.9), r+0.2, 2.6, 'wood', v=16)
            bpy.ops.mesh.primitive_cone_add(radius1=1.0, radius2=0.05, depth=2.0, location=(x, y, h+2.0), vertices=16)
            fl = bpy.context.active_object; fl.name = 'flame'; fl.data.materials.append(self.M['flame']); self._link(fl)
            self.point_light((x, y, h+2.2), energy=4200, color=(1.0, 0.62, 0.3))

    def courtyard(self, half=12, wall_h=2.2, wall_t=0.6, gate_side='-y', z=0.0):
        # walled square enclosure around the walkable area, with a gate opening on one side
        segs = {'+x': (half, 0, 90), '-x': (-half, 0, 90), '+y': (0, half, 0), '-y': (0, -half, 0)}
        for side, (cx, cy, rz) in segs.items():
            length = half*2
            if side == gate_side:
                # split into two with a central gate gap
                g = 3.0
                self.box('cy_wall', (cx - (0 if rz else (length/4+g/4)), cy - ((length/4+g/4) if rz else 0), wall_h/2+z), (wall_t if rz==90 else length/2-g/2, length/2-g/2 if rz==90 else wall_t, wall_h), 'stone', rz=0)
                self.box('cy_wall', (cx + (0 if rz else (length/4+g/4)), cy + ((length/4+g/4) if rz else 0), wall_h/2+z), (wall_t if rz==90 else length/2-g/2, length/2-g/2 if rz==90 else wall_t, wall_h), 'stone', rz=0)
            else:
                self.box('cy_wall', (cx, cy, wall_h/2+z), (wall_t if rz==90 else length, length if rz==90 else wall_t, wall_h), 'stone', rz=0)

    def well(self, x, y):
        self.cyl('well_ring', (x, y, 0.5), 0.9, 1.0, 'stone', v=16)
        self.cyl('well_hole', (x, y, 0.95), 0.65, 0.15, 'wood', v=16)
        for ox in (-0.85, 0.85): self.box('well_post', (x+ox, y, 1.6), (0.16, 0.16, 2.2), 'wood')
        self.box('well_beam', (x, y, 2.7), (2.0, 0.16, 0.16), 'wood')

    def flag_pole(self, x, y, h=3.2):
        self.cyl('pole', (x, y, h/2), 0.08, h, 'wood', v=6)
        self.box('flag', (x+0.6, y, h-0.5), (1.1, 0.05, 0.7), random.choice([self.M['red'], self.M['awning']]))

    def veg_rows(self, x, y, rows=4, cols=6):
        for r in range(rows):
            self.box('veg_bed', (x, y+r*0.9, 0.15), (cols*0.5, 0.7, 0.3), 'ground')

    def forest(self, r0=16, r1=40, count=90):
        """dense surrounding forest (heavier than trees()) for wilderness scenes"""
        self.trees(r0=r0, r1=r1, count=count)

    def walkpath_strip(self, length=44, width=8, cx=0, cy=0, rz=0, z=0.0, mat='stone'):
        """WALK-FIRST: a straight walkable path/road (the player's route through a scene)."""
        self.box(WALK_PREFIX + 'strip', (cx, cy, z-0.1), (width, length, 0.2), mat, rz=rz)
        self._base_ground()
        return self

    def lamp_post(self, x, y, lit=False, h=3.6):
        self.box('lamp_post', (x, y, h/2), (0.18, 0.18, h), 'wood')
        self.box('lamp_arm', (x, y+0.4, h-0.2), (0.12, 0.9, 0.12), 'wood')
        self.box('lamp_head', (x, y+0.8, h-0.3), (0.5, 0.5, 0.7), 'glow' if lit else 'wood')
        if lit: self.point_light((x, y+0.8, h-0.3), 50)

    def trees_along(self, length=44, width=8, count=60, cy=0):
        """forest packed along BOTH sides of a strip road (leaves the road clear)."""
        for i in range(count):
            side = 1 if i % 2 else -1
            x = side * random.uniform(width/2+1.5, width/2+22)
            y = random.uniform(-length/2-4, length/2+4) + cy
            s = random.uniform(0.8, 1.7)
            self.cyl('trunk_', (x, y, 1.2*s), 0.25*s, 2.4*s, 'trunk', v=8)
            self.sph('fol_', (x, y, 3.0*s), 1.6*s, random.choice(self.fol), sz=1.15)

    # ---------- builders: interior / room type (dollhouse cutaway) ----------
    def interior_room(self, w=14, d=12, wall_h=5.0, floor='wood'):
        self.box(WALK_PREFIX + 'floor', (0, 0, -0.1), (w, d, 0.2), floor)   # walkable floor
        # only the FAR walls (back +y, left -x) so the ortho cam looks into the room
        self.box('wall_back', (0, d/2, wall_h/2), (w, 0.35, wall_h), 'wood')
        self.box('wall_left', (-w/2, 0, wall_h/2), (0.35, d, wall_h), 'wood')
        self._room = (w, d)

    def hearth(self, x=0, y=None):
        if y is None: y = self._room[1]/2 - 0.4
        self.box('hearth', (x, y, 1.2), (2.6, 0.8, 2.4), 'stone')
        self.box('mantel', (x, y-0.2, 2.3), (3.0, 1.0, 0.3), 'wood')
        self.box('fire_glow', (x, y-0.35, 0.6), (1.4, 0.3, 0.9), 'flame')
        self.point_light((x, y-0.4, 0.9), energy=380, color=(1.0, 0.55, 0.2))

    def table(self, x=0, y=0):
        self.box('table_top', (x, y, 1.0), (2.4, 1.4, 0.2), 'wood')
        for ox in (-1.0, 1.0):
            for oy in (-0.55, 0.55): self.box('table_leg', (x+ox, y+oy, 0.5), (0.15, 0.15, 1.0), 'wood')
        self.box('chair', (x-1.6, y, 0.6), (0.7, 0.7, 1.2), 'wood')
        self.box('chair', (x+1.6, y, 0.6), (0.7, 0.7, 1.2), 'wood')
        self.box('stool', (x, y-1.3, 0.5), (0.6, 0.6, 1.0), 'awning')     # the pale new stool

    def bed(self, x, y):
        self.box('bed', (x, y, 0.5), (2.6, 1.6, 1.0), 'wood'); self.box('quilt', (x, y, 1.05), (2.4, 1.4, 0.2), 'blue')

    def shelf(self, x, y):
        for zz in (2.0, 2.9, 3.8): self.box('shelf', (x, y, zz), (0.4, 2.6, 0.15), 'wood')

    def hanging_lamp(self, x, y, z=4.2):
        self.cyl('hlamp', (x, y, z), 0.3, 0.5, 'glow', v=10); self.point_light((x, y, z), energy=130)

    # ---------- camera ----------
    def set_ortho(self, scale=42, pos=(22, -22, 24), target=(0, 0, 1.5)):
        from mathutils import Vector
        cam = bpy.data.objects.get('SceneCam')
        if not cam:
            cd = bpy.data.cameras.new('SceneCam'); cam = bpy.data.objects.new('SceneCam', cd); self.scene.collection.objects.link(cam)
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = scale
        cam.location = Vector(pos); cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        self.scene.camera = cam; self.cam = cam
        return self

    # ---------- atomic bundle export ----------
    def export(self, res=(1344, 768)):
        s = self.scene; s.render.resolution_x, s.render.resolution_y = res; s.render.resolution_percentage = 100
        # 1) background (transparent, AgX)
        s.render.film_transparent = True; s.render.image_settings.color_mode = 'RGBA'
        s.view_settings.view_transform = 'AgX'; s.view_settings.look = 'None'; s.view_settings.exposure = 0.2
        if hasattr(s.eevee, 'taa_render_samples'): s.eevee.taa_render_samples = 96
        s.render.filepath = self.dir + 'background.png'; bpy.ops.render.render(write_still=True)
        # 2) mask (walk_* = white, else black), same ortho cam
        M = bpy.data.materials
        def emit(n, v):
            m = M.get(n) or M.new(n); m.use_nodes = True; nt = m.node_tree
            for x in list(nt.nodes): nt.nodes.remove(x)
            e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
            e.inputs['Color'].default_value = (v, v, v, 1); nt.links.new(e.outputs['Emission'], o.inputs['Surface']); return m
        white, black = emit('__white__', 1), emit('__black__', 0)
        saved = {}
        for o in bpy.data.objects:
            if o.type == 'MESH' and not o.hide_render:
                saved[o.name] = list(o.data.materials); o.data.materials.clear()
                o.data.materials.append(white if o.name.startswith(WALK_PREFIX) else black)
        w = s.world.node_tree.nodes.get('Background'); sw = (tuple(w.inputs['Color'].default_value), w.inputs['Strength'].default_value)
        w.inputs['Color'].default_value = (0, 0, 0, 1); w.inputs['Strength'].default_value = 0
        s.render.film_transparent = False; s.render.image_settings.color_mode = 'BW'
        s.view_settings.view_transform = 'Standard'; s.view_settings.exposure = 0
        s.render.filepath = self.dir + 'mask.png'; bpy.ops.render.render(write_still=True)
        for o in bpy.data.objects:
            if o.name in saved:
                o.data.materials.clear()
                for m in saved[o.name]: o.data.materials.append(m)
        w.inputs['Color'].default_value = sw[0]; w.inputs['Strength'].default_value = sw[1]
        s.render.image_settings.color_mode = 'RGBA'; s.view_settings.view_transform = 'AgX'; s.view_settings.exposure = 0.2; s.render.film_transparent = True
        # 3) lean collision/occlusion GLB (playable core only; exclude fill), + ortho camera
        bpy.ops.object.select_all(action='DESELECT'); n = 0
        for o in self.col.objects:
            if o.type == 'MESH' and not any(o.name.startswith(p) for p in FILL_PREFIXES):
                o.select_set(True); n += 1
        if self.cam.name not in s.collection.objects:
            try: s.collection.objects.link(self.cam)
            except Exception: pass
        self.cam.select_set(True); s.camera = self.cam; bpy.context.view_layer.objects.active = self.cam
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.export_scene.gltf(filepath=self.dir + 'scene.glb', export_format='GLB', use_selection=True,
                                      export_cameras=True, export_apply=True, export_yup=True)
        return f"{self.key}: background.png + mask.png + scene.glb ({n} playable meshes) -> {self.dir}"
