"""Colors and frames: a frame is a grid of RGB pixels, and everything that gets painted is a mix of colors."""

from __future__ import annotations

from functools import cache
from itertools import pairwise

Color = tuple[int, int, int]
Frame = list[list[Color]]

BLACK: Color = (0, 0, 0)


def blend(a: Color, b: Color, t: float) -> Color:
    """Color between a (t=0) and b (t=1)."""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


@cache
def scale(color: Color, factor: float) -> Color:
    """Multiplies the color's brightness (factor > 1 brightens), capped at 255."""
    return (
        min(255, int(color[0] * factor)),
        min(255, int(color[1] * factor)),
        min(255, int(color[2] * factor)),
    )


def average(colors: list[Color]) -> Color:
    return tuple(sum(c[i] for c in colors) // len(colors) for i in range(3))


def interpolate(points, v: float):
    """Value (number or color) between the (position, value) points at position v."""
    if v <= points[0][0]:
        return points[0][1]
    for (x0, a), (x1, b) in pairwise(points):
        if v <= x1:
            t = (v - x0) / (x1 - x0)
            return blend(a, b, t) if isinstance(a, tuple) else a + (b - a) * t
    return points[-1][1]
