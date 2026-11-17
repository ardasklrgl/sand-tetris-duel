import copy
import unittest
from unittest.mock import patch

import numpy as np

from app.sandtris_env_v10 import SHAPES
from app.web_evil import choose_evil_piece
from app.web_game import ENGINE_LOCK, LiveEnv, load_weights
from app.web_practice import PracticeMatch


class EvilTests(unittest.TestCase):
    def test_minimizes_best_response_not_worst_response(self):
        env = LiveEnv()
        env.reset(seed=123)
        seen = []

        def evaluate(candidate, color, mode):
            shape = SHAPES.index(candidate.piece.base_shape)
            seen.append((shape, color))
            # The tempting -100 is escapable; choose the piece whose BEST is -2.
            scores = [-100, 10] if (shape, color) == (0, 1) else [0, 1]
            if (shape, color) == (2, 3):
                scores = [-5, -2]
            return [0, 1], np.array(scores, dtype=float).reshape(2, 1)

        with patch('app.web_evil.extract_features', side_effect=evaluate):
            selected = choose_evil_piece(env, np.ones(1), np.random.default_rng(8))
        self.assertEqual(selected, (2, 3))
        self.assertEqual(len(set(seen)), 28)

    def test_piece_without_a_valid_bot_response_takes_priority(self):
        env = LiveEnv()
        env.reset(seed=123)

        def evaluate(candidate, color, mode):
            if candidate.piece.base_shape == SHAPES[5] and color == 2:
                return [], np.empty((0, 1))
            return [0], np.array([[-1e9]])

        with patch('app.web_evil.extract_features', side_effect=evaluate):
            self.assertEqual(choose_evil_piece(env, np.ones(1), np.random.default_rng(8)), (5, 2))

    def test_real_search_is_repeatable_and_read_only(self):
        env = LiveEnv()
        env.reset(seed=123)
        env.step(7)
        before = env.world.copy(), copy.deepcopy(env._rng.bit_generator.state), list(env.piece.base_shape), env.piece.color_idx
        with ENGINE_LOCK:
            first = choose_evil_piece(env, load_weights(), np.random.default_rng(8))
            second = choose_evil_piece(env, load_weights(), np.random.default_rng(8))
        self.assertEqual(first, second)
        np.testing.assert_array_equal(env.world, before[0])
        self.assertEqual(env._rng.bit_generator.state, before[1])
        self.assertEqual((env.piece.base_shape, env.piece.color_idx), (before[2], before[3]))

    def test_toggle_preserves_current_piece_and_applies_to_next_piece(self):
        match = PracticeMatch(123, load_weights(), 3, 'human')
        before = match.state()
        enabled = match.set_evil(True)
        for key in ('id', 'turn', 'boards', 'piece'):
            self.assertEqual(enabled[key], before[key])
        with patch('app.web_evil.choose_evil_piece', return_value=(2, 4)) as search:
            moved = match.move(0, placement=dict(x=35, y=0, rotation=0))
            search.assert_called_once()
        self.assertEqual(moved['piece'], dict(shape=SHAPES[2], color=4))
        self.assertTrue(match.set_mode('ai')['evil'])
        match.set_evil(False)
        with patch('app.web_practice.apply_evil_piece', side_effect=AssertionError('Evil ran while off')):
            match.set_mode('human')
            match.move(1, placement=dict(x=35, y=0, rotation=0))

    def test_new_evil_game_selects_first_piece_and_skips_search_on_finish(self):
        with patch('app.web_evil.choose_evil_piece', return_value=(4, 1)) as search:
            match = PracticeMatch(123, load_weights(), 1, 'ai', evil=True)
            self.assertEqual(match.state()['piece'], dict(shape=SHAPES[4], color=1))
            with patch('app.web_game.calculate_ai_action', return_value=0):
                result = match.move(0)
            self.assertEqual(result['result'], 'Practice complete')
            search.assert_called_once()

    def test_toggle_rejects_invalid_values_and_closed_sessions(self):
        match = PracticeMatch(123, load_weights(), 3, 'human')
        for invalid in (None, 1, 'true', {}):
            with self.assertRaises(ValueError):
                match.set_evil(invalid)
        match.close()
        with self.assertRaises(ValueError):
            match.set_evil(True)
