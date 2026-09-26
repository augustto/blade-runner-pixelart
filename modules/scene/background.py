"""The backdrop painted first on the base: the purple fog JOI lights up and the roof's wet floor, then dithered
into pixel-art steps."""

from __future__ import annotations

from modules.core.color import blend, interpolate, scale
from modules.graphics.canvas import REF_WIDTH, Canvas
from modules.scene.layout import EDGE_X, FLOOR_Y, floor_edge, floor_edge_px

# Background fog: color by reference x and brightness by reference y.
PROFILE_X = (
    (0, (110, 50, 140)),
    (105, (78, 30, 104)),
    (125, (47, 6, 70)),
    (140, (37, 4, 57)),
    (155, (26, 4, 42)),
    (170, (19, 6, 31)),
    (185, (11, 7, 21)),
    (200, (7, 6, 12)),
)
PROFILE_Y = (
    (-150, 0.20),
    (-40, 0.22),
    (0, 0.28),
    (10, 0.42),
    (20, 0.58),
    (30, 0.72),
    (40, 0.85),
    (52, 0.97),
    (58, 1.0),
    (300, 1.0),
)
CITY_GLOW = (112, 42, 132)
CITY_GLOW_STRENGTH = 0.34
DITHER_STEP = 5
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def paint_fog(canvas: Canvas) -> None:
    """The purple fog JOI lights up: bright next to her, dark to the right and upward. Starts the base."""
    c = canvas
    columns = [interpolate(PROFILE_X, (x + 0.5) / c.s) for x in range(c.w)]
    edge = c.x(EDGE_X)
    c.base = []
    for y in range(c.h):
        yr = c.ref_y(y + 0.5)
        factor = interpolate(PROFILE_Y, yr)
        if yr >= FLOOR_Y:
            factor *= 0.9
        row = [scale(color, factor) for color in columns]
        glow = max(0.0, 1 - abs(yr - 48) / 52) if yr < FLOOR_Y + 12 else 0.0
        haze = max(0.0, 1 - abs(yr - 15) / 75)
        for x in range(min(c.w, edge)):
            row[x] = blend(row[x], CITY_GLOW, 0.16 * haze)
        if glow:
            for x in range(edge, c.w):
                left = min(1.0, ((x + 0.5) / c.s - EDGE_X) / 14)
                row[x] = blend(row[x], CITY_GLOW, CITY_GLOW_STRENGTH * glow * left)
        c.base.append(row)


def paint_floor(canvas: Canvas) -> None:
    """The roof's wet floor, up to the diagonal edge: tile joints in perspective."""
    c = canvas
    vanish_x, vanish_y = 150, 30
    joint_color = (150, 90, 200)
    for py in range(c.y(FLOOR_Y), c.h):
        for px in range(max(0, floor_edge_px(c, py)), c.w):
            c.plot(px, py, (10, 4, 20), 0.15)
    i = 1
    while (y := FLOOR_Y + 30 * (i / 9) ** 1.7) < c.bottom_ref:
        c.rect(floor_edge(y) + 2, y, REF_WIDTH, y + 0.4, joint_color, 0.05)
        i += 1
    for base_x in range(-400, 600, 30):
        for py in range(c.y(FLOOR_Y), c.h):
            y = c.ref_y(py)
            x = vanish_x + (base_x - vanish_x) * (y - vanish_y) / (83 - vanish_y)
            if floor_edge(y) + 2 < x < REF_WIDTH:
                c.plot(c.x(x), py, joint_color, 0.045)


def quantize(canvas: Canvas) -> None:
    """Runs the base through a Bayer matrix: the gradient becomes pixel-art steps."""
    p = DITHER_STEP
    for y, row in enumerate(canvas.base):
        threshold = BAYER[y % 4]
        for x, (r, g, b) in enumerate(row):
            t = threshold[x % 4] / 16
            row[x] = (
                min(255, int((r + t * p) // p * p)),
                min(255, int((g + t * p) // p * p)),
                min(255, int((b + t * p) // p * p)),
            )
