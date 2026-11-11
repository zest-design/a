# Claseflix · Instagram Agent Skill (versión ilustrada)

Vídeo final: `claseflix_ig_skill_es.mp4` — 1080×1920, 30 fps, 58,2 s, voz original del presentador (aislada), -14 LUFS, color BT.709.

- `anim.html` — animación: panel explicativo por escena, presentador ilustrado (5 poses) y subtítulos sincronizados.
- `render.mjs` — renderiza `anim.html` a `build/video_mudo.mp4` (`node render.mjs`; `--times 1,2.5` para fotogramas sueltos).
- `mix.py` — mezcla voz + música funk (con ducking) + efectos y genera el MP4 final.
- `assets/` — ilustraciones del presentador y logo de Claseflix. `audio/` — voz aislada, música y efectos.
