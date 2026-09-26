"""The render loop: asks the scene for a frame every tick and hands it to the screen.

The loop only depends on the Renderable protocol, so it knows nothing about what is being drawn.
"""

from __future__ import annotations

from collections.abc import Callable
import shutil
import time
from typing import Protocol

from modules.core.color import Frame
from modules.core.timing import FRAME_INTERVAL
from modules.terminal.screen import Screen

MIN_COLUMNS, MIN_ROWS = 60, 16


class Renderable(Protocol):
    def frame(self, tick: int) -> Frame: ...


def run_loop(make_scene: Callable[[int, int], Renderable]) -> None:
    """Runs the scene: make_scene(columns, height in pixels) returns an object with frame(tick).

    The scene is rebuilt whenever the terminal is resized. The cursor is hidden while running and the screen
    is cleared on exit (Ctrl+C).
    """
    screen = Screen()
    size = scene = None
    tick = 0
    screen.open()
    try:
        while True:
            start = time.monotonic()
            columns, rows = shutil.get_terminal_size(fallback=(80, 24))
            if (columns, rows) != size:
                size = (columns, rows)
                big_enough = columns >= MIN_COLUMNS and rows >= MIN_ROWS
                scene = make_scene(columns, rows * 2) if big_enough else None
                screen.clear()
            if scene is None:
                screen.message(f"enlarge the terminal: at least {MIN_COLUMNS}x{MIN_ROWS}", columns, rows)
            else:
                screen.draw(scene.frame(tick))
            tick += 1
            time.sleep(max(0.0, FRAME_INTERVAL - (time.monotonic() - start)))
    except KeyboardInterrupt:
        pass
    finally:
        screen.close()
