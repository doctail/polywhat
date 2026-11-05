"""Small synthesis toolkit for original music and sound effects (numpy + scipy, no samples)."""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)

def secs(d): return np.arange(int(round(d * SR))) / SR
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)
def lp(x, f, order=2): return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)
def noise(d): return rng.standard_normal(int(round(d * SR)))
def env_ad(n, a, d):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(d, 1e-4))

def thud(f0=55, d=0.8, amp=0.7, body=0.3):
    t = secs(d); f = f0 * (1 + 0.6 * np.exp(-t * 18))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    s += body * lp(noise(d), 180) * np.exp(-t * 14)
    return amp * s

def crack(d=0.35, amp=0.5, n=14, lo=1500, hi=6000):
    out = np.zeros(int(round(d * SR))); times = np.sort(rng.uniform(0, d * 0.7, n))
    for i, tc in enumerate(times):
        L = int(0.006 * SR); a = int(tc * SR)
        click = bp(rng.standard_normal(L), lo, hi) * np.exp(-np.arange(L) / (0.0015 * SR))
        out[a:a + L] += click[: len(out) - a] * (1 - i / n * 0.6)
    knock = bp(noise(d), 250, 900) * env_ad(len(out), 0.002, 0.04)
    return amp * (out * 0.7 + knock * 0.8)

def creak(d=1.2, amp=0.25, f_lo=18, f_hi=55, band=(350, 1400)):
    """stick-slip friction: impulse train with wandering rate through a resonant band."""
    t = secs(d); rate = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.3, 0.8) * t + rng.uniform(0, 6)))
    ph = np.cumsum(rate) / SR; imp = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    imp *= rng.uniform(0.5, 1.0, len(imp))
    s = bp(imp, *band, order=3) + 0.3 * bp(noise(d), band[0], band[1]) * 0.05
    return amp * s * np.sin(np.pi * t / d) ** 1.5 / (np.max(np.abs(s)) + 1e-9)

def debris(d=1.6, amp=0.3, n=40):
    out = np.zeros(int(round(d * SR)))
    for _ in range(n):
        a = int(rng.uniform(0, d * 0.85) * SR); L = int(rng.uniform(0.01, 0.05) * SR)
        if a + L > len(out): continue
        f = rng.uniform(300, 2500)
        g = bp(rng.standard_normal(L), f * 0.7, f * 1.4) * np.exp(-np.arange(L) / (0.008 * SR)) * rng.uniform(0.3, 1)
        out[a:a + L] += g
    return amp * out * np.exp(-secs(d) * 1.2)

def rumble(d, amp=0.3, f=90):
    return amp * lp(noise(d), f, order=4) * 4

def whoosh(d=1.2, amp=0.35, f0=300, f1=2400):
    t = secs(d); out = np.zeros_like(t); x = noise(d); steps = 12
    for i in range(steps):
        a, b = int(i * len(t) / steps), int((i + 1) * len(t) / steps)
        fc = f0 * (f1 / f0) ** (i / steps); out[a:b] = bp(x, fc * 0.6, fc * 1.6)[a:b]
    return amp * out * np.sin(np.pi * t / d) ** 2

def clang(d=2.5, amp=0.25, f=180):
    t = secs(d); s = np.zeros_like(t)
    for k, (r, dec) in enumerate(((1.0, 1.2), (2.76, 0.9), (5.4, 0.6), (8.93, 0.4))):
        s += np.sin(2 * np.pi * f * r * t + k) * np.exp(-t / dec) / (k + 1)
    return amp * s * np.minimum(1, t / 0.002)

def boom(d=4.0, amp=0.8, f=32):
    t = secs(d); swell = np.minimum(1, t / 0.4) * np.exp(-np.maximum(0, t - 0.4) * 1.1)
    return amp * (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * swell + 0.3 * amp * rumble(d, 1, 70) * swell

def note(m): return 440 * 2 ** ((m - 69) / 12)

def pad(chord, d, amp=0.05, cutoff=1400, detune=0.18):
    t = secs(d); s = np.zeros_like(t)
    for m in chord:
        for dt in (-detune, 0, detune):
            ph = 2 * np.pi * note(m) * (1 + dt / 100) * t + rng.uniform(0, 6)
            s += 2 * ((ph / (2 * np.pi)) % 1) - 1   # saw
    s = lp(s, cutoff, order=2) / (len(chord) * 3)
    e = np.minimum(1, t / (d * 0.3)) * np.minimum(1, (d - t) / (d * 0.3))
    return amp * s * e

def pluck(m, d=2.5, amp=0.08):
    t = secs(d); f = note(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t * 5)
    return amp * s * np.exp(-t * 1.8) * np.minimum(1, t / 0.004)

class Track:
    def __init__(self, dur): self.x = np.zeros(int(dur * SR) + SR)
    def add(self, at, sig, gain=1.0):
        a = int(at * SR)
        if a >= len(self.x) or a + len(sig) <= 0: return
        if a < 0: sig = sig[-a:]; a = 0
        b = min(len(self.x), a + len(sig)); self.x[a:b] += gain * sig[: b - a]

def write_wav(path, mono, dur):
    import wave
    x = mono[: int(dur * SR)]
    x = lp(x, 14000)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    fade = np.minimum(1, np.arange(len(x)) / (0.5 * SR)) * np.minimum(1, (len(x) - np.arange(len(x))) / (1.0 * SR))
    pcm = (x * fade * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm[:, None], 2, 1).tobytes())
