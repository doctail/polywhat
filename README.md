# polywhat

Low-poly first-person "What if…" videos, built entirely from code (Blender + Python), rendered on a RunPod GPU.

## Run on the pod

```bash
cd /workspace && (git -C polywhat pull --ff-only || git clone --depth 1 https://github.com/doctail/polywhat) && bash polywhat/run.sh heavier
```

The final video is written to `/workspace/polywhat-out/heavier.mp4`.

- First run installs ffmpeg and Blender 5.2 into `/workspace/blender` (cached for next time).
- Re-running the same command **resumes**: frames already rendered are skipped.
- Default engine: EEVEE (~0.5 s/frame on an RTX 5080). Options: `--preview` (960x540) · `--engine cycles` (slower, softer light) · `--samples N` · `--bench N`.
- Long videos are split into acts (see `ACTS` in `timeline.py`); each act renders in its own Blender process and is skipped if already complete.

## Layout

```
run.sh                 entry point (setup + render)
tools/setup.sh         installs ffmpeg + Blender on the pod
tools/render.py        pipeline: Blender frames -> overlay -> audio -> mp4
tools/overlay.py       HUD, captions, vignette (shared look for every video)
tools/pw3d.py          shared Blender helpers (materials, hands, camera keys, render setup)
tools/sfx.py           sound synthesis toolkit (music + effects)
fonts/                 EB Garamond + Inter (SIL Open Font License)
videos/<name>/
  timeline.py          timings, captions, HUD values (single source of truth)
  scene.py             Blender scene + animation, built from code
  audio.py             original music + sound effects (numpy synthesis)
```

## Videos

| folder | status |
|---|---|
| `heavier` | What If You Got Heavier Every Hour and Couldn't Stop? — 8:40, 8 acts |
| `heavier-test` | 30 s pilot (scale -> bed -> floor) |
