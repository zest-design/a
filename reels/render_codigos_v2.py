import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p8"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/86889b7c-44.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255); INK = (14, 14, 16)
PAGE = (31, 30, 29); CB_BG = (44, 43, 41); CB_BORDER = (70, 69, 66); CB_TEXT = (236, 235, 228)
CB_MUTED = (156, 154, 146); CB_CHIP = (66, 65, 62); CB_GROUP = (52, 51, 49); BUBBLE = (20, 20, 19)
CLAUDE_ORANGE = (217, 119, 87)
FD = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(FD + n, int(s))
def serif(s): return ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf", int(s))
def fa(s): return ImageFont.truetype(f"{S}/fa/fa-solid.ttf", int(s))
POP = f"{S}/poppins/Poppins-800.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SPARK = Image.open(f"{S}/p3/spark.png").convert("RGBA")
def spark(h): return SPARK.resize((int(SPARK.width * h / SPARK.height), int(h)), Image.LANCZOS)

# ---------------- cuts -------------------------------------------------------------
SIL = [(0.00, 0.19), (2.25, 2.40), (2.91, 3.04), (4.41, 4.53), (7.69, 7.89), (8.95, 9.25), (9.91, 10.03),
       (15.89, 16.14), (16.19, 16.54), (17.15, 17.34), (19.75, 19.88), (22.75, 23.05), (25.59, 25.89),
       (26.30, 26.60), (27.34, 27.57), (33.22, 33.54), (34.51, 34.73), (35.11, 35.51), (36.20, 36.45),
       (39.16, 39.30), (42.33, 42.57)]
END = 48.05; PAD = 0.04
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

# ---------------- words / captions --------------------------------------------------
PK = json.load(open(f"{P}/wordsA.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (0.00, 2.30, "Aquí tienes cinco códigos secretos para Claude."),
    (2.48, 8.95, "Número cinco: /godmode. Ponlo antes de tu prompt y desbloqueará el estilo de respuesta más agresivo y completo de Claude."),
    (9.20, 15.95, "Número cuatro: L99. Ponlo al final de tu prompt y Claude responderá al nivel experto más avanzado posible."),
    (16.30, 26.10, "Número tres: OODA. Ponlo antes de tu prompt y Claude aplicará un marco de toma de decisiones militar a tu problema y luego te dirá exactamente cómo resolverlo."),
    (26.46, 35.14, "Número dos: ARTIFACTS. Ponlo después de tu prompt y Claude te construirá una app, un juego o un dashboard funcional que irá dentro del chat."),
    (35.46, 42.40, "Número uno: /ghost. Ponlo antes de tu prompt y obtendrás una respuesta totalmente humanizada que pasará cualquier detector de IA."),
    (42.50, 48.00, "Si quieres más de 100 comandos secretos de Claude, comenta aquí abajo 21, que te los haré llegar."),
]
FIX = {(16.30, 26.10): [("Número", 16.30), ("tres:", 16.86), ("OODA.", 17.34), ("Ponlo", 18.46), ("antes", 18.86)]}
def align(s0, s1, text):
    ws = text.split()
    pk = [(w, t) for w, t, _ in PK if s0 - 0.3 <= t <= s1 + 0.1]
    a = [norm(w) for w in ws]; b = [norm(w) for w, _ in pk]
    times = [None] * len(ws)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1): times[i1 + k] = pk[j1 + k][1]
    for k, (w, t) in enumerate(FIX.get((s0, s1), [])): times[k] = t
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
HL = [["godmode"], ["l99"], ["ooda"], ["artifacts"], ["ghost"], ["21"]]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(WORDS):
    hit = next((p for p in HL if [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
    if hit: g = WORDS[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [WORDS[i]]; i += 1; hl = False
        while i < len(WORDS) and len(g) < 3 and not PUNCT.search(g[-1][0]) and not g[-1][2]:
            if WORDS[i][1] - g[0][1] > 0.8 or sum(len(w[0]) for w in g) + len(WORDS[i][0]) > 16: break
            if any([norm(w[0]) for w in WORDS[i:i + len(p)]] == p for p in HL): break
            g.append(WORDS[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w[0] for w in g))
    if not hl: txt = txt.lower().replace("claude", "Claude").replace(" ia", " IA")
    end = g[-1][3] + 0.25 if g[-1][2] else None
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1], end=end, key=(txt == "21")))
for k, c in enumerate(chunks):
    if k and chunks[k - 1]["key"]: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.0)
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else 99
    if c["key"]: nxt = max(nxt, c["t0"] + 1.0)
    c["t1"] = min(nxt, c["end"] or nxt, c["t0"] + 1.6)
    c["f0"], c["f1"] = fo(c["t0"]), fo(c["t1"])
FC = font("InterDisplay-Bold.otf", 62); FK = font("InterDisplay-Black.otf", 150)
def make_caption(txt, hl, key):
    f = FK if key else FC
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 24, 12
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 24, w - 20, h - 16), 16, fill=(0, 0, 0, 110))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, w - 20, h - 20), 16, fill=RED)
    else:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=f, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=f, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"], c["key"])
CAP_X, CAP_Y = 500, 1420
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
def emoji(ch, h):
    ef = ImageFont.truetype(EMOJI, 109)
    e = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); ImageDraw.Draw(e).text((75, 75), ch, font=ef, embedded_color=True, anchor="mm")
    e = e.crop(e.getbbox()); return e.resize((int(e.width * h / e.height), int(h)), Image.LANCZOS)

# Instagram-style white text boxes (same look as the Humano title)
def white_boxes(lines, size=52, em=None):
    ft = ImageFont.truetype(POP, size); pad, pitch, r = 30, int(size * 1.5), 12
    e = emoji(em, size * 1.05) if em else None
    ws = [ft.getlength(l) + 2 * pad + ((e.width + 16) if (e and k == len(lines) - 1) else 0) for k, l in enumerate(lines)]
    Wd, Hd = int(max(ws)) + 4, pitch * len(lines) + 8
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = Wd / 2
    for k, (l, w) in enumerate(zip(lines, ws)):
        y0 = 2 + k * pitch
        d.rounded_rectangle((cx - w / 2, y0 - (2 if k else 0), cx + w / 2, y0 + pitch + 2), r, fill=WHITE)
    for k, (l, w) in enumerate(zip(lines, ws)):
        yc = 2 + k * pitch + pitch / 2 + 3; x0 = cx - w / 2 + pad
        d.text((x0, yc), l, font=ft, fill=(0, 0, 0), anchor="lm")
        if e and k == len(lines) - 1: im.alpha_composite(e, (int(x0 + ft.getlength(l) + 16), int(yc - e.height / 2 - 1)))
    return im
TITLE = white_boxes(["Códigos secretos", "para Claude"], 54, "\U0001F913")
LABELS = [(2.48, 4.40, "5. /godmode"), (9.20, 10.95, "4. L99"), (16.30, 18.40, "3. OODA"),
          (26.46, 28.25, "2. ARTIFACTS"), (35.46, 37.00, "1. /ghost")]
LABELS = [(fo(a), fo(b), white_boxes([t], 74)) for a, b, t in LABELS]
CTA = white_boxes(["Comenta “21”"], 56, "\U0001F447")
F_CTA = fo(45.14)

# ---------------- Claude chat inserts (dark mode, Spanish UI) ----------------------
SS = 2
VX, VY, VW, VH, VR = 60, 236, 960, 1070, 34       # chat window on screen (inside IG margins)
CH_W = 960                                        # scene width (1x)
CHATS = [  # (src start, src end, prompt, code, code position, response)
    (4.40, 9.10, "/godmode Crea una estrategia de marketing para lanzar mi tienda online", "/godmode",
     "Perfecto. Aquí tienes la estrategia completa, sin rodeos:\n1. Define tu cliente ideal y su mayor dolor.\n2. Lanza con una oferta irresistible de 72 h.\n3. Contenido diario en Reels y TikTok…"),
    (10.95, 16.20, "Explícame cómo afecta la inflación a mis ahorros L99", "L99",
     "Análisis a nivel experto: la inflación erosiona el poder adquisitivo real de tu capital. Si tu dinero rinde menos que el IPC, pierdes valor cada mes. Estrategias de cobertura…"),
    (18.40, 26.30, "OODA Mis ventas bajaron un 30% este mes, ¿qué hago?", "OODA",
     "OBSERVAR: caída del 30% concentrada en clientes recurrentes.\nORIENTAR: el problema es retención, no captación.\nDECIDIR: campaña de reactivación + encuesta.\nACTUAR: lanza hoy un email con…"),
    (28.25, 35.30, "Haz un dashboard interactivo de mis gastos mensuales ARTIFACTS", "ARTIFACTS",
     "¡Listo! Aquí tienes tu dashboard interactivo de gastos:"),
    (37.00, 42.45, "/ghost Escribe un post de LinkedIn sobre mi nuevo trabajo", "/ghost",
     "Hoy empiezo una nueva etapa y, sinceramente, todavía no me lo creo. Hace un año ni me imaginaba aquí…"),
]
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
class Chat:
    def __init__(s, a, b, prompt, code, resp):
        s.f0, s.f1 = fo(a), fo(b)
        dur = s.f1 - s.f0
        s.t0 = s.f0 + 8; s.t1 = s.f0 + int(dur * 0.50); s.fsend = s.t1 + 6; s.fconv = s.fsend + 8
        s.prompt, s.code, s.resp = prompt, code, resp
        s.ci = prompt.index(code); s.cj = s.ci + len(code)
        s.plines = wrap(prompt, FT, (CH_W - 2 * 70) * SS)
        s.rlines = wrap(resp, FR, (CH_W - 150) * SS)
CH = [Chat(a, b, p, c, r) for a, b, p, c, r in CHATS]

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

SCN_H = 1300
def draw_chat(c, f):
    sc = Image.new("RGBA", (CH_W * SS, SCN_H * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    if f < c.fconv:   # home screen: greeting + input being typed
        n = 0 if f < c.t0 else min(len(c.prompt), int(round(len(c.prompt) * (f - c.t0 + 1) / max(1, c.t1 - c.t0))))
        sp = spark(50 * SS); g = "Buenas tardes"; gf = serif(56 * SS)
        gw = sp.width + 20 * SS + gf.getlength(g); gx = (CH_W * SS - gw) / 2; gy = 470 * SS
        sc.alpha_composite(sp, (int(gx), int(gy - sp.height / 2)))
        d.text((gx + sp.width + 20 * SS, gy), g, font=gf, fill=(232, 230, 222), anchor="lm")
        send_p = (f - c.fsend) / 6 if f >= c.fsend else 0
        cur, bot = draw_input(d, sc, 30, CH_W - 30, 540 * SS, c.prompt, n, (c.ci, c.cj),
                              "¿En qué puedo ayudarte hoy?", f < c.fsend, send_p)
        return sc, ("type" if c.t0 - 4 <= f < c.fsend else "home"), cur, bot
    # conversation: user bubble + streaming answer
    k = f - c.fconv
    bl = wrap(c.prompt, FT, 640 * SS); bw = max(FT.getlength(x) for x in bl) + 56 * SS
    bh = len(bl) * LH * SS + 40 * SS; bx1 = (CH_W - 30) * SS; bx0 = bx1 - bw; by0 = 120 * SS
    d.rounded_rectangle((bx0, by0, bx1, by0 + bh), 22 * SS, fill=BUBBLE)
    pos = 0
    for j, ln in enumerate(bl):
        y = by0 + 20 * SS + j * LH * SS; d.text((bx0 + 28 * SS, y), ln, font=FT, fill=CB_TEXT)
        if pos <= c.ci < pos + len(ln) + 1:
            a = c.ci - pos; xa = bx0 + 28 * SS + FT.getlength(ln[:a]); xb = bx0 + 28 * SS + FT.getlength(ln[:a + len(c.code)])
            d.rounded_rectangle((xa - 8 * SS, y - 4 * SS, xb + 8 * SS, y + 42 * SS), 8 * SS, outline=(235, 64, 52), width=3 * SS)
        pos += len(ln) + 1
    ry = by0 + bh + 60 * SS
    sp = spark(40 * SS); sc.alpha_composite(sp, (int(40 * SS), int(ry)))
    total = sum(len(x) for x in c.rlines); shown = int(min(total, (k + 1) * 4.2)); acc = 0
    for j, ln in enumerate(c.rlines):
        if acc >= shown: break
        part = ln[:max(0, shown - acc)]
        d.text((100 * SS, ry + j * 50 * SS), part, font=FR, fill=(226, 224, 216)); acc += len(ln)
    yend = ry + len(c.rlines) * 50 * SS
    if c.code == "ARTIFACTS" and shown >= total:   # live dashboard artifact
        ka = k - c.rlines.__len__() * 0; pa = ease_out_cubic((shown and (k - int(total / 4.2))) / 10)
        ax0, ay0, ax1, ay1 = 40 * SS, yend + 20 * SS, (CH_W - 40) * SS, yend + 420 * SS
        d.rounded_rectangle((ax0, ay0, ax1, ay1), 20 * SS, fill=(38, 37, 35), outline=CB_BORDER, width=2 * SS)
        d.text((ax0 + 30 * SS, ay0 + 26 * SS), "Gastos mensuales", font=font("Inter-SemiBold.otf", 30 * SS), fill=CB_TEXT)
        vals = [0.55, 0.8, 0.45, 0.95, 0.65, 0.75]; labs = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
        for q, (v, lb) in enumerate(zip(vals, labs)):
            bxa = ax0 + (60 + q * 135) * SS; hgt = v * 250 * SS * pa
            d.rounded_rectangle((bxa, ay1 - 50 * SS - hgt, bxa + 80 * SS, ay1 - 50 * SS), 10 * SS, fill=CLAUDE_ORANGE if q == 3 else (120, 118, 112))
            d.text((bxa + 40 * SS, ay1 - 24 * SS), lb, font=F_UI2, fill=CB_MUTED, anchor="mm")
    if c.code == "/ghost" and shown >= total:      # AI-detector result
        pa = ease_out_back(min(1, (k - int(total / 4.2)) / 9))
        if pa > 0:
            card = Image.new("RGBA", (560 * SS, 150 * SS), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
            dc.rounded_rectangle((0, 0, 560 * SS - 1, 150 * SS - 1), 22 * SS, fill=(30, 60, 40), outline=(70, 190, 110), width=3 * SS)
            dc.text((52 * SS, 75 * SS), "", font=fa(56 * SS), fill=(90, 210, 130), anchor="mm")
            dc.text((104 * SS, 40 * SS), "Detector de IA", font=F_UI2, fill=(190, 230, 200))
            dc.text((104 * SS, 72 * SS), "99,9% humano", font=font("InterDisplay-Bold.otf", 46 * SS), fill=WHITE)
            card = card.resize((max(1, int(card.width * pa)), max(1, int(card.height * pa))), Image.BICUBIC)
            sc.alpha_composite(card, (int(CH_W * SS / 2 - card.width / 2), int(yend + 60 * SS)))
    # reply box at the bottom
    draw_input(d, sc, 30, CH_W - 30, (SCN_H - 200) * SS, "", 0, (0, 0), "Responder…", False, 0)
    return sc, "conv", None, None

class Cam: pass
cam = Cam(); cam.x = None; cam.tx = None
def chat_view(c, f):
    sc, mode, cur, bot = draw_chat(c, f)
    if mode == "type":
        z = 1.5
        left, right = 30 + VW / 2 / z - 10, CH_W - 30 - VW / 2 / z + 10
        if cam.tx is None: cam.tx = left
        if cur[0] > cam.tx + VW / 2 / z - 60: cam.tx = right
        elif cur[0] < cam.tx - VW / 2 / z + 60: cam.tx = left
        tx, ty, tz = cam.tx, cur[1] + 40, z
    elif mode == "home":
        cam.tx = None; tx, ty, tz = CH_W / 2, 600, 1.0
    else:
        cam.tx = None; tx, ty, tz = CH_W / 2, VH / 2 + 20, 1.0
    if cam.x is None or f == c.f0: cam.x, cam.y, cam.z = tx, ty, tz
    px, py, pz = cam.x, cam.y, cam.z; k = 0.22
    cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k; cam.z += (tz - cam.z) * k
    mv = math.hypot((cam.x - px) * cam.z, (cam.y - py) * cam.z) + abs(cam.z - pz) * 600
    def sample(x, y, z):
        a = 1 / z; x0 = x - VW / 2 * a; y0 = y - VH / 2 * a
        return sc.transform((VW, VH), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=PAGE + (255,))
    ns = 1 if mv < 6 else min(7, 2 + int(mv / 9))
    if ns == 1: return sample(cam.x, cam.y, cam.z)
    acc = None
    for q in range(ns):
        u = q / (ns - 1); s_ = np.asarray(sample(px + (cam.x - px) * u, py + (cam.y - py) * u, pz + (cam.z - pz) * u), np.float32)
        acc = s_ if acc is None else acc + s_
    return Image.fromarray((acc / ns).astype(np.uint8)).convert("RGBA")

# insert background: warm dark gradient (Claude-like) + rounded chat window
yy, xx = np.mgrid[0:H, 0:W]
bg = np.zeros((H, W, 3), np.float32) + np.array([24, 22, 21], np.float32)
glow = np.exp(-(((xx - 200) / 700.0) ** 2 + ((yy - 300) / 700.0) ** 2))[..., None]
glow2 = np.exp(-(((xx - 980) / 600.0) ** 2 + ((yy - 1750) / 600.0) ** 2))[..., None]
bg = bg * (1 - 0.35 * glow - 0.25 * glow2) + np.array(CLAUDE_ORANGE, np.float32) * (0.35 * glow + 0.25 * glow2)
INSERT_BG = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
_sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(_sh).rounded_rectangle((VX, VY + 16, VX + VW, VY + VH + 16), VR, fill=(0, 0, 0, 150))
INSERT_BG.alpha_composite(_sh.filter(ImageFilter.GaussianBlur(26)))
VMASK = Image.new("L", (VW, VH), 0); ImageDraw.Draw(VMASK).rounded_rectangle((0, 0, VW - 1, VH - 1), VR, fill=255)
def insert_frame(c, f):
    canvas = INSERT_BG.copy()
    v = chat_view(c, f)
    k = f - c.f0; left = c.f1 - f
    e = ease_out_cubic(min(k, left) / 7)
    win = Image.new("RGBA", (VW, VH), (0, 0, 0, 0)); win.paste(v, (0, 0), VMASK)
    paste(canvas, win, VX + VW / 2, VY + VH / 2 + (1 - e) * 80, 0.94 + 0.06 * e, min(1, 0.2 + e))
    return canvas

# ---------------- audio: voice + light sound design ---------------------------------
SR = 48000
def sfx(events):
    rng = np.random.default_rng(5); trk = np.zeros(int((TOTAL + 1) * SR))
    def add(sig, t):
        s = int(t * SR); e = min(len(trk), s + len(sig)); trk[s:e] += sig[:e - s]
    n = int(0.42 * SR); t = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n); y = 0.0
    for k in range(n):
        cc = 0.02 + 0.2 * math.sin(math.pi * k / n) ** 2; y += cc * (noise[k] - y); out[k] = y
    whoosh = out / np.abs(out).max() * np.sin(np.pi * t / 0.42) ** 1.8 * 0.16
    n2 = int(0.09 * SR); t2 = np.arange(n2) / SR
    tick = np.sin(2 * np.pi * 1320 * t2) * np.exp(-t2 * 70) * 0.07 + np.sin(2 * np.pi * 1980 * t2) * np.exp(-t2 * 90) * 0.03
    send = np.sin(2 * np.pi * np.cumsum(700 * np.exp(-t2 * 30) + 400) / SR) * np.exp(-t2 * 40) * 0.12
    n3 = int(0.016 * SR); t3 = np.arange(n3) / SR
    n4 = int(1.4 * SR); t4 = np.arange(n4) / SR
    boom = (np.sin(2 * np.pi * (55 + 30 * np.exp(-t4 * 8)) * t4) * np.exp(-t4 * 3.2) * 0.32 +
            rng.standard_normal(n4) * np.exp(-t4 * 18) * 0.05)
    shimmer = sum(np.sin(2 * np.pi * fq * t4) for fq in (1760, 2217, 2637)) * np.exp(-t4 * 2.5) * 0.018
    for kind, tt in events:
        if kind == "whoosh": add(whoosh, max(0, tt - 0.18))
        elif kind == "tick": add(tick, tt)
        elif kind == "send": add(send, tt)
        elif kind == "key": add(np.convolve(rng.standard_normal(n3) * np.exp(-t3 * 400) * rng.uniform(0.025, 0.045), [0.5, 0.5], "same"), tt)
        elif kind == "boom": add(boom + shimmer, tt)
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
    ev = []
    for c in CH:
        ev += [("whoosh", c.f0 / FPS), ("whoosh", c.f1 / FPS)]
        prev = 0
        for f in range(c.t0, c.t1 + 1):
            n = min(len(c.prompt), int(round(len(c.prompt) * (f - c.t0 + 1) / max(1, c.t1 - c.t0))))
            for q in range(prev, n):
                if c.prompt[q] != " " and q % 2 == 0: ev.append(("key", f / FPS + (q - prev) / max(1, n - prev) / FPS))
            prev = n
    ev += [("tick", a / FPS) for a, _, _ in LABELS] + [("tick", 0.05), ("tick", F_CTA / FPS)]
    kc = next(c for c in chunks if c["key"]); ev.append(("boom", kc["f0"] / FPS))
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
        guy = gp.stdout.read(W * H * 3)
        c = next((c for c in CH if c.f0 <= f < c.f1), None)
        if want is not None and not any(0 <= w - f < 12 for w in want):
            if f > max(want): break
            continue
        if c is not None:
            canvas = insert_frame(c, f)
        else:
            canvas = Image.frombuffer("RGB", (W, H), guy).convert("RGBA")
            if f < fo(2.40): canvas.alpha_composite(TITLE, (int(540 - TITLE.width / 2), 290))
            for a, b, im in LABELS:
                if a <= f < b: canvas.alpha_composite(im, (int(540 - im.width / 2), 300))
            if F_CTA <= f < KEY["f0"]: canvas.alpha_composite(CTA, (int(540 - CTA.width / 2), 300))
        if f >= KEY["f0"]:   # the comment keyword: big, at the top, nothing else on screen while it lands
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.035 * math.sin(k / FPS * 2 * math.pi * 1.6))
            paste(canvas, KEY["im"], 540, 400, sc, min(1, 0.35 + k / 3))
        for ch in chunks:
            if ch["key"] or not (ch["f0"] <= f < ch["f1"]): continue
            if KEY["f0"] <= f < KEY["f1"]: continue
            k = f - ch["f0"]
            sc = 0.86 + 0.14 * ease_out_back(k / 5)
            paste(canvas, ch["im"], CAP_X, CAP_Y + (1 - ease_out_cubic(k / 5)) * 8, sc, min(1, 0.35 + k / 3))
        if want is not None and f not in want: continue
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), file=sys.stderr)
    main()
