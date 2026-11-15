#!/usr/bin/env python3
"""Whale in an aurora sky over a neon city.

Procedural 1024x1024 PNG, pure Python standard library only (zlib + struct
for the PNG encoder). Deterministic: a fixed seed drives every random choice,
so two runs produce byte-identical output. No network access.

Concept: a giant whale swims through a night sky lit by aurora ribbons above
a neon city at dusk -- the surprise of scale (a whale in the sky, not the
sea), awe, and momentum from the diagonal arc of the whale's body.
"""

import math
import os
import random
import struct
import time
import zlib

W = 1024
H = 1024

SEED = 20261116

# ---------------------------------------------------------------- buffer

buf = bytearray(W * H * 3)


def _i(x, y):
    return (y * W + x) * 3


def set_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = _i(x, y)
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend_px(x, y, r, g, b, a):
    """Blend colour (r,g,b) over the pixel with alpha a (0..255)."""
    if 0 <= x < W and 0 <= y < H and a:
        i = _i(x, y)
        ia = 255 - a
        buf[i] = (r * a + buf[i] * ia) >> 8
        buf[i + 1] = (g * a + buf[i + 1] * ia) >> 8
        buf[i + 2] = (b * a + buf[i + 2] * ia) >> 8


def add_px(x, y, r, g, b, k):
    """Additive blend: add (r,g,b) * k/255, clamped at 255."""
    if 0 <= x < W and 0 <= y < H and k:
        i = _i(x, y)
        v = buf[i] + ((r * k) >> 8)
        buf[i] = 255 if v > 255 else v
        v = buf[i + 1] + ((g * k) >> 8)
        buf[i + 1] = 255 if v > 255 else v
        v = buf[i + 2] + ((b * k) >> 8)
        buf[i + 2] = 255 if v > 255 else v


def fill_rect(x0, y0, x1, y1, r, g, b):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes((r, g, b)) * (x1 - x0)
    for y in range(y0, y1):
        s = y * W * 3 + x0 * 3
        buf[s:s + len(row)] = row


def blend_rect(x0, y0, x1, y1, r, g, b, a):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x0 >= x1 or y0 >= y1 or not a:
        return
    ia = 255 - a
    for y in range(y0, y1):
        s = y * W * 3 + x0 * 3
        for i in range(s, s + (x1 - x0) * 3, 3):
            buf[i] = (r * a + buf[i] * ia) >> 8
            buf[i + 1] = (g * a + buf[i + 1] * ia) >> 8
            buf[i + 2] = (b * a + buf[i + 2] * ia) >> 8


# ---------------------------------------------------------------- shapes

def fill_rot_ellipse(cx, cy, a, b, deg, r, g, bl, alpha=255):
    """Fill a rotated ellipse (opaque, or alpha-blended when alpha < 255).

    Per row inside the bounding box the x-range comes from the quadratic
    form of the rotated ellipse equation -- no per-pixel test needed.
    """
    th = math.radians(deg)
    c = math.cos(th)
    s = math.sin(th)
    ia2 = 1.0 / (a * a)
    ib2 = 1.0 / (b * b)
    A = c * c * ia2 + s * s * ib2
    # bounding box half-extents of the rotated ellipse
    ex = math.sqrt(a * a * c * c + b * b * s * s)
    ey = math.sqrt(a * a * s * s + b * b * c * c)
    y0 = max(0, int(cy - ey - 1))
    y1 = min(H - 1, int(cy + ey + 1))
    for y in range(y0, y1 + 1):
        dy = y - cy
        B = 2.0 * s * c * dy * (ia2 - ib2)
        C = (s * s * dy * dy) * ia2 + (c * c * dy * dy) * ib2 - 1.0
        disc = B * B - 4.0 * A * C
        if disc <= 0:
            continue
        sq = math.sqrt(disc)
        x_lo = int(cx + (-B - sq) / (2.0 * A))
        x_hi = int(cx + (-B + sq) / (2.0 * A))
        if x_hi < 0 or x_lo >= W:
            continue
        x_lo = max(0, x_lo)
        x_hi = min(W - 1, x_hi)
        base = y * W * 3 + x_lo * 3
        n = (x_hi - x_lo + 1) * 3
        if alpha >= 255:
            buf[base:base + n] = bytes((r, g, bl)) * (x_hi - x_lo + 1)
        else:
            ia = 255 - alpha
            for i in range(base, base + n, 3):
                buf[i] = (r * alpha + buf[i] * ia) >> 8
                buf[i + 1] = (g * alpha + buf[i + 1] * ia) >> 8
                buf[i + 2] = (bl * alpha + buf[i + 2] * ia) >> 8


def fill_circle(cx, cy, rad, r, g, b, alpha=255):
    fill_rot_ellipse(cx, cy, rad, rad, 0, r, g, b, alpha)


def fill_triangle(p0, p1, p2, r, g, b, alpha=255):
    """Scanline triangle fill (opaque or alpha-blended)."""
    pts = sorted((p0, p1, p2), key=lambda p: p[1])
    (x0, y0), (x1, y1), (x2, y2) = pts
    if y2 == y0:
        return
    ia = 255 - alpha

    def edge_x(xa, ya, xb, yb, y):
        if yb == ya:
            return xa
        return xa + (xb - xa) * (y - ya) / (yb - ya)

    for y in range(max(0, y0), min(H, y2 + 1)):
        if y < y1:
            xa = edge_x(x0, y0, x1, y1, y)
            xb = edge_x(x0, y0, x2, y2, y)
        else:
            xa = edge_x(x1, y1, x2, y2, y)
            xb = edge_x(x0, y0, x2, y2, y)
        if xa > xb:
            xa, xb = xb, xa
        xi0 = max(0, int(xa))
        xi1 = min(W - 1, int(xb))
        if xi1 < xi0:
            continue
        base = y * W * 3 + xi0 * 3
        n = (xi1 - xi0 + 1) * 3
        if alpha >= 255:
            buf[base:base + n] = bytes((r, g, b)) * (xi1 - xi0 + 1)
        else:
            for i in range(base, base + n, 3):
                buf[i] = (r * alpha + buf[i] * ia) >> 8
                buf[i + 1] = (g * alpha + buf[i + 1] * ia) >> 8
                buf[i + 2] = (b * alpha + buf[i + 2] * ia) >> 8


def draw_line(x0, y0, x1, y1, r, g, b):
    """Bresenham line, 1 px wide."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, r, g, b)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


# ---------------------------------------------------------------- scene

def lerp(c0, c1, t):
    return (int(c0[0] + (c1[0] - c0[0]) * t),
            int(c0[1] + (c1[1] - c0[1]) * t),
            int(c0[2] + (c1[2] - c0[2]) * t))


def draw_sky():
    stops = [
        (0.00, (14, 12, 48)),
        (0.30, (42, 26, 84)),
        (0.55, (96, 44, 112)),
        (0.75, (178, 66, 112)),
        (0.88, (232, 110, 78)),
        (1.00, (255, 150, 70)),
    ]
    for y in range(H):
        t = y / (H - 1)
        for k in range(len(stops) - 1):
            if t <= stops[k + 1][0]:
                t0, c0 = stops[k]
                t1, c1 = stops[k + 1]
                col = lerp(c0, c1, (t - t0) / (t1 - t0))
                break
        else:
            col = stops[-1][1]
        s = y * W * 3
        buf[s:s + W * 3] = bytes(col) * W


def draw_horizon_glow():
    # Warm band hugging the horizon, fading smoothly both ways
    # (a Gaussian centred just above the skyline, so there is no hard edge).
    for y in range(690, 910):
        t = (y - 845) / 62.0
        a = int(85 * math.exp(-t * t))
        if a <= 0:
            continue
        ia = 255 - a
        s = y * W * 3
        for i in range(s, s + W * 3, 3):
            buf[i] = (255 * a + buf[i] * ia) >> 8
            buf[i + 1] = (150 * a + buf[i + 1] * ia) >> 8
            buf[i + 2] = (90 * a + buf[i + 2] * ia) >> 8


def draw_stars(rng):
    for _ in range(300):
        x = rng.randrange(W)
        y = rng.randrange(0, 780)
        v = rng.randrange(140, 256)
        sz = 1 if rng.random() < 0.8 else 2
        if sz == 1:
            set_px(x, y, v, v, min(255, v + 20))
        else:
            fill_circle(x, y, 2, v, v, min(255, v + 15), alpha=200)
            set_px(x, y, 255, 255, 255)
    # a few bright stars with a cross sparkle
    for _ in range(14):
        x = rng.randrange(40, W - 40)
        y = rng.randrange(30, 500)
        set_px(x, y, 255, 255, 255)
        for d in (1, 2, 3):
            blend_px(x + d, y, 255, 255, 255, 200 - d * 55)
            blend_px(x - d, y, 255, 255, 255, 200 - d * 55)
            blend_px(x, y + d, 255, 255, 255, 200 - d * 55)
            blend_px(x, y - d, 255, 255, 255, 200 - d * 55)


def draw_moon():
    cx, cy, R = 838, 148, 56
    # halo: precomputed radial falloff, additive
    for dy in range(-150, 151):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        half = int(math.sqrt(max(0, 150 * 150 - dy * dy)))
        for dx in range(-half, half + 1):
            d = math.sqrt(dx * dx + dy * dy)
            if d >= R:
                k = int(46 * (1.0 - d / 150.0) ** 2)
                add_px(cx + dx, y, 250, 240, 200, k)
    # disc with a soft inner gradient (concentric fills)
    for rr in range(R, 0, -6):
        shade = 232 + int(20 * (1.0 - rr / R))
        fill_circle(cx, cy, rr, shade, shade - 6, shade - 24)
    fill_circle(cx, cy, R, 246, 242, 218)
    # faint craters
    for (ox, oy, cr) in ((-18, -12, 8), (14, 8, 6), (-4, 20, 5), (22, -18, 4)):
        fill_circle(cx + ox, cy + oy, cr, 214, 210, 188, alpha=110)


# Aurora: flowing ribbons, additive, falloff table shared by all ribbons.
_FALLOFF = [int(255 * (1.0 - t / 64.0) ** 2) for t in range(65)]


def draw_aurora(rng):
    ribbons = [
        # (base_y, amp1, freq1, ph1, amp2, freq2, ph2, thick, alpha, colour)
        (150, 46, 0.0045, 0.7, 18, 0.0110, 2.1, 70, 150, (64, 255, 170)),
        (250, 60, 0.0032, 2.4, 24, 0.0090, 0.4, 95, 120, (80, 120, 255)),
        (330, 40, 0.0055, 4.0, 16, 0.0130, 1.2, 55, 130, (70, 226, 230)),
    ]
    sin = math.sin
    for (y0, a1, f1, p1, a2, f2, p2, thick, amax, col) in ribbons:
        cr, cg, cb = col
        for x in range(W):
            cy = int(y0 + a1 * sin(x * f1 + p1) + a2 * sin(x * f2 + p2))
            top = cy - thick
            bot = cy + thick
            if bot < 0 or top >= H:
                continue
            for dy in range(-thick, thick + 1):
                yy = cy + dy
                if yy < 0 or yy >= H:
                    continue
                k = (_FALLOFF[(abs(dy) * 64) // thick] * amax) >> 8
                if k:
                    add_px(x, yy, cr, cg, cb, k)


def draw_whale():
    dark = (12, 17, 46)
    rim = (96, 255, 205)
    # --- rim light: aurora-coloured shapes peeking out above the body
    fill_rot_ellipse(545, 474, 332, 97, -28, *rim)
    fill_rot_ellipse(332, 584, 152, 107, -20, *rim)
    fill_rot_ellipse(884, 264, 88, 28, -55, *rim)
    # --- tail flukes (behind the body, drawn first)
    fill_rot_ellipse(884, 268, 86, 27, -55, *dark)
    fill_rot_ellipse(868, 330, 82, 25, 14, *dark)
    # --- tail stock
    fill_rot_ellipse(762, 358, 122, 31, -35, *dark)
    # --- main body and head
    fill_rot_ellipse(540, 480, 330, 95, -28, *dark)
    fill_rot_ellipse(330, 590, 150, 105, -20, *dark)
    # --- belly lit by the aurora: a smaller ellipse shifted down inside
    fill_rot_ellipse(560, 512, 300, 58, -28, 36, 110, 128, alpha=150)
    fill_rot_ellipse(345, 622, 128, 62, -20, 44, 118, 132, alpha=140)
    # --- dorsal fin (the pectoral fin was removed: as a separate dark
    # ellipse below the belly it read as a floating leaf, not a fin)
    fill_triangle((606, 396), (664, 328), (700, 400), *dark)
    # --- eye (small, bright, clearly inside the head)
    fill_circle(256, 584, 7, 235, 245, 255)
    fill_circle(254, 586, 3, 10, 12, 30)


def draw_spout(rng):
    bx, by = 306, 506
    # faint narrow cone of light rising from the blowhole
    fill_triangle((300, by), (312, by), (306, 352), 200, 240, 255, alpha=18)
    # particles that burst upward and turn into stars
    for i in range(180):
        t = rng.random()
        spread = 16 + t * 95
        px = int(bx + (rng.random() - 0.5) * 2 * spread)
        py = int(by - t * 165 - rng.random() * 12)
        v = int(255 * (1.0 - t * 0.55))
        sz = 1 if rng.random() < 0.7 else 2
        a = 255 if t < 0.5 else int(255 * (1.0 - t) * 2)
        if sz == 1:
            blend_px(px, py, v, min(255, v + 20), 255, a)
        else:
            fill_circle(px, py, 2, v, min(255, v + 20), 255, alpha=a)
    # a few stars born from the spray
    for _ in range(10):
        px = int(bx + (rng.random() - 0.5) * 260)
        py = int(by - 150 - rng.random() * 60)
        set_px(px, py, 255, 255, 255)


def draw_city(rng):
    # deep silhouette skyline with lit windows and neon strips
    windows = [(255, 200, 90), (140, 240, 255), (255, 110, 180),
               (255, 240, 180), (120, 255, 170)]
    neons = [(60, 240, 255), (255, 70, 180), (120, 255, 170), (255, 180, 60)]
    x = -10
    while x < W:
        w = rng.randrange(46, 112)
        h = rng.randrange(70, 205)
        top = H - h
        shade = rng.randrange(8, 17)
        fill_rect(x, top, x + w, H, shade, shade + 2, shade + 16)
        # windows
        for gy in range(top + 12, H - 10, 17):
            for gx in range(x + 7, x + w - 8, 14):
                if rng.random() < 0.38:
                    c = windows[rng.randrange(len(windows))]
                    fill_rect(gx, gy, gx + 6, gy + 8, *c)
        # neon strip on some buildings
        if rng.random() < 0.30:
            nc = neons[rng.randrange(len(neons))]
            nx = x + rng.randrange(8, max(9, w - 12))
            blend_rect(nx - 3, top + 6, nx + 7, H, *nc, 70)
            fill_rect(nx, top + 6, nx + 4, H, *nc)
        # rooftop antenna with a red beacon
        if rng.random() < 0.35:
            ax = x + w // 2
            draw_line(ax, top, ax, top - 16, 40, 40, 60)
            set_px(ax, top - 18, 255, 60, 60)
        x += w + rng.randrange(0, 14)
    # thin bright horizon line where city meets sky
    for xx in range(W):
        blend_px(xx, 838, 255, 170, 110, 60)


# ---------------------------------------------------------------- PNG

def write_png(path, w, h, data):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: None
        raw += data[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        return out + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    t0 = time.time()
    rng = random.Random(SEED)
    draw_sky()
    draw_horizon_glow()
    draw_stars(rng)
    draw_moon()
    draw_aurora(rng)
    draw_whale()
    draw_spout(rng)
    draw_city(rng)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, W, H, buf)
    dt = time.time() - t0
    print(f"wrote {path} ({size} bytes) in {dt:.2f}s")


if __name__ == "__main__":
    main()
