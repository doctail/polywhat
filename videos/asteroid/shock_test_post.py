"""Overlay + audio + mp4 for the shock-wave realism test.   python3 shock_test_post.py OUT_DIR [--fps 30]
Reads OUT_DIR/raw/frame_XXXX.png, writes OUT_DIR/shock_test.mp4 and OUT_DIR/shock_test-light.mp4 (480p)."""
import os, sys, glob, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import timeline as TL
from overlay import compose
from sfx import *  # noqa
from PIL import Image

out = sys.argv[1]; FPS = 30; T0 = 170.0; T_SHOCK = 4.0; DUR = 12.0
raw = sorted(glob.glob(os.path.join(out, 'raw', 'frame_*.png')))
comp = os.path.join(out, 'comp'); os.makedirs(comp, exist_ok=True)
for p in raw:
    f = int(os.path.basename(p)[6:10]); dst = os.path.join(comp, f'frame_{f:04d}.jpg')
    if os.path.exists(dst): continue
    compose(Image.open(p), T0 + (f - 1) / FPS, TL).convert('RGB').save(dst, quality=94)
print('overlay done', len(raw), flush=True)

# ---- sound: city ambience -> (wave) boom + glass + debris + alarms
fx = Track(DUR + 1)
amb = lp(noise(DUR + 1), 900) * 0.04 + bp(noise(DUR + 1), 2000, 5000) * 0.006
fx.add(0, amb)
for t in np.arange(0.3, T_SHOCK, 1.1):                     # distant traffic swells
    fx.add(t, whoosh(1.6, 0.04, 200, 700))
fx.add(T_SHOCK - 0.02, boom(6.0, 1.0, 30))
fx.add(T_SHOCK, thud(45, 1.2, 0.8, body=0.6))
fx.add(T_SHOCK, rumble(5.0, 0.35, 60) * np.exp(-secs(5.0) * 0.7))
for k in range(26):                                        # windows bursting along the street
    t = T_SHOCK + 0.02 + abs(np.random.normal(0, 0.35))
    fx.add(t, crack(0.4, np.random.uniform(0.15, 0.4), n=18, lo=2500, hi=9000))
for k in range(5):                                         # glass raining down, hitting the street
    fx.add(T_SHOCK + 0.8 + k * 0.6, debris(2.5, 0.22 - k * 0.03, n=90))
t = np.arange(int(6.5 * SR)) / SR                          # car alarms: two-tone sirens
for start, f1, f2, rate, g in [(T_SHOCK + 0.7, 900, 1300, 2.4, 0.05), (T_SHOCK + 1.1, 700, 1050, 3.1, 0.035)]:
    sw = np.where((t * rate) % 1 < 0.5, f1, f2); ph = 2 * np.pi * np.cumsum(sw) / SR
    fx.add(start, g * np.sign(np.sin(ph)) * 0.6 * np.minimum(1, t / 0.05))
wav = os.path.join(out, 'shock_test.wav'); write_wav(wav, fx.x, DUR)

mp4 = os.path.join(out, 'shock_test.mp4'); light = os.path.join(out, 'shock_test-light.mp4')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', os.path.join(comp, 'frame_%04d.jpg'), '-i', wav,
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', mp4], check=True)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp4, '-vf', 'scale=-2:480', '-c:v', 'libx264', '-preset', 'veryfast',
                '-crf', '26', '-c:a', 'aac', '-b:a', '96k', light], check=True)
print('done:', mp4, light)
