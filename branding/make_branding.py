"""Channel icon (800x800) and banner (2560x1440) for 'No Off Switch'. Pure PIL, drawn at 2x then downscaled."""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
NAME = "No Off Switch"

def lerp(a, b, t): return a + (b - a) * t
def lc(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def vgrad(w, h, stops):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / (h - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1: d.line([(0, y), (w, y)], fill=lc(c0, c1, (t - t0) / (t1 - t0))); break
    return im

def glow(im, x, y, r, color, alpha):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for i in range(40, 0, -1):
        rr = r * i / 40; a = int(alpha * (1 - i / 40) ** 2 * 255)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color + (a,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.08)))

def spaced(d, x, y, text, f, fill, track, center=True):
    ws = [d.textlength(c, font=f) for c in text]; tot = sum(ws) + track * (len(text) - 1)
    if center: x -= tot / 2
    for c, w in zip(text, ws): d.text((x, y), c, font=f, fill=fill, anchor="ls"); x += w + track

def lowpoly_land(d, w, horizon, h, seed, base, var, rows=7, cols=18):
    """faceted ground between horizon and bottom, perspective-ish rows."""
    rnd = random.Random(seed)
    ys = [horizon + (h - horizon) * ((i / rows) ** 1.8) for i in range(rows + 1)]
    pts = [[(w * j / cols + (rnd.uniform(-.35, .35) * w / cols if 0 < j < cols else 0), y + (rnd.uniform(-.2, .2) * (ys[1] - ys[0]) if 0 < i < rows else 0))
            for j in range(cols + 1)] for i, y in enumerate(ys)]
    for i in range(rows):
        for j in range(cols):
            a, b, c, e = pts[i][j], pts[i][j + 1], pts[i + 1][j + 1], pts[i + 1][j]
            for tri in ((a, b, c), (a, c, e)):
                k = rnd.uniform(-var, var) + i * 0.02
                d.polygon(tri, fill=tuple(max(0, min(255, int(ch * (1 + k)))) for ch in base))

def mountains(d, w, horizon, seed, color, height, n=9):
    rnd = random.Random(seed); xs = [w * i / n for i in range(n + 1)]
    for i in range(n):
        x0, x1 = xs[i] - w / n * .4, xs[i + 1] + w / n * .4; px = rnd.uniform(x0 + (x1 - x0) * .3, x1 - (x1 - x0) * .3)
        ph = horizon - rnd.uniform(.4, 1) * height
        d.polygon([(x0, horizon), (px, ph), (x1, horizon)], fill=color)
        d.polygon([(px, ph), (x1, horizon), (px + (x1 - px) * .2, horizon)], fill=tuple(int(c * .85) for c in color))

# ------------------------------------------------------------------ banner
def banner():
    S = 2; W, H = 2560 * S, 1440 * S
    im = vgrad(W, H, [(0, (28, 44, 82)), (0.38, (110, 120, 170)), (0.5, (246, 176, 120)), (0.56, (250, 214, 160)), (1, (60, 50, 50))]).convert("RGBA")
    horizon = int(H * 0.56)
    glow(im, W // 2, horizon - 20 * S, 520 * S, (255, 214, 150), 0.9)
    d = ImageDraw.Draw(im)
    mountains(d, W, horizon, 3, (126, 112, 150), 260 * S, 11)
    mountains(d, W, horizon, 9, (92, 84, 120), 150 * S, 15)
    lowpoly_land(d, W, horizon, H, 5, (98, 134, 72), 0.12)
    # road to the vanishing point (first-person)
    vx = W // 2
    d.polygon([(vx - 6 * S, horizon), (vx + 6 * S, horizon), (vx + 900 * S, H), (vx - 900 * S, H)], fill=(58, 58, 64))
    for i in range(14):
        t0, t1 = (i / 14) ** 2.2, ((i + .45) / 14) ** 2.2
        y0, y1 = lerp(horizon, H, t0), lerp(horizon, H, t1); w0, w1 = lerp(1, 18, t0) * S, lerp(1, 18, t1) * S
        d.polygon([(vx - w0, y0), (vx + w0, y0), (vx + w1, y1), (vx - w1, y1)], fill=(236, 196, 90))
    # streaks (speed)
    rnd = random.Random(4)
    for _ in range(70):
        a = rnd.uniform(0, math.tau); r0 = rnd.uniform(300, 900) * S; L = rnd.uniform(80, 260) * S
        x0, y0 = vx + math.cos(a) * r0, horizon + math.sin(a) * r0 * .55
        d.line([(x0, y0), (x0 + math.cos(a) * L, y0 + math.sin(a) * L * .55)], fill=(255, 245, 225, 70), width=2 * S)
    im = im.resize((2560, 1440), Image.LANCZOS)
    # darken safe area for legibility
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([507 - 40, 508 - 10, 2053 + 40, 932 + 10], 60, fill=(10, 14, 28, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im)
    title = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Medium.ttf"), 190)
    sub = ImageFont.truetype(os.path.join(FONTS, "Inter-SemiBold.ttf"), 34)
    it = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Italic.ttf"), 56)
    tl = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
    td.text((1280, 772), NAME, font=title, fill=(0, 0, 0, 170), anchor="ms"); im.alpha_composite(tl.filter(ImageFilter.GaussianBlur(14)))
    d.text((1280, 772), NAME, font=title, fill=(255, 255, 255), anchor="ms")
    spaced(d, 1280, 588, "FIRST-PERSON  WHAT IF  VIDEOS", sub, (255, 228, 190), 7)
    d.text((1280, 872), "It starts small. It never stops.", font=it, fill=(255, 255, 255, 235), anchor="ms")
    im.convert("RGB").save(os.path.join(HERE, "banner_2560x1440.png"))

# ------------------------------------------------------------------ icon
def icon():
    S = 2; N = 800 * S
    im = vgrad(N, N, [(0, (24, 34, 66)), (1, (8, 10, 22))]).convert("RGBA")
    d = ImageDraw.Draw(im); rnd = random.Random(2)
    # low-poly facets
    g = 6; pts = [[(N * j / g + (rnd.uniform(-.3, .3) * N / g if 0 < j < g else 0), N * i / g + (rnd.uniform(-.3, .3) * N / g if 0 < i < g else 0)) for j in range(g + 1)] for i in range(g + 1)]
    for i in range(g):
        for j in range(g):
            a, b, c, e = pts[i][j], pts[i][j + 1], pts[i + 1][j + 1], pts[i + 1][j]
            for tri in ((a, b, c), (a, c, e)):
                k = rnd.uniform(0, 1); d.polygon(tri, fill=lc((22, 32, 64), (40, 52, 96), k))
    cx = cy = N // 2
    glow(im, cx, cy, 300 * S, (255, 150, 60), 0.75)
    d = ImageDraw.Draw(im)
    R, wdt = 205 * S, 46 * S
    # power ring with gap at top
    d.arc([cx - R, cy - R, cx + R, cy + R], start=-55, end=235, fill=(255, 255, 255), width=wdt)
    for ang in (-55, 235):  # round caps
        a = math.radians(ang); px, py = cx + math.cos(a) * (R - wdt / 2), cy + math.sin(a) * (R - wdt / 2)
        d.ellipse([px - wdt / 2, py - wdt / 2, px + wdt / 2, py + wdt / 2], fill=(255, 255, 255))
    # the 'switch' is an arrow that keeps going up
    col = (255, 168, 72)
    d.rounded_rectangle([cx - wdt / 2, cy - 250 * S, cx + wdt / 2, cy + 20 * S], wdt // 2, fill=col)
    d.polygon([(cx, cy - 330 * S), (cx - 70 * S, cy - 225 * S), (cx + 70 * S, cy - 225 * S)], fill=col)
    im = im.resize((800, 800), Image.LANCZOS)
    im.convert("RGB").save(os.path.join(HERE, "icon_800.png"))
    # preview as YouTube shows it (circle, small)
    m = Image.new("L", (800, 800), 0); ImageDraw.Draw(m).ellipse([0, 0, 799, 799], fill=255)
    prev = Image.new("RGB", (800, 800), (255, 255, 255)); prev.paste(im.convert("RGB"), (0, 0), m)
    prev.resize((98, 98), Image.LANCZOS).save(os.path.join(HERE, "icon_preview_98.png"))

if __name__ == "__main__":
    banner(); icon(); print("ok")
