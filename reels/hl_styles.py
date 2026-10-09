"""Highlight caption styles + revenue card + PNG corner (shared by preview and final render)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FD + name, int(size))
RED = (229, 22, 34); RED_DK = (120, 6, 14); WHITE = (255, 255, 255)
FC = font("InterDisplay-Bold.otf", 64)
FH = font("InterDisplay-Black.otf", 74)

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def blur_shadow(size, box, r, blur, alpha, off):
    sh = Image.new("RGBA", size, (0, 0, 0, 0)); x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]), r, fill=(0, 0, 0, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur))

def plain_caption(txt):
    """normal (non-highlight) caption: white Inter Display Bold, soft dark halo"""
    tw = FC.getlength(txt); bb = FC.getbbox(txt)
    w, h = int(tw + 84), int(bb[3] - bb[1] + 64)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=FC, fill=(0, 0, 0, 200), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, 200))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=FC, fill=WHITE, anchor="mm")
    return im

def hl_a(txt):
    """A - current: red rounded box, white bold text"""
    tw = FC.getlength(txt); bb = FC.getbbox(txt)
    w, h = int(tw + 84), int(bb[3] - bb[1] + 64)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(blur_shadow((w, h), (20, 20, w - 20, h - 20), 16, 8, 50, (0, 4)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, w - 20, h - 20), 16, fill=RED)
    d.text((w / 2, h / 2 - 2), txt, font=FC, fill=WHITE, anchor="mm")
    return im

def hl_b(txt):
    """B - sticker: heavier/bigger text, red box with white border, tilted, deep soft shadow"""
    tw = FH.getlength(txt); bb = FH.getbbox(txt); px, py, m = 30, 16, 40
    bw, bh = int(tw + 2 * px), int(bb[3] - bb[1] + 2 * py)
    w, h = bw + 2 * m, bh + 2 * m
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(blur_shadow((w, h), (m, m, m + bw, m + bh), 20, 12, 110, (0, 10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m - 6, m - 6, m + bw + 6, m + bh + 6), 24, fill=WHITE)
    d.rounded_rectangle((m, m, m + bw, m + bh), 18, fill=RED)
    d.text((w / 2, h / 2 - 3), txt, font=FH, fill=WHITE, anchor="mm")
    return im

def hl_c(txt):
    """C - block: heavier/bigger text, red box with hard offset dark-red block behind, slight tilt"""
    tw = FH.getlength(txt); bb = FH.getbbox(txt); px, py, m, o = 30, 16, 36, 10
    bw, bh = int(tw + 2 * px), int(bb[3] - bb[1] + 2 * py)
    w, h = bw + 2 * m + o, bh + 2 * m + o
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(blur_shadow((w, h), (m, m, m + bw + o, m + bh + o), 16, 12, 70, (0, 8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m + o, m + o, m + bw + o, m + bh + o), 14, fill=RED_DK)
    d.rounded_rectangle((m, m, m + bw, m + bh), 14, fill=RED)
    d.text((m + bw / 2, m + bh / 2 - 3), txt, font=FH, fill=WHITE, anchor="mm")
    return im

TILT = {"A": 0.0, "B": -3.0, "C": 2.0}
MAKE = {"A": hl_a, "B": hl_b, "C": hl_c}

def place(canvas, im, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))

def anim_plain(k):
    """(scale, dy, angle_mul, alpha) for frame k after entry - current pop"""
    return 0.86 + 0.14 * ease_out_back(k / 5), (1 - ease_out_cubic(k / 5)) * 8, 1.0, min(1, 0.35 + k / 3)
def anim_hl(k, style):
    if style == "A": return anim_plain(k)
    # punchier pop: from 55% with a stronger overshoot, rotation settles into its tilt
    s = 0.55 + 0.45 * ease_out_back(k / 7, 2.6)
    return s, (1 - ease_out_cubic(k / 7)) * 14, 0.4 + 0.6 * ease_out_cubic(k / 6), min(1, 0.3 + k / 2.5)

def draw_caption(canvas, c, k, cx, cy, style):
    if c["hl"]:
        s, dy, am, a = anim_hl(k, style)
        place(canvas, c["im"], cx, cy + dy, s, TILT[style] * am * c.get("tilt_sign", 1), a)
    else:
        s, dy, _, a = anim_plain(k)
        place(canvas, c["im"], cx, cy + dy, s, 0, a)

# ---------------- revenue card ------------------------------------------------------
def revenue_card(src_png, mode="rebuild", width=760):
    """'rebuild' = crisp redraw of the screenshot (same look); 'image' = the screenshot upscaled"""
    if mode == "image":
        sh = Image.open(src_png).convert("RGBA")
        sc = width / sh.width; card = sh.resize((width, int(sh.height * sc)), Image.LANCZOS)
    else:
        sc = width / 316; cw, ch = width, int(145 * sc)
        card = Image.new("RGBA", (cw, ch), (40, 40, 40, 255)); d = ImageDraw.Draw(card)
        d.text((cw / 2, 38 * sc), "Estimated revenue", font=font("Inter-Regular.otf", 19 * sc), fill=(170, 170, 170), anchor="mm")
        d.text((cw / 2, 92 * sc), "$2,931.14", font=font("Inter-Regular.otf", 46 * sc), fill=(245, 245, 245), anchor="mm")
    r = 34
    mask = Image.new("L", card.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, card.width - 1, card.height - 1), r, fill=255)
    card.putalpha(mask)
    m = 50; out = Image.new("RGBA", (card.width + 2 * m, card.height + 2 * m), (0, 0, 0, 0))
    out.alpha_composite(blur_shadow(out.size, (m, m, m + card.width, m + card.height), r, 18, 130, (0, 14)))
    ImageDraw.Draw(out).rounded_rectangle((m - 3, m - 3, m + card.width + 2, m + card.height + 2), r + 3, fill=(255, 255, 255, 40))
    out.alpha_composite(card, (m, m))
    return out

# ---------------- guy PNG (cut-out) bottom-left ------------------------------------
PNG_SCALE = 0.56
PNG_X, PNG_Y = -70, 1920 - int(1920 * PNG_SCALE) + 40   # bottom-left, cropped by the frame edge
def png_cutout(guy_rgb, mask_l):
    """guy_rgb: HxWx3 uint8 (1080x1920), mask_l: PIL L same size -> RGBA sprite with soft shadow"""
    w, h = int(1080 * PNG_SCALE), int(1920 * PNG_SCALE)
    g = Image.fromarray(guy_rgb).resize((w, h), Image.LANCZOS).convert("RGBA")
    m = mask_l.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8))
    g.putalpha(m)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(m.point(lambda v: int(v * 0.55)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.alpha_composite(sh, (10, 8)); out.alpha_composite(g)
    return out
