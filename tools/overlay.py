"""2D overlay compositor: vignette, HUD (top-left value block + top-right counter), italic captions, fades.
Reads everything from the video's timeline module so every video shares the same look."""
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")

@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)

def serif(s): return font("EBGaramond-Medium.ttf", s)
def italic(s): return font("EBGaramond-Italic.ttf", s)
def sans(s): return font("Inter-SemiBold.ttf", s)

ICONS = os.path.join(ROOT, "tools", "icons")
@lru_cache(None)
def icon_img(name, height):
    im = Image.open(os.path.join(ICONS, name + ".png")).convert("RGBA")
    return im.resize((int(im.width * height / im.height), height), Image.LANCZOS)

@lru_cache(None)
def vignette(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 * 0.8 + ((y - h / 2) / (h / 2)) ** 2 * 0.8)
    a = np.clip((d - 0.55) / 0.75, 0, 1) ** 1.6 * 0.55
    top = np.clip(1 - y / (h * 0.26), 0, 1) ** 1.5 * 0.40          # scrim behind the HUD
    alpha = np.clip(a + top * (1 - a), 0, 1)
    rgba = np.zeros((h, w, 4), np.uint8); rgba[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")

def spaced(draw, xy, text, f, fill, track, anchor="ls"):
    """letter-spaced small caps; anchor l or r on baseline."""
    widths = [draw.textlength(c, font=f) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x, y = xy
    if anchor == "rs": x -= total
    for c, wd in zip(text, widths):
        draw.text((x, y), c, font=f, fill=fill, anchor="ls"); x += wd + track
    return total

import re
_SUP = re.compile(r"(\^-?\d+)")
def rich(d, xy, text, f, fill, anchor="ls"):
    """draw text where '^-16' style tokens become superscripts. anchor: ls / rs / ms (baseline)."""
    if "^" not in text:
        d.text(xy, text, font=f, fill=fill, anchor=anchor); return
    small = ImageFont.truetype(f.path, max(8, int(f.size * 0.58)))
    parts = [(p[1:], small) if p.startswith("^") else (p, f) for p in _SUP.split(text) if p]
    widths = [d.textlength(p, font=ff) for p, ff in parts]; total = sum(widths) + sum(f.size * 0.12 for p, ff in parts if ff is small)
    x, y = xy
    if anchor[0] == "r": x -= total
    elif anchor[0] == "m": x -= total / 2
    for (p, ff), w in zip(parts, widths):
        dy = -int(f.size * 0.42) if ff is small else 0
        d.text((x, y + dy), p.replace("-", "\u2212") if ff is small else p, font=ff, fill=fill, anchor="ls"); x += w + (f.size * 0.12 if ff is small else 0)

def shadow_text(base, xy, text, f, fill, anchor, blur, alpha):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    rich(d, xy, text, f, (0, 0, 0, int(160 * alpha)), anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)
    rich(ImageDraw.Draw(base), xy, text, f, fill[:3] + (int(255 * alpha),), anchor)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))

def compose(img, t, TL):
    W, H = img.size; k = W / 1920.0
    base = img.convert("RGBA")
    base.alpha_composite(vignette(W, H))
    d = ImageDraw.Draw(base)
    st = TL.hud_state(t); HUD = TL.HUD
    white, dim, dimmer = (255, 255, 255, 235), (255, 255, 255, 180), (255, 255, 255, 150)
    L = int(80 * k)
    spaced(d, (L, int(92 * k)), HUD["label"], sans(int(15 * k)), white, 3.2 * k)
    shadow_text(base, (L - 4 * k, int(178 * k)), st["value"], serif(int(92 * k)), (255, 255, 255, 255), "ls", 10 * k, 1.0)
    d = ImageDraw.Draw(base)
    spaced(d, (L, int(214 * k)), st["sub"], sans(int(14 * k)), dim, 3.0 * k)
    dy = 0
    if "icon" in st:                       # comparison picture under the 'AS HEAVY AS ...' line
        dy = int(104 * k)
        if st["icon"] and st.get("icon_alpha", 1) > 0:
            ic = icon_img(st["icon"], int(84 * k)).copy()
            a = st.get("icon_alpha", 1.0)
            if a < 1: ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
            sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 140), (L, int(234 * k)), ic)
            base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8 * k)))
            base.alpha_composite(ic, (L, int(232 * k)))
            d = ImageDraw.Draw(base)
    d.rectangle([L, int(236 * k) + dy, L + int(34 * k), int(238 * k) + dy], fill=(255, 190, 90, 230))
    w = spaced(d, (L, int(270 * k) + dy), "NEXT", sans(int(13 * k)), dimmer, 3.0 * k)
    spaced(d, (L + w + 14 * k, int(270 * k) + dy), st["next_label"], sans(int(13 * k)), white, 3.0 * k)
    rich(d, (L, int(312 * k) + dy), st["next_value"], serif(int(34 * k)), white, "ls")
    R = W - int(80 * k)
    spaced(d, (R, int(92 * k)), HUD["right_label"], sans(int(15 * k)), white, 3.2 * k, anchor="rs")
    shadow_text(base, (R, int(178 * k)), st["right_value"], serif(int(92 * k)), (255, 255, 255, 255), "rs", 10 * k, 1.0)
    d = ImageDraw.Draw(base)
    spaced(d, (R, int(214 * k)), st.get("right_sub", HUD["right_sub"]), sans(int(14 * k)), dim, 3.0 * k, anchor="rs")
    if st.get("extra_label"):
        spaced(d, (R, int(270 * k)), st["extra_label"], sans(int(13 * k)), dimmer, 3.0 * k, anchor="rs")
        rich(d, (R, int(312 * k)), st["extra_value"], serif(int(34 * k)), white, "rs")
    for a, b, s in TL.CAPTIONS:
        if a <= t <= b:
            al = min(clamp((t - a) / .35), clamp((b - t) / .35))
            shadow_text(base, (W // 2, H - int(120 * k)), s, italic(int(58 * k)), (255, 255, 255, 255), "ms", 14 * k, al)
    fd = max(1 - t / .6, (t - (TL.DURATION - 0.7)) / .7)
    if fd > 0:
        base.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(fd)))))
    return base.convert("RGB")
