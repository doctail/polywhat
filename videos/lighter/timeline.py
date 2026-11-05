"""What If You Got Lighter Every Hour and Couldn't Stop? — script + timing (9:00).
Rule: mass = 70 kg / 2^hour, body keeps its size (volume 0.066 m^3, cross-section ~0.7 m^2) and stays intact.
Physics used for the numbers:
  - floating: you rise to the altitude where air density = your mass / your volume (ISA atmosphere)
  - in space: sunlight pushes ~4.6 µN per m^2 at 1 AU (fully absorbed), falling with 1/r^2 and with the Doppler factor
    (1-b)/(1+b) as you speed up; proper acceleration = force / mass; integrated relativistically from hour 30.
  - 'hours' are YOUR hours; Earth time is computed from time dilation."""
import math

FPS = 30
TITLE = "What If You Got Lighter Every Hour and Couldn't Stop?"

ACTS = [
    ("house",        0.0,  42.0),
    ("street",      42.0, 125.0),
    ("ascent",     125.0, 215.0),
    ("sail",       215.0, 305.0),
    ("interstellar", 305.0, 425.0),
    ("deep",       425.0, 515.0),
    ("outro",      515.0, 540.0),
]
DURATION = ACTS[-1][2]

HOUR_KEYS = [
    (0, 0), (3.6, 0), (4.2, 1), (13.0, 1), (13.6, 2), (27.2, 2), (28.0, 3), (42, 3.1),
    (43, 4), (60, 4.6), (62, 5), (78, 6), (86, 7), (102, 8), (112, 9), (122, 9.9), (125, 10),
    (133, 11), (146, 12), (153, 13), (160, 15), (176, 16), (184, 17), (192, 20), (196, 22), (202, 25), (208, 28), (215, 29),
    (222, 30), (230, 31), (242, 34), (253, 36.5), (270, 41), (281, 44), (289, 46), (297, 50), (305, 51),
    (318, 54), (329, 56), (341, 59), (355, 62), (368, 66), (380, 72), (390, 80), (398, 90), (413, 95), (423, 100),
    (429, 102), (436, 106), (450, 112), (463, 120), (470, 126), (487, 131), (497, 140), (502, 150), (540, 150),
]

EVENTS = dict(
    jump=24.0, ceiling=24.6, launch=31.4, door=36.0,
    gust=52.0, blown=66.0, grab=72.0, lift=118.0, float=122.5,
    clouds=136.0, jet=146.5, dark=166.0, meteors=202.0, sunpush=212.0,
    leave_atm=236.0, mars=253.0, jupiter=270.0, saturn=281.0, neptune=297.0,
    voyager=341.0, blueshift=355.0, proxima=429.0, galaxy_exit=487.0, galaxy_view=494.0,
)

CAPTIONS = [
    # house
    (0.4, 3.4, "In less than six days, you will leave the galaxy."),
    (4.0, 6.8, "Every hour, your mass halves."),
    (7.4, 10.4, "Your body stays exactly the same size."),
    (11.0, 13.2, "Hour one. You feel light. Fast."),
    (13.8, 16.6, "Hour two. Seventeen kilograms."),
    (17.2, 20.2, "Your muscles are as strong as ever."),
    (20.8, 23.6, "So a small jump..."),
    (24.0, 26.8, "...puts your head into the ceiling."),
    (28.0, 30.8, "Hour three. Under nine kilograms."),
    (31.4, 34.4, "Every step launches you across the room."),
    (35.0, 38.0, "Time to go outside."),
    (38.6, 41.6, "That's a mistake."),
    # street
    (43.0, 46.0, "Hour four. As light as a house cat."),
    (47.5, 50.5, "Walking feels like walking on the Moon."),
    (52.0, 55.0, "And then the wind picks up."),
    (62.0, 65.0, "Hour five. A gust is stronger than your weight."),
    (66.0, 69.0, "It carries you down the street."),
    (72.0, 75.0, "You grab the first thing you can."),
    (79.0, 82.0, "Hour six. Your feet barely touch the ground."),
    (86.0, 89.0, "Hour seven. Lighter than a basketball."),
    (93.0, 96.0, "Even a breeze moves you now."),
    (103.0, 106.0, "Hour eight. You drift like a leaf."),
    (112.5, 115.5, "Hour nine. Lighter than a phone."),
    (118.0, 121.0, "And then your feet leave the ground."),
    (122.5, 125.0, "Hour ten. You are lighter than air."),
    # ascent
    (127.0, 130.5, "You float. Slowly. Upward."),
    (133.5, 137.0, "Hour eleven. Eight kilometers. Almost as high as Everest."),
    (140.0, 143.5, "It's far below freezing. You don't feel a thing."),
    (146.5, 150.0, "Hour twelve. Thirteen kilometers. Above the jets."),
    (153.0, 156.5, "Hour thirteen. Eight grams, and still rising."),
    (160.0, 163.5, "Hour fifteen. Inside the ozone layer."),
    (166.0, 169.5, "The sky above you is turning black."),
    (176.0, 179.5, "Hour sixteen. Lighter than a paperclip."),
    (184.0, 187.5, "Hour seventeen. Thirty-five kilometers up."),
    (190.5, 194.0, "Hour twenty. Fifty kilometers. The air is almost gone."),
    (196.0, 199.5, "Hour twenty-two. Lighter than a grain of rice."),
    (202.0, 205.5, "Hour twenty-five. Meteors burn up around you."),
    (208.0, 211.5, "Hour twenty-eight. Something else starts to push you."),
    (212.0, 214.8, "Sunlight."),
    # sail
    (217.0, 221.0, "Light carries a tiny push. Normally, you'd never notice."),
    (223.0, 226.5, "But you now weigh less than a grain of sand."),
    (230.0, 234.0, "Hour thirty-one. The Sun pushes harder than the Earth pulls."),
    (236.0, 239.5, "You leave the atmosphere behind."),
    (242.0, 245.5, "Hour thirty-four. One percent of the speed of light."),
    (253.0, 256.5, "You cross the orbit of Mars."),
    (259.0, 263.0, "Every hour you get lighter, so every hour the push gets stronger."),
    (270.0, 273.5, "Hour forty-one. Jupiter's orbit."),
    (281.0, 284.5, "Hour forty-four. Saturn's. Almost a third of light speed."),
    (289.0, 292.5, "Hour forty-six. Lighter than a speck of dust."),
    (297.0, 301.0, "Hour fifty. You pass Neptune at two-thirds the speed of light."),
    # interstellar
    (307.0, 310.5, "Nothing in the solar system can catch you now."),
    (314.0, 317.5, "The Sun is just a bright star behind you."),
    (322.0, 325.5, "Hour fifty-five. Lighter than a single bacterium."),
    (329.0, 332.5, "Hour fifty-six. Ninety-two percent of light speed."),
    (341.0, 344.5, "Hour fifty-nine. You pass Voyager 1. It took forty-nine years to get here."),
    (348.0, 351.5, "You took two and a half days."),
    (355.0, 358.5, "Hour sixty-two. The stars ahead are turning blue."),
    (361.5, 365.0, "The stars behind you turn red, and fade."),
    (368.0, 371.5, "Hour sixty-six. Lighter than a virus."),
    (375.0, 378.5, "Time is slowing down. For you."),
    (381.0, 385.0, "For every hour you feel, days pass on Earth."),
    (390.0, 393.5, "Hour eighty. Lighter than a single protein."),
    (398.0, 401.5, "Hour ninety. Earth has aged half a year."),
    (406.0, 409.5, "You are still speeding up."),
    (413.0, 416.5, "Hour ninety-five. You weigh as much as one proton."),
    (420.0, 424.0, "Hour one hundred. Three years have passed on Earth."),
    # deep
    (429.0, 432.5, "Hour one hundred and two. You pass the nearest star."),
    (436.0, 439.5, "Hour one hundred and six. Lighter than an electron."),
    (443.0, 446.5, "But still not zero."),
    (450.0, 453.5, "Hour one hundred and twelve. Earth has aged twenty-six years."),
    (456.5, 460.5, "For you, it's been four and a half days."),
    (463.0, 466.5, "Hour one hundred and twenty. A century."),
    (470.0, 473.5, "Hour one hundred and twenty-six. Lighter than a neutrino."),
    (477.0, 480.5, "Lighter than almost anything that has mass."),
    (487.0, 490.5, "Hour one hundred and thirty-one. You rise out of the Milky Way."),
    (494.0, 497.5, "Behind you, the whole galaxy comes into view."),
    (502.0, 505.5, "Hour one hundred and fifty. Nineteen thousand light-years out."),
    (508.0, 512.5, "On Earth, nineteen thousand years have passed."),
    # outro
    (517.0, 520.5, "One hundred and fifty halvings."),
    (522.0, 525.5, "And you still haven't reached zero."),
    (528.0, 531.5, "You never will."),
    (533.0, 538.0, "What if you got heavier instead?"),
]

# (hour you cross it, label, its mass)
MILESTONES = [
    (1, "A TEN-YEAR-OLD", "~35 kg"), (4, "A HOUSE CAT", "~4.5 kg"), (6.8, "A BASKETBALL", "~600 g"), (8.7, "A PHONE", "~170 g"),
    (9.8, "THE AIR YOU DISPLACE", "~80 g"), (16.1, "A PAPERCLIP", "~1 g"), (21.5, "A GRAIN OF RICE", "~25 mg"),
    (30, "A GRAIN OF SAND", "~65 µg"), (46, "A SPECK OF DUST", "~1 ng"), (55, "A BACTERIUM", "~1 pg"),
    (66, "A VIRUS", "~10^-18 kg"), (79, "A PROTEIN MOLECULE", "~10^-22 kg"), (95, "A PROTON", "1.7×10^-27 kg"),
    (106, "AN ELECTRON", "9.1×10^-31 kg"), (126, "A NEUTRINO (UPPER LIMIT)", "<10^-36 kg"),
]
EQUAL = {1, 95}

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def hour_at(t):
    for (t0, a), (t1, b) in zip(HOUR_KEYS, HOUR_KEYS[1:]):
        if t <= t1:
            return a + (b - a) * smooth((t - t0) / (t1 - t0)) if t1 > t0 else b
    return HOUR_KEYS[-1][1]

def mass_h(h): return 70.0 * 2 ** (-h)
def mass_at(t): return mass_h(hour_at(t))
def act_at(t):
    for n, a, b in ACTS:
        if a <= t < b: return n
    return ACTS[-1][0]

# ---- atmosphere: float altitude (km) for a given hour
_ISA = [(0, 1.225), (2, 1.007), (4, 0.819), (6, 0.660), (8, 0.526), (10, 0.414), (12, 0.312), (14, 0.228), (16, 0.166), (18, 0.122),
        (20, 0.0889), (25, 0.0401), (30, 0.0184), (40, 0.0040), (50, 0.00103), (60, 3.1e-4), (70, 8.3e-5), (80, 1.85e-5), (90, 3.4e-6), (100, 5.6e-7)]
VOLUME = 70 / 1060
def altitude_km(h):
    rho = mass_h(h) / VOLUME
    if rho >= _ISA[0][1]: return 0.0
    for (h0, r0), (h1, r1) in zip(_ISA, _ISA[1:]):
        if r1 <= rho <= r0:
            k = (math.log(r0) - math.log(rho)) / (math.log(r0) - math.log(r1)); return h0 + k * (h1 - h0)
    return 100.0

# ---- light sail flight from hour 30 (relativistic), tabulated per 0.25 h
def _simulate():
    c, L, AU, A = 2.998e8, 3.828e26, 1.496e11, 0.7
    tau, w, r, te = 30 * 3600.0, 0.0, AU, 30 * 3600.0
    tab = {}
    nxt = 30.0
    while tau < 160 * 3600:
        m = mass_h(tau / 3600); b = math.tanh(w)
        F = L / (4 * math.pi * r * r * c) * A * math.exp(-2 * w)   # = (1-b)/(1+b), stable at b -> 1
        a = F / m
        h = min(60.0, max(1e-3, 1e-4 * c / max(a, 1e-9)))
        w += a / c * h; r += c * math.sinh(w) * h; te += math.cosh(w) * h; tau += h
        if tau / 3600 >= nxt:
            tab[round(nxt, 2)] = (math.tanh(w), r / AU, te / 3600); nxt += 0.25
    return tab
_SAIL = _simulate()
def sail_state(h):
    """(beta, distance from Sun in AU, Earth time in hours) at your hour h (>= 30)."""
    if h < 30: return (0.0, 1.0, h)
    k = round(math.floor(h * 4) / 4, 2); k = min(k, max(_SAIL))
    return _SAIL.get(k, _SAIL[max(_SAIL)])

# ---- formatting
def fmt_mass(m):
    if m >= 1: return f"{m:,.1f} kg" if m < 10 else f"{m:,.0f} kg"
    for unit, f in (("g", 1e-3), ("mg", 1e-6), ("µg", 1e-9), ("ng", 1e-12), ("pg", 1e-15)):
        if m >= f: v = m / f; return f"{v:,.0f} {unit}" if v >= 10 else f"{v:,.1f} {unit}"
    e = math.floor(math.log10(m)); mant = m / 10 ** e
    return f"{mant:.1f}×10^{e} kg"   # ^n is drawn as a superscript by the overlay

def fmt_speed(b):
    if b < 0.001: return f"{b * 299792:,.0f} km/s"
    if b < 0.99: return f"{b * 100:.1f}% of light"
    nines = min(12, int(-math.log10(1 - b)))
    return f"{b * 100:.{max(1, nines - 1)}f}% of light"

def fmt_years(hours):
    y = hours / (24 * 365.25)
    if y < 1 / 12: return f"+{hours / 24:,.0f} days"
    if y < 1: mo = round(y * 12); return f"+{mo} month" + ("s" if mo != 1 else "")
    return f"+{y:,.1f} years" if y < 10 else f"+{y:,.0f} years"

HUD = dict(label="YOUR MASS", right_label="HOUR", right_sub="HALVING EVERY HOUR")

def hud_state(t):
    h = hour_at(t); m = mass_h(h)
    passed = [x for x in MILESTONES if x[0] <= h + 1e-6]; upcoming = [x for x in MILESTONES if x[0] > h + 1e-6]
    if passed:
        eq = passed[-1][0] in EQUAL and h - passed[-1][0] < 0.3
        sub = ("AS LIGHT AS " if eq else "LIGHTER THAN ") + passed[-1][1]
    else:
        sub = "A NORMAL ADULT"
    nx, nv = (upcoming[0][1], upcoming[0][2]) if upcoming else ("ZERO", "never")
    st = dict(value=fmt_mass(m), sub=sub, next_label=nx, next_value=nv, right_value=str(int(h + 0.02)),
              right_sub=f"DAY {int(h // 24) + 1}  ·  HALVING EVERY HOUR")
    act = act_at(t)
    if act == "ascent":
        st["extra_label"], st["extra_value"] = "ALTITUDE", f"{altitude_km(h):,.0f} km"
    elif act in ("sail", "interstellar", "deep", "outro") and h >= 30:
        b, au, te = sail_state(h)
        if act == "sail" or h < 78: st["extra_label"], st["extra_value"] = "SPEED", fmt_speed(b)
        else: st["extra_label"], st["extra_value"] = "ON EARTH", fmt_years(te)
    return st
