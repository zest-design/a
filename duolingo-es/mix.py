# Mixes voiceover + ducked music + SFX cues and muxes with the silent render.
import subprocess, sys
out = sys.argv[1] if len(sys.argv) > 1 else 'duolingo_es.mp4'
END = 36.4
cues = [('audio/wrong.mp3', t, .30) for t in [2.46, 7.06, 10.86]] + \
       [(f'audio/whoosh{1 + i % 2}.mp3', t, .28) for i, t in enumerate([3.55, 7.95, 12.18, 13.7, 18.62, 23.88, 31.0])] + \
       [('audio/pop2.mp3', t, .24) for t in [0.75, 1.0, 9.0, 9.9, 15.75, 15.9, 16.03, 16.6, 19.5, 19.85, 20.15, 20.45, 32.1, 34.3]] + \
       [('audio/correct.mp3', t, .45) for t in [20.75, 25.49, 27.41, 29.28]] + \
       [('audio/sparkle.mp3', t, .35) for t in [13.25, 31.05]]
inputs = ['-i', 'build/video_mudo.mp4', '-i', 'audio/voz_es.mp3', '-i', 'audio/musica.mp3']
f = ['[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[vo][sc]',
     f'[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.32,apad,atrim=0:{END},afade=t=out:st={END - 1.4}:d=1.4[mu0]',
     '[mu0][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=350[mu]']
labels = []
for i, (fn, t, vol) in enumerate(cues):
    inputs += ['-i', fn]; ms = int(t * 1000)
    f.append(f'[{3 + i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[s{i}]'); labels.append(f'[s{i}]')
f.append(f'[vo][mu]{"".join(labels)}amix=inputs={2 + len(labels)}:normalize=0:duration=first,apad,atrim=0:{END},loudnorm=I=-14:TP=-1.5:LRA=11[aout]')
subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(f), '-map', '0:v', '-map', '[aout]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], check=True)
print('wrote', out)
