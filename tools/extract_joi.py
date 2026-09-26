#!/usr/bin/env python3
"""Extracts JOI's hologram from assets/joi.jpg and writes modules/characters/joi/sprite.py.

Usage (from the project root; requires ImageMagick):

    python3 tools/extract_joi.py

The film frame is reduced to 200x83 pixels (the resolution at which the hologram itself has ~1 pixel blocks),
what remains of the hologram is cut out with a brightness mask, and the colors are quantized into a small
palette. The program itself doesn't read the image: it only uses the sprite generated here.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SPRITE = ROOT / "modules" / "characters" / "joi" / "sprite.py"
WIDTH, HEIGHT = 200, 83
CUT_X = 105
THRESHOLD = 160
COLORS = 50
BODY_Y = 66
FILL_UNTIL_X = 12
WRIST_X, WRIST_Y = (70, 73), (52, 54)
CROWN_LEFT_Y, CROWN_RIGHT_Y = 30, 12
BACK_BLEND_Y = (4, 8)
BRIGHTEN = 1.15
GREEN = (0, 255, 0)
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

Color = tuple[int, int, int]
Pixel = tuple[int, int]


def magick(*args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(["magick", *args], input=stdin, check=True, capture_output=True).stdout


def read_ppm(data: bytes) -> list[list[Color]]:
    parts = data.split(b"\n", 3)
    width, height = map(int, parts[1].split())
    raw = parts[3]
    return [[tuple(raw[(y * width + x) * 3 : (y * width + x) * 3 + 3]) for x in range(width)] for y in range(height)]


def write_ppm(pixels: list[list[Color]]) -> bytes:
    body = b"".join(bytes(c) for row in pixels for c in row)
    return b"P6\n%d %d\n255\n" % (len(pixels[0]), len(pixels)) + body


def merge_rows(frame: list[list[Color]]) -> list[list[Color]]:
    """Removes the hologram's scanlines: each pair of rows becomes the average of the two, brightened."""
    merged = []
    for y in range(0, len(frame) - 1, 2):
        mean = [
            tuple(min(255, round((a[i] + b[i]) / 2 * BRIGHTEN)) for i in range(3))
            for a, b in zip(frame[y], frame[y + 1])
        ]
        merged += [mean, mean]
    return merged + [merged[-1]] * (len(frame) - len(merged))


def mask(frame: list[list[Color]]) -> list[list[bool]]:
    """Hologram pixels: strong brightness, without loose specks and without holes."""
    height = len(frame)
    strong = [[x < CUT_X and max(frame[y][x]) > THRESHOLD for x in range(WIDTH)] for y in range(height)]

    def neighbors(x: int, y: int):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < WIDTH and 0 <= y + dy < height:
                yield x + dx, y + dy

    # The largest connected blob of bright pixels is the hologram.
    seen: set[Pixel] = set()
    largest: set[Pixel] = set()
    for y0 in range(height):
        for x0 in range(WIDTH):
            if not strong[y0][x0] or (x0, y0) in seen:
                continue
            blob, queue = {(x0, y0)}, deque([(x0, y0)])
            seen.add((x0, y0))
            while queue:
                for n in neighbors(*queue.popleft()):
                    if strong[n[1]][n[0]] and n not in seen:
                        seen.add(n)
                        blob.add(n)
                        queue.append(n)
            if len(blob) > len(largest):
                largest = blob

    # Flood from the border: whatever it can't reach is inside the hologram, so holes get filled.
    border = {(x, y) for y in range(height) for x in range(WIDTH) if x in (0, WIDTH - 1) or y in (0, height - 1)}
    queue = deque(p for p in border if p not in largest)
    outside = set(queue)
    while queue:
        for n in neighbors(*queue.popleft()):
            if n not in largest and n not in outside:
                outside.add(n)
                queue.append(n)
    return [[(x, y) not in outside and x < CUT_X for x in range(WIDTH)] for y in range(height)]


def quantize(frame: list[list[Color]], inside: list[list[bool]]) -> list[list[Color | None]]:
    """Quantizes only the hologram's pixels; the rest of the frame becomes None."""
    cutout = [[frame[y][x] if inside[y][x] else GREEN for x in range(CUT_X)] for y in range(len(frame))]
    out = magick("ppm:-", "+dither", "-colors", str(COLORS + 1), "ppm:-", stdin=write_ppm(cutout))
    quantized = read_ppm(out)
    return [[quantized[y][x] if inside[y][x] else None for x in range(CUT_X)] for y in range(len(frame))]


def close_body(pixels: list[list[Color | None]]) -> list[list[Color | None]]:
    """Closes the gaps on the body's left edge: it leaves the frame on the left, with no cutouts.

    From the arm's height down, each row gets color from the frame's edge up to FILL_UNTIL_X; holes take
    the color of the nearest neighbor. The brightness mask left a jagged edge there. Only the left edge is
    touched: the rest (the hand, especially) stays as it came out of the film.
    """
    for y in range(BODY_Y, len(pixels)):
        row = pixels[y]
        filled = [x for x, color in enumerate(row) if color is not None]
        if not filled:
            continue
        first = filled[0]
        for x in range(min(filled[-1], FILL_UNTIL_X) + 1):
            if row[x] is None:
                row[x] = row[first] if x < first else row[x - 1]
    return pixels


def smooth_crown(pixels: list[list[Color | None]]) -> list[list[Color | None]]:
    """Smooths the outline of the top of the head, which came out of the film in big steps.

    The rows come in pairs (merge_rows), so the edge jumped several pixels every two rows. Each edge becomes
    a line through the middle of those pairs, averaged over its neighbors; the left one down to CROWN_LEFT_Y
    (where the hair leaves the frame), the right one only down to CROWN_RIGHT_Y (below it is the face).
    Pixels that grow take the color of the edge; holes inside the outline take the color on their left.
    """

    def edges(until: int, side: int) -> list[float]:
        knots = [(y + 0.5, [x for x, c in enumerate(pixels[y]) if c is not None][side]) for y in range(0, until, 2)]
        line = []
        for y in range(until):
            below = [k for k in knots if k[0] <= y] or knots[:1]
            above = [k for k in knots if k[0] > y] or knots[-1:]
            (ya, xa), (yb, xb) = below[-1], above[0]
            line.append(xa if ya == yb else xa + (xb - xa) * (y - ya) / (yb - ya))
        return [sum(line[max(0, y - 1) : y + 2]) / len(line[max(0, y - 1) : y + 2]) for y in range(until)]

    left, right = edges(CROWN_LEFT_Y, 0), edges(CROWN_RIGHT_Y, -1)
    for y in range(CROWN_LEFT_Y):
        row = pixels[y]
        filled = [x for x, color in enumerate(row) if color is not None]
        first, last = filled[0], filled[-1]
        start = round(left[y])
        end = round(right[y]) if y < CROWN_RIGHT_Y else last
        for x in range(first, last + 1):
            if row[x] is None:
                row[x] = row[x - 1]
        for x in range(min(start, first), max(end, last) + 1):
            if x < start or x > end:
                row[x] = None
            elif row[x] is None:
                row[x] = row[first] if x < first else row[last]
    return pixels


def smooth_back(pixels: list[list[Color | None]]) -> list[list[Color | None]]:
    """Takes the wave out of the back of the hair (the left edge, from the crown to where it leaves the frame).

    The outline went down almost straight and then opened up all at once, in an S. It becomes a parabola
    fitted to the edge, which bends only one way. At the top it blends with the crown's outline (between the
    rows of BACK_BLEND_Y), which the parabola would make wider.
    """
    edge = [[x for x, color in enumerate(pixels[y]) if color is not None][0] for y in range(CROWN_LEFT_Y)]
    sums = [sum(y**k for y in range(CROWN_LEFT_Y)) for k in range(5)]
    matrix = [[sums[i + j] for j in range(3)] + [sum(x * y**i for y, x in enumerate(edge))] for i in range(3)]
    for i in range(3):
        for k in range(i + 1, 3):
            f = matrix[k][i] / matrix[i][i]
            matrix[k] = [a - f * b for a, b in zip(matrix[k], matrix[i])]
    coef = [0.0] * 3
    for i in reversed(range(3)):
        coef[i] = (matrix[i][3] - sum(matrix[i][j] * coef[j] for j in range(i + 1, 3))) / matrix[i][i]
    top, bottom = BACK_BLEND_Y
    for y in range(CROWN_LEFT_Y):
        t = min(1.0, max(0.0, (y - top) / (bottom - top)))
        start = max(0, round((1 - t) * edge[y] + t * (coef[0] + coef[1] * y + coef[2] * y * y)))
        row, first = pixels[y], edge[y]
        for x in range(min(start, first), max(start, first)):
            row[x] = None if x < start else row[first]
    return pixels


def trim_wrist(pixels: list[list[Color | None]]) -> list[list[Color | None]]:
    """Removes the loose bump left on top of the arm, by the wrist (columns WRIST_X, rows WRIST_Y)."""
    for y in range(*WRIST_Y):
        for x in range(*WRIST_X):
            pixels[y][x] = None
    return pixels


def generate() -> str:
    data = magick(
        str(ROOT / "assets" / "joi.jpg"),
        "-crop", "1600x660+0+120",
        "+repage",
        "-filter", "box",
        "-resize", f"{WIDTH}x{HEIGHT}!",
        "-depth", "8",
        "ppm:-",
    )  # fmt: skip
    frame = merge_rows(read_ppm(data))
    pixels = trim_wrist(close_body(smooth_back(smooth_crown(quantize(frame, mask(frame))))))
    colors = sorted({c for row in pixels for c in row if c is not None}, key=lambda c: (sum(c), c))
    letter = {c: LETTERS[i] for i, c in enumerate(colors)}
    rows = ["".join(letter[c] if c else "." for c in row) for row in pixels]
    body = "\n".join(f'    "{row}",' for row in rows)
    palette = "\n".join(f'    "{letter[c]}": {c},' for c in colors)
    return f'''"""Giant JOI sprite, generated by tools/extract_joi.py (do not edit by hand).

Each row is {CUT_X} characters wide: "." is transparent and the letters index into PALETTE.
The sprite is at the scale of the film frame reduced to {WIDTH}x{HEIGHT} pixels and
touches the top-left corner.
"""

PALETTE = {{
{palette}
}}

ROWS = (
{body}
)
'''


if __name__ == "__main__":
    SPRITE.write_text(generate(), encoding="utf-8")
    print(f"{SPRITE.relative_to(ROOT)} written")
