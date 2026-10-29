# Append the presenter's CTA (take 2 of CTA_1.mp4) to the end of the animated reel.
# Captions on the CTA copy the animated reel's own caption style (grey sentence, current word bold white).
import json, re, sys, subprocess, difflib, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = "/tmp/claude-0/-home-user-a/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6/scratchpad"; P = f"{S}/p17"
U = "/root/.claude/uploads/4adeb0ae-e86a-540e-91ea-dcf609d3b0a6"
ANIM, CTA = f"{U}/7e0e4cee-reel-final-sin-rotulos.mp4", f"{U}/c5c0b77c-CTA_1.mp4"
OUT = sys.argv[1]; PREVIEW = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
W, H, FPS = 1080, 1920, 24
A_DUR = 59.875
KEEP = [(13.68, 23.10), (23.24, 23.72)]          # take 2, with the short hesitation before "mismo" tightened
CTA_DUR = sum(b - a for a, b in KEEP)
def m(t):
    o = 0.0
    for a, b in KEEP:
        if t <= a: return o
        if t < b: return o + t - a
        o += b - a
    return o
TEXT = "Y si quieres aprender a generar este tipo de contenido paso a paso, he preparado para ti un material, así que comenta aquí abajo y te lo haré llegar directamente para que puedas empezar a crearlos hoy mismo."
PK = [(w, t) for w, t, _ in json.load(open(f"{P}/wordsC.json")) if 13.0 < t < 23.8]
def norm(s): return re.sub(r"[^\wáéíóúñü]", "", s.lower())
ws = TEXT.split(); a = [norm(w) for w in ws]; b = [norm(w) for w, _ in PK]; times = [None] * len(ws)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
        for k in range(i2 - i1): times[i1 + k] = PK[j1 + k][1]
times[0] = max(times[0] or 13.72, 13.72)
for i in range(len(ws)):
    if times[i] is None:
        lo = max(j for j in range(i) if times[j] is not None); hi = next((j for j in range(i + 1, len(ws)) if times[j] is not None), None)
        times[i] = times[lo] + 0.18 if hi is None else times[lo] + (times[hi] - times[lo]) * (i - lo) / (hi - lo)
for i in range(1, len(times)): times[i] = max(times[i], times[i - 1] + 0.08)
WT = [(w, m(t)) for w, t in zip(ws, times)]          # word start in CTA-local seconds
# lines: up to 5 words / 30 chars, break after punctuation
LINES = []; cur = []
for k, (w, t) in enumerate(WT):
    cur.append(k)
    txt = " ".join(WT[j][0] for j in cur)
    nxt = WT[k + 1][0] if k + 1 < len(WT) else ""
    if re.search(r"[,.]$", w) or len(cur) >= 5 or len(txt) + 1 + len(nxt) > 30 or k == len(WT) - 1:
        LINES.append(cur); cur = []
FR = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 50)
FB = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 50)
CAP_Y = 1470
def caption(line, active):
    words = [WT[j][0] for j in line]; fonts = [FB if j == active else FR for j in line]
    sp = FR.getlength(" "); tw = sum(f.getlength(w) for w, f in zip(words, fonts)) + sp * (len(words) - 1)
    im = Image.new("RGBA", (W, 140), (0, 0, 0, 0)); sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im); ds = ImageDraw.Draw(sh); x = (W - tw) / 2
    for j, w, f in zip(line, words, fonts):
        col = (255, 255, 255, 255) if j == active else (205, 205, 205, 175)
        ds.text((x, 70), w, font=f, fill=(0, 0, 0, 150), anchor="lm"); d.text((x, 70), w, font=f, fill=col, anchor="lm"); x += f.getlength(w) + sp
    out = sh.filter(ImageFilter.GaussianBlur(6)); out.alpha_composite(im); return out
def overlay_for(t):
    li = None
    for L in LINES:
        if WT[L[0]][1] <= t: li = L
    if li is None: return None
    last_end = WT[li[-1]][1] + 0.6
    nxt = next((L for L in LINES if WT[L[0]][1] > t), None)
    if nxt is None and t > CTA_DUR: return None
    act = max(j for j in li if WT[j][1] <= t)
    return caption(li, act)

def main():
    vf = ";".join(f"[0:v]trim=start={s:.4f}:end={e:.4f},setpts=PTS-STARTPTS[v{i}]" for i, (s, e) in enumerate(KEEP))
    vf += ";" + "".join(f"[v{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=1:a=0,fps={FPS},format=rgb24[o]"
    nf = int(round(CTA_DUR * FPS))
    gp = subprocess.Popen(["ffmpeg", "-v", "error", "-i", CTA, "-filter_complex", vf, "-map", "[o]", "-frames:v", str(nf), "-f", "rawvideo", "-"],
                          stdout=subprocess.PIPE, bufsize=10 ** 8)
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
        im = Image.frombuffer("RGB", (W, H), fr).convert("RGBA"); ov = overlay_for(f / FPS)
        if ov is not None: im.alpha_composite(ov, (0, CAP_Y - 70))
        if PREVIEW: im.convert("RGB").save(f"{P}/pv_{f / FPS:05.2f}.png")
        else: enc.stdin.write(im.convert("RGB").tobytes())
    gp.kill()
    if PREVIEW: return
    enc.stdin.close(); enc.wait()
    # CTA voice: same trims, tiny fades at the joins, loudness matched to the animated reel (-14.2 LUFS)
    af = ";".join(f"[0:a]atrim=start={s:.4f}:end={e:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={e - s - 0.01:.4f}:d=0.01[a{i}]" for i, (s, e) in enumerate(KEEP))
    af += ";" + "".join(f"[a{i}]" for i in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=0:a=1,highpass=f=70,loudnorm=I=-14.2:TP=-1.5:LRA=9,aresample=44100,aformat=channel_layouts=stereo[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", CTA, "-filter_complex", af, "-map", "[o]", "-ar", "44100", f"{P}/cta_a.wav"], check=True)
    # final: animated reel untouched in timing (24 fps), then the CTA; short audio fade at the cut
    fc = (f"[0:v]fps={FPS},format=yuv420p[va];[1:v]format=yuv420p[vb];[va][vb]concat=n=2:v=1:a=0[v];"
          f"[0:a]afade=t=out:st={A_DUR - 0.06:.3f}:d=0.06[aa];[2:a]afade=t=in:d=0.02[ab];[aa][ab]concat=n=2:v=0:a=1,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ANIM, "-i", f"{P}/cta_v.mp4", "-i", f"{P}/cta_a.wav", "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)

if __name__ == "__main__":
    for L in LINES: print(f"{WT[L[0]][1]:5.2f}  " + " ".join(WT[j][0] for j in L), file=sys.stderr)
    main()
