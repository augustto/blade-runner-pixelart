"""ANSI encoding: each terminal row holds 2 pixels (the top one is the "▀" foreground color, the bottom one is the
background)."""

from __future__ import annotations

from functools import lru_cache

from modules.core.color import Color

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_SCREEN = "\033[2J"
HOME_AND_CLEAR = "\033[H\033[J"
BEGIN_SYNC = "\033[?2026h"
END_SYNC = "\033[?2026l"


@lru_cache(maxsize=65536)
def fg_code(color: Color) -> str:
    return f"\033[38;2;{color[0]};{color[1]};{color[2]}m"


@lru_cache(maxsize=65536)
def bg_code(color: Color) -> str:
    return f"\033[48;2;{color[0]};{color[1]};{color[2]}m"


def move_to(row: int) -> str:
    """Cursor to the start of the given terminal row (0-based)."""
    return f"\033[{row + 1};1H"


def ansi_row(top: list[Color], bottom: list[Color]) -> str:
    """One terminal row built from two pixel rows.

    A color code is only emitted when the color changes: the background is mostly a smooth gradient, so this
    cuts a good share of each frame's bytes.
    """
    parts: list[str] = []
    fg = bg = None
    for t, b in zip(top, bottom):
        if t != fg:
            parts.append(fg_code(t))
            fg = t
        if b != bg:
            parts.append(bg_code(b))
            bg = b
        parts.append("▀")
    parts.append(RESET)
    return "".join(parts)
