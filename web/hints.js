/* Practice-only landing heatmap; no game state or policy is changed. */
(() => {
  'use strict';
  if (typeof practice === 'undefined' || !practice) return;
  const mode = document.getElementById('ai-mode');
  const button = document.createElement('button');
  button.id = 'polish-ai-hints';
  button.type = 'button';
  button.textContent = 'AI hints';
  button.setAttribute('aria-pressed', 'false');
  button.title = 'Combined scores across all four rotations, anchored to the pile surface. Trained evaluator, before lookahead.';
  mode.before(button);
  const modeButtons = document.createElement('div');
  modeButtons.className = 'polish-mode-buttons';
  button.before(modeButtons);
  modeButtons.append(button, mode);
  const canvas = document.createElement('canvas');
  canvas.width = 340; canvas.height = 600;
  canvas.className = 'polish-hints-canvas';
  canvas.setAttribute('aria-hidden', 'true');
  const board = document.getElementById('human-board');
  board.parentElement.append(canvas);
  const ctx = canvas.getContext('2d');
  const field = document.createElement('canvas');
  field.width = 340; field.height = 600;
  const fieldCtx = field.getContext('2d');
  const glow = document.createElement('canvas');
  glow.width = 340; glow.height = 600;
  const glowCtx = glow.getContext('2d');
  let maskedWorld = null, grainMask = null;
  const colorProbe = document.createElement('span');
  colorProbe.className = 'polish-hint-color';
  colorProbe.setAttribute('aria-hidden', 'true');
  board.parentElement.append(colorProbe);
  let enabled = false, data = null, requested = '', controller = null;
  let painted = '', lastColorCheck = 0, color = [170, 160, 230], retryAt = 0;
  let seenKey = '';
  function key() {
    return state && !state.result ? `${state.id}:${state.turn}` : '';
  }
  function eligible() {
    return enabled && state && !state.result && !document.hidden && (state.mode === 'human' || paused);
  }
  function align() { canvas.style.top = `${board.offsetTop}px`; }
  new ResizeObserver(align).observe(board);
  align();
  function clear() { ctx.clearRect(0, 0, 340, 600); painted = ''; }
  function showBehindPieces() {
    ctx.clearRect(0, 0, 340, 600);
    ctx.drawImage(glow, 0, 0);
    if (state?.mode === 'human' && piece && !state.result) {
      for (const [bx, by] of shapeAt(state.piece.shape, piece.rotation)) {
        ctx.clearRect((piece.x + bx * 5) * 4, (piece.y + by * 5) * 4, 20, 20);
      }
    }
  }
  button.onclick = () => {
    enabled = !enabled;
    button.setAttribute('aria-pressed', String(enabled));
    if (!enabled) {
      controller?.abort(); controller = null; requested = ''; data = null; clear();
    }
    document.getElementById('human-board').focus({preventScroll:true});
  };
  async function requestHints(current) {
    requested = current;
    controller?.abort();
    const request = new AbortController(); controller = request;
    const id = state.id, turn = state.turn;
    try {
      const response = await fetch(`/api/practice/hints?id=${encodeURIComponent(id)}&turn=${turn}`, {signal:request.signal});
      const next = await response.json();
      if (!eligible() || request.signal.aborted || current !== key()) return;
      if (!response.ok) throw new Error(next.error || 'Hints unavailable');
      data = next;
      painted = '';
    } catch (error) {
      if (request.signal.aborted || current !== key() || !eligible()) return;
      requested = ''; retryAt = performance.now() + 1500;
    }
  }
  function paint(now) {
    const current = key();
    if (current !== seenKey) { seenKey = current; retryAt = 0; }
    if (!eligible() || !current) {
      controller?.abort(); controller = null; requested = ''; data = null;
      if (painted) clear();
      return;
    }
    if (requested !== current && now >= retryAt) {
      data = null; clear();
      requestHints(current);
    }
    if (!data || `${data.id}:${data.turn}` !== current || (animation && state.mode === 'human' && !paused)) {
      if (painted) clear();
      return;
    }
    if (now - lastColorCheck > 120) {
      lastColorCheck = now;
      const rgb = getComputedStyle(colorProbe).color.match(/[\d.]+/g);
      if (rgb) color = rgb.slice(0, 3).map(Number);
    }
    const signature = `${current}:${color.join(',')}`;
    if (signature === painted) { showBehindPieces(); return; }
    clear();
    const pixels = ctx.createImageData(340, 600);
    const low = Math.min(...color), high = Math.max(...color);
    const vivid = color.map(c => high > low ? 30 + (c - low) * 185 / (high - low) : c);
    const luminance = (vivid[0] * .2126 + vivid[1] * .7152 + vivid[2] * .0722) / 255;
    const brightnessCompensation = .28 * Math.max(0, Math.min(1, (luminance - .28) / .5));
    // Nearby comparable choices form one continuous region, not one dot per
    // candidate. Limit the whole group's score range to avoid bridging a
    // gradual chain from a weak choice all the way to a strong one.
    const regions = [];
    for (const p of [...data.placements].sort((a,b) => a.x - b.x)) {
      const previous = regions.at(-1);
      if (previous && p.x <= previous.lastX + 5 &&
          Math.max(previous.high, p.strength) - Math.min(previous.low, p.strength) <= .16) {
        previous.right = Math.min(340, (p.x + 5) * 4);
        previous.lastX = p.x;
        previous.low = Math.min(previous.low, p.strength);
        previous.high = Math.max(previous.high, p.strength);
        previous.sum += p.strength;
        previous.count++;
      } else {
        regions.push({left:p.x * 4, right:Math.min(340, (p.x + 5) * 4), lastX:p.x,
          low:p.strength, high:p.strength, sum:p.strength, count:1});
      }
    }
    for (let x = 0; x < 340; x++) {
      let bright = 0, faint = 0;
      for (const region of regions) {
        const t = region.sum / region.count;
        const priority = Math.pow(Math.max(0, (t - .65) / .35), 2.4);
        const distance = Math.max(region.left - x, x - region.right, 0);
        const spread = (15 + 27 * priority) * (1 - brightnessCompensation * priority);
        bright = Math.max(bright, priority * Math.exp(-distance * distance / (2 * spread * spread)));
        faint = Math.max(faint, .04 * t * t * Math.exp(-distance * distance / 200));
      }
      const intensity = Math.min(.96, .94 * bright + faint);
      if (intensity < .004) continue;
      const saturation = Math.min(1, Math.pow(bright, .65) * 1.15);
      const rgb = vivid.map(c => Math.round(65 + (c - 65) * saturation));
      const grainX = Math.min(84, Math.floor(x / 4));
      const nextX = Math.min(84, grainX + 1);
      const fraction = (x % 4) / 4;
      const surface = ((1 - fraction) * data.surface[grainX] + fraction * data.surface[nextX]) * 4;
      const centerY = Math.min(599, surface + 1);
      const reach = (15 + 19 * bright) * (1 - brightnessCompensation * bright);
      for (let y = Math.max(0, Math.floor(centerY - reach * 3)); y < Math.min(600, centerY + 14); y++) {
        const dy = y - centerY;
        const sigma = dy < 0 ? reach : 4;
        const alpha = intensity * Math.exp(-dy * dy / (2 * sigma * sigma));
        const offset = (y * 340 + x) * 4;
        pixels.data[offset] = rgb[0]; pixels.data[offset + 1] = rgb[1]; pixels.data[offset + 2] = rgb[2];
        pixels.data[offset + 3] = Math.round(255 * alpha);
      }
    }
    fieldCtx.putImageData(pixels, 0, 0);
    glowCtx.clearRect(0, 0, 340, 600);
    glowCtx.filter = 'blur(6px)';
    glowCtx.drawImage(field, 0, 0);
    glowCtx.filter = 'none';
    // Mask after smoothing so no light bleeds back over any occupied grain.
    const world = state.boards.human.world;
    if (maskedWorld !== world) {
      maskedWorld = world;
      grainMask = new Path2D();
      for (let y = 0; y < 150; y++) {
        let start = -1;
        for (let x = 0; x <= 85; x++) {
          const occupied = x < 85 && world[y][x] !== 0;
          if (occupied && start < 0) start = x;
          if (!occupied && start >= 0) {
            grainMask.rect(start * 4, y * 4, (x - start) * 4, 4);
            start = -1;
          }
        }
      }
    }
    glowCtx.globalCompositeOperation = 'destination-out';
    glowCtx.fill(grainMask);
    glowCtx.globalCompositeOperation = 'source-over';
    showBehindPieces();
    painted = signature;
  }
  const originalDraw = draw;
  draw = function () {
    // Paused inspection uses the settled board. Running AI playback is unchanged.
    const playback = animation;
    if (eligible() && paused) animation = null;
    originalDraw();
    animation = playback;
    paint(performance.now());
  };
})();
