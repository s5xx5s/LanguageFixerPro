"""
Icon Generator - Language Fixer Pro
===================================
Draws app_icon.ico at 512px and downsamples it, so the 16px tray size
stays readable instead of turning into mush.
"""

import os
from PIL import Image, ImageDraw, ImageFont

ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]
ACCENT = "#1A6FD4"
ACCENT_DARK = "#0F4F9E"


def _font(names, size):
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _centered(draw, box, text, font, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((x0 + (x1 - x0 - (r - l)) / 2 - l,
               y0 + (y1 - y0 - (b - t)) / 2 - t), text, font=font, fill=fill)


def render_small(size=512):
    """Simplified mark for 16/24px — detail at that size only turns to mush."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 16
    d.rounded_rectangle((pad, pad, size - pad, size - pad), radius=size // 4, fill=ACCENT)
    font = _font(["tahoma.ttf", "arial.ttf", "segoeui.ttf"], int(size * 0.72))
    _centered(d, (pad, pad, size - pad, size - pad), "ع", font, "white")
    return img


def render(size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 16
    radius = size // 4

    # background plate with a subtle vertical shade
    d.rounded_rectangle((pad, pad, size - pad, size - pad), radius=radius, fill=ACCENT_DARK)
    d.rounded_rectangle((pad, pad, size - pad, size - pad - size // 12),
                        radius=radius, fill=ACCENT)

    ar_font = _font(["tahoma.ttf", "arial.ttf", "segoeui.ttf"], int(size * 0.34))
    en_font = _font(["segoeuib.ttf", "arialbd.ttf", "arial.ttf"], int(size * 0.34))

    half = size // 2
    _centered(d, (pad, pad, half + size // 20, half + size // 20), "ع", ar_font, "white")
    _centered(d, (half - size // 20, half - size // 20, size - pad, size - pad),
              "A", en_font, "white")

    # diagonal divider tying the two letters together
    d.line((int(size * 0.34), int(size * 0.68), int(size * 0.66), int(size * 0.32)),
           fill=(255, 255, 255, 170), width=max(2, size // 36))
    return img


def create_icon(path=None):
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
    master = render(512)
    small = render_small(512)
    frames = [(small if s <= 24 else master).resize((s, s), Image.LANCZOS)
              for s in ICON_SIZES]
    frames[-1].save(path, format="ICO", sizes=[(s, s) for s in ICON_SIZES],
                    append_images=frames[:-1])
    return path


if __name__ == "__main__":
    print("Icon written to:", create_icon())
