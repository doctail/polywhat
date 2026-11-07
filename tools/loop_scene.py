"""Blender scene for a seamless 10 s loop Short: an endless stack of identical rooms.
   dir=down : your weight doubles -> the floor cracks and gives way, you drop into the identical room below, again and again
   dir=up   : your weight halves  -> you drift up, push through the ceiling into the identical room above, again and again
   blender -b -P loop_scene.py -- --dir down --out DIR [--res 1080x1920] [--samples 24] [--frames a-b] [--times 1,2]
The camera after one full loop sits exactly N_CYCLES floors lower/higher, so frame LAST+1 == frame 1."""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pw3d import *  # noqa

get = args(sys.argv)
DIR = get("--dir", "down"); OUT = get("--out", "/tmp/loop_raw"); RES = get("--res", "1080x1920")
ENGINE = get("--engine", "eevee"); SAMPLES = int(get("--samples", "24")); DEVICE = get("--device", "gpu")
TIMES = get("--times"); FRAMES = get("--frames")
FPS, DUR, NC = 30, 10.0, 3          # 10 s, 3 floors per loop
P = DUR / NC; H = 3.0; EYE = 1.62
scene = reset()
SGN = -1 if DIR == "down" else 1
LEVELS = range(-1, NC + 2)            # rooms drawn (level k sits at y = SGN*k*H)

def room(k):
    y0 = SGN * k * H; rr = random.Random(5)    # same seed: every room identical
    S = []
    W1, W2 = 0xc9d6dc, 0xbccbd2
    S.append(box(f"wb{k}", 7, H, 0.2, W1, (0, y0 + H / 2, 3.5))); S.append(box(f"wl{k}", 0.2, H, 7, W2, (-3.5, y0 + H / 2, 0)))
    S.append(box(f"wr{k}", 0.2, H, 7, W2, (3.5, y0 + H / 2, 0))); S.append(box(f"wf{k}", 7, H, 0.2, W1, (0, y0 + H / 2, -3.5)))
    S.append(box(f"win{k}", 1.6, 1.2, 0.05, 0x9fc6e8, (0.6, y0 + 1.6, -3.39), emit=1.2))
    S.append(box(f"frame{k}", 1.74, 1.34, 0.06, 0xffffff, (0.6, y0 + 1.6, -3.4)))
    S.append(box(f"bed{k}", 1.6, 0.5, 2.1, 0x6e4a30, (-2.4, y0 + 0.25, -2.2), bevel=0.03)); S.append(box(f"mat{k}", 1.5, 0.22, 2.0, 0xf3f1ec, (-2.4, y0 + 0.6, -2.2), bevel=0.06))
    S.append(box(f"blk{k}", 1.54, 0.08, 1.2, 0x5f8fae, (-2.4, y0 + 0.74, -1.9), bevel=0.03)); S.append(box(f"pil{k}", 0.7, 0.14, 0.4, 0xffffff, (-2.4, y0 + 0.78, -3.0), bevel=0.05))
    S.append(box(f"ward{k}", 0.6, 2.1, 1.3, 0x7d5a3c, (3.1, y0 + 1.05, -1.6), bevel=0.02))
    S.append(box(f"desk{k}", 1.2, 0.75, 0.6, 0x8a6a4c, (2.6, y0 + 0.375, 1.2)))
    S.append(box(f"rug{k}", 2.2, 0.012, 0.9, 0xa0503c, (0.3, y0 + 0.006, -2.6)))
    for wx, wz, ww, wd in ((0, -3.38, 7, 0.04), (0, 3.38, 7, 0.04), (-3.38, 0, 0.04, 7), (3.38, 0, 0.04, 7)):
        S.append(box(f"base{k}{wx}{wz}", ww, 0.14, wd, 0xffffff, (wx, y0 + 0.07, wz)))
    S.append(box(f"pic{k}", 0.05, 0.7, 1.0, 0x2a3440, (-3.38, y0 + 1.7, -1.0))); S.append(box(f"pica{k}", 0.03, 0.6, 0.9, 0xe0a050, (-3.35, y0 + 1.7, -1.0)))
    S.append(box(f"pot{k}", 0.35, 0.4, 0.35, 0xb85c38, (2.9, y0 + 0.2, -3.0))); S.append(ico(f"plant{k}", 0.42, 0x3f7d3a, (2.9, y0 + 0.7, -3.0)))
    S.append(box(f"ns{k}", 0.5, 0.55, 0.45, 0x6e4a30, (-1.2, y0 + 0.275, -3.05))); S.append(box(f"nsl{k}", 0.2, 0.3, 0.2, 0xfff3d6, (-1.2, y0 + 0.7, -3.05), emit=2.0))
    S.append(box(f"lamp{k}", 0.5, 0.06, 0.5, 0xfff3d6, (-1.9, y0 + H - 0.30, 1.9), emit=4.0))
    for (cx_, cz_, w_, d_) in ((-2.4, 0, 2.2, 7), (2.4, 0, 2.2, 7), (0, -2.4, 2.6, 2.2), (0, 2.4, 2.6, 2.2)):   # ceiling panels around the hole zone
        S.append(box(f"ceilp{k}{cx_}{cz_}", w_, 0.04, d_, 0xf6f2ec, (cx_, y0 + H - 0.26, cz_)))
    L = light('AREA', f"pl{k}", 220, (1.0, 0.9, 0.78), (0.0, y0 + H - 0.35, 0.0), (0, y0, 0), size=2.5)
    # floor slab = planks (the middle ones are the ones that give way)
    planks = []
    for i in range(14):
        x = -3.25 + i * 0.5
        if abs(x) < 1.3:
            piv = empty(f"pk{k}_{i}", (x + (-0.25 if x < 0 else 0.25), y0, 0))
            off = -(-0.25 if x < 0 else 0.25)
            box("plank", 0.48, 0.24, 2.6, [0xa8774c, 0x9c6c42, 0xb08050][i % 3], (off, -0.12, 0), parent=piv, bevel=0.01)
            box("ceilunder", 0.5, 0.04, 2.6, 0xf6f2ec, (off, -0.26, 0), parent=piv)
            planks.append((piv, 1 if x < 0 else -1))
        else: S.append(box(f"fl{k}_{i}", 0.48, 0.24, 7, [0xa8774c, 0x9c6c42, 0xb08050][i % 3], (x, y0 - 0.12, 0), bevel=0.01))
    for z in (-2.4, 2.4): S.append(box(f"flz{k}{z}", 2.6, 0.24, 2.2, 0xa3734a, (0, y0 - 0.12, z)))
    # cracks on the floor (dark seams) - grown by scaling
    cr = empty(f"cracks{k}", (0, y0 + 0.004, 0))
    for j in range(8):
        a = j / 8 * math.tau + rr.uniform(-0.3, 0.3); px, pz = 0.0, 0.0
        for seg in range(4):
            ln = rr.uniform(0.18, 0.38); a2 = a + rr.uniform(-0.5, 0.5); nx, nz = px + math.cos(a2) * ln, pz + math.sin(a2) * ln
            c = box("crack", 0.022 * (1 - seg * 0.2), 0.01, ln, 0x24160c, ((px + nx) / 2, 0, (pz + nz) / 2), parent=cr); c.rotation_euler = (0, 0, -a2 + math.pi / 2)
            px, pz = nx, nz
    return S, planks, cr

world((0.3, 0.32, 0.36), 0.4)
statics = []; floors = {}
for k in LEVELS:
    S, planks, cr = room(k); statics += S; floors[k] = (planks, cr)
merge_static("rooms", statics); bake_modifiers(scene)
cam = camera(80)
hL, hR = hand(cam, -1), hand(cam, 1)
legs = link(bpy.data.objects.new("legs", None))
for s in (-1, 1):
    shoe = empty(f"shoe{s}", (s * 0.12, 0, -0.05)); shoe.parent = legs; shoe.location = B(s * 0.12, 0.0, -0.05)
    box("sole", 0.112, 0.03, 0.29, 0xf4f4f2, (0, 0.015, -0.01), parent=shoe, bevel=0.014)
    box("upper", 0.1, 0.075, 0.2, 0x2f4a66, (0, 0.07, 0.03), parent=shoe, bevel=0.035)
    box("toe", 0.1, 0.05, 0.09, 0x2f4a66, (0, 0.05, -0.1), parent=shoe, bevel=0.028)

def phase(t): return t % P, int(t // P)

def body_y(t):
    """floor level under your feet (down) / height of your eyes (up)"""
    p, c = phase(t)
    if DIR == "down":
        base = -c * H
        if p < 0.45: return base + lerp(EYE - 0.38, EYE, sm(p / 0.45))                 # stand back up after landing
        if p < 2.2: return base + EYE - 0.02 * math.sin(p * 9) * cl((p - 1.2) / 1.0)   # trembling as it cracks
        if p < 3.0: k = (p - 2.2) / 0.8; return base + EYE - (H + 0.38) * k * k     # drop
        return base - H + EYE - 0.38                                                   # crouched on the next floor
    else:
        base = c * H
        # drift up from eye height to the ceiling, press, break through, keep rising to the same height one floor up
        if p < 2.0: return base + lerp(EYE, H - 0.42, sm(p / 2.0) * 0.7 + (p / 2.0) * 0.3)
        if p < 2.4: return base + H - 0.42 + 0.03 * math.sin((p - 2.0) * 30)           # pushing against the ceiling
        k = (p - 2.4) / (P - 2.4); return base + lerp(H - 0.42, H + EYE, sm(k))

def frame(f):
    t = (f - 1) / FPS; p, c = phase(t)
    y = body_y(t)
    shake = 0.0
    if DIR == "down":
        if 2.15 < p < 2.6: shake = 0.03 * (1 - (p - 2.15) / 0.45)
        if 3.0 < p or p < 0.25: shake = max(shake, 0.04 * (1 - ((p - 3.0) if p > 3.0 else (p + P - 3.0)) / 0.6))
        pos = Vector((0.05, y, 0.75)) + Vector((math.sin(t * 61) * shake, math.sin(t * 47) * shake, 0))
        look = Vector((0.0, y - 1.25, -1.6))
        cam_key(cam, pos, look, f)
        ly = (-c * H) if p < 2.2 else (y - EYE)
        if p >= 3.0: ly = -(c + 1) * H
        legs.location = B(0.05, ly, 0.42); key(legs, "location", f)
        vis(hL, True, f); vis(hR, True, f)
    else:
        pos = Vector((0.05, y, 0.3)); look = Vector((0.0, y + 1.5, -0.7))
        if 1.9 < p < 2.5: pos += Vector((math.sin(t * 50) * 0.01, 0, 0))
        cam_key(cam, pos, look, f)
        legs.location = B(0, -50, 0); key(legs, "location", f)
        vis(hL, False, f); vis(hR, False, f)
        press = cl((p - 1.5) / 0.5) * (1 - cl((p - 2.5) / 0.4))
        for h, s in ((hL, -1), (hR, 1)):
            h.location = (s * 0.26, lerp(-0.2, 0.05, press), lerp(-0.5, -0.38, press)); h.rotation_euler = (lerp(-0.2, 1.35, press), s * -0.2, s * -0.15)
            key(h, "location", f); key(h, "rotation_euler", f)
    # floors: level c's middle planks crack and give way during this cycle; levels already passed stay open
    for k, (planks, cr) in floors.items():
        lvl = k if DIR == "down" else k + 1          # 'up' breaks the floor slab ABOVE you (= floor of room k+1)
        if lvl not in floors: continue
        pl, crk = floors[lvl]
        if lvl - (0 if DIR == "down" else 1) < c: g = 1.0               # already broken
        elif lvl - (0 if DIR == "down" else 1) > c: g = 0.0
        else: g = cl((p - (2.2 if DIR == "down" else 2.35)) / 0.35)
        cg = 1.0 if lvl - (0 if DIR == "down" else 1) < c else (0.0 if lvl - (0 if DIR == "down" else 1) > c else cl((p - 0.7) / 1.4))
        crk.scale = (max(cg, 0.001) if g <= 0.02 else 0.001,) * 3; key(crk, "scale", f)
        for piv, s in pl:
            ang = g * 1.35 * (1 if DIR == "down" else -1)
            piv.rotation_euler = (0, s * ang, 0); key(piv, "rotation_euler", f)

f_lo, f_hi = 1, int(DUR * FPS)
if TIMES:
    frs = [int(round(float(x) * FPS)) + 1 for x in TIMES.split(",")]; f_lo, f_hi = max(1, min(frs) - 1), min(f_hi, max(frs) + 1)
elif FRAMES:
    a, b = map(int, FRAMES.split("-")); f_lo, f_hi = max(f_lo, a), min(f_hi, b)
for f in range(f_lo, f_hi + 1): frame(f)
setup_render(scene, OUT, RES, ENGINE, SAMPLES, DEVICE, FPS, f_lo, f_hi, exposure=0.3)
scene.render.use_motion_blur = False
render(scene, TIMES.split(",") if TIMES else None, FPS)
print("[loop] done", flush=True)
