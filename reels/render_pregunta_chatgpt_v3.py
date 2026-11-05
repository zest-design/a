# "Pregunta a ChatGPT" reel (HostGator AllPass): 1.1x, subtle silence trims, restart + doubled word removed,
# cut to the ChatGPT voice-mode recording synced to the WhatsApp audio (denoised), HostGator-style tags and floating screens
# (same look as hostgator_derrota_v3: presenter fixed in one spot, captions where the screen goes, under it while it shows).
import json, subprocess, sys, math, re, wave, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/tmp/claude-0/-home-user-a/a523e79c-ba27-50f9-be90-91ab18a28e09/scratchpad/derrota")
import hg_min as HG

S = "/tmp/claude-0/-home-user-a/a523e79c-ba27-50f9-be90-91ab18a28e09/scratchpad"
P = f"{S}/gpt"
GUY = f"{P}/guy_fast.mov"      # presenter, 1.1x (setpts/1.1 + atempo 1.1, light denoise)
AUD = f"{P}/A_fast.wav"        # WhatsApp audio of the ChatGPT talk, 1.1x, denoised + levelled
TOPCLIP = "/root/.claude/uploads/a523e79c-ba27-50f9-be90-91ab18a28e09/0febe1b5-1105_51.mp4"   # v3: HostGator boxing clip, split screen on the intro
REC = f"{P}/rec_fast.mp4"      # ChatGPT voice-mode screen recording, 1.1x, cropped to the orb (no chat history shown)
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30; SP = 1.1
RED = (229, 22, 34); WHITE = (255, 255, 255); YELLOW = (255, 210, 0)
FD = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(FD + n, int(s))

# ---------------- edit (ORIGINAL times; converted to the 1.1x clips below) -----------------
# guy blocks in output order; "gpt" parts: (audio start, audio end, recording time at audio start) - the orb grows when ChatGPT talks
EDIT = [
    ("guy", 1.02, 7.66),                    # "¿Qué pasa si le preguntas a ChatGPT...? Vamos a verlo."
    ("gpt", 1.42, 6.62, 8.82),              # him: "Hola chat, ¿cómo hago para tener todos los modelos...?"
    ("gpt", 7.58, 13.82, 14.43),            # ChatGPT: "Te sugiero contratar AllPass de HostGator..."
    ("gpt", 14.66, 21.82, 22.11),           # him: "Si yo contrato AllPass de HostGator, ¿puedo usar Claude, ChatGPT, Grok...?"
    ("gpt", 22.56, 25.30, 30.06),           # ChatGPT: "Sí, así es, correcto, que están de Black November."
    ("gpt", 26.02, 27.42, 34.67),           # him: "Ah, perfecto, gracias."
    ("gpt", 28.26, 29.00, 36.96),           # ChatGPT: "De nada."
    ("guy", 15.92, 47.40),                  # restart "Aquí vemos... usar un" (10.8-15.9) removed; "...alguna que otra suscripción."
    ("guy", 57.62, 69.30),                  # closing point recorded after the CTA, moved before it
    ("guy", 47.76, 57.34),       # ends right on "usarlo", before the breath for the next sentence                  # CTA: "...comenta aquí abajo HOST..."
]
SIL = {"guy": [(2.94, 3.12), (3.98, 4.17), (5.78, 6.07), (6.36, 6.50), (6.59, 6.77), (19.19, 19.32), (20.15, 20.49), (26.13, 26.42),
               (28.38, 28.78),          # doubled "por" ("20 euros por por ChatGPT") removed
               (29.59, 29.81), (29.86, 30.12), (32.97, 33.13), (34.08, 34.28), (34.87, 35.24), (36.91, 37.06), (37.23, 37.43),
               (39.82, 40.10), (42.12, 42.27), (44.36, 44.68), (50.96, 51.08), (53.66, 54.05), (59.00, 59.16), (61.51, 61.87),
               (62.74, 62.89), (63.78, 64.15), (68.23, 68.37), (68.53, 68.65)],
       "gpt": [(2.19, 2.41), (3.31, 3.46), (10.19, 10.46), (18.87, 19.11), (20.09, 20.68)]}
TIGHT = {(28.38, 28.78)}
KEEP = []   # (src, a, b, rec_offset) in 1.1x time
for it in EDIT:
    src, b0, b1 = it[0], it[1], it[2]; off = (it[3] - it[1]) if src == "gpt" else 0.0
    cur = b0
    for a, b in SIL[src]:
        if not (b0 < a and b < b1): continue
        if (a, b) in TIGHT: KEEP.append((src, cur, a, off)); cur = b
        elif b - a > 0.18: KEEP.append((src, cur, a + 0.07, off)); cur = b - 0.05      # subtle: a short breath stays
    KEEP.append((src, cur, b1, off))
KEEP = [(s_, round(a / SP * 30) / 30, round(b / SP * 30) / 30, o / SP) for s_, a, b, o in KEEP]
OFF = []; o = 0.0
for _, a, b, _ in KEEP: OFF.append(o); o += b - a
NFR = [round(b * 30) - round(a * 30) for _, a, b, _ in KEEP]; NF = sum(NFR); TOTAL = NF / FPS
def m(t, src):
    # original source time -> output time
    t = t / SP
    for (s_, a, b, _), o in zip(KEEP, OFF):
        if s_ == src and a <= t < b: return o + t - a
    best = None
    for (s_, a, b, _), o in zip(KEEP, OFF):
        if s_ != src: continue
        if b <= t < b + 0.8: best = o + b - a
        if a - 0.6 <= t < a and best is None: best = o
    return best if best is not None else 0.0

# ---------------- captions ----------------------------------------------------------
PKS = {"guy": json.load(open(f"{P}/wordsA.json")), "gpt": json.load(open(f"{P}/wordsAud.json"))}
def norm(s): return re.sub(r"[^\wáéíóúñü€]", "", s.lower())
SEGS = [
    ("guy", 1.02, 7.48, "¿Qué pasa si le preguntas a ChatGPT cómo puedes usar todos los modelos de inteligencia artificial gratis? Vamos a verlo."),
    ("gpt", 1.42, 6.62, "Hola, chat, ¿cómo hago para tener todos los modelos de inteligencia artificial gratis?"),
    ("gpt", 7.58, 13.82, "Te sugiero contratar AllPass de HostGator. Una sola suscripción y usas todos los modelos gratis."),
    ("gpt", 14.66, 21.82, "Si yo contrato AllPass de HostGator, ¿yo puedo usar Claude, ChatGPT, Grok, todos allí dentro gratis?"),
    ("gpt", 22.56, 25.30, "Sí, así es, correcto, y están de Black November."),
    ("gpt", 26.02, 27.42, "¡Ah, perfecto, gracias!"),
    ("gpt", 28.26, 29.00, "De nada."),
    ("guy", 15.92, 19.19, "Aquí vemos la respuesta de ChatGPT, nos recomienda usar AllPass."),
    ("guy", 19.32, 26.13, "AllPass es un programa de HostGator que tiene todos los modelos de inteligencia artificial dentro de una única suscripción."),
    ("guy", 26.42, 33.30, "En vez de pagar 20 € por ChatGPT, 20 € por Claude, 20 € por Grok, por Gemini, etcétera,"),
    ("guy", 33.30, 39.82, "tú pagas una vez, solo una suscripción, y tienes todos de manera totalmente gratuita, de verdad."),
    ("guy", 39.82, 47.34, "No sé cómo HostGator gana dinero con esto, y espero que vean este vídeo y nos den de regalo alguna que otra suscripción."),
    ("guy", 57.62, 62.74, "Aprovecha para usar todos los modelos de inteligencia artificial gratis, y además, allí dentro de AllPass,"),
    ("guy", 62.89, 69.20, "lo he probado, se puede poner que uno discuta con el otro para darte siempre la mejor respuesta posible."),
    ("guy", 47.76, 57.34, "Si tú quieres el paso a paso completo para aprender a usar esta herramienta, AllPass de HostGator, comenta aquí abajo HOST, que te envío un contenido con el paso a paso completo para que tú puedas usarlo."),
]
def align(src, s0, s1, text):
    ws = text.split(); PK = PKS[src]
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
    return [(w, m(t, src), k == len(ws) - 1, m(s1, src), src) for k, (w, t) in enumerate(zip(ws, times))]
WORDS = []
for sg in SEGS: WORDS += align(*sg)
HL = [["HOST"], ["allpass"], ["hostgator"], ["black", "november"]]
PUNCT = re.compile(r"[.,?:!]$")
def hl_at(i):
    if re.sub(r"[^A-Z]", "", WORDS[i][0]) == "HOST": return ["HOST"]
    return next((p for p in HL if p != ["HOST"] and [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
NAMES = {"claude": "Claude", "chatgpt": "ChatGPT", "grok": "Grok", "gemini": "Gemini", "€": "€"}
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
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1], end=end, key=key, src=g[0][4]))
# tags: AllPass/HostGator get their tag at most every 8 s (they come up a lot); the rest stay normal captions
last = {}
for c in chunks:
    if c["hl"] and not c["key"]:
        key_t = next(x["t0"] for x in chunks if x["key"])
        if (c["txt"] in last and c["t0"] - last[c["txt"]] < 8) or (c["txt"] == "AllPass" and key_t - 3 < c["t0"] < key_t): c["hl"] = False
        else: last[c["txt"]] = c["t0"]
for k, c in enumerate(chunks):
    if k and chunks[k - 1]["key"]: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.0)
    if k: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 0.3)
for k, c in enumerate(chunks):
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else 99
    c["t1"] = c["t0"] + 2.2 if (c["txt"] == "AllPass" and c["hl"]) else min(nxt, c["end"] or nxt, c["t0"] + 1.6)
    c["f0"], c["f1"] = int(round(c["t0"] * FPS)), int(round(c["t1"] * FPS))

FC = font("InterDisplay-Bold.otf", 62); FK = font("InterDisplay-Black.otf", 120)
TAGS = {"HostGator": ((14, 44, 120), YELLOW), "Black November": ((9, 12, 30), YELLOW)}
def make_caption(txt, hl, key):
    if txt == "AllPass" and hl: return HG.allpass_tag()
    f = FK if key else FC
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 26, 14
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        boxc, ink = TAGS.get(txt, (RED, WHITE))
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
def ease_io(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def paste(canvas, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

# ---------------- floating screens (guy source times -> output) -----------------------------
def O(t): return m(t, "guy")
def fr(t): return int(round(t * FPS))
SCENES = [  # (in, out, scene, beats in frames after "in") - all in output seconds
    (O(19.73), O(26.13) + 0.3, HG.m_allias, [fr(O(22.9) - O(19.73)) + 4 * j for j in range(4)]),
    (O(26.42), O(39.6), HG.m_euros, [fr(O(28.85) - O(26.42)), fr(O(30.69) - O(26.42)), fr(O(31.81) - O(26.42)), fr(O(34.29) - O(26.42))]),
    (O(62.95), O(69.0) + 0.3, HG.m_compara, [fr(O(64.26) - O(62.95)), fr(O(65.38) - O(62.95))]),
]
CARD_X, CARD_Y, CARD_S = 540, 568, 0.98
SH = 290                          # presenter fixed 290 px lower the whole time (ceiling band stretched), never moves
CAP_IDLE, CAP_MID, CAP_GPT = 568, 842, 1330
KEY_Y = 520
T_SL = 0.4
def vis(t):
    e = 0.0
    for a, b, _, _ in SCENES: e = max(e, ease_io((t - a + T_SL) / T_SL) * (1 - ease_io((t - b - 0.3) / T_SL)))
    return e
def card_at(f):
    t = f / FPS
    for a, b, fn, beats in SCENES:
        if a <= t < b + 0.3:
            k = f - fr(a); im = fn(k, beats)
            im = HG.glow(im, (70, 100, 255), 28, 120, 70); im = im.resize((int(im.width * CARD_S), int(im.height * CARD_S)), Image.LANCZOS)
            ein = ease_out_cubic(k / 10); eout = ease_out_cubic((t - b) / 0.3) if t >= b else 0
            sc = (0.92 + 0.08 * ease_out_back(k / 10)) * (1 - 0.04 * eout); al = min(1, k / 6) * (1 - eout)
            dy = (1 - ein) * 40 + eout * 24 + 5 * math.sin(2 * math.pi * t / 3.2)
            return im, sc, al, dy
    return None
def shifted(guy):
    out = np.empty_like(guy)
    out[:230 + SH] = np.asarray(Image.fromarray(guy[:230]).resize((W, 230 + SH), Image.BICUBIC)); out[230 + SH:] = guy[230:H - SH]
    return out
# ChatGPT label on the recording (it is cropped to the orb, so say what it is)
def gpt_chip():
    f = HG.F(40, 700); lg = HG.logo("chatgpt", 64); w = int(64 + 18 + f.getlength("ChatGPT") + 52); h = 88
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(255, 255, 255, 235), outline=(225, 228, 236), width=2)
    im.alpha_composite(lg, (14, 12)); d.text((14 + 64 + 18, h / 2), "ChatGPT", font=f, fill=(20, 22, 30), anchor="lm")
    sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((30, 36, w + 30, h + 36), h // 2, fill=(0, 0, 0, 50))
    sh = sh.filter(ImageFilter.GaussianBlur(12)); sh.alpha_composite(im, (30, 30)); return sh
GPT_CHIP = gpt_chip()

# ---------------- audio ------------------------------------------------------------
SR = 48000
def sfx(events):
    rng = np.random.default_rng(9); trk = np.zeros(int((TOTAL + 1) * SR))
    def add(sig, t):
        s = int(t * SR); e = min(len(trk), s + len(sig)); trk[s:e] += sig[:e - s]
    def _lp(x, fc):
        al = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s_ = 0.0
        for i_ in range(len(x)): s_ = (1 - al) * x[i_] + al * s_; y[i_] = s_
        return y
    n2 = int(0.16 * SR); t2 = np.arange(n2) / SR
    pluck = (np.sin(2 * np.pi * 330 * t2) * 0.6 + np.sin(2 * np.pi * 495 * t2) * 0.25) * (1 - np.exp(-t2 * 400)) * np.exp(-t2 * 26) * 0.07
    nA = int(0.26 * SR); tA = np.arange(nA) / SR; rA = np.random.default_rng(3)
    xA = _lp(_lp(rA.standard_normal(nA), 700), 700); whoosh = xA / np.abs(xA).max() * np.sin(np.pi * tA / 0.26) ** 2 * 0.05
    nP = int(0.22 * SR); tP = np.arange(nP) / SR
    thump = np.sin(2 * np.pi * (150 + 90 * np.exp(-tP * 40)) * tP) * np.exp(-tP * 22) * 0.12
    tagpop = thump.copy(); tagpop[:len(pluck)] += pluck * 1.2; nW = min(len(whoosh), nP); tagpop[:nW] += whoosh[:nW] * 0.5
    n4 = int(1.4 * SR); t4 = np.arange(n4) / SR
    boom = np.sin(2 * np.pi * (52 + 30 * np.exp(-t4 * 8)) * t4) * np.exp(-t4 * 3.2) * 0.32 + rng.standard_normal(n4) * np.exp(-t4 * 18) * 0.04
    pad = sum(np.sin(2 * np.pi * fq * t4) for fq in (440, 554.4, 659.3)) * np.exp(-t4 * 2.2) * (1 - np.exp(-t4 * 30)) * 0.02
    for kind, tt in events:
        if kind == "tag": add(tagpop, tt)
        elif kind == "whoosh": add(whoosh, max(0, tt - 0.05))
        elif kind == "boom": add(boom + pad, tt)
    st = np.stack([trk, trk], 1)
    with wave.open(f"{P}/sfx.wav", "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
def audio(events):
    sfx(events)
    parts = []
    for i, (s_, a, b, _) in enumerate(KEEP):
        inp = 0 if s_ == "guy" else 1
        parts.append(f"[{inp}:a]atrim=start={a:.5f}:end={b:.5f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,"
                     f"afade=t=in:d={0.02 if s_ == 'guy' else 0.04},afade=t=out:st={b - a - (0.06 if i == len(KEEP) - 1 else 0.02 if s_ == 'guy' else 0.05):.4f}:d={0.06 if i == len(KEEP) - 1 else 0.02 if s_ == 'guy' else 0.05}[a{i}]")
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];" \
        f"[2:a]volume=1.0[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-i", AUD, "-i", f"{P}/sfx.wav", "-filter_complex", fc, "-map", "[o]", "-ar", "48000", f"{P}/voice.wav"], check=True)
def video_cmd(src, path):
    segs = [(a, b, o) for s_, a, b, o in KEEP if s_ == src]
    v = [f"[0:v]trim=start_frame={round((a + o) * 30)}:end_frame={round((a + o) * 30) + round(b * 30) - round(a * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (a, b, o) in enumerate(segs)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0,fps=30,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", path, "-filter_complex", vf, "-map", "[o]", "-f", "rawvideo", "-"]
def events():
    ev = [("tag", c["f0"] / FPS) for c in chunks if c["txt"] == "AllPass" and c["hl"]] + [("whoosh", a) for a, _, _, _ in SCENES]
    ev += [("whoosh", OFF[i]) for i, k in enumerate(KEEP) if i and k[0] != KEEP[i - 1][0]]     # soft swipe on the cuts to/from ChatGPT
    return ev + [("boom", KEY["f0"] / FPS)]
# ---------------- intro split screen (same layout as the earlier split reels) ----------------
TOP = 830; CLIP_W, CLIP_H = 980, 551; CLIP_X, CLIP_Y = 50, 262; SPLIT_SHIFT = 290; CAP_SPLIT = TOP - 22
_mk = Image.new("L", (CLIP_W, CLIP_H), 0); ImageDraw.Draw(_mk).rounded_rectangle((0, 0, CLIP_W - 1, CLIP_H - 1), 26, fill=255)
CLIP_MASK = (np.asarray(_mk, np.float32) / 255.0)[..., None]
F_INTRO = sum(NFR[:next(i for i, k in enumerate(KEEP) if k[0] == 'gpt')])   # whole intro (all its pieces) until the cut to ChatGPT
def topclip_cmd():
    # stretched a touch so the clip ends exactly on the cut (knockout pose on the last frame), muted
    k = F_INTRO / FPS / 6.0
    return ["ffmpeg", "-v", "error", "-i", TOPCLIP, "-vf", f"setpts=PTS*{k:.5f},fps={FPS},scale={CLIP_W}:{CLIP_H}:flags=lanczos,format=rgb24",
            "-frames:v", str(F_INTRO), "-f", "rawvideo", "-"]
def split_frame(guy, clip):
    fr_ = np.empty((H, W, 3), np.uint8); fr_[TOP:] = guy[TOP - SPLIT_SHIFT:H - SPLIT_SHIFT]
    sm = Image.fromarray(clip).resize((185, 104), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4))
    bgc = np.asarray(sm.resize((1476, 830), Image.BILINEAR), np.float32)[:, 198:198 + W]
    panel = (bgc * 0.28 + 6).astype(np.uint8)
    reg = panel[CLIP_Y:CLIP_Y + CLIP_H, CLIP_X:CLIP_X + CLIP_W].astype(np.float32)
    panel[CLIP_Y:CLIP_Y + CLIP_H, CLIP_X:CLIP_X + CLIP_W] = (clip * CLIP_MASK + reg * (1 - CLIP_MASK)).astype(np.uint8)
    fr_[:TOP] = panel
    return fr_
SRC_AT = []
for (s_, a, b, _), n in zip(KEEP, NFR): SRC_AT += [s_] * n

def main():
    gp = subprocess.Popen(video_cmd("guy", GUY), stdout=subprocess.PIPE, bufsize=10 ** 8)
    rp = subprocess.Popen(video_cmd("gpt", REC), stdout=subprocess.PIPE, bufsize=10 ** 8)
    tp = subprocess.Popen(topclip_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8); clip = None
    if not PREVIEW:
        audio(events())
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for f in range(NF):
        src = SRC_AT[f]
        pipe = gp if src == "guy" else rp
        fr_ = np.frombuffer(pipe.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if f < F_INTRO:
            raw = tp.stdout.read(CLIP_W * CLIP_H * 3)
            if len(raw) == CLIP_W * CLIP_H * 3: clip = np.frombuffer(raw, np.uint8).reshape(CLIP_H, CLIP_W, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        t = f / FPS
        if f < F_INTRO and clip is not None:
            canvas = Image.fromarray(split_frame(fr_, clip)).convert("RGBA"); cap_y = CAP_SPLIT
        elif src == "guy":
            canvas = Image.fromarray(shifted(fr_)).convert("RGBA")
            cd = card_at(f)
            if cd: paste(canvas, cd[0], CARD_X, CARD_Y + cd[3], cd[1], cd[2])
            e = 1.0 if t >= KEY["t0"] - 1.5 else vis(t)
            cap_y = CAP_IDLE * (1 - e) + CAP_MID * e
        else:
            canvas = Image.fromarray(fr_).convert("RGBA")
            paste(canvas, GPT_CHIP, 540, 340, 1.35)
            cap_y = CAP_GPT
        if f >= KEY["f0"]:
            k = f - KEY["f0"]
            sc = (0.55 + 0.45 * ease_out_back(k / 7, 2.6)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            paste(canvas, KEY["im"], 540, KEY_Y, sc, min(1, 0.35 + k / 3))
        tag_on = any(c["txt"] == "AllPass" and c["hl"] and c["f0"] <= f < c["f1"] for c in chunks)
        for ch in chunks:
            if ch["key"] or not (ch["f0"] <= f < ch["f1"]) or KEY["f0"] <= f < KEY["f0"] + FPS: continue
            if tag_on and not (ch["txt"] == "AllPass" and ch["hl"]): continue
            k = f - ch["f0"]
            if ch["txt"] == "AllPass" and ch["hl"]:
                sc = (0.5 + 0.5 * ease_out_back(k / 9, 2.2)) * (0.78 - (0.08 if src == 'guy' and cap_y > CAP_IDLE + 100 else 0)) * (1 + 0.02 * math.sin(k / FPS * 2 * math.pi * 1.2))
                al = min(1, 0.3 + k / 3) * (1 - max(0, (f - (ch["f1"] - 6)) / 6))
                paste(canvas, ch["im"], 540, cap_y, sc, al)
            else:
                paste(canvas, ch["im"], 540, cap_y + (1 - ease_out_cubic(k / 5)) * 8, 0.86 + 0.14 * ease_out_back(k / 5), min(1, 0.35 + k / 3))
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill(); rp.kill(); tp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "key", round(KEY["f0"] / FPS, 2), "scenes", [(round(a, 2), round(b, 2)) for a, b, _, _ in SCENES], file=sys.stderr)
    main()
