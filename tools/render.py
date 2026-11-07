"""Full pipeline for one video:  Blender render -> 2D overlay -> audio -> mp4.
Usage:  python3 tools/render.py VIDEO [--preview] [--engine cycles|eevee] [--samples N] [--device gpu|cpu]
Output: $OUT_DIR/VIDEO.mp4   (OUT_DIR defaults to /workspace/polywhat-out if /workspace exists, else ./out)
Re-running resumes: frames already rendered/composited are skipped."""
import argparse, glob, importlib.util, os, shutil, subprocess, sys, time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

def log(*a): print("[polywhat]", *a, flush=True)

def find_blender():
    cands = [os.environ.get("BLENDER"), "/workspace/blender/blender", shutil.which("blender")]
    for c in cands:
        if c and os.path.exists(c): return [c, "-b", "--factory-startup", "-P"]
    try:
        import bpy  # noqa: F401  (local dev: Blender as a python module)
        return [sys.executable]
    except Exception:
        sys.exit("Blender not found: run tools/setup.sh or set BLENDER=/path/to/blender")

def load_timeline(vdir):
    spec = importlib.util.spec_from_file_location("timeline", os.path.join(vdir, "timeline.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

_TL = None
def _comp(job):
    src, dst, t, vdir = job
    global _TL
    if _TL is None: _TL = load_timeline(vdir)
    from overlay import compose
    from PIL import Image
    compose(Image.open(src), t, _TL).save(dst, quality=94)
    return dst

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--preview", action="store_true")
    ap.add_argument("--engine", default="eevee"); ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--device", default="gpu"); ap.add_argument("--res", default=None)
    ap.add_argument("--bench", type=int, default=0, help="render only the first N frames and report seconds per frame")
    ap.add_argument("--shorts", action="store_true", help="render only the Shorts segments (videos/X/shorts.py) and build the vertical Shorts")
    ap.add_argument("--loop", action="store_true", help="make the purpose-built 10 s loop Short (videos/X/loop.py)")
    a = ap.parse_args()
    if a.loop:
        sys.exit(subprocess.run([sys.executable, os.path.join(ROOT, "tools", "loopshort.py"), a.video, "--device", a.device]
                                + (["--preview"] if a.preview else [])).returncode)
    vdir = os.path.join(ROOT, "videos", a.video)
    if not os.path.isdir(vdir): sys.exit(f"unknown video '{a.video}'. Available: {os.listdir(os.path.join(ROOT, 'videos'))}")
    out_root = os.environ.get("OUT_DIR") or ("/workspace/polywhat-out" if os.path.isdir("/workspace") else os.path.join(ROOT, "out"))
    tag = a.video + ("-" + a.engine if a.engine != "eevee" else "") + ("-preview" if a.preview else "") + (f"-bench" if a.bench else "")
    work = os.path.join(out_root, tag); raw, comp = os.path.join(work, "raw"), os.path.join(work, "comp")
    os.makedirs(raw, exist_ok=True); os.makedirs(comp, exist_ok=True)
    TL = load_timeline(vdir)
    res = a.res or ("960x540" if a.preview else "1920x1080")
    samples = a.samples or ((16 if a.preview else 64) if a.engine == "cycles" else (12 if a.preview else 24))
    t0 = time.time()

    log(f"1/4 3D render {a.video} {res} engine={a.engine} samples={samples}")
    base = find_blender() + [os.path.join(vdir, "scene.py"), "--", "--out", raw, "--res", res,
                             "--engine", a.engine, "--samples", str(samples), "--device", a.device]
    acts = getattr(TL, "ACTS", None)
    def done_frames():
        return {int(os.path.basename(f)[:-4]) for f in glob.glob(os.path.join(raw, "*.png")) if os.path.getsize(f) > 0 and os.path.basename(f)[:-4].isdigit()}
    if a.shorts:
        spec = importlib.util.spec_from_file_location("shorts", os.path.join(vdir, "shorts.py")); SM = importlib.util.module_from_spec(spec); spec.loader.exec_module(SM)
        fr_ = lambda x: int(round(x * TL.FPS)) + 1
        segs = [(fr_(c0), fr_(c1)) for s in SM.SHORTS for c0, c1, _ in s["clips"]]
        for name, s0, s1 in acts:
            f0, f1 = int(round(s0 * TL.FPS)) + 1, int(round(s1 * TL.FPS))
            for g0, g1 in segs:
                a0, a1 = max(f0, g0), min(f1, g1)
                if a0 > a1: continue
                have = done_frames()
                if all(f in have for f in range(a0, a1 + 1)): continue
                ta = time.time(); log(f"   act {name}: frames {a0}-{a1}")
                subprocess.run(base + ["--act", name, "--frames", f"{a0}-{a1}"], check=True)
                log(f"   {time.time() - ta:.0f}s")
        wav = os.path.join(work, "audio.wav")
        if not os.path.exists(wav): subprocess.run([sys.executable, os.path.join(vdir, "audio.py"), wav], check=True)
        by_num = {int(os.path.basename(f)[:-4]): f for f in glob.glob(os.path.join(raw, "*.png")) if os.path.basename(f)[:-4].isdigit()}
        for i, sh in enumerate(SM.SHORTS, 1):      # clean{i}.mp4 = the short's clips back to back (picture + audio), no overlay
            clean = os.path.join(out_root, f"{a.video}-clean{i}.mp4")
            seq = os.path.join(work, f"seq{i}"); shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq); j = 0
            for c0, c1, _ in sh["clips"]:
                for fn in range(fr_(c0), fr_(c1)): os.symlink(by_num[fn], os.path.join(seq, f"{j:05d}.png")); j += 1
            af = "".join(f"[1:a]atrim=start={c0:.3f}:end={c1:.3f},asetpts=PTS-STARTPTS[a{k}];" for k, (c0, c1, _) in enumerate(sh["clips"]))
            af += "".join(f"[a{k}]" for k in range(len(sh["clips"]))) + f"concat=n={len(sh['clips'])}:v=0:a=1,loudnorm=I=-14:TP=-1.5[aout]"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(TL.FPS), "-i", os.path.join(seq, "%05d.png"), "-i", wav,
                            "-filter_complex", af, "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", clean], check=True)
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "shorts.py"), a.video, "--clean", "--out", out_root], check=True)
        log(f"DONE shorts in {(time.time() - t0) / 60:.1f} min -> {out_root}/{a.video}-short*.mp4"); return
    if a.bench:
        cmd = base + ["--frames", f"1-{a.bench}"] + (["--act", acts[0][0]] if acts else [])
        tb = time.time(); subprocess.run(cmd, check=True); el = time.time() - tb
        log(f"BENCH {a.bench} frames in {el:.0f}s (includes ~10-30s startup) -> ~{el / a.bench:.2f} s/frame"); return
    if acts:
        for name, s0, s1 in acts:
            f0, f1 = int(round(s0 * TL.FPS)) + 1, int(round(s1 * TL.FPS))
            have = done_frames()
            if all(f in have for f in range(f0, f1 + 1)):
                log(f"   act {name}: already rendered"); continue
            ta = time.time(); log(f"   act {name}: frames {f0}-{f1}")
            subprocess.run(base + ["--act", name], check=True)
            log(f"   act {name}: {time.time() - ta:.0f}s ({(time.time() - ta) / (f1 - f0 + 1):.2f} s/frame)")
    else:
        subprocess.run(base, check=True)
    frames = sorted((f for f in glob.glob(os.path.join(raw, "*.png")) if os.path.getsize(f) > 0 and os.path.basename(f)[:-4].isdigit()),
                    key=lambda f: int(os.path.basename(f)[:-4]))
    n_exp = int(TL.DURATION * TL.FPS)
    if len(frames) < n_exp: sys.exit(f"only {len(frames)}/{n_exp} frames rendered — re-run the same command to resume")
    log(f"   {len(frames)} frames in {time.time() - t0:.0f}s")

    log("2/4 overlay (HUD + captions)")
    jobs = []
    for i, f in enumerate(frames):
        dst = os.path.join(comp, f"{i + 1:05d}.jpg")
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(f): jobs.append((f, dst, i / TL.FPS, vdir))   # redo if the raw frame was re-rendered
    with Pool(max(1, os.cpu_count() - 1)) as p:
        for k, _ in enumerate(p.imap_unordered(_comp, jobs, chunksize=8)):
            if k % 300 == 0: log(f"   {k}/{len(jobs)}")

    log("3/4 audio")
    wav = os.path.join(work, "audio.wav")
    subprocess.run([sys.executable, os.path.join(vdir, "audio.py"), wav], check=True)

    log("4/4 encode")
    mp4 = os.path.join(out_root, tag + ".mp4"); tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(TL.FPS), "-i", os.path.join(comp, "%05d.jpg"),
                    "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-15:TP=-1.5", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)
    if not a.preview and not a.bench:   # small review copy (~1/10 size) to send over chat
        light = os.path.join(out_root, tag + "-light.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", "scale=854:480", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", light], check=True)
        log(f"light copy -> {light}")
    log(f"DONE in {(time.time() - t0) / 60:.1f} min -> {mp4}")

if __name__ == "__main__":
    main()
