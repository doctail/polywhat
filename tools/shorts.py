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

END_HOLD = 1.6   # seconds of end card (last frame, darkened, with the open question)

def clip_audio_filter(n_inputs_specs, total_end_pad):
    """filter_complex that trims each (input, seek, dur) piece, fades its edges and concatenates them."""
    parts, labels = [], []
    for j, (inp, seek, dur) in enumerate(n_inputs_specs):
        parts.append(f"[{inp}:a]atrim=start={seek:.3f}:duration={dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st={max(0, dur - 0.06):.3f}:d=0.06[a{j}]")
        labels.append(f"[a{j}]")
    parts.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1,apad=pad_dur={total_end_pad:.2f}[aout]")
    return ";".join(parts)

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
    if clean: cw, ch, cx, cy = int(792 * k) // 2 * 2, int(880 * k) // 2 * 2, int(564 * k), int(30 * k)    # raw render: no HUD to dodge
    else:     cw, ch, cx, cy = int(644 * k) // 2 * 2, int(716 * k) // 2 * 2, int(638 * k), int(205 * k)   # finished video: stay clear of HUD + captions
    OW, OH, VY, VH = 1080, 1920, 420, 1200
    EDGE = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); gd = ImageDraw.Draw(EDGE)
    for y in range(90):
        a_ = int(200 * (1 - y / 90)); gd.line([(0, VY + y), (OW, VY + y)], fill=(6, 7, 12, a_)); gd.line([(0, VY + VH - 1 - y), (OW, VY + VH - 1 - y)], fill=(6, 7, 12, a_))
    def text_c(frame, y, txt, f, col, al=1.0, blur=12):
        shadow_text(frame, (OW // 2, y), txt, f, col, "ms", blur, al)
    for i, s in enumerate(SH, 1):
        if only and i not in only: continue
        clips = s["clips"]; dst = os.path.join(out, f"{name}-short{i}.mp4")
        # where each clip's pixels come from
        pieces, acc = [], 0.0
        for (c0, c1, _) in clips:
            if clean: pieces.append((os.path.join(out, f"{name}-clean{i}.mp4"), acc, c1 - c0)); acc += c1 - c0
            else: pieces.append((src, c0, c1 - c0))
        total = sum(c1 - c0 for c0, c1, _ in clips) + END_HOLD
        srcs = sorted(set(p[0] for p in pieces)); idx = {p: j + 1 for j, p in enumerate(srcs)}
        enc_cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", "30", "-i", "-"]
        for p in srcs: enc_cmd += ["-i", p]
        enc_cmd += ["-filter_complex", clip_audio_filter([(idx[p], sk, du) for p, sk, du in pieces], END_HOLD), "-map", "0:v", "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-t", f"{total:.3f}", "-movflags", "+faststart", dst]
        enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)
        fsz = OW * VH * 3; n = 0; last = None; tl = 0.0
        for ci, ((c0, c1, line), (p, sk, du)) in enumerate(zip(clips, pieces)):
            dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{sk:.3f}", "-t", f"{du:.3f}", "-i", p, "-vf",
                                    f"crop={cw}:{ch}:{cx}:{cy},scale={OW}:{VH}:flags=lanczos,fps=30", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            m = 0
            while True:
                raw = dec.stdout.read(fsz)
                if len(raw) < fsz: break
                t = c0 + m / 30.0; m += 1; n += 1
                frame = Image.new("RGBA", (OW, OH), (6, 7, 12, 255)); frame.paste(Image.frombytes("RGB", (OW, VH), raw), (0, VY)); frame.alpha_composite(EDGE)
                d = ImageDraw.Draw(frame); st = TL.hud_state(t)
                hk = s["hook"]; f = italic(64)
                while d.textlength(hk, font=f) > OW - 90: f = italic(f.size - 2)
                text_c(frame, 108, hk, f, (255, 255, 255, 255), 1.0, 10); d = ImageDraw.Draw(frame)
                spaced(d, (60, 190), TL.HUD["label"], sans(22), (255, 255, 255, 230), 4)
                vf = serif(122)
                while d.textlength(st["value"].replace("^", ""), font=vf) > 700: vf = serif(vf.size - 4)
                pop = 1.0 + 0.08 * max(0, 1 - m / 5)          # value 'pops' on every cut
                vf = serif(int(vf.size * pop))
                shadow_text(frame, (54, 318), st["value"], vf, (255, 255, 255, 255), "ls", 10, 1.0); d = ImageDraw.Draw(frame)
                sub = st["sub"]; sf = sans(19)
                while d.textlength(sub, font=sf) + len(sub) * 3 > 720: sf = sans(sf.size - 1)
                spaced(d, (60, 362), sub, sf, (255, 255, 255, 190), 3)
                spaced(d, (OW - 60, 190), TL.HUD["right_label"], sans(22), (255, 255, 255, 230), 4, anchor="rs")
                shadow_text(frame, (OW - 60, 318), st["right_value"], serif(int(122 * pop)), (255, 255, 255, 255), "rs", 10, 1.0); d = ImageDraw.Draw(frame)
                d.rectangle([60, 382, 108, 385], fill=(255, 190, 90, 230))
                if line:
                    al = min(1.0, m / 4); text_c(frame, 1745, line, italic(66), (255, 255, 255, 255), al)
                if m <= 2: frame.alpha_composite(Image.new("RGBA", (OW, OH), (255, 255, 255, 70 if m == 1 else 30)))   # flash on cut
                last = frame
                enc.stdin.write(frame.convert("RGB").tobytes())
            dec.wait()
        # end card: freeze, darken, open question + full-video prompt
        for j in range(int(END_HOLD * 30)):
            fr_ = last.copy(); al = min(1.0, j / 6)
            fr_.alpha_composite(Image.new("RGBA", (OW, OH), (0, 0, 0, int(150 * al))))
            text_c(fr_, 1000, s["end"], italic(76), (255, 255, 255, 255), al)
            tw = sum(ImageDraw.Draw(fr_).textlength(c, font=sans(26)) + 5 for c in "FULL VIDEO ON THE CHANNEL") - 5
            spaced(ImageDraw.Draw(fr_), (OW // 2 - tw / 2, 1110), "FULL VIDEO ON THE CHANNEL", sans(26), (255, 190, 90, int(255 * al)), 5)
            enc.stdin.write(fr_.convert("RGB").tobytes())
        enc.stdin.close(); enc.wait()
        print(f"[shorts] {dst}  ({total:.1f}s, {len(clips)} cuts)", flush=True)

if __name__ == "__main__":
    main()
