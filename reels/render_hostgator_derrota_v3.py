# Full-screen talking-head reel (HostGator AllPass "derrota"): silence trims, restart + CTA retakes removed,
# v2: captions on top (between the floating screen and his head while it shows), HostGator-style AllPass tag held ~2.2 s with a soft pop,
# minimal horizontal HostGator-style screens floating above his head.
# v3: he stays in one place the whole time (fixed 290 px lower, ceiling band stretched); captions sit where the screen goes,
# and move down between screen and head while a screen shows.
import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/tmp/claude-0/-home-user-a/a523e79c-ba27-50f9-be90-91ab18a28e09/scratchpad/derrota")
import hg_min as HG

S = "/tmp/claude-0/-home-user-a/a523e79c-ba27-50f9-be90-91ab18a28e09/scratchpad"
P = f"{S}/derrota"
GUY = "/root/.claude/uploads/a523e79c-ba27-50f9-be90-91ab18a28e09/5d1eea80-hostgator_-_derrota_1_1.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255); YELLOW = (255, 210, 0)
FD = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(FD + n, int(s))

# ---------------- edit (source times) ----------------------------------------------
# blocks in output order: talk up to "...que tú necesitas." | closing line recorded after the CTA | CTA take 3 (complete, clear "HOST")
BLOCKS = [(2.62, 58.24), (90.12, 97.92), (76.72, 83.50)]
SIL = [(6.89, 7.09), (8.72, 8.89), (9.18, 9.35), (10.04, 10.24), (11.66, 12.08), (12.46, 12.81), (13.30, 13.89), (14.90, 15.20),
       (16.21, 16.34), (17.17, 17.32), (19.32, 19.70), (20.27, 20.64), (26.47, 27.04), (29.95, 30.42), (32.76, 33.10), (33.44, 33.74),
       (33.97, 37.02),            # restart "Puedes hacerle preguntas a..." removed, the full retake follows
       (41.76, 42.12), (45.70, 46.21), (49.99, 50.29), (53.20, 53.57), (92.15, 92.28), (92.56, 92.68), (92.94, 93.08), (93.90, 94.25),
       (94.82, 95.39), (96.76, 96.94), (82.18, 82.87)]
CUTS_TIGHT = {(33.97, 37.02)}
KEEP = []
for b0, b1 in BLOCKS:
    cur = b0
    for a, b in SIL:
        if not (b0 < a and b < b1): continue
        if (a, b) in CUTS_TIGHT: KEEP.append((cur, a + 0.04)); cur = b - 0.04
        elif b - a > 0.18: KEEP.append((cur, a + 0.07)); cur = b - 0.05     # subtle: a short breath stays
    KEEP.append((cur, b1))
KEEP = [(round(a * 30) / 30, round(b * 30) / 30) for a, b in KEEP]
OFF = []; o = 0.0
for a, b in KEEP: OFF.append(o); o += b - a
NF = sum(round(b * 30) - round(a * 30) for a, b in KEEP); TOTAL = NF / FPS
def m(t):
    # source time -> output time (blocks are out of order, so look the segment up)
    for (a, b), o in zip(KEEP, OFF):
        if a <= t < b: return o + t - a
    best = None
    for (a, b), o in zip(KEEP, OFF):
        if b <= t < b + 0.8: best = o + b - a
        if a - 0.6 <= t < a and best is None: best = o
    return best if best is not None else 0.0

# ---------------- captions ----------------------------------------------------------
PK = json.load(open(f"{P}/wordsA.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (2.62, 7.00, "HostGator acaba de derrotar a todas las inteligencias artificiales."),
    (7.09, 11.70, "Han lanzado un producto llamado AllPass, que tiene todas las IAs: ChatGPT,"),
    (11.70, 18.80, "Claude, Grok, todas las chinas, todo lo que tú hoy pagas de suscripción está metido ahí."),
    (19.40, 26.47, "Es que además la suscripción a AllPass es mucho más barata que una sola, es más barata que ChatGPT, más barata que Claude."),
    (27.00, 33.97, "De verdad, no sé cómo ganan dinero esa gente, pero es increíble que en un único producto tenga todo ahí."),
    (37.02, 45.70, "Puedes hacerle preguntas al modelo que quieras y además puedes poner que un modelo cuestione la respuesta del otro. Eso es lo más increíble que he visto."),
    (46.00, 53.20, "Por último, lo más loco que he probado es que tú puedes crear tu propio agente, dejarlo guardado y cuando tú quieras hablar con él,"),
    (53.40, 58.24, "ahí simplemente pones al agente en la conversación y él responde en el momento que tú necesitas."),
    (90.12, 97.92, "Es increíble que ahora tú tengas todas las IAs en un único lugar y además por 10 veces menos el precio."),
    (76.72, 83.50, "Y si tú lo quieres probar, comenta aquí abajo HOST, que te voy a enviar un paso a paso completo para que tú lo puedas conseguir."),
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
    return [(w, m(t), k == len(ws) - 1, m(s1)) for k, (w, t) in enumerate(zip(ws, times))]   # -> output times
WORDS = []
for sg in SEGS: WORDS += align(*sg)
HL = [["HOST"], ["allpass"], ["hostgator"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if re.sub(r"[^A-Z]", "", WORDS[i][0]) == "HOST": return ["HOST"]
    return next((p for p in HL if p != ["HOST"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
NAMES = {"claude": "Claude", "chatgpt": "ChatGPT", "grok": "Grok", "ias": "IAs", "pdf": "PDF"}
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
    if k and chunks[k - 1]["key"]: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.0)   # captions hidden ~1 s on the keyword
    if k: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 0.3)
for k, c in enumerate(chunks):
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else 99
    c["t1"] = c["t0"] + 2.2 if c["txt"] == "AllPass" else min(nxt, c["end"] or nxt, c["t0"] + 1.6)
    c["f0"], c["f1"] = int(round(c["t0"] * FPS)), int(round(c["t1"] * FPS))

FC = font("InterDisplay-Bold.otf", 62); FK = font("InterDisplay-Black.otf", 120); FA = font("InterDisplay-Black.otf", 78)
def make_caption(txt, hl, key):
    if txt == "AllPass": return HG.allpass_tag()
    if False:
        f = FA; tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady, M = 34, 20, 44
        w, h = int(tw + 2 * padx + 2 * M), int(bb[3] - bb[1] + 2 * pady + 2 * M)
        box = (M, M, w - M, h - M)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gl = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle(box, 22, fill=(40, 120, 255, 170))
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(18)))
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((M, M + 6, w - M, h - M + 6), 22, fill=(0, 0, 0, 120))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        x = np.linspace(0, 1, w)[None, :, None]; y = np.linspace(0, 1, h)[:, None, None]
        c0, c1 = np.array([10, 52, 190]), np.array([38, 150, 255]); t_ = np.clip(x * 0.8 + y * 0.2, 0, 1)
        grad = Image.fromarray((c0 * (1 - t_) + c1 * t_).astype(np.uint8)).convert("RGBA")
        mk = Image.new("L", (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle(box, 22, fill=255)
        im.paste(grad, (0, 0), mk)
        ImageDraw.Draw(im).rounded_rectangle(box, 22, outline=(140, 200, 255), width=3)
        ImageDraw.Draw(im).text((w / 2, h / 2 - 3), txt, font=f, fill=YELLOW, anchor="mm")
        return im
    f = FK if key else FC
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 26, 14
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        boxc, ink = ((14, 44, 120), YELLOW) if txt == "HostGator" else (RED, WHITE)
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 24, w - 20, h - 16), 18, fill=(0, 0, 0, 110))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, w - 20, h - 20), 18, fill=boxc)
    else:
        ink = WHITE
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=f, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=f, fill=ink, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"], c["key"])
KEY = next(c for c in chunks if c["key"])

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def paste(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

# ---------------- audio ------------------------------------------------------------
SR = 48000
def sfx(events):
    rng = np.random.default_rng(9); trk = np.zeros(int((TOTAL + 1) * SR))
    def add(sig, t):
        s = int(t * SR); e = min(len(trk), s + len(sig)); trk[s:e] += sig[:e - s]
    n2 = int(0.16 * SR); t2 = np.arange(n2) / SR   # soft low pluck for the AllPass tag
    pluck = (np.sin(2 * np.pi * 330 * t2) * 0.6 + np.sin(2 * np.pi * 495 * t2) * 0.25) * (1 - np.exp(-t2 * 400)) * np.exp(-t2 * 26) * 0.07
    n4 = int(1.4 * SR); t4 = np.arange(n4) / SR
    boom = np.sin(2 * np.pi * (52 + 30 * np.exp(-t4 * 8)) * t4) * np.exp(-t4 * 3.2) * 0.32 + rng.standard_normal(n4) * np.exp(-t4 * 18) * 0.04
    pad = sum(np.sin(2 * np.pi * fq * t4) for fq in (440, 554.4, 659.3)) * np.exp(-t4 * 2.2) * (1 - np.exp(-t4 * 30)) * 0.02
    def _lp(x, fc):
        al = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s_ = 0.0
        for i_ in range(len(x)): s_ = (1 - al) * x[i_] + al * s_; y[i_] = s_
        return y
    nA = int(0.26 * SR); tA = np.arange(nA) / SR; rA = np.random.default_rng(3)
    xA = _lp(_lp(rA.standard_normal(nA), 700), 700); whoosh = xA / np.abs(xA).max() * np.sin(np.pi * tA / 0.26) ** 2 * 0.05
    nP = int(0.22 * SR); tP = np.arange(nP) / SR   # tag pop: low thump + the soft pluck + a faint airy tail
    thump = np.sin(2 * np.pi * (150 + 90 * np.exp(-tP * 40)) * tP) * np.exp(-tP * 22) * 0.12
    tagpop = thump.copy(); tagpop[:len(pluck)] += pluck * 1.2; tagpop[:len(whoosh) if len(whoosh) < nP else nP] += whoosh[:nP] * 0.5
    for kind, tt in events:
        if kind == "pluck": add(pluck, tt)
        elif kind == "tag": add(tagpop, tt)
        elif kind == "whoosh": add(whoosh, max(0, tt - 0.05))
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
def events():
    return [("tag", c["f0"] / FPS) for c in chunks if c["txt"] == "AllPass"] + [("whoosh", a) for a, b, _, _ in SCENES] + [("boom", KEY["f0"] / FPS)]

# ---------------- floating screens (output times) ------------------------------------
def fr(t): return int(round(t * FPS))
SCENES = [  # (in, out, scene, beats in frames after "in")
    (6.25, 14.90, HG.m_allias, [fr(8.16 - 6.25), fr(8.90 - 6.25), fr(9.21 - 6.25), fr(9.92 - 6.25)]),
    (17.10, 24.50, HG.m_barata, [fr(19.57 - 17.10), fr(20.61 - 17.10)]),
    (28.36, 36.85, HG.m_compara, [0, fr(33.17 - 28.36)]),
    (37.10, 48.40, HG.m_agente, [0, fr(41.24 - 37.10), fr(44.74 - 37.10)]),
    (48.60, 55.45, HG.m_10x, [fr(53.32 - 48.60)]),
]
SLIDE = [(6.25, 14.90), (17.10, 24.50), (28.36, 55.45)]   # short gaps between screens keep him down
SH = 290                     # how far he slides down while a screen shows (face is not scaled)
CARD_X, CARD_Y, CARD_S = 540, 568, 0.98
CAP_IDLE, CAP_MID = 568, 842   # where the screen goes / between screen and head
KEY_Y = 520                    # HOST in the free space above his head; captions under it
T_SL = 0.4
def slide_at(t):
    e = 0.0
    for a, b in SLIDE: e = max(e, ease_io_((t - a + T_SL) / T_SL) * (1 - ease_io_((t - b - 0.3) / T_SL)))   # down before the screen, up after it left
    return e
def ease_io_(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
CARD_CACHE = {}
def card_at(f):
    t = f / FPS
    for a, b, fn, beats in SCENES:
        if a <= t < b + 0.3:
            k = f - fr(a); im = fn(k, beats)
            im = HG.glow(im, (70, 100, 255), 28, 120, 70); im = im.resize((int(im.width * CARD_S), int(im.height * CARD_S)), Image.LANCZOS)
            ein = HG.ease_out_cubic(k / 10); eout = HG.ease_out_cubic((t - b) / 0.3) if t >= b else 0
            sc = (0.92 + 0.08 * HG.ease_out_back(k / 10)) * (1 - 0.04 * eout)
            al = min(1, k / 6) * (1 - eout)
            dy = (1 - ein) * 40 + eout * 24 + 5 * math.sin(2 * math.pi * t / 3.2)
            return im, sc, al, dy
    return None
def shifted(guy, e):
    sh = int(round(SH * e))
    if sh == 0: return Image.fromarray(guy)
    out = np.empty_like(guy)
    band = Image.fromarray(guy[:230]).resize((W, 230 + sh), Image.BICUBIC)      # only ceiling/wall stretched
    out[:230 + sh] = np.asarray(band); out[230 + sh:] = guy[230:H - sh]
    return Image.fromarray(out)

def main():
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        audio(events())
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        t = f / FPS; e = 1.0 if t >= SCENES[-1][1] else slide_at(t)    # e: caption between screen and head (always during the CTA)
        canvas = shifted(guy, 1.0).convert("RGBA")                      # fixed position, no up/down movement
        cd = card_at(f)
        if cd: paste(canvas, cd[0], CARD_X, CARD_Y + cd[3], cd[1], cd[2])
        if f >= KEY["f0"]:
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            paste(canvas, KEY["im"], 540, KEY_Y, sc, min(1, 0.35 + k / 3))
        cap_y = CAP_IDLE * (1 - e) + CAP_MID * e
        tag_on = any(c["txt"] == "AllPass" and c["f0"] <= f < c["f1"] for c in chunks)
        for ch in chunks:
            if ch["key"] or not (ch["f0"] <= f < ch["f1"]) or KEY["f0"] <= f < KEY["f0"] + FPS: continue
            if tag_on and ch["txt"] != "AllPass": continue          # the tag holds the caption spot for ~2.2 s
            k = f - ch["f0"]
            if ch["txt"] == "AllPass":
                sc = (0.5 + 0.5 * ease_out_back(k / 9, 2.2)) * (0.82 - 0.04 * e) * (1 + 0.02 * math.sin(k / FPS * 2 * math.pi * 1.2))
                al = min(1, 0.3 + k / 3) * (1 - max(0, (f - (ch["f1"] - 6)) / 6))
                paste(canvas, ch["im"], 540, cap_y, sc, al)
            else:
                paste(canvas, ch["im"], 540, cap_y + (1 - ease_out_cubic(k / 5)) * 8, 0.86 + 0.14 * ease_out_back(k / 5), min(1, 0.35 + k / 3))
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "key", round(KEY["f0"] / FPS, 2), file=sys.stderr)
    main()
