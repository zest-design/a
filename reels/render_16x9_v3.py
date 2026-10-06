import sys, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Reuse timeline, words, captions, pills, sfx and audio from the vertical v3 script.
_out = sys.argv[1] if len(sys.argv) > 1 else "/dev/null"
_prev = sys.argv[2] if len(sys.argv) > 2 else None
sys.argv = ["render3.py", _out] + ([_prev] if _prev else [])
_src = open("/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad/render3.py").read()
exec(_src.split("# ---------------- main ----")[0])

W, H = 1920, 1080
# ---------------- 16:9 layout ------------------------------------------------------
LX0, LX1 = 80, 1250            # left content column
LCX = (LX0 + LX1) // 2
CW, CH, CX, CY, CR = 1170, 658, 80, 80, 30    # site card (16:9)
BAND_Y = 768
CAP_Y = 950
GW, GH, GX, GY, GR = 560, 960, 1290, 60, 32  # talking-head card
GCROP_Y = 20                  # source crop: 720 x 1234 from y=20

bg = vgrad(W, H, (22, 22, 25), (11, 11, 13))
yy, xx = np.mgrid[0:H, 0:W]
gl = np.exp(-(((xx - 700) / 700.0) ** 2 + ((yy - 900) / 380.0) ** 2))[..., None]
gl2 = np.exp(-(((xx - 1570) / 420.0) ** 2 + ((yy - 560) / 600.0) ** 2))[..., None]
bg = bg * (1 - 0.16 * gl - 0.12 * gl2) + np.array(RED, float) * (0.16 * gl + 0.12 * gl2)
base_img = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
base_img.alpha_composite(shadow_layer((W, H), (GX, GY, GX + GW, GY + GH), GR, 24, 170, (0, 14)))
base_hook = np.array(base_img.convert("RGB"))
split_img = base_img.copy()
split_img.alpha_composite(shadow_layer((W, H), (CX, CY, CX + CW, CY + CH), CR, 24, 170, (0, 14)))
ImageDraw.Draw(split_img).rounded_rectangle((CX - 2, CY - 2, CX + CW + 1, CY + CH + 1), CR + 2, outline=(255, 255, 255, 30), width=2)
base_split = np.array(split_img.convert("RGB"))

def rmask(w, h, r):
    mk = Image.new("L", (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return mk
cmask = rmask(CW, CH, CR); cmask_np = np.array(cmask, float)[..., None] / 255
gmask_np = np.array(rmask(GW, GH, GR), float)[..., None] / 255

def guy_cmd16():
    v = [f"[0:v]trim=start_frame={round(s * 30)}:end_frame={round(e * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=1:a=0,fps=30,crop=720:1234:0:{GCROP_Y},scale={GW}:{GH}:flags=lanczos,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF), "-f", "rawvideo", "-"]

def zoom_small(img, z, cx, cy):
    if abs(z - 1) < 1e-3: return img
    h, w = img.shape[:2]; ww, hh = w / z, h / z
    x0 = min(max(cx - ww / 2, 0), w - ww); y0 = min(max(cy - hh / 2, 0), h - hh)
    return np.array(Image.fromarray(img).resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + ww, y0 + hh)))
FACE = (GW / 2, (640 - GCROP_Y) * GW / 720)   # eyes in card coords

# ---------------- hook typography (left column) ------------------------------------
HS_FONT = font("InterDisplay-SemiBold.otf", 66)
def _fit_big(txt):
    size = 156
    while font("InterDisplay-Black.otf", size).getlength(txt) > LX1 - LX0 - 60 and size > 70: size -= 4
    return font("InterDisplay-Black.otf", size)
def layout_line(idx, fnt, y, hl=()):
    ws = [hook_word(i) for i in idx]
    gaps = [fnt.getlength(" ") + (26 if (a in hl or b in hl) else 0) for a, b in zip(idx, idx[1:])]
    tot = sum(fnt.getlength(w) for w in ws) + sum(gaps)
    x = LCX - tot / 2; out = []
    for k, (i, w) in enumerate(zip(idx, ws)):
        out.append((i, w, x, y, fnt)); x += fnt.getlength(w) + (gaps[k] if k < len(gaps) else 0)
    return out
HOOK_L = []
for small, big, hl, end in HOOK:
    fb = _fit_big(" ".join(hook_word(i) for i in big))
    items = []
    if small: items += layout_line(small, HS_FONT, 400)
    items += layout_line(big, fb, 490 if small else 450, hl)
    f0 = fo(words[(small or big)[0]][1])
    f1 = F_CARD0 if end == "card" else F_SPLIT if end == "split" else fo(words[end][1])
    HOOK_L.append(dict(items=items, hl=hl, f0=f0, f1=f1))

fs16 = font("InterDisplay-Medium.otf", 58); fb16 = font("InterDisplay-Black.otf", 230); fu16 = font("Inter-Bold.otf", 40)
def card16(canvas, f):
    k = f - F_CARD0
    sp = fs16.getlength(" "); tot = sum(fs16.getlength(w) for w in CARD_WORDS) + sp * (len(CARD_WORDS) - 1)
    x = LCX - tot / 2
    for j, w in enumerate(CARD_WORDS):
        kk = k - j * 2
        if kk >= 0:
            im = Image.new("RGBA", (int(fs16.getlength(w)) + 20, 90), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((10, 10), w, font=fs16, fill=(225, 225, 230))
            paste(canvas, im, x - 10 + im.width / 2, 330 + (1 - ease_out_cubic(kk / 5)) * 24,
                  scale=0.7 + 0.3 * ease_out_back(kk / 5), alpha=min(1, kk / 3 + 0.2))
        x += fs16.getlength(w) + sp
    if f >= F_COUNT0 - 3:
        p = ease_out_cubic((f - F_COUNT0) / max(1, F_COUNT1 - F_COUNT0))
        num = f"{int(round(5000 * p / 50.0) * 50):,}".replace(",", ".")
        im = Image.new("RGBA", (1150, 300), (0, 0, 0, 0)); di = ImageDraw.Draw(im)
        tw = fb16.getlength("$" + num); x0 = 575 - tw / 2
        di.text((x0, 10), "$", font=fb16, fill=RED); di.text((x0 + fb16.getlength("$"), 10), num, font=fb16, fill=WHITE)
        paste(canvas, im, LCX, 560, scale=0.88 + 0.12 * ease_out_back((f - F_COUNT0 + 3) / 7))
        if p > 0.95:
            d = ImageDraw.Draw(canvas); lab = "DÓLARES"; sp2 = 12
            x = LCX - (sum(fu16.getlength(c) + sp2 for c in lab) - sp2) / 2
            for ch in lab:
                d.text((x, 720), ch, font=fu16, fill=(160, 160, 168)); x += fu16.getlength(ch) + sp2

def blend_into(full, img, x, y, mask, alpha=1.0):
    h, w = img.shape[:2]
    reg = full[y:y + h, x:x + w].astype(np.float32); m = mask * alpha
    full[y:y + h, x:x + w] = (reg * (1 - m) + img * m).astype(np.uint8)

# ---------------- main -------------------------------------------------------------
def render16():
    pops = [p["f0"] for p in pills] + [F_COUNT1]
    whooshes = [F_CARD0, F_CARD1, F_SPLIT]
    gp = subprocess.Popen(guy_cmd16(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    tp = subprocess.Popen(top_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    whooshes += seg_starts[1:]
    if not PREVIEW:
        sfx_track(whooshes, pops); audio()
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{S}/voice2.wav", "-c:v", "libx264", "-preset", "slow",
                                "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                                "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(float(x) * FPS)) for x in sys.argv[2].split(",")) if PREVIEW else None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(GW * GH * 3), np.uint8).reshape(GH, GW, 3)
        top = np.frombuffer(tp.stdout.read(CW * CH * 3), np.uint8).reshape(CH, CW, 3) if f >= F_SPLIT else None
        if want is not None and f not in want:
            if f > max(want): break
            continue
        pi = piece_index(f)
        z = (1.0 if pi % 2 == 0 else 1.08)
        if f < F_SPLIT: z += beat_zoom(f)
        e = ease_out_cubic((f - F_SPLIT) / TRANS) if f >= F_SPLIT else 0.0
        if f < F_SPLIT: full = base_hook.copy()
        elif e >= 1: full = base_split.copy()
        else: full = (base_hook * (1 - e) + base_split * e).astype(np.uint8)
        if f >= F_SPLIT:
            since = min((f - s for s in seg_starts if s <= f), default=99)
            card = top
            if since < 6 and since != f - F_SPLIT:
                q = ease_out_cubic(since / 6); k = int((1 - q) * 40) + 1
                if k > 1:
                    acc = np.zeros_like(top, dtype=np.float32)
                    for s in range(k): acc += np.roll(top, s - k // 2, axis=1)
                    card = np.roll((acc / k).astype(np.uint8), int((1 - q) * 160), axis=1)
            yoff = int((1 - e) * 90)
            blend_into(full, card, CX, CY + yoff if CY + yoff + CH <= H else CY, cmask_np, alpha=e)
        g = zoom_small(guy, z, *FACE)
        blend_into(full, g, GX, GY, gmask_np)
        canvas = Image.fromarray(full).convert("RGBA")
        if f < F_SPLIT:
            if F_CARD0 <= f < F_CARD1: card16(canvas, f)
            else: hook_text(canvas, f)
        else:
            for p in pills:
                if p["f0"] <= f < p["f1"]:
                    k = f - p["f0"]; left = p["f1"] - f
                    a = min(1, k / 4) * min(1, left / 4)
                    dy = (1 - ease_out_back(k / 8)) * 24
                    if p["step"] == -1:
                        sc = 1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.3)
                        paste(canvas, p["im"], LX0 - p["pad"] * 1.2 + p["im"].width * 0.6, BAND_Y - p["pad"] * 1.2 + p["im"].height * 0.6 + dy, scale=sc * 1.2, alpha=a)
                    else:
                        paste(canvas, p["im"], LX0 - p["pad"] * 1.2, BAND_Y - p["pad"] * 1.2 + dy, scale=1.2, alpha=a, center=False)
                    if p["prog"] is not None:
                        paste(canvas, p["prog"], LX1 - p["prog"].width, BAND_Y + 50 + dy, alpha=a, center=False)
            for c in chunks:
                if c["hidden"] or not (c["f0"] <= f < c["f1"]): continue
                k = f - c["f0"]
                sc = 0.86 + 0.14 * ease_out_back(k / 5)
                paste(canvas, c["im"], LCX, CAP_Y + (1 - ease_out_cubic(k / 5)) * 10, scale=sc * 1.08, alpha=min(1, 0.35 + k / 3) * min(1, e * 2))
        out = np.array(canvas.convert("RGB"))
        if PREVIEW: Image.fromarray(out).save(f"{S}/pv16_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    gp.kill(); tp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

render16()
