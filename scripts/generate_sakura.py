#!/usr/bin/env python3
"""Render the ASCII blossom into an animated panel for the README.

Reads assets/ascii/sakura.txt (produced by make_ascii.py) and writes:

    assets/sakura/dark.svg
    assets/sakura/light.svg

Same rules as the banner: pure SMIL, no scripts, no external assets, and every
looping animation returns to its exact starting state.

Run:  python scripts/generate_sakura.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import (PAL, FONT, esc, esc_literal, reveal, gradient_defs,  # noqa: E402
                   window_chrome, write_svg)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets" / "ascii" / "sakura.txt"
OUT_DIR = ROOT / "assets" / "sakura"

W, H = 920, 486
PANEL = (26, 26, W - 52, H - 52)

ART_SIZE = 14                # font size of the blossom itself
ART_X, ART_TOP = 68, 92      # where the blossom sits
CHAR_W, LINE_H = 8.4, 15.8   # matched to ART_SIZE in the mono stack

NOTE_X = 534
NOTES = [
    ("bloom", "five petals, one commit at a time"),
    ("season", "always spring in the terminal"),
    ("made of", "maths, not a photo"),
]

PETAL_GLYPHS = ["&#10047;", "&#10048;", "&#183;", "&#42;"]   # ✿ ❀ · *


def art_lines() -> list[str]:
    if not ART.exists():
        raise SystemExit("assets/ascii/sakura.txt is missing -- run make_ascii.py first")
    return ART.read_text(encoding="utf-8").rstrip("\n").splitlines()


def defs(p: dict, mode: str) -> str:
    x, y, w, h = PANEL
    return (
        '<defs>' + gradient_defs(p, mode) +
        f'<clipPath id="panelClip"><rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'rx="18"/></clipPath></defs>'
    )


def background(p: dict) -> str:
    s = [f'<rect width="{W}" height="{H}" rx="24" fill="{p["bg"]}"/>',
         f'<rect width="{W}" height="{H}" rx="24" fill="url(#dots)"/>']
    s.append('<circle cx="230" cy="230" r="280" fill="url(#glowP)">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0;26 18;0 0" dur="16s" repeatCount="indefinite"/></circle>')
    s.append('<circle cx="740" cy="330" r="290" fill="url(#glowB)">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0;-22 -16;0 0" dur="19s" repeatCount="indefinite"/></circle>')
    s.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
             f'stroke="{p["border"]}" stroke-width="1.5"/>')
    s.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
             f'stroke="url(#shimmer)" stroke-width="1.5" opacity=".75"/>')
    return "".join(s)


def falling_petals(p: dict) -> str:
    """Petals drifting down inside the panel, on a loop with no visible restart.

    Each petal falls the full panel height in its own time and is offset by a
    fraction of that time, so at any moment the fall is evenly populated.
    """
    x0, y0, w, h = PANEL
    rng = random.Random(11)
    s = ['<g clip-path="url(#panelClip)">']
    for i in range(16):
        px = x0 + 18 + rng.randrange(0, w - 36)
        dur = 9 + rng.randrange(0, 90) / 10
        begin = -rng.randrange(0, int(dur * 10)) / 10      # negative = already falling
        size = 9 + rng.randrange(0, 6)
        sway = 14 + rng.randrange(0, 22)
        glyph = PETAL_GLYPHS[i % len(PETAL_GLYPHS)]
        colour = p["petal1"] if i % 3 else p["petal3"]
        s.append(
            f'<text x="{px}" y="{y0 - 20}" font-size="{size}" fill="{colour}" '
            f'opacity=".34" text-anchor="middle">{glyph}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;{sway} {h + 60};0 0" keyTimes="0;0.999;1" dur="{dur}s" '
            f'begin="{begin}s" repeatCount="indefinite" calcMode="linear"/>'
            f'<animate attributeName="opacity" values="0;.4;.4;0" '
            f'keyTimes="0;0.08;0.85;1" dur="{dur}s" begin="{begin}s" '
            f'repeatCount="indefinite"/></text>'
        )
    s.append('</g>')
    return "".join(s)


def blossom(p: dict, lines: list[str]) -> str:
    """The ASCII art itself: revealed row by row, then left to breathe."""
    width = max(len(line) for line in lines) * CHAR_W
    height = len(lines) * LINE_H
    cx = ART_X + width / 2
    cy = ART_TOP + height / 2

    s = [f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{width * 0.62:.0f}" '
         f'ry="{height * 0.72:.0f}" fill="url(#glowP)" filter="url(#soft)">'
         f'<animate attributeName="rx" values="{width * 0.62:.0f};{width * 0.68:.0f};'
         f'{width * 0.62:.0f}" dur="7s" repeatCount="indefinite"/></ellipse>']

    # A slow breath on the whole flower.
    s.append('<g><animateTransform attributeName="transform" type="translate" '
             'values="0 0;0 -5;0 0" dur="8s" repeatCount="indefinite" '
             'calcMode="spline" keyTimes="0;0.5;1" '
             'keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>')
    for i, line in enumerate(lines):
        # esc_literal, not esc: the ramp contains "&#", which the entity-aware
        # version would turn back into a broken entity and kill the whole SVG.
        text = esc_literal(line).replace(" ", "&#160;")
        s.append(
            f'<text x="{ART_X}" y="{ART_TOP + i * LINE_H:.0f}" font-size="{ART_SIZE}" '
            f'xml:space="preserve" fill="url(#sak)" filter="url(#tiny)" opacity="0">'
            f'<animate attributeName="opacity" values="0;1" dur=".22s" '
            f'begin="{0.3 + i * 0.075:.2f}s" fill="freeze"/>{text}</text>'
        )
    s.append('</g>')
    return "".join(s)


def sidebar(p: dict) -> str:
    s = [reveal(f'<text x="{NOTE_X}" y="122" font-size="13.5" fill="{p["muted"]}">'
                f'$ cat sakura.txt</text>', 0.4)]
    s.append(reveal(
        f'<text x="{NOTE_X}" y="164" font-size="27" font-weight="700" '
        f'fill="{p["text"]}">&#127800; <tspan fill="url(#sak)">sakura</tspan></text>', 0.8))
    y = 214
    for i, (key, value) in enumerate(NOTES):
        s.append(reveal(
            f'<text x="{NOTE_X}" y="{y}" font-size="13">'
            f'<tspan fill="{p["g2"]}">{key}</tspan>'
            f'<tspan fill="{p["dim"]}" dx="10">&#8594;</tspan></text>', 1.3 + i * 0.3))
        s.append(reveal(
            f'<text x="{NOTE_X}" y="{y + 20}" font-size="13" fill="{p["text"]}">'
            f'{esc(value)}</text>', 1.45 + i * 0.3))
        y += 54

    fy = PANEL[1] + PANEL[3] - 28
    s.append(f'<line x1="{NOTE_X}" y1="{fy - 24}" x2="{PANEL[0] + PANEL[2] - 34}" '
             f'y2="{fy - 24}" stroke="{p["border"]}" stroke-width="1"/>')
    s.append(reveal(f'<text x="{NOTE_X}" y="{fy}" font-size="12.5" fill="{p["muted"]}">'
                    f'asu ~ % <tspan fill="url(#sak)">bloom --forever</tspan></text>', 2.6))
    s.append(f'<rect x="{NOTE_X + 196}" y="{fy - 11}" width="8" height="14" '
             f'fill="{p["petal2"]}"><animate attributeName="opacity" '
             f'values="1;1;0;0;1" keyTimes="0;.45;.5;.95;1" dur="1.1s" '
             f'repeatCount="indefinite"/></rect>')
    return "".join(s)


def build(mode: str, lines: list[str]) -> str:
    p = PAL[mode]
    x, y, w, h = PANEL
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
        f'role="img" aria-label="Sakura drawn in ASCII" font-family="{FONT}">',
        defs(p, mode),
        background(p),
        window_chrome(p, x, y, w, h, "asu@webcore: ~/sakura"),
        falling_petals(p),
        blossom(p, lines),
        sidebar(p),
        f'<g clip-path="url(#panelClip)"><rect x="{x}" y="{y}" width="{w}" height="22" '
        f'fill="{p["scan"]}"><animateTransform attributeName="transform" '
        f'type="translate" values="0 -40;0 {h + 10};0 -40" dur="11s" '
        f'repeatCount="indefinite"/></rect></g>',
        '</svg>',
    ])


def main() -> None:
    lines = art_lines()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mode in ("dark", "light"):
        target = OUT_DIR / f"{mode}.svg"
        write_svg(target, build(mode, lines))
        print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
