"""K painted on the rooftop: his sprite at the terminal's scale, lit by JOI, with his shadow, the haze that keeps
him readable, his reflection in the puddles, the cigarette's ember and the smoke.

What he is doing on each tick comes from characters/k/behavior.py; this module only paints it.
"""

from __future__ import annotations

import math

from modules.characters.k import behavior, sprites
from modules.core.color import Color, Frame, blend, scale
from modules.graphics.canvas import Canvas
from modules.graphics.sprite import Grid, resize
from modules.scene.effects import light_point, puff, wisp
from modules.scene.layout import CIGARETTE_X, CIGARETTE_Y, K_FEET_Y
from modules.scene.puddles import Puddles

ASH_COLOR = (110, 96, 98)
LIVE_EMBER_COLOR = (220, 124, 64)


class K:
    def __init__(self, canvas: Canvas, k_scale: float, puddles: Puddles) -> None:
        self.canvas = canvas
        self.k_scale = k_scale
        self.puddles = puddles
        self.haze: list[tuple[int, int, float]] = []
        self.cache: dict[tuple, Grid] = {}
        self._build_haze()

    def paint(self, frame: Frame, tick: int, light: float) -> None:
        """K on this tick, and the cigarette on the shelf behind him when he left it there. light is the
        hologram's brightness, which his lit side follows."""
        st = behavior.state(tick)
        if st.on_shelf:
            self._paint_shelf_cigarette(frame, tick)
        self._paint_figure(frame, tick, st, light)

    def _build_haze(self) -> None:
        """Pink haze around K (relative to his feet): keeps the dark coat readable against the towers."""
        ks = self.k_scale
        rx, ry = 8 * ks + 2, 16 * ks + 2
        for dy in range(-int(2 * ry), 2):
            for dx in range(-int(rx), int(rx) + 1):
                d = math.hypot(dx / rx, (dy + 11 * ks) / ry)
                if d < 1:
                    self.haze.append((dx, dy, 0.24 * (1 - d) ** 1.5))

    def _sprite(self, key: tuple) -> Grid:
        if key not in self.cache:
            grid = [[sprites.PALETTE.get(c) for c in row] for row in sprites.sprite(*key)]
            self.cache[key] = resize(grid, self.k_scale, lambda c: c[0] > 100)
        return self.cache[key]

    def _paint_figure(self, frame: Frame, tick: int, st: behavior.State, light: float) -> None:
        """K himself, with the haze behind him, his shadow, the glint at his feet and his reflection."""
        canvas = self.canvas
        key = (st.pose, st.detail, st.wind, st.mirrored, st.arm)
        grid = self._sprite(key)
        feet, left = canvas.y(K_FEET_Y), canvas.x(st.x)
        top, center = feet - len(grid), left + len(grid[0]) // 2
        for dx, dy, strength in self.haze:
            canvas.blend_at(frame, center + dx, feet + dy, (140, 56, 150), strength)
        shadow = round(9 * self.k_scale)
        for i in range(shadow):
            canvas.blend_at(frame, center + 2 + i, feet + i // 4, (6, 2, 12), 0.55 * (1 - i / shadow))
        glint = round(8 * self.k_scale)
        for i in range(1, glint):
            if (center - 1, feet + i) not in self.puddles.mask:
                canvas.blend_at(frame, center - 1, feet + i, (150, 40, 140), 0.32 * (1 - i / glint))
        for dy, row in enumerate(grid):
            for dx, color in enumerate(row):
                if color is not None and canvas.in_bounds(left + dx, top + dy):
                    frame[top + dy][left + dx] = scale(color, light) if color[0] > 100 else color
        self.puddles.reflect_sprite(frame, tick, grid, left, feet)
        self._paint_cigarette(frame, tick, st, key, left, top, len(grid))

    def _ember_color(self, ember: float) -> Color:
        return blend(ASH_COLOR, LIVE_EMBER_COLOR, min(1.0, ember * 1.4))

    def _paint_cigarette(
        self, frame: Frame, tick: int, st: behavior.State, key: tuple, left: int, top: int, height: int
    ) -> None:
        """The cigarette's ember (or the lighter's flame) in his hand or mouth, and the smoke from his drags."""
        canvas = self.canvas
        b = max(1, round(self.k_scale))
        rows = sprites.sprite(*key)
        rx, ry = len(self._sprite(key)[0]) / len(rows[0]), height / len(rows)

        def at(column: float, row: float) -> tuple[int, int]:
            return left + int(column * rx), top + int(row * ry)

        mark = sprites.LIFT_EMBER.get(st.arm) or sprites.ember_position(rows)
        if mark is not None:
            x, y = at(*mark)
            if rows[mark[1]][mark[0]] == "Y":
                color = ((255, 240, 170), (255, 214, 90), (255, 180, 60))[tick % 3]
                light_point(canvas, frame, x, y, (255, 200, 110), 0.5, 3 * b)
            else:
                color = self._ember_color(st.ember)
                if st.ember > 0.2:
                    light_point(canvas, frame, x, y, LIVE_EMBER_COLOR, 0.2 * st.ember, 2 * b)
            for bx in range(b):
                for by in range(b):
                    if canvas.in_bounds(x + bx, y + by):
                        frame[y + by][x + bx] = color
            if st.arm == "resting" and st.ember > 0.2:
                wisp(canvas, frame, tick, x, y, 0.22, b)
        if st.smoke is not None:
            mouth_x, mouth_y = at(*sprites.MOUTH)
            a = st.smoke
            puff(
                canvas,
                frame,
                mouth_x + a * 0.22 * b,
                mouth_y - a * 0.3 * b,
                (1 + a * 0.13) * b,
                0.5 * (1 - a / behavior.SMOKE_FRAMES),
            )

    def _paint_shelf_cigarette(self, frame: Frame, tick: int) -> None:
        """The cigarette resting on the shelf: the ember and the paper, 1 pixel each, and the wisp of smoke.
        It sits behind K."""
        canvas = self.canvas
        x, y = canvas.x(CIGARETTE_X), canvas.y(CIGARETTE_Y)
        ember = 0.6 + 0.15 * math.sin(tick * 0.3)
        if 0 <= x + 1 < canvas.w and 0 <= y < canvas.h:
            frame[y][x] = (168, 158, 156)
            frame[y][x + 1] = self._ember_color(ember)
            light_point(canvas, frame, x + 1, y, LIVE_EMBER_COLOR, 0.16 * ember, 2)
        wisp(canvas, frame, tick, x + 1, y, 0.3, 1)
