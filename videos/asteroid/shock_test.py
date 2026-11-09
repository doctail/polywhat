"""Realism test clip for the asteroid video: Chelyabinsk shock wave arriving on 5th Ave (timeline ~170-182 s).
Blender script:
  blender -b --factory-startup -P videos/asteroid/shock_test.py -- --assets /workspace/assets --out DIR
          [--res 1920x1080] [--samples 48] [--engine cycles|eevee] [--device gpu|cpu] [--frames 1-360|a,b,c]
          [--no-dust] [--fps 30]
Frames go to DIR/frame_0001.png ...; existing frames are skipped (resume)."""
import sys, os, math, random, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'city'))
import bpy
import numpy as np
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--assets', default='/workspace/assets'); ap.add_argument('--out', default='out/shock_test')
ap.add_argument('--res', default='1920x1080'); ap.add_argument('--samples', type=int, default=48)
ap.add_argument('--engine', default='cycles'); ap.add_argument('--device', default='gpu')
ap.add_argument('--frames', default=''); ap.add_argument('--no-dust', action='store_true'); ap.add_argument('--no-glass', action='store_true'); ap.add_argument('--cards', action='store_true')
ap.add_argument('--fps', type=int, default=30); ap.add_argument('--quality', action='store_true'); ap.add_argument('--city', default='chicago'); ap.add_argument('--blend', default='')
ARGS = ap.parse_args(argv)
os.makedirs(ARGS.out, exist_ok=True)

FPS = ARGS.fps; DUR = 12.0; NF = int(DUR * FPS)
T_SHOCK = 4.0                    # = timeline 174.0 s (EVENTS ch_shock)
TL_OFFSET = 170.0
C_SOUND = 340.0

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = FPS; scn.frame_start = 1; scn.frame_end = NF
random.seed(11); np.random.seed(11)

# ---------------------------------------------------------------- 1) people first (bpy.ops is cheap in an empty scene)
import people as PP
MOC = os.path.join(ROOT, 'tools', 'city', 'mocap')
ppl_coll = bpy.data.collections.new('people'); scn.collection.children.link(ppl_coll)
BVH = [os.path.join(MOC, f) for f in sorted(os.listdir(MOC)) if f.endswith('.bvh')]
N_IDLE, N_WALK = 22, 8
crowd = []
try:
    import humans; HF = humans.HumanFactory(ppl_coll); print('[people] MPFB humans', flush=True)
except Exception as e:
    HF = None; print('[people] MPFB not available, using mannequins:', repr(e)[:200], flush=True)
for i in range(N_IDLE + N_WALK):
    walker = i >= N_IDLE
    if HF: P = HF.make(100 + i, walker_bvh=BVH[i % len(BVH)] if walker else None)
    else: P = PP.make_person(BVH[i % len(BVH)], 100 + i, ppl_coll)
    P['walker'] = walker
    crowd.append(P)
print('people built', flush=True)

# ---------------------------------------------------------------- 2) the city
class NS: pass
A = NS(); A.tex = os.path.join(ARGS.assets, 'tex'); A.models = os.path.join(ARGS.assets, 'models')
A.city_dir = os.path.join(ROOT, 'tools', 'city'); A.engine = ARGS.engine; A.city = ARGS.city
CITIES = {
    # 5th Ave between 38th and 39th St, looking south to the Empire State
    'nyc': dict(osm='osm_midtown.json', lat0=40.7515, lon0=-73.9840, area=(-860, -800, 780, 820), street=['5th Avenue'],
                look=(-0.5, -0.87), pos=1000.0, default_h=[14, 18, 22, 26, 30], landmark=(-211, -333, 70)),
    # State Street between Monroe and Adams, looking south down the Loop
    'chicago': dict(osm='osm_chicago.json', lat0=41.8815, lon0=-87.6300, area=(-820, -820, 820, 820),
                    street=['South State Street'], look=(0, -1), pos=100.0, default_h=[30, 45, 60, 80, 110]),
}
for k, v in CITIES[ARGS.city].items(): setattr(A, k, v)
A.osm = os.path.join(ROOT, 'tools', 'city', 'data', A.osm)
G = dict(A=A, __name__='city')
CITY = os.path.join(ROOT, 'tools', 'city', 'city.py')
exec(compile(open(CITY).read(), CITY, 'exec'), G)
base, d, n, FW = G['base'], G['d'], G['n'], G['FW']
side_poly = G['side_poly']; buildings = G['buildings']
from shapely.geometry import Point
east = n; w_dir = -d                       # the wave travels away from the impact, toward the camera and past it
from shapely.strtree import STRtree
_bt = STRtree([b[0] for b in buildings]); _bl = [b[0] for b in buildings]
def in_building(p2):
    pt = Point(p2); return any(_bl[i].contains(pt) for i in _bt.query(pt))
def on_sidewalk(p2, margin=0.0):
    pt = Point(p2)
    if not side_poly.contains(pt) or in_building(p2): return False
    return margin <= 0 or not any(_bl[i].distance(pt) < margin for i in _bt.query(pt.buffer(margin)))
curb = next(o for o in np.arange(FW / 2 - 3, FW / 2 + 10, 0.2) if on_sidewalk(base + east * o))
wall = next((o for o in np.arange(curb, curb + 15, 0.2) if not on_sidewalk(base + east * o)), curb + 4)
CAM = base + east * (curb + min(1.6, (wall - curb) * 0.45))
print(f'sidewalk from {curb:.1f} to {wall:.1f} m off the centre line; camera at {np.dot(CAM - base, east):.1f}', flush=True)
def arrival(p2):                           # seconds
    return T_SHOCK + float(np.dot(np.array(p2[:2]) - CAM, w_dir)) / C_SOUND
print('city built', flush=True)

for o in [o for o in scn.collection.objects if o.name.startswith(('i_hydrant', 'i_trash', 'i_streetlamp', 'i_sig', 'i_tree'))]:
    p = np.array(o.location[:2])
    if min(np.linalg.norm(p - (CAM + d * s)) for s in (0, 1, 2)) < 5.0: bpy.data.objects.remove(o)
for o in [o for o in scn.collection.objects if o.name.startswith('i_car')]:
    p = np.array(o.location[:2]); rel = p - CAM
    if np.dot(rel, d) < 16 and abs(np.dot(rel, east)) < 9: bpy.data.objects.remove(o)
# ---------------------------------------------------------------- 3) place & animate people
def sidewalk_spot(along, side_off):
    p = base + d * along + east * side_off
    return p if on_sidewalk(p, 0.6) else None
def yaw_of(P):
    fwd, up, right = PP._frame_axes(P)
    wv = P['arm'].matrix_world.to_3x3() @ fwd
    return math.atan2(wv.y, wv.x)
sky_dir = d * 0.8 + east * 0.25          # the trail is to the south-southeast
spots = []
for P in crowd:
    for _ in range(200):
        side = random.choice([1, 1, -1])               # more on the camera side
        off = side * (curb + random.uniform(0.6, 3.5))
        along = random.uniform(8, 60) if side > 0 else random.uniform(4, 70)
        p = sidewalk_spot(along, off)
        if p is not None and all(np.linalg.norm(p - q) > 1.4 for q in spots) and np.linalg.norm(p - CAM) > 9.0 and np.dot(p - CAM, d) > 6: break
        p = None
    if p is None:                                    # no room left on the sidewalk: drop this person
        for o in [P['root'], P['arm']] + list(P['arm'].children) + ([P['mesh']] if 'mesh' in P else []): o.hide_render = True
        continue
    spots.append(p)
    root = P['root']; root.location = (p[0], p[1], 0.15)
    bpy.context.view_layer.update()
    shock_f = arrival(p) * FPS
    react = shock_f + random.uniform(3, 10)          # human reaction ~0.1-0.33 s
    if P['walker']:
        dirn = d if random.random() < 0.5 else -d
        root.rotation_euler.z = 0; bpy.context.view_layer.update()
        root.rotation_euler.z = math.atan2(dirn[1], dirn[0]) - yaw_of(P)
        a0, a1 = P['action'].frame_range
        end = int(a1) - 1
        PP.hold_pose(P, end, end + 1)
        scn.frame_set(end + 1)
        PP.look_up(P, end + 10, random.uniform(20, 35))
    else:
        PP.make_idle(P)
        tgt = sky_dir + np.random.normal(0, 0.35, 2)
        root.rotation_euler.z = 0; bpy.context.view_layer.update()
        root.rotation_euler.z = math.atan2(tgt[1], tgt[0]) - yaw_of(P)
        scn.frame_set(1)
        PP.look_up(P, 1, random.uniform(22, 40), point=random.random() < 0.2)
    # hold the look until the wave, then duck and cover
    f_hold = int(react) - 2
    scn.frame_set(f_hold)
    for pb in P['arm'].pose.bones:
        pb.keyframe_insert('location', frame=f_hold); pb.keyframe_insert('rotation_quaternion', frame=f_hold)
    scn.frame_set(int(react) + 5)
    PP.cover(P, int(react) + 5, lean=random.uniform(30, 55))
scn.frame_set(1)
print('people placed', flush=True)

# ---------------------------------------------------------------- 4) glass: window shards from street-facing facades
glass = bpy.data.materials.new('shard'); gb = glass.node_tree.nodes['Principled BSDF']
gb.inputs['Base Color'].default_value = (0.32, 0.38, 0.4, 1); gb.inputs['Metallic'].default_value = 0.9
gb.inputs['Roughness'].default_value = 0.12; gb.inputs['Coat Weight'].default_value = 1.0
# one irregular shard triangle, size 1
sh_me = bpy.data.meshes.new('shard'); sh_me.from_pydata([(0, 0, 0), (1, 0.15, 0.05), (0.35, 0.9, -0.05)], [], [(0, 1, 2)])
sh_me.materials.append(glass); shard_obj = bpy.data.objects.new('shard_src', sh_me)
G['lib'].objects.link(shard_obj)
pts, vel, t0, tl, spin, size = [], [], [], [], [], []
# car footprints: shards that fall on a car stop on its roof instead of passing through it
from shapely.geometry import Polygon as _Poly
_clen = {id(c): L for c, L in G['CARS']}
_cars = []
for o in scn.collection.objects:
    c = getattr(o, 'instance_collection', None)
    if c is None or id(c) not in _clen: continue
    L = _clen[id(c)]; W = 1.95; a = o.rotation_euler.z; ca, sa = math.cos(a), math.sin(a)
    pts_ = [(o.location.x + ca * x - sa * y, o.location.y + sa * x + ca * y) for x, y in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2))]
    _cars.append((_Poly(pts_).buffer(0.15), float(c.get('height', 1.5)) + 0.03))     # land ON the roof, never inside the cabin
_ct = STRtree([c[0] for c in _cars]) if _cars else None
def ground_at(x, y):
    if _ct is None: return Z_GROUND
    pt = Point(x, y)
    for i in _ct.query(pt):
        if _cars[i][0].contains(pt): return _cars[i][1]
    return Z_GROUND
G_ACC = 9.81; Z_GROUND = 0.17
for pg, h, mh, tags, roof in buildings:
    c = np.array(pg.centroid.coords[0])
    if np.linalg.norm(c - CAM) > 260 or mh > 1: continue
    ring = G['ring_dir'](pg.exterior.coords, True)
    for i in range(len(ring)):
        a_, b_ = np.array(ring[i]), np.array(ring[(i + 1) % len(ring)])
        L = np.linalg.norm(b_ - a_)
        if L < 4: continue
        t_ = (b_ - a_) / L; nrm = np.array([t_[1], -t_[0]])          # outward for CCW
        if abs(np.dot(nrm, east)) < 0.8: continue                     # only walls facing the avenue
        mid = (a_ + b_) / 2
        if abs(np.dot(mid - base, east)) > FW / 2 + 16: continue      # must front 5th Ave
        if np.dot(nrm, base - mid) < 0: continue                      # facing the street
        along = float(np.dot(mid - CAM, d))
        if along < -40 or along > 150: continue
        for s in np.arange(1.5, L - 1, 3.0):
            for z in np.arange(6.0, min(h - 1, 75), 3.6):
                if random.random() < 0.35: continue                   # not every window goes
                p0 = a_ + t_ * s
                ta = arrival(p0)
                for k in range(random.randint(10, 18)):
                    q = p0 + t_ * random.uniform(-1.2, 1.2) + nrm * 0.05
                    zz = z + random.uniform(-1.2, 1.2)
                    v = nrm * random.uniform(1.5, 7.0) + t_ * random.uniform(-1.5, 1.5) + w_dir * random.uniform(0.5, 4.0)
                    vz = random.uniform(-1.0, 3.0)
                    # time to reach the ground:  zz + vz t - g/2 t^2 = Z_GROUND
                    tland = (vz + math.sqrt(vz * vz + 2 * G_ACC * (zz - Z_GROUND))) / G_ACC
                    zg = ground_at(q[0] + v[0] * tland, q[1] + v[1] * tland)
                    if zg > Z_GROUND: tland = (vz + math.sqrt(vz * vz + 2 * G_ACC * (zz - zg))) / G_ACC
                    land = np.array([q[0] + v[0] * tland, q[1] + v[1] * tland])
                    if np.linalg.norm(land - CAM) < 15 and random.random() < 0.7: continue   # no confetti carpet at the lens
                    pts.append((q[0], q[1], zz)); vel.append((v[0], v[1], vz))
                    t0.append(ta + random.uniform(0.0, 0.12)); tl.append(tland)
                    spin.append((random.uniform(-25, 25), random.uniform(-25, 25), random.uniform(-25, 25)))
                    size.append(random.uniform(0.04, 0.12) * (1.6 if random.random() < 0.06 else 1.0))
print('shards', len(pts), flush=True)
pm = bpy.data.meshes.new('shard_pts'); pm.from_pydata(pts, [], [])
def attr(name, typ, data, comp):
    at = pm.attributes.new(name, typ, 'POINT'); at.data.foreach_set('vector' if comp == 3 else 'value', np.array(data, dtype=np.float32).ravel())
attr('vel', 'FLOAT_VECTOR', vel, 3); attr('spin', 'FLOAT_VECTOR', spin, 3)
attr('t0', 'FLOAT', t0, 1); attr('tl', 'FLOAT', tl, 1); attr('size', 'FLOAT', size, 1)
shards = bpy.data.objects.new('shards', pm); scn.collection.objects.link(shards)

ng = bpy.data.node_groups.new('shard_fall', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N = ng.nodes; Lk = ng.links.new
gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
def named(name, typ):
    x = N.new('GeometryNodeInputNamedAttribute'); x.data_type = typ; x.inputs['Name'].default_value = name; return x.outputs['Attribute']
def math_(op, a, b=None, clamp=False):
    m = N.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    for i, v in enumerate([a, b]):
        if v is None: continue
        if isinstance(v, (int, float)): m.inputs[i].default_value = v
        else: Lk(v, m.inputs[i])
    return m.outputs[0]
def vmath(op, a, b):
    m = N.new('ShaderNodeVectorMath'); m.operation = op
    Lk(a, m.inputs[0])
    if op == 'SCALE':
        if isinstance(b, (int, float)): m.inputs['Scale'].default_value = b
        else: Lk(b, m.inputs['Scale'])
    else:
        if isinstance(b, tuple): m.inputs[1].default_value = b
        else: Lk(b, m.inputs[1])
    return m.outputs[0]
st = N.new('GeometryNodeInputSceneTime')
tt = math_('SUBTRACT', st.outputs['Seconds'], named('t0', 'FLOAT'))
te = math_('MINIMUM', math_('MAXIMUM', tt, 0.0), named('tl', 'FLOAT'))
off = vmath('SCALE', named('vel', 'FLOAT_VECTOR'), te)
cz = N.new('ShaderNodeCombineXYZ'); Lk(math_('MULTIPLY', math_('MULTIPLY', te, te), -0.5 * G_ACC), cz.inputs['Z'])
off = vmath('ADD', off, cz.outputs[0])
sp = N.new('GeometryNodeSetPosition'); Lk(gi.outputs[0], sp.inputs['Geometry']); Lk(off, sp.inputs['Offset'])
vis = N.new('FunctionNodeCompare'); vis.data_type = 'FLOAT'; vis.operation = 'GREATER_THAN'
Lk(tt, vis.inputs[0]); vis.inputs[1].default_value = 0.0
oi = N.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = shard_obj
iop = N.new('GeometryNodeInstanceOnPoints')
Lk(sp.outputs[0], iop.inputs['Points']); Lk(vis.outputs[0], iop.inputs['Selection']); Lk(oi.outputs['Geometry'], iop.inputs['Instance'])
rot = N.new('FunctionNodeEulerToRotation'); Lk(vmath('SCALE', named('spin', 'FLOAT_VECTOR'), te), rot.inputs[0])
Lk(rot.outputs[0], iop.inputs['Rotation'])
Lk(named('size', 'FLOAT'), iop.inputs['Scale'])
Lk(iop.outputs[0], go.inputs[0])
mod = shards.modifiers.new('fall', 'NODES'); mod.node_group = ng
if ARGS.no_glass: shards.hide_render = True

broken = None
for m in list(G['FAC'].values()) + [G['M_STORE'], G['ESB_MAT']]:
    nt_ = m.node_tree; bsd = nt_.nodes['Principled BSDF']
    if not bsd.inputs['Metallic'].links or not bsd.inputs['Base Color'].links: continue
    if broken is None:
        broken = {}
    vb = nt_.nodes.new('ShaderNodeValue'); vb.outputs[0].default_value = 0.0
    vb.outputs[0].keyframe_insert('default_value', frame=int((T_SHOCK + 0.05) * FPS))
    vb.outputs[0].default_value = 0.85; vb.outputs[0].keyframe_insert('default_value', frame=int((T_SHOCK + 0.5) * FPS))
    met = bsd.inputs['Metallic'].links[0].from_socket; col = bsd.inputs['Base Color'].links[0].from_socket
    mm = nt_.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt_.links.new(met, mm.inputs[0]); nt_.links.new(vb.outputs[0], mm.inputs[1])
    mx_ = nt_.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; nt_.links.new(mm.outputs[0], mx_.inputs[0])
    nt_.links.new(col, mx_.inputs[6]); mx_.inputs[7].default_value = (0.012, 0.012, 0.014, 1)
    nt_.links.new(mx_.outputs[2], bsd.inputs['Base Color'])
    inv = nt_.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt_.links.new(vb.outputs[0], inv.inputs[1])
    mm2 = nt_.nodes.new('ShaderNodeMath'); mm2.operation = 'MULTIPLY'; nt_.links.new(met, mm2.inputs[0]); nt_.links.new(inv.outputs[0], mm2.inputs[1])
    nt_.links.new(mm2.outputs[0], bsd.inputs['Metallic'])

# ---------------------------------------------------------------- 5) trees whip, car hazard lights, camera
for o in scn.collection.objects:
    if not o.name.startswith('i_tree'): continue
    p = np.array(o.location[:2]);
    if np.linalg.norm(p - CAM) > 400: continue
    f0 = arrival(p) * FPS; k = np.array([-w_dir[1], w_dir[0]])       # tilt axis
    rz = o.rotation_euler.z
    for df, a in [(0, 0), (4, 0.22), (9, -0.07), (15, 0.12), (22, -0.03), (30, 0.06), (45, 0.0)]:
        o.rotation_euler = (a * k[0], a * k[1], rz); o.keyframe_insert('rotation_euler', frame=f0 + df)
head = G['M_HEAD'].node_tree.nodes['Principled BSDF']
for f in range(1, NF + 1, 1):
    t = f / FPS
    on = t > T_SHOCK + 0.6 and int((t - T_SHOCK) * 2.4) % 2 == 0
    head.inputs['Emission Strength'].default_value = 9.0 if on else 1.5
    head.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    head.inputs['Emission Color'].default_value = (1.0, 0.45, 0.05, 1) if t > T_SHOCK + 0.6 else (1.0, 0.95, 0.85, 1)
    head.inputs['Emission Color'].keyframe_insert('default_value', frame=f)

# Chelyabinsk smoke trail: a long thickening tube high in the southern sky
from mathutils import Vector as V
tp0 = base + d * 9000 + east * 7000; tp1 = base + d * 6000 - east * 3000
cu = bpy.data.curves.new('trail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 4
spl = cu.splines.new('POLY'); spl.points.add(23)
for i, pt in enumerate(spl.points):
    u = i / 23
    p = tp0 * (1 - u) + tp1 * u
    pt.co = (p[0], p[1], 5200 - 3600 * u + 250 * math.sin(u * 7), 1)
    pt.radius = 25 + 160 * u + 40 * math.sin(u * 13) ** 2
trail = bpy.data.objects.new('trail', cu); scn.collection.objects.link(trail)
tm = bpy.data.materials.new('trail'); tb = tm.node_tree.nodes['Principled BSDF']
tb.inputs['Base Color'].default_value = (0.95, 0.93, 0.9, 1); tb.inputs['Roughness'].default_value = 1.0
tb.inputs['Subsurface Weight'].default_value = 0.0; tb.inputs['Alpha'].default_value = 0.85
tb.inputs['Emission Color'].default_value = (1, 0.97, 0.92, 1); tb.inputs['Emission Strength'].default_value = 0.35
ntm = tm.node_tree; lw = ntm.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
trn = ntm.nodes.new('ShaderNodeBsdfTransparent'); ms = ntm.nodes.new('ShaderNodeMixShader')
pw = ntm.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 0.6
ntm.links.new(lw.outputs['Facing'], pw.inputs[0])
ad = ntm.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.use_clamp = True; ad.inputs[1].default_value = 0.45
ntm.links.new(pw.outputs[0], ad.inputs[0]); ntm.links.new(ad.outputs[0], ms.inputs[0])
ntm.links.new(tb.outputs[0], ms.inputs[1]); ntm.links.new(trn.outputs[0], ms.inputs[2])
ntm.links.new(ms.outputs[0], ntm.nodes['Material Output'].inputs['Surface'])
tb.inputs['Alpha'].default_value = 1.0
cu.materials.append(tm)

# dust: kicked up behind the wave front, rolling north along the avenue
# camera object (animated further down)
cam_data = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_data); scn.collection.objects.link(cam); scn.camera = cam
if ARGS.cards:
    dm = bpy.data.materials.new('dustcard')
    try: dm.surface_render_method = 'DITHERED'
    except Exception: pass
    nt = dm.node_tree; Nn = nt.nodes; Ll = nt.links.new
    bs = Nn['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.6, 0.56, 0.5, 1); bs.inputs['Roughness'].default_value = 1.0
    tc = Nn.new('ShaderNodeTexCoord'); oi_ = Nn.new('ShaderNodeObjectInfo')
    nz = Nn.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.2
    nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.62
    Ll(tc.outputs['Generated'], nz.inputs['Vector'])
    wm_ = Nn.new('ShaderNodeMath'); wm_.operation = 'MULTIPLY'; wm_.inputs[1].default_value = 37.0
    Ll(oi_.outputs['Random'], wm_.inputs[0]); Ll(wm_.outputs[0], nz.inputs['W'])
    nr = Nn.new('ShaderNodeMapRange'); nr.inputs['From Min'].default_value = 0.42; nr.inputs['From Max'].default_value = 0.72
    Ll(nz.outputs['Fac'], nr.inputs['Value'])
    sub = Nn.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    Ll(tc.outputs['Generated'], sub.inputs[0])
    ln = Nn.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; Ll(sub.outputs[0], ln.inputs[0])
    rr = Nn.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0.5; rr.inputs['From Max'].default_value = 0.1
    rr.interpolation_type = 'SMOOTHSTEP'; Ll(ln.outputs['Value'], rr.inputs['Value'])
    m1 = Nn.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; Ll(nr.outputs['Result'], m1.inputs[0]); Ll(rr.outputs['Result'], m1.inputs[1])
    m2 = Nn.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; Ll(m1.outputs[0], m2.inputs[0]); Ll(oi_.outputs['Alpha'], m2.inputs[1])
    Ll(m2.outputs[0], bs.inputs['Alpha'])
    pme = bpy.data.meshes.new('card'); pme.from_pydata([(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0)], [], [(0, 1, 2, 3)])
    pme.uv_layers.new(); pme.materials.append(dm)
    cards = []
    def card(p, z, t_on, s0, s1, a_max, rise, drift, near=False):
        o = bpy.data.objects.new('dust', pme); scn.collection.objects.link(o); cards.append(o)
        con = o.constraints.new('DAMPED_TRACK'); con.target = cam; con.track_axis = 'TRACK_Z'
        f_on = t_on * FPS
        for df, sc_, al, up, dr in [(-1, s0 * 0.3, 0.0, 0, 0), (3, s0, a_max, 0.3, 0.25), (20, (s0 + s1) / 2, a_max * 0.95, 0.6, 0.65),
                                    (60, s1 * 0.85, a_max * 0.8, 0.85, 0.9), (200, s1, a_max * 0.6, 1.0, 1.0)]:
            o.scale = (sc_, sc_, sc_); o.color = (1, 1, 1, al)
            q = p + w_dir * drift * dr
            o.location = (q[0], q[1], z + rise * up)
            for path in ('scale', 'color', 'location'): o.keyframe_insert(path, frame=f_on + df)
    rnd = random.Random(5)
    for i in range(90):
        along = rnd.uniform(8, 320); lat = rnd.uniform(-(FW / 2 + 4), FW / 2 + 4)
        p = base + d * along + east * lat
        card(p, rnd.uniform(0.6, 5), arrival(p) + rnd.uniform(0.0, 0.25), rnd.uniform(5, 10), rnd.uniform(14, 30),
             rnd.uniform(0.35, 0.7), rnd.uniform(4, 14), rnd.uniform(6, 22))
    for i in range(10):                                   # a few close to the lens, rushing past
        p = CAM + d * rnd.uniform(4, 14) + east * rnd.uniform(-9, 2)
        card(p, rnd.uniform(0.8, 2.5), arrival(p) + rnd.uniform(0.05, 0.3), 3, rnd.uniform(9, 14), rnd.uniform(0.25, 0.45), 3, rnd.uniform(8, 16))
    print('dust cards', len(cards), flush=True)

# camera: slow push, shake at the wave
cam_data.lens = 20; cam_data.sensor_width = 36; cam_data.clip_end = 30000
look_t = base + d * 70 - east * 30
rng = np.random.default_rng(3)
for f in range(1, NF + 1):
    t = f / FPS
    p = CAM + d * min(t, T_SHOCK) * 0.35 + d * max(0, t - T_SHOCK) * 0.05
    z = 1.62
    tgt = V((look_t[0], look_t[1], 17.0))
    loc = V((p[0], p[1], z))
    q = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    if t >= T_SHOCK:
        dec = math.exp(-(t - T_SHOCK) * 1.6) * (1.0 if t - T_SHOCK > 0.05 else 0.6)
        loc += V(tuple(rng.normal(0, 0.05 * dec, 3)))
        q = Euler((q.x + rng.normal(0, 0.022 * dec), q.y + rng.normal(0, 0.012 * dec), q.z + rng.normal(0, 0.02 * dec)))
    cam.location = loc; cam.rotation_euler = q
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
# shake keys must not be smoothed
if cam.animation_data and cam.animation_data.action:
    for fc in PP._fcurves(cam.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ---------------------------------------------------------------- 6) render
rx, ry = map(int, ARGS.res.split('x'))
scn.render.resolution_x, scn.render.resolution_y = rx, ry
scn.render.image_settings.file_format = 'PNG'
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Base Contrast'; scn.view_settings.exposure = 0.6
# production ("fast") profile by default; --quality restores the slow settings
scn.render.use_motion_blur = ARGS.quality; scn.render.motion_blur_shutter = 0.5
if ARGS.engine == 'cycles':
    scn.render.engine = 'CYCLES'; scn.cycles.samples = ARGS.samples; scn.cycles.use_denoising = True; scn.cycles.denoising_input_passes = 'RGB'; scn.cycles.denoising_prefilter = 'NONE'
    scn.cycles.transparent_max_bounces = 64; scn.cycles.max_bounces = 4; scn.cycles.glossy_bounces = 3; scn.cycles.diffuse_bounces = 2; scn.cycles.volume_bounces = 0
    if not ARGS.quality:
        c = scn.cycles
        c.max_bounces = 3; c.diffuse_bounces = 1; c.glossy_bounces = 1; c.transmission_bounces = 1; c.transparent_max_bounces = 8
        c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05; c.adaptive_min_samples = 4
        c.use_fast_gi = True; c.fast_gi_method = 'REPLACE'
        c.texture_limit_render = '2048'
        c.sample_clamp_indirect = 3.0                          # kills fireflies from the shards early
        scn.render.use_simplify = True; scn.render.simplify_subdivision_render = 0
    scn.cycles.caustics_reflective = False; scn.cycles.caustics_refractive = False
    scn.cycles.volume_step_rate = 4.0
    if ARGS.device == 'gpu':
        pr = bpy.context.preferences.addons['cycles'].preferences
        for tdev in ('OPTIX', 'CUDA'):
            try: pr.compute_device_type = tdev; break
            except Exception: pass
        pr.get_devices(); [setattr(dv, 'use', dv.type != 'CPU') for dv in pr.devices]; scn.cycles.device = 'GPU'
        scn.render.use_persistent_data = True
        try: scn.cycles.denoiser = 'OPTIX'                   # GPU denoiser, much faster than OIDN on CPU
        except Exception: pass
else:
    scn.render.engine = 'BLENDER_EEVEE'; ee = scn.eevee; ee.taa_render_samples = ARGS.samples
    for k, v in dict(use_raytracing=True, ray_tracing_method='SCREEN', use_fast_gi=True, use_shadows=True,
                     shadow_ray_count=2, shadow_step_count=8).items():
        try: setattr(ee, k, v)
        except Exception as e: print('[eevee] skip', k, e)
    # same lighting as Cycles: the HDRI sun is extracted as a shadow-casting sun (no extra lamp)
    if 'sun' in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects['sun'])
    W = G['world']
    for k, v in dict(sun_threshold=5.0, sun_angle=math.radians(0.6), use_sun_shadow=True).items():
        try: setattr(W, k, v)
        except Exception as e: print('[eevee] skip', k, e)
# haze + DUST, both in the compositor (no sampling noise, ~free): depth from the mist pass.
# dust at a pixel starts when the wave reaches that depth:  since = (t - T) + depth / c ;  depth = 40 + mist * 2460
bpy.context.view_layer.use_pass_mist = True
G['world'].mist_settings.start = 40; G['world'].mist_settings.depth = 2500; G['world'].mist_settings.falloff = 'LINEAR'
tr = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); scn.compositing_node_group = tr
tr.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
TN = tr.nodes; TL_ = tr.links.new
rl = TN.new('CompositorNodeRLayers'); outn = TN.new('NodeGroupOutput')
def cm(op, a, b=None, clamp=False):
    m = TN.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    for i, v in enumerate([a, b]):
        if v is None: continue
        if isinstance(v, (int, float)): m.inputs[i].default_value = v
        else: TL_(v, m.inputs[i])
    return m
mist = rl.outputs['Mist']
haze = cm('MULTIPLY', mist, 0.3)
SINCE = cm('ADD', cm('MULTIPLY', mist, 2460.0 / C_SOUND).outputs[0], 40.0 / C_SOUND)       # input[1] of the next node set per frame
since = cm('ADD', SINCE.outputs[0], 0.0); T_IN = since                                   # since = depth/c + (t - T)
grow = cm('MULTIPLY', since.outputs[0], 0.9, clamp=True)
ic = TN.new('CompositorNodeImageCoordinates')
img_in = rl.outputs['Image']; TL_(img_in, ic.inputs[0])
DRIFT = TN.new('ShaderNodeVectorMath'); DRIFT.operation = 'ADD'; TL_(ic.outputs['Uniform'], DRIFT.inputs[0])
nz = TN.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.6
nz.inputs['Detail'].default_value = 7; nz.inputs['Roughness'].default_value = 0.6
TL_(DRIFT.outputs[0], nz.inputs['Vector'])
nr = TN.new('ShaderNodeMapRange'); nr.inputs['From Min'].default_value = 0.22; nr.inputs['From Max'].default_value = 0.62
TL_(nz.outputs['Fac'], nr.inputs['Value'])
sep = TN.new('ShaderNodeSeparateXYZ'); TL_(ic.outputs['Normalized'], sep.inputs[0])
ylow = cm('SUBTRACT', 1.5, cm('MULTIPLY', sep.outputs['Y'], 1.0).outputs[0], clamp=True)   # thicker near the ground
dist = cm('MULTIPLY', cm('POWER', mist, 0.25).outputs[0], 1.6, clamp=True)                  # nothing right on the lens
dust = cm('MULTIPLY', cm('MULTIPLY', grow.outputs[0], nr.outputs['Result']).outputs[0], cm('MULTIPLY', ylow.outputs[0], dist.outputs[0]).outputs[0])
DUST_GAIN = cm('MULTIPLY', dust.outputs[0], 0.0)                                            # gain set per frame
fac = cm('ADD', haze.outputs[0], DUST_GAIN.outputs[0], clamp=True)
mx = TN.new('ShaderNodeMix'); mx.data_type = 'RGBA'
TL_(fac.outputs[0], mx.inputs[0]); TL_(img_in, mx.inputs[6]); mx.inputs[7].default_value = (0.62, 0.66, 0.72, 1)
TL_(mx.outputs[2], outn.inputs[0])

if ARGS.blend: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ARGS.blend))
if ARGS.frames:
    if '-' in ARGS.frames: a_, b_ = map(int, ARGS.frames.split('-')); frames = range(a_, b_ + 1)
    else: frames = [int(x) for x in ARGS.frames.split(',')]
else: frames = range(1, NF + 1)
import time
for f in frames:
    path = os.path.join(os.path.abspath(ARGS.out), f'frame_{f:04d}.png')
    if os.path.exists(path): continue
    t = f / FPS
    T_IN.inputs[1].default_value = t - T_SHOCK
    k = 0.0 if t < T_SHOCK - 1.6 else min(1.0, (t - T_SHOCK + 1.6) / 1.6)          # the wall shows up 1.6 s before it hits
    DUST_GAIN.inputs[1].default_value = 0.0 if ARGS.no_dust else 1.15 * k
    DRIFT.inputs[1].default_value = (-0.35 * max(0, t - T_SHOCK), 0.12 * max(0, t - T_SHOCK), 0)   # rolls across the frame
    nz.inputs['W'].default_value = 0.35 * t
    dk = 0.0 if t < T_SHOCK else min(1.0, (t - T_SHOCK) / 1.5)
    mx.inputs[7].default_value = tuple(a * (1 - dk) + b * dk for a, b in zip((0.62, 0.66, 0.72), (0.68, 0.63, 0.56))) + (1,)
    t1 = time.time(); scn.frame_set(f); scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f'[shock] frame {f}/{NF} {time.time() - t1:.1f}s', flush=True)
