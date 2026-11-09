#!/usr/bin/env bash
# Speed/quality comparison on the asteroid shock clip: EEVEE vs Cycles with few samples, same frames.
#   bash polywhat/tools/engine_test.sh            (frames 100-220 = the wave arriving; 1280x720)
# Result: /workspace/polywhat-out/engine_test/compare.mp4 (top EEVEE, bottom Cycles) + times.txt
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/tools/city/pod_setup.sh"
OUT=/workspace/polywhat-out/engine_test; mkdir -p "$OUT"
FR="${FRAMES:-100-220}"
for cfg in "eevee:64" "cycles:20"; do
  eng=${cfg%%:*}; sp=${cfg##*:}
  echo "[test] $eng $sp samples, frames $FR"
  "$BL" -b --factory-startup -P "$ROOT/videos/asteroid/shock_test.py" -- --assets /workspace/assets --out "$OUT/$eng" \
        --res 1280x720 --samples "$sp" --engine "$eng" --device gpu --frames "$FR" > "$OUT/$eng.log" 2>&1
  grep -E "Error|Traceback" "$OUT/$eng.log" | head -5
  grep "\[shock\] frame" "$OUT/$eng.log" | tail -n +2 | awk -v e=$eng '{gsub("s","",$4); t+=$4; c++} END {if(c) printf "[test] %s: %.2f s per frame (%d frames)\n", e, t/c, c}' | tee -a "$OUT/times.txt"
done
python3 "$ROOT/tools/engine_compare.py" "$OUT"
