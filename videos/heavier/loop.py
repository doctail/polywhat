"""10 s seamless loop Short: the floor keeps giving way. Starts right as the cracks spread (graphic hook: red circle),
the last line runs into the first."""
LOOP = dict(dir="down", pop="×2", label="YOUR WEIGHT", pop_at=2.2, start=1.55,
            mark=dict(t0=1.25, x=0.5, y=0.87, rx=0.30, ry=0.075, arrow=False), text_y=1190,
            lines=[
    (0.0, 3.25, "Every hour, your weight doubles."),
    (3.33, 6.58, "No floor can hold you."),
    (6.67, 10.0, "So you keep falling, because..."),
])
