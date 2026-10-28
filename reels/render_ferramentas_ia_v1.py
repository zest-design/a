import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p16"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/2145642b-52_base_flipado.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)
PAGE = (31, 30, 29); CARD = (44, 43, 41); BORDER = (72, 70, 67); TXT = (236, 235, 228); MUTED = (160, 158, 150)
ORANGE = (217, 119, 87); GREEN = (82, 196, 120)
BRAND = {"Perplexity": (32, 128, 141), "Firecrawl": (240, 90, 40), "PostHog": (245, 140, 20), "Playwright": (46, 160, 90), "Composio": (124, 92, 246)}
FD = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(FD + n, int(s))
def serif(s): return ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf", int(s))
def fa(s): return ImageFont.truetype(f"{S}/fa/fa-solid.ttf", int(s))
POP = f"{S}/poppins/Poppins-800.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SPARK = Image.open(f"{S}/p3/spark.png").convert("RGBA")
def spark(h): return SPARK.resize((int(SPARK.width * h / SPARK.height), int(h)), Image.LANCZOS)


# ---------------- cuts -------------------------------------------------------------
SIL = [(0.00, 0.66), (4.12, 4.86), (8.55, 8.68), (9.62, 10.26), (13.19, 13.31), (15.20, 15.76), (20.24, 20.42), (21.27, 21.75),
       (25.35, 25.64), (26.05, 26.48), (27.55, 27.68), (30.54, 30.76), (32.71, 32.94), (34.13, 34.41), (35.40, 35.67), (36.40, 36.56),
       (38.00, 43.24)]
END = 47.30; PAD = 0.04
KEEP = []; cur = max(0, SIL[0][1] - PAD)
for a, b in SIL[1:]:
    KEEP.append((max(0, cur), a + PAD)); cur = b - PAD
KEEP.append((cur, END))
KEEP = [(round(a * 30) / 30, round(b * 30) / 30) for a, b in KEEP]
def m(t):
    o = 0.0
    for a, b in KEEP:
        if t <= a: return o
        if t < b: return o + t - a
        o += b - a
    return o
NF = sum(round(b * 30) - round(a * 30) for a, b in KEEP); TOTAL = NF / FPS
def fo(t): return int(round(m(t) * FPS))

# ---------------- captions ----------------------------------------------------------
PK = json.load(open(f"{P}/wordsA.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (0.66, 4.12, "Para escribir, esta es mala, esta es buena y esta es genial."),
    (4.86, 9.62, "Para investigar, esta es una basura, esta está bien y esta es una locura."),
    (10.26, 15.20, "Para crear apps y sitios web, esta es mala, esta es buena y esta es genial."),
    (15.76, 21.27, "Para crear contenido, esta es una basura, esta está bien y esta es la que necesitas."),
    (21.75, 26.05, "Para programar, esta es terrible, esta es buena y esta es genial."),
    (26.48, 30.54, "Para marketing, esta es mala, esta es buena y esta es genial."),
    (30.76, 35.40, "Si tú quieres aprender muchas más herramientas de inteligencia artificial,"),
    (35.67, 38.00, "síguenos y estate pendiente de nuestros contenidos,"),
    (43.24, 47.28, "porque cada día posteamos aquí las mejores herramientas para diferentes tareas que tú haces hoy."),
]
def align(s0, s1, text):
    ws = text.split()
    pk = [(w, t) for w, t, _ in PK if s0 - 0.3 <= t <= s1 + 0.1]
    a = [norm(w) for w in ws]; b = [norm(w) for w, _ in pk]
    times = [None] * len(ws)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1): times[i1 + k] = pk[j1 + k][1]
    anchors = [(-1, s0)] + [(i, t) for i, t in enumerate(times) if t is not None] + [(len(ws), s1)]
    for i in range(len(ws)):
        if times[i] is None:
            lo = max(x for x in anchors if x[0] < i); hi = min(x for x in anchors if x[0] > i)
            span = ws[lo[0] + 1:hi[0]]; tot = sum(len(w) + 2 for w in span) or 1
            pre = sum(len(w) + 2 for w in ws[lo[0] + 1:i]); t0 = lo[1] + (0.25 if lo[0] >= 0 else 0)
            times[i] = t0 + (hi[1] - t0) * pre / tot
    for i in range(1, len(times)): times[i] = max(times[i], times[i - 1] + 0.06)
    return [(w, t, k == len(ws) - 1, s1) for k, (w, t) in enumerate(zip(ws, times))]
WORDS = []
for sg in SEGS: WORDS += align(*sg)
HL = [["escribir"], ["investigar"], ["apps"], ["contenido"], ["programar"], ["marketing"], ["ZZZZ"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("ZZZZ"): return ["ZZZZ"]
    return next((p for p in HL if p != ["ZZZZ"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
chunks = []; i = 0
while i < len(WORDS):
    hit = hl_at(i)
    if hit: g = WORDS[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [WORDS[i]]; i += 1; hl = False
        while i < len(WORDS) and len(g) < 3 and not PUNCT.search(g[-1][0]) and not g[-1][2]:
            if WORDS[i][1] - g[0][1] > 0.8 or sum(len(w[0]) for w in g) + len(WORDS[i][0]) > 16 or hl_at(i): break
            g.append(WORDS[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w[0] for w in g))
    key = False
    if not hl: txt = txt.lower().replace("claude", "Claude")
    end = g[-1][3] + 0.25 if g[-1][2] else None
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1], end=end, key=key))
for k, c in enumerate(chunks):
    if k and chunks[k - 1]["key"]: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.0)
    if k: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 0.3)
for k, c in enumerate(chunks):
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else 99
    c["t1"] = min(nxt, c["end"] or nxt, c["t0"] + 1.6)
    c["f0"], c["f1"] = fo(c["t0"]), fo(c["t1"])

FC = font("InterDisplay-Bold.otf", 62); FK = font("InterDisplay-Black.otf", 120)
def make_caption(txt, hl, key):
    f = FK if key else FC
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 26, 14
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 24, w - 20, h - 16), 18, fill=(0, 0, 0, 110))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, w - 20, h - 20), 18, fill=RED)
    else:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=f, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=f, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"], c["key"])

# ---------------- helpers ----------------------------------------------------------
def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def paste(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
def pop(k, n=7): return 0.75 + 0.25 * ease_out_back(k / n), min(1, k / 3 + 0.2), (1 - ease_out_cubic(k / n)) * 26
def emoji(ch, h):
    ef = ImageFont.truetype(EMOJI, 109)
    e = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); ImageDraw.Draw(e).text((75, 75), ch, font=ef, embedded_color=True, anchor="mm")
    e = e.crop(e.getbbox()); return e.resize((int(e.width * h / e.height), int(h)), Image.LANCZOS)
def white_boxes(lines, size=52, em=None):
    ft = ImageFont.truetype(POP, size); pad, pitch, r = 30, int(size * 1.5), 12
    e = emoji(em, size * 1.05) if em else None
    ws = [ft.getlength(l) + 2 * pad + ((e.width + 16) if (e and k == len(lines) - 1) else 0) for k, l in enumerate(lines)]
    Wd, Hd = int(max(ws)) + 4, pitch * len(lines) + 8
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = Wd / 2
    for k, w in enumerate(ws):
        y0 = 2 + k * pitch; d.rounded_rectangle((cx - w / 2, y0 - (2 if k else 0), cx + w / 2, y0 + pitch + 2), r, fill=WHITE)
    for k, (l, w) in enumerate(zip(lines, ws)):
        yc = 2 + k * pitch + pitch / 2 + 3; x0 = cx - w / 2 + pad
        d.text((x0, yc), l, font=ft, fill=(0, 0, 0), anchor="lm")
        if e and k == len(lines) - 1: im.alpha_composite(e, (int(x0 + ft.getlength(l) + 16), int(yc - e.height / 2 - 1)))
    return im
CHECK = chr(0xf00c)
def rr(d, box, r, **kw): d.rounded_rectangle(box, r, **kw)


def it(d, xy, icon, text, fnt, fill, anchor="lm", icol=None):
    # icon (Font Awesome) + text, drawn with the right fonts
    fi = fa(fnt.size * 0.9); gap = fnt.size * 0.45
    w = fi.getlength(icon) + gap + fnt.getlength(text); x, y = xy
    if anchor == "mm": x -= w / 2
    d.text((x, y), icon, font=fi, fill=icol or fill, anchor="lm"); d.text((x + fi.getlength(icon) + gap, y), text, font=fnt, fill=fill, anchor="lm")
PAGE = (31, 30, 29); CB_BG = (44, 43, 41); CB_BORDER = (70, 69, 66); CB_TEXT = (236, 235, 228)
CB_MUTED = (156, 154, 146); CB_CHIP = (66, 65, 62); CB_GROUP = (52, 51, 49); BUBBLE = (20, 20, 19)
CLAUDE_ORANGE = (217, 119, 87)
SS = 2
F_UI = font("Inter-Medium.otf", 26 * SS); F_UI2 = font("Inter-Regular.otf", 26 * SS)
FT = font("Inter-Regular.otf", 32 * SS); FR = font("Inter-Regular.otf", 33 * SS)
LH = 46

# ---------------- audio ------------------------------------------------------------
SR = 48000
def sfx(events):
    rng = np.random.default_rng(9); trk = np.zeros(int((TOTAL + 1) * SR))
    def add(sig, t):
        s = int(t * SR); e = min(len(trk), s + len(sig)); trk[s:e] += sig[:e - s]
    n = int(0.42 * SR); t = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n); y = 0.0
    for k in range(n):
        cc = 0.02 + 0.18 * math.sin(math.pi * k / n) ** 2; y += cc * (noise[k] - y); out[k] = y
    whoosh = out / np.abs(out).max() * np.sin(np.pi * t / 0.42) ** 1.8 * 0.15
    n2 = int(0.16 * SR); t2 = np.arange(n2) / SR   # soft low "pluck" for pop-ins (no high clicks)
    pluck = (np.sin(2 * np.pi * 330 * t2) * 0.6 + np.sin(2 * np.pi * 495 * t2) * 0.25) * (1 - np.exp(-t2 * 400)) * np.exp(-t2 * 26) * 0.07
    n4 = int(1.4 * SR); t4 = np.arange(n4) / SR
    boom = np.sin(2 * np.pi * (52 + 30 * np.exp(-t4 * 8)) * t4) * np.exp(-t4 * 3.2) * 0.32 + rng.standard_normal(n4) * np.exp(-t4 * 18) * 0.04
    pad = sum(np.sin(2 * np.pi * fq * t4) for fq in (440, 554.4, 659.3)) * np.exp(-t4 * 2.2) * (1 - np.exp(-t4 * 30)) * 0.02
    for kind, tt in events:
        if kind == "whoosh": add(whoosh, max(0, tt - 0.18))
        elif kind == "pluck": add(pluck, tt)
        elif kind == "boom": add(boom + pad, tt)
    st = np.stack([trk, trk], 1)
    with wave.open(f"{P}/sfx.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
def audio(events):
    sfx(events)
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.008:.4f}:d=0.008[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[1:a]volume=1.0[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{P}/sfx.wav", "-filter_complex", fc, "-map", "[o]", "-ar", "48000", f"{P}/voice.wav"], check=True)
def guy_cmd():
    v = [f"[0:v]trim=start_frame={round(s * 30)}:end_frame={round(e * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=1:a=0,fps=30,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF), "-f", "rawvideo", "-"]


# ================= Tool-tier video: dark flip cards over full-screen talking head =================
CARD_W, CARD_H, CARD_R = 230, 250, 28
CARD_BG = (20, 20, 22); CARD_EDGE = (62, 62, 68)
LOGO_BOX = 128                       # every logo is fitted to the same square, so all cards read equally
LOGO_DIR, TMP_DIR = f"{P}/logos", f"{P}/tmplogos"
import os
def load_logo(name):
    for d in (LOGO_DIR, TMP_DIR):
        p_ = f"{d}/{name}.png"
        if os.path.exists(p_): return Image.open(p_).convert("RGBA")
    raise FileNotFoundError(name)
def fit_logo(im, box=LOGO_BOX, fill=0.92):
    bb = im.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox(); im = im.crop(bb) if bb else im
    # optical balance: wide marks get the full width, tall/square marks a slightly smaller square
    k = box * fill / max(im.width, im.height)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", (box, box), (0, 0, 0, 0)); out.alpha_composite(im, ((box - im.width) // 2, (box - im.height) // 2))
    return out
def manus_claude():
    # both marks shown complete, side by side, same optical height
    a = fit_logo(load_logo("manus"), 112, 1.0); b = fit_logo(load_logo("claude"), 112, 0.86)
    out = Image.new("RGBA", (112 * 2 + 64, 112), (0, 0, 0, 0)); out.alpha_composite(a, (0, 0))
    ImageDraw.Draw(out).text((112 + 32, 56), "+", font=font("InterDisplay-Bold.otf", 60), fill=(225, 225, 230), anchor="mm")
    out.alpha_composite(b, (112 + 64, 0)); return fit_logo(out, LOGO_BOX + 70, 1.0)
F_NAME = font("Inter-SemiBold.otf", 23)
def card_shadow():
    im = Image.new("RGBA", (CARD_W + 80, CARD_H + 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((40, 52, 40 + CARD_W, 52 + CARD_H), CARD_R, fill=(0, 0, 0, 150))
    return im.filter(ImageFilter.GaussianBlur(18))
SHADOW = card_shadow()
def card_base():
    im = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, CARD_W - 1, CARD_H - 1), CARD_R, fill=CARD_BG, outline=CARD_EDGE, width=2)
    # soft top sheen so the dark card still reads as a physical object
    sh = Image.new("L", (CARD_W, CARD_H), 0); ImageDraw.Draw(sh).rounded_rectangle((2, 2, CARD_W - 3, CARD_H // 2), CARD_R, fill=18)
    im.alpha_composite(Image.merge("RGBA", (sh.point(lambda v: 255),) * 3 + (sh,)))
    return im
def card_front(name, logo):
    im = card_base(); d = ImageDraw.Draw(im)
    d.text((CARD_W / 2, 40), name.upper(), font=F_NAME, fill=(212, 212, 218), anchor="mm")
    im.alpha_composite(logo, ((CARD_W - logo.width) // 2, 84 + (LOGO_BOX - logo.height) // 2))
    return im
def card_back():
    im = card_base(); d = ImageDraw.Draw(im)
    d.text((CARD_W / 2, CARD_H / 2 + 4), "?", font=ImageFont.truetype(POP, 112), fill=(64, 64, 70), anchor="mm")
    return im
BACK = card_back()

CATS = [  # (start, label, [(name, logo key), ...], reveal times for each card)
    (0.66, "¿Para escribir?", [("Grok", "grok"), ("ChatGPT", "chatgpt"), ("Claude", "claude")], (1.44, 2.32, 3.28)),
    (4.86, "¿Para investigar?", [("Wikipedia", "wikipedia"), ("Gemini", "gemini"), ("Perplexity", "perplexity")], (5.68, 7.12, 8.16)),
    (10.26, "¿Para crear apps y webs?", [("WordPress", "wordpress"), ("Shopify", "shopify"), ("Lovable", "lovable")], (12.08, 13.28, 14.32)),
    (15.76, "¿Para crear contenido?", [("Canva", "canva"), ("Claude", "claude"), ("Poppy AI", "poppy")], (16.88, 18.55, 19.75)),
    (21.75, "¿Para programar?", [("Terminal", "terminal"), ("Claude Code", "claudecode"), ("Codex", "codex")], (22.55, 23.67, 24.79)),
    (26.48, "¿Para marketing?", [("ChatGPT", "chatgpt"), ("Claude", "claude"), ("Manus + Claude", "manus+claude")], (27.67, 28.55, 29.51)),
]
FRONTS = []
for st, lab, tools, rv in CATS:
    row = []
    for nm, key in tools:
        lg = manus_claude() if key == "manus+claude" else fit_logo(load_logo(key))
        row.append(card_front(nm, lg))
    FRONTS.append(row)
CAT_IM = [white_boxes([lab], 46) for _, lab, _, _ in CATS]
TIER = [("MALA", (226, 38, 38)), ("BUENA", (222, 160, 0)), ("LA MEJOR", (34, 168, 74))]
TIER_F = ImageFont.truetype(POP, 38)
def tier_label(txt, col, on):
    w_ = int(TIER_F.getlength(txt)) + 36; im = Image.new("RGBA", (w_ + 20, 82), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if on:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((10, 16, w_ + 10, 74), 14, fill=(0, 0, 0, 110))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6))); d.rounded_rectangle((10, 10, w_ + 10, 68), 14, fill=col)
    d.text((w_ / 2 + 10, 40), txt, font=TIER_F, fill=WHITE if on else (12, 12, 14), anchor="mm")
    return im
TIER_OFF = [tier_label(t, c, False) for t, c in TIER]; TIER_ON = [tier_label(t, c, True) for t, c in TIER]
TIER_T = [(1.92, 2.72, 3.68), (6.40, 7.68, 9.04), (12.64, 13.68, 14.72), (17.91, 19.19, 20.31), (23.03, 24.07, 25.51), (28.07, 28.87, 29.99)]
POS = [(240, 448), (540, 418), (840, 448)]      # card centres (middle one raised, like the reference)
CAT_Y = 612; CAP_Y = 714; F_END = fo(30.76)

def persp_coeffs(src, dst):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()
def flipped(img, ang):
    """Rotate a card around its vertical axis by ang (0 = facing us) with real perspective."""
    w, h = img.size; c = math.cos(ang); s = math.sin(ang); fz = 1100.0
    if abs(c) < 0.02: return None
    pts = []
    for X, Y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x3, z3 = X * c, X * s; k = fz / (fz + z3); pts.append((x3 * k, Y * k))
    pad = 40; W2 = int(w + 2 * pad); H2 = int(h + 2 * pad)
    dst = [(x + W2 / 2, y + H2 / 2) for x, y in pts]; src = [(0, 0), (w, 0), (w, h), (0, h)]
    out = img.transform((W2, H2), Image.PERSPECTIVE, persp_coeffs(src, dst), Image.BICUBIC)
    shade = 1 - 0.35 * abs(s)
    if shade < 1:
        a = out.getchannel("A"); out = Image.eval(out.convert("RGB"), lambda v: int(v * shade)).convert("RGBA"); out.putalpha(a)
    return out
FLIP = 11   # frames per half-turn
def card_state(ci, i, f):
    """Return (image, angle) for card i in category ci at frame f."""
    st, _, _, rv = CATS[ci]
    fr = fo(rv[i])
    if f < fr: ang = math.pi
    else: ang = math.pi * (1 - ease_io((f - fr) / FLIP))
    if ci > 0:   # previous category's card flips away first
        f0 = fo(st)
        if f < f0 + FLIP:
            p = ease_io((f - f0) / FLIP); a2 = math.pi * p
            return (FRONTS[ci - 1][i], a2) if a2 < math.pi / 2 else (BACK, a2 - math.pi)
    return (FRONTS[ci][i], ang) if ang < math.pi / 2 else (BACK, ang - math.pi)
def cat_at(f):
    c = -1
    for k, (st, _, _, _) in enumerate(CATS):
        if f >= fo(st): c = k
    return c

# follow card for the outro
def follow_card(f):
    im = Image.new("RGBA", (720, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, 719, 229), 30, fill=CARD_BG, outline=CARD_EDGE, width=2)
    d.ellipse((40, 55, 160, 175), fill=(52, 52, 58)); d.text((100, 116), IC(0xf007), font=fa(54), fill=(200, 200, 206), anchor="mm")
    d.text((190, 92), "Herramientas de IA", font=font("InterDisplay-Bold.otf", 40), fill=WHITE, anchor="lm")
    d.text((190, 140), "Nuevas cada día", font=font("Inter-Medium.otf", 28), fill=(160, 160, 168), anchor="lm")
    on = f >= fo(35.67)
    rr(d, (190, 166, 400, 214), 14, fill=(52, 52, 58) if on else (0, 149, 246))
    d.text((295, 190), "Siguiendo" if on else "Seguir", font=font("Inter-SemiBold.otf", 26), fill=WHITE, anchor="mm")
    return im
IC = lambda h: chr(h)

def overlay(canvas, f):
    ci = cat_at(f)
    if 0 <= ci and f < F_END + 10:
        out_p = ease_io((f - F_END) / 10) if f >= F_END else 0.0
        for i in range(3):
            face, ang = card_state(ci, i, f)
            x, y = POS[i]
            k0 = f - fo(CATS[0][0])
            s_in = 0.7 + 0.3 * ease_out_back(min(1, k0 / 8)) if ci == 0 else 1.0
            a_in = min(1, 0.2 + k0 / 4) if ci == 0 else 1.0
            img = flipped(face, ang)
            sh = SHADOW
            alpha = a_in * (1 - out_p); sc = s_in * (1 - 0.15 * out_p)
            cw = max(0.08, abs(math.cos(ang)))
            shn = sh.resize((max(1, int(sh.width * cw)), sh.height))
            paste(canvas, shn, x, y + 6, sc, alpha * 0.9)
            if img is not None: paste(canvas, img, x, y, sc, alpha)
            # tier label
            tw = fo(TIER_T[ci][i])
            if f >= tw:
                kk = f - tw; paste(canvas, TIER_ON[i], x, y - CARD_H / 2 - 32, sc * (0.8 + 0.2 * ease_out_back(kk / 6)), alpha)
            else: paste(canvas, TIER_OFF[i], x, y - CARD_H / 2 - 32, sc, alpha)
        # category question (white box) under the cards
        k = f - fo(CATS[ci][0]); s, a, dy = pop(k)
        paste(canvas, CAT_IM[ci], 540, CAT_Y + dy, s * (1 - 0.15 * out_p), a * (1 - out_p))
    if f >= F_END:
        k = f - F_END; s, a, dy = pop(k - 8)
        if k >= 8: paste(canvas, follow_card(f), 540, 470 + dy, s, a)
    for ch in chunks:
        if not (ch["f0"] <= f < ch["f1"]): continue
        k = f - ch["f0"]
        paste(canvas, ch["im"], 540, CAP_Y + (1 - ease_out_cubic(k / 5)) * 8, 0.86 + 0.14 * ease_out_back(k / 5), min(1, 0.35 + k / 3))

def events():
    ev = []
    for ci, (st, _, _, rv) in enumerate(CATS):
        ev.append(("whoosh", fo(st) / FPS))
        for t in rv: ev.append(("pluck", fo(t) / FPS))
    ev.append(("whoosh", F_END / FPS)); ev.append(("pluck", fo(35.67) / FPS))
    return ev

def main():
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        audio(events())
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        canvas = Image.fromarray(guy).convert("RGBA")
        overlay(canvas, f)
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), file=sys.stderr)
    main()
