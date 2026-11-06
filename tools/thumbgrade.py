"""Shared 'glossy' grade for thumbnails: deep blacks, S-curve contrast, saturation, a blown-out light source
with bloom + glare, vignette and a light sharpen. Turns a flat low-poly render into a punchy, lit-looking frame.
grade(im, light=(x, y) or None, glow_color=(r, g, b)) -> RGBA image"""
import numpy as np
from PIL import Image, ImageFilter


def grade(im, light=None, glow_color=(255, 214, 160), strength=1.0):
    im = im.convert("RGB"); W, H = im.size
    a = np.asarray(im).astype(np.float32) / 255.0
    # 1. crush blacks a bit + filmic S-curve
    a = np.clip((a - 0.04) / 0.96, 0, 1)
    a = a * a * (3 - 2 * a) * 0.55 + a * 0.45
    # 2. saturation (luma-preserving)
    l = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    a = np.clip(l + (a - l) * (1 + 0.25 * strength), 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8))
    # 3. bloom from highlights
    hi = np.clip((a - 0.72) / 0.28, 0, 1) ** 1.5
    hl = Image.fromarray((hi * 255).astype(np.uint8))
    bloom = np.zeros_like(a)
    for r, w in ((8, 0.6), (30, 0.6), (90, 0.5)):
        bloom += np.asarray(hl.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0 * w
    a = np.asarray(out).astype(np.float32) / 255.0
    a = 1 - (1 - a) * (1 - np.clip(bloom * 0.8 * strength, 0, 1))      # screen blend
    # 4. glare from the light source: hot core + wide warm halo
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    if light:
        d = np.hypot(xx - light[0], (yy - light[1]) * 1.15) / W
        gc = np.array(glow_color, np.float32) / 255.0
        halo = (np.exp(-(d / 0.035) ** 2) * 1.0 + np.exp(-(d / 0.12) ** 2) * 0.45 + np.exp(-(d / 0.35) ** 2) * 0.22) * strength
        a = 1 - (1 - a) * (1 - np.clip(halo[..., None] * gc, 0, 1))
        streak = np.exp(-((yy - light[1]) / 3.5) ** 2) * np.exp(-np.abs(xx - light[0]) / (W * 0.18)) * 0.55 * strength
        a = 1 - (1 - a) * (1 - np.clip(streak[..., None] * gc, 0, 1))
    # 5. vignette
    v = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    a *= (1 - 0.42 * np.clip(v - 0.45, 0, 1) ** 1.6)[..., None]
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2)).convert("RGBA")
