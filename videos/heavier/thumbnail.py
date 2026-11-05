"""Thumbnail: POV on the scale (frame t=7 s rendered at 1280x720) + 'Err' on the display + headline.
Usage: python3 thumbnail.py SRC.png OUT.png"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fonts")
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA").resize((1280, 720))
d = ImageDraw.Draw(im)
# repaint the scale display (591-687 x 461-494) with a 7-segment 'Err'
x0, y0, x1, y1 = 591, 461, 687, 494
d.rectangle([x0, y0, x1, y1], fill=(16, 22, 28, 255))
SEG = {"E": "adefg", "r": "eg"}
def seg7(ch, x, y, w, h, t, col):
    on = SEG[ch]; hw = h / 2
    R = {"a": (x, y, x + w, y + t), "g": (x, y + hw - t / 2, x + w, y + hw + t / 2), "d": (x, y + h - t, x + w, y + h),
         "f": (x, y, x + t, y + hw), "b": (x + w - t, y, x + w, y + hw), "e": (x, y + hw, x + t, y + h), "c": (x + w - t, y + hw, x + w, y + h)}
    for s in on: d.rectangle(R[s], fill=col)
for i, ch in enumerate("Err"):
    seg7(ch, x0 + 22 + i * 24, y0 + 6, 15, 22, 3, (255, 90, 70, 255))
# glow on the display
g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rectangle([x0 + 15, y0 + 4, x1 - 10, y1 - 4], fill=(255, 80, 60, 90))
im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
# darken top-left for the text
sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([0, 0, 820, 470], fill=(10, 14, 24, 150))
im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(90)))
d = ImageDraw.Draw(im)
sans = ImageFont.truetype(os.path.join(FONTS, "Inter-SemiBold.ttf"), 22)
serif = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Medium.ttf"), 128)
ital = ImageFont.truetype(os.path.join(FONTS, "EBGaramond-Italic.ttf"), 46)
def spaced(x, y, text, f, fill, track):
    for c in text: d.text((x, y), c, font=f, fill=fill, anchor="ls"); x += d.textlength(c, font=f) + track
def shadow(xy, text, f, fill, blur=10):
    l = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(l).text(xy, text, font=f, fill=(0, 0, 0, 200), anchor="ls")
    im.alpha_composite(l.filter(ImageFilter.GaussianBlur(blur))); ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor="ls")
spaced(70, 110, "YOUR MASS", sans, (255, 255, 255, 235), 5)
shadow((62, 228), "5.8 million", serif, (255, 255, 255, 255))
shadow((62, 340), "Suns", serif, (255, 255, 255, 255))
d = ImageDraw.Draw(im)
d.rectangle([70, 372, 120, 375], fill=(255, 170, 70, 255))
spaced(70, 412, "AND STILL DOUBLING", sans, (255, 220, 180, 235), 5)
shadow((70, 470), "It started at 70 kg.", ital, (255, 255, 255, 240), 8)
im.convert("RGB").save(out, quality=95)
print("ok", out)
