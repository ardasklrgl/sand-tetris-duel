import base64
import unittest
from unittest.mock import patch

from web_game import PRECOMPUTED_PLANS, LiveEnv, load_weights
from web_practice import PracticeMatch


class PracticeTests(unittest.TestCase):
    def test_human_uses_original_physics_without_ai_work(self):
        match = PracticeMatch(123, load_weights(), 1, 'human')
        reference = LiveEnv()
        reference.reset(seed=123)
        reference.place(35, 0, 3)
        with patch('web_game.calculate_ai_action', side_effect=AssertionError('Human practice calculated AI')):
            result = match.move(0, placement=dict(x=35, y=0, rotation=1))
        self.assertEqual(result['boards']['human']['world'], reference.world.tolist())
        self.assertEqual(result['result'], 'Practice complete')
        self.assertEqual(base64.b64decode(result['frames']['human'][-1]), reference.world.tobytes())
        with self.assertRaises(ValueError):
            match.move(1, placement=dict(x=35, y=0, rotation=0))

    def test_live_ai_matches_trained_policy_plan(self):
        seed = min(PRECOMPUTED_PLANS)
        match = PracticeMatch(seed, load_weights(), 5, 'ai')
        reference = LiveEnv()
        reference.reset(seed=seed)
        for turn, action in enumerate(PRECOMPUTED_PLANS[seed][:5]):
            reference.step(action)
            result = match.move(turn)
            self.assertEqual(result['boards']['human']['world'], reference.world.tolist())
        self.assertEqual(result['turn'], 5)
        self.assertEqual(result['result'], 'Practice complete')

    def test_invalid_move_does_not_advance_session(self):
        match = PracticeMatch(123, load_weights(), 200, 'human')
        for turn, placement in [(1, dict(x=35, y=0, rotation=0)), (0, dict(x=-1, y=0, rotation=0)), (0, {})]:
            with self.assertRaises(ValueError):
                match.move(turn, placement=placement)
            self.assertEqual(match.turn, 0)
            self.assertEqual(match.env.step_count, 0)
        match.close()
        with self.assertRaises(ValueError):
            match.move(0, placement=dict(x=35, y=0, rotation=0))
