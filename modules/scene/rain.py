"""The rain: drops at two depths falling diagonally with the wind, that splash on the canopy roof, on the wet
floor or in the puddles (where they open ripples), or vanish into the fog. It never rains under the canopy.

Every drop is rolled once per terminal size; where it is on a frame is a function of the tick.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

from modules.core.color import Color, Frame, blend
from modules.graphics.canvas import Canvas
from modules.scene.canopy import Canopy
from modules.scene.layout import (
    CANOPY_EAVE,
    CANOPY_TOP,
    CANOPY_X0,
    CANOPY_X1,
    FLOOR_Y,
    RAIN_FAR,
    RAIN_NEAR,
    floor_edge_px,
)
from modules.scene.puddles import Puddles, Ripple

SPLASH_COLOR = (215, 220, 255)
RAIN_SLANT = 0.5
DROPLETS = ((-2.0, -4.5), (-0.7, -5.5), (0.7, -5.5), (2.0, -4.5))
ROOF_SPLASH_FRAMES = 6
FLOOR_RIPPLES = ((0, 0.30), (1, 0.22), (2, 0.15), (3, 0.08))
FLOOR_SPLASH_FRAMES = len(FLOOR_RIPPLES)
PUDDLE_SPLASH_FRAMES = 14
SPLASH_FRAMES = {"roof": ROOF_SPLASH_FRAMES, "floor": FLOOR_SPLASH_FRAMES, "puddle": PUDDLE_SPLASH_FRAMES}


def rain_drift(rows: float) -> int:
    """Columns a drop has moved after falling that many rows. Always rounds halves up: with Python's round()
    (half to even) the steps came out uneven and the streak looked broken."""
    return math.floor(rows * RAIN_SLANT + 0.5)


@dataclass(frozen=True)
class Drop:
    """A raindrop: falls down to land_y, slanted by the wind, and splashes there (on the canopy roof, the floor
    or a puddle) or vanishes."""

    x: int
    land_y: int
    speed: int
    length: int
    phase: int
    color: Color
    alpha: float
    impact: str | None
    fall_frames: int
    period: int


class Rain:
    def __init__(self, canvas: Canvas, canopy: Canopy, puddles: Puddles, rng: random.Random) -> None:
        self.canvas = canvas
        self.canopy = canopy
        self.puddles = puddles
        self.drops: list[Drop] = []
        self._build(rng)

    def _build(self, rng: random.Random) -> None:
        """Drops at two depths: the near ones fall faster, longer and brighter.

        They fall diagonally, so the starting column comes from behind: we roll the column x_end where the drop
        reaches the floor (or the bottom of the screen) and derive the start from it, which covers the whole
        screen, including the bottom-left corner, which only drops that started off-screen reach. A drop that
        crosses the canopy roof stops there and splashes; one that reaches the building's roof floor (right of
        the diagonal edge) splashes there; the rest vanish into the fog.
        """
        canvas = self.canvas
        floor = canvas.y(FLOOR_Y)
        for _ in range(int(canvas.w * canvas.h / 190)):
            x_end = rng.randrange(canvas.w)
            land_y = rng.randint(canvas.y(FLOOR_Y + 3), canvas.h - 2)
            on_floor = x_end >= floor_edge_px(canvas, land_y)
            if not on_floor:
                land_y = canvas.h + 8
            depth = (land_y - floor) / max(1, canvas.h - floor) if on_floor else rng.random()
            speed = 2 + round(depth * 2)
            x = x_end - rain_drift(land_y)
            impact = None
            roof_row = self._roof_hit(x, land_y, rng)
            if roof_row is not None:
                land_y, impact = roof_row, "roof"
            elif on_floor and not self.canopy.shelters(x_end, land_y):
                impact = "puddle" if self.puddles.mask.get((x_end, land_y), (0,))[0] > 0.3 else "floor"
            fall_frames = math.ceil((land_y + 1) / speed)
            self.drops.append(
                Drop(
                    x=x,
                    land_y=land_y,
                    speed=speed,
                    length=3 + round(depth * 4),
                    phase=rng.randrange(400),
                    color=RAIN_NEAR if x_end < canvas.x(130) else RAIN_FAR,
                    alpha=0.25 + 0.4 * depth,
                    impact=impact,
                    fall_frames=fall_frames,
                    period=fall_frames + SPLASH_FRAMES.get(impact, 0) + rng.randint(0, 24),
                )
            )
        rows = range(canvas.y(CANOPY_TOP), canvas.y(CANOPY_EAVE))
        for _ in range(4 + (canvas.x(CANOPY_X1) - canvas.x(CANOPY_X0)) // 5):
            land_y = rng.choice(rows)
            span = self.canopy.roof_span(land_y)
            if span is None or span[1] <= span[0]:
                continue
            fall_frames = math.ceil((land_y + 1) / 3)
            self.drops.append(
                Drop(
                    x=rng.randrange(*span) - rain_drift(land_y),
                    land_y=land_y,
                    speed=3,
                    length=4,
                    phase=rng.randrange(400),
                    color=RAIN_NEAR,
                    alpha=0.6,
                    impact="roof",
                    fall_frames=fall_frames,
                    period=fall_frames + ROOF_SPLASH_FRAMES + rng.randint(6, 40),
                )
            )
        targets = [p for p, (m, *_) in self.puddles.mask.items() if m > 0.5]
        for _ in range(6 + len(targets) // 100 if targets else 0):
            x_end, land_y = rng.choice(targets)
            fall_frames = math.ceil((land_y + 1) / 3)
            self.drops.append(
                Drop(
                    x=x_end - rain_drift(land_y),
                    land_y=land_y,
                    speed=3,
                    length=4,
                    phase=rng.randrange(400),
                    color=RAIN_NEAR,
                    alpha=0.5,
                    impact="puddle",
                    fall_frames=fall_frames,
                    period=fall_frames + PUDDLE_SPLASH_FRAMES + rng.randint(6, 30),
                )
            )

    def _roof_hit(self, x: int, land_y: int, rng: random.Random) -> int | None:
        """Row where the drop (at column x on row 0, slanted by the wind) hits the roof, if it crosses it before
        reaching land_y. The roof is a sheet seen from above, so the drop can hit any of its rows."""
        rows = []
        for y in range(self.canvas.y(CANOPY_TOP), min(land_y, self.canvas.y(CANOPY_EAVE) - 1) + 1):
            span = self.canopy.roof_span(y)
            if span and span[0] <= x + rain_drift(y) < span[1]:
                rows.append(y)
        return rng.choice(rows) if rows else None

    def paint(self, frame: Frame, tick: int) -> None:
        """The falling streaks and the splashes on the roof and the floor (puddle rings are ripples())."""
        canvas = self.canvas
        b = canvas.block
        for drop in self.drops:
            p = (tick + drop.phase) % drop.period
            if p < drop.fall_frames:
                head = p * drop.speed
                for i in range(drop.length):
                    y = head - i
                    if 0 <= y < canvas.h and y <= drop.land_y:
                        x = drop.x + rain_drift(y)
                        if 0 <= x < canvas.w:
                            if drop.impact != "roof" and self.canopy.shelters(x, y):
                                continue
                            frame[y][x] = blend(frame[y][x], drop.color, drop.alpha * (1 - i / drop.length))
            elif drop.impact == "roof" and p - drop.fall_frames < ROOF_SPLASH_FRAMES:
                self._roof_splash(frame, drop, p - drop.fall_frames, b)
            elif drop.impact == "floor" and p - drop.fall_frames < FLOOR_SPLASH_FRAMES:
                self._floor_splash(frame, drop, p - drop.fall_frames, b)

    def _roof_splash(self, frame: Frame, drop: Drop, t: int, b: int) -> None:
        """A drop that hit the roof: a flat flash at the impact and droplets that bounce up and fall back onto
        the sheet."""
        x0 = drop.x + rain_drift(drop.land_y)
        fade = 1 - t / ROOF_SPLASH_FRAMES
        if t < 3:
            for dx in range(-(t + 1) * b, (t + 1) * b + 1):
                self.canvas.blend_at(frame, x0 + dx, drop.land_y, SPLASH_COLOR, 0.6 * fade)
        self._droplets(frame, drop, t, b, 0.75 * fade)

    def _floor_splash(self, frame: Frame, drop: Drop, t: int, b: int) -> None:
        """A drop that hit the wet floor: just a faint, flat ripple that opens and fades."""
        canvas = self.canvas
        x0 = drop.x + rain_drift(drop.land_y)
        radius, strength = FLOOR_RIPPLES[t]
        radius *= b
        for dx in range(-radius, radius + 1):
            dy = round(0.5 * math.sqrt(max(0, radius * radius - dx * dx)))
            for y in {drop.land_y - dy, drop.land_y + dy}:
                x = x0 + dx
                if 0 <= y < canvas.h and x >= floor_edge_px(canvas, y):
                    canvas.blend_at(frame, x, y, RAIN_FAR, strength)

    def _droplets(self, frame: Frame, drop: Drop, t: int, b: int, alpha: float) -> None:
        """Droplets (vx, vy) thrown from the roof impact: they rise, fall back, and vanish on reaching the
        sheet again."""
        x0 = drop.x + rain_drift(drop.land_y)
        step = t + 1
        jitter = (drop.phase % 3 - 1) * 0.3
        for vx, vy in DROPLETS:
            dy = (vy * step * 0.4 + 0.35 * step * step) * b
            if dy > 0:
                continue
            x = x0 + round((vx + jitter) * step * 0.5 * b)
            self.canvas.blend_at(frame, x, drop.land_y + round(dy), SPLASH_COLOR, alpha)

    def ripples(self, tick: int) -> list[Ripple]:
        """The ripples drops open in the puddles on this frame: (x, y, radius, strength), the ring growing and
        weakening."""
        b = self.canvas.block
        ripples = []
        for drop in self.drops:
            if drop.impact == "puddle":
                t = (tick + drop.phase) % drop.period - drop.fall_frames
                if 0 <= t < PUDDLE_SPLASH_FRAMES:
                    x = drop.x + rain_drift(drop.land_y)
                    ripples.append((x, drop.land_y, (1 + t * 0.45) * b, (1 - t / PUDDLE_SPLASH_FRAMES) ** 1.4))
        return ripples
