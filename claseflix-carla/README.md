# Claseflix · Carla (anuncio vertical en español)

Vídeos finales (1080×1920, 30 fps, 50,7 s, narración femenina en español, -14 LUFS):
- `claseflix_carla_es_funk.mp4` — música funk/neo-soul (más energía)
- `claseflix_carla_es_lofi.mp4` — música lo-fi (más relajada)

- `anim.html` — animación (escenas sincronizadas palabra por palabra con la narración).
- `render.mjs` — renderiza `anim.html` a `build/video_mudo.mp4` (`node render.mjs`; `--times 1,2.5` para fotogramas sueltos).
- `mix.py` — mezcla voz + música (con ducking) + efectos y genera el MP4 final (`python3 mix.py [voz] [salida] [música] [volumen]`).
- `timemap.js` / `timemap.json` — anclas de tiempo que sincronizan las escenas y efectos con la narración actual.
- `assets/` — ilustraciones de Carla (3 poses) y logo de Claseflix.
- `audio/` — narración, música y efectos.
