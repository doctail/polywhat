#!/usr/bin/env bash
# Usage on the pod:  bash polywhat/run.sh VIDEO [--preview] [--engine eevee] [--samples N]
# Result:            /workspace/polywhat-out/VIDEO.mp4
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
[ $# -ge 1 ] || { echo "usage: bash run.sh VIDEO [options]   videos: $(ls "$ROOT/videos" | tr '\n' ' ')"; exit 1; }
bash "$ROOT/tools/setup.sh"
python3 "$ROOT/tools/render.py" "$@"
