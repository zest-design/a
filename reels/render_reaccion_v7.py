import json, subprocess, sys, re, wave, difflib, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hl_styles
from hl_styles import (plain_caption, hl_b, draw_caption, revenue_card, png_cutout,
                       ease_out_back, ease_out_cubic)

S = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/scratchpad"
P = f"{S}/w"
P2 = f"{S}/w2"
GUY, ANIM, CTA = f"{P}/a.mp4", f"{P2}/fundo.mp4", f"{P2}/cta.mp4"
VIEWS_PNG = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/images/3.png"
REVENUE_PNG = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/images/1.png"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P2}/out_v7.mp4"
ARG = sys.argv[2] if len(sys.argv) > 2 else None
CLIP = [float(x) for x in ARG[5:].split(",")] if ARG and ARG.startswith("clip:") else None
PREVIEW = [float(x) for x in ARG.split(",")] if ARG and not CLIP else None
PNG_SCALE = float(os.environ.get("PNG_SCALE", "0.68"))
W, H, FPS = 1080, 1920, 30
STYLE = "B"

# ---------------- timeline (output frames) - hard cuts between every part ----------
# O: guy full frame, "mira este vídeo"
# R: animation full frame + guy cut-out (PNG) bottom-left, still watching (synced)
# T: hard cut back to the guy full frame (dead 33-44.6 s of the source removed)
# C: hard cut to CTA_FINAL
A_OPEN, O_LEN = 48, 51                 # guy src 1.60 .. 3.30 s
F_R = O_LEN
B_LEN = 751                            # background video 25.04 s (24 fps source, resampled to 30)
A_R0 = A_OPEN + O_LEN                  # guy src frame 99 -> watching continues
F_T = F_R + B_LEN
A_T0 = 1339                            # guy src 44.63 s
TALK_CUT = (1509, 1604)                # src 50.30-53.47 s removed ("y este vídeo ha generado esta cantidad de ingresos")
T_LEN = (TALK_CUT[0] - A_T0) + (1679 - TALK_CUT[1])
F_U = F_T + T_LEN                      # tutorial (screen recordings + WhatsApp narration)
WA0, WA1 = 0.95, 62.35                 # narration with leading/trailing silence removed
# pauses shortened to 0.24 s; the false start "y le pides ahora que te dé el prompt completo para..." (42.3-46.9) is cut
WA_SIL = [(3.84, 4.13), (10.86, 11.19), (17.56, 17.97), (23.32, 24.17), (34.34, 34.63), (40.85, 41.16),
          (42.25, 46.90), (50.60, 51.02), (53.34, 53.97)]
WA_KEEP = []; _c = WA0
for a_, b_ in WA_SIL:
    WA_KEEP.append((_c, a_ + 0.12)); _c = b_ - 0.12
WA_KEEP.append((_c, WA1))
WA_KEEP = [(round(a_ * FPS) / FPS, round(b_ * FPS) / FPS) for a_, b_ in WA_KEEP]
def wa_out(t):                          # narration time -> seconds into the tutorial
    o = 0.0
    for a_, b_ in WA_KEEP:
        if t <= a_: return o
        if t < b_: return o + t - a_
        o += b_ - a_
    return o
def wa_src(k):                          # tutorial frame -> narration time
    for a_, b_ in WA_KEEP:
        n = int(round((b_ - a_) * FPS))
        if k < n: return a_ + k / FPS
        k -= n
    return WA_KEEP[-1][1] + k / FPS       # past the narration: the result keeps playing
U_LEN = sum(int(round((b_ - a_) * FPS)) for a_, b_ in WA_KEEP) + int(round((26.33 - (WA1 - 60.70)) * FPS))
F_C = F_U + U_LEN
C_T0, C_LEN = 23, 428                  # CTA src 0.77 .. 15.03 s
NF = F_C + C_LEN

def out_open(t): return t - A_OPEN / FPS
def out_talk(t):
    if t >= TALK_CUT[1] / FPS: t -= (TALK_CUT[1] - TALK_CUT[0]) / FPS
    elif t >= TALK_CUT[0] / FPS: t = TALK_CUT[0] / FPS
    return F_T / FPS + t - A_T0 / FPS
def talk_src(k): return A_T0 + k if A_T0 + k < TALK_CUT[0] else TALK_CUT[1] + (k - (TALK_CUT[0] - A_T0))
def out_wa(t): return F_U / FPS + wa_out(t)
def out_cta(t): return F_C / FPS + t - C_T0 / FPS

# ---------------- word timings (whisper text aligned to parakeet onsets) -----------
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
def align(pk, s0, s1, text):
    ws = text.split()
    pk = [(w, t) for w, t in pk if s0 - 0.35 <= t <= s1 + 0.1]
    a = [norm(w) for w in ws]; b = [norm(w) for w, _ in pk]
    times = [None] * len(ws)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = pk[blk.b + k][1]
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1): times[i1 + k] = pk[j1 + k][1]
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    anchors = [(-1, s0)] + known + [(len(ws), s1)]
    for i in range(len(ws)):
        if times[i] is None:
            lo = max(x for x in anchors if x[0] < i); hi = min(x for x in anchors if x[0] > i)
            times[i] = lo[1] + (hi[1] - lo[1]) * (i - lo[0]) / (hi[0] - lo[0])
    for i in range(1, len(times)):
        times[i] = max(times[i], times[i - 1] + 0.05)
    return list(zip(ws, times))

PK_A = json.load(open(f"{P}/a_pk.json"))
PK_C = json.load(open(f"{P}/cta_pk2.json"))
OPEN_W = [("Mira", 1.86), ("este", 2.40), ("vídeo.", 2.65)]
TALK_W = align(PK_A, 44.55, 55.9, "Lo has visto completo, ¿verdad? Pues como tú, lo han visto más de un millón de personas "
               "y este vídeo ha generado esta cantidad de ingresos. Te voy a enseñar paso a paso cómo generarlos.")
TALK_W = [(w, t) for w, t in TALK_W if not (TALK_CUT[0] / FPS - 0.1 <= t < TALK_CUT[1] / FPS - 0.05)]
PK_W = json.load(open(f"{P2}/narr_pk.json"))
WA_W = []
for s0, s1, txt in [
    (0.9, 10.6, "Lo primero que vas a hacer es abrir Claude. Vas a elegir uno de los vídeos que te haya gustado y se lo vas a mandar. Con ello vas a mandar el siguiente prompt:"),
    (11.1, 23.3, "Analiza este vídeo escena por escena. Lo quiero recrear con la misma atmósfera, misma estética y mismos ganchos, pero con una historia diferente. Debe durar unos 30 segundos y ser en español."),
    (24.0, 31.6, "A partir de ahí, Claude se va a poner a analizar todas las escenas del vídeo, escena por escena. Lo que no entienda lo va a intentar interpretar"),
    (32.8, 42.1, "por la imagen y lo que no, por el vídeo. Una vez que lo haya analizado entero, te va a generar algunas ideas. Entonces tú eliges la idea que más te guste"),
    (46.9, 52.9, "y le pides ahora el prompt completo listo para generar ese vídeo usando VAIC."),
    (53.7, 62.2, "Una vez que tú le mandes eso y tengas VAIC conectado, VAIC va a generar el vídeo para ti de manera completamente automática. Y este es el resultado."),
]:
    WA_W += align(PK_W, s0, s1, txt)
PK_C = json.load(open(f"{P2}/cta_pk.json"))
CTA_W = []
for s0, s1, txt in [
    (0.5, 7.3, "Y si tú quieres el paso a paso completo, comenta aquí abajo 77 que te voy a enviar un PDF con el paso a paso"),
    (7.4, 15.0, "completo, exactamente como tú tienes que hacer para poder generar este tipo de vídeos o mini novelas. Comenta aquí abajo 77."),
]:
    CTA_W += align(PK_C, s0, s1, txt)

# ---------------- captions ----------------------------------------------------------
PUNCT = re.compile(r"[.,?:!]$")
def build_chunks(words, hlp, tmap, cap_y, f_start, f_end):
    hlp = [p.split() for p in hlp]
    chunks = []; i = 0
    while i < len(words):
        hit = next((p for p in hlp if [norm(w) for w, _ in words[i:i + len(p)]] == [norm(x) for x in p]), None)
        if hit: g = words[i:i + len(hit)]; i += len(hit); hl = True
        else:
            g = [words[i]]; i += 1; hl = False
            while i < len(words) and len(g) < 3 and not PUNCT.search(g[-1][0]):
                if words[i][1] - g[0][1] > 0.75 or sum(len(w) for w, _ in g) + len(words[i][0]) > 15: break
                if any([norm(w) for w, _ in words[i:i + len(p)]] == [norm(x) for x in p] for p in hlp): break
                g.append(words[i]); i += 1
        txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w for w, _ in g)).lower()
        txt = re.sub(r"\bpdf\b", "PDF", txt)
        for a_, b_ in (("claude", "Claude"), ("vaic", "VAIC"), ("seedance", "Seedance")): txt = re.sub(rf"\b{a_}\b", b_, txt)
        chunks.append(dict(txt=txt, hl=hl, t0=g[0][1]))
    merged = []
    for c in chunks:
        if merged and c["hl"] and not merged[-1]["hl"] and " " not in merged[-1]["txt"] and len(merged[-1]["txt"]) <= 3:
            p = merged.pop(); c = dict(c, txt=p["txt"] + " " + c["txt"], t0=p["t0"])
        merged.append(c)
    for c in merged: c["f0"] = max(f_start, int(round((tmap(c["t0"]) + 0.08) * FPS))); c["y"] = cap_y
    for k, c in enumerate(merged):
        nxt = merged[k + 1]["f0"] if k + 1 < len(merged) else f_end
        c["f1"] = min(nxt, c["f0"] + 30, f_end)
    return merged

CAP_Y_TUT = int(os.environ.get('CAP_Y_TUT', '1480'))
def res_cut(t): return t if t < 4.4 else (t - 1.2 if t < 17.2 else t - (1.2 + 18.1667 - 17.2))
RES_W = [(w, res_cut(t)) for w, t in [
    ("¿En", 0.16), ("serio?", 0.64), ("Mira", 2.00), ("por", 2.48), ("dónde", 2.64), ("vas.", 3.04),
    ("Mira", 9.92), ("por", 10.48), ("dónde", 10.64), ("vas.", 10.96),
    ("Ahora", 13.60), ("estás", 13.78), ("en", 13.95), ("problemas.", 14.05),
    ("Ni", 15.76), ("se", 16.08), ("te", 16.24), ("ocurra.", 16.40),
    ("¿Seguro?", 23.68), ("Primero", 25.12), ("discúlpate.", 25.68), ("Lo", 27.12), ("siento.", 27.44)]]
def out_res(t): return F_U / FPS + wa_out(60.70) + t
chunks = build_chunks(OPEN_W, ["este vídeo"], out_open, 520, 0, F_R) + \
    build_chunks(TALK_W, ["un millón de personas", "ingresos", "paso a paso"], out_talk, 520, F_T, F_U) + \
    build_chunks(WA_W, ["abrir Claude", "escena por escena", "misma atmósfera", "mismos ganchos", "30 segundos", "algunas ideas",
                        "el prompt completo", "VAIC", "completamente automática", "el resultado"], out_wa, CAP_Y_TUT, F_U, F_C) + \
    build_chunks(CTA_W, ["paso a paso", "77", "PDF", "mini novelas"],
                 out_cta, 1450, F_C, NF)
_narr_end = max(c["f1"] for c in chunks if F_U <= c["f0"] < F_C)
RES_CHUNKS = build_chunks(RES_W, [], out_res, 1480, _narr_end, F_C)
chunks += RES_CHUNKS
from hl_styles import plain_caption_pill
for c in chunks: c["im"] = hl_b(c["txt"]) if c["hl"] else (plain_caption_pill(c["txt"]) if (F_U <= c["f0"] < F_C and c not in RES_CHUNKS) else plain_caption(c["txt"]))

# revenue screenshot: pops in on "esta cantidad (de ingresos)", stays until the hard cut to the CTA
def _tw(word, after=None):
    ws = [(w, t) for w, t in TALK_W if after is None or t > after]
    return next(t for w, t in ws if norm(w) == word)
CARD_OUT = 5
VIEWS = revenue_card(VIEWS_PNG, "image", width=430)
REV = revenue_card(REVENUE_PNG, "image")
OVERLAYS = [  # (sprite, first frame, last frame, top y)
    (VIEWS, int(round((out_talk(_tw("más")) + 0.08) * FPS)), F_T + TALK_CUT[0] - A_T0, 90),
]
chunks = [c for c in chunks if not any(o[1] <= c['f0'] < o[2] for o in OVERLAYS)]

def place(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    x, y = int(x - im.width / 2), int(y - im.height / 2)
    canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))

# ---------------- reaction cut-out masks --------------------------------------------
# fast human mask on every frame, gated by a dilated clean (BiRefNet) mask from the nearest keyframe
KEYS = sorted(int(f[:4]) for f in os.listdir(f"{P}/rmask_key"))
_kcache = {}
def key_gate(n):
    k = min(KEYS, key=lambda x: abs(x - n))
    if k not in _kcache:
        m = Image.open(f"{P}/rmask_key/{k:04d}.png").convert("L").point(lambda v: 255 if v > 60 else 0)
        _kcache[k] = m.filter(ImageFilter.MaxFilter(41)).filter(ImageFilter.GaussianBlur(6))
    return _kcache[k]
def reaction_mask(n):
    fast = Image.open(f"{P}/rmask_fast/{n:04d}.png").convert("L")
    m = np.minimum(np.asarray(fast), np.asarray(key_gate(n)))
    return Image.fromarray(m).resize((W, H), Image.BILINEAR)

hl_styles.PNG_SCALE = PNG_SCALE
PNG_W, PNG_H = int(1080 * PNG_SCALE), int(1920 * PNG_SCALE)
PNG_X = -int(PNG_W * 0.17)            # crop a little off the left edge, bottom-left anchored
PNG_Y = H - int(PNG_H * 0.93)          # lower ~7 % (chest) runs off the bottom

# ---------------- sources ----------------------------------------------------------
def reader(src, f0, n):
    vf = f"fps={FPS},select='gte(n\\,{f0})',setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,format=rgb24"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", vf, "-vsync", "0", "-frames:v", str(n),
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    def nxt():
        b = p.stdout.read(W * H * 3)
        return np.frombuffer(b, np.uint8).reshape(H, W, 3) if len(b) == W * H * 3 else None
    return nxt

# ---------------- tutorial: screen recordings synced to the narration --------------
EDIT, RES = f"{P2}/rec.mp4", f"{P2}/final_cut.mp4"   # result with 4.4-5.6 s and 17.2-18.2 s removed
SW, SH = 720, 1564
RES_FROM = 60.70                       # "Y este es el resultado" -> the finished video
RES_LEN = 26.33
EXTRA = RES_LEN - (WA1 - RES_FROM)     # the whole (trimmed) result plays, with its own sound, so the story reads
# (narration time, source, source time): linear in between; jumps where the source changes
UMAP = [
    (0.0, "e", 1.30), (9.9, "e", 1.30),         # Claude home with the reference video attached ("abrir Claude", "elegir uno de los vídeos")
    (9.9, "e", 1.45), (23.3, "e", 10.30),       # typing the prompt while it is read out
    (23.3, "e", 10.30), (24.0, "e", 10.90),     # sent
    (24.0, "e", 10.90), (34.9, "e", 38.0),      # Claude analysing frame by frame (sped up)
    (34.9, "e", 38.0), (44.0, "e", 45.9),       # analysis + story ideas
    (44.0, "e", 46.3), (52.9, "e", 51.2),       # typing "Dame el prompt detallado ... con vaic"
    (52.9, "e", 51.2), (57.0, "e", 59.0),       # Claude writing the prompts
    (57.0, "e", 87.45), (59.0, "e", 87.75),     # "Usa vaic y genera el vídeo" on "VAIC va a generar el vídeo"
    (59.0, "e", 87.75), (RES_FROM, "e", 87.75),
    (RES_FROM, "f", 0.0), (WA1 + EXTRA, "f", WA1 + EXTRA - RES_FROM),
]
# never show the attachment/permissions sheet, the photo roll or the iOS text loupe
FORBID = {"e": [(0.0, 1.27)], "f": []}
def umap(w):
    for (w0, s0, t0), (w1, s1, t1) in zip(UMAP[0::2], UMAP[1::2]):
        if w0 <= w < w1 or (w1 == UMAP[-1][0] and w >= w0):
            t = t0 + (t1 - t0) * min(1.0, (w - w0) / max(1e-6, w1 - w0))
            for a, b in FORBID[s0]:
                if a <= t < b: t = b
            return s0, t
    prev = [p for p in UMAP[1::2] if p[0] <= w]
    return (prev[-1][1], prev[-1][2]) if prev else (UMAP[0][1], UMAP[0][2])
class SeqReader:
    def __init__(self, src):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps={FPS},scale={SW}:{SH},format=rgb24", "-vsync", "0",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.n = -1; self.cur = None
    def at(self, t):
        want = int(round(t * FPS))
        while self.n < want:
            b = self.p.stdout.read(SW * SH * 3)
            if len(b) < SW * SH * 3: break
            self.cur = np.frombuffer(b, np.uint8).reshape(SH, SW, 3); self.n += 1
        return self.cur
SCR_SCALE = W / SW                     # 1.5 -> 1080 x 2346
SCR_TOP = int(os.environ.get("SCR_TOP", "150"))   # source px cropped from the top (status bar + nav)
def name_box(fr):
    """box of the account name in "Buenas tardes, <name>": the dark text line right under the orange Claude mark"""
    reg = fr[120:900, 280:440].astype(np.int16)        # the mark is centred; the orange send button sits far right
    org = (reg[..., 0] > 180) & (reg[..., 1] < 150) & (reg[..., 2] < 120)
    ys, xs = np.where(org)
    if len(ys) < 30: return None
    ay1 = 120 + ys.max()
    band = fr[ay1 + 10:ay1 + 110, 60:660].astype(np.int16)
    dark = (band < 130).all(axis=2)
    rows = np.where(dark.sum(axis=1) > 2)[0]
    if len(rows) == 0: return None
    cols = np.where(dark[rows[0]:rows[-1] + 1].any(axis=0))[0]
    y0, y1 = ay1 + 10 + rows[0] - 10, ay1 + 10 + rows[-1] + 12
    x1 = 60 + cols[-1] + 14
    return y0, y1, x1 - 135, x1
def blur_name(fr):
    b = name_box(fr)
    if b is None: return fr
    y0, y1, x0, x1 = b
    out = fr.copy(); im = Image.fromarray(out[y0:y1, x0:x1]).filter(ImageFilter.GaussianBlur(10))
    out[y0:y1, x0:x1] = np.asarray(im); return out
def screen_frame(fr):
    im = Image.fromarray(fr[SCR_TOP:SCR_TOP + int(round(H / SCR_SCALE))])
    return im.resize((W, H), Image.LANCZOS).convert("RGBA")

def render():
    guy = reader(GUY, A_OPEN, O_LEN + B_LEN)
    anim = reader(ANIM, 0, B_LEN)
    talk = reader(GUY, A_T0, 1679 - A_T0); talk_n = [A_T0 - 1]
    cta = reader(CTA, C_T0, C_LEN)
    scr = {"e": SeqReader(EDIT), "f": SeqReader(RES)}
    enc = None
    if PREVIEW is None and CLIP is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{P2}/mix_v7.wav", "-map", "0:v", "-map", "1:a",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    if CLIP:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-ss", str(CLIP[0]), "-t", str(CLIP[1] - CLIP[0]), "-i", f"{P2}/mix_v7.wav",
                                "-map", "0:v", "-map", "1:a", "-vf", "scale=720:1280", "-c:v", "libx264", "-crf", "20",
                                "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", OUT], stdin=subprocess.PIPE)
        want = set(range(int(CLIP[0] * FPS), int(CLIP[1] * FPS)))
    else:
        want = None if PREVIEW is None else {int(round(t * FPS)) for t in PREVIEW}
    for f in range(NF):
        need = want is None or f in want
        if f < F_R:
            fr = guy()
        elif f < F_T:
            g, bg = guy(), anim()
            if need:
                canvas = Image.fromarray(bg).convert("RGBA")
                spr = png_cutout(g, reaction_mask(A_R0 + f - F_R))
                canvas.alpha_composite(spr, (0, PNG_Y), (-PNG_X, 0))
                fr = None
        elif f < F_U:
            want_n = talk_src(f - F_T)
            while talk_n[0] < want_n: fr = talk(); talk_n[0] += 1
        elif f < F_C:
            src, t = umap(wa_src(f - F_U))
            sf = scr[src].at(t); fr = None
            if need:
                if src == "f": canvas = Image.fromarray(sf).resize((W, H), Image.LANCZOS).convert("RGBA")
                else: canvas = screen_frame(blur_name(sf) if t < 10.6 else sf)
        else:
            fr = cta()
        if not need: continue
        if fr is not None: canvas = Image.fromarray(fr).convert("RGBA")
        for spr, o0, o1, oy in OVERLAYS:
            if o0 <= f < o1 + CARD_OUT:
                k = f - o0
                sc = 0.6 + 0.4 * ease_out_back(k / 9, 2.0); al = min(1, 0.2 + k / 4)
                if f >= o1:
                    q = (f - o1 + 1) / CARD_OUT; sc *= 1 - 0.25 * q; al *= 1 - q
                place(canvas, spr, 540, oy + spr.height / 2 + (1 - ease_out_cubic(k / 8)) * 24, sc, al)
        for c in chunks:
            if c["f0"] <= f < c["f1"]: draw_caption(canvas, c, f - c["f0"], 540, c["y"], STYLE)
        out = np.asarray(canvas.convert("RGB"))
        if CLIP: enc.stdin.write(out.tobytes())
        elif want is not None: Image.fromarray(out).save(f"{P2}/pv7_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    if enc: enc.stdin.close(); enc.wait()
    if CLIP: raise SystemExit

# ---------------- audio (hard cuts, 8 ms de-click fades) ---------------------------
SR = 48000
def load(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def rms(x): return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
def audio():
    ga, gb, gc = load(GUY), load(ANIM), load(CTA)
    sp = lambda x, f0, n: x[int(f0 / FPS * SR):int((f0 + n) / FPS * SR)]
    ref = rms(gc[int(0.5 * SR):int(22.7 * SR)])
    ka = ref / rms(ga[int(44.7 * SR):int(55.9 * SR)]); kb = ref / rms(gb) * 0.85
    tot = int(NF / FPS * SR) + SR
    mix = np.zeros((tot, 2), np.float32)
    D = int(0.008 * SR); up = np.linspace(0, 1, D, dtype=np.float32)[:, None]
    def put(seg, f_at):
        seg = seg.copy(); seg[:D] *= up; seg[-D:] *= up[::-1]
        s = int(f_at / FPS * SR); mix[s:s + len(seg)] += seg[:tot - s]
    put(sp(ga, A_OPEN, O_LEN + B_LEN) * ka, 0)          # "mira este vídeo" + his reaction while watching
    put(gb[:int(B_LEN / FPS * SR)] * kb, F_R)           # animation soundtrack starts with the animation
    put(sp(ga, A_T0, TALK_CUT[0] - A_T0) * ka, F_T)
    put(sp(ga, TALK_CUT[1], 1679 - TALK_CUT[1]) * ka, F_T + TALK_CUT[0] - A_T0)
    gw = load(f"{P2}/narr.mp3"); kw = ref / rms(gw[int(1.0 * SR):int(62.2 * SR)])
    fu = F_U
    for a_, b_ in WA_KEEP:                            # tutorial narration (WhatsApp audio), pauses shortened
        n = int(round((b_ - a_) * FPS)); put(gw[int(a_ * SR):int(a_ * SR) + int(n / FPS * SR)] * kw, fu); fu += n
    gf = load(RES); f_at = F_U + int(round(wa_out(RES_FROM) * FPS))
    seg = gf[:int((WA1 + EXTRA - RES_FROM) * SR)] * (ref / rms(gf[:int(8 * SR)])) * 0.9
    n_duck = int((WA1 - RES_FROM) * SR); env = np.ones((len(seg), 1), np.float32); env[:n_duck] = 0.3
    r_ = int(0.25 * SR); env[n_duck:n_duck + r_] = np.linspace(0.3, 1, r_, dtype=np.float32)[:, None]
    put(seg * env, f_at)                              # the result's own sound, under "y este es el resultado"
    put(sp(gc, C_T0, C_LEN), F_C)
    mix = mix[:int(NF / FPS * SR)]
    with wave.open(f"{P2}/mix_v7_raw.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P2}/mix_v7_raw.wav", "-af",
                    "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.94",
                    "-ar", "48000", f"{P2}/mix_v7.wav"], check=True)

if __name__ == "__main__":
    for c in chunks: print(f"{c['f0'] / FPS:6.2f}-{c['f1'] / FPS:6.2f} {'[HL] ' if c['hl'] else ''}{c['txt']}")
    print("overlays", [(o[1] / FPS, o[2] / FPS) for o in OVERLAYS], "total", NF / FPS)
    if (PREVIEW is None and CLIP is None) or (CLIP and not os.path.exists(f"{P2}/mix_v7.wav")): audio()
    render()
