"""Control sheet: every downloaded vehicle side-on, FRONT should point RIGHT (+X).
  blender -b --factory-startup -P tools/city/car_sheet.py -- /workspace/assets OUT.png [--cpu]
Cars whose nose points left need {"flip": true} in tools/city/cars_fix.json."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
argv = sys.argv[sys.argv.index('--') + 1:]
ASSETS, OUT = argv[0], argv[1]; CPU = '--cpu' in argv
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
import cars
lib = bpy.data.collections.new('lib'); scn.collection.children.link(lib)
bpy.context.view_layer.layer_collection.children['lib'].exclude = True
def mk(name):
    c = bpy.data.collections.new(name); lib.children.link(c); return c
root = os.path.join(ASSETS, 'cars'); items = []
for nm in sorted(os.listdir(root)):
    bl = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(root, nm)) for f in fs if f.endswith('.blend')]
    if bl:
        r = cars.load_real_car(nm, max(bl, key=os.path.getsize), mk)
        if r: items.append((nm, r[0]))
COLS = 4
for i, (nm, coll) in enumerate(items):
    x = (i % COLS) * 7.0; z = -(i // COLS) * 4.2
    o = bpy.data.objects.new(nm, None); o.instance_type = 'COLLECTION'; o.instance_collection = coll
    o.location = (x, 0, z); scn.collection.objects.link(o)
    cu = bpy.data.curves.new(nm, 'FONT'); cu.body = f'{i + 1}. {nm}   FRONT >'; cu.size = 0.42; cu.align_x = 'CENTER'
    t = bpy.data.objects.new('t' + nm, cu); t.location = (x, -1.5, z + 2.45); t.rotation_euler = (math.pi / 2, 0, 0)
    m = bpy.data.materials.new('txt'); m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.1, 0.05, 1)
    cu.materials.append(m); scn.collection.objects.link(t)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scn.collection.objects.link(cam); scn.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = COLS * 7.0 + 1
rows = (len(items) + COLS - 1) // COLS
cam.location = ((COLS - 1) * 3.5, -40, -(rows - 1) * 2.1 + 1.0); cam.rotation_euler = (math.pi / 2, 0, 0)
w = bpy.data.worlds.new('w'); scn.world = w; w.node_tree.nodes['Background'].inputs[0].default_value = (0.8, 0.82, 0.85, 1)
s = bpy.data.lights.new('s', 'SUN'); s.energy = 3; so = bpy.data.objects.new('s', s); so.rotation_euler = (0.9, 0.2, 0.4); scn.collection.objects.link(so)
scn.render.resolution_x, scn.render.resolution_y = 1920, int(1920 * (rows * 4.2 + 1) / (COLS * 7.0 + 1))
scn.render.engine = 'CYCLES'; scn.cycles.samples = 16; scn.cycles.use_denoising = True
if not CPU:
    pr = bpy.context.preferences.addons['cycles'].preferences
    for tdev in ('OPTIX', 'CUDA'):
        try: pr.compute_device_type = tdev; break
        except Exception: pass
    pr.get_devices(); [setattr(dv, 'use', dv.type != 'CPU') for dv in pr.devices]; scn.cycles.device = 'GPU'
scn.render.filepath = os.path.abspath(OUT); bpy.ops.render.render(write_still=True); print('[cars] sheet ->', OUT)
