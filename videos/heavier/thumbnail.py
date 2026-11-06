"""Thumbnail: sunset street POV (scene.py --act surface --thumb 1 --times 300) + asphalt cracks + headline.
Usage: python3 thumbnail.py SRC.png OUT.jpg"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from thumbgrade import grade
from PIL import Image, ImageDraw, ImageFilter, ImageFont
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fonts")
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA").resize((1280, 720))
W, H = im.size
im = grade(im, light=(645, 330), glow_color=(255, 200, 150))
# cracks spreading on the asphalt from under you (bottom centre) toward the horizon
rnd = random.Random(4); cr = Image.new("RGBA", im.size, (0, 0, 0, 0)); cd = ImageDraw.Draw(cr)
for i in range(9):
    x, y = W / 2 + rnd.uniform(-140, 140), H + 10; a = math.radians(rnd.uniform(-160, -20)); w = 7
    for k in range(9):
        a += rnd.uniform(-0.45, 0.45); L = rnd.uniform(30, 70) * (1 - k * 0.07)
        nx, ny = x + math.cos(a) * L, y + math.sin(a) * L * 0.55
        if ny < 455: break
        cd.line([(x, y + 3), (nx, ny + 3)], fill=(255, 190, 130, 150), width=max(1, int(w * 0.6))); cd.line([(x, y), (nx, ny)], fill=(10, 6, 14, 245), width=max(1, int(w))); x, y = nx, ny; w *= 0.8
im.alpha_composite(cr)
# soft dark gradient on the left for legibility
sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([0, 0, 640, 430], fill=(15, 10, 30, 120))
im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(80)))
d = ImageDraw.Draw(im)
sans = ImageFont.truetype(os.path.join(FONTS, "Inter-SemiBold.ttf"), 19)
small = ImageFont.truetype(os.path.join(FONTS, "Inter-SemiBold.ttf"), 15)
serif = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Medium.ttf"), 104)
ital = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Italic.ttf"), 38)
def spaced(x, y, text, f, fill, track):
    for c in text: d.text((x, y), c, font=f, fill=fill, anchor="ls"); x += d.textlength(c, font=f) + track
def shadow(xy, text, f, fill, blur=9):
    l = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(l).text(xy, text, font=f, fill=(0, 0, 0, 170), anchor="ls")
    im.alpha_composite(l.filter(ImageFilter.GaussianBlur(blur))); ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor="ls")
spaced(58, 96, "YOUR MASS", sans, (255, 255, 255, 240), 4)
shadow((52, 196), "1.8 Earths", serif, (255, 255, 255, 255))
d = ImageDraw.Draw(im)
spaced(58, 236, "AND STILL DOUBLING", small, (255, 225, 190, 235), 4)
shadow((58, 296), "You can't stop it.", ital, (255, 255, 255, 240), 7)
im.convert("RGB").save(out, quality=95)
print("ok", out)
