"""Vertical Shorts (1080x1920) cut from a finished video.
    python3 tools/shorts.py heavier [--src /workspace/polywhat-out/heavier.mp4] [--out DIR] [--only 1,3]
Segments come from videos/<name>/shorts.py: SHORTS = [dict(start=, end=, hook="...")].
Layout: hook + live mass/hour counter on top, centre crop of the video (clean of the 16:9 HUD and captions),
the current caption below, 'full video' prompt at the end."""
import importlib.util, os, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from overlay import serif, italic, sans, spaced, rich  # noqa

def shadow_text(base, xy, text, f, fill, anchor, blur, alpha):
    """text with a soft drop shadow; blurs only the text's own box (fast at 1080x1920)."""
    if alpha <= 0: return
    d = ImageDraw.Draw(base); x0, y0, x1, y1 = d.textbbox(xy, text, font=f, anchor=anchor); pad = int(blur * 3)
    box = (max(0, x0 - pad), max(0, y0 - pad), min(base.width, x1 + pad), min(base.height, y1 + pad))
    lay = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.text((xy[0] - box[0], xy[1] - box[1]), text, font=f, fill=(0, 0, 0, int(170 * alpha)), anchor=anchor)
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)), (box[0], box[1]))
    ImageDraw.Draw(base).text(xy, text, font=f, fill=fill[:3] + (int(fill[3] * alpha),), anchor=anchor)

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    a = sys.argv[1:]; name = a[0]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    src = opt("--src", f"/workspace/polywhat-out/{name}.mp4"); out = opt("--out", os.path.dirname(src) or ".")
    vdir = os.path.join(ROOT, "videos", name); sys.path.insert(0, vdir)
    TL = load(os.path.join(vdir, "timeline.py"), "timeline"); SH = load(os.path.join(vdir, "shorts.py"), "shorts").SHORTS
    only = [int(x) for x in opt("--only", "").split(",") if x]
    clean = "--clean" in a
    probe_src = os.path.join(out, f"{name}-clean1.mp4") if clean else src
    W0, H0 = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                                "-of", "csv=p=0", probe_src]).decode().split(","))
    k = W0 / 1920.0
    cw, ch, cx, cy = int(792 * k) // 2 * 2, int(880 * k) // 2 * 2, int(564 * k), int(30 * k)
    OW, OH, VY, VH = 1080, 1920, 420, 1200
    EDGE = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); gd = ImageDraw.Draw(EDGE)   # soft edges into the bands
    for y in range(90):
        a_ = int(200 * (1 - y / 90)); gd.line([(0, VY + y), (OW, VY + y)], fill=(6, 7, 12, a_)); gd.line([(0, VY + VH - 1 - y), (OW, VY + VH - 1 - y)], fill=(6, 7, 12, a_))
    for i, s in enumerate(SH, 1):
        if only and i not in only: continue
        t0, t1 = s["start"], s["end"]; dur = t1 - t0
        dst = os.path.join(out, f"{name}-short{i}.mp4")
        vsrc, seek = (os.path.join(out, f"{name}-clean{i}.mp4"), 0.0) if clean else (src, t0)
        dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(seek), "-t", str(dur), "-i", vsrc, "-vf",
                                f"crop={cw}:{ch}:{cx}:{cy},scale={OW}:{VH}:flags=lanczos,fps=30", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               stdout=subprocess.PIPE)
        enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", "30", "-i", "-",
                                "-ss", str(seek), "-t", str(dur), "-i", vsrc, "-map", "0:v", "-map", "1:a",
                                "-af", f"afade=t=in:d=0.25,afade=t=out:st={dur - 0.6}:d=0.6",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                                "-movflags", "+faststart", "-shortest", dst], stdin=subprocess.PIPE)
        fsz = OW * VH * 3; n = 0
        while True:
            raw = dec.stdout.read(fsz)
            if len(raw) < fsz: break
            t = t0 + n / 30.0; n += 1
            frame = Image.new("RGBA", (OW, OH), (6, 7, 12, 255))
            frame.paste(Image.frombytes("RGB", (OW, VH), raw), (0, VY))
            frame.alpha_composite(EDGE)
            d = ImageDraw.Draw(frame); st = TL.hud_state(t)
            # hook
            hk = s["hook"]; f = italic(60)
            while d.textlength(hk, font=f) > OW - 100: f = italic(f.size - 2)
            shadow_text(frame, (OW // 2, 105), hk, f, (255, 255, 255, 255), "ms", 10, 1.0); d = ImageDraw.Draw(frame)
            # counter
            spaced(d, (60, 190), TL.HUD["label"], sans(22), (255, 255, 255, 230), 4)
            vf = serif(118)
            while d.textlength(st["value"].replace("^", ""), font=vf) > 700: vf = serif(vf.size - 4)
            shadow_text(frame, (54, 318), st["value"], vf, (255, 255, 255, 255), "ls", 10, 1.0); d = ImageDraw.Draw(frame)
            sub = st["sub"]; sf = sans(19)
            while d.textlength(sub, font=sf) + len(sub) * 3 > 720: sf = sans(sf.size - 1)
            spaced(d, (60, 362), sub, sf, (255, 255, 255, 190), 3)
            spaced(d, (OW - 60, 190), TL.HUD["right_label"], sans(22), (255, 255, 255, 230), 4, anchor="rs")
            shadow_text(frame, (OW - 60, 318), st["right_value"], serif(118), (255, 255, 255, 255), "rs", 10, 1.0); d = ImageDraw.Draw(frame)
            d.rectangle([60, 382, 108, 385], fill=(255, 190, 90, 230))
            # caption
            for a_, b_, txt in TL.CAPTIONS:
                if a_ <= t <= b_:
                    al = min(1, (t - a_) / .3, (b_ - t) / .3)
                    lines = textwrap.wrap(txt, 30)
                    for j, ln in enumerate(lines[:3]):
                        shadow_text(frame, (OW // 2, 1712 + j * 70 - (len(lines) - 1) * 30), ln, italic(60), (255, 255, 255, 255), "ms", 12, max(0, al))
            if t > t1 - 3.2:
                d = ImageDraw.Draw(frame); al = min(1, (t - (t1 - 3.2)) / .4)
                tw = sum(d.textlength(c, font=sans(24)) + 4 for c in "FULL VIDEO ON THE CHANNEL") - 4
                spaced(d, (OW // 2 - tw / 2, 1880), "FULL VIDEO ON THE CHANNEL", sans(24), (255, 190, 90, int(255 * al)), 4)
            if n < 6: frame.alpha_composite(Image.new("RGBA", (OW, OH), (0, 0, 0, int(255 * (1 - n / 6)))))
            enc.stdin.write(frame.convert("RGB").tobytes())
        enc.stdin.close(); enc.wait(); dec.wait()
        print(f"[shorts] {dst}  ({dur:.0f}s, {n} frames)", flush=True)

if __name__ == "__main__":
    main()
