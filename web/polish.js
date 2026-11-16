/* Shared game presentation, Practice metrics and accessible finish controls. */
(() => {
  'use strict';
  document.body.classList.add('is-polished');
  const stage = document.querySelector('.duel-stage');
  if (!stage || typeof updateUI !== 'function') return;

  document.querySelectorAll('.board-frame').forEach(frame => {
    const overlay = document.createElement('div');
    overlay.className = 'polish-paused';
    overlay.innerHTML = '<button type="button" class="polish-resume" aria-label="Resume game">Paused</button>';
    overlay.querySelector('button').disabled = true;
    overlay.querySelector('button').onclick = () => {
      if (paused && !state?.result) togglePause();
      document.getElementById('human-board').focus({preventScroll:true});
    };
    frame.append(overlay);
  });

  const soloPractice = typeof practice !== 'undefined' && practice;
  let history = null, activeMoveMs = 0, clockAt = performance.now(), clockRunning = false;
  function metrics(snapshot) {
    if (history?.id !== snapshot.id) {
      history = {id:snapshot.id, moves:0, lastTurn:snapshot.turn, grainSum:0, heightSum:0, timeSum:0, lastTime:0};
      activeMoveMs = 0;
      clockAt = performance.now();
      clockRunning = false;
    }
    return history;
  }
  function syncMoveClock() {
    const now = performance.now();
    if (clockRunning) activeMoveMs += now - clockAt;
    clockAt = now;
    clockRunning = !!controllable() && !document.hidden;
  }
  const originalAPI = api;
  api = async function (path, data) {
    const humanTime = activeMoveMs;
    const moving = soloPractice && path === '/api/practice/move';
    if (moving) activeMoveMs = 0;
    let next;
    try { next = await originalAPI(path, data); }
    catch (error) { if (moving) activeMoveMs = humanTime; throw error; }
    if (soloPractice && next.id) {
      const h = metrics(next);
      if (moving && next.turn > h.lastTurn) {
        h.moves++;
        h.lastTurn = next.turn;
        h.grainSum += next.boards.human.world.flat().filter(Boolean).length;
        h.heightSum += next.boards.human.stats.height;
        h.lastTime = next.mode === 'ai' ? next.last_think_ms : humanTime;
        h.timeSum += h.lastTime;
      }
      if (path === '/api/practice/mode') {
        activeMoveMs = 0; clockAt = performance.now(); clockRunning = false;
      }
    }
    return next;
  };
  let detailPanels = [];
  if (soloPractice) {
    const boards = document.querySelector('.boards');
    for (const [side, title] of [['left', 'Board'], ['right', 'Performance']]) {
      const panel = document.createElement('aside');
      panel.className = `polish-detail-panel polish-detail-${side}`;
      panel.setAttribute('aria-label', `${title} statistics`);
      panel.innerHTML = `<h3>${title}</h3><dl>${Array.from({length:4}, () => '<div><dt></dt><dd>—</dd></div>').join('')}</dl>`;
      boards.append(panel);
      detailPanels.push(panel);
    }
  }
  function updatePracticeDetails() {
    if (!soloPractice || !state) return;
    // Keep the original four slots stable; AI timings live in fixed side slots.
    [...document.getElementById('human-stats').children].slice(4).forEach(node => node.remove());
    const s = state.boards.human.stats;
    const h = metrics(state);
    const grainsOnBoard = state.boards.human.world.reduce((sum, row) => sum + row.reduce((n, grain) => n + Number(grain !== 0), 0), 0);
    const number = n => Number(n).toLocaleString(undefined, {maximumFractionDigits:1});
    const time = ms => ms < 1000 ? `${Math.round(ms)}ms` : ms < 60000 ? `${(ms / 1000).toFixed(1)}s` : `${(ms / 60000).toFixed(1)}m`;
    const items = [
      ['Grains placed', number(s.placed * 100)],
      ['On the board', number(grainsOnBoard)],
      ['Avg grains on board', h.moves ? number(h.grainSum / h.moves) : '—'],
      ['Clear % per piece', `${s.clear_turn_percentage.toFixed(1)}%`],
      ['Pile height', `${s.height}/150`],
      ['Avg pile height', h.moves ? `${number(h.heightSum / h.moves)}/150` : '—'],
      ['Last move', h.moves ? time(h.lastTime) : '—'],
      ['Avg move', h.moves ? time(h.timeSum / h.moves) : '—'],
    ];
    detailPanels.flatMap(panel => [...panel.querySelectorAll('dl > div')]).forEach((slot, index) => {
      const [label, value] = items[index];
      if (slot.firstElementChild.textContent !== label) slot.firstElementChild.textContent = label;
      if (slot.lastElementChild.textContent !== value) slot.lastElementChild.textContent = value;
    });
  }

  const result = document.getElementById('result');
  const summary = document.createElement('div');
  summary.id = 'polish-real-summary';
  summary.style.width = '100%';
  result.querySelector('.result-copy').after(summary);
  const actions = document.createElement('div');
  actions.className = 'polish-result-actions';
  result.append(actions);
  actions.append(document.getElementById('play-again'));
  let dismissedResult = null;
  if (soloPractice) {
    const close = document.createElement('button');
    close.className = 'polish-close';
    close.type = 'button';
    close.setAttribute('aria-label', 'Close practice result');
    close.innerHTML = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m4 4 8 8m0-8-8 8"/></svg>';
    close.onclick = () => {
      dismissedResult = `${state.id}:${state.result}`;
      result.hidden = true;
      document.getElementById('human-board').focus({preventScroll:true});
    };
    result.prepend(close);
    result.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); close.click(); }
    });
  } else {
    const replay = document.createElement('button');
    replay.className = 'polish-secondary';
    replay.textContent = 'Replay seed';
    replay.onclick = () => newMatch(false);
    actions.append(replay);
  }

  function scoreMarkup(human, ai, solo = false, aiSolo = false) {
    const count = value => Number(value).toLocaleString();
    return `<div class="polish-score-pair${solo ? ' is-solo' : ''}"><div class="${aiSolo ? 'polish-ai' : ''}"><span>${aiSolo ? 'AI' : 'You'}</span><b>${count(human)}</b><span>grains cleared</span></div>${solo ? '' : `<div class="polish-ai"><span>AI</span><b>${count(ai)}</b><span>grains cleared</span></div>`}</div>`;
  }
  let lastFinished = null;
  const originalUpdate = updateUI;
  updateUI = function () {
    if (soloPractice) syncMoveClock();
    originalUpdate();
    if (!state) return;
    updatePracticeDetails();
    if (soloPractice) syncMoveClock();
    document.body.classList.toggle('is-paused', paused && !state.result);
    document.querySelectorAll('.polish-resume').forEach(button => {
      button.disabled = !paused || !!state.result;
      button.parentElement.setAttribute('aria-hidden', String(button.disabled));
    });
    if (!state.result) {
      lastFinished = null;
      return;
    }
    const finishKey = `${state.id}:${state.result}`;
    if (soloPractice && dismissedResult === finishKey) result.hidden = true;
    if (lastFinished === finishKey) return;
    lastFinished = finishKey;
    const solo = typeof practice !== 'undefined' && practice;
    const aiSolo = solo && state.mode === 'ai';
    result.style.setProperty('--finish-color', aiSolo || state.result === 'AI wins' ? 'var(--ai)' : 'var(--you)');
    summary.innerHTML = scoreMarkup(state.boards.human.stats.grains, state.boards.ai.stats.grains, solo, aiSolo) +
      `<p class="polish-result-caption">${state.turn.toLocaleString()} pieces played · seed ${state.seed}</p>`;
    result.classList.remove('is-arriving');
    void result.offsetWidth;
    result.classList.add('is-arriving');
  };

  document.addEventListener('keydown', event => {
    if (event.key !== ' ' || !paused || !state || state.result) return;
    if (event.target instanceof Element && event.target.closest('input,textarea,select,[contenteditable="true"]')) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (!event.repeat) {
      togglePause();
      document.getElementById('human-board').focus({preventScroll:true});
    }
  }, true);
})();
