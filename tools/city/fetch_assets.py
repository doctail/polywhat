"""Download the free (CC0) assets used by tools/city/city.py into ASSETS (default /workspace/assets).
Safe to re-run: files already present are skipped.   python3 tools/city/fetch_assets.py [ASSETS]
Sources: ambientCG (facades), Poly Haven (ground textures, sky HDRI, trees/props). All CC0."""
import json, os, subprocess, sys, urllib.request, zipfile, io

ROOT = sys.argv[1] if len(sys.argv) > 1 else ('/workspace/assets' if os.path.isdir('/workspace') else os.path.expanduser('~/assets'))
TEX = os.path.join(ROOT, 'tex'); MOD = os.path.join(ROOT, 'models')
UA = {'User-Agent': 'polywhat-asset-fetch/1.0'}

def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r: return r.read()
        except Exception as e:
            print('  retry', i + 1, url, e, flush=True)
    raise SystemExit('download failed: ' + url)

def save(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url); open(path + '.part', 'wb').write(data); os.replace(path + '.part', path)
    print('  got', os.path.relpath(path, ROOT), len(data) // 1024, 'KB', flush=True)

FACADES = ['Facade001', 'Facade005', 'Facade006', 'Facade012', 'Facade014', 'Facade018A', 'Facade019A', 'Facade020A']
for aid in FACADES:
    d = os.path.join(TEX, aid)
    if os.path.exists(os.path.join(d, f'{aid}_2K-JPG_Color.jpg')): continue
    print('ambientCG', aid, flush=True)
    z = zipfile.ZipFile(io.BytesIO(get(f'https://ambientcg.com/get?file={aid}_2K-JPG.zip')))
    os.makedirs(d, exist_ok=True)
    for n in z.namelist():
        if n.endswith('.jpg'): open(os.path.join(d, os.path.basename(n)), 'wb').write(z.read(n))

def ph_files(aid): return json.loads(get('https://api.polyhaven.com/files/' + aid))
for aid in ['road_damaged', 'road_damaged_clean', 'concrete_pavement', 'concrete_floor_01']:
    d = os.path.join(TEX, aid)
    if all(os.path.exists(os.path.join(d, k + '.jpg')) for k in ('diff', 'nor', 'rough')): continue
    print('Poly Haven', aid, flush=True); f = ph_files(aid)
    for m, k in [('Diffuse', 'diff'), ('nor_gl', 'nor'), ('Rough', 'rough')]:
        save(f[m]['2k']['jpg']['url'], os.path.join(d, k + '.jpg'))
if not os.path.exists(os.path.join(TEX, 'sky.hdr')):
    print('Poly Haven sky', flush=True)
    save(ph_files('kloofendal_48d_partly_cloudy_puresky')['hdri']['4k']['hdr']['url'], os.path.join(TEX, 'sky.hdr'))
for aid in ['island_tree_02', 'fire_hydrant', 'metal_trash_can']:
    d = os.path.join(MOD, aid)
    if os.path.exists(os.path.join(d, aid + '.gltf')): continue
    print('Poly Haven model', aid, flush=True)
    g = ph_files(aid)['gltf']['1k']['gltf']
    for rel, inf in g.get('include', {}).items(): save(inf['url'], os.path.join(d, rel))
    save(g['url'], os.path.join(d, aid + '.gltf'))
print('assets ready in', ROOT)
