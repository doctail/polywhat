"""Original score + sound design for 'lighter'. Usage: python3 audio.py OUT.wav"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import timeline as TL
from sfx import *  # noqa

D = TL.DURATION; E = TL.EVENTS
mus, fx = Track(D), Track(D)

# ---------------- music: brighter, rising harmony; it opens up as you leave the ground
ACT_MUSIC = {  # chords (midi), seconds per chord, pad gain, pluck gain, pulse gain
    "house":        ([(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)], 4.0, 0.05, 0.08, 0.0),
    "street":       ([(60, 64, 67), (62, 65, 69), (57, 60, 64), (55, 59, 62)], 4.0, 0.05, 0.07, 0.03),
    "ascent":       ([(53, 60, 64, 67), (55, 62, 65, 69), (57, 64, 67, 72), (60, 64, 67, 71)], 6.0, 0.07, 0.05, 0.0),
    "sail":         ([(57, 64, 69), (53, 60, 65), (55, 62, 67), (52, 59, 64)], 4.0, 0.07, 0.05, 0.05),
    "interstellar": ([(50, 57, 62, 69), (48, 55, 64, 67), (46, 53, 62, 65), (45, 52, 60, 64)], 7.0, 0.08, 0.04, 0.03),
    "deep":         ([(45, 52, 57, 64), (46, 53, 58, 65), (48, 55, 60, 67), (50, 57, 62, 69)], 7.0, 0.09, 0.04, 0.02),
    "outro":        ([(48, 55, 64, 67), (41, 48, 57, 64)], 8.0, 0.07, 0.05, 0.0),
}
for name, a, b in TL.ACTS:
    chords, step, pg, kg, ug = ACT_MUSIC[name]
    t = a; i = 0
    while t < b:
        ch = chords[i % len(chords)]; d = min(step * 1.6, b - t + 2)
        mus.add(t, pad(ch, d, pg))
        mus.add(t, pad((ch[0] - 12,), d, pg * 0.7, cutoff=400))
        for k in range(int(step / 0.5)):
            if (k + i) % 2 == 0 or name in ("house", "street"):
                mus.add(t + k * 0.5, pluck(ch[(k + i) % len(ch)] + 12 + (12 if name in ("ascent", "deep") and k % 4 == 0 else 0), 2.5, kg))
        if ug:
            for k in range(int(step * 2)):
                mus.add(t + k * 0.5, thud(48, 0.3, ug, body=0.0))
        t += step; i += 1
mus.x[int(24.4 * SR): int(25.6 * SR)] *= 0.4
mus.x[int((E["sunpush"] - 0.5) * SR): int((E["sunpush"] + 3) * SR)] *= 0.5

# ---------------- sound design
for td in (3.9, 13.3): fx.add(td, thud(70, 0.4, 0.15))
fx.add(23.7, whoosh(0.6, 0.25, 300, 1800)); fx.add(24.55, thud(60, 0.7, 0.7)); fx.add(24.57, crack(0.15, 0.25, 6, 1500, 5000))
fx.add(27.2, thud(55, 0.5, 0.35))
fx.add(31.4, whoosh(2.0, 0.3, 200, 1500)); fx.add(33.7, thud(52, 0.8, 0.55))
fx.add(35.2, creak(1.6, 0.18, 14, 40, (300, 1100)))
for k in range(8): fx.add(37.8 + k * 0.62, thud(64, 0.3, 0.12))
# street: soft bouncy steps, then wind that grows into a gale
for k in range(5): fx.add(42.6 + k * 2.2, thud(62, 0.35, 0.18))
sa, sb = TL.ACTS[1][1], TL.ACTS[1][2]
env = np.clip((np.arange(int((sb - sa) * SR)) / SR - 9.5) / 3.0, 0.05, 1.0)
wind = bp(noise(sb - sa), 250, 1800) * 0.11 * env * (0.75 + 0.25 * np.sin(np.arange(int((sb - sa) * SR)) / SR * 0.9))
fx.add(sa, wind)
fx.add(E["gust"], whoosh(3.0, 0.35, 150, 1200)); fx.add(E["blown"], whoosh(4.0, 0.4, 120, 900))
fx.add(E["grab"], clang(1.5, 0.25, 240)); fx.add(E["grab"], thud(58, 0.5, 0.4))
for k in range(6): fx.add(80 + k * 7, whoosh(3.5, 0.2, 200, 1200))
fx.add(E["lift"], whoosh(5.0, 0.3, 100, 600))
# ascent: wind thins out with altitude; jet; meteors; the Sun
aa, ab = TL.ACTS[2][1], TL.ACTS[2][2]
fx.add(aa, bp(noise(ab - aa), 200, 1200) * 0.08 * np.linspace(1.0, 0.0, int((ab - aa) * SR)) ** 2)
fx.add(E["jet"] - 2, whoosh(9.0, 0.22, 80, 500))
for k in range(12): fx.add(E["meteors"] + k * 0.6, whoosh(0.8, 0.12, 900, 4000))
fx.add(E["sunpush"], boom(6.0, 0.45, 50))
# sail: rushing grows; a whoosh for each world you pass
pa, pb = TL.ACTS[3][1], TL.ACTS[3][2]
fx.add(pa, rumble(pb - pa, 0.12, 90) * np.linspace(0.1, 1.0, int((pb - pa) * SR)))
fx.add(E["leave_atm"], whoosh(4.0, 0.3, 100, 800))
fx.add(248.5, whoosh(2.5, 0.25, 150, 1500))
for ev in ("mars", "jupiter", "saturn", "neptune"):
    fx.add(E[ev] - 0.4, whoosh(3.2, 0.42, 60, 900)); fx.add(E[ev] + 1.2, boom(3.0, 0.3, 40))
# interstellar + deep: high shimmering drone that climbs
ia, ib = TL.ACTS[4][1], TL.ACTS[5][2]
n = int((ib - ia) * SR); tt = np.arange(n) / SR
f0 = 220 * 2 ** (tt / (ib - ia) * 1.0)
drone = (np.sin(2 * np.pi * np.cumsum(f0) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f0 * 1.5) / SR)) * 0.02 * np.clip(tt / 6, 0, 1)
fx.add(ia, drone)
fx.add(E["voyager"] + 0.2, whoosh(2.0, 0.4, 200, 2500))
for k in range(7): fx.add(380 + k * 2.3 + 0.8, whoosh(1.0, 0.25, 300, 2000))
fx.add(E["blueshift"], boom(5.0, 0.25, 60))
fx.add(E["proxima"], whoosh(3.0, 0.45, 80, 1200)); fx.add(E["proxima"] + 0.6, boom(4.0, 0.4, 36))
fx.add(E["galaxy_exit"], boom(6.0, 0.5, 34)); fx.add(E["galaxy_view"], boom(7.0, 0.45, 30))

mix = mus.x * 1.4 + fx.x * 0.65
mix = np.tanh(mix * 2.0) / 2.0
out = sys.argv[1] if len(sys.argv) > 1 else "audio.wav"
write_wav(out, mix, D)
print("audio ok", out)
