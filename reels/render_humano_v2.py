import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p3"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/14a9b314-1007_21_r.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P}/out.mp4"
PREVIEW = len(sys.argv) > 2
W, H, FPS = 1080, 1920, 30

RED = (229, 22, 34); INK = (26, 26, 28); WHITE = (255, 255, 255); GRAY = (150, 150, 156)
# Claude dark UI (sampled from the screenshot)
PAGE = (21, 21, 21); CB_BG = (32, 32, 31); CB_BORDER = (62, 62, 60); CB_TEXT = (236, 235, 228)
CB_MUTED = (154, 152, 144); CB_CHIP = (64, 64, 63); CB_GROUP = (40, 40, 39); CLAUDE_ORANGE = (217, 119, 87)
PANEL = PAGE
CARD = (34, 34, 36); CARD_BORDER = (60, 60, 64)

FD = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FD + name, int(size))
def serif(size): return ImageFont.truetype("/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf", int(size))
FA = f"{S}/fa/fa-solid.ttf"
def fa(size): return ImageFont.truetype(FA, int(size))
SPARK = Image.open(f"{P}/spark.png").convert("RGBA")
def spark(h):
    return SPARK.resize((int(SPARK.width * h / SPARK.height), int(h)), Image.LANCZOS)

# ---------------- cuts -------------------------------------------------------------
SIL = [(0.00, 0.87), (8.35, 8.76), (14.43, 14.69), (15.61, 16.18), (17.03, 17.16), (19.76, 19.95), (21.11, 21.25),
       (23.94, 24.18), (26.06, 26.41), (36.22, 36.68), (42.05, 42.29), (43.38, 43.78), (48.33, 48.52), (49.73, 49.93),
       (52.50, 52.97), (57.37, 57.65), (61.83, 62.10), (65.15, 65.39), (67.20, 67.45), (73.29, 73.55), (74.30, 74.74),
       (77.20, 77.54), (82.85, 83.02), (83.86, 84.35), (85.02, 85.33), (87.43, 87.72), (91.46, 91.80), (92.15, 92.40),
       (92.79, 93.08)]
END = 94.45; PAD = 0.04
KEEP = []; cur = SIL[0][1] - PAD
for a, b in SIL[1:]:
    KEEP.append((cur, a + PAD)); cur = b - PAD
KEEP.append((cur, END))
KEEP = [(round(a * 30) / 30, round(b * 30) / 30) for a, b in KEEP]
def m(t):
    o = 0.0
    for a, b in KEEP:
        if t <= a: return o
        if t < b: return o + t - a
        o += b - a
    return o
TOTAL = m(999); NF = sum(round(b * 30) - round(a * 30) for a, b in KEEP)
def fo(t): return int(round(m(t) * FPS))

# ---------------- words ------------------------------------------------------------
PK = json.load(open(f"{P}/words.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü$]", "", s.lower())
SEGS = [
    (0.82, 8.45, "Si pagas Claude o ChatGPT, pídele que humanice tus textos, así nadie va a identificar que los has escrito con inteligencia artificial."),
    (8.76, 15.60, "Te voy a enseñar la forma que estamos usando aquí en Claseflix para humanizar todos nuestros textos usando ChatGPT, Claude y otras IA."),
    (16.15, 19.70, "Lo primero de todo, abres la IA que uses y le pones esto:"),
    (26.37, 36.20, "Pero lo importante no es solo decirle ese prompt, lo importante es darle una referencia. ¿Para qué? Para que él sepa qué evitar y qué hacer. Entonces, en ese mismo mensaje, le vas a decir:"),
    (52.89, 67.20, "Con esto, tu inteligencia artificial, sea Claude, ChatGPT o la que quieras, empezará a dejar de usar esos guiones, esas cosas que cantan tan solo de mirarlas que el texto fue creado por inteligencia artificial."),
    (67.45, 77.20, "Si tú quieres el paso a paso para entender esto, estoy preparando un PDF muy detallado para que tú aprendas a humanizar muy bien tu inteligencia artificial o tus agentes."),
    (77.54, 87.43, "Y si tú quieres aprender a generar ingresos con inteligencia artificial, que está totalmente actualizado, y generar entre 300 y 500 dólares cada día, comenta aquí abajo HUMANO,"),
    (87.70, 94.40, "que te voy a enviar el PDF y un vídeo explicando cómo lo consigues paso a paso. Comenta aquí abajo HUMANO."),
]
def align(s0, s1, text):
    ws = text.split()
    pk = [(w, t) for w, t, _ in PK if s0 - 0.35 <= t <= s1 + 0.1]
    a = [norm(w) for w in ws]; b = [norm(w) for w, _ in pk]
    times = [None] * len(ws)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(i2 - i1):
                if j1 + k < j2: times[i1 + k] = pk[j1 + k][1]
    anchors = [(-1, s0)] + [(i, t) for i, t in enumerate(times) if t is not None] + [(len(ws), s1)]
    for i in range(len(ws)):
        if times[i] is None:
            lo = max(x for x in anchors if x[0] < i); hi = min(x for x in anchors if x[0] > i)
            times[i] = lo[1] + (hi[1] - lo[1]) * (i - lo[0]) / (hi[0] - lo[0])
    for i in range(1, len(times)): times[i] = max(times[i], times[i - 1] + 0.05)
    return list(zip(ws, times))
INTROW = align(*SEGS[0])
CAPW = []
for sg in SEGS[1:]: CAPW += align(*sg)

# ---------------- helpers ----------------------------------------------------------
def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def shadow_layer(size, box, radius, blur, alpha, offset=(0, 10), color=(0, 0, 0)):
    sh = Image.new("RGBA", size, (0, 0, 0, 0)); x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]), radius, fill=color + (alpha,))
    return sh.filter(ImageFilter.GaussianBlur(blur))
def paste(canvas, im, x, y, scale=1.0, alpha=1.0, center=True):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    if center: x, y = x - im.width / 2, y - im.height / 2
    x, y = int(x), int(y)
    canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))
def pop(k, n=7): return 0.7 + 0.3 * ease_out_back(k / n), min(1, k / 3 + 0.2), (1 - ease_out_cubic(k / n)) * 30

# ---------------- layout -----------------------------------------------------------
TOP = 768                       # 40 % top panel
OFF_I, OFF_S = 100, 380         # intro shift / split shift of the full-frame talking head
F_SPLIT = fo(8.76); TRANS = 10
CAP_Y = 714                     # caption line inside the panel, just above the seam
VY0, VY1 = 222, 664             # content viewport inside the panel (clear of the IG header)
VH = VY1 - VY0

def head_full(guy, off):
    out = np.empty_like(guy); out[:] = 255
    out[off:] = guy[:H - off]
    if off > 0:
        ramp = np.clip((np.arange(H) - off) / 150, 0, 1).astype(np.float32)[:, None, None]
        ramp = ramp * ramp * (3 - 2 * ramp)
        out = (out.astype(np.float32) * ramp + 255 * (1 - ramp)).astype(np.uint8)
    return out

# ---------------- intro title ------------------------------------------------------
def wt(i): return fo(INTROW[i][1])
F_TI = font("InterDisplay-Medium.otf", 64); F_TB = font("InterDisplay-Black.otf", 74); F_TS = font("Inter-SemiBoldItalic.otf", 46)
def tile_img():
    s = 112; im = Image.new("RGBA", (s + 40, s + 40), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (20, 20, 20 + s, 20 + s), 26, 10, 70, (0, 6)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, 20 + s, 20 + s), 26, fill=WHITE)
    sp = spark(62); im.alpha_composite(sp, (20 + (s - sp.width) // 2, 28))
    d.text((20 + s / 2, 20 + s - 18), "Claude", font=serif(20), fill=INK, anchor="mm")
    return im
TILE = tile_img()
def text_img(txt, fnt, color, track=0):
    w = int(sum(fnt.getlength(c) + track for c in txt)) + 20; asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (w, asc + desc + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 10
    for c in txt: d.text((x, 10), c, font=fnt, fill=color); x += fnt.getlength(c) + track
    return im
T_SIPAGAS = text_img("SI PAGAS", F_TI, INK, 4)
T_OGPT = text_img("o ChatGPT", font("InterDisplay-Medium.otf", 40), (90, 90, 96))
T_PIDE = text_img("PÍDELE QUE HUMANICE", F_TB, RED)
T_TUS = text_img("tus textos así", F_TS, INK)
def hook_title(canvas, f):
    e_out = 1 - ease_out_cubic((f - F_SPLIT) / TRANS) if f >= F_SPLIT else 1
    if e_out <= 0: return
    # row 1: SI PAGAS [tile] o ChatGPT
    k = f - wt(0)
    if k >= 0:
        s, a, dy = pop(k)
        paste(canvas, T_SIPAGAS, 300, 300 + dy, s, a * e_out)
    k = f - wt(2)
    if k >= 0:
        s, a, dy = pop(k, 8)
        paste(canvas, TILE, 560, 300 + dy, s * (1 + 0.04 * math.sin(k / 5)), a * e_out)
    k = f - wt(4)
    if k >= 0:
        s, a, dy = pop(k)
        paste(canvas, T_OGPT, 760, 305 + dy, s, a * e_out)
    # row 2: PÍDELE QUE HUMANICE (word by word wipe), row 3: tus textos así
    k = f - wt(5)
    if k >= 0:
        p = ease_out_cubic(k / 14)
        im = T_PIDE.crop((0, 0, max(1, int(T_PIDE.width * p)), T_PIDE.height))
        full = Image.new("RGBA", T_PIDE.size, (0, 0, 0, 0)); full.alpha_composite(im)
        paste(canvas, full, 520, 432 + (1 - ease_out_cubic(k / 6)) * 16, 0.92 + 0.08 * ease_out_back(k / 8), e_out)
    k = f - wt(8)
    if k >= 0:
        s, a, dy = pop(k)
        paste(canvas, T_TUS, 520, 520 + dy, s, a * e_out)
    # "hecho con IA" stamp crossed out on "inteligencia artificial"
    k = f - wt(len(INTROW) - 2)
    if k >= 0:
        s, a, dy = pop(k)
        paste(canvas, STAMP, 520, 584 + dy, s, a * e_out)
def stamp_img():
    f_ = font("InterDisplay-SemiBold.otf", 34); txt = "nadie notará que es IA"
    w = int(f_.getlength(txt) + 110); h = 64
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (20, 20, 20 + w, 20 + h), 26, 12, 80, (0, 8)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, 20 + w, 20 + h), 20, fill=INK)
    d.text((62, 20 + h / 2), "\uf070", font=fa(28), fill=WHITE, anchor="mm")
    d.text((96, 20 + h / 2), txt, font=f_, fill=WHITE, anchor="lm")
    return im
STAMP = stamp_img()

# ---------------- captions ---------------------------------------------------------
HLP = ["referencia", "qué evitar", "qué hacer", "esos guiones", "pdf", "humano", "300 y 500 dólares", "claseflix",
       "humanizar"]
HLP = [p.split() for p in HLP]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(CAPW):
    hit = next((p for p in HLP if [norm(w) for w, _ in CAPW[i:i + len(p)]] == [norm(x) for x in p]), None)
    if hit: g = CAPW[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [CAPW[i]]; i += 1; hl = False
        while i < len(CAPW) and len(g) < 3 and not PUNCT.search(g[-1][0]):
            if CAPW[i][1] - g[0][1] > 0.75 or sum(len(w) for w, _ in g) + len(CAPW[i][0]) > 15: break
            if any([norm(w) for w, _ in CAPW[i:i + len(p)]] == [norm(x) for x in p] for p in HLP): break
            g.append(CAPW[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w for w, _ in g))
    txt = txt if (txt.isupper() and len(txt) > 3) else txt.lower()
    txt = txt.replace("pdf", "PDF").replace("chatgpt", "ChatGPT").replace("claude", "Claude").replace("claseflix", "Claseflix").replace(" ia", " IA")
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1]))
merged = []
for c in chunks:
    if merged and c["hl"] and not merged[-1]["hl"] and " " not in merged[-1]["txt"] and len(merged[-1]["txt"]) <= 3:
        p = merged.pop(); c = dict(c, txt=p["txt"] + " " + c["txt"], t0=p["t0"])
    merged.append(c)
chunks = merged
for c in chunks: c["f0"] = fo(c["t0"])
for k, c in enumerate(chunks): c["f1"] = min(chunks[k + 1]["f0"] if k + 1 < len(chunks) else NF, c["f0"] + 30)
FC = font("InterDisplay-Bold.otf", 56)
def make_caption(txt, hl):
    tw = FC.getlength(txt); bb = FC.getbbox(txt); padx, pady = 20, 10
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if hl: d.rounded_rectangle((20, 20, w - 20, h - 20), 14, fill=RED)
    d.text((w / 2, h / 2 - 2), txt, font=FC, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"])

# ---------------- top scenes -------------------------------------------------------
SS = 2
SCENES = [(8.76, "intro"), (16.15, "chat"), (26.37, "ref"), (34.20, "chat"), (52.70, "tells"), (67.45, "cta")]
SCENES = [(fo(t), n) for t, n in SCENES]
def scene_at(f):
    cur_ = SCENES[0]
    for s_ in SCENES:
        if f >= s_[0]: cur_ = s_
    return cur_

# --- chat (real Claude dark UI) ---
PROMPT = [
    (19.89, 25.95, "De ahora en adelante, humaniza todos mis textos para que no parezcan creados con inteligencia artificial."),
    (36.62, 43.20, "\nEntra en Wikipedia y busca la página sobre las señales de que un texto fue escrito por inteligencia artificial."),
    (43.74, 48.30, " Enumera todos los patrones que hacen que un texto parezca generado por IA"),
    (48.52, 52.40, " y, a partir de ahora, evita usar cualquiera de ellos."),
]
FULL = "".join(t for _, _, t in PROMPT)
SEG_CH = []; acc = 0
for a, b, t in PROMPT:
    SEG_CH.append((fo(a), max(fo(b), fo(a) + 1), acc, acc + len(t))); acc += len(t)
def chars_at(f):
    n = 0
    for f0, f1, c0, c1 in SEG_CH:
        if f >= f1: n = c1
        elif f >= f0: n = c0 + int(round((c1 - c0) * min(1, (f - f0 + 1) / (f1 - f0)))); break
        else: break
    return n
BX0, BX1 = 50, 1030
PADX, PADT, LH, MAXL = 36, 32, 50, 6
FT = font("Inter-Regular.otf", 33 * SS)
WRAPW = (BX1 - BX0 - 2 * PADX) * SS
LINES = []; pos = 0
for para in FULL.split("\n"):
    ws_ = re.findall(r"\S+\s*", para); ls = pos; line = ""
    for wd in ws_:
        if FT.getlength((line + wd).rstrip()) > WRAPW and line:
            LINES.append((ls, ls + len(line))); ls += len(line); line = wd
        else: line += wd
    LINES.append((ls, ls + len(line))); pos = ls + len(line) + 1
def line_of(n):
    for k, (a, b) in enumerate(LINES):
        if n <= b: return k
    return len(LINES) - 1
F_UI = font("Inter-Medium.otf", 27 * SS); F_UI2 = font("Inter-Regular.otf", 27 * SS)
CH_H = 900          # chat scene height (1x)
GREET_Y = 250; BOX_T = 340
def draw_chat(f):
    sc = Image.new("RGBA", (W * SS, CH_H * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    n = chars_at(f)
    sendk = f - fo(52.42)
    # greeting
    sp = spark(54 * SS); gtxt = "Buenas tardes"; gf = serif(58 * SS)
    gw = sp.width + 22 * SS + gf.getlength(gtxt); gx = (W * SS - gw) / 2
    sc.alpha_composite(sp, (int(gx), int(GREET_Y * SS - sp.height / 2)))
    d.text((gx + sp.width + 22 * SS, GREET_Y * SS), gtxt, font=gf, fill=(232, 230, 222), anchor="lm")
    nlines = 1 if n == 0 else line_of(n) + 1
    vis = min(nlines, MAXL); scroll = max(0, nlines - MAXL)
    top = BOX_T * SS; th = vis * LH * SS; bot = top + (PADT + 4) * SS + th + 100 * SS
    d.rounded_rectangle((BX0 * SS, top, BX1 * SS, bot), 26 * SS, fill=CB_BG, outline=CB_BORDER, width=2 * SS)
    tx, ty = (BX0 + PADX) * SS, top + PADT * SS; cur_xy = (tx, ty)
    if n == 0:
        d.text((tx, ty), "¿En qué puedo ayudarte hoy?", font=FT, fill=CB_MUTED)
    else:
        for k in range(scroll, nlines):
            a, b = LINES[k]; b = min(b, n); y = ty + (k - scroll) * LH * SS
            seg = FULL[a:b].replace("\n", "")
            d.text((tx, y), seg, font=FT, fill=CB_TEXT); cur_xy = (tx + FT.getlength(seg), y)
    if (f // 15) % 2 == 0 or n > 0:
        cx, cy = cur_xy
        d.rectangle((cx + 3 * SS, cy + 4 * SS, cx + 5 * SS, cy + 40 * SS), fill=CB_TEXT)
    by = bot - 52 * SS
    d.text((BX0 * SS + 46 * SS, by), "", font=fa(28 * SS), fill=CB_TEXT, anchor="mm")
    c0 = BX0 * SS + 82 * SS
    d.rounded_rectangle((c0, by - 28 * SS, c0 + 266 * SS, by + 28 * SS), 12 * SS, fill=CB_GROUP)
    d.rounded_rectangle((c0 + 4 * SS, by - 24 * SS, c0 + 108 * SS, by + 24 * SS), 10 * SS, fill=CB_CHIP)
    d.text((c0 + 56 * SS, by), "Chat", font=F_UI, fill=CB_TEXT, anchor="mm")
    d.text((c0 + 188 * SS, by), "Cowork", font=F_UI, fill=CB_MUTED, anchor="mm")
    rx = BX1 * SS - 34 * SS
    if n > 0:
        s_ = 1 - 0.2 * math.sin(min(1, sendk / 8) * math.pi) if 0 <= sendk else 1
        r = 26 * SS * s_
        d.rounded_rectangle((rx - 2 * r + 6 * SS, by - r, rx + 6 * SS, by + r), 12 * SS, fill=CLAUDE_ORANGE)
        d.text((rx - r + 6 * SS, by), "", font=fa(24 * SS), fill=WHITE, anchor="mm"); rx -= 2 * r + 26 * SS
    else:
        d.text((rx, by), "", font=fa(16 * SS), fill=CB_MUTED, anchor="mm"); rx -= 34 * SS
        for k_, hh in enumerate([10, 20, 30, 20, 12]):
            x_ = rx - k_ * 8 * SS
            d.rounded_rectangle((x_ - 2 * SS, by - hh / 2 * SS, x_ + 2 * SS, by + hh / 2 * SS), 2 * SS, fill=CB_TEXT)
        rx -= 62 * SS
    d.text((rx, by), "", font=fa(28 * SS), fill=CB_TEXT, anchor="mm"); rx -= 46 * SS
    d.text((rx, by), "Medio", font=F_UI2, fill=CB_MUTED, anchor="rm"); rx -= F_UI2.getlength("Medio") + 14 * SS
    d.text((rx, by), "Sonnet 5.5", font=F_UI, fill=(206, 204, 196), anchor="rm")
    return sc, (cur_xy[0] / SS, cur_xy[1] / SS + 20), bot / SS, n

class Cam: pass
cam = Cam(); cam.x = cam.y = cam.z = None; cam.tx = None
def chat_target(f, cur, bot, n):
    typing = any(f0 <= f < f1 + 6 for f0, f1, _, _ in SEG_CH)
    if typing:
        z = 1.55
        left, right = BX0 + 540 / z - 14, BX1 - 540 / z + 14
        if cam.tx is None: cam.tx = left
        if cur[0] > cam.tx + 540 / z - 70: cam.tx = right
        elif cur[0] < cam.tx - 540 / z + 70: cam.tx = left
        return cam.tx, cur[1], z
    cam.tx = None
    z = min(1.0, VH / (bot - GREET_Y + 120))
    return 540, (GREET_Y - 60 + bot) / 2, z
def sample(sc, x, y, z, vw=W, vh=VH):
    a = 1 / z; x0 = x - vw / 2 * a; y0 = y - vh / 2 * a
    return sc.transform((vw, vh), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=PAGE + (255,))
def chat_view(f):
    sc, cur, bot, n = draw_chat(f)
    tx, ty, tz = chat_target(f, cur, bot, n)
    if cam.x is None: cam.x, cam.y, cam.z = tx, ty, tz
    px, py, pz = cam.x, cam.y, cam.z; k = 0.22
    cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k; cam.z += (tz - cam.z) * k
    mv = math.hypot((cam.x - px) * cam.z, (cam.y - py) * cam.z) + abs(cam.z - pz) * 600
    ns = 1 if mv < 6 else min(7, 2 + int(mv / 9))
    if ns == 1: return sample(sc, cam.x, cam.y, cam.z)
    acc_ = None
    for i in range(ns):
        u = i / (ns - 1)
        s_ = np.asarray(sample(sc, px + (cam.x - px) * u, py + (cam.y - py) * u, pz + (cam.z - pz) * u), np.float32)
        acc_ = s_ if acc_ is None else acc_ + s_
    return Image.fromarray((acc_ / ns).astype(np.uint8)).convert("RGBA")

# --- generic dark cards for the explanatory scenes ---
F_H = font("InterDisplay-Bold.otf", 44); F_B = font("InterDisplay-SemiBold.otf", 34); F_S = font("Inter-Regular.otf", 27)
def dcard(w, h, r=24, fill=CARD, border=CARD_BORDER):
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (20, 20, 20 + w, 20 + h), r, 12, 150, (0, 8)))
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + w, 20 + h), r, fill=fill, outline=border, width=2)
    return im
def chip(label, icon=None, w=None, icon_img=None, accent=RED):
    tw = F_B.getlength(label); w = w or int(tw + (110 if (icon or icon_img) else 56)); h = 84
    im = dcard(w, h, 20); d = ImageDraw.Draw(im); x = 20 + 18
    if icon_img is not None:
        sp = icon_img; im.alpha_composite(sp, (int(x + 4), int(20 + (h - sp.height) / 2))); x += 62
    elif icon:
        d.rounded_rectangle((x, 20 + 14, x + 56, 20 + 70), 14, fill=accent)
        d.text((x + 28, 20 + 42), icon, font=fa(26), fill=WHITE, anchor="mm"); x += 72
    d.text((x, 20 + 42), label, font=F_B, fill=WHITE, anchor="lm")
    return im
def heading(txt, color=WHITE, f_=F_H):
    im = Image.new("RGBA", (int(f_.getlength(txt)) + 20, 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), txt, font=f_, fill=color); return im

# intro scene: "how we humanize our texts" + AI chips
INTRO_H = heading("Cómo humanizamos nuestros textos")
INTRO_CHIPS = [(fo(13.60), chip("ChatGPT", "")), (fo(14.56), chip("Claude", icon_img=spark(46))), (fo(15.20), chip("otras IA", ""))]
def scene_intro(f, f0):
    im = Image.new("RGBA", (W, VH), PANEL + (255,))
    s, a, dy = pop(f - f0); paste(im, INTRO_H, 540, 120 + dy, s, a)
    k = f - fo(10.80)
    if k >= 0:
        b = chip("Método Claseflix", ""); s, a, dy = pop(k); paste(im, b, 540, 230 + dy, s, a)
    xs = [230, 520, 820]
    for (t0, c), x in zip(INTRO_CHIPS, xs):
        if f >= t0:
            s, a, dy = pop(f - t0); paste(im, c, x, 360 + dy, s, a)
    return im
# reference scene: prompt alone vs prompt + reference, then avoid / do
def scene_ref(f, f0):
    im = Image.new("RGBA", (W, VH), PANEL + (255,)); d = ImageDraw.Draw(im)
    k1 = f - fo(26.37); k2 = f - fo(29.97); k3 = f - fo(32.93); k4 = f - fo(33.73)
    if k1 >= 0:
        c = dcard(440, 200); dc = ImageDraw.Draw(c)
        dc.text((40, 50), "", font=fa(40), fill=GRAY); dc.text((100, 48), "Solo el prompt", font=F_B, fill=GRAY)
        dc.text((40, 120), "La IA adivina qué evitar", font=F_S, fill=GRAY)
        s, a, dy = pop(k1); paste(im, c, 270, 150 + dy, s, a * (0.55 if k2 >= 0 else 1))
        if k2 >= 4:
            p = ease_out_cubic((k2 - 4) / 6); d.line((70, 150, 70 + 400 * p, 150), fill=RED, width=7)
    if k2 >= 0:
        c = dcard(440, 200, fill=(46, 20, 22), border=RED); dc = ImageDraw.Draw(c)
        dc.text((40, 50), "", font=fa(40), fill=WHITE); dc.text((100, 48), "Prompt + referencia", font=F_B, fill=WHITE)
        dc.text((40, 120), "Sabe exactamente qué evitar", font=F_S, fill=(230, 200, 200))
        s, a, dy = pop(k2); paste(im, c, 810, 150 + dy, s, a)
    if k3 >= 0:
        s, a, dy = pop(k3); paste(im, chip("Qué evitar", ""), 330, 350 + dy, s, a)
    if k4 >= 0:
        s, a, dy = pop(k4); paste(im, chip("Qué hacer", ""), 750, 350 + dy, s, a)
    return im
# AI tells being crossed out
TELLS = [(fo(54.97), "Claude", None), (fo(55.69), "ChatGPT", None), (fo(56.97), "la que quieras", None)]
SIGNS = [(fo(60.17), "Guiones largos  —"), (fo(61.13), "«No es X, es Y»"), (fo(62.81), "Listas de tres"),
         (fo(63.53), "«En resumen…»"), (fo(64.73), "Frases de relleno"), (fo(65.53), "Tono robótico")]
SIGN_IM = [(t, chip(l, "")) for t, l in SIGNS]
def scene_tells(f, f0):
    im = Image.new("RGBA", (W, VH), PANEL + (255,)); d = ImageDraw.Draw(im)
    if f < fo(59.0):
        s, a, dy = pop(f - f0); paste(im, heading("Funciona con cualquier IA"), 540, 110 + dy, s, a)
        items = [chip("Claude", icon_img=spark(46)), chip("ChatGPT", ""), chip("la que quieras", "")]
        for (t0, _, _), c, x in zip(TELLS, items, [220, 500, 820]):
            if f >= t0:
                s, a, dy = pop(f - t0); paste(im, c, x, 260 + dy, s, a)
        return im
    k0 = f - fo(59.0)
    s, a, dy = pop(k0); paste(im, heading("Señales de texto hecho con IA"), 540, 60 + dy, s, a)
    for idx, (t0, c) in enumerate(SIGN_IM):
        if f < t0: continue
        col, row = idx % 2, idx // 2
        x = 290 + col * 500; y = 175 + row * 112
        s, a, dy = pop(f - t0); paste(im, c, x, y + dy, s, a)
        k = f - t0
        if k > 5:
            p = ease_out_cubic((k - 5) / 6); x0 = x - c.width / 2 + 34
            d.line((x0, y, x0 + (c.width - 68) * p, y), fill=RED, width=6)
    return im
# CTA scene
def scene_cta(f, f0):
    im = Image.new("RGBA", (W, VH), PANEL + (255,)); d = ImageDraw.Draw(im)
    kpdf = f - fo(69.93); kmoney = f - fo(77.76); kcta = f - fo(85.36); kpv = f - fo(88.48)
    if kmoney < 0:
        s, a, dy = pop(f - f0); paste(im, heading("El paso a paso completo"), 540, 90 + dy, s, a)
        if kpdf >= 0:
            c = dcard(560, 230); dc = ImageDraw.Draw(c)
            dc.rounded_rectangle((44, 50, 144, 170), 16, fill=RED); dc.text((94, 110), "PDF", font=font("InterDisplay-Black.otf", 34), fill=WHITE, anchor="mm")
            dc.text((170, 64), "Guía detallada", font=F_B, fill=WHITE)
            dc.text((170, 116), "Humaniza tu IA", font=F_S, fill=GRAY); dc.text((170, 152), "y tus agentes", font=F_S, fill=GRAY)
            s, a, dy = pop(kpdf, 8); paste(im, c, 540, 290 + dy, s, a)
        return im
    if kcta < 0:
        s, a, dy = pop(kmoney); paste(im, heading("Genera ingresos con IA"), 540, 90 + dy, s, a)
        p = ease_out_cubic((f - fo(82.40)) / 18) if f >= fo(82.40) else 0
        lo = int(round(300 * p / 10) * 10); hi = int(round(500 * p / 10) * 10)
        txt = f"${lo} – ${max(lo, hi)}"
        big = font("InterDisplay-Black.otf", 130)
        t_im = Image.new("RGBA", (int(big.getlength(txt)) + 40, 170), (0, 0, 0, 0)); dt = ImageDraw.Draw(t_im)
        dt.text((20, 10), txt, font=big, fill=WHITE)
        paste(im, t_im, 540, 270, 0.9 + 0.1 * ease_out_back(min(1, max(0, f - fo(82.40)) / 8)))
        if f >= fo(84.32):
            s, a, dy = pop(f - fo(84.32)); paste(im, heading("cada día", (255, 110, 116)), 540, 380 + dy, s, a)
        return im
    kk = kcta
    pulse = 1 + 0.03 * math.sin(kk / FPS * 2 * math.pi * 1.3)
    s, a, dy = pop(kk)
    c = dcard(760, 150, 30, fill=RED, border=RED); dc = ImageDraw.Draw(c)
    dc.text((90, 95), "", font=fa(56), fill=WHITE, anchor="mm")
    dc.text((150, 52), "COMENTA", font=font("Inter-Bold.otf", 26), fill=(255, 210, 212))
    dc.text((150, 82), "“HUMANO”", font=font("InterDisplay-Black.otf", 58), fill=WHITE)
    paste(im, c, 540, 150 + dy, s * pulse, a)
    if kpv >= 0:
        for j, (lab, ic) in enumerate([("PDF detallado", ""), ("Vídeo paso a paso", "")]):
            s, a, dy = pop(kpv - j * 4)
            if kpv - j * 4 >= 0: paste(im, chip(lab, ic), [300, 760][j], 340 + dy, s, a)
    return im

def top_view(f):
    f0, name = scene_at(f)
    if name == "chat": v = chat_view(f)
    elif name == "intro": v = scene_intro(f, f0)
    elif name == "ref": v = scene_ref(f, f0)
    elif name == "tells": v = scene_tells(f, f0)
    else: v = scene_cta(f, f0)
    if name != "chat": cam.x = None
    k = f - f0
    if k < 8 and f0 != F_SPLIT:   # whip-in from the right with motion blur
        q = ease_out_cubic(k / 8); dx = int((1 - q) * 260); n_ = int((1 - q) * 30) + 1
        arr = np.asarray(v.convert("RGB"), np.float32)
        if n_ > 1:
            acc_ = np.zeros_like(arr)
            for s_ in range(n_): acc_ += np.roll(arr, s_ - n_ // 2, axis=1)
            arr = acc_ / n_
        arr = np.roll(arr, dx, axis=1)
        if dx: arr[:, :dx] = PANEL
        v = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    return v

# ---------------- audio ------------------------------------------------------------
SR = 48000
def sfx_track(whoosh_f, pop_f, keys):
    rng = np.random.default_rng(11)
    n = int(0.34 * SR); t = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n); y = 0.0
    for k in range(n):
        c = 0.03 + 0.25 * math.sin(math.pi * k / n) ** 2; y += c * (noise[k] - y); out[k] = y
    whoosh = out / np.abs(out).max() * np.sin(np.pi * np.clip(t / 0.34, 0, 1)) ** 1.6 * 0.2
    n2 = int(0.08 * SR); t2 = np.arange(n2) / SR
    popw = np.sin(2 * np.pi * np.cumsum(950 * np.exp(-t2 * 22) + 260) / SR) * np.exp(-t2 * 45) * 0.24
    n3 = int(0.018 * SR); t3 = np.arange(n3) / SR
    trk = np.zeros(int((TOTAL + 1) * SR))
    for f in whoosh_f:
        s = max(0, int((f / FPS - 0.12) * SR)); trk[s:s + len(whoosh)] += whoosh[:len(trk) - s]
    for f in pop_f:
        s = int(f / FPS * SR); trk[s:s + len(popw)] += popw[:len(trk) - s]
    for tsec in keys:
        click = np.convolve(rng.standard_normal(n3) * np.exp(-t3 * 380) * rng.uniform(0.035, 0.06), [0.5, 0.5], "same")
        s = int(tsec * SR); trk[s:s + n3] += click[:len(trk) - s]
    st = np.stack([trk, trk], 1)
    with wave.open(f"{P}/sfx.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
def audio():
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.008:.4f}:d=0.008[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[1:a]volume=0.9[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{P}/sfx.wav", "-filter_complex", fc, "-map", "[o]",
                    "-ar", "48000", f"{P}/voice.wav"], check=True)
def guy_cmd():
    v = [f"[0:v]trim=start_frame={round(s * 30)}:end_frame={round(e * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=1:a=0,fps=30,scale={W}:{H}:flags=lanczos,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF), "-f", "rawvideo", "-"]

# ---------------- main -------------------------------------------------------------
def render():
    keys = []; prev = 0
    for f in range(NF):
        n = chars_at(f)
        for c in range(prev, n):
            if FULL[c] not in " \n" and c % 2 == 0: keys.append(f / FPS + (c - prev) / max(1, n - prev) / FPS)
        prev = n
    pops = [wt(0), wt(2), wt(4), wt(5), wt(8)] + [t for t, _ in INTRO_CHIPS] + [t for t, _ in SIGNS] + \
           [fo(x) for x in (26.37, 29.97, 32.93, 33.73, 54.97, 55.69, 56.97, 69.93, 84.32, 85.36, 88.48, 52.42)]
    whooshes = [s_[0] for s_ in SCENES]
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        sfx_track(whooshes, pops, keys); audio()
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow",
                                "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                                "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(float(x) * FPS)) for x in sys.argv[2].split(",")) if PREVIEW else None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if want is not None and not any(0 <= w - f < 14 for w in want):
            if f > max(want): break
            continue
        if f < F_SPLIT:
            canvas = Image.fromarray(head_full(guy, OFF_I)).convert("RGBA")
            hook_title(canvas, f)
        else:
            e = ease_out_cubic((f - F_SPLIT) / TRANS)
            off = int(round(OFF_I + (OFF_S - OFF_I) * e)); edge = int(round(TOP * e))
            full = head_full(guy, off) if e < 1 else None
            fr = np.empty((H, W, 3), np.uint8); fr[:] = PANEL
            if e < 1: fr[edge:] = full[edge:]
            else: fr[TOP:] = guy[TOP - OFF_S:H - OFF_S]
            canvas = Image.fromarray(fr).convert("RGBA")
            v = top_view(f)
            if e < 1:
                v = v.copy(); v.putalpha(v.getchannel("A").point(lambda x: int(x * e)))
            canvas.alpha_composite(v, (0, VY0 - int((1 - e) * 120)) if VY0 - int((1 - e) * 120) >= 0 else (0, 0))
            if e < 1: hook_title(canvas, f)
            for c in chunks:
                if not (c["f0"] <= f < c["f1"]): continue
                if any(f0 <= f < f1 for f0, f1, _, _ in SEG_CH): continue
                k = f - c["f0"]
                paste(canvas, c["im"], 540, CAP_Y + (1 - ease_out_cubic(k / 5)) * 8,
                      scale=0.86 + 0.14 * ease_out_back(k / 5), alpha=min(1, 0.35 + k / 3) * e)
        if want is not None and f not in want: continue
        out = np.array(canvas.convert("RGB"))
        if PREVIEW: Image.fromarray(out).save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    gp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

# ======== v2 overrides: intro typography, fewer tells, money scene ========
HS2 = font("InterDisplay-SemiBold.otf", 58)
def fit_big2(txt, mx=880, start=116):
    s_ = start
    while font("InterDisplay-Black.otf", s_).getlength(txt) > mx and s_ > 60: s_ -= 4
    return font("InterDisplay-Black.otf", s_)
def hw(i): return re.sub(r"[¿?¡!.,:;]", "", INTROW[i][0]).lower().replace("chatgpt", "ChatGPT").replace("claude", "Claude")
TILE_W = 104
def layout2(tokens, fnt, y, cx=520):
    # tokens: (kind, idx, hl) kind 'w' word or 't' Claude tile
    sp = fnt.getlength(" ")
    widths = [fnt.getlength(hw(i)) if k == "w" else TILE_W for k, i, _ in tokens]
    gaps = [sp + (22 if (a[2] or b[2]) else 0) + (6 if "t" in (a[0], b[0]) else 0) for a, b in zip(tokens, tokens[1:])]
    x = cx - (sum(widths) + sum(gaps)) / 2; out = []
    for j, ((k, i, hl), w_) in enumerate(zip(tokens, widths)):
        out.append((k, i, hl, x, y, fnt, w_)); x += w_ + (gaps[j] if j < len(gaps) else 0)
    return out
def T(*idx, hl=()): return [("t" if i == "tile" else "w", 2 if i == "tile" else i, i in hl) for i in idx]
PH = [
    (T(0, 1, "tile", 3, 4), T(5, 6, 7, hl=(7,)), T(8, 9), 10),
    (T(10, 11, 12, 13), T(14, hl=(14,)), [], 15),
    (T(15, 16, 17, 18, 19), T(20, 21, hl=(21,)), [], None),
]
INTRO_L = []
for l1, l2, l3, end in PH:
    big_txt = " ".join(hw(i) for k, i, _ in l2)
    fb = fit_big2(big_txt)
    items = layout2(l1, HS2, 250) + layout2(l2, fb, 326) + (layout2(l3, HS2, 470) if l3 else [])
    f0 = fo(INTROW[l1[0][1] if l1[0][0] == "w" else 2][1])
    INTRO_L.append(dict(items=items, f0=f0, end=end))
for k, L in enumerate(INTRO_L):
    L["f1"] = INTRO_L[k + 1]["f0"] if k + 1 < len(INTRO_L) else F_SPLIT + TRANS
TILE2 = tile_img().resize((TILE_W + 36, TILE_W + 36), Image.LANCZOS)
def word_sprite2(w, fnt, hl, box_p):
    asc, desc = fnt.getmetrics(); tw = fnt.getlength(w); padx, pady = 16, 6
    im = Image.new("RGBA", (int(tw + 2 * padx + 40), int(asc + desc + 2 * pady + 40)), (0, 0, 0, 0))
    if hl and box_p > 0:
        bw = (tw + 2 * padx) * box_p; x0 = 20 + (tw + 2 * padx - bw) / 2
        ImageDraw.Draw(im).rounded_rectangle((x0, 20 + desc * 0.35, x0 + bw, im.height - 20 - desc * 0.15), 16, fill=RED)
    ImageDraw.Draw(im).text((20 + padx, 20 + pady), w, font=fnt, fill=WHITE if (hl and box_p > 0.5) else INK)
    return im, 20 + padx, 20 + pady
def hook_title(canvas, f):
    e_out = 1 - ease_out_cubic((f - F_SPLIT) / TRANS) if f >= F_SPLIT else 1
    if e_out <= 0: return
    for L in INTRO_L:
        if not (L["f0"] <= f < L["f1"]): continue
        for k_, i, hl, x, y, fnt, w_ in L["items"]:
            wf = fo(INTROW[i][1])
            if f < wf: continue
            k = f - wf
            sc = 0.55 + 0.45 * ease_out_back(k / 5, 2.2); al = min(1.0, k / 2 + 0.2) * e_out
            dy = (1 - ease_out_cubic(k / 5)) * 24
            asc = fnt.getmetrics()[0]
            if k_ == "t":
                paste(canvas, TILE2, x + w_ / 2, y + asc / 2 + 4 + dy, sc, al); continue
            im, ox, oy = word_sprite2(hw(i), fnt, hl, ease_out_cubic((k - 1) / 5) if hl else 0)
            paste(canvas, im, x + fnt.getlength(hw(i)) / 2 + (im.width / 2 - ox - fnt.getlength(hw(i)) / 2),
                  y + asc / 2 + dy + (im.height / 2 - oy - asc / 2), sc, al)

# fewer tells: three signs, bigger, one column
SIGNS2 = [(fo(60.17), "Guiones largos  —"), (fo(62.09), "Frases que «cantan»"), (fo(64.73), "Tono robótico")]
SIGN2_IM = [(t, chip(l, "", w=560)) for t, l in SIGNS2]
def scene_tells(f, f0):
    im = Image.new("RGBA", (W, VH), PANEL + (255,)); d = ImageDraw.Draw(im)
    if f < fo(59.0):
        s, a, dy = pop(f - f0); paste(im, heading("Funciona con cualquier IA"), 540, 110 + dy, s, a)
        items = [chip("Claude", icon_img=spark(46)), chip("ChatGPT", ""), chip("la que quieras", "")]
        for (t0, _, _), c, x in zip(TELLS, items, [220, 500, 820]):
            if f >= t0:
                s, a, dy = pop(f - t0); paste(im, c, x, 260 + dy, s, a)
        return im
    s, a, dy = pop(f - fo(59.0)); paste(im, heading("Adiós a las señales de IA"), 540, 70 + dy, s, a)
    for idx, (t0, c) in enumerate(SIGN2_IM):
        if f < t0: continue
        y = 185 + idx * 108; k = f - t0
        s, a, dy = pop(k); paste(im, c, 540, y + dy, s, a)
        if k > 6:
            p = ease_out_cubic((k - 6) / 6); x0 = 540 - c.width / 2 + 120
            d.line((x0, y, x0 + (c.width - 170) * p, y), fill=RED, width=6)
    return im

# money scene: no zeros -> rising chart first, then the real figures pop in
BIGF = font("InterDisplay-Black.otf", 130)
def num_img(txt, color=WHITE):
    t_ = Image.new("RGBA", (int(BIGF.getlength(txt)) + 40, 170), (0, 0, 0, 0))
    ImageDraw.Draw(t_).text((20, 10), txt, font=BIGF, fill=color); return t_
N300, NDASH, N500 = num_img("$300"), num_img("–", (120, 120, 126)), num_img("$500")
def chart(f, f0):
    w, h = 620, 210; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for gy in range(0, h, 52): d.line((0, gy, w, gy), fill=(46, 46, 50), width=2)
    pts = [(0, 190), (90, 170), (170, 176), (250, 140), (330, 120), (410, 128), (490, 80), (560, 52), (620, 20)]
    p = ease_io((f - f0) / 40); n = 1 + p * (len(pts) - 1); k = int(n); fr = n - k
    path = pts[:k] + ([(pts[k - 1][0] + (pts[min(k, len(pts) - 1)][0] - pts[k - 1][0]) * fr,
                        pts[k - 1][1] + (pts[min(k, len(pts) - 1)][1] - pts[k - 1][1]) * fr)] if k < len(pts) else [])
    if len(path) > 1: d.line(path, fill=RED, width=8, joint="curve")
    x, y = path[-1]; d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=RED)
    return im
_scene_cta_v1 = scene_cta
def scene_cta(f, f0):
    kmoney = f - fo(77.76); kcta = f - fo(85.36)
    if kmoney < 0 or kcta >= 0: return _scene_cta_v1(f, f0)
    im = Image.new("RGBA", (W, VH), PANEL + (255,))
    s, a, dy = pop(kmoney); paste(im, heading("Genera ingresos con IA"), 540, 80 + dy, s, a)
    k3, k5 = f - fo(82.40), f - fo(83.12)
    if k3 < 0:
        paste(im, chart(f, fo(77.76)), 540, 300, 1, min(1, kmoney / 4))
        return im
    s, a, dy = pop(k3, 6); paste(im, N300, 540 - 230, 270 + dy, s, a)
    if k5 >= 0:
        s, a, dy = pop(k5, 6); paste(im, NDASH, 540, 270, s, a); paste(im, N500, 540 + 230, 270 + dy, s, a)
    return im

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "NF", NF, "split", F_SPLIT, file=sys.stderr)
    render()
