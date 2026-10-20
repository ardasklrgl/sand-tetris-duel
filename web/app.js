'use strict';
const $ = id => document.getElementById(id);
const W = 85, H = 150, SCALE = 4;
const COLORS = ['#000', 'rgb(200,100,100)', 'rgb(100,100,200)', 'rgb(100,200,100)', 'rgb(200,200,100)'];
let state = null, piece = null, busy = false, pendingDrop = false, paused = false;
let pollTimer, epoch = 0, message = '', animation = null;
let gravityTimer = 0, moveTimer = 0, lastTime = 0;
let sandSpeed = 1, instantSettle = false;
const held = new Set();

function saveSandSettings() {
  try { localStorage.setItem('sandtris-settling', JSON.stringify({speed: sandSpeed, instant: instantSettle})); } catch (_) {}
}

function loadSandSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem('sandtris-settling'));
    if (typeof saved?.speed === 'number' && Number.isFinite(saved.speed)) sandSpeed = Math.max(0.1, Math.min(20, saved.speed));
    instantSettle = saved?.instant === true || (saved == null && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  } catch (_) {}
  $('sand-speed').value = sandSpeed;
  $('instant').checked = instantSettle;
  $('sand-speed').disabled = instantSettle;
}

async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed.');
  return result;
}

function shapeAt(shape, rotation) {
  let points = shape.map(p => [...p]);
  for (let i = 0; i < rotation; i++) points = points.map(([x, y]) => [y, -x]);
  const minX = Math.min(...points.map(p => p[0]));
  const minY = Math.min(...points.map(p => p[1]));
  return points.map(([x, y]) => [x - minX, y - minY]);
}

function overlaps(world, x, y, rotation) {
  const shape = shapeAt(state.piece.shape, rotation);
  const rows = Array.isArray(world[0]);
  for (const [bx, by] of shape) {
    for (let gy = 0; gy < 5; gy++) for (let gx = 0; gx < 5; gx++) {
      const xx = x + bx * 5 + gx, yy = y + by * 5 + gy;
      if (xx < 0 || xx >= W || yy < 0 || yy >= H || (rows ? world[yy][xx] : world[yy * W + xx])) return true;
    }
  }
  return false;
}

function fits(x, y, rotation = piece.rotation) {
  const settled = state.boards.human.world;
  const blocked = overlaps(settled, x, y, rotation);
  if (animation) {
    // The server has already finished physics. Show its final board before the
    // falling piece reaches sand that is still moving in the visual playback.
    const frames = animation.frames.human;
    const frame = frames[Math.min(animation.index, frames.length - 1)];
    if (blocked || (frame && overlaps(frame, x, y, rotation))) animation = null;
  }
  return !blocked;
}

function spawn() {
  piece = {x: Math.floor(W / 2) - 5, y: 0, rotation: 0};
  gravityTimer = 0;
  moveTimer = 0;
  pendingDrop = false;
}

function controllable() {
  return state && piece && !state.result && !state.error && !busy && !pendingDrop && !paused;
}

function move(dx, dy) {
  if (!controllable()) return false;
  if (fits(piece.x + dx, piece.y + dy)) {
    piece.x += dx;
    piece.y += dy;
    return true;
  }
  return false;
}

function rotate() {
  if (!controllable()) return;
  const rotation = (piece.rotation + 1) % 4;
  // Exact wall-kick offsets from sandtris.py.
  for (const kick of [0, -1, 1, -2, 2, -3, 3]) {
    if (fits(piece.x + kick * 5, piece.y, rotation)) {
      piece.x += kick * 5;
      piece.rotation = rotation;
      break;
    }
  }
}

function drawWorld(ctx, world) {
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const color = world[y][x];
    if (color) { ctx.fillStyle = COLORS[color]; ctx.fillRect(x * SCALE, y * SCALE, SCALE, SCALE); }
  }
}

function drawFrame(ctx, data) {
  for (let i = 0; i < data.length; i++) {
    if (data[i]) {
      ctx.fillStyle = COLORS[data[i]];
      ctx.fillRect((i % W) * SCALE, Math.floor(i / W) * SCALE, SCALE, SCALE);
    }
  }
}

function draw() {
  for (const name of ['ai', 'human']) {
    const ctx = $(name + '-board').getContext('2d');
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, 340, 600);
    if (!state) continue;
    if (animation && animation.frames[name].length) {
      const frames = animation.frames[name];
      drawFrame(ctx, frames[Math.min(animation.index, frames.length - 1)]);
    } else {
      drawWorld(ctx, state.boards[name].world);
    }
    if (name === 'human' && !state.result && piece) {
      ctx.fillStyle = COLORS[state.piece.color];
      for (const [bx, by] of shapeAt(state.piece.shape, piece.rotation)) {
        ctx.fillRect((piece.x + bx * 5) * SCALE, (piece.y + by * 5) * SCALE, 20, 20);
      }
    }
    if (state.result) {
      ctx.fillStyle = '#000a'; ctx.fillRect(0, 0, 340, 600);
      ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.font = '20px Arial';
      ctx.fillText(state.result, 170, 285);
    }
  }
}

function updateUI() {
  if (!state) { $('status').textContent = message || 'Loading…'; return; }
  for (const name of ['ai', 'human']) {
    const s = state.boards[name].stats;
    const stats = [['Steps', s.steps], ['Clears', s.clears], ['Clear %', s.clear_percentage.toFixed(1) + '%'],
      ['Grains cleared', s.grains.toLocaleString()], ['Clear turns', s.clear_turn_percentage.toFixed(1) + '%'], ['Height', s.height + '/150']];
    $(name + '-stats').innerHTML = stats.map(([label, value]) => `<span>${label}<b>${value}</b></span>`).join('');
  }
  $('status').textContent = message || state.error || state.result || (busy ? 'Placing both pieces…' : paused ? 'Paused' : pendingDrop ? 'Waiting for AI…' : `Turn ${state.turn + 1}`);
  for (const id of ['left', 'right', 'rotate', 'down', 'drop']) $(id).disabled = !controllable();
  for (const id of ['seed', 'restart', 'new']) $(id).disabled = busy;
  $('pause').disabled = busy || !!state.result;
  $('pause').textContent = paused ? 'Resume' : 'Pause';
}

function schedulePoll() {
  clearTimeout(pollTimer);
  if (!state || state.ready || state.result || state.error) return;
  const generation = epoch, id = state.id;
  pollTimer = setTimeout(async () => {
    try {
      const fresh = await api('/api/state?id=' + encodeURIComponent(id));
      if (generation !== epoch || busy) return;
      state = fresh;
      updateUI();
      if (pendingDrop && state.ready) commitDrop(); else schedulePoll();
    } catch (error) {
      if (generation === epoch) { message = error.message; paused = true; updateUI(); }
    }
  }, 150);
}

async function newMatch(random = false) {
  if (busy) return;
  const raw = $('seed').value;
  const seed = random || raw === '' ? null : Number(raw);
  if (seed !== null && (!Number.isInteger(seed) || seed < 0 || seed >= 2 ** 32)) {
    message = 'Seed must be a whole number from 0 to 4294967295.'; updateUI(); return;
  }
  epoch++; clearTimeout(pollTimer); held.clear(); animation = null; busy = true; message = 'Loading…'; updateUI();
  for (const id of ['seed', 'restart', 'new']) $(id).disabled = true;
  try {
    state = await api('/api/new', {seed, previous_id: state?.id});
    $('seed').value = state.seed;
    const url = new URL(location.href); url.searchParams.set('seed', state.seed); history.replaceState(null, '', url);
    paused = false; message = ''; spawn(); $('human-board').focus({preventScroll: true});
  } catch (error) { message = error.message; paused = true; }
  finally {
    busy = false; updateUI(); schedulePoll();
    for (const id of ['seed', 'restart', 'new']) $(id).disabled = false;
  }
}

function requestDrop() {
  if (!controllable()) return;
  // A new drop starts from the board the server has fully simulated. It can
  // supersede slow playback from the previous turn without delaying input.
  animation = null;
  while (fits(piece.x, piece.y + 1)) piece.y++;
  pendingDrop = true;
  held.clear();
  updateUI();
  if (state.ready) commitDrop();
}

function startSandAnimation(next) {
  // Physics has already been fully simulated on the server. Instant mode
  // displays that same final state without decoding or playing intermediate frames.
  animation = null;
  if (instantSettle) return;
  const frames = {};
  for (const name of ['ai', 'human']) {
    frames[name] = next.frames[name].map(encoded => Uint8Array.from(atob(encoded), c => c.charCodeAt(0)));
  }
  const count = Math.max(frames.ai.length, frames.human.length);
  // Playback is visual. The next human piece is usable at once.
  if (count) animation = {frames, index: 0, count, ticks: 0, lastTime: performance.now()};
}

async function commitDrop() {
  if (busy || !state || !state.ready || !pendingDrop || state.result) return;
  busy = true; message = ''; clearTimeout(pollTimer); updateUI();
  try {
    const next = await api('/api/move', {id: state.id, turn: state.turn, placement: {...piece}});
    startSandAnimation(next);
    state = next;
    delete state.frames;
    spawn();
  } catch (error) {
    message = error.message; paused = true;
    try {
      const fresh = await api('/api/state?id=' + encodeURIComponent(state.id));
      if (fresh.turn !== state.turn) spawn();
      state = fresh;
    } catch (_) {}
    pendingDrop = false;
  } finally { busy = false; updateUI(); schedulePoll(); }
}

function togglePause() {
  if (busy || !state || state.result) return;
  paused = !paused; held.clear(); gravityTimer = 0; updateUI();
}

function frame(now) {
  const dt = Math.min(40, now - (lastTime || now));
  lastTime = now;
  if (animation) {
    const elapsed = Math.max(0, now - animation.lastTime);
    animation.lastTime = Math.max(now, animation.lastTime);
    animation.ticks += elapsed * sandSpeed / (1000 / 60);
    animation.index = instantSettle ? animation.count - 1 : Math.min(animation.count - 1, Math.floor(animation.ticks));
    if (instantSettle || animation.ticks >= animation.count) {
      animation = null;
    }
  }
  if (controllable() && !document.hidden) {
    moveTimer += dt;
    if (moveTimer >= 1000 / 60) {
      if (held.has('left')) move(-1, 0);
      if (held.has('right')) move(1, 0);
      if (held.has('down')) move(0, 1);
      moveTimer %= 1000 / 60;
    }
    gravityTimer += dt;
    if (gravityTimer >= 30) {
      gravityTimer -= 30;
      if (!move(0, 1)) requestDrop();
    }
  }
  draw();
  requestAnimationFrame(frame);
}

const keyActions = {ArrowLeft: 'left', a: 'left', A: 'left', ArrowRight: 'right', d: 'right', D: 'right', ArrowDown: 'down', s: 'down', S: 'down'};
document.addEventListener('keydown', event => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLButtonElement) return;
  const action = keyActions[event.key];
  if (action || ['ArrowUp', 'w', 'W', ' ', 'p', 'P'].includes(event.key)) event.preventDefault();
  if (event.repeat) return;
  if (action) held.add(action);
  if (['ArrowUp', 'w', 'W'].includes(event.key)) rotate();
  if (event.key === ' ') requestDrop();
  if (['p', 'P'].includes(event.key)) togglePause();
});
document.addEventListener('keyup', event => held.delete(keyActions[event.key]));
window.addEventListener('blur', () => { held.clear(); if (state && !busy && !state.result) { paused = true; updateUI(); } });
document.addEventListener('visibilitychange', () => { held.clear(); gravityTimer = 0; });
for (const [id, dx, dy] of [['left', -1, 0], ['right', 1, 0], ['down', 0, 1]]) {
  $(id).addEventListener('pointerdown', event => { event.preventDefault(); move(dx, dy); held.add(id); $(id).setPointerCapture(event.pointerId); });
  $(id).addEventListener('pointerup', () => { held.delete(id); $('human-board').focus({preventScroll: true}); });
  $(id).addEventListener('pointercancel', () => held.delete(id));
  $(id).onclick = event => { if (event.detail === 0) move(dx, dy); };
}
$('rotate').onclick = () => { rotate(); $('human-board').focus({preventScroll: true}); };
$('drop').onclick = () => { requestDrop(); $('human-board').focus({preventScroll: true}); };
$('pause').onclick = () => { togglePause(); $('human-board').focus({preventScroll: true}); };
$('restart').onclick = () => newMatch(); $('new').onclick = () => newMatch(true);
$('sand-speed').addEventListener('change', () => {
  const speed = Number($('sand-speed').value);
  if (Number.isFinite(speed) && speed > 0) sandSpeed = Math.max(0.1, Math.min(20, speed));
  $('sand-speed').value = sandSpeed;
  saveSandSettings();
});
$('instant').addEventListener('change', () => {
  instantSettle = $('instant').checked;
  $('sand-speed').disabled = instantSettle;
  saveSandSettings();
});
loadSandSettings();
const urlSeed = new URL(location.href).searchParams.get('seed');
if (urlSeed !== null && /^\d+$/.test(urlSeed) && Number(urlSeed) < 2 ** 32) $('seed').value = urlSeed;
requestAnimationFrame(frame);
newMatch();
