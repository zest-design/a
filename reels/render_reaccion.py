import json, subprocess, sys, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/scratchpad"
P = f"{S}/w"
GUY, ANIM, CTA = f"{P}/a.mp4", f"{P}/b.mp4", f"{P}/cta.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P}/out.mp4"
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)

FD = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FD + name, int(size))

# ---------------- timeline (output frames) -----------------------------------------
# O: keyed open  -> guy (cut-out) over the animation, "mira este vídeo"
# R: reaction    -> animation full frame + guy box bottom-left (no cut, synced)
# T: talk        -> guy full frame (dead 30-44.6 s of the source removed)
# C: CTA         -> CTA_FINAL full frame (leading / trailing silence removed)
XF = 6                                   # soft dissolve on every cut (0.2 s), no zoom change
A_OPEN = 48                              # guy source frame at output frame 0  (1.60 s)
F_R = 51                                 # reaction starts (guy src 3.30 s)
B_LEN = 902                              # animation frames (30.07 s)
F_T = B_LEN - XF                         # talk starts, overlapping the animation tail
A_T0, T_LEN = 1339, 340                  # guy src 44.63 s .. 55.97 s
F_C = F_T + T_LEN - XF
C_T0, C_LEN = 15, 667                    # CTA src 0.50 s .. 22.73 s
NF = F_C + C_LEN

def out_guy_open(t): return t - A_OPEN / FPS
def out_guy_talk(t): return F_T / FPS + t - A_T0 / FPS
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
CTA_W = []
for s0, s1, txt in [
    (0.2, 5.0, "Y si quieres el paso a paso completo, comenta aquí abajo 33 que te lo haré llegar."),
    (5.7, 12.3, "He preparado un PDF completo para ti y te lo voy a enviar totalmente gratis. Comenta aquí abajo 33."),
    (12.35, 19.3, "Y además te voy a enviar un vídeo de cómo generar entre 300 y 500 dólares todos los días usando inteligencia artificial."),
    (19.35, 22.7, "Comenta aquí abajo 33 y te enviaré el PDF y el vídeo."),
]:
    CTA_W += align(PK_C, s0, s1, txt)

# ---------------- captions: white lowercase, red box on highlights ------------------
PUNCT = re.compile(r"[.,?:!]$")
FIX = [("pdf", "PDF"), (" ia", " IA")]
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
        for a, b in FIX: txt = re.sub(rf"\b{a.strip()}\b", b.strip(), txt)
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

chunks = build_chunks(OPEN_W, ["este vídeo"], out_guy_open, 1590, 0, F_R) + \
    build_chunks(TALK_W, ["un millón de personas", "ingresos", "paso a paso"], out_guy_talk, 1590, F_T + XF // 2, F_C + XF // 2) + \
    build_chunks(CTA_W, ["paso a paso", "33", "PDF", "gratis", "300 y 500 dólares", "inteligencia artificial"],
                 out_cta, 1450, F_C + XF // 2, NF)

def shadow_layer(size, box, radius, blur, alpha, offset=(0, 10), color=(0, 0, 0)):
    sh = Image.new("RGBA", size, (0, 0, 0, 0)); x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]), radius, fill=color + (alpha,))
    return sh.filter(ImageFilter.GaussianBlur(blur))
FC = font("InterDisplay-Bold.otf", 64)
def make_caption(txt, hl):
    tw = FC.getlength(txt); bb = FC.getbbox(txt); padx, pady = 22, 12
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if hl:
        im.alpha_composite(shadow_layer((w, h), (20, 20, w - 20, h - 20), 16, 8, 50, (0, 4)))
        d.rounded_rectangle((20, 20, w - 20, h - 20), 16, fill=RED)
    else:
        g_ = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g_).text((w / 2, h / 2 - 2), txt, font=FC, fill=(0, 0, 0, 200), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, 200))
        im.alpha_composite(g_.filter(ImageFilter.GaussianBlur(7))); d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2 - 2), txt, font=FC, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"])

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def paste(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    x, y = int(x - im.width / 2), int(y - im.height / 2)
    canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))

# ---------------- sources ----------------------------------------------------------
def reader(src, f0, n, extra=""):
    vf = f"select='gte(n\\,{f0})',setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos{extra},format=rgb24"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", vf, "-vsync", "0", "-frames:v", str(n),
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    def nxt():
        b = p.stdout.read(W * H * 3)
        return np.frombuffer(b, np.uint8).reshape(H, W, 3) if len(b) == W * H * 3 else None
    return nxt

# reaction box: head-and-shoulders crop of the guy, bottom-left (as in the model video)
BOX_W, BOX_H, BOX_X, BOX_Y = 500, 578, 22, 1196
CROP = (30, 615, 870, 1586)                     # in 1080x1920 guy coords (same 0.865 aspect)
MASKS = f"{P}/masks"
def keyed(guy, bg, af):
    m = Image.open(f"{MASKS}/{af:04d}.png").convert("L").resize((W, H), Image.BILINEAR)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
    return (guy.astype(np.float32) * m + bg.astype(np.float32) * (1 - m)).astype(np.uint8)

def render():
    g_open = reader(GUY, A_OPEN, B_LEN)          # guy frames for O + R (box)
    g_talk = reader(GUY, A_T0, T_LEN)
    anim = reader(ANIM, 0, B_LEN)
    cta = reader(CTA, C_T0, C_LEN)
    enc = None
    if PREVIEW is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{P}/mix.wav", "-map", "0:v", "-map", "1:a",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = None if PREVIEW is None else {int(round(t * FPS)) for t in PREVIEW}
    last_t = None
    for f in range(NF):
        fr_r = fr_t = fr_c = None
        if f < B_LEN:
            gb, bg = g_open(), anim()
            if f < F_R:
                fr_r = keyed(gb, bg, A_OPEN + f) if (want is None or f in want) else bg
            else:
                fr_r = bg.copy()
                box = Image.fromarray(gb).crop(CROP).resize((BOX_W, BOX_H), Image.LANCZOS)
                fr_r[BOX_Y:BOX_Y + BOX_H, BOX_X:BOX_X + BOX_W] = np.asarray(box)
        if F_T <= f < F_T + T_LEN: fr_t = g_talk(); last_t = fr_t
        if f >= F_C: fr_c = cta()
        if fr_r is not None and fr_t is not None:
            e = ease_io((f - F_T + 1) / (XF + 1)); fr = (fr_r * (1 - e) + fr_t * e).astype(np.uint8)
        elif fr_t is not None and fr_c is not None:
            e = ease_io((f - F_C + 1) / (XF + 1)); fr = (fr_t * (1 - e) + fr_c * e).astype(np.uint8)
        else:
            fr = next(x for x in (fr_r, fr_t, fr_c) if x is not None)
        if want is not None and f not in want: continue
        canvas = Image.fromarray(fr).convert("RGBA")
        for c in chunks:
            if not (c["f0"] <= f < c["f1"]): continue
            k = f - c["f0"]
            a = min(1, 0.35 + k / 3)
            if c["f1"] - f <= 3: a *= (c["f1"] - f) / 4 if c["f1"] in (F_R, F_C + XF // 2) else 1
            paste(canvas, c["im"], 540, c["y"] + (1 - ease_out_cubic(k / 5)) * 8,
                  scale=0.86 + 0.14 * ease_out_back(k / 5), alpha=a)
        out = np.asarray(canvas.convert("RGB"))
        if want is not None: Image.fromarray(out).save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
        if f % 300 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    if enc: enc.stdin.close(); enc.wait()

# ---------------- audio ------------------------------------------------------------
SR = 48000
def load(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def rms(x): return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
def ramp(n, up=True):
    r = np.linspace(0, 1, n, dtype=np.float32); r = r * r * (3 - 2 * r)
    return (r if up else r[::-1])[:, None]
def audio():
    ga, gb, gc = load(GUY), load(ANIM), load(CTA)
    sp = lambda x, a, b: x[int(a * SR):int(b * SR)]
    # level-match the two voices (speech-only windows) and the animation soundtrack
    ref = rms(sp(gc, 0.5, 22.7))
    ka = ref / rms(sp(ga, 44.7, 55.9)); kb = ref / rms(gb) * 0.85
    tot = int(NF / FPS * SR) + SR
    mix = np.zeros((tot, 2), np.float32)
    def put(seg, at, fin=0.0, fout=0.0):
        seg = seg.copy(); s = int(at * SR)
        if fin: n = int(fin * SR); seg[:n] *= ramp(n)
        if fout: n = int(fout * SR); seg[-n:] *= ramp(n, False)
        mix[s:s + len(seg)] += seg[:tot - s]
    xf = XF / FPS
    put(sp(ga, A_OPEN / FPS, (A_OPEN + B_LEN) / FPS) * ka, 0, 0.01, xf)          # open + reaction room/voice
    anim_a = gb[:int(B_LEN / FPS * SR)] * kb
    duck = np.ones((len(anim_a), 1), np.float32)
    d0, d1 = int(1.62 * SR), int(2.05 * SR)
    duck[:d0] = 0.28; duck[d0:d1] = 0.28 + 0.72 * ramp(d1 - d0)
    put(anim_a * duck, 0, 0.0, xf)
    put(sp(ga, A_T0 / FPS, (A_T0 + T_LEN) / FPS) * ka, F_T / FPS, xf, xf)        # talk
    put(sp(gc, C_T0 / FPS, (C_T0 + C_LEN) / FPS) * 1.0, F_C / FPS, xf, 0.12)    # CTA
    mix = mix[:int(NF / FPS * SR)]
    with wave.open(f"{P}/mix_raw.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/mix_raw.wav", "-af",
                    "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.94",
                    "-ar", "48000", f"{P}/mix.wav"], check=True)

if __name__ == "__main__":
    for c in chunks: print(f"{c['f0'] / FPS:6.2f}-{c['f1'] / FPS:6.2f} {'[HL] ' if c['hl'] else ''}{c['txt']}")
    if PREVIEW is None: audio()
    render()
