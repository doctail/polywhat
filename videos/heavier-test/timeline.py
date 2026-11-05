"""Single source of truth for timing: used by scene.py (Blender), audio.py and the overlay compositor.
Pilot test: 'What If You Got Heavier Every Hour' — first 30 seconds (scale -> bed -> floor)."""
import math

FPS = 30
DURATION = 30.0
TITLE = "What If You Got Heavier Every Hour and Couldn't Stop?"

# hour keyframes (time s, hour). mass = 70 kg * 2^hour
HOUR_KEYS = [(0, 0), (2.6, 0), (3.2, 1), (5.9, 1), (6.5, 2), (13.2, 2), (14.0, 3),
             (20.6, 3), (21.3, 4), (26.6, 4), (27.3, 5)]

EVENTS = dict(
    walk_start=9.4, sit_done=13.0,
    look_bed=17.0,          # gaze drops to the bed under you
    bed_break=18.6,
    cracks=21.2,
    floor_break=24.0, land=24.95,
)

CAPTIONS = [
    (0.6, 2.9, "You step on the scale."),
    (3.4, 5.7, "One hour later, it reads double."),
    (6.7, 9.0, "Then double again."),
    (10.4, 12.6, "You need to sit down."),
    (13.4, 16.3, "Your bed was built for two people."),
    (16.6, 18.3, "Not for this."),
    (19.4, 21.0, "Hour three. Half a tonne."),
    (21.6, 23.8, "Hour four. As heavy as a car."),
    (24.1, 25.9, "The floor gives way."),
    (26.8, 29.6, "And you are still getting heavier."),
]

COMPARE = ["AN ADULT", "TWO ADULTS", "A GRIZZLY BEAR", "A GRAND PIANO", "A SMALL CAR", "A HIPPO"]

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def hour_at(t):
    for (t0, a), (t1, b) in zip(HOUR_KEYS, HOUR_KEYS[1:]):
        if t <= t1:
            return a + (b - a) * smooth((t - t0) / (t1 - t0)) if t1 > t0 else b
    return HOUR_KEYS[-1][1]

def mass_at(t):
    return 70.0 * 2 ** hour_at(t)

def next_target(h):
    if h < 2.5: return ("THE BED", "560 kg")
    if h < 3.5: return ("THE FLOOR", "1,120 kg")
    return ("THE GROUND", "72 t")

def fmt_mass(m):
    if m < 1000: return f"{round(m):,} kg"
    t = m / 1000
    return f"{t:,.2f} t" if t < 10 else f"{t:,.1f} t"

HUD = dict(label="YOUR MASS", right_label="HOUR", right_sub="DOUBLING EVERY HOUR")

def hud_state(t):
    h = hour_at(t); m = mass_at(t)
    nx, nv = next_target(h)
    return dict(value=fmt_mass(m), sub="AS HEAVY AS " + COMPARE[min(5, round(h))],
                next_label=nx, next_value=nv, right_value=str(round(h)))
