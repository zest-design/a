// Renders anim.html frame by frame (1080x1920, 30fps) and muxes the original audio.
// Usage:
//   node render.mjs                       -> reel_es.mp4
//   node render.mjs --stills 1.5,4.2      -> stills/t1.50.png ...  (add --guides to draw the red zones)
//   node render.mjs --check               -> reports relevant elements touching the red zones
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PW || 'playwright');
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30, W = 1080, H = 1920;
const args = process.argv.slice(2);
const opt = n => { const i = args.indexOf(n); return i >= 0 ? (args[i + 1] ?? true) : null; };
const stills = opt('--stills');
const check = args.includes('--check');
const guides = args.includes('--guides');
const audio = opt('--audio') || path.join(dir, 'audio.m4a');
const out = args.find(a => a.endsWith('.mp4')) || path.join(dir, 'reel_es.mp4');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('PAGE ERROR', e.message));
await page.goto('file://' + path.join(dir, 'anim.html') + (guides ? '?guides' : ''));
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);
const grab = async t => { await page.evaluate(t => window.render(t), t); return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: W, height: H } }); };

if (stills) {
  fs.mkdirSync(path.join(dir, 'stills'), { recursive: true });
  for (const t of String(stills).split(',').map(Number)) fs.writeFileSync(path.join(dir, 'stills', `t${t.toFixed(2)}.png`), await grab(t));
} else if (check) {
  const bad = new Map();
  for (let i = 0; i < duration * FPS; i += 2) {
    const t = i / FPS;
    await page.evaluate(t => window.render(t), t);
    const tr = await page.evaluate(t => window.inTransition(t), t);
    for (const s of await page.evaluate(() => window.checkSafe())) { const k = (tr ? '[transição] ' : '') + s.replace(/\[.*\]/, ''); if (!bad.has(k)) bad.set(k, `${t.toFixed(2)}s ${tr ? '(transição) ' : ''} ${s}`); }
  }
  console.log(bad.size ? [...bad.values()].join('\n') : 'OK: nenhuma informação relevante nas áreas vermelhas');
} else {
  const tmp = out.replace(/\.mp4$/, '.video.mp4');
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const total = Math.round(duration * FPS);
  for (let i = 0; i < total; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  if (fs.existsSync(audio)) {
    await new Promise(r => spawn('ffmpeg', ['-y', '-v', 'error', '-i', tmp, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' }).on('close', r));
    fs.unlinkSync(tmp);
  } else fs.renameSync(tmp, out);
  console.log('wrote', out);
}
await browser.close();
