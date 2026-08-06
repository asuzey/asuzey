"""Shared look and feel for every generated SVG in this profile.

Both the banner and the sakura panel pull their palette, font stack, gradients
and window chrome from here, so changing a colour in one place changes it
everywhere.
"""

from __future__ import annotations

# ---------------------------------------------------------------- palettes ---

PAL = {
    "dark": dict(
        bg="#060B18", panel="#0C1428", panel2="#0A1122",
        border="rgba(148,197,255,.14)", grid="rgba(124,197,255,.05)",
        text="#EAF4FF", muted="#8FA8C8", dim="#5E799E",
        g1="#6FB8FF", g2="#7FE7DF", g3="#B49BFF",
        glow1="#4DA8FF", glow2="#8E7BFF", glow3="#5FE0D6",
        cat="#DCEBFF", heart="#FF9FD0",
        petal1="#FFB3D9", petal2="#FF8FC4", petal3="#C6A8FF",
        scan="rgba(124,197,255,.055)", pill="rgba(111,184,255,.09)",
        rain="#6FB8FF", rain_op=".14", chrome="#111C36",
    ),
    "light": dict(
        bg="#FFFFFF", panel="#F6FAFF", panel2="#EDF4FF",
        border="rgba(28,68,120,.12)", grid="rgba(37,99,235,.05)",
        text="#0C1A33", muted="#4E6A90", dim="#8FA3BE",
        g1="#2F7FE8", g2="#12B3C8", g3="#7C6BF0",
        glow1="#2F7FE8", glow2="#7C6BF0", glow3="#12B3C8",
        cat="#1B3A66", heart="#F06FAE",
        petal1="#F286BC", petal2="#E4609F", petal3="#8A6BE0",
        scan="rgba(47,127,232,.045)", pill="rgba(47,127,232,.07)",
        rain="#2F7FE8", rain_op=".10", chrome="#E4EDFA",
    ),
}

FONT = "'JetBrains Mono','Fira Code','SFMono-Regular',ui-monospace,Consolas,'Liberation Mono',monospace"


# ----------------------------------------------------------------- helpers ---

def esc(text: str) -> str:
    """Escape only what SVG needs; entities in the content are already encoded."""
    return (text.replace("&", "&amp;").replace("&amp;#", "&#")
                .replace("<", "&lt;").replace(">", "&gt;"))


def reveal(element: str, begin: float, dur: float = 0.5) -> str:
    """Fade an element in once at load, then leave it alone."""
    opened = element.replace("<text ", '<text opacity="0" ', 1)
    return opened.replace(
        "</text>",
        f'<animate attributeName="opacity" values="0;1" dur="{dur}s" '
        f'begin="{begin}s" fill="freeze"/></text>',
    )


def gradient_defs(p: dict, mode: str) -> str:
    """The gradients, glows and filters shared by every panel.

    Returns the *contents* of a <defs> block so callers can append their own
    clip paths before closing it.
    """
    s = []
    # Drifting accent gradient, used for headings, pill strokes and links.
    s.append(
        '<linearGradient id="acc" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{p["g1"]}"/>'
        f'<stop offset="50%" stop-color="{p["g2"]}"/>'
        f'<stop offset="100%" stop-color="{p["g3"]}"/>'
        '<animate attributeName="x1" values="0%;-60%;0%" dur="10s" repeatCount="indefinite"/>'
        '<animate attributeName="x2" values="100%;160%;100%" dur="10s" repeatCount="indefinite"/>'
        '</linearGradient>'
    )
    # Petal gradient: pink drifting into lilac, for the sakura art.
    s.append(
        '<linearGradient id="sak" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{p["petal1"]}">'
        f'<animate attributeName="stop-color" '
        f'values="{p["petal1"]};{p["petal2"]};{p["petal3"]};{p["petal1"]}" '
        f'dur="14s" repeatCount="indefinite"/></stop>'
        f'<stop offset="100%" stop-color="{p["petal3"]}">'
        f'<animate attributeName="stop-color" '
        f'values="{p["petal3"]};{p["petal1"]};{p["petal2"]};{p["petal3"]}" '
        f'dur="14s" repeatCount="indefinite"/></stop></linearGradient>'
    )
    # Border shimmer.
    s.append(
        '<linearGradient id="shimmer" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{p["g1"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{p["g2"]}" stop-opacity=".85"/>'
        f'<stop offset="100%" stop-color="{p["g3"]}" stop-opacity="0"/>'
        '<animate attributeName="x1" values="-100%;100%" dur="5s" repeatCount="indefinite"/>'
        '<animate attributeName="x2" values="0%;200%" dur="5s" repeatCount="indefinite"/>'
        '</linearGradient>'
    )
    # Ambient glows.
    strength = (".16", ".13", ".11") if mode == "dark" else (".09", ".07", ".07")
    for name, color, op in (
        ("glowA", p["glow1"], strength[0]),
        ("glowB", p["glow2"], strength[1]),
        ("glowC", p["glow3"], strength[2]),
        ("glowP", p["petal2"], strength[0]),
    ):
        s.append(
            f'<radialGradient id="{name}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0%" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></radialGradient>'
        )
    # Panel sheen.
    top = ".055" if mode == "dark" else ".7"
    s.append(
        '<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#fff" stop-opacity="{top}"/>'
        '<stop offset="22%" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    )
    s.append('<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">'
             '<feGaussianBlur stdDeviation="9"/></filter>')
    # Just enough bloom to make ASCII art glow without smearing the characters.
    s.append('<filter id="tiny" x="-40%" y="-40%" width="180%" height="180%">'
             '<feGaussianBlur stdDeviation="0.55"/></filter>')
    s.append(
        f'<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.5" cy="1.5" r="1.1" fill="{p["grid"]}"/></pattern>'
    )
    return "".join(s)


def window_chrome(p: dict, x: int, y: int, w: int, h: int, title: str) -> str:
    """A rounded terminal window: panel, sheen, traffic lights and a title."""
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{p["panel"]}" '
         f'stroke="{p["border"]}"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="url(#glass)"/>']
    for i, color in enumerate(("#FF6F72", "#FFC56E", "#6FE39B")):
        s.append(f'<circle cx="{x + 24 + i * 20}" cy="{y + 24}" r="5.5" fill="{color}" '
                 f'opacity=".9"/>')
    s.append(f'<text x="{x + w / 2:.0f}" y="{y + 29}" text-anchor="middle" font-size="12" '
             f'fill="{p["muted"]}">{title}</text>')
    return "".join(s)
