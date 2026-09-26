"""Sprites as color grids (None is transparent) and how to rescale them to the terminal."""

from __future__ import annotations

from collections.abc import Callable

from modules.core.color import Color

Grid = list[list[Color | None]]


def resize(grid: Grid, factor: float, highlight: Callable[[Color], bool] | None = None) -> Grid:
    """Rescales a sprite: each new pixel is the average of the block it covers.

    The pixel is left empty if less than half the block has color; when enlarging, each block is a single
    pixel (nearest neighbor) and the result stays blocky. With highlight, a color that passes the test wins
    over the average: without it the lit face and edge of a small sprite get lost in the surrounding dark.
    """
    height, width = len(grid), len(grid[0])
    new_height, new_width = max(1, round(height * factor)), max(1, round(width * factor))
    out: Grid = []
    for ty in range(new_height):
        y0 = ty * height // new_height
        y1 = max(y0 + 1, (ty + 1) * height // new_height)
        row: list[Color | None] = []
        for tx in range(new_width):
            x0 = tx * width // new_width
            x1 = max(x0 + 1, (tx + 1) * width // new_width)
            block = [grid[y][x] for y in range(y0, y1) for x in range(x0, x1)]
            filled = [c for c in block if c is not None]
            bright = [c for c in filled if highlight and highlight(c)]
            if 2 * len(filled) < len(block):
                row.append(None)
            elif bright:
                row.append(bright[0])
            else:
                row.append(tuple(sum(c[i] for c in filled) // len(filled) for i in range(3)))
        out.append(row)
    return out
