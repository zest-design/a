import json, subprocess, sys, re, difflib, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
P = f"{S}/p7"
U = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6"
GUY = f"{U}/1319557e-2BCCD577-1D23-4F85-8635-5F35C51BCE9C_1_1_1.mp4"
REC = f"{U}/7f095f1f-ssstwitter.com_1792429007976.mp4"
OUT = sys.argv[1]
PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
RED = (229, 22, 34); WHITE = (255, 255, 255)

# ---------------- cuts: silences + the false start at ~41 s -----------------------
SIL = [(0.00, 1.10), (2.72, 3.13), (4.45, 4.60), (12.90, 13.28), (13.77, 14.15), (22.03, 22.26), (23.01, 23.17),
       (23.49, 23.81), (24.43, 24.67), (29.17, 29.40), (30.72, 31.00), (35.20, 35.37), (37.95, 38.18), (39.61, 39.75),
       (40.41, 45.20),                                   # "Y generar esto es muy simple…" first attempt
       (51.53, 51.73), (54.29, 54.51), (55.47, 55.59), (57.28, 57.47), (59.60, 60.16), (62.64, 62.86),
       (64.81, 64.95), (65.59, 65.89), (66.89, 67.12), (69.35, 69.60), (70.08, 70.22), (72.47, 72.70), (72.80, 72.99),
       (77.81, 78.03), (81.42, 81.67), (82.95, 83.15), (86.16, 86.37), (87.14, 87.33)]
END = 90.0; PAD = 0.04
KEEP = []; cur = SIL[0][1] - PAD
for a, b in SIL[1:]:
    KEEP.append((cur, a + PAD)); cur = b - PAD
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

# ---------------- words / captions --------------------------------------------------
PK = json.load(open(f"{P}/words.json"))
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
SEGS = [
    (1.20, 2.53, "Mira esto."),
    (2.88, 12.83, "Ahora puedes transformar un PDF de instrucciones de montaje de muebles en un sitio web totalmente interactuable, donde la persona, el cliente final,"),
    (13.28, 23.45, "puede ver cómo montar ese mueble paso a paso, ir hacia atrás y hacia adelante, verlo en 3D, y todo esto se crea de manera muy, muy fácil, y te voy a explicar cómo."),
    (23.78, 30.69, "¿Para qué? Para que tú puedas vender este servicio a empresas, o si tú eres dueño de alguna empresa de muebles, poder dar"),
    (30.97, 40.45, "esa entrega junto con tus muebles a los clientes, porque así los vas a enamorar. Y si tú das este servicio, las empresas se enamorarán de ti por saber hacerlo. Así que vamos a ello."),
    (45.24, 54.30, "Y generar esto es muy simple, lo único que tienes que hacer es ir a Claude y pasarle el PDF y decirle: transforma este paso a paso de montaje en una página"),
    (54.46, 59.65, "con un 3D totalmente interactuable, listo para entregar a un cliente final."),
    (59.98, 65.61, "Claude aquí se pondrá a trabajar y creará todo esto para ti en minutos, listo"),
    (65.82, 72.58, "para que tú lo uses, para que se lo pases a algún cliente o para que tú vendas y entregues el servicio a cualquier empresa."),
    (72.73, 81.53, "Si tú quieres aprender el paso a paso completo de esto, mucho más detallado, he preparado un PDF para ti. Así que si tú quieres aprenderlo, comenta aquí abajo MUEBLE,"),
    (81.69, 89.88, "que te lo haré llegar directamente, y está paso a paso para que tú domines esta habilidad y puedas generar ingresos con inteligencia artificial."),
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

HL = ["sitio web", "3d", "muy muy fácil", "vender este servicio", "enamorar", "claude", "en minutos", "mueble",
      "inteligencia artificial"]
HL = [p.split() for p in HL]
PUNCT = re.compile(r"[.,?:!]$")
chunks = []; i = 0
while i < len(WORDS):
    hit = next((p for p in HL if [norm(w[0]) for w in WORDS[i:i + len(p)]] == p), None)
    if hit: g = WORDS[i:i + len(hit)]; i += len(hit); hl = True
    else:
        g = [WORDS[i]]; i += 1; hl = False
        while i < len(WORDS) and len(g) < 3 and not PUNCT.search(g[-1][0]) and not g[-1][2]:
            if WORDS[i][1] - g[0][1] > 0.8 or sum(len(w[0]) for w in g) + len(WORDS[i][0]) > 16: break
            if any([norm(w[0]) for w in WORDS[i:i + len(p)]] == p for p in HL): break
            g.append(WORDS[i]); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(w[0] for w in g))
    if txt != "MUEBLE":
        txt = txt.lower().replace("claude", "Claude").replace("pdf", "PDF").replace("3d", "3D")
    end = g[-1][3] + 0.25 if g[-1][2] else None
    chunks.append(dict(txt=txt, hl=hl, t0=g[0][1], end=end))
merged = []
for c in chunks:   # avoid a lone short word right before a highlight
    if merged and c["hl"] and not merged[-1]["hl"] and " " not in merged[-1]["txt"] and len(merged[-1]["txt"]) <= 3:
        p = merged.pop(); c = dict(c, txt=p["txt"] + " " + c["txt"], t0=p["t0"])
    merged.append(c)
chunks = merged
for k, c in enumerate(chunks):
    if k and chunks[k - 1]["txt"] == "MUEBLE": c["t0"] = max(c["t0"], chunks[k - 1]["t0"] + 1.1)
    nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else 99
    if c["txt"] == "MUEBLE": nxt = max(nxt, c["t0"] + 1.1)
    c["t1"] = min(nxt, c["end"] or nxt, c["t0"] + 1.6)
    c["f0"], c["f1"] = fo(c["t0"]), fo(c["t1"])

FC = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 62)
FH = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", 74)
def make_caption(txt, hl):
    f = FH if txt == "MUEBLE" else FC
    tw = f.getlength(txt); bb = f.getbbox(txt); padx, pady = 22, 12
    w, h = int(tw + 2 * padx + 40), int(bb[3] - bb[1] + 2 * pady + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if hl:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 24, w - 20, h - 16), 16, fill=(0, 0, 0, 100))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle((20, 20, w - 20, h - 20), 16, fill=RED)
    else:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=f, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=f, fill=WHITE, anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"], c["hl"])

# ---------------- layout -----------------------------------------------------------
TOP = 800                    # ~40 % : app recording
SHIFT = 352                  # talking head rows shown in the bottom panel (face centred)
CW, CH, CX, CY, CR = 1000, 562, 40, 150, 30
CAP_SPLIT, CAP_FULL = 758, 560
T_FULL = 72.73               # CTA: talking head full screen
F_FULL = fo(T_FULL); TRANS = 10
mask = Image.new("L", (CW, CH), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, CW - 1, CH - 1), CR, fill=255)
sh_ = Image.new("RGBA", (W, TOP), (0, 0, 0, 0))
ImageDraw.Draw(sh_).rounded_rectangle((CX, CY + 14, CX + CW, CY + CH + 14), CR, fill=(0, 0, 0, 120))
CARD_SHADOW = sh_.filter(ImageFilter.GaussianBlur(22))

# recording segments: (src start, src end, start inside the recording)
RSEG = [(0.0, 22.00, 0.0), (22.00, 31.00, 23.0), (31.00, 45.20, 4.0), (45.20, 48.90, 13.3), (48.90, 52.00, 20.8),
        (52.00, 60.00, 24.0), (60.00, 99, 0.0)]
seg_starts = []
def rec_cmd():
    ins, parts = [], []
    for i, (a, b, ss) in enumerate(RSEG):
        n = min(fo(b), NF) - fo(a)
        if n <= 0: continue
        seg_starts.append(fo(a)); ins += ["-ss", str(ss), "-i", REC]
        k = len(parts)
        parts.append(f"[{k}:v]fps=30,scale=1280:720,setsar=1,tpad=stop_mode=clone:stop_duration=20,trim=end_frame={n},setpts=PTS-STARTPTS[s{k}]")
    fc = ";".join(parts) + ";" + "".join(f"[s{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0,format=rgb24[o]"
    return ["ffmpeg", "-v", "error"] + ins + ["-filter_complex", fc, "-map", "[o]", "-f", "rawvideo", "-"]
def guy_cmd():
    v = [f"[0:v]trim=start_frame={round(s * 30)}:end_frame={round(e * 30)},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP)]
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=1:a=0,fps=30,scale={W}:{H},format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF), "-f", "rawvideo", "-"]
def audio():
    parts = [f"[0:a]atrim=start={s:.5f}:end={e:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.008:.4f}:d=0.008[a{i}]"
             for i, (s, e) in enumerate(KEEP)]
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", f"{P}/voice.wav"], check=True)

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def paste(canvas, im, x, y, scale, alpha):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, alpha))))
    canvas.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

def top_panel(rec):
    src = Image.frombuffer("RGB", (1280, 720), rec)
    # blurred, slightly darkened copy of the recording behind the card
    small = src.resize((160, 90), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    bg = small.resize((int(TOP * 16 / 9), TOP), Image.BILINEAR)
    x0 = (bg.width - W) // 2; bg = bg.crop((x0, 0, x0 + W, TOP))
    bg = Image.eval(bg, lambda v: int(v * 0.82)).convert("RGBA")
    bg.alpha_composite(CARD_SHADOW)
    card = src.resize((CW, CH), Image.BILINEAR)
    bg.paste(card, (CX, CY), mask)
    return bg

def main():
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    rp = subprocess.Popen(rec_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        audio()
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{P}/voice.wav", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        rec = rp.stdout.read(1280 * 720 * 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        e = ease_out_cubic((f - F_FULL) / TRANS) if f >= F_FULL else 0.0     # 0 = split, 1 = full screen
        if e >= 1:
            canvas = Image.fromarray(guy).convert("RGBA")
        else:
            edge = int(round(TOP * (1 - e))); shift = int(round(SHIFT * (1 - e)))
            fr = np.empty((H, W, 3), np.uint8); fr[edge:] = guy[edge - shift:H - shift]
            canvas = Image.fromarray(fr).convert("RGBA")
            tp = top_panel(rec)
            if e > 0: tp = tp.crop((0, int(TOP * e), W, TOP))
            canvas.alpha_composite(tp, (0, 0))
            if f < 8:   # card settles in at the very start
                pass
        cap_y = CAP_SPLIT + (CAP_FULL - CAP_SPLIT) * e
        for c in chunks:
            if not (c["f0"] <= f < c["f1"]): continue
            k = f - c["f0"]
            if c["txt"] == "MUEBLE":
                sc = (0.6 + 0.4 * ease_out_back(k / 7, 2.4)) * (1 + 0.03 * math.sin(k / FPS * 2 * math.pi * 1.5))
            else: sc = 0.86 + 0.14 * ease_out_back(k / 5)
            paste(canvas, c["im"], 540, cap_y + (1 - ease_out_cubic(k / 5)) * 8, sc, min(1, 0.35 + k / 3))
        out = canvas.convert("RGB")
        if PREVIEW: out.save(f"{P}/pv_{f / FPS:06.2f}.png")
        else: enc.stdin.write(out.tobytes())
    gp.kill(); rp.kill()
    if not PREVIEW: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    print("total", round(TOTAL, 2), "full at", round(F_FULL / FPS, 2), file=sys.stderr)
    main()
