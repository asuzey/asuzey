"""Generate the animated GitHub profile banner.

Run with the bundled Python runtime used by Codex. The output is deliberately
a GIF: GitHub renders it reliably in a profile README, unlike scripted SVG.
"""

from math import cos, sin, pi
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "banner" / "banner.gif"
W, H = 1200, 420
FRAMES, DURATION = 24, 90

NAVY = (8, 18, 42)
PANEL = (13, 35, 72)
BLUE = (75, 183, 255)
SKY = (150, 220, 255)
ICE = (229, 249, 255)
MUTED = (156, 188, 220)
PURPLE = (177, 132, 255)
PINK = (255, 150, 212)
# The cat intentionally stays monochrome: it reads as a calm little mascot,
# while the blue terminal is left to carry the colour.
CAT = (30, 38, 53)
CAT_LIGHT = (235, 244, 252)


def font(size, bold=False):
    fonts = Path("C:/Windows/Fonts")
    name = "consolab.ttf" if bold else "consola.ttf"
    path = fonts / name
    return ImageFont.truetype(path, size) if path.exists() else ImageFont.load_default()


F11, F13, F15 = font(11), font(13), font(15)
F18, F22, F28 = font(18, True), font(22, True), font(28, True)
F62 = font(62, True)
KAWAII = font(28)
CAT_FONT_SIZE = 31
CAT_FONTS = {
    "default": font(CAT_FONT_SIZE),
    "japanese": ImageFont.truetype("C:/Windows/Fonts/YuGothM.ttc", CAT_FONT_SIZE),
    "symbol": ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", CAT_FONT_SIZE),
    "gujarati": ImageFont.truetype("C:/Windows/Fonts/Nirmala.ttc", CAT_FONT_SIZE),
    "khmer": ImageFont.truetype("C:/Windows/Fonts/LeelawUI.ttf", CAT_FONT_SIZE),
    "arabic": ImageFont.truetype("C:/Windows/Fonts/arial.ttf", CAT_FONT_SIZE),
}


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


def glow_line(base, points, fill, width=2):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.line(points, fill=fill + (70,), width=width + 12, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(8))
    base.alpha_composite(layer)
    ImageDraw.Draw(base).line(points, fill=fill + (255,), width=width, joint="curve")


def cat_font(character):
    """Use Windows' native script fonts so the submitted kaomoji stays intact."""
    if character in "へ乀":
        return CAT_FONTS["japanese"]
    if character == "♡":
        return CAT_FONTS["symbol"]
    if character == "૮":
        return CAT_FONTS["gujarati"]
    if character == "៸":
        return CAT_FONTS["khmer"]
    if character == "ل":
        return CAT_FONTS["arabic"]
    return CAT_FONTS["default"]


def draw_submitted_cat(draw, t):
    """The exact cat form selected by the user, drawn with per-script fonts."""
    lines = ("           へ  ♡", "     ૮  >  <)", "       /  ⁻  ៸|", "  乀(ˍ, ل ل")
    x, baseline = 115, 160 + int(sin(t * 2 * pi) * 2)
    for row, line in enumerate(lines):
        cursor = x
        for character in line:
            selected = cat_font(character)
            draw.text((cursor, baseline + row * 39), character, font=selected,
                      fill=ICE, anchor="ls")
            cursor += draw.textlength(character, font=selected)
    draw.text((184, 342), "tiny helper online", font=F11, fill=MUTED, anchor="ma")


def draw_cat(im, t):
    """A tiny kaomoji-inspired cat — intentionally simple and uncoloured."""
    d = ImageDraw.Draw(im)
    x, y = 164, 145
    bob = int(sin(t * 2 * pi) * 3)
    face = "( o.o )" if int(t * FRAMES) % 12 < 10 else "( -.- )"
    kitty = " /\\_/\\\n" + face + "\n  > ^ <"
    # A tiny vertical drift and a floating heart provide motion without
    # turning the mascot into a large, colourful illustration.
    d.multiline_text((x, y + bob), kitty, font=KAWAII, fill=CAT_LIGHT,
                     stroke_width=1, stroke_fill=(72, 91, 118), spacing=-6)
    heart_y = y - 4 + int(sin(t * 2 * pi) * 5)
    d.text((x + 132, heart_y), "<3", font=F18, fill=SKY)
    d.text((x - 10, 337), "tiny helper online", font=F11, fill=MUTED)
    return

    # Legacy vector mascot retained below only as a drawing reference.
    x, y = 154, 148
    bob = int(sin(t * 2 * pi) * 2)
    # Tail, gently swaying behind the chair.
    tail = [(x + 198, y + 185), (x + 230, y + 165 + int(sin(t * 2*pi) * 9)),
            (x + 232, y + 125), (x + 212, y + 112)]
    d.line(tail, fill=CAT, width=17, joint="curve")
    d.line(tail, fill=CAT_LIGHT, width=2, joint="curve")
    # A slim torso hides behind the keyboard. Keeping the body narrow lets the
    # face and little typing paws do the work instead of making a round blob.
    rounded(d, (x + 87, y + 146 + bob, x + 163, y + 232 + bob), 30, CAT, outline=CAT_LIGHT, width=2)
    d.polygon([(x + 61, y + 105 + bob), (x + 75, y + 44 + bob), (x + 109, y + 78 + bob)], fill=CAT, outline=CAT_LIGHT)
    d.polygon([(x + 148, y + 78 + bob), (x + 180, y + 44 + bob), (x + 190, y + 107 + bob)], fill=CAT, outline=CAT_LIGHT)
    d.ellipse((x + 53, y + 66 + bob, x + 194, y + 178 + bob), fill=CAT, outline=CAT_LIGHT, width=3)
    # Inner ears and face.
    d.polygon([(x + 72, y + 96 + bob), (x + 78, y + 62 + bob), (x + 97, y + 86 + bob)], fill=(70, 78, 92))
    d.polygon([(x + 154, y + 86 + bob), (x + 178, y + 62 + bob), (x + 181, y + 98 + bob)], fill=(70, 78, 92))
    blink = 8 <= (int(t * FRAMES) % FRAMES) <= 9
    if blink:
        d.line((x + 89, y + 116 + bob, x + 103, y + 116 + bob), fill=NAVY, width=3)
        d.line((x + 145, y + 116 + bob, x + 159, y + 116 + bob), fill=NAVY, width=3)
    else:
        d.ellipse((x + 91, y + 107 + bob, x + 103, y + 121 + bob), fill=NAVY)
        d.ellipse((x + 147, y + 107 + bob, x + 159, y + 121 + bob), fill=NAVY)
        d.ellipse((x + 95, y + 109 + bob, x + 98, y + 112 + bob), fill=ICE)
        d.ellipse((x + 151, y + 109 + bob, x + 154, y + 112 + bob), fill=ICE)
    d.polygon([(x + 124, y + 129 + bob), (x + 132, y + 129 + bob), (x + 128, y + 135 + bob)], fill=(95, 105, 119))
    d.arc((x + 112, y + 132 + bob, x + 128, y + 145 + bob), 5, 125, fill=CAT_LIGHT, width=2)
    d.arc((x + 128, y + 132 + bob, x + 144, y + 145 + bob), 55, 175, fill=CAT_LIGHT, width=2)
    # Whiskers.
    for off in (-1, 1):
        d.line((x + 116 if off < 0 else x + 140, y + 137 + bob,
                x + 84 if off < 0 else x + 172, y + 131 + bob), fill=ICE, width=2)
        d.line((x + 116 if off < 0 else x + 140, y + 143 + bob,
                x + 82 if off < 0 else x + 174, y + 151 + bob), fill=ICE, width=2)
    # Desk surface and keyboard.
    rounded(d, (x + 12, y + 220, x + 232, y + 249), 8, (17, 48, 91), outline=(77, 183, 255), width=2)
    for row in range(2):
        for col in range(9):
            kx, ky = x + 25 + col * 22, y + 226 + row * 10
            rounded(d, (kx, ky, kx + 16, ky + 6), 2, (72, 128, 195))
    # Paws alternate up/down as if typing.
    left_up = int(sin(t * 2 * pi) * 7)
    right_up = int(sin(t * 2 * pi + pi) * 7)
    d.ellipse((x + 75, y + 194 + left_up, x + 115, y + 225 + left_up), fill=CAT_LIGHT, outline=(92, 107, 126))
    d.ellipse((x + 140, y + 194 + right_up, x + 180, y + 225 + right_up), fill=CAT_LIGHT, outline=(92, 107, 126))
    # Little typing sparks, one side at a time.
    if int(t * FRAMES) % 2 == 0:
        d.text((x + 54, y + 213), "✦", font=F15, fill=SKY)
    else:
        d.text((x + 185, y + 213), "✦", font=F15, fill=SKY)


def make_frame(index):
    t = index / FRAMES
    im = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(im)
    # Gradient backdrop.
    for yy in range(H):
        ratio = yy / H
        col = (int(7 + 10 * ratio), int(19 + 20 * ratio), int(44 + 42 * ratio), 255)
        d.line((0, yy, W, yy), fill=col)
    # Blue glows.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((705, -130, 1320, 470), fill=(30, 150, 255, 42))
    gd.ellipse((-190, 100, 450, 600), fill=(102, 91, 255, 30))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(50)))
    d = ImageDraw.Draw(im)
    # Terminal window.
    rounded(d, (26, 24, 1174, 394), 18, PANEL, outline=(72, 157, 240), width=2)
    rounded(d, (26, 24, 1174, 60), 18, (19, 48, 92))
    d.rectangle((27, 42, 1173, 60), fill=(19, 48, 92))
    for i, color in enumerate((PINK, (255, 205, 116), (97, 236, 163))):
        d.ellipse((48 + i * 20, 37, 60 + i * 20, 49), fill=color)
    d.text((100, 35), "asu@github: ~/profile", font=F13, fill=MUTED)
    # Matrix rain on the far right. Deterministic but frame shifted.
    random.seed(80)
    terms = ["01", "TS", "PY", "AI", "{}", "<>", "C#", "UX", "//", "git"]
    # A dedicated right rail keeps animated code away from all readable text.
    for col in range(15):
        x = 870 + col * 20
        # The 288px rail moves 12px per frame; 24 frames return precisely to
        # the first position, so the GIF repeats without a visual jump.
        start = random.randrange(-180, 160) + index * 12
        for step in range(7):
            y = (start + step * 31) % 288 + 63
            opacity = max(80, 220 - step * 20)
            d.text((x, y), random.choice(terms), font=F11, fill=(83, 198, 255, opacity))
    # Divider and title.
    glow_line(im, [(486, 86), (486, 347)], BLUE, 2)
    d = ImageDraw.Draw(im)
    d.text((539, 101), "HELLO, I'M", font=F15, fill=SKY)
    d.text((533, 126), "ASU", font=F62, fill=ICE, stroke_width=1, stroke_fill=BLUE)
    d.line((539, 206, 850, 206), fill=BLUE, width=2)
    d.text((539, 223), "building practical software", font=F18, fill=ICE)
    d.text((539, 250), "AI · automation · modern web tools.", font=F15, fill=MUTED)
    typed = "ship --with-intent"
    cursor = "_" if index % 6 < 4 else " "
    d.text((539, 303), "asu@github:~$ ", font=F15, fill=BLUE)
    d.text((681, 303), typed + cursor, font=F15, fill=ICE)
    d.text((539, 341), "TYPE  •  BUILD  •  LEARN  •  SHIP", font=F11, fill=PURPLE)
    draw_submitted_cat(d, t)
    d.text((1125, 365), "v1.0", font=F11, fill=MUTED, anchor="ra")
    return im.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [make_frame(i) for i in range(FRAMES)]
    # All motion is periodic across 24 frames, so the infinite loop has no
    # restart jump and feels like one continuous quiet workspace.
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=DURATION, loop=0, optimize=False, disposal=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
