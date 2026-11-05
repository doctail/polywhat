"""Original score + sound design for 'heavier'. Usage: python3 audio.py OUT.wav"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import timeline as TL
from sfx import *  # noqa

D = TL.DURATION; E = TL.EVENTS
mus, fx = Track(D), Track(D)

# ---------------- music: chord progression per act, intensity rising
ACT_MUSIC = {  # chords (midi), seconds per chord, pad gain, pluck gain, pulse gain
    "house":   ([(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)], 4.5, 0.05, 0.07, 0.0),
    "shaft":   ([(45, 52, 57), (43, 50, 55), (41, 48, 53), (40, 47, 52)], 6.0, 0.06, 0.05, 0.03),
    "cavity":  ([(45, 52, 56), (44, 51, 56), (45, 52, 57), (41, 48, 53)], 6.0, 0.06, 0.04, 0.02),
    "plunge":  ([(45, 52, 57), (46, 53, 58), (48, 55, 60), (50, 57, 62)], 4.0, 0.08, 0.04, 0.07),
    "surface": ([(50, 57, 62), (48, 55, 60), (46, 53, 58), (45, 52, 57)], 5.0, 0.06, 0.05, 0.05),
    "space":   ([(48, 55, 64), (45, 52, 60), (41, 48, 57), (43, 50, 59)], 8.0, 0.08, 0.04, 0.0),
    "galaxy":  ([(48, 55, 64, 67), (45, 52, 60, 64), (41, 48, 57, 60), (43, 50, 59, 62)], 6.0, 0.09, 0.05, 0.03),
    "outro":   ([(48, 55, 64), (41, 48, 57)], 8.0, 0.06, 0.05, 0.0),
}
for name, a, b in TL.ACTS:
    chords, step, pg, kg, ug = ACT_MUSIC[name]
    t = a; i = 0
    while t < b:
        ch = chords[i % len(chords)]; d = min(step * 1.6, b - t + 2)
        mus.add(t, pad(ch, d, pg))
        mus.add(t, pad((ch[0] - 12,), d, pg * 0.8, cutoff=400))
        for k in range(int(step / 0.75)):
            if (k + i) % 3 == 0 or name in ("house", "outro"):
                mus.add(t + k * 0.75, pluck(ch[(k + i) % len(ch)] + 12, 2.5, kg))
        if ug:
            for k in range(int(step * 2)):
                mus.add(t + k * 0.5, thud(41 if name != "plunge" else 46, 0.4, ug, body=0.0))
        t += step; i += 1
# music ducks for big moments
mus.x[int(E["floor_break"] * SR): int((E["land"] + 0.6) * SR)] *= 0.4
mus.x[int((E["core"]) * SR): int((E["core"] + 3) * SR)] *= 0.3
mus.x[int((E["bh"] - 0.5) * SR): int((E["bh"] + 4) * SR)] *= 0.25

# ---------------- sound design
for td in (3.3, 6.3, 13.2, 21.0, 28.2, 35.0): fx.add(td, thud(52, 0.8, 0.45))
fx.add(E["look_bed"] - 0.2, creak(1.6, 0.22)); fx.add(E["bed_break"] - 0.9, creak(0.8, 0.25, 30, 70))
fx.add(E["bed_break"], crack(0.4, 0.7, 18, 900, 4000)); fx.add(E["bed_break"] + 0.02, thud(70, 0.6, 0.6)); fx.add(E["bed_break"] + 0.1, debris(1.0, 0.25, 15))
for k in range(6): fx.add(E["cracks"] + k * 0.75, crack(0.25, 0.3, 8, 1200, 5000))
fx.add(E["cracks"] + 1.0, creak(3.0, 0.2, 12, 30, (200, 900)))
fx.add(E["floor_break"], crack(0.5, 0.8, 24, 800, 4000)); fx.add(E["floor_break"], whoosh(0.9, 0.35, 200, 1500))
fx.add(E["floor_break"] + 0.05, debris(2.2, 0.35, 50))
fx.add(E["land"], thud(40, 1.4, 1.0)); fx.add(E["land"], debris(1.8, 0.4, 40)); fx.add(E["land"], rumble(1.5, 0.3) * np.exp(-secs(1.5) * 2))
for k in range(5): fx.add(E["cracks2"] + k * 0.5, crack(0.25, 0.35, 8, 1000, 4500))
fx.add(E["floor2_break"], crack(0.5, 0.8, 24, 700, 3500)); fx.add(E["floor2_break"] + 0.05, debris(2.0, 0.35, 45))
fx.add(E["land2"], thud(36, 1.6, 1.0)); fx.add(E["land2"], debris(1.6, 0.35, 30))
# shaft: grinding rumble that grows with depth
L = TL.ACTS[1][2] - TL.ACTS[1][1]
r = rumble(L, 0.22, 110) * np.linspace(0.4, 1.3, int(L * SR)); fx.add(TL.ACTS[1][1], r)
for k in range(28): fx.add(TL.ACTS[1][1] + 2 + k * 2.9 + rng.uniform(0, 1), crack(0.3, 0.12, 6, 600, 2500))
fx.add(E["pipes"], clang(2.5, 0.25, 160)); fx.add(E["pipes"] + 1.7, clang(2.0, 0.18, 210))
fx.add(E["concrete"], crack(0.6, 0.6, 30, 400, 2500)); fx.add(E["concrete"], debris(2.0, 0.3, 40))
fx.add(E["granite"], crack(0.6, 0.6, 30, 300, 2000)); fx.add(E["granite"], thud(34, 1.4, 0.7))
fx.add(E["close"], thud(30, 2.0, 0.6)); fx.add(E["close"] - 0.5, whoosh(2.5, 0.2, 120, 600))
# cavity: pebbles then rocks hitting you
for k in range(70):
    tko = TL.EVENTS_OLD["pebbles"] - 14 + (k / 70) ** 0.7 * 38; big = tko > TL.EVENTS_OLD["pebbles"]; tk = TL.n(tko)
    fx.add(tk, crack(0.12, 0.08 + (0.14 if big else 0), 4, 800 if big else 2000, 4000 if big else 7000))
    if big and k % 3 == 0: fx.add(tk, thud(60, 0.4, 0.25))
fx.add(E["planet"], boom(3.5, 0.5, 38))
# plunge: wind + roar
pa, pb = TL.ACTS[3][1], TL.ACTS[3][2]
roar = rumble(pb - pa, 0.25, 160) * np.concatenate([np.linspace(0.3, 1.2, int((E["core"] - pa) * SR)), np.linspace(1.2, 0.1, int((pb - E["core"]) * SR) + 2)])[: int((pb - pa) * SR)]
fx.add(pa, roar)
for k in range(8): fx.add(pa + 2 + k * 7, whoosh(3.0, 0.18, 200, 2000))
fx.add(E["core"], boom(4.0, 0.7, 30))
# surface: wind, stress, failures
sa, sb = TL.ACTS[4][1], TL.ACTS[4][2]
fx.add(sa, bp(noise(sb - sa), 200, 900) * 0.05 * np.linspace(0.5, 1.5, int((sb - sa) * SR)))
fx.add(E["plane"], whoosh(9.0, 0.25, 80, 500))
for k in range(10): fx.add(TL.n(276 + k * 5), creak(2.0, 0.15, 10, 25, (150, 600)))
fx.add(TL.n(285.0), crack(0.8, 0.6, 30, 500, 3000)); fx.add(TL.n(285.4), thud(45, 1.5, 0.6)); fx.add(TL.n(285.5), debris(2.5, 0.3, 50))
fx.add(TL.n(298.0), debris(3.0, 0.35, 70)); fx.add(TL.n(298.0), thud(50, 1.0, 0.5))
fx.add(E["crush"], rumble(5.0, 0.6, 80) * np.linspace(0.2, 1.0, 5 * SR))
# space: quiet; big moments only
fx.add(E["bh"] - 0.6, whoosh(1.2, 0.3, 100, 800)); fx.add(E["bh"], boom(6.0, 0.9, 28))
fx.add(E["swallow"], rumble(6.0, 0.25, 60) * np.sin(np.linspace(0, np.pi, 6 * SR)))
fx.add(E["sun"], boom(5.0, 0.4, 44))
# galaxy: low swells
fx.add(E["sgr"], boom(6.0, 0.35, 36)); fx.add(E["outweigh"], boom(6.0, 0.6, 30))

mix = mus.x * 1.4 + fx.x * 0.65
mix = np.tanh(mix * 2.0) / 2.0   # soft limiter: tames transients so music stays audible
out = sys.argv[1] if len(sys.argv) > 1 else "audio.wav"
write_wav(out, mix, D)
print("audio ok", out)
