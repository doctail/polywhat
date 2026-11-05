# polywhat

Low-poly first-person "What if…" videos, built entirely from code (Blender + Python), rendered on a RunPod GPU.

## Run on the pod

```bash
cd /workspace && (git -C polywhat pull --ff-only || git clone --depth 1 https://github.com/doctail/polywhat) && bash polywhat/run.sh heavier-test
```

The final video is written to `/workspace/polywhat-out/heavier-test.mp4`.

- First run installs ffmpeg and Blender 5.2 into `/workspace/blender` (cached for next time).
- Re-running the same command **resumes**: frames already rendered are skipped.
- Options: `--preview` (960x540, fewer samples, for a quick check) · `--engine eevee` (faster if the pod supports GPU OpenGL) · `--samples N`.

## Layout

```
run.sh                 entry point (setup + render)
tools/setup.sh         installs ffmpeg + Blender on the pod
tools/render.py        pipeline: Blender frames -> overlay -> audio -> mp4
tools/overlay.py       HUD, captions, vignette (shared look for every video)
fonts/                 EB Garamond + Inter (SIL Open Font License)
videos/<name>/
  timeline.py          timings, captions, HUD values (single source of truth)
  scene.py             Blender scene + animation, built from code
  audio.py             original music + sound effects (numpy synthesis)
```

## Videos

| folder | status |
|---|---|
| `heavier-test` | 30 s pilot of "What If You Got Heavier Every Hour" (scale -> bed -> floor) |
