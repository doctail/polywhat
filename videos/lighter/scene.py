"""Blender scenes for 'What If You Got Lighter Every Hour' — one act per Blender process.
   blender -b -P scene.py -- --act NAME --out DIR [--res 1920x1080] [--engine eevee|cycles] [--samples N] [--times 2,11]
Frames are written with GLOBAL numbering (act start..end) so all acts share one folder."""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import timeline as TL
from pw3d import *  # noqa

get = args(sys.argv)
ACT = get("--act", "house"); OUT = get("--out", "/tmp/lighter_raw"); RES = get("--res", "1920x1080")
ENGINE = get("--engine", "eevee"); SAMPLES = int(get("--samples", "24")); DEVICE = get("--device", "gpu")
TIMES = get("--times"); FRAMES = get("--frames")
FPS = TL.FPS; E = TL.EVENTS
A0, A1 = [(a, b) for n, a, b in TL.ACTS if n == ACT][0]
F0, F1 = int(round(A0 * FPS)) + 1, int(round(A1 * FPS))
scene = reset()
rnd = random.Random(hash(ACT) % 1000)

def fr(t): return int(round(t * FPS)) + 1
def keyat(ob, path, value, t):
    setattr(ob, path, value); ob.keyframe_insert(path, frame=fr(t))

def hands_pose(hL, hR, f, hx=0.3, hy=-0.24, hz=-0.5, rx=-0.25, spread=0.0):
    for h, s in ((hL, -1), (hR, 1)):
        h.location = (s * (hx + spread), hy, hz); h.rotation_euler = (rx, s * -0.25, s * -0.1)
        key(h, "location", f); key(h, "rotation_euler", f)

# ----------------------------------------------------------------------- shared: suburban street
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

# ======================================================================= ACT 1: HOUSE (jumps)
def act_house():
    world((0.45, 0.65, 0.95), 1.0)
    sun(4.0, (14, 12, 3), (0, 0, -1))
    light('AREA', "ceilfill", 260, (1.0, 0.95, 0.9), (0, 2.6, 0), (0, 0, 0), size=6)
    light('AREA', "winfill", 220, (0.85, 0.92, 1.0), (4.2, 1.5, 0), (0, 1.2, 0), size=3.0, size_y=1.4)
    S = []; W1, W2 = 0xf1ebe0, 0xe9e1d2; H = 2.7
    S.append(box("back", 9, H, 0.2, W1, (0, H / 2, 4.5))); S.append(box("left", 0.2, H, 9, W2, (-4.5, H / 2, 0)))
    # window wall (+x)
    S.append(box("ww_low", 0.2, 0.8, 9, W2, (4.5, 0.4, 0))); S.append(box("ww_top", 0.2, 0.5, 9, W2, (4.5, 2.45, 0)))
    S.append(box("ww_l", 0.2, 1.4, 3.0, W2, (4.5, 1.5, -3.0))); S.append(box("ww_r", 0.2, 1.4, 3.0, W2, (4.5, 1.5, 3.0)))
    S.append(box("sill", 0.2, 0.06, 3.1, 0xffffff, (4.4, 0.82, 0)))
    # door wall (-z): opening at x 1.3..2.5
    S.append(box("dw_l", 5.8, H, 0.2, W1, (-1.6, H / 2, -4.5))); S.append(box("dw_r", 2.0, H, 0.2, W1, (3.5, H / 2, -4.5)))
    S.append(box("dw_top", 1.2, 0.6, 0.2, W1, (1.9, 2.4, -4.5)))
    S.append(box("ceil", 9, 0.2, 9, 0xf6f2ec, (0, H + 0.1, 0))); S.append(box("ceil_lamp", 0.5, 0.08, 0.5, 0xfff3d6, (0, H - 0.02, 0), emit=3.0))
    S.append(box("floor", 9, 0.1, 9, 0xc29466, (0, -0.05, 0)))
    for i in range(18): S.append(box(f"board{i}", 0.02, 0.003, 9, 0xa87a50, (-4.5 + i * 0.5, 0.001, 0)))
    S.append(box("rug", 2.4, 0.012, 1.6, 0x8a6f9f, (0.2, 0.006, 0.6)))
    # bed, nightstand, wardrobe, desk
    S.append(box("bedframe", 1.7, 0.35, 2.1, 0x6e4a30, (-3.4, 0.25, 2.8), bevel=0.02)); S.append(box("mattress", 1.6, 0.25, 2.0, 0xf3f1ec, (-3.4, 0.55, 2.8), bevel=0.05))
    S.append(box("blanket", 1.64, 0.07, 1.2, 0x5f8fae, (-3.4, 0.7, 2.4), bevel=0.03)); S.append(box("pillow", 0.75, 0.15, 0.42, 0xffffff, (-3.4, 0.76, 3.55), bevel=0.06))
    S.append(box("headb", 1.75, 1.0, 0.1, 0x6e4a30, (-3.4, 0.6, 3.9), bevel=0.02))
    S.append(box("wardrobe", 1.4, 2.1, 0.6, 0x7d5a3c, (-2.6, 1.05, -4.1), bevel=0.02))
    S.append(box("desk", 1.4, 0.06, 0.7, 0x8a6a4c, (3.5, 0.75, 2.8))); S.append(box("deskleg", 1.3, 0.72, 0.6, 0x7a5a3c, (3.5, 0.36, 2.8)))
    S.append(box("laptop", 0.4, 0.02, 0.28, 0x2a2e33, (3.4, 0.79, 2.8))); S.append(box("chair", 0.5, 0.5, 0.5, 0x3e5c6e, (3.0, 0.25, 2.2), bevel=0.04))
    S.append(box("frame", 0.9, 0.6, 0.04, 0x2a3440, (-1.0, 1.7, 4.38))); S.append(box("art", 0.8, 0.5, 0.02, 0xd98c5f, (-1.0, 1.7, 4.36)))
    S.append(box("pot", 0.3, 0.35, 0.3, 0xb85c38, (3.9, 0.175, -3.6))); S.append(ico("plant", 0.35, 0x3f7d3a, (3.9, 0.62, -3.6)))
    S.append(box("ball", 0.24, 0.24, 0.24, 0xe07a2e, (-1.8, 0.12, -2.4), bevel=0.1))
    # outside: lawn, street, houses opposite, trees (seen through window and door)
    gp = bpy.data.meshes.new("og"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200); bm.to_mesh(gp); bm.free()
    go = link(bpy.data.objects.new("og", gp)); go.data.materials.append(mat(0x79a552, 0.95)); go.location = (0, 0, -0.06)
    S.append(box("ostreet", 200, 0.02, 7, 0x4a4c52, (0, 0.0, -14)))
    for i in range(10):
        x = -40 + i * 10 + rnd.uniform(-1, 1); w, h = rnd.uniform(6, 8), rnd.uniform(3.5, 6)
        S.append(box(f"oh{i}", w, h, 7, [0xe8dccb, 0xd9c7b0, 0xc9d4dc][i % 3], (x, h / 2, -24)))
        S.append(box(f"ohr{i}", w + 0.6, 0.6, 7.6, [0xa04a38, 0x5a6470][i % 2], (x, h + 0.3, -24)))
    for i in range(30):
        x, z, th = rnd.uniform(-30, 40), rnd.choice((rnd.uniform(-19, -9), rnd.uniform(9, 30))), rnd.uniform(2.5, 4)
        if abs(z) < 6: continue
        S.append(box(f"tt{i}", 0.3, th, 0.3, 0x5a4030, (x if z < 0 else rnd.uniform(9, 40), th / 2, z)))
        S.append(ico(f"tc{i}", rnd.uniform(1.1, 1.7), [0x4f8a3c, 0x5a9440][i % 2], (x if z < 0 else S[-1].location.x, th + 0.8, z)))
    # door panel (hinged at x=1.3)
    door = empty("doorpiv", (1.3, 0, -4.5)); box("doorpanel", 1.2, 2.1, 0.05, 0x8a5a3a, (0.6, 1.05, 0), parent=door, bevel=0.01)
    box("knob", 0.06, 0.06, 0.08, 0xd0b060, (1.05, 1.0, -0.05), parent=door)
    # scale + shoes
    scl = empty("scale", (0, 0, -0.1))
    box("scale_body", 0.5, 0.05, 0.5, 0xeef1f4, (0, 0.025, 0), parent=scl, bevel=0.015, rough=0.35)
    box("scale_win", 0.22, 0.004, 0.08, 0x0b1014, (0, 0.051, -0.19), parent=scl, rough=0.2)
    segs = {}
    for di in range(3):
        cx = -0.06 + di * 0.06
        for s, (sx, sz, w, d) in {"a": (0, -0.025, 0.026, 0.005), "g": (0, 0, 0.026, 0.005), "d": (0, 0.025, 0.026, 0.005), "f": (-0.015, -0.0125, 0.005, 0.022),
                                   "b": (0.015, -0.0125, 0.005, 0.022), "e": (-0.015, 0.0125, 0.005, 0.022), "c": (0.015, 0.0125, 0.005, 0.022)}.items():
            segs[(di, s)] = box(f"seg{di}{s}", w, 0.002, d, 0x7ff0d8, (cx + sx, 0.054, -0.19 + sz), parent=scl, emit=6)
    stand = empty("stand")
    for s in (-1, 1):
        fx, fz = s * 0.09, -0.05
        shoe = empty(f"shoe{s}", (fx, 0.06, fz)); shoe.parent = stand
        box("sole", 0.112, 0.03, 0.29, 0xf4f4f2, (0, 0.015, -0.01), parent=shoe, bevel=0.014)
        box("upper", 0.1, 0.075, 0.2, 0x2f4a66, (0, 0.07, 0.03), parent=shoe, bevel=0.035)
        box("toe", 0.1, 0.05, 0.09, 0x2f4a66, (0, 0.05, -0.1), parent=shoe, bevel=0.028)
        box("toecap", 0.104, 0.028, 0.05, 0xf4f4f2, (0, 0.03, -0.14), parent=shoe, bevel=0.013)
        for k in range(4): box("lace", 0.055, 0.008, 0.01, 0xffffff, (0, 0.11, -0.04 + k * 0.03), parent=shoe)
        limb(f"jean{s}", B(fx, 0.18, fz + 0.08), B(fx + s * 0.02, 1.03, fz + 0.16), 0.055, 0.072, 0x3d5a80, stand)
    merge_static("house_static", S); bake_modifiers(scene)
    cam = camera(60); hL, hR = hand(cam, -1), hand(cam, 1)
    keyat(door, "rotation_euler", (0, 0, 0), 35.2); keyat(door, "rotation_euler", (0, 0, -1.7), 36.8)
    SEGS = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
    EYE = 1.62
    P_SCALE, L_SCALE = Vector((0, EYE, 0.5)), Vector((0, 0, -0.12))
    def state(t):
        p, l, roll = P_SCALE.copy(), L_SCALE.copy(), 0.0
        if 3.9 < t < 4.8: p.y += 0.07 * math.sin((t - 3.9) / 0.9 * math.pi)           # hour one: you bob up off your heels
        if 13.3 < t < 14.1: p.y += 0.05 * math.sin((t - 13.3) / 0.8 * math.pi)
        p.y += 0.006 * math.sin(t * 1.3)
        lk = sm((t - 13.4) / 2.0); l = l.lerp(Vector((4.5, 1.5, -0.5)), lk)                 # look up at the window
        lk2 = sm((t - 17.5) / 2.0); l = l.lerp(Vector((0.3, 1.0, -2.0)), lk2)               # look at your hands
        lk3 = sm((t - 20.6) / 1.6); l = l.lerp(Vector((0.2, 2.2, -4.5)), lk3)               # look ahead and up
        if 22.6 < t < 24.0: p.y -= 0.28 * math.sin(cl((t - 22.6) / 1.4) * math.pi / 2)      # crouch
        if 24.0 <= t:
            if t < 24.55: k = (t - 24.0) / 0.55; p.y = lerp(EYE - 0.28, H - 0.14, 1 - (1 - k) ** 2)
            elif t < 27.2: k = (t - 24.55) / 2.65; p.y = lerp(H - 0.14, EYE, k * k)          # slow fall back down
            if 24.55 < t < 25.4: p += shake(t, 0.03 * (1 - (t - 24.55) / 0.85), 31); roll = 0.08 * math.sin((t - 24.55) * 9) * (1 - (t - 24.55) / 0.85)
            if 24.4 < t < 26.2: l = l.lerp(Vector((0.2, 2.9, -0.6)), math.sin(cl((t - 24.4) / 1.8) * math.pi) * 0.8)   # glance at the ceiling
            if 27.2 < t < 27.8: p.y -= 0.06 * math.sin((t - 27.2) / 0.6 * math.pi)
        if t >= 31.4:                                                                        # one step: across the room
            k = cl((t - 31.4) / 2.3); a = Vector((0, EYE, 0.22)); b = Vector((1.8, EYE, -3.0))
            p = a.lerp(b, sm(k) * 0.3 + k * 0.7); p.y = EYE + 0.95 * math.sin(k * math.pi) - (0.22 if 31.0 < t < 31.6 else 0)
            l = Vector((1.9, 1.5, -6.0))
            if 33.7 < t < 34.6: p += shake(t, 0.025 * (1 - (t - 33.7) / 0.9), 29)
        if t >= 37.6:                                                                        # out of the door, bouncing
            k = cl((t - 37.6) / 4.4); p = Vector((1.85, EYE, -3.0)).lerp(Vector((1.9, EYE, -9.0)), k)
            p.y = EYE + 0.45 * abs(math.sin((t - 37.6) * 1.6)); l = Vector((1.0, 1.8, -20))
        return p, l, roll
    def frame(t, f):
        p, l, roll = state(t); cam_key(cam, p, l, f, roll)
        show = t > 14.0
        vis(hL, not show, f); vis(hR, not show, f)
        if 17.2 < t < 21.0:   # make fists, flex
            k = math.sin(cl((t - 17.2) / 3.8) * math.pi); hands_pose(hL, hR, f, hx=lerp(0.3, 0.2, k), hy=lerp(-0.24, -0.1, k), hz=-0.5, rx=lerp(-0.25, 0.5, k))
        elif 24.2 < t < 26.4:  # arms up against the ceiling
            k = math.sin(cl((t - 24.2) / 2.2) * math.pi); hands_pose(hL, hR, f, hx=lerp(0.3, 0.38, k), hy=lerp(-0.24, 0.12, k), hz=lerp(-0.5, -0.42, k), rx=lerp(-0.25, 1.2, k))
        elif 31.4 < t < 34.0:  # arms flail during the leap
            k = math.sin(cl((t - 31.4) / 2.6) * math.pi); hands_pose(hL, hR, f, hx=0.3 + 0.14 * k, hy=-0.24 + 0.16 * k, rx=-0.25 + 0.6 * k)
        else: hands_pose(hL, hR, f)
        vis(stand, t > 14.0, f)
        m = TL.mass_at(t)
        dg = [None if ch == " " else int(ch) for ch in str(int(round(m))).rjust(3)[-3:]]
        for di in range(3):
            on = SEGS[dg[di]] if dg[di] is not None else ""
            for s in "abcdefg": vis(segs[(di, s)], s not in on, f, recursive=False)
    return frame

# ======================================================================= ACT 2: STREET (blown away)
def act_street():
    world((0.5, 0.68, 0.95), 1.1)
    sun(4.5, (30, 25, 20), (0, 0, 0))
    stat, trees, poles = street(rows=18, start_z=4.0)
    merge_static("street_static", stat); bake_modifiers(scene)
    for tg, ph in list(trees):
        if abs(-tg.location.y - poles[4]) < 6 and tg.location.x > 0:
            for o in [tg] + list(tg.children_recursive): bpy.data.objects.remove(o, do_unlink=True)
            trees.remove((tg, ph))
    lv = leaves(220)
    cam = camera(62); hL, hR = hand(cam, -1), hand(cam, 1)
    legs = link(bpy.data.objects.new("legs", None), cam)
    for sd in (-1, 1):
        lg = link(bpy.data.objects.new(f"leg{sd}", None), legs); lg.location = (sd * 0.11, -0.55, 0.15)
        limb("thigh", (0, 0, 0), (0, -0.85, 0.12), 0.08, 0.065, 0x3d5a80, lg)
        bx = box("shoe", 0.11, 0.09, 0.28, 0x2f4a66, (0, 0, 0), parent=lg, bevel=0.03); bx.location = (0, -0.06, -0.9)
        legs[f"s{sd}"] = lg.name
    GRAB_Z = poles[4]                       # pole you end up holding
    PX = 5.8
    EYE = 1.62
    def wind(t):   # 0 calm .. 1 gale
        return cl((t - 51.5) / 2) * (0.6 + 0.4 * math.sin(t * 0.37) ** 2) * (1.0 if t < 66 else 1.25)
    def body(t):
        """camera position, look target, roll, holding?"""
        if t < E["blown"]:   # moon-walk down the sidewalk
            s = (t - 42) / 2.2; ph = s % 1.0
            z = 1.0 - (t - 42) * 1.25 - (0.0 if t < 52 else (t - 52) * 0.4)
            y = EYE + 0.75 * math.sin(ph * math.pi) * (1 - 0.3 * cl((t - 52) / 10))
            x = 3.8 + (0.4 * sm((t - 52) / 3) if t > 52 else 0)
            look = Vector((2.6, 1.6, z - 20))
            if 52 < t < 60: look = look.lerp(Vector((-3, 3.5, z - 8)), math.sin(cl((t - 52) / 8) * math.pi) * 0.6)   # leaves fly past
            return Vector((x, y, z)), look, 0.0, False
        z0 = 1.0 - (E["blown"] - 42) * 1.25 - (E["blown"] - 52) * 0.4
        gz = GRAB_Z + 0.5
        if t < E["grab"]:    # carried down the street, tumbling
            k = (t - E["blown"]) / (E["grab"] - E["blown"]); kk = 1 - (1 - k) ** 1.6
            z = lerp(z0, gz, kk); y = EYE + 1.1 * math.sin(k * math.pi) + 0.2 * math.sin(t * 5)
            x = lerp(4.2, PX - 0.55, sm(k))
            roll = 0.5 * math.sin(t * 2.3) * math.sin(k * math.pi)
            look = Vector((x - 1.5 * math.sin(t * 1.7), y - 0.4, z - 12))
            return Vector((x, y, z)), look, roll, False
        # holding the pole, downwind of it, facing back into the wind; each hour the wind lifts your body more
        lift = sm((t - 76) / 30) * 0.45 + 0.5 * sm((t - 112) / 10)
        sway = 0.10 * math.sin(t * 2.1) + 0.05 * math.sin(t * 5.3)
        y = 1.35 + lift + sway * 0.4
        if t > E["lift"]: y += 1.8 * sm((t - E["lift"]) / 7) ** 1.5 + 0.6 * cl((t - 122.5) / 2.5)
        x = PX - 0.32 + 0.04 * math.sin(t * 1.3); z = GRAB_Z - 0.62 - 0.12 * lift - 0.06 * sway
        if t < E["grab"] + 0.6:   # swing in from the tumble
            k = sm((t - E["grab"]) / 0.6); x = lerp(PX - 0.55, x, k); z = lerp(gz, z, k)
        look = Vector((PX - 0.1, y - 0.15, GRAB_Z + 6))
        if 95 < t < 104: look = look.lerp(Vector((PX - 0.4, -0.3, z - 0.6)), math.sin(cl((t - 95) / 9) * math.pi) * 0.8)   # look down: feet off the ground
        if t > E["lift"]: look = look.lerp(Vector((PX - 0.6, 0.0, z - 3)), sm((t - E["lift"]) / 4) * 0.7)
        if 72 < t < 73.2: return Vector((x, y, z)) + shake(t, 0.03 * (1 - (t - 72) / 1.2), 25), look, 0.0, True
        return Vector((x, y, z)), look, 0.03 * math.sin(t * 2.1), True
    def frame(t, f):
        p, l, roll, hold = body(t); cam_key(cam, p, l, f, roll)
        vis(hL, False, f); vis(hR, False, f); vis(legs, not hold, f)
        for sd in (-1, 1):
            lg = bpy.data.objects[legs[f"s{sd}"]]; lg.rotation_euler = (0.25 * math.sin(t * 2.4 + sd), 0, 0.15 * math.sin(t * 1.9 + sd * 2)); key(lg, "rotation_euler", f)
        if hold:   # both hands forward-right, gripping
            let_go = sm((t - 122.0) / 1.5)
            for h, s in ((hL, -1), (hR, 1)):
                h.location = (-0.2 + s * 0.07, -0.12 + s * 0.06 - 0.15 * let_go, -0.66 + 0.15 * let_go); h.rotation_euler = (0.25 - 0.6 * let_go, 0.42 - 0.2 * let_go, s * 0.12)
                key(h, "location", f); key(h, "rotation_euler", f)
        elif t > E["blown"]:
            k = t * 3; hands_pose(hL, hR, f, hx=0.36, hy=-0.05 + 0.08 * math.sin(k), hz=-0.48, rx=0.6 + 0.3 * math.sin(k * 1.3))
        else:
            hands_pose(hL, hR, f, hy=-0.24 + 0.05 * math.sin((t - 42) / 2.2 * math.pi * 2))
        w = wind(t)
        for tg, ph in trees:
            loc = tg.location
            if abs(-loc.y - p.z) > 60: continue
            tg.rotation_euler = (-(0.04 + 0.05 * w) * w - 0.03 * w * math.sin(t * 2.4 + ph), 0.01 * math.sin(t * 1.7 + ph), 0); key(tg, "rotation_euler", f)
        for q in lv:   # leaves and paper blowing down the street (toward -z)
            sp = (2 + 18 * w) * q["sp"]
            z = p.z + 25 - ((t * sp + q["ph"] * 20 - q["z"]) % 85)
            y = q["y"] + 0.6 * math.sin(t * 3 * q["sp"] + q["ph"]) if w > 0.05 else 0.02
            x = q["x"] + 0.8 * math.sin(t * 1.3 + q["ph"]) * w
            if w <= 0.05: z = q["z"] + p.z * 0
            q["o"].location = B(x, y, z); q["o"].rotation_euler = (t * 4 * q["sp"] * w, t * 3 * w + q["ph"], t * 2 * w); key(q["o"], "location", f); key(q["o"], "rotation_euler", f)
    return frame


# ======================================================================= ACT 3: ASCENT (through the sky)
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

R_EARTH = 6.371e6
def earth_ball(name, R, center, sub=6, seed=4, cities=False):
    from mathutils import noise
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=R)
    off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
    for fc in bm.faces:
        c = fc.calc_center_median().normalized()
        n = noise.fractal(c * 2.5 + off, 0.55, 2.0, 4); n2 = noise.fractal(c * 60 + off, 0.6, 2.0, 3)
        if n < -0.05 and c.z < 0.985: idx = 5              # ocean (home region stays land)
        elif c.z < -0.9: idx = 6
        else: idx = (0, 1, 2, 3, 4)[min(4, max(0, int((n2 + 0.6) * 4)))]
        if cities and idx < 5 and noise.noise(c * 90 + off) > 0.62: idx = 7
        fc.material_index = idx
    bm.to_mesh(me); bm.free()
    for col in (0x5c8a42, 0x6f9a4a, 0x86a855, 0x9c9a5e, 0xb5a46a, 0x2f5f9a, 0xe9eef2): me.materials.append(mat(col, 0.95))
    me.materials.append(mat(0x7a8a5a, 0.95, emit=0.5, emit_col=0xffb060))
    ob = link(bpy.data.objects.new(name, me)); ob.location = B(*center); return ob

def cloud(name, pos, size, rr):
    parts = []
    for k in range(rr.randint(4, 7)):
        o = ico(f"{name}{k}", size * rr.uniform(0.35, 0.6), 0xf7f8fa, (pos[0] + rr.uniform(-1, 1) * size * 0.7, pos[1] + rr.uniform(0, 0.25) * size, pos[2] + rr.uniform(-1, 1) * size * 0.5), sub=1)
        o.scale = (1.0, 1.0, 0.6); parts.append(o)
    return parts

def act_ascent():
    SUN = Vector((0.75, 0.32, -0.58)).normalized()          # design space
    sd = B(*SUN)
    W = sky_world(tuple(sd))
    sunl = sun(4.0, (0, 0, 0), tuple(-SUN), color=(1.0, 0.93, 0.82), angle=0.6)
    sunl.location = B(*(SUN * 10)); look_rot(sunl, B(*(SUN * 10)), B(0, 0, 0))
    earth_ball("earth", R_EARTH, (0, -R_EARTH - 140, 0), sub=7)
    # fields patch (60 km) + town (1.6 km) around the start point
    me = bpy.data.meshes.new("fields"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=90, y_segments=90, size=30000)
    rr = random.Random(7)
    for fc in bm.faces: fc.material_index = rr.choice((0, 0, 1, 1, 2, 3, 4))
    bm.to_mesh(me); bm.free()
    for col in (0x6f9a4a, 0x86a855, 0x76a04e, 0x9c9a5e, 0x80a050): me.materials.append(mat(col, 0.95))
    link(bpy.data.objects.new("fields", me)).location = (0, 0, 0.5)
    S = [box("townbase", 1800, 0.5, 1800, 0x9aa08c, (0, 0.8, 0))]
    for i in range(-15, 16):
        S.append(box(f"rx{i}", 1800, 0.3, 8, 0x4a4c52, (0, 1.2, i * 60))); S.append(box(f"rz{i}", 8, 0.3, 1800, 0x4a4c52, (i * 60, 1.2, 0)))
    for i in range(-14, 15):
        for j in range(-14, 15):
            if rr.random() < 0.12: S.append(box(f"park{i}{j}", 50, 0.4, 50, 0x5a9440, (i * 60 + 30, 1.1, j * 60 + 30))); continue
            for k in range(4):
                h = rr.uniform(4, 8); S.append(box(f"h{i}{j}{k}", 14, h, 12, [0xe8dccb, 0xd9c7b0, 0xc9d4dc, 0xa04a38, 0x5a6470][rr.randint(0, 4)],
                                                 (i * 60 + 30 + (k % 2 - 0.5) * 24, h / 2 + 1, j * 60 + 30 + (k // 2 - 0.5) * 24)))
    for k in range(12):   # a river and a highway through the fields
        S.append(box(f"river{k}", 260, 1.0, 5000, 0x3f6f9a, (-6000 + k * 900 * 0.3, 0.9, -28000 + k * 5000)))
    S.append(box("highway", 30, 1.0, 60000, 0x55575c, (2500, 1.0, 0)))
    crr = random.Random(9)
    for i in range(110):
        a, d = crr.random() * math.tau, crr.uniform(800, 28000)
        S += cloud(f"cl{i}", (math.cos(a) * d, crr.uniform(1600, 3200), math.sin(a) * d), crr.uniform(250, 900), crr)
    gs = merge_static("ground_static", S); fo = bpy.data.objects["fields"]
    for o in (gs, fo): keyat(o, "hide_render", False, 1); keyat(o, "hide_render", True, 168.5)   # swapped out while you look up
    sdisc = ico("sundisc", 70000, 0, tuple(SUN * 4.0e6), sub=3, material=emission_mat(0xfff4dc, 40.0)); sdisc.visible_shadow = False
    # jet with contrail
    jet = empty("jet")
    box("fus", 4, 4, 38, 0xf2f2f2, (0, 0, 0), parent=jet, bevel=1.0); box("wing", 36, 0.6, 7, 0xdcdcdc, (0, 0, 2), parent=jet)
    box("tail", 0.6, 7, 4, 0x2a5fa8, (0, 4, 16), parent=jet); box("stab", 13, 0.4, 3.5, 0xdcdcdc, (0, 0.8, 16.5), parent=jet)
    trail = [limb(f"trail{k}", (k * 9.0 - 9, -60, 0), (k * 9.0 - 9, -6060, 0), 3, 9, 0, material=emission_mat(0xffffff, 1.4), parent=jet) for k in range(2)]
    # meteors: long glowing streaks
    mets = []
    for i in range(14):
        o = limb(f"met{i}", (0, 0, 0), (0, 0, 2500), 4, 40, 0, material=emission_mat([0xfff0c0, 0xffb060, 0xa0ffd0][i % 3], 18.0))
        mets.append(dict(o=o, t0=E["meteors"] + i * 0.55 + rnd.uniform(0, 0.3), a=rnd.uniform(-0.6, 0.6), d=rnd.uniform(6000, 22000), dy=rnd.uniform(-9000, 3000), side=rnd.choice((-1, 1))))
    for o in [jet] + list(jet.children_recursive) + [m_['o'] for m_ in mets]: o.visible_shadow = False
    cam = camera(64); cam.data.clip_end = 2.0e7
    LOOKS = [(125, (0.05, -1, -0.35)), (129, (0.2, -0.75, -0.6)), (132, (0.25, -0.15, -1)), (139, (0.3, -0.2, -1)), (144, (0.1, -0.7, -0.6)),
             (146.5, (0.25, -0.85, -0.45)), (152, (0.25, -0.6, -0.75)), (156, (0.4, -0.1, -1)), (164, (0.6, -0.12, -0.8)), (166.5, (0.2, 0.85, -0.45)),
             (172, (0.2, 0.75, -0.6)), (176, (-0.2, -0.45, -1)), (186, (-0.5, -0.35, -0.9)), (198, (0.0, -0.25, -1)), (205, (-0.2, -0.15, -1)),
             (209, tuple(SUN * 1.0 + Vector((0, -0.05, 0)))), (215, tuple(SUN))]
    def frame(t, f):
        alt = TL.altitude_vis(t) * 1000.0
        p = Vector((40 * math.sin(t * 0.05), max(alt, 30.0), -60 * (t - 125) - 2 * alt * 0))
        d = track(LOOKS, t).normalized()
        cam_key(cam, p, p + d * 100, f, roll=0.03 * math.sin(t * 0.3))
        cam.data.clip_start = max(0.3, alt * 0.01); cam.data.keyframe_insert("clip_start", frame=f)
        a_km = alt / 1000
        # sky: blue -> deep blue -> black; horizon band dips and thins; stars after ~35 km
        k1, k2 = sm(a_km / 14), sm((a_km - 14) / 30)
        sky = Vector((0.42, 0.62, 0.92)).lerp(Vector((0.08, 0.16, 0.42)), k1).lerp(Vector((0.0, 0.0, 0.01)), k2)
        kv(W["sky"], (*sky, 1), f)
        dip = math.sqrt(2 * max(alt, 1) / R_EARTH)
        kv(W["dip"], dip, f); kv(W["glow"], lerp(0.35, 1.6, k1) * (1 - 0.35 * k2), f)
        kv(W["hcol"], (*Vector((0.75, 0.85, 1.0)).lerp(Vector((0.35, 0.6, 1.0)), k1), 1), f)
        kv(W["stars"], 3.0 * sm((a_km - 30) / 25), f)
        kv(W["sunglow"], 0.4 + 0.6 * k2 + 1.6 * sm((t - E["sunpush"] + 4) / 5), f)
        # jet: crosses below you at ~11.8 km
        jt = (t - E["jet"] + 2) / 9
        jp = Vector((lerp(-2600, 2600, jt), 11800, p.z - 900))
        jet.location = B(*jp); jet.rotation_euler = (0, 0, -math.pi / 2); key(jet, "location", f); key(jet, "rotation_euler", f)
        vis(jet, not (-0.05 < jt < 1.05), f)
        for mt in mets:   # each meteor streaks for ~0.9 s, burning out
            k = (t - mt["t0"]) / 0.9
            on = 0 < k < 1
            if on:
                c = p + Vector((mt["side"] * mt["d"] * 0.6, mt["dy"], -mt["d"]))
                c += Vector((mt["side"] * -1, -0.35, mt["a"])).normalized() * (k * 9000)
                mt["o"].location = B(*c); mt["o"].rotation_quaternion = (B(*Vector((mt["side"] * -1, -0.35, mt["a"])).normalized())).to_track_quat('Z', 'Y')
                s_ = math.sin(k * math.pi); mt["o"].scale = (s_ + 0.01, s_ + 0.01, 0.4 + s_)
            else: mt["o"].scale = (0.001,) * 3
            key(mt["o"], "location", f); key(mt["o"], "rotation_quaternion", f); key(mt["o"], "scale", f)
    return frame

# ======================================================================= ACT 4: SAIL (pushed out by sunlight)
def banded_planet(name, R, cols, bands=14, sub=4, jitter=0.0, seed=1):
    from mathutils import noise
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=R)
    off = Vector((seed, seed * 2, seed * 3))
    for fc in bm.faces:
        c = fc.calc_center_median().normalized()
        b = int((c.z + 1) / 2 * bands + jitter * noise.noise(c * 4 + off) * 3)
        fc.material_index = b % len(cols)
    bm.to_mesh(me); bm.free()
    for col in cols: me.materials.append(mat(col, 0.9))
    return link(bpy.data.objects.new(name, me))

def ring(name, r0, r1, cols, segs=128):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); n = len(cols)
    for j in range(n):
        ra, rb = lerp(r0, r1, j / n), lerp(r0, r1, (j + 1) / n)
        if cols[j] is None: continue
        for i in range(segs):
            a0, a1 = i / segs * math.tau, (i + 1) / segs * math.tau
            fc = bm.faces.new([bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)) for a, r in ((a0, ra), (a1, ra), (a1, rb), (a0, rb))]); fc.material_index = j
    bm.to_mesh(me); bm.free()
    for col in cols: me.materials.append(mat(col if col is not None else 0, 0.8))
    return link(bpy.data.objects.new(name, me))

def streaks(n, color=0xdfe8ff, strength=4.0):
    out = []
    for i in range(n):
        o = box(f"spd{i}", 1, 1, 1, 0, (0, 0, 0), material=emission_mat(color, strength)); o.visible_shadow = False
        out.append(dict(o=o, a=rnd.random() * math.tau, r=rnd.uniform(0.2, 1.0), ph=rnd.random()))
    return out

def place_streaks(sts, p, F, U, Rv, t, v, f, radius=60.0, L=400.0, thick=0.5):
    """dust specks streaming past the camera (moving -F at speed v); stretched with speed."""
    side = F.cross(U).normalized()
    for q in sts:
        z = L / 2 - ((q["ph"] * L + t * v) % L)
        pos = p + F * z + (side * math.cos(q["a"]) + U * math.sin(q["a"])) * q["r"] * radius
        q["o"].location = B(*pos); q["o"].rotation_quaternion = B(*F).to_track_quat('Z', 'Y'); q["o"].rotation_mode = 'QUATERNION'
        ln = thick + min(v * 0.05, L * 0.35)
        q["o"].scale = (thick, thick, ln) if v > 0.01 else (0.001,) * 3
        key(q["o"], "location", f); key(q["o"], "rotation_quaternion", f); key(q["o"], "scale", f)

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

def act_sail():
    world((0.0, 0.0, 0.004), 1.0, stars=True)
    SUN = Vector((0.75, 0.32, -0.58)).normalized(); F = -SUN            # sunlight pushes you straight away from the Sun
    U = Vector((0, 1, 0)); U = (U - F * U.dot(F)).normalized()
    sl = sun(5.0, tuple(SUN * 10), (0, 0, 0), color=(1.0, 0.95, 0.88), angle=0.5)
    fill = sun(0.35, (0, 10, 0), (0, 0, 0), color=(0.6, 0.7, 1.0), angle=5); fill.data.use_shadow = False
    earth_ball("earth", 6371.0, (0, 0, 0), sub=5, cities=True)
    atmo = ico("atmo", 6371.0 * 1.012, 0, (0, 0, 0), sub=5, smooth=True, material=rim_mat(0x5a9cff, 3.0)); atmo.visible_shadow = False
    moon = ico("moon", 1737, 0xbcbcc2, tuple(F * 384400 + F.cross(U).normalized() * 4500 + U * 1200), sub=4)
    sdisc = ico("sundisc", 1.0, 0, (0, 0, 0), sub=3, material=emission_mat(0xfff4dc, 30.0)); sdisc.visible_shadow = False
    side = F.cross(U).normalized()
    planets = []
    def add_planet(ob, R, te, off_dir, rings=None):
        ob.visible_shadow = True; planets.append(dict(o=ob, R=R, tc=te + 1.2, off=off_dir.normalized(), rings=rings))
    mars = banded_planet("mars", 3390, (0xc1592f, 0xb04a26, 0xd0703c, 0x9c4224, 0xe8e0d8), bands=9, jitter=1.0, seed=2); add_planet(mars, 3390, E["mars"], side * 1 + U * 0.3)
    jup = banded_planet("jupiter", 69911, (0xd9b38c, 0xc08a5a, 0xefe0c4, 0xb07850, 0xe8cfa8, 0xa86a44), bands=17, jitter=0.25, seed=3); add_planet(jup, 69911, E["jupiter"], -side + U * 0.2)
    sat = banded_planet("saturn", 58232, (0xe6d3a3, 0xd6bf88, 0xf0e2bc, 0xc8ad78), bands=13, jitter=0.2, seed=4)
    rg = ring("saturn_ring", 74000, 137000, (0xd8c49a, 0xbfae88, None, 0xe2d2ae, 0xcbb890, 0xb6a47e)); rg.parent = sat; rg.rotation_euler = (0.45, 0.2, 0)
    add_planet(sat, 58232, E["saturn"], side * 1.1 - U * 0.25, rings=rg)
    nep = banded_planet("neptune", 24622, (0x3a62c4, 0x4a74d6, 0x2f54ae, 0x5a86e0), bands=8, jitter=0.6, seed=5); add_planet(nep, 24622, E["neptune"], -side * 0.9 - U * 0.3)
    for pl in planets: pl["o"].rotation_euler = (math.radians(70), 0.3, 0)
    sts = streaks(140)
    cam = camera(62); cam.data.clip_start = 5.0; cam.data.clip_end = 5.0e7
    S_KEYS = [(215, 0.0), (222, 150.0), (230, 1500.0), (236, 12000.0), (242, 70000.0), (246, 220000.0), (249, 384400.0), (253, 1.0e6), (260, 3.0e6), (305, 6.0e7)]
    def s_of(t):
        for (t0, a), (t1, b) in zip(S_KEYS, S_KEYS[1:]):
            if t <= t1: k = (t - t0) / (t1 - t0); return math.exp(math.log(max(a, 1.0)) + (math.log(b) - math.log(max(a, 1.0))) * k) if a > 0 else b * k ** 2
        return S_KEYS[-1][1]
    home = Vector((0, 6371 + 93, 0))
    def frame(t, f):
        p = home + F * s_of(t)
        # where to look
        to_earth = (Vector((0, 0, 0)) - p).normalized()
        d = (to_earth * 0.6 + SUN * 0.7).normalized()                                 # Earth below, Sun up ahead
        d = d.lerp(to_earth, sm((t - 223) / 4) * 0.8)                                  # watch Earth fall away
        d = d.lerp((to_earth + U * 0.15).normalized(), sm((t - 236) / 3))
        moonv = (Vector(moon.location.x for _ in ()) if False else None)
        if t > 244: d = d.lerp(F, sm((t - 249.5) / 3.0))                                # turn forward, toward the outer planets
        if 244 < t < 251:   # the Moon slides past
            mpos = F * 384400 + side * 4500 + U * 1200; d = d.lerp((mpos - p).normalized(), math.sin(cl((t - 244) / 7) * math.pi) * 0.6)
        if 258 < t < 265: d = d.lerp(-F + U * 0.1, math.sin(cl((t - 258) / 7) * math.pi))   # look back: the Sun, smaller
        for pl in planets:   # follow each planet as it passes
            k = (t - (pl["tc"] - 4.0)) / 6.5
            if 0 < k < 1:
                rel = F * (pl["R"] * 7.0 * (pl["tc"] - t)) + pl["off"] * pl["R"] * 2.6
                d = d.lerp((rel).normalized(), math.sin(k * math.pi) * 0.45)
        d = d.normalized()
        cam_key(cam, p, p + d * 1000, f, roll=0.02 * math.sin(t * 0.2))
        # Sun disc behind you, shrinking with distance from the Sun
        b, au, te = TL.sail_state(TL.hour_at(t)) if TL.hour_at(t) >= 30 else (0, 1.0, 0)
        dist = 4.0e6; rad = dist * math.tan(math.radians(0.27) / max(au, 1.0)) * 1.6
        sdisc.location = B(*(p + SUN * dist)); sdisc.scale = (rad,) * 3; key(sdisc, "location", f); key(sdisc, "scale", f)
        for pl in planets:
            rel = F * (pl["R"] * 7.0 * (pl["tc"] - t)) + pl["off"] * pl["R"] * 2.6
            on = -5.0 < t - pl["tc"] < 3.0
            pl["o"].location = B(*(p + rel)); key(pl["o"], "location", f); vis(pl["o"], not on, f)
            pl["o"].rotation_euler = (math.radians(70), 0.3, t * 0.2); key(pl["o"], "rotation_euler", f)
        v = 0.0 if t < 236 else 40.0 + 2600.0 * sm((t - 236) / 69) ** 1.4
        place_streaks(sts, p, F, U, None, t, v, f, radius=900.0, L=12000.0, thick=3.0)
    return frame

ACTS = dict(house=act_house, street=act_street, ascent=act_ascent, sail=act_sail)

frame_fn = ACTS[ACT]()
f_lo, f_hi = F0, F1
if TIMES:
    frs = [fr(float(x)) for x in TIMES.split(",")]
    f_lo, f_hi = max(F0, min(frs) - 2), min(F1, max(frs) + 2)
elif FRAMES:
    a, b = map(int, FRAMES.split("-")); f_lo, f_hi = max(F0, a), min(F1, b)
for f in range(f_lo, f_hi + 1):
    frame_fn((f - 1) / FPS, f)
try: scene.eevee.shadow_pool_size = '1024'
except Exception: pass
setup_render(scene, OUT, RES, ENGINE, SAMPLES, DEVICE, FPS, f_lo, f_hi, exposure={"house": 0.35, "street": 0.2, "ascent": 0.1}.get(ACT, 0.0))
render(scene, TIMES.split(",") if TIMES else None, FPS)
print(f"[scene] act {ACT} done", flush=True)
