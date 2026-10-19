"""Playable apple design direction. Run: python web_apple.py."""
import argparse
from urllib.parse import urlparse
import web_demo as original

TITLE = 'Sand Tetris Duel · Studio'
PORT = 8769
CSS = r"""
*{box-sizing:border-box}button,input{transition:background .18s ease,box-shadow .18s ease}button:active:enabled{transform:translateY(1px)}::selection{background:var(--you);color:var(--bg)}input{caret-color:var(--you)}button:focus-visible,input:focus-visible{outline:2px solid var(--you);outline-offset:3px}.controls{margin-top:26px}.controls button{height:36px}.help{line-height:1.7;margin:14px 0 12px}.settings{padding-bottom:6px}.settings label{display:flex;align-items:center;gap:7px}.settings #seed{height:32px}.stats b{font-variant-numeric:tabular-nums}.boards canvas{width:100%;height:auto;max-height:none;aspect-ratio:17/30}.scoreboard{margin-top:26px;padding-top:26px}.footnote{line-height:1.6}.local-record{line-height:1.6}button svg{width:16px;height:16px;vertical-align:middle;pointer-events:none}.controls button{display:flex;justify-content:center;align-items:center;gap:5px}@media(max-width:480px){.help{font-size:10px}.controls{gap:5px}.controls button{height:38px}.settings{gap:6px}.settings #seed{width:96px}.settings button{height:32px;width:80px}}

:root{color-scheme:light;--bg:#f5f5f7;--panel:#f0f0f3;--line:#d9d9df;--muted:#65656d;--ink:#1d1d1f;--ai:#0071e3;--you:#b35d00}
body{background:#f5f5f7;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',sans-serif;padding:42px 22px 60px;min-height:100vh}
main{max-width:760px;padding:34px 44px 30px;background:#fff;border-radius:24px;box-shadow:0 18px 70px #2020300c;margin:auto}
header{margin-bottom:22px;gap:15px}h1{font-size:25px;letter-spacing:-.7px;font-weight:650}.brand-icon{display:grid;place-items:center;width:38px;height:38px;flex:none;color:#fff;background:#0071e3;border-radius:10px}.brand-icon svg{width:23px;height:23px}.brand{display:flex;align-items:center;gap:12px}.match-caption{color:var(--muted);font-size:12px;white-space:nowrap}
progress{height:4px;margin-bottom:24px;border-radius:10px;overflow:hidden}progress::-webkit-progress-value{background:#0071e3}progress::-moz-progress-bar{background:#0071e3}.boards{gap:24px}.board-title h2{font-size:15px}.board-title{margin-bottom:12px}.boards canvas{border:0;border-radius:12px}.stats{padding-top:15px;gap:5px}.stats span{font-size:10px}.stats b{font-size:17px;font-weight:600;margin-top:4px}
button{border:0;border-radius:9px;background:#f0f0f3;color:#353538;font-weight:500}button:hover:enabled{background:#e3e3e8}#drop{background:#0071e3;color:white}#drop:hover:enabled{background:#005dc3}input[type=number]{background:#f5f5f7;border:1px solid #dedee3;border-radius:8px;color:#1d1d1f}button:focus-visible,input:focus-visible,.boards canvas:focus-visible{outline-color:#0071e3}
.scoreboard{padding:26px 24px 20px;background:#f7f7f9;border-radius:16px}.score strong{font-size:34px;font-weight:600;letter-spacing:-1px}.score .middle b{color:#353538}.win-bar{height:5px;border-radius:5px;overflow:hidden;gap:2px}th,td{border-color:#e1e1e6;padding:11px 0}.result,.result.is-ai-win{background:#edf5ff;border:0;border-radius:14px;color:#1d1d1f}.result.is-ai-win h2{color:#0071e3}.result p,.result.is-ai-win p{color:#505c70}.result button,.result.is-ai-win button{color:#fff;background:#0071e3;border:0}.result button:hover:enabled,.result.is-ai-win button:hover:enabled{color:#fff;background:#005dc3}.local-record{text-align:center;font-size:11px}.status-error{color:#a62828}body.is-paused .controls button:disabled{opacity:.4}
@media(max-width:700px){body{padding:18px 12px 32px}main{padding:26px 24px;max-width:760px;border-radius:20px}.match-caption{display:none}}@media(max-width:480px){body{padding:0;background:#fff}main{padding:24px 14px;border-radius:0;box-shadow:none}h1{font-size:21px}.boards{gap:14px}.boards canvas{border-radius:8px}.stats{grid-template-columns:repeat(2,1fr)}.scoreboard{padding:20px 14px}.stats b{font-size:16px}.result h2{font-size:19px}}
"""
HTML = original.HTML.replace("</style>", CSS + "</style>", 1)
HTML = HTML.replace("<header><h1>Sand Tetris Duel</h1></header>", '<header><div class="brand"><span class="brand-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 5h16M4 19h16M6 5c0 4 6 4 6 7s-6 3-6 7M18 5c0 4-6 4-6 7s6 3 6 7"/></svg></span><h1>Sand Tetris Duel</h1></div><span class="match-caption">100 pieces. One duel.</span></header>')

class PreviewHandler(original.DemoHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.respond(200, HTML.encode(), "text/html; charset=utf-8")
        else:
            super().do_GET()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    server = original.DemoServer((args.host, args.port))
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
