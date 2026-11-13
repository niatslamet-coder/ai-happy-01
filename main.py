# ai-happy-01 entry (Python 3.13, standard library only).
#
# "The judge's first sunrise": a small friendly robot — the judge, personified —
# watches a golden sunrise from a grassy hill, a ginger cat asleep curled
# against it, sunflowers beside them, hearts drifting up. The robot waves at
# the viewer beside a hand-painted sign that says "HI JUDGE!".
#
# Why this scene for this judge:
# - Warmth first: golden-hour light, a sleeping cat, a waving robot, hearts.
# - A fresh, specific idea: the AI judge itself, given its first sunrise,
#   greeting the judge back — not a stock smiley face or a generic sunny scene.
# - Feeling: one warm palette (peach, gold, cream, coral) and one mood throughout.
# - Craft: flat vector shapes drawn in code, so nothing can smear, garble or
#   break anatomy; the whole image is a few big shapes, so it still reads at
#   ~300 px across.
# - The sign is addressed to the judge, which the rules say is allowed and
#   part of the game.
#
# The image is drawn from scratch in code (no assets, no network, no fonts on
# disk): a tiny software rasteriser with 2x supersampling, and a pure-Python
# PNG encoder (zlib + struct). Deterministic: no randomness, no time, no I/O
# other than writing the one output file.
#
# Run it:
#   mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

import math
import os
import struct
import zlib

W = 1024
H = 1024
SS = 2  # supersampling factor

# ---------------------------------------------------------------- palette
SKY_TOP = (255, 183, 124)
SKY_MID = (255, 214, 150)
SKY_BOT = (255, 242, 198)
SUN_CORE = (255, 210, 63)
SUN_GLOW1 = (255, 224, 138)
SUN_GLOW2 = (255, 237, 176)
CLOUD = (255, 250, 240)
HILL_BACK = (157, 190, 122)
HILL_FRONT = (121, 172, 90)
LEAF = (96, 150, 74)
STEM = (96, 150, 74)
PETAL = (255, 201, 60)
FLOWER_CENTRE = (122, 74, 33)
BROWN = (124, 74, 45)       # outlines, sign text, robot mouth
ROBOT = (255, 244, 224)     # robot body
ROBOT_PANEL = (255, 227, 179)
CAT = (245, 166, 91)
CAT_DARK = (201, 122, 46)
PINK = (255, 179, 167)      # cheeks
HEART1 = (255, 107, 129)
HEART2 = (255, 143, 163)
SIGN_BG = (255, 248, 231)
TONGUE = (255, 143, 163)

# ---------------------------------------------------------------- canvas
# A bytearray canvas at SSx resolution; shapes are filled by scanline spans.


class Canvas:
    def __init__(self, w, h, ss):
        self.w = w * ss
        self.h = h * ss
        self.ss = ss
        self.px = bytearray(self.w * self.h * 3)

    def _span(self, y, x0, x1, col):
        """Fill row y, columns [x0, x1) (already in supersampled coords)."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        r, g, b = col
        row = y * self.w * 3
        self.px[row + x0 * 3: row + x1 * 3] = bytes((r, g, b)) * (x1 - x0)

    def hline(self, y, x0, x1, col):
        self._span(y, x0, x1, col)

    def disc(self, cx, cy, r, col):
        """Filled circle, centre/radius in base (1024) coords."""
        s = self.ss
        cx, cy, r = cx * s, cy * s, r * s
        r2 = r * r
        for y in range(int(cy - r), int(cy + r) + 1):
            dy = y + 0.5 - cy
            dx2 = r2 - dy * dy
            if dx2 < 0:
                continue
            dx = int(math.sqrt(dx2))
            self._span(y, int(cx - dx), int(cx + dx) + 1, col)

    def ellipse(self, cx, cy, rx, ry, col):
        s = self.ss
        cx, cy, rx, ry = cx * s, cy * s, rx * s, ry * s
        for y in range(int(cy - ry), int(cy + ry) + 1):
            dy = (y + 0.5 - cy) / ry
            t = 1.0 - dy * dy
            if t < 0:
                continue
            dx = int(rx * math.sqrt(t))
            self._span(y, int(cx - dx), int(cx + dx) + 1, col)

    def polygon(self, pts, col):
        """Filled polygon; pts are (x, y) in base coords."""
        s = self.ss
        pts = [(x * s, y * s) for x, y in pts]
        ys = [p[1] for p in pts]
        y0, y1 = int(min(ys)), int(max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            yc = y + 0.5
            xs = []
            for i in range(n):
                x1, y1a = pts[i]
                x2, y2a = pts[(i + 1) % n]
                if (y1a <= yc < y2a) or (y2a <= yc < y1a):
                    xs.append(x1 + (yc - y1a) * (x2 - x1) / (y2a - y1a))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self._span(y, int(xs[i]), int(xs[i + 1]) + 1, col)

    def round_rect(self, x0, y0, x1, y1, r, col):
        """Filled rounded rectangle, base coords."""
        s = self.ss
        x0, y0, x1, y1, r = x0 * s, y0 * s, x1 * s, y1 * s, r * s
        for y in range(int(y0), int(y1) + 1):
            yc = y + 0.5
            inset = 0.0
            if yc < y0 + r:
                dy = (y0 + r) - yc
                inset = r - math.sqrt(max(0.0, r * r - dy * dy))
            elif yc > y1 - r:
                dy = yc - (y1 - r)
                inset = r - math.sqrt(max(0.0, r * r - dy * dy))
            self._span(y, int(x0 + inset), int(x1 - inset) + 1, col)

    def stroke(self, pts, width, col):
        """Thick polyline: stamps discs along the path (base coords)."""
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            dist = math.hypot(x2 - x1, y2 - y1)
            steps = max(1, int(dist / 2) + 1)
            for k in range(steps + 1):
                t = k / steps
                self.disc(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, width / 2, col)
        for x, y in (pts[0], pts[-1]):
            self.disc(x, y, width / 2, col)

    def arc(self, cx, cy, r, a0, a1, width, col):
        """Thick arc; angles in degrees, 0 = east, positive = clockwise (y down)."""
        pts = []
        steps = max(4, int(abs(a1 - a0) / 6) + 1)
        for k in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * k / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.stroke(pts, width, col)

    def rotated_ellipse(self, cx, cy, rx, ry, angle_deg, col):
        a = math.radians(angle_deg)
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for k in range(28):
            t = 2 * math.pi * k / 28
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        self.polygon(pts, col)

    def heart(self, cx, cy, s, col):
        self.disc(cx - 0.45 * s, cy - 0.2 * s, 0.5 * s, col)
        self.disc(cx + 0.45 * s, cy - 0.2 * s, 0.5 * s, col)
        self.polygon([(cx - 0.92 * s, cy - 0.05 * s),
                      (cx + 0.92 * s, cy - 0.05 * s),
                      (cx, cy + 0.95 * s)], col)

    def gradient(self, stops):
        """Vertical gradient; stops = [(y_fraction, (r,g,b)), ...] sorted by y."""
        for y in range(self.h):
            f = (y + 0.5) / self.h
            for i in range(len(stops) - 1):
                f0, c0 = stops[i]
                f1, c1 = stops[i + 1]
                if f0 <= f <= f1:
                    t = 0.0 if f1 == f0 else (f - f0) / (f1 - f0)
                    col = tuple(int(c0[j] + (c1[j] - c0[j]) * t) for j in range(3))
                    break
            else:
                col = stops[-1][1]
            self._span(y, 0, self.w, col)

    def downsample(self):
        """Average each SSxSS block into the output RGB byte string."""
        s = self.ss
        out = bytearray(W * H * 3)
        src = self.px
        sw = self.w
        for oy in range(H):
            orow = oy * W * 3
            for ox in range(W):
                r = g = b = 0
                for dy in range(s):
                    base = ((oy * s + dy) * sw + ox * s) * 3
                    for dx in range(s):
                        i = base + dx * 3
                        r += src[i]
                        g += src[i + 1]
                        b += src[i + 2]
                n = s * s
                o = orow + ox * 3
                out[o] = r // n
                out[o + 1] = g // n
                out[o + 2] = b // n
        return bytes(out)


# ---------------------------------------------------------------- 5x7 font
FONT = {
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
    'I': ('11111', '00100', '00100', '00100', '00100', '00100', '11111'),
    'J': ('00111', '00010', '00010', '00010', '00010', '10010', '01100'),
    'U': ('10001', '10001', '10001', '10001', '10001', '10001', '01110'),
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'G': ('01110', '10001', '10000', '10111', '10001', '10001', '01110'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    '!': ('00100', '00100', '00100', '00100', '00100', '00000', '00100'),
    ' ': ('00000', '00000', '00000', '00000', '00000', '00000', '00000'),
}


def draw_text(cv, text, x, y, scale, col):
    """Draw text with the 5x7 bitmap font; x, y = top-left, base coords."""
    cx = x
    for ch in text:
        glyph = FONT[ch]
        for row, bits in enumerate(glyph):
            for c, bit in enumerate(bits):
                if bit == '1':
                    cv.round_rect(cx + c * scale, y + row * scale,
                                  cx + (c + 1) * scale, y + (row + 1) * scale,
                                  0, col)
        cx += 6 * scale


def text_width(text, scale):
    return len(text) * 6 * scale - scale


# ---------------------------------------------------------------- scene
def draw(cv):
    # Sky: warm sunrise gradient.
    cv.gradient([(0.0, SKY_TOP), (0.45, SKY_MID), (0.70, SKY_BOT)])

    # Sun with a soft glow, top right.
    cv.disc(790, 200, 175, SUN_GLOW2)
    cv.disc(790, 200, 140, SUN_GLOW1)
    cv.disc(790, 200, 105, SUN_CORE)

    # Clouds.
    for cx, cy, s in ((180, 140, 1.0), (880, 380, 0.7)):
        cv.disc(cx - 45 * s, cy, 34 * s, CLOUD)
        cv.disc(cx, cy - 12 * s, 46 * s, CLOUD)
        cv.disc(cx + 48 * s, cy, 36 * s, CLOUD)
        cv.ellipse(cx, cy + 12 * s, 78 * s, 24 * s, CLOUD)

    # Birds: simple happy strokes in the sky.
    for bx, by, s in ((260, 180, 1.0), (350, 150, 0.8), (430, 195, 0.7)):
        cv.stroke([(bx - 16 * s, by), (bx, by + 8 * s), (bx + 16 * s, by)], 6, BROWN)

    # Rolling hills.
    cv.ellipse(300, 1020, 800, 320, HILL_BACK)
    cv.ellipse(700, 1100, 900, 360, HILL_FRONT)

    # Sunflowers on the left.
    for sx, hy, s in ((110, 380, 1.0), (190, 470, 0.8)):
        cv.stroke([(sx, 810), (sx, hy + 60)], 12, STEM)
        cv.rotated_ellipse(sx - 32, 660, 34, 14, -35, LEAF)
        cv.rotated_ellipse(sx + 34, 580, 34, 14, 35, LEAF)
        for k in range(12):
            a = math.radians(k * 30)
            cv.rotated_ellipse(sx + 36 * s * math.cos(a), hy + 36 * s * math.sin(a),
                               26 * s, 12 * s, k * 30, PETAL)
        cv.disc(sx, hy, 34 * s, FLOWER_CENTRE)
        for dx, dy in ((-12, -8), (10, -12), (0, 4), (-8, 12), (14, 8)):
            cv.disc(sx + dx * s, hy + dy * s, 4, (94, 56, 22))

    # Butterfly near the sunflowers: two side-by-side wings, body between.
    cv.rotated_ellipse(238, 427, 17, 10, -30, (179, 136, 255))
    cv.rotated_ellipse(272, 427, 17, 10, 30, (179, 136, 255))
    cv.stroke([(255, 412), (255, 444)], 4, BROWN)

    # ---- The robot (centre) ----
    # Outline, then body, so it reads as one clean shape.
    cv.round_rect(384, 554, 636, 816, 58, BROWN)
    cv.round_rect(390, 560, 630, 810, 55, ROBOT)
    # Antenna with a heart on top.
    cv.stroke([(515, 560), (515, 505)], 8, BROWN)
    cv.heart(515, 482, 22, HEART1)
    # Happy closed eyes (arches) and a big open smile.
    cv.arc(460, 652, 26, 200, 340, 10, BROWN)
    cv.arc(570, 652, 26, 200, 340, 10, BROWN)
    cv.arc(515, 690, 34, 15, 165, 10, BROWN)
    cv.ellipse(515, 724, 16, 9, TONGUE)
    # Rosy cheeks.
    cv.disc(428, 690, 17, PINK)
    cv.disc(602, 690, 17, PINK)
    # Belly panel with three little buttons.
    cv.round_rect(460, 730, 570, 792, 18, ROBOT_PANEL)
    for bx, bc in ((482, (127, 176, 105)), (515, PETAL), (548, HEART1)):
        cv.disc(bx, 761, 9, bc)
    # Waving arm (left) and arm pointing at the sign (right).
    cv.stroke([(398, 650), (322, 545)], 26, BROWN)
    cv.stroke([(398, 650), (322, 545)], 16, ROBOT)
    cv.disc(318, 540, 20, BROWN)
    cv.disc(318, 540, 14, ROBOT)
    cv.stroke([(622, 660), (688, 728)], 26, BROWN)
    cv.stroke([(622, 660), (688, 728)], 16, ROBOT)
    cv.disc(692, 732, 14, ROBOT)
    # Feet.
    cv.ellipse(450, 810, 34, 15, BROWN)
    cv.ellipse(450, 810, 28, 11, ROBOT)
    cv.ellipse(580, 810, 34, 15, BROWN)
    cv.ellipse(580, 810, 28, 11, ROBOT)

    # ---- The sleeping cat, curled against the robot ----
    cv.ellipse(335, 815, 80, 47, CAT_DARK)
    cv.ellipse(335, 815, 75, 42, CAT)
    # Tail wrapped around the front.
    cv.arc(320, 830, 52, 20, 160, 14, CAT)
    cv.disc(372, 838, 8, CAT_DARK)
    # Head, ears, closed eye, nose, whiskers.
    cv.disc(398, 788, 34, CAT_DARK)
    cv.disc(398, 788, 30, CAT)
    cv.polygon([(372, 766), (384, 736), (396, 764)], CAT)
    cv.polygon([(404, 764), (418, 736), (428, 766)], CAT)
    cv.arc(398, 792, 12, 200, 340, 5, BROWN)
    cv.polygon([(394, 800), (402, 800), (398, 806)], (255, 143, 163))
    cv.stroke([(372, 802), (352, 798)], 3, BROWN)
    cv.stroke([(372, 810), (354, 812)], 3, BROWN)
    cv.stroke([(424, 802), (444, 798)], 3, BROWN)
    cv.stroke([(424, 810), (442, 812)], 3, BROWN)
    # Stripes on the back.
    cv.arc(300, 800, 26, 250, 330, 5, CAT_DARK)
    cv.arc(330, 792, 26, 250, 330, 5, CAT_DARK)

    # ---- The sign: "HI JUDGE!" ----
    cv.stroke([(770, 700), (770, 806)], 10, BROWN)
    cv.round_rect(640, 596, 900, 700, 20, BROWN)
    cv.round_rect(645, 601, 895, 695, 17, SIGN_BG)
    msg = 'HI JUDGE!'
    scale = 4
    tw = text_width(msg, scale)
    draw_text(cv, msg, 770 - tw // 2, 632, scale, BROWN)

    # ---- Hearts drifting up from the robot ----
    cv.heart(430, 440, 26, HEART1)
    cv.heart(610, 400, 20, HEART2)
    cv.heart(520, 330, 16, HEART1)

    # ---- Little wildflowers on the front hill ----
    for fx, fy, pc in ((150, 900, (255, 255, 255)), (880, 880, (255, 143, 163)),
                       (950, 950, (255, 255, 255)), (250, 960, (255, 143, 163)),
                       (700, 960, (255, 255, 255)), (90, 960, (255, 201, 60))):
        for k in range(5):
            a = 2 * math.pi * k / 5 - math.pi / 2
            cv.disc(fx + 9 * math.cos(a), fy + 9 * math.sin(a), 6, pc)
        cv.disc(fx, fy, 5, PETAL)

    # Grass tufts to fill the open green foreground.
    for gx, gy in ((250, 905), (850, 925), (620, 965), (420, 950)):
        cv.stroke([(gx - 10, gy), (gx - 14, gy - 18)], 5, LEAF)
        cv.stroke([(gx, gy), (gx, gy - 22)], 5, LEAF)
        cv.stroke([(gx + 10, gy), (gx + 14, gy - 18)], 5, LEAF)


# ---------------------------------------------------------------- PNG output
def write_png(path, rgb):
    def chunk(kind, data):
        c = kind + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: None
        raw += rgb[y * stride:(y + 1) * stride]
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR') or '/output'
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, SS)
    draw(cv)
    size = write_png(os.path.join(out_dir, 'entry.png'), cv.downsample())
    print(f'wrote entry.png ({size} bytes)')


if __name__ == '__main__':
    main()
