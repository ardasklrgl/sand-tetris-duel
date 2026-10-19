"""Standalone console design preview. Run: python web_console.py --port 8768.

Reuses web_demo's match handler, JavaScript, physics, and canvas rendering.
Only the surrounding HTML and CSS differ. The original demo stays untouched.
"""
import argparse
from urllib.parse import urlparse

import web_demo as original

CONSOLE_CSS = r"""
/* All surface effects belong to the page casing, never to a game canvas. */
:root {
  --bg: #0c0e0b; --panel: #393c2d; --line: #565744;
  --muted: #b0ae91; --ink: #e7dfba; --amber: #e9af57;
  --ai: #aba9ed; --you: #d9dc9a;
  --mono: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
}
body {
  min-height: 100vh;
  background: radial-gradient(ellipse at 50% 6%, #34332266, transparent 58%),
    radial-gradient(ellipse at 0% 70%, #17251d55, transparent 60%), #0c0e0b;
  color: var(--ink); font-family: var(--mono);
  padding: 42px 16px 36px;
}
main {
  position: relative; isolation: isolate; width: 100%; max-width: 742px;
  margin: 0 auto; padding: 28px 55px 24px;
  border: 1px solid #77745a; border-radius: 12px;
  background-color: #35382a;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Cpath fill='%23fff' opacity='.07' filter='url(%23n)' d='M0 0h180v180H0z'/%3E%3C/svg%3E"),
    linear-gradient(118deg, #74715325, transparent 27%, #12160d40 85%);
  box-shadow: inset 0 2px 0 #aaa17b66, inset 3px 0 0 #77745b33,
    inset -3px 0 0 #14180f88, inset 0 -5px 0 #191d15,
    0 0 0 5px #202419, 0 0 0 6px #424332, 0 24px 80px #000b;
}
main::before, main::after {
  content: ''; position: absolute; left: 16px; right: 16px; height: 10px;
  pointer-events: none;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'%3E%3Ccircle cx='5' cy='5' r='4' fill='%2323251c' stroke='%23858062'/%3E%3Cpath d='m3 7 4-4' stroke='%23777358' stroke-width='1.3'/%3E%3C/svg%3E") left center/10px 10px no-repeat,
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'%3E%3Ccircle cx='5' cy='5' r='4' fill='%2323251c' stroke='%23858062'/%3E%3Cpath d='m3 3 4 4' stroke='%23777358' stroke-width='1.3'/%3E%3C/svg%3E") right center/10px 10px no-repeat;
}
main::before { top: 14px; } main::after { bottom: 14px; }
header { gap: 16px; margin-bottom: 22px; min-height: 57px; }
.brand { display: flex; align-items: center; gap: 14px; }
.brand-mark {
  display: grid; place-items: center; width: 37px; height: 40px; flex: none;
  border: 1px solid #999071; color: #d7cb9b; background: #22271b;
  box-shadow: inset 0 0 0 3px #404332, 0 1px 0 #99907133;
}
.brand-mark svg { width: 21px; height: 26px; }
h1 { font-family: var(--mono); font-size: 24px; line-height: 1.15; font-weight: 800;
  letter-spacing: -1.1px; color: #eee3bc; text-shadow: 0 2px 0 #11180e; }
.brand-sub { margin-top: 6px; color: #c0b18a; font-size: 9px; letter-spacing: 2.8px; text-transform: uppercase; }
.vent { width: 75px; height: 34px; flex: none; opacity: .8;
  background: repeating-linear-gradient(0deg, #171d13 0 3px, #77745980 3px 4px, transparent 4px 7px);
  border-radius: 2px; }
progress { height: 5px; margin: 0 0 22px; border-radius: 1px;
  background: #181d13; box-shadow: 0 1px 0 #77755a88, 0 -1px 0 #11170c; }
progress::-webkit-progress-bar { background: #181d13; }
progress::-webkit-progress-value { background: var(--amber); box-shadow: 0 0 8px #e9af5755; }
progress::-moz-progress-bar { background: var(--amber); }
.boards { gap: 26px; }
.board-title { margin-bottom: 10px; align-items: center; }
.board-title h2 { font: 700 13px/1.4 var(--mono); letter-spacing: 2px; text-transform: uppercase; }
.board-title h2::before { content: ''; display: inline-block; width: 5px; height: 5px;
  margin: 0 9px 2px 0; background: currentColor; box-shadow: 0 0 6px currentColor; }
/* The canvas dimensions, colors, background, and rendering are unchanged. */
canvas { border-color: #303438; }
.stats { margin-top: 12px; padding: 11px 8px 10px; gap: 4px;
  border: 1px solid #161d13; border-bottom-color: #747155; border-radius: 2px;
  background: #171d14; box-shadow: inset 0 2px 4px #0009; }
.stats span { font: 9px/1.5 var(--mono); color: #b3b092; }
.stats b { margin-top: 4px; font: 500 15px/1.3 var(--mono); color: #edbc72; }
.control-panel { margin: 25px -16px 0; padding: 20px 16px 18px;
  border: 1px solid #777155; border-radius: 3px;
  background: linear-gradient(120deg, #82806430, #10170d18);
  box-shadow: inset 0 1px 0 #b6a77d33, 0 2px 3px #11190c66; }
.controls { margin-top: 0; gap: 8px; }
button {
  border: 1px solid #888165; border-bottom-color: #11180d;
  border-radius: 3px; background: linear-gradient(#63624b, #494b38);
  color: #eee3bc; text-shadow: 0 1px 1px #1118;
  box-shadow: inset 0 1px 0 #bfb08a55, inset 0 -2px 0 #252a1d, 0 2px 2px #151a10aa;
  transition: background-color .12s, box-shadow .12s, transform .12s;
}
button:hover:enabled { background: #737055; color: #fff0c7; }
button:active:enabled { transform: translateY(1px); background: #414531;
  box-shadow: inset 0 2px 3px #1119; }
.controls button { height: 34px; max-width: 64px; font-size: 12px; }
#drop { background: linear-gradient(#a88445, #85652f); color: #fff0ca; border-top-color: #d3b171; }
#drop:hover:enabled { background: #745527; }
.help { color: #cbc4a3; font-size: 10px; line-height: 1.8; margin: 16px 0 15px; }
.settings { gap: 9px; padding-bottom: 3px; color: #cdc6a5; font-size: 11px; }
.settings label { display: flex; align-items: center; gap: 8px; }
.settings #seed { width: 112px; height: 32px; font: 12px var(--mono); }
.settings button { width: 96px; height: 32px; padding: 5px 8px; font-size: 11px; }
input[type=number] { color: #edbc72; background: #171d14; border: 1px solid #151a10;
  border-bottom-color: #817b5b; border-radius: 2px; box-shadow: inset 0 2px 4px #0009;
  font-variant-numeric: tabular-nums; }
button:focus-visible,input:focus-visible,a:focus-visible { outline-color: #f1bf76; }
.result { background: #252c1d; border-color: #8a8960; border-radius: 5px; padding: 15px;
  box-shadow: inset 0 1px 0 #d5ca9c1a; }
.result h2 { font-size: 19px; }
.result p { font-size: 10px; line-height: 1.6; }
.result button { padding: 8px 10px; font-size: 11px; text-shadow: none; }
.result.is-ai-win { background: #22212e; border-color: #68627e; }
.result.is-ai-win button { box-shadow: inset 0 1px 0 #d8d2ff55, 0 2px 2px #0008; }
.scoreboard { margin: 32px -16px 0; padding: 23px 20px 18px;
  background: #191f16; border: 1px solid #141a10; border-bottom-color: #777253;
  border-radius: 3px; box-shadow: inset 0 2px 5px #0009; }
.score { margin-bottom: 19px; }
.score strong { font: 400 37px/1.2 var(--mono); letter-spacing: -2px; }
.score .team { font-size: 10px; letter-spacing: 2px; margin-bottom: 6px; }
.score .middle { font-size: 10px; color: #b1b294; }
.score .middle b { font-size: 16px; color: #e0c697; }
.score small { font-size: 9px; color: #b1b294; }
.win-bar { height: 3px; opacity: .8; }
table { font-size: 10px; }
th,td { padding: 10px 0; border-bottom: 1px solid #3b4230; }
th:first-child,td:first-child { color: #b1b294; }
.footnote { color: #a5a68b; font-size: 9px; line-height: 1.7; }
.local-record { text-align: center; font-size: 10px; line-height: 1.8; margin: 21px 0 0; color: #c3ba98; }
.casing-foot { display: flex; justify-content: center; align-items: center; gap: 10px; margin: 19px auto 0; }
.casing-foot::before,.casing-foot::after { content: ''; width: 45px; height: 3px; background: #191f14; box-shadow: 0 1px 0 #817a5680; }
.casing-foot span { width: 5px; height: 5px; background: #a38b54; border-radius: 50%; }
body.is-paused .controls button:disabled { opacity: .4; }
@media(min-width:700px) { main { max-width: 742px; } }
@media(max-width:699px) {
  body { padding: 24px 14px; } main { padding: 27px 24px 24px; }
  .boards { gap: 20px; } .vent { width: 48px; }
  h1 { font-size: 22px; } .brand-sub { letter-spacing: 1.8px; }
}
@media(max-width:480px) {
  body { padding: 16px 10px; } main { padding: 24px 14px 21px; border-radius: 8px; }
  header { gap: 8px; margin-bottom: 18px; } .brand { gap: 10px; }
  h1 { font-size: 19px; letter-spacing: -.8px; } .brand-sub { font-size: 8px; letter-spacing: 1.2px; }
  .brand-mark { width: 30px; height: 34px; } .vent { width: 27px; height: 27px; }
  .boards { gap: 12px; } .board-title { flex-direction: row; }
  .board-title h2 { font-size: 12px; }
  .stats { grid-template-columns: 1fr 1fr; padding: 9px 7px; gap: 8px 4px; }
  .stats b { font-size: 14px; margin-top: 1px; }
  .control-panel { margin: 20px 0 0; padding: 15px 8px 12px; }
  .controls { gap: 5px; } .controls button { height: 34px; font-size: 11px; }
  .help { font-size: 9px; margin: 13px 2px; }
  .settings { gap: 6px; font-size: 10px; }
  .settings label { gap: 5px; } .settings #seed { width: 90px; height: 30px; font-size: 11px; }
  .settings button { width: 67px; height: 30px; font-size: 10px; padding: 3px 5px; }
  .scoreboard { margin: 24px 0 0; padding: 18px 10px 13px; }
  .score strong { font-size: 29px; } table { font-size: 9px; }
  .local-record { font-size: 9px; }
  .result { padding: 12px; } .result h2 { font-size: 18px; }
}
@media(max-width:350px) {
  .vent { display: none; } .settings { gap: 4px; }
  .settings #seed { width: 78px; } .settings button { width: 58px; }
  .control-panel { padding-left: 5px; padding-right: 5px; }
}
@media(prefers-reduced-motion:reduce) { button { transition: none; } }
"""

HEADER = """<header>
<div class="brand"><div class="brand-mark" aria-hidden="true"><svg viewBox="0 0 21 26" fill="currentColor"><path d="M1 1h19v3H1zm3 4h3v3h3v3h2V8h3V5h3v4h-3v3h-3v3h3v3h3v3H4v-3h3v-3h3v-3H7V9H4zM1 23h19v3H1z"/></svg></div>
<div><h1>Sand Tetris Duel</h1><div class="brand-sub">Human × machine</div></div></div>
<div class="vent" aria-hidden="true"></div></header>"""

# Retain every game element and its ID. Both JavaScript resources are unchanged.
HTML = original.HTML.replace('</style>', CONSOLE_CSS + '\n</style>')
HTML = HTML.replace('<header><h1>Sand Tetris Duel</h1></header>', HEADER)
HTML = HTML.replace('<div class="controls">', '<div class="control-panel"><div class="controls">')
HTML = HTML.replace('<section id="scoreboard"', '</div><section id="scoreboard"')
HTML = HTML.replace('</main>', '<div class="casing-foot" aria-hidden="true"><span></span></div></main>')


class ConsoleHandler(original.DemoHandler):
    def do_GET(self):
        if urlparse(self.path).path == '/':
            self.respond(200, HTML.encode(), 'text/html; charset=utf-8')
        else:
            super().do_GET()


class ConsoleServer(original.DemoServer):
    def __init__(self, address):
        super().__init__(address)
        self.RequestHandlerClass = ConsoleHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8768)
    args = parser.parse_args()
    server = ConsoleServer((args.host, args.port))
    print(f'Sand Tetris Duel — console preview: http://{args.host}:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for match in list(server.matches.values()):
            match.close()
        original.game.THINKER.shutdown(wait=False, cancel_futures=True)


if __name__ == '__main__':
    main()
