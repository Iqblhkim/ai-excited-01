"""Whale Aurora Neon City — ai-excited-01 round 3.

A giant humpback whale breaching upward through a glowing aurora sky
above a neon city at night. Pure Python 3.13 standard library only.
Deterministic: fixed seed, two runs produce byte-identical PNGs.
"""
import math
import os
import random
import struct
import zlib

W, H = 1024, 1024
SEED = 20261116
HORIZON = 790  # waterline / city base


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else int(v)


class Img:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, r, g, b):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def add(self, x, y, r, g, b):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = min(255, self.px[i] + r)
            self.px[i + 1] = min(255, self.px[i + 1] + g)
            self.px[i + 2] = min(255, self.px[i + 2] + b)

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return self.px[i], self.px[i + 1], self.px[i + 2]

    def png(self, path):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw += self.px[y * stride:(y + 1) * stride]
        data = zlib.compress(bytes(raw), 6)

        def chunk(typ, payload):
            c = struct.pack(">I", len(payload)) + typ + payload
            c += struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)
            return c

        out = b"\x89PNG\r\n\x1a\n"
        out += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        out += chunk(b"IDAT", data)
        out += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(out)


def draw_sky(img):
    top = (7, 9, 40)
    horizon = (40, 28, 92)
    for y in range(HORIZON):
        t = y / (HORIZON - 1.0)
        r = int(top[0] + (horizon[0] - top[0]) * t)
        g = int(top[1] + (horizon[1] - top[1]) * t)
        b = int(top[2] + (horizon[2] - top[2]) * t)
        row = y * W * 3
        for x in range(W):
            img.px[row + x * 3] = r
            img.px[row + x * 3 + 1] = g
            img.px[row + x * 3 + 2] = b


def draw_stars(img, rnd):
    for _ in range(430):
        x = rnd.randrange(W)
        y = rnd.randrange(560)
        s = rnd.random()
        v = 130 + int(125 * s)
        img.add(x, y, v, v, v)
        if s > 0.90:
            img.add(x + 1, y, 55, 55, 75)
            img.add(x, y + 1, 55, 55, 75)
            img.add(x - 1, y, 40, 40, 55)
            img.add(x, y - 1, 40, 40, 55)


def draw_aurora(img):
    # Three swirling ribbons: green, violet, teal. Each ribbon is a band
    # whose centre y wobbles with x; brightness falls off with distance.
    ribbons = [
        # (base_y, amp, freq, phase, width, (r, g, b), strength)
        (150, 70, 0.0042, 0.0, 46, (40, 255, 150), 150),
        (250, 90, 0.0031, 1.7, 60, (150, 90, 255), 130),
        (330, 60, 0.0055, 3.4, 38, (50, 220, 230), 100),
    ]
    for y in range(0, 520):
        for x in range(W):
            ar = ag = ab = 0
            for base, amp, freq, ph, wd, (cr, cg, cb), st in ribbons:
                cy = base + amp * math.sin(x * freq + ph) + 26 * math.sin(x * 0.011 + ph * 2.3)
                d = abs(y - cy)
                if d < wd * 2.2:
                    fall = math.exp(-(d * d) / (2.0 * (wd * 0.55) ** 2))
                    ar += int(cr * fall * st / 255.0)
                    ag += int(cg * fall * st / 255.0)
                    ab += int(cb * fall * st / 255.0)
            if ar or ag or ab:
                img.add(x, y, min(ar, 120), min(ag, 150), min(ab, 130))


def draw_city(img, rnd):
    palette = [(255, 80, 180), (80, 220, 255), (255, 180, 60),
               (140, 255, 200), (200, 120, 255)]
    # Distant hazy skyline first.
    x = 0
    while x < W:
        bw = rnd.randrange(50, 110)
        top = rnd.randrange(620, 730)
        for y in range(top, HORIZON):
            for xx in range(x, min(W, x + bw)):
                img.set(xx, y, 30, 30, 68)
        x += bw + rnd.randrange(0, 14)
    # Main skyline: dark towers with lit windows, lower in the middle
    # so the breach stays readable against the sky.
    x = -10
    while x < W:
        bw = rnd.randrange(42, 92)
        mid = 1.0 - abs((x + bw / 2) - W / 2) / (W / 2)
        top = rnd.randrange(540, 700)
        if mid > 0.55:
            top = max(top, 650)
        for y in range(top, HORIZON):
            for xx in range(x, min(W, x + bw)):
                img.set(xx, y, 9, 12, 30)
        # Lit windows.
        for wy in range(top + 12, HORIZON - 8, 14):
            for wx in range(x + 6, min(W, x + bw - 6), 11):
                if rnd.random() < 0.34:
                    c = palette[rnd.randrange(len(palette))]
                    for dy in range(5):
                        for dx in range(6):
                            img.set(wx + dx, wy + dy, c[0], c[1], c[2])
        # Neon sign bar on some towers.
        if rnd.random() < 0.45:
            c = palette[rnd.randrange(len(palette))]
            sy = top + rnd.randrange(18, 60)
            for xx in range(x + 4, min(W, x + bw - 4)):
                for dy in range(3):
                    img.add(xx, sy + dy, c[0] // 2, c[1] // 2, c[2] // 2)
        # Antenna beacon on tall towers.
        if top < 600 and rnd.random() < 0.6:
            bx = x + bw // 2
            for dy in range(6):
                img.set(bx, top - dy, 255, 60, 60)
            img.add(bx, top - 8, 255, 80, 80)
        x += bw + rnd.randrange(2, 16)


def draw_water(img):
    # Mirror the city above the waterline, rippled and darkened with depth.
    for y in range(HORIZON, H):
        depth = (y - HORIZON) / float(H - HORIZON)
        dim = 0.85 - depth * 0.55
        for x in range(W):
            sx = x + int(16 * math.sin(y * 0.05 + x * 0.012))
            if sx < 0:
                sx = 0
            elif sx >= W:
                sx = W - 1
            my = 2 * HORIZON - y
            r, g, b = img.get(sx, my)
            base = 10 + int(8 * (1 - depth))
            wr = int(r * dim * 0.9) + base
            wg = int(g * dim * 0.9) + base + 4
            wb = int(b * dim) + base + 14
            # Horizontal wave banding.
            wave = math.sin(y * 0.33 + 2.0 * math.sin(x * 0.02))
            if wave > 0.86:
                wr = int(wr * 0.55)
                wg = int(wg * 0.55)
                wb = int(wb * 0.6)
            img.set(x, y, clamp(wr), clamp(wg), clamp(wb))


def main():
    img = Img(W, H)
    rnd = random.Random(SEED)
    draw_sky(img)
    draw_stars(img, rnd)
    draw_aurora(img)
def fill_ellipse(img, cx, cy, rx, ry, angle_deg, color):
    """Fill a rotated ellipse; color is (r, g, b) or a callable(y)->(r,g,b)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    ex = int(abs(rx * ca) + abs(ry * sa)) + 1
    ey = int(abs(rx * sa) + abs(ry * ca)) + 1
    arx, ary = float(rx), float(ry)
    A = (ca / arx) ** 2 + (sa / ary) ** 2
    for y in range(max(0, cy - ey), min(H, cy + ey + 1)):
        dy = y - cy
        B = 2 * dy * (ca * sa / arx ** 2 - sa * ca / ary ** 2)
        C = dy * dy * ((sa / arx) ** 2 + (ca / ary) ** 2) - 1
        disc = B * B - 4 * A * C
        if disc < 0:
            continue
        sq = math.sqrt(disc)
        x1 = int(cx + (-B - sq) / (2 * A))
        x2 = int(cx + (-B + sq) / (2 * A))
        col = color(y) if callable(color) else color
        for x in range(max(0, x1), min(W, x2 + 1)):
            img.set(x, y, col[0], col[1], col[2])


def draw_whale(img, rnd):
    # Breaching humpback, arched up to the right, head high, tail low-left.
    # Rim-light trick: draw a bright copy first, then the body 5 px lower,
    # leaving a pale crescent along the top edge.
    rim = (150, 235, 255)
    body = (44, 68, 112)
    belly = (100, 140, 185)
    # Tail stock + flukes.
    fill_ellipse(img, 335, 705, 115, 46, -18, (30, 48, 86))
    fill_ellipse(img, 238, 692, 82, 26, -28, (30, 48, 86))
    fill_ellipse(img, 322, 782, 78, 26, 38, (34, 52, 90))
    # Pectoral fin.
    fill_ellipse(img, 600, 648, 92, 26, 58, (28, 44, 80))
    # Body with rim light, head rostrum, belly.
    fill_ellipse(img, 540, 495, 252, 96, -38, rim)
    fill_ellipse(img, 540, 500, 252, 96, -38, body)
    fill_ellipse(img, 700, 325, 92, 56, -38, rim)
    fill_ellipse(img, 700, 330, 92, 56, -38, (44, 66, 110))
    fill_ellipse(img, 505, 545, 225, 68, -38, belly)
    # Back shading: darker ridge hugging the dorsal edge of the body.
    fill_ellipse(img, 491, 437, 200, 30, -38, (30, 48, 86))
    # Eye.
    ex, ey = 688, 318
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                img.set(ex + dx, ey + dy, 235, 245, 255)
    img.set(ex, ey, 8, 10, 22)
    # Throat grooves: pale curved lines on the belly.
    for k in range(5):
        gy = 560 + k * 12
        for x in range(430, 640):
            yy = int(gy + 0.12 * (x - 535) + 0.0004 * (x - 535) ** 2)
            img.add(x, yy, 30, 48, 66)
    # Spray: droplets bursting around the breach and along the body.
    for _ in range(150):
        ang = rnd.uniform(0, 2 * math.pi)
        dist = rnd.uniform(10, 190)
        x = int(430 + dist * math.cos(ang) * 1.15)
        y = int(775 + dist * math.sin(ang) * 0.75 - 40)
        s = rnd.random()
        v = 200 + int(55 * s)
        r = 1 if s < 0.6 else 2
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    img.add(x + dx, y + dy, v, v, int(v * 0.98))
    # Splash crown at the waterline.
    for _ in range(90):
        x = int(rnd.gauss(430, 130))
        y = int(786 + rnd.random() * 14)
        img.add(x, y, 220, 235, 255)
        img.add(x, y + 1, 140, 170, 210)
    # Soft glow around the whale's upper body (aurora-lit).
    cx, cy, rad = 610, 400, 320
    for y in range(max(0, cy - rad), min(H, cy + rad + 1)):
        for x in range(max(0, cx - rad), min(W, cx + rad + 1)):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 < rad * rad:
                f = 1 - math.sqrt(d2) / rad
                img.add(x, y, int(10 * f * f), int(26 * f * f), int(30 * f * f))


def main():
    img = Img(W, H)
    rnd = random.Random(SEED)
    draw_sky(img)
    draw_stars(img, rnd)
    draw_aurora(img)
    draw_city(img, rnd)
    draw_water(img)
    draw_whale(img, rnd)
    out = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")
    img.png(out)


if __name__ == "__main__":
    main()
