"""Grain-level web placement using the trained bot's original sand physics."""
import base64
import copy
import ctypes

import numpy as np

from sandtris_env_v10 import SandtrisEnv, Piece, GRID_WIDTH, GRID_HEIGHT, _c_core

PHYSICS_FRAME_LIMIT = 200
PLAYBACK_FRAME_LIMIT = 90
_c_core.c_step_sand_frames.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'),
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=3, flags='C_CONTIGUOUS'),
    ctypes.c_int,
]
_c_core.c_step_sand_frames.restype = ctypes.c_int


class LiveEnv(SandtrisEnv):
    def clone(self):
        result = copy.copy(self)
        result.world = self.world.copy()
        result._rng = copy.deepcopy(self._rng)
        result.piece = self.piece.clone(result.world)
        result.piece.rng = result._rng
        return result

    def step(self, action):
        """Bot's discrete placement interface, including lookahead clones."""
        rotation, column = divmod(int(action), self.num_block_cols)
        self.piece.set_rotation(rotation)
        width = (max(x for x, _ in self.piece.shape) + 1) * 5
        x = min(column * 5, GRID_WIDTH - width)
        info, _ = self.place(x, 0, rotation)
        return self._get_obs(), 0.0, self.done, False, info

    def place(self, x, y, rotation, capture=False):
        """Drop a piece, settle it with the local C engine, then clear spans."""
        if self.done:
            return {'cleared_grains': 0}, []
        self.piece.set_rotation(rotation)
        width = (max(bx for bx, _ in self.piece.shape) + 1) * 5
        height = (max(by for _, by in self.piece.shape) + 1) * 5
        if not (0 <= x <= GRID_WIDTH - width and 0 <= y <= GRID_HEIGHT - height):
            raise ValueError('The piece is outside the board.')
        self.step_count += 1
        self.piece.x, self.piece.y = x, y
        self.piece.update_grains()
        if not self.piece.can_move(0, 0):
            self.done = True
            return {'cleared_grains': 0}, []
        while self.piece.move(0, 1):
            pass
        self.piece.lock()
        cleared, frames = self.settle(capture=capture)
        self.done = bool(np.any(self.world[0]))
        self.piece = Piece(self.world, self._rng)
        return {'cleared_grains': cleared}, frames

    def settle(self, capture=False):
        raw_frames = []
        keyframes = set()
        if capture:
            raw_frames.append(self.world.astype(np.uint8).tobytes())
        total_cleared = 0
        while True:
            if capture:
                world = np.ascontiguousarray(self.world, dtype=np.uint8)
                snapshots = np.empty((PHYSICS_FRAME_LIMIT, GRID_HEIGHT, GRID_WIDTH), dtype=np.uint8)
                count = _c_core.c_step_sand_frames(world, snapshots, PHYSICS_FRAME_LIMIT)
                self.world[:] = world
                raw_frames.extend(snapshots[i].tobytes() for i in range(count))
            else:
                self.step_sand()
            cleared = int(self._clear_reward()[1])
            if not cleared:
                break
            total_cleared += cleared
            if capture:
                raw_frames.append(self.world.astype(np.uint8).tobytes())
                keyframes.add(len(raw_frames) - 1)

        if not capture:
            return total_cleared, []
        keyframes.update((0, len(raw_frames) - 1))
        if len(raw_frames) <= PLAYBACK_FRAME_LIMIT:
            selected = range(len(raw_frames))
        else:
            available = [i for i in range(len(raw_frames)) if i not in keyframes]
            slots = max(0, PLAYBACK_FRAME_LIMIT - len(keyframes))
            chosen = (available[int(i)] for i in np.linspace(
                0, len(available) - 1, min(slots, len(available)))) if slots and available else ()
            selected = sorted(keyframes | set(chosen))
        frames = [base64.b64encode(raw_frames[i]).decode('ascii') for i in selected]
        return total_cleared, frames
