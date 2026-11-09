# shared pod setup for the city scenes: Blender, python deps in Blender, CC0 assets, MPFB, BlendKit cars
# sourced by tools/shock_test.sh and tools/engine_test.sh (expects $ROOT)
bash "$ROOT/tools/setup.sh"
BL=/workspace/blender/blender
# GPU check first: stop in 2 minutes instead of 15 if Blender cannot use the card on this host
GPUCHK=$("$BL" -b --factory-startup --debug-cycles --python-expr "import bpy; p=bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX','CUDA'):
    try:
        p.compute_device_type=t; p.get_devices(); print('[gpu-check]', t, [d.name for d in p.devices if d.type==t])
    except Exception as e: print('[gpu-check]', t, 'error', e)" 2>&1)
echo "$GPUCHK" | grep "\[gpu-check\]"
if ! echo "$GPUCHK" | grep -q "\[gpu-check\] [A-Z]* \['"; then
  echo "[gpu] ERROR: Blender cannot use the GPU on this pod. Close it and take another one. Details:"
  echo "$GPUCHK" | grep -i -E "cuda|optix|cuinit|error" | grep -v gpu-check | head -8
  exit 3
fi
PY=$(ls -d /workspace/blender/*/python/bin/python3.[0-9]* | head -1)
"$PY" -c "import shapely, mapbox_earcut" 2>/dev/null || { "$PY" -m ensurepip -q || true; "$PY" -m pip install -q shapely mapbox_earcut; }
python3 "$ROOT/tools/city/fetch_assets.py" /workspace/assets
# realistic people: MPFB 2 (MakeHuman for Blender). The extension lives in ~/.config, which a pod restart wipes: reinstall if missing
[ -d /workspace/mpfb2 ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/makehumancommunity/mpfb2 /workspace/mpfb2
ls ~/.config/blender/5.2/extensions/user_default/mpfb >/dev/null 2>&1 || "$BL" -b -P "$ROOT/tools/city/install_mpfb.py" -- /workspace/mpfb2 2>&1 | grep "\[mpfb\]"
python3 "$ROOT/tools/city/fetch_cars.py" /workspace/assets || true   # needs BLENDERKIT_API_KEY, else procedural cars
