import json, subprocess, sys, re, wave, difflib, os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hl_styles
from hl_styles import (plain_caption, hl_b, draw_caption, revenue_card, png_cutout,
                       ease_out_back, ease_out_cubic)

S = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/scratchpad"
P = f"{S}/w"
GUY, ANIM, CTA = f"{P}/a.mp4", f"{P}/b.mp4", f"{P}/cta.mp4"
REVENUE_PNG = "/tmp/claude-0/-home-user-a/554950d3-6299-51b1-a335-bfdd1ea7030a/images/1.png"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{P}/out_v3.mp4"
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
F_C = F_T + T_LEN
C_T0, C_LEN = 15, 667                  # CTA src 0.50 .. 22.73 s
NF = F_C + C_LEN

def out_open(t): return t - A_OPEN / FPS
def out_talk(t): return F_T / FPS + t - A_T0 / FPS
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

chunks = build_chunks(OPEN_W, ["este vídeo"], out_open, 520, 0, F_R) + \
    build_chunks(TALK_W, ["un millón de personas", "ingresos", "paso a paso"], out_talk, 520, F_T, F_C) + \
    build_chunks(CTA_W, ["paso a paso", "33", "PDF", "gratis", "300 y 500 dólares", "inteligencia artificial"],
                 out_cta, 330, F_C, NF)
for c in chunks: c["im"] = hl_b(c["txt"]) if c["hl"] else plain_caption(c["txt"])

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

def render():
    guy = reader(GUY, A_OPEN, O_LEN + B_LEN)
    anim = reader(ANIM, 0, B_LEN)
    talk = reader(GUY, A_T0, T_LEN)
    cta = reader(CTA, C_T0, C_LEN)
    enc = None
    if PREVIEW is None and CLIP is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{P}/mix_v3.wav", "-map", "0:v", "-map", "1:a",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    if CLIP:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-ss", str(CLIP[0]), "-t", str(CLIP[1] - CLIP[0]), "-i", f"{P}/mix_v2.wav",
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
        elif f < F_C:
            fr = talk()
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
    put(sp(gc, C_T0, C_LEN), F_C)
    mix = mix[:int(NF / FPS * SR)]
    with wave.open(f"{P}/mix_v3_raw.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/mix_v3_raw.wav", "-af",
                    "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.94",
                    "-ar", "48000", f"{P}/mix_v3.wav"], check=True)

if __name__ == "__main__":
    for c in chunks: print(f"{c['f0'] / FPS:6.2f}-{c['f1'] / FPS:6.2f} {'[HL] ' if c['hl'] else ''}{c['txt']}")
    print("card", CARD_F0 / FPS, CARD_F1 / FPS, "total", NF / FPS)
    if PREVIEW is None and CLIP is None: audio()
    render()
