import json, subprocess, sys, math, re, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
U = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6"
GUY = f"{U}/62adc1d3-1006_23.mp4"
SCR = f"{U}/3aeb6081-screen.mp4"
CLO = f"{U}/635fdc7a-ssstwitter.com_1790759069152_1.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{S}/reel_v2.mp4"
PREVIEW = len(sys.argv) > 2
W, H, FPS = 1080, 1920, 30

RED = (229, 22, 34)
DARK = (17, 17, 19)
WHITE = (255, 255, 255)
FD = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FD + name, size)
FA = f"{S}/fa/fa-solid.ttf"

# ---------------- cut list: remove every silence (keeps 40 ms either side) ----------
SIL = [(0.00, 0.75), (6.03, 6.17), (6.42, 6.55), (8.78, 9.14), (13.22, 13.52), (13.98, 14.99), (21.65, 21.80),
       (24.25, 24.44), (25.69, 26.03), (26.49, 27.24), (35.29, 35.58), (38.69, 38.84), (40.14, 40.29),
       (40.80, 40.98), (47.27, 47.45), (48.49, 48.62), (51.76, 51.91), (55.36, 55.59), (58.30, 58.51),
       (59.28, 59.53), (63.64, 63.94), (66.00, 66.25), (67.49, 67.63), (69.15, 69.37), (70.32, 70.62),
       (72.97, 73.15)]
END = 74.70
PADS = 0.04
KEEP = []
cur = SIL[0][1] - PADS
for a, b in SIL[1:]:
    KEEP.append((cur, a + PADS)); cur = b - PADS
KEEP.append((cur, END))
# snap to the 30 fps grid so audio and video cut on identical boundaries
KEEP = [(round(a * 30) / 30, round(b * 30) / 30) for a, b in KEEP]

def m(t):
    o = 0.0
    for a, b in KEEP:
        if t <= a: return o
        if t < b: return o + t - a
        o += b - a
    return o
TOTAL = m(99)
NF = int(round(TOTAL * FPS))
def fo(t): return int(round(m(t) * FPS))
CUTF = [fo(a) for a, b in KEEP]  # output frame where each kept piece starts

SPLIT = 7.52
CARD = (3.52, 6.08)
F_SPLIT = fo(SPLIT)
TRANS = 9

# ---------------- words ------------------------------------------------------------
raw = json.load(open(f"{S}/words.json"))
def fix(ws):
    out = []
    for w, a in ws:
        if w == "inteligência": w = "inteligencia"
        if w == "Cloud.": w = "Claude."
        if w == "essa": w = "esa"
        if w == "Essas": w = "Estas"
        if w == "aqui": w = "aquí"
        if w == "de" and abs(a - 36.01) < 0.05: w = "del"
        if w == "con" and abs(a - 25.53) < 0.05: continue
        if w == "o" and a > 74: continue
        if w == "tu" and abs(a - 25.85) < 0.05: w = "contigo"
        if w == "web." and a > 74: w = "WEB"
        if 66.0 < a < 69.8: continue
        out.append([w, a])
        if w == "aquí" and abs(a - 65.85) < 0.05:
            out += [[x, y] for x, y in [("todas", 66.25), ("han", 66.57), ("sido", 66.73), ("usando", 67.05),
                    ("este", 67.30), ("método", 67.40), ("y", 67.66), ("estoy", 67.80), ("seguro", 68.05),
                    ("que", 68.40), ("tú", 68.60), ("también", 68.85), ("lo", 69.45)]]
    return out
words = fix([[w, a] for w, a, b in raw])

def norm(s): return re.sub(r"[^\wáéíóúñü$]", "", s.lower())
HL = ["5 mil dólares", "inteligencia artificial", "paso a paso", "descargar este vídeo", "a claude",
      "como ejemplo", "muy importante", "con comparación", "profesionalidad", "alucinando", "este método",
      "tutorial completo", "web"]
HL = [p.split() for p in HL]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []
i = 0
while i < len(words):
    hit = None
    for p in HL:
        if [norm(w) for w, _ in words[i:i + len(p)]] == p and not (p == ["web"] and words[i][0] != "WEB"):
            hit = p; break
    if hit:
        g = words[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [words[i]]; i += 1; hl = False
        while i < len(words) and len(g) < 3 and not PUNCT.search(g[-1][0]):
            if words[i][1] - g[0][1] > 0.75: break
            if sum(len(w) for w, _ in g) + len(words[i][0]) > 15: break
            if words[i][0] == "WEB": break
            if any([norm(w) for w, _ in words[i:i + len(p)]] == p for p in HL if p != ["web"]): break
            g.append(words[i]); i += 1
    txt = " ".join(w for w, _ in g)
    txt = re.sub(r"[¿?¡!.,:;“”\"]", "", txt).lower()
    if hl and txt == "web": txt = "“web”"
    chunks.append(dict(txt=txt, t0=g[0][1], hl=hl, hidden=CARD[0] - 0.05 <= g[0][1] < CARD[1] - 0.05))
merged = []
for c in chunks:
    if merged and c["hl"] and not merged[-1]["hl"] and " " not in merged[-1]["txt"] and len(merged[-1]["txt"]) <= 3 \
            and merged[-1]["hidden"] == c["hidden"]:
        p = merged.pop(); c = dict(c, txt=p["txt"] + " " + c["txt"], t0=p["t0"])
    merged.append(c)
chunks = merged
for c in chunks: c["f0"] = fo(c["t0"])
for k, c in enumerate(chunks):
    c["f1"] = chunks[k + 1]["f0"] if k + 1 < len(chunks) else NF
    c["f1"] = min(c["f1"], c["f0"] + 30)

# ---------------- layout -----------------------------------------------------------
TOP_H = 925                     # dark top panel; talking head below
CW, CH, CX, CY, CR = 1020, 600, 30, 130, 30   # site card
BAND_Y = 752                    # step pill band (below the card, never over it)
CAP_Y = 885                     # caption centre line (between card band and his head)
OFF = 382                       # guy full-frame -> split vertical offset

def vgrad(w, h, c0, c1):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(c0, float)[None, None]; b = np.array(c1, float)[None, None]
    return np.repeat(a * (1 - t) + b * t, w, axis=1)

def shadow_layer(size, box, radius, blur, alpha, offset=(0, 10), color=(0, 0, 0)):
    sh = Image.new("RGBA", size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]), radius,
                                         fill=color + (alpha,))
    return sh.filter(ImageFilter.GaussianBlur(blur))

top_bg = vgrad(W, TOP_H, (22, 22, 25), (12, 12, 14))
yy, xx = np.mgrid[0:TOP_H, 0:W]
gl = np.exp(-(((xx - 540) / 560.0) ** 2 + ((yy - 760) / 200.0) ** 2))[..., None]
top_bg = (top_bg * (1 - 0.22 * gl) + np.array(RED, float) * 0.22 * gl)
top_img = Image.fromarray(top_bg.astype(np.uint8)).convert("RGBA")
top_img.alpha_composite(shadow_layer((W, TOP_H), (CX, CY, CX + CW, CY + CH), CR, 22, 160, (0, 14)))
ImageDraw.Draw(top_img).rounded_rectangle((CX - 2, CY - 2, CX + CW + 1, CY + CH + 1), CR + 2, outline=(255, 255, 255, 30), width=2)
top_base = np.array(top_img.convert("RGB"))
cmask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(cmask).rounded_rectangle((0, 0, CW - 1, CH - 1), CR, fill=255)
cmask_np = np.array(cmask, float)[..., None] / 255

card_bg = vgrad(W, H, (20, 20, 23), (10, 10, 12))
yy, xx = np.mgrid[0:H, 0:W]
g2 = np.exp(-(((xx - 520) / 520.0) ** 2 + ((yy - 680) / 520.0) ** 2))[..., None]
card_bg = (card_bg * (1 - 0.30 * g2) + np.array(RED, float) * 0.30 * g2).astype(np.uint8)

# ---------------- pills (steps) ----------------------------------------------------
SLOTS = [
    (7.52, 14.0, "HECHO CON IA", "Webs creadas en minutos", "", 0),
    (14.85, 18.17, "PASO 1", "Entra en motionsites.ai", "", 1),
    (18.17, 28.6, "PASO 2", "Elige tu diseño favorito", "", 2),
    (28.6, 30.45, "PASO 3", "Descarga el vídeo", "", 3),
    (30.45, 35.4, "PASO 4", "Envíalo a Claude", "", 4),
    (35.4, 40.7, "PASO 5", "Describe tu negocio", "", 5),
    (40.7, 47.4, "PASO 6 · CLAVE", "Pásale el vídeo de ejemplo", "", 6),
    (47.4, 55.55, "POR QUÉ FUNCIONA", "La IA aprende comparando", "", 0),
    (55.55, 64.7, "RESULTADO", "Nivel profesional", "", 0),
    (64.7, 70.4, "MÉTODO PROBADO", "Todas hechas así", "", 0),
    (70.4, 99, "TUTORIAL COMPLETO", "Comenta “WEB”", "", -1),
]
def make_pill(label, text, icon, step):
    fl = font("Inter-Bold.otf", 19); ft = font("InterDisplay-Bold.otf", 34); fi = ImageFont.truetype(FA, 30)
    h, ib = 88, 64
    tw = max(ft.getlength(text), sum(fl.getlength(c) + 2 for c in label))
    w = int(12 + ib + 20 + tw + 30)
    pad = 30
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (pad, pad, pad + w, pad + h), 24, 12, 140, (0, 8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), 24, fill=(30, 30, 34), outline=(64, 64, 70), width=2)
    ix, iy = pad + 12, pad + (h - ib) // 2
    d.rounded_rectangle((ix, iy, ix + ib, iy + ib), 17, fill=RED)
    d.text((ix + ib / 2, iy + ib / 2), icon, font=fi, fill=WHITE, anchor="mm")
    tx, x = ix + ib + 20, ix + ib + 20
    for ch in label:
        d.text((x, pad + 15), ch, font=fl, fill=(255, 84, 92)); x += fl.getlength(ch) + 2
    d.text((tx, pad + 38), text, font=ft, fill=WHITE)
    return im, pad
def progress(step):
    im = Image.new("RGBA", (6 * 30, 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(6):
        d.rounded_rectangle((k * 30, 0, k * 30 + 24, 9), 4, fill=RED if k < step else (70, 70, 76))
    return im
pills = []
for a, b, lab, txt, ic, st in SLOTS:
    im, pad = make_pill(lab, txt, ic, st)
    pills.append(dict(f0=max(fo(a), F_SPLIT + TRANS) if a <= SPLIT else fo(a), f1=min(fo(b), NF), im=im, pad=pad, step=st,
                      prog=progress(st) if st > 0 else None))

# ---------------- captions: white lowercase, red box only on highlights ------------
FC = font("InterDisplay-Bold.otf", 62)
def make_caption(txt, hl):
    tw = FC.getlength(txt); bb = FC.getbbox(txt)
    padx, pady = 22, 12
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        box = (20, 20, w - 20, h - 20)
        im.alpha_composite(shadow_layer((w, h), box, 16, 8, 90, (0, 4)))
        ImageDraw.Draw(im).rounded_rectangle(box, 16, fill=RED + (235,))
    else:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2), txt, font=FC, fill=(0, 0, 0, 200), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, 200))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=FC, fill=WHITE, anchor="mm")
    return im
for c in chunks:
    if not c["hidden"]: c["im"] = make_caption(c["txt"], c["hl"])

# ---------------- sources ----------------------------------------------------------
def guy_cmd():
    v = [f"[0:v]trim=start_frame={round(s * 30)}:end_frame={round(e * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=1:a=0,fps=30,scale={W}:{H}:flags=lanczos,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF), "-f", "rawvideo", "-"]

TOPSEG = [
    (7.52, 14.85, CLO, 12.6, None),
    (14.85, 18.17, SCR, 0.3, 150),
    (18.17, 21.61, SCR, 5.5, 250),
    (21.61, 27.12, SCR, 10.0, 260),
    (27.12, 35.53, SCR, 25.9, 260),
    (35.53, 40.60, SCR, 18.9, 260),
    (40.60, 47.45, SCR, 34.0, 260),
    (47.45, 50.45, SCR, 14.9, 260),
    (50.45, 53.05, SCR, 2.0, 150),
    (53.05, 55.60, SCR, 30.0, 260),
    (55.60, 64.73, CLO, 0.0, None),
    (64.73, 99, CLO, 9.13, None),
]
seg_starts = []
def top_cmd():
    ins, parts = [], []
    for i, (a, b, f, ss, cy) in enumerate(TOPSEG):
        n = min(fo(b), NF) - fo(a); seg_starts.append(fo(a))
        ins += ["-ss", str(ss), "-i", f]
        if cy is None:
            geo = f"crop=1440:758:143:143,scale=-2:{CH}:flags=lanczos,crop={CW}:{CH}"
        else:
            geo = f"crop=1080:{int(round(1080 * CH / CW))}:0:{cy},scale={CW}:{CH}:flags=lanczos"
        parts.append(f"[{i}:v]fps=30,{geo},setsar=1,tpad=stop_mode=clone:stop_duration=3,trim=end_frame={n},setpts=PTS-STARTPTS[s{i}]")
    fc = ";".join(parts) + ";" + "".join(f"[s{i}]" for i in range(len(TOPSEG))) + f"concat=n={len(TOPSEG)}:v=1:a=0,format=rgb24[o]"
    return ["ffmpeg", "-v", "error"] + ins + ["-filter_complex", fc, "-map", "[o]", "-f", "rawvideo", "-"]

# ---------------- audio: voice + light sfx -----------------------------------------
SR = 48000
def sfx_track(whoosh_f, pop_f):
    rng = np.random.default_rng(3)
    n = int(0.34 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); y = 0.0
    for k in range(n):  # one-pole low-pass with rising/falling cutoff
        c = 0.03 + 0.25 * math.sin(math.pi * k / n) ** 2
        y += c * (noise[k] - y); out[k] = y
    env = np.sin(np.pi * np.clip(t / (0.34), 0, 1)) ** 1.6
    whoosh = out / np.abs(out).max() * env * 0.22
    n2 = int(0.08 * SR); t2 = np.arange(n2) / SR
    fr = 950 * np.exp(-t2 * 22) + 260
    pop = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t2 * 45) * 0.30
    trk = np.zeros(int((TOTAL + 1) * SR))
    for f in whoosh_f:
        s = max(0, int((f / FPS - 0.12) * SR)); trk[s:s + len(whoosh)] += whoosh[:len(trk) - s]
    for f in pop_f:
        s = int(f / FPS * SR); trk[s:s + len(pop)] += pop[:len(trk) - s]
    st = np.stack([trk, trk], 1)
    with wave.open(f"{S}/sfx.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())

def audio():
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.008:.3f}:d=0.008[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[1:a]volume=0.9[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{S}/sfx.wav", "-filter_complex", fc, "-map", "[o]",
                    "-ar", "48000", f"{S}/voice2.wav"], check=True)

# ---------------- helpers ----------------------------------------------------------
def ease_out_back(x, s=1.6):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def paste(canvas, im, x, y, scale=1.0, alpha=1.0, center=True):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    if center: x, y = x - im.width / 2, y - im.height / 2
    x, y = int(x), int(y)
    canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))

def zoom(img, z, cx=540, cy=975):
    if abs(z - 1) < 1e-3: return img
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return np.array(Image.fromarray(img).resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h)))

def piece_index(f):
    k = 0
    for i, c in enumerate(CUTF):
        if c <= f: k = i
    return k

F_CARD0, F_CARD1 = fo(CARD[0]), fo(CARD[1])
F_COUNT0, F_COUNT1 = fo(4.40), fo(5.20)
fs_card = font("InterDisplay-Medium.otf", 46); fb_card = font("InterDisplay-Black.otf", 176); fu_card = font("Inter-Bold.otf", 34)
CIRC_Y = 640
def circle_face(guy):
    sq = Image.fromarray(guy[420:1440, 30:1050]).resize((440, 440), Image.LANCZOS)
    mk = Image.new("L", (440, 440), 0); ImageDraw.Draw(mk).ellipse((0, 0, 439, 439), fill=255)
    out = Image.new("RGBA", (560, 560), (0, 0, 0, 0))
    glow = Image.new("RGBA", (560, 560), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((40, 40, 520, 520), outline=RED + (255,), width=14)
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(out).ellipse((48, 48, 512, 512), outline=RED, width=8)
    out.paste(sq, (60, 60), mk)
    return out

def hook_card(guy, f):
    k = f - F_CARD0
    canvas = Image.fromarray(card_bg).convert("RGBA")
    paste(canvas, circle_face(guy), 520, CIRC_Y, scale=max(0.05, 0.5 + 0.5 * ease_out_back(k / 8)))
    d = ImageDraw.Draw(canvas)
    if k >= 3:
        a = min(1, (k - 3) / 5)
        sp = fs_card.getlength(" "); tot = sum(fs_card.getlength(w) for w in CARD_WORDS) + sp * (len(CARD_WORDS) - 1)
        x = 520 - tot / 2
        for j, w in enumerate(CARD_WORDS):
            kk = k - 3 - j * 2
            if kk >= 0:
                im = Image.new("RGBA", (int(fs_card.getlength(w)) + 20, 80), (0, 0, 0, 0))
                ImageDraw.Draw(im).text((10, 10), w, font=fs_card, fill=(225, 225, 230))
                paste(canvas, im, x - 10 + im.width / 2 - 10 + 10, 960 + 30 + (1 - ease_out_cubic(kk / 5)) * 22,
                      scale=0.7 + 0.3 * ease_out_back(kk / 5), alpha=min(1, kk / 3 + 0.2))
            x += fs_card.getlength(w) + sp
    if f >= F_COUNT0 - 3:
        p = ease_out_cubic((f - F_COUNT0) / max(1, F_COUNT1 - F_COUNT0))
        val = int(round(5000 * p / 50.0) * 50)
        num = f"{val:,}".replace(",", ".")
        im = Image.new("RGBA", (980, 230), (0, 0, 0, 0)); di = ImageDraw.Draw(im)
        tw = fb_card.getlength("$" + num); x0 = 490 - tw / 2
        di.text((x0, 10), "$", font=fb_card, fill=RED); di.text((x0 + fb_card.getlength("$"), 10), num, font=fb_card, fill=WHITE)
        paste(canvas, im, 520, 1140, scale=0.88 + 0.12 * ease_out_back((f - F_COUNT0 + 3) / 7))
        if p > 0.95:
            lab = "DÓLARES"; sp = 10
            x = 520 - (sum(fu_card.getlength(c) + sp for c in lab) - sp) / 2
            for ch in lab:
                d.text((x, 1262), ch, font=fu_card, fill=(160, 160, 168)); x += fu_card.getlength(ch) + sp
    return canvas

# ---------------- dynamic hook typography (before the split) -----------------------
HOOK = [  # (small-line word idx, big-line word idx, highlighted idx, end word idx or frame)
    ([0, 1, 2], [3, 4, 5], {5}, 6),
    ([], [6, 7], {7}, "card"),
    ([], [18], set(), 19),
    ([19, 20, 21], [22, 23], {23}, "split"),
]
HS_FONT = font("InterDisplay-SemiBold.otf", 58)
def hook_word(i): return re.sub(r"[¿?¡!.,:;]", "", words[i][0]).lower()
def _fit_big(txt):
    size = 120
    while font("InterDisplay-Black.otf", size).getlength(txt) > 860 and size > 60: size -= 4
    return font("InterDisplay-Black.otf", size)
def layout_line(idx, fnt, y, hl=()):
    ws = [hook_word(i) for i in idx]
    gaps = [fnt.getlength(" ") + (22 if (a in hl or b in hl) else 0) for a, b in zip(idx, idx[1:])]
    tot = sum(fnt.getlength(w) for w in ws) + sum(gaps)
    x = 520 - tot / 2; out = []
    for k, (i, w) in enumerate(zip(idx, ws)):
        out.append((i, w, x, y, fnt)); x += fnt.getlength(w) + (gaps[k] if k < len(gaps) else 0)
    return out
HOOK_L = []
for small, big, hl, end in HOOK:
    fb = _fit_big(" ".join(hook_word(i) for i in big))
    items = []
    by = 340 if small else 300
    if small: items += layout_line(small, HS_FONT, 262)
    items += layout_line(big, fb, by, hl)
    f0 = fo(words[(small or big)[0]][1])
    f1 = F_CARD0 if end == "card" else F_SPLIT if end == "split" else fo(words[end][1])
    HOOK_L.append(dict(items=items, hl=hl, f0=f0, f1=f1))
HOOK_BEATS = [fo(words[i][1]) for _, _, hl, _ in HOOK for i in hl] + [fo(words[18][1])]

def word_sprite(w, fnt, hl, box_p):
    asc, desc = fnt.getmetrics()
    tw = fnt.getlength(w); padx, pady = 18, 6
    W2, H2 = int(tw + 2 * padx + 40), int(asc + desc + 2 * pady + 40)
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    if hl and box_p > 0:
        bw = (tw + 2 * padx) * box_p
        x0 = 20 + (tw + 2 * padx - bw) / 2
        ImageDraw.Draw(im).rounded_rectangle((x0, 20 + desc * 0.35, x0 + bw, H2 - 20 - desc * 0.15), 18, fill=RED + (235,))
    else:
        g = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((20 + padx, 20 + pady), w, font=fnt, fill=(0, 0, 0, 190), stroke_width=4, stroke_fill=(0, 0, 0, 190))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((20 + padx, 20 + pady), w, font=fnt, fill=WHITE)
    return im, 20 + padx, 20 + pady

def hook_text(canvas, f):
    for L in HOOK_L:
        if not (L["f0"] <= f < L["f1"]): continue
        for i, w, x, y, fnt in L["items"]:
            wf = fo(words[i][1])
            if f < wf: continue
            k = f - wf
            sc = 0.55 + 0.45 * ease_out_back(k / 5, 2.2)
            a = min(1.0, k / 2 + 0.2)
            dy = (1 - ease_out_cubic(k / 5)) * 26
            hl = i in L["hl"]
            box_p = ease_out_cubic((k - 1) / 5) if hl else 0
            im, ox, oy = word_sprite(w, fnt, hl, box_p)
            cx = x + fnt.getlength(w) / 2; cy = y + (fnt.getmetrics()[0]) / 2 + dy
            paste(canvas, im, cx + (im.width / 2 - ox - fnt.getlength(w) / 2), cy + (im.height / 2 - oy - fnt.getmetrics()[0] / 2), scale=sc, alpha=a)

def beat_zoom(f):
    z = 0.0
    for b in HOOK_BEATS:
        if b <= f: z = max(z, 0.07 * math.exp(-(f - b) / 6.0))
    return z

CARD_WORDS = "webs con un valor de más de".split()

# ---------------- main -------------------------------------------------------------
def render():
    pops = [p["f0"] for p in pills] + [F_COUNT1]
    whooshes = [F_CARD0, F_CARD1, F_SPLIT] + []
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    tp = subprocess.Popen(top_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    whooshes += seg_starts[1:]
    if not PREVIEW:
        sfx_track(whooshes, pops); audio()
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{S}/voice2.wav", "-c:v", "libx264", "-preset", "slow",
                                "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                                "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(float(x) * FPS)) for x in sys.argv[2].split(",")) if PREVIEW else None
    top = None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if f >= F_SPLIT:
            top = np.frombuffer(tp.stdout.read(CW * CH * 3), np.uint8).reshape(CH, CW, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        pi = piece_index(f)
        if f < F_SPLIT:
            if F_CARD0 <= f < F_CARD1:
                canvas = hook_card(guy, f)
            else:
                z = 1.0 if pi % 2 == 0 else 1.10
                if f >= F_CARD1: z = 1.14
                z += beat_zoom(f)
                canvas = Image.fromarray(zoom(guy, z, 540, 900)).convert("RGBA")
        else:
            e = ease_out_cubic((f - F_SPLIT) / TRANS)
            fr = top_base.copy() if True else None
            full = np.empty((H, W, 3), np.uint8); full[:TOP_H] = top_base; full[TOP_H:] = top_base[-1]
            # site card with whip-in on every content change
            since = min((f - s for s in seg_starts if s <= f), default=99)
            card = top; dx = 0
            if since < 6 and since != f - F_SPLIT:
                q = ease_out_cubic(since / 6); dx = int((1 - q) * 160)
                k = int((1 - q) * 40) + 1
                if k > 1:
                    acc = np.zeros_like(top, dtype=np.float32)
                    for s in range(k): acc += np.roll(top, s - k // 2, axis=1)
                    card = (acc / k).astype(np.uint8)
            y0 = CY - int((1 - e) * 260)
            ys = max(0, y0)
            src = card[ys - y0:]; mm = cmask_np[ys - y0:]
            if dx:
                src = np.roll(src, dx, axis=1)
            reg = full[ys:y0 + CH, CX:CX + CW].astype(np.float32)
            full[ys:y0 + CH, CX:CX + CW] = (reg * (1 - mm) + src * mm).astype(np.uint8)
            # talking head (alternating punch-in on every jump cut)
            z = 1.0 if pi % 2 == 0 else 1.07
            g = zoom(guy, z)
            edge = int(round(TOP_H * e)); shift = int(round(OFF * e))
            full[edge:] = g[edge - shift:H - shift]
            canvas = Image.fromarray(full).convert("RGBA")
            for p in pills:
                if p["f0"] <= f < p["f1"]:
                    k = f - p["f0"]; left = p["f1"] - f
                    a = min(1, k / 4) * min(1, left / 4)
                    dy = (1 - ease_out_back(k / 8)) * 24
                    sc = 1.0
                    if p["step"] == -1: sc = 1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.3)
                    if sc != 1.0:
                        paste(canvas, p["im"], 46 - p["pad"] + p["im"].width / 2, BAND_Y - p["pad"] + p["im"].height / 2 + dy, scale=sc, alpha=a)
                    else:
                        paste(canvas, p["im"], 46 - p["pad"], BAND_Y - p["pad"] + dy, alpha=a, center=False)
                    if p["prog"] is not None:
                        paste(canvas, p["prog"], 1030 - p["prog"].width, BAND_Y + 40 + dy, alpha=a, center=False)
        if f < F_SPLIT and not (F_CARD0 <= f < F_CARD1): hook_text(canvas, f)
        for c in chunks:
            if c["hidden"] or not (c["f0"] <= f < c["f1"]): continue
            if f < F_SPLIT: continue
            k = f - c["f0"]
            sc = 0.86 + 0.14 * ease_out_back(k / 5)
            cy = (430 if f < F_SPLIT else 430 + (CAP_Y - 430) * ease_out_cubic((f - F_SPLIT) / TRANS)) + (1 - ease_out_cubic(k / 5)) * 10
            paste(canvas, c["im"], 520 if f < F_SPLIT else 540, cy, scale=sc, alpha=min(1, 0.35 + k / 3))
        out = np.array(canvas.convert("RGB"))
        if PREVIEW: Image.fromarray(out).save(f"{S}/pv2_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    gp.kill(); tp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "s; chunks", len(chunks), file=sys.stderr)
    render()
