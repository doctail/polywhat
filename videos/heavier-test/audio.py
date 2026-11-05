"""Original music + SFX (numpy synthesis, no samples, no licences). Usage: python3 audio.py OUT.wav"""
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as TL
SR = 48000; D = TL.DURATION; N = int(SR * D); t = np.arange(N) / SR
rng = np.random.default_rng(3)
def note(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, k):  # cheap low-pass: moving average whose width follows k
    n = max(1, int(1 / k)); return np.convolve(x, np.ones(n) / n, mode="same")

mus = np.zeros(N)
# slow minimal piano-like pulses (sine + decay), minor progression
prog = [(57, 64, 69), (53, 60, 65), (55, 62, 67), (52, 59, 64)]
beat = 0.75
for i in range(int(D / beat)):
    ch = prog[(i // 8) % 4]; m = ch[i % 3] + (12 if i % 4 == 3 else 0)
    a = int(i * beat * SR); L = int(2.5 * SR); b = min(N, a + L); tt = np.arange(b - a) / SR
    env = np.exp(-tt * 2.2) * (1 - np.exp(-tt * 200))
    f = note(m)
    mus[a:b] += 0.07 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) + 0.1 * np.sin(6 * np.pi * f * tt))
# pad
for i in range(int(D / 6) + 1):
    ch = prog[i % 4]; a = int(i * 6 * SR); b = min(N, a + int(8 * SR)); tt = np.arange(b - a) / SR
    env = np.clip(tt / 2.5, 0, 1) * np.clip((8 - tt) / 2.5, 0, 1)
    for m in ch: mus[a:b] += 0.025 * env * np.sin(2 * np.pi * note(m - 12) * tt)
# rising tension after 17 s
ten = np.clip((t - 17) / 7, 0, 1) * (t < 24)
mus += 0.05 * ten * np.sin(2 * np.pi * 55 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 6 * t))
mus[t > TL.EVENTS['floor_break']] *= 0.15  # music drops out on the fall

sfx = np.zeros(N)
def mixs(*xs):
    L = max(len(x) for x in xs); o = np.zeros(L)
    for x in xs: o[:len(x)] += x
    return o
def add(at, sig):
    a = int(at * SR); b = min(N, a + len(sig)); sfx[a:b] += sig[:b - a]
def thud(f=48, d=0.7, amp=0.5):
    tt = np.arange(int(d * SR)) / SR
    return amp * np.exp(-tt * 7) * np.sin(2 * np.pi * f * tt * (1 - 0.3 * tt))
def noise(d, k, amp, decay):
    tt = np.arange(int(d * SR)) / SR
    return amp * lp(rng.standard_normal(len(tt)), k) * np.exp(-tt * decay)
def creak(d=1.0, f0=180, amp=0.15):
    tt = np.arange(int(d * SR)) / SR
    f = f0 + 40 * np.sin(2 * np.pi * 1.3 * tt)
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    return amp * saw * np.sin(np.pi * tt / d) ** 2 * (0.5 + 0.5 * (rng.random(len(tt)) > 0.6))
for at in (3.0, 6.3, 14.0, 21.3): add(at, thud())
add(17.2, creak(1.2, 160)); add(20.0, creak(1.0, 140, 0.12)); add(22.4, creak(1.4, 110, 0.18))
add(TL.EVENTS['bed_break'], mixs(noise(0.6, 0.35, 0.6, 9), thud(60, 0.5, 0.6)))           # bed snaps
add(21.4, noise(0.3, 0.5, 0.25, 12)); add(23.0, noise(0.3, 0.5, 0.3, 12))  # cracks
add(TL.EVENTS['floor_break'], mixs(noise(1.0, 0.25, 0.7, 3), thud(40, 1.0, 0.7)))            # floor breaks
wind = noise(0.95, 0.06, 0.5, 0.5); add(24.0, wind * np.linspace(0.3, 1, len(wind)))
add(TL.EVENTS['land'], mixs(thud(35, 1.6, 1.0), noise(1.5, 0.12, 0.8, 2.5)))          # landing
add(25.1, noise(3.5, 0.03, 0.25, 0.8))                              # debris settle
mix = mus + sfx
mix /= np.max(np.abs(mix)) / 0.95
fade = np.clip((D - t) / 0.7, 0, 1) * np.clip(t / 0.5, 0, 1)
out = sys.argv[1] if len(sys.argv) > 1 else "audio.wav"
pcm = (np.clip(mix * fade, -1, 1) * 32767).astype("<i2")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm[:, None], 2, 1).tobytes())
print("audio ok", out)
