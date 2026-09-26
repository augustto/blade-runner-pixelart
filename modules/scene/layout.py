"""Where things are, in reference coordinates (200x83), and the colors that several layers share.

The rooftop's left edge runs diagonally from the back wall's corner (EDGE_X, FLOOR_Y) down to the bottom of the
terminal; beyond it there is only the fog lit by JOI.
"""

from __future__ import annotations

from modules.core.color import Color
from modules.graphics.canvas import Canvas

EDGE_X = 113
FLOOR_Y = 55
EDGE_SLOPE = 0.6

K_FEET_Y = 74
K_MIN_SCALE = 0.7
CANOPY_X0, CANOPY_X1 = 172, 200
CANOPY_TOP, CANOPY_EAVE = 44, 49
BENCH_X0, BENCH_X1 = 185, 197
SHELF_X0, SHELF_X1, SHELF_Y = 173, 181, 66
CIGARETTE_X, CIGARETTE_Y = 176, 65

CYAN: Color = (70, 215, 235)
RED: Color = (255, 50, 60)
PINK: Color = (255, 70, 170)
TOKYO_NIGHT_BLUES: tuple[Color, ...] = ((122, 162, 247), (125, 207, 255), (42, 195, 222))
RAIN_NEAR: Color = (215, 175, 245)
RAIN_FAR: Color = (150, 165, 225)


def floor_edge(y: float) -> float:
    """Reference x of the rooftop's left edge at row y (from FLOOR_Y down)."""
    return EDGE_X - EDGE_SLOPE * (y - FLOOR_Y)


def floor_edge_px(canvas: Canvas, py: int) -> int:
    """Pixel x of the rooftop's left edge at pixel row py."""
    return canvas.x(floor_edge(canvas.ref_y(py)))


def k_scale(canvas: Canvas) -> float:
    """K's scale: he never gets smaller than this, or his sprite would turn into mush on small terminals."""
    return max(canvas.s, K_MIN_SCALE)
