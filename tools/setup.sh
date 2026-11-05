#!/usr/bin/env bash
# One-time setup on a fresh RunPod pod (Ubuntu). Safe to re-run: skips what is already installed.
set -euo pipefail
BL_SERIES="${BL_SERIES:-5.2}"
BL_DIR="/workspace/blender"

need_apt=()
for p in ffmpeg xz-utils curl libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 libice6 libegl1; do
  dpkg -s "$p" >/dev/null 2>&1 || need_apt+=("$p")
done
if [ ${#need_apt[@]} -gt 0 ]; then
  echo "[setup] apt: ${need_apt[*]}"
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${need_apt[@]}" >/dev/null
fi

python3 -c "import numpy, PIL, scipy" 2>/dev/null || python3 -m pip install -q numpy pillow scipy

if [ ! -x "$BL_DIR/blender" ]; then
  FILE=$(curl -s "https://download.blender.org/release/Blender${BL_SERIES}/" | grep -o "blender-${BL_SERIES}\.[0-9]*-linux-x64\.tar\.xz" | sort -V | tail -1)
  [ -n "$FILE" ] || { echo "[setup] could not find Blender ${BL_SERIES} on download.blender.org"; exit 1; }
  echo "[setup] downloading $FILE"
  mkdir -p "$BL_DIR"
  curl -sL "https://download.blender.org/release/Blender${BL_SERIES}/$FILE" | tar -xJ -C "$BL_DIR" --strip-components=1
fi
"$BL_DIR/blender" --version | head -1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo "[setup] WARNING: no NVIDIA GPU visible"
