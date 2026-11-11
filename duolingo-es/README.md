# Duolingo · anuncio vertical en español

Vídeo final: `duolingo_es.mp4` — 1080×1920, 30 fps, 36,4 s, narración femenina en español, -14 LUFS, color BT.709.

Estructura: 3 dolores (trabajo que pide inglés, viaje sin poder pedir un café, series pegado a los subtítulos) → giro "Eso se acaba hoy" → Duolingo (aprender jugando, pocos minutos al día, lecciones cortas, racha) → "¿El trabajo? Listo. ¿El viaje? Listo. ¿Tus series? ¡Sin subtítulos!" → logo + "Descárgalo gratis".

- `anim.html` — animación sincronizada con la narración; `render.mjs` — render a `build/video_mudo.mp4`; `mix.py` — mezcla voz + música + efectos.
- `assets/` — ilustraciones del personaje y logos/mascota de Duolingo enviados por el cliente; `fonts/` — Nunito (OFL); `audio/` — voz, música y efectos.
