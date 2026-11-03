import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p20"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/a40d74af-B0DE593B-4430-4E33-82FF-2A27080FA3F2_1.mp4"
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
SIL = [(0.00, 0.87), (2.11, 2.25), (3.34, 3.46), (4.12, 4.33), (5.26, 5.38), (5.65, 5.78), (10.73, 11.00), (11.11, 11.26), (11.83, 12.27),
       (12.67, 12.92), (14.21, 14.50), (16.32, 16.47), (17.16, 17.46), (19.05, 19.35), (20.73, 21.06), (23.86, 24.04), (26.78, 27.16),
       (29.15, 29.28), (31.00, 31.13), (31.15, 31.88), (33.04, 33.17), (33.42, 33.60), (35.61, 35.74), (36.65, 37.17), (37.60, 37.81),
       (38.43, 38.78), (39.59, 39.84), (39.92, 40.04), (40.90, 41.08), (43.40, 43.61), (43.76, 45.72), (47.16, 47.36), (47.64, 48.68),
       (50.87, 51.05), (51.38, 51.64), (51.77, 51.91), (52.41, 52.69), (53.07, 53.70), (58.94, 59.23), (61.12, 61.27), (61.45, 61.63)]
END = 61.80; PAD = 0.04
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
    (0.87, 5.26, "De un simple PDF, Claude me ha creado esto de una manera totalmente sencilla."),
    (5.78, 10.73, "Ya no es solo entregar un PDF para que el cliente monte un mueble. Le podemos pasar una web"),
    (11.00, 12.67, "totalmente interactiva,"),
    (12.92, 20.73, "que le puede medir, que le puede ver el resultado final, que le puede acompañar y tener un servicio mucho mejor a la hora de montar."),
    (21.06, 31.13, "Si tú tienes una tienda, si tú conoces a alguien que tiene una tienda o incluso tú quieres dar este servicio a otras personas, yo te voy a enseñar ahora mismo cómo crear esto en minutos para que tú lo puedas hacer."),
    (31.88, 36.65, "Lo primero que tienes que hacer es ir a Claude, pasar el PDF y simplemente decirle: transforma"),
    (37.17, 43.76, "este manual en una web totalmente interactuable mostrando el paso a paso completo en 3D."),
    (45.72, 53.07, "Con esa simple instrucción, Claude va a hacer que ese PDF se convierta en esa web para ti, totalmente gratis."),
    (53.70, 61.80, "He preparado un PDF con un paso a paso completo. Si tú quieres aprender esto, comenta aquí MUEBLE, que te lo haré llegar para que tú puedas empezar a hacer eso hoy mismo."),
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
HL = [["MUEBLE"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("MUEBLE"): return ["MUEBLE"]
    return next((p for p in HL if p != ["MUEBLE"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "MUEBLE"
    if not hl: txt = txt.lower().replace("pdf", "PDF").replace("3d", "3D").replace("claude", "Claude")
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

# ---------------- audio ------------------------------------------------------------
SR = 48000
def sfx(events):
    rng = np.random.default_rng(9); trk = np.zeros(int((TOTAL + 1) * SR))
    def add(sig, t):
        s = int(t * SR); e = min(len(trk), s + len(sig)); trk[s:e] += sig[:e - s]
    n = int(0.42 * SR); t = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n); y = 0.0
    for k in range(n):
        cc = 0.02 + 0.18 * math.sin(math.pi * k / n) ** 2; y += cc * (noise[k] - y); out[k] = y
    # soft swipe (option A chosen by the user): very low-passed air, short and quiet - replaces the wind-like whoosh
    def _lp(x, fc):
        al = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s_ = 0.0
        for i_ in range(len(x)): s_ = (1 - al) * x[i_] + al * s_; y[i_] = s_
        return y
    nA = int(0.26 * SR); tA = np.arange(nA) / SR; rA = np.random.default_rng(3)
    xA = _lp(_lp(rA.standard_normal(nA), 700), 700); whoosh = xA / np.abs(xA).max() * np.sin(np.pi * tA / 0.26) ** 2 * 0.06
    n2 = int(0.16 * SR); t2 = np.arange(n2) / SR   # soft low "pluck" for pop-ins (no high clicks)
    pluck = (np.sin(2 * np.pi * 330 * t2) * 0.6 + np.sin(2 * np.pi * 495 * t2) * 0.25) * (1 - np.exp(-t2 * 400)) * np.exp(-t2 * 26) * 0.07
    n4 = int(1.4 * SR); t4 = np.arange(n4) / SR
    boom = np.sin(2 * np.pi * (52 + 30 * np.exp(-t4 * 8)) * t4) * np.exp(-t4 * 3.2) * 0.32 + rng.standard_normal(n4) * np.exp(-t4 * 18) * 0.04
    pad = sum(np.sin(2 * np.pi * fq * t4) for fq in (440, 554.4, 659.3)) * np.exp(-t4 * 2.2) * (1 - np.exp(-t4 * 30)) * 0.02
    for kind, tt in events:
        if kind == "whoosh": add(whoosh, max(0, tt - 0.05))
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


# ================= Split screen: 3D assembly-manual web clip on top (looped), presenter below =================
BROLL = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/8e3a4e4f-ssstwitter.com_1792429007976_1.mp4"
TOP = 830                       # top panel height; clip is 1080x608 sitting at the bottom of it (clear of the IG top bar)
CLIP_W, CLIP_H = 980, 551; CLIP_X, CLIP_Y = 50, 262   # inside the IG safe area, rounded like a card
_m = Image.new("L", (CLIP_W, CLIP_H), 0); ImageDraw.Draw(_m).rounded_rectangle((0, 0, CLIP_W - 1, CLIP_H - 1), 26, fill=255)
CLIP_MASK = (np.asarray(_m, np.float32) / 255.0)[..., None]
SHIFT = 290                     # bottom panel shows his face centred
CAP_SPLIT, CAP_FULL = TOP - 22, 470
TRANS = 9
KEY = next(c for c in chunks if c["key"])
F_SPLIT1 = fo(53.70)            # 'He preparado un PDF': back to him alone, captions on top
BG = np.zeros((TOP, W, 3), np.uint8) + np.array([14, 14, 16], np.uint8)
BROLL_VOL = 0.04                # clip audio kept very low, just a subtle bed


# ================= Claude chat (dark, Spanish UI) shown in the top card from "Lo primero que tienes que hacer" =================
F_CHAT = fo(31.88); F_SEND = fo(45.72); F_ART = fo(49.00)
T_PDF = fo(33.60); T_TY0, T_TY1 = fo(35.84), fo(43.40)
PROMPT = "Transforma este manual en una web totalmente interactuable mostrando el paso a paso completo en 3D."
CW, CH = CLIP_W, CLIP_H                      # chat window = same card as the clip
IX0, IX1, ITOP = 70, CW - 70, 236            # composer box (logical px)
def pdf_chip(w=300, h=64):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), 14 * SS, fill=(52, 51, 49), outline=CB_BORDER, width=2 * SS)
    d.rounded_rectangle((12 * SS, 12 * SS, 52 * SS, 52 * SS), 9 * SS, fill=(200, 64, 52))
    d.text((32 * SS, 32 * SS), "PDF", font=font("Inter-Bold.otf", 13 * SS), fill=WHITE, anchor="mm")
    d.text((66 * SS, 22 * SS), "manual_billy.pdf", font=font("Inter-Medium.otf", 20 * SS), fill=CB_TEXT, anchor="lm")
    d.text((66 * SS, 44 * SS), "PDF · 24 páginas", font=font("Inter-Regular.otf", 16 * SS), fill=CB_MUTED, anchor="lm")
    return im
PDF_CHIP = pdf_chip()
def chat_home(f):
    sc = Image.new("RGBA", (CW * SS, CH * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    sp = spark(44 * SS); g = "Buenas tardes"; gf = serif(50 * SS)
    gw = sp.width + 18 * SS + gf.getlength(g); gx = (CW * SS - gw) / 2; gy = 118 * SS
    sc.alpha_composite(sp, (int(gx), int(gy - sp.height / 2))); d.text((gx + sp.width + 18 * SS, gy), g, font=gf, fill=(232, 230, 222), anchor="lm")
    if f >= T_PDF:   # attachment card pops into the composer
        k = f - T_PDF; s_ = 0.7 + 0.3 * ease_out_back(min(1, k / 6))
        ch = PDF_CHIP.resize((int(PDF_CHIP.width * s_), int(PDF_CHIP.height * s_)))
        sc.alpha_composite(ch, (int(IX0 * SS), int((ITOP - 74) * SS + (PDF_CHIP.height - ch.height) / 2)))
    n = 0 if f < T_TY0 else min(len(PROMPT), int(len(PROMPT) * (f - T_TY0 + 1) / max(1, T_TY1 - T_TY0)))
    draw_input(d, sc, IX0, IX1, ITOP * SS, PROMPT, n, (-1, -1), "¿En qué puedo ayudarte hoy?", n > 0 and f < F_SEND - 3,
               (f - (F_SEND - 6)) / 6 if f >= F_SEND - 6 else 0)
    return sc
CONV_H = 980                                   # conversation scene is taller; the camera scrolls to the artifact
def chat_conv(f, clip):
    sc = Image.new("RGBA", (CW * SS, CONV_H * SS), PAGE + (255,)); d = ImageDraw.Draw(sc)
    k = f - F_SEND; e = ease_out_cubic(k / 8)
    fb = font("Inter-Regular.otf", 29 * SS); lines = wrap(PROMPT, fb, 640 * SS)
    bw = max(fb.getlength(l) for l in lines) + 52 * SS; bh = len(lines) * 42 * SS + 34 * SS
    bx1 = (CW - 40) * SS; by0 = int((30 + (1 - e) * 40) * SS)
    sc.alpha_composite(PDF_CHIP, (int(bx1 - PDF_CHIP.width), by0)); by0 += PDF_CHIP.height + 10 * SS
    d.rounded_rectangle((bx1 - bw, by0, bx1, by0 + bh), 22 * SS, fill=BUBBLE)
    for j, l in enumerate(lines): d.text((bx1 - bw + 26 * SS, by0 + 17 * SS + j * 42 * SS), l, font=fb, fill=CB_TEXT)
    ry = by0 + bh + 36 * SS
    sc.alpha_composite(spark(38 * SS), (int(40 * SS), int(ry)))
    resp = ["¡Listo! Convertí tu manual en una web", "interactiva en 3D, paso a paso:"]
    shown = max(0, int((f - F_SEND - 8) * 3.4)); acc = 0
    for j, l in enumerate(resp):
        d.text((96 * SS, ry + 19 * SS + j * 44 * SS), l[:max(0, shown - acc)], font=font("Inter-Regular.otf", 30 * SS), fill=(226, 224, 216), anchor="lm"); acc += len(l)
    if f >= F_ART and clip is not None:   # artifact card with the live 3D web inside
        ka = f - F_ART; pa = ease_out_back(min(1, ka / 8))
        aw, ah = 900, 506; ax0 = (CW - aw) // 2; ay0 = int(ry / SS + 112)
        card_ = Image.new("RGBA", (aw * SS, (ah + 56) * SS), (0, 0, 0, 0)); dc = ImageDraw.Draw(card_)
        dc.rounded_rectangle((0, 0, aw * SS - 1, (ah + 56) * SS - 1), 18 * SS, fill=(38, 37, 35), outline=CB_BORDER, width=2 * SS)
        dc.text((22 * SS, 28 * SS), "Manual interactivo 3D · BILLY", font=font("Inter-SemiBold.otf", 24 * SS), fill=CB_TEXT, anchor="lm")
        dc.text((aw * SS - 22 * SS, 28 * SS), "Artefacto", font=font("Inter-Regular.otf", 20 * SS), fill=CB_MUTED, anchor="rm")
        frame = Image.fromarray(clip).resize(((aw - 20) * SS, (ah - 10) * SS), Image.BILINEAR)
        card_.paste(frame, (10 * SS, 56 * SS))
        if pa < 1: card_ = card_.resize((max(1, int(card_.width * pa)), max(1, int(card_.height * pa))))
        sc.alpha_composite(card_, (int((ax0 + aw / 2) * SS - card_.width / 2), int(ay0 * SS)))
    return sc
ART_CY = 0
def cam_state(f):
    if f < F_SEND:
        p = ease_io((f - (T_TY0 - 6)) / 12) if f >= T_TY0 - 6 else 0.0      # zoom in on the prompt, centred
        return CW / 2, CH / 2 + (318 - CH / 2) * p, 1 + 0.10 * p
    p = 1 - ease_io((f - F_SEND) / 10)
    y = CH / 2 + (318 - CH / 2) * p
    q = ease_io((f - F_ART) / 14) if f >= F_ART else 0.0                  # scroll down to the artifact
    return CW / 2, y + (690 - y) * q, 1 + 0.10 * p
CMASK = Image.new("L", (CW, CH), 0); ImageDraw.Draw(CMASK).rounded_rectangle((0, 0, CW - 1, CH - 1), 26, fill=255)
def chat_view(f, clip):
    sc = chat_home(f) if f < F_SEND else chat_conv(f, clip)
    def sample(x, y, z):
        a = 1 / z; x0 = x - CW / 2 * a; y0 = y - CH / 2 * a
        return sc.transform((CW, CH), Image.AFFINE, (a * SS, 0, x0 * SS, 0, a * SS, y0 * SS), resample=Image.BILINEAR, fillcolor=PAGE + (255,))
    x1, y1, z1 = cam_state(f); x0_, y0_, z0 = cam_state(f - 1)
    mv = math.hypot((x1 - x0_) * z1, (y1 - y0_) * z1) + abs(z1 - z0) * 900
    ns = 1 if mv < 2 else min(7, 2 + int(mv / 5))
    if ns == 1: v = sample(x1, y1, z1)
    else:   # light motion blur while the camera moves
        acc = None
        for q in range(ns):
            u = q / (ns - 1); s_ = np.asarray(sample(x0_ + (x1 - x0_) * u, y0_ + (y1 - y0_) * u, z0 + (z1 - z0) * u), np.float32)
            acc = s_ if acc is None else acc + s_
        v = Image.fromarray((acc / ns).astype(np.uint8)).convert("RGBA")
    return v

def broll_cmd():
    return ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", BROLL, "-vf", f"fps={FPS},scale={CLIP_W}:{CLIP_H}:flags=lanczos,format=rgb24", "-f", "rawvideo", "-"]

def audio_mix(events):
    sfx(events)
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.008:.4f}:d=0.008[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    endt = F_CHAT / FPS
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume={BROLL_VOL},atrim=0:{endt:.3f},afade=t=out:st={endt - 0.6:.3f}:d=0.6[b];" \
        f"[1:a]volume=1.0[s];[v][s][b]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{P}/sfx.wav", "-stream_loop", "-1", "-i", BROLL, "-filter_complex", fc, "-map", "[o]", "-ar", "48000",
                    f"{P}/voice.wav"], check=True)

def events():
    return [("whoosh", F_CHAT / FPS), ("pluck", T_PDF / FPS), ("pluck", F_SEND / FPS), ("pluck", F_ART / FPS), ("whoosh", F_SPLIT1 / FPS), ("boom", KEY["f0"] / FPS)]

def main():
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    bp = subprocess.Popen(broll_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        audio_mix(events())
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    clip = None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if True:
            raw = bp.stdout.read(CLIP_W * CLIP_H * 3)
            if len(raw) == CLIP_W * CLIP_H * 3: clip = np.frombuffer(raw, np.uint8).reshape(CLIP_H, CLIP_W, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        e = 1.0 if f < F_SPLIT1 else 1 - ease_out_cubic((f - F_SPLIT1) / TRANS)
        if e <= 0:
            canvas = Image.fromarray(guy).convert("RGBA")
        else:
            edge = int(round(TOP * e)); shift = int(round(SHIFT * e))
            fr = np.empty((H, W, 3), np.uint8); fr[edge:] = guy[edge - shift:H - shift]
            panel = BG.copy()
            if clip is not None:   # discreet backdrop: the same clip, blurred and darkened
                sm = Image.fromarray(clip).resize((185, 104), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4))
                bgc = np.asarray(sm.resize((1476, 830), Image.BILINEAR), np.float32)[:, 198:198 + W]
                panel = (bgc * 0.28 + 6).astype(np.uint8)
                reg = panel[CLIP_Y:CLIP_Y + CLIP_H, CLIP_X:CLIP_X + CLIP_W].astype(np.float32)
                panel[CLIP_Y:CLIP_Y + CLIP_H, CLIP_X:CLIP_X + CLIP_W] = (clip * CLIP_MASK + reg * (1 - CLIP_MASK)).astype(np.uint8)
            if f >= F_CHAT:   # Claude chat replaces the clip inside the same card (short cross-fade)
                cv = np.asarray(chat_view(min(f, F_SPLIT1 - 1), clip).convert("RGB"), np.float32)
                reg = panel[CLIP_Y:CLIP_Y + CLIP_H, CLIP_X:CLIP_X + CLIP_W].astype(np.float32)
                a_ = min(1.0, (f - F_CHAT) / 6) * CLIP_MASK
                panel[CLIP_Y:CLIP_Y + CLIP_H, CLIP_X:CLIP_X + CLIP_W] = (cv * a_ + reg * (1 - a_)).astype(np.uint8)
            fr[:edge] = panel[TOP - edge:TOP]
            canvas = Image.fromarray(fr).convert("RGBA")
        if f >= KEY["f0"]:   # keyword: big, centred on the top panel
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            paste(canvas, KEY["im"], 540, 318, sc, min(1, 0.35 + k / 3))
        cap_y = CAP_FULL + (CAP_SPLIT - CAP_FULL) * e
        for ch in chunks:
            if ch["key"] or not (ch["f0"] <= f < ch["f1"]) or KEY["f0"] <= f < KEY["f1"]: continue
            k = f - ch["f0"]
            paste(canvas, ch["im"], 540, cap_y + (1 - ease_out_cubic(k / 5)) * 8, 0.86 + 0.14 * ease_out_back(k / 5), min(1, 0.35 + k / 3))
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill(); bp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "split end", round(F_SPLIT1 / FPS, 2), "key", round(KEY["f0"] / FPS, 2), file=sys.stderr)
    main()
