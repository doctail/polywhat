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
    ap.add_argument("--engine", default="cycles"); ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--device", default="gpu"); ap.add_argument("--res", default=None)
    ap.add_argument("--bench", type=int, default=0, help="render only the first N frames and report seconds per frame")
    a = ap.parse_args()
    vdir = os.path.join(ROOT, "videos", a.video)
    if not os.path.isdir(vdir): sys.exit(f"unknown video '{a.video}'. Available: {os.listdir(os.path.join(ROOT, 'videos'))}")
    out_root = os.environ.get("OUT_DIR") or ("/workspace/polywhat-out" if os.path.isdir("/workspace") else os.path.join(ROOT, "out"))
    tag = a.video + ("-" + a.engine if a.engine != "cycles" else "") + ("-preview" if a.preview else "") + (f"-bench" if a.bench else "")
    work = os.path.join(out_root, tag); raw, comp = os.path.join(work, "raw"), os.path.join(work, "comp")
    os.makedirs(raw, exist_ok=True); os.makedirs(comp, exist_ok=True)
    TL = load_timeline(vdir)
    res = a.res or ("960x540" if a.preview else "1920x1080")
    samples = a.samples or ((16 if a.preview else 64) if a.engine == "cycles" else (16 if a.preview else 32))
    t0 = time.time()

    log(f"1/4 3D render {a.video} {res} engine={a.engine} samples={samples}")
    cmd = find_blender() + [os.path.join(vdir, "scene.py"), "--", "--out", raw, "--res", res,
                            "--engine", a.engine, "--samples", str(samples), "--device", a.device]
    if a.bench:
        cmd += ["--frames", f"1-{a.bench}"]
        tb = time.time(); subprocess.run(cmd, check=True); el = time.time() - tb
        log(f"BENCH {a.bench} frames in {el:.0f}s (includes ~10-30s startup) -> ~{el / a.bench:.2f} s/frame"); return
    subprocess.run(cmd, check=True)
    frames = sorted(f for f in glob.glob(os.path.join(raw, "*.png")) if os.path.getsize(f) > 0)
    n_exp = int(TL.DURATION * TL.FPS)
    if len(frames) < n_exp: sys.exit(f"only {len(frames)}/{n_exp} frames rendered — re-run the same command to resume")
    log(f"   {len(frames)} frames in {time.time() - t0:.0f}s")

    log("2/4 overlay (HUD + captions)")
    jobs = []
    for i, f in enumerate(frames):
        dst = os.path.join(comp, f"{i + 1:05d}.jpg")
        if not os.path.exists(dst): jobs.append((f, dst, i / TL.FPS, vdir))
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
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)
    log(f"DONE in {(time.time() - t0) / 60:.1f} min -> {mp4}")

if __name__ == "__main__":
    main()
