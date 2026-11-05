"""Blender scenes for 'What If You Got Heavier Every Hour' — one act per Blender process.
   blender -b -P scene.py -- --act NAME --out DIR [--res 1920x1080] [--engine eevee|cycles] [--samples N] [--times 2,11]
Frames are written with GLOBAL numbering (act start..end) so all acts share one folder."""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import timeline as TL
from pw3d import *  # noqa

get = args(sys.argv)
ACT = get("--act", "house"); OUT = get("--out", "/tmp/heavier_raw"); RES = get("--res", "1920x1080")
ENGINE = get("--engine", "eevee"); SAMPLES = int(get("--samples", "24")); DEVICE = get("--device", "gpu")
TIMES = get("--times"); FRAMES = get("--frames")
FPS = TL.FPS; E = TL.EVENTS_OLD   # scenes are written in the original timing; frames are mapped with TL.o()
A0, A1 = [(a, b) for n, a, b in TL.ACTS if n == ACT][0]
F0, F1 = int(round(A0 * FPS)) + 1, int(round(A1 * FPS))
scene = reset()
rnd = random.Random(hash(ACT) % 1000)

# ======================================================================= ACT 1: HOUSE
def act_house():
    world((0.42, 0.62, 0.92), 1.0)
    FY = 3.0
    sun(4.0, (14, 12, 3), (0, 3, -1))
    light('AREA', "winfill", 260, (0.85, 0.92, 1.0), (4.2, FY + 1.45, 0), (0, FY + 1.2, 0), size=3.2, size_y=1.4)
    light('AREA', "roomfill", 120, (1.0, 0.95, 0.88), (0, FY + 2.55, 0), (0, FY, 0), size=6)
    lamp = light('POINT', "lamp", 0, (1.0, 0.72, 0.45), (2.4, 1.75, -2.6), soft=0.2)
    light('AREA', "lowfill", 90, (1.0, 0.85, 0.7), (0, 2.6, 0), (0, 0, 0), size=5)
    pit = light('POINT', "pitlight", 0, (1.0, 0.7, 0.5), (0.2, -1.2, -1.0), soft=0.5)
    static = []
    S = lambda *a, **k: static.append(box(*a, **k))
    # lower room
    for nm, w, d, x, z in (("lw1", 9, 0.2, 0, -4.5), ("lw2", 9, 0.2, 0, 4.5), ("lw3", 0.2, 9, -4.5, 0), ("lw4", 0.2, 9, 4.5, 0)):
        S(nm, w, 2.75, d, 0xd8cbb4, (x, 1.375, z))
    S("sofa", 2.6, 0.45, 0.9, 0x3e5c6e, (1.6, 0.42, -3.7), bevel=0.06); S("sofab", 2.6, 0.55, 0.25, 0x36505f, (1.6, 0.85, -4.1), bevel=0.06)
    S("rug", 2.2, 0.02, 1.6, 0x9c4a3a, (2.6, 0.01, -2.9))
    S("lpole", 0.06, 1.5, 0.06, 0x222222, (2.4, 0.75, -2.6)); S("lshade", 0.42, 0.32, 0.42, 0xfff0d0, (2.4, 1.62, -2.6), emit=3.0)
    S("cab", 1.0, 0.6, 0.5, 0x5b4636, (-3.2, 0.3, 1.5), bevel=0.02); S("tv", 1.4, 0.8, 0.06, 0x111418, (-4.35, 1.4, 1.5), rough=0.3)
    S("shelf", 0.4, 1.8, 1.2, 0x7d5a3c, (4.2, 0.9, 1.0), bevel=0.02)
    # upper room
    W1 = 0xf1ebe0; W2 = 0xe9e1d2
    S("uw1", 9, 2.6, 0.2, W1, (0, FY + 1.3, -4.5)); S("uw2", 9, 2.6, 0.2, W1, (0, FY + 1.3, 4.5)); S("uw3", 0.2, 2.6, 9, W2, (-4.5, FY + 1.3, 0))
    S("ww_low", 0.2, 0.7, 9, W2, (4.5, FY + 0.35, 0)); S("ww_top", 0.2, 0.4, 9, W2, (4.5, FY + 2.4, 0))
    S("ww_l", 0.2, 1.5, 2.7, W2, (4.5, FY + 1.45, -3.15)); S("ww_r", 0.2, 1.5, 2.7, W2, (4.5, FY + 1.45, 3.15))
    S("sill", 0.16, 0.06, 3.6, 0xffffff, (4.42, FY + 0.72, 0)); S("mull", 0.08, 1.5, 0.07, 0xffffff, (4.45, FY + 1.45, 0))
    S("ceil", 9, 0.2, 9, 0xf6f2ec, (0, FY + 2.7, 0))
    S("rug2", 1.4, 0.012, 1.0, 0x8a6f9f, (1.9, FY + 0.006, 1.6))
    S("wardrobe", 1.4, 2.1, 0.6, 0x7d5a3c, (2.6, FY + 1.05, -4.1), bevel=0.02)
    S("frame", 0.9, 0.6, 0.04, 0x2a3440, (-1.0, FY + 1.7, 4.38)); S("art", 0.8, 0.5, 0.02, 0xd98c5f, (-1.0, FY + 1.7, 4.36))
    S("plant_pot", 0.3, 0.35, 0.3, 0xb85c38, (3.9, FY + 0.175, 1.9)); static.append(ico("plant", 0.35, 0x3f7d3a, (3.9, FY + 0.62, 1.9)))
    S("slipper1", 0.11, 0.05, 0.26, 0x9a4e5a, (0.55, FY + 0.025, 1.3), bevel=0.02); S("slipper2", 0.11, 0.05, 0.26, 0x9a4e5a, (0.75, FY + 0.025, 1.4), bevel=0.02)
    S("phone", 0.08, 0.012, 0.16, 0x15181c, (1.65, FY + 0.006, 0.55), rough=0.3)
    S("nightstand", 0.5, 0.55, 0.45, 0x6e4a30, (-0.35, FY + 0.275, -3.55), bevel=0.02); S("ns_lamp", 0.18, 0.25, 0.18, 0xfff3d6, (-0.35, FY + 0.68, -3.55), emit=1.5)
    # basement pit under the lower floor
    S("pitfloor", 7, 0.3, 7, 0x4a3524, (0.3, -2.85, -1.0), rough=1)
    for nm, w, d, x, z in (("pw1", 7, 0.3, 0.3, -4.5), ("pw2", 7, 0.3, 0.3, 2.5), ("pw3", 0.3, 7, -3.2, -1.0), ("pw4", 0.3, 7, 3.8, -1.0)):
        S(nm, w, 2.6, d, 0x5a4330, (x, -1.55, z), rough=1)
    for i in range(14):
        static.append(ico(f"stone{i}", rnd.uniform(0.08, 0.25), 0x6b5a48, (rnd.uniform(-2.5, 3), -2.65, rnd.uniform(-4, 2))))
    # outside (only seen through the window)
    gp = bpy.data.meshes.new("ground"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60); bm.to_mesh(gp); bm.free()
    go = link(bpy.data.objects.new("ground", gp)); go.data.materials.append(mat(0x6f9a4a, 0.95)); go.location = (64.8, 0, -0.05)
    for i in range(34):
        x, z, h = 9 + rnd.random() * 45, -25 + rnd.random() * 50, 2 + rnd.random() * 3
        S(f"trunk{i}", 0.35, h, 0.35, 0x5a4030, (x, h / 2, z))
        static.append(ico(f"crown{i}", 1.3 + rnd.random() * 1.3, [0x4f8a3c, 0x5a9440, 0x447a34][i % 3], (x, h + 0.9, z)))
    # breakable floors
    def make_floor(name, top, hole, cols):
        falling = []; T = 0.5
        for ix in range(-9, 9):
            for iz in range(-9, 9):
                x, z = ix * T + T / 2, iz * T + T / 2
                c = cols[(ix + iz) % 2]
                inside, edge = hole(x, z)
                fall = (rnd.random() < .5) if edge else inside
                ob = box(f"{name}_{ix}_{iz}", T * 0.995, 0.25, T * 0.995, c, (x, top - 0.125, z), rough=0.55)
                if fall: falling.append(dict(ob=ob, x=x, z=z, top=top, vx=(rnd.random() - .5) * 1.2, vz=(rnd.random() - .5) * 1.2,
                                             rx=(rnd.random() - .5) * 6, rz=(rnd.random() - .5) * 6, delay=rnd.random() * 0.25))
                else: static.append(ob)
        return falling
    h1 = lambda x, z: ((-2.6 < x < 0.3 and -3.3 < z < -0.6), (-2.6 < x < 0.3 and -3.3 < z < -0.6) and (x < -2.3 or x > 0.0 or z < -3.0 or z > -0.9))
    h2 = lambda x, z: ((-1.0 < x < 1.4 and -2.4 < z < 0.2), (-1.0 < x < 1.4 and -2.4 < z < 0.2) and (x < -0.7 or x > 1.1 or z < -2.1 or z > -0.1))
    fall1 = make_floor("t1", FY, h1, (0xc29466, 0xbb8d5f))
    fall2 = make_floor("t2", 0.0, h2, (0x8a6a4c, 0x7f6145))
    # jagged cracks: chains of short dark segments that appear one after another
    def cracks(name, cx, cz, y, n, t0):
        segs = []
        for i in range(n):
            a = rnd.random() * math.tau; px, pz = cx + math.cos(a) * rnd.uniform(0.1, 0.5), cz + math.sin(a) * rnd.uniform(0.1, 0.5)
            for k in range(6):
                a += rnd.uniform(-0.7, 0.7); L = rnd.uniform(0.12, 0.3)
                nx, nz = px + math.cos(a) * L, pz + math.sin(a) * L
                ob = box(f"{name}{i}_{k}", L, 0.008, 0.02 - k * 0.002, 0x120b07, ((px + nx) / 2, y + 0.004, (pz + nz) / 2), rough=1)
                ob.rotation_euler = (0, 0, -a); segs.append((ob, t0 + i * 0.12 + k * 0.18)); px, pz = nx, nz
        return segs
    crk1 = cracks("c1_", -1.2, -1.95, FY, 14, E["cracks"])
    crk2 = cracks("c2_", 0.2, -1.1, 0.0, 10, E["cracks2"])
    # bed (two halves)
    bed = empty("bed"); bedL = empty("bedL", (-1.6, FY, -2.0)); bedR = empty("bedR", (-1.6, FY, -2.0)); bedL.parent = bed; bedR.parent = bed
    for nm, w, h, d, c, p, par, bv in (("frL", 1.7, 0.32, 1.1, 0x6e4a30, (0, 0.26, -0.55), bedL, 0.02), ("frR", 1.7, 0.32, 1.1, 0x6e4a30, (0, 0.26, 0.55), bedR, 0.02),
                                        ("matL", 1.6, 0.26, 1.05, 0xf3f1ec, (0, 0.55, -0.53), bedL, 0.05), ("matR", 1.6, 0.26, 1.05, 0xf3f1ec, (0, 0.55, 0.53), bedR, 0.05),
                                        ("head", 1.75, 1.0, 0.1, 0x6e4a30, (0, 0.62, -1.12), bedL, 0.02), ("pillow", 0.75, 0.15, 0.42, 0xffffff, (0, 0.76, -0.82), bedL, 0.06),
                                        ("blanket", 1.64, 0.07, 0.95, 0x5f8fae, (0, 0.7, 0.55), bedR, 0.03)):
        box(nm, w, h, d, c, p, parent=par, bevel=bv)
    # scale with 7-segment display
    scl = empty("scale", (1.2, FY, 0.9))
    box("scale_body", 0.5, 0.05, 0.5, 0xeef1f4, (0, 0.025, 0), parent=scl, bevel=0.015, rough=0.35)
    box("scale_win", 0.22, 0.004, 0.08, 0x0b1014, (0, 0.051, -0.19), parent=scl, rough=0.2)
    SEG = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
    segs = {}
    for di in range(3):
        cx = -0.06 + di * 0.06
        for s, (sx, sz, w, d) in {"a": (0, -0.025, 0.026, 0.005), "g": (0, 0, 0.026, 0.005), "d": (0, 0.025, 0.026, 0.005), "f": (-0.015, -0.0125, 0.005, 0.022),
                                   "b": (0.015, -0.0125, 0.005, 0.022), "e": (-0.015, 0.0125, 0.005, 0.022), "c": (0.015, 0.0125, 0.005, 0.022)}.items():
            segs[(di, s)] = box(f"seg{di}{s}", w, 0.002, d, 0x7ff0d8, (cx + sx, 0.054, -0.19 + sz), parent=scl, emit=6)
    # sneakers + jeans
    stand = empty("stand")
    for s in (-1, 1):
        fx, fz = 1.2 + s * 0.09, 0.95
        shoe = empty(f"shoe{s}", (fx, FY + 0.012, fz)); shoe.parent = stand
        box("sole", 0.112, 0.03, 0.29, 0xf4f4f2, (0, 0.015, -0.01), parent=shoe, bevel=0.014)
        box("upper", 0.1, 0.075, 0.2, 0x2f4a66, (0, 0.07, 0.03), parent=shoe, bevel=0.035)
        box("toe", 0.1, 0.05, 0.09, 0x2f4a66, (0, 0.05, -0.1), parent=shoe, bevel=0.028)
        box("toecap", 0.104, 0.028, 0.05, 0xf4f4f2, (0, 0.03, -0.14), parent=shoe, bevel=0.013)
        box("swoosh", 0.004, 0.02, 0.1, 0xff9a40, (s * 0.051, 0.06, 0.0), parent=shoe)
        for k in range(4): box("lace", 0.055, 0.008, 0.01, 0xffffff, (0, 0.11, -0.04 + k * 0.03), parent=shoe)
        box("tongue", 0.06, 0.03, 0.05, 0x2f4a66, (0, 0.12, 0.08), parent=shoe, bevel=0.012)
        limb(f"jean{s}", B(fx, FY + 0.13, fz + 0.08), B(fx + s * 0.02, FY + 0.98, fz + 0.16), 0.055, 0.072, 0x3d5a80, stand)
    cam = camera(58); hL, hR = hand(cam, -1), hand(cam, 1)
    merge_static("house_static", static); bake_modifiers(scene)

    POS = [(0, (1.2, 4.52, 0.86)), (E["walk"], (1.2, 4.52, 0.86)), (9.6, (0.6, 4.6, 0.4)), (10.8, (-0.3, 4.58, -1.4)), (E["sit"], (-1.05, 4.3, -2.0))]
    LOOK = [(0, (1.2, 3.0, 0.42)), (8.2, (1.2, 3.0, 0.42)), (9.2, (-0.8, 4.0, -2.4)), (10.8, (-1.6, 3.6, -2.2)), (E["sit"], (2.5, 3.6, -1.6)),
            (E["look_bed"], (2.5, 3.6, -1.6)), (E["look_bed"] + 0.8, (-0.45, 3.3, -2.05)), (17.8, (-0.45, 3.3, -2.05)), (19.0, (1.2, 3.0, -1.7))]
    LAND1, LOOKUP1 = Vector((0.15, 0.72, -1.05)), Vector((-0.9, 3.4, -2.0))
    LAND2, LOOKUP2 = Vector((0.2, -2.1, -1.0)), Vector((-0.4, 3.6, -1.8))

    def state(t):
        p, l = track(POS, t), track(LOOK, t); roll = 0.0
        for td in (3.3, 6.3):
            k = t - td
            if 0 < k < .6: p.y -= 0.05 * math.sin(k / .6 * math.pi)
        if E["walk"] + 0.2 < t < E["sit"]: p.y += 0.035 * math.sin((t - E["walk"]) * 9)
        if t > E["sit"]: p.y -= 0.06 * sm((t - E["sit"]) / 4)
        if t > E["bed_break"]:
            bb = cl((t - E["bed_break"]) / 0.22); p.y -= 0.36 * bb * bb
            if t - E["bed_break"] < 1.2: p += shake(t, 0.03 * (1 - (t - E["bed_break"]) / 1.2), 31)
        if E["cracks"] - 0.5 < t < E["floor_break"]: p += shake(t, 0.004 + 0.012 * sm((t - E["cracks"]) / 4), 37)
        if t > E["floor_break"]:
            ff = cl((t - E["floor_break"]) / (E["land"] - E["floor_break"]))
            sp = state(E["floor_break"] - 1e-3)[0]
            p = sp.lerp(LAND1, ff * ff); l = track(LOOK, E["floor_break"]).lerp(LOOKUP1, sm((t - E["floor_break"] - .1) / 1.2))
            roll = 0.25 * math.sin(ff * math.pi)
            if 0 < t - E["land"] < 1.6: p += shake(t, 0.06 * math.exp(-(t - E["land"]) * 3), 27)
            if t > E["land"] + 1.0: l = LOOKUP1.lerp(Vector((2.5, 0.9, -3.2)), sm((t - E["land"] - 1.0) / 1.6))
            if t > E["cracks2"] - 0.2: l = l.lerp(Vector((0.4, 0.0, -1.5)), sm((t - E["cracks2"] + 0.2) / 0.9))
            if E["cracks2"] < t < E["floor2_break"]: p += shake(t, 0.006 + 0.012 * sm((t - E["cracks2"]) / 2.5), 41)
        if t > E["floor2_break"]:
            ff = cl((t - E["floor2_break"]) / (E["land2"] - E["floor2_break"]))
            p = LAND1.lerp(LAND2, ff * ff); l = Vector((0.4, 0.0, -1.5)).lerp(LOOKUP2, sm((t - E["floor2_break"]) / 1.4))
            roll = -0.2 * math.sin(ff * math.pi)
            if 0 < t - E["land2"] < 1.6: p += shake(t, 0.07 * math.exp(-(t - E["land2"]) * 3), 25)
            if t > E["land2"] + 1.6: l = LOOKUP2 + Vector((0.3 * math.sin((t - 33) * 0.4), 0, 0.2 * math.sin((t - 33) * 0.3)))
        return p, l, roll

    SEGS = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}
    def frame(t, f):
        p, l, roll = state(t); cam_key(cam, p, l, f, roll)
        show = E["sit"] - 0.6 < t < E["land2"] + 1.2
        vis(hL, not show, f); vis(hR, not show, f)
        hy, hz, hx, hrx = -0.24, -0.5, 0.3, -0.25
        if t > E["look_bed"]:
            k = sm((t - E["look_bed"]) / 1.0); hy, hz, hx = lerp(-0.24, -0.2, k), lerp(-0.5, -0.46, k), lerp(0.3, 0.34, k)
        for tb in (E["floor_break"], E["floor2_break"]):
            if tb < t < tb + 1.4:
                k = math.sin(cl((t - tb) / 1.4) * math.pi); hy = lerp(hy, -0.12, k); hx = lerp(hx, 0.44, k); hrx = lerp(-0.25, 0.7, k)
        fl = 0.04 * math.sin((t - E["bed_break"]) * 20) if E["bed_break"] < t < E["bed_break"] + .5 else 0
        for h, s in ((hL, -1), (hR, 1)):
            h.location = (s * hx, hy + s * fl, hz); h.rotation_euler = (hrx, s * -0.25, s * -0.1); key(h, "location", f); key(h, "rotation_euler", f)
        vis(stand, t >= E["walk"] + 1.2, f)
        m = TL.mass_at(TL.n(t)) if t < E["walk"] + 1.0 else None
        dg = [None if ch == " " else int(ch) for ch in str(int(round(m))).rjust(3)[-3:]] if m is not None else [None] * 3
        for di in range(3):
            on = (SEGS[dg[di]] if dg[di] is not None else "") if m is not None else "g"
            for s in "abcdefg": vis(segs[(di, s)], s not in on, f, recursive=False)
        bb = cl((t - E["bed_break"]) / 0.3) if t > E["bed_break"] else 0
        bedL.rotation_euler = (-0.24 * bb, 0, 0); bedR.rotation_euler = (0.28 * bb, 0, 0)
        bedL.location = B(-1.6, FY - 0.12 * bb, -2.0 + 0.06 * bb); bedR.location = B(-1.6, FY - 0.14 * bb, -2.0 - 0.06 * bb)
        for ob in (bedL, bedR): key(ob, "location", f); key(ob, "rotation_euler", f)
        tf = t - E["floor_break"]
        if tf > 0: bed.location = B(-0.6 * min(1, tf), max(-2.75, -5.39 * tf * tf * 1.1), 0); bed.rotation_euler = (0, max(-0.25, -0.2 * tf), 0)
        else: bed.location = (0, 0, 0); bed.rotation_euler = (0, 0, 0)
        key(bed, "location", f); key(bed, "rotation_euler", f)
        for segs_, t_end in ((crk1, E["floor_break"]), (crk2, E["floor2_break"])):
            for ob, ta in segs_: vis(ob, not (ta < t < t_end + 0.05), f, recursive=False)
        for tiles, tb, floor_y in ((fall1, E["floor_break"], 0.13), (fall2, E["floor2_break"], -2.57)):
            tt = t - tb
            for k in tiles:
                d = max(0.0, tt - k["delay"])
                if tt <= 0: k["ob"].location = B(k["x"], k["top"] - 0.125, k["z"]); k["ob"].rotation_euler = (0, 0, 0)
                else:
                    md = min(d, .9); fy = floor_y
                    lx, lz = k["x"] + k["vx"] * md, k["z"] + k["vz"] * md
                    if tiles is fall1 and h2(lx, lz)[0]: fy = 0.13 if t < E["floor2_break"] + k["delay"] else -2.5
                    y = max(fy, k["top"] - 0.125 - 5.4 * d * d)
                    if fy < 0 and t > E["floor2_break"]:
                        d2 = max(0.0, t - E["floor2_break"] - k["delay"]); y = max(fy, 0.13 - 5.4 * d2 * d2)
                    k["ob"].location = B(k["x"] + k["vx"] * md, y, k["z"] + k["vz"] * md); k["ob"].rotation_euler = (k["rx"] * md * .3, -k["rz"] * md * .3, 0)
                key(k["ob"], "location", f); key(k["ob"], "rotation_euler", f)
        lamp.data.energy = 220 if t > E["floor_break"] - 0.2 else 0; lamp.data.keyframe_insert("energy", frame=f)
        pit.data.energy = 120 if t > E["floor2_break"] - 0.2 else 0; pit.data.keyframe_insert("energy", frame=f)
    return frame

# ======================================================================= ACT 2: SHAFT (sinking)
def strata(depth):
    """color + emission for rock at a given depth (m below the house)."""
    if depth < 2: return 0x5a4330, 0
    if depth < 10: return [0x5e4532, 0x6a4e38, 0x52402f][int(depth) % 3], 0
    if depth < 14: return 0x8d8f93, 0          # concrete / foundations
    if depth < 30: return [0x8a6a4a, 0x7c5d40, 0x93724f][int(depth / 2) % 3], 0   # clay
    if depth < 38: return [0xb08c62, 0xa5825a][int(depth / 2) % 2], 0              # sandstone
    if depth < 70: return [0x8f7f84, 0x9a8a8e, 0x857579][int(depth / 3) % 3], 0   # granite
    return [0x4a3a36, 0x3e302c, 0x55413a][int(depth / 3) % 3], 0

def tube(name, y_top, y_bot, step, radius, colfn, sides=14, jitter=0.12):
    """vertical tube of rings (inner surface visible), one merged mesh; faces get 3 shades for a rocky texture."""
    bm = bmesh.new(); mats = {}; me = bpy.data.meshes.new(name)
    y = y_top; rr = random.Random(3)
    while y > y_bot:
        depth = -y; col, em = colfn(depth)
        res = bmesh.ops.create_cone(bm, cap_ends=False, segments=sides, radius1=radius, radius2=radius, depth=step)
        for v in res["verts"]:
            j = 1 + rr.uniform(-jitter, jitter); v.co.x *= j; v.co.y *= j
        bmesh.ops.translate(bm, vec=Vector((0, 0, y - step / 2)), verts=res["verts"])
        for fc in {f for v in res["verts"] for f in v.link_faces}:
            shade = rr.choice((0, 0, 1, 2))
            fc.material_index = mats.setdefault((col, round(em, 1), shade), len(mats))
        y -= step
    bm.to_mesh(me); bm.free()
    for (col, em, shade), i in sorted(mats.items(), key=lambda kv: kv[1]):
        f = (1.0, 0.72, 1.22)[shade]
        c = int(min(255, ((col >> 16) & 255) * f)) << 16 | int(min(255, ((col >> 8) & 255) * f)) << 8 | int(min(255, (col & 255) * f))
        me.materials.append(mat(c, 0.95, emit=em, emit_col=0xff6a20) if em > 0 else mat(c, 0.95))
    return link(bpy.data.objects.new(name, me))

def veins(name, radius, y_top, y_bot, n, glowfn, width=0.035):
    """glowing cracks on the inside of a tube: short zig-zag chains of thin emissive bars (one merged mesh)."""
    rr = random.Random(hash(name) % 997); bm = bmesh.new(); mats = {}; me = bpy.data.meshes.new(name)
    for _ in range(n):
        y = rr.uniform(y_bot, y_top); a = rr.random() * math.tau
        col, st = glowfn(-y)
        if st <= 0: continue
        mi = mats.setdefault((col, round(st, 1)), len(mats))
        px, py = a, y
        for k in range(rr.randint(3, 6)):
            da, dy = rr.uniform(-0.25, 0.25) / radius * 2, rr.uniform(-1.2, 0.4) * radius * 0.6
            nx, ny = px + da, py + dy
            p0 = Vector((math.cos(px) * radius * 0.99, math.sin(px) * radius * 0.99, py)); p1 = Vector((math.cos(nx) * radius * 0.99, math.sin(nx) * radius * 0.99, ny))
            L = (p1 - p0).length; w = width * rr.uniform(0.6, 1.4) * (1 - k * 0.12)
            res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((w, w, L)), verts=res["verts"])
            q = (p1 - p0).to_track_quat('Z', 'Y')
            bmesh.ops.rotate(bm, verts=res["verts"], cent=Vector((0, 0, 0)), matrix=q.to_matrix())
            bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=res["verts"])
            for fc in {f for v in res["verts"] for f in v.link_faces}: fc.material_index = mi
            px, py = nx, ny
    bm.to_mesh(me); bm.free()
    for (col, st), i in sorted(mats.items(), key=lambda kv: kv[1]): me.materials.append(emission_mat(col, st))
    return link(bpy.data.objects.new(name, me))

def act_shaft():
    world((0.02, 0.02, 0.03), 0.2)
    tube("shaft", 2.0, -175, 1.0, 1.0, strata)
    veins("shaft_veins", 1.0, -72, -175, 300, lambda d: ((0xff7a2a if d < 130 else 0xffb050), 0 if d < 72 else 2.0 + 4.0 * cl((d - 72) / 90)), width=0.012)
    # looking up you see where you came from: jagged broken floors, the lit room above, its ceiling and lamp
    top = []
    for ring_y, r0, cols in ((2.0, 1.0, (0x8a6a4c, 0x7f6145)), (5.0, 1.4, (0xc29466, 0xbb8d5f))):
        for ix in range(-8, 8):
            for iz in range(-8, 8):
                x, z = ix * 0.5 + 0.25, iz * 0.5 + 0.25; d = math.hypot(x, z)
                if d < r0 + rnd.uniform(-0.2, 0.45) or d > 4.2: continue
                top.append(box(f"tt{ring_y}_{ix}_{iz}", 0.5, 0.25, 0.5, cols[(ix + iz) % 2], (x, ring_y + 0.125, z), rough=0.6))
        for k in range(10):   # snapped boards hanging into the hole
            a = rnd.random() * math.tau; L = rnd.uniform(0.4, 0.9)
            b = box(f"board{ring_y}{k}", 0.08, L, 0.18, cols[0], (math.cos(a) * (r0 + 0.1), ring_y - L / 2 + 0.1, math.sin(a) * (r0 + 0.1)), rough=0.7)
            b.rotation_euler = (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), a); top.append(b)
    top.append(box("ceiling", 9, 0.2, 9, 0xf3eee6, (0, 8.0, 0)))
    for nm, x, z, w, d in (("tw1", 0, -4.4, 9, 0.2), ("tw2", 0, 4.4, 9, 0.2), ("tw3", -4.4, 0, 0.2, 9), ("tw4", 4.4, 0, 0.2, 9)):
        top.append(box(nm, w, 5.6, d, 0xece5d8, (x, 5.2 + 2.8, z)))
    top.append(box("lampcord", 0.02, 0.6, 0.02, 0x222222, (0.6, 7.6, -0.4))); top.append(box("bulb", 0.25, 0.2, 0.25, 0xfff0d0, (0.6, 7.25, -0.4), emit=6))
    merge_static("shaft_top", top)
    room = light('AREA', "roomlight", 500, (1.0, 0.92, 0.8), (0, 7.6, 0), (0, 0, 0), size=6)
    light('POINT', "bulblight", 300, (1.0, 0.85, 0.65), (0.6, 7.0, -0.4), soft=0.3)
    toplight = light('SPOT', "toplight", 600, (1.0, 0.95, 0.85), (0, 1.6, 0), (0, -10, 0)); toplight.data.spot_size = math.radians(70)
    iris = ico("iris", 1.5, 0x3a2c24, (0, 1.85, 0), sub=2, material=mat(0x3a2c24, 1.0)); iris.scale = (0.001, 0.001, 0.001)
    heat = light('POINT', "heat", 0, (1.0, 0.55, 0.25), (0, 0, 0), soft=0.6)
    fill = light('POINT', "fill", 60, (1.0, 0.92, 0.85), (0, 0, 0), soft=0.4)
    # pipes and cables crossing the shaft near the top
    stat = []
    for y, c, r, ang in ((-5.5, 0x9aa3ad, 0.08, 0.3), (-6.4, 0x3a3f46, 0.03, 1.2), (-8.2, 0x6d7d8c, 0.12, 2.0), (-9.1, 0x2a2e33, 0.025, 0.7)):
        a, b = Vector((math.cos(ang) * 1.3, math.sin(ang) * 1.3, y)), Vector((-math.cos(ang) * 1.3, -math.sin(ang) * 1.3, y))
        stat.append(limb(f"pipe{y}", a, b, r, r, c, rough=0.4))
    # rebar ends sticking out of the concrete band
    for i in range(16):
        a = rnd.random() * math.tau; y = -rnd.uniform(10.2, 13.8)
        p0 = Vector((math.cos(a) * 1.05, math.sin(a) * 1.05, y)); p1 = Vector((math.cos(a) * 0.82, math.sin(a) * 0.82, y + rnd.uniform(-.1, .1)))
        stat.append(limb(f"rebar{i}", p0, p1, 0.012, 0.012, 0x6b4a36, rough=0.6))
    # wall rocks for parallax
    for i in range(70):
        a = rnd.random() * math.tau; d = rnd.uniform(1, 170); col, em = strata(d)
        o = ico(f"wr{i}", rnd.uniform(0.08, 0.22), col, (0, 0, 0), material=mat(col, 0.95, emit=em * 0.6, emit_col=0xff6a20) if em else None)
        o.location = Vector((math.cos(a) * 0.93, math.sin(a) * 0.93, -d)); stat.append(o)
    merge_static("shaft_static", stat)
    # sideways dust at the end
    dust = [ico(f"dust{i}", rnd.uniform(0.006, 0.018), 0xc9b9a6, (0, 0, 0)) for i in range(90)]
    dseed = [(rnd.random() * math.tau, rnd.uniform(-1.2, 1.2), rnd.random()) for _ in dust]
    cam = camera(64)
    DEPTH = [(36, 0.2), (42, 0.8), (46, 2.5), (52, 6.0), (60, 11.5), (68, 17), (77, 32), (89, 60), (102, 100), (120, 160)]
    def depth(t):
        for (t0, a), (t1, b) in zip(DEPTH, DEPTH[1:]):
            if t <= t1: return a + (b - a) * (t - t0) / (t1 - t0)
        return DEPTH[-1][1]
    LOOKS = [(36, (0.05, 1, 0.1)), (55, (0.1, 1, 0.05)), (57, (1, -0.15, 0.2)), (61.5, (0.3, -0.9, 0.2)), (66, (0.1, 1, 0.1)),
             (74, (0.1, 1, 0.1)), (77.5, (0.25, -0.9, 0.2)), (81, (0.1, 1, 0.1)), (83.5, (0.3, -0.9, 0.2)), (88.5, (0.2, 0.9, 0.2)), (98, (0.25, -0.9, 0.15)), (104, (0.15, 1, 0.1)), (110, (0.45, -0.7, 0.3)), (120, (0.3, -0.85, -0.35))]
    def frame(t, f):
        d = depth(t); y = -d
        p = Vector((0.0, y, 0.0)) + shake(t, 0.01 + 0.01 * cl((t - 60) / 40), 19)
        dirv = track(LOOKS, t).normalized()
        cam_key(cam, p, p + dirv, f, roll=0.05 * math.sin(t * 0.3))
        heat.location = B(0, y - 0.6, 0); heat.data.energy = 90 * cl((d - 60) / 80) ** 1.3; key(heat, "location", f); heat.data.keyframe_insert("energy", frame=f)
        fill.location = B(0, y + 0.4, 0); fill.data.energy = 60 * (1 - 0.6 * cl((d - 70) / 60)); key(fill, "location", f); fill.data.keyframe_insert("energy", frame=f)
        s = 1 - sm((t - E["close"]) / 3.0); c_ = max(0.001, 1 - s); iris.scale = (c_, c_, 0.12 * c_ + 0.001); key(iris, "scale", f)
        toplight.data.energy = 600 * s; toplight.data.keyframe_insert("energy", frame=f)
        k = cl((t - E["dust"]) / 6)
        for o, (a, dy, ph) in zip(dust, dseed):
            r = 0.95 - 0.9 * ((ph + (t - E["dust"]) * 0.12) % 1.0) * k if k > 0 else 0.95
            o.location = B(math.cos(a) * r, y + dy, math.sin(a) * r); key(o, "location", f)
    return frame

# ======================================================================= ACT 3: CAVITY (tiny planet)
def act_cavity():
    world((0.01, 0.01, 0.012), 0.1)
    R = 8.0
    rock_cave("cavity", R, (0, 0, 0), (0x5a4a40, 0x463830, 0x6e5c4e), glow=(0xff6a28, 1.6, 0.5), rough=0.3, seed=2)
    core = light('POINT', "core", 140, (1.0, 0.62, 0.32), (0.3, -0.4, 0.2), soft=0.3)
    light('POINT', "fill", 700, (1.0, 0.8, 0.6), (4, 3, -2.5), soft=1.0); light('POINT', "fill2", 260, (0.55, 0.65, 1.0), (-4, -2.5, 3), soft=1.0)
    cam = camera(70); hL, hR = hand(cam, -1, glow=2.0), hand(cam, 1, glow=2.0)
    rocks = []
    for i in range(170):
        big = i > 70
        o = ico(f"rock{i}", rnd.uniform(0.04, 0.12) if not big else rnd.uniform(0.15, 0.55), [0x6b5446, 0x7a6252, 0x5c483c][i % 3], (0, 0, 0), sub=1)
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        t0 = (E["pebbles"] - 16 + rnd.random() * 14) if not big else (E["pebbles"] + rnd.random() * 26)
        rocks.append(dict(o=o, v=v, r0=R - 0.3, t0=t0, acc=rnd.uniform(0.25, 0.5) if not big else rnd.uniform(0.35, 0.7), spin=Vector((rnd.random(), rnd.random(), rnd.random())) * 3))
    def frame(t, f):
        yaw = (t - 120) * 0.07; pitch = 0.25 * math.sin((t - 120) * 0.11)
        d = Vector((math.cos(yaw) * math.cos(pitch), math.sin(pitch), math.sin(yaw) * math.cos(pitch)))
        p = Vector((0, 0, 0)) + shake(t, 0.004, 13)
        cam_key(cam, p, p + d, f, roll=0.04 * math.sin(t * 0.2))
        for h, s in ((hL, -1), (hR, 1)):
            h.location = (s * 0.3, -0.26 + 0.01 * math.sin(t * 1.3 + s), -0.5); h.rotation_euler = (-0.3, s * -0.25, s * -0.1)
            key(h, "location", f); key(h, "rotation_euler", f)
        core.data.energy = 120 + 120 * sm((t - 150) / 10); core.data.keyframe_insert("energy", frame=f)
        for k in rocks:
            dt = t - k["t0"]
            if dt <= 0: r = k["r0"]
            else: r = max(0.0, k["r0"] - k["acc"] * dt * dt * (1 + 0.6 * sm((t - 150) / 10)))
            sc = 1.0 if r > 0.9 else max(0.001, r / 0.9)
            k["o"].location = B(*(k["v"] * max(r, 0.01))); k["o"].scale = (sc, sc, sc); k["o"].rotation_euler = tuple(k["spin"] * max(dt, 0) * 0.3)
            key(k["o"], "location", f); key(k["o"], "scale", f); key(k["o"], "rotation_euler", f)
    return frame

# ======================================================================= ACT 4: PLUNGE (to the core)
def plunge_color(s):
    if s < 0.12: return [0x4a3a32, 0x3c2f29][int(s * 300) % 2], 0
    if s < 0.68: return [0x3a1c14, 0x4a2216, 0x2e1610][int(s * 300) % 3], 0
    if s < 0.9: return [0x5a2a14, 0x6a3218][int(s * 300) % 2], 0
    return 0x7a4a20, 0

def plunge_glow(s):
    if s < 0.12: return 0xff7a2a, 2.0
    if s < 0.68: return 0xff6a20, 3.5 + 3 * (s - 0.12)
    if s < 0.9: return 0xffa040, 6.0
    return 0xffe0a0, 7.0

def act_plunge():
    world((0.0, 0.0, 0.0), 0.0)
    L = 1800.0
    tube("lava", 2.0, -L, 4.0, 3.0, lambda depth: plunge_color(depth / L), sides=16, jitter=0.18)
    veins("lava_veins", 3.0, 0, -L, 1800, lambda d: plunge_glow(d / L), width=0.04)
    streaks = []
    for i in range(160):
        a = rnd.random() * math.tau; y = -rnd.uniform(0, L); col, em = plunge_color(-y / L)
        o = box(f"st{i}", 0.05, 7.0, 0.05, 0, (0, 0, 0), material=emission_mat(0xffd9a0, 2.0 + em))
        o.location = Vector((math.cos(a) * 2.6, math.sin(a) * 2.6, y)); streaks.append(o)
    merge_static("streaks", streaks)
    rock_cave("corecav", 45, (0, -L - 40, 0), (0x6a3418, 0x542a14, 0x7e4020), glow=(0xffb050, 3.0, 0.35), rough=0.18, seed=5)
    corel = light('POINT', "corelight", 7.0e4, (1.0, 0.75, 0.45), (0, -L - 40, 0), soft=4)
    glowl = light('POINT', "glow", 600, (1.0, 0.65, 0.35), (0, 0, 0), soft=1.0)
    cam = camera(66); hL, hR = hand(cam, -1, glow=1.5), hand(cam, 1, glow=1.5)
    Y = [(170, 0), (176, -20), (186, -160), (205, -620), (220, -1150), (229, -1790), (235, -1830), (245, -1840)]
    def ypos(t):
        for (t0, a), (t1, b) in zip(Y, Y[1:]):
            if t <= t1:
                k = (t - t0) / (t1 - t0); k = k * k * (3 - 2 * k) if t0 >= 229 else k
                return a + (b - a) * k
        return Y[-1][1]
    def frame(t, f):
        y = ypos(t); spd = abs(ypos(t + 0.05) - ypos(t)) / 0.05
        amp = min(0.08, 0.004 + spd * 0.0006)
        p = Vector((0, y, 0)) + shake(t, amp, 29)
        if t < 229: d = Vector((0.25 * math.sin(t * 0.21), -1, 0.25 * math.cos(t * 0.17)))
        else:
            k = sm((t - 229) / 4); yaw = (t - 229) * 0.12
            d = Vector((0.25 * math.sin(t * 0.21), -1, 0.25 * math.cos(t * 0.17))).lerp(Vector((math.cos(yaw), 0.05, math.sin(yaw))), k)
        cam_key(cam, p, p + d, f, roll=0.15 * math.sin(t * 0.13))
        glowl.location = B(0, y - 4, 0); key(glowl, "location", f)
        for h, s in ((hL, -1), (hR, 1)):
            h.location = (s * 0.32, -0.22, -0.5); h.rotation_euler = (0.2 if t < 229 else -0.25, s * -0.25, s * -0.1)
            key(h, "location", f); key(h, "rotation_euler", f)
    return frame

# ======================================================================= ACT 5: SURFACE (gravity rises)
def act_surface():
    world((0.55, 0.72, 0.95), 1.1)
    sunl = sun(4.5, (30, 25, 20), (0, 0, 0))
    gp = bpy.data.meshes.new("ground"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=600); bm.to_mesh(gp); bm.free()
    go = link(bpy.data.objects.new("ground", gp)); go.data.materials.append(mat(0x79a552, 0.95))
    stat = [box("road", 7, 0.02, 600, 0x4a4c52, (0, 0.01, -250))]
    for i in range(120): stat.append(box(f"dash{i}", 0.15, 0.022, 1.6, 0xf0d060, (0, 0.012, -i * 5)))
    for side in (-1, 1): stat.append(box(f"walk{side}", 2.0, 0.08, 600, 0xb8b4ac, (side * 4.6, 0.04, -250)))
    houses, trees, poles = [], [], []
    for i in range(26):
        for side in (-1, 1):
            z = -6 - i * 11 + rnd.uniform(-1, 1); x = side * rnd.uniform(9, 12); w, d, h = rnd.uniform(6, 8), rnd.uniform(6, 8), rnd.uniform(3, 6.5)
            g = empty(f"house{i}{side}", (x, 0, z))
            box("walls", w, h, d, [0xe8dccb, 0xd9c7b0, 0xc9d4dc, 0xf0e2c8][(i + side) % 4], (0, h / 2, 0), parent=g)
            roof = empty("roofp", (0, h, 0)); roof.parent = g; roof.location = (0, 0, h)
            rm = bpy.data.meshes.new("roof"); bm = bmesh.new()
            vs = [bm.verts.new(v) for v in ((-w / 2 - .3, -d / 2 - .3, 0), (w / 2 + .3, -d / 2 - .3, 0), (w / 2 + .3, d / 2 + .3, 0), (-w / 2 - .3, d / 2 + .3, 0), (0, -d / 2 - .3, 2.2), (0, d / 2 + .3, 2.2))]
            for fc in ((0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)): bm.faces.new([vs[k] for k in fc])
            bm.to_mesh(rm); bm.free(); ro = link(bpy.data.objects.new("roof", rm), roof); ro.data.materials.append(mat([0xa04a38, 0x5a6470, 0x8a5a3a][i % 3], 0.8))
            for k in range(3): box("win", 0.05, 1.0, 1.0, 0x6a90b0, (-side * (w / 2 + 0.02), h * 0.55, -d / 3 + k * d / 3), parent=g, rough=0.2)
            houses.append(dict(g=g, roof=roof, h=h))
            for k in range(2):
                tx, tz, th = side * rnd.uniform(6, 7.5), z + rnd.uniform(-5, 5), rnd.uniform(2.5, 4.5)
                tg = empty(f"tree{i}{side}{k}", (tx, 0, tz))
                box("trunk", 0.3, th, 0.3, 0x5a4030, (0, th / 2, 0), parent=tg)
                ico("crown", rnd.uniform(1.1, 1.8), [0x4f8a3c, 0x5a9440, 0x447a34][k], (0, th + 0.8, 0), parent=tg).location = (0, 0, th + 0.8)
                trees.append(dict(g=tg, lean=rnd.uniform(-1, 1)))
        if i % 2 == 0:
            pg = empty(f"pole{i}", (5.8, 0, -i * 11)); box("pole", 0.18, 7, 0.18, 0x6a5a4a, (0, 3.5, 0), parent=pg); box("arm", 1.6, 0.12, 0.12, 0x6a5a4a, (0, 6.6, 0), parent=pg)
            poles.append(pg)
    # bridge in the distance
    bridge = empty("bridge", (0, 0, -170)); bL = empty("bL", (0, 0, 0)); bR = empty("bR", (0, 0, 0)); bL.parent = bridge; bR.parent = bridge
    bL.location = (-12, 0, 6); bR.location = (12, 0, 6)
    box("deckL", 24, 1.0, 6, 0x8a8f96, (-12, 0, 0), parent=bL); box("deckR", 24, 1.0, 6, 0x8a8f96, (12, 0, 0), parent=bR)
    for x in (-30, 30): stat.append(box(f"pier{x}", 3, 7, 6, 0x9a9a9a, (x, 3.0, -170)))
    stat.append(box("river", 120, 0.05, 30, 0x4f7fa8, (0, 0.03, -175), rough=0.15))
    plane = empty("plane", (0, 0, 0))
    box("fus", 1.6, 1.6, 14, 0xf2f2f2, (0, 0, 0), parent=plane, bevel=0.5); box("wing", 18, 0.25, 3, 0xdcdcdc, (0, 0, 0), parent=plane)
    box("tail", 0.3, 3, 2, 0xc0392b, (0, 1.6, 6), parent=plane); box("stab", 6, 0.2, 1.6, 0xdcdcdc, (0, 0.3, 6.2), parent=plane)
    merge_static("surface_static", stat); bake_modifiers(scene)
    cam = camera(60); hL, hR = hand(cam, -1), hand(cam, 1)
    def frame(t, f):
        g = TL.surface_g(TL.n(t))
        eye = max(0.35, 1.65 * g ** -0.6)
        crush = sm((t - E["crush"]) / 4)
        eye = lerp(eye, 0.12, crush)
        p = Vector((1.5, eye, 2.0)) + shake(t, 0.002 + 0.01 * cl((g - 2) / 6), 17)
        look = Vector((1.0, eye * 0.85 + 0.6 * (1 - cl((g - 1.5) / 4)), -40))
        if E["plane"] - 1 < t < E["plane"] + 9: look = look.lerp(Vector((-10, 30, -60)), math.sin(cl((t - E["plane"] + 1) / 10) * math.pi) * 0.8)
        if E["crush"] < t: look = look.lerp(Vector((1.5, -10, -5)), crush)
        cam_key(cam, p, look, f)
        show = g > 2.4
        vis(hL, not show, f); vis(hR, not show, f)
        for h, s in ((hL, -1), (hR, 1)):
            h.location = (s * 0.34, -0.26, -0.48); h.rotation_euler = (-0.6, s * -0.3, s * -0.1); key(h, "location", f); key(h, "rotation_euler", f)
        sq = g ** -0.35
        for tr in trees:
            tr["g"].scale = (1, 1, sq); tr["g"].rotation_euler = (0, tr["lean"] * 0.3 * cl((g - 1.5) / 5), 0)
            key(tr["g"], "scale", f); key(tr["g"], "rotation_euler", f)
        for hs in houses:
            rk = cl((g - 1.8) / 2.5); wk = cl((g - 3.0) / 5)
            hs["roof"].scale = (1, 1, max(0.05, 1 - 0.9 * rk)); hs["roof"].location = (0, 0, hs["h"] * (1 - 0.6 * wk)); hs["g"].scale = (1, 1, max(0.3, 1 - 0.6 * wk))
            key(hs["roof"], "scale", f); key(hs["roof"], "location", f); key(hs["g"], "scale", f)
        for pg in poles: pg.rotation_euler = (0.35 * cl((g - 2.0) / 4), 0, 0); key(pg, "rotation_euler", f)
        bk = sm((t - 285) / 3)
        bL.rotation_euler = (0, -0.35 * bk, 0); bR.rotation_euler = (0, 0.35 * bk, 0); bL.location = (-12, 0, 6 - 4 * bk); bR.location = (12, 0, 6 - 4 * bk)
        for ob in (bL, bR): key(ob, "rotation_euler", f); key(ob, "location", f)
        pt = cl((t - E["plane"]) / 9)
        plane.location = B(lerp(-160, 160, pt), lerp(55, 35, pt), -120); plane.rotation_euler = (0, 0, -math.pi / 2); key(plane, "location", f); key(plane, "rotation_euler", f)
        vis(plane, not (E["plane"] - 0.1 < t < E["plane"] + 9.1), f)
    return frame

# ======================================================================= ACT 6: SPACE (collapse + black hole)
def earth_mesh(name, r):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=r)
    rr = random.Random(5); seeds = [Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized() for _ in range(14)]
    for fc in bm.faces:
        c = fc.calc_center_median().normalized()
        land = max(c.dot(s) for s in seeds) > 0.86
        fc.material_index = (2 if abs(c.z) > 0.88 else (1 if land else 0))
    bm.to_mesh(me); bm.free()
    em = mat(0x2a5fa8, 0.4, emit=0.001, emit_col=0xff5a1a); lm = mat(0x4e8a3e, 0.9, emit=0.001, emit_col=0xff5a1a); im = mat(0xf2f6f8, 0.6, emit=0.001, emit_col=0xff5a1a)
    for m in (em, lm, im): me.materials.append(m)
    return link(bpy.data.objects.new(name, me)), (em, lm, im)

def accretion(name, r_in, r_out, segs=96):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); mats = []
    rings = 6
    for j in range(rings):
        r0, r1 = lerp(r_in, r_out, j / rings), lerp(r_in, r_out, (j + 1) / rings)
        for i in range(segs):
            a0, a1 = i / segs * math.tau, (i + 1) / segs * math.tau
            vs = [bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)) for a, r in ((a0, r0), (a1, r0), (a1, r1), (a0, r1))]
            fc = bm.faces.new(vs); fc.material_index = j * 2 + (i % 2)
    bm.to_mesh(me); bm.free()
    for j in range(rings):
        k = j / (rings - 1)
        for alt in (0, 1):
            me.materials.append(emission_mat([0xfff0c8, 0xffc060, 0xff8a30, 0xff6a20, 0xd84a18, 0x8a2a10][j], (4.5 - 3.2 * k) * (1.0 if alt else 0.7)))
    return link(bpy.data.objects.new(name, me))

def act_space():
    world((0.004, 0.005, 0.01), 1.0, stars=True)
    sunlamp = sun(5.0, (40, 10, 30), (0, 0, 0), color=(1, 0.96, 0.9), angle=1.0)
    earth, emats = earth_mesh("earth", 5.0)
    moon = ico("moon", 1.3, 0xbcbcc2, (14, 2, -10), sub=3)
    bh = ico("bh", 1.0, 0, (0, 0, 0), sub=3, material=emission_mat(0x000000, 0.0)); bh.scale = (0.001,) * 3
    disk = accretion("disk", 1.6, 6.0); disk.rotation_euler = (math.radians(78), 0, 0); disk.scale = (0.001,) * 3
    frags = []
    for i in range(60):
        o = ico(f"frag{i}", rnd.uniform(0.08, 0.3), [0x2a5fa8, 0x4e8a3e, 0x7a5a42][i % 3], (0, 0, 0), sub=1)
        frags.append(dict(o=o, a=rnd.random() * math.tau, r0=rnd.uniform(4, 9), y=rnd.uniform(-1.5, 1.5), sp=rnd.uniform(0.8, 1.6)))
    sunb = ico("sunball", 7.0, 0, (0, 0, 0), sub=3, material=emission_mat(0xffd070, 3.5))
    sunl = light('POINT', "sunlight", 0, (1, 0.92, 0.75), (0, 0, 0), soft=6)
    cam = camera(45)
    def frame(t, f):
        # Earth shrinks from 339 to 372, glowing as it collapses
        k = sm((t - 339) / (E["bh"] - 339)); R = lerp(1.0, 0.18, k) if t < E["bh"] else max(0.001, 0.18 * (1 - sm((t - E["bh"]) / 1.0)))
        earth.scale = (R, R, R); earth.rotation_euler = (0.3, 0, t * 0.05); key(earth, "scale", f); key(earth, "rotation_euler", f)
        glow = 0.0 if t < 345 else 2.5 * sm((t - 345) / 25)
        for m in emats:
            m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = glow
            m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
        b = sm((t - E["bh"] + 0.3) / 1.2)
        bh.scale = (b * 0.9,) * 3; disk.scale = (b,) * 3
        disk.rotation_euler = (math.radians(78), 0, t * 0.6)
        for o in (bh, disk): key(o, "scale", f)
        key(disk, "rotation_euler", f)
        for fr in frags:
            dt = t - E["swallow"]
            if dt < 0: fr["o"].location = B(0, 0, 0); fr["o"].scale = (0.001,) * 3
            else:
                r = max(0, fr["r0"] - dt * 0.9 * fr["sp"]); a = fr["a"] + dt * (2.0 / max(r, 0.6))
                fr["o"].location = B(math.cos(a) * r, fr["y"] * r / fr["r0"], math.sin(a) * r); s = 1.0 if r > 1.2 else max(0.001, r / 1.2)
                fr["o"].scale = (s,) * 3
            key(fr["o"], "location", f); key(fr["o"], "scale", f)
        mk = sm((t - 376) / 16)
        ma = 0.6 + mk * 2.5
        moon.location = B(math.cos(ma) * lerp(15, 9, mk), 2 - mk, math.sin(ma) * lerp(15, 9, mk) * -1); key(moon, "location", f)
        st = t - E["sun"]
        if st < 0: sp = Vector((300, 0, -300))
        else:
            a = -0.8 + st * 0.18; rr = lerp(140, 70, sm(st / 18))
            sp = Vector((math.cos(a) * rr, 8 * math.sin(st * 0.3), math.sin(a) * rr))
        sunb.location = B(*sp); sunl.location = B(*sp); sunl.data.energy = 0 if st < 0 else 2.0e6; key(sunb, "location", f); key(sunl, "location", f); sunl.data.keyframe_insert("energy", frame=f)
        # camera: slow orbit, pulls back for the Sun
        ca = 0.5 + (t - 330) * 0.012; cd = lerp(26, 22, sm((t - 330) / 40)) if t < E["sun"] else lerp(22, 230, sm((t - E["sun"]) / 14))
        cp = Vector((math.cos(ca) * cd, 4 + cd * 0.12, math.sin(ca) * cd))
        cam_key(cam, cp, Vector((0, 0, 0)) if t < E["sun"] else Vector((0, 0, 0)).lerp(sp * 0.35, sm((t - E["sun"]) / 10)), f)
    return frame

# ======================================================================= ACT 7/8: GALAXY + OUTRO
def galaxy_mesh(name, n=9000, R=1000.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rr = random.Random(11)
    cols = [(0xcfe0ff, 5.0), (0xfff1d0, 6.0), (0xffd6b0, 4.0), (0xff9ad0, 2.5)]
    for i in range(n):
        arm = i % 2; d = rr.random() ** 0.9
        ang = arm * math.pi + d * 6.0 + rr.gauss(0, 0.32 * (1.2 - d))
        r = d * R; x, z = math.cos(ang) * r, math.sin(ang) * r; y = rr.gauss(0, 18 * (1 - d) + 4)
        s = rr.uniform(1.0, 3.2) * (1.6 if i % 37 == 0 else 1.0)
        vs = [bm.verts.new((x + dx, -z + dz, y)) for dx, dz in ((-s, -s), (s, -s), (s, s), (-s, s))]
        fc = bm.faces.new(vs); fc.material_index = 3 if (i % 23 == 0 and d > 0.25) else (0 if d > 0.5 else (1 if i % 3 else 2))
    # bulge
    for i in range(1800):
        v = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 0.6))) * 110; s = rr.uniform(1.0, 2.6)
        vs = [bm.verts.new((v.x + dx, v.y + dz, v.z)) for dx, dz in ((-s, -s), (s, -s), (s, s), (-s, s))]
        fc = bm.faces.new(vs); fc.material_index = 1
    bm.to_mesh(me); bm.free()
    for c, e in cols: me.materials.append(emission_mat(c, e))
    return link(bpy.data.objects.new(name, me))

def act_galaxy(outro=False):
    world((0.002, 0.002, 0.005), 1.0, stars=True)
    gal = galaxy_mesh("galaxy")
    sgr = ico("sgr", 14, 0, (0, 0, 0), sub=2, material=emission_mat(0xfff0d0, 10.0))
    our = Vector((520, 0, 160))
    bh = ico("you", 1.0, 0, tuple(our), sub=3, material=emission_mat(0x000000, 0.0))
    disk = accretion("disk", 1.6, 6.0); disk.location = B(*our); disk.rotation_euler = (math.radians(70), 0, 0)
    near = []
    for i in range(140):
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 0.3), rnd.gauss(0, 1))).normalized() * rnd.uniform(20, 120)
        o = ico(f"ns{i}", rnd.uniform(0.6, 1.6), 0, tuple(our + v), sub=1, material=emission_mat([0xcfe0ff, 0xfff1d0, 0xffd0a0][i % 3], 7.0))
        near.append(dict(o=o, v=v, a=math.atan2(v.z, v.x), r=v.length, y=v.y))
    cam = camera(50)
    def bh_size(t):  # visual size grows with log(mass)
        h = TL.hour_at(TL.n(t)); return 2.0 * 2 ** ((h - 95) / 7.0)
    def frame(t, f):
        s = bh_size(t); bh.scale = (s,) * 3; disk.scale = (s,) * 3
        disk.rotation_euler = (math.radians(70), 0, t * 0.5)
        for o in (bh, disk): key(o, "scale", f)
        key(disk, "rotation_euler", f)
        gal.rotation_euler = (0, 0, -t * 0.004); key(gal, "rotation_euler", f)
        for n_ in near:
            dt = max(0, t - 428); r = max(0.0, n_["r"] - dt * dt * 0.09)
            a = n_["a"] + dt * (6.0 / max(r, 6))
            n_["o"].location = B(our.x + math.cos(a) * r, n_["y"] * r / n_["r"], our.z + math.sin(a) * r)
            sc = 1.0 if r > s * 2 else max(0.001, r / (s * 2)); n_["o"].scale = (sc,) * 3
            key(n_["o"], "location", f); key(n_["o"], "scale", f)
        if not outro:
            if t < 455:     # pull back from you to the whole galaxy
                k = sm((t - 410) / 45); dist = 30 * (1 + k * 120)
                tgt = our.lerp(Vector((0, 0, 0)), sm((t - 430) / 25) * 0.7)
                cp = our + Vector((0.4, 0.35 + 0.35 * k, 0.85)).normalized() * dist
            elif t < 476:   # glide toward the center (Sgr A*)
                k = sm((t - 458) / 14)
                tgt = our.lerp(Vector((0, 0, 0)), 0.7 + 0.3 * k)
                cp = (our + Vector((0.4, 0.7, 0.85)).normalized() * 3630).lerp(Vector((180, 520, 620)), k)
            else:           # turn back to you: you outshine the center
                k = sm((t - 478) / 8)
                tgt = Vector((0, 0, 0)).lerp(our, k)
                cp = Vector((180, 520, 620)).lerp(our + Vector((60, 220, 300)), k)
        else:
            k = sm((t - 495) / 25); tgt = our.lerp(Vector((0, 0, 0)), 0.5); cp = our + Vector((300, 900 + 2400 * k, 900 + 2400 * k))
        cam_key(cam, cp, tgt, f)
    return frame

ACTS = dict(house=act_house, shaft=act_shaft, cavity=act_cavity, plunge=act_plunge, surface=act_surface,
            space=act_space, galaxy=lambda: act_galaxy(False), outro=lambda: act_galaxy(True))

frame_fn = ACTS[ACT]()
if get("--thumb") and ACT == "surface":   # dramatic sunset backlight, only for the thumbnail still
    world_sunset(0.9, horizon=(1.0, 0.42, 0.12), mid=(0.85, 0.3, 0.38), top=(0.06, 0.1, 0.32))
    for o in scene.objects:
        if o.type == 'LIGHT' and o.data.type == 'SUN':
            o.data.energy = 6.0; o.data.color = (1.0, 0.55, 0.3); o.data.angle = math.radians(1.5)
            look_rot(o, B(2, 9, -100), B(1, 0, 0))
        if o.name.startswith("hand"): o.hide_render = True
        for ch in getattr(o, "children_recursive", []):
            if o.name.startswith("hand"): ch.hide_render = True
    ico("sundisc", 9, 0, (2, 13, -300), sub=3, material=emission_mat(0xfff0c0, 12.0))
    ico("sunhalo", 22, 0, (2, 13, -310), sub=3, material=emission_mat(0xff9a50, 2.5))
f_lo, f_hi = F0, F1
if TIMES:
    fr = [int(round(float(x) * FPS)) + 1 for x in TIMES.split(",")]
    f_lo, f_hi = max(F0, min(fr) - 2), min(F1, max(fr) + 2)   # bake only around the requested stills
elif FRAMES:
    a, b = map(int, FRAMES.split("-")); f_lo, f_hi = max(F0, a), min(F1, b)
for f in range(f_lo, f_hi + 1):
    frame_fn(TL.o((f - 1) / FPS), f)
setup_render(scene, OUT, RES, ENGINE, SAMPLES, DEVICE, FPS, f_lo, f_hi, exposure=0.6 if get("--thumb") else {"house": 0.35, "surface": 0.2}.get(ACT, 0.0))
if get("--thumb"):
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = 0.3
    for o in scene.objects:
        if o.name.startswith("hand"):
            for x in [o] + list(o.children_recursive): x.animation_data_clear(); x.hide_render = True
render(scene, TIMES.split(",") if TIMES else None, FPS)
print(f"[scene] act {ACT} done", flush=True)
