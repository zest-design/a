import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p19"
GUY = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/ff56ff9f-C15F23C5-3BB0-4072-B8CD-BC99C29AC8EB_1_1.mp4"
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
SIL = [(0.00, 0.67), (3.06, 3.28), (4.33, 4.47), (5.00, 5.18), (7.95, 8.09), (8.42, 8.82), (11.03, 11.19), (12.13, 12.51),
       (13.69, 13.99), (16.42, 16.71), (18.10, 18.25), (19.90, 20.29), (21.00, 21.15), (21.51, 21.77), (22.72, 22.84), (23.09, 23.24),
       (24.53, 24.90), (25.38, 36.36), (44.64, 45.13), (47.40, 47.76), (49.20, 49.37), (51.62, 51.77)]
END = 53.55; PAD = 0.04
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
    (0.67, 4.70, "El nivel de cosas que podemos crear con inteligencia artificial ya supera lo normal."),
    (5.18, 8.42, "Mira este vídeo de aquí. Ya se están usando inteligencia artificial"),
    (8.82, 15.95, "dentro de cámaras normales para detectar objetos, pelotas en este caso, analizar datos de manera completamente automática,"),
    (16.71, 25.38, "rendimiento de jugadores e incluso calculando el nivel de estadísticas para apuestas, sistemas y demás."),
    (36.36, 44.64, "Si tú quieres aprender a crear sistemas de análisis como esto, te preparé un PDF aquí para ti, así que comenta aquí abajo ANÁLISIS, que te envío un PDF con una guía"),
    (45.13, 53.55, "paso a paso en cómo tú puedes usar la inteligencia artificial para analizar datos a través de cámaras o incluso a través de vídeos o grabaciones televisivas."),
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
HL = [["ANÁLISIS"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if WORDS[i][0].startswith("ANÁLISIS"): return ["ANÁLISIS"]
    return next((p for p in HL if p != ["ANÁLISIS"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
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
    key = txt == "ANÁLISIS"
    if not hl: txt = txt.lower().replace("pdf", "PDF").replace("claude", "Claude")
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

# ================= Split screen: sports-analysis AI clip on top, presenter below =================
BROLL = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/c7a7e896-Video_Project_7_1.mp4"
TOP = 830                       # top panel height; clip is 1080x608 sitting at the bottom of it (clear of the IG top bar)
CLIP_W, CLIP_H = 980, 551; CLIP_X, CLIP_Y = 50, 262   # inside the IG safe area, rounded like a card
_m = Image.new("L", (CLIP_W, CLIP_H), 0); ImageDraw.Draw(_m).rounded_rectangle((0, 0, CLIP_W - 1, CLIP_H - 1), 26, fill=255)
CLIP_MASK = (np.asarray(_m, np.float32) / 255.0)[..., None]
SHIFT = 290                     # bottom panel shows his face centred
CAP_SPLIT, CAP_FULL = TOP - 22, 1505
TRANS = 9
KEY = next(c for c in chunks if c["key"])
F_SPLIT1 = 10 ** 9              # split screen stays until he stops talking (clip loops)
BG = np.zeros((TOP, W, 3), np.uint8) + np.array([14, 14, 16], np.uint8)
BROLL_VOL = 0.04                # clip audio kept very low, just a subtle bed

def broll_cmd():
    # skip the frozen stretch (10-38 s of the source): 0-10, then the moving part 43-62, then the start again
    segs = [(0, 10), (43, 62.2), (0, 12)]
    fc = ";".join(f"[0:v]trim=start={x}:end={y},setpts=PTS-STARTPTS[s{i}]" for i, (x, y) in enumerate(segs))
    fc += ";" + "".join(f"[s{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0,fps={FPS},scale={CLIP_W}:{CLIP_H}:flags=lanczos,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", BROLL, "-filter_complex", fc, "-map", "[o]", "-f", "rawvideo", "-"]

def audio_mix(events):
    sfx(events)
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.008:.4f}:d=0.008[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    endt = TOTAL
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume={BROLL_VOL},atrim=0:{endt:.3f},afade=t=out:st={endt - 0.6:.3f}:d=0.6[b];" \
        f"[1:a]volume=1.0[s];[v][s][b]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{P}/sfx.wav", "-stream_loop", "-1", "-i", BROLL, "-filter_complex", fc, "-map", "[o]", "-ar", "48000",
                    f"{P}/voice.wav"], check=True)

def events():
    return [("boom", KEY["f0"] / FPS)]

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
            fr[:edge] = panel[TOP - edge:TOP]
            canvas = Image.fromarray(fr).convert("RGBA")
        if f >= KEY["f0"]:   # keyword: big, centred on the top panel
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            paste(canvas, KEY["im"], 540, CLIP_Y + CLIP_H / 2, sc, min(1, 0.35 + k / 3))
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
