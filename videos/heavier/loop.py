"""10 s seamless loop Short: the floor keeps giving way.
v2 (after 37.6% stayed / 62.3% swiped): starts mid-fall, question as the top hook, text on screen at frame 0, punchier grade.
The last line runs into the first, so the sentence only completes on the rewatch."""
LOOP = dict(dir="down", pop="×2", label="HOW DEEP WOULD YOU FALL?", label_size=52, pop_at=2.2, start=2.3, grade=True,
            mark=dict(t0=1.25, x=0.5, y=0.87, rx=0.30, ry=0.075, arrow=False), text_y=1190, text_size=84,
            lines=[
    (0.0, 3.30, "Your weight doubles every hour."),
    (3.33, 6.63, "No floor can hold you."),
    (6.67, 10.0, "So you keep falling, because..."),
])
