import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p13"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/30adc34f-49.mp4"
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
SIL = [(0.00, 0.26), (2.46, 2.63), (4.33, 4.46), (4.84, 5.04), (8.25, 8.53), (11.98, 12.11), (12.48, 12.71), (12.74, 12.94),
       (14.29, 14.47), (14.78, 14.91), (15.42, 15.81), (16.50, 16.62), (17.16, 17.39), (18.73, 18.88), (20.83, 21.09), (21.12, 21.42),
       (21.55, 21.70), (26.36, 26.65), (28.03, 28.21), (29.08, 29.43), (31.25, 31.40), (31.54, 31.66), (32.82, 33.29), (33.63, 33.83),
       (33.85, 34.02), (36.91, 37.40), (38.45, 38.58), (39.97, 40.22), (41.18, 41.35), (43.27, 43.39), (44.21, 44.43), (44.46, 44.68),
       (48.74, 48.89)]
END = 49.97; PAD = 0.04
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
    (0.26, 4.84, "Si Claude te sigue dando malas respuestas, tienes que hacer que 100 versiones de Claude luchen a muerte."),
    (5.04, 8.25, "Esta habilidad se llama Arena Skill y es completamente gratis."),
    (8.40, 12.48, "La tienes que usar siempre que no estés satisfecho con la respuesta que Claude te devuelve."),
    (12.71, 15.42, "En lugar de preguntarle a Claude una y otra vez,"),
    (15.76, 20.83, "la Arena Skill crea 100 subagentes y le da a cada uno exactamente la misma tarea."),
    (21.09, 28.03, "Pero cada uno elabora de forma diferente, con distintos razonamientos, distintos flujos de trabajo, distintas estrategias."),
    (28.10, 33.29, "Luego compiten, se critican, se atacan entre ellos hasta llegar a una solución fuerte."),
    (33.70, 39.97, "Así, en lugar de perder el tiempo repitiendo una y otra vez los prompts con Claude, obtienes siempre la mejor respuesta."),
    (40.22, 44.21, "Para configurarlo, pega este enlace y luego escribe Install_the_skill."),
    (44.43, 49.95, "Si quieres la configuración completa, he preparado para ti un contenido con el paso a paso completo. Comenta ARENA y te lo hago llegar."),
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
HL = [["arena", "skill"], ["gratis"], ["100"], ["ARENA"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("ARENA"): return ["ARENA"]
    return next((p for p in HL if p != ["ARENA"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "ARENA"
    if not hl: txt = txt.lower().replace("claude", "Claude").replace("install_the_skill", "Install the skill")
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
SHIFT = 450                  # bottom panel shows his face centred
CAP_SPLIT, CAP_FULL = 800, 1420
F_SPLIT0, F_SPLIT1 = fo(1.84), fo(44.43)
TRANS = 9
TITLE = white_boxes(["100 CLAUDES LUCHANDO", "A MUERTE"], 56, chr(0x2694))
SC = [(1.84, "A"), (5.04, "B"), (8.40, "C"), (12.71, "D"), (15.76, "E"), (21.09, "F"), (28.10, "G"), (33.70, "H"), (40.22, "Z")]
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

# ---- scenes for the Arena Skill video (Claude) ---------------------------------------------
IC = lambda h: chr(h)
def badge(text, icon, col, fnt=None):
    fnt = fnt or F_B; w = int(fa(fnt.size).getlength(icon) + fnt.getlength(text) + fnt.size * 0.45 + 64); h = int(fnt.size * 1.75)
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((15, 21, 15 + w, 21 + h), h // 2, fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im); rr(d, (15, 15, 15 + w, 15 + h), h // 2, fill=col)
    it(d, (15 + w / 2, 15 + h / 2), icon, text, fnt, WHITE, "mm"); return im
F_T = font("InterDisplay-Bold.otf", 40); F_SM = font("Inter-Medium.otf", 24); F_XS = font("Inter-Regular.otf", 22)
GREEN_B = (46, 150, 84); BAD = (200, 64, 64)
CY = 520
f_now = [0]
def put(im, c_, tt, sc_=0.96, y=CY):
    s, a, dy = pop(f_now[0] - T(tt)); paste(im, c_, 540, y + dy, s * sc_, a)
def pop_badge(c_, b, x, y, tt):
    if f_now[0] >= T(tt):
        k = f_now[0] - T(tt); paste(c_, b, x, y, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
SP30 = spark(30); SP22 = spark(22)
RNG = np.random.default_rng(4)
JIT = RNG.uniform(-1, 1, (100, 2)); ORDER = RNG.permutation(100); PH = RNG.uniform(0, 6.28, 100)

# A · 100 Claudes fight to the death -------------------------------------------------------
def scene_A(f, f0):
    im = PANEL.copy(); d = ImageDraw.Draw(im)
    fight = f >= T(3.92)
    for q in range(100):
        tt = T(2.56) + q * 0.12
        if f < tt: continue
        r_, c = divmod(q, 10); x = 140 + c * 60; y = 280 + r_ * 46
        k = f - tt; s = 0.5 + 0.5 * ease_out_back(min(1, k / 4))
        if fight:
            kk = f - T(3.92); amp = 7 * min(1, kk / 4)
            x += amp * math.sin(kk * 0.9 + PH[q]) * 1.4; y += amp * math.cos(kk * 1.1 + PH[q] * 1.3)
            if ORDER[q] < min(60, kk * 3):   # knocked out
                g = SP30.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * 0.22)))
                im.alpha_composite(g, (int(x - 15), int(y - 15))); continue
        sp = SP30 if s >= 0.99 else SP30.resize((max(1, int(30 * s)), max(1, int(30 * s))))
        im.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))
    if f >= T(2.88):
        k = f - T(2.88); s = 0.6 + 0.4 * ease_out_back(k / 7)
        lab = Image.new("RGBA", (300, 160), (0, 0, 0, 0)); dl = ImageDraw.Draw(lab)
        dl.text((150, 70), "×100", font=font("InterDisplay-Black.otf", 100), fill=ORANGE, anchor="mm")
        paste(im, lab, 860, 450, s, min(1, 0.3 + k / 3))
    if fight:
        k = f - T(3.92); s = 0.6 + 0.4 * ease_out_back(k / 7)
        paste(im, badge("A muerte", IC(0xf54c), BAD), 860, 560, s, min(1, 0.3 + k / 3))
    return im

# B · the skill ----------------------------------------------------------------------------
def scene_B(f, f0):
    im = PANEL.copy()
    c_ = card(900, 330); d = ImageDraw.Draw(c_)
    c_.alpha_composite(icon_tile(IC(0xf091), ORANGE, 160), (80, 80))
    d.text((276, 112), "Arena Skill", font=font("InterDisplay-Bold.otf", 72), fill=WHITE, anchor="lm")
    sub = "Skill para Claude"; rr(d, (278, 172, 278 + F_M.getlength(sub) + 92, 222), 25, fill=(60, 58, 55))
    d.text((300, 197), sub, font=F_M, fill=TXT, anchor="lm"); c_.alpha_composite(spark(30), (int(300 + F_M.getlength(sub) + 18), 182))
    pop_badge(c_, badge("100% gratis", IC(0xf06b), GREEN_B), 400, 300, 7.70)
    put(im, c_, 5.04); return im

# C · not satisfied with the answer ---------------------------------------------------------
ASK = "Escríbeme un email para conseguir mi primer cliente"
GENERIC = ["Hola, en el competitivo panorama digital actual,", "las empresas como la tuya necesitan un socio", "que de verdad se preocupe por…"]
def scene_C(f, f0):
    im = PANEL.copy()
    c_ = card(940, 440, fill=PAGE); d = ImageDraw.Draw(c_)
    bw = F_S.getlength(ASK) + 56
    rr(d, (970 - 24 - bw, 54, 970 - 24, 120), 22, fill=(20, 20, 19)); d.text((970 - 24 - bw + 28, 87), ASK, font=F_S, fill=TXT, anchor="lm")
    c_.alpha_composite(spark(38), (62, 150))
    shown = int(max(0, f - T(8.60)) * 3.4); acc = 0
    for j, ln in enumerate(GENERIC):
        d.text((116, 152 + j * 46), ln[:max(0, shown - acc)], font=F_S, fill=TXT); acc += len(ln)
    if f >= T(10.16):
        p = ease_io((f - T(10.16)) / 10)
        for j, ln in enumerate(GENERIC):
            yy = 170 + j * 46; d.line((116, yy, 116 + F_S.getlength(ln) * p, yy), fill=BAD, width=3)
    pop_badge(c_, badge("Respuesta genérica", IC(0xf165), BAD, F_M), 300, 400, 10.40)
    put(im, c_, 8.40); return im

# D · asking again and again -------------------------------------------------------------------
def scene_D(f, f0):
    im = PANEL.copy()
    n = 1 + sum(f >= T(t) for t in (13.36, 14.00, 14.56, 15.04))
    for q in range(n):
        c_ = card(760, 250, fill=PAGE); d = ImageDraw.Draw(c_)
        c_.alpha_composite(spark(30), (62, 66))
        for j, w_ in enumerate((520, 600, 380)): rr(d, (110, 72 + j * 34, 110 + w_, 88 + j * 34), 8, fill=(70, 68, 64))
        rr(d, (62, 196, 330, 248), 14, fill=(52, 51, 49), outline=BORDER, width=2)
        it(d, (196, 222), IC(0xf2f9), "Volver a intentar", F_SM, TXT, "mm", icol=ORANGE)
        tt = T(12.71) if q == 0 else T((13.36, 14.00, 14.56, 15.04)[q - 1])
        s, a, dy = pop(f - tt)
        off = (n - 1 - q) * 22
        paste(im, c_, 540 - off * 1.2, 470 - off + dy, s * (1 - 0.04 * (n - 1 - q)), a * (1 - 0.18 * (n - 1 - q)))
    lab = badge(f"Intento {n}", IC(0xf2f9), ORANGE, F_M)
    paste(im, lab, 820, 300, 1, 1)
    return im

# E · 100 subagents, same task ------------------------------------------------------------------
CMD = "/arena " + ASK
def scene_E(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450, fill=(24, 23, 22)); d = ImageDraw.Draw(c_)
    for q, col in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))): d.ellipse((60 + q * 28, 52, 76 + q * 28, 68), fill=col)
    d.text((970 / 2 + 15, 60), "Arena · Claude", font=F_SM, fill=MUTED, anchor="mm")
    n = min(len(CMD), int(max(0, f - T(15.90)) * 1.6)); mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 23)
    d.text((62, 112), "> " + CMD[:n], font=mono, fill=(230, 228, 220), anchor="lm")
    if f >= T(16.88):
        p = min(1, (f - T(16.88)) / 24); cnt = int(100 * p)
        d.text((62, 156), f"Creando subagentes… {cnt}/100", font=mono, fill=ORANGE if p < 1 else GREEN, anchor="lm")
        for q in range(cnt):
            r_, c = divmod(q, 20); x = 74 + c * 42; y = 200 + r_ * 42
            rr(d, (x - 16, y - 16, x + 16, y + 16), 7, fill=(52, 51, 49), outline=ORANGE if f >= T(18.91) else BORDER, width=2)
            c_.alpha_composite(SP22 if False else spark(20), (int(x - 10), int(y - 10)))
    pop_badge(c_, badge("Misma tarea ×100", IC(0xf0c5), ORANGE, F_M), 700, 448, 19.55)
    put(im, c_, 15.76); return im

# F · each one attacks it differently --------------------------------------------------------------
AG = [("Agente 1", "Primeros principios", IC(0xf5fc)), ("Agente 2", "Inversión", IC(0xf362)), ("Agente 3", "Trabajar hacia atrás", IC(0xf2ea))]
CHIPS = [("Razonamientos", IC(0xf5dc), 24.35), ("Flujos de trabajo", IC(0xf542), 25.55), ("Estrategias", IC(0xf140), 26.75)]
def scene_F(f, f0):
    im = PANEL.copy()
    for q, (a1, a2, ic) in enumerate(AG):
        tt = T(21.31) + q * 5
        if f < tt: continue
        c_ = card(280, 250, 22); d = ImageDraw.Draw(c_)
        d.text((60, 72), a1, font=F_SM, fill=MUTED, anchor="lm"); c_.alpha_composite(spark(26), (254, 59))
        d.text((170, 150), ic, font=fa(50), fill=ORANGE, anchor="mm")
        d.text((170, 232), a2, font=font("Inter-SemiBold.otf", 25), fill=WHITE, anchor="mm")
        s, a, dy = pop(f - tt); paste(im, c_, 540 + (q - 1) * 310, 420 + dy, s, a)
    for q, (lab, ic, tt) in enumerate(CHIPS):
        if f < T(tt): continue
        k = f - T(tt); paste(im, badge(lab, ic, (70, 52, 44), F_SM), 540 + (q - 1) * 312, 640, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
    return im

# G · they compete until one survives ----------------------------------------------------------------
def alive(f):
    if f < T(28.59): return 100
    if f >= T(32.40): return 1
    p = (f - T(28.59)) / (T(32.40) - T(28.59)); return max(1, int(round(100 * (0.01 ** p))))
def scene_G(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450); d = ImageDraw.Draw(c_)
    n = alive(f); rnd = 1 + int(math.log2(100 / max(1, n)))
    d.text((70, 82), f"Ronda {min(rnd, 7)}", font=F_T, fill=WHITE, anchor="lm")
    d.text((900, 82), f"Agentes en pie: {n}", font=F_B, fill=ORANGE, anchor="rm")
    for q in range(100):
        r_, c = divmod(q, 20); x = 92 + c * 42; y = 160 + r_ * 44
        if ORDER[q] < n:
            c_.alpha_composite(SP30, (int(x - 15), int(y - 15)))
        else:
            d.text((x, y), IC(0xf00d), font=fa(18), fill=(85, 83, 79), anchor="mm")
    steps = [("Compiten", IC(0xf6de), 28.59), ("Se critican", IC(0xf075), 29.47), ("Se atacan", IC(0xf0e7), 30.27)]
    for q, (lab, ic, tt) in enumerate(steps):
        if f < T(tt): continue
        k = f - T(tt); paste(c_, badge(lab, ic, (70, 52, 44), F_SM), 210 + q * 290, 410, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
    if f >= T(29.47) and f < T(31.40):
        k = f - T(29.47); paste(c_, badge("Demasiado genérico", IC(0xf00d), BAD, F_XS), 760, 140, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
    if f >= T(32.40):
        k = f - T(32.40); w_ = badge("Solución más fuerte", IC(0xf091), GREEN_B, F_B)
        paste(c_, w_, 500, 275, 0.6 + 0.4 * ease_out_back(k / 7), min(1, 0.3 + k / 3))
    put(im, c_, 28.10); return im

# H · stop re-prompting, get the best answer ---------------------------------------------------------
GOOD = ["Asunto: 3 ideas para duplicar tus ventas", "Hola Ana, vi tu tienda y tengo una idea", "concreta que te puede traer clientes…"]
def scene_H(f, f0):
    im = PANEL.copy()
    c_ = card(940, 450); d = ImageDraw.Draw(c_)
    rr(d, (70, 70, 470, 450), 22, fill=(60, 36, 36), outline=BAD, width=2)
    d.text((270, 112), "Repetir prompts", font=F_B, fill=WHITE, anchor="mm")
    d.text((270, 230), IC(0xf2f9), font=fa(80), fill=(235, 140, 140), anchor="mm")
    if f >= T(34.59):
        mins = min(45, int((f - T(34.59)) * 1.6))
        it(d, (270, 345), IC(0xf017), f"{mins} min perdidos", F_M, (240, 170, 170), "mm")
    rr(d, (500, 70, 900, 450), 22, fill=(30, 60, 42), outline=(46, 160, 90), width=2)
    d.text((700, 112), "Mejor respuesta", font=F_B, fill=WHITE, anchor="mm")
    if f >= T(38.07):
        k = f - T(38.07); c_.alpha_composite(spark(30), (530, 160))
        shown = int(k * 4); acc = 0
        for j, ln in enumerate(GOOD):
            d.text((530, 214 + j * 40), ln[:max(0, shown - acc)], font=font("Inter-Regular.otf", 21), fill=TXT); acc += len(ln)
        pop_badge(c_, badge("Ganadora entre 100", IC(0xf091), GREEN_B, F_SM), 700, 400, 38.70)
    else:
        d.text((700, 250), IC(0xf091), font=fa(80), fill=(90, 120, 100), anchor="mm")
    put(im, c_, 33.70); return im

# Z · Claude chat (dark, Spanish): paste link, type "Install the skill" ---------------------------------
LINK = "github.com/…/arena-skill"; FULL = LINK + " Install the skill"
T_PASTE, T_TYPE, T_SEND = 41.40, 43.05, 44.10
def chat_n(f):
    if f < T(T_PASTE): return 0
    if f < T(T_TYPE): return len(LINK)
    return min(len(FULL), len(LINK) + int((f - T(T_TYPE) + 1) * 16 / FPS))
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
SCENE_FN = {"A": scene_A, "B": scene_B, "C": scene_C, "D": scene_D, "E": scene_E, "F": scene_F, "G": scene_G, "H": scene_H, "Z": scene_Z}

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
    for t in (2.88, 3.92, 7.70, 10.40, 13.36, 14.00, 14.56, 15.04, 16.88, 19.55, 21.31, 24.35, 25.55, 26.75, 28.59, 29.47,
              30.27, 32.40, 38.07, 41.40):
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
            canvas.alpha_composite(TITLE, (int(540 - TITLE.width / 2), 232))
        if f >= KEY["f0"]:   # keyword: big, at the top, alone
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            paste(canvas, KEY["im"], 540, 330, sc, min(1, 0.35 + k / 3))
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
