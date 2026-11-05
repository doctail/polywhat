"""Shared Blender helpers for polywhat scenes (materials, primitives, first-person hands, camera keys, render setup).
Design space is y-up (x, y_up, z); B() converts to Blender's z-up (x, -z, y)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Quaternion

def B(x, y, z): return Vector((x, -z, y))
def lerp(a, b, t): return a + (b - a) * t
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(x): x = cl(x); return x * x * (3 - 2 * x)

def args(argv):
    a = argv[argv.index("--") + 1:] if "--" in argv else []
    def get(name, default=None): return a[a.index(name) + 1] if name in a else default
    return get

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene

def srgb(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def rgb(hexcol): return (srgb(((hexcol >> 16) & 255) / 255), srgb(((hexcol >> 8) & 255) / 255), srgb((hexcol & 255) / 255), 1)

_mats = {}
def mat(hexcol, rough=0.75, emit=0.0, metal=0.0, emit_col=None):
    key = (hexcol, rough, emit, metal, emit_col)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(f"m{len(_mats)}"); m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0:
        bsdf.inputs["Emission Color"].default_value = rgb(emit_col if emit_col is not None else hexcol)
        bsdf.inputs["Emission Strength"].default_value = emit
    _mats[key] = m; return m

def emission_mat(hexcol, strength):
    """pure emission (cheap, used for stars, glows, lava)."""
    m = bpy.data.materials.new(f"em{len(_mats)}"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = rgb(hexcol); em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0]); _mats[("em", len(_mats))] = m
    return m

def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None: obj.parent = parent
    return obj

def box(name, w, h, d, color, pos, parent=None, bevel=0.0, rough=0.75, emit=0.0, material=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=Vector((w, d, h)), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(material or mat(color, rough, emit))
    ob.location = B(*pos) if parent is None else Vector((pos[0], -pos[2], pos[1]))
    if bevel > 0:
        md = ob.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
    return link(ob, parent)

def empty(name, pos=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None); ob.location = B(*pos) if parent is None else Vector(pos)
    return link(ob, parent)

def limb(name, a, b, r0, r1, color, parent=None, segs=12, rough=0.8, material=None):
    a, b = Vector(a), Vector(b); L = (b - a).length
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=L); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(material or mat(color, rough))
    ob.location = (a + b) / 2; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    return link(ob, parent)

def ico(name, r, color, pos, sub=1, material=None, smooth=False, parent=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(material or mat(color, 0.9))
    ob.location = B(*pos) if parent is None else Vector(pos)
    return link(ob, parent)

def merge_static(name, objs):
    """join many static mesh objects into one (much faster per-frame sync)."""
    objs = [o for o in objs if o.type == 'MESH']
    if not objs: return None
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); mats = []
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); me.transform(o.matrix_world)
        off = len(mats); mats += list(me.materials)
        for p in me.polygons: p.material_index += off
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    out = bpy.data.meshes.new(name); bm.to_mesh(out); bm.free()
    for m in mats: out.materials.append(m)
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    return link(bpy.data.objects.new(name, out))

def bake_modifiers(scene):
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in list(scene.objects):
        if ob.type == 'MESH' and ob.modifiers:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); ob.modifiers.clear(); ob.data = me

# ------------------------------------------------------------------ world, lights
def world(color=(0.42, 0.62, 0.92), strength=1.0, stars=False):
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes["Background"]; bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength
    if stars:   # procedural star field: thresholded voronoi on view direction
        tc = nt.nodes.new("ShaderNodeTexCoord"); vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 420.0
        ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
        ramp.color_ramp.elements[1].position = 0.035; ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
        mix = nt.nodes.new("ShaderNodeMath"); mix.operation = 'MULTIPLY'; mix.inputs[1].default_value = 6.0
        add = nt.nodes.new("ShaderNodeMixRGB"); add.blend_type = 'ADD'; add.inputs[0].default_value = 1.0
        nt.links.new(tc.outputs["Window"] if False else tc.outputs["Generated"], vor.inputs["Vector"])
        nt.links.new(vor.outputs["Distance"], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], mix.inputs[0])
        add.inputs[1].default_value = (*color, 1)
        nt.links.new(mix.outputs[0], add.inputs[2])
        nt.links.new(add.outputs[0], bg.inputs[0])
    return w

def look_rot(obj, src, dst):
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = (dst - src).to_track_quat('-Z', 'Y')

def light(kind, name, energy, color, pos, target=None, size=None, size_y=None, soft=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if size is not None: d.size = size
    if size_y is not None: d.shape = 'RECTANGLE'; d.size_y = size_y
    if soft is not None: d.shadow_soft_size = soft
    o = link(bpy.data.objects.new(name, d)); o.location = B(*pos)
    if target is not None: look_rot(o, B(*pos), B(*target))
    return o

def sun(energy, pos, target, color=(1.0, 0.9, 0.78), angle=2.5):
    d = bpy.data.lights.new("sun", 'SUN'); d.energy = energy; d.angle = math.radians(angle); d.color = color
    o = link(bpy.data.objects.new("sun", d)); o.location = B(*pos); look_rot(o, B(*pos), B(*target)); return o

# ------------------------------------------------------------------ first-person camera + hands
SKIN, SLEEVE = 0xe0a985, 0x3d6f73
def camera(fov_y=58):
    cd = bpy.data.cameras.new("cam"); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov_y); cd.clip_start = 0.02; cd.clip_end = 5000
    cam = link(bpy.data.objects.new("cam", cd)); bpy.context.scene.camera = cam; cam.rotation_mode = 'QUATERNION'
    return cam

def hand(cam, side, glow=0.0):
    h = link(bpy.data.objects.new(f"hand{side}", None), cam)
    skin = mat(SKIN, 0.6, emit=glow, emit_col=0xff9a50) if glow else mat(SKIN, 0.6)
    limb("forearm", (0, 0, 0.62), (0, 0, 0.1), 0.07, 0.06, SLEEVE, h)
    limb("wrist", (0, 0, 0.13), (0, 0, -0.02), 0.048, 0.045, 0, h, material=skin)
    pm = bpy.data.meshes.new("palm"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=(0.12, 0.04, 0.13), verts=bm.verts); bm.to_mesh(pm); bm.free()
    po = link(bpy.data.objects.new("palm", pm), h); po.location = (0, 0, -0.08); po.data.materials.append(skin)
    md = po.modifiers.new("b", "BEVEL"); md.width = 0.016; md.segments = 3
    # relaxed, slightly spread and curled fingers
    for i in range(4):
        x = -0.045 + i * 0.03; ln = 0.085 - abs(i - 1.5) * 0.012; spread = (i - 1.5) * 0.012
        limb("f1", (x, 0, -0.14), (x + spread, -0.018, -0.14 - ln * .55), 0.017, 0.016, 0, h, segs=8, material=skin)
        limb("f2", (x + spread, -0.018, -0.14 - ln * .55), (x + spread * 1.6, -0.045, -0.14 - ln * 0.95), 0.016, 0.014, 0, h, segs=8, material=skin)
    limb("thumb", (side * -0.055, 0, -0.05), (side * -0.095, -0.02, -0.11), 0.019, 0.016, 0, h, segs=8, material=skin)
    return h

def key(ob, path, f): ob.keyframe_insert(path, frame=f)

_vis = {}
def vis(ob, hidden, f, recursive=True):
    obs = [ob] + (list(ob.children_recursive) if recursive else [])
    for o in obs:
        if _vis.get(o.name) != hidden:
            o.hide_render = hidden; o.hide_viewport = hidden; o.keyframe_insert("hide_render", frame=f); _vis[o.name] = hidden

def cam_key(cam, pos, look, f, roll=0.0):
    pb, lb = B(*pos), B(*look)
    cam.location = pb; cam.rotation_quaternion = (lb - pb).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
    key(cam, "location", f); key(cam, "rotation_quaternion", f)

def track(keys, t):
    if t <= keys[0][0]: return Vector(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1: return Vector(a).lerp(Vector(b), sm((t - t0) / (t1 - t0)))
    return Vector(keys[-1][1])

def shake(t, amp, f=23):
    return Vector((math.sin(t * f) * amp, math.sin(t * f * 1.3 + 1) * amp, math.sin(t * f * .7 + 2) * amp))

# ------------------------------------------------------------------ render setup
def setup_render(scene, out, res, engine, samples, device, fps, f0, f1, exposure=0.35):
    w, h = map(int, res.split("x")); r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps = fps; scene.frame_start, scene.frame_end = f0, f1
    r.use_motion_blur = True
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'
    vs = scene.view_settings; vs.view_transform = 'AgX'
    looks = [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items]
    vs.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in looks else 'None'
    vs.exposure = exposure
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    if engine == "eevee":
        r.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
        scene.eevee.taa_render_samples = samples
    else:
        r.engine = 'CYCLES'; c = scene.cycles
        c.samples = samples; c.use_denoising = True; c.max_bounces = 4; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.03
        r.use_persistent_data = True
        if device == "gpu":
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for dt in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
                try:
                    prefs.compute_device_type = dt; prefs.get_devices()
                    if [d for d in prefs.devices if d.type == dt]:
                        for d in prefs.devices: d.use = d.type == dt
                        c.device = 'GPU'; print(f"[scene] GPU: {dt}", flush=True); break
                except Exception: pass
    os.makedirs(out, exist_ok=True)
    r.filepath = os.path.join(out, "")
    r.use_overwrite = False; r.use_placeholder = True

def render(scene, times=None, fps=30):
    if times:
        r = scene.render; base = r.filepath
        for tt in times:
            f = int(round(float(tt) * fps)) + 1
            scene.frame_set(f); r.filepath = os.path.join(base, f"t_{float(tt):06.2f}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
