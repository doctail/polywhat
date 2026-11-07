"""NYC Midtown street set from real OpenStreetMap data (5th Ave), PBR facades (ambientCG), Poly Haven
textures/HDRI/props, real OSM street trees, procedural cars & taxis, signals, street lights.
Executed by a scene script with a namespace `A` (tex, models, osm, pos, engine) already defined:
    G = dict(A=A); exec(compile(open(CITY).read(), CITY, 'exec'), G)
Afterwards G holds base (camera point on 5th Ave), d (direction south), n (east), FW, world nodes, materials...
"""
import sys, os, json, math, random, argparse
import bpy
from mathutils import Vector
from shapely.geometry import Polygon, LineString, MultiPolygon, Point, box
from shapely.ops import unary_union, linemerge, polygonize, nearest_points
from shapely.strtree import STRtree
import mapbox_earcut as earcut
import numpy as np

TEX = os.path.abspath(A.tex); MOD = os.path.abspath(A.models)
random.seed(7); np.random.seed(7)

scn = bpy.context.scene

# ================================================================ OSM -> local metres
els = json.load(open(A.osm))['elements']
lat0, lon0 = 40.7515, -73.9840
KX = math.cos(math.radians(lat0)) * 111320.0; KY = 110540.0
def P(pt): return ((pt['lon'] - lon0) * KX, (pt['lat'] - lat0) * KY)
AREA = box(-860, -800, 780, 820)

def fnum(s):
    try: return float(str(s).replace('m', '').split()[0].split(';')[0].replace(',', '.'))
    except Exception: return None

def heights(t):
    h = fnum(t.get('height')) or fnum(t.get('building:height'))
    if h is None and 'building:levels' in t:
        lv = fnum(t['building:levels']); h = lv * 3.6 + 2 if lv else None
    mh = fnum(t.get('min_height'))
    if mh is None and 'building:min_level' in t:
        ml = fnum(t['building:min_level']); mh = ml * 3.6 if ml else 0
    return h, (mh or 0.0)

def to_poly(e):
    if e['type'] == 'way' and 'geometry' in e:
        pts = [P(g) for g in e['geometry']]
        if len(pts) < 4: return None
        poly = Polygon(pts)
    elif e['type'] == 'relation':
        outs = [LineString([P(g) for g in m['geometry']]) for m in e.get('members', []) if m.get('role') == 'outer' and 'geometry' in m]
        ins = [LineString([P(g) for g in m['geometry']]) for m in e.get('members', []) if m.get('role') == 'inner' and 'geometry' in m]
        po = list(polygonize(linemerge(outs))) if outs else []
        if not po: return None
        poly = unary_union(po)
        pi = list(polygonize(linemerge(ins))) if ins else []
        if pi: poly = poly.difference(unary_union(pi))
    else: return None
    if not poly.is_valid: poly = poly.buffer(0)
    return None if poly.is_empty else poly

parts, outlines = [], []
for e in els:
    t = e.get('tags', {})
    if 'building:part' in t:
        pg = to_poly(e)
        if pg is not None: parts.append((pg, t))
    elif 'building' in t:
        pg = to_poly(e)
        if pg is not None and pg.area > 8 and pg.intersects(AREA): outlines.append((pg, t))
part_tree = STRtree([p for p, _ in parts]) if parts else None
buildings = []   # (polygon, h, min_h, tags, roof)
for pg, t in outlines:
    if part_tree is not None:
        idx = part_tree.query(pg)
        cov = sum(parts[i][0].intersection(pg).area for i in idx)
        if cov > 0.5 * pg.area: continue      # replaced by its parts
    h, mh = heights(t)
    if h is None: h = random.choice([14, 18, 22, 26, 30])
    for g in (pg.geoms if isinstance(pg, MultiPolygon) else [pg]):
        buildings.append((g, max(h, 4), mh, t, t.get('roof:shape', 'flat')))
for pg, t in parts:
    h, mh = heights(t)
    if h is None: continue
    for g in (pg.geoms if isinstance(pg, MultiPolygon) else [pg]):
        if g.area > 1: buildings.append((g, h, mh, t, t.get('roof:shape', 'flat')))

# roads
W_BY = {'primary': 15.0, 'secondary': 11.0, 'tertiary': 11.0, 'residential': 10.0, 'unclassified': 9.0, 'service': 6.0}
roads, avenues = [], []
for e in els:
    t = e.get('tags', {}); hw = t.get('highway')
    if e['type'] != 'way' or hw not in W_BY or 'geometry' not in e: continue
    if t.get('tunnel') == 'yes' or t.get('layer', '0').startswith('-'): continue
    ls = LineString([P(g) for g in e['geometry']])
    if not ls.intersects(AREA): continue
    name = t.get('name', ''); w = W_BY[hw]
    if 'Avenue' in name or 'Broadway' in name or 'Americas' in name: w = 17.5
    roads.append((ls, w, name, t))
    if w >= 17: avenues.append((ls, w, name, t))
road_poly = unary_union([ls.buffer(w / 2, cap_style=2, join_style=2) for ls, w, _, _ in roads])
road_poly = road_poly.buffer(-3).buffer(3).buffer(2.5).buffer(-2.5).intersection(AREA)
side_poly = AREA.difference(road_poly)
sigs = [P(e) for e in els if e['type'] == 'node' and e.get('tags', {}).get('highway') == 'traffic_signals']
trees = [P(e) for e in els if e['type'] == 'node' and e.get('tags', {}).get('natural') == 'tree']
print(f'buildings {len(buildings)} roads {len(roads)} signals {len(sigs)} trees {len(trees)}', flush=True)

# ================================================================ materials
def img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color: im.colorspace_settings.name = 'Non-Color'
    return im

def pbr(name, color, normal=None, rough=None, metal=None, scale=(1, 1), ao=None, tint_var=0.0,
        sat=1.0, val=1.0, normal_strength=1.0, coat=0.0, rough_add=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / scale[0], 1 / scale[1], 1)
    L.new(tc.outputs['UV'], mp.inputs['Vector'])
    oi = N.new('ShaderNodeObjectInfo')
    off = N.new('ShaderNodeVectorMath'); off.operation = 'MULTIPLY'; off.inputs[1].default_value = (7.31, 0.0, 0)
    L.new(oi.outputs['Random'], off.inputs[0])
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    L.new(mp.outputs['Vector'], add.inputs[0]); L.new(off.outputs['Vector'], add.inputs[1]); vec = add.outputs['Vector']
    def tex(path, nc):
        t = N.new('ShaderNodeTexImage'); t.image = img(path, nc); L.new(vec, t.inputs['Vector']); return t
    col_out = tex(color, False).outputs['Color']
    hsv = N.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat
    L.new(col_out, hsv.inputs['Color']); col_out = hsv.outputs['Color']
    mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = val * (1 - tint_var); mr.inputs['To Max'].default_value = val * (1 + tint_var)
    L.new(oi.outputs['Random'], mr.inputs['Value']); L.new(mr.outputs['Result'], hsv.inputs['Value'])
    if ao:
        a = tex(ao, True); mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        mx.inputs['Factor'].default_value = 0.8
        L.new(col_out, mx.inputs[6]); L.new(a.outputs['Color'], mx.inputs[7]); col_out = mx.outputs[2]
    L.new(col_out, bsdf.inputs['Base Color'])
    if rough:
        r = tex(rough, True); ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.use_clamp = True; ad.inputs[1].default_value = rough_add
        L.new(r.outputs['Color'], ad.inputs[0]); L.new(ad.outputs['Value'], bsdf.inputs['Roughness'])
    if metal: L.new(tex(metal, True).outputs['Color'], bsdf.inputs['Metallic'])
    if normal:
        n = tex(normal, True); nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_strength
        L.new(n.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if coat: bsdf.inputs['Coat Weight'].default_value = coat
    return m

def acg(aid, size, **kw):
    pre = os.path.join(TEX, aid, f'{aid}_2K-JPG_'); ex = lambda s: (pre + s) if os.path.exists(pre + s) else None
    return pbr(aid + str(size), pre + 'Color.jpg', normal=ex('NormalGL.jpg'), rough=ex('Roughness.jpg'), metal=ex('Metalness.jpg'),
               ao=ex('AmbientOcclusion.jpg'), scale=size, **kw)
def ph(aid, size, **kw):
    dd = os.path.join(TEX, aid)
    return pbr(aid, os.path.join(dd, 'diff.jpg'), normal=os.path.join(dd, 'nor.jpg'), rough=os.path.join(dd, 'rough.jpg'), scale=size, **kw)

FAC = {
    'brick_a': acg('Facade018A', (22, 22), tint_var=0.18),
    'stone_a': acg('Facade019A', (22, 22), tint_var=0.15),
    'brick_b': acg('Facade020A', (22, 22), tint_var=0.18),
    'glass_a': acg('Facade001', (32, 32), coat=0.3),
    'glass_b': acg('Facade005', (70, 70), coat=0.3),
    'grid_w':  acg('Facade006', (30, 30), tint_var=0.06),
    'grid_br': acg('Facade012', (100, 100), tint_var=0.12),
    'grid_dk': acg('Facade014', (100, 100), tint_var=0.12),
}
ESB_MAT = acg('Facade019A', (16, 16), tint_var=0.0, sat=0.5, val=1.25)
M_ROOF = ph('concrete_floor_01', (6, 6), tint_var=0.25, val=0.8)
M_ROAD = ph('road_damaged', (6, 6), sat=0.15, val=0.8)
M_SIDE = ph('concrete_pavement', (3.0, 3.0), sat=0.6, val=0.78)
M_CURB = ph('concrete_floor_01', (2, 2), val=0.7)
M_STORE = acg('Facade001', (5, 5), coat=0.5, val=0.85)

def plain(name, rgb, rough=0.5, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.new(name); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = (*rgb, 1); b.inputs['Emission Strength'].default_value = emit
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.03
    return m
M_PAINT = plain('lane_paint', (0.8, 0.8, 0.76), rough=0.7)
M_POLE = plain('pole', (0.03, 0.04, 0.035), rough=0.4, metal=0.7)
M_SIGPOLE = plain('sigpole', (0.05, 0.05, 0.05), rough=0.45, metal=0.6)
M_SIGHEAD = plain('sighead', (0.45, 0.33, 0.04), rough=0.5)
M_RED = plain('red', (1.0, 0.05, 0.02), emit=6); M_GRN = plain('grn', (0.1, 1.0, 0.6), emit=6)
M_TIRE = plain('tire', (0.02, 0.02, 0.02), rough=0.8)
M_RIM = plain('rim', (0.5, 0.5, 0.52), rough=0.25, metal=1.0)
M_CARGLASS = plain('carglass', (0.01, 0.012, 0.015), rough=0.03, coat=1.0)
M_HEAD = plain('head', (1.0, 0.95, 0.85), emit=2); M_TAIL = plain('tail', (0.8, 0.02, 0.01), emit=2)
M_TRIM = plain('trim', (0.02, 0.02, 0.02), rough=0.3)
TAXI = (0.95, 0.62, 0.02)
PAINTS = [(TAXI, 'taxi')] * 4 + [((0.02, 0.02, 0.02), 'k'), ((0.6, 0.6, 0.62), 's'), ((0.85, 0.85, 0.85), 'w'),
          ((0.05, 0.08, 0.2), 'b'), ((0.25, 0.25, 0.27), 'g'), ((0.35, 0.02, 0.02), 'r')]

def pick_facade(h):
    if h > 150: return random.choice(['glass_b', 'grid_w', 'stone_a', 'glass_a'])
    if h > 60: return random.choice(['stone_a', 'grid_w', 'stone_a', 'brick_b', 'brick_a'])
    return random.choice(['brick_a', 'brick_b', 'stone_a', 'brick_a', 'stone_a'])

# ================================================================ mesh helpers
def mesh_obj(name, verts, faces, uvs, mats, face_mat, coll=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name='UVMap'); flat_uv = [c for f in uvs for uv in f for c in uv]
    uvl.data.foreach_set('uv', flat_uv)
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', face_mat)
    ob = bpy.data.objects.new(name, me); (coll or scn.collection).objects.link(ob)
    return ob

def tri_polygon(pg):
    rings = [list(pg.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in pg.interiors]
    verts = [p for r in rings for p in r]
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    return verts, earcut.triangulate_float64(np.array(verts, dtype=np.float64), ends).reshape(-1, 3)

def ring_dir(coords, ccw=True):
    ls = list(coords)[:-1]
    a = sum(ls[i][0] * ls[(i + 1) % len(ls)][1] - ls[(i + 1) % len(ls)][0] * ls[i][1] for i in range(len(ls)))
    return ls if (a > 0) == ccw else ls[::-1]

STORE_H = 4.5
city = bpy.data.collections.new('city'); scn.collection.children.link(city)
BV, BF, BU, BM = [], [], [], []
MATS = list(FAC.values()) + [M_STORE, M_ROOF, ESB_MAT]
MI = {id(m): i for i, m in enumerate(MATS)}
def building(pg, h, mh, mat, roof):
    def quad(a, b, z0, z1, u0, u1, ta, tb, mi):
        k = len(BV); BV.extend([(a[0], a[1], z0), (b[0], b[1], z0), (tb[0], tb[1], z1), (ta[0], ta[1], z1)])
        BF.append((k, k + 1, k + 2, k + 3)); BU.append([(u0, z0), (u1, z0), (u1, z1), (u0, z1)]); BM.append(mi)
    c = np.array(pg.centroid.coords[0])
    taper = 0.25 if roof == 'pyramidal' and pg.area < 2000 else 1.0
    T = lambda p: tuple(c + (np.array(p) - c) * taper)
    rings = [ring_dir(pg.exterior.coords, True)] + [ring_dir(r.coords, False) for r in pg.interiors]
    for r in rings:
        u = 0.0
        for i in range(len(r)):
            a, b = r[i], r[(i + 1) % len(r)]; L = math.dist(a, b)
            if L < 1e-3: continue
            if mh < 0.5 and h > STORE_H + 3 and taper == 1:
                quad(a, b, 0, STORE_H, u, u + L, a, b, MI[id(M_STORE)])
                quad(a, b, STORE_H, h, u, u + L, a, b, MI[id(mat)])
            else:
                quad(a, b, mh, h, u, u + L, T(a), T(b), MI[id(mat)])
            u += L
    if taper != 1: pg = Polygon([T(p) for p in pg.exterior.coords])
    tv, tris = tri_polygon(pg); base0 = len(BV)
    BV.extend([(x, y, h) for x, y in tv])
    for t in tris:
        BF.append((base0 + int(t[0]), base0 + int(t[1]), base0 + int(t[2]))); BU.append([(tv[int(k)][0], tv[int(k)][1]) for k in t]); BM.append(MI[id(M_ROOF)])

def flush_building_obj(name):
    global BV, BF, BU, BM
    if not BF: return
    ob = mesh_obj(name, BV, BF, BU, MATS, BM, city)
    for p in ob.data.polygons:
        if p.material_index == MI[id(M_ROOF)] and p.normal.z < 0: p.flip()
    BV, BF, BU, BM = [], [], [], []

def flat(geom, z, mat, name, walls_mat=None, wall_h=0.0):
    geoms = geom.geoms if hasattr(geom, 'geoms') else [geom]
    V, F, U, M = [], [], [], []
    for pg in geoms:
        if pg.geom_type != 'Polygon' or pg.area < 0.5: continue
        tv, tris = tri_polygon(pg); b0 = len(V)
        V.extend([(x, y, z) for x, y in tv])
        for t in tris:
            F.append((b0 + int(t[0]), b0 + int(t[1]), b0 + int(t[2]))); U.append([(tv[int(k)][0], tv[int(k)][1]) for k in t]); M.append(0)
        if walls_mat is not None:
            for r in [ring_dir(pg.exterior.coords, True)] + [ring_dir(x.coords, False) for x in pg.interiors]:
                u = 0
                for i in range(len(r)):
                    a, b = r[i], r[(i + 1) % len(r)]; L = math.dist(a, b); k = len(V)
                    V.extend([(a[0], a[1], z - wall_h), (b[0], b[1], z - wall_h), (b[0], b[1], z), (a[0], a[1], z)])
                    F.append((k, k + 1, k + 2, k + 3)); U.append([(u, 0), (u + L, 0), (u + L, wall_h), (u, wall_h)]); M.append(1); u += L
    ob = mesh_obj(name, V, F, U, [mat] + ([walls_mat] if walls_mat else []), M)
    for p in ob.data.polygons:
        if p.material_index == 0 and p.normal.z < 0: p.flip()
    return ob

# ================================================================ camera rig
fifth = [x for x in avenues if x[2] == '5th Avenue']
fl = linemerge([x[0] for x in fifth]); fl = fl if fl.geom_type == 'LineString' else max(fl.geoms, key=lambda g: g.length)
FW = 17.5
base = np.array(fl.interpolate(A.pos).coords[0]); ahead = np.array(fl.interpolate(A.pos + 5).coords[0])
d = (ahead - base) / np.linalg.norm(ahead - base)      # southwards (direction of traffic)
n = np.array([-d[1], d[0]])                             # left when facing south = east
CAM0 = base

# ================================================================ build city
esb_zone = Point(-211, -333).buffer(70)
for i, (pg, h, mh, t, roof) in enumerate(buildings):
    is_esb = pg.intersects(esb_zone) and (h > 100 or 'building:part' in t)
    mat = ESB_MAT if is_esb else FAC[pick_facade(h)]
    building(pg, h, mh, mat, roof)
    if np.linalg.norm(np.array(pg.centroid.coords[0]) - CAM0) < 260: flush_building_obj(f'b{i}')
    elif len(BF) > 20000: flush_building_obj(f'bm{i}')
flush_building_obj('bm_last')
flat(road_poly, 0.0, M_ROAD, 'road')
flat(side_poly, 0.15, M_SIDE, 'sidewalk', walls_mat=M_CURB, wall_h=0.15)
bpy.ops.mesh.primitive_plane_add(size=8000, location=(0, 0, -0.03)); bpy.context.object.data.materials.append(M_ROOF)

# ---------------- lane markings + crosswalks
PV, PF, PU, PM = [], [], [], []
def strip(p0, p1, wdt):
    p0 = np.array(p0); p1 = np.array(p1); dd = p1 - p0; L = np.linalg.norm(dd)
    if L < 1e-3: return
    nn = np.array([-dd[1], dd[0]]) / L * wdt / 2; k = len(PV)
    for q in (p0 - nn, p1 - nn, p1 + nn, p0 + nn): PV.append((q[0], q[1], 0.012))
    PF.append((k, k + 1, k + 2, k + 3)); PU.append([(0, 0), (1, 0), (1, 1), (0, 1)]); PM.append(0)
inter_pts = []
for als, aw, an, _ in avenues:
    lanes = 5
    for k in range(1, lanes):
        try: ol = als.offset_curve(-aw / 2 + k * aw / lanes)
        except Exception: continue
        if ol.is_empty or ol.geom_type != 'LineString': continue
        for s in np.arange(0, ol.length - 3, 12.0): strip(ol.interpolate(s).coords[0], ol.interpolate(s + 3.0).coords[0], 0.13)
street_lines = [(ls, w) for ls, w, nm, _ in roads if w < 17]
for als, aw, an, _ in avenues:
    for sls, sw in street_lines:
        ip = als.intersection(sls)
        if ip.is_empty or ip.geom_type != 'Point': continue
        inter_pts.append((np.array(ip.coords[0]), aw, sw))
        s = sls.project(ip); a = np.array(sls.interpolate(max(s - 1, 0)).coords[0]); b = np.array(sls.interpolate(min(s + 1, sls.length)).coords[0])
        dv = (b - a) / (np.linalg.norm(b - a) + 1e-9); nv = np.array([-dv[1], dv[0]])
        for sign in (-1, 1):
            c = np.array(ip.coords[0]) + dv * sign * (aw / 2 + 2.6)
            for k in np.arange(-sw / 2 + 0.6, sw / 2 - 0.3, 1.2): strip(tuple(c + nv * k - dv * 1.7), tuple(c + nv * k + dv * 1.7), 0.6)
        av_s = als.project(ip); a2 = np.array(als.interpolate(max(av_s - 1, 0)).coords[0]); b2 = np.array(als.interpolate(av_s + 1).coords[0])
        da = (b2 - a2) / (np.linalg.norm(b2 - a2) + 1e-9); na = np.array([-da[1], da[0]])
        for sign in (-1, 1):
            c = np.array(ip.coords[0]) + da * sign * (sw / 2 + 2.6)
            for k in np.arange(-aw / 2 + 0.6, aw / 2 - 0.3, 1.2): strip(tuple(c + na * k - da * 1.7), tuple(c + na * k + da * 1.7), 0.6)
mesh_obj('paint', PV, PF, PU, [M_PAINT], PM)

# ================================================================ asset library (hidden, instanced)
lib = bpy.data.collections.new('lib'); scn.collection.children.link(lib)
bpy.context.view_layer.layer_collection.children['lib'].exclude = True
def asset_collection(name):
    c = bpy.data.collections.new(name); lib.children.link(c); return c
def instance(coll, loc, rot=0.0, scale=1.0):
    o = bpy.data.objects.new('i_' + coll.name, None); o.instance_type = 'COLLECTION'; o.instance_collection = coll
    o.location = loc; o.rotation_euler = (0, 0, rot); o.scale = (scale,) * 3; scn.collection.objects.link(o); return o

def import_gltf(name, path):
    c = asset_collection(name)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for uc in list(o.users_collection): uc.objects.unlink(o)
        c.objects.link(o)
    zs = [(o.matrix_world @ Vector(v)).z for o in new if o.type == 'MESH' for v in o.bound_box]
    xs = [(o.matrix_world @ Vector(v)).x for o in new if o.type == 'MESH' for v in o.bound_box]
    print(name, 'height', max(zs) - min(zs), 'width', max(xs) - min(xs), 'zmin', min(zs), flush=True)
    return c, max(zs) - min(zs)

TREE, tree_h = import_gltf('tree', os.path.join(MOD, 'island_tree_02', 'island_tree_02.gltf'))
HYD, _ = import_gltf('hydrant', os.path.join(MOD, 'fire_hydrant', 'fire_hydrant.gltf'))
CAN, _ = import_gltf('trash', os.path.join(MOD, 'metal_trash_can', 'metal_trash_can.gltf'))

# ---------------- procedural cars
def _own(o, coll):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    coll.objects.link(o); return o
def cube(coll, loc, size, mat, bevel=0.0, taper=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    for v in o.data.vertices:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        if taper is not None and v.co.z > 0: v.co.x *= taper[0]; v.co.y *= taper[1]
    if bevel:
        m = o.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = 3
    o.data.materials.append(mat); return _own(o, coll)
def cyl(coll, loc, r, depth, mat, rot):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return _own(o, coll)

def make_car(name, paint, kind='sedan'):
    c = asset_collection(name)
    body = plain('paint_' + name, paint, rough=0.35, coat=1.0)
    if kind == 'suv': Lb, Wb, Hb, Hc, cab_len, cab_off, cab_tap = 4.9, 1.95, 0.95, 0.75, 3.0, -0.2, (0.9, 0.9)
    elif kind == 'van': Lb, Wb, Hb, Hc, cab_len, cab_off, cab_tap = 5.6, 2.0, 1.2, 0.95, 4.4, -0.35, (0.96, 0.95)
    else: Lb, Wb, Hb, Hc, cab_len, cab_off, cab_tap = 4.7, 1.83, 0.72, 0.58, 2.4, -0.25, (0.72, 0.86)
    zc = 0.32
    cube(c, (0, 0, zc + Hb / 2), (Lb, Wb, Hb), body, bevel=0.14)
    cube(c, (cab_off, 0, zc + Hb + Hc / 2 - 0.02), (cab_len, Wb * 0.9, Hc), M_CARGLASS, bevel=0.1, taper=cab_tap)
    cube(c, (cab_off, 0, zc + Hb + Hc - 0.03), (cab_len * cab_tap[0] * 0.92, Wb * 0.9 * cab_tap[1] * 0.97, 0.06), body, bevel=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = sx * (Lb / 2 - 0.85); y = sy * (Wb / 2 - 0.12)
            cyl(c, (x, y, 0.34), 0.34, 0.24, M_TIRE, (math.pi / 2, 0, 0))
            cyl(c, (x, y + sy * 0.125, 0.34), 0.22, 0.01, M_RIM, (math.pi / 2, 0, 0))
    for sy in (-1, 1):
        cube(c, (Lb / 2 - 0.02, sy * (Wb / 2 - 0.3), zc + Hb * 0.68), (0.06, 0.4, 0.14), M_HEAD)
        cube(c, (-Lb / 2 + 0.02, sy * (Wb / 2 - 0.25), zc + Hb * 0.72), (0.06, 0.35, 0.12), M_TAIL)
    cube(c, (0, 0, zc + 0.12), (Lb + 0.02, Wb + 0.02, 0.16), M_TRIM, bevel=0.05)
    if paint == TAXI and kind == 'sedan':
        cube(c, (cab_off, 0, zc + Hb + Hc + 0.1), (0.9, 0.28, 0.25), plain('taxisign', (1, 0.95, 0.85), emit=1.5), bevel=0.03)
    return c, Lb
CARS = []
for i, (p, tag) in enumerate(PAINTS):
    kind = 'sedan' if tag == 'taxi' else random.choice(['sedan', 'sedan', 'suv', 'suv', 'van'])
    CARS.append(make_car(f'car{i}', p, kind))

def drop_cars(line, width, one_way_dir, lanes, density, max_dist=700, skip_lane=None):
    if line.length < 10: return
    for k in range(lanes):
        if skip_lane is not None and k == skip_lane: continue
        off = -width / 2 + (k + 0.5) * width / lanes
        try: ol = line.offset_curve(off)
        except Exception: continue
        if ol.is_empty or ol.geom_type != 'LineString': continue
        s = random.uniform(0, 15)
        while s < ol.length - 3:
            p = np.array(ol.interpolate(s).coords[0]); q = np.array(ol.interpolate(min(s + 1, ol.length)).coords[0])
            if np.linalg.norm(p - CAM0) < max_dist and not any(np.linalg.norm(p - ip) < aw / 2 + 4 for ip, aw, sw in inter_pts):
                coll, Lc = random.choice(CARS)
                dd = (q - p) * one_way_dir
                instance(coll, (p[0], p[1], 0), math.atan2(dd[1], dd[0]) + random.uniform(-0.02, 0.02))
                s += Lc + (random.uniform(1.2, 3.0) if random.random() < density else random.uniform(8, 40))
            else: s += 6
for als, aw, an, t in avenues:
    q0 = np.array(als.coords[0]); q1 = np.array(als.coords[-1]); ldir = (q1 - q0) / (np.linalg.norm(q1 - q0) + 1e-9)
    sgn = 1 if np.dot(ldir, d) > 0 else -1
    # leave the lane where camera C stands empty in front of it
    drop_cars(als, aw - 3, sgn, 4, 0.55, skip_lane=None)
for sls, sw in street_lines:
    if sw >= 10: drop_cars(sls, sw - 2.5, random.choice([1, -1]), 1, 0.4, max_dist=350)
# clear cars that would sit on top of camera positions
for o in [o for o in scn.collection.objects if o.name.startswith('i_car')]:
    p = np.array(o.location[:2])
    if np.linalg.norm(p - (base - n * 1.5)) < 7 or np.linalg.norm(p - (base - n * 1.5 + d * 6)) < 7: bpy.data.objects.remove(o)

# ---------------- street furniture
side_edge = side_poly.boundary
def curb_point(p, inset=0.7):
    q = nearest_points(side_edge, Point(p))[0]; qa = np.array(q.coords[0])
    inside = side_poly.contains(Point(p))
    v = (np.array(p) - qa) if inside else (qa - np.array(p))
    L = np.linalg.norm(v); v = v / L if L > 1e-6 else np.array([1.0, 0.0])
    return qa + v * inset, v
# signal + street-light assets (built once, instanced: bpy.ops in a big scene is very slow)
def make_signal(name, lit):
    c = asset_collection(name)
    cyl(c, (0, 0, 3.0), 0.11, 6.0, M_SIGPOLE, (0, 0, 0))
    cyl(c, (3.0, 0, 5.7), 0.07, 6.0, M_SIGPOLE, (0, math.pi / 2, 0))
    cube(c, (5.6, 0, 5.0), (0.32, 0.32, 1.0), M_SIGHEAD)
    cube(c, (5.6, 0, 5.75), (0.06, 0.06, 0.5), M_SIGPOLE)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(5.6 - 0.17, 0, 4.7 if lit is M_GRN else 5.3))
    o = bpy.context.object; o.data.materials.append(lit); _own(o, c)
    return c
SIG = [make_signal('sig_g', M_GRN), make_signal('sig_r', M_RED)]
def make_lamp():
    c = asset_collection('streetlamp')
    cyl(c, (0, 0, 4.5), 0.1, 9.0, M_POLE, (0, 0, 0))
    cyl(c, (1.5, 0, 9.0), 0.05, 3.0, M_POLE, (0, math.pi / 2, 0))
    cube(c, (2.9, 0, 8.95), (0.75, 0.32, 0.14), M_POLE, bevel=0.04)
    return c
LAMP = make_lamp()
for ip, aw, sw in inter_pts:
    if np.linalg.norm(ip - CAM0) > 700: continue
    for corner in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        guess = ip + np.array(corner) * (aw / 2 + 1.5)
        cp, v = curb_point(guess, 0.8)
        to_c = (ip - cp); to_c /= np.linalg.norm(to_c)
        instance(random.choice(SIG), (cp[0], cp[1], 0.15), math.atan2(to_c[1], to_c[0]))
road_edge = road_poly.boundary
for als, aw, an, _ in avenues:
    for side in (-1, 1):
        try: ol = als.offset_curve(side * (aw / 2 + 0.6))
        except Exception: continue
        if ol.is_empty or ol.geom_type != 'LineString': continue
        for s in np.arange(15, ol.length, 36.0):
            p = np.array(ol.interpolate(s).coords[0])
            if np.linalg.norm(p - CAM0) > 600 or not side_poly.contains(Point(p)): continue
            q = np.array(ol.interpolate(min(s + 1, ol.length)).coords[0]); dd = (q - p) / (np.linalg.norm(q - p) + 1e-9)
            to_road = np.array(nearest_points(road_edge, Point(p))[0].coords[0]) - p
            nn = to_road / (np.linalg.norm(to_road) + 1e-9)
            instance(LAMP, (p[0], p[1], 0.15), math.atan2(nn[1], nn[0]))
            if random.random() < 0.35:
                hp2, _ = curb_point(p + dd * 4, 0.5); instance(HYD, (hp2[0], hp2[1], 0.15), random.uniform(0, 6.28), 1.0)
            if random.random() < 0.5:
                tp, _ = curb_point(p - dd * 5, 0.6); instance(CAN, (tp[0], tp[1], 0.15), random.uniform(0, 6.28), 1.0)
TS = 11.0 / max(tree_h, 0.1)
for tp in trees:
    tp = np.array(tp)
    if np.linalg.norm(tp - CAM0) > 650: continue
    instance(TREE, (tp[0], tp[1], 0.15), random.uniform(0, 6.28), TS * random.uniform(0.75, 1.15))

# ================================================================ world / sky
world = bpy.data.worlds.new('W'); scn.world = world
wn = world.node_tree.nodes; wl = world.node_tree.links
env = wn.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(TEX, 'sky.hdr'))
wm = wn.new('ShaderNodeMapping'); wtc = wn.new('ShaderNodeTexCoord')
im = env.image; W, H = im.size
px = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)[:, :, :3].sum(axis=2)
yy, xx = np.unravel_index(np.argmax(px), px.shape)
sun_u = (xx + 0.5) / W; sun_el = ((yy + 0.5) / H - 0.5) * math.pi
# Blender equirect lookup: u = atan2(dir.y, -dir.x)/(2pi) + 0.5  ->  azimuth of texel u: atan2(sin(a), -cos(a)), a=(u-0.5)*2pi
a_tex = (sun_u - 0.5) * 2 * math.pi
src_az = math.atan2(math.sin(a_tex), -math.cos(a_tex))
want_az = math.atan2(d[1], d[0]) + math.radians(150)      # sun behind-left of the southward camera
SKY_ROT = want_az - src_az
wm.inputs['Rotation'].default_value = (0, 0, SKY_ROT)
wl.new(wtc.outputs['Generated'], wm.inputs['Vector']); wl.new(wm.outputs['Vector'], env.inputs['Vector'])
wl.new(env.outputs['Color'], wn['Background'].inputs['Color']); wn['Background'].inputs['Strength'].default_value = 1.3
print('sun elevation', math.degrees(sun_el), flush=True)
if A.engine == 'eevee':
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(0.6)
    so = bpy.data.objects.new('sun', sd); scn.collection.objects.link(so)
    sdir = Vector((math.cos(want_az) * math.cos(sun_el), math.sin(want_az) * math.cos(sun_el), math.sin(sun_el)))
    so.rotation_euler = (-sdir).to_track_quat('-Z', 'Y').to_euler()

