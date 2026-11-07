"""What Every Asteroid Size Looks Like Hitting Your City — full video (~8:35).
Single source of truth for timing: scene.py (Blender, per act), audio.py and the overlay all read this file.
You stand on the same street for every impact. Each size gets its own act.
Numbers: stony asteroid (3,000 kg/m3) at ~20 km/s unless a real event is named. Energy = 1/2 m v^2, TNT 4.184e9 J/t."""
import math

FPS = 30
TITLE = "What Every Asteroid Size Looks Like Hitting Your City"

ACTS = [
    ("intro",     0.0,  22.0),
    ("pebble",   22.0,  58.0),    # 1 cm  - shooting star
    ("stone",    58.0,  96.0),    # 10 cm - meteorite through a car roof
    ("boulder",  96.0, 136.0),    # 1 m   - daytime fireball
    ("chelyab", 136.0, 196.0),    # 20 m  - Chelyabinsk airburst, windows blow in
    ("tunguska", 196.0, 254.0),   # 50 m  - Tunguska, forest/town flattened
    ("city",    254.0, 314.0),    # 140 m - city killer, ground impact 40 km away
    ("km1",     314.0, 374.0),    # 1 km  - fireball dome over the horizon, ejecta rain
    ("km10",    374.0, 446.0),    # 10 km - Chicxulub: the sky catches fire
    ("km100",   446.0, 496.0),    # 100 km - rock vapour wall
    ("outro",   496.0, 515.0),
]
DURATION = ACTS[-1][2]

def tnt(d_m, v=20e3, rho=3000.0):
    m = rho * math.pi / 6 * d_m ** 3
    return 0.5 * m * v * v / 4.184e9          # tonnes of TNT

def fmt_tnt(t):
    if t < 1: return f"{t * 1e3:,.0f} kg TNT" if t >= 1e-3 else f"{t * 1e6:,.0f} g TNT"
    if t < 1e3: return f"{t:,.0f} t TNT"
    if t < 1e6: return f"{t / 1e3:,.0f} kilotons"
    mt = t / 1e6
    if mt < 1e3: return f"{mt:,.0f} megatons"
    if mt < 1e6: return f"{mt / 1e3:,.0f} thousand Mt"
    if mt < 1e9: return f"{mt / 1e6:,.0f} million Mt"
    return f"{mt / 1e9:,.0f} billion Mt"

# per size: act, diameter label, comparison, icon, energy (t TNT), how often, distance to impact
SIZES = [
    ("pebble",   "1 cm",   "A PEA",            "rice",      tnt(0.01),  "MILLIONS EVERY DAY",          "80 km UP"),
    ("stone",    "10 cm",  "A BASEBALL",       "ball",      tnt(0.10),  "MANY EVERY DAY",              "NEXT TO YOU"),
    ("boulder",  "1 m",    "A WASHING MACHINE", "car",      tnt(1.0),   "SEVERAL TIMES A YEAR",        "40 km UP"),
    ("chelyab",  "20 m",   "A HOUSE",          "house",     470e3,      "ABOUT ONCE A CENTURY",        "30 km UP, 40 km AWAY"),
    ("tunguska", "50 m",   "A JUMBO JET",      "plane",     12e6,       "EVERY FEW CENTURIES",         "8 km UP, 15 km AWAY"),
    ("city",     "140 m",  "A STADIUM",        "stadium",   tnt(140, 17e3), "ABOUT EVERY 20,000 YEARS", "40 km AWAY"),
    ("km1",      "1 km",   "A SMALL MOUNTAIN", "mountain",  tnt(1000),  "ABOUT EVERY 500,000 YEARS",   "150 km AWAY"),
    ("km10",     "10 km",  "MOUNT EVEREST",    "mountain",  1e14,       "ABOUT EVERY 100 MILLION YEARS", "2,000 km AWAY"),
    ("km100",    "100 km", "A SMALL COUNTRY",  "earth",     tnt(1e5),   "NOT FOR 3 BILLION YEARS",     "THE OTHER SIDE OF EARTH"),
]
SIZE_OF = {s[0]: s for s in SIZES}

# event times (seconds) used by scene + audio
EVENTS = dict(
    meteor1=27.0, meteor2=33.5, meteor3=41.0, meteor4=47.0,
    stone_in=66.0, stone_hit=69.4,
    fireball=101.0, burst=105.5, boom1=121.0,
    ch_streak=141.0, ch_flash=146.0, ch_shock=174.0,
    tg_streak=199.0, tg_flash=203.0, tg_heat=206.0, tg_shock=219.0,
    ct_streak=258.0, ct_hit=262.5, ct_quake=272.0, ct_shock=286.0,
    k1_glow=318.0, k1_hit=320.5, k1_quake=332.0, k1_ejecta=340.0, k1_shock=355.0,
    k10_glow=378.0, k10_quake=392.0, k10_ejecta=400.0, k10_fire=418.0, k10_dark=436.0,
    k100_glow=450.0, k100_wall=462.0, k100_hit=488.0,
)

CAPTIONS = [
    # intro
    (0.6, 3.6, "Something from space hits Earth every single day."),
    (4.2, 7.4, "Most of it is smaller than a grain of sand."),
    (8.2, 11.4, "So let's make it bigger. One size at a time."),
    (12.4, 15.6, "You stand on this street for every single one."),
    (16.6, 20.6, "Same speed every time: about twenty kilometres a second."),
    # pebble
    (22.8, 26.2, "A pebble the size of a pea."),
    (27.6, 31.0, "It never reaches you. It burns up 80 km above your head."),
    (32.0, 35.4, "That streak is the air around it, glowing."),
    (36.6, 40.6, "It carries the energy of a hand grenade, and it's gone in a second."),
    (42.0, 45.6, "Millions of these hit the atmosphere every day."),
    (47.6, 51.0, "You call them shooting stars."),
    (52.0, 56.6, "Make it ten times wider, and it gets a thousand times heavier."),
    # stone
    (59.0, 62.6, "Ten centimetres. About the size of a baseball."),
    (63.4, 66.0, "It glows high up, then goes dark."),
    (66.2, 69.3, "The air slows it down to the speed of a falling stone."),
    (70.0, 73.4, "In 1992, one did exactly this to a car in New York."),
    (74.4, 78.4, "It isn't hot when it lands. Space left it frozen inside."),
    (79.4, 83.4, "Pieces like this fall somewhere on Earth every day."),
    (84.6, 88.6, "Collectors will pay more than the car was worth."),
    (89.6, 94.4, "Ten times wider again. Now it weighs a tonne and a half."),
    # boulder
    (97.0, 100.4, "One metre. A washing machine made of rock."),
    (101.4, 104.6, "In daylight, it's brighter than the Moon."),
    (105.6, 108.8, "It explodes forty kilometres up."),
    (109.8, 113.8, "As much energy as 75 tonnes of TNT. Nothing reaches the ground but dust."),
    (115.0, 119.4, "The sound takes two minutes to get down to you."),
    (121.2, 124.6, "A deep boom. Car alarms. That's it."),
    (126.0, 130.0, "This happens several times every year. Usually over the ocean."),
    (131.0, 135.0, "Now twenty metres. It's not a rock anymore. It's a house."),
    # chelyabinsk
    (137.0, 140.6, "In 2013, one this size hit Chelyabinsk, Russia."),
    (141.6, 145.0, "It comes in at nineteen kilometres a second."),
    (146.2, 149.4, "For a moment, it's brighter than the Sun."),
    (150.4, 154.4, "You feel the heat on your face from forty kilometres away."),
    (155.6, 159.4, "It left a smoke trail across half the sky."),
    (160.4, 164.4, "Almost 500 kilotons. Thirty times Hiroshima."),
    (165.4, 169.6, "People came to the windows to look."),
    (170.6, 173.6, "That was a mistake."),
    (175.0, 178.6, "The shock wave arrives almost two minutes later."),
    (179.6, 183.6, "Windows blow in across the whole city. Fifteen hundred people hurt."),
    (184.6, 188.6, "Almost all of them by flying glass."),
    (189.6, 194.6, "If you ever see a flash like that: get away from the windows."),
    # tunguska
    (197.0, 200.6, "Fifty metres. About the size of a jumbo jet."),
    (201.6, 204.6, "In 1908, one exploded over Siberia."),
    (205.6, 209.0, "Twelve megatons. The heat is like standing next to an oven."),
    (210.0, 214.0, "Then the trees start to lean."),
    (219.6, 223.0, "The blast flattens everything in its path."),
    (224.0, 228.4, "In Siberia, eighty million trees went down."),
    (229.4, 233.4, "Over an area bigger than London."),
    (234.4, 238.4, "It happened over empty forest. Almost no one was there."),
    (239.4, 243.4, "Over a city, there would be nothing left standing."),
    (244.4, 248.4, "Something this size hits every few centuries."),
    (249.4, 253.6, "And it still doesn't reach the ground. The next one will."),
    # city killer
    (255.0, 258.6, "A hundred and forty metres. A football stadium."),
    (259.6, 262.4, "This one doesn't explode in the air."),
    (263.0, 266.6, "It hits the ground forty kilometres away."),
    (267.6, 271.0, "A hundred and fifty megatons."),
    (272.2, 275.6, "Ten seconds later, the ground jumps."),
    (276.6, 280.6, "The crater is three kilometres wide. A city could fit inside it."),
    (281.6, 285.2, "The mushroom cloud climbs higher than any jet can fly."),
    (286.6, 290.0, "Then the air arrives."),
    (291.6, 295.6, "Every roof on your street is gone."),
    (296.6, 300.6, "Astronomers call this size a 'city killer'."),
    (301.6, 305.6, "It happens about once every twenty thousand years."),
    (306.6, 312.6, "We track most of them. Not all."),
    # 1 km
    (315.0, 318.6, "One kilometre. A small mountain."),
    (319.6, 322.6, "It hits a hundred and fifty kilometres away."),
    (323.6, 327.6, "The fireball rises above the horizon. It keeps rising."),
    (328.6, 332.0, "Seventy-five thousand megatons."),
    (333.0, 336.6, "The ground shakes like a magnitude-seven earthquake."),
    (337.6, 341.6, "Then it starts to rain. Rocks."),
    (342.6, 346.6, "Molten pieces of the ground, thrown out and falling back."),
    (347.6, 351.6, "The crater is fifteen kilometres wide."),
    (352.6, 356.4, "The blast wave reaches you three minutes later."),
    (357.6, 361.6, "Dust spreads around the world. Summer gets colder for years."),
    (362.6, 366.6, "This happens roughly every half a million years."),
    (367.6, 372.6, "Now make it ten kilometres."),
    # 10 km
    (375.0, 378.6, "Ten kilometres. As tall as Mount Everest."),
    (379.6, 383.0, "Sixty-six million years ago, one hit Mexico."),
    (384.0, 388.0, "You're two thousand kilometres away. You don't see it hit."),
    (389.0, 391.6, "You see the sky light up."),
    (392.6, 396.0, "The earthquake is bigger than any ever recorded."),
    (397.0, 401.0, "Rock thrown into space starts coming back down. Everywhere."),
    (402.0, 406.0, "Thousands of burning streaks, all over the world."),
    (407.0, 411.0, "The sky turns orange. The air gets as hot as an oven."),
    (412.0, 416.0, "One hundred million megatons."),
    (418.0, 422.0, "Forests catch fire on every continent."),
    (423.0, 427.0, "Then the smoke and dust block the Sun."),
    (428.0, 432.0, "Darkness for months. Plants die. Then the animals that eat them."),
    (433.0, 437.0, "Three quarters of all species disappear. Including the dinosaurs."),
    (438.0, 444.4, "Now make it a hundred kilometres."),
    # 100 km
    (447.0, 450.6, "A hundred kilometres. The size of a small country."),
    (451.6, 455.6, "It hits on the other side of the planet."),
    (456.6, 460.6, "It doesn't make a crater. It makes a wound in the crust."),
    (461.6, 465.6, "A cloud of vaporised rock spreads around the whole Earth."),
    (466.6, 470.6, "It glows. It comes over the horizon toward you."),
    (471.6, 475.6, "Thousands of degrees. The sky itself becomes the heat source."),
    (476.6, 480.6, "Rivers boil. The top of the oceans boils."),
    (481.6, 486.6, "Nothing on the surface survives. Maybe something deep underground."),
    (488.4, 494.6, "Earth hasn't been hit this hard in more than three billion years."),
    # outro
    (497.0, 501.0, "And all of it at the same speed. Just a bigger rock."),
    (502.4, 507.4, "Size is everything."),
    (508.4, 513.6, "Next: what if the wind kept getting stronger?"),
]

HUD = dict(label="ASTEROID", right_label="ENERGY", right_sub="")

def act_at(t):
    for n, a, b in ACTS:
        if a <= t < b: return n
    return ACTS[-1][0]

def hud_state(t):
    act = act_at(t)
    order = [s[0] for s in SIZES]
    if act == "intro":
        nxt = SIZES[0]
        return dict(value="—", sub="PICK A SIZE", icon=None, icon_alpha=0.0, next_label="SIZE", next_value=nxt[1],
                    right_value="—", right_sub="AT 20 km/s")
    if act == "outro":
        s = SIZES[-1]
    else:
        s = SIZE_OF[act]
    i = order.index(s[0]); nxt = SIZES[i + 1] if i + 1 < len(SIZES) else None
    a0 = [a for n, a, b in ACTS if n == s[0]][0]
    al = max(0.0, min(1.0, (t - a0) / 0.4))
    return dict(value=s[1], sub=s[2], icon=s[3], icon_alpha=al,
                next_label="SIZE" if nxt else "THE END", next_value=nxt[1] if nxt else "of the line",
                right_value=fmt_tnt(s[4]), right_sub=s[5], extra_label="WHERE", extra_value=s[6].lower())

# no retime (scene time == video time)
def o(t): return t
def n(t): return t
EVENTS_OLD = EVENTS
