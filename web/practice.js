'use strict';
sandSpeed = 1.5;
let aiTimer;
updateUI = function () {
  clearTimeout(aiTimer);
  const ai = state?.mode === 'ai';
  document.body.classList.toggle('is-paused', paused);
  document.body.classList.toggle('is-practice-ai', ai);
  $('practice-player').textContent = ai ? 'AI demonstration' : 'You · Practice';
  $('status').textContent = message || state?.error || (paused ? 'Paused' : '');
  $('status').hidden = !$('status').textContent;
  for (const id of ['left', 'right', 'rotate', 'down', 'drop']) $(id).disabled = !controllable();
  for (const id of ['seed', 'restart', 'new', 'piece-limit', 'ai-mode', 'play-again']) $(id).disabled = busy;
  $('pause').disabled = !state || !!state.result;
  $('pause').textContent = paused ? 'Resume' : 'Pause';
  $('practice-help').textContent = ai ? 'The AI plays at its own pace. Pause to take a closer look.' : 'Arrow keys or WASD: move, rotate, soft drop · Space: drop · P: pause';
  if (!state) return;
  const s = state.boards.human.stats;
  const items = [['Pieces', `${s.steps}/${state.limit}`], ['Clears', s.clears], ['Grains', s.grains.toLocaleString()], ['Clear %', `${s.clear_percentage.toFixed(1)}%`]];
  if (ai) items.push(['Last move', state.turn ? `${state.last_think_ms.toFixed(1)} ms` : '—'], ['Avg move', state.turn ? `${state.average_think_ms.toFixed(1)} ms` : '—']);
  $('human-stats').innerHTML = items.map(([label, value]) => `<span>${label}<b>${value}</b></span>`).join('');
  $('match-progress').max = state.limit;
  $('match-progress').value = state.turn;
  $('match-progress').setAttribute('aria-label', `${state.turn} of ${state.limit} pieces played`);
  $('result').hidden = !state.result;
  $('result-title').textContent = state.result || '';
  if (ai && !busy && !paused && !state.result && !state.error && !message) aiTimer = setTimeout(playAI, 0);
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
  $('ai-mode').textContent = ai ? 'AI mode: on' : 'AI mode: off';
  newMatch();
};
$('piece-limit').onchange = () => newMatch();
$('play-again').onclick = () => newMatch(true);
updateUI();
