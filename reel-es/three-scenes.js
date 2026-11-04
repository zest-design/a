// Real 3D scenes (three.js) for the reel: a photoreal laptop and an isometric farm-to-table diagram.
// Each scene owns one WebGL renderer; posters copy its canvas into their own 2D canvas.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const W = 1080, H = 1920;
const C = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const P = (t, a, b) => C((t - a) / (b - a));
const L = (a, b, k) => a + (b - a) * k;
const eo = k => 1 - Math.pow(1 - k, 3);
const eio = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const eback = (k, s = 1.70158) => 1 + (s + 1) * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2);
RectAreaLightUniformsLib.init();

function makeRenderer(alpha) {
  const r = new THREE.WebGLRenderer({ antialias: true, alpha, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  r.setPixelRatio(1); r.setSize(W, H, false);
  r.toneMapping = THREE.ACESFilmicToneMapping; r.outputColorSpace = THREE.SRGBColorSpace;
  r.shadowMap.enabled = true; r.shadowMap.type = THREE.VSMShadowMap;
  return r;
}
function cached(renderFn, END) {
  let lastT = null, endCv = null;
  return lt => {
    if (lt >= END) {
      if (!endCv) { renderFn(END); endCv = document.createElement('canvas'); endCv.width = W; endCv.height = H; endCv.getContext('2d').drawImage(renderFn.canvas, 0, 0); endCv.meta = renderFn.meta(); }
      return { canvas: endCv, meta: endCv.meta };
    }
    if (lt !== lastT) { renderFn(lt); lastT = lt; }
    return { canvas: renderFn.canvas, meta: renderFn.meta() };
  };
}
function radialTexture(stops, size = 512) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const g = c.getContext('2d'), gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  stops.forEach(([o, col]) => gr.addColorStop(o, col)); g.fillStyle = gr; g.fillRect(0, 0, size, size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// =====================================================================
// LAPTOP
// =====================================================================
function buildLaptop() {
  const renderer = makeRenderer(false);
  const scene = new THREE.Scene();
  // studio backdrop: screen-space gradient + matching fog for the floor horizon
  const bg = document.createElement('canvas'); bg.width = 540; bg.height = 960;
  { const g = bg.getContext('2d'); const gr = g.createRadialGradient(270, 470, 20, 270, 470, 620); gr.addColorStop(0, '#22305A'); gr.addColorStop(.45, '#101834'); gr.addColorStop(1, '#05070F'); g.fillStyle = gr; g.fillRect(0, 0, 540, 960); }
  scene.background = new THREE.CanvasTexture(bg); scene.background.colorSpace = THREE.SRGBColorSpace;
  scene.fog = new THREE.Fog(0x0A1024, 22, 46);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture;
  scene.environmentIntensity = .42;

  const camera = new THREE.PerspectiveCamera(24, W / H, .1, 200);

  // ---- materials ----
  const alu = new THREE.MeshPhysicalMaterial({ color: 0x5A5E67, metalness: 1, roughness: .34, clearcoat: .15, clearcoatRoughness: .4 });
  const aluDark = new THREE.MeshPhysicalMaterial({ color: 0x2C2F35, metalness: .9, roughness: .5 });
  const keyMat = new THREE.MeshPhysicalMaterial({ color: 0x0D0D0F, metalness: .05, roughness: .5, sheen: .4, sheenRoughness: .6, sheenColor: 0x333344 });
  const padMat = new THREE.MeshPhysicalMaterial({ color: 0x4E525A, metalness: .7, roughness: .18, clearcoat: 1, clearcoatRoughness: .08 });
  const bezelMat = new THREE.MeshPhysicalMaterial({ color: 0x030304, metalness: 0, roughness: .06, clearcoat: 1, clearcoatRoughness: .03 });
  const grilleCv = document.createElement('canvas'); grilleCv.width = 128; grilleCv.height = 512;
  { const g = grilleCv.getContext('2d'); g.fillStyle = '#5A5E67'; g.fillRect(0, 0, 128, 512); g.fillStyle = '#0b0b0c'; for (let y = 6; y < 512; y += 12) for (let x = 6 + (y / 12 % 2) * 6; x < 128; x += 12) { g.beginPath(); g.arc(x, y, 2.6, 0, 7); g.fill(); } }
  const grilleTex = new THREE.CanvasTexture(grilleCv); grilleTex.colorSpace = THREE.SRGBColorSpace; grilleTex.anisotropy = 8;
  const grilleMat = new THREE.MeshPhysicalMaterial({ map: grilleTex, metalness: .9, roughness: .4 });

  // ---- screen texture (website) ----
  const sc = document.createElement('canvas'); sc.width = 1600; sc.height = 1000;
  const sx = sc.getContext('2d');
  const screenTex = new THREE.CanvasTexture(sc); screenTex.colorSpace = THREE.SRGBColorSpace; screenTex.anisotropy = 8;
  const drawScreen = (on, h, b, wk) => {
    const g = sx;
    const gr = g.createLinearGradient(0, 0, 1600, 1000); gr.addColorStop(0, '#140F2A'); gr.addColorStop(.6, '#2A1E5C'); gr.addColorStop(1, '#4B2C8F');
    g.fillStyle = gr; g.fillRect(0, 0, 1600, 1000);
    g.globalAlpha = .5; const rg = g.createRadialGradient(1200, 200, 10, 1200, 200, 700); rg.addColorStop(0, 'rgba(183,243,74,.35)'); rg.addColorStop(1, 'rgba(183,243,74,0)'); g.fillStyle = rg; g.fillRect(0, 0, 1600, 1000); g.globalAlpha = 1;
    g.fillStyle = 'rgba(255,255,255,.08)'; g.fillRect(0, 96, 1600, 2);
    g.font = '800 34px Inter'; g.fillStyle = '#B7F34A'; g.fillText('● Ritmo', 56, 62);
    g.font = '500 28px Inter'; g.fillStyle = '#B9B0E6'; ['Producto', 'Precios', 'Equipos', 'Blog'].forEach((s, i) => g.fillText(s, 300 + i * 170, 60)); g.fillText('Entrar', 1460, 60);
    g.textAlign = 'center';
    g.globalAlpha = h; g.fillStyle = '#fff'; g.font = '800 104px Inter';
    g.fillText('Organiza tu semana', 800, 330 + (1 - h) * 30); g.fillText('en minutos.', 800, 450 + (1 - h) * 30);
    g.font = '500 34px Inter'; g.fillStyle = '#C9C1F0'; g.fillText('Arrastra tus tareas y Ritmo organiza el resto.', 800, 530 + (1 - h) * 20);
    g.globalAlpha = b; g.fillStyle = '#B7F34A'; g.beginPath(); g.roundRect(650, 580, 300, 80, 40); g.fill();
    g.fillStyle = '#111'; g.font = '800 32px Inter'; g.fillText('Empieza gratis', 800, 632);
    g.globalAlpha = wk; g.fillStyle = 'rgba(255,255,255,.07)'; g.beginPath(); g.roundRect(120, 720, 1360, 220, 24); g.fill();
    g.textAlign = 'left'; g.font = '700 24px Inter'; g.fillStyle = '#B9B0E6'; ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'].forEach((d, i) => g.fillText(d, 160 + i * 270, 770));
    [[160, 200, '#B7F34A'], [430, 160, '#7CC6FE'], [700, 230, '#F49AC2'], [970, 150, '#FFD43B'], [1240, 190, '#B7F34A']].forEach(([x, w, c], i) => { g.fillStyle = c; g.globalAlpha = wk * .85; g.beginPath(); g.roundRect(x, 800 + (i % 2) * 56, w * C(wk * 1.4 - i * .1), 40, 10); g.fill(); });
    g.globalAlpha = 1; g.textAlign = 'left';
    // display off: near black with faint reflection only
    if (on < 1) { g.fillStyle = `rgba(0,0,0,${1 - on})`; g.fillRect(0, 0, 1600, 1000); }
    screenTex.needsUpdate = true;
  };

  // ---- geometry ----
  const BW = 3.04, BD = 2.12, BH = .11, LT = .055, LD = 2.0;
  const lap = new THREE.Group(); scene.add(lap);
  const base = new THREE.Mesh(new RoundedBoxGeometry(BW, BH, BD, 6, .05), alu);
  base.position.y = BH / 2; base.castShadow = true; base.receiveShadow = true; lap.add(base);
  // keyboard well + keys
  const well = new THREE.Mesh(new RoundedBoxGeometry(2.56, .01, 1.02, 3, .004), aluDark);
  well.position.set(0, BH + .001, -.42); lap.add(well);
  const U = .168, G = .014, rows = [[Array(14).fill(14.5 / 14), .5], [[...Array(13).fill(1), 1.5], 1], [[1.5, ...Array(13).fill(1)], 1], [[1.75, ...Array(11).fill(1), 1.75], 1], [[2.25, ...Array(10).fill(1), 2.25], 1], [[1, 1, 1.25, 1.5, 5, 1.5, 1.25, 1, 1], 1]];
  const keyDefs = []; let zc = -.88;
  rows.forEach(([ws, hh]) => { let x = -14.5 * U / 2; const d = hh * U - G; ws.forEach(w => { keyDefs.push([x + w * U / 2, zc + d / 2, w * U - G, d]); x += w * U; }); zc += hh * U; });
  const keyGeo = new RoundedBoxGeometry(1, .03, 1, 2, .12);
  const keys = new THREE.InstancedMesh(keyGeo, keyMat, keyDefs.length);
  const m4 = new THREE.Matrix4();
  keyDefs.forEach(([x, z, w, d], i) => { m4.compose(new THREE.Vector3(x, BH + .012, z), new THREE.Quaternion(), new THREE.Vector3(w, 1, d)); keys.setMatrixAt(i, m4); });
  keys.castShadow = true; keys.receiveShadow = true; lap.add(keys);
  const pad = new THREE.Mesh(new RoundedBoxGeometry(1.3, .006, .8, 3, .003), padMat); pad.position.set(0, BH + .0015, .56); lap.add(pad);
  [-1, 1].forEach(s => { const gr = new THREE.Mesh(new THREE.PlaneGeometry(.2, .98), grilleMat); gr.rotation.x = -Math.PI / 2; gr.position.set(s * 1.4, BH + .002, -.42); lap.add(gr); });
  const lip = new THREE.Mesh(new THREE.BoxGeometry(.5, .02, .04), aluDark); lip.position.set(0, BH - .02, BD / 2 + .005); lap.add(lip);
  const hinge = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, 2.5, 24), aluDark); hinge.rotation.z = Math.PI / 2; hinge.position.set(0, BH + .02, -BD / 2 + .02); lap.add(hinge);
  // lid (pivot at the back edge)
  const pivot = new THREE.Group(); pivot.position.set(0, BH + .02, -BD / 2 + .02); lap.add(pivot);
  const lid = new THREE.Mesh(new RoundedBoxGeometry(BW, LD, LT, 6, .025), alu); lid.position.set(0, LD / 2, -LT / 2); lid.castShadow = true; pivot.add(lid);
  const bezel = new THREE.Mesh(new RoundedBoxGeometry(BW - .04, LD - .04, .006, 3, .002), bezelMat); bezel.position.set(0, LD / 2, .002); pivot.add(bezel);
  const screenMat = new THREE.MeshPhysicalMaterial({ color: 0x000000, emissive: 0xffffff, emissiveMap: screenTex, emissiveIntensity: 0, roughness: .05, clearcoat: 1, clearcoatRoughness: .02 });
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(2.86, 1.79), screenMat); screen.position.set(0, LD / 2 + .03, .0062); pivot.add(screen);
  const cam = new THREE.Mesh(new THREE.CircleGeometry(.018, 24), new THREE.MeshPhysicalMaterial({ color: 0x101830, roughness: .1, clearcoat: 1 })); cam.position.set(0, LD - .055, .0063); pivot.add(cam);
  // screen light spilling onto the keyboard
  const spill = new THREE.RectAreaLight(0x9C90FF, 0, 2.86, 1.79); spill.position.set(0, LD / 2 + .03, .02); spill.rotation.y = Math.PI; pivot.add(spill);

  // ---- floor, contact shadow, lights ----
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ color: 0x0B1128, roughness: .5, metalness: .05 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const ao = new THREE.Mesh(new THREE.PlaneGeometry(4.4, 3.4), new THREE.MeshBasicMaterial({ map: radialTexture([[0, 'rgba(0,0,0,.75)'], [.55, 'rgba(0,0,0,.35)'], [1, 'rgba(0,0,0,0)']]), transparent: true, depthWrite: false }));
  ao.rotation.x = -Math.PI / 2; ao.position.y = .002; scene.add(ao);
  const pool = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), new THREE.MeshBasicMaterial({ map: radialTexture([[0, 'rgba(110,130,220,.12)'], [1, 'rgba(110,130,220,0)']]), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  pool.rotation.x = -Math.PI / 2; pool.position.y = .001; scene.add(pool);
  const key = new THREE.RectAreaLight(0xFFF4E8, 5.5, 5, 2.4); key.position.set(-4, 5.5, 4.5); key.lookAt(0, .4, 0); scene.add(key);
  const rim = new THREE.RectAreaLight(0x7A6BFF, 9, 6, 1.6); rim.position.set(2.5, 2.8, -5); rim.lookAt(0, 1, 0); scene.add(rim);
  const fill = new THREE.RectAreaLight(0x5AA0FF, 1.6, 4, 3); fill.position.set(5, 2, 3); fill.lookAt(0, .5, 0); scene.add(fill);
  const sun = new THREE.DirectionalLight(0xffffff, .9); sun.position.set(-1.5, 8, 2.5); sun.castShadow = true;
  Object.assign(sun.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: 1, far: 20 }); sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 10; sun.shadow.blurSamples = 20; sun.shadow.bias = -.0004;
  scene.add(sun);

  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), .32, .55, .82); composer.addPass(bloom);
  composer.addPass(new OutputPass());

  const fn = lt => {
    // camera: slow orbit + dolly in
    const k = eio(P(lt, 0, 2.4));
    const az = L(30, 12, k) * Math.PI / 180, el = L(25, 16, k) * Math.PI / 180, dist = L(25, 20, k);
    const tgt = new THREE.Vector3(0, L(.55, .8, k), 0);
    camera.position.set(tgt.x + dist * Math.cos(el) * Math.sin(az), tgt.y + dist * Math.sin(el), tgt.z + dist * Math.cos(el) * Math.cos(az));
    camera.lookAt(tgt); camera.updateProjectionMatrix();
    lap.position.y = (1 - eo(P(lt, 0, .5))) * .6;
    // lid opens from closed to ~108°
    const ok = eback(P(lt, .25, 1.35), .9);
    pivot.rotation.x = L(Math.PI / 2 - .012, -.31, ok);
    const on = eo(P(lt, .85, 1.25));
    screenMat.emissiveIntensity = 1.05 * on;
    spill.intensity = 1.8 * on;
    drawScreen(on, eo(P(lt, 1.0, 1.45)), eo(P(lt, 1.2, 1.5)), eo(P(lt, 1.3, 1.9)));
    composer.render();
  };
  fn.canvas = renderer.domElement; fn.meta = () => ({});
  return cached(fn, 2.6);
}

// =====================================================================
// FARM → TABLE (isometric, orthographic)
// =====================================================================
export const FARM_STEPS = [
  { t: 'Cosecha', s: 'Día 1', cap: 'Cosechamos los tomates en el campo.', a: .45, b: 1.1 },
  { t: 'Empaque', s: 'Día 2', cap: 'Se lavan y se empacan el mismo día.', a: 1.1, b: 1.75 },
  { t: 'Tu mesa', s: 'Día 3', cap: 'Llegan frescos a tu mesa.', a: 1.75, b: 2.6 },
];
function buildFarm() {
  const renderer = makeRenderer(true); renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture; scene.environmentIntensity = .55;
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -100, 200);
  const M = c => new THREE.MeshStandardMaterial({ color: c, roughness: .78, metalness: 0 });
  const add = (geo, mat, x, y, z, parent = scene) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m; };
  const RB = (w, h, d, r = .08) => new RoundedBoxGeometry(w, h, d, 3, r);

  const world = new THREE.Group(); scene.add(world);
  // ground: grass on soil
  const grass = add(RB(12, .5, 12, .3), M(0x93CC6E), 0, -.25, 0, world);
  add(RB(11.8, 1.1, 11.8, .3), M(0x8A5A3A), 0, -.95, 0, world).castShadow = false;
  // ---- stage 1: field + barn + silo (back-left) ----
  const st1 = new THREE.Group(); world.add(st1);
  add(RB(4.6, .12, 4.2, .05), M(0x6B4A2F), -3.2, .06, -3.0, st1);
  const crops = [];
  const leaf = M(0x3E9B3A), tom = new THREE.MeshStandardMaterial({ color: 0xE5412F, roughness: .35 });
  for (let i = 0; i < 6; i++) for (let j = 0; j < 7; j++) {
    const g = new THREE.Group(); g.position.set(-5.1 + j * .62, .12, -4.7 + i * .66); st1.add(g);
    add(new THREE.ConeGeometry(.2, .5, 7), leaf, 0, .25, 0, g);
    const tm = add(new THREE.SphereGeometry(.09, 10, 8), tom, .1, .3, .08, g);
    crops.push({ g, tm });
  }
  const barn = new THREE.Group(); barn.position.set(-.6, 0, -4.2); st1.add(barn);
  add(RB(2.0, 1.5, 1.6, .04), M(0xC0392B), 0, .75, 0, barn);
  const roofShape = new THREE.Shape(); roofShape.moveTo(-1.15, 0); roofShape.lineTo(0, .85); roofShape.lineTo(1.15, 0); roofShape.lineTo(-1.15, 0);
  const roof = add(new THREE.ExtrudeGeometry(roofShape, { depth: 1.8, bevelEnabled: false }), M(0x7B241C), 0, 1.5, -.9, barn);
  add(new THREE.BoxGeometry(.8, 1.0, .05), M(0xF5F0E6), 0, .5, .81, barn);
  add(new THREE.BoxGeometry(.66, .86, .06), M(0x922B21), 0, .5, .82, barn);
  const silo = new THREE.Group(); silo.position.set(1.0, 0, -4.9); st1.add(silo);
  add(new THREE.CylinderGeometry(.42, .42, 2.4, 24), new THREE.MeshStandardMaterial({ color: 0xCFD6DB, roughness: .35, metalness: .6 }), 0, 1.2, 0, silo);
  add(new THREE.SphereGeometry(.42, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xA8B2B9, roughness: .3, metalness: .7 }), 0, 2.4, 0, silo);
  // ---- stage 2: packing plant (right) ----
  const st2 = new THREE.Group(); st2.position.set(3.4, 0, -2.4); world.add(st2);
  add(RB(3.0, 1.5, 2.4, .05), M(0xB9C2CC), 0, .75, 0, st2);
  for (let i = 0; i < 3; i++) { const s = new THREE.Shape(); s.moveTo(0, 0); s.lineTo(0, .55); s.lineTo(1.0, 0); s.lineTo(0, 0); add(new THREE.ExtrudeGeometry(s, { depth: 2.4, bevelEnabled: false }), M(0x8395A7), -1.5 + i * 1.0, 1.5, -1.2, st2); }
  add(new THREE.CylinderGeometry(.16, .2, 1.4, 16), M(0x7F8C8D), 1.0, 2.2, -.7, st2);
  add(new THREE.BoxGeometry(1.2, .9, .06), M(0x34495E), .3, .45, 1.21, st2);
  const crateMat = M(0xC89B62);
  [[-1.2, .9], [-.75, .95], [-1.0, 1.4]].forEach(([x, z], i) => add(RB(.36, .3, .36, .03), crateMat, x, .15 + (i === 2 ? .3 : 0), z + .4, st2));
  // ---- stage 3: house + table (front) ----
  const st3 = new THREE.Group(); st3.position.set(.2, 0, 3.4); world.add(st3);
  add(RB(2.2, 1.4, 1.9, .05), M(0xF4E6CC), 0, .7, 0, st3);
  const hr = new THREE.Shape(); hr.moveTo(-1.3, 0); hr.lineTo(0, .9); hr.lineTo(1.3, 0); hr.lineTo(-1.3, 0);
  add(new THREE.ExtrudeGeometry(hr, { depth: 2.1, bevelEnabled: false }), M(0xD9673E), 0, 1.4, -1.05, st3);
  const winMat = new THREE.MeshStandardMaterial({ color: 0xFFE3A3, emissive: 0xFFC766, emissiveIntensity: .6, roughness: .3 });
  add(new THREE.BoxGeometry(.06, .55, .5), winMat, 1.11, .85, -.45, st3);
  add(new THREE.BoxGeometry(.06, .9, .45), M(0x7A4A2A), 1.11, .45, .4, st3);
  add(new THREE.BoxGeometry(.5, .45, .06), winMat, -.4, .85, .96, st3);
  const table = new THREE.Group(); table.position.set(.3, 0, 1.75); st3.add(table);
  add(new THREE.CylinderGeometry(.62, .62, .06, 28), M(0xFFFFFF), 0, .62, 0, table);
  add(new THREE.CylinderGeometry(.06, .08, .6, 10), M(0x8A6A4A), 0, .3, 0, table);
  [[-.8, 0], [.8, 0]].forEach(([x, z]) => { add(RB(.36, .06, .36, .02), M(0x8A6A4A), x, .42, z, table); add(RB(.36, .4, .06, .02), M(0x8A6A4A), x + Math.sign(x) * .17, .62, z, table).rotation.y = Math.PI / 2; });
  const plates = [[-.3, .05], [.3, -.05]].map(([x, z]) => { const p = new THREE.Group(); p.position.set(x, .66, z); table.add(p); add(new THREE.CylinderGeometry(.2, .16, .03, 24), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: .2 }), 0, 0, 0, p); const food = new THREE.Group(); p.add(food); [[0, 0], [.07, .05], [-.06, .06]].forEach(([fx, fz]) => add(new THREE.SphereGeometry(.06, 10, 8), tom, fx, .05, fz, food)); add(new THREE.SphereGeometry(.05, 8, 6), leaf, .02, .06, -.07, food); return food; });
  // ---- road ----
  const roadMat = M(0x3B3A3F), lineMat = M(0xF4D35E);
  const RP = [[-.6, -3.1], [-.6, -.2], [3.4, -.2], [3.4, 2.6], [1.6, 2.6]];
  const segL = []; let totL = 0;
  for (let i = 1; i < RP.length; i++) {
    const [x0, z0] = RP[i - 1], [x1, z1] = RP[i], len = Math.hypot(x1 - x0, z1 - z0); segL.push(len); totL += len;
    const seg = add(new THREE.BoxGeometry(x0 === x1 ? .9 : len + .9, .04, z0 === z1 ? .9 : len + .9), roadMat, (x0 + x1) / 2, .02, (z0 + z1) / 2, world); seg.castShadow = false;
    const n = Math.floor(len / .5);
    for (let j = 1; j < n; j++) { const u = j / n; add(new THREE.BoxGeometry(x0 === x1 ? .06 : .22, .01, z0 === z1 ? .06 : .22), lineMat, L(x0, x1, u), .045, L(z0, z1, u), world).castShadow = false; }
  }
  const STOP = [0, (segL[0]) / totL + .0, (segL[0] + segL[1] + segL[2] + segL[3]) / totL];
  STOP[1] = (segL[0] + segL[1] * .97) / totL; // in front of the plant
  const along = k => { let d = k * totL; for (let i = 0; i < segL.length; i++) { if (d <= segL[i] || i === segL.length - 1) { const u = C(d / segL[i]); const [x0, z0] = RP[i], [x1, z1] = RP[i + 1]; return [L(x0, x1, u), L(z0, z1, u), Math.atan2(x1 - x0, z1 - z0)]; } d -= segL[i]; } };
  // ---- truck ----
  const truck = new THREE.Group(); world.add(truck);
  const tb = new THREE.Group(); truck.add(tb);
  add(RB(.62, .5, .55, .06), M(0xF4D35E), 0, .38, .5, tb);
  add(new THREE.BoxGeometry(.5, .2, .04), new THREE.MeshStandardMaterial({ color: 0x223344, roughness: .1, metalness: .3 }), 0, .5, .78, tb);
  add(RB(.66, .14, .95, .03), M(0x5B6770), 0, .22, -.25, tb);
  [[-.3, .45], [.3, .45], [-.3, -.45], [.3, -.45]].forEach(([x, z]) => { const w = add(new THREE.CylinderGeometry(.13, .13, .1, 16), M(0x1E1E1E), x, .13, z, tb); w.rotation.z = Math.PI / 2; });
  const loadTom = new THREE.Group(), loadBox = new THREE.Group(); tb.add(loadTom); tb.add(loadBox);
  for (let i = 0; i < 9; i++) add(new THREE.SphereGeometry(.1, 10, 8), tom, -.18 + (i % 3) * .18, .36, -.55 + Math.floor(i / 3) * .25, loadTom);
  for (let i = 0; i < 4; i++) add(RB(.26, .24, .3, .02), crateMat, -.14 + (i % 2) * .28, .41, -.45 + Math.floor(i / 2) * .36, loadBox);
  // ---- trees ----
  const trunk = M(0x6E4B2A), canopy = M(0x2E8B57), canopy2 = M(0x3FA66A);
  [[-5.2, 1.2], [-4.6, 3.2], [-5.3, 5.0], [-3.2, 5.2], [-1.6, 5.3], [5.2, 5.1], [5.3, 3.4], [5.2, .7], [-2.6, 1.6], [-4.0, -.4], [1.6, 5.4], [5.4, -4.8]].forEach(([x, z], i) => {
    const g = new THREE.Group(); g.position.set(x, 0, z); world.add(g);
    add(new THREE.CylinderGeometry(.08, .1, .5, 8), trunk, 0, .25, 0, g);
    add(new THREE.IcosahedronGeometry(.42, 1), i % 2 ? canopy : canopy2, 0, .8, 0, g);
  });
  // ---- active-stage highlight rings ----
  const rings = [[-2.4, -3.3, 3.4], [3.4, -2.0, 2.4], [.6, 3.9, 2.4]].map(([x, z, r]) => {
    const m = new THREE.Mesh(new THREE.RingGeometry(r - .14, r, 64), new THREE.MeshBasicMaterial({ color: 0x2E8B57, transparent: true, opacity: 0, depthWrite: false }));
    m.rotation.x = -Math.PI / 2; m.position.set(x, .07, z); world.add(m); return m;
  });
  const anchors = [new THREE.Vector3(-2.6, 2.4, -4.6), new THREE.Vector3(3.4, 2.6, -2.4), new THREE.Vector3(.6, 2.6, 3.4)];
  const stages = [st1, st2, st3];

  // ---- lights ----
  scene.add(new THREE.HemisphereLight(0xFFF6E5, 0x6B8F5A, .9));
  const sun = new THREE.DirectionalLight(0xFFF1DA, 2.4); sun.position.set(-6, 12, 5); sun.castShadow = true;
  Object.assign(sun.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 40 }); sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 5; sun.shadow.blurSamples = 16; sun.shadow.bias = -.0005;
  scene.add(sun);

  const isoDir = new THREE.Vector3(1, .82, 1).normalize();
  const VIEW = { c: new THREE.Vector3(0, -.2, 0), z: 1 };
  const FOCUS = [new THREE.Vector3(-2.0, 0, -3.2), new THREE.Vector3(2.6, 0, -1.4), new THREE.Vector3(1.2, 0, 2.8)];
  const proj = new THREE.Vector3();
  let metaNow = {};
  const fn = lt => {
    // which step is active and how strongly
    const act = FARM_STEPS.map(s => C(P(lt, s.a, s.a + .15)) * (1 - C(P(lt, s.b - .05, s.b + .1))));
    // camera framing: overview, then gently follow the active step
    const fc = new THREE.Vector3().copy(VIEW.c); let zoom = 1;
    act.forEach((a, i) => { fc.lerp(FOCUS[i], a * .45); zoom += a * .16; });
    const halfW = 12.2 / zoom, halfH = halfW * H / W;
    Object.assign(cam, { left: -halfW, right: halfW, top: halfH * .94, bottom: -halfH * 1.06 });
    cam.position.copy(fc).addScaledVector(isoDir, 40); cam.lookAt(fc); cam.updateProjectionMatrix();
    // build-up
    const gk = eback(P(lt, 0, .45), 1.1); world.scale.setScalar(Math.max(.001, L(.6, 1, C(gk)))); world.position.y = (1 - C(gk)) * -1.5;
    stages.forEach((s, i) => { const k = eback(P(lt, .1 + i * .08, .45 + i * .08), 2); s.position.y = (1 - C(k)) * 3; s.scale.setScalar(Math.max(.001, k)); });
    // emphasise the active stage (a small lift) and its ring
    stages.forEach((s, i) => { s.position.y += Math.sin(Math.PI * C(P(lt, FARM_STEPS[i].a, FARM_STEPS[i].a + .3))) * .25; });
    rings.forEach((r, i) => { r.material.opacity = act[i] * (.65 + .25 * Math.sin(lt * 9)); r.scale.setScalar(1 + .04 * Math.sin(lt * 9)); });
    // story: harvest -> tomatoes loaded -> boxes -> plates filled
    const harvest = P(lt, .6, 1.0);
    crops.forEach((c, i) => { const q = C(harvest * 1.6 - (i % 7) * .09); c.tm.scale.setScalar(Math.max(.001, 1 - q)); });
    const pack = P(lt, 1.42, 1.58);
    loadTom.visible = harvest > .3 && pack < .5; loadTom.scale.setScalar(Math.max(.001, C((harvest - .3) * 3) * (1 - C(pack * 2))));
    loadBox.visible = pack >= .5; loadBox.scale.setScalar(Math.max(.001, eback(C((pack - .5) * 2), 2)));
    const serve = eback(P(lt, 2.15, 2.4), 2);
    loadBox.visible = loadBox.visible && lt < 2.12;
    plates.forEach(f => f.scale.setScalar(Math.max(.001, serve)));
    // truck route with stops
    let k = 0;
    if (lt < 1.2) k = 0; else if (lt < 1.42) k = L(0, STOP[1], eio(P(lt, 1.2, 1.42)));
    else if (lt < 1.82) k = STOP[1]; else k = L(STOP[1], STOP[2], eio(P(lt, 1.82, 2.12)));
    const [tx, tz, ang] = along(k);
    truck.position.set(tx, .04, tz); truck.rotation.y = ang;
    truck.scale.setScalar(Math.max(.001, eback(P(lt, .35, .6), 2)));
    renderer.render(scene, cam);
    // label anchors in poster pixels
    metaNow = { act, pts: anchors.map(a => { proj.copy(a).applyMatrix4(world.matrixWorld); proj.project(cam); return [(proj.x + 1) / 2 * W, (1 - proj.y) / 2 * H]; }) };
  };
  fn.canvas = renderer.domElement; fn.meta = () => metaNow;
  return cached(fn, 2.6);
}

let laptopR = null, farmR = null;
export const laptop3D = lt => (laptopR ||= buildLaptop())(lt);
export const farm3D = lt => (farmR ||= buildFarm())(lt);
