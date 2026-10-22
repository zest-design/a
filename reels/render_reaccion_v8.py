"""Reaction reel, CTA 22 (trading niche): same format as reaccion_77.

O  guy full frame "mira este vídeo"
R  stick-figure animation full frame + guy cut-out (PNG) watching, bottom-left
T  guy talking (pauses trimmed); the "companies that pay creators" screen recording is inserted while he talks about it
U  tutorial: Instagram niche search -> Claude screen recording, synced to the narration -> the result plays in full
C  CTA (audio only): the result keeps looping, blurred, behind a "Comenta 22" card
"""
import json, subprocess, sys, re, wave, difflib, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hl_styles
from hl_styles import (plain_caption, plain_caption_pill, hl_b, draw_caption, png_cutout, font, blur_shadow,
                       ease_out_back, ease_out_cubic, RED, WHITE)

S = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/scratchpad"
P = f"{S}/w3"
GUY, ANIM = f"{P}/f4.mp4", f"{P}/fundo.mp4"
EMP, NICHO, REC, RES = f"{P}/empresas.mp4", f"{P}/nicho.mp4", f"{P}/rec.mp4", f"{P}/final.mp4"
NARR, CTA_A = f"{P}/narr.m4a", f"{P}/cta.m4a"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P}/out_v8.mp4"
ARG = sys.argv[2] if len(sys.argv) > 2 else None
CLIP = [float(x) for x in ARG[5:].split(",")] if ARG and ARG.startswith("clip:") else None
PREVIEW = [float(x) for x in ARG.split(",")] if ARG and not CLIP else None
PNG_SCALE = float(os.environ.get("PNG_SCALE", "0.68"))
CAP_Y_TALK = int(os.environ.get("CAP_Y_TALK", "520"))
CAP_Y_TUT = 1480
W, H, FPS = 1080, 1920, 30
STYLE = "B"

def keep_list(t0, t1, sil, pad=0.12):
    out = []; c = t0
    for a, b in sil:
        out.append((c, a + pad)); c = b - pad
    out.append((c, t1))
    return [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in out]
def mk_maps(keep):
    def fwd(t):                         # source time -> seconds into the section
        o = 0.0
        for a, b in keep:
            if t <= a: return o
            if t < b: return o + t - a
            o += b - a
        return o
    def back(k):                        # section frame -> source time
        for a, b in keep:
            n = int(round((b - a) * FPS))
            if k < n: return a + k / FPS
            k -= n
        return keep[-1][1] + k / FPS
    n = sum(int(round((b - a) * FPS)) for a, b in keep)
    return fwd, back, n

# ---------------- timeline ----------------------------------------------------------
A_OPEN, O_LEN = 16, 47                 # guy src 0.53 .. 2.10 s ("mira este vídeo")
F_R = O_LEN
B_LEN = 471                            # animation 15.72 s
R_SRC0, R_SRC1 = 63, 504               # guy watching: src frames 2.10 .. 16.80 s, spread over the animation
F_T = F_R + B_LEN
TK_KEEP = keep_list(16.70, 68.10, [(25.15, 25.61), (26.30, 26.86)])
tk_fwd, tk_back, T_LEN = mk_maps(TK_KEEP)
EMP_T0, EMP_T1 = 30.95, 50.70          # "Hay otras empresas ..." .. "... lo que tú estés creando."
EMP_S0, EMP_S1 = 1.05, 18.30           # screen recording without the control centre (0-1 s)
F_U = F_T + T_LEN
WA_KEEP = keep_list(1.35, 74.50, [(4.54, 5.15), (28.19, 32.58), (51.85, 59.30), (71.39, 71.80)])
wa_fwd, wa_back, WA_N = mk_maps(WA_KEEP)
RES_FROM, RES_LEN = 71.70, 13.80       # "Y este será el resultado final" -> the result plays in full
U_LEN = WA_N + int(round((RES_LEN - (74.50 - RES_FROM)) * FPS))
F_C = F_U + U_LEN
CTA_KEEP = keep_list(1.00, 20.00, [])
cta_fwd, cta_back, C_LEN = mk_maps(CTA_KEEP)
NF = F_C + C_LEN

def out_open(t): return t - A_OPEN / FPS
def out_talk(t): return F_T / FPS + tk_fwd(t)
def out_wa(t): return F_U / FPS + wa_fwd(t)
def out_cta(t): return F_C / FPS + cta_fwd(t)

# ---------------- words (whisper text aligned to parakeet onsets) -------------------
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
def align_all(pk, segs):
    out = []
    for s0, s1, txt in segs: out += align(pk, s0, s1, txt)
    return out

PK_T = json.load(open(f"{P}/f4_pk.json"))
PK_N = json.load(open(f"{P}/narr_pk.json"))
PK_C = json.load(open(f"{P}/cta_pk.json"))
OPEN_W = [("Mira", 0.64), ("este", 1.44), ("vídeo.", 1.68)]
TALK_W = align_all(PK_T, [
    (16.7, 25.8, "Te has quedado hasta el final, ¿verdad? Pues tú no has sido el único. Este vídeo ha cogido más de 90 millones de reproducciones y ha generado más de 3.000 dólares."),
    (26.6, 30.9, "Te voy a enseñar cómo en un paso a paso simple. Así que vente conmigo."),
    (30.9, 40.9, "Hay otras empresas que están pagando a personas por crear contenido en redes sociales para ellos. Aquí tienes un montón de ejemplos. Hay una lista aquí completa, es gigantesca."),
    (41.4, 50.5, "Hay empresas que pagan por vídeos y hay empresas que pagan por visualizaciones. Entonces tú puedes elegir la que más te guste, la que encaja con lo que tú estés creando."),
    (50.8, 64.9, "Yo te recomiendo elegir un nicho donde tú puedas reaprovechar la cuenta para diferentes empresas. Por ejemplo, si tú hablas de trading, de póker o de cosas que tú puedas aprovechar la misma cuenta para diferentes empresas, te hará ganar más dinero con menos trabajo."),
    (65.0, 68.1, "Ahora vamos a ver cómo replicamos un vídeo así de manera fácil."),
])
WA_W = align_all(PK_N, [
    (1.2, 6.6, "Primero vas a ir a Instagram y vas a buscar el nicho en el cual quieres trabajar."),
    (6.7, 11.9, "Yo en este caso voy a trabajar en el de trading como ejemplo, pero tú eliges el que más te guste."),
    (12.0, 19.9, "Al buscar trading vas a ver varios vídeos con millones de views. Vas a elegir alguno, lo vas a descargar y luego vas a ir a Claude."),
    (20.2, 27.9, "Dentro de Claude le vas a pasar tu vídeo elegido, el vídeo que hayas descargado, y le vas a enviar el siguiente prompt:"),
    (32.0, 42.5, "Quiero replicar este vídeo usando el mismo gancho, estética y duración. Haz un análisis escena a escena para construir 5 ideas diferentes de vídeo."),
    (43.0, 51.7, "Claude empezará a trabajar, analizará el vídeo escena por escena, analizará los textos que tenga, los dibujos, todo lo demás y lo hará todo para ti."),
    (59.3, 66.2, "Luego al final te dará todas las informaciones del vídeo y aquí simplemente le tienes que pedir lo siguiente:"),
    (66.3, 71.5, "Usa VAIC y genera la idea 1 completa."),
    (71.6, 74.5, "Y este será el resultado final que vas a obtener."),
])
CTA_W = align_all(PK_C, [
    (0.8, 10.6, "Y si tú quieres aprender el paso a paso completo, detalle por detalle, he preparado un PDF completo para ti y te lo enviaré si comentas aquí abajo el número 22."),
    (11.0, 19.8, "Comenta 22 y te haré llegar el PDF completo para que tú puedas empezar hoy a crear los vídeos y a generar ingresos en Internet."),
])

# ---------------- captions ----------------------------------------------------------
PUNCT = re.compile(r"[.,?:!]$")
FIX = (("claude", "Claude"), ("vaic", "VAIC"), ("instagram", "Instagram"), ("pdf", "PDF"))
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
        txt = re.sub(r"(?<=\d)\.(?=\d)", "§", " ".join(w for w, _ in g))     # keep the thousands dot in "3.000"
        txt = re.sub(r"[¿?¡!.,:;]", "", txt).lower().replace("§", ".")
        for a_, b_ in FIX: txt = re.sub(rf"\b{a_}\b", b_, txt)
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

def talk_is_screen(t): return EMP_T0 <= t < EMP_T1
TALK_FACE_W = [(w, t) for w, t in TALK_W if not talk_is_screen(t)]
TALK_SCR_W = [(w, t) for w, t in TALK_W if talk_is_screen(t)]
TALK_HL = ["90 millones", "3.000 dólares", "paso a paso", "por vídeos", "por visualizaciones", "un nicho", "más dinero", "manera fácil"]
F_EMP0, F_EMP1 = int(round(out_talk(EMP_T0) * FPS)), int(round(out_talk(EMP_T1) * FPS))
chunks = build_chunks(OPEN_W, ["este vídeo"], out_open, CAP_Y_TALK, 0, F_R)
face1 = build_chunks([x for x in TALK_FACE_W if x[1] < EMP_T0], TALK_HL, out_talk, CAP_Y_TALK, F_T, F_EMP0)
scr = build_chunks(TALK_SCR_W, TALK_HL, out_talk, CAP_Y_TUT, F_EMP0, F_EMP1)
face2 = build_chunks([x for x in TALK_FACE_W if x[1] >= EMP_T1], TALK_HL, out_talk, CAP_Y_TALK, F_EMP1, F_U)
tut = build_chunks(WA_W, ["ir a Instagram", "el nicho", "millones de views", "ir a Claude", "el siguiente prompt",
                          "mismo gancho", "5 ideas", "escena por escena", "lo hará todo para ti", "Usa VAIC", "la idea 1",
                          "el resultado final"], out_wa, CAP_Y_TUT, F_U, F_C)
cta = build_chunks(CTA_W, ["paso a paso", "PDF", "22", "generar ingresos"], out_cta, CAP_Y_TUT, F_C, NF)
PILL = set(map(id, scr + tut))
chunks += face1 + scr + face2 + tut + cta
for c in chunks: c["im"] = hl_b(c["txt"]) if c["hl"] else (plain_caption_pill(c["txt"]) if id(c) in PILL else plain_caption(c["txt"]))

def place(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    x, y = int(x - im.width / 2), int(y - im.height / 2)
    canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))

# ---------------- "Comenta 22" card for the CTA -------------------------------------
def comment_card():
    f1, f2 = font("InterDisplay-Bold.otf", 76), font("InterDisplay-Black.otf", 230)
    w, h, m = 640, 560, 60
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    im.alpha_composite(blur_shadow(im.size, (m, m, m + w, m + h), 48, 26, 150, (0, 18)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m, m, m + w, m + h), 48, fill=(255, 255, 255, 255))
    d.text((m + w / 2, m + 104), "Comenta", font=f1, fill=(22, 22, 24), anchor="mm")
    bx0, by0, bx1, by1 = m + 120, m + 190, m + w - 120, m + h - 60
    d.rounded_rectangle((bx0, by0, bx1, by1), 40, fill=RED)
    d.text(((bx0 + bx1) / 2, (by0 + by1) / 2 - 8), "22", font=f2, fill=WHITE, anchor="mm")
    return im
CARD = comment_card()
CARD_Y = 820
PULSES = [int(round(out_cta(t) * FPS)) for w, t in CTA_W if norm(w) == "22"]

# ---------------- reaction cut-out masks --------------------------------------------
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
PNG_X = -int(PNG_W * 0.17)
PNG_Y = H - int(PNG_H * 0.93)

# ---------------- tutorial mapping: (narration time, source, source time) ----------
UMAP = [
    (1.2, "n", 0.0), (19.5, "n", 12.6),        # Instagram: search "trading", videos with millions of views
    (19.5, "e", 0.50), (22.0, "e", 0.50),        # "luego vas a ir a Claude. Dentro de Claude"
    (22.0, "e", 3.30), (32.3, "e", 3.30),      # "le vas a pasar tu vídeo elegido" -> video attached
    (32.3, "e", 3.35), (41.6, "e", 18.85),     # typing the prompt while it is read out
    (41.6, "e", 18.85), (43.0, "e", 19.6),     # sent
    (43.0, "e", 19.6), (48.5, "e", 51.5),      # Claude analysing (sped up)
    (48.5, "e", 51.5), (51.85, "e", 56.5),     # analysis + 5 ideas
    (59.3, "e", 56.5), (66.2, "e", 59.6),      # "te dará todas las informaciones del vídeo"
    (66.2, "e", 59.6), (71.5, "e", 64.0),      # typing "Usa vaic y genera la idea 1 completa"
    (71.5, "e", 64.0), (RES_FROM, "e", 64.0),
    (RES_FROM, "f", 0.0), (RES_FROM + RES_LEN, "f", RES_LEN),
]
FORBID = {"n": [], "e": [(0.0, 0.50), (0.55, 3.27)], "f": []}   # control centre, attachment sheet + photo roll never show   # the attachment sheet + photo roll never show
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
    def __init__(self, src, w, h, loop=False):
        self.src, self.w, self.h, self.loop = src, w, h, loop
        self.base = 0
        self._open()
    def _open(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", self.src, "-vf", f"fps={FPS},scale={self.w}:{self.h}:flags=lanczos,format=rgb24",
                                   "-vsync", "0", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.n = -1; self.cur = None
    def at(self, t):
        want = int(round(t * FPS)) - self.base
        while self.n < want:
            b = self.p.stdout.read(self.w * self.h * 3)
            if len(b) < self.w * self.h * 3:
                if self.loop:                   # restart from the top: keep the frame index modulo the clip length
                    length = self.n + 1; self.p.kill(); self._open(); self.base += length; want -= length; continue
                break
            self.cur = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3); self.n += 1
        return self.cur
SW, SH = 1080, 2346                    # screen recordings at 1080 wide
SCR_TOP = 225                          # status bar / nav cropped; the bottom strip runs off
def screen_frame(fr): return Image.fromarray(fr[SCR_TOP:SCR_TOP + H]).convert("RGBA")
def full_frame(fr): return Image.fromarray(fr).resize((W, H), Image.LANCZOS).convert("RGBA")

def render():
    guy = SeqReader(GUY, W, H)
    anim = SeqReader(ANIM, W, H)
    rd = {"n": SeqReader(NICHO, SW, SH), "e": SeqReader(REC, SW, SH), "f": SeqReader(RES, 720, 1280),
          "emp": SeqReader(EMP, SW, SH)}
    cta_bg = SeqReader(RES, 720, 1280, loop=True)
    enc = None
    if PREVIEW is None and CLIP is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{P}/mix_v8.wav", "-map", "0:v", "-map", "1:a",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    if CLIP:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-ss", str(CLIP[0]), "-t", str(CLIP[1] - CLIP[0]), "-i", f"{P}/mix_v8.wav",
                                "-map", "0:v", "-map", "1:a", "-vf", "scale=720:1280", "-c:v", "libx264", "-crf", "20",
                                "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", OUT], stdin=subprocess.PIPE)
        want = set(range(int(CLIP[0] * FPS), int(CLIP[1] * FPS)))
    else:
        want = None if PREVIEW is None else {int(round(t * FPS)) for t in PREVIEW}
    for f in range(NF):
        need = want is None or f in want
        canvas = None
        if f < F_R:
            g = guy.at((A_OPEN + f) / FPS)
            if need: canvas = full_frame(g)
        elif f < F_T:
            k = f - F_R
            n = R_SRC0 + int(round(k * (R_SRC1 - R_SRC0) / (B_LEN - 1)))
            g, bg = guy.at(n / FPS), anim.at(k / FPS)
            if need:
                canvas = Image.fromarray(bg).convert("RGBA")
                canvas.alpha_composite(png_cutout(g, reaction_mask(n)), (0, PNG_Y), (-PNG_X, 0))
        elif f < F_U:
            t = tk_back(f - F_T)
            if talk_is_screen(t):
                e = rd["emp"].at(EMP_S0 + (t - EMP_T0) * (EMP_S1 - EMP_S0) / (EMP_T1 - EMP_T0))
                if need: canvas = screen_frame(e)
            else:
                g = guy.at(t)
                if need: canvas = full_frame(g)
        elif f < F_C:
            src, t = umap(wa_back(f - F_U))
            sf = rd[src].at(t)
            if need: canvas = full_frame(sf) if src == "f" else screen_frame(sf)
        else:
            k = f - F_C
            bg = cta_bg.at(k / FPS)
            if need:
                im = Image.fromarray(bg).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(18))
                canvas = Image.blend(im, Image.new("RGB", (W, H), (12, 12, 14)), 0.45).convert("RGBA")
                sc = 0.55 + 0.45 * ease_out_back(k / 10, 2.2); al = min(1, 0.2 + k / 4)
                for p0 in PULSES:                       # little bump each time he says "22"
                    if 0 <= f - p0 < 10: sc *= 1 + 0.07 * np.sin(np.pi * (f - p0) / 10)
                place(canvas, CARD, 540, CARD_Y, sc, al)
        if not need: continue
        for c in chunks:
            if c["f0"] <= f < c["f1"]: draw_caption(canvas, c, f - c["f0"], 540, c["y"], STYLE)
        out = np.asarray(canvas.convert("RGB"))
        if CLIP: enc.stdin.write(out.tobytes())
        elif want is not None: Image.fromarray(out).save(f"{P}/pv8_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    if enc: enc.stdin.close(); enc.wait()

# ---------------- audio (hard cuts, 8 ms de-click fades) ---------------------------
SR = 48000
def load(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def rms(x): return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
def audio():
    ga, gb, gn, gc, gf = load(GUY), load(ANIM), load(NARR), load(CTA_A), load(RES)
    ref = rms(ga[int(17 * SR):int(68 * SR)])
    kb = ref / rms(gb) * 0.85; kn = ref / rms(gn[int(1.3 * SR):int(74 * SR)]); kc = ref / rms(gc[int(1 * SR):int(20 * SR)])
    kf = ref / rms(gf) * 0.9
    tot = int(NF / FPS * SR) + SR
    mix = np.zeros((tot, 2), np.float32)
    D = int(0.008 * SR); up = np.linspace(0, 1, D, dtype=np.float32)[:, None]
    def put(seg, f_at):
        seg = seg.copy(); seg[:D] *= up; seg[-D:] *= up[::-1]
        s = int(f_at / FPS * SR); mix[s:s + len(seg)] += seg[:tot - s]
    def put_keep(x, keep, f_at, k=1.0):
        for a, b in keep:
            n = int(round((b - a) * FPS)); put(x[int(a * SR):int(a * SR) + int(n / FPS * SR)] * k, f_at); f_at += n
    put(ga[int(A_OPEN / FPS * SR):int((A_OPEN + O_LEN) / FPS * SR)], 0)     # "mira este vídeo"
    put(gb[:int(B_LEN / FPS * SR)] * kb, F_R)                               # the animation's own sound
    put_keep(ga, TK_KEEP, F_T)                                              # talk (screen insert keeps his voice)
    put_keep(gn, WA_KEEP, F_U, kn)                                          # tutorial narration
    f_at = F_U + int(round(wa_fwd(RES_FROM) * FPS))                        # the result, ducked under the last line
    seg = gf[:int(RES_LEN * SR)] * kf
    n_duck = int((74.50 - RES_FROM) * SR); env = np.ones((len(seg), 1), np.float32); env[:n_duck] = 0.3
    r_ = int(0.25 * SR); env[n_duck:n_duck + r_] = np.linspace(0.3, 1, r_, dtype=np.float32)[:, None]
    put(seg * env, f_at)
    put_keep(gc, CTA_KEEP, F_C, kc)                                         # CTA voice
    bed = np.tile(gf, (int(np.ceil(C_LEN / FPS / (len(gf) / SR))) + 1, 1))[:int(C_LEN / FPS * SR)] * kf * 0.12
    put(bed, F_C)                                                           # the result's music, low, under the CTA
    mix = mix[:int(NF / FPS * SR)]
    with wave.open(f"{P}/mix_v8_raw.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/mix_v8_raw.wav", "-af",
                    "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.94",
                    "-ar", "48000", f"{P}/mix_v8.wav"], check=True)

if __name__ == "__main__":
    for c in sorted(chunks, key=lambda c: c["f0"]):
        print(f"{c['f0'] / FPS:6.2f}-{c['f1'] / FPS:6.2f} {'[HL] ' if c['hl'] else ''}{c['txt']}")
    print("F_T", F_T / FPS, "emp", F_EMP0 / FPS, F_EMP1 / FPS, "F_U", F_U / FPS, "F_C", F_C / FPS, "total", NF / FPS)
    if (PREVIEW is None and CLIP is None) or (CLIP and not os.path.exists(f"{P}/mix_v8.wav")): audio()
    if PREVIEW and PREVIEW[0] > 9000: raise SystemExit
    render()
