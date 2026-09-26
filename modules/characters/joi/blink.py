"""JOI's blink: the eye pixels in the sprite (sprite.py) and when they close.

The sprite is fixed, so blinking means swapping the open eye for an eyelid: skin covers the eye and a dark
lash line shows up a little below it. Each logical sprite row takes up two pixel rows.
"""

from __future__ import annotations

from modules.core.timing import seeded

PERIOD = 30
CHANCE = 0.75
CLOSED_FRAMES = 2

SKIN = {(26, 58): "W", (26, 59): "W", (28, 64): "W"}
LASHES = {(28, 58): "f", (28, 59): "j", (30, 64): "f"}


def close_eyes(rows: tuple[str, ...]) -> tuple[str, ...]:
    """The sprite with its eyes closed (each swap applies to the sprite's pair of rows)."""
    swaps = {**SKIN, **LASHES}
    out = []
    for y, row in enumerate(rows):
        for (sy, x), letter in swaps.items():
            if y // 2 == sy // 2:
                row = row[:x] + letter + row[x + 1 :]
        out.append(row)
    return tuple(out)


def is_blinking(tick: int) -> bool:
    """Are the eyes closed on this frame? Sometimes the blink comes as a double."""
    t, rng = seeded(tick, PERIOD, 3)
    if rng.random() >= CHANCE:
        return False
    if rng.random() < 0.15:
        start = rng.randint(0, PERIOD - 2 * CLOSED_FRAMES - 2)
        second = start + CLOSED_FRAMES + 2
        return start <= t < start + CLOSED_FRAMES or second <= t < second + CLOSED_FRAMES
    start = rng.randint(0, PERIOD - CLOSED_FRAMES)
    return start <= t < start + CLOSED_FRAMES
