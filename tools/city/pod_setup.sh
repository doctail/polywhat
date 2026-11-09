# shared pod setup for the city scenes: Blender, python deps in Blender, CC0 assets, MPFB, BlendKit cars
# sourced by tools/shock_test.sh and tools/engine_test.sh (expects $ROOT)
bash "$ROOT/tools/setup.sh"
BL=/workspace/blender/blender
PY=$(ls -d /workspace/blender/*/python/bin/python3.[0-9]* | head -1)
"$PY" -c "import shapely, mapbox_earcut" 2>/dev/null || { "$PY" -m ensurepip -q || true; "$PY" -m pip install -q shapely mapbox_earcut; }
python3 "$ROOT/tools/city/fetch_assets.py" /workspace/assets
# realistic people: MPFB 2 (MakeHuman for Blender). The extension lives in ~/.config, which a pod restart wipes: reinstall if missing
[ -d /workspace/mpfb2 ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/makehumancommunity/mpfb2 /workspace/mpfb2
ls ~/.config/blender/5.2/extensions/user_default/mpfb >/dev/null 2>&1 || "$BL" -b -P "$ROOT/tools/city/install_mpfb.py" -- /workspace/mpfb2 2>&1 | grep "\[mpfb\]"
python3 "$ROOT/tools/city/fetch_cars.py" /workspace/assets || true   # needs BLENDERKIT_API_KEY, else procedural cars
