"""Thumbnail: edge of space POV (scene.py --act ascent --times 207.5 at 1280x720) + glossy grade + headline.
Usage: python3 thumbnail.py SRC.png OUT.jpg"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from thumbgrade import grade
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fonts")
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA").resize((1280, 720))
im = grade(im, light=(842, 246), glow_color=(255, 225, 180), strength=1.2)
sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([0, 0, 620, 420], fill=(5, 8, 20, 110))
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
shadow((52, 196), "0.5 mg", serif, (255, 255, 255, 255))
d = ImageDraw.Draw(im)
spaced(58, 236, "AND STILL HALVING", small, (190, 215, 255, 235), 4)
shadow((58, 296), "You can't come down.", ital, (255, 255, 255, 240), 7)
im.convert("RGB").save(out, quality=95)
print("ok", out)
