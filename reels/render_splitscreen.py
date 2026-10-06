import json, subprocess, sys, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"
U = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6"
GUY = f"{U}/62adc1d3-1006_23.mp4"
SCR = f"{U}/3aeb6081-screen.mp4"
CLO = f"{U}/635fdc7a-ssstwitter.com_1790759069152_1.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{S}/reel.mp4"
PREVIEW = len(sys.argv) > 2  # render only listed seconds as stills
W, H, FPS = 1080, 1920, 30

RED = (230, 25, 35)
DARK = (20, 20, 22)
WHITE = (255, 255, 255)
FD = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FD + name, size)
FA = f"{S}/fa/fa-solid.ttf"

# ---------------- timeline (source seconds of the talking-head video) -------------
KEEP = [(0.62, 8.80), (9.05, 14.00), (14.85, 26.58), (27.12, 74.80)]
def m(t):
    o = 0.0
    for a, b in KEEP:
        if t <= a: return o
        if t < b: return o + t - a
        o += b - a
    return o
TOTAL = m(99)
NF = int(round(TOTAL * FPS))
def fo(t): return int(round(m(t) * FPS))

SPLIT = 7.52          # starts talking about the sites
CARD = (3.52, 6.08)   # $5.000 hook card
F_SPLIT = fo(SPLIT)
TRANS = 10            # frames of full->split transition

# ---------------- words (parakeet timings, corrected) -----------------------------
raw = json.load(open(f"{S}/words.json"))
words = []
for w, a, b in raw:
    words.append([w, a])
def fix(ws):
    out = []
    skip_con = False
    for i, (w, a) in enumerate(ws):
        if w == "inteligência": w = "inteligencia"
        if w == "Cloud.": w = "Claude."
        if w == "essa": w = "esa"
        if w == "Essas": w = "Estas"
        if w == "aqui": w = "aquí"
        if w == "de" and abs(a - 36.01) < 0.05: w = "del"
        if w == "con" and abs(a - 25.53) < 0.05: continue
        if w == "o" and a > 74: continue
        if w == "tu" and abs(a - 25.85) < 0.05: w = "contigo"
        if w == "web." and a > 74: w = "“WEB”"
        if 66.0 < a < 69.8:  # badly recognised stretch, rebuilt from whisper text
            continue
        out.append([w, a])
        if w == "aquí" and abs(a - 65.85) < 0.05:
            seq = [("todas", 66.25), ("han", 66.57), ("sido", 66.73), ("usando", 67.05), ("este", 67.61),
                   ("método", 67.77), ("y", 68.25), ("estoy", 68.40), ("seguro", 68.62), ("que", 68.95),
                   ("tú", 69.10), ("también", 69.30), ("lo", 69.70)]
            out += [[x, y] for x, y in seq]
    return out
words = fix(words)

CHUNKS = """¿Sabías que ahora|puedes crear webs
en|minutos
#que tienen un valor de más de 5 mil dólares?
Sí, eso que|acabas de escuchar.
Estas webs que|estás viendo aquí
fueron creadas|totalmente
usando|inteligencia artificial
y te voy a enseñar|el paso a paso
aquí|ahora mismo.
Lo primero|que tienes que hacer
es ir a|esta web
que está|aquí.
Y ahí eliges|el tipo de web
que quieres|replicar.
Elige el diseño|que más te guste
y que más|encaje
con el cliente|o contigo mismo.
Una vez que tú|tengas el diseño,
vas a|descargar este vídeo
y lo vas a|mandar a Claude.
Le vas a pedir:|quiero que hagas
la web|de este negocio
y le puedes|pasar
el nombre|del negocio,
describe|el negocio
o directamente|la web antigua
que tengan.|¿Ok?
Y una vez que tú|le pases eso,
le pasas el vídeo|como ejemplo.
Es muy|importante
que le pases|el vídeo
porque la|inteligencia artificial
no sabe|lo que es mejor,
más bonito,|más moderno.
Ella entiende|con comparación.
Entonces, cuando tú|le pasas el vídeo,
ella|compara
con lo que tú|esperas de ella
y va a|replicar
esa web|completa
con un nivel|de profesionalidad
que te vas a|quedar alucinando.
Estas webs|que he hecho aquí
todas han sido|usando este método
y estoy seguro que|tú también
lo vas a|conseguir.
Si tú quieres|el tutorial completo,
paso|a paso,
comenta aquí abajo|“WEB”""".split("\n")

chunks = []
wi = 0
for line in CHUNKS:
    hidden = line.startswith("#")
    txt = line.lstrip("#")
    parts = txt.split("|") if "|" in txt else ["", txt]
    n = len(txt.replace("|", " ").split())
    seg = words[wi:wi + n]
    exp = txt.replace("|", " ").split()
    got = [w for w, _ in seg]
    def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
    if [norm(x) for x in exp] != [norm(x) for x in got]:
        print("MISMATCH", exp, got, file=sys.stderr)
    chunks.append(dict(small=parts[0], big=parts[1], t0=seg[0][1], hidden=hidden))
    wi += n
assert wi == len(words), (wi, len(words))
for i, c in enumerate(chunks):
    c["t1"] = chunks[i + 1]["t0"] if i + 1 < len(chunks) else 74.80
    c["f0"] = fo(c["t0"]); c["f1"] = fo(c["t1"])

# ---------------- step / info pills ------------------------------------------------
SLOTS = [
    (7.52, 14.0, "HECHO CON IA", "Webs creadas en minutos", ""),
    (14.85, 18.17, "PASO 1", "Entra en motionsites.ai", ""),
    (18.17, 28.6, "PASO 2", "Elige tu diseño favorito", ""),
    (28.6, 30.45, "PASO 3", "Descarga el vídeo", ""),
    (30.45, 35.4, "PASO 4", "Envíalo a Claude", ""),
    (35.4, 40.7, "PASO 5", "Describe tu negocio", ""),
    (40.7, 47.4, "PASO 6 · CLAVE", "Pásale el vídeo de ejemplo", ""),
    (47.4, 55.55, "POR QUÉ FUNCIONA", "La IA aprende comparando", ""),
    (55.55, 64.7, "RESULTADO", "Nivel profesional", ""),
    (64.7, 70.4, "MÉTODO PROBADO", "Todas hechas así", ""),
    (70.4, 99, "TUTORIAL COMPLETO", "Comenta “WEB”", ""),
]

def shadow_layer(size, box, radius, blur, alpha, offset=(0, 10)):
    sh = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]), radius, fill=(0, 0, 0, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur))

def make_pill(label, text, icon, big=False):
    k = 1.25 if big else 1.0
    fl = font("Inter-Bold.otf", int(24 * k)); ft = font("InterDisplay-ExtraBold.otf", int(40 * k))
    fi = ImageFont.truetype(FA, int(40 * k))
    pad = 40
    ib = int(86 * k)
    tw = max(ft.getlength(text), fl.getlength(label) * 1.12)
    w = int(14 * k + ib + 24 * k + tw + 34 * k); h = int(116 * k)
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    im.alpha_composite(shadow_layer(im.size, (pad, pad, pad + w, pad + h), int(30 * k), 14, 70))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), int(30 * k), fill=WHITE)
    ix, iy = pad + int(15 * k), pad + (h - ib) // 2
    d.rounded_rectangle((ix, iy, ix + ib, iy + ib), int(22 * k), fill=RED)
    d.text((ix + ib / 2, iy + ib / 2), icon, font=fi, fill=WHITE, anchor="mm")
    tx = ix + ib + int(24 * k)
    # letter-spaced label
    x = tx
    for ch in label:
        d.text((x, pad + int(22 * k)), ch, font=fl, fill=RED)
        x += fl.getlength(ch) + 2.2 * k
    d.text((tx, pad + int(52 * k)), text, font=ft, fill=DARK)
    return im, pad

pills = []
for a, b, lab, txt, ic in SLOTS:
    im, pad = make_pill(lab, txt, ic, big=(lab == "TUTORIAL COMPLETO"))
    pills.append(dict(f0=fo(a), f1=min(fo(b), NF), im=im, pad=pad, cta=(lab == "TUTORIAL COMPLETO")))

# ---------------- captions ---------------------------------------------------------
CAP_X = 520           # keeps clear of the right-hand IG buttons
CAP_MAXW = 700
def make_caption(small, big):
    big = big.upper()
    fs = font("InterDisplay-Bold.otf", 46)
    size = 92
    while True:
        fb = font("InterDisplay-Black.otf", size)
        if fb.getlength(big) <= CAP_MAXW or size <= 52: break
        size -= 4
    sw = fs.getlength(small) if small else 0
    bw = fb.getlength(big)
    w = int(max(sw, bw)) + 80; h = 60 + size + 70
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(im)
    y_small = 30; y_big = y_small + (52 if small else 0)
    if small:
        g.text((w / 2, y_small), small, font=fs, fill=(0, 0, 0, 200), anchor="ma", stroke_width=6, stroke_fill=(0, 0, 0, 200))
    g.text((w / 2, y_big), big, font=fb, fill=(0, 0, 0, 170), anchor="ma", stroke_width=8, stroke_fill=(0, 0, 0, 170))
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    im.alpha_composite(glow)
    if small:
        d.text((w / 2, y_small), small, font=fs, fill=WHITE, anchor="ma", stroke_width=2, stroke_fill=DARK)
    d.text((w / 2, y_big), big, font=fb, fill=RED, anchor="ma", stroke_width=3, stroke_fill=WHITE)
    bbox = im.getbbox()
    return im.crop(bbox)

for c in chunks:
    if not c["hidden"]:
        c["im"] = make_caption(c["small"], c["big"])

# ---------------- static backgrounds -----------------------------------------------
def vgrad(w, h, c0, c1):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(c0, float)[None, None]; b = np.array(c1, float)[None, None]
    return np.repeat((a * (1 - t) + b * t), w, axis=1).astype(np.uint8)

TOP_H = 880
top_bg = vgrad(W, TOP_H, (255, 255, 255), (244, 240, 240)).astype(float)
yy, xx = np.mgrid[0:TOP_H, 0:W]
glow = np.exp(-(((xx - 980) / 420.0) ** 2 + ((yy - 820) / 260.0) ** 2))[..., None]
top_bg = (top_bg * (1 - 0.18 * glow) + np.array(RED, float) * 0.18 * glow).astype(np.uint8)

card_bg = vgrad(W, H, (255, 255, 255), (255, 226, 226)).astype(float)
yy, xx = np.mgrid[0:H, 0:W]
g2 = np.exp(-(((xx - 900) / 500.0) ** 2 + ((yy - 1800) / 500.0) ** 2))[..., None]
card_bg = (card_bg * (1 - 0.35 * g2) + np.array(RED, float) * 0.35 * g2).astype(np.uint8)

# content card (sites)
CW, CH, CX, CY, CR = 1020, 730, 30, 120, 34
cmask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(cmask).rounded_rectangle((0, 0, CW - 1, CH - 1), CR, fill=255)
cmask_np = np.array(cmask, float)[..., None] / 255
card_shadow = shadow_layer((W, TOP_H), (CX, CY, CX + CW, CY + CH), CR, 18, 80, (0, 12))
top_base = Image.fromarray(top_bg).convert("RGBA")
top_base.alpha_composite(card_shadow)
top_base = np.array(top_base.convert("RGB"))

# ---------------- source pipes -----------------------------------------------------
def guy_cmd():
    v = []; a = []
    for i, (s, e) in enumerate(KEEP):
        v.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}]")
    vf = ";".join(v) + ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=1:a=0,fps=30,scale={W}:{H}:flags=lanczos,format=rgb24[o]"
    return ["ffmpeg", "-v", "error", "-i", GUY, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(NF),
            "-f", "rawvideo", "-"]

# top segments: (src_start, src_end, file, start_in_file, cropY or None for clothes)
TOPSEG = [
    (7.52, 14.85, CLO, 12.6, None),
    (14.85, 18.17, SCR, 0.3, 150),
    (18.17, 21.61, SCR, 5.5, 250),
    (21.61, 27.12, SCR, 10.0, 260),
    (27.12, 35.53, SCR, 25.9, 260),
    (35.53, 40.60, SCR, 18.9, 260),
    (40.60, 47.45, SCR, 34.0, 260),
    (47.45, 50.45, SCR, 14.9, 260),
    (50.45, 53.05, SCR, 2.0, 150),
    (53.05, 55.60, SCR, 30.0, 260),
    (55.60, 64.73, CLO, 0.0, None),
    (64.73, 99, CLO, 9.13, None),
]
seg_frames = []
def top_cmd():
    ins = []; parts = []
    for i, (a, b, f, ss, cy) in enumerate(TOPSEG):
        n = min(fo(b), NF) - fo(a)
        seg_frames.append((fo(a), n))
        ins += ["-ss", str(ss), "-i", f]
        if cy is None:
            geo = f"crop=1440:758:143:143,scale=-2:{CH}:flags=lanczos,crop={CW}:{CH}"
        else:
            ch = int(round(1080 * CH / CW))
            geo = f"crop=1080:{ch}:0:{cy},scale={CW}:{CH}:flags=lanczos"
        parts.append(f"[{i}:v]fps=30,{geo},setsar=1,tpad=stop_mode=clone:stop_duration=3,trim=end_frame={n},setpts=PTS-STARTPTS[s{i}]")
    fc = ";".join(parts) + ";" + "".join(f"[s{i}]" for i in range(len(TOPSEG))) + \
        f"concat=n={len(TOPSEG)}:v=1:a=0,format=rgb24[o]"
    return ["ffmpeg", "-v", "error"] + ins + ["-filter_complex", fc, "-map", "[o]", "-f", "rawvideo", "-"]

def audio():
    parts = []
    for i, (s, e) in enumerate(KEEP):
        parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={e-s-0.012}:d=0.012[a{i}]")
    fc = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + \
        f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", GUY, "-filter_complex", fc, "-map", "[o]", "-ar", "48000",
                    f"{S}/voice.wav"], check=True)

# ---------------- helpers ----------------------------------------------------------
def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_in_out(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

def paste_rgba(canvas, im, cx, cy, scale=1.0, alpha=1.0, anchor="center"):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    if anchor == "center":
        x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    else:
        x, y = int(cx), int(cy)
    canvas.alpha_composite(im, (x, y)) if (x >= 0 and y >= 0 and x + im.width <= canvas.width and y + im.height <= canvas.height) \
        else canvas.alpha_composite(im, dest=(max(0, x), max(0, y)), source=(max(0, -x), max(0, -y)))

def circle_face(guy):
    # square crop around the face from the full-frame 1080x1920 guy image
    sq = Image.fromarray(guy[420:1440, 30:1050]).resize((470, 470), Image.LANCZOS)
    mask = Image.new("L", (470, 470), 0); ImageDraw.Draw(mask).ellipse((0, 0, 469, 469), fill=255)
    out = Image.new("RGBA", (510, 510), (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse((0, 0, 509, 509), fill=WHITE)
    out.paste(sq, (20, 20), mask)
    return out

F_CARD0, F_CARD1 = fo(CARD[0]), fo(CARD[1])
F_COUNT0, F_COUNT1 = fo(4.40), fo(5.20)
fs_card = font("InterDisplay-Bold.otf", 48)
fb_card = font("InterDisplay-Black.otf", 170)
fu_card = font("Inter-ExtraBold.otf", 40)
circ_shadow = shadow_layer((W, H), (540 - 255, 700 - 255, 540 + 255, 700 + 255), 255, 24, 90, (0, 16))

def hook_card(guy, f):
    k = f - F_CARD0
    canvas = Image.fromarray(card_bg).convert("RGBA")
    e = ease_out_back(k / 9)
    sh = circ_shadow if k > 4 else None
    if sh is not None: canvas.alpha_composite(sh)
    paste_rgba(canvas, circle_face(guy), 520, 700, scale=max(0.05, 0.55 + 0.45 * e))
    d = ImageDraw.Draw(canvas)
    if k >= 4:
        a = min(1, (k - 4) / 6)
        d.text((520, 1020), "webs con un valor de más de", font=fs_card, fill=DARK + (int(255 * a),), anchor="ma")
    if f >= F_COUNT0 - 3:
        p = ease_out_cubic((f - F_COUNT0) / max(1, F_COUNT1 - F_COUNT0))
        val = int(round(5000 * p / 50.0) * 50)
        txt = "$" + f"{val:,}".replace(",", ".")
        im = Image.new("RGBA", (900, 220), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((450, 10), txt, font=fb_card, fill=RED, anchor="ma")
        paste_rgba(canvas, im, 520, 1190, scale=0.9 + 0.1 * ease_out_back((f - F_COUNT0 + 3) / 8))
        if p > 0.95:
            lab = "DÓLARES"
            x = 520 - (sum(fu_card.getlength(c) + 8 for c in lab) - 8) / 2
            for ch in lab:
                d.text((x, 1310), ch, font=fu_card, fill=DARK); x += fu_card.getlength(ch) + 8
    return canvas

def zoom(img, z, cx=540, cy=900):
    if z == 1.0: return img
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return np.array(Image.fromarray(img).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)))

# ---------------- main loop --------------------------------------------------------
def render():
    gp = subprocess.Popen(guy_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    tp = subprocess.Popen(top_cmd(), stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        audio()
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{S}/voice.wav", "-c:v", "libx264", "-preset", "slow",
                                "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                                "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    want = set(int(float(x) * FPS) for x in sys.argv[2].split(",")) if PREVIEW else None
    seg_starts = [a for a, n in seg_frames]
    top = None
    for f in range(NF):
        guy = np.frombuffer(gp.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if f >= F_SPLIT:
            top = np.frombuffer(tp.stdout.read(CW * CH * 3), np.uint8).reshape(CH, CW, 3)
        if want is not None and f not in want:
            if f > max(want): break
            continue
        if f < F_SPLIT:
            if F_CARD0 <= f < F_CARD1:
                canvas = hook_card(guy, f)
            else:
                z = 1.0
                if f >= F_CARD1:  # punch-in after the card
                    z = 1.14
                canvas = Image.fromarray(zoom(guy, z)).convert("RGBA")
        else:
            e = ease_out_cubic((f - F_SPLIT) / TRANS)
            fr = np.empty((H, W, 3), np.uint8)
            edge = int(round(880 * e)); shift = int(round(415 * e))
            fr[:TOP_H] = top_base
            # content card with pop on cuts
            since = min((f - s for s in seg_starts if s <= f), default=99)
            pop = 1.0 if since >= 7 else 0.965 + 0.035 * ease_out_cubic(since / 7)
            card = top
            cm = cmask_np
            if pop != 1.0:
                pw, ph = int(CW * pop), int(CH * pop)
                card = np.array(Image.fromarray(top).resize((pw, ph), Image.BILINEAR))
                cm = np.array(cmask.resize((pw, ph), Image.BILINEAR), float)[..., None] / 255
            ph, pw = card.shape[:2]
            x0 = CX + (CW - pw) // 2; y0 = CY + (CH - ph) // 2 - int((1 - e) * 220)
            ys, ye = max(y0, 0), y0 + ph
            region = fr[ys:ye, x0:x0 + pw].astype(float)
            c = card[ys - y0:].astype(float); mm = cm[ys - y0:]
            fr[ys:ye, x0:x0 + pw] = (region * (1 - mm) + c * mm).astype(np.uint8)
            if since < 4:  # quick flash on cut
                fl = (1 - since / 4) * 0.35
                fr[ys:ye, x0:x0 + pw] = (fr[ys:ye, x0:x0 + pw] * (1 - fl * mm) + 255 * fl * mm).astype(np.uint8)
            fr[TOP_H:] = top_base[-1]
            fr[edge:] = guy[edge - shift:H - shift]
            canvas = Image.fromarray(fr).convert("RGBA")
            # pills
            for p in pills:
                if p["f0"] <= f < p["f1"]:
                    k = f - p["f0"]; left = p["f1"] - f
                    a = min(1, k / 5) * min(1, left / 5)
                    sx = 1 - ease_out_back(k / 10)
                    sc = 1.0
                    if p["cta"]:
                        sc = 1 + 0.035 * math.sin(k / FPS * 2 * math.pi * 1.4)
                        paste_rgba(canvas, p["im"], 520, 300, scale=sc * (0.6 + 0.4 * ease_out_back(k / 10)), alpha=a)
                    else:
                        paste_rgba(canvas, p["im"], 56 - p["pad"] - 120 * sx, 232 - p["pad"], alpha=a, anchor="tl")
        # captions
        for c in chunks:
            if c["hidden"] or not (c["f0"] <= f < c["f1"]): continue
            k = f - c["f0"]
            sc = 0.82 + 0.18 * ease_out_back(k / 6)
            cy = 1250 if f < F_SPLIT else 880
            paste_rgba(canvas, c["im"], CAP_X, cy, scale=sc, alpha=min(1, k / 2 + 0.3))
        out = np.array(canvas.convert("RGB"))
        if PREVIEW:
            Image.fromarray(out).save(f"{S}/pv_{f / FPS:06.2f}.png")
        else:
            enc.stdin.write(out.tobytes())
        if f % 150 == 0: print(f"{f}/{NF}", file=sys.stderr, flush=True)
    gp.kill(); tp.kill()
    if not PREVIEW:
        enc.stdin.close(); enc.wait()

render()
