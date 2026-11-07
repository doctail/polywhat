"""Blender scenes for 'What Every Asteroid Size Looks Like Hitting Your City' — one act per Blender process.
   blender -b -P scene.py -- --act NAME --out DIR [--res 1920x1080] [--engine eevee] [--samples N] [--times 2,11]
Frames are written with GLOBAL numbering so all acts share one folder.
You stand on the same sidewalk for every impact; the impact point is straight down the road (design -z)."""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import timeline as TL
from pw3d import *  # noqa

get = args(sys.argv)
ACT = get("--act", "intro"); OUT = get("--out", "/tmp/asteroid_raw"); RES = get("--res", "1920x1080")
ENGINE = get("--engine", "eevee"); SAMPLES = int(get("--samples", "24")); DEVICE = get("--device", "gpu")
TIMES = get("--times"); FRAMES = get("--frames")
FPS = TL.FPS; E = TL.EVENTS
A0, A1 = [(a, b) for n, a, b in TL.ACTS if n == ACT][0]
F0, F1 = int(round(A0 * FPS)) + 1, int(round(A1 * FPS))
scene = reset(); scene.view_settings.exposure = 0.2
rnd = random.Random(hash(ACT) % 1000)

def fr(t): return int(round(t * FPS)) + 1
def keyat(ob, path, value, t):
    setattr(ob, path, value); ob.keyframe_insert(path, frame=fr(t))

# ----------------------------------------------------------------------- kit (shared with 'lighter')
def street(rows=16, start_z=-6.0, spacing=11.0, with_poles=True):
    """road along -z; houses, trees, poles on both sides. Returns (trees, poles) as lists of (group, base_pos)."""
    gp = bpy.data.meshes.new("ground"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=800); bm.to_mesh(gp); bm.free()
    go = link(bpy.data.objects.new("ground", gp)); go.data.materials.append(mat(0x79a552, 0.95)); go.location = (0, 300, 0)
    stat = [box("road", 7, 0.02, 800, 0x4a4c52, (0, 0.01, -300))]
    for i in range(160): stat.append(box(f"dash{i}", 0.15, 0.022, 1.6, 0xf0d060, (0, 0.012, 20 - i * 5)))
    for side in (-1, 1): stat.append(box(f"walk{side}", 2.0, 0.08, 800, 0xb8b4ac, (side * 4.6, 0.04, -300)))
    trees, poles = [], []
    for i in range(rows):
        for side in (-1, 1):
            z = start_z - i * spacing + rnd.uniform(-1, 1); x = side * rnd.uniform(9, 12); w, d, h = rnd.uniform(6, 8), rnd.uniform(6, 8), rnd.uniform(3.5, 6.5)
            wall_c = [0xe8dccb, 0xd9c7b0, 0xc9d4dc, 0xf0e2c8][(i + side) % 4]; roof_c = [0xa04a38, 0x5a6470, 0x8a5a3a][i % 3]
            stat.append(box(f"walls{i}{side}", w, h, d, wall_c, (x, h / 2, z)))
            for k in range(3): stat.append(box(f"win{i}{side}{k}", 0.05, 1.0, 1.0, 0x6a90b0, (x - side * (w / 2 + 0.02), h * 0.55, z - d / 3 + k * d / 3), rough=0.2))
            stat.append(box(f"door{i}{side}", 0.05, 2.0, 1.0, 0x6e4a30, (x - side * (w / 2 + 0.02), 1.0, z + d / 2 - 1.0)))
            rm = bpy.data.meshes.new("roof"); bm = bmesh.new()
            vs = [bm.verts.new(v) for v in ((-w / 2 - .3, -d / 2 - .3, 0), (w / 2 + .3, -d / 2 - .3, 0), (w / 2 + .3, d / 2 + .3, 0), (-w / 2 - .3, d / 2 + .3, 0), (0, -d / 2 - .3, 2.2), (0, d / 2 + .3, 2.2))]
            for fc in ((0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)): bm.faces.new([vs[k] for k in fc])
            bm.to_mesh(rm); bm.free(); ro = link(bpy.data.objects.new("roof", rm)); ro.data.materials.append(mat(roof_c, 0.8)); ro.location = B(x, h, z); stat.append(ro)
            for k in range(2):
                tx, tz, th = side * rnd.uniform(6, 7.5), z + rnd.uniform(-5, 5), rnd.uniform(2.5, 4.5)
                tg = empty(f"tree{i}{side}{k}", (tx, 0, tz))
                box("trunk", 0.3, th, 0.3, 0x5a4030, (0, th / 2, 0), parent=tg)
                ico("crown", rnd.uniform(1.1, 1.8), [0x4f8a3c, 0x5a9440, 0x447a34][k], (0, 0, 0), parent=tg).location = (0, 0, th + 0.8)
                trees.append((tg, rnd.random() * 6))
        if with_poles and i % 2 == 0:
            pz = start_z + 6 - i * spacing
            pg = empty(f"pole{i}", (5.8, 0, pz)); box("pole", 0.18, 7, 0.18, 0x6a5a4a, (0, 3.5, 0), parent=pg); box("arm", 1.6, 0.12, 0.12, 0x6a5a4a, (0, 6.6, 0), parent=pg)
            poles.append(pz)
    for i in range(len(poles) - 1):   # sagging wires
        a, b = poles[i], poles[i + 1]
        for k in range(6):
            z0, z1 = a + (b - a) * k / 6, a + (b - a) * (k + 1) / 6
            y0, y1 = 6.6 - 0.6 * math.sin(math.pi * k / 6), 6.6 - 0.6 * math.sin(math.pi * (k + 1) / 6)
            for wx in (5.2, 6.4): stat.append(limb(f"wire{i}{k}{wx}", B(wx, y0, z0), B(wx, y1, z1), 0.015, 0.015, 0x222222))
    return stat, trees, poles

def leaves(n, color_set=(0xc98a2e, 0xa8552a, 0x8aa03c, 0xd9b44a, 0xf2f2ea)):
    out = []
    for i in range(n):
        big = i % 7 == 0
        o = box(f"leaf{i}", rnd.uniform(0.14, 0.26) * (2.2 if big else 1), 0.01, rnd.uniform(0.1, 0.2) * (2.6 if big else 1), 0xf4f4ee if big else color_set[i % len(color_set)], (0, -50, 0))
        out.append(dict(o=o, x=rnd.uniform(-5, 8), y=rnd.uniform(0.2, 4.5), z=rnd.uniform(-60, 20), ph=rnd.random() * 6, sp=rnd.uniform(0.7, 1.3)))
    return out

def sky_world(sun_dir):
    """keyable sky: base colour, horizon glow band (dips with altitude), sun glow, stars.
    returns dict of node sockets to keyframe: sky (rgb), dip, glow, sunglow, stars."""
    w = bpy.data.worlds.new("sky"); scene.world = w; w.use_nodes = True; nt = w.node_tree; N, Lk = nt.nodes, nt.links
    bg = N["Background"]; bg.inputs[1].default_value = 1.0
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Generated"], sep.inputs[0])
    def val(v): n = N.new("ShaderNodeValue"); n.outputs[0].default_value = v; return n
    def m(op, a, b=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: Lk.new(x, n.inputs[i])
        return n.outputs[0]
    dip, glow, sung, stars = val(0.0), val(1.0), val(0.6), val(0.0)
    # horizon band: exp(-((z + dip) / 0.09)^2)
    zz = m('DIVIDE', m('ADD', sep.outputs["Z"], dip.outputs[0]), 0.09); band = m('EXPONENT', m('MULTIPLY', m('MULTIPLY', zz, zz), -1.0))
    band = m('MULTIPLY', band, glow.outputs[0])
    # sun glow: exp(-(1 - dot(D, S)) * 60) + wide halo
    dot = N.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'; Lk.new(tc.outputs["Generated"], dot.inputs[0]); dot.inputs[1].default_value = tuple(sun_dir)
    one_m = m('SUBTRACT', 1.0, dot.outputs["Value"])
    sg = m('ADD', m('MULTIPLY', m('EXPONENT', m('MULTIPLY', one_m, -400.0)), 30.0), m('MULTIPLY', m('EXPONENT', m('MULTIPLY', one_m, -40.0)), 0.12))
    sg = m('MULTIPLY', sg, sung.outputs[0])
    # stars: thresholded voronoi, only above the horizon
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 380.0; Lk.new(tc.outputs["Generated"], vor.inputs["Vector"])
    st = m('MULTIPLY', m('LESS_THAN', vor.outputs["Distance"], 0.03), stars.outputs[0])
    st = m('MULTIPLY', st, m('GREATER_THAN', m('ADD', sep.outputs["Z"], dip.outputs[0]), 0.0))
    sky = N.new("ShaderNodeRGB"); sky.outputs[0].default_value = (0.42, 0.62, 0.92, 1)
    hcol = N.new("ShaderNodeRGB"); hcol.outputs[0].default_value = (0.55, 0.75, 1.0, 1)
    scol = N.new("ShaderNodeRGB"); scol.outputs[0].default_value = (1.0, 0.9, 0.7, 1)
    def add_col(a, b_col, fac):
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'ADD'; mx.clamp_result = False
        Lk.new(fac, mx.inputs[0]); Lk.new(a, mx.inputs[6]); Lk.new(b_col, mx.inputs[7]); return mx.outputs[2]
    c = add_col(sky.outputs[0], hcol.outputs[0], band)
    c = add_col(c, scol.outputs[0], sg)
    white = N.new("ShaderNodeRGB"); white.outputs[0].default_value = (1, 1, 1, 1)
    c = add_col(c, white.outputs[0], st)
    Lk.new(c, bg.inputs[0])
    return dict(sky=sky.outputs[0], dip=dip.outputs[0], glow=glow.outputs[0], sunglow=sung.outputs[0], stars=stars.outputs[0], hcol=hcol.outputs[0])

def kv(sock, v, f):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)

def rim_mat(hexcol, strength, power=4.0):
    """glow only at the silhouette edge (atmosphere / halo): emission * (1 - facing)^power over transparent."""
    m = bpy.data.materials.new("rim"); m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); lw = N.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.5
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = power
    em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = rgb(hexcol); em.inputs[1].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    Lk.new(lw.outputs["Facing"], pw.inputs[0]); Lk.new(pw.outputs[0], mx.inputs[0]); Lk.new(tr.outputs[0], mx.inputs[1]); Lk.new(em.outputs[0], mx.inputs[2]); Lk.new(mx.outputs[0], out.inputs[0])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m


# ======================================================================= the town (dynamic near houses)
CAM_P = Vector((1.4, 1.62, 3.0))
IMPACT_DIR = Vector((-0.12, 0.0, -1.0)).normalized()          # straight-ish down the road

class Town:
    """houses with separate windows / roof / walls, trees and poles as groups, plus a car. Built for destruction."""
    def __init__(self, rows=9, parked_car=True):
        gp = bpy.data.meshes.new("ground"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60000); bm.to_mesh(gp); bm.free()
        go = link(bpy.data.objects.new("ground", gp)); go.data.materials.append(mat(0x6f9a4a, 0.95))
        stat = [box("road", 7, 0.02, 3000, 0x4a4c52, (0, 0.01, -1400))]
        for i in range(400): stat.append(box(f"dash{i}", 0.15, 0.022, 1.6, 0xf0d060, (0, 0.012, 20 - i * 5)))
        for side in (-1, 1): stat.append(box(f"walk{side}", 2.0, 0.08, 3000, 0xb8b4ac, (side * 4.6, 0.04, -1400)))
        self.houses, self.trees, self.poles = [], [], []
        rr = random.Random(3)
        for i in range(rows + 22):
            for side in (-1, 1):
                z = 8 - i * 11 + rr.uniform(-1, 1); x = side * rr.uniform(9, 12); w, d, h = rr.uniform(6, 8), rr.uniform(6, 8), rr.uniform(3.5, 6.5)
                wall_c = [0xe8dccb, 0xd9c7b0, 0xc9d4dc, 0xf0e2c8][(i + side) % 4]; roof_c = [0xa04a38, 0x5a6470, 0x8a5a3a][i % 3]
                if i < rows:
                    g = empty(f"house{i}{side}", (x, 0, z)); walls = empty("walls", (0, 0, 0)); walls.parent = g; walls.location = (0, 0, 0)
                    box("w", w, h, d, wall_c, (0, h / 2, 0), parent=walls)
                    wins = []
                    for k in range(3):
                        wo = box("win", 0.05, 1.1, 1.2, 0x8fb4d0, (-side * (w / 2 + 0.03), h * 0.55, -d / 3 + k * d / 3), parent=g, rough=0.08)
                        wins.append(wo)
                    box("door", 0.05, 2.0, 1.0, 0x6e4a30, (-side * (w / 2 + 0.03), 1.0, d / 2 - 1.0), parent=walls)
                    roof = empty("roofp", (0, 0, 0)); roof.parent = g; roof.location = (0, 0, h)
                    rm = bpy.data.meshes.new("roof"); bm = bmesh.new()
                    vs = [bm.verts.new(v) for v in ((-w / 2 - .3, -d / 2 - .3, 0), (w / 2 + .3, -d / 2 - .3, 0), (w / 2 + .3, d / 2 + .3, 0), (-w / 2 - .3, d / 2 + .3, 0), (0, -d / 2 - .3, 2.2), (0, d / 2 + .3, 2.2))]
                    for fc in ((0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)): bm.faces.new([vs[q] for q in fc])
                    bm.to_mesh(rm); bm.free(); ro = link(bpy.data.objects.new("roof", rm), roof); ro.data.materials.append(mat(roof_c, 0.8))
                    self.houses.append(dict(g=g, walls=walls, roof=roof, wins=wins, x=x, z=z, w=w, d=d, h=h, side=side, wall_c=wall_c, roof_c=roof_c, ph=rr.random()))
                else:
                    stat.append(box(f"fh{i}{side}", w, h, d, wall_c, (x, h / 2, z)))
                    stat.append(box(f"fr{i}{side}", w + .6, 1.2, d + .6, roof_c, (x, h + .6, z)))
                if i < rows + 6:
                    for k in range(2):
                        tx, tz, th = side * rr.uniform(6, 7.5), z + rr.uniform(-5, 5), rr.uniform(2.5, 4.5)
                        tg = empty(f"tree{i}{side}{k}", (tx, 0, tz))
                        box("trunk", 0.3, th, 0.3, 0x5a4030, (0, th / 2, 0), parent=tg)
                        cr = ico("crown", rr.uniform(1.1, 1.8), [0x4f8a3c, 0x5a9440, 0x447a34][k], (0, 0, 0), parent=tg); cr.location = (0, 0, th + 0.8)
                        self.trees.append(dict(g=tg, z=tz, x=tx, h=th, ph=rr.random(), crown=cr))
            if i % 2 == 0 and i < rows + 6:
                pz = 14 - i * 11
                pg = empty(f"pole{i}", (5.8, 0, pz)); box("pole", 0.18, 7, 0.18, 0x6a5a4a, (0, 3.5, 0), parent=pg); box("arm", 1.6, 0.12, 0.12, 0x6a5a4a, (0, 6.6, 0), parent=pg)
                self.poles.append(dict(g=pg, z=pz, ph=rr.random()))
        # distant hills on the horizon so the road doesn't just end
        for k in range(26):
            a = -1.2 + k * 0.1; dist = rr.uniform(9000, 14000)
            stat.append(ico(f"hill{k}", rr.uniform(1500, 2800), 0x5f8a50, (math.sin(a) * dist, -900, -math.cos(a) * dist), sub=2))
        if parked_car:
            car = empty("car", (1.9, 0, -5.5))
            box("cbody", 1.8, 0.7, 4.2, 0xc0392b, (0, 0.75, 0), parent=car, bevel=0.12)
            cab = box("ccab", 1.6, 0.6, 2.2, 0x9a2c22, (0, 1.38, 0.2), parent=car, bevel=0.12)
            self.windshield = box("glass", 1.5, 0.5, 0.05, 0x9fc3dc, (0, 1.38, -0.92), parent=car, rough=0.08)
            for wx in (-0.85, 0.85):
                for wz in (-1.3, 1.3): box("wheel", 0.3, 0.6, 0.6, 0x1a1a1a, (wx, 0.3, wz), parent=car, bevel=0.1)
            self.car, self.cab = car, cab
        merge_static("town_static", stat)

    # --- damage helpers (blast comes from -z, so things are pushed toward +z)
    def shatter_windows(self, t, max_dist=200.0, rng=None):
        rng = rng or random.Random(5); bpy.context.view_layer.update()
        for hs in self.houses:
            dz = CAM_P.z - hs["z"]
            if abs(dz) > max_dist: continue
            tt = t + max(0.0, -dz) / 340.0 * 0.0 + rng.uniform(0, 0.25)
            for wo in hs["wins"]:
                keyat(wo, "hide_render", False, 1); keyat(wo, "hide_render", True, tt)
                wp = wo.matrix_world.translation.copy()
                for s_ in range(5):
                    sh = box("shard", rng.uniform(0.1, 0.3), rng.uniform(0.1, 0.35), 0.02, 0xbfe0f0, (0, -100, 0), rough=0.05)
                    p0 = Vector((wp.x, wp.z, -wp.y)) + Vector((rng.uniform(-.5, .5), rng.uniform(-.4, .4), rng.uniform(-.5, .5)))
                    v = Vector((-hs["side"] * rng.uniform(2, 6), rng.uniform(0, 3), rng.uniform(3, 9)))
                    for q in range(0, 26):
                        dt = q / 30.0; pos = p0 + v * dt + Vector((0, -4.9 * dt * dt, 0))
                        if pos.y < 0.02: pos.y = 0.02
                        sh.location = B(*pos); sh.rotation_euler = (dt * 9 + s_, dt * 7, dt * 5); sh.keyframe_insert("location", frame=fr(tt) + q); sh.keyframe_insert("rotation_euler", frame=fr(tt) + q)
                    sh.location = B(0, -100, 0); sh.keyframe_insert("location", frame=fr(tt) - 1)

    def blow_roofs(self, t, frac=1.0, rng=None):
        rng = rng or random.Random(6)
        for hs in self.houses:
            if rng.random() > frac: continue
            tt = t + rng.uniform(0, 0.6); r = hs["roof"]
            keyat(r, "location", Vector((0, 0, hs["h"])), tt)
            keyat(r, "rotation_euler", (0, 0, 0), tt)
            keyat(r, "location", Vector((rng.uniform(-3, 3), rng.uniform(-3, 3) + 0 - 25, hs["h"] + rng.uniform(6, 14))), tt + 1.6)   # Blender local: -Y = +z design
            keyat(r, "rotation_euler", (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-1, 1)), tt + 1.6)
            keyat(r, "location", Vector((rng.uniform(-4, 4), -45, -hs["h"] - 2)), tt + 3.2)
            keyat(r, "hide_render", False, tt + 3.1); keyat(r, "hide_render", True, tt + 3.3)

    def flatten_trees(self, t, ang=1.4, spread=1.0, rng=None):
        rng = rng or random.Random(7)
        for tr in self.trees + [dict(g=p["g"], z=p["z"], ph=p["ph"]) for p in self.poles]:
            dz = CAM_P.z - tr["z"]
            tt = t - dz / 300.0 * spread + rng.uniform(0, 0.3)
            a = ang * rng.uniform(0.8, 1.05)
            keyat(tr["g"], "rotation_euler", (0, 0, 0), tt - 0.1)
            keyat(tr["g"], "rotation_euler", (a * 0.6, rng.uniform(-.15, .15), 0), tt + 0.35)
            keyat(tr["g"], "rotation_euler", (a, rng.uniform(-.2, .2), 0), tt + 0.8)

    def collapse(self, t, frac=0.7, rng=None):
        rng = rng or random.Random(8)
        for hs in self.houses:
            if rng.random() > frac: continue
            tc = t + rng.uniform(0, 2.5)
            keyat(hs["walls"], "scale", (1, 1, 1), tc); keyat(hs["walls"], "scale", (1.08, 1.08, 0.15), tc + 0.7)
            keyat(hs["roof"], "location", Vector((0, 0, hs["h"])), tc); keyat(hs["roof"], "location", Vector((0, 0, 0.6)), tc + 0.8)
            keyat(hs["roof"], "rotation_euler", (0, 0, 0), tc); keyat(hs["roof"], "rotation_euler", (rng.uniform(-.3, .3), rng.uniform(-.3, .3), 0), tc + 0.8)
            for wo in hs["wins"]: keyat(wo, "hide_render", False, 1); keyat(wo, "hide_render", True, tc + 0.3)
            pile = empty("pile", (0, 0, 0)); pile.parent = hs["g"]; pile.location = (0, 0, 0)
            for k in range(14):
                bw, bh = rng.uniform(0.8, 2.6), rng.uniform(0.4, 1.2)
                pb = box("rub", bw, bh, rng.uniform(0.8, 2.4), [hs["wall_c"], hs["wall_c"], hs["roof_c"], 0x9a8f86][k % 4],
                         (rng.uniform(-hs["w"] / 2, hs["w"] / 2), bh / 2 + rng.uniform(0, 1.0), rng.uniform(-hs["d"] / 2, hs["d"] / 2)), parent=pile)
                pb.rotation_euler = (rng.uniform(-.6, .6), rng.uniform(-.6, .6), rng.uniform(0, 3))
            keyat(pile, "scale", (0.001,) * 3, tc + 0.2); keyat(pile, "scale", (1, 1, 1), tc + 0.8)

    def ignite(self, t, frac=1.0, rng=None):
        """flames on tree crowns / roofs: emissive cones flickering (keyed scale)"""
        rng = rng or random.Random(9); flames = []
        fm = emission_mat(0xff7a1a, 18.0); fm2 = emission_mat(0xffd060, 30.0)
        for tr in self.trees:
            if rng.random() > frac: continue
            for k in range(2):
                me = bpy.data.meshes.new("flame"); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.9 - k * .4, radius2=0.0, depth=2.4 - k * .8); bm.to_mesh(me); bm.free()
                fo = link(bpy.data.objects.new("flame", me), tr["g"]); fo.location = (rng.uniform(-.3, .3), rng.uniform(-.3, .3), tr["h"] + 1.4 + k * .2)
                fo.data.materials.append(fm if k == 0 else fm2); fo.visible_shadow = False
                flames.append((fo, t + rng.uniform(0, 4), rng.random() * 6))
        return flames

def sky_keys(W, f, sky=None, glow=None, hcol=None, sunglow=None, stars=None, dip=0.0):
    if sky is not None: kv(W["sky"], (*sky, 1), f)
    if glow is not None: kv(W["glow"], glow, f)
    if hcol is not None: kv(W["hcol"], (*hcol, 1), f)
    if sunglow is not None: kv(W["sunglow"], sunglow, f)
    if stars is not None: kv(W["stars"], stars, f)
    kv(W["dip"], dip, f)

DAY_SKY, DUSK_SKY, NIGHT_SKY = Vector((0.30, 0.52, 0.95)), Vector((0.10, 0.12, 0.28)), Vector((0.012, 0.018, 0.05))
ORANGE_SKY, RED_SKY, DARK_SKY = Vector((1.0, 0.42, 0.12)), Vector((0.55, 0.08, 0.02)), Vector((0.03, 0.025, 0.02))

def streak(name, color, strength, r_head, tail_len, thick=1.0, smoke=False):
    """glowing head + tail (+ optional persistent smoke trail segments)"""
    g = empty(name); g.rotation_mode = 'QUATERNION'
    ico("head", r_head, 0, (0, 0, 0), sub=2, material=emission_mat(color, strength), parent=g)
    tl = limb("tail", (0, 0, 0), (0, 0, tail_len), r_head * 0.9 * thick, r_head * 0.05, 0, g, material=emission_mat(color, strength * 0.4))
    for o in [g] + list(g.children_recursive): o.visible_shadow = False
    return g

def fly(g, p0, p1, t0, t1, f, t, accel=False):
    """place streak g on the segment p0->p1 at time t (tail points back along the path)"""
    k = cl((t - t0) / (t1 - t0)); k = k * k if accel else k
    pos = p0.lerp(p1, k); dirv = (p1 - p0).normalized()
    g.location = B(*pos); g.rotation_quaternion = B(*(-dirv)).to_track_quat('Z', 'Y')
    key(g, "location", f); key(g, "rotation_quaternion", f)
    vis(g, not (t0 <= t <= t1), f)
    return pos

def cloud_puff(name, pos, size, color=0xb8b0a8, n=7, rng=None, emit=0.0):
    rng = rng or random.Random(2); g = empty(name, pos)
    m = mat(color, 0.95, emit=emit, emit_col=0xff8a40) if emit else mat(color, 0.95)
    for k in range(n):
        o = ico("puff", size * rng.uniform(0.35, 0.6), 0, (rng.uniform(-1, 1) * size * .6, rng.uniform(-.3, .5) * size, rng.uniform(-1, 1) * size * .6), sub=2, material=m, parent=g)
        o.visible_shadow = False
    return g

def fireball(name, pos, r, hot=0xfff0c0, mid=0xff8a2a):
    g = empty(name, pos)
    core = ico("core", r * 0.8, 0, (0, 0, 0), sub=3, material=emission_mat(0xffd070, 9.0), parent=g)
    shell = ico("shell", r, 0, (0, 0, 0), sub=2, material=emission_mat(0xff5a10, 4.0), parent=g)
    rr = random.Random(int(r * 7) + 3)
    for k in range(10):   # lumpy outer fire
        a = rr.random() * math.tau; e = rr.uniform(-0.2, 0.9)
        o = ico("lump", r * rr.uniform(0.35, 0.55), 0, (math.cos(a) * r * 0.75, e * r * 0.7, math.sin(a) * r * 0.75), sub=2, material=emission_mat([0xff6a1a, 0xff8a2a, 0xe0400a][k % 3], 5.0), parent=g)
        o.visible_shadow = False
    for o in (g, core, shell): o.visible_shadow = False
    return g

def mushroom(name, pos, rng=None):
    rng = rng or random.Random(4); g = empty(name, pos)
    stem = empty("stem", (0, 0, 0)); stem.parent = g
    for k in range(10):
        o = ico("st", 0.18, 0, (rng.uniform(-.05, .05), k * 0.1, rng.uniform(-.05, .05)), sub=2, material=mat(0x8a7a6e, 0.95, emit=0.6, emit_col=0xff7030), parent=stem); o.visible_shadow = False
    cap = empty("cap", (0, 0, 0)); cap.parent = g; cap.location = B(0, 1.0, 0)
    for k in range(16):
        a = k / 16 * math.tau
        o = ico("cp", rng.uniform(0.22, 0.32), 0, (math.cos(a) * 0.32, rng.uniform(-.05, .12), math.sin(a) * 0.32), sub=2, material=mat(0x9a8a7c, 0.95, emit=0.8, emit_col=0xff6a20), parent=cap); o.visible_shadow = False
    for k in range(6):
        o = ico("cc", 0.3, 0, (rng.uniform(-.15, .15), 0.15, rng.uniform(-.15, .15)), sub=2, material=mat(0xa89888, 0.95, emit=1.2, emit_col=0xff8a30), parent=cap); o.visible_shadow = False
    return g, stem, cap

def dust_wall(name, n=40, rng=None, color=0x9a8676):
    rng = rng or random.Random(11); parts = []
    m = mat(color, 0.98)
    for i in range(n):
        o = ico(f"{name}{i}", 1.0, 0, (0, -50, 0), sub=2, material=m); o.visible_shadow = False
        parts.append(dict(o=o, x=rng.uniform(-120, 120), s=rng.uniform(8, 22), h=rng.uniform(0, 1), ph=rng.random()))
    return parts

def place_dust(parts, t, t_arrive, speed, f, height=30.0):
    """a wall of dust rolling toward you along +z; arrives at the camera at t_arrive"""
    zf = CAM_P.z - (t_arrive - t) * speed
    for q in parts:
        z = zf - q["ph"] * 25; on = t > t_arrive - 2000.0 / speed
        y = q["s"] * 0.5 + q["h"] * height * cl((t - t_arrive + 20) / 20)
        q["o"].location = B(q["x"], y, z); q["o"].scale = (q["s"],) * 3
        key(q["o"], "location", f); key(q["o"], "scale", f)
        vis(q["o"], not on, f)

def debris_layer(n, color_set=(0x8a7a6a, 0x6a5a4a, 0xc9a070, 0x5a6a3a)):
    return leaves(n, color_set)

def place_debris(lv, t, p, w, f, dirz=1.0):
    for q in lv:
        sp = (2 + 30 * w) * q["sp"]
        z = p.z - 60 + ((t * sp * dirz + q["ph"] * 20 - q["z"]) % 85)
        y = q["y"] + 0.8 * math.sin(t * 3 * q["sp"] + q["ph"]) if w > 0.05 else -5
        q["o"].location = B(q["x"], y, z); q["o"].rotation_euler = (t * 6 * q["sp"], t * 5 + q["ph"], t * 3)
        key(q["o"], "location", f); key(q["o"], "rotation_euler", f)

SUN_DIR = Vector((0.55, 0.42, -0.72)).normalized()     # design space, ahead-right, mid height

def base_scene(sky=DAY_SKY, sun_e=4.0, cam_fov=62, dusk=False, car=True, rows=9):
    W = sky_world(tuple(B(*SUN_DIR)))
    sky_keys(W, 1, sky=sky, glow=0.28 if not dusk else 1.0, hcol=(0.75, 0.85, 1.0) if not dusk else (1.0, 0.55, 0.35), sunglow=0.5 if not dusk else 0.2, stars=0.0 if not dusk else 1.5)
    sl = sun(sun_e, tuple(SUN_DIR * 10), (0, 0, 0), color=(1.0, 0.94, 0.85) if not dusk else (1.0, 0.6, 0.4), angle=1.0)
    town = Town(rows=rows, parked_car=car)
    cam = camera(cam_fov); cam.data.clip_end = 60000
    return W, sl, town, cam

def fx_light(name, pos, color=(1.0, 0.85, 0.6)):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = 0.0; d.color = color; d.angle = math.radians(3)
    o = link(bpy.data.objects.new(name, d)); o.location = B(*pos); look_rot(o, B(*pos), B(0, 0, 0)); return o

def flash_keys(lamp, t, peak, rise=0.08, hold=0.4, fall=3.0, base=0.0):
    lamp.data.energy = base; lamp.data.keyframe_insert("energy", frame=fr(t - 0.1))
    lamp.data.energy = peak; lamp.data.keyframe_insert("energy", frame=fr(t + rise))
    lamp.data.energy = peak * 0.6; lamp.data.keyframe_insert("energy", frame=fr(t + rise + hold))
    lamp.data.energy = base; lamp.data.keyframe_insert("energy", frame=fr(t + rise + hold + fall))

def expo_keys(t, peak, fall=2.5, base=None):
    vs = scene.view_settings; b = vs.exposure if base is None else base
    vs.exposure = b; vs.keyframe_insert("exposure", frame=fr(t - 0.05))
    vs.exposure = b + peak; vs.keyframe_insert("exposure", frame=fr(t + 0.06))
    vs.exposure = b; vs.keyframe_insert("exposure", frame=fr(t + fall))

def handheld(t, amp=1.0):
    return Vector((0.012 * math.sin(t * 0.9) + 0.006 * math.sin(t * 2.3), 0.008 * math.sin(t * 1.3), 0.0)) * amp

def quake(t, t0, dur, amp):
    k = cl((t - t0) / 0.4) * cl((t0 + dur - t) / (dur * 0.6))
    return shake(t, amp * k, 31) + shake(t, amp * 0.5 * k, 13)

LOOK0 = Vector((0.2, 3.6, -60.0))

# ======================================================================= ACTS
def act_intro():
    W, sl, town, cam = base_scene()
    lv = leaves(60)
    def frame(t, f):
        look = LOOK0.lerp(Vector((0.5, 40, -60)), math.sin(cl((t - 3.5) / 9) * math.pi) * 0.7)   # glance up at the sky
        cam_key(cam, CAM_P + handheld(t), look, f)
        place_debris(lv, t, CAM_P, 0.0, f)
    return frame

def act_pebble():
    W, sl, town, cam = base_scene(sky=NIGHT_SKY, sun_e=0.0, dusk=True, car=True)
    sky_keys(W, 1, sky=DUSK_SKY * 0.35, glow=0.5, hcol=(0.5, 0.35, 0.45), sunglow=0.0, stars=2.2)
    moon = light('SUN', "moonl", 0.25, (0.6, 0.7, 1.0), (-10, 10, 5), (0, 0, 0))
    for hs in town.houses:   # lit windows at night
        for wo in hs["wins"]: wo.data.materials.clear(); wo.data.materials.append(mat(0xffd9a0, 0.5, emit=2.5, emit_col=0xffc070))
    lamps = [light('POINT', f"sl{i}", 300, (1.0, 0.8, 0.55), (5.2, 6.4, p["z"]), soft=0.3) for i, p in enumerate(town.poles[:6])]
    mets = []
    for i, (te, a, b) in enumerate(((E["meteor1"], (-900, 1300, -2600), (500, 900, -2400)), (E["meteor2"], (800, 1500, -2200), (-200, 1000, -2600)),
                                    (E["meteor3"], (-300, 1700, -2000), (700, 1100, -2300)), (E["meteor4"], (200, 1600, -2500), (-900, 1000, -2200)),
                                    (52.5, (-700, 1400, -2400), (300, 1000, -2500)))):
        g = streak(f"met{i}", 0xe0f0ff, 60.0, 6.0, 260.0)
        mets.append((g, Vector(a), Vector(b), te, te + (1.1 if i != 2 else 1.6)))
    def frame(t, f):
        look = Vector((0.6, 1400, -2400)) - CAM_P
        look = CAM_P + Vector((0.8, 4.0, -60)).lerp(look.normalized() * 60, sm((t - 23) / 3.5))
        cam_key(cam, CAM_P + handheld(t), look, f)
        for g, a, b, t0, t1 in mets: fly(g, a, b, t0, t1, f, t)
    return frame

def act_stone():
    W, sl, town, cam = base_scene()
    stone = empty("stone"); ico("rock", 0.06, 0x3a3634, (0, 0, 0), sub=2, parent=stone)
    glow = ico("glowr", 0.35, 0, (0, 0, 0), sub=2, material=emission_mat(0xffc080, 30.0), parent=stone); glow.visible_shadow = False
    hole = box("hole", 0.25, 0.02, 0.25, 0x050505, (0, 1.69, 0.2), parent=town.car)
    car = town.car; carp = Vector((1.9, 0, -5.5)); roof_hit = carp + Vector((0.0, 1.68, 0.2))
    keyat(hole, "hide_render", True, 1); keyat(hole, "hide_render", False, E["stone_hit"])
    keyat(town.cab, "scale", (1, 1, 1), E["stone_hit"]); keyat(town.cab, "scale", (1.03, 0.82, 1.0), E["stone_hit"] + 0.08)
    keyat(car, "location", B(*carp), E["stone_hit"]); keyat(car, "location", B(*(carp + Vector((0, -0.08, 0)))), E["stone_hit"] + 0.06)
    keyat(car, "location", B(*carp), E["stone_hit"] + 0.4)
    puff = cloud_puff("dustp", (roof_hit.x, roof_hit.y, roof_hit.z), 1.1, color=0xcfc4b8)
    keyat(puff, "scale", (0.001,) * 3, E["stone_hit"]); keyat(puff, "scale", (1, 1, 1), E["stone_hit"] + 0.4); keyat(puff, "scale", (1.6, 1.6, 1.6), E["stone_hit"] + 2.5)
    keyat(puff, "hide_render", False, E["stone_hit"] + 2.4); keyat(puff, "hide_render", True, E["stone_hit"] + 2.6)
    keyat(town.windshield, "hide_render", False, 1); keyat(town.windshield, "hide_render", True, E["stone_hit"] + 0.05)
    hazard = [light('POINT', f"hz{s_}", 0, (1.0, 0.6, 0.1), (carp.x + s_ * 0.8, 0.8, carp.z - 2.2), soft=0.1) for s_ in (-1, 1)]
    for k in range(int((A1 - E["stone_hit"] - 1) * 2)):
        for hz in hazard:
            tt = E["stone_hit"] + 0.6 + k * 0.5
            hz.data.energy = 60 if k % 2 == 0 else 0; hz.data.keyframe_insert("energy", frame=fr(tt))
    def frame(t, f):
        # high glowing point -> dark fall -> hit
        if t < E["stone_in"] + 1.4:
            k = cl((t - (E["stone_in"] - 3)) / 4.4); pos = Vector((-400, 2600, -2200)).lerp(Vector((-60, 900, -450)), k)
            stone.location = B(*pos); stone.scale = (40, 40, 40)
        else:
            k = cl((t - (E["stone_in"] + 1.4)) / (E["stone_hit"] - E["stone_in"] - 1.4)); pos = Vector((-60, 900, -450)).lerp(roof_hit, k * k * 0.15 + k * 0.85)
            stone.location = B(*pos); stone.scale = (lerp(40, 1, cl(k * 3)),) * 3
        if t > E["stone_hit"]: stone.location = B(*(roof_hit - Vector((0, 0.3, 0))))
        key(stone, "location", f); key(stone, "scale", f)
        vis(glow, not (t < E["stone_in"] + 1.2), f)
        vis(stone, not (E["stone_in"] - 3 < t < E["stone_hit"] + 0.1), f)
        lk = Vector((-60, 900, -450)) if t < E["stone_hit"] - 0.6 else roof_hit
        if t < E["stone_in"] - 3.2: lk = LOOK0
        if t < E["stone_hit"] - 0.6: look = CAM_P + (lk - CAM_P).normalized() * 60
        else: look = roof_hit
        if t > E["stone_hit"] + 4: look = roof_hit.lerp(roof_hit + Vector((0, -0.4, 0)), sm((t - E["stone_hit"] - 4) / 3))
        look = (CAM_P + (LOOK0 - CAM_P)).lerp(look, sm((t - (E["stone_in"] - 3.2)) / 1.5)) if t < E["stone_in"] - 1.7 else look
        p = Vector((0.6, 1.62, 0.5)) + handheld(t)
        if t > E["stone_hit"] + 3: p = p.lerp(Vector((1.4, 1.62, -2.6)), sm((t - E["stone_hit"] - 3) / 5))     # walk up to the car
        if E["stone_hit"] < t < E["stone_hit"] + 0.5: p += shake(t, 0.02 * (1 - (t - E["stone_hit"]) / 0.5), 40)
        cam_key(cam, p, look, f)
    return frame

def airburst_common(W, sl, cam, t_streak, t_burst, a, b, color=0xfff0d0, head=40.0, tail=4000, smoke=True, peak=60.0, sky_peak=3.0):
    g = streak("bolide", color, 80.0, head, tail)
    fl = fx_light("flashl", tuple(b))
    flash_keys(fl, t_burst, peak, fall=4.0)
    expo_keys(t_burst, 3.0 if peak > 30 else 1.2, fall=3.0, base=0.2)
    for tt, k in ((t_burst - 0.1, 0.0), (t_burst + 0.08, 1.0), (t_burst + 0.6, 0.7), (t_burst + 3.5, 0.0)):
        kv(W["sky"], (*DAY_SKY.lerp(Vector((3.0, 2.9, 2.6)), k), 1), fr(tt))
    ball = ico("burst", 1.0, 0, tuple(b), sub=3, material=emission_mat(0xfff6e0, 60.0)); ball.visible_shadow = False
    keyat(ball, "scale", (0.001,) * 3, t_burst - 0.05); keyat(ball, "scale", (head * 8,) * 3, t_burst + 0.25); keyat(ball, "scale", (head * 2,) * 3, t_burst + 2.5)
    keyat(ball, "hide_render", False, t_burst - 0.1); keyat(ball, "hide_render", True, t_burst + 2.6)
    trail = []
    if smoke:   # persistent smoke trail along the path
        n = 44
        for i in range(n):
            q = a.lerp(b, i / (n - 1))
            pf = cloud_puff(f"tr{i}", (q.x, q.y, q.z), head * 5.0, color=0xe6e0da, n=4, rng=random.Random(i))
            tp = t_streak + (t_burst - t_streak) * (i / (n - 1))
            keyat(pf, "scale", (0.001,) * 3, tp); keyat(pf, "scale", (1, 1, 1), tp + 0.4); keyat(pf, "scale", (2.2, 2.2, 2.2), A1)
            keyat(pf, "location", B(*q), tp); keyat(pf, "location", B(*(q + Vector((head * 6, 0, 0)))), A1)
            trail.append(pf)
        big = cloud_puff("bursts", (b.x, b.y, b.z), head * 6, color=0xe0d6cc, n=9, rng=random.Random(99))
        keyat(big, "scale", (0.001,) * 3, t_burst); keyat(big, "scale", (1, 1, 1), t_burst + 1.5); keyat(big, "scale", (1.8, 1.8, 1.8), A1)
    return g

def act_boulder():
    W, sl, town, cam = base_scene()
    a, b = Vector((-7000, 13000, -15000)), Vector((1000, 7000, -13000))
    g = airburst_common(W, sl, cam, E["fireball"] - 2.5, E["burst"], a, b, head=90.0, tail=4000, peak=12.0)
    lv = leaves(80)
    def frame(t, f):
        fly(g, a, b, E["fireball"] - 2.5, E["burst"], f, t)
        target = a.lerp(b, cl((t - E["fireball"] + 2.5) / (E["burst"] - E["fireball"] + 2.5)))
        look = CAM_P + (target - CAM_P).normalized() * 60
        look = (LOOK0).lerp(look, sm((t - 98) / 2.5))
        if t > E["burst"] + 8: look = look.lerp(LOOK0, sm((t - E["burst"] - 8) / 4))
        if t > E["boom1"] - 0.5: look = look.lerp(CAM_P + (b - CAM_P).normalized() * 60, sm((t - E["boom1"] + 0.5) / 1.5) * 0.7)
        p = CAM_P + handheld(t)
        if E["boom1"] < t < E["boom1"] + 2.5: p += shake(t, 0.015 * (1 - (t - E["boom1"]) / 2.5), 29)
        cam_key(cam, p, look, f)
        w = 0.35 * cl((t - E["boom1"]) / 0.3) * (1 - cl((t - E["boom1"] - 3) / 3))
        place_debris(lv, t, CAM_P, w, f)
    return frame

def act_chelyab():
    W, sl, town, cam = base_scene()
    sky_keys(W, 1, sky=DAY_SKY * 0.9, glow=1.0, hcol=(1.0, 0.85, 0.75), sunglow=0.6)
    a, b = Vector((-30000, 22000, -24000)), Vector((6000, 9000, -30000))
    g = airburst_common(W, sl, cam, E["ch_streak"], E["ch_flash"], a, b, head=120.0, tail=9000, peak=80.0)
    town.shatter_windows(E["ch_shock"], max_dist=120)
    lv = leaves(140)
    def frame(t, f):
        fly(g, a, b, E["ch_streak"], E["ch_flash"], f, t)
        target = a.lerp(b, cl((t - E["ch_streak"]) / (E["ch_flash"] - E["ch_streak"])))
        look = CAM_P + (target - CAM_P).normalized() * 60
        look = LOOK0.lerp(look, sm((t - 139.5) / 2))
        if E["ch_flash"] < t < E["ch_flash"] + 1.0: look += Vector((0, -6, 0)) * math.sin(cl((t - E["ch_flash"]) / 1.0) * math.pi)   # flinch
        if t > 155: look = look.lerp(CAM_P + ((a + b) * 0.5 - CAM_P).normalized() * 60, sm((t - 155) / 3))           # the smoke trail
        if t > 165: look = look.lerp(Vector((-8.5, 2.3, CAM_P.z - 4.0)), sm((t - 165) / 2.5))                     # the windows next to you
        if t > E["ch_shock"] + 1.5: look = look.lerp(LOOK0, sm((t - E["ch_shock"] - 1.5) / 4))
        p = CAM_P + handheld(t)
        if E["ch_shock"] < t < E["ch_shock"] + 3: p += shake(t, 0.05 * (1 - (t - E["ch_shock"]) / 3), 33)
        cam_key(cam, p, look, f)
        w = 0.8 * cl((t - E["ch_shock"]) / 0.3) * (1 - cl((t - E["ch_shock"] - 4) / 5))
        place_debris(lv, t, CAM_P, w, f)
    return frame

def act_tunguska():
    W, sl, town, cam = base_scene(rows=12)
    a, b = Vector((-24000, 30000, -22000)), Vector((-1500, 7000, -15000))
    g = airburst_common(W, sl, cam, E["tg_streak"], E["tg_flash"], a, b, head=200.0, tail=9000, peak=140.0, smoke=False)
    fb = fireball("tgfire", tuple(b), 1.0)
    keyat(fb, "scale", (0.001,) * 3, E["tg_flash"]); keyat(fb, "scale", (1400,) * 3, E["tg_flash"] + 1.0); keyat(fb, "scale", (2200,) * 3, E["tg_flash"] + 6)
    keyat(fb, "hide_render", False, E["tg_flash"] - .1); keyat(fb, "hide_render", True, E["tg_flash"] + 7)
    town.flatten_trees(E["tg_shock"], ang=1.45); town.blow_roofs(E["tg_shock"] + 0.3, frac=0.8); town.shatter_windows(E["tg_shock"], max_dist=200)
    lv = leaves(220); dust = dust_wall("tgd", 50)
    smoke = []   # trees start to smoke in the heat
    for tr in town.trees[:24]:
        pf = cloud_puff("tsm", (0, 0, 0), 0.8, color=0x7a7068, n=3); pf.parent = tr["g"]; pf.location = (0, 0, tr["h"] + 2.0)
        keyat(pf, "scale", (0.001,) * 3, E["tg_heat"] + tr["ph"] * 2); keyat(pf, "scale", (1.2, 1.2, 1.2), E["tg_heat"] + 3 + tr["ph"] * 2)
    def frame(t, f):
        fly(g, a, b, E["tg_streak"], E["tg_flash"], f, t)
        target = a.lerp(b, cl((t - E["tg_streak"]) / (E["tg_flash"] - E["tg_streak"])))
        look = CAM_P + (target - CAM_P).normalized() * 60
        look = LOOK0.lerp(look, sm((t - 197.5) / 2))
        if E["tg_flash"] < t < E["tg_flash"] + 1.4: look += Vector((0, -10, 0)) * math.sin(cl((t - E["tg_flash"]) / 1.4) * math.pi)
        if t > 209.5: look = look.lerp(Vector((-6.5, 3.0, CAM_P.z - 14)), sm((t - 209.5) / 2) * (1 - sm((t - E["tg_shock"] - 1) / 2)))   # trees leaning
        if t > E["tg_shock"] + 1: look = look.lerp(LOOK0 + Vector((0, -1.5, 0)), sm((t - E["tg_shock"] - 1) / 3))
        p = CAM_P + handheld(t)
        if 210 < t < E["tg_shock"]: p += shake(t, 0.004 * (t - 210), 17)
        if E["tg_shock"] < t: p += quake(t, E["tg_shock"], 6, 0.06)
        cam_key(cam, p, look, f)
        for tr in town.trees[:30]:   # leaning in the heat-wind before the blast
            if t < E["tg_shock"] - 0.2:
                lean = 0.12 * cl((t - 210) / 9) + 0.03 * math.sin(t * 3 + tr["ph"] * 6) * cl((t - 210) / 9)
                tr["g"].rotation_euler = (lean, 0, 0); key(tr["g"], "rotation_euler", f)
        w = cl((t - E["tg_shock"]) / 0.3) * (1 - 0.6 * cl((t - E["tg_shock"] - 8) / 6))
        place_debris(lv, t, CAM_P, w, f)
        place_dust(dust, t, E["tg_shock"] + 0.6, 340.0, f, height=40)
        sky = DAY_SKY.lerp(Vector((0.85, 0.6, 0.45)), cl((t - E["tg_flash"]) / 2) * (1 - 0.5 * cl((t - E["tg_shock"]) / 4)))
        sky = sky.lerp(Vector((0.55, 0.48, 0.42)), cl((t - E["tg_shock"]) / 3))
        sky_keys(W, f, sky=sky)
    return frame

def ground_impact(W, cam, t_hit, dist, dome_r, cloud_h, rng_seed=1, color_far=0x8a7a6a):
    """flash + fireball dome on the horizon that grows and lifts into a mushroom."""
    pos = Vector((-0.12 * dist, 0, -dist))
    fl = fx_light("impl", (pos.x, dist * 0.3, pos.z)); flash_keys(fl, t_hit, 90.0, fall=6.0)
    expo_keys(t_hit, 1.8, fall=4.0)
    fb = fireball("dome", tuple(pos), 1.0)
    keyat(fb, "scale", (0.001,) * 3, t_hit); keyat(fb, "scale", (dome_r * 0.6,) * 3, t_hit + 0.6); keyat(fb, "scale", (dome_r,) * 3, t_hit + 6)
    keyat(fb, "location", B(*pos), t_hit + 3); keyat(fb, "location", B(*(pos + Vector((0, cloud_h * 0.9, 0)))), t_hit + 22)
    keyat(fb, "scale", (dome_r * 0.9,) * 3, t_hit + 22)
    g, stem, cap = mushroom("mush", tuple(pos))
    keyat(g, "scale", (0.001,) * 3, t_hit + 2.5); keyat(g, "scale", (cloud_h * 0.3,) * 3, t_hit + 6); keyat(g, "scale", (cloud_h,) * 3, t_hit + 26); keyat(g, "scale", (cloud_h * 1.25,) * 3, t_hit + 60)
    keyat(fb, "hide_render", False, t_hit - .1); keyat(fb, "hide_render", True, t_hit + 24)
    return pos

def act_city():
    W, sl, town, cam = base_scene(rows=12)
    a = Vector((-14000, 60000, -40000)); bpt = Vector((-1000, 0, -9000))
    g = streak("cityb", 0xfff0d0, 90.0, 150.0, 9000)
    pos = ground_impact(W, cam, E["ct_hit"], 9000, 1300, 7000)
    town.blow_roofs(E["ct_shock"] + 0.2, frac=1.0); town.flatten_trees(E["ct_shock"], ang=1.45); town.shatter_windows(E["ct_shock"], max_dist=200)
    lv = leaves(220); dust = dust_wall("ctd", 60, color=0x8e7a68)
    def frame(t, f):
        fly(g, a, bpt, E["ct_streak"], E["ct_hit"], f, t, accel=False)
        look = LOOK0 + Vector((0, 4 + 30 * cl((t - E["ct_hit"] - 2) / 20), 0))
        if t < E["ct_hit"]: look = LOOK0.lerp(CAM_P + (a.lerp(bpt, cl((t - E["ct_streak"]) / 4.5)) - CAM_P).normalized() * 60, sm((t - 256.5) / 1.5))
        if E["ct_hit"] < t < E["ct_hit"] + 1.4: look += Vector((0, -8, 0)) * math.sin(cl((t - E["ct_hit"]) / 1.4) * math.pi)
        if t > E["ct_shock"] + 1: look = look.lerp(LOOK0 + Vector((0, 2, 0)), sm((t - E["ct_shock"] - 1) / 3))
        p = CAM_P + handheld(t) + quake(t, E["ct_quake"], 7, 0.05) + quake(t, E["ct_shock"], 6, 0.07)
        cam_key(cam, p, look, f)
        w = cl((t - E["ct_shock"]) / 0.3) * (1 - 0.5 * cl((t - E["ct_shock"] - 8) / 6))
        place_debris(lv, t, CAM_P, w, f)
        place_dust(dust, t, E["ct_shock"] + 0.5, 340.0, f, height=60)
        sky = DAY_SKY.lerp(Vector((0.9, 0.62, 0.42)), cl((t - E["ct_hit"]) / 3) * 0.6).lerp(Vector((0.5, 0.42, 0.36)), cl((t - E["ct_shock"]) / 3))
        sky_keys(W, f, sky=sky)
    return frame

def ejecta(n, rng, color=0xffa040):
    out = []
    for i in range(n):
        g = streak(f"ej{i}", color, 40.0, rng.uniform(1.5, 4.0), rng.uniform(60, 160))
        x0 = rng.uniform(-400, 400); z0 = rng.uniform(-600, 40)
        a = Vector((x0 + rng.uniform(-200, 200), rng.uniform(500, 900), z0 - rng.uniform(100, 400)))
        b = Vector((x0, 0, z0))
        out.append(dict(g=g, a=a, b=b, t0=rng.random(), dur=rng.uniform(1.2, 2.2)))
    return out

def place_ejecta(ej, t, t0, t1, f, rate=1.0):
    for q in ej:
        start = t0 + q["t0"] * (t1 - t0) * rate
        fly(q["g"], q["a"], q["b"], start, start + q["dur"], f, t, accel=True)

def act_km1():
    W, sl, town, cam = base_scene(rows=12)
    pos = ground_impact(W, cam, E["k1_hit"], 14000, 5500, 16000)
    town.collapse(E["k1_quake"] + 1.5, frac=0.35); town.blow_roofs(E["k1_shock"], frac=1.0); town.flatten_trees(E["k1_shock"], ang=1.45)
    town.shatter_windows(E["k1_quake"], max_dist=200)
    rng = random.Random(21); ej = ejecta(70, rng)
    lv = leaves(240); dust = dust_wall("k1d", 70, color=0x7a6a5e)
    def frame(t, f):
        look = LOOK0 + Vector((0, 6 + 40 * cl((t - E["k1_hit"] - 2) / 20), 0))
        if E["k1_hit"] < t < E["k1_hit"] + 1.4: look += Vector((0, -8, 0)) * math.sin(cl((t - E["k1_hit"]) / 1.4) * math.pi)
        if E["k1_ejecta"] - 1 < t < E["k1_shock"] - 2: look = look.lerp(Vector((-2, 30, -40)), sm((t - E["k1_ejecta"] + 1) / 3))
        if t > E["k1_shock"] + 1: look = look.lerp(LOOK0 + Vector((0, 4, 0)), sm((t - E["k1_shock"] - 1) / 3))
        p = CAM_P + handheld(t) + quake(t, E["k1_quake"], 8, 0.12) + quake(t, E["k1_shock"], 7, 0.09)
        cam_key(cam, p, look, f)
        place_ejecta(ej, t, E["k1_ejecta"], E["k1_shock"] + 2, f)
        w = cl((t - E["k1_shock"]) / 0.3)
        place_debris(lv, t, CAM_P, w, f)
        place_dust(dust, t, E["k1_shock"] + 0.5, 340.0, f, height=80)
        sky = DAY_SKY.lerp(Vector((1.0, 0.6, 0.35)), cl((t - E["k1_glow"]) / 3) * 0.7).lerp(Vector((0.4, 0.3, 0.25)), cl((t - E["k1_shock"]) / 4))
        sky = sky.lerp(Vector((0.18, 0.14, 0.12)), cl((t - 358) / 8))
        sky_keys(W, f, sky=sky, glow=1.5)
    return frame

def act_km10():
    W, sl, town, cam = base_scene(rows=12)
    fl = fx_light("glowl", (-2000, 800, -20000), color=(1.0, 0.55, 0.25)); flash_keys(fl, E["k10_glow"], 20.0, rise=1.5, hold=10, fall=30, base=0.0)
    town.collapse(E["k10_quake"] + 1.0, frac=0.6); town.shatter_windows(E["k10_quake"], max_dist=200)
    flames = town.ignite(E["k10_fire"], frac=0.8)
    rng = random.Random(31); ej = ejecta(110, rng, color=0xff9a40)
    hi = []   # streaks high across the whole sky
    for i in range(60):
        g = streak(f"hs{i}", 0xffb060, 50.0, 30.0, 2500)
        x0 = rng.uniform(-30000, 30000); z0 = rng.uniform(-40000, 5000)
        hi.append(dict(g=g, a=Vector((x0, rng.uniform(18000, 26000), z0)), b=Vector((x0 + rng.uniform(-6000, 6000), rng.uniform(2000, 6000), z0 + rng.uniform(-4000, 4000))), t0=rng.random(), dur=rng.uniform(2.5, 4.5)))
    smoke = dust_wall("k10s", 60, color=0x2a2420)
    lv = leaves(200, (0x3a2a1a, 0xff8a30, 0x5a4a3a, 0x2a2a2a))
    def frame(t, f):
        look = LOOK0 + Vector((0, 4 + 10 * cl((t - E["k10_glow"]) / 6), 0))
        if t > E["k10_ejecta"] - 1: look = look.lerp(Vector((0, 60, -40)), sm((t - E["k10_ejecta"] + 1) / 3) * (1 - sm((t - 416) / 3)))
        if t > 417: look = look.lerp(Vector((-6, 4, CAM_P.z - 18)), sm((t - 417) / 3))
        if t > 427: look = look.lerp(LOOK0 + Vector((0, 6, 0)), sm((t - 427) / 4))
        p = CAM_P + handheld(t) + quake(t, E["k10_quake"], 10, 0.16)
        cam_key(cam, p, look, f)
        for q in hi:
            st = E["k10_ejecta"] + q["t0"] * 30
            fly(q["g"], q["a"], q["b"], st, st + q["dur"], f, t, accel=True)
        place_ejecta(ej, t, E["k10_ejecta"] + 3, E["k10_fire"] + 6, f)
        for fo, tf, ph in flames:
            on = t > tf
            s_ = (0.6 + 0.4 * math.sin(t * 13 + ph) * math.sin(t * 7 + ph * 2)) if on else 0.001
            fo.scale = (s_, s_, s_ * 1.2); key(fo, "scale", f)
        place_dust(smoke, t, E["k10_dark"] - 4, 120.0, f, height=60)
        heat = cl((t - 404) / 6)
        sky = DAY_SKY.lerp(ORANGE_SKY, cl((t - E["k10_glow"]) / 20) * 0.5).lerp(ORANGE_SKY * 1.1, heat).lerp(RED_SKY, cl((t - 420) / 6)).lerp(DARK_SKY, cl((t - E["k10_dark"] + 6) / 8))
        sky_keys(W, f, sky=sky, glow=2.0 + 2 * heat, hcol=(1.0, 0.5, 0.2))
        sl.data.energy = lerp(4.0, 1.5, heat) * (1 - cl((t - E["k10_dark"] + 6) / 6)); sl.data.keyframe_insert("energy", frame=f)
        w = 0.5 * heat
        place_debris(lv, t, CAM_P, w, f)
    return frame

def act_km100():
    W, sl, town, cam = base_scene(sky=DUSK_SKY, sun_e=1.2, dusk=True, rows=12)
    sky_keys(W, 1, sky=DUSK_SKY, glow=1.2, hcol=(1.0, 0.55, 0.35), sunglow=0.3, stars=0.6)
    fl = fx_light("glow100", (0, 900, -30000), color=(1.0, 0.7, 0.45)); flash_keys(fl, E["k100_glow"], 12.0, rise=2, hold=8, fall=2, base=0.0)
    # the glowing wall of rock vapour: a curved band that rises on the horizon and rolls toward you
    me = bpy.data.meshes.new("wall"); bm = bmesh.new(); segs = 40
    for i in range(segs):
        a0, a1 = -1.0 + 2 * i / segs, -1.0 + 2 * (i + 1) / segs
        vs = [bm.verts.new(v) for v in ((math.sin(a0), 0, 0), (math.sin(a1), 0, 0), (math.sin(a1), 0, 1), (math.sin(a0), 0, 1))]
        bm.faces.new(vs)
    bm.to_mesh(me); bm.free()
    wall = link(bpy.data.objects.new("vwall", me)); wall.data.materials.append(emission_mat(0xffb070, 12.0)); wall.visible_shadow = False
    top = cloud_puff("vtop", (0, 0, 0), 1.0, color=0xff9a60, n=12, emit=6.0)
    flames = town.ignite(476, frac=1.0)
    def frame(t, f):
        k = cl((t - E["k100_wall"]) / (E["k100_hit"] - E["k100_wall"]))
        dist = lerp(40000, 30, k ** 1.6); h = lerp(200, 9000, cl(k * 1.4))
        wall.location = B(0, 0, CAM_P.z - dist); wall.scale = (dist * 1.2 + 300, 1, h); key(wall, "location", f); key(wall, "scale", f)
        vis(wall, t < E["k100_wall"], f)
        top.location = B(0, h, CAM_P.z - dist); top.scale = (dist * 0.25 + 50, h * 0.08 + 20, dist * 0.02 + 30); key(top, "location", f); key(top, "scale", f)
        vis(top, t < E["k100_wall"], f)
        look = LOOK0 + Vector((0, 3 + 25 * k, 0))
        p = CAM_P + handheld(t) + quake(t, 458, 12, 0.05) * 0.6
        cam_key(cam, p, look, f)
        sky = DUSK_SKY.lerp(Vector((0.6, 0.3, 0.2)), cl((t - E["k100_glow"]) / 6)).lerp(Vector((1.0, 0.55, 0.25)), cl((t - 470) / 12)).lerp(Vector((1.0, 0.9, 0.75)), cl((t - 484) / 4))
        sky_keys(W, f, sky=sky, glow=1.2 + 3 * k, hcol=(1.0, 0.6, 0.3))
        for fo, tf, ph in flames:
            on = t > tf
            s_ = (0.6 + 0.4 * math.sin(t * 13 + ph) * math.sin(t * 7 + ph * 2)) if on else 0.001
            fo.scale = (s_, s_, s_ * 1.2); key(fo, "scale", f)
    expo_keys(E["k100_hit"] - 0.5, 0.0, fall=0.1)
    vs = scene.view_settings; vs.exposure = 0.0; vs.keyframe_insert("exposure", frame=fr(E["k100_hit"] - 1.0)); vs.exposure = 6.0; vs.keyframe_insert("exposure", frame=fr(E["k100_hit"] + 0.8))
    return frame

def act_outro():
    W, sl, town, cam = base_scene(sky=DUSK_SKY, sun_e=1.2, dusk=True)
    g = streak("lastmet", 0xe0f0ff, 60.0, 6.0, 260.0)
    lv = leaves(160)
    def frame(t, f):
        fly(g, Vector((-800, 1500, -2400)), Vector((400, 1000, -2500)), 503.0, 504.2, f, t)
        look = LOOK0.lerp(Vector((0.4, 30, -60)), math.sin(cl((t - 500) / 7) * math.pi) * 0.7)
        cam_key(cam, CAM_P + handheld(t), look, f)
        w = 0.6 * cl((t - 508) / 3)
        place_debris(lv, t, CAM_P, w, f)
        for tr in town.trees[:30]:
            tr["g"].rotation_euler = (0.08 * w + 0.04 * w * math.sin(t * 3 + tr["ph"] * 6), 0, 0); key(tr["g"], "rotation_euler", f)
    return frame

ACTS = dict(intro=act_intro, pebble=act_pebble, stone=act_stone, boulder=act_boulder, chelyab=act_chelyab, tunguska=act_tunguska,
            city=act_city, km1=act_km1, km10=act_km10, km100=act_km100, outro=act_outro)

frame_fn = ACTS[ACT]()
f_lo, f_hi = F0, F1
if TIMES:
    frs = [fr(float(x)) for x in TIMES.split(",")]
    f_lo, f_hi = max(F0, min(frs) - 2), min(F1, max(frs) + 2)
elif FRAMES:
    a_, b_ = map(int, FRAMES.split("-")); f_lo, f_hi = max(F0, a_), min(F1, b_)
for f in range(f_lo, f_hi + 1):
    frame_fn((f - 1) / FPS, f)
try: scene.eevee.shadow_pool_size = '1024'
except Exception: pass
setup_render(scene, OUT, RES, ENGINE, SAMPLES, DEVICE, FPS, f_lo, f_hi, exposure=0.2)
render(scene, TIMES.split(",") if TIMES else None, FPS)
print(f"[scene] act {ACT} done", flush=True)
