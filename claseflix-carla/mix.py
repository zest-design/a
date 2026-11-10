# Mixes voice + music (ducked) + SFX cues and muxes with the silent render.
import subprocess, sys, json
TM = json.load(open('timemap.json'))
def new(t):  # first-take time -> current voiceover time
    for (o0, n0), (o1, n1) in zip(TM, TM[1:]):
        if t <= o1: return n0 + (n1 - n0) * (t - o0) / (o1 - o0)
    return t
END = 50.7
voice = sys.argv[1] if len(sys.argv) > 1 else 'audio/voz_es_v2.mp3'
out = sys.argv[2] if len(sys.argv) > 2 else 'claseflix_carla_es_funk.mp4'
music = sys.argv[3] if len(sys.argv) > 3 else 'audio/musica_funk.mp3'
mvol = float(sys.argv[4]) if len(sys.argv) > 4 else 0.34  # music level under the voice
whoosh = [new(t) for t in [4.05, 6.73, 9.1, 18.57, 21.9, 30.37, 32.25, 34.9, 37.05, 39.2, 41.75]] + [43.4, 45.15]
pops = [new(t) for t in [7.55, 7.9, 8.26, 12.62, 13.8, 15.73, 17.24, 24.96, 26.0, 27.26, 28.95, 29.75, 35.5, 36.3, 38.4]]
spark = [new(20.82), 45.42]
cues = [(f'audio/whoosh{1 + i % 2}.mp3', t, 0.35) for i, t in enumerate(whoosh)] + \
       [('audio/pop2.mp3', t, 0.30) for t in pops] + [('audio/sparkle.mp3', t, 0.45) for t in spark]
inputs = ['-i', 'build/video_mudo.mp4', '-i', voice, '-i', music]
f = []
f.append('[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0,asplit=2[vo][sc]')
f.append(f'[2:a]aresample=48000,aformat=channel_layouts=stereo,volume={mvol},apad,atrim=0:{END},afade=t=out:st={END - 1.2}:d=1.2[mu0]')
f.append('[mu0][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=350[mu]')
labels = []
for i, (fn, t, vol) in enumerate(cues):
    inputs += ['-i', fn]
    ms = int(t * 1000)
    f.append(f'[{3 + i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[s{i}]')
    labels.append(f'[s{i}]')
f.append(f'[vo][mu]{"".join(labels)}amix=inputs={2 + len(labels)}:normalize=0:duration=first,apad,atrim=0:{END},loudnorm=I=-14:TP=-1.5:LRA=11[aout]')
cmd = ['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(f), '-map', '0:v', '-map', '[aout]',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
print('wrote', out)
