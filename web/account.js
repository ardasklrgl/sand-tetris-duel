'use strict';
(() => {
  const form = document.getElementById('auth-form');
  if (!form) return;
  const username = document.getElementById('auth-username');
  const password = document.getElementById('auth-password');
  const note = document.getElementById('username-note');
  const error = document.getElementById('auth-error');
  const loginTab = document.getElementById('login-tab');
  const signupTab = document.getElementById('signup-tab');
  const submit = form.querySelector('button[type="submit"]');
  let mode = location.hash === '#signup' ? 'signup' : 'login';
  let checkSerial = 0;

  function setMode(next) {
    mode = next;
    loginTab.setAttribute('aria-selected', String(mode === 'login'));
    signupTab.setAttribute('aria-selected', String(mode === 'signup'));
    password.autocomplete = mode === 'signup' ? 'new-password' : 'current-password';
    submit.textContent = mode === 'signup' ? 'Sign up' : 'Log in';
    note.textContent = '';
    error.textContent = '';
    checkSerial++;
  }
  loginTab.addEventListener('click', () => { history.replaceState(null, '', location.pathname + location.search); setMode('login'); });
  signupTab.addEventListener('click', () => { history.replaceState(null, '', location.pathname + location.search + '#signup'); setMode('signup'); checkUsername(); });

  async function checkUsername() {
    const serial = ++checkSerial;
    note.className = 'form-note';
    const name = username.value.trim();
    if (mode !== 'signup' || !name) { note.textContent = ''; return; }
    if (!/^[A-Za-z0-9_]{3,20}$/.test(name)) {
      note.textContent = 'Use 3–20 letters, numbers, or underscores.';
      note.classList.add('is-error');
      return;
    }
    try {
      const response = await fetch('/api/username?name=' + encodeURIComponent(name));
      const result = await response.json();
      if (serial !== checkSerial) return;
      note.textContent = result.available ? 'Username is available.' : 'That username is already taken.';
      note.classList.add(result.available ? 'is-success' : 'is-error');
    } catch (_) {
      if (serial === checkSerial) note.textContent = '';
    }
  }
  username.addEventListener('input', () => { clearTimeout(username.checkTimer); username.checkTimer = setTimeout(checkUsername, 280); });
  username.addEventListener('blur', checkUsername);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    error.textContent = '';
    submit.disabled = true;
    try {
      const response = await fetch('/api/' + mode, {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: username.value.trim(), password: password.value})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Please try again.');
      const next = new URLSearchParams(location.search).get('next');
      location.assign(next && next.startsWith('/') && !next.startsWith('//') ? next : '/leaderboard');
    } catch (cause) {
      error.textContent = cause.message;
      submit.disabled = false;
    }
  });
  setMode(mode);
})();
