// Renders anim.html frame-by-frame with headless Chromium and encodes an MP4.
// Usage: node render.mjs [out.mp4] [--frames 0,48,96] (frames => PNG stills only)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 24;
const args = process.argv.slice(2);
const stillsIdx = args.indexOf('--frames');
const stills = stillsIdx >= 0 ? args[stillsIdx + 1].split(',').map(Number) : null;
const out = args.find(a => a.endsWith('.mp4')) || path.join(dir, 'stitch_text_clip2.mp4');

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto('file://' + path.join(dir, 'anim.html') + '?render');
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);
const grab = async t => {
  await page.evaluate(t => window.render(t), t);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1920, height: 1080 } });
};

if (stills) {
  fs.mkdirSync(path.join(dir, 'stills'), { recursive: true });
  for (const f of stills) fs.writeFileSync(path.join(dir, 'stills', `f${String(f).padStart(4, '0')}.png`), await grab(f / FPS));
} else {
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const total = Math.round(duration * FPS);
  for (let i = 0; i < total; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 48 === 0) console.log(`frame ${i}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close();
