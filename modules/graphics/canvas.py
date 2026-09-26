"""Painting base: the pixel grid for the whole terminal, mapped to the film's reference frame, and blinking lights.

The film frame is 2.4:1 and is defined in reference coordinates (200x83 pixels). When the terminal is taller
than that (a window split in half, for instance) there is room left above and below; the scene fills it, and
reference coordinates then have negative y above the frame and y greater than 83 below it.

The base is painted once per terminal size; each frame starts as a copy of it, with the lights on top.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from modules.core.color import BLACK, Color, Frame, blend

REF_WIDTH = 200
ASPECT = 2.4
SPACE_ABOVE = 0.62

PATTERNS = {
    "steady": "1" * 44 + "0" + "1" + "0" + "1" * 14,
    "blink": "1" * 7 + "0" * 5,
    "faulty": "1" * 12 + "0101" + "1" * 3 + "0" * 10 + "10" + "11" + "0" * 8,
    "window": "1" * 70 + "0" * 50,
    "beacon": "1" * 4 + "0" * 8,
}

LightPixel = tuple[int, int, Color, Color]


@dataclass
class Light:
    """Pixels that switch between on and off, following a blink pattern."""

    pixels: list[LightPixel]
    pattern: str
    phase: int

    def is_on(self, tick: int) -> bool:
        cycle = PATTERNS[self.pattern]
        return cycle[(tick + self.phase) % len(cycle)] == "1"


class Canvas:
    """Pixel canvas for the whole terminal, scaled to the reference frame."""

    def __init__(self, columns: int, height: int) -> None:
        """columns x height in terminal pixels (2 pixels per text row)."""
        self.columns = columns
        self.w = min(columns, int(height * ASPECT))
        self.h = height
        self.ox = (columns - self.w) // 2
        self.s = self.w / REF_WIDTH
        self.core = min(height, round(self.w / ASPECT))
        self.dy = round((height - self.core) * SPACE_ABOVE)
        self.base: Frame = []
        self.lights: list[Light] = []

    @property
    def block(self) -> int:
        """Side, in pixels, of one "pixel" of a small sprite (letters, glyphs) at the current scale."""
        return max(1, round(self.s))

    @property
    def top_ref(self) -> float:
        """Reference coordinate of the terminal's top row (0 or negative)."""
        return -self.dy / self.s

    @property
    def bottom_ref(self) -> float:
        """Reference coordinate of the terminal's bottom row (83 or more)."""
        return (self.h - self.dy) / self.s

    # Coordinates.

    def x(self, v: float) -> int:
        """Pixel column of reference x."""
        return round(v * self.s)

    def y(self, v: float) -> int:
        """Pixel row of reference y."""
        return round(v * self.s) + self.dy

    def ref_y(self, py: float) -> float:
        """Reference y of pixel row py."""
        return (py - self.dy) / self.s

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    # Painting the base (once per size).

    def plot(self, x: int, y: int, color: Color, alpha: float = 1.0) -> None:
        if self.in_bounds(x, y):
            row = self.base[y]
            row[x] = color if alpha >= 1 else blend(row[x], color, alpha)

    def rect(self, x0: float, y0: float, x1: float, y1: float, color: Color, alpha: float = 1.0) -> None:
        """Rectangle in reference coordinates, at least 1 pixel on each side."""
        px0, py0 = self.x(x0), self.y(y0)
        px1, py1 = max(px0 + 1, self.x(x1)), max(py0 + 1, self.y(y1))
        for y in range(max(0, py0), min(self.h, py1)):
            for x in range(max(0, px0), min(self.w, px1)):
                self.plot(x, y, color, alpha)

    def glow(self, cx: float, cy: float, rx: float, ry: float, color: Color, on: float, off: float) -> list[LightPixel]:
        """Elliptical halo around (cx, cy), in pixels: the color blends with whatever is on the base."""
        pixels = []
        for y in range(max(0, int(cy - ry)), min(self.h, int(cy + ry) + 1)):
            for x in range(max(0, int(cx - rx)), min(self.w, int(cx + rx) + 1)):
                d = math.hypot((x - cx) / rx, (y - cy) / ry)
                if d < 1:
                    under = self.base[y][x]
                    strength = (1 - d) ** 2
                    pixels.append((x, y, blend(under, color, strength * on), blend(under, color, strength * off)))
        return pixels

    def add_light(
        self,
        points: list[tuple[int, int]],
        color: Color,
        pattern: str,
        phase: int,
        alpha: float = 1.0,
        off: float = 0.15,
        halo: tuple[float, float, float, float, float] | None = None,
    ) -> None:
        """Creates a light from the given (x, y) pixels; halo is (cx, cy, rx, ry, strength), in pixels."""
        pixels = self.glow(*halo[:4], color, halo[4], 0.0) if halo else []
        for x, y in points:
            if self.in_bounds(x, y):
                under = self.base[y][x]
                pixels.append((x, y, blend(under, color, alpha), blend(under, color, alpha * off)))
        if pixels:
            self.lights.append(Light(pixels, pattern, phase))

    # Painting a frame (every tick).

    def new_frame(self, tick: int) -> Frame:
        """A copy of the base with the lights as they are on this tick."""
        frame = [row[:] for row in self.base]
        for light in self.lights:
            on = light.is_on(tick)
            for x, y, lit, unlit in light.pixels:
                frame[y][x] = lit if on else unlit
        return frame

    def blend_at(self, frame: Frame, x: int, y: int, color: Color, alpha: float) -> None:
        """Blends color into the frame pixel (x, y), if it is on screen."""
        if self.in_bounds(x, y):
            frame[y][x] = blend(frame[y][x], color, alpha)

    def letterbox(self, frame: Frame) -> Frame:
        """The frame across the whole terminal width, with black bars on the sides if the terminal is too wide."""
        left, right = [BLACK] * self.ox, [BLACK] * (self.columns - self.w - self.ox)
        return [left + row + right for row in frame]
