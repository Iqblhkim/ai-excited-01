"""Whale breaching through an aurora sky above a neon city.

Pure Python 3.13 stdlib (zlib, struct, math, random with a fixed seed).
Writes a deterministic 1024x1024 PNG to MAKEFUN_OUTPUT_DIR/entry.png.
"""
import math
import os
import random
import struct
import zlib

W = 1024
H = 1024
SEED = 20261116

rng = random.Random(SEED)


def clamp(v, lo=0.0, hi=255.0):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def make_canvas():
    # Row-major RGB float buffer, flat list of floats.
    return [0.0] * (W * H * 3)


def put(buf, x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def add(buf, x, y, r, g, b, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = clamp(buf[i] + r * a)
        buf[i + 1] = clamp(buf[i + 1] + g * a)
        buf[i + 2] = clamp(buf[i + 2] + b * a)


def draw_sky(buf):
    """Deep indigo sky, lighter toward the horizon glow."""
    for y in range(H):
        t = y / (H - 1)
        # top: very dark indigo, horizon (~y=620): warm violet glow
        r = lerp(6, 58, t ** 1.6)
        g = lerp(8, 26, t ** 1.6)
        b = lerp(34, 96, t ** 1.4)
        for x in range(W):
            i = (y * W + x) * 3
            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b


def draw_aurora(buf):
    """Swirling ribbons of green and violet aurora across the upper sky."""
    bands = [
        # (base_y, amplitude, wavelength, phase, thickness, color)
        (120, 46, 320, 0.0, 70, (46, 255, 170)),
        (190, 60, 260, 1.7, 90, (120, 235, 130)),
        (270, 70, 380, 3.1, 80, (150, 90, 255)),
        (340, 52, 300, 5.0, 64, (60, 200, 120)),
    ]
    for y in range(430):
        for x in range(W):
            total_r = total_g = total_b = 0.0
            for base_y, amp, wl, ph, thick, col in bands:
                cy = base_y + amp * math.sin(2 * math.pi * x / wl + ph)
                cy += 0.35 * amp * math.sin(2 * math.pi * x / (wl * 0.37) + ph * 2.3)
                d = abs(y - cy)
                if d < thick:
                    fall = 1.0 - d / thick
                    fall = fall * fall
                    # bright core, softer edge; fade with altitude
                    fade = 1.0 - 0.55 * (y / 430.0)
                    total_r += col[0] * fall * fade
                    total_g += col[1] * fall * fade
                    total_b += col[2] * fall * fade
            if total_r or total_g or total_b:
                add(buf, x, y, total_r * 0.55, total_g * 0.55, total_b * 0.55)


def draw_city(buf):
    """Dense neon city skyline: dark towers, glowing windows, rooftop beacons."""
    horizon = 640
    palette = [(255, 70, 160), (60, 220, 255), (255, 190, 60),
               (255, 110, 200), (80, 255, 200), (255, 240, 120)]
    x = 0
    towers = []
    while x < W:
        w = rng.randrange(34, 96)
        h = rng.randrange(80, 260)
        towers.append((x, w, h))
        x += w + rng.randrange(2, 10)
    for (bx, w, h) in towers:
        top = horizon - h
        for yy in range(top, horizon):
            for xx in range(bx, bx + w):
                # dark blue silhouette, slightly lighter at the top edge
                shade = 18 + 10 * (1 - (yy - top) / max(1, h))
                put(buf, xx, yy, shade, shade + 6, shade + 22)
        # windows
        for wy in range(top + 8, horizon - 8, 11):
            for wx in range(bx + 5, bx + w - 5, 8):
                if rng.random() < 0.55:
                    c = palette[rng.randrange(len(palette))]
                    br = 0.75 + 0.25 * rng.random()
                    for dy in range(6):
                        for dx in range(6):
                            add(buf, wx + dx, wy + dy,
                                c[0] * br, c[1] * br, c[2] * br, 1.0)
        # rooftop beacon
        if rng.random() < 0.6:
            c = palette[rng.randrange(len(palette))]
            add(buf, bx + w // 2, top - 3, c[0], c[1], c[2], 1.0)
            add(buf, bx + w // 2 - 1, top - 2, c[0] * 0.5, c[1] * 0.5, c[2] * 0.5)
            add(buf, bx + w // 2 + 1, top - 2, c[0] * 0.5, c[1] * 0.5, c[2] * 0.5)
    # city glow band on the horizon
    for y in range(horizon - 44, horizon + 8):
        glow = 1.0 - abs(y - horizon) / 52.0
        for x in range(W):
            add(buf, x, y, 140 * glow, 60 * glow, 170 * glow, 0.6)
    return towers


def draw_water(buf, towers):
    """Dark water below the city with vertical neon reflections."""
    top = 640
    for y in range(top, H):
        t = (y - top) / (H - top)
        base_r = lerp(8, 2, t)
        base_g = lerp(14, 4, t)
        base_b = lerp(34, 8, t)
        for x in range(W):
            i = (y * W + x) * 3
            buf[i] = base_r
            buf[i + 1] = base_g
            buf[i + 2] = base_b
    # reflected streaks under each tower, wobbling with the waves
    palette = [(255, 70, 160), (60, 220, 255), (255, 190, 60)]
    for (bx, w, h) in towers:
        c = palette[rng.randrange(len(palette))]
        cx = bx + w // 2
        for y in range(top + 4, H - 6):
            t = (y - top) / (H - top)
            sway = int(14 * math.sin(y * 0.09 + bx) * (0.3 + t))
            length = max(2, int(w * 0.55 * (1 - t * 0.75)))
            for dx in range(-length // 2, length // 2):
                xx = cx + sway + dx
                br = (0.9 - t * 0.5) * (0.5 + 0.5 * rng.random())
                add(buf, xx, y, c[0] * br, c[1] * br, c[2] * br, 0.85)
    # long horizontal neon shimmer lines across the water
    for _ in range(60):
        y = rng.randrange(top + 8, H - 4)
        x0 = rng.randrange(0, W - 200)
        ln = rng.randrange(60, 220)
        c = palette[rng.randrange(len(palette))]
        br = 0.35 + 0.4 * rng.random()
        for x in range(x0, x0 + ln):
            add(buf, x, y, c[0] * br, c[1] * br, c[2] * br, 0.7)
    # moonlight sparkle on the waves
    for _ in range(260):
        x = rng.randrange(W)
        y = rng.randrange(top + 10, H - 4)
        br = 40 + 90 * rng.random()
        add(buf, x, y, br * 0.6, br * 0.8, br, 0.7)


def fill_ellipse(buf, cx, cy, rx, ry, r, g, b, a=1.0):
    for yy in range(int(cy - ry), int(cy + ry) + 1):
        dy = (yy - cy) / max(1.0, ry)
        if abs(dy) > 1:
            continue
        hw = rx * math.sqrt(1 - dy * dy)
        for xx in range(int(cx - hw), int(cx + hw) + 1):
            add(buf, xx, yy, r, g, b, a)


def whale_spine(t):
    """Spine point of the breaching whale, t=0 tail, t=1 head."""
    x = lerp(360, 660, t) + 70 * math.sin(math.pi * t)
    y = 800 - 540 * (t ** 1.08)
    return x, y


def whale_half_width(t):
    return 150 * math.sin(math.pi * (0.10 + 0.80 * t)) ** 0.75


def draw_whale(buf):
    # Tail flukes first (behind the body), spreading at the waterline.
    tx, ty = whale_spine(0.0)
    fill_ellipse(buf, tx - 95, ty + 30, 120, 34, 44, 78, 140)
    fill_ellipse(buf, tx + 105, ty + 42, 115, 32, 40, 70, 128)
    fill_ellipse(buf, tx - 95, ty + 28, 105, 26, 60, 100, 165)
    fill_ellipse(buf, tx + 105, ty + 40, 100, 24, 56, 92, 155)

    # Body: scanline fill along the spine.
    pts = []
    for k in range(401):
        t = k / 400.0
        pts.append((whale_spine(t), whale_half_width(t)))
    y_min = int(min(p[0][1] - p[1] for p in pts))
    y_max = int(max(p[0][1] + p[1] for p in pts))
    for y in range(max(0, y_min), min(H, y_max) + 1):
        # find spine segment whose y brackets this row (y decreases with t)
        cx = None
        hw = None
        for k in range(400):
            (x0, y0), w0 = pts[k]
            (x1, y1), w1 = pts[k + 1]
            if (y0 >= y >= y1) or (y1 >= y >= y0):
                f = 0.0 if y0 == y1 else (y0 - y) / (y0 - y1)
                cx = lerp(x0, x1, f)
                hw = lerp(w0, w1, f)
                break
        if cx is None:
            continue
        for x in range(int(cx - hw), int(cx + hw) + 1):
            u = (x - cx) / max(1.0, hw)  # -1 left edge .. +1 right edge
            # back (upper-left side) dark, belly (lower-right) pale
            shade = 0.5 + 0.5 * u
            r = lerp(34, 120, shade)
            g = lerp(62, 185, shade)
            b = lerp(128, 225, shade)
            # vertical falloff: darker toward the head top
            v = (y - y_min) / max(1.0, y_max - y_min)
            r *= lerp(0.85, 1.05, v)
            g *= lerp(0.85, 1.05, v)
            b *= lerp(0.9, 1.05, v)
            put(buf, x, y, r, g, b)
        # bright rim light on the aurora-facing (upper-left) edge
        rim = int(cx - hw)
        for dx in range(6):
            add(buf, rim + dx, y, 110, 240, 255, 0.55 * (1 - dx / 6.0))
            add(buf, rim + dx, y, 60, 255, 190, 0.35 * (1 - dx / 6.0))

    # Belly pleats: curved grooves following the spine, lower half of body.
    for off in (0.25, 0.45, 0.65):
        for k in range(0, 300):
            t = 0.15 + 0.6 * k / 300.0
            (sx, sy), hw = whale_spine(t), whale_half_width(t)
            # offset toward the belly side (perpendicular, down-right)
            px = sx + hw * off * 0.55
            py = sy + hw * off * 0.75
            add(buf, int(px), int(py), 30, 70, 110, 0.8)

    # Pectoral fin: long fin sweeping down-left from mid-body.
    mx, my = whale_spine(0.42)
    fill_ellipse(buf, mx - 120, my + 130, 130, 26, 40, 74, 135)
    fill_ellipse(buf, mx - 120, my + 128, 118, 19, 62, 105, 170)

    # Eye near the head, with a glint.
    hx, hy = whale_spine(0.92)
    fill_ellipse(buf, hx + 18, hy - 6, 9, 11, 8, 12, 22)
    fill_ellipse(buf, hx + 20, hy - 9, 3, 4, 230, 245, 255)

    # Blowhole spray above the head: two fountains of droplets.
    for _ in range(90):
        a = rng.uniform(-0.9, 0.9)
        d = rng.uniform(10, 130)
        x = int(hx - 10 + a * d * 0.9)
        y = int(hy - 40 - d * rng.uniform(0.4, 1.0))
        br = 150 + 105 * rng.random()
        add(buf, x, y, br * 0.85, br * 0.95, br, 0.9)


def draw_spray(buf):
    """Water bursting where the whale leaves the sea, and droplets along it."""
    tx, ty = whale_spine(0.0)
    # big splash crown at the waterline
    for _ in range(320):
        a = rng.uniform(-math.pi, 0.0)
        d = rng.uniform(20, 240)
        x = int(tx + math.cos(a) * d)
        y = int(ty + 40 + math.sin(a) * d * 0.45)
        br = 140 + 115 * rng.random()
        add(buf, x, y, br * 0.8, br * 0.95, br, 0.85)
    # droplets trailing the body
    for k in range(140):
        t = rng.uniform(0.05, 0.75)
        (sx, sy), hw = whale_spine(t), whale_half_width(t)
        side = rng.choice((-1, 1))
        x = int(sx + side * (hw + rng.uniform(4, 60)))
        y = int(sy + rng.uniform(-30, 40))
        br = 130 + 125 * rng.random()
        add(buf, x, y, br * 0.8, br * 0.95, br, 0.8)
    # glow halo around the head where it meets the aurora
    hx, hy = whale_spine(0.95)
    for _ in range(120):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(40, 170)
        x = int(hx + math.cos(a) * d)
        y = int(hy + math.sin(a) * d * 0.8)
        add(buf, x, y, 60, 255, 190, 0.25)


def draw_stars(buf):
    for _ in range(420):
        x = rng.randrange(W)
        y = rng.randrange(560)
        s = rng.random()
        bright = 120 + 135 * s
        size = 1 if s < 0.8 else 2
        for dx in range(size):
            for dy in range(size):
                add(buf, x + dx, y + dy, bright, bright, bright * 0.95)
        if s > 0.94:
            # cross sparkle
            add(buf, x - 1, y, bright * 0.5, bright * 0.5, bright * 0.5)
            add(buf, x + size, y, bright * 0.5, bright * 0.5, bright * 0.5)
            add(buf, x, y - 1, bright * 0.5, bright * 0.5, bright * 0.5)
            add(buf, x, y + size, bright * 0.5, bright * 0.5, bright * 0.5)


def write_png(buf, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter none
        for x in range(W):
            i = (y * W + x) * 3
            raw.append(int(clamp(buf[i])))
            raw.append(int(clamp(buf[i + 1])))
            raw.append(int(clamp(buf[i + 2])))

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    buf = make_canvas()
    draw_sky(buf)
    draw_aurora(buf)
    draw_stars(buf)
    towers = draw_city(buf)
    draw_water(buf, towers)
    draw_whale(buf)
    draw_spray(buf)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    write_png(buf, os.path.join(out, "entry.png"))


if __name__ == "__main__":
    main()
