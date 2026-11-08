"""10 s infinite-zoom loop Short (Droste): you shrink into the tiny room on the rug, which has a tinier room on its rug...
Seamless: after 10 s you are in the same pose one room down (1/16 = four halvings). Teases the 'shrank' video."""
LOOP = dict(dir="shrink", pop="÷2", label="WHAT IF YOU NEVER STOPPED SHRINKING?", label_size=31, pop_every=2.5, pop_at=1.2,
            start=0.0, grade=True, text_y=1500, text_size=80,
            lines=[
    (0.0, 3.30, "Every few seconds, you're half as tall."),
    (3.33, 6.63, "There's always a smaller room."),
    (6.67, 10.0, "And you never reach the bottom, because..."),
])
