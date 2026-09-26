"""The terminal as an output device: writes frames, redrawing only the rows that changed."""

from __future__ import annotations

import sys

from modules.core.color import Color, Frame
from modules.terminal.ansi import (
    BEGIN_SYNC,
    CLEAR_SCREEN,
    END_SYNC,
    HIDE_CURSOR,
    HOME_AND_CLEAR,
    RESET,
    SHOW_CURSOR,
    ansi_row,
    move_to,
)


class Screen:
    """Writes frames to the terminal, redrawing only the rows that changed. Synchronized output avoids flicker."""

    def __init__(self) -> None:
        self.previous: list[tuple[list[Color], list[Color]]] = []

    def open(self) -> None:
        self._write(HIDE_CURSOR)

    def close(self) -> None:
        self._write(HOME_AND_CLEAR + RESET + SHOW_CURSOR)

    def clear(self) -> None:
        self.previous = []
        sys.stdout.write(CLEAR_SCREEN)

    def draw(self, frame: Frame) -> None:
        pairs = [(frame[y], frame[y + 1]) for y in range(0, len(frame) - 1, 2)]
        out = [BEGIN_SYNC]
        for i, (top, bottom) in enumerate(pairs):
            if i < len(self.previous) and self.previous[i] == (top, bottom):
                continue
            out.append(move_to(i) + ansi_row(top, bottom))
        out.append(END_SYNC)
        self._write("".join(out))
        self.previous = pairs

    def message(self, text: str, columns: int, rows: int) -> None:
        """Text centered on an otherwise empty screen."""
        self._write(HOME_AND_CLEAR + "\n" * (rows // 2) + text.center(columns)[:columns])

    @staticmethod
    def _write(text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()
