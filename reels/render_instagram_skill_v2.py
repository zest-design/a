import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p11"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/0142cbff-47_base_2.mp4"
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
SIL = [(0.04, 0.16), (4.20, 4.43), (5.64, 5.88), (5.91, 6.27), (10.07, 10.36), (14.15, 14.55), (16.85, 16.99), (18.44, 18.86),
       (21.05, 21.33), (23.22, 23.54), (25.26, 25.58), (28.37, 28.58), (32.36, 32.55), (32.65, 32.82), (34.25, 34.59), (34.59, 34.73),
       (36.68, 36.84), (41.48, 41.73), (44.23, 44.43), (47.30, 47.46), (47.73, 48.00), (51.20, 51.34), (52.59, 52.86), (61.42, 61.69)]
END = 62.30; PAD = 0.04
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
    (0.16, 1.75, "Claude acaba de matar Instagram."),
    (1.84, 5.85, "Ahora puedes conectar Claude a Instagram y gestionará toda tu cuenta por ti."),
    (6.08, 10.05, "La skill se llama Instagram Agent Skill y es completamente gratuita."),
    (10.32, 14.12, "No es una sola skill, son 11 y cada una hace un trabajo distinto."),
    (14.24, 18.42, "Una escribe tus publicaciones basándose en las 21 fórmulas de ganchos más probadas."),
    (18.81, 21.40, "Otra comenta publicaciones de otras personas por ti."),
    (21.93, 23.22, "Otra se encarga de las respuestas,"),
    (23.70, 25.26, "otra optimiza tu perfil,"),
    (25.70, 28.37, "otra planifica tu semana entera de Instagram"),
    (28.58, 32.36, "y así te ayuda a saber qué publicar, cuándo publicar y con quién interactuar."),
    (32.73, 36.68, "Lo más loco de esta skill de viralidad, así llamémosla,"),
    (36.78, 44.23, "es que encuentra los reels con mejor rendimiento de tu nicho, te analiza por qué funcionan, convierte esas ideas en guiones originales para ti."),
    (44.38, 52.59, "De esa forma, tú nunca te quedas atascado pensando en qué publicar, cuándo publicar, qué vídeos son virales, qué voz poner y quién es tu audiencia."),
    (52.81, 56.30, "Para configurarlo, solo ve a Claude y pega este enlace."),
    (56.49, 62.30, "Y si tú quieres la configuración completa, el paso a paso detallado, comenta aquí abajo 99 y te lo hago llegar."),
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
HL = [["instagram", "agent", "skill"], ["gratuita"], ["11"], ["viralidad"], ["99"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i): return next((p for p in HL if [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "99"
    if not hl: txt = txt.lower().replace("claude", "Claude").replace("instagram", "Instagram")
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
SHIFT = 362                  # bottom panel shows his face centred
CAP_SPLIT, CAP_FULL = 800, 1420
F_SPLIT0, F_SPLIT1 = fo(1.84), fo(56.40)
TRANS = 9
TITLE = white_boxes(["TU INSTAGRAM EN", "PILOTO AUTOMÁTICO"], 56, chr(0x1F916))
SC = [(1.84, "A"), (6.08, "B"), (10.32, "C"), (14.24, "D"), (28.58, "E"), (32.73, "V"), (44.38, "N"), (52.81, "Z")]
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

# ---- scenes for the Instagram Agent Skill video -------------------------------------
IC = lambda h: chr(h)
def fb(s): return ImageFont.truetype(f"{S}/fa/fa-brands.ttf", int(s))
IG_STOPS = [(254, 218, 117), (250, 126, 30), (214, 41, 118), (150, 47, 191), (79, 91, 213)]
def ig_grad(w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    u = np.clip((xx / max(1, w - 1) + (1 - yy / max(1, h - 1))) / 2, 0, 1) * (len(IG_STOPS) - 1)
    i0 = np.minimum(u.astype(int), len(IG_STOPS) - 2); fr = (u - i0)[..., None]
    st = np.array(IG_STOPS, np.float32)
    return Image.fromarray((st[i0] * (1 - fr) + st[i0 + 1] * fr).astype(np.uint8)).convert("RGBA")
def ig_tile(s):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); mk = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, s - 1, s - 1), int(s / 4.2), fill=255)
    im.paste(ig_grad(s, s), (0, 0), mk)
    ImageDraw.Draw(im).text((s / 2, s / 2), IC(0xf16d), font=fb(s * 0.64), fill=WHITE, anchor="mm")
    return im
def claude_tile(s):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, s - 1, s - 1), int(s / 4.2), fill=(38, 37, 35), outline=ORANGE, width=4)
    sp = spark(s * 0.56); im.alpha_composite(sp, (int(s / 2 - sp.width / 2), int(s / 2 - sp.height / 2)))
    return im
def ig_ring(s):   # avatar with Instagram gradient ring
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); mk = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mk).ellipse((0, 0, s - 1, s - 1), fill=255); im.paste(ig_grad(s, s), (0, 0), mk)
    d = ImageDraw.Draw(im); d.ellipse((6, 6, s - 7, s - 7), fill=PAGE); d.ellipse((11, 11, s - 12, s - 12), fill=(90, 88, 84))
    d.text((s / 2, s / 2 + 2), IC(0xf007), font=fa(s * 0.42), fill=(200, 198, 190), anchor="mm")
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
F_T = font("InterDisplay-Bold.otf", 40); F_SM = font("Inter-Medium.otf", 24); F_XS = font("Inter-Regular.otf", 22)
CY = 520           # vertical centre of panel content (keeps clear of the IG top bar and the seam caption)
def put(im, c_, tt, sc_=1.0, y=CY):
    s, a, dy = pop(f_now[0] - T(tt)); paste(im, c_, 540, y + dy, s * sc_, a)
f_now = [0]
def type_n(txt, f, tt, cps=28): return 0 if f < T(tt) else min(len(txt), int((f - T(tt) + 1) * cps / FPS))

# A · Claude + Instagram -------------------------------------------------------------
def scene_A(f, f0):
    im = PANEL.copy()
    if f < T(3.68):
        c_ = card(940, 400); d = ImageDraw.Draw(c_)
        c_.alpha_composite(ig_tile(170), (110, 90)); c_.alpha_composite(claude_tile(170), (740, 90))
        d.text((195, 300), "Instagram", font=F_B, fill=TXT, anchor="mm"); d.text((825, 300), "Claude", font=F_B, fill=TXT, anchor="mm")
        p = ease_io((f - T(2.32)) / 16) if f >= T(2.32) else 0
        x0, x1, y = 300, 730, 175
        for q in range(14):
            a_ = x0 + q * 31; b_ = a_ + 18
            if a_ > x0 + (x1 - x0) * p: break
            rr(d, (a_, y - 4, min(b_, x1), y + 4), 4, fill=ORANGE)
        if p >= 1:
            k = f - T(2.32) - 16; s = 0.6 + 0.4 * ease_out_back(k / 7)
            r_ = 38 * s; d.ellipse((515 - r_, y - r_, 515 + r_, y + r_), fill=GREEN)
            d.text((515, y + 1), CHECK, font=fa(max(8, 36 * s)), fill=WHITE, anchor="mm")
            d.text((515, 300), "Conectado", font=F_M, fill=(140, 220, 160), anchor="mm")
        put(im, c_, 1.84, 0.96); return im
    c_ = card(940, 440); d = ImageDraw.Draw(c_)
    c_.alpha_composite(ig_tile(76), (70, 62))
    d.text((166, 100), "Tu cuenta de Instagram", font=F_T, fill=WHITE, anchor="lm")
    rows = [(IC(0xf304), "Publicaciones"), (IC(0xf075), "Comentarios"), (IC(0xf3e5), "Respuestas"), (IC(0xf007), "Perfil")]
    for q, (ic, lab) in enumerate(rows):
        y = 200 + q * 64; on = f >= T(3.90) + q * 7
        it(d, (80, y), ic, lab, F_B, TXT if on else MUTED)
        if on:
            k = f - (T(3.90) + q * 7); s = 0.6 + 0.4 * ease_out_back(k / 6)
            pill = "Claude lo gestiona"; pw = F_SM.getlength(pill) + 90
            rr(d, (900 - pw, y - 24, 900, y + 24), 24, fill=(36, 58, 44), outline=(70, 160, 100), width=2)
            sp = spark(26); c_.alpha_composite(sp, (int(900 - pw + 18), int(y - 13)))
            d.text((900 - pw + 54, y), pill, font=F_SM, fill=(170, 230, 185), anchor="lm")
    put(im, c_, 3.68, 0.96); return im

# B · the skill -----------------------------------------------------------------------
def scene_B(f, f0):
    im = PANEL.copy()
    c_ = card(940, 330); d = ImageDraw.Draw(c_)
    c_.alpha_composite(ig_tile(160), (80, 80))
    d.text((276, 112), "Instagram Agent Skill", font=font("InterDisplay-Bold.otf", 58), fill=WHITE, anchor="lm")
    sub = "Skill para Claude"; rr(d, (278, 168, 278 + F_M.getlength(sub) + 92, 218), 25, fill=(60, 58, 55))
    d.text((300, 193), sub, font=F_M, fill=TXT, anchor="lm"); c_.alpha_composite(spark(30), (int(300 + F_M.getlength(sub) + 18), 178))
    if f >= T(9.30):
        b = badge("100% gratis", IC(0xf06b), (46, 150, 84)); k = f - T(9.30); s = 0.6 + 0.4 * ease_out_back(k / 7)
        paste(c_, b, 400, 296, s, min(1, 0.3 + k / 3))
    put(im, c_, 6.08, 0.96); return im

# C · 11 skills ------------------------------------------------------------------------
SK = [(IC(0xf304), "Escritor"), (IC(0xf075), "Comentarios"), (IC(0xf3e5), "Respuestas"), (IC(0xf007), "Perfil"),
      (IC(0xf073), "Planificador"), (IC(0xf06d), "Viralidad"), (IC(0xf0e7), "Ganchos"), (IC(0xf03d), "Guiones"),
      (IC(0xf00a), "Cuadrícula"), (IC(0xf06e), "Monitor"), (IC(0xf004), "Interacción")]
def scene_C(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450); d = ImageDraw.Draw(c_)
    c_.alpha_composite(ig_tile(56), (70, 58)); d.text((144, 86), "Instagram Agent Skill", font=F_T, fill=WHITE, anchor="lm")
    tw, th, gx, gy = 196, 98, 16, 16
    for q, (ic, lab) in enumerate(SK):
        tt = T(10.90) + q * 2
        if f < tt: continue
        row, col = divmod(q, 4); n = 4 if row < 2 else 3
        x = 30 + (940 - (n * tw + (n - 1) * gx)) / 2 + col * (tw + gx); y = 150 + row * (th + gy)
        k = f - tt; a = min(1, 0.3 + k / 3); s = 0.85 + 0.15 * ease_out_back(k / 6)
        tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); dt = ImageDraw.Draw(tile)
        rr(dt, (0, 0, tw - 1, th - 1), 18, fill=(52, 51, 49), outline=BORDER, width=2)
        dt.text((tw / 2, 36), ic, font=fa(30), fill=ORANGE, anchor="mm"); dt.text((tw / 2, 74), lab, font=F_SM, fill=TXT, anchor="mm")
        tile = tile.resize((int(tw * s), int(th * s)), Image.BICUBIC)
        if a < 1: tile.putalpha(tile.getchannel("A").point(lambda v: int(v * a)))
        c_.alpha_composite(tile, (int(x + tw / 2 - tile.width / 2), int(y + th / 2 - tile.height / 2)))
    if f >= T(12.16):
        k = f - T(12.16); s = 0.6 + 0.4 * ease_out_back(k / 7)
        b = badge("11 skills", IC(0xf5fd), RED, font("InterDisplay-Bold.otf", 34)); paste(c_, b, 800, 88, s, min(1, 0.3 + k / 3))
    put(im, c_, 10.32, 0.96); return im

# D · what each one does ----------------------------------------------------------------
HOOK = "Nadie te cuenta esto sobre crecer en Instagram…"
def scene_D(f, f0):
    im = PANEL.copy()
    if f < T(18.81):   # post writer + 21 hook formulas
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf304), "Nueva publicación", F_T, WHITE, icol=ORANGE)
        rr(d, (70, 150, 910, 300), 20, fill=(38, 37, 35), outline=BORDER, width=2)
        n = type_n(HOOK, f, 14.80, 30); d.text((100, 190), HOOK[:n], font=F_B, fill=TXT, anchor="lm")
        if f < T(14.80) + len(HOOK) * FPS / 30 + 6 and (f // 8) % 2 == 0:
            xc = 100 + F_B.getlength(HOOK[:n]) + 4; d.rectangle((xc, 172, xc + 3, 208), fill=TXT)
        for q in range(2): rr(d, (100, 238 + q * 30, 100 + [560, 400][q], 252 + q * 30), 7, fill=(64, 63, 60))
        rr(d, (690, 352, 910, 412), 16, fill=(0, 149, 246)); d.text((800, 382), "Compartir", font=F_B, fill=WHITE, anchor="mm")
        if f >= T(16.40):
            k = f - T(16.40); s = 0.6 + 0.4 * ease_out_back(k / 7)
            paste(c_, badge("21 fórmulas de ganchos", IC(0xf0e7), ORANGE), 340, 382, s, min(1, 0.3 + k / 3))
        put(im, c_, 14.24, 0.96); return im
    if f < T(21.93):   # comments on other people's posts
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf075), "Comenta por ti", F_T, WHITE, icol=ORANGE)
        cm = [("@lucia.fit", (214, 41, 118), "¡Qué buen consejo! Lo pruebo hoy mismo.", 19.13),
              ("@marcos.dev", (79, 91, 213), "Brutal la explicación, guardado para luego.", 19.95),
              ("@ana.viajes", (250, 126, 30), "Justo lo que necesitaba leer esta semana.", 20.80)]
        for q, (u, col, txt, tt) in enumerate(cm):
            if f < T(tt): continue
            y = 175 + q * 92; k = f - T(tt); dx = (1 - ease_out_cubic(k / 6)) * 40
            avatar(d, (100 + dx, y + 20), 26, col, u[1].upper())
            d.text((146 + dx, y), u, font=F_SM, fill=MUTED, anchor="lm"); d.text((146 + dx, y + 36), txt, font=F_M, fill=TXT, anchor="lm")
            c_.alpha_composite(spark(26), (int(866 + dx), int(y + 6)))
        put(im, c_, 18.81, 0.96); return im
    if f < T(23.93):   # replies
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 92), IC(0xf3e5), "Responde por ti", F_T, WHITE, icol=ORANGE)
        q1 = "¿Cuánto cuesta tu curso?"; avatar(d, (100, 190), 26, (150, 47, 191), "C")
        rr(d, (140, 160, 140 + F_M.getlength(q1) + 48, 220), 26, fill=(60, 58, 55)); d.text((164, 190), q1, font=F_M, fill=TXT, anchor="lm")
        if f >= T(22.30):
            r1 = "¡Hola! Te envío toda la info por DM ahora mismo."; n = type_n(r1, f, 22.30, 40)
            w_ = F_M.getlength(r1) + 48; rr(d, (910 - w_, 250, 910, 310), 26, fill=(0, 149, 246))
            d.text((910 - w_ + 24, 280), r1[:n], font=F_M, fill=WHITE, anchor="lm")
        if f >= T(23.10):
            k = f - T(23.10); s = 0.6 + 0.4 * ease_out_back(k / 7)
            paste(c_, badge("Respondido por Claude", CHECK, (46, 150, 84), F_M), 730, 380, s, min(1, 0.3 + k / 3))
        put(im, c_, 21.93, 0.96); return im
    if f < T(26.01):   # profile optimizer
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        c_.alpha_composite(ig_ring(150), (70, 70))
        d.text((250, 105), "tu_marca", font=F_T, fill=WHITE, anchor="lm")
        for q, (nm, lb) in enumerate((("128", "publicaciones"), ("24,5 mil", "seguidores"), ("310", "seguidos"))):
            x = 250 + q * 215; d.text((x, 165), nm, font=F_B, fill=WHITE, anchor="lm"); d.text((x, 202), lb, font=F_XS, fill=MUTED, anchor="lm")
        p = ease_io((f - T(24.10)) / 10) if f >= T(24.10) else 0
        old = "Hola, bienvenidos a mi perfil"; new = "Te ayudo a crecer en Instagram con IA"
        d.text((76, 282), old, font=F_M, fill=tuple(int(c * (1 - p) + 70 * p) for c in TXT), anchor="lm")
        if p > 0: d.line((76, 284, 76 + F_M.getlength(old) * p, 284), fill=(220, 80, 80), width=3)
        if p >= 1:
            k = f - T(24.10) - 10; n = type_n(new, f, 24.45, 45)
            d.text((76, 330), new[:n], font=F_B, fill=WHITE, anchor="lm")
        if f >= T(25.10):
            k = f - T(25.10); s = 0.6 + 0.4 * ease_out_back(k / 7)
            paste(c_, badge("Perfil optimizado", CHECK, (46, 150, 84), F_M), 770, 400, s, min(1, 0.3 + k / 3))
        put(im, c_, 23.93, 0.96); return im
    # weekly planner
    c_ = card(940, 440); d = ImageDraw.Draw(c_)
    it(d, (70, 92), IC(0xf073), "Tu semana en Instagram", F_T, WHITE, icol=ORANGE)
    days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    plan = [("Reel", ORANGE), ("Carrusel", (79, 91, 213)), ("Story", (214, 41, 118)), ("Reel", ORANGE), ("Carrusel", (79, 91, 213)), ("Story", (214, 41, 118)), ("Reel", ORANGE)]
    cw = 112
    for q, dd in enumerate(days):
        x = 70 + q * (cw + 8); d.text((x + cw / 2, 160), dd, font=F_SM, fill=MUTED, anchor="mm")
        rr(d, (x, 186, x + cw, 400), 14, fill=(38, 37, 35), outline=BORDER, width=2)
        tt = T(26.30) + q * 4
        if f >= tt:
            k = f - tt; h_ = 70 * ease_out_back(k / 6); lab, col = plan[q]
            rr(d, (x + 8, 200, x + cw - 8, 200 + max(10, h_)), 10, fill=col)
            if k > 3: d.text((x + cw / 2, 235), lab, font=font("Inter-SemiBold.otf", 20), fill=WHITE, anchor="mm")
            if k > 5: d.text((x + cw / 2, 300), ["18:00", "13:00", "20:00", "18:30", "12:00", "11:00", "19:00"][q], font=F_XS, fill=TXT, anchor="mm")
    put(im, c_, 26.01, 0.96); return im

# E · what / when / who ----------------------------------------------------------------
def scene_E(f, f0):
    im = PANEL.copy()
    items = [(IC(0xf304), "Qué", "publicar", 29.75), (IC(0xf073), "Cuándo", "publicar", 30.49), (IC(0xf007), "Con quién", "interactuar", 31.21)]
    for q, (ic, a1, a2, tt) in enumerate(items):
        x = 540 + (q - 1) * 310; on = f >= T(tt)
        c_ = card(280, 330, 24); d = ImageDraw.Draw(c_)
        if on: rr(d, (30, 30, 309, 359), 24, outline=ORANGE, width=3)
        d.text((170, 130), ic, font=fa(60), fill=ORANGE if on else (110, 108, 102), anchor="mm")
        d.text((170, 240), a1, font=font("InterDisplay-Bold.otf", 46), fill=WHITE if on else (130, 128, 122), anchor="mm")
        d.text((170, 292), a2, font=F_M, fill=TXT if on else (110, 108, 102), anchor="mm")
        if on: k = f - T(tt); s = 0.92 + 0.08 * ease_out_back(k / 6); a = 1
        else: k = f - f0; s = 0.9; a = min(0.55, k / 6)
        paste(im, c_, x, CY - (1 - ease_out_cubic((f - T(tt)) / 6)) * 16 * on, s, a)
    return im

# V · virality skill ----------------------------------------------------------------------
VIEWS = ["1,2 M", "845 mil", "2,4 M", "310 mil", "1,8 M", "96 mil"]
TOP3 = {0, 2, 4}
def thumb(q, w, h):
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0)); mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), 16, fill=255)
    hues = [(70, 40, 90), (30, 60, 90), (90, 45, 40), (40, 70, 60), (85, 60, 30), (50, 50, 70)]
    g = np.zeros((h, w, 3), np.float32) + np.array(hues[q], np.float32)
    g *= (0.7 + 0.6 * np.linspace(1, 0, h))[:, None, None]
    t.paste(Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 0), mk)
    d = ImageDraw.Draw(t); d.text((w / 2, h / 2 - 20), IC(0xf04b), font=fa(44), fill=(255, 255, 255, 220), anchor="mm")
    it(d, (14, h - 26), IC(0xf04b), VIEWS[q], F_SM, WHITE)
    return t
def scene_V(f, f0):
    im = PANEL.copy()
    if f < T(37.10):
        c_ = card(900, 280); d = ImageDraw.Draw(c_)
        c_.alpha_composite(icon_tile(IC(0xf06d), (226, 76, 52), 150), (80, 95))
        d.text((262, 138), "Skill de viralidad", font=font("InterDisplay-Bold.otf", 64), fill=WHITE, anchor="lm")
        sub = "Virality Engine"; rr(d, (264, 196, 264 + F_M.getlength(sub) + 40, 244), 24, fill=(60, 58, 55))
        d.text((284, 220), sub, font=F_M, fill=TXT, anchor="lm")
        put(im, c_, 32.73, 1.0); return im
    if f < T(40.22):   # best-performing reels in your niche
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        it(d, (70, 88), IC(0xf002), "Reels con mejor rendimiento de tu nicho", font("InterDisplay-Bold.otf", 36), WHITE, icol=ORANGE)
        tw_, th_ = 130, 230
        for q in range(6):
            tt = T(37.30) + q * 3
            if f < tt: continue
            x = 70 + q * (tw_ + 14); y = 140; k = f - tt
            hl_ = q in TOP3 and f >= T(38.62)
            th = thumb(q, tw_, th_)
            if f >= T(38.62) and not hl_:
                th.putalpha(th.getchannel("A").point(lambda v: int(v * 0.4)))
            c_.alpha_composite(th, (x, int(y + (1 - ease_out_cubic(k / 6)) * 30)))
            if hl_:
                rr(d, (x - 4, y - 4, x + tw_ + 4, y + th_ + 4), 18, outline=ORANGE, width=4)
                rr(d, (x + tw_ / 2 - 40, y + th_ + 14, x + tw_ / 2 + 40, y + th_ + 50), 18, fill=ORANGE)
                d.text((x + tw_ / 2, y + th_ + 32), "Top", font=font("Inter-SemiBold.otf", 22), fill=WHITE, anchor="mm")
        put(im, c_, 37.10, 0.96); return im
    if f < T(41.66):   # why they work
        c_ = card(940, 440); d = ImageDraw.Draw(c_)
        c_.alpha_composite(thumb(2, 170, 300), (70, 110))
        rr(d, (66, 106, 244, 414), 18, outline=ORANGE, width=4)
        d.text((290, 120), "¿Por qué funciona?", font=F_T, fill=WHITE, anchor="lm")
        rows = ["Gancho en el primer segundo", "Ritmo rápido, sin pausas", "Final que invita a comentar"]
        for q, r_ in enumerate(rows):
            tt = T(40.40) + q * 6
            if f < tt: continue
            k = f - tt; y = 205 + q * 74; dx = (1 - ease_out_cubic(k / 6)) * 30
            d.ellipse((290 + dx, y - 20, 330 + dx, y + 20), fill=GREEN); d.text((310 + dx, y + 1), CHECK, font=fa(20), fill=WHITE, anchor="mm")
            d.text((348 + dx, y), r_, font=F_B, fill=TXT, anchor="lm")
        put(im, c_, 40.22, 0.96); return im
    c_ = card(940, 440); d = ImageDraw.Draw(c_)   # original scripts
    it(d, (70, 88), IC(0xf15c), "Guion original para ti", F_T, WHITE, icol=ORANGE)
    lines = [("GANCHO", "“Esto cambió mi forma de usar Instagram…”"), ("DESARROLLO", "3 pasos claros, uno por plano"),
             ("CIERRE", "“Comenta GUIA y te lo envío”")]
    for q, (lab, txt) in enumerate(lines):
        tt = T(42.20) + q * 10; y = 170 + q * 82
        if f < tt: continue
        k = f - tt; n = max(0, min(len(txt), int((k - 2) * 50 / FPS)))
        rr(d, (70, y - 22, 70 + 190, y + 22), 12, fill=(70, 50, 44)); d.text((165, y), lab, font=font("Inter-SemiBold.otf", 22), fill=(245, 180, 150), anchor="mm")
        d.text((284, y), txt[:n], font=F_M, fill=TXT, anchor="lm")
    if f >= T(43.40):
        k = f - T(43.40); s = 0.6 + 0.4 * ease_out_back(k / 7)
        paste(c_, badge("100% original", CHECK, (46, 150, 84), F_M), 740, 430, s, min(1, 0.3 + k / 3))
    put(im, c_, 41.66, 0.96); return im

# N · never stuck again ---------------------------------------------------------------------
QS = [("¿Qué publicar?", 47.50), ("¿Cuándo publicar?", 48.62), ("¿Qué vídeos son virales?", 49.42), ("¿Qué voz poner?", 50.46), ("¿Quién es tu audiencia?", 51.42)]
def scene_N(f, f0):
    im = PANEL.copy()
    c_ = card(900, 460); d = ImageDraw.Draw(c_)
    it(d, (70, 88), IC(0xf3c1), "Nunca más atascado", F_T, WHITE, icol=ORANGE)
    for q, (qq, tt) in enumerate(QS):
        y = 160 + q * 64; on = f >= T(tt)
        if on:
            k = f - T(tt); s = 0.6 + 0.4 * ease_out_back(k / 6); r_ = 20 * s
            d.ellipse((90 - r_, y - r_, 90 + r_, y + r_), fill=GREEN); d.text((90, y + 1), CHECK, font=fa(max(8, 20 * s)), fill=WHITE, anchor="mm")
        else:
            d.ellipse((70, y - 20, 110, y + 20), outline=(110, 108, 102), width=3)
        d.text((134, y), qq, font=F_B, fill=TXT if on else (125, 123, 117), anchor="lm")
        if on: d.text((890, y), "Resuelto", font=F_SM, fill=(140, 220, 160), anchor="rm")
    put(im, c_, 44.38, 0.96); return im

# Z · Claude chat (dark mode, Spanish UI): paste the link ------------------------------------
LINK = "github.com/…/instagram-agent-skill"
def chat_scene(f):
    sc = Image.new("RGBA", (W * SS, TOP * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    sp = spark(50 * SS); g = "Buenas tardes"; gf = serif(56 * SS)
    gw = sp.width + 20 * SS + gf.getlength(g); gx = (W * SS - gw) / 2; gy = 340 * SS
    sc.alpha_composite(sp, (int(gx), int(gy - sp.height / 2)))
    d.text((gx + sp.width + 20 * SS, gy), g, font=gf, fill=(232, 230, 222), anchor="lm")
    n = len(LINK) if f >= T(55.13) else 0
    send_p = (f - T(55.93)) / 6 if f >= T(55.93) else 0
    cur, bot = draw_input(d, sc, 70, W - 70, 400 * SS, LINK, n, (-1, -1), "¿En qué puedo ayudarte hoy?", n > 0 and f < T(55.93), send_p)
    if n:   # pasted link, underlined like a link
        x0 = (70 + 34) * SS; y0 = 400 * SS + 28 * SS + 42 * SS
        d.line((x0, y0, x0 + FT.getlength(LINK), y0), fill=(110, 160, 230), width=2 * SS)
    return sc, cur, bot
def zoom_state(f):
    p = ease_io((f - T(55.13)) / 12) if f >= T(55.13) else 0.0
    return 540 + (400 - 540) * p, 410 + (430 - 410) * p, 1 + 0.3 * p
def scene_Z(f, f0):
    sc, cur, bot = chat_scene(f)
    def sample(x, y, z):
        a = 1 / z; x0 = x - W / 2 * a; y0 = y - TOP / 2 * a
        return sc.transform((W, TOP), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=PAGE + (255,))
    x1, y1, z1 = zoom_state(f); x0_, y0_, z0 = zoom_state(f - 1)
    mv = abs(z1 - z0) * 900
    ns = 1 if mv < 4 else min(7, 2 + int(mv / 8))
    if ns == 1: v = sample(x1, y1, z1)
    else:
        acc = None
        for q in range(ns):
            u = q / (ns - 1); s_ = np.asarray(sample(x0_ + (x1 - x0_) * u, y0_ + (y1 - y0_) * u, z0 + (z1 - z0) * u), np.float32)
            acc = s_ if acc is None else acc + s_
        v = Image.fromarray((acc / ns).astype(np.uint8)).convert("RGBA")
    win = PANEL.copy()   # chat lives in a rounded window inside the IG safe area
    sh = Image.new("RGBA", (W, TOP), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((WX0, WY0 + 12, WX1, WY1 + 12), 30, fill=(0, 0, 0, 140))
    win.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    win.paste(v, (0, 0), WMASK); ImageDraw.Draw(win).rounded_rectangle((WX0, WY0, WX1, WY1), 30, outline=BORDER, width=2)
    k = f - f0; a = min(1, k / 5)
    if a < 1: win = Image.blend(PANEL, win, a)
    return win
WX0, WY0, WX1, WY1 = 56, 236, 1024, 786
WMASK = Image.new("L", (W, TOP), 0); ImageDraw.Draw(WMASK).rounded_rectangle((WX0, WY0, WX1, WY1), 30, fill=255)
SCENE_FN = {"A": scene_A, "B": scene_B, "C": scene_C, "D": scene_D, "E": scene_E, "V": scene_V, "N": scene_N, "Z": scene_Z}

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
    for t in (2.95, 3.90, 9.30, 12.16, 16.40, 18.81, 21.93, 23.10, 23.93, 25.10, 26.01, 29.75, 30.49, 31.21, 37.10, 38.62, 40.22,
              41.66, 43.40, 47.50, 48.62, 49.42, 50.46, 51.42, 55.13):
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
