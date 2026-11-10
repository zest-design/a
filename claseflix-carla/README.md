# Claseflix · Carla (anuncio vertical en español)

Vídeo final: `claseflix_carla_es.mp4` — 1080×1920, 30 fps, 50,6 s, narración femenina en español, -14 LUFS.

- `anim.html` — animación (escenas sincronizadas palabra por palabra con la narración).
- `render.mjs` — renderiza `anim.html` a `build/video_mudo.mp4` (`node render.mjs`; `--times 1,2.5` para fotogramas sueltos).
- `mix.py` — mezcla voz + música (con ducking) + efectos y genera el MP4 final.
- `assets/` — ilustraciones de Carla (3 poses) y logo de Claseflix.
- `audio/` — narración, música y efectos.
