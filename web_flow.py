"""Playable flow design direction. Run: python web_flow.py."""
import argparse
from http import cookies
from html import escape
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlparse
import web_demo as original
from web_accounts import AccountStore

TITLE = 'Sand Tetris Duel · Drift'
PORT = 8770
ROOT = Path(__file__).resolve().parent
BEACH_ASSETS = ROOT / 'design' / 'beach' / 'assets'
CSS = r"""
*{box-sizing:border-box}button,input{transition:background .18s ease,box-shadow .18s ease}button:active:enabled{transform:translateY(1px)}::selection{background:var(--you);color:var(--bg)}input{caret-color:var(--you)}button:focus-visible,input:focus-visible{outline:2px solid var(--you);outline-offset:3px}.controls{margin-top:26px}.controls button{height:36px}.help{line-height:1.7;margin:14px 0 12px}.settings{padding-bottom:6px}.settings label{display:flex;align-items:center;gap:7px}.settings #seed{height:32px}.stats b{font-variant-numeric:tabular-nums}.boards canvas{width:100%;height:auto;max-height:none;aspect-ratio:17/30}.scoreboard{margin-top:26px;padding-top:26px}.footnote{line-height:1.6}.local-record{line-height:1.6}button svg{width:16px;height:16px;vertical-align:middle;pointer-events:none}.controls button{display:flex;justify-content:center;align-items:center;gap:5px}@media(max-width:480px){.help{font-size:10px}.controls{gap:5px}.controls button{height:38px}.settings{gap:6px}.settings #seed{width:96px}.settings button{height:32px;width:80px}}

:root{color-scheme:dark;--bg:#101116;--panel:#000;--line:#353641;--muted:#a9abb8;--ink:#eeeef5;--ai:hsl(265 72% 77%);--you:hsl(55 72% 77%);--mono:'SFMono-Regular',Menlo,Monaco,Consolas,'Liberation Mono',monospace}
body{min-height:100vh;background:#0b0b11;color:var(--ink);font-family:var(--mono);padding:48px 22px 70px;scrollbar-color:#444454 #111118}
#sand-atmosphere{position:fixed;inset:0;width:100vw;height:100vh;max-height:none;border:0;background:#0b0b11;pointer-events:none;z-index:0;image-rendering:auto;outline:none}
main{max-width:746px;padding:34px 42px 28px;background:transparent;box-shadow:none;border:1px solid #ffffff16;border-radius:3px;position:relative;z-index:1;isolation:isolate}
main::before{content:'';position:absolute;inset:0 -8px;background:rgba(17,18,25,.65);border-radius:24px;z-index:-1;pointer-events:none}
header{margin-bottom:24px;gap:16px}h1{font-family:var(--mono);font-size:21px;letter-spacing:-.8px;font-weight:700}.brand{display:flex;align-items:center;gap:12px}.brand-icon{color:var(--ai);width:24px;height:24px}.brand-icon svg{width:24px;height:24px}#atmosphere-toggle{background:transparent;border:1px solid var(--line);font-size:10px;padding:6px 9px;color:var(--muted);white-space:nowrap}#atmosphere-toggle:hover{color:var(--ink);background:#24252f}
.brand,.brand a,.brand h1,.title-letter{color:#fff}.brand a{text-decoration:none}.site-nav{display:flex;align-items:center;gap:8px;color:#666876;white-space:nowrap}.site-nav a,.site-nav button{width:auto;height:auto;padding:4px 1px;border:0;border-radius:0;background:transparent;color:var(--muted);font:10px var(--mono);text-decoration:none}.site-nav a:hover,.site-nav button:hover:enabled{border-color:transparent;background:transparent;color:var(--ink)}.site-nav button:active:enabled{transform:none}.site-nav a[aria-current="page"],.site-nav button[aria-pressed="true"]{color:var(--you)}
.site-nav-separator{font-size:9px;color:#555764;user-select:none}
body.is-background-view main{max-width:none;padding:0;background:transparent}body.is-background-view main::before{display:none}body.is-background-view main>:not(header){display:none}body.is-background-view header{position:fixed;z-index:2;top:22px;right:26px;margin:0}body.is-background-view .brand{display:none}
body.is-background-view .site-nav>:not(#nav-background){display:none}
.title-letter{display:inline-block;transform-origin:50% 100%}.play-title-animation .title-letter{animation:title-wave 820ms cubic-bezier(.16,1,.3,1) both;animation-delay:calc(140ms + var(--i)*70ms)}
@keyframes title-wave{0%,100%{transform:translateY(0) scale(1);color:#fff;text-shadow:0 0 0 transparent}38%,52%{transform:translateY(-4px) scale(1.045);color:#fff;text-shadow:0 0 6px #fff,0 0 13px var(--you),0 0 25px var(--ai)}}
progress{height:2px;margin-bottom:24px}.boards{gap:24px}.board-title h2{font:500 13px var(--mono)}.board-title{margin-bottom:12px}.board-title h2::before{content:'';display:inline-block;width:5px;height:5px;background:currentColor;margin:0 8px 2px 0}.boards canvas{border-color:#343640;border-radius:0}.stats{padding-top:14px}.stats span{font-size:9px}.stats b{font:500 15px var(--mono);margin-top:7px}.ai .stats b{color:var(--ai)}.human .stats b{color:var(--you)}button,input{font-family:var(--mono)}button{border-radius:4px;font-size:11px;background:#1c1d26}button:hover:enabled{background:#2d2e3b;border-color:var(--ai)}#drop{color:#101116;background:var(--you);border-color:transparent}#drop:hover:enabled{filter:brightness(.86)}.controls button{font-size:11px}.help{font-size:10px}.settings{font-size:11px}.settings #seed{font-size:11px;width:118px}.settings button{font-size:10px;width:100px}.settings input{background:#0b0c12;border-radius:3px}.scoreboard{border-top:1px solid #ffffff12;padding-top:28px}.score strong{font-size:32px;font-weight:400}.score .ai strong{color:var(--ai)}.score .humans strong{color:var(--you)}.score .middle b{font-size:15px}th,td{font-size:10px;border-color:#292a34;padding:12px 0}.footnote{font-size:9px}.local-record{font-size:10px}.result,.result.is-ai-win{background:#191a26;border-color:var(--ai);border-radius:4px}.result.is-ai-win p{color:var(--muted)}.result h2{font-size:20px}.result p{font-size:10px}.result.is-ai-win button{background:var(--ai);color:#101116}.result.is-ai-win button:hover:enabled{background:var(--ai);filter:brightness(.8);color:#101116}.win-bar{height:3px}
@media(max-width:700px){body{padding:26px 14px 40px}main{max-width:746px;padding:28px 24px}}@media(max-width:480px){body{padding:14px 9px 30px}main{padding:22px 13px}h1{font-size:16px}.brand{gap:8px}header{gap:8px}#atmosphere-toggle{font-size:9px;padding:6px}.boards{gap:13px}.stats{grid-template-columns:repeat(2,1fr)}.stats b{font-size:14px}.help{font-size:9px}.settings button{width:76px}.settings #seed{width:92px}.score strong{font-size:27px}.brand-icon{display:none}}

/* Apple layout geometry with Drift typography and animated palette. */
body { padding: 42px 22px 60px; }
main { max-width: 760px; padding: 34px 44px 30px; border: 0; border-radius: 24px; }
header { margin-bottom: 22px; gap: 15px; }
progress { height: 4px; border-radius: 10px; overflow: hidden; background: #000; }
progress::-webkit-progress-bar { background: #000; }
.boards { gap: 24px; }
.boards canvas { border: 0; border-radius: 12px; }
.stats { padding-top: 15px; gap: 5px; }
.stats b { margin-top: 4px; }
button { border: 0; border-radius: 9px; }
#atmosphere-toggle { border-radius: 9px; }
.settings button { width: 96px; height: 32px; }
.settings input[type=number] { border-radius: 8px; }
.scoreboard { padding: 26px 24px 20px; border: 0; border-radius: 16px; background: var(--panel); }
.win-bar { height: 5px; border-radius: 5px; overflow: hidden; gap: 2px; }
th, td { padding: 11px 0; }
.local-scoreboard { margin-top: 22px; padding-top: 20px; border-top: 1px solid #292a34; }
.local-record { margin: 0 0 13px; color: var(--muted); font-size: 10px; text-align: left; }
.local-score { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; text-align: center; }
.local-score strong { display: block; font-size: 23px; line-height: 1.15; font-weight: 400; font-variant-numeric: tabular-nums; }
.local-score .team { margin-bottom: 3px; font-size: 9px; }
.local-score small { display: block; margin-top: 3px; color: var(--muted); font-size: 9px; }
.local-score .human { color: var(--you); }
.local-score .ai { color: var(--ai); }
.local-score .middle { min-width: 76px; color: var(--muted); font-size: 9px; line-height: 1.45; }
.local-score .middle b { display: block; color: var(--ink); font-size: 13px; font-weight: 400; font-variant-numeric: tabular-nums; }
.local-win-bar { display: flex; height: 3px; gap: 2px; margin-top: 12px; overflow: hidden; border-radius: 3px; background: #20212a; }
.local-win-bar span { min-width: 0; transition: flex-grow .25s ease; }
.local-win-bar span:nth-child(1) { background: var(--ai); }
.local-win-bar span:nth-child(2) { background: #63686c; }
.local-win-bar span:nth-child(3) { background: var(--you); }
.duel-stage { position: relative; }
.duel-stage .result {
  position: absolute; z-index: 3; left: 50%; top: var(--board-center, 45%);
  transform: translate(-50%, -50%); width: max-content; max-width: calc(100% - 24px);
  margin: 0; padding: 18px 22px; border: 1px solid var(--line); border-radius: 16px;
  background: #191a26f5; box-shadow: 0 12px 38px #0009;
  display: flex; flex-direction: column; align-items: center; gap: 13px;
}
.duel-stage .result[hidden] { display: none; }
.duel-stage .result-copy { width: auto; justify-content: center; }
.duel-stage .result h2 { font-size: 20px; text-align: center; }
.duel-stage .result p { display: none; }
.duel-stage .result button { margin: 0; padding: 8px 15px; border-radius: 9px; }
.duel-stage .result.is-ai-win { border-color: var(--ai); }
@media(max-width:700px) {
  body { padding: 18px 12px 32px; }
  main { max-width: 760px; padding: 26px 24px; border-radius: 20px; }
}
@media(max-width:480px) {
  body { padding: 0; }
  main { padding: 24px 14px; border-radius: 0; }
  main::before { inset: 0; border-radius: 0; }
  .boards { gap: 14px; }
  .boards canvas { border-radius: 8px; }
  .scoreboard { padding: 20px 14px; }
  .local-scoreboard { margin-top: 18px; padding-top: 17px; }
  .settings button { width: 80px; height: 32px; }
  .settings #seed { width: 96px; }
  .duel-stage .result { padding: 15px 19px; }
  .duel-stage .result h2 { font-size: 18px; }
  .site-nav { gap: 6px; }
  .site-nav a, .site-nav button { font-size: 9px; }
  body.is-background-view header { top: 12px; right: 12px; }
}


/* Board names stay inside their dark frames; match information shares one panel. */
.board-frame { background: #000; border-radius: 12px; overflow: hidden; }
.board-frame .board-title { margin: 0; padding: 11px 14px 9px; min-height: 35px; }
.board-frame canvas { border-radius: 0; }
.match-panel { margin-top: 20px; padding: 22px 24px; background: var(--panel); border-radius: 16px; }
.match-stats { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 24px; }
.match-panel .stats { padding-top: 0; }
.match-panel .controls { margin-top: 22px; }
.match-panel .settings { padding-bottom: 0; }
.match-panel .controls button:not(#drop), .match-panel .settings button { background: #292b36; }
.match-panel .controls button:not(#drop):hover:enabled, .match-panel .settings button:hover:enabled { background: #373a48; }
.ai .stats span.clear-pulse, .ai .stats span.grain-pulse { --stat-glow: var(--ai); }
.human .stats span.clear-pulse, .human .stats span.grain-pulse { --stat-glow: var(--you); }
.stats span.clear-pulse b, .stats span.grain-pulse b { animation: stat-pulse 1.5s cubic-bezier(.16,1,.3,1); transform-origin: 25% 70%; }
@keyframes stat-pulse { 0%,100% { transform: scale(1); color: var(--stat-glow); text-shadow: 0 0 0 transparent; filter: none; } 18%,62% { transform: scale(1.085); color: #fff; text-shadow: 0 0 4px #fff,0 0 11px var(--stat-glow),0 0 24px var(--stat-glow),0 0 36px var(--stat-glow); filter: drop-shadow(0 0 6px var(--stat-glow)); } }
@keyframes title-glow { 0%,100% { color: #fff; text-shadow: 0 0 0 transparent; } 50% { color: #fff; text-shadow: 0 0 7px var(--you),0 0 14px var(--ai); } }
@keyframes stat-glow { 0%,100% { color: var(--stat-glow); filter: none; } 45% { color: #fff; filter: drop-shadow(0 0 5px var(--stat-glow)) drop-shadow(0 0 10px var(--stat-glow)); } }
@media(prefers-reduced-motion:reduce) {
  .play-title-animation .title-letter { animation-name: title-glow; animation-duration: 420ms; animation-delay: calc(50ms + var(--i)*28ms); }
  .stats span.clear-pulse b, .stats span.grain-pulse b { animation-name: stat-glow; animation-duration: 1s; }
}
@media(max-width:480px) {
  .board-frame { border-radius: 8px; }
  .board-frame .board-title { padding: 10px 11px 8px; min-height: 32px; }
  .match-panel { margin-top: 16px; padding: 18px 14px; }
  .match-stats { gap: 14px; }
}

"""
TITLE_BOOT_SCRIPT = r'''<script>
(() => {
  const seenKey = 'sandtris-title-animation-seen';
  const replayKey = 'sandtris-title-animation-replay';
  const paletteKey = 'sandtris-palette-time';
  let animate = false;
  try {
    const paletteTime = Number(sessionStorage.getItem(paletteKey));
    if (Number.isFinite(paletteTime)) {
      const hue = 265 + paletteTime * .85;
      document.documentElement.style.setProperty('--ai', `hsl(${hue} 72% 77%)`);
      document.documentElement.style.setProperty('--you', `hsl(${hue + 150} 72% 77%)`);
    }
    animate = !sessionStorage.getItem(seenKey) || sessionStorage.getItem(replayKey) === '1';
    sessionStorage.setItem(seenKey, '1');
    sessionStorage.removeItem(replayKey);
  } catch (_) { animate = true; }
  if (animate) document.body.classList.add('play-title-animation');
})();
</script>'''

HTML = original.HTML.replace("</style>", CSS + "</style>", 1)
HTML = HTML.replace("</head>", '<link rel="icon" type="image/png" href="/favicon.png"></head>', 1)
title_letters = []
letter_index = 0
for character in "Sand Tetris Duel":
    if character == " ":
        title_letters.append('<span class="title-space" aria-hidden="true">&nbsp;</span>')
    else:
        title_letters.append(f'<span class="title-letter" aria-hidden="true" style="--i:{letter_index}">{character}</span>')
        letter_index += 1
title_markup = ''.join(title_letters)
HTML = HTML.replace("<header><h1>Sand Tetris Duel</h1></header>", f'<header><div class="brand"><a id="brand-home" href="/" aria-label="Sand Tetris Duel home"><h1 aria-label="Sand Tetris Duel">{title_markup}</h1></a></div><nav class="site-nav" aria-label="Page navigation"><a href="/about">About</a><span class="site-nav-separator" aria-hidden="true">|</span><a href="/leaderboard">Leaderboard</a><span class="site-nav-separator" aria-hidden="true">|</span><button id="nav-background" type="button" aria-pressed="false">Background</button><span class="nav-account-slot"></span></nav></header>')
HTML = HTML.replace("<body>", '<body>' + TITLE_BOOT_SCRIPT + '<canvas id="sand-atmosphere" aria-hidden="true"></canvas><video id="sand-beach-video" src="/beach-assets/night-beach.mp4" poster="/beach-assets/night-beach-poster.jpg" muted loop playsinline preload="auto" hidden aria-hidden="true"></video>', 1)
HTML = HTML.replace('</body>', '<script src="/beach-background.js"></script></body>', 1)

# Keep the result inside the play area, outside normal document flow.
HTML = HTML.replace('<section id="result"', '<div class="duel-stage"><section id="result"', 1)
HTML = HTML.replace('<p id="status"', '</div><p id="status"', 1)
HTML = HTML.replace('</body>', r"""<script>
(() => {
  const stage = document.querySelector('.duel-stage');
  const board = document.getElementById('human-board');
  function centerResult() {
    const bounds = board.getBoundingClientRect();
    stage.style.setProperty('--board-center', `${bounds.top - stage.getBoundingClientRect().top + bounds.height / 2}px`);
  }
  new ResizeObserver(centerResult).observe(stage);
  centerResult();
})();
</script></body>""")


# The frame includes each title and canvas; both stats groups move into one
# shared surface with controls and seed actions. Original element IDs stay intact.
ai_stats = '<div id="ai-stats" class="stats" aria-label="AI statistics"></div>'
human_stats = '<div id="human-stats" class="stats" aria-label="Your statistics"></div>'
HTML = HTML.replace(ai_stats, '', 1).replace(human_stats, '', 1)
HTML = HTML.replace('<article class="ai"><div class="board-title">', '<article class="ai"><div class="board-frame"><div class="board-title">', 1)
HTML = HTML.replace('<article class="human"><div class="board-title">', '<article class="human"><div class="board-frame"><div class="board-title">', 1)
HTML = HTML.replace('</canvas></article>', '</canvas></div></article>', 2)
HTML = HTML.replace('<p id="status"', '<section class="match-panel" aria-label="Match statistics and controls"><div class="match-stats"><div class="ai">' + ai_stats + '</div><div class="human">' + human_stats + '</div></div><p id="status"', 1)
HTML = HTML.replace('<section id="scoreboard"', '</section><section id="scoreboard"', 1)
local_scoreboard = '''<div class="local-scoreboard" aria-label="Your record in this browser">
<p id="local-record" class="local-record">Your record in this browser</p>
<div class="local-score"><div class="ai"><div class="team">AI</div><strong id="local-losses">0</strong><small>wins</small></div><div class="middle"><b id="local-matches">0</b>matches<br><span id="local-draws">0 draws</span></div><div class="human"><div class="team">YOU</div><strong id="local-wins">0</strong><small>wins</small></div></div>
<div class="local-win-bar" aria-hidden="true"><span id="local-loss-segment"></span><span id="local-draw-segment"></span><span id="local-win-segment"></span></div>
</div>'''
HTML = HTML.replace('<p id="local-record" class="local-record"></p>', '', 1)
HTML = HTML.replace('<p class="footnote">Design preview: these global figures are illustrative, not live results.</p></section>', '<p class="footnote">Design preview: these global figures are illustrative, not live results.</p>' + local_scoreboard + '</section>', 1)
HTML = HTML.replace('</body>', r'''<script>
(() => {
  const backgroundButton = document.getElementById('nav-background');
  document.getElementById('brand-home').addEventListener('click', event => {
    if (location.pathname === '/') {
      event.preventDefault();
      document.body.classList.remove('play-title-animation');
      void document.body.offsetWidth;
      document.body.classList.add('play-title-animation');
    } else {
      try { sessionStorage.setItem('sandtris-title-animation-replay', '1'); } catch (_) {}
    }
  });
  function setBackgroundView(active) {
    document.body.classList.toggle('is-background-view', active);
    backgroundButton.setAttribute('aria-pressed', String(active));
    backgroundButton.textContent = active ? 'Return' : 'Background';
  }
  backgroundButton.addEventListener('click', () => setBackgroundView(!document.body.classList.contains('is-background-view')));
  addEventListener('keydown', event => { if(event.key === 'Escape' && document.body.classList.contains('is-background-view')) setBackgroundView(false); });

  function watchStat(id, index, pulseClass) {
    const stats = document.getElementById(id);
    let previous = null;
    function check() {
      const item = stats.children[index];
      const value = Number(item?.querySelector('b')?.textContent.replace(/[^0-9.-]/g, ''));
      if (!Number.isFinite(value)) return;
      if (previous !== null && value > previous) {
        item.classList.remove(pulseClass);
        void item.offsetWidth;
        item.classList.add(pulseClass);
      }
      previous = value;
    }
    new MutationObserver(check).observe(stats, {childList:true, subtree:true, characterData:true});
    check();
  }
  watchStat('ai-stats', 1, 'clear-pulse');
  watchStat('human-stats', 1, 'clear-pulse');
  watchStat('ai-stats', 2, 'grain-pulse');
  watchStat('human-stats', 2, 'grain-pulse');
})();
</script></body>''', 1)

PAGE_STYLE = HTML.split('<style>', 1)[1].split('</style>', 1)[0]
INFO_CSS = r'''
.info-page main { min-height: 720px; }
.info-page .brand a { color: inherit; text-decoration: none; }
.info-content { padding: 38px 0 10px; }
.info-intro { max-width: none; margin-bottom: 24px; padding: 24px; border-radius: 16px; background: #000; }
.info-intro h2 { margin: 0 0 14px; font: 700 34px/1.08 var(--mono); letter-spacing: -1.5px; }
.info-intro p { max-width: 66ch; margin: 0; color: var(--muted); font-size: 12px; line-height: 1.75; }
.sample-label { display: inline-block; margin-bottom: 13px; color: var(--you); font-size: 9px; letter-spacing: .08em; text-transform: uppercase; }
.info-visual { margin: 0 0 30px; padding: 24px; border-radius: 16px; background: #000; }
.duel-preview { display: grid; grid-template-columns: minmax(0,1fr) auto minmax(0,1fr); align-items: center; gap: 22px; }
.preview-side > span { display: block; margin-bottom: 9px; font-size: 10px; }
.preview-side.ai-preview > span { color: var(--ai); }
.preview-side.you-preview > span { color: var(--you); }
.preview-board { position: relative; height: 190px; overflow: hidden; border: 1px solid #242630; border-radius: 10px; background: #050506; }
.pixel-pile { position: absolute; inset: auto 10px 0; display: flex; align-items: flex-end; gap: 3px; height: 75%; }
.pixel-pile i { flex: 1; min-width: 0; height: var(--h); background: var(--c); box-shadow: 0 -5px 16px color-mix(in srgb,var(--c) 48%,transparent); }
.preview-seed { min-width: 92px; text-align: center; }
.preview-seed b { display: block; color: var(--ink); font-size: 12px; font-weight: 500; }
.preview-seed span { display: block; margin-top: 6px; color: var(--muted); font-size: 9px; }
.info-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; padding: 24px; border-radius: 16px; background: #000; }
.info-copy { padding-top: 18px; border-top: 1px solid #343641; }
.info-copy h3 { margin: 0 0 9px; font-size: 13px; font-weight: 600; }
.info-copy p { margin: 0; color: var(--muted); font-size: 10px; line-height: 1.7; }
.leaderboard-summary { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; text-align: center; }
.leaderboard-summary strong { display: block; font-size: 44px; line-height: 1; font-weight: 400; font-variant-numeric: tabular-nums; }
.leaderboard-summary .ai-total strong { color: var(--ai); }
.leaderboard-summary .human-total strong { color: var(--you); }
.leaderboard-summary small { display: block; margin-top: 7px; color: var(--muted); font-size: 9px; }
.leaderboard-summary .versus { color: var(--muted); font-size: 10px; }
.leaderboard-summary .versus b { display: block; margin-bottom: 4px; color: var(--ink); font-size: 14px; font-weight: 400; }
.sample-bar { display: flex; height: 5px; gap: 2px; margin: 22px 0 4px; overflow: hidden; border-radius: 5px; }
.sample-bar span:nth-child(1) { flex: 59.5; background: var(--ai); }
.sample-bar span:nth-child(2) { flex: 1.7; background: #63686c; }
.sample-bar span:nth-child(3) { flex: 38.8; background: var(--you); }
.standings { margin-top: 24px; padding: 24px; border-radius: 16px; background: #000; }
.standings h3 { margin: 0 0 12px; font-size: 12px; font-weight: 600; }
.standings table th:first-child,.standings table td:first-child { width: 42px; }
.standings table th:nth-child(2),.standings table td:nth-child(2) { text-align: left; color: var(--ink); }
.standings .positive { color: var(--you); }
.standings .negative { color: var(--ai); }
.info-note { margin: 18px 0 0; color: var(--muted); font-size: 9px; line-height: 1.6; }
.about-frame { padding: 30px; border-radius: 16px; background: #000; }
.about-section + .about-section { margin-top: 28px; padding-top: 28px; border-top: 1px solid #292b34; }
.about-section h2 { max-width: 760px; margin: 0 0 15px; font: 700 34px/1.08 var(--mono); letter-spacing: -1.5px; }
.about-section h3 { margin: 0 0 12px; color: var(--ink); font-size: 13px; font-weight: 600; }
.about-section p { max-width: none; margin: 0; color: var(--muted); font-size: 11px; line-height: 1.8; }
.about-section p + p { margin-top: 12px; }
.about-controls { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 18px 0 0; color: var(--ink); font-size: 9px; }
.about-controls span { white-space: nowrap; }
.about-controls b { display: inline-block; min-width: 24px; margin-right: 5px; color: var(--you); font-weight: 600; }
.web-stamps { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 16px; }
.web-stamp { display: grid; width: 88px; height: 31px; place-items: center; box-sizing: border-box; border: 1px solid currentColor; background: #08080a; color: var(--ai); font-size: 7px; font-weight: 700; line-height: 1.15; letter-spacing: .08em; text-align: center; text-transform: uppercase; box-shadow: inset 0 0 0 1px #171820; }
.web-stamp:nth-child(even) { color: var(--you); }
.web-stamp:nth-child(3n) { border-style: dashed; }
.site-nav { flex: 1; justify-content: flex-end; }
.nav-account-slot { margin-left: auto; }
.site-nav .account-link { display: inline-flex; align-items: center; gap: 7px; color: var(--ink); }
.account-light { display: inline-block; width: 7px; height: 7px; flex: none; border-radius: 1px; background: #757986; }
.account-light.is-on { background: var(--you); box-shadow: 0 0 8px var(--you); }
.info-page .info-content { padding-top: 26px; }
.info-page .about-frame { padding: 26px 28px; }
.about-section h2,.info-page .info-intro h2 { margin: 0 0 13px; font: 500 14px/1.5 var(--mono); letter-spacing: 0; }
.about-section h3,.standings h3 { font-size: 12px; font-weight: 500; }
.about-section p { font-size: 11px; }
.about-section ol { margin: 0; padding-left: 20px; color: var(--muted); font-size: 11px; line-height: 1.85; }
.about-section li + li { margin-top: 8px; }
.about-section li::marker { color: var(--you); }
.about-section .about-controls { margin-top: 15px; }
.social-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.social-tags a { display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px; border: 1px solid #363744; border-radius: 6px; background: #000; color: var(--ink); text-decoration: none; transition: color .18s ease,border-color .18s ease; }
.social-tags svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.social-tags a:hover { border-color: var(--you); color: var(--you); }
.site-panel { padding: 24px; border-radius: 16px; background: #000; }
.site-panel + .site-panel { margin-top: 15px; }
.site-panel h2 { margin: 0 0 15px; font: 500 13px/1.4 var(--mono); }
.site-panel p { margin: 0; color: var(--muted); font-size: 11px; line-height: 1.75; }
.site-panel p + p { margin-top: 10px; }
.site-panel .sample-label { margin-bottom: 10px; }
.site-panel .inline-link { color: var(--you); text-decoration: none; }
.site-panel .inline-link:hover { text-decoration: underline; }
.site-panel .panel-cta { display: inline-block; margin-top: 17px; padding: 8px 13px; border-radius: 8px; background: #292b36; color: var(--ink); font-size: 10px; text-decoration: none; }
.site-panel .panel-cta:hover { background: #373a48; }
.personal-top { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.personal-top .rank { color: var(--you); font-size: 11px; }
.personal-score { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; margin-top: 16px; text-align: center; }
.personal-score strong { display: block; font-size: 26px; font-weight: 400; color: var(--you); }
.personal-score .ai-score strong { color: var(--ai); }
.personal-score small { color: var(--muted); font-size: 9px; }
.personal-score .score-middle { color: var(--muted); font-size: 9px; }
.personal-score .score-middle b { display: block; color: var(--ink); font-size: 13px; font-weight: 400; }
.personal-bar { display: flex; height: 4px; gap: 2px; margin: 17px 0 18px; border-radius: 4px; overflow: hidden; background: #292b36; }
.personal-bar i { min-width: 0; }
.personal-bar i:nth-child(1) { background: var(--you); }
.personal-bar i:nth-child(2) { background: #757986; }
.personal-bar i:nth-child(3) { background: var(--ai); }
.compare-line { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding-top: 10px; border-top: 1px solid #292b34; }
.compare-line + .compare-line { margin-top: 9px; }
.compare-line b { color: var(--ink); font-size: 11px; font-weight: 500; white-space: nowrap; }
.standings-table th,.standings-table td { padding: 10px 5px; font-size: 10px; }
.standings-table th:first-child,.standings-table td:first-child { width: 34px; padding-left: 0; }
.standings-table th:nth-child(2),.standings-table td:nth-child(2) { text-align: left; }
.standings-table th:last-child,.standings-table td:last-child { padding-right: 0; }
.standings-table .your-rank td { border-top: 1px solid #555768; }
.auth-switch { display: flex; gap: 16px; margin-bottom: 22px; }
.auth-switch button { padding: 4px 0; border-radius: 0; background: transparent; color: var(--muted); }
.auth-switch button:hover,.auth-switch button[aria-selected="true"] { background: transparent; color: var(--you); }
.auth-form { max-width: 350px; }
.auth-form label { display: block; margin-top: 15px; color: var(--muted); font-size: 10px; }
.auth-form input { display: block; width: 100%; height: 37px; margin-top: 6px; padding: 8px 10px; border: 1px solid #363744; border-radius: 7px; background: #111219; color: var(--ink); font-size: 11px; }
.auth-form input:focus { border-color: var(--you); }
.auth-form .auth-submit { margin-top: 18px; padding: 9px 16px; border-radius: 8px; background: #292b36; }
.auth-form .auth-submit:hover { background: #373a48; }
.form-note { min-height: 18px; margin-top: 7px !important; font-size: 10px !important; }
.form-note.is-error { color: #e6a2a2; }
.form-note.is-success { color: var(--you); }
@media(max-width:600px) {
  .info-page main { min-height: 100vh; }
  .info-content { padding-top: 28px; }
  .info-intro h2 { font-size: 27px; }
  .duel-preview { grid-template-columns: 1fr 1fr; gap: 13px; }
  .preview-seed { grid-column: 1 / -1; grid-row: 1; }
  .preview-board { height: 150px; }
  .info-columns { grid-template-columns: 1fr; gap: 22px; }
  .leaderboard-summary strong { font-size: 34px; }
  .info-visual { padding: 18px 14px; }
  .info-intro,.info-columns,.standings { padding: 18px 14px; }
  .about-frame { padding: 22px 16px; }
  .about-section h2 { font-size: 27px; }
  .info-page .about-frame,.site-panel { padding: 20px 16px; }
  .about-section h2 { font-size: 14px; }
  .site-nav { flex-wrap: wrap; column-gap: 7px; row-gap: 4px; }
  .nav-account-slot { margin-left: 0; }
  .standings-table { font-size: 9px; }
}
'''

POLISH_CSS = r'''
html { scrollbar-gutter: stable; }
header { flex-wrap: wrap; }
.brand { flex: 0 0 auto; }
.site-nav { flex: 0 1 auto; margin-left: auto; justify-content: flex-end; flex-wrap: nowrap; gap: 8px; max-width: 100%; min-width: 0; }
.site-nav > * { flex-shrink: 0; }
.nav-account-slot { margin-left: 0; display: inline-flex; align-items: center; }
.nav-account-slot::before { content: '|'; margin-right: 8px; color: #555764; font-size: 9px; }
.site-panel,.about-frame,.board-frame,.match-panel,.scoreboard { box-shadow: 0 10px 36px 4px #000000a0; }
main::before { box-shadow: 0 18px 64px 10px #000000a8; }
.game-leaderboard { margin-top: 20px; padding: 24px; border-radius: 16px; background: #000; box-shadow: 0 10px 36px 4px #000000a0; }
.scoreboard > .footnote { margin: 12px 0; }
.scoreboard .local-scoreboard { margin-top: 0; }
.match-panel .controls button:not(#drop),.match-panel .settings button,.site-panel .panel-cta { background: #000; border: 1px solid var(--line); }
.match-panel .controls button:not(#drop):hover:enabled,.match-panel .settings button:hover:enabled,.site-panel .panel-cta:hover { background: #101116; border-color: #5c5f6b; }
.site-panel a.panel-cta[href^="/login"],.auth-form .auth-submit { color: #101116; background: var(--you); border: 1px solid transparent; }
.site-panel a.panel-cta[href^="/login"]:hover,.auth-form .auth-submit:hover:enabled { background: var(--you); filter: brightness(.86); border-color: transparent; }
.info-page main { min-height: 0; }
.account-page .info-content { padding-top: 8px; padding-bottom: 0; }
.account-page .auth-switch { margin-bottom: 16px; }
.auth-form { max-width: none; display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 14px 16px; }
.auth-form label { margin: 0; }
.auth-form label > span { display: block; padding-left: 6px; }
.auth-form input { height: 32px; padding: 6px; border: 1px solid var(--line); border-radius: 8px; background: #0b0c12; }
.auth-form .form-note { min-height: 0; margin: 6px 0 0 !important; }
.auth-form .form-note:empty { display: none; }
.auth-form #auth-error { grid-column: 1 / -1; }
.auth-form .auth-submit { grid-column: 1 / -1; justify-self: start; margin-top: 0; padding: 7px 16px; }
.game-leaderboard h2 { margin: 0; font: 500 12px/1.5 var(--mono); }
.game-leaderboard p { color: var(--muted); font-size: 10px; line-height: 1.7; }
.panel-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.panel-heading h2 { margin: 0; }
.panel-heading > span,.panel-heading > a { color: var(--muted); font-size: 9px; text-decoration: none; }
.panel-heading > a:hover { color: var(--you); }
.profile-panel .personal-top h2 { font-weight: 500; margin-bottom: 0; }
.profile-panel .personal-top .sample-label { margin-bottom: 6px; }
.profile-metrics { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 12px; margin-top: 20px; }
.profile-metrics small { display: block; color: var(--muted); font-size: 9px; }
.profile-metrics b { display: block; margin-top: 5px; color: var(--ink); font-size: 14px; font-weight: 400; }
.personal-bar i:nth-child(1) { background: var(--ai); }
.personal-bar i:nth-child(3) { background: var(--you); }
.table-scroll { width: calc(100% + 48px); max-width: calc(100% + 48px); margin: -24px; padding: 24px; overflow-x: auto; }
.standings-table th:nth-child(n) { color: var(--muted); }
.standings-table th:first-child,.standings-table td:first-child { padding-left: 6px; }
.standings-table tbody td:nth-child(n) { color: var(--rank-color,var(--ai)); }
.standings-table td:nth-child(2) { max-width: 160px; overflow-wrap: anywhere; }
.standings-table th:nth-child(2),.standings-table td:nth-child(2) { text-align: left; }
.standings-table .is-me { background: #ffffff04; }
.rank-number { font-weight: 700; }
.rank-1 { text-shadow: 0 0 5px var(--you),0 0 14px var(--you),0 0 28px color-mix(in srgb,var(--you) 65%,transparent); }
.rank-2 { text-shadow: 0 0 4px var(--you),0 0 10px color-mix(in srgb,var(--you) 60%,transparent); }
.rank-3 { text-shadow: 0 0 6px color-mix(in srgb,var(--you) 65%,transparent); }
.comparison-table { table-layout: fixed; }
.comparison-table th,.comparison-table td { font-size: 10px; padding: 11px 3px; }
.comparison-table th:first-child { width: 40%; }
.comparison-table th:nth-child(2),.comparison-table td:nth-child(2) { color: var(--ai); }
.comparison-table th:nth-child(3),.comparison-table td:nth-child(3),.comparison-table th:nth-child(4),.comparison-table td:nth-child(4) { color: var(--you); }
.comparison-table th:last-child,.comparison-table td:last-child { padding-right: 0; }
.pagination { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 18px; font-size: 9px; }
.pagination a { color: var(--ink); text-decoration: none; padding: 6px 0; }
.pagination a:hover { color: var(--you); }
.pagination span { color: var(--muted); }
.pagination [aria-disabled] { color: #5b5e6c; }
#rankings { scroll-margin-top: 24px; }
@media(max-width:700px) {
  header { row-gap: 15px; }
  .site-nav { font-size: 9px; }
}
@media(max-width:480px) {
  .site-nav { gap: 5px; overflow-x: auto; justify-content: flex-start; margin-left: 0; width: 100%; padding-bottom: 3px; scrollbar-width: none; }
  .site-nav::-webkit-scrollbar { display: none; }
  .site-nav a,.site-nav button { font-size: 9px; }
  .nav-account-slot::before { margin-right: 5px; }
  .game-leaderboard { padding: 20px 14px; }
  .profile-metrics { grid-template-columns: repeat(2,minmax(0,1fr)); row-gap: 17px; }
  .comparison-table th,.comparison-table td { font-size: 9px; }
  .standings-table th,.standings-table td { font-size: 9px; padding: 10px 3px; }
  .auth-form { grid-template-columns: minmax(0,1fr); gap: 12px; }
}
'''

def page_nav(current):
    about_current = ' aria-current="page"' if current == 'about' else ''
    leaderboard_current = ' aria-current="page"' if current == 'leaderboard' else ''
    return f'''<nav class="site-nav" aria-label="Page navigation"><a href="/about"{about_current}>About</a><span class="site-nav-separator" aria-hidden="true">|</span><a href="/leaderboard"{leaderboard_current}>Leaderboard</a><span class="site-nav-separator" aria-hidden="true">|</span><button id="nav-background" type="button" aria-pressed="false">Background</button><span class="nav-account-slot"></span></nav>'''

INFO_BACKGROUND_SCRIPT = r'''<script>
(() => {
  const button = document.getElementById('nav-background');
  document.getElementById('brand-home').addEventListener('click', () => {
    try { sessionStorage.setItem('sandtris-title-animation-replay', '1'); } catch (_) {}
  });
  function setBackgroundView(active) {
    document.body.classList.toggle('is-background-view', active);
    button.setAttribute('aria-pressed', String(active));
    button.textContent = active ? 'Return' : 'Background';
  }
  button.addEventListener('click', () => setBackgroundView(!document.body.classList.contains('is-background-view')));
  addEventListener('keydown', event => { if(event.key === 'Escape' && document.body.classList.contains('is-background-view')) setBackgroundView(false); });
})();
</script>'''

def build_info_page(page_title, current, content):
    header = f'''<header><div class="brand"><a id="brand-home" href="/" aria-label="Return to Sand Tetris Duel"><h1 aria-label="Sand Tetris Duel">{title_markup}</h1></a></div>{page_nav(current)}</header>'''
    page_class = 'info-page account-page' if current == 'account' else 'info-page'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{page_title} · Sand Tetris Duel</title><link rel="icon" type="image/png" href="/favicon.png"><style>{PAGE_STYLE}{INFO_CSS}{POLISH_CSS}</style></head><body class="{page_class}">{TITLE_BOOT_SCRIPT}<canvas id="sand-atmosphere" aria-hidden="true"></canvas><video id="sand-beach-video" src="/beach-assets/night-beach.mp4" poster="/beach-assets/night-beach-poster.jpg" muted loop playsinline preload="auto" hidden aria-hidden="true"></video><main>{header}<div class="info-content">{content}</div></main><script src="/beach-background.js"></script>{INFO_BACKGROUND_SCRIPT}</body></html>'''

ABOUT_CONTENT = '''
<article class="about-frame">
  <section class="about-section"><h2>How to play</h2><ol><li>A game will open by default at the main page with a random seed. You can just jump in and play, or pick your own seed or replay a seed. The seed determines the shapes and colors of the pieces you get. You and the AI receive the same exact sequence of piece shapes and colors so it's a fair battle.</li><li>Move and rotate your falling piece, then drop it wherever it fits. Sand grains fall and settle independently after each placement.</li><li>Connect grains of the same color from one wall to the other to clear them. The only condition for clearing is that a group of same color sand touches both wall. A group can only be formed when grains touch orthogonally.</li><li>After 100 pieces, the side that cleared more grains wins. You can replay the same seed or start a new match.</li></ol><div class="about-controls" aria-label="Game controls"><span><b>← →</b> move</span><span><b>↑</b> rotate</span><span><b>↓</b> soft drop</span><span><b>Space</b> drop</span><span><b>P</b> pause</span></div></section>
  <section class="about-section"><h2>About the game</h2><p>Sand Tetris Duel grew from the popular game Sandtris, a falling sand take on Tetris. Pieces break into moving grains instead of staying locked to a grid. The gameplay is pretty intuitive once you play a few rounds.</p><p>I trained an AI to play the game basically. It is pretty decent from my test runs. It managed to survive 216,892 steps/pieces at one run, which is over 24 hours of gameplay, at about 0.25-0.3s per piece. The AI doesn't run that fast in the duel mode, instead it matches your speed for better experience. You can see in real time where the AI is placing the pieces, and the same seed helps since you are basically playing the same game. More technical details of the AI can be found in my github.</p><p>As I said the AI is decent, but there is a benchmark needed. Is it actually human level? This game is to test that. From my experience it isn't unbeatable at all, since the 100 piece cutoff gives room for error to both sides. If it was until game over instead of 100 pieces, then AI would just win, unless if people are willing to play for hours, even days. 100 pieces is the sweet spot.</p><p>Signed in matches contribute to your record and the leaderboard when they finish. The leaderboard ranks players by wins minus losses, with grains cleared breaking ties.</p></section>
  <section class="about-section"><h2>About me</h2><p>I'm Arda. If you have any feedbacks, suggestions or just want to contact me, use the links below. I would massively appreciate any feedback, so feel free to reach out.</p>
    <div class="social-tags" aria-label="Social links">
      <a href="https://x.com/cupsyx" target="_blank" rel="noopener noreferrer" aria-label="Arda on X (@cupsyx)" title="X · @cupsyx"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 3h4l12 18h-4L4 3Zm16 0L4 21"/></svg></a>
      <a href="https://github.com/ardasklrgl" target="_blank" rel="noopener noreferrer" aria-label="Arda on GitHub" title="GitHub · ardasklrgl"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 19c-4.3 1.3-4.3-2.5-6-3m12 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 19 4.77 5.07 5.07 0 0 0 18.91 1S17.73.65 15 2.48a13.38 13.38 0 0 0-7 0C5.27.65 4.09 1 4.09 1A5.07 5.07 0 0 0 4 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 8 18.13V22"/></svg></a>
      <a href="mailto:ardasklrgl@gmail.com" aria-label="Email Arda at ardasklrgl@gmail.com" title="ardasklrgl@gmail.com"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg></a>
    </div>
  </section>
</article>
'''

AUTH_CONTENT = '''
<section class="site-panel"><div class="auth-switch" role="tablist" aria-label="Account action"><button id="login-tab" type="button" role="tab" aria-selected="true">Log in</button><button id="signup-tab" type="button" role="tab" aria-selected="false">Sign up</button></div><form id="auth-form" class="auth-form"><div class="auth-field"><label><span>Username</span><input id="auth-username" name="username" autocomplete="username" minlength="3" maxlength="20" aria-describedby="username-note" required></label><p id="username-note" class="form-note" aria-live="polite"></p></div><div class="auth-field"><label><span>Password</span><input id="auth-password" name="password" type="password" autocomplete="current-password" minlength="8" maxlength="128" required></label></div><p id="auth-error" class="form-note is-error" role="alert"></p><button class="auth-submit" type="submit">Log in</button></form></section>
'''
AUTH_SCRIPT = r'''<script src="/account.js"></script>'''

def number(value):
    return f"{value:,}"

def rank_mark(rank):
    if rank <= 3:
        return f'<span class="rank-number rank-{rank}" aria-label="Rank {rank}">{rank}</span>'
    return str(rank)

def leaderboard_table(players, user=None, own=None):
    if not players:
        return '<p class="empty-record">No ranked matches yet. Complete a signed-in duel to join the board.</p>'
    rows = []
    entries = list(players)
    if own and all(player['id'] != own['id'] for player in entries):
        entries.append(own)
    for player in entries:
        current = bool(user and player['id'] == user['id'])
        extra = own and player['id'] == own['id'] and all(p['id'] != own['id'] for p in players)
        classes = ('is-me ' if current else '') + ('your-rank' if extra else '')
        rank = player['rank']
        rank_color = 'var(--you)' if rank < 5 else '#fff' if rank == 5 else f'color-mix(in srgb,#fff {max(0,100-(rank-5)*10)}%,var(--ai))'
        name = f'<span class="rank-name rank-{rank}">{escape(player["username"])}</span>' if rank <= 3 else escape(player['username'])
        rows.append(f'''<tr class="{classes.strip()}" style="--rank-color:{rank_color}"><td>{rank_mark(rank)}</td><td>{name}</td><td>{player['wins']}–{player['losses']}</td><td>{player['difference']:+d}</td><td>{number(player['grains'])}</td></tr>''')
    return f'''<div class="table-scroll"><table class="standings-table"><thead><tr><th scope="col">#</th><th scope="col">Player</th><th scope="col">W–L</th><th scope="col">+/−</th><th scope="col">Grains</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''

def score_pair(ai, human, draws, human_label='Your'):
    total = ai + human + draws
    return f'''<div class="personal-score"><div class="ai-score"><strong>{number(ai)}</strong><small>AI wins</small></div><div class="score-middle"><b>{number(total)}</b>matches · {number(draws)} {'draw' if draws == 1 else 'draws'}</div><div><strong>{number(human)}</strong><small>{human_label} wins</small></div></div><div class="personal-bar" aria-label="AI {ai} wins, {human_label} {human} wins, {draws} draws"><i style="flex:{ai}"></i><i style="flex:{draws if total else 1}"></i><i style="flex:{human}"></i></div>'''

def leaderboard_content(user, board):
    mine, profile, community = board['mine'], board['profile'], board['community']
    if user:
        rank = f"#{mine['rank']} · Top {mine['top_percent']}%" if mine else 'Unranked · play your first match'
        wins, losses, draws, matches = (mine[key] if mine else 0 for key in ('wins','losses','draws','matches'))
        rate = f'{100*wins/matches:.1f}%' if matches else '—'
        best = number(profile['best_human']) if matches else '—'
        personal = f'''<section class="site-panel profile-panel" aria-label="Your player profile"><div class="personal-top"><h2>{escape(user['username'])}</h2><span class="rank">{rank}</span></div>{score_pair(losses,wins,draws)}<div class="profile-metrics"><div><small>Win rate</small><b>{rate}</b></div><div><small>Wins − losses</small><b>{wins-losses:+d}</b></div><div><small>Total grains</small><b>{number(mine['grains']) if mine else '0'}</b></div><div><small>Best clear total</small><b>{best}</b></div></div></section>'''
    else:
        personal = '''<section class="site-panel"><h2>Keep your place in the duel.</h2><p>Log in or sign up to save your results and compare your play with the AI and the human average.</p><a class="panel-cta" href="/login?next=/leaderboard">Log in / Sign up</a></section>'''
    def metric(value, suffix='', decimals=0):
        return '—' if value is None else (f'{value:,.{decimals}f}' + suffix)
    totals = board['totals']
    total = totals['matches']
    stats = [
        ('Win rate', metric(100*totals['ai_wins']/total if total else None,'%',1), metric(100*totals['human_wins']/total if total else None,'%',1), metric(100*mine['wins']/mine['matches'] if mine else None,'%',1)),
        ('Average grains cleared', metric(community['ai_average']),metric(community['human_average']),metric(profile['human_average']) if profile else '—'),
        ('Average clears',metric(community['ai_clears'],'',1),metric(community['human_clears'],'',1),metric(profile['human_clears'],'',1) if profile else '—'),
        ('Clear efficiency',metric(community['ai_efficiency'],'%',1),metric(community['human_efficiency'],'%',1),metric(profile['human_efficiency'],'%',1) if profile else '—'),
        ('Average pieces played',metric(community['ai_steps'],'',1),metric(community['human_steps'],'',1),metric(profile['human_steps'],'',1) if profile else '—'),
        ('Best grains cleared',metric(community['best_ai'] if total else None),metric(community['best_human'] if total else None),metric(profile['best_human'] if mine else None) if profile else '—')]
    comparison = '<table class="comparison-table"><thead><tr><th scope="col">Per match</th><th scope="col">AI</th><th scope="col">Humans</th><th scope="col">You</th></tr></thead><tbody>' + ''.join(f'<tr><td>{label}</td><td>{ai}</td><td>{human}</td><td>{own}</td></tr>' for label,ai,human,own in stats) + '</tbody></table>'
    community_panel = f'''<section class="site-panel"><div class="panel-heading"><h2>AI vs humans</h2><span>{number(board['players'])} ranked players</span></div>{score_pair(totals['ai_wins'],totals['human_wins'],totals['draws'],'Human')}{comparison}</section>'''
    page, pages = board['page'], board['pages']
    prev = f'<a href="/leaderboard?page={page-1}#rankings">Previous</a>' if page>1 else '<span aria-disabled="true">Previous</span>'
    next_link = f'<a href="/leaderboard?page={page+1}#rankings">Next</a>' if page<pages else '<span aria-disabled="true">Next</span>'
    ranking = f'''<section id="rankings" class="site-panel"><div class="panel-heading"><h2>Leaderboard</h2><span>{number(board['players'])} players</span></div>{leaderboard_table(board['entries'],user,mine)}<nav class="pagination" aria-label="Leaderboard pages">{prev}<span>Page {page} of {pages}</span>{next_link}</nav></section>'''
    return personal + community_panel + ranking

ABOUT_HTML = build_info_page('About', 'about', ABOUT_CONTENT)

GAME_ACCOUNT_CSS = '''
.site-nav { flex: 1; justify-content: flex-end; }
.nav-account-slot { margin-left: auto; }
.site-nav .account-link { display: inline-flex; align-items: center; gap: 7px; color: var(--ink); }
.account-light { display: inline-block; width: 7px; height: 7px; flex: none; border-radius: 1px; background: #757986; }
.account-light.is-on { background: var(--you); box-shadow: 0 0 8px var(--you); }
@media(max-width:600px) { .site-nav { flex-wrap: wrap; column-gap: 7px; row-gap: 4px; } .nav-account-slot { margin-left: 0; } }
'''
GAME_HTML = HTML.replace('</style>', GAME_ACCOUNT_CSS + POLISH_CSS + '</style>', 1)

def account_nav(user):
    if user:
        return f'<a class="account-link" href="/account"><span class="account-light is-on" aria-hidden="true"></span>Logged in as {escape(user["username"])}</a>'
    return '<a class="account-link" href="/login"><span class="account-light" aria-hidden="true"></span>Log in / Sign up</a>'

def add_account_nav(document, user):
    return document.replace('<span class="nav-account-slot"></span>', '<span class="nav-account-slot">' + account_nav(user) + '</span>', 1)

def game_document(user, totals, board=None):
    count = totals['matches']
    ai = totals['ai_wins']
    human = totals['human_wins']
    draws = totals['draws']
    ai_share = 100 * ai / count if count else 0
    human_share = 100 * human / count if count else 0
    average_ai = round(totals['ai_grains'] / count) if count else 0
    average_human = round(totals['human_grains'] / count) if count else 0
    scoreboard = f'''<section id="scoreboard" class="scoreboard" aria-label="Global AI versus humans scoreboard"><div class="score"><div class="ai"><div class="team">AI</div><strong>{number(ai)}</strong><small>wins · {ai_share:.1f}%</small></div><div class="middle"><b>{number(count)}</b>matches<br>{number(draws)} draws</div><div class="humans"><div class="team">HUMANS</div><strong>{number(human)}</strong><small>wins · {human_share:.1f}%</small></div></div><div class="win-bar" aria-hidden="true"><span style="flex:{ai}"></span><span style="flex:{draws}"></span><span style="flex:{human}"></span></div><table><thead><tr><th scope="col">Per completed match</th><th scope="col">AI</th><th scope="col">Humans</th></tr></thead><tbody><tr><td>Average grains cleared</td><td>{number(average_ai)}</td><td>{number(average_human)}</td></tr><tr><td>Total grains cleared</td><td>{number(totals['ai_grains'])}</td><td>{number(totals['human_grains'])}</td></tr></tbody></table><p class="footnote">Live results from completed signed-in matches.</p>{local_scoreboard}</section>'''
    start = GAME_HTML.index('<section id="scoreboard"')
    end = GAME_HTML.index('</section>', start) + len('</section>')
    preview = ''
    if board is not None:
        preview = '<section class="game-leaderboard" aria-label="Top ten players"><div class="panel-heading"><h2>Top 10 players</h2><a href="/leaderboard#rankings">Full leaderboard ↗</a></div>' + leaderboard_table(board['top'], user) + '</section>'
    return add_account_nav(GAME_HTML[:start] + scoreboard + preview + GAME_HTML[end:], user)

def account_content(user, board):
    mine = board['mine']
    record = f'{mine["wins"]} wins · {mine["losses"]} losses · {mine["draws"]} draws' if mine else 'No completed matches yet.'
    return f'''<section class="site-panel"><h2>Logged in as {escape(user['username'])}</h2><p>{record}</p><p><a class="inline-link" href="/leaderboard">View your leaderboard record</a></p><button id="sign-out" class="panel-cta" type="button">Sign out</button></section><script>document.getElementById('sign-out').addEventListener('click', async () => {{ await fetch('/api/logout', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:'{{}}'}}); location.assign('/'); }});</script>'''

class PreviewHandler(original.DemoHandler):
    def current_user(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get('Cookie', ''))
        except cookies.CookieError:
            return None
        item = jar.get('sandtris_session')
        return self.server.accounts.user_for_token(item.value) if item else None

    def session_token(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get('Cookie', ''))
        except cookies.CookieError:
            return None
        item = jar.get('sandtris_session')
        return item.value if item else None

    def respond_session(self, status, payload, token=None, clear=False):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if token or clear:
            secure = '; Secure' if self.headers.get('X-Forwarded-Proto') == 'https' else ''
            cookie = ('sandtris_session=; Max-Age=0' if clear else
                      f'sandtris_session={token}; Max-Age=2592000')
            self.send_header('Set-Cookie', cookie + '; Path=/; HttpOnly; SameSite=Lax' + secure)
        self.end_headers()
        self.wfile.write(raw)

    def read_account_data(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise ValueError('Expected JSON.')
        origin = self.headers.get('Origin')
        if origin and urlparse(origin).netloc != self.headers.get('Host'):
            raise ValueError('Request origin does not match this site.')
        length = int(self.headers.get('Content-Length', '0'))
        if not 0 < length <= 1024:
            raise ValueError('Invalid request size.')
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError('Expected an object.')
        return data

    def get_match(self, match_id):
        match = super().get_match(match_id)
        owner = getattr(match, 'owner_user_id', None)
        if owner and (not self.current_user() or self.current_user()['id'] != owner):
            raise ValueError('Sign in to continue this match.')
        return match

    def on_new_match(self, match):
        user = self.current_user()
        match.owner_user_id = user['id'] if user else None

    def after_move(self, match, state):
        if state['result']:
            self.server.accounts.record_match(match, getattr(match, 'owner_user_id', None))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        user = self.current_user()
        assets = {
            "/favicon.png": (ROOT / "web" / "favicon.png", "image/png"),
            "/beach-background.js": (ROOT / "web" / "beach-background.js", "text/javascript; charset=utf-8"),
            "/account.js": (ROOT / "web" / "account.js", "text/javascript; charset=utf-8"),
            "/beach-assets/night-beach.mp4": (BEACH_ASSETS / "night-beach.mp4", "video/mp4"),
            "/beach-assets/night-beach-poster.jpg": (BEACH_ASSETS / "night-beach-poster.jpg", "image/jpeg"),
            "/beach-assets/sandtris-readme.txt": (BEACH_ASSETS / "sandtris-readme.txt", "text/plain; charset=utf-8"),
        }
        if path == "/":
            self.respond(200, game_document(user, self.server.accounts.global_stats(), self.server.accounts.standings(user['id'] if user else None)).encode(), "text/html; charset=utf-8")
        elif path in {"/about", "/about/"}:
            self.respond(200, add_account_nav(ABOUT_HTML, user).encode(), "text/html; charset=utf-8")
        elif path in {"/leaderboard", "/leaderboard/"}:
            try:
                page = int(parse_qs(parsed.query).get('page', ['1'])[0])
            except ValueError:
                page = 1
            document = build_info_page('Leaderboard', 'leaderboard', leaderboard_content(user, self.server.accounts.standings(user['id'] if user else None, page)))
            self.respond(200, add_account_nav(document, user).encode(), "text/html; charset=utf-8")
        elif path in {"/login", "/login/"}:
            if user:
                document = build_info_page('Account', 'account', account_content(user, self.server.accounts.standings(user['id'])))
            else:
                document = build_info_page('Log in', 'account', AUTH_CONTENT + AUTH_SCRIPT)
            self.respond(200, add_account_nav(document, user).encode(), "text/html; charset=utf-8")
        elif path in {"/account", "/account/"}:
            document = build_info_page('Account', 'account', account_content(user, self.server.accounts.standings(user['id']))) if user else build_info_page('Log in', 'account', AUTH_CONTENT + AUTH_SCRIPT)
            self.respond(200, add_account_nav(document, user).encode(), "text/html; charset=utf-8")
        elif path == '/api/username':
            name = parse_qs(parsed.query).get('name', [''])[0]
            self.respond(200, {'available': self.server.accounts.available(name)})
        elif path in assets:
            file, content_type = assets[path]
            if file.is_file():
                self.respond(200, file.read_bytes(), content_type)
            else:
                self.respond(404, b"Background asset not found", "text/plain; charset=utf-8")
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in {'/api/login', '/api/signup', '/api/logout'}:
            return super().do_POST()
        try:
            data = self.read_account_data()
            if path == '/api/logout':
                self.server.accounts.end_session(self.session_token())
                self.respond_session(200, {'ok': True}, clear=True)
                return
            username = data.get('username')
            password = data.get('password')
            if not isinstance(username, str) or not isinstance(password, str):
                raise ValueError('Enter a username and password.')
            if len(username) > 20 or len(password) > 128:
                raise ValueError('Username or password is too long.')
            if path == '/api/login':
                address = self.client_address[0]
                with self.server.auth_lock:
                    attempts = [stamp for stamp in self.server.auth_attempts.get(address, []) if time.monotonic() - stamp < 60]
                    self.server.auth_attempts[address] = attempts
                    if len(attempts) >= 6:
                        raise ValueError('Too many login attempts. Try again in a minute.')
                try:
                    user_id = self.server.accounts.login(username, password)
                except ValueError:
                    with self.server.auth_lock:
                        self.server.auth_attempts.setdefault(address, []).append(time.monotonic())
                    raise
            else:
                user_id = self.server.accounts.signup(username, password)
            token = self.server.accounts.create_session(user_id)
            self.respond_session(200, {'username': username}, token=token)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.respond(400, {'error': str(exc)})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    server = original.DemoServer((args.host, args.port))
    server.accounts = AccountStore(os.environ.get('SANDTRIS_DB_PATH', '/tmp/sandtris-duel-accounts.sqlite3'))
    server.auth_lock = threading.Lock()
    server.auth_attempts = {}
    server.RequestHandlerClass = PreviewHandler
    print(f"{TITLE}: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for match in list(server.matches.values()):
            match.close()
        original.game.THINKER.shutdown(wait=False, cancel_futures=True)

if __name__ == "__main__":
    main()
