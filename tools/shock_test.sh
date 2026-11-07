#!/usr/bin/env bash
# Realism test clip for the asteroid video (12 s, Chelyabinsk shock wave on 5th Ave).
# Usage on the pod:  bash polywhat/tools/shock_test.sh            (1280x720, Cycles GPU, 64 samples)
#                    RES=1920x1080 SAMPLES=96 bash polywhat/tools/shock_test.sh
#                    bash polywhat/tools/shock_test.sh --frames 1-30     (quick check of the first second)
# Result: /workspace/polywhat-out/shock_test/shock_test.mp4  and  shock_test-light.mp4 (480p, send this one to Claude)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
bash "$ROOT/tools/setup.sh"
BL=/workspace/blender/blender
PY=$(ls -d /workspace/blender/*/python/bin/python3.[0-9]* | head -1)
"$PY" -c "import shapely, mapbox_earcut" 2>/dev/null || { "$PY" -m ensurepip -q || true; "$PY" -m pip install -q shapely mapbox_earcut; }
python3 "$ROOT/tools/city/fetch_assets.py" /workspace/assets
# realistic people: MPFB 2 (MakeHuman for Blender). The extension lives in ~/.config, which a pod restart wipes: reinstall if missing
[ -d /workspace/mpfb2 ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/makehumancommunity/mpfb2 /workspace/mpfb2
ls ~/.config/blender/5.2/extensions/user_default/mpfb >/dev/null 2>&1 || "$BL" -b -P "$ROOT/tools/city/install_mpfb.py" -- /workspace/mpfb2 2>&1 | grep "\[mpfb\]"
python3 "$ROOT/tools/city/fetch_cars.py" /workspace/assets   # needs BLENDERKIT_API_KEY, else procedural cars
OUT=/workspace/polywhat-out/shock_test
mkdir -p "$OUT/raw"
START=$(date +%s)
"$BL" -b --factory-startup -P "$ROOT/videos/asteroid/shock_test.py" -- --assets /workspace/assets --out "$OUT/raw" \
      --res "${RES:-1280x720}" --samples "${SAMPLES:-64}" --engine "${ENGINE:-cycles}" --device gpu "$@" 2>&1 \
      | grep --line-buffered -E "^\[shock\]|^\[cars\]|people|city built|shards|Error|Traceback|File \"" || true
echo "[shock] render time: $(( ($(date +%s) - START) / 60 )) min"
python3 "$ROOT/videos/asteroid/shock_test_post.py" "$OUT"
