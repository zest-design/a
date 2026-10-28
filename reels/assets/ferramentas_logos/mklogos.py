# builds logo PNGs (RGBA, trimmed). Built-in ones are final; missing ones get a temporary crop from the reference.
import subprocess, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"; O = f"{S}/p16/logos"; TMP = f"{S}/p16/tmplogos"
R = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/a0707af5-igexport-DZU16X2zJbC.mp4"
def trim(im):
    bb = im.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox(); return im.crop(bb) if bb else im
def glyph(fontfile, ch, col, size=600):
    f = ImageFont.truetype(fontfile, size); im = Image.new("RGBA", (int(size * 1.6), int(size * 1.6)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), ch, font=f, fill=col, anchor="mm"); return trim(im)
FB = f"{S}/fa/fa-brands.ttf"; FS = f"{S}/fa/fa-solid.ttf"
glyph(FB, chr(0xf19a), (255, 255, 255)).save(f"{O}/wordpress.png")
glyph(FB, chr(0xe057), (149, 191, 71)).save(f"{O}/shopify.png")
glyph(FB, chr(0xf266), (240, 240, 240)).save(f"{O}/wikipedia.png")
gpt = Image.open(f"{S}/p3/gpt_white.png").convert("RGBA"); trim(gpt).save(f"{O}/chatgpt.png")
sp = Image.open(f"{S}/p3/spark.png").convert("RGBA"); trim(sp).save(f"{O}/claude.png")
# terminal: rounded black tile with >_
t = Image.new("RGBA", (600, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
d.rounded_rectangle((0, 0, 599, 599), 120, fill=(8, 8, 10), outline=(110, 110, 118), width=14)
d.line((130, 200, 250, 300, 130, 400), fill=WHITE if False else (255, 255, 255), width=44, joint="curve"); d.rounded_rectangle((290, 380, 470, 420), 20, fill=(255, 255, 255))
t.save(f"{O}/terminal.png")
# Claude Code pixel mascot (drawn on a pixel grid)
px = ["..XXXXXXXX..", "..XXXXXXXX..", "..X.XXXX.X..", "XXXXXXXXXXXX", "XXXXXXXXXXXX", "..XXXXXXXX..", "..X.X..X.X..", "..X.X..X.X.."]
cell = 50; m = Image.new("RGBA", (12 * cell, 8 * cell), (0, 0, 0, 0)); dm = ImageDraw.Draw(m)
for r, row in enumerate(px):
    for c, ch in enumerate(row):
        if ch == "X": dm.rectangle((c * cell, r * cell, (c + 1) * cell - 1, (r + 1) * cell - 1), fill=(217, 119, 87))
m.save(f"{O}/claudecode.png")
# temporary fallbacks from the reference (used only until the user sends the real files)
from PIL import ImageFilter
def grab(tt):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(tt), "-i", R, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombuffer("RGB", (720, 1280), raw)
def cut_bg(im, inv=False, keep_bg=False):
    """remove only the background connected to the border, so white parts INSIDE a logo (Canva lettering) stay"""
    im = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
    if keep_bg:
        out = im.convert("RGBA"); mk = Image.new("L", im.size, 0)
        ImageDraw.Draw(mk).rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.width // 6, fill=255); out.putalpha(mk); return out
    if inv:   # black line-art (Grok, Manus): ink becomes white, paper becomes transparent, inner lines survive
        lum = np.asarray(im.convert("L"), np.float32); alpha = np.clip((235 - lum) * 1.6, 0, 255).astype(np.uint8)
        out = Image.new("RGBA", im.size, (242, 242, 245, 0)); out.putalpha(Image.fromarray(alpha)); return trim(out)
    key = im.copy()
    for xy in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
        ImageDraw.floodfill(key, xy, (255, 0, 255), thresh=70)
    k = np.asarray(key); bg = (k[..., 0] == 255) & (k[..., 1] == 0) & (k[..., 2] == 255)
    alpha = Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    rgb = np.asarray(im).copy()
    if inv: rgb[...] = 240
    out = Image.fromarray(rgb).convert("RGBA"); out.putalpha(alpha); return trim(out)
FR = {"grok": (3.3, (99, 228, 213, 338), dict(inv=True)), "gemini": (6.6, (309, 158, 413, 262), {}), "perplexity": (6.6, (506, 226, 620, 338), {}),
      "lovable": (11.2, (501, 221, 626, 340), {}), "canva": (16.4, (99, 228, 213, 338), {}), "poppy": (16.4, (505, 222, 622, 344), dict(keep_bg=True)),
      "codex": (20.4, (501, 221, 626, 340), {}), "manus": (23.8, (482, 228, 552, 312), dict(inv=True))}
for n, (tt, box, kw) in FR.items():
    if os.path.exists(f"{O}/{n}.png"): continue          # a real file from the user wins
    cut_bg(grab(tt).crop(box), **kw).save(f"{TMP}/{n}.png")
print("ok")
