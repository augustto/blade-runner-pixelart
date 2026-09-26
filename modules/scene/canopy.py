"""The sheet-metal canopy in the right corner, where K sits and smokes: painted once on the base, plus the water
dripping from its eave every frame. The rain asks it where the roof is and which pixels it shelters."""

from __future__ import annotations

import math

from modules.characters.k.sprites import SEAT_HEIGHT
from modules.core.color import Frame, blend
from modules.graphics.canvas import Canvas
from modules.scene.layout import (
    BENCH_X0,
    BENCH_X1,
    CANOPY_EAVE,
    CANOPY_TOP,
    CANOPY_X0,
    CANOPY_X1,
    K_FEET_Y,
    RAIN_FAR,
    SHELF_X0,
    SHELF_X1,
    SHELF_Y,
)

DRIP_SPLASH_COLOR = (200, 200, 255)


class Canopy:
    def __init__(self, canvas: Canvas, k_scale: float) -> None:
        self.canvas = canvas
        self.k_scale = k_scale
        self.shelter = (0, 0, canvas.h, canvas.h)
        self.drips: list[tuple[int, int, int]] = []
        self._build()

    def _build(self) -> None:
        """The sheet-metal canopy in the right corner, under which K smokes: a roof in perspective, two posts,
        a back wall, a lamp, the bench he sits on and the cigarette shelf. Rain doesn't get in (see rain.py)
        and drips from the eave."""
        canvas = self.canvas
        x0, x1 = CANOPY_X0, CANOPY_X1
        feet = K_FEET_Y
        mid = (x0 + x1) / 2
        canvas.rect(x0 + 1.5, CANOPY_EAVE, x1 - 1.5, feet - 0.5, (34, 22, 54), 0.72)
        for y in range(CANOPY_EAVE + 3, feet, 5):
            canvas.rect(x0 + 1.5, y, x1 - 1.5, y + 0.6, (22, 14, 36), 0.8)
        for py in range(canvas.y(feet) - 2, canvas.y(feet) + 3):
            for px in range(canvas.x(x0), canvas.x(x1)):
                d = math.hypot((px / canvas.s - mid) / ((x1 - x0) / 2), (py - canvas.y(feet)) / (3 * canvas.s + 1))
                if d < 1:
                    canvas.plot(px, py, (255, 190, 120), 0.16 * (1 - d))
        for x in (x0, x1 - 1):
            canvas.rect(x, CANOPY_EAVE, x + 1, feet, (46, 36, 70))
        canvas.rect(x0, CANOPY_EAVE, x0 + 0.5, feet, (190, 68, 170), 0.5)
        self._bench(feet)
        canvas.rect(SHELF_X0, SHELF_Y, SHELF_X1, SHELF_Y + 1, (118, 90, 152))
        canvas.rect(SHELF_X0 + 1, SHELF_Y + 1, SHELF_X0 + 2, SHELF_Y + 4, (46, 36, 70))
        for y in range(CANOPY_TOP, CANOPY_EAVE - 2):
            inset = (CANOPY_EAVE - 2 - y) * 0.7
            for px in range(canvas.x(x0 + inset), min(canvas.w, canvas.x(x1 - inset) + 1)):
                canvas.plot(px, canvas.y(y), (92, 78, 126) if px % 3 else (66, 54, 98))
        canvas.rect(x0 - 1, CANOPY_EAVE - 2, x1 + 1, CANOPY_EAVE, (24, 16, 40))
        canvas.rect(x0 - 1, CANOPY_EAVE - 2, x1 + 1, CANOPY_EAVE - 1.4, (150, 120, 200), 0.6)
        px, py = canvas.x(mid), canvas.y(CANOPY_EAVE + 3)
        canvas.rect(mid, CANOPY_EAVE, mid + 0.6, CANOPY_EAVE + 3, (46, 36, 70))
        canvas.add_light(
            [(px, py), (px, py + 1)],
            (255, 200, 120),
            "steady",
            14,
            halo=(px, py, 12 * canvas.s + 1, 13 * canvas.s + 1, 0.3),
        )
        self.shelter = (canvas.x(x0), min(canvas.w, canvas.x(x1)), canvas.y(CANOPY_TOP), canvas.y(feet))
        self.drips = [
            (min(canvas.w - 1, canvas.x(x0 + (x1 - x0) * f)), 23 + 7 * i, 5 * i * 3)
            for i, f in enumerate((0.05, 0.35, 0.65, 0.95))
        ]

    def _bench(self, feet: float) -> None:
        """The bench K sits on, sized to his sprite's seat."""
        canvas = self.canvas
        height, ground = max(3, round(SEAT_HEIGHT * self.k_scale)), canvas.y(feet)
        bx0, bx1 = canvas.x(BENCH_X0), canvas.x(BENCH_X1)
        for y in range(ground - height, ground):
            for x in range(bx0, bx1):
                if y == ground - height:
                    color = (118, 90, 152)
                elif y == ground - 1 or x in (bx0, bx1 - 1):
                    color = (18, 10, 30)
                else:
                    color = (44, 30, 66)
                canvas.plot(x, y, color)

    def roof_span(self, y: int) -> tuple[int, int] | None:
        """Columns the canopy roof covers on row y: the top face narrows toward the back and the front eave is
        straight (the same measurements as _build). Outside the roof, None."""
        canvas = self.canvas
        yr = canvas.ref_y(y + 0.5)
        if not CANOPY_TOP <= yr < CANOPY_EAVE:
            return None
        inset = (CANOPY_EAVE - 2 - yr) * 0.7 if yr < CANOPY_EAVE - 2 else -1
        return canvas.x(CANOPY_X0 + inset), min(canvas.w, canvas.x(CANOPY_X1 - inset) + 1)

    def shelters(self, x: int, y: int) -> bool:
        """Whether the pixel is inside K's canopy (from its roof down to its floor), where it doesn't rain."""
        x0, x1, top, bottom = self.shelter
        return x0 <= x < x1 and top <= y <= bottom

    def paint(self, frame: Frame, tick: int) -> None:
        """Water dripping from the canopy roof's eave down to the floor."""
        canvas = self.canvas
        eave = canvas.y(CANOPY_EAVE)
        feet = canvas.y(K_FEET_Y)
        for x, period, phase in self.drips:
            p = (tick + phase) % period
            y = eave + int(p * 1.6 * max(1.0, canvas.s))
            if y < feet and 0 <= x < canvas.w:
                for dy in range(2):
                    if 0 <= y - dy < canvas.h:
                        frame[y - dy][x] = blend(frame[y - dy][x], RAIN_FAR, 0.6 - 0.25 * dy)
            elif y == feet and 0 <= x < canvas.w - 1:
                row = frame[min(feet, canvas.h - 1)]
                row[x] = blend(row[x], DRIP_SPLASH_COLOR, 0.35)
