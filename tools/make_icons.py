"""White silhouette icons for the HUD comparison line (cairo). Output: tools/icons/<name>.png (240x150, transparent).
Run once locally; the PNGs are committed so the pod only needs PIL."""
import math, os, random
import cairo

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
W, H = 240, 150
WHITE = (1, 1, 1)

def canvas():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_source_rgba(1, 1, 1, 0.95); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    return s, c

def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()

def ell(c, x, y, rx, ry):
    c.save(); c.translate(x, y); c.scale(rx, ry); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()

def cut(c):  # draw in 'erase' mode
    c.set_operator(cairo.OPERATOR_CLEAR)

def paint(c):
    c.set_operator(cairo.OPERATOR_OVER); c.set_source_rgba(1, 1, 1, 0.95)

def person(c, x, y, s):
    c.arc(x, y - 62 * s, 13 * s, 0, 2 * math.pi); c.fill()
    rrect(c, x - 17 * s, y - 46 * s, 34 * s, 46 * s, 12 * s); c.fill()
    c.set_line_width(11 * s); c.move_to(x - 8 * s, y - 4 * s); c.line_to(x - 9 * s, y + 38 * s); c.stroke(); c.move_to(x + 8 * s, y - 4 * s); c.line_to(x + 9 * s, y + 38 * s); c.stroke()

def icons():
    D = {}
    def people(c): person(c, 95, 100, 1.0); person(c, 145, 100, 1.0)
    def bear(c):
        ell(c, 110, 85, 62, 34); c.fill(); c.arc(170, 70, 24, 0, 2 * math.pi); c.fill()
        c.arc(160, 48, 9, 0, 2 * math.pi); c.fill(); c.arc(181, 48, 9, 0, 2 * math.pi); c.fill(); ell(c, 192, 76, 12, 9); c.fill()
        for x in (66, 90, 130, 152): rrect(c, x - 9, 95, 18, 40, 6); c.fill()
    def bed(c):
        rrect(c, 30, 90, 180, 16, 4); c.fill(); rrect(c, 30, 50, 14, 80, 4); c.fill(); rrect(c, 196, 76, 14, 54, 4); c.fill()
        rrect(c, 44, 74, 152, 18, 8); c.fill(); rrect(c, 50, 58, 40, 16, 8); c.fill()
    def car(c):
        rrect(c, 25, 72, 190, 40, 14); c.fill()
        c.move_to(60, 74); c.line_to(85, 42); c.line_to(160, 42); c.line_to(185, 74); c.close_path(); c.fill()
        cut(c); c.move_to(76, 70); c.line_to(92, 50); c.line_to(118, 50); c.line_to(118, 70); c.close_path(); c.fill()
        c.move_to(126, 70); c.line_to(126, 50); c.line_to(155, 50); c.line_to(172, 70); c.close_path(); c.fill()
        c.arc(70, 114, 20, 0, 2 * math.pi); c.fill(); c.arc(172, 114, 20, 0, 2 * math.pi); c.fill(); paint(c)
        c.arc(70, 114, 14, 0, 2 * math.pi); c.fill(); c.arc(172, 114, 14, 0, 2 * math.pi); c.fill()
    def elephant(c):
        ell(c, 105, 75, 65, 40); c.fill(); c.arc(170, 62, 30, 0, 2 * math.pi); c.fill()
        for x in (62, 88, 122, 146): rrect(c, x - 11, 90, 22, 48, 6); c.fill()
        c.set_line_width(14); c.move_to(192, 70); c.curve_to(205, 95, 196, 118, 210, 132); c.stroke()
        cut(c); ell(c, 158, 64, 15, 22); c.fill(); paint(c); ell(c, 156, 64, 11, 18); c.set_source_rgba(1, 1, 1, 0.6); c.fill(); paint(c)
    def whale(c):
        c.move_to(30, 80); c.curve_to(35, 40, 150, 35, 195, 62); c.curve_to(212, 72, 210, 100, 190, 104); c.curve_to(130, 112, 60, 108, 30, 80); c.fill()
        c.move_to(36, 80); c.line_to(10, 56); c.line_to(18, 80); c.line_to(8, 102); c.close_path(); c.fill()
        cut(c); c.set_line_width(4); c.set_dash([8, 6]); c.move_to(110, 30); c.line_to(110, 120); c.stroke(); c.set_dash([]); paint(c)
    def concrete(c):
        rrect(c, 40, 40, 160, 90, 6); c.fill(); cut(c); c.set_line_width(5)
        c.move_to(110, 40); c.line_to(100, 70); c.line_to(122, 88); c.line_to(108, 130); c.stroke()
        c.move_to(100, 70); c.line_to(70, 82); c.stroke(); c.move_to(122, 88); c.line_to(160, 96); c.stroke(); paint(c)
    def granite(c):
        pts = [(40, 120), (60, 60), (100, 32), (150, 40), (196, 76), (204, 120)]
        c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.fill()
        cut(c); c.set_line_width(3)
        for a, b in (((60, 60), (110, 84)), ((100, 32), (110, 84)), ((150, 40), (110, 84)), ((196, 76), (150, 96)), ((110, 84), (150, 96)), ((150, 96), (204, 120)), ((110, 84), (90, 120))):
            c.move_to(*a); c.line_to(*b); c.stroke()
        paint(c)
    def ship(c):
        c.move_to(10, 92); c.line_to(232, 92); c.line_to(214, 120); c.line_to(26, 120); c.close_path(); c.fill()
        rrect(c, 6, 84, 230, 10, 2); c.fill(); rrect(c, 150, 50, 22, 36, 3); c.fill(); rrect(c, 158, 34, 6, 18, 2); c.fill()
    def pyramid(c):
        c.move_to(30, 128); c.line_to(120, 30); c.line_to(210, 128); c.close_path(); c.fill()
        cut(c); c.set_line_width(2.5)
        for i in range(1, 7):
            y = 30 + 98 * i / 7; hw = 90 * i / 7; c.move_to(120 - hw, y); c.line_to(120 + hw, y); c.stroke()
        paint(c)
    def gravity(c):
        c.arc(120, 75, 14, 0, 2 * math.pi); c.fill(); c.set_line_width(4)
        for r, al in ((32, 0.95), (50, 0.65), (68, 0.35)):
            c.set_source_rgba(1, 1, 1, al); c.set_dash([10, 7]); c.arc(120, 75, r, 0, 2 * math.pi); c.stroke()
        c.set_dash([]); paint(c); c.set_line_width(5)
        for a in (0, math.pi):
            x0 = 120 + math.cos(a) * 100; x1 = 120 + math.cos(a) * 76
            c.move_to(x0, 75); c.line_to(x1, 75); c.stroke(); d = -math.cos(a)
            c.move_to(x1, 75); c.line_to(x1 - d * 10, 67); c.stroke(); c.move_to(x1, 75); c.line_to(x1 - d * 10, 83); c.stroke()
    def asteroid(c):
        rr = random.Random(3); pts = []
        for i in range(13):
            a = i / 13 * 2 * math.pi; r = 52 + rr.uniform(-10, 10); pts.append((130 + math.cos(a) * r * 1.2, 75 + math.sin(a) * r))
        c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path(); c.fill()
        cut(c)
        for x, y, r in ((110, 60, 10), (150, 90, 13), (160, 55, 7)): c.arc(x, y, r, 0, 2 * math.pi); c.fill()
        paint(c); c.set_line_width(6); c.set_source_rgba(1, 1, 1, 0.5)
        for k in range(3): c.move_to(60 - k * 8, 108 + k * 8); c.line_to(16 - k * 8, 132 + k * 8); c.stroke()
        paint(c)
    def moon(c):
        c.arc(120, 75, 58, 0, 2 * math.pi); c.fill(); cut(c)
        for x, y, r in ((100, 55, 12), (140, 92, 16), (138, 48, 7), (95, 98, 8)): c.arc(x, y, r, 0, 2 * math.pi); c.fill()
        paint(c)
    def earth(c):
        c.arc(120, 75, 58, 0, 2 * math.pi); c.fill(); cut(c); c.set_line_width(3)
        for k in (-0.6, 0, 0.6): ell(c, 120, 75, 58 * math.cos(k * 1.2) if k else 1, 58); c.stroke()
        for y in (45, 75, 105): c.move_to(62, y); c.line_to(178, y); c.stroke()
        paint(c)
    def blackhole(c):
        c.set_line_width(14); ell(c, 120, 78, 104, 24); c.stroke()
        cut(c); c.arc(120, 72, 34, 0, 2 * math.pi); c.fill(); paint(c)
        c.set_line_width(14); c.save(); c.rectangle(0, 78, W, H); c.clip(); ell(c, 120, 78, 104, 24); c.stroke(); c.restore()
        c.set_line_width(4); c.arc(120, 72, 38, 0, 2 * math.pi); c.stroke()
    def sun(c):
        c.arc(120, 75, 36, 0, 2 * math.pi); c.fill(); c.set_line_width(7)
        for i in range(12):
            a = i / 12 * 2 * math.pi; c.move_to(120 + math.cos(a) * 46, 75 + math.sin(a) * 46); c.line_to(120 + math.cos(a) * 66, 75 + math.sin(a) * 66); c.stroke()
    def galaxy(c):
        rr = random.Random(5)
        for i in range(700):
            arm = i % 2; d = rr.random() ** 0.8; a = arm * math.pi + d * 5.2 + rr.gauss(0, 0.25)
            x, y = 120 + math.cos(a) * d * 100, 75 + math.sin(a) * d * 52
            c.arc(x, y, rr.uniform(0.8, 2.2), 0, 2 * math.pi); c.fill()
        c.arc(120, 75, 13, 0, 2 * math.pi); c.fill()
    for k, fn in dict(people=people, bear=bear, bed=bed, car=car, elephant=elephant, whale=whale, concrete=concrete, granite=granite,
                      ship=ship, pyramid=pyramid, gravity=gravity, asteroid=asteroid, moon=moon, earth=earth, blackhole=blackhole,
                      sun=sun, galaxy=galaxy).items():
        D[k] = fn
    # ---- 'lighter' comparison icons
    def child(c): person(c, 120, 108, 0.82)
    def cat(c):
        ell(c, 112, 92, 52, 26); c.fill(); c.arc(166, 70, 22, 0, 2 * math.pi); c.fill()
        c.move_to(150, 58); c.line_to(152, 34); c.line_to(166, 50); c.close_path(); c.fill()
        c.move_to(170, 50); c.line_to(184, 34); c.line_to(186, 60); c.close_path(); c.fill()
        for x in (76, 96, 128, 146): rrect(c, x - 7, 100, 14, 32, 5); c.fill()
        c.set_line_width(9); c.move_to(62, 88); c.curve_to(36, 80, 34, 50, 50, 38); c.stroke()
    def ball(c):
        c.arc(120, 75, 52, 0, 2 * math.pi); c.fill(); cut(c); c.set_line_width(5)
        c.move_to(68, 75); c.line_to(172, 75); c.stroke(); c.move_to(120, 23); c.line_to(120, 127); c.stroke()
        c.arc(54, 75, 40, -0.95, 0.95); c.stroke(); c.arc(186, 75, 40, math.pi - 0.95, math.pi + 0.95); c.stroke(); paint(c)
    def phone(c):
        rrect(c, 92, 14, 56, 122, 10); c.fill(); cut(c); rrect(c, 98, 26, 44, 96, 3); c.fill(); paint(c)
        c.set_source_rgba(1, 1, 1, 0.35); rrect(c, 98, 26, 44, 96, 3); c.fill(); paint(c)
    def balloon(c):
        ell(c, 120, 62, 38, 46); c.fill(); c.move_to(112, 106); c.line_to(128, 106); c.line_to(120, 114); c.close_path(); c.fill()
        c.set_line_width(3); c.move_to(120, 114); c.curve_to(110, 125, 130, 135, 120, 146); c.stroke()
    def paperclip(c):
        c.set_line_width(8)
        c.move_to(150, 40); c.line_to(150, 105); c.arc(130, 105, 20, 0, math.pi); c.line_to(110, 30); c.arc(124, 30, 14, math.pi, 0)
        c.line_to(138, 100); c.arc(130, 100, 8, 0, math.pi); c.line_to(122, 50); c.stroke()
    def rice(c):
        for x, y, a in ((80, 60, 0.4), (150, 62, -0.5), (115, 104, 0.15)):
            c.save(); c.translate(x, y); c.rotate(a); ell(c, 0, 0, 26, 10); c.fill(); c.restore()
    def sand(c):
        rr = random.Random(3)
        for i in range(7):
            x, y, r = 70 + i * 17 + rr.uniform(-6, 6), 85 + rr.uniform(-20, 20), rr.uniform(8, 14)
            c.move_to(x + r, y)
            for k in range(1, 7): a = k / 6 * 2 * math.pi; rk = r * rr.uniform(0.7, 1.1); c.line_to(x + math.cos(a) * rk, y + math.sin(a) * rk)
            c.close_path(); c.fill()
    def dust(c):
        rr = random.Random(8)
        for i in range(40): c.arc(120 + rr.gauss(0, 30), 75 + rr.gauss(0, 18), rr.uniform(1.5, 4.5), 0, 2 * math.pi); c.fill()
    def bacterium(c):
        rrect(c, 70, 52, 100, 46, 23); c.fill(); c.set_line_width(3)
        for k in range(5): c.move_to(70, 66 + k * 5); c.curve_to(50, 60 + k * 8, 40, 80 + k * 6, 22, 70 + k * 10); c.stroke()
    def virus(c):
        c.arc(120, 75, 34, 0, 2 * math.pi); c.fill(); c.set_line_width(5)
        for i in range(12):
            a = i / 12 * 2 * math.pi; c.move_to(120 + math.cos(a) * 34, 75 + math.sin(a) * 34); c.line_to(120 + math.cos(a) * 50, 75 + math.sin(a) * 50); c.stroke()
            c.arc(120 + math.cos(a) * 53, 75 + math.sin(a) * 53, 6, 0, 2 * math.pi); c.fill()
    def protein(c):
        rr = random.Random(2); x, y = 70, 70
        for i in range(26):
            c.arc(x, y, 9, 0, 2 * math.pi); c.fill(); x += rr.uniform(-14, 18); y += rr.uniform(-14, 14); x = min(175, max(65, x)); y = min(120, max(30, y))
    def proton(c):
        c.arc(120, 75, 44, 0, 2 * math.pi); c.fill(); cut(c)
        for x, y in ((104, 64), (136, 64), (120, 92)): c.arc(x, y, 13, 0, 2 * math.pi); c.fill()
        paint(c); c.set_source_rgba(1, 1, 1, 0.45)
        for x, y in ((104, 64), (136, 64), (120, 92)): c.arc(x, y, 13, 0, 2 * math.pi); c.fill()
        paint(c)
    def electron(c):
        c.set_line_width(4)
        for a in (0, math.pi / 3, -math.pi / 3):
            c.save(); c.translate(120, 75); c.rotate(a); ell(c, 0, 0, 66, 22); c.restore(); c.stroke()
        c.arc(120, 75, 8, 0, 2 * math.pi); c.fill(); c.arc(186, 75, 9, 0, 2 * math.pi); c.fill()
    def neutrino(c):
        c.arc(150, 75, 10, 0, 2 * math.pi); c.fill(); c.set_line_width(3)
        for k, w in ((0, 1.0), (1, 0.6), (2, 0.35)):
            c.set_source_rgba(1, 1, 1, 0.95 * w); c.move_to(136 - k * 28, 75); c.line_to(110 - k * 28, 75); c.stroke()
        paint(c)
    for k, fn in dict(child=child, cat=cat, ball=ball, phone=phone, balloon=balloon, paperclip=paperclip, rice=rice, sand=sand, dust=dust,
                      bacterium=bacterium, virus=virus, protein=protein, proton=proton, electron=electron, neutrino=neutrino).items():
        D[k] = fn
    # ---- 'asteroid' comparison icons
    def house(c):
        c.move_to(60, 78); c.line_to(120, 28); c.line_to(180, 78); c.close_path(); c.fill()
        c.rectangle(74, 76, 92, 58); c.fill(); cut(c); c.rectangle(110, 100, 20, 34); c.fill(); c.rectangle(84, 88, 18, 16); c.fill(); c.rectangle(140, 88, 18, 16); c.fill(); paint(c)
    def plane(c):
        ell(c, 120, 75, 78, 9); c.fill()
        c.move_to(110, 72); c.line_to(80, 30); c.line_to(96, 30); c.line_to(138, 72); c.close_path(); c.fill()
        c.move_to(110, 78); c.line_to(80, 120); c.line_to(96, 120); c.line_to(138, 78); c.close_path(); c.fill()
        c.move_to(52, 72); c.line_to(42, 50); c.line_to(52, 50); c.line_to(66, 72); c.close_path(); c.fill()
    def stadium(c):
        ell(c, 120, 80, 82, 40); c.fill(); cut(c); ell(c, 120, 80, 56, 24); c.fill(); paint(c)
        c.set_source_rgba(1, 1, 1, 0.5); ell(c, 120, 80, 50, 20); c.fill(); paint(c)
    def mountain(c):
        c.move_to(30, 130); c.line_to(100, 30); c.line_to(140, 86); c.line_to(160, 62); c.line_to(212, 130); c.close_path(); c.fill()
        cut(c); c.move_to(86, 50); c.line_to(100, 30); c.line_to(114, 50); c.line_to(106, 46); c.line_to(100, 54); c.line_to(94, 46); c.close_path(); c.fill(); paint(c)
    for k, fn in dict(house=house, plane=plane, stadium=stadium, mountain=mountain).items():
        D[k] = fn
    return D

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in icons().items():
        s, c = canvas(); fn(c); s.write_to_png(os.path.join(OUT, name + ".png"))
    print("icons:", len(icons()))
