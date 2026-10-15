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

if (stills) {
  const sd = path.join(dir, 'stills'); fs.mkdirSync(sd, { recursive: true });
  for (const f of stills) fs.writeFileSync(path.join(sd, `f${String(f).padStart(4, '0')}.png`), await grab(f / FPS));
} else {
  // camada gráfica (com alfa) sobre o vídeo original; áudio original normalizado para -14 LUFS
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-i', src, '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-filter_complex', '[0:v]fps=30,scale=1080:1920:flags=lanczos,setsar=1[b];[b][1:v]overlay=0:0:eof_action=pass[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]',
    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS),
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
