"""Single-board practice with the duel's physics and AI policy."""
import secrets
import threading
import time
import numpy as np
import web_game as game


class PracticeMatch:
    def __init__(self, seed, weights, limit, mode):
        self.id = secrets.token_urlsafe(18)
        self.seed, self.weights, self.limit, self.mode = seed, weights, limit, mode
        self.lock = threading.RLock()
        self.env = game.LiveEnv()
        self.env.reset(seed=seed)
        self.stats = game.Stats()
        self.search_rng = np.random.default_rng(np.random.SeedSequence([seed, 731]))
        self.turn, self.result, self.closed = 0, None, False
        self.last_think_ms = self.total_think_ms = 0.0
        self.ai_moves = 0

    def set_mode(self, mode):
        if mode not in ('human', 'ai'):
            raise ValueError('Choose a valid practice mode.')
        with self.lock:
            if self.closed:
                raise ValueError('This practice session has closed.')
            self.mode = mode
            return self.state()

    def close(self):
        with self.lock:
            self.closed = True

    def state(self):
        with self.lock:
            board = dict(world=self.env.world.tolist(), done=bool(self.env.done), stats=self.stats.serialize(self.env))
            return dict(id=self.id, seed=self.seed, turn=self.turn, limit=self.limit, mode=self.mode,
                        result=self.result, ready=not self.closed and not self.result, error=None,
                        last_think_ms=self.last_think_ms,
                        ai_moves=self.ai_moves,
                        average_think_ms=self.total_think_ms / self.ai_moves if self.ai_moves else 0.0,
                        piece=dict(shape=self.env.piece.base_shape, color=self.env.piece.color_idx),
                        boards=dict(human=board, ai=board))

    def move(self, turn, action=None, placement=None):
        with self.lock:
            if self.closed or self.result:
                raise ValueError('This practice session has finished.')
            if type(turn) is not int or turn != self.turn:
                raise ValueError('This turn was already played. Refresh the board.')
            env = self.env.clone()
            with game.ENGINE_LOCK:
                if self.mode == 'ai':
                    start = time.perf_counter()
                    selected = game.calculate_ai_action(env, self.weights, self.search_rng)
                    think_ms = (time.perf_counter() - start) * 1000
                    rotation, column = divmod(int(selected), 17)
                    env.piece.set_rotation(rotation)
                    width = (max(x for x, _ in env.piece.shape) + 1) * 5
                    x, y = min(column * 5, 85 - width), 0
                else:
                    if (not isinstance(placement, dict)
                            or any(type(placement.get(k)) is not int for k in ('x', 'y', 'rotation'))
                            or not 0 <= placement['rotation'] < 4):
                        raise ValueError('Choose a valid placement.')
                    x, y, rotation = placement['x'], placement['y'], (-placement['rotation']) % 4
                before = int(np.count_nonzero(env.world))
                info, frames = env.place(x, y, rotation, capture=True)
            self.env = env
            if self.mode == 'ai':
                self.last_think_ms = think_ms
                self.total_think_ms += think_ms
                self.ai_moves += 1
            self.stats.record(before, env, info)
            self.turn += 1
            if env.done:
                self.result = 'Game over'
            elif self.turn >= self.limit:
                self.result = 'Practice complete'
            state = self.state()
            state['frames'] = dict(human=frames, ai=[])
            return state
