import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p14"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/050df8c3-Le-dije-la-verdad-esta-20261026-175217_1.mp4"
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
SIL = [(0.00, 1.20), (1.27, 1.53), (3.48, 3.67), (9.47, 9.59), (10.57, 10.85), (11.34, 11.57), (17.97, 18.23), (18.27, 18.50),
       (20.49, 20.73), (28.41, 28.64), (28.68, 29.02), (31.70, 31.89), (32.48, 32.71), (38.18, 38.34), (38.34, 38.52), (39.86, 40.74),
       (42.86, 43.34), (46.71, 47.05), (49.05, 49.29), (49.32, 49.56), (53.82, 54.09), (55.68, 55.90), (58.05, 58.18)]
END = 59.20; PAD = 0.04
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
    (1.20, 3.48, "Claude acaba de matar a los day traders."),
    (3.67, 7.95, "Ahora puedes hacer operaciones ganadoras automáticamente dentro de Claude."),
    (8.08, 11.34, "Se llama Trader Skill y es completamente gratuita."),
    (11.44, 14.70, "No es solo una skill, son 11 y cada una hace un trabajo distinto."),
    (14.80, 17.97, "Una analiza miles de gráficos buscando setups para ti."),
    (18.50, 20.49, "Otra sigue las noticias de última hora,"),
    (20.73, 28.41, "otra encuentra el momento perfecto para entrar, y así tú vas a ver siempre cuándo entrar, salir y cómo ganar la máxima cantidad de dinero posible."),
    (28.64, 32.40, "Lo más loco es que esta skill es la máquina del tiempo."),
    (32.71, 38.18, "Antes de arriesgar un solo dólar, reproduce todos los resultados posibles de esa operación."),
    (38.52, 43.80, "Luego da las estadísticas, lo más preciso posible en el resultado."),
    (43.95, 49.05, "Es el mismo tipo de software que empresas como Bloomberg cobran miles de euros por usar."),
    (49.29, 53.82, "Para configurarla, pega este enlace dentro de Claude y escribe Install_Skill."),
    (54.09, 59.18, "Si quieres la configuración completa, sígueme y comenta aquí abajo TRADE y te la hago llegar."),
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
HL = [["trader", "skill"], ["gratuita"], ["11"], ["máquina", "del", "tiempo"], ["TRADE"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("TRADE"): return ["TRADE"]
    return next((p for p in HL if p != ["TRADE"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "TRADE"
    if not hl: txt = txt.lower().replace("claude", "Claude").replace("install_skill", "Install Skill").replace("bloomberg", "Bloomberg")
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
SHIFT = 300                  # bottom panel shows his face centred
CAP_SPLIT, CAP_FULL = 800, 1460
F_SPLIT0, F_SPLIT1 = fo(3.67), fo(53.95)
TRANS = 9
TITLE = white_boxes(["CLAUDE AHORA HACE", "TRADING POR TI"], 56, chr(0x1F4C8))
SC = [(3.67, "A"), (8.08, "B"), (11.44, "C"), (14.80, "D"), (18.50, "E"), (20.73, "F"), (24.51, "G"), (28.64, "H"), (32.71, "I"), (38.52, "J"), (43.95, "K"), (49.29, "Z")]
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

# ---- scenes for the Trader Skill video (Claude) -------------------------------------------------
IC = lambda h: chr(h)
def badge(text, icon, col, fnt=None):
    fnt = fnt or F_B; w = int(fa(fnt.size).getlength(icon) + fnt.getlength(text) + fnt.size * 0.45 + 64); h = int(fnt.size * 1.75)
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((15, 21, 15 + w, 21 + h), h // 2, fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im); rr(d, (15, 15, 15 + w, 15 + h), h // 2, fill=col)
    it(d, (15 + w / 2, 15 + h / 2), icon, text, fnt, WHITE, "mm"); return im
F_T = font("InterDisplay-Bold.otf", 40); F_SM = font("Inter-Medium.otf", 24); F_XS = font("Inter-Regular.otf", 22)
F_NUM = font("InterDisplay-Bold.otf", 30)
UP = (38, 186, 120); DN = (232, 72, 72); GREEN_B = (46, 150, 84); TEAL = (40, 170, 190)
CY = 520
f_now = [0]
def put(im, c_, tt, sc_=0.96, y=CY):
    s, a, dy = pop(f_now[0] - T(tt)); paste(im, c_, 540, y + dy, s * sc_, a)
def pop_badge(c_, b, x, y, tt):
    if f_now[0] >= T(tt):
        k = f_now[0] - T(tt); paste(c_, b, x, y, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
def eur(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " $"

# ---------- tiny 3D engine (painter's algorithm, 2x supersampled) ----------
S3 = 2
def rot3(p, yaw, pitch):
    x, y, z = p; cy_, sy_ = math.cos(yaw), math.sin(yaw); x, z = x * cy_ + z * sy_, -x * sy_ + z * cy_
    cp, sp = math.cos(pitch), math.sin(pitch); y, z = y * cp - z * sp, y * sp + z * cp
    return x, y, z
class Cam:
    def __init__(s, yaw, pitch, dist, cx=540, cy=500, fl=760): s.yaw, s.pitch, s.dist, s.cx, s.cy, s.fl = yaw, pitch, dist, cx, cy, fl
    def cam(s, p): x, y, z = rot3(p, s.yaw, s.pitch); return x, y, z + s.dist
    def proj(s, p):
        x, y, z = s.cam(p); k = s.fl / max(0.1, z); return (s.cx + x * k) * S3, (s.cy - y * k) * S3, z, k
LDIR = np.array([-0.35, 0.8, -0.5]); LDIR = LDIR / np.linalg.norm(LDIR)
def box_faces(cam, c, size, col, spin=0.0):
    sx, sy, sz = size; cx, cy, cz = c; V = []
    for dx in (-1, 1):
        for dy in (-1, 1):
            for dz in (-1, 1):
                x, z = dx * sx / 2, dz * sz / 2
                x, z = x * math.cos(spin) + z * math.sin(spin), -x * math.sin(spin) + z * math.cos(spin)
                V.append((cx + x, cy + dy * sy / 2, cz + z))
    F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    Cv = [np.array(cam.cam(v)) for v in V]; Pv = [cam.proj(v) for v in V]; bc = sum(Cv) / 8; out = []
    for fi in F:
        ctr = sum(Cv[i] for i in fi) / 4; n = ctr - bc; nn = np.linalg.norm(n)
        if nn < 1e-6: continue
        n = n / nn
        if np.dot(n, ctr) >= -1e-6: continue
        lam = 0.42 + 0.58 * max(0.0, float(np.dot(n, LDIR)))
        out.append((float(ctr[2]), [Pv[i][:2] for i in fi], tuple(int(min(255, ch * lam)) for ch in col)))
    return out
def layer3d(): return Image.new("RGBA", (W * S3, TOP * S3), (0, 0, 0, 0))
def flat3d(lay): return lay.resize((W, TOP), Image.LANCZOS)

# ---------- candles ----------
def make_candles(n, seed, start=360.0, drift=0.0, vol=1.2):
    r = np.random.default_rng(seed); out = []; p = start
    for i in range(n):
        o = p; c = o + r.normal(drift, vol); h = max(o, c) + abs(r.normal(0, vol * 0.6)); l = min(o, c) - abs(r.normal(0, vol * 0.6))
        out.append((o, h, l, c)); p = c
    return out
CND1 = make_candles(34, 3, 360, 0.12, 1.0)
def draw_candles(d, box, cnd, n, lo, hi):
    x0, y0, x1, y1 = box; cw = (x1 - x0) / len(cnd)
    Y = lambda v: y1 - (v - lo) / (hi - lo) * (y1 - y0)
    for i, (o, h, l, c) in enumerate(cnd[:n]):
        x = x0 + i * cw + cw / 2; col = UP if c >= o else DN
        d.line((x, Y(h), x, Y(l)), fill=col, width=2)
        d.rectangle((x - cw * 0.32, Y(max(o, c)), x + cw * 0.32, max(Y(min(o, c)), Y(max(o, c)) + 2)), fill=col)
    return Y

# A · winning trades automatically (layout) ------------------------------------------------------
def scene_A(f, f0):
    im = PANEL.copy()
    c_ = card(940, 440, fill=PAGE); d = ImageDraw.Draw(c_)
    c_.alpha_composite(spark(36), (62, 60))
    msg = ["TSLA ha cerrado por encima de 362,18 $ a las 10:15.", "He colocado una orden automáticamente:"]
    shown = int(max(0, f - T(4.00)) * 3.6); acc = 0
    for j, ln in enumerate(msg):
        d.text((114, 62 + j * 44), ln[:max(0, shown - acc)], font=F_S, fill=TXT); acc += len(ln)
    if f >= T(5.20):
        k = f - T(5.20); s = 0.7 + 0.3 * ease_out_back(k / 7)
        t_ = card(560, 200, 20, fill=(38, 37, 35)); dt = ImageDraw.Draw(t_)
        it(dt, (66, 78), IC(0xf080), "Orden ejecutada", F_SM, MUTED)
        dt.text((66, 140), "COMPRA", font=font("InterDisplay-Black.otf", 52), fill=UP, anchor="lm")
        dt.text((66 + font("InterDisplay-Black.otf", 52).getlength("COMPRA") + 22, 140), "TSLA", font=font("InterDisplay-Black.otf", 52), fill=WHITE, anchor="lm")
        dt.text((66, 196), "10:15 · 364,18 $ · 10 acciones", font=F_SM, fill=TXT, anchor="lm")
        paste(c_, t_, 380, 330, s, min(1, 0.3 + k / 3))
    if f >= T(6.00):
        k = f - T(6.00); st = Image.new("RGBA", (300, 90), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        rr(ds, (6, 6, 294, 84), 14, outline=(110, 160, 235), width=5); ds.text((150, 46), "AUTOMÁTICA", font=font("InterDisplay-Black.otf", 34), fill=(110, 160, 235), anchor="mm")
        st = st.rotate(8, expand=True, resample=Image.BICUBIC)
        paste(c_, st, 770, 330, 1.6 - 0.6 * ease_out_cubic(k / 6), min(1, k / 4))
    put(im, c_, 3.67); return im

# B · the skill (layout) -----------------------------------------------------------------------------
def scene_B(f, f0):
    im = PANEL.copy()
    c_ = card(900, 330); d = ImageDraw.Draw(c_)
    c_.alpha_composite(icon_tile(IC(0xf201), UP, 160), (80, 80))
    d.text((276, 112), "Trader Skill", font=font("InterDisplay-Bold.otf", 72), fill=WHITE, anchor="lm")
    sub = "Skill para Claude"; rr(d, (278, 172, 278 + F_M.getlength(sub) + 92, 222), 25, fill=(60, 58, 55))
    d.text((300, 197), sub, font=F_M, fill=TXT, anchor="lm"); c_.alpha_composite(spark(30), (int(300 + F_M.getlength(sub) + 18), 182))
    pop_badge(c_, badge("100% gratis", IC(0xf06b), GREEN_B), 400, 300, 10.30)
    put(im, c_, 8.08); return im

# C · 11 skills — 3D ring around Claude -------------------------------------------------------------
SK = [(IC(0xf201), "Gráficos"), (IC(0xf1ea), "Noticias"), (IC(0xf090), "Entrada"), (IC(0xf08b), "Salida"), (IC(0xf1da), "Máquina del tiempo"),
      (IC(0xf3ed), "Riesgo"), (IC(0xf555), "Cartera"), (IC(0xf0f3), "Alertas"), (IC(0xf118), "Sentimiento"), (IC(0xf1ec), "Backtest"), (IC(0xf02d), "Diario")]
SKCOL = [(217, 119, 87), (200, 104, 74), (226, 140, 100), (190, 96, 70), (230, 128, 90)]
def scene_C(f, f0):
    im = PANEL.copy(); k = f - f0
    grow = ease_out_cubic(k / 14)
    cam = Cam(0.0, -0.38 + 0.04 * math.sin(k / 50), 10.4, 540, 470, 820)
    lay = layer3d(); dl = ImageDraw.Draw(lay)
    # floor ring
    pts = [cam.proj((3.6 * math.cos(a), -0.7, 3.6 * math.sin(a)))[:2] for a in np.linspace(0, 2 * math.pi, 90)]
    dl.line(pts + [pts[0]], fill=(120, 80, 60), width=3 * S3)
    rot_ = k * 0.018 + 0.3
    items = []
    for q, (ic, lab) in enumerate(SK):
        tq = T(11.70) + q * 2
        if f < tq: continue
        a = rot_ + q * 2 * math.pi / 11; r_ = 3.6 * grow
        c = (r_ * math.cos(a), 0.0, r_ * math.sin(a))
        s_ = 1.0 * ease_out_back(min(1, (f - tq) / 6))
        if s_ <= 0.01: continue
        for fc in box_faces(cam, c, (s_, s_, s_), SKCOL[q % len(SKCOL)], spin=-a): items.append(fc + (None,))
        items.append((cam.cam(c)[2] - 0.6, None, None, (q, c, s_)))
    items.sort(key=lambda t: -t[0])
    labels = []
    for z, poly, col, meta in items:
        if poly is not None: dl.polygon(poly, fill=col, outline=tuple(max(0, v - 40) for v in col))
        else:
            q, c, s_ = meta; X, Y, Z, kk = cam.proj(c)
            fs = max(10, int(0.5 * kk * S3 * s_)); dl.text((X, Y), SK[q][0], font=fa(fs), fill=WHITE, anchor="mm")
            labels.append((Z, X / S3, Y / S3 + 0.85 * kk * s_, q))
    # Claude core
    core = spark(150 * (0.7 + 0.3 * grow)); im.alpha_composite(core, (int(540 - core.width / 2), int(cam.proj((0, 0.3, 0))[1] / S3 - core.height / 2)))
    im.alpha_composite(flat3d(lay))
    d = ImageDraw.Draw(im)
    for Z, X, Y, q in sorted(labels, key=lambda t: t[0])[:4]:
        lab = SK[q][1]; w_ = F_SM.getlength(lab) + 28
        rr(d, (X - w_ / 2, Y - 18, X + w_ / 2, Y + 18), 14, fill=(30, 29, 28)); d.text((X, Y), lab, font=F_SM, fill=TXT, anchor="mm")
    if f >= T(12.72):
        kk = f - T(12.72); paste(im, badge("11 skills", IC(0xf5fd), RED, font("InterDisplay-Bold.otf", 36)), 540, 270, 0.6 + 0.4 * ease_out_back(kk / 7), min(1, 0.3 + kk / 3))
    return im

# D · chart scanner (layout) -------------------------------------------------------------------------
ROWS = [("AAPL", 228.14, 0.8), ("NVDA", 138.62, 2.4), ("TSLA", 364.18, 3.1), ("AMZN", 186.40, -0.6), ("MSFT", 418.25, 0.3), ("META", 572.90, 1.7)]
SETUPS = {1: 16.70, 2: 17.10, 5: 17.50}
def spark_line(d, box, seed, up):
    r = np.random.default_rng(seed); v = np.cumsum(r.normal(0.15 if up else -0.15, 1, 24)); x0, y0, x1, y1 = box
    v = (v - v.min()) / (np.ptp(v) + 1e-6)
    d.line([(x0 + i * (x1 - x0) / 23, y1 - vv * (y1 - y0)) for i, vv in enumerate(v)], fill=UP if up else DN, width=3)
def scene_D(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450, fill=(20, 20, 22), border=(60, 60, 64)); d = ImageDraw.Draw(c_)
    it(d, (66, 80), IC(0xf201), "Escáner de gráficos", F_T, WHITE, icol=ORANGE)
    n = min(5259, int(5259 * ease_out_cubic((f - T(15.04)) / 60))) if f >= T(15.04) else 0
    d.text((910, 80), f"{n:,} de 5.259 acciones".replace(",", "."), font=F_SM, fill=MUTED, anchor="rm")
    for q, (tk, px, ch) in enumerate(ROWS):
        y = 150 + q * 50; hl = q in SETUPS and f >= T(SETUPS[q])
        if hl: rr(d, (56, y - 22, 914, y + 22), 10, fill=(44, 34, 28), outline=ORANGE, width=2)
        d.text((76, y), tk, font=font("Inter-SemiBold.otf", 26), fill=WHITE, anchor="lm")
        d.text((330, y), eur(px), font=F_SM, fill=TXT, anchor="rm")
        d.text((450, y), f"{'+' if ch >= 0 else ''}{ch:.1f}%".replace(".", ","), font=F_SM, fill=UP if ch >= 0 else DN, anchor="rm")
        spark_line(d, (490, y - 16, 690, y + 16), q + 7, ch >= 0)
        if hl: rr(d, (760, y - 17, 900, y + 17), 17, fill=ORANGE); d.text((830, y), "Setup", font=font("Inter-SemiBold.otf", 22), fill=WHITE, anchor="mm")
    put(im, c_, 14.80); return im

# E · breaking news (layout) ---------------------------------------------------------------------------
def scene_E(f, f0):
    im = PANEL.copy()
    ph = Image.new("RGBA", (520, 470), (0, 0, 0, 0)); dp = ImageDraw.Draw(ph)
    g = ImageDraw.Draw(ph); rr(g, (0, 0, 519, 469), 40, fill=(26, 36, 70))
    dp.text((260, 60), "martes, 27 de octubre", font=F_SM, fill=(220, 225, 240), anchor="mm")
    dp.text((260, 140), "8:04", font=font("InterDisplay-Bold.otf", 110), fill=WHITE, anchor="mm")
    if f >= T(18.83):
        k = f - T(18.83); nt = Image.new("RGBA", (470, 170), (0, 0, 0, 0)); dn = ImageDraw.Draw(nt)
        rr(dn, (0, 0, 469, 169), 26, fill=(235, 235, 240, 235))
        rr(dn, (20, 20, 66, 66), 12, fill=(38, 37, 35)); sp = spark(30); nt.alpha_composite(sp, (int(43 - sp.width / 2), 28))
        dn.text((80, 43), "Trader Skill · ahora", font=font("Inter-SemiBold.otf", 22), fill=(40, 40, 45), anchor="lm")
        for j, ln in enumerate(("Última hora: el dato de empleo sale", "por encima de lo previsto.", "Revisa tus posiciones.")):
            dn.text((24, 86 + j * 28), ln, font=font("Inter-Medium.otf", 21), fill=(30, 30, 35), anchor="lm")
        paste(ph, nt, 260, 330 + (1 - ease_out_cubic(k / 7)) * 40, 0.9 + 0.1 * ease_out_back(k / 7), min(1, k / 4))
    s, a, dy = pop(f - T(18.50)); paste(im, ph, 540, CY + dy, s, a)
    return im

# F · perfect time to enter (layout) ------------------------------------------------------------------
def chart_card(f, title, n_c, extra):
    c_ = card(940, 450, fill=(20, 20, 22), border=(60, 60, 64)); d = ImageDraw.Draw(c_)
    it(d, (66, 78), IC(0xf201), title, F_T, WHITE, icol=ORANGE)
    d.text((910, 80), "TSLA · 5 min", font=F_SM, fill=MUTED, anchor="rm")
    for q in range(5): d.line((70, 150 + q * 64, 900, 150 + q * 64), fill=(40, 40, 44), width=1)
    Y = draw_candles(d, (70, 140, 800, 440), CND1, n_c, 352, 374)
    extra(d, Y); return c_
def scene_F(f, f0):
    im = PANEL.copy()
    n_c = min(len(CND1), 12 + int(max(0, f - T(20.73)) / 3))
    def ex(d, Y):
        d.rectangle((70, Y(363), 400, Y(357)), outline=(110, 110, 120), width=2); d.text((80, Y(363) - 16), "Rango de apertura", font=F_XS, fill=MUTED, anchor="lm")
        if f >= T(22.27):
            k = f - T(22.27); y = Y(364.18); x = 70 + 22 * (730 / len(CND1))
            d.line((70, y, 900, y), fill=UP, width=3)
            rr(d, (790, y - 22, 908, y + 22), 10, fill=UP); d.text((849, y), "364,18", font=font("Inter-SemiBold.otf", 22), fill=WHITE, anchor="mm")
            d.polygon([(x, y + 14), (x - 14, y + 40), (x + 14, y + 40)], fill=UP)
    c_ = chart_card(f, "Momento de entrada", n_c, ex)
    pop_badge(c_, badge("Entra ahora", IC(0xf017), UP, F_M), 300, 430, 22.40)
    put(im, c_, 20.73); return im

# G · when to get in, get out, max profit (layout) ------------------------------------------------------
def scene_G(f, f0):
    im = PANEL.copy()
    def ex(d, Y):
        for lab, v, col, tt in (("Entrada 364,18", 364.18, UP, 24.83), ("Stop 358,32", 358.32, DN, 25.23), ("Objetivo 370,04", 370.04, TEAL, 26.67)):
            if f < T(tt): continue
            k = f - T(tt); y = Y(v); xe = 70 + 830 * ease_out_cubic(k / 8)
            d.line((70, y, xe, y), fill=col, width=3)
            w_ = F_XS.getlength(lab) + 24; rr(d, (900 - w_, y - 20, 900, y + 20), 10, fill=col); d.text((900 - w_ / 2, y), lab, font=font("Inter-SemiBold.otf", 21), fill=WHITE, anchor="mm")
    c_ = chart_card(f, "Plan de la operación", 26, ex)
    pop_badge(c_, badge("Máximo beneficio", IC(0xf201), TEAL, F_M), 310, 430, 27.07)
    put(im, c_, 24.51); return im

# H · the time machine — 3D clock rewinding ------------------------------------------------------------
def scene_H(f, f0):
    im = PANEL.copy(); k = f - f0
    cam = Cam(0.35 * math.sin(k / 40), -0.5, 9, 540, 560, 780)
    lay = layer3d(); dl = ImageDraw.Draw(lay)
    items = []
    for q in range(12):
        a = q * math.pi / 6; c = (2.6 * math.cos(a), 2.6 * math.sin(a), 0)
        s_ = 0.42 if q % 3 else 0.62
        for fc in box_faces(cam, c, (s_, s_, s_ * 0.8), ORANGE if q % 3 == 0 else (150, 110, 90)): items.append(fc)
    # dial disc
    disc = [cam.proj((2.95 * math.cos(a), 2.95 * math.sin(a), 0.35))[:2] for a in np.linspace(0, 2 * math.pi, 72)]
    dl.polygon(disc, fill=(36, 35, 33), outline=(90, 88, 84))
    items.sort(key=lambda t: -t[0])
    for z, poly, col in items: dl.polygon(poly, fill=col, outline=tuple(max(0, v - 40) for v in col))
    ang = -k * 0.22   # hands spin backwards: rewinding time
    for L, wdt, sp_ in ((1.6, 7, 1.0), (2.2, 4, 12.0)):
        a = math.pi / 2 + ang * sp_ / 6
        p0 = cam.proj((0, 0, -0.1)); p1 = cam.proj((L * math.cos(a), L * math.sin(a), -0.1))
        dl.line((p0[0], p0[1], p1[0], p1[1]), fill=WHITE, width=wdt * S3)
    p0 = cam.proj((0, 0, -0.1)); dl.ellipse((p0[0] - 12 * S3, p0[1] - 12 * S3, p0[0] + 12 * S3, p0[1] + 12 * S3), fill=ORANGE)
    im.alpha_composite(flat3d(lay))
    t_ = Image.new("RGBA", (900, 90), (0, 0, 0, 0)); dt = ImageDraw.Draw(t_)
    it(dt, (450, 45), IC(0xf1da), "Máquina del tiempo", font("InterDisplay-Bold.otf", 56), WHITE, "mm", icol=ORANGE)
    s, a, dy = pop(k); paste(im, t_, 540, 290 + dy, s, a)
    return im

# I · replays every possible outcome — 3D fan of simulated paths ----------------------------------------
NP = 30; RNG = np.random.default_rng(11)
PATHS = np.cumsum(RNG.normal(0.03, 0.32, (NP, 50)), axis=1); PATHS = np.concatenate([np.zeros((NP, 1)), PATHS], axis=1)
def scene_I(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(34.91):   # not a single dollar at risk: spinning coin
        t_ = Image.new("RGBA", (900, 90), (0, 0, 0, 0)); dt = ImageDraw.Draw(t_)
        dt.text((450, 45), "Antes de arriesgar 1 $", font=font("InterDisplay-Bold.otf", 50), fill=WHITE, anchor="mm")
        s, a, dy = pop(k); paste(im, t_, 540, 300 + dy, s, a)
        w_ = abs(math.cos(k * 0.16)) * 150 + 10; d = ImageDraw.Draw(im)
        d.ellipse((540 - w_, 380, 540 + w_, 680), fill=(214, 168, 70), outline=(160, 120, 40), width=6)
        if w_ > 60:
            cf = font("InterDisplay-Black.otf", 120); tx = Image.new("RGBA", (260, 160), (0, 0, 0, 0))
            ImageDraw.Draw(tx).text((130, 80), "1 $", font=cf, fill=(150, 108, 30), anchor="mm")
            tx = tx.resize((max(1, int(260 * (w_ - 10) / 150)), 160)); im.alpha_composite(tx, (int(540 - tx.width / 2), 450))
        return im
    kk = f - T(34.91)
    cam = Cam(-0.55 + 0.25 * math.sin(kk / 45), -0.32, 11.5, 560, 560, 900)
    lay = layer3d(); dl = ImageDraw.Draw(lay)
    # floor grid
    for gx in np.linspace(-4, 4, 9): dl.line([cam.proj((gx, -2.2, z))[:2] for z in (-3, 3)], fill=(70, 60, 54), width=S3)
    for gz in np.linspace(-3, 3, 7): dl.line([cam.proj((x, -2.2, gz))[:2] for x in (-4, 4)], fill=(70, 60, 54), width=S3)
    # entry plane edge
    dl.line([cam.proj((-4, 0, z))[:2] for z in (-3, 3)], fill=(200, 200, 200), width=2 * S3)
    prog = min(1.0, kk / 40); shown = max(2, int(51 * prog)); nshow = min(NP, int(4 + kk * 1.8))
    order = sorted(range(nshow), key=lambda i: -cam.cam((0, 0, -3 + 6 * i / (NP - 1)))[2])
    for i in order:
        z = -3 + 6 * i / (NP - 1); ys = PATHS[i, :shown] * 0.55
        col = UP if PATHS[i, -1] > 0 else DN
        pts = [cam.proj((-4 + 8 * j / 50, float(np.clip(y, -2.1, 2.6)), z))[:2] for j, y in enumerate(ys)]
        dl.line(pts, fill=col + (190,), width=3 * S3, joint="curve")
    dl.ellipse([cam.proj((-4, 0, 0))[0] - 10 * S3, cam.proj((-4, 0, 0))[1] - 10 * S3, cam.proj((-4, 0, 0))[0] + 10 * S3, cam.proj((-4, 0, 0))[1] + 10 * S3], fill=WHITE)
    im.alpha_composite(flat3d(lay))
    d = ImageDraw.Draw(im); n = min(10000, int(10000 * ease_io(min(1, kk / 70))))
    it(d, (90, 290), IC(0xf1da), f"{n:,}".replace(",", ".") + " simulaciones", font("InterDisplay-Bold.otf", 46), WHITE, icol=ORANGE)
    d.text((92, 344), "TSLA · todos los resultados posibles", font=F_SM, fill=MUTED, anchor="lm")
    return im

# J · statistics — 3D histogram -----------------------------------------------------------------------
HIST = [0.10, 0.22, 0.38, 0.55, 0.72, 0.90, 1.00, 0.82, 0.60, 0.40, 0.22]
def scene_J(f, f0):
    im = PANEL.copy(); k = f - f0
    cam = Cam(-0.5 + 0.15 * math.sin(k / 50), -0.38, 12.5, 540, 660, 800)
    lay = layer3d(); dl = ImageDraw.Draw(lay); items = []
    for gx in np.linspace(-5, 5, 11): dl.line([cam.proj((gx, 0, z))[:2] for z in (-1.2, 1.2)], fill=(70, 60, 54), width=S3)
    for q, h in enumerate(HIST):
        g = ease_out_cubic((f - T(38.60) - q * 1.5) / 14)
        if g <= 0: continue
        hh = 3.6 * h * g; x = -5 + q
        col = DN if q < 3 else ((150, 150, 150) if q < 5 else UP)
        for fc in box_faces(cam, (x, hh / 2, 0), (0.78, hh, 0.9), col): items.append(fc)
    items.sort(key=lambda t: -t[0])
    for z, poly, col in items: dl.polygon(poly, fill=col, outline=tuple(max(0, v - 50) for v in col))
    for lab, x in (("Stop", -4.0), ("Entrada", -1.0), ("Objetivo", 3.0)):
        X, Y, _, _ = cam.proj((x, -0.35, 1.2)); dl.text((X, Y + 12 * S3), lab, font=font("Inter-SemiBold.otf", 22 * S3), fill=TXT, anchor="mm")
    im.alpha_composite(flat3d(lay))
    d = ImageDraw.Draw(im)
    it(d, (90, 290), IC(0xf080), "Estadísticas de cada resultado", font("InterDisplay-Bold.otf", 42), WHITE, icol=ORANGE)
    if f >= T(39.15):
        kk = f - T(39.15); paste(im, badge("Objetivo: 64%", IC(0xf058), UP, F_M), 360, 375, 0.6 + 0.4 * ease_out_back(kk / 7), min(1, 0.3 + kk / 3))
    if f >= T(41.39):
        kk = f - T(41.39); paste(im, badge("Stop: 21%", IC(0xf057), DN, F_M), 720, 375, 0.6 + 0.4 * ease_out_back(kk / 7), min(1, 0.3 + kk / 3))
    return im

# K · same software Bloomberg charges thousands for (layout) -----------------------------------------------
def scene_K(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450); d = ImageDraw.Draw(c_)
    d.text((500, 82), "El mismo tipo de software", font=F_T, fill=WHITE, anchor="mm")
    rr(d, (70, 130, 480, 450), 22, fill=(20, 20, 22), outline=(80, 80, 86), width=2)
    d.text((275, 175), "Terminal profesional", font=F_B, fill=WHITE, anchor="mm")
    if f >= T(45.95): d.text((275, 218), "tipo Bloomberg", font=F_SM, fill=MUTED, anchor="mm")
    for q in range(4): spark_line(d, (110, 250 + q * 34, 440, 276 + q * 34), q + 30, q % 2 == 0)
    if f >= T(46.99):
        k = f - T(46.99); paste(c_, badge("Miles de € al año", IC(0xf153), DN, F_M), 275, 418, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
    rr(d, (520, 130, 930, 450), 22, fill=(30, 60, 42), outline=(46, 160, 90), width=2)
    c_.alpha_composite(icon_tile(IC(0xf201), UP, 96), (677, 170))
    d.text((725, 310), "Trader Skill", font=F_B, fill=WHITE, anchor="mm"); c_.alpha_composite(spark(28), (840, 296))
    d.text((725, 380), "Gratis", font=font("InterDisplay-Black.otf", 56), fill=(140, 230, 170), anchor="mm")
    put(im, c_, 43.95); return im

# Z · Claude chat (dark, Spanish): paste link, type "Install Skill" ---------------------------------------
LINK = "github.com/…/trader-skill"; FULL = LINK + " Install Skill"
T_PASTE, T_TYPE, T_SEND = 50.43, 52.83, 53.60
def chat_n(f):
    if f < T(T_PASTE): return 0
    if f < T(T_TYPE): return len(LINK)
    return min(len(FULL), len(LINK) + int((f - T(T_TYPE) + 1) * 18 / FPS))
def chat_scene(f):
    sc = Image.new("RGBA", (W * SS, TOP * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    sp = spark(50 * SS); g = "Buenas tardes"; gf = serif(56 * SS)
    gw = sp.width + 20 * SS + gf.getlength(g); gx = (W * SS - gw) / 2; gy = 340 * SS
    sc.alpha_composite(sp, (int(gx), int(gy - sp.height / 2)))
    d.text((gx + sp.width + 20 * SS, gy), g, font=gf, fill=(232, 230, 222), anchor="lm")
    n = chat_n(f); send_p = (f - T(T_SEND)) / 6 if f >= T(T_SEND) else 0
    draw_input(d, sc, 110, W - 130, 400 * SS, FULL, n, (-1, -1), "¿En qué puedo ayudarte hoy?", n > 0 and f < T(T_SEND), send_p)
    if n:
        x0 = (110 + 34) * SS; y0 = 400 * SS + 28 * SS + 42 * SS
        d.line((x0, y0, x0 + FT.getlength(LINK), y0), fill=(110, 160, 230), width=2 * SS)
    return sc
def zoom_state(f):
    p = ease_io((f - T(T_PASTE)) / 12) if f >= T(T_PASTE) else 0.0
    return 540 + (520 - 540) * p, 410 + (440 - 410) * p, 1 + 0.18 * p
def scene_Z(f, f0):
    sc = chat_scene(f)
    def sample(x, y, z):
        a = 1 / z; x0 = x - W / 2 * a; y0 = y - TOP / 2 * a
        return sc.transform((W, TOP), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=PAGE + (255,))
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
    win.paste(v, (0, 0), WMASK); ImageDraw.Draw(win).rounded_rectangle((WX0, WY0, WX1, WY1), 30, outline=BORDER, width=2)
    a = min(1, (f - f0) / 5)
    if a < 1: win = Image.blend(PANEL, win, a)
    return win
WX0, WY0, WX1, WY1 = 56, 236, 1024, 786
WMASK = Image.new("L", (W, TOP), 0); ImageDraw.Draw(WMASK).rounded_rectangle((WX0, WY0, WX1, WY1), 30, fill=255)
SCENE_FN = {"A": scene_A, "B": scene_B, "C": scene_C, "D": scene_D, "E": scene_E, "F": scene_F, "G": scene_G, "H": scene_H,
            "I": scene_I, "J": scene_J, "K": scene_K, "Z": scene_Z}

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
    for t in (5.20, 6.00, 10.30, 12.72, 16.70, 17.10, 17.50, 18.83, 22.27, 22.40, 24.83, 25.23, 26.67, 27.07, 34.91, 39.15, 41.39,
              46.99, 50.43):
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
