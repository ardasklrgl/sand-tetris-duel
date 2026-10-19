"""Background-only night beach study. Run python web_beach.py, then open port 8771."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent / 'design' / 'beach'

class BeachHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] == '/':
            self.path = '/beach.html'
        super().do_GET()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8771)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), partial(BeachHandler, directory=str(ROOT)))
    print(f'Night beach study: http://{args.host}:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
