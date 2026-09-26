"""Time is measured in ticks (frames): every animation is a function of the tick, so it survives resizes."""

from __future__ import annotations

import random

FRAME_INTERVAL = 0.1


def ticks(seconds: float) -> int:
    return round(seconds / FRAME_INTERVAL)


def seeded(tick: int, period: int, seed: int) -> tuple[int, random.Random]:
    """Frame within the period and a fixed RNG for that period: events that are a function of the tick."""
    slot, t = divmod(tick, period)
    return t, random.Random(slot * 1_000_003 + seed)
