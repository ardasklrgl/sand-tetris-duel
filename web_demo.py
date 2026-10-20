"""Separate local 100-piece demo. Run: python web_demo.py (port 8766)."""
import argparse
import json
import secrets
from urllib.parse import urlparse

import web_game as game

LIMIT = 100


class DemoMatch(game.Match):
    def __init__(self, seed, weights):
        super().__init__(seed, weights,
                         precomputed_actions=game.PRECOMPUTED_PLANS.get(seed),
                         plan_limit=LIMIT)

    def prepare(self):
        if self.turn >= LIMIT:
            human, ai = self.stats["human"].grains, self.stats["ai"].grains
            self.result = "You win" if human > ai else "AI wins" if ai > human else "Draw"
            self.action = None
            return
        super().prepare()

    def state(self):
        with self.lock:
            result = super().state()
            result["limit"] = LIMIT
            result["result_reason"] = (
                "topout" if self.human.done or self.ai.done else "limit"
            ) if self.result else None
            return result


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sand Tetris Duel</title>
<style>
:root{color-scheme:dark;--bg:#111315;--panel:#191c1f;--line:#303438;--muted:#a2a8ae;--ink:#eef0f1;--ai:#aba9ed;--you:#d9dc9a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,sans-serif}main{max-width:730px;margin:auto;padding:25px 20px 42px}header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}h1{font-size:20px;letter-spacing:-.7px;margin:0}h1 span{font-weight:400;color:var(--muted)}header a{font-size:12px;color:var(--muted);text-decoration:none}a:hover{color:var(--ink)}.eyebrow{font-size:10px;letter-spacing:1.7px;text-transform:uppercase;color:var(--muted)}.match-line{display:flex;justify-content:space-between;align-items:center;margin-bottom:9px}.match-line p{margin:0;color:var(--muted);font-size:12px}.counter{font-variant-numeric:tabular-nums;font-size:14px}.counter span{color:var(--muted)}progress{display:block;appearance:none;width:100%;height:3px;border:0;margin-bottom:20px;background:var(--line)}progress::-webkit-progress-bar{background:var(--line)}progress::-webkit-progress-value{background:var(--you)}progress::-moz-progress-bar{background:var(--you)}.boards{display:grid;grid-template-columns:1fr 1fr;gap:24px}.board-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.board-title h2{font-size:16px;font-weight:600;margin:0}.board-title small{color:var(--muted);font-size:11px}.ai h2{color:var(--ai)}.human h2{color:var(--you)}canvas{display:block;width:100%;height:auto;background:#000;border:1px solid var(--line);image-rendering:pixelated;outline:none}canvas:focus-visible{outline:2px solid var(--you);outline-offset:3px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;padding:12px 0 0}.stats span{color:var(--muted);font-size:10px;white-space:nowrap}.stats b{display:block;color:var(--ink);font-size:16px;font-weight:500;font-variant-numeric:tabular-nums;margin-top:2px}.status-error{color:#e8a9a9;font-size:12px;margin:8px 0}.status-error[hidden]{display:none}button,input{font:inherit}button{cursor:pointer;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:5px;padding:8px 12px}button:hover:enabled{background:#282c30}button:disabled{opacity:1;cursor:default}body.is-paused .controls button:disabled{opacity:.4}button:focus-visible,input:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--you);outline-offset:3px}.controls{display:flex;gap:6px;justify-content:center;flex-wrap:nowrap;margin-top:18px}.controls button{flex:1 1 0;max-width:64px;min-width:0;height:32px;padding:5px 3px;font-size:12px}#drop{max-width:64px}.help{font-size:11px;color:var(--muted);text-align:center;margin:11px 0 5px}.settings{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:nowrap;overflow-x:auto;padding:0 0 4px;color:var(--muted);font-size:12px;scrollbar-width:thin}.settings button{display:inline-flex;align-items:center;justify-content:center;width:96px;height:32px;padding:5px 9px}.settings label,.settings button{flex:none;white-space:nowrap}.settings input[type=number]{width:55px}.settings #seed{width:118px}.compact{display:none}input[type=number]{width:57px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:6px}input[type=checkbox]{accent-color:var(--you);vertical-align:middle}.result{border:1px solid var(--line);border-radius:8px;background:#20221c;padding:17px 20px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;gap:14px}.result[hidden]{display:none}.result-copy{display:flex;align-items:center;flex-wrap:wrap;column-gap:10px;row-gap:2px}.result h2{font-size:22px;line-height:1.2;margin:0;white-space:nowrap}.result.is-ai-win{background:#181823;border-color:#494765}.result.is-ai-win h2{color:var(--ai)}.result p{color:var(--muted);font-size:12px;line-height:1.2;margin:0}.result.is-ai-win p{color:#c4c2e8}.result p[hidden]{display:none}.result button{background:var(--you);color:#161810;border:1px solid transparent;font-weight:600;white-space:nowrap;transition:background-color .15s ease,border-color .15s ease}.result.is-ai-win button{background:var(--ai);color:#171624}.result button:hover:enabled{background:#989b64;border-color:transparent;color:#161810}.result.is-ai-win button:hover:enabled{background:#7b79b8;border-color:transparent;color:#171624}.scoreboard{margin-top:33px;padding-top:32px}.score{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;text-align:center;margin:0 0 17px}.score strong{font-size:38px;line-height:1.2;letter-spacing:-1px;font-weight:500;font-variant-numeric:tabular-nums}.score .team{font-size:11px;margin-bottom:5px}.score .ai{color:var(--ai)}.score .humans{color:var(--you)}.score .middle{color:var(--muted);font-size:11px}.score .middle b{display:block;font-size:17px;font-weight:400;color:var(--ink)}.score small{display:block;color:var(--muted);font-size:10px;margin-top:4px}.win-bar{display:flex;height:4px;gap:3px;margin-bottom:17px}.win-bar span:nth-child(1){background:var(--ai);flex:742}.win-bar span:nth-child(2){background:#63686c;flex:22}.win-bar span:nth-child(3){background:var(--you);flex:484}table{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}th,td{padding:9px 0;border-bottom:1px solid #24282b;text-align:right}th:first-child,td:first-child{text-align:left;color:var(--muted)}th{font-weight:500}th:nth-child(2){color:var(--ai)}th:nth-child(3){color:var(--you)}.footnote{color:var(--muted);font-size:11px;margin:12px 0 0}.local-record{color:var(--muted);font-size:12px;margin-top:20px}
@media(min-width:700px){main{max-width:670px}.boards{gap:26px}canvas{max-height:515px;width:100%}}@media(max-width:480px){main{padding:18px 12px 28px}.boards{gap:12px}.board-title{align-items:start;flex-direction:column;gap:2px}.board-title small{font-size:9px}.stats{grid-template-columns:1fr 1fr;gap:8px}.stats b{font-size:15px}.settings{gap:5px;font-size:11px}.settings .wide{display:none}.settings .compact{display:inline}.settings button{width:76px;height:27px;padding:3px 6px}.settings #seed{width:88px;padding:4px}.controls{gap:4px}.controls button{min-width:0;padding:5px 2px;font-size:11px}.result{padding:13px;flex-wrap:wrap}.result-copy{width:100%}.result button{margin-left:auto}.result h2{font-size:19px}.match-line p{font-size:11px}.score strong{font-size:31px}}
@media(max-width:350px){.settings{gap:4px}.settings #seed{width:74px}.settings button{width:72px}.controls button{font-size:10px}}
</style>
</head>
<body><main>
<header><h1>Sand Tetris Duel</h1></header>
<progress id="match-progress" value="0" max="100" aria-label="Pieces played out of 100"></progress>
<section id="result" class="result" aria-live="polite" hidden><div class="result-copy"><h2 id="result-title"></h2><p id="result-detail"></p></div><button id="play-again">Play again</button></section>
<section class="boards" aria-label="Sandtris duel boards">
<article class="ai"><div class="board-title"><h2>AI</h2></div><canvas id="ai-board" width="340" height="600" aria-label="AI Sandtris board"></canvas><div id="ai-stats" class="stats" aria-label="AI statistics"></div></article>
<article class="human"><div class="board-title"><h2>You</h2></div><canvas id="human-board" width="340" height="600" tabindex="0" aria-label="Your Sandtris board. Use arrow keys to move and rotate; space to drop."></canvas><div id="human-stats" class="stats" aria-label="Your statistics"></div></article>
</section>
<p id="status" class="status-error" role="status" aria-live="polite" hidden></p>
<div class="controls"><button id="left" aria-label="Move left">←</button><button id="right" aria-label="Move right">→</button><button id="rotate" aria-label="Rotate">↻</button><button id="down" aria-label="Soft drop">↓</button><button id="drop">Drop <small>␣</small></button><button id="pause">Pause</button></div>
<p class="help">Arrow keys or WASD: move, rotate, soft drop · Space: drop · P: pause</p>
<input id="sand-speed" type="hidden" value="1.5"><input id="instant" type="checkbox" hidden><div class="settings"><label>Seed <input id="seed" type="number" min="0" max="4294967295" aria-label="Seed"></label><button id="restart" aria-label="Replay seed"><span class="wide">Replay seed</span><span class="compact">Replay</span></button><button id="new" aria-label="New match"><span class="wide">New match</span><span class="compact">New</span></button></div>
<section id="scoreboard" class="scoreboard" aria-label="Illustrative AI versus humans scoreboard">
<div class="score"><div class="ai"><div class="team">AI</div><strong>742</strong><small>wins · 59.5%</small></div><div class="middle"><b>1,248</b>matches<br>22 draws</div><div class="humans"><div class="team">HUMANS</div><strong>484</strong><small>wins · 38.8%</small></div></div>
<div class="win-bar" aria-hidden="true"><span></span><span></span><span></span></div>
<table><thead><tr><th scope="col">Per completed match</th><th scope="col">AI</th><th scope="col">Humans</th></tr></thead><tbody><tr><td>Average grains cleared</td><td>6,420</td><td>5,180</td></tr><tr><td>Average clear %</td><td>68.3%</td><td>55.1%</td></tr><tr><td>Total grains cleared</td><td>8,012,160</td><td>6,464,640</td></tr></tbody></table>
<p class="footnote">Design preview: these global figures are illustrative, not live results.</p></section>
<p id="local-record" class="local-record"></p>
</main><script src="/app.js"></script><script src="/demo.js"></script></body></html>"""

JS = r"""'use strict';
// The original controls and simulation client are reused without editing them.
sandSpeed = 1.5; instantSettle = false; $('sand-speed').value = 1.5; $('sand-speed').disabled = false; $('instant').checked = false; saveSandSettings();
const recordKey = 'sandtris-100-demo-record-v1';
let demoRecord;
try { demoRecord = JSON.parse(localStorage.getItem(recordKey)); } catch (_) {}
if (!demoRecord || !Array.isArray(demoRecord.matches)) demoRecord = {matches: []};
demoRecord.matches = demoRecord.matches.filter(m => m && typeof m.id === 'string' && ['You win','AI wins','Draw'].includes(m.result));
function renderRecord() {
  const matches = demoRecord.matches;
  const wins = matches.filter(m => m.result === 'You win').length;
  const losses = matches.filter(m => m.result === 'AI wins').length;
  const draws = matches.filter(m => m.result === 'Draw').length;
  if ($('local-wins')) {
    $('local-wins').textContent = wins.toLocaleString();
    $('local-losses').textContent = losses.toLocaleString();
    $('local-matches').textContent = matches.length.toLocaleString();
    $('local-draws').textContent = `${draws.toLocaleString()} ${draws === 1 ? 'draw' : 'draws'}`;
    const segments = [$('local-loss-segment'), $('local-draw-segment'), $('local-win-segment')];
    const values = matches.length ? [losses, draws, wins] : [0, 1, 0];
    segments.forEach((segment, index) => { segment.style.flexGrow = values[index]; });
  } else {
    $('local-record').textContent = `Your record on this browser: ${wins} wins · ${losses} losses · ${draws} draws`;
  }
}
function showNotice() {
  const notice = (message && message !== 'Loading…' ? message : '') || state?.error || '';
  $('status').textContent = notice;
  $('status').hidden = !notice;
}
updateUI = function () {
  document.body.classList.toggle('is-paused', paused);
  showNotice();
  if (!state) return;
  for (const name of ['ai','human']) {
    const s = state.boards[name].stats;
    const items = [['Pieces', `${s.steps}/${state.limit}`], ['Clears', s.clears], ['Grains', s.grains.toLocaleString()], ['Clear %', `${s.clear_percentage.toFixed(1)}%`]];
    const stats = $(name + '-stats');
    if (stats.children.length !== items.length) {
      stats.innerHTML = items.map(([label,value]) => `<span>${label}<b>${value}</b></span>`).join('');
    } else {
      items.forEach(([,value], index) => {
        const number = stats.children[index].querySelector('b');
        const next = String(value);
        if (number.textContent !== next) number.textContent = next;
      });
    }
  }
  $('match-progress').max = state.limit;
  $('match-progress').value = Math.min(state.turn,state.limit);
  for (const id of ['left','right','rotate','down','drop']) $(id).disabled = !controllable();
  for (const id of ['seed','restart','new','play-again']) $(id).disabled = busy;
  $('pause').disabled = busy || !!state.result;
  $('pause').textContent = paused ? 'Resume' : 'Pause';
  $('result').hidden = !state.result;
  $('result').classList.toggle('is-ai-win', state.result === 'AI wins');
  if (state.result) {
    $('result-title').textContent = state.result === 'You win' ? 'You win!' : state.result === 'AI wins' ? 'AI wins' : 'Draw';
    const humanGrains = state.boards.human.stats.grains;
    const aiGrains = state.boards.ai.stats.grains;
    const winnerGrains = Math.max(humanGrains, aiGrains);
    const loserGrains = Math.min(humanGrains, aiGrains);
    const detail = $('result-detail');
    detail.hidden = state.result === 'Draw';
    detail.textContent = detail.hidden ? '' : `Cleared ${(winnerGrains - loserGrains).toLocaleString()} more grains${loserGrains > 0 ? `, ${(winnerGrains / loserGrains).toFixed(2)}× as many` : ''}`;
    if (!demoRecord.matches.some(m => m.id === state.id)) {
      demoRecord.matches.push({id:state.id,result:state.result});
      try { localStorage.setItem(recordKey,JSON.stringify(demoRecord)); } catch (_) {}
      renderRecord();
    }
  }
};
// Keep the final boards visible; the match result has its own panel.
draw = function () {
  for (const name of ['ai','human']) {
    const ctx = $(name + '-board').getContext('2d');
    ctx.fillStyle = '#000'; ctx.fillRect(0,0,340,600);
    if (!state) continue;
    if (animation && animation.frames[name].length) {
      const frames = animation.frames[name];
      drawFrame(ctx,frames[Math.min(animation.index,frames.length-1)]);
    } else drawWorld(ctx,state.boards[name].world);
    if (name === 'human' && !state.result && piece) {
      ctx.fillStyle = COLORS[state.piece.color];
      for (const [bx,by] of shapeAt(state.piece.shape,piece.rotation)) ctx.fillRect((piece.x+bx*5)*SCALE,(piece.y+by*5)*SCALE,20,20);
    }
  }
};
$('play-again').onclick = () => newMatch(true);
renderRecord();
updateUI();
"""


class DemoHandler(game.Handler):
    def on_new_match(self, match):
        """Extension point for associating a match with a signed-in player."""
        pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.respond(200, HTML.encode(), "text/html; charset=utf-8")
        elif path == "/demo.js":
            self.respond(200, JS.encode(), "text/javascript; charset=utf-8")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/api/new":
            return super().do_POST()
        try:
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Expected JSON")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected an object")
            seed = data.get("seed")
            if seed is not None and (type(seed) is not int or not 0 <= seed < 2**32):
                raise ValueError("Seed must be a whole number between 0 and 4294967295.")
            previous_id = data.get("previous_id")
            if previous_id is not None and not isinstance(previous_id, str):
                raise ValueError("Invalid previous match")
            with self.server.matches_lock:
                if seed is None:
                    seed = self.server.next_seed()
                previous = self.server.matches.pop(previous_id, None)
                if previous:
                    previous.close()
                if len(self.server.matches) >= 16:
                    self.server.matches.pop(next(iter(self.server.matches))).close()
                match = DemoMatch(seed, self.server.weights)
                self.server.matches[match.id] = match
            self.on_new_match(match)
            self.respond(200, match.state())
        except (ValueError, TypeError) as exc:
            self.respond(400, dict(error=str(exc)))


class DemoServer(game.GameServer):
    def __init__(self, address):
        super().__init__(address)
        self.RequestHandlerClass = DemoHandler
        self.seed_pool = []

    def next_seed(self):
        # Called while matches_lock is held. Use every cached seed before repeats.
        if not game.PRECOMPUTED_PLANS:
            return secrets.randbelow(2**32)
        if not self.seed_pool:
            self.seed_pool = list(game.PRECOMPUTED_PLANS)
            secrets.SystemRandom().shuffle(self.seed_pool)
        return self.seed_pool.pop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = DemoServer((args.host, args.port))
    print(f"Sandtris {LIMIT}-piece demo: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for match in list(server.matches.values()):
            match.close()
        game.THINKER.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
