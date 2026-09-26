"""The city around the film frame: towers, windows, neon signs, blurred lights, ships, K's balcony and the footer.

Everything here is painted on the Canvas grid, in reference coordinates. With the terminal at the film's
aspect ratio almost nothing shows beyond what is already in the frame (the balcony, a few windows and neons);
with a tall terminal the towers grow upward and the city fills the space that used to be black.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import NamedTuple

from modules.core.color import Color, Frame, blend
from modules.graphics.canvas import REF_WIDTH, Canvas, Light
from modules.scene.layout import CYAN, EDGE_X, FLOOR_Y, PINK, RED, TOKYO_NIGHT_BLUES, floor_edge

# (widths, darkness, tint, bottom, top range, share of the space above, gap range), from back to front.
LAYERS = (
    ((4, 8), 0.28, (34, 14, 56), 50, (10, 34), 0.55, (-1, 2)),
    ((8, 15), 0.45, (14, 6, 28), 53, (2, 30), 0.80, (0, 9)),
    ((15, 30), 0.62, (4, 2, 8), FLOOR_Y, (-4, 24), 1.00, (8, 24)),
)
WINDOW_COLORS = ((255, 238, 205), (245, 240, 225), (225, 232, 240), (255, 226, 180))
NEON_COLORS = TOKYO_NIGHT_BLUES
NEON_PATTERNS = ("steady",) * 6 + ("blink", "faulty", "window")

STROKES = (
    ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
    ((0, 2), (1, 2), (2, 2), (3, 2), (4, 2)),
    ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
    ((2, 0), (2, 1), (2, 2), (2, 3), (2, 4)),
    ((4, 0), (4, 1), (4, 2), (4, 3), (4, 4)),
    ((0, 4), (1, 3), (2, 2), (3, 1), (4, 0)),
    ((0, 0), (1, 1), (2, 2), (3, 3), (4, 4)),
    ((1, 1), (2, 1), (3, 1)),
    ((1, 3), (2, 3), (3, 3)),
)

SHIP = (
    "..DSD....",
    "Tdddddddh",
    ".sssssss.",
    ".u.....u.",
)
SHIP_COLORS: dict[str, Color] = {
    "d": (32, 36, 58),
    "D": (76, 84, 124),
    "s": (16, 18, 32),
    "u": (120, 200, 255),
    "h": (255, 248, 225),
    "T": (255, 70, 60),
    "S": (240, 246, 255),
}
TAIL_LIGHT_OFF: Color = (72, 24, 28)


def glyph(rng: random.Random) -> set[tuple[int, int]]:
    return set().union(*rng.sample(STROKES, rng.randint(3, 4)))


class Tower(NamedTuple):
    x0: float
    x1: float
    top: float
    bottom: float
    darkness: float
    fog: float


@dataclass(frozen=True)
class Ship:
    """A ship that crosses the city and disappears, waiting a while before coming back."""

    y: int
    speed: float
    direction: int
    phase: float
    cycle: float
    pixels: tuple[tuple[int, int, str], ...]
    thrusters: tuple[tuple[int, int], ...]
    nose: int
    width: int


class City:
    """Built in steps (the build_* methods), because the scene interleaves them with the other layers: the order
    decides what covers what on the base and the sequence of numbers drawn from the city's RNG. Only the ships are
    painted every frame."""

    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas
        self.towers: list[Tower] = []
        self.ships: list[Ship] = []
        self.occupied: list[tuple[float, float, float, float]] = [(168, 40, 202, 76)]
        self.no_signs = [(104, 26, 202, 78), (0, -4, 76, 90)]

    def _tower(
        self,
        x0: float,
        x1: float,
        top: float,
        darkness: float,
        bottom: float = FLOOR_Y,
        fog: float = 0.0,
        tint: Color = (4, 2, 8),
    ) -> None:
        """A dark tower in the fog; with fog > 0 it fades out over its last rows, down to bottom."""
        canvas = self.canvas
        for y in range(max(0, canvas.y(top)), min(canvas.h, canvas.y(bottom))):
            e = darkness
            if fog:
                e *= min(1.0, (bottom - canvas.ref_y(y)) / fog)
            px0, px1 = canvas.x(x0), min(canvas.w, canvas.x(x1))
            for x in range(px0, px1):
                volume = 0.8 + 0.4 * (x - px0) / max(1, px1 - px0 - 1)
                edge = 0.55 if x in (px0, px1 - 1) else 1
                canvas.base[y][x] = blend(canvas.base[y][x], tint, min(1.0, e * volume * edge))
        self.towers.append(Tower(x0, x1, top, bottom, darkness, fog))

    def build_towers(self, rng: random.Random) -> None:
        """Skyline: on the right, three layers of buildings (thin ones at the back, wide ones in front); on the
        left, behind JOI, silhouettes in the fog, wider and darker the closer they are. They hold the blurred
        lights."""
        high = self.canvas.top_ref
        for widths, darkness, tint, bottom, (t0, t1), share, (gap0, gap1) in LAYERS:
            x = EDGE_X + 2 - rng.uniform(0, 5)
            while x < REF_WIDTH + 2:
                width = rng.uniform(*widths)
                top = rng.uniform(t0, t1) + high * share * rng.uniform(0.6, 1.0)
                self._tower(x, min(x + width, REF_WIDTH + 2), top, darkness, bottom=bottom, tint=tint)
                if width > 8 and rng.random() < 0.6:
                    crown = top - rng.uniform(3, 6)
                    self._tower(x + 1.5, x + width - 1.5, crown, darkness, bottom=top + 1, tint=tint)
                x += width + rng.uniform(gap0, gap1)
        backdrop = []
        x = -rng.uniform(0, 6)
        while x < EDGE_X - 6:
            width = rng.uniform(8, 26)
            backdrop.append((width, x, rng.uniform(high * 0.97, 14) - (width - 8) * 0.3))
            x += width * rng.uniform(0.6, 1.0)
        for width, x, top in sorted(backdrop):
            darkness = 0.42 + 0.28 * (width - 8) / 18
            self._tower(max(0.0, x), min(x + width, EDGE_X - 4), top, darkness, bottom=64, fog=10, tint=(12, 5, 24))

    def build_windows(self, rng: random.Random) -> None:
        """Dark windows, some lit (blinking now and then), and antennas with warning lights, on the sharp
        towers."""
        canvas = self.canvas
        for x0, x1, top, bottom, darkness, fog in self.towers:
            if fog:
                continue
            for yr in range(int(top) + 3, int(bottom - fog) - 3, 4):
                for xr in range(int(x0) + 2, int(x1) - 1, 3):
                    roll = rng.random()
                    if any(a0 <= xr < a1 and b0 <= yr < b1 for a0, b0, a1, b1 in self.occupied):
                        continue
                    x, y = canvas.x(xr), canvas.y(yr)
                    if roll < 0.22:
                        canvas.plot(x, y, (58, 34, 84), 0.7)
                    elif roll < 0.27:
                        color = rng.choice(WINDOW_COLORS)
                        canvas.add_light(
                            [(x, y)], color, "window", rng.randrange(120), alpha=0.5 + 0.4 * darkness, off=0.25
                        )
            if rng.random() < 0.6 and bottom == FLOOR_Y:
                cx, height = (x0 + x1) / 2, rng.uniform(3, 7)
                canvas.rect(cx, top - height, cx + 0.6, top, (30, 20, 50), 0.9)
                px, py = canvas.x(cx), canvas.y(top - height)
                canvas.add_light(
                    [(px, py)], RED, "beacon", rng.randrange(12), halo=(px, py, 3 * canvas.s + 1, 2 * canvas.s + 1, 0.4)
                )

    def _sign_size(self, glyph_count: int, vertical: bool) -> tuple[int, int]:
        """Width and height, in pixels, of a sign with that many glyphs."""
        b = self.canvas.block
        length = glyph_count * 6 * b - b + 2
        return (5 * b + 2, length) if vertical else (length, 5 * b + 2)

    def _sign(
        self,
        x: int,
        y: int,
        glyphs: list[set[tuple[int, int]]],
        vertical: bool,
        color: Color,
        pattern: str,
        phase: int,
    ) -> None:
        """A dark panel with neon glyphs; (x, y) is the top-left corner, in pixels."""
        canvas = self.canvas
        b = canvas.block
        step = 6 * b
        w, h = self._sign_size(len(glyphs), vertical)
        for py in range(y, y + h):
            for px in range(x, x + w):
                border = px in (x, x + w - 1) or py in (y, y + h - 1)
                canvas.plot(px, py, (26, 30, 52), 0.22 if border else 0.5)
        points = []
        for i, g in enumerate(glyphs):
            gx, gy = (x + 1, y + 1 + i * step) if vertical else (x + 1 + i * step, y + 1)
            for cx, cy in g:
                points += [(gx + cx * b + bx, gy + cy * b + by) for by in range(b) for bx in range(b)]
        canvas.add_light(
            points,
            color,
            pattern,
            phase,
            alpha=0.95,
            off=0.2,
            halo=(x + w / 2, y + h / 2, w * 1.1 + 2, h * 0.7 + 2, 0.28),
        )

    def build_neons(self, rng: random.Random) -> None:
        """Vertical and horizontal neon signs on the towers, all in Tokyo Night blues."""
        canvas = self.canvas
        high = -canvas.top_ref
        wanted = min(18, 3 + int(high / 7))
        placed = 0
        for _ in range(wanted * 10):
            if placed >= wanted:
                break
            x0, x1, top, bottom, _darkness, _fog = rng.choice(self.towers)
            vertical = rng.random() < 0.6
            glyphs = [glyph(rng) for _ in range(rng.randint(2, 4))]
            w, h = self._sign_size(len(glyphs), vertical)
            wr, hr = w / canvas.s, h / canvas.s
            ymax = min(bottom - hr - 4, FLOOR_Y - hr - 6)
            if x1 - x0 < wr + 2 or ymax <= top + 5:
                continue
            xr, yr = rng.uniform(x0 + 1, x1 - wr - 1), rng.uniform(top + 5, ymax)
            blocked = self.occupied + self.no_signs
            if any(xr < a1 and xr + wr > a0 and yr < b1 and yr + hr > b0 for a0, b0, a1, b1 in blocked):
                continue
            self.occupied.append((xr, yr, xr + wr, yr + hr))
            self._sign(
                canvas.x(xr),
                canvas.y(yr),
                glyphs,
                vertical,
                rng.choice(NEON_COLORS),
                rng.choice(NEON_PATTERNS),
                rng.randrange(120),
            )
            placed += 1

    def build_bokeh(self, rng: random.Random) -> None:
        """Out-of-focus lights, like the film's (three small windows inside a halo), on the towers in the fog.

        Each light sits in a window of a regular grid on its tower, with dark windows between them: the light
        belongs to a building and two lights never overlap. The further right, the fainter; and up high, where
        the fog is darker, too.
        """
        canvas = self.canvas
        s = canvas.s
        for x0, x1, top, bottom, _darkness, fog in self.towers:
            if not fog:
                continue
            for y in range(int(top) + 4, int(bottom - fog) - 2, 6):
                for x in range(int(x0) + 3, int(x1) - 2, 6):
                    if any(a0 - 4 <= x < a1 + 4 and b0 - 3 <= y < b1 + 3 for a0, b0, a1, b1 in self.occupied):
                        continue
                    roll = rng.random()
                    if roll < 0.45:
                        canvas.plot(canvas.x(x), canvas.y(y), (72, 46, 104), 0.6)
                        continue
                    if roll > 0.45 + 0.30:
                        continue
                    strength = rng.uniform(0.13, 0.3) * min(1.2, max(0.25, 1.1 - (x - 62) / 110))
                    strength *= 1 - 0.5 * min(1.0, max(0.0, -y / 60))
                    cx, cy = x * s, y * s + canvas.dy
                    glow = (190, 175, 210)
                    pixels = canvas.glow(cx, cy, 4 * s + 1, 2.4 * s + 1, glow, strength * 1.5, strength * 0.8)
                    for dx in (-1, 0, 1):
                        px, py = round(cx + dx * max(2, 2 * s)), round(cy)
                        if canvas.in_bounds(px, py):
                            under = canvas.base[py][px]
                            pixels.append(
                                (
                                    px,
                                    py,
                                    blend(under, (230, 220, 240), min(1, strength * 3.2)),
                                    blend(under, (230, 220, 240), strength * 1.4),
                                )
                            )
                    left, right = canvas.x(x0), canvas.x(x1)
                    pixels = [p for p in pixels if left <= p[0] < right]
                    canvas.lights.append(Light(pixels, "window", rng.randint(0, 119)))

    @property
    def _ship_block(self) -> int:
        return max(1, round(self.canvas.s * 1.2))

    def build_ships(self, rng: random.Random) -> None:
        """Two distant ships crossing the city in opposite directions, one higher than the other."""
        canvas = self.canvas
        b = self._ship_block
        limit = max(8, canvas.dy + canvas.x(36))
        heights = (rng.randint(3, limit // 2), rng.randint(limit // 2 + 3, limit))
        sprite_width = len(SHIP[0])
        for i, (speed, direction) in enumerate(((1.8, 1), (1.5, -1))):
            pixels, thrusters = [], []
            for dy, row in enumerate(SHIP):
                for dx, letter in enumerate(row):
                    if letter == ".":
                        continue
                    col = dx if direction > 0 else sprite_width - 1 - dx
                    for by in range(b):
                        for bx in range(b):
                            pixels.append((col * b + bx, dy * b + by, letter))
                    if letter == "u":
                        thrusters.append((col * b + b // 2, dy * b + b))
            speed *= max(0.5, canvas.s)
            width = sprite_width * b
            self.ships.append(
                Ship(
                    y=heights[i],
                    speed=speed,
                    direction=direction,
                    phase=(canvas.w * 0.25 + width) if i == 0 else 0.0,
                    cycle=canvas.w + 2 * width + speed * rng.uniform(1300, 2000),
                    pixels=tuple(pixels),
                    thrusters=tuple(thrusters),
                    nose=(sprite_width - 1) * b if direction > 0 else 0,
                    width=width,
                )
            )

    def paint(self, frame: Frame, tick: int) -> None:
        """The ships on this tick: thruster glow, headlight beam, body, and the blinking strobe and tail light."""
        canvas = self.canvas
        b = self._ship_block
        strobe_on = tick % 20 < 2
        tail_on = tick // 5 % 2 == 0
        blue = SHIP_COLORS["u"]
        glowing = (SHIP_COLORS["h"], SHIP_COLORS["T"], SHIP_COLORS["S"], blue)
        for ship in self.ships:
            pos = (tick * ship.speed + ship.phase) % ship.cycle
            if pos >= canvas.w + ship.width:
                continue
            x0 = int(pos - ship.width) if ship.direction > 0 else int(canvas.w - pos)
            y0 = ship.y + round(math.sin(tick * 0.05 + ship.phase) * b)
            for dx, dy in ship.thrusters:
                for gx in range(-2 * b, 2 * b + 1):
                    for gy in range(4 * b):
                        alpha = 0.26 * (1 - gy / (4 * b)) * (1 - abs(gx) / (2 * b + 1))
                        canvas.blend_at(frame, x0 + dx + gx, y0 + dy + gy, blue, alpha)
            beam = 8 * b
            for step in range(1, beam):
                for dy in range(step // 2 + 1):
                    alpha = 0.16 * (1 - step / beam) * (1 - dy / (step // 2 + 1))
                    canvas.blend_at(
                        frame, x0 + ship.nose + ship.direction * step, y0 + 2 * b + dy, (255, 240, 200), alpha
                    )
            for dx, dy, letter in ship.pixels:
                color = SHIP_COLORS[letter]
                if letter == "S" and not strobe_on:
                    color = SHIP_COLORS["D"]
                elif letter == "T" and not tail_on:
                    color = TAIL_LIGHT_OFF
                x, y = x0 + dx, y0 + dy
                if canvas.in_bounds(x, y):
                    frame[y][x] = color
                    if color in glowing:
                        for hx, hy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                            canvas.blend_at(frame, hx, hy, color, 0.25)

    def build_balcony(self) -> None:
        """The edge of the roof, to K's left: the parapet in perspective, the railing and the lamp.

        The edge runs down diagonally, from the back (at the corner) to the bottom of the terminal; outside it
        there is only the fog lit by JOI. The parapet and railing follow that diagonal.
        """
        canvas = self.canvas
        s = canvas.s
        for py in range(canvas.y(FLOOR_Y), canvas.h):
            y = canvas.ref_y(py)
            xe = canvas.x(floor_edge(y))
            depth = y - FLOOR_Y
            width = max(2, round((2 + depth * 0.1) * s))
            canvas.plot(xe, py, (190, 68, 170), 0.55)
            canvas.plot(xe + 1, py, (124, 90, 164), 0.9)
            for x in range(xe + 2, xe + 2 + width):
                canvas.plot(x, py, (40, 24, 60))
            canvas.plot(xe + 2 + width, py, (12, 6, 20), 0.6)
            height = max(3, round((6 + depth * 0.12) * s))
            canvas.plot(xe + 1, py - height, (98, 68, 132))
            if py % max(3, round(5 * s)) == 0:
                for y2 in range(py - height, py):
                    canvas.plot(xe + 1, y2, (62, 40, 94))
        xe, py = canvas.x(floor_edge(FLOOR_Y + 1)), canvas.y(FLOOR_Y + 1)
        height = max(3, round(6 * s))
        for y in range(py - height - 1, py):
            canvas.plot(xe + 1, y, (98, 68, 132))
        canvas.add_light(
            [(xe + 1, py - height - 2), (xe + 1, py - height - 1)],
            (255, 200, 120),
            "steady",
            20,
            halo=(xe + 1, py - height - 2, 5 * s + 1, 4 * s + 1, 0.4),
        )

    def build_footer(self) -> None:
        """A parapet and railing at the bottom of the terminal, when there is room below the film frame."""
        canvas = self.canvas
        bottom = canvas.bottom_ref
        if bottom < 96:
            return
        top = bottom - 7
        canvas.rect(0, top, 200, bottom, (8, 4, 14), 0.96)
        for x in range(200):
            canvas.rect(x, top, x + 1, top + 0.9, blend(PINK, CYAN, x / 200), 0.55)
        canvas.rect(0, top - 6, 200, top - 5.2, (60, 42, 92), 0.9)
        for x in range(2, 200, 6):
            canvas.rect(x, top - 6, x + 0.8, top, (24, 14, 38), 0.95)
