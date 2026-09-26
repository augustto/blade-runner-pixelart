"""Small effects several layers paint every frame: puffs of smoke or steam, and points of light with a halo."""

from __future__ import annotations

import math

from modules.core.color import Color, Frame
from modules.graphics.canvas import Canvas

SMOKE_COLOR: Color = (206, 200, 226)


def puff(canvas: Canvas, frame: Frame, cx: float, cy: float, radius: float, alpha: float) -> None:
    """A soft round puff of smoke, stronger in the middle."""
    if alpha <= 0.02:
        return
    r = max(0.6, radius)
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = math.hypot(x - cx, y - cy) / r
            if d <= 1:
                canvas.blend_at(frame, x, y, SMOKE_COLOR, alpha * (1 - d * 0.6))


def wisp(canvas: Canvas, frame: Frame, tick: int, x: int, y: int, alpha: float, b: int) -> None:
    """A wisp of smoke: three particles in different phases, rising slowly and swaying."""
    for j in range(3):
        age = (tick + j * 12) % 36
        puff(
            canvas,
            frame,
            x + math.sin(age * 0.35 + j) * b - age * 0.06 * b,
            y - 1 - age * 0.25 * b,
            b * 0.6,
            alpha * (1 - age / 36),
        )


def light_point(canvas: Canvas, frame: Frame, x: int, y: int, color: Color, alpha: float, radius: int) -> None:
    """A pixel of light with a halo of the given radius around it (the blend falls off with distance)."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d = math.hypot(dx, dy)
            if d <= radius:
                canvas.blend_at(frame, x + dx, y + dy, color, alpha * (1 - d / (radius + 1)) if d else 1.0)
