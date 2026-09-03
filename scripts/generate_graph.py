#!/usr/bin/env python3
"""Draw a year of contributions as a calendar heatmap.

This replaces a third-party graph image that started answering 402 once its
hosting plan ran out -- the last borrowed picture on the profile. The numbers
come from the same GraphQL query the stats card uses, so nothing new is asked
of GitHub, and the drawing matches the rest of the palette.

    GitHub Actions   secrets.GITHUB_TOKEN is passed in automatically
    locally          GITHUB_TOKEN=ghp_xxx python scripts/generate_graph.py

Out:  assets/graph/dark.svg
      assets/graph/light.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import PAL, FONT, reveal, gradient_defs, window_chrome, write_svg  # noqa: E402
from generate_stats import (LOGIN, fetch, summarise, placeholder,  # noqa: E402
                            holds_real_figures)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "graph"

W, H = 920, 252
PANEL = (26, 26, W - 52, 200)

CELL, GAP = 11, 3
GRID_X, GRID_Y = 66, 88

# Empty, then four rising levels of activity.
LEVELS = {
    "dark": ["#0F1A30", "#1E3A5F", "#3E7BB8", "#6FB8FF", "#7FE7DF"],
    "light": ["#E8F0FA", "#BBD8F5", "#7FB3E8", "#3E7BB8", "#1E5A96"],
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level(count: int, busiest: int) -> int:
    """Which of the five shades a day earns."""
    if count <= 0:
        return 0
    if busiest <= 1:
        return 4
    return min(4, 1 + int(3 * (count - 1) / busiest))


def frame(p: dict, mode: str, placeholder_marker: bool) -> list[str]:
    x, y, w, h = PANEL
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
        f'role="img" aria-label="A year of contributions for {LOGIN}" '
        f'font-family="{FONT}">',
        '<!--placeholder-->' if placeholder_marker else '',
        '<defs>' + gradient_defs(p, mode) +
        f'<clipPath id="panelClip"><rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'rx="18"/></clipPath></defs>',
        f'<rect width="{W}" height="{H}" rx="24" fill="{p["bg"]}"/>',
        f'<rect width="{W}" height="{H}" rx="24" fill="url(#dots)"/>',
        '<circle cx="300" cy="120" r="240" fill="url(#glowB)">'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;24 16;0 0" dur="17s" repeatCount="indefinite"/></circle>',
        '<circle cx="720" cy="180" r="230" fill="url(#glowA)">'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;-20 -14;0 0" dur="21s" repeatCount="indefinite"/></circle>',
        f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
        f'stroke="{p["border"]}" stroke-width="1.5"/>',
        f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
        f'stroke="url(#shimmer)" stroke-width="1.5" opacity=".75"/>',
        window_chrome(p, x, y, w, h, "asu@webcore: ~/graph"),
    ]


def build(mode: str, data: dict) -> str:
    p = PAL[mode]
    shades = LEVELS[mode]
    x, y, w, h = PANEL
    weeks = data["calendar"]
    s = frame(p, mode, bool(data.get("placeholder")))

    if not weeks:
        s.append(f'<text x="{W / 2:.0f}" y="132" text-anchor="middle" font-size="14" '
                 f'fill="{p["muted"]}">the year fills in on the next run</text></svg>')
        return "".join(s)

    busiest = max((count for week in weeks for _, count in week), default=0)
    total = sum(count for week in weeks for _, count in week)

    # Weekday gutter.
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        s.append(f'<text x="{GRID_X - 10}" y="{GRID_Y + row * (CELL + GAP) + 9}" '
                 f'text-anchor="end" font-size="9" fill="{p["dim"]}">{label}</text>')

    # One month label per month, placed at the week its first days fall in.
    seen: set[int] = set()
    for index, week in enumerate(weeks):
        if not week:
            continue
        iso = week[0][0]
        month = int(iso[5:7])
        if month not in seen and int(iso[8:10]) <= 7:
            seen.add(month)
            s.append(f'<text x="{GRID_X + index * (CELL + GAP)}" y="{GRID_Y - 10}" '
                     f'font-size="9" fill="{p["dim"]}">{MONTHS[month - 1]}</text>')

    # The grid itself. Cells fade in as a wave across the year, once.
    for index, week in enumerate(weeks):
        cx = GRID_X + index * (CELL + GAP)
        begin = 0.25 + index * 0.012
        for day, (_, count) in enumerate(week):
            cy = GRID_Y + day * (CELL + GAP)
            s.append(
                f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{shades[level(count, busiest)]}" opacity="0">'
                f'<animate attributeName="opacity" values="0;1" dur=".3s" '
                f'begin="{begin:.2f}s" fill="freeze"/></rect>'
            )

    baseline = GRID_Y + 7 * (CELL + GAP) + 18
    s.append(reveal(f'<text x="{GRID_X}" y="{baseline}" font-size="12" '
                    f'fill="{p["muted"]}">{total:,} contributions in the last year'
                    f'</text>', 1.1))

    # Legend, right aligned inside the panel.
    lx = x + w - 40 - 5 * (CELL + GAP)
    s.append(reveal(f'<text x="{lx - 8}" y="{baseline}" text-anchor="end" font-size="10" '
                    f'fill="{p["dim"]}">less</text>', 1.1))
    for i, shade in enumerate(shades):
        s.append(f'<rect x="{lx + i * (CELL + GAP)}" y="{baseline - 10}" width="{CELL}" '
                 f'height="{CELL}" rx="2.5" fill="{shade}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;1" dur=".3s" '
                 f'begin="{1.1 + i * 0.05:.2f}s" fill="freeze"/></rect>')
    s.append(reveal(f'<text x="{lx + 5 * (CELL + GAP) + 6}" y="{baseline}" '
                    f'font-size="10" fill="{p["dim"]}">more</text>', 1.1))

    s.append(f'<g clip-path="url(#panelClip)"><rect x="{x}" y="{y}" width="{w}" '
             f'height="18" fill="{p["scan"]}"><animateTransform '
             f'attributeName="transform" type="translate" '
             f'values="0 -40;0 {h + 10};0 -40" dur="10s" repeatCount="indefinite"/>'
             f'</rect></g></svg>')
    return "".join(s)


def main() -> None:
    stand_in = "--placeholder" in sys.argv
    data = placeholder() if stand_in else summarise(fetch())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mode in ("dark", "light"):
        target = OUT_DIR / f"{mode}.svg"
        if stand_in and holds_real_figures(target):
            print(f"kept {target.relative_to(ROOT)} -- it already has a real year")
            continue
        write_svg(target, build(mode, data))
        print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
