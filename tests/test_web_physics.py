"""The duel's grain physics must match the environment used to train the AI."""
import base64
import copy
import unittest

import numpy as np

from sandtris_env_v10 import SandtrisEnv
from web_game import calculate_ai_action, load_weights
from web_physics import LiveEnv


class WebPhysicsTests(unittest.TestCase):
    def test_search_does_not_consume_match_piece_rng(self):
        env = LiveEnv()
        env.reset(seed=3200399780)
        rng_before = copy.deepcopy(env._rng.bit_generator.state)
        world_before = env.world.copy()
        search_rng = np.random.default_rng(731)
        calculate_ai_action(env, load_weights(), search_rng)
        self.assertEqual(env._rng.bit_generator.state, rng_before)
        np.testing.assert_array_equal(env.world, world_before)

    def test_discrete_placements_match_training_engine(self):
        for seed in (7, 42, 3200399780):
            with self.subTest(seed=seed):
                web, local = LiveEnv(), SandtrisEnv()
                web.reset(seed=seed)
                local.reset(seed=seed)
                actions = np.random.default_rng(seed).integers(0, 68, size=30)
                for action in actions:
                    _, _, web_done, _, web_info = web.step(int(action))
                    _, _, local_done, _, local_info = local.step(int(action))
                    np.testing.assert_array_equal(web.world, local.world)
                    self.assertEqual(web_info['cleared_grains'], local_info['cleared_grains'])
                    self.assertEqual(web_done, local_done)
                    self.assertEqual(web.piece.base_shape, local.piece.base_shape)
                    self.assertEqual(web.piece.color_idx, local.piece.color_idx)
                    if web_done:
                        break

    def test_captured_frames_end_at_the_final_board(self):
        animated, direct = LiveEnv(), LiveEnv()
        animated.reset(seed=3200399780)
        direct.reset(seed=3200399780)
        for action in (29, 11, 40, 6, 42):
            rotation, column = divmod(action, 17)
            animated.piece.set_rotation(rotation)
            width = (max(x for x, _ in animated.piece.shape) + 1) * 5
            info, frames = animated.place(min(column * 5, 85 - width), 0,
                                           rotation, capture=True)
            _, _, _, _, direct_info = direct.step(action)
            self.assertEqual(info, direct_info)
            self.assertGreaterEqual(len(frames), 2)
            final = np.frombuffer(base64.b64decode(frames[-1]), dtype=np.uint8)
            np.testing.assert_array_equal(final.reshape(animated.world.shape), animated.world)
            np.testing.assert_array_equal(animated.world, direct.world)

    def test_long_fall_keeps_final_animation_frame(self):
        env = LiveEnv()
        env.reset(seed=7)
        env.world[0, 0] = 1
        cleared, frames = env.settle(capture=True)
        self.assertEqual(cleared, 0)
        self.assertLessEqual(len(frames), 33)
        final = np.frombuffer(base64.b64decode(frames[-1]), dtype=np.uint8)
        np.testing.assert_array_equal(final.reshape(env.world.shape), env.world)
        self.assertEqual(env.world[-1, 0], 1)


if __name__ == '__main__':
    unittest.main()
