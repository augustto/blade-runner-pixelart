"""K's sprites: letters that index into PALETTE ("." is transparent).

Standing K sprites are 11 pixels wide at the reference frame's scale (200x83), where he is 22 tall, and face
left, toward JOI: only the side turned to her catches the hologram's magenta light (face and coat edge). When
he walks to the right the sprite is mirrored and the light still comes from the left, so the face falls into
shadow and the bright edge moves to his back. Seated he faces the screen (13 pixels wide, 15 tall).
"""

from __future__ import annotations

from modules.core.color import Color

PALETTE: dict[str, Color] = {
    "F": (236, 72, 160),
    "f": (148, 42, 122),
    "n": (206, 62, 142),
    "d": (116, 32, 100),
    "h": (34, 18, 52),
    "r": (128, 40, 136),
    "C": (30, 17, 46),
    "c": (21, 12, 35),
    "L": (18, 10, 30),
    "S": (10, 6, 18),
    "i": (168, 158, 156),
    "E": (215, 100, 48),
    "Y": (255, 214, 90),
    "y": (255, 240, 170),
}

HEAD = (
    "..hhhh.....",
    "..Fhhh.....",
    "..nfhh.....",
    "...dhh.....",
)
COAT = ("..rCCCc....",) * 14
LEGS = (
    ("...L.L.....", "...L.L.....", "...L.L.....", "..SL.LS...."),
    ("..L..L.....", ".L....L....", ".L....L....", "SL....LS..."),
    ("...LL......", "...LL......", "...LL......", "..SLLS......"),
)
COAT_FLAPS = (
    (),
    ((16, 7), (17, 7), (17, 8)),
    ((15, 7), (16, 7), (16, 8), (17, 7), (17, 8), (17, 9)),
)
CROUCH_ROW = 12

SEATED = (
    "..hhhh.....",
    "..Fhhh.....",
    "..nfhh.....",
    "...dhh.....",
    "..rCCCc....",
    "..rCCCc....",
    "..rCCCc....",
    "..rCCCc....",
    "..rCCCCc...",
    "LLLLLLCCc..",
    "LL.........",
    "LL.........",
    "LL.........",
    "SS.........",
)
SEAT_HEIGHT = 4
MOUTH = (2, 2)
CROUCH = 6


def mirror(rows: list[str]) -> list[str]:
    """Turns the sprite to face right: the light comes from the left, so the face goes dark and the edge
    switches sides."""
    swap = str.maketrans("rcFfhnd", "crfhhfh")
    return [row[::-1].translate(swap) for row in rows]


LIFT = ("lift1", "lift2", "lift3")
LIFT_PIXELS = {
    "lift1": ((1, 5, "C"), (1, 6, "C"), (1, 7, "F"), (0, 7, "i")),
    "lift2": ((1, 4, "C"), (1, 5, "C"), (1, 6, "C"), (0, 6, "F"), (0, 5, "i")),
    "lift3": ((1, 4, "C"), (1, 5, "C"), (1, 6, "C"), (0, 5, "C"), (0, 4, "F"), (0, 3, "i")),
}
# In these poses the ember sticks out one column in front of the sprite, so it is not painted in it.
LIFT_EMBER = {"lift1": (-1, 7), "lift2": (-1, 5), "lift3": (-1, 3)}


def _seated(arm: str) -> tuple[str, ...]:
    """K seated in profile, with his arm in one of these poses: "free" (hand on the knee), "resting"
    (cigarette in hand, lying across the lap), "lift1".."lift3" (the hand swinging forward and up, on the way
    to the mouth and back), "drag" (hand raised to the mouth, the ember at its tip), "lighting" (the lighter's
    flame) or "reaching" (arm stretched forward, to the shelf)."""
    rows = [list(row) for row in SEATED]

    def paint(x: int, y: int, letter: str) -> None:
        rows[y][x] = letter

    for y in range(5, 8):
        paint(1, y, "C")
    paint(1, 8, "F")
    if arm == "resting":
        paint(2, 8, "F")
        paint(1, 8, "i")
        paint(0, 8, "E")
    elif arm in LIFT:
        for y in range(4, 9):
            paint(1, y, ".")
        for x, y, letter in LIFT_PIXELS[arm]:
            paint(x, y, letter)
    elif arm in ("drag", "lighting"):
        for y in range(4, 9):
            paint(1, y, "C")
        paint(1, 3, "F")
        paint(1, 2, "i")
        if arm == "lighting":
            paint(0, 2, "Y")
            paint(0, 1, "y")
        else:
            paint(0, 2, "E")
    elif arm == "reaching":
        for y in (6, 7, 8):
            paint(1, y, ".")
        paint(1, 4, "C")
        paint(1, 5, "C")
        paint(0, 5, "F")
    return tuple("".join(row) for row in rows)


def sprite(pose: str, detail: int = 0, wind: int = 0, mirrored: bool = False, arm: str = "free") -> tuple[str, ...]:
    """K's frame: pose "seated" (facing the screen; arm as in _seated), "standing" (detail: coat rows removed,
    to crouch; wind 0..2 lifts the coat's hem) or "walking" (detail 0 or 1: the two steps)."""
    if pose == "seated":
        return _seated(arm)
    legs = LEGS[0 if pose == "standing" else 1 + detail]
    rows = [list(row) for row in HEAD + COAT + legs]
    if pose == "standing":
        for y, x in COAT_FLAPS[wind]:
            rows[y][x] = "c"
        del rows[CROUCH_ROW : CROUCH_ROW + detail]
    out = ["".join(row) for row in rows]
    return tuple(mirror(out) if mirrored else out)


def ember_position(sprite_rows: tuple[str, ...]) -> tuple[int, int] | None:
    """(column, row) of the ember (or the flame) in the sprite, if the cigarette is visible."""
    for y, row in enumerate(sprite_rows):
        for x, letter in enumerate(row):
            if letter in "EY":
                return x, y
    return None
