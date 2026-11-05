"""Blender scene for the 'heavier' POV pilot (30 s). Run:
   blender -b -P scene.py -- --out DIR [--res 1920x1080] [--engine cycles|eevee] [--device gpu|cpu]
                              [--samples 64] [--frames 1-900] [--times 2,11,19]
Everything is built from code (no external assets). Coordinates are Z-up; helper B() converts
from the y-up layout used while designing (x, y_up, z) -> (x, -z, y_up)."""
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Quaternion, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline as TL

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
OUT = arg("--out", os.path.join(HERE, "..", "..", "out", "heavier-test", "raw"))
RES = arg("--res", "1920x1080")
ENGINE = arg("--engine", "cycles")
DEVICE = arg("--device", "gpu")
SAMPLES = int(arg("--samples", "64"))
FRAMES = arg("--frames", None)
TIMES = arg("--times", None)
FPS = TL.FPS
NF = int(TL.DURATION * FPS)
E = TL.EVENTS
FLOOR_Y = 3.0

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
rnd = random.Random(7)

def B(x, y, z): return Vector((x, -z, y))
def lerp(a, b, t): return a + (b - a) * t
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(x): x = cl(x); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ materials
_mats = {}
def mat(hexcol, rough=0.75, emit=0.0, metal=0.0):
    key = (hexcol, rough, emit, metal)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(f"m_{hexcol:06x}_{len(_mats)}"); m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    r, g, b = ((hexcol >> 16) & 255) / 255, ((hexcol >> 8) & 255) / 255, (hexcol & 255) / 255
    srgb = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    col = (srgb(r), srgb(g), srgb(b), 1)
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0:
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = emit
    _mats[key] = m; return m

def link(obj, parent=None):
    scene.collection.objects.link(obj)
    if parent is not None: obj.parent = parent
    return obj

def box(name, w, h, d, color, pos, parent=None, bevel=0.0, rough=0.75, emit=0.0):
    """w,h,d and pos in the y-up design space."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((w, d, h)), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat(color, rough, emit))
    ob.location = B(*pos) if parent is None else Vector((pos[0], -pos[2], pos[1]))
    if bevel > 0:
        md = ob.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
    return link(ob, parent)

def empty(name, pos=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = B(*pos) if parent is None else Vector(pos)
    return link(ob, parent)

def limb(name, a, b, r0, r1, color, parent=None, segs=12, rough=0.8):
    """tapered cylinder between points a,b given in the parent's local (blender) space."""
    a, b = Vector(a), Vector(b)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    L = (b - a).length
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=L)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat(color, rough))
    ob.location = (a + b) / 2
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    return link(ob, parent)

def ico(name, r, color, pos, sub=1):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat(color, 0.9)); ob.location = B(*pos)
    return link(ob)

# ------------------------------------------------------------------ world + lights
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.42, 0.62, 0.92, 1); bg.inputs[1].default_value = 1.0

def look_rot(obj, src, dst):
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = (dst - src).to_track_quat('-Z', 'Y')

sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 4.0; sun.angle = math.radians(2.5); sun.color = (1.0, 0.9, 0.78)
so = link(bpy.data.objects.new("sun", sun)); so.location = B(14, 12, 3); look_rot(so, B(14, 12, 3), B(0, 3, -1))
win = bpy.data.lights.new("winfill", 'AREA'); win.energy = 260; win.size = 3.2; win.size_y = 1.4; win.shape = 'RECTANGLE'; win.color = (0.85, 0.92, 1.0)
wo = link(bpy.data.objects.new("winfill", win)); wo.location = B(4.2, FLOOR_Y + 1.45, 0); look_rot(wo, B(4.2, 4.45, 0), B(0, 4.2, 0))
roomfill = bpy.data.lights.new("roomfill", 'AREA'); roomfill.energy = 120; roomfill.size = 6; roomfill.color = (1.0, 0.95, 0.88)
rf = link(bpy.data.objects.new("roomfill", roomfill)); rf.location = B(0, FLOOR_Y + 2.55, 0); look_rot(rf, B(0, 5.55, 0), B(0, 3.0, 0))
lamp = bpy.data.lights.new("lamp", 'POINT'); lamp.energy = 220; lamp.color = (1.0, 0.72, 0.45); lamp.shadow_soft_size = 0.2
lo = link(bpy.data.objects.new("lamp", lamp)); lo.location = B(2.4, 1.75, -2.6)
lowfill = bpy.data.lights.new("lowfill", 'AREA'); lowfill.energy = 90; lowfill.size = 5; lowfill.color = (1.0, 0.85, 0.7)
lf = link(bpy.data.objects.new("lowfill", lowfill)); lf.location = B(0, 2.6, 0); look_rot(lf, B(0, 2.6, 0), B(0, 0, 0))

# ------------------------------------------------------------------ house
# lower room
box("lfloor", 9, 0.2, 9, 0x8a6a4c, (0, -0.1, 0))
for nm, w, d, x, z in (("lw1", 9, 0.2, 0, -4.5), ("lw2", 9, 0.2, 0, 4.5), ("lw3", 0.2, 9, -4.5, 0), ("lw4", 0.2, 9, 4.5, 0)):
    box(nm, w, 2.75, d, 0xd8cbb4, (x, 1.375, z))
box("sofa", 2.6, 0.45, 0.9, 0x3e5c6e, (1.6, 0.42, -3.7), bevel=0.06); box("sofab", 2.6, 0.55, 0.25, 0x36505f, (1.6, 0.85, -4.1), bevel=0.06)
box("rug", 2.2, 0.02, 1.6, 0x9c4a3a, (0.2, 0.01, -1.6))
box("lpole", 0.06, 1.5, 0.06, 0x222222, (2.4, 0.75, -2.6)); box("lshade", 0.42, 0.32, 0.42, 0xfff0d0, (2.4, 1.62, -2.6), emit=3.0)
box("cab", 1.0, 0.6, 0.5, 0x5b4636, (-3.2, 0.3, 1.5), bevel=0.02)
box("tv", 1.4, 0.8, 0.06, 0x111418, (-4.35, 1.4, 1.5), rough=0.3)
# upper room walls with window on +x
WALL = 0xf1ebe0
box("uw1", 9, 2.6, 0.2, WALL, (0, FLOOR_Y + 1.3, -4.5)); box("uw2", 9, 2.6, 0.2, WALL, (0, FLOOR_Y + 1.3, 4.5))
box("uw3", 0.2, 2.6, 9, 0xe9e1d2, (-4.5, FLOOR_Y + 1.3, 0))
box("ww_low", 0.2, 0.7, 9, 0xe9e1d2, (4.5, FLOOR_Y + 0.35, 0)); box("ww_top", 0.2, 0.4, 9, 0xe9e1d2, (4.5, FLOOR_Y + 2.4, 0))
box("ww_l", 0.2, 1.5, 2.7, 0xe9e1d2, (4.5, FLOOR_Y + 1.45, -3.15)); box("ww_r", 0.2, 1.5, 2.7, 0xe9e1d2, (4.5, FLOOR_Y + 1.45, 3.15))
box("sill", 0.16, 0.06, 3.6, 0xffffff, (4.42, FLOOR_Y + 0.72, 0)); box("mull", 0.08, 1.5, 0.07, 0xffffff, (4.45, FLOOR_Y + 1.45, 0))
box("ceil", 9, 0.2, 9, 0xf6f2ec, (0, FLOOR_Y + 2.7, 0))
box("skirt1", 9, 0.1, 0.03, 0xffffff, (0, FLOOR_Y + 0.05, -4.39)); box("skirt2", 0.03, 0.1, 9, 0xffffff, (-4.39, FLOOR_Y + 0.05, 0))
# outside
gp = bpy.data.meshes.new("ground"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=120); bm.to_mesh(gp); bm.free()
go = link(bpy.data.objects.new("ground", gp)); go.data.materials.append(mat(0x6f9a4a, 0.95)); go.location = (0, 0, -0.05)
for i in range(34):
    x, z, h = 9 + rnd.random() * 45, -25 + rnd.random() * 50, 2 + rnd.random() * 3
    box(f"trunk{i}", 0.35, h, 0.35, 0x5a4030, (x, h / 2, z))
    ico(f"crown{i}", 1.3 + rnd.random() * 1.3, [0x4f8a3c, 0x5a9440, 0x447a34][i % 3], (x, h + 0.9, z), sub=1)
for i in range(6):
    ico(f"hill{i}", 14 + rnd.random() * 8, 0x7aa556, (70 + rnd.random() * 30, -8, -40 + i * 16), sub=2)
# breakable floor tiles (slab top at FLOOR_Y)
T = 0.5; tiles = []
static_bm = bmesh.new(); static_mats = {}
for ix in range(-9, 9):
    for iz in range(-9, 9):
        x, z = ix * T + T / 2, iz * T + T / 2
        col = 0xc29466 if (ix + iz) % 2 else 0xbb8d5f
        inside = (-2.6 < x < 0.3) and (-3.3 < z < -0.6)
        edge = inside and (x < -2.3 or x > 0.0 or z < -3.0 or z > -0.9)
        fall = (rnd.random() < .5) if edge else inside
        vx, vz, rx, rz, delay = (rnd.random() - .5) * 1.2, (rnd.random() - .5) * 1.2, (rnd.random() - .5) * 6, (rnd.random() - .5) * 6, rnd.random() * 0.25
        if fall:
            ob = box(f"tile_{ix}_{iz}", T * 0.995, 0.25, T * 0.995, col, (x, FLOOR_Y - 0.125, z), rough=0.55)
            tiles.append(dict(ob=ob, x=x, z=z, fall=True, vx=vx, vz=vz, rx=rx, rz=rz, delay=delay))
        else:
            mi = static_mats.setdefault(col, len(static_mats))
            res = bmesh.ops.create_cube(static_bm, size=1.0)
            bmesh.ops.scale(static_bm, vec=Vector((T * 0.995, T * 0.995, 0.25)), verts=res["verts"])
            bmesh.ops.translate(static_bm, vec=B(x, FLOOR_Y - 0.125, z), verts=res["verts"])
            for fc in {f for v in res["verts"] for f in v.link_faces}: fc.material_index = mi
sme = bpy.data.meshes.new("floor_static"); static_bm.to_mesh(sme); static_bm.free()
for col in static_mats: sme.materials.append(mat(col, 0.55))
link(bpy.data.objects.new("floor_static", sme))
# cracks
cracks = []
for i in range(30):
    a = rnd.random() * math.tau; r = 0.3 + rnd.random() * 1.6; L = 0.3 + rnd.random() * 0.8
    ob = box(f"crack{i}", L, 0.006, 0.014, 0x140d08, (-1.2 + math.cos(a) * r, FLOOR_Y + 0.004, -1.95 + math.sin(a) * r), rough=1)
    ob.rotation_euler = (0, 0, -(a + (rnd.random() - .5) * .8)); cracks.append((ob, i))
# bed: two halves split along z=-2.0 (design space)
bed = empty("bed", (0, 0, 0))
bedL = empty("bedL", (-1.6, FLOOR_Y, -2.0)); bedR = empty("bedR", (-1.6, FLOOR_Y, -2.0))
bedL.parent = bed; bedR.parent = bed
def lbox(nm, w, h, d, c, p, par, **k):
    return box(nm, w, h, d, c, p, parent=par, **k)
lbox("frL", 1.7, 0.32, 1.1, 0x6e4a30, (0, 0.26, -0.55), bedL, bevel=0.02); lbox("frR", 1.7, 0.32, 1.1, 0x6e4a30, (0, 0.26, 0.55), bedR, bevel=0.02)
lbox("matL", 1.6, 0.26, 1.05, 0xf3f1ec, (0, 0.55, -0.53), bedL, bevel=0.05); lbox("matR", 1.6, 0.26, 1.05, 0xf3f1ec, (0, 0.55, 0.53), bedR, bevel=0.05)
lbox("head", 1.75, 1.0, 0.1, 0x6e4a30, (0, 0.62, -1.12), bedL, bevel=0.02)
lbox("pillow", 0.75, 0.15, 0.42, 0xffffff, (0, 0.76, -0.82), bedL, bevel=0.06)
lbox("blanket", 1.64, 0.07, 0.95, 0x5f8fae, (0, 0.7, 0.55), bedR, bevel=0.03)
for par, z in ((bedL, -1.0), (bedL, -0.1), (bedR, 0.1), (bedR, 1.0)):
    for x in (-0.75, 0.75): lbox("leg", 0.1, 0.12, 0.1, 0x4a3020, (x, 0.06, z), par)
box("nightstand", 0.5, 0.55, 0.45, 0x6e4a30, (-1.6 + 1.25, FLOOR_Y + 0.275, -3.55), bevel=0.02)
box("ns_lamp", 0.18, 0.25, 0.18, 0xfff3d6, (-0.35, FLOOR_Y + 0.68, -3.55), emit=1.5)
box("rug2", 2.4, 0.012, 1.6, 0x8a9fb0, (1.5, FLOOR_Y + 0.006, 0.4))
box("wardrobe", 1.4, 2.1, 0.6, 0x7d5a3c, (2.6, FLOOR_Y + 1.05, -4.1), bevel=0.02)
box("frame", 0.9, 0.6, 0.04, 0x2a3440, (-1.0, FLOOR_Y + 1.7, 4.38)); box("art", 0.8, 0.5, 0.02, 0xd98c5f, (-1.0, FLOOR_Y + 1.7, 4.36))
box("plant_pot", 0.3, 0.35, 0.3, 0xb85c38, (3.9, FLOOR_Y + 0.175, 1.9)); ico("plant", 0.35, 0x3f7d3a, (3.9, FLOOR_Y + 0.62, 1.9))
# bathroom scale with 7-segment display (3 digits)
scl = empty("scale", (1.2, FLOOR_Y, 0.9))
box("scale_body", 0.5, 0.05, 0.5, 0xeef1f4, (0, 0.025, 0), parent=scl, bevel=0.015, rough=0.35)
box("scale_win", 0.22, 0.004, 0.08, 0x0b1014, (0, 0.051, -0.19), parent=scl, rough=0.2)
SEG = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
segs = {}
for di in range(3):
    cx = -0.06 + di * 0.06
    for s, (sx, sz, w, d) in {"a": (0, -0.025, 0.026, 0.005), "g": (0, 0, 0.026, 0.005), "d": (0, 0.025, 0.026, 0.005),
                               "f": (-0.015, -0.0125, 0.005, 0.022), "b": (0.015, -0.0125, 0.005, 0.022),
                               "e": (-0.015, 0.0125, 0.005, 0.022), "c": (0.015, 0.0125, 0.005, 0.022)}.items():
        segs[(di, s)] = box(f"seg{di}{s}", w, 0.002, d, 0x7ff0d8, (cx + sx, 0.054, -0.19 + sz), parent=scl, emit=6)
# feet (sneakers) + jeans legs on the scale
stand = empty("stand", (0, 0, 0))
for s in (-1, 1):
    fx, fz = 1.2 + s * 0.09, 0.95
    shoe = empty(f"shoe{s}", (fx, FLOOR_Y + 0.05, fz)); shoe.parent = stand; shoe.location = B(fx, FLOOR_Y + 0.05, fz)
    box("sole", 0.11, 0.035, 0.29, 0xf4f4f2, (0, 0.017, -0.01), parent=shoe, bevel=0.012)
    box("upper", 0.1, 0.07, 0.24, 0x30475e, (0, 0.07, 0.02), parent=shoe, bevel=0.03)
    box("toe", 0.098, 0.05, 0.07, 0x30475e, (0, 0.055, -0.12), parent=shoe, bevel=0.024)
    box("toecap", 0.1, 0.03, 0.05, 0xf4f4f2, (0, 0.035, -0.135), parent=shoe, bevel=0.012)
    for k in range(3): box("lace", 0.06, 0.006, 0.012, 0xffffff, (0, 0.107, -0.02 + k * 0.035), parent=shoe)
    limb(f"jean{s}", B(fx, FLOOR_Y + 0.1, fz + 0.07), B(fx + s * 0.02, FLOOR_Y + 0.98, fz + 0.16), 0.052, 0.07, 0x3d5a80, stand)
# ------------------------------------------------------------------ camera + hands
camd = bpy.data.cameras.new("cam"); camd.sensor_fit = 'VERTICAL'; camd.angle_y = math.radians(58); camd.clip_start = 0.02; camd.clip_end = 300
cam = link(bpy.data.objects.new("cam", camd)); scene.camera = cam; cam.rotation_mode = 'QUATERNION'
SKIN, SLEEVE = 0xe0a985, 0x3d6f73
def make_hand(side):
    h = bpy.data.objects.new(f"hand{side}", None); link(h, cam)
    limb("forearm", (0, 0, 0.62), (0, 0, 0.1), 0.07, 0.06, SLEEVE, h)
    limb("wrist", (0, 0, 0.13), (0, 0, -0.02), 0.048, 0.045, SKIN, h)
    palm = bpy.data.meshes.new("palm"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=(0.12, 0.04, 0.13), verts=bm.verts); bm.to_mesh(palm); bm.free()
    po = link(bpy.data.objects.new("palm", palm), h); po.location = (0, 0, -0.08); po.data.materials.append(mat(SKIN, 0.6))
    md = po.modifiers.new("b", "BEVEL"); md.width = 0.016; md.segments = 3
    for i in range(4):
        x = -0.042 + i * 0.028; ln = 0.085 - abs(i - 1.5) * 0.012
        limb("f1", (x, 0, -0.14), (x, -0.012, -0.14 - ln * .55), 0.0165, 0.0155, SKIN, h, segs=8)
        limb("f2", (x, -0.012, -0.14 - ln * .55), (x, -0.03, -0.14 - ln), 0.0155, 0.014, SKIN, h, segs=8)
    limb("thumb", (side * -0.055, 0, -0.05), (side * -0.085, -0.012, -0.12), 0.017, 0.015, SKIN, h, segs=8)
    return h
hL, hR = make_hand(-1), make_hand(1)

# bake bevel modifiers into plain meshes (faster per-frame scene sync)
_dg = bpy.context.evaluated_depsgraph_get()
for ob in list(scene.objects):
    if ob.type == 'MESH' and ob.modifiers:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(_dg))
        ob.modifiers.clear(); ob.data = me

# ------------------------------------------------------------------ animation (baked per frame)
POS = [(0, (1.2, 4.52, 0.86)), (9.4, (1.2, 4.52, 0.86)), (10.6, (0.6, 4.6, 0.4)), (11.8, (-0.3, 4.58, -1.4)), (13.0, (-1.05, 4.3, -2.0))]
LOOK = [(0, (1.2, 3.0, 0.42)), (9.2, (1.2, 3.0, 0.42)), (10.2, (-0.8, 4.0, -2.4)), (11.8, (-1.6, 3.6, -2.2)),
        (13.0, (2.5, 3.6, -1.6)), (E["look_bed"], (2.5, 3.6, -1.6)), (E["look_bed"] + 1.0, (-0.45, 3.3, -2.05)),
        (E["bed_break"] + 1.6, (-0.45, 3.3, -2.05)), (21.6, (1.2, 3.0, -1.7))]
def track(keys, t):
    if t <= keys[0][0]: return Vector(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1: return Vector(a).lerp(Vector(b), sm((t - t0) / (t1 - t0)))
    return Vector(keys[-1][1])
def shake(t, amp, f=23):
    return Vector((math.sin(t * f) * amp, math.sin(t * f * 1.3 + 1) * amp, math.sin(t * f * .7 + 2) * amp))

def cam_state(t):
    p, l = track(POS, t), track(LOOK, t)
    for td in (3.0, 6.3):
        k = t - td
        if 0 < k < .6: p.y -= 0.05 * math.sin(k / .6 * math.pi)
    if 9.6 < t < 12.6: p.y += 0.035 * math.sin((t - 9.6) * 9); p.x += 0.015 * math.sin((t - 9.6) * 4.5)
    if t > 13: p.y -= 0.06 * sm((t - 13) / 5)
    bb = cl((t - E["bed_break"]) / 0.22)
    if t > E["bed_break"]:
        p.y -= 0.36 * bb * bb; k = t - E["bed_break"]
        if k < 1.2: p += shake(t, 0.03 * (1 - k / 1.2), 31)
    if 17.0 < t < E["bed_break"]: p += shake(t, 0.004 * (t - 17), 40)
    if 20.8 < t < E["floor_break"]: p += shake(t, 0.004 + 0.012 * sm((t - 20.8) / 3.2), 37)
    roll = 0.0
    if t > E["floor_break"]:
        ff = cl((t - E["floor_break"]) / (E["land"] - E["floor_break"]))
        sp = cam_state(E["floor_break"] - 1e-4)[0]; sp.y -= 0.05
        ep = Vector((0.15, 0.72, -1.05)); p = sp.lerp(ep, ff * ff)
        le = Vector((-0.9, 3.4, -2.0)); l0 = track(LOOK, E["floor_break"])
        l = l0.lerp(le, sm((t - E["floor_break"] - .15) / 1.6))
        roll = 0.25 * math.sin(ff * math.pi)
        k = t - E["land"]
        if 0 < k < 1.6: p += shake(t, 0.06 * math.exp(-k * 3), 27)
        if t > E["land"] + 1.4: l = le.lerp(Vector((-0.6, 3.7, -2.5)), sm((t - E["land"] - 1.4) / 4))
    return p, l, roll

def set_key(ob, path, f):
    ob.keyframe_insert(path, frame=f)
_vis = {}
def vis_key(ob, hidden, f):
    if _vis.get(ob.name) != hidden:
        ob.hide_render = hidden; ob.hide_viewport = hidden
        ob.keyframe_insert("hide_render", frame=f); _vis[ob.name] = hidden

def digits_for(n):
    s = str(int(n)).rjust(3)[-3:]
    return [None if ch == " " else int(ch) for ch in s]

falling = [k for k in tiles if k["fall"]]
for f in range(1, NF + 1):
    t = (f - 1) / FPS
    p, l, roll = cam_state(t)
    pb, lb = B(*p), B(*l)
    q = (lb - pb).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
    cam.location = pb; cam.rotation_quaternion = q
    set_key(cam, "location", f); set_key(cam, "rotation_quaternion", f)
    # hands (camera-local)
    show = 12.4 < t < E["land"] + 0.6
    for hh in (hL, hR):
        vis_key(hh, not show, f)
        for ch in hh.children_recursive: vis_key(ch, not show, f)
    hy, hz, hx, hrx = -0.24, -0.5, 0.3, -0.25
    if t > E["look_bed"]:
        k = sm((t - E["look_bed"]) / 1.0); hy, hz, hx = lerp(-0.24, -0.2, k), lerp(-0.5, -0.46, k), lerp(0.3, 0.34, k)
    if t > E["floor_break"]:
        k = sm((t - E["floor_break"]) / .4); hy = lerp(hy, -0.15, k); hx = lerp(hx, 0.42, k); hrx = lerp(-0.15, 0.6, k)
    fl = 0.04 * math.sin((t - E["bed_break"]) * 20) if E["bed_break"] < t < E["bed_break"] + .5 else 0
    for h, s in ((hL, -1), (hR, 1)):
        h.location = (s * hx, hy + s * fl, hz); h.rotation_euler = (hrx, s * -0.25, s * -0.1)
        set_key(h, "location", f); set_key(h, "rotation_euler", f)
    vis_key(stand, False, f) if t < 9.8 else vis_key(stand, True, f)
    for ch in stand.children_recursive: vis_key(ch, t >= 9.8, f)
    # scale digits
    m = TL.mass_at(t) if t < 9.6 else None
    dg = digits_for(round(m)) if m is not None else [None, None, None]
    for di in range(3):
        on = SEG[dg[di]] if dg[di] is not None else ("g" if m is None else "")
        for s in "abcdefg": vis_key(segs[(di, s)], s not in on, f)
    # bed break
    bb = cl((t - E["bed_break"]) / 0.22) if t > E["bed_break"] else 0
    bedL.rotation_euler = (-0.22 * bb, 0, 0); bedR.rotation_euler = (0.26 * bb, 0, 0)
    bedL.location = B(-1.6, FLOOR_Y - 0.1 * bb, -2.0 + 0.06 * bb); bedR.location = B(-1.6, FLOOR_Y - 0.12 * bb, -2.0 - 0.06 * bb)
    for ob in (bedL, bedR): set_key(ob, "location", f); set_key(ob, "rotation_euler", f)
    tf = t - E["floor_break"]
    if tf > 0:
        bed.location = B(-0.6 * min(1, tf), max(-2.7, -5.39 * tf * tf * 1.1), 0); bed.rotation_euler = (0, max(-0.3, -0.2 * tf), 0)
    else:
        bed.location = (0, 0, 0); bed.rotation_euler = (0, 0, 0)
    set_key(bed, "location", f); set_key(bed, "rotation_euler", f)
    # cracks
    for ob, i in cracks:
        sx = cl((t - E["cracks"] - i * 0.07) / 1.5, 0.001, 1); ob.scale = (sx, 1, 1); set_key(ob, "scale", f)
        vis_key(ob, not (E["cracks"] < t < E["floor_break"] + 0.05), f)
    # falling tiles
    for k in falling:
        d = max(0.0, tf - k["delay"])
        if tf <= 0:
            k["ob"].location = B(k["x"], FLOOR_Y - 0.125, k["z"]); k["ob"].rotation_euler = (0, 0, 0)
        else:
            y = max(0.13, FLOOR_Y - 0.125 - 4.9 * d * d * 1.1); md = min(d, .9)
            k["ob"].location = B(k["x"] + k["vx"] * md, y, k["z"] + k["vz"] * md)
            k["ob"].rotation_euler = (k["rx"] * md * .3, -k["rz"] * md * .3, 0)
        set_key(k["ob"], "location", f); set_key(k["ob"], "rotation_euler", f)
    lamp.energy = 220 if t > E["floor_break"] - 0.2 else 0; lamp.keyframe_insert("energy", frame=f)

# ------------------------------------------------------------------ render settings
w, h = map(int, RES.split("x"))
r = scene.render; r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, NF
r.use_motion_blur = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items] else 'None'
scene.view_settings.exposure = 0.35
if ENGINE == "eevee":
    r.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = SAMPLES
    try: scene.eevee.use_shadows = True
    except Exception: pass
    try: scene.eevee.use_raytracing = True
    except Exception: pass
else:
    r.engine = 'CYCLES'; c = scene.cycles
    c.samples = SAMPLES; c.use_denoising = True; c.max_bounces = 4; c.diffuse_bounces = 3; c.glossy_bounces = 2; c.transparent_max_bounces = 4
    c.use_adaptive_sampling = True; c.adaptive_threshold = 0.03
    r.use_persistent_data = True
    if DEVICE == "gpu":
        prefs = bpy.context.preferences.addons["cycles"].preferences; ok = False
        for dt in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = dt; prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == dt]
                if devs:
                    for d in prefs.devices: d.use = d.type == dt
                    c.device = 'GPU'; ok = True; print(f"[scene] GPU: {dt} x{len(devs)}", flush=True)
                    c.denoiser = 'OPTIX' if dt == "OPTIX" else 'OPENIMAGEDENOISE'; break
            except Exception as ex:
                print("[scene] device", dt, "unavailable:", ex)
        if not ok: print("[scene] WARNING: no GPU found, rendering on CPU", flush=True)
os.makedirs(OUT, exist_ok=True)

if TIMES:
    for tt in TIMES.split(","):
        f = int(round(float(tt) * FPS)) + 1
        scene.frame_set(f); r.filepath = os.path.join(OUT, f"t_{float(tt):06.2f}.png")
        bpy.ops.render.render(write_still=True)
else:
    if FRAMES:
        a, b = map(int, FRAMES.split("-")); scene.frame_start, scene.frame_end = a, b
    r.filepath = os.path.join(OUT, "")
    r.use_overwrite = False; r.use_placeholder = True   # resumable: skips frames already on disk
    bpy.ops.render.render(animation=True)
print("[scene] done", flush=True)
