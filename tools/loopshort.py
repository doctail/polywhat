"""Seamless 10 s loop Short, made on purpose (not cut from the long video).
    python3 tools/loopshort.py heavier [--preview] [--samples N] [--device gpu|cpu]
Config: videos/<name>/loop.py  ->  LOOP = dict(dir="down"|"up", lines=[(t0, t1, text)...], pop="×2", label="YOUR WEIGHT")
Output: $OUT_DIR/<name>-loop.mp4  (1080x1920, exactly 10.0 s; last frame flows into the first)"""
import importlib.util, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from overlay import serif, italic, sans, spaced          # noqa
from shorts import shadow_text                            # noqa
from render import find_blender, log                      # noqa
import sfx                                                # noqa

FPS, DUR, NC = 30, 10.0, 3
P = DUR / NC

def overlay(img, t, L):
    W, H = img.size; k = W / 1080
    base = img.convert("RGBA"); d = ImageDraw.Draw(base)
    # gradient for legibility
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(int(H * 0.35)):
        a = int(170 * (1 - y / (H * 0.35)) ** 1.5); gd.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, a))
    for y in range(int(H * 0.18)):
        a = int(120 * (1 - y / (H * 0.18))); gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    base.alpha_composite(g); d = ImageDraw.Draw(base)
    # label + pop at each break
    lab = L.get("label", "YOUR WEIGHT")
    tw = sum(d.textlength(c, font=sans(int(26 * k))) + 6 * k for c in lab) - 6 * k
    spaced(d, (W / 2 - tw / 2, int(150 * k)), lab, sans(int(26 * k)), (255, 255, 255, 220), 6 * k)
    p = t % P; tb = L.get("pop_at", 2.2)
    since = p - tb
    if since < 0: since += P
    sc = 1.0 + 0.35 * max(0.0, 1 - since / 0.25)
    shadow_text(base, (W // 2, int(330 * k)), L["pop"], serif(int(150 * k * sc)), (255, 205, 120, 255), "ms", 12 * k, 1.0)
    for a, b, txt in L["lines"]:
        if a <= t < b:
            al = min(1.0, (t - a) / 0.15, (b - t) / 0.15)
            lines = [txt] if ImageDraw.Draw(base).textlength(txt, font=italic(int(74 * k))) < W * 0.86 else _wrap(txt)
            for j, ln in enumerate(lines):
                shadow_text(base, (W // 2, int((1500 + j * 88 - (len(lines) - 1) * 44) * k)), ln, italic(int(74 * k)), (255, 255, 255, 255), "ms", 14 * k, al)
    return base.convert("RGB")

def _wrap(s):
    w = s.split(); h = len(w) // 2 + len(w) % 2
    return [" ".join(w[:h]), " ".join(w[h:])]

def audio(L, path):
    n = int(DUR * sfx.SR); x = np.zeros(n * 2)
    def add(t, sig, gain=1.0):
        i = int(t * sfx.SR); seg = sig[: max(0, len(x) - i)] * gain; x[i:i + len(seg)] += seg
    tt = np.arange(n * 2) / sfx.SR
    for c in range(NC + 1):                       # (one extra cycle so tails wrap into the start)
        o = c * P
        if L["dir"] == "down":
            add(o + 0.7, sfx.creak(1.4, 0.16, 12, 40, (250, 900)))
            add(o + 2.15, sfx.crack(0.4, 0.55, 14, 900, 6000)); add(o + 2.2, sfx.thud(48, 0.6, 0.45))
            add(o + 2.25, sfx.whoosh(0.75, 0.3, 200, 1500)); add(o + 3.0, sfx.thud(42, 0.9, 0.9)); add(o + 3.02, sfx.debris(0.6, 0.25))
        else:
            add(o + 0.2, sfx.whoosh(1.8, 0.12, 400, 2500)); add(o + 2.0, sfx.thud(70, 0.3, 0.3))
            add(o + 2.35, sfx.crack(0.35, 0.4, 10, 1200, 7000)); add(o + 2.45, sfx.whoosh(0.8, 0.3, 500, 3000))
    for i in range(int(DUR * 2) + 2):            # clock ticking: every hour, again
        add(i * 0.5, sfx.pluck(96 if i % 2 == 0 else 91, 0.08, 0.10))
    # drone with frequencies that complete whole cycles in 10 s -> seamless
    base = 55.0 if L["dir"] == "down" else 110.0
    for h, gnn in ((1, 0.06), (1.5, 0.03), (2, 0.03)):
        x[:n] += gnn * np.sin(2 * np.pi * round(base * h * DUR) / DUR * tt[:n]) * (1 + 0.3 * np.sin(2 * np.pi * NC / DUR * tt[:n]))
    y = x[:n] + np.concatenate([x[n:2 * n], np.zeros(0)])[:n]       # wrap the overflow onto the start
    y = np.tanh(y * 1.6) / 1.6
    sfx.write_wav(path, y, DUR)

def main():
    a = sys.argv[1:]; name = a[0]; preview = "--preview" in a
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    vdir = os.path.join(ROOT, "videos", name)
    spec = importlib.util.spec_from_file_location("loopcfg", os.path.join(vdir, "loop.py")); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M); L = M.LOOP
    out_root = os.environ.get("OUT_DIR") or ("/workspace/polywhat-out" if os.path.isdir("/workspace") else os.path.join(ROOT, "out"))
    tag = f"{name}-loop" + ("-preview" if preview else ""); work = os.path.join(out_root, tag); raw = os.path.join(work, "raw"); comp = os.path.join(work, "comp")
    os.makedirs(raw, exist_ok=True); os.makedirs(comp, exist_ok=True)
    res = opt("--res", "540x960" if preview else "1080x1920"); samples = opt("--samples", "8" if preview else "32")
    log(f"loop {name}: render {res}")
    subprocess.run(find_blender() + [os.path.join(ROOT, "tools", "loop_scene.py"), "--", "--dir", L["dir"], "--out", raw, "--res", res,
                                     "--samples", samples, "--device", opt("--device", "gpu")], check=True)
    frames = sorted([f for f in os.listdir(raw) if f[:-4].isdigit()], key=lambda f: int(f[:-4]))
    for i, f in enumerate(frames):
        overlay(Image.open(os.path.join(raw, f)), i / FPS, L).save(os.path.join(comp, f"{i:05d}.jpg"), quality=93)
    wav = os.path.join(work, "audio.wav"); audio(L, wav)
    mp4 = os.path.join(out_root, tag + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(comp, "%05d.jpg"), "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{DUR}", "-movflags", "+faststart", mp4], check=True)
    log(f"DONE -> {mp4}")

if __name__ == "__main__":
    main()
