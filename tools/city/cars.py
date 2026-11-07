"""Load a downloaded vehicle .blend as a normalised asset collection: real size, centred, wheels on z=0,
front pointing +X.  Per-model fixes in cars_fix.json  {"name": {"flip": true, "yaw": 0, "scale": 1.0}}."""
import os, re, math, json
import bpy
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = json.load(open(os.path.join(HERE, 'cars_fix.json'))) if os.path.exists(os.path.join(HERE, 'cars_fix.json')) else {}
FRONT_KW = re.compile(r'head|front|grill|grille|hood|bonnet|windshield|windscreen|wiper', re.I)
REAR_KW = re.compile(r'tail|rear|back|trunk|boot|brake|exhaust|spoiler', re.I)
JUNK_KW = re.compile(r'shadow|ground|floor|backdrop|studio|catcher|^WGT|sensor', re.I)   # NOT 'plane': modellers often leave bodies named Plane.0xx

def load_real_car(name, path, make_collection):
    try:
        with bpy.data.libraries.load(path, link=False) as (src, dst): dst.objects = list(src.objects)
    except Exception as e:
        print('[cars] cannot read', path, e, flush=True); return None
    objs = [o for o in dst.objects if o is not None and o.type in ('MESH', 'EMPTY', 'CURVE', 'ARMATURE')]
    def wmat(o):                       # matrix_world is not evaluated for freshly appended data
        m = o.matrix_basis.copy()
        while o.parent is not None:
            m = o.parent.matrix_basis @ o.matrix_parent_inverse @ m; o = o.parent
        return m
    W = {o: wmat(o) for o in objs}
    meshes, dropped = [], []
    for o in objs:
        if o.type != 'MESH' or len(o.data.vertices) == 0: continue
        co = np.empty(len(o.data.vertices) * 3, dtype=np.float32); o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        a, b = co.min(0), co.max(0)
        cs = [W[o] @ Vector((x, y, z)) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        ext = [max(c[i] for c in cs) - min(c[i] for c in cs) for i in range(3)]
        flat = ext[2] < 0.03 and max(ext[0], ext[1]) > 1.0          # shadow planes, floors
        if max(ext) > 9 or flat or JUNK_KW.search(o.name) or o.hide_render:
            dropped.append(o.name); continue
        meshes.append((o, cs))
    if not meshes: return None
    if FIX.get(name, {}).get('skip'): return None
    keep = set(o for o, _ in meshes) | set(o for o in objs if o.type != 'MESH')
    c = make_collection('rc_' + name)
    for o in keep: c.objects.link(o)
    allc = [p for _, cs in meshes for p in cs]
    lo = Vector([min(p[i] for p in allc) for i in range(3)]); hi = Vector([max(p[i] for p in allc) for i in range(3)])
    # ground = bottom of the tyres (some models carry hidden helpers or plates below the wheels)
    WHEEL = re.compile(r'wheel|tire|tyre|rim|rubber', re.I)
    wz = [min(p.z for p in cs) for o, cs in meshes if WHEEL.search(o.name + ' ' + ' '.join(m.name for m in o.data.materials if m))]
    if wz: lo.z = sorted(wz)[len(wz) // 2]          # median of the wheels' lowest points
    dims = hi - lo; ctr = (lo + hi) / 2
    long_y = dims.y > dims.x
    def score(rx):
        acc = []
        for o, cs in meshes:
            names = o.name + ' ' + ' '.join(m.name for m in o.data.materials if m)
            if rx.search(names): acc.append(sum((p.y if long_y else p.x) for p in cs) / 8)
        return sum(acc) / len(acc) if acc else None
    f, r = score(FRONT_KW), score(REAR_KW)
    mid = ctr.y if long_y else ctr.x
    if f is not None and r is not None and abs(f - r) > 0.3: front_pos = f > r
    elif f is not None: front_pos = f > mid
    elif r is not None: front_pos = r < mid
    else: front_pos = not long_y
    fx = FIX.get(name, {})
    if fx.get('flip'): front_pos = not front_pos
    if long_y: yaw = -math.pi / 2 if front_pos else math.pi / 2
    else: yaw = 0.0 if front_pos else math.pi
    yaw += math.radians(fx.get('yaw', 0))
    L = max(dims.x, dims.y)
    sc = fx.get('scale', 1.0 if 3.0 < L < 7.5 else 4.7 / L)
    M = Matrix.Scale(sc, 4) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(Vector((-ctr.x, -ctr.y, -lo.z - fx.get('z', 0.0))))
    root = bpy.data.objects.new('root_' + name, None); c.objects.link(root); root.matrix_world = M
    for o in keep:
        if o.parent is None or o.parent not in keep:
            mw = W.get(o, o.matrix_basis).copy(); o.parent = root; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = mw
    print(f'[cars] {name}: wheels {len(wz)}, {L * sc:.2f} x {min(dims.x, dims.y) * sc:.2f} x {dims.z * sc:.2f} m, front {"+" if front_pos else "-"}{"Y" if long_y else "X"}'
          f'{" (fixed)" if fx else ""}, dropped {dropped[:4]}', flush=True)
    return c, L * sc
