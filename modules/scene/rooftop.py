"""Details of the rooftop where K stands: the back wall with its pipe, the antenna, the air conditioner, the barrel
and the chimney with steam.

Everything is defined in reference-frame coordinates (200x83) and painted onto the base, before K's canopy.
Nothing stands in front of K: he walks from x = 108 to 182 with his feet at y = 74, so the objects stay behind
that line (smaller y). The floor is left clear. Only the steam is painted every frame.
"""

from __future__ import annotations

import math

from modules.core.color import Color, Frame
from modules.graphics.canvas import Canvas
from modules.scene.effects import puff
from modules.scene.layout import FLOOR_Y, floor_edge

WALL_Y = 50
END_X = 200
WALL_COLOR = (36, 24, 56)
CAP_COLOR = (110, 84, 148)
METAL_COLOR = (56, 44, 82)
METAL_TOP_COLOR = (98, 82, 132)
SLOT_COLOR = (26, 16, 42)
PIPE_COLOR = (70, 56, 100)
JOI_LIGHT_COLOR = (190, 68, 170)
SHADOW_COLOR = (6, 2, 12)


class Rooftop:
    def __init__(self, canvas: Canvas) -> None:
        """Paints the back wall and what stands in front of it onto the base, from back to front."""
        self.canvas = canvas
        self.steam: list[tuple[int, int, int]] = []
        self._wall()
        self._pipe(128, 166, 51.8)
        self._antenna(122, 34)
        self._air_conditioner(128, 62, 14, 7)
        self._barrel(144, 63, 4, 6)
        self._chimney(136, 53.5, 4, 0)

    def _wall(self) -> None:
        """The low wall at the back of the roof, running from the parapet's corner to the end of the terminal:
        a light cap, joints, and JOI's pink light on the corner. The city's towers are behind it."""
        canvas = self.canvas
        x0 = floor_edge(FLOOR_Y) + 1
        canvas.rect(x0, WALL_Y, END_X, FLOOR_Y, WALL_COLOR)
        canvas.rect(x0, WALL_Y, END_X, WALL_Y + 1, CAP_COLOR)
        canvas.rect(x0, WALL_Y + 1, END_X, WALL_Y + 1.7, SHADOW_COLOR, 0.5)
        for x in range(int(x0) + 7, END_X, 11):
            canvas.rect(x, WALL_Y + 1.7, x + 0.7, FLOOR_Y, (22, 14, 36))
        canvas.rect(x0, FLOOR_Y - 0.7, END_X, FLOOR_Y, SHADOW_COLOR, 0.55)
        canvas.rect(x0, WALL_Y, x0 + 0.6, FLOOR_Y, JOI_LIGHT_COLOR, 0.5)

    def _pipe(self, x0: float, x1: float, y: float) -> None:
        """A pipe fixed to the wall, with clamps."""
        canvas = self.canvas
        canvas.rect(x0, y, x1, y + 1, PIPE_COLOR)
        canvas.rect(x0, y, x1, y + 0.4, (130, 108, 170), 0.6)
        x = x0 + 3
        while x < x1:
            canvas.rect(x, y - 0.4, x + 0.8, y + 1.4, (30, 20, 46))
            x += 8

    def _antenna(self, x: float, top: float) -> None:
        """A mast with two crossbars and a red warning light at the top, attached to the wall."""
        canvas = self.canvas
        canvas.rect(x, top, x + 0.8, FLOOR_Y, (52, 40, 78))
        canvas.rect(x, top, x + 0.4, FLOOR_Y, JOI_LIGHT_COLOR, 0.45)
        for y, half in ((top + 5, 3), (top + 10, 2)):
            canvas.rect(x - half, y, x + 0.8 + half, y + 0.7, (52, 40, 78))
        px, py = canvas.x(x), canvas.y(top)
        s = canvas.s
        canvas.add_light([(px, py - 1), (px, py)], (255, 50, 60), "blink", 9, halo=(px, py, 3 * s + 1, 3 * s + 1, 0.5))

    def _box(
        self, x0: float, bottom: float, width: float, height: float, front: Color, top: Color, depth: float
    ) -> None:
        """A volume seen slightly from above: shadow on the floor, front, lid, and JOI's pink light on the
        left side."""
        canvas = self.canvas
        canvas.rect(x0 + 1, bottom, x0 + width + 3, bottom + 1.2, SHADOW_COLOR, 0.5)
        canvas.rect(x0, bottom - height, x0 + width, bottom, front)
        canvas.rect(x0, bottom - height - depth, x0 + width, bottom - height, top)
        canvas.rect(x0, bottom - height - depth, x0 + 0.6, bottom, JOI_LIGHT_COLOR, 0.45)

    def _air_conditioner(self, x0: float, bottom: float, width: float, height: float) -> None:
        """Air conditioner: a slotted grille on the right, a flat panel on the left, and a faulty blinking LED."""
        canvas = self.canvas
        self._box(x0, bottom, width, height, METAL_COLOR, METAL_TOP_COLOR, 2)
        y = bottom - height + 1.2
        while y < bottom - 1:
            canvas.rect(x0 + width * 0.42, y, x0 + width - 1, y + 0.6, SLOT_COLOR)
            y += 1.5
        canvas.rect(x0 + 1.5, bottom - height + 1.2, x0 + width * 0.35, bottom - 1, (48, 36, 72))
        px, py = canvas.x(x0 + 2.5), canvas.y(bottom - 1.5)
        s = canvas.s
        canvas.add_light([(px, py)], (255, 90, 60), "faulty", 17, halo=(px, py, 2 * s + 1, 2 * s + 1, 0.35))

    def _barrel(self, x0: float, bottom: float, width: float, height: float) -> None:
        """An oil drum: body, two rings and the light rim on top."""
        self._box(x0, bottom, width, height, (62, 44, 86), (120, 98, 152), 1.2)
        for y in (bottom - height * 0.7, bottom - height * 0.3):
            self.canvas.rect(x0, y, x0 + width, y + 0.7, (36, 24, 56))

    def _chimney(self, x: float, bottom: float, height: float, phase: int) -> None:
        """An exhaust pipe on top of the wall, with a cap, where steam rises (painted every frame)."""
        canvas = self.canvas
        canvas.rect(x, bottom - height, x + 1.6, bottom, (58, 44, 84))
        canvas.rect(x - 0.5, bottom - height - 0.8, x + 2.1, bottom - height, (100, 82, 134))
        canvas.rect(x, bottom - height, x + 0.5, bottom, JOI_LIGHT_COLOR, 0.4)
        self.steam.append((canvas.x(x + 0.8), canvas.y(bottom - height - 1), phase))

    def paint(self, frame: Frame, tick: int) -> None:
        """Steam from the wall's chimneys: puffs that rise, grow and fade, carried to the right by the wind."""
        b = self.canvas.block
        for x, y, phase in self.steam:
            for j in range(4):
                age = (tick + phase + j * 14) % 56
                puff(
                    self.canvas,
                    frame,
                    x + math.sin(age * 0.2 + j) * b + age * 0.06 * b,
                    y - age * 0.22 * b,
                    b * (0.8 + age * 0.03),
                    0.22 * (1 - age / 56),
                )
