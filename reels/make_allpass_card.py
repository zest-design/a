# AllPass (HostGator) page recording from 0:11 -> 980x552 card clip: fixed window over the scrolling page,
# long reading pauses shortened and the still ending dropped.
import subprocess, sys
SRC = "/root/.claude/uploads/a523e79c-ba27-50f9-be90-91ab18a28e09/0b4b0bdb-allpass-hostgator_1.mp4"
OUT = sys.argv[1]
SEG = [(11.0, 26.3), (27.1, 35.6), (36.4, 40.8)]
Y = 520                      # window top: hero tag, headline, text and the yellow button fit at the start
f = ";".join(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30,crop=1320:742:0:{Y},scale=980:552:flags=lanczos[s{i}]" for i, (a, b) in enumerate(SEG))
f += ";" + "".join(f"[s{i}]" for i in range(len(SEG))) + f"concat=n={len(SEG)}:v=1:a=0,format=yuv420p[o]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", f, "-map", "[o]", "-c:v", "libx264", "-preset", "slow", "-crf", "12", OUT], check=True)
