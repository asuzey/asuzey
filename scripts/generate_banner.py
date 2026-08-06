#!/usr/bin/env python3
"""Build ASU's animated GitHub profile banner.

The output is a pair of pure-SMIL SVG files -- no JavaScript, no external fonts,
no network requests -- so GitHub renders them straight from the README through a
<picture> element:

    assets/banner/dark.svg
    assets/banner/light.svg

Two rules the whole file follows:

1. Every looping animation returns to its exact starting state, so nothing ever
   snaps back to frame one.
2. Nothing animated overlaps anything readable. The code rain lives inside the
   left panel only, and the text column keeps its own space.

Run:  python scripts/generate_banner.py
      python scripts/generate_banner.py --grid    (adds a tuning ruler)
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import PAL, FONT, esc, reveal, gradient_defs, window_chrome  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "banner"

# Set by --grid: overlays a coordinate ruler so the mascot can be nudged by eye.
SHOW_GRID = False

W, H = 1180, 560

# ---------------------------------------------------------------- content ---

NAME = "ASU"
GREETING = "Hi &#9825; I&#8217;m"

ROLES = [
    "Full-Stack Developer",
    "Python Service Builder",
    "AI-Assisted Workflows",
    "Certified Cat Person",
]

INFO = [
    ("~/building", "practical software, shipped small and often"),
    ("~/learning", "PHP &#183; Laravel &#183; C# and Unity fundamentals"),
    ("~/github", "github.com/asuzey"),
    ("~/vibe", "webcore workspace &#183; lo-fi &#183; terminal glow"),
]

SKILLS = [
    "TypeScript", "React", "Next.js", "Python", "FastAPI",
    "C#", "Unity", "Laravel", "Docker", "Git",
]

SOCIALS = ["GitHub", "Projects", "Say hi"]

# ------------------------------------------------------------- the mascot ---
#
# NUDGING THE CAT
# ---------------
# Each line is (dx, dy, text) in pixels, measured from the mascot's anchor
# point (CAT_X, CAT_Y below):
#
#     dx  >0 moves the line RIGHT, <0 moves it LEFT
#     dy  >0 moves the line DOWN,  <0 moves it UP
#
# CAT_X / CAT_Y move the whole cat, CAT_SIZE scales it, CAT_LINE_H sets the gap
# between rows. Run `python scripts/generate_banner.py --grid` to render a
# 20px ruler over the panel, read the offsets you want, then delete the ruler
# by running the plain command again.
#
CAT_X, CAT_Y = 142, 208        # anchor: left edge and first baseline
CAT_SIZE = 36                  # glyph size
CAT_LINE_H = 34                # vertical gap between rows

CAT_LINES = [
    (84,  0, "へ"),
    (14,  0, "૮  >  <)"),
    (34,  0, "/ ⁻  ៸|"),
    (0,   0, "乀(ˍ, ل ل"),
]
CAT_HEART = (148, -4, 24)      # (dx, dy, size) for the &#9825; beside the ear

RAIN_TOKENS = ["01", "10", "{}", "</>", "TS", "PY", "C#", "~/", "&&", "::", "()", "=>"]

# The mascot pulls glyphs from Japanese, Gujarati, Khmer and Arabic blocks, so
# the stack names a covering font per platform and lets the browser fall back
# character by character.
CAT_FONT = (
    "'Segoe UI Symbol','Segoe UI','Nirmala UI','Leelawadee UI','Yu Gothic',"
    "'Noto Sans JP','Noto Sans Gujarati','Noto Sans Khmer','Noto Sans Arabic',"
    "'Hiragino Sans','Apple Symbols','Arial Unicode MS',sans-serif"
)

# ---------------------------------------------------------------- geometry ---

LP_X, LP_Y, LP_W, LP_H = 32, 32, 396, 496      # left panel  (the cat room)
RP_X, RP_Y, RP_W, RP_H = 452, 32, 696, 496     # right panel (the terminal)


def defs(p: dict, mode: str) -> str:
    s = ['<defs>', gradient_defs(p, mode)]

    # Clip regions.
    s.append(
        f'<clipPath id="leftClip"><rect x="{LP_X}" y="{LP_Y}" width="{LP_W}" '
        f'height="{LP_H}" rx="18"/></clipPath>'
    )
    s.append(
        f'<clipPath id="rightClip"><rect x="{RP_X}" y="{RP_Y}" width="{RP_W}" '
        f'height="{RP_H}" rx="18"/></clipPath>'
    )

    # Typewriter clips: one rectangle per role, widening then collapsing in turn.
    cycle = len(ROLES) * 4.6
    for i, role in enumerate(ROLES):
        width = len(role) * 10.2
        b = i * 4.6
        keys = f"0;{b/cycle:.4f};{(b+1.5)/cycle:.4f};{(b+3.4)/cycle:.4f};{(b+3.9)/cycle:.4f};1"
        s.append(
            f'<clipPath id="role{i}"><rect x="{RP_X + 62}" y="188" height="28" width="0">'
            f'<animate attributeName="width" dur="{cycle}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="{keys}" '
            f'values="0;0;{width:.0f};{width:.0f};0;0"/></rect></clipPath>'
        )

    s.append('</defs>')
    return "".join(s)


def background(p: dict) -> str:
    s = [f'<rect width="{W}" height="{H}" rx="24" fill="{p["bg"]}"/>',
         f'<rect width="{W}" height="{H}" rx="24" fill="url(#dots)"/>']
    # Slow-drifting light. Each translate returns to 0 0, so the loop is seamless.
    s.append('<circle cx="180" cy="140" r="310" fill="url(#glowB)">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0;34 24;0 0" dur="15s" repeatCount="indefinite"/></circle>')
    s.append('<circle cx="1000" cy="470" r="330" fill="url(#glowA)">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0;-28 -20;0 0" dur="18s" repeatCount="indefinite"/></circle>')
    s.append('<circle cx="640" cy="60" r="230" fill="url(#glowC)">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0;18 26;0 0" dur="13s" repeatCount="indefinite"/></circle>')
    # Drifting motes.
    for cx, cy, r, dur, dy in (
        (146, 500, 2.0, 9, -70), (352, 96, 1.6, 12, 62), (720, 528, 2.2, 11, -84),
        (930, 108, 1.5, 10, 70), (1092, 300, 1.8, 13, -60), (60, 300, 1.4, 8, 52),
        (1140, 470, 1.5, 15, -48), (250, 540, 1.7, 14, -66),
    ):
        s.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{p["g2"]}" opacity=".3">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {dy};0 0" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".08;.45;.08" dur="{dur}s" '
            f'repeatCount="indefinite"/></circle>'
        )
    s.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
             f'stroke="{p["border"]}" stroke-width="1.5"/>')
    s.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
             f'stroke="url(#shimmer)" stroke-width="1.5" opacity=".75"/>')
    return "".join(s)


def window_chrome(p: dict, x: int, y: int, w: int, h: int, title: str) -> str:
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{p["panel"]}" '
         f'stroke="{p["border"]}"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="url(#glass)"/>']
    for i, color in enumerate(("#FF6F72", "#FFC56E", "#6FE39B")):
        s.append(f'<circle cx="{x + 24 + i * 20}" cy="{y + 24}" r="5.5" fill="{color}" opacity=".9"/>')
    s.append(f'<text x="{x + w / 2:.0f}" y="{y + 29}" text-anchor="middle" font-size="12" '
             f'fill="{p["muted"]}">{title}</text>')
    return "".join(s)


def code_rain(p: dict) -> str:
    """A genuinely endless rain: two identical stacks, scrolled by exactly one period."""
    rng = random.Random(7)
    period = 286
    step = 26
    s = ['<g clip-path="url(#leftClip)" opacity="1">']
    for col in range(12):
        x = LP_X + 26 + col * 32
        dur = 11 + (col % 5) * 2.5
        offset = rng.randrange(0, period)
        s.append(f'<g><animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;0 {period}" dur="{dur}s" repeatCount="indefinite" '
                 f'calcMode="linear"/>')
        for copy in (0, 1):
            for row in range(period // step + 1):
                y = LP_Y + 44 + ((offset + row * step) % period) - period * (1 - copy)
                token = rng.choice(RAIN_TOKENS)
                s.append(f'<text x="{x}" y="{y}" font-size="11" fill="{p["rain"]}" '
                         f'opacity="{p["rain_op"]}">{esc(token)}</text>')
        s.append('</g>')
    s.append('</g>')
    return "".join(s)


def cat(p: dict) -> str:
    """The mascot: kaomoji, monochrome, bobbing, blinking, quietly purring hearts."""
    cx = LP_X + LP_W / 2
    left, cy = CAT_X, CAT_Y
    size, line_h = CAT_SIZE, CAT_LINE_H
    s = []

    # Pool of light under the cat.
    s.append(f'<ellipse cx="{cx:.0f}" cy="{cy + 46:.0f}" rx="118" ry="72" '
             f'fill="url(#glowA)" filter="url(#soft)">'
             f'<animate attributeName="rx" values="118;128;118" dur="6s" '
             f'repeatCount="indefinite"/></ellipse>')

    # Whole-cat motion: a 6s breath, plus a 9s sway. Both start and end at rest.
    s.append(f'<g font-family="{CAT_FONT}" font-size="{size}" fill="{p["cat"]}" '
             f'xml:space="preserve">')
    s.append('<animateTransform attributeName="transform" type="translate" '
             'values="0 0;0 -7;0 0" dur="6s" repeatCount="indefinite" '
             'calcMode="spline" keyTimes="0;0.5;1" '
             'keySplines="0.4 0 0.2 1;0.4 0 0.2 1" additive="sum"/>')
    s.append(f'<animateTransform attributeName="transform" type="rotate" '
             f'values="0 {cx:.0f} {cy:.0f};1.4 {cx:.0f} {cy:.0f};'
             f'0 {cx:.0f} {cy:.0f};-1.4 {cx:.0f} {cy:.0f};0 {cx:.0f} {cy:.0f}" '
             f'dur="9s" repeatCount="indefinite" additive="sum"/>')

    # The glyphs themselves are never substituted -- this is the exact shape ASU
    # picked, so every bit of life comes from moving the lines, not redrawing them.
    for i, (dx, dy, line) in enumerate(CAT_LINES):
        x = left + dx
        y = cy + i * line_h + dy
        if i == 0:
            # The ear twitches every few seconds.
            s.append(
                f'<text x="{x:.0f}" y="{y:.0f}">{esc(line)}'
                f'<animateTransform attributeName="transform" type="rotate" '
                f'values="0 {x + 12:.0f} {y:.0f};0 {x + 12:.0f} {y:.0f};'
                f'-9 {x + 12:.0f} {y:.0f};6 {x + 12:.0f} {y:.0f};'
                f'0 {x + 12:.0f} {y:.0f};0 {x + 12:.0f} {y:.0f}" '
                f'keyTimes="0;0.62;0.68;0.74;0.8;1" dur="5.6s" '
                f'repeatCount="indefinite"/></text>'
            )
        elif i == 3:
            # The two little paws shuffle, pivoting under the body.
            s.append(
                f'<text x="{x:.0f}" y="{y:.0f}">{esc(line)}'
                f'<animateTransform attributeName="transform" type="rotate" '
                f'values="0 {x + 30:.0f} {y - 10:.0f};1.8 {x + 30:.0f} {y - 10:.0f};'
                f'0 {x + 30:.0f} {y - 10:.0f};-1.8 {x + 30:.0f} {y - 10:.0f};'
                f'0 {x + 30:.0f} {y - 10:.0f}" dur="3.6s" '
                f'repeatCount="indefinite"/></text>'
            )
        else:
            s.append(f'<text x="{x:.0f}" y="{y:.0f}">{esc(line)}</text>')

    # The heart beside the ear. It is wrapped in its own translated group so the
    # scale animation beats around the glyph instead of around the SVG origin.
    hdx, hdy, hsize = CAT_HEART
    s.append(
        f'<g transform="translate({left + hdx:.0f},{cy + hdy:.0f})">'
        f'<text x="0" y="0" text-anchor="middle" font-size="{hsize}" fill="{p["heart"]}">&#9825;'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="1;1.24;1;1.12;1" dur="2.4s" repeatCount="indefinite"/></text></g>'
    )
    s.append('</g>')

    # A couple of hearts drifting up past the cat, staggered so there is no gap.
    for i, (dx, dur, delay) in enumerate(((78, 5.6, 0.4), (104, 6.8, 3.2))):
        s.append(
            f'<text x="{cx + dx:.0f}" y="{cy + 92:.0f}" font-size="{15 + i * 3}" '
            f'fill="{p["heart"]}" opacity="0" text-anchor="middle">&#9825;'
            f'<animate attributeName="opacity" values="0;.85;0" dur="{dur}s" '
            f'begin="{delay}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;{-6 + i * 6} -58" dur="{dur}s" begin="{delay}s" '
            f'repeatCount="indefinite"/></text>'
        )

    # Twinkles.
    for x, y, dur, begin in ((LP_X + 58, 152, 3.4, 0.2), (LP_X + 330, 196, 4.1, 1.3),
                             (LP_X + 84, 352, 3.8, 2.2), (LP_X + 322, 384, 4.4, 0.8)):
        s.append(
            f'<text x="{x}" y="{y}" font-size="13" fill="{p["g2"]}" opacity=".2" '
            f'text-anchor="middle">&#10022;'
            f'<animate attributeName="opacity" values=".12;.7;.12" dur="{dur}s" '
            f'begin="{begin}s" repeatCount="indefinite"/></text>'
        )

    # Caption + a little prompt of its own.
    s.append(f'<text x="{cx:.0f}" y="418" text-anchor="middle" font-size="12" '
             f'letter-spacing="1.5" fill="{p["dim"]}">&#9825; tiny helper online</text>')
    s.append(f'<text x="{LP_X + 26}" y="486" font-size="12.5" fill="{p["muted"]}">'
             f'asu ~ % <tspan fill="url(#acc)">pet cat</tspan></text>')
    s.append(f'<rect x="{LP_X + 128}" y="475" width="8" height="14" fill="{p["g2"]}">'
             f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.45;.5;.95;1" '
             f'dur="1.1s" repeatCount="indefinite"/></rect>')

    # Scanline sweep across the cat room.
    s.append(f'<g clip-path="url(#leftClip)"><rect x="{LP_X}" y="{LP_Y}" width="{LP_W}" '
             f'height="30" fill="{p["scan"]}">'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 -40;0 {LP_H + 10};0 -40" dur="9s" repeatCount="indefinite"/>'
             f'</rect></g>')

    if SHOW_GRID:
        s.append(tuning_grid())
    return "".join(s)


def tuning_grid() -> str:
    """A throwaway ruler for --grid: 20px lattice plus the mascot anchor point.

    Read a distance off this, add it to the matching dx/dy in CAT_LINES, and
    re-run without the flag.
    """
    s = ['<g clip-path="url(#leftClip)" font-size="8" fill="#FF6F72">']
    for gx in range(LP_X, LP_X + LP_W, 20):
        heavy = (gx - LP_X) % 100 == 0
        s.append(f'<line x1="{gx}" y1="{LP_Y}" x2="{gx}" y2="{LP_Y + LP_H}" '
                 f'stroke="#FF6F72" stroke-width="{0.6 if heavy else 0.25}" '
                 f'opacity="{0.55 if heavy else 0.25}"/>')
        if heavy:
            s.append(f'<text x="{gx + 2}" y="{LP_Y + 46}">{gx}</text>')
    for gy in range(LP_Y, LP_Y + LP_H, 20):
        heavy = (gy - LP_Y) % 100 == 0
        s.append(f'<line x1="{LP_X}" y1="{gy}" x2="{LP_X + LP_W}" y2="{gy}" '
                 f'stroke="#FF6F72" stroke-width="{0.6 if heavy else 0.25}" '
                 f'opacity="{0.55 if heavy else 0.25}"/>')
        if heavy:
            s.append(f'<text x="{LP_X + 4}" y="{gy - 3}">{gy}</text>')
    # The anchor every dx/dy is measured from.
    s.append(f'<circle cx="{CAT_X}" cy="{CAT_Y}" r="4" fill="none" stroke="#6FE39B" '
             f'stroke-width="1.5"/>')
    s.append(f'<text x="{CAT_X + 8}" y="{CAT_Y - 6}" fill="#6FE39B" font-size="10">'
             f'CAT_X,CAT_Y = {CAT_X},{CAT_Y}</text>')
    # One marker per mascot line, so each dx/dy is visible where it lands.
    for i, (dx, dy, _) in enumerate(CAT_LINES):
        mx, my = CAT_X + dx, CAT_Y + i * CAT_LINE_H + dy
        s.append(f'<circle cx="{mx}" cy="{my}" r="2.5" fill="#FFC56E"/>')
        s.append(f'<text x="{mx + 5}" y="{my + 11}" fill="#FFC56E" font-size="9">'
                 f'[{i}] {dx},{dy}</text>')
    s.append('</g>')
    return "".join(s)


def terminal(p: dict) -> str:
    x = RP_X + 36
    s = []

    s.append(reveal(f'<text x="{x}" y="108" font-size="14.5" fill="{p["muted"]}">'
                    f'$ whoami</text>', 0.35))
    s.append(reveal(
        f'<text x="{x}" y="154" font-size="34" font-weight="700" fill="{p["text"]}">'
        f'{GREETING} <tspan fill="url(#acc)">{NAME}</tspan></text>', 0.75))

    # Rotating job titles, typed out one character-width at a time.
    s.append(f'<text x="{x}" y="207" font-size="17" fill="{p["g2"]}">&gt;</text>')
    for i, role in enumerate(ROLES):
        s.append(f'<g clip-path="url(#role{i})"><text x="{RP_X + 62}" y="208" '
                 f'font-size="17" font-weight="600" fill="url(#acc)">{esc(role)}</text></g>')

    # A caret that walks along with whichever role is currently being typed.
    cycle = len(ROLES) * 4.6
    keys, vals = ["0"], ["0 0"]
    for i, role in enumerate(ROLES):
        width = len(role) * 10.2
        b = i * 4.6
        keys += [f"{b/cycle:.4f}", f"{(b+1.5)/cycle:.4f}", f"{(b+3.4)/cycle:.4f}",
                 f"{(b+3.9)/cycle:.4f}"]
        vals += ["0 0", f"{width:.0f} 0", f"{width:.0f} 0", "0 0"]
    keys.append("1")
    vals.append("0 0")
    s.append(
        f'<rect x="{RP_X + 62}" y="193" width="8" height="19" fill="{p["g2"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.45;.5;.95;1" '
        f'dur="1s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" dur="{cycle}s" '
        f'repeatCount="indefinite" calcMode="linear" keyTimes="{";".join(keys)}" '
        f'values="{";".join(vals)}"/></rect>'
    )

    # Key / value rows.
    y = 252
    for i, (key, value) in enumerate(INFO):
        s.append(reveal(
            f'<text x="{x}" y="{y}" font-size="14">'
            f'<tspan fill="{p["g2"]}">{key}</tspan>'
            f'<tspan fill="{p["dim"]}" dx="12">&#8594;</tspan>'
            f'<tspan fill="{p["text"]}" dx="12">{value}</tspan></text>', 1.2 + i * 0.3))
        y += 28

    # Skill pills.
    s.append(reveal(f'<text x="{x}" y="{y + 20}" font-size="12" letter-spacing="2.5" '
                    f'fill="{p["dim"]}">STACK</text>', 2.6))
    px, py = x, y + 38
    for i, skill in enumerate(SKILLS):
        w = len(skill) * 7.6 + 26
        if px + w > RP_X + RP_W - 36:
            px, py = x, py + 42
        s.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".4s" '
            f'begin="{2.8 + i * 0.11:.2f}s" fill="freeze"/>'
            f'<rect x="{px:.0f}" y="{py}" width="{w:.0f}" height="30" rx="15" '
            f'fill="{p["pill"]}" stroke="url(#acc)" stroke-width="1">'
            f'<animate attributeName="stroke-width" values="1;1.7;1" dur="3.6s" '
            f'begin="{i * 0.36:.2f}s" repeatCount="indefinite"/></rect>'
            f'<text x="{px + w / 2:.0f}" y="{py + 20}" text-anchor="middle" '
            f'font-size="13" fill="{p["text"]}">{esc(skill)}</text></g>'
        )
        px += w + 11

    # Footer prompt, set apart by a hairline so it never crowds the pills.
    fy = RP_Y + RP_H - 24
    s.append(f'<line x1="{x}" y1="{fy - 26}" x2="{RP_X + RP_W - 36}" y2="{fy - 26}" '
             f'stroke="{p["border"]}" stroke-width="1"/>')
    links = "".join(
        f'<tspan dx="14" fill="url(#acc)" font-weight="600">{esc(item)}</tspan>'
        + (f'<tspan dx="14" fill="{p["dim"]}">&#183;</tspan>' if i < len(SOCIALS) - 1 else "")
        for i, item in enumerate(SOCIALS)
    )
    s.append(reveal(f'<text x="{x}" y="{fy}" font-size="13.5">'
                    f'<tspan fill="{p["muted"]}">$ connect --with</tspan>{links}</text>', 4.4))
    s.append(f'<rect x="{RP_X + RP_W - 44}" y="{fy - 12}" width="8" height="14" '
             f'fill="{p["g2"]}"><animate attributeName="opacity" values="1;1;0;0;1" '
             f'keyTimes="0;.45;.5;.95;1" dur="1.1s" repeatCount="indefinite"/></rect>')

    # Scanline over the terminal, slower than the cat room so they never sync up.
    s.append(f'<g clip-path="url(#rightClip)"><rect x="{RP_X}" y="{RP_Y}" width="{RP_W}" '
             f'height="24" fill="{p["scan"]}">'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 -40;0 {RP_H + 10};0 -40" dur="13s" repeatCount="indefinite"/>'
             f'</rect></g>')
    return "".join(s)


def build(mode: str) -> str:
    p = PAL[mode]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
        f'role="img" aria-label="ASU &#8212; building practical software" '
        f'font-family="{FONT}">',
        defs(p, mode),
        background(p),
        window_chrome(p, LP_X, LP_Y, LP_W, LP_H, "asu@webcore: ~/cat"),
        code_rain(p),
        cat(p),
        window_chrome(p, RP_X, RP_Y, RP_W, RP_H, "webcore &#8212; zsh &#8212; 120x34"),
        terminal(p),
        '</svg>',
    ]
    return "".join(parts)


def main() -> None:
    global SHOW_GRID
    SHOW_GRID = "--grid" in sys.argv

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mode in ("dark", "light"):
        target = OUT_DIR / f"{mode}.svg"
        target.write_text(build(mode), encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size / 1024:.1f} KB)")
    if SHOW_GRID:
        print("\ntuning ruler is ON -- open the SVG, read the offsets you want,")
        print("edit CAT_LINES / CAT_X / CAT_Y, then re-run without --grid.")


if __name__ == "__main__":
    main()
