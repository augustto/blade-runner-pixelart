"""K on the rooftop: smokes sitting under a canopy, leaves the cigarette on the shelf, walks to JOI, talks, and
comes back.

The loop (everything is a function of the tick, so it survives terminal resizes):
  smoke     seated on the bench facing JOI, taking drags, for 60 s (on the first lap, lighting up first)
  leave     rests the cigarette on the shelf, where it keeps burning and smoking
  stand     gets up from the bench
  go        walks to the edge of the roof
  talk      60 s beside JOI
  back      walks back to the canopy
  sit       sits down again
  take      picks the cigarette up from the shelf and goes back to smoking
"""

from __future__ import annotations

import random
from typing import NamedTuple

from modules.characters.k.sprites import CROUCH, LIFT
from modules.core.timing import ticks

SMOKE_S, LEAVE_S, STAND_S, GO_S, TALK_S, BACK_S, SIT_S, TAKE_S = 60, 1.2, 0.8, 6, 60, 6, 0.8, 1.2
FIRST_FLAME_S = 1.5
DRAG_S = 6.3
SMOKE_FRAMES = 26
SEATED_X, NEAR_X = 182, 108

PHASES = tuple(ticks(s) for s in (SMOKE_S, LEAVE_S, STAND_S, GO_S, TALK_S, BACK_S, SIT_S, TAKE_S))
CYCLE = sum(PHASES)

WIND_SHAPES = (1, 2)
FRAMES_PER_SHAPE = 2


def wind(tick: int) -> int:
    """Gusts that make the coat's hem flutter, quickly, for 3 s every minute (a function of the tick)."""
    slot, t = divmod(tick, 60)
    if random.Random(slot * 104729 + 11).random() < 0.5 and 10 <= t < 40:
        return WIND_SHAPES[t // FRAMES_PER_SHAPE % len(WIND_SHAPES)]
    return 0


class State(NamedTuple):
    pose: str
    x: float
    detail: int = 0
    wind: int = 0
    mirrored: bool = False
    arm: str = "free"
    ember: float = 0.0
    on_shelf: bool = True
    smoke: int | None = None


def _drags(t: int, first_lap: bool) -> tuple[str, float, int | None]:
    """(arm, ember, smoke) on the bench: rests with the cigarette on his lap, raises it, drags, and exhales."""
    flame = ticks(FIRST_FLAME_S) if first_lap else 0
    if t < flame:
        return "lighting", 0.15 + 0.5 * t / max(1, flame), None
    period = ticks(DRAG_S)
    lap, u = divmod(t - flame, period)
    if u >= 27:
        smoke = u - 27
    elif lap > 0 and u + period - 27 < SMOKE_FRAMES:
        smoke = u + period - 27
    else:
        smoke = None
    if u < 9 or u >= 33:
        return "resting", 0.25, smoke
    if u < 12:
        return LIFT[u - 9], 0.25, smoke
    if u >= 30:
        return LIFT[32 - u], 0.3, smoke
    if u < 15:
        return "drag", 0.3, smoke
    if u < 27:
        pull = (u - 15) / 12
        return "drag", 0.3 + 0.7 * (1 - abs(2 * pull - 1)), smoke
    return "drag", 0.35, smoke


def state(tick: int) -> State:
    """What K is doing on this tick: pose, position, arm, cigarette and smoke."""
    t = tick % CYCLE
    smoke, leave, stand, go, talk, back, sit, take = PHASES

    if t < smoke:
        arm, ember, puff = _drags(t, first_lap=tick < CYCLE)
        return State("seated", SEATED_X, arm=arm, ember=ember, on_shelf=False, smoke=puff)
    t -= smoke
    if t < leave:
        return State("seated", SEATED_X, arm="reaching" if t < leave - 3 else "free", on_shelf=t >= 4)
    t -= leave
    if t < stand:
        return State("standing", SEATED_X, detail=round(CROUCH * (1 - t / stand)))
    t -= stand
    if t < go:
        return State("walking", SEATED_X + (NEAR_X - SEATED_X) * t / go, detail=t // 3 % 2)
    t -= go
    if t < talk:
        return State("standing", NEAR_X, wind=wind(tick))
    t -= talk
    if t < back:
        return State("walking", NEAR_X + (SEATED_X - NEAR_X) * t / back, detail=t // 3 % 2, mirrored=True)
    t -= back
    if t < sit:
        return State("standing", SEATED_X, detail=round(CROUCH * t / sit))
    t -= sit
    if t < take // 2:
        return State("seated", SEATED_X, arm="reaching")
    return State("seated", SEATED_X, arm="drag", ember=0.5, on_shelf=False)
