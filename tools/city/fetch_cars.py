"""Download free (royalty-free) vehicle models from BlendKit (blendkit.com) into ASSETS/cars/<name>/*.blend.
Needs a free BlendKit account key in the environment:  export BLENDERKIT_API_KEY=...
   python3 tools/city/fetch_cars.py [ASSETS]
The licence of every model is 'royalty_free' (commercial use in renders allowed, no resale of the model).
Files already present are skipped. Without the key the script exits quietly (procedural cars are used)."""
import json, os, sys, time, uuid, urllib.request, urllib.error

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/workspace/assets'
OUT = os.path.join(ROOT, 'cars'); os.makedirs(OUT, exist_ok=True)
KEY = os.environ.get('BLENDERKIT_API_KEY') or os.environ.get('BLENDKIT_API_KEY')
API = 'https://www.blendkit.com/api/v1'
# (file name, asset version id)  — picked from free search results: everyday traffic, moderate polycount
CARS = [
    ('taxi_a',        'df0873dc-915c-4558-b222-11ee02f3ae3a'),   # Taxi
    ('taxi_b',        'ba44c58c-aa4c-4639-a0f2-d37b21588d6e'),   # Car TAXI
    ('suv_audi_q3',   '84e85e41-a719-4830-93fc-00e5e8d0262d'),   # 2020 Audi Q3 Sportback
    ('suv_audi_rsq3', '09e14f72-bd82-4d18-97dd-aff690dfa243'),   # 2019 Audi RS Q3 Sportback
    ('sedan_bmw_a',   '0d04267e-73c3-465e-a322-058712017cf5'),   # Bmw
    ('sedan_bmw_b',   'e05e1b7a-860f-4f71-bd60-d22eb41ce922'),   # Bmw
    ('sedan_volvo',   '088b3f09-9fd8-46a6-8cb3-de0828248e9e'),   # Volvo S90
    ('suv_landcruiser', 'd0acb569-d94c-480e-bf53-e254fa786d2b'), # Toyota Land Cruiser 200
    ('van_patriot',   'af57776f-2ede-492e-9d85-ca6764bf9bca'),   # Van Patriot USA
    ('police',        '2a656281-2a7a-4479-b655-4920abda5fe9'),   # Police Car
    ('sport_toyota',  '6f9b992c-8c82-451e-bd2d-a3321179f68e'),   # Toyota GR GT
]
PREFER = ['resolution_1K', 'resolution_2K', 'blend']        # smaller textures first: fine for street distance

def req(url, auth=True, raw=False):
    h = {'User-Agent': 'polywhat-fetch/1.0'}
    if auth and KEY: h['Authorization'] = 'Bearer ' + KEY
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=600) as r:
                data = r.read(); return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            print('  http', e.code, url[:90], flush=True)
            if e.code in (401, 403): raise SystemExit('BlendKit refused the key (401/403): check BLENDERKIT_API_KEY')
        except Exception as e:
            print('  retry', i + 1, e, flush=True)
        time.sleep(3)
    return None

if not KEY:
    print('[cars] BLENDERKIT_API_KEY not set: keeping procedural cars'); sys.exit(0)
scene = str(uuid.uuid4())
for name, aid in CARS:
    ddir = os.path.join(OUT, name)
    if os.path.isdir(ddir) and any(x.endswith('.blend') for _, _, fs in os.walk(ddir) for x in fs): continue
    a = req(f'{API}/assets/{aid}/')
    if not a: print('[cars] skip', name); continue
    files = {f.get('fileType'): f for f in a.get('files', [])}
    f = next((files[k] for k in PREFER if k in files), None)
    if not f: print('[cars] no blend for', name, list(files)); continue
    link = req(f['downloadUrl'] + f'?scene_uuid={scene}')
    url = (link or {}).get('filePath')
    if not url: print('[cars] no download link for', name, link); continue
    data = req(url, auth=False, raw=True)
    if not data: print('[cars] download failed', name); continue
    os.makedirs(ddir, exist_ok=True)
    if data[:2] == b'PK':                                  # some resolutions come zipped with their textures
        import zipfile, io; zipfile.ZipFile(io.BytesIO(data)).extractall(ddir)
    else:
        open(os.path.join(ddir, name + '.blend'), 'wb').write(data)
    print(f'[cars] {name}: {a.get("name")} ({a.get("license")}) {len(data) // 1024} KB', flush=True)
print('[cars] ready:', sorted(os.listdir(OUT)))
