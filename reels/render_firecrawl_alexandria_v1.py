import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p15"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/bdd3e3cb-Le-dije-la-verdad-esta-20261026-175935_1.mp4"
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
SIL = [(0.00, 0.56), (2.32, 2.46), (6.65, 7.09), (8.68, 9.03), (14.04, 14.31), (14.59, 15.37), (19.32, 19.61), (20.35, 20.85),
       (23.57, 23.80), (26.08, 26.24), (26.80, 27.12), (27.70, 27.91), (27.91, 28.29), (35.76, 36.20), (41.74, 42.21), (44.71, 45.03),
       (45.94, 46.52), (51.95, 52.12), (53.57, 53.80), (54.47, 54.84), (56.14, 58.46), (59.64, 59.77), (65.91, 66.25), (66.49, 66.80),
       (69.86, 70.02), (71.01, 71.24), (72.48, 72.73), (73.17, 73.53), (76.14, 76.32), (77.75, 77.87)]
END = 78.06; PAD = 0.04
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
    (0.56, 8.68, "Claude te está mintiendo, y aunque tú veas miles de enlaces en sus respuestas, la gran mayoría es falso o están desactualizados."),
    (9.03, 14.04, "Esto fue lo que descubrieron los investigadores cuando se pusieron a analizar enlace por enlace de todas las respuestas."),
    (15.37, 20.35, "¿Cómo puedes solucionar esto? Ve a Claude, haz clic en conectores y conecta Firecrawl."),
    (20.85, 27.70, "Luego, cuando lo conectes con tu cuenta, vas a ver que Claude se convierte en el investigador más potente del planeta."),
    (28.10, 35.76, "Firecrawl ha creado una biblioteca de conocimiento muy potente para agentes de inteligencia artificial. Se llama Alexandria y obtiene datos de miles"),
    (36.20, 41.74, "de proveedores. Así consigues que la información más precisa sobre empresas, actividad, contratación e investigación"),
    (42.21, 45.94, "sea lo más auténtica posible, incluso para encontrar clientes."),
    (46.52, 51.95, "Pídele a Claude que use Alexandria para encontrar empresas que estén contratando en tu área de negocio."),
    (52.07, 56.10, "Claude podrá combinar datos reales de contratación real"),
    (58.46, 65.91, "para explicarte por qué cada negocio podría encajar contigo. Así llegas a la persona responsable con la información más precisa en tiempo real."),
    (66.25, 71.01, "Si quieres mi configuración completa y otros 10 casos de uso para Firecrawl,"),
    (71.24, 78.06, "comenta aquí abajo FIRE y te lo hago llegar. He preparado para ti un contenido paso a paso para que tú lo puedas usar."),
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
HL = [["firecrawl"], ["alexandria"], ["FIRE"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("FIRE"): return ["FIRE"]
    return next((p for p in HL if p != ["FIRE"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "FIRE"
    if not hl: txt = txt.lower().replace("claude", "Claude").replace("firecrawl", "Firecrawl").replace("alexandria", "Alexandria")
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
F_SPLIT0, F_SPLIT1 = fo(2.48), fo(66.25)
TRANS = 9
TITLE = white_boxes(["CLAUDE TE ESTÁ", "MINTIENDO"], 56, chr(0x1F925))
SC = [(2.48, "A"), (9.03, "B"), (15.37, "C"), (20.85, "D"), (28.10, "E"), (36.20, "F"), (42.21, "G"), (46.52, "H"), (52.07, "I"), (59.95, "J"), (61.66, "K")]
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

# ---- scenes for the Firecrawl / Alexandria video (Claude) ------------------------------------------
FC_RED = (250, 93, 25); GOOD = (38, 186, 120); BADC = (232, 72, 72); AMBER = (230, 160, 40)
FIRE = IC(0xf06d)
def fc_tile(s):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, s - 1, s - 1), int(s / 4.2), fill=FC_RED); d.text((s / 2, s / 2 + 1), FIRE, font=fa(s * 0.52), fill=WHITE, anchor="mm")
    return im
def status_pill(d, xy, txt, col):
    x, y = xy; w_ = F_XS.getlength(txt) + 26
    rr(d, (x - w_, y - 17, x, y + 17), 9, fill=tuple(int(c * 0.28) for c in col), outline=col, width=2)
    d.text((x - w_ / 2, y), txt, font=font("Inter-SemiBold.otf", 19), fill=col, anchor="mm")
LINKS = [("techdaily.com/ia-2023", "404", BADC), ("statsworld.io/2022-data", "DESACTUALIZADO", AMBER), ("newsline.com/mercados", "200 OK", GOOD),
         ("blog.saasly.co/precios", "404", BADC), ("govdata.org/censo-2019", "DESACTUALIZADO", AMBER), ("apizef.dev/auth", "404", BADC)]
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)

# A · Claude's answer is full of broken links (layout) ----------------------------------------------
def scene_A(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450, fill=PAGE); d = ImageDraw.Draw(c_)
    it(d, (66, 78), IC(0xf0c1), "Comprobación de enlaces", F_T, WHITE, icol=ORANGE)
    d.text((910, 80), "Respuesta de Claude", font=F_SM, fill=MUTED, anchor="rm")
    for q, (url, st, col) in enumerate(LINKS):
        tt = T(3.30) + q * 3
        if f < tt: continue
        y = 150 + q * 50; k = f - tt
        d.text((70, y), url, font=MONO, fill=(170, 190, 235), anchor="lm")
        if f >= T(5.44) + q * 3:
            status_pill(d, (910, y), st, col)
            if col != GOOD and f >= T(7.92): d.line((70, y, 70 + MONO.getlength(url), y), fill=BADC, width=2)
    if f >= T(6.96):
        k = f - T(6.96); paste(c_, badge("La mayoría: falsos o desactualizados", IC(0xf071), BADC, F_SM), 500, 456, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
    put(im, c_, 2.48); return im

# B · researchers checked link by link (layout) -----------------------------------------------------
def scene_B(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450, fill=PAGE); d = ImageDraw.Draw(c_)
    it(d, (66, 78), IC(0xf002), "Análisis enlace por enlace", F_T, WHITE, icol=ORANGE)
    scan = (f - T(11.84)) / 5 if f >= T(11.84) else -1
    for q, (url, st, col) in enumerate(LINKS):
        y = 150 + q * 50
        act = 0 <= scan - q < 1
        if act: rr(d, (56, y - 22, 924, y + 22), 10, fill=(52, 48, 44))
        d.text((70, y), url, font=MONO, fill=(170, 190, 235) if scan >= q else (110, 110, 110), anchor="lm")
        if scan - q >= 1:
            ok = col == GOOD
            d.ellipse((866, y - 17, 900, y + 17), fill=GOOD if ok else BADC)
            d.text((883, y + 1), CHECK if ok else IC(0xf00d), font=fa(18), fill=WHITE, anchor="mm")
        elif act:
            d.text((883, y), IC(0xf002), font=fa(24), fill=ORANGE, anchor="mm")
    it(d, (70, 448), IC(0xf0c0), "Estudio de investigadores", F_SM, MUTED)
    put(im, c_, 9.03); return im

# C · Claude → Connectors → Firecrawl (layout, dark Claude UI in Spanish) ----------------------------
def scene_C(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450, fill=PAGE); d = ImageDraw.Draw(c_)
    d.text((70, 80), "Conectores", font=font("InterDisplay-Bold.otf", 44), fill=WHITE, anchor="lm")
    d.text((70, 124), "Conecta Claude con tus herramientas favoritas.", font=F_SM, fill=MUTED, anchor="lm")
    rr(d, (560, 58, 910, 104), 14, fill=(44, 43, 41), outline=BORDER, width=2)
    d.text((586, 81), IC(0xf002), font=fa(20), fill=MUTED, anchor="mm")
    q_ = "Firecrawl"; n = 0 if f < T(17.68) else min(len(q_), int((f - T(17.68) + 1) * 14 / FPS))
    d.text((610, 81), q_[:n] if n else "Buscar", font=F_SM, fill=TXT if n else MUTED, anchor="lm")
    rows = [("Firecrawl", "Busca, extrae y analiza la web", None), ("Gmail", "Correo electrónico", IC(0xf0e0)), ("Google Drive", "Archivos y documentos", IC(0xf07b))]
    vis = rows if n < len(q_) else rows[:1]
    for q, (nm, sub, ic) in enumerate(vis):
        y = 190 + q * 92
        rr(d, (60, y - 38, 920, y + 38), 16, fill=(44, 43, 41), outline=ORANGE if nm == "Firecrawl" and n >= len(q_) else BORDER, width=2)
        if ic is None: c_.alpha_composite(fc_tile(56), (82, y - 28))
        else: rr(d, (82, y - 28, 138, y + 28), 14, fill=(70, 68, 64)); d.text((110, y), ic, font=fa(24), fill=WHITE, anchor="mm")
        d.text((160, y - 13), nm, font=F_B, fill=WHITE, anchor="lm"); d.text((160, y + 20), sub, font=F_XS, fill=MUTED, anchor="lm")
        if nm == "Firecrawl":
            on = f >= T(19.65)
            if f >= T(18.80) and not on:
                rr(d, (760, y - 24, 900, y + 24), 12, fill=WHITE); d.text((830, y), "Conectar", font=font("Inter-SemiBold.otf", 22), fill=(20, 20, 20), anchor="mm")
            elif on:
                rr(d, (820, y - 18, 890, y + 18), 18, fill=GOOD); d.ellipse((856, y - 14, 884, y + 14), fill=WHITE)
                d.text((806, y), "Conectado", font=F_SM, fill=(140, 220, 160), anchor="rm")
    put(im, c_, 15.37); return im

# D · the most powerful researcher on the planet — 3D globe --------------------------------------------
NG = 900; _i = np.arange(NG) + 0.5
GPH = np.arccos(1 - 2 * _i / NG); GTH = math.pi * (1 + 5 ** 0.5) * _i
GLOBE = np.stack([np.cos(GTH) * np.sin(GPH), np.cos(GPH), np.sin(GTH) * np.sin(GPH)], 1)
_r = np.random.default_rng(5); ARCS = [(int(_r.integers(NG)), int(_r.integers(NG))) for _ in range(16)]
def slerp(a, b, t):
    om = math.acos(max(-1, min(1, float(np.dot(a, b))))); s = math.sin(om) or 1e-6
    return (math.sin((1 - t) * om) * a + math.sin(t * om) * b) / s
def scene_D(f, f0):
    im = PANEL.copy(); k = f - f0
    lay = layer3d(); dl = ImageDraw.Draw(lay)
    cam = Cam(k * 0.012, -0.32, 6.2, 540, 540, 780)
    R = 2.0 * (0.85 + 0.15 * ease_out_cubic(k / 12))
    # soft glow behind the globe
    gl = Image.new("RGBA", (W, TOP), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse((540 - 300, 540 - 300, 540 + 300, 540 + 300), fill=ORANGE + (60,))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(60)))
    pts = []
    for p in GLOBE:
        X, Y, Z, kk = cam.proj(tuple(p * R)); pts.append((Z, X, Y, kk))
    zc = cam.dist
    for Z, X, Y, kk in sorted(pts, key=lambda t: -t[0]):
        front = Z < zc; r_ = (2.6 if front else 1.6) * S3 * kk / 125
        col = (240, 200, 180, 235) if front else (120, 90, 80, 120)
        dl.ellipse((X - r_, Y - r_, X + r_, Y + r_), fill=col)
    # glowing connection arcs (Claude researching everywhere)
    na = min(len(ARCS), int(max(0, k - 6) / 4))
    for q in range(na):
        a, b = GLOBE[ARCS[q][0]], GLOBE[ARCS[q][1]]
        seg = [slerp(a, b, t) * R * (1 + 0.25 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 28)]
        P = [cam.proj(tuple(s_)) for s_ in seg]
        prog = min(1.0, (k - 6 - q * 4) / 10)
        upto = max(2, int(len(P) * prog))
        dl.line([(x, y) for x, y, _, _ in P[:upto]], fill=ORANGE + (230,), width=3 * S3)
    im.alpha_composite(flat3d(lay))
    sp = spark(110); im.alpha_composite(sp, (int(540 - sp.width / 2), int(540 - sp.height / 2)))
    pill = Image.new("RGBA", (680, 80), (0, 0, 0, 0)); dp = ImageDraw.Draw(pill)
    rr(dp, (0, 0, 679, 79), 40, fill=(30, 29, 28, 235), outline=BORDER, width=2)
    pill.alpha_composite(spark(40), (36, 20)); dp.text((96, 40), "+", font=F_T, fill=MUTED, anchor="mm")
    pill.alpha_composite(fc_tile(46), (122, 17)); dp.text((190, 40), "Claude + Firecrawl", font=F_B, fill=WHITE, anchor="lm")
    s, a, dy = pop(k); paste(im, pill, 540, 280 + dy, s * 0.9, a)
    if f >= T(25.09):
        kk = f - T(25.09); paste(im, badge("El investigador más potente del planeta", IC(0xf0ac), ORANGE, F_SM), 540, 735, 0.6 + 0.4 * ease_out_back(kk / 7), min(1, 0.3 + kk / 3))
    return im

# E · Alexandria knowledge library — 3D shelves ------------------------------------------------------------
BOOKC = [(176, 70, 52), (60, 98, 150), (196, 150, 70), (70, 130, 96), (140, 70, 120), (210, 110, 70), (90, 90, 160)]
_rb = np.random.default_rng(8)
SHELF = []
for side in (-1, 1):
    for lvl in range(4):
        z = 0.0
        while z < 16:
            w_ = float(_rb.uniform(0.18, 0.34)); h_ = float(_rb.uniform(0.55, 0.82))
            SHELF.append((side, lvl, z + w_ / 2, w_, h_, BOOKC[int(_rb.integers(len(BOOKC)))])); z += w_ + 0.02
def scene_E(f, f0):
    im = PANEL.copy(); k = f - f0
    lay = layer3d(); dl = ImageDraw.Draw(lay)
    cz = -2.0 + k * 0.05
    cam = Cam(0.0, -0.08, 0.0, 540, 470, 640)
    def P(x, y, z): return cam.proj((x, y, z - cz))
    # floor + aisle
    fl = [P(-2.2, -1.4, cz + 0.6)[:2], P(2.2, -1.4, cz + 0.6)[:2], P(2.2, -1.4, cz + 30)[:2], P(-2.2, -1.4, cz + 30)[:2]]
    dl.polygon(fl, fill=(58, 44, 36))
    dl.polygon([P(-0.5, -1.39, cz + 0.6)[:2], P(0.5, -1.39, cz + 0.6)[:2], P(0.5, -1.39, cz + 30)[:2], P(-0.5, -1.39, cz + 30)[:2]], fill=(120, 40, 30))
    items = []
    for side, lvl, z, w_, h_, col in SHELF:
        zz = z - cz
        if zz < 0.7 or zz > 18: continue
        x = side * 1.75; y = -1.0 + lvl * 0.95
        for fc in box_faces(cam, (x, y + h_ / 2, zz), (0.5, h_, w_), col): items.append(fc)
    for side in (-1, 1):
        for lvl in range(5):
            y = -1.05 + lvl * 0.95
            for zz0 in np.arange(max(0.8, 0.0 - cz % 2 + 0.8), 18, 2.0):
                for fc in box_faces(cam, (side * 1.75, y, zz0 + 1.0), (0.62, 0.06, 2.0), (92, 62, 42)): items.append(fc)
    items.sort(key=lambda t: -t[0])
    for z, poly, col in items:
        fade = max(0.25, min(1.0, 1.25 - z / 18))
        dl.polygon(poly, fill=tuple(int(c * fade) for c in col))
    lib = Image.new("RGBA", (W, TOP), (34, 26, 22, 255)); lib.alpha_composite(flat3d(lay))
    im = chat_window(lib, f, f0 - 10)
    if f >= T(29.17):
        kk = f - T(29.17); t_ = card(760, 120, 26, fill=(30, 29, 28)); dt = ImageDraw.Draw(t_)
        t_.alpha_composite(fc_tile(64), (62, 58))
        dt.text((150, 74), "Biblioteca de conocimiento", font=F_B, fill=WHITE, anchor="lm"); dt.text((150, 112), "para agentes de IA", font=F_SM, fill=MUTED, anchor="lm")
        paste(im, t_, 540, 300, 0.7 + 0.3 * ease_out_back(kk / 8), min(1, 0.3 + kk / 3))
    if f >= T(33.25):
        kk = f - T(33.25); paste(im, badge("Alexandria", IC(0xf02d), FC_RED, font("InterDisplay-Bold.otf", 44)), 540, 690, 0.6 + 0.4 * ease_out_back(kk / 7), min(1, 0.3 + kk / 3))
    return im

# F · thousands of data providers flowing in — 3D network ---------------------------------------------------
_rn = np.random.default_rng(12); NN = 220
NODES = _rn.normal(0, 1, (NN, 3)); NODES = NODES / np.linalg.norm(NODES, axis=1)[:, None] * _rn.uniform(2.6, 3.6, (NN, 1))
NPH = _rn.uniform(0, 1, NN)
CATS = [("Empresas", IC(0xf1ad), 38.20), ("Actividad", IC(0xf201), 39.91), ("Contratación", IC(0xf0b1), 40.39), ("Investigación", IC(0xf0c3), 41.11)]
def scene_F(f, f0):
    im = PANEL.copy(); k = f - f0
    lay = layer3d(); dl = ImageDraw.Draw(lay)
    cam = Cam(0.4 + k * 0.01, -0.25, 9.6, 540, 545, 700)
    core = []
    for fc in box_faces(cam, (0, 0, 0), (1.5, 1.5, 1.5), FC_RED, spin=k * 0.03): core.append(fc)
    pts = []
    for i, p in enumerate(NODES):
        X, Y, Z, kk = cam.proj(tuple(p)); pts.append((Z, X, Y, kk, i))
    for Z, X, Y, kk, i in sorted(pts, key=lambda t: -t[0]):
        r_ = 3.4 * S3 * kk / 95
        dl.ellipse((X - r_, Y - r_, X + r_, Y + r_), fill=(190, 210, 250, 245 if Z < cam.dist else 120))
    # data particles travelling to the core
    for i in range(0, NN, 2):
        t = (k / 30 + NPH[i]) % 1.0; p = NODES[i] * (1 - t)
        X, Y, Z, kk = cam.proj(tuple(p)); r_ = 3.0 * S3 * kk / 95
        dl.ellipse((X - r_, Y - r_, X + r_, Y + r_), fill=ORANGE + (int(255 * min(1, t * 3)),))
    core.sort(key=lambda t: -t[0])
    for z, poly, col in core: dl.polygon(poly, fill=col, outline=(255, 160, 120))
    im.alpha_composite(flat3d(lay))
    d = ImageDraw.Draw(im); X, Y = 540, 545
    d.text((X, Y), FIRE, font=fa(54), fill=WHITE, anchor="mm")
    tf = font("InterDisplay-Bold.otf", 40); tw = tf.getlength("Miles de proveedores de datos") + 90
    rr(d, (540 - tw / 2, 252, 540 + tw / 2, 316), 32, fill=(30, 29, 28, 235))
    it(d, (540, 284), IC(0xf1c0), "Miles de proveedores de datos", tf, WHITE, "mm", icol=ORANGE)
    for q, (lab, ic, tt) in enumerate(CATS):
        if f < T(tt): continue
        kk = f - T(tt); paste(im, badge(lab, ic, (70, 52, 44), F_SM), 540 + (q - 1.5) * 232, 712, 0.6 + 0.4 * ease_out_back(kk / 7), min(1, 0.3 + kk / 3))
    return im

# G · as authentic as possible — even for finding clients (layout) ------------------------------------------
def scene_G(f, f0):
    im = PANEL.copy()
    c_ = card(900, 400); d = ImageDraw.Draw(c_)
    c_.alpha_composite(icon_tile(IC(0xf140), FC_RED, 140), (80, 70))
    d.text((260, 112), "Datos auténticos", font=font("InterDisplay-Bold.otf", 56), fill=WHITE, anchor="lm")
    d.text((262, 172), "Verificados y al día", font=F_M, fill=MUTED, anchor="lm")
    for q, (lab, tt) in enumerate((("Información precisa", 42.63), ("Fuentes reales", 43.20), ("Ideal para encontrar clientes", 45.11))):
        if f < T(tt): continue
        y = 266 + q * 52; k = f - T(tt); dx = (1 - ease_out_cubic(k / 6)) * 30
        d.ellipse((84 + dx, y - 17, 118 + dx, y + 17), fill=GOOD); d.text((101 + dx, y + 1), CHECK, font=fa(18), fill=WHITE, anchor="mm")
        d.text((136 + dx, y), lab, font=F_B if q == 2 else F_M, fill=WHITE if q == 2 else TXT, anchor="lm")
    put(im, c_, 42.21); return im

# H · ask Claude to use Alexandria — dark chat, typing with zoom + motion blur -------------------------------
PROMPT = "Usa Alexandria para encontrar empresas que estén contratando en mi área de negocio"
T_TY0, T_TY1 = 46.70, 51.50
def chat_n(f):
    if f < T(T_TY0): return 0
    return min(len(PROMPT), int(len(PROMPT) * (f - T(T_TY0) + 1) / max(1, T(T_TY1) - T(T_TY0))))
def chat_scene(f):
    sc = Image.new("RGBA", (W * SS, TOP * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    sp = spark(50 * SS); g = "Buenas tardes"; gf = serif(56 * SS)
    gw = sp.width + 20 * SS + gf.getlength(g); gx = (W * SS - gw) / 2; gy = 320 * SS
    sc.alpha_composite(sp, (int(gx), int(gy - sp.height / 2)))
    d.text((gx + sp.width + 20 * SS, gy), g, font=gf, fill=(232, 230, 222), anchor="lm")
    n = chat_n(f)
    cur, bot = draw_input(d, sc, 110, W - 130, 380 * SS, PROMPT, n, (-1, -1), "¿En qué puedo ayudarte hoy?", n > 0, 0)
    return sc, cur
def cam_at(f):
    if f < T(T_TY0) - 4: return 540.0, 430.0, 1.0
    _, cur = chat_scene(f) if False else (None, None)
    return None
def zoom_target(f):
    n = chat_n(f)
    if n == 0: return 540.0, 430.0, 1.0
    lines = wrap(PROMPT[:n], FT, (W - 130 - 110 - 68) * SS)
    cx = (110 + 34) + FT.getlength(lines[-1]) / SS; cy = 380 + 28 + (len(lines) - 1) * LH + 20
    return 520.0, cy + 24, 1.16
def zoom_smooth(f):
    p = ease_io((f - T(T_TY0) + 4) / 10) if f >= T(T_TY0) - 4 else 0.0
    tx, ty, tz = zoom_target(max(f, T(T_TY0)))
    acc = [0.0, 0.0]; wsum = 0.0
    for j in range(8):   # short trailing average = smooth camera, deterministic per frame
        x_, y_, _ = zoom_target(max(T(T_TY0), f - j)); w_ = 0.8 ** j; acc[0] += x_ * w_; acc[1] += y_ * w_; wsum += w_
    tx, ty = acc[0] / wsum, acc[1] / wsum
    return 540 + (tx - 540) * p, 430 + (ty - 430) * p, 1 + (tz - 1) * p
def scene_H(f, f0):
    sc, _ = chat_scene(f)
    def sample(x, y, z):
        a = 1 / z; x0 = x - W / 2 * a; y0 = y - TOP / 2 * a
        return sc.transform((W, TOP), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=PAGE + (255,))
    x1, y1, z1 = zoom_smooth(f); x0_, y0_, z0 = zoom_smooth(f - 1)
    mv = math.hypot((x1 - x0_) * z1, (y1 - y0_) * z1) + abs(z1 - z0) * 900
    ns = 1 if mv < 2 else min(7, 2 + int(mv / 5))
    if ns == 1: v = sample(x1, y1, z1)
    else:
        acc = None
        for q in range(ns):
            u = q / (ns - 1); s_ = np.asarray(sample(x0_ + (x1 - x0_) * u, y0_ + (y1 - y0_) * u, z0 + (z1 - z0) * u), np.float32)
            acc = s_ if acc is None else acc + s_
        v = Image.fromarray((acc / ns).astype(np.uint8)).convert("RGBA")
    return chat_window(v, f, f0)
WX0, WY0, WX1, WY1 = 56, 236, 1024, 786
WMASK = Image.new("L", (W, TOP), 0); ImageDraw.Draw(WMASK).rounded_rectangle((WX0, WY0, WX1, WY1), 30, fill=255)
def chat_window(v, f, f0):
    win = PANEL.copy()
    sh = Image.new("RGBA", (W, TOP), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((WX0, WY0 + 12, WX1, WY1 + 12), 30, fill=(0, 0, 0, 140))
    win.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    win.paste(v, (0, 0), WMASK); ImageDraw.Draw(win).rounded_rectangle((WX0, WY0, WX1, WY1), 30, outline=BORDER, width=2)
    a = min(1, (f - f0) / 5)
    if a < 1: win = Image.blend(PANEL, win, a)
    return win

# I · combines real company data + real hiring activity (layout) --------------------------------------------
def scene_I(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450); d = ImageDraw.Draw(c_)
    srcs = [("Datos de empresa", IC(0xf1ad), ["Sector: fitness", "Equipo: 140 personas", "Crece un 30% al año"], 52.79),
            ("Contratación activa", IC(0xf0b1), ["Busca: editor de vídeo", "Publicado hace 2 días", "Contrato: freelance"], 54.84)]
    for q, (ttl, ic, rows, tt) in enumerate(srcs):
        if f < T(tt): continue
        k = f - T(tt); x0 = 70 + q * 300; dy = (1 - ease_out_cubic(k / 7)) * 30
        rr(d, (x0, 70 + dy, x0 + 285, 340 + dy), 18, fill=(38, 37, 35), outline=BORDER, width=2)
        it(d, (x0 + 20, 110 + dy), ic, ttl, font("Inter-SemiBold.otf", 25), WHITE, icol=ORANGE)
        for j, r_ in enumerate(rows): d.text((x0 + 22, 170 + j * 52 + dy), r_, font=font("Inter-Medium.otf", 23), fill=TXT, anchor="lm")
    if f >= T(55.45):
        k = f - T(55.45); p = ease_io(k / 9)
        for q in range(2):
            xa = 70 + q * 300 + 142; d.line((xa, 350, xa + (790 - xa) * p, 340 - p * 10), fill=ORANGE, width=4)
        if p >= 1:
            rr(d, (680, 110, 910, 330), 20, fill=(44, 34, 28), outline=ORANGE, width=3)
            c_.alpha_composite(spark(56), (765, 140))
            d.text((795, 240), "Encaja", font=F_B, fill=WHITE, anchor="mm"); d.text((795, 282), "contigo", font=F_B, fill=WHITE, anchor="mm")
    d.text((500, 410), "Datos reales + contratación real", font=F_M, fill=MUTED, anchor="mm")
    put(im, c_, 52.07); return im

# J · why each business could be a fit (layout, document-like) ---------------------------------------------
FITS = [("Nordia Fitness", "contrata editor de vídeo", "Equipo pequeño, sin editor interno."),
        ("Puerto Café & Co.", "contrata creador de contenido", "Lanzan su canal de YouTube este trimestre."),
        ("Lumen Academy", "contrata 2 editores", "Publican 300 vídeos al mes.")]
def scene_J(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450, fill=(246, 244, 238), border=(220, 216, 206)); d = ImageDraw.Draw(c_)
    d.text((70, 76), "Tres empresas que contratan lo que haces", font=font("Inter-SemiBold.otf", 30), fill=(30, 30, 30), anchor="lm")
    for q, (nm, what, why) in enumerate(FITS):
        tt = T(60.20) + q * 9
        if f < tt: continue
        y = 150 + q * 100; k = f - tt; dx = (1 - ease_out_cubic(k / 6)) * 30
        d.text((70 + dx, y), f"{q + 1}. {nm}", font=font("Inter-SemiBold.otf", 28), fill=(20, 20, 20), anchor="lm")
        d.text((70 + dx + font("Inter-SemiBold.otf", 28).getlength(f"{q + 1}. {nm}") + 14, y), what, font=F_SM, fill=(70, 70, 70), anchor="lm")
        d.text((96 + dx, y + 40), "¿Por qué encaja? " + why, font=font("Inter-Regular.otf", 22), fill=(90, 90, 90), anchor="lm")
        if k > 8: d.ellipse((880, y - 16, 912, y + 16), fill=GOOD); d.text((896, y + 1), CHECK, font=fa(17), fill=WHITE, anchor="mm")
    put(im, c_, 59.95); return im

# K · reach the person in charge with real-time info (layout) -----------------------------------------------
def scene_K(f, f0):
    im = PANEL.copy()
    c_ = card(900, 400, fill=(246, 244, 238), border=(220, 216, 206)); d = ImageDraw.Draw(c_)
    d.ellipse((80, 70, 200, 190), fill=(200, 140, 110)); d.text((140, 130), "LM", font=font("InterDisplay-Bold.otf", 46), fill=WHITE, anchor="mm")
    d.text((230, 104), "Laura Méndez", font=font("InterDisplay-Bold.otf", 44), fill=(20, 20, 20), anchor="lm")
    rr(d, (232, 140, 232 + F_SM.getlength("Directora de Marketing") + 30, 180), 10, fill=(250, 214, 120))
    d.text((247, 160), "Directora de Marketing", font=F_SM, fill=(40, 30, 10), anchor="lm")
    rows = [(IC(0xf0e0), "laura.m•••@nordia•••.com", 62.94), (IC(0xf0c1), "linkedin.com/in/laura-m•••", 63.66)]
    for q, (ic, txt, tt) in enumerate(rows):
        if f < T(tt): continue
        y = 250 + q * 52; it(d, (90, y), ic, txt, font("DejaVuSansMono.ttf", 24) if False else MONO, (50, 50, 50), icol=(120, 120, 120))
    if f >= T(65.34):
        k = f - T(65.34); d.ellipse((90, 352, 108, 370), fill=GOOD); d.text((122, 361), "Actualizado ahora · tiempo real", font=F_SM, fill=(40, 120, 70), anchor="lm")
    put(im, c_, 61.66); return im
SCENE_FN = {"A": scene_A, "B": scene_B, "C": scene_C, "D": scene_D, "E": scene_E, "F": scene_F, "G": scene_G, "H": scene_H,
            "I": scene_I, "J": scene_J, "K": scene_K}

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
    for t in (5.44, 6.96, 12.40, 18.80, 19.65, 25.09, 29.17, 33.25, 38.20, 39.91, 40.39, 41.11, 42.63, 43.20, 45.11, 52.79, 55.02,
              58.80, 59.74, 62.94, 65.34):
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
