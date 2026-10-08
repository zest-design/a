import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p2"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/02db0af6-1007_2.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P}/out.mp4"
PREVIEW = len(sys.argv) > 2
W, H, FPS = 1080, 1920, 30

RED = (229, 22, 34)
INK = (26, 26, 28)          # dark gray, almost black
GRAY = (120, 120, 126)
WHITE = (255, 255, 255)
BG = (255, 255, 255)
# chat box (sampled from the reference screenshot)
CB_BG = (32, 32, 31); CB_BORDER = (60, 60, 58); CB_TEXT = (236, 235, 228); CB_MUTED = (150, 148, 140)
CB_CHIP = (58, 58, 56); FIELD = (255, 120, 120)

FD = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FD + name, int(size))
FA = f"{S}/fa/fa-solid.ttf"
def fa(size): return ImageFont.truetype(FA, int(size))

# ---------------- cuts -------------------------------------------------------------
SIL = [(0.00, 1.02), (6.73, 7.68), (8.36, 8.55), (13.61, 15.13), (23.61, 24.21), (28.42, 28.74), (30.28, 30.61),
       (34.54, 34.72), (35.43, 35.86), (37.64, 37.81), (38.99, 39.12), (40.06, 40.46), (43.11, 43.23), (45.59, 45.87),
       (51.65, 52.17), (53.38, 53.54), (53.78, 54.06), (54.48, 55.08), (58.31, 58.50), (59.25, 59.42), (65.04, 65.44),
       (66.70, 67.30), (71.55, 71.95), (74.99, 75.87), (81.08, 81.30), (83.98, 84.25), (84.39, 84.72), (85.10, 85.53),
       (93.83, 94.26), (101.12, 101.37), (102.15, 102.49), (103.04, 103.24), (104.04, 104.19), (105.02, 105.18),
       (105.98, 106.13), (107.45, 107.64), (109.08, 109.51)]
END = 112.62
PAD = 0.04
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
CUTF = [fo(a) for a, b in KEEP]
def piece_index(f):
    k = 0
    for i, c in enumerate(CUTF):
        if c <= f: k = i
    return k

T_B, T_C = 15.13, 75.87          # ceiling part (prompt scene) / outro on camera
F_B, F_C = fo(T_B), fo(T_C)

# ---------------- word timings (whisper text aligned to parakeet onsets) -----------
PK = json.load(open(f"{P}/words.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (1.02, 6.76, "Claude puede arreglar toda tu vida financiera en tan solo un fin de semana si tú le pasas este prompt."),
    (7.67, 13.57, "Es un prompt preparado para construir riqueza desde cero, desde el punto en el que estás. Y ahí va."),
    (75.83, 81.03, "Si tú le pasas exactamente este prompt, verás que te va a dar una hoja de ruta para cambiar"),
    (81.30, 84.49, "tu vida financiera para siempre en un único fin"),
    (84.73, 85.19, "de semana."),
    (85.53, 93.88, "He preparado un PDF para ti con todo este paso a paso completo para que tú veas exactamente cómo hacerlo. Comenta aquí abajo FINANZAS"),
    (94.26, 102.30, "te lo voy a hacer llegar. Y si tú quieres aprender a generar ingresos con inteligencia artificial de 300 a 500 dólares todos los días,"),
    (102.46, 112.57, "también te he dejado aquí un vídeo preparado para que tú entiendas todo eso y cómo hacerlo paso a paso. Comenta aquí abajo FINANZAS que te envío el PDF y el vídeo."),
]
def align(s0, s1, text):
    ws = text.split()
    pk = [(w, t) for w, t, _ in PK if s0 - 0.35 <= t <= s1 + 0.1]
    a = [norm(w) for w in ws]; b = [norm(w) for w, _ in pk]
    times = [None] * len(ws)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = pk[blk.b + k][1]
    # fuzzy match leftovers by similarity inside opcodes
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            for k in range(i2 - i1):
                if j1 + k < j2: times[i1 + k] = pk[j1 + k][1]
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    anchors = [(-1, s0)] + known + [(len(ws), s1)]
    for i in range(len(ws)):
        if times[i] is None:
            lo = max(x for x in anchors if x[0] < i); hi = min(x for x in anchors if x[0] > i)
            times[i] = lo[1] + (hi[1] - lo[1]) * (i - lo[0]) / (hi[0] - lo[0])
    for i in range(1, len(times)):
        times[i] = max(times[i], times[i - 1] + 0.05)
    return list(zip(ws, times))
HOOKW = align(*SEGS[0]) + align(*SEGS[1])
OUTW = []
for sg in SEGS[2:]: OUTW += align(*sg)

# ---------------- generic helpers ---------------------------------------------------
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

# ---------------- talking head (A and C) -------------------------------------------
OFF_A, OFF_C = 0, 0           # push him down so text lives above his head
FADE = 170
fade_mask = np.ones((H, 1, 1), np.float32)
def head_frame(guy, f, off, z):
    if off == 0 and z == 1.0: return guy
    # zoom around the face, then shift down and blend the top into white
    cy = 760
    if z != 1.0:
        w, h = W / z, H / z; x0 = (W - w) / 2; y0 = min(max(cy - h / 2, 0), H - h)
        g = np.array(Image.fromarray(guy).resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h)))
    else: g = guy
    out = np.empty_like(g); out[:] = 255
    out[off:] = g[:H - off]
    ramp = np.clip((np.arange(H) - off) / FADE, 0, 1).astype(np.float32)[:, None, None]
    ramp = ramp * ramp * (3 - 2 * ramp)
    return (out.astype(np.float32) * ramp + 255 * (1 - ramp)).astype(np.uint8)

# hook typography: "small|big" phrases, *word = red box
HOOK = ["claude puede arreglar|toda tu vida *financiera", "en tan solo|un fin de *semana", "si tú le pasas|este *prompt",
        "es un prompt preparado para|construir *riqueza", "desde cero desde|el punto en el que estás", "|y ahí *va"]
HS = font("InterDisplay-SemiBold.otf", 58)
def fit_big(txt, mx=880, start=118):
    s = start
    while font("InterDisplay-Black.otf", s).getlength(txt) > mx and s > 60: s -= 4
    return font("InterDisplay-Black.otf", s)
def line_items(tokens, fnt, y, cx=520):
    gaps = [fnt.getlength(" ") + (22 if (a[1] or b[1]) else 0) for a, b in zip(tokens, tokens[1:])]
    tot = sum(fnt.getlength(w) for w, _, _ in tokens) + sum(gaps); x = cx - tot / 2; out = []
    for k, (w, hl, t) in enumerate(tokens):
        out.append((w, hl, t, x, y, fnt)); x += fnt.getlength(w) + (gaps[k] if k < len(gaps) else 0)
    return out
HOOK_L = []; wi = 0
for ph in HOOK:
    sm, bg_ = ph.split("|")
    def toks(s):
        global wi
        out = []
        for w in s.split():
            hl = w.startswith("*"); w = w.lstrip("*")
            out.append((w, hl, HOOKW[wi][1])); wi += 1
        return out
    st = toks(sm); bt = toks(bg_)
    fb = fit_big(" ".join(w for w, _, _ in bt))
    items = (line_items(st, HS, 236) if st else []) + line_items(bt, fb, 306 if st else 270)
    HOOK_L.append(dict(items=items, f0=fo((st or bt)[0][2])))
assert wi == len(HOOKW), (wi, len(HOOKW))
for k, L in enumerate(HOOK_L): L["f1"] = HOOK_L[k + 1]["f0"] if k + 1 < len(HOOK_L) else F_B
HOOK_BEATS = [fo(t) for L in HOOK_L for w, hl, t, *_ in L["items"] if hl]

def word_sprite(w, fnt, hl, box_p, color=INK):
    asc, desc = fnt.getmetrics(); tw = fnt.getlength(w); padx, pady = 16, 6
    im = Image.new("RGBA", (int(tw + 2 * padx + 40), int(asc + desc + 2 * pady + 40)), (0, 0, 0, 0))
    if hl and box_p > 0:
        bw = (tw + 2 * padx) * box_p; x0 = 20 + (tw + 2 * padx - bw) / 2
        ImageDraw.Draw(im).rounded_rectangle((x0, 20 + desc * 0.35, x0 + bw, im.height - 20 - desc * 0.15), 16, fill=RED)
    col = WHITE if (hl and box_p > 0.5) else color
    ImageDraw.Draw(im).text((20 + padx, 20 + pady), w, font=fnt, fill=col)
    return im, 20 + padx, 20 + pady
def hook_text(canvas, f):
    for L in HOOK_L:
        if not (L["f0"] <= f < L["f1"]): continue
        for w, hl, t, x, y, fnt in L["items"]:
            wf = fo(t)
            if f < wf: continue
            k = f - wf
            im, ox, oy = word_sprite(w, fnt, hl, ease_out_cubic((k - 1) / 5) if hl else 0)
            asc = fnt.getmetrics()[0]
            paste(canvas, im, x + fnt.getlength(w) / 2 + (im.width / 2 - ox - fnt.getlength(w) / 2),
                  y + asc / 2 + (1 - ease_out_cubic(k / 5)) * 24 + (im.height / 2 - oy - asc / 2),
                  scale=0.55 + 0.45 * ease_out_back(k / 5, 2.2), alpha=min(1.0, k / 2 + 0.2))
def beat_zoom(f):
    z = 0.0
    for b in HOOK_BEATS + OUT_BEATS:
        if b <= f: z = max(z, 0.06 * math.exp(-(f - b) / 6.0))
    return z

# outro captions (1-3 words, dark, red box on highlights)
HL = ["hoja de ruta", "vida financiera", "fin de semana", "pdf", "finanzas", "inteligencia artificial",
      "300 a 500 dólares", "vídeo"]
HL = [p.split() for p in HL]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(OUTW):
    hit = next((p for p in HL if [norm(w) for w, _ in OUTW[i:i + len(p)]] == [norm(x) for x in p]), None)
    if hit:
        g = OUTW[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [OUTW[i]]; i += 1; hl = False
        while i < len(OUTW) and len(g) < 3 and not PUNCT.search(g[-1][0]):
            if OUTW[i][1] - g[0][1] > 0.75 or sum(len(w) for w, _ in g) + len(OUTW[i][0]) > 15: break
            if any([norm(w) for w, _ in OUTW[i:i + len(p)]] == [norm(x) for x in p] for p in HL): break
            g.append(OUTW[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w for w, _ in g))
    txt = txt if txt.isupper() and len(txt) > 3 else txt.lower()
    if txt.lower() == "pdf": txt = "PDF"
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1]))
merged = []
for c in chunks:
    if merged and c["hl"] and not merged[-1]["hl"] and " " not in merged[-1]["txt"] and len(merged[-1]["txt"]) <= 3:
        p = merged.pop(); c = dict(c, txt=p["txt"] + " " + c["txt"], t0=p["t0"])
    merged.append(c)
chunks = merged
for c in chunks: c["f0"] = fo(c["t0"])
for k, c in enumerate(chunks): c["f1"] = min(chunks[k + 1]["f0"] if k + 1 < len(chunks) else NF, c["f0"] + 30)
OUT_BEATS = [c["f0"] for c in chunks if c["hl"]]
FC = font("InterDisplay-Bold.otf", 64)
def make_caption(txt, hl):
    tw = FC.getlength(txt); bb = FC.getbbox(txt); padx, pady = 22, 12
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if hl:
        im.alpha_composite(shadow_layer((w, h), (20, 20, w - 20, h - 20), 16, 8, 50, (0, 4)))
        d.rounded_rectangle((20, 20, w - 20, h - 20), 16, fill=RED)
    if not hl:
        g_ = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g_).text((w / 2, h / 2 - 2), txt, font=FC, fill=(0, 0, 0, 200), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, 200))
        im.alpha_composite(g_.filter(ImageFilter.GaussianBlur(7))); d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2 - 2), txt, font=FC, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"])

# outro badges (white card, red icon)
def make_badge(label, text, icon, big=False):
    k = 1.15 if big else 1.0
    fl = font("Inter-Bold.otf", 20 * k); ft = font("InterDisplay-Bold.otf", 38 * k); fi = fa(32 * k)
    hgt, ib, pad = int(96 * k), int(70 * k), 34
    tw = max(ft.getlength(text), sum(fl.getlength(c) + 2 for c in label))
    w = int(13 * k + ib + 22 * k + tw + 32 * k)
    im = Image.new("RGBA", (w + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (pad, pad, pad + w, pad + hgt), 26, 14, 55, (0, 8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + hgt), int(26 * k), fill=WHITE, outline=(232, 232, 236), width=2)
    ix, iy = pad + int(13 * k), pad + (hgt - ib) // 2
    d.rounded_rectangle((ix, iy, ix + ib, iy + ib), int(18 * k), fill=RED)
    d.text((ix + ib / 2, iy + ib / 2), icon, font=fi, fill=WHITE, anchor="mm")
    x = tx = ix + ib + int(22 * k)
    for ch in label: d.text((x, pad + int(16 * k)), ch, font=fl, fill=RED); x += fl.getlength(ch) + 2
    d.text((tx, pad + int(42 * k)), text, font=ft, fill=INK)
    return im
BADGES = [(79.0, 85.45, "EL RESULTADO", "Hoja de ruta · 12 meses", "", False),
          (85.45, 91.6, "TE LO REGALO", "PDF paso a paso completo", "", False),
          (91.6, 96.0, "COMENTA", "“FINANZAS” 👇".replace(" 👇", ""), "", True),
          (96.0, 102.4, "CON IA", "$300 – $500 por día", "", False),
          (102.4, 109.4, "EXTRA", "Vídeo paso a paso", "", False),
          (109.4, 999, "COMENTA “FINANZAS”", "Recibe el PDF + vídeo", "", True)]
badges = [dict(f0=fo(a), f1=min(fo(b), NF), im=make_badge(l, t, ic, bg), cta=bg) for a, b, l, t, ic, bg in BADGES]

# ---------------- prompt scene (B) -------------------------------------------------
SS = 2                                    # supersampling of the scene
BX0, BX1, BT = 60, 1020, 250              # chat box (scene coords at 1x)
PADX, PADT, LH, MAXL = 38, 34, 52, 8
FT = font("Inter-Regular.otf", 34 * SS)
PROMPT = [  # (src start, src end, text)  -- typed in sync with his voice
    (15.38, 23.50, "Actúa como un estratega de finanzas personales. Quiero construir múltiples fuentes de ingresos y reducir mi dependencia de una sola fuente de ingresos."),
    (24.04, 25.60, "\nAnaliza mis fuentes actuales: "),
    (26.80, 28.40, "[sueldo, freelance…]"),
    (28.74, 30.28, ", el capital que tengo disponible: "),
    (30.61, 32.40, "[$ en mi cuenta]"),
    (35.86, 38.95, " y el tiempo disponible por semana: [__ horas]."),
    (40.46, 51.60, "\nDiseña 7 fuentes de ingresos potenciales que se ajusten a mi situación, incluyendo salarios, inversiones, negocios secundarios, dividendos, ingresos por alquiler, productos digitales,"),
    (52.17, 53.75, " marketing de afiliados o servicios."),
    (55.08, 65.00, " Para cada fuente de ingresos incluye: dificultad de inicio, costo inicial, tiempo para que genere ingresos, nivel de riesgo, escalabilidad y orden de implementación recomendado."),
    (67.30, 74.90, "\nCrea una hoja de ruta de 12 meses y una checklist para hacer mi situación financiera más resiliente."),
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
# field (bracket) colouring
INFIELD = np.zeros(len(FULL) + 1, bool); d_ = 0
for k, ch in enumerate(FULL):
    if ch == "[": d_ = 1
    INFIELD[k] = d_ == 1
    if ch == "]": d_ = 0
# wrap the full prompt once: list of lines -> (start, end) char ranges
WRAPW = (BX1 - BX0 - 2 * PADX) * SS
LINES = []
pos = 0
for para in FULL.split("\n"):
    words_ = re.findall(r"\S+\s*", para)
    line_start = pos; line = ""
    for wd in words_:
        if FT.getlength((line + wd).rstrip()) > WRAPW and line:
            LINES.append((line_start, line_start + len(line))); line_start += len(line); line = wd
        else: line += wd
    LINES.append((line_start, line_start + len(line)))
    pos = line_start + len(line) + 1   # skip the newline
def line_of(n):
    for k, (a, b) in enumerate(LINES):
        if n <= b: return k
    return len(LINES) - 1

ICON = dict(plus="", mic="", down="", up="")
F_SM = font("Inter-Medium.otf", 27 * SS); F_SM2 = font("Inter-Regular.otf", 27 * SS)
def draw_box(d, n, send_p):
    nlines = 1 if n == 0 else line_of(n) + 1
    vis = min(nlines, MAXL); scroll = max(0, nlines - MAXL)
    top = BT * SS; th = vis * LH * SS
    bot = top + (PADT + 6) * SS + th + 110 * SS
    d.rounded_rectangle((BX0 * SS, top, BX1 * SS, bot), 30 * SS, fill=CB_BG, outline=CB_BORDER, width=2 * SS)
    tx, ty = (BX0 + PADX) * SS, top + PADT * SS
    cur_xy = (tx, ty)
    if n == 0:
        d.text((tx, ty), "¿En qué puedo ayudarte hoy?", font=FT, fill=CB_MUTED)
    else:
        for k in range(scroll, nlines):
            a, b = LINES[k]; b = min(b, n)
            if b <= a: cur_xy = (tx, ty + (k - scroll) * LH * SS); continue
            x = tx; y = ty + (k - scroll) * LH * SS
            # draw in runs of equal colour
            s = a
            while s < b:
                e = s
                while e < b and INFIELD[e] == INFIELD[s]: e += 1
                seg = FULL[s:e].replace("\n", "")
                d.text((x, y), seg, font=FT, fill=FIELD if INFIELD[s] else CB_TEXT)
                x += FT.getlength(seg); s = e
            cur_xy = (x, y)
    # caret
    cx, cy = cur_xy
    d.rectangle((cx + 3 * SS, cy + 4 * SS, cx + 6 * SS, cy + 42 * SS), fill=CB_TEXT)
    # bottom row
    by = bot - 62 * SS
    d.text((BX0 * SS + 50 * SS, by), ICON["plus"], font=fa(30 * SS), fill=CB_TEXT, anchor="mm")
    cx0 = BX0 * SS + 90 * SS
    d.rounded_rectangle((cx0, by - 30 * SS, cx0 + 270 * SS, by + 30 * SS), 14 * SS, fill=(44, 44, 42))
    d.rounded_rectangle((cx0 + 5 * SS, by - 25 * SS, cx0 + 110 * SS, by + 25 * SS), 11 * SS, fill=CB_CHIP, outline=(80, 80, 78), width=SS)
    d.text((cx0 + 57 * SS, by), "Chat", font=F_SM, fill=CB_TEXT, anchor="mm")
    d.text((cx0 + 190 * SS, by), "Cowork", font=F_SM2, fill=CB_MUTED, anchor="mm")
    rx = BX1 * SS - 40 * SS
    if n > 0:
        s = 1 - 0.18 * math.sin(min(1, send_p) * math.pi) if send_p > 0 else 1
        r = 30 * SS * s; col = RED
        d.rounded_rectangle((rx - 2 * r + 8 * SS, by - r, rx + 8 * SS, by + r), 14 * SS, fill=col)
        d.text((rx - r + 8 * SS, by), ICON["up"], font=fa(28 * SS), fill=WHITE, anchor="mm")
        rx -= 2 * r + 20 * SS
    else:
        d.text((rx, by), ICON["down"], font=fa(18 * SS), fill=CB_MUTED, anchor="mm"); rx -= 40 * SS
        for k_, hh in enumerate([10, 22, 32, 22, 12]):
            x_ = rx - k_ * 9 * SS
            d.rounded_rectangle((x_ - 2 * SS, by - hh / 2 * SS, x_ + 2 * SS, by + hh / 2 * SS), 2 * SS, fill=CB_TEXT)
        rx -= 60 * SS
    d.text((rx, by), ICON["mic"], font=fa(30 * SS), fill=CB_TEXT, anchor="mm"); rx -= 50 * SS
    d.text((rx, by), "Medio", font=F_SM2, fill=CB_MUTED, anchor="rm"); rx -= F_SM2.getlength("Medio") + 16 * SS
    d.text((rx, by), "Sonnet 5.5", font=F_SM, fill=(200, 198, 190), anchor="rm")
    return (cx / SS, cy / SS + 22), bot / SS

# animation cards (white, under the box; kept left of the IG buttons column)
AX0, AX1 = 60, 868
def card_base(w, h, r=24):
    im = Image.new("RGBA", ((w + 60) * SS, (h + 60) * SS), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (30 * SS, 30 * SS, (30 + w) * SS, (30 + h) * SS), r * SS, 14 * SS, 45, (0, 8 * SS)))
    ImageDraw.Draw(im).rounded_rectangle((30 * SS, 30 * SS, (30 + w) * SS, (30 + h) * SS), r * SS, fill=WHITE, outline=(230, 230, 234), width=2 * SS)
    return im
FT_T = font("InterDisplay-Bold.otf", 36 * SS); FT_S = font("Inter-Regular.otf", 27 * SS); FT_H = font("InterDisplay-Bold.otf", 40 * SS)
FT_C = font("InterDisplay-SemiBold.otf", 29 * SS)
def info_card(title, sub, icon, w=AX1 - AX0, h=124):
    im = card_base(w, h); d = ImageDraw.Draw(im); o = 30 * SS
    d.rounded_rectangle((o + 20 * SS, o + 22 * SS, o + 100 * SS, o + 102 * SS), 20 * SS, fill=RED)
    d.text((o + 60 * SS, o + 62 * SS), icon, font=fa(36 * SS), fill=WHITE, anchor="mm")
    d.text((o + 124 * SS, o + 26 * SS), title, font=FT_T, fill=INK)
    d.text((o + 124 * SS, o + 74 * SS), sub, font=FT_S, fill=GRAY)
    return im
def chip(label, icon, w):
    im = card_base(w, 84, 20); d = ImageDraw.Draw(im); o = 30 * SS
    d.rounded_rectangle((o + 14 * SS, o + 14 * SS, o + 70 * SS, o + 70 * SS), 15 * SS, fill=RED)
    d.text((o + 42 * SS, o + 42 * SS), icon, font=fa(26 * SS), fill=WHITE, anchor="mm")
    d.text((o + 86 * SS, o + 42 * SS), label, font=FT_C, fill=INK, anchor="lm")
    return im
def title_img(txt, accent=None):
    im = Image.new("RGBA", (int(FT_H.getlength(txt)) + 40 * SS, 70 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((0, 10 * SS), txt, font=FT_H, fill=INK)
    return im

def tm(t): return fo(t)
SET1 = [(25.75, "Tus fuentes actuales", "Sueldo, freelance o lo que sea", ""),
        (28.80, "Capital disponible", "Lo que tienes en la cuenta", ""),
        (35.90, "Tiempo por semana", "En horas", "")]
SET1_IM = [(tm(t), info_card(a, b, ic)) for t, a, b, ic in SET1]
CHIPS = [(46.45, "Salario", ""), (47.09, "Inversiones", ""), (47.73, "Negocios secundarios", ""),
         (48.85, "Dividendos", ""), (49.49, "Alquiler", ""), (50.77, "Productos digitales", ""),
         (52.27, "Afiliados", ""), (53.63, "Servicios", "")]
CW2 = (AX1 - AX0 - 18) // 2
CHIPS_IM = [(tm(t), chip(l, ic, CW2)) for t, l, ic in CHIPS]
ROWS = [(57.23, "Dificultad de inicio", ""), (58.43, "Costo inicial", ""), (59.71, "Tiempo para generar ingresos", ""),
        (61.07, "Nivel de riesgo", ""), (62.19, "Escalabilidad", ""), (63.20, "Orden de implementación", "")]
ROWS_IM = [(tm(t), chip(l, ic, AX1 - AX0)) for t, l, ic in ROWS]
T_SET1 = title_img("Completa tus datos"); T_CH = title_img("7 fuentes de ingresos"); T_RW = title_img("Para cada fuente:")
GROUPS = [  # (start, end, kind)
    (tm(25.70), tm(39.10), "set1"), (tm(45.80), tm(54.90), "chips"), (tm(56.90), tm(65.40), "rows"), (tm(67.60), F_C, "road")]
LABELS = [(tm(39.12), tm(40.46), "le vas a decir"), (tm(65.44), tm(67.30), "por último, le escribes")]
FL = font("InterDisplay-SemiBold.otf", 40 * SS)
def label_img(txt):
    w = int(FL.getlength(txt) + 120 * SS)
    im = Image.new("RGBA", (w, 90 * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((40 * SS, 45 * SS), "", font=fa(32 * SS), fill=RED, anchor="mm")
    d.text((80 * SS, 45 * SS), txt, font=FL, fill=INK, anchor="lm")
    return im
LABELS = [(a, b, label_img(t)) for a, b, t in LABELS]

def road_card(f):
    f0 = tm(67.70); w = AX1 - AX0
    im = card_base(w, 230); d = ImageDraw.Draw(im); o = 30 * SS
    d.text((o + 30 * SS, o + 26 * SS), "Hoja de ruta · 12 meses", font=FT_T, fill=INK)
    p = ease_io((f - f0) / 75)
    x0, x1, y = o + 50 * SS, o + (w - 50) * SS, o + 136 * SS
    d.rounded_rectangle((x0, y - 5 * SS, x1, y + 5 * SS), 5 * SS, fill=(234, 234, 238))
    d.rounded_rectangle((x0, y - 5 * SS, x0 + (x1 - x0) * p, y + 5 * SS), 5 * SS, fill=RED)
    for k in range(12):
        x = x0 + (x1 - x0) * k / 11; on = p >= k / 11 - 1e-6
        r = (13 if k in (0, 5, 11) else 9) * SS
        d.ellipse((x - r, y - r, x + r, y + r), fill=RED if on else WHITE, outline=RED if on else (210, 210, 216), width=3 * SS)
        if k in (0, 5, 11):
            d.text((x, y + 44 * SS), f"Mes {k + 1}", font=FT_S, fill=INK if on else GRAY, anchor="mm")
    return im
def check_card(f):
    f0 = tm(70.30); w = AX1 - AX0
    im = card_base(w, 200); d = ImageDraw.Draw(im); o = 30 * SS
    d.text((o + 30 * SS, o + 24 * SS), "Checklist", font=FT_T, fill=INK)
    for k in range(3):
        y = o + (92 + k * 40) * SS; on = f >= f0 + 8 + k * 9
        d.rounded_rectangle((o + 30 * SS, y - 15 * SS, o + 60 * SS, y + 15 * SS), 8 * SS, fill=RED if on else WHITE, outline=RED if on else (200, 200, 206), width=3 * SS)
        if on: d.text((o + 45 * SS, y), "", font=fa(18 * SS), fill=WHITE, anchor="mm")
        d.rounded_rectangle((o + 80 * SS, y - 9 * SS, o + (80 + [420, 340, 470][k]) * SS, y + 9 * SS), 9 * SS, fill=(236, 236, 240))
    return im
SHIELD = info_card("Finanzas más resilientes", "Plan sólido, paso a paso", "")

def pop(k, n=7):  # scale/alpha/offset for an element appearing k frames ago
    return 0.7 + 0.3 * ease_out_back(k / n), min(1, k / 3 + 0.2), (1 - ease_out_cubic(k / n)) * 40

def draw_group(sc, f):
    for g0, g1, kind in GROUPS:
        if not (g0 <= f < g1 + 8): continue
        out = 1 - ease_out_cubic((f - g1) / 8) if f >= g1 else 1.0
        y = 960
        if kind == "set1":
            for k, (t0, im) in enumerate(SET1_IM):
                if f < t0: continue
                s, a, dy = pop(f - t0)
                paste(sc, im, (AX0 - 30) * SS + im.width / 2, (y + k * 150 - 30) * SS + im.height / 2 + (dy + (1 - out) * 60) * SS, s, a * out)
            paste(sc, T_SET1, AX0 * SS, (y - 80) * SS, alpha=min(1, (f - g0) / 5) * out, center=False)
        elif kind == "chips":
            paste(sc, T_CH, AX0 * SS, (y - 80) * SS, alpha=min(1, (f - g0) / 5) * out, center=False)
            for k, (t0, im) in enumerate(CHIPS_IM):
                if f < t0: continue
                s, a, dy = pop(f - t0)
                cx = AX0 + (k % 2) * (CW2 + 18); cy = y + (k // 2) * 104
                paste(sc, im, (cx - 30) * SS + im.width / 2, (cy - 30) * SS + im.height / 2 + (dy + (1 - out) * 60) * SS, s, a * out)
        elif kind == "rows":
            paste(sc, T_RW, AX0 * SS, (y - 80) * SS, alpha=min(1, (f - g0) / 5) * out, center=False)
            for k, (t0, im) in enumerate(ROWS_IM):
                if f < t0: continue
                s, a, dy = pop(f - t0)
                paste(sc, im, (AX0 - 30) * SS + im.width / 2, (y + k * 90 - 30) * SS + im.height / 2 + (dy + (1 - out) * 60) * SS, s, a * out)
        elif kind == "road":
            im = road_card(f); s, a, dy = pop(f - g0)
            paste(sc, im, (AX0 - 30) * SS + im.width / 2, (y - 60 - 30) * SS + im.height / 2 + dy * SS, s, a)
            if f >= tm(70.30):
                im = check_card(f); s, a, dy = pop(f - tm(70.30))
                paste(sc, im, (AX0 - 30) * SS + im.width / 2, (y + 190 - 30) * SS + im.height / 2 + dy * SS, s, a)
            if f >= tm(73.30):
                s, a, dy = pop(f - tm(73.30))
                paste(sc, SHIELD, (AX0 - 30) * SS + SHIELD.width / 2, (y + 410 - 30) * SS + SHIELD.height / 2 + dy * SS, s, a)

# camera schedule (src times) -> modes
MODES = [(15.13, "type"), (25.70, "wide"), (39.10, "label"), (40.46, "type"), (45.80, "wide"), (54.50, "type"),
         (56.90, "wide"), (65.40, "label"), (67.30, "wide"), (74.99, "end")]
MODES = [(fo(t), md) for t, md in MODES]
def mode_at(f):
    md = MODES[0][1]
    for f0, x in MODES:
        if f >= f0: md = x
    return md

SCENE_BG = Image.new("RGBA", (W * SS, H * SS), BG + (255,))
# subtle dotted texture
_d = ImageDraw.Draw(SCENE_BG)
for yy in range(0, H * SS, 48 * SS):
    for xx in range(0, W * SS, 48 * SS):
        _d.ellipse((xx - 2 * SS, yy - 2 * SS, xx + 2 * SS, yy + 2 * SS), fill=(236, 236, 240))
BOX_SHADOW = None

def render_scene(f):
    sc = SCENE_BG.copy()
    n = chars_at(f)
    send_p = (f - tm(74.70)) / 8 if f >= tm(74.70) else 0
    lay = Image.new("RGBA", sc.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cur, bot = draw_box(d, n, send_p)
    sh = shadow_layer((W, H), (BX0, BT, BX1, int(bot)), 30, 18, 70, (0, 14)).resize(sc.size, Image.BILINEAR)
    sc.alpha_composite(sh); sc.alpha_composite(lay)
    for a, b, im in LABELS:
        if a <= f < b + 6:
            k = f - a; o = 1 - ease_out_cubic((f - b) / 6) if f >= b else 1
            s, al, dy = pop(k)
            paste(sc, im, 540 * SS, (930 + dy) * SS, s, al * o)
    draw_group(sc, f)
    return sc, cur, bot

class Cam:
    def __init__(s): s.x, s.y, s.z = 540.0, 960.0, 1.0; s.init = False; s.tx = None
cam = Cam()
def cam_target(f, cur, bot):
    md = mode_at(f)
    if md == "type":
        z = 1.45
        left, right = BX0 + 540 / z - 14, BX1 - 540 / z + 14
        if cam.tx is None: cam.tx = left
        view_r = cam.tx + 540 / z - 70; view_l = cam.tx - 540 / z + 70
        if cur[0] > view_r: cam.tx = right
        elif cur[0] < view_l: cam.tx = left
        return cam.tx, cur[1] + 120, z
    cam.tx = None
    if md == "label": return 540, (BT + 980) / 2 + 40, 1.12
    if md == "end": return 540, (BT + bot) / 2 + 20, 1.12
    return 540, 930, 1.0
def cam_sample(sc, x, y, z):
    # scene point (x, y) maps to output (540, 900); zoom z
    ax, ay = 540, 900
    a = 1 / z
    x0 = x - ax * a; y0 = y - ay * a
    return sc.transform((W, H), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR,
                        fillcolor=BG + (255,))

def scene_frame(f):
    sc, cur, bot = render_scene(f)
    tx, ty, tz = cam_target(f, cur, bot)
    if not cam.init: cam.x, cam.y, cam.z = tx, ty, tz; cam.init = True
    px, py, pz = cam.x, cam.y, cam.z
    k = 0.2
    cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k; cam.z += (tz - cam.z) * k
    mv = math.hypot((cam.x - px) * cam.z, (cam.y - py) * cam.z) + abs(cam.z - pz) * 900
    nsamp = 1 if mv < 6 else min(7, 2 + int(mv / 9))
    if nsamp == 1:
        img = cam_sample(sc, cam.x, cam.y, cam.z)
    else:
        acc = None
        for i in range(nsamp):
            u = i / (nsamp - 1)
            s = np.asarray(cam_sample(sc, px + (cam.x - px) * u, py + (cam.y - py) * u, pz + (cam.z - pz) * u), np.float32)
            acc = s if acc is None else acc + s
        img = Image.fromarray((acc / nsamp).astype(np.uint8))
    # entry from the hook
    k = f - F_B
    if k < 10:
        e = ease_out_cubic(k / 10)
        canvas = Image.new("RGBA", (W, H), BG + (255,))
        img2 = img.resize((W, H)).copy()
        paste(canvas, img2, 540, 960 + (1 - e) * 260, scale=0.85 + 0.15 * e, alpha=e)
        img = canvas
    return img

# ---------------- audio ------------------------------------------------------------
SR = 48000
def sfx_track(whoosh_f, pop_f, keys):
    rng = np.random.default_rng(7)
    n = int(0.34 * SR); t = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n); y = 0.0
    for k in range(n):
        c = 0.03 + 0.25 * math.sin(math.pi * k / n) ** 2; y += c * (noise[k] - y); out[k] = y
    whoosh = out / np.abs(out).max() * np.sin(np.pi * np.clip(t / 0.34, 0, 1)) ** 1.6 * 0.2
    n2 = int(0.08 * SR); t2 = np.arange(n2) / SR
    popw = np.sin(2 * np.pi * np.cumsum(950 * np.exp(-t2 * 22) + 260) / SR) * np.exp(-t2 * 45) * 0.26
    n3 = int(0.018 * SR); t3 = np.arange(n3) / SR
    trk = np.zeros(int((TOTAL + 1) * SR))
    for f in whoosh_f:
        s = max(0, int((f / FPS - 0.12) * SR)); trk[s:s + len(whoosh)] += whoosh[:len(trk) - s]
    for f in pop_f:
        s = int(f / FPS * SR); trk[s:s + len(popw)] += popw[:len(trk) - s]
    for tsec in keys:
        click = rng.standard_normal(n3) * np.exp(-t3 * 380) * rng.uniform(0.035, 0.06)
        click = np.convolve(click, [0.5, 0.5], "same")
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
    keys = []
    prev = 0
    for f in range(F_B, F_C):
        n = chars_at(f)
        for c in range(prev, n):
            if FULL[c] not in " \n" and c % 2 == 0: keys.append(f / FPS + (c - prev) / max(1, n - prev) / FPS)
        prev = n
    pops = [tm(t) for t, *_ in SET1] + [tm(t) for t, *_ in CHIPS] + [tm(t) for t, *_ in ROWS] + \
           [b["f0"] for b in badges] + [tm(70.3), tm(73.3), tm(74.7)] + [a for a, _, _ in LABELS]
    whooshes = [F_B, F_C] + [g[0] for g in GROUPS] + [f0 for f0, md in MODES if f0 > F_B]
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
        in_scene = F_B <= f < F_C
        if want is not None and f not in want and not (in_scene and any(0 <= w - f < 12 for w in want)):
            if f > max(want): break
            continue
        pi = piece_index(f)
        if in_scene:
            canvas = scene_frame(f).convert("RGBA")
        elif f < F_B:
            z = 1.0
            canvas = Image.fromarray(head_frame(guy, f, OFF_A, z)).convert("RGBA")
            hook_text(canvas, f)
        else:
            k = f - F_C
            z = 1.0
            canvas = Image.fromarray(head_frame(guy, f, OFF_C, z)).convert("RGBA")
            for b in badges:
                if b["f0"] <= f < b["f1"]:
                    kk = f - b["f0"]; left = b["f1"] - f
                    a = min(1, kk / 4) * min(1, left / 4)
                    sc = (0.7 + 0.3 * ease_out_back(kk / 8)) * ((1 + 0.03 * math.sin(kk / FPS * 2 * math.pi * 1.3)) if b["cta"] else 1)
                    paste(canvas, b["im"], 500, 1310 + (1 - ease_out_cubic(kk / 8)) * 20, scale=sc, alpha=a)
            for c in chunks:
                if not (c["f0"] <= f < c["f1"]): continue
                kk = f - c["f0"]
                paste(canvas, c["im"], 500, 1450 + (1 - ease_out_cubic(kk / 5)) * 10,
                      scale=0.86 + 0.14 * ease_out_back(kk / 5), alpha=min(1, 0.35 + kk / 3))
        if want is not None and f not in want: continue
        out = np.array(canvas.convert("RGB"))
        if PREVIEW: Image.fromarray(out).save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    gp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "NF", NF, "F_B", F_B, "F_C", F_C, file=sys.stderr)
    render()
