"""Local, turn-synchronized Sandtris duel. Run: python web_game.py."""
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import gzip
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import parse_qs, urlparse

import numpy as np
from sandtris_env_v10 import GRID_WIDTH, GRID_HEIGHT
from sandtris_lookahead_bot import find_best_placement_lookahead
from web_physics import LiveEnv

ROOT = Path(__file__).resolve().parent
# The C evaluator has shared scratch buffers, so all native work is serialized.
ENGINE_LOCK = threading.Lock()
THINKER = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sandtris-ai")


@dataclass
class Stats:
    placed: int = 0
    clears: int = 0
    grains: int = 0

    def record(self, before, env, info):
        cleared = int(info.get("cleared_grains", 0))
        added = int(np.count_nonzero(env.world)) - before + cleared
        self.placed += int(added == 100)
        self.clears += int(cleared > 0)
        self.grains += cleared

    def serialize(self, env):
        rows = np.flatnonzero(np.any(env.world != 0, axis=1))
        return dict(steps=env.step_count, placed=self.placed, clears=self.clears,
                    grains=self.grains,
                    clear_percentage=round(100 * self.grains / (self.placed * 100), 1) if self.placed else 0,
                    clear_turn_percentage=round(100 * self.clears / env.step_count, 1) if env.step_count else 0,
                    height=int(GRID_HEIGHT - rows[0]) if len(rows) else 0)


class Match:
    def __init__(self, seed, weights):
        self.id = secrets.token_urlsafe(18)
        self.seed = seed
        self.weights = weights
        self.lock = threading.RLock()
        self.human, self.ai = LiveEnv(), LiveEnv()
        self.human.reset(seed=seed)
        self.ai.reset(seed=seed)
        self.stats = {"human": Stats(), "ai": Stats()}
        # An independent stream controls color-lookahead's sampled shapes.
        self.search_rng = np.random.default_rng(np.random.SeedSequence([seed, 731]))
        self.turn = 0
        self.action = None
        self.think_ms = 0
        self.error = None
        self.result = None
        self.closed = False
        self.prepare()

    def prepare(self):
        self.action = None
        snapshot = self.ai.clone()
        self.future = THINKER.submit(self._think, snapshot)

    def _think(self, snapshot):
        try:
            start = time.perf_counter()
            with ENGINE_LOCK:
                action = find_best_placement_lookahead(
                    snapshot, self.weights, k=3, extraction_mode="clipped",
                    lookahead_mode="color", rng=self.search_rng)
            elapsed = round((time.perf_counter() - start) * 1000)
            with self.lock:
                if not self.closed:
                    self.action, self.think_ms = int(action), elapsed
        except Exception as exc:
            with self.lock:
                self.error = f"AI could not prepare a move: {exc}"

    def close(self):
        with self.lock:
            self.closed = True
            self.future.cancel()

    def state(self):
        with self.lock:
            return dict(id=self.id, seed=self.seed, turn=self.turn, result=self.result,
                        ready=self.action is not None and not self.result and not self.error,
                        error=self.error, think_ms=self.think_ms,
                        piece=dict(shape=self.human.piece.base_shape, color=self.human.piece.color_idx),
                        boards={name: dict(world=env.world.tolist(), done=bool(env.done),
                                           stats=self.stats[name].serialize(env))
                                for name, env in [("human", self.human), ("ai", self.ai)]})

    def move(self, turn, action=None, placement=None):
        with self.lock:
            if self.closed or self.result:
                raise ValueError("This match has finished. Start a new match.")
            if type(turn) is not int or turn != self.turn:
                raise ValueError("This turn was already played. Refresh the board.")
            if placement is None:
                if type(action) is not int or not 0 <= action < 68:
                    raise ValueError("Choose a valid placement.")
            elif (not isinstance(placement, dict)
                  or any(type(placement.get(key)) is not int for key in ('x', 'y', 'rotation'))
                  or not 0 <= placement['rotation'] < 4):
                raise ValueError("Choose a valid grain-level placement.")
            if self.error:
                raise ValueError(self.error)
            if self.action is None:
                raise ValueError("The AI is still preparing its move.")
            ai_action = self.action
            # Work on copies; a failed turn cannot leave only one board advanced.
            human, ai = self.human.clone(), self.ai.clone()
            records = []
            frames = {}
            with ENGINE_LOCK:
                for name, env, selected in [("human", human, action), ("ai", ai, ai_action)]:
                    before = int(np.count_nonzero(env.world))
                    if name == 'human' and placement is not None:
                        # sandtris.py rotates (x, y) -> (y, -x), opposite
                        # the existing evaluator's rotation numbering.
                        x, y = placement['x'], placement['y']
                        rotation = (-placement['rotation']) % 4
                    else:
                        rotation, column = divmod(selected, 17)
                        env.piece.set_rotation(rotation)
                        width = (max(bx for bx, _ in env.piece.shape) + 1) * 5
                        x, y = min(column * 5, GRID_WIDTH - width), 0
                    info, frames[name] = env.place(x, y, rotation, capture=True)
                    records.append((name, before, env, info))
            self.human, self.ai = human, ai
            for name, before, env, info in records:
                self.stats[name].record(before, env, info)
            self.turn += 1
            if human.done or ai.done:
                self.result = "Draw" if human.done and ai.done else "AI wins" if human.done else "You win"
                self.action = None
            elif not self.closed:
                self.prepare()
            state = self.state()
            state["last_actions"] = dict(human=action, ai=ai_action)
            state["frames"] = frames
            return state


def load_weights():
    weights = np.load(ROOT / "best_clipped_weights_run2.npy")
    if weights.shape != (24,) or not np.all(np.isfinite(weights)):
        raise RuntimeError("Expected 24 finite weights in best_clipped_weights_run2.npy")
    return weights


class GameServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, Handler)
        self.matches = {}
        self.matches_lock = threading.Lock()
        self.weights = load_weights()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def after_move(self, match, state):
        """Extension point for recording a completed server-side match."""
        pass

    def respond(self, status, payload, content_type="application/json"):
        raw = json.dumps(payload).encode() if content_type == "application/json" else payload
        compressed = len(raw) > 4096 and 'gzip' in self.headers.get('Accept-Encoding', '')
        if compressed:
            raw = gzip.compress(raw, compresslevel=1)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        if compressed:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def get_match(self, match_id):
        with self.server.matches_lock:
            match = self.server.matches.get(match_id)
        if match is None:
            raise ValueError("Match expired. Start a new match.")
        return match

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.respond(200, dict(status="ok"))
            return
        if parsed.path == "/api/state":
            try:
                match = self.get_match(parse_qs(parsed.query).get("id", [None])[0])
                self.respond(200, match.state())
            except ValueError as exc:
                self.respond(404, dict(error=str(exc)))
            return
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/style.css": ("style.css", "text/css; charset=utf-8")}
        if parsed.path not in files:
            self.respond(404, dict(error="Not found"))
            return
        name, mime = files[parsed.path]
        self.respond(200, (ROOT / "web" / name).read_bytes(), mime)

    def do_POST(self):
        try:
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Expected JSON")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected an object")
            if self.path == "/api/new":
                seed = data.get("seed")
                if seed is None:
                    seed = secrets.randbelow(2**32)
                if type(seed) is not int or not 0 <= seed < 2**32:
                    raise ValueError("Seed must be a whole number between 0 and 4294967295.")
                with self.server.matches_lock:
                    previous = self.server.matches.pop(data.get("previous_id"), None)
                    if previous:
                        previous.close()
                    if len(self.server.matches) >= 16:
                        oldest = next(iter(self.server.matches))
                        self.server.matches.pop(oldest).close()
                    match = Match(seed, self.server.weights)
                    self.server.matches[match.id] = match
                self.respond(200, match.state())
            elif self.path == "/api/move":
                match = self.get_match(data.get("id"))
                state = match.move(data.get("turn"), data.get("action"), data.get("placement"))
                self.after_move(match, state)
                self.respond(200, state)
            else:
                self.respond(404, dict(error="Not found"))
        except (ValueError, TypeError) as exc:
            self.respond(400, dict(error=str(exc)))
        except Exception:
            import traceback
            traceback.print_exc()
            self.respond(500, dict(error="The turn could not be completed. Restart the match."))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Bind address; use 0.0.0.0 in a container")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    server = GameServer((args.host, args.port))
    print(f"Sandtris Duel listening on {args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        THINKER.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
