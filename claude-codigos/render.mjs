// Renderiza anim.html quadro a quadro (Chromium headless) e compõe sobre o vídeo original.
// Uso: node render.mjs <video-original.mp4> [saida.mp4] [--frames 0,120,300] (só PNGs de conferência)
import { createRequire } from 'node:module';
import { spawn, execSync } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch { pw = require(path.join(execSync('npm root -g').toString().trim(), 'playwright')); }
const { chromium } = pw;

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30;
const args = process.argv.slice(2);
const stillsIdx = args.indexOf('--frames');
const stills = stillsIdx >= 0 ? args[stillsIdx + 1].split(',').map(Number) : null;
const mp4s = args.filter(a => a.endsWith('.mp4'));
const src = mp4s[0];
const out = mp4s[1] || path.join(dir, 'codigos_secretos_claude.mp4');

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('pageerror', e.message));
await page.goto('file://' + path.join(dir, 'anim.html') + '?render');
await page.evaluate(() => window.ready);
const duration = await page.evaluate(() => window.DURATION);
const grab = async t => {
  await page.evaluate(t => window.render(t), t);
  return page.screenshot({ type: 'png', omitBackground: true });
};

// Cortes na gravação original (mesmos valores de anim.html): rosto = frames [14,107), teto = frames [128,2059).
// Remove o silêncio do início, o silêncio entre o rosto e o teto e a sobra do final.
const F = n => (n / FPS).toFixed(5);
const CUTS = '[0:v]trim=start_frame=14:end_frame=107,setpts=PTS-STARTPTS[v1];[0:v]trim=start_frame=128:end_frame=2059,setpts=PTS-STARTPTS[v2];'
  + '[v1][v2]concat=n=2:v=1:a=0,fps=30,scale=1080:1920:flags=lanczos,setsar=1[b];';
const ACUTS = `[0:a]atrim=start=${F(14)}:end=${F(107)},asetpts=PTS-STARTPTS,afade=t=in:d=0.01[a1];`
  + `[0:a]atrim=start=${F(128)}:end=${F(2059)},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=${((2059 - 128) / FPS - 0.08).toFixed(3)}:d=0.08[a2];[a1][a2]concat=n=2:v=0:a=1[a12]`;

if (stills) {
  const sd = path.join(dir, 'stills'); fs.mkdirSync(sd, { recursive: true });
  for (const f of stills) fs.writeFileSync(path.join(sd, `f${String(f).padStart(4, '0')}.png`), await grab(f / FPS));
} else {
  // 1) aplica os cortes na gravação original (arquivo intermediário quase sem perdas)
  const cut = path.join(dir, 'stills', '_cut.mp4'); fs.mkdirSync(path.dirname(cut), { recursive: true });
  execSync(`ffmpeg -y -v error -i "${src}" -filter_complex "${CUTS}${ACUTS}" -map "[b]" -map "[a12]" -c:v libx264 -preset fast -crf 10 -c:a pcm_s16le -f matroska "${cut}.raw.mkv"`);
  // normalização do áudio feita aqui (fazer no mesmo passo do pipe de imagens perdia amostras)
  execSync(`ffmpeg -y -v error -i "${cut}.raw.mkv" -map 0:v -map 0:a -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -c:a pcm_s16le -f matroska "${cut}"`);
  // 2) camada gráfica (com alfa) sobre o vídeo cortado; áudio normalizado para -14 LUFS
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-i', cut, '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-filter_complex', '[0:v][1:v]overlay=0:0:eof_action=pass[v]',
    '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const total = Math.round(duration * FPS);
  for (let i = 0; i < total; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close();
