#!/usr/bin/env python3
"""Draw a sakura blossom as ASCII art.

cemdenizexe's profile derives its ASCII portrait from a photo. This does the
same job for a cherry blossom, except the source is maths rather than an image,
so the script needs no Pillow, no font and no asset -- just Python.

The blossom is five notched petals around a stamen disc. Each output cell is
supersampled, coverage becomes a brightness, and brightness picks a character
off the ramp. Where two petals overlap the result is dimmed, which is what
gives the drawing its visible seams instead of one flat cloud.

Run:  python scripts/make_ascii.py
Out:  assets/ascii/sakura.txt
"""

from __future__ import annotations

from math import cos, sin, pi, hypot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "ascii" / "sakura.txt"

# Monospace cells are roughly twice as tall as they are wide, so the grid is
# about twice as wide as it is tall to keep the blossom round.
COLS, ROWS = 56, 27
SUPERSAMPLE = 3
EXTENT = 1.20          # world units mapped across the vertical axis

# Dark -> light. Index 0 is the densest character, and brightness is inverted
# below, so the brightest part of the flower gets the heaviest ink.
RAMP = "@&#W%G8P5SYJ?7*!~^:. "

PETALS = 5
PETAL_DIST = 0.60      # distance from the centre to each petal's own centre
PETAL_W = 0.40         # half-width of a petal
PETAL_H = 0.50         # half-length of a petal
PETAL_FALLOFF = 1.15   # higher = tighter, brighter petal core
NOTCH_R = 0.16         # the little dent in each petal tip
SEAM = 0.72            # how much to dim where two petals overlap
STAMEN_R = 0.15

# Petal 0 points straight up; the rest follow every 72 degrees.
_AXES = [(cos(-pi / 2 + k * 2 * pi / PETALS), sin(-pi / 2 + k * 2 * pi / PETALS))
         for k in range(PETALS)]


def brightness(x: float, y: float) -> float:
    """How lit up this point of the blossom is, 0 (empty) to 1 (brightest)."""
    values = []
    for ca, sa in _AXES:
        along = x * ca + y * sa          # along the petal axis
        across = -x * sa + y * ca        # perpendicular to it

        t = (across / PETAL_W) ** 2 + ((along - PETAL_DIST) / PETAL_H) ** 2
        if t > 1.0:
            continue
        # The notch at the tip is what makes a blossom read as sakura.
        if hypot(across, along - (PETAL_DIST + PETAL_H * 1.02)) < NOTCH_R:
            continue
        values.append(1.0 - t ** PETAL_FALLOFF)

    best = max(values) if values else 0.0
    if len(values) > 1:
        best *= SEAM                     # the shaded crease between two petals

    # The stamen cluster: the brightest thing in the drawing.
    r = hypot(x, y)
    if r < STAMEN_R:
        best = 1.0
    elif r < STAMEN_R * 1.8:
        best = max(best, 0.5)

    return min(1.0, best)


def render() -> list[str]:
    span_y = EXTENT * 2
    span_x = EXTENT * 2 * (COLS / ROWS) * 0.5   # 0.5 = monospace cell aspect
    n = len(RAMP)
    lines = []

    for row in range(ROWS):
        out = ""
        for col in range(COLS):
            total = 0.0
            for sy in range(SUPERSAMPLE):
                for sx in range(SUPERSAMPLE):
                    u = (col + (sx + 0.5) / SUPERSAMPLE) / COLS
                    v = (row + (sy + 0.5) / SUPERSAMPLE) / ROWS
                    total += brightness(-span_x / 2 + u * span_x,
                                        -span_y / 2 + v * span_y)
            value = total / (SUPERSAMPLE * SUPERSAMPLE)
            out += " " if value < 0.05 else RAMP[min(n - 1, int((1.0 - value) * (n - 1)))]
        lines.append(out.rstrip())
    return lines


def main() -> None:
    lines = render()
    # Trim blank rows top and bottom so the art sits tight in its panel.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {OUT.relative_to(ROOT)}  ({len(lines)} lines, "
          f"{max(len(line) for line in lines)} cols)")


if __name__ == "__main__":
    main()
