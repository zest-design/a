import json, subprocess, sys, re, difflib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p5"
SRC = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/b047ea9c-1009_4.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)
CAP_X, CAP_Y = 540, 672          # on the seam between the dashboard and the talking head

PK = json.load(open(f"{P}/words.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (0.98, 5.06, "Ahora es totalmente posible crear dashboards como este que estás viendo aquí. ¿Por qué?"),
    (5.30, 13.92, "Porque ahora con Claude Code podemos crear dashboards muy avanzados, páginas webs, toda la parte tecnológica de una empresa en minutos."),
    (14.04, 23.13, "Si tú quieres aprender a hacer dashboards como estos, páginas webs, dominar Claude Code de punta a punta, es decir, desde cero, sin saber nada, solo tienes que saber encender el ordenador,"),
    (23.58, 26.53, "hasta un nivel avanzado de crear dashboards como este que estás viendo aquí,"),
    (26.78, 28.04, "comenta aquí abajo"),
    (28.30, 33.57, "CODE, que te voy a enviar un vídeo donde te explico paso a paso cómo consigues crear"),
    (33.94, 39.55, "cualquier solución tecnológica para empresas, incluyendo esta, en minutos, usando Claude."),
]
def align(s0, s1, text):
    ws = text.split()
    pk = [(w, t) for w, t, _ in PK if s0 - 0.35 <= t <= s1 + 0.1]
    a = [norm(w) for w in ws]; b = [norm(w) for w, _ in pk]
    times = [None] * len(ws)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1): times[i1 + k] = pk[j1 + k][1]
    anchors = [(-1, s0)] + [(i, t) for i, t in enumerate(times) if t is not None] + [(len(ws), s1)]
    for i in range(len(ws)):
        if times[i] is None:
            lo = max(x for x in anchors if x[0] < i); hi = min(x for x in anchors if x[0] > i)
            # spread by character length between anchors
            span = ws[lo[0] + 1:hi[0]]; tot = sum(len(w) + 2 for w in span) or 1
            pre = sum(len(w) + 2 for w in ws[lo[0] + 1:i])
            t0 = lo[1] + (0.3 if lo[0] >= 0 else 0)
            times[i] = t0 + (hi[1] - t0) * pre / tot
    for i in range(1, len(times)): times[i] = max(times[i], times[i - 1] + 0.06)
    return [(w, t, k == len(ws) - 1, s1) for k, (w, t) in enumerate(zip(ws, times))]
WORDS = []
for sg in SEGS: WORDS += align(*sg)
# keep the product name together as a single token
_m = []
for w in WORDS:
    if _m and _m[-1][0] == "Claude" and norm(w[0]) == "code" and not w[0].startswith("CODE"):
        _m[-1] = ("Claude " + w[0], _m[-1][1], w[2], w[3])
    else: _m.append(w)
WORDS = _m

PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(WORDS):
    if WORDS[i][0].startswith("CODE"):
        g = [WORDS[i]]; i += 1; hl = True
    else:
        g = [WORDS[i]]; i += 1; hl = False
        while i < len(WORDS) and len(g) < 3 and not PUNCT.search(g[-1][0]) and not g[-1][2]:
            if WORDS[i][0].startswith("CODE"): break
            if WORDS[i][1] - g[0][1] > 0.8 or sum(len(w[0]) for w in g) + len(WORDS[i][0]) > 16: break
            g.append(WORDS[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w[0] for w in g))
    if not hl:
        txt = txt.lower().replace("claude code", "Claude Code").replace("claude", "Claude")
    end = g[-1][3] + 0.25 if g[-1][2] else None   # hold until the end of the sentence, then clear
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1], end=end))
for k, c in enumerate(chunks):   # the comment keyword stays on screen a bit longer
    if k and chunks[k - 1]["hl"]: c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.1)
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else 99
    if c["hl"]: nxt = max(nxt, c["t0"] + 1.1)
    c["t1"] = min(nxt, c["end"] or nxt, c["t0"] + 1.6)

FC = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 62)
FH = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", 74)
def make_caption(txt, hl):
    f = FH if hl else FC
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 26, 12
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 24, w - 20, h - 16), 18, fill=(0, 0, 0, 110))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, w - 20, h - 20), 18, fill=RED)
    else:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=f, fill=(0, 0, 0, 200), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, 200))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=f, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"])

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def paste(canvas, im, x, y, scale, alpha):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

def overlay(canvas, t):
    for c in chunks:
        if not (c["t0"] <= t < c["t1"]): continue
        k = (t - c["t0"]) * FPS
        if c["hl"]:   # the comment keyword gets a bigger, bouncier entrance and a light pulse
            sc = (0.6 + 0.4 * ease_out_back(k / 7, 2.4)) * (1 + 0.03 * np.sin(k / FPS * 2 * np.pi * 1.5))
        else:
            sc = 0.86 + 0.14 * ease_out_back(k / 5)
        paste(canvas, c["im"], CAP_X, CAP_Y + (1 - ease_out_cubic(k / 5)) * 8, sc, min(1, 0.35 + k / 3))

def main():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=lanczos,format=rgb24",
                            "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                                "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    f = 0
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        t = f / FPS
        if PREVIEW and not any(abs(t - p) < 0.5 / FPS for p in PREVIEW): f += 1; continue
        canvas = Image.frombuffer("RGB", (W, H), b).convert("RGBA")
        overlay(canvas, t)
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{t:05.2f}.png")
        else: enc.stdin.write(out.tobytes())
        f += 1
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    for c in chunks: print(f'{c["t0"]:6.2f}-{c["t1"]:6.2f} {"*" if c["hl"] else " "} {c["txt"]}', file=sys.stderr)
    main()
