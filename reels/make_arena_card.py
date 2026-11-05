# Crops the vertical arena.ai screen recording into a 980x551 landscape card clip that follows the page:
# each section opens on its title, then eases down to the top of the ranking.
import subprocess, sys, numpy as np
from PIL import Image
SRC = "/root/.claude/uploads/a523e79c-ba27-50f9-be90-91ab18a28e09/281bd173-arena_llm_1_1.mp4"
OUT = sys.argv[1]; PREV = sys.argv[2:] and [float(x) for x in sys.argv[2].split(",")]
SW, SH = 1320, 2868; CW, CH = 980, 552; WH = round(SW * CH / CW)   # window height in source px (742)
T0 = 0.9                                                              # skip the cookie banner
DROP = [(12.50, 12.96), (19.74, 20.23), (26.87, 27.26), (36.74, 37.26)]   # blank loading screens between sections
# (section start, window top on the title, window top on the ranking, seconds held on the title)
SEC = [(0.9, 500, 1220, 1.3), (12.8, 500, 1220, 1.2), (20.4, 500, 1100, 1.2), (27.3, 560, 1100, 1.3), (37.2, 520, 1268, 0.7)]
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
# nav menu opened by a tap (page below gets dimmed): the camera snaps up to the menu right at the tap
MENU = [(9.62, 12.45), (18.33, 19.75), (25.78, 26.85), (35.62, 36.75)]; MTOP = 300; MSNAP = 0.3
def top_at(t):
    s = max([x for x in SEC if x[0] <= t] or [SEC[0]], key=lambda x: x[0])
    k = t - s[0]
    y = s[1] + (s[2] - s[1]) * ease((k - s[3]) / 0.8)
    for a, b in MENU:
        if a - MSNAP <= t < b: y += (MTOP - y) * ease((t - (a - MSNAP)) / MSNAP)
    return y
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC], capture_output=True, text=True).stdout)
NF = int((dur - T0 - 0.05) * 30)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(T0), "-i", SRC, "-vf", "fps=30,format=rgb24", "-frames:v", str(NF), "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
if not PREV:
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{CW}x{CH}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
want = set(int(round((x - T0) * 30)) for x in PREV) if PREV else None
for f in range(NF):
    raw = p.stdout.read(SW * SH * 3)
    if len(raw) < SW * SH * 3: break
    if want is not None and f not in want:
        if f > max(want): break
        continue
    ts = T0 + f / 30
    if any(a <= ts < b for a, b in DROP): continue
    y = top_at(ts); y0 = int(y); fy = y - y0
    a = np.frombuffer(raw, np.uint8).reshape(SH, SW, 3)
    win = a[y0:y0 + WH + 1].astype(np.float32); win = win[:-1] * (1 - fy) + win[1:] * fy     # sub-pixel scroll, no jitter
    im = Image.fromarray(win.astype(np.uint8)).resize((CW, CH), Image.LANCZOS)
    if PREV: im.save(f"{OUT}_{T0 + f / 30:05.1f}.png")
    else: enc.stdin.write(im.tobytes())
p.kill()
if not PREV: enc.stdin.close(); enc.wait()
print("frames", NF, file=sys.stderr)
