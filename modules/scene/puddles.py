"""The puddles on the floor, which reflect JOI, the city and K.

Each puddle is an ellipse with a wobbly, soft edge (the water fades into the floor, with no outline). On the base
it only darkens and cools the floor; the reflection is painted every frame, over what is already on screen:

  - the middle puddle shows, upside down, a piece of JOI's hologram (the arm, the hand and the body) taken from
    the frame already painted, so the reflection pulses and has her scanlines and glitch;
  - the puddles at the bottom of the terminal show the skyline, fainter and blurrier: the windows, the signs
    and the passing ships become soft glints on the water;
  - K: whatever he steps on inside a puddle becomes a dark reflection just below his feet, fading with distance.

The reflection trembles slowly, like water, and is stronger on the far side of the puddle and weaker on the near
side, where the floor shows through. Rain falling into them opens ripples: soft rings that grow and fade, and
that bend the reflection as they pass. Each ripple is (x, y, radius, strength), in pixels, and the rain is the
one that rolls the drops.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from modules.core.color import Frame, blend
from modules.graphics.canvas import Canvas
from modules.graphics.sprite import Grid
from modules.scene.layout import FLOOR_Y, floor_edge

WATER_COLOR = (30, 26, 72)
SKY_COLOR = (70, 40, 112)
WATER_DEPTH_COLOR = (30, 34, 96)
RIM_GLOW_COLOR = (120, 100, 170)
RIPPLE_COLOR = (190, 190, 245)
FLATTEN = 0.4

Ripple = tuple[int, int, float, float]


@dataclass(frozen=True)
class PuddleSpec:
    """A puddle: center and radii (reference coordinates), where it takes its reflection from (the column
    offset, the row mirrored at its center and how much it stretches), the reflection's strength, how much of
    the fog shows at the back, the blur width (columns on each side) and the brightness gain of what it
    reflects (small lights vanish in the blur)."""

    x: float
    y: float
    rx: float
    ry: float
    look_x: float
    look_y: float
    stretch: float
    strength: float
    sky: float
    blur: int
    gain: float


def smoothstep(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Puddles:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas
        self.specs = self._specs()
        self.mask: dict[tuple[int, int], tuple[float, float, int]] = {}
        self._build()

    def _specs(self) -> tuple[PuddleSpec, ...]:
        """The middle puddle (reflects JOI) and, at the bottom of the terminal (above the footer railing, when
        there is one), two that reflect the city: a small one in the gap between the middle one and the right
        one, and the larger one on the right."""
        ground_end = self.canvas.bottom_ref - (14 if self.canvas.bottom_ref >= 96 else 0)
        return (
            PuddleSpec(130, 76, 35.1, 7.02, 45, 63, 1.1, 0.35, 0.28, 1, 1.0),
            PuddleSpec(162, ground_end - 3, 5.5, 2.6, 6, 40, 1.6, 0.33, 0.15, 2, 2.2),
            PuddleSpec(180, ground_end - 5, 13, 4.4, 0, 36, 1.6, 0.33, 0.15, 2, 2.2),
        )

    def _build(self) -> None:
        """Builds the puddle masks (self.mask: pixel -> (opacity, position from 0 at the back to 1 near the camera,
        puddle index)) and darkens the base underneath them."""
        canvas = self.canvas
        for i, spec in enumerate(self.specs):
            rx, ry = spec.rx * canvas.s, max(2.0, spec.ry * canvas.s)
            cx, cy = canvas.x(spec.x), canvas.y(spec.y)
            for y in range(max(0, int(cy - ry * 1.3)), min(canvas.h, int(cy + ry * 1.3) + 1)):
                yr = canvas.ref_y(y + 0.5)
                limit = canvas.x(floor_edge(yr)) + 4 + max(2, round((2 + (yr - FLOOR_Y) * 0.1) * canvas.s))
                for x in range(max(limit, int(cx - rx * 1.3)), min(canvas.w, int(cx + rx * 1.3) + 1)):
                    dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                    angle = math.atan2(dy, dx)
                    edge = (
                        1
                        + 0.10 * math.sin(3 * angle + 0.7 + i)
                        + 0.06 * math.sin(5 * angle + 2.1)
                        + 0.04 * math.sin(9 * angle)
                    )
                    m = smoothstep((1 - math.hypot(dx, dy) / edge) / 0.35)
                    if m < 0.03 or self.mask.get((x, y), (0,))[0] >= m:
                        continue
                    t = min(1.0, max(0.0, (dy + 1) / 2))
                    self.mask[(x, y)] = (m, t, i)
                    under = blend(canvas.base[y][x], WATER_COLOR, 0.6 * m)
                    under = blend(under, SKY_COLOR, spec.sky * m * (1 - t))
                    canvas.base[y][x] = blend(under, RIM_GLOW_COLOR, 0.10 * 4 * m * (1 - m) * (1 - 0.5 * t))

    def reflect(self, frame: Frame, tick: int, ripples: list[Ripple]) -> None:
        """Paints what the puddles reflect: the scene flipped vertically, stretched, shifted and blurred, with
        the water's tremble and bent by the rain's ripples."""
        canvas = self.canvas
        for (x, y), (m, t, i) in self.mask.items():
            spec = self.specs[i]
            yr = canvas.ref_y(y + 0.5)
            ys = canvas.y(spec.look_y - (yr - spec.y) * spec.stretch)
            if not 0 <= ys < canvas.h - 1:
                continue
            wave = math.sin(y * 0.9 + tick * 0.13) * 0.8 + math.sin(y * 2.3 - tick * 0.21 + x * 0.3) * 0.4
            for cx, cy, radius, strength in ripples:
                if abs(x - cx) <= radius + 4 and abs(y - cy) <= (radius + 4) * FLATTEN:
                    dist = math.hypot(x - cx, (y - cy) / FLATTEN) - radius
                    wave += strength * 2.0 * math.sin(dist * 1.6) * math.exp(-dist * dist / 4)
            xs = canvas.x((x + 0.5) / canvas.s - spec.look_x) + round(wave)
            total, weight = [0, 0, 0], 0
            for row in (ys, ys + 1):
                for d in range(-spec.blur, spec.blur + 1):
                    w = spec.blur + 1 - abs(d)
                    px = min(canvas.w - 1, max(0, xs + d))
                    for c, channel in enumerate(frame[row][px]):
                        total[c] += channel * w
                    weight += w
            reflected = tuple(min(255, int(c * spec.gain / weight)) for c in total)
            reflected = blend(reflected, WATER_DEPTH_COLOR, 0.12)
            frame[y][x] = blend(frame[y][x], reflected, m * (spec.strength + 0.5 * (1 - t)))

    def reflect_sprite(self, frame: Frame, tick: int, grid: Grid, left: int, feet: int) -> None:
        """A figure's reflection in the puddles (K's): the sprite flipped upside down from its feet, with the
        water's tremble, fading as it moves away."""
        height = len(grid)
        for dy, row in enumerate(grid):
            y = 2 * feet - 1 - (feet - height + dy)
            depth = (y - feet) / height
            if not 0 <= y < self.canvas.h:
                continue
            shift = round(math.sin(y * 0.8 + tick * 0.15) * 0.8)
            for dx, color in enumerate(row):
                x = left + dx + shift
                water = self.mask.get((x, y))
                if color is not None and water and 0 <= x < self.canvas.w:
                    frame[y][x] = blend(frame[y][x], color, min(1.0, water[0] * 0.6 * (1 - depth) ** 1.3))

    def paint_ripples(self, frame: Frame, ripples: list[Ripple]) -> None:
        """The drops' rings in the puddles: a soft light line (the blend falls off with distance from the ring),
        flattened by perspective, that only exists where there is water."""
        for cx, cy, radius, strength in ripples:
            half = (radius + 2) * FLATTEN
            for y in range(int(cy - half) - 1, int(cy + half) + 2):
                for x in range(int(cx - radius) - 2, int(cx + radius) + 3):
                    water = self.mask.get((x, y))
                    if not water:
                        continue
                    dist = abs(math.hypot(x - cx, (y - cy) / FLATTEN) - radius)
                    if dist < 1.4:
                        frame[y][x] = blend(frame[y][x], RIPPLE_COLOR, 0.42 * strength * (1 - dist / 1.4) * water[0])
