import subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
SRC = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/d7a15ef8-1008_1.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)
FD = "/usr/share/fonts/opentype/inter/"
FA = ImageFont.truetype(f"{S}/fa/fa-solid.ttf", 40)

T_IN, T_CLICK = 14.30, 15.44          # button enters / "clic"
CX, CY = 510, 1335                     # below his chin, clear of the IG buttons column

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def button():
    f = ImageFont.truetype(FD + "InterDisplay-Bold.otf", 50); txt = "Ver el vídeo completo"
    tw = f.getlength(txt); h = 118; w = int(tw + 210); pad = 40
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 12, pad + w, pad + h + 12), h // 2, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), h // 2, fill=RED)
    cx = pad + 64; cy = pad + h / 2
    d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=WHITE)
    d.text((cx + 4, cy), "", font=ImageFont.truetype(f"{S}/fa/fa-solid.ttf", 30), fill=RED, anchor="mm")
    d.text((pad + 124, cy), txt, font=f, fill=WHITE, anchor="lm")
    return im, (w, h)
BTN, (BW, BH) = button()
HAND = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
_d = ImageDraw.Draw(HAND)
for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
    _d.text((60 + dx, 60 + dy), "", font=ImageFont.truetype(f"{S}/fa/fa-solid.ttf", 76), fill=(30, 30, 32), anchor="mm")
_d.text((60, 60), "", font=ImageFont.truetype(f"{S}/fa/fa-solid.ttf", 76), fill=WHITE, anchor="mm")

def paste(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

def overlay(canvas, t):
    if t < T_IN: return
    k = (t - T_IN) * FPS
    sc = 0.6 + 0.4 * ease_out_back(k / 9); a = min(1, k / 4)
    dy = (1 - ease_out_cubic(k / 9)) * 60
    kc = (t - T_CLICK) * FPS
    if kc >= 0:
        press = math.sin(min(1, kc / 7) * math.pi) * 0.07 if kc < 7 else 0
        sc *= 1 - press
        if kc > 7: sc *= 1 + 0.025 * math.sin((kc - 7) / FPS * 2 * math.pi * 1.4)
        if kc < 16:   # ripple
            r = 60 + kc * 22; al = int(160 * (1 - kc / 16))
            rp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ImageDraw.Draw(rp).rounded_rectangle((CX - BW / 2 - r * 0.4, CY - BH / 2 - r * 0.25, CX + BW / 2 + r * 0.4, CY + BH / 2 + r * 0.25),
                                                 int(BH / 2 + r * 0.25), outline=RED + (al,), width=6)
            canvas.alpha_composite(rp)
    paste(canvas, BTN, CX, CY + dy, sc, a)
    # tapping hand: slides in, taps on "clic", then leaves
    kh = (t - (T_CLICK - 0.45)) * FPS
    if 0 <= kh < 34:
        hx = CX + BW / 2 - 90; hy = CY + 70
        mv = (1 - ease_out_cubic(kh / 10)) * 120
        tap = math.sin(min(1, max(0, kh - 13) / 6) * math.pi) * 18
        ha = min(1, kh / 4) * (1 - max(0, kh - 26) / 8)
        paste(canvas, HAND, hx + mv, hy + mv - tap, 1 - tap / 200, ha)

def main():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=lanczos,format=rgb24",
                            "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                                "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    f = 0
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        t = f / FPS
        if PREVIEW and not any(abs(t - p) < 0.5 / FPS for p in PREVIEW): f += 1; continue
        canvas = Image.frombuffer("RGB", (W, H), b).convert("RGBA")
        overlay(canvas, t)
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{S}/p4/pv_{t:05.2f}.png")
        else: enc.stdin.write(out.tobytes())
        f += 1
    if not PREVIEW: enc.stdin.close(); enc.wait()

main()
