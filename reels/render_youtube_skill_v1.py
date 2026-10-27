import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p12"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/46d809d5-4848.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)
PAGE = (33, 33, 33); CARD = (47, 47, 47); BORDER = (72, 72, 72); TXT = (236, 236, 236); MUTED = (160, 160, 160)
ORANGE = (220, 40, 40); GREEN = (82, 196, 120)
FD = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(FD + n, int(s))
def serif(s): return ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf", int(s))
def fa(s): return ImageFont.truetype(f"{S}/fa/fa-solid.ttf", int(s))
POP = f"{S}/poppins/Poppins-800.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SPARK = Image.open(f"{S}/p3/spark.png").convert("RGBA")
def spark(h): return SPARK.resize((int(SPARK.width * h / SPARK.height), int(h)), Image.LANCZOS)

# ---------------- cuts -------------------------------------------------------------
SIL = [(0.04, 0.32), (6.18, 6.39), (6.41, 6.58), (10.22, 10.47), (12.00, 12.16), (15.20, 15.36), (15.38, 15.55), (18.53, 18.91),
       (25.90, 26.10), (26.15, 26.32), (30.81, 31.07), (31.44, 31.74), (35.10, 35.35), (35.35, 35.59), (44.86, 45.04), (45.07, 45.26),
       (47.02, 47.29), (47.91, 48.20), (48.37, 48.85), (51.52, 51.91), (51.92, 52.13), (57.37, 57.58), (57.58, 57.88), (61.41, 61.64),
       (63.57, 63.81), (65.04, 65.17)]
END = 65.80; PAD = 0.04
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
    (0.32, 2.45, "ChatGPT acaba de matar a YouTube."),
    (2.56, 6.18, "Ahora puedes conectar ChatGPT a YouTube y gestionar todo tu canal por ti."),
    (6.40, 10.22, "Esta skill se llama YouTube Agent Skill y es completamente gratuita."),
    (10.40, 15.20, "No es una sola skill de ChatGPT, son 11 y cada una hace un trabajo distinto."),
    (15.28, 18.53, "Una escribe tus vídeos basándose en 21 fórmulas de ganchos probadas."),
    (18.86, 25.90, "Otra te genera las miniaturas y los títulos, otra edita tus vídeos, otra se encarga de los comentarios y otra planifica toda tu semana de YouTube."),
    (26.15, 30.81, "Así te ayuda a saber qué publicar, cuándo publicar y cómo conseguir que la gente vea tus vídeos."),
    (31.07, 35.10, "Lo más loco que he visto de esta skill es que encuentra los vídeos más virales,"),
    (35.59, 41.30, "busca en tu nicho, analiza títulos, ganchos, estructuras y los recrea completamente para ti."),
    (41.40, 44.86, "Así jamás te quedas atascado intentando averiguar qué tipo de contenido crear."),
    (45.26, 47.91, "Vas a recibir siempre vídeos virales con tu voz y"),
    (48.66, 51.52, "adaptados a tu audiencia porque ha analizado previamente tus vídeos."),
    (52.08, 57.37, "Para configurarlo por completo, pega este enlace en ChatGPT y escríbele Install_Skill."),
    (57.88, 61.41, "Si quieres la configuración completa, he preparado un PDF con un paso a paso para ti,"),
    (61.64, 65.71, "que si tú comentas aquí abajo YOUTUBE y nos sigues, te lo voy a hacer llegar."),
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
HL = [["youtube", "agent", "skill"], ["gratuita"], ["11"], ["21"], ["virales"], ["YOUTUBE"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("YOUTUBE"): return ["YOUTUBE"]
    return next((p for p in HL if p != ["YOUTUBE"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "YOUTUBE"
    if not hl: txt = txt.lower().replace("chatgpt", "ChatGPT").replace("youtube", "YouTube").replace("pdf", "PDF").replace("install_skill", "Install Skill")
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
KEY = next(c for c in chunks if c["key"])

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

# ---------------- layout -----------------------------------------------------------
TOP = 820                    # top panel (visuals); talking head below
SHIFT = 320                  # bottom panel shows his face centred
CAP_SPLIT, CAP_FULL = 800, 1480
F_SPLIT0, F_SPLIT1 = fo(2.56), fo(57.62)
TRANS = 9
TITLE = white_boxes(["ASÍ CHATGPT CAMBIA", "TU FORMA DE CREAR", "EN YOUTUBE"], 56)
SC = [(2.56, "A"), (6.40, "B"), (10.40, "C"), (15.28, "D"), (26.15, "E"), (31.07, "V"), (45.26, "W"), (52.08, "Z")]
SC = [(fo(t), n) for t, n in SC]
def scene_at(f):
    s_ = None
    for f0, n in SC:
        if f >= f0: s_ = (f0, n)
    return s_
def T(t): return fo(t)

# panel primitives
# panel primitives -------------------------------------------------------------------
F_H = font("InterDisplay-Bold.otf", 46); F_B = font("InterDisplay-SemiBold.otf", 36); F_S = font("Inter-Regular.otf", 30)
F_M = font("Inter-Medium.otf", 30); F_MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
def card(w, h, r=26, fill=CARD, border=BORDER, shadow=True):
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + w, 40 + h), r, fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(im).rounded_rectangle((30, 30, 30 + w, 30 + h), r, fill=fill, outline=border, width=2)
    return im
def icon_tile(icon, color, s=110):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, s - 1, s - 1), s // 4, fill=color); d.text((s / 2, s / 2), icon, font=fa(s * 0.48), fill=WHITE, anchor="mm")
    return im
def chip(label, icon, color, w=None, check=False):
    tw = F_B.getlength(label); w = w or int(tw + 120); h = 78
    im = card(w, h, 20); d = ImageDraw.Draw(im)
    rr(d, (48, 44, 98, 94), 12, fill=color); d.text((73, 69), icon, font=fa(24), fill=WHITE, anchor="mm")
    d.text((114, 69), label, font=F_B, fill=TXT, anchor="lm")
    return im
def panel_bg():
    yy, xx = np.mgrid[0:TOP, 0:W]
    bg = np.zeros((TOP, W, 3), np.float32) + np.array(PAGE, np.float32)
    gl = np.exp(-(((xx - 160) / 600.0) ** 2 + ((yy - 120) / 420.0) ** 2))[..., None]
    bg = bg * (1 - 0.22 * gl) + np.array(ORANGE, np.float32) * 0.22 * gl
    return Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
PANEL = panel_bg()

def claude_window(w, h):
    im = card(w, h, 26, fill=PAGE); return im

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
def wrap(txt, fnt, width):
    lines = []
    for para in txt.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if fnt.getlength(t) > width and cur: lines.append(cur); cur = w
            else: cur = t
        lines.append(cur)
    return lines
def draw_input(d, sc, x0, x1, top, text, n, code_span, placeholder, show_caret, send_p):
    lines = wrap(text[:n], FT, (x1 - x0 - 2 * 34) * SS) if n else [""]
    th = max(1, len(lines)) * LH * SS
    bot = top + 30 * SS + th + 96 * SS
    d.rounded_rectangle((x0 * SS, top, x1 * SS, bot), 26 * SS, fill=CB_BG, outline=CB_BORDER, width=2 * SS)
    tx, ty = (x0 + 34) * SS, top + 28 * SS; cur = (tx, ty)
    if n == 0:
        d.text((tx, ty), placeholder, font=FT, fill=CB_MUTED)
    else:
        pos = 0
        for k, ln in enumerate(lines):
            y = ty + k * LH * SS
            d.text((tx, y), ln, font=FT, fill=CB_TEXT)
            # highlight the code (red outline like the reference) once fully typed
            ci, cj = code_span
            if n >= cj and pos <= ci < pos + len(ln) + 1:
                a = ci - pos; xa = tx + FT.getlength(ln[:a]); xb = tx + FT.getlength(ln[:a + (cj - ci)])
                d.rounded_rectangle((xa - 8 * SS, y - 4 * SS, xb + 8 * SS, y + 42 * SS), 8 * SS, outline=(235, 64, 52), width=3 * SS)
            pos += len(ln) + 1
            cur = (tx + FT.getlength(ln), y)
    if show_caret:
        d.rectangle((cur[0] + 4 * SS, cur[1] + 4 * SS, cur[0] + 7 * SS, cur[1] + 40 * SS), fill=CB_TEXT)
    by = bot - 50 * SS
    d.text(((x0 + 44) * SS, by), "", font=fa(26 * SS), fill=CB_TEXT, anchor="mm")
    c0 = (x0 + 78) * SS
    d.rounded_rectangle((c0, by - 27 * SS, c0 + 254 * SS, by + 27 * SS), 12 * SS, fill=CB_GROUP)
    d.rounded_rectangle((c0 + 4 * SS, by - 23 * SS, c0 + 104 * SS, by + 23 * SS), 10 * SS, fill=CB_CHIP)
    d.text((c0 + 54 * SS, by), "Chat", font=F_UI, fill=CB_TEXT, anchor="mm")
    d.text((c0 + 180 * SS, by), "Cowork", font=F_UI, fill=CB_MUTED, anchor="mm")
    rx = (x1 - 30) * SS
    if n > 0:
        s_ = 1 - 0.2 * math.sin(min(1, send_p) * math.pi) if send_p > 0 else 1; r = 25 * SS * s_
        d.rounded_rectangle((rx - 2 * r + 6 * SS, by - r, rx + 6 * SS, by + r), 12 * SS, fill=CLAUDE_ORANGE)
        d.text((rx - r + 6 * SS, by), "", font=fa(23 * SS), fill=WHITE, anchor="mm"); rx -= 2 * r + 24 * SS
    else:
        d.text((rx, by), "", font=fa(15 * SS), fill=CB_MUTED, anchor="mm"); rx -= 32 * SS
        for k_, hh in enumerate([10, 20, 30, 20, 12]):
            xx = rx - k_ * 8 * SS
            d.rounded_rectangle((xx - 2 * SS, by - hh / 2 * SS, xx + 2 * SS, by + hh / 2 * SS), 2 * SS, fill=CB_TEXT)
        rx -= 60 * SS
    d.text((rx, by), "", font=fa(26 * SS), fill=CB_TEXT, anchor="mm"); rx -= 44 * SS
    d.text((rx, by), "Medio", font=F_UI2, fill=CB_MUTED, anchor="rm"); rx -= F_UI2.getlength("Medio") + 14 * SS
    d.text((rx, by), "Sonnet 5.5", font=F_UI, fill=(206, 204, 196), anchor="rm")
    return (cur[0] / SS, cur[1] / SS + 20), bot / SS

# ---- scenes for the YouTube Agent Skill video (ChatGPT) --------------------------------
IC = lambda h: chr(h)
def fb(s): return ImageFont.truetype(f"{S}/fa/fa-brands.ttf", int(s))
YT = (255, 0, 51)
GPT = Image.open(f"{S}/p3/gpt_white.png").convert("RGBA")
def gpt(h): return GPT.resize((int(GPT.width * h / GPT.height), int(h)), Image.LANCZOS)
def yt_tile(s):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, s - 1, s - 1), int(s / 4.2), fill=YT)
    d.text((s / 2, s / 2 + 2), IC(0xf167), font=fb(s * 0.6), fill=WHITE, anchor="mm")
    return im
def gpt_tile(s):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, s - 1, s - 1), int(s / 4.2), fill=(0, 0, 0), outline=(90, 90, 90), width=3)
    g = gpt(s * 0.58); im.alpha_composite(g, (int(s / 2 - g.width / 2), int(s / 2 - g.height / 2)))
    return im
def avatar(d, xy, r, col, letter):
    x, y = xy; d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    d.text((x, y), letter, font=font("InterDisplay-Bold.otf", r * 1.05), fill=WHITE, anchor="mm")
def badge(text, icon, col, fnt=None):
    fnt = fnt or F_B; w = int(fa(fnt.size).getlength(icon) + fnt.getlength(text) + fnt.size * 0.45 + 64); h = int(fnt.size * 1.75)
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((15, 21, 15 + w, 21 + h), h // 2, fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im); rr(d, (15, 15, 15 + w, 15 + h), h // 2, fill=col)
    it(d, (15 + w / 2, 15 + h / 2), icon, text, fnt, WHITE, "mm"); return im
def pop_badge(c_, b, x, y, tt):
    if f_now[0] >= T(tt):
        k = f_now[0] - T(tt); paste(c_, b, x, y, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
F_T = font("InterDisplay-Bold.otf", 40); F_SM = font("Inter-Medium.otf", 24); F_XS = font("Inter-Regular.otf", 22)
GREEN_B = (46, 150, 84)
CY = 520
f_now = [0]
def put(im, c_, tt, sc_=0.96, y=CY):
    s, a, dy = pop(f_now[0] - T(tt)); paste(im, c_, 540, y + dy, s * sc_, a)
def typed(txt, tt, cps=30):
    f = f_now[0]; return "" if f < T(tt) else txt[:min(len(txt), int((f - T(tt) + 1) * cps / FPS))]
def gpt_pill(d, c_, x1, y, label="ChatGPT lo gestiona"):
    pw = F_SM.getlength(label) + 90
    rr(d, (x1 - pw, y - 24, x1, y + 24), 24, fill=(36, 58, 44), outline=(70, 160, 100), width=2)
    c_.alpha_composite(gpt(26), (int(x1 - pw + 18), int(y - 13)))
    d.text((x1 - pw + 54, y), label, font=F_SM, fill=(170, 230, 185), anchor="lm")

# thumbnails drawn in-house (no real creators): gradient + bold title + play badge
TH_STY = [((120, 20, 30), (20, 10, 10), "ESTO LO\nCAMBIA TODO"), ((20, 60, 130), (5, 10, 30), "PROBÉ ESTO\n30 DÍAS"),
          ((150, 90, 10), (30, 15, 5), "NADIE LO\nSABE"), ((40, 110, 70), (5, 25, 15), "EL ERROR\nN.º 1"),
          ((90, 30, 140), (15, 5, 30), "DE 0 A\n100K"), ((140, 40, 90), (25, 5, 15), "NO HAGAS\nESTO")]
def thumb(q, w, h, views=None):
    c1, c2, txt = TH_STY[q % len(TH_STY)]
    yy, xx = np.mgrid[0:h, 0:w]; u = np.clip((xx / w * 0.6 + yy / h * 0.4), 0, 1)[..., None]
    g = np.array(c1, np.float32) * (1 - u) + np.array(c2, np.float32) * u
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0)); mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), max(6, w // 18), fill=255)
    t.paste(Image.fromarray(g.astype(np.uint8)).convert("RGBA"), (0, 0), mk); d = ImageDraw.Draw(t)
    ft = ImageFont.truetype(POP, max(12, int(h * 0.2)))
    d.multiline_text((w * 0.07, h * 0.12), txt, font=ft, fill=WHITE, spacing=int(h * 0.02))
    if views:
        vf = font("Inter-SemiBold.otf", max(12, int(h * 0.12))); vw = vf.getlength(views) + 14
        rr(d, (w - vw - 8, h - vf.size - 16, w - 8, h - 8), 6, fill=(0, 0, 0, 200)); d.text((w - vw / 2 - 8, h - vf.size / 2 - 12), views, font=vf, fill=WHITE, anchor="mm")
    return t

# A · ChatGPT + YouTube ----------------------------------------------------------------
def scene_A(f, f0):
    im = PANEL.copy()
    if f < T(4.40):
        c_ = card(940, 400); d = ImageDraw.Draw(c_)
        c_.alpha_composite(yt_tile(170), (110, 90)); c_.alpha_composite(gpt_tile(170), (740, 90))
        d.text((195, 300), "YouTube", font=F_B, fill=TXT, anchor="mm"); d.text((825, 300), "ChatGPT", font=F_B, fill=TXT, anchor="mm")
        p = ease_io((f - T(2.96)) / 14) if f >= T(2.96) else 0
        x0, x1, y = 300, 730, 175
        for q in range(14):
            a_ = x0 + q * 31
            if a_ > x0 + (x1 - x0) * p: break
            rr(d, (a_, y - 4, min(a_ + 18, x1), y + 4), 4, fill=(200, 200, 200))
        if p >= 1:
            k = f - T(2.96) - 14; s = 0.6 + 0.4 * ease_out_back(k / 7); r_ = 38 * s
            d.ellipse((515 - r_, y - r_, 515 + r_, y + r_), fill=GREEN); d.text((515, y + 1), CHECK, font=fa(max(8, 36 * s)), fill=WHITE, anchor="mm")
            d.text((515, 300), "Conectado", font=F_M, fill=(140, 220, 160), anchor="mm")
        put(im, c_, 2.56); return im
    c_ = card(940, 440); d = ImageDraw.Draw(c_)
    c_.alpha_composite(yt_tile(76), (70, 62)); d.text((166, 100), "Tu canal de YouTube", font=F_T, fill=WHITE, anchor="lm")
    rows = [(IC(0xf03d), "Vídeos"), (IC(0xf03e), "Miniaturas"), (IC(0xf075), "Comentarios"), (IC(0xf073), "Calendario")]
    for q, (ic, lab) in enumerate(rows):
        y = 200 + q * 64; on = f >= T(4.70) + q * 6
        it(d, (80, y), ic, lab, F_B, TXT if on else MUTED)
        if on: gpt_pill(d, c_, 900, y)
    put(im, c_, 4.40); return im

# B · the skill -------------------------------------------------------------------------
def scene_B(f, f0):
    im = PANEL.copy()
    c_ = card(940, 330); d = ImageDraw.Draw(c_)
    c_.alpha_composite(yt_tile(160), (80, 80))
    d.text((276, 112), "YouTube Agent Skill", font=font("InterDisplay-Bold.otf", 60), fill=WHITE, anchor="lm")
    sub = "Skill para ChatGPT"; rr(d, (278, 168, 278 + F_M.getlength(sub) + 92, 218), 25, fill=(64, 64, 64))
    d.text((300, 193), sub, font=F_M, fill=TXT, anchor="lm"); c_.alpha_composite(gpt(30), (int(300 + F_M.getlength(sub) + 18), 178))
    pop_badge(c_, badge("100% gratis", IC(0xf06b), GREEN_B), 400, 296, 9.40)
    put(im, c_, 6.40); return im

# C · 11 skills --------------------------------------------------------------------------
SK = [(IC(0xf304), "Guionista"), (IC(0xf03e), "Miniaturas"), (IC(0xf0c4), "Editor"), (IC(0xf075), "Comentarios"),
      (IC(0xf073), "Planificador"), (IC(0xf201), "Viralidad"), (IC(0xf0e7), "Ganchos"), (IC(0xf002), "SEO"),
      (IC(0xf10b), "Shorts"), (IC(0xf1fe), "Retención"), (IC(0xf080), "Analítica")]
def scene_C(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450); d = ImageDraw.Draw(c_)
    c_.alpha_composite(yt_tile(56), (70, 58)); d.text((144, 86), "YouTube Agent Skill", font=F_T, fill=WHITE, anchor="lm")
    tw, th, gx, gy = 196, 98, 16, 16
    for q, (ic, lab) in enumerate(SK):
        tt = T(11.00) + q * 2
        if f < tt: continue
        row, col = divmod(q, 4); n = 4 if row < 2 else 3
        x = 30 + (940 - (n * tw + (n - 1) * gx)) / 2 + col * (tw + gx); y = 150 + row * (th + gy)
        k = f - tt; a = min(1, 0.3 + k / 3); s = 0.85 + 0.15 * ease_out_back(k / 6)
        tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); dt = ImageDraw.Draw(tile)
        rr(dt, (0, 0, tw - 1, th - 1), 18, fill=(56, 56, 56), outline=BORDER, width=2)
        dt.text((tw / 2, 36), ic, font=fa(30), fill=YT, anchor="mm"); dt.text((tw / 2, 74), lab, font=F_SM, fill=TXT, anchor="mm")
        tile = tile.resize((int(tw * s), int(th * s)), Image.BICUBIC)
        if a < 1: tile.putalpha(tile.getchannel("A").point(lambda v: int(v * a)))
        c_.alpha_composite(tile, (int(x + tw / 2 - tile.width / 2), int(y + th / 2 - tile.height / 2)))
    pop_badge(c_, badge("11 skills", IC(0xf5fd), RED, font("InterDisplay-Bold.otf", 34)), 800, 88, 13.12)
    put(im, c_, 10.40); return im

# D · what each one does --------------------------------------------------------------------
HOOK = "“Probé esto durante 30 días y…”"
def scene_D(f, f0):
    im = PANEL.copy()
    if f < T(18.86):   # script writer
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf304), "Guion de vídeo", F_T, WHITE, icol=YT)
        d.text((72, 160), "GANCHO", font=font("Inter-SemiBold.otf", 24), fill=(255, 110, 110), anchor="lm")
        rr(d, (72, 186, 78, 270), 3, fill=YT)
        tx = typed(HOOK, 15.60, 26); d.text((100, 228), tx, font=F_B, fill=TXT, anchor="lm")
        if len(tx) < len(HOOK) and (f // 8) % 2 == 0: xc = 100 + F_B.getlength(tx) + 4; d.rectangle((xc, 210, xc + 3, 246), fill=TXT)
        for q in range(3): rr(d, (72, 300 + q * 26, 72 + [520, 420, 470][q], 312 + q * 26), 6, fill=(70, 70, 70))
        pop_badge(c_, badge("21 fórmulas de ganchos", IC(0xf0e7), YT), 660, 400, 16.96)
        put(im, c_, 15.28); return im
    if f < T(21.10):   # thumbnails + titles
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf03e), "Miniatura y título", F_T, WHITE, icol=YT)
        if f >= T(19.50):
            k = f - T(19.50); s = 0.7 + 0.3 * ease_out_back(k / 7)
            paste(c_, thumb(0, 400, 225), 270, 290, s, min(1, 0.3 + k / 3))
        titles = ["Esto cambió mi canal para siempre", "Probé la IA 30 días en YouTube", "El error que frena tus vistas"]
        for q, t_ in enumerate(titles):
            tt = T(20.50) + q * 4
            if f < tt: continue
            y = 200 + q * 76; on = q == 0 and f >= T(20.50) + 14
            rr(d, (500, y - 30, 910, y + 30), 14, fill=(36, 58, 44) if on else (56, 56, 56), outline=(70, 160, 100) if on else BORDER, width=2)
            d.text((520, y), t_, font=font("Inter-Medium.otf", 21), fill=TXT, anchor="lm")
        put(im, c_, 18.86); return im
    if f < T(22.30):   # video editor
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf0c4), "Edita tus vídeos", F_T, WHITE, icol=YT)
        p = ease_io((f - T(21.20)) / 18)
        cols = [(70, 110, 170), (170, 90, 60), (90, 150, 90), (150, 80, 150), (70, 140, 150)]
        x = 72
        for q, c in enumerate(cols):
            wq = [190, 120, 210, 140, 150][q]
            if q in (1, 3): wq = int(wq * (1 - 0.75 * p))
            rr(d, (x, 190, x + wq - 6, 290), 10, fill=c); x += wq
        rr(d, (72, 310, 910, 360), 10, fill=(50, 50, 50))
        for q in range(60): d.line((80 + q * 14, 335 - (q * 37 % 17), 80 + q * 14, 335 + (q * 37 % 17)), fill=(130, 130, 130), width=4)
        ph = 72 + 830 * min(1, (f - T(21.10)) / 36); d.line((ph, 170, ph, 380), fill=YT, width=4)
        if p >= 1: d.text((910, 150), "Cortes automáticos", font=F_SM, fill=(140, 220, 160), anchor="rm")
        put(im, c_, 21.10); return im
    if f < T(23.82):   # comments
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf075), "Comentarios", F_T, WHITE, icol=YT)
        cm = [("@laura.crea", (214, 41, 118), "¿Qué programa usas para editar?", 22.40),
              ("@dani.tech", (79, 91, 213), "Brutal, ¿harás la parte 2?", 22.80),
              ("@sofi.vlogs", (250, 126, 30), "Me suscribo, justo lo que buscaba", 23.20)]
        for q, (u, col, txt, tt) in enumerate(cm):
            if f < T(tt): continue
            y = 175 + q * 92; k = f - T(tt); dx = (1 - ease_out_cubic(k / 6)) * 40
            avatar(d, (100 + dx, y + 20), 26, col, u[1].upper())
            d.text((146 + dx, y), u, font=F_SM, fill=MUTED, anchor="lm"); d.text((146 + dx, y + 36), txt, font=F_M, fill=TXT, anchor="lm")
            if k > 6: d.text((900, y + 20), "Respondido", font=F_SM, fill=(140, 220, 160), anchor="rm")
        put(im, c_, 22.30); return im
    c_ = card(940, 440); d = ImageDraw.Draw(c_)   # weekly planner
    it(d, (70, 92), IC(0xf073), "Tu semana en YouTube", F_T, WHITE, icol=YT)
    days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    plan = [("Vídeo", YT), ("Short", (79, 91, 213)), ("Short", (79, 91, 213)), ("Vídeo", YT), ("Short", (79, 91, 213)), ("Directo", (46, 150, 84)), ("Short", (79, 91, 213))]
    hrs = ["18:00", "13:00", "20:00", "17:30", "12:00", "11:00", "19:00"]
    cw = 112
    for q, dd in enumerate(days):
        x = 70 + q * (cw + 8); d.text((x + cw / 2, 160), dd, font=F_SM, fill=MUTED, anchor="mm")
        rr(d, (x, 186, x + cw, 400), 14, fill=(40, 40, 40), outline=BORDER, width=2)
        tt = T(24.14) + q * 4
        if f >= tt:
            k = f - tt; h_ = 70 * ease_out_back(k / 6); lab, col = plan[q]
            rr(d, (x + 8, 200, x + cw - 8, 200 + max(10, h_)), 10, fill=col)
            if k > 3: d.text((x + cw / 2, 235), lab, font=font("Inter-SemiBold.otf", 20), fill=WHITE, anchor="mm")
            if k > 5: d.text((x + cw / 2, 300), hrs[q], font=F_XS, fill=TXT, anchor="mm")
    put(im, c_, 23.82); return im

# E · what / when / how ------------------------------------------------------------------
def scene_E(f, f0):
    im = PANEL.copy()
    items = [(IC(0xf03d), "Qué", "publicar", 27.34), (IC(0xf073), "Cuándo", "publicar", 28.14), (IC(0xf06e), "Cómo", "conseguir vistas", 29.18)]
    for q, (ic, a1, a2, tt) in enumerate(items):
        x = 540 + (q - 1) * 310; on = f >= T(tt)
        c_ = card(280, 330, 24); d = ImageDraw.Draw(c_)
        if on: rr(d, (30, 30, 309, 359), 24, outline=YT, width=3)
        d.text((170, 130), ic, font=fa(60), fill=YT if on else (110, 110, 110), anchor="mm")
        d.text((170, 240), a1, font=font("InterDisplay-Bold.otf", 46), fill=WHITE if on else (130, 130, 130), anchor="mm")
        d.text((170, 292), a2, font=F_M, fill=TXT if on else (110, 110, 110), anchor="mm")
        if on: k = f - T(tt); s = 0.92 + 0.08 * ease_out_back(k / 6); a = 1
        else: s = 0.9; a = min(0.55, (f - f0) / 6)
        paste(im, c_, x, CY - (1 - ease_out_cubic((f - T(tt)) / 6)) * 16 * on, s, a)
    return im

# V · virality ------------------------------------------------------------------------------
VIEWS = ["2,1 M", "540 mil", "3,4 M", "180 mil", "1,6 M", "95 mil"]
TOP3 = {0, 2, 4}
def scene_V(f, f0):
    im = PANEL.copy()
    if f < T(33.66):
        c_ = card(900, 280); d = ImageDraw.Draw(c_)
        c_.alpha_composite(icon_tile(IC(0xf06d), (226, 60, 40), 150), (80, 95))
        d.text((262, 138), "Skill de viralidad", font=font("InterDisplay-Bold.otf", 64), fill=WHITE, anchor="lm")
        sub = "Virality Engine"; rr(d, (264, 196, 264 + F_M.getlength(sub) + 40, 244), 24, fill=(64, 64, 64))
        d.text((284, 220), sub, font=F_M, fill=TXT, anchor="lm")
        put(im, c_, 31.07, 1.0); return im
    if f < T(36.74):   # most viral videos in your niche
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 88), IC(0xf002), "Los vídeos más virales de tu nicho", font("InterDisplay-Bold.otf", 36), WHITE, icol=YT)
        tw_, th_ = 266, 150
        for q in range(6):
            tt = T(33.80) + q * 3
            if f < tt: continue
            col, row = q % 3, q // 3; x = 72 + col * (tw_ + 20); y = 140 + row * (th_ + 26); k = f - tt
            hl_ = q in TOP3 and f >= T(34.62)
            t_ = thumb(q, tw_, th_, VIEWS[q])
            if f >= T(34.62) and not hl_: t_.putalpha(t_.getchannel("A").point(lambda v: int(v * 0.35)))
            c_.alpha_composite(t_, (x, int(y + (1 - ease_out_cubic(k / 6)) * 24)))
            if hl_: rr(d, (x - 4, y - 4, x + tw_ + 4, y + th_ + 4), 14, outline=YT, width=4)
        put(im, c_, 33.66); return im
    if f < T(39.22):   # breaks down titles, hooks, structures
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        c_.alpha_composite(thumb(2, 300, 169, "3,4 M"), (70, 120)); rr(d, (66, 116, 374, 293), 14, outline=YT, width=4)
        d.text((410, 120), "Analiza", font=F_T, fill=WHITE, anchor="lm")
        rows = [("Título", "Curiosidad + número", 37.22), ("Gancho", "Promesa en 3 segundos", 37.62), ("Estructura", "Problema → prueba → resultado", 38.26)]
        for q, (lab, det, tt) in enumerate(rows):
            if f < T(tt): continue
            k = f - T(tt); y = 200 + q * 78; dx = (1 - ease_out_cubic(k / 6)) * 30
            d.ellipse((410 + dx, y - 18, 446 + dx, y + 18), fill=GREEN); d.text((428 + dx, y + 1), CHECK, font=fa(18), fill=WHITE, anchor="mm")
            d.text((462 + dx, y - 12), lab, font=F_B, fill=WHITE, anchor="lm"); d.text((462 + dx, y + 22), det, font=F_SM, fill=MUTED, anchor="lm")
        put(im, c_, 36.74); return im
    if f < T(41.78):   # recreated for you
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 88), IC(0xf15c), "Recreado para ti", F_T, WHITE, icol=YT)
        lines = [("TÍTULO", "“Probé la IA 30 días en mi canal”"), ("GANCHO", "“Esto me ahorró 20 horas a la semana…”"), ("ESTRUCTURA", "Problema → prueba → resultado")]
        for q, (lab, txt) in enumerate(lines):
            tt = T(39.40) + q * 9; y = 170 + q * 82
            if f < tt: continue
            k = f - tt; n = max(0, min(len(txt), int((k - 2) * 55 / FPS)))
            rr(d, (70, y - 22, 70 + 200, y + 22), 12, fill=(80, 36, 40)); d.text((170, y), lab, font=font("Inter-SemiBold.otf", 22), fill=(255, 170, 170), anchor="mm")
            d.text((294, y), txt[:n], font=F_M, fill=TXT, anchor="lm")
        pop_badge(c_, badge("Listo para grabar", CHECK, GREEN_B, F_M), 730, 430, 40.82)
        put(im, c_, 39.22); return im
    c_ = card(900, 440); d = ImageDraw.Draw(c_)   # never stuck
    it(d, (70, 88), IC(0xf3c1), "Nunca más atascado", F_T, WHITE, icol=YT)
    ideas = ["Vídeo: Probé la IA 30 días", "Short: El error n.º 1", "Vídeo: De 0 a 10K suscriptores"]
    d.text((72, 150), "¿Qué contenido crear hoy?", font=F_M, fill=MUTED, anchor="lm")
    for q, idea in enumerate(ideas):
        tt = T(43.30) + q * 6
        if f < tt: continue
        k = f - tt; y = 215 + q * 70; dx = (1 - ease_out_cubic(k / 6)) * 30
        rr(d, (70 + dx, y - 28, 900, y + 28), 14, fill=(52, 52, 52), outline=BORDER, width=2)
        d.text((100 + dx, y), IC(0xf0eb), font=fa(24), fill=(255, 200, 80), anchor="mm"); d.text((130 + dx, y), idea, font=F_B, fill=TXT, anchor="lm")
    put(im, c_, 41.78); return im

# W · with your voice, for your audience -------------------------------------------------------
def scene_W(f, f0):
    im = PANEL.copy()
    c_ = card(900, 440); d = ImageDraw.Draw(c_)
    it(d, (70, 88), IC(0xf06d), "Vídeos virales para tu canal", F_T, WHITE, icol=YT)
    rows = [(IC(0xf130), "Con tu voz", "Escrito como hablas tú", 46.62), (IC(0xf0c0), "Adaptado a tu audiencia", "Lo que tu público quiere ver", 49.30),
            (IC(0xf080), "Basado en tus vídeos", "Analiza lo que ya funcionó", 50.82)]
    for q, (ic, lab, det, tt) in enumerate(rows):
        y = 190 + q * 84; on = f >= T(tt)
        rr(d, (70, y - 34, 70 + 68, y + 34), 16, fill=YT if on else (60, 60, 60)); d.text((104, y), ic, font=fa(28), fill=WHITE, anchor="mm")
        d.text((160, y - 14), lab, font=F_B, fill=WHITE if on else (120, 120, 120), anchor="lm")
        d.text((160, y + 20), det, font=F_SM, fill=MUTED if on else (95, 95, 95), anchor="lm")
        if on:
            k = f - T(tt); s = 0.6 + 0.4 * ease_out_back(k / 6); r_ = 20 * s
            d.ellipse((860 - r_, y - r_, 860 + r_, y + r_), fill=GREEN); d.text((860, y + 1), CHECK, font=fa(max(8, 20 * s)), fill=WHITE, anchor="mm")
    put(im, c_, 45.26); return im

# Z · ChatGPT chat (dark mode, Spanish UI): paste link + type "Install Skill" ----------------------
LINK = "github.com/…/youtube-agent-skill"; CMD = " Install Skill"
G_BG = (33, 33, 33); G_IN = (48, 48, 48); G_TX = (236, 236, 236); G_MU = (175, 175, 175)
FG = font("Inter-Regular.otf", 32 * SS); FGH = font("Inter-Medium.otf", 44 * SS)
T_PASTE, T_TYPE, T_SEND = 54.10, 55.60, 57.10
def chat_text(f):
    if f < T(T_PASTE): return ""
    s = LINK
    if f >= T(T_TYPE): s += CMD[:min(len(CMD), int((f - T(T_TYPE) + 1) * 14 / FPS))]
    return s
def chat_scene(f):
    sc = Image.new("RGBA", (W * SS, TOP * SS), G_BG + (255,)); d = ImageDraw.Draw(sc)
    d.text((W * SS / 2, 330 * SS), "¿En qué puedo ayudar?", font=FGH, fill=G_TX, anchor="mm")
    x0, x1, y0, y1 = 110 * SS, (W - 120) * SS, 400 * SS, 540 * SS
    d.rounded_rectangle((x0, y0, x1, y1), 44 * SS, fill=G_IN)
    txt = chat_text(f); tx, ty = x0 + 36 * SS, y0 + 46 * SS
    if not txt: d.text((tx, ty), "Pregunta lo que quieras", font=FG, fill=G_MU, anchor="lm")
    else:
        d.text((tx, ty), txt[:len(LINK)], font=FG, fill=(130, 175, 255), anchor="lm")
        d.text((tx + FG.getlength(LINK), ty), txt[len(LINK):], font=FG, fill=G_TX, anchor="lm")
        if f < T(T_SEND) and (f // 8) % 2 == 0:
            xc = tx + FG.getlength(txt) + 4 * SS; d.rectangle((xc, ty - 20 * SS, xc + 3 * SS, ty + 20 * SS), fill=G_TX)
    by = y1 - 40 * SS
    d.text((x0 + 44 * SS, by), "+", font=font("Inter-Regular.otf", 44 * SS), fill=G_TX, anchor="mm")
    d.text((x0 + 104 * SS, by), IC(0xf1de), font=fa(24 * SS), fill=G_TX, anchor="mm")
    d.text((x0 + 132 * SS, by), "Herramientas", font=font("Inter-Regular.otf", 26 * SS), fill=G_TX, anchor="lm")
    cx = x1 - 52 * SS; r = 28 * SS
    if txt:
        s_ = 1 - 0.18 * math.sin(min(1, (f - T(T_SEND)) / 6) * math.pi) if f >= T(T_SEND) else 1
        d.ellipse((cx - r * s_, by - r * s_, cx + r * s_, by + r * s_), fill=(255, 255, 255))
        d.text((cx, by), IC(0xf062), font=fa(24 * SS * s_), fill=(0, 0, 0), anchor="mm")
    else:
        d.ellipse((cx - r, by - r, cx + r, by + r), fill=(255, 255, 255))
        for k_, hh in enumerate([10, 20, 14, 22]):
            xx = cx - 15 * SS + k_ * 10 * SS; d.rounded_rectangle((xx - 2 * SS, by - hh / 2 * SS, xx + 2 * SS, by + hh / 2 * SS), 2 * SS, fill=(0, 0, 0))
    if len(txt) <= len(LINK): d.text((cx - 64 * SS, by), IC(0xf130), font=fa(26 * SS), fill=G_TX, anchor="mm")
    d.text((W * SS / 2, 590 * SS), "ChatGPT puede cometer errores. Comprueba la información importante.", font=font("Inter-Regular.otf", 20 * SS), fill=(140, 140, 140), anchor="mm")
    return sc, txt
def zoom_state(f):
    p = ease_io((f - T(T_PASTE)) / 12) if f >= T(T_PASTE) else 0.0
    q = ease_io((f - T(T_TYPE)) / 16) if f >= T(T_TYPE) else 0.0
    return 540 + (520 - 540) * p, 410 + (440 - 410) * p, 1 + 0.15 * p
def scene_Z(f, f0):
    sc, _ = chat_scene(f)
    def sample(x, y, z):
        a = 1 / z; x0 = x - W / 2 * a; y0 = y - TOP / 2 * a
        return sc.transform((W, TOP), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=G_BG + (255,))
    x1, y1, z1 = zoom_state(f); x0_, y0_, z0 = zoom_state(f - 1)
    mv = math.hypot((x1 - x0_) * z1, (y1 - y0_) * z1) + abs(z1 - z0) * 900
    ns = 1 if mv < 4 else min(7, 2 + int(mv / 8))
    if ns == 1: v = sample(x1, y1, z1)
    else:
        acc = None
        for q in range(ns):
            u = q / (ns - 1); s_ = np.asarray(sample(x0_ + (x1 - x0_) * u, y0_ + (y1 - y0_) * u, z0 + (z1 - z0) * u), np.float32)
            acc = s_ if acc is None else acc + s_
        v = Image.fromarray((acc / ns).astype(np.uint8)).convert("RGBA")
    win = PANEL.copy()
    sh = Image.new("RGBA", (W, TOP), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((WX0, WY0 + 12, WX1, WY1 + 12), 30, fill=(0, 0, 0, 140))
    win.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    win.paste(v, (0, 0), WMASK); ImageDraw.Draw(win).rounded_rectangle((WX0, WY0, WX1, WY1), 30, outline=(70, 70, 70), width=2)
    a = min(1, (f - f0) / 5)
    if a < 1: win = Image.blend(PANEL, win, a)
    return win
WX0, WY0, WX1, WY1 = 56, 236, 1024, 786
WMASK = Image.new("L", (W, TOP), 0); ImageDraw.Draw(WMASK).rounded_rectangle((WX0, WY0, WX1, WY1), 30, fill=255)
SCENE_FN = {"A": scene_A, "B": scene_B, "C": scene_C, "D": scene_D, "E": scene_E, "V": scene_V, "W": scene_W, "Z": scene_Z}

def top_panel(f):
    f0, n = scene_at(f); f_now[0] = f
    v = SCENE_FN[n](f, f0)
    # code label (white box) on top of the panel
    k = f - f0; s, a, dy = pop(k)
    # whip-in when the connector changes
    if 0 <= k < 8 and f0 != SC[0][0]:
        q = ease_out_cubic(k / 8); arr = np.asarray(v.convert("RGB"), np.float32); nn = int((1 - q) * 30) + 1
        if nn > 1:
            acc = np.zeros_like(arr)
            for s_ in range(nn): acc += np.roll(arr, s_ - nn // 2, axis=1)
            arr = acc / nn
        dx = int((1 - q) * 240); arr = np.roll(arr, dx, axis=1)
        if dx: arr[:, :dx] = np.array(PAGE, np.float32)
        v = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    return v

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
def events():
    ev = [("whoosh", F_SPLIT0 / FPS), ("whoosh", F_SPLIT1 / FPS)] + [("whoosh", f0 / FPS) for f0, _ in SC[1:]]
    for t in (3.70, 4.70, 9.40, 13.12, 16.96, 19.50, 20.50, 21.10, 22.30, 23.82, 27.34, 28.14, 29.18, 33.66, 34.62, 36.74,
              39.22, 40.82, 41.78, 43.30, 46.62, 49.30, 50.82, 54.10):
        ev.append(("pluck", T(t) / FPS))
    ev.append(("boom", KEY["f0"] / FPS))
    return ev

TAGS = []
def main():
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        audio(events())
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        # e: 0 = full screen, 1 = split
        if f < F_SPLIT0: e = 0.0
        elif f < F_SPLIT1: e = ease_out_cubic((f - F_SPLIT0) / TRANS)
        else: e = 1 - ease_out_cubic((f - F_SPLIT1) / TRANS)
        if e <= 0:
            canvas = Image.fromarray(guy).convert("RGBA")
        else:
            edge = int(round(TOP * e)); shift = int(round(SHIFT * e))
            fr = np.empty((H, W, 3), np.uint8); fr[edge:] = guy[edge - shift:H - shift]
            canvas = Image.fromarray(fr).convert("RGBA")
            tp = top_panel(f if f < F_SPLIT1 else F_SPLIT1 - 1)
            canvas.alpha_composite(tp.crop((0, TOP - edge, W, TOP)), (0, 0))
        if f < F_SPLIT0 + 3:
            canvas.alpha_composite(TITLE, (int(540 - TITLE.width / 2), 290))
        if f >= KEY["f0"]:   # keyword: big, at the top, alone
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            paste(canvas, KEY["im"], 540, 400, sc, min(1, 0.35 + k / 3))
        cap_y = CAP_FULL + (CAP_SPLIT - CAP_FULL) * e
        tag = next(((a, im) for a, b, im, _n in TAGS if a <= f < b), None)
        if tag:
            k = f - tag[0]
            paste(canvas, tag[1], 540, cap_y + (1 - ease_out_cubic(k / 6)) * 10, 0.8 + 0.2 * ease_out_back(k / 6), min(1, 0.3 + k / 3))
        for ch in chunks:
            if tag or ch["key"] or not (ch["f0"] <= f < ch["f1"]) or KEY["f0"] <= f < KEY["f1"]: continue
            k = f - ch["f0"]
            paste(canvas, ch["im"], 540 if e > 0.5 else 500, cap_y + (1 - ease_out_cubic(k / 5)) * 8, 0.86 + 0.14 * ease_out_back(k / 5), min(1, 0.35 + k / 3))
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "split", round(F_SPLIT0 / FPS, 2), round(F_SPLIT1 / FPS, 2), "key", round(KEY["f0"] / FPS, 2), file=sys.stderr)
    main()
