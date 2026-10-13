// Renders anim.html frame-by-frame with headless Chromium and encodes an MP4
// (with a silent stereo track so editors and Reels accept it like any other clip).
// Usage: node render.mjs [out.mp4]
//        node render.mjs --frames 30,60,90 [--grid]   (PNG stills only; --grid overlays the Instagram grid)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30, W = 1080, H = 1920;
const args = process.argv.slice(2);
const stillsIdx = args.indexOf('--frames');
const stills = stillsIdx >= 0 ? args[stillsIdx + 1].split(',').map(Number) : null;
const grid = args.includes('--grid');
const out = args.find(a => a.endsWith('.mp4')) || path.join(dir, 'reel_97_dolares.mp4');

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await page.goto('file://' + path.join(dir, 'anim.html') + '?render' + (grid ? '&grid' : ''));
await page.evaluate(() => Promise.all(['italic 900 40px BarlowC', 'italic 800 40px BarlowC', '200 40px BarlowC', '300 40px BarlowC', '300 40px Poppins', '400 40px Poppins', '600 40px Poppins'].map(f => document.fonts.load(f))));
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);
const grab = async t => {
  await page.evaluate(t => window.render(t), t);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: W, height: H } });
};

if (stills) {
  const sd = path.join(dir, 'stills'); fs.mkdirSync(sd, { recursive: true });
  for (const f of stills) fs.writeFileSync(path.join(sd, `f${String(f).padStart(4, '0')}.png`), await grab(f / FPS));
} else {
  const total = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-map', '0:v', '-map', '1:a',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '128k', '-t', String(duration), '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < total; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close();
