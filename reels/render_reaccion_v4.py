import json, subprocess, sys, re, wave, difflib, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hl_styles
from hl_styles import (plain_caption, hl_b, draw_caption, revenue_card, png_cutout,
                       ease_out_back, ease_out_cubic)

S = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/scratchpad"
P = f"{S}/w"
GUY, ANIM, CTA = f"{P}/a.mp4", f"{P}/b.mp4", f"{P}/cta.mp4"
REVENUE_PNG = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/images/1.png"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P}/out_v4.mp4"
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
B_LEN = 902                            # animation 30.07 s
A_R0 = A_OPEN + O_LEN                  # guy src frame 99 -> watching continues
F_T = F_R + B_LEN
A_T0, T_LEN = 1339, 340                # guy src 44.63 .. 55.97 s
F_U = F_T + T_LEN                      # tutorial (screen recordings + WhatsApp narration)
WA0, WA1 = 0.55, 66.15                 # narration with leading/trailing silence removed
# long pauses inside the narration are shortened to 0.24 s (0.12 s kept on each side)
WA_SIL = [(11.58, 11.91), (19.07, 19.53), (21.15, 22.07), (28.70, 29.38), (40.35, 41.52), (42.19, 42.67),
          (47.50, 47.88), (55.03, 56.19), (58.12, 59.01)]
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
    return WA_KEEP[-1][1]
U_LEN = sum(int(round((b_ - a_) * FPS)) for a_, b_ in WA_KEEP)
F_C = F_U + U_LEN
C_T0, C_LEN = 15, 667                  # CTA src 0.50 .. 22.73 s
NF = F_C + C_LEN

def out_open(t): return t - A_OPEN / FPS
def out_talk(t): return F_T / FPS + t - A_T0 / FPS
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
PK_W = json.load(open(f"{P}/wa_pk.json"))
WA_W = []
for s0, s1, txt in [
    (0.6, 10.3, "Lo primero que vas a hacer es ir a Claude y le vas a pedir que analice el vídeo que tú hayas escogido como ejemplo y que te dé el detalle escena por escena."),
    (10.4, 21.2, "Esta parte es muy importante para que Claude analice fotograma a fotograma y también analice el audio del vídeo para poder encajar y entender cómo está construido ese vídeo."),
    (21.6, 32.4, "Una vez que termine el análisis le vas a pedir que ahora te dé una idea para crear otro, escena por escena, usando lo mismo pero parecido. En este caso yo estoy creando animales,"),
    (32.4, 41.3, "pues le pido otros animales, pero en tu caso debería de ser un vídeo muy parecido al que tú estás construyendo, cambiando simplemente los personajes."),
    (41.3, 50.8, "Una vez que ya te dé la idea, ahora simplemente le vas a decir usa VAIC para crear las imágenes y luego usa Seedance en VAIC para generar el vídeo."),
    (50.8, 58.1, "Así ya Claude tendrá la capacidad de generar las imágenes y los vídeos y con ello crear el vídeo entero."),
    (58.7, 66.1, "Aquí podemos ver cómo Claude está trabajando, crea las imágenes, crea los vídeos y luego lo monta todo para ti."),
]:
    WA_W += align(PK_W, s0, s1, txt)
CTA_W = []
for s0, s1, txt in [
    (0.2, 5.0, "Y si quieres el paso a paso completo, comenta aquí abajo 33 que te lo haré llegar."),
    (5.7, 12.3, "He preparado un PDF completo para ti y te lo voy a enviar totalmente gratis. Comenta aquí abajo 33."),
    (12.35, 19.3, "Y además te voy a enviar un vídeo de cómo generar entre 300 y 500 dólares todos los días usando inteligencia artificial."),
    (19.35, 22.7, "Comenta aquí abajo 33 y te enviaré el PDF y el vídeo."),
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
chunks = build_chunks(OPEN_W, ["este vídeo"], out_open, 520, 0, F_R) + \
    build_chunks(TALK_W, ["un millón de personas", "ingresos", "paso a paso"], out_talk, 520, F_T, F_C) + \
    build_chunks(WA_W, ["escena por escena", "fotograma a fotograma", "una idea", "otros animales", "los personajes",
                        "VAIC", "Seedance", "crea las imágenes", "crea los vídeos"], out_wa, CAP_Y_TUT, F_U, F_C) + \
    build_chunks(CTA_W, ["paso a paso", "33", "PDF", "gratis", "300 y 500 dólares", "inteligencia artificial"],
                 out_cta, 1450, F_C, NF)
from hl_styles import plain_caption_pill
for c in chunks: c["im"] = hl_b(c["txt"]) if c["hl"] else (plain_caption_pill(c["txt"]) if F_U <= c["f0"] < F_C else plain_caption(c["txt"]))

# revenue screenshot: pops in on "esta cantidad (de ingresos)", stays until the hard cut to the CTA
CARD = revenue_card(REVENUE_PNG, "image")
CARD_F0 = int(round((out_talk(next(t for w, t in TALK_W if norm(w) == "esta")) + 0.08) * FPS))
CARD_F1 = int(round((out_talk(next(t for w, t in TALK_W if norm(w) == 'te')) + 0.02) * FPS))
CARD_OUT = 5
CARD_Y = 330
chunks = [c for c in chunks if not (CARD_F0 <= c['f0'] < CARD_F1)]

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
    vf = f"select='gte(n\\,{f0})',setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,format=rgb24"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", vf, "-vsync", "0", "-frames:v", str(n),
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    def nxt():
        b = p.stdout.read(W * H * 3)
        return np.frombuffer(b, np.uint8).reshape(H, W, 3) if len(b) == W * H * 3 else None
    return nxt

# ---------------- tutorial: screen recordings synced to the narration --------------
EDIT, RES = f"{P}/edit.mp4", f"{P}/res.mp4"
SW, SH = 720, 1564
# (narration time, source, source time): linear in between; jumps where the source changes
UMAP = [
    (0.55, "e", 0.0), (3.3, "e", 0.0),          # Claude home while "ir a Claude"
    (3.3, "e", 0.0), (9.9, "e", 5.8),           # typing "analiza este video y dame el detalle escena por escena"
    (9.9, "e", 5.8), (21.5, "e", 53.5),         # Claude extracting frames + audio -> analysis (sped up)
    (21.5, "e", 53.5), (24.3, "e", 60.3),       # analysis table, starts typing the idea prompt
    (24.3, "e", 60.3), (30.2, "e", 68.5),       # "ahora dame una idea ... usando otros animales" sent
    (30.2, "e", 68.5), (32.4, "e", 71.0),
    (32.4, "e", 71.0), (41.4, "e", 94.0),       # "La madriguera", 30 s version, "Cómo producirlo en VAIC"
    (41.4, "e", 94.0), (45.2, "e", 95.5),
    (45.2, "e", 95.5), (50.6, "e", 104.4),      # typing "usa vaic ... usa seedance en vaic ..." in sync
    (50.6, "e", 104.4), (58.6, "e", 204.5),     # Claude working with VAIC (sped up)
    (58.6, "e", 204.5), (61.2, "e", 208.0),     # summary sheet with the generated images
    (61.2, "e", 208.0), (62.3, "e", 210.7),     # generated image detail
    (62.3, "r", 0.8), (63.5, "r", 4.8),         # "Ya tienes el vídeo de 30 s generado con Seedance"
    (63.5, "r", 12.8), (66.2, "r", 16.9),       # the finished video playing
]
# never show iOS menus / control centre / notifications / link dialog / blank browser
FORBID = {"e": [(58.95, 59.75)], "r": [(0.0, 0.75), (5.1, 12.7), (17.0, 99)]}
def umap(w):
    for (w0, s0, t0), (w1, s1, t1) in zip(UMAP[0::2], UMAP[1::2]):
        if w0 <= w < w1 or (w1 == UMAP[-1][0] and w >= w0):
            t = t0 + (t1 - t0) * min(1.0, (w - w0) / max(1e-6, w1 - w0))
            for a, b in FORBID[s0]:
                if a <= t < b: t = b
            return s0, t
    return UMAP[-1][1], UMAP[-1][2]
class SeqReader:
    def __init__(self, src):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={SW}:{SH},format=rgb24", "-vsync", "0",
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
def screen_frame(fr):
    im = Image.fromarray(fr[SCR_TOP:SCR_TOP + int(round(H / SCR_SCALE))])
    return im.resize((W, H), Image.LANCZOS).convert("RGBA")

def render():
    guy = reader(GUY, A_OPEN, O_LEN + B_LEN)
    anim = reader(ANIM, 0, B_LEN)
    talk = reader(GUY, A_T0, T_LEN)
    cta = reader(CTA, C_T0, C_LEN)
    scr = {"e": SeqReader(EDIT), "r": SeqReader(RES)}
    enc = None
    if PREVIEW is None and CLIP is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{P}/mix_v4.wav", "-map", "0:v", "-map", "1:a",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    if CLIP:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-ss", str(CLIP[0]), "-t", str(CLIP[1] - CLIP[0]), "-i", f"{P}/mix_v4.wav",
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
            fr = talk()
        elif f < F_C:
            src, t = umap(wa_src(f - F_U))
            sf = scr[src].at(t); fr = None
            if need: canvas = screen_frame(sf)
        else:
            fr = cta()
        if not need: continue
        if fr is not None: canvas = Image.fromarray(fr).convert("RGBA")
        if CARD_F0 <= f < CARD_F1 + CARD_OUT:
            k = f - CARD_F0
            sc = 0.6 + 0.4 * ease_out_back(k / 9, 2.0); al = min(1, 0.2 + k / 4)
            if f >= CARD_F1:
                q = (f - CARD_F1 + 1) / CARD_OUT; sc *= 1 - 0.25 * q; al *= 1 - q
            place(canvas, CARD, 540, CARD_Y + CARD.height / 2 + (1 - ease_out_cubic(k / 8)) * 24, sc, al)
        for c in chunks:
            if c["f0"] <= f < c["f1"]: draw_caption(canvas, c, f - c["f0"], 540, c["y"], STYLE)
        out = np.asarray(canvas.convert("RGB"))
        if CLIP: enc.stdin.write(out.tobytes())
        elif want is not None: Image.fromarray(out).save(f"{P}/pv3_{f / FPS:06.2f}.png")
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
    put(sp(ga, A_T0, T_LEN) * ka, F_T)
    gw = load(f"{P}/wa.mp4"); kw = ref / rms(gw[int(1.0 * SR):int(66.0 * SR)])
    fu = F_U
    for a_, b_ in WA_KEEP:                            # tutorial narration (WhatsApp audio), pauses shortened
        n = int(round((b_ - a_) * FPS)); put(gw[int(a_ * SR):int(a_ * SR) + int(n / FPS * SR)] * kw, fu); fu += n
    put(sp(gc, C_T0, C_LEN), F_C)
    mix = mix[:int(NF / FPS * SR)]
    with wave.open(f"{P}/mix_v4_raw.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/mix_v4_raw.wav", "-af",
                    "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.94",
                    "-ar", "48000", f"{P}/mix_v4.wav"], check=True)

if __name__ == "__main__":
    for c in chunks: print(f"{c['f0'] / FPS:6.2f}-{c['f1'] / FPS:6.2f} {'[HL] ' if c['hl'] else ''}{c['txt']}")
    print("card", CARD_F0 / FPS, CARD_F1 / FPS, "total", NF / FPS)
    if (PREVIEW is None and CLIP is None) or (CLIP and not os.path.exists(f"{P}/mix_v4.wav")): audio()
    render()
