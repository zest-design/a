import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p9"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/33518428-45_base.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)
PAGE = (31, 30, 29); CARD = (44, 43, 41); BORDER = (72, 70, 67); TXT = (236, 235, 228); MUTED = (160, 158, 150)
ORANGE = (217, 119, 87); GREEN = (82, 196, 120)
BRAND = {"Perplexity": (32, 128, 141), "Firecrawl": (240, 90, 40), "Playwright": (46, 160, 90)}
FD = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(FD + n, int(s))
def serif(s): return ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf", int(s))
def fa(s): return ImageFont.truetype(f"{S}/fa/fa-solid.ttf", int(s))
POP = f"{S}/poppins/Poppins-800.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SPARK = Image.open(f"{S}/p3/spark.png").convert("RGBA")
def spark(h): return SPARK.resize((int(SPARK.width * h / SPARK.height), int(h)), Image.LANCZOS)

# ---------------- cuts -------------------------------------------------------------
SIL = [(0.00, 0.17), (8.25, 8.41), (16.85, 17.08), (17.18, 17.37), (17.89, 18.15), (26.73, 26.94), (27.65, 27.94),
       (28.35, 28.50), (29.22, 29.49), (29.82, 29.95), (33.49, 33.68), (38.34, 38.59), (38.75, 38.94), (41.98, 42.14)]
END = 43.86; PAD = 0.04
KEEP = []; cur = SIL[0][1] - PAD
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
    (0.00, 2.70, "Aquí tienes los tres conectores más potentes para Claude."),
    (3.04, 8.00, "Número uno: Perplexity. Convierte a Claude en el investigador con IA más potente del planeta."),
    (8.16, 16.85, "Le da a Claude el poder de encontrar cualquier artículo, cita o dato al instante, y se asegura de que nunca alucine ni reciba información desactualizada."),
    (17.31, 28.30, "Número dos: Firecrawl. Le permite a Claude ver internet, y así tú puedes hacer scraping, copiar datos de cualquier sitio web, extraer recursos de una marca e incluso investigar tu competencia por ti."),
    (28.51, 38.30, "Número tres: Playwright. Le da manos a Claude, así puede controlar tu navegador, rellenar formularios, probar tu sitio web e incluso usar herramientas que no tienen conexión con IA."),
    (38.67, 43.83, "Si quieres la configuración completa, comenta aquí abajo CONECTORES y te la hago llegar."),
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
HL = [["perplexity"], ["firecrawl"], ["playwright"], ["conectores"]]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(WORDS):
    hit = next((p for p in HL if [norm(w[0]) for w in WORDS[i:i + len(p)]] == p and not (p == ["conectores"] and WORDS[i][0] != "CONECTORES")), None)
    if hit: g = WORDS[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [WORDS[i]]; i += 1; hl = False
        while i < len(WORDS) and len(g) < 3 and not PUNCT.search(g[-1][0]) and not g[-1][2]:
            if WORDS[i][1] - g[0][1] > 0.8 or sum(len(w[0]) for w in g) + len(WORDS[i][0]) > 16: break
            if WORDS[i][0] == "CONECTORES" or norm(WORDS[i][0]) in ("perplexity", "firecrawl", "playwright"): break
            g.append(WORDS[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w[0] for w in g))
    key = txt == "CONECTORES"
    if not key: txt = txt.lower().replace("claude", "Claude").replace(" ia", " IA").replace("perplexity", "Perplexity").replace("firecrawl", "Firecrawl").replace("playwright", "Playwright")
    end = g[-1][3] + 0.25 if g[-1][2] else None
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1], end=end, key=key))
for k, c in enumerate(chunks):
    if k and chunks[k - 1]["key"]: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.0)
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
F_SPLIT0, F_SPLIT1 = fo(3.04), fo(38.55)
TRANS = 9
TITLE = white_boxes(["Los 3 conectores más", "potentes para Claude"], 54, "\U0001F913")
LABEL_IM = {n: white_boxes([t], 60) for n, t in (("P", "1. Perplexity"), ("F", "2. Firecrawl"), ("W", "3. Playwright"))}
SC = [(3.04, "P"), (17.31, "F"), (28.51, "W")]
SC = [(fo(t), n) for t, n in SC]
def scene_at(f):
    s_ = None
    for f0, n in SC:
        if f >= f0: s_ = (f0, n)
    return s_
def T(t): return fo(t)

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
def intro_card(name, sub, icon):
    im = card(900, 250); d = ImageDraw.Draw(im)
    im.alpha_composite(icon_tile(icon, BRAND[name], 150), (80, 80))
    d.text((270, 110), name, font=font("InterDisplay-Bold.otf", 76), fill=WHITE)
    rr(d, (272, 210, 272 + F_M.getlength(sub) + 40, 258), 24, fill=(60, 58, 55))
    d.text((292, 234), sub, font=F_M, fill=TXT, anchor="lm")
    sp = spark(34); im.alpha_composite(sp, (int(272 + F_M.getlength(sub) + 58), 217))
    return im
INTRO = {"P": intro_card("Perplexity", "Conector para Claude", ""),
         "F": intro_card("Firecrawl", "Conector para Claude", ""),
         "W": intro_card("Playwright", "Conector para Claude", "")}

def panel_bg():
    yy, xx = np.mgrid[0:TOP, 0:W]
    bg = np.zeros((TOP, W, 3), np.float32) + np.array(PAGE, np.float32)
    gl = np.exp(-(((xx - 160) / 600.0) ** 2 + ((yy - 120) / 420.0) ** 2))[..., None]
    bg = bg * (1 - 0.22 * gl) + np.array(ORANGE, np.float32) * 0.22 * gl
    return Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
PANEL = panel_bg()

def claude_window(w, h):
    im = card(w, h, 26, fill=PAGE); return im

# ---- Perplexity scene -------------------------------------------------------------
def scene_P(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(4.48):
        s, a, dy = pop(k); paste(im, INTRO["P"], 540, 560 + dy, s, a); return im
    win = card(960, 440, 26, fill=PAGE); d = ImageDraw.Draw(win); ox, oy = 30, 30
    # user message bubble
    msg = "Investiga el mercado de coches eléctricos en España"
    bw = F_S.getlength(msg) + 56
    rr(d, (ox + 960 - 24 - bw, oy + 24, ox + 960 - 24, oy + 92), 22, fill=(20, 20, 19))
    d.text((ox + 960 - 24 - bw + 28, oy + 58), msg, font=F_S, fill=TXT, anchor="lm")
    win.alpha_composite(spark(38), (ox + 28, oy + 124))
    # tool call pill
    t_tool = T(4.90)
    if f >= t_tool:
        kk = f - t_tool; done = f >= T(8.16)
        pill = f"{'Investigó' if done else 'Buscando con'} Perplexity" + ("" if not done else " · 24 fuentes")
        pw = F_M.getlength(pill) + 110
        rr(d, (ox + 84, oy + 116, ox + 84 + pw, oy + 172), 28, fill=(48, 47, 45), outline=BORDER, width=2)
        d.text((ox + 118, oy + 144), "" if done else "", font=fa(24), fill=GREEN if done else BRAND["Perplexity"], anchor="mm")
        d.text((ox + 146, oy + 144), pill, font=F_M, fill=TXT, anchor="lm")
        if not done:   # progress bar
            p = (kk / max(1, T(8.16) - t_tool)); rr(d, (ox + 84, oy + 190, ox + 84 + 600, oy + 198), 4, fill=(60, 58, 55))
            rr(d, (ox + 84, oy + 190, ox + 84 + 600 * min(1, p), oy + 198), 4, fill=BRAND["Perplexity"])
    # answer with source chips
    if f >= T(8.16):
        lines = ["El mercado creció un 38% en 2025, impulsado por", "el Plan MOVES y la bajada de precios…"]
        shown = int((f - T(8.16)) * 3.2); acc = 0
        for j, ln in enumerate(lines):
            part = ln[:max(0, shown - acc)]; acc += len(ln)
            d.text((ox + 86, oy + 210 + j * 46), part, font=F_S, fill=TXT)
        for q, (lab, ic, tt) in enumerate((("Artículo", "", 10.24), ("Cita", "", 10.80), ("Dato", "", 11.36))):
            if f >= T(tt) and f < T(14.48):
                kk = f - T(tt); s, a, dy = pop(kk)
                c_ = chip(lab, ic, BRAND["Perplexity"])
                paste(win, c_, ox + 86 + 130 + q * 270, oy + 350 + dy, s * 0.9, a)
    for q, (lab, tt) in enumerate((("Sin alucinaciones", 14.48), ("Datos actualizados", 15.76))):
        if f >= T(tt):
            s, a, dy = pop(f - T(tt)); paste(win, chip(lab, CHECK, (46, 140, 80)), ox + 86 + 190 + q * 400, oy + 350 + dy, s * 0.9, a)
    paste(im, win, 540, 548, 0.96, 1)
    return im

# ---- Firecrawl scene --------------------------------------------------------------
def browser(w, h, url):
    im = card(w, h, 22, fill=(250, 250, 248), border=(210, 210, 210)); d = ImageDraw.Draw(im)
    rr(d, (30, 30, 30 + w, 100), 22, fill=(236, 236, 234)); d.rectangle((30, 70, 30 + w, 100), fill=(236, 236, 234))
    for q, col in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        d.ellipse((58 + q * 30, 56, 76 + q * 30, 74), fill=col)
    rr(d, (170, 48, 30 + w - 30, 84), 18, fill=WHITE)
    d.text((196, 66), "", font=fa(18), fill=(120, 120, 120), anchor="mm"); d.text((216, 66), url, font=F_M, fill=(60, 60, 60), anchor="lm")
    return im
def scene_F(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(18.99):
        s, a, dy = pop(k); paste(im, INTRO["F"], 540, 560 + dy, s, a); return im
    if f < T(23.87):
        b = browser(600, 400, "tienda-ejemplo.com"); d = ImageDraw.Draw(b)
        # page content
        rr(d, (60, 130, 340, 300), 14, fill=(232, 228, 222)); d.text((200, 215), "", font=fa(70), fill=(200, 160, 120), anchor="mm")
        d.text((370, 140), "Zapatillas Run X", font=font("InterDisplay-Bold.otf", 34), fill=(30, 30, 30))
        d.text((370, 190), "89,90 €", font=font("InterDisplay-Bold.otf", 40), fill=(220, 80, 40))
        for q in range(3): rr(d, (370, 250 + q * 26, 370 + [220, 180, 200][q], 262 + q * 26), 6, fill=(220, 220, 220))
        rr(d, (370, 340, 560, 386), 12, fill=(30, 30, 30)); d.text((465, 363), "Comprar", font=F_M, fill=WHITE, anchor="mm")
        # scanning sweep
        p = ((f - T(18.99)) % 45) / 45; ys = 110 + p * 310
        sw = Image.new("RGBA", b.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sw)
        ds.rectangle((30, ys - 40, 630, ys), fill=BRAND["Firecrawl"] + (40,)); ds.line((30, ys, 630, ys), fill=BRAND["Firecrawl"] + (255,), width=4)
        b.alpha_composite(sw)
        paste(im, b, 362, 550, 0.94, min(1, (f - T(18.99)) / 5 + 0.2))
        if f >= T(21.39):   # extracted JSON
            j = card(360, 400, 22, fill=(24, 24, 23)); dj = ImageDraw.Draw(j)
            rows = [('{', TXT), ('  "producto":', (156, 220, 254)), ('    "Run X",', (206, 145, 120)), ('  "precio": 89.90,', (156, 220, 254)),
                    ('  "stock": true,', (156, 220, 254)), ('  "fotos": 6', (156, 220, 254)), ('}', TXT)]
            n = int((f - T(21.39)) / 3) + 1
            for q, (row, col) in enumerate(rows[:n]): dj.text((56, 60 + q * 46), row, font=F_MONO, fill=col)
            s, a, dy = pop(f - T(21.39)); paste(im, j, 838, 560 + dy, s * 0.94, a)
        return im
    if f < T(26.19):   # brand assets
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 80), "Recursos de marca extraídos", font=F_H, fill=WHITE)
        cols = [(20, 24, 38), (240, 90, 40), (255, 196, 120), (245, 242, 236)]
        for q, col in enumerate(cols):
            kq = f - T(23.87) - q * 3
            if kq >= 0:
                s = ease_out_back(kq / 7); x = 80 + q * 210
                rr(d, (x, 170, x + int(180 * s), 330), 20, fill=col, outline=(90, 90, 90), width=2)
                if s > 0.9: d.text((x + 10, 350), "#%02X%02X%02X" % col, font=F_MONO, fill=MUTED)
        d.text((80, 410), "Tipografía:", font=F_S, fill=MUTED); d.text((260, 400), "Aa Inter Display", font=font("InterDisplay-Bold.otf", 40), fill=WHITE)
        s, a, dy = pop(f - T(23.87)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    # competitors
    c_ = card(940, 470); d = ImageDraw.Draw(c_)
    d.text((80, 76), "Análisis de competencia", font=F_H, fill=WHITE)
    rows = [("Competidor A", 0.82, "29 €/mes"), ("Competidor B", 0.64, "19 €/mes"), ("Tu marca", 0.48, "24 €/mes")]
    for q, (n_, v, pr) in enumerate(rows):
        kq = f - T(26.19) - q * 4; y = 170 + q * 100
        d.text((80, y + 20), n_, font=F_B, fill=TXT if q < 2 else BRAND["Firecrawl"])
        rr(d, (380, y + 8, 780, y + 40), 16, fill=(60, 58, 55))
        if kq >= 0: rr(d, (380, y + 8, 380 + 400 * v * ease_out_cubic(kq / 12), y + 40), 16, fill=BRAND["Firecrawl"] if q == 2 else (150, 148, 140))
        d.text((800, y + 24), pr, font=F_M, fill=MUTED, anchor="lm")
    s, a, dy = pop(f - T(26.19)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im

# ---- Playwright scene -------------------------------------------------------------
def scene_W(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(30.43):
        s, a, dy = pop(k); paste(im, INTRO["W"], 540, 560 + dy, s, a); return im
    if f < T(34.67):
        b = browser(900, 470, "mi-sitio.com/contacto"); d = ImageDraw.Draw(b)
        d.text((90, 140), "Contacto", font=font("InterDisplay-Bold.otf", 44), fill=(30, 30, 30))
        fields = [("Nombre", "Laura Gómez"), ("Email", "laura@empresa.com")]
        t_fill = T(33.63)
        for q, (lab, val) in enumerate(fields):
            y = 210 + q * 100
            d.text((90, y), lab, font=F_M, fill=(90, 90, 90))
            rr(d, (90, y + 36, 610, y + 84), 12, fill=WHITE, outline=(46, 160, 90) if f >= t_fill + q * 14 else (200, 200, 200), width=3)
            if f >= t_fill + q * 14:
                n = int((f - t_fill - q * 14) * 1.4); d.text((108, y + 60), val[:n], font=F_S, fill=(30, 30, 30), anchor="lm")
        rr(d, (660, 386, 880, 440), 14, fill=(46, 160, 90)); d.text((770, 413), "Enviar", font=F_B, fill=WHITE, anchor="mm")
        # automated cursor
        path = [(700, 160), (350, 270), (350, 370), (770, 413)]
        tt = [T(30.43), T(33.30), T(33.63) + 14, T(34.40)]
        cx, cy = path[0]
        for q in range(len(tt) - 1):
            if tt[q] <= f < tt[q + 1]:
                u = ease_io((f - tt[q]) / max(1, tt[q + 1] - tt[q])); cx = path[q][0] + (path[q + 1][0] - path[q][0]) * u; cy = path[q][1] + (path[q + 1][1] - path[q][1]) * u
            elif f >= tt[q + 1]: cx, cy = path[q + 1]
        d.text((cx + 30, cy + 30), "", font=fa(52), fill=(20, 20, 20), stroke_width=3, stroke_fill=WHITE)
        tag = Image.new("RGBA", (360, 56), (0, 0, 0, 0)); dt = ImageDraw.Draw(tag)
        rr(dt, (0, 0, 359, 55), 28, fill=(46, 160, 90)); dt.text((180, 28), "Claude controla el navegador", font=font("Inter-SemiBold.otf", 24), fill=WHITE, anchor="mm")
        b.alpha_composite(tag, (int(min(560, cx + 60)), int(cy + 50)))
        paste(im, b, 540, 550, 0.94, min(1, (f - T(30.43)) / 5 + 0.2)); return im
    if f < T(36.03):   # tests
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 76), "Pruebas de tu sitio web", font=F_H, fill=WHITE)
        tests = ["Página de inicio carga", "Formulario de contacto", "Proceso de compra", "Versión móvil"]
        for q, t_ in enumerate(tests):
            y = 160 + q * 72; on = f >= T(34.67) + 4 + q * 5
            d.ellipse((80, y + 4, 124, y + 48), fill=(46, 160, 90) if on else (70, 68, 64))
            if on: d.text((102, y + 26), "", font=fa(22), fill=WHITE, anchor="mm")
            d.text((150, y + 26), t_, font=F_B, fill=TXT if on else MUTED, anchor="lm")
        if f >= T(34.67) + 24:
            rr(d, (610, 380, 900, 440), 30, fill=(30, 70, 45), outline=(46, 160, 90), width=3)
            d.text((755, 410), "4/4 superadas", font=F_B, fill=WHITE, anchor="mm")
        s, a, dy = pop(f - T(34.67)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    c_ = card(940, 470); d = ImageDraw.Draw(c_)
    d.text((80, 76), "Herramientas sin conexión con IA", font=F_H, fill=WHITE)
    tools = [("", "Excel web"), ("", "Correo"), ("", "Calendario"), ("", "Tu CRM")]
    for q, (ic, nm) in enumerate(tools):
        kq = f - T(36.03) - q * 4
        if kq >= 0:
            s = ease_out_back(kq / 7); x = 80 + q * 210
            rr(d, (x, 170, x + 180, 350), 22, fill=(52, 51, 49), outline=BORDER, width=2)
            d.text((x + 90, 235), ic, font=fa(max(8, int(60 * min(1, s)))), fill=(46, 160, 90), anchor="mm")
            d.text((x + 90, 310), nm, font=F_M, fill=TXT, anchor="mm")
    d.text((80, 400), "  Claude las usa por ti, como una persona", font=F_S, fill=MUTED)
    s, a, dy = pop(f - T(36.03)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
SCENE_FN = {"P": scene_P, "F": scene_F, "W": scene_W}

def top_panel(f):
    f0, n = scene_at(f)
    v = SCENE_FN[n](f, f0)
    # code label (white box) on top of the panel
    k = f - f0; s, a, dy = pop(k)
    paste(v, LABEL_IM[n], 540, 266, 1.0, 1.0)
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
    for t in (4.48, 10.24, 10.80, 11.36, 14.48, 15.76, 18.99, 21.39, 23.87, 26.19, 30.43, 34.67, 36.03):
        ev.append(("pluck", T(t) / FPS))
    ev.append(("boom", KEY["f0"] / FPS))
    return ev

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
        for ch in chunks:
            if ch["key"] or not (ch["f0"] <= f < ch["f1"]) or KEY["f0"] <= f < KEY["f1"]: continue
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
