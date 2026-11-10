# Recipe-app screen recording (1.5 s -> 23 s) + presenter CTA (take 1 of CTA_2_1.mp4) with standard captions.
import json, re, sys, subprocess, difflib, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"; P = f"{S}/p23"
U = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6"
MAIN, CTA = f"{U}/d22eca67-IMG_1595.mp4", f"{U}/5e8dc587-CTA_2_1.mp4"
OUT = sys.argv[1]; PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 30
M0, M1 = 1.5, 23.0
KEEP = [(0.94, 6.02), (6.27, 7.98), (8.21, 12.80)]        # take 1, inner pauses tightened
CTA_DUR = sum(b - a for a, b in KEEP)
def m(t):
    o = 0.0
    for a, b in KEEP:
        if t <= a: return o
        if t < b: return o + t - a
        o += b - a
    return o
TEXT = "Y si quieres aprender a generar paso a paso contenidos de manera automática como esto usando inteligencia artificial, comenta aquí abajo, que te haré llegar un material completo con el paso a paso para que puedas empezar a generarlos hoy mismo."
PK = [(w, t) for w, t, _ in json.load(open(f"{P}/wordsC.json")) if t < 13.0]
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
ws = TEXT.split(); a = [norm(w) for w in ws]; b = [norm(w) for w, _ in PK]; times = [None] * len(ws)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
        for k in range(i2 - i1): times[i1 + k] = PK[j1 + k][1]
for i in range(len(ws)):
    if times[i] is None:
        lo = max([j for j in range(i) if times[j] is not None] or [None]) if i else None
        hi = next((j for j in range(i + 1, len(ws)) if times[j] is not None), None)
        t0 = times[lo] if lo is not None else 0.94
        times[i] = t0 + 0.2 if hi is None else t0 + (times[hi] - t0) * (i - (lo if lo is not None else -1)) / (hi - (lo if lo is not None else -1))
for i in range(1, len(times)): times[i] = max(times[i], times[i - 1] + 0.08)
WT = [(w, m(t)) for w, t in zip(ws, times)]
# chunks: 1-3 words, <=16 chars, break on punctuation
PUN = re.compile(r"[.,?:!]$"); chunks = []; i = 0
while i < len(WT):
    g = [i]; i += 1
    while i < len(WT) and len(g) < 3 and not PUN.search(WT[g[-1]][0]):
        if sum(len(WT[j][0]) for j in g) + len(WT[i][0]) > 16 or WT[i][1] - WT[g[0]][1] > 0.8: break
        g.append(i); i += 1
    txt = re.sub(r"[¿?¡!.,:;]", "", " ".join(WT[j][0] for j in g)).lower()
    chunks.append(dict(txt=txt, t0=WT[g[0]][1]))
for k, c in enumerate(chunks): c["t1"] = min(chunks[k + 1]["t0"] if k + 1 < len(chunks) else CTA_DUR, c["t0"] + 1.6)
FD = "/usr/share/fonts/opentype/inter/"; FC = ImageFont.truetype(FD + "InterDisplay-Bold.otf", 62)
def make_caption(txt):
    tw = FC.getlength(txt); bb = FC.getbbox(txt); w, h = int(tw + 92), int(bb[3] - bb[1] + 68)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((w / 2, h / 2 - 2), txt, font=FC, fill=(0, 0, 0, 210), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 210))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); ImageDraw.Draw(im).text((w / 2, h / 2 - 2), txt, font=FC, fill=(255, 255, 255), anchor="mm")
    return im
for c in chunks: c["im"] = make_caption(c["txt"])
def ease_out_back(x, s=1.7): x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
CAP_Y = 1490                                     # on his chest, never over the face

def main():
    vf = ";".join(f"[0:v]trim=start={s:.4f}:end={e:.4f},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP))
    vf += ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=1:a=0,fps={FPS},format=rgb24[o]"
    nf = int(round(CTA_DUR * FPS))
    gp = subprocess.Popen(["ffmpeg", "-v", "error", "-i", CTA, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(nf), "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
    if not PREVIEW:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", f"{P}/cta_v.mp4"], stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in PREVIEW) if PREVIEW else None
    for f in range(nf):
        fr = gp.stdout.read(W * H * 3)
        if len(fr) < W * H * 3: break
        if want is not None and f not in want:
            if f > max(want): break
            continue
        t = f / FPS; im = Image.frombuffer("RGB", (W, H), fr).convert("RGBA")
        for c in chunks:
            if c["t0"] <= t < c["t1"]:
                k = (t - c["t0"]) * FPS; sc = 0.86 + 0.14 * ease_out_back(k / 5); cim = c["im"]
                cim = cim.resize((max(1, int(cim.width * sc)), max(1, int(cim.height * sc))), Image.BICUBIC)
                al = min(1, 0.35 + k / 3)
                if al < 1: cim = cim.copy(); cim.putalpha(cim.getchannel("A").point(lambda v: int(v * al)))
                im.alpha_composite(cim, (int(540 - cim.width / 2), int(CAP_Y + (1 - ease_out_cubic(k / 5)) * 8 - cim.height / 2)))
        if PREVIEW: im.convert("RGB").save(f"{P}/pv_{t:05.2f}.png")
        else: enc.stdin.write(im.convert("RGB").tobytes())
    gp.kill()
    if PREVIEW: return
    enc.stdin.close(); enc.wait()
    af = ";".join(f"[0:a]atrim=start={s:.4f}:end={e:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={e - s - 0.01:.4f}:d=0.01[a{i}]" for i, (s, e) in enumerate(KEEP))
    af += ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,aformat=channel_layouts=stereo[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", CTA, "-filter_complex", af, "-map", "[o]", "-ar", "48000", f"{P}/cta_a.wav"], check=True)
    d0 = M1 - M0
    fc = (f"[0:v]trim=start={M0}:end={M1},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},format=yuv420p[va];[1:v]format=yuv420p[vb];[va][vb]concat=n=2:v=1:a=0[v];"
          f"[0:a]atrim=start={M0}:end={M1},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={d0 - 0.06:.3f}:d=0.06[aa];"
          f"[2:a]afade=t=in:d=0.02[ab];[aa][ab]concat=n=2:v=0:a=1,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", MAIN, "-i", f"{P}/cta_v.mp4", "-i", f"{P}/cta_a.wav", "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)

if __name__ == "__main__":
    for c in chunks: print(f'{c["t0"]:5.2f} {c["txt"]}', file=sys.stderr)
    main()
