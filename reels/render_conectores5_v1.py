import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p10"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/8919c5a6-46_base_3.mp4"
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
SIL = [(0.00, 0.57), (3.14, 3.29), (3.85, 4.02), (9.07, 9.45), (9.88, 10.05), (12.81, 13.00), (14.50, 14.75), (17.17, 17.50),
       (17.53, 17.77), (23.24, 23.51), (27.01, 27.30), (27.90, 28.41), (29.26, 29.63), (29.93, 30.16), (30.45, 30.72),
       (36.70, 36.97), (37.73, 38.05), (40.39, 40.64), (40.99, 41.35), (41.95, 42.12), (51.42, 51.64), (57.60, 57.81),
       (58.13, 58.33), (58.55, 58.79), (59.04, 59.22), (62.81, 62.98), (63.54, 63.81), (67.51, 67.67), (67.98, 68.26)]
END = 68.95; PAD = 0.04
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
    (0.32, 2.95, "Aquí tienes los cinco conectores más potentes de Claude."),
    (3.36, 9.07, "Número uno: Perplexity. Perplexity le da a Claude el acceso al motor de investigación más potente del planeta."),
    (9.28, 17.17, "¿Para qué? Para que haga investigaciones a fondo, para obtener información sobre cualquier tema e incluso obtener información en tiempo real, que a veces sabemos que va un poquito atrasada."),
    (17.72, 27.95, "Número dos: Firecrawl. Le permite a Claude ver internet, así puede hacer scraping, copiar datos de otros sitios web, extraer recursos de una marca e incluso investigar tu competencia por ti al instante."),
    (28.36, 40.39, "Número tres: PostHog. Convierte a Claude en tu detective privado: descubre bugs, encuentra dónde estás perdiendo clientes e incluso mejora tu sitio web automáticamente. Es como una auditoría completa totalmente gratuita."),
    (41.31, 51.42, "Número cuatro: Playwright. Le da manos a Claude. Aquí Claude empieza a poder controlar el navegador, puede hacer clic y puede usar herramientas que no tienen conexión con la inteligencia artificial, conexión directa."),
    (51.55, 63.54, "Número cinco: Composio. Le permite a Claude conectarse a todas las apps que usas a la vez, en lugar de tener que conectar una por una. Es como un agregador de MCPs, de conectores, que te da habilidades extremas."),
    (63.55, 68.90, "Si tú quieres el prompt para configurar todo esto de una única vez, comenta aquí abajo POST que te lo hago llegar."),
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
HL = [["perplexity"], ["firecrawl"], ["posthog"], ["playwright"], ["composio"], ["post"]]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(WORDS):
    hit = next((p for p in HL if [norm(w[0]) for w in WORDS[i:i + len(p)]] == p and not (p == ["post"] and not WORDS[i][0].startswith("POST"))), None)
    if hit: g = WORDS[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [WORDS[i]]; i += 1; hl = False
        while i < len(WORDS) and len(g) < 3 and not PUNCT.search(g[-1][0]) and not g[-1][2]:
            if WORDS[i][1] - g[0][1] > 0.8 or sum(len(w[0]) for w in g) + len(WORDS[i][0]) > 16: break
            if WORDS[i][0].startswith("POST") or norm(WORDS[i][0]) in ("perplexity", "firecrawl", "posthog", "playwright", "composio"): break
            g.append(WORDS[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w[0] for w in g))
    key = txt == "POST"
    if not key: txt = txt.lower().replace("claude", "Claude").replace(" ia", " IA").replace("perplexity", "Perplexity").replace("firecrawl", "Firecrawl").replace("playwright", "Playwright").replace("posthog", "PostHog").replace("composio", "Composio").replace("mcps", "MCPs")
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
F_SPLIT0, F_SPLIT1 = fo(3.36), fo(63.45)
TRANS = 9
TITLE = white_boxes(["Los 5 conectores más", "potentes de Claude"], 54, chr(0x1F913))
LABEL_IM = {n: white_boxes([t], 60) for n, t in (("P", "1. Perplexity"), ("F", "2. Firecrawl"), ("H", "3. PostHog"), ("W", "4. Playwright"), ("C", "5. Composio"))}
SC = [(3.36, "P"), (17.72, "F"), (28.36, "H"), (41.31, "W"), (51.55, "C")]
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
INTRO = {"P": intro_card("Perplexity", "Conector para Claude", chr(0xf002)),
         "F": intro_card("Firecrawl", "Conector para Claude", chr(0xf06d)),
         "H": intro_card("PostHog", "Conector para Claude", chr(0xf21b)),
         "W": intro_card("Playwright", "Conector para Claude", chr(0xf630)),
         "C": intro_card("Composio", "Conector para Claude", chr(0xf1e6))}

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
# ---- scenes for the 5-connector video ----------------------------------------------
IC = lambda h: chr(h)
def win_card(w=960, h=440): return card(w, h, 26, fill=PAGE)

# 1 · Perplexity --------------------------------------------------------------------
def scene_P(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(4.64):
        s, a, dy = pop(k); paste(im, INTRO["P"], 540, 560 + dy, s, a); return im
    win = win_card(); d = ImageDraw.Draw(win); ox, oy = 30, 30
    msg = "Investiga a fondo el mercado de coches eléctricos"
    bw = F_S.getlength(msg) + 56
    rr(d, (ox + 960 - 24 - bw, oy + 24, ox + 960 - 24, oy + 92), 22, fill=(20, 20, 19))
    d.text((ox + 960 - 24 - bw + 28, oy + 58), msg, font=F_S, fill=TXT, anchor="lm")
    win.alpha_composite(spark(38), (ox + 28, oy + 124))
    t_tool, t_done = T(5.10), T(10.48)
    if f >= t_tool:
        done = f >= t_done
        pill = "Investigación profunda · 48 fuentes" if done else "Buscando con Perplexity"
        pw = F_M.getlength(pill) + 110
        rr(d, (ox + 84, oy + 116, ox + 84 + pw, oy + 172), 28, fill=(48, 47, 45), outline=BORDER, width=2)
        d.text((ox + 118, oy + 144), IC(0xf00c) if done else IC(0xf002), font=fa(24), fill=GREEN if done else BRAND["Perplexity"], anchor="mm")
        d.text((ox + 146, oy + 144), pill, font=F_M, fill=TXT, anchor="lm")
        if not done:
            p = (f - t_tool) / max(1, t_done - t_tool)
            rr(d, (ox + 84, oy + 190, ox + 684, oy + 198), 4, fill=(60, 58, 55))
            rr(d, (ox + 84, oy + 190, ox + 84 + 600 * min(1, p), oy + 198), 4, fill=BRAND["Perplexity"])
    if f >= t_done:
        lines = ["Las ventas crecieron un 38% en 2025, impulsadas", "por el Plan MOVES y la bajada de precios…"]
        shown = int((f - t_done) * 3.2); acc = 0
        for j, ln in enumerate(lines):
            d.text((ox + 86, oy + 210 + j * 46), ln[:max(0, shown - acc)], font=F_S, fill=TXT); acc += len(ln)
    items = [("Cualquier tema", IC(0xf0ac), BRAND["Perplexity"], 12.48), ("En tiempo real", IC(0xf111), (210, 60, 60), 14.56),
             ("Siempre actualizada", IC(0xf00c), (46, 140, 80), 16.40)]
    for q, (lab, ic, col, tt) in enumerate(items):
        if f >= T(tt):
            s, a, dy = pop(f - T(tt)); paste(win, chip(lab, ic, col), ox + 86 + 145 + q * 300, oy + 350 + dy, s * 0.82, a)
    paste(im, win, 540, 548, 0.96, 1)
    return im

# 2 · Firecrawl ---------------------------------------------------------------------
def browser(w, h, url):
    im = card(w, h, 22, fill=(250, 250, 248), border=(210, 210, 210)); d = ImageDraw.Draw(im)
    rr(d, (30, 30, 30 + w, 100), 22, fill=(236, 236, 234)); d.rectangle((30, 70, 30 + w, 100), fill=(236, 236, 234))
    for q, col in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        d.ellipse((58 + q * 30, 56, 76 + q * 30, 74), fill=col)
    rr(d, (170, 48, 30 + w - 30, 84), 18, fill=WHITE)
    d.text((196, 66), IC(0xf023), font=fa(18), fill=(120, 120, 120), anchor="mm"); d.text((216, 66), url, font=F_M, fill=(60, 60, 60), anchor="lm")
    return im
def scene_F(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(19.00):
        s, a, dy = pop(k); paste(im, INTRO["F"], 540, 560 + dy, s, a); return im
    if f < T(23.48):
        b = browser(600, 400, "tienda-ejemplo.com"); d = ImageDraw.Draw(b)
        rr(d, (60, 130, 340, 300), 14, fill=(232, 228, 222)); d.text((200, 215), IC(0xf290), font=fa(70), fill=(200, 160, 120), anchor="mm")
        d.text((370, 140), "Zapatillas Run X", font=font("InterDisplay-Bold.otf", 34), fill=(30, 30, 30))
        d.text((370, 190), "89,90 €", font=font("InterDisplay-Bold.otf", 40), fill=(220, 80, 40))
        for q in range(3): rr(d, (370, 250 + q * 26, 370 + [220, 180, 200][q], 262 + q * 26), 6, fill=(220, 220, 220))
        rr(d, (370, 340, 560, 386), 12, fill=(30, 30, 30)); d.text((465, 363), "Comprar", font=F_M, fill=WHITE, anchor="mm")
        p = ((f - T(19.0)) % 45) / 45; ys = 110 + p * 310
        sw = Image.new("RGBA", b.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sw)
        ds.rectangle((30, ys - 40, 630, ys), fill=BRAND["Firecrawl"] + (40,)); ds.line((30, ys, 630, ys), fill=BRAND["Firecrawl"] + (255,), width=4)
        b.alpha_composite(sw)
        paste(im, b, 362, 550, 0.94, min(1, (f - T(19.0)) / 5 + 0.2))
        if f >= T(21.96):
            j = card(360, 400, 22, fill=(24, 24, 23)); dj = ImageDraw.Draw(j)
            rows = [('{', TXT), ('  "producto":', (156, 220, 254)), ('    "Run X",', (206, 145, 120)), ('  "precio": 89.90,', (156, 220, 254)),
                    ('  "stock": true,', (156, 220, 254)), ('  "fotos": 6', (156, 220, 254)), ('}', TXT)]
            n = int((f - T(21.96)) / 3) + 1
            for q, (row, col) in enumerate(rows[:n]): dj.text((56, 60 + q * 46), row, font=F_MONO, fill=col)
            s, a, dy = pop(f - T(21.96)); paste(im, j, 838, 560 + dy, s * 0.94, a)
        return im
    if f < T(25.48):
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 80), "Recursos de marca extraídos", font=F_H, fill=WHITE)
        cols = [(20, 24, 38), (240, 90, 40), (255, 196, 120), (245, 242, 236)]
        for q, col in enumerate(cols):
            kq = f - T(23.48) - q * 3
            if kq >= 0:
                s = ease_out_back(kq / 7); x = 80 + q * 210
                rr(d, (x, 170, x + int(180 * s), 330), 20, fill=col, outline=(90, 90, 90), width=2)
                if s > 0.9: d.text((x + 10, 350), "#%02X%02X%02X" % col, font=F_MONO, fill=MUTED)
        d.text((80, 410), "Tipografía:", font=F_S, fill=MUTED); d.text((260, 400), "Aa Inter Display", font=font("InterDisplay-Bold.otf", 40), fill=WHITE)
        s, a, dy = pop(f - T(23.48)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    c_ = card(940, 470); d = ImageDraw.Draw(c_)
    d.text((80, 76), "Análisis de competencia", font=F_H, fill=WHITE)
    rows = [("Competidor A", 0.82, "29 €/mes"), ("Competidor B", 0.64, "19 €/mes"), ("Tu marca", 0.48, "24 €/mes")]
    for q, (n_, v, pr) in enumerate(rows):
        kq = f - T(25.48) - q * 4; y = 170 + q * 100
        d.text((80, y + 20), n_, font=F_B, fill=TXT if q < 2 else BRAND["Firecrawl"])
        rr(d, (380, y + 8, 780, y + 40), 16, fill=(60, 58, 55))
        if kq >= 0: rr(d, (380, y + 8, 380 + 400 * v * ease_out_cubic(kq / 12), y + 40), 16, fill=BRAND["Firecrawl"] if q == 2 else (150, 148, 140))
        d.text((800, y + 24), pr, font=F_M, fill=MUTED, anchor="lm")
    if f >= T(27.24):
        rr(d, (640, 432, 900, 480), 24, fill=(60, 40, 30), outline=BRAND["Firecrawl"], width=2)
        it(d, (770, 456), IC(0xf0e7), "al instante", F_M, WHITE, "mm", BRAND["Firecrawl"])
    s, a, dy = pop(f - T(25.48)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im

# 3 · PostHog -----------------------------------------------------------------------
def scene_H(f, f0):
    im = PanelHog = PANEL.copy(); k = f - f0
    if f < T(30.68):
        s, a, dy = pop(k); paste(im, INTRO["H"], 540, 560 + dy, s, a); return im
    if f < T(32.92):   # private detective: sessions being inspected
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        it(d, (80, 104), IC(0xf21b), "Tu detective privado", F_H, WHITE, "lm", BRAND["PostHog"])
        sess = [("Sesión #4821", "Abandona en el pago"), ("Sesión #4822", "Error al enviar formulario"), ("Sesión #4823", "Sale tras 6 s en /precios")]
        for q, (a_, b_) in enumerate(sess):
            y = 170 + q * 92
            rr(d, (80, y, 900, y + 76), 16, fill=(52, 51, 49))
            d.text((110, y + 38), a_, font=F_M, fill=TXT, anchor="lm"); d.text((380, y + 38), b_, font=F_S, fill=MUTED, anchor="lm")
        p = ((f - T(30.68)) % 50) / 50; mx = 140 + p * 720; my = 210 + 92 * ((f - T(30.68)) // 50 % 3)
        d.ellipse((mx - 44, my - 44, mx + 44, my + 44), outline=BRAND["PostHog"], width=7)
        d.line((mx + 30, my + 30, mx + 62, my + 62), fill=BRAND["PostHog"], width=10)
        s, a, dy = pop(f - T(30.68)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    if f < T(33.80):   # bugs
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 76), "Bugs encontrados", font=F_H, fill=WHITE)
        bugs = ["El botón de pago no responde", "Error 404 en /checkout", "Formulario lento en móvil"]
        for q, b_ in enumerate(bugs):
            kq = f - T(32.92) - q * 4
            if kq < 0: continue
            y = 170 + q * 92
            rr(d, (80, y, 900, y + 76), 16, fill=(70, 34, 34), outline=(200, 70, 70), width=2)
            d.text((120, y + 38), IC(0xf188), font=fa(30), fill=(240, 100, 100), anchor="mm")
            d.text((160, y + 38), b_, font=F_B, fill=WHITE, anchor="lm")
        s, a, dy = pop(f - T(32.92)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    if f < T(35.48):   # funnel: where you lose customers
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 76), "Dónde pierdes clientes", font=F_H, fill=WHITE)
        st = [("Visitas", 1.0), ("Producto", 0.62), ("Carrito", 0.31), ("Pago", 0.09)]
        for q, (n_, v) in enumerate(st):
            kq = f - T(33.80) - q * 3; y = 165 + q * 72
            d.text((80, y + 26), n_, font=F_B, fill=TXT, anchor="lm")
            if kq >= 0:
                wv = 520 * v * ease_out_cubic(kq / 10)
                rr(d, (260, y + 6, 260 + max(20, wv), y + 48), 12, fill=(220, 60, 60) if q == 3 else BRAND["PostHog"])
                d.text((800, y + 26), f"{int(v * 100)}%", font=F_B, fill=(240, 100, 100) if q == 3 else TXT, anchor="lm")
        s, a, dy = pop(f - T(33.80)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    if f < T(38.03):   # automatic improvements
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 76), "Mejoras automáticas", font=F_H, fill=WHITE)
        fx = ["Botón de pago corregido", "Página /checkout restaurada", "Formulario 3× más rápido"]
        for q, t_ in enumerate(fx):
            on = f >= T(35.48) + 6 + q * 8; y = 170 + q * 88
            d.ellipse((80, y + 6, 128, y + 54), fill=(46, 160, 90) if on else (70, 68, 64))
            if on: d.text((104, y + 30), IC(0xf00c), font=fa(24), fill=WHITE, anchor="mm")
            d.text((150, y + 30), t_, font=F_B, fill=TXT if on else MUTED, anchor="lm")
        s, a, dy = pop(f - T(35.48)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    c_ = card(940, 470); d = ImageDraw.Draw(c_)   # full audit, free
    d.text((80, 76), "Auditoría completa", font=F_H, fill=WHITE)
    p = ease_out_cubic((f - T(38.03)) / 24); cx, cy, r = 250, 290, 110
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(60, 58, 55), width=22)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * 0.92 * p, fill=(46, 160, 90), width=22)
    d.text((cx, cy), str(int(92 * p)), font=font("InterDisplay-Black.otf", 80), fill=WHITE, anchor="mm")
    for q, t_ in enumerate(["Rendimiento", "Conversión", "Errores"]):
        it(d, (460, 200 + q * 60), IC(0xf00c), t_, F_B, TXT, "lm", (90, 210, 130))
    if f >= T(40.51):
        rr(d, (460, 380, 760, 440), 30, fill=(30, 70, 45), outline=(46, 160, 90), width=3)
        d.text((610, 410), "100% gratis", font=F_B, fill=WHITE, anchor="mm")
    s, a, dy = pop(f - T(38.03)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im

# 4 · Playwright --------------------------------------------------------------------
def scene_W(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(42.91):
        s, a, dy = pop(k); paste(im, INTRO["W"], 540, 560 + dy, s, a); return im
    if f < T(47.55):
        b = browser(900, 470, "mi-sitio.com/contacto"); d = ImageDraw.Draw(b)
        d.text((90, 140), "Contacto", font=font("InterDisplay-Bold.otf", 44), fill=(30, 30, 30))
        fields = [("Nombre", "Laura Gómez"), ("Email", "laura@empresa.com")]
        t_fill = T(44.43)
        for q, (lab, val) in enumerate(fields):
            y = 210 + q * 100
            d.text((90, y), lab, font=F_M, fill=(90, 90, 90))
            on = f >= t_fill + q * 14
            rr(d, (90, y + 36, 610, y + 84), 12, fill=WHITE, outline=(46, 160, 90) if on else (200, 200, 200), width=3)
            if on: d.text((108, y + 60), val[:int((f - t_fill - q * 14) * 1.4)], font=F_S, fill=(30, 30, 30), anchor="lm")
        clicked = f >= T(46.75) + 10
        rr(d, (660, 386, 880, 440), 14, fill=(30, 120, 70) if clicked else (46, 160, 90)); d.text((770, 413), "Enviado ✓" if clicked else "Enviar", font=F_B, fill=WHITE, anchor="mm")
        path = [(700, 160), (350, 270), (350, 370), (770, 413)]
        tt = [T(42.91), T(44.20), T(44.43) + 14, T(46.75) + 6]
        cx, cy = path[0]
        for q in range(len(tt) - 1):
            if tt[q] <= f < tt[q + 1]:
                u = ease_io((f - tt[q]) / max(1, tt[q + 1] - tt[q])); cx = path[q][0] + (path[q + 1][0] - path[q][0]) * u; cy = path[q][1] + (path[q + 1][1] - path[q][1]) * u
            elif f >= tt[q + 1]: cx, cy = path[q + 1]
        if T(46.75) + 6 <= f < T(46.75) + 16:   # click ripple
            rr_ = (f - T(46.75) - 6) * 6; d.ellipse((cx - rr_, cy - rr_, cx + rr_, cy + rr_), outline=(46, 160, 90), width=4)
        d.text((cx + 30, cy + 30), IC(0xf245), font=fa(52), fill=(20, 20, 20), stroke_width=3, stroke_fill=WHITE)
        tag = Image.new("RGBA", (360, 56), (0, 0, 0, 0)); dt = ImageDraw.Draw(tag)
        rr(dt, (0, 0, 359, 55), 28, fill=(46, 160, 90)); dt.text((180, 28), "Claude controla el navegador", font=font("Inter-SemiBold.otf", 24), fill=WHITE, anchor="mm")
        b.alpha_composite(tag, (int(min(560, cx + 60)), int(min(cy + 50, 440))))
        paste(im, b, 540, 550, 0.94, min(1, (f - T(42.91)) / 5 + 0.2)); return im
    c_ = card(940, 470); d = ImageDraw.Draw(c_)
    d.text((80, 76), "Herramientas sin conexión con IA", font=F_H, fill=WHITE)
    tools = [(IC(0xf1c3), "Excel web"), (IC(0xf0e0), "Correo"), (IC(0xf073), "Calendario"), (IC(0xf1ad), "Tu CRM")]
    for q, (ic, nm) in enumerate(tools):
        kq = f - T(47.55) - q * 4
        if kq >= 0:
            s = ease_out_back(kq / 7); x = 80 + q * 210
            rr(d, (x, 170, x + 180, 350), 22, fill=(52, 51, 49), outline=BORDER, width=2)
            d.text((x + 90, 235), ic, font=fa(max(8, int(60 * min(1, s)))), fill=(46, 160, 90), anchor="mm")
            d.text((x + 90, 310), nm, font=F_M, fill=TXT, anchor="mm")
    if f >= T(50.59):
        rr(d, (80, 385, 520, 445), 30, fill=(30, 70, 45), outline=(46, 160, 90), width=3)
        it(d, (300, 415), IC(0xf0c1), "Conexión directa", F_B, WHITE, "mm")
    s, a, dy = pop(f - T(47.55)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im

# 5 · Composio ----------------------------------------------------------------------
APPS = [(IC(0xf0e0), "Correo"), (IC(0xf073), "Calendario"), (IC(0xf15c), "Docs"), (IC(0xf1ad), "CRM"), (IC(0xf086), "Chat"), (IC(0xf0ae), "Tareas")]
def scene_C(f, f0):
    im = PANEL.copy(); k = f - f0
    if f < T(52.91):
        s, a, dy = pop(k); paste(im, INTRO["C"], 540, 560 + dy, s, a); return im
    if f < T(56.43):   # hub: all apps at once
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        cx, cy = 500, 260
        p = ease_out_cubic((f - T(53.63)) / 14) if f >= T(53.63) else 0
        for q, (ic, nm) in enumerate(APPS):
            ang = -math.pi / 2 + q * 2 * math.pi / 6; x = cx + 330 * math.cos(ang); y = cy + 170 * math.sin(ang)
            if p > 0: d.line((cx, cy, cx + (x - cx) * p, cy + (y - cy) * p), fill=BRAND["Composio"], width=5)
            rr(d, (x - 62, y - 42, x + 62, y + 42), 18, fill=(52, 51, 49), outline=BRAND["Composio"] if p >= 1 else BORDER, width=3)
            d.text((x, y - 10), ic, font=fa(30), fill=WHITE, anchor="mm"); d.text((x, y + 24), nm, font=font("Inter-Medium.otf", 22), fill=TXT, anchor="mm")
        d.ellipse((cx - 62, cy - 62, cx + 62, cy + 62), fill=(44, 43, 41), outline=ORANGE, width=4)
        sp = spark(70); c_.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))
        if f >= T(55.79):
            rr(d, (cx - 150, 430, cx + 150, 480), 25, fill=BRAND["Composio"]); d.text((cx, 455), "Todas a la vez", font=F_M, fill=WHITE, anchor="mm")
        s, a, dy = pop(f - T(52.91)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    if f < T(59.23):   # one by one vs all at once
        c_ = card(940, 470); d = ImageDraw.Draw(c_)
        d.text((80, 76), "Sin Composio vs. con Composio", font=F_H, fill=WHITE)
        rr(d, (80, 160, 470, 440), 20, fill=(60, 36, 36), outline=(200, 70, 70), width=2)
        d.text((275, 200), "Una por una", font=F_B, fill=WHITE, anchor="mm")
        for q in range(4):
            on = f >= T(56.43) + q * 12
            it(d, (130, 255 + q * 44), IC(0xf017), "conectar app " + str(q + 1), F_S, (240, 160, 160)) if on else None
        rr(d, (500, 160, 890, 440), 20, fill=(30, 60, 42), outline=(46, 160, 90), width=2)
        d.text((695, 200), "Todas a la vez", font=F_B, fill=WHITE, anchor="mm")
        if f >= T(57.95):
            d.text((695, 320), IC(0xf00c), font=fa(90), fill=(90, 210, 130), anchor="mm")
            d.text((695, 400), "1 sola conexión", font=F_M, fill=TXT, anchor="mm")
        s, a, dy = pop(f - T(56.43)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
    c_ = card(940, 470); d = ImageDraw.Draw(c_)   # MCP aggregator
    d.text((80, 76), "Agregador de MCPs y conectores", font=F_H, fill=WHITE)
    names = ["Gmail MCP", "Drive MCP", "Slack MCP", "Notion MCP", "GitHub MCP", "+250 más"]
    p = ease_io((f - T(60.40)) / 30) if f >= T(60.40) else 0
    for q, n_ in enumerate(names):
        x0 = 80 + (q % 3) * 270; y0 = 160 + (q // 3) * 80
        x = x0 + (330 - x0) * p * 0.0; y = y0
        rr(d, (x, y, x + 240, y + 62), 16, fill=(52, 51, 49), outline=BORDER, width=2)
        d.text((x + 120, y + 31), n_, font=F_M, fill=TXT, anchor="mm")
    if f >= T(61.79):
        rr(d, (80, 350, 900, 440), 24, fill=BRAND["Composio"])
        it(d, (490, 395), IC(0xf0e7), "Habilidades extremas para Claude", F_B, WHITE, "mm")
    s, a, dy = pop(f - T(59.23)); paste(im, c_, 540, 550 + dy, s * 0.94, a); return im
SCENE_FN = {"P": scene_P, "F": scene_F, "H": scene_H, "W": scene_W, "C": scene_C}

def top_panel(f):
    f0, n = scene_at(f)
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
    for t in (4.64, 12.48, 14.56, 16.40, 19.00, 21.96, 23.48, 25.48, 30.68, 32.92, 33.80, 35.48, 38.03, 42.91, 47.55, 52.91, 56.43, 59.23):
        ev.append(("pluck", T(t) / FPS))
    ev.append(("boom", KEY["f0"] / FPS))
    return ev

TAGS = []
for k, c in enumerate(chunks):
    if c["hl"] and not c["key"]:
        n = {"perplexity": "P", "firecrawl": "F", "posthog": "H", "playwright": "W", "composio": "C"}[c["txt"].lower()]
        if any(t_[3] == n for t_ in TAGS): continue
        st = chunks[k - 1] if k and chunks[k - 1]["txt"].startswith("número") else c
        TAGS.append((st["f0"], c["f1"] + 6, LABEL_IM[n], n))
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
