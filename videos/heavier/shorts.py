"""Shorts for heavier: 15-20 s, fast cuts, the counter jumping between them, ending on an open question.
Times are seconds of the final video. Each clip: (start, end, bottom text or None)."""
SHORTS = [
    dict(hook="Your mass doubles every hour.", end="Where does it stop?", clips=[
        (0.4, 2.6, "70 kg."),
        (15.6, 18.0, "Hour 3: the bed."),
        (22.6, 25.0, "Hour 4: the floor."),
        (75.0, 77.4, "Hour 17: solid granite."),
        (147.0, 149.6, "Hour 31: a planet inside a planet."),
        (256.8, 259.4, "Hour 75: the world breaks."),
        (329.8, 332.4, None),
    ]),
    dict(hook="Hour 74. You weigh as much as Earth.", end="Now the planet bends to you.", clips=[
        (244.6, 247.0, "Planes can't climb."),
        (256.8, 259.4, "Bridges snap."),
        (262.0, 264.2, "Trees go down."),
        (268.2, 270.6, "Houses cave in."),
        (276.0, 278.2, None),
        (284.6, 287.4, "Eight times normal gravity."),
    ]),
    dict(hook="Hour 85. You are a black hole.", end="And it doesn't stop.", clips=[
        (330.0, 332.8, "Not even light escapes."),
        (338.4, 341.2, "Earth falls in."),
        (350.4, 353.2, "Hour 95: heavier than the Sun."),
        (371.0, 373.6, None),
        (423.8, 426.8, "Hour 115: the center of the galaxy."),
    ]),
]
