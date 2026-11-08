"""Seamless 10 s 'never stop shrinking' loop: a room with a tiny copy of itself on the rug, which has a tinier copy, ...
The camera shrinks continuously toward the fixed point of the room->mini-room similarity, so after one loop it is in
exactly the same pose one level down: frame LAST+1 == frame 1 (an infinite-zoom / Droste loop).
   blender -b -P droste_scene.py -- --out DIR [--res 1080x1920] [--samples 24] [--times 0,5]"""
import bpy, math, os, random, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pw3d import *  # noqa

get = args(sys.argv)
OUT = get("--out", "/tmp/droste_raw"); RES = get("--res", "1080x1920"); ENGINE = get("--engine", "eevee")
SAMPLES = int(get("--samples", "24")); DEVICE = get("--device", "gpu"); TIMES = get("--times"); FRAMES = get("--frames")
FPS, DUR = 30, 10.0
S = 1.0 / 16.0                      # each room is 1/16 of the one around it (= 4 halvings per loop)
LEVELS = 5
O1 = Vector((0.85, 0.016, -1.55))   # where the mini room sits (design coords, ON TOP of the rug)
FIX = O1 / (1 - S)                  # fixed point of x -> O1 + S*x
scene = reset(); scene.view_settings.exposure = 0.25

def build_room(parent):
    """one room (no ceiling), built in local design coords around the origin, parented to `parent`."""
    W1, W2 = 0xd9cbb6, 0xcbb9a0
    H = 2.6
    box("floor", 7, 0.1, 7, 0xa8774c, (0, -0.05, 0), parent=parent)
    for i in range(14): box("seam", 0.012, 0.004, 7, 0x80583a, (-3.5 + i * 0.5, 0.002, 0), parent=parent)
    box("wb", 7, H, 0.2, W1, (0, H / 2, -3.5), parent=parent); box("wf", 7, H, 0.2, W1, (0, H / 2, 3.5), parent=parent)
    box("wl", 0.2, H, 7, W2, (-3.5, H / 2, 0), parent=parent); box("wr", 0.2, H, 7, W2, (3.5, H / 2, 0), parent=parent)
    for (x, z, w, d) in ((0, -3.38, 7, 0.04), (0, 3.38, 7, 0.04), (-3.38, 0, 0.04, 7), (3.38, 0, 0.04, 7)):
        box("base", w, 0.14, d, 0xffffff, (x, 0.07, z), parent=parent)
    box("win", 1.8, 1.3, 0.05, 0xbfe0ff, (0.4, 1.55, -3.38), parent=parent, emit=2.2)
    box("winf", 1.94, 1.44, 0.06, 0xffffff, (0.4, 1.55, -3.39), parent=parent)
    box("rug", 2.6, 0.012, 2.0, 0xb8432e, (0.85, 0.006, -1.55), parent=parent)
    box("rugb", 2.3, 0.013, 1.7, 0xd9a441, (0.85, 0.007, -1.55), parent=parent)
    box("bedframe", 1.7, 0.4, 2.2, 0x6e4a30, (-2.4, 0.2, 1.8), parent=parent, bevel=0.03)
    box("mattress", 1.6, 0.25, 2.1, 0xf3f1ec, (-2.4, 0.52, 1.8), parent=parent, bevel=0.06)
    box("blanket", 1.64, 0.08, 1.3, 0x3f6fa8, (-2.4, 0.68, 1.5), parent=parent, bevel=0.03)
    box("pillow", 0.75, 0.16, 0.42, 0xffffff, (-2.4, 0.72, 2.7), parent=parent, bevel=0.06)
    box("ward", 0.6, 2.1, 1.4, 0x7d5a3c, (3.05, 1.05, 1.2), parent=parent, bevel=0.02)
    box("desk", 1.3, 0.75, 0.65, 0x8a6a4c, (-2.6, 0.375, -2.8), parent=parent)
    box("lampb", 0.18, 0.3, 0.18, 0x333333, (-2.9, 0.9, -2.8), parent=parent); box("lamps", 0.36, 0.22, 0.36, 0xffe2a8, (-2.9, 1.15, -2.8), parent=parent, emit=3.0)
    box("book", 0.3, 0.05, 0.22, 0x2e7d6a, (-2.4, 0.78, -2.75), parent=parent)
    box("pot", 0.36, 0.42, 0.36, 0xb85c38, (2.9, 0.21, -2.9), parent=parent); ico("plant", 0.45, 0x3f7d3a, (2.9, 0.72, -2.9), parent=parent)
    box("ball", 0.26, 0.26, 0.26, 0xe8c02a, (-0.9, 0.13, -0.4), parent=parent, bevel=0.12)
    box("chair", 0.5, 0.5, 0.5, 0x3e5c6e, (-1.9, 0.25, -2.3), parent=parent, bevel=0.04)

world((0.55, 0.62, 0.72), 0.7)
sun(3.2, (6, 9, -4), (0, 0, 0), color=(1.0, 0.92, 0.82), angle=2.0)
for lv in range(LEVELS):
    sc = S ** lv
    org = O1 * (1 - sc) / (1 - S)          # origin of level lv
    e = empty(f"lvl{lv}", tuple(org)); e.scale = (sc, sc, sc)
    build_room(e)
bpy.context.view_layer.update()

cam = camera(70)
C0 = Vector((-0.1, 1.62, 0.55))             # standing in the big room, looking down at the little room on the rug
LOOK = (FIX - C0).normalized()

def frame(f):
    t = (f - 1) / FPS
    k = S ** (t / DUR)                      # continuous shrink: one full level per loop
    p = FIX + (C0 - FIX) * k
    sway = Vector((math.sin(t / DUR * math.tau) * 0.03, 0, math.cos(t / DUR * math.tau * 2) * 0.02)) * k   # periodic, so still seamless
    cam_key(cam, p + sway, p + sway + LOOK, f)
    cam.data.clip_start = 0.02 * k; cam.data.keyframe_insert("clip_start", frame=f)

f_lo, f_hi = 1, int(DUR * FPS)
if TIMES:
    frs = [int(round(float(x) * FPS)) + 1 for x in TIMES.split(",")]; f_lo, f_hi = max(1, min(frs) - 1), min(f_hi, max(frs) + 1)
elif FRAMES:
    a, b = map(int, FRAMES.split("-")); f_lo, f_hi = max(f_lo, a), min(f_hi, b)
for f in range(f_lo, f_hi + 1): frame(f)
setup_render(scene, OUT, RES, ENGINE, SAMPLES, DEVICE, FPS, f_lo, f_hi, exposure=0.25)
scene.render.use_motion_blur = False
render(scene, TIMES.split(",") if TIMES else None, FPS)
print("[droste] done", flush=True)
