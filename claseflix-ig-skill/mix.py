# Mixes the presenter's isolated voice + ducked music + SFX cues and muxes with the silent render.
import subprocess, sys
out = sys.argv[1] if len(sys.argv) > 1 else 'claseflix_ig_skill_es.mp4'
END = 58.2
scene_starts = [1.75, 3.55, 5.45, 9.35, 13.25, 17.15, 20.05, 21.55, 23.35, 26.05, 30.1, 33.75, 37.05, 41.05, 48.95, 52.55]
whoosh = [t - 0.08 for t in scene_starts]
pops = [0.15, 1.3, 2.3, 2.55, 3.1, 4.2, 4.6, 5.1, 6.35, 11.0, 11.5, 12.0, 15.2, 16.9, 19.3, 22.9, 24.4, 27.4, 28.0, 28.9,
        35.95, 40.2, 44.4, 45.0, 45.8, 46.9, 48.1, 51.2, 56.8]
spark = [8.72, 31.65, 57.35]
cues = [(f'audio/whoosh{1 + i % 2}.mp3', t, 0.28) for i, t in enumerate(whoosh)] + \
       [('audio/pop2.mp3', t, 0.24) for t in pops] + [('audio/sparkle.mp3', t, 0.35) for t in spark]
inputs = ['-i', 'build/video_mudo.mp4', '-i', 'audio/voz_rapaz.mp3', '-i', 'audio/musica_funk60.mp3']
f = ['[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[vo][sc]',
     f'[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.28,apad,atrim=0:{END},afade=t=out:st={END - 1.5}:d=1.5[mu0]',
     '[mu0][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=350[mu]']
labels = []
for i, (fn, t, vol) in enumerate(cues):
    inputs += ['-i', fn]; ms = int(max(0, t) * 1000)
    f.append(f'[{3 + i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[s{i}]'); labels.append(f'[s{i}]')
f.append(f'[vo][mu]{"".join(labels)}amix=inputs={2 + len(labels)}:normalize=0:duration=first,apad,atrim=0:{END},loudnorm=I=-14:TP=-1.5:LRA=11[aout]')
subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(f), '-map', '0:v', '-map', '[aout]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], check=True)
print('wrote', out)
