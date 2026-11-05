"""What If You Got Heavier Every Hour and Couldn't Stop? — full video (8:40).
Single source of truth for timing: scene.py (Blender, per act), audio.py and the overlay all read this file.
Physics: mass = 70 kg x 2^hour, body size unchanged."""

FPS = 30
TITLE = "What If You Got Heavier Every Hour and Couldn't Stop?"

# acts: (name, start s, end s) — each act is rendered by its own Blender process
ACTS = [
    ("house",   0.0,  36.0),
    ("shaft",  36.0, 120.0),
    ("cavity", 120.0, 170.0),
    ("plunge", 170.0, 245.0),
    ("surface", 245.0, 330.0),
    ("space",  330.0, 410.0),
    ("galaxy", 410.0, 495.0),
    ("outro",  495.0, 520.0),
]
DURATION = ACTS[-1][2]

HOUR_KEYS = [
    (0, 0), (3.0, 0), (3.6, 1), (6.0, 1), (6.6, 2), (12.4, 2), (13.2, 3), (20.2, 3), (21.0, 4), (27.4, 4), (28.2, 5),
    (34.0, 5), (35.0, 6),
    (46, 8), (52, 10), (60, 12), (68, 15), (77, 17), (89, 21), (102, 24),
    (122, 25), (135, 27), (146, 29), (150, 31),
    (178, 36), (196, 40), (205, 50), (218, 58), (232, 66), (240, 70),
    (250, 72), (262, 74), (277, 75), (291, 76), (305, 77), (319, 79), (329, 80),
    (352, 81), (357, 82), (380, 88), (392, 95),
    (414, 100), (430, 105), (440, 110), (452, 115), (478, 117),
]

# event times used by scene + audio
EVENTS = dict(
    walk=8.4, sit=11.8, look_bed=14.4, bed_break=16.2, cracks=18.6, floor_break=23.4, land=24.3,
    cracks2=28.4, floor2_break=31.0, land2=31.8,
    pipes=57.0, concrete=68.0, granite=77.0, glow=82.0, close=95.0, dust=112.0,
    pebbles=142.0, planet=162.0,
    plunge=171.0, mantle=186.0, core=229.0,
    plane=268.0, collapse_start=291.0, crush=325.0,
    bh=372.0, swallow=380.0, sun=392.0,
    pullback=412.0, sgr=462.0, outweigh=489.0,
)

CAPTIONS = [
    # house
    (0.4, 3.3, "In five days, you will outweigh a black hole."),
    (3.6, 6.0, "Every hour, your mass doubles."),
    (6.6, 9.4, "Your body stays exactly the same size."),
    (9.8, 12.2, "Everything around you has to deal with it."),
    (13.2, 15.8, "Hour three. Over half a tonne."),
    (16.4, 18.4, "Your bed gives up first."),
    (19.0, 21.0, "The floor is next."),
    (21.2, 23.2, "Hour four. As heavy as a car."),
    (24.8, 27.3, "You land one floor down."),
    (28.2, 30.7, "Hour five. This floor won't hold either."),
    (32.4, 35.6, "Hour six. Nothing in a house can hold an elephant on one spot."),
    # shaft
    (37.0, 40.5, "Below the house, the soil doesn't hold."),
    (42.0, 45.0, "You start to sink."),
    (47.0, 50.0, "Hour eight. Eighteen tonnes."),
    (52.0, 55.5, "Hour ten. Half a blue whale."),
    (57.0, 60.5, "Pipes. Cables. Foundations."),
    (62.0, 65.0, "None of it slows you down."),
    (68.0, 71.5, "Hour fifteen. Concrete crumbles like chalk."),
    (77.0, 80.5, "Hour seventeen. Even granite gives way."),
    (82.0, 85.5, "The rock around you starts to glow."),
    (89.0, 92.5, "Hour twenty-one. Heavier than the largest aircraft carrier ever built."),
    (95.0, 98.5, "Above you, the hole closes."),
    (102.0, 105.5, "Hour twenty-four. One day. One million tonnes."),
    (108.0, 111.0, "And something strange begins."),
    (113.0, 117.5, "Dust is falling toward you. Sideways."),
    # cavity
    (122.0, 125.5, "Everything with mass has gravity."),
    (128.0, 131.5, "Yours is no longer small."),
    (135.0, 138.5, "Hour twenty-seven. Heavier than the Great Pyramid."),
    (142.0, 146.0, "Pebbles drift in. Then rocks."),
    (150.0, 153.5, "Hour thirty-one."),
    (155.0, 159.5, "One meter away, you pull as hard as the whole Earth."),
    (162.0, 166.5, "You are a planet now. Buried inside another one."),
    # plunge
    (172.0, 175.5, "You fall faster."),
    (179.0, 182.5, "Through the crust."),
    (186.0, 190.0, "Into the mantle. Rock that flows like very slow honey."),
    (196.0, 199.5, "Hour forty. Seventy-seven billion tonnes."),
    (205.0, 209.5, "Hour fifty. Roughly the mass of the asteroid that ended the dinosaurs."),
    (215.0, 218.5, "Day three. Thousands of degrees."),
    (222.0, 225.5, "You don't feel any of it."),
    (229.0, 232.5, "You reach the core."),
    (235.0, 238.5, "The center of the Earth. The bottom of everything."),
    (240.5, 244.5, "Hour seventy. You outweigh the Moon."),
    # surface
    (247.0, 250.5, "Meanwhile, on the surface."),
    (253.0, 256.5, "Nobody knows where you went."),
    (262.0, 265.5, "Hour seventy-four. Everyone weighs twenty percent more."),
    (269.0, 272.5, "Stairs feel steeper. Planes need longer runways."),
    (277.0, 280.5, "Hour seventy-five. Over forty percent more."),
    (285.0, 288.5, "Old bridges start to fail."),
    (291.0, 294.5, "Hour seventy-six. Gravity has almost doubled."),
    (298.0, 301.5, "Trees bend. Roofs give way."),
    (305.0, 309.0, "Hour seventy-seven. You are heavier than the Earth."),
    (312.0, 315.5, "Standing up is no longer possible."),
    (319.0, 323.0, "Hour seventy-nine. Eight times normal gravity."),
    (325.0, 329.5, "The planet starts falling inward. Toward you."),
    # space
    (332.0, 335.5, "From space, it looks almost quiet."),
    (339.0, 343.0, "The Earth is shrinking."),
    (347.0, 351.0, "Oceans, mountains, cities. All sliding inward."),
    (357.0, 360.5, "Hour eighty-two."),
    (362.0, 366.0, "Fifty-six Earths of mass, inside a human body."),
    (368.0, 371.0, "Not even light can escape now."),
    (372.5, 376.0, "You are a black hole."),
    (380.0, 384.0, "And what was left of the Earth falls in."),
    (392.0, 395.5, "Day four. Heavier than the Sun."),
    (398.0, 402.0, "Now the Sun orbits you."),
    # galaxy
    (412.0, 415.5, "And you keep doubling."),
    (420.0, 424.0, "Planets lose their orbits."),
    (430.0, 434.0, "Nearby stars begin to drift toward you."),
    (440.0, 444.0, "Hour one hundred and ten. Forty-six thousand Suns."),
    (452.0, 456.0, "Hour one hundred and fifteen. One and a half million Suns."),
    (462.0, 466.0, "At the heart of our galaxy sits Sagittarius A*."),
    (468.0, 472.0, "Four million Suns. The heaviest thing for light-years."),
    (478.0, 482.0, "Hour one hundred and seventeen."),
    (484.0, 488.0, "Less than five days after you stepped on a scale,"),
    (489.0, 493.0, "you outweigh it."),
    # outro
    (497.0, 501.0, "One hundred and seventeen doublings."),
    (503.0, 507.0, "That's all it took."),
    (510.0, 513.5, "And it still isn't stopping."),
    (515.0, 519.0, "What if you got lighter instead?"),
]

# milestones: (hour, label, value shown under NEXT)
MILESTONES = [   # (hour you cross it, label, its mass)
    (1, "TWO ADULTS", "140 kg"), (2, "A GRIZZLY BEAR", "~280 kg"), (3, "WHAT YOUR BED CAN HOLD", "~500 kg"),
    (4, "A SMALL CAR", "~1.1 t"), (6, "AN ELEPHANT", "~4.5 t"), (10, "HALF A BLUE WHALE", "~72 t"),
    (15, "WHAT CONCRETE CAN HOLD", "~2,000 t"), (17, "WHAT GRANITE CAN HOLD", "~9,000 t"),
    (20.4, "THE LARGEST AIRCRAFT CARRIER", "~100,000 t"), (26.4, "THE GREAT PYRAMID", "~6 million t"),
    (31, "EARTH-STRENGTH GRAVITY", "at one meter"), (50, "THE DINOSAUR ASTEROID", "trillions of t"),
    (69.8, "THE MOON", "1 Moon"), (76.3, "THE EARTH", "1 Earth"), (82, "A BLACK HOLE YOUR SIZE", "57 Earths"),
    (94.5, "THE SUN", "1 Sun"), (116.6, "SAGITTARIUS A*", "4.3 million Suns"),
]

EARTH_KG, SUN_KG, MOON_KG = 5.97e24, 1.99e30, 7.35e22
EQUAL = {1, 2, 3, 4, 6, 10, 82}   # milestones that mean 'as heavy as' at the moment they are reached

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def hour_at(t):
    for (t0, a), (t1, b) in zip(HOUR_KEYS, HOUR_KEYS[1:]):
        if t <= t1:
            return a + (b - a) * smooth((t - t0) / (t1 - t0)) if t1 > t0 else b
    return HOUR_KEYS[-1][1]

def mass_at(t): return 70.0 * 2 ** hour_at(t)
def surface_g(t): return (EARTH_KG + mass_at(t)) / EARTH_KG

def act_at(t):
    for n, a, b in ACTS:
        if a <= t < b: return n
    return ACTS[-1][0]

def fmt_mass(m):
    if m < 1000: return f"{round(m):,} kg"
    t = m / 1000
    if t < 10: return f"{t:,.2f} t"
    if t < 1e6: return f"{t:,.0f} t"
    if m < MOON_KG * 0.5:
        for div, name in ((1e6, "million"), (1e9, "billion"), (1e12, "trillion"), (1e15, "quadrillion"), (1e18, "quintillion")):
            if t < div * 1000: return f"{t / div:,.1f} {name} t"
    if m < EARTH_KG * 0.5: return f"{m / MOON_KG:,.1f} Moons"
    if m < SUN_KG * 0.5: return f"{m / EARTH_KG:,.1f} Earths" if m < 100 * EARTH_KG else f"{m / EARTH_KG:,.0f} Earths"
    s = m / SUN_KG
    if s < 1000: return f"{s:,.1f} Suns"
    if s < 1e6: return f"{s / 1000:,.0f} thousand Suns"
    return f"{s / 1e6:,.1f} million Suns"

HUD = dict(label="YOUR MASS", right_label="HOUR", right_sub="DOUBLING EVERY HOUR")

def hud_state(t):
    h = hour_at(t); m = mass_at(t)
    passed = [x for x in MILESTONES if x[0] <= h + 1e-6]
    upcoming = [x for x in MILESTONES if x[0] > h + 1e-6]
    if passed:
        eq = passed[-1][0] in EQUAL and h - passed[-1][0] < 0.15
        sub = ("AS HEAVY AS " if eq else "HEAVIER THAN ") + passed[-1][1]
        if passed[-1][0] == 31: sub = "ONE METER AWAY, YOU PULL LIKE EARTH"
    else:
        sub = "AS HEAVY AS AN ADULT"
    if act_at(t) == "surface":
        sub = f"SURFACE GRAVITY  {surface_g(t):.1f} g"
    nx, nv = (upcoming[0][1], upcoming[0][2]) if upcoming else ("NOTHING", "it doesn't stop")
    day = int(h // 24) + 1
    return dict(value=fmt_mass(m), sub=sub, next_label=nx, next_value=nv,
                right_value=str(int(h + 0.02)), right_sub=f"DAY {day}  ·  DOUBLING EVERY HOUR")
