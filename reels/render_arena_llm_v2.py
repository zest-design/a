import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/a523e79c-ba27-50f9-be90-91ab18a28e09/scratchpad"
P = f"{S}/arena"
SRC = "/root/.claude/uploads/a523e79c-ba27-50f9-be90-91ab18a28e09/5e5ae131-anking_arena_llm_1_1.mp4"
SP = 1.1                      # whole talk sped up 1.1x (pitch kept): GUY is SRC run through setpts=PTS/1.1 + atempo=1.1
GUY = f"{P}/guy_fast.mov"
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


# ---------------- cuts -------------------------------------------------------------
# silences >= 0.12 s, plus the restart "Si tú usas AllPass de HostGator," (25.88-29.26) removed
SIL = [(0.00, 0.90), (9.24, 9.55), (10.17, 10.44), (12.06, 12.20), (12.72, 12.98), (16.67, 17.08), (19.90, 20.05), (21.45, 21.90), (23.60, 23.73),
       (24.97, 25.15), (25.88, 29.26), (31.83, 31.97), (32.33, 32.46), (35.83, 36.36), (36.76, 36.89), (37.45, 37.84), (38.37, 38.74),
       (39.16, 39.40), (40.12, 40.28), (40.86, 41.04), (43.58, 43.81), (46.35, 46.52), (47.23, 47.80), (48.21, 48.59), (52.85, 53.02),
       (54.34, 54.75), (59.46, 60.23), (60.87, 61.13), (67.81, 68.12), (68.63, 68.96), (70.27, 70.40)]
END = 73.66
# all times above are in the original recording; convert to the 1.1x clip
SIL = [(x / SP, y / SP) for x, y in SIL]; END /= SP
# subtle silence removal: pauses up to 0.18 s stay as they are, longer ones are trimmed to a short breath
# (0.07 s after the last word + 0.05 s before the next), the restart cut stays tight
CUT = (25.88 / SP, 29.26 / SP)
KEEP = []; cur = max(0, SIL[0][1] - 0.05)
for a, b in SIL[1:]:
    if (a, b) == CUT: KEEP.append((cur, a + 0.04)); cur = b - 0.04
    elif b - a > 0.18: KEEP.append((cur, a + 0.07)); cur = b - 0.05
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
PK = [(w, t / SP, e / SP) for w, t, e in json.load(open(f"{P}/wordsA.json"))]
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (0.90, 5.30, "¿Sabías que existe una página web con el ranking de todos los modelos de inteligencia artificial?"),
    (5.45, 12.40, "Hacen estudios con cada modelo y deciden cuál es el mejor para código, para imagen, para crear texto, para escribir correos, etc."),
    (12.90, 15.70, "Entra en esta web, la web se llama Arena LLM"),
    (15.85, 21.45, "y ahí puedes ver cuál es mejor en cada cosa y puedes decidirte por cuál suscribirte o cuál comprar."),
    (21.85, 25.88, "Pero aquí va un tip, un truco, un hack, llamémoslo así."),
    (29.26, 35.83, "HostGator tiene una herramienta llamada AllPass, donde tienen todas las inteligencias artificiales gratis dentro de una única suscripción."),
    (36.20, 46.35, "Pagas una vez y tienes Claude, ChatGPT, Gemini, todo dentro de una única herramienta y además puedes obligar que una cuestione la respuesta de la otra."),
    (46.35, 47.23, "Es increíble."),
    (47.60, 52.85, "Tienen de alguna forma todos los modelos allí gratis para ti, tú pagas solo una única suscripción."),
    (53.00, 59.46, "Además, ahora en noviembre, tienen la Black November y lo tienen tirado de precio. De verdad, no sé cómo ganan dinero esa gente."),
    (59.90, 67.81, "Comenta aquí HOST, que he preparado para ti un contenido completo con un paso a paso para que tú sepas cómo acceder a Arena LLM, ver los mejores modelos"),
    (67.81, 73.66, "y además cómo puedes contratar AllPass y así disfrutar de todos los modelos gratis en una única suscripción."),
]
SEGS = [(a / SP, b / SP, t) for a, b, t in SEGS]
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
HL = [["HOST"], ["hostgator"], ["black", "november"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if re.sub(r"[^A-Z]", "", WORDS[i][0]) == "HOST": return ["HOST"]
    return next((p for p in HL if p != ["HOST"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
NAMES = {"arena": "Arena", "llm": "LLM", "claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini", "hostgator": "HostGator",
         "allpass": "AllPass", "black": "Black", "november": "November"}
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
    key = txt == "HOST"
    if not hl: txt = " ".join(NAMES.get(w, w) for w in txt.lower().split())
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
TAGS = {"HostGator": ((14, 44, 120), (255, 204, 0)),          # dark blue tag, yellow text
        "Black November": ((9, 12, 30), (255, 204, 0))}       # navy almost black, yellow text
def make_caption(txt, hl, key):
    f = FK if key else FC
    box, ink = TAGS.get(txt, (RED, WHITE))
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 26, 14
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 24, w - 20, h - 16), 18, fill=(0, 0, 0, 110))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, w - 20, h - 20), 18, fill=box)
    else:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=f, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=f, fill=ink if hl else WHITE, anchor="mm")
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
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e - s - 0.02:.4f}:d=0.02[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[1:a]volume=1.0[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{P}/sfx.wav", "-filter_complex", fc, "-map", "[o]", "-ar", "48000", f"{P}/voice.wav"], check=True)
def guy_cmd():
    v = [f"[0:v]trim=start_frame={round(s * 30)}:end_frame={round(e * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=1:a=0,fps=30,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF), "-f", "rawvideo", "-"]

# ================= Split screen: arena.ai ranking recording on top (cropped to a card that follows the page, looped), presenter below =================
BROLL = f"{P}/broll_card.mp4"          # made by make_arena_card.py from the vertical screen recording
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
BROLL_VOL = 0.0                 # top clip muted

def broll_cmd():
    return ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", BROLL, "-vf", f"fps={FPS},scale={CLIP_W}:{CLIP_H}:flags=lanczos,format=rgb24", "-f", "rawvideo", "-"]

def audio_mix(events):
    sfx(events)
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e - s - 0.02:.4f}:d=0.02[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    endt = TOTAL
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[1:a]volume=1.0[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[o]"   # top clip is silent (muted)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", f"{P}/sfx.wav", "-filter_complex", fc, "-map", "[o]", "-ar", "48000",
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
