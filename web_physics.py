"""Grain-level web placement with sandtris.py-style sand physics.

Both boards use a seeded version of sandtris.py's grain tick and wall-to-wall
clear. The AI keeps its existing color-lookahead search and C feature scorer.
"""
import base64
import copy
import random

import numpy as np
from scipy.ndimage import label

FOUR_NEIGHBORS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
from sandtris_env_v10 import SandtrisEnv, Piece, GRID_WIDTH, GRID_HEIGHT


class LiveEnv(SandtrisEnv):
    def __init__(self, render_mode=None):
        super().__init__(render_mode=render_mode)
        self.sand_rng = random.Random()

    def reset(self, seed=None, options=None):
        result = super().reset(seed=seed, options=options)
        # Keep sand randomness separate from the shared piece/color sequence.
        self.sand_rng = random.Random(seed)
        return result

    def clone(self):
        result = copy.copy(self)
        result.world = self.world.copy()
        result._rng = copy.deepcopy(self._rng)
        result.sand_rng = copy.deepcopy(self.sand_rng)
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
        """Drop from a legal grain-level position, then run live sand ticks."""
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
        """Tick sand and clear after each tick until no sand changes."""
        frames = []
        def record():
            if capture:
                frames.append(base64.b64encode(self.world.astype(np.uint8).tobytes()).decode('ascii'))
        record()
        total_cleared = 0
        world = self.world.tolist()
        while True:
            changed = False
            # This is sandtris.py's bottom-up pass: each grain tries down first,
            # then a randomized left/right diagonal when blocked below.
            for y in range(GRID_HEIGHT - 2, -1, -1):
                row, below = world[y], world[y + 1]
                for x in range(GRID_WIDTH):
                    color = row[x]
                    if not color:
                        continue
                    if not below[x]:
                        below[x], row[x] = color, 0
                        changed = True
                    else:
                        directions = [-1, 1]
                        self.sand_rng.shuffle(directions)
                        for dx in directions:
                            nx = x + dx
                            if 0 <= nx < GRID_WIDTH and not below[nx]:
                                below[nx], row[x] = color, 0
                                changed = True
                                break
            self.world[:] = world
            # A wall-to-wall component needs its color on both edge columns.
            # Skip four full-board component scans on the many ticks where that
            # necessary condition is absent. This cannot change a clear.
            left = {row[0] for row in world if row[0]}
            candidates = left & {row[-1] for row in world if row[-1]}
            cleared = self._clear_spanning(candidates) if candidates else 0
            total_cleared += int(cleared)
            if changed or cleared:
                record()
            if cleared:
                world = self.world.tolist()
            if not changed and not cleared:
                break
        return total_cleared, frames

    def _clear_spanning(self, colors):
        """Remove exactly the same four-neighbor spans as sandtris.py.

        Only components touching the left wall can qualify. SciPy labels the
        candidate color once; matching labels on the right wall identify every
        component to remove without scanning each component in Python.
        """
        cleared = 0
        for color in colors:
            labels, _ = label(self.world == color, structure=FOUR_NEIGHBORS)
            left = np.unique(labels[:, 0])
            right = np.unique(labels[:, -1])
            spanning = np.intersect1d(left[left != 0], right[right != 0], assume_unique=True)
            if spanning.size:
                mask = np.isin(labels, spanning)
                cleared += int(np.count_nonzero(mask))
                self.world[mask] = 0
        return cleared
