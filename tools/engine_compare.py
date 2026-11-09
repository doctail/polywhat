"""Stack the EEVEE and Cycles frames of engine_test.sh into one labelled video (top EEVEE, bottom Cycles)."""
import os, sys, glob, subprocess
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; tmp = os.path.join(out, 'stack'); os.makedirs(tmp, exist_ok=True)
times = open(os.path.join(out, 'times.txt')).read() if os.path.exists(os.path.join(out, 'times.txt')) else ''
def label(name):
    for l in times.splitlines():
        if f' {name}:' in l: return name.upper() + '  ' + l.split(':', 1)[1].strip()
    return name.upper()
try: font = ImageFont.truetype('DejaVuSans-Bold.ttf', 30)
except Exception: font = ImageFont.load_default()
ev = sorted(glob.glob(os.path.join(out, 'eevee', 'frame_*.png'))); cy = {os.path.basename(p): p for p in glob.glob(os.path.join(out, 'cycles', 'frame_*.png'))}
n = 0
for p in ev:
    q = cy.get(os.path.basename(p))
    if not q: continue
    a = Image.open(p).convert('RGB').resize((960, 540)); b = Image.open(q).convert('RGB').resize((960, 540))
    im = Image.new('RGB', (960, 1080)); im.paste(a, (0, 0)); im.paste(b, (0, 540)); d = ImageDraw.Draw(im)
    for y, txt in ((10, label('eevee')), (550, label('cycles'))):
        d.rectangle((8, y, 8 + 18 * len(txt), y + 40), fill=(0, 0, 0)); d.text((14, y + 4), txt, fill=(255, 220, 60), font=font)
    n += 1; im.save(os.path.join(tmp, f'{n:04d}.jpg'), quality=90)
if n:
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '30', '-i', os.path.join(tmp, '%04d.jpg'), '-c:v', 'libx264', '-crf', '20',
                    '-pix_fmt', 'yuv420p', os.path.join(out, 'compare.mp4')], check=True)
print('[test] compare video:', os.path.join(out, 'compare.mp4'), n, 'frames'); print(times)
