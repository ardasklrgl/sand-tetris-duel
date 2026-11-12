'use strict';
sandSpeed = 1.5;
let aiTimer;
let practiceModeRequested = false;
function formatMoveTime(ms) {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}
updateUI = function () {
  clearTimeout(aiTimer);
  if (practiceModeRequested && !busy) {
    practiceModeRequested = false;
    switchPracticeMode();
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
  if (ai) items.push(['Last move', state.ai_moves ? formatMoveTime(state.last_think_ms) : '—'], ['Avg move', state.ai_moves ? formatMoveTime(state.average_think_ms) : '—']);
  $('human-stats').innerHTML = items.map(([label, value]) => `<span>${label}<b>${value}</b></span>`).join('');
  $('match-progress').max = state.limit;
  $('match-progress').value = state.turn;
  $('match-progress').setAttribute('aria-label', `${state.turn} of ${state.limit} pieces played`);
  $('result').hidden = !state.result;
  $('result-title').textContent = state.result || '';
  if (ai && !busy && !paused && !state.result && !state.error && !message && !practiceModeRequested) aiTimer = setTimeout(playAI, 0);
};
async function switchPracticeMode() {
  busy = true;
  clearHeld();
  updateUI();
  try {
    state = await api('/api/practice/mode', {id: state.id,
      mode: $('ai-mode').getAttribute('aria-pressed') === 'true' ? 'ai' : 'human'});
    if (state.mode === 'human') spawn();
    message = '';
  } catch (error) {
    message = error.message;
    $('ai-mode').setAttribute('aria-pressed', String(state.mode === 'ai'));
    $('ai-mode').textContent = state.mode === 'ai' ? 'Practice mode' : 'AI mode';
  } finally {
    busy = false;
    updateUI();
  }
}
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
  practiceModeRequested = true;
  clearHeld();
  updateUI();
};
$('piece-limit').onchange = () => newMatch();
$('play-again').onclick = () => newMatch(true);
updateUI();
