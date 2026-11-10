// Renders anim.html frame-by-frame with headless Chromium and encodes a silent MP4.
// Usage: node render.mjs [out.mp4] [--times 0.5,2,10]  (times => PNG stills only)
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30, Wd = 1080, Ht = 1920;
const args = process.argv.slice(2);
const ti = args.indexOf('--times');
const stills = ti >= 0 ? args[ti + 1].split(',').map(Number) : null;
const out = args.find(a => a.endsWith('.mp4')) || path.join(dir, 'build', 'video_mudo.mp4');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Wd, height: Ht }, deviceScaleFactor: 1 });
await page.goto('file://' + path.join(dir, 'anim.html') + '?render');
await page.waitForFunction(() => window.READY === true);
await page.evaluate(() => Promise.all([...document.images].map(i => i.decode().catch(() => {}))));
const duration = await page.evaluate(() => window.DURATION);
const grab = async (t, type = 'jpeg') => {
  await page.evaluate(t => window.render(t), t);
  return page.screenshot(type === 'png' ? { type: 'png' } : { type: 'jpeg', quality: 95 });
};

if (stills) {
  fs.mkdirSync(path.join(dir, 'stills'), { recursive: true });
  for (const t of stills) fs.writeFileSync(path.join(dir, 'stills', `t${t.toFixed(2)}.png`), await grab(t, 'png'));
} else {
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
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
