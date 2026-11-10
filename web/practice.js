'use strict';
sandSpeed = 1.5;
let aiTimer;
let practiceRestartRequested = false;
function formatMoveTime(ms) {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}
updateUI = function () {
  clearTimeout(aiTimer);
  if (practiceRestartRequested && !busy) {
    practiceRestartRequested = false;
    newMatch();
    return;
  }
  const ai = state?.mode === 'ai';
  document.body.classList.toggle('is-paused', paused);
  document.body.classList.toggle('is-practice-ai', ai);
  $('practice-player').textContent = ai ? 'AI' : 'You';
  $('status').textContent = message || state?.error || '';
  $('status').hidden = !$('status').textContent;
  for (const id of ['left', 'right', 'rotate', 'down', 'drop']) $(id).disabled = !controllable();
  for (const id of ['seed', 'restart', 'new', 'piece-limit', 'play-again']) $(id).disabled = busy;
  $('ai-mode').disabled = !state;
  $('pause').disabled = !state || !!state.result;
  $('pause').textContent = paused ? 'Resume' : 'Pause';
  $('practice-help').textContent = ai ? 'The AI plays at its own pace. Pause to take a closer look.' : 'Arrow keys or WASD: move, rotate, soft drop · Space: drop · P: pause';
  if (!state) return;
  const s = state.boards.human.stats;
  const items = [['Pieces', `${s.steps}/${state.limit}`], ['Clears', s.clears], ['Grains', s.grains.toLocaleString()], ['Clear %', `${s.clear_percentage.toFixed(1)}%`]];
  if (ai) items.push(['Last move', state.turn ? formatMoveTime(state.last_think_ms) : '—'], ['Avg move', state.turn ? formatMoveTime(state.average_think_ms) : '—']);
  $('human-stats').innerHTML = items.map(([label, value]) => `<span>${label}<b>${value}</b></span>`).join('');
  $('match-progress').max = state.limit;
  $('match-progress').value = state.turn;
  $('match-progress').setAttribute('aria-label', `${state.turn} of ${state.limit} pieces played`);
  $('result').hidden = !state.result;
  $('result-title').textContent = state.result || '';
  if (ai && !busy && !paused && !state.result && !state.error && !message && !practiceRestartRequested) aiTimer = setTimeout(playAI, 0);
};
async function playAI() {
  if (!state || busy || paused || state.result || state.mode !== 'ai') return;
  busy = true;
  updateUI();
  try {
    const next = await api('/api/practice/move', {id: state.id, turn: state.turn});
    startSandAnimation(next);
    state = next;
    delete state.frames;
  } catch (error) {
    message = error.message;
    paused = true;
  } finally {
    busy = false;
    updateUI();
  }
}
$('ai-mode').onclick = () => {
  const ai = $('ai-mode').getAttribute('aria-pressed') !== 'true';
  $('ai-mode').setAttribute('aria-pressed', String(ai));
  $('ai-mode').textContent = ai ? 'Practice mode' : 'AI mode';
  practiceRestartRequested = true;
  clearHeld();
  updateUI();
};
$('piece-limit').onchange = () => newMatch();
$('play-again').onclick = () => newMatch(true);
updateUI();
