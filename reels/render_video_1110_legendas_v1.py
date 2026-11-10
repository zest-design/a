# Captions only, on the original video (no cuts, no colour changes).
import json, re, sys, subprocess, difflib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"; P = f"{S}/p24"
SRC = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/ba8a2f32-1110_5.mp4"
OUT = sys.argv[1]; PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
TEXT = ("Y si quieres aprender a generar este tipo de contenido, comenta aquí abajo, que he preparado un material para ti "
        "con un paso a paso completo para poder hacerlo con inteligencia artificial, totalmente automático. Comenta aquí abajo y te lo haré llegar.")
PK = [(w, t) for w, t, _ in json.load(open(f"{P}/wordsA.json"))]
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
ws = TEXT.split(); a = [norm(w) for w in ws]; b = [norm(w) for w, _ in PK]; times = [None] * len(ws)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
        for k in range(i2 - i1): times[i1 + k] = PK[j1 + k][1]
if times[0] is None: times[0] = PK[0][1]
for i in range(len(ws)):
    if times[i] is None:
        lo = max(j for j in range(i) if times[j] is not None); hi = next((j for j in range(i + 1, len(ws)) if times[j] is not None), None)
        times[i] = times[lo] + 0.2 if hi is None else times[lo] + (times[hi] - times[lo]) * (i - lo) / (hi - lo)
for i in range(1, len(times)): times[i] = max(times[i], times[i - 1] + 0.08)
PUN = re.compile(r"[.,?:!]$"); chunks = []; i = 0
while i < len(ws):
    g = [i]; i += 1
    while i < len(ws) and len(g) < 3 and not PUN.search(ws[g[-1]]):
        if sum(len(ws[j]) for j in g) + len(ws[i]) > 16 or times[i] - times[g[0]] > 0.8: break
        g.append(i); i += 1
    chunks.append(dict(txt=re.sub(r"[¿?¡!.,:;]", "", " ".join(ws[j] for j in g)).lower(), t0=times[g[0]], last=ws[g[-1]]))
END = 33.0
for k, c in enumerate(chunks):
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else END
    c["t1"] = min(nxt, c["t0"] + (1.2 if PUN.search(c["last"]) else 1.6))
FC = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 62)
def make_caption(txt):
    tw = FC.getlength(txt); bb = FC.getbbox(txt); w, h = int(tw + 92), int(bb[3] - bb[1] + 68)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=FC, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=FC, fill=(255, 255, 255), anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"])
def ease_out_back(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
CAP_Y = 420                                  # top, above his head
def main():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"],
                           stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", SRC,
                                "-map", "0:v", "-map", "1:a", "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                                "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                                "-c:a", "copy", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    f = 0
    while True:
        fr = dec.stdout.read(W * H * 3)
        if len(fr) < W * H * 3: break
        t = f / FPS
        if PREVIEW and not any(abs(t - p) < 0.5 / FPS for p in PREVIEW): f += 1; continue
        im = Image.frombuffer("RGB", (W, H), fr).convert("RGBA")
        for c in chunks:
            if c["t0"] <= t < c["t1"]:
                k = (t - c["t0"]) * FPS; sc = 0.86 + 0.14 * ease_out_back(k / 5); cim = c["im"]
                cim = cim.resize((max(1, int(cim.width * sc)), max(1, int(cim.height * sc))), Image.BICUBIC)
                al = min(1, 0.35 + k / 3)
                if al < 1: cim = cim.copy(); cim.putalpha(cim.getchannel("A").point(lambda v: int(v * al)))
                im.alpha_composite(cim, (int(540 - cim.width / 2), int(CAP_Y + (1 - ease_out_cubic(k / 5)) * 8 - cim.height / 2)))
        if PREVIEW: im.convert("RGB").save(f"{P}/pv_{t:05.2f}.png")
        else: enc.stdin.write(im.convert("RGB").tobytes())
        f += 1
    if not PREVIEW: enc.stdin.close(); enc.wait()
if __name__ == "__main__":
    for c in chunks: print(f'{c["t0"]:5.2f}-{c["t1"]:5.2f} {c["txt"]}', file=sys.stderr)
    main()
