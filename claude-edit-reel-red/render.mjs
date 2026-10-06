// Renders anim.html frame-by-frame with headless Chromium, encodes an MP4 and
// muxes the narration audio.
// Usage: node render.mjs <narration.mp4> [out.mp4]
//        node render.mjs --range 0:800 seg.mp4   (video-only segment, used by render-parallel.sh)
//        node render.mjs --frames 30,300,900 [--grid]   (PNG stills only; --grid overlays the Instagram grid, --bg renders the background layer only)
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
const rangeIdx = args.indexOf('--range');
const rangeArg = rangeIdx >= 0 ? args[rangeIdx + 1] : null;
const mp4s = args.filter(a => a.endsWith('.mp4'));
const audio = mp4s[0];
const out = mp4s[1] || path.join(dir, 'claude_edit_reel_red.mp4');

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await page.goto('file://' + path.join(dir, 'anim.html') + '?render' + (grid ? '&grid' : ''));
await page.evaluate(() => Promise.all(['italic 900 40px BarlowC', 'italic 800 40px BarlowC', '200 40px BarlowC', '300 40px BarlowC', '300 40px Poppins', '400 40px Poppins', '600 40px Poppins'].map(f => document.fonts.load(f))));
if (args.includes('--bg')) await page.evaluate(() => { window.LAYER = 'bg'; });
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);
const grab = async t => {
  await page.evaluate(t => window.render(t), t);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: W, height: H } });
};

if (stills) {
  const sd = path.join(dir, args.includes('--bg') ? 'stills-bg' : 'stills'); fs.mkdirSync(sd, { recursive: true });
  for (const f of stills) fs.writeFileSync(path.join(sd, `f${String(f).padStart(4, '0')}.png`), await grab(f / FPS));
} else if (rangeArg) {
  // video-only segment of frames [a, b) — render-parallel.sh runs several and joins them
  const [a, b] = rangeArg.split(':').map(Number);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS), mp4s[0]],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = a; i < b; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', mp4s[0]);
} else {
  if (!audio) throw new Error('pass the narration video/audio as the first .mp4 argument');
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
    '-r', String(FPS), '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
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
