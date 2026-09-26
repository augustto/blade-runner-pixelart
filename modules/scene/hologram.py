"""JOI's giant hologram: the sprite scaled to the terminal, pulsing, with scanlines, a sweeping band of light,
glitches, her blink and her hair swaying in the wind.

The sprite (characters/joi/sprite.py) was extracted at the reference frame's scale, so it touches the top-left
corner of the film frame and is multiplied by the terminal's scale. Each row is stored as contiguous runs
(spans), precomputed per brightness level, so a frame only copies slices.
"""

from __future__ import annotations

import math

from modules.characters.joi import sprite as joi_sprite
from modules.characters.joi.blink import close_eyes, is_blinking
from modules.core.color import Color, Frame, average, blend, scale
from modules.core.timing import seeded
from modules.graphics.canvas import Canvas
from modules.graphics.sprite import Grid, resize

Spans = list[tuple[int, list[Color]]]
Tail = list[tuple[int, float, list[tuple[int, Color]]]]

SCANLINE = 0.78
HAIR_BLUE_MARGIN = 35
HAIR_WIND = 5.0
HAIR_TIPS = (46, 68)
LEVELS = 25
DISSOLVE = 30


class Hologram:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas
        self.skin: list[Spans] = []
        self.closed: list[Spans] = []
        self.hair: list[Spans] = []
        self.tail: Tail = []
        self.eye_rows: set[int] = set()
        self.cache: dict[tuple[str, int, int], Spans] = {}
        self._build()

    def _build(self) -> None:
        """JOI at the size of the screen: her skin with the eyes open and closed, the hair apart (it sways in the
        wind) and the tail that dissolves below the film frame."""

        def grid(rows: tuple[str, ...]) -> Grid:
            return resize([[joi_sprite.PALETTE[c] if c != "." else None for c in row] for row in rows], self.canvas.s)

        def is_hair(color: Color | None) -> bool:
            return color is not None and color[2] - color[0] > HAIR_BLUE_MARGIN

        def without_hair(g: Grid) -> list[Spans]:
            return self._to_spans([[None if is_hair(c) else c for c in row] for row in g])[0]

        open_eyes = grid(joi_sprite.ROWS)
        self.tail = self._to_spans(open_eyes)[1]
        self.hair = self._to_spans([[c if is_hair(c) else None for c in row] for row in open_eyes])[0]
        self.skin = without_hair(open_eyes)
        self.closed = without_hair(grid(close_eyes(joi_sprite.ROWS)))
        self.eye_rows = {y for y, (a, b) in enumerate(zip(self.skin, self.closed)) if a != b}

    def _to_spans(self, grid: Grid) -> tuple[list[Spans], Tail]:
        """A pose as contiguous runs per row (to be written in one go), plus the tail below it.

        Below the film frame her body continues and dissolves little by little, like a projection losing
        strength (the color blends more and more with what is behind it).
        """
        canvas = self.canvas
        rows: list[Spans] = [[] for _ in range(canvas.h)]
        for i, row in enumerate(grid):
            if canvas.dy + i >= canvas.h:
                break
            spans: Spans = []
            for x, color in enumerate(row):
                if color is None:
                    continue
                if spans and spans[-1][0] + len(spans[-1][1]) == x:
                    spans[-1][1].append(color)
                else:
                    spans.append((x, [color]))
            rows[canvas.dy + i] = spans
        columns = [[grid[-i][x] for i in range(1, 7) if grid[-i][x] is not None] for x in range(len(grid[0]))]
        raw = [average(colors) if grid[-1][x] and len(colors) >= 3 else None for x, colors in enumerate(columns)]
        n = len(raw)
        last = []
        for x in range(n):
            window = [raw[min(max(i, 0), n - 1)] for i in range(x - 2, x + 3)]
            filled = [color for color in window if color]
            last.append(average(filled) if raw[x] and len(filled) >= 4 else None)
        length = max(6, round(DISSOLVE * canvas.s))
        tail = []
        start = canvas.dy + len(grid)
        for y in range(start, min(canvas.h, start + length)):
            strength = (1 - (y - start) / length) ** 1.6
            tail.append((y, strength, [(x, color) for x, color in enumerate(last) if color is not None]))
        return rows, tail

    def pulse(self, tick: int) -> float:
        """Overall hologram brightness: breathes slowly and flickers once in a while."""
        f = 1 + 0.035 * math.sin(tick * 0.21)
        t, rng = seeded(tick, 70, 5)
        if rng.random() < 0.3 and t == rng.randint(0, 69):
            f *= 0.82
        return f

    def glitch(self, tick: int) -> tuple[int, int, int] | None:
        """Hologram glitch: a band of rows slides sideways for a few frames. Returns (top, bottom, shift)."""
        canvas = self.canvas
        t, rng = seeded(tick, 110, 11)
        happens, start, duration = rng.random() < 0.6, rng.randint(0, 100), rng.randint(2, 4)
        top, tall = canvas.dy + rng.randint(0, canvas.core * 3 // 4), rng.randint(3, max(4, canvas.core // 7))
        shift = rng.choice((-3, -2, 2, 3))
        if happens and start <= t < start + duration:
            return top, top + tall, max(1, round(abs(shift) * canvas.s)) * (1 if shift > 0 else -1)
        return None

    def _level_spans(self, layer: str, y: int, level: int) -> Spans:
        key = (layer, y, level)
        spans = self.cache.get(key)
        if spans is None:
            factor = level / LEVELS
            source = {"hair": self.hair, "open": self.skin, "closed": self.closed}[layer]
            spans = [(x, [scale(c, factor) for c in colors]) for x, colors in source[y]]
            self.cache[key] = spans
        return spans

    def hair_wind(self, y: int, tick: int) -> int:
        """How far row y of the hair shifts to the right (the wind blows that way, like the rain): only the tips
        sway, in a slow wave that travels down the strands, with even slower gusts."""
        start, end = HAIR_TIPS
        root = min(1.0, max(0.0, (self.canvas.ref_y(y) - start) / (end - start)))
        if root == 0:
            return 0
        wave = 0.3 + 0.55 * math.sin(tick * 0.07 - root * 3) + 0.35 * math.sin(tick * 0.021 + 1.3)
        return round(HAIR_WIND * max(self.canvas.s, 1.0) * root**1.3 * wave)

    def paint(self, frame: Frame, tick: int) -> None:
        canvas = self.canvas
        pulse = self.pulse(tick)
        glitch = self.glitch(tick)
        eyes = "closed" if is_blinking(tick) else "open"
        sweep = (tick * 0.8) % (canvas.core + 40) - 20 + canvas.dy
        for y, (skin, hair) in enumerate(zip(self.skin, self.hair)):
            if not skin and not hair:
                continue
            f = pulse * (1.0 if y % 2 == 0 else SCANLINE)
            if abs(y - sweep) < 2.5 * canvas.s:
                f *= 1.18
            shift = 0
            if glitch and glitch[0] <= y < glitch[1]:
                shift, f = glitch[2], f * 1.25
            level = max(1, min(int(f * LEVELS), 2 * LEVELS))
            row = frame[y]
            sway = self.hair_wind(y, tick)
            face = eyes if y in self.eye_rows else "open"
            for layer, offset in (("hair", 0), ("hair", sway), (face, 0)):
                for x, colors in self._level_spans(layer, y, level):
                    x += shift + offset
                    if x < 0:
                        colors, x = colors[-x:], 0
                    row[x : x + len(colors)] = colors[: max(0, canvas.w - x)]
        for y, strength, points in self.tail:
            factor = pulse * (1.0 if y % 2 == 0 else SCANLINE)
            row = frame[y]
            for x, color in points:
                row[x] = blend(row[x], scale(color, factor), strength)
